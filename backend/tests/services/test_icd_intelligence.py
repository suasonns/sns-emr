from __future__ import annotations

from app.services.icd_intelligence import (
    gather_patient_evidence,
    primary_dx_guardrails,
    recommend_icd_candidates,
)


class FakeMappingResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class FakeDB:
    def __init__(self):
        self._rows = {
            "diagnosis": [
                {
                    "source": "RN_IA",
                    "dx_type": "PRIMARY",
                    "icd_code": "I50.9",
                    "description": "CHF with edema",
                }
            ],
            "notes": [
                {
                    "note_type": "RN ICA",
                    "discipline": "NURSING",
                    "content": "Patient reports shortness of breath and volume overload.",
                    "observed_data": {"edema": "present"},
                    "assessment": {"reason": "NYHA class III"},
                }
            ],
        }

    def execute(self, statement, params=None):
        sql = str(statement).lower()
        if "diagnosis_sources" in sql:
            return FakeMappingResult(self._rows["diagnosis"])
        if "clinical_notes" in sql:
            return FakeMappingResult(self._rows["notes"])
        raise AssertionError(f"Unexpected SQL: {sql}")


def test_recommend_icd_candidates_matches_chf_keywords():
    suggestions = recommend_icd_candidates(
        "CHF with edema, NYHA class III, volume overload, dyspnea, poor exercise tolerance",
        max_results=3,
    )

    assert suggestions
    assert suggestions[0]["category_key"] == "HEART_DISEASE_CHF"
    assert suggestions[0]["confidence"] > 0.5


def test_recommend_icd_candidates_returns_empty_for_blank_text():
    assert recommend_icd_candidates("   ") == []


def test_primary_dx_guardrails_include_denied_prefixes():
    guardrails = primary_dx_guardrails()
    assert "F" in guardrails["deny_prefixes"]
    assert "R" in guardrails["deny_prefixes"]
    assert "Z" in guardrails["deny_prefixes"]


def test_gather_patient_evidence_uses_real_diagnosis_and_note_data():
    evidence = gather_patient_evidence(FakeDB(), "patient-123", tenant_id="tenant-456")

    assert evidence["source_count"] >= 2
    assert "CHF" in evidence["text"]
    assert "edema" in evidence["text"].lower()
    assert evidence["diagnosis_sources"][0]["source"] == "RN_IA"


def test_recommend_icd_candidates_uses_patient_evidence_text():
    patient_evidence = {
        "text": "CHF with edema and NYHA class III volume overload",
        "source_count": 2,
    }

    suggestions = recommend_icd_candidates("", patient_evidence=patient_evidence, max_results=3)

    assert suggestions
    assert suggestions[0]["category_key"] == "HEART_DISEASE_CHF"
