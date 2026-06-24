from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import (
    TaskDiscipline,
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskStatus,
    TaskType,
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


def _required_enum_member(enum_cls, preferred_names: list[str]):
    """
    Resolve the first matching enum member by name.

    Raises:
        ValueError if none of the preferred names exist.
    """
    for name in preferred_names:
        member = getattr(enum_cls, name, None)
        if member is not None:
            return member

    raise ValueError(
        f"Missing required enum in {enum_cls.__name__}: expected one of {preferred_names}"
    )


def _optional_enum_member(enum_cls, preferred_names: list[str]):
    """
    Resolve the first matching enum member by name.

    Returns:
        Enum member if found, otherwise None.
    """
    for name in preferred_names:
        member = getattr(enum_cls, name, None)
        if member is not None:
            return member
    return None


def _as_date(value):
    if value is None:
        return None
    return value.date() if hasattr(value, "date") else value


def _set_due_fields(task: Task, due_at: datetime) -> None:
    if hasattr(task, "due_at"):
        task.due_at = due_at
    if hasattr(task, "due_date"):
        task.due_date = due_at.date()


def _active_recurring_statuses() -> list[TaskStatus]:
    """
    Canonical active statuses for unresolved recurring tasks.
    """
    statuses: list[TaskStatus] = []

    for name in ("PENDING", "IN_PROGRESS", "OVERDUE", "ESCALATED"):
        member = _optional_enum_member(TaskStatus, [name])
        if member is not None and member not in statuses:
            statuses.append(member)

    if not statuses:
        raise ValueError(
            "TaskStatus enum has no usable active recurring statuses. "
            "Expected at least PENDING, IN_PROGRESS, OVERDUE, or ESCALATED."
        )

    return statuses


def _touch_task(task: Task, *, when: datetime) -> None:
    if hasattr(task, "updated_at"):
        task.updated_at = when


def _set_created_by(task: Task, created_by: Optional[uuid.UUID]) -> None:
    if hasattr(task, "created_by"):
        task.created_by = created_by


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

    Behavior:
    - if an existing task is found and is unresolved, normalize it to PENDING
      and refresh its due date
    - if an existing task is COMPLETED or WAIVED, preserve that outcome and do
      not create a duplicate
    """
    now = _now_utc()

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

    pending = _required_enum_member(TaskStatus, ["PENDING"])
    completed = _optional_enum_member(TaskStatus, ["COMPLETED"])
    waived = _optional_enum_member(TaskStatus, ["WAIVED"])

    if existing:
        current_status = getattr(existing, "status", None)

        if current_status not in {completed, waived}:
            existing.status = pending
            _set_due_fields(existing, due_at)
            _touch_task(existing, when=now)

        return existing

    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=task_type,
        status=pending,
        origin=origin,
        discipline=discipline,
        regulatory_basis=regulatory_basis,
    )

    _set_created_by(task, created_by)
    _set_due_fields(task, due_at)

    if hasattr(task, "created_at"):
        task.created_at = now
    if hasattr(task, "updated_at"):
        task.updated_at = now

    attach_active_benefit_period_to_task(
        db,
        task=task,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    db.add(task)
    return task


def _ensure_active_task_by_type(
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
    Active-task idempotency for recurring obligations.

    Behavior:
    - if an ACTIVE recurring task already exists, reuse it and refresh due date
    - if only COMPLETED/WAIVED tasks exist, create a NEW active task

    Used for recurring obligations like IDG_REVIEW.
    """
    now = _now_utc()
    pending = _required_enum_member(TaskStatus, ["PENDING"])
    active_statuses = _active_recurring_statuses()

    existing_active = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.task_type == task_type,
            Task.status.in_(active_statuses),
        )
        .order_by(Task.created_at.desc())
        .first()
    )

    if existing_active:
        existing_active.status = pending
        _set_due_fields(existing_active, due_at)
        _touch_task(existing_active, when=now)
        return existing_active

    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=task_type,
        status=pending,
        origin=origin,
        discipline=discipline,
        regulatory_basis=regulatory_basis,
    )

    _set_created_by(task, created_by)
    _set_due_fields(task, due_at)

    if hasattr(task, "created_at"):
        task.created_at = now
    if hasattr(task, "updated_at"):
        task.updated_at = now

    attach_active_benefit_period_to_task(
        db,
        task=task,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    db.add(task)
    return task


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

    if hasattr(patient, "updated_at"):
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
    - IDG_REVIEW due +15 days (PENDING, active-task idempotent)
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).one()
    tenant_id = getattr(patient, "tenant_id", None)

    if not tenant_id:
        raise ValueError("Patient is missing tenant_id")

    incoming_soc = election_signed_at.date()
    existing_soc = _as_date(getattr(patient, "soc_date", None))

    # SOC immutability
    if existing_soc is None:
        try:
            patient.soc_date = incoming_soc
        except Exception:
            patient.soc_date = election_signed_at

    # Admission authorization stamps (set once)
    if hasattr(patient, "admission_authorized_at") and getattr(patient, "admission_authorized_at", None) is None:
        patient.admission_authorized_at = election_signed_at

    if hasattr(patient, "election_signed_at") and getattr(patient, "election_signed_at", None) is None:
        patient.election_signed_at = election_signed_at

    if hasattr(patient, "updated_at"):
        patient.updated_at = _now_utc()

    origin_manual = _required_enum_member(TaskOrigin, ["MANUAL", "SYSTEM"])
    origin_periodic = _required_enum_member(TaskOrigin, ["PERIODIC", "SYSTEM"])
    rn_disc = _required_enum_member(TaskDiscipline, ["RN"])

    rn_ica_type = _required_enum_member(TaskType, [TASK_INITIAL_RN_ICA])
    noe_type = _required_enum_member(TaskType, [TASK_NOE_DUE])

    # Regulatory basis resolution:
    # keep fallback order explicit and deterministic
    rn_basis = _required_enum_member(TaskRegulatoryBasis, ["IDG_REVIEW"])
    noe_basis = _required_enum_member(TaskRegulatoryBasis, ["IDG_REVIEW"])

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

    # IDG review cadence (active-task idempotent)
    idg_type = _optional_enum_member(TaskType, ["IDG_REVIEW"])
    if idg_type is not None:
        idg_basis = _required_enum_member(TaskRegulatoryBasis, ["IDG_REVIEW"])

        _ensure_active_task_by_type(
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
