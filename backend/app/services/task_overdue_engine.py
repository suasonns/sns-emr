from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.task import Task


# --- Policy constants (survey defensible defaults) ---
ESCALATION_DAYS = 7  # days after due_date to escalate


def evaluate_task_timeliness(db: Session, *, as_of: date | None = None) -> dict:
    """
    Evaluates all non-completed tasks and updates status to:
      - OVERDUE if due_date < today
      - ESCALATED if overdue beyond ESCALATION_DAYS

    Returns counts for audit/logging.
    """
    today = as_of or date.today()

    updated = {
        "overdue": 0,
        "escalated": 0,
    }

    # Only tasks that are still actionable
    tasks = (
        db.query(Task)
        .filter(Task.status.in_(["PENDING", "OVERDUE"]))
        .all()
    )

    for task in tasks:
        if task.due_date >= today:
            continue

        days_overdue = (today - task.due_date).days

        # Escalation threshold
        if days_overdue >= ESCALATION_DAYS:
            if task.status != "ESCALATED":
                task.status = "ESCALATED"
                updated["escalated"] += 1
        else:
            if task.status != "OVERDUE":
                task.status = "OVERDUE"
                updated["overdue"] += 1

    if updated["overdue"] or updated["escalated"]:
        db.commit()

    return updated