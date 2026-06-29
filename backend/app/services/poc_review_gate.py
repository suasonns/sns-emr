from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm.attributes import flag_modified

from app.models.clinical_note import ClinicalNote

POC_REVIEW_VERSION = "3.0.0"
VALID_DECISIONS = {"APPROVE", "REJECT", "NEEDS_REVISION"}


# =========================================================
# EXCEPTIONS
# =========================================================

class POCReviewGateError(Exception):
    def __init__(self, message: str, blocking_pocs: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.message = message
        self.blocking_pocs = blocking_pocs


# =========================================================
# PUBLIC API
# =========================================================

def enforce_poc_review_gate(note: ClinicalNote) -> None:
    blocking_pocs = get_unreviewed_required_pocs(note)
    if blocking_pocs:
        raise POCReviewGateError(
            message="Clinical note cannot be finalized until all required POC reviews are completed.",
            blocking_pocs=blocking_pocs,
        )


def get_unreviewed_required_pocs(note: ClinicalNote) -> list[dict[str, Any]]:
    container = _get_container(note)
    pocs = container["pocs"]

    blocking: list[dict[str, Any]] = []
    for poc in pocs:
        if not isinstance(poc, dict):
            continue

        review = _normalize_review(poc.get("review"))
        required = bool(review.get("required", True))
        reviewed = bool(review.get("reviewed", False))

        if required and not reviewed:
            problem = poc.get("problem") if isinstance(poc.get("problem"), dict) else {}
            blocking.append(
                {
                    "poc_id": poc.get("poc_id"),
                    "status": poc.get("status"),
                    "problem_code": problem.get("code"),
                    "problem_name": problem.get("name"),
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
    normalized_decision = (decision or "").strip().upper()
    if normalized_decision not in VALID_DECISIONS:
        raise ValueError(f"Invalid POC review decision '{decision}'")

    container = _get_container(note)
    pocs = container["pocs"]

    target: dict[str, Any] | None = None
    for poc in pocs:
        if isinstance(poc, dict) and str(poc.get("poc_id")) == str(poc_id):
            target = poc
            break

    if target is None:
        raise ValueError("POC not found")

    review = _normalize_review(target.get("review"))
    review["required"] = True
    review["reviewed"] = True
    review["reviewed_by"] = str(reviewer_user_id)
    review["reviewed_at"] = _utc_now_iso()
    review["decision"] = normalized_decision
    review["comment"] = comment

    target["review"] = review
    target["last_updated_at"] = _utc_now_iso()
    target["status"] = _map_decision_to_status(normalized_decision)

    container["meta"] = _meta()
    flag_modified(note, "plan_of_care_updates")
    return target


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _get_container(note: ClinicalNote) -> dict[str, Any]:
    if not isinstance(note.plan_of_care_updates, dict):
        note.plan_of_care_updates = {
            "meta": _meta(),
            "pocs": [],
        }
        flag_modified(note, "plan_of_care_updates")
        return note.plan_of_care_updates

    if "meta" not in note.plan_of_care_updates or not isinstance(note.plan_of_care_updates["meta"], dict):
        note.plan_of_care_updates["meta"] = _meta()
        flag_modified(note, "plan_of_care_updates")

    if "pocs" not in note.plan_of_care_updates or not isinstance(note.plan_of_care_updates["pocs"], list):
        note.plan_of_care_updates["pocs"] = []
        flag_modified(note, "plan_of_care_updates")

    return note.plan_of_care_updates


def _normalize_review(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {
            "required": True,
            "reviewed": False,
            "reviewed_by": None,
            "reviewed_at": None,
            "decision": None,
            "comment": None,
        }

    payload = {
        "required": bool(value.get("required", True)),
        "reviewed": bool(value.get("reviewed", False)),
        "reviewed_by": value.get("reviewed_by"),
        "reviewed_at": value.get("reviewed_at"),
        "decision": value.get("decision"),
        "comment": value.get("comment"),
    }
    return payload


def _map_decision_to_status(decision: str) -> str:
    mapping = {
        "APPROVE": "REVIEWED",
        "REJECT": "REJECTED",
        "NEEDS_REVISION": "NEEDS_REVISION",
    }
    return mapping.get(decision, "DRAFT")


def _meta() -> dict[str, Any]:
    return {
        "name": "POC_REVIEW_GATE",
        "version": POC_REVIEW_VERSION,
        "generated_at": _utc_now_iso(),
    }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
