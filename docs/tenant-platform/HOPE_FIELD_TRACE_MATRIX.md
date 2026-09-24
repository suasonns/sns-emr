# HOPE Field Trace Matrix (Phase 2, independent re-trace)

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED — findings in this document are not yet fixed. See `RNICA_PHASE3_REMEDIATION_REGISTER.md` for defect IDs and current status.

**Scope:** every HOPE item code declared in
`backend/app/domain/forms/form_registry.py:341-418 (HOPE_ADMIN 341-362, PREFERENCES 364-369, DIAGNOSIS 371-376, SYMPTOM 378-395, SFV 397-400, SKIN 402-406, MEDICATION 408-412, FINALIZATION 414-418)`, traced to the frontend
field path(s) that populate it, the UI control that writes it, the backend
extraction function (if any), the exporter line that emits it, and its test
coverage.

**Repository state inspected:** `suasonns/sns-emr`, branch
`suasonns-fantastic-memory`, commit `16264cf` (`git log --oneline -1` →
`16264cf fix(rnica): fix ReferenceError in SEVERITY_COLORS module constant`).

**Method:** repository-only. Every cell is derived from a direct read or a
repository-wide `Select-String` scan performed in this pass. No claim is
carried forward from the prior pass without re-derivation.

**Status vocabulary:** VERIFIED_COMPLETE, PRESENT_CORRECTLY_PLACED,
PRESENT_MISPLACED, PRESENT_RESPONSE_SET_INCOMPLETE, PRESENT_NOT_HARVESTED,
PRESENT_NOT_WIRED, DUPLICATE_OF_FACESHEET, DUPLICATE_EDITABLE_AUTHORITY,
MISSING_FROM_SNS, NOT_APPLICABLE, NOT_FOUND_IN_REPOSITORY, CONFLICTING,
REQUIRES_AUTHORITY_REVIEW, NOT_VERIFIED.

---

## 0. Global result that applies to every row

A repository-wide scan of `backend/` for any function that reads an RNICA
`form_data` clinical **value** and assembles a HOPE item-code-keyed payload
returned **no match**. Backend HOPE code is exclusively:

| Backend HOPE surface | File:line | What it actually does |
|---|---|---|
| Item-code metadata constants | `backend/app/domain/forms/form_registry.py:341-418` | Declares lists of code strings only |
| Metadata attachment | `form_registry.py:446-453, 506, 544, 923, 937` | Copies those lists into form metadata |
| Metadata getters | `form_registry.py:1137-1145, 1148-1156` | Returns the code list for a form/trigger; never touches `form_data` |
| Submission workflow status | `backend/app/services/rnica_hope_workflow_service.py:25-200` | Tracks submissionNumber / alreadySubmitted / close / ready / export / unlock; only `form_data["finalization"]` submission bookkeeping (`:45-51, 95-99`) |
| SFV/HUV trigger engine | `backend/app/services/hope_phase_b_engine.py:1-470` | Creates SFV/HUV tasks from J2051 impact severity; emits no HOPE payload |
| HOPE workflow endpoints | `backend/app/api/visits.py:1358-1478` | Workflow-status mutations only |

Therefore the **"backend extraction function" column is `NONE FOUND` for
every single item code below**, and every row's harvest authority is
`sns-emr-frontend/src/intake/hopeReportMapper.js`. This is recorded once
here rather than repeated 55 times.

---

## 1. Section A — Administrative (`HOPE_ADMIN_ITEM_CODES`, form_registry.py:341-362)

| Item code | Section | Frontend field path(s) | Reachable from UI? | Backend extraction | Exporter file:line | Test coverage | Status |
|---|---|---|---|---|---|---|---|
| A0050 | Admin | none (hard-coded `"1 - Add new record"`) | N/A — constant | NONE FOUND | `hopeReportMapper.js:554` | NONE FOUND | NOT_APPLICABLE |
| A0100 | Admin | `agency.npi/.ccn/.facilityId` (caller-supplied) | No — agency config, not RNICA | NONE FOUND | `hopeReportMapper.js:555` | NONE FOUND | PRESENT_CORRECTLY_PLACED |
| A0215 | Admin | `demographics.livingSituation.siteOfService` | Yes — official code map + legacy crosswalk `hopeReportMapper.js:58-73, 105-122` | NONE FOUND | `hopeReportMapper.js:556` | `hopeReportMapper.test.js:369-389` | PRESENT_CORRECTLY_PLACED |
| A0220 | Admin | `patient.socDate` → `admissionsOrder.levelOfCare.effectiveDate` → `completionDate` | Partly — third fallback is the signature date | NONE FOUND | `hopeReportMapper.js:557` | NONE FOUND | REQUIRES_AUTHORITY_REVIEW |
| A0250 | Admin | `options.timepoint` | N/A — caller option | NONE FOUND | `hopeReportMapper.js:558` (map `:38-43`) | `hopeReportMapper.test.js:112` | PRESENT_CORRECTLY_PLACED |
| A0270 | Admin | `options.discharge.dischargeDate` | No RNICA control (discharge caller only) | NONE FOUND | `hopeReportMapper.js:561` | NONE FOUND | PRESENT_NOT_WIRED |
| A0500 | Admin | `patient.firstName/.lastName/.middleInitial` | Facesheet-sourced (`splitPatientName` `:328-340`) | NONE FOUND | `hopeReportMapper.js:565` | NONE FOUND | PRESENT_CORRECTLY_PLACED |
| A0550 | Admin | `demographics.address.zip` | Yes — `RNICA.jsx:8015` | NONE FOUND | `hopeReportMapper.js:566` | NONE FOUND | DUPLICATE_EDITABLE_AUTHORITY |
| A0600 | Admin | `patient.ssn`, `patient.medicareNumber` | Facesheet-sourced | NONE FOUND | `hopeReportMapper.js:567` | NONE FOUND | PRESENT_CORRECTLY_PLACED |
| A0700 | Admin | `patient.medicaidNumber` | Facesheet-sourced | NONE FOUND | `hopeReportMapper.js:568` | NONE FOUND | PRESENT_CORRECTLY_PLACED |
| A0810 | Admin | `demographics.gender` ‖ `patient.sex` | Yes — `RNICA.jsx:7987-7988` (6 values incl. Non-binary/Other/Declined) vs `SEX_MAP` 2 values (`hopeReportMapper.js:49-54`) | NONE FOUND | `hopeReportMapper.js:569` | NONE FOUND | PRESENT_RESPONSE_SET_INCOMPLETE |
| A0900 | Admin | `demographics.dob` ‖ `patient.dob` | Yes — `RNICA.jsx:7988`; also editable on Facesheet | NONE FOUND | `hopeReportMapper.js:570` | NONE FOUND | DUPLICATE_EDITABLE_AUTHORITY |
| A1005 | Admin | `demographics.ethnicity` | Yes — `RNICA.jsx:7994-7995` (3 options) | NONE FOUND | `hopeReportMapper.js:571` (`arrayText`, no code lookup) | NONE FOUND | PRESENT_RESPONSE_SET_INCOMPLETE |
| A1010 | Admin | `demographics.race` | Yes — `RNICA.jsx:7992-7993` (6 options) | NONE FOUND | `hopeReportMapper.js:572` (`arrayText`, no code lookup) | NONE FOUND | PRESENT_RESPONSE_SET_INCOMPLETE |
| A1110 | Admin | `demographics.preferredLanguage`, `.needsInterpreter` | Yes — `RNICA.jsx:7997-7999` | NONE FOUND | `hopeReportMapper.js:573` | NONE FOUND | PRESENT_RESPONSE_SET_INCOMPLETE ("Other" has no free-text companion, `:7997-7998`) |
| A1400 | Admin | `patient.primaryPayerType`, `.secondaryPayerType` (Facesheet) | No RNICA control by design; crosswalk `hopeReportMapper.js:152-183` | NONE FOUND | `hopeReportMapper.js:574` | `hopeReportMapper.test.js:542-601` | PRESENT_CORRECTLY_PLACED |
| A1805 | Admin | `demographics.livingSituation.admittedFrom` | Yes — official code map `hopeReportMapper.js:76-92` | NONE FOUND | `hopeReportMapper.js:575` | `hopeReportMapper.test.js:408-432` | PRESENT_CORRECTLY_PLACED |
| A1905 | Admin | `demographics.livingSituation.livingArrangement` | Yes — official code map `hopeReportMapper.js:95-103` | NONE FOUND | `hopeReportMapper.js:576` | `hopeReportMapper.test.js:445-471` | PRESENT_CORRECTLY_PLACED |
| A1910 | Admin | `demographics.livingSituation.availabilityOfAssistance` | Yes — but plain `lookup()` on `ASSISTANCE_MAP` (`:182-190`), not `officialCodeLookup()` | NONE FOUND | `hopeReportMapper.js:577` | NONE FOUND | NOT_VERIFIED (codes unconfirmed against CMS — see AUTHORITY_APPLICABILITY_REGISTER.md) |
| A2115 | Admin | `options.discharge.reasonCode/.reasonLabel` | No RNICA control | NONE FOUND | `hopeReportMapper.js:562` | NONE FOUND | PRESENT_NOT_WIRED |

## 2. Section F — Preferences (`HOPE_PREFERENCES_ITEM_CODES`, form_registry.py:364-369)

| Item code | Section | Frontend field path(s) | Reachable from UI? | Backend extraction | Exporter file:line | Test coverage | Status |
|---|---|---|---|---|---|---|---|
| F2000 | Preferences | `demographics.advancedCarePlanning.cprPreferenceAskedStatus`, `.codeStatus`, `.codeStatusDate` | Yes (`askedStatus()` `hopeReportMapper.js:311-325`) | NONE FOUND | `hopeReportMapper.js:586` | `hopeReportMapper.test.js:106,159,219-221,269-270,290,345` | PRESENT_CORRECTLY_PLACED |
| F2100 | Preferences | `...lifeSustainingAskedStatus`, `.lifeSustainingTreatmentPreference(+Date)` | Yes | NONE FOUND | `hopeReportMapper.js:587` | `...test.js:132,170,233-234,291` | PRESENT_CORRECTLY_PLACED |
| F2200 | Preferences | `...hospitalizationAskedStatus`, `.hospitalizationPreference(+Date)` | Yes | NONE FOUND | `hopeReportMapper.js:588` | `...test.js:140,181,242-243,292` | PRESENT_CORRECTLY_PLACED |
| F3000 | Preferences | `spiritual.concernsAskedStatus`, `.concernsDiscussed(+Date)`, `.spiritualConcerns`, `.notes` | Yes | NONE FOUND | `hopeReportMapper.js:589` | `...test.js:148,189,251-252,293` | PRESENT_CORRECTLY_PLACED |

> Note: the whole Section F block is filtered out of HUV1/HUV2 output
> (`hopeReportMapper.js:657`), consistent with `HOPE_HUV_ITEM_CODES`
> excluding `HOPE_PREFERENCES_ITEM_CODES` (`form_registry.py:430-441`).

## 3. Section I — Diagnoses (`HOPE_DIAGNOSIS_ITEM_CODES`, form_registry.py:371-376)

| Item code | Section | Frontend field path(s) | Reachable from UI? | Backend extraction | Exporter file:line | Test coverage | Status |
|---|---|---|---|---|---|---|---|
| I0010 | Diagnoses | `diagnoses.primaryDiagnosis.hopeDiagnosisCategory`, `.icd10`, `.description` | Yes | NONE FOUND | `hopeReportMapper.js:598-601` (labels `:124-137`) | `hopeReportMapper.test.js:499-520` | PRESENT_CORRECTLY_PLACED |
| I0600 | Diagnoses | `diagnoses.hopeComorbidities.heartFailure` (structured) ‖ regex over the diagnosis list (legacy) | Yes — `RNICA.jsx:2633` checkbox loop over `HOPE_COMORBIDITY_CATEGORIES:2499` | NONE FOUND | `hopeReportMapper.js:539-541, 545` | NONE FOUND | PRESENT_CORRECTLY_PLACED |
| I6202 | Diagnoses | `diagnoses.hopeComorbidities.copd` | Yes — same loop | NONE FOUND | `hopeReportMapper.js:539-541, 546` | NONE FOUND | PRESENT_CORRECTLY_PLACED |
| I8005 | Diagnoses | `diagnoses.hopeComorbidities.other` | **Yes** — dedicated checkbox `RNICA.jsx:2668`; default `RNICA.jsx:534` | NONE FOUND | `hopeReportMapper.js:542, 547` | NONE FOUND | PRESENT_CORRECTLY_PLACED (prior "dead path" claim refuted — see DEAD_EXPORT_PATH_ANALYSIS.md) |

Additional comorbidity codes are emitted by the mapper but are **not**
declared in `form_registry.py`: I0100, I0900, I0950, I1101, I1510, I2102,
I2900, I2910, I4501, I4801, I5150, I5401 (`hopeReportMapper.js:440-453`) and
the group row `I0000` (`:603`). Each is reachable via the same checkbox loop
(`RNICA.jsx:2633`), but the backend registry does not declare them →
`CONFLICTING` between exporter inventory and registry inventory.

## 4. Section J — Symptoms (`HOPE_SYMPTOM_ITEM_CODES`, form_registry.py:378-395)

| Item code | Section | Frontend field path(s) | Reachable from UI? | Backend extraction | Exporter file:line | Test coverage | Status |
|---|---|---|---|---|---|---|---|
| J0050 | Symptoms | `imminentDeath.appearsThreeDaysOrLess` | Yes | NONE FOUND | `hopeReportMapper.js:609` | NONE FOUND | CONFLICTING — `diagnoses.terminalPrognosis` is also tagged `hopeCode: "J0050"` (`RNICA.jsx:8925`) but never read by the mapper |
| J0900 | Symptoms | `pain.screenedForPain`, `.painSeverityCategory`, `.standardizedPainToolType`, `.screeningDate` | Yes (`painScreeningResponse()` `:221-268`) | NONE FOUND | `hopeReportMapper.js:610` | `hopeReportMapper.test.js:625-717` | PRESENT_CORRECTLY_PLACED |
| J0905 | Symptoms | derived from `pain.painIntensity.current`, `.painManagementPlan`, `.painLocation` | Derived, not directly answerable | NONE FOUND | `hopeReportMapper.js:611` | NONE FOUND | PRESENT_NOT_WIRED (no discrete control for the CMS item) |
| J0910 | Symptoms | `pain.comprehensiveAssessmentCompleted`, `.comprehensiveAssessmentDate`, `derivePainFindings()` `:342-350` | Yes | NONE FOUND | `hopeReportMapper.js:612` | NONE FOUND | PRESENT_CORRECTLY_PLACED |
| J0915 | Symptoms | `pain.neuropathicPain` | Yes | NONE FOUND | `hopeReportMapper.js:613` | `hopeReportMapper.test.js:728-764` | PRESENT_CORRECTLY_PLACED |
| J2030 | Symptoms | `respiratory.shortnessOfBreathScreened`, `.sobSeverity`, `.screeningDate` | Yes | NONE FOUND | `hopeReportMapper.js:614` | NONE FOUND | PRESENT_CORRECTLY_PLACED |
| J2040 | Symptoms | `respiratory.treatmentInitiated`, `.treatmentDate` | Yes | NONE FOUND | `hopeReportMapper.js:615` | NONE FOUND | PRESENT_CORRECTLY_PLACED |
| J2050 | Symptoms | `sfv.symptomImpactScreeningCompleted`, `.symptomImpactScreeningDate` ‖ `symptomImpact.assessmentDate` | Yes — `RNICA.jsx:9396-9397` | NONE FOUND | `hopeReportMapper.js:616` | NONE FOUND | PRESENT_CORRECTLY_PLACED |
| J2051A-H | Symptoms | `symptomImpact.{pain,shortnessOfBreath,anxiety,nausea,vomiting,diarrhea,constipation,agitation}` (`IMPACT_KEYS` `:292-301`) | Yes | NONE FOUND | `hopeReportMapper.js:617` via `symptomEntries()` `:384-392` | NONE FOUND | PRESENT_CORRECTLY_PLACED |
| (J2051 as a single code) | Symptoms | same | — | NONE FOUND | `hopeReportMapper.js:617` emits code `"J2051"`, while `form_registry.py:386-394` declares `J2051A`-`J2051H` | NONE FOUND | CONFLICTING (code-granularity mismatch registry vs exporter) |

## 5. SFV (`HOPE_SFV_ITEM_CODES`, form_registry.py:397-400)

| Item code | Section | Frontend field path(s) | Reachable from UI? | Backend extraction | Exporter file:line | Test coverage | Status |
|---|---|---|---|---|---|---|---|
| J2052 | SFV | `sfv.inPersonSfvCompleted`, `.sfvDate`, `.reasonNotCompleted` | Yes — `RNICA.jsx:9398-9400` | NONE FOUND (task-side lifecycle only, `hope_phase_b_engine.py:377-430`) | `hopeReportMapper.js:618` | NONE FOUND | CONFLICTING — self-attested on the triggering form; backend forbids same-visit completion (`hope_phase_b_engine.py:409-410`) |
| J2053 | SFV | `sfv.symptomImpactAtSfv.*` | Yes — `RNICA.jsx:9403-9410` | NONE FOUND | `hopeReportMapper.js:619` | NONE FOUND | PRESENT_CORRECTLY_PLACED |

## 6. Section M — Skin (`HOPE_SKIN_ITEM_CODES`, form_registry.py:402-406)

| Item code | Section | Frontend field path(s) | Reachable from UI? | Backend extraction | Exporter file:line | Test coverage | Status |
|---|---|---|---|---|---|---|---|
| M1190 | Skin | `skin.skinConditionsPresent` | Yes | NONE FOUND | `hopeReportMapper.js:625` | NONE FOUND | CONFLICTING — `SIDEBAR_CONFIG` also tags M1190 on `performanceStatus` (`RNICA.jsx:209`) |
| M1195 | Skin | `skin.skinStatus[]` | Yes | NONE FOUND | `hopeReportMapper.js:626` | NONE FOUND | PRESENT_RESPONSE_SET_INCOMPLETE |
| M1200 | Skin | `skin.woundImpairment`, `skin.notes` (`deriveSkinTreatments()` `:352-357`) | Yes | NONE FOUND | `hopeReportMapper.js:627` | NONE FOUND | PRESENT_NOT_HARVESTED (structured wound rows at `RNICA.jsx:9360` are not read) |

## 7. Section N — Medications (`HOPE_MEDICATION_ITEM_CODES`, form_registry.py:408-412)

| Item code | Section | Frontend field path(s) | Reachable from UI? | Backend extraction | Exporter file:line | Test coverage | Status |
|---|---|---|---|---|---|---|---|
| N0500 | Medications | `medications.scheduledOpioid`, `.scheduledOpioidDate` | **No** — `medications` is absent from `FORM_REGISTRY` (`RNICA.jsx:242-249`); no writer found anywhere except a seed script (`backend/scripts/populate_loren_shields.py:563`) | NONE FOUND | `hopeReportMapper.js:633` | NONE FOUND | CONFLICTING (see ITEM_CODE_CONFLICT_MATRIX.md) |
| N0510 | Medications | `medications.prnOpioid`, `.prnOpioidDate` | No — same | NONE FOUND | `hopeReportMapper.js:634` | NONE FOUND | CONFLICTING |
| N0520 | Medications | `medications.bowelRegimen`, `.bowelRegimenDate` (`:529-530`) | No — same | NONE FOUND | `hopeReportMapper.js:635` | NONE FOUND | CONFLICTING |

## 8. Section Z — Finalization (`HOPE_FINALIZATION_ITEM_CODES`, form_registry.py:414-418)

| Item code | Section | Frontend field path(s) | Reachable from UI? | Backend extraction | Exporter file:line | Test coverage | Status |
|---|---|---|---|---|---|---|---|
| Z0350 | Finalization | `finalization.signatureDate` ‖ assessment metadata | Yes (HUV timepoints only, `:641-643`) | NONE FOUND | `hopeReportMapper.js:642` | `hopeReportMapper.test.js:122` | PRESENT_CORRECTLY_PLACED |
| Z0400 | Finalization | — | — | NONE FOUND | **NOT EMITTED** — no `"Z0400"` string exists outside `form_registry.py:416` | NONE FOUND | PRESENT_NOT_HARVESTED |
| Z0500 | Finalization | `finalization.signatureCertification`, `.clinicianSignature`, `.signatureDate`, `.hopeSubmissionNumber`, `.hopeAlreadySubmitted` | Yes — `RNICA.jsx:9719-9720`; submission fields synced server-side (`rnica_hope_workflow_service.py:45-51`) | NONE FOUND (workflow sync only, not item extraction) | `hopeReportMapper.js:644` | NONE FOUND | PRESENT_CORRECTLY_PLACED |

---

## 9. Consumers of the exporter

| Consumer | File:line |
|---|---|
| `HopeReport.jsx` | `sns-emr-frontend/src/intake/HopeReport.jsx:13, 162` |
| `ComplianceHopeBoard.jsx` | `sns-emr-frontend/src/intake/ComplianceHopeBoard.jsx:9, 416` |
| `RNICA.jsx` (SFV + admission status only) | `sns-emr-frontend/src/components/RNICA.jsx:123, 11225` |
| Completion-status derivation | `hopeReportMapper.js:673-714` (`getHopeAdmissionStatus`) |

**Counts:** 55 registry-declared item codes traced; 0 with a backend
extraction function; 13 exporter-emitted codes not declared in the registry;
1 declared code (Z0400) never emitted.
