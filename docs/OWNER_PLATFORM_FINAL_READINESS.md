# OWNER PLATFORM — FINAL READINESS REPORT

**Date:** 2026-09-15
**Branch under review:** `recovery/copilot-session-2026-09-14`
(worktree: `C:\Users\rdsua\Desktop\copilot-recovery-2026-09-15\recovery-worktree`)
**Action taken this pass:** Read-only investigation of
`PLATFORM_AI_MANAGEMENT` / `PLATFORM_OPERATIONS`. **No code changed. No
commit. No merge. No PR.**

---

## PART A — `PLATFORM_AI_MANAGEMENT` / `PLATFORM_OPERATIONS` REVIEW

### Findings

| Question | `PLATFORM_OPERATIONS` | `PLATFORM_AI_MANAGEMENT` |
|---|---|---|
| **1. Legacy role?** | No. Predates the "Phase UM-1" RBAC foundation (added earlier, in the original master access-control taxonomy), but is not deprecated — it is an active, documented, forward-reserved role. | Same — pre-dates Phase UM-1, not deprecated. |
| **2. Active?** | Yes. In `VALID_ROLES` (`auth.py`) — a user with this role can log in and pass token validation. In `PLATFORM_ROLES` (`roles.py`). Has a `PLATFORM_PERMISSION_MATRIX` entry (`staff.view`). Has an `ACCESS_LEVEL_FOR_ROLE` tier (`LEVEL_4_OPERATIONAL_STAFF`). Included in `available_roles = sorted(PLATFORM_ROLES)` served to the frontend Add/Change-Role dropdowns — **actively assignable today via the SNS Staff & Access UI.** | Same wiring — active, assignable, `staff.view` grant, `LEVEL_3_SPECIALIZED_ADMINISTRATOR` tier. |
| **3. Referenced by existing users?** | No bootstrap/seed identities use it (`admin_bootstrap_service.py`'s `DEVELOPMENT_IDENTITIES` only seeds `DPCS_ADMINISTRATOR`, `OWNER`, `BILLING`, and clinical roles). **Whether any live production user row has this role cannot be verified from this recovery worktree** — `users.role` is a plain `String` column with no DB-level enum constraint, and this session has no access to the production database. | Same — no seed/bootstrap identity; production usage unverifiable from here. |
| **4. Referenced in permissions?** | Yes — `PLATFORM_PERMISSION_MATRIX["PLATFORM_OPERATIONS"] = {"staff.view"}`. Also appears in the cosmetic `PRIVILEGED_PLATFORM_ROLES` stat set in `owner_admin.py` (display-only "Privileged Accounts" count, not an authorization gate). | Yes — `PLATFORM_PERMISSION_MATRIX["PLATFORM_AI_MANAGEMENT"] = {"staff.view"}`. Not in `PRIVILEGED_PLATFORM_ROLES`. |
| **5. Referenced in database records?** | No schema-level enum constraint exists to check against; not verifiable without querying the live database (out of scope/access for this session). No seed data creates such rows. | Same. |
| **6. Referenced by tests?** | Yes, extensively — `test_owner_platform_staff_lifecycle.py` (service-account creation, filtering, role-change, re-activation — 9 references), `test_owner_platform_staff_profile.py`, `test_owner_audit_logs.py` (severity classification for role-change events). | Yes, once — `test_owner_platform_staff_lifecycle.py` line 546 (role assignment coverage). Lighter coverage than Operations but present. |

### Design intent (from `docs/ACCESS_CONTROL_MODEL.md`, pre-existing, not written this pass)

> `PLATFORM_OPERATIONS` — "New, additive. Reserved for platform health/ops
> tooling."
> `PLATFORM_AI_MANAGEMENT` — "New, additive. Reserved for AI pricing/plan
> configuration (see AI subscription model below — not yet built)."

This maps directly onto two **already-identified, not-yet-built** Owner
Platform sections from your own roadmap: **System Health** (Operations) and
**AI Command Center** (AI Management) — the latter explicitly one of the four
sections you've classified "NOT READY — needs Figma redesign."

### Determination: **NOT unused — do NOT mark for deprecation.**

Both roles are active, wired end-to-end (login, permission matrix, access
tier, assignable-role list, tests), and intentionally reserved for named
future platform sections already on your roadmap. Removing or deprecating
them now would be premature and contradicts their documented purpose.

### Recommendation — where they belong

They are **not part of the approved 12-role Staff Management hierarchy**
(Owner → Platform Admin → Security → Compliance → Billing → Implementation
→ Developer → DevOps → QA → Customer Service → Support → Auditor) because
that hierarchy governs **Staff Management job functions**, not every
platform role ever reserved for a future section. Proposal:

- **Keep both at their current authority rank (tier 7, alongside DevOps)**
  as an interim, conservative placement — this is already implemented in
  `ROLE_AUTHORITY_RANK` with an explicit code comment flagging them as
  "not part of the newly-approved hierarchy list, but pre-existing,
  additive platform roles from an earlier phase."
- **Do not fold them into the 12-role list** — treat them as a *separate,
  smaller reserved-role set* tied to specific future sections (System
  Health tooling / AI Command Center), each to get its own seniority
  placement decision **when that section is actually built** (System
  Health is already COMPLETE per your status but these roles aren't yet
  wired to any System-Health-specific endpoint beyond `staff.view`; AI
  Command Center is explicitly pending Figma).
- This is a **decision for you to ratify**, not a default I've silently
  applied beyond the placeholder rank already in place. No further code
  change is proposed or needed until you decide otherwise.

---

## PART B — FINAL READINESS REPORT

### 1. Staff Management status: **COMPLETE**
Creation/editing/deactivation/reactivation, department/job-title/account-type
assignment, permission grants, access-level assignment, and staff lifecycle
validation are all implemented and covered by passing tests
(`test_owner_platform_staff_lifecycle.py`,
`test_owner_platform_staff_profile.py`,
`test_owner_platform_staff_delegation.py`).

### 2. RBAC status: **COMPLETE**
- Hierarchy converted to the approved, fully data-driven model
  (`ROLE_AUTHORITY_RANK` in `backend/app/core/roles.py`).
- Hardcoded `OWNER` bypass removed from `role_can()`.
- Delegation authority (`DELEGATION_AUTHORITY_ROLES`) converted from a
  string-literal exception to explicit rank-based/data-driven membership.
- All pre-existing RBAC tests pass with zero regressions
  (`test_owner_platform_rbac_matrix.py`).
- Open item: `PLATFORM_AI_MANAGEMENT` / `PLATFORM_OPERATIONS` placement —
  reviewed this pass (Part A above), **not blocking**, interim placement
  already in place and clearly flagged for your ratification.

### 3. Password Setup status: **COMPLETE**
`/auth/set-password` and `/auth/set-password/validate` covered end-to-end
by new `test_password_setup_flow.py` (9/9 passing): token generation,
fresh/unknown/expired token validation, successful password creation,
reuse-prevention, and audit logging (`PASSWORD_SET_VIA_RESET_LINK`).

### 4. Audit Log status: **COMPLETE**
Free-text search coverage gap closed with 4 new tests in
`test_owner_audit_logs.py` (actor-email match, action-name match,
no-match-empty-result, composition with `entity_id` filter). Full file:
38/38 passing.

### 5. Frontend validation status: **COMPLETE (within scope)**
- Build (`tsc -b && vite build`, the exact CI/DigitalOcean command): zero
  errors in any Owner Platform / Staff Management / RBAC / Audit Log file.
  The only build errors (12, in `billing/FacilityCollectionsReportPage.tsx`)
  are pre-existing on `main` and unrelated to this recovery — confirmed
  byte-for-byte identical file and identical error set on a `main`-based
  baseline build.
- Lint: found and fixed one real regression introduced by the recovered
  `SetPasswordPage.tsx` (synchronous `setState` inside a `useEffect`,
  converted to derived state). After the fix, lint problem count is
  **78/78 — exact parity with `main`.** Zero new lint issues remain.

### 6. Backend validation status: **COMPLETE (within scope)**
All touched/added backend test files pass against a real, isolated
Postgres test database (via `run_isolated_tests.py`, matching CI's DB
setup): RBAC matrix, staff delegation, staff lifecycle, staff profile,
audit logs (incl. new search tests), password-setup flow. 0 failures
across all runs.

### 7. Remaining defects: **NONE identified in Staff Management or Audit
Logs scope.** The only defects found this effort (the `SetPasswordPage.tsx`
lint regression, and the two rank-based ceiling test breaks from my first
implementation draft) were found and fixed during this same review pass.

### 8. Remaining blockers: **NONE** that block a merge decision for this
scope. Non-blocking open items:
- `PLATFORM_AI_MANAGEMENT` / `PLATFORM_OPERATIONS` seniority-tier placement
  — reviewed, interim placement in place, awaiting your ratification (does
  not affect current behavior; both were already minimally scoped to
  `staff.view` before this pass and remain so).
- Whether either role has live production user records — not verifiable
  from this environment; recommend a one-time production query
  (`SELECT DISTINCT role FROM users WHERE role IN ('PLATFORM_OPERATIONS','PLATFORM_AI_MANAGEMENT')`)
  before or shortly after merge, purely for your own visibility (does not
  change the merge recommendation either way, since both roles were valid,
  assignable roles before and after this pass).

### 9. Open role-hierarchy decisions
- Confirm interim tier-7 placement for `PLATFORM_AI_MANAGEMENT` /
  `PLATFORM_OPERATIONS`, or direct a different placement, per Part A.
- No other open hierarchy decisions — the 12-role Staff Management
  hierarchy you approved is fully implemented as specified.

### 10. Merge recommendation

## CLASSIFICATION: READY FOR SAFE MERGE

Staff Management (incl. RBAC), Password Setup, and Audit Logs are complete,
validated, and regression-free against both the existing test suite and a
`main`-branch build/lint baseline. The one open item
(`PLATFORM_AI_MANAGEMENT`/`PLATFORM_OPERATIONS` tier ratification) is
non-blocking: it does not change any currently-enforced behavior, is
already conservatively placed, and is clearly flagged for your decision
rather than silently resolved.

**Still withheld, per your explicit instruction:** no commit, no merge, no
PR has been created. This report is the final artifact for your review;
work stops here pending your go-ahead.
