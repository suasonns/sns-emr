# app/services/clinical_note_service.py

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.clinical_note import ClinicalNote
from app.services.clinical_note_validation_engine import (
    validate_and_trigger_incident,
)
from app.services.task_engine import process_tasks_for_note


# =========================================================
# SAVE (DRAFT)
# =========================================================

def save_clinical_note(
    db: Session,
    *,
    note: ClinicalNote,
    user_id: UUID,
):
    """
    Save clinical note as draft and run:
    1) Validation Engine
    2) Incident Engine
    3) Task Engine

    ENTERPRISE RULES:
    - Non-blocking validation
    - Idempotent processing
    - Single transaction boundary
    """

    # -----------------------------
    # Persist draft
    # -----------------------------
    db.add(note)
    db.flush()  # ✅ DO NOT COMMIT YET

    # -----------------------------
    # VALIDATION + INCIDENT ENGINE
    # -----------------------------
    validation_result = validate_and_trigger_incident(
        db=db,
        note=note,
        actor_user_id=user_id,
        actor_role="CLINICIAN",
    )

    # -----------------------------
    # TASK ENGINE
    # -----------------------------
    process_tasks_for_note(
        db=db,
        note=note,
        user_id=user_id,
    )

    # -----------------------------
    # FINALIZE TRANSACTION
    # -----------------------------
    db.commit()
    db.refresh(note)

    return note, validation_result


# =========================================================
# FINALIZE (SIGN)
# =========================================================

def finalize_clinical_note(
    db: Session,
    *,
    note: ClinicalNote,
    user_id: UUID,
):
    """
    Finalize (sign) clinical note.

    ENTERPRISE FLOW:
    1) Validation Engine (final pass)
    2) Incident Engine (ensure created)
    3) Task Engine
    4) Finalize note
    5) Commit

    IMPORTANT:
    - Still NON-BLOCKING (compliance alerts not blockers)
    """

    # -----------------------------
    # VALIDATION + INCIDENT ENGINE
    # -----------------------------
    validation_result = validate_and_trigger_incident(
        db=db,
        note=note,
        actor_user_id=user_id,
        actor_role="CLINICIAN",
    )

    # -----------------------------
    # TASK ENGINE
    # -----------------------------
    process_tasks_for_note(
        db=db,
        note=note,
        user_id=user_id,
    )

    # -----------------------------
    # FINALIZE NOTE (SIGN)
    # -----------------------------
    note.finalize(user_id=user_id)

    db.add(note)

    # -----------------------------
    # FINAL COMMIT
    # -----------------------------
    db.commit()
    db.refresh(note)

    return note, validation_result