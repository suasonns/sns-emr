from __future__ import annotations

from datetime import timedelta, timezone
from sqlalchemy.orm import Session

from app.models.task import Task
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
# INTERNAL HELPER (IDEMPOTENT)
# =========================================================

def _idg_task_exists(db: Session, tenant_id, patient_id) -> bool:
    return (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status == TaskStatus.PENDING,
        )
        .first()
        is not None
    )


# =========================================================
# INITIAL IDG (ON ADMISSION)
# =========================================================

def schedule_initial_idg_on_admission(db, patient, soc_datetime):
    """
    Enterprise guarantees:
    - No duplicate IDG tasks
    - due_at + due_date set
    - BP attached
    - status explicitly set
    """

    if _idg_task_exists(db, patient.tenant_id, patient.id):
        return  # ✅ idempotency

    due_at = soc_datetime.astimezone(timezone.utc) + timedelta(days=15)

    task = Task(
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        task_type=TaskType.IDG_REVIEW,
        origin=TaskOrigin.PERIODIC,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,
        status=TaskStatus.PENDING,  # ✅ explicit
        due_date=due_at.date(),
        due_at=due_at,
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
    """
    Enterprise guarantees:
    - Safe guard if completed_at is missing
    - No duplicate scheduled IDG
    - due_at enforced
    - BP attached
    """

    if not completed_task.completed_at:
        return  # ✅ safety guard

    if _idg_task_exists(
        db,
        completed_task.tenant_id,
        completed_task.patient_id,
    ):
        return  # ✅ idempotency

    due_at = (
        completed_task.completed_at.astimezone(timezone.utc)
        + timedelta(days=15)
    )

    next_task = Task(
        tenant_id=completed_task.tenant_id,
        patient_id=completed_task.patient_id,
        task_type=TaskType.IDG_REVIEW,
        origin=TaskOrigin.PERIODIC,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,
        status=TaskStatus.PENDING,  # ✅ explicit
        due_date=due_at.date(),
        due_at=due_at,
    )

    attach_active_benefit_period_to_task(
        db,
        task=next_task,
        tenant_id=completed_task.tenant_id,
        patient_id=completed_task.patient_id,
        as_of_date=next_task.due_date,
    )

    db.add(next_task)
