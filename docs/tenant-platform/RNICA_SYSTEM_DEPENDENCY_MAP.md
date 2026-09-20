# RNICA System Dependency Map

**STATUS: DISCOVERY ONLY — NO REDESIGN — NO CODE — NO SCHEMA — NO MIGRATIONS**

This document inventories everything the RN Initial Comprehensive Assessment
(RNICA) touches, before any Tenant UX redesign work begins. It is grounded in
direct repository evidence (file:line citations). Where no connection was
found after a real search, this is stated explicitly as **NO CONNECTION
FOUND** rather than assumed.

Companion documents:
- `RNICA_UI_DEPENDENCY_MAP.md` — per-UI-element classification
- `RNICA_REDESIGN_IMPACT_ANALYSIS.md` — redesign risk analysis

> **ARCHITECTURAL CORRECTION NOTICE — see `RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`:**
> The Owner has locked a product decision that `diagnoses.clinicalNarrative`
> was incorrectly placed and must not remain a nurse-facing narrative input in
> the redesigned RNICA. `finalization.clinicalNarrative` is the sole
> authoritative future Clinical Narrative. Dependency evidence below reflects
> the current repository state and is unchanged.

---

## 1. Repository Path Index

| Layer | Path |
|---|---|
| Model | `backend/app/models/rnica_assessment.py` |
| Amendment model | `backend/app/models/rnica_amendment.py` |
| POC adapter (RNICA → POC) | `backend/app/services/rnica_poc_adapter.py` |
| Finalization/readiness service | `backend/app/services/rnica_finalization_service.py` |
| Intelligence (AI/heuristics) service | `backend/app/services/rnica_intelligence.py` |
| HOPE workflow service | `backend/app/services/rnica_hope_workflow_service.py` |
| Amendment service | `backend/app/services/rnica_amendment_service.py` |
| Canonical key/normalization | `backend/app/domain/clinical/rn_ica_keys.py` |
| Required-field validation engine | `backend/app/services/clinical_note_validation_engine.py` |
| Assessment history serialization | `backend/app/services/assessment_history_service.py` |
| Dashboard consumption | `backend/app/services/dashboard_service.py` |
| Structured findings | `backend/app/services/evidence/structured_findings.py` |
| API — visit-scoped actions, lock, HOPE, amendments, intelligence | `backend/app/api/visits.py` |
| API — POC/finalization routes | `backend/app/api/routes/rnica_poc.py` |
| UI page | `sns-emr-frontend/src/components/RNICA.jsx` |
| Autosave hook | `useAssessmentAutosave` (used in `RNICA.jsx`) |

---

## 2. Model Fields (`backend/app/models/rnica_assessment.py:11-78`)

`id, patient_id, visit_id, admission_id, tenant_id, assessment_type, status,
locked, hope_workflow_status, hope_closed_at, hope_closed_by, hope_ready_at,
hope_ready_by, hope_exported_to_batch_at, hope_exported_to_batch_by,
hope_export_batch_id, hope_submission_number, hope_already_submitted,
hope_submitted_at, hope_submitted_by, hope_inactivated, hope_inactivated_at,
hope_inactivated_by, hope_unlocked_at, hope_unlocked_by, hope_unlock_reason,
form_data, notes, field_provenance, client_request_id, locked_at, created_at,
updated_at` (`rnica_assessment.py:11-78`), plus relationships `patient`,
`visit` (`rnica_assessment.py:14-78`).

FKs: `patients.id`, `visits.id`, `admissions.id`, `tenants.id`
(`rnica_assessment.py:15-28`).

---

## 3. Domain-by-Domain Trace

| Domain | Connection Found | Evidence |
|---|---|---|
| Face Sheet (`PatientFaceSheet`) | **NO CONNECTION FOUND** (no FK/service link in RNICA layer) | Facesheet fields are separate: `backend/app/models/patient_facesheet.py:23-353` |
| CTI (Certification) | **NO CONNECTION FOUND** (only finalization "signature certification" attestation, unrelated to CTI model) | `backend/app/services/rnica_finalization_service.py:103-108` |
| F2F (Face-to-Face) | **NO CONNECTION FOUND** | — |
| IDG (Interdisciplinary Group) | **NO CONNECTION FOUND** (direct model/service link); IDG-adjacent consumption only via general assessment-history/dashboard reads | `backend/app/services/assessment_history_service.py:90-125` |
| POC (Plan of Care) | **YES — strong, central** | `backend/app/services/rnica_poc_adapter.py:6-29,74-93,126-170,222-287,295-367,432-668`; finalization checks POC completeness `rnica_finalization_service.py:35-90,144-165`; API `backend/app/api/routes/rnica_poc.py:186-207,227-393,412-538` |
| HUV / SFV | **YES** (exist as distinct HOPE workflow visit types, not RNICA-specific but shared HOPE machinery) | Form registry `backend/app/domain/forms/form_registry.py:96-100,148-150,430-436,913-944,1098-1105`; workflow engine `backend/app/services/hope_phase_b_engine.py:24-33,167-181,277-293,330-370,419-426,500-501`; SFV model `backend/app/models/sfv_requirement.py:19,65`; RNICA key acceptance `backend/app/domain/clinical/rn_ica_keys.py:13-15` |
| HOPE | **YES — direct** | HOPE lifecycle columns live on the RNICA model itself: `rnica_assessment.py:33-50`; workflow service: `backend/app/services/rnica_hope_workflow_service.py:1-21,42-68,103-195`; router HOPE actions: `backend/app/api/visits.py:1382-1479` |
| Advance Care Planning | **NO CONNECTION FOUND** | — |
| Caregiver Assessment | **NO direct model/service link**; intelligence output *mentions* caregiver-related recommendations | `backend/app/services/rnica_intelligence.py:98-156` |
| Orders | **NO DIRECT MODEL FK FOUND**; indirect action exists to create a patient order from an RNICA suggestion via POC adapter | `backend/app/api/routes/rnica_poc.py:515-538` (`ADD_PATIENT_ORDER_FROM_RNICA_SUGGESTION`); `rnica_poc_adapter.py:432-668` |
| Diagnoses | **YES** | Intelligence reads `form_data.diagnoses.primaryDiagnosis`, `diseaseTrajectory`: `rnica_intelligence.py:66-75`; finalization checks diagnosis narrative/LCD baseline: `rnica_finalization_service.py:120-135`; POC adapter uses diagnosis content: `rnica_poc_adapter.py:222-287,432-668` |
| Medications | **NO CONNECTION FOUND** | — |
| Certifications | **Only finalization/signature attestation, not the CTI/Certification model** | `rnica_finalization_service.py:102-109`; HOPE lifecycle metadata acts similarly: `rnica_assessment.py:33-50`, `rnica_hope_workflow_service.py:42-68,103-195` |
| Benefit Period Logic | **NO DIRECT RNICA CONNECTION FOUND** (benefit-period fields live on facesheet, not RNICA) | `backend/app/models/patient_facesheet.py:201-203` |
| Admission Logic | **YES** — RNICA is scoped to and gated by admission | `rnica_assessment.py:19-28`; POC creation blocked until admission exists: `rnica_poc_adapter.py:126-153,317-326` |
| Eligibility (LCD / `PayerEligibilityCheck` / `EligibilityVerification`) | **Partial** — LCD only, as a required narrative field, not a scored evaluator; `PayerEligibilityCheck`/`EligibilityVerification` — **NO CONNECTION FOUND** | LCD gate: `rnica_finalization_service.py:130-136`; readiness endpoint: `backend/app/api/routes/rnica_poc.py:193-210`; lock re-check: `backend/app/api/visits.py:1204-1223` |
| Billing Readiness | **NO CONNECTION FOUND** — billing readiness engine is entirely separate and does not join RNICA data | `backend/app/billing/services/billing_readiness_service.py:1-23` (payer/benefit-period/NOE/cert/F2F/POC-signature/MSP logic, no RNICA join) |
| QA / Compliance Review | **NO DEDICATED CONNECTION FOUND** beyond generic dashboard/audit-log consumption | `backend/app/services/dashboard_service.py:1147-1152` |
| Survey Readiness | **NO CONNECTION FOUND** | — |
| Audit Events | **YES** — lock and amendment actions write audit events | Lock: `RNICA_ASSESSMENT_LOCKED` `backend/app/api/visits.py:1238-1251`; amendments: `RNICA_AMENDMENT_SUBMITTED/APPROVED/DENIED` `backend/app/services/rnica_amendment_service.py:125-139,189-201,227-239` |
| Structured Findings | **YES** | Intelligence accepts `structured_findings_signals`: `rnica_intelligence.py:176-222`; endpoint passes `list_pending_structured_findings(...)`: `backend/app/api/visits.py:1657-1676`; independent validation layer: `backend/app/services/evidence/structured_findings.py:1928-2135`; also stored on `backend/app/models/patient_evidence.py:184-205` |
| AI Findings | **YES** (rules/heuristics engine, not an LLM/ML call — see Section 5) | `rnica_intelligence.py:57-222` |
| Validation Rules | **YES** | Canonical keys `rn_ica_keys.py:6-41`; finalization checks `rnica_finalization_service.py:35-165`; POC mutation rules `rnica_poc_adapter.py:104-170,295-668`; required-field engine `clinical_note_validation_engine.py:380-470,613,934-970` |

---

## 4. Save / Validation / Lock / Sign Behavior

- **Save**: autosave via `useAssessmentAutosave` (frontend, 30s interval, per prior
  frontend audit of `RNICA.jsx`).
- **Validation (client)**: `validateRNICA` in `RNICA.jsx` (frontend gate before
  allowing finalize/lock actions).
- **Validation (server)**: `clinical_note_validation_engine.py:380-470,934-970`
  enforces required fields: Primary Diagnosis, LCD Supporting Evidence,
  Clinical Narrative, Disease Trajectory, PPS, KPS, Code Status,
  Life-Sustaining Treatment Preference, Hospitalization Preference, Pain
  Screening, Respiratory Rate, Weight, Appetite/Intake, ADL Assistance
  Required, Mobility Decline, Cognitive Decline, Plan of Care Narrative.
- **Finalization readiness (server)**: `rnica_finalization_service.py:35-171`
  checks: signature certification attestation, clinician signature present,
  clinical narrative reviewed (if narrative present), LCD baseline narrative
  present, referrals reviewed, POC completeness (goals/interventions/discipline
  present), CHHA POC completed (if HHA assigned). It does **not** check
  `PatientPayer`, `PatientInsurance`, eligibility, authorizations, or billing
  readiness (`rnica_finalization_service.py:94-171`).
- **Lock**: `POST /visits/rnica/{assessment_id}/lock`
  (`backend/app/api/visits.py:1177-1265`) re-runs
  `evaluate_finalization_readiness(...)` and rejects the lock if unmet;
  on success writes `RNICA_ASSESSMENT_LOCKED` audit event
  (`visits.py:1238-1251`).
- **Sign**: clinician signature and signature-certification attestation are
  required fields inside `form_data.finalization`, checked at
  `rnica_finalization_service.py:102-116`. No separate e-signature service was
  found; signature is a stored attestation value, not a cryptographic
  signature integration.
- **Amendment (post-lock correction)**: locked content is never mutated.
  `POST /rnica/{assessment_id}/correction-request` creates a separate
  `RnicaAmendment` row (`backend/app/models/rnica_amendment.py:1-116`) with
  approve/deny endpoints (`backend/app/api/visits.py:1522-1655`), each step
  writing its own audit event
  (`backend/app/services/rnica_amendment_service.py:125-139,189-201,227-239`).

---

## 5. AI Dependency Detail

**RNICA "Intelligence" (`GET /rnica/{assessment_id}/intelligence`,
`backend/app/api/visits.py:1657-1678` →
`backend/app/services/rnica_intelligence.py:57-222`)**

- **Not an AI/LLM call.** It is a deterministic rules/heuristics engine —
  output mode is explicitly `"recommendation_only"`
  (`rnica_intelligence.py:195`). No OpenAI/Azure/ML client is present in this
  code path.
- **Input**: `form_data` sections — `diagnoses`, `pain`, `respiratory`,
  `safety`, `musculoskeletal`, `neurological`, `imminentDeath`,
  `psychosocial` (`rnica_intelligence.py:57-176`); plus
  `gather_patient_evidence(...)` and `list_pending_structured_findings(...)`
  (`visits.py:1670-1671`).
- **Logic**: hardcoded thresholds/booleans (pain ≥7, oxygen use, fall risk,
  delirium signs, imminent-death indicators, psychosocial distress)
  (`rnica_intelligence.py:70-174`).
- **Output**: `summary` (overall_priority, counts), `findings`,
  `recommendations`, `missing_evidence`, `evidence` (assessment_text,
  sections, patient_evidence), `structured_findings_signals` passthrough
  (`rnica_intelligence.py:184-222`).
- **Consumer**: the RNICA "Intelligence" panel in `RNICA.jsx`.
- **Failure impact**: advisory only — it informs the clinician but is not a
  gate on save/lock/finalize (finalization readiness is a separate function,
  Section 4).

**LCD (Local Coverage Determination) evaluation**
- Represented as a **required narrative field**
  (`diagnoses.lcdEligibilityNarrative`), not a scored/automated eligibility
  evaluator, at the backend layer searched
  (`rnica_finalization_service.py:130-136`).
- Output is boolean presence/absence of the narrative, not an eligibility
  score.
- **No confirmed backend join** between RNICA LCD narrative and
  `patient_payers`/`patient_insurances` for claim eligibility was found
  (`billing_readiness_service.py:1-23` uses payer/benefit-period/NOE/cert/F2F/
  POC-signature/MSP data, not RNICA).

---

## 6. Downstream Consumers of Locked/Finalized RNICA Data

| Consumer | Evidence |
|---|---|
| Plan of Care (explicit, action-driven, not automatic on lock) | `backend/app/services/rnica_poc_adapter.py:1-48,71-84` |
| Assessment history / timeline | `backend/app/services/assessment_history_service.py:13-125` |
| Dashboards (incomplete/unlocked RNICA counts, alert logic) | `backend/app/services/dashboard_service.py:20,386-388,1147-1152` |
| Audit log | `backend/app/api/visits.py:1238-1251`; `rnica_amendment_service.py:125-139,189-201,227-239` |
| Billing readiness / claims / NOE | **NOT FOUND** — no backend code was found joining `rnica_assessments` with `patient_payers`/`patient_insurances` for billing readiness or claims |
| Dedicated QA/QAPI report | **NOT FOUND** beyond the generic dashboard/audit-log consumers above |

---

## 7. Open Findings / Gaps for Future Review (informational only — no action proposed)

- RNICA finalization does not gate on billing/eligibility state — if a future
  redesign or workflow change assumes it does, that assumption is currently
  false per the evidence above.
- No dedicated RNICA Pydantic schema was found in `backend/app/schemas/`;
  request validation is split between amendment-endpoint request models
  (`backend/app/api/visits.py:1488-1509`) and the required-field engine
  (`clinical_note_validation_engine.py`).
- "AI Findings" is a rules engine, not a generative/ML system — this
  materially affects how "AI Critical" is defined in the UI Dependency Map.

**No implementation, redesign, schema change, or code change is proposed by
this document. Inventory only.**
