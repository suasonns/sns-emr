# RNICA Section Inventory

Status: Implementation-detail research (read-only inventory) � no code
changes made in producing this document.
Companion to: SNS_DESIGN_SYSTEM_1.0.md, SNS_RNICA_MASTER_MAP_1.0.md,
SNS_POC_GENERATION_MATRIX_1.0.md.

This document inventories the CURRENT (as-built) implementation of every
RNICA section � components, database storage, API endpoints, validation,
audit events, HOPE/narrative/POC/order/task dependencies, and current
screen routing � as the field/database/API/validation/HOPE/audit inventory
called for in SNS_RNICA_MASTER_MAP_1.0.md's "Status / Next Steps".

Produced by three parallel research passes over the codebase (repo root:
`sns-emr-frontend/src/components/RNICA.jsx`, `backend/app/models/`,
`backend/app/api/visits.py`, `backend/app/services/`). Citations are
file path + line number/range so every claim is independently verifiable.
"Target Facesheet Section" labels below use the tier language from the
draft available when each research pass ran; cross-reference against the
canonical Section 1-12 numbering in `SNS_RNICA_MASTER_MAP_1.0.md` � a
mapping table is provided at the end of this document.

No code changes are authorized by this document alone.

---
# RNICA Technical Inventory — Assigned Sections (Tiers 1, 3, 9)

> **Scope of this document:** Covers the 12 areas assigned to this agent. All citations are verifiable at the listed file paths and line ranges. Claims marked "None found in codebase" reflect genuine absence after search, not omission.

---

## Tier 1 — Core Assessment Sections

---

### 1. Patient Demographics (`demographics`)

- **Current Section:** "Patient Demographics" — SIDEBAR_CONFIG key `demographics`, label "Patient Demographics", icon 👤, color green
  - `sns-emr-frontend/src/components/RNICA.jsx:200`
- **Component Name:** `renderDemographics(data, update, COLORS, styles)` — standalone named function
  - `RNICA.jsx:3817–3999`
  - Renders Cards: "Patient Information" (A1110), "Address", "Emergency Contact", "Primary Caregiver (PCG)", "Caregiver Willingness & Capability Evaluation" (CDPH), "Living Situation" (A1905), "Advanced Care Planning" (F2000/F2100/F2200)
  - **Note:** Caregiver Assessment and Advanced Care Planning are rendered inside `renderDemographics()` — they do NOT have their own named render functions (covered separately as areas 2 and 3 below).
- **Database Tables:**
  - `rnica_assessments` (PostgreSQL) — `form_data` JSONB column, path `form_data.demographics.*`
  - `backend/app/models/rnica_assessment.py:11–34`
  - On every save/update, demographics data is synced: `form_data.demographics.pcg` → `patient_contacts` table (role: PRIMARY_CAREGIVER); `form_data.diagnoses` primary/secondary/comorbidities → `patient_diagnoses` table; summary text → `patient_facesheet` (primary_diagnosis, secondary_diagnoses fields).
  - `backend/app/api/visits.py:175–221` (`_sync_facesheet_from_rnica`), `visits.py:293–423` (`_sync_shared_records_from_rnica`)
- **API Endpoints:**
  - `POST /visits/rnica/save` — create (visits.py:751)
  - `GET /visits/rnica/{assessment_id}` — load by ID, with shared-data overlay (visits.py:860)
  - `GET /visits/rnica/by-patient/{patient_id}` — load latest non-locked (visits.py:892)
  - `PUT /visits/rnica/{assessment_id}` — update (visits.py:930)
  - `POST /visits/rnica/{assessment_id}/lock` — lock (visits.py:978)
  - `GET /visits/rnica/{assessment_id}/intelligence` — AI suggestions (visits.py:1002)
- **Validation Rules:**
  - **Errors (block finalization):** `demographics.firstName`, `demographics.lastName`, `demographics.dob`, `demographics.gender` all required
  - **Warnings:** HOPE A1110 `preferredLanguage` required; HOPE A1005 `ethnicity[]` required; HOPE A1010 `race[]` required; PCG assessed flag must be set; CDPH: `pcg.willingToProvideCare`, `pcg.ableToAdministerMeds`, `pcg.caregiverEvaluation.willingnessScore`, `pcg.caregiverEvaluation.capabilityScore` required (skipped if `pcg.noPcg` is true)
  - Source: `RNICA.jsx:770–820` (`validateRNICA()`)
  - No backend validation in `clinical_note_validation_engine.py` specific to this section — that engine operates on `ClinicalNote` model visits, not `RnicaAssessment` rows. None found in codebase for direct RNICA backend field validation.
- **Audit Events:**
  - **No RNICA-specific audit calls found** on `POST /visits/rnica/save` (visits.py:751–795), `PUT /visits/rnica/{assessment_id}` (visits.py:930–975), or `POST /visits/rnica/{assessment_id}/lock` (visits.py:978–999). The `_safe_log_event()` helper at visits.py:2028 is imported and exists, but it is NOT called in any of the RNICA CRUD endpoints. Only the general `FINALIZE_VISIT` event (tied to `Visit` records, not `RnicaAssessment` records) is logged at visits.py:4439–4444 and 4576–4581.
  - **Gap:** Demographic edits, saves, updates, and locks on RNICA assessments produce no audit trail in `audit_logs`.
- **HOPE Dependencies:**
  - HOPE A1110 (preferred language): `demographics.preferredLanguage` — warning if missing
  - HOPE A1005 (ethnicity): `demographics.ethnicity[]` — warning if missing
  - HOPE A1010 (race): `demographics.race[]` — warning if missing
  - Source: `RNICA.jsx:SIDEBAR_CONFIG:200`, `validateRNICA():776–789`
- **Narrative Dependencies:**
  - Indirect: `demographics.firstName/lastName/dob` are referenced in patient-banner display but do NOT feed `diagnoses.lcdEligibilityNarrative` directly. No evidence of auto-generated narrative from this section.
  - `demographics.pcg.name` is synced to the shared `patient_contacts` table (PRIMARY_CAREGIVER role), which may be referenced in other narrative contexts outside RNICA. `visits.py:361–371`
- **POC Dependencies:**
  - `poc_compiler_rn_mapper.py`: `map_rn_ica_to_problem_nodes()` reads `rn_ica_data.get("primary_diagnosis")` and generic `"caregiver_support"` keyword from diagnosis/poc_content. Demographics itself does not generate POC nodes, but `pcg.caregiverEvaluation` data could match the `caregiver_support` rule keyword. `poc_compiler_rn_mapper.py:63,73`
  - `finalization.pocEntries` is where generated POC problems are stored. `RNICA.jsx:729`
- **Order Dependencies:** None found in codebase. Demographics data does not directly trigger orders.
- **Task Dependencies:**
  - None specific to demographics. The `process_initial_rn_ica_finalize()` call (triggered on visit finalization, visits.py:3122) uses visit-level data, not form-level demographics fields, to create HUV1/HUV2 tasks.
- **Current Screens:** ROUTES index 0 — "Patient Demographics", `formSection: "demographics"` (`RNICA.jsx:167`)
- **Target Facesheet Section:** Section 1-4 (Patient Snapshot / Current Concerns / Diagnosis Summary / Assessment Findings core)
- **Migration Risk:** **High** — Core patient identity data; HOPE A1005/A1010/A1110 compliance; facesheet sync logic tied to PCG and ACP extractions; critical `_overlay_shared_code_status` reads from this section at GET time.
- **Migration Complexity:** **High** — Demographics section drives 5 separate downstream syncs (`patient_contacts`, `patient_code_statuses`, `patient_facesheet`, `patient_diagnoses`, `patient_allergies`); overlay logic reads live data from shared tables; contains the PCG assessment tri-state logic (`pcgIsAssessed`) and ACP data that is stored inconsistently (see area 3).

---

### 2. Caregiver Assessment (`caregiverAssessment`)

- **Current Section:** "Caregiver Assessment" — SIDEBAR_CONFIG key `caregiverAssessment`, label "Caregiver Assessment", icon 🧑‍⚕️, `parent: "demographics"`, `scrollTarget: "pcg"`, `cdphRequired: true`
  - `RNICA.jsx:202`
- **Component Name:** Inline JSX within `renderDemographics()` — **no separate named component**. The PCG card renders lines ~3869–3908 (Card "Primary Caregiver (PCG)", id="pcg") and lines ~3915–3960 (Card "Caregiver Willingness & Capability Evaluation"). The `FormTriState`, `FormRadioGroup`, `FormSelect`, `FormCheckboxGroup` primitives are reused.
  - `RNICA.jsx:3869–3960`
- **Database Tables:**
  - `rnica_assessments.form_data` — JSON path `form_data.demographics.pcg.*`
  - Schema: `pcg.{ assessed, name, relationship, phone, healthStatus, anxietyLevel, ableToAdministerMeds, willingToProvideCare, pcgConcerns, caregiverEvaluation.{ physicalAbility, cognitiveAbility, emotionalReadiness, availabilityForCare, trainingNeeds[], willingnessScore, capabilityScore, supportSystemAdequacy, evaluationNotes }, noPcg, noPcgReason }`
  - `RNICA.jsx:310–331` (INITIAL_FORM definition)
  - On save/update: `pcg.name/relationship/phone` → `patient_contacts` table (role: PRIMARY_CAREGIVER)
  - `visits.py:244–254` (`_extract_rnica_pcg`), `visits.py:361–371` (`set_patient_contact`)
  - The `caregiverEvaluation` sub-fields (willingnessScore, capabilityScore, trainingNeeds, etc.) are **NOT** synced to any separate table — they remain only in `rnica_assessments.form_data`. None found in codebase.
- **API Endpoints:** Same 6 RNICA endpoints as Demographics (no section-specific endpoint)
- **Validation Rules:**
  - **Warning:** `pcg.assessed` flag must be truthy (via `pcgIsAssessed()` helper) — `RNICA.jsx:802–804`
  - **Warnings (CDPH, skipped if `pcg.noPcg`):** `pcg.willingToProvideCare`, `pcg.ableToAdministerMeds`, `pcg.caregiverEvaluation.willingnessScore`, `pcg.caregiverEvaluation.capabilityScore` — `RNICA.jsx:806–820`
  - `pcgIsAssessed()` backward-compat logic: `assessed===true` OR `noPcg===true` OR any legacy field populated — `RNICA.jsx:1163–1168`
- **Audit Events:** None found in codebase (same gap as Demographics — no RNICA-specific audit logging).
- **HOPE Dependencies:** None — `hope: []` in SIDEBAR_CONFIG. Caregiver Assessment is a CDPH (California state) requirement, not a CMS HOPE element. `RNICA.jsx:202`
- **Narrative Dependencies:**
  - Indirect: PCG health status, anxiety level, and capability scores could support caregiver narrative context for the LCD eligibility narrative, but **no automated dependency** found. No code that reads `pcg.caregiverEvaluation` to populate `lcdEligibilityNarrative`.
- **POC Dependencies:**
  - The `poc_compiler_rn_mapper.py` RULE_KEYWORDS set includes `"caregiver_support"` (`poc_compiler_rn_mapper.py:72`). `_derive_keywords_from_rn_ica()` reads `rn_ica_data.get("poc_content")` and primary diagnosis text but does NOT explicitly parse `demographics.pcg`. Caregiver Support POC items may arise from free-text keyword matching, but no direct field mapping. `poc_compiler_rn_mapper.py:29–65`
- **Order Dependencies:** None found in codebase.
- **Task Dependencies:** None found in codebase specific to caregiver section.
- **Current Screens:** ROUTES index 0 ("Patient Demographics", `formSection: "demographics"`) — renders as a sub-section via scrollTarget "pcg". No separate route entry. `RNICA.jsx:167,202`
- **Target Facesheet Section:** Section 1-4 (Patient Snapshot / Current Concerns / Diagnosis Summary / Assessment Findings core)
- **Migration Risk:** **High** — CDPH survey compliance; `pcg.assessed` tri-state logic was a deliberate bug-fix (RNICA gap-review item #6, `RNICA.jsx:313–315`); PCG contact sync feeds shared `patient_contacts` table. Any redesign must preserve the explicit "not yet assessed" state.
- **Migration Complexity:** **Medium** — Data is a nested sub-key of demographics; the caregiver evaluation sub-fields are isolated to RNICA `form_data`; the PCG sync logic in `_extract_rnica_pcg()` is simple (name/relationship/phone only — ignores evaluation fields).

---

### 3. Advanced Care Planning (`advancedCarePlanning`)

- **Current Section:** "Advanced Care Planning" — SIDEBAR_CONFIG key `advancedCarePlanning`, label "Advanced Care Planning", icon 📜, HOPE codes `["F2000","F2100","F2200"]`, color green, `parent: "demographics"`, `scrollTarget: "advancedCarePlanning"`, `cdphRequired: true`
  - `RNICA.jsx:203`
- **Component Name:** Inline JSX within `renderDemographics()` — **no separate named component**. Card titled "Advanced Care Planning" rendered at `RNICA.jsx:3974–3996` (id="advancedCarePlanning"). Fields: Code Status (F2000), Life-Sustaining Treatment Preference (F2100), Hospitalization Preference (F2200), Decision Maker, POA Name/Phone, Advance Directive on File, POLST on File.
- **Database Tables:**
  - **⚠️ Storage inconsistency:** INITIAL_FORM defines ACP data at `form_data.demographics.advancedCarePlanning.*` (`RNICA.jsx:337–343`), but the backend helper functions read and write it at the **top-level** `form_data.advancedCarePlanning.*`:
    - `_extract_rnica_code_status()` reads `form_data.get("advancedCarePlanning")` — `visits.py:238–241`
    - `_extract_rnica_dpoa()` reads `form_data.get("advancedCarePlanning")` — `visits.py:257–265`
    - `_extract_rnica_decision_maker()` reads `form_data.get("advancedCarePlanning")` — `visits.py:268–273`
    - `_overlay_shared_code_status()` writes back to `result["advancedCarePlanning"]` (top-level) — `visits.py:798–857`
  - Synced tables: `patient_code_statuses` (code status, source "RN_ICA") and `patient_contacts` (DPOA role, DECISION_MAKER role) — `visits.py:350–395`
  - The `form_data.demographics.advancedCarePlanning` frontend path and `form_data.advancedCarePlanning` backend path are **different paths in the JSONB**. This likely means the backend sync reads empty/stale data unless the frontend was adjusted to write at top-level too.
- **API Endpoints:** Same 6 RNICA endpoints. `_overlay_shared_code_status()` is applied on all GET responses.
- **Validation Rules:**
  - **Errors (HOPE required, block finalization):**
    - `demographics.advancedCarePlanning.codeStatus` → "F2000: Code status is required"
    - `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference` → "F2100: Life-sustaining treatment preference required"
    - `demographics.advancedCarePlanning.hospitalizationPreference` → "F2200: Hospitalization preference required"
  - Source: `RNICA.jsx:791–799`
  - These validation paths use `formData.demographics.advancedCarePlanning.*` (matching INITIAL_FORM), but backend extracts from `form_data.advancedCarePlanning` (top-level). **Mismatch.**
- **Audit Events:** None found in codebase (same gap as other RNICA sections).
- **HOPE Dependencies:**
  - **F2000** (Code Status/Preferences) — `demographics.advancedCarePlanning.codeStatus` — CMS HOPE required
  - **F2100** (Life-Sustaining Treatment Preference) — `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference`
  - **F2200** (Hospitalization Preference) — `demographics.advancedCarePlanning.hospitalizationPreference`
  - Also listed in `finalization` SIDEBAR_CONFIG hope array: `["F2000","F2100","F2200"]` (`RNICA.jsx:235`) indicating these items appear in the finalization HOPE checklist as well.
  - `_overlay_shared_code_status()` overlays authoritative code status, DPOA, and decision maker from shared tables at read time — `visits.py:798–857`
- **Narrative Dependencies:**
  - Code status (from `advancedCarePlanning.codeStatus`) is synced to `patient_code_statuses` table and displayed on the Facesheet. It feeds all downstream documents that reference code status (orders, nursing notes), though no direct link to `lcdEligibilityNarrative`.
- **POC Dependencies:** None found — ACP data is not referenced by `poc_compiler_rn_mapper.py`.
- **Order Dependencies:**
  - Code status is a prerequisite input for Admission Orders (affects what orders are appropriate), but no direct automated order generation from ACP fields found. None found in codebase as a hard dependency.
- **Task Dependencies:** None found in codebase specific to ACP section.
- **Current Screens:** ROUTES index 0 ("Patient Demographics") — scrollTarget "advancedCarePlanning" within demographics screen. No separate route. `RNICA.jsx:167,203`
- **Target Facesheet Section:** Section 1-4 (Patient Snapshot / Current Concerns / Diagnosis Summary / Assessment Findings core)
- **Migration Risk:** **High** — F2000/F2100/F2200 are CMS HOPE required fields; code status drives shared `patient_code_statuses` table which all other notes/orders read; the storage mismatch between frontend path (`demographics.advancedCarePlanning`) and backend extraction path (`advancedCarePlanning` top-level) is a latent bug that could cause silent data loss on syncs.
- **Migration Complexity:** **High** — The `_overlay_shared_code_status()` write-back (live overlay pattern), the DPOA/Decision Maker contact sync, and the F-code HOPE compliance requirement all make this deeply interconnected. The path inconsistency must be resolved before or during migration.

---

### 4. Pain Assessment (`pain`)

- **Current Section:** "Pain Assessment" — SIDEBAR_CONFIG key `pain`, label "Pain Assessment", icon ⚡, HOPE codes `["J0900","J0915"]`, color green, `sfv: true`
  - `RNICA.jsx:205`
- **Component Name:** `renderGenericSection("pain", ...)` — generic dispatcher at `RNICA.jsx:4016`. Within it, Pain-specific logic derives patient type (verbal/non-verbal/pediatric) from `pain.verbalizesPain` and age (`RNICA.jsx:4020–4055`). Pain scale sub-components used:
  - `NumericPainScale` (imported from `../assessments/pain/NumericPainScale`)
  - `PAINADScale` (imported from `../assessments/pain/PAINADScale`)
  - `FLACCScale` (imported from `../assessments/pain/FLACCScale`)
  - `BodyMapPain` component at `RNICA.jsx:3649–3795`
  - `RNICA.jsx:18–20,62–64`
- **Database Tables:**
  - `rnica_assessments.form_data` — path `form_data.pain.*`
  - Schema: `{ verbalizesPain, uncomfortableBecauseOfPain, neuropathicPain, screeningDate, comprehensiveAssessmentCompleted, comprehensiveAssessmentDate, assessmentTool, painIntensity.{current,worst,best,acceptable}, painLocation[], painCharacter[], painRadiation, painBodySites[], painMapMode, aggravatingFactors[], relievingFactors[], painManagementPlan, flacc.{face,legs,activity,cry,consolability,total}, painad.{breathing,vocalization,facialExpression,bodyLanguage,consolability,total}, nonPharmInterventions[] }`
  - `RNICA.jsx:360–381`
  - NOT synced to any separate table. Stays in `rnica_assessments.form_data`. None found in codebase for separate pain table.
- **API Endpoints:** Same 6 RNICA endpoints.
- **Validation Rules:**
  - **Warnings (HOPE):**
    - J0900: `pain.verbalizesPain` required
    - J0915: `pain.uncomfortableBecauseOfPain` required
  - Source: `RNICA.jsx:828–834`
  - `sfv: true` in SIDEBAR_CONFIG indicates pain items are SFV triggers when MODERATE/SEVERE.
- **Audit Events:** None found in codebase (same RNICA gap).
- **HOPE Dependencies:**
  - **J0900** (Pain Verbalization): `pain.verbalizesPain` — also drives pain scale selection (verbal/non-verbal mode auto-derive) — `RNICA.jsx:828–833, 4033–4038`
  - **J0915** (Uncomfortable Because of Pain): `pain.uncomfortableBecauseOfPain` — `RNICA.jsx:829–833`
  - `pain.verbalizesPain` field value (`"0"`, `"1"`, `"2"`, `"3"`) maps to HOPE J0900 coding — `RNICA.jsx:4035–4037`
- **Narrative Dependencies:**
  - `pain.painManagementPlan` is a free-text field; no automated injection into `lcdEligibilityNarrative`. No code found that reads pain data to generate LCD narrative text.
  - Pain data (verbalizesPain, painIntensity) participates in the `buildClientLcdFacts()` function only indirectly (no direct pain LCD fact field — pain impact feeds through symptomImpact J2051). None found for direct pain-to-narrative link.
- **POC Dependencies:**
  - `poc_compiler_rn_mapper.py` RULE_KEYWORDS includes `"pain"` (`poc_compiler_rn_mapper.py:63`). When pain keyword is detected in RN ICA data, a Pain POC problem node is generated. The mapper reads `rn_ica_data.get("poc_content")` and keyword extraction from diagnosis/symptom text — `poc_compiler_rn_mapper.py:47–84`.
- **Order Dependencies:**
  - Pain severity indicators (MODERATE/SEVERE) feed HOPE Phase B SFV trigger logic (`hope_phase_b_engine.py:145–155,319–394`). `pain_impact` from J2051 (symptomImpact, not directly pain section) drives SFV task creation. The pain section's `flacc/painad/verbalizesPain` data does NOT directly trigger orders — orders are created in the Admissions Order / Hospice Orders Hub sections.
- **Task Dependencies:**
  - Pain scoring (via symptomImpact J2051 pain score — cross-references symptomImpact section) drives SFV requirement task if MODERATE or SEVERE: `hope_phase_b_engine.py:145–155,319–394`. The `pain.verbalizesPain` HOPE J0900 flag does NOT itself create a task.
- **Current Screens:** ROUTES index 2 ("Pain Assessment", `formSection: "pain"`) — `RNICA.jsx:169`
- **Target Facesheet Section:** Section 1-4 (Patient Snapshot / Current Concerns / Diagnosis Summary / Assessment Findings core)
- **Migration Risk:** **High** — HOPE J0900/J0915 required fields; pain scale selection depends on J0900 value; SFV trigger chain ultimately roots in symptom impact (which includes pain score); FLACC/PAINAD sub-components are separate imported files.
- **Migration Complexity:** **Medium** — Pain data is self-contained in `form_data.pain`; no facesheet sync; the imported scale components (NumericPainScale, PAINADScale, FLACCScale) are separate files that must travel with any redesign.

---

### 5. Symptom Impact (`symptomImpact`)

- **Current Section:** "Symptom Impact" — SIDEBAR_CONFIG key `symptomImpact`, label "Symptom Impact", icon 📊, HOPE code `["J2051"]`, color **red** (SFV-type color)
  - `RNICA.jsx:206`
- **Component Name:** `renderGenericSection("symptomImpact", ...)` — `RNICA.jsx:4016`
- **Database Tables:**
  - `rnica_assessments.form_data` — path `form_data.symptomImpact.*`
  - Schema: `{ pain, shortnessOfBreath, anxiety, nausea, vomiting, diarrhea, constipation, agitation, totalScore, assessmentDate }`
  - `RNICA.jsx:383–390`
  - NOT synced to any separate table. The `j2051_pain_impact` and `j2051_non_pain_impact` values are extracted from `clinical_notes` at visit finalization time (not directly from `rnica_assessments.form_data`): `visits.py:3102–3106` references `_extract_j2051_impacts_from_notes()`.
- **API Endpoints:** Same 6 RNICA endpoints.
- **Validation Rules:**
  - **Warnings (HOPE J2051 A–H):** All 8 items required:
    - `symptomImpact.pain` → "HOPE J2051A: pain score required"
    - `symptomImpact.shortnessOfBreath` → J2051B
    - `symptomImpact.anxiety` → J2051C
    - `symptomImpact.nausea` → J2051D
    - `symptomImpact.vomiting` → J2051E
    - `symptomImpact.diarrhea` → J2051F
    - `symptomImpact.constipation` → J2051G
    - `symptomImpact.agitation` → J2051H
  - Source: `RNICA.jsx:836–842`
- **Audit Events:** None found in codebase.
- **HOPE Dependencies:**
  - **J2051** (Symptom Impact Rating, 8-item) — all 8 sub-items map directly to `symptomImpact.*` fields
  - **Critical HOPE Phase B dependency:** `symptomImpact.pain` (pain impact) and aggregate of other symptoms (non-pain impact) drive the SFV requirement trigger. If ANY item is MODERATE or SEVERE, an SFV task must be created within 2 calendar days: `hope_phase_b_engine.py:145–155,319–394`, `visits.py:3102–3130`
  - The SFV trigger reads J2051 from `clinical_notes` (via `_extract_j2051_impacts_from_notes` at finalization time), not directly from `rnica_assessments.form_data` — `visits.py:3102–3106`.
- **Narrative Dependencies:**
  - `symptomImpact.pain` and other scores feed `buildClientLcdFacts()` only indirectly (no direct LCD field). `RNICA.jsx:1326–1391`.
  - `dyspnea` and `nausea_vomiting` are in the POC rule keywords — these may match from symptom descriptions — `poc_compiler_rn_mapper.py:66,71`.
  - No direct auto-injection into `lcdEligibilityNarrative`.
- **POC Dependencies:**
  - `poc_compiler_rn_mapper.py` keywords include `"pain"`, `"dyspnea"`, `"anxiety"`, `"nausea_vomiting"`, `"constipation"` — `poc_compiler_rn_mapper.py:63–71,79`. High symptom scores may match these rule keywords and generate POC problem nodes.
- **Order Dependencies:**
  - MODERATE/SEVERE symptom scores trigger the SFV task (a visit requirement, not a medication/DME order). No direct order generation found.
- **Task Dependencies:**
  - **Critical:** MODERATE or SEVERE score in any J2051 field → creates `SFVRequirement` record + `Task` (type SFV) due within 2 calendar days — `hope_phase_b_engine.py:319–394`, `visits.py:3122–3130`.
- **Current Screens:** ROUTES index 3 ("Symptom Impact", `formSection: "symptomImpact"`) — `RNICA.jsx:170`
- **Target Facesheet Section:** Section 1-4 (Patient Snapshot / Current Concerns / Diagnosis Summary / Assessment Findings core)
- **Migration Risk:** **High** — J2051 A–H are ALL required CMS HOPE items; any of them triggers mandatory SFV task creation if MODERATE/SEVERE; this is the primary driver of HOPE Phase B compliance scheduling.
- **Migration Complexity:** **High** — The J2051 extraction for SFV triggering reads from `clinical_notes` at visit finalization, not from the RNICA form directly; the data path from form entry to task creation passes through multiple services (`hope_phase_b_engine`, `visits.py` finalization hook, `sfv_requirement` table).

---

### 6. Diagnoses (`diagnoses`) — including `lcdEligibilityNarrative`

- **Current Section:** "Diagnoses" — SIDEBAR_CONFIG key `diagnoses`, label "Diagnoses", icon 🔬, HOPE codes `["I0010","J0050"]`, color green
  - `RNICA.jsx:207`
- **Component Name:** `renderGenericSection("diagnoses", ...)` — `RNICA.jsx:4016`. Contains three named sub-components:
  - `LcdEligibilityCard({ diagnosesData, fullFormData, updateField, styles, COLORS })` — `RNICA.jsx:1448–1731`; drives live LCD detection/evaluation cycle via `detectLCD`, `getLCDConfig`, `evaluateLCD` APIs
  - `SecondaryDiagnosesCard({ diagnosesData, updateField, styles, COLORS })` — `RNICA.jsx:1737–1808`; feeds HOPE comorbidity detection
  - `HopeComorbiditiesCard({ diagnosesData, updateField, styles, COLORS })` — `RNICA.jsx:1853–1974`; renders HOPE I0100–I8005 comorbidity checklist
- **Database Tables:**
  - `rnica_assessments.form_data` — path `form_data.diagnoses.*`
  - Schema:
    ```
    {
      primaryDiagnosis: { icd10, description, onsetDate },
      secondaryDiagnoses: [{ icd10, description, relatedToTerminal }],
      comorbidities: [],
      terminalPrognosis,
      diseaseTrajectory,
      lcdEligibilityNarrative,       ← free-text narrative, no auto-generation
      ndsEligibility: {
        detectedDisease, criteriaAnswers: {[disease]: {}}, criteriaFacts: {[disease]: {}}
      },
      hopeComorbidities: {
        cancer, heartFailure, pvdPad, cardiovascularExclHF, liverDisease,
        renalDisease, sepsis, diabetesMellitus, neuropathy, stroke,
        dementia, neurologicalConditions, seizureDisorder, copd,
        other, additionalNote
      }
    }
    ```
  - `RNICA.jsx:391–426`
  - **Synced tables on every save/update:**
    - `patient_diagnoses` (primary) via `sync_official_primary_diagnosis()` — `visits.py:321–332`, source "RN_ICA"
    - `patient_diagnoses` (secondary + comorbidities) via `sync_secondary_and_comorbidity_diagnoses()` — `visits.py:334–342`
    - `patient_facesheet.primary_diagnosis` (text) — `visits.py:207`
    - `patient_facesheet.secondary_diagnoses` (text) — `visits.py:208`
- **API Endpoints:** Same 6 RNICA endpoints. Additionally, diagnoses section is the consumer of three eligibility API calls (frontend):
  - `POST /eligibility/detect-lcd` — `detectLCD()` — `RNICA.jsx:1473–1483`
  - `GET /eligibility/lcd-config/{disease}` — `getLCDConfig()` — `RNICA.jsx:1497–1513`
  - `POST /eligibility/evaluate-lcd` — `evaluateLCD()` — `RNICA.jsx:1529–1546`
  - Source: `RNICA.jsx:32` (import of `detectLCD, evaluateLCD, getLCDConfig`)
- **Validation Rules:**
  - **Error:** HOPE I0010 — `diagnoses.primaryDiagnosis.icd10` required — `RNICA.jsx:844–847`
  - No HOPE validation for secondary diagnoses, comorbidities, or LCD narrative.
- **Audit Events:** None found in codebase (same RNICA gap). Notably, diagnosis syncs to `patient_diagnoses` happen silently on save/update with no audit trail.
- **HOPE Dependencies:**
  - **I0010** (Principal Diagnosis ICD-10): `diagnoses.primaryDiagnosis.icd10` — required error — `RNICA.jsx:844`
  - **J0050** (Prognosis — appears in BOTH Diagnoses and Imminent Death): Listed in diagnoses SIDEBAR_CONFIG alongside I0010. In INITIAL_FORM, `imminentDeath.appearsThreeDaysOrLess` is the primary J0050 field.
  - **HOPE I-section comorbidities (I0100–I8005):** `diagnoses.hopeComorbidities.*` maps to 14 HOPE categories — `RNICA.jsx:1826–1841` (`HOPE_COMORBIDITY_CATEGORIES` with `hopeCode` per entry). Auto-detection from ICD-10 via regex, but clinician must confirm. Cancer exclusion carve-out implemented — `RNICA.jsx:1897–1903`.
- **Narrative Dependencies — `lcdEligibilityNarrative`:**
  - Field: `form_data.diagnoses.lcdEligibilityNarrative` (string) — `RNICA.jsx:398`
  - **Embedded within Diagnoses section, NOT a separate top-level section**
  - **Not auto-generated:** The LCD eligibility evaluation (via `LcdEligibilityCard`) shows pass/fail criteria, but the narrative text field is a plain free-text `<textarea>` that the clinician fills manually.
  - `buildClientLcdFacts()` auto-computes facts from 9 other RNICA sections (performanceStatus, musculoskeletal, nutrition, gastrointestinal, genitourinary, vitals, respiratory) to drive criteria evaluation — `RNICA.jsx:1326–1391` — but these facts are shown in the UI for reference; they do NOT auto-populate the narrative textarea.
  - `lcdEligibilityNarrative` is only stored in `rnica_assessments.form_data.diagnoses` — not synced to `patient_facesheet` or any other table. None found in codebase.
- **POC Dependencies:**
  - `poc_compiler_rn_mapper.py:map_rn_ica_to_problem_nodes()` reads `rn_ica_data.get("primary_diagnosis")` (string) and resolves to disease keywords (cancer, chf, copd, dementia, etc.) from ALIAS_MAP — `poc_compiler_rn_mapper.py:46–100`. Primary diagnosis drives the majority of POC problem generation.
  - Secondary diagnoses contribute via `_derive_keywords_from_rn_ica()` — `poc_compiler_rn_mapper.py:29–65`.
- **Order Dependencies:**
  - Primary diagnosis ICD-10 is synced to `patient_diagnoses` (source RN_ICA) and is used as the authoritative diagnosis for physician orders and billing. No direct automated order trigger from this section alone.
- **Task Dependencies:** None directly from diagnoses section (SFV task creation is from `symptomImpact`, not diagnoses).
- **Current Screens:** ROUTES index 4 ("Diagnoses", `formSection: "diagnoses"`) — `RNICA.jsx:171`
- **Target Facesheet Section:** Section 1-4 (Patient Snapshot / Current Concerns / Diagnosis Summary / Assessment Findings core)
- **Migration Risk:** **High** — HOPE I0010 required; primary diagnosis drives `patient_diagnoses` sync (authoritative ICD-10 record); `LcdEligibilityCard` calls 3 separate backend eligibility APIs; `HopeComorbiditiesCard` with 14 HOPE I-codes; `lcdEligibilityNarrative` is a legally significant free-text field for LCD compliance.
- **Migration Complexity:** **High** — Three named sub-components (`LcdEligibilityCard`, `SecondaryDiagnosesCard`, `HopeComorbiditiesCard`) with complex state management; `buildClientLcdFacts()` cross-section fact aggregation from 9 other sections; 3 external eligibility API calls with debouncing; diagnosis sync to 2 shared tables; `hopeComorbidities` auto-detection with ICD-10 regex.

---

### 7. Performance Status (`performanceStatus`)

- **Current Section:** "Performance Status" — SIDEBAR_CONFIG key `performanceStatus`, label "Performance Status", icon 📈, HOPE code `["M1190"]`, color green
  - `RNICA.jsx:208`
- **Component Name:** `renderGenericSection("performanceStatus", ...)` — `RNICA.jsx:4016`. Named sub-component:
  - `DeclineTrackerCard({ patientId, assessmentId, performanceData, weight, styles, COLORS })` — `RNICA.jsx:2001–2145`; fetches prior RNICA/recert PPS/KPS/FAST/weight history via `fetchPerformanceHistory(patientId)` (`../api/facesheet`) to show trend
  - `WeightLossAutoCalcCard` (defined around `RNICA.jsx:2145–2270`); fetches prior weight history to auto-suggest weight loss % text for `nutrition.weightLossPastSixMonths`
- **Database Tables:**
  - `rnica_assessments.form_data` — path `form_data.performanceStatus.*`
  - Schema: `{ pps, ppsJustification, kps, kpsJustification, ecog, ecogJustification, fast, fastStage, nyha, nyhaJustification, functionalDeclineNotes }`
  - `RNICA.jsx:429–436`
  - NOT synced to any separate table directly. However, `performanceStatus.pps` and `performanceStatus.kps` are read by `buildClientLcdFacts()` as LCD facts → drives the `LcdEligibilityCard` in Diagnoses section — `RNICA.jsx:1346–1348`.
  - `fetchPerformanceHistory()` reads from a `patient_facesheet`-adjacent API that returns prior assessment PPS/KPS/FAST/weight for trend display — `RNICA.jsx:2012` (import: `../api/facesheet`).
- **API Endpoints:** Same 6 RNICA endpoints. Plus frontend-side `GET /facesheet/performance-history/{patient_id}` (via `fetchPerformanceHistory`).
- **Validation Rules:**
  - **Warning (HOPE M1190):** At least one of `performanceStatus.pps` or `performanceStatus.kps` required — `RNICA.jsx:850–852`
  - No hard error for performance status (warning only).
- **Audit Events:** None found in codebase.
- **HOPE Dependencies:**
  - **M1190** (Functional Status): `performanceStatus.pps` or `performanceStatus.kps` — HOPE warning — `RNICA.jsx:850`
  - `performanceStatus.fast` / `performanceStatus.nyha` are non-HOPE items but feed LCD eligibility criteria (FAST stage ≥7a, NYHA class) — `RNICA.jsx:1357–1358`
- **Narrative Dependencies:**
  - `performanceStatus.pps` and `kps` feed `buildClientLcdFacts()` → `LcdEligibilityCard` evaluates LCD criteria using PPS/KPS — `RNICA.jsx:1346–1348`
  - `DeclineTrackerCard` generates a copyable summary sentence (e.g. "PPS declined from 50% to 40%...") that the clinician can paste into notes — `RNICA.jsx:2080–2091`. This text is NOT auto-injected into `lcdEligibilityNarrative`; it requires manual copy-paste.
  - `WeightLossAutoCalcCard` can insert a suggested string into `nutrition.weightLossPastSixMonths` field (cross-section write) — `RNICA.jsx:2229–2233`.
- **POC Dependencies:**
  - `poc_compiler_rn_mapper.py` RULE_KEYWORDS includes `"general_decline"`, `"fatigue"` — `poc_compiler_rn_mapper.py:53,64`. PPS/KPS values are not directly parsed by the mapper, but may match via keyword extraction from `rn_ica_data.get("assessment")` text fields.
- **Order Dependencies:** None found directly from performance status data.
- **Task Dependencies:** None found directly. `process_initial_rn_ica_finalize()` creates HUV1/HUV2 tasks based on visit type, not performance status values.
- **Current Screens:** ROUTES index 5 ("Performance Status", `formSection: "performanceStatus"`) — `RNICA.jsx:172`
- **Target Facesheet Section:** Section 1-4 (Patient Snapshot / Current Concerns / Diagnosis Summary / Assessment Findings core)
- **Migration Risk:** **High** — HOPE M1190 required; PPS/KPS/FAST feed LCD eligibility evaluation; historical trend data (DeclineTrackerCard) is essential for LCD eligibility documentation and CMS/ADR review.
- **Migration Complexity:** **Medium** — `DeclineTrackerCard` and `WeightLossAutoCalcCard` are separate named sub-components with their own API calls; `buildClientLcdFacts()` cross-references are read-only; no facesheet sync for PPS/KPS themselves.

---

## Tier 3 — HOPE Sections

---

### 8. Imminent Death (`imminentDeath`)

- **Current Section:** "Imminent Death" — SIDEBAR_CONFIG key `imminentDeath`, label "Imminent Death", icon ⏳, HOPE code `["J0050"]`, color green
  - `RNICA.jsx:219`
- **Component Name:** `renderGenericSection("imminentDeath", ...)` — `RNICA.jsx:4016`. Inline section config with no separate named component.
- **Database Tables:**
  - `rnica_assessments.form_data` — path `form_data.imminentDeath.*`
  - Schema: `{ appearsThreeDaysOrLess, indicators[], comfortMeasuresInPlace, familyNotified, notes }`
  - `RNICA.jsx:572–580`
  - NOT synced to any separate table. None found in codebase.
- **API Endpoints:** Same 6 RNICA endpoints.
- **Validation Rules:**
  - **Warning (HOPE J0050):** `imminentDeath.appearsThreeDaysOrLess` required — `RNICA.jsx:860–862`
- **Audit Events:** None found in codebase.
- **HOPE Dependencies:**
  - **J0050** (Prognosis of 3 days or less): `imminentDeath.appearsThreeDaysOrLess` — HOPE warning. Note: J0050 is also listed in the Diagnoses SIDEBAR_CONFIG `hope` array (`RNICA.jsx:207`), suggesting it is relevant in both sections. The actual validated field for J0050 in `validateRNICA()` is `formData.imminentDeath.appearsThreeDaysOrLess` — `RNICA.jsx:860`.
  - **Must remain separate from general nursing assessment** per assignment brief (Tier 3 constraint).
- **Narrative Dependencies:** None found. `imminentDeath.notes` is a free-text field only.
- **POC Dependencies:** None found in `poc_compiler_rn_mapper.py` for imminent death keywords.
- **Order Dependencies:** None found in codebase. Comfort measures being in place (`comfortMeasuresInPlace`) and family notification (`familyNotified`) are documentation fields only.
- **Task Dependencies:** None found in codebase. `familyNotified` flag is a checkbox with no automated task creation.
- **Current Screens:** ROUTES index 16 ("Imminent Death", `formSection: "imminentDeath"`) — `RNICA.jsx:183`
- **Target Facesheet Section:** Section 7 — HOPE & Symptom Follow-Up
- **Migration Risk:** **High** — J0050 is a required CMS HOPE item; the "appears 3 days or less" assessment is a clinical/compliance gate that affects care planning and family notification documentation. Must not be merged with general nursing assessments.
- **Migration Complexity:** **Low** — Simple section; 5 fields; no facesheet sync; no sub-components; no cross-section dependencies.

---

### 9. SFV — Symptom Follow-up Visit (`sfv`)

- **Current Section:** "SFV" — SIDEBAR_CONFIG key `sfv`, label "SFV", icon 🔴, HOPE codes `["J2050","J2052","J2053"]`, color **red**
  - `RNICA.jsx:220`
- **Component Name:** `renderGenericSection("sfv", ...)` — `RNICA.jsx:4016`. No separate named component for the SFV section itself. `getSfvStatus()` is imported from `../intake/hopeReportMapper` — `RNICA.jsx:69`.
- **Database Tables:**
  - `rnica_assessments.form_data` — path `form_data.sfv.*`
  - Schema:
    ```
    {
      symptomImpactScreeningCompleted, symptomImpactScreeningDate,
      inPersonSfvCompleted, sfvDate, reasonNotCompleted, findings,
      triggeredSymptoms[],
      symptomImpactAtSfv: { pain, shortnessOfBreath, anxiety, nausea, vomiting, diarrhea, constipation, agitation },
      interventions[], notes
    }
    ```
  - `RNICA.jsx:582–594`
  - NOT synced to any separate table from `rnica_assessments.form_data`. However:
    - SFV completion is tracked in `sfv_requirements` table (via `SFVRequirement` model). SFV requirement records are created by `maybe_trigger_sfv_from_hope_timepoint()` — `hope_phase_b_engine.py:319–394`.
    - SFV requirement completion is recorded via `complete_sfv_requirement_from_visit()` — `hope_phase_b_engine.py:397–446` — when a qualifying in-person RN visit is finalized.
- **API Endpoints:** Same 6 RNICA endpoints. The SFV requirement tracking occurs via the visit finalization endpoint (`POST /visits/{visit_id}/finalize`), not directly via RNICA endpoints.
- **Validation Rules:**
  - No explicit HOPE validation in `validateRNICA()` for `sfv.*` fields (the function validates `symptomImpact`, pain, diagnoses, etc., but not the sfv section fields directly). None found.
  - SFV visit eligibility rules: must be in-person, must be by RN/LPN/LVN, must be a SEPARATE visit from the triggering INITIAL_RN_ICA/HUV — `hope_phase_b_engine.py:417–426`.
- **Audit Events:** None found in codebase for `sfv` section changes.
- **HOPE Dependencies:**
  - **J2050** (SFV Completed): `sfv.inPersonSfvCompleted` — was in-person SFV performed?
  - **J2052** (SFV Findings): `sfv.findings`
  - **J2053** (Reason SFV Not Completed): `sfv.reasonNotCompleted`
  - `sfv.symptomImpactAtSfv` mirrors the J2051 8-item scale at SFV time (the "follow-up" re-assessment of symptom impact)
  - **Must remain separate from general nursing sections** — `RNICA.jsx:14` color comment: "SFV = RED"
- **Narrative Dependencies:** None found. `sfv.findings` and `sfv.notes` are free-text.
- **POC Dependencies:** None found in `poc_compiler_rn_mapper.py` for SFV-specific keywords.
- **Order Dependencies:** None found directly from SFV section data.
- **Task Dependencies:**
  - SFV task creation: triggered by MODERATE/SEVERE symptom impact from initial RNICA (or HUV1/HUV2) — `hope_phase_b_engine.py:319–394`. Due date is 2 calendar days after trigger.
  - SFV task completion: `complete_sfv_requirement_from_visit()` is called at `visits.py:3108–3112` when a qualifying visit is finalized. Sets `SFVRequirement.status = "COMPLETED"` and completes the Task record.
- **Current Screens:** ROUTES index 17 ("SFV", `formSection: "sfv"`) — `RNICA.jsx:184`
- **Target Facesheet Section:** Section 7 — HOPE & Symptom Follow-Up
- **Migration Risk:** **High** — J2050/J2052/J2053 are CMS HOPE compliance items; SFV documentation is linked to the `sfv_requirements` table and `tasks` table; the in-person/discipline/separate-visit rules are hard-enforced in `hope_phase_b_engine.py`. Must remain visually and structurally separate from general nursing sections per CMS guidance.
- **Migration Complexity:** **High** — SFV spans two subsystems: the RNICA `form_data.sfv.*` fields AND the `sfv_requirements`/`tasks` tables; completion tracking goes through visit finalization logic, not RNICA save; `getSfvStatus()` import from `hopeReportMapper` adds an external dependency.

---

### 10. Symptom Follow-Up (J2051 at SFV — `sfv.symptomImpactAtSfv`)

- **Current Section:** This is NOT a separate top-level RNICA section. It is the `symptomImpactAtSfv` sub-object within the `sfv` section — `RNICA.jsx:588–593`.
  - In the context of HOPE, J2051 appears at two timepoints:
    1. **Initial assessment** → `form_data.symptomImpact.*` (Tier 1, area 5)
    2. **At SFV time** → `form_data.sfv.symptomImpactAtSfv.*` (this area)
  - SIDEBAR_CONFIG lists only `symptomImpact` (with HOPE J2051) as a standalone section — `RNICA.jsx:206`. There is no separate "Symptom Follow-Up" SIDEBAR_CONFIG entry distinct from `sfv`. The J2051 re-assessment at SFV time is embedded within the `sfv` section.
- **Component Name:** Inline JSX within `renderGenericSection("sfv", ...)`. No separate named component for `symptomImpactAtSfv`.
- **Database Tables:**
  - `rnica_assessments.form_data` — path `form_data.sfv.symptomImpactAtSfv.*`
  - Schema: `{ pain, shortnessOfBreath, anxiety, nausea, vomiting, diarrhea, constipation, agitation }` — mirrors the 8 J2051 fields
  - `RNICA.jsx:588–593`
  - NOT synced to any separate table. The `j2051_pain_impact` and `j2051_non_pain_impact` extracted at HUV1/HUV2 finalization time (for triggering a subsequent SFV) come from `clinical_notes` ROS data, not from this field — `visits.py:3102–3106`.
- **API Endpoints:** Same 6 RNICA endpoints.
- **Validation Rules:** None found specific to `sfv.symptomImpactAtSfv` fields in `validateRNICA()`. The `sfv` section has no HOPE validation warnings in the frontend validation function.
- **Audit Events:** None found in codebase.
- **HOPE Dependencies:**
  - J2051 at SFV timepoint — same 8 items as initial symptomImpact but documented at the SFV visit
  - If any SFV J2051 score is MODERATE/SEVERE at a HUV visit (not initial RNICA), `process_huv_finalize()` re-evaluates and may create another SFV — `hope_phase_b_engine.py:487–518`
- **Narrative Dependencies:** None found.
- **POC Dependencies:** None found for SFV-specific symptom follow-up data.
- **Order Dependencies:** None found.
- **Task Dependencies:** Same SFV task creation chain as area 9, but triggered from HUV1/HUV2 visits reading J2051 data.
- **Current Screens:** Part of ROUTES index 17 ("SFV", `formSection: "sfv"`) — `RNICA.jsx:184`
- **Target Facesheet Section:** Section 7 — HOPE & Symptom Follow-Up
- **Migration Risk:** **High** — CMS HOPE J2051 compliance at SFV timepoint; must be kept separate from the initial J2051 screening (area 5); the two J2051 snapshots must both be present in submitted HOPE data.
- **Migration Complexity:** **Low** — Structurally simple (8 score fields, sub-key of `sfv`); no separate sub-components; the complexity is conceptual (two J2051 timepoints that must not be merged).

---

### 11. HOPE Elements — General Cross-Cutting Master List

- **Current Section:** There is **no dedicated "HOPE Elements" screen or route** in RNICA.jsx. HOPE item codes are distributed across sections. The master list/mapping is defined in two places:

  **A. SIDEBAR_CONFIG `hope` arrays** (per-section HOPE code lists) — `RNICA.jsx:199–235`:
  | Section Key | HOPE Item IDs |
  |---|---|
  | `demographics` | A1110, A1005, A1010 |
  | `advancedCarePlanning` | F2000, F2100, F2200 |
  | `pain` | J0900, J0915 |
  | `symptomImpact` | J2051 |
  | `diagnoses` | I0010, J0050 |
  | `performanceStatus` | M1190 |
  | `neurological` | N0500, N0510, N0520 |
  | `skin` | M1190 |
  | `imminentDeath` | J0050 |
  | `sfv` | J2050, J2052, J2053 |
  | `finalization` | F2000, F2100, F2200 |

  **B. `HOPE_COMORBIDITY_CATEGORIES` array** (I-section comorbidities) — `RNICA.jsx:1826–1841`:
  | HOPE Code | Condition | Form Field |
  |---|---|---|
  | I0100 | Cancer | `diagnoses.hopeComorbidities.cancer` |
  | I0600 | Heart Failure | `diagnoses.hopeComorbidities.heartFailure` |
  | I0900 | PVD/PAD | `diagnoses.hopeComorbidities.pvdPad` |
  | I0950 | Cardiovascular (excl. HF) | `diagnoses.hopeComorbidities.cardiovascularExclHF` |
  | I1101 | Liver Disease | `diagnoses.hopeComorbidities.liverDisease` |
  | I1510 | Renal Disease | `diagnoses.hopeComorbidities.renalDisease` |
  | I2102 | Sepsis | `diagnoses.hopeComorbidities.sepsis` |
  | I2900 | Diabetes Mellitus | `diagnoses.hopeComorbidities.diabetesMellitus` |
  | I2910 | Neuropathy | `diagnoses.hopeComorbidities.neuropathy` |
  | I4501 | Stroke | `diagnoses.hopeComorbidities.stroke` |
  | I4801 | Dementia/Alzheimer's | `diagnoses.hopeComorbidities.dementia` |
  | I5150 | Neurological Conditions | `diagnoses.hopeComorbidities.neurologicalConditions` |
  | I5401 | Seizure Disorder | `diagnoses.hopeComorbidities.seizureDisorder` |
  | I6202 | COPD | `diagnoses.hopeComorbidities.copd` |
  | I8005 | Other Medical Condition | `diagnoses.hopeComorbidities.other` |

  **C. Validation function `validateRNICA()`** — `RNICA.jsx:765–886` — checks: A1005, A1010, A1110, F2000, F2100, F2200, J0900, J0915, J2051(A–H), I0010, M1190, N0500, J0050. This is the closest thing to a "master HOPE validation list" in the codebase.

  **D. `hopeReportMapper.js`** (referenced by import at `RNICA.jsx:69`): `getSfvStatus()` is imported from `../intake/hopeReportMapper` — suggests a separate mapper file handles HOPE report generation, but it is not within this file's scope.

- **Component Name:** `HopeTag({ code })` — `RNICA.jsx:1041–1048` — renders green HOPE badge inline. `HopeComorbiditiesCard` — `RNICA.jsx:1853–1974` — is the main HOPE I-section UI. The `AssessmentModeContext` controls whether HOPE tags/validations apply (`mode === "ongoing"` suppresses HOPE items) — `RNICA.jsx:153`.
- **Database Tables:** All HOPE field values are stored in `rnica_assessments.form_data` across various paths (as itemized above). `hopeComorbidities.*` specifically at `form_data.diagnoses.hopeComorbidities.*`.
- **API Endpoints:** Same 6 RNICA endpoints. `finalization.hopeSubmissionNumber` and `finalization.hopeAlreadySubmitted` track submission state — `RNICA.jsx:735–736`.
- **Validation Rules:** See `validateRNICA()` — `RNICA.jsx:776–862` — centralizes all HOPE field validations. Mode-gated: `includeHopeRequirements = mode !== "ongoing"` — `RNICA.jsx:768`.
- **Audit Events:** None found in codebase for HOPE submission or comorbidity changes.
- **HOPE Dependencies:** This IS the master list — self-referential. All HOPE items in RNICA map to fields in other sections. The I-section comorbidities (`I0100–I8005`) require clinician confirmation; they are NEVER auto-checked silently — `RNICA.jsx:1897–1943`.
- **Narrative Dependencies:** HOPE comorbidities affect LCD eligibility evaluation (e.g., `heartFailure` → NYHA criteria, `copd` → PO2/PCO2 criteria).
- **POC Dependencies:** HOPE comorbidity categories map closely to `poc_compiler_rn_mapper.py` RULE_KEYWORDS (`chf`, `copd`, `cancer`, `dementia`, `stroke`, etc.) — `poc_compiler_rn_mapper.py:46–84`.
- **Order Dependencies:** None directly from HOPE items themselves.
- **Task Dependencies:** J2051 HOPE items trigger SFV tasks (covered in areas 5, 9, 10).
- **Current Screens:** Distributed — no single screen. Key screens: Demographics (A-codes, F-codes), Diagnoses (I-codes, J0050), Pain (J0900/J0915), Symptom Impact (J2051), Performance Status (M1190), Neurological (N-codes), Imminent Death (J0050), SFV (J2050–J2053), Finalization (F-codes recap).
- **Target Facesheet Section:** Section 7 — HOPE & Symptom Follow-Up
- **Migration Risk:** **High** — CMS HOPE compliance; any restructuring that merges or reorders these sections must preserve the exact field-to-HOPE-ID mappings; the `AssessmentModeContext` "ongoing" mode suppressor must be preserved.
- **Migration Complexity:** **High** — Distributed across 10+ sections; no single centralized backend HOPE table; the `hopeReportMapper.js` import indicates an external mapper that must be kept in sync.

---

## Tier 9 — Finalization

---

### 12. Finalization (`finalization`)

- **Current Section:** "Finalization" — SIDEBAR_CONFIG key `finalization`, label "Finalization", icon ✅, HOPE codes `["F2000","F2100","F2200"]`, color green
  - `RNICA.jsx:235`
- **Component Name:** `renderGenericSection("finalization", ...)` — `RNICA.jsx:4016`. No separate named component; inline section config.
- **Database Tables:**
  - `rnica_assessments.form_data` — path `form_data.finalization.*`
  - Schema:
    ```
    {
      completedSections[],
      incompleteCount,
      responseToInterventions: {
        initialResponseSummary, interventionEffectiveness[], baselineEstablished, baselineDate, progressNotes
      },
      pocEntries[],
      pocDraft: { problem, goal, intervention, discipline },
      pocGenerationCompleted,
      pocReviewedWithIdg,
      signatureCertification,
      clinicianSignature,
      signatureDate,
      hopeSubmissionNumber,
      hopeAlreadySubmitted,
      supervisorReview: { required, reviewedBy, reviewDate },
      assessmentLocked,
      lockedTimestamp
    }
    ```
  - `RNICA.jsx:715–741`
  - `rnica_assessments` model top-level columns also track lock state: `locked` (Boolean), `locked_at` (DateTime), `status` (String: "DRAFT"/"LOCKED") — `backend/app/models/rnica_assessment.py:24,29–31`. These are redundant with `form_data.finalization.assessmentLocked` / `lockedTimestamp`.
  - `finalization.pocEntries[]` stores POC problems generated during RNICA; the authoritative POC table is separate (managed by `poc_compiler_service.py`, `poc_engine.py`, etc.), but the relationship/sync between `rnica_assessments.form_data.finalization.pocEntries` and the canonical POC tables is **not directly evident** in `visits.py` RNICA endpoints.
- **API Endpoints:**
  - `POST /visits/rnica/{assessment_id}/lock` — locks assessment: sets `rnica_assessments.locked = True`, `status = "LOCKED"`, `locked_at = now()` — `visits.py:978–999`
  - `PUT /visits/rnica/{assessment_id}` — saves draft including finalization fields
  - `POST /visits/rnica/save` — initial save
  - Visit-level finalization (different from RNICA lock): `POST /visits/{visit_id}/finalize` triggers `process_initial_rn_ica_finalize()` when `INITIAL_RN_ICA` task type is completed — `visits.py:3114–3130`. This creates HUV1/HUV2 tasks and potentially SFV task. This is on the `Visit` model, not `RnicaAssessment`.
- **Validation Rules:**
  - **Error:** `finalization.clinicianSignature` required — `RNICA.jsx:881–883`
  - **Warning (CDPH):** `finalization.pocGenerationCompleted` must be true — `RNICA.jsx:822–825`
  - **Error (Admissions Order, logically part of pre-finalization gates):** `admissionsOrder.levelOfCare.level` and `admissionsOrder.toVerification.verbalOrderReadBack` required — `RNICA.jsx:871–878`
  - All previous section HOPE warnings/errors must be resolved for clean finalization
  - Lock endpoint has no RNICA-specific pre-lock validation in `visits.py:978–999` (unlike MSW ICA which blocks lock if suicide risk notifications are incomplete — `visits.py:1193–1197`). None found.
- **Audit Events:**
  - **`FINALIZE_VISIT`** (entity_type: "visit") — logged at `visits.py:4439–4444` and `visits.py:4576–4581` when a Visit is finalized. This is the Visit finalization, NOT the RNICA lock. The RNICA lock endpoint (`POST /visits/rnica/{assessment_id}/lock`) has **no `_safe_log_event` call**. None found in codebase for RNICA-specific lock audit.
  - The pattern is consistent: all other RNICA CRUD operations (save, update, lock) lack audit logging.
- **HOPE Dependencies:**
  - F2000/F2100/F2200 are listed in `finalization` SIDEBAR_CONFIG `hope` array — `RNICA.jsx:235` — implying these ACP HOPE items are re-confirmed or surfaced in the finalization review checklist.
  - `finalization.hopeSubmissionNumber` and `finalization.hopeAlreadySubmitted` — track CMS HOPE submission state — `RNICA.jsx:735–736`.
  - `finalization.completedSections[]` and `finalization.incompleteCount` track HOPE section completion status for pre-lock gate.
  - Visit-level `process_initial_rn_ica_finalize()` creates HUV1/HUV2 and SFV tasks based on J2051 symptom impact data — `hope_phase_b_engine.py:449–484`, `visits.py:3122–3130`. These are finalization-time HOPE Phase B dependencies.
- **Narrative Dependencies:**
  - `finalization.responseToInterventions.initialResponseSummary` and `progressNotes` are free-text baseline documentation fields (CDPH Gap #3) — `RNICA.jsx:720–727`.
  - `finalization.pocEntries[]` is where POC problems generated during assessment are stored — `RNICA.jsx:729`.
  - No auto-generation of `lcdEligibilityNarrative` from finalization data.
- **POC Dependencies:**
  - `finalization.pocEntries[]` stores the POC problems/goals/interventions identified during the RNICA — `RNICA.jsx:729`. `pocGenerationCompleted` flag is a CDPH required gate — `RNICA.jsx:823`.
  - `poc_compiler_rn_mapper.py:map_rn_ica_to_problem_nodes()` maps RN ICA data to POC problem nodes for the canonical POC service. The relationship between `rnica_assessments.form_data.finalization.pocEntries` and the canonical POC tables managed by `poc_engine.py`/`poc_service.py` is a **gap** — no explicit sync call found in RNICA CRUD endpoints. None found in codebase.
  - `finalization.pocReviewedWithIdg` flag — `RNICA.jsx:730`.
- **Order Dependencies:**
  - RNICA lock does NOT automatically submit orders. Orders (medications, DME, etc.) in `ordersHub`/`admissionsOrder` sections have their own submission paths (`physician_order_service.py`). However, `admissionsOrder.levelOfCare.level` is required before lock (validation error) — `RNICA.jsx:871`.
  - At visit finalization, `sync_official_primary_diagnosis()` is called with diagnosis from clinical notes — `visits.py:3136–3144`. Level of care is synced to `patient_facesheet.current_level_of_care` via `_extract_rnica_level_of_care()` — `visits.py:284–290,397–412`.
- **Task Dependencies:**
  - **HUV1 task** (HOPE Phase B — days 6–15) and **HUV2 task** (days 16–30) are created when an INITIAL_RN_ICA task type visit is finalized — `hope_phase_b_engine.py:262–300`, `visits.py:3122–3130`.
  - **SFV task** (within 2 calendar days) created if J2051 MODERATE/SEVERE — `hope_phase_b_engine.py:319–394`.
  - **`auto_complete_tasks_for_visit()`** is also called at finalization — `visits.py:80`; completes any open tasks associated with this visit.
  - `finalization.supervisorReview.required` — `RNICA.jsx:737` — flag for supervisor review workflow, but no automated task creation found for this flag in the RNICA lock endpoint. None found in codebase.
- **Amendment logic:** The RNICA lock endpoint is a simple boolean flip (`locked = True`) with no amendment/addendum workflow. The general visit reopen logic (`REOPEN_VISIT` at `visits.py:3780`) applies to `Visit` records. No RNICA-specific amendment/unlock endpoint found. None found in codebase.
- **Current Screens:** ROUTES index 27 ("Finalization", `formSection: "finalization"`) — `RNICA.jsx:196`
- **Target Facesheet Section:** Section 12 — Final Review & Finalization
- **Migration Risk:** **High** — Clinician signature required for legal validity; HOPE F2000/F2100/F2200 re-confirmation; HUV1/HUV2/SFV task creation is gated on visit finalization; POC generation required (CDPH Gap #4). No RNICA-specific amendment workflow exists — a significant compliance gap.
- **Migration Complexity:** **High** — Finalization bridges RNICA `form_data` state, the `RnicaAssessment` model's `locked/status/locked_at` columns, the `Visit` model's finalization, HOPE Phase B task creation (`hope_phase_b_engine.py`), POC generation (`poc_compiler_rn_mapper.py`), and facesheet/diagnosis syncs. Two separate "lock" concepts exist: `RnicaAssessment.locked` (RNICA-specific) and `Visit.status = FINALIZED` (visit-level). The relationship between them is not explicitly enforced in code.

---

## Cross-Cutting Gaps Identified

1. **No RNICA-specific audit logging** on any of the 5 RNICA CRUD endpoints (`save`, `GET`, `by-patient`, `update`, `lock`) — `visits.py:751–999`. Only general `FINALIZE_VISIT` on `Visit` rows is logged.
2. **ACP storage path mismatch**: INITIAL_FORM places ACP at `demographics.advancedCarePlanning` (`RNICA.jsx:337–343`), but backend helpers read/write `form_data.advancedCarePlanning` at top-level (`visits.py:238–265, 819–855`). This could cause the code-status sync and DPOA sync to silently read empty values.
3. **No RNICA pre-lock validation on backend**: The `POST /visits/rnica/{assessment_id}/lock` endpoint does not enforce any HOPE completeness check — unlike MSW ICA which blocks lock on missing suicide notifications (`visits.py:1193–1197`).
4. **No amendment/addendum workflow** for locked RNICA assessments (`rnica_assessments.locked = True`). None found in codebase.
5. **`lcdEligibilityNarrative` is manual**: No auto-generation; the LCD criteria evaluation UI shows pass/fail but the narrative field requires manual entry.
6. **`finalization.pocEntries` vs. canonical POC tables**: The relationship between RNICA-local POC entries and the authoritative POC engine (`poc_service.py`, `poc_engine.py`) has no explicit sync call in any RNICA endpoint. None found in codebase.
7. **J2051 at finalization reads from `clinical_notes`**, not from `rnica_assessments.form_data.symptomImpact` — `visits.py:3102–3106`. This means the HOPE Phase B SFV trigger depends on the clinical note being present, not just the RNICA form being saved.

---

# RNICA Technical Inventory — Head-to-Toe Clinical Systems + Safety
## Scope: Sections 1–11 of the Head-To-Toe Body Systems + Safety Assignment

> **Citation format used throughout:** `file:line-range`
> All data-store claims reference `backend/app/models/rnica_assessment.py` (JSONB `form_data` column, lines 26).
> All frontend section configs reference `sns-emr-frontend/src/components/RNICA.jsx`.
> All backend API references are to `backend/app/api/visits.py`.
> All validation references are to `backend/app/services/clinical_note_validation_engine.py` unless stated otherwise.

---

### ### 1 — Neurological

- **Current Section:** `Neurological` — sidebar label "Neurological" (`SIDEBAR_CONFIG` entry, `RNICA.jsx:209`)
- **Component Name:** No named React component. Rendered via `renderGenericSection()` (inline function, `RNICA.jsx:5669`) consuming the `SECTION_CONFIGS.neurological` data-driven config object (`RNICA.jsx:4655–4707`). Section header + collapse driven by `renderAllSections()` (`RNICA.jsx:5628–5675`).
- **Database Tables:** Single table — `rnica_assessments` (`backend/app/models/rnica_assessment.py:11`). Data stored as JSON key `form_data.neurological` within the `form_data` JSONB column (line 26). Shape defined in `INITIAL_FORM.neurological` (`RNICA.jsx:439–452`): includes `consciousness`, `orientation`, `communication`, `hearing`, `vision`, `balance`, `cognition`, `delirium`, `seizureHistory`, `psychiatricHistory`, `sensoryDeficits`, `sleepRest`, `hopeItems` (n0500/n0510/n0520), `notes`. No separate table.
- **API Endpoints:**
  - `POST /visits/rnica/save` — creates assessment (`visits.py:751`)
  - `GET /visits/rnica/{assessment_id}` — fetches by ID (`visits.py:860`)
  - `GET /visits/rnica/by-patient/{patient_id}` — fetches latest for patient (`visits.py:892`)
  - `PUT /visits/rnica/{assessment_id}` — updates (`visits.py:930`)
  - `POST /visits/rnica/{assessment_id}/lock` — locks (`visits.py:978`)
  - `GET /visits/rnica/{assessment_id}/intelligence` — AI signal summary (`visits.py:1002`)
  - *(All RNICA endpoints share these 6; none are section-specific.)*
- **Validation Rules:**
  - **HOPE warning (frontend, `validateRNICA`):** `neurological.hopeItems.n0500` missing → warning `"HOPE N0500: BIMS repetition required"` (`RNICA.jsx:855–856`). Applies only in ICA mode (not `ongoing`).
  - **Backend ROS completeness (`_validate_required_ros`):** `neurological` is in `REQUIRED_FULL_ROS_SECTIONS` (`clinical_note_validation_engine.py:67–69`). For comprehensive-encounter ClinicalNotes (not RNICA endpoint directly), absence of neurological ROS data generates a compliance-blocking item. The ROS completeness check requires at least one of: `mental_status`, `orientation`, `cognitive_status`, `communication_ability`, `speech_pattern`, `confusion`, `agitation`, `anxiety`, `neuro_narrative`, or `narrative` (`clinical_note_validation_engine.py:192–205`).
  - **Backend RN ICA required fields:** `neurological.cognitiveDecline` listed as a tracked path in `RN_ICA_REQUIRED_FIELD_GROUPS` (`clinical_note_validation_engine.py:504–511`); generates `rn_ica_required_missing` warning/audit_flag if absent.
  - No required-field hard errors for neurological body-system fields in the frontend `validateRNICA`.
- **Audit Events:** None found. The `save_rnica_assessment`, `update_rnica_assessment`, and `lock_rnica_assessment` endpoints in `visits.py` (lines 751–999) contain no `log_event` / `_safe_log_event` calls. The `_write_audit_log` in the validation engine (`clinical_note_validation_engine.py:699–706`) fires only for `ClinicalNote` objects, not `RnicaAssessment` objects. **Audit logging for RNICA save/update/lock: None found in codebase.**
- **HOPE Dependencies:** `N0500` (BIMS Repetition), `N0510` (BIMS Recall), `N0520` (Temporal Orientation) — explicitly declared in `SIDEBAR_CONFIG` (`RNICA.jsx:209`) and in `INITIAL_FORM.neurological.hopeItems` (`RNICA.jsx:451`). Frontend validation warning fires on missing `n0500` (`RNICA.jsx:855–856`). N0510 and N0520 are captured in fields but have no dedicated validation warning in the current codebase beyond the HOPE tag display.
- **Narrative Dependencies:** `neurological.cognitiveDecline` is a tracked path in `RN_ICA_REQUIRED_FIELD_GROUPS` (`clinical_note_validation_engine.py:504–511`) and feeds into general RN ICA completeness checking. No code found that auto-populates `diagnoses.lcdEligibilityNarrative` from neurological data. The `evidence_harvester.py` does not explicitly harvest any `neurological.*` form keys as named facts (though text-based harvesting may pick up narrative fields). **No direct wiring to `lcdEligibilityNarrative` found.**
- **POC Dependencies:** The `poc_compiler_rn_mapper.py` includes `confusion_delirium` and `seizure_disorder` as rule keywords (`RNICA.jsx:73,82`) and maps clinical text terms like `"confusion"`, `"delirium"`, `"agitation"`, `"seizure"` to those POC rule keywords (`poc_compiler_rn_mapper.py:46–84`). The `neurological` section's free-text `notes` and structured fields can indirectly feed POC keyword detection. Direct programmatic extraction of `neurological.*` fields into POC node creation: **not confirmed in codebase**; linkage is text-match–based only.
- **Order Dependencies:** None found. No code in `visits.py` or any service generates an order from `neurological` section data.
- **Task Dependencies:** None found directly tied to neurological section.
- **Current Screens:** RNICA is a single-page scrollable accordion. The `neurological` route is at position 7 in the `ROUTES` array (0-indexed: 6), between `performanceStatus` and `cardiovascular` (`RNICA.jsx:173`). Rendered as an accordion panel with section key `"neurological"`, `formSection: "neurological"`. No separate route/URL for individual sections.
- **Target Facesheet Section:** Section 5 — Head-To-Toe Clinical Assessment
- **Migration Risk:** **High** — HOPE items N0500–N0520 are CMS-required data elements. Restructuring this section must preserve the three BIMS sub-fields and the HOPE validation warning; any UI reorganization that loses BIMS capture breaks HOPE submission compliance.
- **Migration Complexity:** **High** — Three HOPE-coded sub-fields (BIMS) with backend validation checks, a cognitive-decline path tracked in the RN ICA required field group, and indirect POC keyword linkage via text analysis.

---

### ### 2 — Cardiovascular

- **Current Section:** `Cardiovascular` — sidebar label "Cardiovascular" (`SIDEBAR_CONFIG`, `RNICA.jsx:210`)
- **Component Name:** No named React component. Rendered via `renderGenericSection()` (`RNICA.jsx:5669`) consuming `SECTION_CONFIGS.cardiovascular` (`RNICA.jsx:4709–4727`). Accordion shell via `renderAllSections()` (`RNICA.jsx:5628–5675`).
- **Database Tables:** `rnica_assessments.form_data.cardiovascular` (JSONB key). Shape: `bpSymptoms`, `pulseQuality`, `edema` (present/location/severity/pitting), `chestPain` (present/type/frequency), `peripheralCirculation`, `heartSounds`, `jvd`, `notes` (`RNICA.jsx:455–462`). No separate table.
- **API Endpoints:** Same six shared RNICA endpoints as above (`visits.py:751–1027`). No cardiovascular-specific endpoint.
- **Validation Rules:**
  - No frontend required-field validation errors or warnings in `validateRNICA` for cardiovascular fields (`RNICA.jsx:765–886` reviewed — no `cardiovascular.*` checks).
  - Backend ROS completeness: `cardiovascular` is in `REQUIRED_FULL_ROS_SECTIONS` (`clinical_note_validation_engine.py:68`). For comprehensive ClinicalNotes, any of `heart_rhythm`, `edema`, `edema_location`, `pulse_assessment`, `chest_pain`, `dizziness`, `syncope`, `cardiac_findings`, `cardiovascular_narrative`, or `narrative` must be present (`clinical_note_validation_engine.py:207–221`).
  - No fields from this section appear in `RN_ICA_REQUIRED_FIELD_GROUPS`.
- **Audit Events:** None found (same as above — no `log_event` calls in RNICA endpoints).
- **HOPE Dependencies:** None. `hope: []` in `SIDEBAR_CONFIG` (`RNICA.jsx:210`).
- **Narrative Dependencies:** `edema` location and `bpSymptoms` may be text-harvested indirectly. The `poc_compiler_rn_mapper.py` includes `"edema"` as a rule keyword (`RNICA.jsx:71`); relevant cardiovascular text could feed POC detection. `CARDIAC_DIAGNOSIS_KEYWORDS` in the validation engine (`clinical_note_validation_engine.py:124–138`) triggers conditional NYHA requirement when cardiac diagnoses are present — this is a diagnosis-driven check, not a cardiovascular section check. **No direct wiring to `lcdEligibilityNarrative`.**
- **POC Dependencies:** Text-match–based only via `poc_compiler_rn_mapper.py`; `edema`, `cardiac_disease`, `chf` keywords. No direct field mapping from `cardiovascular.*` to POC nodes found.
- **Order Dependencies:** None found.
- **Task Dependencies:** None found.
- **Current Screens:** Route position 8 (ROUTES index 7), key `"cardiovascular"` (`RNICA.jsx:174`). Single-page accordion panel.
- **Target Facesheet Section:** Section 5 — Head-To-Toe Clinical Assessment
- **Migration Risk:** **Low** — No HOPE items, no required-field validation, no cross-section data dependencies that would break on restructure.
- **Migration Complexity:** **Low** — Purely data-collection fields; no custom renderers, no external sync side-effects, no downstream order or narrative generation.

---

### ### 3 — Respiratory

- **Current Section:** `Respiratory` — sidebar label "Respiratory" (`SIDEBAR_CONFIG`, `RNICA.jsx:211`); `sfv: true` flag present.
- **Component Name:** No named React component. Rendered via `renderGenericSection()` (`RNICA.jsx:5669`) consuming `SECTION_CONFIGS.respiratory` (`RNICA.jsx:4729–4756`). Two cards: "Respiratory Assessment" and "Oxygen Therapy."
- **Database Tables:** `rnica_assessments.form_data.respiratory` (JSONB key). Shape: `sobSeverity`, `exertionLevel`, `shortnessOfBreathScreened`, `screeningDate`, `treatmentInitiated`, `treatmentDate`, `lungSounds[]`, `respirations[]`, `coughType`, `sputumCharacter`, `oxygenTherapy` (inUse, type, litersPerMinute, hoursPerDay, satOnO2), `notes` (`RNICA.jsx:465–476`). Also indirectly referenced via `formData.vitals.oxygenSaturation` (`RNICA.jsx:1379`) in LCD evidence calculations. No separate table.
- **API Endpoints:** Same six shared RNICA endpoints.
- **Validation Rules:**
  - **Frontend:** `sobSeverity` field has `sfv: true` flag in config (`RNICA.jsx:4734`), meaning Moderate/Severe triggers the SFV-Required banner (via `getSfvStatus()` at `RNICA.jsx:5822–5833`). No hard `errors[]` for respiratory fields in `validateRNICA`.
  - **Backend ROS completeness:** `respiratory` in `REQUIRED_FULL_ROS_SECTIONS` (`clinical_note_validation_engine.py:70`) and `REQUIRED_FOCUSED_ROS_SECTIONS` (`clinical_note_validation_engine.py:82`). Minimum acceptable fields: `dyspnea`, `dyspnea_level`, `oxygen_use`, `oxygen_used`, `oxygen_lpm`, `lung_sounds`, `respiratory_effort`, `cough`, `secretions`, `orthopnea`, `respiratory_narrative`, or `narrative` (`clinical_note_validation_engine.py:222–238`).
  - **Backend symptom intervention check:** `_validate_symptom_interventions` warns `"moderate_or_severe_dyspnea_without_intervention"` if `dyspnea_level` is MODERATE/SEVERE/AT_REST and no `interventions.respiratory` is documented (`clinical_note_validation_engine.py:1452–1454`).
  - **Backend RN ICA required:** `"Respiratory Rate"` in `RN_ICA_REQUIRED_FIELD_GROUPS`, resolved from `vitals.respirations` or `respiratory.respiratoryRate` (`clinical_note_validation_engine.py:459–467`).
- **Audit Events:** None found in RNICA-specific endpoints.
- **HOPE Dependencies:** None. `hope: []` in `SIDEBAR_CONFIG` (`RNICA.jsx:211`). However `sfv: true` — SOB severity at Moderate/Severe activates the SFV required workflow (HOPE J2050/J2052/J2053), making this section indirectly critical for HOPE SFV compliance.
- **Narrative Dependencies:** The `evidence_harvester.py` includes `"respiratory"` as one of the recognized form-data sections to scan (`evidence_harvester.py:791`). It specifically harvests `o2_sat_percent` (from `oxygenTherapy.satOnO2` or `vitals.oxygenSaturation`, `evidence_harvester.py:536–551`) and `respiratory_failure_history` (`evidence_harvester.py:710`). These facts feed into the NDS/LCD eligibility engine (e.g., PULMONARY_COPD criteria, `eligibility/engine.py:19–25`). **However, no code auto-generates text in `diagnoses.lcdEligibilityNarrative` from respiratory data.** The narrative field is free-text, manually authored. The CMS LCD guidance expectation (dyspnea as prognosis evidence) is NOT automatically wired in the current codebase.
- **POC Dependencies:** `poc_compiler_rn_mapper.py` maps `"dyspnea"` and SOB-related text keywords to the `dyspnea` POC rule keyword (`poc_compiler_rn_mapper.py:178–179`). Text from `respiratory.notes` or `sobSeverity` values can feed this mapper. No direct field extraction from `respiratory.*` confirmed.
- **Order Dependencies:** `respiratory.oxygenTherapy.inUse` and `respiratory.oxygenTherapy.litersPerMinute` fields exist and capture oxygen use. The safety section also has an `oxygenInUse` checkbox. **However, no code in `visits.py`, `rnica_intelligence.py`, or any service automatically generates an Oxygen order from these fields.** The governance documentation expectation that Respiratory triggers Oxygen/DME orders is **not implemented in the current codebase**; it is conceptual/future work.
- **Task Dependencies:** Moderate/Severe SOB triggers the SFV required notification banner (`RNICA.jsx:5822–5833`) and, on the SFV section side, drives HOPE SFV task creation via `hope_phase_b_engine.py`. The respiratory section is an upstream trigger for that task chain, but no task is created directly from the respiratory section endpoint.
- **Current Screens:** Route position 9 (ROUTES index 8), key `"respiratory"`, `formSection: "respiratory"` (`RNICA.jsx:175`).
- **Target Facesheet Section:** Section 5 — Head-To-Toe Clinical Assessment
- **Migration Risk:** **Medium** — SFV trigger logic (`sfv: true` flag + SOB severity thresholds) means any refactoring of `sobSeverity` field name or path must preserve SFV activation. The oxygen therapy sub-object is referenced by the eligibility evidence harvester. Breaking the `respiratory.oxygenTherapy.satOnO2` path would silently break LCD evidence collection.
- **Migration Complexity:** **Medium** — Two-card layout, SFV flag, evidence harvester cross-reference for O2 sat, symptom-intervention validation hook in the backend engine.

---

### ### 4 — Infection

- **Current Section:** `Infection` — sidebar label "Infection" (`SIDEBAR_CONFIG`, `RNICA.jsx:212`)
- **Component Name:** No named React component. Rendered via `renderGenericSection()` (`RNICA.jsx:5669`) consuming `SECTION_CONFIGS.infection` (`RNICA.jsx:4758–4768`). One card: "Infection Assessment."
- **Database Tables:** `rnica_assessments.form_data.infection` (JSONB key). Shape: `allergies[]`, `currentInfections[]`, `historyOfResistantInfections[]`, `immunosuppressed`, `precautions[]`, `notes` (`RNICA.jsx:479–486`). **Important:** `infection.allergies` is additionally synced to the shared `patient_allergies` table via `sync_allergies_from_source()` called inside `_sync_shared_records_from_rnica()` on every save and update (`visits.py:234–235, 344–348`). This is the only section in the 11 that writes to a separate table beyond `rnica_assessments`.
- **API Endpoints:** Same six shared RNICA endpoints. The allergy sync side-effect runs on `POST /visits/rnica/save` and `PUT /visits/rnica/{assessment_id}` (`visits.py:787–793, 963–969`).
- **Validation Rules:**
  - No frontend required-field validation errors or warnings in `validateRNICA` for infection fields.
  - No infection-specific rules in `RN_ICA_REQUIRED_FIELD_GROUPS`.
  - Backend ROS completeness: `infection` / `immunological` are NOT in `REQUIRED_FULL_ROS_SECTIONS` (`clinical_note_validation_engine.py:66–78`). No ROS completeness check applies to this section.
- **Audit Events:** None found in RNICA-specific endpoints. (The `sync_allergies_from_source` function writes to `patient_allergies` but no `log_event` is called from it or from the RNICA save/update endpoints.)
- **HOPE Dependencies:** None. `hope: []` (`RNICA.jsx:212`).
- **Narrative Dependencies:** `_build_rnica_allergy_summary()` (`visits.py:166–172`) reads `infection.allergies` and writes to `patient_facesheet.allergies` and `patient_facesheet.has_allergies` on every RNICA save/update (`visits.py:206–210`). This is facesheet text-field mirroring, not an LCD narrative. **No wiring to `diagnoses.lcdEligibilityNarrative`.**
- **POC Dependencies:** No direct POC compiler linkage from infection fields found. `"infection"` is a rule keyword in `poc_compiler_rn_mapper.py` (`RNICA.jsx:59`), so free text from `infection.notes` can match it via text analysis, but no direct field extraction.
- **Order Dependencies:** None found. No code auto-generates antibiotic or wound-care orders from infection section data.
- **Task Dependencies:** None found.
- **Current Screens:** Route position 10 (ROUTES index 9), key `"infection"`, `formSection: "infection"` (`RNICA.jsx:176`).
- **Target Facesheet Section:** Section 5 — Head-To-Toe Clinical Assessment
- **Migration Risk:** **Medium** — The `infection.allergies` array is the source of truth for the shared `patient_allergies` table sync. Any path change to this field (e.g., renaming `infection` to something else in the form data shape) will silently break allergy propagation to the shared table and to the Facesheet `allergies` field.
- **Migration Complexity:** **Medium** — The allergy sync side-effect (writes to `patient_allergies` table on every RNICA save) means this section has a hidden write path to a separate table that must be preserved or re-implemented in the redesign.

---

### ### 5 — GI (Gastrointestinal)

- **Current Section:** `Gastrointestinal` — sidebar label "Gastrointestinal" (`SIDEBAR_CONFIG`, `RNICA.jsx:213`); `sfv: true` flag present.
- **Component Name:** No named React component for the section overall. Rendered via `renderGenericSection()` (`RNICA.jsx:5669`). However, the "Constipation — Auto-Suggested from Last BM Date" card uses `ConstipationAutoAssessCard` — a named helper component (`RNICA.jsx:2286–2371`) — via a `customRenderer: "constipationAutoAssess"` dispatch in `renderGenericSection` (`RNICA.jsx:4144–4156`). All other GI cards use generic field rendering.
- **Database Tables:** `rnica_assessments.form_data.gastrointestinal` (JSONB key). Shape: `nausea`, `vomiting`, `diarrhea`, `constipation`, `bowelSounds`, `abdomen`, `bowelStatus`, `lastBM`, `continence`, `feedingTube` (present/type/site), `ostomy` (present/type/condition), `notes` (`RNICA.jsx:489–496`). No separate table.
- **API Endpoints:** Same six shared RNICA endpoints.
- **Validation Rules:**
  - **Frontend:** `nausea`, `vomiting`, `diarrhea`, `constipation` fields all have `sfv: true` flag (`RNICA.jsx:4776–4779`). Moderate/Severe values trigger the SFV-Required banner.
  - No hard errors/warnings in `validateRNICA` for GI-specific fields.
  - **Backend ROS completeness:** `gastrointestinal` in both `REQUIRED_FULL_ROS_SECTIONS` (`clinical_note_validation_engine.py:71`) and `REQUIRED_FOCUSED_ROS_SECTIONS` (`clinical_note_validation_engine.py:83`). Minimum fields: `appetite`, `oral_intake`, `food_intake`, `nausea`, `vomiting`, `constipation`, `diarrhea`, `bowel_pattern`, `dysphagia`, `nutrition`, `gi_narrative`, or `narrative` (`clinical_note_validation_engine.py:239–255`).
  - **Backend RN ICA required:** `"Appetite / Intake"` in `RN_ICA_REQUIRED_FIELD_GROUPS` resolves from `nutrition.appetite` or `gastrointestinal.appetite` (`clinical_note_validation_engine.py:477–485`).
  - `gastrointestinal.bowelStatus` and `gastrointestinal.ostomy.present` are read in the LCD eligibility evidence logic (`RNICA.jsx:1343, 1350, 1371`) to detect continence-related ADL dependency.
- **Audit Events:** None found.
- **HOPE Dependencies:** None. `hope: []` (`RNICA.jsx:213`). `sfv: true` means GI symptom severity drives HOPE SFV workflow indirectly (J2051 D–G).
- **Narrative Dependencies:** GI symptom data feeds the `ConstipationAutoAssessCard` which auto-suggests a constipation severity rating from `lastBM` and `diarrhea` fields. `gastrointestinal.appetite` / `gastrointestinal.bowelStatus` contribute to continence/ADL dependency facts in the LCD evidence harvester (`RNICA.jsx:1342–1350`). **No direct auto-population of `diagnoses.lcdEligibilityNarrative` from GI data.**
- **POC Dependencies:** `nausea_vomiting` and `constipation` are POC rule keywords (`poc_compiler_rn_mapper.py:76–79`). Text-match–based only.
- **Order Dependencies:** None found. Feeding tube and ostomy presence is captured but no order is auto-generated from it.
- **Task Dependencies:** Moderate/Severe nausea/vomiting/diarrhea/constipation trigger the SFV required workflow upstream.
- **Current Screens:** Route position 11 (ROUTES index 10), key `"gastrointestinal"`, `formSection: "gastrointestinal"` (`RNICA.jsx:177`).
- **Target Facesheet Section:** Section 5 — Head-To-Toe Clinical Assessment
- **Migration Risk:** **Medium** — Four SFV-trigger fields (nausea/vomiting/diarrhea/constipation). `lastBM` drives the `ConstipationAutoAssessCard` logic. `gastrointestinal.bowelStatus` is read by the LCD eligibility evidence code — renaming the path would silently break continence-dependency detection.
- **Migration Complexity:** **Medium** — Custom `ConstipationAutoAssessCard` component (needs separate handling), four SFV triggers, LCD evidence path references, and the fact that `gastrointestinal.appetite` double-maps to `nutrition.appetite` in the RN ICA required field resolver.

---

### ### 6 — Nutrition

- **Current Section:** `Nutrition` — sidebar label "Nutrition" (`SIDEBAR_CONFIG`, `RNICA.jsx:214`)
- **Component Name:** No named React component for the section. Rendered via `renderGenericSection()` (`RNICA.jsx:5669`). The first card uses `customRenderer: "weightLossAutoCalc"` which dispatches to `WeightLossAutoCalcCard` — a named helper component (`RNICA.jsx:2165–2285`) — via dispatch in `renderGenericSection` (`RNICA.jsx`). All other cards use generic field rendering.
- **Database Tables:** `rnica_assessments.form_data.nutrition` (JSONB key). Shape: `weightLossPastSixMonths`, `appetite`, `dietType`, `fluidIntake`, `swallowingIssues[]`, `oralMucosa`, `dentures` (upper/lower/condition), `nutritionalSupplements`, `notes` (`RNICA.jsx:499–506`). No separate table.
- **API Endpoints:** Same six shared RNICA endpoints.
- **Validation Rules:**
  - **Backend RN ICA required:** `"Weight"` path `vitals.weight` or `nutrition.weight` or `weight` (`clinical_note_validation_engine.py:468–476`); `"Appetite / Intake"` path `nutrition.appetite` or `gastrointestinal.appetite` (`clinical_note_validation_engine.py:477–485`). Both are tracked in `RN_ICA_REQUIRED_FIELD_GROUPS` and generate blockers if absent.
  - No frontend hard errors in `validateRNICA` for nutrition fields.
  - Backend ROS: nutrition/GI is handled under `gastrointestinal` ROS section (see above); no separate `nutrition` ROS section exists in `REQUIRED_FULL_ROS_SECTIONS`.
- **Audit Events:** None found.
- **HOPE Dependencies:** None. `hope: []` (`RNICA.jsx:214`).
- **Narrative Dependencies:** The `evidence_harvester.py` includes `"nutrition"` as a recognized form-data section (`evidence_harvester.py:790`). It harvests `weight_loss_lbs`, `weight_loss_percent_6_months`, `oral_intake_decline`, `dysphagia`, `progressive_malnutrition`, `muscle_wasting` (`evidence_harvester.py:56–61, 89–90`). These feed into NDS eligibility criteria (e.g., failure-to-thrive, general debility diagnoses). The eligibility snapshot service surfaces `nutrition.oral_intake_decline`, `nutrition.weight_loss_lbs`, `nutrition.dysphagia` (`eligibility_snapshot_service.py:64–76`). **However, no code auto-generates text in `diagnoses.lcdEligibilityNarrative` from nutrition data.** CMS LCD expectation (nutritional decline as prognosis evidence) is tracked in evidence facts but the narrative field remains manually authored.
- **POC Dependencies:** `appetite_decline` is a POC rule keyword (`poc_compiler_rn_mapper.py:183–203`). Many nutrition-related text terms map to it. Text-match–based. `WeightLossAutoCalcCard` computes a weight-loss percentage but this is local UI logic; it writes `nutrition.weightLossPastSixMonths` back to form state.
- **Order Dependencies:** None found. No code auto-generates nutritional supplement or dietitian orders from nutrition section data. The `referrals.dietitian` section exists separately. The governance doc expectation of Supplies orders from Nutrition: **not implemented in codebase.**
- **Task Dependencies:** None found directly tied to nutrition section.
- **Current Screens:** Route position 12 (ROUTES index 11), key `"nutrition"`, `formSection: "nutrition"` (`RNICA.jsx:178`).
- **Target Facesheet Section:** Section 5 — Head-To-Toe Clinical Assessment
- **Migration Risk:** **Medium** — Weight and appetite fields are in `RN_ICA_REQUIRED_FIELD_GROUPS` and generate compliance blockers. The evidence harvester reads from multiple nutrition-related keys; path changes risk silently breaking eligibility calculations.
- **Migration Complexity:** **Medium** — `WeightLossAutoCalcCard` custom component (loads prior weight from history API), backend evidence harvester path dependencies for weight/appetite/dysphagia, dual-path resolution for `nutrition.appetite` vs `gastrointestinal.appetite` in the required-field resolver.

---

### ### 7 — Endocrine

- **Current Section:** `Endocrine` — sidebar label "Endocrine" (`SIDEBAR_CONFIG`, `RNICA.jsx:215`)
- **Component Name:** No named React component. Rendered via `renderGenericSection()` (`RNICA.jsx:5669`) consuming `SECTION_CONFIGS.endocrine` (`RNICA.jsx:4819–4840`). Three cards: Thyroid Assessment, Diabetes Management, Endocrine Symptoms.
- **Database Tables:** `rnica_assessments.form_data.endocrine` (JSONB key). Shape: `thyroid` (assessment/notes), `diabetes` (type/glucoseMonitoring/lastHbA1c/lastHbA1cDate/insulinType/insulinDose/oralHypoglycemics[]), `endocrineSymptoms[]`, `symptomSeverity{}`, `currentEndocrineMeds[]`, `notes` (`RNICA.jsx:509–521`). No separate table.
- **API Endpoints:** Same six shared RNICA endpoints.
- **Validation Rules:**
  - **Backend ROS completeness:** `endocrine` in `REQUIRED_FULL_ROS_SECTIONS` (`clinical_note_validation_engine.py:74`). Minimum fields: `diabetes`, `blood_sugar`, `hypoglycemia`, `hyperglycemia`, `polyuria`, `polydipsia`, `thyroid_condition`, `endocrine_narrative`, or `narrative` (`clinical_note_validation_engine.py:271–283`).
  - No frontend required-field errors/warnings in `validateRNICA`.
  - No fields from endocrine in `RN_ICA_REQUIRED_FIELD_GROUPS`.
- **Audit Events:** None found.
- **HOPE Dependencies:** None. `hope: []` (`RNICA.jsx:215`).
- **Narrative Dependencies:** `endocrine` section is NOT in the `evidence_harvester.py` recognized sections list (`evidence_harvester.py:788–796`). No wiring to `diagnoses.lcdEligibilityNarrative`. Diabetes-related data (`hopeComorbidities.diabetesMellitus`) is captured in the diagnoses section separately for HOPE I0010. **No cross-section linkage from endocrine data to narrative found.**
- **POC Dependencies:** No endocrine-specific POC rule keywords in `poc_compiler_rn_mapper.py`. Free-text in `endocrine.notes` could theoretically match generic keywords.
- **Order Dependencies:** None found.
- **Task Dependencies:** None found.
- **Current Screens:** Route position 13 (ROUTES index 12), key `"endocrine"`, `formSection: "endocrine"` (`RNICA.jsx:179`).
- **Target Facesheet Section:** Section 5 — Head-To-Toe Clinical Assessment
- **Migration Risk:** **Low** — No HOPE items, no required-field validation gates, no evidence harvester dependencies, no external sync side-effects.
- **Migration Complexity:** **Low** — Three standard data-collection cards, no custom renderers, no downstream write paths.

---

### ### 8 — GU (Genitourinary)

- **Current Section:** `Genitourinary` — sidebar label "Genitourinary" (`SIDEBAR_CONFIG`, `RNICA.jsx:216`)
- **Component Name:** No named React component. Rendered via `renderGenericSection()` (`RNICA.jsx:5669`) consuming `SECTION_CONFIGS.genitourinary` (`RNICA.jsx:4842–4872`). Five cards: Urinary Status, Catheter Assessment, Urine Output, Reproductive Concerns, Bladder Management.
- **Database Tables:** `rnica_assessments.form_data.genitourinary` (JSONB key). Shape: `urinaryStatus`, `frequency`, `catheter` (present/type/size/insertionDate/lastChangeDate/condition/urineCharacteristics[]), `urineOutput`, `twentyFourHourVolume`, `reproductive` (concerns[]/notes), `bladderManagement[]`, `notes` (`RNICA.jsx:524–535`). No separate table.
- **API Endpoints:** Same six shared RNICA endpoints.
- **Validation Rules:**
  - **Backend ROS completeness:** `genitourinary` in `REQUIRED_FULL_ROS_SECTIONS` (`clinical_note_validation_engine.py:73`) and `REQUIRED_FOCUSED_ROS_SECTIONS` (`clinical_note_validation_engine.py:86`). Minimum fields: `continence`, `incontinence`, `foley`, `catheter`, `urinary_frequency`, `urinary_retention`, `dysuria`, `hematuria`, `gu_narrative`, or `narrative` (`clinical_note_validation_engine.py:256–270`).
  - No frontend required-field errors/warnings in `validateRNICA`.
  - `genitourinary.urinaryStatus` and `genitourinary.catheter.present` are read by LCD eligibility evidence code for continence/ADL dependency detection (`RNICA.jsx:1342, 1370`).
- **Audit Events:** None found.
- **HOPE Dependencies:** None. `hope: []` (`RNICA.jsx:216`).
- **Narrative Dependencies:** `genitourinary.urinaryStatus` and `genitourinary.catheter.present` feed the LCD eligibility helper (`RNICA.jsx:1342–1371`) for detecting incontinence-or-catheter-ostomy dependency. These facts contribute to general functional-status evidence but NOT to `diagnoses.lcdEligibilityNarrative` auto-population.
- **POC Dependencies:** No GU-specific POC keywords in `poc_compiler_rn_mapper.py`. Incontinence-related text could match generic keywords.
- **Order Dependencies:** None found. Catheter data is captured but no catheter-care order is auto-generated.
- **Task Dependencies:** None found.
- **Current Screens:** Route position 14 (ROUTES index 13), key `"genitourinary"`, `formSection: "genitourinary"` (`RNICA.jsx:180`).
- **Target Facesheet Section:** Section 5 — Head-To-Toe Clinical Assessment
- **Migration Risk:** **Low** — No HOPE items, no required-field validation, no sync side-effects. Catheter and continence paths referenced in LCD evidence code — path changes could silently break incontinence-dependency detection.
- **Migration Complexity:** **Low** — Standard data collection; the LCD evidence helper reads `urinaryStatus` and `catheter.present` directly (`RNICA.jsx:1342–1371`) — these two field paths must be preserved or the reference updated.

---

### ### 9 — Musculoskeletal

- **Current Section:** `Musculoskeletal` — sidebar label "Musculoskeletal" (`SIDEBAR_CONFIG`, `RNICA.jsx:217`)
- **Component Name:** No named React component. Rendered via `renderGenericSection()` (`RNICA.jsx:5669`) consuming `SECTION_CONFIGS.musculoskeletal` (`RNICA.jsx:4874–4905`). Four cards: Musculoskeletal Assessment, Mobility Assessment, ADL Assessment, Fall History & Notes.
- **Database Tables:** `rnica_assessments.form_data.musculoskeletal` (JSONB key). Shape: `weakness`, `rigidity`, `contractures`, `contracturesLocation[]`, `romLimitations[]`, `gait`, `assistiveDevices[]`, `fallHistory` (fallsLast90Days/fallInjuries), `mobility` (ambulatoryStatus/endurance/transferAbility), `adl` (bathing/dressing/toileting/transferring/eating/grooming), `notes` (`RNICA.jsx:538–555`). No separate table.
- **API Endpoints:** Same six shared RNICA endpoints.
- **Validation Rules:**
  - **Frontend:** No hard errors in `validateRNICA`. `musculoskeletal.adl.*` fields are directly referenced in the LCD eligibility helper (`RNICA.jsx:1329–1349`) for ADL dependency scoring.
  - **Backend ROS completeness:** `musculoskeletal` in `REQUIRED_FULL_ROS_SECTIONS` (`clinical_note_validation_engine.py:76`). Minimum fields: `mobility`, `ambulation`, `transfer_status`, `strength`, `rom`, `contractures`, `fall_history`, `assistive_device`, `bedbound`, `musculoskeletal_narrative`, or `narrative` (`clinical_note_validation_engine.py:285–300`).
  - **Backend RN ICA required:** `"Mobility Decline"` path `functionalStatus.mobilityDecline` or `functional_status.mobility_decline` or `mobility_decline` in `RN_ICA_REQUIRED_FIELD_GROUPS` (`clinical_note_validation_engine.py:495–503`).
  - **Backend evidence harvester:** `musculoskeletal.fallHistory.fallsLast90Days` (or alias `fallsLast90Days`) is harvested to produce `fall_risk` fact (`evidence_harvester.py:447–465`).
  - **Backend functional assessment:** `musculoskeletal.mobility.ambulatoryStatus` and `adl.*` values are used in the LCD ADL dependency detection at `RNICA.jsx:1329–1349`; `musculoskeletal.adl.dressing` and `adl.bathing` specifically drive `dressingScore` and `bathingScore` (`RNICA.jsx:1348–1349`).
- **Audit Events:** None found.
- **HOPE Dependencies:** None. `hope: []` (`RNICA.jsx:217`).
- **Narrative Dependencies:** `musculoskeletal.adl.*` (bathing, dressing, toileting, transferring, eating, grooming) are read by the LCD eligibility helper (`RNICA.jsx:1329–1349`) to compute ADL dependency counts and scores for NDS eligibility. `musculoskeletal.fallHistory.fallsLast90Days` feeds the `fall_risk` Boolean fact into the eligibility evidence harvester (`evidence_harvester.py:447–465`) and then the eligibility snapshot (`eligibility_snapshot_service.py:78–82`). **No auto-population of `diagnoses.lcdEligibilityNarrative`.** The POC compiler maps `fall_risk` and `caregiver_support` keywords from musculoskeletal-related text (`poc_compiler_rn_mapper.py:69`).
- **POC Dependencies:** `fall_risk` is a POC rule keyword. Assistive device names (`walker`, `wheelchair`, etc.) map to `fall_risk` in `poc_compiler_rn_mapper.py` (`RNICA.jsx:162–174`). ADL-related text maps to `general_decline` and `caregiver_support` keywords. The `poc_compiler_rn_mapper.py` reads form text for keyword matches; no direct `musculoskeletal.*` field extraction into POC nodes confirmed.
- **Order Dependencies:** None found. DME items (walker, wheelchair, hospital bed) are captured as `assistiveDevices` but no DME order is auto-generated from this field.
- **Task Dependencies:** None found directly. Fall history data flows to eligibility evidence but does not generate a task on its own.
- **Current Screens:** Route position 15 (ROUTES index 14), key `"musculoskeletal"`, `formSection: "musculoskeletal"` (`RNICA.jsx:181`).
- **Target Facesheet Section:** Section 5 — Head-To-Toe Clinical Assessment
- **Migration Risk:** **Medium** — ADL scores directly drive the LCD eligibility helper; `fallsLast90Days` drives the `fall_risk` evidence fact. Path changes will break these downstream calculations silently.
- **Migration Complexity:** **Medium** — Six ADL select-fields with scoring semantics, fall history sub-object with evidence harvester dependency, mobility sub-object, multiple POC keyword mappings. No custom renderers, but substantial cross-section read paths.

---

### ### 10 — Skin/Wounds

- **Current Section:** `Skin / Wounds` — sidebar label "Skin / Wounds" (`SIDEBAR_CONFIG`, `RNICA.jsx:218`); HOPE `M1190`.
- **Component Name:** No named React component for the section overall. Rendered via `renderGenericSection()` (`RNICA.jsx:5669`) consuming `SECTION_CONFIGS.skin` (`RNICA.jsx:4907–4930`). Three cards: Skin Assessment (hopeCode: M1190), Braden Scale, Wound Documentation & Notes. The `skin` section also references a `BodyMap` component (`RNICA.jsx:3416`) and `WoundMarker` (`RNICA.jsx:3395`) but these appear to be defined for use in the Pain section (`skinBodySites` in the pain form data shape); wound body-site mapping for the skin section uses `skinBodySites: []` in `INITIAL_FORM.skin` (`RNICA.jsx:562`) — however the `SECTION_CONFIGS.skin` cards do not include a body-map field; wound body sites are in `form_data.skin.skinBodySites` and `form_data.skin.wounds[]` but no `customRenderer: "bodyMap"` dispatch is present in the skin section config. Wound documentation is via free-text `woundImpairment` textarea only.
- **Database Tables:** `rnica_assessments.form_data.skin` (JSONB key). Shape: `skinConditionsPresent`, `skinStatus[]`, `skinTurgor`, `skinBodySites[]`, `braden` (sensoryPerception/moisture/activity/mobility/nutrition/frictionShear/total), `pressureInjuryRisk`, `wounds[]`, `woundImpairment`, `notes` (`RNICA.jsx:558–570`). No separate table. The `wounds[]` array and `skinBodySites[]` are stored in the JSONB column.
- **API Endpoints:** Same six shared RNICA endpoints.
- **Validation Rules:**
  - **Frontend (`validateRNICA`):** `skin.braden.total` missing → **warning** `"Braden Scale total required"` (`RNICA.jsx:866–868`). This is a warning (not a blocking error). No other skin-specific validation in `validateRNICA`.
  - **Backend ROS completeness:** `integumentary` (mapped from `skin` via alias) in `REQUIRED_FULL_ROS_SECTIONS` (`clinical_note_validation_engine.py:75`). Minimum fields: `skin_integrity`, `skin_color`, `skin_temperature`, `skin_turgor`, `pressure_injury`, `wound`, `wound_assessment`, `skin_tear`, `bruising`, `edema`, `comprehensive_skin_assessment`, `skin_narrative`, or `narrative` (`clinical_note_validation_engine.py:301–318`).
  - **Backend incident detection:** `skin_tear` and `bruising` in the observed data trigger incident reports (`clinical_note_validation_engine.py:1519–1547`). These are ClinicalNote-path checks, not RNICA endpoint checks.
  - **Backend symptom intervention check:** `_validate_symptom_interventions` warns `"skin_tear_documented_without_skin_intervention"` (`clinical_note_validation_engine.py:1456–1457`).
- **Audit Events:** None found in RNICA-specific endpoints.
- **HOPE Dependencies:** `M1190` — declared in `SIDEBAR_CONFIG` (`RNICA.jsx:218`). The M1190 hopeCode tag is displayed on the "Skin Assessment" card header (`RNICA.jsx:4911`). M1190 is the HOPE pressure ulcer/wound status item. The Braden Scale total and wound documentation are the key M1190 data fields. The frontend validation warning for `braden.total` is the only HOPE-related enforcement currently present.
- **Narrative Dependencies:** The `evidence_harvester.py` includes `"skin"` in recognized form-data sections (`evidence_harvester.py:796`). `stage_3_or_4_decubitus_12_months` is a tracked evidence fact (`evidence_harvester.py:110`) relevant to debility/failure-to-thrive LCD criteria. The `poc_compiler_rn_mapper.py` includes `wound_skin_integrity` as a POC rule keyword and maps `"wound"`, `"pressure_injury"`, `"skin_breakdown"`, `"decubitus"` etc. to it (`poc_compiler_rn_mapper.py:294–300`). The `dynamic_condition_detection_engine.py` harvests `has_wounds` from structured wound flags and text keywords (`dynamic_condition_detection_engine.py:14, 50–107`). **No auto-population of `diagnoses.lcdEligibilityNarrative` from skin data.** CMS LCD expectation (pressure ulcers as prognosis evidence) is tracked in evidence but not wired to the narrative field.
- **POC Dependencies:** `wound_skin_integrity` is a POC rule keyword actively used in `poc_compiler_rn_mapper.py` (`RNICA.jsx:71`). `dynamic_condition_detection_engine.py` sets `has_wounds` from skin wound data, which can influence care model decisions. These are text-match and flag-based; no direct `skin.wounds[]` array extraction to POC nodes confirmed.
- **Order Dependencies:** No code found that auto-generates wound-care orders from `skin.wounds[]` or `skin.woundImpairment`. The governance doc expectation of Wound-care Orders from Skin/Wounds section: **not implemented in current codebase.** The ordersHub section allows manual entry of treatment orders, but no automated linkage from skin findings exists.
- **Task Dependencies:** None found directly. `has_wounds` flag from `dynamic_condition_detection_engine` may influence care model, but no task is generated from RNICA skin section data directly.
- **Current Screens:** Route position 16 (ROUTES index 15), key `"skin"`, `formSection: "skin"` (`RNICA.jsx:182`).
- **Target Facesheet Section:** Section 5 — Head-To-Toe Clinical Assessment
- **Migration Risk:** **High** — HOPE M1190 coverage requires Braden Scale and wound status fields to survive intact; the frontend Braden warning and HOPE tag must be preserved. The `skin` evidence harvester dependency and `dynamic_condition_detection_engine` `has_wounds` flag mean that structural changes can silently break downstream eligibility and care-model signals.
- **Migration Complexity:** **High** — Braden Scale six-sub-field scoring widget, `wounds[]` array (structured wound documentation), `skinBodySites[]` array (body-map integration data, though not currently rendered via a body-map card), HOPE M1190 tag, incident detection cross-reference in the validation engine, `dynamic_condition_detection_engine` wound flag, POC keyword linkage.

---

### ### 11 — Safety

*(Sub-items: fall risk, disaster readiness, emergency preparedness, home safety, transfer safety, caregiver safety — inventoried below)*

- **Current Section:** `Safety` — sidebar label "Safety" (`SIDEBAR_CONFIG`, `RNICA.jsx:221`)
- **Component Name:** No named React component. Rendered via `renderGenericSection()` (`RNICA.jsx:5669`) consuming `SECTION_CONFIGS.safety` (`RNICA.jsx:4981–5007`). Two cards: "Safety Assessment" and "Disaster Triage."
- **Database Tables:** `rnica_assessments.form_data.safety` (JSONB key). Shape: `safetyAssessmentCompleted`, `homeEnvironment[]`, `fallRiskAssessmentCompleted`, `fallRiskLevel`, `firearmInHome`, `oxygenInUse`, `oxygenSafetyReviewed`, `disasterLevel`, `disasterLevelOneConditions[]`, `disasterLevelTwoConditions[]`, `notes` (`RNICA.jsx:597–608`). No separate table.

  **Sub-item coverage within the `safety` form data shape:**
  - **Fall risk:** `fallRiskAssessmentCompleted` (bool), `fallRiskLevel` (Low/Moderate/High radio) — rendered in "Safety Assessment" card (`RNICA.jsx:4992–4993`). Fall history data (number of falls, injuries) is in `musculoskeletal.fallHistory` — that section feeds fall_risk evidence facts (`evidence_harvester.py:447–465`); the safety section captures current risk level only.
  - **Disaster readiness / Emergency preparedness:** `disasterLevel` (Level 1 Priority / Level 2 Urgent / Level 3 Non-urgent), `disasterLevelOneConditions[]` (ventilator dependent, IV meds, oxygen dependent, suction dependent, tube feeding, wound vac, no caregiver), `disasterLevelTwoConditions[]` (not in SECTION_CONFIG schema but in INITIAL_FORM, `RNICA.jsx:605–607`) — rendered in "Disaster Triage" card (`RNICA.jsx:4998–5005`).
  - **Home safety:** `homeEnvironment[]` checkbox group (adequate lighting, handrails, throw rugs, clutter/obstacles, stairs without railing, pets, weapons/firearms, pest infestation, inadequate heating/cooling, smoke detectors) (`RNICA.jsx:4987–4991`).
  - **Oxygen/fire safety:** `oxygenInUse` (bool) and `oxygenSafetyReviewed` (bool) (`RNICA.jsx:4995–4996`). Cross-references `respiratory.oxygenTherapy.inUse` conceptually but no code synchronizes the two fields — they must be entered independently.
  - **Transfer safety / Caregiver safety:** NOT explicitly present as named fields in `INITIAL_FORM.safety` or `SECTION_CONFIGS.safety`. Transfer safety (transfer ability, hoyer lift) is captured in `musculoskeletal.mobility.transferAbility`. Caregiver safety assessment (caregiver health, willingness, capability) is in `demographics.pcg.caregiverEvaluation`. The safety section does not have dedicated transfer-safety or caregiver-safety sub-fields. This is a **gap** — these topics exist in sibling sections but not in the Safety section itself.
  - **Firearm:** `firearmInHome` bool (`RNICA.jsx:4994`).

- **API Endpoints:** Same six shared RNICA endpoints. No safety-specific endpoint. `safety` data is additionally harvested by `eligibility_snapshot_service.py` which reads `fall_risk` fact (derived from musculoskeletal and safety fields) into the snapshot (`eligibility_snapshot_service.py:78–82`).
- **Validation Rules:**
  - No frontend required-field errors or warnings in `validateRNICA` for safety fields.
  - No safety-specific rules in `RN_ICA_REQUIRED_FIELD_GROUPS`.
  - No safety section in backend `REQUIRED_FULL_ROS_SECTIONS` or `REQUIRED_FOCUSED_ROS_SECTIONS`.
  - `safety.fallRiskLevel` is not checked by the backend validation engine; fall risk is instead derived from `musculoskeletal.fallHistory.fallsLast90Days` by the evidence harvester.
- **Audit Events:** None found.
- **HOPE Dependencies:** None. `hope: []` (`RNICA.jsx:221`).
- **Narrative Dependencies:** `eligibility_snapshot_service.py` surfaces `safety.fall_risk` in the snapshot object (`eligibility_snapshot_service.py:78–82`). This is a derived Boolean from the evidence harvester (reading from musculoskeletal fallHistory, not directly from `safety.fallRiskLevel`). The safety section's own `fallRiskLevel` field is NOT currently used by the evidence harvester — only `musculoskeletal.fallHistory.fallsLast90Days`. **No wiring of safety section data to `diagnoses.lcdEligibilityNarrative`.**
- **POC Dependencies:** `fall_risk` is a POC rule keyword in `poc_compiler_rn_mapper.py`. Home-safety hazard text can map to `fall_risk` and `caregiver_support` keywords via text-match. The disaster level conditions (ventilator dependent, oxygen dependent, no caregiver) are structured checkboxes but are not extracted by the POC compiler — text-match only if they appear as free-text notes.
- **Order Dependencies:** `oxygenInUse` in the safety section is captured but not wired to any oxygen order generation. No code auto-generates DME or safety equipment orders from safety section data.
- **Task Dependencies:** None found. Disaster Level 1 conditions include "No caregiver" but this does not auto-generate a task. `firearmInHome` is captured but no task or escalation is triggered from it in the current codebase.
- **Current Screens:** Route position 19 (ROUTES index 18), key `"safety"`, `formSection: "safety"` (`RNICA.jsx:185`).
- **Target Facesheet Section:** Section 9 — Safety & Environment
- **Migration Risk:** **Medium** — The safety section's `fallRiskLevel` field is structurally disconnected from the evidence harvester's `fall_risk` derivation (which reads from musculoskeletal fallHistory). Migrating to a Facesheet-style Safety section needs to reconcile this split: fall risk is currently split across two sections. `oxygenInUse` duplicates data from `respiratory.oxygenTherapy.inUse` with no sync. Transfer safety and caregiver safety are in sibling sections, not here — migration should consolidate or clarify ownership.
- **Migration Complexity:** **Low** — The section itself contains simple checkbox and radio fields. The complexity arises from the cross-section data model issue (fall risk data split between musculoskeletal and safety, oxygen-in-use duplicated) rather than from the section's own rendering logic. No custom renderers, no HOPE items, no external sync side-effects from the safety section itself.

---

## Global Notes Applicable to All 11 Sections

1. **Single-table JSONB architecture:** All 11 sections store data exclusively in `rnica_assessments.form_data` as named JSONB keys. There are no separate tables for any of these sections (except `infection.allergies` which has a write-through to `patient_allergies` via `_sync_shared_records_from_rnica`). `rnica_assessment.py:11–34`.

2. **Shared API endpoints:** All 11 sections are served by the same 6 RNICA endpoints. There are no section-granular endpoints. `visits.py:751–1027`.

3. **No audit logging on RNICA endpoints:** `save_rnica_assessment`, `update_rnica_assessment`, `lock_rnica_assessment`, and `get_rnica_intelligence` contain no `log_event` / `_safe_log_event` calls. `visits.py:751–1027` reviewed. The `_safe_log_event` calls in `visits.py` are exclusively in the older clinical note workflow.

4. **Rendering pattern:** Every section (except demographics) is rendered by a single `renderGenericSection()` function via data-driven `SECTION_CONFIGS` — there are no per-section named React components. `RNICA.jsx:5628–5675`.

5. **POC generation linkage (all sections):** POC compiler integration (`poc_compiler_rn_mapper.py`) is text-analysis–based, not field-extraction–based. No section has a confirmed direct field → POC node path. POC generation from RNICA data is a text-keyword-matching layer, not a structured mapping.

6. **LCD narrative gap (Respiratory, Skin, Nutrition):** The CMS LCD guidance expectation that dyspnea, pressure ulcers, and nutritional decline should appear in the LCD Eligibility Narrative IS partially addressed by the evidence harvester (which reads respiratory, skin, and nutrition form data for NDS eligibility detection). However, **none of these sections auto-populate the `diagnoses.lcdEligibilityNarrative` free-text field.** That field remains manually authored. The linkage is at the eligibility signal/detection level only, not at the narrative generation level.

7. **Order generation gap (Respiratory, Skin, Nutrition, Safety):** The governance expectation that Respiratory → Oxygen/DME orders, Skin/Wounds → Wound-care orders, Nutrition → Supplies orders, and Safety → DME orders are auto-generated is **not implemented in the current codebase.** The ordersHub section accepts manual entry; no automated order-trigger from these sections exists.

---

# RNICA Technical Inventory — Sections 1–14 (Whole-Person/Caregiver, Action Center, Narrative, Care Planning)

> **Scope:** Items 1–14 as assigned. All claims cited to exact file paths and line numbers. All "None found" or "Not yet implemented" declarations are verified against actual code; no claims are invented.
>
> **Key architectural facts established during research:**
> - `RnicaAssessment` (`backend/app/models/rnica_assessment.py:11`) has a single `form_data JSONB` column. All RNICA section data lives inside this column unless otherwise noted below.
> - Four RNICA-specific API endpoints exist in `backend/app/api/visits.py:751–1027`: `POST /visits/rnica/save`, `GET /visits/rnica/{id}`, `GET /visits/rnica/by-patient/{id}`, `PUT /visits/rnica/{id}`, `POST /visits/rnica/{id}/lock`, `GET /visits/rnica/{id}/intelligence`.
> - Authoritative POC tables (`plan_of_care`, `plan_of_care_versions`, `poc_problems`, `poc_goals`, `poc_interventions`) **do exist** as real separate tables — see `backend/app/models/plan_of_care.py`, `plan_of_care_version.py`, `poc.py`. However, the RNICA save/update endpoints make **no calls into those tables** — they only store POC draft entries as JSON inside `form_data.finalization.pocEntries`.
> - The `OrdersHubCard` component (`RNICA.jsx:2794`) calls completely independent physician-order APIs (`/physician-orders/*`) that operate outside the RNICA data lifecycle. These APIs have their own audit logging.
> - `clinical_note_validation_engine.py` operates on `ClinicalNote` model objects (regular visit notes), **not** directly on RNICA `form_data`.

---

### 1. Psychosocial

- **Current Section:** "Psychosocial" (`SIDEBAR_CONFIG` key `psychosocial`, `RNICA.jsx:223`)
- **Component Name:** Inline schema-driven JSX rendered by the generic `SECTION_CONFIG` renderer. Section config defined at `RNICA.jsx:5009–5047`. No named sub-component function; rendered via the shared card-loop renderer around `RNICA.jsx:4160`. `SIDEBAR_CONFIG` notes `parent: "assessment"` and `scrollTarget: "psychosocial"`.
- **Database Tables:** JSON key `psychosocial` inside `rnica_assessments.form_data` (table `rnica_assessments`, model `RnicaAssessment`, `backend/app/models/rnica_assessment.py:26`). **No separate authoritative table exists.** The data is never synced to any other table on save.
- **API Endpoints:**
  - `POST /visits/rnica/save` — creates new assessment with all form_data including psychosocial (`visits.py:751`)
  - `PUT /visits/rnica/{assessment_id}` — updates entire form_data blob (`visits.py:930`)
  - `GET /visits/rnica/{assessment_id}` — retrieves (`visits.py:860`)
  - `GET /visits/rnica/by-patient/{patient_id}` — retrieves by patient (`visits.py:892`)
  - `POST /visits/rnica/{assessment_id}/lock` — locks (`visits.py:978`)
- **Validation Rules:**
  - Frontend `validateRNICA()` (`RNICA.jsx:765–886`): **no explicit rules** for `psychosocial.*` fields. No required-field errors or warnings target this section.
  - `clinical_note_validation_engine.py:319–333`: Defines `ROS_COMPLETENESS_RULES["psychosocial"]` requiring at least one of `support_system`, `primary_caregiver`, `caregiver_availability`, `patient_coping`, `family_coping`, `caregiver_stress`, `psychosocial_concerns`, `msw_need`, `narrative` — **but this rule runs only against `ClinicalNote` objects (visit notes), not RNICA form_data directly.**
  - No backend validation specifically for RNICA psychosocial fields found.
- **Audit Events:** None found directly for RNICA save/update. The RNICA endpoints (`visits.py:751–1027`) do not call `log_event` or `_safe_log_event`. (The `_safe_log_event` pattern is used only in visit finalization endpoints elsewhere in `visits.py:2028–2057`.)
- **HOPE Dependencies:** `hope: []` — `SIDEBAR_CONFIG` line 223. No HOPE Item IDs assigned to this section.
- **Narrative Dependencies:** Does not directly feed `diagnoses.lcdEligibilityNarrative`. However, clinical content (e.g., distress rating, coping assessment, intervention plan) would logically inform a manually authored narrative. No automated pipeline exists.
- **POC Dependencies:** The Psychosocial section's data (coping concerns, intervention plan) is conceptually expected to feed POC problem generation. In practice today, the RN manually copies concerns into `finalization.pocEntries` free-text fields. No automated extraction from `psychosocial.*` to POC exists.
- **Order Dependencies:** None. Psychosocial data does not gate or trigger any order.
- **Task Dependencies:** None found for RNICA psychosocial section specifically. (MSW ICA has suicide-risk task creation, but that is a separate form.)
- **Current Screens:** RNICA Step 20 (`ROUTES` array index 19, `RNICA.jsx:186`: `{ key: "psychosocial", nav: "Psychosocial", formSection: "psychosocial" }`).
- **Target Facesheet Section:** Section 8 — Whole-Person & Caregiver Assessment
- **Migration Risk:** Low — self-contained JSON section, no cross-cutting dependencies.
- **Migration Complexity:** Low — no foreign-key entanglements; pure form data move from a sequential step to a persistent panel.

---

### 2. Spiritual

- **Current Section:** "Spiritual" (`SIDEBAR_CONFIG` key `spiritual`, `RNICA.jsx:224`)
- **Component Name:** Inline schema-driven JSX. Section config at `RNICA.jsx:5049–5069`. No named sub-component. `SIDEBAR_CONFIG` notes `parent: "assessment"` and `scrollTarget: "spiritual"`.
- **Database Tables:** JSON key `spiritual` inside `rnica_assessments.form_data`. **No separate authoritative table.** Not synced to any other table on save.
- **API Endpoints:** Same five RNICA endpoints as Section 1 (save/get/get-by-patient/update/lock at `visits.py:751–1027`).
- **Validation Rules:**
  - Frontend `validateRNICA()`: **no explicit rules** for `spiritual.*`.
  - `clinical_note_validation_engine.py:334–346`: Defines `ROS_COMPLETENESS_RULES["spiritual"]` requiring at least one of `faith_preference`, `spiritual_concerns`, `spiritual_distress`, `chaplain_needed`, `clergy_requested`, `sc_need`, `narrative` — **applies to visit notes only, not RNICA form_data.**
  - No backend validation for RNICA spiritual fields found.
- **Audit Events:** None found (same as Section 1).
- **HOPE Dependencies:** `hope: []` — `SIDEBAR_CONFIG` line 224. None.
- **Narrative Dependencies:** Does not feed `diagnoses.lcdEligibilityNarrative` automatically.
- **POC Dependencies:** `chaplainNeeded: false` flag at `INITIAL_FORM.spiritual.chaplainNeeded` (`RNICA.jsx:633`) is intended to inform a Chaplain referral/POC entry. No automated pipeline pushes this to POC or to the `referrals` section; manual RN action required.
- **Order Dependencies:** None. No order gating.
- **Task Dependencies:** None found in RNICA context. Spiritual care suicide-risk task creation is present in SCICA (`_sync_scica_escalations`, `visits.py:634–659`), but that is a separate form.
- **Current Screens:** RNICA Step 21 (`ROUTES` array index 20, `RNICA.jsx:187`).
- **Target Facesheet Section:** Section 8 — Whole-Person & Caregiver Assessment
- **Migration Risk:** Low — self-contained, no cross-cutting dependencies.
- **Migration Complexity:** Low — same profile as Psychosocial.

---

### 3. Bereavement

- **Current Section:** "Bereavement" (`SIDEBAR_CONFIG` key `bereavement`, `RNICA.jsx:225`)
- **Component Name:** Inline schema-driven JSX. Section config at `RNICA.jsx:5071–5088`. No named sub-component.
- **Database Tables:** JSON key `bereavement` inside `rnica_assessments.form_data`. **No separate authoritative table.** However, a `BereavementAggregationEngine` (`bereavement_aggregation_engine.py`) is instantiated as a singleton at `visits.py:734`. This engine processes visit notes (not RNICA form_data directly) — it is **not** wired to RNICA bereavement section data on save.
- **API Endpoints:** Same five RNICA endpoints (`visits.py:751–1027`).
- **Validation Rules:**
  - Frontend `validateRNICA()`: **no explicit rules** for `bereavement.*`.
  - No backend validation specific to RNICA bereavement fields found.
- **Audit Events:** None found.
- **HOPE Dependencies:** `hope: []` — `SIDEBAR_CONFIG` line 225. None.
- **Narrative Dependencies:** Does not feed `diagnoses.lcdEligibilityNarrative` automatically.
- **POC Dependencies:** `bereavementVisitNeeded: false` (`RNICA.jsx:643`) is intended to trigger a bereavement visit plan. No automated pipeline to POC exists today.
- **Order Dependencies:** None.
- **Task Dependencies:** None found in the RNICA save/update flow. The `BereavementAggregationEngine` singleton at `visits.py:734` is available but is not called from RNICA save/update handlers (only from visit note finalization flow elsewhere in the file).
- **Current Screens:** RNICA Step 22 (`ROUTES` array index 21, `RNICA.jsx:188`).
- **Target Facesheet Section:** Section 8 — Whole-Person & Caregiver Assessment
- **Migration Risk:** Low — self-contained JSON. Note: if the `BereavementAggregationEngine` is ever wired to RNICA bereavement data, that becomes a new dependency.
- **Migration Complexity:** Low — no active engine calls in current RNICA flow.

---

### 4. Personal Care

- **Current Section:** "Personal Care" (`SIDEBAR_CONFIG` key `personalCare`, `RNICA.jsx:226`)
- **Component Name:** Inline schema-driven JSX. Section config at `RNICA.jsx:5090–5128`. No named sub-component.
- **Database Tables:** JSON key `personalCare` inside `rnica_assessments.form_data`. **No separate authoritative table.** `equipmentSupplyNeeds` sub-array (line 655–657) is not synced to `patient_orders` or any DME/supply table on save.
- **API Endpoints:** Same five RNICA endpoints (`visits.py:751–1027`).
- **Validation Rules:**
  - Frontend `validateRNICA()`: **no explicit rules** for `personalCare.*`.
  - No backend validation found.
- **Audit Events:** None found.
- **HOPE Dependencies:** `hope: []` — `SIDEBAR_CONFIG` line 226. None.
- **Narrative Dependencies:** Does not feed `diagnoses.lcdEligibilityNarrative`.
- **POC Dependencies:** `aideTasks` and `aideVisitPreferences` sub-objects are intended to inform HA/HHA visit frequency in the POC. No automated pipeline exists today; the RN manually enters this in `admissionsOrder.visitFrequency` and `finalization.pocEntries`.
- **Order Dependencies:** `equipmentSupplyNeeds` checklist items (e.g., "Hospital bed", "Wheelchair", `RNICA.jsx:5119–5124`) represent DME/supply needs that conceptually should become Orders Hub entries, but **no automated conversion from this checklist to `patient_orders` or `physician_orders` exists today**. This is a key gap.
- **Task Dependencies:** None found.
- **Current Screens:** RNICA Step 23 (`ROUTES` array index 22, `RNICA.jsx:189`).
- **Target Facesheet Section:** Section 8 — Whole-Person & Caregiver Assessment
- **Migration Risk:** Medium — the `equipmentSupplyNeeds` checklist creates a gap/expectation mismatch: items identified here do not automatically populate the Orders Hub, which could confuse nurses in a redesigned flow where both sections are visible simultaneously.
- **Migration Complexity:** Medium — the equipment checklist's relationship to Orders Hub DME entries needs an explicit design decision during migration.

---

### 5. Teaching Needs

- **Current Section:** "Teaching Needs" (`SIDEBAR_CONFIG` key `teachingNeeds`, `RNICA.jsx:227`)
- **Component Name:** Inline schema-driven JSX. Section config at `RNICA.jsx:5130–5157`. Relies on `DEFAULT_EDUCATION_TOPICS` constant (`RNICA.jsx:248–255`) to populate the initial `educationTopics` array.
- **Database Tables:** JSON key `teachingNeeds` inside `rnica_assessments.form_data`. **No separate authoritative table.**
- **API Endpoints:** Same five RNICA endpoints (`visits.py:751–1027`).
- **Validation Rules:**
  - Frontend `validateRNICA()`: **no explicit rules** for `teachingNeeds.*`.
  - No backend validation found.
- **Audit Events:** None found.
- **HOPE Dependencies:** `hope: []` — `SIDEBAR_CONFIG` line 227. None.
- **Narrative Dependencies:** Does not feed `diagnoses.lcdEligibilityNarrative`.
- **POC Dependencies:** Teaching needs (e.g., barriers to learning, follow-up plan) are conceptually expected to generate a teaching/education POC intervention. No automated pipeline to POC exists today.
- **Order Dependencies:** None.
- **Task Dependencies:** None found.
- **Current Screens:** RNICA Step 24 (`ROUTES` array index 23, `RNICA.jsx:190`).
- **Target Facesheet Section:** Section 8 — Whole-Person & Caregiver Assessment
- **Migration Risk:** Low — purely informational section, no cross-cutting dependencies.
- **Migration Complexity:** Low — straightforward panel move.

---

### 6. Admission Orders

- **Current Section:** "Admissions Order" (`SIDEBAR_CONFIG` key `admissionsOrder`, `RNICA.jsx:228–230`)
- **Component Name:** Inline schema-driven JSX. Section config at `RNICA.jsx:5159–5187`. `SIDEBAR_CONFIG` declares `subFields: ["levelOfCare","visitFrequency","haAssignment","initialPocIdg","nonCoveredItems"]` and `features: ["verbalOrderReadBack","locSelection","disciplineFrequency"]`. No separate named component; rendered via card-loop renderer. `visitFrequency` is pre-populated from `DEFAULT_VISIT_DISCIPLINES` constant (`RNICA.jsx:258–264`) seeded in `INITIAL_FORM.admissionsOrder.visitFrequency` (`RNICA.jsx:679`).
- **Database Tables:**
  - Primary: JSON key `admissionsOrder` inside `rnica_assessments.form_data`. **Not an authoritative separate table.**
  - On RNICA save/update, `_extract_rnica_level_of_care()` (`visits.py:284–290`) syncs `admissionsOrder.levelOfCare.level` → `patient_facesheet.current_level_of_care` (`visits.py:397–412`). This is the **only** field from `admissionsOrder` that escapes into a real table.
  - A separate `soc_orders.py` router (`POST /soc-orders/patients/{patient_id}/rn-admission`) exists for finalizing the RN admission order — it calls `authorize_admission()` and runs guardrails. This endpoint is distinct from the RNICA save flow; it must be called explicitly after the RNICA is completed.
- **API Endpoints:**
  - `POST /visits/rnica/save` — persists `admissionsOrder` as JSON (`visits.py:751`)
  - `PUT /visits/rnica/{assessment_id}` — updates (`visits.py:930`)
  - `POST /soc-orders/patients/{patient_id}/rn-admission` — finalizes admission order, runs guardrails + `authorize_admission()` (`soc_orders.py:59–156`)
- **Validation Rules:**
  - Frontend `validateRNICA()` (`RNICA.jsx:870–878`):
    - **Error:** `admissionsOrder.levelOfCare.level` — "Level of Care is required for admission"
    - **Error:** `admissionsOrder.toVerification.verbalOrderReadBack` — "Verbal order read-back verification required"
  - `soc_orders.py`: `AdmissionGuardrailAssessmentService.assess_admission()` (`soc_orders.py:86–110`) — hard-stop if guardrails fail; requires `narrative`, `has_decline`, `lcd_status` fields in the payload.
  - Backend: No inline validation of `visitFrequency` disciplines or `haAssignment`.
- **Audit Events:** `soc_orders.py` returns guardrails result but does not call `log_event` directly. The `authorize_admission()` service may log internally (not verified in scope). RNICA save/update do not call `log_event`.
- **HOPE Dependencies:** `hope: []` — `SIDEBAR_CONFIG` line 228. None.
- **Narrative Dependencies:** `soc_orders.py:30–36` declares `narrative: str | None` as a required guardrail field — this references the LCD Eligibility Narrative (item 9), meaning the Admissions Order finalization endpoint expects narrative content. It does **not** auto-copy from `diagnoses.lcdEligibilityNarrative`; the caller must pass it explicitly.
- **POC Dependencies:** `admissionsOrder.initialPocIdg` sub-object (`RNICA.jsx:682–686`) has checkbox `created` + note: *"IDG should only be created after all problems identified during this Assessment have been added to Initial POC."* This is a documentation checkbox only — it does not create a real `plan_of_care` record. `visitFrequency` discipline frequencies are stored as JSON (`RNICA.jsx:679`) and are not pushed to any `plan_of_care_versions` or discipline-frequency table.
- **Order Dependencies:** **This is the key redesign concern.** Currently `admissionsOrder` is Step 25 of 28 — it is sequentially gated behind all clinical assessment steps. The `POST /soc-orders/patients/{patient_id}/rn-admission` endpoint is independent of RNICA completion status (no check that the RNICA is locked or complete before it can be called), but the **UI** only exposes it within the RNICA sequential flow. Becoming a persistent "Admission Action Center" requires decoupling this UI gating.
- **Task Dependencies:** `authorize_admission()` service internally may create admission-related tasks (not verified in scope). No direct task creation in `soc_orders.py` endpoint body.
- **Current Screens:** RNICA Step 25 (`ROUTES` array index 24, `RNICA.jsx:191–192`, with `subFields`).
- **Target Facesheet Section:** Admission Action Center (persistent, not a numbered section)
- **Migration Risk:** **High** — Level of Care is synced to Facesheet on every RNICA save. Decoupling this into a persistent panel means the sync logic (`_sync_shared_records_from_rnica`, `visits.py:293–423`) must be preserved or replicated; the `POST /soc-orders/.../rn-admission` guardrail flow must be callable independently of RNICA step sequence; and `visitFrequency` data currently lives only in `form_data` with no separate table.
- **Migration Complexity:** **High** — sequential workflow dependency on assessment completion is currently enforced only via UI step ordering, not backend gate, but the guardrail service (`soc_orders.py:86–110`) expects narrative/decline data that only exists after the clinical assessment is done. Decoupling this means designing when/how the Action Center can be used pre-assessment, and what partial-assessment guardrail behavior should look like.

---

### 7. Hospice Orders Hub

- **Current Section:** "Hospice Orders Hub" (`SIDEBAR_CONFIG` key `ordersHub`, `RNICA.jsx:231–233`)
- **Component Name:** `OrdersHubCard` — a named exported React component (`RNICA.jsx:2794`). It is embedded inside the `medications` section card via `customRenderer: "ordersHub"` (`RNICA.jsx:5207`). The `medications` section in `ROUTES` maps to `formSection: "medications"` (`RNICA.jsx:193`).
- **Database Tables:**
  - **`physician_orders`** table (model `PhysicianOrder`, `backend/app/models/physician_order.py:56`) — DME, Supply, Lab, Treatment, Diet, Other orders all route through this table via `OrdersHubCard.handleAddOrder()` (`RNICA.jsx:2920–2976`), which calls `createPhysicianOrder` + `submitPhysicianOrder`. **This is a fully separate, authoritative table.**
  - **`patient_orders`** table (model `PatientOrder`, `backend/app/models/patient_order.py`) — generic non-medication orders; see `backend/app/api/patient_orders.py`. The `OrdersHubCard` currently calls the `/physician-orders/` endpoints only (not `/patient-orders/`), so DME/Supply/Lab/Treatment/Diet orders placed via `OrdersHubCard` go to `physician_orders`, not `patient_orders`.
  - **`order_templates`** / `order_template_items` — used by "Import Pack" (`order_templates.py:202`, `RNICA.jsx:2871`).
  - **Medications:** `INITIAL_FORM.medications` JSON key (`RNICA.jsx:693–701`) stores `scheduledOpioid`, `prnOpioid`, `bowelRegimen`, `currentMedications`, `orders`, `medReconciliation` as JSON inside `rnica_assessments.form_data`. Actual medication records created via the Medications sub-section go to a separate medications table through `listMedications`, `addMedication`, `discontinueMedication` from `api/icaAssessments` (not examined in detail here, but separate from `form_data`).
- **API Endpoints:**
  - `GET /physician-orders/patients/{patient_id}` — list orders (`physician_orders.py:187`)
  - `POST /physician-orders/patients/{patient_id}` — create DRAFT order (`physician_orders.py:238`)
  - `POST /physician-orders/{order_id}/submit` — submit (`physician_orders.py:276`)
  - `POST /physician-orders/{order_id}/clinical-review` — clinical review (`physician_orders.py:305`)
  - `POST /physician-orders/{order_id}/approve` — MD approval/signature (`physician_orders.py:339`)
  - `POST /physician-orders/{order_id}/execute` — mark implemented (`physician_orders.py:391`)
  - `POST /physician-orders/{order_id}/complete` — mark completed (`physician_orders.py:412`)
  - `POST /physician-orders/{order_id}/cancel` — cancel (`physician_orders.py:438`)
  - `GET /physician-orders/{order_id}/status-history` — audit trail (`physician_orders.py:207`)
  - `GET /order-templates` — list templates (`order_templates.py:103`)
  - `POST /order-templates/{template_id}/import` — Import Pack (`order_templates.py:202`)
  - `GET /lab-catalog` — lab test catalog (via `getLabCatalog`, `RNICA.jsx:2857`)
  - `POST /fax/patients/{patient_id}` / `GET /fax/patients/{patient_id}` — fax orders (`RNICA.jsx:3010–3023`)
  - `GET /vendors` — vendor list for DME/supply (`RNICA.jsx:2864–2868`)
- **Validation Rules:**
  - Frontend `OrdersHubCard`: `ordered_by_provider_name` required for every order (`RNICA.jsx:2940–2942`); phone read-back required for `VERBAL_PHONE` source type (`RNICA.jsx:2943–2947`); `prescriber_authenticated` required for Import Pack (`RNICA.jsx:2877–2880`).
  - Backend `physician_orders.py:339–388`: `svc.approve_order()` enforces provider-role gate (`ORDER_ALL_SIGNER_ROLES`); NP/PA restricted to STAT/URGENT orders. `log_event("PROVIDER_SIGNATURE_ACCESS_DENIED")` on failure.
  - `validateRNICA()`: No explicit rules for `ordersHub` section fields (the JSON `medications` form_data blob has no required-field validation in `validateRNICA`).
- **Audit Events:** Full audit trail per order lifecycle action via `log_event()` in `physician_orders.py`: `CREATE_PHYSICIAN_ORDER` (line 266), `SUBMIT_PHYSICIAN_ORDER` (295), `CLINICAL_REVIEW_PHYSICIAN_ORDER` (329), `APPROVE_PHYSICIAN_ORDER` (371), `PROVIDER_SIGNATURE_ACCESS_GRANTED` (381), `PROVIDER_SIGNATURE_ACCESS_DENIED` (363), `EXECUTE_PHYSICIAN_ORDER` (403), `COMPLETE_PHYSICIAN_ORDER` (428), `CANCEL_PHYSICIAN_ORDER` (453). **This is the most thoroughly audited section in the entire RNICA.**
- **HOPE Dependencies:** `hope: []` — `SIDEBAR_CONFIG` line 231. None.
- **Narrative Dependencies:** None — does not feed `diagnoses.lcdEligibilityNarrative`.
- **POC Dependencies:** Orders placed here (DME, supplies, medications) are conceptually part of the POC but are stored in `physician_orders` / `patient_orders`, not in `poc_interventions`. No programmatic link between `physician_orders` entries and `poc_interventions` exists today.
- **Order Dependencies:** **This is the key redesign concern.** The `OrdersHubCard` already operates against a fully independent `physician_orders` API with its own audit trail — it does NOT depend on RNICA form_data being saved or the RNICA being in any particular status. The only coupling is **UI presentation**: it is embedded as a section in the RNICA sequential wizard. Making it a persistent cross-cutting "Admission Action Center" element is architecturally straightforward from the backend perspective. The UI migration is the complexity.
- **Task Dependencies:** `PhysicianOrder` model docstring (`physician_order.py:44`): *"On approval a signature is captured and the linked ORDER_MD_APPROVAL task (see Task.reference_type / Task.reference_id) is auto-completed."* Task auto-completion on MD approval is implemented inside `svc.approve_order()`.
- **Current Screens:** RNICA Step 26 (`ROUTES` array index 25, `RNICA.jsx:193–194`), declared with `subViews: ["ordersList","orderEntry","medReconciliation","startedStoppedLog"]`.
- **Target Facesheet Section:** Admission Action Center (persistent, not a numbered section)
- **Migration Risk:** **High** — the Orders Hub is currently deeply embedded in the RNICA sequential flow, but technically already operates independently. The risk is nurses expect to enter orders after completing clinical assessment; a persistent panel changes when orders can be entered and may cause workflow confusion or premature ordering before clinical findings are complete.
- **Migration Complexity:** **High** — while the backend is already decoupled, the frontend `OrdersHubCard` is exported from `RNICA.jsx` and will need to be extracted into a standalone component importable by the new Facesheet-style layout. The `medications` section's JSON form_data (opioid/bowel/medReconciliation flags stored in `rnica_assessments.form_data.medications`) will also need to be reconciled against the persistent order state in `physician_orders`.

---

### 8. Referrals

- **Current Section:** "Referrals" (`SIDEBAR_CONFIG` key `referrals`, `RNICA.jsx:234`)
- **Component Name:** Inline schema-driven JSX. Section config at `RNICA.jsx:5211–5229`. No named sub-component.
- **Database Tables:** JSON key `referrals` inside `rnica_assessments.form_data`. **No separate authoritative table.** Referral data is never synced to any other table on RNICA save/update. Note: the `task.py` model and task service exist separately but are not wired to RNICA referral section data.
- **API Endpoints:** Same five RNICA endpoints (`visits.py:751–1027`). No dedicated referrals API exists outside RNICA context that is called from this section.
- **Validation Rules:**
  - Frontend `validateRNICA()`: **no explicit rules** for `referrals.*`.
  - No backend validation found.
- **Audit Events:** None found.
- **HOPE Dependencies:** `hope: []` — `SIDEBAR_CONFIG` line 234. None.
- **Narrative Dependencies:** Does not feed `diagnoses.lcdEligibilityNarrative`.
- **POC Dependencies:** Referrals to Social Work, Spiritual Care, Therapy, Dietitian, Pharmacist, and Volunteer are conceptually expected to generate corresponding POC intervention entries and/or `Task` records (e.g., MSW referral → MSW ICA task). **No automated pipeline from `referrals.*` to tasks, POC, or any other table exists today.** This is a significant gap.
- **Order Dependencies:** **This is the key redesign concern.** Like the Orders Hub, referrals are logically an action that should be possible independently of RNICA completion (e.g., urgent social work referral). Currently gated behind Step 27 of 28 in the sequential wizard. The backend has no gate — the `referrals` JSON is saved with the RNICA blob on any save call. Decoupling into a persistent panel is architecturally straightforward but requires a clear design for which table owns a referral (currently none).
- **Task Dependencies:** None found in current RNICA flow. Conceptually, a checked `socialWork.referred` should create a `Task` for the MSW team, but this automation does not exist today.
- **Current Screens:** RNICA Step 27 (`ROUTES` array index 26, `RNICA.jsx:195`).
- **Target Facesheet Section:** Admission Action Center (persistent, not a numbered section)
- **Migration Risk:** **High** — the referrals section has NO authoritative table and NO task generation today. Promoting it to a persistent Action Center panel without also building a proper `referrals` table and task-generation pipeline creates a situation where referrals placed early in the workflow are invisible to receiving disciplines.
- **Migration Complexity:** **High** — requires net-new backend work: a `referrals` table (or equivalent), API endpoints, task auto-generation on referral creation, and cross-discipline visibility. This is more greenfield work than any of the other 13 items in scope.

---

### 9. Narrative (`diagnoses.lcdEligibilityNarrative`)

- **Current Section:** Rendered as a sub-card of the "Diagnoses" section (`SIDEBAR_CONFIG` key `diagnoses`, `RNICA.jsx:207`). The card is titled "Narrative & Disease Trajectory" and lives inside `SECTION_CONFIG.diagnoses.cards` at `RNICA.jsx:5594–5598`.
- **Component Name:** Inline schema-driven JSX via generic card renderer. No separate named component exists. The field config is: `{ type: "textarea", label: "LCD Eligibility Narrative", path: "lcdEligibilityNarrative", rows: 6, placeholder: "Document the patient's terminal illness, functional decline trajectory, and LCD eligibility criteria..." }` (`RNICA.jsx:4596`). There is **no dedicated "Narrative" section** in `SIDEBAR_CONFIG` or `ROUTES` — the narrative lives within the Diagnoses step.
- **Database Tables:** JSON key `diagnoses.lcdEligibilityNarrative` (string) inside `rnica_assessments.form_data` (`RNICA.jsx:398`). Not synced to any separate table on save. **No `narrative` table or column exists** in `rnica_assessments` outside of `form_data`.
- **API Endpoints:**
  - Same five RNICA endpoints.
  - `GET /visits/rnica/{assessment_id}/intelligence` (`visits.py:1002`) — returns `build_rnica_intelligence()` output which includes clinical findings and recommendations derived from form_data fields (including `diagnoses.primaryDiagnosis`, `diseaseTrajectory`, etc.) but **does NOT generate or modify `lcdEligibilityNarrative`**. The intelligence endpoint is advisory only.
- **Validation Rules:**
  - `clinical_note_validation_engine.py:384–396` — `RN_ICA_REQUIRED_FIELD_GROUPS` includes `{ "label": "LCD Eligibility Narrative", "paths": ["diagnoses.lcdEligibilityNarrative", "lcd_eligibility_narrative", "assessment_summary", "nursing_summary"] }`. This runs against `ClinicalNote` objects (visit notes), **not directly against RNICA form_data**. However, this constant defines the compliance expectation.
  - `soc_orders.py:30–36`: The `RNAdmissionOrder` Pydantic model includes `narrative: str | None` — this is passed to `AdmissionGuardrailAssessmentService` and can trigger a hard-stop if the narrative is missing/insufficient (`soc_orders.py:98–109`). The caller is responsible for passing `diagnoses.lcdEligibilityNarrative` value here; no auto-extraction exists in `soc_orders.py`.
  - Frontend `validateRNICA()`: **no explicit validation rule for `lcdEligibilityNarrative`** in `RNICA.jsx:765–886`. It is not flagged as required or warned in the frontend validator.
- **Audit Events:** None found specifically for narrative changes (same as all RNICA section saves).
- **HOPE Dependencies:** `SIDEBAR_CONFIG` for `diagnoses`: `hope: ["I0010","J0050"]` (`RNICA.jsx:207`). These apply to the primary diagnosis and prognosis fields within the Diagnoses section, not the narrative textarea itself.
- **Narrative Dependencies:** This IS the narrative. Mechanism:
  - **Generation:** **Plain free-text textarea only** — the nurse types the narrative manually. There is **no auto-generation function** anywhere in the codebase that composes narrative text from other section data. No function named `generateNarrative`, `composeNarrative`, `autoGenerate`, or similar was found in `RNICA.jsx` or any backend service.
  - **Intelligence assist:** `GET /visits/rnica/{assessment_id}/intelligence` (`visits.py:1002`) calls `build_rnica_intelligence()` (`rnica_intelligence.py:57+`), which produces structured clinical findings and recommendations (e.g., "High pain burden — review treatment plan") that are displayed in the right-side intelligence panel. These are **suggestions for the nurse** to draw from, not automated narrative text insertion. The intelligence output is a separate `findings` + `recommendations` array, not a narrative string.
  - **Eligibility detection assist:** `detectLCD`, `evaluateLCD`, `getLCDConfig` (`RNICA.jsx:33`) are imported and used in the `lcdEligibility` custom renderer (within the Diagnoses section), which detects the terminal diagnosis and presents CMS LCD criteria to guide clinical judgment. This populates `diagnoses.ndsEligibility` but does **not** auto-populate `lcdEligibilityNarrative`.
  - **Summary:** `lcdEligibilityNarrative` is entirely nurse-authored free text with no auto-composition engine.
- **POC Dependencies:** None directly — the narrative is not an input to POC generation.
- **Order Dependencies:** `soc_orders.py` expects narrative content as an input to admission guardrails (described above). This is the only operational dependency.
- **Task Dependencies:** None.
- **Current Screens:** RNICA Step 5 (`ROUTES` array index 4: `{ key: "diagnoses", nav: "Diagnoses", formSection: "diagnoses" }`, `RNICA.jsx:171`). The narrative card is the last card within that step.
- **Target Facesheet Section:** Section 10 — Clinical Narrative & Disease Trajectory
- **Migration Risk:** Medium — `soc_orders.py` has a hard dependency on narrative being populated at finalization time; the redesign must ensure the narrative field remains accessible and its value is passed to the guardrail endpoint.
- **Migration Complexity:** Medium — extracting the narrative textarea from within the Diagnoses step into its own Section 10 panel is straightforward UI work, but requires verifying the value flows correctly to the `soc_orders` guardrail caller.

---

### 10. Problem Generation

- **Current Section:** "Plan of Care — Problem Generation (CDPH Gap #4)" — rendered as a sub-card inside the "Finalization" section (`RNICA.jsx:5243–5246`).
- **Component Name:** Inline JSX inside the Finalization section renderer. The POC issue editor is rendered conditionally via `shouldRenderPocIssueEditor` flag at `RNICA.jsx:4254–4303`. It renders a manual entry form with fields: Problem, Goal, Intervention / Frequency, Discipline.
- **Database Tables:**
  - **Current (implemented):** `finalization.pocEntries` array and `finalization.pocDraft` object stored as JSON inside `rnica_assessments.form_data.finalization` (`RNICA.jsx:728–729`). These are free-text entries only — **no foreign key** to any other table.
  - **Authoritative POC tables (exist but NOT wired to RNICA POC draft):** `poc_problems` (`backend/app/models/poc.py:37`), `poc_goals` (`poc.py:209`), `poc_interventions` (`poc.py:339`), anchored through `plan_of_care_versions` (`plan_of_care_version.py:31`) and `plan_of_care` (`plan_of_care.py:27`). These are real, normalized, FK-enforced tables. They are populated by the clinical rules engine and IDG process — **not by the RNICA save endpoint today**.
  - **Assessment of gap:** The RNICA `form_data.finalization.pocEntries` JSON array and the `poc_problems` table are **two separate, unconnected representations** of the same concept. There is no API endpoint in `visits.py` or elsewhere that pushes `finalization.pocEntries` entries into `poc_problems`.
- **API Endpoints:**
  - RNICA save/update endpoints persist `pocEntries` as part of form_data — not as actual `poc_problems` records.
  - **No dedicated "create POC problem from RNICA" endpoint exists** in the codebase.
  - The POC tables are presumably populated via the clinical rules engine (source: `plan_of_care_version.py:50` — `source_kind IN ('ICA','RN_UPDATE','IDG_UPDATE','SYSTEM')` — `ICA` suggests there is/was a planned integration path) but no such route was found in the visited API files.
- **Validation Rules:**
  - Frontend `validateRNICA()` (`RNICA.jsx:822–825`): `!formData.finalization.pocGenerationCompleted` → **warning** "CDPH: POC generation from assessment problems required before lock" — does not block save, only warns.
  - No backend validation prevents locking an RNICA without POC entries.
- **Audit Events:** None found.
- **HOPE Dependencies:** None.
- **Narrative Dependencies:** None.
- **POC Dependencies:** This IS the POC generation step. As documented above: **the current implementation is a manual, freetext-only draft stored in RNICA form_data, not connected to the authoritative `poc_problems` / `poc_goals` / `poc_interventions` tables.**
- **Order Dependencies:** None.
- **Task Dependencies:** None.
- **Current Screens:** RNICA Step 28 (`ROUTES` array index 27, `RNICA.jsx:196`, `key: "finalization"`). The POC editor is inside the Finalization card.
- **Target Facesheet Section:** Section 11 — Care Planning & Team Recommendations
- **Migration Risk:** **High** — the gap between `finalization.pocEntries` JSON and the real `poc_problems` table is a major architectural debt. Any redesign that promotes Problem Generation to a standalone Section 11 must decide whether to (a) continue using form_data as a draft and add an API to push to `poc_problems` at finalization, or (b) immediately create `poc_problems` records in real-time as the nurse adds them.
- **Migration Complexity:** **High** — requires bridging two completely separate data representations. The `PlanOfCareVersion.source_kind` value `'ICA'` suggests this integration was planned but not implemented.

---

### 11. Goals

- **Current Section:** Part of the inline POC issue editor in "Finalization" section (`RNICA.jsx:4280`). No separate "Goals" section exists in `SIDEBAR_CONFIG` or `ROUTES`.
- **Component Name:** `FormInput` for `pocDraft.goal` within the POC issue editor at `RNICA.jsx:4280`. Combined with Problem, Intervention, and Discipline in a single 4-field entry row.
- **Database Tables:**
  - **Current (implemented):** `finalization.pocDraft.goal` (draft string) and `finalization.pocEntries[].goal` (completed entry string) — all JSON inside `rnica_assessments.form_data`. **No separate table.**
  - **Authoritative table:** `poc_goals` (`backend/app/models/poc.py:209`) — real separate table with `goal_text`, `measurable_outcome`, `target_timeframe`, `status`, `source_kind` columns, anchored to `poc_problems.id`. **Not wired to RNICA form_data today.**
- **API Endpoints:** No dedicated endpoint. Goals are stored as part of `pocEntries` JSON via the RNICA save/update endpoints. `poc_goals` table has no API endpoint in the files examined.
- **Validation Rules:** None — `pocDraft.goal` is an optional free-text field; the "Add to POC" button only requires `pocDraft.problem` to be non-empty (`RNICA.jsx:4285`).
- **Audit Events:** None.
- **HOPE Dependencies:** None.
- **Narrative Dependencies:** None.
- **POC Dependencies:** This IS the Goals component. Same gap as Problem Generation: `poc_goals` table exists but is not connected to RNICA form_data.
- **Order Dependencies:** None.
- **Task Dependencies:** None.
- **Current Screens:** RNICA Step 28 (Finalization), same as Problem Generation.
- **Target Facesheet Section:** Section 11 — Care Planning & Team Recommendations
- **Migration Risk:** **High** — same as Problem Generation.
- **Migration Complexity:** **High** — `poc_goals` has richer data structure (`measurable_outcome`, `target_timeframe`) than the single freetext `goal` string in `pocDraft`. Schema alignment needed.

---

### 12. Interventions

- **Current Section:** Part of the inline POC issue editor in "Finalization" section (`RNICA.jsx:4281`). No separate "Interventions" section in `SIDEBAR_CONFIG` or `ROUTES`.
- **Component Name:** `FormInput` for `pocDraft.intervention` within the POC issue editor at `RNICA.jsx:4281`. Combined in the same 4-field row as Problem/Goal/Discipline.
- **Database Tables:**
  - **Current (implemented):** `finalization.pocDraft.intervention` (draft string) and `finalization.pocEntries[].intervention` (string) — JSON inside `rnica_assessments.form_data`. **No separate table.**
  - **Authoritative table:** `poc_interventions` (`backend/app/models/poc.py:339`) — real table with `discipline`, `intervention_text`, `frequency`, `instructions`, `status`, `source_kind` columns. **Not wired to RNICA form_data today.**
- **API Endpoints:** None dedicated. Stored via RNICA save/update as JSON blob.
- **Validation Rules:** None explicit.
- **Audit Events:** None.
- **HOPE Dependencies:** None.
- **Narrative Dependencies:** None.
- **POC Dependencies:** This IS the Interventions component. Same structural gap as Problems/Goals. The `poc_interventions.discipline` column enforces a CHECK constraint (`'RN','MSW','SC','LVN','HHA','MD','IDG','OTHER'`, `poc.py:357–361`), which is richer than the free-text discipline dropdown in `pocDraft.discipline` (`RNICA.jsx:4282`).
- **Order Dependencies:** None.
- **Task Dependencies:** None.
- **Current Screens:** RNICA Step 28 (Finalization).
- **Target Facesheet Section:** Section 11 — Care Planning & Team Recommendations
- **Migration Risk:** **High** — same as Problem Generation.
- **Migration Complexity:** **High** — `poc_interventions.frequency` is a separate column from `intervention_text`; the current `pocDraft.intervention` field combines both into a single string ("e.g., RN visits 2x/wk, titrate opioid per protocol" — see placeholder at `RNICA.jsx:4281`). Splitting this into separate fields on migration.

---

### 13. Discipline Recommendations

- **Current Section:** Discipline is a single `FormSelect` field (`RNICA.jsx:4282–4283`) inside the same POC issue editor row in "Finalization". Options: `["RN", "LVN/LPN", "MSW", "Chaplain", "HHA", "Volunteer", "Dietitian", "All disciplines"]`. A separate `visitFrequency` sub-section in "Admissions Order" (`RNICA.jsx:5166–5169`) captures per-discipline visit frequencies using `DEFAULT_VISIT_DISCIPLINES` (`RNICA.jsx:258–264`).
- **Component Name:** `FormSelect` for `pocDraft.discipline` at `RNICA.jsx:4282`. `visitFrequency` renders via generic card renderer at `RNICA.jsx:5166–5169` (inline JSX, no named component). Neither is a named React component.
- **Database Tables:**
  - **Current (implemented):** `finalization.pocEntries[].discipline` — JSON string in `rnica_assessments.form_data`. `admissionsOrder.visitFrequency` array — JSON in `rnica_assessments.form_data`. **Neither has a separate table.**
  - **Authoritative table:** `poc_interventions.discipline` column (`poc.py:396–399`) with CHECK constraint — **not connected to RNICA data today.** No `discipline_frequency` table exists separately; the `poc_interventions.frequency` column is the closest analog.
- **API Endpoints:** No dedicated endpoint. Stored via RNICA save/update.
- **Validation Rules:** None for `pocDraft.discipline`; it is optional. `admissionsOrder.visitFrequency` has no validation rules in `validateRNICA()`.
- **Audit Events:** None.
- **HOPE Dependencies:** None.
- **Narrative Dependencies:** None.
- **POC Dependencies:** This IS the Discipline Recommendations component. `visitFrequency` data in `admissionsOrder` is supposed to seed the per-discipline frequency columns in `poc_interventions`, but **no pipeline exists to do this today.**
- **Order Dependencies:** None directly.
- **Task Dependencies:** None.
- **Current Screens:** Discipline dropdown: RNICA Step 28 (Finalization). Visit frequency disciplines: RNICA Step 25 (`admissionsOrder`, `RNICA.jsx:191`).
- **Target Facesheet Section:** Section 11 — Care Planning & Team Recommendations
- **Migration Risk:** **High** — discipline data is split across two RNICA steps (Step 25 for frequency, Step 28 for POC discipline assignment) with no authoritative table. Consolidating into Section 11 requires reconciling both sources.
- **Migration Complexity:** **High** — requires designing the data model for how visit frequencies and POC discipline assignments relate, and building the pipeline to `poc_interventions`.

---

### 14. Visit Frequencies

- **Current Section:** Part of "Admissions Order" step — `admissionsOrder.visitFrequency` array (`RNICA.jsx:679`), seeded from `DEFAULT_VISIT_DISCIPLINES` (`RNICA.jsx:258–264`: SN/HA/MSW/SC/RN-SUP). Also referenced in Finalization POC editor as free-text inside `pocDraft.intervention`.
- **Component Name:** Rendered as inline JSX inside the `admissionsOrder` card titled "Visit Frequency" (described in `SIDEBAR_CONFIG` features: `"disciplineFrequency"`, line 230). No named component. The data model is `{ discipline, label, frequency, duration, prnVisits }` per entry.
- **Database Tables:**
  - **Current (implemented):** `admissionsOrder.visitFrequency` array JSON inside `rnica_assessments.form_data`. **No separate table.** Not synced to any other table on save.
  - **Relevant model:** `poc_interventions.frequency` column (`poc.py:407–410`, `String(100)`) — the authoritative location for visit frequency per intervention per discipline. **Not populated from RNICA `visitFrequency` today.**
  - No `discipline_frequency` or `visit_schedule` table found in `backend/app/models/`.
- **API Endpoints:** No dedicated endpoint. Stored via RNICA save/update JSON blob.
- **Validation Rules:** None — `admissionsOrder.visitFrequency` frequencies are free-text strings; no required-field validation in `validateRNICA()`.
- **Audit Events:** None.
- **HOPE Dependencies:** None.
- **Narrative Dependencies:** None.
- **POC Dependencies:** `admissionsOrder.visitFrequency` entries are intended to be the authoritative admission-phase visit schedule that seeds the POC. **This pipeline does not exist today.** `PlanOfCareVersion.source_kind = 'ICA'` (`plan_of_care_version.py:50`) implies the design intent, but no ICA-to-POC promotion endpoint was found.
- **Order Dependencies:** Visit frequencies are part of the verbal admission order (T.O. Verification at `RNICA.jsx:5180–5186`). Logically, the signed admission order approval via `POST /soc-orders/patients/{patient_id}/rn-admission` should fix the visit schedule, but that endpoint does not receive or store `visitFrequency` data (`soc_orders.py:30–36` — only `narrative`, `has_decline`, `lcd_status` fields accepted).
- **Task Dependencies:** None found.
- **Current Screens:** RNICA Step 25 (`admissionsOrder`, `RNICA.jsx:191`).
- **Target Facesheet Section:** Section 11 — Care Planning & Team Recommendations
- **Migration Risk:** **High** — Visit frequencies are a critical clinical and billing data point. Currently they are pure JSON free-text with no enforcement, no separate table, and no pipeline to the POC. They are also conceptually part of the Admission Order (Section 6 target), creating a cross-section ownership ambiguity between "Admission Action Center" and "Section 11 — Care Planning."
- **Migration Complexity:** **High** — requires net-new data model (discipline frequency table or formal integration into `poc_interventions.frequency`), a promotion endpoint, and a UI ownership decision (does visit frequency live in the Action Center alongside the admission order, or in Section 11 alongside POC?).

---

## Summary of Cross-Cutting Observations

| Area | Separate Table Today? | API Outside RNICA? | Audit Logged? | Migration Risk |
|------|-----------------------|-------------------|--------------|----------------|
| Psychosocial | ❌ JSON only | ❌ | ❌ | Low |
| Spiritual | ❌ JSON only | ❌ | ❌ | Low |
| Bereavement | ❌ JSON only | ❌ | ❌ | Low |
| Personal Care | ❌ JSON only | ❌ | ❌ | Medium |
| Teaching Needs | ❌ JSON only | ❌ | ❌ | Low |
| Admission Orders | Partial (LOC → facesheet) | ✅ `/soc-orders/…` | Partial | **High** |
| Orders Hub | ✅ `physician_orders` | ✅ `/physician-orders/*` | ✅ Full | **High** |
| Referrals | ❌ JSON only | ❌ | ❌ | **High** |
| Narrative | ❌ JSON only | ❌ (intelligence advisory) | ❌ | Medium |
| Problem Generation | ❌ JSON only (POC tables exist, unconnected) | ❌ | ❌ | **High** |
| Goals | ❌ JSON only (`poc_goals` unconnected) | ❌ | ❌ | **High** |
| Interventions | ❌ JSON only (`poc_interventions` unconnected) | ❌ | ❌ | **High** |
| Discipline Recs | ❌ JSON only | ❌ | ❌ | **High** |
| Visit Frequencies | ❌ JSON only | ❌ | ❌ | **High** |

**Critical finding:** The `POCProblem` / `POCGoal` / `POCIntervention` / `PlanOfCare` / `PlanOfCareVersion` tables (`backend/app/models/poc.py`, `plan_of_care.py`, `plan_of_care_version.py`) are real, hardened, FK-safe tables — confirmed status "HARDENED / FK SAFE" in file headers. However, **the RNICA assessment's POC draft has zero API integration with these tables today**. The `PlanOfCareVersion.source_kind = 'ICA'` value (`plan_of_care_version.py:49`) is a declared future integration point that has not been implemented. The redesign's Section 11 work is therefore largely greenfield backend integration, not just UI rearrangement.

---

## Target Section Mapping (Loose Tier Labels ? Canonical Section 1�12)

The individual entries above use looser "Target Facesheet Section" labels
from earlier drafts of this governance thread (e.g. "Section 1-4 core",
"Section 5", "Admission Action Center"). Cross-reference against the
canonical numbering in `SNS_RNICA_MASTER_MAP_1.0.md`:

| Inventoried area | Canonical target (Master Map) |
|---|---|
| Patient Demographics, Caregiver Assessment, Advanced Care Planning | Section 1 � Patient & Encounter Snapshot |
| Pain Assessment, Symptom Impact | Section 2 � Immediate Needs & Symptom Triage |
| Diagnoses (incl. embedded Narrative field) | Section 3 � Disease History & Clinical Trajectory (structured findings); Section 10 for the narrative text itself |
| Performance Status | Section 4 � Functional & Performance Status |
| Neurological, Cardiovascular, Respiratory, Infection, GI, GU, Endocrine, Musculoskeletal, Nutrition, Skin/Wounds | Section 5 � Head-To-Toe Clinical Assessment |
| Disease-specific LCD criteria (embedded in Diagnoses today) | Section 6 � Disease Specific Criteria & Eligibility Support |
| Imminent Death, SFV, Symptom Follow-Up, HOPE Elements | Section 7 � HOPE & Symptom Follow-Up |
| Psychosocial, Spiritual, Bereavement, Personal Care, Teaching Needs | Section 8 � Whole Person & Caregiver Assessment |
| Safety | Section 9 � Safety, Environment, Equipment & Supplies |
| Narrative (diagnoses.lcdEligibilityNarrative) | Section 10 � Clinical Narrative & Disease Trajectory |
| Problem Generation, Goals, Interventions, Discipline Recommendations, Visit Frequencies | Section 11 � Master Plan of Care Review |
| Finalization | Section 12 � Final Review & Finalization |
| Admission Orders, Hospice Orders Hub, Referrals | Admission Action Center (global, non-numbered) |

---

## Cross-Cutting Gaps Found (Read Across All Three Research Passes)

These recurring gaps were independently identified by more than one research
pass and should be treated as priority findings for the RNICA redesign,
separate from any individual section's risk/complexity rating:

1. **No RNICA-specific audit logging.** None of the ~28 sections have audit
   events tied to POST/PUT /visits/rnica/* create/update/lock endpoints.
   Only a general FINALIZE_VISIT event exists, tied to Visit records,
   not RnicaAssessment records. This is a compliance gap independent of
   the redesign and should be raised as its own governance/engineering
   item (see SNS_DESIGN_SYSTEM_1.0.md �2.5 Preserve Existing Compliance
   Behavior � note this is a pre-existing gap, not something the redesign
   is introducing).
2. **Advanced Care Planning storage path mismatch.** Frontend INITIAL_FORM
   defines ACP fields at orm_data.demographics.advancedCarePlanning.*,
   but backend sync helpers (_extract_rnica_code_status,
   _extract_rnica_dpoa, _extract_rnica_decision_maker,
   _overlay_shared_code_status) read/write orm_data.advancedCarePlanning
   (top-level). This is a latent bug independent of the redesign � flagged
   for separate engineering triage, not to be silently "fixed" as a side
   effect of a UI redesign per �2.5.
3. **No authoritative Plan of Care / Orders / Referrals tables exist yet.**
   Problem Generation, Goals, Interventions, Discipline Recommendations,
   Visit Frequencies, Admission Orders, Hospice Orders Hub, and Referrals
   are all currently stored only as JSON keys inside
   nica_assessments.form_data, with no separate authoritative table, no
   task-generation pipeline, and (for Referrals) no cross-discipline
   visibility. Per SNS_DESIGN_SYSTEM_1.0.md �2.3 (Identity of Data), the
   Master Sync Rules in SNS_RNICA_MASTER_MAP_1.0.md and the POC
   Generation Rule in SNS_POC_GENERATION_MATRIX_1.0.md �7 both assume an
   authoritative Plan of Care / Orders data model � **this must be built,
   not just redesigned visually**, before the per-section POC panels or
   the global Admission Action Center can be real (not merely a UI mock).
4. **HOPE validation lives in the frontend only.** alidateRNICA() in
   RNICA.jsx is the only place HOPE-required-field warnings/errors are
   enforced; the backend clinical_note_validation_engine.py operates on
   ClinicalNote/visit-note objects, not directly on RnicaAssessment rows.
   Any redesign that restructures fields must keep alidateRNICA()'s HOPE
   checks in sync with wherever those fields move, or backend-side
   validation should be added � a decision this document flags but does
   not make.


---

## HOPE Crosswalk (Deliverable 6)

Source: CMS HOPE v1.02 Guidance Manual and Item Set (official item names/
definitions extracted from the attached CMS PDFs) cross-referenced against
a user-provided SNS HOPE/SFV target-mapping table, reconciled against the
codebase-confirmed findings in Tier 1 / Tier 3 / Tier 9 above (this
section's own research, not re-derived).

**How to read the table:** "SNS Target Section" and "SNS Target Field"
describe where the item SHOULD live per the target mapping. "Current RNICA
Implementation" reports what the Tier 1/3/9 codebase research actually
found in `RNICA.jsx` / `visits.py` today. Where the two disagree, that is a
real gap to close during implementation, not an error in either document.

### HOPE Mapping Validation Rule

A HOPE item may exist in one of four states:

1. **Mapped and Implemented** — target section is approved, and the
   codebase research confirmed the field exists and is wired to that HOPE
   code.
2. **Mapped and Partially Implemented** — target section is approved; some
   but not all of the item's sub-elements (e.g. one J2051 sub-item, or the
   screening flag without the date) were confirmed.
3. **Mapped but Not Implemented** — target section is approved, but the
   codebase research found no corresponding RNICA field at all.
4. **Not Applicable to RNICA** — the item belongs to a different module
   (patient demographics, billing, admission/discharge workflow) and is
   correctly out of RNICA's scope.

**The HOPE Crosswalk establishes the target destination. The Section
Inventory establishes the implementation status. The Crosswalk is not
evidence that a field is currently wired in code.** Approving the target
mapping (Category A, below) does not certify current implementation —
that is a separate, ongoing verification task carried out in this
Section Inventory.

### Category A — Target Mapping (Approved)

The following HOPE-item-group → RNICA-section destinations are approved
architecture (per `SNS_RNICA_MASTER_MAP_1.0.md` and the user-provided
target crosswalk) and are not re-litigated by implementation gaps found
below:

| HOPE Items | Target RNICA Destination |
|---|---|
| A items | Demographics / Encounter |
| F items | Advanced Care Planning → Goals of Care → Spiritual / Existential |
| I items | Diagnoses |
| J items | Symptoms → Pain → Dyspnea → Symptom Impact → Imminent Death |
| M items | Integumentary |
| N items | Medications |
| Z items | Finalization |

### Category B — Implementation Verification (Inventory Work)

The per-item tables below are Category B: they report whether the
approved target mapping is *currently* satisfied in code. Gaps found here
(e.g. F3000, J0905/J0910, J2030/J2040, N0500/N0510/N0520, M1195/M1200) do
**not** block or reopen the approved architecture — they become tracked
implementation findings to resolve during the build phases in
`SNS_RNICA_MASTER_MAP_1.0.md`'s Build Order.

### Section A — Administrative Information

| Code | CMS Item Name | SNS Target Section | Current RNICA Implementation |
|---|---|---|---|
| A0050 | Type of Record | HOPE Record Admin | Not part of RNICA form_data — record type is implicit in which endpoint/workflow is used. Likely owned by visit/admission workflow, not RNICA. |
| A0100 | Facility Provider Numbers | Agency Settings | Out of RNICA scope — agency profile data. |
| A0215 | Site of Service at Admission | General Assessment | Not confirmed in RNICA.jsx by codebase research — likely admission/registration module. |
| A0220 | Admission Date | General Assessment | Not confirmed in RNICA.jsx — likely `Visit`/admission record. |
| A0250 | Reason for Record | HOPE Record Admin | Maps to the ADM/HUV1/HUV2/DC distinction already used by `hope_phase_b_engine.py` for SFV triggering — not a direct RNICA field. |
| A0270 | Discharge Date | Discharge Workflow | Out of RNICA scope. |
| A0500 | Legal Name of Patient | Patient Overview | Out of RNICA scope — sourced from patient/demographics record, not RNICA form_data. |
| A0550 | Patient ZIP Code | Patient Overview | Out of RNICA scope. |
| A0600 | SSN / Medicare Numbers | Patient Overview | Out of RNICA scope. |
| A0700 | Medicaid Number | Patient Overview | Out of RNICA scope. |
| A0810 | Sex | Patient Overview | Out of RNICA scope. |
| A0900 | Birth Date | Patient Overview | Out of RNICA scope. |
| A1005 | Ethnicity | Patient Demographics | **Confirmed** — `demographics` SIDEBAR_CONFIG hope array; validated in `validateRNICA()` (`RNICA.jsx:776-862`). |
| A1010 | Race | Patient Demographics | **Confirmed** — same as A1005. |
| A1110 | Language | General Assessment | **Confirmed** — `demographics` hope array; interpreter-need sub-field. |
| A1400 | Payer Information | Patient Overview / Billing | Out of RNICA scope. |
| A1805 | Admitted From | General Assessment | Not confirmed in RNICA.jsx. |
| A1905 | Living Arrangements | General Assessment | Not confirmed as a distinct HOPE-tagged field in RNICA.jsx (residence type exists in demographics but not wired to a HOPE code by the codebase research). |
| A1910 | Availability of Assistance | General Assessment | Not confirmed as a distinct HOPE-tagged field — overlaps conceptually with Caregiver Assessment, but no HOPE code wiring found. |
| A2115 | Reason for Discharge | Discharge Workflow | Out of RNICA scope. |

### Section F — Preferences / Spiritual

| Code | CMS Item Name | SNS Target Section | Current RNICA Implementation |
|---|---|---|---|
| F2000 | CPR Preference | Advanced Care Planning | **Confirmed** — `advancedCarePlanning`/`finalization` hope arrays; feeds `_extract_rnica_code_status` (subject to the ACP storage-path bug noted in Cross-Cutting Gaps). |
| F2100 | Other Life-Sustaining Treatment Preferences | Advanced Care Planning | **Confirmed** — same as F2000. |
| F2200 | Hospitalization Preference | Advanced Care Planning / Goals of Care | **Confirmed** — same as F2000. |
| F3000 | Spiritual/Existential Concerns | Spiritual Screening (target Section 8) | **GAP — not found.** No SIDEBAR_CONFIG hope array references F3000 anywhere in RNICA.jsx. The RNICA "Spiritual" content (target Section 8, Whole Person & Caregiver Assessment) exists as a clinical field but is not wired as a CMS HOPE item. This is a real, previously-unflagged compliance gap. |

### Section I — Active Diagnoses / Comorbidities

| Code | CMS Item Name | SNS Target Section | Current RNICA Implementation |
|---|---|---|---|
| I0010 | Principal Diagnosis | Diagnosis Review | **Confirmed** — `diagnoses` hope array; `formData.diagnoses`. |
| I0100 | Cancer | Diagnosis Review (comorbidities) | **Confirmed** — `HOPE_COMORBIDITY_CATEGORIES` (`RNICA.jsx:1826-1841`), `diagnoses.hopeComorbidities.cancer`. |
| I0600 | Heart Failure | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.heartFailure`. |
| I0900 | PVD/PAD | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.pvdPad`. |
| I0950 | Cardiovascular (excl. HF) | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.cardiovascularExclHF`. |
| I1101 | Liver Disease | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.liverDisease`. |
| I1510 | Renal Disease | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.renalDisease`. |
| I2102 | Sepsis | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.sepsis`. |
| I2900 | Diabetes Mellitus | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.diabetesMellitus`. |
| I2910 | Neuropathy | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.neuropathy`. |
| I4501 | Stroke | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.stroke`. |
| I4801 | Dementia (incl. Alzheimer's) | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.dementia`. |
| I5150 | Neurological Conditions | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.neurologicalConditions`. |
| I5401 | Seizure Disorder | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.seizureDisorder`. |
| I6202 | COPD | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.copd`. |
| I8005 | Other Medical Condition | Diagnosis Review | **Confirmed** — `diagnoses.hopeComorbidities.other`. |

### Section J — Health Conditions (Pain / Dyspnea / Symptom Impact / SFV)

| Code | CMS Item Name | SNS Target Section | Current RNICA Implementation |
|---|---|---|---|
| J0050 | Death is Imminent | Imminently Dying Assessment | **Confirmed** — validated at `imminentDeath.appearsThreeDaysOrLess` (`RNICA.jsx:860-862`); also cross-listed in the Diagnoses hope array (`RNICA.jsx:207`) — one CMS item, two section references, needs reconciliation during migration. |
| J0900 | Pain Screening | Pain Assessment | **Confirmed** — `pain` hope array; validated in `validateRNICA()`. |
| J0905 | Pain Active Problem | Pain Assessment | **GAP — not confirmed.** Prior research found J0900/J0915 validated but did not identify a distinct `pain.activeProblem`-style field for J0905. |
| J0910 | Comprehensive Pain Assessment | Pain Assessment | **GAP — not confirmed.** No distinct comprehensive-pain-assessment-completed field identified separate from the general pain assessment fields. |
| J0915 | Neuropathic Pain | Pain Assessment | **Confirmed** — `pain` hope array; validated in `validateRNICA()`. |
| J2030 | Screening for Shortness of Breath | Respiratory Assessment | **GAP — not confirmed.** No distinct SOB-screening-completed/date field identified in the Respiratory section by the codebase research; respiratory dyspnea findings exist but are not wired to J2030 specifically. |
| J2040 | Treatment for Shortness of Breath | Respiratory Assessment | **GAP — not confirmed.** No distinct SOB-treatment-initiated field identified. |
| J2050 | Symptom Impact Screening | Symptom Impact | **Naming correction:** the official CMS name is "Symptom Impact Screening" (a gate: was screening done, and if so proceed to J2051) — it is NOT "SFV Completed" as an earlier draft of this inventory assumed. RNICA's `sfv` SIDEBAR_CONFIG hope array lists J2050 (`RNICA.jsx:220`), which conflates the screening-gate item with the SFV section; the actual screening gate logically belongs with `symptomImpact` (J2051), not `sfv`. Flag for reconciliation during migration — do not assume the current code's placement is correct. |
| J2051 (A-H) | Symptom Impact (Pain, SOB, Anxiety, Nausea, Vomiting, Diarrhea, Constipation, Agitation) | Symptom Impact | **Confirmed** — `symptomImpact` hope array; validated J2051 A-H in `validateRNICA()`; also re-assessed at SFV time via `sfv.symptomImpactAtSfv.*` (`RNICA.jsx:588-593`). This is the primary SFV trigger source (`hope_phase_b_engine.py:319-394`). |
| J2052 | Symptom Follow-up Visit (SFV) | SFV Engine / SFV Review | **Confirmed** — `sfv.inPersonSfvCompleted`, `sfv.reasonNotCompleted`; completion tracked via `sfv_requirements` table and `complete_sfv_requirement_from_visit()` (`hope_phase_b_engine.py:397-446`), not via RNICA save directly. |
| J2053 | SFV Symptom Impact | SFV Engine / SFV Review | **Confirmed** — `sfv.symptomImpactAtSfv.*` (`RNICA.jsx:588-593`). |

### Section M — Skin Conditions

| Code | CMS Item Name | SNS Target Section | Current RNICA Implementation |
|---|---|---|---|
| M1190 | Skin Conditions (yes/no gate) | Integumentary Assessment | **Confirmed** — referenced in BOTH `performanceStatus` and `skin` SIDEBAR_CONFIG hope arrays (`RNICA.jsx` per area 11 above) — this dual-listing is itself a data-integrity question to resolve during migration (which section is authoritative for M1190?). |
| M1195 | Types of Skin Conditions | Integumentary Assessment | **GAP — not confirmed.** No distinct multi-select "types of skin condition" field wired to a HOPE code was identified separate from the general skin/wound findings fields. |
| M1200 | Skin and Ulcer/Injury Treatments | Integumentary Assessment | **GAP — not confirmed.** No distinct HOPE-coded treatments-checklist field identified; wound care interventions exist as free-text/POC fields only. |

### Section N — Medications

| Code | CMS Item Name | SNS Target Section | Current RNICA Implementation |
|---|---|---|---|
| N0500 | Scheduled Opioid | Medication Review | **GAP — not found.** No SIDEBAR_CONFIG hope array in RNICA.jsx references N0500/N0510/N0520 at all. There is no RNICA field for "was a scheduled opioid initiated/continued." This is a previously-unflagged compliance gap — N-section items are entirely absent from RNICA today. |
| N0510 | PRN Opioid | Medication Review | **GAP — not found.** Same as N0500. |
| N0520 | Bowel Regimen | Medication Review / GI | **GAP — not found.** Same as N0500; also relevant to the GI/Gastrointestinal assessment target section, not just Medication Review. |

### Section Z — Record Administration

| Code | CMS Item Name | SNS Target Section | Current RNICA Implementation |
|---|---|---|---|
| Z0350 | Date Assessment Completed | Finalization | **Confirmed** — `finalization` section timestamps (see Tier 9 Finalization inventory above). |
| Z0400 | Signature(s) of Person(s) Completing Record | Finalization | **Confirmed** — RN signature capture in Finalization (see Tier 9 above). |
| Z0500 | Signature of Person Verifying Record Completion | Finalization | Not separately confirmed from Z0400 by the codebase research — may be the same signature capture, or may be a distinct supervisor-review signature; needs verification during implementation planning. |

### HOPE Crosswalk — Summary of New Gaps Found

Cross-referencing the official CMS HOPE v1.02 item set against the
codebase-confirmed RNICA field inventory (Tier 1/3/9 above) surfaces
gaps beyond the two already documented in Cross-Cutting Gaps Found:

1. **F3000 (Spiritual/Existential Concerns) has no RNICA field wiring at all** — a CMS-required HOPE item with no home in the current form.
2. **The entire Section N (N0500 Scheduled Opioid, N0510 PRN Opioid, N0520 Bowel Regimen) is absent from RNICA** — no fields, no HOPE codes, nothing. These would need to be sourced from medication orders/MAR data or added as new RNICA fields.
3. **J2030/J2040 (Screening/Treatment for Shortness of Breath) are not distinctly wired** — the Respiratory section captures dyspnea findings, but not these two specific CMS screening/treatment-gate items.
4. **J0905/J0910 (Pain Active Problem, Comprehensive Pain Assessment) are not distinctly wired** — only J0900 (screening) and J0915 (neuropathic) are confirmed.
5. **M1195/M1200 (Types of Skin Conditions, Skin/Ulcer Treatments) are not distinctly wired as HOPE-coded fields** — general skin/wound findings exist but not as this specific CMS checklist structure.
6. **J2050 naming/placement should be reconciled** — its official meaning ("Symptom Impact Screening" gate) does not match its current placement solely in the `sfv` section; it logically belongs adjacent to J2051 in Symptom Impact.
7. **M1190 is referenced from two different sections** (`performanceStatus` and `skin`) — needs a single authoritative owner.

These six items (F3000, N0500-0520, J2030/J2040, J0905/J0910, M1195/M1200)
represent CMS HOPE v1.02 items with no current RNICA field — they are
new-field-creation work, not just UI-migration work, and should be
prioritized accordingly in the Field Inventory / Phase 1 build order in
`SNS_RNICA_MASTER_MAP_1.0.md`.

### High-Risk HOPE Inventory Review List

These are the highest-risk items because they have **approved target
mappings** in the RNICA architecture (Category A) but were specifically
identified as needing implementation verification (Category B) before
build completion. Organized into four risk tiers with per-item inventory
tasks.

**Tier 1 — Critical (Review First)**

1. **J2050 → J2053 (Symptom Impact / SFV Logic)** — `J2050`, `J2051`,
   `J2052`, `J2053`.
   Reason: highest workflow complexity; multiple dependencies; potential
   naming mismatch discovered (see J2050 naming correction above);
   HOPE-specific submission logic; narrative dependency; POC dependency.
   Inventory tasks: Field Verification, Trigger Logic, Export Mapping,
   Validation Rules, RNICA Ownership.

2. **J0905 / J0910 (Pain Workflow)** — `J0905`, `J0910`.
   Reason: pain drives hospice care planning; POC generation dependency;
   narrative dependency; survey risk if missing.
   Inventory tasks: Pain Assessment Fields, POC Integration, Evidence
   Mapping, Narrative Usage.
   Pain and symptom burden are core hospice documentation elements.

3. **J2030 / J2040 (Dyspnea Workflow)** — `J2030`, `J2040`.
   Reason: dyspnea is a major hospice symptom; respiratory POC
   dependency; HOPE dependency; equipment dependency.
   Inventory tasks: Respiratory Fields, POC Dependency, Action Center
   Triggers, Export Logic.
   Dyspnea is identified as a major indicator in pulmonary hospice
   documentation.

**Tier 2 — High Risk**

4. **N0500 / N0510 / N0520 (Medication Items)** — `N0500`, `N0510`,
   `N0520`.
   Reason: medication workflow; opioid workflow; bowel regimen workflow;
   potential implementation gap.
   Inventory tasks: Medication Mapping, Validation Rules, HOPE Export,
   Action Center Linkage.

5. **M1195 / M1200 (Skin Workflow)** — `M1195`, `M1200`.
   Reason: Integumentary ownership; pressure injury workflow; skin
   treatment workflow; POC dependency.
   Inventory tasks: Integumentary Mapping, Wound Fields, Treatment
   Logic, Narrative Dependency.
   Pressure injuries and skin decline are significant hospice
   documentation elements.

**Tier 3 — Medium Risk**

6. **F3000 (Spiritual / Existential Concerns)**.
   Reason: mapped architecturally; implementation not confirmed;
   Section 8 dependency.
   Inventory tasks: Spiritual Assessment Fields, Chaplain Workflow,
   Narrative Integration.

7. **Diagnosis / Comorbidity Validation** — `I0010`, Comorbidity
   Categories.
   Reason: diagnosis drives eligibility; narrative dependency;
   certification dependency.
   Inventory tasks: Diagnosis Mapping, Disease-Specific Links, LCD
   Support Mapping.
   Disease-specific and non-disease-specific factors must support the
   clinical picture of decline and prognosis.

**Tier 4 — Final Verification**

8. **Demographic Items** — A-series items.
   Review: CMS Export, Registration Source, Facesheet Mapping.

9. **Finalization Items** — `Z0350`, `Z0400`, `Z0500`.
   Review: Finalization Workflow, Submission Logic, Audit Logging.

### Recommended Review Sequence

1. J2050
2. J2051
3. J2052
4. J2053
5. J0905
6. J0910
7. J2030
8. J2040
9. N0500
10. N0510
11. N0520
12. M1195
13. M1200
14. F3000
15. I0010 / Comorbidities
16. A-Series
17. Z-Series

This order addresses the highest-risk items first: symptom impact, pain,
dyspnea, medications, skin integrity, and spiritual concerns — the items
most closely tied to hospice assessment, individualized plan-of-care
generation, symptom management, and supporting evidence for decline and
prognosis documentation.

### Expected Inventory Output For Each Item

For each HOPE item, the inventory should record:

- HOPE Item ID
- CMS Name
- RNICA Section
- RNICA Field
- Status: Implemented / Partial / Missing / N/A
- POC Dependency
- Narrative Dependency
- Export Dependency
- Validation Rules
- Migration Complexity

### Deliverable #6 Definition — SNS_HOPE_CROSSWALK_1.0

This HOPE Crosswalk (the tables above) constitutes Deliverable #6,
formally named `SNS_HOPE_CROSSWALK_1.0`. Its authoritative column set,
for any future revision or export of this deliverable as a standalone
document, is:

| Column | Purpose |
|---|---|
| HOPE Item ID | Official CMS item code (e.g. J2051A) |
| CMS Item Name | Official CMS item label |
| Target RNICA Section | Approved destination per Category A above |
| Target RNICA Field | Actual/planned field path in RNICA form_data |
| Mapping Type | Direct, Derived, Calculated, or Narrative Supported |
| Trigger Logic | When the item is required/activated (e.g. SFV threshold) |
| Export Logic | How the value is packaged for HOPE export |
| Current Status | Implemented / Partial / Missing / Not Applicable (per the HOPE Mapping Validation Rule above) |
| Notes | Reconciliation flags (e.g. J2050 naming, M1190 dual-listing) |

The tables in this document currently present this information in a
condensed 4-column form (Code / CMS Item Name / SNS Target Section /
Current RNICA Implementation); the full 9-column form above is the
target schema if this crosswalk is ever split into its own standalone
file.

### Governance Outcome

```
Deliverable #6 — HOPE Crosswalk (SNS_HOPE_CROSSWALK_1.0)

STATUS: Accepted — Architecture Complete
Implementation Validation Required During SNS_RNICA_SECTION_INVENTORY_1.0
```

This preserves the approved target-state architecture (Category A) while
allowing the inventory phase to continue documenting where the existing
codebase does or does not currently satisfy the HOPE mapping (Category B).
No architecture changes are implied or authorized by any Category B
finding above.


---

## Action Center Trigger Inventory (Deliverable 8) and Audit Event Crosswalk (Deliverable 7)

Source: dedicated codebase research pass over `backend/app/api/` (physician
orders, medications, patient orders, communications log, visits) and
`backend/app/models/` (AuditLog, PhysicianOrder, PatientOrder,
CommunicationsLog, RnicaAssessment). Read-only research; every claim below
is file:line-cited by the underlying pass. Full endpoint/model detail is
condensed here — see the appendix tables for the raw citation list this
summary was built from, retained in this document rather than as a
separate scratch file.

### Completeness Matrix — Action Center Categories

| Action Center Category | Endpoint | Model | UI | MD Approval | Task Generation | Audit Event |
|---|---|---|---|---|---|---|
| Medication Requests | Yes | Yes | Yes | Partial (via PhysicianOrder link) | Implicit | Yes |
| Physician Orders | Yes | Yes | Yes | Yes | Yes | Yes |
| Physician Contact | Yes | Yes | Yes | No | No | Yes |
| DME Orders | Yes | Yes | Yes | No | No | Yes |
| Supply Orders | Yes | Yes | Yes | No | No | Yes |
| Oxygen Orders | Yes | Yes | Yes | No | No | Yes |
| Lab Requests | Yes | Yes | Yes | No | No | Yes |
| Treatment Orders | Yes | Yes | Yes | No | No | Yes |
| Diet Orders | Yes | Yes | Yes | No | No | Yes |
| Referrals | **No** | **No** | **No** | No | No | **No** |
| Office Communication | Yes | Yes | Yes | No (workflow gate only) | Yes (via bridge) | **No** |

DME/Supply/Oxygen/Lab/Treatment/Diet orders share one generic
`PatientOrder` model/endpoint family distinguished by `order_type`; they
are listed as separate rows above because they are separate Action
Center categories per the Master Map, but they are one implementation
(`backend/app/models/patient_order.py`, `backend/app/api/patient_orders.py` per the endpoint appendix below).

### Endpoint Inventory by Category

**Physician Orders** (full lifecycle, `backend/app/api/physician_orders.py`):
- `POST /physician-orders/patients/{patient_id}` -> `CREATE_PHYSICIAN_ORDER`
- `POST /{order_id}/submit` -> `SUBMIT_PHYSICIAN_ORDER`
- `POST /{order_id}/clinical-review` -> `CLINICAL_REVIEW_PHYSICIAN_ORDER`
- `POST /{order_id}/approve` -> `APPROVE_PHYSICIAN_ORDER` + `PROVIDER_SIGNATURE_ACCESS_GRANTED` (denial path -> `PROVIDER_SIGNATURE_ACCESS_DENIED`)
- `POST /{order_id}/execute` -> `EXECUTE_PHYSICIAN_ORDER`
- `POST /{order_id}/complete` -> `COMPLETE_PHYSICIAN_ORDER`
- `POST /{order_id}/cancel` -> `CANCEL_PHYSICIAN_ORDER`
- `GET /{order_id}/status-history` -> reads `PhysicianOrderStatusEvent` (immutable transition log, separate from `AuditLog`)
- `GET /patients/{patient_id}` -> list orders (no audit; read-only)

**Medications** (`backend/app/api/medications.py`):
- `POST /medications/patients/{patient_id}` -> `ADD_MEDICATION`
- `POST /{medication_id}/discontinue` -> `DISCONTINUE_MEDICATION`
- `GET /medications/drug-search` -> RxNorm typeahead, no audit (read-only lookup)

**DME / Supply / Oxygen / Lab / Treatment / Diet Orders** (`backend/app/api/patient_orders.py`, `PatientOrder` model, `order_type` distinguishes category):
- `POST /patient-orders/patients/{patient_id}` -> `ADD_PATIENT_ORDER`
- `POST /{order_id}/discontinue` -> `DISCONTINUE_PATIENT_ORDER`
- `GET /patient-orders/patients/{patient_id}` -> list (optionally filtered by `order_type`)
- No MD-approval gate, no signature fields, no task linkage, no intermediate status states — only `active`/`discontinued`.

**Physician Contact** — `SET_PATIENT_PHYSICIAN_ASSIGNMENT` audit action; this is administrative assignment/linking of physician contact info to a patient, distinct from a `PhysicianOrder`. No MD approval gate applies (by design — it is not a clinical order).

**Communications Log** (`backend/app/api/communications_log/router.py`):
- `POST /communications-log` -> **no audit event** (line 278)
- `POST /{commlog_id}/acknowledge` -> **no audit event** (line 404)
- `POST /{commlog_id}/verify` -> **no audit event** (line 459)
- `POST /{commlog_id}/resolve` -> **no audit event** (line 529)
- Workflow states: `RECEIVED -> ACKNOWLEDGED -> VERIFIED -> RESOLVED`. Task generation/alerts occur via a bridge service, but none of the four lifecycle transitions above write to `AuditLog`.

**RNICA Assessment** (`backend/app/api/visits.py`):
- `POST /visits/rnica/save` -> **no audit event** (line 752)
- `PUT /visits/rnica/{assessment_id}` -> **no audit event** (line 931)
- `POST /visits/rnica/{assessment_id}/lock` -> **no audit event** (line 979)
- `RnicaAssessment` model itself has no `created_by`/`updated_by`/`locked_by` columns — the whole form is one JSONB `form_data` blob with no field-level or record-level audit trail today.

**Referrals** — no model, no endpoint, no UI, no audit logging found anywhere in the codebase. Not implemented.

**Visits** (context, not an Action Center category): `POST /visits/create` -> `CREATE_VISIT`; `POST /visits/{visit_id}/finalize` -> `FINALIZE_VISIT`.

### AuditLog Mechanism (ground truth for the crosswalk)

- Table: `backend/app/models/audit_log.py`. Key columns: `id`, `request_id`, `tenant_id` (required), `user_id`, `role`, **`action`** (the primary audit-action key), `entity_type`, `entity_id`, `ip_address`, `description`, `event_metadata` (JSON), `created_at`, `created_by`.
- Composite indexes on `(tenant_id, action)`, `(tenant_id, entity_type)`, `(tenant_id, user_id)` support fast per-tenant/per-workflow/per-user audit queries.
- Logging call site: `app.services.audit_logger.log_event()`.
- Total distinct `action` values enumerated across the codebase during this research pass: **59**.

### Audit Event Crosswalk — Coverage by Workflow

| Workflow | Audit Coverage |
|---|---|
| Physician Orders | **Full** — 9 distinct action types across the complete create -> submit -> clinical-review -> approve -> execute -> complete/cancel lifecycle, plus a separate immutable `PhysicianOrderStatusEvent` transition log. |
| Medications | **Partial** — create + discontinue logged; links to `PhysicianOrder` for signature traceability when applicable. |
| DME / Supply / Oxygen / Lab / Treatment / Diet Orders | **Partial** — create + discontinue logged; no status-transition events, no fulfillment/transmission tracking. |
| Physician Contact | **Partial** — assignment event logged; no approval workflow (by design, not a clinical order). |
| Office Communication | **Gap** — task/alert generation happens via a bridge service, but none of the 4 lifecycle transitions (create/acknowledge/verify/resolve) write an `AuditLog` row. |
| RNICA Assessment | **Critical gap** — zero audit events for save/update/lock; the model itself lacks `created_by`/`updated_by`/`locked_by` columns. |
| Referrals | **Not implemented** — no model, endpoint, UI, or audit logging exists. |

### Gaps Found (Action Center + Audit)

1. **RNICA Assessment lifecycle has zero audit logging** (`save_rnica_assessment`, `update_rnica_assessment`, `lock_rnica_assessment` in `backend/app/api/visits.py` lines 752/931/979) despite being the primary hospice intake form. This is the single highest-priority audit gap in the codebase — a compliance surveyor would identify it immediately.
2. **Communications Log has zero audit logging** on create or any of its three status transitions (acknowledge/verify/resolve), despite being a multi-step clinical workflow.
3. **Referrals are entirely unimplemented** — no model, endpoint, UI, or audit trail. Must be explicitly scoped as future work, not assumed to exist.
4. **Generic PatientOrder categories (DME/Supply/Oxygen/Lab/Treatment/Diet) have no MD approval workflow and no status-transition audit events** — by design (clinical-staff direct entry), but this distinction should be stated explicitly in governance so stakeholders don't assume these orders are physician-vetted the way `PhysicianOrder` records are.
5. **`RnicaAssessment` has no `created_by`/`updated_by`/`locked_by` model columns** — even if audit logging is added at the API layer, the underlying record itself cannot answer "who last touched this" without parsing `form_data` JSON (which does not reliably contain this either).

### Recommended Remediation (for future implementation phases, not authorized by this document)

1. Add `log_event()` calls to the three RNICA save/update/lock endpoints (`SAVE_RNICA_ASSESSMENT`, `UPDATE_RNICA_ASSESSMENT`, `LOCK_RNICA_ASSESSMENT`; `entity_type="rnica_assessment"`).
2. Add `log_event()` calls to the four Communications Log endpoints (`CREATE_COMMUNICATIONS_LOG`, `ACKNOWLEDGE_COMMUNICATIONS_LOG`, `VERIFY_COMMUNICATIONS_LOG`, `RESOLVE_COMMUNICATIONS_LOG`).
3. Scope and build Referrals as a net-new model/endpoint/UI/audit feature if required for the RNICA target build.
4. Add status-transition audit events and fulfillment/transmission metadata to the generic `PatientOrder` workflow.
5. Add `created_by`/`updated_by`/`locked_by` columns to `RnicaAssessment` so record-level provenance does not depend solely on audit-log correlation.

These remediation items are implementation/inventory findings only — no
code changes are authorized by this document.


---

## Status / Next Steps — Remaining Inventory Deliverables

With Deliverable #6 (HOPE Crosswalk) and Deliverables #7/#8 (Audit Event
Crosswalk, Action Center Trigger Inventory) completed at the architecture
level above, the remaining inventory deliverables are each formalized
below as their own named output document, per the numbered list in
`SNS_RNICA_MASTER_MAP_1.0.md`'s Build Order. None of these are authorized
as code changes — this remains inventory/documentation work only.

### 1. Field Inventory (Highest Priority)

**Purpose:** Catalog every RNICA field. For each field, identify: Field
Name, Section Owner, Data Type, Required/Optional Status, HOPE
Dependencies, POC Dependencies, Narrative Dependencies.

**Output:** `SNS_RNICA_FIELD_INVENTORY_1.0`

### 2. Database Mapping

**Purpose:** Map every RNICA field to: Database Table, Column, Enum,
Relationship, Migration Source.

**Output:** `SNS_RNICA_DATABASE_MAPPING_1.0`

### 3. API Mapping

**Purpose:** Map UI → API → Database for every field. Identify GET
endpoints, POST endpoints, PATCH endpoints, validation layers, and
missing endpoints.

**Output:** `SNS_RNICA_API_MAPPING_1.0`

### 4. Validation Inventory

**Purpose:** Document for each field whether it is Required, Conditional,
HOPE Required, CDPH Required, CMS Required, and/or POC Required.

**Output:** `SNS_RNICA_VALIDATION_INVENTORY_1.0`

### 5. Narrative Source Inventory

**Purpose:** Identify every narrative paragraph source. Map Narrative
Section → Source Fields → POC References → HOPE References. Supports
patient-specific documentation and decline narratives.

**Output:** `SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0`

### 6. Audit Crosswalk

**Purpose:** Identify audit events. Track Created, Modified, Deleted,
Resolved, Finalized, Signed. (Baseline findings already captured above in
this document's Audit Event Crosswalk section — this deliverable extends
that baseline to full field-level coverage once implemented.)

**Output:** `SNS_RNICA_AUDIT_CROSSWALK_1.0`

### 7. Action Center Trigger Inventory

**Purpose:** Map every clinical trigger to its Action Center consequence,
e.g. Dyspnea → Oxygen Request; Pain Crisis → Physician Contact; Pressure
Injury → Wound Supplies. (Baseline findings already captured above in
this document's Action Center Trigger Inventory section.)

**Output:** `SNS_ACTION_CENTER_TRIGGER_INVENTORY_1.0`

### 8. POC Evidence Mapping

**Purpose:** Validate Finding → Problem → Goal → Intervention and confirm
every proposed POC item has source evidence. Aligns with the approved POC
Evidence Requirement in `SNS_RNICA_MASTER_MAP_1.0.md` and hospice
documentation expectations for patient-specific evidence.

**Output:** `SNS_POC_EVIDENCE_MAPPING_1.0`

### 9. Migration Complexity Ratings

**Purpose:** Classify migration effort per field/workflow:

- **LOW** — existing field, reuse
- **MEDIUM** — field exists but needs rewrite
- **HIGH** — new workflow required
- **CRITICAL** — database + API + UI redesign

**Output:** `SNS_MIGRATION_COMPLEXITY_RATINGS_1.0`

### 10. Implementation Gap Report (Recommended Addition)

**Purpose:** Compare Approved Architecture vs. Current RNICA. Status:
Implemented, Partial, Missing, Deprecated. Must explicitly include the
high-risk HOPE items already identified above: J2050-J2053, J0905-J0910,
J2030-J2040, N0500-N0520, M1195-M1200, F3000.

**Output:** `SNS_IMPLEMENTATION_GAP_REPORT_1.0`

### Deliverable Numbering (Current)

The canonical numbering for the remaining inventory work, reconciled with
what has already shipped in this document:

1. Field Inventory — `SNS_RNICA_FIELD_INVENTORY_1.0` — **pending, next up**
2. Database Mapping — `SNS_RNICA_DATABASE_MAPPING_1.0` — pending
3. API Mapping — `SNS_RNICA_API_MAPPING_1.0` — pending
4. Validation Inventory — `SNS_RNICA_VALIDATION_INVENTORY_1.0` — pending
5. Narrative Source Inventory — `SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0` — pending
6. HOPE Crosswalk — **Architecture Complete** (this document, above)
7. Audit Crosswalk — `SNS_RNICA_AUDIT_CROSSWALK_1.0` — baseline captured (this document, above); full field-level version pending
8. Action Center Trigger Inventory — `SNS_ACTION_CENTER_TRIGGER_INVENTORY_1.0` — baseline captured (this document, above); full trigger-mapping version pending
9. POC Evidence Mapping — `SNS_POC_EVIDENCE_MAPPING_1.0` — pending
10. Migration Complexity Ratings — `SNS_MIGRATION_COMPLEXITY_RATINGS_1.0` — pending

Note: the Recommended Execution Order below sequences Audit Crosswalk (7)
and Action Center Trigger Inventory (8) after Narrative Source Inventory
(5) because their baseline findings are already captured, but their
full field-level versions depend on Field Inventory (1) being complete
first — hence the Dependency Chain below runs 1→2→3→4→5→7→8→9→10 with 6
already done.

### Dependency Chain

```
Field Inventory (1)
      ↓
Database Mapping (2)
      ↓
API Mapping (3)
      ↓
Validation Inventory (4)
      ↓
Narrative Source Inventory (5)
      ↓
Audit Crosswalk (7)
      ↓
Action Center Trigger Inventory (8)
      ↓
POC Evidence Mapping (9)
      ↓
Migration Complexity Ratings (10)
```

Every remaining inventory artifact depends on Field Inventory (1) being
complete first, since Database/API/Validation/Narrative/Audit/Action
Center/POC Evidence mappings all key off the field catalog it produces.

### Recommended Next Step: Deliverable #1 — Field Inventory

**Output:** `SNS_RNICA_FIELD_INVENTORY_1.0`

**Scope — for every RNICA field, capture:**

- Field Name
- Section
- Subsection
- Field Type
- Required / Optional
- Source System
- HOPE Dependency
- POC Dependency
- Narrative Dependency
- Action Center Dependency
- Audit Requirement
- Current Implementation Status

**Priority Field Review Order** (sections that drive hospice eligibility,
POC generation, and narrative generation, reviewed first):

**Priority 1 — Section 4, Functional & Performance Status.** Highest
impact on eligibility, recertification, narrative, POC generation, and
LCD support. Inventory fields: PPS, KPS, FAST, NYHA, ECOG; Eating,
Bathing, Dressing, Transfer, Ambulation, Continence; Strength, Endurance.
These are core decline indicators used throughout hospice eligibility and
prognosis support. **Start here — everything else depends on it.**

**Priority 2 — Section 2, Immediate Needs & Symptom Triage.** Inventory
fields: Pain, Dyspnea, Anxiety, Agitation, Nausea, Vomiting, Secretions,
Bleeding, Acute Distress, Current Interventions, Response. These drive
symptom management and many initial POC recommendations.

**Priority 3 — Section 5, Respiratory.** Inventory fields: Dyspnea,
Oxygen, Pulse Ox, Breath Sounds, Secretions, Cough, Nebulizer Use.
Respiratory decline and dyspnea are significant hospice indicators.

**Priority 4 — Section 5, Nutrition / Hydration.** Inventory fields:
Weight, Weight Change, Appetite, Intake, Hydration, Dysphagia,
Supplements. Nutritional decline and weight loss are major hospice
documentation elements.

**Priority 5 — Section 5, Integumentary.** Inventory fields: Skin
Assessment, Pressure Injury, Stage, Drainage, Wounds, Skin Tears,
Bruising, Rashes, Treatments. Pressure injuries and skin breakdown
support both care planning and terminal-status documentation.

**Priority 6 — Infection.**

**Priority 7 — Disease-Specific Criteria.**

**Priority 8 — Whole Person & Caregiver.**

This sequence aligns with documentation of decline, ADL dependency,
symptom burden, nutritional status, infections, skin integrity, disease
progression, and terminal prognosis support emphasized in hospice
eligibility and documentation guidance.

### Governance Status

```
SNS_DESIGN_SYSTEM_1.0            — Complete
SNS_POC_GENERATION_MATRIX_1.0    — Complete
SNS_RNICA_MASTER_MAP_1.0         — Complete
SNS_HOPE_CROSSWALK_1.0           — Architecture Complete

NEXT: SNS_RNICA_FIELD_INVENTORY_1.0
```

No code changes should occur until the Field Inventory is complete and
reviewed, consistent with the governance rule that architecture and
inventory are completed before implementation begins. Each numbered
deliverable requires its own explicit approval to begin, consistent with
this document's Governance Freeze.
