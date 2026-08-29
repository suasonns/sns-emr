from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Index, DateTime, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class RemittanceAdvice(Base):
    """
    One inbound ERA (X12 835) file/upload event. Header-level payer and
    total-paid info; the individual claim-level payment lines it produced
    are Payment rows (see app.billing.models.payment.Payment).
    """

    __tablename__ = "remittance_advices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    payer_name = Column(String(255), nullable=True)

    total_paid_amount = Column(Numeric(12, 2), nullable=True)

    payment_date = Column(String(16), nullable=True, doc="Raw 835 CCYYMMDD payment date")

    claim_count = Column(Integer, nullable=False, default=0, server_default=text("0"))

    file_name = Column(String(255), nullable=True)

    raw_content = Column(Text, nullable=True)

    status = Column(
        String(32),
        nullable=False,
        default="RECEIVED",
        server_default=text("'RECEIVED'"),
        doc="RECEIVED / POSTED / PARTIALLY_POSTED",
    )

    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    created_by = Column(String(255), nullable=True)

    tenant = relationship("Tenant")
    payments = relationship("Payment", back_populates="remittance_advice")

    __table_args__ = (
        Index("ix_remittance_advice_tenant_status", "tenant_id", "status"),
    )
