from __future__ import annotations

from datetime import datetime, timezone, timedelta
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import (
    TaskStatus,
    TaskType,
    TaskOrigin,
    TaskDiscipline,
    TaskRegulatoryBasis,
)
from app.services.benefit_period_service import rollover_benefit_period
from app.services.task_benefit_period_linker import attach_active_benefit_period_to_task


# ---------------------------------------------------------------------
# Task type identifiers
# ---------------------------------------------------------------------
TASK_INITIAL_RN_ICA = "INITIAL_RN_ICA"
TASK_NOE_DUE = "NOE_DUE"


# ---------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _pick_open_status() -> TaskStatus:
    if hasattr(TaskStatus, "PENDING"):
        return TaskStatus.PENDING
    return list(TaskStatus)[0]


def _task_type(name: str) -> TaskType:
    if hasattr(TaskType, name):
        return getattr(TaskType, name)

    raise HTTPException(
        status_code=500,
        detail=f"TaskType missing enum member '{name}'. Add it to app.models.enums.TaskType.",
    )


def _get_patient(db: Session, patient_id: uuid.UUID) -> Patient:
    patient = db.query(Patient).filter(Patient.id == patient_id).one_or_none()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient


# ---------------------------------------------------------------------
# Task creation helper
# ---------------------------------------------------------------------
def _ensure_task(
    db: Session,
    *,
    tenant_id,
    patient_id: uuid.UUID,
    task_type: TaskType,
    due_at: datetime,
    created_by: uuid.UUID | None,
    discipline: TaskDiscipline,
    regulatory_basis: TaskRegulatoryBasis,
    origin: TaskOrigin,
) -> None:
    """
    Idempotent task creation with required enterprise fields.

    Guarantees:
    - no duplicate open task of same type for same patient
    - due_date and due_at both populated
    - regulatory_basis always set
    - benefit period auto-attached when available
    """

    open_status = _pick_open_status()

    existing = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.task_type == task_type,
            Task.status == open_status,
        )
        .first()
    )

    if existing:
        return

    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=task_type,
        origin=origin,
        discipline=discipline,
        regulatory_basis=regulatory_basis,
        status=open_status,
        due_at=due_at,
        due_date=due_at.date(),
        created_by=created_by,
    )

    attach_active_benefit_period_to_task(
        db,
        task=task,
        tenant_id=tenant_id,
        patient_id=patient_id,
        as_of_date=task.due_date,
    )

    db.add(task)


# ---------------------------------------------------------------------
# Records release consent
# ---------------------------------------------------------------------
def record_records_release_consent(
    db: Session,
    *,
    patient_id: uuid.UUID,
    signed_at: datetime,
    user_id: uuid.UUID | None,
) -> Patient:
    """
    Phase 1 self-referral / records release consent only.

    Guarantees:
    - does not admit patient
    - does not create clinical admission tasks
    """
    patient = _get_patient(db, patient_id)

    if getattr(patient, "tenant_id", None):
        db.info["tenant_id"] = patient.tenant_id

    patient.records_release_signed_at = signed_at
    patient.admission_status = "RECORDS_PENDING"

    db.flush()
    return patient


# ---------------------------------------------------------------------
# Admission authorization
# ---------------------------------------------------------------------
def authorize_admission(
    db: Session,
    *,
    patient_id: uuid.UUID,
    election_signed_at: datetime,
    authorized_by_user_id: uuid.UUID | None,
) -> Patient:
    """
    Enterprise admission authorization.

    Guarantees:
    - SOC anchored to election_signed_at if not already set
    - admission status updated
    - benefit period created/rolled over via single authoritative service
    - IDG_REVIEW scheduled due SOC + 15 days, with both due_at and due_date
    - INITIAL_RN_ICA scheduled due SOC + 48 hours
    - NOE_DUE scheduled due SOC + 5 days
    - tasks include regulatory_basis and auto-attach to benefit period
    """

    patient = _get_patient(db, patient_id)

    if getattr(patient, "tenant_id", None):
        db.info["tenant_id"] = patient.tenant_id

    # -------------------------------------------------
    # SOC immutability
    # -------------------------------------------------
    if patient.soc_date is None:
        patient.election_signed_at = election_signed_at
        patient.soc_date = election_signed_at

    patient.admission_authorized_at = _now_utc()
    patient.admission_authorized_by = authorized_by_user_id
    patient.admission_status = "ADMITTED"

    db.flush()

    soc = patient.soc_date
    tenant_id = patient.tenant_id

    # -------------------------------------------------
    # Create / ensure benefit period
    # -------------------------------------------------
    rollover_benefit_period(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient.id,
        election_date=soc.date(),
        start_date=soc.date(),
        benefit_type="INITIAL",
    )

    # -------------------------------------------------
    # Schedule required tasks
    # -------------------------------------------------
    idg_due_at = soc.astimezone(timezone.utc) + timedelta(days=15)
    rn_due_at = soc.astimezone(timezone.utc) + timedelta(hours=48)
    noe_due_at = soc.astimezone(timezone.utc) + timedelta(days=5)

    # IDG_REVIEW
    _ensure_task(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
        task_type=TaskType.IDG_REVIEW,
        due_at=idg_due_at,
        created_by=authorized_by_user_id,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,
        origin=TaskOrigin.PERIODIC,
    )

    # INITIAL_RN_ICA
    _ensure_task(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
        task_type=_task_type(TASK_INITIAL_RN_ICA),
        due_at=rn_due_at,
        created_by=authorized_by_user_id,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.CERTIFICATION,
        origin=TaskOrigin.ADMISSION,
    )

    # NOE_DUE
    _ensure_task(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
        task_type=_task_type(TASK_NOE_DUE),
        due_at=noe_due_at,
        created_by=authorized_by_user_id,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.CERTIFICATION,
        origin=TaskOrigin.ADMISSION,
    )

    db.flush()
    return patient
