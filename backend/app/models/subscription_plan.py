# models/subscription_plan.py
"""
Platform-wide subscription plan catalog (SNS's own pricing tiers).

NOT tenant-scoped -- this is SNS's product catalog, analogous to a
price list. A tenant's actual subscription (which plan it is on, its
seat count, its billing status) lives in TenantSubscription, which has
a FK to this table.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, Numeric, String, Integer, Index, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class SubscriptionPlan(BaseModel):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    plan_code = Column(String(64), nullable=False, unique=True, index=True)
    plan_label = Column(String(255), nullable=False)

    monthly_rate = Column(Numeric(12, 2), nullable=True)
    seat_allowance = Column(Integer, nullable=True)

    status = Column(
        String(32),
        nullable=False,
        server_default=text("'ACTIVE'"),
        index=True,
    )
    # ACTIVE / RETIRED -- retired plans stay for historical subscriptions
    # but cannot be assigned to a new TenantSubscription.

    __table_args__ = (
        Index("ix_subscription_plans_status", "status"),
    )
