"""Per-worktree / per-run test-database identity derivation and validation.

This module is the single source of truth for how an isolated Postgres test
database's name is computed and validated. It exists so that no two
concurrently-running Copilot sessions/worktrees (or CI jobs) can ever resolve
to the same physical `sns_emr_test*` database -- see the 2026-09-03 incident
where two sessions racing against a single shared `sns_emr_test` database
produced non-deterministic pytest results (tables vanishing mid-run, deadlocks
on schema rebuild, idle-in-transaction connections left behind).

Naming contract (do not weaken):

    sns_emr_test_<worktree_id>_<run_id>

- worktree_id: first 8 hex chars of SHA-256(normalized absolute worktree path)
- run_id: explicit TEST_RUN_ID env var if provided, otherwise a securely
  generated short hex identifier (not a timestamp -- two runs started in the
  same clock tick must never collide)

Allowed characters in the full database name: lowercase a-z, digits 0-9,
underscore. Anything else is rejected outright rather than silently sanitized,
so a caller notices a real problem instead of getting a silently-mangled name.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets

REQUIRED_PREFIX = "sns_emr_test_"

# Postgres identifier length limit (NAMEDATALEN - 1).
_POSTGRES_IDENTIFIER_LIMIT = 63

_ALLOWED_NAME_CHARS = re.compile(r"^[a-z0-9_]+$")


class UnsafeTestDatabaseNameError(RuntimeError):
    """Raised when a database name does not satisfy the disposable-test-db
    naming contract. The caller must never create, drop, or mutate a database
    whose name fails this check."""


def compute_worktree_id(worktree_path: str) -> str:
    """First 8 hex characters of SHA-256 of the normalized absolute worktree
    path. Deterministic for a given worktree, distinct across worktrees."""
    normalized = os.path.normcase(os.path.normpath(os.path.abspath(worktree_path)))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest[:8]


def worktree_root_from_module(module_file: str, *, levels_below_root: int) -> str:
    """Single canonical way to discover the repository/worktree root given
    `__file__` of a script living at a known depth beneath it.

    Regression guard (2026-09-03): `run_isolated_tests.py` originally
    hand-rolled its own `dirname(dirname(...))` chain and miscounted how many
    directories separate it from the repository root, silently treating the
    `backend/` directory itself as the worktree root and generating a bogus
    nested `.../backend/backend` path when re-deriving `backend_dir`. Every
    caller must go through this one function instead of repeating the
    `os.path.dirname` chain locally.

    `levels_below_root` is the number of directories between `module_file`'s
    parent directory and the worktree root, e.g. for
    `backend/scripts/run_isolated_tests.py` that's 2
    (`scripts/` -> `backend/` -> root), and for `backend/_create_test_db.py`
    that's 1 (`backend/` -> root).
    """
    path = os.path.dirname(os.path.abspath(module_file))
    for _ in range(levels_below_root):
        path = os.path.dirname(path)
    return path


def compute_run_id() -> str:
    """Explicit TEST_RUN_ID if provided; otherwise a securely generated short
    identifier. Never derived from the current timestamp alone."""
    override = os.getenv("TEST_RUN_ID")
    if override:
        return _sanitize_component(override, field_name="TEST_RUN_ID")
    return secrets.token_hex(4)


def _sanitize_component(value: str, *, field_name: str) -> str:
    lowered = value.strip().lower()
    if not lowered:
        raise UnsafeTestDatabaseNameError(f"{field_name} must not be empty.")
    if not _ALLOWED_NAME_CHARS.match(lowered):
        raise UnsafeTestDatabaseNameError(
            f"{field_name}={value!r} contains characters outside [a-z0-9_]. "
            "Refusing to build a database name from it."
        )
    return lowered


def build_database_name(
    worktree_id: str, run_id: str, worker_id: str | None = None
) -> str:
    """Build `sns_emr_test_<worktree_id>_<run_id>` (or
    `sns_emr_test_<worktree_id>_<run_id>_<worker_id>` for a pytest-xdist
    worker), validating character set and the Postgres identifier length
    limit."""
    worktree_id = _sanitize_component(worktree_id, field_name="worktree_id")
    run_id = _sanitize_component(run_id, field_name="run_id")
    name = f"{REQUIRED_PREFIX}{worktree_id}_{run_id}"
    if worker_id:
        worker_id = _sanitize_component(worker_id, field_name="worker_id")
        name = f"{name}_{worker_id}"
    if len(name) > _POSTGRES_IDENTIFIER_LIMIT:
        raise UnsafeTestDatabaseNameError(
            f"Generated database name {name!r} ({len(name)} chars) exceeds "
            f"the PostgreSQL identifier limit of {_POSTGRES_IDENTIFIER_LIMIT}."
        )
    validate_database_name(name)
    return name


def validate_database_name(name: str) -> None:
    """Raise UnsafeTestDatabaseNameError unless `name` is a safe, disposable
    test-database name. This is the gate every create/drop/mutate operation
    must pass through first."""
    if not name.startswith(REQUIRED_PREFIX):
        raise UnsafeTestDatabaseNameError(
            f"UNSAFE_TEST_DATABASE_NAME: Refusing to create, drop, or mutate "
            f"a non-test database ({name!r} does not start with "
            f"{REQUIRED_PREFIX!r})."
        )
    if not _ALLOWED_NAME_CHARS.match(name):
        raise UnsafeTestDatabaseNameError(
            f"UNSAFE_TEST_DATABASE_NAME: {name!r} contains characters outside "
            "[a-z0-9_]."
        )
    if len(name) > _POSTGRES_IDENTIFIER_LIMIT:
        raise UnsafeTestDatabaseNameError(
            f"UNSAFE_TEST_DATABASE_NAME: {name!r} ({len(name)} chars) exceeds "
            f"the PostgreSQL identifier limit of {_POSTGRES_IDENTIFIER_LIMIT}."
        )


def build_application_name(worktree_id: str, run_id: str, pid: int) -> str:
    """`sns-emr-test:<worktree_id>:<run_id>:<pid>` -- lets pg_stat_activity
    unambiguously identify which session/run owns a given connection."""
    return f"sns-emr-test:{worktree_id}:{run_id}:{pid}"


def redact_database_url(url: str) -> str:
    """Render a database URL with the password hidden. Every place this
    module (or its callers) prints/logs a database URL must go through this
    -- never print a raw TEST_DATABASE_URL/DATABASE_URL string."""
    try:
        from sqlalchemy.engine import make_url

        return make_url(url).render_as_string(hide_password=True)
    except Exception:
        return "<unparseable-database-url>"


def advisory_lock_key(database_name: str) -> int:
    """Deterministic 64-bit signed integer lock key derived from the database
    name, for use with pg_try_advisory_lock(key). Two different database
    names must (for all practical purposes) never collide."""
    digest = hashlib.sha256(database_name.encode("utf-8")).digest()
    # Interpret the first 8 bytes as a signed 64-bit integer -- Postgres
    # advisory lock keys are bigint (signed 64-bit).
    value = int.from_bytes(digest[:8], byteorder="big", signed=False)
    signed_range = 1 << 63
    return value - (1 << 64) if value >= signed_range else value


class scoped_env_vars:
    """Context manager that sets one or more environment variables and
    guarantees their PRIOR value (present or absent) is restored on exit --
    success, exception, or KeyboardInterrupt/interruption all run the same
    __exit__ path. Used so setup-only variables (e.g. EXPECTED_DB during an
    Alembic migration) can never leak into a pytest subprocess launched
    later in the same process's environment.

    Usage:
        with scoped_env_vars(EXPECTED_DB="some_db"):
            ...  # os.environ["EXPECTED_DB"] == "some_db" here
        # os.environ["EXPECTED_DB"] is back to whatever it was before (or
        # absent if it was absent before), even if the block raised.
    """

    _SENTINEL = object()

    def __init__(self, **values: str) -> None:
        self._values = values
        self._prior: dict[str, object] = {}

    def __enter__(self) -> "scoped_env_vars":
        for key, value in self._values.items():
            self._prior[key] = os.environ.get(key, self._SENTINEL)
            os.environ[key] = value
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        for key, prior in self._prior.items():
            if prior is self._SENTINEL:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prior  # type: ignore[assignment]
        return None
