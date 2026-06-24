# app/services/poc_review_gate.py

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm.attributes import flag_modified

from app.models.clinical_note import ClinicalNote


# =========================================================
# EXCEPTIONS
# =========================================================

class POCReviewGateError(Exception):
    """
    Raised when a clinical note cannot be finalized because one or more
    generated POCs require clinician review.
    """

    def __init__(self, message: str, blocking_pocs: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.message = message
        self.blocking_pocs = blocking_pocs


# =========================================================
# PUBLIC API
# =========================================================

def enforce_poc_review_gate(note: ClinicalNote) -> None:
    """
    Block finalization when plan_of_care_updates contains review-required POCs
    that have not been reviewed.

    Rules:
    - Only blocks POCs where review.required is true.
    - Does not block dismissed/resolved POCs.
    - Requires review.reviewed == true.
    - Intended to run before note.finalize().
    """

    blocking_pocs = get_unreviewed_required_pocs(note)

    if blocking_pocs:
        raise POCReviewGateError(
            message="Clinical note cannot be finalized until all required POC reviews are completed.",
            blocking_pocs=blocking_pocs,
        )


def get_unreviewed_required_pocs(note: ClinicalNote) -> list[dict[str, Any]]:
    """
    Return all required POCs that still need review.
    """

    container = _get_container(note)
    pocs = container.get("pocs")

    if not isinstance(pocs, list):
        return []

    blocking: list[dict[str, Any]] = []

    for poc in pocs:
        if not isinstance(poc, dict):
            continue

        status = str(poc.get("status") or "").upper()
        if status in {"DISMISSED", "RESOLVED"}:
            continue

        review = poc.get("review")
        if not isinstance(review, dict):
            review = {}

        required = bool(review.get("required", False))
        reviewed = bool(review.get("reviewed", False))

        if required and not reviewed:
            problem = poc.get("problem") if isinstance(poc.get("problem"), dict) else {}

            blocking.append(
                {
                    "poc_id": poc.get("poc_id"),
                    "status": poc.get("status"),
                    "problem": {
                        "code": problem.get("code"),
                        "display": problem.get("display"),
                        "category": problem.get("category"),
                    },
                    "reason": "POC requires clinician review before finalization.",
                }
            )

    return blocking


def review_poc(
    *,
    note: ClinicalNote,
    poc_id: str,
    reviewer_user_id: UUID,
    decision: str,
    comment: str | None = None,
) -> dict[str, Any]:
    """
    Apply clinician review decision to one POC.

    Valid decisions:
    - ACCEPT
    - DISMISS
    - MODIFY

    Behavior:
    - ACCEPT marks reviewed true and activates the POC.
    - DISMISS marks reviewed true and dismisses the POC.
    - MODIFY keeps review incomplete and leaves the POC in DRAFT.
    """

    normalized_decision = str(decision or "").strip().upper()

    if normalized_decision not in {"ACCEPT", "DISMISS", "MODIFY"}:
        raise ValueError("decision must be ACCEPT, DISMISS, or MODIFY")

    container = _get_container(note)
    pocs = container.get("pocs")

    if not isinstance(pocs, list):
        raise ValueError("plan_of_care_updates.pocs must be a list")

    target = None

    for poc in pocs:
        if isinstance(poc, dict) and str(poc.get("poc_id")) == str(poc_id):
            target = poc
            break

    if target is None:
        raise ValueError("POC not found")

    review = target.get("review")
    if not isinstance(review, dict):
        review = {
            "required": True,
            "reviewed": False,
            "reviewed_by": None,
            "reviewed_at": None,
        }

    now = _utc_now_iso()

    if normalized_decision == "ACCEPT":
        review["required"] = True
        review["reviewed"] = True
        review["reviewed_by"] = str(reviewer_user_id)
        review["reviewed_at"] = now
        review["decision"] = "ACCEPT"

        if comment:
            review["comment"] = comment

        target["status"] = "ACTIVE"

    elif normalized_decision == "DISMISS":
        review["required"] = True
        review["reviewed"] = True
        review["reviewed_by"] = str(reviewer_user_id)
        review["reviewed_at"] = now
        review["decision"] = "DISMISS"

        if comment:
            review["comment"] = comment

        target["status"] = "DISMISSED"

    elif normalized_decision == "MODIFY":
        review["required"] = True
        review["reviewed"] = False
        review["reviewed_by"] = str(reviewer_user_id)
        review["reviewed_at"] = now
        review["decision"] = "MODIFY"

        if comment:
            review["comment"] = comment

        target["status"] = "DRAFT"
        target["modification_required"] = True

    target["review"] = review
    target["updated_at"] = now
    target["updated_by"] = str(reviewer_user_id)

    flag_modified(note, "plan_of_care_updates")

    return target


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _get_container(note: ClinicalNote) -> dict[str, Any]:
    if not isinstance(note.plan_of_care_updates, dict):
        note.plan_of_care_updates = {
            "meta": {},
            "pocs": [],
        }
        flag_modified(note, "plan_of_care_updates")

    if "pocs" not in note.plan_of_care_updates or not isinstance(note.plan_of_care_updates["pocs"], list):
        note.plan_of_care_updates["pocs"] = []
        flag_modified(note, "plan_of_care_updates")

    return note.plan_of_care_updates


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()