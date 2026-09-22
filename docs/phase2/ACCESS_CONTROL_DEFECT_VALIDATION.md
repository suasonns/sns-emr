# Access Control Defect Validation

**Document Status:** COMPLETE — all 3 defects (AC-001, AC-002, AC-003) REMEDIATED and verified.

Purpose: single source-of-truth evidence record for AC-001, AC-002,
AC-003 — pre-remediation defect confirmation and post-remediation
verification. Consolidates evidence previously distributed across
`ACCESS_CONTROL_DEFECT_REACHABILITY.md` with the remediation outcome
now recorded alongside it.

| ID | File / Function | Pre-remediation defect | Reachability evidence | Test evidence (pre) | Classification (pre) | Remediation applied | Test evidence (post) | Status |
|----|------------------|------------------------|------------------------|----------------------|------------------------|----------------------|------------------------|--------|
| AC-001 | `backend/app/core/permissions.py::has_permission()` | Unconditionally returned `True` for any role/action | 5 live call sites in `backend/app/api/survey.py` (`download_chart_pdf`, `view_compliance`, `export_data` actions), router confirmed mounted in `backend/app/api/registry.py`, no other auth check on these routes | `test_adr_audit_policy.py` and pre-existing suite never exercised this function; zero direct test coverage | ACTIVE DEFECT | Delegates to `has_capability(role, VIEW_ALL_TENANT_PATIENTS)` for the 3 known actions; deny-by-default otherwise | `test_ac001_survey_permission_enforcement.py`: 403 for `RN`, 401 unauthenticated, non-403 for `ADMINISTRATOR` across all 5 routes — all pass | REMEDIATED |
| AC-002 | `backend/app/api/audit_dashboard.py:85` | Gate listed literal `"QA"`, which does not match any issued role (`QA_MANAGER`/`QA_REVIEWER`/`COMPLIANCE_OFFICER` per `app.core.roles`) | Confirmed via direct trace of `normalize_role()`/`role_matches()`/`_ALIASES`/`QA_ROLES` in `roles.py`; only 2 repo-wide literal `"QA"` occurrences, one being this gate | No test previously asserted QA-role access to this route | ACTIVE DEFECT (functional denial, not an intrusion path) | `require_roles(["ADMIN", "DPCS", *sorted(QA_ROLES)])` | `test_ac002_audit_dashboard_qa_role.py`: `QA_MANAGER`/`QA_REVIEWER`/`COMPLIANCE_OFFICER`/`ADMIN`/`DPCS` pass, `RN`/unauthenticated denied, regression-guard confirms no literal `"QA"` remains in the gate — all pass | REMEDIATED |
| AC-003 | `backend/app/api/adr_exports.py::export_adr` | Zero authentication, authorization, or tenant-ownership check on `patient_id`; no audit logging | Confirmed via direct code read: no `Depends(...)` auth dependency present, `req.patient_id` used as-is; router confirmed mounted in `registry.py`; no frontend caller found (grep), no UI/API guard elsewhere; existing `test_adr_audit_policy.py` only unit-tests `AdrAuditService`, never the HTTP route | No test previously exercised the route's auth/tenant behavior | ACTIVE DEFECT | Added `Depends(require_capability(VIEW_ALL_TENANT_PATIENTS))`; bound `patient_id` via `get_authorized_patient(db, patient_uuid, user)` (404 on cross-tenant/nonexistent); added `log_event()` call for `ADR_EXPORT`. Also fixed a co-located, previously-undiscovered defect: `run_full_audit()` was called with positional args against a keyword-only signature, causing a `TypeError` on every prior invocation | `test_ac003_adr_export_protection.py`: 401 unauthenticated, 403 wrong role, 200 + PDF for authorized same-tenant, 404 cross-tenant, 404 nonexistent/malformed id, audit row written — all pass | REMEDIATED |

## Runtime verification method

All "Test evidence (post)" results were obtained by executing the
named test files against a real, isolated Postgres database via
`python scripts\run_isolated_tests.py -- <args>` (the repository's
documented isolated-test procedure — spins up a per-run database and
applies all Alembic migrations), not by static inference. Exact
pass/fail counts and exit codes for each run are recorded in
`docs/phase2/ACCESS_CONTROL_DEFECT_REMEDIATION.md`'s "Test Results"
section.

## Unverified items (explicitly out of scope, unchanged by this remediation)

- Three `/survey/*` routes remain unable to return 200 due to missing
  SQL views not created by any migration (pre-existing, undocumented
  before this session, unrelated to authorization).
- `/survey/export-bundle` has a separate, pre-existing
  `log_security_activity()` keyword-argument bug unrelated to
  authorization.
- `require_permission()` stub in `permissions.py` (unused, no call
  sites) — left untouched.
- `security/deps.py` dev-only no-auth stub — left untouched.
- Duplicate `CurrentUser` implementations across `core/auth.py` and
  `core/security.py` — documented, not consolidated (out of authorized
  scope; no RBAC/authority redesign was authorized).

## Decision

Both required decision axes from the governing review are resolved:

- **New-abstraction need:** NOT NEEDED. All three fixes reuse existing,
  already-adopted mechanisms (`has_capability`, `QA_ROLES`,
  `get_authorized_patient`, `log_event`). No new permission model,
  role, or authority abstraction was introduced.
- **Implementation action:** COMPLETE. All three defects are
  remediated and verified by passing, newly-added tests plus a clean
  broader-suite and full-suite regression run (full-suite failures are
  pre-existing and unrelated — see
  `ACCESS_CONTROL_DEFECT_REMEDIATION.md`).

## ACP terminology confirmation

ACP = Advance Care Planning throughout. No content in this document or
the remediation work treats ACP as "Access Control Policy."
