# app/services/poc_warning_autosuggest.py

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import TaskStatus, CompletionReferenceType


logger = logging.getLogger("sns_emr")


# =========================================================
# HELPERS
# =========================================================

def _utcnow():
    return datetime.now(timezone.utc)


def _task_type_noncompliant():
    """
    Safe resolver for POC_NONCOMPLIANT_STRUCTURE task type.
    """
    value = getattr(Task, "task_type", None)

    # Try enum first
    return "POC_NONCOMPLIANT_STRUCTURE"


def _completed_status():
    member = getattr(TaskStatus, "COMPLETED", None)
    return member if member is not None else "COMPLETED"


def _reference_type_note():
    member = getattr(CompletionReferenceType, "NOTE", None)
    return member if member is not None else "NOTE"


# =========================================================
# MAIN FUNCTION
# =========================================================

def suggest_close_poc_noncompliant_structure_tasks(
    *,
    db: Session,
    patient_id,
    corrected_note_id,
    tenant_id: Optional[UUID] = None,
    actor_user_id: Optional[UUID] = None,
) -> int:
    """
    Auto-suggest closure by attaching a corrected POC note as evidence
    to existing open POC_NONCOMPLIANT_STRUCTURE tasks.

    Behavior:
    - DOES NOT mark tasks completed
    - ONLY attaches evidence when missing
    - idempotent-safe
    - audit-friendly
    """

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------
    if db is None:
        logger.error("POC autosuggest called with db=None")
        return 0

    if not patient_id:
        logger.warning("POC autosuggest missing patient_id")
        return 0

    if not corrected_note_id:
        logger.warning(
            "POC autosuggest missing corrected_note_id patient_id=%s",
            str(patient_id),
        )
        return 0

    now = _utcnow()
    updated = 0

    # -----------------------------------------------------
    # QUERY
    # -----------------------------------------------------
    query = (
        db.query(Task)
        .filter(Task.patient_id == patient_id)
        .filter(Task.task_type == _task_type_noncompliant())
        .filter(Task.status != _completed_status())
    )

    if tenant_id is not None and hasattr(Task, "tenant_id"):
        query = query.filter(Task.tenant_id == tenant_id)

    tasks = query.all()

    # -----------------------------------------------------
    # UPDATE LOOP
    # -----------------------------------------------------
    for task in tasks:
        # idempotency guard
        if getattr(task, "completion_reference_id", None) == str(corrected_note_id):
            continue

        # only attach if empty
        if (
            getattr(task, "completion_reference_type", None) is None
            and not getattr(task, "completion_reference_id", None)
        ):
            if hasattr(task, "completion_reference_type"):
                task.completion_reference_type = _reference_type_note()

            if hasattr(task, "completion_reference_id"):
                task.completion_reference_id = str(corrected_note_id)

            # ✅ audit fields
            if hasattr(task, "updated_at"):
                task.updated_at = now

            if hasattr(task, "updated_by"):
                task.updated_by = actor_user_id

            # ✅ optional metadata
            if hasattr(task, "details") and isinstance(task.details, dict):
                task.details["autosuggest"] = {
                    "type": "POC_NONCOMPLIANT_STRUCTURE",
                    "linked_note_id": str(corrected_note_id),
                    "linked_at": now.isoformat(),
                }

            updated += 1

    # -----------------------------------------------------
    # LOGGING
    # -----------------------------------------------------
    logger.info(
        "POC autosuggest linked %s tasks patient_id=%s note_id=%s",
        updated,
        str(patient_id),
        str(corrected_note_id),
    )

    return updated