# services/owner_licensing_service.py
"""
OwnerLicensingService — subscription plan / license seat allocation for
the Owner Portal Billing & Licensing page.

Backed by tenant_subscriptions / license_allocations (see alembic
revision e4f5a6b7c8d9). Until those tables are populated, every query
below returns an empty list / (None, None) honestly -- never a
fabricated seat count.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.license_allocation import LicenseAllocation as LicenseAllocationModel
from app.models.tenant import Tenant
from app.models.tenant_subscription import TenantSubscription
from app.schemas.owner_billing_licensing import LicenseAllocation, RenewalSummary


class OwnerLicensingService:
    def __init__(self, db: Session):
        self.db = db

    def get_license_allocations(self, tenant_id: Optional[UUID] = None) -> List[LicenseAllocation]:
        """License Allocation Summary panel, grouped by plan tier."""
        query = select(
            LicenseAllocationModel.plan_label,
            func.coalesce(func.sum(LicenseAllocationModel.seats_used), 0),
            func.coalesce(func.sum(LicenseAllocationModel.seats_total), 0),
        ).group_by(LicenseAllocationModel.plan_label)
        if tenant_id is not None:
            query = query.where(LicenseAllocationModel.tenant_id == tenant_id)

        rows = self.db.execute(query).all()
        return [
            LicenseAllocation(plan_label=row[0], seats_used=int(row[1]), seats_total=int(row[2]))
            for row in rows
        ]

    def get_total_seats(self, tenant_id: Optional[UUID] = None) -> Tuple[Optional[int], Optional[int]]:
        """Returns (total_seats_used, total_seats_allocated)."""
        query = select(
            func.sum(LicenseAllocationModel.seats_used),
            func.sum(LicenseAllocationModel.seats_total),
        )
        if tenant_id is not None:
            query = query.where(LicenseAllocationModel.tenant_id == tenant_id)

        used, total = self.db.execute(query).one()
        return (int(used) if used is not None else None, int(total) if total is not None else None)

    def get_upcoming_renewals(self, tenant_id: Optional[UUID] = None) -> List[RenewalSummary]:
        """Subscription renewal/term dates."""
        query = (
            select(
                TenantSubscription.tenant_id,
                func.coalesce(Tenant.display_name, Tenant.legal_name),
                TenantSubscription.renewal_date,
            )
            .join(Tenant, Tenant.id == TenantSubscription.tenant_id)
            .where(TenantSubscription.renewal_date.is_not(None))
        )
        if tenant_id is not None:
            query = query.where(TenantSubscription.tenant_id == tenant_id)

        rows = self.db.execute(query).all()
        return [
            RenewalSummary(tenant_id=str(row[0]), agency_name=row[1], renewal_date=row[2])
            for row in rows
        ]
