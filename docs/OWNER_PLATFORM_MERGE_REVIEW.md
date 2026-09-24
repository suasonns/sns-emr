# OWNER PLATFORM MERGE REVIEW

**Date:** 2026-09-15
**Scope:** Staff Management (incl. RBAC, Password Setup) and Audit Logs
only.
**Source branch:** `recovery/copilot-session-2026-09-14`
(worktree: `C:\Users\rdsua\Desktop\copilot-recovery-2026-09-15\recovery-worktree`)
**Action taken:** Documentation only. No commit. No merge. No PR.

---

## 1. Files To Merge

### Database Migrations (5, new)
- `backend/alembic/versions/um2a1c2c3o5u6_add_account_type_to_users.py`
- `backend/alembic/versions/um2b1c2c3o5u7_add_identity_fields_to_users.py`
- `backend/alembic/versions/um2c1c2c3o5u8_add_platform_to_users.py`
- `backend/alembic/versions/um2d1c2c3o5u9_add_staff_status_and_permission_grants.py`
- `backend/alembic/versions/um2s1a2f3f4b5_add_department_notes_updated_by_to_users.py`

### Backend — Core RBAC / Domain (7)
- `backend/app/core/roles.py` *(rewritten this pass: RBAC hierarchy conversion, hardcoded OWNER bypass removed)*
- `backend/app/core/account_types.py` (new)
- `backend/app/core/departments.py` (new)
- `backend/app/core/job_titles.py` (new)
- `backend/app/core/platforms.py` (new)
- `backend/app/core/protected_tenants.py` (modified)
- `backend/app/core/role_guards.py` (modified) — `require_owner()` untouched/verified distinct from the removed bypass
- `backend/app/core/auth.py` (modified — `VALID_ROLES` extended for the new platform roles)

### Backend — Models (3)
- `backend/app/models/__init__.py`
- `backend/app/models/staff_permission_grant.py` (new)
- `backend/app/models/user.py`

### Backend — API (1)
- `backend/app/api/owner_admin.py`

### Backend — Services (1)
- `backend/app/services/admin_bootstrap_service.py`

### Backend — Tests (7)
- `backend/tests/test_owner_platform_rbac_matrix.py` (new)
- `backend/tests/test_owner_platform_staff_delegation.py` (new)
- `backend/tests/test_owner_platform_staff_lifecycle.py` (new)
- `backend/tests/test_owner_platform_staff_profile.py` (new)
- `backend/tests/test_owner_audit_logs.py` (extended this pass — 4 new free-text search tests)
- `backend/tests/test_treatment_identity_migration.py` (modified)
- `backend/tests/test_password_setup_flow.py` (new this pass — closes the password-setup test-coverage gap)

### Frontend — Owner Platform UI (11)
- `sns-emr-frontend/src/App.tsx`
- `sns-emr-frontend/src/api/ownerAdmin.ts`
- `sns-emr-frontend/src/owner/OwnerDashboard.jsx`
- `sns-emr-frontend/src/owner/accessLevels.js` (new)
- `sns-emr-frontend/src/owner/auditCategories.js` (new)
- `sns-emr-frontend/src/owner/components/AddStaffModal.jsx` (new)
- `sns-emr-frontend/src/owner/components/AuditEventDrawer.jsx` (new)
- `sns-emr-frontend/src/owner/components/StaffProfileDrawer.jsx` (new)
- `sns-emr-frontend/src/owner/pages/AuditLogs.jsx`
- `sns-emr-frontend/src/owner/pages/UserManagement.jsx`
- `sns-emr-frontend/src/owner/shell/OwnerShell.jsx` (new)

### Frontend — Password Setup / Auth (2)
- `sns-emr-frontend/src/pages/SetPasswordPage.tsx` (new; lint-fixed this pass — synchronous `setState`-in-`useEffect` converted to derived state)
- `sns-emr-frontend/src/utils/authorization.ts` (route-scope broadening, approved as-is)

### Frontend — Branding (6, incidental to the recovered session; not functionally part of Staff Management/Audit Logs but bundled in the same recovered commit)
- `sns-emr-frontend/public/brand/sns-logo-dark.svg`
- `sns-emr-frontend/public/brand/sns-logo-icon-dark-tile.svg` (new)
- `sns-emr-frontend/public/brand/sns-logo-icon-dark.svg` (new)
- `sns-emr-frontend/public/brand/sns-logo-icon.svg`
- `sns-emr-frontend/public/brand/sns-logo-light.svg`
- `sns-emr-frontend/src/components/BrandLogo.tsx`

### Documentation (2, new)
- `docs/PLATFORM_ARCHITECTURE_ROADMAP.md`
- `docs/SNS_STAFF_ACCESS_CHECKPOINT.md`

### Repo config (1, new)
- `.github/copilot-instructions.md`

**Total: 47 files** (46 originally recovered + 1 new test file added this pass: `test_password_setup_flow.py`).

---

## 2. Merge Risks

| Risk | File(s) | Assessment |
|---|---|---|
| **HIGH IMPACT — authorization engine modification** | `backend/app/core/roles.py` | Removed the hardcoded `OWNER` bypass and the `!= "OWNER"` delegation exception; replaced with rank-based, data-driven logic. Validation passed with 0 regressions across the full RBAC/delegation/lifecycle test suite — **not a blocker** — but this is the platform's authorization engine, so it requires elevated merge awareness (second reviewer, careful post-merge monitoring) regardless of passing tests. |
| **Assignment-ceiling scope error (found & fixed during this effort)** | `backend/app/core/roles.py` | First draft applied the rank ceiling to every role pair, which over-restricted previously-unrestricted pairs (e.g. Support-on-Customer-Service) and broke 2 existing tests. Corrected by scoping the ceiling to only OWNER/PLATFORM_ADMIN-tier targets, matching original behavior exactly. Verified via full regression run — 0 failures remain. |
| **Frontend route-gate broadening** | `sns-emr-frontend/src/utils/authorization.ts` | Broadens `/owner` route entry from `role === "OWNER"` to any platform-scoped role. Not a permission bypass — backend `role_can()`/`require_platform_permission()` remain authoritative. Explicitly approved by you ("Option A"). Low risk. |
| **Lint regression (found & fixed)** | `sns-emr-frontend/src/pages/SetPasswordPage.tsx` | Recovered file originally called `setState` synchronously inside a `useEffect` (missing-token case). Fixed by converting to derived state; lint now at exact parity with `main` (78/78 problems, no new issues). |
| **Reserved-but-unratified roles** | `backend/app/core/roles.py` (`ROLE_AUTHORITY_RANK`) | `PLATFORM_AI_MANAGEMENT` / `PLATFORM_OPERATIONS` are placed at an interim rank (tier 7). Per your ROLE DECISION, they are retained, not renamed, not folded into Staff Management — this is not a merge blocker, but the tier placement is explicitly interim pending your final ratification. |
| **Migration ordering** | 5 new Alembic migrations | All 5 apply cleanly in the isolated test runner (`alembic upgrade head` succeeds, verified during every test run this pass). No manual intervention required. |
| **Branding/documentation files bundled in the same recovered changeset** | SVGs, `BrandLogo.tsx`, 2 docs, `.github/copilot-instructions.md` | Incidental to the recovered session, not functionally coupled to Staff Management/Audit Logs. Low risk (no logic), but flagged as scope creep if a strict "Staff Management + Audit Logs only" merge is required — see recommendation in §5. |

**No file in this changeset is classified HIGH RISK or BLOCKED.**

---

## 3. Validation Evidence

All validation performed against `recovery/copilot-session-2026-09-14` in
its isolated worktree, using the project's isolated Postgres test runner
(`backend/scripts/run_isolated_tests.py`), which mirrors the CI database
setup.

**Backend — all passing, 0 failures:**
- `test_owner_platform_rbac_matrix.py`
- `test_owner_platform_staff_delegation.py`
- `test_owner_platform_staff_lifecycle.py`
- `test_owner_platform_staff_profile.py`
- `test_owner_audit_logs.py` (38 tests total, incl. 4 new free-text search tests)
- `test_password_setup_flow.py` (9 tests, new — token generation, validate: fresh/unknown/expired, set-password: success/reuse-prevented/expired/unknown, audit log entry)

**Frontend build** (`npm run build` = `tsc -b && vite build`, the exact
command CI/DigitalOcean run):
- Zero errors in any Staff Management / RBAC / Audit Log / Password Setup file.
- 12 pre-existing TypeScript errors remain, all confined to
  `sns-emr-frontend/src/pages/billing/FacilityCollectionsReportPage.tsx`
  (unmodified, untouched by recovery) — confirmed byte-identical to `main`
  and reproducing the same 12 errors on a `main`-based baseline build.
  Unrelated to this merge scope.

**Frontend lint** (`npm run lint`):
- `main` baseline: 78 problems (71 errors, 7 warnings).
- Recovery branch, after the `SetPasswordPage.tsx` fix: **78 problems (71
  errors, 7 warnings) — exact parity.** Zero net-new lint issues.

**Password setup validation:** completed (token issuance, expiry, reuse
prevention, invalid-token handling, audit logging all covered by new
tests).

**Audit log validation:** completed (existing filter/date/category/entity
coverage plus newly-added free-text search coverage).

**Recovery validation:** completed (all 46 recovered files inventoried,
diffed against `main`, and exercised via the test suite above).

---

## 4. Rollback Strategy

- The recovery branch (`recovery/copilot-session-2026-09-14`) is fully
  isolated in its own worktree; `main` has not been touched at any point in
  this effort.
- On merge, standard rollback applies: revert the merge commit if a
  post-merge issue is found. No production deployment has occurred as part
  of this work.
- Because the migrations are additive (new columns/tables, no destructive
  changes to existing columns), a rollback does not require a compensating
  data migration beyond the standard `alembic downgrade` for the 5 new
  revisions, in reverse order.
- If only the RBAC rewrite in `roles.py` needs to be reverted post-merge
  (and not the rest of Staff Management/Audit Logs), it can be reverted
  independently since it is a single, self-contained file with its own
  test suite (`test_owner_platform_rbac_matrix.py`) that would immediately
  reveal any behavioral regression from a partial revert.

---

## 5. Final Merge Recommendation

**Staff Management (incl. RBAC, Password Setup) and Audit Logs: READY FOR
MERGE REVIEW.**

- All functional completion criteria met (per `OWNER_PLATFORM_FINAL_READINESS.md`).
- All identified security findings resolved (hardcoded OWNER bypass and
  delegation exception removed, replaced with data-driven rank logic; no
  new bypasses introduced).
- Full backend test suite for this scope: 0 failures.
- Frontend build/lint: 0 new issues vs. `main` baseline.
- No file classified HIGH RISK or BLOCKED.

**One scope note for your decision, not a blocker:** the branding assets,
`.github/copilot-instructions.md`, and the 2 documentation files
(`PLATFORM_ARCHITECTURE_ROADMAP.md`, `SNS_STAFF_ACCESS_CHECKPOINT.md`) are
bundled in the same recovered changeset but are not functionally part of
Staff Management or Audit Logs. If you want a strictly scoped merge, these
6 files could be split into a separate, lower-risk follow-up commit rather
than merged in the same batch — flagging this for your call, not making
the split unilaterally.

**Per your explicit instruction: no commit, no merge, no PR has been made.**
This document is the stopping point for this pass, awaiting your review.
