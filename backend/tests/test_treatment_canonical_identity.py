from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyDiseaseTreatment,
    OntologyDiseaseTreatmentLimitation,
)
from app.ontology.treatment_identity import DuplicateCanonicalIdentityError, normalize_ontology_concept_name
from scripts.expand_ontology_phase2_neurologic import CONTRACTURE, STROKE, run as run_phase2_script
from scripts.import_neurologic_production_source_manifest import run as run_neurologic_manifest_script
from tests.ontology_neurologic_baseline import seed_base_neurologic_diseases


def _seed_phase2(db_session) -> dict[str, OntologyDisease]:
    seed_base_neurologic_diseases(db_session)
    db_session.commit()
    run_phase2_script(db_session)
    db_session.commit()
    return {
        disease.disease_name: disease
        for disease in db_session.query(OntologyDisease).all()
    }


def test_treatment_identity_ignores_category_and_preserves_one_serial_casting_row(db_session):
    diseases = _seed_phase2(db_session)
    run_neurologic_manifest_script(db_session)
    db_session.commit()

    contracture = diseases[CONTRACTURE]
    normalized = normalize_ontology_concept_name(" Serial   Casting ")
    rows = (
        db_session.query(OntologyDiseaseTreatment)
        .filter_by(disease_id=contracture.id, normalized_name=normalized)
        .all()
    )
    assert len(rows) == 1
    assert rows[0].treatment_name == "Serial Casting"
    assert rows[0].treatment_category == "DISEASE_DIRECTED"


def test_treatment_limitation_identity_ignores_category_and_never_creates_second_row(db_session):
    diseases = _seed_phase2(db_session)
    run_neurologic_manifest_script(db_session)
    db_session.commit()

    stroke = diseases[STROKE]
    normalized = normalize_ontology_concept_name("Anticoagulation Contraindicated")
    rows = (
        db_session.query(OntologyDiseaseTreatmentLimitation)
        .filter_by(disease_id=stroke.id, normalized_name=normalized)
        .all()
    )
    assert len(rows) == 1
    assert rows[0].limitation_category == "CONTRAINDICATED"


def test_implicated_importers_are_idempotent_for_treatment_identity(db_session):
    diseases = _seed_phase2(db_session)
    before = {
        "treatments": db_session.query(OntologyDiseaseTreatment).count(),
        "limitations": db_session.query(OntologyDiseaseTreatmentLimitation).count(),
    }
    run_neurologic_manifest_script(db_session)
    db_session.commit()
    after_first = {
        "treatments": db_session.query(OntologyDiseaseTreatment).count(),
        "limitations": db_session.query(OntologyDiseaseTreatmentLimitation).count(),
    }
    run_phase2_script(db_session)
    db_session.commit()
    run_neurologic_manifest_script(db_session)
    db_session.commit()
    after_second = {
        "treatments": db_session.query(OntologyDiseaseTreatment).count(),
        "limitations": db_session.query(OntologyDiseaseTreatmentLimitation).count(),
    }

    assert diseases[CONTRACTURE].disease_name == CONTRACTURE
    assert after_first["treatments"] >= before["treatments"]
    assert after_first["limitations"] >= before["limitations"]
    assert after_second == after_first


def test_duplicate_canonical_rows_raise_in_lookup_path(db_session):
    diseases = _seed_phase2(db_session)
    contracture = diseases[CONTRACTURE]

    dup_id_1 = str(uuid.uuid4())
    dup_id_2 = str(uuid.uuid4())
    normalized_name = normalize_ontology_concept_name("Serial Casting")

    # This test intentionally bypasses the canonical-identity uniqueness
    # constraint to construct a duplicate-row scenario and prove
    # DuplicateCanonicalIdentityError fires. ontology_* tables have no
    # tenant_id and are never cleared between tests, so both the dropped
    # constraint and the duplicate rows MUST be reverted here in a `finally`
    # -- otherwise duplicate protection stays permanently disabled and the
    # leftover duplicate rows corrupt every later test in the same suite run
    # (including the canonicalization migration's re-entrant merge, which
    # previously surfaced this as orphaned evidence_rule references).
    db_session.execute(text("ALTER TABLE ontology_disease_treatment DROP CONSTRAINT uq_ont_dis_treat_disease_norm_name"))
    db_session.execute(
        text(
            """
            INSERT INTO ontology_disease_treatment (id, disease_id, treatment_name, normalized_name, treatment_category, description)
            VALUES (:id1, :disease_id, :name1, :normalized_name, :cat1, :desc1),
                   (:id2, :disease_id, :name2, :normalized_name, :cat2, :desc2)
            """
        ),
        {
            "id1": dup_id_1,
            "id2": dup_id_2,
            "disease_id": str(contracture.id),
            "name1": "Serial Casting",
            "name2": " Serial   Casting ",
            "normalized_name": normalized_name,
            "cat1": "SUPPORTIVE",
            "cat2": "DISEASE_DIRECTED",
            "desc1": "duplicate one",
            "desc2": "duplicate two",
        },
    )
    db_session.commit()

    try:
        with pytest.raises(DuplicateCanonicalIdentityError) as excinfo:
            run_neurologic_manifest_script(db_session)

        exc = excinfo.value
        assert exc.table_name == "ontology_disease_treatment"
        assert exc.disease_id == contracture.id
        assert exc.normalized_name == normalized_name
        assert len(exc.row_ids) >= 2
    finally:
        # The exception above leaves the session's transaction aborted at
        # the DB level; roll back before issuing cleanup DDL/DML. The
        # constraint drop and duplicate insert above are already committed,
        # so this only clears the failed script's incomplete transaction.
        db_session.rollback()
        db_session.execute(
            text("DELETE FROM ontology_disease_treatment WHERE id IN (:id1, :id2)"),
            {"id1": dup_id_1, "id2": dup_id_2},
        )
        db_session.execute(
            text(
                "ALTER TABLE ontology_disease_treatment "
                "ADD CONSTRAINT uq_ont_dis_treat_disease_norm_name UNIQUE (disease_id, normalized_name)"
            )
        )
        db_session.commit()
