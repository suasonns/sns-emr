# app/api/patients.py

import uuid
from datetime import date
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.tenancy.registry import assert_known_tenant
from app.tenancy.context import set_tenant_context, get_tenant_id

from app.models.patient import Patient
from app.models.visit import Visit
from app.services.dx_policy import is_primary_allowed
from app.services.patient_lifecycle import validate_patient_transition  # kept for future use

# Optional import – must never crash endpoints
try:
    from app.services.task_overdue_engine import evaluate_task_timeliness
except ImportError:
    evaluate_task_timeliness = None


# =========================================================
# TENANT GUARD + CONTEXT (DEV MODE, RLS OFF)
# =========================================================

def require_valid_tenant(user=Depends(get_current_user)):
    """
    Global tenant safety guard:
    - requires tenant_id present
    - requires tenant_id in canonical registry
    """
    tenant_id = getattr(user, "tenant_id", None)
    if tenant_id is None and isinstance(user, dict):
        tenant_id = user.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing tenant context",
        )

    try:
        assert_known_tenant(str(tenant_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    return user


def set_tenant_context(
    db: Session = Depends(get_db_tenant),
    user=Depends(require_valid_tenant),
):
    """
    Request-scoped tenant context initializer (ORM-only; no RLS/GUCs).

    Stores:
      db.info["tenant_id"]
      db.info["user_id"]
    """
    db.info["tenant_id"] = str(user.tenant_id)
    db.info["user_id"] = str(getattr(user, "id", "")) if getattr(user, "id", None) else None
    return user


def get_tenant_id(db: Session) -> str:
    """
    Canonical ORM tenant accessor.
    Fails closed if missing.
    """
    tenant_id = db.info.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing tenant context in DB session",
        )
    return str(tenant_id)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/patients",
    tags=["patients"],
    # Enterprise-grade: tenant enforcement applied once, for all endpoints in this router
    dependencies=[Depends(set_tenant_context)],
)


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
    user=Depends(set_tenant_context),
):
    tenant_id = get_tenant_id(db)

    # Policy guard for primary dx
    if payload.primary_diagnosis:
        if not is_primary_allowed(
            db,
            tenant_id=tenant_id,
            code=payload.primary_diagnosis,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Primary diagnosis not allowed by policy.",
            )

    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,                      # ✅ tenant boundary (canonical)
        mrn=payload.mrn,
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        primary_diagnosis=payload.primary_diagnosis,
        status="ACTIVE",                          # ✅ required by DB constraint
        acuity_state=AcuityState.ROUTINE.value,   # ✅ clinical default
        created_by=getattr(user, "id", None),
    )

    # Enterprise rule: creator must immediately be able to see the patient.
    # Achieved by inserting a patient_assignment in the SAME transaction.
    try:
        db.add(patient)
        db.flush()  # ensures patient.id exists in transaction

        db.execute(
            text("""
                INSERT INTO public.patient_assignments
                    (id, tenant_id, patient_id, user_id, role_at_assignment, assigned_by, assigned_at)
                VALUES
                    (:id, :tenant_id, :patient_id, :user_id, :role_at_assignment, :assigned_by, NOW())
                ON CONFLICT (patient_id, user_id) DO NOTHING
            """),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": str(tenant_id),
                "patient_id": str(patient.id),
                "user_id": str(user.id),
                "role_at_assignment": (getattr(user, "role", "") or "").strip().upper() or "STAFF",
                "assigned_by": str(user.id),
            },
        )

        db.commit()
        db.refresh(patient)
    except Exception:
        db.rollback()
        raise

    return patient


# =========================================================
# UPDATE PATIENT
# =========================================================

@router.put("/{patient_id}", summary="Update patient")
def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    db: Session = Depends(get_db_tenant),
    user=Depends(set_tenant_context),
):
    tenant_id = get_tenant_id(db)

    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.tenant_id == tenant_id,
        )
        .first()
    )

    if not patient:
        # Prefer 404 to avoid existence leak across tenants
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return patient


# =========================================================
# LIST PATIENTS
# =========================================================

@router.get("/", summary="List patients (admin sees all, staff sees assigned)")
def list_patients(
    db: Session = Depends(get_db_tenant),
    user=Depends(set_tenant_context),
):
    tenant_id = get_tenant_id(db)
    role = (getattr(user, "role", "") or "").strip().upper()

    # Always allow ADMIN to see tenant census
    if role == "ADMIN":
        return (
            db.query(Patient)
            .filter(Patient.tenant_id == tenant_id)
            .order_by(Patient.full_name)
            .all()
        )

    # Check if patient_assignments exists (avoid UndefinedTable crashes)
    has_assignments = db.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'patient_assignments'
            )
        """)
    ).scalar()

    # If assignments table is missing, degrade safely:
    # - RN/LVN/MSW/SC/MD/NP can see tenant census (clinical continuity)
    # - CHHA/VOLUNTEER and unknown roles see none (least privilege)
    if not has_assignments:
        clinical_roles = {"RN", "LVN", "LPN", "MSW", "SC", "MD", "NP", "SW", "CHAPLAIN"}
        if role in clinical_roles:
            return (
                db.query(Patient)
                .filter(Patient.tenant_id == tenant_id)
                .order_by(Patient.full_name)
                .all()
            )
        return []

    # Assignment-based visibility for non-admin (table exists)
    stmt = text("""
        SELECT p.*
        FROM public.patients p
        JOIN public.patient_assignments pa
          ON pa.patient_id = p.id
        WHERE p.tenant_id = :tenant_id
          AND pa.user_id = :uid
        ORDER BY p.full_name
    """)

    return (
        db.query(Patient)
        .from_statement(stmt)
        .params(tenant_id=str(tenant_id), uid=str(user.id))
        .all()
    )


# =========================================================
# VISITS FOR PATIENT
# =========================================================

@router.get("/{patient_id}/visits", summary="List visits for a patient")
def list_visits_for_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(set_tenant_context),
):
    tenant_id = get_tenant_id(db)

    return (
        db.query(Visit)
        .filter(
            Visit.patient_id == patient_id,
            Visit.tenant_id == tenant_id,
        )
        .order_by(Visit.visit_datetime.desc())
        .all()
    )


# =========================================================
# CHART SUMMARY
# =========================================================

@router.get("/{patient_id}/chart-summary", summary="Patient chart summary")
def patient_chart_summary(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(set_tenant_context),
):
    tenant_id = get_tenant_id(db)

    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.tenant_id == tenant_id,
        )
        .first()
    )

    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    visits = (
        db.query(Visit)
        .filter(
            Visit.patient_id == patient_id,
            Visit.tenant_id == tenant_id,
        )
        .all()
    )

    return {
        "patient": patient,
        "visits": visits,
    }