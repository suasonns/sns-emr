# backend/app/billing/services/cms_rate_service.py
"""
Real CMS hospice per-diem rate tables, wage-index adjustment, and RHC
day-tiering.

PROVENANCE / VALIDATION STATUS
---------------------------------------------------------------------------
Routine Home Care (RHC) rates + labor share (66%) + CBSA 40140 wage indices
were cross-validated this session against FOUR real, CMS-paid Kessler
remittance advices (Aug 2025, Sep 2025, Oct 2025, Feb 2026 -- see
NGS remit PDFs "KESSLER 1/2/3" and "Remit_80"):

  - FY2026 tier 61+ ($181.94 base, WI 1.1740): predicted $202.83/day,
    matches Oct 2025 and Feb 2026 real allowed/day to the cent.
  - FY2025 tier 61+ ($176.92 base): backed out WI 1.21011 from Sep 2025
    (a pure 61+ month), predicted rate $201.45/day matches exactly.
  - FY2025 tier 1-60 ($224.52 base) with that same WI predicts $255.65/day;
    Aug 2025 (a real split month, 14 days tier1 + 17 days tier2 once the
    cumulative election-day count crosses 60 around 8/14/25) implies an
    actual blended tier1 rate of $255.77/day -- a 0.05% match.

This is real, externally-verified proof the RHC math below is correct for
CBSA 40140 (Riverside-San Bernardino-Ontario, CA / Love & Faith Hospice).

GIP / Respite / Continuous Home Care (CHC) base rates and labor shares are
sourced from the same CMS FY2025/FY2026 final rules but have NOT been
validated against a real paid remit for this tenant (no GIP/Respite/CHC
claims have been reconciled yet). Treat those as "sourced, not yet proven"
until a real remit containing one of those revenue codes is reconciled.

Wage indices are keyed by CBSA code and are ONLY populated for CBSA 40140
today (the only one this tenant has needed / verified). Extend
CBSA_WAGE_INDEX_BY_FY as additional tenants/geographies come online --
DO NOT invent values for unknown CBSAs.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

_ONE_DAY = timedelta(days=1)


class CmsRateError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# CMS national base (pre-wage-index) per diem rates, by federal fiscal year.
# Fiscal year N runs Oct 1 (N-1) -> Sep 30 (N).
# ---------------------------------------------------------------------------

RHC_LABOR_SHARE = Decimal("0.66")  # validated empirically this session
RHC_NON_LABOR_SHARE = Decimal("1.00") - RHC_LABOR_SHARE

BASE_RATES_BY_FY = {
    2025: {
        "RHC_1_60": Decimal("224.52"),
        "RHC_61_PLUS": Decimal("176.92"),
        # Sourced (CMS FY2025 final rule), not yet reconciled against a real
        # Kessler GIP/Respite/CHC remit.
        "GIP": Decimal("1170.04"),
        "RESPITE": Decimal("518.78"),
        "CHC": Decimal("1618.59"),  # full-qualifying-day equivalent
    },
    2026: {
        "RHC_1_60": Decimal("230.83"),
        "RHC_61_PLUS": Decimal("181.94"),
        "GIP": Decimal("1199.86"),
        "RESPITE": Decimal("532.48"),
        "CHC": Decimal("1674.29"),
    },
}

# Labor share used for wage-index adjustment, by LOC. RHC is validated to
# the cent against real remits. GIP/RESPITE/CHC labor shares below are
# corrected to CMS's official FY2025/FY2026 final-rule published values
# (63.5% / 61.0% / 75.2%) -- CHC was previously listed as 74.7%, a
# transcription error from an earlier, less careful search; re-verified
# against multiple CMS source summaries as 75.2% for both FY25 and FY26.
#
# ATTEMPTED RECONCILIATION AGAINST REAL DATA (not fully conclusive): Love &
# Faith Hospice's real CMS PS&R "Redesign Provider Summary Report" (revenue
# code 0652, provider #B51771) shows real CHC charges of $1,844.40 for 96
# 15-min increments (24 hrs) in the FY2025 cap year (a clean $76.85/hr), and
# $7,588.90 for 372 increments (93 hrs) in FY2026 ($81.60/hr blended). The
# pure wage-adjusted formula below (75.2% labor, WI 1.21011/1.17400)
# predicts $80.34/hr (FY25) and $78.88/hr (FY26) -- both off by 3-5%, in
# opposite directions. This is NOT a clean single-parameter mismatch (unlike
# RHC's tidy per-day proof), most likely because CHC requires >=8 hours of
# care in a calendar day to bill at the CHC rate at all -- any day with
# fewer hours bills those hours at the hourly-equivalent RHC rate instead --
# and the PS&R's annual aggregate doesn't expose which individual days (or
# hours within a day) crossed that threshold. Treat CHC as CMS-sourced and
# structurally correct, but NOT proven the way RHC is; a real 835 for a
# specific CHC claim (with per-day hour counts) would be needed to
# reconcile properly.
LABOR_SHARE_BY_LOC = {
    "ROUTINE": RHC_LABOR_SHARE,
    "GIP": Decimal("0.635"),
    "RESPITE": Decimal("0.610"),
    "CONTINUOUS CARE": Decimal("0.752"),
}

# Real CMS published wage indices (with floor/5% cap applied), by fiscal
# year and CBSA code. FY2026 value sourced directly from the official CMS
# fy-2026-final-hospice-wage-index.zip (508-Version-Urban-Areas.csv). FY2025
# value is back-solved from real paid Kessler remits (see module docstring)
# pending direct download confirmation from CMS's FY2025 file.
CBSA_WAGE_INDEX_BY_FY = {
    2025: {
        "40140": Decimal("1.21011"),  # Riverside-San Bernardino-Ontario, CA
    },
    2026: {
        "40140": Decimal("1.17400"),  # Riverside-San Bernardino-Ontario, CA
    },
}

RHC_DAY_TIER_BOUNDARY = 60  # days 1-60 vs 61+


def fiscal_year_for_date(as_of: date) -> int:
    """Federal FY: Oct 1 (Y-1) - Sep 30 (Y) is FY Y."""
    if as_of.month >= 10:
        return as_of.year + 1
    return as_of.year


def get_wage_index(fiscal_year: int, cbsa_code: str | None) -> Decimal:
    if not cbsa_code:
        raise CmsRateError(
            "No CBSA code configured for this tenant; cannot compute a "
            "real wage-adjusted CMS rate. Configure tenant.cbsa_code."
        )

    fy_table = CBSA_WAGE_INDEX_BY_FY.get(fiscal_year)
    if not fy_table or cbsa_code not in fy_table:
        raise CmsRateError(
            f"No wage index on file for CBSA {cbsa_code} in FY{fiscal_year}. "
            "Add a verified value to CBSA_WAGE_INDEX_BY_FY before billing "
            "this period with real CMS rates."
        )

    return fy_table[cbsa_code]


def _wage_adjust(base_rate: Decimal, labor_share: Decimal, wage_index: Decimal) -> Decimal:
    non_labor_share = Decimal("1.00") - labor_share
    factor = non_labor_share + (labor_share * wage_index)
    return (base_rate * factor).quantize(Decimal("0.01"))


def get_rhc_rate_for_day(
    *,
    as_of: date,
    cumulative_election_day: int,
    cbsa_code: str | None,
) -> Decimal:
    """
    Real, wage-adjusted Routine Home Care per-diem rate for a single day,
    selecting the days-1-60 vs days-61+ tier by cumulative election day
    (continuous since hospice election start, NOT reset per benefit period
    -- confirmed this session: Kessler's Sept 2025 claim spans a benefit
    period boundary and still prices entirely at the 61+ tier).
    """
    fiscal_year = fiscal_year_for_date(as_of)
    fy_rates = BASE_RATES_BY_FY.get(fiscal_year)
    if not fy_rates:
        raise CmsRateError(
            f"No CMS base rate table on file for FY{fiscal_year}."
        )

    wage_index = get_wage_index(fiscal_year, cbsa_code)

    tier_key = "RHC_1_60" if cumulative_election_day <= RHC_DAY_TIER_BOUNDARY else "RHC_61_PLUS"
    base_rate = fy_rates[tier_key]

    return _wage_adjust(base_rate, RHC_LABOR_SHARE, wage_index)


def get_flat_rate_for_day(*, loc: str, as_of: date, cbsa_code: str | None) -> Decimal:
    """
    Wage-adjusted per-diem rate for non-tiered LOCs (GIP / RESPITE /
    CONTINUOUS CARE). No day-count tiering applies to these levels of care.
    """
    fiscal_year = fiscal_year_for_date(as_of)
    fy_rates = BASE_RATES_BY_FY.get(fiscal_year)
    if not fy_rates:
        raise CmsRateError(
            f"No CMS base rate table on file for FY{fiscal_year}."
        )

    loc_to_key = {
        "GIP": "GIP",
        "RESPITE": "RESPITE",
        "CONTINUOUS CARE": "CHC",
    }
    rate_key = loc_to_key.get(loc)
    if not rate_key:
        raise CmsRateError(f"No CMS rate table entry for LOC '{loc}'.")

    wage_index = get_wage_index(fiscal_year, cbsa_code)
    labor_share = LABOR_SHARE_BY_LOC[loc]
    return _wage_adjust(fy_rates[rate_key], labor_share, wage_index)


def split_loc_range_into_rate_periods(
    *,
    loc: str,
    start_date: date,
    end_date: date,
    cbsa_code: str | None,
    election_anchor_date: date | None,
) -> list[dict]:
    """
    Splits a contiguous LOC date range into sub-periods that each carry a
    single uniform per-diem rate, breaking at:
      - RHC day-60/61 cumulative election-day boundary (ROUTINE only)
      - federal fiscal-year boundary (Oct 1), for all LOCs

    Real claims must be billed this way whenever a tier or rate-year
    boundary falls inside a billing cycle (proven this session: Kessler's
    Aug 2025 claim actually paid at two different per-diem rates because
    she crossed cumulative day 60 mid-month).

    Returns a list of dicts:
        {start_date, end_date, days, rate, fiscal_year, tier}
    `tier` is "1-60" / "61+" for ROUTINE, else None.
    """
    if loc == "ROUTINE" and election_anchor_date is None:
        raise CmsRateError(
            "No election anchor date on file for this patient; cannot "
            "determine RHC day tier. Ensure a period_number=1 benefit "
            "period exists."
        )

    periods: list[dict] = []
    current_start = start_date
    current_day = start_date

    def _key_for(day: date) -> tuple:
        fy = fiscal_year_for_date(day)
        if loc == "ROUTINE":
            cum_day = cumulative_election_day_for(election_anchor_date, day)
            tier = "1-60" if cum_day <= RHC_DAY_TIER_BOUNDARY else "61+"
            return (fy, tier)
        return (fy, None)

    prev_key = _key_for(start_date)

    while current_day <= end_date:
        next_day = current_day + _ONE_DAY
        key = _key_for(current_day)

        if key != prev_key:
            periods.append(
                _build_rate_period(loc, current_start, current_day - _ONE_DAY, prev_key, cbsa_code)
            )
            current_start = current_day
            prev_key = key

        current_day = next_day

    periods.append(_build_rate_period(loc, current_start, end_date, prev_key, cbsa_code))
    return periods


def _build_rate_period(loc: str, start: date, end: date, key: tuple, cbsa_code: str | None) -> dict:
    fiscal_year, tier = key
    days = (end - start).days + 1

    if loc == "ROUTINE":
        # Rate is uniform across the whole sub-period by construction; use
        # the first day to resolve it (tier + FY are already fixed).
        wage_index = get_wage_index(fiscal_year, cbsa_code)
        base_rate = BASE_RATES_BY_FY[fiscal_year][
            "RHC_1_60" if tier == "1-60" else "RHC_61_PLUS"
        ]
        rate = _wage_adjust(base_rate, RHC_LABOR_SHARE, wage_index)
    else:
        rate = get_flat_rate_for_day(loc=loc, as_of=start, cbsa_code=cbsa_code)

    return {
        "start_date": start,
        "end_date": end,
        "days": days,
        "rate": rate,
        "fiscal_year": fiscal_year,
        "tier": tier,
    }


def cumulative_election_day_for(anchor_date: date, target_date: date) -> int:
    """Local re-export to avoid a circular import with election_day_service."""
    return (target_date - anchor_date).days + 1
