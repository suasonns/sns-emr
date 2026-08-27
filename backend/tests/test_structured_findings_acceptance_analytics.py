"""Tests for Structured Findings Acceptance Analytics (PR #16).

Scope, per instruction: report ONLY what is persisted in review_status
(NEW / APPLIED / DISMISSED) and structured_findings concept codes. No new
tables/columns; no "Modified" or "Conflicted" buckets.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from app.models.patient import Patient
from app.models.patient_evidence import PatientEvidenceRecord, PatientHarvestedSignal
from app.services.evidence.harvest_service import get_structured_findings_acceptance_analytics
from tests.conftest import TEST_USER_ID, _test_tenant_id


def _tenant_id():
    return uuid.UUID(_test_tenant_id())


def _make_patient(db_session):
    patient = Patient(
        tenant_id=_tenant_id(),
        mrn=f"SFA-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Structured findings analytics test",
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
        original_documentation="Analytics fixture text.",
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
    concept_code="NEURO_HEMIPARESIS_RIGHT",
    recorded_at=None,
):
    signal = PatientHarvestedSignal(
        tenant_id=_tenant_id(),
        patient_id=patient_id,
        evidence_record_id=evidence_record_id,
        source_type="REFERRAL_HNP",
        recorded_at=recorded_at or datetime.now(timezone.utc),
        signal_key=f"signal-{uuid.uuid4().hex[:8]}",
        signal_text="Analytics fixture signal.",
        original_text_excerpt="Analytics fixture signal.",
        clinical_system="neurological",
        requires_idg_review=False,
        requires_poc_review=False,
        review_status=review_status,
        structured_findings=[
            {
                "concept_code": concept_code,
                "value": True,
                "source_type": "REFERRAL_HNP",
                "source_excerpt": "Analytics fixture signal.",
                "confidence": 0.9,
                "assertion_status": "CURRENT",
                "subject": "PATIENT",
            }
        ],
    )
    db_session.add(signal)
    db_session.commit()
    return signal


def test_analytics_counts_by_status_and_application_rate(db_session):
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="APPLIED")
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="APPLIED")
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="APPLIED")
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="DISMISSED")
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="NEW")

    result = get_structured_findings_acceptance_analytics(db_session, tenant_id=_tenant_id(), patient_id=patient.id)

    assert result["total_signals"] == 5
    assert result["by_status"] == {"NEW": 1, "APPLIED": 3, "DISMISSED": 1}
    assert result["reviewed_count"] == 4
    # 3 applied / 4 reviewed = 0.75
    assert result["application_rate"] == 0.75


def test_analytics_application_rate_is_none_when_nothing_reviewed(db_session):
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="NEW")

    result = get_structured_findings_acceptance_analytics(db_session, tenant_id=_tenant_id(), patient_id=patient.id)

    assert result["reviewed_count"] == 0
    assert result["application_rate"] is None


def test_analytics_counts_by_concept(db_session):
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    _make_signal(
        db_session,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        review_status="APPLIED",
        concept_code="CV_HEART_FAILURE_SYSTOLIC",
    )
    _make_signal(
        db_session,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        review_status="DISMISSED",
        concept_code="CV_HEART_FAILURE_SYSTOLIC",
    )
    _make_signal(
        db_session,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        review_status="APPLIED",
        concept_code="NEURO_HEMIPARESIS_RIGHT",
    )

    result = get_structured_findings_acceptance_analytics(db_session, tenant_id=_tenant_id(), patient_id=patient.id)

    by_concept = {c["concept_code"]: c for c in result["by_concept"]}
    assert by_concept["CV_HEART_FAILURE_SYSTOLIC"]["total"] == 2
    assert by_concept["CV_HEART_FAILURE_SYSTOLIC"]["APPLIED"] == 1
    assert by_concept["CV_HEART_FAILURE_SYSTOLIC"]["DISMISSED"] == 1
    assert by_concept["NEURO_HEMIPARESIS_RIGHT"]["total"] == 1
    assert by_concept["NEURO_HEMIPARESIS_RIGHT"]["APPLIED"] == 1


def test_analytics_counts_by_patient_when_no_patient_filter(db_session):
    patient_a = _make_patient(db_session)
    patient_b = _make_patient(db_session)
    evidence_a = _make_evidence_record(db_session, patient_id=patient_a.id)
    evidence_b = _make_evidence_record(db_session, patient_id=patient_b.id)
    _make_signal(db_session, patient_id=patient_a.id, evidence_record_id=evidence_a.id, review_status="APPLIED")
    _make_signal(db_session, patient_id=patient_b.id, evidence_record_id=evidence_b.id, review_status="DISMISSED")
    _make_signal(db_session, patient_id=patient_b.id, evidence_record_id=evidence_b.id, review_status="DISMISSED")

    result = get_structured_findings_acceptance_analytics(db_session, tenant_id=_tenant_id())

    by_patient = {p["patient_id"]: p for p in result["by_patient"]}
    assert by_patient[str(patient_a.id)]["total"] == 1
    assert by_patient[str(patient_a.id)]["APPLIED"] == 1
    assert by_patient[str(patient_b.id)]["total"] == 2
    assert by_patient[str(patient_b.id)]["DISMISSED"] == 2


def test_analytics_filters_by_date_range(db_session):
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    old_signal = _make_signal(
        db_session,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        review_status="APPLIED",
        recorded_at=datetime.now(timezone.utc) - timedelta(days=30),
    )
    recent_signal = _make_signal(
        db_session,
        patient_id=patient.id,
        evidence_record_id=evidence.id,
        review_status="DISMISSED",
        recorded_at=datetime.now(timezone.utc),
    )

    result = get_structured_findings_acceptance_analytics(
        db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
    )

    assert result["total_signals"] == 1
    assert result["by_status"] == {"NEW": 0, "APPLIED": 0, "DISMISSED": 1}
    assert old_signal.review_status == "APPLIED"  # sanity: old signal untouched, just excluded
    assert recent_signal.review_status == "DISMISSED"


def test_analytics_scoped_to_tenant(db_session):
    """A signal from a different tenant must never be counted."""
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="APPLIED")

    other_tenant_id = uuid.uuid4()
    result = get_structured_findings_acceptance_analytics(db_session, tenant_id=other_tenant_id)

    assert result["total_signals"] == 0
    assert result["by_status"] == {"NEW": 0, "APPLIED": 0, "DISMISSED": 0}
    assert result["application_rate"] is None


def test_analytics_excludes_signals_with_no_structured_findings(db_session):
    """Narrative-only signals (structured_findings == []) share the same
    review_status vocabulary/table but are NOT part of the Structured
    Findings feature -- they must never be counted here."""
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="APPLIED")

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
        review_status="ACKNOWLEDGED",
        structured_findings=[],
    )
    db_session.add(narrative_only)
    db_session.commit()

    result = get_structured_findings_acceptance_analytics(db_session, tenant_id=_tenant_id(), patient_id=patient.id)

    assert result["total_signals"] == 1
    assert "ACKNOWLEDGED" not in result["by_status"]
    assert result["by_status"]["APPLIED"] == 1


def test_analytics_endpoint_requires_valid_patient_id(client, rn_headers):
    resp = client.get(
        "/visits/rnica/signals/analytics",
        params={"patient_id": "not-a-uuid"},
        headers=rn_headers,
    )
    assert resp.status_code == 422


def test_analytics_endpoint_returns_tenant_summary(client, db_session, rn_headers):
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id, review_status="APPLIED")

    resp = client.get(
        "/visits/rnica/signals/analytics",
        params={"patient_id": str(patient.id)},
        headers=rn_headers,
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_signals"] == 1
    assert body["by_status"]["APPLIED"] == 1
    assert body["application_rate"] == 1.0
