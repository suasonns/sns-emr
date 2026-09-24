# PHASE 1 FAILURE ROOT CAUSE ANALYSIS

**Scope:** `backend/tests/test_treatment_identity_migration.py`
**Trigger:** Post-commit scoped validation on `review/staff-management-rbac-auditlogs` (commit `3364a13`)
**Status:** Investigation complete. One defect fixed and re-validated. One failure confirmed pre-existing and out of Phase 1 scope.

---

## FAILURE 1

### 1. Exact test name
`test_migration_downgrade_and_reupgrade_leave_current_equal_to_head`

### 2. Exact assertion failure
```
AssertionError: assert {'um2d1c2c3o5u9'} == {'um2a1c2c3o5u6'}
```

### 3. Full stack trace (as originally observed)
```
    def test_migration_downgrade_and_reupgrade_leave_current_equal_to_head():
        ...
        command.downgrade(cfg, "-1")
        command.upgrade(cfg, "head")
        script = ScriptDirectory.from_config(cfg)
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current = set(context.get_current_heads())
        heads = set(script.get_heads())
>       assert current == heads == {HEAD_REVISION}
E       AssertionError: assert {'um2d1c2c3o5u9'} == {'um2a1c2c3o5u6'}
tests/test_treatment_identity_migration.py:156: AssertionError
```

### 4. Failing file
`backend/tests/test_treatment_identity_migration.py`

### 5. Failing line
Line 156 (assertion); root cause at line 15 (constant declaration).

### 6. Root cause
The recovery branch's edit to this test file changed the module constant:
```
- HEAD_REVISION = "d9e8f7a6b5c4"
+ HEAD_REVISION = "um2a1c2c3o5u6"
```
`um2a1c2c3o5u6` is only the **2nd of 5 new migrations** added in this changeset
(`um2s1a2f3f4b5 → um2a1c2c3o5u6 → um2b1c2c3o5u7 → um2c1c2c3o5u8 → um2d1c2c3o5u9`),
not the true chain head. The true head, confirmed via `ScriptDirectory.get_heads()`
and via `alembic current` after a full migration run, is `um2d1c2c3o5u9`. The
constant was set to the wrong revision id when the migrations were written/recovered.

### 7. Reproduces on `main`? 
**NO.** `main` does not contain any of the 5 new Phase 1 migrations, so this
exact failure mode (a stale intermediate revision id) cannot occur there — the
pre-recovery constant (`d9e8f7a6b5c4`) is a different (also unrelated) value.

### 8. Reproduces on `review/staff-management-rbac-auditlogs`? 
**YES** — prior to fix (commit `09a870a`). **NO** — after fix (amended into `3364a13`).

### 9. Classification
**PHASE-1 INTRODUCED.**

### 10. Evidence supporting classification
- `git diff b552fcb HEAD -- backend/tests/test_treatment_identity_migration.py` showed the *only* change to this file was the one-line `HEAD_REVISION` constant.
- The value it was changed to (`um2a1c2c3o5u6`) only exists because Phase 1 added new migrations; it is not a `main`-origin value.
- Confirmed defect is isolated to this one line, fully attributable to the Phase 1 migration set.

### Fix applied
| | |
|---|---|
| File | `backend/tests/test_treatment_identity_migration.py` |
| Line | 15 |
| Original value | `HEAD_REVISION = "um2a1c2c3o5u6"` |
| Corrected value | `HEAD_REVISION = "um2d1c2c3o5u9"` |
| Why it became stale | Set to an intermediate migration in the 5-migration chain instead of the final one when the recovery migrations were authored. |
| Test proving the repair | `test_migration_downgrade_and_reupgrade_leave_current_equal_to_head` — re-run individually and as part of the full scoped suite: **PASSED** after the fix. |
| Commit | Amended into `3364a13` (still 38 files, +7501/-488 — no scope change; recovery branch and excluded files untouched). |

---

## FAILURE 2

### 1. Exact test name
`test_migration_remaps_treatment_references_and_preserves_survivor_metadata`

### 2. Exact assertion failure
No assertion is reached; the test errors out during setup (`command.downgrade`).
```
NotImplementedError: Forward-only migration
```

### 3. Full stack trace
```
    def test_migration_remaps_treatment_references_and_preserves_survivor_metadata():
        engine = create_engine(TEST_DATABASE_URL, future=True)
        cfg = _alembic_cfg()
        with scoped_env_vars(...):
>           command.downgrade(cfg, PRE_MIGRATION_REVISION)
tests/test_treatment_identity_migration.py:29: in test_migration_remaps_treatment_references_and_preserves_survivor_metadata
    command.downgrade(cfg, PRE_MIGRATION_REVISION)
... (alembic command/script/runtime frames) ...
>       raise NotImplementedError("Forward-only migration")
E       NotImplementedError: Forward-only migration
alembic/versions/p9r8q7s6t5u4_add_billing_scope_permission_levels.py:37: NotImplementedError
```
Pytest run output: `1 failed, 1 passed` for this file (post-fix state).

### 4. Failing file
Raised from `backend/alembic/versions/p9r8q7s6t5u4_add_billing_scope_permission_levels.py:37`
(triggered by the `downgrade()` call at `backend/tests/test_treatment_identity_migration.py:29`).

### 5. Failing line
`alembic/versions/p9r8q7s6t5u4_add_billing_scope_permission_levels.py:37`

### 6. Root cause
`PRE_MIGRATION_REVISION = "c3f7a1e9b0d2"` (line 14) sits earlier in the migration
chain than `p9r8q7s6t5u4_add_billing_scope_permission_levels.py`. Alembic's
`downgrade(cfg, PRE_MIGRATION_REVISION)` must therefore execute the `downgrade()`
of every migration between the current head and that target — including
`p9r8q7s6t5u4`, whose `downgrade()` unconditionally raises
`NotImplementedError("Forward-only migration")` by design (it is an intentionally
irreversible, forward-only migration, unrelated to Owner Platform / Staff
Management / RBAC). This migration and its forward-only design predate the
recovery branch's fork point and exist unmodified on `main`.

### 7. Reproduces on `main`? 
**YES.** Ran the identical test file against an unmodified `main` checkout
(commit `b552fcb`, current head `pay3v4e5r6i7f`, no Phase 1 migrations present)
using the same isolated test runner. Result: **identical failure**, same
`NotImplementedError: Forward-only migration` raised from the same file/line.
Confirmed by direct test execution, not inference.

### 8. Reproduces on `review/staff-management-rbac-auditlogs`? 
**YES** (both before and after the `HEAD_REVISION` fix — that fix does not
affect this test's execution path).

### 9. Classification
**PRE-EXISTING.** Outside Phase 1 scope.

### 10. Evidence supporting classification
- Direct reproduction on unmodified `main` (not just static analysis): the failure is byte-for-byte identical (same exception type, same message, same raising file/line).
- `git show b552fcb:backend/alembic/versions/p9r8q7s6t5u4_add_billing_scope_permission_levels.py` confirms this migration and its forward-only `downgrade()` already exist on `main`, authored for a Billing feature, unrelated to Owner Platform/RBAC/Staff Management/Password Setup/Audit Logs.
- No Phase 1 file touches `p9r8q7s6t5u4_add_billing_scope_permission_levels.py`, `PRE_MIGRATION_REVISION`, or the test's downgrade-target logic.
- Per the "do not fix unrelated pre-existing issues" rule, this failure is documented here as **KNOWN PRE-EXISTING FAILURE — OUTSIDE PHASE 1** and is not a Phase 1 merge blocker.

---

## RE-VALIDATION RESULTS (post-fix, full scoped suite)

Command:
```
python scripts\run_isolated_tests.py -- tests/test_owner_platform_rbac_matrix.py tests/test_owner_platform_staff_delegation.py tests/test_owner_platform_staff_lifecycle.py tests/test_owner_platform_staff_profile.py tests/test_owner_audit_logs.py tests/test_password_setup_flow.py tests/test_treatment_identity_migration.py -q
```

| Test file | Result |
|---|---|
| `test_owner_platform_rbac_matrix.py` | PASSED |
| `test_owner_platform_staff_delegation.py` | PASSED |
| `test_owner_platform_staff_lifecycle.py` | PASSED |
| `test_owner_platform_staff_profile.py` | PASSED |
| `test_owner_audit_logs.py` | PASSED |
| `test_password_setup_flow.py` | PASSED |
| `test_treatment_identity_migration.py` | 1 passed / **1 failed** (pre-existing, documented above) |

Alembic head after full upgrade: `['um2d1c2c3o5u9']` — correct, matches expected Phase 1 chain tail.

---

## UPDATED READINESS CLASSIFICATION

| Item | Status |
|---|---|
| Phase 1 introduced defect (`HEAD_REVISION`) | **FIXED, RE-VALIDATED, PASSING** |
| Pre-existing unrelated failure (`p9r8q7s6t5u4` forward-only downgrade) | **CONFIRMED PRE-EXISTING, OUTSIDE PHASE 1 SCOPE, NOT A BLOCKER** |
| Commit `3364a13` scope | Unchanged: 38 files, +7501/-488 |
| Recovery branch (`recovery/copilot-session-2026-09-14`) | Untouched, unmodified |
| Excluded files (9) | Untouched, unmodified |
| Frontend build/lint against amended commit | **NOT YET RE-RUN** — required before push/PR |

**Push / PR / Merge:** Still on hold pending explicit authorization, per current instructions.
