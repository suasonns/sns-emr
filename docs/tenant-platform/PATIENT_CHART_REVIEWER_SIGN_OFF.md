# PATIENT_CHART_REVIEWER_SIGN_OFF.md

## Status

REVIEWER APPROVAL RECORD — TEMPLATE (unsigned)

Companion sign-off record for the Patient Chart documentation baseline:
`PATIENT_CHART_WORKFLOW_AUTHORITY.md`,
`PATIENT_CHART_CORRECTION_LIST.md`,
`PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md`,
`PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md`,
`PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md`, and
`PATIENT_CHART_SOURCE_MAPPING.md`. None of those six documents is
reopened by this document.

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED BY THIS DOCUMENT

This record ships unsigned as part of the documentation baseline. Rows
are completed by reviewers outside this pull request as approvals occur.

## Approval Scope

Reviewer signatures approve:

- The Patient Chart documentation baseline
- The repository-discovery scope
- The authority and source-classification model
- The documentation-only pull-request boundary

Reviewer signatures do not approve:

- Application implementation
- Patient Chart production deployment
- API or schema changes
- Database migrations
- Production-data modification
- Automated eligibility or prognosis decisions
- Physician-certification automation
- Automatic Plan-of-Care activation

## Required Reviewers

| Review Area | Reviewer | Role or Credentials | Decision | Date | Conditions |
|---|---|---|---|---|---|
| Product and Workflow Authority | | | | | |
| Clinical Authority | | | | | |
| California Compliance | | | | | |
| CMS and LCD | | | | | |
| Privacy, Security, and Record Integrity | | | | | |
| Engineering Discovery | | | | | |

Allowed decisions:
- `APPROVED`
- `APPROVED_WITH_CONDITIONS`
- `CHANGES_REQUIRED`
- `BLOCKED`

## Conditional-Approval Tracking

| Condition ID | Review Area | Required Action | Owner | Blocking | Resolution Evidence | Status |
|---|---|---|---|---|---|---|
| | | | | YES / NO | | OPEN / RESOLVED |

## Final Gate Checklist

- [ ] Every required review area has a recorded decision.
- [ ] Every approving reviewer is identified.
- [ ] Reviewer role or credentials are recorded.
- [ ] Every conditional approval has a corresponding condition record.
- [ ] Every blocking condition is resolved.
- [ ] Resolution evidence is linked.
- [ ] California and CMS requirements are classified separately.
- [ ] Repository-current-state findings are not represented as
      regulatory requirements.
- [ ] SNS workflow decisions are not represented as regulatory
      requirements.
- [ ] Insufficiently retrieved sources remain marked for deeper review.
- [ ] The source-citation register (`PATIENT_CHART_SOURCE_MAPPING.md`)
      has been reviewed.
- [ ] The documentation-only boundary remains intact.
- [ ] No application implementation is authorized.

## Final Authorization

Documentation pull request:
- [ ] APPROVED
- [ ] APPROVED WITH CONDITIONS
- [ ] CHANGES REQUIRED
- [ ] BLOCKED

Repository discovery:
- [ ] AUTHORIZED
- [ ] NOT AUTHORIZED

Application implementation:
- [ ] NOT AUTHORIZED

Final approver:

Role:

Date:

Decision notes:

## Implementation boundary

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED HERE
