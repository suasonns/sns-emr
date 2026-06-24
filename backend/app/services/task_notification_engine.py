# app/services/task_notification_engine.py
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import TaskStatus, TaskType


# =========================================================
# CONFIGURATION
# =========================================================

NOTICE_3_DAY = 3
NOTICE_1_DAY = 1


# =========================================================
# MAIN ENGINE
# =========================================================

def run_task_notification_engine(
    *,
    db: Session,
    tenant_id: UUID,
) -> None:
    """
    PRE-DUE notification engine.

    This does NOT replace overdue_engine.
    It runs BEFORE tasks become overdue.

    Covers:
    - 3 days before due ✅
    - 1 day before due ✅
    - due today ✅
    """

    today = date.today()

    tasks = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.status != TaskStatus.COMPLETED,
            Task.task_type == TaskType.POC_UPDATE,  # ✅ focused on POC initially
        )
        .all()
    )

    for task in tasks:
        if task.due_date is None:
            continue

        days_until_due = (task.due_date - today).days

        # =========================================================
        # UPCOMING (3 DAYS BEFORE)
        # =========================================================
        if days_until_due == NOTICE_3_DAY:
            _notify(task, "POC DUE IN 3 DAYS")

        # =========================================================
        # UPCOMING (1 DAY BEFORE)
        # =========================================================
        elif days_until_due == NOTICE_1_DAY:
            _notify(task, "POC DUE TOMORROW")

        # =========================================================
        # DUE TODAY
        # =========================================================
        elif days_until_due == 0:
            _notify(task, "POC DUE TODAY")


# =========================================================
# NOTIFICATION HANDLER
# =========================================================

def _notify(task: Task, message: str) -> None:
    """
    Minimal safe notification handler.

    For now:
    - logs to console
    - placeholder for future:
        - UI alerts
        - SMS / email
        - dashboard flags
    """

    print(
        f"[NOTIFICATION] Patient={task.patient_id} "
        f"Task={task.task_type} "
        f"Due={task.due_date} "
        f"Message={message}"
    )
