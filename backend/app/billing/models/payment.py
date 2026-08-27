from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, Index, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Payment(Base):
    """
    One claim-level payment line posted from an ERA (835). Matched to the
    real Claim row when the 835's claim control number resolves to one;
    left unmatched (claim_id NULL) otherwise so a biller can manually
    reconcile it instead of the payment silently disappearing.
    """

    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    remittance_advice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("remittance_advices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    claim_id = Column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    claim_control_number = Column(String(64), nullable=True, index=True)

    patient_name = Column(String(255), nullable=True, doc="Raw NM1*QC name from the 835 (fallback display when unmatched)")

    billed_amount = Column(Numeric(12, 2), nullable=True)

    allowed_amount = Column(Numeric(12, 2), nullable=True)

    paid_amount = Column(Numeric(12, 2), nullable=True)

    patient_responsibility = Column(Numeric(12, 2), nullable=True)

    payment_date = Column(String(16), nullable=True, doc="Raw 835 CCYYMMDD date")

    is_denied = Column(Boolean, nullable=False, default=False)

    match_status = Column(
        String(32),
        nullable=False,
        default="UNMATCHED",
        doc="MATCHED / UNMATCHED / MANUAL_REVIEW",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    remittance_advice = relationship("RemittanceAdvice", back_populates="payments")
    claim = relationship("Claim")
    adjustments = relationship(
        "PaymentAdjustment", back_populates="payment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_payment_tenant_match_status", "tenant_id", "match_status"),
        Index("ix_payment_claim_control_number", "claim_control_number"),
    )
