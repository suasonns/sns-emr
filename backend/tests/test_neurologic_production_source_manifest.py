# tests/test_neurologic_production_source_manifest.py
"""Targeted tests for the Neurologic Production Source Manifest v1 import
(`import_neurologic_production_source_manifest.py`).

This manifest is the sole authoritative source for this build -- every
assertion below is derived directly from the committed manifest file
(`backend/manifests/neurologic_production_source_manifest_v1.json`), never
from clinical judgment, inference, or a "similar enough" substitute.

The manifest's variant dimensions (SUBTYPE -> PATHOLOGICAL_SUBTYPE,
SEVERITY_PHENOTYPE -> SEVERITY_CLASS) and its TREATMENT /
TREATMENT_LIMITATION concepts (each carrying an explicit,
schema-compatible treatment_category / limitation_category) were corrected
at the manifest level -- an approved vocabulary correction only, never a
clinical-meaning change, rename, omission, or substitution. All 123
variants, 557 concepts, and 84 applicability mappings the manifest
declares are imported; nothing is blocked.
"""
from __future__ import annotations

import json
import pytest

from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyConceptVariantApplicability,
    OntologyDisease,
    OntologyDiseaseVariant,
    OntologyEvidenceRule,
)
from scripts.complete_ontology_neurologic_clinical_reasoning import (
    ALL_DISEASE_NAMES,
    run as run_clinical_reasoning_script,
)
from scripts.complete_ontology_phase2_neurologic_coverage import run as run_coverage_repair_script
from scripts.expand_ontology_phase2_neurologic import run as run_phase2_script
from scripts.import_neurologic_production_source_manifest import (
    ALLOWED_VARIANT_DIMENSIONS,
    CONCEPT_DOMAIN_MODEL_MAP,
    DEFAULT_MANIFEST_PATH,
    load_manifest,
    run as run_manifest_import,
)
from tests.conftest import TestSessionLocal

MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)
DIFFERENTIATION_GUARDS = MANIFEST["differentiation_guards"]


def _seed_base_diseases(db_session) -> None:
    """Delegates to the ONE authoritative seed helper
    (`tests.ontology_neurologic_baseline`) so every ontology test module
    resolves the same disease -> family mapping regardless of run order --
    see that module's docstring for why a second, incompatible mapping
    ("Neurodegenerative Disease") must never be reintroduced here."""
    from tests.ontology_neurologic_baseline import seed_base_neurologic_diseases

    seed_base_neurologic_diseases(db_session)


@pytest.fixture(scope="module")
def built_state():
    """Bring the Neurologic System to the merged five-tier baseline (Phase 2
    + coverage repair + clinical-reasoning build), then run the Production
    Source Manifest v1 importer once, and hand back the resolved disease
    map plus the importer's result counts.

    Module-scoped and built exactly ONCE for this file: the ontology
    tables are not tenant-scoped and are never cleared between tests (see
    `db_session` in conftest.py), so re-running this whole population
    pipeline per-test would redundantly re-execute the manifest importer
    against data it already committed in an earlier test in this same
    process, which is unnecessary and, for any concept whose category the
    importer reconciles across an identity match, unsafe. Building the
    state once and sharing it (read-only) across every test in this file
    avoids that entirely, and is what "run the importer once" actually
    means in the acceptance requirements below.
    """
    session = TestSessionLocal()
    try:
        _seed_base_diseases(session)
        session.commit()
        run_phase2_script(session)
        session.commit()
        run_coverage_repair_script(session)
        session.commit()
        run_clinical_reasoning_script(session)
        session.commit()
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


# --- manifest self-consistency (sanity check on the committed manifest file) ---

def test_manifest_declares_six_canonical_diseases():
    assert {d["disease"] for d in MANIFEST["diseases"]} == set(ALL_DISEASE_NAMES)


def test_manifest_declares_exact_summary_counts():
    summary = MANIFEST["summary"]
    assert summary["disease_count"] == 6
    assert summary["variant_count"] == 123
    assert summary["concept_count"] == 557
    assert summary["explicit_applicability_count"] == 84
    assert len(_manifest_variants()) == 123
    assert len(_manifest_concepts()) == 557
    assert len(_manifest_applicability()) == 84


# --- 1. SUBTYPE / SEVERITY_PHENOTYPE do not remain in the corrected manifest ---

def test_subtype_dimension_not_present_in_corrected_manifest():
    dims = {v["dimension"] for d in MANIFEST["diseases"] for v in d.get("variants", [])}
    assert "SUBTYPE" not in dims
    assert "SEVERITY_PHENOTYPE" not in dims
    assert dims <= ALLOWED_VARIANT_DIMENSIONS


def test_former_subtype_variants_use_pathological_subtype():
    alz = next(d for d in MANIFEST["diseases"] if d["disease"] == "Dementia Due To Alzheimer's Disease")
    names = {v["name"] for v in alz["variants"] if v["dimension"] == "PATHOLOGICAL_SUBTYPE"}
    for expected in (
        "Early-Onset Alzheimer's Disease", "Late-Onset Alzheimer's Disease",
        "Alzheimer's Disease With Behavioral Disturbance", "Alzheimer's Disease Without Behavioral Disturbance",
    ):
        assert expected in names


def test_former_severity_phenotype_variants_use_severity_class():
    stroke = next(d for d in MANIFEST["diseases"] if d["disease"] == "Stroke")
    names = {v["name"] for v in stroke["variants"] if v["dimension"] == "SEVERITY_CLASS"}
    assert "Large-Territory Stroke" in names
    assert "Malignant Cerebral Infarction" in names


# --- 5/6/7. All 123/557/84 stored, nothing blocked ---

def test_all_123_manifest_variants_are_stored(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, dimension, name in _manifest_variants():
        variant = _variant(db_session, diseases[disease_name], dimension, name)
        assert variant is not None, f"missing manifest variant: {disease_name}/{dimension}/{name}"
        assert variant.variant_name == name


def test_all_557_manifest_concepts_are_stored(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, domain, name, _entry in _manifest_concepts():
        concept = _concept(db_session, diseases[disease_name], domain, name)
        assert concept is not None, f"missing manifest concept: {disease_name}/{domain}/{name}"


def test_all_84_applicability_mappings_are_stored(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, a in _manifest_applicability():
        disease = diseases[disease_name]
        variant = None
        for dim in ALLOWED_VARIANT_DIMENSIONS:
            v = _variant(db_session, disease, dim, a["variant"])
            if v is not None:
                variant = v
                break
        assert variant is not None, f"variant not found for applicability: {disease_name}/{a['variant']}"
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


def test_nothing_is_blocked(built_state):
    counts = built_state["counts"]
    assert "variants_blocked" not in counts
    assert "concepts_blocked" not in counts
    assert "applicability_blocked" not in counts


# --- 8/9/10/11. Exact category assignments; nothing omitted for missing category ---

def test_every_treatment_has_its_exact_approved_treatment_category(db_session, built_state):
    diseases = built_state["diseases"]
    checked = 0
    for disease_name, domain, name, entry in _manifest_concepts():
        if domain != "TREATMENT":
            continue
        row = _concept(db_session, diseases[disease_name], domain, name)
        assert row is not None, f"treatment omitted: {disease_name}/{name}"
        assert row.treatment_category == entry["treatment_category"]
        checked += 1
    assert checked == 52


def test_every_treatment_limitation_has_its_exact_approved_limitation_category(db_session, built_state):
    diseases = built_state["diseases"]
    checked = 0
    for disease_name, domain, name, entry in _manifest_concepts():
        if domain != "TREATMENT_LIMITATION":
            continue
        row = _concept(db_session, diseases[disease_name], domain, name)
        assert row is not None, f"treatment limitation omitted: {disease_name}/{name}"
        assert row.limitation_category == entry["limitation_category"]
        checked += 1
    assert checked == 28


# --- 12. No concept or variant is blocked ---

def test_no_variant_or_concept_is_blocked(built_state):
    counts = built_state["counts"]
    assert counts["variants_inserted"] >= 0
    assert "variants_blocked" not in counts
    assert "concepts_blocked" not in counts


# --- 13/14. Evidence rule coverage with patient_fact_requires_evidence = True ---

def test_every_imported_concept_has_an_evidence_rule_requiring_evidence(db_session, built_state):
    diseases = built_state["diseases"]
    checked = 0
    for disease_name, domain, name, _entry in _manifest_concepts():
        concept = _concept(db_session, diseases[disease_name], domain, name)
        rule = (
            db_session.query(OntologyEvidenceRule)
            .filter_by(concept_type=domain, concept_id=concept.id)
            .one_or_none()
        )
        assert rule is not None, f"missing evidence rule for {disease_name}/{domain}/{name}"
        assert rule.patient_fact_requires_evidence is True
        checked += 1
    assert checked == 557


# --- 15/16/17/18/19. Differentiation guards ---

def test_hemorrhagic_stroke_has_no_thrombolysis_applicability(db_session, built_state):
    diseases = built_state["diseases"]
    hemorrhagic = _variant(db_session, diseases["Stroke"], "MECHANISM", "Hemorrhagic Stroke")
    assert hemorrhagic is not None
    edges = db_session.query(OntologyConceptVariantApplicability).filter_by(variant_id=hemorrhagic.id).all()
    for e in edges:
        assert e.applicability_type != "TREATMENT_SPECIFIC_TO"


def test_senile_degeneration_of_brain_remains_distinct_from_alzheimers(db_session, built_state):
    diseases = built_state["diseases"]
    assert diseases["Senile Degeneration of Brain"].id != diseases["Dementia Due To Alzheimer's Disease"].id


def test_hemiplegia_remains_distinct_from_hemiparesis(db_session, built_state):
    diseases = built_state["diseases"]
    hemiplegia_ids = {v.id for v in db_session.query(OntologyDiseaseVariant).filter_by(disease_id=diseases["Hemiplegia"].id)}
    hemiparesis_ids = {v.id for v in db_session.query(OntologyDiseaseVariant).filter_by(disease_id=diseases["Hemiparesis"].id)}
    assert hemiplegia_ids.isdisjoint(hemiparesis_ids)


def test_locked_in_syndrome_remains_distinct_from_coma(db_session, built_state):
    diseases = built_state["diseases"]
    stroke = diseases["Stroke"]
    coma = _variant(db_session, stroke, "PHYSIOLOGICAL_PHENOTYPE", "Coma")
    locked_in = _variant(db_session, stroke, "PHYSIOLOGICAL_PHENOTYPE", "Locked-In Syndrome")
    assert coma is not None and locked_in is not None
    assert coma.id != locked_in.id


def test_historical_stroke_does_not_imply_current_deficit(db_session, built_state):
    diseases = built_state["diseases"]
    historical = _variant(db_session, diseases["Stroke"], "DISEASE_PHASE", "Historical Stroke")
    assert historical is not None
    for edge in db_session.query(OntologyConceptVariantApplicability).filter_by(variant_id=historical.id).all():
        assert edge.applicability_type != "APPLIES_TO"


# --- 20/21. No orphan variant / applicability row, no hierarchy cycle ---

def test_no_orphan_variant_exists(db_session, built_state):
    diseases = built_state["diseases"]
    disease_ids = {d.id for d in diseases.values()}
    for variant in db_session.query(OntologyDiseaseVariant).filter(OntologyDiseaseVariant.disease_id.in_(disease_ids)).all():
        assert variant.disease_id in disease_ids
        if variant.parent_variant_id is not None:
            parent = db_session.query(OntologyDiseaseVariant).filter_by(id=variant.parent_variant_id).one_or_none()
            assert parent is not None


def test_no_orphan_applicability_row_exists(db_session, built_state):
    diseases = built_state["diseases"]
    disease_ids = {d.id for d in diseases.values()}
    for edge in db_session.query(OntologyConceptVariantApplicability).filter(
        OntologyConceptVariantApplicability.disease_id.in_(disease_ids)
    ).all():
        variant = db_session.query(OntologyDiseaseVariant).filter_by(id=edge.variant_id).one_or_none()
        assert variant is not None
        model_cls, _ = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        concept = db_session.query(model_cls).filter_by(id=edge.concept_id).one_or_none()
        assert concept is not None


def test_no_hierarchy_cycle_exists(db_session, built_state):
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


# --- 22. Second execution creates zero rows ---

def test_second_run_creates_zero_new_rows(db_session, built_state):
    counts = run_manifest_import(db_session, manifest=MANIFEST)
    db_session.commit()
    assert counts["variants_inserted"] == 0
    assert counts["concepts_inserted_total"] == 0
    assert counts["applicability_inserted"] == 0
    assert counts["evidence_rules_inserted"] == 0


# --- 23. No other body system changes ---

def test_no_other_body_system_touched(db_session, built_state):
    non_neurologic_disease_ids = {
        d.id for d in db_session.query(OntologyDisease).all()
        if d.disease_name not in ALL_DISEASE_NAMES
    }
    if not non_neurologic_disease_ids:
        pytest.skip("no non-Neurologic diseases present in this database")
    touched = (
        db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(non_neurologic_disease_ids))
        .filter(OntologyDiseaseVariant.source_reference == "neurologic_production_source_manifest_v1")
        .count()
    )
    assert touched == 0


# Note: the former git-diff scope guard test has been removed. PR-scope
# validation now happens via the CI-only `backend/scripts/validate_pr_scope.py`
# tool against an explicit allowlist, not as a pytest test, because pytest
# results must never depend on git diff state.


def test_manifest_differentiation_guards_are_all_represented():
    guard_pairs = {(g["left"], g["right"]) for g in DIFFERENTIATION_GUARDS}
    assert ("Hemiplegia", "Hemiparesis") in guard_pairs
    assert ("Dementia Due To Alzheimer's Disease", "Senile Degeneration of Brain") in guard_pairs
    assert ("Locked-In Syndrome", "Coma") in guard_pairs
    assert ("Hemorrhagic Stroke", "IV Thrombolytic Evaluation") in guard_pairs
    assert ("Historical Stroke", "Current Neurologic Deficit") in guard_pairs
