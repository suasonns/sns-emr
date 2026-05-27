# app/api/patients.py

import uuid
from datetime import date
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.models.patient import Patient
from app.models.visit import Visit
from app.services.dx_policy import is_primary_allowed
from app.services.patient_lifecycle import validate_patient_transition

# Optional import – must never crash endpoints
try:
    from app.services.task_overdue_engine import evaluate_task_timeliness
except Exception:
    evaluate_task_timeliness = None


router = APIRouter(prefix="/patients", tags=["patients"])


# =========================================================
# ENUMS
# =========================================================

class AcuityState(str, Enum):
    ROUTINE = "ROUTINE"
    CRISIS = "CRISIS"


class AcuityUpdate(BaseModel):
    acuity_state: AcuityState


# =========================================================
# SCHEMAS
# =========================================================

class PatientCreate(BaseModel):
    mrn: str
    full_name: str
    date_of_birth: date
    primary_diagnosis: str | None = None


class PatientUpdate(BaseModel):
    full_name: str | None = None
    primary_diagnosis: str | None = None
    status: str | None = None


# =========================================================
# CREATE PATIENT
# =========================================================

@router.post("/", summary="Create patient")
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    if payload.primary_diagnosis:
        if not is_primary_allowed(
            db,
            tenant_id=user.tenant_id,
            code=payload.primary_diagnosis,
        ):
            raise HTTPException(
                status_code=400,
                detail="Primary diagnosis not allowed by policy.",
            )

    patient = Patient(
        id=uuid.uuid4(),
        mrn=payload.mrn,
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        primary_diagnosis=payload.primary_diagnosis,
    )

    try:
        db.add(patient)
        db.commit()
        db.refresh(patient)
    except Exception:
        db.rollback()
        raise

    return patient

# =========================================================
# UPDATE PATIENT
# =========================================================

@router.put("/", summary="Update patient")
def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return patient


# =========================================================
# LIST PATIENTS
# =========================================================

@router.get("/", summary="List patients (read-only)")
def list_patients(
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = getattr(user, "role", "") or ""
    role = role.strip().upper()

    # ---------------------------------------------------------
    # ENTERPRISE DISCIPLINE SCOPE
    # RN/NP/MD (and optionally ADMIN) may view full census.
    # CHHA/VOLUNTEER must not list all patients.
    # ---------------------------------------------------------
    allowed_roles = {"RN", "NP", "MD", "ADMIN"}

    if role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="You may not list all patients. Access is restricted by discipline.",
        )

    return db.query(Patient).order_by(Patient.full_name).all()

# =========================================================
# VISITS FOR PATIENT
# =========================================================

@router.get("/{patient_id}/visits", summary="List visits for a patient")
def list_visits_for_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    return (
        db.query(Visit)
        .filter(Visit.patient_id == patient_id)
        .order_by(Visit.visit_date.desc())
        .all()
    )


# =========================================================
# CHART SUMMARY
# =========================================================

@router.get("/{patient_id}/chart-summary", summary="Patient chart summary")
def patient_chart_summary(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    visits = (
        db.query(Visit)
        .filter(Visit.patient_id == patient_id)
        .all()
    )

    return {
        "patient": patient,
        "visits": visits,
    }