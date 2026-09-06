# models/platform_invoice.py
"""
An invoice SNS issues to a tenant for its subscription (platform
billing) -- the "Upcoming Outstandings" / balance-due source. Distinct
from app.billing.models.claim.Claim, which is a hospice claim a tenant
bills to a PAYER on behalf of a patient.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, Date, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PlatformInvoice(BaseModel):
    __tablename__ = "platform_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenant_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    invoice_number = Column(String(64), nullable=True, unique=True)

    amount = Column(Numeric(12, 2), nullable=True)

    status = Column(
        String(32),
        nullable=False,
        server_default=text("'PENDING'"),
        index=True,
    )
    # PENDING / PAID / OVERDUE / VOID

    issued_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)

    tenant = relationship("Tenant")
    subscription = relationship("TenantSubscription")

    __table_args__ = (
        Index("ix_platform_invoices_tenant_status", "tenant_id", "status"),
        Index("ix_platform_invoices_due_date", "due_date"),
    )
