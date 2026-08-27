# SNS RNICA API Mapping 1.0 — Phase 1, Deliverable 3

**STATUS: FROZEN — ACCEPTED COMPLETE (2026-08-21)**
No further edits except factual corrections.

## INVENTORY RULE

This document maps existing fields to their actual current API
implementation (UI → API → Handler → Database → Response). It does not
modify `SNS_RNICA_FIELD_INVENTORY_1.0`, `SNS_RNICA_DATABASE_MAPPING_1.0`,
`SNS_RNICA_MASTER_MAP_1.0`, or `SNS_HOPE_CROSSWALK_1.0`. It does not
propose new endpoints, redesign the API surface, or discuss future
architecture.

Source of truth:
- `sns-emr-frontend/src/components/RNICA.jsx` (form, `validateRNICA()`, API bindings)
- `sns-emr-frontend/src/api/icaAssessments.ts` (frontend API client)
- `backend/app/api/visits.py` (route handlers, lines 751-1027)
- `backend/app/services/rnica_intelligence.py`, `code_status_sync_service.py`, `diagnosis_sync_service.py`, `contact_sync_service.py`, `app/api/patient_allergies.py`

## Output columns

Component | Endpoint | Method | Payload | Response | Auth | Validation | Database Write | Dependencies

---

## 1. Endpoint inventory (current implementation only)

All RNICA endpoints are registered under the `/visits` router
(`backend/app/api/visits.py:666`, `APIRouter(prefix="/visits")`), so the
effective base path is `/visits/rnica`. There is **no separate Pydantic
request/response model** for any RNICA endpoint — every handler accepts
`payload: dict` and returns a hand-built `dict`. Request/response shape
below reflects what the code actually sends/reads, not a declared schema.

| # | Purpose | Method | Endpoint | Frontend caller |
|---|---|---|---|---|
| 1 | Load APIs | GET | `/visits/rnica/{assessment_id}` | `getRnicaAssessment()` |
| 2 | Load APIs (by patient) | GET | `/visits/rnica/by-patient/{patient_id}` | `getRnicaAssessmentByPatient()` |
| 3 | Save API (create) | POST | `/visits/rnica/save` | `saveRnicaAssessment()` |
| 4 | Update API | PUT | `/visits/rnica/{assessment_id}` | `updateRnicaAssessment()` |
| 5 | Sign/Lock API | POST | `/visits/rnica/{assessment_id}/lock` | `lockRnicaAssessment()` |
| 6 | Lookup/Intelligence API | GET | `/visits/rnica/{assessment_id}/intelligence` | `getRnicaIntelligence()` |

There is **no DELETE endpoint** for RNICA assessments (Delete APIs: none
exist in current implementation). There is **no PATCH endpoint** (partial
update) — `update_rnica_assessment` (PUT) always replaces the entire
`form_data` object. There is **no dedicated HOPE API or dedicated POC
API** for RNICA — HOPE items are fields inside the same `form_data`
blob (see Database Mapping §2), and POC generation is not invoked from
any RNICA endpoint in the current code (only the frontend field
`finalization.pocGenerationCompleted` is checked/warned on, per
`validateRNICA()` line 823-825 in `RNICA.jsx`). "Orders APIs" for RNICA
are limited to fields inside `admissionsOrder`/`medications`
(`form_data` paths) — there is no separate orders endpoint invoked by
`RNICA.jsx`.

### 1.1 `POST /visits/rnica/save` — `save_rnica_assessment` (`visits.py:751`)

- **Component:** `RNICA.jsx` save handler → `api.saveRNICAAssessment(patientId, formData)` → `saveRnicaAssessment()` (`icaAssessments.ts:49`).
- **Payload:** `{ "patientId": "<uuid>", "formData": { ...entire form state... } }`.
- **Response:** `{ "assessmentId": "<uuid>", "status": "saved" }`.
- **Auth:** Required. `Security(get_current_user)` (`app/core/security.py:204`) — Bearer JWT, `AUTH_MODE == "TOKEN"` required or the dependency itself raises 503. No RNICA-specific role check in the handler; tenant/assignment scoping is enforced via `get_authorized_patient(db, patient_uuid, current_user)`.
- **Validation:**
  - Backend: `patientId` presence (`422` if missing) and UUID format (`422` if invalid). No validation of `formData` contents at all — any JSON shape is accepted and stored as-is.
  - Frontend: `validateRNICA(formData, mode)` runs client-side before the call is made (`RNICA.jsx:5572`), producing `errors`/`warnings`; only "errors" block the client from proceeding — see Deliverable #4 for the full rule catalogue found in this function (`RNICA.jsx:765-886`).
  - Database: none — `form_data` is JSONB with no CHECK constraints.
- **Database Write:** Inserts one row into `rnica_assessments` (`patient_id`, `tenant_id` copied from the resolved `Patient`, `form_data`, `assessment_type="RNICA"`, `status="DRAFT"`, `locked=False`). Then calls `_sync_facesheet_from_rnica()` and `_sync_shared_records_from_rnica()` (see Dependencies).
- **Dependencies:** `_sync_facesheet_from_rnica` (legacy text mirror → `patient_facesheets`), `_sync_shared_records_from_rnica` → `sync_official_primary_diagnosis`/`sync_secondary_and_comorbidity_diagnoses` (`patient_diagnoses`), `sync_allergies_from_source` (`patient_allergies`), `set_current_code_status` (`patient_code_statuses`), `set_patient_contact` ×3 (`patient_contacts`), direct write to `patient_facesheets.current_level_of_care`. Full field-level detail already recorded in `SNS_RNICA_DATABASE_MAPPING_1.0` §3.
- **Error paths:** `422` — missing/invalid `patientId`; `404` — patient not found or not in caller's tenant (`get_authorized_patient`, raised deliberately as 404 not 403 to avoid existence probing); `403` — user inactive/missing (`get_authorized_patient`); `401`/`503` — auth failures (missing/invalid bearer token, or `AUTH_MODE != "TOKEN"`). No explicit handling of sync-function failures — if any `_sync_*` call raises, it propagates as an unhandled `500` after the primary `rnica_assessments` row is already committed (i.e. the RNICA row can be saved successfully while a downstream sync silently fails or throws after commit).

### 1.2 `GET /visits/rnica/{assessment_id}` — `get_rnica_assessment` (`visits.py:860`)

- **Component:** `RNICA.jsx` load-by-assessment path → `api.getRNICAAssessment(assessmentId)` → `getRnicaAssessment()` (`icaAssessments.ts:53`).
- **Payload:** none (path param only).
- **Response:** `{ "assessmentId", "patientId", "formData", "locked", "createdAt", "updatedAt" }`. `formData` is **not** the raw stored JSONB — it is passed through `_overlay_shared_code_status()` first (see below).
- **Auth:** Required, same as 1.1. Authorization via `get_authorized_patient(db, record.patient_id, current_user)`.
- **Validation:** Backend validates only that `assessment_id` is a UUID (`422` otherwise). No frontend validation occurs on load (validation runs on save/lock, not load).
- **Database Write:** none (read-only).
- **Dependencies:** `_overlay_shared_code_status()` (`visits.py:798-857`) — reads live values from `patient_code_statuses` (via `get_current_code_status`) and `patient_contacts` (via `get_patient_contacts`) and overlays them onto the returned `formData.advancedCarePlanning.{codeStatus,codeStatusDisplayLabel,codeStatusSource,codeStatusEffectiveDate,poaName,poaPhone,decisionMaker}` and `formData.demographics.pcg.{name,relationship,phone}`. **The on-disk `form_data` snapshot is left unmodified** — this overlay only affects what is returned to the caller, so a previously-charted assessment always displays the *current* shared code-status/contact values rather than what was true when it was written.
- **Error paths:** `422` invalid UUID; `404` assessment not found, or patient not found/not in tenant; `403` inactive/missing user; `401`/`503` auth failures.

### 1.3 `GET /visits/rnica/by-patient/{patient_id}` — `get_rnica_assessment_by_patient` (`visits.py:892`)

- **Component:** `RNICA.jsx` initial-load path when opened from a patient context (no existing assessment id) → `api.getRNICAAssessmentByPatient(patientId)` → `getRnicaAssessmentByPatient()` (`icaAssessments.ts:57`).
- **Payload:** none (path param only).
- **Response:** same shape as 1.2, or `{ "assessmentId": null }` if the patient has no RNICA assessments at all.
- **Auth/Validation/Dependencies:** same as 1.2. Selection logic: most recent **unlocked** assessment wins; if all are locked, the most recently created (locked) one is returned (`visits.py:905-911`).
- **Error paths:** `422` invalid UUID; `404` patient not found/not in tenant; `403` inactive/missing user; `401`/`503` auth.

### 1.4 `PUT /visits/rnica/{assessment_id}` — `update_rnica_assessment` (`visits.py:930`)

- **Component:** `RNICA.jsx` save handler when an assessment already exists → `api.updateRNICAAssessment(assessmentId, formData)` → `updateRnicaAssessment()` (`icaAssessments.ts:61`, sends `{ formData }`).
- **Payload:** `{ "formData": { ...entire form state... } }`.
- **Response:** `{ "assessmentId", "status": "updated", "locked" }`.
- **Auth:** Required, same pattern as above. **No explicit `locked` check in the handler** — a locked assessment can still be overwritten by this endpoint at the API layer; enforcement of "don't edit a locked assessment" exists only in the frontend UI, not the backend.
- **Validation:** Backend validates `assessment_id` UUID format only; `formData` defaults to the existing `record.form_data` if omitted, otherwise fully replaces it (no merge, no partial-field patch semantics). Frontend `validateRNICA()` runs the same as 1.1 before calling.
- **Database Write:** `record.form_data = form_data`; `record.status = "DRAFT"` (status is reset to DRAFT on every update, even if it had been advanced). Then the same `_sync_facesheet_from_rnica()` / `_sync_shared_records_from_rnica()` pair as save.
- **Dependencies:** identical sync dependency set as 1.1.
- **Error paths:** `422` invalid UUID; `404` assessment not found or patient not found/tenant mismatch; `403` inactive/missing user; `401`/`503` auth; same unhandled-post-commit sync failure risk as 1.1.

### 1.5 `POST /visits/rnica/{assessment_id}/lock` — `lock_rnica_assessment` (`visits.py:978`)

- **Component:** `RNICA.jsx` "sign/finalize" action → `api.lockRNICAAssessment(assessmentId)` → `lockRnicaAssessment()` (`icaAssessments.ts:65`), called only after `validateRNICA()` reports no `errors` (`RNICA.jsx:5572-5579`).
- **Payload:** none.
- **Response:** `{ "assessmentId", "status": "locked", "locked": true }`.
- **Auth:** Required, same pattern.
- **Validation:** Backend performs **no validation of form completeness at all** — any assessment, regardless of contents, can be locked via a direct call to this endpoint. All completeness/required-field enforcement (signature present, level of care present, T.O. verification, HOPE-required fields, etc.) is frontend-only, inside `validateRNICA()`, gating whether the frontend *chooses* to call this endpoint — it is not re-checked server-side.
- **Database Write:** `record.locked = True`; `record.status = "LOCKED"`; `record.locked_at = now()`. No sync-function calls (diagnoses/allergies/etc. are not re-synced on lock).
- **Dependencies:** none beyond the primary table write.
- **Error paths:** `422` invalid UUID; `404` assessment not found or patient not found/tenant mismatch; `403` inactive/missing user; `401`/`503` auth.

### 1.6 `GET /visits/rnica/{assessment_id}/intelligence` — `get_rnica_intelligence` (`visits.py:1002`)

- **Component:** `RNICA.jsx` insight/summary panel → `api.getRNICAIntelligence(assessmentId)` → `getRnicaIntelligence()` (`icaAssessments.ts:69`), only called when `currentAssessmentId` is truthy (`RNICA.jsx:5459`, `756-757`).
- **Payload:** none (path param only).
- **Response:** JSON object built by `build_rnica_intelligence()` (`rnica_intelligence.py:176-210`): `{ mode: "recommendation_only", patient_id, generated_at, summary: { overall_priority, finding_count, recommendation_count, missing_evidence_count, source_count }, findings: [...], recommendations: [{title, priority}], missing_evidence: [...], evidence: { assessment_text, sections, patient_evidence } }`.
- **Auth:** Required, same pattern.
- **Validation:** none (read-only, derived/computed endpoint).
- **Database Write:** none.
- **Dependencies:** `gather_patient_evidence()` (`app/services/icd_intelligence.py`) — pulls supporting clinical-note/diagnosis evidence text for the patient; `build_rnica_intelligence()` internally calls `_collect_findings()` on the stored `form_data` to derive findings/recommendations/evidence/missing-evidence — this is the closest thing in the current codebase to a "HOPE calculation" or "POC-adjacent" computation reachable from an RNICA endpoint, but it produces read-only recommendation text, not a POC record, and is explicitly labeled `"mode": "recommendation_only"` in its own output.

---

## 2. Per-section field-flow mapping (Sections 1-28)

There is **one save/update endpoint pair for the entire form** — RNICA
has no per-field or per-section API. Every field documented in
`SNS_RNICA_FIELD_INVENTORY_1.0` follows the identical flow below unless
called out as an exception in §3.

**Universal flow (all sections):**
`RNICA.jsx` form state (`formData.<section>.<field>`) → `validateRNICA()` client-side check (only for the specific fields it inspects — see §3.1) → `api.saveRNICAAssessment` / `api.updateRNICAAssessment` → `POST /visits/rnica/save` or `PUT /visits/rnica/{assessment_id}` → `save_rnica_assessment` / `update_rnica_assessment` (`visits.py`) → `rnica_assessments.form_data` (whole-object JSONB write, no per-field validation) → response echoes `assessmentId`/`status` only (not the saved data). On next load: `GET /visits/rnica/{assessment_id}` or `GET /visits/rnica/by-patient/{patient_id}` → `get_rnica_assessment(_by_patient)` → `record.form_data` (optionally overlaid per §1.2) → response `formData`.

| Section | Frontend Source | Endpoint (save/load) | Method | Auth | Validation | Database Write | Dependencies |
|---|---|---|---|---|---|---|---|
| 1 Patient Demographics | `RNICA.jsx` demographics fields | `/visits/rnica/save`, `/visits/rnica/{id}`, `/visits/rnica/by-patient/{id}` | POST/PUT/GET | Y | Frontend: firstName/lastName/dob/gender required; HOPE A1110/A1005/A1010 warnings; ACP codeStatus/F2100/F2200 required (errors); PCG assessed/willingness/capability warnings — see §3.1 | `rnica_assessments.form_data` | Code Status → `patient_code_statuses`; PCG/DPOA/Decision Maker → `patient_contacts`; overlay on GET (§1.2) |
| 2 Vitals (+ IV) | `RNICA.jsx` vitals fields | same | POST/PUT/GET | Y | none in `validateRNICA()` | `rnica_assessments.form_data` | none |
| 3 Pain Assessment | `RNICA.jsx` pain fields | same | POST/PUT/GET | Y | HOPE J0900/J0915 warnings | `rnica_assessments.form_data` | none |
| 4 Symptom Impact | `RNICA.jsx` symptomImpact fields | same | POST/PUT/GET | Y | HOPE J2051 A-H warnings (8 fields) | `rnica_assessments.form_data` | none |
| 5 Diagnoses | `RNICA.jsx` diagnoses fields | same | POST/PUT/GET | Y | HOPE I0010 primary ICD-10 required (error) | `rnica_assessments.form_data` | Primary/secondary/comorbidity → `patient_diagnoses`; legacy mirror → `patient_facesheets` |
| 6 Performance Status | `RNICA.jsx` performanceStatus fields | same | POST/PUT/GET | Y | HOPE M1190 (PPS or KPS) warning | `rnica_assessments.form_data` | none |
| 7 Neurological (+ Sleep/Rest) | `RNICA.jsx` neurological fields | same | POST/PUT/GET | Y | HOPE N0500 (BIMS) warning | `rnica_assessments.form_data` | none |
| 8 Cardiovascular | `RNICA.jsx` cardiovascular fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 9 Respiratory (+ O2) | `RNICA.jsx` respiratory fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 10 Infection | `RNICA.jsx` infection fields (incl. allergies) | same | POST/PUT/GET | Y | none in `validateRNICA()` | `rnica_assessments.form_data` | Allergies → `patient_allergies`; legacy mirror → `patient_facesheets` |
| 11 Gastrointestinal (+ Feeding Tube, Ostomy) | `RNICA.jsx` gastrointestinal fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 12 Nutrition (+ Dentures) | `RNICA.jsx` nutrition fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 13 Endocrine | `RNICA.jsx` endocrine fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 14 Genitourinary (+ Catheter, Reproductive) | `RNICA.jsx` genitourinary fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 15 Musculoskeletal (+ Fall History, Mobility, ADL) | `RNICA.jsx` musculoskeletal fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 16 Skin/Wounds (+ Braden) | `RNICA.jsx` skin fields | same | POST/PUT/GET | Y | Braden total warning | `rnica_assessments.form_data` | none |
| 17 Imminent Death | `RNICA.jsx` imminentDeath fields | same | POST/PUT/GET | Y | HOPE J0050 warning | `rnica_assessments.form_data` | none |
| 18 SFV (+ Symptom Impact at SFV) | `RNICA.jsx` sfv fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 19 Safety | `RNICA.jsx` safety fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 20 Psychosocial | `RNICA.jsx` psychosocial fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 21 Spiritual | `RNICA.jsx` spiritual fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 22 Bereavement | `RNICA.jsx` bereavement fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 23 Personal Care (+ Aide Visit Preferences) | `RNICA.jsx` personalCare fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 24 Teaching Needs | `RNICA.jsx` teachingNeeds fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 25 Admissions Order (+ HA Assignment, Initial POC/IDG, TO Verification) | `RNICA.jsx` admissionsOrder fields | same | POST/PUT/GET | Y | Level of Care required (error); T.O. verbal read-back required (error) | `rnica_assessments.form_data` | Level of Care → `patient_facesheets.current_level_of_care` |
| 26 Hospice Orders Hub (+ Med Reconciliation) | `RNICA.jsx` medications fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 27 Referrals | `RNICA.jsx` referrals fields | same | POST/PUT/GET | Y | none | `rnica_assessments.form_data` | none |
| 28 Finalization (+ Response to Interventions, Supervisor Review) | `RNICA.jsx` finalization fields | same | POST/PUT/GET | Y | POC generation completed warning; clinician signature required (error) | `rnica_assessments.form_data` | Lock via `POST /visits/rnica/{id}/lock` |

---

## 3. Exceptions to the universal flow

### 3.1 Frontend-validated fields (the complete `validateRNICA()` rule set — `RNICA.jsx:765-886`)

This is the full list of fields the current frontend actually validates
on save/lock (all other ~270+ fields in the Field Inventory have **no**
frontend validation rule at all — see full catalogue in Deliverable #4):

| Field | Rule Type | Message |
|---|---|---|
| `demographics.firstName` | Required (error) | "First name is required" |
| `demographics.lastName` | Required (error) | "Last name is required" |
| `demographics.dob` | Required (error) | "Date of birth is required" |
| `demographics.gender` | Required (error) | "Gender is required" |
| `demographics.preferredLanguage` | Conditional warning (mode≠ongoing) | HOPE A1110 |
| `demographics.ethnicity` | Conditional warning (mode≠ongoing) | HOPE A1005 |
| `demographics.race` | Conditional warning (mode≠ongoing) | HOPE A1010 |
| `demographics.advancedCarePlanning.codeStatus` | Conditional required (error, mode≠ongoing) | HOPE F2000 |
| `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference` | Conditional required (error, mode≠ongoing) | HOPE F2100 |
| `demographics.advancedCarePlanning.hospitalizationPreference` | Conditional required (error, mode≠ongoing) | HOPE F2200 |
| `demographics.pcg` (assessed Y/N) | Warning | PCG status unassessed |
| `demographics.pcg.willingToProvideCare` | Conditional warning (skipped if `pcg.noPcg`) | CDPH caregiver willingness |
| `demographics.pcg.ableToAdministerMeds` | Conditional warning (skipped if `pcg.noPcg`) | CDPH med administration ability |
| `demographics.pcg.caregiverEvaluation.willingnessScore` | Conditional warning | CDPH willingness score |
| `demographics.pcg.caregiverEvaluation.capabilityScore` | Conditional warning | CDPH capability score |
| `finalization.pocGenerationCompleted` | Warning | CDPH POC generation before lock |
| `pain.verbalizesPain` | Conditional warning (mode≠ongoing) | HOPE J0900 |
| `pain.uncomfortableBecauseOfPain` | Conditional warning (mode≠ongoing) | HOPE J0915 |
| `symptomImpact.{pain,shortnessOfBreath,anxiety,nausea,vomiting,diarrhea,constipation,agitation}` (8 fields) | Conditional warning (mode≠ongoing) | HOPE J2051 A-H |
| `diagnoses.primaryDiagnosis.icd10` | Conditional required (error, mode≠ongoing) | HOPE I0010 |
| `performanceStatus.pps` / `.kps` | Conditional warning (mode≠ongoing, at least one required) | HOPE M1190 |
| `neurological.hopeItems.n0500` | Conditional warning (mode≠ongoing) | HOPE N0500 (BIMS) |
| `imminentDeath.appearsThreeDaysOrLess` | Conditional warning (mode≠ongoing) | HOPE J0050 |
| `skin.braden.total` | Warning | Braden Scale total |
| `admissionsOrder.levelOfCare.level` | Required (error) | Level of Care required for admission |
| `admissionsOrder.toVerification.verbalOrderReadBack` | Required (error) | T.O. read-back verification |
| `finalization.clinicianSignature` | Required (error) | Clinician signature required |

Only fields marked "error" block `lockRnicaAssessment()` from being
called (`RNICA.jsx:5572-5579`, `isValid = Object.keys(errors).length === 0`);
"warning" fields do not block save or lock. `mode="ongoing"` (RN
Recertification) skips all HOPE-item requirements
(`includeHopeRequirements = mode !== "ongoing"`, line 768).

### 3.2 Sync-dependency endpoints reached indirectly (not separate RNICA endpoints — invoked inside 1.1/1.4)

These do not have their own frontend-callable routes for RNICA; they are
internal function calls triggered by save/update:

| Function | File | Writes to | Invoked from |
|---|---|---|---|
| `_sync_facesheet_from_rnica` | `visits.py:175-220` | `patient_facesheets` (legacy text mirror) | save (1.1), update (1.4) |
| `_sync_shared_records_from_rnica` | `visits.py:293-421` | `patient_diagnoses`, `patient_allergies`, `patient_code_statuses`, `patient_contacts`, `patient_facesheets.current_level_of_care` | save (1.1), update (1.4) |
| `sync_official_primary_diagnosis` | `diagnosis_sync_service.py` | `patient_diagnoses` | via `_sync_shared_records_from_rnica` |
| `sync_secondary_and_comorbidity_diagnoses` | `diagnosis_sync_service.py` | `patient_diagnoses` | via `_sync_shared_records_from_rnica` |
| `sync_allergies_from_source` | `app/api/patient_allergies.py` | `patient_allergies` | via `_sync_shared_records_from_rnica` |
| `set_current_code_status` | `code_status_sync_service.py` | `patient_code_statuses` | via `_sync_shared_records_from_rnica` |
| `set_patient_contact` (×3: PCG, DPOA, Decision Maker) | `contact_sync_service.py` | `patient_contacts` | via `_sync_shared_records_from_rnica` |
| `get_current_code_status`, `get_patient_contacts` | `code_status_sync_service.py`, `contact_sync_service.py` | (read-only) | via `_overlay_shared_code_status()`, GET endpoints (1.2/1.3) |

### 3.3 Known path-mismatch (carried forward from Database Mapping, restated here as an API-layer consequence)

`_extract_rnica_code_status`/`_extract_rnica_dpoa`/`_extract_rnica_decision_maker`
(`visits.py:238-274`) read `form_data.get("advancedCarePlanning")` at the
**top level** of the payload, while `RNICA.jsx` and the Field Inventory
both nest this data under `form_data.demographics.advancedCarePlanning`.
Practical consequence for this API Mapping deliverable: the
`save`/`update` request payload sent by the frontend never has a
top-level `advancedCarePlanning` key, so these three extractors receive
`None` on every real call, and their corresponding `patient_code_statuses`
/ `patient_contacts` (DPOA, Decision Maker) sync writes are effectively
dead code in production traffic. `_extract_rnica_pcg` is unaffected — it
correctly reads `form_data.demographics.pcg`. This is recorded as an
observed fact only; no code change is made here.

---

## Status

**Deliverable #3 (`SNS_RNICA_API_MAPPING_1.0`) complete.** All 6 RNICA
endpoints documented (component, endpoint, method, payload, response,
auth, validation, database write, dependencies); all 28 sections traced
through the single universal save/update/load flow; the complete
frontend validation rule set recorded; all sync-dependency functions
and their target tables recorded; the code-status/contact path-mismatch
carried forward from Database Mapping restated in API terms.

No changes made to `SNS_RNICA_FIELD_INVENTORY_1.0`,
`SNS_RNICA_DATABASE_MAPPING_1.0`, `SNS_RNICA_MASTER_MAP_1.0`, or
`SNS_HOPE_CROSSWALK_1.0`. No code changes are authorized by this document.

Next, per the stated sequence: Deliverable #4 —
`SNS_RNICA_VALIDATION_INVENTORY_1.0`, pending explicit direction to
proceed.
