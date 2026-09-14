# Migration Register

Authoritative record of the Alembic migration graph state and all
forward-only (non-reversible-by-design) migrations, as of this
stabilization effort.

## Graph state (verified 2026-09-13)

```
$ python -m alembic heads
pay3v4e5r6i7f (head)

$ python -m alembic branches
p7q8r9s0t1u2 (branchpoint)
             -> q8r9s0t1u2v3
             -> q1r2s3t4u5v6
```

- **Single head:** `pay3v4e5r6i7f`. The repository does not have multiple
  competing heads. (An earlier "7 Alembic heads" finding in this program's
  history was proven to be a bug in an ad-hoc analysis script, not a real
  condition of the migration graph — see the System-Wide Baseline Report
  for that investigation. AST-based parsing confirmed 108 migrations, 1
  root, 1 head, fully connected.)
- **One branchpoint** (`p7q8r9s0t1u2`) exists with two branches
  (`q8r9s0t1u2v3`, `q1r2s3t4u5v6`) that reconverge further down the chain
  before reaching the single head above — this is a normal, intentional
  Alembic branch/merge pattern, not an orphan chain.

## Forward-only migrations (repo-wide, verified via grep for `NotImplementedError`/"Forward-only" in `downgrade()`)

Only two migrations in the entire history are forward-only:

### 1. `p9r8q7s6t5u4_add_billing_scope_permission_levels.py`

- **Revises:** `n8m7b6v5c4x3`
- **upgrade():** adds `billing_provider_agency_service_scopes.permission_level`
  (nullable=False, server_default `'VIEW'`) and a check constraint
  restricting it to `('VIEW', 'EDIT')`.
- **downgrade():** `raise NotImplementedError("Forward-only migration")`.
- **Status:** historical, already merged into `origin/main`
  (`git merge-base --is-ancestor <rev> origin/main` → exit 0).
- **Is the underlying change actually lossless?** Yes — the `upgrade()`
  only adds a column with a default and a check constraint; a real
  `downgrade()` could technically be implemented with zero data loss.
- **Why it stays forward-only anyway:** see
  `DECISION_LOG.md` § "Historical migration immutability (`p9r8q7s6t5u4`)".
  This repo's own `schema_policy.md` states Alembic history is
  forward-only as of `sns-emr-stable-2026-06-04`; this migration predates
  and falls under that policy. If the column is ever removed, that must be
  a **new** forward-only migration, not an edit to this file.
- **Test coverage:**
  `tests/test_treatment_identity_migration.py::test_permission_level_migration_is_intentionally_historical_forward_only`
  — asserts the guard fires with the documented message, and that the
  column, its check constraint (looked up by definition via
  `pg_get_constraintdef`, not by name — this repo's naming convention
  rewrites explicit constraint names), and `alembic_version` are all
  unchanged after the failed downgrade attempt (no partial downgrade).

### 2. `n8m7b6v5c4x3_add_facility_payment_expectation_workflow_fields.py`

- **Revises:** `i2j3k4l5m6n7`
- **upgrade():** adds several nullable/defaulted columns to
  `facility_payment_expectations` / `facility_payment_allocations`, then
  runs a data migration that collapses any `source` value not in the
  current known-value set (including the legacy `'MANUAL'`, remapped to
  `'AUTHORIZED_MANUAL_ENTRY'`) down to `'NOT_VERIFIED'`.
- **downgrade():** `raise NotImplementedError("Forward-only migration.")`.
- **Is the underlying change actually lossless?** No — the
  `UPDATE ... source = CASE ... ELSE 'NOT_VERIFIED' END` step is a genuine,
  irreversible collapse of the original value once it falls outside the
  recognized set. This one was never a candidate for reversal.
- **Test coverage:**
  `tests/test_treatment_identity_migration.py::test_facility_payment_expectation_migration_is_correctly_forward_only`
  — asserts the guard fires with the documented message, and that the
  schema (a representative added column) and the `source` check constraint
  (looked up by definition, same reason as above) and `alembic_version` are
  unchanged after the failed downgrade attempt (no partial downgrade).

## Chain ordering relevant to migration-replay tests

```
... -> af1833134391 -> c3f7a1e9b0d2 (PRE_MIGRATION_REVISION)
     -> d9e8f7a6b5c4 (treatment-identity canonicalization, under test)
     -> ... -> i2j3k4l5m6n7 -> n8m7b6v5c4x3 (forward-only #2)
     -> ... -> p9r8q7s6t5u4 (forward-only #1)
     -> ... -> pay3v4e5r6i7f (HEAD)
```

Both forward-only migrations sit strictly between `PRE_MIGRATION_REVISION`
and `HEAD`. Consequently, a full `downgrade()` replay from `HEAD` back to
`PRE_MIGRATION_REVISION` is permanently impossible by design — this is
intentional, not a bug. Any test that needs a database at
`PRE_MIGRATION_REVISION` must build directly to it from an empty database
(`command.upgrade(cfg, "c3f7a1e9b0d2")`), never downgrade to it from `HEAD`.
`test_migration_remaps_treatment_references_and_preserves_survivor_metadata`
does exactly this.

## `tenants.facesheet_protection_mode` traceability

Introduced by migration `b7c3d2e1f0a9_add_facesheet_field_suggestions.py`
(part of the main chain above, well before either forward-only boundary) and
present on `HEAD`. It is reachable from both the current branch and
`origin/main`'s migration graph — there is no orphaned chain that owns it,
and it was never missed during normal `alembic upgrade head` traversal. (See
System-Wide Baseline Report for the original investigation that raised this
as a question; it was resolved as not-an-issue once the single-head model was
confirmed.)
