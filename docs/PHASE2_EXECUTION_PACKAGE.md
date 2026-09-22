# PHASE2_EXECUTION_PACKAGE.md

**Document Status:** ACTIVE

**Status:** Planning only. No code, schema, or migration has been executed under
this package. Execution requires separate explicit authorization per workstream.

**Corrects:** an earlier draft of this package that introduced "Access Control
Policy" as a meaning for "ACP." Repository-wide evidence review (33 files,
~210 occurrences, zero exceptions) confirmed `ACP` means **Advance Care
Planning** everywhere in this codebase. "Access Control Policy" is not a term
used anywhere in this repository and is not introduced by this package.

**Terminology note (see `PHASE2_TERMINOLOGY_DECISION.md` for full evidence):**
`ACP` = Advance Care Planning, always, in this repository. Workstreams 1–3
below are therefore never labeled "ACP" — they use the repository's actual
terms: **Authority enforcement**, **RBAC enforcement**, **Permission
enforcement**, and **Audit enforcement**. Only Workstream 4 (RNICA) uses
`ACP`, and only in its correct clinical meaning.

**Completed work (this update only — see
`docs/phase2/ACCESS_CONTROL_DEFECT_REMEDIATION.md` and
`docs/phase2/ACCESS_CONTROL_DEFECT_VALIDATION.md` for full evidence):**
Three access-control defects surfaced during Workstream 2 evidence-gathering
(`has_permission()` stub in `permissions.py`, unreachable `"QA"` role gate in
`audit_dashboard.py`, and unauthenticated/untenanted `export_adr` in
`adr_exports.py`) were explicitly authorized and remediated, each by reusing
an existing mechanism (`has_capability`, `QA_ROLES`, `get_authorized_patient`,
`log_event`) — no new authority model, capability, or abstraction was
introduced. All three have passing dedicated tests plus a clean broader
authority/RBAC/audit/tenant suite run and a full-suite regression run (15
pre-existing, unrelated failures only, none touching the changed files). This
does not close Workstream 2 in full — the broader route-enforcement
enumeration described below remains open — but these three specific,
verified defects are done.

---

## PHASE 2 OBJECTIVE

Close the four outstanding enforcement/completeness gaps identified during
Phase 1A reconciliation and Phase 1B baseline freeze, split into four
independently authorizable workstreams so none is blocked by, or conflated
with, another:

1. Authority enforcement and RBAC enforcement (formalize what Phase 1A
   already selected as the single authority model — no new model).
2. Permission enforcement at the route level (close gaps where routes do
   not yet call the selected authority model).
3. Audit enforcement completion (close gaps where mutating actions are not
   yet logged).
4. RNICA Advance Care Planning (ACP) six-field reconciliation and validation
   parity (close the server/client enforcement gap already documented and
   approved in `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md`).

Workstreams 1–3 are Owner Platform / cross-cutting backend work. Workstream 4
is RNICA-scoped clinical validation work. They touch different files and can
be authorized, sequenced, and executed independently.

---

## IMPLEMENTATION SCOPE

### Workstream 1 — Authority model and RBAC enforcement

**Selected model (per `PHASE1A_AUTHORITY_MODEL.md`, already ratified, not
re-decided here):** Role Authority Rank (`ROLE_AUTHORITY_RANK`,
`backend/app/core/roles.py:299`) + capability-based `role_can()`
(`backend/app/core/roles.py:502`) against `PLATFORM_PERMISSION_MATRIX`
(`backend/app/core/roles.py:376`).

**Current state:** `GATE-004` (`PHASE1A_IMPLEMENTATION_GATE_REGISTER.md`) is
already marked `OPEN / SATISFIED` — the model exists and is formalized. This
workstream's job is verification/enforcement completeness, not model design.

**Work:**
- Enumerate every backend route that performs a privileged/owner-scoped
  action and confirm it calls `role_can()` (or an equivalent dependency) with
  the correct capability string.
- `role_can()` is currently invoked from exactly one API module:
  `backend/app/api/owner_admin.py`. Confirm whether this is the full intended
  enforcement surface or whether other privileged routes (staff management,
  billing admin, audit dashboard) are missing enforcement — this is a
  verification task, not an assumption.
- No new authority model, no new role, no new rank is introduced.

### Workstream 2 — Backend permission and route enforcement

**Work:**
- For each route identified as missing enforcement in Workstream 1, add the
  appropriate `role_can()` / dependency check.
- Add/confirm 403 responses for unauthorized roles are consistent
  (`HTTPException(status_code=403, ...)`) across all newly-enforced routes.
- No change to `PLATFORM_PERMISSION_MATRIX` capability definitions unless a
  route enforcement gap reveals a missing capability entry (must be flagged
  and separately approved before adding).

### Workstream 3 — Audit-event and audit-log completion

**Current state (verified this session):**
- Audit infrastructure exists: `AuditLog` model
  (`backend/app/models/audit_log.py`), `log_event()` helper
  (`backend/app/services/audit_logger.py:24`), and a local
  `_safe_log_event()` wrapper in `backend/app/api/visits.py:3092` already
  used at 16 call sites in that file (lines 1240, 1328, 3534, 3571, 4056,
  4289, 4394, 4529, 4639, 4960, 5223, 5897, 6266, 6434).
- **Confirmed gap:** the 5 core RNICA CRUD endpoints — `POST /rnica/save`
  (`visits.py:774`), `GET /rnica/{assessment_id}` (`visits.py:919`),
  `PUT /rnica/{assessment_id}` (`visits.py:1087`),
  `DELETE /rnica/{assessment_id}` (`visits.py:1145`), and
  `POST /rnica/{assessment_id}/lock` (`visits.py:1177`) — have **no**
  `_safe_log_event()` calls. Only the generic `FINALIZE_VISIT` event on
  `Visit` rows is logged elsewhere; RNICA-specific create/read/update/
  delete/lock actions are not. This matches the gap already recorded in
  `docs/RNICA_COMPLETION_LEDGER.md` §"No RNICA-specific audit logging."

**Work:**
- Add `_safe_log_event()` calls to the 5 RNICA CRUD endpoints listed above,
  using the existing event/action taxonomy (no new audit table columns).
- Verify `AuditLog.event_metadata` (DB column `metadata`) captures enough
  context (assessment id, patient id, actor) for each new event.
- No schema change: `audit_logs` table already has the columns needed
  (`action`, `entity_type`, `entity_id`, `event_metadata`, `user_id`, `role`).

### Workstream 4 — RNICA Advance Care Planning (ACP) six-field reconciliation

**Approved target (per `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md`,
already accepted, not re-decided here):**
1. CPR Preference Discussion Status —
   `demographics.advancedCarePlanning.cprPreferenceAskedStatus`
2. Code Status — `demographics.advancedCarePlanning.codeStatus`
3. Life-Sustaining Treatment Discussion Status —
   `demographics.advancedCarePlanning.lifeSustainingAskedStatus`
4. Life-Sustaining Treatment Preference —
   `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference`
5. Hospitalization Preference Discussion Status —
   `demographics.advancedCarePlanning.hospitalizationAskedStatus`
6. Hospitalization Preference —
   `demographics.advancedCarePlanning.hospitalizationPreference`

**Current state (per the reconciliation decision, re-verified paths above,
not re-litigated):** all 6 fields already exist in `form_data` today — no new
schema/storage required. Only 3 of 6 (Code Status, Life-Sustaining Treatment
Preference, Hospitalization Preference) are server hard-required at Lock via
`RN_ICA_REQUIRED_FIELD_GROUPS` in
`backend/app/services/clinical_note_validation_engine.py:380-517`. The other
3 (discussion-status fields) are not server-enforced; one
(`lifeSustainingAskedStatus`) is client-required in `RNICA.jsx:975-976` but
the other two are not enforced anywhere.

**Separately tracked defect (same document, different bug):** a storage-path
mismatch where the frontend writes `demographics.advancedCarePlanning.*` but
backend sync extractors (`_extract_rnica_code_status`, `_extract_rnica_dpoa`,
`_extract_rnica_decision_maker` in `backend/app/api/visits.py:238-274`) read
`form_data.advancedCarePlanning.*` (top-level, no `demographics` wrapper).
This causes the Code Status → `patient_code_statuses` and DPOA/Decision-Maker
→ `patient_contacts` syncs to silently receive `None`.

**Work (per the reconciliation decision's own scope — not expanded here):**
1. Add server-side Lock enforcement for the 3 currently-unenforced
   discussion-status fields in `clinical_note_validation_engine.py`
   (`RN_ICA_REQUIRED_FIELD_GROUPS`), applied prospectively only — no rewrite
   of already-locked/signed records.
2. Add/confirm client-side requiredness in `RNICA.jsx` for all 3
   discussion-status fields (only 1 of 3 is currently client-required).
3. Fix the storage-path mismatch in the 3 named `visits.py:238-274`
   extractor functions so they read `demographics.advancedCarePlanning.*`
   (matching where the frontend actually writes), restoring the Code
   Status/DPOA/Decision-Maker syncs.
4. Consolidate the ACP presentation into one dedicated screen/card, per
   `RNICA_PHASED_IMPLEMENTATION_PLAN.md` Increment 9 (UI reorganization only
   — no new fields, no new validation rules beyond items 1–2 above).
5. Label each field as an official CMS HOPE requirement (F2000/F2100/F2200
   family) vs. an SNS-internal-only requirement, per the reconciliation
   decision's own open labeling requirement — this is a documentation/
   verification task using existing CMS HOPE guidance, not a new design
   decision.

**Explicitly out of scope for Workstream 4 (per the reconciliation
decision, restated here so it is not silently expanded):**
- No new ACP fields beyond the approved 6.
- No reduction from 6 to 3.
- No change to already-locked/signed RNICA records.
- No unrelated RNICA Master Map sections (Spiritual/F3000, Pain/J0905-J0910,
  N0500 family, etc.) — those are separate, un-authorized gaps tracked
  elsewhere (`RNICA_COMPLETION_LEDGER.md`) and are not part of Phase 2.

---

## DEPENDENCIES

| Workstream | Depends on | Reason |
|---|---|---|
| 1. Authority/RBAC | None (Phase 1A `GATE-004` already satisfied) | Verification only |
| 2. Route enforcement | Workstream 1 output (route/gap enumeration) | Cannot add enforcement before gaps are enumerated |
| 3. Audit completion | None | Independent — audit infrastructure already exists |
| 4. RNICA ACP | None (reconciliation decision already approved) | Independent — does not touch RBAC/audit code |

Workstreams 1–3 all touch backend Owner-Platform-adjacent code
(`app/core/roles.py`, `app/api/owner_admin.py`, `app/services/audit_logger.py`).
Workstream 4 touches RNICA-only files
(`clinical_note_validation_engine.py`, `visits.py:238-274` extractor
functions, `RNICA.jsx`). **No file overlap between Workstream 4 and
Workstreams 1–3** — they may be authorized and executed in parallel or in
either order.

---

## DATABASE IMPACT

| Workstream | Migration required? | Detail |
|---|---|---|
| 1. Authority/RBAC | No | No new tables/columns; `ROLE_AUTHORITY_RANK`/`PLATFORM_PERMISSION_MATRIX` are Python dicts, not DB-backed |
| 2. Route enforcement | No | Enforcement is code-level (route dependencies), not schema |
| 3. Audit completion | No | `audit_logs` table already has all required columns (verified: `action`, `entity_type`, `entity_id`, `event_metadata`, `user_id`, `role`, `request_id`, `ip_address`) |
| 4. RNICA ACP | No | All 6 target fields already exist in `rnica_assessments.form_data` (JSONB) today, per the reconciliation decision — confirmed no new keys needed |

**No migrations are required for Phase 2 as scoped.** If implementation
discovers an unexpected schema need in any workstream, that must be reported
and separately authorized before any migration is created — consistent with
the "no migrations" planning-only rule already in force.

---

## CODE IMPACT

| Workstream | Files affected |
|---|---|
| 1. Authority/RBAC | `backend/app/core/roles.py` (read/verify only, no edits expected unless a capability gap is found), `backend/app/api/owner_admin.py` (verify existing `role_can()` call sites) |
| 2. Route enforcement | Whichever route files Workstream 1 identifies as missing enforcement (not yet enumerated — enumeration is Workstream 1's output) |
| 3. Audit completion | `backend/app/api/visits.py` (add `_safe_log_event()` calls at 5 RNICA CRUD endpoints: lines 774, 919, 1087, 1145, 1177) |
| 4. RNICA ACP | `backend/app/services/clinical_note_validation_engine.py:380-517` (add 3 fields to `RN_ICA_REQUIRED_FIELD_GROUPS`), `backend/app/api/visits.py:238-274` (fix `_extract_rnica_code_status`/`_extract_rnica_dpoa`/`_extract_rnica_decision_maker` path), `sns-emr-frontend/src/components/RNICA.jsx` (client requiredness for 2 remaining discussion-status fields, ACP screen consolidation) |

---

## UI IMPACT

| Workstream | UI areas |
|---|---|
| 1. Authority/RBAC | None (backend-only verification) |
| 2. Route enforcement | Possible new 403 error states on previously-unenforced screens — exact screens unknown until Workstream 1 enumerates gaps |
| 3. Audit completion | Owner Platform Audit Logs screen (`sns-emr-frontend/src/owner/pages/AuditLogs.jsx`) will show new RNICA audit events once logged — no code change to that screen required, only new data flowing into it |
| 4. RNICA ACP | `RNICA.jsx` — Advanced Care Planning card (`RNICA.jsx:3974-3996`); adds 2 new required-field indicators and consolidates the section per Increment 9 |

**Note:** `sns-emr-frontend/src/owner/pages/AuditLogs.jsx` currently has an
uncommitted local modification in this worktree (flagged during Phase 1B
verification, not yet resolved). This must be reconciled before Workstream 3
execution touches audit-log-adjacent code, to avoid conflating an
unrelated pre-existing change with Phase 2 work.

---

## TEST PLAN

| Workstream | Required test coverage |
|---|---|
| 1. Authority/RBAC | Re-run existing `backend/tests/test_owner_platform_rbac_matrix.py` (already passing per Phase 1B verification) — no new tests unless a gap is found |
| 2. Route enforcement | New test per newly-enforced route: authorized-role-succeeds + unauthorized-role-403, mirroring the pattern in `test_owner_platform_rbac_matrix.py` |
| 3. Audit completion | New assertions (extend `backend/tests/test_owner_audit_logs.py` or `test_audit_logging.py`) confirming each of the 5 RNICA CRUD actions produces exactly one `AuditLog` row with correct `action`/`entity_type`/`entity_id` |
| 4. RNICA ACP | New backend test(s) for the 3 newly-enforced discussion-status fields blocking Lock when missing (mirroring existing FAST/NYHA conditional Lock tests in `clinical_note_validation_engine.py` test suite); regression test confirming the storage-path fix restores `patient_code_statuses`/`patient_contacts` sync (per `RNICA_COMPLETION_LEDGER.md`'s suggested verification: unit test on `_sync_facesheet_from_rnica`/extractor functions); frontend test/manual verification that `RNICA.jsx` blocks save/lock on the 2 newly-required discussion-status fields |

All backend tests run via `backend/scripts/run_isolated_tests.py` (the only
sanctioned test-runner in this repository) against `127.0.0.1` (not
`localhost`, per the Phase 0/1B `DATABASE_URL` host finding).

---

## ACCEPTANCE CRITERIA

- Workstream 1: route/gap enumeration is complete and documented; no
  unaccounted-for privileged route remains unclassified.
- Workstream 2: every route identified in Workstream 1 as needing
  enforcement has it, and returns 403 for unauthorized roles in tests.
- Workstream 3: all 5 RNICA CRUD endpoints produce an audit log row on
  success; existing audit tests plus new assertions pass.
- Workstream 4: all 6 approved ACP fields are enforced consistently
  (server Lock-blocking + client requiredness) exactly as specified in
  `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md`; the storage-path fix is
  verified to restore the Code Status/DPOA/Decision-Maker syncs; no
  already-locked record is altered.

## EXIT CRITERIA

- Each workstream's acceptance criteria are independently verified and
  reported with evidence (test output, not assumption).
- No workstream introduces a new authority model, a new "Access Control
  Policy" abstraction, a new ACP field, or a reduction of the approved
  6-field ACP target.
- No migration was created (all 4 workstreams are migration-free as scoped).
- Any newly-discovered gap (schema need, missing capability, additional
  unenforced route) is reported and separately authorized, not silently
  implemented.

---

## IMPLEMENTATION ORDER

1. Workstream 1 (Authority/RBAC verification) — must run first; it produces
   the input Workstream 2 needs.
2. Workstream 3 (Audit completion) and Workstream 4 (RNICA ACP) — no
   dependency on 1 or 2 or each other; may run in parallel with Workstream 1,
   or in any order the user prefers.
3. Workstream 2 (Route enforcement) — runs after Workstream 1's enumeration
   is available.

---

## RISKS

- **AuditLogs.jsx uncommitted local change** (carried over from Phase 1B)
  could be conflated with Workstream 3 work if not resolved first.
- **RNICA storage-path fix (Workstream 4, item 3) changes production sync
  behavior** for Code Status/DPOA/Decision-Maker — must be verified not to
  regress the Facesheet, which currently displays whatever the (broken) sync
  currently produces; a "fix" here changes displayed data for existing
  patients, not just new saves. Requires explicit confirmation this is
  desired before implementation.
- **New Lock-blocking fields (Workstream 4, item 1)** could block staff from
  completing RNICA assessments that previously did not require the 3
  discussion-status fields — must be applied prospectively only (already a
  stated constraint in the approved reconciliation decision).
- **Route enforcement gaps (Workstream 2) are currently unknown in count**
  until Workstream 1 completes — scope/effort cannot be sized precisely
  until that enumeration exists.

## ROLLBACK PLAN

- All 4 workstreams are additive (new enforcement, new audit calls, new
  Lock-blocking rules) with no schema/migration changes — rollback is a
  straightforward `git revert` of the workstream's commit(s), no data
  migration or backfill required.
- Workstream 4's storage-path fix is the only item with a live-data
  behavioral effect (changes what the sync reads); if reverted, the
  pre-existing (broken) read path is restored exactly, with no data loss,
  since no destructive write is introduced.

---

## PHASE 2 READINESS

Planning complete. Each workstream is independently scoped, grounded in
verified repository evidence (file paths and line numbers cited above), and
has no migration requirement as currently understood. No implementation has
occurred. Awaiting explicit per-workstream (or combined) execution
authorization.
