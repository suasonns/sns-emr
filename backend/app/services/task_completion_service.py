from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import TaskStatus, CompletionReferenceType


def complete_task_with_evidence(
    *,
    db: Session,
    task: Task,
    reference_type: CompletionReferenceType,
    reference_id: UUID,
    user_id: UUID | None,
) -> Task:
    """
    Enterprise-grade completion:
    - sets status=COMPLETED
    - requires evidence reference_type + reference_id
    - sets completed_at timestamp
    - never allows completion without evidence (survey-defensible)
    """

    if task.status == TaskStatus.COMPLETED:
        return task

    if reference_type is None or reference_id is None:
        raise HTTPException(status_code=400, detail="Completion evidence is required.")

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)
    task.completion_reference_type = reference_type
    task.completion_reference_id = reference_id

    # optional: provenance (if your Task model supports it)
    # task.completed_by = user_id

    db.add(task)
    return task