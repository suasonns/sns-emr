# Staff Management Gap Report

Scope: Staff Management, including RBAC, Access Levels, Permission Grants, Account Types,
Departments, Job Titles, Staff Lifecycle, Password Setup, User Management. No redesign, no new
architecture. Classification: COMPLETE / PARTIAL / MISSING.

| Item | Frontend | Backend | Database | API | Test | Classification |
|---|---|---|---|---|---|---|
| **Staff creation** | `AddStaffModal.jsx` implemented | `POST /users` (owner_admin.py) validates account_type/department/job_title/platform | `users` table + `account_types`/`departments`/`job_titles`/`platforms` catalogs | Implemented | `test_owner_platform_staff_profile.py`, `test_owner_platform_staff_lifecycle.py` — passing | **COMPLETE** |
| **Staff editing** | `StaffProfileDrawer.jsx` profile tab | Profile update endpoints in `owner_admin.py` | Same as above | Implemented | Covered by staff profile/lifecycle test files | **COMPLETE** |
| **Staff deactivation** | Status controls in `UserManagement.jsx`/`StaffProfileDrawer.jsx` | `PATCH /users/{id}/status` (ACTIVE/SUSPENDED/DISABLED/REMOVED) | `users.platform_staff_status` column (migration `um2d1c2c3o5u9`) | Implemented | `test_owner_platform_staff_lifecycle.py` — passing (final-owner cannot be disabled/removed/demoted verified) | **COMPLETE** |
| **Access assignment (role change)** | Role selector in `StaffProfileDrawer.jsx` | `PATCH /users/{id}/role` | `users.role` (existing column) | Implemented | `test_owner_platform_staff_lifecycle.py` — self-role-change blocked, non-owner cannot assign OWNER, verified | **COMPLETE** |
| **RBAC (capability model & enforcement)** | `accessLevels.js` (display), `allowed_actions` consumed per-row | `roles.py::role_can()`, `role_guards.py::require_platform_permission()` | No dedicated table (code-defined matrix) + `staff_permission_grants` table for delegated grants | Implemented across all `owner_admin.py` staff endpoints | `test_owner_platform_rbac_matrix.py` — 20/20 passing | **COMPLETE** (functionally); hierarchy tier ORDERING still needs approval — not a missing capability, a labeling decision already flagged separately |
| **Permission inheritance** | N/A (backend-derived) | `effective_capabilities_for_role()` unions role-default capabilities with active delegated grants; there is **no parent-child role hierarchy inheritance** — the model is a flat per-role capability matrix plus explicit delegation, not cascading inheritance between roles | `staff_permission_grants` table | `capabilities_for_role()` exposes the computed union | `test_owner_platform_staff_delegation.py` — 17/17 passing, verifies grants add to and revocation removes from the effective set | **COMPLETE** as implemented (capability composition via role-default + grant union); note this is not a hierarchical inheritance tree — confirm that is the intended model, since "inheritance" could imply the latter |
| **Departments** | Department filter/field in `UserManagement.jsx`/`AddStaffModal.jsx` | `departments.py` catalog + validation | `users.department` column (migration `um2s1a2f3f4b5`) | `available_departments` returned by `owner_admin.py` | Exercised in staff lifecycle/profile tests | **COMPLETE** |
| **Job titles** | Job-title field, department-scoped | `job_titles.py` (department-scoped catalog + free-text fallback) | No dedicated table — `users` field, validated against `job_titles.py` | `job_titles_by_department` returned by `owner_admin.py` | Exercised in staff lifecycle/profile tests | **COMPLETE** |
| **Account types** | Account-type column/filter in `UserManagement.jsx` | `account_types.py` (validated constants) | `users.account_type` column (migration `um2a1c2c3o5u6`) | `available_account_types` returned by `owner_admin.py` | Exercised in staff lifecycle/profile tests | **COMPLETE** |
| **Password setup** | `SetPasswordPage.tsx` + `/set-password` route in `App.tsx` | `POST /auth/set-password`, `GET /auth/set-password/validate` (pre-existing on `main`, not part of the 46 recovered files) | Uses existing password/reset-token fields on `users` | Implemented (pre-existing) | **No dedicated test found anywhere (main or recovery branch) for the token-based `/auth/set-password` flow** | **MISSING** (test coverage only — the endpoints and frontend page exist, but there is no automated test verifying the set-password token flow end-to-end) |
| **Audit logging (of staff actions)** | N/A (feeds Audit Logs page) | `_severity_for_event`, `_affected_permissions_for_role_change` in `owner_admin.py` | Existing audit log table (pre-existing, extended with severity/entity fields) | Implemented | `test_owner_audit_logs.py` — 34/34 passing | **COMPLETE** |
| **Validation** (account-type/department/job-title/platform field validation on create & edit) | Form-level validation in `AddStaffModal.jsx`/`StaffProfileDrawer.jsx` | Server-side validation in `owner_admin.py` against `account_types.py`/`departments.py`/`job_titles.py`/`platforms.py` | N/A | Implemented | Covered by `test_owner_platform_staff_profile.py`/`test_owner_platform_staff_lifecycle.py` | **COMPLETE** |
| **Frontend build/typecheck/lint** | N/A | N/A | N/A | N/A | **Never run** against the recovery worktree (no `node_modules` installed) | **MISSING** (validation gap, not an implementation gap — code exists but is unverified to compile/lint/build) |
| **Merge to `main`** | N/A | N/A | N/A | N/A | N/A | **MISSING** — all of the above exists only in the isolated `recovery/copilot-session-2026-09-14` branch; none of it is live on `main` today |

## Overall Staff Management classification: **PARTIAL**

All 12 functional completion criteria the directive listed for Staff Management
(creation/editing/deactivation/access-assignment/RBAC/permission-inheritance/departments/
job-titles/account-types/password-setup/audit-logging/validation) are implemented and, with one
exception, backed by passing tests. The two items keeping this from COMPLETE:
1. **Password setup** has no dedicated automated test for the token-based flow.
2. **Nothing has been merged, frontend-built, or deployed** — the entire feature set exists only
   in the isolated recovery branch.
