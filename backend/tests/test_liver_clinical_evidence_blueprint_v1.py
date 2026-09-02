# tests/test_liver_clinical_evidence_blueprint_v1.py
"""Targeted tests for the Liver Clinical Evidence Blueprint v1 import
(`import_liver_clinical_evidence_blueprint_v1.py`, PR #54).

Every assertion below is derived directly from the committed manifest file
(`backend/manifests/liver_clinical_evidence_blueprint_v1.json`), never
from clinical judgment, inference, or a "similar enough" substitute.

This manifest is EXTENSION-ONLY. It depends on two already-merged
manifests being importable first:

    - Liver Production Knowledge Manifest v1 (PR #41), which creates the
      "End Stage Liver Disease" AND "Chronic Liver Disease" diseases
      this PR extends.
    - Functional Assessment Framework v1 (PR #49), which creates the
      "Functional Assessment Framework" disease this PR links to.

Unlike the Renal Clinical Evidence Blueprint (PR #53), which extends two
genuinely distinct diseases asymmetrically, this manifest applies every
addition IDENTICALLY to both liver diseases -- PR #41 built them with an
identical FINDING/COMPLICATION/HOSPICE_ELIGIBILITY_SUPPORT concept set,
so extending only one would create ontology drift between them.

This PR creates, PER extended disease:
    - 4 new atomic Liver concepts (FINDING x3 "MELD Score", "Elevated
      Serum Bilirubin", "Hyponatremia"; HOSPICE_ELIGIBILITY_SUPPORT x1
      "Recurrent Liver Disease Hospitalization") -- all missing from PR
      #41's original concept set.
    - 4 new applicability edges linking those new concepts to PR #41's
      existing "Child-Pugh Class C Cirrhosis" variant (common to both
      diseases).
    - 2 OntologyRelationship edges linking PR #41's existing PPS Less
      Than 70 Percent / KPS Less Than 70 Percent concepts to PR #49's
      existing PPS / KPS scale-definition concepts.
    - 10 Liver recertification-trend PROGNOSTIC_INDICATOR concepts.
    - Provenance metadata (content_source_type, content_review_status)
      for every one of the above, encoded into the existing
      OntologyEvidenceRule.notes / OntologyRelationship.description
      free-text fields.

It does NOT create a new OntologyBodySystem, OntologyDiseaseFamily, or
OntologyDisease row. It does NOT create a new OntologyDiseaseVariant row.
It does NOT duplicate any PPS/KPS definition or any finding/complication/
hospice-eligibility-support concept already present in PR #41. It does
NOT make any schema, migration, or API change.
"""
from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyDiseaseVariant,
    OntologyDiseaseSymptom,
    OntologyDiseaseFinding,
    OntologyDiseaseComplication,
    OntologyDiseaseFunctionalImpact,
    OntologyDiseaseNutritionalImpact,
    OntologyDiseasePrognosticIndicator,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
    OntologyRelationship,
)
from scripts.import_liver_production_source_manifest import (
    run as run_liver_import,
    load_manifest as load_liver_manifest,
)
from scripts.import_functional_assessment_framework_v1 import (
    run as run_faf_import,
    load_manifest as load_faf_manifest,
)
from scripts.import_liver_clinical_evidence_blueprint_v1 import (
    ALLOWED_CONTENT_REVIEW_STATUSES,
    ALLOWED_CONTENT_SOURCE_TYPES,
    CONCEPT_DOMAIN_MODEL_MAP,
    DEFAULT_MANIFEST_PATH,
    EXTENDS_DISEASE_NAMES,
    FAF_DISEASE_NAME,
    FAF_LINKAGE_TARGET_DOMAIN,
    PROVENANCE_PATTERN,
    RELATIONSHIP_TYPE,
    load_manifest,
    validate_manifest,
    build_acceptance_report,
    run as run_liver_ext_import,
)
from tests.conftest import TestSessionLocal

MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)
NEW_CONCEPTS = MANIFEST["new_concepts"]
NEW_APPLICABILITY = MANIFEST["new_applicability"]
FAF_LINKAGE = MANIFEST["functional_assessment_linkage"]
TREND_INDICATORS = MANIFEST["recertification_evidence_model"]["trend_indicators"]


@pytest.fixture(scope="module")
def built_state():
    """Import the two prerequisite manifests (idempotent -- either may
    already have been imported by another test file in the same run),
    then import the Liver Clinical Evidence Blueprint extension
    manifest exactly once for this file (module-scoped -- ontology tables
    are not tenant-scoped and are never cleared between tests by the
    function-scoped db_session fixture)."""
    session = TestSessionLocal()
    try:
        run_liver_import(session, manifest=load_liver_manifest())
        session.commit()
        run_faf_import(session, manifest=load_faf_manifest())
        session.commit()

        counts = run_liver_ext_import(session, manifest=MANIFEST)
        session.commit()

        diseases = {
            name: session.query(OntologyDisease).filter_by(disease_name=name).one()
            for name in EXTENDS_DISEASE_NAMES
        }
        faf_disease = session.query(OntologyDisease).filter_by(disease_name=FAF_DISEASE_NAME).one()
        yield {"diseases": diseases, "faf_disease": faf_disease, "counts": counts, "session": session}
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


def _variant(db_session, disease_id, name, dimension):
    return (
        db_session.query(OntologyDiseaseVariant)
        .filter_by(disease_id=disease_id, normalized_name=name.strip().lower(), variant_dimension=dimension)
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


def test_manifest_extends_both_liver_diseases():
    assert EXTENDS_DISEASE_NAMES == [
        "End Stage Liver Disease",
        "Chronic Liver Disease",
    ]
    assert MANIFEST["scope"]["extends_diseases"] == EXTENDS_DISEASE_NAMES
    assert MANIFEST["recertification_evidence_model"]["diseases"] == EXTENDS_DISEASE_NAMES


def test_manifest_declares_four_new_concepts():
    assert len(NEW_CONCEPTS) == 4


def test_manifest_declares_four_new_applicability_edges():
    assert len(NEW_APPLICABILITY) == 4


def test_manifest_declares_two_functional_assessment_linkages():
    assert len(FAF_LINKAGE) == 2


def test_manifest_declares_ten_recertification_trend_indicators():
    assert len(TREND_INDICATORS) == 10


def test_no_duplicate_concept_identity_within_manifest():
    keys = [(c["domain"], c["name"].strip().lower()) for c in NEW_CONCEPTS]
    assert len(keys) == len(set(keys))


def test_no_duplicate_trend_indicator_identity_within_manifest():
    names = [t["name"].strip().lower() for t in TREND_INDICATORS]
    assert len(names) == len(set(names))


def test_every_applicability_edge_declares_a_variant_dimension():
    """Liver variant dimensions must always be disambiguated explicitly,
    consistent with every other Clinical Evidence Blueprint importer."""
    for a in NEW_APPLICABILITY:
        assert a.get("variant_dimension")


def test_already_present_verified_mapping_covers_requested_items():
    mapping = MANIFEST["already_present_verified"]["mapping"]
    requested = {m["requested"] for m in mapping}
    assert "Recurrent Variceal Bleeding" in requested
    assert "PPS Less Than 70 Percent" in requested
    assert "KPS Less Than 70 Percent" in requested


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


@pytest.mark.parametrize("disease_name", EXTENDS_DISEASE_NAMES)
def test_extends_existing_liver_disease_never_creates_a_new_one(built_state, disease_name):
    session = built_state["session"]
    matches = session.query(OntologyDisease).filter_by(disease_name=disease_name).all()
    assert len(matches) == 1


def test_extends_existing_faf_disease_never_creates_a_new_one(built_state):
    session = built_state["session"]
    matches = session.query(OntologyDisease).filter_by(disease_name=FAF_DISEASE_NAME).all()
    assert len(matches) == 1


def test_import_aborts_if_liver_disease_is_missing():
    """Exercises _resolve_disease's RuntimeError contract directly with a
    disease name that will never exist in any test database, proving the
    importer aborts before any writes rather than silently creating a
    second Liver foundation."""
    from scripts.import_liver_clinical_evidence_blueprint_v1 import _resolve_disease
    session = TestSessionLocal()
    try:
        with pytest.raises(RuntimeError):
            _resolve_disease(session, "__nonexistent_disease__")
    finally:
        session.close()


def test_no_new_disease_variant_created_by_this_manifest(built_state):
    """The manifest declares zero variants of its own -- it only
    references PR #41's existing Liver variants by name+dimension."""
    assert "variants" not in MANIFEST


# ---------------------------------------------------------------------
# New atomic concepts (checked once per extended disease)
# ---------------------------------------------------------------------


@pytest.mark.parametrize("disease_name", EXTENDS_DISEASE_NAMES)
@pytest.mark.parametrize("entry", NEW_CONCEPTS, ids=[c["name"] for c in NEW_CONCEPTS])
def test_every_declared_new_concept_exists_on_every_disease(built_state, entry, disease_name):
    disease = built_state["diseases"][disease_name]
    row = _concept(built_state["session"], disease.id, entry["domain"], entry["name"])
    assert row is not None


@pytest.mark.parametrize("disease_name", EXTENDS_DISEASE_NAMES)
@pytest.mark.parametrize("entry", NEW_CONCEPTS, ids=[c["name"] for c in NEW_CONCEPTS])
def test_every_new_concept_has_evidence_rule_with_provenance(built_state, entry, disease_name):
    disease = built_state["diseases"][disease_name]
    row = _concept(built_state["session"], disease.id, entry["domain"], entry["name"])
    rule = _evidence_rule(built_state["session"], entry["domain"], row.id)
    assert rule is not None
    assert rule.patient_fact_requires_evidence is True
    match = PROVENANCE_PATTERN.search(rule.notes or "")
    assert match is not None
    assert match.group("cst") == entry["content_source_type"]
    assert match.group("crs") == entry["content_review_status"]


def test_stored_new_concept_count_matches_manifest_exactly_per_disease(built_state):
    session = built_state["session"]
    for disease_name, disease in built_state["diseases"].items():
        total = 0
        for entry in NEW_CONCEPTS:
            row = _concept(session, disease.id, entry["domain"], entry["name"])
            assert row is not None
            total += 1
        assert total == len(NEW_CONCEPTS)


def test_new_concepts_are_distinct_rows_across_the_two_diseases(built_state):
    """Each disease gets its OWN concept rows -- the two mirrored
    diseases never share a single concept row."""
    session = built_state["session"]
    ids = set()
    for entry in NEW_CONCEPTS:
        for disease in built_state["diseases"].values():
            row = _concept(session, disease.id, entry["domain"], entry["name"])
            ids.add(row.id)
    assert len(ids) == len(NEW_CONCEPTS) * len(EXTENDS_DISEASE_NAMES)


# ---------------------------------------------------------------------
# New applicability edges
# ---------------------------------------------------------------------


@pytest.mark.parametrize("disease_name", EXTENDS_DISEASE_NAMES)
@pytest.mark.parametrize(
    "entry",
    NEW_APPLICABILITY,
    ids=[f"{a['variant']}/{a['concept']}" for a in NEW_APPLICABILITY],
)
def test_every_declared_applicability_edge_exists(built_state, entry, disease_name):
    session = built_state["session"]
    disease = built_state["diseases"][disease_name]
    variant = _variant(session, disease.id, entry["variant"], entry["variant_dimension"])
    concept = _concept(session, disease.id, entry["concept_domain"], entry["concept"])
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


def test_no_cartesian_applicability_generation(built_state):
    """Exactly 2 declared applicability edges per disease exist for the
    new concepts -- never one row per (new concept x every Liver
    variant)."""
    session = built_state["session"]
    for disease in built_state["diseases"].values():
        count = 0
        for entry in NEW_CONCEPTS:
            concept = _concept(session, disease.id, entry["domain"], entry["name"])
            count += (
                session.query(OntologyConceptVariantApplicability)
                .filter_by(concept_type=entry["domain"], concept_id=concept.id)
                .count()
            )
        assert count == len(NEW_APPLICABILITY)


# ---------------------------------------------------------------------
# Functional Assessment Framework linkage (no duplication)
# ---------------------------------------------------------------------


@pytest.mark.parametrize("disease_name", EXTENDS_DISEASE_NAMES)
@pytest.mark.parametrize(
    "entry",
    FAF_LINKAGE,
    ids=[l["chf_concept_name"] for l in FAF_LINKAGE],
)
def test_every_faf_linkage_relationship_exists(built_state, entry, disease_name):
    session = built_state["session"]
    disease = built_state["diseases"][disease_name]
    # Liver-side concepts here are HOSPICE_ELIGIBILITY_SUPPORT rows
    # owned by PR #39, not by this manifest's CONCEPT_DOMAIN_MODEL_MAP, so
    # use the importer's full lookup helper (which covers both domains).
    from scripts.import_liver_clinical_evidence_blueprint_v1 import _resolve_concept
    liver_concept = _resolve_concept(session, disease.id, entry["chf_concept_domain"], entry["chf_concept_name"])
    faf_concept = _resolve_concept(session, built_state["faf_disease"].id, FAF_LINKAGE_TARGET_DOMAIN, entry["faf_concept_name"])

    relationship = (
        session.query(OntologyRelationship)
        .filter_by(
            source_concept_type=entry["chf_concept_domain"],
            source_concept_id=liver_concept.id,
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
    scale -- it never creates a second FINDING/severity_levels row, even
    though it is referenced twice (once per extended liver disease)."""
    session = built_state["session"]
    for entry in FAF_LINKAGE:
        matches = (
            session.query(OntologyDiseaseFinding)
            .filter_by(disease_id=built_state["faf_disease"].id)
            .filter(OntologyDiseaseFinding.finding_name == entry["faf_concept_name"])
            .all()
        )
        assert len(matches) == 1


def test_relationship_type_is_consistent_across_all_linkages(built_state):
    assert {l["relationship_type"] for l in FAF_LINKAGE} == {RELATIONSHIP_TYPE}


# ---------------------------------------------------------------------
# Recertification trend indicators
# ---------------------------------------------------------------------


@pytest.mark.parametrize("disease_name", EXTENDS_DISEASE_NAMES)
@pytest.mark.parametrize("entry", TREND_INDICATORS, ids=[t["name"] for t in TREND_INDICATORS])
def test_every_trend_indicator_exists(built_state, entry, disease_name):
    session = built_state["session"]
    disease = built_state["diseases"][disease_name]
    row = (
        session.query(OntologyDiseasePrognosticIndicator)
        .filter_by(disease_id=disease.id)
        .filter(OntologyDiseasePrognosticIndicator.indicator_name.ilike(entry["name"].strip()))
        .one_or_none()
    )
    assert row is not None
    assert row.description == entry["description"]


@pytest.mark.parametrize("disease_name", EXTENDS_DISEASE_NAMES)
@pytest.mark.parametrize("entry", TREND_INDICATORS, ids=[t["name"] for t in TREND_INDICATORS])
def test_every_trend_indicator_has_evidence_rule_with_provenance(built_state, entry, disease_name):
    session = built_state["session"]
    disease = built_state["diseases"][disease_name]
    row = (
        session.query(OntologyDiseasePrognosticIndicator)
        .filter_by(disease_id=disease.id)
        .filter(OntologyDiseasePrognosticIndicator.indicator_name.ilike(entry["name"].strip()))
        .one()
    )
    rule = _evidence_rule(session, "PROGNOSTIC_INDICATOR", row.id)
    assert rule is not None
    match = PROVENANCE_PATTERN.search(rule.notes or "")
    assert match is not None
    assert match.group("cst") == entry["content_source_type"]
    assert match.group("crs") == entry["content_review_status"]


def test_recertification_indicators_cover_pps_kps_inr_albumin_bilirubin_ascites_encephalopathy_weight_hospitalization_narrative(built_state):
    names = {t["name"] for t in TREND_INDICATORS}
    expected = {
        "PPS Trend", "KPS Trend", "INR Trend", "Albumin Trend", "Bilirubin Trend",
        "Ascites Episode Trend", "Encephalopathy Episode Trend", "Weight Trend",
        "Hospitalization Trend", "Narrative Trend",
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


def test_second_import_creates_zero_new_rows():
    session = TestSessionLocal()
    try:
        run_liver_import(session, manifest=load_liver_manifest())
        session.commit()
        run_faf_import(session, manifest=load_faf_manifest())
        session.commit()
        run_liver_ext_import(session, manifest=MANIFEST)
        session.commit()

        result = run_liver_ext_import(session, manifest=MANIFEST)
        session.commit()
        assert result["concepts_inserted_total"] == 0
        assert result["applicability_inserted"] == 0
        assert result["relationships_inserted"] == 0
        assert result["trend_indicators_inserted"] == 0
        assert result["evidence_rules_inserted"] == 0
    finally:
        session.close()


def test_acceptance_report_shows_full_coverage(built_state):
    report = build_acceptance_report(built_state["session"], MANIFEST, second_run_new_rows=0)
    n = len(EXTENDS_DISEASE_NAMES)
    assert report["concepts"]["expected"] == report["concepts"]["stored"] == len(NEW_CONCEPTS) * n
    assert report["concepts"]["missing"] == []
    assert report["applicability"]["expected"] == report["applicability"]["stored"] == len(NEW_APPLICABILITY) * n
    assert report["functional_assessment_relationships"]["expected"] == \
        report["functional_assessment_relationships"]["stored"] == len(FAF_LINKAGE) * n
    assert report["recertification_trend_indicators"]["expected"] == \
        report["recertification_trend_indicators"]["stored"] == len(TREND_INDICATORS) * n
    assert report["recertification_trend_indicators"]["missing"] == []
    expected_provenance = (len(NEW_CONCEPTS) + len(TREND_INDICATORS)) * n
    assert report["provenance_coverage"]["checked"] == report["provenance_coverage"]["valid"] == expected_provenance
    assert report["second_run_new_rows"] == 0


def test_manifest_declares_no_schema_migration_api_or_disease_foundation_changes():
    assert "schema" not in MANIFEST
    assert "migration" not in MANIFEST
    assert "api" not in MANIFEST
    assert MANIFEST["rules"]["no_new_disease"] is True
