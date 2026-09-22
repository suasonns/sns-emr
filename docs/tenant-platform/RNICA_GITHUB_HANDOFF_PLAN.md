# RNICA_GITHUB_HANDOFF_PLAN.md

**Status:** New (6th document in the Implementation Authority package)
**Objective:** Move RNICA from approved design to controlled implementation
documentation, then begin the broader Patient Chart workflow phase.

## A. Authority package (this repository)

`docs/tenant-platform/` contains the six controlling documents:

1. `RNICA_IMPLEMENTATION_AUTHORITY.md`
2. `RNICA_SCREEN_AUTHORITY_MATRIX.md`
3. `RNICA_DATA_MAPPING_MATRIX.md`
4. `RNICA_AI_GOVERNANCE.md`
5. `RNICA_LOCK_READINESS_MATRIX.md`
6. `RNICA_GITHUB_HANDOFF_PLAN.md` (this file)

Plus the required deliverable produced alongside them:
`RNICA_CURRENT_TO_TARGET_GAP_REPORT.md`.

Existing authority documents (`RNICA_REDESIGN_SOURCE_OF_TRUTH.md`,
`RNICA_SCREEN_BY_SCREEN_EVIDENCE_MATRIX.md`,
`RNICA_WORKFLOW_AUTHORITY_MAP.md`, `PATIENT_CHART_AUTHORITY_MAP.md`) remain
controlling for product intent and evidence traceability and are **not**
reopened by this package.

## B. This documentation pull request

This pull request:
- Adds/updates the six authority documents above.
- Adds a repository discovery appendix with exact routes, components, APIs,
  schemas, validators, adapters, audit events, and tests (folded into the
  Data Mapping and Lock Readiness matrices rather than a separate file, to
  avoid a second divergent copy of the same facts).
- Replaces every placeholder in the Data Mapping and Lock Readiness
  matrices with verified repository behavior, or marks the cell
  `[IMPLEMENTATION DISCOVERY REQUIRED]` where direct verification could not
  be completed in this pass (listed exhaustively in the Gap Report).
- Adds `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md`, classifying every target
  behavior for all 13 screens.
- Does **not** modify any application code, schema, or migration.

## C. Required gap report

See `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md`. No implementation estimate or
code plan should be approved until this classification is reviewed.

## D. Follow-on implementation plan structure (not part of this PR)

> **[PRODUCT-AUTHORITY UPDATE — 2026-09-22]** The final canonical RNICA
> screen order (navigation position, not necessarily build-increment
> order) is: 1 Patient Story, 2 Evidence & Intake, 3 Pain & Symptom
> Burden, 4 Diagnosis & LCD, 5 Functional Status, 6-13 unchanged. See
> `RNICA_NAVIGATION_SPECIFICATION.md`. Increment numbers below describe
> implementation sequencing and are not automatically the screen's
> navigation position.

The follow-on implementation plan, once approved, must be organized into
independently verifiable increments:

1. Shell, routes, navigation, shared patient header, responsive framework
   (the 13-screen navigation does not exist today — this is the largest
   single increment)
2. Patient Story and Evidence & Intake presentation
3. Functional Status and conditional scales (fix the ECOG enforcement gap)
4. Pain & Symptom Burden
5. Diagnosis & LCD, excluding any Final Clinical Narrative duplication
6. Body Systems
7. Caregiver & Support and Safety & Clinical Risk
8. ACP & Goals of Care (resolve the ACP hard-required-field count question)
9. Orders & POC explicit actions
10. Compliance & Readiness parity
11. AI Action Center governance and freshness
12. Finalization, signature, lock, amendment, audit (fix the `status`
    reset-to-`DRAFT` defect)
13. Regression, accessibility, responsive, and historical-record
    verification

Each increment must identify affected ownership domains, tests, migration
impact, rollback/feature-flag behavior, and acceptance criteria.

## E. Figma-limit handling

The approved Figma production-candidate screens are the visual baseline.
Older/duplicate frames are superseded. Apply these terminology corrections
during implementation without reopening architecture:
- Replace eligibility-determination language with evidence-support language.
- Use "LCD Supporting Evidence Present" / "Supports LCD documentation review."
- State that physician certification remains required.
- Preserve Finalization as the sole Final Clinical Narrative authority.

Record any remaining visual discrepancy as a design-debt item, not as
permission to reinterpret authority.

## F. Gate before Patient Chart redesign

RNICA need not be fully coded before Patient Chart design begins. The
required gate is:

- The six RNICA authority documents are committed.
- Repository mappings and lock matrices contain no unresolved placeholders
  for critical paths (non-critical cells may remain
  `[IMPLEMENTATION DISCOVERY REQUIRED]` if listed in the Gap Report).
- The RNICA Current-to-Target Gap Report is approved.
- Figma frames are versioned/superseded clearly.
- No unresolved narrative, AI, eligibility, signature, lock, or audit
  authority conflict remains.

Then, and only then, create `PATIENT_CHART_WORKFLOW_AUTHORITY.md` using
`PATIENT_CHART_AUTHORITY_MAP.md` as ownership authority and RNICA as the
workflow-first proof of concept.

## G. Copy-paste instruction (for future automation/handoff)

> Add the RNICA implementation-authority documents exactly as the
> implementation governance baseline. Do not modify application code in the
> documentation pull request. Validate every screen against the current
> repository and replace placeholders with exact routes, components,
> fields, API/service calls, validators, HOPE/POC mappings, lock checks,
> amendment behavior, audit events, and tests. Produce a current-to-target
> gap report using the required implementation classifications. Preserve
> Finalization as the sole active Clinical Narrative authority, preserve
> historical data and audit history, keep AI advisory only, and do not
> present LCD evidence as physician eligibility determination. After the
> documentation package and gap report are approved, prepare a separate
> phased implementation plan. The broader Patient Chart workflow phase may
> begin after the documentation gate, without waiting for RNICA coding to
> finish.
