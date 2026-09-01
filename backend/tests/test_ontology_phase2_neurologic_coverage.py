"""Targeted tests for the Neurologic Phase 2 Atomic Concept Coverage Repair
(`complete_ontology_phase2_neurologic_coverage.py`).

Scope is strictly limited to the six approved Phase 2 diseases: Stroke,
Hemiplegia, Hemiparesis, Contracture, Dementia Due To Alzheimer's Disease,
and Senile Degeneration of Brain. These tests assert:

    1. Every atomic concept in the approved manifest exists independently.
    2. Existing compressed aggregate records (from PR #34) remain present
       and unchanged.
    3. No hard deletion occurs (compressed and atomic records coexist).
    4. No schema, migration, model, or enum change occurs (no active/status
       column exists on any of the leaf concept tables touched here).
    5. No duplicate atomic concept exists within the same disease and
       domain.
    6. Every new atomic concept has an evidence rule.
    7. patient_fact_requires_evidence is true on every such rule.
    8. Senile Degeneration of Brain remains distinct from Dementia Due To
       Alzheimer's Disease.
    9. Alzheimer-specific hospice criteria are not automatically attached
       to Senile Degeneration of Brain.
    10. The second population run creates zero new rows.
    11. No other body system changes.
    12. No unrelated files change (asserted via the change set at review
        time, not exercised by this suite).
"""

from __future__ import annotations

import pytest
from sqlalchemy import inspect as sa_inspect

from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDisease,
    OntologyDiseaseComplication,
    OntologyDiseaseDiagnosticTest,
    OntologyDiseaseEndStageFinding,
    OntologyDiseaseFamily,
    OntologyDiseaseFinding,
    OntologyDiseaseFunctionalImpact,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseaseLab,
    OntologyDiseaseMedication,
    OntologyDiseaseNutritionalImpact,
    OntologyDiseasePrognosticIndicator,
    OntologyDiseaseSymptom,
    OntologyDiseaseTreatment,
    OntologyDiseaseTreatmentLimitation,
    OntologyEvidenceRule,
    OntologyRelationship,
)
from scripts.complete_ontology_phase2_neurologic_coverage import (
    ALL_DISEASE_NAMES,
    ALZ,
    CONCEPT_DOMAINS,
    CONTRACTURE,
    HEMIPARESIS,
    HEMIPLEGIA,
    SDB,
    STROKE,
    run as run_coverage_repair,
)
from scripts.expand_ontology_phase2_neurologic import run as run_phase2_expansion

# A representative sample of atomic concepts that must exist independently
# after the repair -- both compressed-record splits and manifest-approved
# additions, across every disease and domain touched.
EXPECTED_ATOMIC_SYMPTOMS = {
    STROKE: {"Dysarthria", "Aphasia", "Ataxia", "Imbalance", "Confusion", "Altered Mental Status",
             "Hemiparesis", "Hemiplegia", "Vision Loss", "Hemianopia", "Sudden Vision Loss",
             "Visual Field Deficit", "Global Aphasia", "Seizure"},
    HEMIPLEGIA: {"Shoulder Pain", "Chronic Pain"},
    HEMIPARESIS: {"Reduced Grip Strength", "Imbalance"},
    CONTRACTURE: {"Visible Joint Deformity", "Range-of-Motion Limited by Pain"},
    ALZ: {"Behavioral Symptoms", "Psychological Symptoms", "Aphasia", "Apraxia", "Agnosia"},
    SDB: {"Memory Impairment", "Disorientation", "Dysphagia"},
}
EXPECTED_ATOMIC_COMPLICATIONS = {
    STROKE: {"Deep Vein Thrombosis", "Pulmonary Embolism", "Malnutrition", "Dehydration"},
    ALZ: {"Malnutrition", "Dehydration"},
    SDB: {"Dehydration"},
}
EXPECTED_ATOMIC_TREATMENTS = {
    STROKE: {"Physical Therapy", "Occupational Therapy", "Speech Therapy", "Swallow Therapy",
             "Thrombolytic Therapy", "Mechanical Thrombectomy"},
    HEMIPLEGIA: {"Physical Therapy", "Occupational Therapy"},
    ALZ: {"Behavioral Management", "Environmental Management"},
}
EXPECTED_ATOMIC_MEDICATIONS = {
    STROKE: {"Aspirin", "Antiplatelet Therapy", "Baclofen", "Tizanidine"},
    CONTRACTURE: {"Botulinum Toxin for Documented Spasticity"},
}

# Compressed aggregate records created by PR #34 that must still be present
# and untouched (name unchanged, no active/status flag exists to flip).
# Each entry: (label, model_cls, name_attr, disease_name, compressed_name)
EXPECTED_COMPRESSED_RECORDS_STILL_PRESENT = [
    ("symptom", OntologyDiseaseSymptom, "symptom_name", STROKE, "Sudden Vision Loss/Field Cut"),
    ("symptom", OntologyDiseaseSymptom, "symptom_name", STROKE, "Ataxia/Imbalance"),
    ("symptom", OntologyDiseaseSymptom, "symptom_name", ALZ, "Behavioral/Psychological Symptoms"),
    ("finding", OntologyDiseaseFinding, "finding_name", STROKE, "Hemiparesis/Hemiplegia on Exam"),
    ("complication", OntologyDiseaseComplication, "complication_name", STROKE,
     "Deep Vein Thrombosis/Pulmonary Embolism"),
    ("complication", OntologyDiseaseComplication, "complication_name", ALZ, "Malnutrition/Dehydration"),
    ("complication", OntologyDiseaseComplication, "complication_name", SDB, "Malnutrition/Dehydration"),
    ("prognostic_indicator", OntologyDiseasePrognosticIndicator, "indicator_name", ALZ,
     "Recurrent Infections/Aspiration"),
    ("treatment_limitation", OntologyDiseaseTreatmentLimitation, "limitation_name", STROKE,
     "Not A Thrombolysis/Thrombectomy Candidate"),
]



@pytest.fixture()
def repaired_state(db_session):
    """Seed PR #34's Phase 2 expansion (which creates the compressed
    aggregate records this repair targets) and then run the coverage-repair
    script, handing back the resolved disease map. Safe to call repeatedly
    -- both scripts are idempotent."""
    run_phase2_expansion(db_session)
    db_session.commit()
    run_coverage_repair(db_session)
    db_session.commit()
    diseases = {
        name: db_session.query(OntologyDisease).filter_by(disease_name=name).one()
        for name in ALL_DISEASE_NAMES
    }
    return diseases


def _names_for(db_session, model_cls, name_attr, disease_id):
    rows = db_session.query(model_cls).filter_by(disease_id=disease_id).all()
    return {getattr(r, name_attr) for r in rows}


def test_approved_atomic_symptoms_exist_independently(db_session, repaired_state):
    for disease_name, expected_names in EXPECTED_ATOMIC_SYMPTOMS.items():
        disease = repaired_state[disease_name]
        present = _names_for(db_session, OntologyDiseaseSymptom, "symptom_name", disease.id)
        missing = expected_names - present
        assert not missing, f"{disease_name} missing atomic symptoms: {missing}"


def test_approved_atomic_complications_exist_independently(db_session, repaired_state):
    for disease_name, expected_names in EXPECTED_ATOMIC_COMPLICATIONS.items():
        disease = repaired_state[disease_name]
        present = _names_for(db_session, OntologyDiseaseComplication, "complication_name", disease.id)
        missing = expected_names - present
        assert not missing, f"{disease_name} missing atomic complications: {missing}"


def test_approved_atomic_treatments_exist_independently(db_session, repaired_state):
    for disease_name, expected_names in EXPECTED_ATOMIC_TREATMENTS.items():
        disease = repaired_state[disease_name]
        rows = db_session.query(OntologyDiseaseTreatment).filter_by(disease_id=disease.id).all()
        present = {r.treatment_name for r in rows}
        missing = expected_names - present
        assert not missing, f"{disease_name} missing atomic treatments: {missing}"


def test_approved_atomic_medications_exist_independently(db_session, repaired_state):
    for disease_name, expected_names in EXPECTED_ATOMIC_MEDICATIONS.items():
        disease = repaired_state[disease_name]
        present = _names_for(db_session, OntologyDiseaseMedication, "medication_name", disease.id)
        missing = expected_names - present
        assert not missing, f"{disease_name} missing atomic medications: {missing}"


def test_compressed_aggregate_records_remain_present_and_unchanged(db_session, repaired_state):
    """PR #34's compressed aggregate records must still exist by name after
    the repair -- they are never hard-deleted, deactivated, or renamed."""
    for label, model_cls, name_attr, disease_name, compressed_name in EXPECTED_COMPRESSED_RECORDS_STILL_PRESENT:
        disease = repaired_state[disease_name]
        existing = db_session.query(model_cls).filter_by(disease_id=disease.id, **{name_attr: compressed_name})
        rows = existing.all()
        assert len(rows) == 1, (
            f"compressed {label} record '{compressed_name}' for {disease_name} must still be present exactly once"
        )


def test_no_active_or_status_column_added_to_leaf_concept_tables(db_session):
    """No schema/model change occurred: none of the leaf concept tables this
    script writes to have gained an active/status column. (OntologyDisease,
    OntologyDiseaseFamily, OntologyBodySystem, OntologyRelationship,
    OntologyDiseaseTreatmentLimitation, OntologyDiseaseEndStageFinding, and
    OntologyDiseaseValidationResult are the only pre-existing tables with an
    `active` column -- that was true before this script and remains true.)"""
    leaf_tables_without_active = [
        OntologyDiseaseSymptom,
        OntologyDiseaseFinding,
        OntologyDiseaseLab,
        OntologyDiseaseDiagnosticTest,
        OntologyDiseaseComplication,
        OntologyDiseasePrognosticIndicator,
        OntologyDiseaseFunctionalImpact,
        OntologyDiseaseNutritionalImpact,
        OntologyDiseaseHospiceEligibilitySupport,
        OntologyDiseaseTreatment,
        OntologyDiseaseMedication,
    ]
    for model_cls in leaf_tables_without_active:
        column_names = {c.name for c in sa_inspect(model_cls).columns}
        assert "active" not in column_names, f"{model_cls.__name__} must not have gained an active column"
        assert "status" not in column_names, f"{model_cls.__name__} must not have gained a status column"


def test_no_duplicate_atomic_concept_within_disease_and_domain(db_session, repaired_state):
    disease_ids = [d.id for d in repaired_state.values()]
    for model_cls, _concept_type, name_attr in CONCEPT_DOMAINS:
        rows = db_session.query(model_cls).filter(model_cls.disease_id.in_(disease_ids)).all()
        names = [(row.disease_id, getattr(row, name_attr)) for row in rows]
        assert len(names) == len(set(names)), f"duplicate rows found in {model_cls.__name__}"


def test_every_new_atomic_concept_has_active_evidence_rule(db_session, repaired_state):
    disease_ids = [d.id for d in repaired_state.values()]
    for model_cls, concept_type, _name_attr in CONCEPT_DOMAINS:
        rows = db_session.query(model_cls).filter(model_cls.disease_id.in_(disease_ids)).all()
        for row in rows:
            rule = (
                db_session.query(OntologyEvidenceRule)
                .filter_by(concept_type=concept_type, concept_id=row.id)
                .one_or_none()
            )
            assert rule is not None, f"missing evidence rule for {concept_type} {row.id}"
            assert rule.patient_fact_requires_evidence is True


def test_senile_degeneration_of_brain_remains_distinct_from_alzheimers(db_session, repaired_state):
    sdb = repaired_state[SDB]
    alz = repaired_state[ALZ]

    assert sdb.id != alz.id
    assert sdb.disease_name != alz.disease_name
    assert sdb.disease_family_id != alz.disease_family_id

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


def test_alzheimer_specific_hospice_criteria_not_attached_to_sdb(db_session, repaired_state):
    """This script adds no new OntologyDiseaseHospiceEligibilitySupport rows
    for any disease; SDB's hospice-eligibility-support content therefore
    remains exactly what PR #34 established: general-decline-only, never
    the Alzheimer's-specific LCD or FAST staging terminology."""
    sdb = repaired_state[SDB]
    hospice_rows = (
        db_session.query(OntologyDiseaseHospiceEligibilitySupport)
        .filter_by(disease_id=sdb.id)
        .all()
    )
    for row in hospice_rows:
        combined_text = f"{row.indicator_name} {row.description} {row.supporting_evidence} {row.lcd_reference}".lower()
        assert "fast stage" not in combined_text
        sanitized_text = combined_text.replace("non-alzheimer-specific", "").replace("non-alzheimer's-specific", "")
        assert "alzheimer" not in sanitized_text


def test_second_run_creates_zero_new_rows(db_session):
    run_phase2_expansion(db_session)
    db_session.commit()
    run_coverage_repair(db_session)
    db_session.commit()
    counts_second_run = run_coverage_repair(db_session)
    db_session.commit()
    assert all(v == 0 for v in counts_second_run.values())


def test_other_body_systems_unchanged(db_session, repaired_state):
    def _snapshot():
        return set(
            db_session.query(OntologyDisease.id, OntologyDisease.disease_name)
            .join(OntologyDiseaseFamily, OntologyDisease.disease_family_id == OntologyDiseaseFamily.id)
            .join(OntologyBodySystem, OntologyDiseaseFamily.body_system_id == OntologyBodySystem.id)
            .filter(OntologyBodySystem.system_name != "Neurologic System")
            .all()
        )

    before = _snapshot()
    run_coverage_repair(db_session)
    db_session.commit()
    after = _snapshot()
    assert before == after


def test_script_touches_only_ontology_tables_no_patient_or_schema_modules(db_session):
    """Structural assertion: the coverage-repair script module imports
    nothing from patient-facing, staffing, or schema/migration modules, and
    defines/uses no patient-fact, order, or staffing model class."""
    import scripts.complete_ontology_phase2_neurologic_coverage as script_module

    module_names = dir(script_module)
    for forbidden in ("PatientFact", "POCOrder", "StaffAssignment", "PatientTreatment", "alembic"):
        assert forbidden not in module_names, f"coverage-repair script must not reference {forbidden}"
