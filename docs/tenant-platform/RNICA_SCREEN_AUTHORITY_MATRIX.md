# RNICA_SCREEN_AUTHORITY_MATRIX.md

**Status:** v2 — repository-validated. Supersedes v1 (commit `7836ca1`).
**Purpose:** Define screen ownership, editability, sources, outputs, and
prohibited behavior for each of the 13 approved RNICA workflow destinations.

## Global rule

A screen may aggregate or present data owned elsewhere. Presentation does
not transfer ownership. **Repository status:** none of the 13 screens exist
as discrete routes/components today. `RNICA.jsx` is a single legacy
28-module component (`NAV_SECTIONS`/`LEGACY_ROUTES`,
`sns-emr-frontend/src/components/RNICA.jsx:~157-190`). The mapping below
states which legacy modules/fields the future screen must consume, not
which screen currently exists.

## 1. Patient Story
- **Purpose:** Read-only patient orientation. **Owns:** Nothing.
- **Consumes:** `fetchPatientSummary` (`src/api/patientCharts.js`),
  `fetchFacesheet` (`src/api/facesheet.ts`), diagnoses/decline evidence from
  legacy `demographics`/`diagnoses`/`performanceStatus` modules, caregiver
  context from legacy `psychosocial`/`bereavement` modules, `intelligence`
  state (from `getRnicaIntelligence`).
- **Produces:** Navigation only. **Editable:** No, except links to
  authoritative source screens.
- **AI:** May show saved advisory summary and missing evidence with
  freshness (see `RNICA_AI_GOVERNANCE.md`).
- **Prohibited:** New data authority, certification, risk score, generated
  Final Clinical Narrative.
- **Repository status:** Not implemented as a screen. The panels shown in
  the approved Figma frame (Why Hospice, Recent Hospitalization, Current
  Clinical Concerns, RNICA Intelligence, Missing Information, Caregiver
  Overview) do not have a corresponding aggregation component in
  `RNICA.jsx` today.

## 2. Evidence & Intake
- **Purpose:** Review referral, facesheet, imported records, vitals, and
  available evidence. **Owns:** RNICA intake-review state only where
  already canonical (legacy `demographics`, `vitals`, `referrals` modules).
- **Consumes:** Facesheet (`fetchFacesheet`, `fetchPerformanceHistory`),
  structured findings signals harvested from documents
  (`intelligence.structured_findings_signals`,
  `applyStructuredFindings.js`), `CONCEPT_REGISTRY`
  (`structuredFindingRegistry.generated.js`).
- **Produces:** Reviewed/missing-evidence state via
  `reviewHarvestedSignal`/`batchReviewHarvestedSignals`
  (`src/api/icaAssessments.ts`).
- **Editable:** Only fields owned by RNICA intake; external-source data
  must retain provenance (`structuredFieldProvenance` state,
  `RNICA.jsx`, confirmed).
- **Prohibited:** Becoming the document repository or silently changing
  source records.
- **Repository status:** Structured-findings review/apply/provenance
  mechanism is confirmed built and tested (`test_structured_findings*.py`,
  `applyStructuredFindings.test.js`). No dedicated "Evidence & Intake"
  screen exists; it is currently interleaved across legacy `demographics`/
  `vitals`/`referrals` modules.

## 3. Functional Status
- **Purpose:** Capture functional performance and diagnosis-relevant
  scales. **Owns:** legacy `performanceStatus` module fields.
- **Always visible:** PPS, KPS — enforced hard-required at Lock for
  RN ICA/Update/Recert (`clinical_note_validation_engine.py:987-1112`).
- **Conditional:** FAST (dementia-related, server-enforced), NYHA
  (cardiac-related, server-enforced), ECOG (**no server enforcement branch
  found — confirmed open defect**).
- **Produces:** Functional evidence, HOPE data
  (`rnica_hope_workflow_service.py`), validation state, LCD facts
  (`buildClientLcdFacts()`, `RNICA.jsx`, reads `performanceStatus.pps/kps/
  nyha/fast`).
- **Prohibited:** Irrelevant scales, disabled placeholders, automatic
  eligibility determination.

## 4. Pain & Symptom Burden
- **Purpose:** Capture pain and symptom burden. **Owns:** legacy `pain`,
  `symptomImpact` modules (`NumericPainScale`, `PAINADScale`, `FLACCScale`
  components, `SYMPTOM_IMPACT_CHECKLIST` constant mapping to HOPE J2051 A-H).
- **Consumes:** Medication/order display (`src/api/medications.js`) where
  authorized; source ownership remains external.
- **Produces:** HOPE pain/symptom items, findings, warnings, follow-up
  needs (SFV status, `getSfvStatus`/`getHopeAdmissionStatus`,
  `src/intake/hopeReportMapper.js`).
- **AI:** Advisory follow-up suggestions only.
- **Prohibited:** Silent medication/order changes; derived values
  overwriting manual entries.

## 5. Diagnosis & LCD
- **Purpose:** Capture diagnoses, relatedness, comorbidities, LCD evidence,
  and LCD Supporting Narrative. **Owns:** legacy `diagnoses` module,
  including `ndsEligibility` sub-state.
- **Produces:** Diagnosis evidence, LCD support via
  `detectLCD`/`evaluateLCD`/`getLCDConfig`
  (`src/api/eligibility.ts:62-87` → `/eligibility/lcd-*` backend routes),
  HOPE diagnosis mapping, validation output.
- **AI:** May identify supporting evidence and gaps only — confirmed the
  client builds a facts object (`buildClientLcdFacts`,
  `RNICA.jsx:~1478-1520`) sent to the server evaluator; output is a
  criteria-match structure, not an eligibility verdict, and must be
  presented per `RNICA_AI_GOVERNANCE.md` §5 language rules.
- **Prohibited:** Final Clinical Narrative, physician certification,
  eligibility confirmation, AI prognosis.

## 6. Body Systems
- **Purpose:** Capture ten body-system assessments. **Owns:**
  `RNICA_BODY_SYSTEM_MODULES` (`src/config/bodySystems.js`) — Neurological,
  Cardiovascular, Respiratory, Infection, Gastrointestinal, Nutrition,
  Endocrine, Genitourinary, Musculoskeletal, Skin/Wounds, plus Imminent
  Death and SFV modules.
- **Produces:** Clinical findings; feeds Structured Findings and LCD facts
  (confirmed: nutrition/musculoskeletal/genitourinary/gastrointestinal/
  vitals/respiratory fields are read directly by `buildClientLcdFacts()`).
- **Server validation:** RN ICA notes explicitly **skip** the generic
  full/focused Review-of-Systems required-section validator
  (`_validate_required_ros`, `clinical_note_validation_engine.py:791-934`,
  `if is_rn_ica: return`) — Body Systems completeness for RN ICA Lock is
  governed only by the Cognitive-Decline/Mobility-Decline entries in the
  17-item hard-required list, not a full per-system requirement.
- **Prohibited:** Assuming every system feeds Intelligence; hiding
  clinically significant findings.

## 7. Caregiver & Support
- **Purpose:** Capture caregiver availability, willingness, capability,
  concerns, psychosocial/spiritual/personal-care and teaching needs.
  **Owns:** legacy `psychosocial`, `spiritual`, `bereavement`,
  `personalCare`, `teachingNeeds` modules.
- **Produces:** Documented findings and plan-of-care inputs.
- **Prohibited:** Derived burden, sustainability, or caregiver-risk scores
  unless a separately approved validated instrument exists (none found in
  repository).

## 8. Safety & Clinical Risk
- **Purpose:** Capture documented risk factors, home/oxygen safety,
  imminent-death screening, and interventions. **Owns:** legacy `safety`,
  `imminentDeath` modules.
- **Produces:** Documented concerns, warnings, source-linked advisory
  findings.
- **Prohibited:** New aggregate risk score or derived high/medium/low
  engine unless a validated tool is explicitly authorized. Fall
  Risk/Morse scoring appears in the product screenshot but its Lock-blocking
  status is **not found** in the 17-item hard-required list —
  `[IMPLEMENTATION DISCOVERY REQUIRED]`.

## 9. ACP & Goals of Care
- **Purpose:** Capture treatment preferences and advance-care-planning
  fields. **Owns:** legacy ACP fields (spread across `demographics`/
  `diagnoses` in the current module layout — no dedicated ACP module
  confirmed).
- **Produces:** HOPE ACP mappings, POC inputs, readiness status.
- **Confirmed hard-required at Lock (3, not 6 — corrected from v1):** Code
  Status, Life-Sustaining Treatment Preference, Hospitalization Preference
  (`RN_ICA_REQUIRED_FIELD_GROUPS`,
  `clinical_note_validation_engine.py:380-517`). Advance Directives, POA,
  CPR Preference, and Decision Maker are **not found** in the hard-required
  list — `[IMPLEMENTATION DISCOVERY REQUIRED]` (may be optional/soft fields
  today; must be verified before presenting them as Lock-blocking).
- **Prohibited:** Owning POC interventions, final certification, or Final
  Clinical Narrative.

## 10. Orders & POC
- **Purpose:** Show and explicitly initiate authorized order/POC actions.
  **Owns:** RNICA action state only; `poc_problems` remain owned by the
  authoritative Plan of Care domain (`rnica_poc_adapter.py`).
- **Consumes/Produces:** `viewRnicaSectionPoc`, `addRnicaSectionPocProblem`,
  `updateRnicaSectionPocProblem`, `resolveRnicaSectionPocProblem`,
  `linkExistingRnicaSectionPocProblem`, `mergeRnicaPocDuplicateProblems`,
  `deactivateRnicaSectionPocProblem`, `viewRnicaAllPoc` — all confirmed in
  `src/api/icaAssessments.ts` calling `backend/app/api/routes/rnica_poc.py`.
- **Confirmed:** POC is never auto-generated at Lock
  (`docs/rnica-poc-lock-no-autogen-disposition.md`; confirmed still true at
  `visits.py:1178-1250` — the lock handler explicitly does not call
  `poc_generation_service`).
- **Prohibited:** Silent order creation, silent POC mutation, automated
  physician approval.

## 11. Compliance & Readiness
- **Purpose:** Display all enforced blockers, warnings, HOPE state,
  referral review, POC/CHHA readiness, and navigation to sources.
  **Owns:** Presentation only.
- **Produces:** `getRnicaFinalizationReadiness` (`GET /visits/rnica/{id}/
  finalization-readiness`) — confirmed single source of truth shared with
  the server Lock gate (`evaluate_finalization_readiness`, same function
  called by both the readiness endpoint and the lock endpoint).
- **Prohibited:** Hiding/truncating blockers, changing severity,
  representing non-connected readiness engines (e.g. CTI, Survey
  Readiness, Billing Readiness — not found anywhere in this repository) as
  operational.

## 12. AI Action Center
- **Purpose:** Present RNICA Intelligence findings, missing evidence,
  documentation gaps, compliance signals, and freshness. **Owns:** No
  clinical source data. **Source:** `getRnicaIntelligence`
  (`src/api/icaAssessments.ts`) → `intelligence` state in `RNICA.jsx`.
- **Prohibited:** Eligibility, prognosis, certification, narrative
  authority, risk scoring, live-typing claims, silent mutations. See
  `RNICA_AI_GOVERNANCE.md` for the full trigger/output/language contract.

## 13. Finalization
- **Purpose:** Complete Final Clinical Narrative, readiness, manual
  attestation, signature, lock, amendment, and audit review.
- **Owns:** `finalization.clinicalNarrative`,
  `finalization.signatureCertification`, `finalization.clinicianSignature`
  — confirmed as the exact field paths read at Lock time
  (`backend/app/api/visits.py:1178-1250`, audit metadata block).
- **Produces:** `lockRnicaAssessment` (`POST /visits/rnica/{id}/lock`),
  `requestRnicaCorrection`/`listRnicaAmendments`/`approveRnicaAmendment`/
  `denyRnicaAmendment` (all confirmed wired, backed by
  `rnica_amendment.py`/`rnica_amendment_service.py`, tested in
  `test_rnica_amendments.py`, `test_rnica_finalization.py`).
- **Confirmed defect:** `record.status = "DRAFT"` runs unconditionally on
  every `PUT /visits/rnica/{id}` update (`visits.py:1118`), even trivial
  autosave ticks — this is a pre-existing, still-present bug, not new
  behavior to design around. Logged in
  `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md` as "Implemented but defective."
- **Prohibited:** Duplicate narrative, automatic signature/attestation/
  lock, bypass of server readiness.
