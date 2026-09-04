#!/usr/bin/env python
"""Wrapper that gives every pytest invocation its own isolated Postgres test
database, so no two concurrently-running Copilot sessions/worktrees (or CI
jobs) can ever collide on a shared `sns_emr_test` database again.

This is now the REQUIRED way to run backend tests locally -- do not invoke
`_create_test_db.py` and `pytest` separately against a fixed `sns_emr_test`
name; that reintroduces the exact cross-session collision this wrapper
exists to prevent.

Usage:

    python backend/scripts/run_isolated_tests.py -- tests/test_foo.py -v
    python backend/scripts/run_isolated_tests.py --retain-on-failure -- tests/

Everything after `--` is passed straight through to `pytest`.

What it does:
  1. Derives worktree_id (from this checkout's path) and a fresh run_id.
  2. Creates + migrates an isolated database via `_create_test_db.py`'s logic.
  3. Exports TEST_DATABASE_URL / SNS_TEST_WORKTREE_ID / SNS_TEST_RUN_ID /
     PYTHONHASHSEED=0 to a pytest subprocess.
  4. Runs pytest with the given arguments, capturing its exit code.
  5. Marks the database COMPLETE or FAILED in the ownership manifest.
  6. Tears the database down (drops it) unless --retain-on-failure was
     given and the run failed.
  7. Always releases the advisory lock and disposes connections, even if
     pytest crashes or is interrupted (KeyboardInterrupt is caught and still
     runs teardown before re-raising).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from _create_test_db import main as create_and_migrate  # noqa: E402
from scripts.test_db_identity import (  # noqa: E402
    compute_run_id,
    compute_worktree_id,
    worktree_root_from_module,
)
from scripts.test_db_registry import update_lifecycle_status  # noqa: E402
from scripts.test_db_lifecycle import teardown_isolated_database  # noqa: E402
from app.core.database import DATABASE_URL  # noqa: E402
from urllib.parse import urlsplit, urlunsplit  # noqa: E402


def _parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retain-on-failure", action="store_true")
    parser.add_argument("--worktree-id", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--worker-id", default=None)
    if "--" in argv:
        split = argv.index("--")
        own_args, pytest_args = argv[:split], argv[split + 1 :]
    else:
        own_args, pytest_args = argv, []
    return parser.parse_args(own_args), pytest_args


def _admin_url_for(database_name: str) -> str:
    parts = urlsplit(DATABASE_URL)
    return urlunsplit(parts._replace(path=f"/{database_name}"))


def main(argv: list[str] | None = None) -> int:
    args, pytest_args = _parse_args(argv if argv is not None else sys.argv[1:])

    # backend/scripts/run_isolated_tests.py -> 2 levels below the worktree
    # root (scripts/ -> backend/ -> root). See worktree_root_from_module's
    # docstring for why this must not be a locally hand-rolled dirname chain.
    worktree_path = worktree_root_from_module(__file__, levels_below_root=2)
    worktree_id = args.worktree_id or compute_worktree_id(worktree_path)
    run_id = args.run_id or compute_run_id()

    create_args = ["--worktree-id", worktree_id, "--run-id", run_id]
    if args.worker_id:
        create_args += ["--worker-id", args.worker_id]
    test_url = create_and_migrate(create_args)
    database_name = urlsplit(test_url).path.lstrip("/")

    env = dict(os.environ)
    env["TEST_DATABASE_URL"] = test_url
    env["SNS_TEST_WORKTREE_ID"] = worktree_id
    env["SNS_TEST_RUN_ID"] = run_id
    env["PYTHONHASHSEED"] = "0"

    update_lifecycle_status(database_name, "TESTING")

    exit_code = 1
    try:
        backend_dir = os.path.join(worktree_path, "backend")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", *pytest_args],
            cwd=backend_dir,
            env=env,
        )
        exit_code = result.returncode
    except KeyboardInterrupt:
        exit_code = 130
        raise
    finally:
        update_lifecycle_status(database_name, "COMPLETE" if exit_code == 0 else "FAILED")
        retain = args.retain_on_failure and exit_code != 0
        teardown_isolated_database(
            test_database_url=_admin_url_for(database_name),
            database_name=database_name,
            worktree_id=worktree_id,
            run_id=run_id,
            retain=retain,
        )
        if retain:
            print(f"[run_isolated_tests] Retained failed database '{database_name}' for inspection.")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
