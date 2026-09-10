# Open Defects List

Pre-existing failures confirmed unrelated to this branch (Priorities 1-8,
Billing Readiness / Eligibility / Admissions SSOT work). Verified by
running each in isolation and confirming the same failure reproduces
independent of this branch's changes.

| # | Test | Cause | Severity | Recommendation |
|---|---|---|---|---|
| 1 | `test_rnica_poc_adapter.py::test_lock_rnica_assessment_creates_no_poc_version_or_problem` | Fails only in full-suite runs: an unscoped global `PlanOfCareVersion.count()` query is polluted by other test files' leftover rows (test-ordering/global-state issue). Passes in isolation. | Low (test hygiene, not a product defect) | Scope the query/assertion to the test's own tenant/patient before merge of any future work touching this test; not required to block this PR. |
| 2 | `test_treatment_identity_migration.py::test_migration_remaps_treatment_references_and_preserves_survivor_metadata` | A later migration (`p9r8q7s6t5u4_add_billing_scope_permission_levels.py`) is deliberately forward-only and raises `NotImplementedError` on `downgrade()`, which breaks this test's full downgrade-to-base-and-reupgrade cycle. | Medium (blocks any full down/up migration test, by design) | Known, accepted limitation of the forward-only migration; not caused by or fixable within this branch's scope. |
| 3 | `test_treatment_identity_migration.py::test_migration_downgrade_and_reupgrade_leave_current_equal_to_head` | Same root cause as #2. | Medium | Same as #2. |

## Not Reproduced This Run

`test_test_database_isolation.py::test_run_isolated_tests_tears_down_after_pytest_subprocess_is_killed`
was seen intermittently in an earlier full-suite run (concurrency/timing
flake under load) but did not reproduce in either of the two final full
regression runs performed for this deliverable. Noting for visibility;
not currently an open failure.

## None of the above are caused by, or should block, this PR.
