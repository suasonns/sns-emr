from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.billing.services.cms_rate_service import (
    CmsRateError,
    split_loc_range_into_rate_periods,
)


class ClaimSegmentError(RuntimeError):
    pass


def _inclusive_days(start_date: date, end_date: date) -> int:
    return (end_date - start_date).days + 1


def build_claim_lines(
    loc_segments: list[dict],
    rate_schedule: dict | None = None,
    *,
    cbsa_code: str | None = None,
    election_anchor_date: date | None = None,
) -> list[dict]:
    """
    Converts LOC segments into claim-level billing lines.

    When `cbsa_code` (and, for ROUTINE, `election_anchor_date`) are
    provided, real CMS wage-adjusted per-diem rates are used, and a segment
    is split into multiple claim lines wherever it crosses an RHC day-tier
    boundary (day 60/61) or a federal fiscal-year boundary (Oct 1) -- both
    of which change the per-diem rate mid-segment, as confirmed by real
    Kessler remittances this session.

    Falls back to the legacy flat `rate_schedule` lookup (or $0.00) ONLY
    when no CMS-rate inputs are configured at all (cbsa_code is None). If
    a tenant HAS opted into real CMS rates but a specific period can't be
    priced (e.g. an unpopulated fiscal year or missing CBSA wage index),
    this does NOT silently produce a $0.00 line -- that would look
    identical to an intentionally-unconfigured tenant and hide real,
    uncollected revenue. Instead each such line is flagged with
    `rate_gap_reason` so callers (billing_engine) can surface it instead of
    quietly under-billing.
    """

    if not loc_segments:
        return []

    claim_lines: list[dict] = []

    for segment in loc_segments:
        start_date = segment["start_date"]
        end_date = segment["end_date"]
        loc = segment["loc"]
        pos = segment["pos"]

        if not start_date or not end_date or not loc:
            continue

        use_cms_rates = cbsa_code and (loc != "ROUTINE" or election_anchor_date)

        rate_gap_reason = None
        rate_periods = None

        if use_cms_rates:
            try:
                rate_periods = split_loc_range_into_rate_periods(
                    loc=loc,
                    start_date=start_date,
                    end_date=end_date,
                    cbsa_code=cbsa_code,
                    election_anchor_date=election_anchor_date,
                )
            except CmsRateError as exc:
                rate_periods = None
                rate_gap_reason = str(exc)
        elif cbsa_code and loc == "ROUTINE" and not election_anchor_date:
            # Tenant has real CMS rates on, but this patient has no election
            # anchor on file -- ROUTINE can't be tiered without one.
            rate_gap_reason = (
                "No election anchor date on file for this patient; RHC "
                "day-tier cannot be determined. Ensure a period_number=1 "
                "benefit period exists."
            )

        if rate_periods is not None:
            for period in rate_periods:
                amount = period["rate"] * Decimal(period["days"])
                claim_lines.append(
                    {
                        "from_date": str(period["start_date"]),
                        "to_date": str(period["end_date"]),
                        "days": period["days"],
                        "loc": loc,
                        "pos": pos,
                        "facility_name": segment.get("facility_name"),
                        "revenue_code": _map_revenue_code(loc),
                        "rate": str(period["rate"]),
                        "estimated_amount": str(amount),
                        "fiscal_year": period["fiscal_year"],
                        "rhc_day_tier": period["tier"],
                        "rate_gap_reason": None,
                    }
                )
            continue

        days = _inclusive_days(start_date, end_date)

        # ✅ Safe default rate handling (legacy flat schedule / $0.00) --
        # only reached for tenants with no CBSA configured, or for a
        # specific period this tenant's CMS-rate config can't yet price
        # (rate_gap_reason will be set in the latter case).
        rate = Decimal("0.00")
        if rate_schedule and loc in rate_schedule:
            rate = Decimal(str(rate_schedule[loc]))

        amount = rate * Decimal(days)

        claim_lines.append(
            {
                "from_date": str(start_date),
                "to_date": str(end_date),
                "days": days,
                "loc": loc,
                "pos": pos,
                "facility_name": segment.get("facility_name"),
                "revenue_code": _map_revenue_code(loc),
                "rate": str(rate),
                "estimated_amount": str(amount),
                "fiscal_year": None,
                "rhc_day_tier": None,
                "rate_gap_reason": rate_gap_reason,
            }
        )

    return claim_lines


def _map_revenue_code(loc: str) -> str | None:
    """
    Basic hospice revenue code mapping (STRUCTURE ONLY)
    """

    mapping = {
        "ROUTINE": "0651",
        "CONTINUOUS CARE": "0652",
        "RESPITE": "0655",
        "GIP": "0656",
    }

    return mapping.get(loc)
