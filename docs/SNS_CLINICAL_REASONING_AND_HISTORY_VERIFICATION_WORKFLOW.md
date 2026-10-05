# SNS Clinical Reasoning and Medical-History Verification Workflow

**Status:** Draft SNS workflow specification for later implementation  
**Current phase:** Documentation design  
**Applies to:** RNICA, Evidence & Intake, Patient Story, Diagnosis & LCD, Clinical Review, recertification review, and future discipline workflows  
**Deferred:** Ontology completion, Intelligence Harvester reasoning weights, AI-generated conclusions, diagnosis coding, and automated eligibility determinations

---

## 1. Purpose

SNS must help the hospice clinician:

1. Recognize immediate threats.
2. Keep the patient safe.
3. Keep the patient comfortable.
4. Understand the patient's actual medical story.
5. Distinguish known facts from reported or missing history.
6. Focus attention on the primary terminal diagnosis and related conditions.
7. Elevate unrelated findings when they materially affect safety or comfort.
8. Track missing records without blocking documentation of the current bedside assessment.
9. Preserve source attribution and correction history.
10. Reduce duplicate entry and administrative follow-up burden.

The governing clinical question is:

> Do we know enough to care for this patient safely, keep the patient comfortable, support the patient and family, and accurately understand the patient’s current clinical story?

---

## 2. Authority boundaries

This specification separates regulatory requirements from SNS policy.

### Confirmed federal requirements

- The hospice must complete and document a patient-specific comprehensive assessment addressing physical, psychosocial, emotional, and spiritual needs related to the terminal illness and related conditions.
- The assessment considers available objective information, subjective complaints, complications and risks, function, symptom severity, imminence of death, and medication profile.
- The clinical record must contain correct available clinical information, including assessments, plans of care, clinical notes, symptom-management response, certifications, directives, and orders.

### SNS policy proposed in this document

- ABCs, Maslow/basic needs, safety, comfort, history verification, diagnosis-aware interpretation, longitudinal comparison, and family preparation form the clinical-reasoning workflow.
- Source-confidence labels, missing-record statuses, task priorities, dashboards, and escalation behavior are SNS internal workflow choices.
- AI may organize and draft, but may not independently confirm diagnoses, determine relatedness, establish eligibility, or close evidence tasks.

---

## 3. Clinical-reasoning sequence

### Layer 1: Immediate physiologic stability

Assess first:

- Airway
- Breathing
- Circulation
- Acute change in consciousness
- Uncontrolled bleeding or other time-sensitive deterioration

**SNS behavior**

- Urgent observations surface above routine body-system review.
- Immediate threats cannot be hidden behind collapsed sections.
- SNS records the observation and escalation status without independently diagnosing the cause.

### Layer 2: Basic needs and symptom burden

Assess:

- breathing comfort;
- pain;
- nutrition and hydration;
- elimination;
- sleep and rest;
- temperature and environmental comfort;
- communication;
- mobility and positioning;
- emotional, psychosocial, and spiritual distress.

### Layer 3: Safety

Evaluate:

- falls or syncope;
- aspiration;
- medication safety;
- oxygen, lines, tubes, and equipment;
- skin integrity;
- infection;
- cognition or behavior;
- transfers and ambulation;
- caregiver capability;
- home environment;
- food, utilities, medications, and emergency support.

**Override rule:** A material safety concern may outrank diagnosis-based focus.

### Layer 4: Comfort and goals of care

Determine:

- Is the patient comfortable now?
- Which symptoms cause distress?
- Which interventions are effective?
- What does the patient want?
- What does the family understand?
- What education or preparation is needed?
- Is the current care consistent with goals?

**Override rule:** An uncontrolled comfort concern may outrank diagnosis-based focus.

### Layer 5: Medical-story verification

Treat referral and current H&P as starting evidence, not automatically as the complete history.

Ask:

- What does the referral say?
- What is supported by received records?
- What is reported only by the patient, family, or caregiver?
- Which diagnoses are confirmed?
- Which diagnoses are incomplete, contradictory, or unverified?
- Which prior PCPs, specialists, facilities, hospitalizations, and procedures are missing?
- Does the known history explain the current observations?
- Are important periods of progression absent?

### Layer 6: Diagnosis-aware interpretation

Relate current findings to:

1. Proposed principal terminal diagnosis
2. Related secondary diagnoses
3. Other contributing conditions
4. Conditions currently considered unrelated
5. Safety concerns
6. Comfort concerns
7. Unexplained findings

Relationship states:

- Confirmed by clinician
- Supported by received evidence
- Possible relationship requiring review
- Unrelated per approved determination
- Not yet determined

SNS must not infer terminal relatedness solely from common co-occurrence.

### Layer 7: Longitudinal comparison

Classify observations as:

- New
- Worsening
- Stable
- Improving
- Fluctuating
- Unable to compare
- Conflicting sources
- Prior baseline unavailable

Do not convert missing baseline into “stable” or “no change.”

### Layer 8: Family understanding and end-of-life preparation

Track:

- understanding of illness;
- awareness of expected changes;
- signs requiring a hospice call;
- goals and preferences;
- caregiver readiness and limitations;
- unresolved disagreement;
- requested support;
- education provided;
- follow-up education needed.

Avoid requiring the nurse to re-enter the same education narrative in multiple sections.

---

## 4. Medical-history verification workflow

### Step 1: Capture the reported story

Capture without prematurely confirming:

- reported condition or event;
- approximate date or period;
- source person or source document;
- reporter relationship;
- provider or facility if known;
- city and state;
- records availability;
- immediate safety or comfort relevance;
- clarification note.

### Step 2: Build provider and facility history

Maintain a chronological directory containing:

- provider or organization name;
- provider type;
- specialty;
- city and state;
- approximate period of care;
- phone and fax;
- health-information-management contact;
- request method;
- source who identified the provider;
- potentially relevant record types.

Permitted date precision:

- exact date;
- month/year;
- year only;
- approximate period;
- unknown.

### Step 3: Build hospitalization and major-event history

Capture:

- facility;
- location;
- admission and discharge date or approximation;
- reason for visit;
- reported diagnoses;
- procedures or treatments;
- discharge destination;
- record status;
- possible relevance to the terminal condition;
- safety or comfort relevance;
- verification state.

### Step 4: Classify provenance

Allowed source classifications:

- Primary clinical record received
- Provider-confirmed
- Corroborated by multiple sources
- Patient-reported
- Family/caregiver-reported
- Referral-reported
- Medication-supported
- Observed by hospice clinician
- Conflicting information
- Source unavailable
- Not yet verified

These describe provenance and do not rank a person's credibility.

### Step 5: Identify history gaps

Examples:

- incomplete H&P;
- missing discharge summary;
- unknown prior PCP or specialist;
- reported hospitalization without records;
- diagnosis without source evidence;
- medication suggesting an undocumented condition;
- device or procedure without documentation;
- inconsistent diagnosis dates;
- conflicting allergies;
- conflicting code status;
- missing progression evidence;
- unavailable baseline.

### Step 6: Classify operational priority

#### Immediate safety blocker

Use when missing information is required for safe current care, such as:

- medication or dose conflict;
- uncertain oxygen order;
- unresolved allergy conflict;
- unclear code status requiring immediate clarification;
- uncertain device status affecting present care;
- missing information needed to manage severe active symptoms.

Required behavior:

- prominent alert;
- responsible owner;
- due-now state;
- escalation path;
- documented interim safety plan.

#### Admission or care-planning priority

Use when information materially affects comprehensive assessment or planning but current care can proceed safely.

#### Longitudinal enhancement

Use for older records that may strengthen disease-progression history, recertification support, or the consolidated patient story.

These priority definitions require final SNS clinical-governance approval before production use.

### Step 7: Create a bounded record request

Capture:

- source;
- requested documents;
- requested date range;
- purpose;
- authorization state;
- request date/time;
- request method;
- sender;
- destination;
- transmission confirmation;
- next follow-up date;
- priority;
- owner;
- status;
- attempt history;
- response;
- linked documents;
- closure reason.

Prefer a bounded request that answers the clinical question. Allow a broader request when fragmented history reasonably requires it and authorization permits it.

### Step 8: Receive and reconcile

1. Link documents to the request.
2. Verify patient identity match.
3. Record received date and file/page count if available.
4. Mark the requested scope complete, partial, unclear, or not received.
5. Extract candidate diagnoses, hospitalizations, procedures, medications, devices, and findings.
6. Present extracted candidates for authorized clinician confirmation.
7. Preserve the source document unchanged.
8. Record provenance for accepted structured facts.
9. Flag conflicts instead of overwriting.
10. Close, renew, or narrow the request.

AI-extracted material remains proposed until clinician confirmation.

### Step 9: Update the clinical story

An authorized reviewer determines whether evidence changes:

- principal terminal diagnosis consideration;
- related-condition review;
- secondary diagnoses;
- symptom interpretation;
- baseline;
- disease trajectory;
- safety plan;
- comfort measures;
- plan of care;
- patient/family education;
- certification or recertification support.

---

## 5. RNICA behavior

Missing history must not stop documentation of current observations.

RNICA displays distinctly:

- Current observed finding
- Observation source
- Historical baseline unavailable
- Open evidence request
- Clinical interpretation pending evidence

RNICA must not present an unverified historical statement as confirmed.

---

## 6. Patient Story behavior

### Known and supported

- confirmed diagnoses;
- verified hospitalizations;
- significant procedures;
- progression history;
- known providers.

### Reported, not yet confirmed

- family-reported history;
- approximate hospitalizations;
- suspected diagnoses;
- incomplete date ranges.

### Active information gaps

- requests pending;
- requests overdue;
- partial records;
- conflicting evidence;
- unknown providers or facilities.

Do not merge these categories into one narrative without source labels.

---

## 7. Future Intelligence Harvester behavior

After documentation workflows are completed and the ontology is rebuilt, the Intelligence Harvester may:

- detect missing periods;
- identify mentioned prior providers or hospitalizations;
- propose an evidence-request candidate;
- extract facts with provenance;
- connect evidence to the timeline;
- surface contradictions;
- draft a consolidated medical history;
- explain what remains unverified.

The Intelligence Harvester may not independently:

- send a record request;
- sign or create an authorization;
- confirm a diagnosis;
- determine terminal relatedness;
- determine hospice eligibility;
- close an evidence task;
- overwrite clinician-confirmed information.

---

## 8. Acceptance criteria

The workflow passes only when:

- present safety and comfort documentation can continue despite missing history;
- every historical fact has provenance;
- reported information is distinguishable from verified information;
- every open request has an owner and next action;
- attempts are append-only;
- partial records remain visibly incomplete;
- conflicting records are not silently overwritten;
- documents are linked to the correct patient and Admission;
- AI-extracted content requires confirmation;
- active gaps surface without duplicate manual entry;
- closure requires a documented outcome;
- role permissions, patient isolation, Admission isolation, and audit history pass;
- absence of a record is never treated as proof that an event did not occur.
