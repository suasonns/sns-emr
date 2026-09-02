"""Targeted tests for the Neurologic Clinical Reasoning Completion build
(`complete_ontology_neurologic_clinical_reasoning.py`) -- the Tier 4
(OntologyDiseaseVariant) / Tier 5 applicability (OntologyConceptVariant
Applicability) knowledge layer added on top of the merged Neurologic Phase 2
baseline (PR #34, #35).

Scope is strictly limited to the same six approved diseases: Stroke,
Hemiplegia, Hemiparesis, Contracture, Dementia Due To Alzheimer's Disease,
and Senile Degeneration of Brain. These tests assert that:

    - no new canonical disease, disease family, or body system is created
    - Tier 4 variants support recursive parent/child nesting
    - a single Tier 5 concept can be linked to more than one Tier 4 variant
      (multi-dimension applicability)
    - ischemic and hemorrhagic stroke mechanism knowledge is never conflated
      (e.g. thrombolysis is TREATMENT_SPECIFIC_TO ischemic stroke and
      CONTRAINDICATED_FOR hemorrhagic stroke, never both/neither)
    - left- and right-hemisphere/laterality variants remain distinct rows
    - a historical stroke variant never implies an automatically-active
      current deficit (SUPPORTS_DIFFERENTIATION, not an assertion of fact)
    - Locked-In Syndrome is never conflated with Coma
    - Hemiplegia and Hemiparesis variant/severity knowledge remains distinct
    - Senile Degeneration of Brain remains distinct from Dementia Due To
      Alzheimer's Disease, with no Alzheimer-specific hospice/FAST content
      ever linked to it through the new applicability table
    - no duplicate variant exists within the same disease+dimension
    - no duplicate applicability edge exists
    - every Tier 4 variant has an active OntologyEvidenceRule with
      patient_fact_requires_evidence = True
    - a second run of the population script creates zero new rows
    - no other body system is touched
    - only the four authorized files are part of this change
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
    OntologyDiseaseFamily,
    OntologyDiseaseVariant,
    OntologyEvidenceRule,
)
from scripts.complete_ontology_neurologic_clinical_reasoning import (
    ALL_DISEASE_NAMES,
    ALZ,
    CONTRACTURE,
    HEMIPARESIS,
    HEMIPLEGIA,
    SDB,
    STROKE,
    export_five_tier_acceptance_baseline,
    run as run_clinical_reasoning_script,
    write_acceptance_baseline_export,
)
from scripts.complete_ontology_phase2_neurologic_coverage import run as run_coverage_repair_script
from scripts.expand_ontology_phase2_neurologic import EXISTING_DISEASE_NAMES, SYSTEM_NAME
from scripts.expand_ontology_phase2_neurologic import run as run_phase2_script

BASE_DISEASE_FAMILY = {
    STROKE: "Cerebrovascular Disease",
    HEMIPLEGIA: "Cerebrovascular Disease",
    HEMIPARESIS: "Cerebrovascular Disease",
    CONTRACTURE: "Cerebrovascular Disease",
    ALZ: "Dementia Disorders",
}


def _seed_base_diseases(db_session) -> None:
    """Minimal System -> Family -> Disease seed for the five pre-existing
    Neurologic diseases, matching the exact system/family names
    expand_ontology_phase2_neurologic.py expects to find already in place.
    Idempotent -- safe to call every time the fixture runs."""
    system = db_session.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one_or_none()
    if system is None:
        system = OntologyBodySystem(system_name=SYSTEM_NAME)
        db_session.add(system)
        db_session.flush()

    family_cache = {}
    for name in EXISTING_DISEASE_NAMES:
        family_name = BASE_DISEASE_FAMILY[name]
        family = family_cache.get(family_name)
        if family is None:
            family = (
                db_session.query(OntologyDiseaseFamily)
                .filter_by(body_system_id=system.id, family_name=family_name)
                .one_or_none()
            )
            if family is None:
                family = OntologyDiseaseFamily(body_system_id=system.id, family_name=family_name)
                db_session.add(family)
                db_session.flush()
            family_cache[family_name] = family

        disease = db_session.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
        if disease is None:
            disease = OntologyDisease(disease_family_id=family.id, disease_name=name)
            db_session.add(disease)
    db_session.flush()


@pytest.fixture()
def built_state(db_session):
    """Seed the base Neurologic disease rows (Stroke, Hemiplegia,
    Hemiparesis, Contracture, Dementia Due To Alzheimer's Disease), run the
    Phase 2 baseline expansion (idempotent prerequisite -- also creates
    Senile Degeneration of Brain), then run the clinical-reasoning build
    once to bring the Neurologic System to a known Tier 4/5 state, then
    hand back the resolved disease map. Safe to call repeatedly -- all
    steps are idempotent."""
    _seed_base_diseases(db_session)
    db_session.commit()
    run_phase2_script(db_session)
    db_session.commit()
    run_coverage_repair_script(db_session)
    db_session.commit()
    run_clinical_reasoning_script(db_session)
    db_session.commit()
    diseases = {
        name: db_session.query(OntologyDisease).filter_by(disease_name=name).one()
        for name in ALL_DISEASE_NAMES
    }
    return diseases


def _variant(db_session, disease, dimension, name):
    normalized = name.strip().lower()
    return (
        db_session.query(OntologyDiseaseVariant)
        .filter_by(disease_id=disease.id, variant_dimension=dimension, normalized_name=normalized)
        .one()
    )


def test_no_new_canonical_disease_family_or_body_system_created(db_session, built_state):
    """The clinical-reasoning build must never create a new OntologyDisease,
    OntologyDiseaseFamily, or OntologyBodySystem row -- only Tier 4/5
    content attached to the six pre-existing diseases."""
    for name in ALL_DISEASE_NAMES:
        rows = db_session.query(OntologyDisease).filter_by(disease_name=name).all()
        assert len(rows) == 1, f"{name} must resolve to exactly one pre-existing disease row"

    forbidden_disease_names = {
        "Ischemic Stroke", "Thrombotic Stroke", "Embolic Stroke", "Cardioembolic Stroke",
        "Hemorrhagic Stroke", "Intracerebral Hemorrhage", "Subarachnoid Hemorrhage",
        "Brainstem Stroke", "Cerebellar Stroke", "Left-Hemisphere Stroke", "Right-Hemisphere Stroke",
        "Coma", "Locked-In Syndrome", "Vegetative State",
    }
    existing_disease_names = {d.disease_name for d in db_session.query(OntologyDisease.disease_name).all()}
    assert forbidden_disease_names.isdisjoint(existing_disease_names)

    neuro_system = built_state[STROKE].disease_family.body_system
    system_count = (
        db_session.query(OntologyBodySystem)
        .filter_by(system_name=neuro_system.system_name)
        .count()
    )
    assert system_count == 1


def test_variants_recursively_nest_under_parent(db_session, built_state):
    """Cardioembolic Stroke -> Embolic Stroke -> Ischemic Stroke must form a
    real recursive parent chain via parent_variant_id, not three
    independent top-level rows."""
    stroke = built_state[STROKE]
    ischemic = _variant(db_session, stroke, "MECHANISM", "Ischemic Stroke")
    embolic = _variant(db_session, stroke, "MECHANISM", "Embolic Stroke")
    cardioembolic = _variant(db_session, stroke, "MECHANISM", "Cardioembolic Stroke")

    assert ischemic.parent_variant_id is None
    assert embolic.parent_variant_id == ischemic.id
    assert cardioembolic.parent_variant_id == embolic.id

    # Child-variant relationship resolves correctly in both directions.
    assert cardioembolic in embolic.child_variants
    assert embolic in ischemic.child_variants
    assert cardioembolic.parent_variant.id == embolic.id


def test_hemorrhagic_and_ischemic_mechanism_never_conflated(db_session, built_state):
    """Hemorrhagic Stroke must never share a mechanism parent with Ischemic
    Stroke, and treatment applicability must correctly differentiate them:
    thrombolysis is specific to ischemic stroke and explicitly
    contraindicated for hemorrhagic stroke -- never both, never neither."""
    stroke = built_state[STROKE]
    ischemic = _variant(db_session, stroke, "MECHANISM", "Ischemic Stroke")
    hemorrhagic = _variant(db_session, stroke, "MECHANISM", "Hemorrhagic Stroke")
    assert ischemic.id != hemorrhagic.id
    assert ischemic.parent_variant_id is None
    assert hemorrhagic.parent_variant_id is None

    edges = (
        db_session.query(OntologyConceptVariantApplicability)
        .filter(
            OntologyConceptVariantApplicability.variant_id.in_([ischemic.id, hemorrhagic.id]),
            OntologyConceptVariantApplicability.concept_type == "TREATMENT",
        )
        .all()
    )
    by_variant = {(e.variant_id, e.applicability_type) for e in edges}
    assert (ischemic.id, "TREATMENT_SPECIFIC_TO") in by_variant
    assert (hemorrhagic.id, "CONTRAINDICATED_FOR") in by_variant
    # Never simultaneously specific-to AND contraindicated-for the same variant.
    assert (ischemic.id, "CONTRAINDICATED_FOR") not in by_variant
    assert (hemorrhagic.id, "TREATMENT_SPECIFIC_TO") not in by_variant


def test_left_and_right_hemisphere_variants_remain_distinct(db_session, built_state):
    stroke = built_state[STROKE]
    left = _variant(db_session, stroke, "HEMISPHERE", "Left-Hemisphere Stroke")
    right = _variant(db_session, stroke, "HEMISPHERE", "Right-Hemisphere Stroke")
    assert left.id != right.id
    assert left.normalized_name != right.normalized_name

    left_edges = {
        e.concept_id
        for e in db_session.query(OntologyConceptVariantApplicability).filter_by(variant_id=left.id).all()
    }
    right_edges = {
        e.concept_id
        for e in db_session.query(OntologyConceptVariantApplicability).filter_by(variant_id=right.id).all()
    }
    # Both sides carry independent applicability knowledge (not a single
    # shared/ambiguous laterality row).
    assert len(left_edges) > 0
    assert len(right_edges) > 0


def test_concept_may_apply_to_multiple_variants(db_session, built_state):
    """A single Tier 5 concept (Visual Field Deficit) must be able to carry
    applicability to more than one Tier 4 variant at once -- confirming the
    many-to-many edge table design is actually exercised, not just declared
    in the schema."""
    stroke = built_state[STROKE]
    finding = (
        db_session.query(OntologyConceptVariantApplicability.concept_id)
        .join(OntologyDiseaseVariant, OntologyConceptVariantApplicability.variant_id == OntologyDiseaseVariant.id)
        .filter(
            OntologyDiseaseVariant.disease_id == stroke.id,
            OntologyConceptVariantApplicability.concept_type == "FINDING",
        )
        .all()
    )
    concept_ids = [row[0] for row in finding]
    # "Visual Field Deficit" was linked to Temporal-Lobe, Occipital-Lobe,
    # Left-Hemisphere, Right-Hemisphere, and PCA-territory variants.
    counts: dict = {}
    for cid in concept_ids:
        counts[cid] = counts.get(cid, 0) + 1
    assert any(count >= 3 for count in counts.values()), (
        "expected at least one Tier 5 finding linked to 3+ distinct Tier 4 variants"
    )


def test_historical_stroke_never_implies_active_current_deficit(db_session, built_state):
    """A Historical Stroke variant must only ever carry SUPPORTS_
    DIFFERENTIATION applicability toward a deficit symptom -- never
    MAY_OCCUR_WITH/STRONGLY_ASSOCIATED_WITH/APPLIES_TO, which would imply
    the deficit is currently active just because a stroke occurred in the
    past."""
    stroke = built_state[STROKE]
    historical = _variant(db_session, stroke, "DISEASE_PHASE", "Historical Stroke")
    edges = (
        db_session.query(OntologyConceptVariantApplicability)
        .filter_by(variant_id=historical.id)
        .all()
    )
    assert len(edges) > 0
    for edge in edges:
        assert edge.applicability_type == "SUPPORTS_DIFFERENTIATION"

    residual = _variant(db_session, stroke, "RESIDUAL_DEFICIT_STATE", "Residual Deficit Following Stroke")
    residual_edges = (
        db_session.query(OntologyConceptVariantApplicability).filter_by(variant_id=residual.id).all()
    )
    assert any(e.applicability_type == "MAY_OCCUR_WITH" for e in residual_edges)


def test_locked_in_syndrome_never_conflated_with_coma(db_session, built_state):
    stroke = built_state[STROKE]
    coma = _variant(db_session, stroke, "PHYSIOLOGICAL_PHENOTYPE", "Coma")
    locked_in = _variant(db_session, stroke, "PHYSIOLOGICAL_PHENOTYPE", "Locked-In Syndrome")
    assert coma.id != locked_in.id
    assert coma.parent_variant_id != locked_in.id
    assert locked_in.parent_variant_id != coma.id

    locked_in_edges = (
        db_session.query(OntologyConceptVariantApplicability).filter_by(variant_id=locked_in.id).all()
    )
    assert any(e.applicability_type == "SUPPORTS_DIFFERENTIATION" for e in locked_in_edges), (
        "Locked-In Syndrome must carry differentiation knowledge distinguishing it from coma"
    )


def test_hemiplegia_and_hemiparesis_remain_distinct(db_session, built_state):
    hemiplegia = built_state[HEMIPLEGIA]
    hemiparesis = built_state[HEMIPARESIS]
    assert hemiplegia.id != hemiparesis.id

    differentiation = _variant(db_session, hemiparesis, "SEVERITY_CLASS", "Hemiplegia Differentiation")
    edges = (
        db_session.query(OntologyConceptVariantApplicability).filter_by(variant_id=differentiation.id).all()
    )
    assert any(e.applicability_type == "SUPPORTS_DIFFERENTIATION" for e in edges)

    # Hemiplegia and Hemiparesis each have their own independent laterality
    # variants -- never a single shared variant row across both diseases.
    left_hemiplegia = _variant(db_session, hemiplegia, "LATERALITY", "Left Hemiplegia")
    left_hemiparesis = _variant(db_session, hemiparesis, "LATERALITY", "Left Hemiparesis")
    assert left_hemiplegia.disease_id == hemiplegia.id
    assert left_hemiparesis.disease_id == hemiparesis.id
    assert left_hemiplegia.id != left_hemiparesis.id


def test_senile_degeneration_of_brain_remains_distinct_from_alzheimers(db_session, built_state):
    sdb = built_state[SDB]
    alz = built_state[ALZ]
    assert sdb.id != alz.id

    sdb_alz_diff = _variant(db_session, sdb, "PATHOLOGICAL_SUBTYPE", "Alzheimer's Differentiation")
    edges = (
        db_session.query(OntologyConceptVariantApplicability).filter_by(variant_id=sdb_alz_diff.id).all()
    )
    assert len(edges) > 0
    for edge in edges:
        assert edge.applicability_type == "SUPPORTS_DIFFERENTIATION"

    # No SDB variant is ever linked, via applicability, to an Alzheimer's-
    # specific FAST-stage finding (those FINDING rows only exist under ALZ's
    # own disease_id, so this also confirms no cross-disease concept_id
    # leakage occurred).
    sdb_variant_ids = {
        v.id for v in db_session.query(OntologyDiseaseVariant).filter_by(disease_id=sdb.id).all()
    }
    edges_for_sdb = (
        db_session.query(OntologyConceptVariantApplicability)
        .filter(OntologyConceptVariantApplicability.variant_id.in_(sdb_variant_ids))
        .all()
    )
    assert all(e.disease_id == sdb.id for e in edges_for_sdb)

    # No END_STAGE_SUPPORT_FOR/HOSPICE_SUPPORT_FOR applicability edge on any
    # SDB variant ever cites Alzheimer-specific FAST-stage language.
    for e in edges_for_sdb:
        assert "fast stage" not in (e.description or "").lower()


def test_no_duplicate_variant_within_disease_and_dimension(db_session, built_state):
    for disease in built_state.values():
        variants = db_session.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).all()
        seen = set()
        for v in variants:
            key = (v.variant_dimension, v.normalized_name)
            assert key not in seen, f"duplicate variant {key} for disease {disease.disease_name}"
            seen.add(key)


def test_no_duplicate_applicability_edge(db_session, built_state):
    disease_ids = [d.id for d in built_state.values()]
    edges = (
        db_session.query(OntologyConceptVariantApplicability)
        .filter(OntologyConceptVariantApplicability.disease_id.in_(disease_ids))
        .all()
    )
    seen = set()
    for e in edges:
        key = (e.concept_type, e.concept_id, e.variant_id, e.applicability_type)
        assert key not in seen, f"duplicate applicability edge {key}"
        seen.add(key)


def test_every_active_variant_has_an_evidence_rule_requiring_evidence(db_session, built_state):
    disease_ids = [d.id for d in built_state.values()]
    variants = (
        db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(disease_ids), OntologyDiseaseVariant.active.is_(True))
        .all()
    )
    assert len(variants) > 0
    for variant in variants:
        rule = (
            db_session.query(OntologyEvidenceRule)
            .filter_by(concept_type="DISEASE_VARIANT", concept_id=variant.id)
            .one_or_none()
        )
        assert rule is not None, f"missing evidence rule for variant {variant.variant_name}"
        assert rule.patient_fact_requires_evidence is True


def test_contracture_anatomical_and_severity_variants_present(db_session, built_state):
    contracture = built_state[CONTRACTURE]
    fixed = _variant(db_session, contracture, "SEVERITY_CLASS", "Fixed Contracture")
    hip = _variant(db_session, contracture, "ANATOMICAL_LOCATION", "Hip Contracture")
    assert fixed.disease_id == contracture.id
    assert hip.disease_id == contracture.id
    assert fixed.id != hip.id


def test_second_run_creates_zero_new_rows(db_session, built_state):
    """Idempotency: running the population function a second time against
    the same session must insert nothing new anywhere."""
    counts = run_clinical_reasoning_script(db_session)
    db_session.commit()
    assert counts["new_symptoms_inserted"] == 0
    assert counts["new_findings_inserted"] == 0
    assert counts["new_complications_inserted"] == 0
    assert counts["variants_inserted"] == 0
    assert counts["applicability_edges_inserted"] == 0
    assert counts["variant_evidence_rules_inserted"] == 0
    assert counts["concept_evidence_rules_inserted"] == 0
    assert counts["unresolved_applicability_defs"] == []


def test_export_file_is_generated_from_the_database(db_session, built_state, tmp_path):
    """The acceptance export must be produced by reading the populated
    database (never hand-authored) and written to disk as valid JSON."""
    target = tmp_path / "neurologic_five_tier_acceptance_baseline.json"
    written_path = write_acceptance_baseline_export(db_session, path=target)
    assert written_path == target
    assert target.exists()
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["tier4_variant_count"] > 0
    assert payload["tier5_applicability_count"] > 0


def test_export_contains_all_six_neurologic_diseases(db_session, built_state):
    payload = export_five_tier_acceptance_baseline(db_session)
    assert set(payload["diseases"]) == set(ALL_DISEASE_NAMES)


def test_export_contains_every_tier4_variant(db_session, built_state):
    payload = export_five_tier_acceptance_baseline(db_session)
    disease_ids = [d.id for d in built_state.values()]
    db_variant_count = (
        db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(disease_ids))
        .count()
    )
    assert db_variant_count == 122
    assert payload["tier4_variant_count"] == db_variant_count
    assert len(payload["variants"]) == db_variant_count


def test_export_contains_every_tier5_applicability_row(db_session, built_state):
    payload = export_five_tier_acceptance_baseline(db_session)
    disease_ids = [d.id for d in built_state.values()]
    db_edge_count = (
        db_session.query(OntologyConceptVariantApplicability)
        .filter(OntologyConceptVariantApplicability.disease_id.in_(disease_ids))
        .count()
    )
    assert db_edge_count >= 150
    assert payload["tier5_applicability_count"] == db_edge_count
    assert len(payload["applicability"]) == db_edge_count


def test_export_every_applicability_row_resolves_to_an_existing_concept(db_session, built_state):
    payload = export_five_tier_acceptance_baseline(db_session)
    unresolved = [e for e in payload["applicability"] if e["concept_name"] is None]
    assert unresolved == [], f"applicability rows with unresolved concept names: {unresolved}"


def test_export_every_variant_resolves_to_an_existing_canonical_disease(db_session, built_state):
    payload = export_five_tier_acceptance_baseline(db_session)
    valid_disease_ids = {str(d.id) for d in built_state.values()}
    bad = [v for v in payload["variants"] if v["disease_id"] not in valid_disease_ids]
    assert bad == [], f"variants with an unresolvable disease_id: {bad}"


def test_export_recursive_parent_paths_contain_no_cycle(db_session, built_state):
    """Walk each variant's parent_variant_id chain directly against the
    database (independent of the export's own cycle-breaking logic) and
    assert no variant id ever repeats -- a repeat would indicate a cycle."""
    disease_ids = [d.id for d in built_state.values()]
    all_variants = (
        db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(disease_ids))
        .all()
    )
    by_id = {v.id: v for v in all_variants}
    for variant in all_variants:
        seen = set()
        current = variant
        while current is not None:
            assert current.id not in seen, f"cycle detected reaching variant {variant.variant_name}"
            seen.add(current.id)
            current = by_id.get(current.parent_variant_id) if current.parent_variant_id else None
        assert len(seen) < 10, "unexpectedly deep parent chain -- possible undetected cycle"


def test_export_has_no_orphan_tier4_variant(db_session, built_state):
    """Every variant's parent_variant_id (when set) must reference another
    variant that actually exists, and every variant's disease_id must
    reference one of the six approved diseases -- no orphans."""
    disease_ids = {d.id for d in built_state.values()}
    all_variants = (
        db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(disease_ids))
        .all()
    )
    all_variant_ids = {v.id for v in all_variants}
    for variant in all_variants:
        assert variant.disease_id in disease_ids
        if variant.parent_variant_id is not None:
            assert variant.parent_variant_id in all_variant_ids, (
                f"orphan variant: {variant.variant_name} references a missing parent"
            )


def test_export_has_no_orphan_tier5_applicability_row(db_session, built_state):
    """Every applicability edge's variant_id must reference an existing
    Tier 4 variant row -- no orphans."""
    disease_ids = [d.id for d in built_state.values()]
    all_variant_ids = {
        v.id
        for v in db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(disease_ids))
        .all()
    }
    all_edges = (
        db_session.query(OntologyConceptVariantApplicability)
        .filter(OntologyConceptVariantApplicability.disease_id.in_(disease_ids))
        .all()
    )
    for edge in all_edges:
        assert edge.variant_id in all_variant_ids, f"orphan applicability edge {edge.id}"


def test_export_paths_contain_all_five_tiers(db_session, built_state):
    payload = export_five_tier_acceptance_baseline(db_session)
    for variant in payload["variants"]:
        # [Body System, Disease Family, Canonical Disease, ...variant chain]
        assert len(variant["path"]) >= 3
    for edge in payload["applicability"]:
        # [Body System, Disease Family, Canonical Disease, ...variant chain,
        #  Tier 5 Domain, Tier 5 Concept Name]
        assert len(edge["path"]) >= 5
        assert edge["path"][-2] == edge["concept_type"]
        assert edge["path"][-1] == edge["concept_name"]


def test_export_senile_degeneration_of_brain_remains_distinct_from_alzheimers(db_session, built_state):
    payload = export_five_tier_acceptance_baseline(db_session)
    sdb_variant_ids = {v["id"] for v in payload["variants"] if v["disease_id"] == str(built_state[SDB].id)}
    alz_variant_ids = {v["id"] for v in payload["variants"] if v["disease_id"] == str(built_state[ALZ].id)}
    assert sdb_variant_ids.isdisjoint(alz_variant_ids)

    # Structural check (not narrative-prose matching): no applicability row
    # attached to a Senile Degeneration of Brain variant may reference a
    # concept whose *name* is itself Alzheimer/FAST-branded (e.g. a "FAST
    # Stage 7" concept), and no HOSPICE_SUPPORT_FOR edge attached to SDB may
    # point at a concept that is exclusively an Alzheimer's-branded concept.
    forbidden_concept_name_markers = ("FAST Stage", "Alzheimer")
    sdb_edges = [e for e in payload["applicability"] if e["variant_id"] in sdb_variant_ids]
    for edge in sdb_edges:
        concept_name = edge["concept_name"] or ""
        for marker in forbidden_concept_name_markers:
            assert marker not in concept_name, (
                f"Alzheimer/FAST-stage concept name leaked into a Senile Degeneration of Brain "
                f"applicability row: {edge}"
            )


def test_export_hemorrhagic_stroke_has_no_thrombolysis_applicability(db_session, built_state):
    payload = export_five_tier_acceptance_baseline(db_session)
    stroke_id = str(built_state[STROKE].id)
    hemorrhagic_variant_ids = {
        v["id"]
        for v in payload["variants"]
        if v["disease_id"] == stroke_id and "Hemorrhagic" in v["variant_name"]
    }
    assert hemorrhagic_variant_ids, "expected at least one Hemorrhagic Stroke variant in the export"
    offending = [
        e
        for e in payload["applicability"]
        if e["variant_id"] in hemorrhagic_variant_ids
        and e["concept_name"] == "Thrombolytic Therapy"
        and e["applicability_type"] != "CONTRAINDICATED_FOR"
    ]
    assert offending == [], f"hemorrhagic stroke must never carry non-contraindicated thrombolysis applicability: {offending}"


def test_export_locked_in_syndrome_remains_distinct_from_coma(db_session, built_state):
    payload = export_five_tier_acceptance_baseline(db_session)
    stroke_id = str(built_state[STROKE].id)
    phenotype_variants = {
        v["variant_name"]
        for v in payload["variants"]
        if v["disease_id"] == stroke_id and v["variant_dimension"] == "PHYSIOLOGICAL_PHENOTYPE"
    }
    assert "Locked-In Syndrome" in phenotype_variants
    assert "Coma" in phenotype_variants
    locked_in_ids = {
        v["id"]
        for v in payload["variants"]
        if v["disease_id"] == stroke_id and v["variant_name"] == "Locked-In Syndrome"
    }
    coma_ids = {
        v["id"]
        for v in payload["variants"]
        if v["disease_id"] == stroke_id and v["variant_name"] == "Coma"
    }
    assert locked_in_ids.isdisjoint(coma_ids)


def test_no_other_body_system_touched(db_session, built_state):
    """Only the Neurologic body system's diseases may gain Tier 4/5 rows;
    every other body system's disease set must be completely untouched by
    this build."""
    neuro_system_id = built_state[STROKE].disease_family.body_system_id
    other_system_disease_ids = {
        d.id
        for d in db_session.query(OntologyDisease).all()
        if d.disease_family.body_system_id != neuro_system_id
    }
    if not other_system_disease_ids:
        pytest.skip("no other body system present in this database to assert against")
    variant_rows = (
        db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(other_system_disease_ids))
        .count()
    )
    assert variant_rows == 0


def test_only_authorized_files_changed():
    """This PR may only touch: the ORM model file (Tier 4/5 classes), the
    one forward-only Alembic migration, the population script, and its test
    file -- never patients.py or any other unrelated workspace file."""
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
        "backend/app/models/ontology_disease_blueprint.py",
        "backend/scripts/complete_ontology_neurologic_clinical_reasoning.py",
        "backend/tests/test_ontology_neurologic_clinical_reasoning.py",
        "backend/artifacts/neurologic_five_tier_acceptance_baseline.json",
    )
    allowed_prefixes = ("backend/alembic/versions/",)
    disallowed = [
        path for path in changed
        if not path.endswith(allowed_suffixes) and not path.startswith(allowed_prefixes)
    ]
    assert disallowed == [], f"unauthorized files changed: {disallowed}"
