# app/api/physician_orders.py

"""
Physician Orders endpoints — MD-approval-gated order lifecycle per
docs/compliance/orders.md (DRAFT -> PENDING_HOSPICE_MD_APPROVAL ->
APPROVED -> EXECUTED / CANCELLED). Distinct from the Orders Hub's generic
`patient-orders` endpoints (DME/Supply/Lab/Treatment/Diet/Other), which
have no approval workflow.
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

# Any clinical role may draft/submit an order; only MD may approve.
CLINICAL_ROLES = ["LVN", "RN", "NP", "PA", "MD", "Surveyor"]
# "MD" is the legacy/live provider-discipline role. MEDICAL_DIRECTOR and
# ATTENDING_PHYSICIAN are the newer canonical prescriber roles used by the
# dashboard widget-visibility engine (app/core/roles.py). Both vocabularies
# are accepted here so a real prescriber is recognized either way, but
# administrative rank (Administrator/DPCS) must NEVER satisfy this gate —
# see the `allow_clinical_admin=False` on the approval endpoint below.
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


class OrderApprove(BaseModel):
    signature_method: str = "ELECTRONIC"


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
        "signed_at": order.signed_at.isoformat() if order.signed_at else None,
        "signature_method": order.signature_method,
        "signature_event_id": str(order.signature_event_id) if order.signature_event_id else None,
        "executed_at": order.executed_at.isoformat() if order.executed_at else None,
        "cosignature_due_at": order.cosignature_due_at.isoformat() if order.cosignature_due_at else None,
        "awaiting_countersignature": order.status == "EXECUTED" and order.signed_at is None,
        "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None,
        "cancelled_by_name": name_map.get(order.cancelled_by),
        "cancel_reason": order.cancel_reason,
        "created_at": order.created_at.isoformat() if order.created_at else None,
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
        ids.update({o.created_by, o.signed_by_user_id, o.cancelled_by})
    name_map = _user_name_map(db, ids)
    return [_serialize(o, name_map) for o in orders]


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
        )
    except svc.PhysicianOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        user_id=user.user_id, role=user.role, action="CREATE_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id),
        metadata={"patient_id": str(patient_id)},
    )
    return _serialize(order, _user_name_map(db, {order.created_by, order.signed_by_user_id, order.cancelled_by}))


@router.post("/{order_id}/submit", summary="Submit a DRAFT order for MD approval (creates ORDER_MD_APPROVAL task)")
def submit_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    order = _get_order_or_404(db, order_id, user)
    try:
        order = svc.submit_for_approval(db, order=order, submitted_by=user.user_id)
    except svc.PhysicianOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        user_id=user.user_id, role=user.role, action="SUBMIT_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id), metadata={},
    )
    return _serialize(order, _user_name_map(db, {order.created_by, order.signed_by_user_id, order.cancelled_by}))


@router.post("/{order_id}/approve", summary="MD-only: approve and sign a pending physician order")
def approve_order(
    order_id: uuid.UUID,
    payload: OrderApprove,
    db: Session = Depends(get_db),
    # allow_clinical_admin=False: Administrator/DPCS must never gain physician
    # signature authority merely by rank. Only an actual prescriber role may
    # sign — dashboard visibility of this queue is a separate concern.
    user: CurrentUser = Depends(require_roles(MD_ONLY, allow_clinical_admin=False)),
):
    order = _get_order_or_404(db, order_id, user)
    try:
        order = svc.approve_order(
            db, order=order, approved_by=user.user_id, signature_method=payload.signature_method
        )
    except svc.PhysicianOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        user_id=user.user_id, role=user.role, action="APPROVE_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id),
        metadata={"signature_event_id": str(order.signature_event_id)},
    )
    return _serialize(order, _user_name_map(db, {order.created_by, order.signed_by_user_id, order.cancelled_by}))


@router.post("/{order_id}/execute", summary="Mark an APPROVED order as EXECUTED")
def execute_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    order = _get_order_or_404(db, order_id, user)
    try:
        order = svc.execute_order(db, order=order)
    except svc.PhysicianOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        user_id=user.user_id, role=user.role, action="EXECUTE_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id), metadata={},
    )
    return _serialize(order, _user_name_map(db, {order.created_by, order.signed_by_user_id, order.cancelled_by}))


@router.post("/{order_id}/cancel", summary="Cancel an order (any pre-EXECUTED status)")
def cancel_order(
    order_id: uuid.UUID,
    payload: OrderCancel,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    order = _get_order_or_404(db, order_id, user)
    try:
        order = svc.cancel_order(db, order=order, cancelled_by=user.user_id, reason=payload.reason)
    except svc.PhysicianOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log_event(
        user_id=user.user_id, role=user.role, action="CANCEL_PHYSICIAN_ORDER",
        entity_type="physician_order", entity_id=str(order.id), metadata={"reason": payload.reason},
    )
    return _serialize(order, _user_name_map(db, {order.created_by, order.signed_by_user_id, order.cancelled_by}))
