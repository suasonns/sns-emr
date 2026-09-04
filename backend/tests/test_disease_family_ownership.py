from __future__ import annotations

import uuid

import pytest

from app.models.ontology_disease_blueprint import OntologyBodySystem, OntologyDisease, OntologyDiseaseFamily
from app.ontology.disease_family_ownership import (
    DiseaseFamilyOwnershipConflict,
    authoritative_family_name_for,
    resolve_or_create_authoritative_disease,
)
from scripts.expand_ontology_phase2_neurologic import ALZ, SDB, SYSTEM_NAME, run as run_phase2_script
from scripts.import_dementia_production_hardening import run as run_dementia_hardening_script
from tests.ontology_neurologic_baseline import seed_base_neurologic_diseases


def _family_name(db_session, disease_name: str) -> str:
    return (
        db_session.query(OntologyDiseaseFamily.family_name)
        .join(OntologyDisease, OntologyDisease.disease_family_id == OntologyDiseaseFamily.id)
        .filter(OntologyDisease.disease_name == disease_name)
        .scalar()
    )


def _run_order(db_session, order: tuple[str, ...]) -> None:
    seed_base_neurologic_diseases(db_session)
    db_session.commit()
    for step in order:
        if step == "phase2":
            run_phase2_script(db_session)
        elif step == "dementia":
            run_dementia_hardening_script(db_session)
        else:
            raise AssertionError(step)
        db_session.commit()


@pytest.mark.parametrize(
    "order",
    [
        ("phase2", "dementia"),
        ("dementia", "phase2"),
    ],
)
def test_authoritative_family_is_order_independent(db_session, order):
    _run_order(db_session, order)
    assert _family_name(db_session, ALZ) == authoritative_family_name_for(ALZ)
    assert _family_name(db_session, SDB) == authoritative_family_name_for(SDB)
    assert _family_name(db_session, ALZ) != _family_name(db_session, SDB)


def test_conflicting_existing_family_raises_detailed_conflict(db_session):
    system = db_session.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one_or_none()
    if system is None:
        system = OntologyBodySystem(id=uuid.uuid4(), system_name=SYSTEM_NAME)
        db_session.add(system)
        db_session.flush()
    wrong_family = OntologyDiseaseFamily(
        id=uuid.uuid4(),
        body_system_id=system.id,
        family_name="Wrong Dementia Family",
    )
    disease = db_session.query(OntologyDisease).filter_by(disease_name=ALZ).one_or_none()
    original_family_id = None
    if disease is None:
        disease = OntologyDisease(
            id=uuid.uuid4(),
            disease_family_id=wrong_family.id,
            disease_name=ALZ,
        )
        db_session.add_all([system, wrong_family, disease])
    else:
        original_family_id = disease.disease_family_id
        db_session.add(wrong_family)
        db_session.flush()
        disease.disease_family_id = wrong_family.id
    db_session.commit()
    try:
        with pytest.raises(DiseaseFamilyOwnershipConflict) as excinfo:
            resolve_or_create_authoritative_disease(
                db_session,
                disease_name=ALZ,
                importer_name="test-importer",
                source_manifest="test-manifest.json",
                create_if_missing=False,
            )

        exc = excinfo.value
        assert exc.disease_id == disease.id
        assert exc.disease_name == ALZ
        assert exc.existing_family_id == wrong_family.id
        assert exc.existing_family_name == "Wrong Dementia Family"
        assert exc.requested_family_name == authoritative_family_name_for(ALZ)
        assert exc.importer_name == "test-importer"
        assert exc.source_manifest == "test-manifest.json"
    finally:
        if original_family_id is not None:
            disease.disease_family_id = original_family_id
            db_session.commit()


def test_reruns_do_not_duplicate_neurologic_disease_rows(db_session):
    _run_order(db_session, ("dementia", "phase2"))
    first_count = db_session.query(OntologyDisease).filter(OntologyDisease.disease_name.in_([ALZ, SDB])).count()

    run_dementia_hardening_script(db_session)
    db_session.commit()
    run_phase2_script(db_session)
    db_session.commit()

    second_count = db_session.query(OntologyDisease).filter(OntologyDisease.disease_name.in_([ALZ, SDB])).count()
    assert first_count == 2
    assert second_count == first_count
