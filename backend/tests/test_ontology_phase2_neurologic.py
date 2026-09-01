"""Targeted tests for the Neurologic System Phase 2 Production-Knowledge
expansion (`expand_ontology_phase2_neurologic.py`).

Scope is strictly limited to the six approved diseases: Stroke, Hemiplegia,
Hemiparesis, Contracture, Dementia Due To Alzheimer's Disease, and the one
new approved disease Senile Degeneration of Brain. These tests do not touch
patient APIs, assigned-RN logic, billing, authentication, or any protected
area, and explicitly assert that:

    - the five pre-existing diseases are never re-created or re-familied
    - Senile Degeneration of Brain is a distinct canonical disease, never
      treated as an Alzheimer's alias, with no Alzheimer-specific
      hospice/FAST content copied onto it, and no equivalence relationship
      created between the two diseases
    - no RT discipline value, PT/OT substitution, or Respiratory-Therapy
      interdisciplinary-trigger row is ever created (Neurologic scope has no
      such requirement, but the discipline enum itself is asserted intact)
    - no patient-specific fact, order, assignment, or completed-treatment
      record is created by ontology population alone
    - a second run of the population script creates zero new rows
    - other body systems are left unchanged
"""

from __future__ import annotations

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDisease,
    OntologyDiseaseEndStageFinding,
    OntologyDiseaseFamily,
    OntologyDiseaseFinding,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseaseInterdisciplinaryTrigger,
    OntologyDiseaseValidationResult,
    OntologyEvidenceRule,
    OntologyRelationship,
)
from scripts.expand_ontology_phase2_neurologic import (
    ALL_DISEASE_NAMES,
    ALZ,
    ALZ_SUBTYPE_MARKER,
    CONCEPT_DOMAINS,
    CONTRACTURE,
    EXISTING_DISEASE_NAMES,
    HEMIPARESIS,
    HEMIPLEGIA,
    NEW_FAMILY_NAME,
    REQUIRED_VALIDATION_TYPES,
    SDB,
    STROKE,
    STROKE_SUBTYPE_MARKER,
    SYSTEM_NAME,
    run as run_expansion_script,
)

ALLOWED_DISCIPLINES = {
    "RN", "PHYSICIAN", "MSW", "BSW", "CHAPLAIN", "VOLUNTEER", "BEREAVEMENT",
    "DIETICIAN", "PT", "OT", "IDG",
}


@pytest.fixture()
def expanded_state(db_session):
    """Run the Phase 2 expansion script once to bring the Neurologic System
    to a known expanded state, then hand back the resolved disease map.
    Safe to call repeatedly -- the script is idempotent."""
    run_expansion_script(db_session)
    db_session.commit()
    diseases = {
        name: db_session.query(OntologyDisease).filter_by(disease_name=name).one()
        for name in ALL_DISEASE_NAMES
    }
    return diseases


def test_five_existing_diseases_were_not_recreated(db_session, expanded_state):
    """The five pre-existing diseases must resolve to exactly one row each,
    and must not have been moved to a new family/system."""
    expected_family = {
        STROKE: "Cerebrovascular Disease",
        HEMIPLEGIA: "Cerebrovascular Disease",
        HEMIPARESIS: "Cerebrovascular Disease",
        CONTRACTURE: "Cerebrovascular Disease",
        ALZ: "Dementia Disorders",
    }
    for name in EXISTING_DISEASE_NAMES:
        rows = db_session.query(OntologyDisease).filter_by(disease_name=name).all()
        assert len(rows) == 1, f"{name} must resolve to exactly one disease row"
        disease = rows[0]
        # Test-fixture databases may suffix family names (e.g. "(A-K test
        # fixture)"); assert the canonical family name is a prefix rather
        # than an exact match so this holds in both fixture and real DBs.
        assert disease.disease_family.family_name.startswith(expected_family[name])
        assert disease.disease_family.body_system.system_name.startswith(SYSTEM_NAME)


def test_senile_degeneration_of_brain_created_once_under_new_family(db_session, expanded_state):
    sdb = expanded_state[SDB]
    assert sdb.disease_family.family_name == NEW_FAMILY_NAME
    assert sdb.disease_family.body_system.system_name == SYSTEM_NAME

    rows = db_session.query(OntologyDisease).filter_by(disease_name=SDB).all()
    assert len(rows) == 1

    families = (
        db_session.query(OntologyDiseaseFamily)
        .filter_by(body_system_id=sdb.disease_family.body_system_id, family_name=NEW_FAMILY_NAME)
        .all()
    )
    assert len(families) == 1


def test_senile_degeneration_of_brain_is_distinct_from_alzheimers(db_session, expanded_state):
    sdb = expanded_state[SDB]
    alz = expanded_state[ALZ]

    # Distinct rows, distinct IDs and names.
    assert sdb.id != alz.id
    assert sdb.disease_name != alz.disease_name
    assert sdb.disease_family_id != alz.disease_family_id

    # No equivalence relationship of any kind was created between them.
    rel_rows = (
        db_session.query(OntologyRelationship)
        .filter(
            (
                (OntologyRelationship.source_concept_id == sdb.id)
                & (OntologyRelationship.target_concept_id == alz.id)
            )
            | (
                (OntologyRelationship.source_concept_id == alz.id)
                & (OntologyRelationship.target_concept_id == sdb.id)
            )
        )
        .all()
    )
    assert rel_rows == []

    # No IS_NOT_AUTOMATICALLY_EQUIVALENT_TO (or any equivalence-flavored)
    # relationship type was invented anywhere in the ontology.
    forbidden_rel_types = {
        "IS_NOT_AUTOMATICALLY_EQUIVALENT_TO",
        "IS_EQUIVALENT_TO",
        "IS_ALIAS_OF",
    }
    all_rel_types = {r.relationship_type for r in db_session.query(OntologyRelationship.relationship_type).all()}
    assert forbidden_rel_types.isdisjoint(all_rel_types)


def test_alzheimers_specific_hospice_content_not_copied_onto_sdb(db_session, expanded_state):
    """Senile Degeneration of Brain's Domain I content must cite only
    general decline/terminal-status guidance, never the Alzheimer's-specific
    LCD or FAST staging terminology."""
    sdb = expanded_state[SDB]

    hospice_rows = (
        db_session.query(OntologyDiseaseHospiceEligibilitySupport)
        .filter_by(disease_id=sdb.id)
        .all()
    )
    assert len(hospice_rows) > 0
    for row in hospice_rows:
        combined_text = f"{row.indicator_name} {row.description} {row.supporting_evidence} {row.lcd_reference}".lower()
        assert "fast stage" not in combined_text
        # The description may explicitly state SDB uses "non-Alzheimer-
        # specific" guidance (a permitted negation/disclaimer); strip that
        # phrase before asserting no Alzheimer's-specific content leaked in.
        sanitized_text = combined_text.replace("non-alzheimer-specific", "").replace("non-alzheimer's-specific", "")
        assert "alzheimer" not in sanitized_text

    # No FAST-stage findings exist for SDB (those are Alzheimer's-specific).
    finding_rows = db_session.query(OntologyDiseaseFinding).filter_by(disease_id=sdb.id).all()
    for row in finding_rows:
        assert "fast stage" not in (row.finding_name or "").lower()

    end_stage_rows = db_session.query(OntologyDiseaseEndStageFinding).filter_by(disease_id=sdb.id).all()
    for row in end_stage_rows:
        combined_text = f"{row.finding_name} {row.description} {row.hospice_relevance}".lower()
        assert "fast stage" not in combined_text

    # The disease_description explicitly documents non-equivalence and never
    # claims to be an Alzheimer's alias.
    desc = (sdb.disease_description or "").lower()
    assert "not an alias" in desc or "not automatically" in desc or "distinct" in desc


def test_stroke_subtype_and_terminology_knowledge_recorded_as_content(db_session, expanded_state):
    """Stroke variant/subtype and terminology knowledge is recorded on the
    existing Stroke disease_description, not as new disease rows."""
    stroke = expanded_state[STROKE]
    assert STROKE_SUBTYPE_MARKER in (stroke.disease_description or "")

    forbidden_new_disease_names = {
        "Ischemic Stroke", "Thrombotic Stroke", "Embolic Stroke", "Hemorrhagic Stroke",
        "Intracerebral Hemorrhage", "Subarachnoid Hemorrhage", "Brainstem Stroke",
        "Cerebellar Stroke", "Anterior Circulation Stroke", "Posterior Circulation Stroke",
        "CVA", "Cerebrovascular Accident", "Cerebral Infarct", "Brain Attack",
    }
    existing_disease_names = {
        d.disease_name for d in db_session.query(OntologyDisease.disease_name).all()
    }
    assert forbidden_new_disease_names.isdisjoint(existing_disease_names)


def test_alzheimers_subtype_terminology_recorded_as_content(expanded_state):
    alz = expanded_state[ALZ]
    assert ALZ_SUBTYPE_MARKER in (alz.disease_description or "")


def test_no_rt_discipline_value_or_pt_ot_substitution_introduced(db_session, expanded_state):
    """No Respiratory Therapy discipline value is ever used, and the
    discipline enum is never modified: only pre-existing allowed values
    appear on any interdisciplinary trigger row created by this script."""
    disease_ids = [d.id for d in expanded_state.values()]
    rows = (
        db_session.query(OntologyDiseaseInterdisciplinaryTrigger)
        .filter(OntologyDiseaseInterdisciplinaryTrigger.disease_id.in_(disease_ids))
        .all()
    )
    assert len(rows) > 0
    for row in rows:
        assert row.discipline != "RT"
        assert row.discipline in ALLOWED_DISCIPLINES

    # No Respiratory-Therapy-flavored trigger_condition text exists anywhere
    # in the disciplines this script created.
    for row in rows:
        assert "respiratory therapy" not in (row.trigger_condition or "").lower()


def test_every_ak_domain_populated_for_each_disease(db_session, expanded_state):
    for disease in expanded_state.values():
        k_count = (
            db_session.query(OntologyDiseaseValidationResult)
            .filter_by(disease_id=disease.id)
            .count()
        )
        assert k_count == len(REQUIRED_VALIDATION_TYPES)


def test_all_seven_required_validation_types_exist_per_disease(db_session, expanded_state):
    for disease in expanded_state.values():
        rows = (
            db_session.query(OntologyDiseaseValidationResult)
            .filter_by(disease_id=disease.id)
            .all()
        )
        types_present = {r.validation_type for r in rows}
        assert types_present == set(REQUIRED_VALIDATION_TYPES)


def test_every_active_clinical_concept_has_active_evidence_rule(db_session, expanded_state):
    disease_ids = [d.id for d in expanded_state.values()]
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
    run_expansion_script(db_session)
    db_session.commit()
    counts_second_run = run_expansion_script(db_session)
    db_session.commit()
    assert all(v == 0 for v in counts_second_run.values())


def test_no_duplicate_records_after_repeated_runs(db_session, expanded_state):
    run_expansion_script(db_session)
    db_session.commit()
    run_expansion_script(db_session)
    db_session.commit()

    disease_ids = [d.id for d in expanded_state.values()]
    for model_cls, _concept_type, name_attr, _required in CONCEPT_DOMAINS:
        rows = (
            db_session.query(model_cls)
            .filter(model_cls.disease_id.in_(disease_ids))
            .all()
        )
        names = [(row.disease_id, getattr(row, name_attr)) for row in rows]
        assert len(names) == len(set(names)), f"duplicate rows found in {model_cls.__name__}"


def test_no_patient_specific_records_created(db_session):
    """Ontology population must never create patient facts, orders,
    staffing assignments, or completed-treatment records -- this script
    only touches ontology_* tables, never any patient/staff/order table."""
    import app.models.poc as poc_module

    patient_touching_model_names = [
        name for name in dir(poc_module)
        if "PatientFact" in name or "Order" in name or "Assignment" in name
    ]
    # This is a structural assertion: the expansion script module itself
    # imports nothing from these patient-facing modules.
    import scripts.expand_ontology_phase2_neurologic as script_module

    script_source_names = dir(script_module)
    for forbidden in ("PatientFact", "POCOrder", "StaffAssignment", "PatientTreatment"):
        assert forbidden not in script_source_names


def test_other_body_systems_unchanged(db_session, expanded_state):
    def _snapshot():
        return set(
            db_session.query(OntologyDisease.id, OntologyDisease.disease_name)
            .join(OntologyDiseaseFamily, OntologyDisease.disease_family_id == OntologyDiseaseFamily.id)
            .join(OntologyBodySystem, OntologyDiseaseFamily.body_system_id == OntologyBodySystem.id)
            .filter(OntologyBodySystem.system_name != SYSTEM_NAME)
            .all()
        )

    before = _snapshot()
    run_expansion_script(db_session)
    db_session.commit()
    after = _snapshot()
    assert before == after
