"""Targeted tests for the Endocrine System / Diabetes Mellitus and Related
Disorders ontology A-K population script.

Scope is strictly limited to the new Endocrine content added by
`populate_ontology_ak_endocrine_diabetes.py`. These tests do not touch
RNICA, patient APIs, assigned-RN logic, billing, authentication, or any
protected area, and explicitly assert that pre-existing
Neurologic/Cardiovascular/Renal/Pulmonary ontology content and
relationships are left unchanged.
"""

from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDisease,
    OntologyDiseaseFamily,
    OntologyDiseaseValidationResult,
    OntologyEvidenceRule,
    OntologyRelationship,
)
from scripts.populate_ontology_ak_endocrine_diabetes import (
    APPROVED_DISEASE_NAMES,
    CONCEPT_DOMAINS,
    DI,
    FAMILY_NAME,
    GDM,
    OSDM,
    REQUIRED_VALIDATION_TYPES,
    SYSTEM_NAME,
    T1DM,
    T2DM,
    run as run_population_script,
)

PRIOR_SYSTEM_NAMES = [
    "Neurologic System",
    "Cardiovascular System",
    "Renal System",
    "Pulmonary System",
]


@pytest.fixture()
def clean_endocrine_state(db_session):
    """Run the population script once to bring the Endocrine System to a
    known populated state, then hand back the resolved disease map. Safe
    to call repeatedly -- the script is idempotent."""
    run_population_script(db_session)
    db_session.commit()
    system = (
        db_session.query(OntologyBodySystem)
        .filter_by(system_name=SYSTEM_NAME)
        .one()
    )
    family = (
        db_session.query(OntologyDiseaseFamily)
        .filter_by(body_system_id=system.id, family_name=FAMILY_NAME)
        .one()
    )
    diseases = {
        d.disease_name: d
        for d in db_session.query(OntologyDisease)
        .filter(OntologyDisease.disease_family_id == family.id)
        .all()
    }
    return diseases


def test_endocrine_system_created_once(db_session, clean_endocrine_state):
    run_population_script(db_session)
    db_session.commit()
    systems = (
        db_session.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).all()
    )
    assert len(systems) == 1


def test_diabetes_family_created_once(db_session, clean_endocrine_state):
    run_population_script(db_session)
    db_session.commit()
    system = db_session.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one()
    families = (
        db_session.query(OntologyDiseaseFamily)
        .filter_by(body_system_id=system.id, family_name=FAMILY_NAME)
        .all()
    )
    assert len(families) == 1


def test_all_five_diabetes_diseases_created_once(clean_endocrine_state):
    assert set(clean_endocrine_state.keys()) == set(APPROVED_DISEASE_NAMES)
    for name in (T1DM, T2DM, GDM, OSDM, DI):
        assert name in clean_endocrine_state


def test_diabetes_insipidus_differentiated_from_diabetes_mellitus(clean_endocrine_state):
    """Diabetes Insipidus must be its own disease row, described as an
    ADH/water-regulation disorder and NOT a glucose-metabolism disorder --
    it must never be conflated with Type 1/Type 2/Gestational/Other
    Specified Diabetes Mellitus purely on the basis of shared naming."""
    di = clean_endocrine_state[DI]
    assert "ADH" in di.disease_type or "Water-Regulation" in di.disease_type
    assert "Not a Glucose-Metabolism Disorder" in di.disease_type
    assert "no shared glucose-metabolism pathology" in di.disease_description.lower()
    assert "does not involve hyperglycemia" in di.disease_description.lower()
    assert di.id != clean_endocrine_state[T1DM].id
    assert di.id != clean_endocrine_state[T2DM].id
    assert di.id != clean_endocrine_state[GDM].id
    assert di.id != clean_endocrine_state[OSDM].id


def test_every_ak_domain_populated_for_each_disease(db_session, clean_endocrine_state):
    for disease in clean_endocrine_state.values():
        k_count = (
            db_session.query(OntologyDiseaseValidationResult)
            .filter_by(disease_id=disease.id)
            .count()
        )
        assert k_count == len(REQUIRED_VALIDATION_TYPES)


def test_all_seven_required_validation_types_exist_per_disease(
    db_session, clean_endocrine_state
):
    for disease in clean_endocrine_state.values():
        rows = (
            db_session.query(OntologyDiseaseValidationResult)
            .filter_by(disease_id=disease.id)
            .all()
        )
        types_present = {r.validation_type for r in rows}
        assert types_present == set(REQUIRED_VALIDATION_TYPES)


def test_every_active_clinical_concept_has_active_evidence_rule(
    db_session, clean_endocrine_state
):
    disease_ids = [d.id for d in clean_endocrine_state.values()]
    for model_cls, concept_type, _name_attr, _required in CONCEPT_DOMAINS:
        rows = (
            db_session.query(model_cls)
            .filter(model_cls.disease_id.in_(disease_ids))
            .all()
        )
        for row in rows:
            if not getattr(row, "active", True):
                continue
            rule = (
                db_session.query(OntologyEvidenceRule)
                .filter_by(concept_type=concept_type, concept_id=row.id)
                .one_or_none()
            )
            assert rule is not None, f"missing active evidence rule for {concept_type} {row.id}"
            assert rule.patient_fact_requires_evidence is True


def test_population_script_second_execution_creates_zero_new_rows(db_session):
    run_population_script(db_session)
    db_session.commit()
    counts_second_run = run_population_script(db_session)
    db_session.commit()
    assert all(v == 0 for v in counts_second_run.values())


def test_no_duplicate_records_after_repeated_runs(db_session, clean_endocrine_state):
    run_population_script(db_session)
    db_session.commit()
    run_population_script(db_session)
    db_session.commit()

    for model_cls, _concept_type, name_attr, _required in CONCEPT_DOMAINS:
        disease_ids = [d.id for d in clean_endocrine_state.values()]
        rows = (
            db_session.query(model_cls)
            .filter(model_cls.disease_id.in_(disease_ids))
            .all()
        )
        names = [(row.disease_id, getattr(row, name_attr)) for row in rows]
        assert len(names) == len(set(names)), f"duplicate rows found in {model_cls.__name__}"


def test_prior_body_systems_unchanged(db_session, clean_endocrine_state):
    def _snapshot():
        return (
            db_session.query(OntologyDisease.id, OntologyDisease.disease_name)
            .join(OntologyDiseaseFamily, OntologyDisease.disease_family_id == OntologyDiseaseFamily.id)
            .join(OntologyBodySystem, OntologyDiseaseFamily.body_system_id == OntologyBodySystem.id)
            .filter(OntologyBodySystem.system_name.in_(PRIOR_SYSTEM_NAMES))
            .all()
        )

    before = _snapshot()
    run_population_script(db_session)
    db_session.commit()
    after = _snapshot()
    assert set(before) == set(after)


def test_existing_relationships_unchanged_except_documented_additions(db_session):
    def _non_endocrine_relationship_snapshot():
        endocrine_disease_ids = {
            d.id
            for d in db_session.query(OntologyDisease)
            .join(OntologyDiseaseFamily, OntologyDisease.disease_family_id == OntologyDiseaseFamily.id)
            .join(OntologyBodySystem, OntologyDiseaseFamily.body_system_id == OntologyBodySystem.id)
            .filter(OntologyBodySystem.system_name == SYSTEM_NAME)
            .all()
        }
        rows = (
            db_session.query(OntologyRelationship)
            .filter(
                ~OntologyRelationship.source_concept_id.in_(endocrine_disease_ids)
                if endocrine_disease_ids
                else True
            )
            .all()
        )
        return {(r.id, r.relationship_type, r.source_concept_id, r.target_concept_id, r.active) for r in rows}

    before = _non_endocrine_relationship_snapshot()
    run_population_script(db_session)
    db_session.commit()
    after = _non_endocrine_relationship_snapshot()
    assert before == after


def test_t1dm_may_contribute_to_ckd_relationship_exists(db_session, clean_endocrine_state):
    t1dm = clean_endocrine_state[T1DM]
    ckd = db_session.query(OntologyDisease).filter_by(disease_name="Chronic Kidney Disease").one()
    rel = (
        db_session.query(OntologyRelationship)
        .filter_by(
            source_concept_type="DISEASE",
            source_concept_id=t1dm.id,
            relationship_type="MAY_CONTRIBUTE_TO",
            target_concept_type="DISEASE",
            target_concept_id=ckd.id,
        )
        .one_or_none()
    )
    assert rel is not None


def test_t2dm_may_contribute_to_ckd_relationship_exists(db_session, clean_endocrine_state):
    t2dm = clean_endocrine_state[T2DM]
    ckd = db_session.query(OntologyDisease).filter_by(disease_name="Chronic Kidney Disease").one()
    rel = (
        db_session.query(OntologyRelationship)
        .filter_by(
            source_concept_type="DISEASE",
            source_concept_id=t2dm.id,
            relationship_type="MAY_CONTRIBUTE_TO",
            target_concept_type="DISEASE",
            target_concept_id=ckd.id,
        )
        .one_or_none()
    )
    assert rel is not None


def test_no_ckd_relationship_for_gestational_or_diabetes_insipidus(
    db_session, clean_endocrine_state
):
    """Per approved change-control decision: Gestational Diabetes Mellitus
    and Diabetes Insipidus must never carry a MAY_CONTRIBUTE_TO Chronic
    Kidney Disease relationship."""
    ckd = db_session.query(OntologyDisease).filter_by(disease_name="Chronic Kidney Disease").one()
    for excluded_name in (GDM, DI):
        disease = clean_endocrine_state[excluded_name]
        rel = (
            db_session.query(OntologyRelationship)
            .filter_by(
                source_concept_type="DISEASE",
                source_concept_id=disease.id,
                relationship_type="MAY_CONTRIBUTE_TO",
                target_concept_type="DISEASE",
                target_concept_id=ckd.id,
            )
            .one_or_none()
        )
        assert rel is None, f"unexpected CKD relationship found for {excluded_name}"


def test_no_ckd_relationship_for_other_specified_diabetes(db_session, clean_endocrine_state):
    """OSDM's CKD relationship was not explicitly approved; it must be
    omitted rather than assumed."""
    ckd = db_session.query(OntologyDisease).filter_by(disease_name="Chronic Kidney Disease").one()
    osdm = clean_endocrine_state[OSDM]
    rel = (
        db_session.query(OntologyRelationship)
        .filter_by(
            source_concept_type="DISEASE",
            source_concept_id=osdm.id,
            relationship_type="MAY_CONTRIBUTE_TO",
            target_concept_type="DISEASE",
            target_concept_id=ckd.id,
        )
        .one_or_none()
    )
    assert rel is None


def test_hospice_eligibility_support_uses_general_decline_source_only(
    db_session, clean_endocrine_state
):
    """No diabetes-specific LCD exists in this repository; Domain I content
    must be explicitly sourced from the generic general-decline guidance
    and never mislabeled as a diabetes-specific LCD."""
    from app.models.ontology_disease_blueprint import OntologyDiseaseHospiceEligibilitySupport

    for disease in clean_endocrine_state.values():
        rows = (
            db_session.query(OntologyDiseaseHospiceEligibilitySupport)
            .filter_by(disease_id=disease.id)
            .all()
        )
        assert len(rows) > 0
        for row in rows:
            assert "L33393" in row.lcd_reference
            assert "non-disease-specific" in row.lcd_reference
