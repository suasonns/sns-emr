# Phase 1A — Reconciliation Report

Status: Planning/reconciliation only. No code, schema, or migration changes made
under this document.

## Required Decisions

### Decision A — Repository recovery status
**Selected: READY WITH CONDITIONS**
Staff Management/RBAC/Password Setup/Audit Logs recovery scope is merged
(PR #91, commit `6f456ab`, plus hotfix `4182f0f` — both confirmed ancestors of
`HEAD` via `git merge-base --is-ancestor`). Condition: one non-blocking governance
item remains open — no document confirms the second-reviewer sign-off on
`roles.py` was ever recorded (see Decision Register item 1).

### Decision B — Owner Platform status
**Selected: partially authoritative**
5 of 9 nav sections are COMPLETE (Dashboard, Agency Management, System Health,
Staff Management, Audit Logs — the last two per the now-confirmed PR #91 merge).
4 sections remain PARTIAL/NOT STARTED and explicitly pending Figma redesign or
net-new backend work (Analytics, Billing & Licensing, Settings, AI Command
Center), per `OWNER_PLATFORM_ROADMAP_STATUS.md` / `OWNER_PLATFORM_REMAINING_WORK.md`.

### Decision C — Tenant Platform status
**Selected: deferred**
ADR-004 ("Tenant Platform Deferred Until Owners Platform Complete") is Accepted
and unmodified. Its three gate conditions (Owners Platform stabilization
complete / roadmap complete / backlog reviewed) are not yet all satisfied — Owner
Platform is only partially complete per Decision B. No superseding ADR exists.

### Decision D — RNICA status
**Selected: design only**
`RNICA_REDESIGN_SOURCE_OF_TRUTH.md`, `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`, and
`RNICA_NARRATIVE_FIELDS_ANALYSIS.md` are target-state design/analysis documents.
None contains language authorizing implementation to begin now. Because RNICA is
Tenant Platform scope, it is additionally gated by ADR-004 (Decision C) — design
work may continue, but implementation is not authorized until that gate clears.

### Decision E — AI status
**Selected: foundation only**
No AI Command Center backend exists anywhere in the codebase (static UI shell,
`readOnly` input, zero API wiring — per `OWNER_PLATFORM_REMAINING_WORK.md`). AI
work is also Tenant Platform-adjacent intelligence scope gated by ADR-004. No
document authorizes implementation beyond design/roadmap discussion.

### Decision F — Authority Model
**Selected: single authority model, single RBAC hierarchy, single permission strategy — all three now exist as one coherent set**
- Single RBAC hierarchy: `ROLE_AUTHORITY_RANK`, data-driven, confirmed live in
  `backend/app/core/roles.py` (no hardcoded delegation-exception bypass — `grep`
  returned zero matches).
- Single authority model: `role_can()` / `PLATFORM_PERMISSION_MATRIX`, deny-by-default
  for all non-OWNER roles; OWNER's own unconditional grant is a deliberate,
  documented architectural exception (not a residual defect).
- Single permission strategy: rank-comparison based (`actor_rank >= target_rank`),
  replacing the former hardcoded string-literal exception.

---

## Required Outputs

### Output 1 — Authoritative Recovery Position
Staff Management, RBAC, Password Setup, and Audit Logs recovery work is **merged
into `main`** (PR #91 `6f456ab` + dependency-closure hotfix `4182f0f`, both
confirmed ancestors of current `HEAD`). This supersedes every earlier "blocked" /
"high risk" / "do not merge" document in the recovery set — those documents
describe resolved, historical findings, not a live blocking condition.

### Output 2 — Authoritative Readiness Position
Owner Platform is **NOT fully complete**. 5 of 9 sections are complete (including
the now-merged RBAC/Staff Mgmt/Audit Logs scope); 4 sections (Analytics, Billing &
Licensing, Settings, AI Command Center) remain PARTIAL/NOT STARTED, each
explicitly requiring Figma redesign (or, for AI Command Center, net-new backend
architecture) before further implementation, per standing user directive recorded
in `OWNER_PLATFORM_ROADMAP_STATUS.md`.

### Output 3 — Authoritative RBAC Position
The data-driven `ROLE_AUTHORITY_RANK` model in `backend/app/core/roles.py` is
final. No further RBAC hierarchy decision is outstanding. One non-code
governance item remains open (second-reviewer sign-off — see Decision Register).

### Output 4 — Authoritative Authority Map Position
`role_can()` + `PLATFORM_PERMISSION_MATRIX`, rank-based, deny-by-default with a
documented OWNER exception, is the single live authority model. Tenant Platform
authority-map design documents (e.g. `PATIENT_CHART_AUTHORITY_MAP.md`) describe a
**future target state only** and do not describe or supersede the currently
implemented Owner Platform authority model.

### Output 5 — Authoritative Implementation Sequence
1. Close the one open governance item (second-reviewer sign-off on `roles.py`) —
   documentation/process action only, no code change.
2. Continue/complete the remaining 4 Owner Platform sections in the order already
   recommended in `OWNER_PLATFORM_ROADMAP_STATUS.md` §6 (Settings scope →
   Settings Figma → Analytics Figma → Billing & Licensing Figma → AI Command
   Center Figma+backend), each gated on its own Figma approval per standing
   directive.
3. Only after Owner Platform is fully COMPLETE (all 9 sections) does ADR-004's
   gate clear, at which point Tenant Platform work (RNICA implementation, AI
   Command Center backend, evidence/narrative intelligence) may begin — subject
   to a fresh authorization at that time, not implied by this reconciliation.

This sequence is a restatement of the already-existing, already-approved
ordering found in the source documents — it is not a new architecture or a new
plan.

---

## Contradictions Found vs. Resolved

| # | Contradiction (as it appeared before direct review) | Resolved? | How |
|---|---|---|---|
| 1 | RBAC hierarchy allegedly unresolved between "blocked" and "ready" docs | Resolved | Live code confirms the "ready" position; no bypass present |
| 2 | Recovery branch allegedly unmerged per Owner Platform status docs | Resolved | `git` confirms PR #91 + hotfix merged and ancestors of `HEAD` |
| 3 | "DO NOT MERGE" recommendation vs. later "READY FOR MERGE" verdict | Resolved | Time-ordered: blocker (`authorization.ts`) was fixed and approved between the two documents |
| 4 | Authority model — is OWNER's bypass a defect or by design? | Resolved | Only the *delegation-exception* bypass was a defect (fixed); OWNER's own root grant is an accepted, unchanged architectural choice |

No CONFLICTING documents remain in the reviewed set (see
`PHASE1A_DOCUMENT_REVIEW_MATRIX.md`).
