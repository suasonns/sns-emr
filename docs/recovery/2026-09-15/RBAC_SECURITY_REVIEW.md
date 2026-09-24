# RBAC Security Review

Read-only. No code changed. All line numbers refer to the recovered files staged in
`recovery/copilot-session-2026-09-14`.

---

## Finding 1 — `authorization.ts` broadens owner-route access

- **File:** `sns-emr-frontend/src/utils/authorization.ts`
- **Line:** 26 (function `hasRouteAccess`, in the `access === "owner"` branch)
- **Before (current `main`):**
  ```ts
  if (access === "owner") return user.access_scope === "platform" && user.role === "OWNER";
  ```
- **After (recovered):**
  ```ts
  if (access === "owner") return user.access_scope === "platform";
  ```
- **Explanation:** Main restricts the `/owner` route shell to `access_scope === "platform" AND
  role === "OWNER"` — literally only the Owner account. The recovered version drops the
  `role === "OWNER"` clause entirely, so **any** user with `access_scope === "platform"` (i.e. any
  of the 8 new `PLATFORM_*` roles: `PLATFORM_ADMIN`, `PLATFORM_SECURITY`, `PLATFORM_DEVELOPER`,
  `PLATFORM_DEVOPS`, `PLATFORM_IMPLEMENTATION`, `PLATFORM_CUSTOMER_SERVICE`, `PLATFORM_QA`,
  `PLATFORM_AUDITOR`, plus the pre-existing `PLATFORM_SUPPORT`/`PLATFORM_BILLING`/
  `PLATFORM_OPERATIONS`/`PLATFORM_AI_MANAGEMENT`/`PLATFORM_COMPLIANCE`) can now load the owner
  shell and reach every page under `/owner/*` at the routing layer.
- **Security impact:** MEDIUM, not CRITICAL, **provided** every action inside the owner shell is
  independently re-checked server-side. In this recovery that appears to be true for the new
  `staff.*` surface — `owner_admin.py`'s new endpoints call `require_platform_permission()` /
  `role_can()` per-action, and non-OWNER platform roles are denied capabilities they don't hold
  (validated by `test_owner_platform_rbac_matrix.py`). **However**, this review did not
  independently re-verify every *pre-existing* `/owner/*` page and endpoint (tenant onboarding,
  financials, system health, adoption dashboards) for equivalent per-action server-side gating —
  those were built under the old assumption that reaching `/owner` implied `role === "OWNER"`.
  Widening the route gate without auditing every existing owner page's action-level authorization
  could expose UI surface (data visible client-side, even if mutations are blocked) that was never
  designed to be viewed by non-OWNER platform staff.
- **Recommended repair (do not apply yet):** Before merging this line, audit every non-recovered
  page under `sns-emr-frontend/src/owner/` for hidden reliance on "if I'm here, I'm OWNER" — either
  confirm each has its own scope check, or make each page call
  `capabilities_for_role()`/`allowed_actions` (the pattern already used by the new staff pages) and
  gate both rendering and actions on that, not just on having reached the route.

---

## Finding 2 — `roles.py` contains an unconditional OWNER superuser path

- **File:** `backend/app/core/roles.py`
- **Lines:** 452–510 (function `role_can`), specifically **lines 485–486**:
  ```python
  if normalized_actor == "OWNER":
      return True
  ```
  (mirrored at line 429 inside `effective_capabilities_for_role`: `if normalized == "OWNER": return
  set(STAFF_CAPABILITIES)`, and again at line 395 inside `_role_grants`.)
- **Explanation:** `role_can()` is deny-by-default for every other role — it checks capability
  validity, platform-role membership, the effective-capability matrix, and a target-hierarchy
  ceiling. For `OWNER`, all of that is bypassed unconditionally: `OWNER` gets `True` for *any*
  `capability` argument (as long as it's in `STAFF_CAPABILITIES` at all) regardless of
  `target_role` — including targets that are themselves `OWNER`, and including
  `staff.assign_owner_role`. Every other actor is explicitly blocked from
  `staff.assign_owner_role` and from mutating an `OWNER` target (lines ~495-497), but OWNER itself
  has no such ceiling.
- **Security impact:** This is the same finding as `rbac-validation.md` check #7
  ("Owner permissions are not hardcoded" — **FAIL**). It is a deliberate, commented design choice
  (see the docstring at line ~443: "OWNER is intentionally not listed here — is_owner_role() always
  grants every staff.* capability unconditionally"), not an accidental bypass, and it is
  consistent with the pre-existing `is_owner_role()`/`require_owner()` pattern already used
  elsewhere in the codebase (unchanged by this recovery). The risk is architectural rather than a
  bug: OWNER authority is a code constant, not a database/config row, so it cannot be revoked,
  time-limited, or audited-as-a-grant the way every other role's authority now can be via
  `StaffPermissionGrant`. If the SNS platform's compliance model requires that *all* privilege,
  including Owner's, be revocable/auditable at the data layer (e.g. for a break-glass or
  ownership-transfer scenario), this hardcoding does not meet that bar.
- **Recommended repair (do not apply yet):** Two options for a future change (not applied here):
  (a) accept the hardcoded OWNER bypass as an intentional "root" pattern, matching how
  `is_owner_role()` already behaves elsewhere, and document it as an accepted exception rather
  than a defect; or (b) if strict "no hardcoded owner permission" compliance is required, replace
  the unconditional `return True` with a lookup against a seeded, protected
  `OWNER` row in the same permission-grant table used for delegation, with a system invariant that
  it can never be fully revoked below a minimum safe set (e.g. `staff.assign_owner_role`) rather
  than being a code-level bypass. Either choice needs an explicit decision — this review does not
  recommend one over the other.

---

## Summary table

| # | File | Lines | Impact | Confidence |
|---|---|---|---|---|
| 1 | `sns-emr-frontend/src/utils/authorization.ts` | 26 | Route-level access broadened from OWNER-only to any platform-scope role; relies on per-action backend gating being complete everywhere under `/owner` | 8/10 |
| 2 | `backend/app/core/roles.py` | 452, 485-486 (also 395, 429) | OWNER bypasses the entire new capability/ceiling model unconditionally; intentional but not database-driven | 9/10 |

No code has been modified as part of this review.
