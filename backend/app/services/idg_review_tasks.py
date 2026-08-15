# services/idg_review_tasks.py

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.idg_review import IDGReview
from app.models.enums import TaskType, TaskStatus


def _plus_14_days(d):
    return d + timedelta(days=14)


def ensure_initial_idg_review_task(
    db: Session,
    *,
    tenant_id,
    patient_id,
    benefit_period_id,
    anchor_date,
) -> Task:

    due_date = _plus_14_days(anchor_date)

    existing = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.benefit_period_id == benefit_period_id,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status == TaskStatus.PENDING,
        )
        .first()
    )

    if existing:
        return existing

    task = Task(
        tenant_id=tenant_id,
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        task_type=TaskType.IDG_REVIEW,
        discipline="IDG_TEAM",
        origin="PERIODIC",
        due_date=due_date,
        status=TaskStatus.PENDING,
    )

    db.add(task)
    return task


def complete_current_idg_review_task(
    db: Session,
    *,
    idg_review: IDGReview,
) -> Task | None:

    task = (
        db.query(Task)
        .filter(
            Task.tenant_id == idg_review.tenant_id,
            Task.patient_id == idg_review.patient_id,
            Task.benefit_period_id == idg_review.benefit_period_id,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status == TaskStatus.PENDING,
        )
        .order_by(Task.due_date.asc())
        .first()
    )

    if not task:
        return None

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)
    task.completion_reference_type = "IDG_REVIEW"
    task.completion_reference_id = idg_review.id

    return task


def schedule_next_idg_review_task(
    db: Session,
    *,
    idg_review: IDGReview,
) -> Task:

    return ensure_initial_idg_review_task(
        db=db,
        tenant_id=idg_review.tenant_id,
        patient_id=idg_review.patient_id,
        benefit_period_id=idg_review.benefit_period_id,
        anchor_date=idg_review.review_date,
    )
    