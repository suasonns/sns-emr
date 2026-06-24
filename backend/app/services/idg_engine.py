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
    """
    Result of IDG readiness check.

    blocked = True → IDG cannot proceed
    reasons = list of compliance blockers
    """

    def __init__(self):
        self.blocked: bool = False
        self.reasons: List[str] = []

    def add_reason(self, reason: str) -> None:
        if reason not in self.reasons:
            self.reasons.append(reason)
            self.blocked = True


# =========================================================
# STATUS HELPERS (CANONICAL)
# =========================================================
def _active_task_statuses():
    """
    ACTIVE tasks = tasks that are not completed.

    MUST MATCH Task Engine behavior.
    """
    return [
        TaskStatus.PENDING,
        TaskStatus.IN_PROGRESS,
        TaskStatus.OVERDUE,
    ]


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

    BLOCK CONDITIONS:
    1. Active tasks exist
    2. Red flags unresolved
    3. Needs clarification not resolved
    4. Incident not completed
    """

    result = IDGCheckResult()

    # -----------------------------------------------------
    # 1. CHECK ACTIVE TASKS (CRITICAL CMS REQUIREMENT)
    # -----------------------------------------------------
    active_tasks = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.tenant_id == tenant_id,
            Task.status.in_(_active_task_statuses()),
        )
        .all()
    )

    if active_tasks:
        result.add_reason("All active tasks must be completed before IDG")

    # -----------------------------------------------------
    # 2. LOAD NOTES ONCE
    # -----------------------------------------------------
    notes = (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.patient_id == patient_id,
            ClinicalNote.tenant_id == tenant_id,
        )
        .all()
    )

    # -----------------------------------------------------
    # 3. CHECK RED FLAGS
    # -----------------------------------------------------
    if any(_has_items(note.red_flags) for note in notes):
        result.add_reason("Unresolved red flags in clinical notes")

    # -----------------------------------------------------
    # 4. CHECK NEEDS CLARIFICATION
    # -----------------------------------------------------
    if any(_has_items(note.needs_clarification) for note in notes):
        result.add_reason("Clinical documentation requires clarification")

    # -----------------------------------------------------
    # 5. CHECK INCIDENT COMPLETION
    # -----------------------------------------------------
    if any(_is_incident_pending(note) for note in notes):
        result.add_reason("Incident reports must be completed before IDG")

    return result


# =========================================================
# UTILITIES
# =========================================================
def _has_items(value) -> bool:
    return isinstance(value, list) and len(value) > 0


def _is_incident_pending(note) -> bool:
    status = getattr(note, "incident_status", None)
    if not status:
        return False

    return str(status).upper() == "PENDING"