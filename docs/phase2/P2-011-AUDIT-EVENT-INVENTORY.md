# P2-011 - Audit Event Inventory

## Owner

- Primary: Engineering Lead
- Reviewer: Compliance Lead

## Priority and Target

- Priority: `High`
- Target: `Week 3`

## Dependencies

- P2-010

## Objective

Inventory all patient-record and workflow audit events relevant to Patient Chart authority.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `CALIFORNIA_REQUIRED`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Inventory create, update, delete, lock, unlock, and status events
- [ ] Inventory certification events
- [ ] Inventory POC events
- [ ] Inventory visit-note events
- [ ] Inventory correction, amendment, and addendum events
- [ ] Inventory discharge and transition events
- [ ] Record actor, role, timestamp, source, before/after state, and retention
- [ ] Identify missing or inconsistent events

### Coverage Amendment (Phase 2 Review): Backup, Disaster Recovery, and Downtime

- [ ] Validate backup configuration and evidence.
- [ ] Validate disaster-recovery procedures.
- [ ] Validate manual clinical documentation during EHR downtime.
- [ ] Validate restoration and reconciliation of downtime documentation.
- [ ] Validate linkage of electronic health information from multiple providers.
- [ ] Validate emergency and after-hours record retrieval.

### Coverage Amendment (Phase 2 Review): Visit-Type and Completion-Evidence Validation

- [ ] Inventory and normalize visit types used by routes, APIs, services, database fields, and UI components.
- [ ] Validate that completed visits require completion timestamps.
- [ ] Validate that completed visit tasks link to supporting documentation.
- [ ] Confirm that schedule status alone does not represent completed clinical documentation.
- [ ] Identify inconsistent or duplicate visit-status values.

## Required Deliverables

- [ ] Audit-event catalog
- [ ] Event field matrix
- [ ] Missing-event list
- [ ] Test inventory

## Findings

### Current State

### Target State

### Gaps

### Risks

### Affected Repository Paths

### Historical-Record Impact

### Test Impact

## Exit Criteria

- [ ] All authority-critical workflows assessed
- [ ] Missing events classified
- [ ] Retention and retrieval documented
- [ ] Historical impact documented

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
