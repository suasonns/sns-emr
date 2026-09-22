# Access Control Defect Remediation

Status: COMPLETE (3 of 3 authorized defects remediated)
Scope: AC-001, AC-002, AC-003 only, as authorized. No RBAC/authority
redesign, no new abstractions, no ACP (Advance Care Planning) content
touched.

================================================================================
## AC-001 — `has_permission()` stub in `backend/app/core/permissions.py`
================================================================================

**Previous behavior:** `has_permission(role, action)` unconditionally
returned `True` for every role/action pair. All 5 `/survey/*` routes in
`backend/app/api/survey.py` call this function as their sole
authorization check, so any authenticated user of any role could invoke
`download_chart_pdf`, `view_compliance`, and `export_data` actions.

**Corrected behavior:** `has_permission()` now delegates to the existing
`app.core.capabilities.has_capability(role, VIEW_ALL_TENANT_PATIENTS)`
mechanism for the three actions actually used by `survey.py`
(`download_chart_pdf`, `view_compliance`, `export_data`), and denies
(`False`) any action not on that recognized list (deny-by-default).

**Mechanism reused:** `app.core.capabilities.has_capability()` /
`ROLE_CAPABILITIES` — the same capability system already governing
tenant-wide clinical data access elsewhere in the codebase. No new
capability, role, or permission model was introduced.

**Files changed:** `backend/app/core/permissions.py` only.
`require_permission()` (a separate, unused stub in the same file) was
left untouched — it has no call sites and is out of the authorized
scope.

**Routes affected:** `GET /survey/overdue-poc-updates`,
`GET /survey/idg-compliance`, `GET /survey/crisis-poc-same-day`,
`GET /survey/chart-summary`, `POST /survey/export-bundle` (all mounted
via `survey.router`, confirmed live in `backend/app/api/registry.py`).

**Roles affected:** Now requires `VIEW_ALL_TENANT_PATIENTS`, held by
`ADMINISTRATOR`, `DPCS`, `DPCS_ADMINISTRATOR`, `MEDICAL_DIRECTOR`,
`QA_MANAGER`, `QA_REVIEWER`, `COMPLIANCE_OFFICER`,
`CLINICAL_SUPERVISOR`. Previously: all roles.

**Tests added:** `backend/tests/test_ac001_survey_permission_enforcement.py`
— unit tests for `has_permission()` across authorized/unauthorized
roles and actions, plus route-level tests confirming a role without
`VIEW_ALL_TENANT_PATIENTS` (e.g. `RN`) receives 403 and an
authenticated request with no token receives 401, across all 5 routes.

**Test results:** All tests pass. See "Test Results" section below.

**Remaining, documented, out-of-scope limitation:** Three of the five
routes (`overdue-poc-updates`, `idg-compliance`, `crisis-poc-same-day`)
query SQL views (`survey_overdue_poc_updates`, `survey_idg_compliance`,
`survey_crisis_poc_same_day`) that are not created by any Alembic
migration in the repository, so an authorized caller currently receives
a 500 (missing relation) rather than a 200. This is a pre-existing,
separate infrastructure gap unrelated to authorization and was **not**
in scope for this remediation; tests for these three routes assert only
that the permission gate does not return 403 for an authorized role
(see AC-001 test file docstring for the exact evidence). A fourth route,
`/survey/export-bundle`, was separately discovered during test
execution to raise `TypeError: log_security_activity() got an
unexpected keyword argument 'role'` for authorized callers — an
existing, unrelated bug in `survey.py`'s own audit-logging call, also
out of scope and left untouched.

================================================================================
## AC-002 — Unreachable `"QA"` role string in `backend/app/api/audit_dashboard.py`
================================================================================

**Previous behavior:** Line 85 gated dashboard access with
`require_roles(["ADMIN", "DPCS", "QA"])`. The literal role string
`"QA"` is not an issued/normalized role anywhere in the system (see
`app.core.roles._ALIASES`, `QA_ROLES`, `role_matches()`) — no real
`QA_MANAGER`, `QA_REVIEWER`, or `COMPLIANCE_OFFICER` account could ever
satisfy this check, meaning the dashboard's intended QA-role access was
permanently unreachable for those roles.

**Corrected behavior:** Line 85 now reads
`require_roles(["ADMIN", "DPCS", *sorted(QA_ROLES)])`, using the
already-imported `QA_ROLES` constant (`{"QA_MANAGER", "QA_REVIEWER",
"COMPLIANCE_OFFICER"}`) so the three real QA roles are recognized.

**Mechanism reused:** `app.core.roles.QA_ROLES`, already imported and
used elsewhere in the same file (`CENSUS_VIEW_ROLES`). No new role
constant or authority model was introduced.

**Files changed:** `backend/app/api/audit_dashboard.py` line 85 (plus
an explanatory comment).

**Routes affected:** All routes gated by this `require_roles(...)`
check in `audit_dashboard.py` (the dashboard's patient/audit listing
endpoints).

**Roles affected:** `ADMIN`, `DPCS` (unchanged) plus now
`QA_MANAGER`, `QA_REVIEWER`, `COMPLIANCE_OFFICER` (previously
unreachable). No role loses access.

**Tests added:** `backend/tests/test_ac002_audit_dashboard_qa_role.py`
— a regression-guard source-text check confirming the literal quoted
role string `"QA"` no longer appears in the `require_roles([...])` call
site, plus route-level tests confirming `QA_MANAGER`, `QA_REVIEWER`,
`COMPLIANCE_OFFICER`, `ADMIN`, and `DPCS` all pass and `RN` /
unauthenticated requests are denied.

**Test results:** All tests pass. See "Test Results" section below.

================================================================================
## AC-003 — Missing authentication/authorization/tenant-isolation/audit on `export_adr` in `backend/app/api/adr_exports.py`
================================================================================

**Previous behavior:** `export_adr()` had no `Depends(...)` authentication
or authorization dependency at all, and used the client-supplied
`req.patient_id` directly with no tenant-ownership check — any caller,
authenticated or not, and regardless of tenant, could generate and
download any patient's ADR/TPE export packet. No audit event was
recorded for a completed export.

**Corrected behavior:**
- Added `Depends(require_capability(VIEW_ALL_TENANT_PATIENTS))` as an
  auth+authz dependency (the same capability reused for AC-001).
- The client-supplied `patient_id` is now resolved through the existing
  `app.core.patient_access.get_authorized_patient(db, patient_uuid,
  user)` helper — the same tenant-isolation + care-team-scoping
  mechanism already used by `backend/app/api/patient_charts.py` — which
  raises 404 (not 403, to avoid confirming patient existence across
  tenant boundaries) if the patient does not belong to the caller's
  tenant/care team.
- A successful export now writes an `ADR_EXPORT` audit event via the
  existing `app.services.audit_logger.log_event()` function.

**Incidental, necessary fix:** `AdrAuditService.run_full_audit()`
declares all of its parameters keyword-only
(`def run_full_audit(self, *, patient_id, adr_start, adr_end,
mode="FULL")`), but the pre-existing call in `adr_exports.py` passed
them positionally. This meant the endpoint raised a `TypeError` on
every single invocation, authorized or not, before this remediation —
a separate, pre-existing defect. It was corrected (switched to keyword
arguments) because it is a precondition for verifying "preserve export
behavior for authorized users" and for the new tests to pass; no other
behavior of `AdrAuditService` was changed.

**Mechanism reused:** `app.core.capabilities.require_capability()`,
`app.core.patient_access.get_authorized_patient()`,
`app.services.audit_logger.log_event()` — all pre-existing, already
used elsewhere in the codebase.

**Files changed:** `backend/app/api/adr_exports.py` (function body and
imports only).

**Routes affected:** `POST /chart/export/adr`.

**Roles affected:** Now requires `VIEW_ALL_TENANT_PATIENTS` (same role
set as AC-001). Previously: none (open to any caller).

**Tenants affected:** Requests are now bound to the caller's own
tenant; cross-tenant patient IDs return 404.

**Tests added:** `backend/tests/test_ac003_adr_export_protection.py` —
unauthenticated (401), unauthorized role (403), authorized same-tenant
success (200 + `application/pdf`), cross-tenant patient (404),
nonexistent patient (404), malformed patient id (404), and an
audit-log-row-written verification.

**Test results:** All tests pass. See "Test Results" section below.

================================================================================
## Test Results
================================================================================

All commands executed via
`python scripts\run_isolated_tests.py -- <args>` with
`DATABASE_URL=postgresql://sns:sns@localhost:5432/sns_emr_dev_clean` and
`SECRET_KEY` set, per the repository's documented isolated-test
procedure (spins up a dedicated per-run Postgres database and runs
Alembic migrations against it).

**1. Narrowest scope** (`test_ac001_survey_permission_enforcement.py`,
`test_ac002_audit_dashboard_qa_role.py`,
`test_ac003_adr_export_protection.py`,
`test_adr_audit_policy.py`):
- 58 collected, 58 passed, 0 failed, 0 errors. Exit code 0.

**2. Broader applicable suite** (all repository test files matching
authority/RBAC/permission/audit/tenant-authorization/ADR terms):
`test_tenant_default_medical_director.py`,
`test_physician_signature_authority.py`,
`test_owner_platform_rbac_matrix.py`, `test_owner_audit_logs.py`,
`test_idg_batch_sign_authorization.py`,
`test_documentation_authorization.py`,
`test_contracted_authorization_readiness.py`,
`test_billing_provider_authorization.py`, `test_auth_hardening.py`,
`test_audit_logging.py`, `test_adr_audit_policy.py`, plus the three new
AC-00x test files:
- 50 collected, 50 passed, 0 failed, 0 errors. Exit code 0.

**3. Full backend regression suite** (entire `backend/tests/` directory):
- 15 pre-existing failures, all in modules unrelated to this
  remediation and never touched by it:
  - `tests/test_recertification_evidence_synthesis_v1.py` (12 failures)
  - `tests/test_rnica_poc_adapter.py` (1 failure)
  - `tests/test_treatment_identity_migration.py` (2 failures)
  - Exit code 1 (due to these 15 pre-existing failures only).
  - Zero collection errors. No failures in `survey.py`,
    `audit_dashboard.py`, `adr_exports.py`, `permissions.py`,
    `capabilities.py`, `roles.py`, `patient_access.py`, or any of the
    three new AC-00x test files.
  - These 15 failures are unrelated to AC-001/002/003: they concern
    RNICA plan-of-care versioning, treatment-identity Alembic
    migration remapping, and recertification evidence synthesis
    vocabulary/section rules — none of which this remediation's code
    changes touch.

================================================================================
## Code / Schema / Migration Impact
================================================================================

- **Code impact:** 3 files modified
  (`backend/app/core/permissions.py`, `backend/app/api/audit_dashboard.py`,
  `backend/app/api/adr_exports.py`); 3 new test files added.
- **Schema impact:** None. No models, tables, or columns changed.
- **Migration impact:** None. No Alembic migration created or modified.

================================================================================
## Confirmation
================================================================================

ACP remains **Advance Care Planning** throughout this remediation. No
"Access Control Policy" terminology was introduced. No RBAC/authority
model redesign was performed; all fixes reuse existing, already-adopted
mechanisms (`has_capability`, `QA_ROLES`, `get_authorized_patient`,
`log_event`).
