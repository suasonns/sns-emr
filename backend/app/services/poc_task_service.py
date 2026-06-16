from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.care_model_engine import (
    determine_care_model,
    should_anchor_poc_from_rn_visit,
)
from app.models.enums import TaskOrigin, TaskStatus, TaskType
from app.models.patient import Patient
from app.models.task import Task
from app.models.visit import Visit


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_visit_type(value: Optional[str]) -> str:
    return (value or "").strip().upper()


def _resolve_visit_service_date(visit: Visit) -> date:
    candidate_values = [
        getattr(visit, "visit_date", None),
        getattr(visit, "visit_datetime", None),
        getattr(visit, "finalized_at", None),
        getattr(visit, "created_at", None),
    ]

    for value in candidate_values:
        if value is None:
            continue

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

    raise ValueError("Visit has no usable service date")


def _active_poc_statuses() -> list[TaskStatus]:
    statuses: list[TaskStatus] = []

    for name in ("OPEN", "PENDING", "DUE"):
        member = getattr(TaskStatus, name, None)
        if member is not None:
            statuses.append(member)

    if not statuses:
        raise ValueError(
            "TaskStatus enum has no usable active statuses. Expected at least PENDING or DUE."
        )

    return statuses


def _default_new_task_status() -> TaskStatus:
    for name in ("OPEN", "PENDING", "DUE"):
        member = getattr(TaskStatus, name, None)
        if member is not None:
            return member

    raise ValueError(
        "TaskStatus enum has no usable creation status. Expected OPEN, PENDING, or DUE."
    )


def _default_manual_origin():
    for name in ("MANUAL", "SYSTEM"):
        member = getattr(TaskOrigin, name, None)
        if member is not None:
            return member
    raise ValueError("TaskOrigin enum has no usable MANUAL or SYSTEM member")


def _default_periodic_origin():
    for name in ("PERIODIC", "SYSTEM"):
        member = getattr(TaskOrigin, name, None)
        if member is not None:
            return member
    raise ValueError("TaskOrigin enum has no usable PERIODIC or SYSTEM member")


def get_open_poc_task(db: Session, patient_id) -> Optional[Task]:
    active_statuses = _active_poc_statuses()

    return (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.patient_id == patient_id,
            Task.task_type == TaskType.POC_UPDATE,
            Task.status.in_(active_statuses),
        )
        .order_by(Task.due_date.asc(), Task.created_at.asc())
        .first()
    )


def get_periodic_poc_task_for_due_date(
    *,
    db: Session,
    patient_id,
    due_date: date,
) -> Optional[Task]:
    """
    Return the existing periodic POC task for the exact patient + due_date cycle,
    regardless of whether it is pending, due, or completed.

    This is the key function that prevents duplicate same-cycle POC obligations.
    """
    periodic_origin = _default_periodic_origin()

    return (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.patient_id == patient_id,
            Task.task_type == TaskType.POC_UPDATE,
            Task.origin == periodic_origin,
            Task.due_date == due_date,
        )
        .order_by(Task.created_at.asc())
        .first()
    )


def create_poc_task(
    *,
    db: Session,
    patient: Patient,
    due_date: date,
    origin,
    benefit_period_id=None,
    visit: Optional[Visit] = None,
) -> Task:
    now = utcnow()

    # ---------------------------------------------------------
    # Resolve required compliance fields
    # ---------------------------------------------------------
    discipline_value = None

    if visit is not None:
        discipline_value = getattr(visit, "visit_discipline", None)

    if not discipline_value:
        discipline_value = "RN"

    regulatory_basis_value = "POC_UPDATE"
    alert_reason_value = "POC_UPDATE"

    task = Task(
        task_type=TaskType.POC_UPDATE,
        status=_default_new_task_status(),
        due_date=due_date,
        origin=origin,
        discipline=discipline_value,
        regulatory_basis=regulatory_basis_value,
        alert_reason=alert_reason_value,
        created_at=now,
        updated_at=now,
    )

    if hasattr(task, "id") and getattr(task, "id", None) is None:
        import uuid
        task.id = uuid.uuid4()

    if hasattr(task, "patient_id"):
        task.patient_id = patient.id

    if hasattr(task, "tenant_id"):
        task.tenant_id = getattr(patient, "tenant_id", None)

    if hasattr(task, "benefit_period_id"):
        task.benefit_period_id = benefit_period_id

    if hasattr(task, "created_by"):
        task.created_by = (
            getattr(visit, "finalized_by", None)
            or getattr(visit, "provider_id", None)
            or getattr(patient, "created_by", None)
        )

    if hasattr(task, "updated_by"):
        task.updated_by = (
            getattr(visit, "finalized_by", None)
            or getattr(visit, "provider_id", None)
        )

    db.add(task)
    db.flush()
    return task


def complete_task_with_visit_evidence(
    *,
    task: Task,
    visit: Visit,
) -> None:
    task.status = TaskStatus.COMPLETED
    task.completed_at = utcnow()
    task.completion_reference_type = "VISIT"
    task.completion_reference_id = visit.id

    if hasattr(task, "updated_at"):
        task.updated_at = utcnow()

    if hasattr(task, "updated_by"):
        task.updated_by = (
            getattr(visit, "finalized_by", None)
            or getattr(visit, "provider_id", None)
        )


def attach_visit_as_same_cycle_evidence(
    *,
    task: Task,
    visit: Visit,
) -> Task:
    """
    Same-cycle update / amendment-safe behavior:
    - Do NOT create a duplicate POC task
    - Reuse the existing cycle task
    - Refresh audit fields
    - Optionally link latest supporting visit evidence

    If your policy is 'one task, many contributing visits', you can later replace
    this with a dedicated task_evidence table. For now this keeps the single cycle task
    and refreshes the latest evidence pointer.
    """
    if hasattr(task, "updated_at"):
        task.updated_at = utcnow()

    if hasattr(task, "updated_by"):
        task.updated_by = (
            getattr(visit, "finalized_by", None)
            or getattr(visit, "provider_id", None)
        )

    # Only update evidence pointer if the task is still active;
    # if already completed, keep the existing completion semantics intact.
    current_status = getattr(task, "status", None)
    if current_status in _active_poc_statuses():
        if hasattr(task, "completion_reference_type"):
            task.completion_reference_type = "VISIT"
        if hasattr(task, "completion_reference_id"):
            task.completion_reference_id = visit.id

    return task


def upsert_next_periodic_poc_task(
    *,
    db: Session,
    patient: Patient,
    anchor_visit: Visit,
    benefit_period_id=None,
) -> Task:
    """
    RULE:
    - One periodic POC task per patient per cycle (due_date)
    - If same-cycle task already exists, reuse it
    - If open task exists but due_date needs movement, update it
    - Only create if no matching cycle task exists at all
    """
    anchor_date = _resolve_visit_service_date(anchor_visit)
    next_due_date = anchor_date + timedelta(days=14)

    # ---------------------------------------------------------
    # 1) Exact same cycle already exists → reuse it
    # ---------------------------------------------------------
    existing_same_due = get_periodic_poc_task_for_due_date(
        db=db,
        patient_id=patient.id,
        due_date=next_due_date,
    )
    if existing_same_due:
        return attach_visit_as_same_cycle_evidence(
            task=existing_same_due,
            visit=anchor_visit,
        )

    # ---------------------------------------------------------
    # 2) Existing active/open POC task exists → move/update it
    # ---------------------------------------------------------
    existing_open = get_open_poc_task(db, patient.id)
    if existing_open:
        existing_open.due_date = next_due_date

        if hasattr(existing_open, "origin"):
            existing_open.origin = _default_periodic_origin()

        if hasattr(existing_open, "updated_at"):
            existing_open.updated_at = utcnow()

        if hasattr(existing_open, "updated_by"):
            existing_open.updated_by = (
                getattr(anchor_visit, "finalized_by", None)
                or getattr(anchor_visit, "provider_id", None)
            )

        if benefit_period_id is not None and hasattr(existing_open, "benefit_period_id"):
            existing_open.benefit_period_id = benefit_period_id

        return existing_open

    # ---------------------------------------------------------
    # 3) Truly new cycle → create
    # ---------------------------------------------------------
    return create_poc_task(
        db=db,
        patient=patient,
        due_date=next_due_date,
        origin=_default_periodic_origin(),
        benefit_period_id=benefit_period_id,
        visit=anchor_visit,
    )


def create_and_complete_same_day_crisis_poc(
    *,
    db: Session,
    patient: Patient,
    visit: Visit,
    benefit_period_id=None,
) -> Task:
    today_due = _resolve_visit_service_date(visit)

    existing_same_due = get_periodic_poc_task_for_due_date(
        db=db,
        patient_id=patient.id,
        due_date=today_due,
    )
    if existing_same_due:
        return attach_visit_as_same_cycle_evidence(
            task=existing_same_due,
            visit=visit,
        )

    task = create_poc_task(
        db=db,
        patient=patient,
        due_date=today_due,
        origin=_default_manual_origin(),
        benefit_period_id=benefit_period_id,
        visit=visit,
    )
    complete_task_with_visit_evidence(task=task, visit=visit)
    db.flush()
    return task


def handle_poc_on_finalized_rn_visit(
    *,
    db: Session,
    patient: Patient,
    visit: Visit,
    benefit_period_id=None,
) -> Optional[Task]:
    """
    Compliance behavior:

    ROUTINE + RN_ONLY:
      - any finalized RN visit anchors next POC due visit_date + 14

    ROUTINE + RN support present (LVN and/or CHHA):
      - only finalized supervisory RN visit anchors next POC due +14

    WOUND override:
      - any finalized RN visit anchors next POC due +14 regardless of supervisory status

    CRISIS:
      - every finalized RN visit triggers same-day POC and completes it with visit evidence
    """
    visit_type = normalize_visit_type(getattr(visit, "visit_type", None))
    if visit_type != "RN":
        return None

    decision = determine_care_model(
        has_chha=bool(getattr(patient, "has_chha", False)),
        has_lvn=bool(getattr(patient, "has_lvn", False)),
        has_wounds=bool(getattr(patient, "has_wounds", False)),
        acuity_state=getattr(patient, "acuity_state", None),
    )

    if decision.poc_trigger_policy.value == "SAME_DAY_ANY_RN_CRISIS":
        return create_and_complete_same_day_crisis_poc(
            db=db,
            patient=patient,
            visit=visit,
            benefit_period_id=benefit_period_id,
        )

    should_anchor = should_anchor_poc_from_rn_visit(
        is_supervisory_visit=bool(getattr(visit, "is_supervisory", False)),
        decision=decision,
    )

    if not should_anchor:
        return None

    return upsert_next_periodic_poc_task(
        db=db,
        patient=patient,
        anchor_visit=visit,
        benefit_period_id=benefit_period_id,
    )