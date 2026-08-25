from __future__ import annotations

"""
CMS late-NOE (Notice of Election) non-covered-day penalty calculator.

Real CMS rule (42 CFR 418.24(b) / CMS Transmittal 2551 and successors):
a hospice must submit its NOE (electronic 837 TOB 8XA or paper equivalent)
within 5 calendar days after the effective date of election. If the NOE is
filed late, all days from the election effective date through the day
before the date of filing are NOT covered by the hospice benefit (i.e.
non-billable to Medicare under RHC/GIP/CHC/Respite rates) -- the days from
the filing date forward are payable normally. This penalty is waived only
for CMS-recognized "exceptional circumstances" (documented on the benefit
period as noe_exception_reason).

This module intentionally computes ONLY the penalty window; it does not
decide what to do with claim lines that fall inside it -- callers (e.g.
billing_engine.py) are responsible for zeroing/flagging the overlapping
days, the same "never silently zero without a reason" pattern used for
CMS rate gaps in claim_segment_service.py.
"""

from dataclasses import dataclass
from datetime import date, timedelta

# CMS's NOE filing deadline: 5 calendar days after the election effective
# date. A NOE filed ON OR BEFORE (election_date + 5 days) is timely.
NOE_TIMELY_FILING_WINDOW_DAYS = 5


class NoePenaltyError(RuntimeError):
    pass


@dataclass(frozen=True)
class NoePenaltyResult:
    is_late: bool
    is_exempt: bool
    non_covered_start: date | None
    non_covered_end: date | None
    non_covered_days: int
    reason: str | None


def _filing_deadline(election_date: date) -> date:
    return election_date + timedelta(days=NOE_TIMELY_FILING_WINDOW_DAYS)


def compute_noe_penalty(
    election_date: date,
    noe_submitted_date: date | None,
    exception_reason: str | None = None,
    *,
    as_of_date: date | None = None,
) -> NoePenaltyResult:
    """
    Determines whether a hospice election's NOE was filed late and, if so,
    the resulting non-covered day range.

    Args:
        election_date: the benefit period's real election effective date
            (BenefitPeriod.election_date for the INITIAL / period_number=1
            period).
        noe_submitted_date: the real date the NOE was actually filed/
            accepted. None means "not yet filed".
        exception_reason: if set, a CMS-recognized exception applies and
            the late-filing penalty is waived regardless of timing --
            this must be a real, documented justification, never a
            default/placeholder value.
        as_of_date: for an unfiled NOE, the date to evaluate lateness
            against (defaults to today). Only used when
            noe_submitted_date is None, to flag an overdue-but-not-yet-
            filed election as already in penalty territory.

    Returns:
        NoePenaltyResult. When is_late is True and is_exempt is False,
        non_covered_start/end/days describe the real non-covered window
        that must be excluded from billable claim lines.
    """
    if election_date is None:
        raise NoePenaltyError("election_date is required to evaluate NOE timeliness")

    deadline = _filing_deadline(election_date)

    if exception_reason:
        return NoePenaltyResult(
            is_late=False,
            is_exempt=True,
            non_covered_start=None,
            non_covered_end=None,
            non_covered_days=0,
            reason=f"CMS exception applies: {exception_reason}",
        )

    if noe_submitted_date is None:
        # Not filed yet. Only flag it late once the deadline has actually
        # passed as of the evaluation date -- do not fabricate a penalty
        # for an election that is still within its timely-filing window.
        evaluation_date = as_of_date or date.today()
        if evaluation_date <= deadline:
            return NoePenaltyResult(
                is_late=False,
                is_exempt=False,
                non_covered_start=None,
                non_covered_end=None,
                non_covered_days=0,
                reason=None,
            )
        # Overdue and still unfiled: the non-covered window currently runs
        # from election_date through the day before "today" (it keeps
        # growing daily until the NOE is actually filed).
        non_covered_end = evaluation_date - timedelta(days=1)
        non_covered_days = (non_covered_end - election_date).days + 1
        return NoePenaltyResult(
            is_late=True,
            is_exempt=False,
            non_covered_start=election_date,
            non_covered_end=non_covered_end,
            non_covered_days=non_covered_days,
            reason=(
                f"NOE not yet filed; election {election_date.isoformat()} "
                f"exceeded the {NOE_TIMELY_FILING_WINDOW_DAYS}-day filing "
                f"deadline ({deadline.isoformat()})"
            ),
        )

    if noe_submitted_date <= deadline:
        return NoePenaltyResult(
            is_late=False,
            is_exempt=False,
            non_covered_start=None,
            non_covered_end=None,
            non_covered_days=0,
            reason=None,
        )

    non_covered_end = noe_submitted_date - timedelta(days=1)
    non_covered_days = (non_covered_end - election_date).days + 1

    return NoePenaltyResult(
        is_late=True,
        is_exempt=False,
        non_covered_start=election_date,
        non_covered_end=non_covered_end,
        non_covered_days=non_covered_days,
        reason=(
            f"NOE filed {noe_submitted_date.isoformat()}, after the "
            f"{NOE_TIMELY_FILING_WINDOW_DAYS}-day deadline "
            f"({deadline.isoformat()}) for election {election_date.isoformat()}"
        ),
    )


def apply_noe_penalty_to_claim_lines(
    claim_lines: list[dict],
    penalty: NoePenaltyResult,
) -> list[dict]:
    """
    Post-processes already-priced claim lines (as produced by
    claim_segment_service.build_claim_lines) to zero out and flag any day
    range that falls inside a late-NOE non-covered window. Splits a claim
    line into up to three pieces (before/inside/after the penalty window)
    so only the truly non-covered days lose their revenue -- covered days
    on the same line keep their real priced amount.

    This never silently drops revenue: every zeroed/split line carries a
    `noe_penalty_reason` so callers can surface it the same way
    `rate_gap_reason` surfaces CMS rate gaps.
    """
    if not penalty.is_late or penalty.is_exempt or not claim_lines:
        return claim_lines

    window_start = penalty.non_covered_start
    window_end = penalty.non_covered_end

    result: list[dict] = []
    for line in claim_lines:
        from_date = date.fromisoformat(line["from_date"])
        to_date = date.fromisoformat(line["to_date"])

        overlap_start = max(from_date, window_start)
        overlap_end = min(to_date, window_end)

        if overlap_start > overlap_end:
            # No overlap with the penalty window -- unaffected.
            result.append(line)
            continue

        # Portion before the penalty window (still billable as-is).
        if from_date < overlap_start:
            before = dict(line)
            before_end = overlap_start - timedelta(days=1)
            before["to_date"] = before_end.isoformat()
            before["days"] = (before_end - from_date).days + 1
            before["estimated_amount"] = _scale_amount(line, before["days"])
            result.append(before)

        # The non-covered portion itself: zeroed, flagged.
        penalized = dict(line)
        penalized["from_date"] = overlap_start.isoformat()
        penalized["to_date"] = overlap_end.isoformat()
        penalized["days"] = (overlap_end - overlap_start).days + 1
        penalized["rate"] = "0.00"
        penalized["estimated_amount"] = "0.00"
        penalized["noe_penalty_reason"] = penalty.reason
        result.append(penalized)

        # Portion after the penalty window (still billable as-is).
        if to_date > overlap_end:
            after = dict(line)
            after_start = overlap_end + timedelta(days=1)
            after["from_date"] = after_start.isoformat()
            after["days"] = (to_date - after_start).days + 1
            after["estimated_amount"] = _scale_amount(line, after["days"])
            result.append(after)

    return result


def _scale_amount(line: dict, days: int) -> str:
    """
    Re-derives a sub-range's dollar amount from the line's per-day rate
    rather than re-splitting the original estimated_amount, so rounding
    stays anchored to the real per-diem rate.
    """
    from decimal import Decimal

    rate = Decimal(str(line.get("rate", "0.00")))
    return str(rate * Decimal(days))
