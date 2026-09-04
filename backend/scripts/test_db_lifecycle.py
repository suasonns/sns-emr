"""Lifecycle orchestration for isolated test databases: advisory-locked
create/migrate/teardown, connection cleanup, and safety guards.

This is the one place that actually issues CREATE DATABASE / DROP DATABASE /
terminate-backend statements. Every other script (`_create_test_db.py`,
`run_isolated_tests.py`) goes through here so the safety contract (name
validation, ownership, advisory lock, connection disposal) is enforced in
exactly one place.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator
from urllib.parse import urlsplit, urlunsplit

import psycopg2
from sqlalchemy import create_engine, text

from scripts.test_db_identity import advisory_lock_key, validate_database_name
from scripts.test_db_registry import (
    OwnershipError,
    remove_ownership_record,
    update_lifecycle_status,
    verify_ownership,
    write_ownership_record,
)


class TestDatabaseLockUnavailableError(RuntimeError):
    """Raised when the advisory lock for a test database name is already
    held by another process. Callers must not wait indefinitely -- this is
    raised immediately instead of blocking."""

    # Not a pytest test class despite the name -- silence the collection
    # warning triggered when this module is imported by a test file.
    __test__ = False


def _admin_url(any_db_url: str) -> str:
    """Build a URL pointing at the 'postgres' maintenance database on the
    same server, so CREATE/DROP DATABASE never runs from a connection bound
    to the database being created or dropped."""
    parts = urlsplit(any_db_url)
    return urlunsplit(parts._replace(path="/postgres"))


def _admin_connection(any_db_url: str):
    parts = urlsplit(_admin_url(any_db_url))
    return psycopg2.connect(
        dbname=parts.path.lstrip("/"),
        user=parts.username,
        password=parts.password,
        host=parts.hostname,
        port=parts.port or 5432,
    )


@contextmanager
def _advisory_lock(any_db_url: str, database_name: str) -> Iterator[None]:
    """Hold a session-scoped Postgres advisory lock keyed on `database_name`
    for the duration of the `with` block. Raises immediately (never blocks)
    if another process already holds it. The lock is scoped per-database-name
    -- different isolated databases can be created/dropped fully
    concurrently."""
    key = advisory_lock_key(database_name)
    conn = _admin_connection(any_db_url)
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute("SELECT pg_try_advisory_lock(%s)", (key,))
        (acquired,) = cur.fetchone()
        if not acquired:
            raise TestDatabaseLockUnavailableError(
                "TEST_DATABASE_LOCK_UNAVAILABLE: Another process owns this "
                f"test database lifecycle ({database_name!r})."
            )
        try:
            yield
        finally:
            cur.execute("SELECT pg_advisory_unlock(%s)", (key,))
    finally:
        conn.close()


def terminate_owned_connections(any_db_url: str, database_name: str) -> int:
    """Terminate only backend connections whose datname matches
    `database_name`. Does not touch any other database. Returns the number of
    connections terminated."""
    conn = _admin_connection(any_db_url)
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = %s AND pid <> pg_backend_pid()",
            (database_name,),
        )
        return len(cur.fetchall())
    finally:
        conn.close()


def _count_owned_connections(any_db_url: str, database_name: str) -> int:
    conn = _admin_connection(any_db_url)
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT count(*) FROM pg_stat_activity "
            "WHERE datname = %s AND pid <> pg_backend_pid()",
            (database_name,),
        )
        (n,) = cur.fetchone()
        return n
    finally:
        conn.close()


def _database_exists(any_db_url: str, database_name: str) -> bool:
    conn = _admin_connection(any_db_url)
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
        return cur.fetchone() is not None
    finally:
        conn.close()


def create_isolated_database(
    *,
    test_database_url: str,
    database_name: str,
    worktree_path: str,
    worktree_id: str,
    run_id: str,
    application_name: str,
) -> None:
    """Steps 1-11 of the required creation sequence: validate name, acquire
    the per-name advisory lock, terminate any stale owned connections, drop
    the database if it already exists (only ever a same-owner leftover, since
    the name is unique to this worktree+run), and create it fresh. Writes the
    CREATING ownership record before doing anything destructive."""
    validate_database_name(database_name)

    with _advisory_lock(test_database_url, database_name):
        write_ownership_record(
            database_name=database_name,
            worktree_path=worktree_path,
            worktree_id=worktree_id,
            run_id=run_id,
            application_name=application_name,
            lifecycle_status="CREATING",
        )
        if _database_exists(test_database_url, database_name):
            # Only reachable if a previous run with the same worktree+run_id
            # was interrupted before cleanup. Verify ownership before
            # touching it -- never drop a database this process didn't
            # create.
            verify_ownership(database_name, worktree_id, run_id)
            terminate_owned_connections(test_database_url, database_name)
            conn = _admin_connection(test_database_url)
            conn.autocommit = True
            try:
                cur = conn.cursor()
                cur.execute(f'DROP DATABASE IF EXISTS "{database_name}"')
            finally:
                conn.close()

        conn = _admin_connection(test_database_url)
        conn.autocommit = True
        try:
            cur = conn.cursor()
            cur.execute(f'CREATE DATABASE "{database_name}"')
        finally:
            conn.close()


def teardown_isolated_database(
    *,
    test_database_url: str,
    database_name: str,
    worktree_id: str,
    run_id: str,
    retain: bool = False,
) -> None:
    """Steps 19-20: dispose connections, verify ownership, drop the database
    unless retention was requested. Always releases the advisory lock (the
    `with` block's finally) even if a step raises."""
    if retain:
        update_lifecycle_status(database_name, "FAILED")
        return

    with _advisory_lock(test_database_url, database_name):
        verify_ownership(database_name, worktree_id, run_id)
        update_lifecycle_status(database_name, "CLEANING")
        terminate_owned_connections(test_database_url, database_name)
        remaining = _count_owned_connections(test_database_url, database_name)
        if remaining:
            raise OwnershipError(
                f"Refusing to drop {database_name!r}: {remaining} connection(s) "
                "still present after termination."
            )
        if _database_exists(test_database_url, database_name):
            conn = _admin_connection(test_database_url)
            conn.autocommit = True
            try:
                cur = conn.cursor()
                cur.execute(f'DROP DATABASE IF EXISTS "{database_name}"')
            finally:
                conn.close()
        remove_ownership_record(database_name)
