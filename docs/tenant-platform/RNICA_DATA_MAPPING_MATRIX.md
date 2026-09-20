# RNICA_DATA_MAPPING_MATRIX.md

**Status:** v2 — repository-validated. Supersedes v1 (commit `7836ca1`).
**Purpose:** Field-level implementation worksheet.
**Rule:** For the ~300-field granular inventory, this document points to the
existing, already-committed, field-level authoritative sources rather than
duplicating them (duplicating ~300 rows here would create a second,
divergent copy of the same fact). Those sources are read-only references,
not superseded by this package:

- `docs/SNS_RNICA_FIELD_INVENTORY_1.0.md` — field name/type/requiredness/source
- `docs/SNS_RNICA_API_MAPPING_1.0.md` — field/section → backend endpoint
- `docs/SNS_RNICA_DATABASE_MAPPING_1.0.md` — field/section → ORM model/table
- `docs/SNS_RNICA_VALIDATION_INVENTORY_1.0.md` — validation rule catalog
- `docs/SNS_RNICA_HOPE_CROSSWALK_VERIFICATION_2.0.md` — HOPE item crosswalk
- `docs/SNS_RNICA_AUDIT_INVENTORY_1.0.md` — audit event catalog
- `RNICA_COMPLETION_MATRIX.md` (repo root) — 556-row per-field completion status

**Known staleness warning:** `docs/RNICA_COMPLETION_LEDGER.md` (an earlier,
already-committed document) claims "no amendment workflow", "no audit
trail", and "no ClinicalNarrative model" exist. Direct repository
verification this pass **contradicts** those claims: amendment workflow
(`rnica_amendment.py`, `rnica_amendment_service.py`), Lock-time audit
logging (`_safe_log_event`, `RNICA_ASSESSMENT_LOCKED`), and
`finalization.clinicalNarrative` (a JSONB field, not a dedicated ORM model)
are all confirmed present in current code. Treat that ledger as historical
(reflects an earlier point in development), and treat this document plus
direct grep/view of current code as authoritative for "is it built today."

## Cross-cutting mechanisms (fully verified this pass, not placeholders)

| Mechanism | Canonical path | Type | Confirmed behavior | Citation |
|---|---|---|---|---|
| Autosave | `useAssessmentAutosave` hook | interval timer | 30000ms (30s) interval; dirty-check via `JSON.stringify` comparison against last-persisted payload; skipped if `locked`, `saving`, or already mid-autosave; failures are `console.warn`-only (no user-facing surface) | `src/hooks/useAssessmentAutosave.ts:1-153` |
| Lock | `POST /visits/rnica/{id}/lock` | API + server validation | Idempotent re-lock (no re-validation, no duplicate audit); otherwise re-runs `evaluate_finalization_readiness`; 400 with `unmetChecks` if not ready; sets `locked/status/locked_at`; syncs HOPE fields; emits `RNICA_ASSESSMENT_LOCKED` audit event | `backend/app/api/visits.py:1178-1250` |
| Locked-record edit protection | `PUT`/`DELETE /visits/rnica/{id}` | HTTP 423 | Both routes reject with 423 and point to the correction-request endpoint | `visits.py:1109-1115, 1164-1169` |
| `status` reset defect | `record.status` | ORM field | Set to `"DRAFT"` unconditionally on every non-locked `PUT`, including trivial autosave ticks — confirmed still present | `visits.py:1118` |
| Amendment | `finalization.*` correction records | API + model | `requestRnicaCorrection` / `listRnicaAmendments` / `approveRnicaAmendment` / `denyRnicaAmendment` | `src/api/icaAssessments.ts`; `backend/app/models/rnica_amendment.py`; `backend/app/services/rnica_amendment_service.py` |
| POC adapter | `poc_problems` (authoritative POC domain, not duplicated in RNICA) | API adapter | `viewRnicaSectionPoc`/`addRnicaSectionPocProblem`/`updateRnicaSectionPocProblem`/`resolveRnicaSectionPocProblem`/`linkExistingRnicaSectionPocProblem`/`mergeRnicaPocDuplicateProblems`/`deactivateRnicaSectionPocProblem`/`viewRnicaAllPoc`; never auto-generated at Lock | `backend/app/api/routes/rnica_poc.py`; `docs/rnica-poc-lock-no-autogen-disposition.md` |
| Structured Findings | `intelligence.structured_findings_signals` | signal review | `reviewHarvestedSignal`/`batchReviewHarvestedSignals`; provenance recorded per applied field (`section, path, value, concept_code, source_type, source_excerpt, recorded_at, confidence, signal_id`); conflicts (RN value vs. AI value) surfaced, never overwritten | `RNICA.jsx` `handleApplyStructuredSignal`; `CONCEPT_REGISTRY` in `structuredFindingRegistry.generated.js` |
| LCD evidence | `diagnoses.ndsEligibility.*` | client facts → server eval | `buildClientLcdFacts(formData)` builds a facts object from `performanceStatus`, `nutrition`, `musculoskeletal.adl.*`, `genitourinary`, `gastrointestinal`, `vitals`, `respiratory`; sent to `evaluateLCD()` → `POST /eligibility/lcd-evaluate`. Response is a criteria-match structure, not an eligibility verdict. | `RNICA.jsx` `buildClientLcdFacts`/`buildLcdEvaluationPayload`; `src/api/eligibility.ts:62-87` |
| Intelligence refresh | `intelligence` state | API call | `getRnicaIntelligence`; confirmed triggered on Load and on readiness/refresh actions, not on every keystroke (no effect keyed to `formData` found) | `src/api/icaAssessments.ts`; `RNICA.jsx` |
| HOPE lifecycle | `getSfvStatus`, `getHopeAdmissionStatus` | derived state | Client-side derivation from `form_data`; server-side sync at Lock via `rnica_hope_workflow_service.sync_submission_fields_from_form_data` | `src/intake/hopeReportMapper.js`; `backend/app/services/rnica_hope_workflow_service.py`; `visits.py` Lock handler |
| Required-field validation | `RN_ICA_REQUIRED_FIELD_GROUPS` (17 items) | server validator | See `RNICA_LOCK_READINESS_MATRIX.md` for the full table | `backend/app/services/clinical_note_validation_engine.py:380-517` |

## Per-screen mapping status

| Screen | Legacy module(s) consumed | Field-level detail source | Confirmed gaps this pass |
|---|---|---|---|
| 1. Patient Story | `demographics`, `diagnoses`, `performanceStatus`, `psychosocial`, `bereavement`, `intelligence` | `SNS_RNICA_FIELD_INVENTORY_1.0.md` | No aggregation component exists; presentation-only build required |
| 2. Evidence & Intake | `demographics`, `vitals`, `referrals` + structured findings pipeline | same + `SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0.md` | No dedicated screen; fields currently interleaved |
| 3. Functional Status | `performanceStatus` | same + `SNS_RNICA_HOPE_CROSSWALK_VERIFICATION_2.0.md` | ECOG has no server enforcement |
| 4. Pain & Symptom Burden | `pain`, `symptomImpact` | same | HOPE J2050/J2051 wiring defects previously logged in `RNICA_COMPLETION_LEDGER.md` — not re-verified this pass, carry forward as `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| 5. Diagnosis & LCD | `diagnoses` (incl. `ndsEligibility`) | same + `src/api/eligibility.ts` | none confirmed this pass beyond terminology-language enforcement (see AI Governance) |
| 6. Body Systems | `RNICA_BODY_SYSTEM_MODULES` (10 systems) + `imminentDeath`, `sfv` | `SNS_RNICA_DATABASE_MAPPING_1.0.md` | RN ICA skips generic ROS validator (`_validate_required_ros`); 43 previously-catalogued auto-populatable structured-findings gaps in `RNICA_CERTIFICATION_PACKAGE.md` — not re-verified this pass, carried forward as historical reference only |
| 7. Caregiver & Support | `psychosocial`, `spiritual`, `bereavement`, `personalCare`, `teachingNeeds` | `SNS_RNICA_FIELD_INVENTORY_1.0.md` | none confirmed this pass |
| 8. Safety & Clinical Risk | `safety`, `imminentDeath` | same | Fall Risk/Morse Lock-blocking status unconfirmed |
| 9. ACP & Goals of Care | scattered across `demographics`/`diagnoses` (no dedicated module) | same + `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md` | **Resolved this pass:** target is 6 fields (3 Preference + 3 paired Discussion Status); all 6 already exist in `form_data` (`demographics.advancedCarePlanning.{codeStatus, lifeSustainingTreatmentPreference, hospitalizationPreference, cprPreferenceAskedStatus, lifeSustainingAskedStatus, hospitalizationAskedStatus}`); server enforces only the 3 Preference fields today; HOPE-vs-SNS-internal labeling and response-set integrity still `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| 10. Orders & POC | POC adapter (see cross-cutting table) | `SNS_POC_EVIDENCE_INVENTORY_1.0.md`, `SNS_POC_GENERATION_MATRIX_1.0.md` | none confirmed this pass |
| 11. Compliance & Readiness | `getRnicaFinalizationReadiness` | `RNICA_LOCK_READINESS_MATRIX.md` | none confirmed this pass |
| 12. AI Action Center | `getRnicaIntelligence`, `CONCEPT_REGISTRY` | `RNICA_AI_GOVERNANCE.md` | no dedicated audit event for AI-recommendation apply/dismiss confirmed |
| 13. Finalization | `finalization` module, Lock, Amendment | `RNICA_LOCK_READINESS_MATRIX.md` | `status`-reset-to-`DRAFT` defect |

## Mapping acceptance rules (unchanged from v1)

- No blank authority-owner cell.
- No UI field without a canonical source or explicit future-direction marker.
- No derived field without a documented rule and test.
- No required field without both client and server behavior documented.
- No lock dependency without an exact server check.
- No HOPE item without an official version/reference recorded.
- No legacy field may be deleted or overwritten without approved migration
  and historical-data plan.
