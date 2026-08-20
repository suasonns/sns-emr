from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.patient_access import get_authorized_patient
from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models.med_reconciliation import (
    MedReconciliationImport,
    MedReconciliationItem,
)
from app.models.medication import Medication

from app.services.med_reconciliation_import_service import create_import_with_items
from app.services.med_reconciliation_comparison import compare_imported_item_against_med_list
from app.services.med_reconciliation_normalizer import normalize_med_reconciliation_item
from app.services.reconciliation_task_service import (
    create_reconciliation_task_if_needed,
    complete_reconciliation_review_task_if_exists,
)
from app.services.med_safety import evaluate_medication_safety

router = APIRouter(
    prefix="/med-reconciliation",
    tags=["med-reconciliation"],
)

VALID_SOURCE_TYPES = {"PDF", "CCD", "C-CDA", "SCANNED_DOC", "MANUAL"}
VALID_SOURCE_CONTEXTS = {"HOSPITAL_DISCHARGE", "ED_VISIT", "INPATIENT_STAY", "OTHER"}
VALID_LIST_TYPES = {"INPATIENT_HISTORY", "DISCHARGE_LIST"}
VALID_SEVERITY = {"MILD", "MODERATE", "SEVERE"}
VALID_REVIEW_STATUSES = {"PENDING", "REVIEWED", "ACCEPTED", "REJECTED"}


# =====================================================
# HELPERS
# =====================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}") from exc


def _existing_medications_payload_for_patient(
    db: Session,
    patient_id: uuid.UUID,
):
    """
    Build a comparison-friendly medication payload list from active meds.
    """
    meds = (
        db.query(Medication)
        .filter(Medication.patient_id == patient_id)
        .filter(Medication.is_active == True)  # noqa: E712
        .all()
    )

    payload = []
    for med in meds:
        payload.append(
            {
                "id": med.id,
                "medication_name": med.medication_name,
                "canonical_name": med.canonical_name,
                "dose": med.dosage,
                "dose_normalized": getattr(med, "dose_normalized", med.dosage),
                "route_normalized": getattr(med, "route_normalized", med.route),
                "frequency_normalized": getattr(med, "frequency_normalized", med.frequency),
            }
        )
    return payload


def _apply_comparison_fields_if_present(item: MedReconciliationItem, comparison) -> None:
    """
    Safely populate comparison-related model fields only if the ORM class currently includes them.
    This prevents runtime errors if DB migration is ahead of ORM model update.
    """
    if hasattr(item, "comparison_status"):
        setattr(item, "comparison_status", comparison.match_type)

    if hasattr(item, "comparison_flags"):
        setattr(item, "comparison_flags", comparison.discrepancy_flags)

    if hasattr(item, "matched_medication_id"):
        matched_id = comparison.existing_medication_id
        setattr(item, "matched_medication_id", matched_id)

    if hasattr(item, "comparison_review_reason"):
        setattr(item, "comparison_review_reason", comparison.review_reason)

    if hasattr(item, "dose_normalized"):
        setattr(item, "dose_normalized", comparison.imported_dose_normalized)

    if hasattr(item, "route_normalized"):
        setattr(item, "route_normalized", comparison.imported_route_normalized)

    if hasattr(item, "frequency_normalized"):
        setattr(item, "frequency_normalized", comparison.imported_frequency_normalized)


# =====================================================
# SCHEMAS
# =====================================================

class MedReconciliationImportCreate(BaseModel):
    tenant_id: str = Field(..., description="Tenant UUID")
    patient_id: str = Field(..., description="Patient UUID")
    source_type: str = Field(..., description="PDF | CCD | C-CDA | SCANNED_DOC | MANUAL")
    source_context: str = Field(..., description="HOSPITAL_DISCHARGE | ED_VISIT | INPATIENT_STAY | OTHER")
    source_file_name: Optional[str] = Field(default=None)
    uploaded_by: Optional[str] = Field(default=None)
    raw_summary: Optional[str] = Field(default=None)

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class MedReconciliationImportResponse(BaseModel):
    status: str
    import_id: str

    model_config = {"extra": "forbid"}


class MedReconciliationImportListItem(BaseModel):
    id: str
    tenant_id: str
    patient_id: str
    source_type: str
    source_context: str
    status: str
    source_file_name: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    parsed_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    raw_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "extra": "forbid",
        "from_attributes": True,
    }


class MedReconciliationImportListResponse(BaseModel):
    count: int
    items: List[MedReconciliationImportListItem]

    model_config = {"extra": "forbid"}


class MedReconciliationItemCreate(BaseModel):
    import_id: str
    tenant_id: str
    patient_id: str
    list_type: str
    med_name_raw: str
    med_name_normalized: Optional[str] = None
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    indication: Optional[str] = None
    reaction_description: Optional[str] = None
    severity: Optional[str] = None
    reaction_category_suggested: Optional[str] = None
    reaction_category_final: Optional[str] = None
    is_discharge_candidate: bool = False
    requires_immediate_review: bool = False
    is_critical_reaction: bool = False
    notes: Optional[str] = None

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class MedReconciliationItemResponse(BaseModel):
    status: str
    item_id: str

    model_config = {"extra": "forbid"}


class MedReconciliationReviewCompleteResponse(BaseModel):
    status: str
    item_id: str
    review_status: str

    model_config = {"extra": "forbid"}


class MedReconciliationPriorDuplicateDetail(BaseModel):
    incoming_med_name_raw: str
    incoming_med_name_normalized: Optional[str] = None
    existing_item_id: str
    existing_import_id: str
    existing_review_status: str
    existing_med_name_raw: Optional[str] = None
    existing_created_at: Optional[str] = None

    model_config = {
        "extra": "forbid",
    }


class MedReconciliationAutoImportRow(BaseModel):
    list_type: str = "DISCHARGE_LIST"
    med_name_raw: str
    med_name_normalized: Optional[str] = None
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    indication: Optional[str] = None
    reaction_description: Optional[str] = None
    severity: Optional[str] = None
    reaction_category_suggested: Optional[str] = None
    reaction_category_final: Optional[str] = None
    is_discharge_candidate: bool = False
    requires_immediate_review: bool = False
    is_critical_reaction: bool = False
    notes: Optional[str] = None

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class MedReconciliationAutoImportRequest(BaseModel):
    tenant_id: str = Field(..., description="Tenant UUID")
    patient_id: str = Field(..., description="Patient UUID")
    source_type: str = Field(
        default="MANUAL",
        description="PDF | CCD | C-CDA | SCANNED_DOC | MANUAL",
    )
    source_context: str = Field(
        default="OTHER",
        description="HOSPITAL_DISCHARGE | ED_VISIT | INPATIENT_STAY | OTHER",
    )
    source_file_name: Optional[str] = Field(default=None)
    uploaded_by: Optional[str] = Field(default=None, description="User UUID")
    raw_summary: Optional[str] = Field(default=None)
    medications: List[MedReconciliationAutoImportRow]

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class MedReconciliationAutoImportResponse(BaseModel):
    status: str
    import_id: str

    items_created: int
    item_ids: List[str]

    task_item_ids: List[str] = Field(default_factory=list)
    auto_accepted_item_ids: List[str] = Field(default_factory=list)

    duplicate_item_ids: List[str] = Field(default_factory=list)
    duplicate_details: List[MedReconciliationPriorDuplicateDetail] = Field(default_factory=list)

    # ✅ expose automatic backlog-collapse results
    dedup_collapsed_item_ids: List[str] = Field(default_factory=list)
    dedup_closed_task_ids: List[str] = Field(default_factory=list)

    model_config = {
        "extra": "forbid",
    }


# =====================================================
# ROUTES
# =====================================================

@router.get("/health")
def med_reconciliation_health():
    return {"status": "ok"}


@router.post("/imports", response_model=MedReconciliationImportResponse)
def create_med_reconciliation_import(
    payload: MedReconciliationImportCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if payload.source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid source_type")

    if payload.source_context not in VALID_SOURCE_CONTEXTS:
        raise HTTPException(status_code=400, detail="Invalid source_context")

    tenant_uuid = _parse_uuid(payload.tenant_id, "tenant_id")
    patient_uuid = _parse_uuid(payload.patient_id, "patient_id")
    get_authorized_patient(db, patient_uuid, user)
    if tenant_uuid != user.tenant_id:
        raise HTTPException(status_code=404, detail="Patient not found")

    uploaded_by_uuid = (
        _parse_uuid(payload.uploaded_by, "uploaded_by") if payload.uploaded_by else None
    )

    now = _utcnow()

    try:
        record = MedReconciliationImport(
            id=uuid.uuid4(),
            tenant_id=tenant_uuid,
            patient_id=patient_uuid,
            source_type=payload.source_type,
            source_context=payload.source_context,
            status="PENDING_REVIEW",
            source_file_name=payload.source_file_name,
            uploaded_by=uploaded_by_uuid,
            uploaded_at=now,
            raw_summary=payload.raw_summary,
            created_at=now,
            updated_at=now,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return MedReconciliationImportResponse(
            status="CREATED",
            import_id=str(record.id),
        )

    except IntegrityError as exc:
        db.rollback()
        orig = getattr(exc, "orig", None)
        detail = str(orig) if orig else "Database integrity error"
        raise HTTPException(status_code=400, detail=f"Integrity error: {detail}")

    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(exc)}")


@router.get("/imports", response_model=MedReconciliationImportListResponse)
def list_med_reconciliation_imports(
    patient_id: Optional[str] = Query(default=None),
    tenant_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    query = db.query(MedReconciliationImport).filter(
        MedReconciliationImport.tenant_id == user.tenant_id
    )

    if patient_id:
        patient_uuid = _parse_uuid(patient_id, "patient_id")
        get_authorized_patient(db, patient_uuid, user)
        query = query.filter(
            MedReconciliationImport.patient_id == patient_uuid
        )

    if tenant_id:
        tenant_uuid = _parse_uuid(tenant_id, "tenant_id")
        query = query.filter(
            MedReconciliationImport.tenant_id == tenant_uuid
        )

    if status:
        query = query.filter(MedReconciliationImport.status == status)

    records = (
        query.order_by(MedReconciliationImport.uploaded_at.desc())
        .limit(limit)
        .all()
    )

    items = [
        MedReconciliationImportListItem.model_validate(record)
        for record in records
    ]

    return MedReconciliationImportListResponse(count=len(items), items=items)


@router.post(
    "/import-auto",
    response_model=MedReconciliationAutoImportResponse,
)
def create_med_reconciliation_import_auto(
    payload: MedReconciliationAutoImportRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Production-grade Med Reconciliation import.

    Features:
    - validates input before DB writes
    - creates import + reconciliation items
    - auto-accepts clean matches
    - creates tasks only for discrepancy / safety review
    - surfaces prior unresolved duplicates instead of creating more noise
    - exposes automatic backlog collapse results
    - commits only after successful service execution
    """

    # -----------------------------------------------------
    # STEP 1 — VALIDATION
    # -----------------------------------------------------
    if payload.source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_type '{payload.source_type}'",
        )

    if payload.source_context not in VALID_SOURCE_CONTEXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_context '{payload.source_context}'",
        )

    if not payload.medications:
        raise HTTPException(
            status_code=400,
            detail="medications is required",
        )

    tenant_uuid = _parse_uuid(payload.tenant_id, "tenant_id")
    patient_uuid = _parse_uuid(payload.patient_id, "patient_id")
    get_authorized_patient(db, patient_uuid, user)
    if tenant_uuid != user.tenant_id:
        raise HTTPException(status_code=404, detail="Patient not found")

    uploaded_by_uuid = (
        _parse_uuid(payload.uploaded_by, "uploaded_by")
        if payload.uploaded_by else None
    )

    # -----------------------------------------------------
    # STEP 2 — PER-ROW VALIDATION
    # -----------------------------------------------------
    for idx, med in enumerate(payload.medications):
        list_type = (med.list_type or "").strip().upper()

        if list_type not in VALID_LIST_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid list_type '{list_type}' at medications[{idx}]",
            )

        if not (med.med_name_raw or "").strip():
            raise HTTPException(
                status_code=400,
                detail=f"med_name_raw is required at medications[{idx}]",
            )

        if med.severity and med.severity not in VALID_SEVERITY:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity '{med.severity}' at medications[{idx}]",
            )

    # -----------------------------------------------------
    # STEP 3 — SERVICE EXECUTION
    # -----------------------------------------------------
    try:
        result = create_import_with_items(
            db=db,
            tenant_id=tenant_uuid,
            patient_id=patient_uuid,
            source_type=payload.source_type,
            source_context=payload.source_context,
            source_file_name=payload.source_file_name,
            uploaded_by=uploaded_by_uuid,
            raw_summary=payload.raw_summary,
            medications=[m.model_dump() for m in payload.medications],
        )

        db.commit()

        return MedReconciliationAutoImportResponse(
            status=result["status"],
            import_id=result["import_id"],
            items_created=result["items_created"],
            item_ids=result["item_ids"],
            task_item_ids=result.get("task_item_ids", []),
            auto_accepted_item_ids=result.get("auto_accepted_item_ids", []),
            duplicate_item_ids=result.get("duplicate_item_ids", []),
            duplicate_details=[
                MedReconciliationPriorDuplicateDetail(**d)
                for d in result.get("duplicate_details", [])
            ],
            dedup_collapsed_item_ids=result.get("dedup_collapsed_item_ids", []),
            dedup_closed_task_ids=result.get("dedup_closed_task_ids", []),
        )

    except IntegrityError as exc:
        db.rollback()
        orig = getattr(exc, "orig", None)
        detail = str(getattr(orig, "pgerror", orig)) if orig else "Database integrity error"
        raise HTTPException(
            status_code=400,
            detail=f"Integrity error: {detail}",
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during med reconciliation import: {str(exc)}",
        )


@router.post("/items", response_model=MedReconciliationItemResponse)
def create_med_reconciliation_item(
    payload: MedReconciliationItemCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if payload.list_type not in VALID_LIST_TYPES:
        raise HTTPException(status_code=400, detail="Invalid list_type")

    if payload.severity and payload.severity not in VALID_SEVERITY:
        raise HTTPException(status_code=400, detail="Invalid severity")

    import_uuid = _parse_uuid(payload.import_id, "import_id")
    tenant_uuid = _parse_uuid(payload.tenant_id, "tenant_id")
    patient_uuid = _parse_uuid(payload.patient_id, "patient_id")
    get_authorized_patient(db, patient_uuid, user)
    if tenant_uuid != user.tenant_id:
        raise HTTPException(status_code=404, detail="Patient not found")

    parent_import = (
        db.query(MedReconciliationImport)
        .filter(MedReconciliationImport.id == import_uuid)
        .first()
    )

    if not parent_import:
        raise HTTPException(status_code=404, detail="Import not found")

    if parent_import.tenant_id != tenant_uuid:
        raise HTTPException(status_code=400, detail="tenant mismatch")

    if parent_import.patient_id != patient_uuid:
        raise HTTPException(status_code=400, detail="patient mismatch")

    now = _utcnow()

    try:
        # -----------------------------------------------------
        # NORMALIZE INPUT
        # -----------------------------------------------------
        normalized = normalize_med_reconciliation_item(
            med_name_raw=payload.med_name_raw,
            dose=payload.dose,
            route=payload.route,
            frequency=payload.frequency,
        )

        med_name_normalized = (
            payload.med_name_normalized or normalized["med_name_normalized"]
        )
        dose_normalized = normalized["dose_normalized"]
        route_normalized = normalized["route_normalized"]
        frequency_normalized = normalized["frequency_normalized"]

        # -----------------------------------------------------
        # COMPARE AGAINST ACTIVE MEDS
        # -----------------------------------------------------
        existing_medications = _existing_medications_payload_for_patient(
            db=db,
            patient_id=patient_uuid,
        )

        comparison = compare_imported_item_against_med_list(
            imported_item={
                "med_name_raw": payload.med_name_raw,
                "med_name_normalized": med_name_normalized,
                "dose": payload.dose,
                "dose_normalized": dose_normalized,
                "route_normalized": route_normalized,
                "frequency_normalized": frequency_normalized,
            },
            existing_medications=existing_medications,
        )

        review_status = (
            "ACCEPTED"
            if str(getattr(comparison, "match_type", "")).upper()
            == "EXACT_NORMALIZED_MATCH"
            else "PENDING"
        )

        # -----------------------------------------------------
        # BUILD ITEM
        # -----------------------------------------------------
        item = MedReconciliationItem(
            id=uuid.uuid4(),
            import_id=import_uuid,
            tenant_id=tenant_uuid,
            patient_id=patient_uuid,
            list_type=payload.list_type,
            med_name_raw=payload.med_name_raw,
            med_name_normalized=med_name_normalized,
            dose=payload.dose,
            route=payload.route,
            frequency=payload.frequency,
            indication=payload.indication,
            reaction_description=payload.reaction_description,
            severity=payload.severity,
            reaction_category_suggested=payload.reaction_category_suggested,
            reaction_category_final=payload.reaction_category_final,
            is_discharge_candidate=payload.is_discharge_candidate,
            requires_immediate_review=payload.requires_immediate_review,
            is_critical_reaction=payload.is_critical_reaction,
            review_status=review_status,
            notes=payload.notes,
            created_at=now,
            updated_at=now,
        )

        _apply_comparison_fields_if_present(item, comparison)
        item = evaluate_medication_safety(item)

        # -----------------------------------------------------
        # INSERT WITH SAVEPOINT (RACE SAFE)
        # -----------------------------------------------------
        try:
            with db.begin_nested():
                db.add(item)
                db.flush()

                if review_status == "PENDING":
                    create_reconciliation_task_if_needed(
                        db=db,
                        tenant_id=item.tenant_id,
                        patient_id=item.patient_id,
                        reconciliation_item_id=item.id,
                        review_reason=getattr(comparison, "review_reason", None),
                    )

        except IntegrityError as exc:
            # ✅ HANDLE UNIQUE INDEX (DUPLICATE)
            if "uq_med_recon_active_patient_mednorm" in str(exc):

                existing = (
                    db.query(MedReconciliationItem)
                    .filter(MedReconciliationItem.patient_id == patient_uuid)
                    .filter(MedReconciliationItem.review_status == "PENDING")
                    .filter(
                        MedReconciliationItem.med_name_normalized
                        == med_name_normalized
                    )
                    .order_by(MedReconciliationItem.created_at.desc())
                    .first()
                )

                if existing:
                    return MedReconciliationItemResponse(
                        status="DUPLICATE_SUPPRESSED",
                        item_id=str(existing.id),
                    )

            # unknown integrity error → propagate
            raise

        db.commit()
        db.refresh(item)

        return MedReconciliationItemResponse(
            status="ITEM_CREATED",
            item_id=str(item.id),
        )

    except IntegrityError as exc:
        db.rollback()
        orig = getattr(exc, "orig", None)
        detail = str(orig) if orig else "Database integrity error"
        raise HTTPException(
            status_code=400,
            detail=f"Integrity error: {detail}",
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(exc)}",
        )

@router.post("/items/{item_id}/review", response_model=MedReconciliationReviewCompleteResponse)
def complete_reconciliation_review(
    item_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    item_uuid = _parse_uuid(item_id, "item_id")

    item = (
        db.query(MedReconciliationItem)
        .filter(MedReconciliationItem.id == item_uuid)
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    get_authorized_patient(db, item.patient_id, user)

    try:
        item.review_status = "REVIEWED"
        item.updated_at = _utcnow()

        complete_reconciliation_review_task_if_exists(
            db=db,
            reconciliation_item_id=item.id,
            completion_reference_type="MED_RECON_ITEM",
            completion_reference_id=item.id,
        )

        db.commit()
        db.refresh(item)

        return MedReconciliationReviewCompleteResponse(
            status="REVIEW_COMPLETED",
            item_id=str(item.id),
            review_status=item.review_status,
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(exc)}")