from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.med_reconciliation import (
    MedReconciliationImport,
    MedReconciliationItem,
)
from app.models.medication import Medication
from app.services.med_reconciliation_audit_service import (
    log_med_reconciliation_audit_event,
)
from app.services.med_reconciliation_comparison import (
    compare_imported_item_against_med_list,
)
from app.services.med_reconciliation_dedup_service import (
    close_older_duplicate_tasks_when_one_duplicate_remains_active,
)
from app.services.med_reconciliation_normalizer import (
    normalize_med_reconciliation_item,
)
from app.services.med_safety import evaluate_medication_safety
from app.services.reconciliation_task_service import (
    create_reconciliation_task_if_needed,
)

logger = logging.getLogger(__name__)

VALID_LIST_TYPES = {"INPATIENT_HISTORY", "DISCHARGE_LIST"}
VALID_SOURCE_TYPES = {"PDF", "CCD", "C-CDA", "SCANNED_DOC", "MANUAL"}
VALID_SOURCE_CONTEXTS = {"HOSPITAL_DISCHARGE", "ED_VISIT", "INPATIENT_STAY", "OTHER"}
UNRESOLVED_REVIEW_STATUSES = {"PENDING"}
ACTIVE_MED_DEDUP_INDEX_NAME = "uq_med_recon_active_patient_signature"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _resolve_source_type(source_type: str) -> str:
    value = (source_type or "").strip().upper()
    if value not in VALID_SOURCE_TYPES:
        raise ValueError("Invalid source_type")
    return value


def _resolve_source_context(source_context: str) -> str:
    value = (source_context or "").strip().upper()
    if value not in VALID_SOURCE_CONTEXTS:
        raise ValueError("Invalid source_context")
    return value


def _existing_medications_payload_for_patient(
    db: Session,
    patient_id,
) -> List[Dict[str, Any]]:
    meds = (
        db.query(Medication)
        .filter(Medication.patient_id == patient_id)
        .filter(Medication.is_active.is_(True))
        .all()
    )

    payload: List[Dict[str, Any]] = []
    for med in meds:
        payload.append(
            {
                "id": med.id,
                "medication_name": getattr(med, "medication_name", None),
                "canonical_name": getattr(med, "canonical_name", None),
                "dose_normalized": getattr(med, "dose_normalized", None)
                or getattr(med, "dosage", None),
                "route_normalized": getattr(med, "route_normalized", None)
                or getattr(med, "route", None),
                "frequency_normalized": getattr(med, "frequency_normalized", None)
                or getattr(med, "frequency", None),
            }
        )
    return payload


def _require_med_name_raw(row: Dict[str, Any], index: int) -> str:
    value = (row.get("med_name_raw") or "").strip()
    if not value:
        raise ValueError(f"med_name_raw is required at medications[{index}]")
    return value


def _resolve_list_type(row: Dict[str, Any], index: int) -> str:
    list_type = (row.get("list_type") or "DISCHARGE_LIST").strip().upper()
    if list_type not in VALID_LIST_TYPES:
        raise ValueError(f"Invalid list_type at medications[{index}]")
    return list_type


def _signature_text(*parts: Any) -> str:
    normalized_parts: list[str] = []
    for part in parts:
        value = "" if part is None else str(part).strip().lower()
        normalized_parts.append(value)
    return "|".join(normalized_parts)


def _build_signature_hash(
    *,
    med_name_normalized: str | None,
    dose_normalized: str | None,
    route_normalized: str | None,
    frequency_normalized: str | None,
) -> str:
    signature_text = _signature_text(
        med_name_normalized,
        dose_normalized,
        route_normalized,
        frequency_normalized,
    )
    return hashlib.sha256(signature_text.encode("utf-8")).hexdigest()


def _safe_audit(**kwargs) -> None:
    try:
        log_med_reconciliation_audit_event(**kwargs)
    except Exception as audit_exc:
        logger.exception("MED_RECON_AUDIT_FAILED error=%s", str(audit_exc))


def create_import_with_items(
    *,
    db: Session,
    tenant_id,
    patient_id,
    source_type: str,
    source_context: str,
    source_file_name: str | None,
    uploaded_by,
    raw_summary: str | None,
    medications: List[Dict[str, Any]],
) -> dict[str, Any]:
    if not medications:
        raise ValueError("medications is required")

    now = _utcnow()
    resolved_source_type = _resolve_source_type(source_type)
    resolved_source_context = _resolve_source_context(source_context)

    import_record = MedReconciliationImport(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        source_type=resolved_source_type,
        source_context=resolved_source_context,
        status="PENDING_REVIEW",
        source_file_name=_clean_str(source_file_name),
        uploaded_by=uploaded_by,
        uploaded_at=now,
        raw_summary=_clean_str(raw_summary),
        created_at=now,
        updated_at=now,
    )

    db.add(import_record)
    db.flush()

    existing_medications = _existing_medications_payload_for_patient(
        db=db,
        patient_id=patient_id,
    )

    created_items: list[MedReconciliationItem] = []
    item_ids: list[str] = []
    task_item_ids: list[str] = []
    duplicate_item_ids: list[str] = []

    for idx, row in enumerate(medications):
        med_name_raw = _require_med_name_raw(row, idx)
        list_type = _resolve_list_type(row, idx)

        normalized = normalize_med_reconciliation_item(
            med_name_raw=med_name_raw,
            dose=row.get("dose"),
            route=row.get("route"),
            frequency=row.get("frequency"),
        )

        med_name_normalized = normalized.get("med_name_normalized")
        dose_normalized = normalized.get("dose_normalized")
        route_normalized = normalized.get("route_normalized")
        frequency_normalized = normalized.get("frequency_normalized")

        signature_hash = _build_signature_hash(
            med_name_normalized=med_name_normalized,
            dose_normalized=dose_normalized,
            route_normalized=route_normalized,
            frequency_normalized=frequency_normalized,
        )

        _safe_audit(
            db=db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            import_id=import_record.id,
            stage="NORMALIZATION",
            event_type="NORMALIZATION_COMPLETED",
            med_name_raw=med_name_raw,
            normalized_payload={
                **normalized,
                "signature_hash": signature_hash,
            },
        )

        prior_duplicate = (
            db.query(MedReconciliationItem)
            .filter(MedReconciliationItem.patient_id == patient_id)
            .filter(MedReconciliationItem.review_status.in_(UNRESOLVED_REVIEW_STATUSES))
            .filter(MedReconciliationItem.signature_hash == signature_hash)
            .first()
        )

        if prior_duplicate:
            duplicate_item_ids.append(str(prior_duplicate.id))

            _safe_audit(
                db=db,
                tenant_id=tenant_id,
                patient_id=patient_id,
                import_id=import_record.id,
                stage="DEDUP",
                event_type="DUPLICATE_PRECHECK",
                med_name_raw=med_name_raw,
                normalized_payload={
                    **normalized,
                    "signature_hash": signature_hash,
                    "existing_item_id": str(prior_duplicate.id),
                },
            )

            try:
                close_older_duplicate_tasks_when_one_duplicate_remains_active(
                    db=db,
                    patient_id=patient_id,
                    med_name_normalized=med_name_normalized,
                )
            except Exception as cleanup_exc:
                logger.exception(
                    "MED_RECON_TASK_DEDUP_CLEANUP_FAILED patient_id=%s med_name_normalized=%s error=%s",
                    str(patient_id),
                    med_name_normalized,
                    str(cleanup_exc),
                )

            continue

        comparison = compare_imported_item_against_med_list(
            imported_item={
                "med_name_normalized": med_name_normalized,
                "dose_normalized": dose_normalized,
                "route_normalized": route_normalized,
                "frequency_normalized": frequency_normalized,
            },
            existing_medications=existing_medications,
        )

        _safe_audit(
            db=db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            import_id=import_record.id,
            stage="COMPARISON",
            event_type="COMPARISON_COMPLETED",
            med_name_raw=med_name_raw,
            comparison_payload={
                "match_type": getattr(comparison, "match_type", None),
                "flags": getattr(comparison, "discrepancy_flags", None),
            },
        )

        item = MedReconciliationItem(
            id=uuid.uuid4(),
            import_id=import_record.id,
            tenant_id=tenant_id,
            patient_id=patient_id,
            list_type=list_type,
            med_name_raw=med_name_raw,
            med_name_normalized=med_name_normalized,
            dose=_clean_str(row.get("dose")),
            route=_clean_str(row.get("route")),
            frequency=_clean_str(row.get("frequency")),
            indication=_clean_str(row.get("indication")),
            dose_normalized=dose_normalized,
            route_normalized=route_normalized,
            frequency_normalized=frequency_normalized,
            signature_hash=signature_hash,
            reaction_description=_clean_str(row.get("reaction_description")),
            severity=_clean_str(row.get("severity")),
            reaction_category_suggested=_clean_str(row.get("reaction_category_suggested")),
            review_status="PENDING",
            created_at=now,
            updated_at=now,
        )

        item = evaluate_medication_safety(item)

        savepoint = db.begin_nested()
        try:
            db.add(item)
            db.flush()
            savepoint.commit()
        except IntegrityError as exc:
            savepoint.rollback()

            existing_duplicate = (
                db.query(MedReconciliationItem)
                .filter(MedReconciliationItem.patient_id == patient_id)
                .filter(MedReconciliationItem.review_status.in_(UNRESOLVED_REVIEW_STATUSES))
                .filter(MedReconciliationItem.signature_hash == signature_hash)
                .first()
            )

            logger.warning(
                "Duplicate med reconciliation item suppressed by DB constraint",
                extra={
                    "tenant_id": str(tenant_id),
                    "patient_id": str(patient_id),
                    "import_id": str(import_record.id),
                    "signature_hash": signature_hash,
                    "index_name": ACTIVE_MED_DEDUP_INDEX_NAME,
                },
            )

            duplicate_item_ids.append(
                str(existing_duplicate.id) if existing_duplicate else str(item.id)
            )

            _safe_audit(
                db=db,
                tenant_id=tenant_id,
                patient_id=patient_id,
                import_id=import_record.id,
                stage="DEDUP",
                event_type="DUPLICATE_DB_CONSTRAINT",
                med_name_raw=med_name_raw,
                normalized_payload={
                    **normalized,
                    "signature_hash": signature_hash,
                    "error": str(exc.orig) if getattr(exc, "orig", None) else str(exc),
                    "existing_item_id": str(existing_duplicate.id) if existing_duplicate else None,
                },
            )

            try:
                close_older_duplicate_tasks_when_one_duplicate_remains_active(
                    db=db,
                    patient_id=patient_id,
                    med_name_normalized=med_name_normalized,
                )
            except Exception as cleanup_exc:
                logger.exception(
                    "MED_RECON_TASK_DEDUP_CLEANUP_FAILED patient_id=%s med_name_normalized=%s error=%s",
                    str(patient_id),
                    med_name_normalized,
                    str(cleanup_exc),
                )

            continue

        created_items.append(item)
        item_ids.append(str(item.id))

        _safe_audit(
            db=db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            import_id=import_record.id,
            stage="DECISION",
            event_type="ITEM_CREATED",
            med_name_raw=med_name_raw,
            comparison_payload={
                "item_id": str(item.id),
                "match_type": getattr(comparison, "match_type", None),
                "flags": getattr(comparison, "discrepancy_flags", None),
                "signature_hash": signature_hash,
            },
        )

        try:
            task = create_reconciliation_task_if_needed(
                db=db,
                tenant_id=tenant_id,
                patient_id=patient_id,
                import_id=import_record.id,
                item_id=item.id,
                comparison=comparison,
            )

            if task is not None:
                task_item_ids.append(str(task.id))

            _safe_audit(
                db=db,
                tenant_id=tenant_id,
                patient_id=patient_id,
                import_id=import_record.id,
                stage="TASK",
                event_type="TASK_CREATED" if task else "TASK_SKIPPED",
                comparison_payload={
                    "item_id": str(item.id),
                    "task_id": str(task.id) if task else None,
                    "match_type": getattr(comparison, "match_type", None),
                    "flags": getattr(comparison, "discrepancy_flags", None),
                },
            )
        except Exception as task_exc:
            logger.exception(
                "MED_RECON_TASK_CREATE_FAILED patient_id=%s item_id=%s error=%s",
                str(patient_id),
                str(item.id),
                str(task_exc),
            )

            _safe_audit(
                db=db,
                tenant_id=tenant_id,
                patient_id=patient_id,
                import_id=import_record.id,
                stage="TASK",
                event_type="TASK_CREATE_FAILED",
                comparison_payload={
                    "item_id": str(item.id),
                    "error": str(task_exc),
                    "match_type": getattr(comparison, "match_type", None),
                    "flags": getattr(comparison, "discrepancy_flags", None),
                },
            )

        try:
            close_older_duplicate_tasks_when_one_duplicate_remains_active(
                db=db,
                patient_id=patient_id,
                med_name_normalized=med_name_normalized,
            )
        except Exception as cleanup_exc:
            logger.exception(
                "MED_RECON_TASK_DEDUP_CLEANUP_FAILED patient_id=%s med_name_normalized=%s error=%s",
                str(patient_id),
                med_name_normalized,
                str(cleanup_exc),
            )

            _safe_audit(
                db=db,
                tenant_id=tenant_id,
                patient_id=patient_id,
                import_id=import_record.id,
                stage="TASK",
                event_type="TASK_DEDUP_CLEANUP_FAILED",
                comparison_payload={
                    "item_id": str(item.id),
                    "error": str(cleanup_exc),
                    "med_name_normalized": med_name_normalized,
                },
            )

    import_record.updated_at = _utcnow()

    return {
        "status": import_record.status,
        "import_id": str(import_record.id),
        "items_created": len(created_items),
        "item_ids": item_ids,
        "task_item_ids": task_item_ids,
        "duplicate_item_ids": duplicate_item_ids,
    }