"""Tests for the RNICA structured-findings application layer's read/review
functions -- list_pending_structured_findings() and
review_harvested_signal() in app.services.evidence.harvest_service, and
build_rnica_intelligence()'s structured_findings_signals wiring.

These exercise the API surface a clinician-facing "Apply to RNICA
field(s)" workflow depends on: listing pending structured findings for a
patient, and recording a reviewed disposition once the RN has acted on
them. Nothing here writes into a chart record itself -- that is
applyStructuredFindings.js's job on the frontend.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.models.patient import Patient
from app.models.patient_evidence import PatientEvidenceRecord, PatientHarvestedSignal
from app.services.evidence.harvest_service import (
    list_pending_structured_findings,
    review_harvested_signal,
)
from app.services.rnica_intelligence import build_rnica_intelligence
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id: uuid.UUID) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"SFA-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Structured findings application-layer test",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_evidence_record(db_session, *, tenant_id, patient_id) -> PatientEvidenceRecord:
    record = PatientEvidenceRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        source_type="REFERRAL_HNP",
        source_record_id=uuid.uuid4(),
        recorded_at=datetime.now(timezone.utc),
        recorded_by_user_id=TEST_USER_ID,
        recorded_by_name="Test User",
        original_documentation="Right hemiparesis after prior stroke; right foot wound noted.",
    )
    db_session.add(record)
    db_session.commit()
    return record


def _make_signal(
    db_session,
    *,
    tenant_id,
    patient_id,
    evidence_record_id,
    structured_findings,
    review_status="NEW",
) -> PatientHarvestedSignal:
    signal = PatientHarvestedSignal(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        evidence_record_id=evidence_record_id,
        source_type="REFERRAL_HNP",
        recorded_at=datetime.now(timezone.utc),
        signal_key="right_hemiparesis",
        signal_text="Right hemiparesis after prior stroke.",
        original_text_excerpt="Right hemiparesis after prior stroke.",
        clinical_system="neurological",
        requires_idg_review=False,
        requires_poc_review=False,
        review_status=review_status,
        structured_findings=structured_findings,
    )
    db_session.add(signal)
    db_session.commit()
    return signal


_SAMPLE_FINDING = {
    "concept_code": "NEURO_HEMIPARESIS_RIGHT",
    "value": True,
    "source_type": "REFERRAL_HNP",
    "source_excerpt": "Right hemiparesis after prior stroke.",
    "confidence": 0.9,
    "assertion_status": "CURRENT",
    "subject": "PATIENT",
}


def test_list_pending_structured_findings_returns_only_new_signals_with_findings(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    evidence = _make_evidence_record(db_session, tenant_id=tenant_id, patient_id=patient.id)

    with_findings = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        structured_findings=[_SAMPLE_FINDING],
    )
    _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        structured_findings=[],
    )
    _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        structured_findings=[_SAMPLE_FINDING],
        review_status="ACKNOWLEDGED",
    )

    results = list_pending_structured_findings(db_session, patient.id)

    assert len(results) == 1
    assert results[0]["id"] == str(with_findings.id)
    assert results[0]["structured_findings"] == [_SAMPLE_FINDING]
    assert results[0]["original_text_excerpt"] == "Right hemiparesis after prior stroke."


def test_list_pending_structured_findings_returns_empty_for_patient_with_no_signals(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    assert list_pending_structured_findings(db_session, patient.id) == []


def test_review_harvested_signal_marks_applied_and_stamps_reviewer(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    evidence = _make_evidence_record(db_session, tenant_id=tenant_id, patient_id=patient.id)
    signal = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        structured_findings=[_SAMPLE_FINDING],
    )

    updated = review_harvested_signal(
        db_session,
        signal_id=signal.id,
        tenant_id=tenant_id,
        disposition="APPLIED",
        reviewed_by_user_id=TEST_USER_ID,
        reason="Applied 3 structured field(s)",
    )

    assert updated.review_status == "APPLIED"
    assert updated.reviewed_by_user_id == TEST_USER_ID
    assert updated.reviewed_at is not None
    assert updated.review_disposition_reason == "Applied 3 structured field(s)"

    # No longer returned as pending once reviewed.
    assert list_pending_structured_findings(db_session, patient.id) == []


def test_review_harvested_signal_marks_dismissed(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    evidence = _make_evidence_record(db_session, tenant_id=tenant_id, patient_id=patient.id)
    signal = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        structured_findings=[_SAMPLE_FINDING],
    )

    updated = review_harvested_signal(
        db_session,
        signal_id=signal.id,
        tenant_id=tenant_id,
        disposition="DISMISSED",
        reviewed_by_user_id=TEST_USER_ID,
        reason="Not clinically relevant to current POC",
    )

    assert updated.review_status == "DISMISSED"
    assert list_pending_structured_findings(db_session, patient.id) == []


def test_review_harvested_signal_rejects_invalid_disposition(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    evidence = _make_evidence_record(db_session, tenant_id=tenant_id, patient_id=patient.id)
    signal = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        structured_findings=[_SAMPLE_FINDING],
    )

    with pytest.raises(ValueError):
        review_harvested_signal(
            db_session,
            signal_id=signal.id,
            tenant_id=tenant_id,
            disposition="ACKNOWLEDGED",  # not a valid disposition -- only APPLIED/DISMISSED
        )


def test_review_harvested_signal_rejects_cross_tenant_signal(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    other_tenant_id = uuid.uuid4()
    patient = _make_patient(db_session, tenant_id)
    evidence = _make_evidence_record(db_session, tenant_id=tenant_id, patient_id=patient.id)
    signal = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        structured_findings=[_SAMPLE_FINDING],
    )

    with pytest.raises(LookupError):
        review_harvested_signal(
            db_session,
            signal_id=signal.id,
            tenant_id=other_tenant_id,
            disposition="DISMISSED",
        )


def test_build_rnica_intelligence_includes_structured_findings_signals():
    signals = [
        {
            "id": str(uuid.uuid4()),
            "source_type": "REFERRAL_HNP",
            "clinical_system": "neurological",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "original_text_excerpt": "Right hemiparesis after prior stroke.",
            "structured_findings": [_SAMPLE_FINDING],
        }
    ]

    intelligence = build_rnica_intelligence(
        {}, patient_id="patient-1", structured_findings_signals=signals
    )

    assert intelligence["structured_findings_signals"] == signals


def test_build_rnica_intelligence_defaults_structured_findings_signals_to_empty_list():
    intelligence = build_rnica_intelligence({}, patient_id="patient-1")

    assert intelligence["structured_findings_signals"] == []
