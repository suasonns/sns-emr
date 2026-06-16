from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import (
    TaskStatus,
    TaskType,
    TaskOrigin,
    TaskDiscipline,
    TaskRegulatoryBasis,
    CompletionReferenceType,
)
from app.services.task_benefit_period_linker import attach_active_benefit_period_to_task


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _open_status() -> TaskStatus:
    if hasattr(TaskStatus, "PENDING"):
        return TaskStatus.PENDING
    return list(TaskStatus)[0]


def _completed_status() -> TaskStatus:
    if hasattr(TaskStatus, "COMPLETED"):
        return TaskStatus.COMPLETED
    return list(TaskStatus)[0]


def _ensure_next_idg_review_task(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    due_at: datetime,
    created_by: Optional[uuid.UUID],
) -> None:
    """
    Compliance: completing an IDG_REVIEW must schedule the next due +15 days.
    Idempotent: if an open IDG_REVIEW already exists, do nothing.
    """
    idg_type = getattr(TaskType, "IDG_REVIEW", None)
    if idg_type is None:
        return  # environment doesn't have IDG_REVIEW task type

    existing = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.task_type == idg_type,
            Task.status == _open_status(),
        )
        .first()
    )
    if existing:
        return

    rn = getattr(TaskDiscipline, "RN", list(TaskDiscipline)[0])
    basis = getattr(TaskRegulatoryBasis, "IDG_REVIEW", list(TaskRegulatoryBasis)[0])
    origin = getattr(TaskOrigin, "PERIODIC", list(TaskOrigin)[0])

    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=idg_type,
        origin=origin,
        discipline=rn,
        regulatory_basis=basis,
        status=_open_status(),
        created_by=str(created_by) if created_by else None,
    )

    if hasattr(task, "due_at"):
        task.due_at = due_at
    if hasattr(task, "due_date"):
        task.due_date = due_at.date()

    attach_active_benefit_period_to_task(
        db,
        task=task,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    db.add(task)
    db.flush()


def complete_task_with_evidence(
    db: Session,
    *,
    task_id: uuid.UUID,
    completion_reference_type: CompletionReferenceType | None,
    completion_reference_id: uuid.UUID | None,
    completed_by: uuid.UUID | None,
    completed_at: Optional[datetime] = None,
) -> Task:
    """
    Production-grade compliance gate.

    CONTRACT (must match existing repo tests and call sites):
      complete_task_with_evidence(
        db,
        task_id=...,
        completion_reference_type=...,
        completion_reference_id=...,
        completed_by=...,
      )

    ENFORCEMENT:
    - Cannot complete without evidence (type + id)
    - Sets completed_at and evidence fields
    - IDG_REVIEW completion schedules next due +15 days (idempotent)
    """
    task = db.query(Task).filter(Task.id == task_id).one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if completion_reference_type is None or completion_reference_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completion requires evidence: completion_reference_type and completion_reference_id are required",
        )

    completed_status = _completed_status()

    # Idempotency: if already completed with same evidence, no-op
    if task.status == completed_status:
        if (
            getattr(task, "completion_reference_type", None) == completion_reference_type
            and getattr(task, "completion_reference_id", None) == completion_reference_id
        ):
            return task

    when = completed_at or _now_utc()
    was_completed = task.status == completed_status

    task.status = completed_status

    if hasattr(task, "completed_at"):
        task.completed_at = when

    if hasattr(task, "completion_reference_type"):
        task.completion_reference_type = completion_reference_type

    if hasattr(task, "completion_reference_id"):
        task.completion_reference_id = completion_reference_id

    if hasattr(task, "completed_by"):
        task.completed_by = completed_by

    db.add(task)
    db.flush()

    # ✅ IDG cadence: completion schedules next due +15 days
    if not was_completed and getattr(task, "task_type", None) == getattr(TaskType, "IDG_REVIEW", None):
        _ensure_next_idg_review_task(
            db,
            tenant_id=task.tenant_id,
            patient_id=task.patient_id,
            due_at=when + timedelta(days=15),
            created_by=completed_by,
        )

    return task