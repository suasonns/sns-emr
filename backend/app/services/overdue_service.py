from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import TaskStatus, TaskType


def mark_overdue_poc_tasks(db: Session) -> None:
    """
    Mark ROUTINE POC_UPDATE tasks as overdue when SLA expires.
    """

    now = datetime.now(timezone.utc)

    overdue_tasks = (
        db.query(Task)
        .filter(
            Task.task_type == TaskType.POC_UPDATE,
            Task.status == TaskStatus.PENDING,
            Task.sla_due_at < now,
            Task.is_overdue == False,
        )
        .all()
    )

    for task in overdue_tasks:

        # ✅ BASIC OVERDUE FLAG
        task.is_overdue = True

        # ✅ ESCALATION LEVEL
        days_overdue = (now - task.sla_due_at).days

        if days_overdue >= 7:
            task.escalation_level = 3
        elif days_overdue >= 3:
            task.escalation_level = 2
        else:
            task.escalation_level = 1

        task.escalated_at = now
        task.escalation_reason = "SLA_EXPIRED"

        # ✅ REQUIRED FOR DB integrity
        task.updated_at = now

    db.commit()