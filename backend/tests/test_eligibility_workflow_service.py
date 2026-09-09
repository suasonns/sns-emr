"""
Tests for app.billing.services.eligibility_workflow_service -- Phases 1-4
of the Eligibility, Admission, Benefit-Period, and Billing-Readiness
Workflow Correction directive: recording eligibility source documents,
payer-eligibility verifications, benefit-period determinations, and the
Phase 4 admission gate derived from them.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.billing.services.billing_readiness_service import check_patient_billing_readiness
from app.billing.services.eligibility_workflow_service import (
    BENEFIT_PERIOD_REVIEW_BLOCKER_MESSAGE,
    ELIGIBILITY_REVIEW_BLOCKER_MESSAGE,
    evaluate_admission_gate,
    get_latest_benefit_period_determination,
    get_latest_eligibility_verification,
    record_benefit_period_determination,
    record_eligibility_source_document,
    record_eligibility_verification,
)
from app.models.document_record import DocumentRecord
from app.models.patient import Patient
from app.models.user import User

from tests.test_billing_readiness_service import (
    _fully_ready_patient,
    _make_admitted,
    _make_patient,
)

SERVICE_DATE = date(2026, 3, 15)


def _make_user(db_session, tenant_id: str, *, role: str = "RN") -> uuid.UUID:
    user_id = uuid.uuid4()
    db_session.add(
        User(
            id=user_id,
            tenant_id=uuid.UUID(str(tenant_id)),
            email=f"{user_id.hex[:8]}@example.com",
            full_name="Test Staff Member",
            role=role,
        )
    )
    db_session.commit()
    return user_id


def _make_document_record(db_session, tenant_id: str, patient: Patient, user_id: uuid.UUID) -> DocumentRecord:
    doc = DocumentRecord(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
        source="EXTERNAL",
        file_name="eligibility-report.pdf",
        uploaded_by=user_id,
        created_by=user_id,
    )
    db_session.add(doc)
    db_session.commit()
    return doc


# ---------------------------------------------------------------------
# Phase 1 -- eligibility source document
# ---------------------------------------------------------------------


def test_record_eligibility_source_document_creates_active_row(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-ELIG-DOC-1")
    user_id = _make_user(db_session, tenant.id)
    doc_record = _make_document_record(db_session, tenant.id, patient, user_id)

    esd = record_eligibility_source_document(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        document_record_id=str(doc_record.id),
        document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
        uploaded_by_user_id=str(user_id),
        verification_date=date(2026, 2, 1),
    )

    assert esd.status == "ACTIVE"
    assert esd.document_record_id == doc_record.id


def test_superseding_document_marks_prior_superseded(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-ELIG-DOC-2")
    user_id = _make_user(db_session, tenant.id)
    doc_record_1 = _make_document_record(db_session, tenant.id, patient, user_id)
    doc_record_2 = _make_document_record(db_session, tenant.id, patient, user_id)

    original = record_eligibility_source_document(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        document_record_id=str(doc_record_1.id),
        document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
        uploaded_by_user_id=str(user_id),
    )

    newer = record_eligibility_source_document(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        document_record_id=str(doc_record_2.id),
        document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
        uploaded_by_user_id=str(user_id),
        supersedes_document_id=str(original.id),
    )

    db_session.refresh(original)
    assert original.status == "SUPERSEDED"
    assert newer.status == "ACTIVE"
    assert newer.supersedes_document_id == original.id


# ---------------------------------------------------------------------
# Phase 2 -- eligibility verification (append-only reverification)
# ---------------------------------------------------------------------


def test_reverification_appends_and_supersedes_prior(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-ELIG-VER-1")
    user_id = _make_user(db_session, tenant.id)
    doc_record = _make_document_record(db_session, tenant.id, patient, user_id)
    esd = record_eligibility_source_document(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        document_record_id=str(doc_record.id),
        document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
        uploaded_by_user_id=str(user_id),
    )

    intake_verification = record_eligibility_verification(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        source_document_id=str(esd.id),
        verified_by_user_id=str(user_id),
        status="VERIFIED_ACTIVE",
        verification_method="MANUAL_ENTRY",
    )

    # Biller's later reverification must APPEND, not overwrite.
    biller_verification = record_eligibility_verification(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        source_document_id=str(esd.id),
        verified_by_user_id=str(user_id),
        status="VERIFIED_ACTIVE",
        verification_method="PORTAL_CHECK",
    )

    db_session.refresh(intake_verification)
    assert intake_verification.superseded_at is not None  # marked current-vs-not, never deleted
    assert biller_verification.superseded_at is None
    assert intake_verification.id != biller_verification.id

    latest = get_latest_eligibility_verification(db_session, tenant_id=tenant.id, patient_id=str(patient.id))
    assert latest.id == biller_verification.id


# ---------------------------------------------------------------------
# Phase 3 -- benefit-period determination
# ---------------------------------------------------------------------


def test_determination_never_manufactures_a_period_number_when_incomplete(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-BPD-1")
    determination = record_benefit_period_determination(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        determination_status="INFORMATION_INCOMPLETE",
    )
    assert determination.anticipated_benefit_period_number is None
    assert determination.determination_status == "INFORMATION_INCOMPLETE"


def test_correction_supersedes_prior_determination_append_only(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-BPD-2")
    user_id = _make_user(db_session, tenant.id, role="RN")

    first = record_benefit_period_determination(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        determination_status="CONFLICT_REQUIRES_REVIEW",
        conflict_reason="Prior hospice episode count unclear from source document.",
    )

    corrected = record_benefit_period_determination(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        determination_status="BENEFIT_PERIOD_CONFIRMED",
        anticipated_benefit_period_number=1,
        determined_by_user_id=str(user_id),
        supersedes_determination_id=str(first.id),
    )

    db_session.refresh(first)
    assert first.superseded_at is not None
    assert first.superseded_by_id == corrected.id
    assert corrected.determination_status == "BENEFIT_PERIOD_CONFIRMED"

    latest = get_latest_benefit_period_determination(db_session, tenant_id=tenant.id, patient_id=str(patient.id))
    assert latest.id == corrected.id


# ---------------------------------------------------------------------
# Phase 4 -- admission gate
# ---------------------------------------------------------------------


def test_gate_is_clear_when_no_eligibility_or_determination_rows_exist(db_session, tenant):
    """
    Non-regression rule: a patient with NEITHER row (every pre-existing
    admitted test fixture / legacy record) must never be penalized by
    this new gate.
    """
    patient = _make_patient(db_session, tenant.id, mrn="MRN-GATE-1")
    gate = evaluate_admission_gate(db_session, tenant_id=tenant.id, patient_id=str(patient.id))
    assert gate.gate_status == "CLEAR"
    assert gate.blockers == []


def test_gate_requires_review_when_eligibility_verification_unresolved(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-GATE-2")
    user_id = _make_user(db_session, tenant.id)
    doc_record = _make_document_record(db_session, tenant.id, patient, user_id)
    esd = record_eligibility_source_document(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        document_record_id=str(doc_record.id),
        document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
        uploaded_by_user_id=str(user_id),
    )
    record_eligibility_verification(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        source_document_id=str(esd.id),
        verified_by_user_id=str(user_id),
        status="REVIEW_REQUIRED",
    )

    gate = evaluate_admission_gate(db_session, tenant_id=tenant.id, patient_id=str(patient.id))
    assert gate.gate_status == "ADMISSION_REVIEW_REQUIRED"
    assert ELIGIBILITY_REVIEW_BLOCKER_MESSAGE in gate.blockers


def test_gate_requires_review_when_benefit_period_determination_unresolved(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-GATE-3")
    record_benefit_period_determination(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        determination_status="CONFLICT_REQUIRES_REVIEW",
    )

    gate = evaluate_admission_gate(db_session, tenant_id=tenant.id, patient_id=str(patient.id))
    assert gate.gate_status == "ADMISSION_REVIEW_REQUIRED"
    assert BENEFIT_PERIOD_REVIEW_BLOCKER_MESSAGE in gate.blockers


def test_gate_is_clear_when_both_are_confirmed(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-GATE-4")
    user_id = _make_user(db_session, tenant.id)
    doc_record = _make_document_record(db_session, tenant.id, patient, user_id)
    esd = record_eligibility_source_document(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        document_record_id=str(doc_record.id),
        document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
        uploaded_by_user_id=str(user_id),
    )
    record_eligibility_verification(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        source_document_id=str(esd.id),
        verified_by_user_id=str(user_id),
        status="VERIFIED_ACTIVE",
    )
    record_benefit_period_determination(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        determination_status="BENEFIT_PERIOD_CONFIRMED",
        anticipated_benefit_period_number=1,
        determined_by_user_id=str(user_id),
    )

    gate = evaluate_admission_gate(db_session, tenant_id=tenant.id, patient_id=str(patient.id))
    assert gate.gate_status == "CLEAR"
    assert gate.blockers == []


# ---------------------------------------------------------------------
# Integration: the gate surfaces as an exceptional billing blocker only
# when it fires (Directive item 10 -- never a silent exclusion).
# ---------------------------------------------------------------------


def test_billing_readiness_unaffected_when_no_eligibility_rows_exist(db_session, tenant):
    """
    Every pre-existing test fixture in test_billing_readiness_service.py
    has no EligibilityVerification/BenefitPeriodDetermination row -- this
    confirms the gate really is a no-op for them.
    """
    patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-GATE-INTEGRATION-1")
    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )
    assert result.ready is True
    assert result.blockers == []


def test_billing_readiness_surfaces_exceptional_benefit_period_review_blocker(db_session, tenant):
    patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-GATE-INTEGRATION-2")
    _make_admitted(db_session, tenant.id, patient)
    record_benefit_period_determination(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        determination_status="CONFLICT_REQUIRES_REVIEW",
    )

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )
    assert result.ready is False
    assert BENEFIT_PERIOD_REVIEW_BLOCKER_MESSAGE in result.blockers
