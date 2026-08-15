# services/idg_task_engine.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.idg_review import IDGReview
from app.models.idg_meeting import IDGMeeting
from app.models.enums import TaskType, TaskStatus


# =========================================================
# GET NEXT IDG MEETING
# =========================================================

def get_next_idg_meeting(
    db: Session,
    *,
    tenant_id,
    patient_id,
    after_datetime: datetime,
) -> Optional[IDGMeeting]:

    return (
        db.query(IDGMeeting)
        .filter(
            IDGMeeting.tenant_id == tenant_id,
            IDGMeeting.patient_id == patient_id,
            IDGMeeting.status == "SCHEDULED",
            IDGMeeting.meeting_date > after_datetime,
        )
        .order_by(IDGMeeting.meeting_date.asc())
        .first()
    )


# =========================================================
# CREATE TASK FOR MEETING
# =========================================================

def ensure_idg_task_for_meeting(
    db: Session,
    *,
    tenant_id,
    patient_id,
    benefit_period_id,
    meeting: IDGMeeting,
) -> Task:

    existing = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.benefit_period_id == benefit_period_id,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status.in_([
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
            ]),
            Task.idg_meeting_id == meeting.id,
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
        origin="CALENDAR",
        due_date=meeting.meeting_date.date(),
        due_at=meeting.meeting_date,
        status=TaskStatus.PENDING,
        idg_meeting_id=meeting.id,
    )

    db.add(task)
    return task


# =========================================================
# COMPLETE TASK (STRICT MATCH BY MEETING)
# =========================================================

def complete_idg_task_for_review(
    db: Session,
    *,
    idg_review: IDGReview,
) -> Optional[Task]:

    task = (
        db.query(Task)
        .filter(
            Task.tenant_id == idg_review.tenant_id,
            Task.patient_id == idg_review.patient_id,
            Task.idg_meeting_id == idg_review.idg_meeting_id,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status.in_([
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
            ]),
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
# SCHEDULE NEXT TASK FROM NEXT MEETING
# =========================================================

def schedule_next_idg_task(
    db: Session,
    *,
    idg_review: IDGReview,
) -> Optional[Task]:

    next_meeting = get_next_idg_meeting(
        db,
        tenant_id=idg_review.tenant_id,
        patient_id=idg_review.patient_id,
        after_datetime=idg_review.review_date,
    )

    if not next_meeting:
        return None

    return ensure_idg_task_for_meeting(
        db=db,
        tenant_id=idg_review.tenant_id,
        patient_id=idg_review.patient_id,
        benefit_period_id=idg_review.benefit_period_id,
        meeting=next_meeting,
    )