# Recovery File Matrix — 46 files

Read-only. Source: `git status --short` in `recovery/copilot-session-2026-09-14`
(`C:\Users\rdsua\Desktop\copilot-recovery-2026-09-15\recovery-worktree`), diffed against `main` HEAD
`b552fcb`. **Correction to prior report:** exact count is **19 modified / 27 new** (not 22/24 as
stated in the first recovery summary — re-verified directly against `git status --short` this pass).

Legend for tag columns: ✅ = directly relevant, — = not applicable.

| # | Path | New/Mod | Owner Platform | RBAC | Audit Logs | Auth | Frontend | Backend | Migrations | Tests |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `backend/app/api/owner_admin.py` | Mod | ✅ | ✅ | ✅ | — | — | ✅ | — | — |
| 2 | `backend/app/core/auth.py` | Mod | — | ✅ | — | ✅ | — | ✅ | — | — |
| 3 | `backend/app/core/protected_tenants.py` | Mod | ✅ | — | — | — | — | ✅ | — | — |
| 4 | `backend/app/core/role_guards.py` | Mod | ✅ | ✅ | — | ✅ | — | ✅ | — | — |
| 5 | `backend/app/core/roles.py` | Mod | ✅ | ✅ | — | ✅ | — | ✅ | — | — |
| 6 | `backend/app/models/__init__.py` | Mod | — | — | — | — | — | ✅ | — | — |
| 7 | `backend/app/models/user.py` | Mod | ✅ | ✅ | — | — | — | ✅ | ✅ | — |
| 8 | `backend/app/services/admin_bootstrap_service.py` | Mod | ✅ | — | — | — | — | ✅ | — | — |
| 9 | `backend/tests/test_treatment_identity_migration.py` | Mod | — | — | — | — | — | — | ✅ | ✅ |
| 10 | `sns-emr-frontend/public/brand/sns-logo-dark.svg` | Mod | — | — | — | — | ✅ | — | — | — |
| 11 | `sns-emr-frontend/public/brand/sns-logo-icon.svg` | Mod | — | — | — | — | ✅ | — | — | — |
| 12 | `sns-emr-frontend/public/brand/sns-logo-light.svg` | Mod | — | — | — | — | ✅ | — | — | — |
| 13 | `sns-emr-frontend/src/api/ownerAdmin.ts` | Mod | ✅ | ✅ | ✅ | — | ✅ | — | — | — |
| 14 | `sns-emr-frontend/src/App.tsx` | Mod | ✅ | — | — | ✅ | ✅ | — | — | — |
| 15 | `sns-emr-frontend/src/components/BrandLogo.tsx` | Mod | — | — | — | — | ✅ | — | — | — |
| 16 | `sns-emr-frontend/src/owner/OwnerDashboard.jsx` | Mod | ✅ | ✅ | — | — | ✅ | — | — | — |
| 17 | `sns-emr-frontend/src/owner/pages/AuditLogs.jsx` | Mod | ✅ | ✅ | ✅ | — | ✅ | — | — | — |
| 18 | `sns-emr-frontend/src/owner/pages/UserManagement.jsx` | Mod | ✅ | ✅ | — | — | ✅ | — | — | — |
| 19 | `sns-emr-frontend/src/utils/authorization.ts` | Mod | ✅ | ✅ | — | ✅ | ✅ | — | — | — |
| 20 | `.github/copilot-instructions.md` | New | — | — | — | — | — | — | — | — |
| 21 | `backend/alembic/versions/um2a1c2c3o5u6_add_account_type_to_users.py` | New | ✅ | — | — | — | — | ✅ | ✅ | — |
| 22 | `backend/alembic/versions/um2b1c2c3o5u7_add_identity_fields_to_users.py` | New | ✅ | — | — | — | — | ✅ | ✅ | — |
| 23 | `backend/alembic/versions/um2c1c2c3o5u8_add_platform_to_users.py` | New | ✅ | — | — | — | — | ✅ | ✅ | — |
| 24 | `backend/alembic/versions/um2d1c2c3o5u9_add_staff_status_and_permission_grants.py` | New | ✅ | ✅ | — | — | — | ✅ | ✅ | — |
| 25 | `backend/alembic/versions/um2s1a2f3f4b5_add_department_notes_updated_by_to_users.py` | New | ✅ | — | — | — | — | ✅ | ✅ | — |
| 26 | `backend/app/core/account_types.py` | New | ✅ | — | — | — | — | ✅ | — | — |
| 27 | `backend/app/core/departments.py` | New | ✅ | — | — | — | — | ✅ | — | — |
| 28 | `backend/app/core/job_titles.py` | New | ✅ | — | — | — | — | ✅ | — | — |
| 29 | `backend/app/core/platforms.py` | New | ✅ | — | — | — | — | ✅ | — | — |
| 30 | `backend/app/models/staff_permission_grant.py` | New | ✅ | ✅ | — | — | — | ✅ | ✅ | — |
| 31 | `backend/tests/test_owner_audit_logs.py` | New | ✅ | — | ✅ | — | — | — | — | ✅ |
| 32 | `backend/tests/test_owner_platform_rbac_matrix.py` | New | ✅ | ✅ | — | — | — | — | — | ✅ |
| 33 | `backend/tests/test_owner_platform_staff_delegation.py` | New | ✅ | ✅ | — | — | — | — | — | ✅ |
| 34 | `backend/tests/test_owner_platform_staff_lifecycle.py` | New | ✅ | ✅ | — | — | — | — | — | ✅ |
| 35 | `backend/tests/test_owner_platform_staff_profile.py` | New | ✅ | — | — | — | — | — | — | ✅ |
| 36 | `docs/PLATFORM_ARCHITECTURE_ROADMAP.md` | New | ✅ | — | — | — | — | — | — | — |
| 37 | `docs/SNS_STAFF_ACCESS_CHECKPOINT.md` | New | ✅ | — | — | — | — | — | — | — |
| 38 | `sns-emr-frontend/public/brand/sns-logo-icon-dark.svg` | New | — | — | — | — | ✅ | — | — | — |
| 39 | `sns-emr-frontend/public/brand/sns-logo-icon-dark-tile.svg` | New | — | — | — | — | ✅ | — | — | — |
| 40 | `sns-emr-frontend/src/owner/accessLevels.js` | New | ✅ | ✅ | — | — | ✅ | — | — | — |
| 41 | `sns-emr-frontend/src/owner/auditCategories.js` | New | ✅ | — | ✅ | — | ✅ | — | — | — |
| 42 | `sns-emr-frontend/src/owner/components/AddStaffModal.jsx` | New | ✅ | ✅ | — | — | ✅ | — | — | — |
| 43 | `sns-emr-frontend/src/owner/components/AuditEventDrawer.jsx` | New | ✅ | — | ✅ | — | ✅ | — | — | — |
| 44 | `sns-emr-frontend/src/owner/components/StaffProfileDrawer.jsx` | New | ✅ | ✅ | — | — | ✅ | — | — | — |
| 45 | `sns-emr-frontend/src/owner/shell/OwnerShell.jsx` | New | ✅ | ✅ | — | ✅ | ✅ | — | — | — |
| 46 | `sns-emr-frontend/src/pages/SetPasswordPage.tsx` | New | — | — | — | ✅ | ✅ | — | — | — |

## Notes
- Full purpose/dependency narrative per file: `recovered-file-inventory.md`.
- Full per-file conflict classification (A/B/C/D): `conflict-analysis.md`.
- 9 brand SVGs/logo files are a cosmetic rebrand track, unrelated to RBAC; low risk regardless of
  classification.
