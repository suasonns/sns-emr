"""
Accounts-receivable aging report -- standard healthcare AR aging computed
entirely from existing claims/payment/adjustment/denial records.

No new data store. This module is pure calculation over data already
persisted by app.billing.models.claim.Claim,
app.billing.models.payment.Payment,
app.billing.models.payment_adjustment.PaymentAdjustment, and
app.billing.models.denial.Denial -- the same tables backing the Claims
Management, Payment Posting, and Denials & Appeals pages.

BUSINESS RULE (approved 2026-09-05):
    Outstanding Balance = Total Charges
                           - Posted Payments
                           - Adjustments (835 CAS lines, all group codes)
                           - Write-offs (denials the biller marked
                             WRITTEN_OFF instead of appealing)

    Claims whose computed balance is <= 0 (fully paid, or overpaid) are
    excluded from this report -- an overpayment is a credit-balance
    concern, not an aging/collection concern (see the separate Credit
    Balance Report).

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

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.billing.models.claim import Claim
from app.billing.models.denial import Denial
from app.billing.models.payment import Payment
from app.billing.models.payment_adjustment import PaymentAdjustment
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.tenant import Tenant

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


def _patient_name(first_name: str | None, middle_name: str | None, last_name: str | None) -> str | None:
    parts = [p for p in (first_name, middle_name, last_name) if p]
    return " ".join(parts) if parts else None


@dataclass
class _BucketTotals:
    total_outstanding: Decimal = field(default_factory=lambda: Decimal("0.00"))
    claim_count: int = 0

    def add(self, amount: Decimal) -> None:
        self.total_outstanding += amount
        self.claim_count += 1


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
        return {
            "as_of": as_of.isoformat(),
            "summary": {"total_outstanding": "0.00", "claim_count": 0, "average_days_outstanding": 0},
            "by_bucket": [{"bucket": b, "total_outstanding": "0.00", "claim_count": 0} for b in AGING_BUCKETS],
            "by_payer": [],
            "by_agency": [],
            "claims": [],
        }

    tenant_id_strs = [str(t) for t in tenant_ids]

    # 1) Submitted claims for these tenants (aging clock requires exported_at).
    claim_rows = (
        db.query(
            Claim.id.label("claim_id"),
            Claim.tenant_id.label("tenant_id"),
            Claim.patient_id.label("patient_id"),
            Claim.payer_name.label("payer_name"),
            Claim.total_charge.label("total_charge"),
            Claim.status.label("status"),
            Claim.claim_control_number.label("claim_control_number"),
            Claim.exported_at.label("exported_at"),
            Patient.mrn.label("mrn"),
            PatientFaceSheet.first_name.label("patient_first_name"),
            PatientFaceSheet.middle_name.label("patient_middle_name"),
            PatientFaceSheet.last_name.label("patient_last_name"),
        )
        .join(Patient, Patient.id == Claim.patient_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .filter(Claim.tenant_id.in_(tenant_id_strs))
        .filter(Claim.exported_at.isnot(None))
        .all()
    )

    if not claim_rows:
        return {
            "as_of": as_of.isoformat(),
            "summary": {"total_outstanding": "0.00", "claim_count": 0, "average_days_outstanding": 0},
            "by_bucket": [{"bucket": b, "total_outstanding": "0.00", "claim_count": 0} for b in AGING_BUCKETS],
            "by_payer": [],
            "by_agency": [],
            "claims": [],
        }

    claim_ids = [r.claim_id for r in claim_rows]

    # 2) Posted payments per claim.
    payments_by_claim: dict = dict(
        db.query(Payment.claim_id, func.coalesce(func.sum(Payment.paid_amount), 0))
        .filter(Payment.claim_id.in_(claim_ids))
        .group_by(Payment.claim_id)
        .all()
    )

    # 3) 835 CAS adjustments per claim (all group codes -- CO/PR/OA/PI/CR).
    adjustments_by_claim: dict = dict(
        db.query(Payment.claim_id, func.coalesce(func.sum(PaymentAdjustment.amount), 0))
        .join(PaymentAdjustment, PaymentAdjustment.payment_id == Payment.id)
        .filter(Payment.claim_id.in_(claim_ids))
        .group_by(Payment.claim_id)
        .all()
    )

    # 4) Biller-initiated write-offs (denials explicitly marked WRITTEN_OFF).
    write_offs_by_claim: dict = dict(
        db.query(Denial.claim_id, func.coalesce(func.sum(Denial.denied_amount), 0))
        .filter(Denial.claim_id.in_(claim_ids))
        .filter(Denial.status == "WRITTEN_OFF")
        .group_by(Denial.claim_id)
        .all()
    )

    # 5) Agency display names for the "By Agency" breakdown.
    agency_names: dict = {
        str(t.id): (t.display_name or t.legal_name)
        for t in db.query(Tenant.id, Tenant.display_name, Tenant.legal_name)
        .filter(Tenant.id.in_(tenant_id_strs))
        .all()
    }

    bucket_totals: dict[str, _BucketTotals] = {b: _BucketTotals() for b in AGING_BUCKETS}
    payer_totals: dict[str, dict] = defaultdict(lambda: {"total_outstanding": Decimal("0.00"), "claim_count": 0, "by_bucket": {b: Decimal("0.00") for b in AGING_BUCKETS}})
    agency_totals: dict[str, dict] = defaultdict(lambda: {"total_outstanding": Decimal("0.00"), "claim_count": 0, "by_bucket": {b: Decimal("0.00") for b in AGING_BUCKETS}})

    claims_out = []
    total_outstanding = Decimal("0.00")
    total_days_weighted = 0

    for r in claim_rows:
        total_charge = Decimal(str(r.total_charge or 0))
        posted_payments = Decimal(str(payments_by_claim.get(r.claim_id, 0)))
        adjustments = Decimal(str(adjustments_by_claim.get(r.claim_id, 0)))
        write_offs = Decimal(str(write_offs_by_claim.get(r.claim_id, 0)))

        outstanding = total_charge - posted_payments - adjustments - write_offs

        # Fully paid/overpaid claims are not an aging/collection concern --
        # they belong on the (separate, not-yet-built) Credit Balance Report.
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
                "patient_name": _patient_name(r.patient_first_name, r.patient_middle_name, r.patient_last_name),
                "mrn": r.mrn,
                "payer_name": payer_name,
                "claim_control_number": r.claim_control_number,
                "status": r.status,
                "total_charge": str(total_charge.quantize(Decimal("0.01"))),
                "posted_payments": str(posted_payments.quantize(Decimal("0.01"))),
                "adjustments": str(adjustments.quantize(Decimal("0.01"))),
                "write_offs": str(write_offs.quantize(Decimal("0.01"))),
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
