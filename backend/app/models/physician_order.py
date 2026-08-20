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
    docs/compliance/orders.md:

        DRAFT -> PENDING_HOSPICE_MD_APPROVAL -> APPROVED -> EXECUTED
                                              -> CANCELLED (from any
                                                 pre-EXECUTED status)

    Only the Medical Director (MD role) may approve. Approval requires
    prescriber_authenticated=True and, for verbal/phone orders,
    phone_readback_confirmed=True. On approval a signature is captured
    (signed_by_user_id, signed_at, signature_method, signature_event_id)
    and the linked ORDER_MD_APPROVAL task (see Task.reference_type /
    Task.reference_id) is auto-completed.
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

    patient = relationship("Patient", back_populates="physician_orders")
