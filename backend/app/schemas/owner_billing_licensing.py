# schemas/owner_billing_licensing.py
"""
DTOs for the Owner Portal → Billing & Licensing Management page.

Backed by app.models.subscription_plan.SubscriptionPlan,
tenant_subscription.TenantSubscription, platform_invoice.PlatformInvoice,
platform_payment.PlatformPayment, and license_allocation.LicenseAllocation
(alembic revision e4f5a6b7c8d9). Every field here is intentionally
Optional / defaults to an empty collection because those tables
currently contain no rows -- no tenant has been onboarded onto a
platform subscription yet. OwnerBillingService/OwnerLicensingService/
OwnerRevenueService populate real values once real subscription/
invoice/payment records exist, WITHOUT changing this contract or the
frontend types in sns-emr-frontend/src/api/ownerAdmin.ts
(OwnerBillingLicensingResponse mirrors this module field-for-field).

Do not populate these with fabricated values. Until real
subscription/invoice/payment rows exist, every field must be
None / [] -- never an invented figure.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class RevenueMetrics(BaseModel):
    """Aggregate SNS-side revenue KPIs. Requires platform_invoices/platform_payments."""

    total_monthly_revenue: Optional[float] = None
    outstanding_invoice_count: Optional[int] = None
    outstanding_invoice_total: Optional[float] = None
    active_agencies: Optional[int] = None
    licensed_agencies: Optional[int] = None
    avg_revenue_per_agency: Optional[float] = None


class TenantBillingSummary(BaseModel):
    """One row of the Client Billing Overview table. Requires subscriptions + platform_invoices."""

    tenant_id: str
    agency_name: str
    plan_type: Optional[str] = None
    seats_used: Optional[int] = None
    seats_licensed: Optional[int] = None
    monthly_rate: Optional[float] = None
    last_payment_date: Optional[date] = None
    status: Optional[str] = None  # PAID / OVERDUE / PENDING / TRIAL
    balance_due: Optional[float] = None


class RevenueByAgency(BaseModel):
    tenant_id: str
    agency_name: str
    amount: Optional[float] = None


class PaymentHistory(BaseModel):
    """One row of Recent History. Requires platform_payments (distinct from claim-level `payments`)."""

    tenant_id: str
    agency_name: str
    occurred_at: Optional[datetime] = None
    amount: Optional[float] = None
    status: Optional[str] = None  # SUCCESS / PENDING / OVERDUE


class InvoiceSummary(BaseModel):
    """One row of Upcoming Outstandings. Requires platform_invoices."""

    tenant_id: str
    agency_name: str
    due_date: Optional[date] = None
    amount: Optional[float] = None
    status: Optional[str] = None  # UPCOMING / OVERDUE


class RenewalSummary(BaseModel):
    """Subscription renewal/term date. Requires subscriptions.renewal_date."""

    tenant_id: str
    agency_name: str
    renewal_date: Optional[date] = None
    plan_type: Optional[str] = None


class LicenseAllocation(BaseModel):
    """One plan tier's seat usage. Requires license_allocations (or seat columns on subscriptions)."""

    plan_label: str
    seats_used: Optional[int] = None
    seats_total: Optional[int] = None


class BillingLicensingResponse(BaseModel):
    """
    Full payload for GET /api/owner/billing-licensing.

    Mirrors OwnerBillingLicensingResponse in
    sns-emr-frontend/src/api/ownerAdmin.ts. Keep both in sync when this
    contract changes.
    """

    kpis: RevenueMetrics
    clients: List[TenantBillingSummary] = []
    revenue_by_agency: List[RevenueByAgency] = []
    recent_payments: List[PaymentHistory] = []
    upcoming_outstandings: List[InvoiceSummary] = []
    license_allocations: List[LicenseAllocation] = []
    total_seats_used: Optional[int] = None
    total_seats_allocated: Optional[int] = None
    data_available: bool = False
    unavailable_reason: Optional[str] = (
        "No tenant is currently subscribed to a platform billing plan. "
        "This response is real, not a stub -- see backend readiness report."
    )
