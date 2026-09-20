# PATIENT_CHART_CORRECTION_LIST.md

## Status

APPROVED FOR DESIGN AND IMPLEMENTATION COPY CLEANUP

This document defines required Patient Chart terminology and authority
corrections. Supersedes the earlier draft correction list; consistent
with, and does not reopen, `PATIENT_CHART_WORKFLOW_AUTHORITY.md` or
`PATIENT_CHART_AUTHORITY_MAP.md`.

This document does not authorize:
- Application-code changes
- API changes
- Schema changes
- Migrations
- Production-data changes
- Workflow implementation

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED BY THIS DOCUMENT

---

# Global Authority Rules

1. Patient Chart workflow pages must not duplicate source-record ownership.
2. Presentation and aggregation do not transfer ownership.
3. Every displayed clinical, operational, certification, signature, or
   compliance status must identify its authoritative source.
4. Patient Chart must not independently determine hospice eligibility,
   terminal prognosis, physician certification, order authorization, or
   Plan of Care approval.
5. Supporting evidence must remain distinguishable from physician
   judgment and certification.
6. Signed or authenticated records must not be silently overwritten.
7. Corrections, amendments, and addenda must preserve the original
   record and remain traceable.
8. Review, approval, authentication, and signature must remain separate
   events.

---

# Patient Story

## Replace Eligibility Wording

Replace: `LCD Status: Eligible`
With: `LCD Supporting Evidence Present`

Replace: `5 of 5 Clinical Criteria Met`
With: `5 Supporting Evidence Criteria Identified`

## Replace Prognosis Wording

Do not use: `Limited life expectancy of 6 months or less`
unless Patient Story is displaying an authenticated physician
certification record.

Use: `Physician Certification Status: [Current Status]`
Add: `Source: Physician Certification Record`

If no authenticated certification record is available, display:
`Physician Certification Status Unavailable`

## Replace Trajectory Wording

Replace: `Showing Gradual Downward Trajectory`
With: `Documented Functional Decline`

Do not display predicted trajectory, generated prognosis, or automatic
eligibility conclusions.

## Patient Story Boundary

Patient Story:
- Owns no clinical data
- Is read-only
- Aggregates approved source records
- Must identify source workspaces
- Must link users to authoritative source records for editing

---

# Know the Patient

Replace: `Related to Terminal Trajectory`
With: `Hospice Related`

Retain source labels such as:
- `Source: Facesheet`
- `Source: Intake & Admission`
- `Source: Diagnosis & LCD`
- `Source: Care Team`
- `Source: Insurance`

Know the Patient must not become a new demographics, diagnosis,
insurance, or care-team authority.

---

# Document Visit

Add: `Source: Visit Notes`

Every completed visit note must retain:
- Author identity
- Professional credentials, where applicable
- Patient identifier
- Visit identifier
- Discipline
- Service date and time
- Entry date and time
- Authentication status
- Signature status
- Amendment, addendum, and correction history

Do not silently replace, merge, rewrite, or reattribute signed visit
documentation.

Review by one clinician must not be represented as another clinician's
authentication or signature.

---

# Manage Treatment

Replace: `Add New Order`
With: `Create Draft Order`

Add: `Requires Physician Review and Authorization`

If the repository supports requests rather than draft orders, use:
`Submit Order Request`

## Ownership Wording

Manage Treatment is a workflow layer.
- Medication records remain owned by the Medication domain.
- Physician-order records remain owned by the Physician Orders domain.
- DME records remain owned by the DME domain.
- Medication reconciliation remains owned by its verified source
  workflow.

Manage Treatment must not:
- Issue physician orders
- Approve physician orders
- Sign physician orders
- Infer physician approval
- Silently modify medications
- Silently create DME orders

Draft, review, approval, authentication, and signature must remain
separate states.

---

# Plan Care

Add: `Source: Plan of Care`
under Plan of Care completeness and status.

Retain: `Assessment is the source. Plan of Care is the response.`

## Plan of Care Boundary

- The Plan of Care workspace owns the Plan of Care record.
- The comprehensive assessment supplies findings and identified needs.
- The interdisciplinary team develops and proposes the Plan of Care and
  updates.
- Required physician approval and signature remain separate
  authenticated events.
- Proposed modifications must remain distinguishable from approved
  modifications.
- A proposed modification must not appear active until required
  approval is recorded.
- All Plan of Care versions must remain traceable.

Do not silently activate recommended goals, interventions, frequencies,
or modifications.

---

# Coordinate Team

Replace: `Auto Aggregator Validated`
With: `Aggregated from Approved Source Workspaces`

Replace: `Eligible for Physician Batch Signature`
With: `Pending Physician Review and Signature`

## Ownership Wording

Coordinate Team presents source-linked interdisciplinary information and
authorized coordination actions.

Coordinate Team does not own or silently modify:
- Plan of Care
- Orders
- Medications
- Visit Notes
- Communication Log
- IDG records
- CHHA records
- Volunteer records

Add source labels where applicable:
- `Source: Plan of Care`
- `Source: Physician Orders`
- `Source: Medications`
- `Source: Visit Notes`
- `Source: Communication Log`
- `Source: IDG`

Review and signature must remain separate events.

A facilitator-entered review must not be represented as a physician
signature or approval.

---

# Ensure Compliance

Replace: `LCD Eligibility Verified`
With: `LCD Documentation Review Complete`

Replace: `Eligible`
With: `Supporting Evidence Identified`

Replace: `5 of 5 Criteria Met`
With: `5 Supporting Evidence Criteria Identified`

Add: `Source: Diagnosis & LCD`

## Compliance Boundary

Ensure Compliance presents:
- Deficiencies
- Missing documentation
- Readiness checks
- Due items
- Source-linked validation results
- HOPE status
- Plan of Care status
- Order and signature status

Ensure Compliance does not:
- Determine hospice eligibility
- Generate terminal prognosis
- Perform physician certification
- Authenticate source records
- Approve Plan of Care changes
- Sign orders
- Correct source documentation
- Replace source records

Every deficiency must identify:
- Source workspace
- Source record or field
- Applicable rule
- Severity
- Resolution destination
- Last evaluated timestamp

Replace unsupported `Survey Readiness` wording with:
`Documentation Readiness`
unless repository discovery confirms a separately authorized
survey-readiness capability.

---

# Handle Transitions

Handle Transitions must preserve distinct ownership for:
- Revocation
- Transfer
- Discharge
- Death documentation
- Bereavement

Discharge completion must support:
- Medical-record reconciliation
- Missing-information review
- Deficiency analysis
- Preservation of source records
- Preservation of amendments and audit history

Transition workflows must not overwrite source discharge, death,
bereavement, visit, order, Plan of Care, communication, or assessment
records.

---

# Track & Report

Add source labels for:
- `Source: Issues & Outcomes`
- `Source: Incident Logs`
- `Source: Faxes`
- `Source: Visit Notes`
- `Source: Plan of Care`
- `Source: Compliance`

Track & Report is read-only unless a separately authorized source
workflow is opened.

Reports and analytics must not become clinical-record authority.

---

# Patient Chart Home

Replace: `Continue Assessment`
With: `Continue RNICA Assessment`

This keeps the relationship between the Patient Chart assessment phase
and RNICA explicit.

---

# Source-Ownership Labels

Use consistent source labels:
- `Source: Facesheet`
- `Source: Intake & Admission`
- `Source: RNICA`
- `Source: Physician Orders`
- `Source: Medications`
- `Source: DME`
- `Source: Plan of Care`
- `Source: Visit Notes`
- `Source: Communication Log`
- `Source: Diagnosis & LCD`
- `Source: Compliance & HOPE`
- `Source: IDG`
- `Source: Documents & Images`
- `Source: Physician Certification Record`

A workflow page may aggregate these sources but must not acquire their
authority.

---

# Prohibited Terminology

Do not use without a traceable authenticated source record:
- Eligible
- Eligibility Confirmed
- LCD Match: High
- Satisfies LCD
- Terminal Trajectory
- Prognosis Generated
- Certification Verified
- Physician Approved
- Signed
- Survey Ready

Preferred wording:
- Supporting Evidence Identified
- LCD Supporting Evidence Present
- Documentation Review Complete
- Documentation Alignment Identified
- Physician Certification Status
- Physician Certification Required
- Documented Clinical Findings
- Documented Functional Decline
- Pending Physician Review
- Pending Physician Signature
- Documentation Readiness

---

# Record-Integrity Requirements

Signed or authenticated source records must not be silently overwritten.

Corrections, amendments, and addenda must:
- Preserve the original entry
- Identify the actor
- Record the date and time
- Record the reason
- Record authentication
- Remain distinct and traceable

Denied correction or amendment requests must retain the required
written justification.

---

# California and CMS Source Mapping

## California CDPH

Primary source: `DPH-18-002E-HospiceAgencies_Text.pdf`

Map implementation and repository discovery to:
- Section 74860: Admission and certification
- Section 74864: Initial and comprehensive assessments
- Section 74868: Individualized Plan of Care
- Section 74872: Plan of Care review and updates
- Section 74888: Medical record service
- Medical-record authentication, correction, amendment, addendum,
  reconciliation, deficiency-analysis, access, and audit requirements
- Electronic-record access control, unique authentication, backup, and
  disaster-recovery requirements

## CMS and LCD

Primary sources:
- `cms guidelines.pdf`, LCD L34538
- `1.pdf`, LCD L33393
- Applicable attached disease-specific terminal-prognosis guides

Map Patient Chart wording to these principles:
- Hospice coverage depends on physician certification.
- Diagnosis alone does not establish terminal prognosis.
- Documentation must support the physician's clinical judgment.
- LCD criteria provide documentation guidance and do not replace
  individualized physician judgment.
- Baseline and follow-up findings should be used where decline over
  time supports prognosis.
- Applicable disease-specific guidance, functional status, ADLs,
  symptoms, comorbidities, complications, hospitalizations, and
  objective findings must remain source-linked.
- The UI must not convert supporting criteria into an automatic
  eligibility verdict.

## Source-Conflict Rule

Apply authorities in this order:
1. Newest California CDPH hospice requirements
2. Current California statutes and directives
3. Current federal CMS hospice requirements
4. Current applicable CMS LCD guidance
5. Accreditation standards
6. Internal and legacy rules

If sources conflict, document the conflict and follow the newest
controlling authority.

---

## Provenance note

The California CDPH section numbers and CMS/LCD identifiers above are
recorded as supplied source citations for this correction list. They
have not been independently re-verified against the referenced PDFs in
this pass; treat them as authoritative input pending that verification,
consistent with this document family's rule of never filling an
unresolved citation with an assumption.

## Implementation boundary

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED HERE
