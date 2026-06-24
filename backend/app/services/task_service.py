from __future__ import annotations

import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.med_reconciliation import MedReconciliationItem


# =========================================================
# TASK COMPLETION
# =========================================================

def complete_task(
    *,
    db: Session,
    task_id: UUID,
    completion_reference_type: CompletionReferenceType,
    completion_reference_id: UUID,
    completed_by: UUID | None = None,
) -> Task:
    """
    Compliance-safe task completion.

    REQUIRED:
    - status = COMPLETED
    - completed_at set
    - updated_at set
    - reference stored (audit)
    """

    task = db.query(Task).filter(Task.id == task_id).one_or_none()
    if not task:
        raise ValueError("Task not found")

    if task.status == "COMPLETED":
        raise ValueError("Task already completed")

    task.status = "COMPLETED"
    task.completed_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)  # ✅ REQUIRED FIX

    task.completion_reference_type = completion_reference_type
    task.completion_reference_id = completion_reference_id

    if completed_by:
        task.completed_by = completed_by

    db.commit()
    db.refresh(task)

    return task

# =========================================================
# MED SAFETY TASK CREATION
# =========================================================

def create_med_safety_task(
    db: Session,
    item: MedReconciliationItem,
) -> Task:

    task = Task(
        id=uuid.uuid4(),
        tenant_id=item.tenant_id,
        patient_id=item.patient_id,
        title="Medication Safety Review Required",
        description=f"High-risk med or reaction: {item.med_name_raw}",
        status="PENDING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db.add(task)

    return task