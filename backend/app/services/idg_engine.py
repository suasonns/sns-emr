# app/services/idg_engine.py

from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.clinical_note import ClinicalNote
from app.models.task import Task
from app.models.enums import TaskStatus


# =========================================================
# IDG CHECK RESULT
# =========================================================

class IDGCheckResult:
    def __init__(self):
        self.blocked: bool = False
        self.reasons: List[str] = []


# =========================================================
# MAIN ENTRY POINT
# =========================================================

def enforce_idg_readiness(
    db: Session,
    *,
    patient_id: UUID,
    tenant_id: UUID,
) -> IDGCheckResult:
    """
    Enforce IDG compliance rules before meeting/closure.
    """

    result = IDGCheckResult()

    # -----------------------------------------------------
    # 1. CHECK OPEN TASKS
    # -----------------------------------------------------
    open_tasks = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.tenant_id == tenant_id,
            Task.status.in_([_status_due(), _status_pending()]),
        )
        .all()
    )

    if open_tasks:
        result.blocked = True
        result.reasons.append("Open tasks must be completed before IDG")

    # -----------------------------------------------------
    # 2. CHECK RED FLAGS
    # -----------------------------------------------------
    notes = (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.patient_id == patient_id,
            ClinicalNote.tenant_id == tenant_id,
        )
        .all()
    )

    for note in notes:
        if _has_items(note.red_flags):
            result.blocked = True
            result.reasons.append("Unresolved red flags in clinical notes")
            break

    # -----------------------------------------------------
    # 3. CHECK NEEDS CLARIFICATION
    # -----------------------------------------------------
    for note in notes:
        if _has_items(note.needs_clarification):
            result.blocked = True
            result.reasons.append("Clinical documentation needs clarification")
            break

    # -----------------------------------------------------
    # 4. CHECK INCIDENT COMPLETION
    # -----------------------------------------------------
    for note in notes:
        if _is_incident_pending(note):
            result.blocked = True
            result.reasons.append("Incident reports must be completed")
            break

    return result


# =========================================================
# ENUM HELPERS
# =========================================================

def _status_due():
    for s in TaskStatus:
        if str(s.value).upper() in ("DUE",):
            return s
    return list(TaskStatus)[0]


def _status_pending():
    for s in TaskStatus:
        if str(s.value).upper() in ("PENDING",):
            return s
    return list(TaskStatus)[0]


# =========================================================
# UTILITIES
# =========================================================

def _has_items(value):
    return isinstance(value, list) and len(value) > 0


def _is_incident_pending(note):
    status = getattr(note, "incident_status", None)

    if not status:
        return False

    return str(status).upper() in ("PENDING",)