# SUPERADMIN Plan Traceability

**Document Status:** REFERENCE ONLY — superseded as the primary decision record by
`SUPERADMIN_OWNER_MODEL_DECISION.md` (the FINAL PRODUCT DECISION). Content is not contradicted by
that decision; retained for traceability detail (developer-account provisioning, login, and
session-expiration evidence).

Status: EVIDENCE-BASED, READ-ONLY INVESTIGATION (with two focused test additions — see
`SUPERADMIN_DEVELOPER_LOGIN_VALIDATION.md`)

Authoritative product decision (this session): **SUPERADMIN is the owner account for SNS Tech
Solutions.** It is not merely a "developer login" label and not a tenant hospice role. No file in
the repository uses the literal string `SUPERADMIN` (no underscore) as a canonical role. The
closest, and — after inspection — the actual, existing implementation of "the SNS Tech Solutions
owner account" is the `OWNER` role/account already defined in `app/core/roles.py` and provisioned
by `app/services/admin_bootstrap_service.py`.

## Repository-wide term search (raw counts, this session)

| Term | Occurrences (non-doc-history) | Notes |
|---|---|---|
| `SUPERADMIN` (no underscore) | 3 (frontend only) | `TenantDashboard.jsx` literal in an `ADMIN_SETTING_ROLES` array; `OwnerDashboard.jsx` fallback display label/message. Never issued by the backend as a role value — unreachable in practice. |
| `SUPER_ADMIN` | 3 (backend) + 1 (frontend) | `roles.py` `_ALIASES` (`SUPER_ADMIN -> ADMINISTRATOR`), `admin/chart_export.py` ad-hoc role set, `StaffAssignment.jsx` mirrors the same alias. Tenant-tier alias only, unrelated to the platform OWNER concept. |
| `SUPER ADMIN MODE` | 1 file (`tenant_orm_filters.py`) | Tenant-filter bypass keyed on `tenant_id is None`; never imported by the running app. Dead code. |
| `developer login` / `developer account` | 0 | Not a repository term prior to this session. |
| `platform administrator` | matches `PLATFORM_ADMIN` role only | Distinct, lower-tier platform staff role — not the SNS Tech Solutions owner. |
| `system administrator` | 0 | Not a repository term. |
| `owner platform` | many (docs) | `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md` and the `docs/owner-platform/*` specs — confirms "Owner Platform" is an SNS Tech Solutions platform, governed by the `OWNER` role. |
| `development access` | 0 | Not a repository term. |
| `seed_superadmin` / `create_superuser` | 0 | No such function exists. The actual mechanism is `provision_development_logins()` in `admin_bootstrap_service.py`. |
| `authority rank` | `docs/recovery/2026-09-15/RBAC_HIERARCHY_DECISION.md` | Discusses a *different, unrelated* low-privilege `PLATFORM_DEVELOPER` staff role (capability: `staff.view` only) — not the SNS Tech Solutions owner/SUPERADMIN concept. Must not be conflated. |
| `role aliases` | `app/core/roles.py::_ALIASES` | Canonical alias table; `SUPER_ADMIN -> ADMINISTRATOR` only. |
| `role capabilities` | `app/core/roles.py::PLATFORM_PERMISSION_MATRIX` | `OWNER` holds every `staff.*` capability unconditionally (`test_owner_has_every_staff_capability`). |
| `JWT claims` | `app/api/auth.py`, `app/core/security.py` | `sub`, `tenant_id`, `role`, `typ`, `jti`, `iss`, `aud`, `iat`, `exp`, `email` — verified live this session. |
| `tenant switching` / `tenant selection` | `app/api/owner_admin.py` (`GET /api/owner/tenants`) | OWNER lists all tenants (metadata/admin only); there is no "enter tenant as an agent" clinical-context switch for OWNER. |
| `developer console` / `developer diagnostics` | 0 | Not a repository term or feature. Classified NOT FOUND. |

## Required traceability table

| Requirement or plan item | Source file | Exact repository statement | Implementation location | Test evidence | Status |
|---|---|---|---|---|---|
| SUPERADMIN role definition | `app/core/roles.py` | `PLATFORM_ROLES = {"OWNER", ...}`; no `SUPERADMIN` entry anywhere | `OWNER` role is the canonical implementation of the SNS Tech Solutions owner account, per this session's product decision | `tests/test_owner_platform_rbac_matrix.py::test_owner_has_every_staff_capability` | IMPLEMENTED AND TESTED (as `OWNER`) |
| Developer account creation | `app/services/admin_bootstrap_service.py` | `DevelopmentIdentity(email_env="DEV_PLATFORM_OWNER_EMAIL", ..., full_name="SNS Tech Solutions", role="OWNER")` inside `provision_development_logins()` | Called unconditionally at real startup (`app/main.py`) and by `scripts/seed_login_accounts.py`; no-op unless env vars are set (no implicit secrets) | `tests/test_auth_hardening.py::test_provisioning_authentication_authorization_and_password_flows` | IMPLEMENTED AND TESTED |
| Developer login | `app/api/auth.py` `POST /auth/login` | Verifies password hash, issues JWT via `create_access_token` | Verified LIVE this session (200, correct `role`/`tenant_id` claims); invalid password correctly returns 401 | `test_auth_hardening.py` + live verification (this session) | IMPLEMENTED AND TESTED |
| JWT/session role claim | `app/api/auth.py`, `app/core/security.py` | JWT payload includes `role`, `tenant_id`, `sub`, `exp`, etc. | Verified live claims: `role=OWNER`, `tenant_id=<PLATFORM_TENANT_ID>` | `test_auth_hardening.py` | IMPLEMENTED AND TESTED |
| Platform administration | `app/api/owner_admin.py` (`/api/owner/*`), `src/owner/*` | `require_platform_permission("staff.view")`, `role_can()` ceiling checks | Verified live: `/api/owner/users`, `/api/owner/tenants`, `/api/owner/audit-logs` all return 200 for OWNER | `test_owner_platform_rbac_matrix.py`, `test_auth_hardening.py` | IMPLEMENTED AND TESTED |
| Tenant selection | `app/api/owner_admin.py` `GET /api/owner/tenants` | Owner Platform Rule: "The Owner Platform does NOT operate hospice agencies" (`SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`) | OWNER lists all tenants (admin metadata) but does not "enter" a tenant's clinical context | Verified live (8 tenants listed; no clinical-context switch exists) | IMPLEMENTED AND TESTED (matches documented "no clinical operation" intent) |
| Cross-tenant behavior | `app/core/middleware/clinical_access_guard.py` | `access_scope == "platform"` is denied any path outside `PLATFORM_ALLOWED_PREFIXES` | OWNER sees cross-tenant admin metadata but is blocked from `/patients` (PHI) with 403 | Verified live (`GET /patients` -> 403 "Clinical access is not permitted for this role"); `test_auth_hardening.py` | IMPLEMENTED AND TESTED |
| Developer navigation | `sns-emr-frontend/src/utils/authorization.ts`, `src/owner/*` | `hasRouteAccess(user, "owner") = access_scope === "platform"`; `getDefaultRoute` -> `/owner` | Verified live: login lands on `/owner` with Dashboard/Tenant Management/System Health/User Management/Audit Logs/Analytics/Billing & Licensing/Settings/AI Command Center | New: `sns-emr-frontend/src/utils/authorization.test.ts` (added this session) + live browser verification | IMPLEMENTED AND TESTED |
| Developer diagnostics | — | No occurrences of "developer diagnostics"/"developer console" anywhere in the repository | — | — | NOT FOUND |
| SUPER ADMIN MODE | `app/core/tenant_orm_filters.py`, `app/core/tenant_routing_middleware.py`, `app/main.py` | ORM bypass fires only when `get_current_tenant() is None`; its only setter (`TenantRoutingMiddleware`) is commented out in `main.py`; the module itself is never imported | Present in source, never registered, never reachable in the running app; unrelated to any role including OWNER | None (unreachable) | NOT FOUND (dead/unregistered code) |
| Audit logging | `app/api/auth.py`, `app/api/owner_admin.py` | `log_event(..., action="LOGIN_SUCCESS"/"LOGIN_FAILED"/"OWNER_CREATED_STAFF", ...)` | Verified: login endpoint always logs; owner-admin staff mutations always logs | `test_auth_hardening.py` (drives login attempts recorded in `audit_logs`) | IMPLEMENTED AND TESTED |
| Logout/session expiration | Frontend "Sign out" button; JWT `exp` claim | Stateless JWT with `exp` (verified 3600s lifetime); no server-side revocation/blacklist endpoint found | Frontend clears session client-side and redirects to `/login` | Verified live (Sign out -> `/login`) | PARTIAL (client-side logout works; no server-side token revocation exists — this is a pre-existing architectural characteristic of the whole JWT design, not specific to SUPERADMIN/OWNER, and out of this task's scope to change) |

## Critical distinction (must not be conflated)

- **`OWNER` role** (this session's SUPERADMIN) — the SNS Tech Solutions platform owner account.
  Fully implemented, live-verified, tested.
- **`SUPER_ADMIN` alias** (`roles.py::_ALIASES`) — an unrelated tenant-tier role-name alias that
  normalizes to `ADMINISTRATOR`. Has nothing to do with the platform owner.
- **"SUPER ADMIN MODE"** (`tenant_orm_filters.py`) — an unrelated, dead/unregistered tenant-filter
  bypass keyed on `tenant_id is None`. Not gated by any role name, not triggered by OWNER login,
  and not reachable by any live code path today.
- **`PLATFORM_DEVELOPER`** (`roles.py::PLATFORM_ROLES`) — an unrelated, minimally-privileged
  internal platform-staff role (`staff.view` only), discussed in
  `docs/recovery/2026-09-15/RBAC_HIERARCHY_DECISION.md`. Not the SNS Tech Solutions owner account.
