# P2-012 - Workflow Authority Validation

## Owner

- Primary: Product Owner
- Reviewer: Architecture Lead

## Priority and Target

- Priority: `Medium`
- Target: `Week 4`

## Dependencies

- Approved Patient Chart authority matrix

## Objective

Validate that each Patient Chart workflow phase presents, edits, and routes data according to the approved authority model.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `SNS_INTERNAL_WORKFLOW`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Validate Patient Story
- [ ] Validate Know the Patient
- [ ] Validate Assess
- [ ] Validate Document Visit
- [ ] Validate Manage Treatment
- [ ] Validate Plan Care
- [ ] Validate Coordinate Team
- [ ] Validate Ensure Compliance
- [ ] Validate Handle Transitions
- [ ] Validate Track & Report

## Required Deliverables

- [ ] Workflow authority verification matrix
- [ ] Write-authority map
- [ ] Conflict log

## Findings

### Current State

### Target State

### Gaps

### Risks

### Affected Repository Paths

### Historical-Record Impact

### Test Impact

## Exit Criteria

- [ ] All ten workflow phases assessed
- [ ] Display versus edit authority documented
- [ ] Silent cross-workspace mutations identified
- [ ] Conflicts classified

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
