# models/tenant_subscription.py
"""
One tenant's subscription to an SNS platform plan (the Billing &
Licensing "Client Billing Overview" row source).

Tenant-scoped: every row belongs to exactly one tenant. Distinct from
app.billing.models.contract.Contract, which is a tenant's contract
with an insurance PAYER (clinical billing), not with SNS itself.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, Date, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class TenantSubscription(BaseModel):
    __tablename__ = "tenant_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status = Column(
        String(32),
        nullable=False,
        server_default=text("'TRIAL'"),
        index=True,
    )
    # ACTIVE / TRIAL / PAST_DUE / SUSPENDED / CANCELLED. Client Billing
    # Overview status pill (PAID/OVERDUE/PENDING/TRIAL) is derived from
    # this plus the tenant's most recent PlatformInvoice, not stored
    # redundantly here.

    seats_licensed = Column(Integer, nullable=True)
    monthly_rate_override = Column(Numeric(12, 2), nullable=True)
    # Null means "use plan.monthly_rate"; set only when a tenant has a
    # negotiated rate different from the plan's list price.

    start_date = Column(Date, nullable=True)
    renewal_date = Column(Date, nullable=True)

    tenant = relationship("Tenant")
    plan = relationship("SubscriptionPlan")

    __table_args__ = (
        Index("ix_tenant_subscriptions_tenant_status", "tenant_id", "status"),
        Index("ix_tenant_subscriptions_renewal_date", "renewal_date"),
    )
