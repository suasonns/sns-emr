# Owner Platform Security Review

Read-only. No code changed. Review-only, per directive. All line numbers refer to the recovered
files staged in `recovery/copilot-session-2026-09-14`.

| # | File | Line(s) | Function | Security impact | Classification | Required correction (not yet applied) |
|---|---|---|---|---|---|---|
| 1 | `sns-emr-frontend/src/utils/authorization.ts` | 26 | `hasRouteAccess()` | Route-level access to `/owner/*` broadened from `access_scope === "platform" && role === "OWNER"` to `access_scope === "platform"` alone — any of the 13 new/existing platform roles can now load the owner shell client-side. Actual mutation risk is bounded by backend `role_can()`/`allowed_actions` gating on the *new* staff endpoints (verified by tests), but the *pre-existing* owner pages (tenant onboarding, financials, system health) were built assuming route access implied OWNER identity and were not re-audited in this recovery for independent per-action gating. | **HIGH** | Audit every existing (non-recovered) `/owner/*` page/endpoint for its own server-side authorization check independent of route access; only then confirm this broadening is safe. Until that audit is done, do not merge this line. |
| 2 | `backend/app/core/roles.py` | 452 (function start), 485-486 (bypass) | `role_can()` | `OWNER` receives an unconditional `return True` for any capability in `STAFF_CAPABILITIES`, bypassing the entire matrix/ceiling logic that governs every other role. Mirrored in `effective_capabilities_for_role()` (line 429) and `_role_grants()` (line 395). This is a hardcoded authority path, not a database-driven grant — it cannot be revoked, time-boxed, or audited as a row the way delegated grants can. | **MEDIUM** (intentional, documented design; consistent with the pre-existing, unmodified `is_owner_role()` pattern elsewhere in the codebase — not a newly introduced bug, but does not meet a strict "no hardcoded owner authority" bar if that is a hard requirement) | Explicit decision needed: accept as intentional root-authority pattern (recommended default, matches existing `is_owner_role()`/`require_owner()` precedent), or redesign as a protected, non-revocable-floor database grant if strict compliance requires it. No code change until decided. |
| 3 | `backend/app/api/owner_admin.py` | `list_platform_users()` (main: cross-tenant query; recovered: `u.role = ANY(:platform_roles)` predicate — see `HIGH_RISK_CONFLICT_REPORT.md` §1 for exact hunk) | `list_platform_users` | The `/users` endpoint's query semantics are fully replaced (tenant-filtered roster → platform-staff-only roster) rather than extended. This is a **behavioral risk to existing consumers**, not a new privilege-escalation path per se — if anything outside the 46 recovered files still expects the old cross-tenant roster from this exact route, it silently gets a different, narrower result set instead of an error. | **MEDIUM** (functional/regression risk, not a direct authorization bypass — the new query is, if anything, more restrictive, not less) | Confirm no other consumer depends on the old cross-tenant `/users` behavior before merging; if one exists, either version the route or make the platform-staff behavior additive (new route) instead of replacing. |

## Classification summary

- **CRITICAL:** none found.
- **HIGH:** 1 (`authorization.ts` route broadening — pending completion of the per-action gating
  audit on existing owner pages).
- **MEDIUM:** 2 (`roles.py` hardcoded OWNER bypass — architectural/compliance question, not a bug;
  `owner_admin.py` `/users` semantic replacement — regression risk, not privilege escalation).
- **LOW:** none found as independently new in this pass beyond what's already covered above.

## Explicit statement

No CRITICAL-severity finding was identified in this review. The one HIGH item is contingent on
work not yet done (auditing pre-existing owner pages), not a confirmed live exploit in the
recovered code itself — the recovered code's *own* new endpoints already enforce
`role_can()`/`require_platform_permission()` correctly per the passing
`test_owner_platform_rbac_matrix.py` suite. **No fixes have been applied.** Review only, per
directive.
