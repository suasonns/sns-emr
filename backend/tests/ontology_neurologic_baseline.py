# tests/ontology_neurologic_baseline.py
"""Canonical, single-source-of-truth prerequisite baseline for every
Neurologic-system ontology test module (Issue #63D-adjacent stabilization).

WHY THIS FILE EXISTS
--------------------
Multiple test files previously hand-rolled their own private
`_seed_base_diseases()` helper to bring the five pre-existing Neurologic
diseases (Stroke, Hemiplegia, Hemiparesis, Contracture, Dementia Due To
Alzheimer's Disease) into existence before exercising a script under test.
Two INCOMPATIBLE family-name mappings existed across those copies:

    - the correct mapping (matching the production
      `expand_ontology_phase2_neurologic.py` docstring/contract):
          Stroke, Hemiplegia, Hemiparesis, Contracture -> "Cerebrovascular
          Disease"; Dementia Due To Alzheimer's Disease -> "Dementia
          Disorders"
    - a second, WRONG mapping that a few files invented independently:
          Stroke -> "Cerebrovascular Disease"; every other disease ->
          "Neurodegenerative Disease" (never a real production family)

Because the `ontology_*` tables carry no `tenant_id` column, they are never
cleared between tests (see `db_session` in conftest.py) -- whichever test
module's fixture ran FIRST in a given pytest session "won" and created
these rows, silently determining every later module's disease-family
assertions. That is a non-deterministic, order-dependent test defect, not a
production defect: production code (`expand_ontology_phase2_neurologic.py`)
never creates or renames these families itself -- it only resolves the
five diseases by name and requires them to already exist.

This module is now the ONE authoritative place that defines and seeds that
baseline. Every test module that needs the five pre-existing diseases to
exist must import and call `seed_base_neurologic_diseases()` (or use the
`canonical_neurologic_baseline` fixture) instead of inventing its own copy.
"""

from __future__ import annotations

from typing import Dict

import pytest

from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDisease,
    OntologyDiseaseFamily,
)
from app.ontology.disease_family_ownership import BASE_DISEASE_FAMILY, resolve_or_create_authoritative_disease
from scripts.expand_ontology_phase2_neurologic import (
    ALZ,
    CONTRACTURE,
    EXISTING_DISEASE_NAMES,
    HEMIPARESIS,
    HEMIPLEGIA,
    STROKE,
    SYSTEM_NAME,
)
from scripts.expand_ontology_phase2_neurologic import run as run_phase2_script
from scripts.complete_ontology_phase2_neurologic_coverage import run as run_coverage_repair_script
from scripts.complete_ontology_neurologic_clinical_reasoning import run as run_clinical_reasoning_script

class MissingOntologyPrerequisiteError(RuntimeError):
    """Raised when a required prerequisite disease/family/manifest cannot
    be resolved after the canonical seed step. Carries the exact missing
    identity in its message (MISSING_ONTOLOGY_PREREQUISITE: <name>)."""


def seed_base_neurologic_diseases(db_session) -> None:
    """Idempotent get-or-create seed of the five pre-existing Neurologic
    diseases under their one authoritative family mapping
    (`BASE_DISEASE_FAMILY`). Safe to call from any test module, any number
    of times, in any order relative to other modules -- it never creates a
    second family for an already-resolved disease and never re-families an
    existing disease row.
    """
    system = db_session.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one_or_none()
    if system is None:
        system = OntologyBodySystem(system_name=SYSTEM_NAME)
        db_session.add(system)
        db_session.flush()

    for name in EXISTING_DISEASE_NAMES:
        resolve_or_create_authoritative_disease(
            db_session,
            disease_name=name,
            importer_name="tests.ontology_neurologic_baseline",
            source_manifest=__file__,
            system_name=SYSTEM_NAME,
            create_if_missing=True,
        )
    db_session.flush()


def build_canonical_neurologic_baseline(db_session) -> Dict[str, OntologyDisease]:
    """Deterministically import every declared prerequisite for the
    Neurologic-system ontology test suite, in a fixed order, and return the
    resolved disease map. Explicitly imports each prerequisite manifest
    rather than relying on another test module having run first.

    Order (fixed, never alphabetical/collection-order dependent):
        1. seed the five pre-existing base diseases (this module)
        2. Phase 2 expansion (adds Senile Degeneration of Brain)
        3. Phase 2 atomic-concept coverage repair
        4. Neurologic clinical-reasoning Tier 4/5 build

    Raises MissingOntologyPrerequisiteError if any of the six required
    diseases cannot be resolved after import.
    """
    seed_base_neurologic_diseases(db_session)
    db_session.commit()
    run_phase2_script(db_session)
    db_session.commit()
    run_coverage_repair_script(db_session)
    db_session.commit()
    run_clinical_reasoning_script(db_session)
    db_session.commit()

    from scripts.expand_ontology_phase2_neurologic import ALL_DISEASE_NAMES

    diseases: Dict[str, OntologyDisease] = {}
    missing = []
    for name in ALL_DISEASE_NAMES:
        disease = db_session.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
        if disease is None:
            missing.append(name)
        else:
            diseases[name] = disease
    if missing:
        raise MissingOntologyPrerequisiteError(
            f"MISSING_ONTOLOGY_PREREQUISITE: {missing}"
        )
    return diseases


@pytest.fixture()
def canonical_neurologic_baseline(db_session):
    """Pytest fixture wrapping `build_canonical_neurologic_baseline`. Each
    step is idempotent (get-or-create), so calling this fixture from many
    test modules within the same test session/database is always safe and
    never produces duplicate rows, regardless of which module runs first."""
    return build_canonical_neurologic_baseline(db_session)
