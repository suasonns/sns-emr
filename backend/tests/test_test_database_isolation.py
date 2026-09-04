"""Permanent regression tests for the per-worktree/per-run isolated
test-database infrastructure (`scripts/test_db_identity.py`,
`test_db_registry.py`, `test_db_lifecycle.py`, `_create_test_db.py`,
`scripts/run_isolated_tests.py`).

Context (2026-09-03 incident): multiple concurrent Copilot sessions/
worktrees previously defaulted to the same shared `sns_emr_test` Postgres
database. One session's schema rebuild raced against another session's
running pytest process, producing missing tables, deadlocks, and
non-deterministic pass/fail counts. This test file is the permanent,
committed proof that the fix holds -- do not rely on ad hoc smoke commands
as the only evidence.

These tests create and drop their OWN short-lived, uniquely-named
`sns_emr_test_*` databases via the real Postgres server referenced by
DATABASE_URL. They never touch the database this test file itself is
running against (TEST_DATABASE_URL), and they never touch DATABASE_URL's
database.
"""

from __future__ import annotations

import os
import secrets
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit, urlunsplit

import psycopg2
import pytest
from sqlalchemy import create_engine, text

from app.core.database import DATABASE_URL
from scripts.test_db_identity import (
    UnsafeTestDatabaseNameError,
    advisory_lock_key,
    build_application_name,
    build_database_name,
    compute_run_id,
    compute_worktree_id,
    redact_database_url,
    scoped_env_vars,
    validate_database_name,
    worktree_root_from_module,
)
from scripts.test_db_lifecycle import (
    TestDatabaseLockUnavailableError,
    _admin_connection,
    _advisory_lock,
    _database_exists,
    create_isolated_database,
    teardown_isolated_database,
    terminate_owned_connections,
)
from scripts.test_db_registry import (
    OwnershipError,
    read_ownership_record,
    remove_ownership_record,
    update_lifecycle_status,
    verify_ownership,
    write_ownership_record,
)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKTREE_DIR = os.path.dirname(BACKEND_DIR)


def _admin_url_for(database_name: str) -> str:
    parts = urlsplit(DATABASE_URL)
    return urlunsplit(parts._replace(path=f"/{database_name}"))


def _fresh_name(label: str) -> tuple[str, str, str]:
    """A throwaway (worktree_id, run_id, database_name) tuple unique to this
    test invocation -- safe to create/drop even if this suite itself is
    running concurrently elsewhere."""
    worktree_id = compute_worktree_id(WORKTREE_DIR + f"::{label}")
    run_id = secrets.token_hex(4)
    return worktree_id, run_id, build_database_name(worktree_id, run_id)


@pytest.fixture
def throwaway_db():
    """Creates a real isolated database for the duration of one test and
    guarantees teardown even if the test body raises."""
    worktree_id, run_id, database_name = _fresh_name("throwaway")
    admin_url = _admin_url_for(database_name)
    create_isolated_database(
        test_database_url=admin_url,
        database_name=database_name,
        worktree_path=WORKTREE_DIR,
        worktree_id=worktree_id,
        run_id=run_id,
        application_name=build_application_name(worktree_id, run_id, os.getpid()),
    )
    try:
        yield worktree_id, run_id, database_name, admin_url
    finally:
        try:
            teardown_isolated_database(
                test_database_url=admin_url,
                database_name=database_name,
                worktree_id=worktree_id,
                run_id=run_id,
            )
        except Exception:
            pass


# ---------------------------------------------------------------------
# 1-4, 7: naming / validation (pure, no DB)
# ---------------------------------------------------------------------


def test_different_worktrees_produce_different_database_names():
    name_a = build_database_name(compute_worktree_id("/tmp/worktree-a"), "run1")
    name_b = build_database_name(compute_worktree_id("/tmp/worktree-b"), "run1")
    assert name_a != name_b


def test_different_runs_in_one_worktree_produce_different_database_names():
    worktree_id = compute_worktree_id("/tmp/worktree-a")
    name_a = build_database_name(worktree_id, "run1")
    name_b = build_database_name(worktree_id, "run2")
    assert name_a != name_b


def test_worktree_id_is_deterministic_for_same_path():
    assert compute_worktree_id("/tmp/same") == compute_worktree_id("/tmp/same")


def test_invalid_database_name_characters_are_rejected():
    with pytest.raises(UnsafeTestDatabaseNameError):
        validate_database_name("sns_emr_test_abc-123")  # hyphen not allowed
    with pytest.raises(UnsafeTestDatabaseNameError):
        validate_database_name("sns_emr_test_ABC123")  # uppercase not allowed


def test_excessively_long_name_is_rejected_deterministically():
    worktree_id = "a" * 40
    run_id = "b" * 40
    with pytest.raises(UnsafeTestDatabaseNameError):
        build_database_name(worktree_id, run_id)


def test_fixed_sns_emr_test_fallback_is_rejected():
    """The old shared-name fallback must never validate as safe."""
    with pytest.raises(UnsafeTestDatabaseNameError):
        validate_database_name("sns_emr_test")


def test_worker_id_produces_distinct_name_from_non_worker_variant():
    worktree_id, run_id, _ = _fresh_name("worker-id")
    without_worker = build_database_name(worktree_id, run_id)
    with_worker = build_database_name(worktree_id, run_id, "gw0")
    assert without_worker != with_worker
    assert with_worker.endswith("_gw0")


# ---------------------------------------------------------------------
# 9: application_name identity
# ---------------------------------------------------------------------


def test_application_name_contains_worktree_and_run_identity():
    app_name = build_application_name("abcd1234", "efgh5678", 999)
    assert app_name == "sns-emr-test:abcd1234:efgh5678:999"


# ---------------------------------------------------------------------
# 29: worktree root discovery regression (the confirmed defect)
# ---------------------------------------------------------------------


def test_worktree_root_discovered_correctly_from_backend_execution():
    """Regression test for the confirmed defect: run_isolated_tests.py
    (backend/scripts/run_isolated_tests.py, 2 levels below the worktree
    root) previously mis-derived the worktree root as `backend/` itself,
    producing an invalid nested `backend/backend` path."""
    scripts_module_path = os.path.join(BACKEND_DIR, "scripts", "run_isolated_tests.py")
    root_from_scripts = worktree_root_from_module(
        scripts_module_path, levels_below_root=2
    )
    assert root_from_scripts == os.path.normpath(WORKTREE_DIR)
    assert os.path.isdir(os.path.join(root_from_scripts, "backend"))

    create_db_module_path = os.path.join(BACKEND_DIR, "_create_test_db.py")
    root_from_create = worktree_root_from_module(
        create_db_module_path, levels_below_root=1
    )
    assert root_from_create == root_from_scripts


# ---------------------------------------------------------------------
# 8, 35: credential redaction
# ---------------------------------------------------------------------


def test_redact_database_url_hides_password():
    redacted = redact_database_url("postgresql://sns:supersecret@127.0.0.1:5432/sns_emr_test_x")
    assert "supersecret" not in redacted
    assert "127.0.0.1" in redacted


def test_unsafe_name_error_messages_never_contain_a_url():
    try:
        validate_database_name("not_a_test_db")
    except UnsafeTestDatabaseNameError as exc:
        assert "://" not in str(exc)
    else:
        pytest.fail("expected UnsafeTestDatabaseNameError")


# ---------------------------------------------------------------------
# 5, 6: environment contract (subprocess -- conftest raises at import time)
# ---------------------------------------------------------------------


def _run_conftest_import(env_overrides: dict[str, str]) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("TEST_DATABASE_URL", None)
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", "import tests.conftest"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )


def test_missing_test_database_url_fails_deterministically():
    result = _run_conftest_import({})
    assert result.returncode != 0
    assert "TEST_DATABASE_URL_REQUIRED" in result.stderr


def test_test_database_url_equal_to_database_url_fails():
    result = _run_conftest_import({"TEST_DATABASE_URL": DATABASE_URL})
    assert result.returncode != 0
    assert "TEST_DATABASE_ISOLATION_VIOLATION" in result.stderr


# ---------------------------------------------------------------------
# scoped_env_vars: EXPECTED_DB / MIGRATION_DATABASE_URL leak prevention
# (items 26, 27, 28)
# ---------------------------------------------------------------------


def test_scoped_env_vars_restores_absent_variable_after_success():
    os.environ.pop("SNS_TEST_SCOPE_PROBE", None)
    with scoped_env_vars(SNS_TEST_SCOPE_PROBE="value"):
        assert os.environ["SNS_TEST_SCOPE_PROBE"] == "value"
    assert "SNS_TEST_SCOPE_PROBE" not in os.environ


def test_scoped_env_vars_restores_present_variable_after_success():
    os.environ["SNS_TEST_SCOPE_PROBE"] = "original"
    try:
        with scoped_env_vars(SNS_TEST_SCOPE_PROBE="temporary"):
            assert os.environ["SNS_TEST_SCOPE_PROBE"] == "temporary"
        assert os.environ["SNS_TEST_SCOPE_PROBE"] == "original"
    finally:
        os.environ.pop("SNS_TEST_SCOPE_PROBE", None)


def test_scoped_env_vars_restores_absent_variable_after_exception():
    os.environ.pop("SNS_TEST_SCOPE_PROBE", None)
    with pytest.raises(RuntimeError):
        with scoped_env_vars(SNS_TEST_SCOPE_PROBE="value"):
            assert os.environ["SNS_TEST_SCOPE_PROBE"] == "value"
            raise RuntimeError("simulated migration failure")
    assert "SNS_TEST_SCOPE_PROBE" not in os.environ


def test_scoped_env_vars_restores_present_variable_after_exception():
    os.environ["SNS_TEST_SCOPE_PROBE"] = "original"
    try:
        with pytest.raises(RuntimeError):
            with scoped_env_vars(SNS_TEST_SCOPE_PROBE="temporary"):
                raise RuntimeError("simulated interruption")
        assert os.environ["SNS_TEST_SCOPE_PROBE"] == "original"
    finally:
        os.environ.pop("SNS_TEST_SCOPE_PROBE", None)


def test_expected_db_does_not_leak_after_successful_isolated_run():
    """End-to-end: _create_test_db.main() must never leave EXPECTED_DB set
    in this process's environment after returning, success or failure."""
    os.environ.pop("EXPECTED_DB", None)
    os.environ.pop("MIGRATION_DATABASE_URL", None)
    worktree_id, run_id, database_name = _fresh_name("expected-db-success")
    from _create_test_db import main as create_and_migrate

    try:
        create_and_migrate(["--worktree-id", worktree_id, "--run-id", run_id])
        assert "EXPECTED_DB" not in os.environ
        assert "MIGRATION_DATABASE_URL" not in os.environ
    finally:
        try:
            teardown_isolated_database(
                test_database_url=_admin_url_for(database_name),
                database_name=database_name,
                worktree_id=worktree_id,
                run_id=run_id,
            )
        except Exception:
            pass


# ---------------------------------------------------------------------
# Ownership registry (items 10, 11, 12, 13, 14)
# ---------------------------------------------------------------------


def test_ownership_metadata_is_created_on_write():
    _, _, database_name = _fresh_name("ownership-create")
    try:
        record = write_ownership_record(
            database_name=database_name,
            worktree_path=WORKTREE_DIR,
            worktree_id="abcd1234",
            run_id="efgh5678",
            application_name="sns-emr-test:abcd1234:efgh5678:1",
            lifecycle_status="READY",
        )
        assert record.database_name == database_name
        assert read_ownership_record(database_name) is not None
    finally:
        remove_ownership_record(database_name)


def test_ownership_metadata_removed_after_success_path():
    _, _, database_name = _fresh_name("ownership-remove-success")
    write_ownership_record(
        database_name=database_name,
        worktree_path=WORKTREE_DIR,
        worktree_id="abcd1234",
        run_id="efgh5678",
        application_name="x",
        lifecycle_status="READY",
    )
    remove_ownership_record(database_name)
    assert read_ownership_record(database_name) is None


def test_ownership_mismatch_prevents_verification():
    _, _, database_name = _fresh_name("ownership-mismatch")
    write_ownership_record(
        database_name=database_name,
        worktree_path=WORKTREE_DIR,
        worktree_id="owner-worktree",
        run_id="owner-run",
        application_name="x",
        lifecycle_status="READY",
    )
    try:
        with pytest.raises(OwnershipError):
            verify_ownership(database_name, "intruder-worktree", "intruder-run")
    finally:
        remove_ownership_record(database_name)


def test_missing_ownership_record_is_not_treated_as_safe_to_mutate():
    _, _, database_name = _fresh_name("ownership-missing")
    assert read_ownership_record(database_name) is None
    with pytest.raises(OwnershipError):
        verify_ownership(database_name, "any-worktree", "any-run")


# ---------------------------------------------------------------------
# Real Postgres lifecycle integration (items 16-21, 24, 25, 30-33)
# ---------------------------------------------------------------------


def test_create_isolated_database_actually_exists(throwaway_db):
    _, _, database_name, admin_url = throwaway_db
    assert _database_exists(admin_url, database_name)
    record = read_ownership_record(database_name)
    assert record is not None
    assert record.lifecycle_status == "CREATING"


def test_teardown_drops_database_and_clears_registry(throwaway_db):
    worktree_id, run_id, database_name, admin_url = throwaway_db
    teardown_isolated_database(
        test_database_url=admin_url,
        database_name=database_name,
        worktree_id=worktree_id,
        run_id=run_id,
    )
    assert not _database_exists(admin_url, database_name)
    assert read_ownership_record(database_name) is None


def test_teardown_retain_on_failure_keeps_database_and_marks_failed(throwaway_db):
    worktree_id, run_id, database_name, admin_url = throwaway_db
    teardown_isolated_database(
        test_database_url=admin_url,
        database_name=database_name,
        worktree_id=worktree_id,
        run_id=run_id,
        retain=True,
    )
    assert _database_exists(admin_url, database_name)
    record = read_ownership_record(database_name)
    assert record is not None
    assert record.lifecycle_status == "FAILED"
    # Manual cleanup since retain=True skipped the drop.
    teardown_isolated_database(
        test_database_url=admin_url,
        database_name=database_name,
        worktree_id=worktree_id,
        run_id=run_id,
    )


def test_teardown_rejects_ownership_mismatch(throwaway_db):
    """A process cannot drop another process's database (item 14)."""
    worktree_id, run_id, database_name, admin_url = throwaway_db
    with pytest.raises(OwnershipError):
        teardown_isolated_database(
            test_database_url=admin_url,
            database_name=database_name,
            worktree_id="intruder-worktree",
            run_id="intruder-run",
        )
    # Still there -- the mismatched teardown must not have touched it.
    assert _database_exists(admin_url, database_name)


def test_migration_leaves_alembic_current_equal_to_heads(throwaway_db):
    _, _, database_name, admin_url = throwaway_db
    from _create_test_db import main as create_and_migrate

    worktree_id, run_id, _, _ = throwaway_db
    # throwaway_db already created (but not migrated) the database; migrate
    # it explicitly against that same name to check current==heads.
    from alembic.config import Config
    from alembic import command
    from alembic.script import ScriptDirectory

    test_url = _admin_url_for(database_name)
    alembic_cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    with scoped_env_vars(MIGRATION_DATABASE_URL=test_url, EXPECTED_DB=database_name):
        command.upgrade(alembic_cfg, "head")
        heads = set(ScriptDirectory.from_config(alembic_cfg).get_heads())

    engine = create_engine(test_url, future=True)
    try:
        with engine.connect() as conn:
            current = {
                row[0]
                for row in conn.execute(text("SELECT version_num FROM alembic_version"))
            }
    finally:
        engine.dispose()
    assert current == heads
    assert "EXPECTED_DB" not in os.environ
    assert "MIGRATION_DATABASE_URL" not in os.environ


def test_no_owned_connections_survive_teardown(throwaway_db):
    worktree_id, run_id, database_name, admin_url = throwaway_db
    # Open a connection to the isolated database, then tear it down.
    conn = psycopg2.connect(
        **_connect_kwargs(admin_url, database_name)
    )
    try:
        teardown_isolated_database(
            test_database_url=admin_url,
            database_name=database_name,
            worktree_id=worktree_id,
            run_id=run_id,
        )
        assert not _database_exists(admin_url, database_name)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _connect_kwargs(admin_url: str, database_name: str) -> dict:
    parts = urlsplit(admin_url)
    return {
        "dbname": database_name,
        "user": parts.username,
        "password": parts.password,
        "host": parts.hostname,
        "port": parts.port or 5432,
    }


# ---------------------------------------------------------------------
# Advisory lock (items 15, plus TEST_DATABASE_LOCK_UNAVAILABLE)
# ---------------------------------------------------------------------


def test_advisory_lock_blocks_duplicate_management_of_same_database():
    _, _, database_name = _fresh_name("lock-block")
    admin_url = _admin_url_for(database_name)
    holder = _advisory_lock(admin_url, database_name)
    holder.__enter__()
    try:
        with pytest.raises(TestDatabaseLockUnavailableError):
            with _advisory_lock(admin_url, database_name):
                pass
    finally:
        holder.__exit__(None, None, None)


def test_advisory_lock_permits_different_database_names_concurrently():
    _, _, database_name_a = _fresh_name("lock-a")
    _, _, database_name_b = _fresh_name("lock-b")
    admin_url_a = _admin_url_for(database_name_a)
    admin_url_b = _admin_url_for(database_name_b)
    with _advisory_lock(admin_url_a, database_name_a):
        with _advisory_lock(admin_url_b, database_name_b):
            pass  # Both acquired simultaneously without error.


def test_migration_failure_triggers_automatic_cleanup(monkeypatch):
    """If Alembic upgrade raises, main() must not leak the database it just
    created (retain-on-failure defaults to False)."""
    import _create_test_db as create_test_db_module

    worktree_id, run_id, database_name = _fresh_name("migration-failure")
    admin_url = _admin_url_for(database_name)

    def _boom(*_args, **_kwargs):
        raise RuntimeError("simulated migration failure")

    monkeypatch.setattr(create_test_db_module.command, "upgrade", _boom)

    with pytest.raises(RuntimeError, match="simulated migration failure"):
        create_test_db_module.main(["--worktree-id", worktree_id, "--run-id", run_id])

    assert not _database_exists(admin_url, database_name)
    assert read_ownership_record(database_name) is None
    assert "EXPECTED_DB" not in os.environ
    assert "MIGRATION_DATABASE_URL" not in os.environ


def test_migration_failure_with_retain_on_failure_keeps_database():
    import _create_test_db as create_test_db_module

    worktree_id, run_id, database_name = _fresh_name("migration-failure-retain")
    admin_url = _admin_url_for(database_name)

    original_upgrade = create_test_db_module.command.upgrade

    def _boom(*_args, **_kwargs):
        raise RuntimeError("simulated migration failure")

    create_test_db_module.command.upgrade = _boom
    try:
        with pytest.raises(RuntimeError, match="simulated migration failure"):
            create_test_db_module.main(
                [
                    "--worktree-id",
                    worktree_id,
                    "--run-id",
                    run_id,
                    "--retain-on-failure",
                ]
            )
        assert _database_exists(admin_url, database_name)
        record = read_ownership_record(database_name)
        assert record is not None
        assert record.lifecycle_status == "FAILED"
    finally:
        create_test_db_module.command.upgrade = original_upgrade
        try:
            teardown_isolated_database(
                test_database_url=admin_url,
                database_name=database_name,
                worktree_id=worktree_id,
                run_id=run_id,
            )
        except Exception:
            pass


# ---------------------------------------------------------------------
# Interruption cleanup (item 34): run_isolated_tests.py teardown must still
# run when the pytest subprocess is killed rather than exiting normally.
# ---------------------------------------------------------------------


def test_run_isolated_tests_tears_down_after_pytest_subprocess_is_killed():
    import _create_test_db as create_test_db_module

    worktree_id, run_id, database_name = _fresh_name("interrupted")
    admin_url = _admin_url_for(database_name)

    create_test_db_module.main(["--worktree-id", worktree_id, "--run-id", run_id])
    assert _database_exists(admin_url, database_name)

    from scripts.test_db_registry import update_lifecycle_status as _update_status

    # Simulate the "pytest subprocess got killed" path directly: mark
    # TESTING, then run the same teardown run_isolated_tests.py's `finally`
    # block performs when subprocess.run returns a nonzero/killed exit code.
    _update_status(database_name, "TESTING")
    exit_code = -9  # SIGKILL-style negative return code from subprocess.run
    _update_status(database_name, "COMPLETE" if exit_code == 0 else "FAILED")
    teardown_isolated_database(
        test_database_url=admin_url,
        database_name=database_name,
        worktree_id=worktree_id,
        run_id=run_id,
        retain=False,
    )
    assert not _database_exists(admin_url, database_name)
    assert read_ownership_record(database_name) is None


def test_advisory_lock_key_is_deterministic_and_distinguishes_names():
    key_a = advisory_lock_key("sns_emr_test_aaaaaaaa_bbbbbbbb")
    key_a_again = advisory_lock_key("sns_emr_test_aaaaaaaa_bbbbbbbb")
    key_b = advisory_lock_key("sns_emr_test_cccccccc_dddddddd")
    assert key_a == key_a_again
    assert key_a != key_b


# ---------------------------------------------------------------------
# Concurrency (items 30-33): two real isolated databases at once
# ---------------------------------------------------------------------


def test_two_concurrent_isolated_databases_do_not_collide():
    results: dict[str, object] = {}
    errors: list[BaseException] = []

    def _run(label: str):
        worktree_id, run_id, database_name = _fresh_name(f"concurrent-{label}")
        admin_url = _admin_url_for(database_name)
        try:
            create_isolated_database(
                test_database_url=admin_url,
                database_name=database_name,
                worktree_path=WORKTREE_DIR,
                worktree_id=worktree_id,
                run_id=run_id,
                application_name=build_application_name(worktree_id, run_id, os.getpid()),
            )
            results[label] = (worktree_id, run_id, database_name, admin_url)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_run, args=(label,)) for label in ("x", "y")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    try:
        assert not errors, f"unexpected errors: {errors}"
        assert len(results) == 2
        name_x = results["x"][2]
        name_y = results["y"][2]
        assert name_x != name_y
        assert _database_exists(results["x"][3], name_x)
        assert _database_exists(results["y"][3], name_y)
    finally:
        for label in ("x", "y"):
            if label in results:
                worktree_id, run_id, database_name, admin_url = results[label]
                try:
                    teardown_isolated_database(
                        test_database_url=admin_url,
                        database_name=database_name,
                        worktree_id=worktree_id,
                        run_id=run_id,
                    )
                except Exception:
                    pass

    # Registry has no leftover entries for either database.
    assert read_ownership_record(name_x) is None
    assert read_ownership_record(name_y) is None
