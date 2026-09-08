"""Single authoritative current-diagnosis resolver.

Root-cause fix for the diagnosis-divergence chain identified across the
RNICA vertical slice: multiple locations (`Patient.primary_diagnosis`,
`PatientFaceSheet.primary_diagnosis`, `RnicaAssessment.form_data.diagnoses`,
the shared clinical-context builder) each independently held their own copy
of "the current primary diagnosis," and nothing kept them in sync when the
authoritative record changed.

SSOT definition used here (per directive):
    AUTHORITATIVE  -- exactly one location holds the current fact:
                      `PatientDiagnosis` rows (diagnosis_type=PRIMARY,
                      status=ACTIVE, active=True). The unique partial index
                      `uq_patient_diagnoses_one_active_primary` enforces at
                      most one such row per patient at the database level.
    PROJECTION     -- `Patient.primary_diagnosis` (legacy plain-string
                      column, kept only for backward compatibility/quick
                      display -- never written to independently by new
                      code, never treated as authoritative when a
                      PatientDiagnosis row exists).
    ASSESSMENT_DRAFT -- `RnicaAssessment.form_data.diagnoses.primaryDiagnosis`
                      -- an RN's in-progress assessment copy. May legitimately
                      diverge from the authoritative record (e.g. an RN typed
                      something the Medical Director hasn't reconciled yet).
                      Divergence is surfaced as an explicit conflict, never
                      silently overwritten and never silently hidden.

Every consumer that needs "the current diagnosis" (shared clinical context,
disease blueprint, LCD, certification support, narrative generation, billing
readiness) MUST call `resolve_current_diagnosis_context()` below instead of
reading any of the above copies directly.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

CONTEXT_VERSION = "diagnosis-resolver-v1"


def _diagnosis_to_dict(row: Any) -> dict[str, Any]:
    return {
        "source_record_id": str(row.id),
        "icd10_code": row.icd10_code,
        "description": row.diagnosis_description,
        "display_name": row.display_name,
        "status": row.status.value if hasattr(row.status, "value") else row.status,
        "diagnosis_type": row.diagnosis_type.value if hasattr(row.diagnosis_type, "value") else row.diagnosis_type,
        "is_terminal": bool(row.is_terminal),
        "is_related_to_terminal": bool(row.is_related_to_terminal),
        "effective_date": row.effective_date.isoformat() if row.effective_date else None,
        "created_by": str(row.created_by) if row.created_by else None,
        "updated_by": str(row.updated_by) if row.updated_by else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def resolve_current_diagnosis_context(db: Session, patient_id: str) -> dict[str, Any]:
    """Return the one resolved, authoritative current-diagnosis context for
    `patient_id`. Never raises -- returns an explicit `unavailable_reason`
    instead of a silent empty/default value so callers can distinguish
    "no diagnosis documented" from "resolver failed."
    """

    from app.models.patient import Patient
    from app.models.patient_diagnosis import PatientDiagnosis

    result: dict[str, Any] = {
        "context_version": CONTEXT_VERSION,
        "available": False,
        "unavailable_reason": None,
        "primary": None,
        "primary_source": None,  # "PatientDiagnosis" (authoritative) | "Patient.primary_diagnosis" (compatibility projection, fallback only)
        "secondary": [],
        "comorbidities": [],
    }

    try:
        rows = (
            db.query(PatientDiagnosis)
            .filter(PatientDiagnosis.patient_id == patient_id, PatientDiagnosis.active.is_(True))
            .all()
        )
    except Exception as exc:  # pragma: no cover - defensive, DB layer failure
        result["unavailable_reason"] = f"DIAGNOSIS_RESOLVER_QUERY_FAILED: {exc}"
        return result

    primary_rows = [r for r in rows if r.diagnosis_type == r.diagnosis_type.__class__.PRIMARY and r.status == r.status.__class__.ACTIVE]
    secondary_rows = [r for r in rows if r.diagnosis_type == r.diagnosis_type.__class__.SECONDARY]
    comorbidity_rows = [r for r in rows if r.diagnosis_type == r.diagnosis_type.__class__.COMORBIDITY]

    result["secondary"] = [_diagnosis_to_dict(r) for r in secondary_rows]
    result["comorbidities"] = [_diagnosis_to_dict(r) for r in comorbidity_rows]

    if primary_rows:
        # The DB unique partial index guarantees at most one active PRIMARY
        # row per patient -- if more than one somehow returns, that itself
        # is a data-integrity defect, not something to silently pick from.
        if len(primary_rows) > 1:
            result["unavailable_reason"] = (
                "MULTIPLE_ACTIVE_PRIMARY_DIAGNOSES_VIOLATES_INVARIANT"
            )
            return result
        result["primary"] = _diagnosis_to_dict(primary_rows[0])
        result["primary_source"] = "PatientDiagnosis"
        result["available"] = True
        return result

    # Fallback: compatibility projection only, explicitly labeled as such.
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is not None and patient.primary_diagnosis:
        result["primary"] = {
            "source_record_id": None,
            "icd10_code": None,
            "description": patient.primary_diagnosis,
            "display_name": patient.primary_diagnosis,
            "status": "ACTIVE",
            "diagnosis_type": "PRIMARY",
            "is_terminal": True,
            "is_related_to_terminal": False,
            "effective_date": None,
            "created_by": None,
            "updated_by": None,
            "updated_at": None,
        }
        result["primary_source"] = "Patient.primary_diagnosis"
        result["available"] = True
        return result

    result["unavailable_reason"] = "NO_PRIMARY_DIAGNOSIS_DOCUMENTED"
    return result


def detect_rnica_diagnosis_conflict(
    resolved: dict[str, Any], rnica_primary_diagnosis: dict[str, Any] | None
) -> dict[str, Any] | None:
    """Compare the resolved authoritative primary diagnosis against an
    RNICA assessment's own `diagnoses.primaryDiagnosis` snapshot.

    Returns None when they agree (or the RNICA field is blank -- nothing to
    conflict with). Returns an explicit conflict dict otherwise -- this is
    surfaced to the RN, never silently resolved either direction. Per
    directive: "If equality does not hold, show one explicit conflict.
    Never silently display inconsistent values."
    """

    if not resolved.get("available") or not resolved.get("primary"):
        return None

    rnica_description = ((rnica_primary_diagnosis or {}).get("description") or "").strip()
    if not rnica_description:
        return None

    authoritative_description = (resolved["primary"].get("description") or "").strip()
    if rnica_description.casefold() == authoritative_description.casefold():
        return None

    return {
        "conflict": "PRIMARY_DIAGNOSIS_DIVERGENCE",
        "authoritative_source": resolved.get("primary_source"),
        "authoritative_value": resolved["primary"].get("description"),
        "rnica_assessment_value": rnica_primary_diagnosis.get("description"),
        "resolution_required": True,
    }
