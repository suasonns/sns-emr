from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.visit import Visit
from app.models.enums import (
    TaskStatus,
    TaskType,
    CompletionReferenceType,
)
from app.services.task_completion_service import complete_task_with_evidence


def auto_complete_tasks_for_visit(
    *,
    db: Session,
    visit: Visit,
    user_id: UUID | None,
) -> None:
    """
    Automatically complete tasks satisfied by a finalized visit.

    Compliance rules:
    - Completion is evidence-based (VISIT)
    - Uses canonical completion service
    - DB CHECK constraint enforces correctness
    """

    if not visit.finalized_at:
        return

    # Tasks this visit can satisfy
    completable_task_types = {
        TaskType.INITIAL_RN_ICA,
        TaskType.INITIAL_MSW_ICA,
        TaskType.INITIAL_SC_ICA,
        TaskType.INITIAL_BEREAVEMENT,
        TaskType.POC_UPDATE,
    }

    tasks = (
        db.query(Task)
        .filter(
            Task.patient_id == visit.patient_id,
            Task.status != TaskStatus.COMPLETED,
            Task.task_type.in_(completable_task_types),
        )
        .all()
    )

    for task in tasks:
        complete_task_with_evidence(
            db=db,
            task=task,
            reference_type=CompletionReferenceType.VISIT,
            reference_id=visit.id,
            user_id=user_id,
        )

    # DO NOT commit here — caller controls transaction