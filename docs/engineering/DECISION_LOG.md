# Decision Log

Chronological record of non-obvious engineering decisions made during the
Zero-Failure Baseline stabilization effort on
`fix/billing-readiness-authoritative-reconciliation`. Each entry records the
question, the options considered, the decision, and the rationale, so a
future reader does not have to reconstruct the reasoning from git history.

---

## 2026-09-13 — Historical migration immutability (`p9r8q7s6t5u4`)

**Question:** While root-causing a migration-replay test failure, we found
that a genuinely reversible historical migration
(`p9r8q7s6t5u4_add_billing_scope_permission_levels.py`, already merged into
`origin/main`) had its `downgrade()` intentionally stubbed with
`raise NotImplementedError("Forward-only migration")`, even though its
`upgrade()` only adds a nullable-with-default column and a check
constraint — a change that is technically 100% lossless to reverse. Should
we implement a real `downgrade()` for it?

**Options considered:**
- **Outcome A** — Treat historical/applied migrations as immutable. Leave
  `p9r8q7s6t5u4` byte-identical to `origin/main`. If a real downgrade is
  ever needed, ship it as a *new* forward-only migration that undoes the
  column, not as an edit to the historical file.
- **Outcome B** — Implement `downgrade()` in place, since the change is
  provably lossless and the file has no other callers depending on the
  guard.
- **Outcome C** — Leave the guard in place but add a comment explaining why
  (no test change).

**Decision: Outcome A.**

**Rationale:**
- `docs/engineering/schema_policy.md` (pre-existing, written well before
  this session) already states: *"As of sns-emr-stable-2026-06-04: Alembic
  history is forward-only... No migration squashing."* This is the
  project's own documented policy, not an invented one.
- Throughout this multi-week stabilization program the user repeatedly and
  explicitly restated the same standing rule ("never rewrite an
  applied/historical migration") independent of whether a specific edit is
  provably safe. That standing instruction is treated as authoritative even
  though no CI check currently enforces migration-file checksums.
- Losslessness of one specific edit does not establish a safe precedent for
  the next one; a blanket "historical migrations are immutable" rule is
  simpler to reason about and audit than a case-by-case "unless we can
  prove it's safe" rule.
- `git merge-base --is-ancestor <p9r8q7s6t5u4 commit> origin/main` returned
  exit 0, confirming the file is historical/applied, not part of this
  branch's new work.

**What changed instead:**
- `backend/alembic/versions/p9r8q7s6t5u4_add_billing_scope_permission_levels.py`
  was reverted to be byte-identical to `origin/main` (verified via empty
  `git diff origin/main -- <path>`).
- `backend/tests/test_treatment_identity_migration.py` was rewritten so
  that the previously-failing downgrade-replay test never crosses this
  migration (or the also-forward-only `n8m7b6v5c4x3`) at all: it builds
  directly from an empty scratch database to the pre-migration revision
  instead of downgrading from HEAD.
- Two new tests were added
  (`test_permission_level_migration_is_intentionally_historical_forward_only`,
  `test_facility_payment_expectation_migration_is_correctly_forward_only`)
  that assert the forward-only guard fires with the documented message
  *and* that no partial downgrade occurred (schema, check constraints, and
  `alembic_version` are all unchanged after the guard raises), on disposable
  scratch databases dedicated to each test.

**See also:** `MIGRATION_REGISTER.md` for the full forward-only migration
inventory and chain ordering.

---

## 2026-09-13 — Shared static test database replaced with per-test isolated scratch databases

**Question:** `test_recertification_evidence_synthesis_v1.py` was hardcoded
to a fixed database name (`sns_emr_test_pr59_isolated`) that was never
re-migrated, so it silently drifted out of schema sync and every test in
the file failed against current models. Should the fix rebuild that fixed
database on every run, or should the test stop depending on a shared fixed
database at all?

**Decision:** Prefer the ambient `TEST_DATABASE_URL` (already freshly
migrated per-run by `scripts/run_isolated_tests.py`), with a schema-currency
check, rather than reintroducing a second fixed database that could drift
again. For the destructive migration-replay tests in
`test_treatment_identity_migration.py`, go further and give each test its
own fully disposable scratch database (via
`scripts/test_db_lifecycle.py::create_isolated_database` /
`teardown_isolated_database`), because those tests perform destructive
`downgrade()`/`upgrade()` cycles that must never run against the
shared per-suite-run database other tests depend on.

**Rationale:** A single shared, never-rebuilt database name is exactly the
failure mode that caused the original 12 recertification failures — fixing
it by hardcoding a *different* shared database would only defer the same
class of bug. Per-test disposable databases eliminate both cross-test
pollution and schema drift by construction.

---

## 2026-09-13 — RN-ICA count assertions scoped to the admission under test

**Question:** `test_rnica_poc_adapter.py` asserted a global
`.count()` of `PlanOfCareVersion`/`POCProblem` rows for a fixed
`tenant_id`, which failed intermittently because other tests sharing that
`tenant_id` had already committed rows before this test ran.

**Decision:** Scope the counts to the specific admission's
`plan_of_care_id`s under test, not the whole tenant.

**Rationale:** The test's intent was to verify behavior for *this*
admission's plan of care, not to assert an invariant about the entire
tenant's data (which is inherently order-dependent when tests share a
database). Scoping to the actual foreign keys under test makes the
assertion correct regardless of what else has run before it.
