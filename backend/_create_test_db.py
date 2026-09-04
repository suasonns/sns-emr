"""Build/rebuild an ISOLATED, per-worktree/per-run Postgres test database from
the current Alembic migrations (the true source of truth for production
schema).

Incident 2026-09-03: multiple concurrent Copilot sessions/worktrees all
defaulted to the same shared `sns_emr_test` database. One session's
`DROP SCHEMA public CASCADE` (to rebuild the schema) raced against another
session's running pytest process, causing tables to vanish mid-test-run,
migration deadlocks, and non-deterministic pass/fail/error counts that had
nothing to do with the code under test. See
`backend/scripts/test_db_identity.py` / `test_db_registry.py` /
`test_db_lifecycle.py` for the isolation contract this script now enforces:
every independently-running session gets its OWN uniquely-named database
(`sns_emr_test_<worktree_id>_<run_id>`), protected by a per-database-name
Postgres advisory lock and an ownership manifest so no session can ever
touch another session's database.

Usage:

    python backend/_create_test_db.py
        Derives worktree_id from this checkout's path and a fresh random
        run_id, builds an isolated TEST_DATABASE_URL, creates/migrates it,
        and prints the resulting TEST_DATABASE_URL for the caller to export.

    python backend/_create_test_db.py --database-name sns_emr_test_ab12cd34_ef56
        Rebuilds a *specific* previously-created isolated database (must
        already have an ownership record from this same worktree+run, or
        pass matching --worktree-id/--run-id explicitly).

Prefer `backend/scripts/run_isolated_tests.py` for actually running pytest --
it derives the identity, creates the database, exports TEST_DATABASE_URL to
the pytest subprocess, and tears the database down afterwards. This script is
the lower-level "just build me a schema" primitive it (and CI) builds on.
"""

from __future__ import annotations

import argparse
import os
import sys
from urllib.parse import urlsplit, urlunsplit

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.database import DATABASE_URL
from scripts.test_db_identity import (
    build_application_name,
    build_database_name,
    compute_run_id,
    compute_worktree_id,
    redact_database_url,
    scoped_env_vars,
    validate_database_name,
    worktree_root_from_module,
)
from scripts.test_db_lifecycle import create_isolated_database
from scripts.test_db_registry import update_lifecycle_status


def _backend_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _worktree_root() -> str:
    # backend/_create_test_db.py -> 1 level below the worktree root.
    return worktree_root_from_module(__file__, levels_below_root=1)


def _build_url_for_database(any_db_url: str, database_name: str) -> str:
    parts = urlsplit(any_db_url)
    return urlunsplit(parts._replace(path=f"/{database_name}"))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-name", default=None)
    parser.add_argument("--worktree-id", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--worker-id", default=None)
    parser.add_argument("--retain-on-failure", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> str:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    worktree_path = _worktree_root()
    worktree_id = args.worktree_id or compute_worktree_id(worktree_path)
    run_id = args.run_id or compute_run_id()
    database_name = args.database_name or build_database_name(
        worktree_id, run_id, args.worker_id
    )
    validate_database_name(database_name)

    application_name = build_application_name(worktree_id, run_id, os.getpid())

    # Admin operations (CREATE/DROP DATABASE, advisory lock, connection
    # termination) always go through a connection to the 'postgres'
    # maintenance database on the SAME server as DATABASE_URL -- never
    # through a connection bound to the database being created/dropped.
    admin_reference_url = _build_url_for_database(DATABASE_URL, database_name)

    print(
        f"[isolate] worktree_id={worktree_id} run_id={run_id} "
        f"database={database_name} application_name={application_name}"
    )

    try:
        create_isolated_database(
            test_database_url=admin_reference_url,
            database_name=database_name,
            worktree_path=worktree_path,
            worktree_id=worktree_id,
            run_id=run_id,
            application_name=application_name,
        )
        update_lifecycle_status(database_name, "MIGRATING")

        test_url = _build_url_for_database(DATABASE_URL, database_name)

        print(f"[rebuild] Running Alembic migrations against '{database_name}'...")
        backend_dir = _backend_dir()
        alembic_cfg = Config(os.path.join(backend_dir, "alembic.ini"))
        alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
        # scoped_env_vars guarantees MIGRATION_DATABASE_URL/EXPECTED_DB are
        # restored to their exact prior value (present or absent) on exit --
        # including on exception/interruption -- so neither can ever leak
        # into a pytest subprocess launched later in this same process.
        with scoped_env_vars(
            MIGRATION_DATABASE_URL=test_url, EXPECTED_DB=database_name
        ):
            command.upgrade(alembic_cfg, "head")

            from alembic.script import ScriptDirectory

            script_dir = ScriptDirectory.from_config(alembic_cfg)
            heads = set(script_dir.get_heads())

            engine = create_engine(test_url, future=True)
            try:
                with engine.connect() as conn:
                    current = {
                        row[0]
                        for row in conn.execute(
                            text("SELECT version_num FROM alembic_version")
                        )
                    }
            finally:
                engine.dispose()

            if current != heads:
                raise RuntimeError(
                    "DATABASE SCHEMA DRIFT DETECTED after upgrade: "
                    f"current={sorted(current)} heads={sorted(heads)}"
                )
            print(f"[rebuild] Alembic current == heads ({sorted(heads)}).")

        update_lifecycle_status(database_name, "READY")
        print(f"[rebuild] Done. '{database_name}' is READY.")
        print(f"TEST_DATABASE_URL={redact_database_url(test_url)}")
        return test_url
    except Exception:
        try:
            update_lifecycle_status(database_name, "FAILED")
        except Exception:
            pass
        if not args.retain_on_failure:
            # Best-effort cleanup so a failed rebuild doesn't leak a database
            # forever; ownership is verified inside teardown.
            from scripts.test_db_lifecycle import teardown_isolated_database

            try:
                teardown_isolated_database(
                    test_database_url=admin_reference_url,
                    database_name=database_name,
                    worktree_id=worktree_id,
                    run_id=run_id,
                    retain=False,
                )
            except Exception:
                pass
        raise


if __name__ == "__main__":
    main()
