# app/api/physician_orders.py

"""
Physician Orders endpoints — MD-approval-gated order lifecycle per
docs/compliance/orders.md, extended per the Phase 1 lifecycle expansion
(owner directive 2026-08-21, additive-only):

    DRAFT -> [PENDING_CLINICAL_REVIEW] -> PENDING_HOSPICE_MD_APPROVAL
          -> APPROVED -> EXECUTED -> COMPLETED
          -> EXPIRED (from APPROVED/EXECUTED)
          -> CANCELLED (from any non-terminal status)

Clinical review is conditional, not mandatory for every order — see
physician_order_service.requires_clinical_review(). Distinct from the
Orders Hub's generic `patient-orders` endpoints (DME/Supply/Lab/Treatment/
Diet/Other), which have no approval workflow.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.patient_access import get_authorized_patient
from app.models.patient import Patient
from app.models.physician_order import PhysicianOrder
from app.models.user import User
from app.services import physician_order_service as svc
from app.services.audit_logger import log_event

router = APIRouter(prefix="/physician-orders", tags=["physician-orders"])

# Any clinical role may draft/submit an order; only an authorized provider
# signer may approve.
CLINICAL_ROLES = ["LVN", "RN", "NP", "PA", "MD", "Surveyor"]
# "MD" is the legacy/live provider-discipline role. MEDICAL_DIRECTOR and
# ATTENDING_PHYSICIAN are the newer canonical prescriber roles used by the
# dashboard widget-visibility engine (app/core/roles.py). Both vocabularies
# are accepted here so a real prescriber is recognized either way, but
# administrative rank (Administrator/DPCS) must NEVER satisfy this gate —
# see the `allow_clinical_admin=False` on the approval endpoint below.
#
# Kept for backward compatibility (e.g. regression tests asserting
# administrative rank never satisfies a signature gate). The live
# `/approve` endpoint below now gates on
# `svc.ORDER_ALL_SIGNER_ROLES` (Provider Signature Authority Model,
# app/services/physician_order_service.py) — primary providers (this
# list) plus alternate authorized provider signers (NP/PA) — with the
# NP/PA STAT/URGENT-category eligibility check enforced inside
# `svc.approve_order()` itself, since that's a per-order (not per-role)
# authorization decision.
MD_ONLY = ["MD", "MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN"]


class OrderCreate(BaseModel):
    order_text: str
    order_category: str = "OTHER"
    source_type: str = "WRITTEN"
    ordered_by_provider_name: str
    ordered_by_provider_role: str
    ordered_at: datetime | None = None
    prescriber_authenticated: bool = False
    phone_readback_confirmed: bool | None = None
    priority: str = "ROUTINE"
    urgency_reason: str | None = None


class OrderSubmit(BaseModel):
    # Explicit override; omit to let requires_clinical_review() decide.
    force_clinical_review: bool | None = None
    bypass_reason: str | None = None


class OrderClinicalReview(BaseModel):
    approve: bool
    reason: str | None = None


class OrderApprove(BaseModel):
    signature_method: str = "ELECTRONIC"
    # Required when the signer is an alternate authorized provider (NP/PA)
    # signing a STAT/URGENT order in place of the primary provider — see
    # svc.approve_order() / Provider Signature Authority Model.
    alternate_signer_reason: str | None = None


class OrderComplete(BaseModel):
    completion_evidence: str


class OrderCancel(BaseModel):
    reason: str | None = None


def _user_name_map(db: Session, user_ids: set) -> dict:
    """Batch-resolve user ids -> display name, for audit-trail attribution
    (who entered/imported the order vs. who signed/cancelled it) — one query
    for a whole order list instead of N+1."""
    ids = {uid for uid in user_ids if uid}
    if not ids:
        return {}
    rows = db.query(User.id, User.full_name, User.display_name, User.role).filter(User.id.in_(ids)).all()
    return {row[0]: (row[2] or row[1] or "Unknown") for row in rows}


def _serialize(order: PhysicianOrder, name_map: dict | None = None) -> dict:
    name_map = name_map or {}
    return {
        "id": str(order.id),
        "patient_id": str(order.patient_id),
        "status": order.status,
        "status_label": svc.label_for(order.status),
        "priority": order.priority,
        "urgency_reason": order.urgency_reason,
        "order_text": order.order_text,
        "order_category": order.order_category,
        "source_type": order.source_type,
        "ordered_by_provider_name": order.ordered_by_provider_name,
        "ordered_by_provider_role": order.ordered_by_provider_role,
        "ordered_at": order.ordered_at.isoformat() if order.ordered_at else None,
        "prescriber_authenticated": order.prescriber_authenticated,
        "phone_readback_confirmed": order.phone_readback_confirmed,
        # Who (staff member) entered/imported this order into the chart —
        # distinct from ordered_by_provider_name, which is who GAVE the
        # order (the physician/NP/PA). Needed so the agency can audit
        # "who put in what" separately from "who ordered it".
        "entered_by_user_id": str(order.created_by) if order.created_by else None,
        "entered_by_name": name_map.get(order.created_by),
        "signed_by_user_id": str(order.signed_by_user_id) if order.signed_by_user_id else None,
        "signed_by_name": name_map.get(order.signed_by_user_id),
        "signed_by_provider_role": order.signed_by_provider_role,
        "alternate_signer_reason": order.alternate_signer_reason,
        "signed_at": order.signed_at.isoformat() if order.signed_at else None,
        "signature_method": order.signature_method,
        "signature_event_id": str(order.signature_event_id) if order.signature_event_id else None,
        "executed_at": order.executed_at.isoformat() if order.executed_at else None,
        "cosignature_due_at": order.cosignature_due_at.isoformat() if order.cosignature_due_at else None,
        "awaiting_countersignature": order.status == "EXECUTED" and order.signed_at is None,
        # --- Phase 1 lifecycle expansion fields ---
        "clinical_review_required": order.clinical_review_required,
        "clinical_reviewed_by_name": name_map.get(order.clinical_reviewed_by),
        "clinical_reviewed_at": order.clinical_reviewed_at.isoformat() if order.clinical_reviewed_at else None,
        "clinical_review_result": order.clinical_review_result,
        "clinical_review_bypassed": order.clinical_review_bypassed,
        "clinical_review_bypass_reason": order.clinical_review_bypass_reason,
        "implemented_by_name": name_map.get(order.implemented_by),
        "completed_at": order.completed_at.isoformat() if order.completed_at else None,
        "completed_by_name": name_map.get(order.completed_by),
        "completion_evidence": order.completion_evidence,
        "expires_at": order.expires_at.isoformat() if order.expires_at else None,
        "expiration_type": order.expiration_type,
        "expired_at": order.expired_at.isoformat() if order.expired_at else None,
        "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None,
        "cancelled_by_name": name_map.get(order.cancelled_by),
        "cancel_reason": order.cancel_reason,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


def _name_ids(order: PhysicianOrder) -> set:
    return {
        order.created_by, order.signed_by_user_id, order.cancelled_by,
        order.clinical_reviewed_by, order.implemented_by, order.completed_by,
    }


def _get_patient_or_404(db: Session, patient_id: uuid.UUID, user: CurrentUser) -> Patient:
    return get_authorized_patient(db, patient_id, user)


def _get_order_or_404(db: Session, order_id: uuid.UUID, user: CurrentUser) -> PhysicianOrder:
    order = svc.get_order(db, tenant_id=user.tenant_id, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Physician order not found")
    get_authorized_patient(db, order.patient_id, user)
    return order


@router.get("/patients/{patient_id}", summary="List a patient's physician orders")
def list_orders(
    patient_id: uuid.UUID,
    status_filter: str | None = None,
    category_filter: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    _get_patient_or_404(db, patient_id, user)
    orders = svc.list_orders(
        db, tenant_id=user.tenant_id, patient_id=patient_id,
        status_filter=status_filter, category_filter=category_filter,
    )
    ids = set()
    for o in orders:
        ids.update(_name_ids(o))
    name_map = _user_name_map(db, ids)
    return [_serialize(o, name_map) for o in orders]


@router.get("/{order_id}/status-history", summary="Immutable status-transition audit trail for an order")
def order_status_history(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    order = _get_order_or_404(db, order_id, user)
    events = svc.get_status_history(db, tenant_id=user.tenant_id, order_id=order.id)
    ids = {e.changed_by_user_id for e in events if e.changed_by_user_id}
    name_map = _user_name_map(db, ids)
    return [
        {
            "id": str(e.id),
            "from_status": e.from_status,
            "from_status_label": svc.label_for(e.from_status) if e.from_status else None,
            "to_status": e.to_status,
            "to_status_label": svc.label_for(e.to_status),
            "changed_by_user_id": str(e.changed_by_user_id) if e.changed_by_user_id else None,
            "changed_by_name": name_map.get(e.changed_by_user_id),
            "changed_by_role": e.changed_by_role,
            "changed_at": e.changed_at.isoformat() if e.changed_at else None,
            "reason": e.reason,
            "automatic": e.automatic,
            "clinical_review_bypassed": e.clinical_review_bypassed,
            "clinical_review_bypass_reason": e.clinical_review_bypass_reason,
            "evidence": e.evidence,
        }
        for e in events
    ]


@router.post("/patients/{patient_id}", summary="Create a DRAFT physician order")
def create_order(
    patient_id: uuid.UUID,
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    _get_patient_or_404(db, patient_id, user)
    try:
        order = svc.create_draft(
            db,
            tenant_id=user.tenant_id,
            patient_id=patient_id,
            order_text=payload.order_text,
            order_category=payload.order_category,
            source_type=payload.source_type,
            ordered_by_provider_name=payload.ordered_by_provider_name,
            ordered_by_provider_role=payload.ordered_by_provider_role,
            ordered_at=payload.ordered_at,
            prescriber_authenticated=payload.prescriber_authenticated,
            phone_readback_confirmed=payload.phone_readback_confirmed,
            created_by=user.user_id,
            priority=payload.priority,
            urgency_reason=payload.urgency_reason,
        )
    except svc.PhysicianOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        db=db, tenant_id=str(user.tenant_id),
        user_id=user.user_id, role=user.role, action="CREATE_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id),
        metadata={"patient_id": str(patient_id), "priority": order.priority},
    )
    db.commit()
    return _serialize(order, _user_name_map(db, _name_ids(order)))


@router.post(
    "/{order_id}/submit",
    summary="Submit a DRAFT order — routes to Pending Clinical Review or Pending Physician Signature",
)
def submit_order(
    order_id: uuid.UUID,
    payload: OrderSubmit,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    order = _get_order_or_404(db, order_id, user)
    try:
        order = svc.submit_for_approval(
            db, order=order, submitted_by=user.user_id, submitted_by_role=user.role,
            force_clinical_review=payload.force_clinical_review, bypass_reason=payload.bypass_reason,
        )
    except svc.PhysicianOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        db=db, tenant_id=str(user.tenant_id),
        user_id=user.user_id, role=user.role, action="SUBMIT_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id),
        metadata={"routed_to": order.status},
    )
    db.commit()
    return _serialize(order, _user_name_map(db, _name_ids(order)))


@router.post(
    "/{order_id}/clinical-review",
    summary="Authorized clinical reviewer completes Pending Clinical Review (approve -> Pending Physician "
    "Signature, or return to Draft with reason)",
)
def clinical_review_order(
    order_id: uuid.UUID,
    payload: OrderClinicalReview,
    db: Session = Depends(get_db),
    # Any clinical role may review per agency policy scope — LVN scope
    # limitations are enforced at the agency-policy layer, not hard-coded
    # here (owner directive: "do not assume an LVN may independently
    # validate every order type").
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    order = _get_order_or_404(db, order_id, user)
    try:
        order = svc.complete_clinical_review(
            db, order=order, reviewed_by=user.user_id, reviewed_by_role=user.role,
            approve=payload.approve, reason=payload.reason,
        )
    except svc.PhysicianOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        db=db, tenant_id=str(user.tenant_id),
        user_id=user.user_id, role=user.role, action="CLINICAL_REVIEW_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id),
        metadata={"approve": payload.approve, "reason": payload.reason, "result": order.clinical_review_result},
    )
    db.commit()
    return _serialize(order, _user_name_map(db, _name_ids(order)))


@router.post("/{order_id}/approve", summary="Authorized provider signer: approve and sign a pending physician order")
def approve_order(
    order_id: uuid.UUID,
    payload: OrderApprove,
    db: Session = Depends(get_db),
    # allow_clinical_admin=False: Administrator/DPCS must never gain
    # provider signature authority merely by rank. Only an actual
    # authorized provider signer role may sign — dashboard visibility of
    # this queue is a separate concern. Primary providers (Attending
    # Physician/Hospice Physician/Medical Director/Medical Director
    # Designee/legacy "MD") may always sign; alternate authorized
    # provider signers (NP/PA) pass this endpoint-level role gate but are
    # further restricted to STAT/URGENT eligible-category orders inside
    # svc.approve_order() (a per-order, not per-role, decision).
    user: CurrentUser = Depends(require_roles(svc.ORDER_ALL_SIGNER_ROLES, allow_clinical_admin=False)),
):
    order = _get_order_or_404(db, order_id, user)
    try:
        order = svc.approve_order(
            db, order=order, approved_by=user.user_id, approved_by_role=user.role,
            signature_method=payload.signature_method,
            alternate_signer_reason=payload.alternate_signer_reason,
        )
    except svc.PhysicianOrderError as exc:
        log_event(
            db=db, tenant_id=str(user.tenant_id),
            user_id=user.user_id, role=user.role, action="PROVIDER_SIGNATURE_ACCESS_DENIED",
            entity_type="physician_order", entity_id=str(order.id),
            metadata={"reason": str(exc)},
        )
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        db=db, tenant_id=str(user.tenant_id),
        user_id=user.user_id, role=user.role, action="APPROVE_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id),
        metadata={"signature_event_id": str(order.signature_event_id)},
    )
    # Physician Identity Mapping audit trail: this signature was only
    # reachable because _get_order_or_404() -> get_authorized_patient()
    # already confirmed an ACTIVE verified physician_id linkage for this
    # signer-tier role — record that explicitly for survey evidence.
    log_event(
        db=db, tenant_id=str(user.tenant_id),
        user_id=user.user_id, role=user.role, action="PROVIDER_SIGNATURE_ACCESS_GRANTED",
        entity_type="physician_order", entity_id=str(order.id),
        metadata={"signed_by_provider_role": order.signed_by_provider_role},
    )
    db.commit()
    return _serialize(order, _user_name_map(db, _name_ids(order)))


@router.post("/{order_id}/execute", summary="Mark a Signed order as Implemented (EXECUTED)")
def execute_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    order = _get_order_or_404(db, order_id, user)
    try:
        order = svc.execute_order(db, order=order, executed_by=user.user_id, executed_by_role=user.role)
    except svc.PhysicianOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        db=db, tenant_id=str(user.tenant_id),
        user_id=user.user_id, role=user.role, action="EXECUTE_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id), metadata={},
    )
    db.commit()
    return _serialize(order, _user_name_map(db, _name_ids(order)))


@router.post("/{order_id}/complete", summary="Mark an Implemented order as Completed (requires completion evidence)")
def complete_order(
    order_id: uuid.UUID,
    payload: OrderComplete,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    order = _get_order_or_404(db, order_id, user)
    try:
        order = svc.complete_order(
            db, order=order, completed_by=user.user_id, completed_by_role=user.role,
            completion_evidence=payload.completion_evidence,
        )
    except svc.PhysicianOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        db=db, tenant_id=str(user.tenant_id),
        user_id=user.user_id, role=user.role, action="COMPLETE_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id),
        metadata={"completion_evidence": payload.completion_evidence},
    )
    db.commit()
    return _serialize(order, _user_name_map(db, _name_ids(order)))


@router.post("/{order_id}/cancel", summary="Cancel an order (any non-terminal status, reason required)")
def cancel_order(
    order_id: uuid.UUID,
    payload: OrderCancel,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    order = _get_order_or_404(db, order_id, user)
    try:
        order = svc.cancel_order(
            db, order=order, cancelled_by=user.user_id, cancelled_by_role=user.role, reason=payload.reason,
        )
    except svc.PhysicianOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        db=db, tenant_id=str(user.tenant_id),
        user_id=user.user_id, role=user.role, action="CANCEL_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id), metadata={"reason": payload.reason},
    )
    db.commit()
    return _serialize(order, _user_name_map(db, _name_ids(order)))
