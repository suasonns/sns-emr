# P2-009 - Reconciliation & Deficiency Analysis Audit

## Owner

- Primary: Compliance Lead
- Reviewer: Engineering Lead

## Priority and Target

- Priority: `High`
- Target: `Week 3`

## Dependencies

- P2-006

## Objective

Validate discharge record reconciliation, missing-information detection, resolution tracking, and completion states.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `CALIFORNIA_REQUIRED`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Locate reconciliation and deficiency implementations
- [ ] Map discharge reconciliation trigger
- [ ] Map required-record inventory
- [ ] Map missing-information detection
- [ ] Map deficiency severity and owner
- [ ] Map resolution destination
- [ ] Map completion and reopening
- [ ] Map audit history

## Required Deliverables

- [ ] Reconciliation workflow map
- [ ] Deficiency-analysis matrix
- [ ] Completion-state table
- [ ] Gap log

## Findings

### Current State

### Target State

### Gaps

### Risks

### Affected Repository Paths

### Historical-Record Impact

### Test Impact

## Exit Criteria

- [ ] Clinical and administrative discharge states are distinguished
- [ ] Missing information is traceable
- [ ] Resolution and completion evidence are documented
- [ ] Audit history is mapped

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
