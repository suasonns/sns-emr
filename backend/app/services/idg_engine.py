# services/idg_engine.py

from __future__ import annotations

from typing import List
from uuid import UUID
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.clinical_note import ClinicalNote
from app.models.task import Task
from app.models.enums import TaskStatus
from app.models.idg_review import IDGReview


# =========================================================
# CONFIGURATION
# =========================================================

IDG_LOOKBACK_DAYS = 15

INCIDENT_BLOCKING_STATUSES = {"PENDING", "IN_PROGRESS", "ESCALATED"}


# =========================================================
# IDG CHECK RESULT
# =========================================================
class IDGCheckResult:
    def __init__(self):
        self.blocked: bool = False
        self.reasons: List[str] = []

    def add_reason(self, reason: str) -> None:
        if reason not in self.reasons:
            self.reasons.append(reason)
            self.blocked = True


# =========================================================
# STATUS HELPERS
# =========================================================
def _active_task_statuses():
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
    result = IDGCheckResult()

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=IDG_LOOKBACK_DAYS)

    # -----------------------------------------------------
    # ✅ 0. IDG REVIEW MUST EXIST AND BE VALID
    # -----------------------------------------------------
    last_review = (
        db.query(IDGReview)
        .filter(
            IDGReview.patient_id == patient_id,
            IDGReview.tenant_id == tenant_id,
        )
        .order_by(IDGReview.review_date.desc())
        .first()
    )

    if not last_review:
        result.add_reason("No IDG review exists for patient")
        return result

    if not last_review.is_finalized:
        result.add_reason("Latest IDG review is not finalized")

    if not last_review.plan_of_care_version_id:
        result.add_reason("IDG review is not linked to Plan of Care")

    if last_review.review_date < cutoff:
        result.add_reason("IDG review is outdated")

    # -----------------------------------------------------
    # ✅ 1. ACTIVE TASKS
    # -----------------------------------------------------
    active_tasks = (
        db.query(Task.id)
        .filter(
            Task.patient_id == patient_id,
            Task.tenant_id == tenant_id,
            Task.status.in_(_active_task_statuses()),
        )
        .limit(1)
        .all()
    )

    if active_tasks:
        result.add_reason("All active tasks must be completed before IDG")

    # -----------------------------------------------------
    # ✅ 2. LOAD RELEVANT NOTES ONLY
    # -----------------------------------------------------
    notes = (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.patient_id == patient_id,
            ClinicalNote.tenant_id == tenant_id,
            ClinicalNote.created_at >= cutoff,
        )
        .all()
    )

    # -----------------------------------------------------
    # ✅ 3. RED FLAGS
    # -----------------------------------------------------
    if any(_has_items(note.red_flags) for note in notes):
        result.add_reason("Unresolved red flags in clinical notes")

    # -----------------------------------------------------
    # ✅ 4. NEEDS CLARIFICATION
    # -----------------------------------------------------
    if any(_has_items(note.needs_clarification) for note in notes):
        result.add_reason("Clinical documentation requires clarification")

    # -----------------------------------------------------
    # ✅ 5. INCIDENT BLOCKS
    # -----------------------------------------------------
    if any(_is_incident_blocking(note) for note in notes):
        result.add_reason("Incident reports must be completed before IDG")

    return result


# =========================================================
# UTILITIES
# =========================================================
def _has_items(value) -> bool:
    if not value:
        return False

    if isinstance(value, list):
        return len(value) > 0

    return False


def _is_incident_blocking(note) -> bool:
    status = getattr(note, "incident_status", None)
    if not status:
        return False

    return str(status).upper() in INCIDENT_BLOCKING_STATUSES