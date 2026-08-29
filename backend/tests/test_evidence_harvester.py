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


def test_harvest_from_source_is_idempotent_when_reprocessed(db_session, monkeypatch):
    """RNICA Phase 4 reprocess validation: a document/source can legitimately
    be re-harvested (e.g. a recovery sweep retrying after an interrupted
    first attempt, or an operator explicitly re-running extraction).
    Calling harvest_from_source twice for the exact same
    (tenant_id, source_type, source_record_id) must reuse the original
    PatientEvidenceRecord rather than creating a duplicate, and must never
    create a second, duplicate set of PatientHarvestedSignal rows -- this
    is what the DB-level unique constraint + the existence check at the
    top of harvest_from_source are for."""
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)

    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    source_record_id = uuid.uuid4()
    recorded_at = datetime.now(timezone.utc)
    text = "Patient reports increasing pain and decreased appetite over the past week."

    first = harvest_from_source(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        source_type="CLINICAL_NOTE",
        source_record_id=source_record_id,
        recorded_at=recorded_at,
        text=text,
        recorded_by_user_id=TEST_USER_ID,
        recorded_by_name="Test User",
    )
    assert first is not None

    # Simulate a reprocess: the exact same source is harvested again.
    second = harvest_from_source(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        source_type="CLINICAL_NOTE",
        source_record_id=source_record_id,
        recorded_at=recorded_at,
        text=text,
        recorded_by_user_id=TEST_USER_ID,
        recorded_by_name="Test User",
    )
    assert second is not None
    assert second.id == first.id, "reprocessing the same source must reuse the existing evidence record, not duplicate it"

    all_records = (
        db_session.query(PatientEvidenceRecord)
        .filter(
            PatientEvidenceRecord.tenant_id == tenant_id,
            PatientEvidenceRecord.source_type == "CLINICAL_NOTE",
            PatientEvidenceRecord.source_record_id == source_record_id,
        )
        .all()
    )
    assert len(all_records) == 1, "reprocessing must never create a second evidence record for the same source"


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


# ═══════════ Deterministic wound safety-net regression tests ═══════════
# Real defect: a 63KB H&P/referral export contained an explicit wound-care
# order ("wound care order for L side of buttocks and R foot") at char
# offset ~58,735 -- past the old single-slice 12,000-char truncation, so it
# was silently never sent to the model on ANY run. These tests use the
# exact real source wording (including the OCR/export-style glued spacing)
# and pin down that explicit wound language is now detected deterministically,
# independent of the LLM, on every run, with no variance.

_REAL_WOUND_EXCERPT = (
    "Dr. Massey that runs the boarding care facility pt is at is req a wound care "
    "order for L sideof buttocksandRfoot. He also was informed that home health "
    "nurse came to facility to evaluate the pt."
)


def test_deterministic_wound_detector_finds_left_buttock_order():
    candidates = ai_extraction_service.detect_wound_candidates(_REAL_WOUND_EXCERPT)
    locations = {c.location: c.outcome for c in candidates}
    assert locations.get("left buttock") == "STRUCTURED_FINDING_CREATED"


def test_deterministic_wound_detector_finds_right_foot_order():
    candidates = ai_extraction_service.detect_wound_candidates(_REAL_WOUND_EXCERPT)
    locations = {c.location: c.outcome for c in candidates}
    assert locations.get("right foot") == "STRUCTURED_FINDING_CREATED"


def test_deterministic_wound_detector_two_locations_one_passage_are_separate():
    candidates = ai_extraction_service.detect_wound_candidates(_REAL_WOUND_EXCERPT)
    created = [c for c in candidates if c.outcome == "STRUCTURED_FINDING_CREATED"]
    locations = sorted(c.location for c in created)
    assert locations == ["left buttock", "right foot"]
    # Never combined into one string.
    assert all(";" not in loc and " and " not in loc for loc in locations)


def test_deterministic_wound_detector_history_only_is_rejected_not_dropped():
    candidates = ai_extraction_service.detect_wound_candidates(
        "History of a wound to the left buttock, now resolved."
    )
    assert any(c.outcome == "REJECTED_HISTORICAL" and c.location == "left buttock" for c in candidates)
    assert not any(c.outcome == "STRUCTURED_FINDING_CREATED" for c in candidates)


def test_deterministic_wound_detector_resolved_wound_is_historical():
    candidates = ai_extraction_service.detect_wound_candidates(
        "Right foot wound, resolved as of last visit."
    )
    assert any(c.assertion_status == "HISTORICAL" for c in candidates)
    assert not any(c.outcome == "STRUCTURED_FINDING_CREATED" for c in candidates)


def test_deterministic_wound_detector_no_wound_produces_no_finding():
    candidates = ai_extraction_service.detect_wound_candidates("Skin intact, no wound noted on exam.")
    assert not any(c.outcome == "STRUCTURED_FINDING_CREATED" for c in candidates)


def test_deterministic_wound_detector_negated_wound_is_rejected_not_dropped():
    candidates = ai_extraction_service.detect_wound_candidates("Patient denies any wound at this time.")
    assert any(c.assertion_status == "NEGATED" for c in candidates)
    assert not any(c.outcome == "STRUCTURED_FINDING_CREATED" for c in candidates)


def test_deterministic_wound_detector_uncertain_wound_is_rejected_not_dropped():
    candidates = ai_extraction_service.detect_wound_candidates(
        "Possible wound versus rash on the right foot, uncertain at this time."
    )
    assert any(c.assertion_status == "UNCERTAIN" for c in candidates)
    assert not any(c.outcome == "STRUCTURED_FINDING_CREATED" for c in candidates)


def test_deterministic_wound_detector_is_consistent_across_repeated_runs():
    # Run the identical input repeatedly -- must produce the exact same
    # result every time (this is the whole point of a deterministic,
    # non-LLM safety net: no run-to-run variance).
    results = [ai_extraction_service.detect_wound_candidates(_REAL_WOUND_EXCERPT) for _ in range(10)]
    normalized = [sorted((c.location, c.assertion_status, c.outcome) for c in r) for r in results]
    assert all(n == normalized[0] for n in normalized)
    assert {"left buttock", "right foot"}.issubset(
        {loc for loc, _status, outcome in normalized[0] if outcome == "STRUCTURED_FINDING_CREATED"}
    )


def test_extract_signals_surfaces_wound_findings_even_when_ai_unconfigured(monkeypatch):
    # The deterministic safety net must fire independent of the LLM path --
    # simulate the worst case (Azure OpenAI entirely unconfigured) and
    # confirm the wound findings still make it through.
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)

    signals = ai_extraction_service.extract_signals(
        text=_REAL_WOUND_EXCERPT,
        discipline=None,
        note_type="REFERRAL_HNP",
        source_type="REFERRAL_HNP",
    )

    all_findings = [f for s in signals for f in s.structured_findings]
    wound_findings = [f for f in all_findings if f["concept_code"] == "SKIN_WOUND_PRESENT"]
    locations = sorted(f["value"] for f in wound_findings)
    assert locations == ["left buttock", "right foot"]


def test_split_into_chunks_covers_entire_document_no_data_lost():
    # Regression for the root defect: the old code truncated at
    # MAX_SOURCE_TEXT_CHARS and silently discarded everything after it.
    long_text = ("Routine visit note text. " * 2000) + "wound care order for left heel."
    assert len(long_text) > ai_extraction_service.MAX_SOURCE_TEXT_CHARS
    chunks = ai_extraction_service._split_into_chunks(long_text, ai_extraction_service.MAX_SOURCE_TEXT_CHARS)
    assert sum(len(c) for c in chunks) == len(long_text)
    assert "wound care order for left heel" in "".join(chunks)

