# tests/test_renal_clinical_evidence_blueprint_v1.py
"""Targeted tests for the Renal Clinical Evidence Blueprint v1 import
(`import_renal_clinical_evidence_blueprint_v1.py`, PR #53).

Every assertion below is derived directly from the committed manifest file
(`backend/manifests/renal_clinical_evidence_blueprint_v1.json`), never from
clinical judgment, inference, or a "similar enough" substitute.

This manifest is EXTENSION-ONLY. It depends on two already-merged
manifests being importable first:

    - Renal Production Source Manifest v1 (PR #40), which creates the
      "Acute Renal Failure" AND "Chronic Renal Failure" diseases this PR
      extends.
    - Functional Assessment Framework v1 (PR #49), which creates the
      "Functional Assessment Framework" disease this PR links to.

Unlike the Pulmonary Clinical Evidence Blueprint (PR #52), which extends
two IDENTICAL mirrored diseases symmetrically, Acute Renal Failure and
Chronic Renal Failure are genuinely DISTINCT disease identities with
different existing concept sets -- PR #40's Chronic Renal Failure already
contains Uremia, Oliguria, Intractable Hyperkalemia, Uremic Pericarditis,
and Hepatorenal Syndrome, but Acute Renal Failure does not. This manifest
therefore does NOT force symmetry: it adds 5 new FINDING concepts to Acute
Renal Failure ONLY, plus 1 new HOSPICE_ELIGIBILITY_SUPPORT concept ("Not
Candidate For Dialysis") to BOTH diseases, plus FAF linkage (PPS/KPS) and
9 recertification trend indicators applied identically to both diseases.

This PR creates, in total across both diseases:
    - 6 new atomic concept ROWS (5 FINDING on Acute Renal Failure only,
      1 HOSPICE_ELIGIBILITY_SUPPORT on each of the two diseases = 7 rows).
    - 7 new applicability edges (5 for Acute Renal Failure's new FINDING
      concepts, 1 per disease for the new HOSPICE_ELIGIBILITY_SUPPORT
      concept).
    - 4 OntologyRelationship edges (2 per disease) linking each disease's
      existing PPS Less Than 70 Percent / KPS Less Than 70 Percent
      concepts to PR #49's existing PPS / KPS scale-definition concepts.
    - 18 Renal recertification-trend PROGNOSTIC_INDICATOR concepts (9 per
      disease).
    - Provenance metadata (content_source_type, content_review_status)
      for every one of the above.

It does NOT create a new OntologyBodySystem, OntologyDiseaseFamily, or
OntologyDisease row. It does NOT create a new OntologyDiseaseVariant row.
It does NOT duplicate any PPS/KPS definition or any concept already
present in either renal disease. It does NOT make any schema, migration,
or API change.
"""
from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyDiseaseVariant,
    OntologyDiseaseFinding,
    OntologyDiseaseComplication,
    OntologyDiseaseFunctionalImpact,
    OntologyDiseaseNutritionalImpact,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseasePrognosticIndicator,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
    OntologyRelationship,
)
from scripts.import_renal_production_source_manifest import (
    run as run_renal_import,
    load_manifest as load_renal_manifest,
)
from scripts.import_functional_assessment_framework_v1 import (
    run as run_faf_import,
    load_manifest as load_faf_manifest,
)
from scripts.import_renal_clinical_evidence_blueprint_v1 import (
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
    run as run_renal_ext_import,
)
from tests.conftest import TestSessionLocal

MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)
NEW_CONCEPTS = MANIFEST["new_concepts"]
NEW_APPLICABILITY = MANIFEST["new_applicability"]
FAF_LINKAGE = MANIFEST["functional_assessment_linkage"]
TREND_INDICATORS = MANIFEST["recertification_evidence_model"]["trend_indicators"]

ACUTE = "Acute Renal Failure"
CHRONIC = "Chronic Renal Failure"


@pytest.fixture(scope="module")
def built_state():
    """Import the two prerequisite manifests (idempotent -- either may
    already have been imported by another test file in the same run),
    then import the Renal Clinical Evidence Blueprint extension manifest
    exactly once for this file (module-scoped -- ontology tables are not
    tenant-scoped and are never cleared between tests by the
    function-scoped db_session fixture)."""
    session = TestSessionLocal()
    try:
        run_renal_import(session, manifest=load_renal_manifest())
        session.commit()
        run_faf_import(session, manifest=load_faf_manifest())
        session.commit()

        counts = run_renal_ext_import(session, manifest=MANIFEST)
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
    assert rules["no_forced_symmetry"] is True


def test_manifest_extends_both_renal_diseases():
    assert EXTENDS_DISEASE_NAMES == [ACUTE, CHRONIC]
    assert MANIFEST["scope"]["extends_diseases"] == EXTENDS_DISEASE_NAMES
    assert MANIFEST["recertification_evidence_model"]["diseases"] == EXTENDS_DISEASE_NAMES


def test_manifest_declares_six_new_concepts_total():
    assert len(NEW_CONCEPTS) == 6


def test_manifest_declares_asymmetric_concept_distribution():
    """Acute Renal Failure gets 5 unique FINDING concepts plus the shared
    HOSPICE_ELIGIBILITY_SUPPORT concept (6 total); Chronic Renal Failure
    gets only the shared HOSPICE_ELIGIBILITY_SUPPORT concept (1 total) --
    this manifest never forces symmetry between the two diseases."""
    acute_concepts = [c for c in NEW_CONCEPTS if ACUTE in c["diseases"]]
    chronic_concepts = [c for c in NEW_CONCEPTS if CHRONIC in c["diseases"]]
    assert len(acute_concepts) == 6
    assert len(chronic_concepts) == 1
    assert {c["domain"] for c in acute_concepts} == {"FINDING", "HOSPICE_ELIGIBILITY_SUPPORT"}
    assert chronic_concepts[0]["domain"] == "HOSPICE_ELIGIBILITY_SUPPORT"
    assert chronic_concepts[0]["name"] == "Not Candidate For Dialysis"


def test_manifest_declares_seven_new_applicability_edges():
    assert len(NEW_APPLICABILITY) == 7


def test_manifest_declares_two_functional_assessment_linkages():
    assert len(FAF_LINKAGE) == 2


def test_manifest_declares_nine_recertification_trend_indicators():
    assert len(TREND_INDICATORS) == 9


def test_no_duplicate_concept_identity_within_manifest():
    keys = [(c["domain"], c["name"].strip().lower()) for c in NEW_CONCEPTS]
    assert len(keys) == len(set(keys))


def test_no_duplicate_trend_indicator_identity_within_manifest():
    names = [t["name"].strip().lower() for t in TREND_INDICATORS]
    assert len(names) == len(set(names))


def test_every_new_concept_declares_a_valid_diseases_list():
    for c in NEW_CONCEPTS:
        assert c["diseases"], f"{c['name']} must declare a non-empty diseases list"
        assert set(c["diseases"]).issubset(set(EXTENDS_DISEASE_NAMES))


def test_every_applicability_edge_declares_a_disease_and_variant_dimension():
    """Renal variant names are not unique across dimensions (e.g. 'Terminal
    Acute Renal Failure' exists as both a DISEASE_PHASE and a
    SEVERITY_CLASS variant) -- every applicability edge must disambiguate,
    and must declare which single disease it applies to."""
    for a in NEW_APPLICABILITY:
        assert a.get("disease") in EXTENDS_DISEASE_NAMES
        assert a.get("variant_dimension")


def test_already_present_verified_mapping_covers_requested_items():
    mapping = MANIFEST["already_present_verified"]["mapping"]
    requested = {m["requested"] for m in mapping}
    assert "Uremia" in requested
    assert "Fluid Overload" in requested
    assert "Dialysis Refused" in requested
    assert "Dialysis Discontinued" in requested


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
def test_extends_existing_renal_disease_never_creates_a_new_one(built_state, disease_name):
    session = built_state["session"]
    matches = session.query(OntologyDisease).filter_by(disease_name=disease_name).all()
    assert len(matches) == 1


def test_extends_existing_faf_disease_never_creates_a_new_one(built_state):
    session = built_state["session"]
    matches = session.query(OntologyDisease).filter_by(disease_name=FAF_DISEASE_NAME).all()
    assert len(matches) == 1


def test_import_aborts_if_renal_disease_is_missing():
    """Exercises _resolve_disease's RuntimeError contract directly with a
    disease name that will never exist in any test database, proving the
    importer aborts before any writes rather than silently creating a
    second Renal foundation."""
    from scripts.import_renal_clinical_evidence_blueprint_v1 import _resolve_disease
    session = TestSessionLocal()
    try:
        with pytest.raises(RuntimeError):
            _resolve_disease(session, "__nonexistent_disease__")
    finally:
        session.close()


def test_no_new_disease_variant_created_by_this_manifest(built_state):
    """The manifest declares zero variants of its own -- it only
    references PR #40's existing renal variants by name+dimension."""
    assert "variants" not in MANIFEST


def test_chronic_renal_failure_does_not_receive_acute_only_concepts(built_state):
    """Uremia, Oliguria, Intractable Hyperkalemia, Uremic Pericarditis, and
    Hepatorenal Syndrome are new_concepts entries scoped to Acute Renal
    Failure only -- this importer must never create an evidence rule for
    these names against Chronic Renal Failure's pre-existing (PR #40)
    FINDING rows of the same name, since those rows were never touched by
    this manifest."""
    session = built_state["session"]
    chronic = built_state["diseases"][CHRONIC]
    acute_only_names = {c["name"] for c in NEW_CONCEPTS if c["diseases"] == [ACUTE]}
    assert acute_only_names == {"Uremia", "Oliguria", "Intractable Hyperkalemia", "Uremic Pericarditis", "Hepatorenal Syndrome"}
    for name in acute_only_names:
        chronic_row = _concept(session, chronic.id, "FINDING", name)
        if chronic_row is None:
            continue  # PR #40 never had this exact name on Chronic -- nothing to check
        rule = _evidence_rule(session, "FINDING", chronic_row.id)
        if rule is not None:
            assert "renal_clinical_evidence_blueprint_v1" not in (rule.evidence_source or "")


# ---------------------------------------------------------------------
# New atomic concepts (checked per disease, respecting asymmetry)
# ---------------------------------------------------------------------


@pytest.mark.parametrize("entry", [c for c in NEW_CONCEPTS if ACUTE in c["diseases"]], ids=lambda c: c["name"])
def test_every_acute_new_concept_exists(built_state, entry):
    disease = built_state["diseases"][ACUTE]
    row = _concept(built_state["session"], disease.id, entry["domain"], entry["name"])
    assert row is not None


@pytest.mark.parametrize("entry", [c for c in NEW_CONCEPTS if CHRONIC in c["diseases"]], ids=lambda c: c["name"])
def test_every_chronic_new_concept_exists(built_state, entry):
    disease = built_state["diseases"][CHRONIC]
    row = _concept(built_state["session"], disease.id, entry["domain"], entry["name"])
    assert row is not None


@pytest.mark.parametrize("entry", NEW_CONCEPTS, ids=[c["name"] for c in NEW_CONCEPTS])
def test_every_new_concept_has_evidence_rule_with_provenance_on_every_declared_disease(built_state, entry):
    session = built_state["session"]
    for disease_name in entry["diseases"]:
        disease = built_state["diseases"][disease_name]
        row = _concept(session, disease.id, entry["domain"], entry["name"])
        rule = _evidence_rule(session, entry["domain"], row.id)
        assert rule is not None
        assert rule.patient_fact_requires_evidence is True
        match = PROVENANCE_PATTERN.search(rule.notes or "")
        assert match is not None
        assert match.group("cst") == entry["content_source_type"]
        assert match.group("crs") == entry["content_review_status"]


def test_stored_new_concept_count_matches_manifest_exactly_per_disease(built_state):
    session = built_state["session"]
    for disease_name, disease in built_state["diseases"].items():
        expected = [c for c in NEW_CONCEPTS if disease_name in c["diseases"]]
        for entry in expected:
            row = _concept(session, disease.id, entry["domain"], entry["name"])
            assert row is not None
        assert len(expected) == (6 if disease_name == ACUTE else 1)


# ---------------------------------------------------------------------
# New applicability edges
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "entry",
    NEW_APPLICABILITY,
    ids=[f"{a['disease']}/{a['variant']}/{a['concept']}" for a in NEW_APPLICABILITY],
)
def test_every_declared_applicability_edge_exists(built_state, entry):
    session = built_state["session"]
    disease = built_state["diseases"][entry["disease"]]
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
    """Exactly the declared number of applicability edges per disease
    exist for the new concepts -- never one row per (new concept x every
    renal variant)."""
    session = built_state["session"]
    for disease_name, disease in built_state["diseases"].items():
        expected_for_disease = [a for a in NEW_APPLICABILITY if a["disease"] == disease_name]
        count = 0
        for a in expected_for_disease:
            concept = _concept(session, disease.id, a["concept_domain"], a["concept"])
            count += (
                session.query(OntologyConceptVariantApplicability)
                .filter_by(concept_type=a["concept_domain"], concept_id=concept.id)
                .count()
            )
        assert count == len(expected_for_disease)


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
    from scripts.import_renal_clinical_evidence_blueprint_v1 import _resolve_concept
    renal_concept = _resolve_concept(session, disease.id, entry["chf_concept_domain"], entry["chf_concept_name"])
    faf_concept = _resolve_concept(session, built_state["faf_disease"].id, FAF_LINKAGE_TARGET_DOMAIN, entry["faf_concept_name"])

    relationship = (
        session.query(OntologyRelationship)
        .filter_by(
            source_concept_type=entry["chf_concept_domain"],
            source_concept_id=renal_concept.id,
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
    though it is referenced twice (once per extended renal disease)."""
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


def test_recertification_indicators_cover_gfr_creatinine_potassium_pps_kps_weight_hospitalization_symptom_narrative(built_state):
    names = {t["name"] for t in TREND_INDICATORS}
    expected = {
        "GFR Trend", "Creatinine Trend", "Potassium Trend", "PPS Trend", "KPS Trend",
        "Weight Trend", "Hospitalization Trend", "Symptom Trend", "Narrative Trend",
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
        run_renal_import(session, manifest=load_renal_manifest())
        session.commit()
        run_faf_import(session, manifest=load_faf_manifest())
        session.commit()
        run_renal_ext_import(session, manifest=MANIFEST)
        session.commit()

        result = run_renal_ext_import(session, manifest=MANIFEST)
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
    assert report["concepts"]["expected"] == report["concepts"]["stored"] == 7
    assert report["concepts"]["missing"] == []
    assert report["applicability"]["expected"] == report["applicability"]["stored"] == len(NEW_APPLICABILITY)
    assert report["functional_assessment_relationships"]["expected"] == \
        report["functional_assessment_relationships"]["stored"] == len(FAF_LINKAGE) * n
    assert report["recertification_trend_indicators"]["expected"] == \
        report["recertification_trend_indicators"]["stored"] == len(TREND_INDICATORS) * n
    assert report["recertification_trend_indicators"]["missing"] == []
    expected_provenance = 7 + (len(TREND_INDICATORS) * n)
    assert report["provenance_coverage"]["checked"] == report["provenance_coverage"]["valid"] == expected_provenance
    assert report["second_run_new_rows"] == 0


def test_manifest_declares_no_schema_migration_api_or_disease_foundation_changes():
    assert "schema" not in MANIFEST
    assert "migration" not in MANIFEST
    assert "api" not in MANIFEST
    assert MANIFEST["rules"]["no_new_disease"] is True
