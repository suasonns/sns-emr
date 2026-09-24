from __future__ import annotations

"""
Election Compliance-Review API (issue #142/#145 API phase). Thin router
over app.billing.services.election_addendum_service.resolve_compliance_review /
reopen_compliance_review -- resolution and mandatory-addendum-requirement
creation must stay atomic; this router never re-implements that logic.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api._compliance_common import require_compliance_review_role, resolve_actor
from app.billing.services import election_addendum_service as svc
from app.core.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.models.compliance_obligation import ComplianceAuditEvent, ComplianceObligation

router = APIRouter(tags=["Election Compliance Review"], dependencies=[Depends(require_compliance_review_role())])


# ---------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------


class ComplianceReviewResolve(BaseModel):
    benefit_period_id: str
    resolved_election_date: date
    resolution_reason: str


class ComplianceReviewReopen(BaseModel):
    reopen_reason: str


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _get_obligation(db: Session, tenant_id: str, obligation_id: str) -> ComplianceObligation:
    obligation = db.get(ComplianceObligation, obligation_id)
    if obligation is None or str(obligation.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Compliance review not found")
    if obligation.obligation_type != svc.COMPLIANCE_REVIEW_OBLIGATION_TYPE:
        raise HTTPException(status_code=404, detail="Compliance review not found")
    return obligation


def _serialize(obligation: ComplianceObligation) -> dict:
    return {
        "id": str(obligation.id),
        "tenant_id": str(obligation.tenant_id),
        "patient_id": str(obligation.patient_id),
        "admission_id": str(obligation.admission_id) if obligation.admission_id else None,
        "benefit_period_id": str(obligation.benefit_period_id) if obligation.benefit_period_id else None,
        "obligation_type": obligation.obligation_type,
        "status": obligation.status,
        "required_by_at": obligation.required_by_at.isoformat() if obligation.required_by_at else None,
        "completed_at": obligation.completed_at.isoformat() if obligation.completed_at else None,
        "completion_evidence_reference": obligation.completion_evidence_reference,
        "notes": obligation.notes,
    }


# ---------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------


@router.get("/election-compliance-reviews/{obligation_id}", operation_id="GetElectionComplianceReview")
def get_compliance_review(
    obligation_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    obligation = _get_obligation(db, current_user.tenant_id, obligation_id)
    return _serialize(obligation)


@router.get(
    "/admissions/{admission_id}/election-compliance-reviews",
    operation_id="ListAdmissionElectionComplianceReviews",
)
def list_admission_compliance_reviews(
    admission_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    rows = (
        db.query(ComplianceObligation)
        .filter(
            ComplianceObligation.tenant_id == current_user.tenant_id,
            ComplianceObligation.admission_id == admission_id,
            ComplianceObligation.obligation_type == svc.COMPLIANCE_REVIEW_OBLIGATION_TYPE,
        )
        .order_by(ComplianceObligation.created_at.desc())
        .all()
    )
    return [_serialize(r) for r in rows]


# ---------------------------------------------------------------------
# Resolve / reopen
# ---------------------------------------------------------------------


@router.post("/election-compliance-reviews/{obligation_id}/resolve", operation_id="ResolveElectionComplianceReview")
def resolve_compliance_review(
    obligation_id: str,
    payload: ComplianceReviewResolve,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    obligation = _get_obligation(db, current_user.tenant_id, obligation_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        outcome = svc.resolve_compliance_review(
            db,
            tenant_id=current_user.tenant_id,
            compliance_obligation_id=obligation.id,
            benefit_period_id=payload.benefit_period_id,
            resolved_election_date=payload.resolved_election_date,
            resolution_reason=payload.resolution_reason,
            resolved_by_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(obligation)
    result = _serialize(obligation)
    result["mandatory_addendum_outcome"] = outcome.outcome
    result["election_addendum_request_id"] = (
        str(outcome.election_addendum_request.id) if outcome.election_addendum_request else None
    )
    return result


@router.post("/election-compliance-reviews/{obligation_id}/reopen", operation_id="ReopenElectionComplianceReview")
def reopen_compliance_review(
    obligation_id: str,
    payload: ComplianceReviewReopen,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    obligation = _get_obligation(db, current_user.tenant_id, obligation_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.reopen_compliance_review(
            db,
            tenant_id=current_user.tenant_id,
            compliance_obligation_id=obligation.id,
            reopen_reason=payload.reopen_reason,
            reopened_by_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    db.commit()
    db.refresh(obligation)
    return _serialize(obligation)


@router.get("/election-compliance-reviews/{obligation_id}/audit", operation_id="GetElectionComplianceReviewAudit")
def get_compliance_review_audit(
    obligation_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    obligation = _get_obligation(db, current_user.tenant_id, obligation_id)
    rows = (
        db.query(ComplianceAuditEvent)
        .filter(
            ComplianceAuditEvent.tenant_id == current_user.tenant_id,
            ComplianceAuditEvent.compliance_obligation_id == obligation.id,
        )
        .order_by(ComplianceAuditEvent.created_at.asc())
        .all()
    )
    return [
        {
            "id": str(r.id),
            "event_type": r.event_type,
            "actor_user_id": str(r.actor_user_id) if r.actor_user_id else None,
            "actor_account_discipline": r.actor_account_discipline,
            "prior_value": r.prior_value,
            "new_value": r.new_value,
            "reason": r.reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
