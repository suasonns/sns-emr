from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.idg_review import IDGReview
from app.models.idg_meeting import IDGMeeting
from app.models.enums import TaskType, TaskStatus

from app.services.idg_task_generator import create_idg_task_from_meeting


# =========================================================
# COMPLETE TASK WHEN IDG REVIEW FINALIZED
# =========================================================

def complete_idg_task_from_review(
    db: Session,
    *,
    idg_review: IDGReview,
) -> Task | None:

    task = (
        db.query(Task)
        .filter(
            Task.tenant_id == idg_review.tenant_id,
            Task.patient_id == idg_review.patient_id,
            Task.idg_meeting_id == idg_review.idg_meeting_id,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status == TaskStatus.PENDING,
        )
        .first()
    )

    if not task:
        return None

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)

    task.completion_reference_type = "IDG_REVIEW"
    task.completion_reference_id = idg_review.id

    return task


# =========================================================
# SCHEDULE NEXT TASK AFTER REVIEW
# =========================================================

def schedule_next_idg_task(
    db: Session,
    *,
    idg_review: IDGReview,
) -> Task | None:

    next_meeting = (
        db.query(IDGMeeting)
        .filter(
            IDGMeeting.tenant_id == idg_review.tenant_id,
            IDGMeeting.patient_id == idg_review.patient_id,
            IDGMeeting.meeting_date > idg_review.review_date,
        )
        .order_by(IDGMeeting.meeting_date.asc())
        .first()
    )

    if not next_meeting:
        return None

    return create_idg_task_from_meeting(
        db,
        meeting=next_meeting,
    )


# =========================================================
# FULL FINALIZE FLOW (CALL THIS)
# =========================================================

def finalize_idg_review_and_update_tasks(
    db: Session,
    *,
    idg_review: IDGReview,
):

    # 1. complete current task
    complete_idg_task_from_review(
        db=db,
        idg_review=idg_review,
    )

    # 2. schedule next task
    schedule_next_idg_task(
        db=db,
        idg_review=idg_review,
    )