# SUPERADMIN / SNS Tech Solutions Owner Account — Implementation & Validation

**Document Status:** VALIDATED / CLOSED — workstream closed by explicit product decision. Do not
reopen unless field testing identifies a real workflow gap, support-access becomes a defined
requirement, or a security issue is discovered.

Status: Evidence-based validation only. No new architecture, no new tenant
model, no new "elevated access" mode was invented or implemented during this
validation. Scope followed the instruction's "smallest safe remediation"
limits (one focused test added; zero production code changed).

Term discipline (reaffirmed, unchanged from prior docs):
- SUPERADMIN (product concept in this instruction) = the existing `OWNER`
  role/account, the SNS Tech Solutions platform-owner account.
- `SUPER_ADMIN` (alias in `roles.py` → `ADMINISTRATOR`) and "SUPER ADMIN MODE"
  (dead code in `tenant_orm_filters.py`) are unrelated and must not be
  conflated with OWNER.
- `PLATFORM_DEVELOPER` (docs/recovery/2026-09-15/RBAC_HIERARCHY_DECISION.md)
  is a separate, low-privilege internal staff role — not the owner concept.
- ACP = Advance Care Planning (unrelated to this document).

## 1. PLAN SOURCES FOUND

| Source | Relevance |
|---|---|
| docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md (LOCKED) | Defines "Owner Platform" as SNS Tech Solutions; does not operate hospice agencies |
| backend/app/services/admin_bootstrap_service.py | Canonical account-provisioning mechanism (`provision_development_logins`) |
| backend/app/core/roles.py | `PLATFORM_ROLES`, capability matrix; no literal `SUPERADMIN` role exists |
| backend/app/core/middleware/clinical_access_guard.py | Enforces platform/tenant/billing route-prefix boundaries |
| backend/app/api/owner_admin.py, owner_billing_licensing.py | The entire implemented Owner Platform route surface |
| backend/app/api/auth.py (`switch-agency`/`linked-agencies`) | Only tenant-plurality feature in the repo; unrelated to OWNER (see §7) |
| docs/phase2/SUPERADMIN_DEVELOPER_LOGIN_VALIDATION.md | Prior validation in this session (login, RBAC boundary, dead-code findings) — superseded in scope by this document, not contradicted |

No plan document describes a "tenant selection/switching," "elevated owner
support mode," or "patient-data access with non-disclosing response" feature
for OWNER as an implemented item. These appear in this instruction as
requirements to *verify*, not as citations to an existing implemented spec.

## 2. SUPERADMIN ROLE DEFINITION

No role literally named `SUPERADMIN` exists. The product concept maps to
`OWNER` in `PLATFORM_ROLES` (`backend/app/core/roles.py`): tier-1 platform
role, unconditional `staff.*` capabilities, `access_scope="platform"`.

## 3. OWNER ACCOUNT STATUS

One active `OWNER` account exists in the live dev DB (`tenant_id =
PLATFORM_TENANT_ID`, `active = True`), provisioned via
`provision_development_logins()` from `DEV_PLATFORM_OWNER_EMAIL` /
`DEV_PLATFORM_OWNER_PASSWORD` (no hardcoded/implicit secret). One unrelated
inactive test-tenant `OWNER` row exists (not a duplicate/conflict).

## 4. AUTHENTICATION RESULT

- Live `POST /auth/login` with correct credentials → 200, JWT `role=OWNER`,
  `tenant_id=PLATFORM_TENANT_ID`.
- Wrong password → 401 (generic, non-disclosing).
- **Disabled account** → 401 (generic, non-disclosing). Confirmed by code
  (`auth.py::login()` filters `User.active.is_(True)` before any password
  check) and now by a new focused test:
  `backend/tests/test_superadmin_owner_disabled_account.py::test_disabled_owner_account_cannot_log_in`
  — **PASSED**.
- Live browser UI login/logout also verified (see prior session validation).

## 5. OWNER PLATFORM RESULT

Full implemented Owner Platform route surface (`app/api/registry.py`
registers exactly two owner routers):

| Area | Routes (owner_admin.py / owner_billing_licensing.py) | Guard | Audit | Test coverage |
|---|---|---|---|---|
| Tenant management | GET/POST `/tenants`, PATCH `/tenants/{id}/status`, PATCH `/tenants/{id}/financials` | `require_owner` / platform access_scope via `clinical_access_guard` | `log_event` on create/status/financials changes | test_owner_platform_rbac_matrix.py, test_auth_hardening.py |
| User/staff management | GET/POST `/users`, PATCH `/users/{id}`, `/users/{id}/status`, `/revoke-access`, `/remove`, `/permissions`, `/reset-password` | `require_platform_permission("staff.*")` | `log_event` on every mutating call (7 call sites) | test_owner_platform_rbac_matrix.py |
| Audit logs (viewer) | GET `/audit-logs` | `require_owner` | n/a (read) | test_owner_audit_log*.py |
| System health | GET `/system-health` | `require_owner` | n/a (read) | not independently found |
| Adoption health | GET `/adoption-health` | `require_owner` | n/a (read) | not independently found |
| Billing & Licensing | GET `""`, `/kpis`, `/licenses`, `/invoices`, `/payments`, `/revenue`, `/tenants` | `require_owner` | n/a (read-only; `data_available` flag until real subscriptions onboarded) | not independently found |

"Integrations," "diagnostics," "recovery/support operations," and "platform
reports" as named concepts **do not exist** as separate routes/functions in
the repository. The Owner Platform's implemented surface is exactly the
table above (tenants, staff/users, audit-log viewer, system-health,
adoption-health, billing/licensing). Status: **DOCUMENTED, PARTIALLY TESTED**
(system-health, adoption-health, and billing/licensing read endpoints have no
dedicated test found; not a defect — read-only, owner-guarded, no PHI).

## 6. TENANT ACCESS RESULT

OWNER can act on tenant *records* (create, activate/deactivate, financials
toggle) via `/api/owner/tenants*` — confirmed live (200) and by RBAC matrix
tests. OWNER has **no route** that returns another tenant's operational
dashboard/workspace; there is no "log in as tenant" surface at all.

## 7. TENANT SWITCHING RESULT

**NOT FOUND.** No tenant-selection/switching mechanism exists for OWNER.
The only tenant-plurality feature in the repository is
`POST /auth/switch-agency` / `GET /auth/linked-agencies`
(`backend/app/api/auth.py` ~L365-450), which is unrelated: it lets **the same
physical person** who holds **separate accounts** in multiple agencies
(matched by SSN/name/DOB/license) switch between those accounts, and it
requires **that target account's own password**. It is not an OWNER
capability and grants no support-mode access to another tenant's data.
Consequently "clear tenant-specific state on switch," "audited entry/exit for
tenant switching," etc. do not apply — there is nothing to clear or audit
because the feature does not exist for OWNER.

## 8. PATIENT-DATA ACCESS RESULT

Live-verified: `GET /patients` with an OWNER JWT → **403** ("Clinical access
is not permitted for this role"), enforced by `clinical_access_guard`
matching `access_scope_for_role("OWNER") == "platform"` against
`PLATFORM_ALLOWED_PREFIXES` (which excludes `/patients`). OWNER has **zero**
patient-data access today — no blanket bypass, but also no "support mode" to
intentionally and auditedly view a tenant's patient data. This is maximally
protective by default, not a defect.

## 9. CLINICAL-ACTION BOUNDARIES

No clinical write/read action (orders, notes, assessments, exports) is
reachable by OWNER; all are behind the `/patients`-and-adjacent prefixes
blocked by `clinical_access_guard`. Confirmed by the same live 403 test in
§8 and by `test_owner_platform_rbac_matrix.py`.

## 10. ELEVATED ACCESS STATUS ("Elevated Owner Support Mode")

Searched for: impersonation, assume-tenant, support-mode, break-glass,
elevated-access, diagnostic-mode, tenant-assumption, switch_agency.
Only hit: `switch-agency` (§7, unrelated).

**Classification: NOT FOUND.** No impersonation/tenant-assumption/support-mode
mechanism exists for OWNER anywhere in the repository (backend or frontend).

## 11. FRONTEND RESULT

`sns-emr-frontend/src/utils/authorization.ts` (`hasRouteAccess` /
`getDefaultRoute` / `canAccessPath`) matches backend `access_scope` semantics
exactly: OWNER → `/owner` only. New tests added this session
(`authorization.test.ts`, 4 tests) — **PASSED**. No frontend UI exists for
tenant switching or elevated/support mode (consistent with §7/§10 — nothing
to wire because the feature doesn't exist).

## 12. BACKEND RESULT

`login()` already filters disabled accounts (non-disclosing 401).
`clinical_access_guard` already fully blocks OWNER from clinical routes.
`owner_admin.py` / `owner_billing_licensing.py` are the complete, already-
guarded, already-audited (for mutations) Owner Platform surface. No backend
defect found; no production code changed.

## 13. AUDIT RESULT

15 `log_event(...)` call sites in `owner_admin.py` cover every mutating
owner action (tenant create/status/financials, user create/update/status/
revoke/remove/permissions/reset-password). Read-only endpoints (system-
health, adoption-health, billing/licensing, audit-log viewer itself) are not
separately audited — consistent with normal read-audit conventions elsewhere
in the codebase; not flagged as a defect.

## 14. TEST RESULTS

Ran via `python scripts\run_isolated_tests.py --` (isolated per-run DB):

```
tests/test_superadmin_owner_disabled_account.py
tests/test_auth_hardening.py
tests/test_owner_platform_rbac_matrix.py
......................                                          [100%]
22 passed, 0 failed
```

Plus previously-passing frontend tests: `authorization.test.ts` — 4/4 passed
(`npx vitest run`).

No broader/full-backend regression suite was re-run in this task (already
reconciled against the same 15 known pre-existing/unrelated failures in the
immediately-prior AC-00x closeout in this session; nothing in this task
touched production code, so that baseline is unaffected).

## 15. FILES CHANGED

New only (no production code modified):
- `backend/tests/test_superadmin_owner_disabled_account.py`
- `sns-emr-frontend/src/utils/authorization.test.ts`
- `docs/phase2/SUPERADMIN_PLAN_TRACEABILITY.md`
- `docs/phase2/SUPERADMIN_DEVELOPER_LOGIN_VALIDATION.md`
- `docs/phase2/SUPERADMIN_OWNER_ACCOUNT_VALIDATION.md` (this file)

Pre-existing uncommitted files from the prior AC-00x task (unrelated, already
reviewed/accepted) remain uncommitted and untouched.

## 16. SCHEMA AND MIGRATION IMPACT

None. No schema change, no migration created or modified.

## 17. CONFIRMED DEFECTS

None.

## 18. REMAINING VERIFIED GAPS

1. No dedicated test exists for `/system-health`, `/adoption-health`, or the
   billing/licensing read endpoints (read-only, owner-guarded, no PHI —
   low risk, not blocking).
2. No "Elevated Owner Support Mode" (tenant-assumption with audited
   entry/exit and non-disclosing patient responses) exists for OWNER. Any
   requirement describing such a mode is a **feature that must be designed
   and built**, not a defect in an existing implementation.

## 19. PRODUCT DECISIONS REQUIRED

- **Should OWNER ever be granted a controlled, audited, time-boxed
  "support mode" to view a specific tenant's patient data for support
  purposes?** No such mechanism exists today (§7, §8, §10). Building one is
  a new capability (new tenant-assumption flow, new audit event types, new
  non-disclosing-response contract, new frontend UI) — out of this
  validation task's "smallest safe remediation" boundary and requires
  explicit product/security sign-off before implementation.

## 20. FINAL STATUS

**COMPLETE WITH VERIFIED GAPS**

Rationale: OWNER account, authentication (including disabled-account
rejection, now tested), RBAC/route boundaries, and the entire implemented
Owner Platform surface (tenants, users, audit-logs, system-health,
adoption-health, billing/licensing) are verified correct with passing tests
and zero confirmed defects. The gaps are the absence of a tenant-
switching/"Elevated Owner Support Mode" feature that was never built — a
scope/product decision, not a regression or defect — and are reported above
rather than silently implemented or silently dropped.

CONFIRMATION: ACP REMAINS ADVANCE CARE PLANNING.
