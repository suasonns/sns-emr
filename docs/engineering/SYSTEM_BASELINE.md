# System Zero-Failure Baseline

**Branch:** `fix/billing-readiness-authoritative-reconciliation`
**Baseline commit:** `7b56b74`
**Established:** 2026-09-13

This document is the authoritative snapshot of repository health at the point
the zero-failure baseline stabilization program was completed. It exists to
give any future session (or engineer) a single place to confirm "is this
still true" before assuming regression.

---

## 1. Backend Test Counts

- **Suite:** `python scripts/run_isolated_tests.py` (full backend suite,
  isolated per-run Postgres database, migrated from `pay3v4e5r6i7f` head).
- **Result (JUnit-authoritative):** `tests=3007, failures=0, errors=0,
  skipped=10`, wall time ≈ 601–614s.
- **Skips:** 10 pre-existing/unrelated skips (environment-gated tests, not
  masking defects — enumerated in `CHANGE_LEDGER.md`).
- **Exit-code note:** the wrapper script can return shell exit code 1 due to
  a PowerShell `NativeCommandError` artifact from stderr-redirected Alembic
  `INFO` log lines. This is **not** a test failure signal — the JUnit XML
  `failures`/`errors` attributes are authoritative.

## 2. Frontend Build & Test Counts

- **Build:** `npx tsc -b` (project-reference mode) — **0 errors**.
- **Tests:** `npx vitest run` — **269/269 passed**.
- **Last fixed defect:** 12 TypeScript build errors in
  `FacilityCollectionsReportPage.tsx` (MUI v9 `Stack` prop-overload and
  `TextField InputLabelProps` API renames — no behavior change).

## 3. Migration Graph

- **Single head:** `pay3v4e5r6i7f`.
- **Root:** single connected chain, one normal branch/merge point at
  `p7q8r9s0t1u2` → (`q8r9s0t1u2v3`, `q1r2s3t4u5v6`) → recombines downstream.
- **No orphan chains.** (Earlier "7 Alembic heads" finding was a parser
  defect in ad-hoc analysis tooling, not a real repository condition —
  confirmed via AST-based traversal: 108 migrations, 1 root, 1 head,
  fully connected.)
- **Policy:** forward-only history (see `docs/engineering/schema_policy.md`
  and `DECISION_LOG.md`, Outcome A). Historical/applied migrations are
  immutable; `downgrade()` is not retrofitted onto shipped migrations solely
  to satisfy a test. Tests that need to validate forward-only boundaries
  assert that a full downgrade replay stops at the boundary, not that it
  succeeds past it.
- **Verified via `alembic heads`:** `pay3v4e5r6i7f (head)` — single head,
  confirmed directly against the dev database.

## 4. Admission Lifecycle (Authoritative Vocabulary)

| Status | Written by | Read by | Business purpose |
|---|---|---|---|
| `DRAFT` | Intake UI (pre-admission draft creation) | Intake workflow | Patient record started, not yet submitted |
| `PENDING` | Intake submission | Eligibility/verification workflow | Awaiting eligibility/insurance verification |
| `ADMITTED` | Admission finalization | Billing readiness, clinical charting, care planning | Active patient under care — the canonical "in service" status |
| `AUTHORIZED` | Payer/authorization workflow | Billing readiness matrix | Payer authorization obtained for continued/ongoing service |
| `ACTIVE` | (legacy/alias context — superseded by `ADMITTED` in current vocabulary) | Legacy readers only | Historical status predating the `ADMITTED` vocabulary consolidation |
| `DISCHARGED` | Discharge workflow | Billing close-out, reporting | Patient no longer receiving active service |

`ADMITTED` is the current canonical in-service status; `ACTIVE` is a legacy
alias that predates the vocabulary consolidation performed earlier in this
program (demo-seed data was fixed to stop hardcoding stale `ACTIVE` values).
Full admission-lifecycle **architecture** review (e.g. whether `ACTIVE`
should be formally removed) remains explicitly out of scope for this
stabilization pass per prior directive — current behavior is left
unchanged.

## 5. Runtime & Dependency Versions

| Component | Version |
|---|---|
| Python | 3.13.14 |
| Node.js | 24.19.0 |
| PostgreSQL | 16.14 |
| FastAPI | 0.136.1 |
| SQLAlchemy | 2.0.49 |
| Alembic | 1.18.4 |
| Pydantic | 2.13.3 |
| React | ^19.2.6 |
| MUI (`@mui/material`) | ^9.0.1 |
| Vite | ^8.0.12 |
| TypeScript | ~6.0.2 |

## 6. Approved Architecture Decisions (this program)

1. **Migration immutability (Outcome A):** historical/applied Alembic
   migrations are never edited, even when a specific change is provably
   lossless. See `DECISION_LOG.md`.
2. **`TEST_DATABASE_URL` preference:** test bootstrap must prefer a
   freshly-migrated `TEST_DATABASE_URL` over any hardcoded/stale isolated
   database name.
3. **Check-constraint verification pattern:** any test asserting a check
   constraint's presence/definition must query `pg_constraint` /
   `pg_get_constraintdef()` and filter by definition content — SQLAlchemy's
   naming convention rewrites explicit constraint names into a hashed
   pattern, so name-based lookups are unreliable.
4. **ADMITTED vocabulary:** `ADMITTED` is the canonical in-service admission
   status going forward; `ACTIVE` is legacy.

## 7. Known Limitations

- 10 backend test skips remain (pre-existing, environment-gated — not
  defects).
- Admission lifecycle vocabulary still contains the legacy `ACTIVE` alias;
  full consolidation is deferred (explicitly out of scope here).
- Several long-lived worktrees contain already-merged or abandoned content
  that has not yet been deleted from disk (see
  `WORKTREE_RECONCILIATION.md` for full disposition).
- Owner/Tenant/Biller dashboard redesign (Tailwind, OwnerShell, navigation,
  branding) is intentional, in-progress modernization work and is not a
  stabilization blocker.
