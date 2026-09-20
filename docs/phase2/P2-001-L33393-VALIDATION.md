# P2-001 - LCD L33393 Validation

## Owner

- Primary: Compliance Lead
- Reviewer: Clinical Reviewer

## Priority and Target

- Priority: `Critical`
- Target: `Week 1`

## Dependencies

- PR #92 merged
- `L33393_VALIDATION_CHECKLIST.md` available

## Objective

Complete section-level validation of LCD L33393 and map verified requirements to the repository.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Regulatory/Authority Drivers

- `LCD_DOCUMENTATION_GUIDANCE`
- `FEDERAL_CMS_REQUIRED`

## Validation Tasks

- [ ] Retrieve and review the complete LCD L33393 source
- [ ] Record contractor, jurisdiction, revision, effective date, and status
- [ ] Map general indications and documentation guidance
- [ ] Map non-disease-specific guidance
- [ ] Map all disease-specific sections
- [ ] Identify conflicts with L34538 or newer CMS guidance
- [ ] Update source mapping with exact source locations
- [ ] Keep L33393 marked `DEEP_REVIEW_REQUIRED` until all exit criteria are met

### Coverage Amendment (Phase 2 Review): Principal-Diagnosis Restriction Screening

- [ ] Screen proposed principal hospice diagnoses against all attached never-primary, inappropriate-primary, and not-allowable diagnosis lists.
- [ ] Distinguish principal terminal diagnosis, related conditions, coexisting conditions, and symptoms.
- [ ] Record conflicts between code restrictions, disease guides, and current LCD guidance.
- [ ] Follow the newest controlling CMS source when guidance conflicts.

## Required Deliverables

- [ ] Section-level L33393 source map
- [ ] Applicability and conflict log
- [ ] Repository mapping table
- [ ] Updated source-mapping entries

## Findings

### Current State

### Target State

### Gaps

### Risks

### Affected Repository Paths

### Historical-Record Impact

### Test Impact

## Exit Criteria

- [ ] Every mapped requirement has an exact source location
- [ ] Conflicts identify the controlling source
- [ ] No automatic eligibility logic is authorized
- [ ] Reviewer records VALIDATED, VALIDATED_WITH_GAPS, or NOT_VALIDATED

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
