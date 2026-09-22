# Phase 1A — Platform Direction

Status: Planning/reconciliation only. Formalizes the current-vs-target state and
program authorization status established in Phase 1A. This is the bridge
document between Phase 1A and any future Phase 1B authorization — it does not
itself authorize Phase 1B.

## Current State

- **Owner Platform:** 5 of 9 nav sections COMPLETE — Dashboard, Agency Management
  (Tenant Management), System Health (all pre-existing/unchanged on `main`), plus
  Staff Management and Audit Logs (now merged via PR #91 `6f456ab` + hotfix
  `4182f0f`).
- **RBAC/Authority:** Single, live, data-driven model (`ROLE_AUTHORITY_RANK` +
  `role_can()`), formalized in `PHASE1A_AUTHORITY_MODEL.md`. No open code defect;
  one open governance sign-off item.
- **Tenant Platform:** Not started. Deferred under ADR-004.
- **RNICA:** Design/analysis documents exist (`RNICA_REDESIGN_SOURCE_OF_TRUTH.md`
  and related); no implementation.
- **AI Command Center:** Static frontend shell only; zero backend.
- **Billing & Licensing / Analytics / Settings:** Live on `main`, but each PARTIAL
  and explicitly pending Figma redesign approval before further work, per
  standing user directive.

## Target State

- All 9 Owner Platform nav sections COMPLETE, validated (backend tests, frontend
  build/lint), and frozen as a baseline.
- ADR-004's three conditions satisfied (Owner Platform stabilization, roadmap,
  and backlog review all complete), at which point the ADR's gate can be
  formally re-evaluated (and potentially superseded by a follow-up ADR, per
  ADR-004's own "Consequences" section).
- Tenant Platform intelligence work (RNICA implementation, evidence/narrative
  engines, AI Command Center backend) begins only after that gate clears, under
  its own separate, explicit authorization.

## Deferred Programs

| Program | Reason Deferred | Governing Document |
|---|---|---|
| Tenant Platform (all intelligence work) | ADR-004 gate not satisfied | ADR-004 |
| RNICA implementation | Design-only status; also gated by ADR-004 | GOV-004, ADR-004 |
| AI Command Center backend | No backend exists; also gated by ADR-004 | GOV-005, ADR-004 |
| Analytics / Billing & Licensing / Settings redesign implementation | Standing directive requires Figma approval first | `OWNER_PLATFORM_ROADMAP_STATUS.md` |

## Authorized Programs

| Program | Authorization Basis | Scope |
|---|---|---|
| None — no new implementation program is authorized by this reconciliation | Phase 1A is planning/reconciliation only | N/A |

*(Phase 1A explicitly does not authorize any implementation. The "first
implementation task" concept previously discussed in an earlier planning pass
remains a proposal, not an authorization, until a future phase formally approves
it.)*

## Blocked Programs

| Program | Blocker | Unblock Condition |
|---|---|---|
| Tenant Platform / RNICA / AI backend | ADR-004 gate | Owner Platform must reach full COMPLETE status (all 9 sections) |
| Settings / Analytics / Billing & Licensing further implementation | Missing Figma-approved designs | Figma designs must be produced and approved (product/design work, not engineering) |

## Future Sequencing (proposed, not yet ratified — see GOV-007)

1. Close open governance items (sign-off, tier ratification).
2. Complete remaining 4 Owner Platform sections in Figma-first order.
3. Re-evaluate ADR-004 gate once Owner Platform is fully COMPLETE.
4. Separately authorize Tenant Platform/RNICA/AI work at that time.

## Dependencies

- Platform Direction depends on `PHASE1A_GOVERNANCE_REGISTER.md` (GOV-001
  through GOV-007) and `PHASE1A_AUTHORITY_MODEL.md` for its authority-related
  claims.
- Any future Phase 1B (baseline freeze) or Phase 2+ (implementation) decision
  must be evaluated against this document's Deferred/Authorized/Blocked
  classification — it is the single source of truth for "what may proceed now"
  as of this reconciliation.
