# Changelog

All notable changes to this repository are documented in this file.

## [Unreleased]

### RNICA Baseline Stabilization — 2026-09-20

- **PR #113** — Repository Stabilization (MERGED, merge commit `3530e87f`)
  - Root-caused and fixed 6 pre-existing defects blocking a zero-failure
    CI baseline:
    1. Stale `HEAD_REVISION` test constant in
       `backend/tests/test_treatment_identity_migration.py`.
    2. `entity_type` downgrade narrowing bug in
       `x3y4z5a6b7c8_eligibility_workflow_correction.py`.
    3. Forward-only migration incorrectly marked irreversible:
       `p9r8q7s6t5u4_add_billing_scope_permission_levels.py`.
    4. Forward-only migration incorrectly marked irreversible:
       `n8m7b6v5c4x3_add_facility_payment_expectation_workflow_fields.py`.
    5. Scope-check constraint downgrade bug in
       `i2j3k4l5m6n7_correct_billing_provider_authorization_architecture.py`.
    6. RNICA POC test-isolation bug in
       `test_rnica_poc_adapter.py::test_lock_rnica_assessment_creates_no_poc_version_or_problem`.
  - Verified: Frontend Build, Backend Schema and Import, Preflight, full
    backend test suite (0 failures), Alembic drift-free, and a full
    downgrade/upgrade migration roundtrip.
  - Tagged as `rnica-baseline-verified-2026-09`.

- **PR #111** — Documentation / Phase 2 Discovery (MERGED, merge commit
  `1ffe6db`)
  - Establishes the Patient Chart documentation baseline, authority
    model, compliance-discovery framework, source-mapping structure, and
    reviewer-governance process.
  - Rebased onto the `rnica-baseline-verified-2026-09` baseline after PR
    #113 merged.
  - Documentation-only: 139 changed files, no application code, APIs,
    schemas, migrations, permissions, or production data.
  - Establishes Phase 2 discovery issues (Epic #93, Tracker #94, P2-001
    through P2-016, issues #95-#110).

- **PR #92** — CLOSED_NOT_MERGED (superseded by PR #111; contained
  unrelated application, build, configuration, dependency, and branding
  commits not appropriate for a documentation-only PR).

### Baseline Tag

- `rnica-baseline-verified-2026-09` — first verified zero-failure
  baseline on `main` (commit `3530e87f`). See
  [#114](../../issues/114) and [#115](../../issues/115) for the full
  traceability record and regression investigation policy.
