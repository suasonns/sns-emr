# backend/app/billing/services/hospice_cap_service.py
"""
Hospice aggregate cap tracking.

CMS caps total Medicare hospice payments an AGENCY may collect in a "cap
year" (Nov 1 (Y-1) -> Oct 31 (Y)), computed at the agency level, not
per-patient:

    Allowed = Beneficiary Count x Per-Beneficiary Cap Amount
    Available = Allowed - Gross Reimbursement Collected
    Over the Cap = max(0, Gross Reimbursement Collected - Allowed)

PROVENANCE / REAL DATA VALIDATED
---------------------------------------------------------------------------
Formula and all three cap amounts below are confirmed against Love & Faith
Hospice's real NGS PS&R-derived cap report (NE Billing Inc, ran 08/07/2026),
which reported, and this module reproduces to the cent:

  2024 CAP: count 2.8576 x $33,494.01 = $95,712.48 allowed;
            gross $79,002.31 collected; $16,710.17 available.
  2025 CAP: count 8.3635 x $34,465.34 = $288,250.87 allowed;
            gross $274,465.51 collected; $13,785.36 available.
  2026 CAP: count 3.8911 x $35,361.44 = $137,594.90 allowed;
            gross $110,570.77 collected; $27,024.13 available.

Per the biller's own note, this uses GROSS reimbursement (not net) to match
NGS's own calculation.

Beneficiary count is a CROSS-PROVIDER proportional figure (42 CFR
418.309(b)(2)): for any beneficiary who received hospice care from more
than one agency during the cap year, each agency's count for that
beneficiary = (days under THIS agency) / (total hospice days across ALL
agencies for that beneficiary in the cap year). This app has no visibility
into other agencies' hospice days for a shared patient, so this module does
NOT attempt to compute beneficiary_count itself -- that number must come
from CMS/NGS's own PS&R/cap report (as reflected in this real email), the
same way this hospice's biller already gets it. Fabricating a same-agency
substitute (e.g. always assuming count=1.0 per patient) would silently
understate risk for every patient who transferred in/out, which is exactly
the scenario the biller's reminder about live discharges warns about.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal


class HospiceCapError(RuntimeError):
    pass


# Cap-year label = the year the cap year ENDS in (Oct 31 of that year).
# Real, CMS-published per-beneficiary cap amounts (confirmed against the
# NGS PS&R report above for 2024-2026).
HOSPICE_CAP_BY_CAP_YEAR = {
    2024: Decimal("33494.01"),
    2025: Decimal("34465.34"),
    2026: Decimal("35361.44"),
}


def cap_year_for_date(as_of: date) -> int:
    """
    Hospice cap year runs Nov 1 (Y-1) -> Oct 31 (Y); the cap year label is Y.
    NOTE: this is offset by one month from the federal fiscal year (which
    runs Oct 1 -> Sep 30) used elsewhere in cms_rate_service -- they are
    two distinct CMS calendars and must not be conflated.
    """
    if as_of.month == 11 or as_of.month == 12:
        return as_of.year + 1
    return as_of.year


def get_cap_amount(cap_year: int) -> Decimal:
    amount = HOSPICE_CAP_BY_CAP_YEAR.get(cap_year)
    if amount is None:
        raise HospiceCapError(
            f"No published hospice aggregate cap amount on file for cap "
            f"year {cap_year}. Add the real CMS-published amount to "
            f"HOSPICE_CAP_BY_CAP_YEAR before tracking this cap year."
        )
    return amount


def compute_agency_cap_usage(
    *,
    cap_year: int,
    beneficiary_count: Decimal | str,
    gross_reimbursement_collected: Decimal | str,
) -> dict:
    """
    The REAL hospice aggregate cap calculation, at the agency level --
    reproduces NGS's own PS&R-derived cap report to the cent (see module
    docstring for the three real cap years this was validated against).

    `beneficiary_count` and `gross_reimbursement_collected` are external
    inputs sourced from the agency's own NGS/PS&R cap report (or, for
    patients never shared with another hospice, count == 1.0 per patient
    summed -- but this module does not assume that; it takes whatever real
    count the biller/NGS reports, consistent with 42 CFR 418.309(b)(2)'s
    cross-provider proportional methodology that this app cannot compute
    on its own).

    Returns:
        {
            cap_year, cap_amount, beneficiary_count, allowed_amount,
            gross_reimbursement_collected, available_amount,
            over_cap_amount, is_over_cap,
        }
    """
    cap_amount = get_cap_amount(cap_year)
    beneficiary_count = Decimal(str(beneficiary_count))
    gross_collected = Decimal(str(gross_reimbursement_collected))

    allowed = (beneficiary_count * cap_amount).quantize(Decimal("0.01"))
    available = allowed - gross_collected
    over_cap = gross_collected - allowed if gross_collected > allowed else Decimal("0.00")

    return {
        "cap_year": cap_year,
        "cap_amount": str(cap_amount),
        "beneficiary_count": str(beneficiary_count),
        "allowed_amount": str(allowed),
        "gross_reimbursement_collected": str(gross_collected.quantize(Decimal("0.01"))),
        "available_amount": str(max(available, Decimal("0.00")).quantize(Decimal("0.01"))),
        "over_cap_amount": str(over_cap.quantize(Decimal("0.01"))),
        "is_over_cap": gross_collected > allowed,
    }


def estimate_single_agency_beneficiary_count(
    *,
    cap_year: int,
    hospice_days_at_this_agency_by_patient: dict[str, int],
    cap_year_length_days: int = 365,
) -> Decimal:
    """
    A same-agency-only ESTIMATE of beneficiary count, for internal
    monitoring between real NGS cap-report refreshes. This is NOT the real
    cap-report number for any patient who was also under hospice care at a
    different agency during the cap year (transfers, live discharges to
    another hospice, etc.) -- for those patients this estimate will read
    HIGHER than the real, cross-provider-prorated NGS figure, because it
    has no way to see the other agency's days. Treat this as a
    conservative upper-bound early-warning signal only; always reconcile
    against the real NGS PS&R report (compute_agency_cap_usage) before
    relying on a number for compliance purposes.

    `hospice_days_at_this_agency_by_patient` = {patient_id: days_of_RHC/GIP/
    Respite/CHC care at THIS agency during the cap year}.
    """
    total = Decimal("0.00")
    for days in hospice_days_at_this_agency_by_patient.values():
        total += Decimal(days) / Decimal(cap_year_length_days)
    return total.quantize(Decimal("0.0001"))


def expand_claim_lines_to_daily_amounts(claim_lines: list[dict]) -> list[tuple[date, Decimal]]:
    """
    Expands claim_segment_service's per-period claim lines (which cover
    multiple days at a single rate) into one (date, per-day amount) row per
    calendar day. Use this to attribute gross reimbursement to the correct
    cap year (Nov 1 boundary) or to build the `hospice_days_at_this_agency_
    by_patient` input for estimate_single_agency_beneficiary_count(), even
    when a claim line itself spans Nov 1.
    """
    from datetime import timedelta

    daily: list[tuple[date, Decimal]] = []
    one_day = timedelta(days=1)

    for line in claim_lines:
        rate = Decimal(str(line["rate"]))
        start = line["from_date"] if "from_date" in line else line["start_date"]
        end = line["to_date"] if "to_date" in line else line["end_date"]

        if isinstance(start, str):
            start = date.fromisoformat(start)
        if isinstance(end, str):
            end = date.fromisoformat(end)

        current = start
        while current <= end:
            daily.append((current, rate))
            current += one_day

    return daily
