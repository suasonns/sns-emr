# P2-014 - Regulatory Coverage Matrix

## Owner

- Primary: Compliance Lead
- Reviewer: Clinical and Engineering Reviewers

## Priority and Target

- Priority: `High`
- Target: `Week 4`

## Dependencies

- P2-003
- P2-005
- P2-009
- P2-011
- P2-013

## Objective

Consolidate validated California, CMS, LCD, internal, and repository-current-state requirements into one coverage matrix.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `CALIFORNIA_REQUIRED`
- `FEDERAL_CMS_REQUIRED`
- `LCD_DOCUMENTATION_GUIDANCE`
- `SNS_INTERNAL_WORKFLOW`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Collect validated findings from dependency issues
- [ ] Map exact source and section
- [ ] Map repository evidence
- [ ] Assign requirement label
- [ ] Assign coverage status
- [ ] Record gaps, conflicts, and controlling authority
- [ ] Record owner and blocking status

## Required Deliverables

- [ ] Regulatory coverage matrix
- [ ] Source-conflict register
- [ ] Unmapped-requirement list

## Findings

### Current State

### Target State

### Gaps

### Risks

### Affected Repository Paths

### Historical-Record Impact

### Test Impact

## Exit Criteria

- [ ] Every included requirement has evidence
- [ ] Requirement labels are consistent
- [ ] Conflicts identify controlling authority
- [ ] Unmapped items are explicit

## Required Evidence

- Exact repository paths
- Relevant routes, components, services, APIs, database entities, validators, permissions, and tests
- Current status model and audit behavior
- Screenshots or excerpts where useful, without patient-sensitive information
- Source classification for every requirement

## Allowed Requirement Labels

- `CALIFORNIA_REQUIRED`
- `FEDERAL_CMS_REQUIRED`
- `LCD_DOCUMENTATION_GUIDANCE`
- `ACCREDITATION_REQUIREMENT`
- `SNS_INTERNAL_WORKFLOW`
- `REPOSITORY_CURRENT_STATE`
- `FUTURE_PRODUCT_DECISION`

## Status

- [x] `NOT_STARTED`
- [ ] `IN_PROGRESS`
- [ ] `REVIEW`
- [ ] `COMPLETE`
- [ ] `BLOCKED`
