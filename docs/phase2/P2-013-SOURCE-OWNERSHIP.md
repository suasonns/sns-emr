# P2-013 - Source Ownership Verification

## Owner

- Primary: Product Owner
- Reviewer: Architecture Lead

## Priority and Target

- Priority: `Medium`
- Target: `Week 4`

## Dependencies

- P2-012

## Objective

Verify the authoritative owner and provenance chain for every source domain consumed by Patient Chart.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `SNS_INTERNAL_WORKFLOW`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Validate Facesheet and Intake ownership
- [ ] Validate RNICA ownership
- [ ] Validate Visit Notes ownership
- [ ] Validate Physician Orders ownership
- [ ] Validate Medications ownership
- [ ] Validate DME ownership
- [ ] Validate Plan of Care ownership
- [ ] Validate IDG and Communication ownership
- [ ] Validate Compliance and HOPE ownership
- [ ] Validate transition and reporting ownership

### Coverage Amendment (Phase 2 Review): HOPE, HUV1/HUV2, SFV, and QIES

- [ ] Validate HOPE source ownership.
- [ ] Validate HOPE Admission, Update Visit, and Discharge record relationships.
- [ ] Validate HUV1, HUV2, and SFV timing/status ownership.
- [ ] Validate QIES submission-status ownership and provenance.
- [ ] Separate official CMS requirements from SNS internal workflow.
- [ ] Record unavailable or unconnected HOPE/QIES capabilities as `NOT_CURRENTLY_CONNECTED`.

### Coverage Amendment (Phase 2 Review): Medication, Orders, DME, and Controlled Substances

- [ ] Validate medication source ownership and write authority.
- [ ] Validate physician-order draft, review, approval, signature, and discontinuation states.
- [ ] Validate DME source ownership and status transitions.
- [ ] Validate reconciliation provenance.
- [ ] Validate controlled-substance accountability and reconciliation interfaces where applicable.
- [ ] Confirm that Manage Treatment does not silently modify source records.

## Required Deliverables

- [ ] Source ownership matrix
- [ ] Producer-consumer map
- [ ] Duplicate-ownership log

## Findings

### Current State

### Target State

### Gaps

### Risks

### Affected Repository Paths

### Historical-Record Impact

### Test Impact

## Exit Criteria

- [ ] Every source has one authoritative owner
- [ ] Consumers do not silently acquire ownership
- [ ] Duplicate ownership classified
- [ ] Evidence attached

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
