# RNICA Experience Implementation Plan

**"Preserve the Engine. Simplify the Experience."**

**STATUS: PLANNING ONLY — NO CODE — NO SCHEMA — NO MIGRATIONS**

This is a planning document only. It defines *what a future, separately
authorized implementation would need to do* to simplify the RNICA
experience while preserving every existing engine (HOPE, POC, SFV,
validation, structured findings, audit, autosave/lock). No implementation
begins from this document. It depends on and cross-references
`RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`, `AI_VISIBILITY_MATRIX.md`,
`RNICA_SYSTEM_DEPENDENCY_MAP.md`, `RNICA_UI_DEPENDENCY_MAP.md`,
`RNICA_REDESIGN_IMPACT_ANALYSIS.md`, and
`RNICA_USABILITY_AND_AI_REVIEW.md` (all in this directory).

> **ARCHITECTURAL CORRECTION NOTICE — see `RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`:**
> The Owner has locked a product decision that `diagnoses.clinicalNarrative`
> was incorrectly placed and must not remain a nurse-facing narrative input in
> the redesigned RNICA; `finalization.clinicalNarrative` is the sole
> authoritative future Clinical Narrative. Any plan content below that treats
> both narrative fields as permanent parallel inputs must be read in light of
> that correction.

---

## Phase 2 — Simplification Without Removal

**Rule: nothing is removed; everything is reorganized.**

The 27 existing RNICA sections (`RNICA.jsx:164-192`) are not eliminated,
renamed at the data layer, or reduced in required-field count. A future
presentation layer could regroup them for navigation purposes only:

| Future presentation group | Underlying sections retained unchanged |
|---|---|
| 1. Patient Story | New presentation layer only — see Phase 4; does not replace any section, draws from existing data (demographics, diagnoses, facesheet context) |
| 2. Evidence & Intake | Patient Demographics, Vitals, Referrals |
| 3. Clinical Assessment | Pain Assessment, Symptom Impact, Diagnoses, Performance Status, the 10 body-system sections, Imminent Death, SFV |
| 4. Caregiver & Support | Caregiver Assessment (nested), Psychosocial, Spiritual, Personal Care, Teaching Needs |
| 5. Safety & Risk | Safety, Bereavement (risk-adjacent items) |
| 6. Compliance & Readiness | Advanced Care Planning (nested), Admissions Order, Certifications-adjacent finalization prerequisites |
| 7. Final Review | Finalization (signature, attestation, lock) |

**Constraint carried forward from `RNICA_UI_DEPENDENCY_MAP.md` and
`RNICA_REDESIGN_IMPACT_ANALYSIS.md`**: regrouping is a navigation/label
change only. Every field key, validation rule, and endpoint call listed in
those documents as COMPLIANCE CRITICAL, WORKFLOW CRITICAL, or DO NOT TOUCH
must remain wired exactly as-is under the new grouping.

---

## Phase 4 — Patient Story Layer (Planning)

**Current state**: no "Patient Story" capability exists anywhere in the
repository (`RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` — NOT FOUND / NOT
BUILT). This is genuinely new scope, not a re-surfacing of hidden
functionality.

A future Patient Story layer would need to source each element from
existing data, without inventing new backend authorities:

| Patient Story element | Proposed data source (existing) | Status |
|---|---|---|
| Why Hospice | `diagnoses.primaryDiagnosis`, `diagnoses.diseaseTrajectory`, `diagnoses.clinicalNarrative` | Data exists; no story-layer aggregation exists yet |
| Primary Diagnosis | `diagnoses.primaryDiagnosis` | Data exists |
| Hospitalization Summary | Admission/facesheet context (`admission_id`, patient summary) | Data exists elsewhere; not aggregated into a "summary" view for RNICA |
| Caregiver Summary | `demographics.pcg` fields + caregiver-related Intelligence recommendation text | Data exists but unlabeled (see AI_VISIBILITY_MATRIX §3) |
| Current Risks | Intelligence panel findings (`rnica_intelligence.py:184-222`) | Data exists |
| Clinical Summary | Aggregation of body-system findings | Data exists per-section; no single-summary aggregation exists yet |
| AI Summary | Intelligence panel `summary` field | Data exists |
| Missing Information | Intelligence panel `missing_evidence` field | Data exists |

**Planning conclusion**: a Patient Story layer is achievable primarily as
a *new presentation aggregation* over already-existing fields and the
already-existing Intelligence output — it does not require new backend
authorities for most elements, except "Hospitalization Summary" and
"Clinical Summary," which would need new aggregation logic (not new source
data). This still requires a separate implementation authorization before
any code is written.

---

## Phase 5 — Action Center (Planning)

**Current state**: validation surfaces as passive error/warning maps
(`validateRNICA`, `RNICA.jsx:942-1102`) and a separate finalization
readiness checklist (`rnica_finalization_service.py:35-171`), each
rendered as its own list/alert.

A future Action Center would reorganize the *presentation* of these same
outputs into task-oriented buckets, using the same underlying logic:

| Action Center bucket | Existing source (unchanged) |
|---|---|
| My Next Actions | Aggregation of unmet `validateRNICA` errors + unmet finalization checks |
| Compliance Issues | HOPE-tagged warnings/errors (J0900, J2051, I0010, etc.) from `validateRNICA` |
| Billing Issues | **None currently exist for RNICA** — `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` confirms no billing-readiness connection; this bucket would be empty until/unless a future, separately authorized integration is built |
| Missing Information | Intelligence panel `missing_evidence` field |
| Suggested AI Actions | Intelligence panel `recommendations` field |
| Ready To Complete | Finalization readiness checklist result (`ready: true/false`) |

**Same logic, different experience** — no validation rule, required field,
or finalization check is altered; only its grouping/labeling changes.

---

## Phase 6 — Nurse-First Automation (Planning)

| Automation candidate | Safe to automate? | Rationale |
|---|---|---|
| Auto Populate (Symptom Impact from body-system fields) | **Yes, already partially implemented** (`RNICA.jsx:10955-10992`) — blank-only fill, never overwrites manual entry; extending coverage is low-risk | Existing precedent |
| Auto Explanation | **Not currently possible** — no Explanation Engine exists (`RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`); would be new scope | New capability required |
| Auto Evidence Harvesting | **Already implemented**, just not independently surfaced (`gather_patient_evidence`) — no further automation needed, only visibility improvement | Existing |
| Auto Recommendations | **Already implemented** via Intelligence panel `recommendations` | Existing |
| Auto Verification | **Must remain clinician-driven** — signature certification attestation and clinician signature are compliance-required manual acts and must never be auto-checked (`rnica_finalization_service.py:102-116`) | Compliance-driven, not automatable |

**What should remain clinician-driven**: signature/attestation, clinical
narrative content and its "reviewed" confirmation, LCD narrative content,
referrals-reviewed confirmation, and any HOPE submission action.

**What should remain compliance-driven (not simplified away)**: all 21
hard-error fields, the 7 finalization readiness checks, and HOPE lifecycle
actions (full list in `RNICA_USABILITY_AND_AI_REVIEW.md` §6–7).

---

## Phase 7 — Redesign Protection

This reuses and confirms the classification already established in
`RNICA_UI_DEPENDENCY_MAP.md` and `RNICA_USABILITY_AND_AI_REVIEW.md` §7 —
no new classification work is introduced here; this section exists to
satisfy the requirement that every feature be classified in the context of
this specific implementation plan.

| Classification | Representative features |
|---|---|
| **VISUAL ONLY** | Section navigation labels, progress indicators, patient summary header layout |
| **WORKFLOW CRITICAL** | Manual Save, Lock button/flow, amendment request/approve/deny, POC-linked actions |
| **AI CRITICAL** | Intelligence panel data contract, LCD detect/config/eval chain, allergy/interaction checker |
| **BILLING CRITICAL** | **None** — confirmed no billing-critical RNICA element exists |
| **COMPLIANCE CRITICAL** | Diagnoses/LCD/narrative fields, PPS/KPS/treatment-preference fields, referrals-reviewed, signature certification, clinician signature, HOPE status/actions |
| **SYSTEM CRITICAL** | Lock endpoint call and its audit event, admission/tenant scoping |
| **DO NOT TOUCH** | Signature certification checkbox, clinician signature field, Lock button logic, amendment deny-reason requirement |

---

## Simplified Workflow Acceptance Criteria — Status

| Criterion | Status per current evidence |
|---|---|
| All 27 RNICA sections still exist | Not started (planning only); no section proposed for removal |
| HOPE still functions | Preserved by design — Phase 2 regrouping does not touch HOPE fields/actions |
| CTI still functions | N/A — CTI does not exist in RNICA today (nothing to regress) |
| F2F still functions | N/A — F2F does not exist in RNICA today (nothing to regress) |
| IDG still functions | N/A — no direct IDG-RNICA link exists today (nothing to regress) |
| POC still functions | Preserved by design — POC adapter contract untouched in this plan |
| HUV still functions | N/A — no RNICA-specific HUV surface exists today (nothing to regress) |
| SFV still functions | Preserved by design — SFV nav/trigger untouched |
| Validation engine still functions | Preserved by design — Phase 5 only regroups presentation, not logic |
| Structured findings still function | Preserved by design |
| Compliance review still functions | N/A for RNICA-specific dedicated review (does not exist); generic dashboard consumption unaffected |
| Billing readiness still functions | N/A — not connected to RNICA today (nothing to regress) |
| Lock workflow still functions | Preserved by design — DO NOT TOUCH |
| Autosave still functions | Preserved by design |
| Audit history still functions | Preserved by design — lock/amendment audit events untouched |
| Existing AI outputs still function | Preserved by design — Intelligence panel data contract untouched; only refresh-trigger *frequency* is candidate for future improvement (separate authorization) |
| No regression in survey readiness | N/A — does not exist today |
| No regression in billing readiness | N/A — does not exist today (nothing to regress) |

---

## Nurse-First Acceptance Criteria — Status

| Criterion | Status |
|---|---|
| Nurse sees Patient Story first | Not started — requires Phase 4 (new presentation aggregation), separately authorized |
| Nurse sees AI Summary first | Not started — requires Phase 4/5 reordering |
| Nurse sees Missing Information first | Not started — requires Phase 5 (Action Center) |
| Nurse sees Compliance Risks first | Not started — requires Phase 5 |
| Nurse sees Billing Risks first | N/A — no billing risk data exists for RNICA to surface |
| Nurse knows what to do next without hunting | Not started — requires Phase 5 (My Next Actions) |
| AI recommendations are visible without Save/Lock | Not started — requires a refresh-trigger change to the Intelligence panel (separate authorization; documented as the root cause in `AI_VISIBILITY_MATRIX.md` §7) |
| Validation is actionable and understandable | Partially true today (messages are specific); presentation grouping improvement is Phase 5 |
| Duplicate entry opportunities documented | **Done** — Symptom Impact vs. body-system duplication documented in `RNICA_USABILITY_AND_AI_REVIEW.md` §1/§4 |
| Hidden backend capabilities surfaced | **Done (documented, not implemented)** — see `AI_VISIBILITY_MATRIX.md` §3–5 |

---

## AI Responsiveness Acceptance Criteria — Status

| Criterion | Status |
|---|---|
| Every AI feature inventoried | **Done** — `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`, `AI_VISIBILITY_MATRIX.md` |
| Every AI trigger documented | **Done** — `AI_VISIBILITY_MATRIX.md` §1 |
| Every AI output documented | **Done** — `AI_VISIBILITY_MATRIX.md` §1 |
| Every AI consumer documented | **Done** — `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` |
| Hidden AI outputs identified | **Done** — `AI_VISIBILITY_MATRIX.md` §3 |
| Backend-only AI identified | **Done** — `AI_VISIBILITY_MATRIX.md` §1 (Evidence Harvesting row) |
| Delayed AI identified | **Done** — LCD chain, `AI_VISIBILITY_MATRIX.md` §1 |
| Save-triggered AI identified | **Done** — Intelligence panel, `AI_VISIBILITY_MATRIX.md` §1 |
| Lock-triggered AI identified | **Done** — Intelligence panel re-refresh on lock, `AI_VISIBILITY_MATRIX.md` §1 |
| Live AI opportunities identified | **Done** — allergy/interaction checker cited as the working reference pattern, `AI_VISIBILITY_MATRIX.md` §2 |

**"Why does AI feel unresponsive?" — documented, evidence-based answer**:
see `AI_VISIBILITY_MATRIX.md` §7. In summary: the Intelligence panel is
refresh-gated on Save/Lock rather than live; the LCD signal requires three
sequential debounced network calls; and one working AI-adjacent feature
requires an undiscoverable manual trigger. This is a presentation/timing
issue, not a missing- or broken-capability issue.

---

## Final Success Test

**"If RNICA were redesigned tomorrow, can we preserve HOPE, CTI, F2F, IDG,
POC, HUV, SFV, Validation, Structured Findings, Billing Readiness,
Compliance Logic, Survey Readiness, and AI Intelligence while making the
experience dramatically simpler?"**

**Answer: YES**, with the following evidence-based qualification:

- HOPE, POC, SFV, Validation, Structured Findings, and AI Intelligence are
  real, wired capabilities whose data contracts and logic this plan does
  not alter — only their presentation/grouping (Phases 2, 5) and their
  refresh timing (a candidate future improvement, not yet authorized) are
  in scope.
- CTI, F2F, IDG, Billing Readiness, Compliance Logic (dedicated), and
  Survey Readiness **do not currently exist as RNICA-connected
  capabilities** (per `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`). "Preserving"
  them means confirming this plan does not accidentally imply their
  existence or remove any of the fragments that do exist (e.g. the
  signature-certification attestation, which is unrelated to CTI proper).
  There is nothing at risk of regression for capabilities that were never
  built.
- Every item classified DO NOT TOUCH, COMPLIANCE CRITICAL, WORKFLOW
  CRITICAL, or SYSTEM CRITICAL in `RNICA_UI_DEPENDENCY_MAP.md` and
  `RNICA_USABILITY_AND_AI_REVIEW.md` §7 remains untouched by every phase in
  this plan.

**This document authorizes planning only. No code, schema, migration,
API, or UI change occurs as a result of this document. A separate
Implementation Authorization Review is required before any phase begins
implementation.**
