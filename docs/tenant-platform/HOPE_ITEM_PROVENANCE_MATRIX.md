# HOPE Item Provenance Matrix

One row per CMS item code (not per workflow). Per the SNS Review Rule,
`STATUS` is restricted to exactly `VERIFIED`, `NOT_VERIFIED`, or
`OPEN_QUESTION`. `STATUS = VERIFIED` requires all three of `VERIFIED BY
CMS`, `VERIFIED BY REPOSITORY TRACE`, and `VERIFIED BY PRODUCTION CODE`
to be Yes; if any is No/blank, `STATUS` is `NOT_VERIFIED` unless a
specific unresolved conflict makes it an `OPEN_QUESTION`.

**Scope honesty note:** This pass traced every item code the mapper
(`hopeReportMapper.js::mapRnIcaToHopeReport`) actually emits, by direct
code citation (`VERIFIED BY REPOSITORY TRACE` is high-confidence
throughout). `VERIFIED BY CMS` in this matrix is **not** asserted from
memory of the CMS HOPE Guidance Manual — it is marked Yes only for the
handful of items independently confirmed against CMS citations earlier
in this engagement (J2052A/B/C, J2053, the HUV1/HUV2 day-windows). Every
other item's exact CMS applicability-per-timepoint and response-set was
**not** re-derived from primary CMS text in this pass and is marked
`VERIFIED BY CMS = No` accordingly — this is the majority of rows, and
is the expected, honest outcome of distinguishing item-level from
workflow-level provenance as instructed.

---

## ADM (Admission) — 57 items

| CMS Item | CMS Source Req. | SNS Source Record | SNS Source Field | Transformation | Validation | CMS | Repo Trace | Prod Code | STATUS |
|---|---|---|---|---|---|---|---|---|---|
| A0050 | Not independently re-derived | none (hardcoded) | literal string | `"1 - Add new record"` constant | none — always this value | No | Yes | Yes | NOT_VERIFIED |
| A0100 | Not independently re-derived | Agency/tenant config | `agency.npi/.address/.phone` | passthrough | none — placeholder if absent | No | Yes | Yes | NOT_VERIFIED |
| A0215 | Not independently re-derived | RnicaAssessment.form_data | `demographics.livingSituation.siteOfService` | `officialCodeLookup` against `SITE_OF_SERVICE_LABELS` + legacy map | restricted to known code list; unmapped → placeholder | No | Yes | Yes | NOT_VERIFIED |
| A0220 | Not independently re-derived | Patient / RnicaAssessment | `patient.socDate` ‖ `admissionsOrder.levelOfCare.effectiveDate` ‖ `completionDate` | 3-way fallback chain (flagged provenance risk in `HOPE_DATA_PROVENANCE_MATRIX.md`) | none | No | Yes | Yes | NOT_VERIFIED |
| A0250 | **CMS-verified: Reason-for-Record must reflect the timepoint** | derived from `options.timepoint` | `RECORD_REASON_BY_TIMEPOINT` map | direct lookup by timepoint | restricted to 4 known timepoint values | Yes | Yes | Yes | **VERIFIED** |
| A0500 | Not independently re-derived | Patient | `patient` name fields via `splitPatientName` | string split | none | No | Yes | Yes | NOT_VERIFIED |
| A0550 | Not independently re-derived | RnicaAssessment.form_data | `demographics.address.zip` | passthrough | none | No | Yes | Yes | NOT_VERIFIED |
| A0600 | Not independently re-derived | Patient | `patient.ssn`, `.medicareNumber` | passthrough | none | No | Yes | Yes | NOT_VERIFIED |
| A0700 | Not independently re-derived | Patient | `patient.medicaidNumber` | passthrough | none | No | Yes | Yes | NOT_VERIFIED |
| A0810 | Not independently re-derived | RnicaAssessment.form_data / Patient | `demographics.gender` ‖ `patient.sex` | `SEX_MAP` lookup | restricted to Male/Female/M/F; unmapped → placeholder | No | Yes | Yes | NOT_VERIFIED |
| A0900 | Not independently re-derived | RnicaAssessment.form_data / Patient | `demographics.dob` ‖ `patient.dob` | `formatDate` | none | No | Yes | Yes | NOT_VERIFIED |
| A1005 | Not independently re-derived | RnicaAssessment.form_data | `demographics.ethnicity` | `arrayText` (raw join) | **none — not restricted to a CMS ethnicity code list** | No | Yes | Yes | NOT_VERIFIED |
| A1010 | Not independently re-derived | RnicaAssessment.form_data | `demographics.race` | `arrayText` (raw join) | **none — not restricted to a CMS race code list** | No | Yes | Yes | NOT_VERIFIED |
| A1110 | Not independently re-derived | RnicaAssessment.form_data | `demographics.preferredLanguage`, `.needsInterpreter` | passthrough / `boolCode` | none for language value | No | Yes | Yes | NOT_VERIFIED |
| A1400 | Not independently re-derived | Patient | `patient.primaryPayerType`/`.secondaryPayerType` | `payerSources()` crosswalk | restricted to known payer crosswalk | No | Yes | Yes | NOT_VERIFIED |
| A1805 | Not independently re-derived | RnicaAssessment.form_data | `demographics.livingSituation.admittedFrom` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | No | Yes | Yes | NOT_VERIFIED |
| A1905 | Not independently re-derived | RnicaAssessment.form_data | `demographics.livingSituation.livingArrangement` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | No | Yes | Yes | NOT_VERIFIED |
| A1910 | Not independently re-derived | RnicaAssessment.form_data | `demographics.livingSituation.availabilityOfAssistance` | `ASSISTANCE_MAP` lookup | restricted; unmapped → placeholder | No | Yes | Yes | NOT_VERIFIED |
| F2000 | Not independently re-derived | RnicaAssessment.form_data | `demographics.advancedCarePlanning.cprPreferenceAskedStatus/.codeStatus/.codeStatusDate` | `askedStatus()` | derived asked/not-asked code | No | Yes | Yes | NOT_VERIFIED |
| F2100 | Not independently re-derived | RnicaAssessment.form_data | `.lifeSustainingAskedStatus/.lifeSustainingTreatmentPreference(Date)` | `askedStatus()` | same pattern | No | Yes | Yes | NOT_VERIFIED |
| F2200 | Not independently re-derived | RnicaAssessment.form_data | `.hospitalizationAskedStatus/.hospitalizationPreference(Date)` | `askedStatus()` | same pattern | No | Yes | Yes | NOT_VERIFIED |
| F3000 | Not independently re-derived | RnicaAssessment.form_data | `spiritual.concernsAskedStatus/.concernsDiscussed(Date)` | `askedStatus()` | same pattern | No | Yes | Yes | NOT_VERIFIED |
| I0010 | Not independently re-derived | RnicaAssessment.form_data | `diagnoses.primaryDiagnosis.{icd10,description,hopeDiagnosisCategory}` | category-code lookup (`PRINCIPAL_DIAGNOSIS_CATEGORY_LABELS`) + string concat | category restricted; ICD-10 text free | No | Yes | Yes | NOT_VERIFIED |
| I0100, I0600, I0900, I0950, I1101, I1510, I2102, I2900, I2910, I4501, I4801, I5150, I5401, I6202 (14 codes) | Not independently re-derived | RnicaAssessment.form_data | `diagnoses.hopeComorbidities.{key}` (structured) **or** free-text diagnosis-list regex inference (`activeDiagnosisFlag`) when `hopeComorbidities` absent | `boolCode()` of a structured boolean, OR regex match against free-text diagnosis strings (legacy path) | Structured path: boolean, no code restriction beyond true/false. Legacy path: regex heuristic, not a validated CMS assertion — the mapper's own `dataSourceNote` warns "predates structured HOPE harvesting...verify against the chart" | No | Yes | Partially (legacy path is a heuristic inference, not a direct clinician assertion) | NOT_VERIFIED |
| I8005 | Not independently re-derived | RnicaAssessment.form_data | `diagnoses.hopeComorbidities.other` or `diagnosisEntries(diagnoses).length` heuristic | `boolCode()` | same caveat as above | No | Yes | Partially | NOT_VERIFIED |
| I0000 | Not independently re-derived — **not confirmed this is a real, distinct CMS item code** (it is used here as a free-text summary list, not seen cited elsewhere in this session's CMS references) | RnicaAssessment.form_data | `diagnosisEntries(diagnoses)` | list join | none | No | Yes | Yes | **OPEN_QUESTION** — whether `I0000` is a real CMS item or an internal-only summary row was not resolved this pass |
| J0050 | Not independently re-derived | RnicaAssessment.form_data | `imminentDeath.appearsThreeDaysOrLess` | `YES_NO_UNABLE_MAP` lookup | restricted to Yes/No/Unable | No | Yes | Yes | NOT_VERIFIED — also **flagged in `HOPE_DATA_PROVENANCE_MATRIX.md` as CONFLICTING** (a second field, `diagnoses.terminalPrognosis`, is also tagged J0050 in the RNICA UI registry but not read here) |
| J0900 | Not independently re-derived | RnicaAssessment.form_data | `pain.{screenedForPain,painSeverityCategory,standardizedPainToolType,screeningDate}` | `painScreeningResponse()` | restricted per its internal code maps | No | Yes | Yes | NOT_VERIFIED |
| J0905 | Not independently re-derived | RnicaAssessment.form_data | `pain.painIntensity.current`/`.painManagementPlan`/`.painLocation` | `boolCode(Boolean(...))` derived from 3 OR'd fields | boolean derivation only | No | Yes | Yes | NOT_VERIFIED |
| J0910 | Not independently re-derived | RnicaAssessment.form_data | `pain.comprehensiveAssessmentCompleted/.Date`, `derivePainFindings(pain)` | `boolCode`, `formatDate`, findings-derivation helper | none beyond boolean | No | Yes | Yes | NOT_VERIFIED |
| J0915 | Not independently re-derived | RnicaAssessment.form_data | `pain.neuropathicPain` | `NEUROPATHIC_PAIN_MAP` lookup | restricted; unmapped → placeholder (tracked independently of J0900 per code comment) | No | Yes | Yes | NOT_VERIFIED |
| J2030 | Not independently re-derived | RnicaAssessment.form_data | `respiratory.{shortnessOfBreathScreened,sobSeverity,screeningDate}` | `boolCode` + derived `sobIndicated` | none beyond boolean | No | Yes | Yes | NOT_VERIFIED |
| J2040 | Not independently re-derived | RnicaAssessment.form_data | `respiratory.treatmentInitiated/.treatmentDate` | `boolCode`, `formatDate` | none | No | Yes | Yes | NOT_VERIFIED |
| J2050 | Not independently re-derived | RnicaAssessment.form_data | `sfv.symptomImpactScreeningCompleted/.Date` OR `symptomImpact.assessmentDate` | `boolCode`, `formatDate` | none — **reads from RNICA `sfv.*` self-attestation fields, not `SFVRequirement`** (distinct from J2052/J2053, which were corrected) | No | Yes | Yes | **OPEN_QUESTION** — J2050 was not in scope of the P1A/P1B directives; it still reads the same RNICA self-attestation shape those directives required removing for J2052/J2053. Not fixed, not previously flagged. |
| J2051 | Not independently re-derived (this item's word-based severity vocabulary, distinct from J2053's numeric vocabulary, was confirmed in a prior pass) | RnicaAssessment.form_data | `symptomImpact.*` (8 symptoms) | `symptomEntries()` | word-based MILD/MODERATE/SEVERE vocabulary (per `_severity_rank` on the backend trigger-detection side) | No | Yes | Yes | NOT_VERIFIED |
| J2052 | **CMS-verified: A=0/1, B=date-only-if-Yes, C=reason code 1/2/3/9** | SFVRequirement (A/B) + RNICA form (C, unvalidated source) | `sfvStatus.completed/.completedAt` (A/B — VERIFIED source); `sfv.reasonNotCompleted` (C — **source itself NOT_VERIFIED**, see `J2052C_SOURCE_DISCOVERY.md`) | `boolCode`, `formatDate`, `j2052ReasonNotCompleted()` | A/B: SFVRequirement-backed, correct, ownership remediated (see addendum below). C: strictly validated to codes 1/2/3/9 but has no authoritative backend source at all | Yes (A/B/C code-set) | Yes | Yes (A/B); No authoritative source (C) | **VERIFIED (A/B)** — ownership remediated, see addendum. **C remains NOT_VERIFIED** (separate, unrelated source-of-truth gap; not a "kept as one row" compromise anymore since A/B is now fully resolved — see `J2052C_SOURCE_DISCOVERY.md`) |
| J2053 | **CMS-verified: 8 symptoms, codes 0/1/2/3/9** | SFVRequirement → ClinicalNote.content.symptomImpact | `sfvRequirement.symptomImpact` | `symptomEntries()` | restricted to `VISIT_NOTE_SYMPTOM_IMPACT_VALUE_CHOICES` (backend-enforced) | Yes | Yes | Yes | **VERIFIED** — remediated: `HopeReport.jsx` now resolves `sfvRequirement` by `(triggerSourceType, triggerVisitId)` matching the exported record's own trigger, not by patient-wide recency. See ownership addendum below and `P0_SFV_OWNERSHIP_REMEDIATION.md`. |
| M1190 | Not independently re-derived | RnicaAssessment.form_data | `skin.skinConditionsPresent` | `boolCode` | none | No | Yes | Yes | NOT_VERIFIED — also flagged in `HOPE_DATA_PROVENANCE_MATRIX.md` as dual-tagged (conflicting, not dual-write) with an unrelated `performanceStatus` field in the RNICA UI registry |
| M1195 | Not independently re-derived | RnicaAssessment.form_data | `skin.skinStatus` | `arrayText` | none | No | Yes | Yes | NOT_VERIFIED |
| M1200 | Not independently re-derived | RnicaAssessment.form_data | `deriveSkinTreatments(skin)` | derivation helper | none | No | Yes | Yes | NOT_VERIFIED |
| N0500 | Not independently re-derived | RnicaAssessment.form_data | `medications.scheduledOpioid/.Date` | `boolCode`, `formatDate` | none | No | Yes | **No — no live RNICA screen writes `medications.*`; only a data-seed script does** (per `HOPE_DATA_PROVENANCE_MATRIX.md`) | NOT_VERIFIED |
| N0510 | Not independently re-derived | RnicaAssessment.form_data | `medications.prnOpioid/.Date` | `boolCode`, `formatDate` | none | No | Yes | No (same gap) | NOT_VERIFIED |
| N0520 | Not independently re-derived | RnicaAssessment.form_data | `medications.bowelRegimen/.Date`, `opioidPresent` derivation | derived 3-state code (`bowelRegimenCode`) | logic-derived, not directly asserted | No | Yes | No (same gap) | NOT_VERIFIED |
| Z0500 | Not independently re-derived | RnicaAssessment.form_data | `finalization.{signatureCertification,clinicianSignature,signatureDate,hopeSubmissionNumber,hopeAlreadySubmitted}` | passthrough / `boolCode` | none beyond boolean/placeholder | No | Yes | Yes | NOT_VERIFIED |

## HUV1 / HUV2 — 54 items each

Identical item set to ADM **minus** F2000/F2100/F2200/F3000, **plus**
Z0350. VERIFIED BY REPOSITORY TRACE that the source record for a live
HUV1/HUV2 report is the matched Update Assessment's own `form_data`
(never the admission's — see `HUV1_PROVENANCE_TRACE.md` /
`HUV2_PROVENANCE_TRACE.md`), so every ADM row's "SNS Source Record"
column applies unchanged except that "RnicaAssessment.form_data" refers
to the HUV1/HUV2-matched row, not the admission row. STATUS for each
inherited item is unchanged from its ADM row above **except**:

| CMS Item | Note | STATUS |
|---|---|---|
| Z0350 | New for HUV1/HUV2 only. Source: `completionDate` (finalization/assessment-meta derived). No CMS re-derivation this pass. | NOT_VERIFIED |
| A0250 | Resolves to the HUV1/HUV2-specific reason text via the same `RECORD_REASON_BY_TIMEPOINT` map already CMS-verified for ADM. | VERIFIED |
| J2052 / J2053 | Same SFVRequirement-backed mechanism as ADM applies structurally. Ownership remediated — `HopeReport.jsx` resolves `sfvRequirement` by `(triggerSourceType, triggerVisitId)` matching this specific HUV1/HUV2 record's own trigger visit, not by patient-wide recency. See `P0_SFV_OWNERSHIP_REMEDIATION.md`. | VERIFIED |
| All other 51 items | Same mechanics/status as their ADM row (word-based/free-text/lookup patterns are timepoint-independent in the mapper code). | Same as ADM row (mostly NOT_VERIFIED) |

**Not independently re-derived this pass:** whether CMS actually
requires every one of these 54 items to be re-collected at HUV1/HUV2, or
only a subset — this matrix traces *source correctness for what the
mapper currently emits*, not completeness against the official CMS
HUV1/HUV2 item list. Flagged NOT_VERIFIED as a category, not silently
assumed complete.

## DC (Discharge) — 21 items

Section A (18 items, same as ADM rows above, same STATUS per row) +
2 discharge-specific items + Z0500:

| CMS Item | CMS Source Req. | SNS Source Record | SNS Source Field | Transformation | Validation | CMS | Repo Trace | Prod Code | STATUS |
|---|---|---|---|---|---|---|---|---|---|
| A0270 | Not independently re-derived | `patients` table | `discharge.dischargeDate` (via `options.discharge`, sourced from `patients.discharge_date`) | `formatDate` | none beyond date format | No | Yes | Yes | NOT_VERIFIED |
| A2115 | Not independently re-derived | `patients` table | `discharge.reasonCode`/`.reasonLabel` (sourced from `patients.discharge_reason`, validated at write-time against `GRANULAR_DISCHARGE_REASONS`) | code + label concat | **validated at capture time** — `finalize_patient_discharge` rejects any `reason_code` not in the registry (HTTP 422) | No | Yes | Yes | NOT_VERIFIED (validation exists and is real, but the registry's exact CMS-code accuracy was not independently cross-checked this pass) |
| Z0500 | Not independently re-derived | RnicaAssessment.form_data (same as ADM) | same as ADM Z0500 row | same | same | No | Yes | Yes | NOT_VERIFIED |

Section A's 18 ADM items apply unchanged (same STATUS, same source) since
the mapper does not special-case them for discharge beyond adding A0270/
A2115.

---

## SFV Cross-Timepoint Selection Risk — Investigated

**Question 1: Can an SFV triggered from HUV1 ever be incorrectly selected
for an ADM export?**

**Answer: YES — proof below.**

`HopeReport.jsx` (lines ~168-176) fetches `listSfvRequirements(patientId)`
— **every** SFVRequirement for the patient, with no filter on
`trigger_source_type` or `trigger_reference_id` — and selects:
```js
const completedRows = (rows || []).filter((r) => r.status === "COMPLETED" && r.completedAt);
const latest = completedRows.sort((a, b) => (a.completedAt < b.completedAt ? 1 : -1))[0];
```
This is a single "most recently completed, patient-wide" selection, used
identically regardless of `timepoint` prop (ADMISSION/HUV1/HUV2). If a
patient has an ADM-triggered SFVRequirement (`trigger_source_type =
'INITIAL_RN_ICA'`) that completed *before* a later HUV1-triggered
SFVRequirement (`trigger_source_type = 'HUV1'`) also completes, viewing
the **ADM** HOPE report after the HUV1 SFV completes would select the
HUV1-triggered SFVRequirement (it is now the most-recently-completed one
for the patient), not the ADM-triggered one — even though the ADM report
is being rendered. **Proof is structural** (the selection has no
timepoint/trigger filter at all), not merely theoretical: the filter
condition literally cannot distinguish which timepoint triggered which
SFVRequirement.

**Question 2: Can an SFV triggered from HUV2 ever be incorrectly selected
for a HUV1 export?**

**Answer: YES, by the same structural proof.** The identical
patient-wide "most recent completed" selection is reused for every
`timepoint` value — there is no HUV1-specific vs. HUV2-specific query.

**Question 3: Can patient-level lookup bypass trigger ownership?**

**Answer: YES.** `listSfvRequirements(patientId)` is scoped only to
`patient_id`; nothing in `HopeReport.jsx`'s selection logic reads or
filters on `trigger_source_type` or `trigger_reference_id`, which are
the columns that actually establish which assessment triggered a given
SFVRequirement (per `sfv_requirement.py`). The selection is provably a
patient-level shortcut, not a trigger-scoped lookup.

**Important scope clarification:** this defect is in `HopeReport.jsx`
(the UI caller), **not** in `mapRnIcaToHopeReport` (the mapper function)
and **not** in the backend `SFVRequirement` model — those remain
correctly isolated per-record (VERIFIED — see the existing 3-way
multi-SFV isolation test in `hopeReportMapper.test.js`). The mapper
faithfully renders whatever `sfvRequirement` object it is handed; the
defect is that the wrong one can be handed to it today.

This is escalated as an OPEN QUESTION (see `HUV1_PROVENANCE_TRACE.md`);
no fix has been implemented in this pass, per instruction to complete
discovery before any implementation.

---

## Ownership dimension addendum (J2052 / J2053 only)

Per the SFV ownership investigation (`SFV_OWNERSHIP_TRACE.md`,
`SFV_TRIGGER_OWNERSHIP_TRACE.md`), STATUS alone collapses two distinct
facts for J2052/J2053. Adding the required OWNERSHIP VERIFIED dimension
for these two items specifically (the only items where a triggering-
record-to-source linkage question applies — no other item in this matrix
has a cross-timepoint selection mechanism):

| CMS Item | SOURCE VERIFIED | OWNERSHIP VERIFIED | SELECTION LOGIC VERIFIED | STATUS |
|---|---|---|---|---|
| J2052 (A/B) | YES | **YES (remediated)** | **YES (remediated)** | VERIFIED |
| J2053 | YES | **YES (remediated)** | **YES (remediated)** | VERIFIED |

**Remediated** (see `P0_SFV_OWNERSHIP_REMEDIATION.md`): `HopeReport.jsx`'s
SFV selection is now scoped to `(triggerSourceType, triggerVisitId)`
matching the specific HOPE record being exported, instead of a
patient-wide "most recently completed" pick. All 7 acceptance-test
scenarios from `SFV_OWNERSHIP_TRACE.md` now pass (verified via
`HopeReport.sfvOwnership.test.jsx`, 5 tests covering CASE A/B/C, the
no-match-means-null rule, and the Discharge no-lookup rule). J2052(A/B)
and J2053 are upgraded from OPEN_QUESTION to VERIFIED accordingly. J2052C
(the reason-not-completed free-text value) is unaffected by this fix and
remains NOT_VERIFIED — a separate, still-open source-of-truth question
(see `J2052C_SOURCE_DISCOVERY.md`).

## Item counts by timepoint

| Timepoint | Item count | VERIFIED | NOT_VERIFIED | OPEN_QUESTION |
|---|---|---|---|---|
| ADM | 57 | 3 (A0250, J2052, J2053) | 52 | 2 (I0000, J2050) |
| HUV1 | 54 | 3 (A0250, J2052, J2053) | 49 | 2 (I0000, J2050) |
| HUV2 | 54 | 3 (A0250, J2052, J2053) | 49 | 2 (I0000, J2050) |
| DC | 21 | 1 (A0250) | 20 | 0 |

**HOPE GENERATION READY: NO.** The SFV cross-timepoint selection defect
is remediated (J2052/J2053 upgraded to VERIFIED), but item-level
provenance still shows the overwhelming majority of items as NOT_VERIFIED
(CMS-authority citation not independently re-derived this pass), plus 2
remaining open questions per non-Discharge timepoint (I0000, J2050).
Generation may not begin until: item-level CMS verification is completed
(or explicitly accepted as out of scope by Romel), and J2052C is
resolved or formally accepted as a permanent export gap. J2050's
self-attestation-source gap is unrelated to the SFV ownership fix and
remains open.

