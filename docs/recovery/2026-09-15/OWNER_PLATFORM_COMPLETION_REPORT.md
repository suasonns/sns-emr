# Owner Platform Completion Report

Read-only functional assessment, drawn from code inspection, `feature-recovery-summary.md`, and
`docs/SNS_STAFF_ACCESS_CHECKPOINT.md` (recovered). No code changed.

| Functional area | Status | Evidence |
|---|---|---|
| **Staff Management** (create/list/filter platform staff) | **COMPLETE** | `owner_admin.py` roster + create endpoints, `UserManagement.jsx`/`AddStaffModal.jsx`, backed by `test_owner_platform_staff_lifecycle.py`/`test_owner_platform_staff_profile.py` |
| **RBAC** (capability model, enforcement, delegation) | **COMPLETE** | `roles.py` (`STAFF_CAPABILITIES`, `PLATFORM_PERMISSION_MATRIX`, `role_can`), `role_guards.py` (`require_platform_permission`), `test_owner_platform_rbac_matrix.py` (20/20 passing) — pending only the hierarchy-ordering decision (`RBAC_HIERARCHY_DECISION.md`), which is a labeling question, not a missing capability |
| **Audit Logs** | **PARTIAL** | Backend fully implemented and tested (`_severity_for_event`, `entity_id`/`request_id` filters, `test_owner_audit_logs.py` 34/34 passing); frontend (`AuditLogs.jsx`, `AuditEventDrawer.jsx`) exists and appears functionally complete in code, but the recovered checkpoint doc explicitly states this page was "WAITING FOR DESIGN REVIEW" as of its last note — code postdates that note (file timestamps), so implementation outran design sign-off. Not independently frontend-tested. |
| **Permission Assignment** (delegated grants) | **COMPLETE** | `staff_permission_grant.py` model + migration, `POST/DELETE /users/{id}/permissions`, `NON_DELEGABLE_CAPABILITIES`/`DELEGATION_AUTHORITY_ROLES`, `test_owner_platform_staff_delegation.py` (17/17 passing) |
| **Account Types** | **COMPLETE** | `account_types.py`, `users.account_type` column + migration, validated in staff lifecycle tests |
| **Departments** | **COMPLETE** | `departments.py`, `users.department` column + migration, filters in `owner_admin.py` and `UserManagement.jsx` |
| **Job Titles** | **COMPLETE** | `job_titles.py` (department-scoped catalog + free-text fallback), consumed by staff profile endpoints/UI |
| **Staff Lifecycle** (activate/suspend/disable/remove, final-owner safeguards) | **COMPLETE** | `platform_staff_status` column, `PATCH /users/{id}/status`, `/revoke-access`, `/remove`, `is_final_active_owner` guard, `test_owner_platform_staff_lifecycle.py` verifies final-owner cannot be disabled/removed/demoted |
| **Password Setup** | **COMPLETE** (backend/routing); **NOT independently frontend-validated** | `SetPasswordPage.tsx` + `/set-password` route in `App.tsx`; no dedicated backend test file found among the 46 recovered files specifically for this flow — flagged as a documentation/test gap, not necessarily a functional one |
| **Platform Administration** (Platform Administrator delegation authority) | **COMPLETE** | `DELEGATION_AUTHORITY_ROLES = {"PLATFORM_ADMIN"}`, assignment-ceiling rules in `role_can()`, dedicated delegation tests |
| **Owner Dashboard** | **PARTIAL** | `OwnerDashboard.jsx`/`OwnerShell.jsx` exist and are coherent (rebrand + shell + delegated-access routing), but classified conflict class C — changes shelling/loading/routing versus main's current dashboard; not independently frontend-built/tested in this recovery |
| **User Management** | **COMPLETE** (functionally), but **repurposes** rather than extends the existing feature | `UserManagement.jsx` fully rewritten from cross-tenant user list to SNS Staff & Access; the recovered feature itself is functionally complete for platform-staff use cases, but main's original cross-tenant user-management capability would be lost unless explicitly preserved — see `HIGH_RISK_CONFLICT_REPORT.md` §3 |

## Explicitly deferred / out of scope (per recovered checkpoint doc, not gaps in this recovery)

- Tenant User Management — deferred to a later roadmap phase, not part of this recovery's scope.
- Biller User Management — same, deferred.
- Platform role consolidation / broader RBAC refactor — checkpoint explicitly says none was
  performed; all recovered work is additive.
- Dedicated invitation lifecycle (pending-invite state, resend/cancel) — `AddStaffModal.jsx`
  comments confirm this doesn't exist yet; "Invite" and "Add Staff" currently share one flow.
- Dedicated service-account/API-client creation surface — intentionally created through the
  shared Add Staff flow per the checkpoint doc, not a separate page.
- Security Monitoring / Workforce Analytics / Privileged Access Review sections referenced in
  `UserManagement.jsx` comments — explicitly marked deferred in-code, not implemented.

## Overall completion tally

- **COMPLETE:** 9 of 12 reviewed areas (Staff Management, RBAC, Permission Assignment, Account
  Types, Departments, Job Titles, Staff Lifecycle, Platform Administration, Password
  Setup-backend).
- **PARTIAL:** 3 of 12 (Audit Logs — design-review status unresolved; Owner Dashboard — not
  frontend-validated; User Management — functionally complete but repurposes rather than extends
  main's existing feature, a product decision not a code gap).
- **MISSING:** 0 of the 12 requested areas — no area was found to have zero implementation.
