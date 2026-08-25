# backend/tests/test_claim_segment_service.py
"""
Regression test for a real production-readiness bug found during audit:
when a tenant IS configured for real CMS rates (cbsa_code set) but a
specific period can't be priced (e.g. a fiscal year not yet populated in
cms_rate_service.BASE_RATES_BY_FY), build_claim_lines() used to silently
fall back to the legacy $0.00 flat-rate path with no visible signal --
indistinguishable from a tenant that was never configured for real rates
at all. That silently under-bills real service days. This test locks in
the fix: such a line is still produced (so the pipeline doesn't crash),
but carries a `rate_gap_reason`, and the aggregated revenue summary flags
`has_rate_gaps=True` so it surfaces instead of hiding.
"""

from datetime import date

from app.billing.services.claim_segment_service import build_claim_lines
from app.billing.services.revenue_service import build_revenue_summary_from_claim_lines


def test_unpriced_fiscal_year_surfaces_rate_gap_instead_of_silent_zero():
    # FY2030 (Oct 2029 -> Sep 2030) has no entry in BASE_RATES_BY_FY.
    loc_segments = [
        {
            "start_date": date(2029, 10, 1),
            "end_date": date(2029, 10, 5),
            "loc": "ROUTINE",
            "pos": "HOME",
            "facility_name": None,
        }
    ]

    claim_lines = build_claim_lines(
        loc_segments,
        cbsa_code="40140",
        election_anchor_date=date(2020, 1, 1),
    )

    assert len(claim_lines) == 1
    line = claim_lines[0]
    assert line["rate"] == "0.00"
    assert line["rate_gap_reason"] is not None
    assert "FY2030" in line["rate_gap_reason"]

    revenue_summary = build_revenue_summary_from_claim_lines(claim_lines)
    assert revenue_summary["has_rate_gaps"] is True
    assert revenue_summary["rows"][0]["rate_gap_reason"] is not None


def test_missing_election_anchor_on_cms_rate_enabled_tenant_surfaces_gap():
    loc_segments = [
        {
            "start_date": date(2025, 9, 1),
            "end_date": date(2025, 9, 5),
            "loc": "ROUTINE",
            "pos": "HOME",
            "facility_name": None,
        }
    ]

    # Tenant has a real CBSA configured, but this patient has no election
    # anchor on file -- RHC tiering can't be determined.
    claim_lines = build_claim_lines(
        loc_segments,
        cbsa_code="40140",
        election_anchor_date=None,
    )

    assert len(claim_lines) == 1
    assert claim_lines[0]["rate"] == "0.00"
    assert claim_lines[0]["rate_gap_reason"] is not None


def test_normal_priced_period_has_no_rate_gap():
    loc_segments = [
        {
            "start_date": date(2025, 10, 1),
            "end_date": date(2025, 10, 5),
            "loc": "ROUTINE",
            "pos": "HOME",
            "facility_name": None,
        }
    ]

    claim_lines = build_claim_lines(
        loc_segments,
        cbsa_code="40140",
        election_anchor_date=date(2020, 1, 1),  # long past tier-1, day-61+ tier
    )

    assert all(line["rate_gap_reason"] is None for line in claim_lines)
    revenue_summary = build_revenue_summary_from_claim_lines(claim_lines)
    assert revenue_summary["has_rate_gaps"] is False


def test_unconfigured_tenant_legacy_zero_path_has_no_rate_gap_flag():
    # A tenant with no cbsa_code at all is the pre-existing, intentional
    # $0.00 placeholder behavior -- must NOT be flagged as a rate gap.
    loc_segments = [
        {
            "start_date": date(2025, 10, 1),
            "end_date": date(2025, 10, 5),
            "loc": "ROUTINE",
            "pos": "HOME",
            "facility_name": None,
        }
    ]

    claim_lines = build_claim_lines(loc_segments)
    assert claim_lines[0]["rate"] == "0.00"
    assert claim_lines[0]["rate_gap_reason"] is None
