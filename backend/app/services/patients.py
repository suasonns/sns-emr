from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from app.core.db_session import get_db
from app.core.permissions import require_roles
from app.core.auth import CurrentUser
from app.models.patient import Patient
from app.services.mrn import generate_mrn
from app.services.audit_logger import log_event

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/admit", status_code=status.HTTP_201_CREATED)
def admit_patient(
    *,
    full_name: str,
    date_of_birth: date,
    primary_diagnosis: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    """
    Admit a patient to hospice.
    """

    mrn = generate_mrn()

    patient = Patient(
        mrn=mrn,
        full_name=full_name,
        date_of_birth=date_of_birth,
        primary_diagnosis=primary_diagnosis,
        status="active",
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    # Audit the admission
    log_event(
        user_id=user.user_id,
        role=user.role,
        action="ADMIT_PATIENT",
        entity_type="patient",
        entity_id=str(patient.id),
    )

    return {
        "patient_id": str(patient.id),
        "mrn": patient.mrn,
        "status": patient.status,
    }
