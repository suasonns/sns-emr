import uuid
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.db_session import get_db
from app.core.permissions import require_roles
from app.core.visit_types import normalize_visit_type

from app.models.amendment import Amendment
from app.models.clinical_note import ClinicalNote
from app.models.medication import Medication
from app.models.patient import Patient
from app.models.visit import Visit

from app.services.task_overdue_engine import evaluate_task_timeliness

router = APIRouter(prefix="/patients", tags=["patients"])


# =========================================================
# ENUM VALIDATION (ROUTINE / CRISIS ONLY)
# =========================================================
class AcuityState(str, Enum):
    ROUTINE = "ROUTINE"
    CRISIS = "CRISIS"


class AcuityUpdate(BaseModel):
    acuity_state: AcuityState


# =========================================================
# PATIENT LISTING
# =========================================================
@router.get("/", summary="List patients (read-only)")
def list_patients(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Surveyor"])),
):
    patients = db.query(Patient).all()
    return [
        {
            "patient_id": str(p.id),
            "mrn": p.mrn,
            "full_name": p.full_name,
            "date_of_birth": p.date_of_birth,
            "primary_diagnosis": p.primary_diagnosis,
            "status": p.status,
        }
        for p in patients
    ]


# =========================================================
# VISITS FOR PATIENT
# =========================================================
@router.get("/{patient_id}/visits", summary="List visits for a patient (read-only)")
def list_visits_for_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "LVN", "NP", "MD", "Surveyor"])),
):
    visits = (
        db.query(Visit)
        .filter(Visit.patient_id == patient_id)
        .order_by(Visit.visit_datetime.desc())
        .all()
    )

    return [
        {
            "visit_id": str(v.id),
            "visit_type": v.visit_type,
            "visit_datetime": v.visit_datetime,
            "status": v.status,
            "provider_id": str(v.provider_id),
            "is_supervisory": getattr(v, "is_supervisory", False),
            "acuity_state_at_visit": getattr(v, "acuity_state_at_visit", None),
        }
        for v in visits
    ]


# =========================================================
# CHART SUMMARY (READ-ONLY EXPORT)
# =========================================================
@router.get("/{patient_id}/chart-summary", summary="Patient chart summary (read-only export view)")
def patient_chart_summary(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Surveyor"])),
):
    evaluate_task_timeliness(db)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {
        "patient": {"patient_id": str(patient.id)},
        "visits": [],
        "clinical_notes": [],
        "amendments": [],
        "medications": [],
    }


# =========================================================
# SET PATIENT ACUITY + AUTO-CREATE NOTE
# =========================================================
@router.patch("/{patient_id}/acuity", summary="Set patient acuity state (ROUTINE/CRISIS)")
def set_patient_acuity(
    patient_id: uuid.UUID,
    payload: AcuityUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Normalize and validate acuity value (works for str or Enum)
    new_acuity = payload.acuity_state
    if hasattr(new_acuity, "value"):
        new_acuity = new_acuity.value
    new_acuity = (new_acuity or "").upper()

    if new_acuity not in ("ROUTINE", "CRISIS"):
        raise HTTPException(status_code=422, detail="acuity_state must be ROUTINE or CRISIS")

    previous_acuity = getattr(patient, "acuity_state", None)

    # No-op protection
    if previous_acuity == new_acuity:
        return {
            "patient_id": str(patient.id),
            "acuity_state": patient.acuity_state,
            "note_created": False,
        }

    # Update patient acuity
    patient.acuity_state = new_acuity
    now = datetime.utcnow()

    # Crisis timing (only if columns exist)
    if new_acuity == "CRISIS":
        if hasattr(patient, "crisis_started_at") and getattr(patient, "crisis_started_at", None) is None:
            patient.crisis_started_at = now
        if hasattr(patient, "crisis_ended_at"):
            patient.crisis_ended_at = None
    else:
        if hasattr(patient, "crisis_ended_at"):
            patient.crisis_ended_at = now

    db.flush()

    # Find latest visit to attach the note
    visit = (
        db.query(Visit)
        .filter(Visit.patient_id == patient.id)
        .order_by(Visit.visit_datetime.desc())
        .first()
    )

    # Create a draft RN visit if needed (visit_id is NOT NULL on clinical_notes)
    if visit is None:
        visit = Visit(
            patient_id=patient.id,
            provider_id=user.user_id,
            visit_type=normalize_visit_type("RN"),
            visit_datetime=now,
            status="draft",
            created_by=user.user_id,
            is_supervisory=False,
            acuity_state_at_visit=new_acuity,
        )
        db.add(visit)
        db.flush()

    note_content = (
        f"Patient acuity state changed from {previous_acuity} to {new_acuity}.\n\n"
        "Change reflects current clinical status and Plan of Care needs. "
        "Acuity update supports appropriate visit frequency, supervisory requirements, "
        "and Plan of Care oversight.\n\n"
        "No direct patient contact occurred for this acuity update entry unless otherwise documented."
    )

    # Build ClinicalNote using REQUIRED + known-safe fields
    note_kwargs = {
        "visit_id": visit.id,                   # NOT NULL
        "author_id": user.user_id,              # NOT NULL (critical fix)
        "note_type": "Clinical Chart Review",   # NOT NULL
        "content": note_content,                # NOT NULL
        "status": "finalized",
        "finalized_at": now,
        "finalized_by": user.user_id,
    }

    # Optional fields only if your model supports them
    if hasattr(ClinicalNote, "created_by"):
        note_kwargs["created_by"] = user.user_id

    note = ClinicalNote(**note_kwargs)
    db.add(note)
    db.commit()

    return {
        "patient_id": str(patient.id),
        "acuity_state": patient.acuity_state,
        "previous_acuity": previous_acuity,
        "note_created": True,
        "note_id": str(note.id),
        "note_visit_id": str(visit.id),
    }