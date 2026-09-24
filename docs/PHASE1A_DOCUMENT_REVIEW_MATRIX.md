# Phase 1A — Document Review Matrix

Status: Planning only. No code, schema, or migration changes. Classifications below
are based on documents actually read in this session plus direct `git`/`grep`
evidence (branch ancestry, merge commits, live `roles.py` content) — not on prior
sub-agent summaries.

Classification legend: AUTHORITATIVE / SUPERSEDED / REFERENCE ONLY / CONFLICTING / UNKNOWN

| Area | Document | Position (as written) | Classification | Basis |
|---|---|---|---|---|
| RBAC | `docs/recovery/2026-09-15/rbac-validation.md` | 6/7 checks pass; hardcoded OWNER bypass = FAIL | SUPERSEDED | Finding fixed per later docs; confirmed absent in live `roles.py` via `grep` |
| RBAC | `docs/recovery/2026-09-15/RBAC_SECURITY_REVIEW.md` | 2 findings (route-gate broadening MEDIUM, hardcoded bypass 9/10) | SUPERSEDED | Both findings addressed in later docs; route-gate broadening explicitly approved by user ("Option A") |
| Recovery | `docs/recovery/2026-09-15/HIGH_RISK_CONFLICT_REPORT.md` | 3 files HIGH RISK | SUPERSEDED | Risk items resolved per `OWNER_PLATFORM_MERGE_REVIEW.md` |
| Recovery | `docs/recovery/2026-09-15/FINAL_MERGE_RECOMMENDATION.md` | "DO NOT MERGE" (1 file BLOCKED) | SUPERSEDED | Blocker (`authorization.ts`) resolved; PR #91 subsequently merged |
| RBAC | `docs/recovery/2026-09-15/RBAC_HIERARCHY_DECISION.md` | 2 hierarchy options presented, undecided | SUPERSEDED | Decision made — data-driven `ROLE_AUTHORITY_RANK` model confirmed live in code |
| Recovery/RBAC | `docs/OWNER_PLATFORM_FINAL_READINESS.md` | Staff Mgmt/RBAC/Password Setup/Audit Logs COMPLETE, ready for merge | AUTHORITATIVE | Matches confirmed merged state (PR #91 + hotfix, ancestors of `HEAD`) |
| Recovery | `docs/PHASE1_MERGE_BLOCKERS.md` | No blockers open; 1 governance item (2nd reviewer sign-off) | AUTHORITATIVE | Consistent with merge; governance item remains genuinely open (see Decision Register) |
| Recovery | `docs/PHASE1_RELEASE_CANDIDATE.md` | Commit `3364a13`, branch ready for PR | AUTHORITATIVE | Confirmed: `3364a13` exists, is the tip commit of the merged branch |
| Recovery | `docs/PHASE1_FAILURE_ROOT_CAUSE.md` | 1 test defect fixed, 1 pre-existing failure documented | REFERENCE ONLY | Historical diagnostic record; not a live position |
| Recovery | `docs/OWNER_PLATFORM_MERGE_REVIEW.md` | 47-file list, all risks resolved/accepted, ready for merge | AUTHORITATIVE | Consistent with confirmed merge |
| Owner Platform | `docs/OWNER_PLATFORM_ROADMAP_STATUS.md` | Recovery branch "NOT merged" (dated 2026-09-15) | SUPERSEDED (partially) | Merge-status claim is stale (PR #91 merged same day); the 9-section inventory and "4 sections still pending Figma redesign" content remains AUTHORITATIVE |
| Owner Platform | `docs/OWNER_PLATFORM_REMAINING_WORK.md` | Staff Mgmt/RBAC/Audit Logs "recovered, not merged" (dated 2026-09-15) | SUPERSEDED (partially) | Same as above — merge-status claim stale; remaining-section inventory (Analytics/Billing/Settings/AI) still AUTHORITATIVE |
| ADR | `docs/architecture/adr/ADR-004-tenant-platform-deferred-until-owners-platform-complete.md` | Status: Accepted. Tenant Platform work deferred until Owner Platform stabilization/roadmap/backlog review complete | AUTHORITATIVE | Current, unmodified, no superseding ADR exists |
| Recovery | `docs/recovery/2026-09-15/conflict-analysis.md` | Not read this pass (size) | UNKNOWN | Not required to resolve the reconciliation — the 4 "early" documents already establish the full finding set independently |
| Tenant/RNICA | `docs/tenant-platform/RNICA_REDESIGN_SOURCE_OF_TRUTH.md` | Design/target-state document | REFERENCE ONLY | Describes intended future design; per ADR-004 this authorizes design discussion only, not implementation |
| Tenant/RNICA | `docs/tenant-platform/RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`, `RNICA_NARRATIVE_FIELDS_ANALYSIS.md` | Design/analysis documents | REFERENCE ONLY | Same basis — design artifacts, no implementation-authorization language found in either |
| Authority | `docs/tenant-platform/PATIENT_CHART_AUTHORITY_MAP.md` | Target authority-map design | REFERENCE ONLY | Describes target state for Tenant Platform, gated by ADR-004; not an authorization to implement now |

## Notes

- No document in this matrix is CONFLICTING once read directly — the apparent
  RBAC/recovery conflicts were resolved by the passage of time and a completed
  merge, not by an unresolved disagreement between two currently-live positions.
- The two "SUPERSEDED (partially)" rows are not fully retired: their RBAC/merge
  claims are stale, but their descriptive inventory of the remaining 4 Owner
  Platform sections is still the best available evidence and remains authoritative
  until a fresher inventory is produced.
