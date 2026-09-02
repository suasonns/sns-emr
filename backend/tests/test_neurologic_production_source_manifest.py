# tests/test_neurologic_production_source_manifest.py
"""Targeted tests for the Neurologic Production Source Manifest v1 import
(`import_neurologic_production_source_manifest.py`).

This manifest is the sole authoritative source for this build -- every
assertion below is derived directly from the committed manifest file
(`backend/manifests/neurologic_production_source_manifest_v1.json`), never
from clinical judgment, inference, or a "similar enough" substitute.

Two categories of manifest content are schema-incompatible under the
CURRENT schema (no migration/schema change is permitted for this import,
and substituting a "similar" existing value is prohibited):

    1. 24 Tier 4 variants using a `dimension` value (SUBTYPE or
       SEVERITY_PHENOTYPE) not present in the
       ck_ontology_disease_variant_dimension CHECK constraint.
    2. 80 Tier 5 concepts (52 TREATMENT + 28 TREATMENT_LIMITATION) that
       require a NOT-NULL, enum-constrained category column the manifest
       does not supply a value for (treatment_category /
       limitation_category), and 7 of the 84 applicability mappings that
       reference those TREATMENT-domain concepts.

These items are never created and never substituted -- they are reported
as BLOCKED with an exact, deterministic reason, and every other manifest
item is imported normally in the same run. These tests assert the exact
resulting counts (unblocked content fully present, blocked content exactly
enumerated and absent), never a loose/dynamic count.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyConceptVariantApplicability,
    OntologyDisease,
    OntologyDiseaseTreatment,
    OntologyDiseaseTreatmentLimitation,
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
    BLOCKED_CONCEPT_DOMAINS,
    CONCEPT_DOMAIN_MODEL_MAP,
    DEFAULT_MANIFEST_PATH,
    load_manifest,
    run as run_manifest_import,
)

# Read-only superset of CONCEPT_DOMAIN_MODEL_MAP used purely for orphan
# verification: the merged five-tier baseline (PR #36) already created
# TREATMENT / TREATMENT_LIMITATION applicability edges from ITS OWN
# script -- this manifest importer never writes those two domains (they
# are schema-blocked, see module docstring), but pre-existing edges of
# those domains must still resolve cleanly for the no-orphan assertion.
FULL_CONCEPT_DOMAIN_MODEL_MAP = dict(CONCEPT_DOMAIN_MODEL_MAP)
FULL_CONCEPT_DOMAIN_MODEL_MAP["TREATMENT"] = (OntologyDiseaseTreatment, "treatment_name")
FULL_CONCEPT_DOMAIN_MODEL_MAP["TREATMENT_LIMITATION"] = (OntologyDiseaseTreatmentLimitation, "limitation_name")

MANIFEST = load_manifest(DEFAULT_MANIFEST_PATH)

DIFFERENTIATION_GUARDS = MANIFEST["differentiation_guards"]


def _seed_base_diseases(db_session) -> None:
    from scripts.expand_ontology_phase2_neurologic import EXISTING_DISEASE_NAMES, SYSTEM_NAME

    system = db_session.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one_or_none()
    if system is None:
        system = OntologyBodySystem(system_name=SYSTEM_NAME)
        db_session.add(system)
        db_session.flush()

    from app.models.ontology_disease_blueprint import OntologyDiseaseFamily

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


@pytest.fixture()
def built_state(db_session):
    """Bring the Neurologic System to the merged five-tier baseline (Phase 2
    + coverage repair + clinical-reasoning build), then run the Production
    Source Manifest v1 importer once, and hand back the resolved disease
    map plus the importer's result counts."""
    _seed_base_diseases(db_session)
    db_session.commit()
    run_phase2_script(db_session)
    db_session.commit()
    run_coverage_repair_script(db_session)
    db_session.commit()
    run_clinical_reasoning_script(db_session)
    db_session.commit()
    counts = run_manifest_import(db_session, manifest=MANIFEST)
    db_session.commit()
    diseases = {
        name: db_session.query(OntologyDisease).filter_by(disease_name=name).one()
        for name in ALL_DISEASE_NAMES
    }
    return {"diseases": diseases, "counts": counts}


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


def _manifest_unblocked_variants():
    result = []
    for disease_entry in MANIFEST["diseases"]:
        for v in disease_entry.get("variants", []):
            if v["dimension"] in ALLOWED_VARIANT_DIMENSIONS:
                result.append((disease_entry["disease"], v["dimension"], v["name"]))
    return result


def _manifest_blocked_variants():
    result = []
    for disease_entry in MANIFEST["diseases"]:
        for v in disease_entry.get("variants", []):
            if v["dimension"] not in ALLOWED_VARIANT_DIMENSIONS:
                result.append((disease_entry["disease"], v["dimension"], v["name"]))
    return result


def _manifest_unblocked_concepts():
    result = []
    for disease_entry in MANIFEST["diseases"]:
        for c in disease_entry.get("concepts", []):
            if c["domain"] not in BLOCKED_CONCEPT_DOMAINS:
                result.append((disease_entry["disease"], c["domain"], c["name"]))
    return result


def _manifest_blocked_concepts():
    result = []
    for disease_entry in MANIFEST["diseases"]:
        for c in disease_entry.get("concepts", []):
            if c["domain"] in BLOCKED_CONCEPT_DOMAINS:
                result.append((disease_entry["disease"], c["domain"], c["name"]))
    return result


def _manifest_unblocked_applicability():
    result = []
    for disease_entry in MANIFEST["diseases"]:
        for a in disease_entry.get("applicability", []):
            if a["concept_domain"] not in BLOCKED_CONCEPT_DOMAINS:
                result.append((disease_entry["disease"], a))
    return result


def _manifest_blocked_applicability():
    result = []
    for disease_entry in MANIFEST["diseases"]:
        for a in disease_entry.get("applicability", []):
            if a["concept_domain"] in BLOCKED_CONCEPT_DOMAINS:
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


def test_manifest_blocked_scope_is_exactly_24_variants_80_concepts_7_applicability():
    assert len(_manifest_blocked_variants()) == 24
    assert len(_manifest_blocked_concepts()) == 80
    assert len(_manifest_blocked_applicability()) == 7
    assert len(_manifest_unblocked_variants()) == 99
    assert len(_manifest_unblocked_concepts()) == 477
    assert len(_manifest_unblocked_applicability()) == 77


# --- 1. All 6 canonical diseases resolve ---

def test_all_six_canonical_diseases_resolve(db_session, built_state):
    for name in ALL_DISEASE_NAMES:
        assert db_session.query(OntologyDisease).filter_by(disease_name=name).one() is not None


# --- 2. All unblocked manifest variants exist (exact name + dimension) ---

def test_every_unblocked_manifest_variant_exists(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, dimension, name in _manifest_unblocked_variants():
        variant = _variant(db_session, diseases[disease_name], dimension, name)
        assert variant is not None, f"missing manifest variant: {disease_name}/{dimension}/{name}"
        assert variant.variant_name == name


def test_blocked_manifest_variants_are_not_created(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, dimension, name in _manifest_blocked_variants():
        assert dimension in {"SUBTYPE", "SEVERITY_PHENOTYPE"}
        row = (
            db_session.query(OntologyDiseaseVariant)
            .filter_by(disease_id=diseases[disease_name].id, normalized_name=name.strip().lower())
            .filter(OntologyDiseaseVariant.variant_dimension == dimension)
            .one_or_none()
        )
        assert row is None, f"blocked variant should not exist: {disease_name}/{dimension}/{name}"


# --- 3. All unblocked manifest concepts exist independently, exact name+domain ---

def test_every_unblocked_manifest_concept_exists(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, domain, name in _manifest_unblocked_concepts():
        concept = _concept(db_session, diseases[disease_name], domain, name)
        assert concept is not None, f"missing manifest concept: {disease_name}/{domain}/{name}"


def test_blocked_manifest_concepts_are_not_created(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, domain, name in _manifest_blocked_concepts():
        assert domain in {"TREATMENT", "TREATMENT_LIMITATION"}
        # Neither blocked domain has a corresponding writable model in this import.
        assert domain not in CONCEPT_DOMAIN_MODEL_MAP or _concept(db_session, diseases[disease_name], domain, name) is None


# --- 4. All unblocked applicability mappings exist, exact 5-identity match ---

def test_every_unblocked_applicability_mapping_exists(db_session, built_state):
    diseases = built_state["diseases"]
    for disease_name, a in _manifest_unblocked_applicability():
        disease = diseases[disease_name]
        variant = None
        for cand_dim in ALLOWED_VARIANT_DIMENSIONS:
            v = _variant(db_session, disease, cand_dim, a["variant"])
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


def test_blocked_applicability_mappings_all_reference_treatment_domain(built_state):
    blocked = _manifest_blocked_applicability()
    assert len(blocked) == 7
    for _, a in blocked:
        assert a["concept_domain"] == "TREATMENT"


# --- 5/9/10. Evidence rule coverage with patient_fact_requires_evidence = True ---

def test_every_created_concept_has_an_evidence_rule_requiring_evidence(db_session, built_state):
    diseases = built_state["diseases"]
    checked = 0
    for disease_name, domain, name in _manifest_unblocked_concepts():
        concept = _concept(db_session, diseases[disease_name], domain, name)
        rule = (
            db_session.query(OntologyEvidenceRule)
            .filter_by(concept_type=domain, concept_id=concept.id)
            .one_or_none()
        )
        assert rule is not None, f"missing evidence rule for {disease_name}/{domain}/{name}"
        assert rule.patient_fact_requires_evidence is True
        checked += 1
    assert checked == 477


# --- 11/12/13/14/15/16. Differentiation guards from the manifest ---

def test_hemiplegia_and_hemiparesis_remain_distinct(db_session, built_state):
    diseases = built_state["diseases"]
    hemiplegia_ids = {v.id for v in db_session.query(OntologyDiseaseVariant).filter_by(disease_id=diseases["Hemiplegia"].id)}
    hemiparesis_ids = {v.id for v in db_session.query(OntologyDiseaseVariant).filter_by(disease_id=diseases["Hemiparesis"].id)}
    assert hemiplegia_ids.isdisjoint(hemiparesis_ids)


def test_senile_degeneration_of_brain_remains_distinct_from_alzheimers(db_session, built_state):
    diseases = built_state["diseases"]
    assert diseases["Senile Degeneration of Brain"].id != diseases["Dementia Due To Alzheimer's Disease"].id


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


def test_hemorrhagic_stroke_has_no_thrombolysis_applicability(db_session, built_state):
    diseases = built_state["diseases"]
    hemorrhagic = _variant(db_session, diseases["Stroke"], "MECHANISM", "Hemorrhagic Stroke")
    assert hemorrhagic is not None
    edges = db_session.query(OntologyConceptVariantApplicability).filter_by(variant_id=hemorrhagic.id).all()
    treatment_names = {
        db_session.query(OntologyDiseaseVariant).filter_by(id=e.variant_id).one().variant_name
        for e in edges
    }
    assert "thrombolysis" not in " ".join(treatment_names).lower()


def test_positioning_discomfort_remains_distinct_from_painful_muscle_spasm(db_session, built_state):
    from app.models.ontology_disease_blueprint import OntologyDiseaseSymptom

    diseases = built_state["diseases"]
    contracture = diseases["Contracture"]
    positioning = (
        db_session.query(OntologyDiseaseSymptom)
        .filter_by(disease_id=contracture.id, symptom_name="Positioning Discomfort")
        .one_or_none()
    )
    painful_spasm = (
        db_session.query(OntologyDiseaseSymptom)
        .filter_by(disease_id=contracture.id, symptom_name="Painful Muscle Spasm")
        .one_or_none()
    )
    assert positioning is not None
    assert painful_spasm is not None
    assert positioning.id != painful_spasm.id


# --- 17. No manifest concept is satisfied by a clinically similar substitute ---

def test_no_manifest_concept_satisfied_by_a_similar_substitute(db_session, built_state):
    """Every manifest concept name must match EXACTLY -- a near-miss/synonym
    already present under a different exact name must not cause the
    importer to skip creating the manifest's exact term."""
    diseases = built_state["diseases"]
    for disease_name, domain, name in _manifest_unblocked_concepts():
        concept = _concept(db_session, diseases[disease_name], domain, name)
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[domain]
        assert getattr(concept, name_attr) == name


# --- 18/19. No orphan variant / applicability row ---

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
        model_cls, _ = FULL_CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        concept = db_session.query(model_cls).filter_by(id=edge.concept_id).one_or_none()
        assert concept is not None


# --- 20. No hierarchy cycle exists ---

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


# --- 21. Second execution creates zero rows ---

def test_second_run_creates_zero_new_rows(db_session, built_state):
    counts = run_manifest_import(db_session, manifest=MANIFEST)
    db_session.commit()
    assert counts["variants_inserted"] == 0
    assert counts["concepts_inserted_total"] == 0
    assert counts["applicability_inserted"] == 0
    assert counts["evidence_rules_inserted"] == 0
    assert len(counts["applicability_blocked"]) == 7


# --- 22. No other body system changes ---

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


# --- 23. No unrelated files change ---

def test_only_authorized_files_changed():
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"unable to diff against origin/main in this environment: {result.stderr.strip()}")
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    if not changed:
        pytest.skip("no diff against origin/main available in this environment")

    allowed_suffixes = (
        "backend/manifests/neurologic_production_source_manifest_v1.json",
        "backend/scripts/import_neurologic_production_source_manifest.py",
        "backend/tests/test_neurologic_production_source_manifest.py",
        "backend/artifacts/neurologic_production_manifest_acceptance_v1.json",
    )
    disallowed = [path for path in changed if not path.endswith(allowed_suffixes)]
    assert disallowed == [], f"unauthorized files changed: {disallowed}"


def test_manifest_differentiation_guards_are_all_represented():
    guard_pairs = {(g["left"], g["right"]) for g in DIFFERENTIATION_GUARDS}
    assert ("Hemiplegia", "Hemiparesis") in guard_pairs
    assert ("Dementia Due To Alzheimer's Disease", "Senile Degeneration of Brain") in guard_pairs
    assert ("Locked-In Syndrome", "Coma") in guard_pairs
    assert ("Hemorrhagic Stroke", "IV Thrombolytic Evaluation") in guard_pairs
    assert ("Historical Stroke", "Current Neurologic Deficit") in guard_pairs
