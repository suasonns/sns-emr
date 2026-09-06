# api/owner_billing_licensing.py
"""
Owner Portal → Billing & Licensing Management API contracts.

Backed by subscription_plans / tenant_subscriptions / platform_invoices
/ platform_payments / license_allocations (alembic revision
e4f5a6b7c8d9). These tables exist but contain no real records yet --
no tenant has been onboarded onto a platform subscription. Every
endpoint below is a REAL, routable, owner-guarded FastAPI endpoint
that returns a structurally valid BillingLicensingResponse (or
sub-resource) with data_available reflecting whether any subscription
row actually exists -- empty/None fields until then, never a
fabricated number.

This lets the frontend (sns-emr-frontend/src/owner/pages/
BillingLicensing.jsx, via fetchOwnerBillingLicensing() in
sns-emr-frontend/src/api/ownerAdmin.ts) hit a real 200 response today
and render its honest "no billing data available yet" empty state.
Onboarding a real tenant subscription (via SubscriptionPlan +
TenantSubscription rows) is the only remaining step to populate this
page with real data -- no route/contract/frontend change is needed.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.role_guards import require_owner
from app.core.security import CurrentUser, get_current_user
from app.schemas.owner_billing_licensing import (
    BillingLicensingResponse,
    InvoiceSummary,
    LicenseAllocation,
    PaymentHistory,
    RevenueByAgency,
    RevenueMetrics,
    TenantBillingSummary,
)
from app.services.owner_billing_service import OwnerBillingService
from app.services.owner_licensing_service import OwnerLicensingService
from app.services.owner_revenue_service import OwnerRevenueService

router = APIRouter(prefix="/api/owner/billing-licensing", tags=["Owner Billing & Licensing"])


_NOT_IMPLEMENTED_REASON = (
    "Platform billing/licensing tables exist but contain no records yet "
    "(no tenant has an active subscription/invoice/payment on file). "
    "See backend readiness report."
)


def _require_platform_owner(user: CurrentUser) -> None:
    require_owner(user)


@router.get("", response_model=BillingLicensingResponse)
def get_billing_licensing(
    tenant_id: Optional[UUID] = Query(default=None),
    quarter_start: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> BillingLicensingResponse:
    """
    Full composite payload. Mirrors GET /api/owner/billing-licensing
    called by fetchOwnerBillingLicensing() in the frontend.
    """
    _require_platform_owner(user)

    billing_service = OwnerBillingService(db)
    licensing_service = OwnerLicensingService(db)
    revenue_service = OwnerRevenueService(db)

    kpis = revenue_service.get_revenue_kpis(tenant_id)
    clients = billing_service.get_client_billing_overview(tenant_id)
    revenue_by_agency = revenue_service.get_revenue_by_agency(tenant_id)
    recent_payments = billing_service.get_recent_payments(tenant_id)
    upcoming_outstandings = billing_service.get_upcoming_outstandings(tenant_id)
    license_allocations = licensing_service.get_license_allocations(tenant_id)
    total_used, total_allocated = licensing_service.get_total_seats(tenant_id)

    # data_available reflects whether any subscription/invoice/payment
    # record exists yet -- not whether the tables exist (they do). An
    # empty result set is the honest, expected state until agencies are
    # actually onboarded onto a platform subscription.
    has_any_data = bool(clients or license_allocations or kpis.total_monthly_revenue is not None)

    return BillingLicensingResponse(
        kpis=kpis,
        clients=clients,
        revenue_by_agency=revenue_by_agency,
        recent_payments=recent_payments,
        upcoming_outstandings=upcoming_outstandings,
        license_allocations=license_allocations,
        total_seats_used=total_used,
        total_seats_allocated=total_allocated,
        data_available=has_any_data,
        unavailable_reason=None if has_any_data else _NOT_IMPLEMENTED_REASON,
    )


@router.get("/kpis", response_model=RevenueMetrics)
def get_billing_kpis(
    tenant_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> RevenueMetrics:
    _require_platform_owner(user)
    return OwnerRevenueService(db).get_revenue_kpis(tenant_id)


@router.get("/licenses", response_model=list[LicenseAllocation])
def get_license_allocations(
    tenant_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[LicenseAllocation]:
    _require_platform_owner(user)
    return OwnerLicensingService(db).get_license_allocations(tenant_id)


@router.get("/invoices", response_model=list[InvoiceSummary])
def get_upcoming_invoices(
    tenant_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[InvoiceSummary]:
    _require_platform_owner(user)
    return OwnerBillingService(db).get_upcoming_outstandings(tenant_id)


@router.get("/payments", response_model=list[PaymentHistory])
def get_recent_payments(
    tenant_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[PaymentHistory]:
    _require_platform_owner(user)
    return OwnerBillingService(db).get_recent_payments(tenant_id)


@router.get("/revenue", response_model=list[RevenueByAgency])
def get_revenue_by_agency(
    tenant_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[RevenueByAgency]:
    _require_platform_owner(user)
    return OwnerRevenueService(db).get_revenue_by_agency(tenant_id)


@router.get("/tenants", response_model=list[TenantBillingSummary])
def get_tenant_billing_summaries(
    tenant_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[TenantBillingSummary]:
    """Per-tenant billing summary rows (Client Billing Overview table)."""
    _require_platform_owner(user)
    return OwnerBillingService(db).get_client_billing_overview(tenant_id)
