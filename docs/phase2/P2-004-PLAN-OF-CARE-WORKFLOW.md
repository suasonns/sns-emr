# P2-004 - Plan of Care Workflow Audit

## Owner

- Primary: Clinical Lead
- Reviewer: Compliance Lead

## Priority and Target

- Priority: `High`
- Target: `Week 2`

## Dependencies

- Approved authority baseline

## Objective

Validate Plan-of-Care development, proposal, physician collaboration, approval, signature, activation, and version behavior.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `CALIFORNIA_REQUIRED`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Locate POC routes, components, services, APIs, and entities
- [ ] Map assessment-to-POC linkage
- [ ] Map IDT development workflow
- [ ] Map physician collaboration
- [ ] Map approval and signature events
- [ ] Map activation behavior
- [ ] Map proposed versus approved modifications
- [ ] Map all version-storage behavior

## Required Deliverables

- [ ] POC workflow map
- [ ] POC ownership matrix
- [ ] POC state-transition table
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

- [ ] Proposal and activation are distinguishable
- [ ] Approval and signature are traceable
- [ ] All versions are accounted for
- [ ] Repository evidence attached

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
