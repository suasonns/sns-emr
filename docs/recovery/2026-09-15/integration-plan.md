# Safe Integration Plan

**DO NOT MERGE YET.** This defines the order and validation gates for landing the recovered
`recovery/copilot-session-2026-09-14` work onto `main`, in dependency order, smallest/safest first.

## Batch 1 — Database models & migrations

**Files:**
- `backend/alembic/versions/um2s1a2f3f4b5_add_department_notes_updated_by_to_users.py`
- `backend/alembic/versions/um2a1c2c3o5u6_add_account_type_to_users.py`
- `backend/alembic/versions/um2b1c2c3o5u7_add_identity_fields_to_users.py`
- `backend/alembic/versions/um2c1c2c3o5u8_add_platform_to_users.py`
- `backend/alembic/versions/um2d1c2c3o5u9_add_staff_status_and_permission_grants.py`
- `backend/app/models/user.py`, `backend/app/models/__init__.py`, `backend/app/models/staff_permission_grant.py`
- `backend/app/core/account_types.py`, `departments.py`, `job_titles.py`, `platforms.py`

**Risk:** Low-Medium. All additive columns/tables; no existing column drops or renames observed.
`user.py`/`models/__init__.py` are conflict class C (main has diverged elsewhere in `user.py` too —
confirm current main's HEAD migration is still `um2d1c2c3o5u9`'s direct ancestor before applying,
since `main` may have gained its own migrations since this branch diverged).

**Dependencies:** None (first batch). Everything else depends on this.

**Validation:** ✅ Already verified — full migration chain applies cleanly to `head` on a fresh
isolated Postgres DB (see `build-validation.md`).

**Rollback:** `alembic downgrade -1` per migration is available for 4 of 5 (the batch's last
migration, `um2d1c2c3o5u9`, was itself verified to downgrade cleanly during the isolated test run).
If a downgrade is needed, revert in reverse order.

---

## Batch 2 — Permissions (RBAC core)

**Files:** `backend/app/core/roles.py` (C), `backend/app/core/role_guards.py` (B),
`backend/app/models/staff_permission_grant.py` (A, also in Batch 1)

**Risk:** **Medium-High** — this is the security-critical core. `roles.py` is flagged conflict
class **C** (additive but touches a security-critical module); OWNER superuser logic is hardcoded
(see `rbac-validation.md` item 7 — FAIL). Recommend manual side-by-side review of `roles.py`
against current `main`'s version before taking it, even though the recovered version is largely
additive.

**Dependencies:** Batch 1 (models must exist for permission-grant queries to work).

**Validation:** ✅ `test_owner_platform_rbac_matrix.py` (20/20 passed) and
`test_owner_platform_staff_delegation.py` (17/17 passed) directly cover this batch.

**Rollback:** Revert `roles.py`/`role_guards.py` to main's version; no schema impact (permission
logic is code-only on top of Batch 1's table).

---

## Batch 3 — Authentication

**Files:** `backend/app/core/auth.py` (B — additive `VALID_ROLES` expansion),
`backend/app/core/protected_tenants.py` (B — additive `PLATFORM_TENANT_ID` constant),
`sns-emr-frontend/src/utils/authorization.ts` (**C — flagged for explicit security review**)

**Risk:** **High for the frontend file specifically.** `conflict-analysis.md` flags that the
recovered `authorization.ts` "deliberately broadens owner-route entry to any platform-scope user."
This must be reviewed against the backend RBAC change as a pair, not landed independently — a
frontend-only broadening without the matching backend `allowed_actions` gating would be a real
privilege-escalation risk.

**Dependencies:** Batch 2.

**Validation:** Backend side covered by Batch 2's test suites. Frontend side: **not yet
independently validated** (no `npm install` run — see `build-validation.md`). Do not merge Batch 3
until frontend build/lint/typecheck passes and a reviewer confirms `authorization.ts`'s broadened
route entry is backed by real backend `allowed_actions` checks on every affected page.

**Rollback:** Revert `authorization.ts` to main's stricter version; backend `auth.py`/
`protected_tenants.py` changes are additive and safe to leave or revert independently.

---

## Batch 4 — Platform Owner UI

**Files:** `sns-emr-frontend/src/owner/shell/OwnerShell.jsx` (A),
`sns-emr-frontend/src/owner/OwnerDashboard.jsx` (C),
`sns-emr-frontend/src/components/BrandLogo.tsx` (B), brand SVG assets (A/B),
`sns-emr-frontend/src/App.tsx` (B — adds `/set-password` route),
`sns-emr-frontend/src/pages/SetPasswordPage.tsx` (A)

**Risk:** Medium. `OwnerDashboard.jsx` is conflict class C ("changes shelling, loading behavior,
and delegated-staff access routing") — needs review against current main's dashboard, not a blind
overwrite.

**Dependencies:** Batches 2–3 (routing/authorization must land first).

**Validation:** Not yet run (frontend build pending — see Batch 3 note).

**Rollback:** Revert to main's `OwnerDashboard.jsx`/`OwnerShell.jsx`; `SetPasswordPage.tsx` and its
route are additive and can be reverted independently by removing the one route line in `App.tsx`.

---

## Batch 5 — Staff Management UI

**Files:** `sns-emr-frontend/src/owner/pages/UserManagement.jsx` (**D — high conflict**),
`sns-emr-frontend/src/owner/components/AddStaffModal.jsx` (A),
`sns-emr-frontend/src/owner/components/StaffProfileDrawer.jsx` (A),
`sns-emr-frontend/src/owner/accessLevels.js` (A),
`sns-emr-frontend/src/api/ownerAdmin.ts` (C)

**Risk:** **High.** `UserManagement.jsx` is flagged HIGH conflict — the recovered version
"repurposes it from cross-tenant user listing to SNS Staff & Access," i.e. a different feature
scope than what may currently be on `main`. This is a full-content replacement, not a merge;
confirm main's current `UserManagement.jsx` doesn't contain independent fixes/features that would
be silently dropped.

**Dependencies:** Batches 1–4.

**Validation:** Backend endpoints these UI components call are covered by Batch 2's passing tests.
Frontend UI itself: not yet built/typechecked.

**Rollback:** Revert `UserManagement.jsx` to main's version; new modal/drawer/helper files can be
deleted independently since nothing else on main references them yet.

---

## Batch 6 — Audit Logs

**Files:** `sns-emr-frontend/src/owner/pages/AuditLogs.jsx` (**D — high conflict**),
`sns-emr-frontend/src/owner/components/AuditEventDrawer.jsx` (A),
`sns-emr-frontend/src/owner/auditCategories.js` (A),
`backend/tests/test_owner_audit_logs.py` (A, already validated)

**Risk:** Medium-High (same "full-content overwrite" caution as Batch 5 for `AuditLogs.jsx`).

**Dependencies:** Batches 1–2 (audit data model/permissions).

**Validation:** ✅ Backend: `test_owner_audit_logs.py` (34/34 passed). Frontend: pending build.

**Rollback:** Revert `AuditLogs.jsx` to main's version; `AuditEventDrawer.jsx`/`auditCategories.js`
can be deleted independently.

---

## Batch 7 — Testing & Documentation

**Files:** all 5 backend test files (`test_owner_audit_logs.py`,
`test_owner_platform_rbac_matrix.py`, `test_owner_platform_staff_delegation.py`,
`test_owner_platform_staff_lifecycle.py`, `test_owner_platform_staff_profile.py`),
`backend/tests/test_treatment_identity_migration.py` (B, 1-line HEAD_REVISION bump),
`docs/PLATFORM_ARCHITECTURE_ROADMAP.md`, `docs/SNS_STAFF_ACCESS_CHECKPOINT.md`,
`.github/copilot-instructions.md`

**Risk:** Low. Tests are additive and already passing; docs are informational.

**Dependencies:** Land alongside the batches they test (tests can go in with each corresponding
batch above rather than last, but doc files can wait until the end).

**Validation:** ✅ 122/122 feature-specific tests pass. `test_treatment_identity_migration.py`'s
1-line `HEAD_REVISION` bump should be re-checked against whatever `main`'s current
`HEAD_REVISION` is at merge time (main may have advanced past `um2d1c2c3o5u9` already via
unrelated migrations — reconcile before taking this line).

**Rollback:** Trivial — tests and docs only, no runtime impact.

---

## Recommended overall sequence

1. Batch 1 (models/migrations) — foundation, low risk, fully validated.
2. Batch 2 (permissions) — core RBAC, medium-high risk, fully validated, needs manual `roles.py` review.
3. Batch 3 (auth) — **stop and get explicit security sign-off on `authorization.ts` before merging.**
4. Batch 4 (Owner UI shell/dashboard) — needs frontend validation first.
5. Batch 5 (Staff Management UI) — HIGH conflict; manual reconciliation with current main required.
6. Batch 6 (Audit Logs UI) — HIGH conflict; manual reconciliation with current main required.
7. Batch 7 (tests/docs) — land tests with their corresponding batch; docs last.

Do not proceed past Batch 2 until: (a) `npm install && tsc --noEmit && npm run lint && npm run
build` pass in the recovery worktree, and (b) a human reviewer has read the `authorization.ts`
diff alongside the backend RBAC diff.
