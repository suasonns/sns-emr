# P2-014 - Regulatory Coverage Matrix

## Owner

- Primary: Compliance Lead
- Reviewer: Clinical and Engineering Reviewers

## Priority and Target

- Priority: `High`
- Target: `Week 4`

## Dependencies

- P2-003
- P2-005
- P2-009
- P2-011
- P2-013

## Objective

Consolidate validated California, CMS, LCD, internal, and repository-current-state requirements into one coverage matrix.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `CALIFORNIA_REQUIRED`
- `FEDERAL_CMS_REQUIRED`
- `LCD_DOCUMENTATION_GUIDANCE`
- `SNS_INTERNAL_WORKFLOW`
- `REPOSITORY_CURRENT_STATE`

## Validation Tasks

- [ ] Collect validated findings from dependency issues
- [ ] Map exact source and section
- [ ] Map repository evidence
- [ ] Assign requirement label
- [ ] Assign coverage status
- [ ] Record gaps, conflicts, and controlling authority
- [ ] Record owner and blocking status

### Coverage Amendment (Phase 2 Review): Principal-Diagnosis Restriction Screening

- [ ] Screen proposed principal hospice diagnoses against all attached never-primary, inappropriate-primary, and not-allowable diagnosis lists.
- [ ] Distinguish principal terminal diagnosis, related conditions, coexisting conditions, and symptoms.
- [ ] Record conflicts between code restrictions, disease guides, and current LCD guidance.
- [ ] Follow the newest controlling CMS source when guidance conflicts.

### Coverage Amendment (Phase 2 Review): HOPE, HUV1/HUV2, SFV, and QIES

- [ ] Validate HOPE source ownership.
- [ ] Validate HOPE Admission, Update Visit, and Discharge record relationships.
- [ ] Validate HUV1, HUV2, and SFV timing/status ownership.
- [ ] Validate QIES submission-status ownership and provenance.
- [ ] Separate official CMS requirements from SNS internal workflow.
- [ ] Record unavailable or unconnected HOPE/QIES capabilities as `NOT_CURRENTLY_CONNECTED`.

### Coverage Amendment (Phase 2 Review): Admission and Assessment Timing

- [ ] Validate physician-order dependency for admission.
- [ ] Validate initial-assessment completion and filing behavior.
- [ ] Validate comprehensive-assessment completion and filing behavior.
- [ ] Validate periodic assessment review and update behavior.
- [ ] Validate assessment-to-Plan-of-Care linkage.
- [ ] Validate timestamps, authorship, status, and evidence supporting completion.

### Coverage Amendment (Phase 2 Review): Privacy, Release of Information, and Amendment-Request Rights

- [ ] Validate patient record-access request workflow.
- [ ] Validate release-of-information workflow and request timestamps.
- [ ] Validate correction/amendment request notifications.
- [ ] Validate approval or denial recording.
- [ ] Validate written justification for denied requests.
- [ ] Validate retention and disposal controls.
- [ ] Validate HIPAA and CMIA access boundaries.
- [ ] Validate breach or suspected-breach reporting workflow.

### Coverage Amendment (Phase 2 Review): Backup, Disaster Recovery, and Downtime

- [ ] Validate backup configuration and evidence.
- [ ] Validate disaster-recovery procedures.
- [ ] Validate manual clinical documentation during EHR downtime.
- [ ] Validate restoration and reconciliation of downtime documentation.
- [ ] Validate linkage of electronic health information from multiple providers.
- [ ] Validate emergency and after-hours record retrieval.

## Required Deliverables

- [ ] Regulatory coverage matrix
- [ ] Source-conflict register
- [ ] Unmapped-requirement list

## Findings

### Current State

### Target State

### Gaps

### Risks

### Affected Repository Paths

### Historical-Record Impact

### Test Impact

## Exit Criteria

- [ ] Every included requirement has evidence
- [ ] Requirement labels are consistent
- [ ] Conflicts identify controlling authority
- [ ] Unmapped items are explicit

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
