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