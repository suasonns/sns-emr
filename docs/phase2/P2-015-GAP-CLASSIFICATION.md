# P2-015 - Gap Classification Review

## Owner

- Primary: Product Owner
- Reviewer: Architecture and Compliance Leads

## Priority and Target

- Priority: `High`
- Target: `Week 4`

## Dependencies

- P2-014

## Objective

Classify each evidence-backed gap for Phase 3 planning without implementing fixes.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `SNS_INTERNAL_WORKFLOW`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Review every matrix gap
- [ ] Assign capability classification
- [ ] Assign compliance, patient-safety, audit, and historical-data risk
- [ ] Identify dependencies
- [ ] Identify smallest safe remediation direction
- [ ] Separate defect, missing capability, rewire, redesign, and future decision
- [ ] Record blocker status

## Required Deliverables

- [ ] Prioritized gap register
- [ ] Risk matrix
- [ ] Dependency map
- [ ] Recommended implementation sequence

## Findings

### Current State

### Target State

### Gaps

### Risks

### Affected Repository Paths

### Historical-Record Impact

### Test Impact

## Exit Criteria

- [ ] Every gap is classified
- [ ] Unsupported assumptions removed
- [ ] Blockers are explicit
- [ ] Phase 3 candidates identified

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
