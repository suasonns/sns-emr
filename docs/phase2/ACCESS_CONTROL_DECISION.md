# ACCESS_CONTROL_DECISION.md

**Status:** Assessment only. No code, schema, migration, RBAC, permission,
tenancy, route, or audit behavior was changed to produce this decision.

**Terminology:** `ACP` = Advance Care Planning throughout. "Access Control
Policy" is never abbreviated as `ACP`.

## Decision Matrix

| Decision | Criteria | Met? |
|---|---|---|
| NOT NEEDED | Repository already contains sufficient documented access-control model | Partially — `docs/ACCESS_CONTROL_MODEL.md` documents roles/levels/scope, but does not consolidate denial behavior, audit expectations, exceptions, or testing expectations into one place |
| **DOCUMENTATION ONLY** | Controls exist but are not documented in one place | **Yes** — enforcement substantially exists (VERIFIED rows in `ACCESS_CONTROL_EVIDENCE.md`: authentication, authority, RBAC ×2 surfaces, tenant isolation, audit); no single document ties subjects/resources/actions/denial-behavior/audit-expectations/testing-expectations together |
| FUTURE WORKSTREAM | Verified implementation gaps require future work that cannot be done through existing authority/RBAC/permission/tenant-isolation/audit mechanisms | No — the verified defects (`has_permission()` stub, `adr_exports.py` missing auth, `audit_dashboard.py` bad role string) are fixable by *applying* the existing RBAC/permission mechanisms that already exist; they do not require new architecture or a new abstraction |
| INSUFFICIENT EVIDENCE | Repository review cannot support a decision | No — sufficient direct evidence (code + tests) was gathered for every row in the evidence table; remaining NOT VERIFIED items are narrow and do not block a decision |

## Access Control Decision

**DOCUMENTATION ONLY**

## Supporting Evidence

- Authentication, Authority, RBAC (both surfaces), Tenant isolation, and
  Audit enforcement are each independently VERIFIED as implemented and
  (mostly) tested — see `ACCESS_CONTROL_EVIDENCE.md`.
- `docs/ACCESS_CONTROL_MODEL.md` already exists and documents the role
  taxonomy, but does not state denial behavior, audit expectations,
  exceptions, or testing requirements as a single reference.
- The 3 verified defects (stub permission check, unauthenticated export
  route, unmatchable role string) are enforcement bugs *within* the
  existing model, not evidence that the model itself is architecturally
  insufficient — they belong to the existing Phase 2 "Permission
  enforcement" / "Route authorization" workstreams already defined in
  `PHASE2_EXECUTION_PACKAGE.md`, not a new abstraction.

## Conflicting Evidence

See `ACCESS_CONTROL_EVIDENCE.md` "Conflicting Evidence" section (duplicate
auth implementations; stub permission check; unmatchable role string;
unauthenticated export route).

## Unverified Areas

See `ACCESS_CONTROL_EVIDENCE.md` "Unverified Areas" section.

## Unsupported-Assumption Audit

| Statement | Evidence | VERIFIED / UNSUPPORTED |
|---|---|---|
| "The existing controls are sufficient and coherent" | Contradicted by 3 directly-read code defects | UNSUPPORTED as an unqualified claim — corrected to "substantially sufficient, with 3 verified enforcement defects" |
| "A distinct Access Control Policy abstraction is required" | No repository evidence requires new architecture; defects are fixable via existing mechanisms | UNSUPPORTED — removed; decision is documentation-only |
| "`has_permission()` always returns True" | Read directly from `backend/app/core/permissions.py` | VERIFIED |
| "`adr_exports.py::export_adr` has no authentication" | Read directly from `backend/app/api/adr_exports.py` — no `Depends(get_current_user)` or equivalent present | VERIFIED |
| "`audit_dashboard.py`'s `\"QA\"` role never matches" | Read directly from `_ALIASES`/`QA_ROLES` in `backend/app/core/roles.py` — no alias maps `"QA"` to an issued role | VERIFIED |
| "Tenant isolation has no gaps" | Not fully traced (SUPER ADMIN MODE gate unverified) | UNRESOLVED — evidence missing on what triggers `get_current_tenant() is None` |

## Code / Schema / Migration Impact

None. This decision authorizes documentation only. The 3 verified defects
are **not** fixed by this document — they remain open items for the
already-existing Phase 2 Permission enforcement / Route authorization
workstreams, pending separate explicit authorization to implement.

## Required Authorization Before Further Action

Any of the following requires separate, explicit authorization before
implementation:
1. Writing the consolidated access-control policy document itself.
2. Fixing the 3 verified defects (`has_permission()` stub, `adr_exports.py`
   missing auth, `audit_dashboard.py` role string).
3. Any code, schema, or migration change of any kind.

## Confirmation

**ACP REMAINS ADVANCE CARE PLANNING.**
