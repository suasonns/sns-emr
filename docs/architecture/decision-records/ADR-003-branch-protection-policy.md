# ADR-003: Branch Protection Policy

## Status

Accepted

## Date

2026-09-20

## Context

Prior to this decision, `main` had no branch protection rules, meaning
any push could merge without CI verification, and pre-existing failures
could silently persist or worsen without being blocked. Once the RNICA
zero-failure baseline (ADR-001) was established, this gap needed to be
closed so the baseline could not silently regress.

## Decision

Branch protection is enabled on `main` requiring the following status
checks to pass before merge, with `strict` mode enabled (branch must be
up to date with `main` before merging):

- `Frontend build`
- `Backend schema and import`
- `preflight`

These are the actual GitHub check-run context names produced by this
repository's CI workflows. Note that "Alembic Drift" and "Migration
Replay" are **not** independent GitHub check contexts — they are
verification steps that run inside `Backend schema and import` and
`preflight`, and are covered by requiring those two checks.

The baseline tag `rnica-baseline-verified-2026-09` must not be deleted
or force-moved. Tag protection is applied so it cannot be deleted or
overwritten by a force-push (see repository tag protection rules).

## Consequences

- No PR can merge into `main` unless the frontend build, backend
  schema/import verification, and the full non-`continue-on-error`
  preflight suite all pass.
- Contributors can no longer merge past a known-red preflight run and
  call it "pre-existing" — any pre-existing failure must be fixed (per
  ADR-002's precedent) or the check will block the merge.
- Future changes to required checks (adding, removing, or renaming) must
  be documented as an amendment to this ADR.

## Related

- ADR-001 — RNICA Baseline
- ADR-002 — Alembic Stabilization
- Issue #114 — RNICA Baseline Preservation and Change Traceability Record
- Issue #115 — Regression Investigation Policy
