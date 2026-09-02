# tests/test_colorectal_rectal_cancer_production_identity_manifest.py
"""Targeted tests for the Colorectal and Rectal Cancer Production Identity
Manifest v1 import (`import_colorectal_rectal_cancer_production_identity_manifest.py`,
PR #48 -- a disease-specific Oncology manifest spanning TWO canonical
diseases).

Every assertion below is derived directly from the committed manifest file
(`backend/manifests/colorectal_rectal_cancer_production_identity_manifest_v1.json`),
never from clinical judgment, inference, or a "similar enough" substitute.

This manifest depends on the Oncology Foundation import (PR #45,
`import_oncology_foundation_v1.py`) having already created the "Oncology"
body system, "Solid Malignancies" family, the canonical "Colorectal Cancer"
disease, and its four foundation Tier 4 variants (Colorectal Primary Site,
Localized Disease, Metastatic Disease, Recurrent Disease). This test module
imports both manifests, in that dependency order, exactly once.

This PR adds ONLY:
    - One new canonical disease: Rectal Cancer.
    - Four new Tier 4 variants for Rectal Cancer (PRIMARY_SITE,
      METASTATIC_STATE x2, RECURRENCE_STATE) -- Rectal Cancer's own rows,
      never shared with or copied from Colorectal Cancer.
    - Nine Tier 5 FINDING identity concepts (5 Colorectal Cancer, 4 Rectal
      Cancer).
    - Seven explicit, individually-declared applicability mappings
      (APPLIES_TO).

It does NOT create a third "Colon Cancer" (or "Colon and Rectal Cancer")
canonical disease, does NOT treat Rectal Cancer as interchangeable with
Colorectal Cancer, does NOT infer that a Colorectal Cancer diagnosis is
Rectal Cancer (or vice versa), and does NOT create stage, grade, molecular
subtype, histology, laterality, metastatic-destination, symptom,
diagnostic, treatment, medication, or prognosis knowledge for either
disease.
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
from scripts.import_colorectal_rectal_cancer_production_identity_manifest import (
    ALLOWED_SOURCE_CLASSIFICATIONS,
    CONCEPT_DOMAIN_MODEL_MAP,
    DEFAULT_MANIFEST_PATH,
    EXISTING_DISEASE_NAME,
    NEW_DISEASE_NAME,
    ALL_DISEASE_NAMES,
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

EXPECTED_COLORECTAL_CONCEPT_NAMES = {
    "Colorectal Cancer", "Colon and Rectal Cancer", "Localized Colorectal Cancer",
    "Metastatic Colorectal Cancer", "Recurrent Colorectal Cancer",
}
EXPECTED_RECTAL_CONCEPT_NAMES = {
    "Rectal Cancer", "Localized Rectal Cancer", "Metastatic Rectal Cancer", "Recurrent Rectal Cancer",
}
EXPECTED_ALL_CONCEPT_NAMES = EXPECTED_COLORECTAL_CONCEPT_NAMES | EXPECTED_RECTAL_CONCEPT_NAMES
EXPECTED_NEW_RECTAL_VARIANT_KEYS = {
    ("PRIMARY_SITE", "Rectal Primary Site"),
    ("METASTATIC_STATE", "Localized Disease"),
    ("METASTATIC_STATE", "Metastatic Disease"),
    ("RECURRENCE_STATE", "Recurrent Disease"),
}
UNSUPPORTED_DIMENSIONS = {"STAGE", "GRADE", "MOLECULAR_SUBTYPE", "HISTOLOGY", "METASTATIC_DESTINATION"}

EXPECTED_DIFFERENTIATION_GUARD_NAMES = [
    "Colorectal Cancer IS_NOT Rectal Cancer",
    "Colorectal Cancer IS_NOT Colorectal Primary Site",
    "Rectal Cancer IS_NOT Rectal Primary Site",
    "Colon and Rectal Cancer DOES_NOT_CREATE Colon Cancer",
    "Colorectal Cancer DOES_NOT_INFER Rectal Cancer",
    "Rectal Cancer DOES_NOT_INFER Colon Cancer",
    "Localized Colorectal Cancer IS_NOT Metastatic Colorectal Cancer",
    "Recurrent Colorectal Cancer IS_NOT Automatically Metastatic Colorectal Cancer",
    "Localized Rectal Cancer IS_NOT Metastatic Rectal Cancer",
    "Recurrent Rectal Cancer IS_NOT Automatically Metastatic Rectal Cancer",
    "Metastatic Colorectal Cancer DOES_NOT_ESTABLISH Metastatic Destination",
    "Metastatic Rectal Cancer DOES_NOT_ESTABLISH Metastatic Destination",
    "Colorectal Cancer Diagnosis DOES_NOT_ESTABLISH Stage",
    "Rectal Cancer Diagnosis DOES_NOT_ESTABLISH Stage",
    "Colorectal Cancer Diagnosis DOES_NOT_ESTABLISH Histology",
    "Rectal Cancer Diagnosis DOES_NOT_ESTABLISH Histology",
    "Colorectal Cancer Diagnosis DOES_NOT_ESTABLISH Molecular Subtype",
    "Rectal Cancer Diagnosis DOES_NOT_ESTABLISH Molecular Subtype",
    "Cancer Diagnosis DOES_NOT_ESTABLISH Prognosis",
    "Cancer Diagnosis DOES_NOT_ESTABLISH Hospice Eligibility",
]


@pytest.fixture(scope="module")
def built_state():
    """Import the Oncology Foundation manifest (dependency), then the
    Colorectal/Rectal Cancer manifest, into a dedicated session against the
    test database, exactly once for this file (module-scoped -- ontology
    tables are not tenant-scoped and are never cleared between tests by the
    function-scoped db_session fixture)."""
    session = TestSessionLocal()
    try:
        run_foundation_import(session, manifest=FOUNDATION_MANIFEST)
        session.commit()
        counts = run_manifest_import(session, manifest=MANIFEST)
        session.commit()
        colorectal = session.query(OntologyDisease).filter_by(disease_name=EXISTING_DISEASE_NAME).one()
        rectal = session.query(OntologyDisease).filter_by(disease_name=NEW_DISEASE_NAME).one()
        yield {
            "colorectal": colorectal,
            "rectal": rectal,
            "diseases": {EXISTING_DISEASE_NAME: colorectal, NEW_DISEASE_NAME: rectal},
            "counts": counts,
            "session": session,
        }
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

def test_manifest_scope_targets_colorectal_and_rectal_cancer():
    assert MANIFEST["scope"]["body_system"] == SYSTEM_NAME
    assert MANIFEST["scope"]["family"] == FAMILY_NAME
    assert set(MANIFEST["scope"]["diseases"]) == set(ALL_DISEASE_NAMES)


def test_manifest_declares_exactly_four_new_rectal_variants():
    variants = MANIFEST["new_variants"][NEW_DISEASE_NAME]
    keys = {(v["dimension"], v["name"]) for v in variants}
    assert keys == EXPECTED_NEW_RECTAL_VARIANT_KEYS
    assert len(variants) == 4
    assert EXISTING_DISEASE_NAME not in MANIFEST["new_variants"]


def test_manifest_declares_exactly_nine_concepts():
    names_by_disease = {}
    for c in MANIFEST["concepts"]:
        names_by_disease.setdefault(c["disease"], set()).add(c["name"])
    assert names_by_disease[EXISTING_DISEASE_NAME] == EXPECTED_COLORECTAL_CONCEPT_NAMES
    assert names_by_disease[NEW_DISEASE_NAME] == EXPECTED_RECTAL_CONCEPT_NAMES
    assert len(MANIFEST["concepts"]) == 9


def test_manifest_declares_exactly_seven_applicability_mappings():
    assert len(MANIFEST["applicability"]) == 7
    for a in MANIFEST["applicability"]:
        assert a["applicability_type"] == "APPLIES_TO"
        assert a["disease"] in ALL_DISEASE_NAMES


def test_manifest_never_attaches_base_identity_concepts_to_a_variant():
    mapped_concepts = {(a["disease"], a["concept"]) for a in MANIFEST["applicability"]}
    assert (EXISTING_DISEASE_NAME, "Colorectal Cancer") not in mapped_concepts
    assert (NEW_DISEASE_NAME, "Rectal Cancer") not in mapped_concepts


def test_manifest_never_maps_applicability_across_diseases():
    """Every applicability entry's variant must belong to the SAME disease
    as its concept -- no Rectal Cancer concept is ever mapped to a
    Colorectal Cancer variant, or vice versa."""
    required_by_disease = {
        disease_name: {(v["dimension"], v["name"]) for v in variants}
        for disease_name, variants in MANIFEST.get("required_existing_variants", {}).items()
    }
    new_by_disease = {
        disease_name: {(v["dimension"], v["name"]) for v in variants}
        for disease_name, variants in MANIFEST.get("new_variants", {}).items()
    }
    for a in MANIFEST["applicability"]:
        disease_name = a["disease"]
        key = (a["variant_dimension"], a["variant"])
        available = required_by_disease.get(disease_name, set()) | new_by_disease.get(disease_name, set())
        assert key in available, f"applicability {a} references a variant not owned by {disease_name}"


def test_manifest_passes_structural_validation():
    assert validate_manifest(MANIFEST) == []


def test_manifest_every_concept_has_classification_reference_and_evidence_flag():
    for c in MANIFEST["concepts"]:
        assert c["source_classification"] in ALLOWED_SOURCE_CLASSIFICATIONS
        assert c["source_reference"]
        assert c["patient_fact_requires_evidence"] is True


def test_manifest_declares_all_twenty_required_differentiation_guards():
    names = [g["guard_name"] for g in MANIFEST["differentiation_guards"]]
    assert names == EXPECTED_DIFFERENTIATION_GUARD_NAMES


# --- 1. Exactly one canonical disease row exists, for both diseases --------

def test_one_canonical_colorectal_cancer_disease_exists(db_session, built_state):
    matches = db_session.query(OntologyDisease).filter_by(disease_name=EXISTING_DISEASE_NAME).all()
    assert len(matches) == 1


def test_one_canonical_rectal_cancer_disease_exists(db_session, built_state):
    matches = db_session.query(OntologyDisease).filter_by(disease_name=NEW_DISEASE_NAME).all()
    assert len(matches) == 1


# --- 2. Both diseases belong to Solid Malignancies --------------------------

def test_both_diseases_belong_to_solid_malignancies(db_session, built_state):
    family = db_session.query(OntologyDiseaseFamily).filter_by(family_name=FAMILY_NAME).one()
    assert built_state["colorectal"].disease_family_id == family.id
    assert built_state["rectal"].disease_family_id == family.id


# --- 3. Colorectal Cancer and Rectal Cancer are distinct diseases -----------

def test_colorectal_and_rectal_cancer_are_distinct(db_session, built_state):
    assert built_state["colorectal"].id != built_state["rectal"].id


# --- 4. No placeholder / third canonical disease exists ---------------------

def test_no_placeholder_or_third_disease_exists(db_session, built_state):
    for forbidden in (
        "Colon Cancer", "Colon and Rectal Cancer", "Colorectal Primary Site", "Rectal Primary Site",
        "Localized Colorectal Cancer", "Metastatic Colorectal Cancer", "Recurrent Colorectal Cancer",
        "Localized Rectal Cancer", "Metastatic Rectal Cancer", "Recurrent Rectal Cancer",
    ):
        assert db_session.query(OntologyDisease).filter_by(disease_name=forbidden).one_or_none() is None


# --- 5. Rectal Cancer's four new variants exist independently --------------

def test_rectal_cancer_four_new_variants_exist_independently(db_session, built_state):
    rectal = built_state["rectal"]
    seen_ids = set()
    for dimension, name in EXPECTED_NEW_RECTAL_VARIANT_KEYS:
        variant = _variant(db_session, rectal, dimension, name)
        assert variant is not None, f"missing Rectal Cancer variant: {dimension}/{name}"
        assert variant.id not in seen_ids
        seen_ids.add(variant.id)
    assert len(seen_ids) == 4


def test_rectal_variants_are_never_shared_with_colorectal(db_session, built_state):
    colorectal, rectal = built_state["colorectal"], built_state["rectal"]
    for dimension, name in EXPECTED_NEW_RECTAL_VARIANT_KEYS:
        rectal_variant = _variant(db_session, rectal, dimension, name)
        colorectal_variant = _variant(db_session, colorectal, dimension, name)
        assert rectal_variant is not None
        if colorectal_variant is not None:
            assert rectal_variant.id != colorectal_variant.id


# --- 6. Colorectal Cancer's pre-existing foundation variants are resolved,
# never re-created -------------------------------------------------------

def test_colorectal_cancer_foundation_variants_resolved_not_duplicated(db_session, built_state):
    colorectal = built_state["colorectal"]
    for dimension, name in (
        ("PRIMARY_SITE", "Colorectal Primary Site"),
        ("METASTATIC_STATE", "Localized Disease"),
        ("METASTATIC_STATE", "Metastatic Disease"),
        ("RECURRENCE_STATE", "Recurrent Disease"),
    ):
        matches = (
            db_session.query(OntologyDiseaseVariant)
            .filter_by(disease_id=colorectal.id, variant_dimension=dimension, normalized_name=name.strip().lower())
            .all()
        )
        assert len(matches) == 1, f"expected exactly one {dimension}/{name} variant for Colorectal Cancer"


# --- 7. All nine Tier 5 concepts exist, keyed to the correct disease -------

def test_all_nine_concepts_exist_for_the_correct_disease(db_session, built_state):
    for c in MANIFEST["concepts"]:
        disease = built_state["diseases"][c["disease"]]
        concept = _concept(db_session, disease, c["domain"], c["name"])
        assert concept is not None, f"missing concept {c['disease']}/{c['name']}"


def test_colon_and_rectal_cancer_concept_belongs_only_to_colorectal_cancer(db_session, built_state):
    colorectal, rectal = built_state["colorectal"], built_state["rectal"]
    assert _concept(db_session, colorectal, "FINDING", "Colon and Rectal Cancer") is not None
    assert _concept(db_session, rectal, "FINDING", "Colon and Rectal Cancer") is None


# --- 8. Localized/Metastatic/Recurrent concepts remain distinct, per disease

def test_localized_and_metastatic_remain_distinct_per_disease(db_session, built_state):
    for disease_name, localized_name, metastatic_name in (
        (EXISTING_DISEASE_NAME, "Localized Colorectal Cancer", "Metastatic Colorectal Cancer"),
        (NEW_DISEASE_NAME, "Localized Rectal Cancer", "Metastatic Rectal Cancer"),
    ):
        disease = built_state["diseases"][disease_name]
        localized = _concept(db_session, disease, "FINDING", localized_name)
        metastatic = _concept(db_session, disease, "FINDING", metastatic_name)
        assert localized is not None and metastatic is not None
        assert localized.id != metastatic.id


def test_recurrent_and_metastatic_remain_distinct_per_disease(db_session, built_state):
    for disease_name, recurrent_name, metastatic_name in (
        (EXISTING_DISEASE_NAME, "Recurrent Colorectal Cancer", "Metastatic Colorectal Cancer"),
        (NEW_DISEASE_NAME, "Recurrent Rectal Cancer", "Metastatic Rectal Cancer"),
    ):
        disease = built_state["diseases"][disease_name]
        recurrent = _concept(db_session, disease, "FINDING", recurrent_name)
        metastatic = _concept(db_session, disease, "FINDING", metastatic_name)
        assert recurrent is not None and metastatic is not None
        assert recurrent.id != metastatic.id


# --- 9. No unsupported variant dimensions are created for either disease ---

@pytest.mark.parametrize("dimension", sorted(UNSUPPORTED_DIMENSIONS))
def test_no_unsupported_variant_dimension_created(db_session, built_state, dimension):
    for disease in (built_state["colorectal"], built_state["rectal"]):
        count = db_session.query(OntologyDiseaseVariant).filter_by(
            disease_id=disease.id, variant_dimension=dimension
        ).count()
        assert count == 0, f"unsupported {dimension} variant found for {disease.disease_name}"


# --- 10. Exactly seven new explicit applicability mappings exist -----------

def test_exactly_seven_new_explicit_applicability_mappings_exist(db_session, built_state):
    expected = {
        (a["disease"], a["variant_dimension"], a["variant"], a["concept_domain"], a["concept"], a["applicability_type"])
        for a in MANIFEST["applicability"]
    }
    assert len(expected) == 7
    for disease_name, variant_dimension, variant_name, concept_domain, concept_name, applicability_type in expected:
        disease = built_state["diseases"][disease_name]
        variant = _variant(db_session, disease, variant_dimension, variant_name)
        concept = _concept(db_session, disease, concept_domain, concept_name)
        assert variant is not None and concept is not None
        edge = db_session.query(OntologyConceptVariantApplicability).filter_by(
            concept_type=concept_domain, concept_id=concept.id, variant_id=variant.id,
            applicability_type=applicability_type,
        ).one_or_none()
        assert edge is not None, f"missing applicability edge for {disease_name}/{concept_name}"


def test_no_cartesian_applicability_generation(db_session, built_state):
    """Total stored applicability count for both diseases must equal the
    manifest's 7 declared new edges plus exactly the 1 pre-existing
    Oncology Foundation edge for Colorectal Cancer -- never a
    variant x concept Cartesian product."""
    colorectal, rectal = built_state["colorectal"], built_state["rectal"]
    total = (
        db_session.query(OntologyConceptVariantApplicability).filter_by(disease_id=colorectal.id).count()
        + db_session.query(OntologyConceptVariantApplicability).filter_by(disease_id=rectal.id).count()
    )
    assert total == 8  # 7 new + 1 pre-existing foundation edge


def test_no_cross_disease_applicability_edges(db_session, built_state):
    """No Rectal Cancer concept is ever mapped to a Colorectal Cancer
    variant, and no Colorectal Cancer concept is ever mapped to a Rectal
    Cancer variant."""
    colorectal, rectal = built_state["colorectal"], built_state["rectal"]
    colorectal_variant_ids = {
        v.id for v in db_session.query(OntologyDiseaseVariant).filter_by(disease_id=colorectal.id).all()
    }
    rectal_variant_ids = {
        v.id for v in db_session.query(OntologyDiseaseVariant).filter_by(disease_id=rectal.id).all()
    }
    for concept_name in EXPECTED_RECTAL_CONCEPT_NAMES:
        concept = _concept(db_session, rectal, "FINDING", concept_name)
        if concept is None:
            continue
        edges = db_session.query(OntologyConceptVariantApplicability).filter_by(
            concept_type="FINDING", concept_id=concept.id
        ).all()
        for edge in edges:
            assert edge.variant_id not in colorectal_variant_ids
    for concept_name in EXPECTED_COLORECTAL_CONCEPT_NAMES:
        concept = _concept(db_session, colorectal, "FINDING", concept_name)
        if concept is None:
            continue
        edges = db_session.query(OntologyConceptVariantApplicability).filter_by(
            concept_type="FINDING", concept_id=concept.id
        ).all()
        for edge in edges:
            assert edge.variant_id not in rectal_variant_ids


# --- 11. Colorectal Cancer does not inherit a "Colon Cancer" pathway -------

def test_colon_and_rectal_cancer_never_creates_a_colon_cancer_disease(db_session, built_state):
    assert db_session.query(OntologyDisease).filter_by(disease_name="Colon Cancer").one_or_none() is None
    assert _concept(db_session, built_state["colorectal"], "FINDING", "Colon Cancer") is None
    assert _concept(db_session, built_state["rectal"], "FINDING", "Colon Cancer") is None


# --- 12. Metastatic findings do not establish a destination -----------------

def test_metastatic_findings_do_not_establish_destination(db_session, built_state):
    for disease in (built_state["colorectal"], built_state["rectal"]):
        count = db_session.query(OntologyDiseaseVariant).filter_by(
            disease_id=disease.id, variant_dimension="METASTATIC_DESTINATION"
        ).count()
        assert count == 0


# --- 13. Every new concept has source classification, provenance, evidence -

def test_every_new_concept_has_source_classification_and_provenance(db_session, built_state):
    for c in MANIFEST["concepts"]:
        disease = built_state["diseases"][c["disease"]]
        concept = _concept(db_session, disease, c["domain"], c["name"])
        assert concept is not None
        rule = _evidence_rule(db_session, c["domain"], concept.id)
        assert rule is not None
        assert rule.notes is not None
        assert f"source_classification={c['source_classification']}" in rule.notes
        assert f"source_reference={c['source_reference']}" in rule.notes


def test_every_new_concept_has_an_evidence_rule_requiring_evidence(db_session, built_state):
    for c in MANIFEST["concepts"]:
        disease = built_state["diseases"][c["disease"]]
        concept = _concept(db_session, disease, c["domain"], c["name"])
        assert concept is not None
        rule = _evidence_rule(db_session, c["domain"], concept.id)
        assert rule is not None
        assert rule.patient_fact_requires_evidence is True


# --- 14. Diagnosis alone never establishes hospice eligibility -------------

def test_neither_disease_establishes_hospice_eligibility(db_session, built_state):
    for disease in (built_state["colorectal"], built_state["rectal"]):
        count = db_session.query(OntologyDiseaseHospiceEligibilitySupport).filter_by(disease_id=disease.id).count()
        assert count == 0
        applic_count = db_session.query(OntologyConceptVariantApplicability).filter_by(
            disease_id=disease.id, applicability_type="HOSPICE_SUPPORT_FOR"
        ).count()
        assert applic_count == 0


# --- 15. Prognosis concepts remain foundation-shared, never newly added ---

def test_prognosis_concepts_are_foundation_shared_not_newly_added(db_session, built_state):
    colorectal, rectal = built_state["colorectal"], built_state["rectal"]
    colorectal_prognostic = {
        p.indicator_name.strip().lower()
        for p in db_session.query(OntologyDiseasePrognosticIndicator).filter_by(disease_id=colorectal.id).all()
    }
    rectal_prognostic = {
        p.indicator_name.strip().lower()
        for p in db_session.query(OntologyDiseasePrognosticIndicator).filter_by(disease_id=rectal.id).all()
    }
    assert colorectal_prognostic == {"progressive disease", "worsening clinical status"}
    assert rectal_prognostic == set()

    for disease in (colorectal, rectal):
        applic_count = db_session.query(OntologyConceptVariantApplicability).filter_by(
            disease_id=disease.id, concept_type="PROGNOSTIC_INDICATOR"
        ).count()
        assert applic_count == 0


# --- 16. Diagnosis alone never establishes treatment ------------------------

def test_neither_disease_establishes_treatment(db_session, built_state):
    for disease in (built_state["colorectal"], built_state["rectal"]):
        assert db_session.query(OntologyDiseaseTreatment).filter_by(disease_id=disease.id).count() == 0
        assert db_session.query(OntologyDiseaseTreatmentLimitation).filter_by(disease_id=disease.id).count() == 0


# --- 17. Acceptance report shows zero orphans/cycles/unresolved/duplicates -

def test_acceptance_report_shows_zero_orphans_cycles_unresolved(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert report["orphan_count"] == 0
    assert report["cycle_count"] == 0
    assert report["unresolved_concept_count"] == 0
    assert report["duplicate_canonical_disease_count"] == 0
    assert report["colon_cancer_canonical_disease_count"] == 0


# --- 18. Second execution creates zero rows --------------------------------

def test_second_execution_creates_zero_rows(db_session, built_state):
    session2 = TestSessionLocal()
    try:
        result = run_manifest_import(session2, manifest=MANIFEST)
        session2.commit()
        total_new = result["variants_inserted"] + result["concepts_inserted_total"] + result["applicability_inserted"]
        assert total_new == 0
    finally:
        session2.close()


# --- 19. Importer rejects an ambiguous / duplicate canonical disease -------

def test_importer_rejects_duplicate_rectal_cancer_disease(db_session, built_state):
    """A defensive structural test: a second Rectal Cancer disease row must
    never be able to exist for the importer to guess between. The schema's
    own unique index on disease_name enforces this at the database level
    (stronger than an application-level check), so attempting to create the
    duplicate itself must fail before the importer is ever invoked."""
    from sqlalchemy.exc import IntegrityError

    session2 = TestSessionLocal()
    try:
        duplicate = OntologyDisease(
            disease_name=NEW_DISEASE_NAME,
            disease_family_id=built_state["rectal"].disease_family_id,
            disease_category="NCI_CANCER_CATALOG",
        )
        session2.add(duplicate)
        with pytest.raises(IntegrityError, match="duplicate key value violates unique constraint"):
            session2.flush()
    finally:
        session2.rollback()
        session2.close()

    # The importer's own defensive duplicate-guard (unreachable via the DB
    # in practice, since the schema's unique index already forbids a real
    # duplicate row) is exercised directly by stubbing only the disease
    # lookup step, while delegating every other query to the real session,
    # to prove the application-level guard logic is also correct in
    # isolation.
    from scripts.import_colorectal_rectal_cancer_production_identity_manifest import (
        _resolve_or_create_new_disease,
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

    real_rectal = built_state["rectal"]
    fake_session = _DuplicatingSession(db_session, [real_rectal, real_rectal])
    family = db_session.query(OntologyDiseaseFamily).filter_by(family_name=FAMILY_NAME).one()
    with pytest.raises(RuntimeError, match="duplicate"):
        _resolve_or_create_new_disease(fake_session, MANIFEST, family)


# --- 20. No sibling oncology disease is affected ----------------------------

def test_no_other_diseases_or_body_systems_affected(db_session, built_state):
    other_diseases = (
        db_session.query(OntologyDisease)
        .filter(OntologyDisease.disease_name.notin_(ALL_DISEASE_NAMES))
        .all()
    )
    for other in other_diseases:
        for dimension, name in EXPECTED_NEW_RECTAL_VARIANT_KEYS:
            variant = _variant(db_session, other, dimension, name)
            if variant is not None:
                # Shared dimension/name pairs (e.g. Localized Disease) may
                # legitimately exist on other cancer diseases from the
                # Oncology Foundation import -- but Rectal Cancer's own
                # PRIMARY_SITE variant name must never leak onto a sibling.
                if dimension == "PRIMARY_SITE":
                    pytest.fail(f"Rectal Cancer's PRIMARY_SITE variant leaked onto {other.disease_name}")


# --- differentiation guards --------------------------------------------------

def test_all_twenty_differentiation_guards_pass(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    results = report["differentiation_guard_results"]
    assert len(results) == 20
    failed = [r["guard_name"] for r in results if not r["passed"]]
    assert failed == [], f"failed guards: {failed}"


def test_evidence_provenance_classification_coverage_is_complete(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert report["evidence_rule_coverage"]["covered"] == report["evidence_rule_coverage"]["expected"] == 9
    assert report["source_provenance_coverage"]["covered"] == report["source_provenance_coverage"]["expected"] == 9
    assert report["source_classification_coverage"]["covered"] == report["source_classification_coverage"]["expected"] == 9


def test_acceptance_report_counts_match_manifest_summary(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    summary = MANIFEST["summary"]
    assert report["expected_new_variants_count"] == summary["new_variants_count"] == 4
    assert report["stored_new_variants_count"] == 4
    assert report["expected_concepts_count"] == summary["concepts_count"] == 9
    assert report["expected_applicability_count"] == summary["applicability_count"] == 7
    assert len(report["differentiation_guard_results"]) == summary["differentiation_guards_count"] == 20
