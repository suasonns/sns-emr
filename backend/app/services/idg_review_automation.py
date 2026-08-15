# services/idg_review_automation.py

from __future__ import annotations

from datetime import timezone
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.patient import Patient
from app.models.idg_meeting import IDGMeeting
from app.models.enums import (
    TaskType,
    TaskOrigin,
    TaskDiscipline,
    TaskRegulatoryBasis,
    TaskStatus,
)
from app.services.task_benefit_period_linker import (
    attach_active_benefit_period_to_task,
)


# =========================================================
# INTERNAL HELPER (IMPROVED IDEMPOTENCY)
# =========================================================

def _idg_task_exists(db: Session, tenant_id, patient_id) -> bool:
    return (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status.in_([
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
            ]),
        )
        .first()
        is not None
    )


# =========================================================
# UTC SAFE HELPER
# =========================================================

def _to_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# =========================================================
# GET NEXT IDG MEETING (CORE FIX)
# =========================================================

def _get_next_idg_meeting(db: Session, tenant_id) -> IDGMeeting:
    return (
        db.query(IDGMeeting)
        .filter(
            IDGMeeting.tenant_id == tenant_id,
            IDGMeeting.status == "SCHEDULED",
        )
        .order_by(IDGMeeting.meeting_date.asc())
        .first()
    )


# =========================================================
# INITIAL IDG (ON ADMISSION)
# =========================================================

def schedule_initial_idg_on_admission(db, patient: Patient, soc_datetime):
    if not patient or patient.status != "active":
        return

    if _idg_task_exists(db, patient.tenant_id, patient.id):
        return

    meeting = _get_next_idg_meeting(db, patient.tenant_id)
    if not meeting:
        return  # ❗ no meeting = no task

    due_at = _to_utc(meeting.meeting_date)

    task = Task(
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        task_type=TaskType.IDG_REVIEW,
        origin=TaskOrigin.PERIODIC,

        # ✅ FIXED DISCIPLINE
        discipline=TaskDiscipline.IDG_TEAM,

        regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,
        status=TaskStatus.PENDING,
        due_date=due_at.date(),
        due_at=due_at,

        # ✅ CRITICAL LINK
        idg_meeting_id=meeting.id,
    )

    attach_active_benefit_period_to_task(
        db,
        task=task,
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        as_of_date=task.due_date,
    )

    db.add(task)


# =========================================================
# NEXT IDG (AFTER COMPLETION)
# =========================================================

def schedule_next_idg_after_completion(db, completed_task):
    if not completed_task or completed_task.status != TaskStatus.COMPLETED:
        return

    patient = (
        db.query(Patient)
        .filter(Patient.id == completed_task.patient_id)
        .first()
    )

    if not patient or patient.status != "active":
        return

    if _idg_task_exists(
        db,
        completed_task.tenant_id,
        completed_task.patient_id,
    ):
        return

    meeting = _get_next_idg_meeting(db, completed_task.tenant_id)
    if not meeting:
        return

    due_at = _to_utc(meeting.meeting_date)

    next_task = Task(
        tenant_id=completed_task.tenant_id,
        patient_id=completed_task.patient_id,
        task_type=TaskType.IDG_REVIEW,
        origin=TaskOrigin.PERIODIC,

        # ✅ FIXED DISCIPLINE
        discipline=TaskDiscipline.IDG_TEAM,

        regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,
        status=TaskStatus.PENDING,
        due_date=due_at.date(),
        due_at=due_at,

        # ✅ CRITICAL LINK
        idg_meeting_id=meeting.id,
    )

    attach_active_benefit_period_to_task(
        db,
        task=next_task,
        tenant_id=completed_task.tenant_id,
        patient_id=completed_task.patient_id,
        as_of_date=next_task.due_date,
    )

    db.add(next_task)
    