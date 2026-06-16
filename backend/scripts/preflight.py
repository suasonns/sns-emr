#!/usr/bin/env python
"""SNS EMR Backend Preflight (Schema Drift Blocker)

Purpose (LOCKED stability posture):
- Fail fast if Alembic is not in sync (current != heads).
- Optionally run `alembic upgrade head` before checking.
- Optionally run pytest.

This script is designed to be run from CI or locally.
Place in: backend/scripts/preflight.py

Non-negotiables:
- Forward-only migrations (never rewrite history).
- No silent drift.

Usage examples:
  python backend/scripts/preflight.py --upgrade
  python backend/scripts/preflight.py --upgrade --pytest
  python backend/scripts/preflight.py --pytest

Environment:
  DATABASE_URL  (optional; used by alembic and tests)
  SKIP_PYTEST=1 (optional; skips pytest even if --pytest)

Exit codes:
  0 = success
  2 = alembic command failure
  3 = drift detected (current != heads)
  4 = pytest failed
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def _rev_ids(output: str) -> set[str]:
    return set(re.findall(r"\b[0-9a-f]{7,40}\b", output.lower()))


def _run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _backend_root() -> Path:
    # backend/scripts/preflight.py -> backend/
    return Path(__file__).resolve().parents[1]


def alembic_upgrade_head(cwd: Path) -> None:
    rc, out, err = _run(["alembic", "upgrade", "head"], cwd)
    if rc != 0:
        print(out)
        print(err, file=sys.stderr)
        raise SystemExit(2)


def alembic_check_in_sync(cwd: Path) -> None:
    rc1, out1, err1 = _run(["alembic", "current"], cwd)
    if rc1 != 0:
        print(out1)
        print(err1, file=sys.stderr)
        raise SystemExit(2)

    rc2, out2, err2 = _run(["alembic", "heads"], cwd)
    if rc2 != 0:
        print(out2)
        print(err2, file=sys.stderr)
        raise SystemExit(2)

    cur = _rev_ids(out1 + "\n" + err1)
    heads = _rev_ids(out2 + "\n" + err2)

    if not cur or not heads:
        print("Could not parse alembic revisions.")
        print("alembic current output:\n", out1, err1)
        print("alembic heads output:\n", out2, err2)
        raise SystemExit(2)

    if cur != heads:
        print("❌ DATABASE SCHEMA DRIFT DETECTED — alembic current != heads")
        print("current:", sorted(cur))
        print("heads:  ", sorted(heads))
        raise SystemExit(3)

    # success
    print("✅ Alembic current == heads")
    print("current:", sorted(cur))


def run_pytest(cwd: Path) -> None:
    if os.getenv("SKIP_PYTEST", "").strip().lower() in {"1", "true", "yes"}:
        print("⚠️ SKIP_PYTEST enabled — skipping pytest")
        return

    rc, out, err = _run(["pytest", "-q"], cwd)
    print(out)
    if rc != 0:
        print(err, file=sys.stderr)
        raise SystemExit(4)

    print("✅ Pytest passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upgrade", action="store_true", help="Run alembic upgrade head before checks")
    parser.add_argument("--pytest", action="store_true", help="Run pytest -q after alembic checks")
    args = parser.parse_args()

    cwd = _backend_root()

    # Optional: echo DATABASE_URL presence (do not print secrets)
    if os.getenv("DATABASE_URL"):
        print("✅ DATABASE_URL is set")
    else:
        print("ℹ️ DATABASE_URL not set (alembic/test config must provide DB connection)")

    if args.upgrade:
        print("▶ Running: alembic upgrade head")
        alembic_upgrade_head(cwd)

    print("▶ Running: alembic current")
    print("▶ Running: alembic heads")
    alembic_check_in_sync(cwd)

    if args.pytest:
        print("▶ Running: pytest -q")
        run_pytest(cwd)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
