# ADR-001: RNICA Baseline

## Status

Accepted

## Date

2026-09-20

## Context

RNICA and Patient Chart discovery/implementation work needs a known-good,
fully-verified starting point. Prior to this decision, `main` carried
several pre-existing CI failures that were routinely dismissed as
"pre-existing" without root-cause investigation, making it impossible to
reliably distinguish new regressions from long-standing latent defects.

## Decision

`main` at commit `3530e87f` (merge of PR #113) is designated the
verified RNICA baseline, tagged `rnica-baseline-verified-2026-09`.

All RNICA and Patient Chart discovery work (Phase 2) begins from this
tag. Any regression investigation must first compare against this tag
before evaluating changes introduced afterward.

## Verified Conditions At Baseline

- Frontend Build: PASS
- Backend Schema and Import: PASS
- Preflight (full backend suite, no `continue-on-error`): PASS
- Full backend test suite (`scripts/run_isolated_tests.py`, unfiltered):
  0 failures, exit code 0
- Alembic autogenerate drift probe: empty diff (no drift)
- Alembic `downgrade -1` / `upgrade head` roundtrip: clean
- `import app.main`: clean

## Consequences

- Future regressions are triaged against this tag as the reference
  point, per the Regression Investigation Policy (see issue #115).
- The tag, the merge commits for PR #113/#111, and the CI history behind
  them must never be deleted or rewritten (see issue #114).
- Branch protection on `main` (see ADR-003) enforces that future changes
  cannot silently regress below this baseline.

## Related

- PR #113 (stabilization, MERGED)
- PR #111 (documentation/Phase 2 discovery, MERGED)
- PR #92 (superseded, CLOSED_NOT_MERGED)
- Issue #114 — RNICA Baseline Preservation and Change Traceability Record
- Issue #115 — RNICA Baseline Decision Record / Regression Investigation Policy
