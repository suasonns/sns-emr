from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task


def complete_task(
    *,
    db: Session,
    task_id: UUID,
    completion_reference_type: str,
    completion_reference_id: UUID,
    completed_by: UUID | None = None,
) -> Task:
    """
    Compliance-safe task completion.

    Guarantees:
    - status = COMPLETED
    - completed_at is set
    - evidence reference is present
    """

    task = db.query(Task).filter(Task.id == task_id).one_or_none()
    if not task:
        raise ValueError("Task not found")

    if task.status == "COMPLETED":
        raise ValueError("Task already completed")

    task.status = "COMPLETED"
    task.completed_at = datetime.now(timezone.utc)
    task.completion_reference_type = completion_reference_type
    task.completion_reference_id = completion_reference_id

    if completed_by:
        task.created_by = completed_by

    db.commit()
    db.refresh(task)
    return task