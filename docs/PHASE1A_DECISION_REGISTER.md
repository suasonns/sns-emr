# Phase 1A — Decision Register

Status: Planning only. Tracks every explicit decision made or deferred during
Phase 1A reconciliation.

| # | Decision | Status | Owner | Basis |
|---|---|---|---|---|
| 1 | Second-reviewer sign-off recorded for `roles.py` (`review/staff-management-rbac-auditlogs`)? | **UNRESOLVED** | Human (user) | No document confirms this was ever recorded; `PHASE1_MERGE_BLOCKERS.md` flagged it as non-blocking but open |
| 2 | `PLATFORM_AI_MANAGEMENT` / `PLATFORM_OPERATIONS` interim tier-7 role placement ratified? | **UNRESOLVED** | Human (user) | `OWNER_PLATFORM_FINAL_READINESS.md` states this is "awaiting ratification"; no later document confirms it |
| 3 | Any live production users currently assigned `PLATFORM_OPERATIONS`/`PLATFORM_AI_MANAGEMENT`? | **UNRESOLVED / NOT VERIFIED** | Human (user) | `OWNER_PLATFORM_FINAL_READINESS.md` recommended a one-time production query; no evidence it was run |
| 4 | RBAC hierarchy model (data-driven rank vs. hardcoded exception) | **RESOLVED** | N/A — already decided | Live code confirms data-driven `ROLE_AUTHORITY_RANK`; no hardcoded bypass present |
| 5 | Recovery branch merge decision (Staff Mgmt/RBAC/Audit Logs/Password Setup) | **RESOLVED** | N/A — already decided | PR #91 (`6f456ab`) + hotfix (`4182f0f`) merged, confirmed ancestors of `HEAD` |
| 6 | `authorization.ts` route-gate broadening (OWNER-only → any platform-scope role) | **RESOLVED** | N/A — already decided | Explicitly approved by user as "Option A" per later documents |
| 7 | Owner Platform overall completion | **UNRESOLVED (in progress, not blocking)** | Human (user), then implementation | 4 of 9 sections remain, each requires a Figma redesign decision first (Settings scope, then Figma for Settings/Analytics/Billing/AI) |
| 8 | ADR-004 gate (Tenant Platform / RNICA / AI implementation start) | **RESOLVED — gate remains CLOSED** | N/A | ADR-004 unmodified; its 3 conditions not all met while Owner Platform is only partially complete |
| 9 | Whether `OWNER_PLATFORM_ROADMAP_STATUS.md` / `OWNER_PLATFORM_REMAINING_WORK.md` need a superseding note for their stale "not merged" language | **RECOMMENDED, NOT YET ACTIONED** | Human (user) to authorize; this is a docs-only edit, would need separate authorization to write | Both documents predate the PR #91 merge that resolved their central claim |

## Unresolved Decisions Requiring Human Input (summary)

1. Confirm or waive the second-reviewer sign-off on `roles.py` (#1).
2. Ratify or revise the interim `PLATFORM_AI_MANAGEMENT`/`PLATFORM_OPERATIONS` tier
   placement (#2).
3. Confirm whether a production query for those two role assignments was ever run,
   and if not, whether it's still needed given no production environment has been
   established in this repository's diagnostics so far (#3).
4. Decide whether to authorize a documentation-only superseding note on the two
   stale Owner Platform status documents (#9) — this would be a Phase 1A-adjacent,
   docs-only edit, not a Phase 1B code action, but is explicitly deferred here
   pending your authorization since Phase 1A is scoped as read/decide-only.

None of items 1–4 block any current functionality or any further Owner Platform
implementation work already in progress — they are governance/documentation
closure items only.
