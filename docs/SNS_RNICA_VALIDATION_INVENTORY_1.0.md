# SNS RNICA Validation Inventory 1.0 — Phase 1, Deliverable 4

**STATUS: FROZEN — ACCEPTED COMPLETE (2026-08-21)**
No further edits except factual corrections.

> **HOPE GOVERNANCE RULE**
>
> RNICA is the authoritative assessment. HOPE is not a separate
> clinician-facing form. All HOPE reporting elements originate from
> RNICA fields through approved mapping, derivation, and validation
> rules. No duplicate clinician documentation shall be required solely
> for HOPE reporting.

## INVENTORY RULE

This document records validation logic as it actually exists today. It
does not modify `SNS_RNICA_FIELD_INVENTORY_1.0`,
`SNS_RNICA_DATABASE_MAPPING_1.0`, or `SNS_RNICA_API_MAPPING_1.0`, and
does not propose new validation rules or redesign existing ones.

Source of truth: `validateRNICA()` in `RNICA.jsx:765-886` (the only
validation logic in the current implementation — there is no backend
or database-level field validation; see `SNS_RNICA_API_MAPPING_1.0` §1.1
for the backend-side confirmation).

## Key finding

**All RNICA field validation is frontend-only, in one function,
`validateRNICA(formData, mode)`.** It runs client-side before a save/lock
call is made. Nothing server-side re-checks it: `save_rnica_assessment`,
`update_rnica_assessment`, and `lock_rnica_assessment` all accept the
payload exactly as sent, with no field-level checks (`visits.py:751-999`).
The database (`rnica_assessments.form_data`, JSONB) has zero CHECK
constraints on its contents. This means: **any client that calls the API
directly (bypassing `RNICA.jsx`) can save or lock an assessment with none
of the below rules satisfied.**

`validateRNICA()` returns `{ errors, warnings, isValid }`.
`isValid = Object.keys(errors).length === 0`. Only `errors` block the UI
from calling `lockRnicaAssessment()` (`RNICA.jsx:5572-5579`). `warnings`
never block save or lock — they are advisory only. Of the ~300 fields in
`SNS_RNICA_FIELD_INVENTORY_1.0`, only 27 fields (below) have any rule at
all; the remaining ~90% have no validation of any kind.

## Required Fields (rule type: "error" — block Lock, not Save)

| Field | Condition | Message |
|---|---|---|
| `demographics.firstName` | always | First name is required |
| `demographics.lastName` | always | Last name is required |
| `demographics.dob` | always | Date of birth is required |
| `demographics.gender` | always | Gender is required |
| `demographics.advancedCarePlanning.codeStatus` | `mode !== "ongoing"` | HOPE F2000: Code status is required |
| `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference` | `mode !== "ongoing"` | HOPE F2100 required |
| `demographics.advancedCarePlanning.hospitalizationPreference` | `mode !== "ongoing"` | HOPE F2200 required |
| `diagnoses.primaryDiagnosis.icd10` | `mode !== "ongoing"` | HOPE I0010: Primary diagnosis ICD-10 required |
| `admissionsOrder.levelOfCare.level` | always | Level of Care is required for admission |
| `admissionsOrder.toVerification.verbalOrderReadBack` | always | Verbal order read-back verification required |
| `finalization.clinicianSignature` | always | Clinician signature required |

Note: none of these are enforced anywhere except this client-side
function — see Key Finding above. "Always" required fields are NOT
required when `mode === "ongoing"` for the HOPE-tagged ones; the four
non-HOPE-tagged fields (name, dob, gender, level of care, T.O.
verification, signature) are required in both `ica` and `ongoing` modes.

## Conditional Fields (rule type: "warning," gated by `mode` or a sibling field)

| Field | Gate | Message |
|---|---|---|
| `demographics.preferredLanguage` | `mode !== "ongoing"` | HOPE A1110 |
| `demographics.ethnicity` (array) | `mode !== "ongoing"`, empty array | HOPE A1005 |
| `demographics.race` (array) | `mode !== "ongoing"`, empty array | HOPE A1010 |
| `pain.verbalizesPain` | `mode !== "ongoing"` | HOPE J0900 |
| `pain.uncomfortableBecauseOfPain` | `mode !== "ongoing"` | HOPE J0915 |
| `symptomImpact.{pain,shortnessOfBreath,anxiety,nausea,vomiting,diarrhea,constipation,agitation}` | `mode !== "ongoing"` (8 fields) | HOPE J2051 A-H |
| `performanceStatus.pps` / `.kps` | `mode !== "ongoing"`, at least one must be present | HOPE M1190 |
| `neurological.hopeItems.n0500` | `mode !== "ongoing"` | HOPE N0500 (BIMS) |
| `imminentDeath.appearsThreeDaysOrLess` | `mode !== "ongoing"` | HOPE J0050 |
| `demographics.pcg.willingToProvideCare` | skipped entirely if `demographics.pcg.noPcg` is true | CDPH caregiver willingness |
| `demographics.pcg.ableToAdministerMeds` | skipped entirely if `demographics.pcg.noPcg` is true | CDPH med-administration ability |
| `demographics.pcg.caregiverEvaluation.willingnessScore` | skipped entirely if `demographics.pcg.noPcg` is true | CDPH willingness score |
| `demographics.pcg.caregiverEvaluation.capabilityScore` | skipped entirely if `demographics.pcg.noPcg` is true | CDPH capability score |
| `skin.braden.total` | none (unconditional warning) | Braden Scale total required |
| `finalization.pocGenerationCompleted` | none (unconditional warning) | CDPH: POC generation from assessment problems required before lock |
| `demographics.pcg` (assessed) | unconditional warning if `pcgIsAssessed()` returns false | Primary Caregiver status not yet assessed |

## Cross-Field Dependencies (actual conditional logic found in code)

| Dependent field(s) | Depends on | Behavior |
|---|---|---|
| `demographics.pcg.willingToProvideCare`, `.ableToAdministerMeds`, `.caregiverEvaluation.willingnessScore`, `.caregiverEvaluation.capabilityScore` | `demographics.pcg.noPcg` | If `noPcg === true`, none of these four are validated at all (entire `if` block skipped, `RNICA.jsx:807-820`) |
| all HOPE-tagged required/conditional fields (11 of the 27 rules above) | `mode` parameter | `includeHopeRequirements = mode !== "ongoing"` (`RNICA.jsx:768`) — an entire block of rules is skipped when the assessment is an RN Recertification rather than an initial ICA |
| `performanceStatus` warning | `pps` OR `kps` | Only fails if **both** are empty — it is an OR, not an AND (either one satisfies HOPE M1190 per current code) |
| Lock button enablement | `errors` object emptiness | `isValid` is computed purely from `errors`; `warnings` never affect whether `lockRnicaAssessment()` can be called |

No other cross-field rules (e.g. date-order checks, numeric-range checks,
required-if-another-field-equals-X patterns beyond the `noPcg`/`mode`
gates above) exist in `validateRNICA()`.

## Save Validation vs. Submit (Lock) Validation

| Action | What runs | What blocks it |
|---|---|---|
| Save (`api.saveRNICAAssessment` / `api.updateRNICAAssessment`) | `validateRNICA()` is computed and stored in component state via `setValidation(...)` (`RNICA.jsx:5525`) for display purposes, but **is not used to block the save call itself** — the save handler does not check `errors` before calling `api.saveRNICAAssessment`/`updateRNICAAssessment` (`RNICA.jsx:5551-5553`) | Nothing — an assessment with every "error"-level field empty can still be saved as a DRAFT |
| Lock/Sign (`api.lockRNICAAssessment`) | `validateRNICA(formData, mode)` is re-run immediately before the call (`RNICA.jsx:5572`) | `errors` only (`RNICA.jsx:5572-5579`) — if any error-level rule fails, `lockRnicaAssessment()` is not called. `warnings` do not block. Backend performs no independent check (see Key Finding) |

## HOPE-Specific Validation (subset of the above, isolated for cross-reference with `SNS_HOPE_CROSSWALK_1.0`)

All rules explicitly tagged with a HOPE item number in the code comments:
A1110, A1005, A1010, F2000, F2100, F2200, J0900, J0915, J2051 A-H (8
items), I0010, M1190, N0500, J0050 — 17 of the 27 total validated fields
carry an explicit HOPE reference. All 17 are suppressed when
`mode === "ongoing"`. No other currently-implemented rule references a
HOPE item number.

## HOPE Field-to-Item Dependency (RNICA Field → HOPE Item → Validation Dependency)

Restated from the tables above, isolated as the explicit
Field→Item→Dependency chain requested for HOPE traceability:

| RNICA Field | HOPE Item | Validation Dependency |
|---|---|---|
| `demographics.preferredLanguage` | A1110 | warning only, suppressed when `mode==="ongoing"` |
| `demographics.ethnicity` | A1005 | warning only, suppressed when `mode==="ongoing"` |
| `demographics.race` | A1010 | warning only, suppressed when `mode==="ongoing"` |
| `demographics.advancedCarePlanning.codeStatus` | F2000 | error, suppressed when `mode==="ongoing"`; also feeds `patient_code_statuses` sync (subject to the ACP path-mismatch noted in Database/API Mapping) |
| `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference` | F2100 | error, suppressed when `mode==="ongoing"` |
| `demographics.advancedCarePlanning.hospitalizationPreference` | F2200 | error, suppressed when `mode==="ongoing"` |
| `pain.verbalizesPain` | J0900 | warning only, suppressed when `mode==="ongoing"` |
| `pain.uncomfortableBecauseOfPain` | J0915 | warning only, suppressed when `mode==="ongoing"` |
| `symptomImpact.{pain,shortnessOfBreath,anxiety,nausea,vomiting,diarrhea,constipation,agitation}` | J2051 A-H | warning only (8 fields), suppressed when `mode==="ongoing"` |
| `diagnoses.primaryDiagnosis.icd10` | I0010 | error, suppressed when `mode==="ongoing"` |
| `performanceStatus.pps` / `.kps` | M1190 | warning only (OR logic — either satisfies), suppressed when `mode==="ongoing"` |
| `neurological.hopeItems.n0500` | N0500 | warning only, suppressed when `mode==="ongoing"` |
| `imminentDeath.appearsThreeDaysOrLess` | J0050 | warning only, suppressed when `mode==="ongoing"` |

**Gap:** HOPE items referenced in `SNS_RNICA_SECTION_INVENTORY_1.0`'s
HOPE Crosswalk as **not confirmed/not found in RNICA** — F3000
(Spiritual/Existential Concerns), J0905/J0910 (Pain Active
Problem/Comprehensive Pain Assessment), J2030/J2040 (SOB
Screening/Treatment), N0510/N0520 (PRN Opioid/Bowel Regimen),
M1195/M1200 (Types of Skin Conditions / Treatments) — have **no
corresponding validation rule** in `validateRNICA()` because they have
no corresponding RNICA field at all. These are carried forward as
Implementation Gaps in Deliverable #9, not invented here.

## HOPE Traceability Matrix (Rules 1-8, per HOPE Governance Rule)

### Rule 1/2/7 — Status per HOPE item (DIRECT / DERIVED / CALCULATED / GAP) with RNICA Section → Field → Item → Mapping Logic

| RNICA Section | RNICA Field | HOPE Item | Status | Mapping Logic |
|---|---|---|---|---|
| Patient Demographics | `demographics.ethnicity` | A1005 | DIRECT | Value read as-is from `form_data`; no transformation |
| Patient Demographics | `demographics.race` | A1010 | DIRECT | Value read as-is |
| Patient Demographics | `demographics.preferredLanguage` | A1110 | DIRECT | Value read as-is |
| Demographics → Advanced Care Planning | `demographics.advancedCarePlanning.codeStatus` | F2000 | DIRECT (validation) / **BROKEN** (sync) | Frontend reads/validates the nested path directly; backend sync extractor reads a different top-level path (`form_data.advancedCarePlanning`) — see `SNS_RNICA_DATABASE_MAPPING_1.0` §3.3, carried into `SNS_RNICA_API_MAPPING_1.0` §3.3 |
| Demographics → Advanced Care Planning | `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference` | F2100 | DIRECT | Value read as-is |
| Demographics → Advanced Care Planning | `demographics.advancedCarePlanning.hospitalizationPreference` | F2200 | DIRECT | Value read as-is |
| Diagnoses | `diagnoses.primaryDiagnosis.icd10` | I0010 | DIRECT | Value read as-is |
| Diagnoses → HOPE Comorbidities | `diagnoses.hopeComorbidities.{cancer,heartFailure,pvdPad,cardiovascularExclHF,liverDisease,renalDisease,sepsis,diabetesMellitus,neuropathy,stroke,dementia,neurologicalConditions,seizureDisorder,copd,other}` (15 fields) | I0100, I0600, I0900, I0950, I1101, I1510, I2102, I2900, I2910, I4501, I4801, I5150, I5401, I6202, I8005 | DIRECT | One boolean field per comorbidity item, 1:1 |
| Imminent Death (also cross-listed under Diagnoses) | `imminentDeath.appearsThreeDaysOrLess` | J0050 | DIRECT, but dual-section-listed | Value read as-is; RNICA lists this HOPE item under two sections (`imminentDeath` and `diagnoses` HOPE arrays) — a reconciliation question, not a derivation |
| Pain Assessment | `pain.verbalizesPain` | J0900 | DIRECT | Value read as-is |
| Pain Assessment | `pain.uncomfortableBecauseOfPain` | J0915 | DIRECT | Value read as-is |
| Pain Assessment | (no field for "active problem" or "comprehensive assessment completed") | J0905, J0910 | **GAP** | No RNICA field exists |
| Respiratory | (no distinct SOB-screening/treatment field) | J2030, J2040 | **GAP** | No RNICA field exists; dyspnea data exists in `respiratory.*` but is not wired to these specific item codes |
| Symptom Impact | `symptomImpact.{pain,shortnessOfBreath,anxiety,nausea,vomiting,diarrhea,constipation,agitation}` | J2051 A-H | DIRECT | One field per letter, 1:1 |
| SFV / Symptom Impact | `sfv.*` HOPE array (currently lists J2050 under `sfv`) | J2050 | DIRECT but **misplaced** | J2050 is the "was screening done" gate that logically precedes J2051; current code lists it under `sfv`, not `symptomImpact` — a placement issue flagged for migration, not resolved here |
| SFV | `sfv.inPersonSfvCompleted`, `.reasonNotCompleted` | J2052 | DERIVED | Completion is tracked via the separate `sfv_requirements` table / `complete_sfv_requirement_from_visit()` engine, not a raw `form_data` read |
| SFV | `sfv.symptomImpactAtSfv.*` | J2053 | DIRECT | Value read as-is, mirrors J2051 structure at SFV time |
| Performance Status | `performanceStatus.pps`, `.kps` | M1190 (skin-conditions gate, dual-listed — see Rule 3 below for the *different*, correct PPS/KPS usage) | DIRECT (for M1190 gate presence check only — see cross-cutting note) | Warning fires if both are empty; dual-listed with `skin` HOPE array — reconciliation question |
| Integumentary | (no distinct multi-select "types"/"treatments" field) | M1195, M1200 | **GAP** | No RNICA field exists; wound care exists only as free-text/POC fields |
| Neurological | `neurological.hopeItems.n0500` | N0500 in the BIMS sense **is actually implemented** — but the *opioid* N0500/N0510/N0520 items are a **different, unrelated CMS code reused across HOPE tool sections** | DIRECT (BIMS) / **GAP** (Scheduled/PRN Opioid, Bowel Regimen) | RNICA's `neurological.hopeItems.n0500` implements the BIMS-repetition item; no RNICA field implements the Medication-Review N0500/N0510/N0520 (opioid/bowel) items at all — recorded as a genuine gap, distinct from the BIMS field of the same number |
| Spiritual Screening | (no HOPE-coded field) | F3000 | **GAP** | Spiritual content exists as a plain clinical field but carries no HOPE item wiring in `SIDEBAR_CONFIG` |

### Rule 3 — One RNICA field supporting multiple HOPE-adjacent purposes (example: PPS)

`performanceStatus.pps` is a single field that supports three distinct
downstream purposes in the current codebase/architecture, though only
one (M1190 gate presence) is a literal CMS HOPE item read; the other two
are broader hospice-documentation uses, not separate HOPE item codes:
- **Functional Status** — raw value displayed/stored for clinical review.
- **Decline Evidence** — feeds `DeclineTrackerCard`'s `summaryText`
  computation (`SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0` §1), comparing
  current vs. prior PPS.
- **Prognosis/HOPE M1190 gate support** — counted (with KPS) toward the
  M1190 "at least one of PPS/KPS present" validation warning.

### Rule 4 — Multiple RNICA fields supporting one HOPE-adjacent outcome (example: Nutrition)

RNICA's `nutrition` section fields (`weight`/`weightChange`, `appetite`,
`intake`, `dysphagia` — per `SNS_RNICA_FIELD_INVENTORY_1.0` Section 12)
collectively support hospice nutritional-decline documentation, but
**no single HOPE item code aggregates them** in the current HOPE
Crosswalk research — there is no confirmed "HOPE Nutrition Outcome" item
wired in RNICA today. This is recorded as an **architecture-intent gap**:
the many-to-one pattern is conceptually correct per hospice documentation
practice, but no such consolidated HOPE item/field exists in the current
implementation to point to.

### Rule 5 — Derivation logic for CALCULATED values

Only one genuinely calculated (not DIRECT) value exists in current RNICA:

| HOPE-adjacent item | Calculation | Source Fields | Validation Rule |
|---|---|---|---|
| Decline Summary (supports LCD eligibility / decline documentation broadly; not itself a single CMS HOPE item code) | `delta = current - prior` per metric (PPS, KPS, FAST [index-based], Weight [+ % change]); only `trend === "decline"` rows are included in the output sentence (`RNICA.jsx:2080-2091`) | `performanceStatus.pps`, `.kps`, `.fast`, `vitals.weight` (current); prior-assessment equivalents via `GET /patients/{patientId}/performance-history` | None — this value is never validated or required; it is advisory/clipboard-only (`SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0` §1) |

No other RNICA/HOPE-adjacent value in the current codebase is
calculated from multiple source fields — every other HOPE-tagged field
is a DIRECT 1:1 read.

### Rule 6 — GAP items (full list, cross-referenced to Deliverable #9)

F3000, J0905, J0910, J2030, J2040, N0500 (opioid sense)/N0510/N0520,
M1195, M1200 — nine confirmed GAP items with no RNICA field at all.
These are carried forward as Implementation Gaps in
`SNS_IMPLEMENTATION_GAP_REPORT_1.0` §1 ("Has no RNICA source").

## Status

**Deliverable #4 (`SNS_RNICA_VALIDATION_INVENTORY_1.0`) complete.** All
validation logic in the current codebase is enumerated: 11 required
("error") rules, 16 conditional ("warning") rules, the cross-field
dependency set, and the save-vs-lock distinction. No backend or database
validation exists to document beyond what is already noted in
`SNS_RNICA_DATABASE_MAPPING_1.0` and `SNS_RNICA_API_MAPPING_1.0`.

No changes made to any frozen artifact. No code changes are authorized
by this document.

Next: Deliverable #5 — `SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0`.
