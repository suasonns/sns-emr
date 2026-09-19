# PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md

## Status

APPROVED WORKFLOW-AUTHORITY BASELINE

Companion to `PATIENT_CHART_WORKFLOW_AUTHORITY.md` (workflow-phase
authority rules), `PATIENT_CHART_CORRECTION_LIST.md` (terminology
corrections), and `PATIENT_CHART_AUTHORITY_MAP.md` (current-state
workspace ownership). Supersedes the earlier draft screen authority
matrix. None of those three documents is reopened by this document.

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED BY THIS DOCUMENT

## Purpose

Define Patient Chart screen purpose, ownership, consumers, producers,
editability, authentication boundaries, and prohibited behavior.

## Global Rule

Patient Chart shall not create duplicate ownership for a record that
already has an authoritative source workspace.

Aggregation does not transfer ownership.

Every status presented as completed, authenticated, approved, certified,
or signed must resolve to a traceable source record.

---

# 1. Patient Story

## Purpose
Read-only patient orientation.

## Owns
Nothing.

## Consumes
- Facesheet
- Intake & Admission
- Diagnosis & LCD
- Physician Certification Record
- RNICA
- Plan of Care
- Physician Orders
- Medications
- Compliance & HOPE
- Care Team
- Recent authorized chart activity

## Produces
Navigation and source links only.

## Editable
No.

## Required Behavior
- Identify every source.
- Display certification only from a traceable certification record.
- Link concerns to authoritative workspaces.
- Show last-updated or source-date information where available.

## Prohibited
- Eligibility determination
- Prognosis generation
- Certification generation
- Final Clinical Narrative ownership
- Risk-score generation
- Silent source-record mutation

---

# 2. Know the Patient

## Purpose
Unified patient profile.

## Owns
Nothing.

## Consumes
- Facesheet
- Intake & Admission
- Insurance
- Diagnosis
- Care Team
- Physician Assignment
- Caregiver and representative information

## Produces
Navigation and source links only.

## Editable
Only through authoritative source workspaces.

## Prohibited
- Duplicate demographics ownership
- Duplicate diagnosis ownership
- Duplicate insurance ownership
- Duplicate care-team ownership
- Terminal-trajectory conclusions

---

# 3. Assess

## Purpose
Entry into RNICA and other authorized assessment workflows.

## Owns
Nothing at the Patient Chart layer.

## Authority Owner
RNICA and each separately authorized discipline-assessment workspace.

## Consumes
Patient context required to open the authoritative assessment.

## Produces
Navigation to the authoritative assessment.

## Prohibited
- Duplicate RNICA fields
- Duplicate Clinical Narrative
- Patient Chart eligibility determination
- Silent rewriting of assessment records

---

# 4. Document Visit

## Purpose
Create, review, authenticate, and retrieve visit documentation.

## Owns
Visit Notes and verified visit-documentation records.

## Consumes
- Patient identity
- Visit context
- Scheduling context, if connected
- Orders
- Plan of Care
- Clinical assessment findings
- Communication context

## Produces
- Visit note
- Authentication event
- Signature event
- Amendment or addendum
- Visit-documentation status

## Required Record Elements
Where applicable:
- Patient identifier
- Visit identifier
- Discipline
- Author identity
- Professional credentials
- Service date and time
- Entry date and time
- Authentication status
- Signature status
- Correction, amendment, and addendum history

## Prohibited
- Silent alteration
- Untraceable correction
- Reattribution of authorship
- Treating review as signature
- Treating schedule status as completed documentation

---

# 5. Manage Treatment

## Purpose
Unified treatment-management workflow.

## Owns
No cross-domain source record.

## Authority Owners
- Medication domain owns medication records.
- Physician Orders domain owns order records.
- DME domain owns DME records.
- Reconciliation workflow owns verified reconciliation records.

## Consumes
- Medications
- Physician Orders
- DME records
- Treatment context
- Pending review and signature states

## Produces
- Draft requests
- Explicit user-initiated workflow actions
- Navigation to source records

## Required Behavior
- Distinguish draft, submitted, reviewed, approved, signed,
  discontinued, and completed states.
- Identify the authenticated actor for approval and signature.
- Preserve order and medication audit history.

## Prohibited
- Nurse-issued physician-order representation
- Automatic physician authorization
- Automatic signature
- Silent medication, order, or DME changes
- AI-generated treatment authority

---

# 6. Plan Care

## Purpose
Develop, review, approve, and preserve the individualized Plan of Care.

## Owns
Plan of Care records and version history.

## Consumes
- Comprehensive assessment
- RNICA findings
- Visit findings
- Patient and representative goals
- Physician input
- IDT input
- Orders and treatment information

## Produces
- Goals
- Interventions
- Frequencies
- Outcomes
- Proposed modifications
- Approved modifications
- Review history
- Approval and signature status

## Required Behavior
- Assessment findings remain source evidence.
- Proposed and approved changes remain distinguishable.
- Required physician approval and signature remain authenticated events.
- All versions remain filed and traceable.
- Review cadence and applicable due dates must be mapped during
  repository discovery.

## Prohibited
- Silent activation of proposed modifications
- Inferred physician approval
- Overwriting prior Plan of Care versions
- Treating RNICA recommendations as active interventions

---

# 7. Coordinate Team

## Purpose
Source-linked interdisciplinary coordination.

## Owns
Only coordination records that repository discovery verifies as native
to this workflow.

## Consumes
- IDG
- Plan of Care
- Physician Orders
- Medications
- Visit Notes
- Communication Log
- CHHA
- Volunteer
- Care Team
- Tasks

## Produces
- Authorized coordination actions
- Source-linked review visibility
- Meeting or follow-up navigation

## Required Behavior
- Identify the source of every item.
- Keep review separate from approval and signature.
- Preserve discipline, author, date, and status.
- Do not attribute one clinician's action to another clinician.

## Prohibited
- Silent source-record mutation
- Physician signature attribution without authenticated signature
- Automatic IDG approval
- Automatic Plan of Care changes
- Unverified "auto-aggregator validated" claims

---

# 8. Ensure Compliance

## Purpose
Present source-linked deficiencies, readiness checks, due items, and
validation results.

## Owns
Compliance presentation and verified compliance-review records only.

## Consumes
- RNICA
- Compliance & HOPE
- Physician Certification Record
- Physician Orders
- Plan of Care
- Visit Notes
- CHHA
- Facesheet
- Intake & Admission
- Diagnosis & LCD
- Documents & Images

## Produces
- Deficiency display
- Documentation-readiness status
- Source-navigation actions
- Verified review events, if repository-supported

## Every Finding Must Identify
- Source workspace
- Source record or field
- Applicable rule
- Severity
- Resolution destination
- Last evaluated timestamp

## Prohibited
- Hospice eligibility determination
- Prognosis determination
- Physician certification
- Source-record correction
- Plan of Care approval
- Order signature
- Final Clinical Narrative ownership
- Unsupported survey-readiness claims

---

# 9. Handle Transitions

## Purpose
Manage episode transitions.

## Owns
Verified transition records for:
- Revocation
- Transfer
- Discharge
- Death documentation
- Bereavement transition

## Consumes
- Patient status
- Plan of Care
- Orders
- Medications
- Visits
- Assessments
- Compliance
- Documents
- Bereavement information

## Produces
- Transition records
- Reconciliation status
- Deficiency status
- Required notices
- Audit events

## Required Behavior
- Reconcile the medical record before representing discharge as
  complete.
- Identify missing or deficient information.
- Preserve source records and transition history.
- Keep discharge, death, and bereavement records distinct.

## Prohibited
- Silent closure with incomplete required documentation
- Overwriting source records
- Combining death and discharge records without verified repository
  authority
- Untraceable status changes

---

# 10. Track & Report

## Purpose
Read-only reporting and operational visibility.

## Owns
Nothing unless repository discovery verifies a dedicated reporting
record.

## Consumes
- Issues & Outcomes
- Incident Logs
- Faxes
- Visit Notes
- Plan of Care
- Compliance
- Transition records
- Other approved reporting sources

## Produces
Reports, analytics, and navigation only.

## Prohibited
- Becoming clinical-record authority
- Editing source records from report output
- Generated clinical conclusions
- Generated eligibility or prognosis
- Untraceable aggregation

---

# Global Authentication and Audit Requirements

Repository discovery must verify support for:
- Role-based authorization
- Unique user identity
- Author identity
- Professional credentials
- Entry date and time
- Service date and time
- Authentication status
- Signature status
- Countersignature or dual-signature details
- Amendments
- Corrections
- Addenda
- Written reason for alteration
- Original-record preservation
- Denied-amendment justification
- Lock and status-change history
- Record retrieval and access
- Backup and disaster-recovery behavior

---

# California and CMS Source Mapping

## California CDPH Mapping

Primary source: `DPH-18-002E-HospiceAgencies_Text.pdf`

| Patient Chart Area | California Mapping |
|---|---|
| Intake & Admission | Section 74860 |
| RNICA and discipline assessments | Section 74864 |
| Plan Care | Section 74868 |
| Plan Care review and updates | Section 74872 |
| Record retrieval and reconciliation | Section 74888 |
| Deficiency analysis | Section 74888 |
| Correction and amendment requests | Section 74888 |
| Authentication, signatures, corrections, addenda | Medical-record documentation requirements |
| Electronic access control, audit, backup, and recovery | Electronic Health Records requirements |

## CMS and LCD Mapping

Primary sources:
- `cms guidelines.pdf`, LCD L34538
- `1.pdf`, LCD L33393
- Attached non-disease-specific and disease-specific terminal-prognosis
  guides

| Patient Chart Area | CMS/LCD Mapping |
|---|---|
| Patient Story | Displays documented facts and traceable certification status only |
| Diagnosis & LCD | Supports documentation review; does not independently certify |
| Functional decline | Uses baseline and follow-up findings when applicable |
| Plan Care | Must remain separate from eligibility support |
| Ensure Compliance | Displays missing support and source-linked deficiencies |
| Recertification | Uses the same prognosis standard and patient-specific supporting documentation |
| Disease-specific evidence | Uses applicable current LCD guidance and attached disease guide |
| Non-listed evidence | May be documented as individualized support for physician judgment |

## Source-Conflict Rule

Apply:
1. Newest California CDPH hospice requirements
2. Current California statutes and directives
3. Current federal CMS hospice requirements
4. Current applicable CMS LCD guidance
5. Accreditation standards
6. Internal and legacy interpretations

Conflicts must be documented rather than silently resolved.

## Provenance note

The California CDPH section numbers and CMS/LCD identifiers above are
recorded as supplied source citations. They have not been independently
re-verified against the referenced PDFs in this pass; treat them as
authoritative input pending that verification, consistent with this
document family's rule of never filling an unresolved citation with an
assumption.

## Implementation boundary

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED HERE

Next: `PATIENT_CHART_CURRENT_STATE_MAPPING.md`,
`PATIENT_CHART_GAP_ANALYSIS.md`, and
`PATIENT_CHART_IMPLEMENTATION_DISCOVERY.md`, per
`PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md`.
