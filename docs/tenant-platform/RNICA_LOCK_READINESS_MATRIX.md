# RNICA_LOCK_READINESS_MATRIX.md

**Status:** v2 — repository-validated. Supersedes v1 (commit `7836ca1`).
**Purpose:** Define one authoritative path from validation to signature,
lock, amendment, and audit.

## 1. Severity model

- **Blocker:** Lock must fail server-side.
- **Warning:** Lock may proceed only if current approved policy allows it;
  must remain visible.
- **Informational:** Does not affect lock.
- **Conditional blocker:** Enforced only when its documented applicability
  condition is true.

## 2. Confirmed server enforcement mechanism

Two distinct server functions govern readiness/lock, confirmed in
`backend/app/api/visits.py` and `backend/app/services/
clinical_note_validation_engine.py`:

1. `evaluate_finalization_readiness(form_data, poc_problems)` — the exact
   function called by **both** `GET /visits/rnica/{id}/finalization-
   readiness` (Compliance & Readiness screen source) and
   `POST /visits/rnica/{id}/lock` (server enforcement). This guarantees the
   UI's Lock button and the server's Lock gate cannot disagree, by
   construction (same function, same call).
2. `RN_ICA_REQUIRED_FIELD_GROUPS` (17-item hard-required field list,
   `clinical_note_validation_engine.py:380-517`), enforced via
   `_validate_required_rn_ica_sections` (:934-975) and
   `_validate_required_functional_assessments` (:987-1112) — this is a
   separate, note-level validation path (used for general clinical-note
   completeness, not specifically the Lock button gate above). Both paths
   must be reconciled/cited together in the implementation plan; treating
   them as identical without verifying call-site parity is
   `[IMPLEMENTATION DISCOVERY REQUIRED]`.

## 3. Required matrix

| Check | Applicability | Server enforcement (confirmed) | Source screen | Lock effect | Audit event |
|---|---|---|---|---|---|
| Primary Diagnosis | All RN ICA/Update/Recert | `RN_ICA_REQUIRED_FIELD_GROUPS` | Diagnosis & LCD | Blocks | Not confirmed as a discrete event; captured only implicitly at `RNICA_ASSESSMENT_LOCKED` |
| LCD Supporting Evidence | All RN ICA/Update/Recert | `RN_ICA_REQUIRED_FIELD_GROUPS` | Diagnosis & LCD | Blocks | same as above |
| Clinical Narrative (`finalization.clinicalNarrative`) | All RN ICA/Update/Recert | `RN_ICA_REQUIRED_FIELD_GROUPS` | Finalization | Blocks | `RNICA_ASSESSMENT_LOCKED` |
| Disease Trajectory | All RN ICA/Update/Recert | `RN_ICA_REQUIRED_FIELD_GROUPS` | Diagnosis & LCD | Blocks | same |
| PPS | RN ICA/Update/Recert (not routine/PRN) | `_validate_required_functional_assessments`, always-required | Functional Status | Blocks | same |
| KPS | RN ICA/Update/Recert (not routine/PRN) | `_validate_required_functional_assessments`, always-required | Functional Status | Blocks | same |
| FAST | Only if dementia-related | `_validate_required_functional_assessments`, conditional | Functional Status | Blocks (if applicable) | same |
| NYHA | Only if cardiac-related | `_validate_required_functional_assessments`, conditional | Functional Status | Blocks (if applicable) | same |
| ECOG | Only if oncology/metastatic/hematologic | **No enforcement branch found — confirmed open defect** | Functional Status | Not enforced today | n/a |
| Code Status | All applicable | `RN_ICA_REQUIRED_FIELD_GROUPS` | ACP & Goals of Care | Blocks | same |
| Life-Sustaining Treatment Preference | All applicable | `RN_ICA_REQUIRED_FIELD_GROUPS` | ACP & Goals of Care | Blocks | same |
| Hospitalization Preference | All applicable | `RN_ICA_REQUIRED_FIELD_GROUPS` | ACP & Goals of Care | Blocks | same |
| Advance Directives / POA / Decision Maker / CPR Preference (approved target: 6 ACP fields total — resolved this pass, see `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md`) | Target authority requires 6; current repository enforces 3 | **Current: `demographics.advancedCarePlanning.{cprPreferenceAskedStatus, lifeSustainingAskedStatus, hospitalizationAskedStatus}` confirmed to already exist (F2000/F2100/F2200-A HOPE comment), not in `RN_ICA_REQUIRED_FIELD_GROUPS`.** No new schema/storage required for the 6-field target. `lifeSustainingAskedStatus` is client-required but not server-enforced (parity gap). HOPE-vs-SNS-internal labeling and response-set integrity remain `[IMPLEMENTATION DISCOVERY REQUIRED]`. | ACP & Goals of Care | Current: no server Lock effect for the 3 discussion-status fields. Target: must block once enforcement added, applied prospectively only | n/a today |
| Pain Screening | All applicable | `RN_ICA_REQUIRED_FIELD_GROUPS` | Pain & Symptom Burden | Blocks | same |
| Pain reassessment / 24h follow-up | Conditional on prior pain score | Referenced in product screenshot ("Pain Reassessment Required" blocking issue) but exact validator **not isolated from the base Pain Screening check in this pass** | Pain & Symptom Burden | `[IMPLEMENTATION DISCOVERY REQUIRED]` | n/a |
| Respiratory Rate, Weight, Appetite/Intake | All applicable | `RN_ICA_REQUIRED_FIELD_GROUPS` | Body Systems | Blocks | same |
| ADL Assistance Required, Mobility Decline, Cognitive Decline | All applicable | `RN_ICA_REQUIRED_FIELD_GROUPS` | Body Systems | Blocks | same |
| Plan of Care Narrative | All applicable | `RN_ICA_REQUIRED_FIELD_GROUPS` | Orders & POC | Blocks | same |
| Fall Risk / Morse score | Shown prominently in product screenshot | **Not found** in `RN_ICA_REQUIRED_FIELD_GROUPS`. Instrument-specific score/interpretation may be retained; RNICA must not invent a new aggregate risk-scoring engine. Becomes a Lock blocker only if a controlling requirement or approved agency policy explicitly requires completion. | Safety & Clinical Risk | **BLOCKED BY AUTHORITY DECISION** — do not add as a hard Lock blocker until that authority is documented | n/a |
| SFV documentation | Shown as blocking in product screenshot ("SFV Assessment Missing") | **Backend enforcement path not isolated in this pass** — `getSfvStatus`/`getHopeAdmissionStatus` (`src/intake/hopeReportMapper.js`) compute client-side status; server-side blocking check not confirmed | Body Systems / SFV | `[IMPLEMENTATION DISCOVERY REQUIRED]` | n/a |
| Attestation (`finalization.signatureCertification`) | Finalization | Read directly by the Lock handler and included in `RNICA_ASSESSMENT_LOCKED` audit metadata (`visits.py`) | Finalization | Confirmed captured, but **not confirmed as a hard blocker** distinct from the general readiness check — `[IMPLEMENTATION DISCOVERY REQUIRED]` | `RNICA_ASSESSMENT_LOCKED` |
| Clinician Signature (`finalization.clinicianSignature`) | Finalization | Same as above | Finalization | Same as above | `RNICA_ASSESSMENT_LOCKED` |
| Legacy Diagnosis narrative review defect | Historical records only | Governed by prior `RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md` (not reopened this pass) | Finalization/legacy review | May block | Not re-verified this pass |

## 4. Lock transaction — confirmed sequence (`visits.py`, `lock_rnica_assessment`)

1. Look up assessment by UUID; 404 if not found.
2. Authorize current user against the patient (`get_authorized_patient`).
3. **Idempotent re-lock:** if `record.locked` is already `True`, return the
   existing lock state immediately — readiness checks are **not** re-run
   and no duplicate audit event is emitted. This is deliberate (comment in
   code: re-running readiness on an already-signed record "could
   spuriously fail if reference data changed after signing").
4. Otherwise, load `poc_problems` via `rnica_poc_adapter.list_all_problems`
   and call `evaluate_finalization_readiness(record.form_data, poc_problems)`.
5. If not ready: raise `HTTPException(400, {"unmetChecks": [...], "checks":
   {...}})` — the same `checks` structure the Compliance & Readiness screen
   renders.
6. If ready: set `record.locked = True`, `record.status = "LOCKED"`,
   `record.locked_at = now(UTC)`; call
   `rnica_hope_workflow_service.sync_submission_fields_from_form_data`;
   commit.
7. POC is explicitly **not** touched here (see
   `docs/rnica-poc-lock-no-autogen-disposition.md`).
8. Emit `_safe_log_event(action="RNICA_ASSESSMENT_LOCKED", entity_type=
   "rnica_assessment", metadata={patientId, signatureCertification,
   clinicianSignature, lockedAt})`; commit again.

## 5. Locked-record edit protection — confirmed

- `PUT /visits/rnica/{id}`: if `record.locked`, raises
  `HTTPException(423, ...)` directing the caller to
  `POST /rnica/{assessment_id}/correction-request` instead
  (`visits.py:1109-1115`).
- `DELETE /visits/rnica/{id}`: same 423 protection
  (`visits.py:1164-1169`).
- **Confirmed open defect (unchanged from prior verification):**
  `record.status = "DRAFT"` is set unconditionally on every successful
  (non-locked) `PUT` (`visits.py:1118`) — even a trivial autosave tick
  resets `status` to `"DRAFT"`. This is pre-existing behavior, not new
  design intent; classified in the Gap Report as "Implemented but
  defective."

## 6. Amendment workflow — confirmed

- `POST /visits/rnica/{id}/correction-request` — creates a distinct,
  timestamped, attributable record; never mutates the original signed
  content (`requestRnicaCorrection`, `src/api/icaAssessments.ts`).
- `GET /visits/rnica/{id}/amendments` — read-only history
  (`listRnicaAmendments`).
- `POST /visits/rnica/{id}/amendments/{amendmentId}/approve` /
  `.../deny` — review actions, backed by `rnica_amendment.py` (model) and
  `rnica_amendment_service.py` (service). Tested in
  `backend/tests/test_rnica_amendments.py`.

## 7. Automated test coverage — confirmed (backend/tests)

`test_rnica_amendments.py`, `test_rnica_finalization.py`,
`test_rnica_order_suggestions.py`, `test_rnica_hope_workflow.py`,
`test_rnica_poc_adapter.py`, `test_rnica_poc_history.py`,
`test_rnica_runtime_validation.py`, `test_structured_findings.py`,
`test_structured_findings_acceptance_analytics.py`,
`test_structured_findings_bulk_api.py`,
`test_structured_findings_application.py`,
`test_structured_findings_rn_productivity_metrics.py`,
`test_evidence_harvester.py`, `test_admission_action_center.py`,
`test_idg_batch_sign_authorization.py`, `test_owner_audit_logs.py` — 16
backend test files directly exercise RNICA-adjacent behavior, plus
`sns-emr-frontend/src/components/rn-ica/applyStructuredFindings.test.js`
on the frontend. This is broader coverage than a prior (now superseded)
completion ledger in this repository claimed; do not assume "no tests
exist" without checking this list first.

## 8. UI requirements (unchanged from v1)

- Compliance & Readiness must show all server-enforced blockers before
  Finalization when available.
- Finalization must show the same blocker identity and severity returned
  by the server.
- Every blocker must navigate to its authoritative source.
- Passed checks may collapse but remain reviewable.
- AI recommendations must be visually separate from blockers.
