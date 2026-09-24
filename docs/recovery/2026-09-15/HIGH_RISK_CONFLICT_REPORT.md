# High-Risk Conflict Report

Read-only analysis. No code changed. Diffs taken from
`recovery/copilot-session-2026-09-14` vs. `main` HEAD `b552fcb`.

---

## 1. `backend/app/api/owner_admin.py`

**Current main version (1,091 lines):** owner-only platform API providing tenant onboarding,
tenant financials, platform-wide audit logs, a cross-tenant `/users` roster (filterable by tenant)
with basic enable/disable/reset-password actions, and system/adoption health endpoints.

**Recovered version (1,477 lines net, +1,433/-44 vs. main):** keeps all existing tenant
onboarding/financial/system-health code untouched, but **rewrites** the `/users` roster from
cross-tenant to platform-staff-only, and adds: `_severity_for_event` / `_affected_permissions_for_role_change`
helpers, richer audit-log filters (`entity_type`, `entity_id`, `request_id`, `severity`,
`affected_permissions`), a 4-state staff lifecycle (`PATCH /users/{id}/status`), delegated
permission grants (`POST /users/{id}/permissions`), and role-change endpoints
(`PATCH /users/{id}/role`) — all gated through `role_can()`/`require_platform_permission()` from
`roles.py`.

**Overlapping regions (exact hunks):**
| Line region (recovered) | What changed |
|---|---|
| `@@ -31,11 +31,30 @@` | new imports: `account_types`, `departments`, `job_titles`, `platforms`, `PLATFORM_TENANT_ID`, `require_platform_permission`, `roles`, `StaffPermissionGrant` |
| `@@ -137,6 +159,134 @@` | adds `_severity_for_event`, `_affected_permissions_for_role_change` |
| `@@ -624,6 +783,25 @@` / `@@ -731,6 +916,12 @@` | audit log endpoint gains new filter params |
| `@@ -770,68 +961,134 @@` (`list_platform_users`) | **behavioral change**: query predicate flips from tenant-filtered (`u.tenant_id = :tenant_id OR :tenant_id IS NULL`) to platform-role-filtered (`u.role = ANY(:platform_roles)`) — main's cross-tenant roster and recovered's platform-staff roster are mutually exclusive query semantics on the same route |
| `@@ -948,7 +1314,461 @@`, `@@ -992,6 +1826,561 @@` | net-new endpoints: lifecycle, delegated grants, staff profile/detail/audit/role-change |

**Conflict risk: HIGH.** The `/users` endpoint's core query is fully replaced, not extended — if
current `main` still depends on the cross-tenant roster behavior anywhere (frontend or otherwise
outside the 46 recovered files), that consumer breaks silently on merge.

**Recommended merge strategy:** manual, section-by-section merge, not a file overwrite.
1. Keep current-`main` tenant onboarding/financial/system-health sections verbatim.
2. Decide explicitly whether `/users` should remain cross-tenant (main's current behavior) or
   become platform-staff-only (recovered behavior) — these cannot both be true for the same route;
   consider whether the recovered platform-staff functionality should be a **new** route instead of
   replacing `/users`.
3. Land the new lifecycle/permission-grant/role-change endpoints as pure additions once the roster
   question above is resolved.
4. This file cannot be merged in isolation — it must land together with `roles.py`,
   `role_guards.py`, `user.py`, the 5 migrations, and `ownerAdmin.ts`/`UserManagement.jsx`.

---

## 2. `backend/app/core/roles.py`

**Current main version (191 lines):** canonical role-alias normalization
(`normalize_role`), `PLATFORM_ROLES`/`CLINICAL_ADMIN_ROLES`/`FINANCIAL_ADMIN_ROLES` sets,
`is_platform_role`, `is_owner_role`, `access_scope_for_role`, `role_matches`. No `staff.*`
capability model exists.

**Recovered version (499 lines, +321/-0 vs. main — purely additive):** adds 8 new
`PLATFORM_*` role strings to `PLATFORM_ROLES` (line ~72-79: `PLATFORM_ADMIN`,
`PLATFORM_SECURITY`, `PLATFORM_DEVELOPER`, `PLATFORM_DEVOPS`, `PLATFORM_IMPLEMENTATION`,
`PLATFORM_CUSTOMER_SERVICE`, `PLATFORM_QA`, `PLATFORM_AUDITOR`), plus an entirely new "SNS Staff &
Access RBAC Foundation" section (lines 244–end): `ACCESS_LEVEL_FOR_ROLE` (line 260),
`PLATFORM_PERMISSION_MATRIX` (line ~329), `STAFF_CAPABILITIES` (line ~300),
`NON_DELEGABLE_CAPABILITIES` (line ~403), `role_can()` (line 452), `can_delegate_capability()`
(line ~512).

**Overlapping regions:** none — every hunk is a pure addition (`git diff --stat` shows
`+321 -0`). Nothing existing is renamed, removed, or behaviorally altered.

**Conflict risk: MEDIUM** (not because of merge collision — there is none — but because this is
the file that defines the entire new authorization surface `owner_admin.py` depends on; a
security-sensitive addition, not a textual conflict).

**Recommended merge strategy:** safe to add as a clean, additive merge. Treat as the first file in
the merge sequence (see `integration-plan.md` Batch 2) since `owner_admin.py`, `role_guards.py`,
and both frontend RBAC files depend on it. See `RBAC_SECURITY_REVIEW.md` below for the one
substantive concern inside this addition (the unconditional OWNER bypass in `role_can()`).

---

## 3. `sns-emr-frontend/src/owner/pages/UserManagement.jsx`

**Current main version (306 lines):** generic owner "User Management" page — cross-tenant user
list with tenant filter, role filter, active/disabled toggle, KPI stats
(`total_users`/`active_now`/`agency_admins`/`disabled_users`), password-reset and enable/disable
actions.

**Recovered version (net +375/-146 vs. main, 521 lines changed region): rewritten** as "SNS Staff
& Access": Human Staff / Service Accounts / API Identities / Audit tabs, department + account-type
+ status filters, backend-driven `allowed_actions` per row, `AddStaffModal`, `StaffProfileDrawer`,
audit sub-feed panel.

**Overlapping regions (exact hunks):**
| Hunk | What changed |
|---|---|
| `@@ -1,26 +1,53 @@` | swaps tenant-list imports for `AddStaffModal`/`StaffProfileDrawer`/access-level helpers |
| `@@ -46,11 +82,43 @@` | new `KpiCard` component, new stats shape |
| `@@ -58,19 +126,24 @@`, `@@ -97,15 +173,37 @@` | replaces tenant-filtered load state with scope/account-type/audit state |
| `@@ -139,189 +237,320 @@` | full page body (table, columns, row actions) rewritten |

**Conflict risk: HIGH — full-content overwrite.** Main's and recovered versions solve visibly
different problems on the same route/component name; there is no line-level reconciliation
possible, only a product decision about which page this route should render.

**Recommended merge strategy:** do not overwrite blindly.
1. Confirm with the product owner whether the cross-tenant "User Management" capability (main) is
   still needed anywhere, or is fully superseded by "SNS Staff & Access" (recovered).
2. If superseded, replace the file — but only in the same commit as `owner_admin.py`'s roster
   change, `ownerAdmin.ts`, `roles.py`, and the 5 migrations (they are not independently
   deployable).
3. If cross-tenant management must be retained, split into two routes/pages instead of one
   replaced file.
4. `AuditLogs.jsx` (284 insertions / 155 deletions) is a sibling file with the same
   overwrite-risk profile and should go through the same review gate even though it wasn't
   explicitly named in this request.

---

## Cross-cutting note

All three files are mutually dependent for a working merge: `roles.py` defines the permission
model; `owner_admin.py` enforces it server-side; `UserManagement.jsx` (and `AuditLogs.jsx`,
`ownerAdmin.ts`) consume it client-side. Merging any one without the others leaves either a
non-functional UI (backend ahead) or an unenforced UI capability (frontend ahead exposing
actions the backend doesn't yet support/reject correctly).
