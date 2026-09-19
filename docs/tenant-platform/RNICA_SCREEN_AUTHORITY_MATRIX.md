# RNICA Screen Authority Matrix

Companion to `RNICA_IMPLEMENTATION_AUTHORITY.md`. Defines the exact field
inventory per screen so engineering does not have to interpret the
Figma Source of Truth. Does not reopen
`RNICA_REDESIGN_SOURCE_OF_TRUTH.md`, `RNICA_SCREEN_BY_SCREEN_EVIDENCE_MATRIX.md`,
or `RNICA_WORKFLOW_AUTHORITY_MAP.md`.

STATUS: IMPLEMENTATION DOCUMENTATION. CODE/SCHEMA/MIGRATIONS BLOCKED.

Legend: same seven labels as `RNICA_IMPLEMENTATION_AUTHORITY.md`, plus
**[IMPLEMENTATION DISCOVERY REQUIRED]** for fields whose exact backend
column/endpoint was not directly re-verified while writing this matrix.

Columns: Field | Type | Required at Lock | Source.

---

## Screen 1 — Patient Story

Presentation-layer only (see `PATIENT_CHART_AUTHORITY_MAP.md` Patient
Story Rule — restated, not reopened). No field here is independently
required at Lock; every value is read from its owning screen.

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| Patient identity / diagnosis header | read-only | No (owned by Facesheet) | `[REPOSITORY-DISCOVERED]` `fetchFacesheet` |
| "Why Hospice" narrative | read-only text | No | `[REPOSITORY-DISCOVERED]` screenshot-confirmed panel; backing field `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Recent Hospitalization summary | read-only | No | `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Current Clinical Concerns (Fall Risk, Pain Control, Respiratory, Nutritional) | read-only, derived | No | `[REPOSITORY-DISCOVERED]` derived from Safety/Pain/Body Systems/Nutrition screens; exact derivation rule `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| RNICA Intelligence summary panel | read-only, AI | No | `[REPOSITORY-DISCOVERED]`, governed by `RNICA_AI_GOVERNANCE.md` |
| Missing Information panel | read-only, AI | No | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |
| Caregiver Overview panel | read-only | No | `[REPOSITORY-DISCOVERED]` sourced from Caregiver & Support |

## Screen 2 — Evidence & Intake

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| Referral data / facesheet facts | read-only | Indirectly — `referrals.reviewed` is a readiness flag | `[REPOSITORY-DISCOVERED]` `RNICA_WORKFLOW_AUTHORITY_MAP.md` Screen 2 |
| Imported documents | list | No | `[REPOSITORY-DISCOVERED]` Documents & Images workspace |
| Evidence Summary / Missing Evidence (AI) | read-only, AI | No | `[REPOSITORY-DISCOVERED]`, governed by `RNICA_AI_GOVERNANCE.md` |
| `referrals.reviewed` | boolean | **Yes** — participates in Finalization readiness | `[REPOSITORY-DISCOVERED]` `RNICA_WORKFLOW_AUTHORITY_MAP.md` Screen 2 Lock Impact |

## Screen 3 — Functional Status

Confirmed directly against the provided Functional Status screenshot.

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| `performanceStatus.pps` (PPS %) | select/percent | **Yes**, always | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["PPS"]`, paths incl. `performanceStatus.pps` (`clinical_note_validation_engine.py:416-425`) |
| `performanceStatus.kps` (KPS %) | select/percent | **Yes**, always | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["KPS"]`, paths incl. `performanceStatus.kps` (same lines) |
| Mobility & Transfer Detail (ambulation state, transfer ability) | text/select | Not independently confirmed — see `Mobility Decline` below | `[REPOSITORY-DISCOVERED]` `functionalStatus.mobilityDecline` (`clinical_note_validation_engine.py:502-509`) |
| Fall Risk / Morse score | numeric + derived risk label | Not confirmed in `RN_ICA_REQUIRED_FIELD_GROUPS` | `[IMPLEMENTATION DISCOVERY REQUIRED]` — screenshot shows "Fall Risk Assessment (Morse) — High Risk (Score 18/25)"; no matching entry found in the 17-item required list |
| Cognitive & Mental Status (Orientation, Clinical Note, Standardized Test) | text | Partially — `Cognitive Decline` is required | `[REPOSITORY-DISCOVERED]` `neurological.cognitiveDecline` (`clinical_note_validation_engine.py:511-517`) |
| ADLs (Bathing, Dressing, Toileting, Transferring, Eating, Continence) | select + text | Partially — `ADL Assistance Required` is required as a single group-level field, not per-ADL-item | `[REPOSITORY-DISCOVERED]` `functionalStatus.adlAssistanceRequired` (`clinical_note_validation_engine.py:494-501`); per-ADL-item requirement `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| ECOG Performance Status | numeric 0-4 + label | **[LOCKED PRODUCT DECISION]** conditionally visible (diagnosis-gated), **no confirmed backend Lock requirement** | `[OPEN DEFECT]` — restated from prior discovery: ECOG has no entry in `RN_ICA_REQUIRED_FIELD_GROUPS` and is not named in `_validate_required_functional_assessments`'s dementia/cardiac branches |
| FAST scale | select | **[LOCKED PRODUCT DECISION]** visible only if dementia-related diagnosis; **[REPOSITORY-DISCOVERED]** compliance-blocking when `dementia_related` is true | `clinical_note_validation_engine.py:1112-1116, 1234+` |
| NYHA class | select | **[LOCKED PRODUCT DECISION]** visible only if cardiac-related diagnosis; **[REPOSITORY-DISCOVERED]** compliance-blocking when `cardiac_related` is true | `clinical_note_validation_engine.py:1117-1121, 1255+` |
| "FAST/NYHA not applicable based on diagnosis" advisory banner | read-only | No | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |

## Screen 4 — Pain & Symptom Burden

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| Pain Screening (`pain.verbalizesPain` / `pain.pain_score`) | boolean/numeric | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Pain Screening"]` (`clinical_note_validation_engine.py:459-466`) |
| Pain Pattern / Severity / Management / Findings | text/select | Not independently confirmed beyond `Pain Screening` | `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Symptom Impact items (J2051 A-H: dyspnea, anxiety, nausea, vomiting, diarrhea, constipation, agitation) | select | Not confirmed in `RN_ICA_REQUIRED_FIELD_GROUPS`; HOPE mapping confirmed separately in prior session discovery | `[REPOSITORY-DISCOVERED]` HOPE J2051 mapping (per `SYMPTOM_IMPACT_CHECKLIST` in `RNICA.jsx`); Lock-blocking status `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Respiratory Rate | numeric | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Respiratory Rate"]` (`clinical_note_validation_engine.py:467-474`) |
| Weight | numeric | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Weight"]` (`clinical_note_validation_engine.py:475-482`) |
| Appetite / Intake | select/text | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Appetite / Intake"]` (`clinical_note_validation_engine.py:483-490`) |
| Pain Findings / Recommendations (AI) | read-only, AI | No | `[REPOSITORY-DISCOVERED]`, governed by `RNICA_AI_GOVERNANCE.md` |

## Screen 5 — Diagnosis & LCD

Confirmed directly against the provided Diagnosis & LCD screenshot.

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| Primary Terminal Diagnosis (ICD-10 + description) | text/code | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Primary Diagnosis"]` (`clinical_note_validation_engine.py:381-389`) |
| Diagnosis Evidence Group / Category | select | No independent Lock rule confirmed | `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Secondary Diagnoses (ICD-10, onset, Hospice Related toggle) | list + boolean | Not confirmed | `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Active Comorbidities & Clinical Impact | text | Not confirmed | `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Disease Trajectory | text/select | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Disease Trajectory"]` (`clinical_note_validation_engine.py:407-415`) |
| LCD Supporting Evidence (narrative) | text | **Yes** — under the label "LCD Supporting Evidence," mapped to `diagnoses.lcdEligibilityNarrative` | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["LCD Supporting Evidence"]` (`clinical_note_validation_engine.py:390-397`) |
| LCD Supporting Narrative (character-counted textarea) | text (2000 char) | Same field as above, screenshot-confirmed | `[REPOSITORY-DISCOVERED]` |
| ADVISORY: LCD Eligibility Support panel | read-only, AI | No | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed — rules-engine advisory, not a certification |
| Clinical Narrative | — | **[LOCKED PRODUCT DECISION]: must NOT appear on this screen.** `finalization.clinicalNarrative` is the sole nurse-facing narrative (Screen 13 only) | Restated from `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`, not reopened |

## Screen 6 — Body Systems

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| Ten body-system sections (Neurological, Cardiovascular, Respiratory, Infection, GI, Nutrition, Endocrine, Genitourinary, Musculoskeletal, Skin/Wounds) | per-system structured fields | **Not required as a full Review-of-Systems set for RN ICA** — `_validate_required_ros` explicitly returns early (skips) for RN ICA notes | `[REPOSITORY-DISCOVERED]` `clinical_note_validation_engine.py:826-831` (`if is_rn_ica: return`) |
| Cognitive Decline (Neurological) | boolean/text | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Cognitive Decline"]` |
| Mobility Decline (Musculoskeletal-adjacent) | boolean/text | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Mobility Decline"]` |
| Imminent Death, SFV | structured fields | **Yes (SFV)** — confirmed as a hard Lock blocker in the Finalization screenshot ("SFV Assessment Missing... Supportive Care Plan (SFV) documentation is a state compliance lock") | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed; exact backend path `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Clinical/Missing/Safety Findings (AI) | read-only, AI | No | `[REPOSITORY-DISCOVERED]`, governed by `RNICA_AI_GOVERNANCE.md` |

## Screen 7 — Caregiver & Support

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| Caregiver assessed / no-caregiver state | boolean + conditional reason | **[DESIGN REQUIREMENT]** no-caregiver reason required when no caregiver documented (restated from `RNICA_WORKFLOW_AUTHORITY_MAP.md`) | `[IMPLEMENTATION DISCOVERY REQUIRED]` — not present in `RN_ICA_REQUIRED_FIELD_GROUPS`; verify at implementation time |
| Psychosocial / Spiritual / Personal Care / Teaching Needs | structured fields | Not confirmed in the 17-item required list | `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Caregiver Risk / Support Risk / Teaching Recommendations (AI) | read-only, AI | No | `[REPOSITORY-DISCOVERED]`, governed by `RNICA_AI_GOVERNANCE.md` |

## Screen 8 — Safety & Clinical Risk

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| Fall Risk | numeric/derived | Not confirmed in the 17-item required list (Morse score itself is `[IMPLEMENTATION DISCOVERY REQUIRED]`, see Screen 3) | `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Safety Issues / Behavior Risks / Cognitive Risks | structured fields | Cognitive Decline is required (shared with Screen 6) | `[REPOSITORY-DISCOVERED]` (see above) |
| Imminent Death Indicators | structured fields | Shared with Screen 6 SFV/Imminent Death | `[REPOSITORY-DISCOVERED]` |
| AI Risk Findings / Suggested Actions | read-only, AI | No | `[REPOSITORY-DISCOVERED]`, governed by `RNICA_AI_GOVERNANCE.md` |

## Screen 9 — ACP & Goals of Care

**Correction to a prior document's characterization:** an earlier
companion document referred to "six ACP hard-required fields." Direct
re-verification against `RN_ICA_REQUIRED_FIELD_GROUPS` in this pass
confirms only **three** ACP-labeled entries in the authoritative
required-field list. This matrix uses the verified three; the other
ACP fields below (Advance Directives, POA, Decision Maker) are real UI
fields but their Lock-blocking status is not confirmed in this list and
is flagged accordingly. `RNICA_WORKFLOW_AUTHORITY_MAP.md` is not edited
to reflect this correction per the standing instruction not to reopen it
— this matrix is the corrected reference going forward.

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| Code Status | select | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Code Status"]` (`clinical_note_validation_engine.py:436-443`) |
| Life-Sustaining Treatment Preference | select | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Life-Sustaining Treatment Preference"]` (`clinical_note_validation_engine.py:444-451`) |
| Hospitalization Preference | select | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Hospitalization Preference"]` (`clinical_note_validation_engine.py:452-458`) |
| CPR Preference | select | Not a separate entry in the required list — may be folded into Code Status | `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Advance Directives | boolean/text | Not confirmed | `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| POA Information / Decision Maker | text | Not confirmed | `[IMPLEMENTATION DISCOVERY REQUIRED]` |

## Screen 10 — Orders & POC

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| Plan of Care Narrative | text | **Yes** | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Plan of Care Narrative"]` (`clinical_note_validation_engine.py:509-517`) |
| Problems / Goals / Interventions | structured, POC-model-backed | Governed by POC completeness/`poc_review_gate.py`, not this list directly | `[REPOSITORY-DISCOVERED]` `PATIENT_CHART_AUTHORITY_MAP.md` POC section |
| Orders | structured, Physician-Order-model-backed | Governed by Physician Orders workspace | `[REPOSITORY-DISCOVERED]` |
| Suggested Orders (AI) | read-only, AI, action-gated | No — advisory only, never auto-creates orders | `[REPOSITORY-DISCOVERED]`, governed by `RNICA_AI_GOVERNANCE.md` |
| POC Readiness / POC Findings | read-only, derived | Feeds Screen 11 | `[REPOSITORY-DISCOVERED]` |

## Screen 11 — Compliance & Readiness

Aggregation screen. All fields here are read-only mirrors of rules
already defined by other screens and by `RNICA_LOCK_READINESS_MATRIX.md`.
No field on this screen independently blocks Lock; it displays the
aggregate `compliance_blocking_items` list produced by
`validate_and_trigger_incident` (`clinical_note_validation_engine.py`).

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| Blocking issue list | read-only, aggregated | n/a — mirrors other screens | `[REPOSITORY-DISCOVERED]` `ValidationResult.compliance_blocking_items` |
| Warnings / advisory list | read-only, aggregated | n/a | `[REPOSITORY-DISCOVERED]` `ValidationResult.warnings` |

## Screen 12 — AI Action Center

Confirmed directly against the provided AI Action Center screenshot.

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| "AI analysis last refreshed... updates on Load, Save, and Lock" banner | read-only | No | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed — direct product evidence of the refresh-trigger rule in `RNICA_AI_GOVERNANCE.md` |
| Advisory Findings (Documented Findings Requiring Review, Missing Evidence, Documentation Gaps, Compliance Signals) | read-only, AI | No | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |
| "Advisory Findings — For Clinician Review Only" disclaimer, "AI does not generate narratives, definitive prognoses, or physician certifications" | read-only, static compliance text | No — but must never be removed or weakened | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed; governed by `RNICA_AI_GOVERNANCE.md` |
| Suggested Follow-Up items, each labeled "SUGGESTION (NOT MANDATED)" | read-only, AI | No | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |
| LCD Supporting Evidence summary ("5 of 5 criteria met") | read-only, AI-adjacent | No — advisory, not the LCD narrative field itself (Screen 5 owns that) | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |
| Readiness & Compliance summary (e.g., "9 of 13 complete," "2 items pending") | read-only, aggregated | n/a — mirrors Screen 11 | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |
| "Refresh AI Analysis" button | action | No | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |

## Screen 13 — Finalization

Confirmed directly against the provided Finalization screenshot.

| Field | Type | Required at Lock | Source |
|---|---|---|---|
| `finalization.clinicalNarrative` | text | **Yes** — "Final clinical narrative fully documented," shown RESOLVED in the readiness checklist | `[REPOSITORY-DISCOVERED]` `RN_ICA_REQUIRED_FIELD_GROUPS["Clinical Narrative"]`, path `finalization.clinicalNarrative` (`clinical_note_validation_engine.py:398-406`); this is the sole nurse-facing narrative per `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md` |
| Readiness Checklist (8 confirmed items in the screenshot: demographics/billing, clinical narrative, pain assessment, functional status HOPE/M-items, caregiver/support, safety/fall risk, SFV documentation, hospice active orders) | read-only, per-item RESOLVED/MISSING | Each item is an independent hard blocker when MISSING | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed; full backend mapping consolidated in `RNICA_LOCK_READINESS_MATRIX.md` |
| Right-rail "N BLOCKING ISSUES DETECTED" panel | read-only, aggregated | n/a — mirrors checklist | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |
| Clinician Certification & Signature (certifying clinician, credential state, attestation statement, "Sign Document" button) | text (read-only identity) + action | **Yes** — signature required before Lock | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |
| "Lock Assessment (Blocked)" button | action, disabled while blockers exist | n/a — the gate itself | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |
| Assessment Audit Logs (autosave, field updates, initialization) | read-only, append-only | n/a | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |

---

## Cross-Screen Field Corrections Log

This section exists so future engineers know which values in prior
companion documents were superseded by direct code re-verification
during this implementation pass, without editing those documents.

| Prior claim | Document | Correction |
|---|---|---|
| "Six ACP fields are hard-required with HOPE mappings" | `RNICA_WORKFLOW_AUTHORITY_MAP.md`, Screen 9 row | Only 3 ACP-labeled entries confirmed in `RN_ICA_REQUIRED_FIELD_GROUPS`: Code Status, Life-Sustaining Treatment Preference, Hospitalization Preference. Additional ACP fields (Advance Directives, POA, CPR Preference, Decision Maker) exist in the UI but their Lock-blocking status is `[IMPLEMENTATION DISCOVERY REQUIRED]`. |
