from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PhysicianOrder(BaseModel):
    """
    MD-signed physician order, distinct from the generic `PatientOrder`
    (DME/Supply/Lab/Treatment/Diet/Other) table used by the Orders Hub.

    Implements the compliance-defined order lifecycle from
    docs/compliance/orders.md, extended per the Phase 1 lifecycle expansion
    (owner directive 2026-08-21 — additive only, existing literals preserved):

        DRAFT -> [PENDING_CLINICAL_REVIEW] -> PENDING_HOSPICE_MD_APPROVAL
              -> APPROVED -> EXECUTED -> COMPLETED
              -> EXPIRED (from APPROVED/EXECUTED, when expires_at passes)
              -> CANCELLED (from any pre-EXECUTED status)

    Display labels (see physician_order_service.STATUS_LABELS) differ from
    the stored literals for readability without a breaking rename:
        DRAFT -> "Draft"
        PENDING_CLINICAL_REVIEW -> "Pending Clinical Review"
        PENDING_HOSPICE_MD_APPROVAL -> "Pending Physician Signature"
        APPROVED -> "Signed"
        EXECUTED -> "Implemented"
        COMPLETED -> "Completed"
        EXPIRED -> "Expired"
        CANCELLED -> "Cancelled"

    PENDING_CLINICAL_REVIEW is CONDITIONAL, not mandatory for every order —
    see physician_order_service.requires_clinical_review(). STAT/urgent
    orders may bypass it (clinical_review_bypassed=True, with
    clinical_review_bypass_reason recorded and audited via
    PhysicianOrderStatusEvent).

    Only the Medical Director (MD role) may approve. Approval requires
    prescriber_authenticated=True and, for verbal/phone orders,
    phone_readback_confirmed=True. On approval a signature is captured
    (signed_by_user_id, signed_at, signature_method, signature_event_id)
    and the linked ORDER_MD_APPROVAL task (see Task.reference_type /
    Task.reference_id) is auto-completed.

    IMPLEMENTED (EXECUTED) vs COMPLETED are distinct: EXECUTED means
    fulfillment/implementation began (e.g. transmitted to pharmacy, DME
    delivery initiated); COMPLETED means all required implementation,
    follow-up, and completion evidence is documented (completed_by,
    completed_at, completion_evidence) — never inferred solely from
    signature or transmission.
    """

    __tablename__ = "physician_orders"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # DRAFT | PENDING_HOSPICE_MD_APPROVAL | APPROVED | EXECUTED | CANCELLED
    status = Column(String(32), nullable=False, server_default="DRAFT", index=True)

    order_text = Column(Text, nullable=False)

    # DME | SUPPLY | LAB | TREATMENT | DIET | OTHER | MEDICATION
    order_category = Column(String(32), nullable=False, server_default="OTHER", index=True)

    # WRITTEN | VERBAL_PHONE | ELECTRONIC | IDG
    source_type = Column(String(32), nullable=False, server_default="WRITTEN")

    ordered_by_provider_name = Column(String(255), nullable=False)
    # MD | NP | PA
    ordered_by_provider_role = Column(String(16), nullable=False)
    ordered_at = Column(DateTime(timezone=True), nullable=False)

    prescriber_authenticated = Column(Boolean, nullable=False, server_default="false")
    # Required True when source_type == VERBAL_PHONE
    phone_readback_confirmed = Column(Boolean, nullable=True)

    # --- MD approval / signature ---
    signed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    signature_method = Column(String(32), nullable=True)
    signature_event_id = Column(UUID(as_uuid=True), nullable=True)

    # --- Provider Signature Authority Model (2026-08-21) ---
    # The actual provider role/credential that signed THIS order — captured
    # at signature time so the signer's tier (primary vs. alternate) is
    # directly queryable on the record, not just inside the status-event
    # audit trail. e.g. "MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "NP", "PA".
    signed_by_provider_role = Column(String(64), nullable=True)
    # Required documentation when an alternate authorized provider (NP/PA)
    # signs a STAT/URGENT order in place of the primary provider — captures
    # why the alternate signer acted rather than the primary provider
    # (e.g. "Attending Physician unreachable, patient in acute distress").
    alternate_signer_reason = Column(Text, nullable=True)

    executed_at = Column(DateTime(timezone=True), nullable=True)

    # For VERBAL_PHONE orders executed by the nurse before MD countersignature
    # (standard hospice practice — the read-back at time of the call is the
    # safety check, not full MD sign-off, so a suffering patient isn't left
    # waiting on comfort meds). Set when executed while still
    # PENDING_HOSPICE_MD_APPROVAL; this is a soft compliance reminder only —
    # it does NOT block anything. MDs often don't countersign for days (in
    # surgery, etc.) — realistically it's often not signed until the next
    # IDG meeting, which can be up to a week out. Nothing about execution or
    # ongoing care is ever blocked by this deadline passing.
    cosignature_due_at = Column(DateTime(timezone=True), nullable=True)

    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    cancel_reason = Column(Text, nullable=True)

    # --- Phase 1 lifecycle expansion (additive, 2026-08-21) ---

    # ROUTINE | STAT | URGENT — STAT/URGENT orders may bypass clinical review
    # so patient care (O2, comfort meds, DME, symptom management) is never
    # delayed waiting in a clinical-review queue.
    priority = Column(String(16), nullable=False, server_default="ROUTINE")
    urgency_reason = Column(Text, nullable=True)

    # Conditional clinical review (NOT mandatory for every order — see
    # physician_order_service.requires_clinical_review()). Null until
    # determined at submit time.
    clinical_review_required = Column(Boolean, nullable=True)
    clinical_reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    clinical_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    # APPROVED_FOR_SIGNATURE | RETURNED_TO_DRAFT
    clinical_review_result = Column(String(32), nullable=True)
    clinical_review_bypassed = Column(Boolean, nullable=False, server_default="false")
    clinical_review_bypass_reason = Column(Text, nullable=True)

    # Implementation (EXECUTED) vs completion (COMPLETED) are distinct.
    implemented_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    completion_evidence = Column(Text, nullable=True)

    # Expiration tracking — set explicitly per order-type/agency policy, never
    # inferred. An expired order must never continue to appear active.
    expires_at = Column(DateTime(timezone=True), nullable=True)
    expiration_type = Column(String(32), nullable=True)
    expired_at = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", back_populates="physician_orders")


class PhysicianOrderStatusEvent(BaseModel):
    """
    Append-only, structured audit trail of every physician_order status
    transition. Distinct from the generic AuditLog so lifecycle history is
    directly queryable (e.g. "show the review/signature history for order
    X") without parsing free-form JSON metadata. Never updated or deleted.
    """

    __tablename__ = "physician_order_status_events"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("physician_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=False)

    changed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    changed_by_role = Column(String(64), nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False)

    reason = Column(Text, nullable=True)
    automatic = Column(Boolean, nullable=False, server_default="false")
    clinical_review_bypassed = Column(Boolean, nullable=False, server_default="false")
    clinical_review_bypass_reason = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
