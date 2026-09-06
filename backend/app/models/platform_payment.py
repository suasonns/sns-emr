# models/platform_payment.py
"""
A payment SNS received from a tenant against a PlatformInvoice -- the
"Recent History" source. Distinct from app.billing.models.payment.Payment,
which is a payer's ERA remittance to a tenant for a patient claim.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PlatformPayment(BaseModel):
    __tablename__ = "platform_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("platform_invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    amount = Column(Numeric(12, 2), nullable=True)

    status = Column(
        String(32),
        nullable=False,
        server_default=text("'PENDING'"),
        index=True,
    )
    # SUCCESS / PENDING / OVERDUE / FAILED

    occurred_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant")
    invoice = relationship("PlatformInvoice")

    __table_args__ = (
        Index("ix_platform_payments_tenant_status", "tenant_id", "status"),
        Index("ix_platform_payments_occurred_at", "occurred_at"),
    )
