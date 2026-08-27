from __future__ import annotations

"""
CMS late-NOTR (Notice of Termination/Revocation) compliance flag.

Real CMS rule (42 CFR 418.24(e) / CMS Transmittal 2551 and successors):
when a hospice election ends for any reason other than death (revocation,
transfer to another hospice, or discharge for cause/no-longer-terminally-
ill), the hospice must submit an electronic NOTR (837 TOB 8XB) within 5
calendar days of the effective date of revocation/discharge. Unlike the
NOE penalty, a late NOTR does not zero out THIS agency's own claim lines
(the patient is already discharged, so there is nothing left on this
agency's books for the gap) -- CMS instead holds the hospice financially
liable for any OTHER Medicare services the beneficiary received during
the gap between the effective date and the (late) filing date, since
those other providers could not bill Medicare while the election
appeared still active. This module only computes the compliance flag and
the liability window for audit/reporting; it intentionally does not
touch billing_engine claim lines.

Not evaluated for death discharges: a death discharge closes the benefit
period without requiring a NOTR (the final claim itself reports the
discharge).
"""

from dataclasses import dataclass
from datetime import date, timedelta

NOTR_TIMELY_FILING_WINDOW_DAYS = 5


class NotrPenaltyError(RuntimeError):
    pass


@dataclass(frozen=True)
class NotrPenaltyResult:
    is_late: bool
    is_exempt: bool
    liability_start: date | None
    liability_end: date | None
    liability_days: int
    reason: str | None


def _filing_deadline(discharge_date: date) -> date:
    return discharge_date + timedelta(days=NOTR_TIMELY_FILING_WINDOW_DAYS)


def compute_notr_penalty(
    discharge_date: date,
    notr_submitted_date: date | None,
    exception_reason: str | None = None,
    *,
    as_of_date: date | None = None,
) -> NotrPenaltyResult:
    """
    Determines whether a hospice discharge/revocation's NOTR was filed
    late and, if so, the resulting liability window (see module docstring
    -- this does not affect this agency's own claim lines).

    Args:
        discharge_date: the patient's real discharge/revocation effective
            date (Patient.discharge_date).
        notr_submitted_date: the real date the NOTR was actually filed.
            None means "not yet filed".
        exception_reason: if set, a CMS-recognized exception waives the
            penalty regardless of timing -- must be a real, documented
            justification.
        as_of_date: for an unfiled NOTR, the date to evaluate lateness
            against (defaults to today).
    """
    if discharge_date is None:
        raise NotrPenaltyError("discharge_date is required to evaluate NOTR timeliness")

    deadline = _filing_deadline(discharge_date)

    if exception_reason:
        return NotrPenaltyResult(
            is_late=False,
            is_exempt=True,
            liability_start=None,
            liability_end=None,
            liability_days=0,
            reason=f"CMS exception applies: {exception_reason}",
        )

    if notr_submitted_date is None:
        evaluation_date = as_of_date or date.today()
        if evaluation_date <= deadline:
            return NotrPenaltyResult(
                is_late=False,
                is_exempt=False,
                liability_start=None,
                liability_end=None,
                liability_days=0,
                reason=None,
            )
        liability_end = evaluation_date - timedelta(days=1)
        liability_days = (liability_end - discharge_date).days + 1
        return NotrPenaltyResult(
            is_late=True,
            is_exempt=False,
            liability_start=discharge_date,
            liability_end=liability_end,
            liability_days=liability_days,
            reason=(
                f"NOTR not yet filed; discharge {discharge_date.isoformat()} "
                f"exceeded the {NOTR_TIMELY_FILING_WINDOW_DAYS}-day filing "
                f"deadline ({deadline.isoformat()}); the agency is liable for "
                "other Medicare services the beneficiary receives until this is filed"
            ),
        )

    if notr_submitted_date <= deadline:
        return NotrPenaltyResult(
            is_late=False,
            is_exempt=False,
            liability_start=None,
            liability_end=None,
            liability_days=0,
            reason=None,
        )

    liability_end = notr_submitted_date - timedelta(days=1)
    liability_days = (liability_end - discharge_date).days + 1

    return NotrPenaltyResult(
        is_late=True,
        is_exempt=False,
        liability_start=discharge_date,
        liability_end=liability_end,
        liability_days=liability_days,
        reason=(
            f"NOTR filed {notr_submitted_date.isoformat()}, after the "
            f"{NOTR_TIMELY_FILING_WINDOW_DAYS}-day deadline ({deadline.isoformat()}) "
            f"for discharge {discharge_date.isoformat()}; the agency is liable for "
            "other Medicare services the beneficiary received during the gap"
        ),
    )
