# ADR-002: Alembic Stabilization

## Status

Accepted

## Date

2026-09-20

## Context

While driving toward the RNICA zero-failure baseline (ADR-001), the full
backend test suite surfaced 6 defects, 5 of which were rooted in
Alembic migration `downgrade()` paths:

1. A migration test's `HEAD_REVISION` constant had gone stale relative
   to the actual migration head.
2. `x3y4z5a6b7c8_eligibility_workflow_correction.py`'s `downgrade()`
   re-narrowed `readiness_workflow_events.entity_type` back to
   `VARCHAR(16)`, even though application code
   (`eligibility_workflow_service.py`) legitimately writes values up to
   29 characters under the wider column added by this migration's
   `upgrade()`.
3. `p9r8q7s6t5u4_add_billing_scope_permission_levels.py`'s `downgrade()`
   was hardcoded to `raise NotImplementedError("Forward-only
   migration")`, despite being a trivially reversible, purely additive
   migration (one column + one check constraint).
4. `n8m7b6v5c4x3_add_facility_payment_expectation_workflow_fields.py`'s
   `downgrade()` was likewise hardcoded to raise
   `NotImplementedError`, despite most of its schema changes being
   reversible (only the one-time data backfill is inherently lossy on
   downgrade, which is normal for backfill migrations).
5. `i2j3k4l5m6n7_correct_billing_provider_authorization_architecture.py`'s
   `downgrade()` re-narrowed the
   `ck_billing_provider_assignment_scope_valid` CHECK constraint back to
   a pre-migration scope list, even though application code now writes
   the newer, wider scope values in normal operation.

Each of these caused real, reproducible test failures once realistic
data existed in the shared test database — they were not merely
theoretical gaps.

## Decision

- Migration `downgrade()` implementations must reflect what application
  code actually persists at the *time of downgrade*, not only what the
  schema looked like before the corresponding `upgrade()`. A
  `downgrade()` must not re-impose a constraint (column width, CHECK
  constraint, etc.) that is narrower than values the application
  legitimately writes under the widened schema.
- A migration must not be marked "forward-only" / `NotImplementedError`
  unless downgrading it is **truly** schema-irreversible. Purely
  additive migrations (new column, new constraint, new index) are
  always reversible and must implement a real `downgrade()`.
- One-time data backfill migrations may accept **data-content** loss on
  downgrade (values written during the backfill are not perfectly
  restorable), but the **schema** must still be fully reversible
  (columns/constraints/indexes dropped back to their prior state).
- No migration safety guard (see `backend/alembic/env.py`,
  `validate_migration_safety()`) should be assumed to have already
  caught these classes of bugs — that guard only inspects the head
  migration's `upgrade()` AST for destructive operations, not
  `downgrade()` correctness on non-head migrations.

## Consequences

- All 5 migration `downgrade()` paths above were corrected as part of
  PR #113.
- The full backend test suite passes with 0 failures on a fresh
  database, and the Alembic autogenerate drift probe returns an empty
  diff.
- Future migrations must be reviewed against this ADR before being
  merged: any `downgrade()` that narrows a column/constraint or that
  raises `NotImplementedError` must include a written justification for
  why it cannot be made reversible.

## Related

- PR #113 (MERGED, merge commit `3530e87f`)
- ADR-001 — RNICA Baseline
- Issue #114 — RNICA Baseline Preservation and Change Traceability Record
- Issue #115 — Regression Investigation Policy (migration trace
  requirements)
