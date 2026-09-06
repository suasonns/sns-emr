from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

FACILITY_ALLOCATION_STATUSES = {
    "PROPOSED",
    "MANUAL_REVIEW_REQUIRED",
    "CONFIRMED",
    "REVERSED",
}


class FacilityPaymentAllocation(Base):
    __tablename__ = "facility_payment_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    facility_payment_expectation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("facility_payment_expectations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    remittance_advice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("remittance_advices.id", ondelete="SET NULL"),
        nullable=True,
    )
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True)
    payment_adjustment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("payment_adjustments.id", ondelete="SET NULL"),
        nullable=True,
    )
    payer_name = Column(String(255), nullable=True)
    amount_applied = Column(Numeric(12, 2), nullable=False)
    payment_date = Column(String(16), nullable=True)
    allocation_status = Column(
        String(32),
        nullable=False,
        default="PROPOSED",
        server_default=text("'PROPOSED'"),
        index=True,
    )
    flagged_for_review = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    flagged_reason = Column(Text, nullable=True)
    match_basis = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    reconciled_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reconciled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    expectation = relationship("FacilityPaymentExpectation", back_populates="allocations")
    payment = relationship("Payment")
    remittance_advice = relationship("RemittanceAdvice")
    claim = relationship("Claim")
    payment_adjustment = relationship("PaymentAdjustment")

    __table_args__ = (
        Index(
            "ix_facility_payment_allocation_tenant_expectation",
            "tenant_id",
            "facility_payment_expectation_id",
        ),
        Index("ix_facility_payment_allocation_payment_id", "payment_id"),
    )
