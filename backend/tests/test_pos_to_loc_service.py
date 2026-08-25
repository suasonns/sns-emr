"""
Tests for app.billing.services.pos_to_loc_service, focused on the CMS
5-consecutive-day inpatient respite cap (42 CFR 418.204): day 6+ of a
single respite occurrence must resolve to the POS default LOC (typically
ROUTINE), not RESPITE.
"""

from __future__ import annotations

from datetime import date

from app.billing.services.pos_to_loc_service import (
    DateRangeEvent,
    RESPITE_MAX_CONSECUTIVE_DAYS,
    build_loc_timeline,
    build_pos_timeline,
    cap_respite_events,
    resolve_loc_for_day,
)


class _FakePosRecord:
    def __init__(self, effective_date, end_date, pos_type, facility_name=None):
        self.effective_date = effective_date
        self.end_date = end_date
        self.pos_type = pos_type
        self.facility_name = facility_name


def test_cap_respite_events_truncates_long_occurrence():
    long_event = DateRangeEvent(
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 10),  # 10-day occurrence, way over the 5-day cap
        reason="family caregiver break",
    )

    capped = cap_respite_events([long_event])

    assert len(capped) == 1
    assert capped[0].start_date == date(2026, 5, 1)
    assert capped[0].end_date == date(2026, 5, 5)
    assert (capped[0].end_date - capped[0].start_date).days + 1 == RESPITE_MAX_CONSECUTIVE_DAYS


def test_cap_respite_events_leaves_short_occurrence_untouched():
    short_event = DateRangeEvent(
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 3),  # 3 days, under the cap
    )

    capped = cap_respite_events([short_event])

    assert capped == [short_event]


def test_resolve_loc_for_day_bills_overage_days_as_routine_default():
    # A 10-day HOME respite occurrence: days 1-5 should resolve to RESPITE,
    # days 6-10 should fall through to the POS default (ROUTINE for HOME).
    respite_events = [
        DateRangeEvent(start_date=date(2026, 5, 1), end_date=date(2026, 5, 10))
    ]
    capped = cap_respite_events(respite_events)

    for day_offset in range(10):
        day = date(2026, 5, 1 + day_offset)
        loc = resolve_loc_for_day(
            day=day,
            pos_type="HOME",
            gip_events=[],
            respite_events=capped,
            continuous_events=[],
        )
        if day_offset < RESPITE_MAX_CONSECUTIVE_DAYS:
            assert loc == "RESPITE", f"day {day_offset + 1} should still be RESPITE"
        else:
            assert loc == "ROUTINE", f"day {day_offset + 1} should have rolled to ROUTINE"


def test_build_loc_timeline_applies_respite_cap_end_to_end():
    start_date = date(2026, 5, 1)
    end_date = date(2026, 5, 10)

    pos_records = [_FakePosRecord(start_date, end_date, "HOME")]
    pos_timeline = build_pos_timeline(pos_records, start_date, end_date)

    respite_events = [DateRangeEvent(start_date=start_date, end_date=end_date)]

    loc_timeline = build_loc_timeline(
        pos_timeline=pos_timeline,
        gip_events=[],
        respite_events=respite_events,
        continuous_events=[],
    )

    resolved_locs = [row["loc"] for row in loc_timeline]
    assert resolved_locs[:5] == ["RESPITE"] * 5
    assert resolved_locs[5:] == ["ROUTINE"] * 5


def test_gip_still_takes_priority_over_capped_respite_overage_days():
    # If GIP overlaps the overage days of a long respite occurrence, GIP
    # should still win (priority order is unaffected by the respite cap).
    respite_events = [
        DateRangeEvent(start_date=date(2026, 5, 1), end_date=date(2026, 5, 10))
    ]
    gip_events = [DateRangeEvent(start_date=date(2026, 5, 6), end_date=date(2026, 5, 8))]
    capped = cap_respite_events(respite_events)

    loc_day_6 = resolve_loc_for_day(
        day=date(2026, 5, 6),
        pos_type="HOME",
        gip_events=gip_events,
        respite_events=capped,
        continuous_events=[],
    )
    assert loc_day_6 == "GIP"
