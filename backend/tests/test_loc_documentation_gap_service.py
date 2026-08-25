"""
Tests for app.billing.services.loc_documentation_gap_service -- the real
GIP/Respite/CHC documentation-gap checks (audit-supportability, not the
respite 5-day rate cap which is enforced elsewhere).
"""

from __future__ import annotations

from datetime import date

from app.billing.services.loc_documentation_gap_service import (
    DateRangeEventLike,
    compute_loc_documentation_gaps,
)


def test_no_gaps_when_all_periods_documented_and_chc_meets_minimum():
    gip_events = [DateRangeEventLike(date(2026, 5, 1), date(2026, 5, 2), reason="Uncontrolled pain crisis")]
    respite_events = [DateRangeEventLike(date(2026, 5, 5), date(2026, 5, 6), reason="Caregiver hospitalization")]
    continuous_events = [DateRangeEventLike(date(2026, 5, 10), date(2026, 5, 10), reason="Actively dying, symptom crisis")]

    result = compute_loc_documentation_gaps(
        gip_events=gip_events,
        respite_events=respite_events,
        continuous_events=continuous_events,
        chc_minutes_by_date={date(2026, 5, 10): 500},
    )

    assert result.has_gaps is False
    assert result.reasons == []


def test_flags_gip_period_missing_reason():
    gip_events = [DateRangeEventLike(date(2026, 5, 1), date(2026, 5, 2), reason=None)]

    result = compute_loc_documentation_gaps(
        gip_events=gip_events,
        respite_events=[],
        continuous_events=[],
        chc_minutes_by_date={},
    )

    assert result.has_gaps is True
    assert "GIP period 2026-05-01-2026-05-02" in result.reasons[0]


def test_flags_respite_period_missing_reason():
    respite_events = [DateRangeEventLike(date(2026, 5, 5), date(2026, 5, 6), reason="   ")]

    result = compute_loc_documentation_gaps(
        gip_events=[],
        respite_events=respite_events,
        continuous_events=[],
        chc_minutes_by_date={},
    )

    assert result.has_gaps is True
    assert "Respite period" in result.reasons[0]


def test_flags_chc_day_under_8_hour_minimum():
    continuous_events = [DateRangeEventLike(date(2026, 5, 10), date(2026, 5, 10), reason="Symptom crisis")]

    result = compute_loc_documentation_gaps(
        gip_events=[],
        respite_events=[],
        continuous_events=continuous_events,
        chc_minutes_by_date={date(2026, 5, 10): 300},
    )

    assert result.has_gaps is True
    assert "CHC day 2026-05-10" in result.reasons[0]
    assert "5.0 documented direct-care" in result.reasons[0]


def test_flags_chc_day_with_zero_documented_minutes():
    continuous_events = [DateRangeEventLike(date(2026, 5, 10), date(2026, 5, 11), reason="Symptom crisis")]

    result = compute_loc_documentation_gaps(
        gip_events=[],
        respite_events=[],
        continuous_events=continuous_events,
        chc_minutes_by_date={date(2026, 5, 10): 500},  # 5/11 has no visits at all
    )

    assert result.has_gaps is True
    assert any("CHC day 2026-05-11" in r for r in result.reasons)
    assert not any("CHC day 2026-05-10" in r for r in result.reasons)
