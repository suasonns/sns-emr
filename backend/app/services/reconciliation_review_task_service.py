from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import TaskStatus, TaskType, TaskDiscipline


RECON_REVIEW_REFERENCE_TYPE = "MED_RECONCILIATION_ITEM"
RECON_REVIEW_ALERT_PREFIX = "MED_RECON_REVIEW_ITEM"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_alert_reason(item_id) -> str:
    return f"{RECON_REVIEW_ALERT_PREFIX}:{item_id}"


def get_open_reconciliation_review_task_for_item(
    *,
    db: Session,
    reconciliation_item_id,
) -> Optional[Task]:
    alert_reason = _build_alert_reason(reconciliation_item_id)

    return (
        db.query(Task)
        .filter(Task.alert_reason == alert_reason)
        .filter(Task.status.in_([TaskStatus.PENDING, TaskStatus.OVERDUE]))
        .first()
    )


def create_reconciliation_task_if_needed(
    *,
    db: Session,
    tenant_id,
    patient_id,
    import_id: Optional[Any] = None,
    item_id: Optional[Any] = None,
    comparison: Optional[Any] = None,
    assigned_discipline: TaskDiscipline = TaskDiscipline.RN,
) -> Optional[Task]:
    if item_id is None or comparison is None:
        return None

    existing = get_open_reconciliation_review_task_for_item(
        db=db,
        reconciliation_item_id=item_id,
    )
    if existing:
        return existing

    match_type = getattr(comparison, "match_type", None)
    discrepancy_flags = getattr(comparison, "discrepancy_flags", None) or []

    needs_task = False

    if match_type in {"NO_MATCH", "PARTIAL_MATCH", "CONFLICT"}:
        needs_task = True

    if discrepancy_flags:
        needs_task = True

    if not needs_task:
        return None

    now = _utcnow()
    due_at = now + timedelta(hours=24)

    task = Task(
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=TaskType.CLINICAL_REVIEW_REQUIRED,
        status=TaskStatus.PENDING,
        discipline=assigned_discipline,
        due_date=due_at,
        sla_start_at=now,
        sla_due_at=due_at,
        alert_reason=_build_alert_reason(item_id),
        escalation_reason="Medication reconciliation discrepancy requires review",
        reference_type=RECON_REVIEW_REFERENCE_TYPE,
        reference_id=item_id,
    )

    db.add(task)
    db.flush()

    return task


def complete_reconciliation_review_task_if_exists(
    *,
    db: Session,
    reconciliation_item_id,
    completion_reference_type: str,
    completion_reference_id,
) -> Optional[Task]:
    task = get_open_reconciliation_review_task_for_item(
        db=db,
        reconciliation_item_id=reconciliation_item_id,
    )
    if not task:
        return None

    now = _utcnow()

    task.status = TaskStatus.COMPLETED
    task.completed_at = now
    task.completion_reference_type = completion_reference_type
    task.completion_reference_id = completion_reference_id

    return task