"""
Credit Balance Report -- claim-level overpayment detection AND
patient/account-level summary, computed from existing claims/payment/
adjustment/denial records (see app.billing.services.claim_financials for
the shared per-claim arithmetic also used by the Aging Report).

BUSINESS RULE (approved 2026-09-05, hybrid claim+account model):

    Claim Net Balance = Total Charges - Posted Payments - Adjustments
                         - Write-offs           (see claim_financials)

    A potential credit balance exists when Claim Net Balance < 0.
    Credit Amount = ABS(Claim Net Balance).

    CLAIM-LEVEL is the authoritative detection/resolution grain -- see
    claim_credit_items. PATIENT/ACCOUNT-LEVEL (patient_accounts) is a
    reporting summary only and must NEVER net away or suppress an
    individual claim's credit balance (a patient with one -$1,000 claim
    and one +$1,000 outstanding claim still shows the -$1,000 claim as a
    credit requiring review, even though their net balance is $0).

    No new financial ledger is created here. A CreditBalanceCase (see
    app.billing.models.credit_balance_case) is only created once a biller
    opens/reviews a claim credit item -- see credit_balance_case_service.
    This module is read-only calculation.

MEDICARE CMS-838 CLASSIFICATION (kept deliberately simple -- three states
only, per approved business rule; this is NOT a payer-taxonomy engine):

    MEDICARE_REPORTABLE -- payer_type resolved to a recognized Medicare
        payer type (MEDICARE_PAYER_TYPES, shared with MSP validation).
    NON_MEDICARE -- payer_type resolved to something else.
    UNKNOWN -- payer_type could not be resolved (no matching PatientPayer
        record for this claim's payer); requires manual billing review.

    Classification is derived strictly from real structured payer metadata
    -- app.models.patient_payer.PatientPayer.payer_type (matched to the
    claim's payer via app.billing.services.claim_financials), reusing the
    same MEDICARE_PAYER_TYPES definition as MSP validation
    (app.billing.services.msp_validation_service). This is NOT a
    payer-name heuristic: a claim whose payer_type cannot be resolved is
    UNKNOWN and requires manual biller review -- it is never guessed from
    the payer_name string. No additional automatic classifications are
    introduced beyond these three unless there is a real business
    requirement.

DUPLICATE PAYMENT DETECTION:
    A claim with 2+ posted Payment rows sharing the exact same nonzero
    paid_amount is flagged "potential_duplicate_payment": true. This is a
    mechanical detection signal only -- the system never auto-assigns a
    root cause. A biller reviewing the case selects the actual cause
    (duplicate payment, posting error, COB issue, MSP issue, recoupment
    timing, or other) via the case action's reason_code -- see
    credit_balance_case_service.DUPLICATE_PAYMENT_REASON_CODES.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.billing.models.credit_balance_case import CreditBalanceCase
from app.billing.services.claim_financials import (
    ClaimFinancialRow,
    agency_display_names,
    find_potential_duplicate_payment_claim_ids,
    load_claim_financials,
)
from app.billing.services.msp_validation_service import MEDICARE_PAYER_TYPES

MEDICARE_REPORTABLE = "MEDICARE_REPORTABLE"
NON_MEDICARE = "NON_MEDICARE"
UNKNOWN = "UNKNOWN"


def classify_medicare_reportability(payer_type: str | None) -> str:
    """
    CMS-838 reportability classification from real payer metadata only
    (PatientPayer.payer_type -- see app.billing.services.claim_financials
    for how it's resolved for a claim). MEDICARE_PAYER_TYPES is the same
    set MSP validation uses to identify "this payer IS Medicare"
    (currently {"MEDICARE", "MEDICARE_HOSPICE"} -- both traditional
    Medicare Part A/B fee-for-service, the only claims CMS-838 covers).

    Deliberately simple -- three states only (MEDICARE_REPORTABLE,
    NON_MEDICARE, UNKNOWN). No payer-name parsing, no fuzzy matching, no
    payer-taxonomy engine. If payer_type is missing (no matching
    PatientPayer record was found for this claim's payer), the
    classification is UNKNOWN and a biller must review and reclassify
    manually (see credit_balance_case_service.RECLASSIFY_MEDICARE) -- it
    is never guessed.
    """
    if not payer_type or not payer_type.strip():
        return UNKNOWN

    normalized = payer_type.strip().upper()
    if normalized in MEDICARE_PAYER_TYPES:
        return MEDICARE_REPORTABLE

    return NON_MEDICARE


@dataclass
class _PatientAccumulator:
    patient_id: str
    patient_name: str | None
    mrn: str | None
    tenant_id: str
    agency_name: str
    payer_names: set = field(default_factory=set)
    primary_payer_name: str | None = None
    secondary_payer_name: str | None = None
    total_charges: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_payments: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_adjustments: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_write_offs: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_positive_ar: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_credit_balance: Decimal = field(default_factory=lambda: Decimal("0.00"))
    claims_with_credit: int = 0
    oldest_unresolved_credit_exported_at: object = None


def _q2(amount: Decimal) -> str:
    return str(amount.quantize(Decimal("0.01")))


def _empty_report(as_of: date) -> dict:
    return {
        "generated_at": date.today().isoformat(),
        "as_of_date": as_of.isoformat(),
        "summary": {
            "total_potential_credits": {"amount": "0.00", "currency": "USD"},
            "claim_count": 0,
            "patient_count": 0,
        },
        "patient_accounts": [],
        "claim_credit_items": [],
    }


def build_credit_balance_report(
    db: Session,
    tenant_ids: list[UUID],
    as_of: date | None = None,
) -> dict:
    """
    Build the Credit Balance Report for one or more agency tenants.

    Callers are responsible for all authorization (see
    app.billing.scope.resolve_multi_agency_tenant_ids) -- this function
    only calculates.
    """
    as_of = as_of or date.today()

    if not tenant_ids:
        return _empty_report(as_of)

    claim_rows: list[ClaimFinancialRow] = load_claim_financials(db, tenant_ids, require_exported=False)
    if not claim_rows:
        return _empty_report(as_of)

    agency_names = agency_display_names(db, tenant_ids)

    # Existing cases for these claims -- if a biller already opened/
    # reviewed one, the report must reflect its real status, not a fresh
    # POTENTIAL guess (most-recently-created case wins if more than one
    # exists for a claim, which should not normally happen).
    claim_ids = [r.claim_id for r in claim_rows]
    existing_cases: dict = {}
    if claim_ids:
        for case in (
            db.query(CreditBalanceCase)
            .filter(CreditBalanceCase.claim_id.in_(claim_ids))
            .order_by(CreditBalanceCase.created_at.asc())
            .all()
        ):
            existing_cases[case.claim_id] = case

    duplicate_payment_claim_ids = find_potential_duplicate_payment_claim_ids(db, claim_ids)

    patient_accumulators: dict[str, _PatientAccumulator] = {}
    claim_items: list[dict] = []
    total_credit = Decimal("0.00")

    for r in claim_rows:
        patient_key = str(r.patient_id)
        agency_id = str(r.tenant_id)
        agency_name = agency_names.get(agency_id, agency_id)

        acc = patient_accumulators.get(patient_key)
        if acc is None:
            acc = _PatientAccumulator(
                patient_id=patient_key,
                patient_name=r.patient_name,
                mrn=r.mrn,
                tenant_id=agency_id,
                agency_name=agency_name,
            )
            patient_accumulators[patient_key] = acc

        acc.payer_names.add(r.payer_name or "Unknown Payer")
        # Same for every claim of this patient (resolved from PatientPayer,
        # not per-claim) -- set once, cheap to overwrite repeatedly.
        acc.primary_payer_name = r.primary_payer_name
        acc.secondary_payer_name = r.secondary_payer_name
        acc.total_charges += r.total_charge
        acc.total_payments += r.posted_payments
        acc.total_adjustments += r.adjustments
        acc.total_write_offs += r.write_offs

        net = r.net_balance
        if net > 0:
            acc.total_positive_ar += net
            continue
        if net == 0:
            continue

        # net < 0 -- a claim-level potential credit balance. NEVER netted
        # away against this patient's other claims (per business rule).
        credit_amount = -net
        acc.total_credit_balance += credit_amount
        acc.claims_with_credit += 1
        if r.exported_at is not None and (
            acc.oldest_unresolved_credit_exported_at is None
            or r.exported_at < acc.oldest_unresolved_credit_exported_at
        ):
            acc.oldest_unresolved_credit_exported_at = r.exported_at

        total_credit += credit_amount

        medicare_classification = classify_medicare_reportability(r.payer_type)
        existing_case = existing_cases.get(r.claim_id)

        claim_items.append(
            {
                "claim_id": str(r.claim_id),
                "tenant_id": agency_id,
                "agency_name": agency_name,
                "patient_id": patient_key,
                "patient_name": r.patient_name,
                "mrn": r.mrn,
                "payer_name": r.payer_name or "Unknown Payer",
                # Patient-level payer responsibility (billing context only
                # -- see claim_financials._payer_priority_lookup). A claim
                # may be billed to a payer that differs from the patient's
                # designated primary (e.g. billed to Medicare while the
                # patient's on-file primary is something else) -- both are
                # shown so a biller isn't missing coordination-of-benefits
                # context when reviewing a credit balance.
                "primary_payer_name": r.primary_payer_name,
                "secondary_payer_name": r.secondary_payer_name,
                # "If available" operational context -- amounts posted
                # specifically from the patient's on-file primary/secondary
                # payer (matched via the posting remittance's payer_name;
                # see claim_financials.load_claim_financials). Zero, not
                # fabricated, when that payer hasn't posted anything on
                # this claim yet.
                "primary_payer_paid": {"amount": _q2(r.primary_payer_paid), "currency": "USD"},
                "secondary_payer_paid": {"amount": _q2(r.secondary_payer_paid), "currency": "USD"},
                "most_recent_payment_date": r.most_recent_payment_date,
                "claim_control_number": r.claim_control_number,
                "status": r.status,
                "total_charge": {"amount": _q2(r.total_charge), "currency": "USD"},
                "posted_payments": {"amount": _q2(r.posted_payments), "currency": "USD"},
                "adjustments": {"amount": _q2(r.adjustments), "currency": "USD"},
                "write_offs": {"amount": _q2(r.write_offs), "currency": "USD"},
                "credit_amount": {"amount": _q2(credit_amount), "currency": "USD"},
                "exported_at": r.exported_at.isoformat() if r.exported_at else None,
                "payment_count": r.payment_count,
                # Detection only -- see module docstring. Root cause is
                # never auto-assigned; a biller selects it via the case
                # action's reason_code once reviewed.
                "potential_duplicate_payment": r.claim_id in duplicate_payment_claim_ids,
                "medicare_classification": (
                    existing_case.medicare_classification if existing_case else medicare_classification
                ),
                # COMPLETE when payer metadata (PatientPayer.payer_type) was
                # actually found for this claim's payer; PARTIAL when no
                # matching PatientPayer record exists (classification fell
                # back to UNKNOWN and requires manual review).
                "data_completeness": "COMPLETE" if r.payer_type else "PARTIAL",
                # No case has been opened yet for an ad-hoc calculated
                # item -- the biller opens one from the UI (see
                # credit_balance_case_service.open_case_for_claim), at
                # which point case_id/status below reflect the real case.
                "case_id": str(existing_case.id) if existing_case else None,
                "case_status": existing_case.status if existing_case else "POTENTIAL",
                "reason_code": existing_case.reason_code if existing_case else None,
            }
        )

    patient_accounts_out = []
    for acc in patient_accumulators.values():
        if acc.claims_with_credit == 0:
            continue
        net_patient_balance = acc.total_positive_ar - acc.total_credit_balance
        patient_accounts_out.append(
            {
                "patient_id": acc.patient_id,
                "patient_name": acc.patient_name,
                "mrn": acc.mrn,
                "tenant_id": acc.tenant_id,
                "agency_name": acc.agency_name,
                "payer_names": sorted(acc.payer_names),
                "primary_payer_name": acc.primary_payer_name,
                "secondary_payer_name": acc.secondary_payer_name,
                "total_charges": {"amount": _q2(acc.total_charges), "currency": "USD"},
                "total_payments": {"amount": _q2(acc.total_payments), "currency": "USD"},
                "total_adjustments": {"amount": _q2(acc.total_adjustments), "currency": "USD"},
                "total_write_offs": {"amount": _q2(acc.total_write_offs), "currency": "USD"},
                "total_positive_ar": {"amount": _q2(acc.total_positive_ar), "currency": "USD"},
                "total_credit_balance": {"amount": _q2(acc.total_credit_balance), "currency": "USD"},
                "net_patient_account_balance": {"amount": _q2(net_patient_balance), "currency": "USD"},
                "claims_with_credit": acc.claims_with_credit,
                "oldest_unresolved_credit": (
                    acc.oldest_unresolved_credit_exported_at.isoformat()
                    if acc.oldest_unresolved_credit_exported_at
                    else None
                ),
            }
        )

    patient_accounts_out.sort(key=lambda p: Decimal(p["total_credit_balance"]["amount"]), reverse=True)
    claim_items.sort(key=lambda c: Decimal(c["credit_amount"]["amount"]), reverse=True)

    return {
        "generated_at": date.today().isoformat(),
        "as_of_date": as_of.isoformat(),
        "summary": {
            "total_potential_credits": {"amount": _q2(total_credit), "currency": "USD"},
            "claim_count": len(claim_items),
            "patient_count": len(patient_accounts_out),
        },
        "patient_accounts": patient_accounts_out,
        "claim_credit_items": claim_items,
    }
