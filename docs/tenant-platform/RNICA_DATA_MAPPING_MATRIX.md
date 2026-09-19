# RNICA Data Mapping Matrix

Companion to `RNICA_IMPLEMENTATION_AUTHORITY.md` and
`RNICA_SCREEN_AUTHORITY_MATRIX.md`. Maps each screen's data to the
frontend API call and backend model/table that produces or consumes it.
Answers "where does this field actually read from and write to."

STATUS: IMPLEMENTATION DOCUMENTATION. CODE/SCHEMA/MIGRATIONS BLOCKED.

Legend: same as `RNICA_IMPLEMENTATION_AUTHORITY.md`.
**[IMPLEMENTATION DISCOVERY REQUIRED]** marks a mapping not directly
re-verified at the column level during this pass — engineering must
confirm before building against it.

---

## Core RNICA Assessment API (`sns-emr-frontend/src/api/icaAssessments.js`)

**[REPOSITORY-DISCOVERED]** confirmed via `RNICA.jsx` imports
(`src/components/RNICA.jsx` lines ~40-65). This is the single API module
backing nearly every RNICA screen's read/write of the assessment record
itself.

| Function | Purpose | Screens using it |
|---|---|---|
| `saveRnicaAssessment` / `updateRnicaAssessment` | Create/update the full assessment JSON document | All 13 screens (each screen writes its own module's slice) |
| `getRnicaAssessment` / `getRnicaAssessmentByPatient` / `getRnicaAssessmentByPatientType` | Load the assessment record | All screens on page load |
| `lockRnicaAssessment` | Executes Finalization Lock | Screen 13 |
| `deleteRnicaAssessment` | Deletes an assessment | Not screen-facing (admin/cleanup path) |
| `getRnicaIntelligence` | Fetches AI/Intelligence advisory output | Screen 1 (RNICA Intelligence panel), Screen 12 (AI Action Center) |
| `getRnicaFinalizationReadiness` | Fetches the aggregated readiness/blocker list | Screen 11, Screen 13 |
| `viewRnicaSectionPoc` / `addRnicaSectionPocProblem` / `updateRnicaSectionPocProblem` / `resolveRnicaSectionPocProblem` / `viewRnicaAllPoc` / `deactivateRnicaSectionPocProblem` / `getRnicaSectionPocProblemHistory` / `linkExistingRnicaSectionPocProblem` / `mergeRnicaPocDuplicateProblems` | Section-linked POC problem CRUD | Screen 10 (and any screen with a POC-linked finding) |
| `requestRnicaCorrection` / `listRnicaAmendments` / `approveRnicaAmendment` / `denyRnicaAmendment` | Post-Lock amendment workflow | Screen 13 (post-Lock state only) |
| `getStructuredFindingsAnalytics` | Structured-findings/AI analytics | Screen 12 |
| `getRnProductivityMetrics` | RN productivity reporting | Not screen-facing (management reporting) |

**[IMPLEMENTATION DISCOVERY REQUIRED]** The exact backend model/table
backing the assessment JSON document (e.g., a single JSONB column vs.
normalized per-module tables) was not re-verified in this pass. Engineers
must confirm the persistence model before mapping individual screen
fields to columns.

## Screen-by-Screen Data Sources

### Screen 1 — Patient Story
- `fetchPatientSummary` (`api/patientCharts.js`) — `[REPOSITORY-DISCOVERED]`
- `fetchCensusWorkspace` (`api/census.js`) — `[REPOSITORY-DISCOVERED]`
- `fetchFacesheet` (`api/facesheet.ts`) → `backend/app/models/patient_facesheet.py` — `[REPOSITORY-DISCOVERED]`
- `getRnicaIntelligence` — RNICA Intelligence panel — `[REPOSITORY-DISCOVERED]`

### Screen 2 — Evidence & Intake
- Referral/intake data — `[IMPLEMENTATION DISCOVERY REQUIRED]` exact
  endpoint not re-verified this pass; likely
  `backend/app/services/admission/admission_service.py` per
  `PATIENT_CHART_AUTHORITY_MAP.md`.
- Evidence harvesting output — `backend/app/services/evidence/ai_extraction_service.py`,
  `structured_findings.py` — `[REPOSITORY-DISCOVERED]`

### Screen 3 — Functional Status
- `performanceStatus.*` fields — core RNICA assessment document — `[REPOSITORY-DISCOVERED]`
- `fetchPerformanceHistory` (`api/facesheet.ts`) → `GET /patients/{id}/performance-history`
  (`backend/app/api/patients.py:4022-4062`) — aggregates PPS/KPS/FAST only
  (not ECOG/NYHA) — `[REPOSITORY-DISCOVERED]`
- Diagnosis-gating for FAST/ECOG/NYHA visibility — `diagnosesIncludeCategory()`
  in `RNICA.jsx` (`~2496-2565`), backed by `HOPE_COMORBIDITY_CATEGORIES`
  (ICD-10 regex) and `SCALE_GATING_KEYWORDS` (free-text fallback) — `[REPOSITORY-DISCOVERED]`
- Backend compliance-blocking for FAST/NYHA — `DEMENTIA_DIAGNOSIS_KEYWORDS` /
  `CARDIAC_DIAGNOSIS_KEYWORDS` in `clinical_note_validation_engine.py:114-190`,
  applied at `:1112-1121, 1234-1320` — `[REPOSITORY-DISCOVERED]`
- ECOG: no backend compliance path found — `[OPEN DEFECT]`, restated

### Screen 4 — Pain & Symptom Burden
- `pain.*`, `symptomImpact.*` fields — core RNICA assessment document — `[REPOSITORY-DISCOVERED]`
- HOPE J0900/J0915 (pain) and J2051 A-H (symptom impact) mappings —
  `SYMPTOM_IMPACT_CHECKLIST` in `RNICA.jsx`, `intake/hopeReportMapper.js` — `[REPOSITORY-DISCOVERED]`

### Screen 5 — Diagnosis & LCD
- `diagnoses.*` fields — core RNICA assessment document — `[REPOSITORY-DISCOVERED]`
- Diagnosis records — `backend/app/models/patient_diagnosis.py`,
  surfaced via `fetchFacesheet` clinical block (`FacesheetDiagnosis` type
  in `api/facesheet.ts`) — `[REPOSITORY-DISCOVERED]`
- LCD detection/evaluation — `detectLCD`, `evaluateLCD`, `getLCDConfig`
  (`api/eligibility.js`) — `[REPOSITORY-DISCOVERED]`
- `buildClientLcdFacts()` (`RNICA.jsx:~1477-1513`) feeds PPS/KPS/NYHA/FAST
  into LCD evaluation; ECOG is not an LCD input — `[REPOSITORY-DISCOVERED]`
- `finalization.clinicalNarrative` is NOT read/written from this screen — `[LOCKED PRODUCT DECISION]`

### Screen 6 — Body Systems
- Ten body-system module fields — core RNICA assessment document,
  `RNICA_BODY_SYSTEM_MODULES` config (`config/bodySystems.js`) — `[REPOSITORY-DISCOVERED]`
- Structured findings extraction — `structured_findings.py` `CONCEPT_REGISTRY` — `[REPOSITORY-DISCOVERED]`
- SFV/Imminent Death backing fields — `[IMPLEMENTATION DISCOVERY REQUIRED]`

### Screen 7 — Caregiver & Support
- `psychosocial`, `spiritual`, `bereavement`, `personalCare`,
  `teachingNeeds` modules — core RNICA assessment document — `[REPOSITORY-DISCOVERED]` (module names confirmed in `RNICA.jsx` module list)
- Caregiver-specific backing fields beyond module presence — `[IMPLEMENTATION DISCOVERY REQUIRED]`

### Screen 8 — Safety & Clinical Risk
- `safety`, `imminentDeath`, `sfv` modules — core RNICA assessment
  document — `[REPOSITORY-DISCOVERED]` (module names confirmed in `RNICA.jsx`)
- Fall risk / Morse score backing field — `[IMPLEMENTATION DISCOVERY REQUIRED]`

### Screen 9 — ACP & Goals of Care
- `advancedCarePlanning.codeStatus`, `.lifeSustainingTreatmentPreference`,
  `.hospitalizationPreference` — core RNICA assessment document — `[REPOSITORY-DISCOVERED]`
  (`clinical_note_validation_engine.py:436-458`)
- HOPE F2000/F2100/F2200-series mapping — cited in
  `RNICA_WORKFLOW_AUTHORITY_MAP.md`; specific field-to-HOPE-item mapping — `[IMPLEMENTATION DISCOVERY REQUIRED]`

### Screen 10 — Orders & POC
- `admissionsOrder` module — core RNICA assessment document — `[REPOSITORY-DISCOVERED]`
- POC problems — `viewRnicaSectionPoc`/`addRnicaSectionPocProblem`/etc. (above) — `[REPOSITORY-DISCOVERED]`
- POC model — `backend/app/models/poc.py`, `plan_of_care.py`,
  `plan_of_care_version.py`, `poc_physician_approval.py` — `[REPOSITORY-DISCOVERED]`
- Physician Orders — `listPhysicianOrders`, `createPhysicianOrder`,
  `submitPhysicianOrder`, `approvePhysicianOrder`, `executePhysicianOrder`,
  `cancelPhysicianOrder` (`api/physicianOrders.js`) →
  `backend/app/models/physician_order.py` — `[REPOSITORY-DISCOVERED]`
- CHHA readiness — `listAideVisitsForPatient`, `getChhaVisitOutcome`,
  `upsertChhaVisitOutcome` (`api/chhaVisits.js`) →
  `backend/app/models/chha_visit_outcome.py` — `[REPOSITORY-DISCOVERED]`

### Screen 11 — Compliance & Readiness
- `getRnicaFinalizationReadiness` — mirrors
  `ValidationResult.compliance_blocking_items` from
  `validate_and_trigger_incident` (`clinical_note_validation_engine.py`) — `[REPOSITORY-DISCOVERED]`
- `referrals.reviewed` — `[REPOSITORY-DISCOVERED]`, restated from Screen 2

### Screen 12 — AI Action Center
- `getRnicaIntelligence`, `getStructuredFindingsAnalytics` — `[REPOSITORY-DISCOVERED]`
- Refresh trigger: Load, Save, Lock only — `[REPOSITORY-DISCOVERED]`,
  screenshot-confirmed ("AI analysis last refreshed... Note: updates on
  Load, Save, and Lock")
- Rules-engine implementation module — `[IMPLEMENTATION DISCOVERY REQUIRED]`
  (this pass did not re-open the rules-engine implementation file; prior
  session discovery referenced `rnica_intelligence.py` as having zero
  performance-scale references, but did not fully map every AI Action
  Center card to a specific rule function)

### Screen 13 — Finalization
- `finalization.clinicalNarrative` — core RNICA assessment document — `[REPOSITORY-DISCOVERED]`
  (`clinical_note_validation_engine.py:398-406`)
- `lockRnicaAssessment` — executes Lock, re-runs
  `validate_and_trigger_incident` server-side — `[REPOSITORY-DISCOVERED]`
- Signature/attestation fields — `[IMPLEMENTATION DISCOVERY REQUIRED]`
  exact backend columns not re-verified this pass
- Post-Lock amendment path — `requestRnicaCorrection`, `listRnicaAmendments`,
  `approveRnicaAmendment`, `denyRnicaAmendment` — `[REPOSITORY-DISCOVERED]`

---

## Known Data Gaps (do not silently fill these at implementation time)

1. **[OPEN DEFECT]** Historical records with `diagnoses.clinicalNarrative`
   present and `clinicalNarrativeReviewed=false` may block Lock with no
   reachable UI control to review/correct — see
   `RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md` (not reopened,
   restated here only as a pointer).
2. **[OPEN DEFECT]** ECOG has no backend Lock-blocking path even when a
   qualifying oncology diagnosis is documented, unlike FAST/NYHA.
3. **[IMPLEMENTATION DISCOVERY REQUIRED]** Fall Risk / Morse score has no
   confirmed entry in `RN_ICA_REQUIRED_FIELD_GROUPS` despite appearing as
   a prominent screenshot field ("High Risk (Score: 18/25)") — confirm
   whether this is validated elsewhere (e.g., a separate safety-specific
   validator not covered by this pass) before assuming it is unvalidated.
4. **[IMPLEMENTATION DISCOVERY REQUIRED]** The exact backend column/table
   for SFV (Supportive Care Plan) documentation, referenced as a hard
   Lock blocker in the Finalization screenshot, was not re-verified at
   the column level this pass.
