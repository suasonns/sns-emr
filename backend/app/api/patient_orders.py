# app/api/patient_orders.py

"""
Generic patient order endpoints: DME / Supply / Lab / Treatment / Diet /
Other. Medications keep their own dedicated router (app/api/medications.py)
since they flow through the drug-safety engine.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.patient_access import get_authorized_patient
from app.models.patient import Patient
from app.models.patient_order import PatientOrder
from app.services.audit_logger import log_event

router = APIRouter(prefix="/patient-orders", tags=["patient-orders"])

CLINICAL_ROLES = ["LVN", "RN", "NP", "MD", "Surveyor"]

ORDER_TYPES = {"DME", "SUPPLY", "LAB", "TREATMENT", "DIET", "OTHER"}
SUB_TYPES = {"NEW", "REFILL", "DC", "PRE_ADMIT"}


class OrderCreate(BaseModel):
    order_type: str
    sub_type: str | None = "NEW"
    order_text: str
    strength: str | None = None
    dosage: str | None = None
    route: str | None = None
    frequency: str | None = None
    indication: str | None = None
    quantity: str | None = None
    payer: str | None = None
    vendor: str | None = None
    administered_by: str | None = None
    special_instruction: str | None = None
    otc_off_market: bool = False
    stat_order: bool = False
    phone_order: bool = False
    start_date: date | None = None
    stop_date: date | None = None


class OrderDiscontinue(BaseModel):
    reason: str | None = None


def _serialize(order: PatientOrder) -> dict:
    return {
        "id": str(order.id),
        "patient_id": str(order.patient_id),
        "order_type": order.order_type,
        "sub_type": order.sub_type,
        "order_text": order.order_text,
        "strength": order.strength,
        "dosage": order.dosage,
        "route": order.route,
        "frequency": order.frequency,
        "indication": order.indication,
        "quantity": order.quantity,
        "payer": order.payer,
        "vendor": order.vendor,
        "administered_by": order.administered_by,
        "special_instruction": order.special_instruction,
        "otc_off_market": order.otc_off_market,
        "stat_order": order.stat_order,
        "phone_order": order.phone_order,
        "start_date": order.start_date.isoformat() if order.start_date else None,
        "stop_date": order.stop_date.isoformat() if order.stop_date else None,
        "status": order.status,
        "discontinued_at": order.discontinued_at.isoformat() if order.discontinued_at else None,
        "discontinue_reason": order.discontinue_reason,
        "source_template_id": str(order.source_template_id) if order.source_template_id else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


@router.get("/patients/{patient_id}", summary="List a patient's non-medication orders, optionally filtered by order_type")
def list_orders(
    patient_id: uuid.UUID,
    order_type: str | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    get_authorized_patient(db, patient_id, user)
    q = db.query(PatientOrder).filter(
        PatientOrder.patient_id == patient_id,
        PatientOrder.tenant_id == user.tenant_id,
    )
    if order_type:
        q = q.filter(PatientOrder.order_type == order_type.strip().upper())
    if status_filter:
        q = q.filter(PatientOrder.status == status_filter.strip().lower())
    orders = q.order_by(PatientOrder.created_at.desc()).all()
    return [_serialize(o) for o in orders]


@router.post(
    "/patients/{patient_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Add a non-medication order (DME/Supply/Lab/Treatment/Diet/Other) to a patient",
)
def add_order(
    patient_id: uuid.UUID,
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    order_type = (payload.order_type or "").strip().upper()
    if order_type not in ORDER_TYPES:
        raise HTTPException(status_code=422, detail=f"order_type must be one of {sorted(ORDER_TYPES)}")

    sub_type = (payload.sub_type or "NEW").strip().upper()
    if sub_type not in SUB_TYPES:
        sub_type = "NEW"

    order = PatientOrder(
        tenant_id=user.tenant_id,
        patient_id=patient_id,
        order_type=order_type,
        sub_type=sub_type,
        order_text=(payload.order_text or "").strip(),
        strength=payload.strength,
        dosage=payload.dosage,
        route=payload.route,
        frequency=payload.frequency,
        indication=payload.indication,
        quantity=payload.quantity,
        payer=payload.payer,
        vendor=payload.vendor,
        administered_by=payload.administered_by,
        special_instruction=payload.special_instruction,
        otc_off_market=payload.otc_off_market,
        stat_order=payload.stat_order,
        phone_order=payload.phone_order,
        start_date=payload.start_date or date.today(),
        stop_date=payload.stop_date,
        created_by=user.user_id,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="ADD_PATIENT_ORDER",
        entity_type="patient_order",
        entity_id=str(order.id),
        metadata={"patient_id": str(patient_id), "order_type": order_type},
    )
    return _serialize(order)


@router.post("/{order_id}/discontinue", summary="Discontinue a non-medication order")
def discontinue_order(
    order_id: uuid.UUID,
    payload: OrderDiscontinue,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    order = (
        db.query(PatientOrder)
        .filter(PatientOrder.id == order_id, PatientOrder.tenant_id == user.tenant_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    get_authorized_patient(db, order.patient_id, user)

    order.status = "discontinued"
    order.discontinued_at = datetime.now(timezone.utc).date()
    order.discontinued_by = user.user_id
    order.discontinue_reason = payload.reason
    db.commit()
    db.refresh(order)

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="DISCONTINUE_PATIENT_ORDER",
        entity_type="patient_order",
        entity_id=str(order.id),
        metadata={"reason": payload.reason},
    )
    return _serialize(order)
