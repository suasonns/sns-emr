# tests/test_renal_production_source_manifest.py
"""Targeted tests for the corrected, source-faithful Renal Production
Source Manifest v1 import (`import_renal_production_source_manifest.py`).

This manifest is the sole authoritative source for this build -- every
assertion below is derived directly from the committed manifest file
(`backend/manifests/renal_production_source_manifest_v1.json`), never
from clinical judgment, inference, or a "similar enough" substitute.

PR #40 correction: Acute Renal Failure (ARF) and Chronic Renal Failure
(CRF) are distinct clinical pathways with distinct Tier 4 variants and
distinct Tier 5 supporting concepts -- they share only the explicit
"required hospice pathway" concepts (dialysis/transplant status, the
four exact LCD lab thresholds). Generic/unsupported concepts are
retained only as GENERAL_CLINICAL_KNOWLEDGE (never as an LCD criterion,
never eligible for HOSPICE_SUPPORT_FOR applicability). Non-disease-
specific decline indicators (KPS/PPS/ADL/ED-visit trends) are retained
as LCD_NON_DISEASE_SPECIFIC and explicitly do not, by themselves,
establish hospice eligibility.
"""
from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
)
from scripts.import_renal_production_source_manifest import (
    ALLOWED_SOURCE_CLASSIFICATIONS,
    ALLOWED_VARIANT_DIMENSIONS,
    CONCEPT_DOMAIN_MODEL_MAP,
    DEFAULT_MANIFEST_PATH,
    load_manifest,
    validate_manifest,
    run as run_manifest_import,
)
from tests.conftest import TestSessionLocal

MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)
ALL_DISEASE_NAMES = [d["disease"] for d in MANIFEST["diseases"]]
ARF = "Acute Renal Failure"
CRF = "Chronic Renal Failure"


@pytest.fixture(scope="module")
def built_state():
    """Import the corrected Renal Production Source Manifest v1 into a
    dedicated session against the test database, exactly once for this
    file (module-scoped -- ontology tables are not tenant-scoped and are
    never cleared between tests by the function-scoped db_session
    fixture)."""
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
    from app.models.ontology_disease_blueprint import OntologyDiseaseVariant

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


def _find_concept_entry(disease_name, domain, name):
    for d_name, dom, n, entry in _manifest_concepts():
        if d_name == disease_name and dom == domain and n == name:
            return entry
    return None


# --- manifest self-consistency ---

def test_manifest_declares_two_canonical_diseases():
    assert {d["disease"] for d in MANIFEST["diseases"]} == {CRF, ARF}


def test_manifest_declares_exact_summary_counts():
    summary = MANIFEST["summary"]
    assert summary["canonical_diseases"] == 2
    assert summary["total_variants"] == len(_manifest_variants())
    assert summary["total_concepts"] == len(_manifest_concepts())
    assert summary["total_applicability_mappings"] == len(_manifest_applicability())


def test_manifest_passes_structural_validation():
    assert validate_manifest(MANIFEST) == []


def test_every_applicability_entry_declares_an_explicit_variant_dimension():
    """No name-only variant matching is permitted -- every applicability
    entry must carry an explicit variant_dimension."""
    for disease_name, a in _manifest_applicability():
        assert a.get("variant_dimension"), f"missing variant_dimension for {disease_name}/{a.get('variant')}"
        assert a["variant_dimension"] in ALLOWED_VARIANT_DIMENSIONS


def test_every_concept_declares_a_valid_source_classification():
    for disease_name, domain, name, entry in _manifest_concepts():
        assert entry.get("source_classification") in ALLOWED_SOURCE_CLASSIFICATIONS
        assert entry.get("source_reference"), f"missing source_reference for {disease_name}/{domain}/{name}"


def test_kps_pps_adl_are_tier5_concepts_not_variants():
    variant_names = {v["name"] for d in MANIFEST["diseases"] for v in d.get("variants", [])}
    for name in (
        "KPS Less Than 70 Percent", "PPS Less Than 70 Percent",
        "Dependence In Two Or More Activities Of Daily Living",
    ):
        assert name not in variant_names


# --- ARF/CRF pathway separation (the PR #40 correction) ---

def test_acute_and_chronic_pathways_do_not_share_disease_specific_variants():
    """PHYSIOLOGICAL_PHENOTYPE (uremia/oliguria/hyperkalemia/pericarditis/
    hepatorenal/fluid-overload phenotypes) is Chronic-only; Acute never
    receives these phenotype variants."""
    arf_dims = {v["dimension"] for d in MANIFEST["diseases"] if d["disease"] == ARF for v in d["variants"]}
    assert "PHYSIOLOGICAL_PHENOTYPE" not in arf_dims


def test_chronic_specific_findings_are_not_attached_to_acute_renal_failure():
    """Do not attach Chronic Renal Failure-specific findings automatically
    to Acute Renal Failure."""
    arf_concept_names = {
        (domain, name) for d_name, domain, name, _ in _manifest_concepts() if d_name == ARF
    }
    for name in (
        "Uremic Pericarditis", "Hepatorenal Syndrome",
        "Intractable Hyperkalemia Greater Than 7.0",
        "Intractable Fluid Overload Not Responsive To Treatment",
    ):
        assert ("FINDING", name) not in arf_concept_names
        assert ("COMPLICATION", name) not in arf_concept_names


def test_acute_specific_comorbidity_support_is_not_attached_to_chronic_renal_failure():
    crf_concept_names = {
        (domain, name) for d_name, domain, name, _ in _manifest_concepts() if d_name == CRF
    }
    for name in ("Mechanical Ventilation", "Disseminated Intravascular Coagulation", "AIDS"):
        assert ("COMPLICATION", name) not in crf_concept_names


def test_platelet_count_and_cachexia_are_independently_queryable_concepts():
    """These are deliberately dual-domain (COMPLICATION support concept
    AND their own dedicated FINDING/NUTRITIONAL_IMPACT concept), not
    merged into one atomic concept."""
    assert _find_concept_entry(ARF, "COMPLICATION", "Platelet Count Less Than 25,000") is not None
    assert _find_concept_entry(ARF, "FINDING", "Platelet Count Less Than 25,000") is not None
    assert _find_concept_entry(ARF, "COMPLICATION", "Cachexia") is not None
    assert _find_concept_entry(ARF, "NUTRITIONAL_IMPACT", "Cachexia") is not None


# --- full coverage: nothing blocked ---

def test_all_manifest_variants_are_stored(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, dimension, name in _manifest_variants():
        variant = _variant(db_session, diseases[disease_name], dimension, name)
        assert variant is not None, f"missing manifest variant: {disease_name}/{dimension}/{name}"
        assert variant.variant_name == name
        assert variant.variant_dimension == dimension


def test_all_manifest_concepts_are_stored(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, domain, name, _entry in _manifest_concepts():
        concept = _concept(db_session, diseases[disease_name], domain, name)
        assert concept is not None, f"missing manifest concept: {disease_name}/{domain}/{name}"


def test_all_applicability_mappings_are_stored(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, a in _manifest_applicability():
        disease = diseases[disease_name]
        variant = _variant(db_session, disease, a["variant_dimension"], a["variant"])
        assert variant is not None, f"variant not found for applicability: {disease_name}/{a['variant_dimension']}/{a['variant']}"
        concept = _concept(db_session, disease, a["concept_domain"], a["concept"])
        assert concept is not None, f"concept not found for applicability: {disease_name}/{a['concept']}"
        edge = (
            db_session.query(OntologyConceptVariantApplicability)
            .filter_by(
                variant_id=variant.id,
                concept_id=concept.id,
                concept_type=a["concept_domain"],
                applicability_type=a["applicability_type"],
            )
            .one_or_none()
        )
        assert edge is not None, f"missing applicability edge: {disease_name}/{a['variant']}->{a['concept']}"
        assert edge.applicability_type == a["applicability_type"]


def test_nothing_is_blocked(built_state):
    counts = built_state["counts"]
    assert "variants_blocked" not in counts
    assert "concepts_blocked" not in counts
    assert "applicability_blocked" not in counts


# --- evidence rule coverage with patient_fact_requires_evidence = True ---

def test_every_imported_concept_has_an_evidence_rule_requiring_evidence(db_session, built_state):
    diseases = built_state["diseases"]
    checked = 0
    for disease_name, domain, name, _entry in _manifest_concepts():
        concept = _concept(db_session, diseases[disease_name], domain, name)
        rule = _evidence_rule(db_session, domain, concept.id)
        assert rule is not None, f"missing evidence rule for {disease_name}/{domain}/{name}"
        assert rule.patient_fact_requires_evidence is True
        checked += 1
    assert checked == len(_manifest_concepts())


def test_hospice_eligibility_support_concepts_require_evidence(db_session, built_state):
    """Critical LCD rule: renal diagnosis alone is insufficient -- every
    HOSPICE_ELIGIBILITY_SUPPORT concept must require evidence."""
    diseases = built_state["diseases"]
    checked = 0
    for disease_name, domain, name, _entry in _manifest_concepts():
        if domain != "HOSPICE_ELIGIBILITY_SUPPORT":
            continue
        concept = _concept(db_session, diseases[disease_name], domain, name)
        rule = _evidence_rule(db_session, domain, concept.id)
        assert rule is not None
        assert rule.patient_fact_requires_evidence is True
        checked += 1
    assert checked > 0


# --- exact LCD threshold concepts: distinct, never merged, never generic ---

def test_creatinine_clearance_and_gfr_remain_independently_queryable(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name in (ARF, CRF):
        disease = diseases[disease_name]
        crcl = _concept(db_session, disease, "HOSPICE_ELIGIBILITY_SUPPORT", "Creatinine Clearance Less Than 15 mL/min")
        gfr = _concept(db_session, disease, "HOSPICE_ELIGIBILITY_SUPPORT", "GFR Less Than 15 mL/min")
        assert crcl is not None and gfr is not None
        assert crcl.id != gfr.id


def test_serum_creatinine_thresholds_remain_distinct_and_diabetes_gated(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name in (ARF, CRF):
        disease = diseases[disease_name]
        generic = _concept(db_session, disease, "HOSPICE_ELIGIBILITY_SUPPORT", "Serum Creatinine Greater Than 8.0 mg/dL")
        diabetic = _concept(
            db_session, disease, "HOSPICE_ELIGIBILITY_SUPPORT",
            "Serum Creatinine Greater Than 6.0 mg/dL For Patient With Diabetes",
        )
        assert generic is not None and diabetic is not None
        assert generic.id != diabetic.id
        diabetic_entry = _find_concept_entry(disease_name, "HOSPICE_ELIGIBILITY_SUPPORT",
                                              "Serum Creatinine Greater Than 6.0 mg/dL For Patient With Diabetes")
        assert "diabetes_status" in diabetic_entry["evidence_requirements"], (
            "the diabetic threshold must require documented diabetes status before it can ever apply"
        )


def test_generic_elevated_serum_creatinine_does_not_satisfy_exact_lcd_threshold(db_session, built_state):
    for disease_name in (ARF, CRF):
        entry = _find_concept_entry(disease_name, "FINDING", "Elevated Serum Creatinine")
        assert entry["source_classification"] == "GENERAL_CLINICAL_KNOWLEDGE"
        assert entry["hospice_support_eligible"] is False
        # No HOSPICE_SUPPORT_FOR applicability may target this concept.
        matches = [
            a for d_name, a in _manifest_applicability()
            if d_name == disease_name and a["concept_domain"] == "FINDING" and a["concept"] == "Elevated Serum Creatinine"
        ]
        assert matches == []


def test_platelet_count_requires_a_documented_lab_result():
    entry = _find_concept_entry(ARF, "FINDING", "Platelet Count Less Than 25,000")
    for field in ("laboratory_name", "laboratory_value", "laboratory_unit", "laboratory_date"):
        assert field in entry["evidence_requirements"]


def test_intractable_hyperkalemia_requires_lab_result_and_treatment_nonresponse():
    entry = _find_concept_entry(CRF, "FINDING", "Intractable Hyperkalemia Greater Than 7.0")
    for field in ("laboratory_name", "laboratory_value", "treatment_response_status"):
        assert field in entry["evidence_requirements"]


def test_intractable_fluid_overload_requires_documented_treatment_nonresponse():
    entry = _find_concept_entry(CRF, "FINDING", "Intractable Fluid Overload Not Responsive To Treatment")
    assert "treatment_response_status" in entry["evidence_requirements"]


def test_generic_fluid_and_volume_overload_do_not_satisfy_intractable_fluid_overload():
    for disease_name in (ARF, CRF):
        for name in ("Fluid Overload", "Volume Overload"):
            entry = _find_concept_entry(disease_name, "FINDING", name)
            assert entry["source_classification"] == "GENERAL_CLINICAL_KNOWLEDGE"
            assert entry["hospice_support_eligible"] is False


def test_intractable_hyperkalemia_is_not_reduced_to_refractory_hyperkalemia():
    exact = _find_concept_entry(CRF, "FINDING", "Intractable Hyperkalemia Greater Than 7.0")
    generic = _find_concept_entry(CRF, "COMPLICATION", "Refractory Hyperkalemia")
    assert exact is not None and generic is not None
    assert exact["source_classification"] == "LCD_DISEASE_SPECIFIC"
    assert generic["source_classification"] == "GENERAL_CLINICAL_KNOWLEDGE"
    assert generic["hospice_support_eligible"] is False


# --- non-disease-specific baseline never independently establishes eligibility ---

def test_non_disease_specific_concepts_are_classified_and_limited(db_session, built_state):
    non_disease_names = [
        "KPS Less Than 70 Percent", "PPS Less Than 70 Percent",
        "Dependence In Two Or More Activities Of Daily Living",
        "Progressive Functional Decline", "Progressive Nutritional Decline",
        "Increasing Emergency Department Visits", "Increasing Hospitalizations",
        "Increasing Physician Visits",
    ]
    checked = 0
    for disease_name in (ARF, CRF):
        for name in non_disease_names:
            entry = _find_concept_entry(disease_name, "HOSPICE_ELIGIBILITY_SUPPORT", name)
            assert entry is not None, f"missing non-disease-specific concept {disease_name}/{name}"
            assert entry["source_classification"] == "LCD_NON_DISEASE_SPECIFIC"
            assert "does not independently establish" in entry["description"].lower()
            checked += 1
    assert checked == len(non_disease_names) * 2


def test_diagnosis_alone_never_establishes_terminal_prognosis(db_session, built_state):
    """The bare DISEASE_PHASE variant representing diagnosis-only status
    ('Acute Renal Failure' itself) must never carry any HOSPICE_SUPPORT_FOR
    applicability -- only the terminal/end-stage phase does."""
    diseases = built_state["diseases"]
    base_variant = _variant(db_session, diseases[ARF], "DISEASE_PHASE", "Acute Renal Failure")
    assert base_variant is not None
    edges = (
        db_session.query(OntologyConceptVariantApplicability)
        .filter_by(variant_id=base_variant.id, applicability_type="HOSPICE_SUPPORT_FOR")
        .all()
    )
    assert edges == []


def test_unsupported_general_concepts_never_receive_hospice_support_applicability():
    general_names = {
        "Pruritus", "Refractory Acidosis", "Anuria", "Fluid Overload",
        "Volume Overload", "Elevated Serum Creatinine", "Refractory Hyperkalemia",
    }
    for disease_name, a in _manifest_applicability():
        if a["concept"] in general_names:
            assert a["applicability_type"] != "HOSPICE_SUPPORT_FOR", (
                f"{a['concept']} is GENERAL_CLINICAL_KNOWLEDGE and must never receive HOSPICE_SUPPORT_FOR"
            )


def test_removed_unsupported_variants_are_not_recreated():
    """Anuric Renal Failure, Renal Transplant Declined, Recurrent Uremic
    Complications, Volume Overload Renal Failure, Mild/Moderate Renal
    Failure were removed from the corrected variant set -- they must not
    reappear as Tier 4 variants."""
    variant_names = {v["name"] for d in MANIFEST["diseases"] for v in d.get("variants", [])}
    for name in (
        "Anuric Renal Failure", "Renal Transplant Declined", "Recurrent Uremic Complications",
        "Volume Overload Renal Failure", "Mild Renal Failure", "Moderate Renal Failure",
    ):
        assert name not in variant_names


# --- differentiation guards from the manifest itself ---

def test_acute_and_chronic_renal_failure_remain_distinct(built_state):
    diseases = built_state["diseases"]
    assert diseases[ARF].id != diseases[CRF].id


def test_not_seeking_dialysis_is_not_equivalent_to_dialysis_discontinued(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name in (ARF, CRF):
        disease = diseases[disease_name]
        a = _concept(db_session, disease, "HOSPICE_ELIGIBILITY_SUPPORT", "Not Seeking Dialysis")
        b = _concept(db_session, disease, "HOSPICE_ELIGIBILITY_SUPPORT", "Discontinuing Dialysis")
        assert a is not None and b is not None
        assert a.id != b.id


def test_not_seeking_renal_transplant_is_not_equivalent_to_dialysis_discontinued(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name in (ARF, CRF):
        disease = diseases[disease_name]
        a = _concept(db_session, disease, "HOSPICE_ELIGIBILITY_SUPPORT", "Not Seeking Renal Transplant")
        b = _concept(db_session, disease, "HOSPICE_ELIGIBILITY_SUPPORT", "Discontinuing Dialysis")
        assert a is not None and b is not None
        assert a.id != b.id


def test_every_manifest_guard_passes():
    """Import once and confirm build_acceptance_report reports every
    declared differentiation guard as passed."""
    from scripts.import_renal_production_source_manifest import build_acceptance_report

    session = TestSessionLocal()
    try:
        run_manifest_import(session, manifest=MANIFEST)
        session.commit()
        report = build_acceptance_report(session, MANIFEST, second_run_new_rows=0)
        assert report["differentiation_guard_results"], "no guards were evaluated"
        for guard in report["differentiation_guard_results"]:
            assert guard["passed"] is True, guard
    finally:
        session.close()


# --- no orphan variant / applicability row, no hierarchy cycle ---

def test_no_orphan_variant_exists(db_session, built_state):
    from app.models.ontology_disease_blueprint import OntologyDiseaseVariant

    diseases = built_state["diseases"]
    disease_ids = {d.id for d in diseases.values()}
    variants = db_session.query(OntologyDiseaseVariant).filter(OntologyDiseaseVariant.disease_id.in_(disease_ids)).all()
    variant_ids = {v.id for v in variants}
    for variant in variants:
        assert variant.disease_id in disease_ids
        if variant.parent_variant_id is not None:
            assert variant.parent_variant_id in variant_ids


def test_no_orphan_applicability_row_exists(db_session, built_state):
    diseases = built_state["diseases"]
    disease_ids = {d.id for d in diseases.values()}
    for edge in db_session.query(OntologyConceptVariantApplicability).filter(
        OntologyConceptVariantApplicability.disease_id.in_(disease_ids)
    ).all():
        from app.models.ontology_disease_blueprint import OntologyDiseaseVariant

        variant = db_session.query(OntologyDiseaseVariant).filter_by(id=edge.variant_id).one_or_none()
        assert variant is not None
        model_cls, _ = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        concept = db_session.query(model_cls).filter_by(id=edge.concept_id).one_or_none()
        assert concept is not None


def test_no_hierarchy_cycle_exists(db_session, built_state):
    from app.models.ontology_disease_blueprint import OntologyDiseaseVariant

    diseases = built_state["diseases"]
    disease_ids = {d.id for d in diseases.values()}
    variants = db_session.query(OntologyDiseaseVariant).filter(OntologyDiseaseVariant.disease_id.in_(disease_ids)).all()
    by_id = {v.id: v for v in variants}
    for v in variants:
        seen = set()
        current = v
        while current.parent_variant_id is not None:
            assert current.id not in seen, f"cycle detected at variant {current.id}"
            seen.add(current.id)
            current = by_id.get(current.parent_variant_id)
            if current is None:
                break


def test_no_unresolved_concept_exists(db_session, built_state):
    """Every applicability row's concept_id must resolve to an existing
    row in the model its concept_type maps to."""
    diseases = built_state["diseases"]
    disease_ids = {d.id for d in diseases.values()}
    for edge in db_session.query(OntologyConceptVariantApplicability).filter(
        OntologyConceptVariantApplicability.disease_id.in_(disease_ids)
    ).all():
        model_cls, _ = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        assert db_session.query(model_cls).filter_by(id=edge.concept_id).one_or_none() is not None


# --- idempotency: second execution creates zero rows ---

def test_second_run_creates_zero_new_rows(db_session, built_state):
    counts = run_manifest_import(db_session, manifest=MANIFEST)
    db_session.commit()
    assert counts["variants_inserted"] == 0
    assert counts["concepts_inserted_total"] == 0
    assert counts["applicability_inserted"] == 0
    assert counts["evidence_rules_inserted"] == 0


# --- no changes to other body systems ---

def test_no_other_body_system_records_touched(db_session, built_state):
    from app.models.ontology_disease_blueprint import OntologyDiseaseVariant

    other_disease_ids = {
        d.id for d in db_session.query(OntologyDisease).all()
        if d.disease_name not in ALL_DISEASE_NAMES
    }
    if not other_disease_ids:
        pytest.skip("no non-Renal diseases present in this database")
    touched = (
        db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(other_disease_ids))
        .filter(OntologyDiseaseVariant.source_reference == "renal_production_source_manifest_v1")
        .count()
    )
    assert touched == 0


# Note: the former git-diff scope guard test has been removed. PR-scope
# validation now happens via the CI-only `backend/scripts/validate_pr_scope.py`
# tool against an explicit allowlist, not as a pytest test, because pytest
# results must never depend on git diff state.
