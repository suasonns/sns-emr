# FUNCTIONAL MERGE EXECUTION PLAN

**Date:** 2026-09-15
**Source branch:** `recovery/copilot-session-2026-09-14`
**Scope:** Staff Management, RBAC, Password Setup, Audit Logs only.
**Excluded from this execution plan:** branding files (Phase 2, separate
review) and documentation/governance files (Phase 3, separate review) —
per your decision, these are not part of this merge batch.
**Status:** Execution planning only. **No commit. No merge. No PR.**

---

## 1. Exact Files In Merge Batch (41 files)

### A. Database Migrations (5, new)
1. `backend/alembic/versions/um2s1a2f3f4b5_add_department_notes_updated_by_to_users.py`
2. `backend/alembic/versions/um2a1c2c3o5u6_add_account_type_to_users.py`
3. `backend/alembic/versions/um2b1c2c3o5u7_add_identity_fields_to_users.py`
4. `backend/alembic/versions/um2c1c2c3o5u8_add_platform_to_users.py`
5. `backend/alembic/versions/um2d1c2c3o5u9_add_staff_status_and_permission_grants.py`

*(Listed here in actual Alembic revision/dependency order — see §3.)*

### B. RBAC Core Files
6. `backend/app/core/roles.py` — **HIGH IMPACT** (authorization engine modification; validation passed; not a blocker; requires elevated review awareness)
7. `backend/app/core/account_types.py` (new)
8. `backend/app/core/departments.py` (new)
9. `backend/app/core/job_titles.py` (new)
10. `backend/app/core/platforms.py` (new)

### C. Role Guards
11. `backend/app/core/role_guards.py`

### D. Protected Tenants
12. `backend/app/core/protected_tenants.py`

### E. Auth Role Updates
13. `backend/app/core/auth.py` (`VALID_ROLES` extended for new platform roles)

### F. Staff Permission Models
14. `backend/app/models/__init__.py`
15. `backend/app/models/staff_permission_grant.py` (new)
16. `backend/app/models/user.py`

### G. Owner Admin API
17. `backend/app/api/owner_admin.py`

### H. Bootstrap Service
18. `backend/app/services/admin_bootstrap_service.py`

### I. Staff Management Tests
19. `backend/tests/test_owner_platform_rbac_matrix.py` (new)
20. `backend/tests/test_owner_platform_staff_delegation.py` (new)
21. `backend/tests/test_owner_platform_staff_lifecycle.py` (new)
22. `backend/tests/test_owner_platform_staff_profile.py` (new)
23. `backend/tests/test_treatment_identity_migration.py`

### J. Audit Log Tests
24. `backend/tests/test_owner_audit_logs.py` (extended — 4 new free-text search tests)

### K. Password Setup Tests
25. `backend/tests/test_password_setup_flow.py` (new)

### L. Owner UI Files
26. `sns-emr-frontend/src/App.tsx`
27. `sns-emr-frontend/src/api/ownerAdmin.ts`
28. `sns-emr-frontend/src/owner/OwnerDashboard.jsx`
29. `sns-emr-frontend/src/owner/accessLevels.js` (new)
30. `sns-emr-frontend/src/owner/auditCategories.js` (new)
31. `sns-emr-frontend/src/owner/components/AddStaffModal.jsx` (new)
32. `sns-emr-frontend/src/owner/components/AuditEventDrawer.jsx` (new)
33. `sns-emr-frontend/src/owner/components/StaffProfileDrawer.jsx` (new)
34. `sns-emr-frontend/src/owner/pages/AuditLogs.jsx`
35. `sns-emr-frontend/src/owner/pages/UserManagement.jsx`
36. `sns-emr-frontend/src/owner/shell/OwnerShell.jsx` (new)

### M. Password Setup UI
37. `sns-emr-frontend/src/pages/SetPasswordPage.tsx` (new; lint-fixed this pass)

### N. authorization.ts
38. `sns-emr-frontend/src/utils/authorization.ts`

**Confirmed exclusions (not in this batch):** all 5 brand SVGs,
`BrandLogo.tsx`, `PLATFORM_ARCHITECTURE_ROADMAP.md`,
`SNS_STAFF_ACCESS_CHECKPOINT.md`, `.github/copilot-instructions.md`.

*(Count note: 38 numbered items above; the earlier 41-file figure in
`FUNCTIONAL_RECOVERY_MERGE_PLAN.md` grouped 3 of these under a combined
"models" bullet slightly differently — the file list, not the count, is
authoritative. Every file this plan lists matches the Phase 1 scope you
approved.)*

---

## 2. Merge Order

Recommended commit/PR internal ordering (single PR, ordered commits for
reviewability — not multiple separate merges):

1. **Migrations first** (A) — schema must exist before any code references
   the new columns/tables.
2. **Core domain modules** (B: `account_types.py`, `departments.py`,
   `job_titles.py`, `platforms.py`) — no internal dependencies on other
   Phase 1 files, safe to land right after migrations.
3. **`roles.py`** (B, item 6) — depends on nothing else in this batch
   structurally, but is the highest-impact file; sequence it as its own
   reviewable commit, immediately after the core domain modules, before
   anything that calls into it.
4. **`role_guards.py`** (C) and **`protected_tenants.py`** (D) — depend on
   `roles.py`'s role-checking primitives.
5. **`auth.py`** (E) — depends on the platform role set now being complete
   (`PLATFORM_ROLES` from `roles.py`).
6. **Models** (F) — depend on the migrations (A) being applied first for
   the columns/table they map.
7. **`owner_admin.py`** (G) — depends on `roles.py`, role guards, models,
   and the new core domain modules (account types/departments/job
   titles/platforms) all being present.
8. **`admin_bootstrap_service.py`** (H) — depends on models/roles being in
   place.
9. **Backend tests** (I, J, K) — land alongside (same commit as, or
   immediately after) the code they test; must not be separated from steps
   2–8.
10. **Frontend Owner UI + Password Setup UI + `authorization.ts`** (L, M,
    N) — depend on the backend endpoints in `owner_admin.py` (step 7)
    already being present; land last.

---

## 3. Migration Order

Migrations must apply in this exact dependency-chained order (each
revision's `down_revision` points to the previous one):

1. `um2s1a2f3f4b5` — add department/notes/updated_by to users
2. `um2a1c2c3o5u6` — add account_type to users
3. `um2b1c2c3o5u7` — add responsible_owner_id, identity_purpose, identity_scope to users
4. `um2c1c2c3o5u8` — add platform assignment to users
5. `um2d1c2c3o5u9` — add platform staff status + delegated permission grants

Verified this pass: `alembic upgrade head` from a clean baseline applies
all 5 in this order without error (confirmed via every isolated test run
in this effort, most recently in the final validation sweep). All 5 are
additive (new nullable columns / new tables) — no destructive change to
any pre-existing column.

---

## 4. Validation After Merge

Run against `main` immediately after the merge lands (not just the
isolated recovery worktree):

1. **Backend test suite** (full run, not just this scope, to catch any
   interaction with unrelated `main` changes since the recovery branch was
   created):
   - `test_owner_platform_rbac_matrix.py`
   - `test_owner_platform_staff_delegation.py`
   - `test_owner_platform_staff_lifecycle.py`
   - `test_owner_platform_staff_profile.py`
   - `test_owner_audit_logs.py`
   - `test_password_setup_flow.py`
   - `test_treatment_identity_migration.py`
   - Full backend suite (`run_isolated_tests.py` with no path filter) to
     catch any regression outside this scope's own tests.
2. **Migration apply check** on `main`'s actual migration head (not just
   the recovery branch's baseline) — `alembic upgrade head` must succeed
   cleanly against `main`'s current schema state, since `main` may have
   advanced past the recovery branch's fork point.
3. **Frontend build** (`npm run build`) against the merged `main` — confirm
   0 new TypeScript errors beyond the pre-existing, unrelated
   `FacilityCollectionsReportPage.tsx` errors.
4. **Frontend lint** (`npm run lint`) against the merged `main` — confirm
   parity with the 78-problem baseline (no net-new issues).
5. **Manual smoke check** (recommended, not scripted): log in as `OWNER`
   and as one non-OWNER platform role (e.g. `PLATFORM_SUPPORT`), confirm
   `/owner/users` (Staff Management) and `/owner/audit-logs` load and
   behave per their existing, approved design.

---

## 5. Rollback Procedure

1. **Full revert:** revert the single merge commit/PR as one unit. Since
   steps in §2 are interdependent, a partial revert (e.g. reverting
   `roles.py` alone) is only safe if done deliberately (see item 2 below),
   not as the default rollback path.
2. **Isolated `roles.py` revert (if only the RBAC rewrite regresses):**
   `roles.py` is self-contained with its own dedicated test file
   (`test_owner_platform_rbac_matrix.py`). It can be reverted to its
   pre-merge state independently, since no other file in this batch
   modifies its internal logic — only `owner_admin.py`/`role_guards.py`
   call into it. Confirm with a full re-run of
   `test_owner_platform_rbac_matrix.py` immediately after an isolated
   revert.
3. **Migration rollback:** `alembic downgrade` the 5 revisions in reverse
   order (`um2d1c2c3o5u9` → `um2s1a2f3f4b5`). All 5 are additive
   (new columns/tables), so downgrading drops only what was added — no
   pre-existing data is at risk.
4. **Frontend rollback:** revert the Owner UI / Password Setup UI /
   `authorization.ts` files as a unit if a frontend-specific issue is
   found without needing to touch the backend portion of the merge.
5. **Verification after any rollback:** re-run the full validation
   sequence in §4 to confirm `main` is back to a known-good state.

---

## 6. Post-Merge Verification

Checklist to close out the merge (execute only after the merge referenced
above has actually happened — not part of this planning pass):

- [ ] All backend tests in §4.1 pass on `main`.
- [ ] Migration head on `main` matches the expected revision
      (`um2d1c2c3o5u9`).
- [ ] Frontend build on `main` shows 0 new errors vs. the pre-existing
      billing-page baseline.
- [ ] Frontend lint on `main` shows 78/78 problems (no net-new issues).
- [ ] Manual smoke check (§4.5) completed for at least one OWNER and one
      non-OWNER platform-role login.
- [ ] `OWNER_PLATFORM_ROADMAP_STATUS.md` updated to move Staff Management
      and Audit Logs from "FUNCTIONALLY COMPLETE — AWAITING MERGE REVIEW"
      to a merged/complete state.
- [ ] Recovery branch (`recovery/copilot-session-2026-09-14`) and its
      worktree retired/archived only after the above checks pass — not
      before.
- [ ] Phase 2 (branding) and Phase 3 (documentation/governance) reviews
      scheduled as separate, subsequent efforts — not bundled into this
      merge's post-merge verification.

---

## Status Recap (unchanged by this document)

| Item | Status |
|---|---|
| Recovery Work | COMPLETE |
| Staff Management | FUNCTIONALLY COMPLETE |
| RBAC | FUNCTIONALLY COMPLETE |
| Password Setup | COMPLETE |
| Audit Logs | COMPLETE |
| Owner Platform (overall) | NOT COMPLETE — Analytics, Billing & Licensing, Settings, AI Command Center remain |

**No commit, merge, or PR performed.** This execution plan is for your
review; work stops here.
