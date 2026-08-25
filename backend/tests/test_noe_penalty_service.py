"""
Tests for app.billing.services.noe_penalty_service, the CMS late-NOE
(Notice of Election) non-covered-day penalty calculator (42 CFR 418.24(b)):
a NOE not filed within 5 calendar days of the election effective date makes
every day from election through the day before filing non-covered.
"""

from __future__ import annotations

from datetime import date

from app.billing.services.noe_penalty_service import (
    NoePenaltyError,
    apply_noe_penalty_to_claim_lines,
    compute_noe_penalty,
)

import pytest


def test_noe_filed_exactly_on_deadline_is_timely():
    election_date = date(2026, 5, 1)
    result = compute_noe_penalty(election_date, noe_submitted_date=date(2026, 5, 6))

    assert result.is_late is False
    assert result.non_covered_days == 0


def test_noe_filed_one_day_before_deadline_is_timely():
    election_date = date(2026, 5, 1)
    result = compute_noe_penalty(election_date, noe_submitted_date=date(2026, 5, 3))

    assert result.is_late is False


def test_noe_filed_one_day_late_penalizes_election_through_day_before_filing():
    election_date = date(2026, 5, 1)
    # Deadline is 5/6; filed 5/7 -> one day late.
    result = compute_noe_penalty(election_date, noe_submitted_date=date(2026, 5, 7))

    assert result.is_late is True
    assert result.is_exempt is False
    assert result.non_covered_start == date(2026, 5, 1)
    assert result.non_covered_end == date(2026, 5, 6)  # day before filing
    assert result.non_covered_days == 6


def test_cms_exception_waives_penalty_even_when_late():
    election_date = date(2026, 5, 1)
    result = compute_noe_penalty(
        election_date,
        noe_submitted_date=date(2026, 5, 20),
        exception_reason="MAC outage confirmed per CMS transmittal 12345",
    )

    assert result.is_late is False
    assert result.is_exempt is True
    assert result.non_covered_days == 0
    assert "MAC outage" in result.reason


def test_unfiled_noe_within_window_is_not_yet_late():
    election_date = date(2026, 5, 1)
    result = compute_noe_penalty(
        election_date,
        noe_submitted_date=None,
        as_of_date=date(2026, 5, 4),
    )

    assert result.is_late is False
    assert result.non_covered_days == 0


def test_unfiled_noe_past_deadline_is_late_and_growing():
    election_date = date(2026, 5, 1)
    result = compute_noe_penalty(
        election_date,
        noe_submitted_date=None,
        as_of_date=date(2026, 5, 10),
    )

    assert result.is_late is True
    assert result.non_covered_start == date(2026, 5, 1)
    assert result.non_covered_end == date(2026, 5, 9)
    assert result.non_covered_days == 9


def test_missing_election_date_raises():
    with pytest.raises(NoePenaltyError):
        compute_noe_penalty(None, noe_submitted_date=date(2026, 5, 1))


def test_apply_penalty_zeroes_and_flags_only_overlapping_claim_line_days():
    election_date = date(2026, 5, 1)
    penalty = compute_noe_penalty(election_date, noe_submitted_date=date(2026, 5, 10))
    assert penalty.non_covered_start == date(2026, 5, 1)
    assert penalty.non_covered_end == date(2026, 5, 9)

    claim_lines = [
        {
            "from_date": "2026-05-01",
            "to_date": "2026-05-15",
            "days": 15,
            "loc": "ROUTINE",
            "rate": "200.00",
            "estimated_amount": "3000.00",
            "rate_gap_reason": None,
        }
    ]

    result = apply_noe_penalty_to_claim_lines(claim_lines, penalty)

    # Split into: non-covered 5/1-5/9 ($0.00), covered 5/10-5/15 ($1200.00).
    assert len(result) == 2

    penalized = result[0]
    assert penalized["from_date"] == "2026-05-01"
    assert penalized["to_date"] == "2026-05-09"
    assert penalized["days"] == 9
    assert penalized["rate"] == "0.00"
    assert penalized["estimated_amount"] == "0.00"
    assert penalized["noe_penalty_reason"] is not None

    covered = result[1]
    assert covered["from_date"] == "2026-05-10"
    assert covered["to_date"] == "2026-05-15"
    assert covered["days"] == 6
    assert covered["rate"] == "200.00"
    assert covered["estimated_amount"] == "1200.00"


def test_apply_penalty_leaves_unaffected_lines_untouched():
    election_date = date(2026, 5, 1)
    penalty = compute_noe_penalty(election_date, noe_submitted_date=date(2026, 5, 3))
    assert penalty.is_late is False

    claim_lines = [
        {
            "from_date": "2026-05-01",
            "to_date": "2026-05-15",
            "days": 15,
            "loc": "ROUTINE",
            "rate": "200.00",
            "estimated_amount": "3000.00",
            "rate_gap_reason": None,
        }
    ]

    result = apply_noe_penalty_to_claim_lines(claim_lines, penalty)
    assert result == claim_lines


def test_apply_penalty_splits_line_that_starts_before_election_window():
    # A claim line spanning before, during, and after the non-covered
    # window should split into three pieces.
    election_date = date(2026, 5, 5)
    penalty = compute_noe_penalty(election_date, noe_submitted_date=date(2026, 5, 15))
    assert penalty.non_covered_start == date(2026, 5, 5)
    assert penalty.non_covered_end == date(2026, 5, 14)

    claim_lines = [
        {
            "from_date": "2026-05-01",
            "to_date": "2026-05-20",
            "days": 20,
            "loc": "ROUTINE",
            "rate": "200.00",
            "estimated_amount": "4000.00",
            "rate_gap_reason": None,
        }
    ]

    result = apply_noe_penalty_to_claim_lines(claim_lines, penalty)
    assert len(result) == 3

    before, penalized, after = result
    assert before["from_date"] == "2026-05-01"
    assert before["to_date"] == "2026-05-04"
    assert before["days"] == 4
    assert before["estimated_amount"] == "800.00"

    assert penalized["from_date"] == "2026-05-05"
    assert penalized["to_date"] == "2026-05-14"
    assert penalized["rate"] == "0.00"

    assert after["from_date"] == "2026-05-15"
    assert after["to_date"] == "2026-05-20"
    assert after["days"] == 6
    assert after["estimated_amount"] == "1200.00"
