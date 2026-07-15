from types import SimpleNamespace

from app.services.admission.admission_service import (
    AdmissionService,
)
from app.services.admission.admission_status_engine import (
    AdmissionStatus,
)


def build_patient(
    *,
    primary_diagnosis=True,
    primary_payer=True,
    admission_order_present=True,
    rn_assigned=True,
    clinical_evidence_complete=True,
    requires_eligibility=False,
    eligibility_complete=True,
    is_transfer=False,
    transfer_verified=True,
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
        primary_diagnosis=primary_diagnosis,
        primary_payer=primary_payer,
        admission_order_present=admission_order_present,
        rn_assigned=rn_assigned,
        clinical_evidence_complete=clinical_evidence_complete,
        requires_eligibility=requires_eligibility,
        eligibility_complete=eligibility_complete,
        is_transfer=is_transfer,
        transfer_verified=transfer_verified,
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
# CAN ADMIT
# =========================================================

def test_patient_can_admit():
    patient = build_patient()

    result = AdmissionService.can_admit(
        patient=patient,
    )

    assert result["allowed"] is True
    assert result["blockers"] == []


def test_patient_cannot_admit_missing_diagnosis():
    patient = build_patient(
        primary_diagnosis=False,
    )

    result = AdmissionService.can_admit(
        patient=patient,
    )

    assert result["allowed"] is False

    assert (
        "Primary diagnosis not established"
        in result["blockers"]
    )


def test_patient_cannot_admit_missing_order():
    patient = build_patient(
        admission_order_present=False,
    )

    result = AdmissionService.can_admit(
        patient=patient,
    )

    assert result["allowed"] is False

    assert (
        "Hospice admission order missing"
        in result["blockers"]
    )


# =========================================================
# ELIGIBILITY
# =========================================================

def test_patient_cannot_admit_missing_eligibility():
    patient = build_patient(
        requires_eligibility=True,
        eligibility_complete=False,
    )

    result = AdmissionService.can_admit(
        patient=patient,
    )

    assert result["allowed"] is False

    assert (
        "Eligibility incomplete"
        in result["blockers"]
    )


# =========================================================
# TRANSFER VALIDATION
# =========================================================

def test_transfer_patient_can_admit():
    patient = build_patient(
        is_transfer=True,
    )

    result = AdmissionService.can_admit(
        patient=patient,
    )

    assert result["allowed"] is True


def test_transfer_patient_missing_form():
    patient = build_patient(
        is_transfer=True,
        transfer_form_uploaded=False,
    )

    result = AdmissionService.can_admit(
        patient=patient,
    )

    assert result["allowed"] is False

    assert (
        "Transfer form missing"
        in result["blockers"]
    )


def test_transfer_patient_missing_cti():
    patient = build_patient(
        is_transfer=True,
        transfer_cti_present=False,
    )

    result = AdmissionService.can_admit(
        patient=patient,
    )

    assert result["allowed"] is False

    assert (
        "Transfer CTI missing"
        in result["blockers"]
    )


# =========================================================
# STATUS TRANSITION SUCCESS
# =========================================================

def test_valid_status_transition():
    patient = build_patient()

    result = (
        AdmissionService.validate_status_change(
            patient=patient,
            current_status=AdmissionStatus.REFERRAL,
            target_status=AdmissionStatus.POTENTIAL_ADMISSION,
            role="ADMIN",
        )
    )

    assert result["allowed"] is True


# =========================================================
# ROLE FAILURE
# =========================================================

def test_invalid_role_transition():
    patient = build_patient()

    result = (
        AdmissionService.validate_status_change(
            patient=patient,
            current_status=AdmissionStatus.REFERRAL,
            target_status=AdmissionStatus.POTENTIAL_ADMISSION,
            role="MARKETER",
        )
    )

    assert result["allowed"] is False


# =========================================================
# INVALID PATH
# =========================================================

def test_invalid_status_path():
    patient = build_patient()

    result = (
        AdmissionService.validate_status_change(
            patient=patient,
            current_status=AdmissionStatus.REFERRAL,
            target_status=AdmissionStatus.ADMITTED,
            role="ADMIN",
        )
    )

    assert result["allowed"] is False


# =========================================================
# ADMITTED STATUS REQUIRES READINESS
# =========================================================

def test_admitted_requires_readiness():
    patient = build_patient(
        primary_diagnosis=False,
    )

    result = (
        AdmissionService.validate_status_change(
            patient=patient,
            current_status=AdmissionStatus.SOC_IN_PROGRESS,
            target_status=AdmissionStatus.ADMITTED,
            role="ADMIN",
        )
    )

    assert result["allowed"] is False

    assert (
        "Primary diagnosis not established"
        in result["blockers"]
    )


# =========================================================
# ADMITTED SUCCESS
# =========================================================

def test_admitted_success():
    patient = build_patient()

    result = (
        AdmissionService.validate_status_change(
            patient=patient,
            current_status=AdmissionStatus.SOC_IN_PROGRESS,
            target_status=AdmissionStatus.ADMITTED,
            role="ADMIN",
        )
    )

    assert result["allowed"] is True


# =========================================================
# SUMMARY
# =========================================================

def test_admission_summary_ready():
    patient = build_patient()

    result = AdmissionService.get_admission_summary(
        patient=patient,
    )

    assert result["ready_for_soc"] is True
    assert result["blocker_count"] == 0


def test_admission_summary_not_ready():
    patient = build_patient(
        primary_diagnosis=False,
        admission_order_present=False,
    )

    result = AdmissionService.get_admission_summary(
        patient=patient,
    )

    assert result["ready_for_soc"] is False
    assert result["blocker_count"] == 2