from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

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
from app.services.task_benefit_period_linker import attach_active_benefit_period_to_task


# ---------------------------------------------------------------------
# Task type identifiers
# ---------------------------------------------------------------------

TASK_INITIAL_RN_ICA = "INITIAL_RN_ICA"
TASK_NOE_DUE = "NOE_DUE"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _enum_member(enum_cls, preferred_names: list[str]):
    for name in preferred_names:
        if hasattr(enum_cls, name):
            return getattr(enum_cls, name)
    return list(enum_cls)[0]


def _as_date(value):
    if value is None:
        return None
    return value.date() if hasattr(value, "date") else value


def _set_due_fields(task: Task, due_at: datetime) -> None:
    if hasattr(task, "due_at"):
        task.due_at = due_at
    if hasattr(task, "due_date"):
        task.due_date = due_at.date()


def _ensure_initial_task_pending_unique(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    task_type: TaskType,
    due_at: datetime,
    created_by: Optional[uuid.UUID],
    discipline: TaskDiscipline,
    regulatory_basis: TaskRegulatoryBasis,
    origin: TaskOrigin,
) -> Task:
    """
    STRICT uniqueness per (tenant_id, patient_id, task_type) across all statuses.

    Used for onboarding tasks which must never duplicate:
    - INITIAL_RN_ICA
    - NOE_DUE

    If an existing task is found and not COMPLETED, it is normalized to PENDING.
    """
    existing = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.task_type == task_type,
        )
        .order_by(Task.created_at.asc())
        .first()
    )

    pending = _enum_member(TaskStatus, ["PENDING"])
    completed = getattr(TaskStatus, "COMPLETED", None)

    if existing:
        if completed is None or existing.status != completed:
            existing.status = pending
        _set_due_fields(existing, due_at)
        return existing

    t = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=task_type,
        status=pending,
        origin=origin,
        discipline=discipline,
        regulatory_basis=regulatory_basis,
        created_by=str(created_by) if created_by else None,
    )
    _set_due_fields(t, due_at)

    attach_active_benefit_period_to_task(
        db,
        task=t,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    db.add(t)
    return t


def _ensure_open_task_by_type(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    task_type: TaskType,
    due_at: datetime,
    created_by: Optional[uuid.UUID],
    discipline: TaskDiscipline,
    regulatory_basis: TaskRegulatoryBasis,
    origin: TaskOrigin,
) -> Task:
    """
    OPEN‑ONLY idempotency:

    - If an OPEN/PENDING task exists: reuse it (and refresh due date)
    - If only COMPLETED tasks exist: create a NEW open task

    Used for recurring obligations like IDG_REVIEW.
    """
    pending = _enum_member(TaskStatus, ["PENDING"])
    open_status = getattr(TaskStatus, "OPEN", None)

    base_q = db.query(Task).filter(
        Task.tenant_id == tenant_id,
        Task.patient_id == patient_id,
        Task.task_type == task_type,
    )

    if open_status is not None:
        existing_open = (
            base_q.filter(Task.status == open_status)
            .order_by(Task.created_at.desc())
            .first()
        )
        if existing_open:
            _set_due_fields(existing_open, due_at)
            return existing_open

    existing_pending = (
        base_q.filter(Task.status == pending)
        .order_by(Task.created_at.desc())
        .first()
    )
    if existing_pending:
        _set_due_fields(existing_pending, due_at)
        return existing_pending

    # No open task exists → create a new one
    t = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=task_type,
        status=pending,
        origin=origin,
        discipline=discipline,
        regulatory_basis=regulatory_basis,
        created_by=str(created_by) if created_by else None,
    )
    _set_due_fields(t, due_at)

    attach_active_benefit_period_to_task(
        db,
        task=t,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    db.add(t)
    return t


# ---------------------------------------------------------------------
# Public Contract: Records release consent
# ---------------------------------------------------------------------

def record_records_release_consent(
    db: Session,
    *,
    patient_id: uuid.UUID,
    signed_at: datetime,
    user_id: Optional[uuid.UUID],
) -> Patient:
    """
    PUBLIC CONTRACT: required by app.api.admission_authorization imports.

    Records release consent only:
    - no admission authorization
    - no onboarding tasks
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).one()

    if hasattr(patient, "records_release_signed_at"):
        patient.records_release_signed_at = signed_at
    if hasattr(patient, "records_release_signed_by"):
        patient.records_release_signed_by = user_id

    patient.updated_at = _now_utc()
    db.commit()
    db.refresh(patient)
    return patient


# ---------------------------------------------------------------------
# Public Contract: Admission authorization
# ---------------------------------------------------------------------

def authorize_admission(
    db: Session,
    *,
    patient_id: uuid.UUID,
    election_signed_at: datetime,
    authorized_by_user_id: Optional[uuid.UUID],
) -> Patient:
    """
    Admission authorization (production stable).

    Guarantees:
    - SOC immutable (no-op if already set)
    - INITIAL_RN_ICA due +2 days (PENDING, strict unique)
    - NOE_DUE due +5 days (PENDING, strict unique)
    - IDG_REVIEW due +15 days (PENDING, OPEN-only idempotent)
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).one()
    tenant_id = patient.tenant_id

    incoming_soc = election_signed_at.date()
    existing_soc = _as_date(getattr(patient, "soc_date", None))

    # SOC immutability
    if existing_soc is None:
        try:
            patient.soc_date = incoming_soc
        except Exception:
            patient.soc_date = election_signed_at

    # Admission auth stamps (set once)
    if hasattr(patient, "admission_authorized_at") and getattr(patient, "admission_authorized_at", None) is None:
        patient.admission_authorized_at = election_signed_at
    if hasattr(patient, "election_signed_at") and getattr(patient, "election_signed_at", None) is None:
        patient.election_signed_at = election_signed_at

    patient.updated_at = _now_utc()

    origin_manual = _enum_member(TaskOrigin, ["MANUAL", "PERIODIC"])
    origin_periodic = _enum_member(TaskOrigin, ["PERIODIC"])
    rn_disc = _enum_member(TaskDiscipline, ["RN"])

    rn_ica_type = _enum_member(TaskType, [TASK_INITIAL_RN_ICA])
    noe_type = _enum_member(TaskType, [TASK_NOE_DUE])

    rn_basis = _enum_member(TaskRegulatoryBasis, ["IDG_REVIEW"])
    noe_basis = _enum_member(TaskRegulatoryBasis, ["NOE", "IDG_REVIEW"])

    # Onboarding tasks (strict unique)
    _ensure_initial_task_pending_unique(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=rn_ica_type,
        due_at=election_signed_at + timedelta(days=2),
        created_by=authorized_by_user_id,
        discipline=rn_disc,
        regulatory_basis=rn_basis,
        origin=origin_manual,
    )

    _ensure_initial_task_pending_unique(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=noe_type,
        due_at=election_signed_at + timedelta(days=5),
        created_by=authorized_by_user_id,
        discipline=rn_disc,
        regulatory_basis=noe_basis,
        origin=origin_manual,
    )

    # IDG review cadence (open-only idempotent)
    if hasattr(TaskType, "IDG_REVIEW"):
        idg_type = TaskType.IDG_REVIEW
        idg_basis = _enum_member(TaskRegulatoryBasis, ["IDG_REVIEW"])

        _ensure_open_task_by_type(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            task_type=idg_type,
            due_at=election_signed_at + timedelta(days=15),
            created_by=authorized_by_user_id,
            discipline=rn_disc,
            regulatory_basis=idg_basis,
            origin=origin_periodic,
        )

    db.commit()
    db.refresh(patient)
    return patient