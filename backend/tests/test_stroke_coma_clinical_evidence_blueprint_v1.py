# tests/test_stroke_coma_clinical_evidence_blueprint_v1.py
"""Targeted tests for the Stroke/Coma Clinical Evidence Blueprint v1 import
(`import_stroke_coma_clinical_evidence_blueprint_v1.py`, PR #57).

Every assertion below is derived directly from the committed manifest file
(`backend/manifests/stroke_coma_clinical_evidence_blueprint_v1.json`), never
from clinical judgment, inference, or a "similar enough" substitute.

This manifest is EXTENSION-ONLY. It depends on two already-merged
manifests being importable first:

    - Neurologic Production Source Manifest v1 (PR #37), which creates the
      "Stroke" disease this PR extends. Coma is NOT a separate disease --
      it already exists inside Stroke as END_STAGE_FINDING concepts
      ("Coma", "Persistent Coma", "Persistent Vegetative State",
      "Minimally Conscious State") and as the SEVERITY_CLASS variant
      "Stroke With Persistent Coma".
    - Functional Assessment Framework v1 (PR #49), which creates the
      "Functional Assessment Framework" disease this PR links to.

This PR creates:
    - 3 new atomic Stroke concepts, all in the HOSPICE_ELIGIBILITY_SUPPORT
      domain (ADL Dependence, Progressive Functional Decline, Progressive
      Nutritional Decline) -- the universal non-disease-specific support
      concepts every other disease foundation already carries but PR #37's
      Stroke foundation never received.
    - 3 new applicability edges linking those new concepts to PR #37's
      existing "Stroke With Persistent Coma" variant.
    - 2 OntologyRelationship edges linking PR #37's existing Palliative
      Performance Scale 40 Percent or Less / Karnofsky Performance Status
      40 Percent or Less concepts to PR #49's existing PPS / KPS
      scale-definition concepts.
    - 7 Stroke recertification-trend PROGNOSTIC_INDICATOR concepts.
    - Provenance metadata (content_source_type, content_review_status)
      for every one of the above, encoded into the existing
      OntologyEvidenceRule.notes / OntologyRelationship.description
      free-text fields.

It does NOT create a new OntologyBodySystem, OntologyDiseaseFamily, or
OntologyDisease row. It does NOT create a new OntologyDiseaseVariant row.
It does NOT duplicate any PPS/KPS/ADL definition, and it does NOT
duplicate any of Stroke's existing coma-related END_STAGE_FINDING
concepts or existing HOSPICE_ELIGIBILITY_SUPPORT concepts. It does NOT
make any schema, migration, or API change.
"""
from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyDiseaseVariant,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseasePrognosticIndicator,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
    OntologyRelationship,
)
from app.models.ontology_disease_blueprint import OntologyBodySystem, OntologyDiseaseFamily
from scripts.complete_ontology_neurologic_clinical_reasoning import (
    run as run_clinical_reasoning_script,
)
from scripts.complete_ontology_phase2_neurologic_coverage import run as run_coverage_repair_script
from scripts.expand_ontology_phase2_neurologic import (
    run as run_phase2_script,
    EXISTING_DISEASE_NAMES,
    SYSTEM_NAME,
)
from scripts.import_neurologic_production_source_manifest import (
    run as run_neuro_foundation_import,
    load_manifest as load_neuro_foundation_manifest,
)
from scripts.import_functional_assessment_framework_v1 import (
    run as run_faf_import,
    load_manifest as load_faf_manifest,
)
from scripts.import_stroke_coma_clinical_evidence_blueprint_v1 import (
    ALLOWED_CONTENT_REVIEW_STATUSES,
    ALLOWED_CONTENT_SOURCE_TYPES,
    CONCEPT_DOMAIN_MODEL_MAP,
    DEFAULT_MANIFEST_PATH,
    EXTENDS_DISEASE_NAME,
    FAF_DISEASE_NAME,
    FAF_LINKAGE_TARGET_DOMAIN,
    PROVENANCE_PATTERN,
    RELATIONSHIP_TYPE,
    load_manifest,
    validate_manifest,
    build_acceptance_report,
    run as run_stroke_ceb_import,
)
from tests.conftest import TestSessionLocal

MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)
NEW_CONCEPTS = MANIFEST["new_concepts"]
NEW_APPLICABILITY = MANIFEST["new_applicability"]
FAF_LINKAGE = MANIFEST["functional_assessment_linkage"]
TREND_INDICATORS = MANIFEST["recertification_evidence_model"]["trend_indicators"]


def _seed_base_diseases(db_session) -> None:
    """Bring the Neurologic System's 6 base diseases (including Stroke)
    into existence -- mirrors test_neurologic_production_source_manifest.py's
    own fixture exactly, since this Clinical Evidence Blueprint depends on
    the full Neurologic foundation build pipeline having already run."""
    system = db_session.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one_or_none()
    if system is None:
        system = OntologyBodySystem(system_name=SYSTEM_NAME)
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
    """Bring the Neurologic System to the merged baseline (Phase 2 +
    coverage repair + clinical-reasoning build + Production Source
    Manifest v1), import the Functional Assessment Framework, then import
    the Stroke/Coma Clinical Evidence Blueprint extension manifest exactly
    once for this file (module-scoped -- ontology tables are not
    tenant-scoped and are never cleared between tests by the
    function-scoped db_session fixture).

    The underlying Phase 2 / coverage-repair / clinical-reasoning seed
    scripts (unlike every manifest importer in this codebase) are NOT
    safe to re-run against a database that already has their rows --
    they predate the idempotent-importer convention. When this test file
    runs in a combined suite alongside test_neurologic_production_source_
    manifest.py (which already builds that same baseline), skip straight
    to importing this manifest against the already-built foundation
    instead of re-running the whole pipeline a second time."""
    session = TestSessionLocal()
    try:
        existing_stroke = session.query(OntologyDisease).filter_by(disease_name=EXTENDS_DISEASE_NAME).one_or_none()
        if existing_stroke is None:
            _seed_base_diseases(session)
            session.commit()
            run_phase2_script(session)
            session.commit()
            run_coverage_repair_script(session)
            session.commit()
            run_clinical_reasoning_script(session)
            session.commit()
            run_neuro_foundation_import(session, manifest=load_neuro_foundation_manifest())
            session.commit()

        existing_faf = session.query(OntologyDisease).filter_by(disease_name=FAF_DISEASE_NAME).one_or_none()
        if existing_faf is None:
            run_faf_import(session, manifest=load_faf_manifest())
            session.commit()

        counts = run_stroke_ceb_import(session, manifest=MANIFEST)
        session.commit()

        stroke_disease = session.query(OntologyDisease).filter_by(disease_name=EXTENDS_DISEASE_NAME).one()
        faf_disease = session.query(OntologyDisease).filter_by(disease_name=FAF_DISEASE_NAME).one()
        yield {"stroke_disease": stroke_disease, "faf_disease": faf_disease, "counts": counts, "session": session}
    finally:
        session.close()


def _concept(db_session, disease_id, domain, name):
    model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[domain]
    return (
        db_session.query(model_cls)
        .filter_by(disease_id=disease_id)
        .filter(getattr(model_cls, name_attr).ilike(name.strip()))
        .one_or_none()
    )


def _variant(db_session, disease_id, name):
    return (
        db_session.query(OntologyDiseaseVariant)
        .filter_by(disease_id=disease_id, normalized_name=name.strip().lower())
        .one_or_none()
    )


def _evidence_rule(db_session, concept_type, concept_id):
    return (
        db_session.query(OntologyEvidenceRule)
        .filter_by(concept_type=concept_type, concept_id=concept_id)
        .one_or_none()
    )


# ---------------------------------------------------------------------
# Manifest structural validation
# ---------------------------------------------------------------------


def test_manifest_is_schema_valid():
    assert validate_manifest(MANIFEST) == []


def test_manifest_declares_extension_only_rules():
    rules = MANIFEST["rules"]
    assert rules["extension_only"] is True
    assert rules["no_new_disease"] is True
    assert rules["no_new_variants"] is True
    assert rules["no_new_pps_kps_definitions"] is True
    assert rules["no_duplicate_assessment_definitions"] is True


def test_manifest_declares_three_new_concepts():
    assert len(NEW_CONCEPTS) == 3


def test_manifest_declares_three_new_applicability_edges():
    assert len(NEW_APPLICABILITY) == 3


def test_manifest_declares_two_functional_assessment_linkages():
    assert len(FAF_LINKAGE) == 2


def test_manifest_declares_seven_recertification_trend_indicators():
    assert len(TREND_INDICATORS) == 7


def test_no_duplicate_concept_identity_within_manifest():
    keys = [(c["domain"], c["name"].strip().lower()) for c in NEW_CONCEPTS]
    assert len(keys) == len(set(keys))


def test_no_duplicate_trend_indicator_identity_within_manifest():
    names = [t["name"].strip().lower() for t in TREND_INDICATORS]
    assert len(names) == len(set(names))


def test_every_new_concept_is_in_hospice_eligibility_support_domain():
    """This manifest adds only the universal non-disease-specific support
    concepts -- it never adds a new SYMPTOM/FINDING/COMPLICATION concept,
    since Stroke's foundation already has an exceptionally rich set of
    those."""
    assert {c["domain"] for c in NEW_CONCEPTS} == {"HOSPICE_ELIGIBILITY_SUPPORT"}


def test_already_present_verified_mapping_covers_requested_items():
    mapping = MANIFEST["already_present_verified"]["mapping"]
    requested = {m["requested"] for m in mapping}
    expected = {
        "Coma", "Persistent Coma", "Persistent Vegetative State", "Minimally Conscious State",
        "Aspiration Pneumonia", "Sepsis", "Pyelonephritis", "Refractory Stage 3 or 4 Pressure Injury",
        "Stroke With Persistent Coma", "Karnofsky Performance Status 40 Percent or Less",
        "Palliative Performance Scale 40 Percent or Less",
    }
    assert requested == expected


# ---------------------------------------------------------------------
# ALL_CLINICAL_CONTENT_HAS_PROVENANCE
# ---------------------------------------------------------------------


@pytest.mark.parametrize("entry", NEW_CONCEPTS, ids=[c["name"] for c in NEW_CONCEPTS])
def test_every_new_concept_has_valid_provenance(entry):
    assert entry["content_source_type"] in ALLOWED_CONTENT_SOURCE_TYPES
    assert entry["content_review_status"] in ALLOWED_CONTENT_REVIEW_STATUSES


@pytest.mark.parametrize("entry", TREND_INDICATORS, ids=[t["name"] for t in TREND_INDICATORS])
def test_every_trend_indicator_has_valid_provenance(entry):
    assert entry["content_source_type"] in ALLOWED_CONTENT_SOURCE_TYPES
    assert entry["content_review_status"] in ALLOWED_CONTENT_REVIEW_STATUSES


@pytest.mark.parametrize("entry", FAF_LINKAGE, ids=[l["relationship_type"] + "/" + l["chf_concept_name"] for l in FAF_LINKAGE])
def test_every_faf_linkage_has_valid_provenance(entry):
    assert entry["content_source_type"] in ALLOWED_CONTENT_SOURCE_TYPES
    assert entry["content_review_status"] in ALLOWED_CONTENT_REVIEW_STATUSES


@pytest.mark.parametrize("entry", NEW_CONCEPTS, ids=[c["name"] for c in NEW_CONCEPTS])
def test_every_new_concept_is_nurse_readable_not_numeric_only(entry):
    assert not entry["name"].strip().isdigit()
    assert len(entry["description"].strip()) > 0


@pytest.mark.parametrize("entry", TREND_INDICATORS, ids=[t["name"] for t in TREND_INDICATORS])
def test_every_trend_indicator_is_nurse_readable_not_numeric_only(entry):
    assert not entry["name"].strip().isdigit()
    assert len(entry["description"].strip()) > 0


# ---------------------------------------------------------------------
# Extension-only guarantees (no new disease/variant/duplicate definition)
# ---------------------------------------------------------------------


def test_extends_existing_stroke_disease_never_creates_a_new_one(built_state):
    session = built_state["session"]
    matches = session.query(OntologyDisease).filter_by(disease_name=EXTENDS_DISEASE_NAME).all()
    assert len(matches) == 1


def test_extends_existing_faf_disease_never_creates_a_new_one(built_state):
    session = built_state["session"]
    matches = session.query(OntologyDisease).filter_by(disease_name=FAF_DISEASE_NAME).all()
    assert len(matches) == 1


def test_import_aborts_if_stroke_disease_is_missing():
    """Exercises _resolve_disease's RuntimeError contract directly with a
    disease name that will never exist in any test database, proving the
    importer aborts before any writes rather than silently creating a
    second Stroke/Coma foundation."""
    from scripts.import_stroke_coma_clinical_evidence_blueprint_v1 import _resolve_disease
    session = TestSessionLocal()
    try:
        with pytest.raises(RuntimeError):
            _resolve_disease(session, "__nonexistent_disease__")
    finally:
        session.close()


def test_no_new_disease_variant_created_by_this_manifest(built_state):
    """The manifest declares zero variants of its own -- it only
    references PR #37's existing 'Stroke With Persistent Coma' variant by
    name."""
    assert "variants" not in MANIFEST


def test_no_new_coma_disease_or_variant_created(built_state):
    """Coma must never become a second disease foundation -- confirms it
    remains folded into Stroke as an END_STAGE_FINDING concept / variant."""
    session = built_state["session"]
    coma_diseases = session.query(OntologyDisease).filter(
        OntologyDisease.disease_name.ilike("%coma%")
    ).all()
    assert coma_diseases == []


# ---------------------------------------------------------------------
# New atomic concepts
# ---------------------------------------------------------------------


@pytest.mark.parametrize("entry", NEW_CONCEPTS, ids=[c["name"] for c in NEW_CONCEPTS])
def test_every_declared_new_concept_exists(built_state, entry):
    row = _concept(built_state["session"], built_state["stroke_disease"].id, entry["domain"], entry["name"])
    assert row is not None


@pytest.mark.parametrize("entry", NEW_CONCEPTS, ids=[c["name"] for c in NEW_CONCEPTS])
def test_every_new_concept_has_evidence_rule_with_provenance(built_state, entry):
    row = _concept(built_state["session"], built_state["stroke_disease"].id, entry["domain"], entry["name"])
    rule = _evidence_rule(built_state["session"], entry["domain"], row.id)
    assert rule is not None
    assert rule.patient_fact_requires_evidence is True
    match = PROVENANCE_PATTERN.search(rule.notes or "")
    assert match is not None
    assert match.group("cst") == entry["content_source_type"]
    assert match.group("crs") == entry["content_review_status"]


def test_stored_new_concept_count_matches_manifest_exactly(built_state):
    session = built_state["session"]
    stroke_id = built_state["stroke_disease"].id
    total = 0
    for entry in NEW_CONCEPTS:
        row = _concept(session, stroke_id, entry["domain"], entry["name"])
        assert row is not None
        total += 1
    assert total == len(NEW_CONCEPTS)


def test_new_hospice_eligibility_support_concepts_stored(built_state):
    session = built_state["session"]
    stroke_id = built_state["stroke_disease"].id
    names = {c["name"].strip().lower() for c in NEW_CONCEPTS if c["domain"] == "HOSPICE_ELIGIBILITY_SUPPORT"}
    stored = {
        row.indicator_name.strip().lower()
        for row in session.query(OntologyDiseaseHospiceEligibilitySupport).filter_by(disease_id=stroke_id).all()
    }
    assert names.issubset(stored)


# ---------------------------------------------------------------------
# New applicability edges
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "entry",
    NEW_APPLICABILITY,
    ids=[f"{a['variant']}/{a['concept']}" for a in NEW_APPLICABILITY],
)
def test_every_declared_applicability_edge_exists(built_state, entry):
    session = built_state["session"]
    stroke_id = built_state["stroke_disease"].id
    variant = _variant(session, stroke_id, entry["variant"])
    concept = _concept(session, stroke_id, entry["concept_domain"], entry["concept"])
    assert variant is not None
    assert concept is not None
    edge = (
        session.query(OntologyConceptVariantApplicability)
        .filter_by(
            concept_type=entry["concept_domain"],
            concept_id=concept.id,
            variant_id=variant.id,
            applicability_type=entry["applicability_type"],
        )
        .one_or_none()
    )
    assert edge is not None


def test_every_new_applicability_edge_targets_stroke_with_persistent_coma():
    assert {a["variant"] for a in NEW_APPLICABILITY} == {"Stroke With Persistent Coma"}


def test_every_new_applicability_edge_is_hospice_support_for():
    assert {a["applicability_type"] for a in NEW_APPLICABILITY} == {"HOSPICE_SUPPORT_FOR"}


def test_no_cartesian_applicability_generation(built_state):
    """Exactly the 3 declared applicability edges exist for the new
    concepts -- never one row per (new concept x every Stroke variant)."""
    session = built_state["session"]
    stroke_id = built_state["stroke_disease"].id
    count = 0
    for entry in NEW_CONCEPTS:
        concept = _concept(session, stroke_id, entry["domain"], entry["name"])
        count += (
            session.query(OntologyConceptVariantApplicability)
            .filter_by(concept_type=entry["domain"], concept_id=concept.id)
            .count()
        )
    assert count == len(NEW_APPLICABILITY)


# ---------------------------------------------------------------------
# Functional Assessment Framework linkage (no duplication)
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "entry",
    FAF_LINKAGE,
    ids=[l["chf_concept_name"] for l in FAF_LINKAGE],
)
def test_every_faf_linkage_relationship_exists(built_state, entry):
    session = built_state["session"]
    # Stroke-side concepts here are HOSPICE_ELIGIBILITY_SUPPORT rows owned by
    # PR #37, so use the importer's full lookup helper.
    from scripts.import_stroke_coma_clinical_evidence_blueprint_v1 import _resolve_concept
    stroke_concept = _resolve_concept(session, built_state["stroke_disease"].id, entry["chf_concept_domain"], entry["chf_concept_name"])
    faf_concept = _resolve_concept(session, built_state["faf_disease"].id, FAF_LINKAGE_TARGET_DOMAIN, entry["faf_concept_name"])

    relationship = (
        session.query(OntologyRelationship)
        .filter_by(
            source_concept_type=entry["chf_concept_domain"],
            source_concept_id=stroke_concept.id,
            relationship_type=entry["relationship_type"],
            target_concept_type=FAF_LINKAGE_TARGET_DOMAIN,
            target_concept_id=faf_concept.id,
        )
        .one_or_none()
    )
    assert relationship is not None
    assert relationship.active is True
    match = PROVENANCE_PATTERN.search(relationship.description or "")
    assert match is not None
    assert match.group("cst") == entry["content_source_type"]
    assert match.group("crs") == entry["content_review_status"]


def test_faf_linkage_never_duplicates_scale_definition(built_state):
    """Each linkage points at PR #49's existing FINDING row for the whole
    scale -- it never creates a second FINDING row."""
    session = built_state["session"]
    from app.models.ontology_disease_blueprint import OntologyDiseaseFinding
    for entry in FAF_LINKAGE:
        matches = (
            session.query(OntologyDiseaseFinding)
            .filter_by(disease_id=built_state["faf_disease"].id)
            .filter(OntologyDiseaseFinding.finding_name == entry["faf_concept_name"])
            .all()
        )
        assert len(matches) == 1


def test_faf_linkage_uses_stroke_own_40_percent_threshold_concepts_not_70_percent():
    """Stroke's foundation uses a 40-percent PPS/KPS threshold convention
    (not the 'Less Than 70 Percent' convention used elsewhere) -- the
    linkage must reference Stroke's own existing concepts rather than
    inventing a new, duplicate 70-percent concept."""
    names = {l["chf_concept_name"] for l in FAF_LINKAGE}
    assert names == {
        "Palliative Performance Scale 40 Percent or Less",
        "Karnofsky Performance Status 40 Percent or Less",
    }


def test_relationship_type_is_consistent_across_all_linkages(built_state):
    assert {l["relationship_type"] for l in FAF_LINKAGE} == {RELATIONSHIP_TYPE}


# ---------------------------------------------------------------------
# Recertification trend indicators
# ---------------------------------------------------------------------


@pytest.mark.parametrize("entry", TREND_INDICATORS, ids=[t["name"] for t in TREND_INDICATORS])
def test_every_trend_indicator_exists(built_state, entry):
    session = built_state["session"]
    row = (
        session.query(OntologyDiseasePrognosticIndicator)
        .filter_by(disease_id=built_state["stroke_disease"].id)
        .filter(OntologyDiseasePrognosticIndicator.indicator_name.ilike(entry["name"].strip()))
        .one_or_none()
    )
    assert row is not None
    assert row.description == entry["description"]


@pytest.mark.parametrize("entry", TREND_INDICATORS, ids=[t["name"] for t in TREND_INDICATORS])
def test_every_trend_indicator_has_evidence_rule_with_provenance(built_state, entry):
    session = built_state["session"]
    row = (
        session.query(OntologyDiseasePrognosticIndicator)
        .filter_by(disease_id=built_state["stroke_disease"].id)
        .filter(OntologyDiseasePrognosticIndicator.indicator_name.ilike(entry["name"].strip()))
        .one()
    )
    rule = _evidence_rule(session, "PROGNOSTIC_INDICATOR", row.id)
    assert rule is not None
    match = PROVENANCE_PATTERN.search(rule.notes or "")
    assert match is not None
    assert match.group("cst") == entry["content_source_type"]
    assert match.group("crs") == entry["content_review_status"]


def test_recertification_indicators_cover_pps_kps_functional_nutritional_hospitalization_symptom_narrative(built_state):
    names = {t["name"] for t in TREND_INDICATORS}
    expected = {
        "PPS Trend", "KPS Trend", "Functional Trend", "Nutritional Trend",
        "Hospitalization Trend", "Symptom Trend", "Narrative Trend",
    }
    assert names == expected


# ---------------------------------------------------------------------
# AI capability boundary (documentation-only, mirrors FAF's trend_policy)
# ---------------------------------------------------------------------


def test_ai_layer_declares_allowed_capabilities():
    ai_may = set(MANIFEST["ai_layer"]["ai_may"])
    assert ai_may == {
        "missing_evidence_detection",
        "missing_documentation_detection",
        "recertification_gap_detection",
        "decline_trend_detection",
        "physician_review_prompts",
        "narrative_support_prompts",
    }


def test_ai_layer_forbids_diagnosis_eligibility_terminal_status_and_prognosis_engines():
    ai_may_not = set(MANIFEST["ai_layer"]["ai_may_not"])
    assert ai_may_not == {
        "diagnosis_engine",
        "eligibility_engine",
        "terminal_status_engine",
        "prognosis_engine",
    }


def test_ai_may_and_ai_may_not_never_overlap():
    ai_may = set(MANIFEST["ai_layer"]["ai_may"])
    ai_may_not = set(MANIFEST["ai_layer"]["ai_may_not"])
    assert ai_may & ai_may_not == set()


# ---------------------------------------------------------------------
# Idempotency and acceptance report
# ---------------------------------------------------------------------


def test_second_import_creates_zero_new_rows(built_state):
    session = built_state["session"]
    result = run_stroke_ceb_import(session, manifest=MANIFEST)
    session.commit()
    assert result["concepts_inserted_total"] == 0
    assert result["applicability_inserted"] == 0
    assert result["relationships_inserted"] == 0
    assert result["trend_indicators_inserted"] == 0
    assert result["evidence_rules_inserted"] == 0


def test_acceptance_report_shows_full_coverage(built_state):
    report = build_acceptance_report(built_state["session"], MANIFEST, second_run_new_rows=0)
    assert report["concepts"]["expected"] == report["concepts"]["stored"] == 3
    assert report["concepts"]["missing"] == []
    assert report["applicability"]["expected"] == report["applicability"]["stored"] == 3
    assert report["functional_assessment_relationships"]["expected"] == \
        report["functional_assessment_relationships"]["stored"] == 2
    assert report["recertification_trend_indicators"]["expected"] == \
        report["recertification_trend_indicators"]["stored"] == 7
    assert report["recertification_trend_indicators"]["missing"] == []
    assert report["provenance_coverage"]["checked"] == report["provenance_coverage"]["valid"] == 10
    assert report["second_run_new_rows"] == 0


def test_manifest_declares_no_schema_migration_api_or_disease_foundation_changes():
    assert "schema" not in MANIFEST
    assert "migration" not in MANIFEST
    assert "api" not in MANIFEST
    assert MANIFEST["rules"]["no_new_disease"] is True
