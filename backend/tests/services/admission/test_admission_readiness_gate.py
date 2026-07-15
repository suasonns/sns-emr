from types import SimpleNamespace

from app.services.admission.admission_readiness_gate import (
    AdmissionReadinessGate,
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

        transfer_form_uploaded=transfer_form_uploaded,
        transfer_eligibility_complete=transfer_eligibility_complete,
        benefit_period_verified=benefit_period_verified,
        days_used_verified=days_used_verified,
        days_remaining_verified=days_remaining_verified,
        transfer_effective_date=transfer_effective_date,
        transfer_orders_present=transfer_orders_present,
        transfer_cti_present=transfer_cti_present,
    )

# ============================================================
# SUCCESS CASE
# ============================================================

def test_ready_for_admission():
    patient = build_patient()

    result = AdmissionReadinessGate.evaluate(patient)

    assert result["ready"] is True
    assert result["blockers"] == []


# ============================================================
# PRIMARY DIAGNOSIS
# ============================================================

def test_missing_primary_diagnosis():
    patient = build_patient(
        primary_diagnosis=False,
    )

    result = AdmissionReadinessGate.evaluate(patient)

    assert result["ready"] is False

    assert (
        "Primary diagnosis not established"
        in result["blockers"]
    )


# ============================================================
# PRIMARY PAYER
# ============================================================

def test_missing_primary_payer():
    patient = build_patient(
        primary_payer=False,
    )

    result = AdmissionReadinessGate.evaluate(patient)

    assert result["ready"] is False

    assert (
        "Primary payer not selected"
        in result["blockers"]
    )


# ============================================================
# ADMISSION ORDER
# ============================================================

def test_missing_admission_order():
    patient = build_patient(
        admission_order_present=False,
    )

    result = AdmissionReadinessGate.evaluate(patient)

    assert result["ready"] is False

    assert (
        "Hospice admission order missing"
        in result["blockers"]
    )


# ============================================================
# RN ASSIGNMENT
# ============================================================

def test_missing_rn_assignment():
    patient = build_patient(
        rn_assigned=False,
    )

    result = AdmissionReadinessGate.evaluate(patient)

    assert result["ready"] is False

    assert (
        "Admitting RN not assigned"
        in result["blockers"]
    )


# ============================================================
# CLINICAL EVIDENCE
# ============================================================

def test_missing_clinical_evidence():
    patient = build_patient(
        clinical_evidence_complete=False,
    )

    result = AdmissionReadinessGate.evaluate(patient)

    assert result["ready"] is False

    assert (
        "Clinical evidence packet incomplete"
        in result["blockers"]
    )


# ============================================================
# ELIGIBILITY
# ============================================================

def test_eligibility_required_and_missing():
    patient = build_patient(
        requires_eligibility=True,
        eligibility_complete=False,
    )

    result = AdmissionReadinessGate.evaluate(patient)

    assert result["ready"] is False

    assert (
        "Eligibility incomplete"
        in result["blockers"]
    )


def test_eligibility_not_required():
    patient = build_patient(
        requires_eligibility=False,
        eligibility_complete=False,
    )

    result = AdmissionReadinessGate.evaluate(patient)

    assert result["ready"] is True


# ============================================================
# TRANSFER VALIDATION
# ============================================================

def test_transfer_verification_required():
    patient = build_patient(
        is_transfer=True,
        transfer_form_uploaded=False,
    )

    result = AdmissionReadinessGate.evaluate(patient)

    assert result["ready"] is False

    assert (
        "Transfer form missing"
        in result["blockers"]
    )


def test_transfer_verification_complete():
    patient = build_patient(
        is_transfer=True,
    )

    result = AdmissionReadinessGate.evaluate(patient)

    assert result["ready"] is True


# ============================================================
# MULTIPLE BLOCKERS
# ============================================================

def test_multiple_blockers_returned():
    patient = build_patient(
        primary_diagnosis=False,
        admission_order_present=False,
        clinical_evidence_complete=False,
    )

    result = AdmissionReadinessGate.evaluate(patient)

    assert result["ready"] is False
    assert len(result["blockers"]) == 3

    assert (
        "Primary diagnosis not established"
        in result["blockers"]
    )

    assert (
        "Hospice admission order missing"
        in result["blockers"]
    )

    assert (
        "Clinical evidence packet incomplete"
        in result["blockers"]
    )