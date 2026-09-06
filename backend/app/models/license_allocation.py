# models/license_allocation.py
"""
Per-tenant, per-plan-tier seat allocation -- the "License Allocation
Summary" panel source. Kept as its own table (rather than reusing
TenantSubscription.seats_licensed alone) so a tenant with seats split
across multiple plan tiers (e.g. a legacy migration) can be
represented without redesigning TenantSubscription.

seats_used is a snapshot column, not computed live from `users` here,
so OwnerLicensingService can choose to reconcile it against active
user counts once this table is populated -- see
OwnerLicensingService.get_license_allocations.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class LicenseAllocation(BaseModel):
    __tablename__ = "license_allocations"

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

    plan_label = Column(String(255), nullable=False)

    seats_used = Column(Integer, nullable=True)
    seats_total = Column(Integer, nullable=True)

    tenant = relationship("Tenant")
    subscription = relationship("TenantSubscription")

    __table_args__ = (
        Index("ix_license_allocations_tenant_plan", "tenant_id", "plan_label"),
    )
