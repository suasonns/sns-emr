# backend/app/services/election_day_service.py
"""
Cumulative hospice election day tracking.

CMS's Routine Home Care two-tier per-diem rate (days 1-60 vs days 61+) is
based on the cumulative count of days the patient has been under a
continuous hospice election -- NOT the day count within the current
benefit period. This was confirmed with real data this session: Margaret
Kessler's Sept 2025 claim (Remit_50 / "KESSLER 2") spans her BP1 -> BP2
boundary (9/13 -> 9/14/25) and still prices entirely at the 61+ tier,
which only holds if the day count carries over across benefit periods.

The "election anchor" is the start_date of the patient's first (INITIAL,
period_number == 1) benefit period. If the patient revokes and later
re-elects hospice, a new anchor would apply from the re-election date --
that scenario is not yet handled here (see TODO below) since no real
patient data has surfaced it yet.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.benefit_period import BenefitPeriod


def get_election_anchor_date(
    db: Session,
    *,
    tenant_id: str | UUID,
    patient_id: str | UUID,
) -> date | None:
    """
    Returns the start_date of the patient's earliest (period_number == 1)
    benefit period, i.e. the day their continuous hospice election began.
    Returns None if no benefit period is on file (caller should fall back
    to a safe default, e.g. $0.00 rate, rather than guessing).
    """
    anchor = db.execute(
        select(BenefitPeriod.start_date)
        .where(
            BenefitPeriod.tenant_id == tenant_id,
            BenefitPeriod.patient_id == patient_id,
            BenefitPeriod.period_number == 1,
        )
    ).scalar_one_or_none()

    if anchor is not None:
        return anchor

    # Fallback: no period_number==1 row found (e.g. backfilled patient) --
    # use the earliest start_date on file for that patient.
    return db.execute(
        select(BenefitPeriod.start_date)
        .where(
            BenefitPeriod.tenant_id == tenant_id,
            BenefitPeriod.patient_id == patient_id,
        )
        .order_by(BenefitPeriod.start_date.asc())
        .limit(1)
    ).scalar_one_or_none()


def cumulative_election_day(anchor_date: date, target_date: date) -> int:
    """
    1-indexed cumulative day number of continuous hospice care as of
    target_date, given the election anchor date (day of election = day 1).
    """
    if target_date < anchor_date:
        raise ValueError(
            f"target_date {target_date} is before election anchor {anchor_date}"
        )

    return (target_date - anchor_date).days + 1


def get_initial_election_noe_info(
    db: Session,
    *,
    tenant_id: str | UUID,
    patient_id: str | UUID,
) -> dict | None:
    """
    Returns the real election_date, noe_submitted_date, and
    noe_exception_reason from the patient's INITIAL (period_number == 1)
    benefit period, for CMS late-NOE penalty evaluation
    (app/billing/services/noe_penalty_service.py). Returns None if no
    period_number == 1 row exists yet (e.g. patient not yet admitted with
    a recorded election).
    """
    row = db.execute(
        select(
            BenefitPeriod.election_date,
            BenefitPeriod.noe_submitted_date,
            BenefitPeriod.noe_exception_reason,
        ).where(
            BenefitPeriod.tenant_id == tenant_id,
            BenefitPeriod.patient_id == patient_id,
            BenefitPeriod.period_number == 1,
        )
    ).first()

    if row is None:
        return None

    return {
        "election_date": row[0],
        "noe_submitted_date": row[1],
        "noe_exception_reason": row[2],
    }


# TODO: if/when a real patient with a hospice revocation + re-election shows
# up, extend get_election_anchor_date to return the anchor of the *current*
# unbroken election span (i.e. reset after a gap), not just period_number==1
# of the patient's entire history. Not implemented now because no real data
# has validated that scenario.
