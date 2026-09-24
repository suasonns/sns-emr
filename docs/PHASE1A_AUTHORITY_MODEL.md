# Phase 1A — Authority Model (Formalized)

Status: Planning/formalization only. Documents the single, already-implemented
authority model. No code changes made under this document.

## 1. Selected Authority Model

**Rank-based Role Authority (`ROLE_AUTHORITY_RANK`) combined with a centralized
capability check function (`role_can()`) backed by `PLATFORM_PERMISSION_MATRIX`.**
This is the one and only authority model in the current codebase — confirmed via
direct inspection of `backend/app/core/roles.py`, not inferred from documents.

## 2. RBAC Hierarchy

- Roles are ordered by an integer rank in `ROLE_AUTHORITY_RANK` (higher rank =
  greater authority).
- `OWNER` sits at the top of the hierarchy.
- All other platform/tenant roles are ordered beneath it by rank value.
- The two roles flagged as provisional (`PLATFORM_AI_MANAGEMENT`,
  `PLATFORM_OPERATIONS`) occupy an **interim tier-7 placement** pending formal
  ratification (see Remaining Gaps, and Decision Register item 2).

## 3. Permission Inheritance

- Authority is rank-comparison based: an actor may act on/manage a target role
  only if `actor_rank >= target_rank` (exact comparator confirmed present in
  `role_can()`).
- There is no separate, independent inheritance tree — a single linear rank
  ordering serves as the inheritance mechanism (higher rank implicitly includes
  authority over all lower ranks it is checked against).

## 4. Exception Handling

- `OWNER` retains an intentional, unconditional grant at the top of the
  hierarchy — this is a deliberate architectural root-authority pattern, not a
  residual defect.
- The defect that was fixed (and is now confirmed absent via `grep`) was a
  **separate, hardcoded delegation-exception bypass** (`if normalized_actor ==
  "OWNER": return True` used opportunistically inside a delegation check), which
  has been replaced with the same rank-comparison logic used everywhere else. No
  other hardcoded exceptions were found.

## 5. Escalation Rules

- No dedicated "escalation" workflow exists in the authority model itself —
  authority is evaluated per-request via `role_can()` at the time of the action;
  there is no time-bound or ticket-based escalation mechanism documented or
  implemented.
- Any future escalation mechanism (e.g., temporary elevated access, break-glass
  patterns) is **not currently implemented** and is not authorized by this
  reconciliation — it would require a separate, explicit decision.

## 6. Deprecated Authority Models

| Model | Status | Evidence |
|---|---|---|
| Hardcoded `OWNER` string-literal bypass inside delegation checks | **DEPRECATED / REMOVED** | Confirmed absent via `grep "normalized_actor == \"OWNER\""` — zero matches in current `roles.py` |
| Alternative hierarchy ordering proposed in `RBAC_HIERARCHY_DECISION.md` (the non-selected option) | **DEPRECATED / NOT ADOPTED** | Superseded by the data-driven rank model actually merged |
| Pre-recovery "old cross-tenant User Management" authorization path (`OWNER_PLATFORM_REMAINING_WORK.md`'s description of the live-`main` predecessor) | **DEPRECATED / REPLACED** | Replaced by the merged Staff Management/RBAC recovery scope (PR #91) |

## 7. Files Implementing Authority

- `backend/app/core/roles.py` — `ROLE_AUTHORITY_RANK`, `role_can()`,
  `PLATFORM_PERMISSION_MATRIX` (core authority logic)
- `sns-emr-frontend` equivalent — `authorization.ts` (frontend route-gate,
  broadened per approved "Option A" to any platform-scope role, not OWNER-only)
- Consumers: `owner_admin.py` (backend staff-management endpoints), the
  `UserManagement.jsx`/`AuditLogs.jsx` frontend pages that call into these gates

*(This list reflects files already identified in the reviewed recovery
documents; no new repository scan was performed to compile it.)*

## 8. Remaining Gaps

1. **Second-reviewer sign-off** on the merged `roles.py` change — not confirmed
   recorded anywhere (non-blocking governance item; see Decision Register #1).
2. **Interim tier-7 role placement** for `PLATFORM_AI_MANAGEMENT` /
   `PLATFORM_OPERATIONS` — awaiting formal ratification (Decision Register #2).
3. **No escalation/break-glass mechanism** exists — noted as an absence, not
   proposed as new work under this document.
4. **Production role-assignment verification** for the two provisional roles has
   not been confirmed as ever having been run (Decision Register #3).

## Exit Requirement Confirmation

**Exactly ONE authority model exists.** No competing or parallel authority model
was found anywhere in the reviewed documents or the live code. This requirement
is satisfied.
