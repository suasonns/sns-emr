# HUV2 Completeness Matrix

Status: Item-level completeness review, HUV2 (second Hospice Update
Visit) — 54 items. Identical item set to HUV1 (ADM minus F2000/F2100/
F2200/F3000, plus Z0350). Source record confirmed as the matched HUV2
assessment's own `form_data` per `HUV2_PROVENANCE_TRACE.md`. This matrix
reformats the already-completed HUV2 item trace on file in
`HOPE_ITEM_PROVENANCE_MATRIX.md`; no new repository research was
performed.

| CMS Item | SNS Source Record | SNS Source Field | Transformation | Validation | STATUS |
|---|---|---|---|---|---|
| A0050 | none (hardcoded) | literal string | `"1 - Add new record"` constant | none — always this value | NOT_VERIFIED |
| A0100 | Agency/tenant config | `agency.npi/.address/.phone` | passthrough | none — placeholder if absent | NOT_VERIFIED |
| A0215 | RnicaAssessment(HUV2).form_data | `demographics.livingSituation.siteOfService` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | NOT_VERIFIED |
| A0220 | Patient / RnicaAssessment(HUV2) | `patient.socDate` ‖ `admissionsOrder.levelOfCare.effectiveDate` ‖ `completionDate` | 3-way fallback chain | none | NOT_VERIFIED |
| A0250 | derived from `options.timepoint` | `RECORD_REASON_BY_TIMEPOINT` map | direct lookup by timepoint | restricted to 4 known timepoint values | **VERIFIED** |
| A0500 | Patient | `patient` name fields via `splitPatientName` | string split | none | NOT_VERIFIED |
| A0550 | RnicaAssessment(HUV2).form_data | `demographics.address.zip` | passthrough | none | NOT_VERIFIED |
| A0600 | Patient | `patient.ssn`, `.medicareNumber` | passthrough | none | NOT_VERIFIED |
| A0700 | Patient | `patient.medicaidNumber` | passthrough | none | NOT_VERIFIED |
| A0810 | RnicaAssessment(HUV2).form_data / Patient | `demographics.gender` ‖ `patient.sex` | `SEX_MAP` lookup | restricted; unmapped → placeholder | NOT_VERIFIED |
| A0900 | RnicaAssessment(HUV2).form_data / Patient | `demographics.dob` ‖ `patient.dob` | `formatDate` | none | NOT_VERIFIED |
| A1005 | RnicaAssessment(HUV2).form_data | `demographics.ethnicity` | `arrayText` (raw join) | none | NOT_VERIFIED |
| A1010 | RnicaAssessment(HUV2).form_data | `demographics.race` | `arrayText` (raw join) | none | NOT_VERIFIED |
| A1110 | RnicaAssessment(HUV2).form_data | `demographics.preferredLanguage`, `.needsInterpreter` | passthrough / `boolCode` | none for language value | NOT_VERIFIED |
| A1400 | Patient | `patient.primaryPayerType`/`.secondaryPayerType` | `payerSources()` crosswalk | restricted to known payer crosswalk | NOT_VERIFIED |
| A1805 | RnicaAssessment(HUV2).form_data | `demographics.livingSituation.admittedFrom` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | NOT_VERIFIED |
| A1905 | RnicaAssessment(HUV2).form_data | `demographics.livingSituation.livingArrangement` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | NOT_VERIFIED |
| A1910 | RnicaAssessment(HUV2).form_data | `demographics.livingSituation.availabilityOfAssistance` | `ASSISTANCE_MAP` lookup | restricted; unmapped → placeholder | NOT_VERIFIED |
| I0010 | RnicaAssessment(HUV2).form_data | `diagnoses.primaryDiagnosis.{icd10,description,hopeDiagnosisCategory}` | category-code lookup + string concat | category restricted; ICD-10 text free | NOT_VERIFIED |
| I0100...I6202 (14 codes) | RnicaAssessment(HUV2).form_data | `diagnoses.hopeComorbidities.{key}` (structured) or regex inference (legacy) | `boolCode()` OR regex heuristic | structured: boolean only; legacy: heuristic | NOT_VERIFIED |
| I8005 | RnicaAssessment(HUV2).form_data | `diagnoses.hopeComorbidities.other` or heuristic | `boolCode()` | same caveat | NOT_VERIFIED |
| I0000 | RnicaAssessment(HUV2).form_data | `diagnosisEntries(diagnoses)` | list join | none | **OPEN_QUESTION** (see `I0000_PROVENANCE_TRACE.md`) |
| J0050 | RnicaAssessment(HUV2).form_data | `imminentDeath.appearsThreeDaysOrLess` | `YES_NO_UNABLE_MAP` lookup | restricted | NOT_VERIFIED — flagged CONFLICTING |
| J0900 | RnicaAssessment(HUV2).form_data | `pain.{screenedForPain,painSeverityCategory,standardizedPainToolType,screeningDate}` | `painScreeningResponse()` | restricted per internal code maps | NOT_VERIFIED |
| J0905 | RnicaAssessment(HUV2).form_data | `pain.painIntensity.current`/`.painManagementPlan`/`.painLocation` | `boolCode(Boolean(...))` | boolean derivation only | NOT_VERIFIED |
| J0910 | RnicaAssessment(HUV2).form_data | `pain.comprehensiveAssessmentCompleted/.Date` | `boolCode`, `formatDate`, `derivePainFindings()` | none beyond boolean | NOT_VERIFIED |
| J0915 | RnicaAssessment(HUV2).form_data | `pain.neuropathicPain` | `NEUROPATHIC_PAIN_MAP` lookup | restricted; unmapped → placeholder | NOT_VERIFIED |
| J2030 | RnicaAssessment(HUV2).form_data | `respiratory.{shortnessOfBreathScreened,sobSeverity,screeningDate}` | `boolCode` + derived `sobIndicated` | none beyond boolean | NOT_VERIFIED |
| J2040 | RnicaAssessment(HUV2).form_data | `respiratory.treatmentInitiated/.treatmentDate` | `boolCode`, `formatDate` | none | NOT_VERIFIED |
| J2050 | RNICA `sfv.*` self-attestation / `symptomImpact` | `sfv.symptomImpactScreeningCompleted/.Date` OR `symptomImpact.assessmentDate` | `boolCode`, `formatDate` | reads self-attestation, not SFVRequirement | **OPEN_QUESTION** (see `J2050_PROVENANCE_TRACE.md`) |
| J2051 | RnicaAssessment(HUV2).form_data | `symptomImpact.*` (8 symptoms) | `symptomEntries()` | word-based MILD/MODERATE/SEVERE vocabulary | NOT_VERIFIED |
| J2052 (A/B) | SFVRequirement | `sfvStatus.completed/.completedAt` | `boolCode`, `formatDate` | ownership remediated — resolved via `(triggerSourceType='HUV2', triggerVisitId)` matching this record's own trigger visit | **VERIFIED** |
| J2052 (C) | RNICA form (unvalidated) | `sfv.reasonNotCompleted` | `j2052ReasonNotCompleted()` | restricted to 1/2/3/9, no authoritative backend source | NOT_VERIFIED (see `J2052C_DECISION_RECORD.md`) |
| J2053 | SFVRequirement → ClinicalNote.content.symptomImpact | `sfvRequirement.symptomImpact` | `symptomEntries()` | backend-enforced value choices; ownership remediated | **VERIFIED** |
| M1190 | RnicaAssessment(HUV2).form_data | `skin.skinConditionsPresent` | `boolCode` | none | NOT_VERIFIED |
| M1195 | RnicaAssessment(HUV2).form_data | `skin.skinStatus` | `arrayText` | none | NOT_VERIFIED |
| M1200 | RnicaAssessment(HUV2).form_data | `deriveSkinTreatments(skin)` | derivation helper | none | NOT_VERIFIED |
| N0500 | RnicaAssessment(HUV2).form_data | `medications.scheduledOpioid/.Date` | `boolCode`, `formatDate` | none | NOT_VERIFIED — no live RNICA screen writes `medications.*` |
| N0510 | RnicaAssessment(HUV2).form_data | `medications.prnOpioid/.Date` | `boolCode`, `formatDate` | none | NOT_VERIFIED (same gap) |
| N0520 | RnicaAssessment(HUV2).form_data | `medications.bowelRegimen/.Date`, `opioidPresent` derivation | derived 3-state code | logic-derived | NOT_VERIFIED (same gap) |
| Z0350 | Finalization/assessment-meta derived | `completionDate` | passthrough/date derivation | none | NOT_VERIFIED — new item vs. ADM, no CMS re-derivation this pass |
| Z0500 | RnicaAssessment(HUV2).form_data | `finalization.{signatureCertification,clinicianSignature,signatureDate,hopeSubmissionNumber,hopeAlreadySubmitted}` | passthrough / `boolCode` | none beyond boolean/placeholder | NOT_VERIFIED |

## Summary

| Status | Count |
|---|---|
| VERIFIED | 3 (A0250, J2052 A/B, J2053) |
| NOT_VERIFIED | 49 |
| OPEN_QUESTION | 2 (I0000, J2050) |
| **Total** | **54** |

**COMPLETENESS: NOT_VERIFIED. DENOMINATOR: NOT_VERIFIED.**

Same caveat as `ADM_COMPLETENESS_MATRIX.md`/`HUV1_COMPLETENESS_MATRIX.md`:
the 54-item denominator is an emitted-code count, not a CMS-authority-
confirmed applicable-item count. Retained:

- **CMS item-set version**: NOT_VERIFIED
- **Total applicable items**: NOT_VERIFIED (54 is emitted-code count)
- **Verified items**: 3 (A0250, J2052 A/B, J2053)
- **NOT_VERIFIED items**: 49
- **OPEN_QUESTION items**: 2 (I0000, J2050)
- **Blocked/Excluded items**: 0
- **Reproducible counting command**: none exists (hand-compiled)
