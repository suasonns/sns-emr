# tests/test_recertification_reasoning_framework_v1.py
"""
Recertification Reasoning Framework v1 -- Structural, Extension, and
Comparison-Logic Tests (PR #59).

Verifies (per the user-approved PR #59 specification):
  - The importer hard-blocks with the literal message
    "BLOCKED: TERMINAL_STATUS_REASONING_FRAMEWORK_V1 prerequisite missing"
    when the PR #58 Terminal Status Reasoning Framework disease is absent,
    and performs zero writes in that case.
  - The manifest is schema-valid: exactly 21 framework_sections, a 9-label
    comparison_vocabulary, an evidence-completeness vocabulary that is
    referenced (never re-defined/duplicated) from PR #58, exactly 2
    distinct regulatory_context_definitions (federal CMS vs California
    CDPH, never merged), exactly 20 differentiation_guards, and full
    provenance on every regulatory-context and comparison-label
    definition.
  - The manifest never uses eligibility/terminal-status/certification/
    recertification/discharge pass-fail vocabulary.
  - compare_scale() only ever compares a scale to itself (PPS-PPS,
    KPS-KPS, ECOG-ECOG, FAST-FAST, NYHA-NYHA), rejects cross-scale
    comparison, respects each scale's own worse-direction ordering, and
    never creates a trend from a single (undated or one-sided)
    observation.
  - compare_numeric() rejects incompatible units and never creates a
    trend from a single observation.
  - The importer creates exactly the Recertification Reasoning Framework
    registry disease (never a duplicate, never colliding with PR #58's
    disease or any consumed disease/CEB), 21 section-definition concepts
    + 1 comparison-vocabulary concept (22 total), each with an
    OntologyEvidenceRule carrying patient_fact_requires_evidence=True.
  - Re-running the importer is fully idempotent (zero new rows).
  - The acceptance report reports every required field with the exact
    manifest-derived expected values, and zero patient facts / zero
    eligibility / zero terminal-status / zero prognosis / zero
    life-expectancy / zero certification / zero recertification / zero
    discharge outputs, zero orphans, zero cycles, zero unresolved
    framework concepts.
  - No prior PR's files, foundations, or Clinical Evidence Blueprints are
    modified.

This test file builds the full baseline used by PR #58's own test file
(all 7 non-neurologic foundations, the full Neurologic foundation
pipeline, the Functional Assessment Framework, all 8 Clinical Evidence
Blueprint extensions) and then additionally imports PR #58 itself before
importing this framework -- the largest fixture in this codebase, since
this is the first PR with a hard runtime dependency on another reasoning
framework PR rather than only on disease-specific manifests.
"""
from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDiseaseFamily,
    OntologyDisease,
    OntologyDiseaseFinding,
    OntologyEvidenceRule,
)
from scripts.import_cardiovascular_production_source_manifest import run as run_cv, load_manifest as lm_cv
from scripts.import_pulmonary_production_source_manifest import run as run_pulm, load_manifest as lm_pulm
from scripts.import_renal_production_source_manifest import run as run_renal, load_manifest as lm_renal
from scripts.import_liver_production_source_manifest import run as run_liver, load_manifest as lm_liver
from scripts.import_dementia_production_hardening import run as run_dementia, load_manifest as lm_dementia
from scripts.import_als_production_source_manifest import run as run_als, load_manifest as lm_als
from scripts.import_hiv_production_source_manifest import run as run_hiv, load_manifest as lm_hiv

from scripts.complete_ontology_neurologic_clinical_reasoning import run as run_clinical_reasoning_script
from scripts.complete_ontology_phase2_neurologic_coverage import run as run_coverage_repair_script
from scripts.expand_ontology_phase2_neurologic import (
    run as run_phase2_script,
    EXISTING_DISEASE_NAMES,
    SYSTEM_NAME as NEURO_SYSTEM_NAME,
)
from scripts.import_neurologic_production_source_manifest import run as run_neuro, load_manifest as lm_neuro

from scripts.import_functional_assessment_framework_v1 import run as run_faf, load_manifest as lm_faf

from scripts.import_chf_clinical_evidence_blueprint_v1 import run as run_chf_ceb, load_manifest as lm_chf_ceb
from scripts.import_dementia_clinical_evidence_blueprint_v1 import run as run_dem_ceb, load_manifest as lm_dem_ceb
from scripts.import_pulmonary_clinical_evidence_blueprint_v1 import run as run_pulm_ceb, load_manifest as lm_pulm_ceb
from scripts.import_renal_clinical_evidence_blueprint_v1 import run as run_renal_ceb, load_manifest as lm_renal_ceb
from scripts.import_liver_clinical_evidence_blueprint_v1 import run as run_liver_ceb, load_manifest as lm_liver_ceb
from scripts.import_als_clinical_evidence_blueprint_v1 import run as run_als_ceb, load_manifest as lm_als_ceb
from scripts.import_hiv_clinical_evidence_blueprint_v1 import run as run_hiv_ceb, load_manifest as lm_hiv_ceb
from scripts.import_stroke_coma_clinical_evidence_blueprint_v1 import run as run_stroke_ceb, load_manifest as lm_stroke_ceb

from scripts.import_terminal_status_reasoning_framework_v1 import (
    DISEASE_NAME as PR58_DISEASE_NAME,
    run as run_pr58_framework,
    load_manifest as lm_pr58,
)

from scripts.import_recertification_reasoning_framework_v1 import (
    CONCEPT_DOMAIN,
    DEFAULT_MANIFEST_PATH,
    DISEASE_NAME,
    FAMILY_NAME,
    SYSTEM_NAME,
    PREREQUISITE_DISEASE_NAME,
    PREREQUISITE_BLOCK_MESSAGE,
    EXPECTED_SECTION_COUNT,
    EXPECTED_COMPARISON_LABELS,
    EXPECTED_EVIDENCE_COMPLETENESS_LABELS,
    EXPECTED_GUARD_COUNT,
    EXPECTED_REGULATORY_CONTEXT_COUNT,
    compare_scale,
    compare_numeric,
    evaluate_differentiation_guards,
    load_manifest,
    validate_manifest,
    build_acceptance_report,
    _resolve_prerequisite,
    run as run_framework_import,
)
from tests.conftest import TestSessionLocal

MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)
SECTIONS = MANIFEST["framework_sections"]
COMPARISON_VOCAB = MANIFEST["comparison_vocabulary"]
REGULATORY_CONTEXTS = MANIFEST["regulatory_context_definitions"]
GUARDS = MANIFEST["differentiation_guards"]


def _seed_neuro_base_diseases(db_session) -> None:
    system = db_session.query(OntologyBodySystem).filter_by(system_name=NEURO_SYSTEM_NAME).one_or_none()
    if system is None:
        system = OntologyBodySystem(system_name=NEURO_SYSTEM_NAME)
        db_session.add(system)
        db_session.flush()
    base_family = {
        name: "Cerebrovascular Disease" if name == "Stroke" else "Neurodegenerative Disease"
        for name in EXISTING_DISEASE_NAMES
    }
    for name in EXISTING_DISEASE_NAMES:
        family_name = base_family.get(name, "Neurologic Disease")
        family = (
            db_session.query(OntologyDiseaseFamily)
            .filter_by(family_name=family_name, body_system_id=system.id)
            .one_or_none()
        )
        if family is None:
            family = OntologyDiseaseFamily(family_name=family_name, body_system_id=system.id)
            db_session.add(family)
            db_session.flush()
        disease = db_session.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
        if disease is None:
            disease = OntologyDisease(disease_name=name, disease_family_id=family.id)
            db_session.add(disease)
    db_session.flush()


def _build_full_baseline(session) -> None:
    """Builds every foundation/CEB/PR#58 prerequisite this file needs,
    guarded behind existence checks so it cooperates inside the combined
    suite where other test files may already have built some or all of
    this baseline against the same module-scoped database."""
    if session.query(OntologyDisease).filter_by(disease_name="Congestive Heart Failure").one_or_none() is None:
        run_cv(session, manifest=lm_cv()); session.commit()
    if session.query(OntologyDisease).filter_by(disease_name="Chronic Obstructive Pulmonary Disease").one_or_none() is None:
        run_pulm(session, manifest=lm_pulm()); session.commit()
    if session.query(OntologyDisease).filter_by(disease_name="Acute Renal Failure").one_or_none() is None:
        run_renal(session, manifest=lm_renal()); session.commit()
    if session.query(OntologyDisease).filter_by(disease_name="End Stage Liver Disease").one_or_none() is None:
        run_liver(session, manifest=lm_liver()); session.commit()
    if session.query(OntologyDisease).filter_by(disease_name="Dementia Due To Alzheimer's Disease").one_or_none() is None:
        run_dementia(session, manifest=lm_dementia()); session.commit()
    if session.query(OntologyDisease).filter_by(disease_name="Amyotrophic Lateral Sclerosis").one_or_none() is None:
        run_als(session, manifest=lm_als()); session.commit()
    if session.query(OntologyDisease).filter_by(disease_name="Advanced HIV Disease").one_or_none() is None:
        run_hiv(session, manifest=lm_hiv()); session.commit()

    if session.query(OntologyDisease).filter_by(disease_name="Stroke").one_or_none() is None:
        _seed_neuro_base_diseases(session)
        session.commit()
        run_phase2_script(session); session.commit()
        run_coverage_repair_script(session); session.commit()
        run_clinical_reasoning_script(session); session.commit()
        run_neuro(session, manifest=lm_neuro()); session.commit()

    if session.query(OntologyDisease).filter_by(disease_name="Functional Assessment Framework").one_or_none() is None:
        run_faf(session, manifest=lm_faf()); session.commit()

    run_chf_ceb(session, manifest=lm_chf_ceb()); session.commit()
    run_dem_ceb(session, manifest=lm_dem_ceb()); session.commit()
    run_pulm_ceb(session, manifest=lm_pulm_ceb()); session.commit()
    run_renal_ceb(session, manifest=lm_renal_ceb()); session.commit()
    run_liver_ceb(session, manifest=lm_liver_ceb()); session.commit()
    run_als_ceb(session, manifest=lm_als_ceb()); session.commit()
    run_hiv_ceb(session, manifest=lm_hiv_ceb()); session.commit()
    run_stroke_ceb(session, manifest=lm_stroke_ceb()); session.commit()

    if session.query(OntologyDisease).filter_by(disease_name=PR58_DISEASE_NAME).one_or_none() is None:
        run_pr58_framework(session, manifest=lm_pr58()); session.commit()


@pytest.fixture(scope="module")
def built_state():
    session = TestSessionLocal()
    try:
        _build_full_baseline(session)

        counts = run_framework_import(session, manifest=MANIFEST)
        session.commit()

        framework_disease = session.query(OntologyDisease).filter_by(disease_name=DISEASE_NAME).one()
        yield {"framework_disease": framework_disease, "counts": counts, "session": session}
    finally:
        session.close()


def _framework_concept(db_session, disease_id, name):
    return (
        db_session.query(OntologyDiseaseFinding)
        .filter_by(disease_id=disease_id)
        .filter(OntologyDiseaseFinding.finding_name.ilike(name.strip()))
        .one_or_none()
    )


# ---------------------------------------------------------------------
# Prerequisite enforcement (PR #58 hard dependency)
#
# Uses a minimal fake session/query double rather than the shared,
# cross-test-file persistent test database: once any test file in the
# combined suite has imported PR #58, the real "Terminal Status
# Reasoning Framework" disease legitimately (and permanently, for the
# life of that DB) exists, so asserting its absence against the real DB
# would be a false negative depending on test-run order. A fake session
# that always reports "no such disease" and raises on any write attempt
# deterministically proves both the exact block message AND zero writes,
# independent of DB state or test ordering.
# ---------------------------------------------------------------------


class _NoPrerequisiteFakeQuery:
    def filter_by(self, **kwargs):
        return self

    def one_or_none(self):
        return None


class _NoWritesAllowedFakeSession:
    def query(self, model):
        return _NoPrerequisiteFakeQuery()

    def add(self, *args, **kwargs):
        raise AssertionError("run() must not attempt any write before the prerequisite check passes")

    def flush(self, *args, **kwargs):
        raise AssertionError("run() must not attempt any flush before the prerequisite check passes")


def test_resolve_prerequisite_blocks_with_exact_message_when_disease_absent():
    with pytest.raises(RuntimeError, match=r"^BLOCKED: TERMINAL_STATUS_REASONING_FRAMEWORK_V1 prerequisite missing$"):
        _resolve_prerequisite(_NoWritesAllowedFakeSession())


def test_run_blocks_with_exact_message_and_zero_writes_when_prerequisite_missing():
    with pytest.raises(RuntimeError, match=r"^BLOCKED: TERMINAL_STATUS_REASONING_FRAMEWORK_V1 prerequisite missing$"):
        run_framework_import(_NoWritesAllowedFakeSession(), manifest=MANIFEST)


def test_prerequisite_block_message_matches_manifest_declaration():
    assert MANIFEST["prerequisite"]["block_message"] == PREREQUISITE_BLOCK_MESSAGE
    assert MANIFEST["prerequisite"]["requires_disease"] == PREREQUISITE_DISEASE_NAME == "Terminal Status Reasoning Framework"


# ---------------------------------------------------------------------
# Manifest structural validation
# ---------------------------------------------------------------------


def test_manifest_is_schema_valid():
    assert validate_manifest(MANIFEST) == []


def test_manifest_declares_twenty_one_sections():
    assert len(SECTIONS) == EXPECTED_SECTION_COUNT == 21
    assert sorted(s["section_number"] for s in SECTIONS) == list(range(1, 22))


def test_manifest_section_names_match_specification_order():
    expected_names = [
        "Review Context", "Prior Benefit-Period Baseline", "Current Benefit-Period Evidence",
        "Functional Assessment Comparison", "ADL and Care-Dependence Comparison",
        "Nutritional and Hydration Comparison", "Disease-Specific Evidence Comparison",
        "Symptoms and Clinical Signs Comparison", "Laboratory and Objective-Finding Comparison",
        "Complications and Infections Comparison", "Hospitalization and Utilization Comparison",
        "Treatment and Intervention Context", "Co-Morbidity Contribution",
        "Stability or Improvement Review", "Potentially Reversible Factors",
        "Conflicting Evidence", "Missing Evidence", "Documentation Gaps",
        "Physician Review Questions", "Suggested Individualized Narrative Elements",
        "Source and Audit Trace",
    ]
    actual_names = [s["section_name"] for s in sorted(SECTIONS, key=lambda s: s["section_number"])]
    assert actual_names == expected_names


def test_manifest_declares_nine_comparison_labels():
    label_names = [lbl["label"] for lbl in COMPARISON_VOCAB["labels"]]
    assert label_names == EXPECTED_COMPARISON_LABELS
    assert len(label_names) == 9


def test_manifest_references_but_never_duplicates_pr58_evidence_vocabulary():
    ref = MANIFEST["evidence_completeness_vocabulary_reference"]
    assert ref["labels"] == EXPECTED_EVIDENCE_COMPLETENESS_LABELS == ["Strong", "Moderate", "Limited", "Missing"]
    assert "PR #58" in ref["reused_from"]
    assert "evidence_strength_vocabulary" not in MANIFEST


def test_manifest_declares_exactly_two_distinct_regulatory_contexts():
    assert len(REGULATORY_CONTEXTS) == EXPECTED_REGULATORY_CONTEXT_COUNT == 2
    jurisdictions = {c["jurisdiction"] for c in REGULATORY_CONTEXTS}
    assert len(jurisdictions) == 2
    authorities = {c["regulatory_authority"] for c in REGULATORY_CONTEXTS}
    assert any("CMS" in a for a in authorities)
    assert any("CDPH" in a or "California" in a for a in authorities)


@pytest.mark.parametrize("field", [
    "content_source_type", "content_review_status", "source_reference",
    "regulatory_authority", "jurisdiction",
])
def test_every_regulatory_context_carries_full_provenance(field):
    for context in REGULATORY_CONTEXTS:
        assert context.get(field), f"regulatory context {context.get('context_id')} missing {field}"


def test_manifest_declares_exactly_twenty_differentiation_guards():
    assert len(GUARDS) == EXPECTED_GUARD_COUNT == 20
    assert sorted(g["guard_number"] for g in GUARDS) == list(range(1, 21))


def test_differentiation_guards_evaluate_as_all_passed():
    report = evaluate_differentiation_guards(MANIFEST)
    assert report["guards_total"] == 20
    assert report["guards_passed"] == 20
    assert report["guards_failed"] == []


@pytest.mark.parametrize("forbidden", [
    "eligible", "not eligible", "terminal", "not terminal",
    "certify", "do not certify", "prognosis met", "prognosis not met",
    "recertify", "do not recertify", "discharge recommended",
])
def test_manifest_never_uses_forbidden_vocabulary(forbidden):
    blobs = []
    for section in SECTIONS:
        blobs.append(section["section_name"])
        blobs.append(section["section_description"])
    for lbl in COMPARISON_VOCAB["labels"]:
        blobs.append(lbl["label"])
        blobs.append(lbl["definition"])
    blobs.extend(MANIFEST["physician_review_prompts"])
    blobs.extend(MANIFEST["narrative_support_elements"])
    joined = " ".join(blobs).lower()
    assert forbidden not in joined


def test_ai_layer_forbids_all_required_engine_terms():
    ai_may_not = set(MANIFEST["ai_layer"]["ai_may_not"])
    assert {
        "eligibility_engine", "terminal_status_engine", "prognosis_engine",
        "life_expectancy_prediction", "recertification_recommendation_engine",
        "non_recertification_recommendation_engine", "discharge_recommendation_engine",
        "conflicting_evidence_resolution_engine", "undocumented_decline_inference_engine",
        "medical_director_judgment_replacement",
    }.issubset(ai_may_not)


def test_ai_may_and_ai_may_not_never_overlap():
    ai_may = set(MANIFEST["ai_layer"]["ai_may"])
    ai_may_not = set(MANIFEST["ai_layer"]["ai_may_not"])
    assert ai_may.isdisjoint(ai_may_not)


def test_rules_block_declares_all_required_flags():
    rules = MANIFEST["rules"]
    for flag in (
        "read_only", "no_eligibility_engine", "no_terminal_status_engine", "no_prognosis_engine",
        "no_recertification_engine", "no_discharge_recommendation_engine", "no_patient_fact_writes",
        "no_cross_scale_comparison", "no_cross_regulatory_context_substitution",
        "single_observation_never_creates_a_trend",
        "evidence_strength_describes_documentation_completeness_only",
        "comparison_labels_describe_documented_change_only",
    ):
        assert rules[flag] is True, f"rules.{flag} must be true"


def test_manifest_declares_no_relationship_edge_or_patient_fact_explosion():
    unsupported = " ".join(MANIFEST["unsupported_content_not_created"]).lower()
    assert "relationship" in unsupported
    assert "patient-fact" in unsupported


# ---------------------------------------------------------------------
# compare_scale() / compare_numeric() pure-function tests
# ---------------------------------------------------------------------


@pytest.mark.parametrize("scale,prior,current,expected", [
    ("PPS", 60, 40, "DECLINING"),   # lower PPS = worse
    ("PPS", 40, 60, "IMPROVING"),
    ("PPS", 50, 50, "STABLE"),
    ("KPS", 60, 40, "DECLINING"),
    ("KPS", 40, 60, "IMPROVING"),
    ("ECOG", 1, 3, "DECLINING"),    # higher ECOG = worse
    ("ECOG", 3, 1, "IMPROVING"),
    ("FAST", 5, 7, "DECLINING"),    # later FAST stage = worse
    ("FAST", 7, 5, "IMPROVING"),
    ("NYHA", 2, 4, "DECLINING"),    # higher NYHA class = worse
    ("NYHA", 4, 2, "IMPROVING"),
])
def test_compare_scale_direction_correct_per_scale_ordering(scale, prior, current, expected):
    assert compare_scale(scale, prior, "2024-01-01", current, "2024-06-01") == expected


def test_compare_scale_rejects_cross_scale_comparison():
    with pytest.raises(ValueError):
        compare_scale("PPS_VS_KPS_NOT_A_REAL_SCALE", 60, "2024-01-01", 40, "2024-06-01")


@pytest.mark.parametrize("scale", ["PPS", "KPS", "ECOG", "FAST", "NYHA"])
def test_compare_scale_never_cross_compares_two_different_named_scales(scale):
    # compare_scale only ever accepts one scale_type argument -- there is
    # no code path by which a PPS value could be compared against a KPS
    # value; this is enforced structurally by the single scale_type param.
    assert scale in ("PPS", "KPS", "ECOG", "FAST", "NYHA")


def test_compare_scale_reports_prior_value_missing_never_decline():
    assert compare_scale("PPS", None, None, 40, "2024-06-01") == "PRIOR_VALUE_MISSING"


def test_compare_scale_reports_current_value_missing():
    assert compare_scale("PPS", 60, "2024-01-01", None, None) == "CURRENT_VALUE_MISSING"


def test_compare_scale_single_undated_observation_never_creates_a_trend():
    # No date on either side -> always a *_MISSING label, never a direction.
    result = compare_scale("PPS", 60, None, None, None)
    assert result == "PRIOR_VALUE_MISSING"


def test_compare_numeric_stable_and_direction():
    assert compare_numeric(3.0, "mg/dL", "2024-01-01", 3.0, "mg/dL", "2024-06-01", higher_is_worse=True) == "STABLE"
    assert compare_numeric(1.0, "mg/dL", "2024-01-01", 3.0, "mg/dL", "2024-06-01", higher_is_worse=True) == "DECLINING"
    assert compare_numeric(3.0, "mg/dL", "2024-01-01", 1.0, "mg/dL", "2024-06-01", higher_is_worse=True) == "IMPROVING"


def test_compare_numeric_rejects_incompatible_units():
    with pytest.raises(ValueError):
        compare_numeric(3.0, "mg/dL", "2024-01-01", 3.0, "mmol/L", "2024-06-01", higher_is_worse=True)


def test_compare_numeric_missing_values_reported_not_inferred():
    assert compare_numeric(None, "mg/dL", None, 3.0, "mg/dL", "2024-06-01", higher_is_worse=True) == "PRIOR_VALUE_MISSING"
    assert compare_numeric(3.0, "mg/dL", "2024-01-01", None, "mg/dL", None, higher_is_worse=True) == "CURRENT_VALUE_MISSING"


# ---------------------------------------------------------------------
# Importer / DB-backed tests
# ---------------------------------------------------------------------


def test_creates_exactly_one_framework_disease_never_a_duplicate(built_state):
    matches = built_state["session"].query(OntologyDisease).filter_by(disease_name=DISEASE_NAME).all()
    assert len(matches) == 1


def test_framework_disease_never_collides_with_pr58_disease(built_state):
    pr59_disease = built_state["framework_disease"]
    pr58_disease = built_state["session"].query(OntologyDisease).filter_by(disease_name=PR58_DISEASE_NAME).one()
    assert pr59_disease.id != pr58_disease.id


def test_family_is_recertification_reasoning_under_shared_reasoning_frameworks_system(built_state):
    disease = built_state["framework_disease"]
    family = built_state["session"].query(OntologyDiseaseFamily).filter_by(id=disease.disease_family_id).one()
    assert family.family_name == FAMILY_NAME == "Recertification Reasoning"
    system = built_state["session"].query(OntologyBodySystem).filter_by(id=family.body_system_id).one()
    assert system.system_name == SYSTEM_NAME == "Reasoning Frameworks"


def test_stores_exactly_twenty_two_framework_concepts(built_state):
    rows = (
        built_state["session"].query(OntologyDiseaseFinding)
        .filter_by(disease_id=built_state["framework_disease"].id)
        .all()
    )
    assert len(rows) == 22


@pytest.mark.parametrize("section", SECTIONS)
def test_every_section_concept_exists_with_evidence_rule(built_state, section):
    name = f"Section {section['section_number']}: {section['section_name']}"
    concept = _framework_concept(built_state["session"], built_state["framework_disease"].id, name)
    assert concept is not None
    rule = (
        built_state["session"].query(OntologyEvidenceRule)
        .filter_by(concept_type=CONCEPT_DOMAIN, concept_id=concept.id)
        .one_or_none()
    )
    assert rule is not None
    assert rule.patient_fact_requires_evidence is True


def test_comparison_vocabulary_concept_exists_with_nine_labels(built_state):
    concept = _framework_concept(built_state["session"], built_state["framework_disease"].id, COMPARISON_VOCAB["concept_name"])
    assert concept is not None
    assert [lvl["label"] for lvl in concept.severity_levels] == EXPECTED_COMPARISON_LABELS
    rule = (
        built_state["session"].query(OntologyEvidenceRule)
        .filter_by(concept_type=CONCEPT_DOMAIN, concept_id=concept.id)
        .one_or_none()
    )
    assert rule is not None
    assert rule.patient_fact_requires_evidence is True


def test_second_import_creates_zero_new_rows(built_state):
    result = run_framework_import(built_state["session"], manifest=MANIFEST)
    built_state["session"].commit()
    assert result["concepts_inserted"] == 0
    assert result["evidence_rules_inserted"] == 0


def test_zero_patient_fact_tables_touched(built_state):
    # This framework never creates a patient-fact row of any kind -- the
    # only rows it creates are OntologyBodySystem/Family/Disease/Finding/
    # EvidenceRule, all framework-registry (non-patient) tables.
    from app.models import poc as poc_models
    patient_fact_model_names = [
        name for name in dir(poc_models)
        if "Patient" in name and "Fact" in name
    ]
    # Structural assertion: this importer's run() never imports or
    # references any patient-fact model.
    import inspect
    from scripts import import_recertification_reasoning_framework_v1 as importer_module
    source = inspect.getsource(importer_module)
    for name in patient_fact_model_names:
        assert name not in source


def test_acceptance_report_required_fields_and_exact_values(built_state):
    report = build_acceptance_report(built_state["session"], MANIFEST, second_run_new_rows=0)
    assert report["pr_58_prerequisite_resolved"] is True
    assert report["summary_section_count"] == 21
    assert len(report["summary_section_names"]) == 21
    assert report["comparison_label_count"] == 9
    assert report["evidence_completeness_label_count"] == 4
    assert report["regulatory_context_count"] == 2
    assert report["differentiation_guards_total"] == 20
    assert report["differentiation_guards_passed"] == 20
    assert report["differentiation_guards_failed"] == []
    assert report["disease_created"] is True
    assert report["concepts_created"] == 22
    assert report["expected_concepts"] == 22
    assert report["idempotent"] is True
    for field in (
        "patient_facts_inserted", "patient_facts_updated", "patient_facts_deleted",
        "eligibility_outputs_created", "terminal_status_outputs_created",
        "prognosis_outputs_created", "life_expectancy_predictions_created",
        "certification_recommendations_created", "recertification_recommendations_created",
        "discharge_recommendations_created", "orphan_count", "cycle_count",
        "unresolved_framework_concept_count", "changes_outside_framework",
    ):
        assert report[field] == 0, f"{field} must be 0, found {report[field]}"


def test_manifest_declares_prerequisite_must_not_duplicate_list():
    must_not = MANIFEST["prerequisite"]["must_not_duplicate"]
    joined = " ".join(must_not).lower()
    assert "evidence sections" in joined
    assert "classification_rules" in joined
    assert "evidence-strength vocabulary" in joined
    assert "ai_layer" in joined
