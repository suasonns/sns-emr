# PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md

## Status

DOCUMENTATION-ONLY REPOSITORY DISCOVERY

## Code Authorization

NOT AUTHORIZED

Do not modify:
- Application code
- APIs
- Database schemas
- Migration history
- Production data
- Routes
- Components
- Validation behavior
- Permissions
- Workflow behavior

---

# Objective

Validate the approved Patient Chart workflow and authority model against
the current repository.

Create documentation that identifies:
- Current source ownership
- Existing implementation
- Reusable capabilities
- Rewiring requirements
- Redesign requirements
- Missing capabilities
- Defects
- Authority conflicts
- Compliance risks
- Required implementation decisions

Do not resolve gaps through code in this pull request.

---

# Documents to Review

1. `PATIENT_CHART_WORKFLOW_AUTHORITY.md`
2. `PATIENT_CHART_CORRECTION_LIST.md`
3. `PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md`
4. `PATIENT_CHART_AUTHORITY_MAP.md`
5. Existing RNICA authority and implementation-planning documents

---

# Required Deliverables

Create:
1. `PATIENT_CHART_CURRENT_STATE_MAPPING.md`
2. `PATIENT_CHART_GAP_ANALYSIS.md`
3. `PATIENT_CHART_IMPLEMENTATION_DISCOVERY.md`

Documentation only.

---

# Workflow Phases to Map

1. Patient Story
2. Know the Patient
3. Assess
4. Document Visit
5. Manage Treatment
6. Plan Care
7. Coordinate Team
8. Ensure Compliance
9. Handle Transitions
10. Track & Report

---

# Required Repository Inventory

For every workflow phase identify:
- Existing route
- Existing navigation entry
- Existing component
- Existing service
- Existing API endpoint
- Existing database entity
- Existing validator
- Existing permission
- Existing authentication behavior
- Existing signature behavior
- Existing amendment behavior
- Existing audit event
- Existing status model
- Existing dependency
- Existing automated test
- Existing feature flag
- Existing historical-data behavior

Use exact repository paths and identifiers.

Do not invent missing paths.

---

# Required Classification

Classify every target capability as one of:
- `REUSABLE`
- `REQUIRES_PRESENTATION_REWIRING`
- `REQUIRES_LOGIC_REWIRING`
- `REQUIRES_REDESIGN`
- `MISSING_PRESENTATION`
- `MISSING_API_OR_SERVICE`
- `MISSING_SCHEMA`
- `CONFIRMED_DEFECT`
- `BLOCKED_BY_AUTHORITY_DECISION`
- `FUTURE_PRODUCT_DIRECTION`
- `NOT_CURRENTLY_CONNECTED`

---

# Ownership Validation

For every displayed value or action document:
- Current authority owner
- Approved target authority owner
- Current producer
- Approved producer
- Current consumers
- Approved consumers
- Editability
- Source provenance
- Authentication requirement
- Signature requirement
- Audit requirement
- Ownership conflict, if any

Patient Chart shall not create duplicate ownership for a record already
owned by an authoritative source workspace.

---

# Critical Authority Validations

Verify:
- Patient Story owns nothing.
- Know the Patient owns nothing.
- RNICA remains assessment authority.
- Visit Notes remains visit-documentation authority.
- Medication records remain owned by the Medication domain.
- Physician Orders remain owned by the Physician Orders domain.
- DME remains owned by the DME domain.
- Plan of Care remains the Plan of Care authority.
- Coordinate Team does not silently mutate source records.
- Ensure Compliance does not own clinical source data.
- Handle Transitions preserves distinct transition records.
- Track & Report is read-only.
- Finalization remains the sole active Final Clinical Narrative
  authority.
- Physician certification remains separate from LCD evidence
  presentation.
- Review, approval, authentication, and signature remain separate
  events.

---

# Compliance Discovery

## Admission and Certification
Document:
- Physician-order dependency for admission
- Certification record ownership
- Certification signers
- Certification dates
- Narrative location
- Authentication
- Recertification behavior
- Linkage to Patient Story and Ensure Compliance

Do not equate LCD evidence with certification.

## Assessment
Document:
- Initial assessment
- Comprehensive assessment
- Assessment updates
- RNICA ownership
- Discipline-assessment ownership
- Assessment-to-Plan-of-Care links
- Filing and audit behavior

## Plan of Care
Document:
- Plan of Care entity
- Version history
- IDT development
- Physician collaboration
- Approval and signature
- Proposed versus approved modifications
- Review cadence
- Linkage to visits and assessments

## Medical Records
Document:
- Record retrieval
- Reconciliation
- Deficiency analysis
- Filing and indexing
- Quality/content control
- Authorized access
- Correction
- Amendment
- Addendum
- Written reason for alteration
- Original-record preservation
- Denial justification
- Audit trail

## Electronic Records
Document:
- Access control
- Unique user identification
- Authentication
- Electronic signatures
- Countersignatures
- Shared-credential prevention
- Audit-event tracking
- Backup behavior
- Disaster-recovery/manual-documentation behavior
- Multi-provider record linkage

---

# Hospice Eligibility and LCD Discovery

Review:
- `cms guidelines.pdf`, LCD L34538
- `1.pdf`, LCD L33393
- Attached applicable disease-specific terminal-prognosis guides
- Attached diagnosis-restriction lists, where available

Document:
- Current principal-diagnosis handling
- Diagnosis-restriction screening
- Related and coexisting conditions
- Baseline and follow-up decline evidence
- Functional status
- ADL dependence
- Nutritional evidence
- Symptoms
- Complications
- Hospitalizations
- Comorbidities
- Objective findings
- Disease-specific criteria
- Recertification evidence
- Physician narrative support
- Contradictory evidence

Do not implement an automatic eligibility pass/fail engine.

Classify LCD output as documentation support, not physician
certification.

---

# California and CMS Source Mapping

Create a source-mapping section in every deliverable.

## California CDPH
Map findings to:
- Section 74860: Admission
- Section 74864: Assessments
- Section 74868: Plan of Care
- Section 74872: Plan of Care Review
- Section 74888: Medical Record Service
- Electronic Health Records requirements
- Applicable record-authentication, amendment, correction, addendum,
  access, audit, backup, and disaster-recovery requirements

## CMS and LCD
Map findings to:
- CMS hospice certification requirements
- LCD L34538
- LCD L33393, where applicable
- Current applicable disease-specific guides
- Non-disease-specific decline and baseline guidance
- Individualized documentation supporting physician judgment

Label every requirement as:
- `CALIFORNIA_REQUIRED`
- `FEDERAL_CMS_REQUIRED`
- `LCD_DOCUMENTATION_GUIDANCE`
- `ACCREDITATION_REQUIREMENT`
- `SNS_INTERNAL_WORKFLOW`
- `REPOSITORY_CURRENT_STATE`
- `FUTURE_PRODUCT_DECISION`

Do not describe an SNS internal workflow as a CMS or California
requirement.

---

# Deliverable Format

Each deliverable must include:
- Current state
- Target state
- Authority owner
- Source mapping
- Gap
- Compliance risk
- Patient-safety risk
- Audit risk
- Affected files
- Affected services
- Dependencies
- Required decision
- Suggested implementation sequence
- Test impact
- Historical-record impact
- Blocking status

---

# Repository-Safe Acceptance Checklist

## Documentation Boundary
- [ ] Documentation-only changes
- [ ] No application-code changes
- [ ] No API changes
- [ ] No schema changes
- [ ] No migrations
- [ ] No production-data changes
- [ ] No workflow implementation

## Coverage
- [ ] Every workflow phase mapped
- [ ] Every source owner mapped
- [ ] Every route mapped
- [ ] Every component mapped
- [ ] Every service mapped
- [ ] Every API mapped
- [ ] Every database entity mapped
- [ ] Every validator mapped
- [ ] Every permission mapped
- [ ] Every signature path mapped
- [ ] Every amendment path mapped
- [ ] Every audit event mapped

## Clinical and Compliance Integrity
- [ ] No UI-generated eligibility verdict
- [ ] No UI-generated prognosis
- [ ] No UI-generated certification
- [ ] No silent order creation
- [ ] No inferred physician approval
- [ ] No review represented as signature
- [ ] No silent source-record overwrite
- [ ] Plan of Care versions preserved
- [ ] Proposed and approved modifications distinguished
- [ ] Corrections and addenda remain traceable
- [ ] Discharge reconciliation mapped
- [ ] Deficiency analysis mapped

## Source Mapping
- [ ] California rules mapped
- [ ] CMS requirements mapped
- [ ] LCD guidance mapped
- [ ] SNS internal rules labeled separately
- [ ] Repository current state labeled separately
- [ ] Conflicts documented
- [ ] Newest controlling authority identified

## Final Gate
- [ ] Every capability classified
- [ ] Reusable capabilities identified
- [ ] Rewiring needs identified
- [ ] Redesign needs identified
- [ ] Missing capabilities identified
- [ ] Defects separated from future direction
- [ ] Authority blockers remain unresolved rather than assumed
- [ ] No application implementation authorized

---

# Completion Rule

Repository discovery is complete only when every Patient Chart workflow
phase, source authority, dependency, authentication path, signature
path, Plan of Care path, certification path, correction/amendment path,
and audit path has been documented.

Only after these deliverables are approved may Patient Chart
implementation planning begin.
