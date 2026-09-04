from __future__ import annotations

import os
import uuid

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from scripts.test_db_identity import scoped_env_vars
from tests.conftest import TEST_DATABASE_URL

PRE_MIGRATION_REVISION = "c3f7a1e9b0d2"
HEAD_REVISION = "d9e8f7a6b5c4"


def _alembic_cfg() -> Config:
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    return cfg


def test_migration_remaps_treatment_references_and_preserves_survivor_metadata():
    engine = create_engine(TEST_DATABASE_URL, future=True)
    cfg = _alembic_cfg()
    with scoped_env_vars(MIGRATION_DATABASE_URL=TEST_DATABASE_URL, EXPECTED_DB=TEST_DATABASE_URL.rsplit("/", 1)[-1]):
        command.downgrade(cfg, PRE_MIGRATION_REVISION)
    try:
        ids = {name: str(uuid.uuid4()) for name in [
            "system", "family", "disease", "survivor", "loser", "variant", "applicability", "evidence", "relationship"
        ]}
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO ontology_body_system (id, system_name, active) VALUES (:id, 'Migration Neurologic System', true)"), {"id": ids["system"]})
            conn.execute(
                text("INSERT INTO ontology_disease_family (id, body_system_id, family_name, active) VALUES (:id, :system_id, 'Migration Cerebrovascular Disease', true)"),
                {"id": ids["family"], "system_id": ids["system"]},
            )
            conn.execute(
                text("INSERT INTO ontology_disease (id, disease_family_id, disease_name, active) VALUES (:id, :family_id, 'Migration Stroke', true)"),
                {"id": ids["disease"], "family_id": ids["family"]},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO ontology_disease_treatment (id, disease_id, treatment_name, treatment_category, description)
                    VALUES (:survivor, :disease_id, 'Serial Casting', 'SUPPORTIVE', 'keep display text'),
                           (:loser, :disease_id, 'Serial Casting', 'DISEASE_DIRECTED', 'duplicate row')
                    """
                ),
                {"survivor": ids["survivor"], "loser": ids["loser"], "disease_id": ids["disease"]},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO ontology_disease_variant (
                        id, disease_id, parent_variant_id, variant_name, normalized_name, variant_dimension,
                        evidence_requirement, source_reference, active
                    )
                    VALUES (:id, :disease_id, NULL, 'Historical Stroke', 'historical stroke', 'DISEASE_PHASE',
                            'Requires evidence', 'test', true)
                    """
                ),
                {"id": ids["variant"], "disease_id": ids["disease"]},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO ontology_concept_variant_applicability (
                        id, disease_id, concept_type, concept_id, variant_id, applicability_type, active
                    )
                    VALUES (:id, :disease_id, 'TREATMENT', :concept_id, :variant_id, 'EXPECTED_WITH', true)
                    """
                ),
                {"id": ids["applicability"], "disease_id": ids["disease"], "concept_id": ids["loser"], "variant_id": ids["variant"]},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO ontology_evidence_rule (
                        id, concept_type, concept_id, evidence_source, evidence_type, confidence, patient_fact_requires_evidence
                    )
                    VALUES (:id, 'TREATMENT', :concept_id, 'test', 'MANIFEST_ATOMIC_CONCEPT', 'HIGH', true)
                    """
                ),
                {"id": ids["evidence"], "concept_id": ids["loser"]},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO ontology_relationship (
                        id, source_concept_type, source_concept_id, relationship_type, target_concept_type, target_concept_id, active
                    )
                    VALUES (:id, 'TREATMENT', :source_id, 'RELATES_TO', 'TREATMENT', :target_id, true)
                    """
                ),
                {"id": ids["relationship"], "source_id": ids["loser"], "target_id": ids["loser"]},
            )

        with scoped_env_vars(MIGRATION_DATABASE_URL=TEST_DATABASE_URL, EXPECTED_DB=TEST_DATABASE_URL.rsplit("/", 1)[-1]):
            command.upgrade(cfg, "head")

        with engine.begin() as conn:
            treatment_rows = conn.execute(
                text(
                    """
                    SELECT id, treatment_name, normalized_name, treatment_category
                      FROM ontology_disease_treatment
                     WHERE disease_id = :disease_id
                    """
                ),
                {"disease_id": ids["disease"]},
            ).mappings().all()
            assert len(treatment_rows) == 1
            survivor = treatment_rows[0]
            assert survivor["id"] == uuid.UUID(ids["survivor"])
            assert survivor["treatment_name"] == "Serial Casting"
            assert survivor["normalized_name"] == "serial casting"
            assert survivor["treatment_category"] == "DISEASE_DIRECTED"

            assert conn.execute(text("SELECT concept_id FROM ontology_evidence_rule WHERE id = :id"), {"id": ids["evidence"]}).scalar_one() == uuid.UUID(ids["survivor"])
            assert conn.execute(text("SELECT concept_id FROM ontology_concept_variant_applicability WHERE id = :id"), {"id": ids["applicability"]}).scalar_one() == uuid.UUID(ids["survivor"])
            rel = conn.execute(
                text("SELECT source_concept_id, target_concept_id FROM ontology_relationship WHERE id = :id"),
                {"id": ids["relationship"]},
            ).one()
            assert rel[0] == uuid.UUID(ids["survivor"])
            assert rel[1] == uuid.UUID(ids["survivor"])
            assert conn.execute(
                text(
                    """
                    SELECT count(*)
                      FROM ontology_evidence_rule er
                     WHERE er.concept_type = 'TREATMENT'
                       AND NOT EXISTS (SELECT 1 FROM ontology_disease_treatment t WHERE t.id = er.concept_id)
                    """
                )
            ).scalar_one() == 0
    finally:
        with scoped_env_vars(MIGRATION_DATABASE_URL=TEST_DATABASE_URL, EXPECTED_DB=TEST_DATABASE_URL.rsplit("/", 1)[-1]):
            command.upgrade(cfg, "head")
        engine.dispose()


def test_migration_downgrade_and_reupgrade_leave_current_equal_to_head():
    engine = create_engine(TEST_DATABASE_URL, future=True)
    cfg = _alembic_cfg()
    try:
        with scoped_env_vars(MIGRATION_DATABASE_URL=TEST_DATABASE_URL, EXPECTED_DB=TEST_DATABASE_URL.rsplit("/", 1)[-1]):
            command.downgrade(cfg, "-1")
            command.upgrade(cfg, "head")
        heads = set(ScriptDirectory.from_config(cfg).get_heads())
        with engine.begin() as conn:
            current = {row[0] for row in conn.execute(text("SELECT version_num FROM alembic_version"))}
        assert current == heads == {HEAD_REVISION}
    finally:
        with scoped_env_vars(MIGRATION_DATABASE_URL=TEST_DATABASE_URL, EXPECTED_DB=TEST_DATABASE_URL.rsplit("/", 1)[-1]):
            command.upgrade(cfg, "head")
        engine.dispose()
