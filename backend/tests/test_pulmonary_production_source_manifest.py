# tests/test_pulmonary_production_source_manifest.py
"""Targeted tests for the Pulmonary Production Source Manifest v1
import (`import_pulmonary_production_source_manifest.py`).

This manifest is the sole authoritative source for this build -- every
assertion below is derived directly from the committed manifest file
(`backend/manifests/pulmonary_production_source_manifest_v1.json`),
never from clinical judgment, inference, or a "similar enough"
substitute. This reuses the exact verbatim-import pattern proven in
test_neurologic_production_source_manifest.py (PR #37) and
test_cardiovascular_production_source_manifest.py (PR #38).
"""
from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
)
from scripts.import_pulmonary_production_source_manifest import (
    ALLOWED_VARIANT_DIMENSIONS,
    CONCEPT_DOMAIN_MODEL_MAP,
    DEFAULT_MANIFEST_PATH,
    load_manifest,
    run as run_manifest_import,
)
from tests.conftest import TestSessionLocal

MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)
ALL_DISEASE_NAMES = [d["disease"] for d in MANIFEST["diseases"]]


@pytest.fixture(scope="module")
def built_state():
    """Import the Pulmonary Production Source Manifest v1 into a
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


# --- manifest self-consistency ---

def test_manifest_declares_two_canonical_diseases():
    assert {d["disease"] for d in MANIFEST["diseases"]} == {
        "End Stage Pulmonary Disease", "Chronic Obstructive Pulmonary Disease",
    }


def test_manifest_declares_exact_summary_counts():
    summary = MANIFEST["summary"]
    assert summary["disease_count"] == 2
    assert summary["variant_count"] == len(_manifest_variants())
    assert summary["concept_count"] == len(_manifest_concepts())
    assert summary["explicit_applicability_count"] == len(_manifest_applicability())


def test_respiratory_physiology_dimension_not_present():
    """Approved vocabulary correction: RESPIRATORY_PHYSIOLOGY is never a
    Tier 4 variant dimension -- the three respiratory-failure phenotype
    variants are stored under the existing PHYSIOLOGICAL_PHENOTYPE
    dimension instead. No new dimension, no migration, no schema change."""
    dims = {v["dimension"] for d in MANIFEST["diseases"] for v in d.get("variants", [])}
    assert "RESPIRATORY_PHYSIOLOGY" not in dims
    assert dims <= ALLOWED_VARIANT_DIMENSIONS


def test_respiratory_failure_variants_stored_under_physiological_phenotype(db_session, built_state):
    diseases = built_state["diseases"]
    expected_names = {
        "Hypoxemic Respiratory Failure",
        "Hypercapnic Respiratory Failure",
        "Combined Hypoxemic Hypercapnic Respiratory Failure",
    }
    for disease in diseases.values():
        for name in expected_names:
            variant = _variant(db_session, disease, "PHYSIOLOGICAL_PHENOTYPE", name)
            assert variant is not None, f"missing respiratory-failure variant: {disease.disease_name}/{name}"


# --- full coverage: nothing blocked ---

def test_all_manifest_variants_are_stored(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, dimension, name in _manifest_variants():
        variant = _variant(db_session, diseases[disease_name], dimension, name)
        assert variant is not None, f"missing manifest variant: {disease_name}/{dimension}/{name}"
        assert variant.variant_name == name


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
        rule = (
            db_session.query(OntologyEvidenceRule)
            .filter_by(concept_type=domain, concept_id=concept.id)
            .one_or_none()
        )
        assert rule is not None, f"missing evidence rule for {disease_name}/{domain}/{name}"
        assert rule.patient_fact_requires_evidence is True
        checked += 1
    assert checked == len(_manifest_concepts())


# --- exact source attribution ---

def test_every_manifest_concept_carries_exact_source_attribution():
    for disease_name, domain, name, entry in _manifest_concepts():
        assert entry.get("source_ids"), f"missing source_ids for {disease_name}/{domain}/{name}"
        for source_id in entry["source_ids"]:
            assert source_id in {s["source_id"] for s in MANIFEST["sources"]}


# --- differentiation guard: the two diseases remain distinct ---

def test_end_stage_pulmonary_disease_remains_distinct_from_copd(built_state):
    diseases = built_state["diseases"]
    assert diseases["End Stage Pulmonary Disease"].id != diseases["Chronic Obstructive Pulmonary Disease"].id


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


# --- no changes to Neurologic or Cardiovascular ---

def test_no_other_body_system_records_touched(db_session, built_state):
    from app.models.ontology_disease_blueprint import OntologyDiseaseVariant

    other_disease_ids = {
        d.id for d in db_session.query(OntologyDisease).all()
        if d.disease_name not in ALL_DISEASE_NAMES
    }
    if not other_disease_ids:
        pytest.skip("no non-Pulmonary diseases present in this database")
    touched = (
        db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(other_disease_ids))
        .filter(OntologyDiseaseVariant.source_reference == "pulmonary_production_source_manifest_v1")
        .count()
    )
    assert touched == 0


# Note: the former git-diff scope guard test has been removed. PR-scope
# validation now happens via the CI-only `backend/scripts/validate_pr_scope.py`
# tool against an explicit allowlist, not as a pytest test, because pytest
# results must never depend on git diff state.
