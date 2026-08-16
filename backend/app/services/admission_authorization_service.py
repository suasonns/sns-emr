# services/admission_authorization_service.py

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.task import Task
from app.models.admission import Admission
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
TASK_INITIAL_MSW_ICA = "INITIAL_MSW_ICA"
TASK_INITIAL_SC_ICA = "INITIAL_SC_ICA"
TASK_INITIAL_BEREAVEMENT = "INITIAL_BEREAVEMENT"
TASK_NOE_DUE = "NOE_DUE"
TASK_IDG_REVIEW = "IDG_REVIEW"


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


def _set_due_fields(task: Task, due_at: datetime, *, when: datetime) -> None:
    """
    Set all due / SLA fields that may be required by the live DB schema.
    """
    if hasattr(task, "due_at"):
        task.due_at = due_at

    if hasattr(task, "due_date"):
        task.due_date = due_at.date()

    if hasattr(task, "sla_start_at"):
        task.sla_start_at = when

    if hasattr(task, "sla_due_at"):
        task.sla_due_at = due_at


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


def _set_task_defaults(
    task: Task,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    task_type: TaskType,
    discipline: TaskDiscipline,
    regulatory_basis: TaskRegulatoryBasis,
    origin: TaskOrigin,
    due_at: datetime,
    created_by: Optional[uuid.UUID],
    when: datetime,
) -> None:
    """
    Normalize all required fields for the current live task schema.
    """
    pending = _required_enum_member(TaskStatus, ["PENDING"])

    task.tenant_id = tenant_id
    task.patient_id = patient_id
    task.task_type = task_type
    task.status = pending
    task.origin = origin
    task.discipline = discipline
    task.regulatory_basis = regulatory_basis

    _set_due_fields(task, due_at, when=when)
    _set_created_by(task, created_by)

    if hasattr(task, "created_at") and getattr(task, "created_at", None) is None:
        task.created_at = when

    if hasattr(task, "updated_at"):
        task.updated_at = when

    if hasattr(task, "is_overdue") and getattr(task, "is_overdue", None) is None:
        task.is_overdue = False

    if hasattr(task, "escalation_level") and getattr(task, "escalation_level", None) is None:
        task.escalation_level = 0


def _new_task(
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
    now = _now_utc()

    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=task_type,
        status=_required_enum_member(TaskStatus, ["PENDING"]),
        origin=origin,
        discipline=discipline,
        regulatory_basis=regulatory_basis,
    )

    _set_task_defaults(
        task,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=task_type,
        discipline=discipline,
        regulatory_basis=regulatory_basis,
        origin=origin,
        due_at=due_at,
        created_by=created_by,
        when=now,
    )

    attach_active_benefit_period_to_task(
        db=None,
        task=task,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    return task


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
    - INITIAL_MSW_ICA
    - INITIAL_SC_ICA
    - INITIAL_BEREAVEMENT
    - NOE_DUE

    Behavior:
    - if an existing task is found and is unresolved, normalize it to PENDING
      and refresh due date / SLA fields
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
            existing.origin = origin
            existing.discipline = discipline
            existing.regulatory_basis = regulatory_basis
            _set_due_fields(existing, due_at, when=now)
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

    _set_task_defaults(
        task,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=task_type,
        discipline=discipline,
        regulatory_basis=regulatory_basis,
        origin=origin,
        due_at=due_at,
        created_by=created_by,
        when=now,
    )

    attach_active_benefit_period_to_task(
        db=db,
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
        existing_active.origin = origin
        existing_active.discipline = discipline
        existing_active.regulatory_basis = regulatory_basis
        _set_due_fields(existing_active, due_at, when=now)
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

    _set_task_defaults(
        task,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=task_type,
        discipline=discipline,
        regulatory_basis=regulatory_basis,
        origin=origin,
        due_at=due_at,
        created_by=created_by,
        when=now,
    )

    attach_active_benefit_period_to_task(
        db=db,
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
    PUBLIC CONTRACT: records release consent only.
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
    Admission authorization — PRODUCTION SAFE (fixed)

    ✅ SOC owned by Admission
    ✅ Task engine untouched
    ✅ Idempotency preserved
    """

    patient = db.query(Patient).filter(Patient.id == patient_id).one()
    tenant_id = getattr(patient, "tenant_id", None)
        
    if not tenant_id:
        raise ValueError("Patient is missing tenant_id")
    
    now = _now_utc()
    
    # ✅ LOAD LATEST ADMISSION (authoritative)
    admission = (
        db.query(Admission)
        .filter(Admission.tenant_id == tenant_id)
        .filter(Admission.patient_id == patient.id)
        .order_by(Admission.created_at.desc())
        .first()
    )

    if not admission:
        admission = Admission(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient.id,
        )

        # safest defaults for current schema
        if hasattr(admission, "status") and getattr(admission, "status", None) is None:
            admission.status = "PENDING"

        # admission_date is owned by SOC workflow
        # do not set during authorization

        if hasattr(admission, "created_at") and getattr(admission, "created_at", None) is None:
            admission.created_at = now

        if hasattr(admission, "created_by"):
            admission.created_by = authorized_by_user_id

        if hasattr(admission, "updated_at"):
            admission.updated_at = now

        if hasattr(admission, "updated_by"):
            admission.updated_by = authorized_by_user_id

        db.add(admission)
        db.flush()

    # --------------------------------------------------
    # PATIENT-LEVEL STAMPS (read by dashboard + charts)
    # --------------------------------------------------

    # SOC immutability: preserve the actual signed timestamp, not the midnight date value.
    if _as_date(getattr(patient, "soc_date", None)) is None:
        patient.soc_date = election_signed_at

    if hasattr(patient, "admission_status"):
        patient.admission_status = "ADMITTED"

    if hasattr(patient, "admission_authorized_at") and getattr(patient, "admission_authorized_at", None) is None:
        patient.admission_authorized_at = election_signed_at

    # --------------------------------------------------
    # AUTHORIZATION + ELECTION SIGNATURE
    # --------------------------------------------------

    if admission.admission_authorized_at is None:
        admission.admission_authorized_at = election_signed_at

    if admission.election_signed_at is None:
        admission.election_signed_at = election_signed_at

    # SOC lives on the admission and the chart reads it from there. Election
    # signature establishes it, and it never moves once established.
    if admission.soc_date is None:
        admission.soc_date = election_signed_at

        if getattr(admission, "effective_date", None) is None:
            admission.effective_date = election_signed_at

        if getattr(admission, "admission_date", None) is None:
            admission.admission_date = election_signed_at
    
    # --------------------------------------------------
    # ✅ STATUS TRANSITION
    # --------------------------------------------------

    if hasattr(admission, "status"):
        admission.status = "AUTHORIZED"

    if not authorized_by_user_id:
        raise ValueError("authorized_by_user_id is required for authorization")

    admission.admission_authorized_by = authorized_by_user_id
    
    admission.updated_at = now
    admission.updated_by = authorized_by_user_id

    # ✅ Patient only gets timestamp update
    if hasattr(patient, "updated_at"):
        patient.updated_at = now

    # --------------------------------------------------
    # ✅ EXISTING TASK ENGINE (UNCHANGED)
    # --------------------------------------------------

    origin_admission = _required_enum_member(TaskOrigin, ["ADMISSION", "SYSTEM"])
    origin_periodic = _required_enum_member(TaskOrigin, ["PERIODIC", "SYSTEM"])

    rn_disc = _required_enum_member(TaskDiscipline, ["RN"])
    sw_disc = _required_enum_member(TaskDiscipline, ["SW", "MSW"])
    chaplain_disc = _required_enum_member(TaskDiscipline, ["CHAPLAIN", "SC"])

    rn_ica_type = _required_enum_member(TaskType, [TASK_INITIAL_RN_ICA])
    msw_ica_type = _required_enum_member(TaskType, [TASK_INITIAL_MSW_ICA])
    sc_ica_type = _required_enum_member(TaskType, [TASK_INITIAL_SC_ICA])
    bereavement_type = _required_enum_member(TaskType, [TASK_INITIAL_BEREAVEMENT])
    noe_type = _required_enum_member(TaskType, [TASK_NOE_DUE])

    admission_basis = _required_enum_member(TaskRegulatoryBasis, ["IDG_REVIEW", "POC_UPDATE"])

    # ✅ KEEP ORIGINAL IDENTITY / UNIQUENESS LOGIC
    _ensure_initial_task_pending_unique(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=rn_ica_type,
        due_at=election_signed_at + timedelta(days=2),
        created_by=authorized_by_user_id,
        discipline=rn_disc,
        regulatory_basis=admission_basis,
        origin=origin_admission,
    )

    _ensure_initial_task_pending_unique(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=msw_ica_type,
        due_at=election_signed_at + timedelta(days=5),
        created_by=authorized_by_user_id,
        discipline=sw_disc,
        regulatory_basis=admission_basis,
        origin=origin_admission,
    )

    _ensure_initial_task_pending_unique(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=sc_ica_type,
        due_at=election_signed_at + timedelta(days=5),
        created_by=authorized_by_user_id,
        discipline=chaplain_disc,
        regulatory_basis=admission_basis,
        origin=origin_admission,
    )

    _ensure_initial_task_pending_unique(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=bereavement_type,
        due_at=election_signed_at + timedelta(days=5),
        created_by=authorized_by_user_id,
        discipline=sw_disc,
        regulatory_basis=admission_basis,
        origin=origin_admission,
    )

    _ensure_initial_task_pending_unique(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=noe_type,
        due_at=election_signed_at + timedelta(days=5),
        created_by=authorized_by_user_id,
        discipline=rn_disc,
        regulatory_basis=admission_basis,
        origin=origin_admission,
    )

    # ✅ IDG REVIEW (RECURRING SAFE)
    idg_type = _optional_enum_member(TaskType, [TASK_IDG_REVIEW])

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