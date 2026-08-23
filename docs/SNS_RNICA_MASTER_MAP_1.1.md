# SNS RNICA Master Map 1.1

Status: **APPROVED FOR GOVERNANCE REVIEW — Architecture Complete. No
Further Architecture Work Required.**
Next Deliverable: `SNS_RNICA_SECTION_INVENTORY_1.0`.
**No Code Changes Authorized Without Separate Approval.**
Companion to: `SNS_DESIGN_SYSTEM_1.0.md`, `SNS_POC_GENERATION_MATRIX_1.0.md`,
`SNS_RNICA_SECTION_INVENTORY_1.0.md` (implementation-detail inventory).

This is the target 12-section architecture for the RNICA redesign, plus a
global (non-numbered) Admission Action Center. It supersedes the looser
"tier" language used in earlier drafts of this governance thread — treat the
section numbers below as canonical for all future references.

## Governance Freeze

As of this version, the following artifacts are **frozen** for the
duration of the `SNS_RNICA_SECTION_INVENTORY_1.0` inventory work (Field,
Database, API, Validation, Narrative Source, HOPE, Audit, Action Center
Trigger, POC Evidence, and Migration Complexity mapping):

- Section Names
- Section Numbers
- POC Ownership
- Master POC Rules
- Action Center Rules
- Dependency Flow
- Evidence Requirements
- Governance Rules

Any future change to these artifacts must go through a **Version 1.1
governance process** (a new, explicit revision cycle), not through ongoing
architectural edits made while inventory work is in progress. This
prevents Field → Database → API → UI mapping from being done against a
moving target. The next deliverable is `SNS_RNICA_SECTION_INVENTORY_1.0`,
not further architecture changes to this document.

---

## Version 1.1 Amendment

**Version 1.1 supersedes the lightweight Section 1-12 descriptions from Version 1.0 below.** The complete verbatim Facesheet RN ICA Implementation Map content (Global Facesheet Frame, Sections 1-12 in full clinical detail, Global Admission Action Center, Facesheet Navigation Behavior, and Definition of Done) is now inserted, unabridged, as the authoritative build specification for RN ICA. Body System Assessment and Imminently Dying remain fully intact. The Master Sync Rules, prior Admission Action Center summary, Dependency Flow, Parallel Workflow, and Status/Next Steps sections from Version 1.0 are preserved unmodified as an addendum at the end of this document.

---

SNS RN ICA COMPLETE FACESHEET IMPLEMENTATION MAP

BUILD RULE

The Facesheet pattern governs the entire RN ICA experience.

The Facesheet is not a small summary placed above the existing form.
The Facesheet is the patient-centered navigation, status, and action layer
through which the complete RN ICA is documented.

All existing RN ICA fields must be preserved.

Do not remove:
- Body System Assessment
- Sleep / Rest
- Imminently Dying
- HOPE items embedded in their clinical locations
- POC controls
- Admission Actions
- Narrative
- Final Review and Signature

GLOBAL FACESHEET FRAME

Always visible:

- Patient identity
- MRN
- DOB
- Benefit period
- Level of care
- Terminal diagnosis
- Related diagnoses
- Code status
- Allergies
- Residence / facility
- Attending physician
- Medical director
- Primary caregiver
- Decision-maker
- Current PPS / KPS / FAST / NYHA
- Assessment completion status
- Autosave status
- Immediate clinical alerts
- Admission Action Center
- Current section navigation

==================================================
SECTION 1 — PATIENT & ENCOUNTER SNAPSHOT
==================================================

Contains:

PATIENT

- Patient name
- MRN
- DOB
- Age
- Sex
- SOC date
- Benefit period
- Level of care
- Payer
- Residence type
- Facility
- Site of service
- Admitted from
- Living arrangement

CLINICAL IDENTITY

- Terminal diagnosis
- Related diagnoses
- Unrelated diagnoses
- Comorbidities
- Code status
- Allergies
- Current medication summary

CARE TEAM

- Attending physician
- Medical director
- Assigned RN
- Assigned disciplines
- Primary caregiver
- Decision-maker
- Emergency contact

COMMUNICATION

- Preferred language
- Interpreter need
- Communication limitations
- Cultural considerations

POC FUNCTIONS

- View Master POC
- View active problems
- View goals
- View interventions

This section displays authoritative information.
It does not duplicate or independently own patient data.

==================================================
SECTION 2 — IMMEDIATE NEEDS & SYMPTOM TRIAGE
==================================================

Contains:

PAIN SCREENING

- Able to verbalize pain
- Patient discomfort from pain
- Pain present
- Pain score
- Pain location
- Pain type
- Pain frequency
- Pain duration
- Pain impact
- Current treatment
- Response to treatment
- Non-pharmacologic measures
- Medication effectiveness
- Side effects

IMMEDIATE SYMPTOMS

- Dyspnea
- Anxiety
- Agitation
- Nausea
- Vomiting
- Diarrhea
- Constipation
- Secretions
- Bleeding
- Acute distress
- Current interventions
- Response

LOCAL POC CONTROLS

- Add to POC
- View POC
- Update POC
- Resolve POC

ACTION CENTER TRIGGERS

- Medication review
- Physician contact
- Oxygen
- Urgent order
- Office communication

==================================================
SECTION 3 — DISEASE HISTORY & CLINICAL TRAJECTORY
==================================================

Contains:

- Primary diagnosis
- Secondary diagnoses
- Related / unrelated status
- Principal diagnosis category
- Comorbidities
- Disease onset
- Disease progression
- Hospitalizations during applicable lookback periods
- ER visits
- Physician visits
- Falls
- Infections
- Weight changes
- Functional changes
- Cognitive changes
- Prior treatments
- Current treatments
- Patient / family report
- Medical-record evidence
- Illness trajectory

TRAJECTORY

- Rapid decline
- Saw-toothed decline
- Slow, steady decline
- Other documented trajectory

Supports:

- Admission narrative
- LCD evidence baseline
- Decline-of-status baseline
- Diagnoses
- Initial POC

==================================================
SECTION 4 — FUNCTIONAL & PERFORMANCE STATUS
==================================================

PERFORMANCE SCALES

- PPS
- KPS
- FAST
- NYHA
- ECOG, when used

MOBILITY

Ambulatory:

- Independent
- Cane
- Walker
- Wheelchair
- Stand-by assistance
- Moderate assistance
- Maximum assistance
- Endurance before resting
- Ramp availability when applicable

Non-ambulatory:

- Bedbound
- Bed rest with bathroom privileges
- Up as tolerated
- Maximum assistance
- Bed-to-chair transfer
- Prescribed exercise
- Range of motion

ADL ASSESSMENT

Dependence scale:

- 0 Independent
- 1 Minimal assistance / supervision
- 2 Moderate assistance
- 3 Maximum / complete dependence

Activities:

- Ambulation
- Toileting / continence
- Transfer
- Dressing
- Feeding
- Bathing

Calculated:

- Total ADL score
- Number of activities with complete dependence

COMPARISON

- Current value
- Previous value
- Change
- Source assessment
- Assessment date

LOCAL POC CONTROLS

- Add to POC
- View POC
- Update POC
- Resolve POC

==================================================
SECTION 5 — BODY SYSTEM ASSESSMENT
HEAD-TO-TOE
==================================================

This section is mandatory and must remain complete.

Each body-system card contains:

- Current findings
- Previous findings
- Change indicator
- Clinical observations
- Other observations
- HOPE item references where applicable
- Add to POC
- View POC
- Update POC
- Resolve POC
- Relevant Admission Action Center actions

--------------------------------------------------
5.1 NEUROLOGICAL / MENTAL / SENSORY
--------------------------------------------------

Symptoms / demeanor:

- Anxiety
- Agitation
- Peaceful
- Confused
- Angry
- Restless
- Depressed
- Seizure
- Combative
- Sundowning
- Tremors / twitching
- Other

Level of consciousness:

- Awake
- Alert
- Lethargic
- Minimally responsive
- Coma

Orientation:

- Time
- Place
- Person
- Disoriented

Psychiatric history:

- None
- Bipolar disorder
- OCD
- Schizophrenia
- Depression
- Other

Communication / voice / speech:

- Normal
- Aphasia
- Slurred speech
- Other
- Speech limited to six or fewer intelligible words

Sensory deficits:

- Blind
- Hard of hearing / deaf
- Other

Sensory aids:

- Glasses
- Hearing aids
- Other

Balance:

- Normal
- Impaired

POC possibilities:

- Cognitive impairment
- Communication deficit
- Confusion
- Anxiety
- Agitation
- Safety risk
- Seizure risk

--------------------------------------------------
5.2 CARDIOVASCULAR
--------------------------------------------------

Blood-pressure status:

- Normal
- Hypotension
- Hypertension

Pulse sites:

- Apical
- Pedal
- Radial
- Femoral

Pulse characteristics:

- Regular
- Irregular
- Weak
- Tachycardia
- Bradycardia
- Absent

Additional findings:

- Cardiac-related pain
- Edema
- Edema location
- Pitting level
- Skin color
- Pacemaker
- Internal defibrillator
- Jugular-vein distention
- Varicose veins
- Central venous line
- Cool extremities
- Stasis ulcer
- Other observations

POC possibilities:

- Fluid-volume excess
- Cardiac symptoms
- Edema
- Perfusion concern
- End-stage heart-disease support

--------------------------------------------------
5.3 RESPIRATORY
--------------------------------------------------

Symptom impact:

- Shortness of breath severity
- Treatment declined when applicable

Exertion level:

- At rest
- Mild exertion
- With speech
- Push of speech
- Pursed-lip breathing
- Other

Lung sounds:

- Clear
- Diminished
- Wheezes
- Crackles
- Rales
- Rhonchi

Respirations:

- Normal
- Labored
- Agonal
- Tachypnea
- Bradypnea
- Cheyne-Stokes
- Orthopnea

Cough:

- None
- Dry / nonproductive
- Productive
- Hemoptysis
- Sputum color
- Barrel chest

Oxygen:

- Oxygen therapy present
- Oxygen rate
- Nasal cannula
- Mask
- Continuous
- PRN
- Oxygen saturation
- Room air
- Saturation at ordered flow rate

Ventilator / airway support:

- Short-term ventilator
- Long-term ventilator
- Ventilator type and settings
- Tracheostomy type
- Tracheostomy size

POC possibilities:

- Dyspnea
- Impaired breathing pattern
- Oxygen dependence
- Airway-clearance problem
- Respiratory distress

Action Center:

- Oxygen
- Nebulizer
- Medication
- DME
- Physician contact

--------------------------------------------------
5.4 IMMUNOLOGICAL / INFECTION
--------------------------------------------------

Allergies:

- Food allergies
- Other allergies
- Sensitivities
- Allergy details

Immune status:

- Immunosuppressed
- Not immunosuppressed

Antibiotic-resistant infection:

- None
- MRSA
- C. difficile
- Other

History of resistant infection:

- None
- MRSA
- C. difficile
- Other

Current active infection:

- None
- Sepsis
- UTI
- Respiratory tract
- IV site
- Wound
- HIV-related
- Pressure area
- Other

Additional:

- Antibiotic use
- Temperature
- Recurrent infection
- Infection history
- Other observations

POC possibilities:

- Active infection
- Infection risk
- Recurrent infection

Action Center:

- Physician contact
- Medication review
- Treatment order
- Lab request

--------------------------------------------------
5.5 GASTRO-INTESTINAL
--------------------------------------------------

Symptom impact:

- Nausea
- Vomiting
- Vomiting occurrences in 24 hours
- Diarrhea
- Constipation

Abdomen:

- Soft
- Firm
- Tympanic
- Tender
- Nontender
- Ascites
- Abdominal girth

Bowel sounds:

- Normal
- Hyperactive
- Hypoactive
- Absent

Stool:

- Normal
- Bloody
- Colostomy
- Ileostomy

Bowel status:

- Regular
- Impaction
- Continent
- Incontinent
- Bowel / bladder program
- Frequency
- Last bowel movement
- Reason bowel regimen could not be initiated
- Other observations

POC possibilities:

- Nausea
- Vomiting
- Diarrhea
- Constipation
- Impaction
- Bowel-management problem
- GI symptom burden

--------------------------------------------------
5.6 NUTRITION / HYDRATION
--------------------------------------------------

Measurements and decline:

- Current weight
- Previous weight
- Weight change
- Weight loss greater than 10 percent
- Height
- BMI
- MAC
- Albumin when available

Appetite:

- Good
- Fair
- Poor
- Anorexia
- Cachexia
- NPO

Swallowing:

- Hiccups
- Dysphagia
- Aspiration precautions
- Aspiration history
- Choking on liquids

Hydration:

- Inadequate fluid intake
- Dry membranes
- Poor skin turgor
- IV fluids

Intake / diet:

- No concerns
- Patient concern
- Caregiver / family concern
- Regular
- Mechanical soft
- Puree
- Liquid
- NPO
- Other

Artificial feeding:

- None
- PEG
- NG
- J-tube
- Pump
- TPN

Oral cavity:

- Normal
- Edentulous
- Stomatitis
- Thrush
- Poor dentition
- Upper dentures
- Lower dentures
- Other

POC possibilities:

- Nutritional deficit
- Weight loss
- Poor intake
- Hydration deficit
- Dysphagia
- Aspiration risk

--------------------------------------------------
5.7 ENDOCRINE
--------------------------------------------------

Impairment:

- Thyroid
- Parathyroid
- Pituitary
- Adrenal
- Pancreas

Diabetes:

- Insulin-dependent
- Non-insulin-dependent
- Glucose-management concern

Additional:

- Endocrine symptoms
- Current treatment
- Other observations

POC possibilities:

- Glucose-management problem
- Endocrine symptom-management problem

--------------------------------------------------
5.8 GENITOURINARY / REPRODUCTIVE
--------------------------------------------------

Urinary continence:

- Continent
- Incontinent
- Bladder program
- Urostomy
- Retention
- Painful urination
- Nocturia

Urine:

- Clear
- Cloudy
- Pale
- Color
- Blood
- Odor

Catheter:

- None
- Foley
- Condom
- Suprapubic
- Urostomy
- Catheter size
- Last-change date

Irrigation:

- Solution
- Frequency
- Duration

Additional:

- Urinary output
- Catheter care
- Other observations

POC possibilities:

- Urinary-elimination problem
- Incontinence
- Retention
- Catheter-management problem
- Urostomy-management problem

--------------------------------------------------
5.9 SLEEP / REST
--------------------------------------------------

Sleep pattern:

- None identified
- Overly drowsy
- Insomnia
- Excessive sleep
- Lack of sleep
- Satisfied with sleep

Additional:

- Sleep duration in 24 hours
- Nighttime symptoms
- Current sleep interventions
- Response
- Other observations

POC possibilities:

- Sleep-pattern disturbance
- Excessive sleep
- Insomnia
- Comfort concern

--------------------------------------------------
5.10 MUSCULOSKELETAL
--------------------------------------------------

Issues:

- Rigidity
- Range-of-motion loss
- Weakness
- Joint swelling
- Spasms / cramps
- Amputation
- Prosthesis
- Contractures
- None

Disability:

- Paraplegia
- Quadriplegia
- Right hemiplegia
- Left hemiplegia
- Right hemiparesis
- Left hemiparesis

Additional:

- Strength
- Mobility
- Transfer ability
- Balance
- Pain with movement
- Other observations

POC possibilities:

- Weakness
- Mobility deficit
- Transfer assistance
- Contracture management
- Fall risk

--------------------------------------------------
5.11 INTEGUMENTARY - SKIN
--------------------------------------------------

This is named Integumentary - Skin.
Do not rename the section Skin/Wounds only.

Skin condition:

- Skin-condition gate
- Normal
- Cool
- Warm
- Dry
- Diaphoretic
- Jaundice
- Mottling

Skin turgor:

- Good
- Fair
- Poor

Skin impairment:

- None
- Present
- Skin-impairment assessment required when present

Impairment details:

- Pressure injury
- Stage
- Wound
- Wound type
- Location
- Length
- Width
- Depth
- Drainage
- Odor
- Periwound condition
- Skin tear
- Surgical wound
- Bruising
- Rash
- Nonhealing wound
- Current treatment
- Dressing
- Dressing frequency
- Pressure-relief measures
- Repositioning plan

Braden assessment:

- Sensory perception
- Moisture
- Activity
- Mobility
- Nutrition
- Friction and shear
- Total score
- Risk category

POC possibilities:

- Impaired skin integrity
- Pressure injury
- Risk for skin breakdown
- Delayed wound healing
- Altered tissue integrity

Goals:

- Promote comfort
- Prevent further breakdown
- Prevent infection
- Promote healing

Interventions:

- Wound assessment
- Wound care
- Dressing changes
- Pressure relief
- Repositioning
- Caregiver education

Action Center:

- Wound supplies
- Dressings
- Hospital bed
- Low-air-loss mattress
- Pressure-relief cushion
- Physician contact

--------------------------------------------------
5.12 IMMINENTLY DYING
--------------------------------------------------

THIS SUBCARD IS REQUIRED.
DO NOT REMOVE IT.
DO NOT MERGE IT INTO NARRATIVE.
DO NOT MOVE IT TO FINALIZATION ONLY.

HOPE item:

- J0050 Death Is Imminent

Core question:

- At the time of this assessment, does the patient appear to have a life expectancy of three days or less?
- Yes
- No

Status indicators:

- Decreased level of consciousness
- Decreased food and fluid intake
- Increased fatigue
- Increased sleeping
- Increased agitation
- Decrease or absence of bowel function
- Decrease or absence of bladder function
- Increased respiratory distress

Additional findings:

- Minimally responsive
- Unresponsive
- Coma
- Mottling
- Cool extremities
- Changes in breathing pattern
- Agonal respirations
- Cheyne-Stokes respirations
- Increased secretions
- Loss of swallowing ability
- Reduced urine output
- Restlessness
- Terminal agitation
- Family / caregiver education completed
- Comfort medications available
- Oxygen available when indicated
- DME and supplies available
- Physician notified when indicated
- IDT notified when indicated
- Other observations

POC possibilities:

- Imminent death
- Terminal agitation
- Respiratory distress
- Secretions
- Comfort-management need
- Caregiver-support need

Immediate actions:

- Medication request
- Comfort-kit review
- Physician contact
- Oxygen
- Suction
- DME
- Supplies
- Spiritual-care referral
- Social-work referral
- Bereavement notification
- Office communication

The comprehensive assessment must include symptoms indicating the imminence of death and must address comfort and dignity throughout the dying process. DPH-18-002E-HospiceAgencies_Text.pdf 【1-700d52】【2-1aef14】

==================================================
SECTION 6 — DISEASE-SPECIFIC CRITERIA & LCD SUPPORT
==================================================

Contains:

- Non-disease-specific criteria
- General decline
- Functional decline
- ADL dependence
- PPS
- KPS
- FAST
- NYHA
- Nutritional decline
- Weight loss
- MAC decline
- BMI decline
- Hospitalizations
- ER visits
- Infections
- Pressure injuries
- Comorbidities

Disease pathways:

- Dementia
- ALS
- Cancer
- Heart disease
- Pulmonary disease
- Stroke / coma
- Renal disease
- Liver disease
- HIV
- Other approved pathways

Behavior:

- Display criteria
- Display supporting RN ICA evidence
- Link to source assessment
- Show met / not met / unavailable / not assessed
- Allow clinician explanation
- Do not automatically certify eligibility
- Do not create duplicate POC problems

Baseline and follow-up clinical evidence are important when decline supports terminal prognosis. hospice_terminal_prog_non-disease_specific.pdf 【3-555368】【4-95a45b】

==================================================
SECTION 7 — HOPE ADMISSION & SYMPTOM FOLLOW-UP
==================================================

RN ICA behavior:

- Harvest HOPE Admission information from RN ICA
- Show completion status
- Show missing HOPE Admission sources
- Do not show regulatory sections as the clinical workflow
- Do not require duplicate entry
- Generate HOPE Admission only from completed and reviewed source data

SFV behavior:

- Monitor symptom-impact findings
- Identify applicable follow-up requirements
- Display status
- Do not create HUV1 or HUV2
- Do not force a future visit

Separate future events:

- HUV1 visit generates HOPE HUV1 when HUV1 occurs
- HUV2 visit generates HOPE HUV2 when HUV2 occurs
- Discharge workflow generates HOPE Discharge when discharge occurs

==================================================
SECTION 8 — WHOLE PERSON, CAREGIVER & SUPPORT
==================================================

CAREGIVER

- Caregiver identity
- Availability
- Health status
- Capacity
- Willingness
- Medication-administration capability
- Anxiety
- Burden
- Education needs
- Safety concerns
- Young children
- Pets
- Additional support

PSYCHOSOCIAL

- Family / social support
- Acceptance of diagnosis
- Compliance concerns
- Coping
- Anxiety
- Anger
- Depression
- Suicide concerns
- Substance-use concerns
- Emotional history
- Financial concerns
- Legal concerns
- Strained relationships
- Cultural concerns
- Burial concerns
- Advance-directive need
- Funeral-planning need
- Distress rating
- Social-work visit need

SPIRITUAL

- Faith tradition
- Patient faith
- Caregiver faith
- Fear
- Hopelessness
- Meaning of illness
- Clergy request
- Declines discussion
- Spiritual-distress rating
- Spiritual-care visit need

BEREAVEMENT

- Patient concerns
- Caregiver concerns
- Multiple losses
- Active grieving
- Risk level
- Bereavement visit need
- Other observations

PERSONAL CARE

- Hospice-aide need
- Grooming
- Light meal preparation
- Linen change
- ADL support

TEACHING NEEDS

- Diagnosis
- Disease process
- Medication administration
- Medication side effects
- Contraindications
- Comfort pack
- Opioid use and risk
- Medication reconciliation
- Oxygen
- DME
- Infection control
- Universal precautions
- Controlled-medication disposal
- Other education

==================================================
SECTION 9 — SAFETY, ENVIRONMENT, DME & SUPPLIES
==================================================

SAFETY

- Safety assessment status
- Fall-risk assessment
- Transfer safety
- Environmental hazards
- Disaster triage
- Incident / occurrence linkage

DISASTER TRIAGE

- Level 1
- Level 2
- Level 3
- Bed- or chair-confined
- Above-ground-floor residence
- Walker / cane dependence
- Electricity-dependent equipment
- Facility disaster support
- Alternate location
- Available helper

DME

For each item:

- Has
- Needs
- Ordered
- Delivered
- Declined
- Not applicable

Items:

- Air mattress
- Bed
- Bedpan
- Egg crate
- Overbed table
- Cane
- Walker
- Wheelchair
- Shower chair
- Geri-chair / recliner
- Hoyer lift
- Urinal
- Commode
- Nebulizer
- Suction machine
- Oxygen concentrator
- E-tank
- Other

SUPPLIES

- Existing supplies
- Needed supplies
- Wound supplies
- Continence supplies
- Oxygen supplies
- Medication supplies
- Other supplies

The assessment identifies needs.
The Admission Action Center initiates the request or order.

==================================================
SECTION 10 — CLINICAL NARRATIVE & DISEASE TRAJECTORY
==================================================

Generated from the full assessment:

- Patient-specific clinical summary
- Terminal-disease summary
- Admission circumstances
- Disease trajectory
- Functional decline
- ADL dependence
- Cognitive decline
- Symptom burden
- Pain burden
- Respiratory burden
- Nutritional decline
- Weight / BMI / MAC findings
- Infection history
- Integumentary findings
- Hospitalization and ER utilization
- Caregiver situation
- Psychosocial findings
- Spiritual findings
- Imminently dying findings when present
- Prognosis-supporting evidence

Editable:

- RN addendum
- Clinician clarification

Rules:

- Narrative remains draft until reviewed
- Narrative uses documented evidence
- Narrative does not silently invent conclusions
- Narrative references current POC
- Narrative does not originate a duplicate POC

==================================================
SECTION 11 — MASTER PLAN OF CARE REVIEW
==================================================

Contains:

- Active problems
- Goals
- Outcome measures
- Interventions
- Disciplines
- Visit frequencies
- Treatments
- Education
- Tasks
- Referrals
- DME
- Supplies
- Medication-support needs
- Safety measures
- Dietary needs
- Personal-care needs
- Caregiver responsibilities
- Physician approvals
- Current statuses
- Source evidence links

Controls:

- View problem
- Edit problem
- Resolve problem
- Deactivate problem
- Merge duplicate problems
- Link existing problem
- View history

Does not:

- Become the primary problem-creation surface
- Create duplicate problems
- Replace the assessment section that originated the problem

The comprehensive assessment serves as the basis for the individualized plan of care, and the plan includes symptoms, services and frequencies, pain management, medication assistance, equipment, supplies, treatments, limitations, diet, allergies, palliative needs, and safety measures. DPH-18-002E-HospiceAgencies_Text.pdf 【5-c932a6】【2-1aef14】

==================================================
SECTION 12 — FINAL REVIEW, SIGNATURE & FINALIZATION
==================================================

Validate:

- Required RN ICA sections complete
- Body System Assessment complete or exceptions documented
- Imminently Dying reviewed
- Required HOPE Admission source fields reviewed
- Required POCs reviewed
- Goals present
- Interventions present
- Disciplines assigned
- Frequencies assigned
- Orders and requests reviewed
- Narrative reviewed
- LCD evidence baseline available
- Decline baseline created
- Referrals reviewed
- Outstanding issues displayed
- Required signatures present

Finalization:

- RN signature
- Signature date and time
- Patient / caregiver acknowledgment when applicable
- Attestation
- Assessment lock
- Audit event
- Correction / amendment path

Generated outputs:

- HOPE Admission
- Initial Clinical Narrative
- Initial Master POC
- LCD evidence baseline
- Decline-of-Status baseline

==================================================
GLOBAL ADMISSION ACTION CENTER
NOT A NUMBERED SECTION
==================================================

Available throughout RN ICA:

- Medication request
- Medication refill
- Physician order
- DME order
- Supply order
- Wound-supply order
- Oxygen order
- Lab request
- Treatment order
- Diet order
- Referral
- Physician contact
- Office communication
- IDT communication

Requirements:

- Does not lose RN ICA draft data
- Does not move the nurse away from the current section
- Does not require RN ICA completion
- Shows request status
- Distinguishes requested, ordered, sent, acknowledged, delivered, and completed

==================================================
FACESHEET NAVIGATION BEHAVIOR
==================================================

The Facesheet displays:

- Patient Snapshot
- Immediate Risks
- Assessment completion
- Body-system status
- Active POC summary
- Open actions
- Narrative status
- HOPE Admission readiness
- LCD evidence status
- Decline baseline status
- Finalization status

The nurse selects a card to enter the focused workspace.

The system must never remove or hide the Body System Assessment.

The system must never remove or hide Imminently Dying.

==================================================
DEFINITION OF DONE
==================================================

RN ICA is complete when:

1. Every existing RN ICA field is preserved.
2. The full Body System Assessment is present.
3. Imminently Dying is present and functional.
4. HOPE Admission can be generated without duplicate entry.
5. Initial POC can be created from assessment findings.
6. Initial narrative can be generated and reviewed.
7. LCD evidence baseline can be displayed.
8. Decline-of-Status baseline can be created.
9. Immediate actions can be initiated without completing the assessment.
10. The assessment can be reviewed, signed, locked, corrected, and audited.
11. HUV1 is not created by RN ICA.
12. HUV2 is not created by RN ICA.
13. HOPE Discharge is not forced during admission.
---

## Addendum - Preserved From Master Map 1.0 (Still Authoritative)

## Master Sync Rules (Critical)

The per-section POC panels (Sections 2–9) and the Master Plan of Care
Review (Section 11) are **two views of the same data, not two data
stores.** This is the architecture that makes per-section POC creation
(`SNS_POC_GENERATION_MATRIX_1.0.md` §7) safe rather than a source of
duplicate/conflicting problem records.

- **Rule 1:** Create POC in a section → immediately appears in Master POC
  (Section 11).
- **Rule 2:** Update POC in a section → immediately updates Master POC.
- **Rule 3:** Update POC in Master POC → immediately updates the
  originating section.
- **Rule 4:** There is only ONE Problem, ONE Goal Set, and ONE Intervention
  Set for each problem. No duplicates. (This is why Section 6 — Disease
  Specific Criteria — must "Link To Existing Problem" rather than create a
  new one, and why Section 7 — HOPE — only updates existing
  symptom-related problems.)
- **Rule 5:** Master POC (Section 11) is a synchronized *view*. It is not a
  separate database/table from the per-section POC entries.

**Origin Metadata Requirement.** Every Problem must store: Originating
Section, Originating Finding(s), Created By, Created Date, Last Updated By,
Last Updated Date, Status (Active / Resolved / Inactive), Related Action
Center Requests, Related Narrative References. This makes survey review,
audit review, recertification review, and interdisciplinary review much
easier, because every care-plan item can be traced back to the assessment
evidence that generated it. (This is additive to, and consistent with, the
Master Plan of Care Governance Rule in `SNS_POC_GENERATION_MATRIX_1.0.md`
§7.12.)

**POC Evidence Requirement.** Every POC problem shall contain at least one
linked assessment finding as its source evidence. Examples:

```
Problem: Impaired Breathing Pattern
Source Evidence: Respiratory Assessment —
  Dyspnea: Moderate
  Oxygen: 2L NC
  Pulse Ox: 88%

Problem: Nutrition Deficit
Source Evidence:
  Weight Loss: 15 lbs
  Appetite: Poor
  Intake: 25%
```

Rules:
- A problem cannot exist without linked evidence.
- Assessment findings remain the authoritative source.
- POC records must be traceable back to assessment findings.
- Section 11 displays source evidence links alongside each problem.

Benefits: Survey Readiness, Audit Readiness, Recertification Review, IDG
Review, Narrative Support, LCD Support. This supports documentation that
demonstrates functional decline, symptom burden, disease progression,
nutritional decline, recurrent complications, and patient-specific evidence
— rather than unsupported conclusions.

**GitHub one-sentence build rule:** Every RNICA section capable of
identifying a clinical problem shall contain `Add To POC`, `View POC`, and
`Update POC` controls. All changes synchronize bidirectionally with a
single Master Plan of Care. Section 11 serves as Master Plan of Care Review
and Governance, not the primary point of problem creation.

**Master Synchronization Rule diagram:**

```
Section Creates Problem
  ↓
Problem Added To Master POC
  ↓
Update In Section
  ↓
Updates Master POC
  ↓
Update In Master POC
  ↓
Updates Originating Section
```

There is only ONE Problem, ONE Goal Set, ONE Intervention Set, and ONE
Master Plan of Care. No duplicates.

This is the most nurse-friendly architecture because it follows the natural
workflow — Find problem → Create/Update POC immediately → Continue
assessment → Review all POCs at the end → Finalize — instead of forcing
nurses to rediscover every problem at the end of a long assessment. This
also keeps the assessment and plan-of-care relationship consistent with
California hospice requirements that the comprehensive assessment drives an
individualized plan of care.

---

## Admission Action Center (NOT an RNICA section — global)

Available from every screen. Not gated behind, or sequenced within, any
numbered section above.

**Contains:** Medication Requests, Physician Orders, DME Orders, Supply
Orders, Oxygen Orders, Lab Requests, Treatment Orders, Diet Orders,
Referrals, Physician Contact, Office Communication.

---

## Dependency Flow (Documentation Chain)

```
Assessment
  ↓
Clinical Findings
  ↓
Problem Generation
  ↓
Goal Generation
  ↓
Intervention Generation
  ↓
Discipline Assignment
  ↓
Frequency Assignment
  ↓
Master Plan of Care
  ↓
Narrative
  ↓
Finalization
```

Problems are created inside Sections 2-9, at their point of origin — not
after the Narrative. Narrative (Section 10) references the existing Master
Plan of Care; it does not create it. This reflects the per-section POC
model in `SNS_POC_GENERATION_MATRIX_1.0.md` §7 and supersedes the earlier
draft's HOPE→Narrative→Problem Generation ordering.

## Parallel Workflow (Never Blocking)

```
Assessment
  ↓
Need Identified
  ↓
Admission Action Center
  ↓
Medication / DME / Supplies / Referrals / Physician Contact
```

This parallel path never waits on the documentation chain above completing
(per `SNS_DESIGN_SYSTEM_1.0.md` §2.1 Patient Comfort Before Documentation
Completion).

---

## Status / Next Steps

**SNS RNICA Master Map 1.0 — STATUS: APPROVED FOR GOVERNANCE REVIEW.
Architecture Complete. No Further Architecture Work Required.** This map,
together with `SNS_DESIGN_SYSTEM_1.0.md` and
`SNS_POC_GENERATION_MATRIX_1.0.md`, forms the authoritative RNICA
architecture, POC architecture, and synchronization model for RNICA Pilot
Build 1.0 — see the **Governance Freeze** at the top of this document for
what is now locked pending a Version 1.1 revision cycle. It aligns with
the California hospice assessment-to-plan-of-care framework and CMS LCD
expectations for documenting decline, functional status, symptoms, disease
progression, and patient-specific evidence supporting terminal prognosis,
while ensuring the plan remains traceable back to documented clinical
evidence (§ POC Evidence Requirement above).

**Next Deliverable:** `SNS_RNICA_SECTION_INVENTORY_1.0`. Required
deliverables:

1. Field Inventory
2. Database Mapping
3. API Mapping
4. Validation Inventory
5. Narrative Source Inventory
6. HOPE Crosswalk
7. Audit Crosswalk
8. Action Center Trigger Inventory
9. POC Evidence Mapping
10. Migration Complexity Ratings

**Build Order (post-inventory):**

```
Phase 1 — Field Inventory
  ↓
Phase 2 — POC Generation Engine
  ↓
Phase 3 — Master POC Synchronization
  ↓
Phase 4 — RNICA UI Migration
  ↓
Phase 5 — HOPE Integration
  ↓
Phase 6 — Narrative Integration
  ↓
Phase 7 — Pilot Testing
```

No code changes are authorized by this document alone — implementation
requires a separate, explicit go-ahead (consistent with
`SNS_DESIGN_SYSTEM_1.0.md` §12 Governance). **No Code Changes Authorized
Without Separate Approval.**