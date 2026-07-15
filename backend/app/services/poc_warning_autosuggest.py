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

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _task_type_noncompliant():
    """
    Safe resolver for POC_NONCOMPLIANT_STRUCTURE task type.
    """
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
    Auto-suggest closure by attaching a corrected POC note as evidence.

    Behavior:
    - DOES NOT mark tasks completed
    - Attaches or corrects evidence linkage
    - idempotent-safe
    - audit-safe (append-only metadata)
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

        existing_ref_id = getattr(task, "completion_reference_id", None)

        # ✅ IDENTITY GUARD (TRUE IDEMPOTENT)
        if existing_ref_id == str(corrected_note_id):
            continue

        # ✅ ATTACH OR CORRECT LINKAGE
        if hasattr(task, "completion_reference_type"):
            task.completion_reference_type = _reference_type_note()

        if hasattr(task, "completion_reference_id"):
            task.completion_reference_id = str(corrected_note_id)

        # -------------------------------------------------
        # AUDIT FIELDS
        # -------------------------------------------------
        if hasattr(task, "updated_at"):
            task.updated_at = now

        if hasattr(task, "updated_by"):
            task.updated_by = actor_user_id

        # -------------------------------------------------
        # APPEND-ONLY METADATA (CRITICAL FIX)
        # -------------------------------------------------
        if hasattr(task, "details"):

            existing_details = getattr(task, "details", None)

            if not isinstance(existing_details, dict):
                task.details = {}

            if "autosuggest_history" not in task.details:
                task.details["autosuggest_history"] = []

            task.details["autosuggest_history"].append({
                "type": "POC_NONCOMPLIANT_STRUCTURE",
                "linked_note_id": str(corrected_note_id),
                "linked_at": now.isoformat(),
                "actor_user_id": str(actor_user_id),
            })

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