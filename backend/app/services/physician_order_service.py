"""
Physician Orders service — implements the compliance-defined order
lifecycle from docs/compliance/orders.md, extended per the Phase 1
lifecycle expansion (owner directive 2026-08-21, additive-only):

    DRAFT -> [PENDING_CLINICAL_REVIEW] -> PENDING_HOSPICE_MD_APPROVAL
          -> APPROVED -> EXECUTED -> COMPLETED
          -> EXPIRED (system/manual, from APPROVED/EXECUTED)
          -> CANCELLED (from any non-terminal status)

Existing stored status literals (DRAFT, PENDING_HOSPICE_MD_APPROVAL,
APPROVED, EXECUTED, CANCELLED) are preserved for backward compatibility.
PENDING_CLINICAL_REVIEW, COMPLETED, and EXPIRED are new literals.
STATUS_LABELS provides a display-label layer so nothing that already reads
the raw status string breaks.

Clinical review is CONDITIONAL, not mandatory for every order (a universal
RN/LVN review gate would delay urgent hospice care). See
`requires_clinical_review()`. STAT/urgent orders may bypass an otherwise-
required review; every bypass is recorded (clinical_review_bypassed,
clinical_review_bypass_reason) and audited via PhysicianOrderStatusEvent.

Only the Medical Director (MD role) may approve. Approval requires
prescriber authentication and, for verbal/phone orders, a confirmed
read-back. Submitting an order for approval creates an
ORDER_MD_APPROVAL task (due 24h after ordered_at, assigned to the MD
role); approving the order auto-completes that task.

IMPLEMENTED (EXECUTED) vs COMPLETED are distinct statuses — see
`complete_order()`. Completion must never be inferred solely from
signature or transmission; it requires completed_by/completed_at/evidence.

Every status transition is recorded via `_record_transition()`, which
writes both a structured PhysicianOrderStatusEvent row (queryable history)
and a generic AuditLog entry (via audit_logger.log_event).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.roles import normalize_role, role_matches
from app.models.physician_order import PhysicianOrder, PhysicianOrderStatusEvent
from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskOrigin,
    TaskDiscipline,
    TaskStatus,
    CompletionReferenceType,
)
from app.services.audit_logger import log_event

VALID_SOURCE_TYPES = {"WRITTEN", "VERBAL_PHONE", "ELECTRONIC", "IDG"}
VALID_PROVIDER_ROLES = {"MD", "NP", "PA"}
VALID_ORDER_CATEGORIES = {"MEDICATION", "DME", "SUPPLY", "LAB", "TREATMENT", "DIET", "OTHER"}
VALID_PRIORITIES = {"ROUTINE", "URGENT", "STAT"}

# Roles that may independently verify/enter a clinically-complete order
# without a separate review checkpoint (a real prescriber authenticating
# their own order, or an RN who has verified a complete verbal order per
# agency policy). Everyone else (office/intake/unclear-source entries)
# triggers PENDING_CLINICAL_REVIEW by default.
SELF_VERIFYING_ROLES = {"MD", "NP", "PA", "RN"}

# =====================================================================
# PROVIDER SIGNATURE AUTHORITY MODEL (owner decision 2026-08-21)
#
# Generalizes the earlier MD-only signer assumption. Signature authority
# is evaluated by document type, provider credential, agency policy,
# workflow type, order type, and urgency — never a flat "is this a
# physician?" check. This is Physician Orders' own signer model; it is
# deliberately NOT a shared/generic engine — CTI (certification_service),
# F2F (f2f_service), and Orders each define independent signer rules per
# their own document type, exactly as directed.
#
# PRIMARY SIGNERS (routed to first, in this precedence order):
#   Attending Physician -> Hospice Physician -> Medical Director ->
#   Medical Director Designee (alias -> Medical Director). "MD" is kept
#   as an accepted primary-signer literal for backward compatibility with
#   the legacy generic provider-discipline role already stored on orders
#   entered before this model existed.
#
# ALTERNATE AUTHORIZED PROVIDER SIGNERS (NP, PA): usable ONLY for
# STAT/URGENT patient-care needs (oxygen, comfort medications, DME,
# hospital bed, supplies, symptom management, immediate treatment
# changes) so patient care is never delayed while attempting to reach a
# specific physician. Never usable for ROUTINE orders, and never usable
# outside the order categories below. Every alternate-signer use must
# record an alternate_signer_reason (see approve_order()).
# =====================================================================
ORDER_PRIMARY_SIGNER_ROLES = [
    "MD", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN", "MEDICAL_DIRECTOR", "MEDICAL_DIRECTOR_DESIGNEE",
]
ORDER_ALTERNATE_SIGNER_ROLES = ["NP", "PA"]
ORDER_ALL_SIGNER_ROLES = ORDER_PRIMARY_SIGNER_ROLES + ORDER_ALTERNATE_SIGNER_ROLES

# STAT/urgent categories an alternate (NP/PA) signer may act on: oxygen
# and comfort medications (MEDICATION), DME/hospital bed (DME), supplies
# (SUPPLY), and symptom management/immediate treatment changes
# (TREATMENT). LAB/DIET/OTHER are excluded — not part of the owner's
# STAT/urgent patient-care list.
ORDER_ALTERNATE_SIGNER_ELIGIBLE_CATEGORIES = {"MEDICATION", "DME", "SUPPLY", "TREATMENT"}


def is_authorized_order_signer(
    role: Optional[str],
    *,
    priority: Optional[str] = None,
    order_category: Optional[str] = None,
) -> bool:
    """True when `role` may sign THIS order under THIS workflow.

    Primary signers (physician-tier) may always sign, any priority/category.
    Alternate signers (NP/PA) may sign ONLY when the order is STAT/URGENT
    AND its category is one of ORDER_ALTERNATE_SIGNER_ELIGIBLE_CATEGORIES —
    never for ROUTINE orders, never outside those categories.
    """
    normalized = normalize_role(role)
    if not normalized:
        return False

    if role_matches(normalized, ORDER_PRIMARY_SIGNER_ROLES, allow_clinical_admin=False):
        return True

    if role_matches(normalized, ORDER_ALTERNATE_SIGNER_ROLES, allow_clinical_admin=False):
        priority_norm = (priority or "").strip().upper()
        category_norm = (order_category or "").strip().upper()
        return (
            priority_norm in ("STAT", "URGENT")
            and category_norm in ORDER_ALTERNATE_SIGNER_ELIGIBLE_CATEGORIES
        )

    return False

# --- Display-label layer (owner directive: no rename of stored literals) ---
STATUS_LABELS = {
    "DRAFT": "Draft",
    "PENDING_CLINICAL_REVIEW": "Pending Clinical Review",
    "PENDING_HOSPICE_MD_APPROVAL": "Pending Physician Signature",
    "APPROVED": "Signed",
    "EXECUTED": "Implemented",
    "COMPLETED": "Completed",
    "EXPIRED": "Expired",
    "CANCELLED": "Cancelled",
}

TERMINAL_STATUSES = {"COMPLETED", "EXPIRED", "CANCELLED"}

# --- Transition-validation graph ---
VALID_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"PENDING_CLINICAL_REVIEW", "PENDING_HOSPICE_MD_APPROVAL", "CANCELLED"},
    "PENDING_CLINICAL_REVIEW": {"PENDING_HOSPICE_MD_APPROVAL", "DRAFT", "CANCELLED"},
    "PENDING_HOSPICE_MD_APPROVAL": {"APPROVED", "EXECUTED", "CANCELLED"},
    "APPROVED": {"EXECUTED", "EXPIRED", "CANCELLED"},
    "EXECUTED": {"APPROVED", "COMPLETED", "EXPIRED", "CANCELLED"},
    "COMPLETED": set(),
    "EXPIRED": set(),
    "CANCELLED": set(),
}


class PhysicianOrderError(Exception):
    """Raised when an order lifecycle transition is not allowed."""


def label_for(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def _assert_transition(order: PhysicianOrder, to_status: str) -> None:
    allowed = VALID_TRANSITIONS.get(order.status, set())
    if to_status not in allowed:
        raise PhysicianOrderError(
            f"Invalid transition: {order.status} -> {to_status} "
            f"(allowed from {order.status}: {sorted(allowed) or 'none — terminal status'})"
        )


def _record_transition(
    db: Session,
    *,
    order: PhysicianOrder,
    from_status: Optional[str],
    to_status: str,
    changed_by,
    changed_by_role: Optional[str] = None,
    reason: Optional[str] = None,
    automatic: bool = False,
    clinical_review_bypassed: bool = False,
    clinical_review_bypass_reason: Optional[str] = None,
    evidence: Optional[str] = None,
    extra_metadata: Optional[dict] = None,
) -> None:
    """Append-only structured audit trail for a status transition. Never
    updated or deleted; written alongside (not instead of) the generic
    AuditLog so lifecycle history is directly queryable."""
    now = datetime.now(timezone.utc)
    event = PhysicianOrderStatusEvent(
        tenant_id=order.tenant_id,
        order_id=order.id,
        from_status=from_status,
        to_status=to_status,
        changed_by_user_id=changed_by,
        changed_by_role=changed_by_role,
        changed_at=now,
        reason=reason,
        automatic=automatic,
        clinical_review_bypassed=clinical_review_bypassed,
        clinical_review_bypass_reason=clinical_review_bypass_reason,
        evidence=evidence,
    )
    db.add(event)

    metadata = {
        "from_status": from_status,
        "to_status": to_status,
        "reason": reason,
        "automatic": automatic,
        "order_source": order.source_type,
        "clinical_review_bypassed": clinical_review_bypassed,
        "clinical_review_bypass_reason": clinical_review_bypass_reason,
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    log_event(
        db=db,
        commit=False,
        user_id=str(changed_by) if changed_by else None,
        tenant_id=str(order.tenant_id),
        role=changed_by_role,
        action="PHYSICIAN_ORDER_STATUS_TRANSITION",
        entity_type="physician_order",
        entity_id=str(order.id),
        metadata=metadata,
    )


def requires_clinical_review(
    *,
    entered_by_role: Optional[str],
    priority: str,
    source_type: str,
    prescriber_authenticated: bool,
) -> bool:
    """Determine whether PENDING_CLINICAL_REVIEW is required for this order.
    Conditional per owner directive — NOT mandatory for every order:

    Bypassed (no review required) when:
    - the order is STAT/URGENT (patient care must not wait on a review queue)
    - a real prescriber (MD/NP/PA) directly entered and authenticated it
    - an RN entered a verbal/phone order and it's marked authenticated
      (agency-policy-verified read-back)

    Required when:
    - a non-clinical role (office staff, intake, unknown) entered the order
    - prescriber_authenticated is False (incomplete authentication)
    """
    if priority in ("STAT", "URGENT"):
        return False

    role = (entered_by_role or "").strip().upper()
    return not (role in SELF_VERIFYING_ROLES and prescriber_authenticated)


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


def get_status_history(db: Session, *, tenant_id, order_id) -> list[PhysicianOrderStatusEvent]:
    return (
        db.query(PhysicianOrderStatusEvent)
        .filter(
            PhysicianOrderStatusEvent.tenant_id == tenant_id,
            PhysicianOrderStatusEvent.order_id == order_id,
        )
        .order_by(PhysicianOrderStatusEvent.changed_at.asc())
        .all()
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
    priority: str = "ROUTINE",
    urgency_reason: Optional[str] = None,
    ordered_by_provider_role_source: Optional[dict] = None,
) -> PhysicianOrder:
    source_type = (source_type or "WRITTEN").strip().upper()
    if source_type not in VALID_SOURCE_TYPES:
        raise PhysicianOrderError(f"source_type must be one of {sorted(VALID_SOURCE_TYPES)}")

    order_category = (order_category or "OTHER").strip().upper()
    if order_category not in VALID_ORDER_CATEGORIES:
        raise PhysicianOrderError(f"order_category must be one of {sorted(VALID_ORDER_CATEGORIES)}")

    # Strict, unchanged backend contract: only canonical MD/NP/PA are ever
    # accepted or stored, regardless of what the UI normalization layer
    # resolved a free-text entry to. `ordered_by_provider_role_source` (if
    # provided) is audit metadata ONLY -- it is never used to derive,
    # relax, or bypass this validation.
    provider_role = (ordered_by_provider_role or "").strip().upper()
    if provider_role not in VALID_PROVIDER_ROLES:
        raise PhysicianOrderError(f"ordered_by_provider_role must be one of {sorted(VALID_PROVIDER_ROLES)}")

    priority = (priority or "ROUTINE").strip().upper()
    if priority not in VALID_PRIORITIES:
        raise PhysicianOrderError(f"priority must be one of {sorted(VALID_PRIORITIES)}")
    if priority in ("STAT", "URGENT") and not urgency_reason:
        raise PhysicianOrderError("urgency_reason is required when priority is STAT or URGENT")

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
        priority=priority,
        urgency_reason=urgency_reason,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    extra_metadata = None
    if isinstance(ordered_by_provider_role_source, dict) and ordered_by_provider_role_source:
        extra_metadata = {
            "ordered_by_provider_role_source": {
                "original_input": ordered_by_provider_role_source.get("original_input"),
                "normalized_value": ordered_by_provider_role_source.get("normalized_value") or provider_role,
                "normalization_method": ordered_by_provider_role_source.get("normalization_method"),
            }
        }

    _record_transition(
        db,
        order=order,
        from_status=None,
        to_status="DRAFT",
        changed_by=created_by,
        reason="Order created",
        extra_metadata=extra_metadata,
    )
    db.commit()
    return order


def submit_for_approval(
    db: Session,
    *,
    order: PhysicianOrder,
    submitted_by,
    submitted_by_role: Optional[str] = None,
    force_clinical_review: Optional[bool] = None,
    bypass_reason: Optional[str] = None,
) -> PhysicianOrder:
    """DRAFT -> PENDING_CLINICAL_REVIEW (Path A) or PENDING_HOSPICE_MD_APPROVAL
    (Path B), depending on `requires_clinical_review()` unless the caller
    explicitly forces the decision (force_clinical_review). A bypass of an
    otherwise-required review (e.g. STAT) must include bypass_reason."""
    if order.status != "DRAFT":
        raise PhysicianOrderError(f"Only DRAFT orders can be submitted (current: {order.status})")

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

    would_require_review = requires_clinical_review(
        entered_by_role=submitted_by_role,
        priority=order.priority,
        source_type=order.source_type,
        prescriber_authenticated=order.prescriber_authenticated,
    )
    needs_review = would_require_review if force_clinical_review is None else force_clinical_review
    bypassed = would_require_review and not needs_review

    if bypassed and not bypass_reason:
        raise PhysicianOrderError("bypass_reason is required to bypass a required clinical review")

    order.clinical_review_required = needs_review
    order.clinical_review_bypassed = bypassed
    order.clinical_review_bypass_reason = bypass_reason if bypassed else None

    from_status = order.status
    if needs_review:
        order.status = "PENDING_CLINICAL_REVIEW"
    else:
        order.status = "PENDING_HOSPICE_MD_APPROVAL"
        _create_md_approval_task(db, order=order, submitted_by=submitted_by)
    db.add(order)
    db.commit()
    db.refresh(order)

    _record_transition(
        db, order=order, from_status=from_status, to_status=order.status,
        changed_by=submitted_by, changed_by_role=submitted_by_role,
        reason=bypass_reason if bypassed else None,
        clinical_review_bypassed=bypassed, clinical_review_bypass_reason=bypass_reason if bypassed else None,
    )
    db.commit()
    return order


def _create_md_approval_task(db: Session, *, order: PhysicianOrder, submitted_by) -> Task:
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
    return task


def complete_clinical_review(
    db: Session,
    *,
    order: PhysicianOrder,
    reviewed_by,
    reviewed_by_role: Optional[str] = None,
    approve: bool,
    reason: Optional[str] = None,
) -> PhysicianOrder:
    """RN/authorized clinical reviewer completes PENDING_CLINICAL_REVIEW:
    approve -> routes to PENDING_HOSPICE_MD_APPROVAL; reject -> returns to
    DRAFT with a required reason (return-for-clarification workflow)."""
    if order.status != "PENDING_CLINICAL_REVIEW":
        raise PhysicianOrderError(f"Only PENDING_CLINICAL_REVIEW orders can be reviewed (current: {order.status})")
    if not approve and not reason:
        raise PhysicianOrderError("reason is required to return an order to DRAFT")

    from_status = order.status
    order.clinical_reviewed_by = reviewed_by
    order.clinical_reviewed_at = datetime.now(timezone.utc)

    if approve:
        order.clinical_review_result = "APPROVED_FOR_SIGNATURE"
        order.status = "PENDING_HOSPICE_MD_APPROVAL"
        db.add(order)
        _create_md_approval_task(db, order=order, submitted_by=reviewed_by)
    else:
        order.clinical_review_result = "RETURNED_TO_DRAFT"
        order.status = "DRAFT"
        db.add(order)

    db.commit()
    db.refresh(order)

    _record_transition(
        db, order=order, from_status=from_status, to_status=order.status,
        changed_by=reviewed_by, changed_by_role=reviewed_by_role, reason=reason,
    )
    db.commit()
    return order


def approve_order(
    db: Session,
    *,
    order: PhysicianOrder,
    approved_by,
    approved_by_role: Optional[str] = None,
    signature_method: str = "ELECTRONIC",
    alternate_signer_reason: Optional[str] = None,
) -> PhysicianOrder:
    """Sign/approve an order. Signature authority is evaluated per THIS
    order (document type = Physician Order, provider credential =
    `approved_by_role`, order type = `order.order_category`, urgency =
    `order.priority`) via `is_authorized_order_signer()` — never a flat
    "is this a physician?" check. Primary signers (Attending Physician,
    Hospice Physician, Medical Director, Medical Director Designee, and
    the legacy "MD" literal) may always sign. Alternate authorized
    provider signers (NP, PA) may sign ONLY STAT/URGENT orders in an
    eligible category (oxygen/comfort meds, DME, supplies, symptom
    management/treatment changes) and MUST supply
    `alternate_signer_reason` documenting why an alternate signer (rather
    than the primary provider) is signing this order."""
    if order.status not in ("PENDING_HOSPICE_MD_APPROVAL", "EXECUTED"):
        raise PhysicianOrderError(
            f"Only orders PENDING_HOSPICE_MD_APPROVAL (or already-executed verbal "
            f"orders awaiting countersignature) can be approved (current: {order.status})"
        )
    if order.status == "EXECUTED" and order.signed_at:
        raise PhysicianOrderError("This order has already been countersigned")

    if not is_authorized_order_signer(
        approved_by_role, priority=order.priority, order_category=order.order_category,
    ):
        raise PhysicianOrderError(
            f"Role '{approved_by_role}' is not authorized to sign this "
            f"{order.priority}/{order.order_category} order. Primary signers "
            f"({', '.join(ORDER_PRIMARY_SIGNER_ROLES)}) may sign any order; "
            f"alternate signers ({', '.join(ORDER_ALTERNATE_SIGNER_ROLES)}) may sign "
            f"only STAT/URGENT orders in {sorted(ORDER_ALTERNATE_SIGNER_ELIGIBLE_CATEGORIES)}."
        )

    is_alternate_signer = role_matches(
        normalize_role(approved_by_role), ORDER_ALTERNATE_SIGNER_ROLES, allow_clinical_admin=False,
    )
    if is_alternate_signer and not alternate_signer_reason:
        raise PhysicianOrderError(
            "alternate_signer_reason is required when an alternate authorized "
            "provider (NP/PA) signs in place of the primary provider."
        )

    now = datetime.now(timezone.utc)
    from_status = order.status
    # If already EXECUTED (nurse acted on a verbal order before MD sign-off),
    # this approval is a countersignature — status stays EXECUTED. Otherwise
    # it's the normal pre-execution approval path.
    if order.status == "PENDING_HOSPICE_MD_APPROVAL":
        order.status = "APPROVED"
    order.signed_by_user_id = approved_by
    order.signed_at = now
    order.signature_method = signature_method
    order.signature_event_id = uuid.uuid4()
    order.signed_by_provider_role = normalize_role(approved_by_role)
    order.alternate_signer_reason = alternate_signer_reason if is_alternate_signer else None
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

    if order.status != from_status:
        _record_transition(
            db, order=order, from_status=from_status, to_status=order.status,
            changed_by=approved_by, changed_by_role=approved_by_role,
            evidence=(
                f"signature_event_id={order.signature_event_id}"
                + (f"; alternate_signer_reason={alternate_signer_reason}" if is_alternate_signer else "")
            ),
        )
    else:
        # Countersignature of an already-EXECUTED order: no status change,
        # but the signature event itself is still audit-worthy.
        _record_transition(
            db, order=order, from_status=from_status, to_status=order.status,
            changed_by=approved_by, changed_by_role=approved_by_role,
            reason="Countersignature of previously-executed verbal order",
            evidence=(
                f"signature_event_id={order.signature_event_id}"
                + (f"; alternate_signer_reason={alternate_signer_reason}" if is_alternate_signer else "")
            ),
        )
    db.commit()
    return order


def execute_order(db: Session, *, order: PhysicianOrder, executed_by=None, executed_by_role: Optional[str] = None) -> PhysicianOrder:
    from_status = order.status
    if order.status == "APPROVED":
        now = datetime.now(timezone.utc)
        order.status = "EXECUTED"
        order.executed_at = now
        order.implemented_by = executed_by
        db.add(order)
        db.commit()
        db.refresh(order)
        _record_transition(db, order=order, from_status=from_status, to_status=order.status, changed_by=executed_by, changed_by_role=executed_by_role)
        db.commit()
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
        order.implemented_by = executed_by
        order.cosignature_due_at = now + timedelta(days=7)
        db.add(order)
        db.commit()
        db.refresh(order)
        _record_transition(db, order=order, from_status=from_status, to_status=order.status, changed_by=executed_by, changed_by_role=executed_by_role)
        db.commit()
        return order

    raise PhysicianOrderError(
        f"Only APPROVED orders (or confirmed VERBAL_PHONE orders pending "
        f"approval) can be executed (current: {order.status}, source_type: {order.source_type})"
    )


def complete_order(
    db: Session,
    *,
    order: PhysicianOrder,
    completed_by,
    completed_by_role: Optional[str] = None,
    completion_evidence: str,
) -> PhysicianOrder:
    """EXECUTED (Implemented) -> COMPLETED. Requires linked completion
    evidence — never inferred solely from signature or transmission. A
    recurring/ongoing order (e.g. a standing medication order) may remain
    EXECUTED indefinitely until discontinued/expired; callers should only
    invoke this for orders with a defined completion point."""
    if order.status != "EXECUTED":
        raise PhysicianOrderError(f"Only EXECUTED (Implemented) orders can be completed (current: {order.status})")
    if not completion_evidence or not completion_evidence.strip():
        raise PhysicianOrderError("completion_evidence is required to mark an order COMPLETED")

    from_status = order.status
    now = datetime.now(timezone.utc)
    order.status = "COMPLETED"
    order.completed_at = now
    order.completed_by = completed_by
    order.completion_evidence = completion_evidence.strip()
    db.add(order)
    db.commit()
    db.refresh(order)

    _record_transition(
        db, order=order, from_status=from_status, to_status=order.status,
        changed_by=completed_by, changed_by_role=completed_by_role,
        evidence=completion_evidence.strip(),
    )
    db.commit()
    return order


def expire_order(db: Session, *, order: PhysicianOrder, expired_by=None, expired_by_role: Optional[str] = None, automatic: bool = True) -> PhysicianOrder:
    """APPROVED/EXECUTED -> EXPIRED, when order.expires_at has passed.
    Preserves the original signed record (signature fields untouched);
    only marks the order no longer active."""
    if order.status not in ("APPROVED", "EXECUTED"):
        raise PhysicianOrderError(f"Only APPROVED or EXECUTED orders can expire (current: {order.status})")
    _assert_transition(order, "EXPIRED")

    from_status = order.status
    now = datetime.now(timezone.utc)
    order.status = "EXPIRED"
    order.expired_at = now
    db.add(order)
    db.commit()
    db.refresh(order)

    _record_transition(
        db, order=order, from_status=from_status, to_status=order.status,
        changed_by=expired_by, changed_by_role=expired_by_role, automatic=automatic,
        reason="expires_at reached" if automatic else None,
    )
    db.commit()
    return order


def expire_due_orders(db: Session, *, tenant_id) -> list[PhysicianOrder]:
    """Batch sweep: expire any APPROVED/EXECUTED order whose expires_at has
    passed. Safe to call repeatedly (idempotent — only acts on non-expired,
    still-active orders)."""
    now = datetime.now(timezone.utc)
    due = (
        db.query(PhysicianOrder)
        .filter(
            PhysicianOrder.tenant_id == tenant_id,
            PhysicianOrder.status.in_(["APPROVED", "EXECUTED"]),
            PhysicianOrder.expires_at.isnot(None),
            PhysicianOrder.expires_at <= now,
        )
        .all()
    )
    return [expire_order(db, order=o, automatic=True) for o in due]


def cancel_order(
    db: Session,
    *,
    order: PhysicianOrder,
    cancelled_by,
    cancelled_by_role: Optional[str] = None,
    reason: Optional[str] = None,
) -> PhysicianOrder:
    if order.status in TERMINAL_STATUSES:
        raise PhysicianOrderError(f"Cannot cancel an order that is already {order.status}")
    if not reason:
        raise PhysicianOrderError("reason is required to cancel an order")
    _assert_transition(order, "CANCELLED")

    from_status = order.status
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

    _record_transition(
        db, order=order, from_status=from_status, to_status=order.status,
        changed_by=cancelled_by, changed_by_role=cancelled_by_role, reason=reason,
    )
    db.commit()
    return order
