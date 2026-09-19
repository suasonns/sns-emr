# PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md

## Status

FINAL DOCUMENTATION REVIEW COMPLETE

## Overall Decision

APPROVED WITH REQUIRED REPOSITORY DISCOVERY ITEMS

The Patient Chart authority package is suitable for a documentation-only
pull request. Application implementation is not authorized by this
review.

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED

---

# Confirmed Strengths

- Patient Story and Know the Patient remain presentation layers.
- RNICA remains assessment authority.
- Visit Notes remains visit-documentation authority.
- Medications, Physician Orders, DME, Plan of Care, IDG, Communication
  Log, Compliance, and transition records retain separate ownership.
- Supporting evidence is separated from physician certification.
- Proposed Plan of Care modifications are separated from approved
  modifications.
- Authentication, signatures, corrections, amendments, addenda, and
  audit history remain distinct.
- Compliance findings remain source-linked and do not replace source
  records.
- Discharge includes medical-record reconciliation and deficiency
  review.
- The repository-discovery prompt prohibits application, API, schema,
  migration, and production-data changes.

---

# Required Compliance Gaps

These 10 items are required repository-discovery treatments for
`PATIENT_CHART_CURRENT_STATE_MAPPING.md`,
`PATIENT_CHART_GAP_ANALYSIS.md`, and
`PATIENT_CHART_IMPLEMENTATION_DISCOVERY.md`, the next deliverables per
`PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md`. None is resolved by this
review; each is carried forward as a required discovery item.

## 1. California and Medicare Prognosis Standards Must Remain Distinct

The retrieved California hospice framework references an initial
certification attesting to a life expectancy of 12 months or less, while
the Medicare hospice LCD states that Medicare hospice coverage depends
on physician certification of a life expectancy of six months or less
if the terminal illness follows its normal course.

Required repository treatment:
- Do not collapse California licensing certification and Medicare
  benefit certification into one field.
- Map each certification status to its applicable authority, program,
  benefit, certifying practitioner, effective date, signature, and
  narrative.
- Do not display `Eligible` based only on LCD evidence.
- Document any conflict between the California and Medicare standards.
- Apply the appropriate requirement according to the patient, payer,
  program, and controlling workflow.

## 2. Certification Must Resolve to an Authenticated Record

Any displayed physician-certification status must link to:
- Certification record
- Certifying practitioner
- Practitioner role
- Certification date
- Benefit period or episode
- Signature or authentication status
- Supporting narrative
- Amendment or addendum history

If the repository cannot resolve these elements, display:
`Physician Certification Status Unavailable`

Do not infer certification from diagnosis, LCD findings, enrollment, or
admission status.

## 3. Plan of Care Approval Must Be Separated From Development

The California framework states that the comprehensive assessment forms
the basis for the individualized Plan of Care, that the interdisciplinary
team develops the written plan, and that Plan of Care updates occur in
collaboration with the attending physician or applicable medical
director.

Repository discovery must distinguish:
- Draft
- Proposed
- Under review
- Approved
- Signed
- Active
- Superseded
- Amended

A proposed goal, intervention, frequency, or modification must not
appear active before required approval is recorded.

## 4. Review, Approval, and Signature Must Remain Separate

IDG review, facilitator documentation, physician review, physician
approval, and physician signature must be separate events.

Required fields include:
- Actor
- Role
- Date and time
- Action
- Source record
- Authentication status
- Signature status

One user's review must not be attributed as another user's approval or
signature.

## 5. Medical-Record Integrity Requires Explicit Discovery

The California framework requires organized and accessible patient
records, authenticated documentation, correction and amendment
procedures, written justification for denied amendment requests, unique
user identification, and traceable addenda.

Repository discovery must verify:
- Original-entry preservation
- Correction reason
- Discovery date
- Correction date
- Correcting user
- Authentication
- Amendment request status
- Denial justification
- Addendum separation
- Audit event
- Wrong-patient and duplicate-record correction handling

## 6. Discharge Must Include Record Reconciliation

The California framework defines reconciliation as ensuring that a
complete and accurate patient record is generated upon discharge, and
defines deficiency analysis as detecting absent or missing information.

The transition workflow must distinguish:
- Clinical discharge status
- Administrative discharge status
- Record-reconciliation status
- Missing-documentation status
- Required notice status
- Bereavement transition status

Do not label the episode administratively complete until the
repository's required reconciliation conditions are satisfied.

## 7. LCD Evidence Must Not Become Automatic Eligibility

The Medicare LCD states that hospice coverage depends on physician
certification and that documentation must support the patient-specific
prognosis. It also recognizes that some patients may not meet listed
guidelines but may still qualify when other clinical factors support the
prognosis.

Required terminology:
- `LCD Supporting Evidence Present`
- `Supporting Evidence Identified`
- `Documentation Review Complete`
- `Physician Certification Required`

Prohibited automatic conclusions:
- `Eligible`
- `Eligibility Confirmed`
- `LCD Passed`
- `Satisfies LCD`
- `5 of 5 Criteria Met, Eligible`

## 8. Baseline and Follow-Up Evidence Must Remain Traceable

The non-disease-specific guidance states that decline assessment should
include baseline and follow-up determinations where appropriate, and
that diagnosis alone may not support terminal prognosis.

Repository discovery must identify source and date for:
- PPS
- KPS
- FAST
- ADL dependence
- Weight and nutritional changes
- Symptoms
- Complications
- Hospitalizations
- Objective measurements
- Disease-specific findings
- Contradictory or stabilizing findings

## 9. Unsupported Readiness Capabilities Must Not Be Presented as Operational

Use: `Documentation Readiness`
unless repository discovery confirms a dedicated and separately
authorized survey-readiness capability.

Do not infer:
- Billing readiness
- Survey readiness
- Schedule reconciliation
- Chart-wide AI
- Automatic IDG aggregation

## 10. Access Control, Backup, and Downtime Require Mapping

The California framework includes authenticated access, unique user
identification, backup requirements, disaster-recovery procedures, and
continued manual documentation during an EHR outage.

Repository discovery must document:
- Role-based access control
- Unique user identity
- Shared-credential prevention
- Backup behavior
- Recovery behavior
- Downtime documentation process
- Restoration and reconciliation of downtime records
- Access to records from multiple providers

---

# Relationship to prior Patient Chart documents

This review does not reopen `PATIENT_CHART_WORKFLOW_AUTHORITY.md`,
`PATIENT_CHART_CORRECTION_LIST.md`,
`PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md`, or
`PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md`. It approves all four and adds
10 required repository-discovery items that those documents' successors
(`PATIENT_CHART_CURRENT_STATE_MAPPING.md`,
`PATIENT_CHART_GAP_ANALYSIS.md`,
`PATIENT_CHART_IMPLEMENTATION_DISCOVERY.md`) must resolve — specifically:
distinguishing California vs. Medicare certification standards (item 1,
new — not previously called out as two distinct standards in this doc
family); linking certification display to an authenticated record with
a defined fallback (item 2, refines the existing Patient Story
certification-wording rule); Plan of Care status-model granularity
(item 3, refines the existing Plan Care approval-separation rule);
review/approval/signature field-level requirements (item 4, refines the
existing Coordinate Team review-vs-signature rule); medical-record
integrity discovery fields (item 5, refines the existing global
correction/amendment rule); discharge status-model granularity (item 6,
refines the existing Handle Transitions reconciliation rule); LCD
terminology (item 7, restates the existing rule, unchanged); baseline/
follow-up evidence traceability (item 8, new); readiness-capability
naming (item 9, restates the existing Ensure Compliance rule,
unchanged); and access-control/backup/downtime discovery (item 10,
refines the existing global access-control-and-audit rule).

---

# Final Compliance Decision

- Patient Chart workflow authority: **APPROVED**
- Patient Chart screen authority matrix: **APPROVED**
- Patient Chart correction list: **APPROVED**
- Repository discovery prompt: **APPROVED**
- Application implementation: **NOT AUTHORIZED**

Next authorized activity: **DOCUMENTATION-ONLY REPOSITORY DISCOVERY**
(`PATIENT_CHART_CURRENT_STATE_MAPPING.md`,
`PATIENT_CHART_GAP_ANALYSIS.md`,
`PATIENT_CHART_IMPLEMENTATION_DISCOVERY.md`), incorporating the 10
required compliance-gap items above.

## Provenance note

The California and Medicare/LCD standards, section references, and
citation markers quoted above are recorded as supplied source input for
this review. They have not been independently re-verified against the
underlying regulatory PDFs in this pass; treat them as authoritative
input pending that verification, consistent with this document family's
rule of never filling an unresolved citation with an assumption.

## Implementation boundary

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED HERE
