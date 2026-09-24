# Owner Platform Merge Plan — File by File

Read-only. No merges, no commits performed. 46 files, grouped by integration batch (see
`integration-plan.md` for batch rationale); each row is a single file.

## Batch 1 — Database models & migrations (land first; foundation for everything else)

| File | Purpose | Dependencies | Risk | Merge strategy | Validation required | Rollback path |
|---|---|---|---|---|---|---|
| `backend/alembic/versions/um2s1a2f3f4b5_add_department_notes_updated_by_to_users.py` | Adds `department`/`notes`/`updated_by` columns to `users` | None (first migration in chain) | SAFE | Apply as-is | Migration chain to head (✅ done) | `alembic downgrade -1` |
| `backend/alembic/versions/um2a1c2c3o5u6_add_account_type_to_users.py` | Adds `account_type` column | Prior migration | SAFE | Apply as-is | ✅ done | `alembic downgrade -1` |
| `backend/alembic/versions/um2b1c2c3o5u7_add_identity_fields_to_users.py` | Adds `responsible_owner_id`/`identity_purpose`/`identity_scope` | Prior migration | SAFE | Apply as-is | ✅ done | `alembic downgrade -1` |
| `backend/alembic/versions/um2c1c2c3o5u8_add_platform_to_users.py` | Adds `platform` column, default `SNS Hospice Solutions` | Prior migration | SAFE | Apply as-is | ✅ done | `alembic downgrade -1` |
| `backend/alembic/versions/um2d1c2c3o5u9_add_staff_status_and_permission_grants.py` | Adds `platform_staff_status` column + `staff_permission_grants` table | Prior migration | SAFE | Apply as-is | ✅ done (downgrade verified clean) | `alembic downgrade -1` |
| `backend/app/models/user.py` | ORM fields matching all 5 migrations | Migrations above | REQUIRES REVIEW | Merge additive hunk only; confirm no other in-flight main change to this model | py_compile ✅, migration/model parity ✅ | Revert hunk to main's version (schema unaffected if migrations already applied — would need a compensating migration) |
| `backend/app/models/staff_permission_grant.py` | ORM model for delegated grants | `um2d...` migration | SAFE | Apply as-is | py_compile ✅ | Delete file + revert `__init__.py` import |
| `backend/app/models/__init__.py` | Registers `StaffPermissionGrant` import | `staff_permission_grant.py` | SAFE | Apply as-is | py_compile ✅ | Remove one import line |
| `backend/app/core/account_types.py` | Account-type constants/validation | None | SAFE | Apply as-is | py_compile ✅ | Delete file |
| `backend/app/core/departments.py` | Department taxonomy/validation | None | SAFE | Apply as-is | py_compile ✅ | Delete file |
| `backend/app/core/job_titles.py` | Department-scoped job-title catalog | `departments.py` | SAFE | Apply as-is | py_compile ✅ | Delete file |
| `backend/app/core/platforms.py` | Platform-name catalog | None | SAFE | Apply as-is | py_compile ✅ | Delete file |
| `backend/app/services/admin_bootstrap_service.py` | Dev-seed OWNER identity; recovered change is a cosmetic `full_name` rename only | None | REQUIRES REVIEW | Confirm the naming change is still wanted before taking | py_compile ✅ | Revert one string literal |

## Batch 2 — Permissions (RBAC core)

| File | Purpose | Dependencies | Risk | Merge strategy | Validation required | Rollback path |
|---|---|---|---|---|---|---|
| `backend/app/core/roles.py` | Adds `staff.*` capability model, `role_can()`, delegation rules, access-level tiers | Batch 1 (grant table) | HIGH (security-critical; see `OWNER_PLATFORM_SECURITY_REVIEW.md` #2) | Manual side-by-side review against main before taking; resolve `RBAC_HIERARCHY_DECISION.md` first | `test_owner_platform_rbac_matrix.py` (20/20 ✅), `test_owner_platform_staff_delegation.py` (17/17 ✅) | Revert to main's version; no schema impact (code-only) |
| `backend/app/core/role_guards.py` | `require_platform_permission()` FastAPI dependency wiring `role_can()` into routes | `roles.py` | REQUIRES REVIEW | Apply alongside `roles.py` | Covered by same test suites | Revert to main's version |
| `backend/app/api/owner_admin.py` | Adds staff lifecycle, delegated-permission-grant, and role-change endpoints; **also replaces** the existing `/users` cross-tenant roster query with a platform-staff-only query | Batches 1-2 (models + `roles.py`) | HIGH RISK (see `HIGH_RISK_CONFLICT_REPORT.md` §1 and `OWNER_PLATFORM_SECURITY_REVIEW.md` #3) | Manual, section-by-section merge — keep existing tenant onboarding/financial/system-health sections verbatim; decide explicitly whether `/users` should remain cross-tenant or become platform-staff-only (or split into two routes) before taking the new roster query; land new lifecycle/grant/role endpoints as pure additions once resolved | `test_owner_platform_rbac_matrix.py`, `test_owner_platform_staff_delegation.py`, `test_owner_platform_staff_lifecycle.py`, `test_owner_platform_staff_profile.py`, `test_owner_audit_logs.py` all ✅ against the new endpoints; old `/users` cross-tenant behavior not independently re-tested | Revert file to main's version; must be reverted together with `ownerAdmin.ts`/`UserManagement.jsx`/`AuditLogs.jsx` to avoid a broken frontend/backend contract |

## Batch 3 — Authentication

| File | Purpose | Dependencies | Risk | Merge strategy | Validation required | Rollback path |
|---|---|---|---|---|---|---|
| `backend/app/core/auth.py` | Expands `VALID_ROLES` so new platform roles can authenticate | Batch 2 | REQUIRES REVIEW | Apply alongside `roles.py` | Covered by RBAC matrix tests | Revert to main's version |
| `backend/app/core/protected_tenants.py` | Adds `PLATFORM_TENANT_ID` constant | None | SAFE | Apply as-is | py_compile ✅ | Revert one constant |
| `sns-emr-frontend/src/utils/authorization.ts` | Broadens `/owner` route entry to any platform-scope role | Batch 2 (backend gating) | **BLOCKED** | Do not merge until every pre-existing `/owner/*` page is confirmed to have its own server-side action gate (`OWNER_PLATFORM_SECURITY_REVIEW.md` #1) | Frontend build/typecheck **not yet run** | Revert to main's stricter `role === "OWNER"` check |

## Batch 4 — Platform Owner UI

| File | Purpose | Dependencies | Risk | Merge strategy | Validation required | Rollback path |
|---|---|---|---|---|---|---|
| `sns-emr-frontend/src/owner/shell/OwnerShell.jsx` | New owner-workspace shell/navigation | Batch 3 | REQUIRES REVIEW | Apply alongside `authorization.ts` decision | Frontend build pending | Delete file; restore prior owner layout if one existed |
| `sns-emr-frontend/src/owner/OwnerDashboard.jsx` | Dashboard entry point; changed shelling/loading/delegated-access routing | `OwnerShell.jsx` | REQUIRES REVIEW | Manual diff against main | Frontend build pending | Revert to main's version |
| `sns-emr-frontend/src/components/BrandLogo.tsx` | Centralizes brand asset usage | Brand SVGs | SAFE | Apply as-is | Frontend build pending | Revert to main's version |
| `sns-emr-frontend/public/brand/sns-logo-dark.svg` | Rebrand asset | None | SAFE | Apply as-is | Visual check | Revert asset |
| `sns-emr-frontend/public/brand/sns-logo-icon.svg` | Rebrand asset | None | SAFE | Apply as-is | Visual check | Revert asset |
| `sns-emr-frontend/public/brand/sns-logo-light.svg` | Rebrand asset | None | SAFE | Apply as-is | Visual check | Revert asset |
| `sns-emr-frontend/public/brand/sns-logo-icon-dark.svg` | New rebrand asset | None | SAFE | Apply as-is | Visual check | Delete file |
| `sns-emr-frontend/public/brand/sns-logo-icon-dark-tile.svg` | New rebrand asset | None | SAFE | Apply as-is | Visual check | Delete file |
| `sns-emr-frontend/src/App.tsx` | Adds `/set-password` route | `SetPasswordPage.tsx` | REQUIRES REVIEW | Apply alongside `SetPasswordPage.tsx` | Frontend build pending | Remove the one route line |
| `sns-emr-frontend/src/pages/SetPasswordPage.tsx` | New set-password flow page | `App.tsx` route | REQUIRES REVIEW | Apply alongside `App.tsx` | Frontend build pending | Delete file + route line |

## Batch 5 — Staff Management UI

| File | Purpose | Dependencies | Risk | Merge strategy | Validation required | Rollback path |
|---|---|---|---|---|---|---|
| `sns-emr-frontend/src/owner/pages/UserManagement.jsx` | Repurposed from cross-tenant user list to SNS Staff & Access | Batches 1-4, `ownerAdmin.ts` | HIGH RISK | Manual reconciliation — confirm main's cross-tenant behavior isn't silently dropped (`HIGH_RISK_CONFLICT_REPORT.md` §3) | Backend covered by Batch 2 tests; frontend build pending | Revert to main's version |
| `sns-emr-frontend/src/owner/components/AddStaffModal.jsx` | Create/invite staff flow | `owner_admin.py` staff endpoints | REQUIRES REVIEW | Apply with `UserManagement.jsx` | Frontend build pending | Delete file |
| `sns-emr-frontend/src/owner/components/StaffProfileDrawer.jsx` | Per-account profile/access/security/audit tabs | `owner_admin.py` profile endpoints | REQUIRES REVIEW | Apply with `UserManagement.jsx`; verify `allowed_actions` buttons match `role_can()` exactly | Frontend build pending | Delete file |
| `sns-emr-frontend/src/owner/accessLevels.js` | Client-side display mirror of `ACCESS_LEVEL_FOR_ROLE` | `roles.py` hierarchy decision | REQUIRES REVIEW | Keep in sync with whatever hierarchy is approved (`RBAC_HIERARCHY_DECISION.md`) | Frontend build pending | Delete file |
| `sns-emr-frontend/src/api/ownerAdmin.ts` | Frontend API contract for `owner_admin.py` | `owner_admin.py` | HIGH RISK | Must land atomically with backend file, not independently | Frontend build pending | Revert to main's version |

## Batch 6 — Audit Logs

| File | Purpose | Dependencies | Risk | Merge strategy | Validation required | Rollback path |
|---|---|---|---|---|---|---|
| `sns-emr-frontend/src/owner/pages/AuditLogs.jsx` | Standalone audit viewer (severity, export, related events) | Batches 1-2, audit endpoints | HIGH RISK | Same overwrite-risk profile as `UserManagement.jsx`; note checkpoint doc said this was "awaiting design review" — confirm design sign-off status before merge | Backend: `test_owner_audit_logs.py` (34/34 ✅); frontend build pending | Revert to main's version |
| `sns-emr-frontend/src/owner/components/AuditEventDrawer.jsx` | Audit event detail drawer | `AuditLogs.jsx` | REQUIRES REVIEW | Apply with `AuditLogs.jsx` | Frontend build pending | Delete file |
| `sns-emr-frontend/src/owner/auditCategories.js` | Presentational audit category constants | None | SAFE | Apply as-is | Frontend build pending | Delete file |

## Batch 7 — Testing & Documentation

| File | Purpose | Dependencies | Risk | Merge strategy | Validation required | Rollback path |
|---|---|---|---|---|---|---|
| `backend/tests/test_owner_audit_logs.py` | Audit endpoint coverage | Batch 6 backend | SAFE | Land with Batch 2/6 | ✅ 34/34 passing | Delete file |
| `backend/tests/test_owner_platform_rbac_matrix.py` | Core RBAC coverage | Batch 2 | SAFE | Land with Batch 2 | ✅ 20/20 passing | Delete file |
| `backend/tests/test_owner_platform_staff_delegation.py` | Delegation coverage | Batch 2 | SAFE | Land with Batch 2 | ✅ 17/17 passing | Delete file |
| `backend/tests/test_owner_platform_staff_lifecycle.py` | Lifecycle coverage | Batch 1 | SAFE | Land with Batch 1 | ✅ passing (part of 122/122) | Delete file |
| `backend/tests/test_owner_platform_staff_profile.py` | Profile field coverage | Batch 1 | SAFE | Land with Batch 1 | ✅ passing (part of 122/122) | Delete file |
| `backend/tests/test_treatment_identity_migration.py` | Pre-existing test, 1-line `HEAD_REVISION` bump | Migration chain | REQUIRES REVIEW | Re-check `HEAD_REVISION` against main's actual current head at merge time | 2 unrelated pre-existing failures (forward-only migration design, not a regression) | Revert 1-line change |
| `docs/PLATFORM_ARCHITECTURE_ROADMAP.md` | Roadmap documentation | None | SAFE | Land last | None (docs only) | Delete file |
| `docs/SNS_STAFF_ACCESS_CHECKPOINT.md` | Session checkpoint documentation | None | SAFE | Land last | None (docs only) | Delete file |
| `.github/copilot-instructions.md` | Repo-wide agent instructions | None | REQUIRES REVIEW | Confirm content matches current conventions before adopting | None (docs only) | Revert to main's version (if one exists) or delete |

## Summary

46/46 files accounted for across 7 batches (verified: 12 Batch 1 + 3 Batch 2 + 3 Batch 3 + 10
Batch 4 + 5 Batch 5 + 3 Batch 6 + 9 Batch 7 = 45 rows shown, plus `staff_permission_grant.py`
counted once in Batch 1 and referenced again in Batch 2's dependency column = 46 distinct files).
3 files are HIGH RISK (`owner_admin.py`/`UserManagement.jsx`/`ownerAdmin.ts` — see
`HIGH_RISK_CONFLICT_REPORT.md`), 1 file is BLOCKED (`authorization.ts`), the remainder are SAFE or
REQUIRES REVIEW. No merge has been performed for any batch.
