# P2-007 - Amendment Workflow Audit

## Owner

- Primary: Compliance Lead
- Reviewer: Engineering Lead

## Priority and Target

- Priority: `High`
- Target: `Week 2`

## Dependencies

- P2-006

## Objective

Validate amendment requests, decisions, notifications, denial justification, record linkage, and audit history.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `CALIFORNIA_REQUIRED`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Locate amendment routes, components, services, APIs, and entities
- [ ] Map patient amendment request intake
- [ ] Map approve/deny decision
- [ ] Map notifications
- [ ] Map written denial justification
- [ ] Map source-record linkage
- [ ] Map audit and historical retention

### Coverage Amendment (Phase 2 Review): Privacy, Release of Information, and Amendment-Request Rights

- [ ] Validate patient record-access request workflow.
- [ ] Validate release-of-information workflow and request timestamps.
- [ ] Validate correction/amendment request notifications.
- [ ] Validate approval or denial recording.
- [ ] Validate written justification for denied requests.
- [ ] Validate retention and disposal controls.
- [ ] Validate HIPAA and CMIA access boundaries.
- [ ] Validate breach or suspected-breach reporting workflow.

## Required Deliverables

- [ ] Amendment workflow map
- [ ] Decision and notification matrix
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

- [ ] Request and decision are traceable
- [ ] Denial justification is retained
- [ ] Original record is preserved
- [ ] Audit behavior documented

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
