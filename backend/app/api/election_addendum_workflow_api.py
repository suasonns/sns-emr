from __future__ import annotations

"""
Election Addendum Relatedness-Review Workflow API. Thin router over
app.billing.services.election_addendum_service -- all state-machine
enforcement (item-level relatedness gating, physician-review gating,
clock-not-stopped-by-review/generation, furnished_at >= generated_at,
exception/acknowledgment rules) stays in the service layer; this module
only handles auth, tenant/patient/admission validation, request/response
shaping, and HTTP error mapping. Never re-implements workflow rules here.
"""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api._compliance_common import require_election_addendum_workflow_role, resolve_actor
from app.billing.models.election_addendum_request import (
    ElectionAddendumAuditEvent,
    ElectionAddendumDetermination,
    ElectionAddendumRequest,
)
from app.billing.services import election_addendum_service as svc
from app.core.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user

router = APIRouter(tags=["Election Addendum Workflow"], dependencies=[Depends(require_election_addendum_workflow_role())])


# ---------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------


class RelatednessReviewStart(BaseModel):
    reason: str


class RelatednessItemCreate(BaseModel):
    determination_type: str
    description: str
    effective_date: date
    current_provider_or_supplier: str | None = None
    source_record_type: str | None = None
    source_record_id: str | None = None


class RelatednessItemDetermine(BaseModel):
    relationship_status: str
    coverage_status: str
    coverage_owner: str
    clinical_rationale: str | None = None


class PhysicianReviewRequest(BaseModel):
    physician_user_id: str


class PhysicianReviewComplete(BaseModel):
    rationale: str


class RelatednessReviewComplete(BaseModel):
    clinical_rationale: str


class AddendumGenerate(BaseModel):
    document_reference: str
    document_version: int


class AddendumFurnish(BaseModel):
    furnished_at: datetime
    furnished_to: str
    furnishing_method: str
    bfcc_qio_information_furnished: bool = True


class AddendumAcknowledge(BaseModel):
    acknowledgment_status: str
    acknowledgment_document_reference: str | None = None
    signature_exception_reason: str | None = None


class AddendumException(BaseModel):
    exception_type: str
    exception_occurred_at: datetime
    reason: str


class AddendumUpdateForPocChange(BaseModel):
    poc_change_date: date


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _get_addendum_request(db: Session, tenant_id: str, addendum_request_id: str) -> ElectionAddendumRequest:
    row = db.get(ElectionAddendumRequest, addendum_request_id)
    if row is None or str(row.tenant_id) != str(tenant_id):
        # Deliberately identical 404 whether the record doesn't exist or
        # belongs to another tenant -- never disclose cross-tenant existence.
        raise HTTPException(status_code=404, detail="Election addendum requirement not found")
    return row


def _get_item(db: Session, tenant_id: str, addendum_request: ElectionAddendumRequest, item_id: str) -> ElectionAddendumDetermination:
    item = db.get(ElectionAddendumDetermination, item_id)
    if (
        item is None
        or str(item.tenant_id) != str(tenant_id)
        or item.addendum_request_id != addendum_request.id
    ):
        raise HTTPException(status_code=404, detail="Relatedness item not found")
    return item


def _serialize_item(item: ElectionAddendumDetermination) -> dict:
    return {
        "id": str(item.id),
        "addendum_request_id": str(item.addendum_request_id),
        "determination_type": item.determination_type,
        "description": item.description,
        "relationship_status": item.relationship_status,
        "coverage_status": item.coverage_status,
        "coverage_owner": item.coverage_owner,
        "clinical_rationale": item.clinical_rationale,
        "effective_date": item.effective_date.isoformat() if item.effective_date else None,
        "current_provider_or_supplier": item.current_provider_or_supplier,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
        "reviewed_by_user_id": str(item.reviewed_by_user_id) if item.reviewed_by_user_id else None,
    }


def _serialize(req: ElectionAddendumRequest) -> dict:
    return {
        "id": str(req.id),
        "tenant_id": str(req.tenant_id),
        "patient_id": str(req.patient_id),
        "admission_id": str(req.admission_id) if req.admission_id else None,
        "benefit_period_id": str(req.benefit_period_id) if req.benefit_period_id else None,
        "trigger_type": req.trigger_type,
        "workflow_status": req.workflow_status,
        "election_effective_date": req.election_effective_date.isoformat() if req.election_effective_date else None,
        "required_by_at": req.required_by_at.isoformat() if req.required_by_at else None,
        "version_number": req.version_number,
        "supersedes_request_id": str(req.supersedes_request_id) if req.supersedes_request_id else None,
        "relatedness_review_started_at": req.relatedness_review_started_at.isoformat()
        if req.relatedness_review_started_at
        else None,
        "relatedness_review_reason": req.relatedness_review_reason,
        "relatedness_determined_at": req.relatedness_determined_at.isoformat()
        if req.relatedness_determined_at
        else None,
        "clinical_rationale": req.clinical_rationale,
        "physician_review_required": req.physician_review_required,
        "physician_review_requested_at": req.physician_review_requested_at.isoformat()
        if req.physician_review_requested_at
        else None,
        "physician_reviewer_user_id": str(req.physician_reviewer_user_id) if req.physician_reviewer_user_id else None,
        "physician_reviewed_at": req.physician_reviewed_at.isoformat() if req.physician_reviewed_at else None,
        "physician_review_rationale": req.physician_review_rationale,
        "generated_at": req.generated_at.isoformat() if req.generated_at else None,
        "document_reference": req.document_reference,
        "document_version": req.document_version,
        "furnished_at": req.furnished_at.isoformat() if req.furnished_at else None,
        "furnished_to": req.furnished_to,
        "furnishing_method": req.furnishing_method,
        "bfcc_qio_information_furnished": req.bfcc_qio_information_furnished,
        "acknowledgment_status": req.acknowledgment_status,
        "acknowledgment_at": req.acknowledgment_at.isoformat() if req.acknowledgment_at else None,
        "acknowledgment_document_reference": req.acknowledgment_document_reference,
        "signature_exception_reason": req.signature_exception_reason,
        "exception_type": req.exception_type,
        "exception_occurred_at": req.exception_occurred_at.isoformat() if req.exception_occurred_at else None,
    }


# ---------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------


@router.get("/election-addendum-requests/{addendum_request_id}", operation_id="GetElectionAddendumRequest")
def get_addendum_request(
    addendum_request_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    return _serialize(req)


@router.get(
    "/election-addendum-requests/{addendum_request_id}/relatedness-items",
    operation_id="ListElectionAddendumRelatednessItems",
)
def list_relatedness_items(
    addendum_request_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    rows = (
        db.query(ElectionAddendumDetermination)
        .filter(ElectionAddendumDetermination.addendum_request_id == req.id)
        .order_by(ElectionAddendumDetermination.created_at.asc())
        .all()
    )
    return [_serialize_item(r) for r in rows]


@router.get("/election-addendum-requests/{addendum_request_id}/audit", operation_id="GetElectionAddendumRequestAudit")
def get_addendum_request_audit(
    addendum_request_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    rows = (
        db.query(ElectionAddendumAuditEvent)
        .filter(
            ElectionAddendumAuditEvent.tenant_id == current_user.tenant_id,
            ElectionAddendumAuditEvent.addendum_request_id == req.id,
        )
        .order_by(ElectionAddendumAuditEvent.created_at.asc())
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


# ---------------------------------------------------------------------
# Relatedness review
# ---------------------------------------------------------------------


@router.post(
    "/election-addendum-requests/{addendum_request_id}/relatedness-review",
    operation_id="StartElectionAddendumRelatednessReview",
)
def start_relatedness_review(
    addendum_request_id: str,
    payload: RelatednessReviewStart,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.start_relatedness_review(
            db,
            addendum_request=req,
            reason=payload.reason,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(req)
    return _serialize(req)


@router.post(
    "/election-addendum-requests/{addendum_request_id}/relatedness-items",
    operation_id="AddElectionAddendumRelatednessItem",
)
def add_relatedness_item(
    addendum_request_id: str,
    payload: RelatednessItemCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        item = svc.add_relatedness_item(
            db,
            addendum_request=req,
            determination_type=payload.determination_type,
            description=payload.description,
            effective_date=payload.effective_date,
            current_provider_or_supplier=payload.current_provider_or_supplier,
            source_record_type=payload.source_record_type,
            source_record_id=payload.source_record_id,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(item)
    return _serialize_item(item)


@router.post(
    "/election-addendum-requests/{addendum_request_id}/relatedness-items/{item_id}/determination",
    operation_id="RecordElectionAddendumRelatednessItemDetermination",
)
def record_relatedness_item_determination(
    addendum_request_id: str,
    item_id: str,
    payload: RelatednessItemDetermine,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    item = _get_item(db, current_user.tenant_id, req, item_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.record_relatedness_item_determination(
            db,
            addendum_request=req,
            item=item,
            relationship_status=payload.relationship_status,
            coverage_status=payload.coverage_status,
            coverage_owner=payload.coverage_owner,
            clinical_rationale=payload.clinical_rationale,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(item)
    return _serialize_item(item)


@router.post(
    "/election-addendum-requests/{addendum_request_id}/physician-review",
    operation_id="RequestElectionAddendumPhysicianReview",
)
def request_physician_review(
    addendum_request_id: str,
    payload: PhysicianReviewRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.request_physician_review(
            db,
            addendum_request=req,
            physician_user_id=payload.physician_user_id,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(req)
    return _serialize(req)


@router.post(
    "/election-addendum-requests/{addendum_request_id}/physician-review/complete",
    operation_id="CompleteElectionAddendumPhysicianReview",
)
def complete_physician_review(
    addendum_request_id: str,
    payload: PhysicianReviewComplete,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.complete_physician_review(
            db,
            addendum_request=req,
            rationale=payload.rationale,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(req)
    return _serialize(req)


@router.post(
    "/election-addendum-requests/{addendum_request_id}/relatedness-review/complete",
    operation_id="CompleteElectionAddendumRelatednessReview",
)
def complete_relatedness_review(
    addendum_request_id: str,
    payload: RelatednessReviewComplete,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.complete_relatedness_review(
            db,
            addendum_request=req,
            clinical_rationale=payload.clinical_rationale,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(req)
    return _serialize(req)


# ---------------------------------------------------------------------
# Generation / furnishing / acknowledgment / exception / updates
# ---------------------------------------------------------------------


@router.post(
    "/election-addendum-requests/{addendum_request_id}/generate",
    operation_id="GenerateElectionAddendumDocument",
)
def generate_addendum_document(
    addendum_request_id: str,
    payload: AddendumGenerate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.generate_addendum_document(
            db,
            addendum_request=req,
            document_reference=payload.document_reference,
            document_version=payload.document_version,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(req)
    return _serialize(req)


@router.post(
    "/election-addendum-requests/{addendum_request_id}/furnish",
    operation_id="RecordElectionAddendumFurnishing",
)
def record_furnishing(
    addendum_request_id: str,
    payload: AddendumFurnish,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.record_furnishing(
            db,
            addendum_request=req,
            furnished_at=payload.furnished_at,
            furnished_to=payload.furnished_to,
            furnishing_method=payload.furnishing_method,
            bfcc_qio_information_furnished=payload.bfcc_qio_information_furnished,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(req)
    return _serialize(req)


@router.post(
    "/election-addendum-requests/{addendum_request_id}/acknowledgment",
    operation_id="RecordElectionAddendumAcknowledgment",
)
def record_acknowledgment(
    addendum_request_id: str,
    payload: AddendumAcknowledge,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.record_acknowledgment(
            db,
            addendum_request=req,
            acknowledgment_status=payload.acknowledgment_status,
            acknowledgment_document_reference=payload.acknowledgment_document_reference,
            signature_exception_reason=payload.signature_exception_reason,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(req)
    return _serialize(req)


@router.post(
    "/election-addendum-requests/{addendum_request_id}/exception",
    operation_id="RecordElectionAddendumException",
)
def record_exception(
    addendum_request_id: str,
    payload: AddendumException,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.record_exception(
            db,
            addendum_request=req,
            exception_type=payload.exception_type,
            exception_occurred_at=payload.exception_occurred_at,
            reason=payload.reason,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(req)
    return _serialize(req)


@router.post(
    "/election-addendum-requests/{addendum_request_id}/updates",
    operation_id="CreateElectionAddendumUpdateForRelatednessChange",
)
def create_addendum_update_for_relatedness_change(
    addendum_request_id: str,
    payload: AddendumUpdateForPocChange,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    req = _get_addendum_request(db, current_user.tenant_id, addendum_request_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        new_row = svc.create_addendum_update_for_relatedness_change(
            db,
            prior_addendum_request=req,
            poc_change_date=payload.poc_change_date,
            created_by_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ElectionAddendumComplianceError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(new_row)
    return _serialize(new_row)
