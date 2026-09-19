# PATIENT_CHART_CROSS_REFERENCE_REVIEW.md

## Status

GOOD WITH 4 RECOMMENDED CHECKS

Cross-reference consistency review across the Patient Chart
documentation baseline in PR #92. This document does not reopen any of
the reviewed documents.

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED BY THIS DOCUMENT

## Confirmed Consistent

| Document | Cross-reference Status |
| --- | --- |
| PATIENT_CHART_WORKFLOW_AUTHORITY.md | Consistent with authority model |
| PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md | Consistent with California/CMS boundaries |
| PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md | Consistent with ownership structure |
| PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md | Consistent with repository-discovery requirements |
| PATIENT_CHART_SOURCE_MAPPING.md | Consistent with source-classification model |
| PATIENT_CHART_REVIEWER_SIGN_OFF.md | Consistent with approval workflow |

## Recommended Checks

The review status ("GOOD WITH 4 RECOMMENDED CHECKS") was supplied
without an itemized list of the four checks. Rather than invent that
list, this document maps it to the four conditions already tracked in
`PATIENT_CHART_REVIEWER_SIGN_OFF.md`, since no distinct set of checks
was provided:

1. Recheck cross-references once **PC-COND-1** (LCD L33393
   section-level mapping, tracked in
   `PATIENT_CHART_LCD_L33393_VALIDATION_CHECKLIST.md`) is resolved and
   `PATIENT_CHART_SOURCE_MAPPING.md` is updated.
2. Recheck cross-references once **PC-COND-2** (certification ownership
   and status-flow validation) is resolved in
   `PATIENT_CHART_CURRENT_STATE_MAPPING.md`.
3. Recheck cross-references once **PC-COND-3** (Plan-of-Care approval/
   signature workflow validation) is resolved in
   `PATIENT_CHART_CURRENT_STATE_MAPPING.md` /
   `PATIENT_CHART_GAP_ANALYSIS.md`.
4. Recheck cross-references once **PC-COND-4** (correction/amendment/
   addendum audit-behavior validation) is resolved in
   `PATIENT_CHART_CURRENT_STATE_MAPPING.md` /
   `PATIENT_CHART_IMPLEMENTATION_DISCOVERY.md`.

If a different set of four checks was intended, this section should be
corrected and this provenance note removed.

## Provenance note

The "Confirmed Consistent" table above was supplied verbatim. The
"Recommended Checks" section was not supplied in itemized form; it is
inferred from the four conditions already recorded as PC-COND-1 through
PC-COND-4 in `PATIENT_CHART_REVIEWER_SIGN_OFF.md`, and is flagged here
as an inference rather than a directly supplied requirement.

## Implementation boundary

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED HERE
