# ACCESS_CONTROL_DEFECT_REACHABILITY.md

**Status:** Reachability verification only. No code, schema, migration,
RBAC, authority hierarchy, tenancy, route, or audit behavior was changed.
ACP terminology is not reopened: `ACP` = Advance Care Planning throughout.

Method: every claim below was confirmed by directly reading the cited file
and by tracing the router-registration chain in
`backend/app/api/registry.py`; nothing is inferred from names or docs.

---

## Finding 1 — `has_permission()` stub (survey.py)

- **File:** `backend/app/core/permissions.py`
- **Function:** `has_permission(*args, **kwargs) -> bool` (line 95) — body is
  `return True` unconditionally. A second, distinct function
  `require_permission()` in the same file (line 72) is also a stub
  ("Placeholder for fine-grained permissions... acts as authenticated user
  gate") but is a FastAPI dependency, not the function used by survey.py.
- **Current code (has_permission):**
  ```python
  def has_permission(*args, **kwargs) -> bool:
      """Placeholder permission check."""
      return True
  ```
- **Caller chain:** `backend/app/api/survey.py` imports `has_permission`
  from `app.core.permissions` and calls it directly (not via `Depends`) at
  5 sites, each guarding with `if not has_permission(...): raise
  HTTPException(403)`:
  - line 39 `survey_chart_pdf` — `"download_chart_pdf"`
  - line 81 `overdue_poc_updates` — `"view_compliance"`
  - line 93 `idg_compliance` — `"view_compliance"`
  - line 105 `crisis_poc_same_day` — `"view_compliance"`
  - line 125 `survey_export_bundle` — `"export_data"`
  Since `has_permission` always returns `True`, `not True` is always
  `False`, so the `raise HTTPException(403)` is unreachable dead code —
  the permission check itself never blocks anyone.
- **Route chain:** these functions are `@router.get`/`@router.get` handlers
  on `router = APIRouter(prefix="/survey", ...)`.
- **Route registration:** `backend/app/api/registry.py` imports `survey`
  in the "CORE TENANT ROUTES" block (line ~29) and includes `survey.router`
  in `tenant_routes` (line 216), which is registered on the live `app`.
  Confirmed mounted, not conditional/optional.
- **UI entry point:** none found. Searched `sns-emr-frontend/src` for
  `/survey/` — no match. No shipped frontend page currently calls these
  endpoints.
- **API entry point:** `GET /survey/chart-summary`, `GET
  /survey/overdue-poc-updates`, `GET /survey/idg-compliance`, `GET
  /survey/crisis-poc-same-day`, `GET /survey/export-bundle` — all live and
  callable by any HTTP client with a valid bearer token.
- **Role exposure:** every one of these 5 endpoints requires only
  `Depends(get_current_user)` (real JWT authentication, delegated to
  `app.core.auth` via `app.dependencies.auth`) — **no role or permission
  restriction is actually enforced**, because the only authorization
  check (`has_permission`) always passes. Any authenticated user of any
  role can call all 5 endpoints.
- **Tenant exposure:** `overdue_poc_updates`/`idg_compliance`/
  `crisis_poc_same_day` execute raw SQL (`SURVEY_OVERDUE_POC_SQL`, etc.)
  with **no `tenant_id` filter** visible in the query text read directly
  from the file — tenant scoping for these three, if any, would have to
  come from the underlying SQL views (`survey_overdue_poc_updates`, etc.),
  which were not opened in this pass (NOT VERIFIED for tenant scope at the
  view level).
- **Existing tests:** none found. Searched `backend/tests` for `survey` —
  no match.
- **Reproduction evidence:** any authenticated user (regardless of role)
  calling `GET /survey/export-bundle` receives a 200 with the export ZIP,
  because `has_permission(current_user, "export_data")` always returns
  `True`. This was verified by reading the function body directly, not by
  executing the server.
- **Classification: ACTIVE DEFECT.** The code path is live, mounted, and
  reachable via direct API call by any authenticated user; the permission
  gate is provably inert.

---

## Finding 2 — `audit_dashboard.py` `"QA"` role gate

- **File:** `backend/app/api/audit_dashboard.py`
- **Function:** `get_audit_dashboard_patients` (line ~83), gated by
  `Depends(require_roles(["ADMIN", "DPCS", "QA"]))` (line 85).
- **Current code:**
  ```python
  user: CurrentUser = Depends(require_roles(["ADMIN", "DPCS", "QA"])),
  ```
- **Caller chain:** `require_roles` (imported from `app.core.permissions`)
  wraps `role_matches(user.role, allowed_roles, ...)` from
  `app.core.roles`. `role_matches` normalizes both the user's role and
  every entry in `allowed_roles` through `normalize_role()`, which only
  rewrites a role if it is a key in `_ALIASES` (`backend/app/core/roles.py`
  lines 24-49). `"QA"` is **not** a key in `_ALIASES`, so
  `normalize_role("QA")` returns `"QA"` unchanged, and the allowed set
  becomes `{"ADMINISTRATOR", "DPCS", "QA"}` verbatim.
- **Role exposure:** the only role strings the platform actually issues
  for QA staff are `QA_MANAGER`, `QA_REVIEWER`, `COMPLIANCE_OFFICER`
  (`QA_ROLES`, `backend/app/core/roles.py` line 139) — none of these
  normalizes to the literal string `"QA"` (no alias maps them there).
  Repository-wide search for the literal role value `"QA"` found exactly
  2 occurrences: this line, and `backend/app/api/visits.py:739`
  (`AMENDMENT_APPROVAL_ROLES`, an unrelated gate). No model, seed data, or
  role-assignment code was found that issues the literal role `"QA"` to a
  user.
- **Effect:** a real `QA_MANAGER`/`QA_REVIEWER`/`COMPLIANCE_OFFICER` user
  is **denied** (403) by this gate; only `ADMINISTRATOR`/`ADMIN`/`DPCS`
  (and their aliases, plus `CLINICAL_ADMIN_ROLES` fallback per
  `role_matches`) can pass. This is a functional/availability defect
  (intended QA staff locked out), **not** an unauthorized-access
  vulnerability — it does not let anyone in who shouldn't be.
- **Route chain:** `@router.get("/patients")` on
  `router = APIRouter(prefix="/audit-dashboard", ...)`.
- **Route registration:** `registry.py` imports `audit_dashboard_router`
  (line 77) and includes it (line 208) in the live app.
- **UI entry point:** none found. Searched `sns-emr-frontend/src` for
  `audit-dashboard/patients` and `audit_dashboard` — no match. The only
  frontend call to this router's prefix is `GET /audit-dashboard/census`
  (`sns-emr-frontend/src/api/census.ts:84`), a **different endpoint**
  (`get_audit_dashboard_census`, not reviewed in this pass, gated
  separately) — not the `/patients` endpoint with the `"QA"` defect.
- **API entry point:** `GET /audit-dashboard/patients` — live, mounted,
  callable directly.
- **Tenant exposure:** `_resolve_tenant_id()` enforces
  `user.tenant_id == resolved` (line ~64), a real tenant check —
  independent of the role-gate defect.
- **Existing tests:** none found for this route. Searched
  `backend/tests` for `audit_dashboard` — no test file match (only an
  unrelated comment in `conftest.py` mentioning the file name).
- **Reproduction evidence:** confirmed by direct trace of
  `normalize_role("QA_MANAGER")` → `"QA_MANAGER"` (no alias) → not in
  `{"ADMINISTRATOR","DPCS","QA"}` → `role_matches` returns `False` → 403.
- **Classification: ACTIVE DEFECT**, but reclassified in scope: this is a
  **functional access-denial bug for legitimate QA roles**, not a
  security exposure. It is live/mounted and reachable via direct API
  call; no UI currently exercises this exact endpoint.

---

## Finding 3 — `adr_exports.py::export_adr` missing authentication

- **File:** `backend/app/api/adr_exports.py`
- **Function:** `export_adr` (line ~24), `@router.post("/export/adr")` on
  `router = APIRouter(prefix="/chart", ...)`.
- **Current code:**
  ```python
  @router.post("/export/adr", response_class=Response)
  def export_adr(req: AdrExportRequest, db=Depends(get_db)):
      ...
  ```
  The only `Depends` is `get_db` — there is **no** `Depends(get_current_user)`
  or any other authentication/authorization dependency anywhere in the
  function signature or body, confirmed by reading the entire file
  (44 lines).
- **Caller chain:** directly invokes `AdrAuditService(db).run_full_audit(
  req.patient_id, req.adr_start, req.adr_end, mode=req.mode)`. Searched
  `app/services/adr_audit_service.py` for the token `tenant` — zero
  matches, confirming no tenant filter is applied inside the audit
  service either.
- **Route registration:** `registry.py` imports
  `from app.api.adr_exports import router as adr_exports_router` inside a
  `try/except` block (lines ~136-139) that only sets it to `None` if the
  import itself raises. The import succeeds (the module has no unmet
  dependencies), so `adr_exports_router is not None` is `True`, and
  `app.include_router(adr_exports_router)` executes (line 171). **The
  route is live and mounted**, not skipped.
- **UI entry point:** none found. Searched `sns-emr-frontend/src` for
  `/chart/export/adr` — no match.
- **API entry point:** `POST /chart/export/adr` — live, mounted, requires
  only a JSON body (`AdrExportRequest`: `patient_id`, `adr_start`,
  `adr_end`, `mode`, `adr_mode`) — **no bearer token, no session, no
  authentication of any kind**.
- **Role exposure:** none — there is no role check because there is no
  authentication step to produce a role at all.
- **Tenant exposure:** none — no tenant_id parameter, filter, or check
  anywhere in the endpoint or in `AdrAuditService.run_full_audit`.
- **Existing tests:** none found. Searched `backend/tests` for
  `adr_export` — no match.
- **Reproduction evidence:** `curl -X POST /chart/export/adr -d
  '{"patient_id": "<any-uuid>", "adr_start": "...", "adr_end": "...",
  "mode": "...", "adr_mode": true}'` with **no `Authorization` header**
  reaches `AdrAuditService.run_full_audit` and returns a PDF (cover sheet
  or deficiency report) containing PHI, confirmed by static trace of the
  function body — no auth dependency exists to reject it.
- **Classification: ACTIVE DEFECT — most severe of the three.** This is
  the only finding of the three that requires **no authentication at
  all**, not merely a bypassed authorization step.

---

## Decision Matrix

| Finding | Classification | Evidence | Action |
|---|---|---|---|
| `has_permission()` (survey.py, 5 sites) | **ACTIVE DEFECT** | Stub `return True`; dead `raise HTTPException(403)`; router mounted (`registry.py:216`); no tests | Retain in implementation justification |
| `audit_dashboard.py` `"QA"` gate | **ACTIVE DEFECT** (functional denial, not intrusion) | `"QA"` absent from `_ALIASES`/`QA_ROLES`; router mounted (`registry.py:208`); no tests; not reached by current UI | Retain in implementation justification, scoped correctly as an availability bug, not an unauthorized-access bug |
| `adr_exports.py::export_adr` no auth | **ACTIVE DEFECT** | Zero `Depends` for auth; router mounted (`registry.py:171`); no tenant filter in service; no tests | Retain in implementation justification — highest priority |

---

## Updated Decision

All three findings are **ACTIVE DEFECTS** in live, mounted, reachable API
code (verified via `registry.py` inclusion, not assumed). None is dead
code, legacy code, or a false positive. Two (`has_permission`,
`export_adr`) are genuine unauthorized-access exposures; one
(`audit_dashboard` `"QA"`) is a functional access-denial bug for
legitimate QA roles, not an intrusion path — this distinction is now
recorded precisely rather than treating all three as equivalent security
holes.

Because all three affect active execution paths, the prior
**DOCUMENTATION ONLY** decision in `docs/phase2/ACCESS_CONTROL_DECISION.md`
is **superseded**: with confirmed active defects requiring an actual code
fix (not merely consolidating documentation), the correct classification
is **FUTURE IMPLEMENTATION WORKSTREAM** for these three specific fixes —
scoped strictly to applying the *existing* authentication/RBAC/permission
mechanisms already in the repository (adding a real `Depends`, fixing the
role list, or replacing the stub body), **not** a new Access Control
Policy abstraction, not a change to RBAC design, and not a change to the
authority hierarchy.

## Confirmation

**ACP REMAINS ADVANCE CARE PLANNING.**
