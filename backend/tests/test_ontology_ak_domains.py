"""Targeted tests for the ontology A-K domain E/H/J/K storage added in this
task: OntologyDiseaseTreatmentLimitation (E), OntologyDiseaseEndStageFinding
(H), OntologyEvidenceRule per-concept coverage (J), and
OntologyDiseaseValidationResult (K).

These tests are scoped strictly to the new/changed storage -- they do not
touch RNICA, patient APIs, assigned-RN logic, or any protected area.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyConceptVariantApplicability,
    OntologyDisease,
    OntologyDiseaseComplication,
    OntologyDiseaseEndStageFinding,
    OntologyDiseaseFamily,
    OntologyDiseaseFunctionalImpact,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseaseNutritionalImpact,
    OntologyDiseaseSymptom,
    OntologyDiseaseTreatmentLimitation,
    OntologyDiseaseValidationResult,
    OntologyEvidenceRule,
    OntologyRelationship,
)
from scripts.populate_ontology_ak_neuro_cardio import (
    APPROVED_DISEASE_NAMES,
    CONCEPT_DOMAINS,
    REQUIRED_VALIDATION_TYPES,
    _resolve_diseases,
    run as run_population_script,
)


@pytest.fixture()
def seeded_disease(db_session):
    """A minimal System -> Family -> Disease chain, isolated to this test."""
    suffix = uuid.uuid4().hex[:8]
    system = OntologyBodySystem(system_name=f"Test System {suffix}")
    db_session.add(system)
    db_session.flush()

    family = OntologyDiseaseFamily(body_system_id=system.id, family_name=f"Test Family {suffix}")
    db_session.add(family)
    db_session.flush()

    disease = OntologyDisease(disease_family_id=family.id, disease_name=f"Test Disease {suffix}")
    db_session.add(disease)
    db_session.commit()
    return disease


def test_treatment_limitation_stored_and_retrieved_by_disease(db_session, seeded_disease):
    row = OntologyDiseaseTreatmentLimitation(
        disease_id=seeded_disease.id,
        limitation_name="Not a Candidate for Revascularization",
        limitation_category="NOT_A_CANDIDATE",
        description="Not a surgical/interventional candidate.",
    )
    db_session.add(row)
    db_session.commit()

    fetched = (
        db_session.query(OntologyDiseaseTreatmentLimitation)
        .filter_by(disease_id=seeded_disease.id)
        .all()
    )
    assert len(fetched) == 1
    assert fetched[0].limitation_category == "NOT_A_CANDIDATE"


def test_end_stage_finding_stored_and_retrieved_by_disease(db_session, seeded_disease):
    row = OntologyDiseaseEndStageFinding(
        disease_id=seeded_disease.id,
        finding_name="Refractory Symptoms Despite Maximal Therapy",
        description="Symptoms uncontrolled despite optimal treatment.",
    )
    db_session.add(row)
    db_session.commit()

    fetched = (
        db_session.query(OntologyDiseaseEndStageFinding)
        .filter_by(disease_id=seeded_disease.id)
        .all()
    )
    assert len(fetched) == 1
    assert fetched[0].finding_name == "Refractory Symptoms Despite Maximal Therapy"


def test_evidence_rule_stored_and_retrieved_by_concept_and_category(db_session, seeded_disease):
    limitation = OntologyDiseaseTreatmentLimitation(
        disease_id=seeded_disease.id,
        limitation_name="Declined Further Treatment",
        limitation_category="TREATMENT_DECLINED",
    )
    db_session.add(limitation)
    db_session.flush()

    rule = OntologyEvidenceRule(
        concept_type="TREATMENT_LIMITATION",
        concept_id=limitation.id,
        evidence_source="Test LCD",
        evidence_type="TREATMENT_LIMITATION",
        confidence="moderate",
        review_trigger="RN_REVIEW",
    )
    db_session.add(rule)
    db_session.commit()

    fetched = (
        db_session.query(OntologyEvidenceRule)
        .filter_by(concept_type="TREATMENT_LIMITATION", concept_id=limitation.id)
        .one()
    )
    assert fetched.evidence_type == "TREATMENT_LIMITATION"
    assert fetched.evidence_source == "Test LCD"


def test_validation_result_persists_after_process_ends(db_session, seeded_disease):
    result = OntologyDiseaseValidationResult(
        disease_id=seeded_disease.id,
        validation_type="DUPLICATE",
        validation_status="PASS",
        details="No duplicates found.",
        error_count=0,
        warning_count=0,
        validator_version="v1",
    )
    db_session.add(result)
    db_session.commit()
    db_session.expunge_all()  # simulate the validation process/session ending

    fetched = (
        db_session.query(OntologyDiseaseValidationResult)
        .filter_by(disease_id=seeded_disease.id, validation_type="DUPLICATE")
        .one()
    )
    assert fetched.validation_status == "PASS"
    assert fetched.validated_at is not None


def test_foreign_key_rejects_orphan_disease_reference_for_treatment_limitation(db_session):
    orphan = OntologyDiseaseTreatmentLimitation(
        disease_id=uuid.uuid4(),
        limitation_name="Orphan Limitation",
        limitation_category="NOT_A_CANDIDATE",
    )
    db_session.add(orphan)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_foreign_key_rejects_orphan_disease_reference_for_end_stage_finding(db_session):
    orphan = OntologyDiseaseEndStageFinding(
        disease_id=uuid.uuid4(),
        finding_name="Orphan Finding",
    )
    db_session.add(orphan)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_foreign_key_rejects_orphan_disease_reference_for_validation_result(db_session):
    orphan = OntologyDiseaseValidationResult(
        disease_id=uuid.uuid4(),
        validation_type="ORPHAN",
        validation_status="PASS",
    )
    db_session.add(orphan)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_duplicate_limitation_name_and_category_rejected(db_session, seeded_disease):
    db_session.add(
        OntologyDiseaseTreatmentLimitation(
            disease_id=seeded_disease.id,
            limitation_name="Comfort-Focused Care",
            limitation_category="COMFORT_FOCUSED",
        )
    )
    db_session.commit()

    db_session.add(
        OntologyDiseaseTreatmentLimitation(
            disease_id=seeded_disease.id,
            limitation_name="Comfort-Focused Care",
            limitation_category="COMFORT_FOCUSED",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_inactive_records_excluded_from_active_queries(db_session, seeded_disease):
    active_row = OntologyDiseaseEndStageFinding(
        disease_id=seeded_disease.id,
        finding_name="Active Finding",
        active=True,
    )
    inactive_row = OntologyDiseaseEndStageFinding(
        disease_id=seeded_disease.id,
        finding_name="Inactive Finding",
        active=False,
    )
    db_session.add_all([active_row, inactive_row])
    db_session.commit()

    active_only = (
        db_session.query(OntologyDiseaseEndStageFinding)
        .filter_by(disease_id=seeded_disease.id, active=True)
        .all()
    )
    names = {row.finding_name for row in active_only}
    assert names == {"Active Finding"}


def test_invalid_limitation_category_rejected_by_check_constraint(db_session, seeded_disease):
    bad_row = OntologyDiseaseTreatmentLimitation(
        disease_id=seeded_disease.id,
        limitation_name="Bad Category Row",
        limitation_category="NOT_A_REAL_CATEGORY",
    )
    db_session.add(bad_row)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_invalid_validation_status_rejected_by_check_constraint(db_session, seeded_disease):
    bad_row = OntologyDiseaseValidationResult(
        disease_id=seeded_disease.id,
        validation_type="DUPLICATE",
        validation_status="BOGUS",
    )
    db_session.add(bad_row)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---------------------------------------------------------------------------
# Committed population script (backend/scripts/populate_ontology_ak_neuro_cardio.py)
#
# These tests exercise the actual script's run() entry point end-to-end
# against the isolated test database, proving it is reproducible from the
# repository -- no hardcoded UUIDs, no reliance on content inserted manually
# outside of source control -- and that a second execution is a true no-op.
# ---------------------------------------------------------------------------

_CONCEPT_ROW_KWARGS = {
    OntologyDiseaseSymptom: {"symptom_name": "Baseline Symptom"},
    OntologyDiseaseComplication: {"complication_name": "Baseline Complication"},
    OntologyDiseaseFunctionalImpact: {"impact_name": "Baseline Functional Impact"},
    OntologyDiseaseNutritionalImpact: {"impact_name": "Baseline Nutritional Impact"},
    OntologyDiseaseHospiceEligibilitySupport: {"indicator_name": "Baseline Eligibility Indicator"},
}


def _get_or_create(db_session, model_cls, defaults=None, **lookup):
    row = db_session.query(model_cls).filter_by(**lookup).one_or_none()
    if row is not None:
        return row
    row = model_cls(**lookup, **(defaults or {}))
    db_session.add(row)
    db_session.flush()
    return row


@pytest.fixture()
def ak_base_content(db_session):
    """Ensure the nine approved diseases exist (by stable name, get-or-create,
    never hardcoded UUIDs) with the minimal set of A-D/F/G/I concept rows the
    script's DOMAIN_COMPLETENESS/EVIDENCE_COVERAGE checks require. Idempotent:
    safe to run every test session without duplicating hierarchy rows."""
    system = _get_or_create(
        db_session, OntologyBodySystem, system_name="Neurologic System (A-K test fixture)"
    )
    cardio_system = _get_or_create(
        db_session, OntologyBodySystem, system_name="Cardiovascular System (A-K test fixture)"
    )
    families = {
        "Cerebrovascular Disease": _get_or_create(
            db_session, OntologyDiseaseFamily,
            body_system_id=system.id, family_name="Cerebrovascular Disease (A-K test fixture)",
        ),
        "Dementia Disorders": _get_or_create(
            db_session, OntologyDiseaseFamily,
            body_system_id=system.id, family_name="Dementia Disorders (A-K test fixture)",
        ),
        "Cardiac": _get_or_create(
            db_session, OntologyDiseaseFamily,
            body_system_id=cardio_system.id, family_name="Cardiac Disease (A-K test fixture)",
        ),
    }
    family_for_disease = {
        "Stroke": "Cerebrovascular Disease",
        "Hemiplegia": "Cerebrovascular Disease",
        "Hemiparesis": "Cerebrovascular Disease",
        "Contracture": "Cerebrovascular Disease",
        "Dementia Due To Alzheimer's Disease": "Dementia Disorders",
        "Chronic Systolic Heart Failure": "Cardiac",
        "Coronary Artery Disease": "Cardiac",
        "Prior Myocardial Infarction": "Cardiac",
        "Atrial Fibrillation": "Cardiac",
    }

    diseases = {}
    for name in APPROVED_DISEASE_NAMES:
        disease = _get_or_create(
            db_session, OntologyDisease,
            disease_name=name,
            defaults={"disease_family_id": families[family_for_disease[name]].id},
        )
        diseases[name] = disease
    db_session.commit()

    for disease in diseases.values():
        for model_cls, kwargs in _CONCEPT_ROW_KWARGS.items():
            _get_or_create(db_session, model_cls, disease_id=disease.id, **kwargs)
    db_session.commit()
    return diseases


@pytest.fixture()
def clean_ak_state(db_session, ak_base_content):
    """Reset just the E/H/J/K rows this script owns for the nine approved
    diseases back to empty, without touching any other body system, disease,
    or non-A-K domain content -- then hand back the base disease map so
    tests can invoke run() against a known-clean starting point."""
    disease_ids = [d.id for d in ak_base_content.values()]

    # Evidence rules AND Tier5 applicability edges must be cleaned up FIRST,
    # while the concept rows they reference (e.g. TreatmentLimitation and
    # EndStageFinding, both directly reset below AND tracked in
    # CONCEPT_DOMAINS) still exist. Deleting the concept rows before looking
    # up their ids left dangling references for every prior test run's rows,
    # because the id lookup below would find nothing once its target rows
    # were already gone. This also applies to EndStageFinding concepts that
    # other importers (e.g. the Neurologic Production Source Manifest, whose
    # "Stroke" disease is shared with this fixture) attach their own Tier5
    # OntologyConceptVariantApplicability edges to -- those edges must be
    # cleaned up here too, not just this script's own evidence rules.
    for model_cls, concept_type, _name_attr, _required in CONCEPT_DOMAINS:
        concept_ids = [
            row.id
            for row in db_session.query(model_cls.id)
            .filter(model_cls.disease_id.in_(disease_ids))
            .all()
        ]
        if concept_ids:
            db_session.query(OntologyEvidenceRule).filter(
                OntologyEvidenceRule.concept_type == concept_type,
                OntologyEvidenceRule.concept_id.in_(concept_ids),
            ).delete(synchronize_session=False)
            db_session.query(OntologyConceptVariantApplicability).filter(
                OntologyConceptVariantApplicability.concept_type == concept_type,
                OntologyConceptVariantApplicability.concept_id.in_(concept_ids),
            ).delete(synchronize_session=False)

    db_session.query(OntologyDiseaseTreatmentLimitation).filter(
        OntologyDiseaseTreatmentLimitation.disease_id.in_(disease_ids)
    ).delete(synchronize_session=False)
    db_session.query(OntologyDiseaseEndStageFinding).filter(
        OntologyDiseaseEndStageFinding.disease_id.in_(disease_ids)
    ).delete(synchronize_session=False)
    db_session.query(OntologyDiseaseValidationResult).filter(
        OntologyDiseaseValidationResult.disease_id.in_(disease_ids)
    ).delete(synchronize_session=False)
    db_session.commit()
    return ak_base_content


def test_diseases_resolved_by_name_not_hardcoded_uuid(db_session, ak_base_content):
    resolved = _resolve_diseases(db_session, APPROVED_DISEASE_NAMES)
    assert set(resolved.keys()) == set(APPROVED_DISEASE_NAMES)
    assert len(resolved) == 9
    for name, disease in resolved.items():
        assert disease.disease_name == name
        assert isinstance(disease.id, uuid.UUID)


def test_population_script_first_execution_creates_expected_records(db_session, clean_ak_state):
    counts = run_population_script(db_session)
    db_session.commit()

    assert counts["treatment_limitations_inserted"] == 23
    assert counts["end_stage_findings_inserted"] == 14
    assert counts["validation_results_inserted"] == 63

    disease_ids = [d.id for d in clean_ak_state.values()]
    assert (
        db_session.query(OntologyDiseaseTreatmentLimitation)
        .filter(OntologyDiseaseTreatmentLimitation.disease_id.in_(disease_ids))
        .count()
        == 23
    )
    assert (
        db_session.query(OntologyDiseaseEndStageFinding)
        .filter(OntologyDiseaseEndStageFinding.disease_id.in_(disease_ids))
        .count()
        == 14
    )
    assert (
        db_session.query(OntologyDiseaseValidationResult)
        .filter(OntologyDiseaseValidationResult.disease_id.in_(disease_ids))
        .count()
        == 63
    )


def test_population_script_second_execution_creates_zero_duplicates(db_session, clean_ak_state):
    run_population_script(db_session)
    db_session.commit()

    counts_second_run = run_population_script(db_session)
    db_session.commit()

    assert counts_second_run == {
        "treatment_limitations_inserted": 0,
        "end_stage_findings_inserted": 0,
        "evidence_rules_inserted": 0,
        "validation_results_inserted": 0,
    }


def test_e_counts_match_per_disease(db_session, clean_ak_state):
    run_population_script(db_session)
    db_session.commit()

    expected = {
        "Stroke": 3, "Hemiplegia": 2, "Hemiparesis": 2, "Contracture": 2,
        "Dementia Due To Alzheimer's Disease": 3, "Chronic Systolic Heart Failure": 3,
        "Coronary Artery Disease": 3, "Prior Myocardial Infarction": 2, "Atrial Fibrillation": 3,
    }
    for name, disease in clean_ak_state.items():
        count = (
            db_session.query(OntologyDiseaseTreatmentLimitation)
            .filter_by(disease_id=disease.id)
            .count()
        )
        assert count == expected[name], f"{name}: expected {expected[name]}, got {count}"


def test_h_counts_match_per_disease(db_session, clean_ak_state):
    run_population_script(db_session)
    db_session.commit()

    expected = {
        "Stroke": 2, "Hemiplegia": 2, "Hemiparesis": 1, "Contracture": 1,
        "Dementia Due To Alzheimer's Disease": 3, "Chronic Systolic Heart Failure": 2,
        "Coronary Artery Disease": 1, "Prior Myocardial Infarction": 1, "Atrial Fibrillation": 1,
    }
    for name, disease in clean_ak_state.items():
        count = (
            db_session.query(OntologyDiseaseEndStageFinding)
            .filter_by(disease_id=disease.id)
            .count()
        )
        assert count == expected[name], f"{name}: expected {expected[name]}, got {count}"


def test_all_63_k_records_exist_with_required_types_per_disease(db_session, clean_ak_state):
    run_population_script(db_session)
    db_session.commit()

    disease_ids = [d.id for d in clean_ak_state.values()]
    total = (
        db_session.query(OntologyDiseaseValidationResult)
        .filter(OntologyDiseaseValidationResult.disease_id.in_(disease_ids))
        .count()
    )
    assert total == 63

    for disease in clean_ak_state.values():
        types_present = {
            row.validation_type
            for row in db_session.query(OntologyDiseaseValidationResult)
            .filter_by(disease_id=disease.id)
            .all()
        }
        assert types_present == set(REQUIRED_VALIDATION_TYPES), disease.disease_name


def test_every_active_supported_concept_has_active_evidence_rule(db_session, clean_ak_state):
    run_population_script(db_session)
    db_session.commit()

    disease_ids = [d.id for d in clean_ak_state.values()]
    for model_cls, concept_type, _name_attr, _required in CONCEPT_DOMAINS:
        rows = (
            db_session.query(model_cls)
            .filter(model_cls.disease_id.in_(disease_ids))
            .all()
        )
        for row in rows:
            if hasattr(model_cls, "active") and not row.active:
                continue
            rule = (
                db_session.query(OntologyEvidenceRule)
                .filter_by(concept_type=concept_type, concept_id=row.id)
                .one_or_none()
            )
            assert rule is not None, f"{model_cls.__tablename__} row {row.id} missing an active evidence rule"
            assert rule.patient_fact_requires_evidence is True


def test_no_other_body_system_receives_ak_records(db_session, clean_ak_state):
    """Only the nine approved diseases may gain E/H/K rows from a run() call.
    Other test fixtures in this file intentionally create synthetic
    "Test Disease ..." rows for isolated unit tests -- those are pre-existing
    noise, not something the population script wrote, so this test compares
    before/after counts rather than asserting an absolute zero."""

    def _non_approved_counts():
        e = (
            db_session.query(OntologyDiseaseTreatmentLimitation)
            .join(OntologyDisease, OntologyDisease.id == OntologyDiseaseTreatmentLimitation.disease_id)
            .filter(OntologyDisease.disease_name.notin_(APPROVED_DISEASE_NAMES))
            .count()
        )
        h = (
            db_session.query(OntologyDiseaseEndStageFinding)
            .join(OntologyDisease, OntologyDisease.id == OntologyDiseaseEndStageFinding.disease_id)
            .filter(OntologyDisease.disease_name.notin_(APPROVED_DISEASE_NAMES))
            .count()
        )
        k = (
            db_session.query(OntologyDiseaseValidationResult)
            .join(OntologyDisease, OntologyDisease.id == OntologyDiseaseValidationResult.disease_id)
            .filter(OntologyDisease.disease_name.notin_(APPROVED_DISEASE_NAMES))
            .count()
        )
        return e, h, k

    before = _non_approved_counts()
    run_population_script(db_session)
    db_session.commit()
    after = _non_approved_counts()
    assert before == after


def test_seven_active_and_two_inactive_cardiovascular_relationships_unchanged(db_session, clean_ak_state):
    """The population script must never touch ontology_relationship rows;
    confirm the previously corrected cardiovascular relationship graph
    (5 disease-disease + 2 disease-complication active, 2 disease-disease
    inactive) is unaffected by running the E/H/J/K population."""
    cardio_names = [
        "Chronic Systolic Heart Failure", "Coronary Artery Disease",
        "Prior Myocardial Infarction", "Atrial Fibrillation", "Stroke",
    ]
    cardio_ids = [
        clean_ak_state[n].id for n in cardio_names if n in clean_ak_state
    ]

    def _snapshot():
        rows = (
            db_session.query(OntologyRelationship)
            .filter(
                OntologyRelationship.source_concept_type == "DISEASE",
                OntologyRelationship.source_concept_id.in_(cardio_ids),
            )
            .all()
        )
        return {(r.id, r.relationship_type, r.target_concept_id, r.active) for r in rows}

    before = _snapshot()
    run_population_script(db_session)
    db_session.commit()
    after = _snapshot()
    assert before == after


def test_orphan_disease_reference_rejected_via_script_path(db_session):
    with pytest.raises(RuntimeError):
        _resolve_diseases(db_session, ["Not A Real Disease Name"])


def test_duplicate_e_and_h_records_rejected_by_unique_constraint(db_session, ak_base_content):
    disease = ak_base_content["Stroke"]
    db_session.add(
        OntologyDiseaseTreatmentLimitation(
            disease_id=disease.id,
            limitation_name="Duplicate-Check Limitation",
            limitation_category="NOT_A_CANDIDATE",
        )
    )
    db_session.commit()
    db_session.add(
        OntologyDiseaseTreatmentLimitation(
            disease_id=disease.id,
            limitation_name="Duplicate-Check Limitation",
            limitation_category="NOT_A_CANDIDATE",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.add(
        OntologyDiseaseEndStageFinding(disease_id=disease.id, finding_name="Duplicate-Check Finding")
    )
    db_session.commit()
    db_session.add(
        OntologyDiseaseEndStageFinding(disease_id=disease.id, finding_name="Duplicate-Check Finding")
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
