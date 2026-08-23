# SNS RNICA Field Inventory 1.0 — Phase 1, Deliverable 1

## STATUS: FROZEN — ACCEPTED COMPLETE (2026-08-21)

This document is accepted as complete and is now frozen. No further
redesign, reordering, or restructuring of this document is authorized.
Corrections limited to factual errors (e.g., a mis-transcribed field
name) may still be made; scope, ordering, and structure may not.

## INVENTORY RULE

This document records the CURRENT RNICA system.

It is not a design document.
It is not a migration document.
It is not a Master Map document.

No inventory entry may be modified to match the target architecture.

Inventory records reality. Architecture records intent.

We are NOT building. We are NOT redesigning. We are NOT mapping to the
Master Map. This is a complete census of the current RNICA assessment,
nothing else.

Status: In progress — read-only inventory, no code changes made in
producing this document.

Source of truth: **Current RNICA HOPE Assessment Screen**, as coded in
`sns-emr-frontend/src/components/RNICA.jsx` (SIDEBAR_CONFIG + default
form-data shape).

## Columns

Current Section | Current Subsection | Current Field Name | Current Label
| Current Field Type | Current Options | Required / Optional | HOPE
Reference | Conditional Logic | Notes.

## Section order (as coded, `RNICA.jsx` SIDEBAR_CONFIG, top to bottom)

1. Patient Demographics
2. Vitals
3. Pain Assessment
4. Symptom Impact
5. Diagnoses
6. Performance Status
7. Neurological
8. Cardiovascular
9. Respiratory
10. Infection
11. Gastrointestinal
12. Nutrition
13. Endocrine
14. Genitourinary
15. Musculoskeletal
16. Skin / Wounds
17. Imminent Death
18. SFV
19. Safety
20. Psychosocial
21. Spiritual
22. Bereavement
23. Personal Care
24. Teaching Needs
25. Admissions Order
26. Hospice Orders Hub
27. Referrals
28. Finalization

No code changes are authorized by this document.

---

## 1. Patient Demographics

Source: `RNICA.jsx:167` (nav), `RNICA.jsx:304-343` (form-data shape),
`RNICA.jsx:771-818` (validation).

### Subsection: Core Demographics

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `demographics.firstName` | First Name | text | free text | Required | — | — | |
| `demographics.lastName` | Last Name | text | free text | Required | — | — | |
| `demographics.dob` | Date of Birth | date | date | Required | — | — | |
| `demographics.gender` | Gender | select | facility list | Required | — | — | |
| `demographics.race[]` | Race | multi-select | facility list | Optional | A1010 | Warning if empty | |
| `demographics.ethnicity[]` | Ethnicity | multi-select | facility list | Optional | A1005 | Warning if empty | |
| `demographics.preferredLanguage` | Preferred Language | select | facility list | Optional | A1110 | Warning if empty | |
| `demographics.needsInterpreter` | Needs Interpreter | boolean | Y/N | Optional | — | — | |
| `demographics.religion` | Religion | text/select | free text | Optional | — | — | |
| `demographics.maritalStatus` | Marital Status | select | facility list | Optional | — | — | |
| `demographics.militaryService` | Military Service | select | facility list | Optional | — | — | |
| `demographics.phone` | Phone | text | phone format | Optional | — | — | |
| `demographics.alternatePhone` | Alternate Phone | text | phone format | Optional | — | — | |

### Subsection: Address

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `demographics.address.street` | Street | text | free text | Optional | — | — | |
| `demographics.address.city` | City | text | free text | Optional | — | — | |
| `demographics.address.state` | State | select | US states | Optional | — | — | |
| `demographics.address.zip` | Zip | text | zip format | Optional | — | — | |
| `demographics.address.county` | County | text | free text | Optional | — | — | |

### Subsection: Emergency Contact

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `demographics.emergencyContact.name` | Name | text | free text | Optional | — | — | |
| `demographics.emergencyContact.relationship` | Relationship | text/select | facility list | Optional | — | — | |
| `demographics.emergencyContact.phone` | Phone | text | phone format | Optional | — | — | |

### Subsection: Primary Caregiver (PCG)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `demographics.pcg.assessed` | Caregiver Assessed This Visit | boolean | Y/N | Optional | — | Warning if unanswered | code comment: distinguishes "confirmed Yes/No" from "not yet asked" |
| `demographics.pcg.noPcg` | No PCG | boolean | Y/N | Optional | — | — | |
| `demographics.pcg.name` | Name | text | free text | Optional | — | — | |
| `demographics.pcg.relationship` | Relationship | text/select | facility list | Optional | — | — | |
| `demographics.pcg.phone` | Phone | text | phone format | Optional | — | — | |
| `demographics.pcg.healthStatus` | Health Status | select | facility list | Optional | — | — | |
| `demographics.pcg.anxietyLevel` | Anxiety Level | select | facility list | Optional | — | — | |
| `demographics.pcg.ableToAdministerMeds` | Able to Administer Meds | select | facility list | Conditional | — | Required (CDPH) if PCG present | |
| `demographics.pcg.willingToProvideCare` | Willing to Provide Care | select | facility list | Conditional | — | Required (CDPH) if PCG present | |
| `demographics.pcg.pcgConcerns` | PCG Concerns | textarea | free text | Optional | — | — | |

### Subsection: CDPH Caregiver Evaluation (nested under PCG)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `demographics.pcg.caregiverEvaluation.physicalAbility` | Physical Ability | select | facility list | Optional | — | — | |
| `demographics.pcg.caregiverEvaluation.cognitiveAbility` | Cognitive Ability | select | facility list | Optional | — | — | |
| `demographics.pcg.caregiverEvaluation.emotionalReadiness` | Emotional Readiness | select | facility list | Optional | — | — | |
| `demographics.pcg.caregiverEvaluation.availabilityForCare` | Availability For Care | select | facility list | Optional | — | — | |
| `demographics.pcg.caregiverEvaluation.trainingNeeds[]` | Training Needs | multi-select | facility list | Optional | — | — | |
| `demographics.pcg.caregiverEvaluation.willingnessScore` | Willingness Score | select/number | facility scale | Conditional | — | Required (CDPH) if PCG present | |
| `demographics.pcg.caregiverEvaluation.capabilityScore` | Capability Score | select/number | facility scale | Conditional | — | Required (CDPH) if PCG present | |
| `demographics.pcg.caregiverEvaluation.supportSystemAdequacy` | Support System Adequacy | select | facility list | Optional | — | — | |
| `demographics.pcg.caregiverEvaluation.evaluationNotes` | Evaluation Notes | textarea | free text | Optional | — | — | |

### Subsection: Living Situation

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `demographics.livingSituation.siteOfService` | Site of Service | select | facility list | Optional | — | — | |
| `demographics.livingSituation.admittedFrom` | Admitted From | select | facility list | Optional | — | — | |
| `demographics.livingSituation.livingArrangement` | Living Arrangement | select | facility list | Optional | — | — | |
| `demographics.livingSituation.availabilityOfAssistance` | Availability of Assistance | select | facility list | Optional | — | — | |

### Subsection: Advanced Care Planning

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `demographics.advancedCarePlanning.codeStatus` | Code Status | select | facility list | Required | F2000 | — | |
| `demographics.advancedCarePlanning.codeStatusDate` | Code Status Date | date | date | Optional | — | — | |
| `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference` | Life-Sustaining Treatment Preference | select | facility list | Required | F2100 | — | |
| `demographics.advancedCarePlanning.lifeSustainingTreatmentPreferenceDate` | Life-Sustaining Treatment Preference Date | date | date | Optional | — | — | |
| `demographics.advancedCarePlanning.hospitalizationPreference` | Hospitalization Preference | select | facility list | Required | F2200 | — | |
| `demographics.advancedCarePlanning.hospitalizationPreferenceDate` | Hospitalization Preference Date | date | date | Optional | — | — | |
| `demographics.advancedCarePlanning.decisionMaker` | Decision Maker | text | free text | Optional | — | — | |
| `demographics.advancedCarePlanning.poaName` | POA Name | text | free text | Optional | — | — | |
| `demographics.advancedCarePlanning.poaPhone` | POA Phone | text | phone format | Optional | — | — | |
| `demographics.advancedCarePlanning.advanceDirectiveOnFile` | Advance Directive On File | boolean | Y/N | Optional | — | — | |
| `demographics.advancedCarePlanning.polstOnFile` | POLST On File | boolean | Y/N | Optional | — | — | |

---

## 2. Vitals

Source: `RNICA.jsx:168` (nav), `RNICA.jsx:346-358` (form-data shape).

### Subsection: Vital Signs

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `vitals.temperature` | Temperature | number | numeric | Optional | — | — | |
| `vitals.temperatureUnit` | Temperature Unit | select | F/C | Optional | — | — | |
| `vitals.pulse` | Pulse | number | numeric | Optional | — | — | |
| `vitals.pulseQuality` | Pulse Quality | select | facility list | Optional | — | — | |
| `vitals.pulseRhythm` | Pulse Rhythm | select | facility list | Optional | — | — | |
| `vitals.respirations` | Respirations | number | numeric | Optional | — | — | |
| `vitals.respirationPattern` | Respiration Pattern | select | facility list | Optional | — | — | |
| `vitals.bloodPressure.systolic` | Blood Pressure — Systolic | number | numeric | Optional | — | — | |
| `vitals.bloodPressure.diastolic` | Blood Pressure — Diastolic | number | numeric | Optional | — | — | |
| `vitals.bloodPressure.position` | Blood Pressure — Position | select | facility list | Optional | — | — | |
| `vitals.height` | Height | number | numeric | Optional | — | — | |
| `vitals.heightUnit` | Height Unit | select | in/cm | Optional | — | — | |
| `vitals.weight` | Weight | number | numeric | Optional | — | — | |
| `vitals.weightUnit` | Weight Unit | select | lbs/kg | Optional | — | — | |
| `vitals.bmi` | BMI | number (computed) | numeric | Optional | — | — | |
| `vitals.mac` | MAC (Mid-Arm Circumference) | number | numeric | Optional | — | — | |
| `vitals.oxygenSaturation` | Oxygen Saturation | number | numeric (%) | Optional | — | — | |
| `vitals.oxygenSaturationOnRA` | Oxygen Saturation on Room Air | boolean | Y/N | Optional | — | — | |

### Subsection: IV Assessment (nested under Vitals)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `vitals.ivAssessment.hasIV` | Has IV | boolean | Y/N | Optional | — | — | |
| `vitals.ivAssessment.type` | Type | select | facility list | Conditional | — | Shown if Has IV | |
| `vitals.ivAssessment.size` | Size | select | facility list | Conditional | — | Shown if Has IV | |
| `vitals.ivAssessment.site` | Site | select | facility list | Conditional | — | Shown if Has IV | |
| `vitals.ivAssessment.dressingType` | Dressing Type | select | facility list | Conditional | — | Shown if Has IV | |
| `vitals.ivAssessment.insertionDate` | Insertion Date | date | date | Conditional | — | Shown if Has IV | |
| `vitals.ivAssessment.lastChangeDate` | Last Change Date | date | date | Conditional | — | Shown if Has IV | |
| `vitals.ivAssessment.condition` | Condition | select | facility list | Conditional | — | Shown if Has IV | |
| `vitals.ivAssessment.flushSchedule` | Flush Schedule | select/text | facility list | Conditional | — | Shown if Has IV | |
| `vitals.ivAssessment.notes` | Notes | textarea | free text | Optional | — | — | |

Note (as-coded, not a mapping judgment): `ivAssessment` is a nested field
group inside the `vitals` form-data object, not a separate top-level
SIDEBAR_CONFIG entry.

---

## 3. Pain Assessment

Source: `RNICA.jsx:169` (nav, `hope: ["J0900","J0915"]`), `RNICA.jsx:360-381`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `pain.verbalizesPain` | Verbalizes Pain | select | Y/N/Unable | Optional | — | — | |
| `pain.uncomfortableBecauseOfPain` | Uncomfortable Because of Pain | select | Y/N/Unable | Optional | — | — | |
| `pain.neuropathicPain` | Neuropathic Pain | boolean | Y/N | Optional | — | — | |
| `pain.screeningDate` | Screening Date | date | date | Optional | J0900 | — | |
| `pain.comprehensiveAssessmentCompleted` | Comprehensive Assessment Completed | boolean | Y/N | Conditional | J0910 | Shown if pain present | |
| `pain.comprehensiveAssessmentDate` | Comprehensive Assessment Date | date | date | Conditional | — | Shown if assessment completed | |
| `pain.assessmentTool` | Assessment Tool | select | facility list | Conditional | — | Shown if assessment completed | |
| `pain.painIntensity.current` | Pain Intensity — Current | number/scale | 0-10 | Conditional | — | Shown if pain present | |
| `pain.painIntensity.worst` | Pain Intensity — Worst | number/scale | 0-10 | Optional | — | — | |
| `pain.painIntensity.best` | Pain Intensity — Best | number/scale | 0-10 | Optional | — | — | |
| `pain.painIntensity.acceptable` | Pain Intensity — Acceptable | number/scale | 0-10 | Optional | — | — | |
| `pain.painLocation[]` | Pain Location | multi-select | body-site list | Optional | — | — | |
| `pain.painCharacter[]` | Pain Character | multi-select | facility list | Optional | — | — | |
| `pain.painRadiation` | Pain Radiation | text | free text | Optional | — | — | |
| `pain.painBodySites[]` | Pain Body Sites | multi-select (map) | body-map coordinates | Optional | — | — | |
| `pain.painMapMode` | Pain Map Mode | toggle | verbal/map | Optional | — | — | |
| `pain.aggravatingFactors[]` | Aggravating Factors | multi-select | facility list | Optional | — | — | |
| `pain.relievingFactors[]` | Relieving Factors | multi-select | facility list | Optional | — | — | |
| `pain.painManagementPlan` | Pain Management Plan | textarea | free text | Optional | J0915 | — | |
| `pain.flacc.face` | FLACC — Face | select | 0-2 scale | Conditional | — | Non-verbal patient | |
| `pain.flacc.legs` | FLACC — Legs | select | 0-2 scale | Conditional | — | Non-verbal patient | |
| `pain.flacc.activity` | FLACC — Activity | select | 0-2 scale | Conditional | — | Non-verbal patient | |
| `pain.flacc.cry` | FLACC — Cry | select | 0-2 scale | Conditional | — | Non-verbal patient | |
| `pain.flacc.consolability` | FLACC — Consolability | select | 0-2 scale | Conditional | — | Non-verbal patient | |
| `pain.flacc.total` | FLACC — Total | number (computed) | 0-10 | Optional | — | — | |
| `pain.painad.breathing` | PAINAD — Breathing | select | 0-2 scale | Conditional | — | Non-verbal patient | |
| `pain.painad.vocalization` | PAINAD — Vocalization | select | 0-2 scale | Conditional | — | Non-verbal patient | |
| `pain.painad.facialExpression` | PAINAD — Facial Expression | select | 0-2 scale | Conditional | — | Non-verbal patient | |
| `pain.painad.bodyLanguage` | PAINAD — Body Language | select | 0-2 scale | Conditional | — | Non-verbal patient | |
| `pain.painad.consolability` | PAINAD — Consolability | select | 0-2 scale | Conditional | — | Non-verbal patient | |
| `pain.painad.total` | PAINAD — Total | number (computed) | 0-10 | Optional | — | — | |
| `pain.nonPharmInterventions[]` | Non-Pharmacological Interventions | multi-select | facility list | Optional | — | — | |

---

## 4. Symptom Impact

Source: `RNICA.jsx:170` (nav, `hope: ["J2051"]`), `RNICA.jsx:384-389`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `symptomImpact.pain` | Pain | select/scale | facility scale | Optional | — | — | |
| `symptomImpact.shortnessOfBreath` | Shortness of Breath | select/scale | facility scale | Optional | — | — | |
| `symptomImpact.anxiety` | Anxiety | select/scale | facility scale | Optional | — | — | |
| `symptomImpact.nausea` | Nausea | select/scale | facility scale | Optional | — | — | |
| `symptomImpact.vomiting` | Vomiting | select/scale | facility scale | Optional | — | — | |
| `symptomImpact.diarrhea` | Diarrhea | select/scale | facility scale | Optional | — | — | |
| `symptomImpact.constipation` | Constipation | select/scale | facility scale | Optional | — | — | |
| `symptomImpact.agitation` | Agitation | select/scale | facility scale | Optional | — | — | |
| `symptomImpact.totalScore` | Total Score | number (computed) | numeric | Optional | J2051 | — | |
| `symptomImpact.assessmentDate` | Assessment Date | date | date | Optional | — | — | |

---

## 5. Diagnoses

Source: `RNICA.jsx:171` (nav, `hope: ["I0010","J0050"]`), `RNICA.jsx:392-426`.

### Subsection: Primary / Secondary Diagnosis

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `diagnoses.primaryDiagnosis.icd10` | Primary Diagnosis — ICD-10 | text/lookup | ICD-10 codes | Required | I0010 | — | |
| `diagnoses.primaryDiagnosis.description` | Primary Diagnosis — Description | text | free text | Required | — | Auto-filled from lookup | |
| `diagnoses.primaryDiagnosis.onsetDate` | Primary Diagnosis — Onset Date | date | date | Optional | — | — | |
| `diagnoses.secondaryDiagnoses[]` | Secondary Diagnoses | multi-entry (list) | ICD-10 codes | Optional | — | — | |
| `diagnoses.comorbidities[]` | Comorbidities | multi-entry (list) | ICD-10 codes | Optional | — | — | |

### Subsection: Prognosis / Trajectory

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `diagnoses.terminalPrognosis` | Terminal Prognosis | textarea | free text | Optional | J0050 | — | |
| `diagnoses.diseaseTrajectory` | Disease Trajectory | textarea | free text | Optional | — | — | |
| `diagnoses.lcdEligibilityNarrative` | LCD Eligibility Narrative | textarea (custom renderer) | free text | Optional | — | — | |

### Subsection: NDS Eligibility (nested under Diagnoses)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `diagnoses.ndsEligibility.detectedDisease` | Detected Disease | text/derived | facility disease list | Optional | — | — | |
| `diagnoses.ndsEligibility.criteriaAnswers{}` | Criteria Answers | object (dynamic) | per-disease criteria | Optional | — | — | |
| `diagnoses.ndsEligibility.criteriaFacts{}` | Criteria Facts | object (dynamic) | per-disease criteria | Optional | — | — | |

### Subsection: HOPE Comorbidities (nested under Diagnoses)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `diagnoses.hopeComorbidities.cancer` | Cancer | boolean | Y/N | Optional | I0100 | — | |
| `diagnoses.hopeComorbidities.heartFailure` | Heart Failure | boolean | Y/N | Optional | I0600 | — | |
| `diagnoses.hopeComorbidities.pvdPad` | PVD/PAD | boolean | Y/N | Optional | I0900 | — | |
| `diagnoses.hopeComorbidities.cardiovascularExclHF` | Cardiovascular (excl. HF) | boolean | Y/N | Optional | I0950 | — | |
| `diagnoses.hopeComorbidities.liverDisease` | Liver Disease | boolean | Y/N | Optional | I1101 | — | |
| `diagnoses.hopeComorbidities.renalDisease` | Renal Disease | boolean | Y/N | Optional | I1510 | — | |
| `diagnoses.hopeComorbidities.sepsis` | Sepsis | boolean | Y/N | Optional | I2102 | — | |
| `diagnoses.hopeComorbidities.diabetesMellitus` | Diabetes Mellitus | boolean | Y/N | Optional | I2900 | — | |
| `diagnoses.hopeComorbidities.neuropathy` | Neuropathy | boolean | Y/N | Optional | I2910 | — | |
| `diagnoses.hopeComorbidities.stroke` | Stroke | boolean | Y/N | Optional | I4501 | — | |
| `diagnoses.hopeComorbidities.dementia` | Dementia | boolean | Y/N | Optional | I4801 | — | |
| `diagnoses.hopeComorbidities.neurologicalConditions` | Neurological Conditions | boolean | Y/N | Optional | I5150 | — | |
| `diagnoses.hopeComorbidities.seizureDisorder` | Seizure Disorder | boolean | Y/N | Optional | I5401 | — | |
| `diagnoses.hopeComorbidities.copd` | COPD | boolean | Y/N | Optional | I6202 | — | |
| `diagnoses.hopeComorbidities.other` | Other | boolean | Y/N | Optional | — | — | |
| `diagnoses.hopeComorbidities.additionalNote` | Additional Note | textarea | free text | Optional | — | — | |

Note (code comment, recorded verbatim): manual overrides live here;
auto-detection from primary/secondary diagnosis happens in
`HopeComorbiditiesCard` and explicitly excludes any category already
represented by the Primary Diagnosis.

---

## 6. Performance Status

Source: `RNICA.jsx:172` (nav, `hope: ["M1190"]`), `RNICA.jsx:429-436`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `performanceStatus.pps` | PPS | select | PPS scale (0-100%, 10-pt increments) | Optional | M1190 | — | |
| `performanceStatus.ppsJustification` | PPS Justification | textarea | free text | Optional | — | — | |
| `performanceStatus.kps` | KPS | select | KPS scale | Optional | — | — | |
| `performanceStatus.kpsJustification` | KPS Justification | textarea | free text | Optional | — | — | |
| `performanceStatus.ecog` | ECOG | select | ECOG scale (0-4) | Optional | — | — | |
| `performanceStatus.ecogJustification` | ECOG Justification | textarea | free text | Optional | — | — | |
| `performanceStatus.fast` | FAST | select | FAST stage | Optional | — | — | |
| `performanceStatus.fastStage` | FAST Stage | select | FAST sub-stage | Optional | — | — | |
| `performanceStatus.nyha` | NYHA | select | NYHA Class I-IV | Optional | — | — | |
| `performanceStatus.nyhaJustification` | NYHA Justification | textarea | free text | Optional | — | — | |
| `performanceStatus.functionalDeclineNotes` | Functional Decline Notes | textarea | free text | Optional | — | — | |

Note (observation, not inventory entry): no "previous value" fields exist
in this section's form-data shape. A separate UI component
(`DeclineTrackerCard`, `RNICA.jsx:1990-2070`) computes PPS/KPS/FAST/Weight
trend comparisons at render time from historical records via
`fetchPerformanceHistory()`.

---

## 7. Neurological

Source: `RNICA.jsx:173` (nav, `hope: ["N0500","N0510","N0520"]`), `RNICA.jsx:439-452`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `neurological.consciousness` | Consciousness | select | facility list | Optional | — | — | |
| `neurological.orientation.time` | Orientation — Time | boolean | Y/N | Optional | — | — | |
| `neurological.orientation.place` | Orientation — Place | boolean | Y/N | Optional | — | — | |
| `neurological.orientation.person` | Orientation — Person | boolean | Y/N | Optional | — | — | |
| `neurological.orientation.situation` | Orientation — Situation | boolean | Y/N | Optional | — | — | |
| `neurological.communication` | Communication | select | facility list | Optional | — | — | |
| `neurological.hearing` | Hearing | select | facility list | Optional | — | — | |
| `neurological.vision` | Vision | select | facility list | Optional | — | — | |
| `neurological.balance` | Balance | select | facility list | Optional | — | — | |
| `neurological.cognition` | Cognition | select | facility list | Optional | — | — | |
| `neurological.delirium` | Delirium | boolean | Y/N | Optional | — | — | |
| `neurological.seizureHistory` | Seizure History | boolean | Y/N | Optional | — | — | |
| `neurological.psychiatricHistory` | Psychiatric History | text/select | free text | Optional | — | — | |
| `neurological.sensoryDeficits[]` | Sensory Deficits | multi-select | facility list | Optional | — | — | |
| `neurological.hopeItems.n0500` | HOPE N0500 | select | facility list | Optional | N0500 | — | |
| `neurological.hopeItems.n0510` | HOPE N0510 | select | facility list | Optional | N0510 | — | |
| `neurological.hopeItems.n0520` | HOPE N0520 | select | facility list | Optional | N0520 | — | |
| `neurological.notes` | Notes | textarea | free text | Optional | — | — | |

### Subsection: Sleep/Rest (nested under Neurological)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `neurological.sleepRest.sleepPattern` | Sleep Pattern | select | facility list | Optional | — | — | |
| `neurological.sleepRest.averageSleepHours` | Average Sleep Hours | number | numeric | Optional | — | — | |
| `neurological.sleepRest.sleepAids[]` | Sleep Aids | multi-select | facility list | Optional | — | — | |
| `neurological.sleepRest.restfulness` | Restfulness | select | facility list | Optional | — | — | |
| `neurological.sleepRest.notes` | Notes | textarea | free text | Optional | — | — | |

Note (as-coded): "Sleep Rest" is a nested field group inside the
`neurological` form-data object, not a separate top-level SIDEBAR_CONFIG
entry.

---

## 8. Cardiovascular

Source: `RNICA.jsx:174` (nav), `RNICA.jsx:455-462`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `cardiovascular.bpSymptoms[]` | BP Symptoms | multi-select | facility list | Optional | — | — | |
| `cardiovascular.pulseQuality` | Pulse Quality | select | facility list | Optional | — | — | |
| `cardiovascular.edema.present` | Edema — Present | select | Y/N | Optional | — | — | |
| `cardiovascular.edema.location[]` | Edema — Location | multi-select | body-site list | Conditional | — | Shown if edema present | |
| `cardiovascular.edema.severity` | Edema — Severity | select | facility scale | Conditional | — | Shown if edema present | |
| `cardiovascular.edema.pitting` | Edema — Pitting | select | facility list | Conditional | — | Shown if edema present | |
| `cardiovascular.chestPain.present` | Chest Pain — Present | select | Y/N | Optional | — | — | |
| `cardiovascular.chestPain.type` | Chest Pain — Type | select | facility list | Conditional | — | Shown if chest pain present | |
| `cardiovascular.chestPain.frequency` | Chest Pain — Frequency | select | facility list | Conditional | — | Shown if chest pain present | |
| `cardiovascular.peripheralCirculation` | Peripheral Circulation | select | facility list | Optional | — | — | |
| `cardiovascular.heartSounds` | Heart Sounds | select | facility list | Optional | — | — | |
| `cardiovascular.jvd` | JVD | select | facility list | Optional | — | — | |
| `cardiovascular.notes` | Notes | textarea | free text | Optional | — | — | |

---

## 9. Respiratory

Source: `RNICA.jsx:175` (nav), `RNICA.jsx:465-476`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `respiratory.sobSeverity` | Shortness of Breath Severity | select | facility scale | Optional | — | — | |
| `respiratory.exertionLevel` | Exertion Level | select | facility list | Optional | — | — | |
| `respiratory.shortnessOfBreathScreened` | Shortness of Breath Screened | boolean | Y/N | Optional | — | — | |
| `respiratory.screeningDate` | Screening Date | date | date | Conditional | — | Shown if screened | |
| `respiratory.treatmentInitiated` | Treatment Initiated | boolean | Y/N | Optional | — | — | |
| `respiratory.treatmentDate` | Treatment Date | date | date | Conditional | — | Shown if treatment initiated | |
| `respiratory.lungSounds[]` | Lung Sounds | multi-select | facility list | Optional | — | — | |
| `respiratory.respirations[]` | Respirations | multi-select | facility list | Optional | — | — | |
| `respiratory.coughType` | Cough Type | select | facility list | Optional | — | — | |
| `respiratory.sputumCharacter` | Sputum Character | select | facility list | Optional | — | — | |
| `respiratory.notes` | Notes | textarea | free text | Optional | — | — | |

### Subsection: Oxygen Therapy (nested under Respiratory)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `respiratory.oxygenTherapy.inUse` | Oxygen In Use | boolean | Y/N | Optional | — | — | |
| `respiratory.oxygenTherapy.type` | Type | select | facility list | Conditional | — | Shown if in use | |
| `respiratory.oxygenTherapy.litersPerMinute` | Liters Per Minute | number | numeric | Conditional | — | Shown if in use | |
| `respiratory.oxygenTherapy.hoursPerDay` | Hours Per Day | number | numeric | Conditional | — | Shown if in use | |
| `respiratory.oxygenTherapy.satOnO2` | Saturation on O2 | number | numeric (%) | Conditional | — | Shown if in use | |

This section is flagged `sfv: true` in SIDEBAR_CONFIG (participates in
Symptom Follow-Up Visit flows) — recorded as-coded, no further
interpretation here.

---

## 10. Infection

Source: `RNICA.jsx:176` (nav), `RNICA.jsx:479-486`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `infection.allergies[]` | Allergies | multi-select/entry | free text list | Optional | — | — | |
| `infection.currentInfections[]` | Current Infections | multi-select/entry | free text list | Optional | — | — | |
| `infection.historyOfResistantInfections[]` | History of Resistant Infections | multi-select/entry | free text list | Optional | — | — | |
| `infection.immunosuppressed` | Immunosuppressed | boolean | Y/N | Optional | — | — | |
| `infection.precautions[]` | Precautions | multi-select | facility list | Optional | — | — | |
| `infection.notes` | Notes | textarea | free text | Optional | — | — | |

---

## 11. Gastrointestinal

Source: `RNICA.jsx:177` (nav), `RNICA.jsx:489-496`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `gastrointestinal.nausea` | Nausea | select | facility scale | Optional | — | — | |
| `gastrointestinal.vomiting` | Vomiting | select | facility scale | Optional | — | — | |
| `gastrointestinal.diarrhea` | Diarrhea | select | facility scale | Optional | — | — | |
| `gastrointestinal.constipation` | Constipation | select | facility scale | Optional | — | — | |
| `gastrointestinal.bowelSounds` | Bowel Sounds | select | facility list | Optional | — | — | |
| `gastrointestinal.abdomen` | Abdomen | select | facility list | Optional | — | — | |
| `gastrointestinal.bowelStatus` | Bowel Status | select | facility list | Optional | — | — | |
| `gastrointestinal.lastBM` | Last BM | date | date | Optional | — | — | |
| `gastrointestinal.continence` | Continence (Bowel) | select | facility list | Optional | — | — | |
| `gastrointestinal.notes` | Notes | textarea | free text | Optional | — | — | |

### Subsection: Feeding Tube (nested under Gastrointestinal)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `gastrointestinal.feedingTube.present` | Feeding Tube Present | boolean | Y/N | Optional | — | — | |
| `gastrointestinal.feedingTube.type` | Type | select | facility list | Conditional | — | Shown if present | |
| `gastrointestinal.feedingTube.site` | Site | select | facility list | Conditional | — | Shown if present | |

### Subsection: Ostomy (nested under Gastrointestinal)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `gastrointestinal.ostomy.present` | Ostomy Present | boolean | Y/N | Optional | — | — | |
| `gastrointestinal.ostomy.type` | Type | select | facility list | Conditional | — | Shown if present | |
| `gastrointestinal.ostomy.condition` | Condition | select | facility list | Conditional | — | Shown if present | |

This section is flagged `sfv: true` in SIDEBAR_CONFIG. `continence` here
covers bowel continence only, as coded.

---

## 12. Nutrition

Source: `RNICA.jsx:178` (nav), `RNICA.jsx:499-506`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `nutrition.weightLossPastSixMonths` | Weight Loss Past Six Months | select/number | facility list | Optional | — | — | |
| `nutrition.appetite` | Appetite | select | facility list | Optional | — | — | |
| `nutrition.dietType` | Diet Type | select | facility list | Optional | — | — | |
| `nutrition.fluidIntake` | Fluid Intake | select | facility list | Optional | — | — | |
| `nutrition.swallowingIssues[]` | Swallowing Issues | multi-select | facility list | Optional | — | — | |
| `nutrition.oralMucosa` | Oral Mucosa | select | facility list | Optional | — | — | |
| `nutrition.nutritionalSupplements` | Nutritional Supplements | text/select | free text | Optional | — | — | |
| `nutrition.notes` | Notes | textarea | free text | Optional | — | — | |

### Subsection: Dentures (nested under Nutrition)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `nutrition.dentures.upper` | Upper Dentures | boolean | Y/N | Optional | — | — | |
| `nutrition.dentures.lower` | Lower Dentures | boolean | Y/N | Optional | — | — | |
| `nutrition.dentures.condition` | Condition | select | facility list | Conditional | — | Shown if dentures present | |

---

## 13. Endocrine

Source: `RNICA.jsx:179` (nav), `RNICA.jsx:509-521`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `endocrine.thyroid.assessment` | Thyroid Assessment | select | facility list | Optional | — | — | |
| `endocrine.thyroid.notes` | Thyroid Notes | textarea | free text | Optional | — | — | |
| `endocrine.diabetes.type` | Diabetes Type | select | facility list | Optional | — | — | |
| `endocrine.diabetes.glucoseMonitoring` | Glucose Monitoring | select | facility list | Optional | — | — | |
| `endocrine.diabetes.lastHbA1c` | Last HbA1c | number | numeric | Optional | — | — | |
| `endocrine.diabetes.lastHbA1cDate` | Last HbA1c Date | date | date | Optional | — | — | |
| `endocrine.diabetes.insulinType` | Insulin Type | select | facility list | Optional | — | — | |
| `endocrine.diabetes.insulinDose` | Insulin Dose | text | free text | Optional | — | — | |
| `endocrine.diabetes.oralHypoglycemics[]` | Oral Hypoglycemics | multi-select | facility list | Optional | — | — | |
| `endocrine.endocrineSymptoms[]` | Endocrine Symptoms | multi-select | facility list (incl. Fatigue) | Optional | — | — | Fatigue is not a standalone field — only present as one checkbox option in this list |
| `endocrine.symptomSeverity{}` | Symptom Severity | object (dynamic) | per-symptom scale | Optional | — | — | |
| `endocrine.currentEndocrineMeds[]` | Current Endocrine Meds | multi-select/entry | free text list | Optional | — | — | |
| `endocrine.notes` | Notes | textarea | free text | Optional | — | — | |

---

## 14. Genitourinary

Source: `RNICA.jsx:180` (nav), `RNICA.jsx:524-535`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `genitourinary.urinaryStatus` | Urinary Status (Continence) | select | facility list | Optional | — | — | |
| `genitourinary.frequency` | Frequency | select | facility list | Optional | — | — | |
| `genitourinary.urineOutput` | Urine Output | select | facility list | Optional | — | — | |
| `genitourinary.twentyFourHourVolume` | 24-Hour Volume | number | numeric | Optional | — | — | |
| `genitourinary.bladderManagement[]` | Bladder Management | multi-select | facility list | Optional | — | — | |
| `genitourinary.notes` | Notes | textarea | free text | Optional | — | — | |

### Subsection: Catheter (nested under Genitourinary)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `genitourinary.catheter.present` | Catheter Present | boolean | Y/N | Optional | — | — | |
| `genitourinary.catheter.type` | Type | select | facility list | Conditional | — | Shown if present | |
| `genitourinary.catheter.size` | Size | select | facility list | Conditional | — | Shown if present | |
| `genitourinary.catheter.insertionDate` | Insertion Date | date | date | Conditional | — | Shown if present | |
| `genitourinary.catheter.lastChangeDate` | Last Change Date | date | date | Conditional | — | Shown if present | |
| `genitourinary.catheter.condition` | Condition | select | facility list | Conditional | — | Shown if present | |
| `genitourinary.catheter.urineCharacteristics[]` | Urine Characteristics | multi-select | facility list | Conditional | — | Shown if present | |

### Subsection: Reproductive (nested under Genitourinary)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `genitourinary.reproductive.concerns[]` | Concerns | multi-select | facility list | Optional | — | — | |
| `genitourinary.reproductive.notes` | Notes | textarea | free text | Optional | — | — | |

`urinaryStatus` here covers urinary continence, as coded.

---

## 15. Musculoskeletal

Source: `RNICA.jsx:181` (nav), `RNICA.jsx:538-555`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `musculoskeletal.weakness` | Weakness | select | facility scale | Optional | — | — | |
| `musculoskeletal.rigidity` | Rigidity | select | facility list | Optional | — | — | |
| `musculoskeletal.contractures` | Contractures | select | None/Mild/Moderate/Severe | Optional | — | — | |
| `musculoskeletal.contracturesLocation[]` | Contractures Location | multi-select | body-site list | Optional | — | — | code comment: added to match depth of sibling body-system findings (e.g. `cardiovascular.edema.location`) |
| `musculoskeletal.paralysis` | Paralysis | select | facility list | Optional | — | — | |
| `musculoskeletal.romLimitations[]` | ROM Limitations | multi-select | facility list | Optional | — | — | |
| `musculoskeletal.gait` | Gait | select | facility list | Optional | — | — | |
| `musculoskeletal.assistiveDevices[]` | Assistive Devices | multi-select | facility list | Optional | — | — | |
| `musculoskeletal.notes` | Notes | textarea | free text | Optional | — | — | |

### Subsection: Fall History (nested under Musculoskeletal)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `musculoskeletal.fallHistory.fallsLast90Days` | Falls Last 90 Days | select/number | facility list | Optional | — | — | |
| `musculoskeletal.fallHistory.fallInjuries` | Fall Injuries | select/text | facility list | Optional | — | — | |

### Subsection: Mobility (nested under Musculoskeletal)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `musculoskeletal.mobility.ambulatoryStatus` | Ambulatory Status | select | facility list | Optional | — | — | |
| `musculoskeletal.mobility.endurance` | Endurance | select | facility list | Optional | — | — | |
| `musculoskeletal.mobility.transferAbility` | Transfer Ability | select | facility list | Optional | — | — | |

### Subsection: ADL (nested under Musculoskeletal)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `musculoskeletal.adl.bathing` | Bathing | select | facility list | Optional | — | — | |
| `musculoskeletal.adl.dressing` | Dressing | select | facility list | Optional | — | — | |
| `musculoskeletal.adl.toileting` | Toileting | select | facility list | Optional | — | — | |
| `musculoskeletal.adl.transferring` | Transferring | select | facility list | Optional | — | — | |
| `musculoskeletal.adl.eating` | Eating | select | facility list | Optional | — | — | |
| `musculoskeletal.adl.grooming` | Grooming | select | facility list | Optional | — | — | |

Note (as-coded): Fall History, Mobility, and ADL are nested field groups
inside the `musculoskeletal` form-data object, not separate top-level
SIDEBAR_CONFIG entries. Fall-risk *assessment* fields
(`fallRiskAssessmentCompleted`, `fallRiskLevel`) are a distinct pair of
fields located in the separate `safety` section (see Section 19 below),
not here.

---

## 16. Skin / Wounds

Source: `RNICA.jsx:182` (nav, `hope: ["M1190"]`), `RNICA.jsx:558-570`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `skin.skinConditionsPresent` | Skin Conditions Present | boolean | Y/N | Optional | M1190 | — | |
| `skin.skinStatus[]` | Skin Status | multi-select | facility list | Optional | — | — | |
| `skin.skinTurgor` | Skin Turgor | select | facility list | Optional | — | — | |
| `skin.skinBodySites[]` | Skin Body Sites | multi-select (map) | body-map coordinates | Optional | — | — | |
| `skin.pressureInjuryRisk` | Pressure Injury Risk | select | facility scale | Optional | — | — | |
| `skin.wounds[]` | Wounds | multi-entry (list) | wound records | Optional | — | — | |
| `skin.woundImpairment` | Wound Impairment | select | facility list | Optional | — | — | |
| `skin.notes` | Notes | textarea | free text | Optional | — | — | |

### Subsection: Braden Scale (nested under Skin)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `skin.braden.sensoryPerception` | Sensory Perception | select | 1-4 scale | Optional | — | — | |
| `skin.braden.moisture` | Moisture | select | 1-4 scale | Optional | — | — | |
| `skin.braden.activity` | Activity | select | 1-4 scale | Optional | — | — | |
| `skin.braden.mobility` | Mobility | select | 1-4 scale | Optional | — | — | |
| `skin.braden.nutrition` | Nutrition | select | 1-4 scale | Optional | — | — | |
| `skin.braden.frictionShear` | Friction/Shear | select | 1-3 scale | Optional | — | — | |
| `skin.braden.total` | Total (computed) | number | numeric | Optional | — | — | |

---

## 17. Imminent Death

Source: `RNICA.jsx:183` (nav, `hope: ["J0050"]`), `RNICA.jsx:573-579`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `imminentDeath.appearsThreeDaysOrLess` | Appears Three Days or Less | select | Y/N/Unable to determine | Optional | J0050 | — | |
| `imminentDeath.indicators[]` | Indicators | multi-select | facility list | Optional | — | — | |
| `imminentDeath.comfortMeasuresInPlace` | Comfort Measures In Place | boolean | Y/N | Optional | — | — | |
| `imminentDeath.familyNotified` | Family Notified | boolean | Y/N | Optional | — | — | |
| `imminentDeath.notes` | Notes | textarea | free text | Optional | — | — | |

---

## 18. SFV (Symptom Follow-Up Visit)

Source: `RNICA.jsx:184` (nav, `hope: ["J2050","J2052","J2053"]`), `RNICA.jsx:582-594`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `sfv.symptomImpactScreeningCompleted` | Symptom Impact Screening Completed | boolean | Y/N | Optional | J2051 (screening logic) | — | |
| `sfv.symptomImpactScreeningDate` | Symptom Impact Screening Date | date | date | Conditional | — | Shown if screening completed | |
| `sfv.inPersonSfvCompleted` | In-Person SFV Completed | boolean | Y/N | Optional | J2050 | — | |
| `sfv.sfvDate` | SFV Date | date | date | Conditional | — | Shown if SFV completed | |
| `sfv.reasonNotCompleted` | Reason Not Completed | select/text | facility list | Conditional | J2052 | Shown if SFV not completed | |
| `sfv.findings` | Findings | textarea | free text | Conditional | — | Shown if SFV completed | |
| `sfv.triggeredSymptoms[]` | Triggered Symptoms | multi-select | facility list | Optional | J2053 | — | |
| `sfv.interventions[]` | Interventions | multi-select | facility list | Optional | — | — | |
| `sfv.notes` | Notes | textarea | free text | Optional | — | — | |

### Subsection: Symptom Impact at SFV (nested under SFV)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `sfv.symptomImpactAtSfv.pain` | Pain | select/scale | facility scale | Optional | — | — | |
| `sfv.symptomImpactAtSfv.shortnessOfBreath` | Shortness of Breath | select/scale | facility scale | Optional | — | — | |
| `sfv.symptomImpactAtSfv.anxiety` | Anxiety | select/scale | facility scale | Optional | — | — | |
| `sfv.symptomImpactAtSfv.nausea` | Nausea | select/scale | facility scale | Optional | — | — | |
| `sfv.symptomImpactAtSfv.vomiting` | Vomiting | select/scale | facility scale | Optional | — | — | |
| `sfv.symptomImpactAtSfv.diarrhea` | Diarrhea | select/scale | facility scale | Optional | — | — | |
| `sfv.symptomImpactAtSfv.constipation` | Constipation | select/scale | facility scale | Optional | — | — | |
| `sfv.symptomImpactAtSfv.agitation` | Agitation | select/scale | facility scale | Optional | — | — | |

HOPE reference codes for J2050/J2052/J2053 are recorded per the
SIDEBAR_CONFIG `hope` array attached to this section (`RNICA.jsx:220`);
exact field-to-code correspondence within the subsection is not verified
in the code beyond this array and should not be treated as confirmed
one-to-one mapping.

---

## 19. Safety

Source: `RNICA.jsx:185` (nav), `RNICA.jsx:597-608`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `safety.safetyAssessmentCompleted` | Safety Assessment Completed | boolean | Y/N | Optional | — | — | |
| `safety.homeEnvironment[]` | Home Environment | multi-select | facility list | Optional | — | — | |
| `safety.fallRiskAssessmentCompleted` | Fall Risk Assessment Completed | boolean | Y/N | Optional | — | — | |
| `safety.fallRiskLevel` | Fall Risk Level | select | facility scale | Conditional | — | Shown if assessment completed | |
| `safety.firearmInHome` | Firearm in Home | boolean | Y/N | Optional | — | — | |
| `safety.oxygenInUse` | Oxygen In Use | boolean | Y/N | Optional | — | — | |
| `safety.oxygenSafetyReviewed` | Oxygen Safety Reviewed | boolean | Y/N | Conditional | — | Shown if oxygen in use | |
| `safety.disasterLevel` | Disaster Level | select | facility list | Optional | — | — | |
| `safety.disasterLevelOneConditions[]` | Disaster Level One Conditions | multi-select | facility list | Conditional | — | Shown per disaster level | |
| `safety.disasterLevelTwoConditions[]` | Disaster Level Two Conditions | multi-select | facility list | Conditional | — | Shown per disaster level | |
| `safety.notes` | Notes | textarea | free text | Optional | — | — | |

Note (as-coded): Fall Risk Assessment fields live in this `safety`
section, separate from the Fall History fields nested under
`musculoskeletal` (Section 15).

---

## 20. Psychosocial

Source: `RNICA.jsx:186` (nav), `RNICA.jsx:611-621`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `psychosocial.familySocialSupport` | Family/Social Support | select | facility list | Optional | — | — | |
| `psychosocial.primarySupportPerson` | Primary Support Person | text | free text | Optional | — | — | |
| `psychosocial.supportRelationship` | Support Relationship | text/select | facility list | Optional | — | — | |
| `psychosocial.patientConcerns[]` | Patient Concerns | multi-select | facility list | Optional | — | — | |
| `psychosocial.caregiverFamilyConcerns[]` | Caregiver/Family Concerns | multi-select | facility list | Optional | — | — | |
| `psychosocial.distressRating` | Distress Rating | select/number | facility scale | Optional | — | — | |
| `psychosocial.psychosocialHistory[]` | Psychosocial History | multi-select | facility list | Optional | — | — | |
| `psychosocial.copingAssessment` | Coping Assessment | select | facility list | Optional | — | — | |
| `psychosocial.copingNotes` | Coping Notes | textarea | free text | Optional | — | — | |
| `psychosocial.interventionPlan[]` | Intervention Plan | multi-select | facility list | Optional | — | — | |
| `psychosocial.notes` | Notes | textarea | free text | Optional | — | — | |

Also registered as a secondary nav entry (`RNICA.jsx:223`) with
`parent: "assessment"`, `scrollTarget: "psychosocial"` — recorded
as-coded.

---

## 21. Spiritual

Source: `RNICA.jsx:187` (nav), `RNICA.jsx:624-635`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `spiritual.patientActiveInFaithTradition` | Patient Active in Faith Tradition | boolean | Y/N | Optional | — | — | |
| `spiritual.patientFaith` | Patient Faith | text/select | free text | Conditional | — | Shown if active in faith tradition | |
| `spiritual.caregiverActiveInFaithTradition` | Caregiver Active in Faith Tradition | boolean | Y/N | Optional | — | — | |
| `spiritual.caregiverFaith` | Caregiver Faith | text/select | free text | Conditional | — | Shown if active in faith tradition | |
| `spiritual.spiritualConcerns[]` | Spiritual Concerns | multi-select | facility list | Optional | — | — | |
| `spiritual.spiritualDistressRating` | Spiritual Distress Rating | select/number | facility scale | Optional | — | — | |
| `spiritual.concernsDiscussed` | Concerns Discussed | boolean | Y/N | Optional | — | — | |
| `spiritual.concernsDiscussedDate` | Concerns Discussed Date | date | date | Conditional | — | Shown if discussed | |
| `spiritual.chaplainNeeded` | Chaplain Needed | boolean | Y/N | Optional | — | — | |
| `spiritual.notes` | Notes | textarea | free text | Optional | — | — | |

Also registered as a secondary nav entry (`RNICA.jsx:224`) with
`parent: "assessment"`, `scrollTarget: "spiritual"` — recorded as-coded.
No field in this section's form-data shape maps to HOPE F3000; recorded
as an observation only, not a gap judgment (that comparison belongs to
Phase 4/Deliverable 9).

---

## 22. Bereavement

Source: `RNICA.jsx:188` (nav), `RNICA.jsx:638-645`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `bereavement.patientConcerns[]` | Patient Concerns | multi-select | facility list | Optional | — | — | |
| `bereavement.caregiverConcerns[]` | Caregiver Concerns | multi-select | facility list | Optional | — | — | |
| `bereavement.bereavementRisk` | Bereavement Risk | select | facility scale | Optional | — | — | |
| `bereavement.riskFactors[]` | Risk Factors | multi-select | facility list | Optional | — | — | |
| `bereavement.bereavementVisitNeeded` | Bereavement Visit Needed | boolean | Y/N | Optional | — | — | |
| `bereavement.notes` | Notes | textarea | free text | Optional | — | — | |

---

## 23. Personal Care

Source: `RNICA.jsx:189` (nav), `RNICA.jsx:648-657`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `personalCare.aideTasks[]` | Aide Tasks | multi-select | facility list | Optional | — | — | |
| `personalCare.volunteerServices[]` | Volunteer Services | multi-select | facility list | Optional | — | — | |
| `personalCare.communityResources[]` | Community Resources | multi-select | facility list | Optional | — | — | |
| `personalCare.equipmentSupplyNeeds[]` | Equipment/Supply Needs | multi-select | facility list | Optional | — | — | |
| `personalCare.notes` | Notes | textarea | free text | Optional | — | — | |

### Subsection: Aide Visit Preferences (nested under Personal Care)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `personalCare.aideVisitPreferences.frequency` | Frequency | select | facility list | Optional | — | — | |
| `personalCare.aideVisitPreferences.preferredTime` | Preferred Time | select | facility list | Optional | — | — | |
| `personalCare.aideVisitPreferences.duration` | Duration | select | facility list | Optional | — | — | |

---

## 24. Teaching Needs

Source: `RNICA.jsx:190` (nav), `RNICA.jsx:660-671`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `teachingNeeds.primaryLearner` | Primary Learner | select | facility list | Optional | — | — | |
| `teachingNeeds.learningStylePreference` | Learning Style Preference | select | facility list | Optional | — | — | |
| `teachingNeeds.barriersToLearning[]` | Barriers to Learning | multi-select | facility list | Optional | — | — | |
| `teachingNeeds.educationTopics[]` | Education Topics | multi-entry (list, default-seeded) | topic/taught/understood/returnDemo/na per row | Optional | — | — | seeded from `DEFAULT_EDUCATION_TOPICS` |
| `teachingNeeds.teachingMethods[]` | Teaching Methods | multi-select | facility list | Optional | — | — | |
| `teachingNeeds.patientFamilyResponse` | Patient/Family Response | select/text | facility list | Optional | — | — | |
| `teachingNeeds.followUpPlan` | Follow-Up Plan | textarea | free text | Optional | — | — | |
| `teachingNeeds.notes` | Notes | textarea | free text | Optional | — | — | |

---

## 25. Admissions Order

Source: `RNICA.jsx:191` (nav), `RNICA.jsx:674-691`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `admissionsOrder.admissionStatement` | Admission Statement | text (static/default) | fixed default text | N/A | — | — | pre-filled boilerplate physician verbal-order statement |
| `admissionsOrder.levelOfCare.level` | Level of Care — Level | select | facility list | Optional | — | — | |
| `admissionsOrder.levelOfCare.effectiveDate` | Level of Care — Effective Date | date | date | Optional | — | — | |
| `admissionsOrder.levelOfCare.justification` | Level of Care — Justification | textarea | free text | Optional | — | — | |
| `admissionsOrder.visitFrequency[]` | Visit Frequency | multi-entry (list, default-seeded) | per-discipline frequency | Optional | — | — | seeded from `DEFAULT_VISIT_DISCIPLINES` |
| `admissionsOrder.treatmentMedsOrderCompleted` | Treatment/Meds Order Completed | boolean | Y/N | Optional | — | — | |
| `admissionsOrder.nonCoveredItems[]` | Non-Covered Items | multi-select/entry | free text list | Optional | — | — | |

### Subsection: HA Assignment (nested under Admissions Order)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `admissionsOrder.haAssignment.assignedAide` | Assigned Aide | select | staff list | Optional | — | — | |
| `admissionsOrder.haAssignment.notApplicable` | Not Applicable | boolean | Y/N | Optional | — | — | |

### Subsection: Initial POC/IDG (nested under Admissions Order)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `admissionsOrder.initialPocIdg.created` | Created | boolean | Y/N | Optional | — | — | |
| `admissionsOrder.initialPocIdg.createdDate` | Created Date | date | date | Conditional | — | Shown if created | |
| `admissionsOrder.initialPocIdg.notes` | Notes (static/default) | text (static/default) | fixed default text | N/A | — | — | default text: "IDG should only be created after all problems identified during this Assessment have been added to Initial POC using the ADD ISSUE feature." |

### Subsection: TO Verification (nested under Admissions Order)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `admissionsOrder.toVerification.verbalOrderReadBack` | Verbal Order Read Back | boolean | Y/N | Optional | — | — | |
| `admissionsOrder.toVerification.verifiedBy` | Verified By | select/text | staff list | Optional | — | — | |
| `admissionsOrder.toVerification.prescriberContacted` | Prescriber Contacted | boolean | Y/N | Optional | — | — | |
| `admissionsOrder.toVerification.verificationTimestamp` | Verification Timestamp | datetime | datetime | Optional | — | — | |

---

## 26. Hospice Orders Hub

Source: `RNICA.jsx:193` (nav, `label: "Hospice Orders Hub"`, `formSection: "medications"`), `RNICA.jsx:694-701`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `medications.scheduledOpioid` | Scheduled Opioid | boolean | Y/N | Optional | — | — | recorded name only; N0500 series correspondence not verified for this field |
| `medications.scheduledOpioidDate` | Scheduled Opioid Date | date | date | Conditional | — | Shown if scheduled opioid | |
| `medications.prnOpioid` | PRN Opioid | boolean | Y/N | Optional | — | — | recorded name only; N0510 series correspondence not verified for this field |
| `medications.prnOpioidDate` | PRN Opioid Date | date | date | Conditional | — | Shown if PRN opioid | |
| `medications.bowelRegimen` | Bowel Regimen | boolean | Y/N | Optional | — | — | recorded name only; N0520 series correspondence not verified for this field |
| `medications.bowelRegimenDate` | Bowel Regimen Date | date | date | Conditional | — | Shown if bowel regimen | |
| `medications.currentMedications[]` | Current Medications | multi-entry (list) | medication records | Optional | — | — | |
| `medications.orders[]` | Orders | multi-entry (list) | order records (Medication/DME/Supply/Lab/Treatment/Diet) | Optional | — | — | order categories: `RNICA.jsx:2748-2753` |

### Subsection: Med Reconciliation (nested under Orders Hub)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `medications.medReconciliation.completed` | Completed | boolean | Y/N | Optional | — | — | |
| `medications.medReconciliation.completedDate` | Completed Date | date | date | Conditional | — | Shown if completed | |
| `medications.medReconciliation.completedBy` | Completed By | select/text | staff list | Conditional | — | Shown if completed | |

Note (as-coded): the SIDEBAR_CONFIG `key` for this nav entry is
`ordersHub`, but its `formSection` points to `medications` in the
form-data shape — recorded verbatim, no interpretation applied. "DME" is
not a separate top-level assessment field group; it appears only as one
of the order categories inside this Hub (`RNICA.jsx:2749`).

---

## 27. Referrals

Source: `RNICA.jsx:195` (nav), `RNICA.jsx:704-713`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `referrals.socialWork.referred` | Social Work — Referred | boolean | Y/N | Optional | — | — | |
| `referrals.socialWork.reason` | Social Work — Reason | textarea | free text | Conditional | — | Shown if referred | |
| `referrals.socialWork.urgency` | Social Work — Urgency | select | facility list | Conditional | — | Shown if referred | |
| `referrals.spiritualCare.referred` | Spiritual Care — Referred | boolean | Y/N | Optional | — | — | |
| `referrals.spiritualCare.reason` | Spiritual Care — Reason | textarea | free text | Conditional | — | Shown if referred | |
| `referrals.spiritualCare.urgency` | Spiritual Care — Urgency | select | facility list | Conditional | — | Shown if referred | |
| `referrals.volunteer.referred` | Volunteer — Referred | boolean | Y/N | Optional | — | — | |
| `referrals.volunteer.type` | Volunteer — Type | select | facility list | Conditional | — | Shown if referred | |
| `referrals.volunteer.urgency` | Volunteer — Urgency | select | facility list | Conditional | — | Shown if referred | |
| `referrals.therapy[]` | Therapy | multi-entry (list) | referral records | Optional | — | — | |
| `referrals.dietitian.referred` | Dietitian — Referred | boolean | Y/N | Optional | — | — | |
| `referrals.dietitian.reason` | Dietitian — Reason | textarea | free text | Conditional | — | Shown if referred | |
| `referrals.pharmacist.referred` | Pharmacist — Referred | boolean | Y/N | Optional | — | — | |
| `referrals.pharmacist.reason` | Pharmacist — Reason | textarea | free text | Conditional | — | Shown if referred | |
| `referrals.other[]` | Other | multi-entry (list) | referral records | Optional | — | — | |
| `referrals.notes` | Notes | textarea | free text | Optional | — | — | |

---

## 28. Finalization

Source: `RNICA.jsx:196` (nav, `hope: ["F2000","F2100","F2200"]`), `RNICA.jsx:716-740`.

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `finalization.completedSections[]` | Completed Sections | array (computed/tracked) | section-key list | N/A | — | — | |
| `finalization.incompleteCount` | Incomplete Count | number (computed) | numeric | N/A | — | — | |
| `finalization.pocEntries[]` | POC Entries | multi-entry (list) | problem/goal/intervention/discipline records | Optional | — | — | |
| `finalization.pocDraft.problem` | POC Draft — Problem | text | free text | N | — | — | |
| `finalization.pocDraft.goal` | POC Draft — Goal | text | free text | N | — | — | |
| `finalization.pocDraft.intervention` | POC Draft — Intervention | text | free text | N | — | — | |
| `finalization.pocDraft.discipline` | POC Draft — Discipline | select | facility list | N | — | — | |
| `finalization.pocGenerationCompleted` | POC Generation Completed | boolean | Y/N | Optional | — | — | |
| `finalization.pocReviewedWithIdg` | POC Reviewed with IDG | boolean | Y/N | Optional | — | — | |
| `finalization.signatureCertification` | Signature Certification | boolean | Y/N | Required (to finalize) | — | — | |
| `finalization.clinicianSignature` | Clinician Signature | text | free text | Required (to finalize) | — | — | |
| `finalization.signatureDate` | Signature Date | date | date | Required (to finalize) | — | — | |
| `finalization.hopeSubmissionNumber` | HOPE Submission Number | text | free text | Optional | — | — | |
| `finalization.hopeAlreadySubmitted` | HOPE Already Submitted | boolean | Y/N | Optional | — | — | |
| `finalization.assessmentLocked` | Assessment Locked | boolean | Y/N | N/A | — | — | |
| `finalization.lockedTimestamp` | Locked Timestamp | datetime | datetime | N/A | — | — | |

### Subsection: Response to Interventions (nested under Finalization)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `finalization.responseToInterventions.initialResponseSummary` | Initial Response Summary | textarea | free text | Optional | — | — | |
| `finalization.responseToInterventions.interventionEffectiveness[]` | Intervention Effectiveness | multi-select | facility list | Optional | — | — | |
| `finalization.responseToInterventions.baselineEstablished` | Baseline Established | boolean | Y/N | Optional | — | — | |
| `finalization.responseToInterventions.baselineDate` | Baseline Date | date | date | Conditional | — | Shown if baseline established | |
| `finalization.responseToInterventions.progressNotes` | Progress Notes | textarea | free text | Optional | — | — | |

### Subsection: Supervisor Review (nested under Finalization)

| Field Name | Label | Type | Options | Required/Optional | HOPE Reference | Conditional Logic | Notes |
|---|---|---|---|---|---|---|---|
| `finalization.supervisorReview.required` | Required | boolean | Y/N | N/A | — | — | |
| `finalization.supervisorReview.reviewedBy` | Reviewed By | select/text | staff list | Conditional | — | Shown if required | |
| `finalization.supervisorReview.reviewDate` | Review Date | date | date | Conditional | — | Shown if required | |

Code comments (recorded verbatim, not interpreted): `pocEntries` /
`pocDraft` are tagged as addressing a prior gap item ("POC
Auto-Generation"); `responseToInterventions` is tagged as addressing a
prior gap item ("Response to Interventions"). Both are recorded here only
as existing fields, per the current-state-only rule.

---

## Status

**All 28 sections complete** (Patient Demographics through Finalization),
in exact current-code order, per `RNICA.jsx` SIDEBAR_CONFIG and default
form-data shape. This is a field-name/type/options/required/HOPE-
reference/conditional-logic/notes census of the current RNICA HOPE
Admission Assessment screen — no Master Map mapping, no reorganization,
no POC content.

`SNS_RNICA_FIELD_INVENTORY_1.0` — Deliverable 1 — **Complete.**

Next, per the Phase 1 sequence: Deliverable 2 —
`SNS_RNICA_DATABASE_MAPPING_1.0` (Field → Table → Column →
Relationships), pending explicit direction to proceed.

No code changes are authorized by this document.
