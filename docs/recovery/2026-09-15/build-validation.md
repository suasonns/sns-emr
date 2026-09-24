# Build / Test Validation Report — Recovery Branch

Branch under test: `recovery/copilot-session-2026-09-14`
Location: `C:\Users\rdsua\Desktop\copilot-recovery-2026-09-15\recovery-worktree`
Base: `main` @ `b552fcb0e90d8eca25beacb55c5b35d3d575d1ee`

## Backend — Python syntax validation

`python -m py_compile` on all 23 recovered/modified backend `.py` files: **PASS (exit 0)**, no
syntax errors.

## Backend — Migration validation

Ran the project's isolated per-worktree test-DB workflow
(`backend/scripts/run_isolated_tests.py`, which creates a throwaway
`sns_emr_test_<worktree>_<run>` database via `_create_test_db.py`, migrates it, runs pytest, then
tears it down — never touches the real `sns_emr_dev_clean` database). Postgres admin connection
used: `postgresql://sns:sns@127.0.0.1:5432/postgres` (used only to CREATE/DROP the isolated test
database).

- **Migration chain applied cleanly from empty DB to `head` (`um2d1c2c3o5u9`)**, including all 5
  recovered migrations:
  - `um2s1a2f3f4b5` — add department/notes/updated_by to users
  - `um2a1c2c3o5u6` — add account_type to users
  - `um2b1c2c3o5u7` — add responsible_owner_id, identity_purpose, identity_scope to users
  - `um2c1c2c3o5u8` — add platform assignment to users
  - `um2d1c2c3o5u9` — add platform staff status + delegated permission grants
- **Route registration / permission / auth validation**: exercised indirectly by the pytest suite
  below (owner API routes, RBAC matrix, staff delegation, permission grants all instantiate the
  FastAPI app and hit real endpoints through `TestClient`).

## Backend — Test suite results

Command: `python scripts/run_isolated_tests.py -- tests/test_owner_audit_logs.py
tests/test_owner_platform_rbac_matrix.py tests/test_owner_platform_staff_delegation.py
tests/test_owner_platform_staff_lifecycle.py tests/test_owner_platform_staff_profile.py
tests/test_treatment_identity_migration.py -v`

**Result: 122 passed, 2 failed** (124 collected).

| Test file | Result |
|---|---|
| test_owner_audit_logs.py | 34/34 passed |
| test_owner_platform_rbac_matrix.py | 20/20 passed |
| test_owner_platform_staff_delegation.py | 17/17 passed |
| test_owner_platform_staff_lifecycle.py | 39/39 passed |
| test_owner_platform_staff_profile.py | 12/12 passed |
| test_treatment_identity_migration.py | 0/2 passed (2 failed) — see below |

### The 2 failures are pre-existing/orthogonal, not caused by the recovered RBAC work

Both failures are in `test_treatment_identity_migration.py`, an unrelated ontology-migration test
that was only trivially touched by the recovered session (diffstat shows a 2-line change to this
file). Both failures are the same root cause:

```
NotImplementedError: Forward-only migration
  File "alembic/versions/p9r8q7s6t5u4_add_billing_scope_permission_levels.py", line 37, in downgrade
```

The test attempts `alembic downgrade` past a migration that was deliberately made forward-only
(`downgrade()` raises `NotImplementedError` by design). This is a **known, already-diagnosed issue**
— the live `main`/checkpoint history for this repo contains a later commit explicitly about this:
`test(migrations): stop crossing forward-only migrations in downgrade replay; document immutability
decision` (visible in this session's own checkpoint branch history). In other words: the recovered
session's snapshot of this test predates that already-applied fix on the baseline; it is not a
regression introduced by the recovered RBAC/staff-access feature itself.

**All 122 tests specific to the recovered feature (owner audit logs, platform RBAC matrix, staff
delegation, staff lifecycle, staff profile) pass with zero failures.**

## Frontend validation — NOT run

`sns-emr-frontend/node_modules` is not installed in the recovery worktree. Installing dependencies
was treated as out of scope for a forensic recovery pass (also avoids the "do not update
dependencies" guidance, since a fresh `npm install` could pull newer transitive versions than what
the original session validated against). Per the recovered session's own final `events.jsonl`
message, the *original* session reported: "backend tests (34 new cases + 6-file regression, exit
0), frontend build (vite bundle clean, unrelated pre-existing tsc error only), and lint (0 issues
on changed files) all pass" — but that is a self-report from before recovery, not independently
re-verified here.

**Action required before merge**: run `npm install && npx tsc --noEmit && npm run lint && npm run
build` inside `sns-emr-frontend` in the recovery worktree (or copy the 27 changed/new frontend
files into your normal dev checkout) to independently confirm the frontend still builds cleanly.

## Route / permission / auth validation

Covered by the passing test suites above — `test_owner_platform_rbac_matrix.py` and
`test_owner_platform_staff_delegation.py` specifically exercise route-level permission gating and
delegated-grant authorization paths, and all pass.

## Summary

| Check | Result |
|---|---|
| Backend Python syntax | ✅ PASS |
| Migration chain (upgrade to head) | ✅ PASS |
| Owner/RBAC/staff backend tests | ✅ PASS (122/122) |
| Unrelated migration-downgrade tests | ⚠️ 2 pre-existing failures (not caused by recovered work) |
| Frontend build/lint/typecheck | ⏳ NOT RUN (needs `npm install`; do before merge) |
