from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.idg_meeting import IDGMeeting
from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskStatus,
    TaskOrigin,
    TaskDiscipline,
    TaskRegulatoryBasis,
)


# =========================================================
# CHECK IF TASK EXISTS FOR MEETING
# =========================================================

def _task_exists_for_meeting(
    db: Session,
    *,
    meeting_id,
) -> bool:
    return (
        db.query(Task)
        .filter(Task.idg_meeting_id == meeting_id)
        .first()
        is not None
    )


# =========================================================
# CREATE TASK FOR ONE MEETING
# =========================================================

def create_idg_task_from_meeting(
    db: Session,
    *,
    meeting: IDGMeeting,
) -> Task | None:

    # ✅ Prevent duplicates
    if _task_exists_for_meeting(db, meeting_id=meeting.id):
        return None

    task = Task(
        tenant_id=meeting.tenant_id,
        patient_id=meeting.patient_id,
        benefit_period_id=meeting.benefit_period_id,

        task_type=TaskType.IDG_REVIEW,
        status=TaskStatus.PENDING,

        origin=TaskOrigin.CALENDAR,
        discipline=TaskDiscipline.IDG_TEAM,

        regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,

        due_date=meeting.meeting_date.date(),
        due_at=meeting.meeting_date,

        # ✅ CRITICAL LINK
        idg_meeting_id=meeting.id,
    )

    db.add(task)
    return task


# =========================================================
# GENERATE TASKS FOR A LIST OF MEETINGS
# =========================================================

def generate_tasks_from_meetings(
    db: Session,
    *,
    meetings: List[IDGMeeting],
) -> List[Task]:

    created_tasks: List[Task] = []

    for meeting in meetings:

        task = create_idg_task_from_meeting(
            db,
            meeting=meeting,
        )

        if task:
            created_tasks.append(task)

    return created_tasks


# =========================================================
# GENERATE TASKS FOR FUTURE MEETINGS (DATABASE QUERY)
# =========================================================

def generate_tasks_for_patient_meetings(
    db: Session,
    *,
    tenant_id,
    patient_id,
) -> List[Task]:

    meetings = (
        db.query(IDGMeeting)
        .filter(
            IDGMeeting.tenant_id == tenant_id,
            IDGMeeting.patient_id == patient_id,
            IDGMeeting.status == "SCHEDULED",
        )
        .all()
    )

    return generate_tasks_from_meetings(
        db=db,
        meetings=meetings,
    )