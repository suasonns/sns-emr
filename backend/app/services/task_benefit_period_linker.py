# services/task_benefit_period_linker.py

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task
from app.services.benefit_period_resolver import get_active_benefit_period


def attach_active_benefit_period_to_task(
    db: Session,
    *,
    task: Task,
    tenant_id: UUID,
    patient_id: UUID,
    as_of_date: date | None = None,
) -> Task:
    """
    Attach the currently active benefit period to a task if:
    - task.benefit_period_id is not already set
    - an active benefit period exists for the given patient and date

    This function is intentionally side-effect-light:
    - it mutates only task.benefit_period_id
    - it does not commit
    - it does not add the task to the session
    """

    if task.benefit_period_id is not None:
        return task

    effective_date = as_of_date or task.due_date or date.today()

    active_bp = get_active_benefit_period(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        as_of_date=effective_date,
    )

    if active_bp is not None:
        task.benefit_period_id = active_bp.id

    return task