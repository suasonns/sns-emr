"""
Tests for app.billing.services.election_addendum_service -- the real
CMS Election Statement Addendum 5-day/72-hour timeliness rule.
"""

from __future__ import annotations

from datetime import date

from app.billing.services.election_addendum_service import compute_addendum_compliance


def test_within_5_days_of_election_gets_5_day_deadline():
    result = compute_addendum_compliance(
        election_date=date(2026, 8, 1),
        requested_date=date(2026, 8, 3),
        delivered_date=date(2026, 8, 6),
    )
    assert result.deadline_days == 5
    assert result.deadline_date == date(2026, 8, 8)
    assert result.is_late is False
    assert result.is_satisfied is True


def test_after_5_days_of_election_gets_72_hour_deadline():
    result = compute_addendum_compliance(
        election_date=date(2026, 8, 1),
        requested_date=date(2026, 9, 1),
        delivered_date=date(2026, 9, 3),
    )
    assert result.deadline_days == 3
    assert result.deadline_date == date(2026, 9, 4)
    assert result.is_late is False


def test_late_delivery_flagged():
    result = compute_addendum_compliance(
        election_date=date(2026, 8, 1),
        requested_date=date(2026, 9, 1),
        delivered_date=date(2026, 9, 10),
    )
    assert result.is_satisfied is True
    assert result.is_late is True
    assert "after the 3-day deadline" in result.reason


def test_not_yet_delivered_and_past_deadline_is_late():
    result = compute_addendum_compliance(
        election_date=date(2026, 8, 1),
        requested_date=date(2026, 9, 1),
        delivered_date=None,
        as_of_date=date(2026, 9, 10),
    )
    assert result.is_satisfied is False
    assert result.is_late is True


def test_not_yet_delivered_but_still_within_deadline_is_pending_not_late():
    result = compute_addendum_compliance(
        election_date=date(2026, 8, 1),
        requested_date=date(2026, 9, 1),
        delivered_date=None,
        as_of_date=date(2026, 9, 2),
    )
    assert result.is_satisfied is False
    assert result.is_late is False


def test_early_discharge_before_deadline_waives_requirement():
    result = compute_addendum_compliance(
        election_date=date(2026, 8, 1),
        requested_date=date(2026, 9, 1),
        delivered_date=None,
        discharge_or_death_date=date(2026, 9, 3),
    )
    assert result.is_satisfied is True
    assert result.is_late is False
    assert result.is_waived_by_early_discharge is True


def test_discharge_after_deadline_does_not_waive_late_addendum():
    result = compute_addendum_compliance(
        election_date=date(2026, 8, 1),
        requested_date=date(2026, 9, 1),
        delivered_date=None,
        discharge_or_death_date=date(2026, 9, 20),
        as_of_date=date(2026, 9, 20),
    )
    assert result.is_satisfied is False
    assert result.is_late is True
    assert result.is_waived_by_early_discharge is False


def test_documented_not_required_reason_waives_requirement():
    result = compute_addendum_compliance(
        election_date=date(2026, 8, 1),
        requested_date=date(2026, 9, 1),
        delivered_date=None,
        not_required_reason="Request withdrawn in writing by representative",
    )
    assert result.is_satisfied is True
    assert result.is_late is False
    assert "Requirement waived" in result.reason
