"""
Tests for app.billing.services.msp_validation_service -- the Medicare
Secondary Payer (MSP) claim-sequencing engine. These lock in the real CMS
rule that an active MSP-type payer must always be sequenced primary to
Medicare, and that any genuine ambiguity in payer ordering is surfaced as
a hard conflict rather than silently defaulting to "Medicare primary".
"""

from __future__ import annotations

from datetime import date

import pytest

from app.billing.services.msp_validation_service import (
    MSP_VALUE_CODES,
    MspValidationError,
    build_msp_value_codes_for_claim,
    resolve_payer_sequence,
    validate_msp_type_code,
)


SERVICE_DATE = date(2026, 5, 15)


def _medicare(**overrides):
    base = {
        "id": "medicare-1",
        "payer_name": "MEDICARE",
        "payer_type": "MEDICARE",
        "subscriber_id": "1EG4TE5MK73",
        "subscriber_id_type": "MBI",
        "effective_start_date": date(2020, 1, 1),
        "end_date": None,
        "is_primary": True,
        "msp_type_code": None,
        "priority_order": None,
    }
    base.update(overrides)
    return base


def _payer(**overrides):
    base = {
        "id": "payer-1",
        "payer_name": "ACME WORKERS COMP",
        "payer_type": "WORKERS_COMP",
        "subscriber_id": "WC12345",
        "subscriber_id_type": "MI",
        "effective_start_date": date(2026, 1, 1),
        "end_date": None,
        "is_primary": False,
        "msp_type_code": None,
        "priority_order": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------
# validate_msp_type_code
# ---------------------------------------------------------------------


def test_validate_msp_type_code_accepts_known_codes():
    for code in MSP_VALUE_CODES:
        validate_msp_type_code(code)  # must not raise


def test_validate_msp_type_code_accepts_none():
    validate_msp_type_code(None)


def test_validate_msp_type_code_rejects_unknown_code():
    with pytest.raises(MspValidationError):
        validate_msp_type_code("99")


# ---------------------------------------------------------------------
# resolve_payer_sequence -- baseline / no-MSP scenarios
# ---------------------------------------------------------------------


def test_single_medicare_payer_resolves_as_primary():
    result = resolve_payer_sequence([_medicare()], service_date=SERVICE_DATE)

    assert result.has_conflict is False
    assert len(result.payers) == 1
    assert result.primary.payer_type == "MEDICARE"
    assert result.primary.sequence_code == "P"


def test_no_payers_on_file_is_a_conflict():
    result = resolve_payer_sequence([], service_date=SERVICE_DATE)

    assert result.has_conflict is True
    assert "No payers on file" in result.conflict_reason


def test_no_active_payer_on_service_date_is_a_conflict():
    lapsed = _medicare(end_date=date(2025, 12, 31))
    result = resolve_payer_sequence([lapsed], service_date=SERVICE_DATE)

    assert result.has_conflict is True
    assert "active coverage window" in result.conflict_reason


def test_future_effective_payer_is_ignored_as_inactive():
    future_payer = _payer(effective_start_date=date(2027, 1, 1))
    result = resolve_payer_sequence(
        [_medicare(), future_payer], service_date=SERVICE_DATE
    )

    assert result.has_conflict is False
    assert len(result.payers) == 1
    assert result.primary.payer_type == "MEDICARE"


def test_medicare_payer_carrying_msp_type_code_is_a_conflict():
    bad_medicare = _medicare(msp_type_code="15")
    result = resolve_payer_sequence([bad_medicare], service_date=SERVICE_DATE)

    assert result.has_conflict is True
    assert "should never itself carry" in result.conflict_reason or "msp_type_code" in result.conflict_reason


def test_two_active_medicare_payers_is_a_conflict():
    result = resolve_payer_sequence(
        [_medicare(id="m1"), _medicare(id="m2")], service_date=SERVICE_DATE
    )

    assert result.has_conflict is True
    assert "one active Medicare payer" in result.conflict_reason


def test_unknown_msp_type_code_on_a_payer_is_a_conflict():
    bad_payer = _payer(msp_type_code="99")
    result = resolve_payer_sequence(
        [_medicare(), bad_payer], service_date=SERVICE_DATE
    )

    assert result.has_conflict is True
    assert "Unknown MSP type code" in result.conflict_reason


# ---------------------------------------------------------------------
# resolve_payer_sequence -- real MSP scenarios (no explicit priority_order)
# ---------------------------------------------------------------------


def test_active_msp_payer_is_auto_sequenced_ahead_of_medicare():
    wc_payer = _payer(msp_type_code="15")  # Workers' Comp
    result = resolve_payer_sequence([_medicare(), wc_payer], service_date=SERVICE_DATE)

    assert result.has_conflict is False
    assert result.payers[0].payer_type == "WORKERS_COMP"
    assert result.payers[0].sequence_code == "P"
    assert result.payers[0].msp_type_code == "15"
    assert result.payers[1].payer_type == "MEDICARE"
    assert result.payers[1].sequence_code == "S"


def test_two_active_msp_payers_with_no_ordering_is_a_conflict():
    wc_payer = _payer(id="wc", payer_name="WORKERS COMP", msp_type_code="15")
    liability_payer = _payer(id="liab", payer_name="AUTO LIABILITY", payer_type="LIABILITY", msp_type_code="47")

    result = resolve_payer_sequence(
        [_medicare(), wc_payer, liability_payer], service_date=SERVICE_DATE
    )

    assert result.has_conflict is True
    assert "Multiple active MSP-type payers" in result.conflict_reason


def test_msp_payer_and_conflicting_is_primary_flag_is_a_conflict():
    wc_payer = _payer(msp_type_code="15")
    other_payer = _payer(
        id="other", payer_name="SUPPLEMENTAL PLAN", payer_type="COMMERCIAL", is_primary=True
    )

    result = resolve_payer_sequence(
        [_medicare(), wc_payer, other_payer], service_date=SERVICE_DATE
    )

    assert result.has_conflict is True
    assert "contradictory payer data" in result.conflict_reason


def test_msp_payer_plus_unflagged_tertiary_payer_orders_deterministically():
    wc_payer = _payer(msp_type_code="15")
    supplemental = _payer(
        id="supp",
        payer_name="AARP SUPPLEMENT",
        payer_type="COMMERCIAL",
        is_primary=False,
        effective_start_date=date(2021, 1, 1),
    )

    result = resolve_payer_sequence(
        [_medicare(), wc_payer, supplemental], service_date=SERVICE_DATE
    )

    assert result.has_conflict is False
    assert [p.payer_type for p in result.payers] == ["WORKERS_COMP", "MEDICARE", "COMMERCIAL"]
    assert [p.sequence_code for p in result.payers] == ["P", "S", "T"]


def test_no_msp_payer_multiple_is_primary_flags_is_a_conflict():
    payer_a = _payer(id="a", payer_name="PLAN A", is_primary=True)
    payer_b = _payer(id="b", payer_name="PLAN B", is_primary=True)

    result = resolve_payer_sequence(
        [_medicare(is_primary=False), payer_a, payer_b], service_date=SERVICE_DATE
    )

    assert result.has_conflict is True
    assert "Multiple payers flagged is_primary" in result.conflict_reason


def test_no_msp_no_flags_multiple_non_medicare_payers_is_a_conflict():
    payer_a = _payer(id="a", payer_name="PLAN A", is_primary=False)
    payer_b = _payer(id="b", payer_name="PLAN B", is_primary=False)

    result = resolve_payer_sequence([payer_a, payer_b], service_date=SERVICE_DATE)

    assert result.has_conflict is True
    assert "cannot be determine" in result.conflict_reason.lower() or "cannot determine" in result.conflict_reason.lower()


def test_is_primary_flag_alone_resolves_sequence_when_unambiguous():
    payer_a = _payer(id="a", payer_name="PLAN A", is_primary=True)

    result = resolve_payer_sequence(
        [_medicare(is_primary=False), payer_a], service_date=SERVICE_DATE
    )

    assert result.has_conflict is False
    assert result.payers[0].payer_name == "PLAN A"
    assert result.payers[0].sequence_code == "P"
    assert result.payers[1].payer_type == "MEDICARE"
    assert result.payers[1].sequence_code == "S"


# ---------------------------------------------------------------------
# resolve_payer_sequence -- explicit priority_order scenarios
# ---------------------------------------------------------------------


def test_explicit_priority_order_is_authoritative():
    wc_payer = _payer(msp_type_code="15", priority_order=1)
    medicare = _medicare(priority_order=2)

    result = resolve_payer_sequence([medicare, wc_payer], service_date=SERVICE_DATE)

    assert result.has_conflict is False
    assert result.payers[0].payer_type == "WORKERS_COMP"
    assert result.payers[1].payer_type == "MEDICARE"


def test_explicit_order_placing_msp_payer_after_medicare_is_a_conflict():
    wc_payer = _payer(msp_type_code="15", priority_order=2)
    medicare = _medicare(priority_order=1)

    result = resolve_payer_sequence([medicare, wc_payer], service_date=SERVICE_DATE)

    assert result.has_conflict is True
    assert "sequenced AFTER Medicare" in result.conflict_reason


def test_partial_explicit_ordering_is_a_conflict():
    payer_a = _payer(id="a", priority_order=1)
    payer_b = _payer(id="b", payer_name="PLAN B", priority_order=None)

    result = resolve_payer_sequence(
        [_medicare(priority_order=None), payer_a, payer_b], service_date=SERVICE_DATE
    )

    assert result.has_conflict is True
    assert "all-or-nothing" in result.conflict_reason


def test_duplicate_priority_order_is_a_conflict():
    payer_a = _payer(id="a", priority_order=1)
    medicare = _medicare(priority_order=1)

    result = resolve_payer_sequence([medicare, payer_a], service_date=SERVICE_DATE)

    assert result.has_conflict is True
    assert "same priority_order" in result.conflict_reason


def test_non_gapless_priority_order_is_a_conflict():
    payer_a = _payer(id="a", priority_order=1)
    medicare = _medicare(priority_order=5)

    result = resolve_payer_sequence([medicare, payer_a], service_date=SERVICE_DATE)

    assert result.has_conflict is True
    assert "clean 1.." in result.conflict_reason


# ---------------------------------------------------------------------
# build_msp_value_codes_for_claim
# ---------------------------------------------------------------------


def test_build_msp_value_codes_returns_entry_for_msp_payer():
    wc_payer = _payer(msp_type_code="15")
    sequence = resolve_payer_sequence([_medicare(), wc_payer], service_date=SERVICE_DATE)

    value_codes = build_msp_value_codes_for_claim(sequence)

    assert len(value_codes) == 1
    assert value_codes[0]["value_code"] == "15"
    assert value_codes[0]["description"] == "Workers' Compensation"


def test_build_msp_value_codes_empty_when_no_msp_payer():
    sequence = resolve_payer_sequence([_medicare()], service_date=SERVICE_DATE)

    assert build_msp_value_codes_for_claim(sequence) == []
