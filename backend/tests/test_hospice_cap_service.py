# backend/tests/test_hospice_cap_service.py
"""
Tests the hospice aggregate cap tracker against Love & Faith Hospice's
REAL official CMS PS&R reports (Provider Statistical and Reimbursement
System, Provider #B51771, run 08/07/26):
  - "Hospice Beneficiary Count Summary (Fully Pro-Rated)" (beneficiary
    counts per cap year)
  - "Redesign Provider Summary Report" Report #OD44203 (gross
    reimbursement per cap year)

Reproduces the resulting Allowed/Available cap figures to the cent, which
also matches the biller's (NE Billing Inc) own cap-monitoring email.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.billing.services.hospice_cap_service import (
    HospiceCapError,
    cap_year_for_date,
    compute_agency_cap_usage,
    estimate_single_agency_beneficiary_count,
    expand_claim_lines_to_daily_amounts,
    get_cap_amount,
)


def test_cap_year_boundaries():
    # Cap year Y runs Nov 1 (Y-1) -> Oct 31 (Y).
    assert cap_year_for_date(date(2025, 10, 31)) == 2025
    assert cap_year_for_date(date(2025, 11, 1)) == 2026
    assert cap_year_for_date(date(2025, 12, 31)) == 2026
    assert cap_year_for_date(date(2026, 1, 1)) == 2026
    assert cap_year_for_date(date(2026, 10, 31)) == 2026


def test_real_published_cap_amounts():
    # Real CMS-published per-beneficiary cap amounts.
    assert get_cap_amount(2024) == Decimal("33494.01")
    assert get_cap_amount(2025) == Decimal("34465.34")
    assert get_cap_amount(2026) == Decimal("35361.44")


def test_unknown_cap_year_raises_instead_of_fabricating():
    with pytest.raises(HospiceCapError):
        get_cap_amount(2030)


def test_matches_real_cms_psr_report_cap_year_2026():
    # Real "Hospice Beneficiary Count Summary" (2026: 3.8911) x real
    # "Redesign Provider Summary Report" gross reimbursement for
    # 10/01/25-09/30/26 ($110,570.77).
    result = compute_agency_cap_usage(
        cap_year=2026,
        beneficiary_count="3.8911",
        gross_reimbursement_collected="110570.77",
    )
    assert result["allowed_amount"] == "137594.90"
    assert result["available_amount"] == "27024.13"
    assert result["is_over_cap"] is False
    assert result["over_cap_amount"] == "0.00"


def test_matches_real_cms_psr_report_cap_year_2025():
    # Beneficiary count 8.3635 x gross reimbursement $274,465.51
    # (10/01/24-09/30/25).
    result = compute_agency_cap_usage(
        cap_year=2025,
        beneficiary_count="8.3635",
        gross_reimbursement_collected="274465.51",
    )
    assert result["allowed_amount"] == "288250.87"
    assert result["available_amount"] == "13785.36"
    assert result["is_over_cap"] is False


def test_matches_real_cms_psr_report_cap_year_2024():
    # Beneficiary count 2.8576 x gross reimbursement $79,002.31
    # (10/01/23-09/30/24).
    result = compute_agency_cap_usage(
        cap_year=2024,
        beneficiary_count="2.8576",
        gross_reimbursement_collected="79002.31",
    )
    # The real report displays this as $95,712.48; our quantized formula
    # produces the identical cent value.
    assert result["allowed_amount"] == "95712.48"
    assert result["available_amount"] == "16710.17"
    assert result["is_over_cap"] is False


def test_over_cap_when_gross_exceeds_allowed():
    result = compute_agency_cap_usage(
        cap_year=2026,
        beneficiary_count="1.0",
        gross_reimbursement_collected="40000.00",
    )
    assert result["is_over_cap"] is True
    assert Decimal(result["over_cap_amount"]) == Decimal("40000.00") - Decimal("35361.44")
    assert result["available_amount"] == "0.00"


def test_single_agency_estimate_is_a_conservative_upper_bound_not_the_real_count():
    # A patient with 200 days entirely at this agency (no transfer)
    # contributes 200/365 to the same-agency-only estimate; this ignores
    # any days spent at another hospice, unlike the real, cross-provider
    # 42 CFR 418.309(b)(2) count NGS reports.
    estimate = estimate_single_agency_beneficiary_count(
        cap_year=2026,
        hospice_days_at_this_agency_by_patient={"kessler": 200},
    )
    assert estimate == (Decimal("200") / Decimal("365")).quantize(Decimal("0.0001"))


def test_expand_claim_lines_to_daily_amounts():
    claim_lines = [
        {"from_date": "2025-10-29", "to_date": "2025-11-02", "rate": "202.83"},
    ]
    daily = expand_claim_lines_to_daily_amounts(claim_lines)
    assert len(daily) == 5
    assert daily[0] == (date(2025, 10, 29), Decimal("202.83"))
    assert daily[-1] == (date(2025, 11, 2), Decimal("202.83"))

    # This single claim line spans the Nov 1 cap-year boundary; confirm the
    # split lands where it should.
    cap_2025_days = [d for d, _ in daily if cap_year_for_date(d) == 2025]
    cap_2026_days = [d for d, _ in daily if cap_year_for_date(d) == 2026]
    assert len(cap_2025_days) == 3  # 10/29, 10/30, 10/31
    assert len(cap_2026_days) == 2  # 11/1, 11/2
