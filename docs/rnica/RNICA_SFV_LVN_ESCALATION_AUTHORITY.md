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

## Source Registry

- CMS HOPE Guidance Manual v1.02, Chapter 1 and Section J.
- CMS HQRP Quality Measure Specifications, HOPE Timely Follow-up Measures.
- CMS HOPE v1.01 to v1.02 Guidance Manual and Item Set Change Table,
  J2053.
- CMS HOPE Implementation FAQs.
- California CDPH DPH-18-002E, §§74864, 74868, and 74872.

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

## Implementation Boundary

`NOT_AUTHORIZED`. This document is discovery/documentation only. No
application behavior, JSX, Tailwind, routes, APIs, migrations, schemas,
enums, or production data are introduced or implied by this document.
