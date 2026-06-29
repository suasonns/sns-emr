from __future__ import annotations

import uuid
from datetime import datetime, timezone, time

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskStatus,
    TaskDiscipline,
    TaskOrigin,
    TaskRegulatoryBasis,
)


def create_sfv_required_task(
    *,
    db: Session,
    patient_id,
    visit_id,
    due_date,
    user_id,
    discipline,
):
    """
    Create one active SFV task per patient.

    Rules:
    - Only one active SFV task is allowed per patient/tenant.
    - This creates the obligation only.
    - It does NOT complete the SFV in the same encounter.
    - Populates all known required task SLA fields.
    """

    now = datetime.now(timezone.utc)

    tenant_id = db.info.get("tenant_id")
    if not tenant_id:
        raise ValueError("Missing tenant_id in DB context")

    # Prevent duplicate active SFV tasks
    existing = (
        db.query(Task)
        .filter(
            and_(
                Task.tenant_id == tenant_id,
                Task.patient_id == patient_id,
                Task.task_type == TaskType.SFV,
                Task.status.in_(
                    [
                        TaskStatus.PENDING,
                        TaskStatus.IN_PROGRESS,
                        TaskStatus.OVERDUE,
                    ]
                ),
            )
        )
        .first()
    )

    if existing:
        return existing

    # Safe discipline conversion
    try:
        task_discipline = TaskDiscipline(str(discipline).strip().upper())
    except Exception:
        task_discipline = TaskDiscipline.RN

    # Normalize due_date / due_at / SLA fields
    if isinstance(due_date, datetime):
        due_at_value = due_date
        due_date_value = due_date.date()
    else:
        due_date_value = due_date
        due_at_value = datetime.combine(
            due_date,
            time(23, 59, 59),
            tzinfo=timezone.utc,
        )

    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=TaskType.SFV,
        status=TaskStatus.PENDING,
        discipline=task_discipline,
        created_at=now,
        updated_at=now,
        created_by=user_id,
        due_date=due_date_value,
        due_at=due_at_value,
        sla_start_at=now,
        sla_due_at=due_at_value,
        origin=TaskOrigin.SYSTEM,
        regulatory_basis=TaskRegulatoryBasis.CONDITION_TRIGGER,
        alert_reason="SFV_TRIGGER",
    )

    db.add(task)
    return task