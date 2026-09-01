"""Targeted tests for the Pulmonary System / Chronic Obstructive Pulmonary
Disease / Chronic Respiratory Failure ontology A-K population script.

Scope is strictly limited to the new Pulmonary content added by
`populate_ontology_ak_pulmonary_copd_crf.py`. These tests do not touch
RNICA, patient APIs, assigned-RN logic, billing, authentication, or any
protected area, and explicitly assert that pre-existing
Neurologic/Cardiovascular/Renal ontology content and relationships are
left unchanged.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDisease,
    OntologyDiseaseEndStageFinding,
    OntologyDiseaseFamily,
    OntologyDiseaseFinding,
    OntologyDiseaseTreatmentLimitation,
    OntologyDiseaseValidationResult,
    OntologyEvidenceRule,
    OntologyRelationship,
)
from scripts.populate_ontology_ak_pulmonary_copd_crf import (
    APPROVED_DISEASE_NAMES,
    CONCEPT_DOMAINS,
    COPD,
    CRF,
    FAMILY_NAME,
    REQUIRED_VALIDATION_TYPES,
    SYSTEM_NAME,
    run as run_population_script,
)


@pytest.fixture()
def clean_pulmonary_state(db_session):
    """Run the population script once to bring the Pulmonary System to a
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


def test_pulmonary_system_created_once(db_session, clean_pulmonary_state):
    run_population_script(db_session)
    db_session.commit()
    systems = (
        db_session.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).all()
    )
    assert len(systems) == 1


def test_pulmonary_disease_family_created_once(db_session, clean_pulmonary_state):
    run_population_script(db_session)
    db_session.commit()
    system = db_session.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one()
    families = (
        db_session.query(OntologyDiseaseFamily)
        .filter_by(body_system_id=system.id, family_name=FAMILY_NAME)
        .all()
    )
    assert len(families) == 1


def test_copd_and_crf_diseases_created_once(clean_pulmonary_state):
    assert set(clean_pulmonary_state.keys()) == set(APPROVED_DISEASE_NAMES)
    assert COPD in clean_pulmonary_state
    assert CRF in clean_pulmonary_state


def test_gold_staging_represented_as_findings_not_diseases(db_session, clean_pulmonary_state):
    """GOLD 1-4 staging must exist as OntologyDiseaseFinding rows under
    COPD -- never as separate OntologyDisease rows (Acute Respiratory
    Failure / Asthma are forbidden disease names for this task)."""
    forbidden_names = {"Acute Respiratory Failure", "Asthma"}
    assert forbidden_names.isdisjoint(clean_pulmonary_state.keys())

    copd = clean_pulmonary_state[COPD]
    findings = (
        db_session.query(OntologyDiseaseFinding)
        .filter_by(disease_id=copd.id)
        .all()
    )
    finding_names = {f.finding_name for f in findings}
    assert any("GOLD Stage 1" in n for n in finding_names)
    assert any("GOLD Stage 4" in n for n in finding_names)
    assert len(findings) > 0


def test_every_ak_domain_populated_for_each_disease(db_session, clean_pulmonary_state):
    for disease in clean_pulmonary_state.values():
        k_count = (
            db_session.query(OntologyDiseaseValidationResult)
            .filter_by(disease_id=disease.id)
            .count()
        )
        assert k_count == len(REQUIRED_VALIDATION_TYPES)

    # CRF-only domains (E: Treatment Limitations, H: End-Stage Findings)
    crf = clean_pulmonary_state[CRF]
    assert (
        db_session.query(OntologyDiseaseTreatmentLimitation)
        .filter_by(disease_id=crf.id)
        .count()
        > 0
    )
    assert (
        db_session.query(OntologyDiseaseEndStageFinding)
        .filter_by(disease_id=crf.id)
        .count()
        > 0
    )


def test_all_seven_required_validation_types_exist_per_disease(
    db_session, clean_pulmonary_state
):
    for disease in clean_pulmonary_state.values():
        rows = (
            db_session.query(OntologyDiseaseValidationResult)
            .filter_by(disease_id=disease.id)
            .all()
        )
        types_present = {r.validation_type for r in rows}
        assert types_present == set(REQUIRED_VALIDATION_TYPES)


def test_every_active_clinical_concept_has_active_evidence_rule(
    db_session, clean_pulmonary_state
):
    disease_ids = [d.id for d in clean_pulmonary_state.values()]
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


def test_no_duplicate_records_after_repeated_runs(db_session, clean_pulmonary_state):
    run_population_script(db_session)
    db_session.commit()
    run_population_script(db_session)
    db_session.commit()

    for model_cls, _concept_type, name_attr, _required in CONCEPT_DOMAINS:
        disease_ids = [d.id for d in clean_pulmonary_state.values()]
        rows = (
            db_session.query(model_cls)
            .filter(model_cls.disease_id.in_(disease_ids))
            .all()
        )
        names = [(row.disease_id, getattr(row, name_attr)) for row in rows]
        assert len(names) == len(set(names)), f"duplicate rows found in {model_cls.__name__}"


def test_neurologic_cardiovascular_renal_rows_unchanged(db_session, clean_pulmonary_state):
    def _snapshot():
        return (
            db_session.query(OntologyDisease.id, OntologyDisease.disease_name)
            .join(OntologyDiseaseFamily, OntologyDisease.disease_family_id == OntologyDiseaseFamily.id)
            .join(OntologyBodySystem, OntologyDiseaseFamily.body_system_id == OntologyBodySystem.id)
            .filter(
                OntologyBodySystem.system_name.in_(
                    ["Neurologic System", "Cardiovascular System", "Renal System"]
                )
            )
            .all()
        )

    before = _snapshot()
    run_population_script(db_session)
    db_session.commit()
    after = _snapshot()
    assert set(before) == set(after)


def test_existing_relationships_unchanged_except_documented_additions(db_session):
    def _non_pulmonary_relationship_snapshot():
        pulmonary_disease_ids = {
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
                ~OntologyRelationship.source_concept_id.in_(pulmonary_disease_ids)
                if pulmonary_disease_ids
                else True
            )
            .all()
        )
        return {(r.id, r.relationship_type, r.source_concept_id, r.target_concept_id, r.active) for r in rows}

    before = _non_pulmonary_relationship_snapshot()
    run_population_script(db_session)
    db_session.commit()
    after = _non_pulmonary_relationship_snapshot()
    assert before == after


def test_copd_may_progress_to_crf_relationship_exists(db_session, clean_pulmonary_state):
    copd = clean_pulmonary_state[COPD]
    crf = clean_pulmonary_state[CRF]
    rel = (
        db_session.query(OntologyRelationship)
        .filter_by(
            source_concept_type="DISEASE",
            source_concept_id=copd.id,
            relationship_type="MAY_PROGRESS_TO",
            target_concept_type="DISEASE",
            target_concept_id=crf.id,
        )
        .one_or_none()
    )
    assert rel is not None


def test_duplicate_finding_rejected_by_unique_constraint(db_session, clean_pulmonary_state):
    copd = clean_pulmonary_state[COPD]
    unique_name = f"Duplicate-Check Pulmonary Finding {uuid.uuid4().hex[:8]}"
    db_session.add(OntologyDiseaseFinding(disease_id=copd.id, finding_name=unique_name))
    db_session.commit()
    db_session.add(OntologyDiseaseFinding(disease_id=copd.id, finding_name=unique_name))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
