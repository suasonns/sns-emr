# Phase 1B Execution Package — Owner Platform Baseline Freeze

Status: PLANNING ONLY. No code, schema, or migration changes performed under
this document. Execution of the freeze requires a separate, explicit
authorization.

---

## 1. Phase 1B Objective

Formally freeze the reconciled Owner Platform recovery baseline (Staff
Management, RBAC, Password Setup, Audit Logs) as the accepted state of `main`,
using the already-merged commits identified in Phase 1A. Phase 1B does not add,
change, or re-review any code — it certifies that what is already merged is the
accepted baseline going forward.

## 2. Scope of Baseline Freeze

- The merge of `review/staff-management-rbac-auditlogs` into `main` via PR #91
  (merge commit `6f456ab`, 2026-09-15).
- The follow-up hotfix `4182f0f` ("restore PR #91 dependency closure"), also
  merged and confirmed an ancestor of current `HEAD`.
- The resulting live state of `backend/app/core/roles.py`
  (`ROLE_AUTHORITY_RANK`, `role_can()`, `PLATFORM_PERMISSION_MATRIX`) and its
  frontend counterpart (`authorization.ts`), plus the Staff Management/Audit
  Logs UI and backend endpoints these commits introduced.
- This is a **freeze of already-existing, already-merged history** — no new
  commit is created by Phase 1B itself beyond, at most, a tag/marker
  identifying the freeze point (subject to Phase 1B execution authorization).

## 3. Exact Repositories/Files Included

- Repository: `suasonns/sns-emr`, branch `main` at/after commit `4182f0f`
  (which is itself after `6f456ab`).
- Files introduced/modified by commit `3364a13` and its merge (per
  `PHASE1_RELEASE_CANDIDATE.md`'s 38-file list and
  `OWNER_PLATFORM_MERGE_REVIEW.md`'s 47-file list — the RBAC/Staff
  Management/Audit Logs/Password Setup change set), principally:
  - `backend/app/core/roles.py`
  - `backend/app/api/owner_admin.py` (and related Staff Management endpoints)
  - Staff Management / Audit Logs migration(s) in `backend/alembic/versions/`
    belonging to that recovery batch
  - `sns-emr-frontend/src/owner/pages/UserManagement.jsx`
  - `sns-emr-frontend/src/owner/pages/AuditLogs.jsx`
  - `sns-emr-frontend/src/owner/utils/authorization.ts` (or equivalent path)
  - Associated backend/frontend test files for this scope

## 4. Exact Repositories/Files Excluded

- **All 84 currently uncommitted changes in this session's working tree**
  (confirmed via `git status --short` at time of this planning, 84 entries) —
  these are unrelated in-progress work (Election Addendum billing models,
  RNICA assessment models, new unrelated Alembic migrations,
  `registry.py`/`idg_review.py` changes, etc.) and are **explicitly out of
  scope** for this freeze. They must not be swept into any Phase 1B commit or
  tag.
- Any Tenant Platform, RNICA, AI Command Center, Billing Platform, or workflow
  code or documents — none of this exists as implementation yet and none of it
  is part of the reconciled recovery baseline.
- The 4 remaining PARTIAL/NOT-STARTED Owner Platform sections (Analytics,
  Billing & Licensing, Settings, AI Command Center) — unchanged by, and not
  part of, this freeze.
- Any other branch not identified above (`recovery/copilot-session-2026-09-14`,
  `docs/rnica-baseline-governance`, `fix/repository-zero-failure-baseline`,
  etc.) — out of scope unless separately authorized.

## 5. Recovery Baseline Definition

The "recovery baseline" is defined as: **the state of `main` immediately after
commit `4182f0f`**, i.e., after both PR #91's merge (`6f456ab`) and its
dependency-closure hotfix are applied, and before any of the 84 currently
uncommitted, unrelated changes in this session's working tree. This is the
single reconciled point Phase 1A concluded is the authoritative recovery
position (GOV-001).

## 6. Verification Procedure

1. Confirm `git merge-base --is-ancestor 4182f0f main` (and `HEAD` of the
   branch being frozen) is true.
2. Confirm `backend/app/core/roles.py` at that commit contains no hardcoded
   `OWNER` delegation-exception bypass (already verified via `grep` in Phase
   1A; re-verify at the exact freeze commit if a different ref is used).
3. Run the backend/frontend test suites scoped to Staff Management/RBAC/Audit
   Logs at the freeze commit and confirm they pass (per
   `OWNER_PLATFORM_FINAL_READINESS.md`'s already-recorded green results — Phase
   1B would re-confirm, not re-design, these results).
4. Confirm `git status --short` at the freeze commit shows no uncommitted
   changes within the included file set (§3).

## 7. Rollback Procedure

- Because Phase 1B freezes an already-merged, already-existing commit, no new
  code is introduced that requires rollback under normal operation.
- If a freeze marker (e.g., a git tag) is created during Phase 1B execution and
  later found to be incorrect, rollback is simply deleting that tag/marker —
  it does not touch `main`'s commit history.
- If a defect is later discovered in the frozen baseline itself, rollback would
  be a standard `git revert` of the relevant commit(s) — this is a Phase 2+
  concern, not a Phase 1B action.

## 8. Acceptance Criteria

- The verification procedure (§6) passes in full.
- No file outside §3's included set is touched by the freeze action.
- The 84 currently uncommitted, unrelated changes remain untouched and
  uncommitted (or are handled entirely separately, outside Phase 1B).
- A written confirmation exists that the freeze point is `4182f0f` (or later,
  if a subsequent, already-merged, in-scope commit is identified before
  execution).

## 9. Exit Criteria

Phase 1B is complete when:
- The freeze point is verified and recorded (e.g., via a tag, changelog entry,
  or equivalent marker — mechanism to be decided at execution time, not this
  planning stage).
- No code, schema, or migration changes have been introduced beyond what was
  already merged.
- The Decision Register's remaining open items (second-reviewer sign-off,
  tier-7 ratification) are either closed or explicitly carried forward as
  non-blocking to Phase 2.

## 10. Preconditions for Phase 2

- Phase 1B freeze verified complete per §9.
- Owner Platform completion status re-confirmed (still 5/9 sections — Phase 1B
  does not change this; Phase 2 entry does not require full Owner Platform
  completion unless Phase 2's specific scope is Tenant Platform work, in which
  case ADR-004's gate (GATE-001) must also be satisfied first).
- Explicit, separate human authorization to begin whatever Phase 2 scope is
  chosen — this package does not itself authorize Phase 2.

---

## Summary (for quick reference)

- **Phase 1B objective:** Certify the already-merged PR #91 + hotfix
  (`6f456ab` → `4182f0f`) as the frozen Owner Platform RBAC/Staff
  Management/Audit Logs baseline.
- **Freeze scope:** That merged commit range and its file set only.
- **Excluded scope:** All 84 current uncommitted/unrelated working-tree
  changes; all Tenant Platform/RNICA/AI/Billing/workflow work; the 4 remaining
  incomplete Owner Platform sections; all other branches.
- **Acceptance criteria:** Verification steps pass; no out-of-scope files
  touched; uncommitted unrelated work left untouched.
- **Exit criteria:** Freeze point recorded; no new code/schema/migration
  introduced; open governance items closed or explicitly deferred.
- **Recommendation:** Planning package ready. Awaiting separate, explicit
  authorization before executing the freeze.
