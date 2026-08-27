"""API-level tests for the Structured Findings batch-review endpoint that
backs "Apply All Non-Conflicting".

Exercises the real HTTP route via TestClient (not just the service
functions covered in test_structured_findings_application.py) so
authorization/tenant-scoping wiring at the API layer is also verified.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from app.models.patient import Patient
from app.models.patient_evidence import PatientEvidenceRecord, PatientHarvestedSignal
from tests.conftest import TEST_USER_ID, _test_tenant_id


def _tenant_id():
    return uuid.UUID(_test_tenant_id())


def _make_patient(db_session):
    patient = Patient(
        tenant_id=_tenant_id(),
        mrn=f"SFB-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Structured findings bulk-action test",
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
        original_documentation="Right hemiparesis; right foot wound noted.",
    )
    db_session.add(record)
    db_session.commit()
    return record


_SAMPLE_FINDING = {
    "concept_code": "NEURO_HEMIPARESIS_RIGHT",
    "value": True,
    "source_type": "REFERRAL_HNP",
    "source_excerpt": "Right hemiparesis after prior stroke.",
    "confidence": 0.9,
    "assertion_status": "CURRENT",
    "subject": "PATIENT",
}


def _make_signal(db_session, *, patient_id, evidence_record_id):
    signal = PatientHarvestedSignal(
        tenant_id=_tenant_id(),
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
        review_status="NEW",
        structured_findings=[_SAMPLE_FINDING],
    )
    db_session.add(signal)
    db_session.commit()
    return signal


def test_batch_review_endpoint_applies_multiple_signals(client, db_session, rn_headers):
    patient = _make_patient(db_session)
    evidence = _make_evidence_record(db_session, patient_id=patient.id)
    signal_a = _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id)
    signal_b = _make_signal(db_session, patient_id=patient.id, evidence_record_id=evidence.id)

    resp = client.post(
        "/visits/rnica/signals/batch-review",
        json={
            "signal_ids": [str(signal_a.id), str(signal_b.id)],
            "disposition": "APPLIED",
            "reason": "Apply All Non-Conflicting",
        },
        headers=rn_headers,
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body["updated"]) == {str(signal_a.id), str(signal_b.id)}
    assert body["not_found"] == []

    db_session.refresh(signal_a)
    db_session.refresh(signal_b)
    assert signal_a.review_status == "APPLIED"
    assert signal_b.review_status == "APPLIED"


def test_batch_review_endpoint_rejects_mixed_patient_batch(client, db_session, rn_headers):
    patient_a = _make_patient(db_session)
    patient_b = _make_patient(db_session)
    evidence_a = _make_evidence_record(db_session, patient_id=patient_a.id)
    evidence_b = _make_evidence_record(db_session, patient_id=patient_b.id)
    signal_a = _make_signal(db_session, patient_id=patient_a.id, evidence_record_id=evidence_a.id)
    signal_b = _make_signal(db_session, patient_id=patient_b.id, evidence_record_id=evidence_b.id)

    resp = client.post(
        "/visits/rnica/signals/batch-review",
        json={"signal_ids": [str(signal_a.id), str(signal_b.id)], "disposition": "APPLIED"},
        headers=rn_headers,
    )

    assert resp.status_code == 422


def test_batch_review_endpoint_rejects_empty_signal_ids(client, rn_headers):
    resp = client.post(
        "/visits/rnica/signals/batch-review",
        json={"signal_ids": [], "disposition": "APPLIED"},
        headers=rn_headers,
    )
    assert resp.status_code == 422
