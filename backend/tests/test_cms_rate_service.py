# backend/tests/test_cms_rate_service.py
"""
Regression tests for cms_rate_service, validated against REAL, CMS-paid
Kessler remittance advices (not fabricated numbers). See
app/billing/services/cms_rate_service.py module docstring for full
provenance of each figure asserted here.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.billing.services.cms_rate_service import (
    CmsRateError,
    get_rhc_rate_for_day,
    split_loc_range_into_rate_periods,
)

CBSA_40140 = "40140"  # Riverside-San Bernardino-Ontario, CA

# Margaret Kessler's real, continuous hospice election start date
# (BP1 start_date / election_date, per her real chart).
KESSLER_ELECTION_ANCHOR = date(2025, 6, 16)


def test_september_2025_is_pure_tier_61_plus_and_matches_real_remit():
    """
    KESSLER 2 remit (paid 10/28/2025): DOS 09/01/25-09/30/25, TOB 813,
    allowed = $10,350.00 - $4,306.40 = $6,043.60 for 30 days
    -> real per-day allowed rate = $201.4533/day.
    """
    rate = get_rhc_rate_for_day(
        as_of=date(2025, 9, 15),
        cumulative_election_day=(date(2025, 9, 15) - KESSLER_ELECTION_ANCHOR).days + 1,
        cbsa_code=CBSA_40140,
    )
    assert rate == Decimal("201.45")


def test_october_2025_is_fy2026_pure_tier_61_plus_and_matches_real_remit():
    """
    KESSLER 3 remit (paid 12/01/2025): DOS 10/01/25-10/31/25, TOB 813,
    allowed = $10,634.75 - $4,346.90 = $6,287.85 for 31 days
    -> real per-day allowed rate = $202.8339/day. Oct 1 crosses into FY2026,
    which uses a different (lower) base rate than FY2025 despite the
    patient staying in the same 61+ tier the whole month.
    """
    rate = get_rhc_rate_for_day(
        as_of=date(2025, 10, 15),
        cumulative_election_day=(date(2025, 10, 15) - KESSLER_ELECTION_ANCHOR).days + 1,
        cbsa_code=CBSA_40140,
    )
    assert rate == Decimal("202.83")


def test_february_2026_matches_real_remit_80():
    """
    Remit_80 (Feb 2026): 28 days, allowed $5,679.35 -> $202.83/day.
    Same FY2026 tier-61+ rate as October -- confirms consistency across
    two independent real remittances four months apart.
    """
    rate = get_rhc_rate_for_day(
        as_of=date(2026, 2, 15),
        cumulative_election_day=(date(2026, 2, 15) - KESSLER_ELECTION_ANCHOR).days + 1,
        cbsa_code=CBSA_40140,
    )
    assert rate == Decimal("202.83")


def test_august_2025_splits_at_real_cumulative_day_60_boundary():
    """
    KESSLER 1 remit (paid 09/30/2025): DOS 08/01/25-08/31/25, TOB 813,
    allowed = $10,550.24 - $3,544.79 = $7,005.45 for 31 days.

    Cumulative election day 60 (from anchor 6/16/25) falls on 8/14/25, so
    August must split into 14 tier-1 days (8/1-8/14) + 17 tier-2 days
    (8/15-8/31). The blended total this produces should match the real
    paid amount within CMS per-diem rounding tolerance (<0.3%).
    """
    periods = split_loc_range_into_rate_periods(
        loc="ROUTINE",
        start_date=date(2025, 8, 1),
        end_date=date(2025, 8, 31),
        cbsa_code=CBSA_40140,
        election_anchor_date=KESSLER_ELECTION_ANCHOR,
    )

    assert len(periods) == 2
    tier1, tier2 = periods

    assert tier1["tier"] == "1-60"
    assert tier1["days"] == 14
    assert tier1["start_date"] == date(2025, 8, 1)
    assert tier1["end_date"] == date(2025, 8, 14)

    assert tier2["tier"] == "61+"
    assert tier2["days"] == 17
    assert tier2["start_date"] == date(2025, 8, 15)
    assert tier2["end_date"] == date(2025, 8, 31)

    total = (tier1["rate"] * tier1["days"]) + (tier2["rate"] * tier2["days"])
    real_paid_allowed = Decimal("7005.45")

    diff_pct = abs(total - real_paid_allowed) / real_paid_allowed
    assert diff_pct < Decimal("0.003"), (
        f"Computed blended August total {total} deviates from real paid "
        f"allowed amount {real_paid_allowed} by more than 0.3%"
    )


def test_september_split_across_benefit_periods_stays_pure_tier_61_plus():
    """
    Confirms the RHC day tier is cumulative across the whole continuous
    election, NOT reset per benefit period: Kessler's BP1 ends 9/13/25 and
    BP2 starts 9/14/25, right in the middle of the September cycle, yet
    the entire month prices at the 61+ tier (single rate period, no split
    at the benefit-period boundary).
    """
    periods = split_loc_range_into_rate_periods(
        loc="ROUTINE",
        start_date=date(2025, 9, 1),
        end_date=date(2025, 9, 30),
        cbsa_code=CBSA_40140,
        election_anchor_date=KESSLER_ELECTION_ANCHOR,
    )

    assert len(periods) == 1
    assert periods[0]["tier"] == "61+"
    assert periods[0]["days"] == 30


def test_missing_cbsa_code_raises_instead_of_guessing():
    with pytest.raises(CmsRateError):
        get_rhc_rate_for_day(
            as_of=date(2026, 1, 1),
            cumulative_election_day=90,
            cbsa_code=None,
        )


def test_missing_election_anchor_raises_for_routine_loc():
    with pytest.raises(CmsRateError):
        split_loc_range_into_rate_periods(
            loc="ROUTINE",
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 31),
            cbsa_code=CBSA_40140,
            election_anchor_date=None,
        )
