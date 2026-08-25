from __future__ import annotations

"""
Real documentation-gap checks for GIP / Respite / Continuous Home Care
(CHC) level-of-care (LOC) billing days -- a compliance/audit exposure
distinct from the respite 5-day rate-rollover cap (already enforced in
pos_to_loc_service).

Real CMS rules this checks against:
  - GIP (42 CFR 418.302 / CMS Hospice Conditions of Participation) requires
    a physician-documented need for inpatient-level symptom management;
    the agency must be able to produce that justification on audit.
  - Respite (42 CFR 418.204(c)) similarly requires a documented caregiver
    need justifying the respite admission.
  - Continuous Home Care / CHC (42 CFR 418.204, CMS Hospice CoPs) requires
    predominantly nursing care with a minimum of 8 hours of direct patient
    care in a 24-hour period; a CHC day without >=480 documented minutes
    of direct care is not CMS-supportable.

This module only reports gaps against real, already-captured data
(GIPPeriod.reason / RespitePeriod.reason / actual visit_minutes rows) --
it never fabricates a justification or invents visit time.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

CHC_MINIMUM_DIRECT_CARE_MINUTES_PER_DAY = 8 * 60


@dataclass(frozen=True)
class DateRangeEventLike:
    start_date: date
    end_date: date
    reason: str | None = None


@dataclass(frozen=True)
class LocDocumentationGapResult:
    has_gaps: bool
    reasons: list[str] = field(default_factory=list)


def _dates_in_range(start_date: date, end_date: date) -> list[date]:
    return [start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1)]


def compute_loc_documentation_gaps(
    *,
    gip_events,
    respite_events,
    continuous_events,
    chc_minutes_by_date: dict[date, int],
) -> LocDocumentationGapResult:
    """
    Args:
        gip_events / respite_events / continuous_events: the same
            DateRangeEvent lists billing_engine already loads for this
            cycle (each carries a real `reason` field sourced from
            GIPPeriod.reason / RespitePeriod.reason /
            ContinuousCareEvent.reason).
        chc_minutes_by_date: real total documented visit_minutes per
            calendar date for this patient/cycle (from visit_minutes
            rows), used to check the CHC 8-hour/day minimum.
    """
    reasons: list[str] = []

    for gip in gip_events:
        if not (gip.reason or "").strip():
            reasons.append(
                f"GIP period {gip.start_date.isoformat()}-{gip.end_date.isoformat()} "
                "has no documented physician justification on file (required to "
                "support inpatient-level symptom management on audit)."
            )

    for respite in respite_events:
        if not (respite.reason or "").strip():
            reasons.append(
                f"Respite period {respite.start_date.isoformat()}-{respite.end_date.isoformat()} "
                "has no documented caregiver-need justification on file."
            )

    for chc in continuous_events:
        if not (chc.reason or "").strip():
            reasons.append(
                f"Continuous Home Care period {chc.start_date.isoformat()}-{chc.end_date.isoformat()} "
                "has no documented clinical justification on file."
            )

        for day in _dates_in_range(chc.start_date, chc.end_date):
            minutes = chc_minutes_by_date.get(day, 0)
            if minutes < CHC_MINIMUM_DIRECT_CARE_MINUTES_PER_DAY:
                hours = minutes / 60
                reasons.append(
                    f"CHC day {day.isoformat()} has only {hours:.1f} documented direct-care "
                    f"hours (CMS requires >= 8 hours/24-hour period); this day is not "
                    "audit-supportable as billed."
                )

    return LocDocumentationGapResult(has_gaps=bool(reasons), reasons=reasons)
