# FILE: task_completion_service.py

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import TaskStatus, CompletionReferenceType
from app.models.clinical_note import ClinicalNote

from app.domain.forms.form_registry import (
    required_form_family_for_task_discipline,
    note_matches_task_family,
)

from app.services.poc_review_gate import enforce_poc_gate

logger = logging.getLogger("sns_emr")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _validate_note_family_matches_task(
    db: Session,
    task: Task,
    note_id: UUID,
) -> None:
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
    user_id: Optional[UUID],
) -> Task:
    """
    Task completion (PRODUCTION VERSION)

    - Enforces Plan of Care exists ✅
    - Requires evidence ✅
    - Validates note type ✅
    - Sets timestamps ✅
    """

    try:
        now = _utcnow()

        # ✅ STEP 1 — POC GATE (CRITICAL)
        enforce_poc_gate(
            db=db,
            tenant_id=task.tenant_id,
            patient_id=task.patient_id,
            admission_id=getattr(task, "admission_id", None),
            actor_user_id=user_id,
        )

        # ✅ STEP 2 — BASIC VALIDATION
        if task.status == TaskStatus.COMPLETED:
            return task

        if not reference_type or not reference_id:
            raise HTTPException(
                status_code=400,
                detail="Completion evidence is required.",
            )

        # ✅ STEP 3 — NOTE VALIDATION
        if reference_type in (
            CompletionReferenceType.NOTE,
            CompletionReferenceType.CLINICAL_NOTE,
        ):
            _validate_note_family_matches_task(
                db=db,
                task=task,
                note_id=reference_id,
            )

        # ✅ STEP 4 — COMPLETE TASK
        task.status = TaskStatus.COMPLETED
        task.completed_at = now
        task.completion_reference_type = reference_type
        task.completion_reference_id = reference_id

        # ✅ STEP 5 — AUDIT FIELDS
        if hasattr(task, "updated_at"):
            task.updated_at = now
        if hasattr(task, "updated_by"):
            task.updated_by = user_id

        # ✅ STEP 6 — SAVE
        db.add(task)
        db.commit()
        db.refresh(task)

        # ✅ STEP 7 — LOG
        logger.info(
            "TASK_COMPLETED task_id=%s patient_id=%s ref_type=%s ref_id=%s",
            str(task.id),
            str(task.patient_id),
            str(reference_type),
            str(reference_id),
        )

        return task

    except Exception:
        db.rollback()
        logger.exception(
            "TASK_COMPLETION_FAILED task_id=%s",
            str(getattr(task, "id", None)),
        )
        raise