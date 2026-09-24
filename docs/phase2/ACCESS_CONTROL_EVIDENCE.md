# ACCESS_CONTROL_EVIDENCE.md

**Status:** Evidence review only. No code, schema, migration, RBAC,
permission, tenancy, route, or audit behavior was changed to produce this
document.

## Terminology Validation

| Statement | Evidence |
|---|---|
| `ACP` = Advance Care Planning | 33/33 files containing the token `ACP` (backend models/services + 26 RNICA/HOPE docs) use it for Advance Care Planning; confirmed in `docs/tenant-platform/RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md` and re-verified this pass — no new occurrence found that contradicts this. |
| Access Control Policy is not ACP | Zero occurrences of "Access Control Policy" anywhere in the repository, confirmed by repository-wide search. |
| Authority, RBAC, permission enforcement, route authorization, tenant isolation, and audit enforcement remain separate concepts | Confirmed structurally distinct in code: authority = `ROLE_AUTHORITY_RANK`/`role_authority_rank()`; RBAC/permission = `role_can()` + `PLATFORM_PERMISSION_MATRIX` and `has_capability()` + `ROLE_CAPABILITIES`; route authorization = `require_roles()`/`require_platform_permission()`/`require_capability()`; tenant isolation = `tenant_orm_filters.py` ORM event listeners; audit = `log_event()`/`AuditLog` — all in separate modules with no naming overlap. |

## Evidence Table

| Area | Evidence | Files | Tests | Status | Notes |
|---|---|---|---|---|---|
| Authentication | JWT bearer auth, HS256, issuer/audience-checked, access/refresh token typing | `backend/app/core/security.py` | `test_auth_hardening.py`, `test_session_stability.py` | VERIFIED | A second, independent auth implementation exists in `backend/app/core/auth.py` (own `CurrentUser`/`VALID_ROLES`), and a third dev-only no-auth stub exists in `backend/app/security/deps.py`. Core mechanism is verified; duplication is a separate conflicting-evidence item below. |
| Authority | `ROLE_AUTHORITY_RANK` (rank-based platform seniority, `OWNER`=0) | `backend/app/core/roles.py:299` | `test_owner_platform_rbac_matrix.py` | VERIFIED | Platform-role hierarchy only; tenant clinical roles use a different (non-rank) model — not a gap, just a different, also-verified mechanism (`CLINICAL_ADMIN_ROLES`, `role_matches()`). |
| RBAC | `role_can()` + `PLATFORM_PERMISSION_MATRIX` (platform/owner surface); `has_capability()` + `ROLE_CAPABILITIES` (clinical patient-access surface) | `backend/app/core/roles.py:376,502`; `backend/app/core/capabilities.py` | `test_owner_platform_rbac_matrix.py` | VERIFIED | Two RBAC mechanisms exist for two different surfaces (platform vs. clinical) — confirmed intentional (module docstrings state each is "the single source of truth" for its own surface, not competing definitions of the same thing). |
| Permission checks | A third mechanism, `has_permission()` in `backend/app/core/permissions.py`, is a hardcoded stub returning `True` unconditionally | `backend/app/core/permissions.py`; consumed at 5 call sites in `backend/app/api/survey.py` (lines 39, 81, 93, 105, 125) | None found | **CONFLICTING** | This is a genuine, verified defect: chart-PDF download, compliance viewing (×3), and data-export checks in `survey.py` currently always pass for any authenticated caller. Confirmed by reading the function body directly (`return True`), not inferred. |
| Route authorization | `require_roles()`, `require_platform_permission()`, `require_capability()`/`require_any_capability()` | `backend/app/core/permissions.py`; `backend/app/core/role_guards.py`; `backend/app/core/capabilities.py` | `test_owner_platform_rbac_matrix.py` (platform routes only) | **CONFLICTING** | Two verified defects: (1) `backend/app/api/audit_dashboard.py:85` gates on `require_roles(["ADMIN","DPCS","QA"])` — `"QA"` does not normalize to any issued role (confirmed via `_ALIASES`/`QA_ROLES` in `roles.py`), so no real QA account can pass. (2) `backend/app/api/adr_exports.py::export_adr` (`POST /chart/export/adr`) has **no auth dependency at all** — confirmed by reading the full file; it returns a PHI-bearing PDF for any `patient_id` with zero authentication or tenant check (also confirmed `AdrAuditService.run_full_audit` has no tenant filtering). |
| Tenant isolation | Global SQLAlchemy `do_orm_execute`/`before_flush` listeners auto-filter reads and block cross-tenant writes | `backend/app/core/tenant_orm_filters.py`; `backend/app/models/tenant_mixin.py` | No dedicated test found exercising this mechanism directly | PARTIAL | Mechanism itself is implemented and its logic was read directly (not inferred). A documented "SUPER ADMIN MODE" bypasses all tenant filtering when `get_current_tenant()` is `None` — the gate controlling when that can happen was not traced in this pass (NOT VERIFIED, folded into PARTIAL here per the requested status set). |
| Audit enforcement | `log_event()`/`AuditLog` model; `_safe_log_event()` wrapper used at 16 call sites in `visits.py` | `backend/app/services/audit_logger.py`; `backend/app/models/audit_log.py` | `test_audit_logging.py`, `test_owner_audit_logs.py` | PARTIAL | Verified gap (already tracked in `PHASE2_EXECUTION_PACKAGE.md` Workstream 3): the 5 core RNICA CRUD endpoints are not logged. No denied-action (403/401) auditing was found anywhere in the repository. |
| Frontend authorization | `RequireRoleAccess.tsx`, `authorization.ts` (`hasRouteAccess`/`hasFeatureAccess`/`canAccessPath`) | `sns-emr-frontend/src/components/RequireRoleAccess.tsx`; `sns-emr-frontend/src/utils/authorization.ts` | No frontend authorization test suite found | PARTIAL | Coarse-grained scope check by design (backend is stated as the enforcement authority per in-code comment) — implemented, but test coverage NOT VERIFIED. |
| Service authorization | `get_authorized_patient()` — tenant + care-team assignment check | `backend/app/core/patient_access.py` | Consumed by `documents.py`; no dedicated unit test found for the helper itself | PARTIAL | Not confirmed to be used by every patient-scoped router in this pass — usage elsewhere NOT VERIFIED. |

## Conflicting Evidence (summary)

1. Three coexisting "who is authenticated" implementations (`core/security.py`, `core/auth.py`, `security/deps.py` dev stub).
2. `has_permission()` stub always returns `True` — 5 real, currently-non-functional guard call sites in `survey.py`.
3. `audit_dashboard.py` role list contains `"QA"`, which matches no real role.
4. `adr_exports.py` export endpoint has zero authentication or tenant enforcement.

## Unverified Areas

- Full extent of routers using (or bypassing) `get_authorized_patient()`.
- Automated test coverage specifically targeting `tenant_orm_filters.py`.
- Conditions under which `get_current_tenant()` returns `None` ("SUPER ADMIN MODE") and what gates that path.
- Frontend authorization test coverage (none found, but a exhaustive search of all frontend test files was not performed).
