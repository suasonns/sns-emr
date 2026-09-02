# tests/test_functional_assessment_framework_v1.py
"""Targeted tests for the Functional Assessment Framework v1 import
(`import_functional_assessment_framework_v1.py`, PR #49).

Every assertion below is derived directly from the committed manifest file
(`backend/manifests/functional_assessment_framework_v1.json`), never from
clinical judgment, inference, or a "similar enough" substitute.

This manifest is fully self-contained: it creates its own new
"Functional Assessment" body system, "Functional Assessment Scales"
family, and "Functional Assessment Framework" disease container. It does
not depend on any other manifest having already been imported.

This PR creates:
    - 45 SEVERITY_CLASS Tier 4 variants (one per individual score level:
      ECOG 5, NYHA 4, FAST 16, KPS 10, PPS 10).
    - 5 FINDING Tier 5 concepts (one per scale: ECOG, NYHA, FAST, KPS, PPS),
      each carrying its full per-level structured knowledge (score,
      display_title, clinical_meaning, functional_summary,
      hospice_interpretation, ai_summary) in its severity_levels JSONB
      column, and visibility-rule/trend-policy metadata in its
      supporting_evidence_types JSONB column.
    - 45 APPLIES_TO applicability edges (one per score level, linking that
      level's variant to its scale's concept).
    - 5 OntologyEvidenceRule rows (one per scale concept), each with
      patient_fact_requires_evidence=True.

It does NOT make any schema change, migration, or API change, and it does
NOT touch the patient-facing `assessments` table.
"""
from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDiseaseFamily,
    OntologyDisease,
    OntologyDiseaseVariant,
    OntologyDiseaseFinding,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
)
from scripts.import_functional_assessment_framework_v1 import (
    ALLOWED_CONTENT_REVIEW_STATUSES,
    ALLOWED_CONTENT_SOURCE_TYPES,
    CONCEPT_DOMAIN,
    DEFAULT_MANIFEST_PATH,
    DISEASE_NAME,
    REQUIRED_LEVEL_FIELDS,
    SYSTEM_NAME,
    VARIANT_DIMENSION,
    load_manifest,
    validate_manifest,
    build_acceptance_report,
    run as run_manifest_import,
)
from tests.conftest import TestSessionLocal

MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)
FAMILY_NAME = MANIFEST["scope"]["family"]

SCALE_CODES = [s["scale_code"] for s in MANIFEST["assessment_scales"]]
CONCEPT_NAMES = {s["concept_name"] for s in MANIFEST["assessment_scales"]}
LEVELS_BY_SCALE = {s["scale_code"]: s["levels"] for s in MANIFEST["assessment_scales"]}
TOTAL_LEVELS = sum(len(v) for v in LEVELS_BY_SCALE.values())


@pytest.fixture(scope="module")
def built_state():
    """Import the Functional Assessment Framework manifest into a
    dedicated session against the test database, exactly once for this
    file (module-scoped -- ontology tables are not tenant-scoped and are
    never cleared between tests by the function-scoped db_session
    fixture)."""
    session = TestSessionLocal()
    try:
        counts = run_manifest_import(session, manifest=MANIFEST)
        session.commit()
        disease = session.query(OntologyDisease).filter_by(disease_name=DISEASE_NAME).one()
        yield {"disease": disease, "counts": counts, "session": session}
    finally:
        session.close()


def _variant(db_session, disease, name):
    return (
        db_session.query(OntologyDiseaseVariant)
        .filter_by(disease_id=disease.id, variant_dimension=VARIANT_DIMENSION, normalized_name=name.strip().lower())
        .one_or_none()
    )


def _concept(db_session, disease, name):
    return (
        db_session.query(OntologyDiseaseFinding)
        .filter_by(disease_id=disease.id)
        .filter(OntologyDiseaseFinding.finding_name == name)
        .one_or_none()
    )


def _applicability(db_session, concept_id, variant_id):
    return (
        db_session.query(OntologyConceptVariantApplicability)
        .filter_by(
            concept_type=CONCEPT_DOMAIN,
            concept_id=concept_id,
            variant_id=variant_id,
            applicability_type="APPLIES_TO",
        )
        .one_or_none()
    )


# ---------------------------------------------------------------------
# Manifest structural validation
# ---------------------------------------------------------------------


def test_manifest_is_schema_valid():
    assert validate_manifest(MANIFEST) == []


def test_manifest_declares_exactly_five_scales():
    assert SCALE_CODES == ["ECOG", "NYHA", "FAST", "KPS", "PPS"]


def test_manifest_declares_45_total_score_levels():
    assert TOTAL_LEVELS == 45


@pytest.mark.parametrize("scale_code,expected_count", [
    ("ECOG", 5), ("NYHA", 4), ("FAST", 16), ("KPS", 10), ("PPS", 10),
])
def test_each_scale_declares_expected_level_count(scale_code, expected_count):
    assert len(LEVELS_BY_SCALE[scale_code]) == expected_count


def test_every_level_declares_all_required_interpretation_fields():
    """DO NOT STORE NUMBERS ONLY -- every level must carry score, title,
    clinical meaning, functional summary, clinical examples, hospice
    interpretation, and an AI summary."""
    for scale_code, levels in LEVELS_BY_SCALE.items():
        for level in levels:
            for field in REQUIRED_LEVEL_FIELDS:
                assert level.get(field), f"{scale_code} {level.get('score')} missing {field}"


def test_every_level_declares_a_non_empty_clinical_examples_list():
    for scale_code, levels in LEVELS_BY_SCALE.items():
        for level in levels:
            examples = level["clinical_examples"]
            assert isinstance(examples, list)
            assert len(examples) > 0
            assert all(isinstance(item, str) and item for item in examples)


@pytest.mark.parametrize("scale_code,score,expected_examples", [
    ("PPS", "40", [
        "MAINLY IN BED",
        "Unable to perform most activities.",
        "Extensive assistance required.",
        "Reduced intake.",
        "Commonly associated with significant overall decline.",
        "Documentation review recommended.",
    ]),
    ("FAST", "7C", [
        "Unable to ambulate independently.",
        "Advanced dementia stage.",
        "Requires assistance with mobility.",
        "Documentation review recommended.",
    ]),
    ("NYHA", "IV", [
        "Symptoms at rest.",
        "Unable to perform physical activity without discomfort.",
        "Advanced CHF functional impairment.",
        "Documentation review recommended.",
    ]),
    ("ECOG", "3", [
        "Limited self-care.",
        "Confined to bed/chair more than half of waking hours.",
        "Significant functional decline.",
        "Documentation review recommended.",
    ]),
])
def test_nurse_ux_dictated_clinical_examples_match_verbatim(scale_code, score, expected_examples):
    """These four score levels' clinical_examples were dictated verbatim
    by the correction spec's "NURSE UX REQUIREMENT" section -- the nurse
    must see exactly this content, unaltered."""
    level = next(lvl for lvl in LEVELS_BY_SCALE[scale_code] if lvl["score"] == score)
    assert level["clinical_examples"] == expected_examples


# ---------------------------------------------------------------------
# ALL_CLINICAL_CONTENT_HAS_PROVENANCE
# ---------------------------------------------------------------------
#
# Content is never removed or replaced with a placeholder -- every score
# level remains fully human-readable and nurse-usable at the point of
# care. Instead, every level is tagged with where its content came from
# and whether it has been formally reviewed, so a nurse, physician, or
# medical director can see both the clinical content AND its review
# status in the same place.

USER_DICTATED_LEVELS = {("PPS", "40"), ("FAST", "7C"), ("NYHA", "IV"), ("ECOG", "3")}


def test_every_level_declares_content_source_type_and_review_status():
    """ALL_CLINICAL_CONTENT_HAS_PROVENANCE: every score level must carry
    both content_source_type and content_review_status, in addition to
    (never instead of) its full clinical content."""
    for scale_code, levels in LEVELS_BY_SCALE.items():
        for level in levels:
            assert level.get("content_source_type") in ALLOWED_CONTENT_SOURCE_TYPES, (
                f"{scale_code} {level.get('score')} missing/invalid content_source_type"
            )
            assert level.get("content_review_status") in ALLOWED_CONTENT_REVIEW_STATUSES, (
                f"{scale_code} {level.get('score')} missing/invalid content_review_status"
            )


@pytest.mark.parametrize("scale_code,score", [
    (s["scale_code"], lvl["score"]) for s in MANIFEST["assessment_scales"] for lvl in s["levels"]
])
def test_user_dictated_levels_are_tagged_user_dictated(scale_code, score):
    level = next(lvl for lvl in LEVELS_BY_SCALE[scale_code] if lvl["score"] == score)
    expected = "USER_DICTATED" if (scale_code, score) in USER_DICTATED_LEVELS else "CLINICAL_SCALE_REFERENCE"
    assert level["content_source_type"] == expected


def test_no_score_level_is_number_only_or_unreadable():
    """FAIL if any score becomes number-only -- every level must retain
    real clinical_meaning, functional_summary, hospice_interpretation,
    ai_summary, and a non-empty clinical_examples list, regardless of
    its content_source_type or content_review_status."""
    placeholder = "SOURCE_NOT_YET_DEFINED"
    for scale_code, levels in LEVELS_BY_SCALE.items():
        for level in levels:
            for field in ("clinical_meaning", "functional_summary", "hospice_interpretation", "ai_summary"):
                value = level.get(field)
                assert value and value != placeholder, (
                    f"{scale_code} {level.get('score')}.{field} is not nurse-readable"
                )
            examples = level.get("clinical_examples")
            assert isinstance(examples, list) and len(examples) > 0
            assert all(item != placeholder for item in examples), (
                f"{scale_code} {level.get('score')} clinical_examples contains a placeholder"
            )


def test_no_duplicate_score_identity_within_manifest():
    seen = set()
    for scale in MANIFEST["assessment_scales"]:
        for level in scale["levels"]:
            key = (scale["scale_code"], level["score"])
            assert key not in seen, f"duplicate score identity {key}"
            seen.add(key)


# ---------------------------------------------------------------------
# Structure creation (body system / family / disease)
# ---------------------------------------------------------------------


def test_body_system_created(built_state):
    db_session = built_state["session"]
    system = db_session.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one_or_none()
    assert system is not None


def test_family_created_under_body_system(built_state):
    db_session = built_state["session"]
    system = db_session.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one()
    family = (
        db_session.query(OntologyDiseaseFamily)
        .filter_by(family_name=FAMILY_NAME, body_system_id=system.id)
        .one_or_none()
    )
    assert family is not None


def test_disease_container_created_exactly_once(built_state):
    db_session = built_state["session"]
    rows = db_session.query(OntologyDisease).filter_by(disease_name=DISEASE_NAME).all()
    assert len(rows) == 1


# ---------------------------------------------------------------------
# Variants (score levels) -- store separately, never numbers-only
# ---------------------------------------------------------------------


def test_stored_variant_count_matches_manifest_exactly(built_state):
    db_session = built_state["session"]
    disease = built_state["disease"]
    stored = (
        db_session.query(OntologyDiseaseVariant)
        .filter_by(disease_id=disease.id, variant_dimension=VARIANT_DIMENSION)
        .count()
    )
    assert stored == TOTAL_LEVELS == 45


@pytest.mark.parametrize("scale_code,score", [
    (s["scale_code"], lvl["score"]) for s in MANIFEST["assessment_scales"] for lvl in s["levels"]
])
def test_every_declared_score_level_variant_exists(built_state, scale_code, score):
    db_session = built_state["session"]
    disease = built_state["disease"]
    variant = _variant(db_session, disease, f"{scale_code} {score}")
    assert variant is not None
    assert variant.variant_code == score


def test_every_variant_carries_full_interpretation_not_number_only(built_state):
    """Each variant's existing free-text columns must carry clinical
    meaning / functional summary / hospice interpretation -- never a bare
    score."""
    db_session = built_state["session"]
    disease = built_state["disease"]
    variants = (
        db_session.query(OntologyDiseaseVariant)
        .filter_by(disease_id=disease.id, variant_dimension=VARIANT_DIMENSION)
        .all()
    )
    assert len(variants) == 45
    for v in variants:
        assert v.description, f"{v.variant_name} missing clinical_meaning"
        assert v.clinical_significance, f"{v.variant_name} missing functional_summary"
        assert v.hospice_relevance, f"{v.variant_name} missing hospice_interpretation"
        assert v.evidence_requirement, f"{v.variant_name} missing evidence_requirement"


def test_no_score_level_collapsed_within_or_across_scales(built_state):
    """ECOG 0 and PPS 100, despite similar clinical meaning, must remain
    distinct rows -- no cross-scale collapsing."""
    db_session = built_state["session"]
    disease = built_state["disease"]
    all_names = [f"{s} {lvl['score']}" for s, lvls in LEVELS_BY_SCALE.items() for lvl in lvls]
    ids = set()
    for name in all_names:
        v = _variant(db_session, disease, name)
        assert v is not None
        ids.add(v.id)
    assert len(ids) == len(all_names) == 45


# ---------------------------------------------------------------------
# Concepts (scales) -- store separately
# ---------------------------------------------------------------------


def test_stored_concept_count_matches_manifest_exactly(built_state):
    db_session = built_state["session"]
    disease = built_state["disease"]
    stored = db_session.query(OntologyDiseaseFinding).filter_by(disease_id=disease.id).count()
    assert stored == 5


@pytest.mark.parametrize("concept_name", sorted(CONCEPT_NAMES))
def test_every_declared_scale_concept_exists(built_state, concept_name):
    db_session = built_state["session"]
    disease = built_state["disease"]
    concept = _concept(db_session, disease, concept_name)
    assert concept is not None


def test_five_scale_concepts_remain_distinct(built_state):
    db_session = built_state["session"]
    disease = built_state["disease"]
    ids = {_concept(db_session, disease, name).id for name in CONCEPT_NAMES}
    assert len(ids) == 5


@pytest.mark.parametrize("scale", MANIFEST["assessment_scales"])
def test_concept_severity_levels_jsonb_matches_manifest_levels(built_state, scale):
    """The concept's severity_levels JSONB column must carry the FULL
    per-level structured record -- this is the mechanism that satisfies
    "must not store scores only" without any schema change."""
    db_session = built_state["session"]
    disease = built_state["disease"]
    concept = _concept(db_session, disease, scale["concept_name"])
    assert concept is not None
    stored_levels = concept.severity_levels
    assert isinstance(stored_levels, list)
    assert len(stored_levels) == len(scale["levels"])
    stored_by_score = {lvl["score"]: lvl for lvl in stored_levels}
    for expected_level in scale["levels"]:
        stored_level = stored_by_score.get(expected_level["score"])
        assert stored_level is not None
        for field in REQUIRED_LEVEL_FIELDS:
            assert stored_level[field] == expected_level[field]
        assert stored_level["patient_fact_requires_evidence"] is True


@pytest.mark.parametrize("scale", MANIFEST["assessment_scales"])
def test_concept_supporting_evidence_types_carries_visibility_rule(built_state, scale):
    db_session = built_state["session"]
    disease = built_state["disease"]
    concept = _concept(db_session, disease, scale["concept_name"])
    assert concept is not None
    payload = concept.supporting_evidence_types
    assert isinstance(payload, dict)
    assert payload["visibility_rule"] == scale["visibility_rule"]
    assert payload["source_classification"] == scale["source_classification"]
    assert payload["source_reference"] == scale["source_reference"]


# ---------------------------------------------------------------------
# Applicability (score level -> scale) -- no Cartesian generation
# ---------------------------------------------------------------------


def test_stored_applicability_count_matches_manifest_exactly(built_state):
    db_session = built_state["session"]
    disease = built_state["disease"]
    stored = db_session.query(OntologyConceptVariantApplicability).filter_by(disease_id=disease.id).count()
    assert stored == 45


@pytest.mark.parametrize("scale_code,score,concept_name", [
    (s["scale_code"], lvl["score"], s["concept_name"])
    for s in MANIFEST["assessment_scales"] for lvl in s["levels"]
])
def test_every_score_level_applies_to_its_own_scale_only(built_state, scale_code, score, concept_name):
    db_session = built_state["session"]
    disease = built_state["disease"]
    variant = _variant(db_session, disease, f"{scale_code} {score}")
    concept = _concept(db_session, disease, concept_name)
    edge = _applicability(db_session, concept.id, variant.id)
    assert edge is not None
    assert edge.applicability_type == "APPLIES_TO"


def test_no_cartesian_applicability_generation(built_state):
    """Exactly 45 applicability edges must exist -- one per score level --
    never the 45 x 5 = 225 Cartesian pool of every level against every
    scale concept."""
    db_session = built_state["session"]
    disease = built_state["disease"]
    edges = db_session.query(OntologyConceptVariantApplicability).filter_by(disease_id=disease.id).all()
    assert len(edges) == 45
    pairs = {(e.concept_id, e.variant_id) for e in edges}
    assert len(pairs) == 45


def test_a_score_level_never_applies_to_a_different_scale(built_state):
    """ECOG 0's variant must never carry an applicability edge to the
    NYHA concept (or any other scale's concept)."""
    db_session = built_state["session"]
    disease = built_state["disease"]
    ecog_variant = _variant(db_session, disease, "ECOG 0")
    nyha_concept = _concept(db_session, disease, "NYHA - New York Heart Association Functional Classification")
    assert _applicability(db_session, nyha_concept.id, ecog_variant.id) is None


# ---------------------------------------------------------------------
# Evidence rules
# ---------------------------------------------------------------------


def test_every_scale_concept_has_evidence_rule_requiring_evidence(built_state):
    db_session = built_state["session"]
    disease = built_state["disease"]
    for name in CONCEPT_NAMES:
        concept = _concept(db_session, disease, name)
        rule = (
            db_session.query(OntologyEvidenceRule)
            .filter_by(concept_type=CONCEPT_DOMAIN, concept_id=concept.id)
            .one_or_none()
        )
        assert rule is not None
        assert rule.patient_fact_requires_evidence is True


def test_evidence_rule_count_matches_manifest_exactly(built_state):
    db_session = built_state["session"]
    disease = built_state["disease"]
    concepts = db_session.query(OntologyDiseaseFinding).filter_by(disease_id=disease.id).all()
    concept_ids = {c.id for c in concepts}
    rules = (
        db_session.query(OntologyEvidenceRule)
        .filter(OntologyEvidenceRule.concept_type == CONCEPT_DOMAIN)
        .filter(OntologyEvidenceRule.concept_id.in_(concept_ids))
        .all()
    )
    assert len(rules) == 5


# ---------------------------------------------------------------------
# Non-eligibility / non-diagnostic invariants
# ---------------------------------------------------------------------


def test_no_assessment_establishes_diagnosis_prognosis_or_eligibility(built_state):
    """This manifest must never create a HOSPICE_ELIGIBILITY_SUPPORT /
    END_STAGE_FINDING row or a HOSPICE_SUPPORT_FOR / PROGNOSTIC_FOR /
    END_STAGE_SUPPORT_FOR applicability edge -- no score independently
    establishes diagnosis, prognosis, hospice eligibility, or terminal
    status."""
    db_session = built_state["session"]
    disease = built_state["disease"]
    forbidden_types = {"HOSPICE_SUPPORT_FOR", "PROGNOSTIC_FOR", "END_STAGE_SUPPORT_FOR"}
    count = (
        db_session.query(OntologyConceptVariantApplicability)
        .filter_by(disease_id=disease.id)
        .filter(OntologyConceptVariantApplicability.applicability_type.in_(forbidden_types))
        .count()
    )
    assert count == 0


# ---------------------------------------------------------------------
# Idempotency and orphan/cycle/unresolved integrity
# ---------------------------------------------------------------------


def test_second_import_creates_zero_new_rows():
    session = TestSessionLocal()
    try:
        run_manifest_import(session, manifest=MANIFEST)
        session.commit()
        result2 = run_manifest_import(session, manifest=MANIFEST)
        session.commit()
        total_new = (
            result2["variants_inserted"]
            + result2["concepts_inserted_total"]
            + result2["applicability_inserted"]
        )
        assert total_new == 0
        assert result2["evidence_rules_inserted"] == 0
    finally:
        session.close()


def test_acceptance_report_shows_zero_orphans_cycles_and_unresolved(built_state):
    db_session = built_state["session"]
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert report["orphan_count"] == 0
    assert report["cycle_count"] == 0
    assert report["unresolved_concept_count"] == 0
    assert report["missing_variants"] == []
    assert report["missing_concepts"] == []
    assert report["missing_applicability"] == []


def test_acceptance_report_all_differentiation_guards_pass(built_state):
    db_session = built_state["session"]
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    failed = [g for g in report["differentiation_guard_results"] if not g["passed"]]
    assert failed == [], f"failed guards: {failed}"


def test_acceptance_report_every_level_has_full_interpretation(built_state):
    db_session = built_state["session"]
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert report["every_score_level_has_full_interpretation_not_number_only"] is True


# ---------------------------------------------------------------------
# Unsupported-content guard: no schema/migration/API/patient-record change
# ---------------------------------------------------------------------


def test_manifest_declares_no_schema_migration_api_or_patient_record_changes():
    unsupported = MANIFEST["unsupported_content_not_created"]
    assert "no new tables/columns" in unsupported["SCHEMA_CHANGES"]
    assert unsupported["MIGRATIONS"] == "none"
    assert unsupported["API_CHANGES"] == "none"
    assert "assessments" in unsupported["PATIENT_RECORD_MODIFICATIONS"]
