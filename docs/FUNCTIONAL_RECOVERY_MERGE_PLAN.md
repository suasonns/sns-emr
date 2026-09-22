# FUNCTIONAL RECOVERY MERGE PLAN

**Date:** 2026-09-15
**Source branch:** `recovery/copilot-session-2026-09-14`
**Status:** Planning document only. **No merge. No commit. No PR.**

Scope control (per your directive): the first functional recovery merge
covers **Staff Management, RBAC, Password Setup, and Audit Logs only**.
Brand assets and documentation are deliberately deferred to later phases
and must not be included in Phase 1.

---

## Phase 1 — Functional Merge Files Only

**Goal:** Merge Staff Management (incl. RBAC, Password Setup) and Audit
Logs — the only sections classified merge-candidate-ready.

### Files included (41)

**Database migrations (5, new):**
- `backend/alembic/versions/um2a1c2c3o5u6_add_account_type_to_users.py`
- `backend/alembic/versions/um2b1c2c3o5u7_add_identity_fields_to_users.py`
- `backend/alembic/versions/um2c1c2c3o5u8_add_platform_to_users.py`
- `backend/alembic/versions/um2d1c2c3o5u9_add_staff_status_and_permission_grants.py`
- `backend/alembic/versions/um2s1a2f3f4b5_add_department_notes_updated_by_to_users.py`

**Backend — core RBAC / domain (7):**
- `backend/app/core/roles.py` **— HIGH IMPACT (authorization engine modification); see Risk note below**
- `backend/app/core/account_types.py` (new)
- `backend/app/core/departments.py` (new)
- `backend/app/core/job_titles.py` (new)
- `backend/app/core/platforms.py` (new)
- `backend/app/core/protected_tenants.py`
- `backend/app/core/role_guards.py`
- `backend/app/core/auth.py`

**Backend — models (3):**
- `backend/app/models/__init__.py`
- `backend/app/models/staff_permission_grant.py` (new)
- `backend/app/models/user.py`

**Backend — API (1):**
- `backend/app/api/owner_admin.py`

**Backend — services (1):**
- `backend/app/services/admin_bootstrap_service.py`

**Backend — tests (7):**
- `backend/tests/test_owner_platform_rbac_matrix.py` (new)
- `backend/tests/test_owner_platform_staff_delegation.py` (new)
- `backend/tests/test_owner_platform_staff_lifecycle.py` (new)
- `backend/tests/test_owner_platform_staff_profile.py` (new)
- `backend/tests/test_owner_audit_logs.py` (extended — 4 new search tests)
- `backend/tests/test_treatment_identity_migration.py`
- `backend/tests/test_password_setup_flow.py` (new)

**Frontend — Owner Platform UI (11):**
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

**Frontend — Password Setup / Auth (2):**
- `sns-emr-frontend/src/pages/SetPasswordPage.tsx` (new; lint-fixed)
- `sns-emr-frontend/src/utils/authorization.ts`

**Explicitly excluded from Phase 1** (deferred to Phase 2/3 per scope control):
- All brand assets (5 SVGs)
- `sns-emr-frontend/src/components/BrandLogo.tsx`
- `docs/PLATFORM_ARCHITECTURE_ROADMAP.md`
- `docs/SNS_STAFF_ACCESS_CHECKPOINT.md`
- `.github/copilot-instructions.md`

### Dependencies
- The 5 migrations must apply in their existing revision order (each
  `down_revision` chains to the prior one) before any backend code that
  reads the new columns/tables (`staff_permission_grant.py`,
  `owner_admin.py`, `roles.py`'s capability model) can function correctly.
- `roles.py` is depended on by `owner_admin.py`, `role_guards.py`, and
  every backend test in this phase — it must land in the same commit/PR
  as the rest of Phase 1, not split further.
- Frontend `OwnerDashboard.jsx` / `OwnerShell.jsx` depend on the backend
  `available_roles`, `access_levels_by_role`, and audit-log endpoints in
  `owner_admin.py` already being present — frontend and backend files in
  this phase must merge together, not staged separately.
- No dependency on Phase 2 (branding) or Phase 3 (docs) — Phase 1 is
  fully self-contained and can merge independently of them.

### Validation Required
- Full backend suite for this scope (already run, 0 failures):
  `test_owner_platform_rbac_matrix.py`,
  `test_owner_platform_staff_delegation.py`,
  `test_owner_platform_staff_lifecycle.py`,
  `test_owner_platform_staff_profile.py`,
  `test_owner_audit_logs.py`, `test_password_setup_flow.py`.
- Alembic migration apply/rollback check (`alembic upgrade head` /
  `alembic downgrade -5`) — upgrade already verified in every test run
  this pass; explicit downgrade check recommended once more immediately
  before merge as a final gate.
- Frontend build (`npm run build`) and lint (`npm run lint`) — already
  run, 0 new errors/issues vs. `main` baseline; re-run once more
  immediately before merge to catch any drift from concurrent `main`
  changes.
- Recommended: a second human reviewer specifically for `roles.py` given
  its HIGH IMPACT classification, even though automated validation passed.

### Rollback Strategy
- Revert the Phase 1 merge commit as a single unit if any issue surfaces
  post-merge — all Phase 1 files are interdependent (see Dependencies) and
  should be reverted together, not piecemeal.
- Migrations are additive only (new columns/tables); `alembic downgrade`
  for the 5 new revisions (in reverse order) cleanly removes the schema
  changes with no destructive impact on pre-existing data.
- If only `roles.py`'s authorization logic needs isolated rollback without
  reverting the rest of Phase 1, it can be reverted independently — it is
  self-contained and has its own dedicated test file
  (`test_owner_platform_rbac_matrix.py`) that will immediately surface any
  regression from a partial revert.

---

## Phase 2 — Branding Files

**Goal:** Merge the incidental brand-asset updates bundled in the original
recovered session, as a separate, lower-risk follow-up.

### Files included (6)
- `sns-emr-frontend/public/brand/sns-logo-dark.svg`
- `sns-emr-frontend/public/brand/sns-logo-icon-dark-tile.svg` (new)
- `sns-emr-frontend/public/brand/sns-logo-icon-dark.svg` (new)
- `sns-emr-frontend/public/brand/sns-logo-icon.svg`
- `sns-emr-frontend/public/brand/sns-logo-light.svg`
- `sns-emr-frontend/src/components/BrandLogo.tsx`

### Dependencies
- None on Phase 1 or Phase 3 — purely static asset + presentational
  component changes, no coupling to RBAC/Staff Management/Audit Logs logic.
- `BrandLogo.tsx` references the SVG asset paths above; these 6 files must
  merge together as one unit (component + assets it renders), not split
  further within this phase.

### Validation Required
- Visual verification that `BrandLogo.tsx` renders correctly with the new/
  updated SVGs across the variants it exposes (light/dark, icon vs. full
  logo) — no automated test coverage exists for this today, so this is a
  manual/visual check.
- Frontend build/lint re-run (low risk of introducing new errors, but
  cheap to confirm given Phase 1's build is already clean).

### Rollback Strategy
- Revert the Phase 2 commit independently of Phase 1 — no shared files,
  no shared logic. Reverting brand assets has zero effect on Staff
  Management/RBAC/Audit Logs functionality.

---

## Phase 3 — Documentation Files

**Goal:** Merge the recovered documentation and repo-config files as a
final, lowest-risk follow-up.

### Files included (3)
- `docs/PLATFORM_ARCHITECTURE_ROADMAP.md` (new)
- `docs/SNS_STAFF_ACCESS_CHECKPOINT.md` (new)
- `.github/copilot-instructions.md` (new)

### Dependencies
- None on Phase 1 or Phase 2 — documentation-only, no executable code.
- Recommended (not required): merge Phase 3 last, after Phase 1 has landed,
  so `SNS_STAFF_ACCESS_CHECKPOINT.md` and
  `PLATFORM_ARCHITECTURE_ROADMAP.md` can be reviewed/updated for accuracy
  against whatever actually merged in Phase 1, rather than merging stale
  documentation ahead of the functional change it describes.

### Validation Required
- Documentation review only — confirm the content still accurately
  reflects the merged state of Staff Management/RBAC/Audit Logs after
  Phase 1, and that `.github/copilot-instructions.md` doesn't conflict
  with any repo-config changes made independently on `main` since the
  recovered session.
- No automated tests apply to this phase.

### Rollback Strategy
- Revert the Phase 3 commit independently — documentation-only, zero
  runtime impact, trivial to revert or amend at any time.

---

## Summary

| Phase | Files | Risk | Depends on |
|---|---|---|---|
| 1 — Functional (Staff Mgmt, RBAC, Password Setup, Audit Logs) | 41 | HIGH IMPACT (`roles.py`) overall LOW-to-MODERATE elsewhere, fully validated | None |
| 2 — Branding | 6 | Low (presentational only) | None (independent of Phase 1) |
| 3 — Documentation | 3 | Minimal (docs only) | Recommended after Phase 1 for accuracy, not a hard dependency |

**No merge, commit, or PR performed.** This plan is for your review and
sequencing decision only.
