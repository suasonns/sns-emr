"""
Accounts-receivable aging report -- standard healthcare AR aging computed
entirely from existing claims/payment/adjustment/denial records.

No new data store. This module is pure calculation over data already
persisted by app.billing.models.claim.Claim,
app.billing.models.payment.Payment,
app.billing.models.payment_adjustment.PaymentAdjustment, and
app.billing.models.denial.Denial -- the same tables backing the Claims
Management, Payment Posting, and Denials & Appeals pages. Per-claim totals
are computed by the shared app.billing.services.claim_financials module,
which is also used by the Credit Balance Report so both reports never
diverge on the underlying arithmetic.

BUSINESS RULE (approved 2026-09-05):
    Outstanding Balance = Total Charges
                           - Posted Payments
                           - Adjustments (835 CAS lines, all group codes)
                           - Write-offs (denials the biller marked
                             WRITTEN_OFF instead of appealing)

    Claims whose computed balance is <= 0 (fully paid, or overpaid) are
    excluded from this report -- an overpayment is a credit-balance
    concern, not an aging/collection concern (see the separate Credit
    Balance Report, app.billing.services.credit_balance_service).

AGING CLOCK (approved 2026-09-05):
    Days outstanding are measured from the claim's submission/export date
    (Claim.exported_at) -- NOT service date, admission date, or
    certification date. This report measures reimbursement collection
    performance AFTER claim submission. A claim with no exported_at has
    never been submitted and has no aging clock yet, so it is excluded.

STANDARD BUCKETS: 0-30, 31-60, 61-90, 91-120, 120+
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.billing.services.claim_financials import agency_display_names, load_claim_financials

AGING_BUCKETS = ["0-30", "31-60", "61-90", "91-120", "120+"]


def _bucket_for_days(days: int) -> str:
    if days <= 30:
        return "0-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    if days <= 120:
        return "91-120"
    return "120+"


@dataclass
class _BucketTotals:
    total_outstanding: Decimal = field(default_factory=lambda: Decimal("0.00"))
    claim_count: int = 0

    def add(self, amount: Decimal) -> None:
        self.total_outstanding += amount
        self.claim_count += 1


def _empty_report(as_of: date) -> dict:
    return {
        "as_of": as_of.isoformat(),
        "summary": {"total_outstanding": "0.00", "claim_count": 0, "average_days_outstanding": 0},
        "by_bucket": [{"bucket": b, "total_outstanding": "0.00", "claim_count": 0} for b in AGING_BUCKETS],
        "by_payer": [],
        "by_agency": [],
        "claims": [],
    }


def build_ar_aging_report(
    db: Session,
    tenant_ids: list[UUID],
    as_of: date | None = None,
) -> dict:
    """
    Build the AR aging report for one or more agency tenants.

    Callers are responsible for authorizing which tenant_ids the current
    user may view (see aging_report_router._resolve_scope_tenant_ids) --
    this function does no authorization of its own, only calculation.
    """
    as_of = as_of or date.today()

    if not tenant_ids:
        return _empty_report(as_of)

    claim_rows = load_claim_financials(db, tenant_ids, require_exported=True)
    if not claim_rows:
        return _empty_report(as_of)

    agency_names = agency_display_names(db, tenant_ids)

    bucket_totals: dict[str, _BucketTotals] = {b: _BucketTotals() for b in AGING_BUCKETS}
    payer_totals: dict[str, dict] = defaultdict(lambda: {"total_outstanding": Decimal("0.00"), "claim_count": 0, "by_bucket": {b: Decimal("0.00") for b in AGING_BUCKETS}})
    agency_totals: dict[str, dict] = defaultdict(lambda: {"total_outstanding": Decimal("0.00"), "claim_count": 0, "by_bucket": {b: Decimal("0.00") for b in AGING_BUCKETS}})

    claims_out = []
    total_outstanding = Decimal("0.00")
    total_days_weighted = 0

    for r in claim_rows:
        outstanding = r.net_balance

        # Fully paid/overpaid claims are not an aging/collection concern --
        # they belong on the (separate) Credit Balance Report.
        if outstanding <= 0:
            continue

        days_outstanding = (as_of - r.exported_at.date()).days
        bucket = _bucket_for_days(max(days_outstanding, 0))

        payer_name = r.payer_name or "Unknown Payer"
        agency_id = str(r.tenant_id)
        agency_name = agency_names.get(agency_id, agency_id)

        bucket_totals[bucket].add(outstanding)
        payer_totals[payer_name]["total_outstanding"] += outstanding
        payer_totals[payer_name]["claim_count"] += 1
        payer_totals[payer_name]["by_bucket"][bucket] += outstanding
        agency_totals[agency_id]["total_outstanding"] += outstanding
        agency_totals[agency_id]["claim_count"] += 1
        agency_totals[agency_id]["by_bucket"][bucket] += outstanding

        total_outstanding += outstanding
        total_days_weighted += days_outstanding

        claims_out.append(
            {
                "claim_id": str(r.claim_id),
                "tenant_id": agency_id,
                "agency_name": agency_name,
                "patient_id": str(r.patient_id),
                "patient_name": r.patient_name,
                "mrn": r.mrn,
                "payer_name": payer_name,
                "claim_control_number": r.claim_control_number,
                "status": r.status,
                "total_charge": str(r.total_charge.quantize(Decimal("0.01"))),
                "posted_payments": str(r.posted_payments.quantize(Decimal("0.01"))),
                "adjustments": str(r.adjustments.quantize(Decimal("0.01"))),
                "write_offs": str(r.write_offs.quantize(Decimal("0.01"))),
                "outstanding_balance": str(outstanding.quantize(Decimal("0.01"))),
                "exported_at": r.exported_at.isoformat() if r.exported_at else None,
                "days_outstanding": days_outstanding,
                "bucket": bucket,
            }
        )

    claims_out.sort(key=lambda c: c["days_outstanding"], reverse=True)

    claim_count = len(claims_out)
    average_days = round(total_days_weighted / claim_count, 1) if claim_count else 0

    return {
        "as_of": as_of.isoformat(),
        "summary": {
            "total_outstanding": str(total_outstanding.quantize(Decimal("0.01"))),
            "claim_count": claim_count,
            "average_days_outstanding": average_days,
        },
        "by_bucket": [
            {
                "bucket": b,
                "total_outstanding": str(bucket_totals[b].total_outstanding.quantize(Decimal("0.01"))),
                "claim_count": bucket_totals[b].claim_count,
            }
            for b in AGING_BUCKETS
        ],
        "by_payer": [
            {
                "payer_name": payer_name,
                "total_outstanding": str(totals["total_outstanding"].quantize(Decimal("0.01"))),
                "claim_count": totals["claim_count"],
                "by_bucket": {b: str(totals["by_bucket"][b].quantize(Decimal("0.01"))) for b in AGING_BUCKETS},
            }
            for payer_name, totals in sorted(payer_totals.items(), key=lambda kv: kv[1]["total_outstanding"], reverse=True)
        ],
        "by_agency": [
            {
                "tenant_id": tenant_id,
                "agency_name": agency_names.get(tenant_id, tenant_id),
                "total_outstanding": str(totals["total_outstanding"].quantize(Decimal("0.01"))),
                "claim_count": totals["claim_count"],
                "by_bucket": {b: str(totals["by_bucket"][b].quantize(Decimal("0.01"))) for b in AGING_BUCKETS},
            }
            for tenant_id, totals in sorted(agency_totals.items(), key=lambda kv: kv[1]["total_outstanding"], reverse=True)
        ],
        "claims": claims_out,
    }
