# ADM Completeness Matrix

Status: Item-level completeness review, ADM (Admission) — 57 items. This
matrix reformats the already-completed ADM item trace on file in
`HOPE_ITEM_PROVENANCE_MATRIX.md` into a dedicated per-timepoint
completeness document, per instruction. No new repository research was
performed; STATUS values are unchanged from the source matrix.

**Scope honesty note (carried forward unchanged):** `VERIFIED BY CMS` is
marked Yes only for items independently confirmed against CMS citations
earlier in this engagement (A0250, J2052, J2053). All other rows'
CMS-text-level correctness was not re-derived this pass and are honestly
marked NOT_VERIFIED, not assumed correct.

| CMS Item | SNS Source Record | SNS Source Field | Transformation | Validation | STATUS |
|---|---|---|---|---|---|
| A0050 | none (hardcoded) | literal string | `"1 - Add new record"` constant | none — always this value | NOT_VERIFIED |
| A0100 | Agency/tenant config | `agency.npi/.address/.phone` | passthrough | none — placeholder if absent | NOT_VERIFIED |
| A0215 | RnicaAssessment.form_data | `demographics.livingSituation.siteOfService` | `officialCodeLookup` against `SITE_OF_SERVICE_LABELS` + legacy map | restricted to known code list; unmapped → placeholder | NOT_VERIFIED |
| A0220 | Patient / RnicaAssessment | `patient.socDate` ‖ `admissionsOrder.levelOfCare.effectiveDate` ‖ `completionDate` | 3-way fallback chain (flagged provenance risk in `HOPE_DATA_PROVENANCE_MATRIX.md`) | none | NOT_VERIFIED |
| A0250 | derived from `options.timepoint` | `RECORD_REASON_BY_TIMEPOINT` map | direct lookup by timepoint | restricted to 4 known timepoint values | **VERIFIED** |
| A0500 | Patient | `patient` name fields via `splitPatientName` | string split | none | NOT_VERIFIED |
| A0550 | RnicaAssessment.form_data | `demographics.address.zip` | passthrough | none | NOT_VERIFIED |
| A0600 | Patient | `patient.ssn`, `.medicareNumber` | passthrough | none | NOT_VERIFIED |
| A0700 | Patient | `patient.medicaidNumber` | passthrough | none | NOT_VERIFIED |
| A0810 | RnicaAssessment.form_data / Patient | `demographics.gender` ‖ `patient.sex` | `SEX_MAP` lookup | restricted to Male/Female/M/F; unmapped → placeholder | NOT_VERIFIED |
| A0900 | RnicaAssessment.form_data / Patient | `demographics.dob` ‖ `patient.dob` | `formatDate` | none | NOT_VERIFIED |
| A1005 | RnicaAssessment.form_data | `demographics.ethnicity` | `arrayText` (raw join) | none — not restricted to a CMS ethnicity code list | NOT_VERIFIED |
| A1010 | RnicaAssessment.form_data | `demographics.race` | `arrayText` (raw join) | none — not restricted to a CMS race code list | NOT_VERIFIED |
| A1110 | RnicaAssessment.form_data | `demographics.preferredLanguage`, `.needsInterpreter` | passthrough / `boolCode` | none for language value | NOT_VERIFIED |
| A1400 | Patient | `patient.primaryPayerType`/`.secondaryPayerType` | `payerSources()` crosswalk | restricted to known payer crosswalk | NOT_VERIFIED |
| A1805 | RnicaAssessment.form_data | `demographics.livingSituation.admittedFrom` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | NOT_VERIFIED |
| A1905 | RnicaAssessment.form_data | `demographics.livingSituation.livingArrangement` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | NOT_VERIFIED |
| A1910 | RnicaAssessment.form_data | `demographics.livingSituation.availabilityOfAssistance` | `ASSISTANCE_MAP` lookup | restricted; unmapped → placeholder | NOT_VERIFIED |
| F2000 | RnicaAssessment.form_data | `.cprPreferenceAskedStatus/.codeStatus/.codeStatusDate` | `askedStatus()` | derived asked/not-asked code | NOT_VERIFIED |
| F2100 | RnicaAssessment.form_data | `.lifeSustainingAskedStatus/.lifeSustainingTreatmentPreference(Date)` | `askedStatus()` | same pattern | NOT_VERIFIED |
| F2200 | RnicaAssessment.form_data | `.hospitalizationAskedStatus/.hospitalizationPreference(Date)` | `askedStatus()` | same pattern | NOT_VERIFIED |
| F3000 | RnicaAssessment.form_data | `spiritual.concernsAskedStatus/.concernsDiscussed(Date)` | `askedStatus()` | same pattern | NOT_VERIFIED |
| I0010 | RnicaAssessment.form_data | `diagnoses.primaryDiagnosis.{icd10,description,hopeDiagnosisCategory}` | category-code lookup + string concat | category restricted; ICD-10 text free | NOT_VERIFIED |
| I0100, I0600, I0900, I0950, I1101, I1510, I2102, I2900, I2910, I4501, I4801, I5150, I5401, I6202 (14 codes) | RnicaAssessment.form_data | `diagnoses.hopeComorbidities.{key}` (structured) or free-text regex inference (legacy path) | `boolCode()` OR regex heuristic | Structured: boolean only. Legacy: heuristic, flagged by mapper's own `dataSourceNote` | NOT_VERIFIED |
| I8005 | RnicaAssessment.form_data | `diagnoses.hopeComorbidities.other` or `diagnosisEntries(diagnoses).length` heuristic | `boolCode()` | same caveat as above | NOT_VERIFIED |
| I0000 | RnicaAssessment.form_data | `diagnosisEntries(diagnoses)` | list join | none | **OPEN_QUESTION** (see `I0000_PROVENANCE_TRACE.md`) |
| J0050 | RnicaAssessment.form_data | `imminentDeath.appearsThreeDaysOrLess` | `YES_NO_UNABLE_MAP` lookup | restricted to Yes/No/Unable | NOT_VERIFIED — also flagged CONFLICTING with `diagnoses.terminalPrognosis` in `HOPE_DATA_PROVENANCE_MATRIX.md` |
| J0900 | RnicaAssessment.form_data | `pain.{screenedForPain,painSeverityCategory,standardizedPainToolType,screeningDate}` | `painScreeningResponse()` | restricted per internal code maps | NOT_VERIFIED |
| J0905 | RnicaAssessment.form_data | `pain.painIntensity.current`/`.painManagementPlan`/`.painLocation` | `boolCode(Boolean(...))` | boolean derivation only | NOT_VERIFIED |
| J0910 | RnicaAssessment.form_data | `pain.comprehensiveAssessmentCompleted/.Date` | `boolCode`, `formatDate`, `derivePainFindings()` | none beyond boolean | NOT_VERIFIED |
| J0915 | RnicaAssessment.form_data | `pain.neuropathicPain` | `NEUROPATHIC_PAIN_MAP` lookup | restricted; unmapped → placeholder | NOT_VERIFIED |
| J2030 | RnicaAssessment.form_data | `respiratory.{shortnessOfBreathScreened,sobSeverity,screeningDate}` | `boolCode` + derived `sobIndicated` | none beyond boolean | NOT_VERIFIED |
| J2040 | RnicaAssessment.form_data | `respiratory.treatmentInitiated/.treatmentDate` | `boolCode`, `formatDate` | none | NOT_VERIFIED |
| J2050 | RNICA `sfv.*` self-attestation / `symptomImpact` | `sfv.symptomImpactScreeningCompleted/.Date` OR `symptomImpact.assessmentDate` | `boolCode`, `formatDate` | none — reads self-attestation, not SFVRequirement | **OPEN_QUESTION** (see `J2050_PROVENANCE_TRACE.md`) |
| J2051 | RnicaAssessment.form_data | `symptomImpact.*` (8 symptoms) | `symptomEntries()` | word-based MILD/MODERATE/SEVERE vocabulary | NOT_VERIFIED |
| J2052 (A/B) | SFVRequirement | `sfvStatus.completed/.completedAt` | `boolCode`, `formatDate` | ownership remediated, trigger-scoped | **VERIFIED** |
| J2052 (C) | RNICA form (unvalidated) | `sfv.reasonNotCompleted` | `j2052ReasonNotCompleted()` | restricted to codes 1/2/3/9, but no authoritative backend source | NOT_VERIFIED (see `J2052C_DECISION_RECORD.md`) |
| J2053 | SFVRequirement → ClinicalNote.content.symptomImpact | `sfvRequirement.symptomImpact` | `symptomEntries()` | restricted to backend-enforced value choices; ownership remediated | **VERIFIED** |
| M1190 | RnicaAssessment.form_data | `skin.skinConditionsPresent` | `boolCode` | none | NOT_VERIFIED |
| M1195 | RnicaAssessment.form_data | `skin.skinStatus` | `arrayText` | none | NOT_VERIFIED |
| M1200 | RnicaAssessment.form_data | `deriveSkinTreatments(skin)` | derivation helper | none | NOT_VERIFIED |
| N0500 | RnicaAssessment.form_data | `medications.scheduledOpioid/.Date` | `boolCode`, `formatDate` | none | NOT_VERIFIED — no live RNICA screen writes `medications.*` (only a data-seed script does) |
| N0510 | RnicaAssessment.form_data | `medications.prnOpioid/.Date` | `boolCode`, `formatDate` | none | NOT_VERIFIED (same gap) |
| N0520 | RnicaAssessment.form_data | `medications.bowelRegimen/.Date`, `opioidPresent` derivation | derived 3-state code | logic-derived, not directly asserted | NOT_VERIFIED (same gap) |
| Z0500 | RnicaAssessment.form_data | `finalization.{signatureCertification,clinicianSignature,signatureDate,hopeSubmissionNumber,hopeAlreadySubmitted}` | passthrough / `boolCode` | none beyond boolean/placeholder | NOT_VERIFIED |

## Summary

| Status | Count |
|---|---|
| VERIFIED | 3 (A0250, J2052 A/B, J2053) |
| NOT_VERIFIED | 52 |
| OPEN_QUESTION | 2 (I0000, J2050) |
| **Total** | **57** |

**Completeness: 3/57 fully VERIFIED (5%).** The remaining 52 items were
not independently re-derived against primary CMS text this engagement —
this is a documentation/CMS-verification backlog, not a known-broken
state. No item in this matrix (outside J2052C, I0000, J2050, and the
N05xx medication-source gap) has an identified repository defect; the
gap is unconfirmed CMS-text accuracy, not proven incorrectness.
