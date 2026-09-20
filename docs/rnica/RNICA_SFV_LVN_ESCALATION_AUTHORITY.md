# RNICA Final SFV and LVN Escalation Authority Matrix

**STATUS:** DISCOVERY / AUTHORITY REFERENCE ONLY. NOT IMPLEMENTATION AUTHORIZATION.
**CODE:** BLOCKED
**SCHEMA:** BLOCKED
**MIGRATIONS:** BLOCKED
**AUTOMATIC VISIT CLASSIFICATION:** BLOCKED

This document is the authoritative, consolidated policy boundary for the
official CMS HOPE Symptom Follow-up Visit (SFV) trigger, who may conduct the
SFV symptom-impact item, SNS's routine-LVN-visit escalation workflow, and
the related California significant-change/Plan-of-Care notification
requirement. It supersedes and refines the SFV-related rows previously
added piecemeal to
[`RNICA_AUTHORITY_MATRIX.md`](./RNICA_AUTHORITY_MATRIX.md) and
[`RNICA_VISIT_CLASSIFICATION_DECISION_TABLE.md`](./RNICA_VISIT_CLASSIFICATION_DECISION_TABLE.md)
§6.1; those documents should be read together with this one.

## Policy Boundary

This policy distinguishes:

1. The official HOPE SFV trigger.
2. Who may conduct the SFV symptom-impact item.
3. SNS escalation from a routine LVN visit.
4. California significant-change notification.
5. Application behaviors that remain prohibited.

Documentation and discovery are authorized.

Application implementation remains `NOT_AUTHORIZED`.

## Citation Audit

### Source 1

**Title:** CMS Hospice Quality Reporting Program Quality Measure
Specifications User's Manual, Draft HOPE-Based Timely Reassessment
Process Measures

**Exact section:** Section 1, Measure Description

**Explicitly supports:**

- The Symptom Impact item J2051 may trigger an SFV.
- A moderate or severe pain or non-pain symptom-impact response triggers
  the expected SFV.
- The SFV is expected within two calendar days.
- The measurement window begins with the J2050B screening date.
- Admission, HUV1, and HUV2 are possible triggering timepoints.
- Up to three SFVs may be required.
- Continued moderate or severe impact at an SFV does not trigger another
  HOPE SFV for the measure.
- Continued clinical follow-up remains expected based on patient need.

### Source 2

**Title:** CMS HOPE v1.01 to HOPE v1.02 Guidance Manual and Item Set
Change Table

**Exact section:** Guidance Manual, Section J, item J2053,
Item-Specific Instructions and Coding Tips

**Explicitly supports:**

- J2053 is the SFV Symptom Impact item.
- J2053 follows symptoms identified in a HOPE Admission or HUV.
- J2053 may be conducted by an RN or LPN/LVN.
- The clinician may use patient/caregiver interview, observation, and
  clinical judgment.

### Source 3

**Title:** CMS HOPE National Implementation Training, Part 4, Section J:
Health Conditions

**Exact section:** Section J item overview

**Explicitly identifies:**

- J2050: Symptom Impact Screening
- J2051: Symptom Impact
- J2052: Symptom Follow-up Visit
- J2053: SFV Symptom Impact

### Source 4

**Title:** CMS HOPE Implementation Frequently Asked Questions

**Exact section:** Symptom Follow-up Visits section

The retrieved CMS result confirms that the FAQ contains a dedicated SFV
section, but the available excerpt does not expose enough of that
section to support additional detailed rules for late or invalid SFVs.
Those behaviors must therefore remain `PENDING_SOURCE_VALIDATION` unless
confirmed against the full FAQ, current HOPE data specifications, or
iQIES validation edits.

### Source 5

**Title:** CMS HOPE Technical Information

**Explicitly supports:**

- HOPE records are submitted through iQIES.
- HOPE data specifications include fatal and warning edits.
- The HOPE Validation Utility Tool produces validation results.
- Current technical edits and errata must be considered when validating
  submissions.

### California Source

**Title:** DPH-18-002E-HospiceAgencies_Text.pdf

**Exact sections:** §§74868(g) through 74868(i)

**Explicitly supports:**

- A proposed Plan-of-Care modification requires written approval before
  implementation.
- A significant change that may require Plan-of-Care modification must
  be reported to the attending physician, Medical Director, or designee
  as soon as possible within 24 hours.
- Agency policy must identify reportable changes, recipients, methods,
  and notification timelines.

## Final Authority Matrix

| Rule | Authority Label | Validation Status | Repository Verified | Source |
|---|---|---|---|---|
| HOPE SFV is symptom-triggered, not time-triggered alone | `OFFICIAL_HOPE_REQUIRED` | `VALIDATED` | `NO` | CMS HOPE Guidance Manual v1.02; CMS HOPE Measures Manual |
| Official SFV trigger is a moderate or severe J2051 symptom-impact response at HOPE Admission, HUV1, or HUV2 | `OFFICIAL_HOPE_REQUIRED` | `VALIDATED` | `NO` | CMS HOPE Measures Manual |
| SFV is expected within two calendar days after the triggering moderate or severe J2051 assessment | `OFFICIAL_HOPE_REQUIRED` | `VALIDATED` | `NO` | CMS HOPE Measures Manual |
| Up to three SFVs may be required, based on qualifying findings at HOPE Admission, HUV1, and HUV2 | `OFFICIAL_HOPE_REQUIRED` | `VALIDATED` | `NO` | CMS HOPE Measures Manual |
| Continued moderate or severe impact found during an SFV does not require another HOPE SFV for the measure | `OFFICIAL_HOPE_REQUIRED` | `VALIDATED` | `NO` | CMS HOPE Measures Manual |
| Continued clinical symptom follow-up remains expected according to patient need | `OFFICIAL_HOPE_REQUIRED` | `VALIDATED` | `NO` | CMS HOPE Measures Manual |
| J2053 SFV symptom-impact item may be conducted by an RN or LPN/LVN | `OFFICIAL_HOPE_REQUIRED` | `VALIDATED` | `NO` | CMS HOPE v1.01 to v1.02 Change Table |
| SFV may occur during the first 30 days because its possible source timepoints include HOPE Admission, HUV1, and HUV2 | `OFFICIAL_HOPE_REQUIRED` | `VALIDATED_WITH_CONTEXT` | `NO` | CMS HOPE Guidance Manual and HOPE Measures Manual |
| Being within the first 30 days does not independently trigger an SFV | `OFFICIAL_HOPE_REQUIRED` | `VALIDATED` | `NO` | CMS HOPE Measures Manual |
| A routine LVN visit is not itself a HOPE Admission, HUV1, or HUV2 trigger record | `PROHIBITED_ASSUMPTION` | `VALIDATED` | `NO` | CMS HOPE trigger model |
| Severe symptoms found during a routine LVN visit automatically create an SFV | `PROHIBITED_ASSUMPTION` | `VALIDATED` | `NO` | Not supported by CMS HOPE trigger requirements |
| Severe symptoms found during a routine LVN visit automatically complete an SFV | `PROHIBITED_ASSUMPTION` | `VALIDATED` | `NO` | Not supported by CMS HOPE requirements |
| RN review is requested when a routine LVN visit identifies a severe, significant, or worsening symptom | `SNS_INTERNAL_WORKFLOW` | `AGENCY_APPROVAL_REQUIRED` | `NO` | SNS escalation policy, informed by California significant-change requirements |
| LVN finding must preserve symptom, severity, service time, author, interventions, notifications, and source note | `SNS_INTERNAL_WORKFLOW` | `DOCUMENTED` | `NO` | SNS audit policy |
| RN reviewer determines whether the finding is connected to a valid HOPE Admission or HUV trigger | `SNS_INTERNAL_WORKFLOW` | `DOCUMENTED` | `NO` | SNS HOPE validation workflow |
| RN reviewer determines whether an official SFV is due | `SNS_INTERNAL_WORKFLOW` | `DOCUMENTED` | `NO` | SNS workflow bounded by CMS HOPE requirements |
| RN reviewer may determine that an additional clinical RN assessment is required even when an SFV is not due | `SNS_INTERNAL_WORKFLOW` | `DOCUMENTED` | `NO` | SNS clinical escalation policy |
| Significant change that may require Plan-of-Care modification must be reported according to California notification requirements | `CALIFORNIA_REQUIRED` | `VALIDATED` | `NO` | CDPH DPH-18-002E §74868(h)-(i) |
| Plan-of-Care modifications require written approval from the authorized physician, Medical Director, or designee before implementation | `CALIFORNIA_REQUIRED` | `VALIDATED` | `NO` | CDPH DPH-18-002E §74868(g) |
| Discipline must come from authenticated identity and verified credential | `SNS_INTERNAL_WORKFLOW` | `DOCUMENTED` | `NO` | SNS authority policy |
| SFV status may not be marked complete from schedule status alone | `PROHIBITED` | `DOCUMENTED` | `NO` | SNS evidence-integrity policy |
| SFV completion requires a valid trigger link, clinician identity, service date, required item evidence, and completion status | `SNS_INTERNAL_WORKFLOW` bounded by `OFFICIAL_HOPE_REQUIRED` | `PARTIALLY_VALIDATED` | `NO` | CMS HOPE requirements plus SNS audit policy |
| Post-finalization SFV changes require correction, modification, inactivation, amendment, or authorized re-finalization | `OFFICIAL_HOPE_REQUIRED` + `SNS_INTERNAL_WORKFLOW` | `PENDING_REPOSITORY_VALIDATION` | `NO` | CMS record-control requirements plus SNS audit policy |
| The measure window starts on the J2050B symptom-impact screening date | `OFFICIAL_HOPE_REQUIRED` | `VALIDATED` | `NO` | CMS HOPE Measures Manual, Section 1 |
| A late SFV may be backdated to appear timely | `PROHIBITED` | `SNS_AUDIT_CONTROL` | `NO` | SNS documentation-integrity rule |
| A late SFV must retain the actual service date and actual entry date | `SNS_INTERNAL_WORKFLOW` | `AGENCY_APPROVAL_REQUIRED` | `NO` | SNS audit policy |
| A late SFV still satisfies the HQRP timely-follow-up measure | `PROHIBITED_ASSUMPTION` | `VALIDATED` | `NO` | CMS defines the measure window as two calendar days |
| Exact CMS submission treatment of a late SFV | `PENDING_SOURCE_VALIDATION` | `UNRESOLVED` | `NO` | Must be verified against the full CMS FAQ, current data specifications, and applicable iQIES edits |
| Exact fatal or warning edit for an invalid SFV sequence | `PENDING_SOURCE_VALIDATION` | `UNRESOLVED` | `NO` | CMS HOPE Technical Information confirms fatal/warning edits exist but the retrieved material does not specify the SFV edit numbers |
| Invalid SFV may be silently converted into another visit type | `PROHIBITED` | `SNS_AUDIT_CONTROL` | `NO` | SNS traceability rule |

## SFV Policy

### Official Trigger

An SFV is required when the HOPE Symptom Impact item J2051 is assessed as
moderate or severe at one of these official source timepoints:

- HOPE Admission
- HUV1
- HUV2

The SFV is expected within two calendar days after the triggering
symptom-impact assessment.

Time in service alone does not trigger an SFV.

### Eligible SFV Clinician

The SFV symptom-impact item J2053 may be conducted by:

- RN
- LPN/LVN

The clinician must be authenticated, actively credentialed, assigned or
authorized for the visit, and acting within applicable scope and agency
policy.

### Routine LVN Visit Outside an Official Trigger

If a routine LVN visit identifies a severe, significant, or worsening
symptom:

1. Preserve the LVN clinical finding.
2. Display: `RN Assessment Review Required`.
3. Create an RN review task or compliance-review item.
4. Record the symptom, severity, intervention, service date/time, LVN
   identity, and notifications.
5. Determine whether the finding is linked to a valid HOPE Admission,
   HUV1, or HUV2 record.
6. Require RN review to determine:
   - Whether an official SFV trigger exists.
   - Whether an SFV is due.
   - Whether an additional RN clinical assessment is required.
   - Whether physician or Medical Director notification is required.
   - Whether Plan-of-Care review is required.

Do not automatically:

- Create an SFV.
- Classify the LVN visit as an SFV.
- Mark an SFV complete.
- Create a HOPE trigger retroactively.
- Backdate a HOPE record.
- Modify the Plan of Care.
- Treat task completion as clinical completion.

### Escalation Actions

Offer only authorized actions:

- Request RN Visit
- Request RN Assessment Review
- Document Existing RN Review
- Record Physician or Medical Director Notification
- Link to Existing HOPE Trigger
- Mark as Clinical Escalation Without SFV

### Audit Evidence

Preserve:

- Patient and episode ID
- Visit and assessment ID
- Benefit period
- LVN user ID and credential
- Assigned discipline
- Service date/time
- Entry date/time
- Symptom and severity
- Intervention performed
- HOPE source record, if any
- J2051 trigger value, if any
- RN reviewer and review timestamp
- SFV applicability decision
- Decision rationale
- Physician or Medical Director notification
- Plan-of-Care review status
- Final classification
- Correction or amendment history

## Given/When/Then Test Scenarios

### Scenario 1: Official HOPE Admission Trigger

**Given** a HOPE Admission contains a moderate or severe J2051
symptom-impact response
**When** the HOPE Admission is validated
**Then** the system must create an SFV due-status tied to that HOPE
Admission
**And** calculate the two-calendar-day follow-up window
**And** preserve the triggering item and source record
**And** not require a separate RN review merely because an LPN/LVN is
authorized to conduct J2053.

### Scenario 2: Official HUV1 Trigger

**Given** a valid HUV1 contains a moderate or severe J2051 response
**When** HUV1 is completed
**Then** the system must identify the SFV requirement
**And** link the SFV to HUV1
**And** preserve the two-calendar-day due window
**And** prevent classification based on visit date alone.

### Scenario 3: Official HUV2 Trigger

**Given** a valid HUV2 contains a moderate or severe J2051 response
**When** HUV2 is completed
**Then** the system must identify the SFV requirement
**And** link the SFV to HUV2
**And** preserve the two-calendar-day due window.

### Scenario 4: LVN Conducts Official SFV

**Given** a valid HOPE Admission or HUV triggered an SFV
**And** an authenticated, credentialed LPN/LVN is authorized to conduct
the SFV symptom-impact item
**When** the LPN/LVN documents J2053 within the required window
**Then** the system may record the LPN/LVN as the SFV clinician
**And** preserve the source trigger, service date, findings, and
completion evidence
**And** must not require an RN solely because the clinician is an
LPN/LVN.

### Scenario 5: Routine LVN Visit Finds Severe Symptom Without HOPE Trigger

**Given** a routine LVN visit is not a HOPE Admission, HUV1, or HUV2
**And** the LVN documents a severe or significant symptom
**When** the visit is saved
**Then** the system must display `RN Assessment Review Required`
**And** create an RN review or compliance item
**And** preserve the LVN finding and interventions
**And** must not create or complete an SFV automatically.

### Scenario 6: RN Confirms No Official SFV Trigger

**Given** an LVN severe-symptom escalation exists
**And** no valid moderate or severe J2051 response exists in HOPE
Admission, HUV1, or HUV2
**When** the RN completes the review
**Then** the RN may classify the event as
`CLINICAL_ESCALATION_WITHOUT_SFV`
**And** document the rationale and follow-up plan
**And** the system must not create a retroactive HOPE trigger.

### Scenario 7: RN Finds Existing HOPE Trigger

**Given** an LVN severe-symptom escalation exists
**And** the RN identifies a valid moderate or severe J2051 response in
an existing HOPE Admission or HUV record
**When** the RN validates the source record
**Then** the system must link the escalation to the existing HOPE
trigger
**And** evaluate the SFV due date and completion status
**And** preserve the RN decision and source link.

### Scenario 8: RN Determines Additional Clinical Assessment Is Needed

**Given** an LVN reports a severe or worsening symptom
**When** the RN reviews the clinical finding
**And** the RN determines further assessment is required
**Then** the system must allow an RN visit or RN assessment to be
requested
**And** preserve the reason and urgency
**And** track required physician or Medical Director notification
**And** keep that RN assessment separate from official SFV
classification unless a valid HOPE trigger exists.

### Scenario 9: Attempted Automatic SFV Completion

**Given** an LVN visit contains a severe symptom
**But** no valid HOPE Admission or HUV trigger has been linked
**When** a user attempts to mark SFV complete
**Then** the system must block completion
**And** explain that a valid triggering HOPE record is missing
**And** preserve the attempted action in the audit trail.

### Scenario 10: Significant Change May Require Plan-of-Care Modification

**Given** an LVN or other personnel member identifies a significant
change that may require Plan-of-Care modification
**When** the finding is documented
**Then** the system must support notification to the attending
physician, Medical Director, or designee according to the required
timeline
**And** create a Plan-of-Care review item
**And** prevent an unapproved Plan-of-Care modification from becoming
active
**And** preserve notifications, approvals, dates, and source
documentation.

## Late and Invalid SFV Rules

### Late SFV

If the SFV occurs after the two-calendar-day measure window:

- Preserve the actual J2050B screening date.
- Preserve the actual SFV service date.
- Preserve the actual entry and signature dates.
- Mark the internal timeliness result as `LATE`.
- Do not backdate the visit.
- Do not represent the record as satisfying the two-day measure.
- Continue clinically appropriate symptom follow-up.
- Route the record for compliance review.

The statement that the SFV does not satisfy the two-day measure follows
directly from the CMS-defined measurement window. The exact CMS
submission disposition of the late record remains
`PENDING_SOURCE_VALIDATION` pending validation against current CMS
submission specifications.

### Invalid SFV

Treat an SFV as internally invalid or blocked when any required
discovery control is missing, including:

- No linked HOPE Admission, HUV1, or HUV2 source.
- No triggering moderate or severe J2051 response.
- Source record belongs to another patient or episode.
- SFV date precedes the triggering assessment.
- Clinician identity or credential cannot be validated.
- Duplicate SFV exists for the same source trigger.
- Required J2052 or J2053 evidence is absent.
- Service date or source date is missing.
- Record sequence conflicts with the linked HOPE record.

These are proposed SNS validation controls. The exact corresponding
iQIES fatal or warning edits must be mapped from current CMS data
specifications before implementation.

## Additional Given/When/Then Edge-Case Scenarios

### Scenario 11: Trigger Record Later Corrected

**Given** an SFV was linked to a moderate or severe J2051 response
**And** the source HOPE record is subsequently corrected or modified
**When** the correction changes the trigger condition
**Then** the system must mark SFV applicability for revalidation
**And** preserve both source versions
**And** must not silently delete the SFV.

### Scenario 12: Trigger Record Inactivated

**Given** an SFV is linked to a HOPE record
**When** the source record is inactivated
**Then** the system must flag the SFV linkage as invalid pending review
**And** preserve the historical relationship
**And** prevent an unsupported final submission state.

### Scenario 13: Late Data Entry but Timely Service

**Given** the SFV service occurred within the two-calendar-day window
**But** documentation was entered later
**When** the record is reviewed
**Then** the system must preserve service date and entry date
separately
**And** must not infer CMS submission validity from service timing
alone
**And** must evaluate current CMS submission rules separately.

### Scenario 14: Timely Visit but Rejected iQIES Record

**Given** the SFV service occurred within the measure window
**And** the submitted record is rejected by iQIES
**When** the Final Validation Report is received
**Then** the system must preserve the rejection details
**And** display submission status separately from clinical timeliness
**And** require correction and resubmission according to the applicable
CMS edit.

### Scenario 15: Patient Discharged Before Expected SFV

**Given** a qualifying trigger exists
**And** the patient is discharged or dies before the planned SFV
**When** the episode closes
**Then** the system must preserve the trigger, discharge event, and
noncompletion reason
**And** must not fabricate an SFV completion
**And** must evaluate the CMS exclusion or measure treatment against
the current HOPE measure specifications before assigning a final
compliance outcome.

## Source Registry

- CMS HOPE Guidance Manual v1.02, Chapter 1 and Section J:
  https://www.cms.gov/files/document/hope-guidance-manual-v1-02.pdf
- CMS HQRP Quality Measure Specifications, HOPE Timely Follow-up
  Measures (HQRP QM User Manual Chapter: HOPE Measures, Section 1):
  https://www.cms.gov/files/document/hqrp-qm-user-manual-chapter-hope-measures-508c.pdf
- CMS HOPE v1.01 to v1.02 Guidance Manual and Item Set Change Table,
  J2053:
  https://www.cms.gov/files/document/hope-v1-01-1-02-guidance-manual-item-set-change-table.pdf
- CMS HOPE National Implementation Training, Part 4, Section J:
  https://www.cms.gov/files/document/part-4section-j-health-conditions-presentation.pdf
- CMS HOPE Implementation FAQs (Symptom Follow-up Visits section):
  https://www.cms.gov/files/document/hope-implementation-faqs.pdf
- CMS HOPE Technical Information:
  https://www.cms.gov/medicare/quality/hospice-quality-reporting-program/hope-technical-information
- California CDPH DPH-18-002E, §§74864, 74868, and 74872:
  https://www.cdph.ca.gov/Programs/OLS/Pages/DPH-18-002E.aspx

## SFV Unresolved Rules Traceability Table

**Status:** DISCOVERY ONLY
**Implementation Authorization:** `NOT_AUTHORIZED`

This table assigns a stable Trace ID to every SFV rule that is not yet
fully validated from a published CMS source, plus the SNS-only rules
that require agency policy approval rather than CMS validation. Each
Trace ID must be referenced by any future implementation ticket so the
underlying source gap or approval gap is not silently assumed away.

| Trace ID | Rule / Question | Current Status | Known Source | Missing Validation | Implementation Risk | Required Artifact |
|-----------|-----------|-----------|-----------|-----------|-----------|-----------|
| SFV-001 | Exact exclusion rules for patient death before SFV | PENDING_SOURCE_VALIDATION | CMS HOPE Measures Manual | Whether death creates exclusion, exception, or failure condition | Incorrect quality measure calculation | CMS HOPE Measures Manual exclusion section |
| SFV-002 | Exact exclusion rules for discharge before SFV | PENDING_SOURCE_VALIDATION | CMS HOPE Measures Manual | Treatment of discharge occurring before follow-up window closes | Incorrect quality measure calculation | CMS Measure Specifications |
| SFV-003 | Patient refusal of SFV | PENDING_SOURCE_VALIDATION | CMS HOPE FAQs | Whether refusal creates exception, exclusion, or failed measure | Incorrect compliance reporting | FAQ SFV section |
| SFV-004 | Patient unavailable during follow-up window | PENDING_SOURCE_VALIDATION | CMS HOPE FAQs | Measure treatment and documentation requirements | Survey and audit risk | FAQ SFV section |
| SFV-005 | Exact late-SFV submission treatment | PENDING_SOURCE_VALIDATION | CMS Measures Manual | CMS handling after two-calendar-day window | Incorrect internal status logic | CMS Measures Manual |
| SFV-006 | Exact late-SFV iQIES status | PENDING_SOURCE_VALIDATION | CMS Technical Information | Fatal edit, warning edit, accepted, or informational status | Invalid submission workflow | HOPE Data Specifications |
| SFV-007 | Duplicate SFV edit logic | PENDING_SOURCE_VALIDATION | CMS Technical Information | Exact duplicate detection rules | Duplicate records | HOPE Data Specifications |
| SFV-008 | SFV linked to corrected source trigger | PENDING_SOURCE_VALIDATION | CMS Technical Information | Correct CMS workflow after source modification | Broken historical linkage | Data Specs & Errata |
| SFV-009 | SFV linked to inactivated source trigger | PENDING_SOURCE_VALIDATION | CMS Technical Information | Required CMS resubmission sequence | Invalid record chain | Data Specs & Errata |
| SFV-010 | Multiple qualifying symptoms from same trigger | PENDING_SOURCE_VALIDATION | CMS Measures Manual | Single SFV vs multiple SFVs | Over-generation of visits | CMS Measures Manual |
| SFV-011 | Multiple severe symptoms during SFV | PARTIALLY_VALIDATED | CMS Measures Manual | Additional recording behavior | Ambiguous documentation | Guidance Manual Section J |
| SFV-012 | Same-day trigger and SFV | PENDING_SOURCE_VALIDATION | CMS Measures Manual | Whether same-day counts as timely | Incorrect measure scoring | CMS Measures Manual |
| SFV-013 | Missing J2053 after valid trigger | PENDING_SOURCE_VALIDATION | CMS Data Specifications | Exact CMS validation edit | Submission failure | Data Specifications |
| SFV-014 | Missing J2052 after valid trigger | PENDING_SOURCE_VALIDATION | CMS Data Specifications | Exact CMS validation edit | Submission failure | Data Specifications |
| SFV-015 | Trigger found after original visit finalized | SNS_WORKFLOW_PENDING | SNS repository review | Revalidation workflow | Audit inconsistency | Repository Rule Mapping |
| SFV-016 | Retrospective trigger discovery | SNS_WORKFLOW_PENDING | SNS workflow concept | Whether prior visit may be linked retroactively | Audit inconsistency | SNS Audit Policy |
| SFV-017 | LVN severe symptom without official trigger | SNS_WORKFLOW_PENDING | SNS escalation proposal | RN review workflow approval | Clinical escalation gap | SNS Policy |
| SFV-018 | RN review SLA after LVN escalation | SNS_WORKFLOW_PENDING | Not defined | Escalation timing requirement | Delayed symptom review | SNS Policy |
| SFV-019 | Compliance status when trigger exists but RN review is incomplete | SNS_WORKFLOW_PENDING | Not defined | Workflow ownership | Open compliance task ambiguity | SNS Policy |
| SFV-020 | Exact iQIES edit numbers impacting SFV submissions | PENDING_SOURCE_VALIDATION | CMS Technical Information | Fatal and warning edit catalog | Unsupported implementation | Current Data Spec Package |

### Discovery Completion Criteria

The SFV design cannot be considered source-complete until:

- [ ] CMS FAQ SFV section fully reviewed
- [ ] Full HOPE Guidance Manual v1.02 Section J reviewed
- [ ] Current HOPE Data Specifications reviewed
- [ ] Current HOPE Errata reviewed
- [ ] iQIES fatal edits mapped
- [ ] iQIES warning edits mapped
- [ ] Patient death/discharge exclusions validated
- [ ] Refusal and unavailable-patient handling validated
- [ ] Duplicate record behavior validated
- [ ] Modify/inactivate workflows validated
- [ ] Repository source-field mapping completed
- [ ] SNS LVN→RN escalation policy approved

### Traceability Final Status

| Area | Status |
|--------|--------|
| CMS SFV Core Requirements | VALIDATED |
| CMS SFV Edge Cases | PENDING_SOURCE_VALIDATION |
| iQIES Edit Mapping | PENDING_SOURCE_VALIDATION |
| Repository Mapping | INCOMPLETE |
| SNS Escalation Policy | PENDING_APPROVAL |
| Production Implementation | NOT_AUTHORIZED |

## Source-Validation Checklist for Unresolved SFV Rules

Complete this checklist before implementing any SFV behavior derived
from this document. Every item is discovery-only; checking an item off
does not itself authorize implementation.

### CMS Guidance Manual

- [ ] Confirm the current controlling HOPE Guidance Manual version.
- [ ] Record the effective date.
- [ ] Verify J2050 instructions.
- [ ] Verify J2051 response values that trigger SFV.
- [ ] Verify J2052 completion and date rules.
- [ ] Verify J2053 completion rules.
- [ ] Verify Admission-triggered SFV requirements.
- [ ] Verify HUV1-triggered SFV requirements.
- [ ] Verify HUV2-triggered SFV requirements.
- [ ] Verify exclusions and applicability rules.

### CMS Measure Specifications

- [ ] Confirm the two-calendar-day measure calculation.
- [ ] Confirm how the J2050B screening date anchors the window.
- [ ] Confirm treatment of same-day SFV.
- [ ] Confirm treatment of an SFV completed after the two-day window.
- [ ] Confirm applicable numerator exclusions.
- [ ] Confirm patient discharge or death treatment.
- [ ] Confirm treatment of continued moderate or severe impact at SFV.
- [ ] Confirm whether up to three SFVs may affect the measure
      independently.

### CMS Implementation FAQs

- [ ] Review every question in the SFV section.
- [ ] Extract any guidance for a missed SFV.
- [ ] Extract any guidance for a late SFV.
- [ ] Extract any guidance for patient refusal.
- [ ] Extract any guidance for patient unavailability.
- [ ] Extract any guidance for discharge or death before follow-up.
- [ ] Extract any guidance for multiple symptoms.
- [ ] Extract any guidance for multiple SFVs.
- [ ] Record the FAQ version and publication date.

### CMS Data Specifications and iQIES

- [ ] Identify the current final HOPE data-specification version.
- [ ] Identify the current errata version.
- [ ] Map every SFV-related fatal edit.
- [ ] Map every SFV-related warning edit.
- [ ] Map duplicate-record edits.
- [ ] Map date-sequence edits.
- [ ] Map missing-trigger edits.
- [ ] Map invalid patient or episode linkage edits.
- [ ] Map missing J2052 edits.
- [ ] Map missing J2053 edits.
- [ ] Verify modify-record behavior.
- [ ] Verify inactivate-record behavior.
- [ ] Verify correction and resubmission behavior.
- [ ] Verify Final Validation Report evidence.
- [ ] Verify accepted, rejected, warning, and fatal statuses.

### Repository Validation

- [ ] Identify the authoritative HOPE source-record table.
- [ ] Identify the J2050B storage field.
- [ ] Identify the J2051 storage fields and values.
- [ ] Identify J2052 storage.
- [ ] Identify J2053 storage.
- [ ] Identify patient and episode linkage.
- [ ] Identify service-date source.
- [ ] Identify entry and signature timestamps.
- [ ] Identify clinician identity and discipline source.
- [ ] Identify HOPE record versioning.
- [ ] Identify correction and inactivation support.
- [ ] Identify iQIES submission and validation statuses.
- [ ] Identify duplicate-control behavior.
- [ ] Identify missing or conflicting source fields.
- [ ] Mark the date-source mapping `COMPLETE` only after all sources
      are verified.

### Agency Policy Validation

- [ ] Approve the routine LVN severe-symptom escalation rule.
- [ ] Define which findings require RN review.
- [ ] Define RN-review priority.
- [ ] Define the responsible RN.
- [ ] Define notification recipients.
- [ ] Define Plan-of-Care review triggers.
- [ ] Define completion evidence.
- [ ] Define compliance escalation for incomplete RN review.
- [ ] Define late-SFV review ownership.
- [ ] Define amendment and correction approval roles.

## Final Authority Audit

| Statement | Audit Result |
|---|---|
| SFV is triggered by moderate or severe J2051 findings at HOPE Admission/HUV | `OFFICIAL_HOPE_REQUIRED: VALIDATED` |
| SFV is expected within two calendar days | `OFFICIAL_HOPE_REQUIRED: VALIDATED` |
| J2053 may be conducted by RN or LPN/LVN | `OFFICIAL_HOPE_REQUIRED: VALIDATED` |
| Every LVN severe-symptom visit automatically triggers SFV | `PROHIBITED_ASSUMPTION` |
| Routine LVN severe symptoms should generate RN review | `SNS_INTERNAL_WORKFLOW` |
| RN review may lead to clinical RN assessment without an SFV | `SNS_INTERNAL_WORKFLOW` |
| Significant-change notification and Plan-of-Care approval controls | `CALIFORNIA_REQUIRED` |
| Automatic SFV creation or completion from routine LVN documentation | `PROHIBITED` |
| Exact late-record submission treatment | `PENDING_SOURCE_VALIDATION` |
| Exact invalid-sequence fatal/warning edit | `PENDING_SOURCE_VALIDATION` |
| Backdating a late SFV | `PROHIBITED` |
| Schedule completion equals SFV completion | `PROHIBITED` |

## Implementation Boundary

`NOT_AUTHORIZED`. This document is discovery/documentation only. No
application behavior, JSX, Tailwind, routes, APIs, migrations, schemas,
enums, or production data are introduced or implied by this document.
