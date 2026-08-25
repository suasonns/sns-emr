from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------
# CLAIM / REVENUE CODE MAP
# ---------------------------------------------------------
# These are structural mappings only.
# Replace / extend based on payer-specific export rules later.
# Do NOT hardcode real reimbursement rates here unless you lock
# your fiscal year + geography + payer schedule intentionally.
# ---------------------------------------------------------

LOC_TO_REVENUE_CODE = {
    "ROUTINE": "0651",
    "CONTINUOUS CARE": "0652",
    "GIP": "0656",
    "RESPITE": "0655",
}


# ---------------------------------------------------------
# DEFAULT RATE SCHEDULE PLACEHOLDER
# ---------------------------------------------------------
# IMPORTANT:
# - This is a STRUCTURE, not an authoritative live Medicare fee schedule.
# - Replace values with your configured payer / fiscal-year schedule.
# - Keeping zeros is safer than inventing real rates.
# ---------------------------------------------------------

DEFAULT_RATE_SCHEDULE = {
    "ROUTINE": Decimal("0.00"),
    "CONTINUOUS CARE": Decimal("0.00"),
    "GIP": Decimal("0.00"),
    "RESPITE": Decimal("0.00"),
}


def to_money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def get_rate_for_loc(loc: str, rate_schedule: dict | None = None) -> Decimal:
    schedule = rate_schedule or DEFAULT_RATE_SCHEDULE
    raw = schedule.get(loc, Decimal("0.00"))

    if isinstance(raw, Decimal):
        return raw

    return Decimal(str(raw))


def build_revenue_summary(
    loc_summary: dict,
    rate_schedule: dict | None = None,
) -> dict:
    """
    Returns money summary by LOC.
    Assumes daily rates for RHC / GIP / RESPITE.
    Continuous Care can later be converted to hourly calculation;
    for now it uses configured loc rate * day count unless specialized
    payer logic is added.
    """
    rate_schedule = rate_schedule or DEFAULT_RATE_SCHEDULE

    revenue_rows = []

    loc_keys = [
        ("ROUTINE", loc_summary.get("routine_days", 0)),
        ("GIP", loc_summary.get("gip_days", 0)),
        ("RESPITE", loc_summary.get("respite_days", 0)),
        ("CONTINUOUS CARE", loc_summary.get("continuous_care_days", 0)),
    ]

    total = Decimal("0.00")

    for loc, days in loc_keys:
        rate = get_rate_for_loc(loc, rate_schedule)
        amount = rate * Decimal(days)
        total += amount

        revenue_rows.append(
            {
                "loc": loc,
                "days": days,
                "revenue_code": LOC_TO_REVENUE_CODE.get(loc),
                "rate": to_money(rate),
                "amount": to_money(amount),
            }
        )

    return {
        "rows": revenue_rows,
        "total_estimated_amount": to_money(total),
    }


def build_revenue_summary_from_claim_lines(claim_lines: list[dict]) -> dict:
    """
    Real-CMS-rate revenue summary, built directly from the (already
    tier/FY-split) claim lines produced by claim_segment_service, so the
    dollar total always matches what would actually be billed on the 837I.

    Falls back gracefully: if claim_lines carry no real rate info (legacy
    $0.00 path), this still produces a correct $0.00 total.

    If any claim line carries a `rate_gap_reason` (a period this tenant's
    CMS-rate configuration couldn't price, e.g. a fiscal year or CBSA wage
    index not yet on file), it is surfaced in both the row and a top-level
    `has_rate_gaps` flag -- this total should NOT be treated as the real
    billable amount until those gaps are resolved.
    """
    revenue_rows = []
    total = Decimal("0.00")
    has_rate_gaps = False

    for line in claim_lines:
        loc = line["loc"]
        days = line["days"]
        rate = Decimal(str(line["rate"]))
        amount = rate * Decimal(days)
        total += amount

        rate_gap_reason = line.get("rate_gap_reason")
        if rate_gap_reason:
            has_rate_gaps = True

        revenue_rows.append(
            {
                "loc": loc,
                "days": days,
                "revenue_code": line.get("revenue_code") or LOC_TO_REVENUE_CODE.get(loc),
                "rate": to_money(rate),
                "amount": to_money(amount),
                "from_date": line.get("from_date"),
                "to_date": line.get("to_date"),
                "fiscal_year": line.get("fiscal_year"),
                "rhc_day_tier": line.get("rhc_day_tier"),
                "rate_gap_reason": rate_gap_reason,
            }
        )

    return {
        "rows": revenue_rows,
        "total_estimated_amount": to_money(total),
        "has_rate_gaps": has_rate_gaps,
    }