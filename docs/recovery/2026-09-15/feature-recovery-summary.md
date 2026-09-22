# Feature Recovery Summary

## Scope recovered from code and docs

The recovered session clearly targeted the roadmap’s **Platform Owner Experience** phase, specifically the **Platform Owner User Management / SNS Staff & Access** slice described in `docs/PLATFORM_ARCHITECTURE_ROADMAP.md`: SNS staff profile, department, platform role, access level, security access, audit history, service accounts, and API identities, plus the “Platform Owner Safeguards” around multiple owners and final-owner continuity.

## What appears completed

### 1. Core backend RBAC foundation

This is the strongest completed area in the recovery set.

- `backend/app/core/roles.py` adds the recovered staff-permission engine (`STAFF_CAPABILITIES`, `PLATFORM_PERMISSION_MATRIX`, `role_can`, `can_delegate_capability`, `ACCESS_LEVEL_FOR_ROLE`, `PLATFORM_STAFF_STATUSES`).
- `backend/app/core/role_guards.py` adds `require_platform_permission()`, making the RBAC rules usable as real FastAPI dependencies.
- `backend/app/core/auth.py` expands `VALID_ROLES` so the new platform roles can actually authenticate.
- `backend/tests/test_owner_platform_rbac_matrix.py` directly exercises owner superuser behavior, non-owner ceilings, denial for tenant/biller roles, and dependency gating.

**Roadmap mapping:** “Platform Roles,” “Access Level,” and part of “Security Access.”

### 2. Platform-staff lifecycle and ownership continuity

The recovered backend goes well beyond simple enable/disable.

- `backend/app/api/owner_admin.py` adds `PATCH /users/{id}/status`, `POST /users/{id}/revoke-access`, `POST /users/{id}/remove`, `PATCH /users/{id}/role`, and `GET /users/{id}` serialization that includes `is_final_active_owner`.
- `backend/app/models/user.py` adds `platform_staff_status` alongside existing `active`, making suspension/disable/remove distinct states.
- `backend/tests/test_owner_platform_staff_delegation.py` and `backend/tests/test_owner_platform_staff_lifecycle.py` verify: final active owner cannot be disabled/removed/demoted, non-owners cannot assign OWNER, self-role change is blocked, and removed accounts cannot authenticate.

**Roadmap mapping:** “SNS Staff Profile,” “Platform Role,” “Security Access,” and “Platform Owner Safeguards.”

### 3. Staff-profile structure for human staff and non-human identities

Recovered code supports both ordinary staff and accountable platform identities.

- `backend/app/models/user.py` adds `department`, `notes`, `updated_by`, `account_type`, `responsible_owner_id`, `identity_purpose`, `identity_scope`, and `platform`.
- `backend/app/core/account_types.py`, `departments.py`, `job_titles.py`, and `platforms.py` define the recovered organizational vocabulary.
- `backend/app/api/owner_admin.py` validates those fields and returns `available_departments`, `available_platforms`, `job_titles_by_department`, and `available_account_types` to the frontend.
- `backend/tests/test_owner_platform_staff_lifecycle.py` verifies account-type filters, responsible-owner metadata, platform defaults/validation, and job-title catalog enforcement.

**Roadmap mapping:** “SNS Staff Profile,” “Department,” “Service Accounts,” and “API Identities.”

### 4. Delegated administration / database-backed permission grants

This is an explicit feature, not a side effect.

- `backend/app/models/staff_permission_grant.py` and migration `um2d...` create a table for delegated `staff.*` grants.
- `backend/app/api/owner_admin.py` adds `GET/POST/DELETE /users/{id}/permissions` and the supporting active-grant query/serialization helpers.
- `backend/app/core/roles.py` defines `NON_DELEGABLE_CAPABILITIES` and `DELEGATION_AUTHORITY_ROLES` so ownership authority cannot be casually delegated.
- `backend/tests/test_owner_platform_staff_delegation.py` proves that a delegated grant changes actual endpoint access and that revocation removes it.

**Roadmap mapping:** “Security Access.”

### 5. Owner UI for SNS Staff & Access

The recovered frontend is a real UI surface, not just API scaffolding.

- `sns-emr-frontend/src/owner/pages/UserManagement.jsx` is repurposed into **SNS Staff & Access** for platform personnel only.
- `AddStaffModal.jsx` handles create/invite flows.
- `StaffProfileDrawer.jsx` handles profile, access, security, and audit tabs for one account.
- `accessLevels.js` renders backend-derived access-level labels without inventing local permission logic.
- `sns-emr-frontend/src/utils/authorization.ts` allows any `platform`-scope user to reach `/owner`, leaving fine-grained controls to backend `allowed_actions`.

**Roadmap mapping:** “SNS Staff Profile,” “Department,” “Platform Role,” “Access Level,” “Security Access,” “Service Accounts,” and “API Identities.”

## What looks partially completed

### 1. Standalone owner Audit Logs page

There is meaningful implementation here, but the evidence is mixed.

- Code exists: `sns-emr-frontend/src/owner/pages/AuditLogs.jsx`, `auditCategories.js`, and `AuditEventDrawer.jsx` form a substantial standalone audit viewer with severity badges, export, related events, and request IDs.
- Backend support exists: `backend/app/api/owner_admin.py` adds audit `severity`, `affected_permissions`, `entity_id`, and `request_id`, and `backend/tests/test_owner_audit_logs.py` covers those behaviors.
- But the recovered checkpoint doc says: `Audit Logs (standalone page) = WAITING FOR DESIGN REVIEW` and says “No code will be written for this ahead of design approval.”

**Interpretation:** by file timestamps, the checkpoint note (`2026-09-14 22:53`) predates the newest audit UI files (`01:19` and `01:24` on 2026-09-15). So the recovered session appears to have moved past the checkpoint and started/implemented the standalone page anyway. That makes the feature real, but it also makes it the clearest documentation/code divergence in the recovery set.

### 2. “Invite Staff” lifecycle

- `AddStaffModal.jsx` explicitly says there is **no separate invite-only pending state** yet: it uses the same create-account flow and treats temp password + reset link as an implicit invitation.
- `UserManagement.jsx` still exposes both **Invite Staff** and **Add Staff** buttons, but they open the same modal and backend path.

**Interpretation:** the UX entry point exists, but the richer invitation lifecycle (pending invite, resend, cancel, never-activated state) is still deferred.

### 3. Per-account audit UX versus org-wide audit UX

- The checkpoint says the per-account drawer’s audit tab was a known minor limitation.
- The recovered backend tests, especially `test_staff_audit_history_reflects_real_lifecycle_events`, suggest the API endpoint now returns more than creation events.

**Interpretation:** there is a documentation/code mismatch here too. The backend side looks stronger than the checkpoint claims, but I did not independently execute the frontend, so this remains “partially completed / needs confirmation” rather than clearly closed.

## What is still missing / explicitly TODO

These gaps are directly supported by comments or docs in the recovered files.

1. **Tenant User Management** — explicitly deferred in `docs/SNS_STAFF_ACCESS_CHECKPOINT.md`; roadmap phase is still Platform Owner before Tenant Experience.
2. **Biller User Management** — also explicitly deferred in the checkpoint and belongs to a later roadmap phase.
3. **Platform role consolidation / RBAC refactor** — checkpoint says no role consolidation or permission refactor was performed; the work is additive.
4. **Dedicated invitation lifecycle** — `AddStaffModal.jsx` says there is no separate pending-invite backend state yet.
5. **Security Monitoring / Workforce Analytics / Privileged Access Review** — `UserManagement.jsx` comments say those sections are deferred and intentionally not represented as complete.
6. **Dedicated service-account or API-client creation surface** — checkpoint says they are intentionally created through the shared Add Staff flow rather than separate pages/buttons.
7. **Post-platform phases from the roadmap** — Tenant Experience, Biller Experience, shared revenue oversight, and end-to-end field-testing readiness remain outside this recovery.

## What looks experimental or still in review

### 1. Standalone Audit Logs UX

Because the checkpoint says it was waiting on design review, but newer code exists, this looks like the most likely “implemented but not yet socially/UX approved” area.

### 2. Brand-shell redesign of the owner platform

- `OwnerShell.jsx`, new dark icon assets, and `BrandLogo.tsx` centralization clearly represent a visual redesign.
- The code is coherent, but there are no recovered frontend tests tied to this shell work.

This looks like polished implementation work, but still more “UI rollout candidate” than conclusively validated infrastructure.

### 3. Future-platform catalog entries

`backend/app/core/platforms.py` includes `SNS Home Health Solutions` and `SNS Scribe` even though its own docstring says only `SNS Hospice Solutions` is staffed today. That is deliberate and documented, but it is also forward-looking rather than immediately exercised business functionality.

## What looks closest to production-ready

Based on code structure plus dedicated backend tests, the most production-leaning recovered pieces are:

1. **Backend RBAC foundation** — `roles.py`, `role_guards.py`, `auth.py`.
2. **Platform-staff API enforcement** — owner-admin staff endpoints, especially role/status/remove/revoke/profile logic.
3. **Schema support** — `user.py` field extensions plus the five chained Alembic migrations.
4. **Delegated permission grants** — `staff_permission_grant.py` + grant/revoke endpoints + delegation tests.
5. **Set-password flow wiring** — `SetPasswordPage.tsx` plus `/set-password` route in `App.tsx`.

Why these look stronger than the rest: they are backed by explicit backend test files (`test_owner_platform_rbac_matrix.py`, `test_owner_platform_staff_profile.py`, `test_owner_platform_staff_lifecycle.py`, `test_owner_platform_staff_delegation.py`, `test_owner_audit_logs.py`) rather than only comments or UI code.

## Roadmap crosswalk

| Roadmap section | Recovered evidence |
|---|---|
| Platform Owner User Management | `owner_admin.py`, `UserManagement.jsx`, `OwnerDashboard.jsx`, `OwnerShell.jsx` |
| SNS Staff Profile | `user.py`, `AddStaffModal.jsx`, `StaffProfileDrawer.jsx`, profile tests |
| Department | `departments.py`, `users.department`, department filters/tests |
| Platform Role | `roles.py`, `update_platform_staff_role`, lifecycle tests |
| Access Level | `ACCESS_LEVEL_FOR_ROLE`, `accessLevels.js`, UI display in staff pages |
| Security Access | `PLATFORM_PERMISSION_MATRIX`, `require_platform_permission`, delegated grants |
| Audit History | `list_audit_logs`, `get_platform_staff_audit_history`, `AuditLogs.jsx`, `AuditEventDrawer.jsx`, audit tests |
| Service Accounts | `account_type`, `responsible_owner_id`, `identity_purpose`, service-account tests/UI tabs |
| API Identities | `identity_scope`, API-client filters/forms/tests |
| Platform Owner Safeguards | final-owner protections in `owner_admin.py` and lifecycle/delegation tests |

## Bottom line

The recovered work is not random unfinished experimentation; it is a coherent **Platform Owner / SNS Staff & Access** feature set spanning schema, RBAC, API, tests, routing, and owner UI. The backend enforcement and test coverage look the most complete. The biggest open question is not the RBAC core — it is the **owner audit standalone UX**, where recovered code exists but the checkpoint note still says the feature was awaiting design review.
