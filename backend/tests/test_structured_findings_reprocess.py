from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.patient import Patient
from app.models.patient_evidence import PatientEvidenceRecord, PatientHarvestedSignal
from app.services.evidence import ai_extraction_service
from app.services.evidence import structured_findings_reprocess_service as reprocess_service
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id: uuid.UUID) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"REPROC-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Reprocess test diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_evidence_record(db_session, *, tenant_id, patient_id, text: str) -> PatientEvidenceRecord:
    record = PatientEvidenceRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        source_type="REFERRAL_HNP",
        source_record_id=uuid.uuid4(),
        recorded_at=datetime.now(timezone.utc),
        original_documentation=text,
        ai_extraction_completed=True,
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
    excerpt: str,
    recorded_at=None,
    review_status="NEW",
    structured_findings_status="PENDING",
    structured_findings=None,
    structured_findings_attempts=0,
) -> PatientHarvestedSignal:
    signal = PatientHarvestedSignal(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        evidence_record_id=evidence_record_id,
        source_type="REFERRAL_HNP",
        source_discipline="RN",
        recorded_at=recorded_at or datetime.now(timezone.utc),
        signal_key="edema_present",
        signal_text="Patient has lower extremity edema.",
        original_text_excerpt=excerpt,
        review_status=review_status,
        structured_findings=structured_findings or [],
        structured_findings_status=structured_findings_status,
        structured_findings_attempts=structured_findings_attempts,
    )
    db_session.add(signal)
    db_session.commit()
    return signal


def _configure_azure(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://fake-resource.openai.azure.com/openai/v1")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake-key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4")


def _fake_model_response(structured_findings):
    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "signals": [
                                        {
                                            "signal_key": "edema_present",
                                            "signal_text": "Patient has lower extremity edema.",
                                            "original_text_excerpt": "2+ pitting edema bilateral lower extremities",
                                            "trend": "STABLE",
                                            "confidence": 0.9,
                                            "clinical_system": "cardiopulmonary",
                                            "requires_idg_review": False,
                                            "requires_poc_review": False,
                                            "structured_findings": structured_findings,
                                        }
                                    ]
                                }
                            )
                        }
                    }
                ]
            }

    return _FakeResponse()


def _mock_extraction(monkeypatch, *, structured_findings=None, call_counter=None):
    """Patch httpx.post so extract_signals_with_diagnostics returns a
    deterministic edema finding (or whatever raw structured_findings list is
    given). Tracks call count via the mutable `call_counter` list if passed."""

    structured_findings = structured_findings if structured_findings is not None else [
        {
            "concept_code": "CV_EDEMA_LOC_BILATERAL_LE",
            "value": True,
            "source_excerpt": "2+ pitting edema bilateral lower extremities",
            "confidence": 0.9,
            "assertion_status": "CURRENT",
            "subject": "PATIENT",
        }
    ]

    def _fake_post(url, headers=None, json=None, timeout=None):
        if call_counter is not None:
            call_counter.append(1)
        return _fake_model_response(structured_findings)

    monkeypatch.setattr(ai_extraction_service.httpx, "post", _fake_post)
    return structured_findings


def _fake_post_raises(url, headers=None, json=None, timeout=None):
    raise RuntimeError("simulated network failure")


@pytest.fixture(autouse=True)
def _isolate_azure_env(monkeypatch):
    # ai_extraction_service reads env vars fresh every call, so make sure no
    # test leaks real Azure config across the suite.
    yield


def test_fresh_pending_row_gets_processed_once(db_session, monkeypatch):
    _configure_azure(monkeypatch)
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    record = _make_evidence_record(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        text="H&P notes 2+ pitting edema bilateral lower extremities.",
    )
    signal = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=record.id,
        excerpt="2+ pitting edema bilateral lower extremities",
    )

    call_counter: list[int] = []
    _mock_extraction(monkeypatch, call_counter=call_counter)

    report = reprocess_service.reprocess_patient(db_session, patient_id=patient.id, tenant_id=tenant_id)
    db_session.commit()

    assert len(call_counter) == 1
    assert report.harvested_signals_count == 1
    assert report.completed_count == 1
    assert report.structured_findings_generated_count == 1
    assert report.skipped_count == 0
    assert report.failed_count == 0

    db_session.refresh(signal)
    assert signal.structured_findings_status == "COMPLETED"
    assert len(signal.structured_findings) == 1
    assert signal.structured_findings[0]["concept_code"] == "CV_EDEMA_LOC_BILATERAL_LE"
    assert signal.structured_findings_attempts == 1
    assert signal.structured_findings_last_attempted_at is not None
    assert signal.structured_findings_last_error is None


def test_rerunning_twice_does_not_duplicate_or_recall_model(db_session, monkeypatch):
    _configure_azure(monkeypatch)
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    record = _make_evidence_record(
        db_session, tenant_id=tenant_id, patient_id=patient.id, text="H&P notes edema."
    )
    _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=record.id,
        excerpt="2+ pitting edema bilateral lower extremities",
    )

    call_counter: list[int] = []
    _mock_extraction(monkeypatch, call_counter=call_counter)

    first_report = reprocess_service.reprocess_patient(db_session, patient_id=patient.id, tenant_id=tenant_id)
    db_session.commit()
    assert first_report.completed_count == 1
    assert len(call_counter) == 1

    second_report = reprocess_service.reprocess_patient(db_session, patient_id=patient.id, tenant_id=tenant_id)
    db_session.commit()

    # No second model call, no duplicate findings appended.
    assert len(call_counter) == 1
    assert second_report.completed_count == 0
    assert second_report.skipped_already_completed_count == 1
    assert second_report.structured_findings_generated_count == 0

    signal = (
        db_session.query(PatientHarvestedSignal)
        .filter(PatientHarvestedSignal.patient_id == patient.id)
        .one()
    )
    assert len(signal.structured_findings) == 1
    assert signal.structured_findings_attempts == 1


def test_rn_reviewed_row_never_touched_even_with_force(db_session, monkeypatch):
    _configure_azure(monkeypatch)
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    record = _make_evidence_record(
        db_session, tenant_id=tenant_id, patient_id=patient.id, text="H&P notes edema."
    )
    signal = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=record.id,
        excerpt="2+ pitting edema bilateral lower extremities",
        review_status="ACKNOWLEDGED",
        structured_findings_status="PENDING",
    )

    call_counter: list[int] = []
    _mock_extraction(monkeypatch, call_counter=call_counter)

    report = reprocess_service.reprocess_patient(
        db_session, patient_id=patient.id, tenant_id=tenant_id, force=True
    )
    db_session.commit()

    assert len(call_counter) == 0
    assert report.skipped_rn_reviewed_count == 1
    assert report.completed_count == 0

    db_session.refresh(signal)
    assert signal.structured_findings_status == "PENDING"
    assert signal.structured_findings == []


def test_failed_row_is_retried_and_can_transition_to_completed(db_session, monkeypatch):
    _configure_azure(monkeypatch)
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    record = _make_evidence_record(
        db_session, tenant_id=tenant_id, patient_id=patient.id, text="H&P notes edema."
    )
    signal = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=record.id,
        excerpt="2+ pitting edema bilateral lower extremities",
        structured_findings_status="FAILED",
        structured_findings_attempts=1,
    )

    monkeypatch.setattr(ai_extraction_service.httpx, "post", _fake_post_raises)
    report = reprocess_service.reprocess_patient(db_session, patient_id=patient.id, tenant_id=tenant_id)
    db_session.commit()

    assert report.failed_count == 1
    db_session.refresh(signal)
    assert signal.structured_findings_status == "FAILED"
    assert signal.structured_findings_attempts == 2
    assert signal.structured_findings_last_error is not None

    # Now the underlying call succeeds -- retry should complete it.
    _mock_extraction(monkeypatch)
    report2 = reprocess_service.reprocess_patient(db_session, patient_id=patient.id, tenant_id=tenant_id)
    db_session.commit()

    assert report2.completed_count == 1
    db_session.refresh(signal)
    assert signal.structured_findings_status == "COMPLETED"
    assert signal.structured_findings_attempts == 3
    assert signal.structured_findings_last_error is None
    assert len(signal.structured_findings) == 1


def test_retry_failed_and_pending_respects_max_attempts(db_session, monkeypatch):
    _configure_azure(monkeypatch)
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    record = _make_evidence_record(
        db_session, tenant_id=tenant_id, patient_id=patient.id, text="H&P notes edema."
    )
    under_cap = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=record.id,
        excerpt="edema excerpt under cap",
        structured_findings_status="FAILED",
        structured_findings_attempts=1,
    )
    at_cap = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=record.id,
        excerpt="edema excerpt at cap",
        structured_findings_status="FAILED",
        structured_findings_attempts=3,
    )

    call_counter: list[int] = []
    _mock_extraction(monkeypatch, call_counter=call_counter)

    report = reprocess_service.retry_failed_and_pending(
        db_session, tenant_id=tenant_id, max_attempts=3
    )
    db_session.commit()

    assert report.harvested_signals_count == 1
    assert len(call_counter) == 1

    db_session.refresh(under_cap)
    db_session.refresh(at_cap)
    assert under_cap.structured_findings_status == "COMPLETED"
    assert at_cap.structured_findings_status == "FAILED"
    assert at_cap.structured_findings_attempts == 3


def test_batch_date_range_filtering_only_picks_up_in_range_rows(db_session, monkeypatch):
    _configure_azure(monkeypatch)
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    record = _make_evidence_record(
        db_session, tenant_id=tenant_id, patient_id=patient.id, text="H&P notes edema."
    )
    now = datetime.now(timezone.utc)
    in_range = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=record.id,
        excerpt="in range excerpt",
        recorded_at=now - timedelta(days=5),
    )
    out_of_range = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=record.id,
        excerpt="out of range excerpt",
        recorded_at=now - timedelta(days=60),
    )

    call_counter: list[int] = []
    _mock_extraction(monkeypatch, call_counter=call_counter)

    report = reprocess_service.reprocess_batch(
        db_session,
        tenant_id=tenant_id,
        start_date=(now - timedelta(days=10)).date(),
        end_date=now.date(),
    )
    db_session.commit()

    assert report.harvested_signals_count == 1
    assert len(call_counter) == 1

    db_session.refresh(in_range)
    db_session.refresh(out_of_range)
    assert in_range.structured_findings_status == "COMPLETED"
    assert out_of_range.structured_findings_status == "PENDING"


def test_report_counts_include_rejected_findings(db_session, monkeypatch):
    _configure_azure(monkeypatch)
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    record = _make_evidence_record(
        db_session, tenant_id=tenant_id, patient_id=patient.id, text="H&P notes edema."
    )
    signal = _make_signal(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        evidence_record_id=record.id,
        excerpt="edema excerpt with one bogus concept",
    )

    _mock_extraction(
        monkeypatch,
        structured_findings=[
            {
                "concept_code": "CV_EDEMA_LOC_BILATERAL_LE",
                "value": True,
                "source_excerpt": "2+ pitting edema bilateral lower extremities",
                "confidence": 0.9,
                "assertion_status": "CURRENT",
                "subject": "PATIENT",
            },
            {
                # Unknown concept_code -- validate_findings() must discard this.
                "concept_code": "NOT_A_REAL_CONCEPT_CODE",
                "value": True,
                "source_excerpt": "some other text",
                "confidence": 0.5,
                "assertion_status": "CURRENT",
                "subject": "PATIENT",
            },
        ],
    )

    report = reprocess_service.reprocess_patient(db_session, patient_id=patient.id, tenant_id=tenant_id)
    db_session.commit()

    assert report.completed_count == 1
    assert report.structured_findings_generated_count == 1
    assert report.rejected_count == 1

    db_session.refresh(signal)
    assert len(signal.structured_findings) == 1
