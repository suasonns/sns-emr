# Platform Owner Compliance Review

Read-only analysis against the recovered code as staged in
`recovery/copilot-session-2026-09-14`. No code changed.

## 1. Platform Owner status

**Confirmed.** `roles.py::is_owner_role()` (pre-existing, unchanged) recognizes only `OWNER`.
`role_can()` (new, line 452) gives `OWNER` an unconditional `return True` for every `staff.*`
capability (line 485-486) before any matrix lookup — OWNER sits structurally above the entire new
permission matrix, not inside it. `ACCESS_LEVEL_FOR_ROLE` (new) explicitly tags OWNER as
`LEVEL_1_OWNER`, the sole top tier. **Platform Owner remains the highest role.**

## 2. Tenant isolation

**Preserved, unchanged.** No recovered file touches `app/models/tenant.py`,
`app/core/protected_tenants.py`'s tenant-scoping logic (only a comment/import-adjacent low-risk
change — see `conflict-analysis.md`), or any tenant-scoped query middleware. Tenant-level row
isolation (`tenant_id` filtering) throughout the rest of the codebase is untouched by this
recovery.

## 3. Biller isolation

`test_owner_platform_rbac_matrix.py::test_tenant_and_biller_roles_never_get_staff_capabilities`
(recovered, new test) explicitly asserts that tenant/biller roles (e.g. `BILLING`) — which are
`FINANCIAL_ADMIN_ROLES`, not `PLATFORM_ROLES` — get **zero** `staff.*` capabilities from
`role_can()`/`effective_capabilities_for_role()`, because `role_can()` first requires
`is_platform_role(actor)` to be true (line ~482) before any capability check runs. Biller/tenant
roles fail that gate unconditionally. **Confirmed isolated** from the new platform-staff
capability surface. (Biller isolation from PHI/clinical data is a separate, pre-existing,
unmodified concern in `roles.py`'s `FINANCIAL_ADMIN_ROLES`/`CLINICAL_ADMIN_ROLES` split.)

## 4. Production agency / training agency isolation

Pre-existing, unmodified: `app/models/tenant.py` enforces
`tenant_type IN ('PRODUCTION', 'TRAINING', 'DEV', 'PLATFORM', 'BILLING')` via a DB check
constraint (baseline migration `521d501c6eea`), not touched by any of the 46 recovered files. The
recovered work operates entirely within the `PLATFORM` scope (platform staff, not agency/tenant
data) and does not introduce any cross-tenant-type data access. **No change to existing
production/training isolation.**

## 5. RBAC hierarchy — ⚠️ DISCREPANCY FROM STATED EXPECTATION

The request asks to confirm:

> Platform Owner > Platform Administrator > Customer Service > Support > Developer

**This exact ordering is NOT what the recovered code implements.** The recovered
`ACCESS_LEVEL_FOR_ROLE` matrix (`roles.py`, ~line 260) defines these tiers instead:

| Tier | Roles |
|---|---|
| LEVEL_1_OWNER | `OWNER` |
| LEVEL_2_ADMINISTRATOR | `PLATFORM_ADMIN` |
| LEVEL_3_SPECIALIZED_ADMINISTRATOR | `PLATFORM_SECURITY`, `PLATFORM_COMPLIANCE`, `PLATFORM_BILLING`, `PLATFORM_AI_MANAGEMENT` |
| LEVEL_4_OPERATIONAL_STAFF | `PLATFORM_OPERATIONS`, **`PLATFORM_DEVELOPER`**, `PLATFORM_DEVOPS`, `PLATFORM_IMPLEMENTATION`, `PLATFORM_QA` |
| LEVEL_5_LIMITED_SUPPORT | **`PLATFORM_SUPPORT`, `PLATFORM_CUSTOMER_SERVICE`** |
| LEVEL_6_READ_ONLY | `PLATFORM_AUDITOR` |

Owner (1) and Administrator (2) match the requested ordering. But **Developer sits at Level 4,
above Customer Service and Support at Level 5** — the inverse of the requested
"Customer Service > Support > Developer" order. `PLATFORM_PERMISSION_MATRIX` corroborates this:
`PLATFORM_DEVELOPER` gets `{"staff.view"}` only (same as Support's baseline before its
`staff.reset_password` addition), while `PLATFORM_CUSTOMER_SERVICE` gets `set()` (zero
capabilities) — Customer Service is in fact the **most** restricted operational role in the
matrix, not ranked above Support/Developer.

**This needs a decision, not a code fix yet:** either (a) the requested hierarchy description in
this task was approximate/aspirational and the recovered implementation (Owner > Admin >
Security/Compliance/Billing/AI > Operations/Dev/DevOps/Implementation/QA >
Support/CustomerService > Auditor) is what should ship, or (b) the recovered `ACCESS_LEVEL_FOR_ROLE`
ordering itself needs correcting before merge to match the intended hierarchy. Flagging this as
the top compliance finding of this review — do not assume either resolution without an explicit
answer.

## 6. No tenant user can access platform-owner resources

**Confirmed, unchanged.** `role_guards.py`'s `require_owner()`/`require_platform_role()` guards
(pre-existing, low-conflict per `conflict-analysis.md`) still gate every `owner_admin.py` route at
the dependency-injection level; `role_can()`'s new capability layer sits **inside** that existing
platform-only gate (`if not is_platform_role(normalized_actor): return False`, line ~482), so a
tenant-scoped role can never reach a `staff.*` capability regardless of the capability matrix
contents. Frontend-side, `authorization.ts::hasRouteAccess("owner", ...)` still requires
`user.access_scope === "platform"` (unchanged by the recovered diff) — a tenant-scope user is
blocked from the `/owner` route shell itself, independent of the one line that was widened (see
`RBAC_SECURITY_REVIEW.md`).

## Bottom line

5 of 6 checks pass cleanly against the recovered code as-is. The RBAC hierarchy check (#5) exposes
a real mismatch between the ordering given in this task and the ordering implemented in the
recovered `roles.py` — this should be resolved explicitly (confirm intended hierarchy) before
Batch 2/3 of the integration plan proceeds.
