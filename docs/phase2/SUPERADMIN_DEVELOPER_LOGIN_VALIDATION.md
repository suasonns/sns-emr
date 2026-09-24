# SUPERADMIN Developer Login Validation

**Document Status:** SUPERSEDED — superseded by `SUPERADMIN_OWNER_MODEL_DECISION.md` and the
FINAL PRODUCT DECISION (SUPERADMIN = SNS Tech Solutions Platform Owner; OWNER = canonical
implementation role). The developer-login evidence below is not contradicted, but this document is
no longer the primary decision record. Retained for historical traceability only.

## 1. Authoritative product decision

SUPERADMIN is the owner account for SNS Tech Solutions (the platform vendor). It is not merely a
developer login and not a tenant hospice role. Developer capabilities, Owner Platform authority,
tenant access, patient-data boundaries, and "Super Admin Mode" were each verified separately
against the repository, per instruction. No assumption of "working," "missing," or "unrestricted
clinical access" was made in advance — see evidence below.

## 2. Repository plan sources

See `docs/phase2/SUPERADMIN_PLAN_TRACEABILITY.md` for the full term search and traceability table.
Summary: no document or code anywhere uses the literal string `SUPERADMIN` as a canonical role.
The existing, already-implemented mechanism that matches "the SNS Tech Solutions owner account" is
the `OWNER` role, defined in `app/core/roles.py::PLATFORM_ROLES` and provisioned via
`app/services/admin_bootstrap_service.py::provision_development_logins()` (identity: `full_name="SNS
Tech Solutions"`, `role="OWNER"`, env-driven, no implicit secrets). `docs/architecture/
SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md` (LOCKED) independently confirms the "Owner Platform"
belongs to SNS Tech Solutions and "does NOT operate hospice agencies."

## 3. Role definition

- Canonical role string: `OWNER` (`app/core/roles.py::PLATFORM_ROLES`).
- Authority rank: tier 1 (`ACCESS_LEVEL_FOR_ROLE`), above `PLATFORM_ADMIN` (tier 2).
- Capabilities: unconditional access to every `staff.*` capability in
  `PLATFORM_PERMISSION_MATRIX` (verified by the existing
  `test_owner_has_every_staff_capability`).
- Normalization: `OWNER` requires no alias — it is already canonical. (`SUPER_ADMIN`, by contrast,
  normalizes to `ADMINISTRATOR`, an unrelated *tenant*-tier role — this is a distinct, pre-existing
  fact and not something this task changed.)
- Authentication claim format: JWT `role` claim is the raw DB value (`OWNER`), checked by
  `core.security.get_current_user`/`require_capability` (no `VALID_ROLES` allow-list) for
  capability-gated routes, and by `core.auth.get_current_user` (`VALID_ROLES` allow-list, which
  does include `OWNER`) for routes using that dependency directly.
- Frontend interpretation: `access_scope` claim (`"platform"` for OWNER) drives
  `hasRouteAccess`/`getDefaultRoute` in `sns-emr-frontend/src/utils/authorization.ts`.
- Tenant implications: OWNER's `tenant_id` is the fixed `PLATFORM_TENANT_ID`
  (`cccccccc-cccc-cccc-cccc-cccccccccccc`), not a hospice tenant.
- Can SUPERADMIN/OWNER be assigned through normal tenant role management? No — `POST
  /api/owner/users` (`create_platform_staff`) validates `payload.role` against `PLATFORM_ROLES`
  and requires `staff.assign_owner_role` (OWNER-only) to create another OWNER; tenant-scoped staff
  endpoints (`app/api/staff.py`) operate on a completely separate, tenant-scoped role set and
  cannot issue `OWNER`.

No new role was created. `OWNER` is the pre-existing canonical role and was used as-is.

## 4. Developer (OWNER) account status

- **An OWNER account for SNS Tech Solutions already exists and is active** in the current
  development database (`sns_emr_dev_clean`): `tenant_id = PLATFORM_TENANT_ID`, `active = true`,
  `account_type = HUMAN_STAFF`. (User ID, login identifier, and password are intentionally not
  reproduced in this document.)
- A second `OWNER` row exists but is **inactive** (`active = false`) and tenant-bound to a
  non-platform test tenant (`@example.test` domain) — this is an inert historical/test row, not a
  duplicate live account.
- No duplicate *active* platform-tenant OWNER accounts exist.
- Account creation source: `provision_development_logins()` (`admin_bootstrap_service.py`),
  triggered by `DEV_PLATFORM_OWNER_EMAIL`/`DEV_PLATFORM_OWNER_PASSWORD` in `backend/dev.env`
  (local, gitignored — see commit "Ignore local dev.env files containing plaintext credentials").
- The account authenticates successfully (verified live in Section 5).

No account was created or modified by this task. No credentials are reproduced above, in any
other document, or in any test file added by this task.

## 4a. System startup (restoring the established local path)

Per `docs/PHASE0_STARTUP_PROCEDURE.md`, the browser's `localhost:5173` connection-refused state was
caused by both dev servers being stopped (no node/python processes running) plus a genuine,
pre-existing, already-documented blocker: the dev database's Alembic revision
(`um2d1c2c3o5u9`) was behind the code's migration head (`f7a8b9c0d1e2`) — the backend's
`assert_alembic_in_sync()` startup guard refused to start (exit code 3) until this was resolved.

This is exactly the "direct startup regression" the instruction authorized fixing: `alembic
upgrade head` was run against `sns_emr_dev_clean` (schema/data migration only — no new migration
files were created, no schema was redesigned). The environment was not otherwise redesigned.

Verified after the fix:

| Check | Result |
|---|---|
| Canonical database reachable | YES (`sns_emr_dev_clean`) |
| Migrations at current head | YES (`alembic current` = `f7a8b9c0d1e2 (head)`) |
| Backend reachable | YES (`http://127.0.0.1:8000`, `Application startup complete.`) |
| Frontend reachable | YES (`http://127.0.0.1:5173`, Vite ready) |
| Login page reachable | YES (`GET /login` renders Email/Password/Sign in) |
| Authentication endpoint reachable | YES (`POST /auth/login` -> 200 for valid credentials) |
| Current-user endpoint reachable | YES (`GET /auth/me` -> 200) |

## 5. Login flow (live-verified, not source inspection)

Verified two ways this session: (a) direct HTTP requests to the running backend, and (b) an actual
browser UI login/logout against the running frontend.

| Item | Result |
|---|---|
| Authentication endpoint | `POST /auth/login` |
| Response status (valid credentials) | 200 |
| Response status (invalid password) | 401 |
| Session/token type | Bearer JWT (`token_type: bearer`) |
| Issued role | `OWNER` |
| Issued tenant claim | `PLATFORM_TENANT_ID` (`cccccccc-...-cccccccccccc`) |
| Issued capabilities | Not embedded in the JWT — resolved server-side per request via
  `role_can()`/`PLATFORM_PERMISSION_MATRIX` (existing, pre-established architecture) |
| Current-user result (`GET /auth/me`) | 200; `role: OWNER`, `access_scope: platform`, matches JWT |
| Landing page (browser) | `/owner` (Owner Platform dashboard) |
| Visible navigation (browser) | Dashboard, Tenant Management, System Health, User Management, Audit Logs, Analytics, Billing & Licensing, Settings, AI Command Center, Sign out |
| Protected navigation | All the above required an authenticated OWNER session; unauthenticated `/owner` is not reachable (redirects to `/login`, per `authorization.ts`) |
| Logout result | Clicking "Sign out" returned the browser to `/login` |
| Invalid-credential result | `POST /auth/login` with wrong password -> 401, no token issued |
| Disabled-account result | Not live-tested (would require disabling the live account, out of scope); the second, inactive OWNER row in the DB was not exercised to avoid touching account state beyond this task's authorization |

No password, JWT, or other reusable token is reproduced in this document.

## 6. Developer (OWNER) access verification

| Area | Repository requirement | Actual behavior | Result |
|---|---|---|---|
| Platform administration | `require_platform_permission`/`role_can()` gate `/api/owner/*` | `GET /api/owner/users` -> 200 | PASS |
| Owner Platform access | Frontend `/owner` gated by `access_scope === "platform"` | Live login landed on `/owner` with full shell | PASS |
| Tenant listing | `GET /api/owner/tenants` | 200; lists all tenants (metadata) | PASS |
| Tenant selection | Owner Platform "does NOT operate hospice agencies" (documented rule) | No clinical tenant-context switch exists for OWNER; none is intended | NOT APPLICABLE (matches documented intent) |
| Tenant switching | Same as above | Same as above | NOT APPLICABLE |
| User administration | `/api/owner/users` (staff CRUD, `staff.*` capabilities) | 200; OWNER has every `staff.*` capability | PASS |
| Role administration | `role_can()` ceiling: only OWNER may assign/mutate another OWNER | Verified by existing `test_no_non_owner_role_can_ever_assign_owner_role` | PASS |
| Configuration access | `/owner/pages/Settings.jsx`, backend `/api/owner/*` settings routes | Reachable from the live OWNER session's navigation | PASS |
| Audit-log access | `GET /api/owner/audit-logs` | 200 | PASS |
| Developer diagnostics | No such feature exists anywhere in the repository | — | NOT APPLICABLE (feature does not exist; not part of the approved plan) |
| Frontend navigation | `hasRouteAccess`/`getDefaultRoute` (`authorization.ts`) | Verified live + new unit tests | PASS |
| Backend endpoints | `/api/owner/*` (allow), `/patients` (deny) | `GET /patients` -> 403 "Clinical access is not permitted for this role" | PASS (correctly denied — OWNER does not get blanket clinical access) |
| SUPER ADMIN MODE | `tenant_orm_filters.py` | Never imported by the running app; only trigger path is commented out | NOT APPLICABLE / NOT FOUND (see Section 8) |

Routine tenant role denial was also verified live: a `DPCS_ADMINISTRATOR` account received 403 on
both `/api/owner/users` and `/api/owner/tenants`.

## 7. Tenant and patient boundaries

- OWNER operates globally (`tenant_id = PLATFORM_TENANT_ID`), without selecting a hospice tenant.
- OWNER does **not** assume a hospice tenant's clinical context, does **not** switch into a
  tenant's patient data, and does **not** require an explicit "developer mode" activation step —
  there is no such step in the repository.
- OWNER **is** subject to normal patient authorization: `clinical_access_guard` middleware blocks
  any `access_scope == "platform"` role (including OWNER) from clinical routes not in its allow-list
  (verified live: `GET /patients` -> 403).
- No blanket bypass exists or was introduced. No tenant isolation was weakened. This matches the
  repository's existing, documented intent ("Owner Platform... does NOT operate hospice
  agencies") — this is **not** a `PRODUCT DECISION REQUIRED` item; the existing behavior already
  matches the stated product intent.
- OWNER's cross-tenant *administrative* visibility (tenant list, staff, audit logs) is intentional
  and already correctly scoped away from PHI.

## 8. SUPER ADMIN MODE

Search performed for the actual implementation and trigger (`app/core/tenant_orm_filters.py`,
`app/core/tenant_context.py`, `app/core/tenant_routing_middleware.py`, `app/main.py`):

- **Exists in source**: yes, as an ORM `do_orm_execute`/`before_flush` event-listener pair that
  bypasses tenant filtering when `get_current_tenant()` returns `None`.
- **Trigger condition**: `tenant_id is None` in a `ContextVar` — entirely unrelated to any role,
  including OWNER/SUPERADMIN.
- **Backend enforcement**: the module is never imported anywhere in `app/`, so its
  `@event.listens_for` decorators never attach to any live SQLAlchemy `Session`.
- **Frontend behavior**: none found; no UI concept of "Super Admin Mode" exists as an activatable
  feature (the two stray `SUPER ADMIN`/`SUPERADMIN` frontend strings found are a dead literal in an
  unrelated tenant-dashboard admin-settings array and a display-label fallback — see
  `SUPERADMIN_PLAN_TRACEABILITY.md`).
- **Role requirement**: none (by design it is role-agnostic; in practice, unreachable).
- **Tenant-context effect / permission effect**: would be a global bypass of tenant filtering if
  ever reachable, but it is not reachable.
- **Activation/deactivation event**: none — the only code path that ever calls
  `set_current_tenant()` with a non-`None` value (`TenantRoutingMiddleware`) is commented out in
  `app/main.py`.
- **Audit event**: only a `logger.warning()` inside the (unreachable) module — no `audit_logs` row.
- **Test coverage**: none found.

**Classification: NOT FOUND** — dead/unregistered code, unreachable via any live path in the
running application. It is not part of the OWNER/SUPERADMIN login and does not affect it in any
way, positively or negatively.

Per the remediation rules ("Do not implement a blanket bypass... do not weaken tenant isolation"),
this task does **not** complete, wire up, or re-enable this module. Re-enabling a global
tenant-filter bypass is exactly the kind of "new universal bypass" the instructions prohibit
without separate evidence and authorization. No action was taken on this module.

## 9. Frontend wiring

Traced: `LoginPage.tsx` (login form) -> backend `/auth/login` -> token stored (session module) ->
`/auth/me` loads current user -> `access_scope`/`role` parsed -> `authorization.ts`
(`hasRouteAccess`/`getDefaultRoute`/`canAccessPath`) gates `/owner` -> Owner Platform shell renders
navigation -> "Sign out" clears session and returns to `/login`.

Frontend checks match backend authority: `access_scope === "platform"` (frontend) corresponds
exactly to the backend's `access_scope_for_role(role) == "platform"` used by
`clinical_access_guard` and `owner_admin.py`'s dependencies. Frontend visibility is not treated as
a substitute for backend enforcement — every capability tested above is backend-enforced
independently of the UI (verified via direct HTTP calls, not just UI navigation).

**Tests added this session**: `sns-emr-frontend/src/utils/authorization.test.ts` — 4 focused unit
tests: OWNER routed to `/owner`, a tenant role excluded from `/owner`, a billing-scoped role
excluded from `/owner`, and an unauthenticated session excluded from `/owner`. All 4 pass.

Gap (documented, not fixed — out of scope as a UI/E2E addition): no existing frontend
component/integration test exercises the live login form or the owner navigation shell directly
(only the pure `authorization.ts` logic is now unit-tested); the login/navigation/logout flow was
instead verified live via direct browser interaction in this session, which is stronger runtime
evidence than a mocked component test but is not itself a checked-in regression test.

## 10. Backend wiring

Traced: `POST /auth/login` (`app/api/auth.py`) -> password verification (`core.security`) ->
`log_event(action="LOGIN_SUCCESS"/"LOGIN_FAILED")` -> JWT issuance (`create_access_token`) ->
`GET /auth/me` (`core.security.get_current_user`) -> role/capability resolution
(`role_can()`/`PLATFORM_PERMISSION_MATRIX`) -> `require_platform_permission()` guards on
`/api/owner/*` -> `clinical_access_guard` middleware enforces the platform/tenant/billing
route-prefix boundary on every request.

**Tests already existing and re-run this session (all pass)**:
`tests/test_auth_hardening.py::test_provisioning_authentication_authorization_and_password_flows`
(valid OWNER login, `/auth/me` identity, OWNER allowed on `/api/owner/tenants`, OWNER denied on
`/patients/`, `/api/dashboard/tenant`, `/api/dashboard/billing`, `/api/dashboard/claim-lifecycle`;
a tenant role denied `/api/owner/tenants`; password change/reset flows; audit-log-referencing
cleanup) and the 21-test `tests/test_owner_platform_rbac_matrix.py` suite (OWNER has every staff
capability, no non-OWNER role can ever assign/mutate an OWNER, unknown role/capability denied,
etc.). No new backend test was needed — this exact matrix was already covered.

No hardcoded bypass for one account was added or found.

## 11. Remediation performed

**None required for backend or login-flow correctness** — the SNS Tech Solutions owner
(SUPERADMIN) login, JWT claims, role resolution, platform-admin access, and tenant/patient
boundary enforcement are already correctly implemented and already covered by an existing,
passing test suite (`test_auth_hardening.py`, `test_owner_platform_rbac_matrix.py`).

**One test-coverage gap closed** (allowed under "adding tests"): added
`sns-emr-frontend/src/utils/authorization.test.ts` (4 tests, all passing) covering
SUPERADMIN/OWNER frontend routing, which had zero prior unit-test coverage.

**Startup regression fixed** (allowed under "fix only the startup regression necessary for this
verification"): ran `alembic upgrade head` against the dev database to resolve the pre-existing,
already-documented schema drift that prevented the backend from starting. No new migration was
created; no schema was changed beyond applying already-committed migrations.

No new authentication architecture, RBAC hierarchy, tenant model, universal bypass, schema change,
or credential hardcoding was introduced.

## 12. Unresolved / not implemented (explicitly out of scope for this task)

- **SUPER ADMIN MODE remains dead/unregistered code.** Whether to ever complete or delete it is a
  separate decision requiring its own authorization (re-enabling it would be a "new universal
  bypass" per the remediation rules).
- **Server-side session/token revocation** does not exist (stateless JWT with `exp` only); this is
  a pre-existing, repository-wide characteristic, not specific to OWNER/SUPERADMIN.
- **Disabled-account login behavior** was not live-tested (would require deactivating the live
  account).
- **No dedicated frontend E2E/integration test** exists for the login form or the owner navigation
  shell as rendered components (verified live via direct browser interaction instead).
- The two stray frontend string literals (`SUPERADMIN` in `TenantDashboard.jsx`'s
  `ADMIN_SETTING_ROLES`, and the `OwnerDashboard.jsx` fallback label/message) are harmless,
  unreachable dead code (no backend role is ever literally `SUPERADMIN`) — left unchanged as an
  unrelated-refactor concern, documented here for visibility.

No item above is silently included in the "developer login is proven operational" conclusion.

## 13. Completion criteria

- [x] Existing plan traced to implementation
- [x] Canonical SUPERADMIN role identified (`OWNER`)
- [x] Developer account exists and is enabled
- [x] Login succeeds
- [x] Invalid credentials fail
- [x] Canonical role is issued
- [x] Current-user endpoint returns correct role
- [x] Developer backend routes work
- [x] Routine tenant roles cannot use developer routes
- [x] Frontend developer navigation works
- [x] Tenant behavior matches the existing plan
- [x] Privileged actions are audited
- [x] SUPER ADMIN MODE is implemented or explicitly classified (classified: NOT FOUND, dead code)
- [x] Focused tests pass (`authorization.test.ts` — new; `test_auth_hardening.py`,
      `test_owner_platform_rbac_matrix.py` — pre-existing, re-run and passing)
- [x] Broader auth/RBAC/tenant/audit tests pass (both files above, 22 tests total, 0 failures)
- [x] No credential is committed (dev.env is gitignored; no password reproduced anywhere in this
      task's output or files)
- [x] No blanket authorization bypass is introduced
- [x] Documentation reflects actual behavior

## 14. Final decision matrix

**VERIFIED COMPLETE**

All applicable completion criteria pass, the existing OWNER/SNS-Tech-Solutions-owner
implementation was traced end to end (role definition -> account -> login -> JWT -> current-user
-> backend authorization -> frontend navigation -> logout -> audit logging), and it was verified
live (both direct HTTP and an actual browser session), not merely inspected from source. The one
genuine gap found (missing frontend unit-test coverage for routing logic) was closed within the
"adding tests" remediation allowance. SUPER ADMIN MODE — a separate, unrelated concept — was
explicitly classified as NOT FOUND (dead/unregistered code) rather than left ambiguous, and was
not touched, per the "do not implement a blanket bypass" rule.
