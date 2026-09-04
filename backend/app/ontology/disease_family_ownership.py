from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDisease,
    OntologyDiseaseFamily,
)

NEUROLOGIC_SYSTEM_NAME = "Neurologic System"

STROKE = "Stroke"
HEMIPLEGIA = "Hemiplegia"
HEMIPARESIS = "Hemiparesis"
CONTRACTURE = "Contracture"
ALZHEIMERS_DEMENTIA = "Dementia Due To Alzheimer's Disease"
SENILE_DEGENERATION_OF_BRAIN = "Senile Degeneration of Brain"

# Authoritative disease-family ownership inventory:
# - expand_ontology_phase2_neurologic.py is the originating/approving source
#   for the ONE new canonical disease introduced in this area:
#   Senile Degeneration of Brain -> Degenerative Brain Disorders.
# - import_dementia_production_hardening.py only hardens the pre-existing
#   Alzheimer's disease and does not own Senile Degeneration of Brain's family.
BASE_DISEASE_FAMILY = {
    STROKE: "Cerebrovascular Disease",
    HEMIPLEGIA: "Cerebrovascular Disease",
    HEMIPARESIS: "Cerebrovascular Disease",
    CONTRACTURE: "Cerebrovascular Disease",
    ALZHEIMERS_DEMENTIA: "Dementia Disorders",
}

AUTHORITATIVE_DISEASE_FAMILY = {
    **BASE_DISEASE_FAMILY,
    SENILE_DEGENERATION_OF_BRAIN: "Degenerative Brain Disorders",
}


class DiseaseFamilyOwnershipConflict(RuntimeError):
    def __init__(
        self,
        *,
        disease_id,
        disease_name: str,
        existing_family_id,
        existing_family_name: str,
        requested_family_id,
        requested_family_name: str,
        importer_name: str,
        source_manifest: str | None = None,
    ) -> None:
        self.disease_id = disease_id
        self.disease_name = disease_name
        self.existing_family_id = existing_family_id
        self.existing_family_name = existing_family_name
        self.requested_family_id = requested_family_id
        self.requested_family_name = requested_family_name
        self.importer_name = importer_name
        self.source_manifest = source_manifest
        super().__init__(
            "Disease family ownership conflict for "
            f"{disease_name!r}: existing_family={existing_family_name!r} ({existing_family_id}), "
            f"requested_family={requested_family_name!r} ({requested_family_id}), "
            f"importer={importer_name!r}, source_manifest={source_manifest!r}, disease_id={disease_id}"
        )


def authoritative_family_name_for(disease_name: str) -> str | None:
    return AUTHORITATIVE_DISEASE_FAMILY.get(disease_name)


def get_or_create_body_system(
    db: Session,
    *,
    system_name: str = NEUROLOGIC_SYSTEM_NAME,
) -> OntologyBodySystem:
    system = db.query(OntologyBodySystem).filter_by(system_name=system_name).one_or_none()
    if system is None:
        system = OntologyBodySystem(id=uuid.uuid4(), system_name=system_name)
        db.add(system)
        db.flush()
    return system


def get_or_create_authoritative_family(
    db: Session,
    *,
    disease_name: str,
    importer_name: str,
    source_manifest: str | None = None,
    system_name: str = NEUROLOGIC_SYSTEM_NAME,
) -> OntologyDiseaseFamily:
    family_name = authoritative_family_name_for(disease_name)
    if family_name is None:
        raise KeyError(f"No authoritative disease-family ownership mapping exists for {disease_name!r}.")
    system = get_or_create_body_system(db, system_name=system_name)
    family = (
        db.query(OntologyDiseaseFamily)
        .filter_by(body_system_id=system.id, family_name=family_name)
        .one_or_none()
    )
    if family is None:
        family = OntologyDiseaseFamily(id=uuid.uuid4(), body_system_id=system.id, family_name=family_name)
        db.add(family)
        db.flush()
    return family


def assert_authoritative_disease_family(
    db: Session,
    disease: OntologyDisease,
    *,
    importer_name: str,
    source_manifest: str | None = None,
    system_name: str = NEUROLOGIC_SYSTEM_NAME,
) -> OntologyDisease:
    expected_name = authoritative_family_name_for(disease.disease_name)
    if expected_name is None:
        return disease
    requested_family = get_or_create_authoritative_family(
        db,
        disease_name=disease.disease_name,
        importer_name=importer_name,
        source_manifest=source_manifest,
        system_name=system_name,
    )
    existing_family = disease.disease_family
    if existing_family is None:
        existing_family = db.query(OntologyDiseaseFamily).filter_by(id=disease.disease_family_id).one()
    if (
        existing_family.id != requested_family.id
        or existing_family.family_name != requested_family.family_name
        or existing_family.body_system_id != requested_family.body_system_id
    ):
        raise DiseaseFamilyOwnershipConflict(
            disease_id=disease.id,
            disease_name=disease.disease_name,
            existing_family_id=existing_family.id,
            existing_family_name=existing_family.family_name,
            requested_family_id=requested_family.id,
            requested_family_name=requested_family.family_name,
            importer_name=importer_name,
            source_manifest=source_manifest,
        )
    return disease


def resolve_or_create_authoritative_disease(
    db: Session,
    *,
    disease_name: str,
    importer_name: str,
    source_manifest: str | None = None,
    system_name: str = NEUROLOGIC_SYSTEM_NAME,
    create_if_missing: bool,
    create_kwargs: dict[str, Any] | None = None,
) -> OntologyDisease:
    disease = db.query(OntologyDisease).filter_by(disease_name=disease_name).one_or_none()
    if disease is not None:
        return assert_authoritative_disease_family(
            db,
            disease,
            importer_name=importer_name,
            source_manifest=source_manifest,
            system_name=system_name,
        )
    if not create_if_missing:
        raise RuntimeError(
            f"{importer_name} requires pre-existing disease {disease_name!r} under its authoritative family."
        )
    family = get_or_create_authoritative_family(
        db,
        disease_name=disease_name,
        importer_name=importer_name,
        source_manifest=source_manifest,
        system_name=system_name,
    )
    kwargs = dict(create_kwargs or {})
    disease = OntologyDisease(
        id=uuid.uuid4(),
        disease_name=disease_name,
        disease_family_id=family.id,
        **kwargs,
    )
    db.add(disease)
    db.flush()
    return disease
