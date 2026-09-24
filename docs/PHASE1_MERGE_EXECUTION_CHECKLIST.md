# PHASE 1 MERGE EXECUTION CHECKLIST

**Date:** 2026-09-15
**Source branch:** `recovery/copilot-session-2026-09-14`
**Target branch:** `main`
**Scope:** Staff Management, RBAC, Password Setup, Audit Logs only.
**Status:** Execution checklist only. **No commit. No merge. No PR.**

---

## 1. Exact Branch Merge Path

```
recovery/copilot-session-2026-09-14
        ↓  (staging cut — recovery branch stays immutable)
review/staff-management-rbac-auditlogs
        ↓  (single pull request)
main
```

- The recovery branch (`recovery/copilot-session-2026-09-14`) is **never**
  merged from directly. It is preserved permanently, untouched, as
  recovery evidence.
- A new branch, `review/staff-management-rbac-auditlogs`, is cut from
  `recovery/copilot-session-2026-09-14` at the exact Phase 1 scope (the 38
  files in §2 only — no branding, no governance/documentation files). This
  staging branch is what actually gets reviewed and merged.
- Single pull request from `review/staff-management-rbac-auditlogs` into
  `main`, one merge event, ordered internal commits (see §2). No squash of
  unrelated history — the 5 migrations and their dependent code land as
  the ordered commit sequence below so `git bisect`/rollback stays
  meaningful.
- `recovery/copilot-session-2026-09-14` and its worktree
  (`C:\Users\rdsua\Desktop\copilot-recovery-2026-09-15\recovery-worktree`)
  remain immutable and are **not** deleted/archived at merge time — they
  persist indefinitely as the permanent recovery record. Only the
  short-lived `review/staff-management-rbac-auditlogs` branch is retired
  after §6 baseline creation completes.
- Excluded from this path: Phase 2 branding files, Phase 3
  governance/documentation files — separate branches/PRs, separate review.

---

## 2. Exact Files Included (38)

**A. Migrations (5)**
1. `backend/alembic/versions/um2s1a2f3f4b5_add_department_notes_updated_by_to_users.py`
2. `backend/alembic/versions/um2a1c2c3o5u6_add_account_type_to_users.py`
3. `backend/alembic/versions/um2b1c2c3o5u7_add_identity_fields_to_users.py`
4. `backend/alembic/versions/um2c1c2c3o5u8_add_platform_to_users.py`
5. `backend/alembic/versions/um2d1c2c3o5u9_add_staff_status_and_permission_grants.py`

**B. RBAC core (5)**
6. `backend/app/core/roles.py` — **HIGH IMPACT**
7. `backend/app/core/account_types.py` (new)
8. `backend/app/core/departments.py` (new)
9. `backend/app/core/job_titles.py` (new)
10. `backend/app/core/platforms.py` (new)

**C/D. Guards (2)**
11. `backend/app/core/role_guards.py`
12. `backend/app/core/protected_tenants.py`

**E. Auth (1)**
13. `backend/app/core/auth.py`

**F. Models (3)**
14. `backend/app/models/__init__.py`
15. `backend/app/models/staff_permission_grant.py` (new)
16. `backend/app/models/user.py`

**G/H. API + bootstrap (2)**
17. `backend/app/api/owner_admin.py`
18. `backend/app/services/admin_bootstrap_service.py`

**I/J/K. Tests (7)**
19. `backend/tests/test_owner_platform_rbac_matrix.py` (new)
20. `backend/tests/test_owner_platform_staff_delegation.py` (new)
21. `backend/tests/test_owner_platform_staff_lifecycle.py` (new)
22. `backend/tests/test_owner_platform_staff_profile.py` (new)
23. `backend/tests/test_treatment_identity_migration.py`
24. `backend/tests/test_owner_audit_logs.py` (extended)
25. `backend/tests/test_password_setup_flow.py` (new)

**L/M/N. Frontend (13)**
26. `sns-emr-frontend/src/App.tsx`
27. `sns-emr-frontend/src/api/ownerAdmin.ts`
28. `sns-emr-frontend/src/owner/OwnerDashboard.jsx`
29. `sns-emr-frontend/src/owner/accessLevels.js` (new)
30. `sns-emr-frontend/src/owner/auditCategories.js` (new)
31. `sns-emr-frontend/src/owner/components/AddStaffModal.jsx` (new)
32. `sns-emr-frontend/src/owner/components/AuditEventDrawer.jsx` (new)
33. `sns-emr-frontend/src/owner/components/StaffProfileDrawer.jsx` (new)
34. `sns-emr-frontend/src/owner/pages/AuditLogs.jsx`
35. `sns-emr-frontend/src/owner/pages/UserManagement.jsx`
36. `sns-emr-frontend/src/owner/shell/OwnerShell.jsx` (new)
37. `sns-emr-frontend/src/pages/SetPasswordPage.tsx` (new; lint-fixed)
38. `sns-emr-frontend/src/utils/authorization.ts`

**Confirmed exclusions:** 5 brand SVGs, `BrandLogo.tsx`,
`PLATFORM_ARCHITECTURE_ROADMAP.md`, `SNS_STAFF_ACCESS_CHECKPOINT.md`,
`.github/copilot-instructions.md`.

---

## 3. Exact Migration Order

```
um2s1a2f3f4b5  (department/notes/updated_by on users)
      ↓
um2a1c2c3o5u6  (account_type on users)
      ↓
um2b1c2c3o5u7  (responsible_owner_id, identity_purpose, identity_scope)
      ↓
um2c1c2c3o5u8  (platform assignment on users)
      ↓
um2d1c2c3o5u9  (staff status + delegated permission grants)   ← head
```

- `alembic upgrade head` must land exactly on `um2d1c2c3o5u9`.
- All 5 are additive only (new nullable columns / new table) — no
  destructive change to a pre-existing column.

---

## 4. Exact Validation Sequence Immediately After Merge

Run against `main` post-merge (not the isolated recovery worktree):

1. Scoped backend tests: `test_owner_platform_rbac_matrix.py`,
   `test_owner_platform_staff_delegation.py`,
   `test_owner_platform_staff_lifecycle.py`,
   `test_owner_platform_staff_profile.py`, `test_owner_audit_logs.py`,
   `test_password_setup_flow.py`, `test_treatment_identity_migration.py`
   — all pass, 0 failures.
2. Full backend suite (`run_isolated_tests.py`, no path filter) — 0
   regressions outside scope.
3. `alembic upgrade head` against `main`'s actual current schema — reaches
   `um2d1c2c3o5u9` cleanly.
4. `npm run build` — 0 new TypeScript errors beyond the pre-existing,
   unrelated `FacilityCollectionsReportPage.tsx` errors.
5. `npm run lint` — parity with the 78-problem baseline (no net-new
   issues).
6. Manual smoke check: `OWNER` login and one non-OWNER platform role
   (e.g. `PLATFORM_SUPPORT`); confirm `/owner/users`, `/owner/audit-logs`,
   and `/auth/set-password` function per approved design.

**Gate:** all 6 must pass before proceeding to §5.

---

## 5. Exact Deployment Validation Sequence

1. Confirm deployed build artifact's commit SHA matches the merge commit.
2. Confirm deployed database's Alembic head = `um2d1c2c3o5u9`.
3. Live smoke test in the deployed environment: `OWNER` login + roster
   load; non-OWNER platform role scoping check; Audit Logs filter/search;
   `/auth/set-password` against a real admin-issued reset link.
4. Authorization spot-check: confirm a tenant (non-platform) user cannot
   reach `/owner/*` routes/endpoints in the deployed environment.
5. Confirm rollback readiness: prior deployment artifact and migration
   downgrade path are available and executable against this target.

**Gate:** all 5 must pass in the actual deployed environment (not
local/CI alone) before proceeding to §6.

---

## 6. Exact Baseline Tag / Checkpoint Strategy

1. Tag the merge/deploy commit with an immutable reference (e.g.
   `owner-platform-foundation-v1`) pointing at the exact merged and
   deployed commit.
2. Record the approved 12-role hierarchy (`ROLE_AUTHORITY_RANK`) and full
   `PLATFORM_PERMISSION_MATRIX` from `roles.py` as the canonical,
   versioned baseline permission model as of this tag.
3. Record the reserved-role decision (`PLATFORM_AI_MANAGEMENT` /
   `PLATFORM_OPERATIONS` — retained, reserved, interim tier 7) as part of
   the tagged baseline.
4. Archive validation evidence from §4 and §5 (test output, build/lint
   results, migration head, deployment smoke-test results) alongside the
   tag.
5. Update `OWNER_PLATFORM_ROADMAP_STATUS.md`: move Staff Management,
   RBAC, Password Setup, Audit Logs from "FUNCTIONALLY COMPLETE —
   AWAITING MERGE REVIEW" to "COMPLETE."
6. Retire only the short-lived `review/staff-management-rbac-auditlogs`
   staging branch after the tag and archived evidence exist.
   `recovery/copilot-session-2026-09-14` is **not** retired — it remains
   permanently as immutable recovery evidence.

---

## 7. Exact Freeze Procedure

1. Lock the architecture surface: `PLATFORM_ROLES`, `ROLE_AUTHORITY_RANK`,
   `PLATFORM_PERMISSION_MATRIX` become frozen — any further change
   requires a new explicit approval cycle, not an incidental edit.
2. Lock the approved design surface: Staff Management's and Audit Logs'
   existing approved designs are confirmed frozen — no redesign, no
   alternate layout.
3. Publish the frozen navigation state (`OwnerDashboard.jsx` `NAV_ITEMS`)
   for the 5 completed sections (Dashboard, Agency Management, System
   Health, Staff Management, Audit Logs). The 4 remaining sections stay
   explicitly outside the freeze, open for Figma-first redesign.
4. Communicate the freeze: the surfaces above move from active
   development to a stable, documented reference state.

---

## 8. Criteria For Declaring "OWNER PLATFORM FOUNDATION COMPLETE"

All 7 must be true simultaneously:

1. Phase 1 merge (§1–§3) landed on `main`.
2. Post-merge validation (§4) passed in full.
3. Deployment validation (§5) passed against the real deployed
   environment.
4. Baseline/checkpoint (§6) complete: tagged, hierarchy/matrix documented,
   reserved-role decision recorded, evidence archived, roadmap updated,
   `review/staff-management-rbac-auditlogs` staging branch retired
   (`recovery/copilot-session-2026-09-14` preserved permanently, not
   retired).
5. Freeze (§7) complete: architecture, design, and navigation surfaces
   locked for the 5 completed sections.
6. No open CRITICAL/HIGH security findings remain in the frozen surface.
7. `PLATFORM_AI_MANAGEMENT` / `PLATFORM_OPERATIONS` tier placement is
   ratified at its interim tier (already done via your ROLE DECISION) —
   not left ambiguous.

**Only when all 7 are true:** `OWNER PLATFORM FOUNDATION COMPLETE`.

This is distinct from **OWNER PLATFORM COMPLETE**, which additionally
requires Analytics, Billing & Licensing, Settings, and AI Command Center
to go through Figma-first redesign and implementation.

---

**No commit, merge, or PR performed.** This checklist is for your review;
work stops here.
