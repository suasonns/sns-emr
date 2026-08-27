"""Tests for RN Productivity Metrics (PR #17).

Scope, per instruction: fields_populated and manual_entries_avoided only,
computed strictly from persisted review_status (APPLIED) and
structured_findings data. No time-saved estimate (that would require an
assumption, not a persisted fact) -- deliberately not implemented here.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from app.models.patient import Patient
from app.models.patient_evidence import PatientEvidenceRecord, PatientHarvestedSignal
from app.services.evidence.harvest_service import get_rn_productivity_metrics
from tests.conftest import TEST_USER_ID, _test_tenant_id


def _tenant_id():
    return uuid.UUID(_test_tenant_id())


def _make_patient(db_session):
    patient = Patient(
        tenant_id=_tenant_id(),
        mrn=f"SFP-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="RN productivity metrics test",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_evidence_record(db_session, *, patient_id):
    record = PatientEvidenceRecord(
        tenant_id=_tenant_id(),
        patient_id=patient_id,
        source_type="REFERRAL_HNP",
        source_record_id=uuid.uuid4(),
        recorded_at=datetime.now(timezone.utc),
        recorded_by_user_id=TEST_USER_ID,
        recorded_by_name="Test User",
        original_documentation="Productivity metrics fixture text.",
    )
    db_session.add(record)
    db_session.commit()
    return record


def _make_signal(
    db_session,
    *,
    patient_id,
    evidence_record_id,
    review_status="NEW",
    concept_codes=("NEURO_HEMIPARESIS_RIGHT",),
    recorded_at=None,
):
    signal = PatientHarvestedSignal(
        tenant_id=_tenant_id(),
        patient_id=patient_id,
        evidence_record_id=evidence_record_id,
        source_type="REFERRAL_HNP",
        recorded_at=recorded_at or datetime.now(timezone.utc),
        signal_key=f"signal-{uuid.uuid4().hex[:8]}",
        signal_text="Productivity metrics fixture signal.",
        original_text_excerpt="Productivity metrics fixture signal.",
        clinical_system="neurological",
        requires_idg_review=False,
        requires_poc_review=False,
        review_status=review_status,
        structured_findings=[
            {
                "concept_code": code,
                "value": True,
                "source_type": "REFERRAL_HNP",
                "source_excerpt": "Productivity metrics fixture signal.",
                "confidence": 0.9,
                "assertion_status": "CURRENT",
                "subject": "PATIENT",
            }
            for code in concept_codes
        ],
    )
    db_session.add(signal)
    db_session.commit()
    return signal


def test_productivity_metrics_counts_applied_signals_and_fields(db_session):
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    # One applied signal with 2 concept codes -> 2 fields populated.
    _make_signal(
        db_session,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        review_status="APPLIED",
        concept_codes=("NEURO_HEMIPARESIS_RIGHT", "SKIN_WOUND_PRESENT"),
    )
    # One applied signal with 1 concept code -> 1 more field populated.
    _make_signal(
        db_session,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        review_status="APPLIED",
        concept_codes=("CV_HEART_FAILURE_SYSTOLIC",),
    )
    # Dismissed and pending signals must not count at all.
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="DISMISSED")
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="NEW")

    result = get_rn_productivity_metrics(db_session, tenant_id=_tenant_id(), patient_id=patient.id)

    assert result["manual_entries_avoided"] == 2
    assert result["fields_populated"] == 3
    assert set(result.keys()) == {"fields_populated", "manual_entries_avoided"}


def test_productivity_metrics_zero_when_nothing_applied(db_session):
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="NEW")
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="DISMISSED")

    result = get_rn_productivity_metrics(db_session, tenant_id=_tenant_id(), patient_id=patient.id)

    assert result == {"fields_populated": 0, "manual_entries_avoided": 0}


def test_productivity_metrics_excludes_narrative_only_signals(db_session):
    """A signal with review_status APPLIED but no structured_findings is a
    narrative-workflow signal, not a Structured Findings one -- it must
    never be counted here."""
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)

    narrative_only = PatientHarvestedSignal(
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        source_type="REFERRAL_HNP",
        recorded_at=datetime.now(timezone.utc),
        signal_key="narrative-only-signal",
        signal_text="Narrative-only signal with no structured findings.",
        original_text_excerpt="Narrative-only signal with no structured findings.",
        clinical_system="general",
        requires_idg_review=False,
        requires_poc_review=False,
        review_status="APPLIED",
        structured_findings=[],
    )
    db_session.add(narrative_only)
    db_session.commit()

    result = get_rn_productivity_metrics(db_session, tenant_id=_tenant_id(), patient_id=patient.id)

    assert result == {"fields_populated": 0, "manual_entries_avoided": 0}


def test_productivity_metrics_filters_by_date_range(db_session):
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    _make_signal(
        db_session,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        review_status="APPLIED",
        recorded_at=datetime.now(timezone.utc) - timedelta(days=30),
    )
    _make_signal(
        db_session,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        review_status="APPLIED",
        recorded_at=datetime.now(timezone.utc),
    )

    result = get_rn_productivity_metrics(
        db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
    )

    assert result["manual_entries_avoided"] == 1
    assert result["fields_populated"] == 1


def test_productivity_metrics_scoped_to_tenant(db_session):
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="APPLIED")

    other_tenant_id = uuid.uuid4()
    result = get_rn_productivity_metrics(db_session, tenant_id=other_tenant_id)

    assert result == {"fields_populated": 0, "manual_entries_avoided": 0}


def test_productivity_metrics_endpoint_requires_valid_patient_id(client, rn_headers):
    resp = client.get(
        "/visits/rnica/signals/productivity-metrics",
        params={"patient_id": "not-a-uuid"},
        headers=rn_headers,
    )
    assert resp.status_code == 422


def test_productivity_metrics_endpoint_returns_summary(client, db_session, rn_headers):
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    _make_signal(
        db_session,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        review_status="APPLIED",
        concept_codes=("NEURO_HEMIPARESIS_RIGHT", "SKIN_WOUND_PRESENT"),
    )

    resp = client.get(
        "/visits/rnica/signals/productivity-metrics",
        params={"patient_id": str(patient.id)},
        headers=rn_headers,
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body == {"fields_populated": 2, "manual_entries_avoided": 1}
