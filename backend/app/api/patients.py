# app/api/patients.py

import uuid
from datetime import date
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.patient import Patient
from app.models.visit import Visit
from app.services.dx_policy import is_primary_allowed

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
# INTERNAL HELPERS (ENTERPRISE SAFE)
# =========================================================
def _set_rls_tenant(db: Session, tenant_id: uuid.UUID) -> None:
    """
    Required for RLS WITH CHECK.
    Must execute inside the same transaction as INSERT/UPDATE.
    """
    db.execute(
        text("SET LOCAL app.current_tenant = :tid"),
        {"tid": str(tenant_id)},
    )


def _set_app_user_id(db: Session, user_uuid: uuid.UUID | None) -> None:
    """
    Optional DB audit context.
    Postgres custom GUCs MUST contain a dot.
    """
    if not user_uuid:
        return

    db.execute(
        text("SELECT set_config('app.user_id', :uid, true)"),
        {"uid": str(user_uuid)},
    )


# =========================================================
# CREATE PATIENT
# =========================================================
@router.post("/", summary="Create patient")
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    role = getattr(user, "role", "").upper()
    user_uuid = getattr(user, "user_id", None) or getattr(user, "id", None)

    if not tenant_id:
        raise HTTPException(status_code=500, detail="Tenant context missing")

    if role not in {"RN", "NP", "MD", "ADMIN"}:
        raise HTTPException(status_code=403, detail="Forbidden")

    # --- CRITICAL CONTEXT ---
    _set_rls_tenant(db, tenant_id)
    _set_app_user_id(db, user_uuid)

    if payload.primary_diagnosis:
        allowed, reason = is_primary_allowed(
            db,
            tenant_id=tenant_id,
            code=payload.primary_diagnosis,
        )
        if not allowed:
            raise HTTPException(status_code=422, detail=reason)

    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=payload.mrn,
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        primary_diagnosis=payload.primary_diagnosis,
        status="ACTIVE",
        created_by=user_uuid,
    )

    try:
        db.add(patient)
        db.commit()
        db.refresh(patient)
    except Exception as e:
        db.rollback()

        # ✅ Enterprise‑correct duplicate MRN handling
        if "patients_mrn_key" in str(e):
            raise HTTPException(
                status_code=409,
                detail="A patient with this MRN already exists in this tenant",
            )

        raise

    return {"patient_id": str(patient.id)}


# =========================================================
# UPDATE PATIENT
# =========================================================
@router.put("/{patient_id}", summary="Update patient")
def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    role = getattr(user, "role", "").upper()
    user_uuid = getattr(user, "user_id", None) or getattr(user, "id", None)

    if not tenant_id:
        raise HTTPException(status_code=500, detail="Tenant context missing")

    if role not in {"RN", "NP", "MD", "ADMIN"}:
        raise HTTPException(status_code=403, detail="Forbidden")

    _set_rls_tenant(db, tenant_id)
    _set_app_user_id(db, user_uuid)

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if payload.primary_diagnosis is not None:
        allowed, reason = is_primary_allowed(
            db,
            tenant_id=tenant_id,
            code=payload.primary_diagnosis,
        )
        if not allowed:
            raise HTTPException(status_code=422, detail=reason)
        patient.primary_diagnosis = payload.primary_diagnosis

    if payload.full_name is not None:
        patient.full_name = payload.full_name

    if payload.status is not None:
        patient.status = payload.status

    db.commit()
    return {"status": "ok"}


# =========================================================
# LIST PATIENTS
# =========================================================
@router.get("/", summary="List patients (read-only)")
def list_patients(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    role = getattr(user, "role", "").upper()

    if not tenant_id:
        raise HTTPException(status_code=500, detail="Tenant context missing")

    # ✅ CRITICAL: RLS applies to SELECT too
    db.execute(
        text("SET LOCAL app.current_tenant = :tid"),
        {"tid": str(tenant_id)},
    )

    if role in {"ADMIN", "MD"}:
        patients = (
            db.query(Patient)
            .filter(Patient.tenant_id == tenant_id)
            .order_by(Patient.full_name.asc())
            .all()
        )
    else:
        if role not in {"RN", "NP", "SURVEYOR"}:
            raise HTTPException(status_code=403, detail="Forbidden")

        patients = (
            db.query(Patient)
            .filter(Patient.tenant_id == tenant_id)
            .order_by(Patient.full_name.asc())
            .all()
        )

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
@router.get("/{patient_id}/visits", summary="List visits for a patient")
def list_visits_for_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    role = getattr(user, "role", "").upper()

    if not tenant_id:
        raise HTTPException(status_code=500, detail="Tenant context missing")

    if role not in {"RN", "LVN", "NP", "MD", "SURVEYOR", "ADMIN"}:
        raise HTTPException(status_code=403, detail="Forbidden")

    visits = (
        db.query(Visit)
        .filter(
            Visit.tenant_id == tenant_id,
            Visit.patient_id == patient_id,
        )
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
# CHART SUMMARY
# =========================================================
@router.get("/{patient_id}/chart-summary", summary="Patient chart summary")
def patient_chart_summary(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    role = getattr(user, "role", "").upper()

    if not tenant_id:
        raise HTTPException(status_code=500, detail="Tenant context missing")

    if role not in {"RN", "NP", "MD", "SURVEYOR", "ADMIN"}:
        raise HTTPException(status_code=403, detail="Forbidden")

    if evaluate_task_timeliness:
        try:
            evaluate_task_timeliness(db=db, tenant_id=tenant_id)
        except TypeError:
            pass

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {
        "patient": {"patient_id": str(patient.id)},
        "visits": [],
        "clinical_notes": [],
        "amendments": [],
        "medications": [],
    }