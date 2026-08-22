# app/services/diagnosis_sync_service.py

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.patient_diagnosis import PatientDiagnosis
from app.models.enums import (
    DiagnosisSource,
    DiagnosisStatus,
    DiagnosisType,
)
from app.services.icd10_resolver_service import (
    ICD10ResolutionError,
    resolve_icd10_diagnosis_for_use,
)

from app.services.poc_rule_loader import (
    validate_primary_diagnosis_rule,
)


# =========================================================
# DIAGNOSIS SYNC SERVICE
# =========================================================
#
# Governance:
#
# ICD10 master + hospice policy
#     = Single source of truth for ICD10 identity and allowed use.
#
# PatientDiagnosis
#     = Authoritative patient diagnosis record and diagnosis history.
#
# Patient.primary_diagnosis
#     = Legacy/cache/display mirror used by existing clinical,
#       billing, POC, certification, recertification, NOE,
#       and claim workflows until all downstream modules consume
#       patient_diagnoses directly.
#
# PatientFaceSheet.primary_diagnosis
#     = Operational display / mirror copy.
#
# Facesheet may contain referral/intake diagnosis before RN ICA.
#
# After RN ICA / CTI / Recert / MD update:
#     - ICD10 resolver validates the diagnosis first
#     - patient_diagnoses is updated first
#     - Patient.primary_diagnosis mirrors display_name
#     - PatientFaceSheet.primary_diagnosis mirrors display_name
#
# IMPORTANT:
# - This service does NOT commit.
# - Caller owns transaction boundary.
# - This service is safe to call from:
#       RN ICA finalize
#       CTI finalize
#       Recert finalize
#       Medical Director diagnosis update
# - If a facesheet row is missing, this service creates a minimal
#   patient_facesheet row as a chart-integrity failsafe.
# - Patient identity is sourced only from PatientFaceSheet
#   first_name / middle_name / last_name.
# - This service must not reconstruct patient identity from legacy
#   patient-level name fields.
# - If a facesheet row is missing, this service may create a minimal
#   diagnosis mirror row only if the PatientFaceSheet database model
#   allows that shape; otherwise caller must create facesheet first.
# =========================================================


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None

    text_value = str(value).strip()

    if not text_value:
        return None

    return text_value


def _clean_source(value: Any) -> str:
    if value is None:
        return "UNKNOWN"

    text_value = str(value).strip().upper()

    if not text_value:
        return "UNKNOWN"

    return text_value


def _diagnosis_source_from_value(value: Any) -> DiagnosisSource:
    """
    Convert caller source text into DiagnosisSource enum.

    Accepted examples:
        REFERRAL
        RN_ICA
        SPECIALIST
        ATTENDING_PHYSICIAN
        MEDICAL_DIRECTOR
        CTI
        RECERT
        MD

    If source is unknown, default to RN_ICA because this service
    is most commonly called from finalized clinical assessment flows.
    """

    cleaned = _clean_source(value)

    if cleaned in DiagnosisSource.__members__:
        return DiagnosisSource[cleaned]

    for enum_item in DiagnosisSource:
        if str(enum_item.value).upper() == cleaned:
            return enum_item

    return DiagnosisSource.RN_ICA


def _workflow_context_from_diagnosis_source(
    source: DiagnosisSource,
) -> str:
    """
    Map diagnosis source to ICD10 hospice workflow context.

    The ICD10 resolver validates by workflow context:
        REFERRAL
        RN_ICA
        CTI
        POC
        FACESHEET

    This helper prevents workflow strings from being scattered across
    calling code.
    """

    source_value = getattr(source, "value", source)
    source_text = str(source_value or "").strip().upper()

    if source_text == "REFERRAL":
        return "REFERRAL"

    if source_text == "RN_ICA":
        return "RN_ICA"

    if source_text == "CTI":
        return "CTI"

    return "RN_ICA"


def _resolve_actor_id(
    *,
    patient: Patient,
    updated_by,
):
    """
    Resolve audit actor.

    Priority:
        1. Explicit updated_by supplied by caller
        2. Patient.created_by fallback

    If neither exists, synchronization returns a safe failure result.
    """

    if updated_by is not None:
        return updated_by

    patient_created_by = getattr(patient, "created_by", None)

    if patient_created_by is not None:
        return patient_created_by

    return None

def _diagnosis_failure_result(
    *,
    reason: str,
    source: str,
    patient_id,
    detail: str | None = None,
) -> dict[str, Any]:
    """
    Standard failure result for diagnosis synchronization.

    Keeps callers/logs consistent and prevents partial assumptions.
    """

    result = {
        "synced": False,
        "reason": reason,
        "source": source,
        "patient_id": (
            str(patient_id)
            if patient_id is not None
            else None
        ),
        "facesheet_updated": False,
        "facesheet_created": False,
        "facesheet_identity_backfilled": False,
        "patient_diagnosis_created": False,
        "previous_diagnosis_historical": False,
        "previous_patient_diagnosis_id": None,
        "active_patient_diagnosis_id": None,
    }

    if detail:
        result["detail"] = detail

    return result


def _same_active_primary(
    diagnosis: PatientDiagnosis | None,
    *,
    icd10_code: str,
    diagnosis_description: str,
    display_name: str,
    source: DiagnosisSource,
) -> bool:
    if diagnosis is None:
        return False

    return (
        diagnosis.icd10_code == icd10_code
        and diagnosis.diagnosis_description == diagnosis_description
        and diagnosis.display_name == display_name
        and diagnosis.source == source
        and diagnosis.status == DiagnosisStatus.ACTIVE
        and diagnosis.active is True
        and diagnosis.resolved_date is None
    )


def _get_current_active_primary_diagnosis(
    db: Session,
    *,
    tenant_id,
    patient_id,
) -> PatientDiagnosis | None:
    return (
        db.query(PatientDiagnosis)
        .filter(
            PatientDiagnosis.tenant_id == tenant_id,
            PatientDiagnosis.patient_id == patient_id,
            PatientDiagnosis.diagnosis_type == DiagnosisType.PRIMARY,
            PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
            PatientDiagnosis.active.is_(True),
            PatientDiagnosis.resolved_date.is_(None),
        )
        .with_for_update()
        .order_by(PatientDiagnosis.created_at.desc())
        .first()
    )


def _create_or_transition_primary_diagnosis(
    db: Session,
    *,
    tenant_id,
    patient_id,
    normalized_diagnosis: dict[str, str],
    source: DiagnosisSource,
    actor_id,
    now: datetime,
) -> dict[str, Any]:
    """
    Create authoritative PatientDiagnosis row.

    If a different active primary exists:
        - old row becomes HISTORICAL
        - old row active = False
        - old row resolved_date = today

    If the same active primary already exists for the same source:
        - do not duplicate
    """

    current_primary = _get_current_active_primary_diagnosis(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    icd10_code = normalized_diagnosis["icd10_code"]
    diagnosis_description = normalized_diagnosis[
        "diagnosis_description"
    ]
    display_name = normalized_diagnosis["display_name"]

    if _same_active_primary(
        current_primary,
        icd10_code=icd10_code,
        diagnosis_description=diagnosis_description,
        display_name=display_name,
        source=source,
    ):
        current_primary.updated_by = actor_id
        current_primary.updated_at = now

        return {
            "patient_diagnosis_created": False,
            "previous_diagnosis_historical": False,
            "previous_patient_diagnosis_id": None,
            "active_patient_diagnosis_id": str(current_primary.id),
        }

    previous_diagnosis_id = None

    if current_primary is not None:
        previous_diagnosis_id = str(current_primary.id)

        current_primary.status = DiagnosisStatus.HISTORICAL
        current_primary.active = False
        current_primary.resolved_date = date.today()
        current_primary.updated_by = actor_id
        current_primary.updated_at = now

        db.flush()

    new_diagnosis = PatientDiagnosis(
        tenant_id=tenant_id,
        patient_id=patient_id,
        diagnosis_type=DiagnosisType.PRIMARY,
        status=DiagnosisStatus.ACTIVE,
        source=source,
        icd10_code=icd10_code,
        diagnosis_description=diagnosis_description,
        display_name=display_name,
        active=True,
        is_terminal=True,
        is_related_to_terminal=True,
        effective_date=date.today(),
        created_by=actor_id,
        change_reason=(
            f"Primary diagnosis synchronized from {source.value}"
        ),
    )

    db.add(new_diagnosis)
    db.flush()

    return {
        "patient_diagnosis_created": True,
        "previous_diagnosis_historical": current_primary is not None,
        "previous_patient_diagnosis_id": previous_diagnosis_id,
        "active_patient_diagnosis_id": str(new_diagnosis.id),
    }


def sync_official_primary_diagnosis(
    db: Session,
    *,
    tenant_id,
    patient_id,
    primary_diagnosis: Any,
    source: str,
    updated_by=None,
) -> dict[str, Any]:
    """
    Synchronize official hospice primary diagnosis.

    Responsibilities:
        1. Resolve and validate incoming primary diagnosis through ICD10 SSOT.
        2. Update patient_diagnoses authoritative record.
        3. Mirror display_name to Patient.primary_diagnosis.
        4. Mirror display_name to PatientFaceSheet.primary_diagnosis.

    This function intentionally does NOT commit.

    Caller owns transaction boundary.
    """

    normalized_source_text = _clean_source(source)
    diagnosis_source = _diagnosis_source_from_value(source)

    try:
        resolved_diagnosis = resolve_icd10_diagnosis_for_use(
            db,
            diagnosis_input=primary_diagnosis,
            diagnosis_role="PRIMARY",
            workflow_context=_workflow_context_from_diagnosis_source(
                diagnosis_source
            ),
        )

        normalized_diagnosis = {
            "icd10_code": resolved_diagnosis.icd10_code,
            "diagnosis_description": (
                resolved_diagnosis.diagnosis_description
            ),
            "display_name": resolved_diagnosis.display_name,
        }
        
        allowed, governance_reason = (
            validate_primary_diagnosis_rule(
                resolved_diagnosis.icd10_code
            )
        )

        if not allowed:
            return _diagnosis_failure_result(
                reason="PRIMARY_DIAGNOSIS_BLOCKED",
                detail=(
                    f"{resolved_diagnosis.icd10_code} "
                    f"is not eligible as a Primary Hospice Diagnosis. "
                    f"Governance Rule: {governance_reason}"
                ),
                source=normalized_source_text,
                patient_id=patient_id,
            )
    except ICD10ResolutionError as exc:
        return _diagnosis_failure_result(
            reason="ICD10_RESOLUTION_FAILED",
            detail=str(exc),
            source=normalized_source_text,
            patient_id=patient_id,
        )

    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.tenant_id == tenant_id,
        )
        .with_for_update()
        .first()
    )

    if not patient:
        return _diagnosis_failure_result(
            reason="PATIENT_NOT_FOUND",
            source=normalized_source_text,
            patient_id=patient_id,
        )

    now = datetime.now(timezone.utc)

    actor_id = _resolve_actor_id(
        patient=patient,
        updated_by=updated_by,
    )

    if actor_id is None:
        return _diagnosis_failure_result(
            reason="MISSING_ACTOR_FOR_AUDIT_FIELDS",
            source=normalized_source_text,
            patient_id=patient.id,
        )

    diagnosis_result = _create_or_transition_primary_diagnosis(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
        normalized_diagnosis=normalized_diagnosis,
        source=diagnosis_source,
        actor_id=actor_id,
        now=now,
    )

    display_name = normalized_diagnosis["display_name"]

    previous_patient_dx = getattr(
        patient,
        "primary_diagnosis",
        None,
    )

    patient.primary_diagnosis = display_name

    if hasattr(patient, "updated_at"):
        patient.updated_at = now

    if hasattr(patient, "updated_by"):
        patient.updated_by = actor_id

    facesheet = (
        db.query(PatientFaceSheet)
        .filter(
            PatientFaceSheet.patient_id == patient.id,
        )
        .with_for_update()
        .first()
    )

    previous_facesheet_dx = None
    facesheet_updated = False
    facesheet_created = False
    facesheet_identity_backfilled = False

    if not facesheet:
        facesheet = PatientFaceSheet(
            patient_id=patient.id,
            dob=getattr(patient, "date_of_birth", None),
            primary_diagnosis=display_name,
            created_by=actor_id,
            updated_by=actor_id,
            updated_at=now,
        )

        db.add(facesheet)

        facesheet_created = True
        facesheet_updated = True
        facesheet_identity_backfilled = False

    else:
        previous_facesheet_dx = getattr(
            facesheet,
            "primary_diagnosis",
            None,
        )

        facesheet.primary_diagnosis = display_name
        facesheet_updated = True
        facesheet_identity_backfilled = False

        if hasattr(facesheet, "updated_at"):
            facesheet.updated_at = now

        if hasattr(facesheet, "updated_by"):
            facesheet.updated_by = actor_id

    return {
        "synced": True,
        "source": normalized_source_text,
        "patient_id": str(patient.id),
        "primary_diagnosis": display_name,
        "icd10_code": normalized_diagnosis["icd10_code"],
        "diagnosis_description": normalized_diagnosis[
            "diagnosis_description"
        ],
        "previous_patient_primary_diagnosis": previous_patient_dx,
        "previous_facesheet_primary_diagnosis": previous_facesheet_dx,
        "facesheet_updated": facesheet_updated,
        "facesheet_created": facesheet_created,
        "facesheet_identity_backfilled": facesheet_identity_backfilled,
        **diagnosis_result,
    }


# =========================================================
# SECONDARY / COMORBIDITY DIAGNOSIS SYNC
# =========================================================
#
# Synchronizes non-primary diagnoses (SECONDARY, with a RELATED/UNRELATED
# classification, and COMORBIDITY) into the authoritative patient_diagnoses
# table. Designed to be called from any module that captures these
# diagnoses (RN ICA, Recert, Facesheet) so there is exactly ONE shared list
# instead of a per-module copy.
#
# Safety posture: this function only ADDS or UPDATES rows. It never
# deactivates/retires a diagnosis the caller's payload happens to omit,
# because a partial or in-progress form save must never silently make an
# active diagnosis disappear from the chart. Retiring a diagnosis is a
# deliberate clinical action and must go through an explicit removal path.
# =========================================================


def _format_diagnosis_input(item: dict[str, Any]) -> str | None:
    icd10 = _clean_text(item.get("icd10") or item.get("code"))
    description = _clean_text(
        item.get("description") or item.get("name") or item.get("label")
    )

    if description and icd10:
        return f"{description} ({icd10})"

    return description or icd10


def _sync_one_non_primary_diagnosis(
    db: Session,
    *,
    tenant_id,
    patient_id,
    item: dict[str, Any],
    diagnosis_type: DiagnosisType,
    diagnosis_role: str,
    source: DiagnosisSource,
    workflow_context: str,
    actor_id,
    now: datetime,
) -> dict[str, Any]:
    diagnosis_input = _format_diagnosis_input(item)

    if not diagnosis_input:
        return {"skipped": True, "reason": "EMPTY_DIAGNOSIS_INPUT"}

    try:
        resolved = resolve_icd10_diagnosis_for_use(
            db,
            diagnosis_input=diagnosis_input,
            diagnosis_role=diagnosis_role,
            workflow_context=workflow_context,
        )
    except ICD10ResolutionError as exc:
        return {
            "skipped": True,
            "reason": "ICD10_RESOLUTION_FAILED",
            "detail": str(exc),
            "input": diagnosis_input,
        }

    relationship = str(
        item.get("relationship") or item.get("classification") or ""
    ).strip().upper()
    is_related_to_terminal = relationship != "UNRELATED"

    existing = (
        db.query(PatientDiagnosis)
        .filter(
            PatientDiagnosis.tenant_id == tenant_id,
            PatientDiagnosis.patient_id == patient_id,
            PatientDiagnosis.diagnosis_type == diagnosis_type,
            PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
            PatientDiagnosis.active.is_(True),
            PatientDiagnosis.resolved_date.is_(None),
            PatientDiagnosis.icd10_code == resolved.icd10_code,
        )
        .first()
    )

    if existing:
        existing.diagnosis_description = resolved.diagnosis_description
        existing.display_name = resolved.display_name
        if diagnosis_type == DiagnosisType.SECONDARY:
            existing.is_related_to_terminal = is_related_to_terminal
        existing.updated_by = actor_id
        existing.updated_at = now

        return {
            "skipped": False,
            "created": False,
            "icd10_code": resolved.icd10_code,
            "diagnosis_id": str(existing.id),
        }

    new_diagnosis = PatientDiagnosis(
        tenant_id=tenant_id,
        patient_id=patient_id,
        diagnosis_type=diagnosis_type,
        status=DiagnosisStatus.ACTIVE,
        source=source,
        icd10_code=resolved.icd10_code,
        diagnosis_description=resolved.diagnosis_description,
        display_name=resolved.display_name,
        active=True,
        is_terminal=False,
        is_related_to_terminal=(
            is_related_to_terminal
            if diagnosis_type == DiagnosisType.SECONDARY
            else False
        ),
        effective_date=date.today(),
        created_by=actor_id,
        change_reason=f"Synchronized from {source.value}",
    )

    db.add(new_diagnosis)
    db.flush()

    return {
        "skipped": False,
        "created": True,
        "icd10_code": resolved.icd10_code,
        "diagnosis_id": str(new_diagnosis.id),
    }


def sync_secondary_and_comorbidity_diagnoses(
    db: Session,
    *,
    tenant_id,
    patient_id,
    secondary_items: list[dict] | None,
    comorbidity_items: list[dict] | None,
    source: str,
    updated_by=None,
) -> dict[str, Any]:
    """
    Synchronize secondary (related/unrelated) and comorbidity diagnoses into
    the authoritative patient_diagnoses table.

    secondary_items / comorbidity_items: list of dicts shaped like
        {"icd10": "I50.9", "description": "...", "relationship": "RELATED"|"UNRELATED"}
    (relationship only meaningful for secondary_items; defaults to RELATED).

    This function intentionally does NOT commit. Caller owns the
    transaction boundary. Items that fail ICD10 resolution are skipped
    (reported in the result) rather than aborting the whole save, so a
    single bad entry cannot block an otherwise valid clinical save.
    """

    diagnosis_source = _diagnosis_source_from_value(source)
    workflow_context = _workflow_context_from_diagnosis_source(diagnosis_source)

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .first()
    )

    if not patient:
        return {
            "synced": False,
            "reason": "PATIENT_NOT_FOUND",
            "patient_id": str(patient_id) if patient_id else None,
        }

    now = datetime.now(timezone.utc)
    actor_id = _resolve_actor_id(patient=patient, updated_by=updated_by)

    if actor_id is None:
        return {
            "synced": False,
            "reason": "MISSING_ACTOR_FOR_AUDIT_FIELDS",
            "patient_id": str(patient.id),
        }

    secondary_results = [
        _sync_one_non_primary_diagnosis(
            db,
            tenant_id=tenant_id,
            patient_id=patient.id,
            item=item,
            diagnosis_type=DiagnosisType.SECONDARY,
            diagnosis_role="SECONDARY",
            source=diagnosis_source,
            workflow_context=workflow_context,
            actor_id=actor_id,
            now=now,
        )
        for item in (secondary_items or [])
        if isinstance(item, dict)
    ]

    comorbidity_results = [
        _sync_one_non_primary_diagnosis(
            db,
            tenant_id=tenant_id,
            patient_id=patient.id,
            item=item,
            diagnosis_type=DiagnosisType.COMORBIDITY,
            diagnosis_role="COMORBIDITY",
            source=diagnosis_source,
            workflow_context=workflow_context,
            actor_id=actor_id,
            now=now,
        )
        for item in (comorbidity_items or [])
        if isinstance(item, dict)
    ]

    return {
        "synced": True,
        "patient_id": str(patient.id),
        "source": diagnosis_source.value,
        "secondary": secondary_results,
        "comorbidities": comorbidity_results,
    }
