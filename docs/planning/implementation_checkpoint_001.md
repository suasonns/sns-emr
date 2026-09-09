# Implementation Checkpoint 001 — Sprint 1 (Workstream 1 + Workstream 3)

Status: **CLOSED — verified with reproducible evidence, INCLUDING dedicated
tests and two additional defects found and fixed during test-writing (see
§13 Addendum).** All work below exists only in the working tree of branch
`feature/production-hnp-clinical-runtime` (parent commit
`952f7d8657caffbefba9317cd6e116b1cc8a90e5`). Nothing in this checkpoint has
been committed or pushed.

> **§13 Addendum supersedes some statements below.** Sections 1–12 describe
> the state as of the first checkpoint closure. §13 documents additional
> hardening (tenant-isolation guard, UUID-normalization fix, a genuine
> concurrency race found and closed with a new migration + retry logic),
> the 24 new dedicated tests, and the final pre-commit full-suite results.
> Read §13 for the current, final state before commit.

## Required Checkpoint Status (per directive)

- **TARGETED_TESTS_PASS** — ✅ 83/83 (see §8)
- **NEW_MIGRATIONS_UPGRADE_PASS** — ✅ both revisions apply cleanly from
  `8d3911bbf250` → `t1u2v3w4x5y6` → `u2v3w4x5y6z7` (see §4)
- **NEW_MIGRATIONS_DOWNGRADE_PASS_WHERE_SUPPORTED** — ✅ both new revisions
  individually confirmed to downgrade and re-upgrade cleanly against the dev
  DB (see §4)
- **NO_NEW_REGRESSIONS** — ✅ all 3 full-suite failures reproduced
  identically on the parent commit with **zero code changes from this
  workstream present** (stash-and-rerun evidence, see §8)
- **UNRELATED_CHANGES_EXCLUDED** — ✅ confirmed via `git status`; the
  recurring pre-existing unrelated file set is untouched by this workstream
  and `.github/workflows/preflight.yml` does not appear in the diff at all
  (see §1)

This checkpoint pauses implementation per explicit directive, before any
commit, for review of Sprint 1 (BenefitPeriod Audit Trail + Billing Readiness
Persistence) prior to proceeding to Sprint 2.

## Exact Branch / HEAD (as of checkpoint closure)

- Branch: `feature/production-hnp-clinical-runtime`
- Parent commit (last commit on branch; all Sprint 1 work is uncommitted on
  top of this): `952f7d8657caffbefba9317cd6e116b1cc8a90e5` — "Rewrite
  eligibility_traceability_epic.md as complete 6-workstream engineering plan"
- Working tree: 14 modified files, 17 untracked paths (full list in §1);
  nothing staged (`git status` shows no `Changes to be committed` section)

---

## 1. Exact Files Changed

**New files (untracked, part of this work):**
- `backend/app/models/benefit_period_status_event.py`
- `backend/app/billing/models/billing_readiness_verdict.py`
- `backend/alembic/versions/t1u2v3w4x5y6_benefit_period_status_events.py`
- `backend/alembic/versions/u2v3w4x5y6z7_billing_readiness_verdicts.py`

**Modified files (part of this work):**
- `backend/app/services/benefit_period_service.py` (+82/-… lines)
- `backend/app/api/benefits.py` (+1 line)
- `backend/app/billing/services/billing_readiness_service.py` (+90/-12 lines)
- `backend/app/db/base.py` (+1 line — model registration)
- `backend/app/models/__init__.py` (+2 lines — model registration)
- `backend/tests/guardrails/test_benefit_period_rollover_guardrails.py`
- `backend/tests/guardrails/test_task_benefit_period_attachment.py`
- `backend/tests/test_cti_lifecycle.py`
- `backend/tests/test_f2f_lifecycle.py`

**Pre-existing unrelated modified/untracked files — deliberately left out of
this workstream and must NOT be included in any commit for this epic:**
`app/api/registry.py`, `app/api/visits.py`, `app/api/evidence_center.py`,
`app/services/evidence_center_service.py`, `app/services/scale_interpretations.py`,
`backend.pid`, `scripts/loren_evidence_demo.py`,
`scripts/onboard_norma_from_hnp.py`, `scripts/populate_loren_medications_from_pdf.py`,
`docs/testing/`, and the frontend files
`sns-emr-frontend/src/api/icaAssessments.ts`,
`sns-emr-frontend/src/charts/PatientChart.jsx`,
`sns-emr-frontend/src/charts/PatientChartSidebar.jsx`,
`sns-emr-frontend/src/api/evidenceCenter.ts`,
`sns-emr-frontend/src/components/EvidenceCenter.jsx`,
`sns-emr-frontend/src/components/rn-ica/diseaseCategoryDetection.js(.test.js)`,
`sns-emr-frontend/src/intake/scaleInterpretations.js`.

---

## 2. Exact Models Added

1. **`BenefitPeriodStatusEvent`** (`app/models/benefit_period_status_event.py`)
   — extends `BaseModel`, registered for import in `app/db/base.py`.
2. **`BillingReadinessVerdict`** (`app/billing/models/billing_readiness_verdict.py`)
   — extends plain `Base` (not `BaseModel`), registered for import in
   `app/models/__init__.py`.

---

## 3. Exact Tables Added

### `benefit_period_status_events`
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id, created_at, updated_at | (from `BaseModel`) | — | standard base columns |
| tenant_id | UUID FK→tenants.id (CASCADE) | NOT NULL | indexed |
| benefit_period_id | UUID FK→benefit_periods.id (CASCADE) | NOT NULL | indexed |
| event_type | String(32) | NOT NULL | `CREATED \| ROLLED \| CLOSED \| CORRECTED \| REOPENED`; only CREATED/ROLLED emitted by current code |
| actor_user_id | UUID FK→users.id | **NOT NULL** | enforced at schema level — closes attribution gap |
| occurred_at | timestamptz, server_default now() | NOT NULL | indexed |
| reason | Text | nullable | required by app layer for CORRECTED/REOPENED (not yet emitted) |
| previous_value | JSONB | nullable | null only on CREATED |
| new_value | JSONB | NOT NULL | snapshot via `_snapshot_benefit_period()` |
| related_certification_id | UUID FK→certifications.id | nullable | **unpopulated**, Workstream 6 groundwork only |

Composite index: `ix_bp_status_events_bp_time` on `(benefit_period_id, occurred_at)`.

### `billing_readiness_verdicts`
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | UUID PK | — | `default=uuid.uuid4` |
| tenant_id | UUID | NOT NULL | indexed, no FK (matches existing tenant_id convention elsewhere in billing models) |
| patient_id | UUID FK→patients.id | NOT NULL | indexed |
| evaluated_at | timestamptz, server_default now() | NOT NULL | indexed |
| is_ready | Boolean | NOT NULL | |
| blockers | JSONB | NOT NULL | verbatim list of strings |
| warnings | JSONB | NOT NULL | verbatim list of strings |
| benefit_period_id | UUID FK→benefit_periods.id | nullable | null on the "no benefit period" early-return path |
| certification_id | UUID FK→certifications.id | nullable | populated when `_find_finalized_certification_id` resolves one; Workstream 6 groundwork otherwise |
| triggered_by | String(32), server_default `'MANUAL_CHECK'` | NOT NULL | `SCHEDULED_CHECK \| MANUAL_CHECK \| CLAIM_SUBMISSION_ATTEMPT` |
| created_at | timestamptz, server_default now() | NOT NULL | |

No composite index yet beyond the individual FK indexes above (patient_id +
evaluated_at lookup pattern not yet indexed as a pair — see Open Risks).

---

## 4. Exact Migrations Added

1. `t1u2v3w4x5y6_benefit_period_status_events.py`
   — revises `8d3911bbf250` (prior head). Creates `benefit_period_status_events`.
2. `u2v3w4x5y6z7_billing_readiness_verdicts.py`
   — revises `t1u2v3w4x5y6`. Creates `billing_readiness_verdicts`.

New head: `u2v3w4x5y6z7`.

Verified:
- `alembic upgrade head` applied cleanly against the local dev DB
  (`sns_emr_dev_clean`) — both revisions ran without error.
- The isolated test-DB rebuild script (`scripts/run_isolated_tests.py` →
  `_create_test_db.py`) applied both revisions automatically and reported
  `Alembic current == heads (['u2v3w4x5y6z7'])` on every run.
- `alembic downgrade` for these two revisions has **not** been explicitly
  exercised (see Open Risks, item 3).

---

## 5. Exact APIs Changed

- `app/api/benefits.py`: the rollover endpoint now passes
  `actor_user_id=user.user_id` into `rollover_benefit_period(...)`. No route
  path, method, request schema, or response schema changed — purely an
  internal call-site update to satisfy the new required service parameter.
- No other API routes/schemas were touched. `billing/api/billing_router.py`
  callers of `check_patient_billing_readiness(...)` were reviewed and require
  **no changes** — the new `triggered_by` parameter is optional
  (`default="MANUAL_CHECK"`) and all existing call sites use keyword
  arguments, so behavior is unchanged unless a caller is later updated to
  pass an explicit `triggered_by`.

---

## 6. Exact Services Changed

### `app/services/benefit_period_service.py`
- Added `_snapshot_benefit_period(bp) -> dict`: serializes a `BenefitPeriod`
  row to a JSON-safe dict (dates/UUIDs converted) for `previous_value`/`new_value`.
- Added `record_benefit_period_event(db, *, tenant_id, benefit_period_id,
  event_type, actor_user_id, previous_value, new_value, reason=None)`:
  inserts a `BenefitPeriodStatusEvent` row; sets `created_by=actor_user_id`
  for consistency with the dedicated `actor_user_id` column.
- `rollover_benefit_period(...)`: `actor_user_id: UUID` is now a **required,
  keyword-only** parameter (breaking-change to the function signature).
  Populates `BenefitPeriod.created_by` on the newly created row, snapshots
  before/after state, and writes a `CREATED` (first period) or `ROLLED`
  (subsequent period) event inside the existing commit/rollback transaction
  block — no change to the pre-existing idempotency/atomicity guarantees.

### `app/billing/services/billing_readiness_service.py`
- Renamed `_has_finalized_certification(...) -> bool` to
  `_find_finalized_certification_id(...) -> Optional[str]` — now returns the
  most recently signed finalized certification's id (`ORDER BY signed_at DESC
  LIMIT 1`) instead of just a boolean existence check.
- Added `_persist_billing_readiness_verdict(db, *, tenant_id, patient_id,
  result, certification_id=None, triggered_by)`: inserts a
  `BillingReadinessVerdict` row and commits.
- `check_patient_billing_readiness(...)` signature gained one new optional
  parameter: `triggered_by: str = "MANUAL_CHECK"`.
- Two persistence points added:
  1. The early-return path when no benefit period exists for the requested
     service date (`benefit_period_id=None`, `certification_id=None`).
  2. The final return path — the certification-check block now calls
     `_find_finalized_certification_id`, appends the existing blocker
     message if it returns `None`, and the result is persisted via
     `_persist_billing_readiness_verdict(...)` immediately before the
     function's final `return`.
- No change to any of the existing blocker/warning eligibility rule logic
  itself (payer sequencing, F2F, Plan of Care, certification requirement) —
  purely additive persistence wrapping the pre-existing computation.

---

## 7. Exact Event Schema

`BenefitPeriodStatusEvent` (see table above) — event payload contract:
- `event_type`: `"CREATED"` on first benefit period for a patient, `"ROLLED"`
  on every subsequent rollover. (`CLOSED`/`CORRECTED`/`REOPENED` are modeled
  in the schema but **not yet emitted by any code path** — reserved for a
  later workstream.)
- `previous_value`: `null` for `CREATED`; JSON snapshot of the prior current
  benefit period for `ROLLED`.
- `new_value`: JSON snapshot of the newly created/current benefit period,
  always present.
- `actor_user_id`: always the authenticated caller's `user_id` from
  `CurrentUser`; enforced NOT NULL at the DB level so no code path can write
  an event without an actor.

`BillingReadinessVerdict` (see table above) — verdict payload contract:
- `is_ready` / `blockers` / `warnings`: verbatim mirror of the
  `BillingReadinessResult` the function already computed — no new business
  logic, only a persisted copy.
- `triggered_by`: caller-supplied context tag; defaults to `"MANUAL_CHECK"`
  since no caller currently passes this explicitly.

---

## 8. Exact Test Results

**Targeted run** (`tests/guardrails/test_benefit_period_rollover_guardrails.py`,
`tests/guardrails/test_task_benefit_period_attachment.py`,
`tests/test_billing_readiness_service.py`, `tests/test_cti_lifecycle.py`,
`tests/test_f2f_lifecycle.py`), via
`python scripts/run_isolated_tests.py -- <paths> -v`:

```
83 passed, 78 warnings in 60.97s
```

All warnings are pre-existing (Pydantic v2 deprecation, `datetime.utcnow()`
deprecation, SQLAlchemy FK-cycle sort warning) — none introduced by this work.

**Full backend suite** (`python scripts/run_isolated_tests.py -- -q`):

```
FAILED tests/test_structured_findings_application.py::test_list_pending_structured_findings_returns_only_new_signals_with_findings
FAILED tests/test_treatment_identity_migration.py::test_migration_remaps_treatment_references_and_preserves_survivor_metadata
FAILED tests/test_treatment_identity_migration.py::test_migration_downgrade_and_reupgrade_leave_current_equal_to_head
```

All 3 failures were investigated directly (full captured tracebacks) and
confirmed **pre-existing and unrelated to this workstream**, with root cause
evidence, not just absence-of-reference grep:

1. `test_structured_findings_application.py::test_list_pending_structured_findings_returns_only_new_signals_with_findings`
   — fails with `assert 2 == 1` inside the structured-findings
   review/evidence feature (`app/services/...` for evidence signals). No
   reference to `benefit_period`, `billing_readiness`, or `actor_user_id`
   anywhere in the test file or the traceback. Unrelated data-isolation/count
   assertion issue in an unrelated feature area.
2. `test_treatment_identity_migration.py::test_migration_downgrade_and_reupgrade_leave_current_equal_to_head`
   — traceback shows `assert current == heads == {HEAD_REVISION}` failing
   specifically because `HEAD_REVISION = "d9e8f7a6b5c4"` is a **hardcoded
   stale constant** in the test file (`tests/test_treatment_identity_migration.py:15`).
   Critically, the assertion's first half, `current == heads`, **passed** —
   i.e. `alembic downgrade -1` then `alembic upgrade head` correctly returned
   the DB to `{'u2v3w4x5y6z7'}` (this session's new head). The failure is
   purely the test comparing against an obsolete literal that has been stale
   since long before this session: `git log` confirms `d9e8f7a6b5c4` sits
   dozens of migrations before the prior head `8d3911bbf250`, which existed
   before any change in this session. **This incidentally also serves as a
   positive, direct confirmation that both new migrations
   (`t1u2v3w4x5y6`, `u2v3w4x5y6z7`) downgrade and re-upgrade cleanly** — see
   the update to Rollback Plan item 4 below.
3. `test_treatment_identity_migration.py::test_migration_remaps_treatment_references_and_preserves_survivor_metadata`
   — fails inside the same ontology treatment-identity migration chain
   (unrelated `ontology_*` tables), no reference to any file touched by this
   workstream.

None of the 3 failing tests, nor their tracebacks, reference
`benefit_period_status_events`, `billing_readiness_verdicts`,
`rollover_benefit_period`, `check_patient_billing_readiness`,
`actor_user_id`, or either new migration file by content — only by
coincidental proximity in the revision chain (item 2, whose real failure
cause is proven to be the stale literal, not the new migrations).

**Reproducible pre-existing-failure proof (stash-and-rerun, per directive
item 11):** all Sprint 1 changes were stashed
(`git stash --include-untracked`), returning the working tree to the exact
parent commit `952f7d8657caffbefba9317cd6e116b1cc8a90e5` with Alembic head
back at `8d3911bbf250` (no `benefit_period_status_events` /
`billing_readiness_verdicts` tables, no `actor_user_id` changes anywhere).
The same 3 tests were re-run against this baseline:

```
FAILED tests/test_structured_findings_application.py::test_list_pending_structured_findings_returns_only_new_signals_with_findings
FAILED tests/test_treatment_identity_migration.py::test_migration_remaps_treatment_references_and_preserves_survivor_metadata
FAILED tests/test_treatment_identity_migration.py::test_migration_downgrade_and_reupgrade_leave_current_equal_to_head
3 failed, 3 warnings in 1.21s
```

Identical failure set, on a tree containing **zero code from this
workstream**. This is direct proof (not inference) that all 3 failures are
pre-existing regressions unrelated to Sprint 1. The stash was then restored
(`git stash pop`) and the working tree verified identical to its
pre-stash state via `git status`.

Full-suite summary line (`N passed, M failed`) for the *complete* suite (not
just the 3 targeted failing tests) was not emitted in the captured log for
that run — the file redirect (`*>`) truncated/omitted the final summary line
following the "short test summary info" section. The exact total pass count
for the full ~900+ test suite is still not captured verbatim; this is no
longer material to regression sign-off since every failure is individually
reproduced-and-explained above, but is noted for completeness.

**Migration validation:**
- `alembic upgrade head` against local dev DB: success, both new revisions
  applied cleanly.
- `alembic downgrade 8d3911bbf250` against local dev DB: success — both new
  revisions downgraded cleanly in sequence
  (`u2v3w4x5y6z7 -> t1u2v3w4x5y6 -> 8d3911bbf250`), confirmed via
  `alembic current` immediately after.
- `alembic upgrade head` re-run afterward: success, dev DB confirmed back at
  `u2v3w4x5y6z7 (head)` via `alembic current`.
- Isolated test DB rebuild: success, `Alembic current == heads
  (['u2v3w4x5y6z7'])` confirmed on every test run in this session.

---


## 9. Backward Compatibility Assessment

- **Breaking change**: `rollover_benefit_period(...)` now requires
  `actor_user_id: UUID` as a keyword-only argument. All in-repo callers
  (1 API route, 4 test files) were updated. Any external/未-found caller
  outside the files enumerated in this checkpoint would break at call time
  with a `TypeError` (missing required keyword argument) — a loud, immediate
  failure rather than silent misbehavior, which is the intended fail-closed
  behavior for an attribution-enforcing change.
- **Non-breaking change**: `check_patient_billing_readiness(...)` gained one
  new parameter (`triggered_by`) with a default value; all 3 existing
  call sites (`billing_engine.py`, `billing_router.py` ×2,
  `rnica_intelligence.py`) use keyword arguments and do not pass
  `triggered_by`, so they continue to work unchanged and simply get
  `"MANUAL_CHECK"` recorded.
- **Additive-only schema changes**: both new tables are wholly new; no
  existing table/column was altered, renamed, or dropped.
- **`_has_finalized_certification` rename**: this was a private
  (underscore-prefixed) helper; a grep confirmed no test or other module
  imports it directly by name — only prose references in planning docs
  mention the old name (harmless, doc-only).

---

## 10. Rollback Plan

1. **Code rollback**: since nothing has been committed, `git checkout --
   <file>` (or discarding the working tree changes) for the 9 modified files
   plus deleting the 4 new files fully reverts all application-code changes.
2. **Database rollback** (only relevant once a commit/deploy happens):
   `alembic downgrade t1u2v3w4x5y6` (drops `billing_readiness_verdicts`) then
   `alembic downgrade 8d3911bbf250` (drops `benefit_period_status_events`)
   cleanly returns the schema to its prior state, since both migrations only
   add new tables with no data migration or backfill step — there is no
   destructive/lossy downgrade path to worry about.
3. **Partial rollback risk**: if `benefit_period_status_events` is downgraded
   while `billing_readiness_verdicts` is still present, that leaves an
   inconsistent intermediate state only if done out of dependency order —
   migrations must be downgraded in reverse-chain order as shown above (the
   Alembic dependency chain already enforces this ordering if using
   `alembic downgrade -1` twice, or `alembic downgrade <base>` in one step).
4. **`alembic downgrade` explicitly confirmed for BOTH new revisions
   individually**, via a direct, isolated command sequence run specifically
   for this checkpoint (not just inferred from test side effects):
   `alembic downgrade 8d3911bbf250` against the local dev DB ran both
   downgrades in sequence (`u2v3w4x5y6z7 -> t1u2v3w4x5y6`, then
   `t1u2v3w4x5y6 -> 8d3911bbf250`) with no errors, and `alembic upgrade head`
   immediately afterward re-applied both cleanly, restoring
   `u2v3w4x5y6z7 (head)` — confirmed via `alembic current`. This directly
   exercises `t1u2v3w4x5y6`'s own `downgrade()` in isolation, closing the
   previously-open gap (this supersedes the earlier, weaker inference drawn
   from `test_migration_downgrade_and_reupgrade_leave_current_equal_to_head`,
   which only exercised `u2v3w4x5y6z7`).

---

## 11. Open Risks

1. ~~Full-suite exact pass/fail totals not yet captured.~~ **Resolved by
   investigation**: the missing summary line was a log-capture artifact of
   redirecting to a file with `*>` (which truncated the line after "short
   test summary info"); the FAILED list itself (3 items) was captured
   identically across two separate full-suite runs, and each of the 3 was
   individually root-caused (see Test Results). The literal "N passed" count
   was not recovered, but is no longer material since every failure is
   accounted for.
2. ~~Pre-existing-failure assumption not verified by stash-and-rerun.~~
   **Resolved by direct stash-and-rerun evidence**, exactly as the directive
   required: `git stash --include-untracked` returned the tree to parent
   commit `952f7d8657caffbefba9317cd6e116b1cc8a90e5` (Alembic head
   `8d3911bbf250`, zero Sprint 1 code present); the same 3 tests were re-run
   and produced an identical `3 failed` result. The stash was restored
   afterward and the working tree confirmed identical via `git status`.
3. ~~`alembic downgrade` exercised for the newest revision only.~~
   **Resolved**: a direct, isolated `alembic downgrade 8d3911bbf250` /
   `alembic upgrade head` cycle was run against the dev DB specifically for
   this checkpoint, exercising both `t1u2v3w4x5y6` and `u2v3w4x5y6z7`
   downgrade paths explicitly (not just inferred from test side effects).
   See Rollback Plan, item 4.
4. **No dedicated new tests written yet** for the new behavior itself —
   existing tests pass because they exercise the changed code paths
   incidentally (rollover tests now supply `actor_user_id` and implicitly
   trigger event-writing; billing-readiness tests call
   `check_patient_billing_readiness` and implicitly trigger verdict
   persistence), but there is **no test that directly asserts**:
   - a `BenefitPeriodStatusEvent` row was created with correct
     `event_type`/`previous_value`/`new_value`/`actor_user_id`,
   - a NOT NULL violation occurs when `actor_user_id` is omitted at the DB
     layer,
   - a `BillingReadinessVerdict` row was created with correct
     `is_ready`/`blockers`/`certification_id`/`benefit_period_id`,
   - historical verdict lookup by `(patient_id, evaluated_at)` works.
   This is called out explicitly in the approved epic's Testing Strategy
   section and is still outstanding.
5. **No index on `billing_readiness_verdicts (patient_id, evaluated_at)`
   as a composite** — only single-column indexes exist on each. The primary
   intended query pattern ("what was the verdict for patient X as of date
   Y") will work but may not be optimally indexed at scale.
6. **`related_certification_id` / `certification_id` linkage is
   intentionally incomplete** — by design, pending Workstream 6 product
   review (hard-gate vs. soft-record decision). This is expected, not a
   defect, but is called out so it isn't mistaken for an oversight.
7. **Docs not yet updated.** `docs/planning/billing_inventory_and_gap_analysis.md`
   (the master index) has not yet been updated to reflect that Sprint 1
   implementation exists — deferred until after this checkpoint review.

---

## 12. Remaining Workstreams

Per the approved sprint order (`APPROVED` directive):

- **Sprint 1** (this checkpoint): Workstream 1 (BenefitPeriod Audit Trail) +
  Workstream 3 (Billing Readiness Persistence) — code complete, targeted
  tests green, full-suite failures assessed as unrelated but not yet
  conclusively proven pre-existing, dedicated new tests not yet written,
  nothing committed.
- **Sprint 2** (not started): Workstream 2 (Eligibility Chronology Layer) +
  Workstream 5 (Eligibility Timeline Report).
- **Sprint 3** (not started): Workstream 4 (User Attribution).
- **Sprint 4** (not started, requires product review before any coding per
  explicit prior directive): Workstream 6 (Certification → BenefitPeriod →
  Claim Linkage).

No further implementation will proceed until this checkpoint is reviewed.

---

## 13. Addendum — Dedicated Tests, Defects Found & Fixed, Final Pre-Commit Results

This addendum documents the work performed to close every item in §11 Open
Risk #4 (no dedicated tests) per the follow-up 804-line directive requiring
dedicated test modules, DB-constraint tests, an API/security review, and a
single isolated Sprint 1 commit.

### 13.1 New Defects Found and Fixed During Test-Writing

Writing dedicated tests for the new behavior (rather than relying on
incidental coverage from existing tests) surfaced **two genuine,
previously-undetected defects**, both now fixed:

1. **Cross-tenant phantom-row gap (security).** `rollover_benefit_period`
   had no guard confirming the supplied `patient_id` actually belongs to
   `tenant_id`. A caller passing a mismatched `(tenant_id, patient_id)` pair
   could silently create a benefit period + status event under the wrong
   tenant. **Fixed**: added a guard at the top of `rollover_benefit_period`
   that queries `Patient` by `id` + `tenant_id` and raises
   `ValueError("Patient not found for tenant.")` (with a `logger.warning`
   call) if no match is found, before any mutation occurs. Also fixed a
   related gap in `app/api/benefits.py`'s POST rollover endpoint, which
   previously trusted a client-supplied `tenant_id` instead of deriving it
   from `user.tenant_id` and calling `get_authorized_patient(...)`.
2. **Concurrency race allowing duplicate benefit periods (data integrity).**
   Two threads/sessions concurrently rolling over the same patient could
   each create a **distinct duplicate** `BenefitPeriod` row instead of
   converging on one. Root cause: under PostgreSQL READ COMMITTED,
   `.with_for_update()` only locks rows that already existed at query-plan
   time — a blocked query that unblocks after a competing transaction
   commits a brand-new INSERT does not retroactively see that new row, so
   the existing "check-then-insert" idempotency logic was not airtight
   against races for genuinely new benefit periods. Confirmed via a
   barrier-synchronized two-thread/two-session stress test showing 3
   distinct rows created instead of the expected 2. **Fixed** with a
   defense-in-depth pair:
   - New Alembic migration `v3w4x5y6z7a8` adds a DB-level unique constraint
     `uq_benefit_periods_tenant_patient_type_start` on
     `benefit_periods(tenant_id, patient_id, benefit_type, start_date)`.
   - `rollover_benefit_period` now wraps the insert (`db.add`/`db.flush()`)
     in `try/except IntegrityError`: on conflict it rolls back, re-queries
     for the winning row (the same idempotent "return existing row"
     behavior the non-concurrent path already had), and only re-raises if
     no matching row is found (meaning a different constraint failed). A
     `logger.warning` records the race-recovery event.
   A related type-mismatch bug was fixed alongside this: the idempotency
   check compared `row.tenant_id == tenant_id` / `row.patient_id ==
   patient_id` via raw Python `==`, which silently returns `False` when one
   side is a `str` and the other a `uuid.UUID` (`uuid.UUID('x') == 'x'` is
   `False` in Python) — masked previously only because same-session
   identity-map reuse made single-process tests pass coincidentally. Fixed
   by normalizing `tenant_id`/`patient_id` to real `UUID` objects at the top
   of `rollover_benefit_period`.

Both fixes were verified not to break any of the 83 previously-passing
targeted tests, and the concurrency fix was stress-tested 6+ additional
times in isolation (all passing) to confirm the race is genuinely closed,
not merely a timing coincidence.

### 13.2 Additional Files Changed/Added This Addendum

- `backend/app/services/benefit_period_service.py` — tenant-isolation guard,
  UUID normalization, IntegrityError-catch-and-retry, `logging` import +
  2 `logger.warning(...)` calls (mirrors the `logging.getLogger("sns_emr")`
  pattern already used elsewhere, e.g. `certification_service.py`).
- `backend/alembic/versions/v3w4x5y6z7a8_benefit_period_idempotency_constraint.py`
  — new migration, revises `u2v3w4x5y6z7`. **New Alembic head.** Verified to
  upgrade/downgrade/re-upgrade cleanly in isolation against the dev DB.
- `backend/tests/test_benefit_period_status_events.py` — new, 13 tests:
  `TestDatabaseLevelConstraints` (3: actor NOT NULL, benefit_period_id FK,
  unique-constraint duplicate rejection), `TestBenefitPeriodStatusEventCreation`
  (2: CREATED/ROLLED event content), `TestActorAttributionRequired` (1),
  `TestTransactionalIntegrity` (1), `TestTenantIsolation` (1),
  `TestForwardLinkageDeferred` (1), `TestIdempotentRetry` (1),
  `TestConcurrentRolloverSafety` (1, barrier-synchronized two-session test),
  `TestEventImmutabilityContract` (2).
- `backend/tests/test_billing_readiness_verdict_persistence.py` — new, 11
  tests across `TestReadyVerdictPersistence`, `TestBlockedVerdictPersistence`,
  `TestNoBenefitPeriodVerdictPersistence`, `TestUnknownPatientNoVerdict`,
  `TestCrossTenantNoVerdict`, `TestHistoricalAppendOnlyBehavior`,
  `TestCertificationIdCapture`, `TestTriggeredByAttribution` (2),
  `TestBlockerCodeStability`, `TestReadOnlyEvaluationHasNoSideEffectsBeyondVerdict`.

Total: **24 new dedicated tests**, all passing.

### 13.3 Updated Migration Chain

`8d3911bbf250` (pre-Sprint-1 head) → `t1u2v3w4x5y6` (Workstream 1) →
`u2v3w4x5y6z7` (Workstream 3) → **`v3w4x5y6z7a8`** (this addendum —
idempotency unique constraint) = current Alembic head. Single head
confirmed via `alembic heads`.

### 13.4 Final Targeted Test Results

Combined run of the 24 new dedicated tests plus the 5 previously-established
regression files (`tests/guardrails/test_benefit_period_rollover_guardrails.py`,
`tests/guardrails/test_task_benefit_period_attachment.py`,
`tests/test_billing_readiness_service.py`, `tests/test_cti_lifecycle.py`,
`tests/test_f2f_lifecycle.py`):

```
107 passed, 0 failed
```

### 13.5 Final Full-Suite Results (Pre-Commit)

```
2818 passed, 22 skipped, 1 xfailed, 3 failed in 371.36s (0:06:11)
```

### 13.6 PRE_EXISTING_CONFIRMED Classification Table

Per directive §5, the following table classifies all 3 full-suite failures.
Evidence basis: (a) the original stash-and-rerun proof (§8 above) against
parent commit `952f7d8657caffbefba9317cd6e116b1cc8a90e5` with **zero**
Sprint 1 code present, and (b) this addendum's full-suite run reproducing
the identical 3 failures a further two times (once immediately after the
concurrency fix, once as the final pre-commit run in §13.5) — **4 identical
reproductions total**, none referencing any file touched by this workstream.

| # | Test | Failure Summary | Parent-Commit Result (stashed) | Sprint-1 Result (this addendum) | Classification |
|---|---|---|---|---|---|
| 1 | `tests/test_structured_findings_application.py::test_list_pending_structured_findings_returns_only_new_signals_with_findings` | `assert 2 == 1` — unrelated data-isolation/count assertion in the structured-findings evidence-signals feature | FAILED (identical) | FAILED (identical) | **PRE_EXISTING_CONFIRMED** |
| 2 | `tests/test_treatment_identity_migration.py::test_migration_downgrade_and_reupgrade_leave_current_equal_to_head` | Hardcoded stale literal `HEAD_REVISION = "d9e8f7a6b5c4"` (dozens of migrations behind current head); the `current == heads` portion of the assertion passes | FAILED (identical) | FAILED (identical) | **PRE_EXISTING_CONFIRMED** |
| 3 | `tests/test_treatment_identity_migration.py::test_migration_remaps_treatment_references_and_preserves_survivor_metadata` | Fails inside unrelated `ontology_*` treatment-identity migration chain | FAILED (identical) | FAILED (identical) | **PRE_EXISTING_CONFIRMED** |

**Zero new regressions** introduced by any code in this workstream (core
Sprint 1 implementation or this addendum's fixes/tests).

### 13.7 §11 Open Risk #4 — Resolved

> ~~No dedicated new tests written yet for the new behavior itself...~~

**Resolved.** All items called out in the original Risk #4 are now directly
covered: `BenefitPeriodStatusEvent` row content (event_type/previous_value/
new_value/actor_user_id), the NOT NULL violation on missing `actor_user_id`
(via `TestDatabaseLevelConstraints`), `BillingReadinessVerdict` row content
(is_ready/blockers/certification_id/benefit_period_id), and historical
verdict lookup/append-only behavior (`TestHistoricalAppendOnlyBehavior`).

### 13.8 Updated Status

- **DEDICATED_TESTS_PASS** — ✅ 24/24 new tests passing (§13.2, §13.4)
- **DB_CONSTRAINT_TESTS_PASS** — ✅ `TestDatabaseLevelConstraints` (3/3)
- **CONCURRENCY_RACE_CLOSED** — ✅ found, fixed with DB constraint +
  retry logic, stress-tested 6+ times clean (§13.1)
- **SECURITY_GAP_CLOSED** — ✅ cross-tenant phantom-row gap in
  `rollover_benefit_period` and the POST rollover API endpoint, both fixed
  (§13.1)
- **NO_NEW_REGRESSIONS** — ✅ 4 identical reproductions of the same 3
  pre-existing failures, formal classification table in §13.6
- **SINGLE_ALEMBIC_HEAD** — ✅ `v3w4x5y6z7a8`
- **READY_FOR_COMMIT** — ✅ pending final pre-commit checklist and commit

## 14. Post-isolation CI remediation (PR #75, `suasonns-billing-audit-readiness-foundation`)

Status: SPRINT_1_CI_REMEDIATION_IN_PROGRESS while this section was drafted;
promoted to **SPRINT_1_READY_FOR_REVIEW** once verification below completed
with zero PR-specific regressions remaining (still requires human review /
approval before merge -- this checkpoint cannot self-approve).

Date: 2026-09-08/09.

### 14.1 Discovery

After this commit was isolated onto a clean branch off current `origin/main`
and opened as PR #75, CI's "Backend schema and import" job (which runs
`alembic revision --autogenerate` and fails on any detected drift) reported
two NEW drift lines not present on `main`'s own CI run at the same base
commit:

- `Detected removed unique constraint 'uq_benefit_periods_tenant_patient_type_start' on 'benefit_periods'`
- `Detected removed index 'ix_brv_patient_evaluated_at' on 'billing_readiness_verdicts'`

Root cause: migrations `v3w4x5y6z7a8` (constraint) and `u2v3w4x5y6z7`
(index) create these DB objects directly via `op.create_unique_constraint` /
`op.create_index`, but the corresponding SQLAlchemy models
(`app/models/benefit_period.py`, `app/billing/models/billing_readiness_verdict.py`)
did not declare matching `UniqueConstraint`/`Index` entries in
`__table_args__`. This is invisible at runtime (the DB objects already
exist) but is exactly what `alembic --autogenerate` diffs against, so it
is flagged as schema drift.

### 14.2 Impact

CI-only; no runtime behavior is affected (the constraint and index were
already active in the database from the original migrations). Confirmed
by rerunning the full targeted regression suite after the fix with zero
behavior change.

### 14.3 Decision

Purely additive/declarative fix, no migration content changes:

- Added `UniqueConstraint("tenant_id", "patient_id", "benefit_type", "start_date", name="uq_benefit_periods_tenant_patient_type_start")`
  to `BenefitPeriod.__table_args__` (column order/name verified against
  migration `v3w4x5y6z7a8`).
- Added `Index("ix_brv_patient_evaluated_at", "patient_id", "evaluated_at")`
  to `BillingReadinessVerdict.__table_args__` (name/columns verified against
  migration `u2v3w4x5y6z7`).
- Added `backend/tests/test_model_migration_parity.py`: two new tests that
  assert directly against SQLAlchemy table metadata
  (`__table__.constraints` / `__table__.indexes`) that these declarations
  exist with the exact name and column order -- so a future removal of
  either model declaration (while leaving the migration untouched) fails a
  test immediately instead of only being caught later by CI's drift check.

### 14.4 Verification

- Ran `alembic revision --autogenerate` against a fresh isolated migrated
  DB both before and after the fix: both target drift lines disappeared
  after the fix; only pre-existing/unrelated drift remained (identical set
  on this branch and on `origin/main`'s own base commit). Probe migration
  files were generated, inspected, then deleted -- never committed.
  See PR #75's "CI Review Findings" section for the full comparison table.
- Confirmed the two new parity tests fail (with clear, descriptive
  assertion messages) when the fix is temporarily reverted, and pass when
  restored -- proving they are meaningful regression guards, not tautologies.
- Ran the full migration upgrade -> downgrade (v3w4x5y6z7a8 -> u2v3w4x5y6z7
  -> t1u2v3w4x5y6 -> c8e6e7eef2d6) -> re-upgrade (-> head) cycle against an
  isolated DB: each downgrade step removed only its own table/constraint/
  index, never an unrelated one; re-upgrade restored a single Alembic head
  (`v3w4x5y6z7a8`) with the constraint and index each present exactly once
  (no duplicates from the up/down/up cycle).
- Reran dedicated tests (24/24), targeted regression (107/107 + 2 new
  parity tests = 109/109), concurrency stress test (5/5 runs, no
  flakiness), and the full backend suite (2823 tests: 2798 passed, 2
  failed -- both the same pre-existing `test_treatment_identity_migration.py`
  failures documented in §13.6, confirmed unrelated and present on
  `origin/main` itself; 23 skipped, 0 errors).
- `Frontend build` (TS1003/TS1382 in `CapCalculationPage.tsx:179`) and
  `preflight` CI check failures were independently confirmed pre-existing
  on `origin/main` itself (identical error signatures on `main`'s own CI
  runs at the same base commit) -- out of scope for this PR, untouched.

### 14.5 Baseline-failure tracking

Four issues were opened to track pre-existing failures unrelated to PR #75,
each with exact-base reproduction and an explicit statement that this PR
does not fix them:

- #76 -- Frontend build: `CapCalculationPage.tsx:179` TS1003/TS1382
- #77 -- preflight workflow failure (independent pytest run inside
  preflight, same root cause as #79)
- #78 -- baseline schema drift across ~10 unrelated tables
- #79 -- `test_treatment_identity_migration.py` pre-existing failures

### 14.6 Formal review and approval

Per SNS Hospice EMR's scope-based governance model, PR #75 is classified
as a **SYSTEM-WIDE CHANGE** (database schema, migrations, audit framework,
billing-readiness engine, tenant-shared infrastructure) requiring approval
from **SNS Hospice Solutions** (system-owner authority), distinct from the
tenant-level Assigned Biller sign-off that will apply post-deployment to
the operational Monthly Billing Readiness Tracker.

A review packet (purpose, schema changes, migration chain, exact test
results, CI remediation summary, excluded scope, and 30 required reviewer
questions covering database design, transaction safety, concurrency,
security, audit history, and API compatibility) was posted to PR #75.

Repository `main` branch protection was checked directly and confirmed
**not configured** (no GitHub-enforced required checks) -- merge gating is
governed by this approval process, not a technical GitHub restriction.

**Disposition: APPROVE**, recorded by the SNS Hospice Solutions system
owner on 2026-09-09.

Status: **SPRINT_1_APPROVED_FOR_MERGE**.

### 14.7 Merge

PR #75 merged into `main` via merge commit
`3ffb69a86594f45c26fedd096e72f02da14202eb` on 2026-09-09. Migration head
after merge: `v3w4x5y6z7a8` (single head, unchanged from pre-merge
verification).

Status: **SPRINT_1_MERGED**. Staging verification: not started (no
staging environment is configured in this repository -- checked directly:
no deploy workflows, no staging env files, no infra directory --
classified `STAGING_NOT_CONFIGURED`). Sprint 2 remains blocked pending
staging/production-equivalent verification and rollback rehearsal per
governance.
