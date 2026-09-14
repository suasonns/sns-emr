# Change Ledger

Summary of every substantive change delivered in the Zero-Failure Baseline
stabilization pass on `fix/billing-readiness-authoritative-reconciliation`,
organized by root cause, for traceability alongside the commits that
implement each one.

## 1. Recertification evidence synthesis — stale isolated test database

- **Symptom:** all 12 tests in
  `backend/tests/test_recertification_evidence_synthesis_v1.py` failing.
- **Root cause:** the test file resolved its database URL from a hardcoded,
  never-re-migrated database name (`sns_emr_test_pr59_isolated`) instead of
  the shared, freshly-migrated `TEST_DATABASE_URL` that
  `scripts/run_isolated_tests.py` provisions per run. The fixed database had
  drifted out of schema sync with current models.
- **Fix:** `_isolated_test_database_url()` / `_isolated_db_available()`
  rewritten to prefer `TEST_DATABASE_URL` and verify schema currency before
  use.
- **File:** `backend/tests/test_recertification_evidence_synthesis_v1.py`
- **Verification:** 12/12 passing in isolation; confirmed again inside the
  3007-test full-suite JUnit run (0 failures, 0 errors).
- **Production code touched:** none. Test-only change. No patient-data
  writes are performed by the synthesis code under test (read-only runtime
  synthesis, unchanged).

## 2. RN-ICA POC adapter — cross-test count pollution

- **Symptom:** 1 intermittent failure in
  `backend/tests/test_rnica_poc_adapter.py`.
- **Root cause:** an unscoped global `.count()` query on
  `PlanOfCareVersion`/`POCProblem` filtered only by a fixed `tenant_id`,
  which also matched rows committed by unrelated earlier tests sharing that
  tenant in the shared per-run database.
- **Fix:** counts rescoped to the specific admission's `plan_of_care_id`s
  under test.
- **File:** `backend/tests/test_rnica_poc_adapter.py`
- **Verification:** 18/18 passing in isolation; confirmed again inside the
  full-suite JUnit run.
- **Production code touched:** none. Test-only change.

## 3. Migration-replay test — crossing intentionally forward-only migrations

- **Symptom:** `test_migration_remaps_treatment_references_and_preserves_survivor_metadata`
  failing when replaying a full `HEAD -> PRE_MIGRATION_REVISION` downgrade.
- **Root cause:** that downgrade path crosses two intentionally forward-only
  migrations (`p9r8q7s6t5u4`, `n8m7b6v5c4x3`), both of which correctly raise
  `NotImplementedError` in `downgrade()`. The test's premise (a full
  HEAD-to-early-revision downgrade) was incompatible with the approved
  forward-only architecture.
- **Policy decision:** see `DECISION_LOG.md`. Historical/applied migrations
  are immutable; `p9r8q7s6t5u4` was reverted to byte-identical
  `origin/main` content after a brief, ultimately-rejected attempt to make
  it reversible (it is technically lossless, but immutability policy
  overrides that).
- **Fix:** the test suite in
  `backend/tests/test_treatment_identity_migration.py` was restructured:
  - The main ontology test now builds directly to `PRE_MIGRATION_REVISION`
    from an empty scratch database, instead of downgrading from `HEAD`, so
    it never crosses either forward-only boundary.
  - `test_permission_level_migration_is_intentionally_historical_forward_only`
    (new) and `test_facility_payment_expectation_migration_is_correctly_forward_only`
    (strengthened) each assert their migration's forward-only guard fires
    with the documented message, and that no partial downgrade occurred
    (schema/check-constraint/`alembic_version` unchanged), each on its own
    disposable scratch database.
  - The existing near-`HEAD` "-1" downgrade/reupgrade sanity test is
    unchanged (it doesn't cross either forward-only migration).
- **Files:** `backend/tests/test_treatment_identity_migration.py` (test-only
  changes). `backend/alembic/versions/p9r8q7s6t5u4_add_billing_scope_permission_levels.py`
  has **zero net diff** against `origin/main` — it was edited and then
  reverted within this session; there is nothing to commit for that file.
- **Verification:** all 4 tests in the file pass together; confirmed again
  inside the full-suite JUnit run.

## 4. Frontend TypeScript build errors (12 → 0)

- **Symptom:** `npx tsc -b` (the same command `npm run build` uses) failed
  with 12 errors in
  `sns-emr-frontend/src/pages/billing/FacilityCollectionsReportPage.tsx`.
- **Root cause:** the installed MUI major version's typings no longer allow
  `alignItems` / `justifyContent` / `flexWrap` directly as `<Stack>` props
  without a `component` prop (6 occurrences), and no longer expose
  `InputLabelProps` on `<TextField>` (renamed to `slotProps.inputLabel`, 6
  occurrences).
- **Fix:** the 6 `<Stack>` occurrences moved their layout props into `sx`;
  the 6 `<TextField ... InputLabelProps={{ shrink: true }}>` occurrences
  became `<TextField ... slotProps={{ inputLabel: { shrink: true } }}>`.
  No behavior change — purely a typings-compatible prop-API migration; the
  rendered CSS/DOM output is identical.
- **File:** `sns-emr-frontend/src/pages/billing/FacilityCollectionsReportPage.tsx`
- **Verification:** `npx tsc -b` exits 0 with no errors; `npx vitest run`
  passes 269/269 across all 19 frontend test files (no change to test
  count or pass count from before the fix, confirming no behavioral
  regression).

## Net effect

| Metric | Before this pass | After this pass |
|---|---|---|
| Backend full suite (JUnit) | 13 failing (historically tracked; see baseline reports) | **0 failed, 0 errors**, 3007 passed, 10 pre-existing/unrelated skips |
| Frontend TypeScript (`tsc -b`) | 12 errors | **0 errors** |
| Frontend tests (`vitest run`) | 269 passed | 269 passed (unchanged) |
| Historical migration files modified | 0 (none should be) | 0 (net; reverted after a since-rejected attempt) |
