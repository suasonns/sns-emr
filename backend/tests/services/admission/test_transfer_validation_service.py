from types import SimpleNamespace

from app.services.admission.transfer_validation_service import (
    TransferValidationService,
)


def build_transfer(
    *,
    is_transfer=True,
    transfer_form_uploaded=True,
    transfer_eligibility_complete=True,
    benefit_period_verified=True,
    days_used_verified=True,
    days_remaining_verified=True,
    transfer_effective_date=True,
    transfer_orders_present=True,
    transfer_cti_present=True,
):
    return SimpleNamespace(
        is_transfer=is_transfer,
        transfer_form_uploaded=transfer_form_uploaded,
        transfer_eligibility_complete=transfer_eligibility_complete,
        benefit_period_verified=benefit_period_verified,
        days_used_verified=days_used_verified,
        days_remaining_verified=days_remaining_verified,
        transfer_effective_date=transfer_effective_date,
        transfer_orders_present=transfer_orders_present,
        transfer_cti_present=transfer_cti_present,
    )


# =========================================================
# NON-TRANSFER
# =========================================================

def test_non_transfer_patient_passes():
    patient = build_transfer(
        is_transfer=False
    )

    result = TransferValidationService.evaluate(
        patient
    )

    assert result["ready"] is True
    assert result["blockers"] == []


# =========================================================
# FULLY VERIFIED TRANSFER
# =========================================================

def test_transfer_fully_verified():
    patient = build_transfer()

    result = TransferValidationService.evaluate(
        patient
    )

    assert result["ready"] is True
    assert result["blockers"] == []


# =========================================================
# TRANSFER FORM
# =========================================================

def test_missing_transfer_form():
    patient = build_transfer(
        transfer_form_uploaded=False
    )

    result = TransferValidationService.evaluate(
        patient
    )

    assert result["ready"] is False
    assert "Transfer form missing" in result["blockers"]


# =========================================================
# ELIGIBILITY
# =========================================================

def test_missing_transfer_eligibility():
    patient = build_transfer(
        transfer_eligibility_complete=False
    )

    result = TransferValidationService.evaluate(
        patient
    )

    assert result["ready"] is False
    assert (
        "Transfer eligibility incomplete"
        in result["blockers"]
    )


# =========================================================
# BENEFIT PERIOD
# =========================================================

def test_missing_benefit_period():
    patient = build_transfer(
        benefit_period_verified=False
    )

    result = TransferValidationService.evaluate(
        patient
    )

    assert result["ready"] is False
    assert (
        "Benefit period not verified"
        in result["blockers"]
    )


# =========================================================
# DAYS USED
# =========================================================

def test_missing_days_used():
    patient = build_transfer(
        days_used_verified=False
    )

    result = TransferValidationService.evaluate(
        patient
    )

    assert result["ready"] is False
    assert (
        "Days used not verified"
        in result["blockers"]
    )


# =========================================================
# DAYS REMAINING
# =========================================================

def test_missing_days_remaining():
    patient = build_transfer(
        days_remaining_verified=False
    )

    result = TransferValidationService.evaluate(
        patient
    )

    assert result["ready"] is False
    assert (
        "Days remaining not verified"
        in result["blockers"]
    )


# =========================================================
# TRANSFER EFFECTIVE DATE
# =========================================================

def test_missing_transfer_effective_date():
    patient = build_transfer(
        transfer_effective_date=False
    )

    result = TransferValidationService.evaluate(
        patient
    )

    assert result["ready"] is False
    assert (
        "Transfer effective date missing"
        in result["blockers"]
    )


# =========================================================
# TRANSFER ORDERS
# =========================================================

def test_missing_transfer_orders():
    patient = build_transfer(
        transfer_orders_present=False
    )

    result = TransferValidationService.evaluate(
        patient
    )

    assert result["ready"] is False
    assert (
        "Transfer orders missing"
        in result["blockers"]
    )


# =========================================================
# TRANSFER CTI
# =========================================================

def test_missing_transfer_cti():
    patient = build_transfer(
        transfer_cti_present=False
    )

    result = TransferValidationService.evaluate(
        patient
    )

    assert result["ready"] is False
    assert (
        "Transfer CTI missing"
        in result["blockers"]
    )


# =========================================================
# MULTIPLE BLOCKERS
# =========================================================

def test_multiple_transfer_blockers():
    patient = build_transfer(
        transfer_form_uploaded=False,
        transfer_orders_present=False,
        transfer_cti_present=False,
    )

    result = TransferValidationService.evaluate(
        patient
    )

    assert result["ready"] is False

    assert len(result["blockers"]) == 3

    assert (
        "Transfer form missing"
        in result["blockers"]
    )

    assert (
        "Transfer orders missing"
        in result["blockers"]
    )

    assert (
        "Transfer CTI missing"
        in result["blockers"]
    )