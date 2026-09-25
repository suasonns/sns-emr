# HUV1 Completeness Matrix

Status: Item-level completeness review, HUV1 (first Hospice Update
Visit) — 54 items. Identical item set to ADM minus F2000/F2100/F2200/
F3000 (advance-care-planning items not re-collected at HUV1), plus
Z0350. Source record confirmed as the matched Update Assessment's own
`form_data` (never the admission's) per `HUV1_PROVENANCE_TRACE.md`. This
matrix reformats the already-completed HUV1 item trace on file in
`HOPE_ITEM_PROVENANCE_MATRIX.md`; no new repository research was
performed.

| CMS Item | SNS Source Record | SNS Source Field | Transformation | Validation | STATUS |
|---|---|---|---|---|---|
| A0050 | none (hardcoded) | literal string | `"1 - Add new record"` constant | none — always this value | NOT_VERIFIED |
| A0100 | Agency/tenant config | `agency.npi/.address/.phone` | passthrough | none — placeholder if absent | NOT_VERIFIED |
| A0215 | RnicaAssessment(HUV1).form_data | `demographics.livingSituation.siteOfService` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | NOT_VERIFIED |
| A0220 | Patient / RnicaAssessment(HUV1) | `patient.socDate` ‖ `admissionsOrder.levelOfCare.effectiveDate` ‖ `completionDate` | 3-way fallback chain | none | NOT_VERIFIED |
| A0250 | derived from `options.timepoint` | `RECORD_REASON_BY_TIMEPOINT` map | direct lookup by timepoint | restricted to 4 known timepoint values | **VERIFIED** |
| A0500 | Patient | `patient` name fields via `splitPatientName` | string split | none | NOT_VERIFIED |
| A0550 | RnicaAssessment(HUV1).form_data | `demographics.address.zip` | passthrough | none | NOT_VERIFIED |
| A0600 | Patient | `patient.ssn`, `.medicareNumber` | passthrough | none | NOT_VERIFIED |
| A0700 | Patient | `patient.medicaidNumber` | passthrough | none | NOT_VERIFIED |
| A0810 | RnicaAssessment(HUV1).form_data / Patient | `demographics.gender` ‖ `patient.sex` | `SEX_MAP` lookup | restricted; unmapped → placeholder | NOT_VERIFIED |
| A0900 | RnicaAssessment(HUV1).form_data / Patient | `demographics.dob` ‖ `patient.dob` | `formatDate` | none | NOT_VERIFIED |
| A1005 | RnicaAssessment(HUV1).form_data | `demographics.ethnicity` | `arrayText` (raw join) | none | NOT_VERIFIED |
| A1010 | RnicaAssessment(HUV1).form_data | `demographics.race` | `arrayText` (raw join) | none | NOT_VERIFIED |
| A1110 | RnicaAssessment(HUV1).form_data | `demographics.preferredLanguage`, `.needsInterpreter` | passthrough / `boolCode` | none for language value | NOT_VERIFIED |
| A1400 | Patient | `patient.primaryPayerType`/`.secondaryPayerType` | `payerSources()` crosswalk | restricted to known payer crosswalk | NOT_VERIFIED |
| A1805 | RnicaAssessment(HUV1).form_data | `demographics.livingSituation.admittedFrom` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | NOT_VERIFIED |
| A1905 | RnicaAssessment(HUV1).form_data | `demographics.livingSituation.livingArrangement` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | NOT_VERIFIED |
| A1910 | RnicaAssessment(HUV1).form_data | `demographics.livingSituation.availabilityOfAssistance` | `ASSISTANCE_MAP` lookup | restricted; unmapped → placeholder | NOT_VERIFIED |
| I0010 | RnicaAssessment(HUV1).form_data | `diagnoses.primaryDiagnosis.{icd10,description,hopeDiagnosisCategory}` | category-code lookup + string concat | category restricted; ICD-10 text free | NOT_VERIFIED |
| I0100...I6202 (14 codes) | RnicaAssessment(HUV1).form_data | `diagnoses.hopeComorbidities.{key}` (structured) or regex inference (legacy) | `boolCode()` OR regex heuristic | structured: boolean only; legacy: heuristic | NOT_VERIFIED |
| I8005 | RnicaAssessment(HUV1).form_data | `diagnoses.hopeComorbidities.other` or heuristic | `boolCode()` | same caveat | NOT_VERIFIED |
| I0000 | ~~RnicaAssessment(HUV1).form_data~~ N/A | ~~`diagnosisEntries(diagnoses)`~~ | N/A | N/A | **RESOLVED (Issue #147)** — not a CMS item; excluded from the applicable-item count. Retained as internal `SNS-DX` row (non-CMS) |
| J0050 | RnicaAssessment(HUV1).form_data | `imminentDeath.appearsThreeDaysOrLess` | `YES_NO_UNABLE_MAP` lookup | restricted | NOT_VERIFIED — flagged CONFLICTING |
| J0900 | RnicaAssessment(HUV1).form_data | `pain.{screenedForPain,painSeverityCategory,standardizedPainToolType,screeningDate}` | `painScreeningResponse()` | restricted per internal code maps | NOT_VERIFIED |
| J0905 | RnicaAssessment(HUV1).form_data | `pain.painIntensity.current`/`.painManagementPlan`/`.painLocation` | `boolCode(Boolean(...))` | boolean derivation only | NOT_VERIFIED |
| J0910 | RnicaAssessment(HUV1).form_data | `pain.comprehensiveAssessmentCompleted/.Date` | `boolCode`, `formatDate`, `derivePainFindings()` | none beyond boolean | NOT_VERIFIED |
| J0915 | RnicaAssessment(HUV1).form_data | `pain.neuropathicPain` | `NEUROPATHIC_PAIN_MAP` lookup | restricted; unmapped → placeholder | NOT_VERIFIED |
| J2030 | RnicaAssessment(HUV1).form_data | `respiratory.{shortnessOfBreathScreened,sobSeverity,screeningDate}` | `boolCode` + derived `sobIndicated` | none beyond boolean | NOT_VERIFIED |
| J2040 | RnicaAssessment(HUV1).form_data | `respiratory.treatmentInitiated/.treatmentDate` | `boolCode`, `formatDate` | none | NOT_VERIFIED |
| J2050 | RNICA `sfv.*` self-attestation / `symptomImpact` | `sfv.symptomImpactScreeningCompleted` (sole source, OR-fallback removed) / `sfv.symptomImpactScreeningDate ‖ symptomImpact.assessmentDate` | `boolCode`, `formatDate` | A. Completed derives solely from the completion flag (Issue #148 fix) | **RESOLVED (Issue #148)** — no longer OPEN_QUESTION |
| J2051 | RnicaAssessment(HUV1).form_data | `symptomImpact.*` (8 symptoms) | `symptomEntries()` | word-based MILD/MODERATE/SEVERE vocabulary | NOT_VERIFIED |
| J2052 (A/B) | SFVRequirement | `sfvStatus.completed/.completedAt` | `boolCode`, `formatDate` | ownership remediated — resolved via `(triggerSourceType='HUV1', triggerVisitId)` matching this record's own trigger visit | **VERIFIED** |
| J2052 (C) | RNICA form (unvalidated) | `sfv.reasonNotCompleted` | `j2052ReasonNotCompleted()` | restricted to 1/2/3/9, no authoritative backend source | NOT_VERIFIED (see `J2052C_DECISION_RECORD.md`) |
| J2053 | SFVRequirement → ClinicalNote.content.symptomImpact | `sfvRequirement.symptomImpact` | `symptomEntries()` | backend-enforced value choices; ownership remediated | **VERIFIED** |
| M1190 | RnicaAssessment(HUV1).form_data | `skin.skinConditionsPresent` | `boolCode` | none | NOT_VERIFIED |
| M1195 | RnicaAssessment(HUV1).form_data | `skin.skinStatus` | `arrayText` | none | NOT_VERIFIED |
| M1200 | RnicaAssessment(HUV1).form_data | `deriveSkinTreatments(skin)` | derivation helper | none | NOT_VERIFIED |
| N0500 | RnicaAssessment(HUV1).form_data | `medications.scheduledOpioid/.Date` | `boolCode`, `formatDate` | none | NOT_VERIFIED — no live RNICA screen writes `medications.*` |
| N0510 | RnicaAssessment(HUV1).form_data | `medications.prnOpioid/.Date` | `boolCode`, `formatDate` | none | NOT_VERIFIED (same gap) |
| N0520 | RnicaAssessment(HUV1).form_data | `medications.bowelRegimen/.Date`, `opioidPresent` derivation | derived 3-state code | logic-derived | NOT_VERIFIED (same gap) |
| Z0350 | Finalization/assessment-meta derived | `completionDate` | passthrough/date derivation | none | NOT_VERIFIED — new item vs. ADM, no CMS re-derivation this pass |
| Z0500 | RnicaAssessment(HUV1).form_data | `finalization.{signatureCertification,clinicianSignature,signatureDate,hopeSubmissionNumber,hopeAlreadySubmitted}` | passthrough / `boolCode` | none beyond boolean/placeholder | NOT_VERIFIED |

## Summary

| Status | Count |
|---|---|
| VERIFIED | 3 (A0250, J2052 A/B, J2053) |
| RESOLVED (Issues #147/#148) | 2 (I0000 — excluded, non-CMS; J2050 — resolved) |
| NOT_VERIFIED | 49 |
| OPEN_QUESTION | 0 |
| **Total (applicable CMS items)** | **53** (54 emitted rows minus I0000) |

**COMPLETENESS: NOT_VERIFIED. DENOMINATOR: NOT_VERIFIED.**

**Update (2026-09-24, Issues #147/#148 sync):** I0000 and J2050 resolved
per PR #163/#162 — same disposition as `ADM_COMPLETENESS_MATRIX.md`. No
other rows re-reviewed in this update; remaining 49 `NOT_VERIFIED` rows
are unchanged pending the full Issue #150 CMS primary-source pass.

Same caveat as `ADM_COMPLETENESS_MATRIX.md`: the 54-item denominator is
an emitted-code count, not a CMS-authority-confirmed applicable-item
count (no CMS HOPE Item Set document exists in this repository — see
`I0010_PRINCIPAL_DIAGNOSIS_PROVENANCE_TRACE.md` Section A). Retained:

- **CMS item-set version**: **VERIFIED BY CMS** — HOPE Guidance Manual
  v1.02, effective October 1, 2025 (`HOPE_CMS_AUTHORITY_SOURCE_REGISTER.md`).
  A CMS document is externally verified and was read directly for I0010
  and Section J items relevant to HUV1, but the full HUV1 item set was
  not individually re-derived page-by-page against v1.02 this pass —
  that remains the scope of issue #150.
- **Total applicable items**: NOT_VERIFIED (53 real-CMS-item count after excluding I0000)
- **Verified items**: 3 (A0250, J2052 A/B, J2053)
- **NOT_VERIFIED items**: 49
- **OPEN_QUESTION items**: 0 (both resolved — see update above)
- **Blocked/Excluded items**: 1 (I0000 — non-CMS, excluded)
- **Reproducible counting command**: none exists (hand-compiled)
