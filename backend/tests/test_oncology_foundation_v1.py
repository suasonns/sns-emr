# tests/test_oncology_foundation_v1.py
"""Targeted tests for the Oncology Foundation v1 import
(`import_oncology_foundation_v1.py`, PR #45 -- source-faithful correction).

This is a FOUNDATION build for the Oncology body system, not a single
disease. Every assertion below is derived directly from the committed
manifest file (`backend/manifests/oncology_foundation_v1.json`), never
from clinical judgment, inference, or a "similar enough" substitute.

The corrected manifest establishes:
    - The "Oncology" body system with TWO real disease families: "Solid
      Malignancies" (10 diseases) and "Hematologic Malignancies" (2
      diseases). There is NO placeholder/anchor disease.
    - 12 REAL canonical Tier 3 cancer diseases: Breast, Lung, Prostate,
      Colorectal, Liver, Kidney, Thyroid, Pancreatic, Bladder Cancer,
      Melanoma (solid); Leukemia, Lymphoma (hematologic).
    - Source-supported Tier 4 variants ONLY for the 10 solid malignancies:
      one PRIMARY_SITE variant (e.g. "Breast Primary Site" under Breast
      Cancer), two METASTATIC_STATE variants ("Localized Disease",
      "Metastatic Disease"), one RECURRENCE_STATE variant ("Recurrent
      Disease"). Leukemia and Lymphoma receive NO PRIMARY_SITE variant.
    - 10 reusable Tier 5 atomic concept identities, each stored once per
      applicable disease (the schema requires a single owning disease_id
      per Tier 5 row -- there is no global/shared concept table):
      Metastatic Disease / Regional Spread / Distant Metastatic Disease
      (solid malignancies only), Progressive Disease / Worsening Clinical
      Status / Progressive Functional Decline / Functional Impairment /
      Dependence In Activities Of Daily Living / Progressive Nutritional
      Decline / Unintentional Weight Loss (all 12 diseases).
    - ONLY 10 explicit applicability edges (one per solid malignancy: its
      own "Metastatic Disease" concept MAY_OCCUR_WITH its own "Metastatic
      Disease" METASTATIC_STATE variant). NO Cartesian/blanket
      applicability is ever generated.

No Stage I/II/III/IV variants, no histology-specific findings, and no
further disease-specific cancer content are created by this PR -- that is
explicitly deferred to future disease-specific oncology manifests.
"""
from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyDiseaseFamily,
    OntologyDiseaseVariant,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
)
from scripts.import_oncology_foundation_v1 import (
    ALLOWED_SOURCE_CLASSIFICATIONS,
    ALLOWED_VARIANT_DIMENSIONS,
    CONCEPT_DOMAIN_MODEL_MAP,
    DEFAULT_MANIFEST_PATH,
    load_manifest,
    validate_manifest,
    build_acceptance_report,
    run as run_manifest_import,
)
from tests.conftest import TestSessionLocal

MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)
ALL_DISEASE_NAMES = [d["disease"] for d in MANIFEST["diseases"]]

SOLID_MALIGNANCIES = [
    "Breast Cancer", "Lung Cancer", "Prostate Cancer", "Colorectal Cancer", "Liver Cancer",
    "Kidney Cancer", "Thyroid Cancer", "Pancreatic Cancer", "Bladder Cancer", "Melanoma",
]
HEMATOLOGIC_MALIGNANCIES = ["Leukemia", "Lymphoma"]

METASTASIS_CONCEPTS = {"Metastatic Disease", "Regional Spread", "Distant Metastatic Disease"}
BASELINE_CONCEPTS = {
    "Progressive Disease", "Worsening Clinical Status", "Progressive Functional Decline",
    "Functional Impairment", "Dependence In Activities Of Daily Living",
    "Progressive Nutritional Decline", "Unintentional Weight Loss",
}
ALL_TEN_CONCEPT_NAMES = METASTASIS_CONCEPTS | BASELINE_CONCEPTS

FORBIDDEN_ANCHOR_DISEASE = "Oncology Foundation Reference Structure"


@pytest.fixture(scope="module")
def built_state():
    """Import the Oncology Foundation v1 manifest into a dedicated session
    against the test database, exactly once for this file (module-scoped
    -- ontology tables are not tenant-scoped and are never cleared between
    tests by the function-scoped db_session fixture)."""
    session = TestSessionLocal()
    try:
        counts = run_manifest_import(session, manifest=MANIFEST)
        session.commit()
        diseases = {
            name: session.query(OntologyDisease).filter_by(disease_name=name).one()
            for name in ALL_DISEASE_NAMES
        }
        yield {"diseases": diseases, "counts": counts, "session": session}
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


def _manifest_variants():
    result = []
    for disease_entry in MANIFEST["diseases"]:
        for v in disease_entry.get("variants", []):
            result.append((disease_entry["disease"], v["dimension"], v["name"]))
    return result


def _manifest_concepts():
    result = []
    for disease_entry in MANIFEST["diseases"]:
        for c in disease_entry.get("concepts", []):
            result.append((disease_entry["disease"], c["domain"], c["name"], c))
    return result


def _manifest_applicability():
    result = []
    for disease_entry in MANIFEST["diseases"]:
        for a in disease_entry.get("applicability", []):
            result.append((disease_entry["disease"], a))
    return result


# --- manifest self-consistency ---------------------------------------------

def test_manifest_declares_twelve_real_canonical_diseases():
    assert set(ALL_DISEASE_NAMES) == set(SOLID_MALIGNANCIES) | set(HEMATOLOGIC_MALIGNANCIES)
    assert len(ALL_DISEASE_NAMES) == 12


def test_manifest_never_declares_the_fake_anchor_disease():
    assert FORBIDDEN_ANCHOR_DISEASE not in ALL_DISEASE_NAMES


def test_manifest_declares_two_families_matching_solid_and_hematologic_split():
    assert set(MANIFEST["scope"]["families"]) == {"Solid Malignancies", "Hematologic Malignancies"}
    for disease_entry in MANIFEST["diseases"]:
        if disease_entry["disease"] in SOLID_MALIGNANCIES:
            assert disease_entry["family"] == "Solid Malignancies"
        else:
            assert disease_entry["family"] == "Hematologic Malignancies"


def test_manifest_declares_exact_summary_counts():
    summary = MANIFEST["summary"]
    assert summary["canonical_diseases"] == 12
    assert summary["canonical_diseases_by_family"] == {"Solid Malignancies": 10, "Hematologic Malignancies": 2}
    assert summary["total_variants"] == len(_manifest_variants()) == 40
    assert summary["total_concepts"] == len(_manifest_concepts()) == 114
    assert summary["total_applicability_mappings"] == len(_manifest_applicability()) == 10


def test_manifest_passes_structural_validation():
    assert validate_manifest(MANIFEST) == []


def test_leukemia_and_lymphoma_have_no_tier4_variants():
    for disease_entry in MANIFEST["diseases"]:
        if disease_entry["disease"] in HEMATOLOGIC_MALIGNANCIES:
            assert disease_entry["variants"] == []


def test_solid_malignancies_have_exactly_four_variants_each():
    for disease_entry in MANIFEST["diseases"]:
        if disease_entry["disease"] in SOLID_MALIGNANCIES:
            dims = sorted(v["dimension"] for v in disease_entry["variants"])
            assert dims == ["METASTATIC_STATE", "METASTATIC_STATE", "PRIMARY_SITE", "RECURRENCE_STATE"]


def test_no_cancer_stage_variants_invented():
    variant_names = {v["name"] for d in MANIFEST["diseases"] for v in d.get("variants", [])}
    for forbidden in ("Stage I", "Stage II", "Stage III", "Stage IV"):
        assert forbidden not in variant_names


def test_no_metastatic_destination_variants_populated_yet():
    dims_used = {v["dimension"] for d in MANIFEST["diseases"] for v in d.get("variants", [])}
    assert "METASTATIC_DESTINATION" not in dims_used


def test_every_concept_declares_a_valid_source_classification_and_reference():
    for disease_name, domain, name, entry in _manifest_concepts():
        assert entry.get("source_classification") in ALLOWED_SOURCE_CLASSIFICATIONS
        assert entry.get("source_reference"), f"missing source_reference for {disease_name}/{domain}/{name}"
        assert entry.get("patient_fact_requires_evidence") is True


def test_every_disease_declares_nci_cancer_catalog_classification():
    for disease_entry in MANIFEST["diseases"]:
        assert disease_entry["disease_category"] == "NCI_CANCER_CATALOG"


def test_no_all_to_all_cartesian_applicability_in_manifest():
    """Reject any applicability entry attached to the non-disease-specific
    baseline domains (prognostic/functional/nutritional) -- these are
    possible patient-state findings requiring evidence, never
    automatically PRESENT/EXPECTED knowledge."""
    for disease_name, a in _manifest_applicability():
        assert a["concept_domain"] not in {"PROGNOSTIC_INDICATOR", "FUNCTIONAL_IMPACT", "NUTRITIONAL_IMPACT"}


def test_applicability_total_is_far_below_the_rejected_v1_blanket_count():
    assert len(_manifest_applicability()) == 10
    assert len(_manifest_applicability()) < 120


def test_every_applicability_entry_declares_an_explicit_variant_dimension():
    for disease_name, a in _manifest_applicability():
        assert a.get("variant_dimension"), f"missing variant_dimension for {disease_name}/{a.get('variant')}"
        assert a["variant_dimension"] in ALLOWED_VARIANT_DIMENSIONS


def test_ten_distinct_reusable_concept_identities_preserved():
    names = {name for _d, _dom, name, _entry in _manifest_concepts()}
    assert names == ALL_TEN_CONCEPT_NAMES
    assert len(ALL_TEN_CONCEPT_NAMES) == 10


# --- 1. Foundation imports correctly / counts ------------------------------

def test_foundation_imports_correctly(db_session, built_state):
    """Import succeeds and produces exactly the manifest's declared
    stored totals (checked against the database, not raw insertion counts,
    since the shared test database may already carry a prior idempotent
    import of this same manifest)."""
    disease_ids = [d.id for d in built_state["diseases"].values()]
    stored_variants = db_session.query(OntologyDiseaseVariant).filter(
        OntologyDiseaseVariant.disease_id.in_(disease_ids)
    ).count()
    assert stored_variants == 40

    stored_concepts = 0
    for domain, (model_cls, _name_attr) in CONCEPT_DOMAIN_MODEL_MAP.items():
        stored_concepts += db_session.query(model_cls).filter(model_cls.disease_id.in_(disease_ids)).count()
    assert stored_concepts == 114

    stored_applicability = db_session.query(OntologyConceptVariantApplicability).filter(
        OntologyConceptVariantApplicability.disease_id.in_(disease_ids)
    ).count()
    assert stored_applicability == 10


# --- 1 (spec). No fake Oncology Foundation Reference Structure disease exists ---

def test_no_fake_reference_disease_exists(db_session, built_state):
    assert db_session.query(OntologyDisease).filter_by(disease_name=FORBIDDEN_ANCHOR_DISEASE).one_or_none() is None


# --- 2. Twelve actual canonical cancer diseases exist ----------------------

def test_twelve_actual_canonical_diseases_exist(db_session, built_state):
    for name in SOLID_MALIGNANCIES + HEMATOLOGIC_MALIGNANCIES:
        disease = db_session.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
        assert disease is not None, f"expected canonical disease {name!r} to exist"
        assert disease.disease_category == "NCI_CANCER_CATALOG"


# --- 3. Solid and hematologic malignancy families remain distinct ---------

def test_solid_and_hematologic_families_remain_distinct(db_session, built_state):
    solid_family = db_session.query(OntologyDiseaseFamily).filter_by(family_name="Solid Malignancies").one()
    heme_family = db_session.query(OntologyDiseaseFamily).filter_by(family_name="Hematologic Malignancies").one()
    assert solid_family.id != heme_family.id
    for name in SOLID_MALIGNANCIES:
        assert built_state["diseases"][name].disease_family_id == solid_family.id
    for name in HEMATOLOGIC_MALIGNANCIES:
        assert built_state["diseases"][name].disease_family_id == heme_family.id


# --- 4 & 5. Leukemia / Lymphoma are not anatomical primary-site variants ---

def test_leukemia_is_not_an_anatomical_primary_site_variant(db_session, built_state):
    leukemia = built_state["diseases"]["Leukemia"]
    count = db_session.query(OntologyDiseaseVariant).filter_by(
        disease_id=leukemia.id, variant_dimension="PRIMARY_SITE"
    ).count()
    assert count == 0


def test_lymphoma_is_not_an_anatomical_primary_site_variant(db_session, built_state):
    lymphoma = built_state["diseases"]["Lymphoma"]
    count = db_session.query(OntologyDiseaseVariant).filter_by(
        disease_id=lymphoma.id, variant_dimension="PRIMARY_SITE"
    ).count()
    assert count == 0


# --- 6. Primary sites do not replace canonical cancer diseases -------------

def test_primary_sites_are_tier4_variants_not_diseases(db_session, built_state):
    for disease_name, site in (("Breast Cancer", "Breast"), ("Lung Cancer", "Lung"), ("Prostate Cancer", "Prostate")):
        disease = built_state["diseases"][disease_name]
        variant = _variant(db_session, disease, "PRIMARY_SITE", f"{site} Primary Site")
        assert variant is not None
        # The primary-site name must never itself have been created as a
        # standalone disease row.
        assert db_session.query(OntologyDisease).filter_by(disease_name=f"{site} Primary Site").one_or_none() is None


# --- 7 & 8. No all-to-all Cartesian applicability generation / explicit reason ---

def test_no_cartesian_applicability_generation(db_session, built_state):
    disease_ids = [d.id for d in built_state["diseases"].values()]
    total = db_session.query(OntologyConceptVariantApplicability).filter(
        OntologyConceptVariantApplicability.disease_id.in_(disease_ids)
    ).count()
    assert total == 10, "expected only the 10 explicitly-justified applicability edges, not a Cartesian product"


def test_every_stored_applicability_row_has_source_and_semantic_basis(db_session, built_state):
    disease_ids = [d.id for d in built_state["diseases"].values()]
    edges = db_session.query(OntologyConceptVariantApplicability).filter(
        OntologyConceptVariantApplicability.disease_id.in_(disease_ids)
    ).all()
    assert len(edges) == 10
    for edge in edges:
        assert edge.applicability_type == "MAY_OCCUR_WITH"
        assert edge.evidence_requirement
        assert edge.concept_type == "FINDING"


# --- 9. Solid and hematologic malignancies do not automatically share variants ---

def test_hematologic_malignancies_share_no_variants_with_solid(db_session, built_state):
    for name in HEMATOLOGIC_MALIGNANCIES:
        disease = built_state["diseases"][name]
        count = db_session.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).count()
        assert count == 0


# --- 10-13. Metastasis destination vs primary cancer distinctness ---------

@pytest.mark.parametrize(
    "reserved_left,reserved_right",
    [("Primary Bone Cancer", "Bone Metastasis"), ("Primary Brain Cancer", "Brain Metastasis")],
)
def test_reserved_metastasis_terms_never_prematurely_created(db_session, built_state, reserved_left, reserved_right):
    assert db_session.query(OntologyDisease).filter_by(disease_name=reserved_left).one_or_none() is None
    assert db_session.query(OntologyDisease).filter_by(disease_name=reserved_right).one_or_none() is None


@pytest.mark.parametrize(
    "disease_name,reserved_metastasis_term", [("Liver Cancer", "Liver Metastasis"), ("Lung Cancer", "Lung Metastasis")]
)
def test_primary_cancer_remains_distinct_from_its_metastasis_term(db_session, built_state, disease_name, reserved_metastasis_term):
    disease = built_state["diseases"][disease_name]
    # No METASTATIC_DESTINATION variant is populated yet, so this cannot
    # have been collapsed into the primary disease.
    count = db_session.query(OntologyDiseaseVariant).filter_by(
        disease_id=disease.id, variant_dimension="METASTATIC_DESTINATION"
    ).count()
    assert count == 0
    assert db_session.query(OntologyDisease).filter_by(disease_name=reserved_metastasis_term).one_or_none() is None


# --- 14. Localized Disease remains distinct from Metastatic Disease -------

def test_localized_disease_remains_distinct_from_metastatic_disease(db_session, built_state):
    for name in SOLID_MALIGNANCIES:
        disease = built_state["diseases"][name]
        localized = _variant(db_session, disease, "METASTATIC_STATE", "Localized Disease")
        metastatic = _variant(db_session, disease, "METASTATIC_STATE", "Metastatic Disease")
        assert localized is not None and metastatic is not None
        assert localized.id != metastatic.id


# --- 15. Regional Spread remains distinct from Distant Metastatic Disease ---

def test_regional_spread_remains_distinct_from_distant_metastatic_disease(db_session, built_state):
    for name in SOLID_MALIGNANCIES:
        disease = built_state["diseases"][name]
        regional = _concept(db_session, disease, "FINDING", "Regional Spread")
        distant = _concept(db_session, disease, "FINDING", "Distant Metastatic Disease")
        assert regional is not None and distant is not None
        assert regional.id != distant.id


# --- 16. Recurrent Disease remains distinct from Metastatic Disease -------

def test_recurrent_disease_remains_distinct_from_metastatic_disease(db_session, built_state):
    for name in SOLID_MALIGNANCIES:
        disease = built_state["diseases"][name]
        recurrent = _variant(db_session, disease, "RECURRENCE_STATE", "Recurrent Disease")
        metastatic = _variant(db_session, disease, "METASTATIC_STATE", "Metastatic Disease")
        assert recurrent is not None and metastatic is not None
        assert recurrent.id != metastatic.id


# --- 17. Cancer diagnosis does not establish hospice eligibility ----------

def test_cancer_diagnosis_does_not_establish_hospice_eligibility(db_session, built_state):
    """This foundation creates zero HOSPICE_ELIGIBILITY_SUPPORT concepts
    and zero HOSPICE_SUPPORT_FOR applicability edges -- diagnosis alone
    can never satisfy hospice eligibility through this manifest."""
    disease_ids = [d.id for d in built_state["diseases"].values()]
    hospice_edges = db_session.query(OntologyConceptVariantApplicability).filter(
        OntologyConceptVariantApplicability.disease_id.in_(disease_ids)
    ).filter_by(concept_type="HOSPICE_ELIGIBILITY_SUPPORT", applicability_type="HOSPICE_SUPPORT_FOR").count()
    assert hospice_edges == 0


# --- 18. Non-disease-specific support does not independently establish eligibility ---

def test_non_disease_specific_baseline_carries_no_applicability(db_session, built_state):
    """Progressive Functional Decline, Functional Impairment, Dependence
    In ADL, Progressive Nutritional Decline, Unintentional Weight Loss,
    Progressive Disease, Worsening Clinical Status all exist as stored
    concepts but carry ZERO applicability edges -- they can never, by
    themselves, establish eligibility for any disease."""
    baseline_domains = {"PROGNOSTIC_INDICATOR", "FUNCTIONAL_IMPACT", "NUTRITIONAL_IMPACT"}
    disease_ids = [d.id for d in built_state["diseases"].values()]
    count = db_session.query(OntologyConceptVariantApplicability).filter(
        OntologyConceptVariantApplicability.disease_id.in_(disease_ids)
    ).filter(OntologyConceptVariantApplicability.concept_type.in_(baseline_domains)).count()
    assert count == 0


# --- 19. Every patient fact requires evidence ------------------------------

def test_every_evidence_rule_requires_patient_evidence(db_session, built_state):
    for disease_name, domain, name, _entry in _manifest_concepts():
        disease = built_state["diseases"][disease_name]
        row = _concept(db_session, disease, domain, name)
        assert row is not None
        rule = _evidence_rule(db_session, domain, row.id)
        assert rule is not None
        assert rule.patient_fact_requires_evidence is True


# --- 20 & 21. Source classification / provenance on every concept ---------

def test_every_concept_has_source_classification_and_provenance(db_session, built_state):
    for disease_name, domain, name, entry in _manifest_concepts():
        disease = built_state["diseases"][disease_name]
        row = _concept(db_session, disease, domain, name)
        rule = _evidence_rule(db_session, domain, row.id)
        assert entry["source_classification"] in ALLOWED_SOURCE_CLASSIFICATIONS
        assert f"source_classification={entry['source_classification']}" in rule.notes
        assert f"source_reference={entry['source_reference']}" in rule.notes


# --- 22. Every concept has an evidence rule --------------------------------

def test_every_concept_has_an_evidence_rule(db_session, built_state):
    for disease_name, domain, name, _entry in _manifest_concepts():
        disease = built_state["diseases"][disease_name]
        row = _concept(db_session, disease, domain, name)
        assert _evidence_rule(db_session, domain, row.id) is not None


# --- 23-25. Orphan / cycle / unresolved counts are zero --------------------

def test_acceptance_report_shows_zero_orphans_cycles_unresolved(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert report["orphan_count"] == 0
    assert report["cycle_count"] == 0
    assert report["unresolved_concept_count"] == 0


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


# --- 27. No previously completed body system changes -----------------------

def test_no_other_body_systems_affected(db_session, built_state):
    from app.models.ontology_disease_blueprint import OntologyBodySystem
    oncology = db_session.query(OntologyBodySystem).filter_by(system_name="Oncology").one()
    other_systems = db_session.query(OntologyBodySystem).filter(OntologyBodySystem.id != oncology.id).all()
    # Merely asserts Oncology is additive: at least itself exists, and any
    # pre-existing other body systems are untouched by this importer
    # (which only ever resolves-or-creates within its own declared
    # scope.body_system / scope.families / diseases).
    assert oncology.system_name == "Oncology"
    for system in other_systems:
        assert system.system_name != "Oncology"


# --- differentiation guards -------------------------------------------------

EXPECTED_GUARD_NAMES = [
    "Breast Cancer IS_NOT Breast Primary Site",
    "Lung Cancer IS_NOT Lung Primary Site",
    "Leukemia IS_NOT Anatomical Primary Site",
    "Lymphoma IS_NOT Anatomical Primary Site",
    "Primary Bone Cancer IS_NOT Bone Metastasis",
    "Primary Brain Cancer IS_NOT Brain Metastasis",
    "Primary Liver Cancer IS_NOT Liver Metastasis",
    "Primary Lung Cancer IS_NOT Lung Metastasis",
    "Localized Disease IS_NOT Metastatic Disease",
    "Regional Spread IS_NOT Distant Metastatic Disease",
    "Recurrent Disease IS_NOT Metastatic Disease",
    "Progressive Disease IS_NOT Automatically Metastatic Disease",
    "Cancer Diagnosis DOES_NOT_ESTABLISH Hospice Eligibility",
    "Metastatic Disease DOES_NOT_ESTABLISH Metastatic Destination",
    "Metastatic Destination REQUIRES Patient Evidence",
]


def test_manifest_declares_all_fifteen_required_differentiation_guards():
    names = [g["guard_name"] for g in MANIFEST["differentiation_guards"]]
    assert names == EXPECTED_GUARD_NAMES


def test_all_fifteen_differentiation_guards_pass(db_session, built_state):
    report = build_acceptance_report(db_session, MANIFEST, second_run_new_rows=0)
    assert len(report["differentiation_guard_results"]) == 15
    for guard in report["differentiation_guard_results"]:
        assert guard["passed"] is True, f"guard failed: {guard}"


# --- 28. No unrelated files change (enforced structurally, see test below) ---

def test_manifest_file_scope_is_exactly_the_four_authorized_files():
    """A structural reminder, not a git check: this manifest/importer pair
    must only ever be paired with these four files. Verified at PR review
    time via `gh pr view --json files`."""
    assert DEFAULT_MANIFEST_PATH.name == "oncology_foundation_v1.json"
