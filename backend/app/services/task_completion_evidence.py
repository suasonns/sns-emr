# services/task_completion_evidence.py

from __future__ import annotations

import uuid
import logging
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
from app.models.clinical_note import ClinicalNote
from app.domain.forms.form_registry import (
    required_form_family_for_task_discipline,
    note_matches_task_family,
)
from app.services.task_benefit_period_linker import attach_active_benefit_period_to_task

logger = logging.getLogger("sns_emr")


# =========================================================
# COMMON UTILITY FUNCTIONS
# =========================================================

def _now_utc() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _open_status() -> TaskStatus:
    """Return the preferred open status with safe enum fallback."""
    if hasattr(TaskStatus, "PENDING"):
        return TaskStatus.PENDING
    return list(TaskStatus)[0]


def _completed_status() -> TaskStatus:
    """Return the completed status with safe enum fallback."""
    if hasattr(TaskStatus, "COMPLETED"):
        return TaskStatus.COMPLETED
    return list(TaskStatus)[0]


def _resolve_task_origin_periodic() -> TaskOrigin:
    """Return the periodic task origin with safe enum fallback."""
    if hasattr(TaskOrigin, "PERIODIC"):
        return TaskOrigin.PERIODIC
    return list(TaskOrigin)[0]


def _resolve_task_discipline_rn() -> TaskDiscipline:
    """Return the RN discipline with safe enum fallback."""
    if hasattr(TaskDiscipline, "RN"):
        return TaskDiscipline.RN
    return list(TaskDiscipline)[0]


def _resolve_regulatory_basis_idg_review() -> TaskRegulatoryBasis:
    """Return the IDG_REVIEW regulatory basis with safe enum fallback."""
    if hasattr(TaskRegulatoryBasis, "IDG_REVIEW"):
        return TaskRegulatoryBasis.IDG_REVIEW
    return list(TaskRegulatoryBasis)[0]


# =========================================================
# FORM-FAMILY VALIDATION (CRITICAL)
# =========================================================

def _validate_note_family_matches_task(
    db: Session,
    task: Task,
    note_id: uuid.UUID,
) -> None:
    """
    Ensure the clinical note family is valid for the task discipline.

    Compliance rule:
    - RN tasks must complete from clinical note families
    - MSW tasks must complete from psychosocial note families
    - SC tasks must complete from spiritual note families
    """
    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinical note not found",
        )

    note_family = getattr(note, "form_family", None)
    if not note_family:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Clinical note has no form_family assigned",
        )

    if not note_matches_task_family(note_family, getattr(task, "discipline", None)):
        required = required_form_family_for_task_discipline(task.discipline)
        required_value = getattr(required, "value", required) if required is not None else "UNKNOWN"

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Task discipline '{task.discipline}' requires form_family "
                f"'{required_value}', but got '{note_family}'."
            ),
        )


# =========================================================
# IDG AUTO-SCHEDULING
# =========================================================

def _ensure_next_idg_review_task(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    due_at: datetime,
    created_by: Optional[uuid.UUID],
) -> None:
    """
    Ensure there is one open IDG review task for the patient.

    Called after completing an IDG_REVIEW task.
    """
    idg_type = getattr(TaskType, "IDG_REVIEW", None)
    if idg_type is None:
        return

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

    now = _now_utc()

    task_kwargs = {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "patient_id": patient_id,
        "task_type": idg_type,
        "origin": _resolve_task_origin_periodic(),
        "discipline": _resolve_task_discipline_rn(),
        "regulatory_basis": _resolve_regulatory_basis_idg_review(),
        "status": _open_status(),
        "created_by": created_by,
    }

    if hasattr(Task, "due_at"):
        task_kwargs["due_at"] = due_at

    if hasattr(Task, "due_date"):
        task_kwargs["due_date"] = due_at.date()

    if hasattr(Task, "updated_at"):
        task_kwargs["updated_at"] = now

    task = Task(**task_kwargs)

    attach_active_benefit_period_to_task(
        db,
        task=task,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    db.add(task)
    db.flush()


# =========================================================
# MAIN COMPLETION FUNCTION
# =========================================================

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
    Complete a task using explicit evidence references.

    Compliance rule:
    - status must become COMPLETED
    - completed_at must be populated
    - completion_reference_type must be populated
    - completion_reference_id must be populated
    - completed_by is recorded when the model supports it

    Idempotency:
    - If the task is already completed with the same evidence, return it.
    - If the task is already completed with different evidence, raise 409.
    """
    task = db.query(Task).filter(Task.id == task_id).one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if completion_reference_type is None or completion_reference_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completion requires evidence",
        )

    completed_status = _completed_status()

    existing_type = getattr(task, "completion_reference_type", None)
    existing_id = getattr(task, "completion_reference_id", None)

    # =========================================================
    # IDEMPOTENCY
    # =========================================================
    if task.status == completed_status:
        if existing_type == completion_reference_type and existing_id == completion_reference_id:
            return task

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task already completed with different evidence",
        )

    # =========================================================
    # FORM-FAMILY ENFORCEMENT
    # =========================================================
    if completion_reference_type in (
        CompletionReferenceType.NOTE,
        CompletionReferenceType.CLINICAL_NOTE,
    ):
        _validate_note_family_matches_task(
            db=db,
            task=task,
            note_id=completion_reference_id,
        )

    when = completed_at or _now_utc()

    task.status = completed_status

    if hasattr(task, "completed_at"):
        task.completed_at = when

    if hasattr(task, "completion_reference_type"):
        task.completion_reference_type = completion_reference_type

    if hasattr(task, "completion_reference_id"):
        task.completion_reference_id = completion_reference_id

    if hasattr(task, "completed_by"):
        task.completed_by = completed_by

    if hasattr(task, "updated_at"):
        task.updated_at = when

    db.add(task)
    db.flush()

    logger.info(
        "Completed task task_id=%s task_type=%s evidence_type=%s evidence_id=%s",
        str(getattr(task, "id", None)),
        str(getattr(getattr(task, "task_type", None), "value", getattr(task, "task_type", None))),
        str(getattr(completion_reference_type, "value", completion_reference_type)),
        str(completion_reference_id),
    )

    # =========================================================
    # IDG SCHEDULING
    # =========================================================
    if getattr(task, "task_type", None) == getattr(TaskType, "IDG_REVIEW", None):
        _ensure_next_idg_review_task(
            db,
            tenant_id=task.tenant_id,
            patient_id=task.patient_id,
            due_at=when + timedelta(days=15),
            created_by=completed_by,
        )

    return task
