# P2-003 - Certification Lifecycle Validation

## Owner

- Primary: Product Owner
- Reviewer: Compliance Lead

## Priority and Target

- Priority: `Critical`
- Target: `Week 1`

## Dependencies

- P2-002

## Objective

Validate initial certification, recertification, status transitions, expiration, amendments, and audit events.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `FEDERAL_CMS_REQUIRED`
- `CALIFORNIA_REQUIRED`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Inventory existing certification states
- [ ] Map initial certification workflow
- [ ] Map recertification workflow
- [ ] Map signature and activation transitions
- [ ] Map expiration and supersession behavior
- [ ] Map correction, amendment, and addendum behavior
- [ ] Map audit events and historical records

## Required Deliverables

- [ ] Certification lifecycle diagram
- [ ] State-transition table
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

- [ ] All current states documented
- [ ] Target authority states mapped
- [ ] Untraceable transitions identified
- [ ] Historical-record impact documented

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
