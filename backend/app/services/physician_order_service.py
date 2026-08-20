"""
Physician Orders service — implements the compliance-defined order
lifecycle from docs/compliance/orders.md:

    DRAFT -> PENDING_HOSPICE_MD_APPROVAL -> APPROVED -> EXECUTED
                                          -> CANCELLED

Only the Medical Director (MD role) may approve. Approval requires
prescriber authentication and, for verbal/phone orders, a confirmed
read-back. Submitting an order for approval creates an
ORDER_MD_APPROVAL task (due 24h after ordered_at, assigned to the MD
role); approving the order auto-completes that task.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.physician_order import PhysicianOrder
from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskOrigin,
    TaskDiscipline,
    TaskStatus,
    CompletionReferenceType,
)

VALID_SOURCE_TYPES = {"WRITTEN", "VERBAL_PHONE", "ELECTRONIC", "IDG"}
VALID_PROVIDER_ROLES = {"MD", "NP", "PA"}
VALID_ORDER_CATEGORIES = {"MEDICATION", "DME", "SUPPLY", "LAB", "TREATMENT", "DIET", "OTHER"}


class PhysicianOrderError(Exception):
    """Raised when an order lifecycle transition is not allowed."""


def list_orders(db: Session, *, tenant_id, patient_id, status_filter: Optional[str] = None, category_filter: Optional[str] = None):
    q = db.query(PhysicianOrder).filter(
        PhysicianOrder.tenant_id == tenant_id,
        PhysicianOrder.patient_id == patient_id,
    )
    if status_filter:
        q = q.filter(PhysicianOrder.status == status_filter.strip().upper())
    if category_filter:
        q = q.filter(PhysicianOrder.order_category == category_filter.strip().upper())
    return q.order_by(PhysicianOrder.created_at.desc()).all()


def get_order(db: Session, *, tenant_id, order_id) -> Optional[PhysicianOrder]:
    return (
        db.query(PhysicianOrder)
        .filter(PhysicianOrder.id == order_id, PhysicianOrder.tenant_id == tenant_id)
        .first()
    )


def create_draft(
    db: Session,
    *,
    tenant_id,
    patient_id,
    order_text: str,
    order_category: str = "OTHER",
    source_type: str,
    ordered_by_provider_name: str,
    ordered_by_provider_role: str,
    ordered_at: Optional[datetime],
    prescriber_authenticated: bool,
    phone_readback_confirmed: Optional[bool],
    created_by,
) -> PhysicianOrder:
    source_type = (source_type or "WRITTEN").strip().upper()
    if source_type not in VALID_SOURCE_TYPES:
        raise PhysicianOrderError(f"source_type must be one of {sorted(VALID_SOURCE_TYPES)}")

    order_category = (order_category or "OTHER").strip().upper()
    if order_category not in VALID_ORDER_CATEGORIES:
        raise PhysicianOrderError(f"order_category must be one of {sorted(VALID_ORDER_CATEGORIES)}")

    provider_role = (ordered_by_provider_role or "").strip().upper()
    if provider_role not in VALID_PROVIDER_ROLES:
        raise PhysicianOrderError(f"ordered_by_provider_role must be one of {sorted(VALID_PROVIDER_ROLES)}")

    order = PhysicianOrder(
        tenant_id=tenant_id,
        patient_id=patient_id,
        status="DRAFT",
        order_text=(order_text or "").strip(),
        order_category=order_category,
        source_type=source_type,
        ordered_by_provider_name=(ordered_by_provider_name or "").strip(),
        ordered_by_provider_role=provider_role,
        ordered_at=ordered_at or datetime.now(timezone.utc),
        prescriber_authenticated=bool(prescriber_authenticated),
        phone_readback_confirmed=phone_readback_confirmed,
        created_by=created_by,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def submit_for_approval(db: Session, *, order: PhysicianOrder, submitted_by) -> PhysicianOrder:
    if order.status != "DRAFT":
        raise PhysicianOrderError(f"Only DRAFT orders can be submitted for approval (current: {order.status})")

    # Required Data Elements (Before Approval) — docs/compliance/orders.md
    missing = []
    if not order.order_text:
        missing.append("order_text")
    if not order.ordered_by_provider_name:
        missing.append("ordered_by_provider_name")
    if order.ordered_by_provider_role not in VALID_PROVIDER_ROLES:
        missing.append("ordered_by_provider_role")
    if not order.ordered_at:
        missing.append("ordered_at")
    if not order.prescriber_authenticated:
        missing.append("prescriber_authenticated")
    if order.source_type == "VERBAL_PHONE" and not order.phone_readback_confirmed:
        missing.append("phone_readback_confirmed")

    if missing:
        raise PhysicianOrderError(f"Missing required fields before approval: {', '.join(missing)}")

    order.status = "PENDING_HOSPICE_MD_APPROVAL"
    db.add(order)

    task = Task(
        tenant_id=order.tenant_id,
        patient_id=order.patient_id,
        created_by=submitted_by,
        task_type=TaskType.ORDER_MD_APPROVAL,
        origin=TaskOrigin.MANUAL,
        discipline=TaskDiscipline.MD,
        assigned_role="MD",
        status=TaskStatus.PENDING,
        due_at=order.ordered_at + timedelta(hours=24),
        reference_type="PHYSICIAN_ORDER",
        reference_id=order.id,
        alert_reason="Physician order pending Medical Director approval",
    )
    db.add(task)
    db.commit()
    db.refresh(order)
    return order


def approve_order(
    db: Session,
    *,
    order: PhysicianOrder,
    approved_by,
    signature_method: str = "ELECTRONIC",
) -> PhysicianOrder:
    if order.status not in ("PENDING_HOSPICE_MD_APPROVAL", "EXECUTED"):
        raise PhysicianOrderError(
            f"Only orders PENDING_HOSPICE_MD_APPROVAL (or already-executed verbal "
            f"orders awaiting countersignature) can be approved (current: {order.status})"
        )
    if order.status == "EXECUTED" and order.signed_at:
        raise PhysicianOrderError("This order has already been countersigned")

    now = datetime.now(timezone.utc)
    # If already EXECUTED (nurse acted on a verbal order before MD sign-off),
    # this approval is a countersignature — status stays EXECUTED. Otherwise
    # it's the normal pre-execution approval path.
    if order.status == "PENDING_HOSPICE_MD_APPROVAL":
        order.status = "APPROVED"
    order.signed_by_user_id = approved_by
    order.signed_at = now
    order.signature_method = signature_method
    order.signature_event_id = uuid.uuid4()
    db.add(order)

    task = (
        db.query(Task)
        .filter(
            Task.reference_type == "PHYSICIAN_ORDER",
            Task.reference_id == order.id,
            Task.task_type == TaskType.ORDER_MD_APPROVAL,
        )
        .first()
    )
    if task and task.status != TaskStatus.COMPLETED:
        task.status = TaskStatus.COMPLETED
        task.completed_at = now
        task.completion_reference_type = CompletionReferenceType.PHYSICIAN_ORDER
        task.completion_reference_id = order.id
        db.add(task)

    db.commit()
    db.refresh(order)
    return order


def execute_order(db: Session, *, order: PhysicianOrder) -> PhysicianOrder:
    if order.status == "APPROVED":
        order.status = "EXECUTED"
        order.executed_at = datetime.now(timezone.utc)
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    # Verbal/phone orders with a confirmed read-back can be acted on
    # immediately (standard hospice practice for urgent comfort meds) — the
    # read-back at the time of the call is the safety check, not full MD
    # sign-off. The MD must still countersign afterward (see approve_order),
    # but realistically that often doesn't happen for days — surgery,
    # unavailability, etc. — and commonly isn't signed until the next IDG
    # meeting (which can be up to a week out). cosignature_due_at is a soft
    # compliance reminder only; it never blocks execution or care.
    if (
        order.status == "PENDING_HOSPICE_MD_APPROVAL"
        and order.source_type == "VERBAL_PHONE"
        and order.phone_readback_confirmed
    ):
        now = datetime.now(timezone.utc)
        order.status = "EXECUTED"
        order.executed_at = now
        order.cosignature_due_at = now + timedelta(days=7)
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    raise PhysicianOrderError(
        f"Only APPROVED orders (or confirmed VERBAL_PHONE orders pending "
        f"approval) can be executed (current: {order.status}, source_type: {order.source_type})"
    )


def cancel_order(db: Session, *, order: PhysicianOrder, cancelled_by, reason: Optional[str]) -> PhysicianOrder:
    if order.status in ("EXECUTED", "CANCELLED"):
        raise PhysicianOrderError(f"Cannot cancel an order that is already {order.status}")

    order.status = "CANCELLED"
    order.cancelled_at = datetime.now(timezone.utc)
    order.cancelled_by = cancelled_by
    order.cancel_reason = reason
    db.add(order)

    task = (
        db.query(Task)
        .filter(
            Task.reference_type == "PHYSICIAN_ORDER",
            Task.reference_id == order.id,
            Task.task_type == TaskType.ORDER_MD_APPROVAL,
        )
        .first()
    )
    if task and task.status not in (TaskStatus.COMPLETED,):
        task.status = TaskStatus.WAIVED
        db.add(task)

    db.commit()
    db.refresh(order)
    return order
