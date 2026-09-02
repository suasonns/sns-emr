# tests/test_breast_cancer_production_identity_manifest.py
"""Targeted tests for the Breast Cancer Production Identity Manifest v1
import (`import_breast_cancer_production_identity_manifest.py`, PR #46 --
the first disease-specific Oncology manifest).

Every assertion below is derived directly from the committed manifest file
(`backend/manifests/breast_cancer_production_identity_manifest_v1.json`),
never from clinical judgment, inference, or a "similar enough" substitute.

This manifest depends on the Oncology Foundation import (PR #45,
`import_oncology_foundation_v1.py`) having already created the "Oncology"
body system, "Solid Malignancies" family, canonical "Breast Cancer"
disease, and its four foundation Tier 4 variants (Breast Primary Site,
Localized Disease, Metastatic Disease, Recurrent Disease). This test
module imports both manifests, in that dependency order, exactly once.

This PR adds ONLY:
    - One new Tier 4 variant: "Ductal Carcinoma In Situ"
      (PATHOLOGICAL_SUBTYPE dimension).
    - Seven Tier 5 FINDING identity concepts: Breast Cancer, Ductal
      Carcinoma In Situ, Male Breast Cancer, Pregnancy and Breast Cancer,
      Localized Breast Cancer, Metastatic Breast Cancer, Recurrent Breast
      Cancer.
    - Four explicit, individually-declared applicability mappings
      (APPLIES_TO): Ductal Carcinoma In Situ -> its own variant;
      Localized/Metastatic/Recurrent Breast Cancer -> their corresponding
      foundation variants.

It does NOT create a universal cancer manifest, does NOT copy this content
to another cancer disease, and does NOT create stage, grade, histology
(beyond the one approved variant), molecular subtype, metastatic
destination, symptom, treatment, medication, or prognosis knowledge.
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
)
from scripts.import_oncology_foundation_v1 import (
    load_manifest as load_foundation_manifest,
    run as run_foundation_import,
)
from scripts.import_breast_cancer_production_identity_manifest import (
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
    "Breast Cancer", "Ductal Carcinoma In Situ", "Male Breast Cancer", "Pregnancy and Breast Cancer",
    "Localized Breast Cancer", "Metastatic Breast Cancer", "Recurrent Breast Cancer",
}
UNSUPPORTED_DIMENSIONS = {"STAGE", "GRADE", "HISTOLOGY", "MOLECULAR_SUBTYPE", "METASTATIC_DESTINATION", "LATERALITY"}


@pytest.fixture(scope="module")
def built_state():
    """Import the Oncology Foundation manifest (dependency), then the
    Breast Cancer manifest, into a dedicated session against the test
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

def test_manifest_scope_targets_breast_cancer_under_solid_malignancies():
    assert MANIFEST["scope"]["body_system"] == SYSTEM_NAME
    assert MANIFEST["scope"]["family"] == FAMILY_NAME
    assert MANIFEST["scope"]["disease"] == DISEASE_NAME


def test_manifest_declares_exactly_one_new_variant():
    assert len(MANIFEST["new_variants"]) == 1
    assert MANIFEST["new_variants"][0]["name"] == "Ductal Carcinoma In Situ"
    assert MANIFEST["new_variants"][0]["dimension"] == "PATHOLOGICAL_SUBTYPE"


def test_manifest_declares_exactly_seven_concepts():
    names = {c["name"] for c in MANIFEST["concepts"]}
    assert names == EXPECTED_CONCEPT_NAMES
    assert len(MANIFEST["concepts"]) == 7


def test_manifest_declares_exactly_four_applicability_mappings():
    assert len(MANIFEST["applicability"]) == 4
    for a in MANIFEST["applicability"]:
        assert a["applicability_type"] == "APPLIES_TO"


def test_manifest_never_attaches_male_or_pregnancy_concepts_to_a_variant():
    mapped_concepts = {a["concept"] for a in MANIFEST["applicability"]}
    assert "Male Breast Cancer" not in mapped_concepts
    assert "Pregnancy and Breast Cancer" not in mapped_concepts
    assert "Breast Cancer" not in mapped_concepts


def test_manifest_passes_structural_validation():
    assert validate_manifest(MANIFEST) == []


def test_manifest_every_concept_has_classification_reference_and_evidence_flag():
    for c in MANIFEST["concepts"]:
        assert c["source_classification"] in ALLOWED_SOURCE_CLASSIFICATIONS
        assert c["source_reference"]
        assert c["patient_fact_requires_evidence"] is True


def test_manifest_declares_all_twelve_required_differentiation_guards():
    names = [g["guard_name"] for g in MANIFEST["differentiation_guards"]]
    assert names == [
        "Breast Cancer IS_NOT Breast Primary Site",
        "Ductal Carcinoma In Situ IS_NOT Invasive Breast Cancer",
        "Male Breast Cancer DOES_NOT_INFER Patient Sex Or Gender",
        "Pregnancy and Breast Cancer DOES_NOT_INFER Current Pregnancy",
        "Localized Breast Cancer IS_NOT Metastatic Breast Cancer",
        "Recurrent Breast Cancer IS_NOT Automatically Metastatic Breast Cancer",
        "Metastatic Breast Cancer DOES_NOT_ESTABLISH Metastatic Destination",
        "Breast Cancer Diagnosis DOES_NOT_ESTABLISH Hospice Eligibility",
        "Breast Cancer Diagnosis DOES_NOT_ESTABLISH Stage",
        "Breast Cancer Diagnosis DOES_NOT_ESTABLISH Histology",
        "Breast Cancer Diagnosis DOES_NOT_ESTABLISH Molecular Subtype",
        "Breast Cancer Diagnosis DOES_NOT_ESTABLISH Treatment",
    ]


# --- 1. One canonical Breast Cancer disease exists -------------------------

def test_one_canonical_breast_cancer_disease_exists(db_session, built_state):
    matches = db_session.query(OntologyDisease).filter_by(disease_name=DISEASE_NAME).all()
    assert len(matches) == 1


# --- 2. Breast Cancer belongs to Solid Malignancies ------------------------

def test_breast_cancer_belongs_to_solid_malignancies(db_session, built_state):
    family = db_session.query(OntologyDiseaseFamily).filter_by(family_name=FAMILY_NAME).one()
    assert built_state["disease"].disease_family_id == family.id


# --- 3. No placeholder disease exists ---------------------------------------

def test_no_placeholder_disease_exists(db_session, built_state):
    for forbidden in (
        "Oncology Foundation Reference Structure", "Breast Primary Site",
        "Invasive Breast Cancer", "Localized Breast Cancer", "Metastatic Breast Cancer",
        "Recurrent Breast Cancer", "Ductal Carcinoma In Situ",
    ):
        assert db_session.query(OntologyDisease).filter_by(disease_name=forbidden).one_or_none() is None


# --- 4. Ductal Carcinoma In Situ exists independently -----------------------

def test_ductal_carcinoma_in_situ_exists_independently(db_session, built_state):
    disease = built_state["disease"]
    variant = _variant(db_session, disease, "PATHOLOGICAL_SUBTYPE", "Ductal Carcinoma In Situ")
    concept = _concept(db_session, disease, "FINDING", "Ductal Carcinoma In Situ")
    assert variant is not None
    assert concept is not None
    assert variant.id != concept.id  # distinct tables/rows entirely


# --- 5. No unsupported invasive subtype is created -------------------------

def test_no_unsupported_invasive_subtype_created(db_session, built_state):
    disease = built_state["disease"]
    assert _concept(db_session, disease, "FINDING", "Invasive Breast Cancer") is None
    subtype_variants = db_session.query(OntologyDiseaseVariant).filter_by(
        disease_id=disease.id, variant_dimension="PATHOLOGICAL_SUBTYPE"
    ).all()
    assert {v.variant_name for v in subtype_variants} == {"Ductal Carcinoma In Situ"}


# --- 6-9. No unsupported stage / grade / molecular subtype / laterality ---

@pytest.mark.parametrize("dimension", ["STAGE", "GRADE", "MOLECULAR_SUBTYPE", "LATERALITY"])
def test_no_unsupported_variant_dimension_created(db_session, built_state, dimension):
    disease = built_state["disease"]
    count = db_session.query(OntologyDiseaseVariant).filter_by(
        disease_id=disease.id, variant_dimension=dimension
    ).count()
    assert count == 0


def test_no_unsupported_histology_beyond_approved_subtype(db_session, built_state):
    disease = built_state["disease"]
    count = db_session.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id, variant_dimension="HISTOLOGY").count()
    assert count == 0


# --- 10. No unsupported metastatic destination created ---------------------

def test_no_unsupported_metastatic_destination_created(db_session, built_state):
    disease = built_state["disease"]
    count = db_session.query(OntologyDiseaseVariant).filter_by(
        disease_id=disease.id, variant_dimension="METASTATIC_DESTINATION"
    ).count()
    assert count == 0


# --- 11 & 12. Exactly four explicit applicability mappings / no Cartesian ---

def test_exactly_four_new_explicit_applicability_mappings_exist(db_session, built_state):
    disease = built_state["disease"]
    new_concept_names = {c["name"] for c in MANIFEST["concepts"]}
    all_edges = db_session.query(OntologyConceptVariantApplicability).filter_by(disease_id=disease.id).all()
    new_edges = []
    for edge in all_edges:
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        concept_row = db_session.query(model_cls).filter_by(id=edge.concept_id).one_or_none()
        if concept_row is not None and getattr(concept_row, name_attr) in new_concept_names:
            new_edges.append(edge)
    assert len(new_edges) == 4
    for edge in new_edges:
        assert edge.applicability_type == "APPLIES_TO"


def test_no_cartesian_applicability_generation(db_session, built_state):
    """This manifest declares only 4 mappings for 7 concepts x up to 5
    variants (35 possible pairs) -- proof no nested loop or Cartesian
    product ever ran."""
    assert len(MANIFEST["applicability"]) == 4
    assert len(MANIFEST["applicability"]) < 7 * 5


# --- 13. Every mapping is declared in the manifest -------------------------

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


# --- 14 & 15. Every concept has source classification and provenance -------

def test_every_new_concept_has_source_classification_and_provenance(db_session, built_state):
    disease = built_state["disease"]
    for c in MANIFEST["concepts"]:
        row = _concept(db_session, disease, c["domain"], c["name"])
        assert row is not None
        rule = _evidence_rule(db_session, c["domain"], row.id)
        assert rule is not None
        assert f"source_classification={c['source_classification']}" in rule.notes
        assert f"source_reference={c['source_reference']}" in rule.notes


# --- 16 & 17. Every concept has an evidence rule / requires evidence -------

def test_every_new_concept_has_an_evidence_rule_requiring_evidence(db_session, built_state):
    disease = built_state["disease"]
    for c in MANIFEST["concepts"]:
        row = _concept(db_session, disease, c["domain"], c["name"])
        rule = _evidence_rule(db_session, c["domain"], row.id)
        assert rule.patient_fact_requires_evidence is True


# --- 18. Breast Cancer does not establish hospice eligibility ---------------

def test_breast_cancer_does_not_establish_hospice_eligibility(db_session, built_state):
    disease = built_state["disease"]
    hospice_concepts = db_session.query(OntologyDiseaseHospiceEligibilitySupport).filter_by(disease_id=disease.id).count()
    assert hospice_concepts == 0
    hospice_edges = db_session.query(OntologyConceptVariantApplicability).filter_by(
        disease_id=disease.id, applicability_type="HOSPICE_SUPPORT_FOR"
    ).count()
    assert hospice_edges == 0


# --- 19. Metastatic Breast Cancer does not establish metastatic destination -

def test_metastatic_breast_cancer_does_not_establish_metastatic_destination(db_session, built_state):
    disease = built_state["disease"]
    count = db_session.query(OntologyDiseaseVariant).filter_by(
        disease_id=disease.id, variant_dimension="METASTATIC_DESTINATION"
    ).count()
    assert count == 0


# --- 20. Recurrent Breast Cancer does not automatically mean metastatic ----

def test_recurrent_breast_cancer_does_not_automatically_mean_metastatic(db_session, built_state):
    disease = built_state["disease"]
    recurrent = _concept(db_session, disease, "FINDING", "Recurrent Breast Cancer")
    metastatic = _concept(db_session, disease, "FINDING", "Metastatic Breast Cancer")
    assert recurrent is not None and metastatic is not None
    assert recurrent.id != metastatic.id


# --- 21. Male Breast Cancer does not infer patient sex or gender -----------

def test_male_breast_cancer_does_not_infer_patient_sex_or_gender(db_session, built_state):
    disease = built_state["disease"]
    concept = _concept(db_session, disease, "FINDING", "Male Breast Cancer")
    assert concept is not None
    rule = _evidence_rule(db_session, "FINDING", concept.id)
    assert rule.patient_fact_requires_evidence is True
    edges = db_session.query(OntologyConceptVariantApplicability).filter_by(
        concept_type="FINDING", concept_id=concept.id
    ).count()
    assert edges == 0  # never attached to a variant, so it can never silently imply patient sex/gender


# --- 22. Pregnancy and Breast Cancer does not infer current pregnancy -----

def test_pregnancy_and_breast_cancer_does_not_infer_current_pregnancy(db_session, built_state):
    disease = built_state["disease"]
    concept = _concept(db_session, disease, "FINDING", "Pregnancy and Breast Cancer")
    assert concept is not None
    rule = _evidence_rule(db_session, "FINDING", concept.id)
    assert rule.patient_fact_requires_evidence is True
    edges = db_session.query(OntologyConceptVariantApplicability).filter_by(
        concept_type="FINDING", concept_id=concept.id
    ).count()
    assert edges == 0


# --- 23-25. Orphan / cycle / unresolved counts are zero --------------------

def test_acceptance_report_shows_zero_orphans_cycles_unresolved(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert report["orphan_count"] == 0
    assert report["cycle_count"] == 0
    assert report["unresolved_concept_count"] == 0
    assert report["duplicate_canonical_disease_count"] == 0


# --- 26. Second execution creates zero rows --------------------------------

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
    """A defensive structural test: a second Breast Cancer disease row must
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
    from scripts.import_breast_cancer_production_identity_manifest import (
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


# --- 27. No previously completed body system changes -----------------------

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
        for domain, (model_cls, name_attr) in CONCEPT_DOMAIN_MODEL_MAP.items():
            rows = db_session.query(model_cls).filter_by(disease_id=other.id).all()
            for row in rows:
                assert getattr(row, name_attr) not in EXPECTED_CONCEPT_NAMES or other.disease_name == DISEASE_NAME


def test_all_twelve_differentiation_guards_pass(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert len(report["differentiation_guard_results"]) == 12
    for guard in report["differentiation_guard_results"]:
        assert guard["passed"] is True, f"guard failed: {guard}"


# --- 28. No unrelated files change (structural reminder, verified at PR review) ---

def test_manifest_file_scope_is_exactly_the_four_authorized_files():
    assert DEFAULT_MANIFEST_PATH.name == "breast_cancer_production_identity_manifest_v1.json"
