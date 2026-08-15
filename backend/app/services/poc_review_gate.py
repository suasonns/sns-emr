# FILE: poc_review_gate.py

from __future__ import annotations

import logging
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion

logger = logging.getLogger("sns_emr")


# =========================================================
# EXCEPTION
# =========================================================

class POCReviewGateError(Exception):
    def __init__(self, message: str, blocking_reason: str) -> None:
        super().__init__(message)
        self.message = message
        self.blocking_reason = blocking_reason


# =========================================================
# CORE CHECK — DOES PATIENT HAVE CURRENT POC?
# =========================================================

def has_current_plan_of_care(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    admission_id: Optional[UUID] = None,
) -> bool:

    query = (
        db.query(PlanOfCare)
        .filter(
            PlanOfCare.tenant_id == tenant_id,
            PlanOfCare.patient_id == patient_id,
        )
    )

    if admission_id is not None:
        query = query.filter(PlanOfCare.admission_id == admission_id)

    poc = query.order_by(PlanOfCare.created_at.desc()).first()

    if not poc or not poc.current_version_id:
        return False

    version = (
        db.query(PlanOfCareVersion)
        .filter(
            PlanOfCareVersion.id == poc.current_version_id,
            PlanOfCareVersion.tenant_id == tenant_id,
        )
        .first()
    )

    if not version:
        logger.error(
            "POC_VERSION_NOT_FOUND tenant_id=%s patient_id=%s poc_id=%s",
            str(tenant_id),
            str(patient_id),
            str(getattr(poc, "id", None)),
        )
        return False

    return version.status in {"ACTIVE", "FINALIZED"}


# =========================================================
# PRIMARY GATE (BLOCK CLINICAL ACTION)
# =========================================================

def enforce_poc_gate(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    admission_id: Optional[UUID] = None,
    actor_user_id: Optional[UUID] = None,
) -> None:
    """
    Blocks clinical actions if NO current POC exists.
    """

    if not has_current_plan_of_care(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        admission_id=admission_id,
    ):
        logger.warning(
            "POC_GATE_BLOCK tenant_id=%s patient_id=%s actor=%s",
            str(tenant_id),
            str(patient_id),
            str(actor_user_id),
        )

        raise POCReviewGateError(
            message="Clinical action blocked: No current Plan of Care found.",
            blocking_reason="POC must exist before proceeding.",
        )


# =========================================================
# OPTIONAL STRICT GATE (IDG REVIEW)
# =========================================================

def enforce_poc_idg_gate(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    admission_id: Optional[UUID] = None,
    actor_user_id: Optional[UUID] = None,
) -> None:
    """
    Optional stricter gate:
    - Requires IDG review completed
    """

    query = (
        db.query(PlanOfCare)
        .filter(
            PlanOfCare.tenant_id == tenant_id,
            PlanOfCare.patient_id == patient_id,
        )
    )

    if admission_id is not None:
        query = query.filter(PlanOfCare.admission_id == admission_id)

    poc = query.order_by(PlanOfCare.created_at.desc()).first()

    if not poc or not poc.current_version_id:
        raise POCReviewGateError(
            message="No Plan of Care found.",
            blocking_reason="Cannot perform IDG check without POC.",
        )

    version = (
        db.query(PlanOfCareVersion)
        .filter(
            PlanOfCareVersion.id == poc.current_version_id,
            PlanOfCareVersion.tenant_id == tenant_id,
        )
        .first()
    )

    if not version:
        raise POCReviewGateError(
            message="POC version not found.",
            blocking_reason="Data inconsistency detected.",
        )

    if not version.reviewed_in_idg:
        logger.warning(
            "POC_IDG_BLOCK tenant_id=%s patient_id=%s actor=%s",
            str(tenant_id),
            str(patient_id),
            str(actor_user_id),
        )

        raise POCReviewGateError(
            message="Clinical action blocked: POC not reviewed by IDG.",
            blocking_reason="IDG review required before proceeding.",
        )
        

def enforce_poc_review_gate(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    admission_id: Optional[UUID] = None,
    actor_user_id: Optional[UUID] = None,
) -> None:
    """
    Backward-compatible wrapper.

    Old code may still import enforce_poc_review_gate().
    Internally, it now uses enforce_poc_gate().
    """
    enforce_poc_gate(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        admission_id=admission_id,
        actor_user_id=actor_user_id,
    )