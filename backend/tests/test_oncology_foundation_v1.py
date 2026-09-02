# tests/test_oncology_foundation_v1.py
"""Targeted tests for the Oncology Foundation v1 import
(`import_oncology_foundation_v1.py`, PR #45).

This is a FOUNDATION build, not a disease-specific cancer manifest. Every
assertion below is derived directly from the committed manifest file
(`backend/manifests/oncology_foundation_v1.json`), never from clinical
judgment, inference, or a "similar enough" substitute.

The manifest establishes:
    - The "Oncology" body system / "Oncology Foundation" family, anchored
      by a single technical reference disease ("Oncology Foundation
      Reference Structure") that is NOT a diagnosable cancer.
    - 12 canonical PRIMARY_SITE variants (Breast, Lung, Prostate,
      Colorectal, Liver, Kidney, Thyroid, Pancreas, Bladder, Skin,
      Leukemia, Lymphoma).
    - 10 reusable Tier 5 atomic concepts (3 METASTASIS FINDING concepts, 3
      FUNCTIONAL_DECLINE concepts, 4 HOSPICE_SUPPORT concepts), each
      generically applicable to every PRIMARY_SITE variant.

No Stage I/II/III/IV variants, no histology-specific findings, and no
disease-specific cancer content are created by this PR -- that is
explicitly deferred to future disease-specific oncology manifests.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyDisease,
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
ANCHOR_DISEASE = "Oncology Foundation Reference Structure"

PRIMARY_SITES = [
    "Breast", "Lung", "Prostate", "Colorectal", "Liver", "Kidney",
    "Thyroid", "Pancreas", "Bladder", "Skin", "Leukemia", "Lymphoma",
]

METASTASIS_CONCEPTS = {"Metastatic Disease", "Regional Spread", "Distant Metastatic Disease"}
FUNCTIONAL_DECLINE_CONCEPTS = {
    "Progressive Functional Decline", "Progressive Nutritional Decline", "Weight Loss",
}
HOSPICE_SUPPORT_CONCEPTS = {
    "Progressive Disease", "Worsening Clinical Status", "Functional Impairment", "ADL Dependence",
}


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


def _find_concept_entry(disease_name, domain, name):
    for d_name, dom, n, entry in _manifest_concepts():
        if d_name == disease_name and dom == domain and n == name:
            return entry
    return None


# --- manifest self-consistency ---

def test_manifest_declares_a_single_anchor_disease():
    assert {d["disease"] for d in MANIFEST["diseases"]} == {ANCHOR_DISEASE}


def test_manifest_declares_exact_summary_counts():
    summary = MANIFEST["summary"]
    assert summary["canonical_diseases"] == 1
    assert summary["total_variants"] == len(_manifest_variants()) == 12
    assert summary["total_concepts"] == len(_manifest_concepts()) == 10
    assert summary["total_applicability_mappings"] == len(_manifest_applicability()) == 120


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


def test_no_unsupported_variants_manufactured():
    """Only PRIMARY_SITE variants are declared -- no STAGE, GRADE,
    HISTOLOGY, MOLECULAR_SUBTYPE, METASTATIC_STATE, or
    METASTATIC_DESTINATION variants are manufactured without explicit
    source support (foundation structure first, disease manifests
    later)."""
    dimensions_used = {v["dimension"] for d in MANIFEST["diseases"] for v in d.get("variants", [])}
    assert dimensions_used == {"PRIMARY_SITE"}


def test_no_cancer_stage_variants_invented():
    variant_names = {v["name"] for d in MANIFEST["diseases"] for v in d.get("variants", [])}
    for forbidden in ("Stage I", "Stage II", "Stage III", "Stage IV"):
        assert forbidden not in variant_names


def test_all_twelve_expected_primary_sites_declared():
    variant_names = {v["name"] for d in MANIFEST["diseases"] for v in d.get("variants", [])}
    assert variant_names == set(PRIMARY_SITES)


# --- 1. Foundation imports correctly ---

def test_foundation_imports_correctly(db_session, built_state):
    """Import succeeds and produces exactly the manifest's declared
    counts. Insertion counts from `built_state` alone are not asserted
    here because the shared test database may already carry a prior
    (idempotent) import from this same manifest -- the stored totals are
    the authoritative check."""
    diseases = built_state["diseases"]
    assert ANCHOR_DISEASE in diseases
    assert len(diseases) == 1
    disease = diseases[ANCHOR_DISEASE]
    stored_variants = db_session.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).count()
    assert stored_variants == 12
    stored_applicability = (
        db_session.query(OntologyConceptVariantApplicability).filter_by(disease_id=disease.id).count()
    )
    assert stored_applicability == 120


def test_oncology_body_system_and_family_created(db_session, built_state):
    from app.models.ontology_disease_blueprint import OntologyBodySystem, OntologyDiseaseFamily

    system = db_session.query(OntologyBodySystem).filter_by(system_name="Oncology").one_or_none()
    assert system is not None
    family = (
        db_session.query(OntologyDiseaseFamily)
        .filter_by(family_name="Oncology Foundation", body_system_id=system.id)
        .one_or_none()
    )
    assert family is not None


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


def test_each_foundation_concept_applies_to_every_primary_site(db_session, built_state):
    """Every one of the 10 reusable foundation concepts must generically
    apply to all 12 PRIMARY_SITE variants -- 10 x 12 = 120 mappings."""
    diseases = built_state["diseases"]
    disease = diseases[ANCHOR_DISEASE]
    for disease_name, domain, name, _entry in _manifest_concepts():
        concept = _concept(db_session, disease, domain, name)
        assert concept is not None
        edges = (
            db_session.query(OntologyConceptVariantApplicability)
            .filter_by(concept_id=concept.id, concept_type=domain)
            .all()
        )
        assert len(edges) == 12, f"expected 12 applicability edges for {name}, found {len(edges)}"


def test_nothing_is_blocked(built_state):
    counts = built_state["counts"]
    assert "variants_blocked" not in counts
    assert "concepts_blocked" not in counts
    assert "applicability_blocked" not in counts


# --- 2, 3, 4: every concept has provenance, evidence rule, classification ---

def test_every_imported_concept_has_source_classification_and_provenance():
    for disease_name, domain, name, entry in _manifest_concepts():
        assert entry.get("source_classification") in ALLOWED_SOURCE_CLASSIFICATIONS, (
            f"missing source classification for {disease_name}/{domain}/{name}"
        )
        assert entry.get("source_reference"), f"missing source provenance for {disease_name}/{domain}/{name}"


def test_every_imported_concept_has_an_evidence_rule_requiring_evidence(db_session, built_state):
    diseases = built_state["diseases"]
    checked = 0
    for disease_name, domain, name, _entry in _manifest_concepts():
        concept = _concept(db_session, diseases[disease_name], domain, name)
        rule = _evidence_rule(db_session, domain, concept.id)
        assert rule is not None, f"missing evidence rule for {disease_name}/{domain}/{name}"
        assert rule.patient_fact_requires_evidence is True
        checked += 1
    assert checked == len(_manifest_concepts()) == 10


# --- concept-group distinctness ---

def test_metastasis_concepts_remain_distinct_from_each_other(db_session, built_state):
    disease = built_state["diseases"][ANCHOR_DISEASE]
    ids = set()
    for name in METASTASIS_CONCEPTS:
        concept = _concept(db_session, disease, "FINDING", name)
        assert concept is not None, f"missing metastasis concept {name}"
        ids.add(concept.id)
    assert len(ids) == len(METASTASIS_CONCEPTS)


def test_hospice_support_concepts_remain_distinct_from_each_other(db_session, built_state):
    disease = built_state["diseases"][ANCHOR_DISEASE]
    ids = set()
    for name in HOSPICE_SUPPORT_CONCEPTS:
        concept = _concept(db_session, disease, "HOSPICE_ELIGIBILITY_SUPPORT", name)
        assert concept is not None, f"missing hospice support concept {name}"
        ids.add(concept.id)
    assert len(ids) == len(HOSPICE_SUPPORT_CONCEPTS)


def test_functional_decline_concepts_are_not_classified_as_hospice_support():
    """FUNCTIONAL_DECLINE concepts are reusable non-disease-specific
    findings, not themselves HOSPICE_ELIGIBILITY_SUPPORT concepts --
    that distinction belongs to disease-specific manifests, not the
    foundation."""
    for name in FUNCTIONAL_DECLINE_CONCEPTS:
        entry = None
        for domain in ("FUNCTIONAL_IMPACT", "NUTRITIONAL_IMPACT"):
            entry = _find_concept_entry(ANCHOR_DISEASE, domain, name)
            if entry is not None:
                break
        assert entry is not None, f"missing functional-decline concept {name}"
        assert entry["source_classification"] == "LCD_NON_DISEASE_SPECIFIC"
        assert entry["hospice_support_eligible"] is False


def test_no_variant_receives_hospice_support_applicability_from_non_eligible_concepts():
    """Only concepts explicitly marked hospice_support_eligible=true may
    ever receive HOSPICE_SUPPORT_FOR applicability."""
    eligible_names = {
        c["name"] for d in MANIFEST["diseases"] for c in d.get("concepts", [])
        if c.get("hospice_support_eligible") is True
    }
    for disease_name, a in _manifest_applicability():
        if a["applicability_type"] == "HOSPICE_SUPPORT_FOR":
            assert a["concept"] in eligible_names, (
                f"{a['concept']} received HOSPICE_SUPPORT_FOR without hospice_support_eligible=true"
            )


# --- differentiation guards from the manifest itself ---

def test_every_manifest_guard_passes():
    """Import once and confirm build_acceptance_report reports every
    declared differentiation guard as passed."""
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


# --- 5 & 6 & 7 & 8: zero orphan concepts, zero orphan applicability,
# zero cycles, zero unresolved concepts ---

def test_no_orphan_variant_exists(db_session, built_state):
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


# --- 9 & 10. Idempotent importer / second execution creates zero rows ---

def test_second_run_creates_zero_new_rows(db_session, built_state):
    counts = run_manifest_import(db_session, manifest=MANIFEST)
    db_session.commit()
    assert counts["variants_inserted"] == 0
    assert counts["concepts_inserted_total"] == 0
    assert counts["applicability_inserted"] == 0
    assert counts["evidence_rules_inserted"] == 0


# --- no changes to other body systems ---

def test_no_other_body_system_records_touched(db_session, built_state):
    other_disease_ids = {
        d.id for d in db_session.query(OntologyDisease).all()
        if d.disease_name not in ALL_DISEASE_NAMES
    }
    if not other_disease_ids:
        pytest.skip("no non-oncology diseases present in this database")
    touched = (
        db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(other_disease_ids))
        .filter(OntologyDiseaseVariant.source_reference == "oncology_foundation_v1")
        .count()
    )
    assert touched == 0


# --- 11. No unrelated files change ---

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
        "backend/manifests/oncology_foundation_v1.json",
        "backend/scripts/import_oncology_foundation_v1.py",
        "backend/tests/test_oncology_foundation_v1.py",
        "backend/artifacts/oncology_foundation_acceptance_v1.json",
    )
    disallowed = [path for path in changed if not path.endswith(allowed_suffixes)]
    assert disallowed == [], f"unauthorized files changed: {disallowed}"
