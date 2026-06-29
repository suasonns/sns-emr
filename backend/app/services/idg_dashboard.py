from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import TaskType, TaskStatus


# =========================================================
# UPCOMING IDG TASKS
# =========================================================

def get_upcoming_idg_tasks(
    db: Session,
    *,
    tenant_id,
):
    return (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status == TaskStatus.PENDING,
        )
        .order_by(Task.due_at.asc())
        .all()
    )


# =========================================================
# OVERDUE IDG TASKS
# =========================================================

def get_overdue_idg_tasks(
    db: Session,
    *,
    tenant_id,
):
    now = datetime.utcnow()

    return (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status == TaskStatus.PENDING,
            Task.due_at < now,
        )
        .order_by(Task.due_at.asc())
        .all()
    )