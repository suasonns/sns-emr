# tests/test_terminal_status_reasoning_framework_v1.py
"""
Terminal Status Reasoning Framework v1 -- Structural and Extension Tests
(PR #58).

Verifies:
  - The manifest is schema-valid and vocabulary-compliant (never uses
    eligibility/terminal-status/certification pass-fail language).
  - The importer creates exactly the Terminal Status Reasoning Framework
    registry disease (never a duplicate, never collides with any of the
    12 consumed diseases), 11 section-definition concepts + 1
    evidence-strength-vocabulary concept (12 total), each with an
    OntologyEvidenceRule carrying patient_fact_requires_evidence=True.
  - Re-running the importer is fully idempotent (zero new rows).
  - classify_concept() correctly routes concepts into the 11 sections per
    the manifest's declarative classification_rules.
  - The acceptance report mechanically proves Section 1-7 evidence
    coverage exists across all 12 target diseases already persisted by
    the 8 merged Clinical Evidence Blueprint PRs.
  - The framework never establishes diagnosis, prognosis, terminal status,
    or hospice eligibility, and the ai_layer vocabulary enforces that
    boundary.

This test file builds the full baseline (all 7 non-neurologic foundations,
the full Neurologic foundation pipeline, the Functional Assessment
Framework, and all 8 Clinical Evidence Blueprint extension manifests)
before importing this framework -- the most complete fixture in this
codebase, since this is the first PR that reads across every prior
disease-specific manifest instead of extending a single disease.
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
    CONCEPT_DOMAIN,
    DEFAULT_MANIFEST_PATH,
    DISEASE_NAME,
    FAMILY_NAME,
    SYSTEM_NAME,
    TARGET_DISEASES,
    classify_concept,
    load_manifest,
    validate_manifest,
    build_acceptance_report,
    run as run_framework_import,
)
from tests.conftest import TestSessionLocal

MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)
SECTIONS = MANIFEST["framework_sections"]
EVIDENCE_VOCAB = MANIFEST["evidence_strength_vocabulary"]
CLASSIFICATION_RULES = MANIFEST["classification_rules"]


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


@pytest.fixture(scope="module")
def built_state():
    """Build the full 12-disease baseline (all 7 non-neurologic foundations,
    the Neurologic foundation pipeline, FAF, and all 8 Clinical Evidence
    Blueprint extensions) exactly once per test file, then import this
    framework. Guards every foundation/CEB import behind an existence
    check so this file cooperates correctly inside the combined suite,
    where other test files may have already built some or all of this
    baseline against the same module-scoped database."""
    session = TestSessionLocal()
    try:
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
# Manifest structural validation
# ---------------------------------------------------------------------


def test_manifest_is_schema_valid():
    assert validate_manifest(MANIFEST) == []


def test_manifest_declares_eleven_sections():
    assert len(SECTIONS) == 11
    assert sorted(s["section_number"] for s in SECTIONS) == list(range(1, 12))


def test_manifest_declares_four_evidence_strength_levels():
    levels = [lvl["level"] for lvl in EVIDENCE_VOCAB["levels"]]
    assert levels == ["Strong", "Moderate", "Limited", "Missing"]


@pytest.mark.parametrize("forbidden", [
    "eligible", "not eligible", "terminal", "not terminal",
    "certify", "do not certify", "prognosis met", "prognosis not met",
])
def test_manifest_never_uses_forbidden_eligibility_vocabulary(forbidden):
    blobs = []
    for section in SECTIONS:
        blobs.append(section["section_name"])
        blobs.append(section["section_description"])
    for lvl in EVIDENCE_VOCAB["levels"]:
        blobs.append(lvl["level"])
        blobs.append(lvl["definition"])
    blobs.extend(MANIFEST["physician_review_prompts"])
    blobs.extend(MANIFEST["narrative_support_elements"])
    joined = " ".join(blobs).lower()
    assert forbidden not in joined


def test_ai_layer_forbids_diagnosis_eligibility_terminal_status_and_prognosis_engines():
    ai_may_not = set(MANIFEST["ai_layer"]["ai_may_not"])
    assert {
        "diagnosis_engine", "eligibility_engine", "terminal_status_engine", "prognosis_engine",
    }.issubset(ai_may_not)


def test_ai_layer_forbids_new_expanded_prohibitions():
    ai_may_not = set(MANIFEST["ai_layer"]["ai_may_not"])
    assert {
        "life_expectancy_prediction",
        "admission_recommendation_engine",
        "recertification_recommendation_engine",
        "pass_fail_eligibility_decision_engine",
        "physician_judgment_override",
        "physician_certification_replacement",
    }.issubset(ai_may_not)


def test_ai_may_and_ai_may_not_never_overlap():
    ai_may = set(MANIFEST["ai_layer"]["ai_may"])
    ai_may_not = set(MANIFEST["ai_layer"]["ai_may_not"])
    assert ai_may.isdisjoint(ai_may_not)


def test_rules_block_declares_read_only_no_engine_flags():
    rules = MANIFEST["rules"]
    assert rules["read_only"] is True
    assert rules["no_eligibility_engine"] is True
    assert rules["no_terminal_status_engine"] is True
    assert rules["no_prognosis_engine"] is True
    assert rules["no_recertification_engine"] is True
    assert rules["evidence_strength_describes_documentation_completeness_only"] is True


def test_manifest_declares_no_new_disease_variants_or_relationship_edges():
    assert "unsupported_content_not_created" in MANIFEST
    joined = " ".join(MANIFEST["unsupported_content_not_created"]).lower()
    assert "relationship" in joined


# ---------------------------------------------------------------------
# classify_concept() unit tests (pure function, no DB required)
# ---------------------------------------------------------------------


@pytest.mark.parametrize("domain,name,expected_section", [
    ("FUNCTIONAL_IMPACT", "ADL Dependence", 1),
    ("NUTRITIONAL_IMPACT", "Progressive Weight Loss", 2),
    ("SYMPTOM", "Disabling Dyspnea At Rest", 3),
    ("FINDING", "Hypoxemia", 3),
    ("LAB", "GFR", 3),
    ("DIAGNOSTIC_TEST", "Echocardiogram", 3),
    ("END_STAGE_FINDING", "FAST Stage 7 or Beyond", 4),
    ("COMPLICATION", "Aspiration Pneumonia", 5),
    ("PROGNOSTIC_INDICATOR", "Narrative Trend", 11),
    ("PROGNOSTIC_INDICATOR", "PPS Trend", 6),
    ("HOSPICE_ELIGIBILITY_SUPPORT", "PPS Less Than 70 Percent", 1),
    ("HOSPICE_ELIGIBILITY_SUPPORT", "Serum Albumin Less Than 2.5 g/dL", 2),
    ("HOSPICE_ELIGIBILITY_SUPPORT", "Concomitant HIV Disease", 7),
    ("HOSPICE_ELIGIBILITY_SUPPORT", "Increasing Hospitalizations", 6),
    ("HOSPICE_ELIGIBILITY_SUPPORT", "NYHA Class IV", 4),
])
def test_classify_concept_routes_known_examples(domain, name, expected_section):
    assert classify_concept(domain, name, CLASSIFICATION_RULES) == expected_section


def test_classify_concept_returns_none_for_unknown_domain():
    assert classify_concept("NOT_A_REAL_DOMAIN", "Anything", CLASSIFICATION_RULES) is None


# ---------------------------------------------------------------------
# Importer / DB-backed tests
# ---------------------------------------------------------------------


def test_creates_exactly_one_framework_disease_never_a_duplicate(built_state):
    matches = (
        built_state["session"].query(OntologyDisease).filter_by(disease_name=DISEASE_NAME).all()
    )
    assert len(matches) == 1


def test_framework_disease_never_collides_with_any_consumed_disease(built_state):
    framework_id = built_state["framework_disease"].id
    for disease_name in TARGET_DISEASES:
        disease = (
            built_state["session"].query(OntologyDisease).filter_by(disease_name=disease_name).one_or_none()
        )
        assert disease is not None, f"{disease_name} should already exist from its foundation/CEB import"
        assert disease.id != framework_id


def test_stores_exactly_twelve_framework_concepts(built_state):
    rows = (
        built_state["session"].query(OntologyDiseaseFinding)
        .filter_by(disease_id=built_state["framework_disease"].id)
        .all()
    )
    assert len(rows) == 12


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


def test_evidence_strength_vocabulary_concept_exists_with_four_levels(built_state):
    concept = _framework_concept(
        built_state["session"], built_state["framework_disease"].id, EVIDENCE_VOCAB["concept_name"]
    )
    assert concept is not None
    assert [lvl["level"] for lvl in concept.severity_levels] == ["Strong", "Moderate", "Limited", "Missing"]
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


def test_acceptance_report_shows_section_one_through_seven_coverage_for_all_twelve_diseases(built_state):
    report = build_acceptance_report(built_state["session"], MANIFEST, second_run_new_rows=0)
    assert report["disease_created"] is True
    assert report["concepts_created"] == 12
    assert report["idempotent"] is True
    assert set(report["section_coverage_by_disease"].keys()) == set(TARGET_DISEASES)
    # Every disease should have nonzero hits in at least one of sections 1-7
    # (some diseases may legitimately lack a given section; this is
    # informational-only coverage, never a validation failure).
    for disease_name, hits in report["section_coverage_by_disease"].items():
        assert sum(hits.values()) > 0, f"{disease_name} should have some classified evidence across sections 1-7"


def test_manifest_declares_no_schema_migration_api_or_disease_foundation_changes():
    unsupported = MANIFEST["unsupported_content_not_created"]
    assert any("relationship" in item.lower() for item in unsupported)
    assert any("score" in item.lower() or "eligibility" in item.lower() for item in unsupported)
