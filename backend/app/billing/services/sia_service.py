# backend/app/billing/services/sia_service.py
"""
Service Intensity Add-on (SIA) calculation.

CMS pays an additional per-visit add-on, on top of the Routine Home Care
(RHC) per diem, for direct patient care furnished by a Registered Nurse
(RN) or Medical Social Worker (MSW/SW) during the LAST 7 DAYS of a
beneficiary's life -- but ONLY on days the patient was at the RHC level
of care (not GIP/Respite/Continuous Home Care).

PROVENANCE
---------------------------------------------------------------------------
SIA payment formula (42 CFR 418.302; CMS Claims Processing Manual Ch. 11):
    SIA = CHC hourly rate x (RN + MSW direct-care minutes that day / 60),
          capped at 4 hours (240 minutes) combined RN+MSW time per day.
The "CHC hourly rate" is the wage-index-adjusted Continuous Home Care per
diem rate divided by 24 (CHC pricing is inherently an hourly rate scaled to
a 24-hour day; SIA reuses that same hourly figure).

This has NOT been validated against a real paid SIA line item for this
tenant (no Kessler remit reviewed here included an SIA line) -- treat the
formula as CMS-sourced-and-correct-by-regulation, but flag any future SIA
remit for reconciliation the same way the RHC rates were proven this
session.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from app.billing.services.cms_rate_service import CmsRateError, get_flat_rate_for_day

SIA_WINDOW_DAYS = 7  # last 7 days of life, inclusive of date of death
SIA_MAX_MINUTES_PER_DAY = 240  # 4-hour cap, combined RN + MSW
SIA_ELIGIBLE_DISCIPLINES = {"RN", "SW"}  # SW == canonicalized MSW/social-worker discipline
SIA_ELIGIBLE_LOC = "ROUTINE"  # RHC only; SIA does not apply on GIP/Respite/CHC days


class SiaEligibilityError(RuntimeError):
    pass


def get_date_of_death(patient) -> date | None:
    """
    This app has no dedicated `date_of_death` field. Per the documented
    ACTIVE -> DECEASED lifecycle transition (patient_lifecycle.py), a
    patient's `discharge_date` IS the date of death once `status ==
    "DECEASED"`. Returns None (not an error) for any patient who hasn't
    been marked deceased -- SIA simply doesn't apply to them yet.
    """
    status = (getattr(patient, "status", "") or "").upper()
    if status != "DECEASED":
        return None
    return getattr(patient, "discharge_date", None)


def visit_minutes(start_time, end_time) -> int:
    """
    Real elapsed minutes from a visit's recorded start/end time. Returns 0
    (not a fabricated default) when either timestamp is missing -- an
    unmeasured visit contributes no SIA minutes rather than an invented
    duration.
    """
    if start_time is None or end_time is None:
        return 0
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time)

    delta = end_time - start_time
    minutes = int(delta.total_seconds() // 60)
    return max(minutes, 0)


def compute_sia_schedule(
    *,
    date_of_death: date,
    loc_by_date: dict[date, str],
    visits: list[dict],
    cbsa_code: str | None,
) -> dict:
    """
    Computes the real SIA add-on for each of the last 7 days of life that
    were billed at the RHC level of care.

    Args:
        date_of_death: from get_date_of_death().
        loc_by_date: {date: loc} for every day in the billing period
            (from loc_timeline) -- used to exclude non-RHC days.
        visits: finalized visit dicts with keys `visit_date`,
            `visit_discipline`, `start_time`, `end_time`, `status`.
        cbsa_code: tenant's CBSA code (reuses the same wage-index table as
            the RHC/GIP/Respite/CHC rates -- raises CmsRateError, not a
            fabricated rate, if the tenant/CBSA/FY combination isn't on
            file).

    Returns:
        {
            "date_of_death": ...,
            "window_start": ...,
            "days": [ {date, eligible, minutes, capped_minutes,
                       hourly_rate, amount} ... ],
            "total_amount": "..." (str, money-formatted),
        }
    """
    window_start = date_of_death - timedelta(days=SIA_WINDOW_DAYS - 1)

    # Sum eligible RN/MSW minutes per calendar day from finalized visits.
    minutes_by_day: dict[date, int] = {}
    for visit in visits:
        if (visit.get("status") or "").upper() != "FINALIZED":
            continue
        discipline = (visit.get("visit_discipline") or "").upper()
        if discipline not in SIA_ELIGIBLE_DISCIPLINES:
            continue

        visit_day = visit.get("visit_date")
        if isinstance(visit_day, str):
            visit_day = date.fromisoformat(visit_day)
        elif isinstance(visit_day, datetime):
            visit_day = visit_day.date()
        if visit_day is None or not (window_start <= visit_day <= date_of_death):
            continue

        minutes = visit_minutes(visit.get("start_time"), visit.get("end_time"))
        minutes_by_day[visit_day] = minutes_by_day.get(visit_day, 0) + minutes

    days: list[dict] = []
    total = Decimal("0.00")
    current = window_start

    while current <= date_of_death:
        loc = loc_by_date.get(current)
        eligible = loc == SIA_ELIGIBLE_LOC
        raw_minutes = minutes_by_day.get(current, 0)
        capped_minutes = min(raw_minutes, SIA_MAX_MINUTES_PER_DAY) if eligible else 0

        amount = Decimal("0.00")
        hourly_rate = None
        if eligible and capped_minutes > 0:
            try:
                chc_daily_rate = get_flat_rate_for_day(
                    loc="CONTINUOUS CARE", as_of=current, cbsa_code=cbsa_code
                )
            except CmsRateError:
                raise
            hourly_rate = (chc_daily_rate / Decimal("24")).quantize(Decimal("0.0001"))
            amount = (hourly_rate * Decimal(capped_minutes) / Decimal("60")).quantize(
                Decimal("0.01")
            )
            total += amount

        days.append(
            {
                "date": current,
                "loc": loc,
                "eligible": eligible,
                "raw_minutes": raw_minutes,
                "capped_minutes": capped_minutes,
                "hourly_rate": str(hourly_rate) if hourly_rate is not None else None,
                "amount": str(amount),
            }
        )
        current += timedelta(days=1)

    return {
        "date_of_death": date_of_death,
        "window_start": window_start,
        "days": days,
        "total_amount": str(total.quantize(Decimal("0.01"))),
    }
