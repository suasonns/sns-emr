from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import date
import uuid

from app.core.db_session import get_db
from app.core.permissions import require_roles
from app.core.security import CurrentUser

from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet

from app.services.mrn import generate_mrn
from app.services.audit_logger import log_event

router = APIRouter(prefix="/patients", tags=["patients"])


# -----------------------------------------------------
# ✅ REQUEST SCHEMA (ENTERPRISE SAFE)
# -----------------------------------------------------

class PatientAdmitRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: str | None = None
    last_name: str = Field(..., min_length=1, max_length=100)

    date_of_birth: date
    primary_diagnosis: str = Field(..., min_length=3, max_length=255)


# -----------------------------------------------------
# ✅ ENDPOINT (PRODUCTION GRADE)
# -----------------------------------------------------

@router.post("/admit", status_code=status.HTTP_201_CREATED)
def admit_patient(
    payload: PatientAdmitRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    """
    Admit a patient to hospice (enterprise-safe).
    """

    # --------------------------------------------------
    # ✅ VALIDATE USER ID
    # --------------------------------------------------
    user_id = getattr(user, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=500,
            detail="Invalid user identity"
        )

    # --------------------------------------------------
    # ✅ GENERATE IDENTIFIERS
    # --------------------------------------------------
    patient_id = uuid.uuid4()
    mrn = generate_mrn()

    # --------------------------------------------------
    # ✅ CREATE PATIENT CORE (NO NAME HERE)
    # --------------------------------------------------
    patient = Patient(
        id=patient_id,
        mrn=mrn,
        date_of_birth=payload.date_of_birth,
        primary_diagnosis=payload.primary_diagnosis,
        status="ACTIVE",
        created_by=user_id,
    )

    # --------------------------------------------------
    # ✅ CREATE FACE SHEET (LEGAL IDENTITY)
    # --------------------------------------------------
    facesheet = PatientFaceSheet(
        patient_id=patient_id,
        first_name=payload.first_name.strip(),
        middle_name=(payload.middle_name or "").strip() or None,
        last_name=payload.last_name.strip(),
        dob=payload.date_of_birth,
        primary_diagnosis=payload.primary_diagnosis,
        created_by=user_id,
        updated_by=user_id,
    )

    # --------------------------------------------------
    # ✅ TRANSACTION SAFE COMMIT
    # --------------------------------------------------
    try:
        db.add(patient)
        db.add(facesheet)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(patient)

    # --------------------------------------------------
    # ✅ AUDIT LOG (ENTERPRISE TRACEABILITY)
    # --------------------------------------------------
    log_event(
        user_id=user.user_id,
        role=user.role,
        action="ADMIT_PATIENT",
        entity_type="patient",
        entity_id=str(patient.id),
        metadata={
            "mrn": patient.mrn,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
        },
    )

    # --------------------------------------------------
    # ✅ RESPONSE
    # --------------------------------------------------
    return {
        "patient_id": str(patient.id),
        "mrn": patient.mrn,
        "status": patient.status,
    }