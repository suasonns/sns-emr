# Owner Platform Gap Report

Read-only. No code changed. Synthesizes remaining open items from all prior recovery reports.

## What remains unfinished

1. **RBAC hierarchy ordering unresolved** — recovered tiering (Owner > Admin > Security/
   Compliance/Billing/AI > Operations/Developer/DevOps/Implementation/QA > Support/Customer
   Service > Auditor) does not match the ordering previously discussed (Owner > Admin > Customer
   Service > Support > Developer). See `RBAC_HIERARCHY_DECISION.md` — needs an explicit decision,
   not code.
2. **`/users` endpoint semantic replacement undecided** — `owner_admin.py`'s roster query changed
   from cross-tenant to platform-staff-only. Needs a product decision: keep as one replaced
   route, or split into two routes so nothing existing silently loses functionality.
3. **`UserManagement.jsx` / `AuditLogs.jsx` full-content rewrites unreconciled** — both pages
   solve materially different problems than their current `main` counterparts; no line-level
   merge is possible, only a manual product/engineering decision on which behavior wins.
4. **Standalone Audit Logs UX design sign-off status unclear** — the recovered checkpoint doc
   says this page was "WAITING FOR DESIGN REVIEW," but code postdating that note exists anyway.
   Needs confirmation of whether design review actually happened after the checkpoint note was
   written.

## What remains missing (zero implementation found)

- **Dedicated invitation lifecycle** (pending-invite state, resend, cancel, never-activated
  tracking) — `AddStaffModal.jsx` explicitly notes this doesn't exist; invite and add-staff share
  one flow today.
- **Dedicated password-setup backend test coverage** — no test file among the 46 recovered files
  targets the set-password flow specifically.
- **Security Monitoring / Workforce Analytics / Privileged Access Review** sections referenced in
  `UserManagement.jsx` comments — explicitly deferred, not implemented in this recovery.
- **Dedicated service-account/API-client creation surface** — intentionally not built; both flow
  through the shared Add Staff modal per the recovered checkpoint doc.

## What still blocks completion

1. **`authorization.ts` broadened owner-route access** — blocked pending a page-by-page audit of
   every pre-existing (non-recovered) `/owner/*` page for independent server-side action gating
   (`OWNER_PLATFORM_SECURITY_REVIEW.md` #1).
2. **`roles.py` hardcoded OWNER superuser bypass** — not a blocking defect by itself (matches
   existing `is_owner_role()` precedent), but blocks a strict "no hardcoded owner authority"
   compliance claim until an explicit accept/redesign decision is made.
3. **No frontend build ever run** — blocks confidence in every frontend file listed
   REQUIRES REVIEW or HIGH RISK in `OWNER_PLATFORM_MERGE_PLAN.md`.

## What still requires UI work

- Reconciling `UserManagement.jsx` and `AuditLogs.jsx` with whatever main currently needs
  preserved (if anything) from the pre-recovery versions.
- Confirming `OwnerDashboard.jsx`/`OwnerShell.jsx` render correctly against current `main`'s
  dependencies (untested since recovery — no frontend build has been run).
- Building the deferred invitation lifecycle UI, if/when prioritized.

## What still requires backend work

- Deciding and implementing the `/users` roster resolution (single route vs. split routes).
- If the RBAC hierarchy decision changes tier assignments, updating `ACCESS_LEVEL_FOR_ROLE` and/or
  `PLATFORM_PERMISSION_MATRIX` to match (not yet done — awaiting decision).
- If the OWNER hardcoding is deemed unacceptable, designing the database-driven floor-permission
  alternative described in `OWNER_PLATFORM_SECURITY_REVIEW.md` #2.

## What still requires testing

- Full frontend validation: `npm install && tsc --noEmit && npm run lint && npm run build` — never
  run against the recovery worktree.
- A dedicated password-setup flow test.
- Regression testing of the `/users` endpoint's old cross-tenant behavior against any real
  consumer, if that behavior is meant to be preserved.
- Re-running `test_treatment_identity_migration.py`'s `HEAD_REVISION` assumption against main's
  actual current Alembic head at merge time (main may have advanced independently).

## Summary

No area is entirely unimplemented. The gaps are concentrated in three places: (1) two open
decisions (RBAC hierarchy ordering, `/users` route semantics) that block merge but not further
recovery, (2) one audit that hasn't been performed (owner-page-by-page authorization gating), and
(3) the frontend build/test pipeline, which has never been executed against this recovery at all.
