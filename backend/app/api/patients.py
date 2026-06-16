from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db_tenant_dependency import get_db_tenant
from app.models.patient import Patient
from app.models.task import Task
from app.models.visit import Visit
from app.models.enums import (
    TaskStatus,
    TaskOrigin,
    TaskType,
    TaskDiscipline,
    TaskRegulatoryBasis,
)
from app.services.dx_policy import is_primary_allowed


# =========================================================
# AUDIT SAFE DB WRAPPER
# =========================================================

def get_db_with_request_state(
    request: Request,
    db: Session = Depends(get_db_tenant),
) -> Generator[Session, None, None]:
    request.state.db = db
    yield db


# =========================================================
# TENANT AUTH
# =========================================================

def require_tenant_user(user=Depends(get_current_user)):
    if getattr(user, "is_superuser", False) or getattr(user, "is_management", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant-scoped endpoint not available to system accounts",
        )
    return user


def _tenant_id_uuid(user) -> uuid.UUID:
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(401, "Missing tenant context")
    try:
        return uuid.UUID(str(tenant_id))
    except Exception:
        raise HTTPException(400, "Invalid tenant_id format")


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(prefix="/patients", tags=["patients"])


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
# LIST PATIENTS
# =========================================================

@router.get("/", summary="List patients")
def list_patients(
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    ALLOWED_LIST_ROLES = {"RN", "LVN", "NP", "MD", "MSW", "SC", "ADMIN"}

    if user.role not in ALLOWED_LIST_ROLES:
        raise HTTPException(403, "Insufficient role scope")

    return (
        db.query(Patient)
        .filter(Patient.tenant_id == tenant_id)
        .order_by(Patient.full_name)
        .all()
    )


# =========================================================
# CREATE
# =========================================================

@router.post("/")
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    if payload.primary_diagnosis:
        if not is_primary_allowed(db, tenant_id=str(tenant_id), code=payload.primary_diagnosis):
            raise HTTPException(400, "Primary diagnosis not allowed")

    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=payload.mrn,
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        primary_diagnosis=payload.primary_diagnosis,
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        acuity_state="ROUTINE",
        created_by=str(getattr(user, "id", "")) or None,
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


# =========================================================
# UPDATE
# =========================================================

@router.put("/{patient_id}")
def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .first()
    )

    if not patient:
        raise HTTPException(404, "Patient not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return patient


# =========================================================
# VISITS
# =========================================================

@router.get("/{patient_id}/visits")
def list_visits_for_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    return (
        db.query(Visit)
        .filter(Visit.patient_id == patient_id, Visit.tenant_id == tenant_id)
        .order_by(Visit.visit_datetime.desc())
        .all()
    )


# =========================================================
# PUT ON SERVICE
# =========================================================

@router.post("/{patient_id}/put-on-service", summary="Put patient on service")
def put_patient_on_service(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.tenant_id == tenant_id,
        )
        .first()
    )

    if not patient:
        raise HTTPException(404, "Patient not found")

    if getattr(patient, "on_service_at", None):
        return {
            "status": "already_on_service",
            "on_service_at": patient.on_service_at,
        }

    now = datetime.now(timezone.utc)
    patient.on_service_at = now

    soc_date = now.date()

    # ✅ ICA TASK DEFINITIONS
    ica_specs = [
        (TaskType.INITIAL_RN_ICA, TaskDiscipline.RN, TaskRegulatoryBasis.IDG_REVIEW, soc_date + timedelta(days=2)),
        (TaskType.INITIAL_MSW_ICA, TaskDiscipline.SW, TaskRegulatoryBasis.IDG_REVIEW, soc_date + timedelta(days=5)),
        (TaskType.INITIAL_SC_ICA, TaskDiscipline.CHAPLAIN, TaskRegulatoryBasis.IDG_REVIEW, soc_date + timedelta(days=5)),
        (TaskType.INITIAL_BEREAVEMENT, TaskDiscipline.SW, TaskRegulatoryBasis.IDG_REVIEW, soc_date + timedelta(days=5)),
    ]

    created = []

    for task_type, discipline, regulatory_basis, due_date in ica_specs:
        task = Task(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient.id,
            task_type=task_type,
            origin=TaskOrigin.PERIODIC,
            discipline=discipline,
            regulatory_basis=regulatory_basis,
            status=TaskStatus.PENDING,
            due_date=due_date,
            created_by=str(getattr(user, "id", "")) or None,
        )
        db.add(task)
        created.append(task_type.value)

    db.commit()

    return {
        "status": "on_service",
        "on_service_at": patient.on_service_at,
        "ica_tasks_created": created,
    }

# =========================================================
# REQUIRED: PATIENT CHART SUMMARY
# =========================================================

@router.get("/{patient_id}/chart-summary")
def patient_chart_summary(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .first()
    )

    if not patient:
        raise HTTPException(404, "Patient not found")

    visits = (
        db.query(Visit)
        .filter(Visit.patient_id == patient_id, Visit.tenant_id == tenant_id)
        .order_by(Visit.visit_datetime.desc())
        .all()
    )

    return {"patient": patient, "visits": visits}