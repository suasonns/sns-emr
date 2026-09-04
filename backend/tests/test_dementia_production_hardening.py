# tests/test_dementia_production_hardening.py
"""Targeted tests for the source-faithful Dementia Production Hardening v1
import (`import_dementia_production_hardening.py`, PR #44).

This manifest is the sole authoritative source for this build -- every
assertion below is derived directly from the committed manifest file
(`backend/manifests/dementia_production_hardening_v1.json`), never from
clinical judgment, inference, or a "similar enough" substitute.

Dementia Due To Alzheimer's Disease is the single canonical disease
hardened by this PR. This is a *hardening* of the pre-existing PR #37
Neurologic manifest content, not a redesign: the disease, body system
("Neurologic System"), and family ("Degenerative Brain Disorders")
already exist once PR #37 is merged, and this importer resolves and
reuses them unchanged rather than re-creating or renaming anything.
Nothing from PR #37 is deleted, deactivated, or modified.

The 16 exact source-faithful concepts (FAST Stage 7, Unable To
Ambulate/Dress/Bathe Without Assistance, Urinary Incontinence, Fecal
Incontinence, No Consistently Meaningful Verbal Communication, Aspiration
Pneumonia, Pyelonephritis, Upper Urinary Tract Infection, Septicemia,
Stage 3/4 Pressure Ulcer, Recurrent Fever After Antibiotics, Ten Percent
Weight Loss In Six Months, Serum Albumin Less Than 2.5 g/dL) are stored
separately -- never collapsed into each other or into a combined/generic
substitute (e.g. Urinary Incontinence and Fecal Incontinence remain
distinct, never merged into a single "urinary and fecal incontinence"
concept; Pyelonephritis and Upper Urinary Tract Infection remain
distinct; Stage 3 and Stage 4 Pressure Ulcer remain distinct). Per the
CMS Dementia LCD, every one of these 16 exact findings is itself a
qualifying hospice-eligibility criterion, so each also carries a
dual-domain HOSPICE_ELIGIBILITY_SUPPORT entry, classified
LCD_DISEASE_SPECIFIC. Non-disease-specific decline indicators (KPS/PPS/
ADL/functional decline) are retained as LCD_NON_DISEASE_SPECIFIC and
explicitly do not, by themselves, establish hospice eligibility. A bare
diagnosis-only DISEASE_PHASE variant never receives HOSPICE_SUPPORT_FOR
applicability -- only the FAST Stage 7 variant does. The Serum Albumin
concept requires laboratory_name/laboratory_value/laboratory_unit/
laboratory_date/source_record evidence and is never inferred.
"""
from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
)
from scripts.import_dementia_production_hardening import (
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
DEMENTIA = "Dementia Due To Alzheimer's Disease"
FAST_STAGE_7 = "FAST Stage 7"

FUNCTIONAL_EVIDENCE_FIELDS = {"functional_assessment", "date", "source_record"}
COMORBIDITY_EVIDENCE_FIELDS = {"diagnosis_date", "source_record"}
NUTRITIONAL_EVIDENCE_FIELDS = {"weight_data", "date", "source_record"}
LABORATORY_EVIDENCE_FIELDS = {
    "laboratory_name", "laboratory_value", "laboratory_unit", "laboratory_date", "source_record",
}

EXACT_CONCEPT_DOMAINS = {
    "FAST Stage 7": "FINDING",
    "Unable To Ambulate Without Assistance": "FUNCTIONAL_IMPACT",
    "Unable To Dress Without Assistance": "FUNCTIONAL_IMPACT",
    "Unable To Bathe Without Assistance": "FUNCTIONAL_IMPACT",
    "Urinary Incontinence": "FUNCTIONAL_IMPACT",
    "Fecal Incontinence": "FUNCTIONAL_IMPACT",
    "No Consistently Meaningful Verbal Communication": "FINDING",
    "Aspiration Pneumonia": "COMPLICATION",
    "Pyelonephritis": "COMPLICATION",
    "Upper Urinary Tract Infection": "COMPLICATION",
    "Septicemia": "COMPLICATION",
    "Stage 3 Pressure Ulcer": "END_STAGE_FINDING",
    "Stage 4 Pressure Ulcer": "END_STAGE_FINDING",
    "Recurrent Fever After Antibiotics": "COMPLICATION",
    "Ten Percent Weight Loss In Six Months": "NUTRITIONAL_IMPACT",
    "Serum Albumin Less Than 2.5 g/dL": "LAB",
}

NON_DISEASE_SPECIFIC_NAMES = [
    "KPS Less Than 70 Percent", "PPS Less Than 70 Percent",
    "ADL Dependence", "Progressive Functional Decline",
]


@pytest.fixture(scope="module")
def built_state():
    """Import the Dementia Production Hardening v1 manifest into a
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

def test_manifest_declares_a_single_canonical_disease():
    assert {d["disease"] for d in MANIFEST["diseases"]} == {DEMENTIA}


def test_manifest_declares_exact_summary_counts():
    summary = MANIFEST["summary"]
    assert summary["canonical_diseases"] == 1
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


def test_no_unsupported_variants_manufactured():
    """Only DISEASE_PHASE (diagnosis-only) and STAGE (FAST Stage 7)
    variants are declared -- this is a targeted hardening, not a full
    staging-ladder redesign; the mild/moderate/severe/FAST-1..6 variants
    already established by PR #37 are intentionally left untouched."""
    dimensions_used = {v["dimension"] for d in MANIFEST["diseases"] for v in d.get("variants", [])}
    assert dimensions_used == {"DISEASE_PHASE", "STAGE"}


def test_exact_source_concepts_cover_every_required_name():
    for name in EXACT_CONCEPT_DOMAINS:
        entry = _find_concept_entry(DEMENTIA, EXACT_CONCEPT_DOMAINS[name], name)
        assert entry is not None, f"missing required exact concept {name}"
        assert entry["source_classification"] == "LCD_DISEASE_SPECIFIC"


# --- 1. Dementia pathway remains distinct (single disease sanity) ---

def test_dementia_pathway_remains_distinct(built_state):
    diseases = built_state["diseases"]
    assert DEMENTIA in diseases
    assert len(diseases) == 1


# --- exact source-faithful concepts never collapsed into each other ---

def test_urinary_and_fecal_incontinence_remain_distinct():
    urinary = _find_concept_entry(DEMENTIA, "FUNCTIONAL_IMPACT", "Urinary Incontinence")
    fecal = _find_concept_entry(DEMENTIA, "FUNCTIONAL_IMPACT", "Fecal Incontinence")
    assert urinary is not None and fecal is not None
    assert id(urinary) != id(fecal)


def test_pyelonephritis_and_upper_uti_remain_distinct():
    pyelo = _find_concept_entry(DEMENTIA, "COMPLICATION", "Pyelonephritis")
    uti = _find_concept_entry(DEMENTIA, "COMPLICATION", "Upper Urinary Tract Infection")
    assert pyelo is not None and uti is not None
    assert id(pyelo) != id(uti)


def test_stage_3_and_stage_4_pressure_ulcer_remain_distinct():
    stage3 = _find_concept_entry(DEMENTIA, "END_STAGE_FINDING", "Stage 3 Pressure Ulcer")
    stage4 = _find_concept_entry(DEMENTIA, "END_STAGE_FINDING", "Stage 4 Pressure Ulcer")
    assert stage3 is not None and stage4 is not None
    assert id(stage3) != id(stage4)


def test_exact_concepts_are_never_replaced_with_generic_equivalents():
    """The manifest must never substitute a generic/collapsed finding
    (e.g. a combined 'Urinary and Fecal Incontinence' or a bare
    'Elevated Serum Creatinine'-style generic threshold) for any of the
    16 exact LCD concepts -- every name below must be present verbatim."""
    for name, domain in EXACT_CONCEPT_DOMAINS.items():
        assert _find_concept_entry(DEMENTIA, domain, name) is not None, f"missing exact concept: {name}"
    assert _find_concept_entry(DEMENTIA, "FUNCTIONAL_IMPACT", "Urinary and Fecal Incontinence") is None
    assert _find_concept_entry(DEMENTIA, "COMPLICATION", "Pyelonephritis or Upper Urinary Tract Infection") is None


# --- functional/dependency findings require evidence ---

def test_fast_and_dependency_findings_require_functional_evidence():
    fast_and_dependency_names = [
        "FAST Stage 7", "Unable To Ambulate Without Assistance", "Unable To Dress Without Assistance",
        "Unable To Bathe Without Assistance", "Urinary Incontinence", "Fecal Incontinence",
        "No Consistently Meaningful Verbal Communication",
    ]
    for name in fast_and_dependency_names:
        domain = EXACT_CONCEPT_DOMAINS[name]
        entry = _find_concept_entry(DEMENTIA, domain, name)
        assert entry is not None
        reqs = set(entry.get("evidence_requirements") or [])
        assert FUNCTIONAL_EVIDENCE_FIELDS <= reqs, f"missing functional evidence fields for {name}"


# --- comorbidity findings require evidence ---

def test_comorbidity_findings_require_diagnosis_evidence():
    comorbidity_names = [
        "Aspiration Pneumonia", "Pyelonephritis", "Upper Urinary Tract Infection", "Septicemia",
        "Stage 3 Pressure Ulcer", "Stage 4 Pressure Ulcer", "Recurrent Fever After Antibiotics",
    ]
    for name in comorbidity_names:
        domain = EXACT_CONCEPT_DOMAINS[name]
        entry = _find_concept_entry(DEMENTIA, domain, name)
        assert entry is not None
        reqs = set(entry.get("evidence_requirements") or [])
        assert COMORBIDITY_EVIDENCE_FIELDS <= reqs, f"missing comorbidity evidence fields for {name}"


# --- nutritional decline requires evidence ---

def test_weight_loss_finding_requires_nutritional_evidence():
    entry = _find_concept_entry(DEMENTIA, "NUTRITIONAL_IMPACT", "Ten Percent Weight Loss In Six Months")
    assert entry is not None
    reqs = set(entry.get("evidence_requirements") or [])
    assert NUTRITIONAL_EVIDENCE_FIELDS <= reqs


# --- albumin threshold requires laboratory evidence ---

def test_serum_albumin_concept_requires_laboratory_evidence():
    """Laboratory-derived thresholds are never inferred -- the Serum
    Albumin concept must require the full laboratory evidence tuple."""
    entry = _find_concept_entry(DEMENTIA, "LAB", "Serum Albumin Less Than 2.5 g/dL")
    assert entry is not None
    reqs = set(entry.get("evidence_requirements") or [])
    assert LABORATORY_EVIDENCE_FIELDS <= reqs


def test_generic_lab_or_functional_language_does_not_satisfy_exact_lcd_threshold():
    """A generic 'low albumin' or 'weight loss' statement must never be
    treated as equivalent to the exact LCD-threshold concept names."""
    assert _find_concept_entry(DEMENTIA, "LAB", "Low Serum Albumin") is None
    assert _find_concept_entry(DEMENTIA, "NUTRITIONAL_IMPACT", "Weight Loss") is None


# --- diagnosis alone never establishes prognosis ---

def test_diagnosis_alone_never_establishes_terminal_prognosis(db_session, built_state):
    """The bare DISEASE_PHASE variant representing diagnosis-only status
    must never carry any HOSPICE_SUPPORT_FOR applicability -- only the
    FAST Stage 7 variant does."""
    diseases = built_state["diseases"]
    base_variant = _variant(db_session, diseases[DEMENTIA], "DISEASE_PHASE", DEMENTIA)
    assert base_variant is not None
    edges = (
        db_session.query(OntologyConceptVariantApplicability)
        .filter_by(variant_id=base_variant.id, applicability_type="HOSPICE_SUPPORT_FOR")
        .all()
    )
    assert edges == []


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


# --- every concept has source classification, provenance, and an
# evidence rule requiring patient-fact evidence ---

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
    assert checked == len(_manifest_concepts())


def test_hospice_eligibility_support_concepts_require_evidence(db_session, built_state):
    """Critical LCD rule: Dementia diagnosis alone is insufficient --
    every HOSPICE_ELIGIBILITY_SUPPORT concept must require evidence."""
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


# --- non-disease support cannot establish eligibility alone ---

def test_non_disease_specific_concepts_are_classified_and_limited():
    checked = 0
    for name in NON_DISEASE_SPECIFIC_NAMES:
        entry = _find_concept_entry(DEMENTIA, "HOSPICE_ELIGIBILITY_SUPPORT", name)
        assert entry is not None, f"missing non-disease-specific concept {name}"
        assert entry["source_classification"] == "LCD_NON_DISEASE_SPECIFIC"
        assert "does not independently establish" in entry["description"].lower() or "cannot independently establish" in entry["description"].lower()
        checked += 1
    assert checked == len(NON_DISEASE_SPECIFIC_NAMES)


def test_non_disease_specific_support_cannot_establish_eligibility_alone(db_session, built_state):
    """Non-disease-specific concepts must be reachable only through
    HOSPICE_SUPPORT_FOR applicability alongside disease-specific evidence
    on the same FAST Stage 7 variant -- never in isolation."""
    diseases = built_state["diseases"]
    non_disease_names = set(NON_DISEASE_SPECIFIC_NAMES)
    disease = diseases[DEMENTIA]
    fast7_variant = _variant(db_session, disease, "STAGE", FAST_STAGE_7)
    assert fast7_variant is not None
    edges = (
        db_session.query(OntologyConceptVariantApplicability)
        .filter_by(variant_id=fast7_variant.id, applicability_type="HOSPICE_SUPPORT_FOR")
        .all()
    )
    linked_names = set()
    for edge in edges:
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        concept_row = db_session.query(model_cls).filter_by(id=edge.concept_id).one_or_none()
        assert concept_row is not None
        linked_names.add(getattr(concept_row, name_attr))
    assert non_disease_names <= linked_names
    disease_specific_present = any(
        _find_concept_entry(DEMENTIA, "HOSPICE_ELIGIBILITY_SUPPORT", n)["source_classification"] == "LCD_DISEASE_SPECIFIC"
        for n in linked_names
        if n not in non_disease_names
    )
    assert disease_specific_present


def test_unsupported_general_concepts_never_receive_hospice_support_applicability():
    general_names = {"Low Serum Albumin", "Weight Loss", "Urinary and Fecal Incontinence"}
    for disease_name, a in _manifest_applicability():
        if a["concept"] in general_names:
            assert a["applicability_type"] != "HOSPICE_SUPPORT_FOR"


# --- differentiation guards from the manifest itself ---

def test_every_manifest_guard_passes():
    """Import once and confirm build_acceptance_report reports every
    declared differentiation guard as passed."""
    from scripts.import_dementia_production_hardening import build_acceptance_report

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


# --- zero orphan concepts, zero orphan applicability, zero cycles, zero
# unresolved concepts ---

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


# --- second execution creates zero rows ---

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
        pytest.skip("no non-Dementia diseases present in this database")
    touched = (
        db_session.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_(other_disease_ids))
        .filter(OntologyDiseaseVariant.source_reference == "dementia_production_hardening_v1")
        .count()
    )
    assert touched == 0


# Note: the former git-diff scope guard test has been removed. PR-scope
# validation now happens via the CI-only `backend/scripts/validate_pr_scope.py`
# tool against an explicit allowlist, not as a pytest test, because pytest
# results must never depend on git diff state.
