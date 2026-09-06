# services/owner_billing_service.py
"""
OwnerBillingService — SNS-side tenant billing summary (subscription
plan, invoice status, balance due, payment history) for the Owner
Portal Billing & Licensing page.

Backed by tenant_subscriptions / platform_invoices / platform_payments
(see alembic revision e4f5a6b7c8d9). Until those tables are populated
with real subscription/invoice/payment records, every query below
returns an empty list honestly -- never a fabricated invoice or
balance figure.

This is intentionally separate from:
  - app/billing/services/billing_readiness_service.py (tenant-scoped
    claim/NOE readiness, not platform billing)
  - app/billing/services/revenue_service.py (tenant's own hospice
    claim revenue from payers, not what the tenant pays SNS)
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.platform_invoice import PlatformInvoice
from app.models.platform_payment import PlatformPayment
from app.models.tenant import Tenant
from app.models.tenant_subscription import TenantSubscription
from app.schemas.owner_billing_licensing import (
    InvoiceSummary,
    PaymentHistory,
    TenantBillingSummary,
)


class OwnerBillingService:
    def __init__(self, db: Session):
        self.db = db

    def get_client_billing_overview(
        self, tenant_id: Optional[UUID] = None
    ) -> List[TenantBillingSummary]:
        """Client Billing Overview table rows."""
        # Most recent subscription per tenant (there may be a history of
        # subscriptions; the latest by start_date is the "current" one).
        latest_sub_ids = select(
            func.max(TenantSubscription.created_at).label("latest_created_at"),
            TenantSubscription.tenant_id,
        ).group_by(TenantSubscription.tenant_id).subquery()

        query = (
            select(Tenant, TenantSubscription)
            .join(TenantSubscription, TenantSubscription.tenant_id == Tenant.id)
            .join(
                latest_sub_ids,
                (TenantSubscription.tenant_id == latest_sub_ids.c.tenant_id)
                & (TenantSubscription.created_at == latest_sub_ids.c.latest_created_at),
            )
        )
        if tenant_id is not None:
            query = query.where(Tenant.id == tenant_id)

        rows = self.db.execute(query).all()

        summaries: List[TenantBillingSummary] = []
        for tenant, subscription in rows:
            latest_invoice = self.db.execute(
                select(PlatformInvoice)
                .where(PlatformInvoice.tenant_id == tenant.id)
                .order_by(PlatformInvoice.issued_date.desc().nullslast())
                .limit(1)
            ).scalar_one_or_none()

            latest_payment_date = self.db.execute(
                select(func.max(PlatformPayment.occurred_at)).where(
                    PlatformPayment.tenant_id == tenant.id,
                    PlatformPayment.status == "SUCCESS",
                )
            ).scalar_one_or_none()

            monthly_rate = (
                float(subscription.monthly_rate_override)
                if subscription.monthly_rate_override is not None
                else None
            )

            # Client Billing Overview status pill is PAID/OVERDUE/PENDING/TRIAL
            # (see schemas/owner_billing_licensing.py), derived from the
            # subscription lifecycle plus the tenant's latest invoice --
            # TenantSubscription.status itself is ACTIVE/TRIAL/PAST_DUE/
            # SUSPENDED/CANCELLED and is not surfaced directly.
            if subscription.status == "TRIAL":
                billing_status = "TRIAL"
            elif latest_invoice is not None and latest_invoice.status == "OVERDUE":
                billing_status = "OVERDUE"
            elif latest_invoice is not None and latest_invoice.status == "PENDING":
                billing_status = "PENDING"
            elif latest_invoice is not None and latest_invoice.status == "PAID":
                billing_status = "PAID"
            else:
                billing_status = None

            summaries.append(
                TenantBillingSummary(
                    tenant_id=str(tenant.id),
                    agency_name=tenant.display_name or tenant.legal_name,
                    plan_type=subscription.plan.plan_label if subscription.plan else None,
                    seats_used=None,  # populated via OwnerLicensingService.get_total_seats per tenant
                    seats_licensed=subscription.seats_licensed,
                    monthly_rate=monthly_rate,
                    last_payment_date=latest_payment_date.date() if latest_payment_date else None,
                    status=billing_status,
                    balance_due=float(latest_invoice.amount) if latest_invoice and latest_invoice.status != "PAID" and latest_invoice.amount is not None else None,
                )
            )
        return summaries

    def get_recent_payments(self, tenant_id: Optional[UUID] = None) -> List[PaymentHistory]:
        """Recent History panel."""
        query = (
            select(PlatformPayment, Tenant)
            .join(Tenant, Tenant.id == PlatformPayment.tenant_id)
            .order_by(PlatformPayment.occurred_at.desc().nullslast())
            .limit(25)
        )
        if tenant_id is not None:
            query = query.where(PlatformPayment.tenant_id == tenant_id)

        rows = self.db.execute(query).all()
        return [
            PaymentHistory(
                tenant_id=str(tenant.id),
                agency_name=tenant.display_name or tenant.legal_name,
                occurred_at=payment.occurred_at,
                amount=float(payment.amount) if payment.amount is not None else None,
                status=payment.status,
            )
            for payment, tenant in rows
        ]

    def get_upcoming_outstandings(self, tenant_id: Optional[UUID] = None) -> List[InvoiceSummary]:
        """Upcoming Outstandings panel."""
        query = (
            select(PlatformInvoice, Tenant)
            .join(Tenant, Tenant.id == PlatformInvoice.tenant_id)
            .where(PlatformInvoice.status.in_(["PENDING", "OVERDUE"]))
            .order_by(PlatformInvoice.due_date.asc().nullslast())
            .limit(25)
        )
        if tenant_id is not None:
            query = query.where(PlatformInvoice.tenant_id == tenant_id)

        rows = self.db.execute(query).all()
        return [
            InvoiceSummary(
                tenant_id=str(tenant.id),
                agency_name=tenant.display_name or tenant.legal_name,
                due_date=invoice.due_date,
                amount=float(invoice.amount) if invoice.amount is not None else None,
                # PlatformInvoice.status is PENDING/PAID/OVERDUE/VOID; this
                # DTO's contract (see schemas/owner_billing_licensing.py)
                # is UPCOMING/OVERDUE, so PENDING maps to UPCOMING here.
                status="OVERDUE" if invoice.status == "OVERDUE" else "UPCOMING",
            )
            for invoice, tenant in rows
        ]
