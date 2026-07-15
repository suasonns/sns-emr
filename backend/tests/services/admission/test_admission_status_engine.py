import pytest

from app.services.admission.admission_status_engine import (
    AdmissionStatus,
    AdmissionStatusEngine,
)


# =========================================================
# STATUS TRANSITIONS
# =========================================================

def test_referral_to_potential_admission_allowed():
    assert AdmissionStatusEngine.can_transition(
        AdmissionStatus.REFERRAL,
        AdmissionStatus.POTENTIAL_ADMISSION,
    )


def test_referral_to_non_admit_allowed():
    assert AdmissionStatusEngine.can_transition(
        AdmissionStatus.REFERRAL,
        AdmissionStatus.NON_ADMIT,
    )


def test_referral_to_admitted_not_allowed():
    assert not AdmissionStatusEngine.can_transition(
        AdmissionStatus.REFERRAL,
        AdmissionStatus.ADMITTED,
    )


def test_potential_admission_to_scheduled_allowed():
    assert AdmissionStatusEngine.can_transition(
        AdmissionStatus.POTENTIAL_ADMISSION,
        AdmissionStatus.ADMISSION_SCHEDULED,
    )


def test_potential_admission_to_transfer_pending_allowed():
    assert AdmissionStatusEngine.can_transition(
        AdmissionStatus.POTENTIAL_ADMISSION,
        AdmissionStatus.TRANSFER_PENDING,
    )


def test_admission_scheduled_to_soc_allowed():
    assert AdmissionStatusEngine.can_transition(
        AdmissionStatus.ADMISSION_SCHEDULED,
        AdmissionStatus.SOC_IN_PROGRESS,
    )


def test_soc_to_admitted_allowed():
    assert AdmissionStatusEngine.can_transition(
        AdmissionStatus.SOC_IN_PROGRESS,
        AdmissionStatus.ADMITTED,
    )


def test_admitted_has_no_valid_forward_transition():
    assert AdmissionStatusEngine.ALLOWED_TRANSITIONS[
        AdmissionStatus.ADMITTED
    ] == []


def test_non_admit_has_no_valid_forward_transition():
    assert AdmissionStatusEngine.ALLOWED_TRANSITIONS[
        AdmissionStatus.NON_ADMIT
    ] == []


# =========================================================
# ROLE AUTHORIZATION
# =========================================================

@pytest.mark.parametrize(
    "role",
    [
        "ADMIN",
        "CASE_MANAGER",
        "DPCS",
        "DPCS_DESIGNEE",
        "ASSIGNED_RN",
        "MEDICAL_DIRECTOR",
        "MEDICAL_DIRECTOR_DESIGNEE",
        "ASSOCIATE_MEDICAL_DIRECTOR",
    ],
)
def test_authorized_roles(role):
    assert AdmissionStatusEngine.role_can_change_status(
        role
    )


@pytest.mark.parametrize(
    "role",
    [
        "MARKETER",
        "CHHA",
        "SC",
        "MSW",
        "INTAKE_COORDINATOR",
        "SCHEDULER",
    ],
)
def test_unauthorized_roles(role):
    assert not AdmissionStatusEngine.role_can_change_status(
        role
    )


# =========================================================
# VALIDATION
# =========================================================

def test_validate_transition_success():
    result = AdmissionStatusEngine.validate_transition(
        current_status=AdmissionStatus.REFERRAL,
        target_status=AdmissionStatus.POTENTIAL_ADMISSION,
        role="ADMIN",
    )

    assert result["allowed"] is True


def test_validate_transition_invalid_role():
    result = AdmissionStatusEngine.validate_transition(
        current_status=AdmissionStatus.REFERRAL,
        target_status=AdmissionStatus.POTENTIAL_ADMISSION,
        role="MARKETER",
    )

    assert result["allowed"] is False


def test_validate_transition_invalid_status_path():
    result = AdmissionStatusEngine.validate_transition(
        current_status=AdmissionStatus.REFERRAL,
        target_status=AdmissionStatus.ADMITTED,
        role="ADMIN",
    )

    assert result["allowed"] is False


# =========================================================
# TASK VISIBILITY
# =========================================================

def test_referral_tasks_visible():
    tasks = AdmissionStatusEngine.get_visible_tasks(
        AdmissionStatus.REFERRAL
    )

    assert "REFERRAL_INTAKE" in tasks
    assert "CLINICAL_RECORD_REQUEST" in tasks


def test_rn_ica_hidden_before_admission():
    hidden = AdmissionStatusEngine.get_hidden_tasks(
        AdmissionStatus.ADMISSION_SCHEDULED
    )

    assert "RN_ICA" in hidden


def test_cti_hidden_before_admission():
    hidden = AdmissionStatusEngine.get_hidden_tasks(
        AdmissionStatus.POTENTIAL_ADMISSION
    )

    assert "CTI_WORKFLOW" in hidden


def test_admitted_tasks_visible():
    tasks = AdmissionStatusEngine.get_visible_tasks(
        AdmissionStatus.ADMITTED
    )

    assert "RN_ICA" in tasks
    assert "POC_WORKFLOW" in tasks
    assert "CTI_WORKFLOW" in tasks


def test_non_admit_tasks():
    tasks = AdmissionStatusEngine.get_visible_tasks(
        AdmissionStatus.NON_ADMIT
    )

    assert "NON_ADMIT_DOCUMENTATION" in tasks
    assert "REFERRAL_CLOSURE" in tasks