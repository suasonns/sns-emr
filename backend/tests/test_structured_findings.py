"""Tests for the shared StructuredFinding contract/validator
(app.services.evidence.structured_findings), the single server-controlled
concept vocabulary used by both the transcript drafter (note_draft_service.py)
and the document/note harvester (ai_extraction_service.py) to safely propose
RNICA structured-field values.

This module only covers what is actually implemented at this layer: concept
validation, assertion-status handling, value_slot bounds, and provenance
round-tripping. Blank-only apply / no-overwrite / clinician-conflict routing
and section-status (EVIDENCE_FOUND vs ASSESSMENT_DRAFTED) are frontend
(RNICA.jsx) concerns layered on top of these validated findings and are not
exercised here.
"""

from __future__ import annotations

from app.services.evidence.structured_findings import (
    CONCEPT_REGISTRY,
    StructuredFinding,
    concept_prompt_catalog,
    is_known_concept,
    validate_finding,
    validate_findings,
)


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
# Registry sanity
# ---------------------------------------------------------------------------

def test_registry_covers_all_eight_requested_sections():
    sections = {m.section for m in CONCEPT_REGISTRY.values()}
    assert sections == {
        "performanceStatus",
        "cardiovascular",
        "respiratory",
        "neurological",
        "infection",
        "skin",
        "nutrition",
        "musculoskeletal",
        # Coverage Expansion (2026-08-28): GI and GU were added as their own
        # sections, in addition to closing remaining gaps within the
        # original eight (ADLs/functional status under musculoskeletal,
        # dentures under nutrition, pressure-relief measures under skin,
        # oxygen hours/SpO2 under respiratory, HOPE BIMS/sleep under
        # neurological). See RNICA Coverage Expansion Matrix.
        "gastrointestinal",
        "genitourinary",
        # Coverage Expansion Phase 2 (2026-08-28): Vitals, Pain, and Endocrine
        # were previously 0% mapped whole sections despite being bounded
        # numeric/enum facts routinely stated in H&P/referral text -- added
        # as their own sections per the RNICA Completion Matrix follow-up.
        "vitals",
        "pain",
        "endocrine",
        # Coverage Expansion Phase 3 (2026-08-28): full gap-analysis matrix
        # sweep -- safety, psychosocial, spiritual, bereavement, personal
        # care, and imminent death were previously 0% mapped; closed every
        # legitimate documented-fact gap while excluding RN/discipline
        # judgment calls (fall-risk/bereavement-risk *scoring*, coping
        # assessment, intervention/referral plans, prognosis judgment).
        "safety",
        "psychosocial",
        "spiritual",
        "bereavement",
        "personalCare",
        "imminentDeath",
        # Coverage Expansion Phase 3 cont'd: teachingNeeds learner-
        # characteristic facts (who the learner is, how they learn, and
        # documented barriers) -- this-visit teaching delivered/response is
        # excluded as a workflow record, not an admission fact.
        "teachingNeeds",
        # Coverage Expansion Phase 3 completion: CDPH-required Caregiver
        # Willingness & Capability Evaluation lives under
        # demographics.pcg.caregiverEvaluation, not its own top-level
        # section -- evaluationNotes (unbounded free text) is excluded.
        "demographics",
    }


def test_is_known_concept():
    assert is_known_concept("RESP_DYSPNEA_WITH_SPEECH") is True
    assert is_known_concept("NOT_A_REAL_CONCEPT") is False


def test_concept_prompt_catalog_lists_every_registered_code():
    catalog = concept_prompt_catalog()
    for code in CONCEPT_REGISTRY:
        assert code in catalog


# ---------------------------------------------------------------------------
# 1. Transcript source
# ---------------------------------------------------------------------------

def test_transcript_source_scenario_sob_with_speech():
    finding = validate_finding(
        _raw("RESP_DYSPNEA_WITH_SPEECH", source_excerpt="Short of breath while speaking."),
        source_type="TRANSCRIPT",
        source_record_id="rec-1",
        source_date="2024-05-01",
    )
    assert finding is not None
    assert finding.source_type == "TRANSCRIPT"
    assert finding.value is True
    assert finding.assertion_status == "CURRENT"
    assert finding.source_excerpt == "Short of breath while speaking."


# ---------------------------------------------------------------------------
# 2. HNP/referral source
# ---------------------------------------------------------------------------

def test_hnp_referral_source_scenario():
    finding = validate_finding(
        _raw("NEURO_HEMIPARESIS_RIGHT", source_excerpt="Right hemiparesis after prior CVA."),
        source_type="REFERRAL_HNP",
        source_record_id="hnp-1",
    )
    assert finding is not None
    assert finding.source_type == "REFERRAL_HNP"


# ---------------------------------------------------------------------------
# 3. Current finding
# ---------------------------------------------------------------------------

def test_current_finding_is_applied():
    finding = validate_finding(_raw("INFECT_CURRENT_SEPSIS", assertion_status="CURRENT"), source_type="TRANSCRIPT")
    assert finding is not None
    assert finding.assertion_status == "CURRENT"


# ---------------------------------------------------------------------------
# 4. Historical finding -- validated (so it's not silently lost) but tagged
# HISTORICAL, never CURRENT -- the frontend must never write this into a
# current-status control.
# ---------------------------------------------------------------------------

def test_historical_finding_retained_but_not_current():
    finding = validate_finding(
        _raw(
            "INFECT_CURRENT_SEPSIS",
            assertion_status="HISTORICAL",
            source_excerpt="History of septic shock from pneumonia in 2023, resolved.",
        ),
        source_type="TRANSCRIPT",
    )
    assert finding is not None
    assert finding.assertion_status == "HISTORICAL"
    assert finding.assertion_status != "CURRENT"


# ---------------------------------------------------------------------------
# 5. Negated finding
# ---------------------------------------------------------------------------

def test_negated_finding_retained_as_negated():
    finding = validate_finding(
        _raw(
            "RESP_OXYGEN_NASAL_CANNULA",
            value=None,
            assertion_status="NEGATED",
            source_excerpt="Patient is not using oxygen.",
        ),
        source_type="TRANSCRIPT",
    )
    # RESP_OXYGEN_NASAL_CANNULA has a numeric value_slot (liters/min) -- a
    # negated oxygen statement has no device/rate to report, so the correct
    # concept for "not using oxygen" is RESP_OXYGEN_NOT_IN_USE (a pure
    # presence concept), not a negated numeric concept. This confirms the
    # numeric concept correctly rejects a valueless/negated submission...
    assert finding is None
    # ...and that the dedicated negative concept validates correctly instead.
    negated = validate_finding(
        _raw("RESP_OXYGEN_NOT_IN_USE", assertion_status="NEGATED", source_excerpt="Patient is not using oxygen."),
        source_type="TRANSCRIPT",
    )
    assert negated is not None
    assert negated.assertion_status == "NEGATED"
    assert negated.value is True  # "the fact that oxygen is not in use" is itself the asserted fact


# ---------------------------------------------------------------------------
# 6. Uncertain finding
# ---------------------------------------------------------------------------

def test_uncertain_finding_defaults_when_assertion_status_missing():
    finding = validate_finding(
        _raw("NEURO_DELIRIUM_PRESENT", assertion_status="not-a-real-status"),
        source_type="TRANSCRIPT",
    )
    assert finding is not None
    assert finding.assertion_status == "UNCERTAIN"


# ---------------------------------------------------------------------------
# 7. Clinician value already present -- this validator has no notion of an
# existing chart value (that's the frontend apply layer's job); documented
# here so the contract boundary is explicit and not silently unspecified.
# ---------------------------------------------------------------------------

def test_validator_has_no_opinion_about_existing_clinician_values():
    finding = validate_finding(_raw("CV_JVD_PRESENT"), source_type="TRANSCRIPT")
    assert finding is not None
    # Blank-only / no-overwrite / conflict-routing is enforced client-side
    # when applying this validated finding to formData, not here.


# ---------------------------------------------------------------------------
# 8. Invalid enum / unknown concept / out-of-range numeric
# ---------------------------------------------------------------------------

def test_unknown_concept_is_rejected():
    assert validate_finding(_raw("MADE_UP_CONCEPT"), source_type="TRANSCRIPT") is None


def test_out_of_range_numeric_value_is_rejected():
    finding = validate_finding(
        _raw("RESP_OXYGEN_NASAL_CANNULA", value=999),
        source_type="TRANSCRIPT",
    )
    assert finding is None


def test_non_numeric_value_for_numeric_slot_is_rejected():
    finding = validate_finding(
        _raw("RESP_OXYGEN_NASAL_CANNULA", value="a lot"),
        source_type="TRANSCRIPT",
    )
    assert finding is None


def test_valid_numeric_value_is_accepted_and_coerced_to_float():
    finding = validate_finding(
        _raw("RESP_OXYGEN_NASAL_CANNULA", value=2),
        source_type="TRANSCRIPT",
    )
    assert finding is not None
    assert finding.value == 2.0


def test_missing_source_excerpt_is_rejected():
    finding = validate_finding(_raw("CV_JVD_PRESENT", source_excerpt=""), source_type="TRANSCRIPT")
    assert finding is None


def test_invalid_source_type_is_rejected():
    finding = validate_finding(_raw("CV_JVD_PRESENT"), source_type="NOT_A_SOURCE_TYPE")
    assert finding is None


# ---------------------------------------------------------------------------
# 9. Duplicate evidence -- the validator processes each item independently
# and does not dedupe; two identical findings both validate. De-duplication
# of the *effect on the chart* is handled by the frontend's blank-only
# apply rule (the second application is a no-op once the field is filled),
# not by discarding data here.
# ---------------------------------------------------------------------------

def test_duplicate_findings_both_validate_independently():
    raw_list = [_raw("CV_JVD_PRESENT"), _raw("CV_JVD_PRESENT")]
    validated = validate_findings(raw_list, source_type="TRANSCRIPT")
    assert len(validated) == 2
    assert validated[0].concept_code == validated[1].concept_code == "CV_JVD_PRESENT"


# ---------------------------------------------------------------------------
# 10. Page reload / persistence -- StructuredFinding round-trips through
# to_dict() (the JSON-serializable shape persisted on ai_note_draft /
# suggested structured findings) without losing any field.
# ---------------------------------------------------------------------------

def test_to_dict_round_trip_preserves_all_fields():
    finding = validate_finding(
        _raw("SKIN_WOUND_PRESENT", value="right foot", source_excerpt="Right foot wound."),
        source_type="TRANSCRIPT",
        source_record_id="rec-9",
        source_date="2024-06-01",
        model_version="gpt-5.4",
        prompt_version="v1",
    )
    assert finding is not None
    payload = finding.to_dict()
    rebuilt = StructuredFinding(**payload)
    assert rebuilt == finding
    assert payload["concept_code"] == "SKIN_WOUND_PRESENT"
    assert payload["value"] == "right foot"
    assert payload["source_record_id"] == "rec-9"
    assert payload["source_date"] == "2024-06-01"
    assert payload["model_version"] == "gpt-5.4"


# ---------------------------------------------------------------------------
# 11. Provenance display -- every accepted finding always carries a full,
# non-empty provenance trail (excerpt/source_type/assertion_status/subject),
# regardless of which concept it is.
# ---------------------------------------------------------------------------

def test_every_accepted_finding_carries_full_provenance():
    findings = validate_findings(
        [_raw("CV_JVD_PRESENT"), _raw("RESP_LUNG_SOUNDS_CRACKLES")],
        source_type="UPLOADED_DOCUMENT",
        source_record_id="doc-1",
        source_date="2024-01-15",
    )
    assert len(findings) == 2
    for f in findings:
        assert f.source_excerpt
        assert f.source_type == "UPLOADED_DOCUMENT"
        assert f.assertion_status in {"CURRENT", "HISTORICAL", "NEGATED", "UNCERTAIN"}
        assert f.subject in {"PATIENT", "FAMILY", "OTHER"}
        assert f.source_record_id == "doc-1"
        assert f.source_date == "2024-01-15"


# ---------------------------------------------------------------------------
# 12. No false section completion -- this validator module has no concept of
# section completion status at all (that lives entirely in RNICA.jsx's
# sectionStatuses); confirmed by absence, not by a positive assertion here.
# ---------------------------------------------------------------------------

def test_module_has_no_completion_concept():
    assert not hasattr(StructuredFinding, "status")
    assert not any(name.lower().startswith("complete") for name in dir(StructuredFinding))


# ---------------------------------------------------------------------------
# Wound / hemiparesis / oxygen specific scenarios from the user's test plan
# ---------------------------------------------------------------------------

def test_wound_present_only_populates_location_no_invented_detail():
    mapping = CONCEPT_REGISTRY["SKIN_WOUND_PRESENT"]
    assert mapping.value_slot is not None
    assert mapping.value_slot.path == "wounds[].location"
    assert mapping.draft_row_field == "location"
    # No FieldWrite for stage/size/drainage/treatment is present.
    written_paths = {fw.path for fw in mapping.writes}
    assert written_paths == {"skinConditionsPresent", "wounds"}


def test_hemiparesis_concept_writes_neuro_and_musculoskeletal_sections():
    mapping = CONCEPT_REGISTRY["NEURO_HEMIPARESIS_RIGHT"]
    sections_written = {fw.section or mapping.section for fw in mapping.writes}
    assert sections_written == {"neurological", "musculoskeletal"}


def test_oxygen_2l_nasal_cannula_full_scenario():
    finding = validate_finding(
        _raw(
            "RESP_OXYGEN_NASAL_CANNULA",
            value=2,
            source_excerpt="Oxygen at 2 L/min by nasal cannula.",
        ),
        source_type="TRANSCRIPT",
        source_record_id="rec-2",
    )
    assert finding is not None
    assert finding.value == 2.0
    assert finding.source_excerpt == "Oxygen at 2 L/min by nasal cannula."
    mapping = CONCEPT_REGISTRY["RESP_OXYGEN_NASAL_CANNULA"]
    written = {(fw.path, fw.value) for fw in mapping.writes}
    assert ("oxygenTherapy.inUse", True) in written
    assert ("oxygenTherapy.type", "Nasal cannula") in written


# ---------------------------------------------------------------------------
# Registry defect fixes: CHF gap, contracture/rigidity severity inference,
# wound multi-site splitting.
# ---------------------------------------------------------------------------

def test_chf_systolic_heart_failure_maps_to_cardiovascular():
    assert "CV_HEART_FAILURE_SYSTOLIC" in CONCEPT_REGISTRY
    mapping = CONCEPT_REGISTRY["CV_HEART_FAILURE_SYSTOLIC"]
    assert mapping.section == "cardiovascular"
    written = {(fw.path, fw.value, fw.op) for fw in mapping.writes}
    assert ("heartFailurePresent", True, "set") in written
    assert ("heartFailureType", "Systolic", "multi_add") in written

    finding = validate_finding(
        _raw("CV_HEART_FAILURE_SYSTOLIC", source_excerpt="SYSTOLIC HEART FAILURE, CHRONIC"),
        source_type="REFERRAL_HNP",
        source_record_id="loren-hnp",
    )
    assert finding is not None
    assert finding.concept_code == "CV_HEART_FAILURE_SYSTOLIC"


def test_heart_failure_presence_and_absence_concepts_exist():
    assert "CV_HEART_FAILURE_PRESENT" in CONCEPT_REGISTRY
    assert "CV_HEART_FAILURE_DIASTOLIC" in CONCEPT_REGISTRY
    assert "CV_HEART_FAILURE_UNSPECIFIED_TYPE" in CONCEPT_REGISTRY
    absent = CONCEPT_REGISTRY["CV_HEART_FAILURE_ABSENT"]
    assert {(fw.path, fw.value) for fw in absent.writes} == {("heartFailurePresent", False)}


def test_contractures_present_does_not_infer_mild_severity():
    mapping = CONCEPT_REGISTRY["MSK_CONTRACTURES_PRESENT"]
    written = {(fw.path, fw.value) for fw in mapping.writes}
    # Presence-only: must NOT write a severity value onto the severity radio.
    assert written == {("contracturesPresent", True)}
    assert "contractures" not in {fw.path for fw in mapping.writes}


def test_contractures_severity_only_applies_when_explicit():
    for severity in ("Mild", "Moderate", "Severe"):
        code = f"MSK_CONTRACTURES_SEVERITY_{severity.upper()}"
        assert code in CONCEPT_REGISTRY
        mapping = CONCEPT_REGISTRY[code]
        written = {(fw.path, fw.value) for fw in mapping.writes}
        assert ("contracturesPresent", True) in written
        assert ("contractures", severity) in written


def test_rigidity_present_does_not_infer_mild_severity():
    mapping = CONCEPT_REGISTRY["MSK_RIGIDITY_PRESENT"]
    written = {(fw.path, fw.value) for fw in mapping.writes}
    assert written == {("rigidityPresent", True)}
    assert "rigidity" not in {fw.path for fw in mapping.writes}


def test_rigidity_severity_only_applies_when_explicit():
    for severity in ("Mild", "Moderate", "Severe"):
        code = f"MSK_RIGIDITY_SEVERITY_{severity.upper()}"
        assert code in CONCEPT_REGISTRY
        mapping = CONCEPT_REGISTRY[code]
        written = {(fw.path, fw.value) for fw in mapping.writes}
        assert ("rigidityPresent", True) in written
        assert ("rigidity", severity) in written


def test_wound_location_multi_site_semicolon_splits_into_two_findings():
    # Reproduces the exact defect found during the Loren audit: the model
    # combined two anatomic sites into one semicolon-joined string instead
    # of emitting two separate findings.
    raw = [
        _raw(
            "SKIN_WOUND_PRESENT",
            value="left buttock; right foot",
            source_excerpt="Wounds noted: left side of buttocks and right foot.",
        )
    ]
    findings = validate_findings(raw, source_type="REFERRAL_HNP", source_record_id="loren-hnp")
    assert len(findings) == 2
    values = sorted(f.value for f in findings)
    assert values == ["left buttock", "right foot"]
    for f in findings:
        assert f.concept_code == "SKIN_WOUND_PRESENT"
        # Every split copy keeps the same shared provenance/assertion fields.
        assert f.source_excerpt == "Wounds noted: left side of buttocks and right foot."
        assert f.assertion_status == "CURRENT"


def test_wound_location_multi_site_and_conjunction_splits():
    raw = [_raw("SKIN_WOUND_PRESENT", value="left buttock and right foot")]
    findings = validate_findings(raw, source_type="TRANSCRIPT", source_record_id="rec-3")
    assert sorted(f.value for f in findings) == ["left buttock", "right foot"]


def test_wound_location_single_site_is_not_split():
    raw = [_raw("SKIN_WOUND_PRESENT", value="right foot")]
    findings = validate_findings(raw, source_type="TRANSCRIPT", source_record_id="rec-4")
    assert len(findings) == 1
    assert findings[0].value == "right foot"


def test_multi_site_split_does_not_affect_non_free_text_concepts():
    # A boolean/numeric concept's value must never be treated as a
    # separator-delimited list even if it happens to contain "and"-like
    # substrings -- only free_text_bounded value slots are split.
    raw = [_raw("CV_HEART_FAILURE_PRESENT", value=True)]
    findings = validate_findings(raw, source_type="TRANSCRIPT", source_record_id="rec-5")
    assert len(findings) == 1
    assert findings[0].value is True


# ---------------------------------------------------------------------------
# RNICA Completion Sprint: Symptom Impact (HOPE J2051) cross-writes
# ---------------------------------------------------------------------------

def test_pain_severity_cross_writes_symptom_impact_with_0_to_3_vocabulary():
    mapping = CONCEPT_REGISTRY["PAIN_SEVERITY_MODERATE"]
    symptom_writes = [fw for fw in mapping.writes if fw.section == "symptomImpact"]
    assert len(symptom_writes) == 1
    assert symptom_writes[0].path == "pain"
    assert symptom_writes[0].value == "2"


def test_sob_severity_cross_writes_symptom_impact_but_dyspnea_at_rest_does_not():
    mapping = CONCEPT_REGISTRY["RESP_SOB_SEVERE"]
    symptom_writes = [fw for fw in mapping.writes if fw.section == "symptomImpact"]
    assert len(symptom_writes) == 1
    assert symptom_writes[0].path == "shortnessOfBreath"
    assert symptom_writes[0].value == "3"
    # RESP_DYSPNEA_AT_REST is an exertion-level fact, not a clean 0-3 severity
    # -- it must NOT cross-write symptomImpact.
    at_rest = CONCEPT_REGISTRY["RESP_DYSPNEA_AT_REST"]
    assert not any(fw.section == "symptomImpact" for fw in at_rest.writes)


def test_gi_symptom_severities_cross_write_symptom_impact_with_0_to_3_vocabulary():
    cases = [
        ("GI_NAUSEA_MILD", "nausea", "1"),
        ("GI_VOMITING_SEVERE", "vomiting", "3"),
        ("GI_DIARRHEA_NONE", "diarrhea", "0"),
        ("GI_CONSTIPATION_MODERATE", "constipation", "2"),
    ]
    for concept_code, path, expected_value in cases:
        mapping = CONCEPT_REGISTRY[concept_code]
        symptom_writes = [fw for fw in mapping.writes if fw.section == "symptomImpact"]
        assert len(symptom_writes) == 1, concept_code
        assert symptom_writes[0].path == path
        assert symptom_writes[0].value == expected_value
        # The original word-vocabulary section write must still be intact.
        own_section_writes = [fw for fw in mapping.writes if fw.section is None]
        assert any(fw.path == path for fw in own_section_writes)


def test_new_anxiety_and_agitation_severity_concepts_write_only_symptom_impact():
    for code, path, value in [
        ("SYMPTOM_ANXIETY_SEVERITY_NONE", "anxiety", "0"),
        ("SYMPTOM_ANXIETY_SEVERITY_SEVERE", "anxiety", "3"),
        ("SYMPTOM_AGITATION_SEVERITY_MILD", "agitation", "1"),
        ("SYMPTOM_AGITATION_SEVERITY_MODERATE", "agitation", "2"),
    ]:
        mapping = CONCEPT_REGISTRY[code]
        assert len(mapping.writes) == 1
        assert mapping.writes[0].section == "symptomImpact"
        assert mapping.writes[0].path == path
        assert mapping.writes[0].value == value


def test_symptom_impact_severity_findings_validate_and_apply_when_current():
    raw = [
        _raw("PAIN_SEVERITY_SEVERE"),
        _raw("SYMPTOM_ANXIETY_SEVERITY_MILD"),
        _raw("SYMPTOM_AGITATION_SEVERITY_NONE"),
        _raw("GI_NAUSEA_MODERATE"),
    ]
    findings = validate_findings(raw, source_type="TRANSCRIPT", source_record_id="rec-6")
    assert len(findings) == 4
    assert all(f.assertion_status == "CURRENT" for f in findings)


# ---------------------------------------------------------------------------
# RNICA Completion Sprint: Skin/Wounds (15 fields, wired onto the existing
# wound draft row rather than fabricating a second row per attribute)
# ---------------------------------------------------------------------------

def test_wound_sub_field_concepts_use_set_row_field_not_push_draft_row():
    # Every new wound attribute concept must enrich the SAME row
    # SKIN_WOUND_PRESENT created -- never create a second row for one wound.
    enum_flag_codes = [
        "SKIN_WOUND_STAGE_2", "SKIN_WOUND_TYPE_PRESSURE_INJURY",
        "SKIN_WOUND_DRAINAGE_MODERATE", "SKIN_WOUND_ODOR_FOUL",
        "SKIN_WOUND_PRESSURE_INJURY_FLAG", "SKIN_WOUND_SKIN_TEAR_FLAG",
        "SKIN_WOUND_SURGICAL_FLAG", "SKIN_WOUND_NONHEALING_FLAG",
    ]
    for code in enum_flag_codes:
        mapping = CONCEPT_REGISTRY[code]
        assert len(mapping.writes) == 1, code
        assert mapping.writes[0].op == "set_row_field", code
        assert mapping.writes[0].path.startswith("wounds[]."), code


def test_wound_measurement_and_free_text_concepts_use_bounded_row_value_slots():
    for code, path, kind in [
        ("SKIN_WOUND_LENGTH_CM", "wounds[].length", "numeric"),
        ("SKIN_WOUND_WIDTH_CM", "wounds[].width", "numeric"),
        ("SKIN_WOUND_DEPTH_CM", "wounds[].depth", "numeric"),
        ("SKIN_WOUND_DRESSING", "wounds[].dressing", "free_text_bounded"),
        ("SKIN_WOUND_DRESSING_FREQUENCY", "wounds[].dressingFrequency", "free_text_bounded"),
        ("SKIN_WOUND_CURRENT_TREATMENT", "wounds[].currentTreatment", "free_text_bounded"),
        ("SKIN_WOUND_PERIWOUND_CONDITION", "wounds[].periwoundCondition", "free_text_bounded"),
    ]:
        mapping = CONCEPT_REGISTRY[code]
        assert mapping.writes == (), code  # no fixed FieldWrite -- value comes from the finding itself
        assert mapping.value_slot is not None, code
        assert mapping.value_slot.kind == kind, code
        assert mapping.value_slot.path == path, code


def test_wound_stage_enum_covers_all_clinically_assertable_cms_stages():
    # N/A is intentionally excluded -- never an AI-asserted value.
    stage_codes = {c for c in CONCEPT_REGISTRY if c.startswith("SKIN_WOUND_STAGE_")}
    assert stage_codes == {
        "SKIN_WOUND_STAGE_1", "SKIN_WOUND_STAGE_2", "SKIN_WOUND_STAGE_3",
        "SKIN_WOUND_STAGE_4", "SKIN_WOUND_STAGE_UNSTAGEABLE", "SKIN_WOUND_STAGE_DTI",
    }


def test_wound_bounded_measurements_respect_clinical_ranges():
    length = CONCEPT_REGISTRY["SKIN_WOUND_LENGTH_CM"].value_slot
    assert length.min_value == 0
    assert length.max_value == 30

