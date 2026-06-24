from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import TaskStatus, CompletionReferenceType
from app.domain.forms.form_registry import (
    required_form_family_for_task_discipline,
    note_matches_task_family,
)
from app.models.clinical_note import ClinicalNote


def _validate_note_family_matches_task(
    db: Session,
    task: Task,
    note_id: UUID,
) -> None:
    """
    Enforce discipline-aware note family matching.

    Examples:
    - RN task -> CLINICAL note family
    - MSW task -> PSYCHOSOCIAL note family
    - SC task -> SPIRITUAL note family
    """
    note = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.id == note_id)
        .first()
    )

    if not note:
        raise HTTPException(status_code=404, detail="Clinical note not found.")

    note_family = getattr(note, "form_family", None)

    if not note_family:
        raise HTTPException(
            status_code=422,
            detail="Clinical note has no form_family assigned.",
        )

    if not note_matches_task_family(note_family, getattr(task, "discipline", None)):
        required_family = required_form_family_for_task_discipline(
            getattr(task, "discipline", None)
        )

        raise HTTPException(
            status_code=409,
            detail=(
                f"Task discipline '{getattr(task, 'discipline', None)}' requires "
                f"form_family '{required_family.value if required_family else 'UNKNOWN'}', "
                f"but got '{note_family}'."
            ),
        )


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
    - enforces discipline-aware note family validation
    - audit-safe (updated_at, updated_by)
    """

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------
    if not getattr(task, "tenant_id", None):
        raise HTTPException(
            status_code=500,
            detail="Task missing tenant context",
        )

    # Already completed → idempotent behavior
    if task.status == TaskStatus.COMPLETED:
        return task

    if reference_type is None or reference_id is None:
        raise HTTPException(
            status_code=400,
            detail="Completion evidence is required.",
        )

    # -----------------------------------------------------
    # FORM FAMILY VALIDATION (CRITICAL)
    # -----------------------------------------------------
    if reference_type in (
        CompletionReferenceType.NOTE,
        CompletionReferenceType.CLINICAL_NOTE,
    ):
        _validate_note_family_matches_task(
            db=db,
            task=task,
            note_id=reference_id,
        )

    # -----------------------------------------------------
    # COMPLETE TASK
    # -----------------------------------------------------
    now = datetime.now(timezone.utc)

    task.status = TaskStatus.COMPLETED
    task.completed_at = now
    task.completion_reference_type = reference_type
    task.completion_reference_id = reference_id

    # -----------------------------------------------------
    # AUDIT FIELDS
    # -----------------------------------------------------
    if hasattr(task, "updated_at"):
        task.updated_at = now

    if hasattr(task, "updated_by"):
        task.updated_by = user_id

    # Optional (future-proof)
    # if hasattr(task, "completed_by"):
    #     task.completed_by = user_id

    # -----------------------------------------------------
    # FINALIZE
    # -----------------------------------------------------
    db.add(task)
    db.flush()

    # -----------------------------------------------------
    # LOGGING (IMPORTANT)
    # -----------------------------------------------------
    try:
        import logging
        logger = logging.getLogger("sns_emr")

        logger.info(
            "Task completed with evidence task_id=%s type=%s ref_type=%s ref_id=%s",
            str(getattr(task, "id", None)),
            str(getattr(task, "task_type", None)),
            str(reference_type),
            str(reference_id),
        )
    except Exception:
        # Logging must never break workflow
        pass

    return task