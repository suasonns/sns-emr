# SNS HOPE Harvest & Compliance Map 1.0

**STATUS: IN PROGRESS**

> **HOPE GOVERNANCE RULE**
>
> RNICA is the authoritative assessment. HOPE is not a separate
> clinician-facing form. All HOPE reporting elements originate from
> RNICA fields through approved mapping, derivation, and validation
> rules. No duplicate clinician documentation shall be required solely
> for HOPE reporting.

## STEP RULE

This document replaces and significantly expands
`SNS_HOPE_HARVEST_RECONCILIATION_1.0` (Phase 2 deliverable). It does not
modify Deliverables #1-#10, does not modify the Master Map, and does not
authorize code changes. Reference screenshots of a third-party system
(HospiceMD) were used **only as UX/workflow guidance** for what a
Compliance module output can look like — item definitions, mapping
types, and gap status are taken from the official CMS HOPE guidance
already summarized in `SNS_RNICA_SECTION_INVENTORY_1.0`'s HOPE Crosswalk
and cross-checked against the frozen SNS Field Inventory / Gap Report /
HOPE Crosswalk Verification. Any item whose current-system status cannot
be confirmed from those frozen sources is marked **UNCONFIRMED**, not
assumed present.

Source artifacts (frozen/Phase-2, unmodified):
- `SNS_RNICA_FIELD_INVENTORY_1.0.md`
- `SNS_RNICA_SECTION_INVENTORY_1.0.md` (HOPE Crosswalk)
- `SNS_RNICA_IMPLEMENTATION_GAP_REPORT_1.0.md`
- `SNS_RNICA_HOPE_CROSSWALK_VERIFICATION_2.0.md`
- `SNS_RNICA_MASTER_MAP_MAPPING_2.0.md`

## Governing Rule (frozen)

```
RNICA CLINICAL ASSESSMENT
+ PATIENT / ADMISSION DATA
+ ORDERS / MEDICATION DATA
+ VISIT / ENCOUNTER DATA
+ DISCHARGE DATA
  ↓
HOPE HARVEST ENGINE
  ↓
VALIDATION + PROVENANCE
  ↓
REPORTING SNAPSHOT
  ↓
HOPE ADMISSION / HUV1 / HUV2 / DISCHARGE
  ↓
QIES SUBMISSION

Parallel outputs:
RNICA + Historical Assessments → LCD ELIGIBILITY WORKSHEET
RNICA + Historical Assessments → DECLINE OF STATUS TREND ENGINE
```

- RNICA is the authoritative clinical assessment.
- HOPE is not a second clinician-facing assessment.
- HOPE clinical values are harvested from RNICA.
- HOPE medication values are harvested from Orders.
- HOPE administrative values are harvested from Patient, Admission,
  Encounter, Provider, and Discharge records.
- Every exported value stores source provenance.
- No duplicate documentation is required solely for HOPE.

## Mapping Type Legend

- **DIRECT** — 1:1 read from a single RNICA (or source module) field.
- **DERIVED** — computed from a workflow/state machine (e.g. SFV
  completion tracking) rather than a raw field read.
- **CALCULATED** — computed from multiple source fields/records (e.g.
  trend deltas, record-type codes).
- **EXTERNAL_AUTHORITATIVE_SOURCE** — sourced from a different module
  that is authoritative for that data (Orders, Patient/Admission,
  Discharge, Agency Configuration) — not RNICA, and not to be
  duplicated into RNICA.
- **GAP** — no source exists in the current system for this item.

"Current status" reflects **what the current SNS codebase actually
implements today** (per the frozen Field Inventory/Gap Report/Crosswalk
Verification), independent of what the target Mapping Type above says
the architecture should be once built.

---

## 1. HOPE Admission Harvest Map

### Section A — Administrative and Demographic Items

| Item ID | Item Name | Source Module | Source Section | Source Field | Mapping Type | Point-in-Time Rule | Current Status | Gap | Notes |
|---|---|---|---|---|---|---|---|---|---|
| A0050 | Type of Record | HOPE Harvest Engine | — | Record-type resolution logic | CALCULATED | Set at export time from reason-for-record context | **UNCONFIRMED** | No record-type resolution engine exists in current codebase | Not part of `rnica_assessments.form_data`; would be new harvest-engine logic |
| A0100 | Provider Numbers | Agency Configuration | — | NPI / CCN / Facility ID | EXTERNAL_AUTHORITATIVE_SOURCE | Static per agency | **UNCONFIRMED** | Out of RNICA scope | Agency profile data, not clinical |
| A0215 | Site of Service at Admission | Patient / Communications & Other Factors | Patient Demographics (or admission workflow) | Not confirmed as a distinct RNICA field | EXTERNAL_AUTHORITATIVE_SOURCE | Point-in-time at admission | **GAP (unconfirmed in RNICA)** | Not identified in Field Inventory | Likely owned by admission/registration module |
| A0220 | Admission Date | Admission | — | SOC/admission date | EXTERNAL_AUTHORITATIVE_SOURCE | Fixed at admission | **Confirmed exists in Visit/Admission record** | None | Not an RNICA `form_data` field |
| A0250 | Reason for Record | HOPE Harvest Engine | — | Admission/HUV1/HUV2/Discharge record-type code | CALCULATED | Set at export time | **UNCONFIRMED** | No harvest-engine record-type logic exists | Ties to `hope_phase_b_engine.py`'s ADM/HUV1/HUV2/DC distinction (used for SFV, not HOPE export) |
| A0500 | Legal Name of Patient | Patient Demographics | — | First/Middle/Last | EXTERNAL_AUTHORITATIVE_SOURCE | Static | **Confirmed** (Patient record) | None | Not RNICA `form_data` |
| A0600 | SSN / Medicare Identifier | Patient Demographics / Payer | — | Identifiers | EXTERNAL_AUTHORITATIVE_SOURCE | Static | **Confirmed** (Patient/Payer record) | None | Out of RNICA scope |
| A0700 | Medicaid Number | Patient Demographics / Payer | — | Identifier | EXTERNAL_AUTHORITATIVE_SOURCE | Static | **Confirmed** (Payer record) | None | Out of RNICA scope |
| A0810 | Sex | Patient Demographics | — | Recorded value | EXTERNAL_AUTHORITATIVE_SOURCE | Static | **Confirmed** | None | Out of RNICA scope |
| A0900 | Birth Date | Patient Demographics | — | DOB | EXTERNAL_AUTHORITATIVE_SOURCE | Static | **Confirmed** | None | Out of RNICA scope |
| A1005 | Ethnicity | RNICA | Patient Demographics | `demographics.ethnicity[]` | DIRECT | Point-in-time at RNICA save | **Confirmed** | None | Validated in `validateRNICA()` |
| A1010 | Race | RNICA | Patient Demographics | `demographics.race[]` | DIRECT | Point-in-time at RNICA save | **Confirmed** | None | Validated in `validateRNICA()` |
| A1110 | Language | RNICA | Patient Demographics | `demographics.preferredLanguage`, `.needsInterpreter` | DIRECT | Point-in-time at RNICA save | **Confirmed** | None | |
| A1805 | Admitted From | RNICA | Patient Demographics (residence type) | Not confirmed as HOPE-coded | EXTERNAL_AUTHORITATIVE_SOURCE / DIRECT (unresolved) | Point-in-time at admission | **GAP (unconfirmed HOPE wiring)** | Residence type exists but not wired to A1805 | Per HOPE Crosswalk §Section A |
| A1905 | Living Arrangements | RNICA | Patient Demographics | Not confirmed as HOPE-coded | DIRECT (unresolved) | Point-in-time at admission | **GAP (unconfirmed HOPE wiring)** | Overlaps Caregiver Assessment; no HOPE code wiring found | Per HOPE Crosswalk §Section A |
| A1910 | Availability of Assistance | RNICA | Caregiver Assessment | Not confirmed as HOPE-coded | DIRECT (unresolved) | Point-in-time at admission | **GAP (unconfirmed HOPE wiring)** | No HOPE code wiring found | Per HOPE Crosswalk §Section A |

### Section F — Preferences

| Item ID | Item Name | RNICA Source Section | RNICA Field | Mapping Type | Current Status | Gap | Notes |
|---|---|---|---|---|---|---|---|
| F2000 | CPR Preference | Demographics → Advanced Care Planning | `demographics.advancedCarePlanning.codeStatus` | DIRECT | **Confirmed in form, BROKEN in sync** | ACP storage-path mismatch — backend extractor reads `form_data.advancedCarePlanning` (top-level), frontend writes `demographics.advancedCarePlanning` (nested) | See `SNS_RNICA_API_MAPPING_1.0` §3.3 and `SNS_RNICA_GAP_VALIDATION_2.0` — sync to `patient_code_statuses` likely silently fails |
| F2100 | Life-Sustaining Treatment Preferences | Demographics → Advanced Care Planning | `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference` | DIRECT | **Confirmed in form, same sync defect** | Same as F2000 | |
| F2200 | Hospitalization Preference | Demographics → Advanced Care Planning | `demographics.advancedCarePlanning.hospitalizationPreference` | DIRECT | **Confirmed in form, same sync defect** | Same as F2000 | |
| F3000 | Spiritual/Existential Concerns | Spiritual | — | DIRECT (target) | **GAP — verified, no RNICA field** | No SIDEBAR_CONFIG hope array references F3000 | Frozen finding, `SNS_RNICA_IMPLEMENTATION_GAP_REPORT_1.0` §1; **F3000 must use the documented discussion response and discussion date; spiritual narrative may support but must not silently replace the coded response** |

### Section I — Diagnoses and Comorbidities

| Item ID | Item Name | RNICA Field | Mapping Type | Current Status | Gap |
|---|---|---|---|---|---|
| I0010 | Principal Diagnosis | `diagnoses.primaryDiagnosis.icd10` | DIRECT | **Confirmed** | None |
| I0100 | Cancer | `diagnoses.hopeComorbidities.cancer` | DIRECT | **Confirmed** | None |
| I0600 | Heart Failure | `diagnoses.hopeComorbidities.heartFailure` | DIRECT | **Confirmed** | None |
| I0900 | PVD/PAD | `diagnoses.hopeComorbidities.pvdPad` | DIRECT | **Confirmed** | None |
| I0950 | Cardiovascular (excl. HF) | `diagnoses.hopeComorbidities.cardiovascularExclHF` | DIRECT | **Confirmed** | None |
| I1101 | Liver Disease | `diagnoses.hopeComorbidities.liverDisease` | DIRECT | **Confirmed** | None |
| I1510 | Renal Disease | `diagnoses.hopeComorbidities.renalDisease` | DIRECT | **Confirmed** | None |
| I2102 | Sepsis | `diagnoses.hopeComorbidities.sepsis` | DIRECT | **Confirmed** | None |
| I2900 | Diabetes Mellitus | `diagnoses.hopeComorbidities.diabetesMellitus` | DIRECT | **Confirmed** | None |
| I2910 | Neuropathy | `diagnoses.hopeComorbidities.neuropathy` | DIRECT | **Confirmed** | None |
| I4501 | Stroke | `diagnoses.hopeComorbidities.stroke` | DIRECT | **Confirmed** | None |
| I4801 | Dementia (incl. Alzheimer's) | `diagnoses.hopeComorbidities.dementia` | DIRECT | **Confirmed** | None |
| I5150 | Neurological Conditions | `diagnoses.hopeComorbidities.neurologicalConditions` | DIRECT | **Confirmed** | None |
| I5401 | Seizure Disorder | `diagnoses.hopeComorbidities.seizureDisorder` | DIRECT | **Confirmed** | None |
| I6202 | COPD | `diagnoses.hopeComorbidities.copd` | DIRECT | **Confirmed** | None |
| I8005 | Other Medical Condition | `diagnoses.hopeComorbidities.other` | DIRECT | **Confirmed** | None |

*Note: the relational Diagnosis record (`patient_diagnoses`, synced via
Diagnoses-sync in `SNS_RNICA_DATABASE_MAPPING_1.0`) remains authoritative
where RNICA synchronizes diagnoses outside `form_data`.*

### Section J — Imminent Death, Pain, Dyspnea, Symptom Impact, SFV

| Item ID | Item Name | RNICA Field | Mapping Type | Current Status | Gap |
|---|---|---|---|---|---|
| J0050 | Death is Imminent | `imminentDeath.appearsThreeDaysOrLess` | DIRECT | **Confirmed, dual-listed** | Also cross-listed under Diagnoses hope array — open reconciliation item, not a missing-field gap |
| J0900 | Pain Screening | `pain.verbalizesPain` | DIRECT | **Confirmed** | None |
| J0905 | Pain Active Problem | — | DIRECT or DERIVED (target) | **GAP — verified** | No RNICA field for "is pain an active problem" |
| J0910 | Comprehensive Pain Assessment | — | DERIVED (target) | **GAP — verified** | No distinct completion-flag field |
| J0915 | Pain Severity / Neuropathic Pain | `pain.uncomfortableBecauseOfPain` | DIRECT | **Confirmed** | None |
| J2030 | SOB Screening | — | DIRECT (target) | **GAP — verified** | No distinct screening-completed/date field; dyspnea findings exist in `respiratory.*` but not wired to J2030 |
| J2040 | SOB Treatment | — | DERIVED (target, from Orders) | **GAP — verified** | No distinct treatment-initiated field |
| J2050 | Symptom Impact Screening | `sfv.*` hope array entry | DIRECT, but **misplaced** | **Confirmed, misplaced** | Belongs conceptually with `symptomImpact` (J2051), not `sfv` — open reconciliation item |
| J2051 (A-H) | Symptom Impact | `symptomImpact.{pain,shortnessOfBreath,anxiety,nausea,vomiting,diarrhea,constipation,agitation}` | DIRECT | **Confirmed** | None — primary SFV trigger source |
| J2052 | SFV Completed / Reason | `sfv.inPersonSfvCompleted`, `.reasonNotCompleted` | DERIVED | **Confirmed** | Tracked via `sfv_requirements` table / `complete_sfv_requirement_from_visit()`, not a raw `form_data` read |
| J2053 | SFV Symptom Impact | `sfv.symptomImpactAtSfv.*` | DIRECT | **Confirmed** | None |

#### J2051 Clinical Source Map

| Symptom | RNICA Source |
|---|---|
| Pain | `pain.*` |
| Shortness of Breath | `respiratory.*` |
| Anxiety | `psychosocial.*` / Neurological |
| Nausea | `gastrointestinal.*` |
| Vomiting | `gastrointestinal.*` |
| Diarrhea | `gastrointestinal.*` |
| Constipation | `gastrointestinal.*` |
| Agitation | `psychosocial.*` / Neurological |

**Rule (target, not yet implemented):** Moderate or severe symptom
impact must create an SFV requirement tied to the originating
screening, due window, assigned visit, completion status, and
reassessment result. **Current status: partially implemented** — the
SFV trigger engine exists (`hope_phase_b_engine.py:319-394`) but reads
from `clinical_notes`, not `rnica_assessments.form_data.symptomImpact` —
see `SNS_RNICA_ACTION_CENTER_TRIGGER_INVENTORY_1.0` and Gap Validation.

### Section M — Skin Conditions and Treatment

| Item ID | Item Name | RNICA Field | Mapping Type | Current Status | Gap |
|---|---|---|---|---|---|
| M1190 | Skin Conditions (gate) | `performanceStatus.pps`/`.kps` (gate) and `skin.*` (dual-listed) | DIRECT | **Confirmed, dual-listed** | Referenced in both `performanceStatus` and `skin` hope arrays — open reconciliation item |
| M1195 | Skin Condition Detail | — | DIRECT or DERIVED (target) | **GAP — verified** | No distinct multi-select "types of skin condition" field |
| M1200 | Skin Treatments | — | DERIVED (target, wound-care Orders where applicable) | **GAP — verified** | No HOPE-coded treatments-checklist field; wound care exists only as free-text/POC |

**Rule (target):** M1190 is the gate. M1195 and M1200 must not be
inferred merely because the Integumentary section was opened — they
require their own captured evidence once built.

### Section N — Medications

| Item ID | Item Name | Authoritative Source | Mapping Type | Current Status | Gap |
|---|---|---|---|---|---|
| N0500 | Scheduled Opioid | Orders / Current Medications | EXTERNAL_AUTHORITATIVE_SOURCE (DERIVED) | **GAP — verified, entire N-section absent** | No RNICA field and no confirmed harvest-from-Orders logic exists today |
| N0510 | PRN Opioid | Orders / Current Medications | EXTERNAL_AUTHORITATIVE_SOURCE (DERIVED) | **GAP — verified** | Same as N0500 |
| N0520 | Bowel Regimen | Orders / Current Medications | EXTERNAL_AUTHORITATIVE_SOURCE (DERIVED) | **GAP — verified** | Same as N0500; also relevant to Gastrointestinal |

**Required provenance per medication item (target, not yet
implemented):** medication/regimen name, order identifier, order date,
effective date, active status at assessment, scheduled/PRN
classification, source order link. **Governance constraint:** each
N-item must be DERIVED from the Orders/Medication Reconciliation module
— RNICA must NOT gain a duplicate opioid/bowel-regimen field, per the
HOPE Governance Rule's "no duplicate clinician documentation"
requirement.

### Section Z — Completion and Attestation

| Item ID | Item Name | Source | Mapping Type | Current Status | Gap |
|---|---|---|---|---|---|
| Z0350 | Date Assessment Completed | `finalization.*` timestamps | DIRECT (target: CALCULATED from validation state) | **Confirmed** | None |
| Z0400 | Signature(s) of Person(s) Completing Record | `finalization.*` signature capture | DIRECT | **Confirmed** | None |
| Z0500 | Signature of Person Verifying Record Completion | — | DIRECT | **Not separately confirmed from Z0400** | Open reconciliation item — may be the same signature capture or a distinct supervisor-review signature |

---

## 2. HUV1 Harvest Map

**Timing:** HUV1 target window = Day 6 through Day 15 after SOC.

| Domain | Items | Source | Current Status |
|---|---|---|---|
| Record metadata | Applicable A-item subset + HUV1 reason-for-record code | Patient, Admission, Encounter, Provider | **UNCONFIRMED** — no record-type/reason-code harvest logic confirmed in current codebase |
| Imminent death | J0050 | RNICA `imminentDeath.appearsThreeDaysOrLess` at HUV1 encounter | **Confirmed field exists**; encounter-tagging UNCONFIRMED |
| Symptom screening | J2050 | RNICA `sfv.*` (misplaced) at HUV1 encounter | **Confirmed field exists, misplaced**; encounter-tagging UNCONFIRMED |
| Symptom impact | J2051 | RNICA `symptomImpact.*` at HUV1 encounter | **Confirmed field exists**; encounter-tagging UNCONFIRMED |
| SFV completion | J2052 | SFV workflow/encounter status | **Confirmed** — `sfv_requirements` / `complete_sfv_requirement_from_visit()` |
| SFV symptom impact | J2053 | RNICA `sfv.symptomImpactAtSfv.*` | **Confirmed** |
| Skin conditions | M1190, M1195, M1200 | HUV1 Integumentary + treatment/order records | M1190 **Confirmed, dual-listed**; M1195/M1200 **GAP — verified** |
| Medications | N0500, N0510, N0520 | Orders active as of the HUV1 assessment | **GAP — verified, entire N-section absent** |
| Completion | Z0350, Z0500 | HUV1 validation and signature | Z0350 **Confirmed**; Z0500 **not separately confirmed** |

**HUV1 Rule:** HUV1 is not copied from Admission. HUV1 is a
point-in-time harvest from HUV1 RNICA findings, active orders as of
HUV1, HUV1/SFV encounter status, and Patient/Admission identifiers. The
reference screenshots and the supplied HUV1 extract show clinical J, M,
and N content in the HUV1 report rather than a full repeat of Admission
demographics, preferences, and diagnoses — this is **UX/workflow
guidance only**; RNICA does not currently implement per-visit
record-type tagging (A0250) to distinguish which submission is "HUV1."

---

## 3. HUV2 Harvest Map

**Timing:** HUV2 target window = Day 16 through Day 30 after SOC.

HUV2 uses the same harvest domains as HUV1: applicable A-item metadata,
J0050, J2050, J2051, J2052, J2053, M1190, M1195, M1200, N0500, N0510,
N0520, Z0350, Z0500. Current-status column is identical to the HUV1
table above — the same fields, the same confirmed/GAP classifications,
the same encounter-tagging UNCONFIRMED note.

**HUV2 Rule:** HUV2 must harvest values as of the HUV2 encounter. HUV2
must not reuse the HUV1 clinical snapshot. The reason-for-record code,
encounter identifier, assessment date, orders-as-of date, and signature
must identify HUV2 independently. **Current status: this
snapshot-independence rule is UNCONFIRMED** — no per-visit
snapshot/versioning mechanism was found in `rnica_assessments` (single
`form_data` blob, no visit-instance history table) per
`SNS_RNICA_DATABASE_MAPPING_1.0`.

---

## 4. HOPE Discharge Harvest Map

The supplied discharge extract is an **administrative closeout record**,
not a repeated clinical HUV assessment.

| Item ID | Item Name | Source | Current Status |
|---|---|---|---|
| A0050 | Type of Record | HOPE Harvest Engine | **UNCONFIRMED** |
| A0100 | Provider Numbers | Agency Configuration | **UNCONFIRMED** (out of RNICA scope) |
| A0220 | Admission Date | Admission | **Confirmed** (Visit/Admission record) |
| A0250 | Reason for Record | Discharge record type | **UNCONFIRMED** — no discharge record-type logic confirmed |
| A0270 | Discharge Date | Discharge | **UNCONFIRMED** — Discharge module exists in RNICA's section list (§28) but discharge-date field wiring to A0270 not confirmed |
| A0500 | Legal Name | Patient Demographics | **Confirmed** (out of RNICA scope) |
| A0600 | SSN / Medicare Identifier | Patient / Payer | **Confirmed** (out of RNICA scope) |
| A0700 | Medicaid Number | Patient / Payer | **Confirmed** (out of RNICA scope) |
| A0810 | Sex | Patient Demographics | **Confirmed** (out of RNICA scope) |
| A0900 | Birth Date | Patient Demographics | **Confirmed** (out of RNICA scope) |
| A2115 | Reason for Discharge | Discharge workflow | **UNCONFIRMED** — not identified as a distinct RNICA field in Field Inventory |
| Signature / completion | — | Authenticated discharge completion | **UNCONFIRMED** |

Discharge must retain the discharge date, reason, author, signature,
and source discharge record. California's current hospice regulations
also require a discharge statement containing the date and reason for
termination and a summary of the patient's status at discharge.

---

## 5. QIES Submission Pipeline (target — not yet implemented)

```
Source Records
  ↓
Harvest Candidate
  ↓
Crosswalk Resolution
  ↓
Point-in-Time Snapshot
  ↓
Validation
  ↓
Exception Queue
  ↓
Clinician / Compliance Review
  ↓
Final Attestation
  ↓
QIES Export
  ↓
Submission Response
  ↓
Correction / Resubmission if required
```

**Current status: GAP — none of this pipeline exists today.** RNICA has
no export/QIES-submission code path; `SNS_RNICA_API_MAPPING_1.0`
confirms only 6 endpoints (save/get/get-by-patient/update/lock/
intelligence), none of which produce a HOPE/QIES export.

### Required Provenance Per Exported Item (target)

Item ID, exported value, mapping type, source module, source record ID,
source field or JSON path, source encounter ID, source order ID (when
applicable), source date, harvest timestamp, derivation version,
validator version, review status, reviewer, attestation timestamp,
submission identifier, submission status, correction history.

**Minimum per-value provenance record (target):**

| Field | Purpose |
|---|---|
| Value | The harvested/exported HOPE value |
| Source RNICA Field | Exact field/JSON path the value was read from |
| Source Assessment Date | Date of the RNICA assessment the value came from |
| Harvest Timestamp | When the harvest engine read/derived the value |
| Validation Status | BLOCKING / WARNING / INFORMATIONAL / PASS (see §9) |

This is the minimum record every exported HOPE value must carry — a bare
value with no source-field, source-date, harvest-timestamp, or
validation-status attached is not sufficient for survey readiness (see
§9 Checkpoint 7).

**Current status: GAP.** No provenance tracking of any kind exists on
`rnica_assessments` beyond `created_at`/`updated_at`/`locked_at` — see
`SNS_RNICA_AUDIT_INVENTORY_1.0` (zero `created_by`/`updated_by` columns,
zero `log_event()` calls in the RNICA handler range).

### QIES Validation Classes (target)

- **BLOCKING** — required data missing or invalid.
- **WARNING** — source exists but requires review.
- **INFORMATIONAL** — derived value or unchanged historical value.
- **PASS** — validated and submission-ready.

**Current status: GAP.** RNICA's only validation classes today are
frontend "error" (blocks Lock) and "warning" (does not block) per
`SNS_RNICA_VALIDATION_INVENTORY_1.0` — there is no submission-readiness
validation tier at all.

---

## 6. LCD Eligibility Worksheet Map

LCD eligibility is a computed worksheet supported by RNICA evidence. It
does not independently certify eligibility and must not replace
physician judgment or the patient-specific narrative.

**Minimum per-criterion display schema (target):** each criterion row
must show **Criterion → Met / Not Met → Evidence → Source Assessment
Link**, not a bare computed checkbox. A criterion marked "Met" with no
linked evidence and no source-assessment link is not survey-ready.
Evidence should reflect the patient-specific findings emphasized by CMS
hospice terminal-prognosis guidance — functional decline, ADL
dependence, PPS/KPS decline, nutritional decline, infections, and
disease-specific findings — not a generic pass/fail flag.

**Current status: GAP.** No criterion in the tables below is currently
rendered with linked evidence or a source-assessment link; the
underlying RNICA fields exist, but there is no LCD worksheet UI, no
Met/Not-Met computation, and no evidence-linking mechanism in the
current codebase.

### Non-Disease-Specific Map

| LCD Criterion | RNICA Source | Current Status |
|---|---|---|
| KPS or PPS below applicable threshold | `performanceStatus.kps`/`.pps` | **Confirmed field exists**; no computed threshold-comparison worksheet exists |
| Dependence in two or more ADLs | ADL fields (Feeding, Ambulation, Continence, Transfer, Bathing, Dressing) | **Confirmed fields exist**; no computed "2+ ADL dependency" flag exists |
| Progressive decline | Historical RNICA comparisons | **Confirmed partially** — only PPS/KPS/FAST/Weight are compared today, via `DeclineTrackerCard` (clipboard-only, not persisted) |
| Increasing utilization | Disease History / hospitalizations / ER visits | **Confirmed fields exist** (Field Inventory §5 Diagnoses); no computed utilization-trend worksheet |
| Comorbidities | `diagnoses.hopeComorbidities.*` | **Confirmed** |

### Dementia Worksheet

| Criterion | RNICA Source | Current Status |
|---|---|---|
| FAST stage 7 or beyond | `performanceStatus.fast` | **Confirmed field exists**; no threshold-comparison logic |
| Ambulation / Dressing / Bathing assistance | ADL fields | **Confirmed fields exist** |
| Urinary and fecal incontinence | ADL / GU / GI fields | **Confirmed fields exist** |
| Six or fewer intelligible words | Neurological / Communication | **Confirmed field exists** (Neurological section) |
| Aspiration pneumonia / Pyelonephritis / Septicemia (past 12 months) | Infection / Disease History | **Confirmed fields exist** (Infection section) |
| Stage 3-4 pressure injuries | Integumentary | **Confirmed field exists** (Skin/Wounds section) |
| Recurrent fever after antibiotics | Infection | **Confirmed field exists** |
| Insufficient intake / weight loss | Nutrition / Vitals | **Confirmed fields exist** |
| Low albumin (when available) | Labs / Nutrition | **GAP — not an RNICA field** (lab-integration dependent) |

### Pulmonary Worksheet

| Criterion | RNICA Source | Current Status |
|---|---|---|
| Dyspnea at rest | Respiratory | **Confirmed field exists** |
| Reduced functional capacity | Mobility / ADL / Performance Status | **Confirmed fields exist** |
| Disease progression / Respiratory hospitalizations | Disease History | **Confirmed fields exist** |
| Oxygen saturation / Oxygen use | Vitals / Respiratory / Orders | **Confirmed fields exist** in Vitals/Respiratory; Orders linkage GAP |
| Hypercapnia (when available) | Labs / external clinical data | **GAP — not an RNICA field** |
| Cor pulmonale / right heart failure | Cardiovascular / Diagnoses | **Confirmed fields exist** |
| Weight loss | Nutrition / Vitals history | **Confirmed fields exist** |
| Resting tachycardia | Vitals / Cardiovascular | **Confirmed field exists** |

### Additional Disease Worksheets (target, not yet built)

Heart disease, ALS, Stroke/coma, Renal disease, Liver disease, HIV,
Cancer, other supported disease pathways — **GAP.** No worksheet-level
computed eligibility logic exists for any disease pathway today; only
the underlying RNICA fields (Diagnoses, Performance Status, clinical
systems) exist, per `SNS_RNICA_MASTER_MAP_1.0` §Section 6.

**Rule:** Do not auto-declare eligibility from a single checkbox. Store
each satisfied, unsatisfied, unavailable, and clinician-explained
criterion separately.

---

## 7. Decline of Status Map

### Required Trend Series

| Trend | RNICA Source | Current Status |
|---|---|---|
| Pain Level | Pain Assessment history | **GAP** — not included in `DeclineTrackerCard`'s calculation (only PPS/KPS/FAST/Weight are) |
| BMI | Height and Weight history | **GAP** — not calculated; only raw weight is compared |
| MAC (mid-arm circumference) | Vitals & Measurements history | **GAP** — no RNICA field for MAC identified in Field Inventory |
| ADL Score | ADL Assessment history | **GAP** — ADL fields are DIRECT-captured but not included in the decline-calculation engine |
| KPS | Performance Status history | **CALCULATED — Confirmed** (current vs. prior, via `GET /patients/{id}/performance-history`) |
| PPS | Performance Status history | **CALCULATED — Confirmed** |
| FAST | Performance Status history | **CALCULATED — Confirmed** (index-based) |
| NYHA | Performance Status history | **GAP** — not included in current calculation engine; not confirmed as an RNICA field at all in Field Inventory |

### Additional High-Value Trends (target, not yet implemented)

Weight (partially confirmed — raw weight delta exists, % change may not
be surfaced), Oxygen saturation, Oxygen rate, Respiratory rate, Dyspnea
severity, Appetite/intake, Pressure-injury stage, Number of active
wounds, Falls, ER visits, Hospitalizations, Infections — **all GAP**.
None of these are included in the current Decline Summary calculation
engine (`RNICA.jsx:2001-2162`), even though most of the underlying
RNICA fields exist individually.

### Full Target Trend Set (superset — exceeds reference-system graph)

The combined target trend set is: **PPS, KPS, FAST, NYHA, ADL Score,
Weight, BMI, MAC, Pain, Dyspnea, Oxygen saturation/use, Falls,
Hospitalizations, Infections.** Every plotted point in every series
must preserve a link back to its source assessment (assessment ID,
assessment date, encounter type) — a trend line with no per-point
source-assessment link is not survey-ready and must not be presented as
proof of decline or eligibility on its own (see §8 "Do Not Copy").
Reference-system parity is a floor, not the target: 6 of the 14 series
above (PPS/KPS/FAST are calculated; Weight is partial) exist today in
some form, the remaining 9 are GAP.

### Trend Requirements (target, not yet implemented)

Preserve native values; do not replace with only a normalized graph;
show baseline/previous/current/delta; display assessment date and
encounter type; allow filtering by benefit period and date range; link
each plotted point to the source assessment; do not imply
improvement/decline when data is missing; distinguish "not assessed"
from zero; flag clinically significant changes for review; do not
automatically determine terminal prognosis.

**Current status: GAP for all of the above.** The current Decline
Summary is a single clipboard-copy sentence with no graph, no
filtering, no source-assessment linking, and no distinction between
"not assessed" and zero — see `SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0`
§1.

---

## 8. Significantly Improved SNS Compliance Workspace (target architecture — not yet built)

```
COMPLIANCE
1. HOPE
   - Admission
   - HUV1
   - HUV2
   - Discharge
   - Validation Exceptions
   - Submission History
   - Corrections
2. LCD Eligibility
   - Non-Disease-Specific
   - Disease-Specific
   - Evidence Worksheet
   - Clinician Narrative
   - Certification Reference
3. Decline of Status
   - Trend Dashboard
   - Graph Data
   - Source Assessment Links
   - Benefit-Period Comparison
```

**Current status: GAP.** No Compliance module of any kind exists in the
current SNS codebase or in `SNS_RNICA_MASTER_MAP_1.0`'s 12-section
architecture — the Master Map's Section 7 (HOPE & Symptom Follow-Up)
covers only in-RNICA HOPE *data entry*, not a separate reporting/
compliance workspace. Adding this workspace is a **new architectural
component**, not covered by the frozen Master Map, and would require a
Version 1.1 governance process per the Master Map's own freeze rule
before being adopted.

### Each HOPE Record Shows (target)

Item ID, item name, harvested value, source module, source record link,
mapping type, validation status, review status, export status,
correction history. **Current status: GAP** — no such record view
exists.

### Do Not Copy From the Reference System

- Do not create a second HOPE data-entry form.
- Do not duplicate medication fields in RNICA.
- Do not hide source provenance.
- Do not flatten missing data to "No."
- Do not overwrite prior HUV snapshots.
- Do not permit silent recalculation after attestation.
- Do not mix LCD criteria with HOPE submission items.
- Do not treat a graph as proof of eligibility.

---

## 9. QIES Submission & Compliance Validation Rules (target — not yet implemented)

**Current status for this entire section: GAP.** As established in §5,
no QIES export pipeline, validation tier, exception queue, or
compliance-checkpoint mechanism exists in the current codebase. The
rules below define what the harvest/validation layer must enforce once
built; none of it is implemented today.

### 9.1 Record-Level Validation

**HOPE Admission** — required before export: A0050, A0100, A0215,
A0220, A0250, A0500, A0810, A0900, A1005, A1010, A1110, F2000, F2100,
F2200, I0010, J2050, J2051, Z0500. Validation: all required items
populated; all mapped RNICA sources exist; all harvested values carry
provenance (§5); clinician attestation present. Failure: **BLOCK
SUBMISSION**.

**HUV1** — window: SOC + Day 6 through Day 15. Required: J0050, J2050,
J2051, J2052, J2053, M1190, M1195 (if applicable), M1200 (if
applicable), N0500, N0510, N0520, Z0500. Validation: visit occurred
inside the HUV1 window; snapshot date preserved; Orders active as of
the assessment date. Failure: **BLOCK SUBMISSION**.

**HUV2** — window: SOC + Day 16 through Day 30. Required fields mirror
HUV1 (§2/§3 confirm the item set is structurally identical). Validation:
independent harvest; independent signature; independent snapshot; **no
reuse of HUV1 data** — a HUV2 record populated from a copied/rolled-over
HUV1 snapshot fails validation even if all fields are technically
populated. Failure: **BLOCK SUBMISSION**.

**Discharge** — required: A0270, A2115, Z0500. Validation: discharge
date exists; discharge reason exists; record signed. Failure: **BLOCK
SUBMISSION**.

| Record | Required Fields | Timing Window | Failure |
|---|---|---|---|
| Admission | A0050, A0100, A0215, A0220, A0250, A0500, A0810, A0900, A1005, A1010, A1110, F2000, F2100, F2200, I0010, J2050, J2051, Z0500 | At admission | **BLOCK SUBMISSION** |
| HUV1 | J0050, J2050, J2051, J2052, J2053, M1190, M1195\*, M1200\*, N0500, N0510, N0520, Z0500 | SOC + Day 6-15 | **BLOCK SUBMISSION** |
| HUV2 | Same set as HUV1 (independent harvest — no reuse of HUV1 values) | SOC + Day 16-30 | **BLOCK SUBMISSION** |
| Discharge | A0270, A2115, Z0500 | At discharge | **BLOCK SUBMISSION** |

\* M1195/M1200 required only when M1190 = Yes / treatment documented, per §9.2 Skin Validation.

### 9.2 HOPE Item Validation Rules

**Symptom Validation** — for Pain, SOB, Anxiety, Nausea, Vomiting,
Diarrhea, Constipation, Agitation (J2051 item set). Allowed values: Not
At All, Slight, Moderate, Severe, Not Applicable. Any other value:
**submission blocked**.

**SFV Validation** — if any J2051 item = Moderate or Severe, SFV is
required. Validate: SFV completed **or** exception documented. Failure
if neither: routes to Level 2 Compliance Review (§9.4), not a hard
block.

**Skin Validation** — if M1190 = Yes, M1195 is required; if treatment is
documented, M1200 is required. Failure: **Validation Error**.

**Medication Validation** — if N0500 = Yes, require an active scheduled
opioid order with Order ID and Order Date; if N0510 = Yes, require an
active PRN opioid order; if N0500 **or** N0510 = Yes, require an N0520
bowel-regimen review. This is the harvest-time enforcement of the
DERIVED order-linkage already noted for N0500/N0510/N0520 in §1 and
§2/§3 (order-number references observed in reference-system evidence,
not yet built in SNS).

### 9.3 LCD Compliance Validation

Validate supporting evidence for PPS, KPS, FAST, ADLs, Comorbidities,
decline evidence, and disease-specific evidence (Dementia, Heart
Disease, Pulmonary, ALS, Stroke/Coma, Renal, Liver, HIV pathways — §6
Non-Disease-Specific/Dementia/Pulmonary worksheets are built here; the
remaining pathways are §6's "Additional Disease Worksheets," still
GAP). This validation is evidentiary — it confirms a criterion has
linked, patient-specific support — not a substitute for the Met/Not-Met
+ Evidence + Source-Assessment-Link display already required in §6.

### 9.4 Exception Handling Procedures

| Level | Examples | Action |
|---|---|---|
| **1 — Blocking** | Missing required HOPE item, missing signature, invalid HUV timing, missing discharge date, invalid provider identifiers | Prevent QIES export; prevent submission; require correction |
| **2 — Compliance Review** | Missing RNICA source, missing provenance, missing SFV, missing medication linkage, missing LCD evidence | Mark Compliance Review Required; hold submission; notify reviewer |
| **3 — Warning** | Historical value unchanged, optional value missing, narrative mismatch, non-critical exception | Allow submission; log warning |

### 9.5 QIES Exception Queue (record schema, target)

Patient, Assessment, HOPE Record Type, HOPE Item, Error Category, Error
Message, Source RNICA Field, Assessment Date, Created Date, Assigned
Reviewer, Status, Resolution Notes, Resolved By, Resolution Date.

Statuses: **Open, In Review, Resolved, Waived, Rejected.**

### 9.6 Compliance Checkpoints

| Checkpoint | Verifies |
|---|---|
| 1 — Assessment Complete | RNICA complete; required sections complete; required signatures complete |
| 2 — Harvest Validation | Every HOPE value traces to an RNICA source or an authoritative external source; no orphaned values |
| 3 — Eligibility Evidence | PPS, KPS, FAST, ADLs, Comorbidities, decline evidence, disease-specific evidence |
| 4 — QIES Ready | No blocking errors; no unresolved compliance-review items; signature present; snapshot locked |
| 5 — Submission | Export successful; submission ID returned; transmission logged |
| 6 — Post-Submission | Acceptance confirmed; corrections tracked; audit history preserved |
| 7 — Survey Readiness | For any submitted HOPE item, demonstrate: HOPE Item → Source RNICA Field → Assessment Date → Clinician Signature → Submission ID |

Checkpoint 1 aligns with California hospice regulations requiring
comprehensive assessment documentation, plan-of-care support, symptom
documentation, safety documentation, and maintained medical records.
Checkpoint 3 aligns with CMS hospice guidance emphasizing
patient-specific evidence, functional decline, ADL dependence,
performance scores, nutritional decline, infections, and
disease-specific criteria supporting terminal prognosis. Checkpoint 7 is
the enforcement point for the per-value provenance record defined in §5
("Required Provenance Per Exported Item") — a value that cannot be
traced through all four links is not survey-ready, consistent with
documentation-traceability, assessment-support, plan-of-care linkage,
symptom-documentation, and record-retention expectations for hospice
compliance.

**Current status for §9.1-9.6: GAP.** None of these validation classes,
exception levels, queue records, or checkpoints exist in the current
codebase; today's only validation is the frontend error/warning tier
noted in `SNS_RNICA_VALIDATION_INVENTORY_1.0`, which governs Lock, not
QIES submission (which does not exist).

---

## 10. Major Remaining Gaps (Consolidated)

This section consolidates the gaps scattered across §1-§9 into the 12
gaps that actually determine whether SNS is compliance-ready — as
distinct from cosmetic/UI improvements. Each entry cross-references the
section(s) where the underlying evidence for the gap already appears in
this document.

| # | Gap | Missing | Current State | See |
|---|---|---|---|---|
| 1 | QIES Submission Engine | Harvest, Validation, Exception Queue, Snapshot Locking, Export, Submission Tracking, Correction Workflow | No confirmed QIES pipeline of any kind | §5, §9 |
| 2 | HOPE Provenance | HOPE Value → Source RNICA Field → Assessment Date → Harvest Timestamp → Validation Status | No per-item source tracking | §5 |
| 3 | HUV Snapshot Architecture | Admission Snapshot, HUV1 Snapshot, HUV2 Snapshot, Discharge Snapshot | No confirmed immutable reporting snapshots | §1-§4 |
| 4 | Compliance Exception Queue | Blocking Errors, Compliance Review, Warnings, Assignment, Resolution Workflow | No dedicated compliance queue | §9.4, §9.5 |
| 5 | LCD Evidence Worksheet | Criterion → Evidence → Assessment Link → Source Field | Current LCD logic is criteria-evaluation only, not evidence-linked | §6 |
| 6 | Disease-Specific LCD Engines | Structured evidence support for Dementia, ALS, Heart Disease, Pulmonary Disease, Stroke/Coma, Renal Disease, Liver Disease, HIV | Only Dementia and Pulmonary worksheets are mapped (partially); the rest have no worksheet logic | §6 |
| 7 | Decline of Status Expansion | BMI, MAC, ADL Score, NYHA, Pain, Dyspnea, Falls, Hospitalizations, Infections, Oxygen | Only PPS, KPS, FAST, Weight are in the current calculation | §7 |
| 8 | Point-to-Point Traceability | RNICA Field → HOPE Item → Submission Record → Submission ID | No chain exists past the RNICA field itself | §5, §9.6 (Checkpoint 7) |
| 9 | Order-Based Medication Harvest | Authoritative linkage for N0500 Scheduled Opioid, N0510 PRN Opioid, N0520 Bowel Regimen from Orders (not duplicated assessment fields) | No Orders-linkage mechanism confirmed | §1, §9.2 |
| 10 | Compliance Workspace | Integrated module: HOPE Admission, HUV1, HUV2, Discharge, LCD Eligibility, Decline of Status, Exceptions, Submission History, Corrections | No Compliance module exists; not in the frozen Master Map's 12 sections | §8 |
| 11 | Survey Defense Package | Consolidated HOPE Item, Source Field, Assessment Date, Clinician, Signature, Submission ID per reported value | No consolidated view answering "where did this value come from?" | §5, §9.6 (Checkpoint 7) |
| 12 | Automated Significant-Change Monitoring | Structured monitoring for weight decline, pain increase, cognition loss, appetite decline, functional decline, with escalation and documentation support | No automated significant-change monitoring exists; California regulations require processes around significant changes in condition and notifications | §7 |

**Priority framing:** Gaps 1-4 and 8 (engine, provenance, snapshots,
exception queue, traceability) are structural prerequisites — none of
Gaps 5-7, 9, 11, or 12 can be made survey-ready without them. Gap 10
(Compliance Workspace) is the presentation layer that depends on Gaps
1-9 and 11-12 being resolved first, and per §8 requires a Version 1.1
governance process before it can be added to the frozen Master Map.

**Current status for all 12 gaps: GAP.** None are implemented in the
current codebase; this table introduces no new findings beyond what
§1-§9 already establish — it only re-orders them by compliance
materiality instead of by document section.

---

## 11. Build Priority (Corrected)

**CORRECTION:** the earlier version of this section sequenced Priority 1
as a standalone QIES/HOPE Infrastructure program. That was wrong and is
superseded below. **RN ICA is the product.** HOPE Admission, HUV1,
HUV2, HOPE Discharge, LCD Eligibility, Decline of Status, Clinical
Narrative, and Master POC are **outputs generated from RN ICA** — none
of them are a standalone module to be built first, and none of them
justify a second clinician-facing assessment form. Build priority
follows the RN ICA lifecycle, not the reporting-engine lifecycle.

**RN ICA Purpose:** RN ICA is the admission assessment and clinical
baseline. HOPE Admission, LCD Eligibility, and Decline of Status are in
scope not because they are separate compliance projects, but because
the admission assessment can be used immediately to (1) generate HOPE
Admission data, (2) establish the initial Decline of Status baseline,
(3) establish the initial LCD evidence baseline, (4) generate the
initial Narrative, and (5) generate the initial Master Plan of Care.
Nothing here is forced: nothing requires future visits to exist, and
nothing about completing RN ICA creates HUV1 or HUV2.

### Priority 1 — RN ICA Build

Implement the approved Facesheet-style RN ICA structure (SNS Design
System 1.0) with autosave, section completion status, current/previous
findings, per-section clinical comments, per-section POC controls, a
persistent Admission Action Center, and finalize/sign/lock/
correction/amendment behavior. Preserve every current RNICA field,
validation, HOPE item reference, clinical data record, existing API
behavior (until replacement parity is proven), audit history, and
provider identity/permission control. Use forward-only migrations; do
not overwrite migration history.

This also carries the data-normalization work required for every
downstream output: every reportable RNICA value must be addressable by
Assessment ID, Patient ID, Encounter ID, RNICA section, field/JSON
path, value, assessment date, author, signature status, and last
modification timestamp — added as the minimum safe structure on top of
the existing `form_data` JSONB record, not a wholesale re-normalization.

This is the prerequisite for every other priority: none of Priorities
2-4 can be built against an RN ICA that does not yet capture and
address its own data reliably.

### Priority 2 — RN ICA Outputs, Subsequent-Encounter Outputs, and Longitudinal Outputs

**RN ICA ROLE (correction):** RN ICA is the hospice Start of Care /
Admission assessment. RN ICA does **not** generate HUV1. RN ICA does
**not** generate HUV2. RN ICA does **not** become the HUV visit. HUV1
and HUV2 are separate follow-up visit encounters with their own
documentation, timing rules, assessment findings, signatures, and HOPE
outputs. This corrects the prior wording in this section, which listed
HUV1/HUV2 as if they were generated from the Admission RN ICA itself.

**What RN ICA provides:** Admission baseline, clinical baseline,
functional baseline, ADL baseline, symptom baseline, PPS/KPS/FAST
baseline, weight/BMI/MAC baseline, initial POC, initial narrative, and
the initial HOPE Admission dataset — the source framework, clinical
evidence model, and longitudinal comparison baseline against which
later visits and cumulative outputs are built.

**Tier 1 — RN ICA Outputs** (generated directly from the completed SOC
assessment):

1. **HOPE Admission** — harvested from RN ICA, Patient/Admission,
   Agency configuration, Diagnoses, Code Status, Preferences, Orders/
   Medications, and signature data. The clinician must not re-enter
   anything already documented in RN ICA or another authoritative
   module.
2. **Initial Clinical Narrative** — generated only after the full SOC
   assessment is complete, from terminal diagnosis, related diagnoses,
   comorbidities, hospitalizations/ER visits, pain/symptom burden,
   respiratory findings, functional status, ADLs, PPS/KPS/FAST/NYHA,
   weight/BMI/MAC, nutritional intake, infections, integumentary
   findings, falls, psychosocial/spiritual/caregiver findings. Remains a
   draft until reviewed and signed by the RN.
3. **Initial Master Plan of Care** — every qualifying clinical section
   supports Add/View/Update/Resolve POC, synchronized to one
   authoritative Master POC via Assessment finding → Problem → Goal →
   Intervention → Discipline → Visit frequency → Task → Master POC.
   Every POC problem retains its originating assessment, section,
   finding, author, dates, status, and related orders/actions. No
   duplicate POC records.
4. **Baseline LCD Evidence** — the SOC data point for the LCD
   Eligibility worksheet (non-disease-specific decline, KPS/PPS, ADL
   dependence, FAST, weight/nutrition, MAC/BMI, hospitalizations/ER
   visits, infections, pressure injuries, comorbidities, plus
   disease-specific pathways). Every criterion must display Met / Not
   Met / Not Assessed / Not Available / Clinician Explanation /
   Supporting Evidence / Source Assessment Link.
5. **Baseline Decline Measurements** — the SOC data point for the
   Decline of Status graph: PPS, KPS, FAST, NYHA, ADL total,
   complete-ADL-dependence count, Weight, BMI, MAC, Pain, Dyspnea,
   Oxygen saturation/rate, Falls, Hospitalizations, ER visits,
   Infections, pressure-injury stage, active wound count.

**Tier 2 — Related Outputs From Subsequent Encounters** (generated from
their own visit encounters, not from the Admission RN ICA):

- **HOPE HUV1** — HUV1 Visit → new visit documentation → HOPE HUV1.
  Generated from the HUV1 visit encounter (Day 6-15 post-SOC),
  harvesting administrative metadata, J/M/N/Z items at that encounter;
  medication values sourced from active Orders as of the HUV1
  assessment date. Must not copy the Admission clinical snapshot (§2
  "HUV1 Rule"). **When a HUV1 visit occurs:** capture the HUV1 visit
  data → generate HOPE HUV1 → update Decline of Status → update
  Narrative if applicable.
- **HOPE HUV2** — HUV2 Visit → new visit documentation → HOPE HUV2.
  Generated from its own independent encounter, assessment date,
  harvest, orders-as-of date, signature, and reporting snapshot (Day
  16-30 post-SOC). Must not reuse or overwrite HUV1 (§3 "HUV2 Rule").
  **When a HUV2 visit occurs:** capture the HUV2 visit data → generate
  HOPE HUV2 → update Decline of Status → update Narrative if
  applicable.
- **HOPE Discharge** — Discharge Visit → discharge documentation →
  HOPE Discharge. Administrative-only, from Patient identity, Admission
  date, Provider information, Discharge date/reason/record, and
  authenticated completion data. Not a second comprehensive RN
  assessment (§4). **When discharge occurs:** capture discharge data →
  generate HOPE Discharge → finalize longitudinal reporting.

**RN ICA establishes:** HOPE Admission capability, Decline of Status
baseline, LCD evidence baseline, Narrative baseline, Master POC
baseline. Subsequent encounters (HUV1, HUV2, Discharge) contribute
additional data when they occur — RN ICA does **not** create HUV1. RN
ICA does **not** create HUV2. Completing RN ICA starts monitoring; it
does not schedule, require, or generate the follow-up visits
themselves.

**Tier 3 — Longitudinal Outputs** (generated from the cumulative patient
record — RN ICA + HUV1 data + HUV2 data + subsequent visits + Orders +
Diagnoses + Discharge information — not a one-time SOC artifact):

- **LCD Eligibility** — extends Tier 1's Baseline LCD Evidence using RN
  ICA + Recertifications + subsequent clinical documentation
  (terminal-prognosis evidence, decline, functional status, ADLs,
  disease progression). LCD eligibility is fundamentally tied to
  recertification support over time, not specifically to HOPE visit
  data — a HUV1/HUV2 encounter may contribute relevant findings, but
  is not the driver of LCD eligibility updates.
- **Decline of Status Graph** — extends Tier 1's Baseline Decline
  Measurements into a longitudinal trend as later encounters are
  harvested.
- **Narrative Progression** — extends the Initial Clinical Narrative
  with findings from subsequent encounters.
- **Master POC Progression** — extends the Initial Master Plan of Care
  as new assessment findings, HUV encounters, and orders update
  Problems/Goals/Interventions.

The Admission Action Center (immediate medication/order/DME/supply/
treatment/lab/diet/referral/physician-contact actions) must be
available throughout RN ICA — not gated on finalization — and must not
lose the nurse's RN ICA location or draft data when opened.

Every harvested HOPE value across all three tiers must retain: HOPE
item ID, harvested value, source module, source record ID, source
assessment/encounter ID (when applicable), source section/field/JSON
path, source order ID (when applicable), source date, harvest
timestamp, mapping version, and validation status — this is the same
provenance model already required in §5.

**Simplest build goal:** RN ICA completes once. Immediately produce
HOPE Admission, Initial LCD Evidence, Initial Decline Baseline, Initial
Narrative, Initial Master POC. Then monitor future events: if HUV1
occurs, produce HOPE HUV1; if HUV2 occurs, produce HOPE HUV2; if
Discharge occurs, produce HOPE Discharge. Continuously update LCD
Eligibility, the Decline Graph, Narrative, and Master POC as
Recertifications and subsequent clinical documentation accumulate.

### Priority 3 — Validation / Submission

Only after HOPE reports can be generated correctly from RN ICA:
implement report validation (blocking errors, compliance-review
exceptions, warnings, exception assignment, resolution tracking),
snapshot locking, export generation, submission tracking, response
storage, correction/resubmission, and full audit trail — the QIES
submission and compliance-checkpoint rules already detailed in §9. A
submitted snapshot must never be silently recalculated after
attestation.

### Priority 4 — Compliance Workspace

Create the Compliance workspace only after Priorities 1-3 work:

```
Compliance
├── HOPE Admission
├── HUV1
├── HUV2
├── HOPE Discharge
├── LCD Eligibility
├── Decline of Status
├── Validation Exceptions
├── Submission History
├── Corrections
└── Audit / Defense
```

The workspace displays outputs; it does not become a second clinical
assessment. As noted in §8, this is a new architectural component
outside the frozen Master Map's 12 sections and requires a Version 1.1
governance process before adoption.

### End-to-End Verification (definition of done)

RN ICA is complete only when one completed assessment reliably
generates: HOPE Admission, HUV1, HUV2, HOPE Discharge, LCD Eligibility,
Decline of Status, Clinical Narrative, Master Plan of Care, and
immediate patient-care actions — with every reported value linked to
its authoritative source, no duplicate HOPE documentation required,
prior snapshots unchanged, corrections/amendments retaining history, and
permissions/audit/tenant separation intact. **No separate HOPE clinical
assessment is permitted.**

**Current status: GAP for all 4 priorities.** This section is a
corrected sequencing view; it does not add scope beyond §1-§10 and does
not authorize any code change. It supersedes the prior "Program
1-4/QIES-first" priority order in this section.

---

## Status

**`SNS_HOPE_HARVEST_RECONCILIATION_1.0` (this document) complete** per
the 10-part required structure: HOPE Admission/HUV1/HUV2/Discharge
harvest maps, QIES submission pipeline, LCD eligibility worksheet map,
Decline-of-status trend map, source-provenance requirements,
validation/exception rules, detailed QIES submission & compliance
validation rules (§9: record-level validation, item validation rules,
exception-handling levels, exception-queue schema, compliance
checkpoints 1-7), and current-SNS-implementation status for every
mapping. The document is centered on the 6 compliance products that
matter to management, clinicians, surveyors, and QIES: HOPE Admission,
HOPE HUV1, HOPE HUV2, HOPE Discharge, LCD Eligibility, and Decline of
Status. §10 consolidates the resulting findings into the 12 major
compliance/reconciliation gaps that remain — QIES Submission Engine,
HOPE Provenance, HUV Snapshot Architecture, Compliance Exception Queue,
LCD Evidence Worksheet, Disease-Specific LCD Engines, Decline of Status
Expansion, Point-to-Point Traceability, Order-Based Medication Harvest,
Compliance Workspace, Survey Defense Package, and Automated
Significant-Change Monitoring — ranked by compliance materiality rather
than by document section. §11 sequences the corrected build priority:
Priority 1 RN ICA Build, Priority 2 (Tier 1 RN ICA Outputs — HOPE
Admission, Initial Narrative, Initial Master POC, Baseline LCD
Evidence, Baseline Decline Measurements; Tier 2 Related Outputs From
Subsequent Encounters — HOPE HUV1, HOPE HUV2, HOPE Discharge, each from
their own visit encounter, not generated by RN ICA; Tier 3 Longitudinal
Outputs — LCD Eligibility, Decline of Status Graph, Narrative
Progression, Master POC Progression, built from the cumulative
patient record), Priority 3 Validation/Submission, Priority 4
Compliance Workspace. RN ICA is the SOC/Admission assessment and
establishes the baseline; it does not generate HUV1 or HUV2 itself.

Reference screenshots (HospiceMD) were used only for UX/workflow
guidance on output structure, not as a source of item definitions or
current-implementation truth. All "Current Status"/"Gap" values are
drawn from the frozen SNS Field Inventory, Gap Report, and HOPE
Crosswalk Verification; items not confirmable from those sources are
marked UNCONFIRMED rather than assumed present.

No code changes are authorized by this document. No frozen artifact
(Deliverables #1-#10, Master Map) was modified.
