from __future__ import annotations

"""
IDG Follow-Up API (issue #143 API phase). Thin router over
app.services.idg_follow_up_service -- extends the existing idg_reviews
table; never creates a second idg_follow_ups table. Does not interfere
with app.services.idg_review_service (IDGMeeting-driven POC
finalization), which is unrelated.

Assignment identifies responsibility for an action -- it never implies
ownership of the patient or the patient's outcome; multiple disciplines
may each contribute to a follow-up.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api._compliance_common import get_tenant_patient, require_idg_follow_up_role, resolve_actor
from app.core.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.models.idg_review import IDGReview, IDGReviewAuditEvent
from app.services import idg_follow_up_service as svc

router = APIRouter(tags=["IDG Follow-Up"], dependencies=[Depends(require_idg_follow_up_role())])


# ---------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------


class IDGFollowUpCreate(BaseModel):
    patient_id: str
    benefit_period_id: str | None = None
    desired_patient_outcome: str
    follow_up_action: str
    follow_up_due_at: datetime
    source_patient_response_event_id: str | None = None
    clinical_outcome_record_id: str | None = None


class IDGFollowUpAssign(BaseModel):
    assigned_user_id: str
    assigned_at: datetime | None = None
    reassignment_reason: str | None = None


class IDGFollowUpProgress(BaseModel):
    progress_summary: str


class IDGFollowUpPatientResponse(BaseModel):
    clinical_outcome_record_id: str


class IDGFollowUpComplete(BaseModel):
    closure_summary: str
    completed_at: datetime | None = None
    remaining_need: bool = False
    continuing_plan: str | None = None


class IDGFollowUpReopen(BaseModel):
    reopen_reason: str


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _get_review(db: Session, tenant_id: str, idg_review_id: str) -> IDGReview:
    # svc.get_idg_follow_up normalizes tenant_id via str() internally -- no
    # per-router conversion needed here.
    try:
        return svc.get_idg_follow_up(db, tenant_id=tenant_id, idg_review_id=idg_review_id)
    except svc.IDGFollowUpError:
        raise HTTPException(status_code=404, detail="IDG review not found")


def _serialize(review: IDGReview) -> dict:
    return {
        "id": str(review.id),
        "tenant_id": str(review.tenant_id),
        "patient_id": str(review.patient_id),
        "benefit_period_id": str(review.benefit_period_id) if review.benefit_period_id else None,
        "follow_up_required": review.follow_up_required,
        "follow_up_status": review.follow_up_status,
        "follow_up_assigned_to_user_id": str(review.follow_up_assigned_to_user_id)
        if review.follow_up_assigned_to_user_id
        else None,
        "follow_up_assigned_at": review.follow_up_assigned_at.isoformat() if review.follow_up_assigned_at else None,
        "follow_up_completed_at": review.follow_up_completed_at.isoformat()
        if review.follow_up_completed_at
        else None,
        "source_patient_response_event_id": str(review.source_patient_response_event_id)
        if review.source_patient_response_event_id
        else None,
        "source_clinical_outcome_record_id": str(review.source_clinical_outcome_record_id)
        if review.source_clinical_outcome_record_id
        else None,
        "desired_patient_outcome": review.desired_patient_outcome,
        "follow_up_action": review.follow_up_action,
        "follow_up_due_date": review.follow_up_due_date.isoformat() if review.follow_up_due_date else None,
        "closure_summary": review.closure_summary,
        "continuing_plan": review.continuing_plan,
        "reopened_at": review.reopened_at.isoformat() if review.reopened_at else None,
        "reopen_reason": review.reopen_reason,
    }


# ---------------------------------------------------------------------
# Create / retrieve
# ---------------------------------------------------------------------


@router.post("/idg-follow-ups", operation_id="CreateIDGFollowUp")
def create_idg_follow_up(
    payload: IDGFollowUpCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    tenant_id = current_user.tenant_id
    get_tenant_patient(db, tenant_id, payload.patient_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        review = svc.create_idg_follow_up(
            db,
            tenant_id=tenant_id,
            patient_id=payload.patient_id,
            benefit_period_id=payload.benefit_period_id,
            desired_patient_outcome=payload.desired_patient_outcome,
            follow_up_action=payload.follow_up_action,
            follow_up_due_date=payload.follow_up_due_at,
            source_patient_response_event_id=payload.source_patient_response_event_id,
            source_clinical_outcome_record_id=payload.clinical_outcome_record_id,
            created_by_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.IDGFollowUpError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(review)
    return _serialize(review)


@router.get("/idg-reviews/{idg_review_id}/follow-up", operation_id="GetIDGFollowUp")
def get_idg_follow_up(
    idg_review_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    review = _get_review(db, current_user.tenant_id, idg_review_id)
    return _serialize(review)


# ---------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------


@router.post("/idg-reviews/{idg_review_id}/assign", operation_id="AssignIDGFollowUp")
@router.post("/idg-reviews/{idg_review_id}/reassign", operation_id="ReassignIDGFollowUp")
def assign_idg_follow_up(
    idg_review_id: str,
    payload: IDGFollowUpAssign,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    review = _get_review(db, current_user.tenant_id, idg_review_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.assign_follow_up(
            db,
            review=review,
            assigned_to_user_id=payload.assigned_user_id,
            assigned_at=payload.assigned_at or datetime.utcnow(),
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
            reassignment_reason=payload.reassignment_reason,
        )
    except svc.IDGFollowUpError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(review)
    return _serialize(review)


@router.post("/idg-reviews/{idg_review_id}/progress", operation_id="RecordIDGFollowUpProgress")
def record_idg_follow_up_progress(
    idg_review_id: str,
    payload: IDGFollowUpProgress,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    review = _get_review(db, current_user.tenant_id, idg_review_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    svc.record_progress(
        db,
        review=review,
        notes=payload.progress_summary,
        actor_user_id=actor_user_id,
        actor_account_discipline=discipline,
    )
    db.commit()
    db.refresh(review)
    return _serialize(review)


@router.post("/idg-reviews/{idg_review_id}/patient-response", operation_id="LinkIDGFollowUpPatientResponse")
def link_idg_follow_up_patient_response(
    idg_review_id: str,
    payload: IDGFollowUpPatientResponse,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    review = _get_review(db, current_user.tenant_id, idg_review_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    svc.link_patient_response(
        db,
        review=review,
        clinical_outcome_record_id=payload.clinical_outcome_record_id,
        actor_user_id=actor_user_id,
        actor_account_discipline=discipline,
    )
    db.commit()
    db.refresh(review)
    return _serialize(review)


@router.post("/idg-reviews/{idg_review_id}/complete", operation_id="CompleteIDGFollowUp")
def complete_idg_follow_up(
    idg_review_id: str,
    payload: IDGFollowUpComplete,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    review = _get_review(db, current_user.tenant_id, idg_review_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.complete_follow_up(
            db,
            review=review,
            closure_summary=payload.closure_summary,
            completed_at=payload.completed_at or datetime.utcnow(),
            remaining_need=payload.remaining_need,
            continuing_plan=payload.continuing_plan,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.IDGFollowUpError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    db.commit()
    db.refresh(review)
    return _serialize(review)


@router.post("/idg-reviews/{idg_review_id}/reopen", operation_id="ReopenIDGFollowUp")
def reopen_idg_follow_up(
    idg_review_id: str,
    payload: IDGFollowUpReopen,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    review = _get_review(db, current_user.tenant_id, idg_review_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.reopen_follow_up(
            db,
            review=review,
            reopen_reason=payload.reopen_reason,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.IDGFollowUpError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    db.commit()
    db.refresh(review)
    return _serialize(review)


@router.get("/idg-reviews/{idg_review_id}/audit", operation_id="GetIDGFollowUpAudit")
def get_idg_follow_up_audit(
    idg_review_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    review = _get_review(db, current_user.tenant_id, idg_review_id)
    rows = (
        db.query(IDGReviewAuditEvent)
        .filter(
            IDGReviewAuditEvent.tenant_id == current_user.tenant_id,
            IDGReviewAuditEvent.idg_review_id == review.id,
        )
        .order_by(IDGReviewAuditEvent.created_at.asc())
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
