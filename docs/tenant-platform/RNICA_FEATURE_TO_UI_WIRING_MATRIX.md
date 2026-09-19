# RNICA Feature-to-UI Wiring Matrix

**STATUS: PLANNING / DISCOVERY ONLY — NO CODE — NO SCHEMA — NO MIGRATIONS**

This matrix inventories every required RNICA-adjacent feature: where it
lives in the repository, whether the backend exists, whether the frontend
surfaces it, who consumes it, and whether it is safe to visually redesign.
It is grounded in `RNICA_SYSTEM_DEPENDENCY_MAP.md`,
`RNICA_UI_DEPENDENCY_MAP.md`, and `RNICA_USABILITY_AND_AI_REVIEW.md` (all
in this directory); no new claims are made beyond what those documents
already cite, plus a small number of explicitly marked new observations
below.

Classification values used (as requested), plus one explicit addition for
capabilities that do not exist anywhere in the repository:
**WIRED**, **PARTIALLY WIRED**, **BACKEND ONLY**, **FRONTEND ONLY**,
**UNKNOWN**, and **NOT FOUND / NOT BUILT** (added because several requested
features — e.g. CTI, F2F, Patient Story — have no repository evidence at
all, which is a distinct condition from "backend exists but isn't wired").

---

| Feature | Repository Location | Backend Status | Frontend Status | Current UI Location | Consumer | Trigger | Output | Visible To Nurse | Visible To AI Panel | Visible To Billing | Visible To Compliance | Classification | Safe To Redesign |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RNICA Intelligence | `backend/app/services/rnica_intelligence.py:57-222`; `backend/app/api/visits.py:1657-1678`; `RNICA.jsx:11791-11829` | Exists (rules engine, not ML) | Exists | "RN ICA Intelligence" sidebar panel | Clinician | Load + Save + Lock (`RNICA.jsx:10917-10921,11024,11069-11071`) | summary/findings/recommendations/missing_evidence | Yes | Yes (is the panel) | No | No | **WIRED** (but see AI_VISIBILITY_MATRIX for timing issues) | Visual: YES / Data contract: NO |
| Structured Findings | `backend/app/services/evidence/structured_findings.py:1928-2135`; `applyStructuredFindings` (`RNICA.jsx:69,10072`) | Exists | Exists, manual-trigger only | "Build Draft from Documented Findings" button (`RNICA.jsx:2009,2106`) | Clinician | Explicit click | Draft narrative text / field application | Yes, but easy to miss | Feeds Intelligence input | No | No | **WIRED** | Visual: YES / Trigger mechanism: NO |
| Validation Engine | Client: `validateRNICA` (`RNICA.jsx:942-1102`); Server: `backend/app/services/clinical_note_validation_engine.py:380-470,934-970` | Exists | Exists (duplicated client+server) | Inline field errors/warnings + lock-time alerts | Clinician | On change (client) / on lock (server) | errors/warnings maps | Yes | No | No | Yes | **WIRED** | Visual: YES / Field set: NO |
| HOPE Generator (submission/export workflow) | `backend/app/services/rnica_hope_workflow_service.py:1-21,42-68,103-195`; `backend/app/api/visits.py:1382-1479` | Exists | Exists | HOPE status/action controls in RNICA UI | HOPE submission batch pipeline | Manual action (ready/close/submit) | HOPE lifecycle state transitions | Yes | No | No | Yes | **WIRED** | Visual: YES / Actions & terminology: NO |
| HOPE Mapping (field→HOPE code tagging) | `HopeTag` component (`RNICA.jsx:1128-1138`); `hope: [...]` arrays throughout `SIDEBAR_CONFIG`/`bodySystems.js` | Exists | Exists | Inline "HOPE ####" tags next to fields | Clinician (visual reference only) | Static render | HOPE code label | Yes | No | No | Yes | **WIRED** | Visual: YES / Code mapping: NO |
| CTI Logic (Certification of Terminal Illness) | **NOT FOUND** in RNICA layer | Not found | Not found | None | — | — | — | No | No | Unknown | Unknown | **NOT FOUND / NOT BUILT** | N/A — nothing exists to protect or redesign |
| F2F Logic (Face-to-Face) | **NOT FOUND** in RNICA layer | Not found | Not found | None | — | — | — | No | No | Unknown | Unknown | **NOT FOUND / NOT BUILT** | N/A |
| IDG Logic | **NOT FOUND** direct link; only generic assessment-history/dashboard reads (`backend/app/services/assessment_history_service.py:90-125`) | Partial (generic only) | Not found (RNICA-specific) | None RNICA-specific | Dashboards/history views | Passive read | Serialized assessment record | Indirect only | No | No | Indirect only | **BACKEND ONLY** (generic, not IDG-specific) | N/A |
| POC Logic | `backend/app/services/rnica_poc_adapter.py:1-668`; `backend/app/api/routes/rnica_poc.py:186-538` | Exists | Exists | POC-linked actions/sections in RNICA UI | POC record, finalization readiness | Explicit action (sync/add order) | POC problems/goals/interventions | Yes | No | No | Yes (finalization gate) | **WIRED** | Visual: YES / Adapter contract: NO |
| HUV Logic | `backend/app/services/hope_phase_b_engine.py:24-33,167-181,277-293` (shared HOPE engine, not RNICA-specific) | Exists (shared) | Not found (no RNICA-specific HUV UI surface) | None specific to RNICA | HOPE workflow engine | Workflow-driven | HOPE visit-type state | No (not RNICA-surfaced) | No | No | Indirect | **BACKEND ONLY** | N/A — no RNICA-specific surface exists |
| SFV Logic | `backend/app/models/sfv_requirement.py:19,65`; SFV nav section + trigger banner (`RNICA.jsx:11393`) | Exists | Exists | "SFV" nav section + trigger banner | Clinician | Symptom-threshold-driven | SFV requirement flag | Yes | No | No | Yes | **WIRED** | Visual: YES / Trigger logic: NO |
| Billing Readiness | `backend/app/billing/services/billing_readiness_service.py:1-23` | Exists, entirely separate | Not found (no RNICA UI surface) | None | Billing platform only | N/A | Billing readiness state | No | No | Yes (elsewhere) | No | **BACKEND ONLY — NOT CONNECTED TO RNICA** | N/A — nothing to protect in RNICA since no link exists |
| Survey Readiness | **NOT FOUND** anywhere in RNICA layer | Not found | Not found | None | — | — | — | No | No | Unknown | Unknown | **NOT FOUND / NOT BUILT** | N/A |
| Compliance Review (dedicated QA/QAPI) | **NOT FOUND** beyond generic dashboard/audit-log consumption (`backend/app/services/dashboard_service.py:1147-1152`) | Partial (generic only) | Partial (generic dashboards only) | Owner/Tenant dashboards, not RNICA-specific | QA/compliance dashboards | Passive read | Counts (unlocked RNICA, etc.) | Indirect only | No | No | Indirect only | **BACKEND ONLY** (generic) | N/A |
| Patient Story | **NOT FOUND** — no dedicated service/model in the repository | Not found | Not found | None | — | — | — | No | No | No | No | **NOT FOUND / NOT BUILT** | N/A — this is new scope, not existing functionality |
| Evidence Harvesting | `gather_patient_evidence(...)` / `list_pending_structured_findings(...)` (`backend/app/api/visits.py:1657-1676`) | Exists | Exists (feeds Intelligence panel) | Embedded in Intelligence panel's "evidence" output | Clinician (indirectly, via Intelligence) | On Intelligence refresh | Evidence bundle | Indirect (not separately labeled) | Yes (is an input) | No | No | **WIRED but not independently surfaced** | Visual: N/A (no standalone surface) |
| Risk Scoring | **NOT FOUND** as a formal score — only rule-based threshold flags exist (`rnica_intelligence.py:70-174`) | Partial (thresholds, not a score) | Partial (renders threshold-derived findings, not a score) | Intelligence panel findings list | Clinician | On Intelligence refresh | Boolean/categorical findings, not a numeric score | Yes | Yes | No | No | **PARTIALLY WIRED** | Visual: YES / Underlying logic: NO |
| Explanation Engine | **NOT FOUND** as a distinct layer separate from finding/recommendation text | Not found | Not found | N/A | — | — | — | No | No | No | No | **NOT FOUND / NOT BUILT** | N/A |
| Recommendation Engine | `rnica_intelligence.py:184-222` (`recommendations` field) | Exists (part of Intelligence engine) | Exists | Intelligence panel recommendations list | Clinician | On Intelligence refresh | Recommendation text list | Yes | Yes (is part of AI panel) | No | No | **WIRED** | Visual: YES / Data contract: NO |
| Caregiver Intelligence | `rnica_intelligence.py:98-156` (caregiver-adjacent recommendation text only; no dedicated caregiver-assessment model link) | Partial (embedded text only) | Partial (renders as generic recommendation, not a labeled caregiver section) | Intelligence panel (unlabeled, mixed with other recommendations) | Clinician | On Intelligence refresh | Caregiver-related recommendation text | Yes, but unlabeled | Yes | No | No | **PARTIALLY WIRED** | Visual: YES (could be labeled) / Data contract: NO |
| Clinical Risk Detection | `rnica_intelligence.py:70-174` (pain, oxygen use, fall risk, delirium, imminent death, psychosocial distress thresholds) | Exists | Exists | Intelligence panel findings | Clinician | On Intelligence refresh | Findings list | Yes | Yes | No | No | **WIRED** | Visual: YES / Threshold logic: NO |
| Medication Intelligence (allergy/interaction) | `RNICA.jsx:6306,6328-6345` | Exists (backend safety-check call, not cited by name here — see medications section) | Exists, live/debounced | Medications section | Clinician | Live, debounced while typing | Allergy/interaction warnings | Yes | No (separate from Intelligence panel) | No | No | **WIRED** — the one genuinely live AI-adjacent feature | Visual: YES / Live-check behavior: NO |
| Diagnosis Intelligence (LCD detect/config/eval) | `RNICA.jsx:1617-1700` | Exists | Exists, sequential 3-step chain | Diagnoses section LCD panel | Clinician | Debounced text change → chained calls | Detected disease → config → eligibility | Yes | No (separate from Intelligence panel) | Indirect (LCD is documentation-only, not a billing computation) | Yes (LCD narrative required for finalization) | **WIRED** — but slow/sequential (see AI_VISIBILITY_MATRIX) | Visual: YES / Chain sequencing: caution |
| Admission Readiness | Admission gating on POC creation (`backend/app/services/rnica_poc_adapter.py:126-153,317-326`); `admission_id` FK (`backend/app/models/rnica_assessment.py:19-28`) | Exists (implicit gating, not a labeled "readiness" feature) | Not found as a distinct labeled UI element | Implicit — surfaces only as an error if admission is missing | POC adapter | On POC action attempt | Block/allow | No (not proactively surfaced) | No | No | No | **PARTIALLY WIRED** (exists as a gate, not a visible readiness indicator) | Visual: YES (could add a proactive indicator) |
| Certification Tracking (CTI) | **NOT FOUND** — only unrelated finalization "signature certification" attestation exists (`backend/app/services/rnica_finalization_service.py:102-109`) | Not found | Not found | N/A | — | — | — | No | No | No | No | **NOT FOUND / NOT BUILT** | N/A |
| Benefit Period Logic | Exists only on `PatientFaceSheet`, not RNICA (`backend/app/models/patient_facesheet.py:201-203`) | Exists elsewhere | Not found in RNICA | N/A (facesheet only) | Facesheet consumers | — | — | No (not RNICA-surfaced) | No | Unknown | Unknown | **BACKEND ONLY (elsewhere, not RNICA-linked)** | N/A |
| Lock Workflow | `backend/app/api/visits.py:1177-1265`; `RNICA.jsx:11028-11051` | Exists | Exists | Lock button + readiness checklist | Clinician | Explicit click | Lock + audit event | Yes | Indirect (re-triggers Intelligence refresh) | No | Yes | **WIRED / DO NOT TOUCH** | Visual: YES / Gate logic: NO |
| Autosave Workflow | `useAssessmentAutosave` hook (used throughout `RNICA.jsx`, e.g. `RNICA.jsx:10545-10553`) | Exists | Exists | Autosave status indicator | Clinician | 30s interval | Persisted draft | Yes | No | No | No | **WIRED** | Visual: YES / Timing: NO |

---

## Summary Counts

- **WIRED**: 15 (Intelligence, Structured Findings, Validation Engine, HOPE Generator, HOPE Mapping, POC Logic, SFV Logic, Evidence Harvesting, Recommendation Engine, Clinical Risk Detection, Medication Intelligence, Diagnosis Intelligence, Lock Workflow, Autosave Workflow, and Billing Readiness's backend — noted separately as not connected)
- **PARTIALLY WIRED**: 3 (Risk Scoring, Caregiver Intelligence, Admission Readiness)
- **BACKEND ONLY**: 4 (IDG Logic, HUV Logic, Compliance Review, Benefit Period Logic) + Billing Readiness (backend only, not connected to RNICA)
- **NOT FOUND / NOT BUILT**: 6 (CTI Logic, F2F Logic, Survey Readiness, Patient Story, Explanation Engine, Certification Tracking)

**No feature in this matrix requires a schema, migration, API, or UI code
change to produce this document. Inventory only.**
