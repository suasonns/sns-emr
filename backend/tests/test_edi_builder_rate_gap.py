"""
Tests for app.billing.services.edi_builder, focused on the rate-gap gate:
a claim line carrying rate_gap_reason (a known unpriced CMS period) must
never be allowed to reach an actual 837I submission, since its dollar
amount is a real under-count, not an intentional $0.00.
"""

from __future__ import annotations

import pytest

from app.billing.services.edi_builder import EDIBuilderError, build_837i_text
from app.billing.services.claim_export_service import _build_claim_lines


def _valid_payload(claim_lines):
    return {
        "claim_header": {
            "claim_control_number": "CCN-1",
            "total_estimated_amount": "100.00",
        },
        "patient": {
            "patient_name": "DOE, JANE",
            "date_of_birth": "1940-01-01",
            "subscriber_id": "1EG4TE5MK73",
            "subscriber_id_type": "MBI",
        },
        "diagnosis": {"primary_diagnosis": "C34.90"},
        "payer": {
            "primary_payer": {"payer_name": "MEDICARE", "payer_type": "MEDICARE"}
        },
        "provider": {
            "agency_name": "LOVE AND FAITH HOSPICE",
            "npi": "1234567890",
            "tax_id": "123456789",
        },
        "attending_provider": {
            "first_name": "JOHN",
            "last_name": "SMITH",
            "npi": "9876543210",
        },
        "rendering_provider": {},
        "certifying_provider": {},
        "claim_lines": claim_lines,
    }


def test_build_837i_text_succeeds_for_clean_claim_line():
    claim_lines = [
        {
            "revenue_code": "0651",
            "estimated_amount": "100.00",
            "days": 5,
            "rate_gap_reason": None,
        }
    ]

    edi_text = build_837i_text(_valid_payload(claim_lines))

    assert "CLM*CCN-1*100.00" in edi_text
    assert "SV2*0651*100.00*UN*5" in edi_text


def test_build_837i_text_rejects_claim_line_with_unresolved_rate_gap():
    claim_lines = [
        {
            "revenue_code": "0651",
            "estimated_amount": "0.00",
            "days": 5,
            "rate_gap_reason": "FY2027 CMS rate table not yet populated",
        }
    ]

    with pytest.raises(EDIBuilderError, match="rate gap"):
        build_837i_text(_valid_payload(claim_lines))


def test_build_claim_lines_propagates_rate_gap_reason_from_snapshot():
    snapshot = {
        "claim_lines": [
            {
                "revenue_code": "0651",
                "from_date": "2026-05-01",
                "to_date": "2026-05-05",
                "days": 5,
                "loc": "ROUTINE",
                "pos": "HOME",
                "rate": "0.00",
                "estimated_amount": "0.00",
                "rate_gap_reason": "FY2027 CMS rate table not yet populated",
            }
        ]
    }

    result = _build_claim_lines(snapshot)

    assert result[0]["rate_gap_reason"] == "FY2027 CMS rate table not yet populated"
