"""Ownership manifest for isolated test databases.

Each isolated `sns_emr_test_<worktree_id>_<run_id>` database gets a small
JSON ownership record written beside the test runner (not inside the test
schema itself, so it survives even if the database is dropped/recreated).
A process may only drop or mutate the lifecycle of a database if its own
(worktree_id, run_id) matches the record -- this is what stops one session
from ever tearing down another session's database.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_REGISTRY_DIR = Path(__file__).resolve().parents[1] / ".test_db_registry"

LIFECYCLE_STATUSES = (
    "CREATING",
    "MIGRATING",
    "READY",
    "TESTING",
    "CLEANING",
    "COMPLETE",
    "FAILED",
)


class OwnershipError(RuntimeError):
    """Raised when a process attempts to mutate/drop a database it does not
    own, or when an ownership record is missing/corrupt when one is
    required."""


@dataclass
class OwnershipRecord:
    database_name: str
    worktree_path: str
    worktree_id: str
    run_id: str
    process_id: int
    application_name: str
    created_at: str
    creating_user: str
    repository_commit: str
    branch_name: str
    lifecycle_status: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def _registry_path(database_name: str) -> Path:
    return _REGISTRY_DIR / f"{database_name}.json"


def _git(args: list[str], cwd: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, check=False,
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def write_ownership_record(
    *,
    database_name: str,
    worktree_path: str,
    worktree_id: str,
    run_id: str,
    application_name: str,
    lifecycle_status: str,
) -> OwnershipRecord:
    if lifecycle_status not in LIFECYCLE_STATUSES:
        raise ValueError(f"Invalid lifecycle_status: {lifecycle_status!r}")
    _REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    record = OwnershipRecord(
        database_name=database_name,
        worktree_path=worktree_path,
        worktree_id=worktree_id,
        run_id=run_id,
        process_id=os.getpid(),
        application_name=application_name,
        created_at=datetime.now(timezone.utc).isoformat(),
        creating_user=os.getenv("USERNAME") or os.getenv("USER") or "unknown",
        repository_commit=_git(["rev-parse", "HEAD"], cwd=worktree_path),
        branch_name=_git(["branch", "--show-current"], cwd=worktree_path),
        lifecycle_status=lifecycle_status,
    )
    _registry_path(database_name).write_text(record.to_json(), encoding="utf-8")
    return record


def update_lifecycle_status(database_name: str, lifecycle_status: str) -> None:
    if lifecycle_status not in LIFECYCLE_STATUSES:
        raise ValueError(f"Invalid lifecycle_status: {lifecycle_status!r}")
    record = read_ownership_record(database_name)
    if record is None:
        raise OwnershipError(
            f"No ownership record for {database_name!r}; cannot update status."
        )
    record.lifecycle_status = lifecycle_status
    _registry_path(database_name).write_text(record.to_json(), encoding="utf-8")


def read_ownership_record(database_name: str) -> Optional[OwnershipRecord]:
    path = _registry_path(database_name)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return OwnershipRecord(**data)


def verify_ownership(database_name: str, worktree_id: str, run_id: str) -> None:
    """Raise OwnershipError unless the caller's (worktree_id, run_id) matches
    the recorded owner of `database_name`. A missing record is NOT
    automatically treated as "unowned/safe" -- callers that need to create a
    brand-new database should write the record themselves before calling
    this, rather than relying on absence-of-record as permission."""
    record = read_ownership_record(database_name)
    if record is None:
        raise OwnershipError(
            f"No ownership record found for {database_name!r}. Refusing to "
            "drop/mutate a database with no verifiable owner."
        )
    if record.worktree_id != worktree_id or record.run_id != run_id:
        raise OwnershipError(
            f"Ownership mismatch for {database_name!r}: owned by "
            f"worktree_id={record.worktree_id!r} run_id={record.run_id!r}, "
            f"but caller is worktree_id={worktree_id!r} run_id={run_id!r}. "
            "Refusing to drop/mutate another session's test database."
        )


def remove_ownership_record(database_name: str) -> None:
    path = _registry_path(database_name)
    if path.exists():
        path.unlink()
