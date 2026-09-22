# OWNER PLATFORM FOUNDATION RELEASE PLAN

**Date:** 2026-09-15
**Source branch:** `recovery/copilot-session-2026-09-14`
**Status:** Planning document only. **No commit. No merge. No PR.**

This plan extends `FUNCTIONAL_MERGE_EXECUTION_PLAN.md` beyond
merge → validate to the full lifecycle required before the Owner Platform
Foundation can be declared complete:

**MERGE → VALIDATE → DEPLOY VALIDATION → BASELINE CREATION → FREEZE →
OWNER PLATFORM FOUNDATION COMPLETE**

Scope: Staff Management, RBAC, Password Setup, Audit Logs (Phase 1
functional merge) only. Branding (Phase 2) and Documentation/Governance
(Phase 3) are separate, subsequent reviews and are not part of this
release sequence.

---

## 1. Functional Merge Sequence (Phase 1)

Single PR, ordered internal commits, keeping the functionally-coupled
components together as one unit (per your directive — RBAC, Staff
Management, Password Setup, Audit Logs, Owner Admin API, Permission
Grants, Account Types, Departments, Job Titles, Platforms, associated
migrations/tests, and `authorization.ts`):

1. **Migrations** (5, in dependency order):
   `um2s1a2f3f4b5` → `um2a1c2c3o5u6` → `um2b1c2c3o5u7` → `um2c1c2c3o5u8` → `um2d1c2c3o5u9`
2. **Core domain modules:** `account_types.py`, `departments.py`,
   `job_titles.py`, `platforms.py`
3. **`roles.py`** — **HIGH IMPACT** (authorization engine, RBAC hierarchy,
   permission evaluation, delegation authority). Its own reviewable commit,
   elevated-review code per your standing classification.
4. **`role_guards.py`**, **`protected_tenants.py`**
5. **`auth.py`** (`VALID_ROLES` extension)
6. **Models:** `models/__init__.py`, `staff_permission_grant.py`, `user.py`
7. **`owner_admin.py`** (Owner Admin API)
8. **`admin_bootstrap_service.py`**
9. **Backend tests** (land with the code they cover, not separated):
   `test_owner_platform_rbac_matrix.py`,
   `test_owner_platform_staff_delegation.py`,
   `test_owner_platform_staff_lifecycle.py`,
   `test_owner_platform_staff_profile.py`,
   `test_owner_audit_logs.py`, `test_password_setup_flow.py`,
   `test_treatment_identity_migration.py`
10. **Frontend:** Owner UI (`App.tsx`, `ownerAdmin.ts`,
    `OwnerDashboard.jsx`, `accessLevels.js`, `auditCategories.js`,
    `AddStaffModal.jsx`, `AuditEventDrawer.jsx`, `StaffProfileDrawer.jsx`,
    `AuditLogs.jsx`, `UserManagement.jsx`, `OwnerShell.jsx`), Password Setup
    UI (`SetPasswordPage.tsx`), and `authorization.ts` — merged together as
    the final step, since these depend on the backend endpoints above
    already being present.

**Explicitly not part of this sequence:** Phase 2 (branding) and Phase 3
(governance/documentation) files — separate reviews, separate merges.

---

## 2. Validation Sequence

Executed against `main` immediately after the Phase 1 merge lands (not the
isolated recovery worktree, since `main` may have advanced since the
recovery branch's fork point):

1. **Backend — scoped suite:**
   `test_owner_platform_rbac_matrix.py`,
   `test_owner_platform_staff_delegation.py`,
   `test_owner_platform_staff_lifecycle.py`,
   `test_owner_platform_staff_profile.py`,
   `test_owner_audit_logs.py`, `test_password_setup_flow.py`,
   `test_treatment_identity_migration.py` — all must pass, 0 failures.
2. **Backend — full suite:** run the entire backend test suite (not just
   this scope) via `run_isolated_tests.py` with no path filter, to catch
   any interaction with unrelated `main` changes.
3. **Migration check:** `alembic upgrade head` against `main`'s actual
   current schema state must reach `um2d1c2c3o5u9` cleanly.
4. **Frontend build:** `npm run build` — 0 new TypeScript errors beyond
   the pre-existing, unrelated `FacilityCollectionsReportPage.tsx` errors.
5. **Frontend lint:** `npm run lint` — parity with the 78-problem baseline
   (no net-new issues).
6. **Manual smoke check:** log in as `OWNER` and as one non-OWNER platform
   role (e.g. `PLATFORM_SUPPORT`); confirm Staff Management (`/owner/users`)
   and Audit Logs (`/owner/audit-logs`) load and function per their
   approved design; confirm the `/auth/set-password` flow completes
   end-to-end for a freshly issued reset link.

**Gate:** all of the above must pass before proceeding to Deploy
Validation. Any failure halts progression and triggers the rollback
procedure in `FUNCTIONAL_MERGE_EXECUTION_PLAN.md` §5.

---

## 3. Deployment Validation Sequence

Distinct from the pre-deploy validation above — this validates the
**deployed** environment, not just the merged source:

1. **Build artifact parity:** confirm the deployed build was produced from
   the exact merged commit (no stale cache, no partial deploy) — verify
   deployed commit SHA matches the merge commit.
2. **Database migration applied in the deploy target:** confirm the
   deployed database's Alembic head matches `um2d1c2c3o5u9` (same check as
   §2.3, but against the actual deployment target, not a local/CI ephemeral
   database).
3. **Live smoke test against the deployed environment:**
   - `OWNER` login succeeds; Staff Management roster loads with real data.
   - A non-OWNER platform role (e.g. `PLATFORM_SUPPORT`) can log in and is
     correctly scoped (cannot exceed its granted `staff.*` capabilities).
   - Audit Logs page loads, filters function, free-text search returns
     expected results.
   - `/auth/set-password` end-to-end flow works against a real
     admin-issued reset link in the deployed environment (not just the
     test suite).
4. **Authorization spot-check in production/staging:** confirm a tenant
   user (non-platform role) cannot reach `/owner/*` routes or API
   endpoints — re-verify the tenant-isolation boundary in the actual
   deployed environment, not only in unit tests.
5. **Rollback readiness confirmed:** verify the previous deployment
   artifact/migration state is still available and the rollback procedure
   (`FUNCTIONAL_MERGE_EXECUTION_PLAN.md` §5) is executable against this
   specific deployment target before declaring deploy validation complete.

**Gate:** all of the above must pass in the actual deployment target
before proceeding to Baseline Creation. This step cannot be satisfied by
local/CI validation alone.

---

## 4. Baseline Creation Process

Once Deploy Validation passes:

1. **Tag the release:** create an immutable reference (e.g. a git tag or
   release marker) pointing at the exact merged/deployed commit for Staff
   Management, RBAC, Password Setup, and Audit Logs.
2. **Record the RBAC hierarchy as the canonical baseline:** capture the
   approved 12-role hierarchy (`ROLE_AUTHORITY_RANK` in `roles.py`) and the
   full `PLATFORM_PERMISSION_MATRIX` as the documented, versioned baseline
   permission model — this becomes the reference state for any future
   change (additions require an explicit new decision, not silent drift).
3. **Record the reserved-role decision:** document
   `PLATFORM_AI_MANAGEMENT` / `PLATFORM_OPERATIONS` as retained, reserved,
   interim-tier-7 roles (per your ROLE DECISION) as part of this baseline,
   so future work on AI Command Center / System Health Operations starts
   from a documented state, not a rediscovered one.
4. **Snapshot validation evidence:** archive the validation results from
   §2 and §3 (test run output, build/lint results, migration head,
   deployment smoke-test results) alongside the baseline tag, so the
   baseline is auditable later.
5. **Update `OWNER_PLATFORM_ROADMAP_STATUS.md`:** move Staff Management,
   RBAC, Password Setup, and Audit Logs from "FUNCTIONALLY COMPLETE —
   AWAITING MERGE REVIEW" to "COMPLETE" in the roadmap tracking document,
   reflecting the now-merged and deployed state.
6. **Retire the recovery worktree/branch:** only after the baseline is
   recorded — archive `recovery/copilot-session-2026-09-14` and its
   worktree, since its contents now live on `main` and are captured in the
   baseline tag/snapshot.

---

## 5. Freeze Process

Once the baseline is created:

1. **Lock the architecture surface:** the RBAC hierarchy, permission
   matrix, and role set (`PLATFORM_ROLES`, `ROLE_AUTHORITY_RANK`,
   `PLATFORM_PERMISSION_MATRIX`) for Staff Management/RBAC become frozen —
   any further change requires a new explicit decision/approval cycle, not
   an incidental edit alongside unrelated work.
2. **Lock the approved design surface:** Staff Management's and Audit
   Logs' approved designs (already in use, not redesigned this effort)
   are confirmed as the frozen reference design for these two sections —
   no alternate layouts, no silent redesign, consistent with your standing
   "follow the approved design system" rule.
3. **Publish the frozen navigation state:** record the current Owner
   Platform navigation (`OwnerDashboard.jsx` `NAV_ITEMS`) as the frozen
   baseline for the sections covered by this release (Dashboard, Agency
   Management, System Health, Staff Management, Audit Logs) — the 4
   remaining sections (Analytics, Billing & Licensing, Settings, AI
   Command Center) are explicitly outside the freeze and remain open for
   Figma-first redesign.
4. **Communicate the freeze:** the frozen surfaces above are not to be
   touched again except through a deliberate, reviewed change process —
   this is the point at which "Owner Platform Foundation" transitions from
   active development to a stable, documented reference state.

---

## 6. Criteria For Declaring "Owner Platform Foundation Complete"

All of the following must be true simultaneously:

1. Phase 1 functional merge (§1) has landed on `main`.
2. Post-merge validation (§2) has passed in full, with 0 failures.
3. Deployment validation (§3) has passed against the actual deployed
   environment, not just local/CI checks.
4. Baseline creation (§4) is complete: release tagged, RBAC hierarchy and
   permission matrix documented as canonical, reserved-role decision
   recorded, validation evidence archived, roadmap status updated, and the
   recovery branch/worktree retired.
5. Freeze (§5) is complete: architecture surface locked, approved design
   surface locked, navigation state published as frozen for the 5
   completed sections.
6. No open CRITICAL or HIGH-severity security findings remain in the
   frozen surface (per prior security review passes — none currently
   open).
7. The one previously-open item — `PLATFORM_AI_MANAGEMENT` /
   `PLATFORM_OPERATIONS` seniority-tier placement — is either ratified at
   its current interim tier or explicitly redecided (not left ambiguous)
   before the freeze in §5 is finalized.

**Only when all 7 are true** may the status be marked:

## OWNER PLATFORM FOUNDATION COMPLETE

This is distinct from, and does not imply, **OWNER PLATFORM COMPLETE** —
the latter additionally requires Analytics, Billing & Licensing, Settings,
and AI Command Center to each go through Figma-first redesign and
implementation, per your standing instruction. Those four sections remain
untouched and unscheduled by this release plan.

---

## Status Recap (unchanged by this document)

| Item | Status |
|---|---|
| Recovery | COMPLETE |
| Staff Management | READY FOR FUNCTIONAL MERGE |
| RBAC | READY FOR FUNCTIONAL MERGE |
| Password Setup | READY FOR FUNCTIONAL MERGE |
| Audit Logs | READY FOR FUNCTIONAL MERGE |
| Owner Platform Foundation | READY FOR FUNCTIONAL MERGE REVIEW |
| Owner Platform (overall) | NOT COMPLETE — Analytics, Billing & Licensing, Settings, AI Command Center remain |

**No commit, merge, or PR performed.** This release plan is for your
review; work stops here.
