# Isolated test databases

Every backend test run — local, inside a Copilot session/worktree, or in CI —
must use its **own** uniquely-named PostgreSQL database. Do not run `pytest`
directly against a fixed `sns_emr_test` database name.

## Why

On 2026-09-03, multiple concurrent Copilot sessions (each its own git
worktree) all defaulted to the same shared `sns_emr_test` database. One
session's schema rebuild (`DROP SCHEMA public CASCADE` + re-migrate) raced
against another session's running `pytest` process. Tables vanished
mid-test-run, migrations deadlocked, and identical test commands produced
different pass/fail counts on every run — none of it caused by the code
under test. See `scripts/test_db_identity.py` for the full naming contract
this infrastructure enforces to make that impossible.

## How to run tests

```powershell
# From backend/, run any subset of pytest args after `--`:
python scripts\run_isolated_tests.py -- tests/test_foo.py -v
python scripts\run_isolated_tests.py -- -q --tb=short
python scripts\run_isolated_tests.py --retain-on-failure -- tests/test_foo.py
```

This:

1. Derives a `worktree_id` (hash of this checkout's absolute path) and a
   fresh random `run_id`.
2. Creates and migrates an isolated `sns_emr_test_<worktree_id>_<run_id>`
   database (own copy of the full schema, from Alembic — never a hand-shaped
   database).
3. Exports `TEST_DATABASE_URL` / `SNS_TEST_WORKTREE_ID` / `SNS_TEST_RUN_ID` /
   `PYTHONHASHSEED=0` to a `pytest` subprocess.
4. Runs pytest, preserving its exit code.
5. Always tears the database down afterwards (drop + release the advisory
   lock + remove the ownership registry entry) — unless `--retain-on-failure`
   was passed and the run failed, in which case the database is kept for
   inspection and marked `FAILED` in the registry.

Two sessions (or two terminal windows) running this at the same time get two
completely independent databases and cannot interfere with each other.

## What NOT to do

- Do not invoke `python _create_test_db.py` followed by a separate `pytest`
  invocation in a way that reuses a fixed database name across runs/sessions.
- Do not set `TEST_DATABASE_URL` to the same value as `DATABASE_URL` — the
  `conftest.py` guard (`TEST_DATABASE_ISOLATION_VIOLATION`) will refuse to
  start.
- Do not invent your own test database name — always go through
  `scripts/test_db_identity.build_database_name` (directly or via
  `run_isolated_tests.py` / `_create_test_db.py`), which enforces the
  `sns_emr_test_` prefix, character set, and PostgreSQL identifier length
  limit (`UNSAFE_TEST_DATABASE_NAME` otherwise).

## CI

`.github/workflows/ci.yml`'s backend job runs tests the same way, deriving
`TEST_RUN_ID` from `github.run_id`/`github.run_attempt` so re-runs of the
same job never collide, and uploads `junit-results.xml` as a build artifact
regardless of pass/fail.

## Permanent tests

See `backend/tests/test_test_database_isolation.py` for the committed
regression suite covering name collision safety, environment-variable
leak prevention, ownership/ownership-mismatch enforcement, advisory-lock
behavior, and real concurrent-database proof.
