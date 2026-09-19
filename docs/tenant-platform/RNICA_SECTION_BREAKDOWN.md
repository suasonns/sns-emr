# RNICA Section Breakdown

**STATUS: DISCOVERY ONLY — NO REDESIGN — NO CODE — NO SCHEMA — NO MIGRATIONS**

This document is the exact RNICA content model, section by section, built
from direct inspection of `sns-emr-frontend/src/components/RNICA.jsx`
(11,507 lines), `sns-emr-frontend/src/config/bodySystems.js`, and the
backend validation/finalization/intelligence services. It supersedes
nothing in `RNICA_SYSTEM_DEPENDENCY_MAP.md`, `RNICA_UI_DEPENDENCY_MAP.md`,
`RNICA_REDESIGN_IMPACT_ANALYSIS.md`, `RNICA_USABILITY_AND_AI_REVIEW.md`,
`RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`, or `AI_VISIBILITY_MATRIX.md` — it
is a finer-grained, field-level companion to those documents.

> **ARCHITECTURAL CORRECTION NOTICE — see `RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`:**
> The Owner has locked a product decision that `diagnoses.clinicalNarrative`
> (documented under Section 10 — Diagnoses below) was incorrectly placed and
> must not remain a nurse-facing narrative input. `finalization.clinicalNarrative`
> (Section 27 — Finalization) is the sole authoritative future Clinical
> Narrative. The field inventory below still reflects the current repository
> state and is unchanged.

**Common mechanisms that apply to every section below** (stated once here
to avoid repeating 27 times):
- **Save Dependency**: every section's fields live in the single
  `form_data` object persisted via `POST`/`PATCH` on save
  (`api.saveRNICAAssessment` / `api.updateRNICAAssessment`,
  `RNICA.jsx:11005-11014`) and via `useAssessmentAutosave` (30s interval).
- **Lock Dependency**: every section's required fields are re-validated by
  client `validateRNICA` (`RNICA.jsx:942-1102`) at lock time; sections that
  feed one of the 7 backend finalization-readiness checks are called out
  individually below (`backend/app/services/rnica_finalization_service.py:35-171`).
- **Audit Dependency**: no section writes its own audit event; the audit
  trail is written once, at the assessment level, on Lock
  (`RNICA_ASSESSMENT_LOCKED`, `backend/app/api/visits.py:1238-1251`) and on
  Amendment actions (`backend/app/services/rnica_amendment_service.py:125-139,189-201,227-239`).
  No section is individually audited.
- **Current Consumers**: unless otherwise noted, every section's data is
  consumed by (a) the RNICA record itself/history view
  (`backend/app/services/assessment_history_service.py:90-125`), (b) the
  RN ICA Intelligence engine only for the specific sections it reads
  (`backend/app/services/rnica_intelligence.py:57-176` — Pain, Diagnoses,
  Safety, Musculoskeletal, Neurological, Imminent Death, Psychosocial), and
  (c) dashboard counts of unlocked/incomplete RNICA
  (`backend/app/services/dashboard_service.py:1147-1152`).

---

## 1. Patient Demographics (with nested Caregiver Assessment & Advanced Care Planning)

**Repository location**: `RNICA.jsx:7920-8205`, nav config `RNICA.jsx:164-213`

**1. Section Name**: Patient Demographics (includes nested "Caregiver
Assessment" and "Advanced Care Planning" sub-sections)

**2. Business Purpose**: patient identity, contact/address, race/
ethnicity/language (HOPE), living situation, primary caregiver status and
capability evaluation (CDPH), and advance directive/treatment-preference
documentation (HOPE/CMS).

**3. Field Inventory**: `firstName`, `lastName`, `dob`, `gender`, `phone`,
`alternatePhone`, `race`, `ethnicity`, `preferredLanguage`,
`needsInterpreter`, `religion`, `maritalStatus`, `militaryService`,
`address.{street,city,state,zip,county}`,
`emergencyContact.{name,relationship,phone}`; **Caregiver (`pcg`)**:
`assessed`, `noPcg`, `noPcgReason`, `name`, `relationship`, `phone`,
`healthStatus`, `anxietyLevel`, `ableToAdministerMeds`,
`willingToProvideCare`, `pcgConcerns`,
`caregiverEvaluation.{physicalAbility,cognitiveAbility,emotionalReadiness,
availabilityForCare,trainingNeeds,willingnessScore,capabilityScore,
supportSystemAdequacy,evaluationNotes}`; **Living Situation**:
`siteOfService`, `admittedFrom`, `livingArrangement`,
`availabilityOfAssistance`; **Advanced Care Planning**:
`cprPreferenceAskedStatus`, `codeStatus`, `codeStatusDate`,
`lifeSustainingAskedStatus`, `lifeSustainingTreatmentPreference`,
`lifeSustainingTreatmentPreferenceDate`, `hospitalizationAskedStatus`,
`hospitalizationPreference`, `hospitalizationPreferenceDate`,
`decisionMaker`, `poaName`, `poaPhone`, `advanceDirectiveOnFile`,
`polstOnFile`. (~45 fields total.)

**4. Required Fields (hard errors)**: `firstName`, `lastName`, `dob`,
`gender`; `advancedCarePlanning.cprPreferenceAskedStatus`,
`advancedCarePlanning.codeStatus`,
`advancedCarePlanning.lifeSustainingAskedStatus`,
`advancedCarePlanning.lifeSustainingTreatmentPreference`,
`advancedCarePlanning.hospitalizationAskedStatus`,
`advancedCarePlanning.hospitalizationPreference` (`RNICA.jsx:947-990`).

**5. Conditional Fields**: `pcg.noPcgReason` shown only if `noPcg=true`;
full PCG detail fields (`name`, `relationship`, etc.) shown only if
`noPcg=false`; Caregiver Willingness & Capability Evaluation card rendered
only when `!pcg.noPcg`; Advanced Care Planning card rendered only when
`showPlanning` is true (`RNICA.jsx:8026-8205`).

**6. Validation Rules**: warnings (not hard errors) for `preferredLanguage`
(HOPE A1110), `ethnicity` (HOPE A1005), `race` (HOPE A1010),
`pcg.assessed`, `pcg.willingToProvideCare`, `pcg.ableToAdministerMeds`,
`caregiverEvaluation.willingnessScore`,
`caregiverEvaluation.capabilityScore` (`RNICA.jsx:955-1005`).

**7. HOPE Dependencies**: `A1110` (language), `A1005` (ethnicity), `A1010`
(race), `A0215` (site of service), `A1805` (admitted from), `A1905`
(living arrangement), `A1910` (availability of assistance), `F2000` (CPR
preference asked), `F2100` (life-sustaining asked), `F2200`
(hospitalization asked).

**8. AI Dependencies**: none directly — Demographics is not one of the
sections read by `rnica_intelligence.py`.

**9. Structured Findings Dependencies**: none identified for this section.

**10. POC Dependencies**: none directly.

**11. Finalization Dependencies**: none of the demographics/ACP fields are
part of the 7 backend finalization-readiness checks (those are diagnoses/
referrals/POC/finalization-section fields only).

**12–13. Save/Lock Dependencies**: standard (see common mechanisms above);
ACP hard-error fields block lock via client `validateRNICA`.

**14. Audit Dependencies**: standard (assessment-level only).

**15. Current Consumers**: patient record/facesheet-adjacent context,
assessment history; not read by Intelligence or POC adapter.

**16. Safe To Rename**: Yes, for card titles/labels (e.g. "Primary
Caregiver" section heading) — field keys and HOPE codes must not be
renamed.

**17. Safe To Move**: Yes — Caregiver Assessment and Advanced Care
Planning could be regrouped elsewhere (e.g. under a "Caregiver & Support"
group per `RNICA_EXPERIENCE_IMPLEMENTATION_PLAN.md` Phase 2) without
breaking any dependency, since nothing downstream reads them by section
position.

**18. Safe To Reorganize**: Yes, per above.

**19. DO NOT TOUCH**: the 6 Advanced Care Planning required fields'
underlying keys and their hard-error validation; HOPE code labels
(A1110/A1005/A1010/F2000/F2100/F2200) must not be removed or relabeled
without regulatory review.

---

## 2. Vitals

**Repository location**: `RNICA.jsx:8765-8798`

**1. Section Name**: Vitals

**2. Business Purpose**: routine vital signs, anthropometrics, and IV
access assessment.

**3. Field Inventory**: `temperature`, `temperatureUnit`, `pulse`,
`pulseQuality`, `respirations`, `bloodPressure.{systolic,diastolic}`,
`oxygenSaturation`, `oxygenSaturationOnRA`, `height`, `weight`, `bmi`
(auto-calculated), `mac`,
`ivAssessment.{hasIV,type,size,site,dressingType,insertionDate,
lastChangeDate,condition,notes}`. (~20 fields.)

**4. Required Fields**: none — no hard errors found in `validateRNICA` for
this section.

**5. Conditional Fields**: IV Assessment detail fields are only meaningful
when `ivAssessment.hasIV` is checked (no code-level hide/show gate
confirmed beyond that).

**6. Validation Rules**: none — fully unvalidated by `validateRNICA`.

**7. HOPE Dependencies**: none.

**8. AI Dependencies**: none — Vitals is not read by
`rnica_intelligence.py`.

**9. Structured Findings Dependencies**: none identified.

**10. POC Dependencies**: none directly.

**11. Finalization Dependencies**: none.

**12–14. Save/Lock/Audit**: standard; no lock-blocking behavior from this
section.

**15. Current Consumers**: assessment history; height/weight/BMI also
referenced by nutrition-section reference cards and LCD fact derivation
(not RNICA intelligence).

**16–18. Safe To Rename/Move/Reorganize**: Yes — this is the least
constrained section in the entire RNICA form; no compliance, AI, or
billing dependency was found.

**19. DO NOT TOUCH**: none identified.

---

## 3. Pain Assessment

**Repository location**: `RNICA.jsx:8802-8869`

**1. Section Name**: Pain Assessment

**2. Business Purpose**: HOPE-mandated pain screening (J0900), pain tool
selection, characterization, and non-pharmacologic management planning.

**3. Field Inventory**: `screenedForPain`, `screeningDate`,
`painSeverityCategory`, `standardizedPainToolType`, `verbalizesPain`,
`uncomfortableBecauseOfPain`, `neuropathicPain`, `assessmentTool`,
`painIntensity.{current,worst,best,acceptable}`,
`comprehensiveAssessmentCompleted`, `comprehensiveAssessmentDate`,
`painLocation`, `painCharacter`, `aggravatingFactors`, `relievingFactors`,
`nonPharmInterventions`, `painManagementPlan`. (~18 fields.)

**4. Required Fields (hard errors)**: `screenedForPain` (HOPE J0900.A);
`painSeverityCategory` (conditional, HOPE J0900.C, required only when
screened positive); `standardizedPainToolType` (conditional, HOPE
J0900.D); `neuropathicPain` (HOPE J0915) (`RNICA.jsx:1010-1020`).

**5. Conditional Fields**: `painSeverityCategory`/`standardizedPainToolType`
required only when `screenedForPain === "1"`; Pain Characteristics card
shown only when `painAssessmentMode === "verbal"`; PAINAD Scale shown only
when mode is `"painad"`; FLACC Scale shown only when mode is `"flacc"`.

**6. Validation Rules**: `verbalizesPain` is a warning, not a hard error
(`RNICA.jsx:1016-1018`).

**7. HOPE Dependencies**: `J0900` (screening/severity/tool), `J0915`
(neuropathic pain).

**8. AI Dependencies**: **Yes** — `rnica_intelligence.py` reads
`form_data.pain` (section text) and `pain.painIntensity.current` to
generate pain-burden findings/recommendations
(`backend/app/services/rnica_intelligence.py:57-76,129-152`).

**9. Structured Findings Dependencies**: pain severity is written by the
structured-findings apply layer into `pain.painSeverityCategory`
(`RNICA.jsx:10190-10212,10942-10970`).

**10. POC Dependencies**: indirect only, via general RNICA→POC problem
generation; no pain-specific adapter logic identified beyond the general
mechanism.

**11. Finalization Dependencies**: none of the pain fields are among the 7
backend finalization checks directly, but `screenedForPain`/
`neuropathicPain` are hard errors that block lock via client validation.

**12–14. Save/Lock/Audit**: standard; hard-error fields block lock.

**15. Current Consumers**: Intelligence panel (pain-burden findings),
Symptom Impact auto-derivation (reads `painSeverityCategory`).

**16. Safe To Rename**: Yes for card/section labels; not for HOPE-coded
field labels (J0900/J0915) without regulatory review.

**17. Safe To Move**: Yes — could be grouped under "Clinical Assessment"
(Phase 2 grouping) without breaking dependencies, since Intelligence reads
by field path, not section position.

**18. Safe To Reorganize**: Yes, per above.

**19. DO NOT TOUCH**: `screenedForPain`, `painSeverityCategory`,
`standardizedPainToolType`, `neuropathicPain` field keys/validation; the
`pain.painIntensity.current` path consumed by the Intelligence engine.

---

## 4. Symptom Impact

**Repository location**: `RNICA.jsx:8875-8894`

**1. Section Name**: Symptom Impact

**2. Business Purpose**: HOPE J2051 A–H symptom-severity summary
(pain, shortness of breath, anxiety, nausea, vomiting, diarrhea,
constipation, agitation).

**3. Field Inventory**: `pain`, `shortnessOfBreath`, `anxiety`, `nausea`,
`vomiting`, `diarrhea`, `constipation`, `agitation`, `assessmentDate`.
(9 fields.)

**4. Required Fields**: none are hard errors — all 8 J2051 items are
**warnings only** (`RNICA.jsx:1021-1024`).

**5. Conditional Fields**: none — all 8 are always rendered; however all 8
are auto-derived (fill-if-blank) from other sections (see below).

**6. Validation Rules**: warning per missing J2051 item, labeled
`HOPE J2051{A-H}: {field} score required`.

**7. HOPE Dependencies**: `J2051A`–`J2051H` (all 8 fields).

**8. AI Dependencies**: indirect — this section is itself partly *derived
from* Intelligence-adjacent body-system fields (pain, respiratory, GI,
neuro), not read as Intelligence input.

**9. Structured Findings Dependencies**: auto-derivation logic
(`RNICA.jsx:10942-10992`) fills each J2051 field from
`pain.painSeverityCategory`, `respiratory.sobSeverity`,
`neurological.symptomsDemeanor` (Anxiety/Agitation checklist presence), and
`gastrointestinal.{nausea,vomiting,diarrhea,constipation}` — only while the
target field is still blank, never overwriting a manual entry.

**10. POC Dependencies**: none identified.

**11. Finalization Dependencies**: none — soft warnings only, not part of
the 7 backend readiness checks.

**12–14. Save/Lock/Audit**: standard; does not block lock (warnings only).

**15. Current Consumers**: HOPE submission payload (via
`rnica_hope_workflow_service.py`).

**16. Safe To Rename**: Yes for UI labels; HOPE code labels (J2051 A–H)
should not be relabeled without regulatory review.

**17. Safe To Move**: Yes.

**18. Safe To Reorganize**: Yes — this section is a strong candidate for
the auto-population/simplification work described in
`RNICA_EXPERIENCE_IMPLEMENTATION_PLAN.md` Phase 6, since the underlying
derivation logic already exists and is safe (blank-fill only).

**19. DO NOT TOUCH**: the auto-derivation's blank-only fill guarantee
(`RNICA.jsx:10955-10992`) — must never be changed to overwrite a manual
entry, and the field keys must remain stable since HOPE submission reads
them directly.

---

## 5. Diagnoses

**Repository location**: `RNICA.jsx:8891-8933` (main), `RNICA.jsx:1973-2140`
(narrative/LCD/comorbidities), `RNICA.jsx:1605-1700` (LCD detect/config/eval)

**1. Section Name**: Diagnoses

**2. Business Purpose**: principal/secondary diagnosis capture, HOPE
comorbidity documentation, disease trajectory, clinical narrative, and LCD
(Local Coverage Determination) eligibility support.

**3. Field Inventory**: `primaryDiagnosis.{icd10,description,onsetDate,
hopeDiagnosisCategory}`, `terminalPrognosis`,
`secondaryDiagnoses[].{icd10,description,relatedToTerminal}`,
`hopeComorbidities.<categoryKey>` (per-category checkboxes),
`lcdEligibilityNarrative`, `clinicalNarrative`, `clinicalNarrativeReviewed`,
`diseaseTrajectory`, `recentHospitalizations`, `recentErVisits`,
`utilizationNotes`, `rnAddendum`, `clinicianClarification`,
`ndsEligibility.{detectedDisease,criteriaAnswers,criteriaFacts}`
(LCD sub-state). (~20+ fields plus repeatable secondary-diagnosis rows.)

**4. Required Fields (hard errors)**: `primaryDiagnosis.icd10`,
`primaryDiagnosis.hopeDiagnosisCategory` (HOPE I0010)
(`RNICA.jsx:1036-1040`).

**5. Conditional Fields**: `clinicalNarrativeReviewed` becomes a
soft-required warning only if `clinicalNarrative` has text
(`RNICA.jsx:1076-1077`); LCD config/evaluation panels only render once
`ndsEligibility.detectedDisease` is populated (`RNICA.jsx:1641-1700`).

**6. Validation Rules**: hard errors on ICD-10 + HOPE category; soft
warning on unreviewed narrative; `primaryDiagnosis.description`,
`terminalPrognosis`, secondary diagnoses, HOPE comorbidities, disease
trajectory, utilization fields, addendum/clarification are all
**unvalidated** by `validateRNICA`.

**7. HOPE Dependencies**: `I0010` (principal diagnosis), `J0050`
(cross-referenced with Imminent Death), plus per-category HOPE codes in
`hopeComorbidities`.

**8. AI Dependencies**: **Yes, extensively** — `rnica_intelligence.py`
reads `primaryDiagnosis.description`, `primaryDiagnosis.icd10`, and
`diseaseTrajectory` for evidence/findings generation
(`backend/app/services/rnica_intelligence.py:63-68,132-153`). Additionally,
the LCD detect/config/eval chain (`detectLCD`, `getLCDConfig`,
`evaluateLCD`) is driven entirely by diagnosis text
(`RNICA.jsx:1605-1700`).

**9. Structured Findings Dependencies**: **Yes** — diagnoses/comorbidity
fields are explicit `applyStructuredFindings`/`CONCEPT_REGISTRY` targets
(`RNICA.jsx:69-71,10072`).

**10. POC Dependencies**: diagnosis/disease-trajectory content feeds POC
problem descriptions via the adapter
(`backend/app/services/rnica_poc_adapter.py:222-287,432-668`).

**11. Finalization Dependencies**: **Yes — two of the 7 backend readiness
checks originate here**: `clinicalNarrativeReviewed` (narrative-reviewed
check) and `lcdEligibilityNarrative` (LCD baseline check)
(`backend/app/services/rnica_finalization_service.py:117-136`).

**12–14. Save/Lock/Audit**: standard; the two finalization checks above
block Lock if unmet.

**15. Current Consumers**: Intelligence panel, LCD evaluator, POC adapter,
HOPE comorbidity submission, finalization readiness gate.

**16. Safe To Rename**: Yes for card/UI labels; not for `icd10`/
`hopeDiagnosisCategory` field keys or HOPE code I0010 labeling.

**17. Safe To Move**: Yes for section position; the LCD panel's *visibility
gating* (only show once diagnosis is entered) is explicitly noted as safe
in `RNICA_EXPERIENCE_IMPLEMENTATION_PLAN.md` Phase 6.

**18. Safe To Reorganize**: Yes, with the LCD/narrative sub-panels kept
functionally intact.

**19. DO NOT TOUCH**: `primaryDiagnosis.icd10`,
`primaryDiagnosis.hopeDiagnosisCategory`, `lcdEligibilityNarrative`,
`clinicalNarrativeReviewed` field keys and their finalization-gate wiring;
the LCD detect→config→eval call sequence and its exact payload shape
(`buildLcdEvaluationPayload`).

---

## 6. Performance Status

**Repository location**: `RNICA.jsx:8939-8976`

**1. Section Name**: Performance Status

**2. Business Purpose**: functional/prognostic scoring (PPS, KPS, ECOG,
FAST, NYHA) supporting HOPE M1190 and disease-specific severity staging.

**3. Field Inventory**: `pps`, `ppsJustification`, `kps`,
`kpsJustification`, `ecog`, `ecogJustification`, `fast`, `fastStage`,
`nyha`, `nyhaJustification`, `functionalDeclineNotes`, plus a non-field
`declineTracker` custom renderer. (~11 fields.)

**4. Required Fields**: none individually required; **warning** if both
`pps` and `kps` are blank (HOPE M1190) (`RNICA.jsx:1044`).

**5. Conditional Fields**: disease-specific scales (FAST for dementia,
NYHA for cardiac) are contextually relevant but not code-gated to a
specific diagnosis in the reviewed code.

**6. Validation Rules**: single combined warning (PPS-or-KPS required).

**7. HOPE Dependencies**: `M1190`.

**8. AI Dependencies**: none directly identified for this section beyond
general evidence gathering.

**9. Structured Findings Dependencies**: **Yes** — `CONCEPT_REGISTRY`
includes an NYHA mapping target (`nyha`) (`RNICA.jsx:1114-1116`;
`backend/app/services/evidence/structured_findings.py`).

**10. POC Dependencies**: none directly identified.

**11. Finalization Dependencies**: none.

**12–14. Save/Lock/Audit**: standard; does not block lock.

**15. Current Consumers**: HOPE submission (M1190), structured-findings
registry.

**16–18. Safe To Rename/Move/Reorganize**: Yes.

**19. DO NOT TOUCH**: the PPS/KPS-or-blank warning logic; HOPE M1190
code label.

---

## 7–16. Body-System Sections (10 sections)

**Repository location**: field definitions in
`sns-emr-frontend/src/config/bodySystems.js:1-190`
(`SHARED_BODY_SYSTEM_CONFIG`, 10 entries), rendered at
`RNICA.jsx:8992-9379`.

Each of the 10 shares the same structural pattern (checkbox/select/radio/
textarea findings for that body system, mostly optional/unvalidated). Only
**Neurological** and **Skin/Wounds** carry HOPE codes; the other 8 carry
none (`hope: []` in `bodySystems.js`).

### 7. Neurological
- **Field Inventory**: `symptomsDemeanor`, `consciousness`,
  `orientation.{time,place,person,situation,disoriented}`,
  `hopeItems.{n0500,n0510,n0520}`, `communication`, `hearing`, `vision`,
  `balance`, `sensoryDeficits`, `sensoryAids`, `cognition`, `delirium`,
  `seizureHistory`, `psychiatricHistory`. (~18 fields.)
- **Required Fields**: none hard; `hopeItems.n0500` is a **warning** if
  missing (BIMS repetition, HOPE N0500) (`RNICA.jsx:1049-1050`).
- **Conditional Fields**: none code-gated beyond general rendering.
- **Validation Rules**: single N0500 warning.
- **HOPE Dependencies**: `N0500`, `N0510`, `N0520`.
- **AI Dependencies**: **Yes** — `rnica_intelligence.py` reads
  `form_data.neurological` for delirium/cognitive findings
  (`rnica_intelligence.py:57-176`); `symptomsDemeanor` (Anxiety/Agitation)
  also feeds Symptom Impact auto-derivation (Section 4 above).
- **Structured Findings Dependencies**: general registry plumbing present;
  no specific mapping beyond symptomsDemeanor→Symptom Impact.
- **POC Dependencies**: none directly.
- **Finalization Dependencies**: none.
- **Current Consumers**: Intelligence panel, Symptom Impact
  auto-derivation, HOPE BIMS submission.
- **Safe To Rename/Move/Reorganize**: Yes.
- **DO NOT TOUCH**: `hopeItems.n0500/n0510/n0520` keys; `symptomsDemeanor`
  path (feeds Symptom Impact derivation).

### 8. Cardiovascular
- **Field Inventory**: `bpSymptoms`, `pulseSites`, `pulseQuality`,
  `edema.{present,location,severity}`, `chestPain.present`, `jvd`,
  `pacemaker`, `internalDefibrillator`, `varicoseVeins`,
  `centralVenousLine`, `coolExtremities`, `stasisUlcer`,
  `heartFailurePresent`, `heartFailureType`. (~15 fields.)
- **Required Fields**: none.
- **Conditional Fields**: none code-gated.
- **Validation Rules**: none.
- **HOPE Dependencies**: none (`hope: []`).
- **AI Dependencies**: none identified.
- **Structured Findings Dependencies**: **Yes** — multiple `cardiovascular.*`
  paths are explicit structured-findings targets
  (`backend/app/services/evidence/structured_findings.py`).
- **POC/Finalization Dependencies**: none identified.
- **Current Consumers**: assessment record only.
- **Safe To Rename/Move/Reorganize**: Yes — no HOPE/AI/finalization
  dependency found.
- **DO NOT TOUCH**: field key paths consumed by the structured-findings
  registry (must not rename without updating the registry).

### 9. Respiratory
- **Field Inventory**: `sobSeverity`, `exertionLevel`, `coughType`,
  `lungSounds`, `respirations`,
  `oxygenTherapy.{inUse,type,litersPerMinute,hoursPerDay,deliveryMode,
  onRoomAir,satOnO2}`,
  `ventilator.{shortTermVentilator,longTermVentilator,
  ventilatorTypeAndSettings,tracheostomyType,tracheostomySize}`, `notes`.
  (~18 fields.)
- **Required Fields**: none.
- **Conditional Fields**: ventilator/tracheostomy detail fields only
  meaningful when ventilator flags are set (no confirmed hard gate).
- **Validation Rules**: none directly, but `sobSeverity` feeds Symptom
  Impact's `shortnessOfBreath` auto-derivation (Section 4).
- **HOPE Dependencies**: none.
- **AI Dependencies**: `respiratory` is one of the sections read by
  `rnica_intelligence.py` (oxygen-use finding).
- **Structured Findings Dependencies**: `respiratory.*` paths present in
  the structured-findings registry.
- **POC/Finalization Dependencies**: none identified.
- **Current Consumers**: Intelligence panel, Symptom Impact
  auto-derivation.
- **Safe To Rename/Move/Reorganize**: Yes.
- **DO NOT TOUCH**: `sobSeverity` path (feeds derivation);
  `oxygenTherapy.inUse` (feeds Intelligence safety finding).

### 10. Infection
- **Field Inventory**: `immunosuppressed`, `precautions`,
  `antibioticResistantInfection`, `historyOfResistantInfections`,
  `currentInfections`, `antibioticUse`, `temperature`, `recurrentInfection`,
  `infectionHistory`, `notes`. (~10 fields.)
- **Required/Conditional/Validation**: none.
- **HOPE/AI/Structured Findings/POC/Finalization Dependencies**: none
  identified.
- **Current Consumers**: assessment record only.
- **Safe To Rename/Move/Reorganize**: Yes — least-constrained body system.
- **DO NOT TOUCH**: none identified.

### 11. Gastrointestinal
- **Field Inventory**: `nausea`, `vomiting`, `vomitingOccurrences24h`,
  `diarrhea`, `constipation`, `bowelSounds`, `abdomen`, `ascites`,
  `abdominalGirth`, `stoolCharacter`, `bowelStatus`, `bowelFrequency`,
  `lastBM`, `reasonBowelRegimenNotInitiated`, `feedingTube.{present,type}`,
  `ostomy.{present,type}`, `notes`. (~18 fields.)
- **Required Fields**: none hard.
- **Validation Rules**: `nausea`, `vomiting`, `diarrhea`, `constipation`
  feed Symptom Impact's J2051 D–G auto-derivation (Section 4), which
  itself is warning-level, not this section.
- **HOPE Dependencies**: none directly on this section.
- **AI Dependencies**: none directly on this section (Symptom Impact is
  the AI-adjacent derivation target, not GI itself, per current evidence).
- **Structured Findings Dependencies**: general registry plumbing present.
- **POC/Finalization Dependencies**: none identified.
- **Current Consumers**: Symptom Impact auto-derivation.
- **Safe To Rename/Move/Reorganize**: Yes.
- **DO NOT TOUCH**: `nausea`/`vomiting`/`diarrhea`/`constipation` path
  names (feed Symptom Impact derivation).

### 12. Nutrition
- **Field Inventory**: `weightLossPastSixMonths`, `appetite`, `dietType`,
  `fluidIntake`, `swallowingIssues`, `oralMucosa`,
  `dentures.{upper,lower}`, `nutritionalSupplements`, `npoStatus`,
  `artificialFeeding`, `oralCavityFindings`, `notes`. (~13 fields.)
- **Required/Conditional/Validation**: none.
- **HOPE/AI/Structured Findings/POC/Finalization Dependencies**: none
  identified.
- **Current Consumers**: assessment record only; cross-referenced by
  Vitals' height/weight/BMI for reference cards.
- **Safe To Rename/Move/Reorganize**: Yes.
- **DO NOT TOUCH**: none identified.

### 13. Endocrine
- **Field Inventory**: `endocrineImpairment`, `thyroid.{assessment,notes}`,
  `diabetes.{type,dependency,glucoseMonitoring,lastHbA1c,lastHbA1cDate,
  insulinType,insulinDose,oralHypoglycemics}`, `endocrineSymptoms`,
  `currentEndocrineMeds`, `notes`. (~15 fields.)
- **Required/Conditional/Validation**: none.
- **HOPE/AI/Structured Findings/POC/Finalization Dependencies**: none
  identified.
- **Current Consumers**: assessment record only.
- **Safe To Rename/Move/Reorganize**: Yes.
- **DO NOT TOUCH**: none identified.

### 14. Genitourinary
- **Field Inventory**: `urinaryStatus`, `frequency`, `urineCharacteristics`,
  `urineColor`, `catheter.{present,type,size,insertionDate,lastChangeDate,
  condition,urineCharacteristics,irrigation.{solution,frequency,duration}}`,
  `catheterCare`, `urineOutput`, `twentyFourHourVolume`,
  `reproductive.{concerns,notes}`, `bladderManagement`, `notes`.
  (~21 fields.)
- **Required/Conditional/Validation**: none.
- **HOPE/AI/Structured Findings/POC/Finalization Dependencies**: none
  identified.
- **Current Consumers**: assessment record only.
- **Safe To Rename/Move/Reorganize**: Yes.
- **DO NOT TOUCH**: none identified.

### 15. Musculoskeletal
- **Field Inventory**: `weakness`, `rigidity`, `rigidityPresent`,
  `contractures`, `contracturesPresent`, `contracturesLocation`,
  `romLimitations`, `musculoskeletalIssues`, `paralysis`, `gait`,
  `assistiveDevices`,
  `mobility.{ambulatoryStatus,endurance,transferAbility}`, `strength`,
  `balance`, `painWithMovement`,
  `adl.{bathing,dressing,toileting,transferring,eating,grooming}`,
  `fallHistory.{fallsLast90Days,fallInjuries}`, `notes`. (~26 fields.)
- **Required Fields**: none hard.
- **Validation Rules**: none direct.
- **HOPE Dependencies**: none (`hope: []`).
- **AI Dependencies**: **Yes** — `rnica_intelligence.py` reads
  `mobility.ambulatoryStatus` for mobility/fall-related findings
  (`backend/app/services/rnica_intelligence.py:117-126`).
- **Structured Findings Dependencies**: general registry plumbing present.
- **POC/Finalization Dependencies**: none identified.
- **Current Consumers**: Intelligence panel.
- **Safe To Rename/Move/Reorganize**: Yes.
- **DO NOT TOUCH**: `mobility.ambulatoryStatus` path (Intelligence input).

### 16. Skin / Wounds
- **Field Inventory**: `skinConditionsPresent`, `skinStatus`,
  `skinTurgor`,
  `braden.{sensoryPerception,moisture,activity,mobility,nutrition,
  frictionShear}` (+ derived `braden.total`), `pressureInjuryRisk`,
  `wounds[]` (repeatable: `presentAsPressureInjury`, `stage`, `woundType`,
  `location`, `length`, `width`, `depth`, `drainage`, `odor`,
  `periwoundCondition`, `isSkinTear`, `isSurgicalWound`,
  `isNonhealingWound`, `currentTreatment`, `dressing`,
  `dressingFrequency`), `woundImpairment`, `pressureReliefMeasures`,
  `repositioningPlan`, `notes`. (~15 top-level fields + 16 per wound row.)
- **Required Fields**: `braden.total` is a **warning** if missing
  (`RNICA.jsx:1060-1061`) — note `braden.total` is a derived value, not a
  directly-entered field in the reviewed section config.
- **Conditional Fields**: `wounds[]` rows are only meaningful if
  `skinConditionsPresent`/wounds are documented; no hard code gate beyond
  that confirmed.
- **HOPE Dependencies**: `M1190` (shared with Performance Status).
- **AI Dependencies**: none directly cited beyond general evidence
  gathering.
- **Structured Findings Dependencies**: general registry plumbing present.
- **POC/Finalization Dependencies**: none identified.
- **Current Consumers**: HOPE M1190 submission (shared context with
  Performance Status).
- **Safe To Rename/Move/Reorganize**: Yes.
- **DO NOT TOUCH**: `braden.total` warning logic; `M1190` HOPE label.

---

## 17. Imminent Death

**Repository location**: `RNICA.jsx:9356-9374`

**1–2. Name / Purpose**: Imminent Death — HOPE J0050 prognosis screening,
comfort-measures and family-notification documentation.

**3. Field Inventory**: `appearsThreeDaysOrLess`, `indicators`
(checkboxGroup: mottling, mandibular breathing, apneic periods, cyanosis,
no urine output, unresponsive, death rattle, Cheyne-Stokes, cool/cold
extremities, decreased LOC, inability to swallow), `comfortMeasuresInPlace`,
`familyNotified`, `notes`. (5 top-level fields.)

**4. Required Fields**: `appearsThreeDaysOrLess` is a **warning** (HOPE
J0050), not a hard error (`RNICA.jsx:1054-1055`).

**5. Conditional Fields**: none code-gated.

**6. Validation Rules**: single J0050 warning.

**7. HOPE Dependencies**: `J0050`.

**8. AI Dependencies**: **Yes** — `rnica_intelligence.py` reads
`imminentDeath.appearsThreeDaysOrLess`; if truthy, emits a high-severity
"imminent death indicators" finding (`rnica_intelligence.py:57-176`).

**9. Structured Findings Dependencies**: none identified beyond generic
plumbing.

**10. POC Dependencies**: none identified.

**11. Finalization Dependencies**: none — warning only.

**12–14. Save/Lock/Audit**: standard; does not block lock.

**15. Current Consumers**: Intelligence panel (high-severity finding).

**16–18. Safe To Rename/Move/Reorganize**: Yes for the `indicators`
checklist and notes; the `appearsThreeDaysOrLess` field key must remain
stable.

**19. DO NOT TOUCH**: `appearsThreeDaysOrLess` path (Intelligence input +
HOPE J0050 label).

---

## 18. SFV

**Repository location**: `RNICA.jsx:9376-9403`

**1–2. Name / Purpose**: SFV (Symptom Follow-up Visit) — tracks whether a
required follow-up visit (triggered by moderate/severe Symptom Impact
scores) has occurred, and re-captures symptom severity at that visit
(HOPE J2050/J2052/J2053).

**3. Field Inventory**: `symptomImpactScreeningCompleted`,
`symptomImpactScreeningDate`, `inPersonSfvCompleted`, `sfvDate`,
`reasonNotCompleted`,
`symptomImpactAtSfv.{pain,shortnessOfBreath,anxiety,nausea,vomiting,
diarrhea,constipation,agitation}` (HOPE J2053 A–H), `triggeredSymptoms`,
`findings`, `notes`. (~15 fields.)

**4. Required Fields**: none are hard errors in `validateRNICA`; SFV
completion is UI-driven by the trigger banner, not a form-level
requirement.

**5. Conditional Fields**: SFV section/banner appears only when
`sfvStatus.required` is true, driven by moderate/severe Symptom Impact
values elsewhere (`RNICA.jsx:11391-11394`).

**6. Validation Rules**: none directly on this section.

**7. HOPE Dependencies**: `J2050`, `J2052`, `J2053A`–`J2053H`.

**8. AI Dependencies**: none directly — the SFV *trigger* itself is
threshold logic on Symptom Impact values, not part of the
`rnica_intelligence.py` findings/recommendations output.

**9. Structured Findings Dependencies**: none identified.

**10. POC Dependencies**: none identified.

**11. Finalization Dependencies**: none identified.

**12–14. Save/Lock/Audit**: standard; SFV completion is not a lock gate.

**15. Current Consumers**: HOPE J2053 submission.

**16–18. Safe To Rename/Move/Reorganize**: Yes for section presentation;
the trigger banner's underlying threshold logic (reading Symptom Impact
severities) must remain wired.

**19. DO NOT TOUCH**: `sfvStatus.required`/`triggeredSymptoms` trigger
logic and its dependency on Symptom Impact field values; HOPE J2053 A–H
labels.

---

## 19. Safety

**Repository location**: `RNICA.jsx:9405-9458`

**1–2. Name / Purpose**: home safety, fall risk, transfer safety,
disaster/incident triage, and DME/supplies readiness.

**3. Field Inventory**: `safetyAssessmentCompleted`, `homeEnvironment`,
`fallRiskAssessmentCompleted`, `fallRiskLevel`, `transferSafetyLevel`,
`firearmInHome`, `oxygenInUse`, `oxygenSafetyReviewed`,
`incidentOccurrenceReported`, `incidentOccurrenceNotes`, `disasterLevel`,
`disasterLevelOneConditions`, `disasterLevelTwoConditions`,
`disasterLevelThreeConditions`, `notes`,
`supplies.{existingCategories,neededCategories,otherSuppliesNotes}`.
(~18 fields.)

**4. Required Fields**: none are hard errors.

**5. Conditional Fields**: `disasterLevel{One,Two,Three}Conditions` are
contextually tied to the selected `disasterLevel` value (no confirmed hard
render-gate beyond visual grouping).

**6. Validation Rules**: none directly in `validateRNICA`.

**7. HOPE Dependencies**: none (`hope: []`).

**8. AI Dependencies**: **Yes** — `rnica_intelligence.py` reads
`safety.fallRiskLevel` (Moderate/High → fall-risk finding) and
`safety.oxygenInUse` (respiratory-safety concern)
(`backend/app/services/rnica_intelligence.py:57-176`).

**9. Structured Findings Dependencies**: none identified beyond generic
plumbing.

**10. POC Dependencies**: none identified.

**11. Finalization Dependencies**: none.

**12–14. Save/Lock/Audit**: standard; does not block lock.

**15. Current Consumers**: Intelligence panel (fall-risk, oxygen-safety
findings).

**16–18. Safe To Rename/Move/Reorganize**: Yes.

**19. DO NOT TOUCH**: `fallRiskLevel`, `oxygenInUse` field paths
(Intelligence inputs).

---

## 20. Psychosocial

**Repository location**: `RNICA.jsx:9459-9498`

**1–2. Name / Purpose**: psychosocial risk/support screening, suicide/
self-harm safety documentation, social work referral triggering.

**3. Field Inventory**: `familySocialSupport`, `primarySupportPerson`,
`supportRelationship`, `patientConcerns` (includes "Suicide concerns"),
`caregiverFamilyConcerns`, `distressRating`, `psychosocialHistory`,
`copingAssessment`, `copingNotes`, `interventionPlan`,
`socialWorkVisitNeeded`, `notes`. (~12 fields.)

**4. Required Fields**: none are hard errors.

**5. Conditional Fields**: `notes` becomes a **warning if blank** when
`patientConcerns` includes "Suicide concerns" (`RNICA.jsx:1064-1067`) —
this is the one safety-critical conditional rule in this section.

**6. Validation Rules**: single conditional safety warning described
above.

**7. HOPE Dependencies**: none (`hope: []`).

**8. AI Dependencies**: **Yes** — `rnica_intelligence.py` reads
`distressRating`; if truthy, emits a psychosocial-support finding
(`rnica_intelligence.py:57-176`).

**9. Structured Findings Dependencies**: none identified beyond generic
plumbing.

**10. POC Dependencies**: none identified.

**11. Finalization Dependencies**: none.

**12–14. Save/Lock/Audit**: standard; the suicide-concerns/notes warning
does not hard-block lock (it is a warning, not an error), but is flagged
as a clinical-safety item that should not be casually removed.

**15. Current Consumers**: Intelligence panel (distress finding).

**16–18. Safe To Rename/Move/Reorganize**: Yes, with the
suicide-concerns/notes safety rule preserved regardless of visual
placement.

**19. DO NOT TOUCH**: the `patientConcerns` "Suicide concerns" value and
its coupling to the `notes` warning — this is a patient-safety
documentation requirement, not merely a UX nicety.

---

## 21. Spiritual

**Repository location**: `RNICA.jsx:9505-9530`

**1–2. Name / Purpose**: faith/spiritual distress screening and chaplain
referral (HOPE F3000).

**3. Field Inventory**: `patientActiveInFaithTradition`, `patientFaith`,
`caregiverActiveInFaithTradition`, `caregiverFaith`, `spiritualConcerns`,
`spiritualDistressRating`, `concernsDiscussed`, `concernsAskedStatus`
(HOPE F3000), `concernsDiscussedDate`, `chaplainNeeded`, `notes`.
(~11 fields.)

**4. Required Fields**: none are hard errors in `validateRNICA`.

**5. Conditional Fields**: none code-gated.

**6. Validation Rules**: none in `validateRNICA` despite `F3000` being a
HOPE-labeled field — this is a gap between HOPE labeling and enforced
validation, noted for awareness only (no change proposed).

**7. HOPE Dependencies**: `F3000` (concerns asked status).

**8. AI Dependencies**: none identified — Spiritual is not one of the
sections read by `rnica_intelligence.py`.

**9. Structured Findings Dependencies**: none identified.

**10. POC Dependencies**: none identified.

**11. Finalization Dependencies**: none.

**12–14. Save/Lock/Audit**: standard; does not block lock.

**15. Current Consumers**: HOPE F3000 submission only.

**16–18. Safe To Rename/Move/Reorganize**: Yes.

**19. DO NOT TOUCH**: `concernsAskedStatus` field key (HOPE F3000 label).

---

## 22. Bereavement

**Repository location**: `RNICA.jsx:9530-9551`

**1–2. Name / Purpose**: patient/caregiver bereavement concerns and risk
assessment.

**3. Field Inventory**: `patientConcerns`, `caregiverConcerns`,
`bereavementRisk`, `riskFactors`, `bereavementVisitNeeded`, `notes`.
(6 fields.)

**4–6. Required/Conditional/Validation**: none — no section-specific
hard errors or warnings in `validateRNICA`.

**7. HOPE Dependencies**: none (`hope: []`).

**8–11. AI/Structured Findings/POC/Finalization Dependencies**: none
identified.

**12–14. Save/Lock/Audit**: standard; does not block lock.

**15. Current Consumers**: assessment record only.

**16–18. Safe To Rename/Move/Reorganize**: Yes.

**19. DO NOT TOUCH**: none identified.

---

## 23. Personal Care

**Repository location**: `RNICA.jsx:9551-9595`

**1–2. Name / Purpose**: home health aide task planning, volunteer
services, community resources, and equipment/supply needs.

**3. Field Inventory**: `aideTasks`,
`aideVisitPreferences.{frequency,preferredTime,duration}`,
`volunteerServices`, `communityResources`, `equipmentSupplyNeeds`,
`notes`. (6 top-level fields.)

**4–6. Required/Conditional/Validation**: none.

**7–11. HOPE/AI/Structured Findings/POC/Finalization Dependencies**: none
identified. Note: `aideTasks`/`aideVisitPreferences` are conceptually
related to the Admissions Order's `haAssignment` (home health aide), but
no direct code-level link between the two was found in this review.

**12–14. Save/Lock/Audit**: standard; does not block lock.

**15. Current Consumers**: assessment record only.

**16–18. Safe To Rename/Move/Reorganize**: Yes.

**19. DO NOT TOUCH**: none identified.

---

## 24. Teaching Needs

**Repository location**: `RNICA.jsx:9595-9642`

**1–2. Name / Purpose**: patient/family education assessment, topics,
methods, and response tracking.

**3. Field Inventory**: `primaryLearner`, `learningStylePreference`,
`barriersToLearning`, `educationTopics[]`, `teachingTopics`,
`teachingTopicsOther`, `teachingMethods`, `patientFamilyResponse`,
`followUpPlan`, `notes`. (~10 fields plus repeatable `educationTopics[]`.)

**4–6. Required/Conditional/Validation**: none.

**7–11. HOPE/AI/Structured Findings/POC/Finalization Dependencies**: none
identified.

**12–14. Save/Lock/Audit**: standard; does not block lock.

**15. Current Consumers**: assessment record only.

**16–18. Safe To Rename/Move/Reorganize**: Yes — one of the least
constrained sections in the form.

**19. DO NOT TOUCH**: none identified.

---

## 25. Admissions Order

**Repository location**: `RNICA.jsx:9642-9673`

**1–2. Name / Purpose**: physician's initial order — level of care, visit
frequency, home health aide assignment, initial POC/IDG completion
marker, non-covered items, and telephone-order (T.O.) verification.

**3. Field Inventory**: `admissionStatement`,
`levelOfCare.{level,effectiveDate,justification}`, `visitFrequency`
(per-discipline table), `treatmentMedsOrderCompleted`,
`haAssignment.{assignedAide,notApplicable}`,
`initialPocIdg.{created,createdDate,notes}`, `nonCoveredItems`,
`toVerification.{verbalOrderReadBack,verifiedBy,prescriberContacted,
verificationTimestamp}`. (~15 fields.)

**4. Required Fields (hard errors, ICA mode only)**: `levelOfCare.level`
(via `admissionsOrder.levelOfCare` check) and
`toVerification.verbalOrderReadBack` (via `admissionsOrder.toVerification`
check) — both required only when `mode === "ica"`, not in "ongoing" mode
(`RNICA.jsx:1081-1087`).

**5. Conditional Fields**: `levelOfCare`/`toVerification` requirement is
mode-conditional (ICA vs. ongoing); `levelOfCare.effectiveDate` is
auto-filled from patient data if blank (`RNICA.jsx:10733-10737`).

**6. Validation Rules**: two ICA-mode-only hard errors as above; all other
fields in this section are unvalidated.

**7. HOPE Dependencies**: none directly (`hope: []`), though this section
is adjacent to the F2000/F2100/F2200 CMS tags shown at a higher sidebar
level in some navigation renderings.

**8. AI Dependencies**: none identified.

**9. Structured Findings Dependencies**: none identified.

**10. POC Dependencies**: **Yes** — `haAssignment` and `initialPocIdg`
feed the CHHA-POC finalization check (below); the section's own note
states IDG should be created only after all assessment problems are added
to Initial POC (`RNICA.jsx:868-875`); the RNICA↔POC bridge is
`backend/app/services/rnica_poc_adapter.py`.

**11. Finalization Dependencies**: **Yes — feeds the CHHA POC readiness
check**: `haAssignment.notApplicable`, `haAssignment.assignedAide`, and
`chhaPoc.completed` together determine the `chhaPocCompleted` check
(`backend/app/services/rnica_finalization_service.py:138-161`).

**12–14. Save/Lock/Audit**: standard; the two ICA-mode hard errors and the
CHHA-POC readiness check both block Lock when unmet.

**15. Current Consumers**: finalization readiness gate, POC adapter.

**16. Safe To Rename**: Yes for card labels; not for
`levelOfCare`/`toVerification`/`haAssignment` keys.

**17. Safe To Move**: Yes.

**18. Safe To Reorganize**: Yes.

**19. DO NOT TOUCH**: `levelOfCare.level`, `toVerification.
verbalOrderReadBack` (ICA-mode hard errors);
`haAssignment.{assignedAide,notApplicable}` (CHHA-POC finalization gate
input).

---

## 26. Referrals

**Repository location**: `RNICA.jsx:9673-9694`

**1–2. Name / Purpose**: social work, spiritual care, volunteer, therapy,
dietitian, and pharmacist referral tracking, plus a review confirmation
gate.

**3. Field Inventory**: `socialWork.{referred,reason,urgency}`,
`spiritualCare.{referred,reason,urgency}`,
`volunteer.{referred,type,urgency}`, `therapy[]`,
`dietitian.{referred,reason}`, `pharmacist.{referred,reason}`, `other[]`,
`notes`, `reviewed`. (~18 fields.)

**4. Required Fields**: no client-side hard error, but **`reviewed` is
required by the backend finalization readiness check**
(`referralsReviewed`) (`backend/app/services/rnica_finalization_service.py:138-144`).

**5. Conditional Fields**: none code-gated beyond the referral-type
sub-fields being relevant only when that referral type's `referred`
checkbox is set.

**6. Validation Rules**: `reviewed` boolean gate enforced server-side at
lock time, not by client `validateRNICA`.

**7. HOPE Dependencies**: none identified.

**8–9. AI/Structured Findings Dependencies**: none identified.

**10. POC Dependencies**: none identified.

**11. Finalization Dependencies**: **Yes** — `referrals.reviewed` is one
of the 7 backend readiness checks.

**12–14. Save/Lock/Audit**: standard; `reviewed=false` blocks Lock via the
server readiness check (not the client validator).

**15. Current Consumers**: finalization readiness gate.

**16–18. Safe To Rename/Move/Reorganize**: Yes for individual referral
type labels/grouping; the `reviewed` field key must remain stable.

**19. DO NOT TOUCH**: `referrals.reviewed` field key and its finalization
gate wiring.

---

## 27. Finalization

**Repository location**: `RNICA.jsx:9694-9720`

**1–2. Name / Purpose**: completion tracking, clinician attestation,
signature, and lock gate — the terminal section of the RNICA.

**3. Field Inventory**: `completedSections`, `incompleteCount`,
`clinicalNarrative` (Section 12's own narrative — **distinct from**
`diagnoses.clinicalNarrative`, see note below), `signatureCertification`,
`clinicianSignature`, `signatureDate`, `hopeSubmissionNumber`,
`hopeAlreadySubmitted`,
`supervisorReview.{required,reviewedBy,reviewDate}`, `assessmentLocked`,
`lockedTimestamp`. (~13 fields.)

**4. Required Fields (hard errors)**: `clinicalNarrative` (Section 12's
own field), `clinicianSignature`, `signatureCertification`
(`RNICA.jsx:1091-1102`).

**5. Conditional Fields**: `signatureDate` is required by the UI's field
definition (`required: true`) but is **not** enforced by
`validateRNICA`'s error map — a UI/validation-engine mismatch noted for
awareness (no change proposed).

**6. Validation Rules**: 3 client hard errors as above; server-side
finalization readiness separately re-checks `signatureCertification`
(`attestation`) and `clinicianSignature` (`signature`)
(`backend/app/services/rnica_finalization_service.py:102-116`).

**7. HOPE Dependencies**: `hopeSubmissionNumber`/`hopeAlreadySubmitted`
relate to HOPE submission tracking (shared context with the HOPE workflow
service), not a HOPE clinical-item code itself.

**8–9. AI/Structured Findings Dependencies**: none identified.

**10. POC Dependencies**: `pocCompleteness` readiness check reads POC
problems/goals/interventions, not a Finalization-section field directly
(`backend/app/services/rnica_finalization_service.py:35-92`).

**11. Finalization Dependencies**: this section **is** the finalization
gate — it directly supplies 2 of the 7 readiness checks
(`signatureCertification`, `clinicianSignature`); the other 5 originate in
Diagnoses (2), Referrals (1), POC (1), and Admissions Order/CHHA (1).

**12. Save Dependency**: standard — this section's fields are saved like
any other, but are also re-persisted immediately before Lock
(`RNICA.jsx:11028-11033`).

**13. Lock Dependency**: **this section's fields, plus the aggregate
7-check readiness result, are the entire gate for the Lock button**
(`RNICA.jsx:11028-11051`; `rnica_finalization_service.py:35-171`).

**14. Audit Dependency**: Lock writes `RNICA_ASSESSMENT_LOCKED`
(`backend/app/api/visits.py:1238-1251`) — this is the one section whose
action directly triggers the assessment-level audit event.

**15. Current Consumers**: the Lock endpoint, HOPE submission tracking.

**16. Safe To Rename**: Yes for card/button labels ("Lock" itself could be
relabeled visually); not for the underlying field keys or gate logic.

**17. Safe To Move**: This section must remain the terminal/last-reached
section functionally (it is the lock gate), even if visually regrouped
under a "Final Review" presentation group (per
`RNICA_EXPERIENCE_IMPLEMENTATION_PLAN.md` Phase 2) — the underlying
sequencing (all other checks must be satisfiable before Lock succeeds)
cannot change.

**18. Safe To Reorganize**: Visual reorganization only, per above.

**19. DO NOT TOUCH**: `signatureCertification`, `clinicianSignature`,
`clinicalNarrative` (Section 12) field keys; the Lock button's call to
`api.lockRNICAAssessment` and its audit-event side effect; the
distinctness of `finalization.clinicalNarrative` from
`diagnoses.clinicalNarrative` — these are two separate fields serving two
separate readiness checks and must not be merged or confused.

---

## Clarifying Note: Two Distinct "Clinical Narrative" Fields

`diagnoses.clinicalNarrative` (Section 5) and
`finalization.clinicalNarrative` (Section 27) are **separate fields with
separate validation and readiness roles**:
- `diagnoses.clinicalNarrative` + `diagnoses.clinicalNarrativeReviewed`
  feed the backend's `narrativeReviewed` finalization check
  (`rnica_finalization_service.py:117-127`).
- `finalization.clinicalNarrative` is a separate, independently required
  client-side hard-error field (`RNICA.jsx:1091-1092`).

Any future redesign must preserve both fields distinctly — merging them
would silently remove one of the two current gates.

---

**Inventory only. No redesign, summarization-as-removal, or field
consolidation is proposed. Every section and field found in the repository
is listed above as of the time of this review.**
