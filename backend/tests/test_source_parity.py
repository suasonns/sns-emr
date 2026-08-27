"""Source-parity proof: a concept must behave identically regardless of
which pipeline it was extracted through.

This is the deliverable requested alongside wiring REFERRAL_HNP,
uploaded-document, and document_intelligence_service.py evidence into the
shared StructuredFinding contract: "A concept must behave identically
whether it comes from transcript, H&P, referral, uploaded document, or
note."

Scope of what "identical" means here:
    - The SAME concept_code, with the SAME raw finding payload (value,
      assertion_status, subject, confidence, source_excerpt, source_date,
      source_location), validates to the SAME accepted/rejected outcome
      and the SAME resolved field writes (`to_dict()["concept_code"]` and
      the registry's `writes`/`value_slot` behavior) no matter which
      source_type it is tagged with.
    - The ONLY thing that legitimately differs between sources is the
      provenance metadata itself (source_type, and whatever
      source_record_id/model_version the calling pipeline supplies) --
      never the applied value, never the section, never the field path.
    - This also proves the ai_extraction_service.py source_type resolver
      (`_resolve_finding_source_type`) correctly maps every real
      evidence pipeline (H&P intake textbox -> REFERRAL_HNP, uploaded H&P
      scan via document_intelligence_service.py -> REFERRAL_HNP, a
      generic uploaded document -> UPLOADED_DOCUMENT, authored clinical
      documentation -> CLINICAL_NOTE) onto the 4 StructuredFinding source
      types, and that note_draft_service.py's transcript path
      (source_type=TRANSCRIPT, exercised directly against the shared
      validator here since it requires no AI call) lands on the exact
      same validated shape.
"""

from __future__ import annotations

from app.services.evidence.ai_extraction_service import _resolve_finding_source_type
from app.services.evidence.structured_findings import validate_finding, validate_findings

ALL_SOURCE_TYPES = ("TRANSCRIPT", "REFERRAL_HNP", "UPLOADED_DOCUMENT", "CLINICAL_NOTE")


def _raw(concept_code: str, **overrides):
    base = {
        "concept_code": concept_code,
        "value": True,
        "source_excerpt": "supporting excerpt text",
        "confidence": 0.9,
        "assertion_status": "CURRENT",
        "subject": "PATIENT",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. Source-type resolver parity: every real evidence pipeline's
#    PatientEvidenceRecord.source_type (+ note_type where relevant) must
#    resolve onto the correct one of the 4 contract source types.
# ---------------------------------------------------------------------------

def test_hnp_intake_textbox_resolves_to_referral_hnp():
    # app/api/patients.py H&P intake calls harvest_from_source(source_type="REFERRAL_HNP", note_type="HNP")
    assert _resolve_finding_source_type("REFERRAL_HNP", "HNP") == "REFERRAL_HNP"


def test_uploaded_hnp_scan_resolves_to_referral_hnp():
    # document_harvest_job.py: DocumentRecord upload classified by
    # document_intelligence_service.py as document_type_guess="H_AND_P"
    assert _resolve_finding_source_type("DOCUMENT_UPLOAD", "H_AND_P") == "REFERRAL_HNP"


def test_uploaded_generic_document_resolves_to_uploaded_document():
    assert _resolve_finding_source_type("DOCUMENT_UPLOAD", "DISCHARGE_SUMMARY") == "UPLOADED_DOCUMENT"
    assert _resolve_finding_source_type("DOCUMENT_UPLOAD", "LABS_DIAGNOSTICS") == "UPLOADED_DOCUMENT"
    assert _resolve_finding_source_type("DOCUMENT_UPLOAD", None) == "UPLOADED_DOCUMENT"


def test_authored_clinical_documentation_resolves_to_clinical_note():
    for source_type in (
        "CLINICAL_NOTE",
        "COMMUNICATION_LOG",
        "ON_CALL_LOG",
        "INCIDENT_REPORT",
        "IDG_NOTE",
        "PLAN_OF_CARE_REVIEW",
        "CERTIFICATION",
        "F2F_ENCOUNTER",
        "VOLUNTEER_NOTE",
        "FACILITY_NOTIFICATION",
    ):
        assert _resolve_finding_source_type(source_type, None) == "CLINICAL_NOTE"


# ---------------------------------------------------------------------------
# 2. Concept-behavior parity: the SAME raw finding, tagged with each of the
#    4 source types in turn, must validate identically apart from the
#    source_type field itself.
# ---------------------------------------------------------------------------

def _accepted_with_source(concept_code: str, source_type: str, **overrides):
    result = validate_finding(_raw(concept_code, **overrides), source_type=source_type)
    assert result is not None, f"{concept_code} unexpectedly rejected for source_type={source_type}"
    return result


def test_respiratory_dyspnea_with_speech_identical_across_all_sources():
    results = {st: _accepted_with_source("RESP_DYSPNEA_WITH_SPEECH", st) for st in ALL_SOURCE_TYPES}
    for st, finding in results.items():
        as_dict = finding.to_dict()
        assert as_dict["concept_code"] == "RESP_DYSPNEA_WITH_SPEECH"
        assert as_dict["value"] is True
        assert as_dict["assertion_status"] == "CURRENT"
        assert as_dict["source_type"] == st
        # Provenance is the ONLY thing tied to source_type -- strip it and
        # every other field must be byte-identical across all 4 sources.
        without_provenance = {k: v for k, v in as_dict.items() if k != "source_type"}
        reference = {k: v for k, v in results["TRANSCRIPT"].to_dict().items() if k != "source_type"}
        assert without_provenance == reference


def test_oxygen_2l_nasal_cannula_identical_across_all_sources():
    results = {
        st: _accepted_with_source(
            "RESP_OXYGEN_NASAL_CANNULA", st, value=2, source_excerpt="Oxygen at 2 L/min by nasal cannula."
        )
        for st in ALL_SOURCE_TYPES
    }
    reference = {k: v for k, v in results["TRANSCRIPT"].to_dict().items() if k != "source_type"}
    for st, finding in results.items():
        as_dict = finding.to_dict()
        assert as_dict["value"] == 2
        assert as_dict["source_type"] == st
        without_provenance = {k: v for k, v in as_dict.items() if k != "source_type"}
        assert without_provenance == reference


def test_wound_present_location_only_identical_across_all_sources():
    results = {
        st: _accepted_with_source(
            "SKIN_WOUND_PRESENT", st, value="right_foot", source_excerpt="Right foot wound noted."
        )
        for st in ALL_SOURCE_TYPES
    }
    reference = {k: v for k, v in results["TRANSCRIPT"].to_dict().items() if k != "source_type"}
    for st, finding in results.items():
        as_dict = finding.to_dict()
        assert as_dict["value"] == "right_foot"
        without_provenance = {k: v for k, v in as_dict.items() if k != "source_type"}
        assert without_provenance == reference


def test_hemiparesis_identical_across_all_sources():
    results = {
        st: _accepted_with_source(
            "NEURO_HEMIPARESIS_RIGHT", st, source_excerpt="Right hemiparesis after prior stroke."
        )
        for st in ALL_SOURCE_TYPES
    }
    reference = {k: v for k, v in results["TRANSCRIPT"].to_dict().items() if k != "source_type"}
    for st, finding in results.items():
        as_dict = finding.to_dict()
        without_provenance = {k: v for k, v in as_dict.items() if k != "source_type"}
        assert without_provenance == reference


def test_rejection_behavior_identical_across_all_sources():
    """An invalid finding must be rejected the same way regardless of source."""
    for source_type in ALL_SOURCE_TYPES:
        assert validate_finding(_raw("NOT_A_REAL_CONCEPT"), source_type=source_type) is None
        assert validate_finding(_raw("RESP_OXYGEN_NASAL_CANNULA", value=999), source_type=source_type) is None


def test_historical_and_negated_gating_identical_across_all_sources():
    """assertion_status handling (retained but not CURRENT) must not vary by source."""
    for source_type in ALL_SOURCE_TYPES:
        historical = validate_finding(
            _raw("INFECT_CURRENT_SEPSIS", assertion_status="HISTORICAL"), source_type=source_type
        )
        assert historical is not None
        assert historical.assertion_status == "HISTORICAL"

        uncertain = validate_finding(
            _raw("RESP_LUNG_SOUNDS_CRACKLES", assertion_status="UNCERTAIN"), source_type=source_type
        )
        assert uncertain is not None
        assert uncertain.assertion_status == "UNCERTAIN"


def test_batch_validate_findings_identical_across_all_sources():
    payload = [
        _raw("PERF_NYHA_CLASS_III"),
        _raw("CV_EDEMA_LOC_BILATERAL_LE", value="bilateral_le"),
        _raw("NOT_A_REAL_CONCEPT"),  # dropped everywhere
    ]
    counts = {st: len(validate_findings(payload, source_type=st)) for st in ALL_SOURCE_TYPES}
    assert set(counts.values()) == {2}
