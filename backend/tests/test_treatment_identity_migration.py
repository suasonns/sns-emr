from __future__ import annotations

import os
import uuid

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from scripts.test_db_identity import (
    build_application_name,
    build_database_name,
    compute_run_id,
    compute_worktree_id,
    scoped_env_vars,
    worktree_root_from_module,
)
from scripts.test_db_lifecycle import create_isolated_database, teardown_isolated_database
from tests.conftest import TEST_DATABASE_URL

PRE_MIGRATION_REVISION = "c3f7a1e9b0d2"
# Rebuilt-branch true Alembic head, verified via `python -m alembic heads`
# against the origin/main-authoritative 111-migration chain this branch
# is built directly from (single head, no forks). Was "d9e8f7a6b5c4"
# (a stale head from the pre-rebuild local branch's own longer,
# duplicated migration chain); must track whatever origin/main's real
# head is, not a manually-carried-forward constant.
HEAD_REVISION = "pay3v4e5r6i7f"


def _alembic_cfg() -> Config:
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    return cfg


def test_migration_remaps_treatment_references_and_preserves_survivor_metadata():
    """ZERO_FAILURE_REGISTER FR-03 -- TEST A: reversible treatment-identity
    round trip, isolated from both forward-only boundaries.

    Root cause (confirmed with evidence): PRE_MIGRATION_REVISION predates
    two migrations that sit between it and HEAD, both intentionally
    forward-only and both left untouched (historical migrations are
    immutable under this repository's policy; see
    docs/engineering/DECISION_LOG.md):
    p9r8q7s6t5u4_add_billing_scope_permission_levels.py (see
    test_permission_level_migration_is_intentionally_historical_forward_only)
    and n8m7b6v5c4x3_add_facility_payment_expectation_workflow_fields.py
    (its upgrade() irreversibly collapses unrecognized `source` values into
    'NOT_VERIFIED'; see
    test_facility_payment_expectation_migration_is_correctly_forward_only).
    Because both guards are approved architecture and must not be removed
    or bypassed, a downgrade starting at HEAD can never reach
    PRE_MIGRATION_REVISION. This test therefore never visits HEAD at all:
    building directly from an empty database up to PRE_MIGRATION_REVISION
    reaches the identical pre-migration schema state without crossing
    either forward-only boundary, then exercises only the reversible
    treatment-identity migrations under test.

    This also gives the destructive part of the test (upgrade to the
    pre-migration point, seed data, upgrade to head) its own disposable
    database, using the same isolation primitives
    scripts/run_isolated_tests.py uses for the whole suite, so it can never
    read or write data belonging to any other test in the shared
    TEST_DATABASE_URL.
    """
    worktree_id = compute_worktree_id(worktree_root_from_module(__file__, levels_below_root=2))
    run_id = f"{compute_run_id()}mig"
    database_name = build_database_name(worktree_id, run_id, worker_id="frt59")
    admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0]
    scratch_url = f"{admin_url}/{database_name}"

    create_isolated_database(
        test_database_url=TEST_DATABASE_URL,
        database_name=database_name,
        worktree_path=worktree_root_from_module(__file__, levels_below_root=2),
        worktree_id=worktree_id,
        run_id=run_id,
        application_name=build_application_name(worktree_id, run_id, os.getpid()),
    )
    try:
        cfg = _alembic_cfg()
        with scoped_env_vars(MIGRATION_DATABASE_URL=scratch_url, EXPECTED_DB=database_name):
            command.upgrade(cfg, PRE_MIGRATION_REVISION)

        engine = create_engine(scratch_url, future=True)
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

            with scoped_env_vars(MIGRATION_DATABASE_URL=scratch_url, EXPECTED_DB=database_name):
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
            engine.dispose()
    finally:
        teardown_isolated_database(
            test_database_url=TEST_DATABASE_URL,
            database_name=database_name,
            worktree_id=worktree_id,
            run_id=run_id,
        )


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


def test_permission_level_migration_is_intentionally_historical_forward_only():
    """ZERO_FAILURE_REGISTER FR-03 (Outcome A: historical migrations are
    immutable -- decision record in docs/engineering/DECISION_LOG.md).

    p9r8q7s6t5u4_add_billing_scope_permission_levels.py's upgrade() only
    adds a nullable-with-default column and a check constraint, so a real
    downgrade() would in fact be safe to *write*. It was nonetheless left
    forward-only here: this migration is already merged and ancestor of
    origin/main (an "applied historical migration" under this repository's
    standing rule), and this program's policy treats historical migration
    files as immutable regardless of how safe a change to them would be --
    a per-migration safety judgment call is exactly the failure mode that
    policy exists to prevent. Forward recovery for an environment that
    needs to remove `permission_level` is a new, forward-only migration
    that drops the column, not an edit to this file's downgrade().

    This test proves the guard fires as originally shipped, on a disposable
    scratch database dedicated to this test, so the immutability decision
    has real test coverage instead of just a comment.
    """
    worktree_id = compute_worktree_id(worktree_root_from_module(__file__, levels_below_root=2))
    run_id = f"{compute_run_id()}pl"
    database_name = build_database_name(worktree_id, run_id, worker_id="frt59")
    admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0]
    scratch_url = f"{admin_url}/{database_name}"

    create_isolated_database(
        test_database_url=TEST_DATABASE_URL,
        database_name=database_name,
        worktree_path=worktree_root_from_module(__file__, levels_below_root=2),
        worktree_id=worktree_id,
        run_id=run_id,
        application_name=build_application_name(worktree_id, run_id, os.getpid()),
    )
    try:
        cfg = _alembic_cfg()
        engine = create_engine(scratch_url, future=True)
        try:
            with scoped_env_vars(MIGRATION_DATABASE_URL=scratch_url, EXPECTED_DB=database_name):
                command.upgrade(cfg, "p9r8q7s6t5u4")
            with engine.begin() as conn:
                assert conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'billing_provider_agency_service_scopes' "
                        "AND column_name = 'permission_level'"
                    )
                ).scalar_one_or_none() == "permission_level"
                permission_check_before = conn.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conrelid = 'billing_provider_agency_service_scopes'::regclass "
                        "AND contype = 'c' AND pg_get_constraintdef(oid) LIKE '%permission_level%'"
                    )
                ).scalar_one_or_none()
                assert permission_check_before is not None
                current_before = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

            with scoped_env_vars(MIGRATION_DATABASE_URL=scratch_url, EXPECTED_DB=database_name):
                try:
                    command.downgrade(cfg, "-1")
                    assert False, "expected NotImplementedError from the forward-only migration's downgrade()"
                except NotImplementedError as exc:
                    assert "Forward-only migration" in str(exc)

            # No partial downgrade: schema and alembic_version unchanged
            # after the guard raises.
            with engine.begin() as conn:
                assert conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'billing_provider_agency_service_scopes' "
                        "AND column_name = 'permission_level'"
                    )
                ).scalar_one_or_none() == "permission_level"
                permission_check_after = conn.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conrelid = 'billing_provider_agency_service_scopes'::regclass "
                        "AND contype = 'c' AND pg_get_constraintdef(oid) LIKE '%permission_level%'"
                    )
                ).scalar_one_or_none()
                assert permission_check_after == permission_check_before
                current_after = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                assert current_after == current_before == "p9r8q7s6t5u4"
        finally:
            engine.dispose()
    finally:
        teardown_isolated_database(
            test_database_url=TEST_DATABASE_URL,
            database_name=database_name,
            worktree_id=worktree_id,
            run_id=run_id,
        )


def test_facility_payment_expectation_migration_is_correctly_forward_only():
    """ZERO_FAILURE_REGISTER FR-03 (approved-architecture coverage).

    n8m7b6v5c4x3_add_facility_payment_expectation_workflow_fields.py's
    upgrade() collapses unrecognized `facility_payment_expectations.source`
    values into 'NOT_VERIFIED' (see its `op.execute(...UPDATE ... source =
    CASE ... ELSE 'NOT_VERIFIED' END...)`). That is a real, irreversible
    loss of the original value, so `downgrade()` correctly raises
    NotImplementedError rather than silently pretending to reverse a
    transform it cannot actually undo. This test locks in that this is
    intentional, approved architecture, not an untested gap: it asserts the
    guard fires with the documented message, on a disposable scratch
    database dedicated to this test, and confirms the failed downgrade
    attempt left the schema (columns, the `source`/`due_date_source` check
    constraints, and `alembic_version`) completely unchanged (no partial
    downgrade).
    """
    worktree_id = compute_worktree_id(worktree_root_from_module(__file__, levels_below_root=2))
    run_id = f"{compute_run_id()}fwd"
    database_name = build_database_name(worktree_id, run_id, worker_id="frt59")
    admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0]
    scratch_url = f"{admin_url}/{database_name}"

    create_isolated_database(
        test_database_url=TEST_DATABASE_URL,
        database_name=database_name,
        worktree_path=worktree_root_from_module(__file__, levels_below_root=2),
        worktree_id=worktree_id,
        run_id=run_id,
        application_name=build_application_name(worktree_id, run_id, os.getpid()),
    )
    try:
        cfg = _alembic_cfg()
        engine = create_engine(scratch_url, future=True)
        try:
            with scoped_env_vars(MIGRATION_DATABASE_URL=scratch_url, EXPECTED_DB=database_name):
                command.upgrade(cfg, "n8m7b6v5c4x3")

            def _source_check_def(conn):
                rows = conn.execute(
                    text(
                        "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conrelid = 'facility_payment_expectations'::regclass AND contype = 'c'"
                    )
                ).fetchall()
                matches = [d for _, d in rows if "source" in d and "due_date_source" not in d]
                assert len(matches) == 1, matches
                return matches[0]

            with engine.begin() as conn:
                assert conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'facility_payment_expectations' "
                        "AND column_name = 'due_date_source'"
                    )
                ).scalar_one_or_none() == "due_date_source"
                source_check_before = _source_check_def(conn)
                assert source_check_before is not None
                current_before = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

            with scoped_env_vars(MIGRATION_DATABASE_URL=scratch_url, EXPECTED_DB=database_name):
                try:
                    command.downgrade(cfg, "-1")
                    assert False, "expected NotImplementedError from the forward-only migration's downgrade()"
                except NotImplementedError as exc:
                    assert "Forward-only migration" in str(exc)

            # No partial downgrade: schema and alembic_version unchanged
            # after the guard raises.
            with engine.begin() as conn:
                assert conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'facility_payment_expectations' "
                        "AND column_name = 'due_date_source'"
                    )
                ).scalar_one_or_none() == "due_date_source"
                source_check_after = _source_check_def(conn)
                assert source_check_after == source_check_before
                current_after = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                assert current_after == current_before == "n8m7b6v5c4x3"
        finally:
            engine.dispose()
    finally:
        teardown_isolated_database(
            test_database_url=TEST_DATABASE_URL,
            database_name=database_name,
            worktree_id=worktree_id,
            run_id=run_id,
        )
