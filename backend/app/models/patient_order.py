from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PatientOrder(BaseModel):
    """
    Generic (non-medication) hospice order: DME, Supplies, Lab, Treatment,
    Diet, or "Other" boilerplate admission orders.

    Medications remain in their own dedicated `Medication` model (which
    powers the drug-safety engine); this table covers every other order
    type shown in the Hospice Orders Hub so the whole "Tx / Meds / DME"
    workflow lives on one consistent, queryable, faxable record shape.
    """

    __tablename__ = "patient_orders"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # DME | SUPPLY | LAB | TREATMENT | DIET | OTHER  (MEDICATION handled by Medication model)
    order_type = Column(String(32), nullable=False, index=True)

    # NEW | REFILL | DC | PRE_ADMIT
    sub_type = Column(String(32), nullable=False, server_default="NEW")

    order_text = Column(Text, nullable=False)

    # Optional clinical detail fields (blank for most DME/Supply/Other rows)
    strength = Column(String(128), nullable=True)
    dosage = Column(String(128), nullable=True)
    route = Column(String(64), nullable=True)
    frequency = Column(String(128), nullable=True)
    indication = Column(String(255), nullable=True)
    quantity = Column(String(64), nullable=True)

    # Ordering/fulfillment metadata
    payer = Column(String(64), nullable=True)
    vendor = Column(String(128), nullable=True)
    administered_by = Column(String(64), nullable=True)
    special_instruction = Column(Text, nullable=True)

    otc_off_market = Column(Boolean, nullable=False, server_default="false")
    stat_order = Column(Boolean, nullable=False, server_default="false")
    phone_order = Column(Boolean, nullable=False, server_default="false")

    start_date = Column(Date, nullable=True)
    stop_date = Column(Date, nullable=True)

    # active | discontinued
    status = Column(String(32), nullable=False, server_default="active")
    discontinued_at = Column(Date, nullable=True)
    discontinued_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    discontinue_reason = Column(Text, nullable=True)

    # Traceability back to the order-set template this row was imported from (nullable)
    source_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("order_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # MANUAL | RULE_SUGGESTED. Mirrors PlanOfCare's source_kind: a
    # RULE_SUGGESTED order was created from an explicit clinician "Add to
    # Orders" action on a system-generated suggestion (see
    # app.services.order_suggestion_service); it is never auto-applied.
    source_kind = Column(String(32), nullable=False, server_default="MANUAL")

    # Traceability back to the RN ICA assessment whose findings produced the
    # suggestion this order was created from (nullable; only set for
    # RULE_SUGGESTED orders).
    source_rnica_assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rnica_assessments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    patient = relationship("Patient", back_populates="patient_orders")

    __table_args__ = (
        Index("ix_patient_orders_patient_type", "patient_id", "order_type"),
        Index("ix_patient_orders_patient_status", "patient_id", "status"),
    )
