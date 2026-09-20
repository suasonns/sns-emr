# P2-006 - Medical Record Correction Audit

## Owner

- Primary: Compliance Lead
- Reviewer: Engineering Lead

## Priority and Target

- Priority: `High`
- Target: `Week 2`

## Dependencies

- Repository access

## Objective

Validate correction behavior, original-entry preservation, reason, dates, authentication, and wrong-record handling.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `CALIFORNIA_REQUIRED`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Locate correction services, APIs, entities, and UI
- [ ] Verify original entry preservation
- [ ] Verify correction reason
- [ ] Verify discovery date
- [ ] Verify correction date
- [ ] Verify correcting user and authentication
- [ ] Verify wrong-patient and duplicate-record correction handling
- [ ] Verify audit events

## Required Deliverables

- [ ] Correction-control inventory
- [ ] Evidence matrix
- [ ] Gap and risk list

## Findings

### Current State

### Target State

### Gaps

### Risks

### Affected Repository Paths

### Historical-Record Impact

### Test Impact

## Exit Criteria

- [ ] Every correction requirement is mapped
- [ ] Silent overwrite risks identified
- [ ] Wrong-record behavior documented
- [ ] Audit evidence attached

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
