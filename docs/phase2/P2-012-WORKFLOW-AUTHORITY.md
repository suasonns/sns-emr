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

### Coverage Amendment (Phase 2 Review): Admission and Assessment Timing

- [ ] Validate physician-order dependency for admission.
- [ ] Validate initial-assessment completion and filing behavior.
- [ ] Validate comprehensive-assessment completion and filing behavior.
- [ ] Validate periodic assessment review and update behavior.
- [ ] Validate assessment-to-Plan-of-Care linkage.
- [ ] Validate timestamps, authorship, status, and evidence supporting completion.

### Coverage Amendment (Phase 2 Review): Visit-Type and Completion-Evidence Validation

- [ ] Inventory and normalize visit types used by routes, APIs, services, database fields, and UI components.
- [ ] Validate that completed visits require completion timestamps.
- [ ] Validate that completed visit tasks link to supporting documentation.
- [ ] Confirm that schedule status alone does not represent completed clinical documentation.
- [ ] Identify inconsistent or duplicate visit-status values.

### Coverage Amendment (Phase 2 Review): Medication, Orders, DME, and Controlled Substances

- [ ] Validate medication source ownership and write authority.
- [ ] Validate physician-order draft, review, approval, signature, and discontinuation states.
- [ ] Validate DME source ownership and status transitions.
- [ ] Validate reconciliation provenance.
- [ ] Validate controlled-substance accountability and reconciliation interfaces where applicable.
- [ ] Confirm that Manage Treatment does not silently modify source records.

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
