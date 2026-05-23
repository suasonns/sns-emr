"""
Enterprise-grade IDG review task management.

Purpose:
- Create, complete, and schedule IDG_REVIEW tasks
- Tasks are audit artifacts and MUST be transaction-safe
"""

from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.idg_review import IDGReview


IDG_TASK_TYPE = "IDG_REVIEW"
TASK_STATUS_PENDING = "PENDING"
TASK_STATUS_COMPLETED = "COMPLETED"

DEFAULT_OWNER_DISCIPLINE = "RN"
DEFAULT_ORIGIN = "PERIODIC"


def _plus_14_days(d):
    return d + timedelta(days=14)


def ensure_initial_idg_review_task(
    db: Session,
    *,
    patient_id,
    benefit_period_id,
    anchor_date,
) -> Task:
    """
    Ensure exactly one pending IDG_REVIEW task exists for
    (patient_id, benefit_period_id).

    Creates task due = anchor_date + 14 days.
    """
    due_date = _plus_14_days(anchor_date)

    existing = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.benefit_period_id == benefit_period_id,
            Task.task_type == IDG_TASK_TYPE,
            Task.status == TASK_STATUS_PENDING,
        )
        .first()
    )

    if existing:
        return existing

    task = Task(
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        task_type=IDG_TASK_TYPE,
        discipline=DEFAULT_OWNER_DISCIPLINE,
        origin=DEFAULT_ORIGIN,
        due_date=due_date,
        status=TASK_STATUS_PENDING,
    )

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def complete_current_idg_review_task(
    db: Session,
    *,
    idg_review: IDGReview,
) -> Task | None:
    """
    Complete the pending IDG_REVIEW task for the review’s
    (patient_id, benefit_period_id) and evidence-link it
    to the IDGReview.
    """
    task = (
        db.query(Task)
        .filter(
            Task.patient_id == idg_review.patient_id,
            Task.benefit_period_id == idg_review.benefit_period_id,
            Task.task_type == IDG_TASK_TYPE,
            Task.status == TASK_STATUS_PENDING,
        )
        .order_by(Task.due_date.asc())
        .first()
    )

    if not task:
        return None

    task.status = TASK_STATUS_COMPLETED
    task.completed_at = datetime.utcnow()
    task.completion_reference_type = "IDG_REVIEW"
    task.completion_reference_id = idg_review.id

    db.commit()
    db.refresh(task)
    return task


def schedule_next_idg_review_task(
    db: Session,
    *,
    idg_review: IDGReview,
) -> Task:
    """
    Create the next pending IDG_REVIEW task due 14 days after
    the IDG review_date.

    Ensures no duplicate pending task exists.
    """
    return ensure_initial_idg_review_task(
        db=db,
        patient_id=idg_review.patient_id,
        benefit_period_id=idg_review.benefit_period_id,
        anchor_date=idg_review.review_date,
    )