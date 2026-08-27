"""
Tests for app.billing.services.noe_edi_builder -- the real electronic
NOE (TOB 81A) / NOTR (TOB 81B) 837I notice builder.
"""

from __future__ import annotations

import pytest

from app.billing.services.noe_edi_builder import EDIBuilderError, build_notice_837i_text


def _valid_notice_export():
    return {
        "patient": {
            "patient_name": "DOE, JANE",
            "date_of_birth": "1940-01-01",
            "subscriber_id": "1EG4TE5MK73",
            "subscriber_id_type": "MBI",
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
        "payer": {
            "primary_payer": {"payer_name": "MEDICARE", "payer_type": "MEDICARE"}
        },
        "tenant_id": "11111111-1111-1111-1111-111111111111",
    }


def test_build_noe_837i_uses_tob_81a_and_occurrence_code_27():
    edi_text = build_notice_837i_text(
        submission_type="NOE",
        control_number="CCN-NOE-1",
        effective_date="2026-08-01",
        notice_export=_valid_notice_export(),
    )

    assert "8:B:A" in edi_text  # TOB 81A -> CLM05 composite
    assert "CLM*CCN-NOE-1" in edi_text
    assert "HI*BH:27:D8:20260801" in edi_text
    assert "DOE, JANE" in edi_text
    assert "MEDICARE" in edi_text


def test_build_notr_837i_uses_tob_81b_and_occurrence_code_42():
    edi_text = build_notice_837i_text(
        submission_type="NOTR",
        control_number="CCN-NOTR-1",
        effective_date="2026-08-15",
        notice_export=_valid_notice_export(),
    )

    assert "8:B:B" in edi_text  # TOB 81B -> CLM05 composite
    assert "HI*BH:42:D8:20260815" in edi_text


def test_build_notice_837i_rejects_unsupported_submission_type():
    with pytest.raises(EDIBuilderError, match="Unsupported notice submission_type"):
        build_notice_837i_text(
            submission_type="BOGUS",
            control_number="CCN-1",
            effective_date="2026-08-01",
            notice_export=_valid_notice_export(),
        )


def test_build_notice_837i_rejects_missing_patient_section():
    export = _valid_notice_export()
    export["patient"] = {}

    with pytest.raises(EDIBuilderError):
        build_notice_837i_text(
            submission_type="NOE",
            control_number="CCN-1",
            effective_date="2026-08-01",
            notice_export=export,
        )
