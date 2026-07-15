from __future__ import annotations

import logging
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion


logger = logging.getLogger("sns_emr")


# =========================================================
# EXCEPTIONS
# =========================================================

class POCReviewGateError(Exception):
    def __init__(self, message: str, blocking_reason: str) -> None:
        super().__init__(message)
        self.message = message
        self.blocking_reason = blocking_reason


# =========================================================
# REVIEW FUNCTION (✅ NEW)
# =========================================================

def review_poc(
    *,
    note,
    poc_id,
    reviewer_user_id,
    decision: str,
    comment: str | None = None,
) -> dict:
    """
    Review/approve/reject a generated POC entry.

    Behavior:
    - Updates note.plan_of_care_updates
    - Enforces valid decisions
    - Appends review metadata (audit-safe)
    """

    if not hasattr(note, "plan_of_care_updates") or not isinstance(note.plan_of_care_updates, dict):
        raise ValueError("Invalid POC structure on note")

    poc = note.plan_of_care_updates.get(poc_id)

    if not poc:
        raise ValueError("POC not found")

    decision = str(decision).upper()

    if decision not in {"APPROVED", "REJECTED"}:
        raise ValueError("Invalid decision value")

    # ✅ ensure structure
    if not isinstance(poc, dict):
        raise ValueError("Invalid POC format")

    # ✅ append-only review history (audit safe)
    review_entry = {
        "reviewed": True,
        "decision": decision,
        "comment": comment,
        "reviewed_by": str(reviewer_user_id),
    }

    if "review_history" not in poc or not isinstance(poc.get("review_history"), list):
        poc["review_history"] = []

    poc["review_history"].append(review_entry)

    # ✅ update current state
    poc["status"] = decision
    poc["review"] = review_entry

    note.plan_of_care_updates[poc_id] = poc

    logger.info(
        "POC_REVIEWED note_id=%s poc_id=%s decision=%s reviewer=%s",
        str(getattr(note, "id", None)),
        str(poc_id),
        decision,
        str(reviewer_user_id),
    )

    return poc


# =========================================================
# PUBLIC API — REVIEW GATE
# =========================================================

def enforce_poc_review_gate(
    db: Session,
    *,
    patient_id: UUID,
    tenant_id: Optional[UUID] = None,
    actor_user_id: Optional[UUID] = None,
) -> None:
    """
    Blocks clinical actions if no APPROVED Plan of Care exists.
    """

    if not has_approved_plan_of_care(
        db=db,
        patient_id=patient_id,
        tenant_id=tenant_id,
    ):
        logger.warning(
            "POC_REVIEW_BLOCK patient_id=%s tenant_id=%s actor=%s",
            str(patient_id),
            str(tenant_id),
            str(actor_user_id),
        )

        raise POCReviewGateError(
            message="Clinical action blocked: No approved Plan of Care found.",
            blocking_reason="POC must be approved before proceeding."
        )


# =========================================================
# CHECK APPROVED POC
# =========================================================

def has_approved_plan_of_care(
    db: Session,
    *,
    patient_id: UUID,
    tenant_id: Optional[UUID] = None,
) -> bool:
    """
    Checks if patient has an APPROVED POC version.
    """

    query = db.query(PlanOfCare).filter(
        PlanOfCare.patient_id == patient_id
    )

    if tenant_id is not None and hasattr(PlanOfCare, "tenant_id"):
        query = query.filter(PlanOfCare.tenant_id == tenant_id)

    poc = query.order_by(PlanOfCare.created_at.desc()).first()

    if not poc or not getattr(poc, "current_version_id", None):
        return False

    version_query = db.query(PlanOfCareVersion).filter(
        PlanOfCareVersion.id == poc.current_version_id,
        PlanOfCareVersion.approval_status == "APPROVED",
    )

    if tenant_id is not None and hasattr(PlanOfCareVersion, "tenant_id"):
        version_query = version_query.filter(
            PlanOfCareVersion.tenant_id == tenant_id
        )

    version = version_query.first()

    if poc.current_version_id and version is None:
        logger.error(
            "POC_DATA_INCONSISTENT patient_id=%s poc_id=%s version_id=%s",
            str(patient_id),
            str(getattr(poc, "id", None)),
            str(poc.current_version_id),
        )

    return version is not None