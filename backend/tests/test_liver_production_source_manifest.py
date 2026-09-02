# tests/test_liver_production_source_manifest.py
"""Targeted tests for the source-faithful Liver Production Source Manifest v1
import (`import_liver_production_source_manifest.py`, PR #41).

This manifest is the sole authoritative source for this build -- every
assertion below is derived directly from the committed manifest file
(`backend/manifests/liver_production_source_manifest_v1.json`), never
from clinical judgment, inference, or a "similar enough" substitute.

End Stage Liver Disease (ESLD) and Chronic Liver Disease (CLD) are
distinct canonical diseases. Exact source-faithful findings/complications
(Prolonged Prothrombin Time, Elevated INR, Low Serum Albumin, Refractory
Ascites, Spontaneous Bacterial Peritonitis, Hepatorenal Syndrome, Hepatic
Encephalopathy, Recurrent Variceal Bleeding) are stored as their own
concepts and never collapsed into generic findings (Abnormal Liver
Function Tests, Ascites), which are retained only as
GENERAL_CLINICAL_KNOWLEDGE and never receive HOSPICE_SUPPORT_FOR
applicability. Non-disease-specific decline indicators (KPS/PPS/ADL/
functional/nutritional decline, weight loss) are retained as
LCD_NON_DISEASE_SPECIFIC and explicitly do not, by themselves, establish
hospice eligibility. A bare diagnosis-only DISEASE_PHASE variant for
each disease never receives HOSPICE_SUPPORT_FOR applicability -- only
the terminal/decompensated phase does.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
)
from scripts.import_liver_production_source_manifest import (
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
ESLD = "End Stage Liver Disease"
CLD = "Chronic Liver Disease"


@pytest.fixture(scope="module")
def built_state():
    """Import the Liver Production Source Manifest v1 into a dedicated
    session against the test database, exactly once for this file
    (module-scoped -- ontology tables are not tenant-scoped and are
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
    assert {d["disease"] for d in MANIFEST["diseases"]} == {ESLD, CLD}


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
    for name in ("KPS Less Than 70 Percent", "PPS Less Than 70 Percent", "ADL Dependence"):
        assert name not in variant_names


# --- exact source-faithful concepts vs generic substitutes ---

def test_exact_findings_are_not_collapsed_into_generic_liver_function_tests():
    for disease_name in (ESLD, CLD):
        generic = _find_concept_entry(disease_name, "FINDING", "Abnormal Liver Function Tests")
        assert generic is not None
        assert generic["source_classification"] == "GENERAL_CLINICAL_KNOWLEDGE"
        assert generic["hospice_support_eligible"] is False
        for exact_name in ("Prolonged Prothrombin Time", "Elevated INR", "Low Serum Albumin"):
            exact = _find_concept_entry(disease_name, "FINDING", exact_name)
            assert exact is not None
            assert exact["source_classification"] == "LCD_DISEASE_SPECIFIC"
            assert exact["hospice_support_eligible"] is True


def test_refractory_ascites_is_not_collapsed_into_generic_ascites():
    for disease_name in (ESLD, CLD):
        exact = _find_concept_entry(disease_name, "COMPLICATION", "Refractory Ascites")
        generic = _find_concept_entry(disease_name, "COMPLICATION", "Ascites")
        assert exact is not None and generic is not None
        assert exact["source_classification"] == "LCD_DISEASE_SPECIFIC"
        assert generic["source_classification"] == "GENERAL_CLINICAL_KNOWLEDGE"
        assert generic["hospice_support_eligible"] is False


def test_end_stage_liver_disease_is_a_dual_domain_concept_not_a_duplicate():
    """'End Stage Liver Disease' exists both as the disease itself and as
    a distinct HOSPICE_ELIGIBILITY_SUPPORT diagnosis-support concept
    attached to both diseases -- these are deliberately dual-domain, not
    merged into one atomic concept."""
    for disease_name in (ESLD, CLD):
        entry = _find_concept_entry(disease_name, "HOSPICE_ELIGIBILITY_SUPPORT", "End Stage Liver Disease")
        assert entry is not None
        assert "decompensation_evidence" in entry["evidence_requirements"]


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
    """Critical LCD rule: liver diagnosis alone is insufficient -- every
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


# --- non-disease-specific baseline never independently establishes eligibility ---

def test_non_disease_specific_concepts_are_classified_and_limited(db_session, built_state):
    non_disease_names = [
        "KPS Less Than 70 Percent", "PPS Less Than 70 Percent", "ADL Dependence",
        "Progressive Functional Decline", "Progressive Nutritional Decline", "Weight Loss",
    ]
    checked = 0
    for disease_name in (ESLD, CLD):
        for name in non_disease_names:
            entry = _find_concept_entry(disease_name, "HOSPICE_ELIGIBILITY_SUPPORT", name)
            assert entry is not None, f"missing non-disease-specific concept {disease_name}/{name}"
            assert entry["source_classification"] == "LCD_NON_DISEASE_SPECIFIC"
            assert "does not independently establish" in entry["description"].lower()
            checked += 1
    assert checked == len(non_disease_names) * 2


def test_diagnosis_alone_never_establishes_terminal_prognosis(db_session, built_state):
    """The bare DISEASE_PHASE variant representing diagnosis-only status
    (named identically to the disease itself) must never carry any
    HOSPICE_SUPPORT_FOR applicability -- only the terminal/decompensated
    phase does."""
    diseases = built_state["diseases"]
    for disease_name, bare_variant_name in ((ESLD, "End Stage Liver Disease"), (CLD, "Chronic Liver Disease")):
        base_variant = _variant(db_session, diseases[disease_name], "DISEASE_PHASE", bare_variant_name)
        assert base_variant is not None
        edges = (
            db_session.query(OntologyConceptVariantApplicability)
            .filter_by(variant_id=base_variant.id, applicability_type="HOSPICE_SUPPORT_FOR")
            .all()
        )
        assert edges == []


def test_unsupported_general_concepts_never_receive_hospice_support_applicability():
    general_names = {"Abnormal Liver Function Tests", "Ascites"}
    for disease_name, a in _manifest_applicability():
        if a["concept"] in general_names:
            assert a["applicability_type"] != "HOSPICE_SUPPORT_FOR", (
                f"{a['concept']} is GENERAL_CLINICAL_KNOWLEDGE and must never receive HOSPICE_SUPPORT_FOR"
            )


# --- differentiation guards from the manifest itself ---

def test_end_stage_and_chronic_liver_disease_remain_distinct(built_state):
    diseases = built_state["diseases"]
    assert diseases[ESLD].id != diseases[CLD].id


def test_every_manifest_guard_passes():
    """Import once and confirm build_acceptance_report reports every
    declared differentiation guard as passed."""
    from scripts.import_liver_production_source_manifest import build_acceptance_report

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
        pytest.skip("no non-Liver diseases present in this database")
    touched = (
        db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(other_disease_ids))
        .filter(OntologyDiseaseVariant.source_reference == "liver_production_source_manifest_v1")
        .count()
    )
    assert touched == 0


# --- no unrelated files change ---

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
        "backend/manifests/liver_production_source_manifest_v1.json",
        "backend/scripts/import_liver_production_source_manifest.py",
        "backend/tests/test_liver_production_source_manifest.py",
        "backend/artifacts/liver_production_manifest_acceptance_v1.json",
    )
    disallowed = [path for path in changed if not path.endswith(allowed_suffixes)]
    assert disallowed == [], f"unauthorized files changed: {disallowed}"
