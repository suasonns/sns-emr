# services/owner_revenue_service.py
"""
OwnerRevenueService — SNS-side platform revenue aggregation (what agencies
pay SNS). This is intentionally DISTINCT from app/billing/services/
revenue_service.py, which computes a tenant's own hospice-claim revenue
from payers -- that is agency-scoped clinical/billing revenue, not
platform revenue.

Backed by platform_invoices / tenant_subscriptions (see alembic
revision e4f5a6b7c8d9). Until those tables are populated with real
subscription/invoice data, every query below returns empty/None
results honestly -- an all-None RevenueMetrics is treated the same as
"not available yet" by the caller (see api/owner_billing_licensing.py).
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.platform_invoice import PlatformInvoice
from app.models.tenant import Tenant
from app.models.tenant_subscription import TenantSubscription
from app.schemas.owner_billing_licensing import RevenueByAgency, RevenueMetrics


class OwnerRevenueService:
    def __init__(self, db: Session):
        self.db = db

    def get_revenue_kpis(self, tenant_id: Optional[UUID] = None) -> RevenueMetrics:
        """Total monthly revenue, avg revenue per agency, etc."""
        active_query = select(TenantSubscription).where(TenantSubscription.status == "ACTIVE")
        if tenant_id is not None:
            active_query = active_query.where(TenantSubscription.tenant_id == tenant_id)
        active_subscriptions = self.db.execute(active_query).scalars().all()

        total_monthly_revenue: Optional[float] = None
        avg_revenue_per_agency: Optional[float] = None
        active_agencies: Optional[int] = None

        rates = [
            float(sub.monthly_rate_override)
            for sub in active_subscriptions
            if sub.monthly_rate_override is not None
        ]
        if rates:
            total_monthly_revenue = sum(rates)
            active_agencies = len({sub.tenant_id for sub in active_subscriptions})
            avg_revenue_per_agency = total_monthly_revenue / active_agencies if active_agencies else None

        outstanding_query = select(
            func.count(PlatformInvoice.id), func.coalesce(func.sum(PlatformInvoice.amount), 0)
        ).where(PlatformInvoice.status.in_(["PENDING", "OVERDUE"]))
        if tenant_id is not None:
            outstanding_query = outstanding_query.where(PlatformInvoice.tenant_id == tenant_id)
        outstanding_count, outstanding_total = self.db.execute(outstanding_query).one()

        licensed_query = select(func.count(TenantSubscription.id))
        if tenant_id is not None:
            licensed_query = licensed_query.where(TenantSubscription.tenant_id == tenant_id)
        licensed_agencies = self.db.execute(licensed_query).scalar_one_or_none()

        return RevenueMetrics(
            total_monthly_revenue=total_monthly_revenue,
            outstanding_invoice_count=int(outstanding_count) if outstanding_count else None,
            outstanding_invoice_total=float(outstanding_total) if outstanding_count else None,
            active_agencies=active_agencies,
            licensed_agencies=int(licensed_agencies) if licensed_agencies else None,
            avg_revenue_per_agency=avg_revenue_per_agency,
        )

    def get_revenue_by_agency(self, tenant_id: Optional[UUID] = None) -> List[RevenueByAgency]:
        """Revenue Contribution by Agency panel."""
        query = (
            select(
                Tenant.id,
                func.coalesce(Tenant.display_name, Tenant.legal_name),
                func.coalesce(func.sum(TenantSubscription.monthly_rate_override), 0),
            )
            .select_from(TenantSubscription)
            .join(Tenant, Tenant.id == TenantSubscription.tenant_id)
            .where(TenantSubscription.status == "ACTIVE")
            .group_by(Tenant.id, Tenant.display_name, Tenant.legal_name)
        )
        if tenant_id is not None:
            query = query.where(TenantSubscription.tenant_id == tenant_id)

        rows = self.db.execute(query).all()
        return [
            RevenueByAgency(tenant_id=str(row[0]), agency_name=row[1], amount=float(row[2]) if row[2] else None)
            for row in rows
        ]
