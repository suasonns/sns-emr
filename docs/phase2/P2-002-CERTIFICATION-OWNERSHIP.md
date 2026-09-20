# P2-002 - Certification Ownership Audit

## Owner

- Primary: Product Owner
- Reviewer: Compliance Lead

## Priority and Target

- Priority: `Critical`
- Target: `Week 1`

## Dependencies

- P2-001

## Objective

Identify the authoritative certification record, owners, signers, storage, and consumers.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `FEDERAL_CMS_REQUIRED`
- `CALIFORNIA_REQUIRED`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Locate certification routes, components, services, APIs, and entities
- [ ] Identify authorized certifying practitioner roles
- [ ] Identify signature and authentication records
- [ ] Identify narrative storage and linkage
- [ ] Identify benefit-period or episode linkage
- [ ] Identify Patient Story and Compliance consumers
- [ ] Document duplicate or conflicting ownership

## Required Deliverables

- [ ] Certification ownership matrix
- [ ] Repository path inventory
- [ ] Ownership-conflict log

## Findings

### Current State

### Target State

### Gaps

### Risks

### Affected Repository Paths

### Historical-Record Impact

### Test Impact

## Exit Criteria

- [ ] Authoritative owner identified
- [ ] Signer and authentication source identified
- [ ] Consumers documented
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
