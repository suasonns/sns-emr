from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from app.models.patient import Patient
from app.models.patient_evidence import PatientEvidenceRecord, PatientHarvestedSignal
from app.services.evidence import ai_extraction_service
from app.services.evidence.harvest_service import extract_narrative_text, harvest_from_source
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id: uuid.UUID) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"EVID-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Evidence harvester test diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def test_extract_narrative_text_collects_prose_and_skips_short_tokens():
    content = {
        "vitals": {"bp": "120/80", "temp": "98.6"},
        "narrative": "Patient reports increasing shortness of breath over the last week.",
        "nested": {
            "caregiver_note": "Family caregiver states patient is sleeping most of the day now.",
            "code": "RN",
        },
        "flags": [True, False, "N/A"],
    }

    text = extract_narrative_text(content)

    assert "shortness of breath" in text
    assert "sleeping most of the day" in text
    assert "120/80" not in text
    assert "RN" not in text


def test_extract_signals_is_inert_when_azure_openai_not_configured(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)

    assert ai_extraction_service.is_configured() is False

    signals = ai_extraction_service.extract_signals(
        text="Patient declining steadily, family very concerned.",
        discipline="RN",
        note_type="RN_VISIT",
        source_type="CLINICAL_NOTE",
    )

    assert signals == []


def test_harvest_from_source_persists_evidence_record_even_when_ai_unconfigured(
    db_session, monkeypatch
):
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)

    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    source_record_id = uuid.uuid4()
    evidence_record = harvest_from_source(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        source_type="COMMUNICATION_LOG",
        source_record_id=source_record_id,
        recorded_at=datetime.now(timezone.utc),
        text="Caregiver called reporting patient has stopped eating for two days.",
        discipline=None,
        recorded_by_user_id=TEST_USER_ID,
        recorded_by_name="Test User",
    )

    assert evidence_record is not None
    assert evidence_record.ai_extraction_completed is True
    assert evidence_record.source_record_id == source_record_id

    persisted = db_session.get(PatientEvidenceRecord, evidence_record.id)
    assert persisted is not None
    assert persisted.original_documentation.startswith("Caregiver called")

    # No signals should exist since AI extraction was skipped (unconfigured).
    signals = (
        db_session.query(PatientHarvestedSignal)
        .filter(PatientHarvestedSignal.evidence_record_id == evidence_record.id)
        .all()
    )
    assert signals == []


def test_harvest_from_source_returns_none_for_blank_text(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    result = harvest_from_source(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        source_type="INCIDENT_REPORT",
        source_record_id=uuid.uuid4(),
        recorded_at=datetime.now(timezone.utc),
        text="   ",
    )

    assert result is None


def test_extract_signals_parses_well_formed_model_response(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://fake-resource.openai.azure.com/openai/v1")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake-key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4")

    import json as _json

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": _json.dumps(
                                {
                                    "signals": [
                                        {
                                            "signal_key": "increasing_dyspnea",
                                            "signal_text": "Patient reports worsening shortness of breath.",
                                            "original_text_excerpt": "SOB has worsened over the past week",
                                            "trend": "DOWN",
                                            "confidence": 0.82,
                                            "clinical_system": "cardiopulmonary",
                                            "requires_idg_review": True,
                                            "requires_poc_review": False,
                                        },
                                        {
                                            # Malformed entry -- missing required fields, should be skipped.
                                            "trend": "UP",
                                        },
                                    ]
                                }
                            )
                        }
                    }
                ]
            }

    def _fake_post(url, headers=None, json=None, timeout=None):
        assert "fake-resource.openai.azure.com" in url
        assert "gpt-5.4" in url
        return _FakeResponse()

    monkeypatch.setattr(ai_extraction_service.httpx, "post", _fake_post)

    signals = ai_extraction_service.extract_signals(
        text="Patient's SOB has worsened over the past week per RN visit note.",
        discipline="RN",
        note_type="RN_VISIT",
        source_type="CLINICAL_NOTE",
    )

    assert len(signals) == 1
    signal = signals[0]
    assert signal.signal_key == "increasing_dyspnea"
    assert signal.trend == "DOWN"
    assert signal.confidence == 0.82
    assert signal.requires_idg_review is True
    assert signal.requires_poc_review is False
