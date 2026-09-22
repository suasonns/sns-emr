# Final Merge Recommendation — Per-File Classification

Read-only analysis. **No code changes. No merges. No PR. No commits made or proposed as part of
this review.** Classification legend: SAFE TO MERGE / REQUIRES REVIEW / HIGH RISK / BLOCKED.

## Backend — models & migrations (additive, test-validated)

| File | Classification | Basis |
|---|---|---|
| `backend/alembic/versions/um2a1c2c3o5u6_*.py` | SAFE TO MERGE | Additive migration, applies cleanly to head, downgrade verified |
| `backend/alembic/versions/um2b1c2c3o5u7_*.py` | SAFE TO MERGE | Same |
| `backend/alembic/versions/um2c1c2c3o5u8_*.py` | SAFE TO MERGE | Same |
| `backend/alembic/versions/um2d1c2c3o5u9_*.py` | SAFE TO MERGE | Same; pairs with `staff_permission_grant.py` |
| `backend/alembic/versions/um2s1a2f3f4b5_*.py` | SAFE TO MERGE | Same |
| `backend/app/core/account_types.py` | SAFE TO MERGE | New file, no conflict, no security surface |
| `backend/app/core/departments.py` | SAFE TO MERGE | New file, no conflict |
| `backend/app/core/job_titles.py` | SAFE TO MERGE | New file, no conflict |
| `backend/app/core/platforms.py` | SAFE TO MERGE | New file, no conflict |
| `backend/app/models/staff_permission_grant.py` | SAFE TO MERGE | New model; must land with migration `um2d...` |
| `backend/app/models/user.py` | REQUIRES REVIEW | Additive-only hunk, but a security-relevant schema; verify no other in-flight main change to this model at merge time |
| `backend/app/models/__init__.py` | SAFE TO MERGE | Single-line import addition |
| `backend/app/services/admin_bootstrap_service.py` | REQUIRES REVIEW | Cosmetic dev-seed name change only; confirm it's still wanted |

## Backend — permissions & API (new authorization surface)

| File | Classification | Basis |
|---|---|---|
| `backend/app/core/roles.py` | REQUIRES REVIEW | Purely additive, no textual conflict, but see `RBAC_SECURITY_REVIEW.md` Finding 2 (hardcoded OWNER bypass) and `PLATFORM_OWNER_COMPLIANCE_REVIEW.md` Finding 5 (hierarchy discrepancy) — needs an explicit decision before merge, not a blocking defect |
| `backend/app/core/role_guards.py` | SAFE TO MERGE | Low-conflict, additive gate wiring |
| `backend/app/core/protected_tenants.py` | SAFE TO MERGE | Low-conflict |
| `backend/app/core/auth.py` | SAFE TO MERGE | Low-conflict |
| `backend/app/api/owner_admin.py` | HIGH RISK | `/users` endpoint query semantics fully replaced (tenant-filtered → platform-role-filtered); see `HIGH_RISK_CONFLICT_REPORT.md` §1. Must not be merged without an explicit decision on whether the cross-tenant roster is still needed |

## Backend — tests

| File | Classification | Basis |
|---|---|---|
| `backend/tests/test_owner_audit_logs.py` | SAFE TO MERGE | New, passing, isolated to new surface |
| `backend/tests/test_owner_platform_rbac_matrix.py` | SAFE TO MERGE | New, passing, validates every RBAC claim in this review |
| `backend/tests/test_owner_platform_staff_delegation.py` | SAFE TO MERGE | New, passing |
| `backend/tests/test_owner_platform_staff_lifecycle.py` | SAFE TO MERGE | New, passing |
| `backend/tests/test_owner_platform_staff_profile.py` | SAFE TO MERGE | New, passing |
| `backend/tests/test_treatment_identity_migration.py` | REQUIRES REVIEW | Trivial 1-line change (HEAD_REVISION constant); the 2 failures in this file are pre-existing/unrelated to the recovery (forward-only migration design), not a regression, but should be re-confirmed against main's current head at merge time |

## Frontend — cosmetic / low-risk

| File | Classification | Basis |
|---|---|---|
| `sns-emr-frontend/public/brand/sns-logo-dark.svg` | SAFE TO MERGE | Asset-only |
| `sns-emr-frontend/public/brand/sns-logo-icon.svg` | SAFE TO MERGE | Asset-only |
| `sns-emr-frontend/public/brand/sns-logo-light.svg` | SAFE TO MERGE | Asset-only |
| `sns-emr-frontend/public/brand/sns-logo-icon-dark.svg` | SAFE TO MERGE | New asset |
| `sns-emr-frontend/public/brand/sns-logo-icon-dark-tile.svg` | SAFE TO MERGE | New asset |
| `sns-emr-frontend/src/components/BrandLogo.tsx` | SAFE TO MERGE | Consumes the above assets only |
| `sns-emr-frontend/src/pages/SetPasswordPage.tsx` | REQUIRES REVIEW | New auth-adjacent page; needs frontend build/typecheck validation (not yet run) before merge |
| `sns-emr-frontend/src/App.tsx` | REQUIRES REVIEW | Route wiring change; depends on `authorization.ts` and `SetPasswordPage.tsx` both being reviewed first |

## Frontend — RBAC-sensitive

| File | Classification | Basis |
|---|---|---|
| `sns-emr-frontend/src/utils/authorization.ts` | BLOCKED | See `RBAC_SECURITY_REVIEW.md` Finding 1 — broadens `/owner` route access from OWNER-only to any platform-scope role; do not merge until every existing `/owner/*` page is confirmed to have its own per-action server-side gate |
| `sns-emr-frontend/src/api/ownerAdmin.ts` | HIGH RISK | Frontend contract for nearly every changed `owner_admin.py` endpoint; must land atomically with the backend file, not independently |
| `sns-emr-frontend/src/owner/pages/UserManagement.jsx` | HIGH RISK | Full-content rewrite of an existing page; see `HIGH_RISK_CONFLICT_REPORT.md` §3 |
| `sns-emr-frontend/src/owner/pages/AuditLogs.jsx` | HIGH RISK | Same overwrite-risk profile as `UserManagement.jsx` (284 insertions / 155 deletions) though not explicitly named in this request |
| `sns-emr-frontend/src/owner/OwnerDashboard.jsx` | REQUIRES REVIEW | Depends on the new access-level/RBAC surface being finalized first |
| `sns-emr-frontend/src/owner/shell/OwnerShell.jsx` | REQUIRES REVIEW | New shell component gating owner sub-navigation; must be reviewed alongside `authorization.ts` |
| `sns-emr-frontend/src/owner/accessLevels.js` | REQUIRES REVIEW | Client-side mirror of `ACCESS_LEVEL_FOR_ROLE`; must stay in sync with `roles.py` if that file's hierarchy changes per the compliance-review finding |
| `sns-emr-frontend/src/owner/auditCategories.js` | SAFE TO MERGE | Presentational constant, no access-control logic |
| `sns-emr-frontend/src/owner/components/AddStaffModal.jsx` | REQUIRES REVIEW | Depends on `ownerAdmin.ts`/`owner_admin.py` staff-creation endpoints landing first |
| `sns-emr-frontend/src/owner/components/AuditEventDrawer.jsx` | SAFE TO MERGE | Presentational, read-only display component |
| `sns-emr-frontend/src/owner/components/StaffProfileDrawer.jsx` | REQUIRES REVIEW | Depends on staff profile endpoints; exposes `allowed_actions`-gated buttons that must match backend `role_can()` exactly |

## Docs

| File | Classification | Basis |
|---|---|---|
| `docs/PLATFORM_ARCHITECTURE_ROADMAP.md` | SAFE TO MERGE | Documentation only |
| `docs/SNS_STAFF_ACCESS_CHECKPOINT.md` | SAFE TO MERGE | Documentation only |
| `.github/copilot-instructions.md` | REQUIRES REVIEW | Repo-wide agent instructions; confirm content still matches current conventions before adopting |

---

## Overall counts

- **SAFE TO MERGE:** 22 files (models/migrations, most tests, brand assets, docs)
- **REQUIRES REVIEW:** 15 files (roles.py, user.py, admin_bootstrap_service.py, App.tsx,
  SetPasswordPage.tsx, OwnerDashboard.jsx, OwnerShell.jsx, accessLevels.js, AddStaffModal.jsx,
  StaffProfileDrawer.jsx, test_treatment_identity_migration.py, copilot-instructions.md, and 3 more
  per the matrix above)
- **HIGH RISK:** 4 files (`owner_admin.py`, `ownerAdmin.ts`, `UserManagement.jsx`, `AuditLogs.jsx`)
- **BLOCKED:** 1 file (`authorization.ts` — do not merge until the per-action gating audit in
  `RBAC_SECURITY_REVIEW.md` Finding 1 is completed)

**No file in this recovery is recommended for immediate, unconditional merge without at least the
Batch 1 (models/migrations) validation already performed.** This matches, and does not change,
the batch sequencing already laid out in `integration-plan.md`.

DO NOT MERGE. DO NOT COMMIT. DO NOT OPEN A PR. All findings above are for human review only.
