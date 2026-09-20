# PATIENT_CHART_CROSS_REFERENCE_REVIEW.md

## Status

`PASS_WITH_VERIFICATION_ITEMS`

Supersedes the earlier draft of this document (which flagged an
unconfirmed "4 recommended checks" inference). This version supplies
the canonical terminology, canonical cross-reference requirements, and
a verification checklist directly.

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED BY THIS DOCUMENT

## Canonical Workflow Names

Use exactly:

1. Patient Story
2. Know the Patient
3. Assess
4. Document Visit
5. Manage Treatment
6. Plan Care
7. Coordinate Team
8. Ensure Compliance
9. Handle Transitions
10. Track & Report

## Canonical Requirement Labels

Use only:

- `CALIFORNIA_REQUIRED`
- `FEDERAL_CMS_REQUIRED`
- `LCD_DOCUMENTATION_GUIDANCE`
- `ACCREDITATION_REQUIREMENT`
- `SNS_INTERNAL_WORKFLOW`
- `REPOSITORY_CURRENT_STATE`
- `FUTURE_PRODUCT_DECISION`

## Canonical Capability Classifications

Use only:

- `REUSABLE`
- `REQUIRES_PRESENTATION_REWIRING`
- `REQUIRES_LOGIC_REWIRING`
- `REQUIRES_REDESIGN`
- `MISSING_PRESENTATION`
- `MISSING_API_OR_SERVICE`
- `MISSING_SCHEMA`
- `CONFIRMED_DEFECT`
- `BLOCKED_BY_AUTHORITY_DECISION`
- `FUTURE_PRODUCT_DIRECTION`
- `NOT_CURRENTLY_CONNECTED`

## Canonical Plan-of-Care States

Use these authority concepts consistently:

- Draft
- Proposed
- Under Review
- Approved
- Signed
- Active
- Superseded
- Amended

Repository discovery may record different existing enum names, but
current repository values must not silently replace the approved
authority concepts.

## Canonical Certification and LCD Terms

Preferred:

- Physician Certification
- Physician Certification Status
- Supporting Evidence Identified
- LCD Supporting Evidence Present
- Clinical Documentation
- Documentation Review Complete
- Recertification

Avoid unsupported conclusions:

- Eligible
- Eligibility Confirmed
- LCD Passed
- Automatically Qualified
- Automatically Eligible
- Prognosis Generated
- Certification Verified

## Required Cross-References

- [ ] `PATIENT_CHART_WORKFLOW_AUTHORITY.md` links to the correction
      list, screen matrix, discovery prompt, compliance review, source
      mapping, and reviewer sign-off.
- [ ] `PATIENT_CHART_CORRECTION_LIST.md` references the workflow
      authority and source mapping.
- [ ] `PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md` references the
      workflow authority and correction list.
- [ ] `PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md` references all
      authority documents and the source mapping.
- [ ] `PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md` references the source
      mapping and L33393 deep-review requirement.
- [ ] `PATIENT_CHART_SOURCE_MAPPING.md` marks L33393 as
      `DEEP_REVIEW_REQUIRED` until validated.
- [ ] `PATIENT_CHART_REVIEWER_SIGN_OFF.md` links to the source mapping,
      compliance review, and L33393 checklist.
- [ ] PR description links all included governance artifacts.
- [ ] Acceptance criteria reference the reviewer sign-off and source
      mapping.

## Verification Result

- Workflow naming: [ ] PASS [ ] FAIL
- Requirement labels: [ ] PASS [ ] FAIL
- Capability classifications: [ ] PASS [ ] FAIL
- Plan-of-Care terminology: [ ] PASS [ ] FAIL
- Certification terminology: [ ] PASS [ ] FAIL
- File links: [ ] PASS [ ] FAIL
- Documentation-only boundary: [ ] PASS [ ] FAIL

Reviewer:

Date:

Notes:

## Implementation boundary

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED HERE
