# backend/tests/test_sia_service.py
"""
Tests the Service Intensity Add-on (SIA) calculator against the documented
CMS formula (42 CFR 418.302 / Claims Processing Manual Ch. 11):
    SIA = CHC hourly rate x (RN+MSW minutes that day / 60), capped at 4
    hours/day, RHC days only, last 7 days of life.

No real Kessler (or other patient) remit reviewed this session has
included an SIA line item yet, so this validates the formula mechanics
and CMS rules (day window, discipline eligibility, RHC-only, 4-hour cap,
missing-timestamp handling) rather than a real paid dollar amount. Flag
for reconciliation the same way RHC rates were, if/when a real SIA remit
line surfaces.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.billing.services.sia_service import (
    SIA_MAX_MINUTES_PER_DAY,
    compute_sia_schedule,
    get_date_of_death,
    visit_minutes,
)


class _FakePatient:
    def __init__(self, status, discharge_date):
        self.status = status
        self.discharge_date = discharge_date


def test_date_of_death_only_for_deceased_patients():
    active = _FakePatient("ACTIVE", date(2026, 2, 10))
    assert get_date_of_death(active) is None

    deceased = _FakePatient("DECEASED", date(2026, 2, 10))
    assert get_date_of_death(deceased) == date(2026, 2, 10)

    discharged = _FakePatient("DISCHARGED", date(2026, 2, 10))
    assert get_date_of_death(discharged) is None


def test_visit_minutes_computed_from_real_timestamps():
    start = datetime(2026, 2, 1, 9, 0, tzinfo=timezone.utc)
    end = datetime(2026, 2, 1, 10, 30, tzinfo=timezone.utc)
    assert visit_minutes(start, end) == 90


def test_visit_minutes_zero_when_timestamps_missing():
    # No fabricated default duration for an unmeasured visit.
    assert visit_minutes(None, None) == 0
    assert visit_minutes(datetime(2026, 2, 1, 9, 0), None) == 0


def test_sia_window_is_last_7_days_of_life_and_rhc_only():
    dod = date(2026, 2, 10)
    loc_by_date = {dod - timedelta(days=i): "ROUTINE" for i in range(7)}
    # Day 8 back is GIP -- outside SIA's RHC-only eligibility even though
    # it would otherwise be within a wider window.
    loc_by_date[dod - timedelta(days=7)] = "GIP"

    visits = [
        {
            "visit_date": str(dod),
            "visit_discipline": "RN",
            "status": "FINALIZED",
            "start_time": datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc),
            "end_time": datetime(2026, 2, 10, 10, 0, tzinfo=timezone.utc),
        }
    ]

    result = compute_sia_schedule(
        date_of_death=dod,
        loc_by_date=loc_by_date,
        visits=visits,
        cbsa_code="40140",
    )

    assert len(result["days"]) == 7
    assert result["window_start"] == dod - timedelta(days=6)
    day_of_death_row = next(d for d in result["days"] if d["date"] == dod)
    assert day_of_death_row["eligible"] is True
    assert day_of_death_row["capped_minutes"] == 60
    assert Decimal(day_of_death_row["amount"]) > Decimal("0.00")


def test_sia_excludes_non_rn_msw_disciplines():
    dod = date(2026, 2, 10)
    loc_by_date = {dod: "ROUTINE"}
    visits = [
        {
            "visit_date": str(dod),
            "visit_discipline": "AIDE",  # not eligible for SIA
            "status": "FINALIZED",
            "start_time": datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc),
            "end_time": datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc),
        }
    ]
    result = compute_sia_schedule(
        date_of_death=dod, loc_by_date=loc_by_date, visits=visits, cbsa_code="40140"
    )
    day_row = next(d for d in result["days"] if d["date"] == dod)
    assert day_row["raw_minutes"] == 0
    assert day_row["amount"] == "0.00"


def test_sia_excludes_non_finalized_visits():
    dod = date(2026, 2, 10)
    loc_by_date = {dod: "ROUTINE"}
    visits = [
        {
            "visit_date": str(dod),
            "visit_discipline": "RN",
            "status": "DRAFT",  # not finalized yet
            "start_time": datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc),
            "end_time": datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc),
        }
    ]
    result = compute_sia_schedule(
        date_of_death=dod, loc_by_date=loc_by_date, visits=visits, cbsa_code="40140"
    )
    day_row = next(d for d in result["days"] if d["date"] == dod)
    assert day_row["raw_minutes"] == 0


def test_sia_caps_combined_rn_plus_msw_minutes_at_four_hours():
    dod = date(2026, 2, 10)
    loc_by_date = {dod: "ROUTINE"}
    visits = [
        {
            "visit_date": str(dod),
            "visit_discipline": "RN",
            "status": "FINALIZED",
            "start_time": datetime(2026, 2, 10, 8, 0, tzinfo=timezone.utc),
            "end_time": datetime(2026, 2, 10, 11, 0, tzinfo=timezone.utc),  # 180 min
        },
        {
            "visit_date": str(dod),
            "visit_discipline": "SW",
            "status": "FINALIZED",
            "start_time": datetime(2026, 2, 10, 13, 0, tzinfo=timezone.utc),
            "end_time": datetime(2026, 2, 10, 15, 0, tzinfo=timezone.utc),  # 120 min
        },
    ]
    result = compute_sia_schedule(
        date_of_death=dod, loc_by_date=loc_by_date, visits=visits, cbsa_code="40140"
    )
    day_row = next(d for d in result["days"] if d["date"] == dod)
    assert day_row["raw_minutes"] == 300  # 180 + 120, before capping
    assert day_row["capped_minutes"] == SIA_MAX_MINUTES_PER_DAY  # capped to 240
