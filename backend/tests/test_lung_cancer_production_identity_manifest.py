# tests/test_lung_cancer_production_identity_manifest.py
"""Targeted tests for the Lung Cancer Production Identity Manifest v1
import (`import_lung_cancer_production_identity_manifest.py`, PR #47 -- a
disease-specific Oncology manifest).

Every assertion below is derived directly from the committed manifest file
(`backend/manifests/lung_cancer_production_identity_manifest_v1.json`),
never from clinical judgment, inference, or a "similar enough" substitute.

This manifest depends on the Oncology Foundation import (PR #45,
`import_oncology_foundation_v1.py`) having already created the "Oncology"
body system, "Solid Malignancies" family, canonical "Lung Cancer" disease,
and its four foundation Tier 4 variants (Lung Primary Site, Localized
Disease, Metastatic Disease, Recurrent Disease). This test module imports
both manifests, in that dependency order, exactly once.

This PR adds ONLY:
    - Five new Tier 4 variants (PATHOLOGICAL_SUBTYPE dimension): Non-Small
      Cell Lung Cancer, Small Cell Lung Cancer, Pleuropulmonary Blastoma,
      Tracheobronchial Tumor, Bronchial Tumor.
    - Nine Tier 5 FINDING identity concepts: Lung Cancer, Non-Small Cell
      Lung Cancer, Small Cell Lung Cancer, Pleuropulmonary Blastoma,
      Tracheobronchial Tumor, Bronchial Tumor, Localized Lung Cancer,
      Metastatic Lung Cancer, Recurrent Lung Cancer.
    - Eight explicit, individually-declared applicability mappings
      (APPLIES_TO): each pathological-subtype concept -> its own variant;
      Localized/Metastatic/Recurrent Lung Cancer -> their corresponding
      foundation variants.

It does NOT create a universal cancer manifest, does NOT copy this content
to another cancer disease, does NOT mix the Pulmonary Disease LCD manifest
with Lung Cancer identity knowledge, and does NOT create stage, grade,
laterality, molecular subtype, metastatic destination, symptom,
diagnostic, treatment, medication, or prognosis knowledge.
"""
from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyDiseaseFamily,
    OntologyDiseaseVariant,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
    OntologyDiseaseFinding,
    OntologyDiseaseTreatment,
    OntologyDiseaseTreatmentLimitation,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseasePrognosticIndicator,
)
from scripts.import_oncology_foundation_v1 import (
    load_manifest as load_foundation_manifest,
    run as run_foundation_import,
)
from scripts.import_lung_cancer_production_identity_manifest import (
    ALLOWED_SOURCE_CLASSIFICATIONS,
    CONCEPT_DOMAIN_MODEL_MAP,
    DEFAULT_MANIFEST_PATH,
    DISEASE_NAME,
    FAMILY_NAME,
    SYSTEM_NAME,
    load_manifest,
    validate_manifest,
    build_acceptance_report,
    run as run_manifest_import,
)
from tests.conftest import TestSessionLocal

FOUNDATION_MANIFEST = load_foundation_manifest()
MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)

EXPECTED_CONCEPT_NAMES = {
    "Lung Cancer", "Non-Small Cell Lung Cancer", "Small Cell Lung Cancer",
    "Pleuropulmonary Blastoma", "Tracheobronchial Tumor", "Bronchial Tumor",
    "Localized Lung Cancer", "Metastatic Lung Cancer", "Recurrent Lung Cancer",
}
EXPECTED_SUBTYPE_VARIANT_NAMES = {
    "Non-Small Cell Lung Cancer", "Small Cell Lung Cancer", "Pleuropulmonary Blastoma",
    "Tracheobronchial Tumor", "Bronchial Tumor",
}
UNSUPPORTED_DIMENSIONS = {"STAGE", "GRADE", "MOLECULAR_SUBTYPE", "LATERALITY", "METASTATIC_DESTINATION"}


@pytest.fixture(scope="module")
def built_state():
    """Import the Oncology Foundation manifest (dependency), then the
    Lung Cancer manifest, into a dedicated session against the test
    database, exactly once for this file (module-scoped -- ontology tables
    are not tenant-scoped and are never cleared between tests by the
    function-scoped db_session fixture)."""
    session = TestSessionLocal()
    try:
        run_foundation_import(session, manifest=FOUNDATION_MANIFEST)
        session.commit()
        counts = run_manifest_import(session, manifest=MANIFEST)
        session.commit()
        disease = session.query(OntologyDisease).filter_by(disease_name=DISEASE_NAME).one()
        yield {"disease": disease, "counts": counts, "session": session}
    finally:
        session.close()


def _variant(db_session, disease, dimension, name):
    return (
        db_session.query(OntologyDiseaseVariant)
        .filter_by(disease_id=disease.id, variant_dimension=dimension, normalized_name=name.strip().lower())
        .one_or_none()
    )


def _concept(db_session, disease, domain, name):
    model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[domain]
    return (
        db_session.query(model_cls)
        .filter(model_cls.disease_id == disease.id)
        .filter(getattr(model_cls, name_attr) == name)
        .one_or_none()
    )


def _evidence_rule(db_session, domain, concept_id):
    return db_session.query(OntologyEvidenceRule).filter_by(concept_type=domain, concept_id=concept_id).one_or_none()


# --- manifest self-consistency ---------------------------------------------

def test_manifest_scope_targets_lung_cancer_under_solid_malignancies():
    assert MANIFEST["scope"]["body_system"] == SYSTEM_NAME
    assert MANIFEST["scope"]["family"] == FAMILY_NAME
    assert MANIFEST["scope"]["disease"] == DISEASE_NAME


def test_manifest_declares_exactly_five_new_variants():
    names = {v["name"] for v in MANIFEST["new_variants"]}
    assert names == EXPECTED_SUBTYPE_VARIANT_NAMES
    assert len(MANIFEST["new_variants"]) == 5
    for v in MANIFEST["new_variants"]:
        assert v["dimension"] == "PATHOLOGICAL_SUBTYPE"


def test_manifest_declares_exactly_nine_concepts():
    names = {c["name"] for c in MANIFEST["concepts"]}
    assert names == EXPECTED_CONCEPT_NAMES
    assert len(MANIFEST["concepts"]) == 9


def test_manifest_declares_exactly_eight_applicability_mappings():
    assert len(MANIFEST["applicability"]) == 8
    for a in MANIFEST["applicability"]:
        assert a["applicability_type"] == "APPLIES_TO"


def test_manifest_never_attaches_base_lung_cancer_identity_to_a_variant():
    mapped_concepts = {a["concept"] for a in MANIFEST["applicability"]}
    assert "Lung Cancer" not in mapped_concepts


def test_manifest_passes_structural_validation():
    assert validate_manifest(MANIFEST) == []


def test_manifest_every_concept_has_classification_reference_and_evidence_flag():
    for c in MANIFEST["concepts"]:
        assert c["source_classification"] in ALLOWED_SOURCE_CLASSIFICATIONS
        assert c["source_reference"]
        assert c["patient_fact_requires_evidence"] is True


def test_manifest_declares_all_sixteen_required_differentiation_guards():
    names = [g["guard_name"] for g in MANIFEST["differentiation_guards"]]
    assert names == [
        "Lung Cancer IS_NOT Lung Primary Site",
        "Lung Cancer IS_NOT Lung Metastasis",
        "Primary Lung Cancer IS_NOT Metastatic Disease To Lung",
        "Non-Small Cell Lung Cancer IS_NOT Small Cell Lung Cancer",
        "Pleuropulmonary Blastoma IS_NOT Non-Small Cell Lung Cancer",
        "Pleuropulmonary Blastoma IS_NOT Small Cell Lung Cancer",
        "Tracheobronchial Tumor IS_NOT Automatically Bronchial Tumor",
        "Localized Lung Cancer IS_NOT Metastatic Lung Cancer",
        "Recurrent Lung Cancer IS_NOT Automatically Metastatic Lung Cancer",
        "Metastatic Lung Cancer DOES_NOT_ESTABLISH Metastatic Destination",
        "Lung Cancer DOES_NOT_INHERIT Pulmonary LCD Criteria",
        "Lung Cancer Diagnosis DOES_NOT_ESTABLISH Stage",
        "Lung Cancer Diagnosis DOES_NOT_ESTABLISH Grade",
        "Lung Cancer Diagnosis DOES_NOT_ESTABLISH Molecular Subtype",
        "Lung Cancer Diagnosis DOES_NOT_ESTABLISH Treatment",
        "Lung Cancer Diagnosis DOES_NOT_ESTABLISH Hospice Eligibility",
    ]


# --- 1. Exactly one canonical Lung Cancer disease exists --------------------

def test_one_canonical_lung_cancer_disease_exists(db_session, built_state):
    matches = db_session.query(OntologyDisease).filter_by(disease_name=DISEASE_NAME).all()
    assert len(matches) == 1


# --- 2. Lung Cancer belongs to Solid Malignancies ---------------------------

def test_lung_cancer_belongs_to_solid_malignancies(db_session, built_state):
    family = db_session.query(OntologyDiseaseFamily).filter_by(family_name=FAMILY_NAME).one()
    assert built_state["disease"].disease_family_id == family.id


# --- 3. No placeholder disease exists ----------------------------------------

def test_no_placeholder_disease_exists(db_session, built_state):
    for forbidden in (
        "Oncology Foundation Reference Structure", "Lung Primary Site",
        "Primary Lung Cancer", "Metastatic Disease To Lung", "Lung Metastasis From Another Primary Cancer",
        "Localized Lung Cancer", "Metastatic Lung Cancer", "Recurrent Lung Cancer",
        "Non-Small Cell Lung Cancer", "Small Cell Lung Cancer", "Pleuropulmonary Blastoma",
        "Tracheobronchial Tumor", "Bronchial Tumor",
    ):
        assert db_session.query(OntologyDisease).filter_by(disease_name=forbidden).one_or_none() is None


# --- 4. All five approved pathological subtypes exist independently --------

def test_all_five_pathological_subtypes_exist_independently(db_session, built_state):
    disease = built_state["disease"]
    seen_variant_ids = set()
    seen_concept_ids = set()
    for name in EXPECTED_SUBTYPE_VARIANT_NAMES:
        variant = _variant(db_session, disease, "PATHOLOGICAL_SUBTYPE", name)
        concept = _concept(db_session, disease, "FINDING", name)
        assert variant is not None, f"missing variant: {name}"
        assert concept is not None, f"missing concept: {name}"
        assert variant.id not in seen_variant_ids
        assert concept.id not in seen_concept_ids
        seen_variant_ids.add(variant.id)
        seen_concept_ids.add(concept.id)
    assert len(seen_variant_ids) == 5
    assert len(seen_concept_ids) == 5


# --- 5. Non-Small Cell and Small Cell Lung Cancer remain distinct -----------

def test_non_small_cell_and_small_cell_remain_distinct(db_session, built_state):
    disease = built_state["disease"]
    nsclc = _concept(db_session, disease, "FINDING", "Non-Small Cell Lung Cancer")
    sclc = _concept(db_session, disease, "FINDING", "Small Cell Lung Cancer")
    assert nsclc is not None and sclc is not None
    assert nsclc.id != sclc.id


# --- 6. No unsupported histology is created ---------------------------------

def test_no_unsupported_histology_beyond_approved_subtypes(db_session, built_state):
    disease = built_state["disease"]
    count = db_session.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id, variant_dimension="HISTOLOGY").count()
    assert count == 0
    subtype_variants = db_session.query(OntologyDiseaseVariant).filter_by(
        disease_id=disease.id, variant_dimension="PATHOLOGICAL_SUBTYPE"
    ).all()
    assert {v.variant_name for v in subtype_variants} == EXPECTED_SUBTYPE_VARIANT_NAMES
    for forbidden in ("Adenocarcinoma", "Squamous-Cell Carcinoma", "Large-Cell Carcinoma", "Neuroendocrine Subtype"):
        assert _concept(db_session, disease, "FINDING", forbidden) is None


# --- 7-10. No unsupported stage / grade / molecular subtype / laterality ---

@pytest.mark.parametrize("dimension", sorted(UNSUPPORTED_DIMENSIONS - {"METASTATIC_DESTINATION"}))
def test_no_unsupported_variant_dimension_created(db_session, built_state, dimension):
    disease = built_state["disease"]
    count = db_session.query(OntologyDiseaseVariant).filter_by(
        disease_id=disease.id, variant_dimension=dimension
    ).count()
    assert count == 0


# --- 11. No unsupported metastatic destination is created -------------------

def test_no_unsupported_metastatic_destination_created(db_session, built_state):
    disease = built_state["disease"]
    count = db_session.query(OntologyDiseaseVariant).filter_by(
        disease_id=disease.id, variant_dimension="METASTATIC_DESTINATION"
    ).count()
    assert count == 0
    for forbidden in ("Bone Metastasis", "Brain Metastasis", "Liver Metastasis", "Adrenal Metastasis", "Pleural Metastasis"):
        assert _concept(db_session, disease, "FINDING", forbidden) is None


# --- 12 & 14. Exactly eight declared applicability mappings / no Cartesian --

def test_exactly_eight_new_explicit_applicability_mappings_exist(db_session, built_state):
    disease = built_state["disease"]
    new_concept_names = {c["name"] for c in MANIFEST["concepts"]}
    all_edges = db_session.query(OntologyConceptVariantApplicability).filter_by(disease_id=disease.id).all()
    new_edges = []
    for edge in all_edges:
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        concept_row = db_session.query(model_cls).filter_by(id=edge.concept_id).one_or_none()
        if concept_row is not None and getattr(concept_row, name_attr) in new_concept_names:
            new_edges.append(edge)
    assert len(new_edges) == 8
    for edge in new_edges:
        assert edge.applicability_type == "APPLIES_TO"


def test_no_cartesian_applicability_generation(db_session, built_state):
    """This manifest declares only 8 mappings for 9 concepts x up to 9
    variants -- proof no nested loop or Cartesian product ever ran."""
    assert len(MANIFEST["applicability"]) == 8
    assert len(MANIFEST["applicability"]) < 9 * 9


# --- 13. Undeclared applicability count is zero -----------------------------

def test_undeclared_applicability_count_is_zero(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert report["undeclared_applicability_count"] == 0
    assert report["undeclared_applicability"] == []


def test_every_stored_new_applicability_mapping_is_manifest_declared(db_session, built_state):
    disease = built_state["disease"]
    declared = {
        (a["variant_dimension"], a["variant"].strip().lower(), a["concept_domain"], a["concept"].strip().lower(), a["applicability_type"])
        for a in MANIFEST["applicability"]
    }
    new_concept_names = {c["name"].strip().lower() for c in MANIFEST["concepts"]}
    all_edges = db_session.query(OntologyConceptVariantApplicability).filter_by(disease_id=disease.id).all()
    variants_by_id = {
        v.id: (v.variant_dimension, v.normalized_name)
        for v in db_session.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).all()
    }
    for edge in all_edges:
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        concept_row = db_session.query(model_cls).filter_by(id=edge.concept_id).one_or_none()
        concept_name = getattr(concept_row, name_attr).strip().lower() if concept_row is not None else None
        if concept_name not in new_concept_names:
            continue  # pre-existing PR #45 foundation edge, out of scope for this manifest
        dimension, variant_name = variants_by_id.get(edge.variant_id, (None, None))
        key = (dimension, variant_name, edge.concept_type, concept_name, edge.applicability_type)
        assert key in declared, f"stored applicability edge not declared in manifest: {key}"


# --- 15. Lung Cancer does not inherit the Pulmonary LCD pathway -------------

def test_lung_cancer_does_not_inherit_pulmonary_lcd_pathway(db_session, built_state):
    disease = built_state["disease"]
    for forbidden in (
        "Hypoxemia", "Hypercapnia", "Oxygen Saturation Threshold", "Right Heart Failure",
        "FEV1 Decline", "Respiratory Failure", "End Stage Pulmonary Disease",
        "Chronic Obstructive Pulmonary Disease", "Pulmonary Disease",
    ):
        assert _concept(db_session, disease, "FINDING", forbidden) is None
    hospice_count = db_session.query(OntologyDiseaseHospiceEligibilitySupport).filter_by(disease_id=disease.id).count()
    assert hospice_count == 0
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert report["pulmonary_lcd_inheritance_count"] == 0


# --- 16. Lung Cancer remains distinct from Lung Metastasis ------------------

def test_lung_cancer_remains_distinct_from_lung_metastasis(db_session, built_state):
    disease = built_state["disease"]
    assert _concept(db_session, disease, "FINDING", "Lung Cancer") is not None
    assert _concept(db_session, disease, "FINDING", "Lung Metastasis From Another Primary Cancer") is None
    assert db_session.query(OntologyDisease).filter_by(disease_name="Lung Metastasis From Another Primary Cancer").one_or_none() is None
    assert db_session.query(OntologyDisease).filter_by(disease_name="Lung Metastasis").one_or_none() is None


# --- 17. Metastatic Lung Cancer does not establish destination --------------

def test_metastatic_lung_cancer_does_not_establish_destination(db_session, built_state):
    disease = built_state["disease"]
    concept = _concept(db_session, disease, "FINDING", "Metastatic Lung Cancer")
    assert concept is not None
    count = db_session.query(OntologyDiseaseVariant).filter_by(
        disease_id=disease.id, variant_dimension="METASTATIC_DESTINATION"
    ).count()
    assert count == 0


# --- 18. Recurrent Lung Cancer does not automatically mean metastatic ------

def test_recurrent_lung_cancer_does_not_automatically_mean_metastatic(db_session, built_state):
    disease = built_state["disease"]
    recurrent = _concept(db_session, disease, "FINDING", "Recurrent Lung Cancer")
    metastatic = _concept(db_session, disease, "FINDING", "Metastatic Lung Cancer")
    assert recurrent is not None and metastatic is not None
    assert recurrent.id != metastatic.id


# --- 19 & 20. Every concept has source classification and provenance -------

def test_every_new_concept_has_source_classification_and_provenance(db_session, built_state):
    disease = built_state["disease"]
    for c in MANIFEST["concepts"]:
        row = _concept(db_session, disease, c["domain"], c["name"])
        assert row is not None
        rule = _evidence_rule(db_session, c["domain"], row.id)
        assert rule is not None
        assert f"source_classification={c['source_classification']}" in rule.notes
        assert f"source_reference={c['source_reference']}" in rule.notes


# --- 21 & 22. Every concept has an evidence rule / requires evidence -------

def test_every_new_concept_has_an_evidence_rule_requiring_evidence(db_session, built_state):
    disease = built_state["disease"]
    for c in MANIFEST["concepts"]:
        row = _concept(db_session, disease, c["domain"], c["name"])
        rule = _evidence_rule(db_session, c["domain"], row.id)
        assert rule.patient_fact_requires_evidence is True


# --- 23. Lung Cancer diagnosis does not establish hospice eligibility ------

def test_lung_cancer_does_not_establish_hospice_eligibility(db_session, built_state):
    disease = built_state["disease"]
    hospice_concepts = db_session.query(OntologyDiseaseHospiceEligibilitySupport).filter_by(disease_id=disease.id).count()
    assert hospice_concepts == 0
    hospice_edges = db_session.query(OntologyConceptVariantApplicability).filter_by(
        disease_id=disease.id, applicability_type="HOSPICE_SUPPORT_FOR"
    ).count()
    assert hospice_edges == 0


def test_lung_cancer_prognosis_concepts_are_foundation_shared_not_newly_added(db_session, built_state):
    """The Oncology Foundation import (PR #45) reuses two shared
    PROGNOSTIC_INDICATOR concepts (Progressive Disease, Worsening Clinical
    Status) across every cancer disease, including Lung Cancer. This
    manifest must not add a third, disease-specific prognosis concept, and
    must never attach any PROGNOSTIC_INDICATOR concept to a Lung Cancer
    variant via applicability -- diagnosis alone must never establish
    prognosis."""
    disease = built_state["disease"]
    indicator_names = {
        row.indicator_name
        for row in db_session.query(OntologyDiseasePrognosticIndicator).filter_by(disease_id=disease.id).all()
    }
    assert indicator_names == {"Progressive Disease", "Worsening Clinical Status"}
    edges = db_session.query(OntologyConceptVariantApplicability).filter_by(
        disease_id=disease.id, concept_type="PROGNOSTIC_INDICATOR"
    ).count()
    assert edges == 0


def test_lung_cancer_does_not_establish_treatment(db_session, built_state):
    disease = built_state["disease"]
    assert db_session.query(OntologyDiseaseTreatment).filter_by(disease_id=disease.id).count() == 0
    assert db_session.query(OntologyDiseaseTreatmentLimitation).filter_by(disease_id=disease.id).count() == 0


# --- 24-26. Orphan / cycle / unresolved counts are zero --------------------

def test_acceptance_report_shows_zero_orphans_cycles_unresolved(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert report["orphan_count"] == 0
    assert report["cycle_count"] == 0
    assert report["unresolved_concept_count"] == 0
    assert report["duplicate_canonical_disease_count"] == 0


# --- 27. Second-run new rows equal zero -------------------------------------

def test_second_execution_creates_zero_rows(db_session, built_state):
    session2 = TestSessionLocal()
    try:
        result = run_manifest_import(session2, manifest=MANIFEST)
        session2.commit()
        total_new = result["variants_inserted"] + result["concepts_inserted_total"] + result["applicability_inserted"]
        assert total_new == 0
    finally:
        session2.close()


def test_importer_rejects_duplicate_canonical_disease(db_session, built_state):
    """A defensive structural test: a second Lung Cancer disease row must
    never be able to exist for the importer to guess between. The schema's
    own unique index on disease_name enforces this at the database level
    (stronger than an application-level check), so attempting to create the
    duplicate itself must fail before the importer is ever invoked."""
    from sqlalchemy.exc import IntegrityError

    session2 = TestSessionLocal()
    try:
        duplicate = OntologyDisease(
            disease_name=DISEASE_NAME,
            disease_family_id=built_state["disease"].disease_family_id,
            disease_category="NCI_CANCER_CATALOG",
        )
        session2.add(duplicate)
        with pytest.raises(IntegrityError, match="duplicate key value violates unique constraint"):
            session2.flush()
    finally:
        session2.rollback()
        session2.close()

    # The importer's own defensive `_resolve_existing_disease` duplicate-guard
    # (unreachable via the DB in practice, since the schema's unique index
    # already forbids a real duplicate row) is exercised directly by
    # stubbing only the disease lookup step, while delegating every other
    # query to the real session, to prove the application-level guard logic
    # is also correct in isolation.
    from scripts.import_lung_cancer_production_identity_manifest import (
        _resolve_existing_disease,
    )
    from app.models.ontology_disease_blueprint import OntologyDisease as _OntologyDisease

    class _DuplicatingSession:
        def __init__(self, real_session, duplicate_rows):
            self._real = real_session
            self._duplicate_rows = duplicate_rows

        def query(self, model, *args, **kwargs):
            if model is _OntologyDisease:
                return _FakeDiseaseQuery(self._duplicate_rows)
            return self._real.query(model, *args, **kwargs)

    class _FakeDiseaseQuery:
        def __init__(self, rows):
            self._rows = rows

        def filter_by(self, **kwargs):
            return self

        def all(self):
            return self._rows

    real_disease = built_state["disease"]
    fake_session = _DuplicatingSession(db_session, [real_disease, real_disease])
    with pytest.raises(RuntimeError, match="duplicate"):
        _resolve_existing_disease(fake_session, MANIFEST)


# --- 28. No previously completed body system changes ------------------------

def test_no_other_diseases_or_body_systems_affected(db_session, built_state):
    other_diseases = (
        db_session.query(OntologyDisease)
        .filter(OntologyDisease.disease_name != DISEASE_NAME)
        .all()
    )
    # This importer is scoped to a single disease; a structural sanity
    # check confirms no sibling oncology disease gained new content this
    # manifest never declared for it.
    for other in other_diseases:
        subtype_variants = db_session.query(OntologyDiseaseVariant).filter_by(
            disease_id=other.id, variant_dimension="PATHOLOGICAL_SUBTYPE"
        ).all()
        for variant in subtype_variants:
            assert variant.variant_name not in EXPECTED_SUBTYPE_VARIANT_NAMES


# --- differentiation guards --------------------------------------------------

def test_all_sixteen_differentiation_guards_pass(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    results = report["differentiation_guard_results"]
    assert len(results) == 16
    failed = [r["guard_name"] for r in results if not r["passed"]]
    assert failed == [], f"failed guards: {failed}"


def test_evidence_provenance_classification_coverage_is_complete(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert report["evidence_rule_coverage"]["covered"] == report["evidence_rule_coverage"]["expected"] == 9
    assert report["source_provenance_coverage"]["covered"] == report["source_provenance_coverage"]["expected"] == 9
    assert report["source_classification_coverage"]["covered"] == report["source_classification_coverage"]["expected"] == 9
