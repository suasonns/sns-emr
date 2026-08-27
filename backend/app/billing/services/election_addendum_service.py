from __future__ import annotations

"""
Real CMS Election Statement Addendum timeliness rule (42 CFR 418.24(b),
CMS Hospice CoPs / Transmittal 10573 and successors):

  - If the addendum is requested within the first 5 days of the hospice
    election, the hospice must furnish it in writing within 5 days of
    the request.
  - If requested after the first 5 days of the election (any time during
    the course of care), the hospice must furnish it within 3 days
    (72 hours) of the request -- regardless of who requested it (patient/
    representative, non-hospice provider, or a Medicare contractor).
  - If the patient dies, revokes the election, or is discharged before
    the applicable deadline elapses and the addendum has not yet been
    furnished, the requirement is considered satisfied (no addendum is
    owed).

This module only evaluates real, already-captured dates (election date,
request date, delivery date, discharge/death date) -- it never fabricates
a delivery or invents a request that wasn't logged.
"""

from dataclasses import dataclass
from datetime import date, timedelta

WITHIN_ELECTION_WINDOW_DAYS = 5
STANDARD_FURNISH_DEADLINE_DAYS = 5
EXPEDITED_FURNISH_DEADLINE_DAYS = 3


class ElectionAddendumComplianceError(RuntimeError):
    pass


@dataclass(frozen=True)
class ElectionAddendumComplianceResult:
    deadline_days: int
    deadline_date: date
    is_satisfied: bool
    is_late: bool
    is_waived_by_early_discharge: bool
    reason: str | None


def compute_addendum_compliance(
    *,
    election_date: date,
    requested_date: date,
    delivered_date: date | None,
    discharge_or_death_date: date | None = None,
    not_required_reason: str | None = None,
    as_of_date: date | None = None,
) -> ElectionAddendumComplianceResult:
    """
    Args:
        election_date: the patient's real hospice election effective date.
        requested_date: the real date the addendum was requested.
        delivered_date: the real date the addendum was actually furnished
            in writing, or None if not yet furnished.
        discharge_or_death_date: the patient's real discharge_date when
            status indicates death/revocation/discharge (see
            sia_service.get_date_of_death for the same convention this
            app uses -- there is no dedicated date_of_death field).
        not_required_reason: a documented reason the requirement doesn't
            apply (e.g. request later withdrawn) -- must be a real,
            documented justification, never assumed.
        as_of_date: evaluation date for a still-undelivered addendum
            (defaults to today).
    """
    if election_date is None:
        raise ElectionAddendumComplianceError("election_date is required")
    if requested_date is None:
        raise ElectionAddendumComplianceError("requested_date is required")

    within_election_window = (requested_date - election_date).days <= WITHIN_ELECTION_WINDOW_DAYS
    deadline_days = STANDARD_FURNISH_DEADLINE_DAYS if within_election_window else EXPEDITED_FURNISH_DEADLINE_DAYS
    deadline_date = requested_date + timedelta(days=deadline_days)

    if not_required_reason:
        return ElectionAddendumComplianceResult(
            deadline_days=deadline_days,
            deadline_date=deadline_date,
            is_satisfied=True,
            is_late=False,
            is_waived_by_early_discharge=False,
            reason=f"Requirement waived: {not_required_reason}",
        )

    if delivered_date is not None:
        is_late = delivered_date > deadline_date
        return ElectionAddendumComplianceResult(
            deadline_days=deadline_days,
            deadline_date=deadline_date,
            is_satisfied=True,
            is_late=is_late,
            is_waived_by_early_discharge=False,
            reason=(
                f"Furnished {delivered_date.isoformat()}, after the "
                f"{deadline_days}-day deadline ({deadline_date.isoformat()})"
                if is_late
                else None
            ),
        )

    # Not yet delivered.
    if discharge_or_death_date is not None and discharge_or_death_date <= deadline_date:
        return ElectionAddendumComplianceResult(
            deadline_days=deadline_days,
            deadline_date=deadline_date,
            is_satisfied=True,
            is_late=False,
            is_waived_by_early_discharge=True,
            reason=(
                f"Requirement satisfied: patient discharged/revoked/died "
                f"{discharge_or_death_date.isoformat()}, before the "
                f"{deadline_days}-day deadline ({deadline_date.isoformat()}) elapsed"
            ),
        )

    evaluation_date = as_of_date or date.today()
    if evaluation_date <= deadline_date:
        return ElectionAddendumComplianceResult(
            deadline_days=deadline_days,
            deadline_date=deadline_date,
            is_satisfied=False,
            is_late=False,
            is_waived_by_early_discharge=False,
            reason=None,
        )

    return ElectionAddendumComplianceResult(
        deadline_days=deadline_days,
        deadline_date=deadline_date,
        is_satisfied=False,
        is_late=True,
        is_waived_by_early_discharge=False,
        reason=(
            f"Election Statement Addendum requested {requested_date.isoformat()} "
            f"not furnished within the {deadline_days}-day deadline "
            f"({deadline_date.isoformat()})"
        ),
    )
