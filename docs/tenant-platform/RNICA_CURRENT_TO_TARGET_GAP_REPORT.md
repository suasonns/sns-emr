# RNICA_CURRENT_TO_TARGET_GAP_REPORT.md

**Status:** Required deliverable per handoff instruction. Repository-verified
this pass (direct grep/view of `RNICA.jsx`, `visits.py`,
`clinical_note_validation_engine.py`, `icaAssessments.ts`,
`useAssessmentAutosave.ts`, `eligibility.ts`, plus 16+ backend test files).
**Rule:** No implementation estimate or code plan is approved by this
report. This report only classifies distance between current repository
behavior and the approved 13-screen target.

## Classification taxonomy (as specified)

- **A — Already implemented and reusable**
- **B — Implemented but requires presentation rewiring**
- **C — Implemented but defective**
- **D — Not implemented, presentation-only**
- **E — Not implemented, requires API/service work**
- **F — Not implemented, requires schema work**
- **G — Blocked by compliance or authority decision**

## Per-screen classification

### 1. Patient Story
- **B** — All source data (facesheet, diagnoses, decline evidence,
  caregiver context, Intelligence) already exists and is reachable via
  existing APIs (`fetchPatientSummary`, `fetchFacesheet`,
  `getRnicaIntelligence`). No new backend/service work identified. The gap
  is a presentation-layer aggregation component that does not exist yet.

### 2. Evidence & Intake
- **B** — Structured Findings review/apply/provenance pipeline is fully
  built (`applyStructuredFindings.js`, `reviewHarvestedSignal`,
  `batchReviewHarvestedSignals`, tested in 5 backend test files). Referral/
  facesheet/vitals data already exists in legacy modules. Gap is
  presentation-only: no dedicated "Evidence & Intake" screen exists;
  content is interleaved across legacy `demographics`/`vitals`/`referrals`.

### 3. Functional Status
- **B** for PPS/KPS/FAST/NYHA — fields, server validation, and HOPE
  mapping all confirmed implemented; conditional visibility for FAST/NYHA
  is a presentation-layer rule to implement against already-validated
  diagnosis data.
- **C** for ECOG — the field/UI exists (visible in the product screenshot)
  but has **no** corresponding server enforcement branch in
  `_validate_required_functional_assessments`. This is implemented-but-
  defective, not merely a presentation gap: the Lock gate silently never
  enforces ECOG even when it should be diagnosis-conditional-required.

### 4. Pain & Symptom Burden
- **B** — Pain scales (Numeric/PAINAD/FLACC components), symptom impact
  checklist (HOPE J2051 A-H), and SFV status derivation all confirmed
  implemented.
- **C** (carried forward, not re-verified this pass) — J2050 misplacement
  and J2051 SFV-trigger source mismatch, per the earlier (still-relevant)
  `SNS_RNICA_GAP_VALIDATION_2.0.md` findings. Flagged for re-verification
  before implementation, not assumed resolved.

### 5. Diagnosis & LCD
- **B** — `detectLCD`/`evaluateLCD`/`getLCDConfig` and
  `buildClientLcdFacts()` are fully built and wired; the criteria-match
  response structure already avoids an eligibility verdict shape. Gap is
  presentation/language enforcement only (apply the evidence-support
  terminology in `RNICA_AI_GOVERNANCE.md` §5 uniformly), plus confirming
  no UI copy currently uses prohibited "Eligible"/"LCD match" language —
  **not verified this pass** (`[IMPLEMENTATION DISCOVERY REQUIRED]`,
  should be checked with a targeted string search before implementation).

### 6. Body Systems
- **B** — All ten body-system modules exist (`RNICA_BODY_SYSTEM_MODULES`)
  and feed both LCD facts and (per prior, unverified-this-pass, `RNICA_
  CERTIFICATION_PACKAGE.md`) Structured Findings for most fields.
- **E** (carried forward from `RNICA_CERTIFICATION_PACKAGE.md`, not
  re-verified this pass) — 43 previously-catalogued auto-populatable
  clinical fields (Skin/Wounds detail, GU catheter detail, GI device/output
  detail, endocrine insulin detail, CV edema pitting, respiratory
  ventilator settings) remain unmapped to Structured Findings concepts.
  This requires concept-registry/service work, not presentation work, if
  still current — flag for re-verification, do not assume resolved or
  unresolved without a fresh check.

### 7. Caregiver & Support
- **B** — Psychosocial/spiritual/bereavement/personal-care/teaching-needs
  modules exist. No derived caregiver-burden scoring exists anywhere in
  the repository (confirmed absent, consistent with the prohibition in
  `RNICA_SCREEN_AUTHORITY_MATRIX.md` §7 — this is compliant by omission,
  not a gap to fill).

### 8. Safety & Clinical Risk
- **B** — Safety and Imminent Death modules exist.
- **G** — Fall Risk/Morse score's Lock-blocking status is shown in the
  product screenshot but is not in the confirmed 17-item hard-required
  list. Until product/compliance authority confirms whether Morse scoring
  is intended as a hard Lock blocker, implementation of blocking behavior
  around it is blocked by an authority decision, not a code gap.

### 9. ACP & Goals of Care
- **C** — A prior document (`RNICA_WORKFLOW_AUTHORITY_MAP.md`, not
  reopened) stated "six ACP hard-required fields"; direct re-verification
  of `RN_ICA_REQUIRED_FIELD_GROUPS` found only 3 (Code Status,
  Life-Sustaining Treatment Preference, Hospitalization Preference).
  Advance Directives, POA, CPR Preference, and Decision Maker either (a)
  exist as optional/soft fields today, or (b) do not exist as RNICA fields
  at all — this distinction was not resolved this pass and is
  implemented-but-possibly-defective relative to the approved design
  intent, pending discovery.

### 10. Orders & POC
- **A** — The POC adapter (`rnica_poc_adapter.py`, `rnica_poc.py`) fully
  implements add/update/resolve/link/merge/deactivate/view operations
  against the authoritative POC domain, with explicit-action-only
  semantics confirmed (no auto-generation at Lock). Directly reusable as-is
  behind the new screen.

### 11. Compliance & Readiness
- **A** — `getRnicaFinalizationReadiness` already returns the exact
  structure the server Lock gate enforces (same function,
  `evaluate_finalization_readiness`). This is the strongest "already
  implemented and reusable" case in the whole package: the new screen is a
  presentation layer over an endpoint that already guarantees UI/server
  parity by construction.

### 12. AI Action Center
- **B** — `getRnicaIntelligence` and Structured Findings both exist and
  are advisory-shaped. Confirmed Load/Save/Lock-only trigger pattern (no
  live-typing refresh found). Gap is presentation (a dedicated Action
  Center screen) plus one confirmed missing piece:
- **E** — No dedicated audit event was found for "AI recommendation
  applied" / "AI recommendation dismissed" as distinct from the generic
  Structured Findings `review_status` persistence. If a discrete audit
  event is required by `RNICA_AI_GOVERNANCE.md` §8, this is backend
  service work, not presentation work.

### 13. Finalization
- **B** for narrative/signature/lock/amendment plumbing — all confirmed
  implemented (`finalization.clinicalNarrative`,
  `finalization.signatureCertification`, `finalization.clinicianSignature`,
  Lock endpoint, amendment endpoints, audit event).
- **C** — `record.status = "DRAFT"` resets unconditionally on every
  non-locked `PUT`, including trivial autosave ticks
  (`visits.py:1118`). This is a confirmed, still-present defect
  predating this session's involvement, not new design intent.

## Cross-cutting classification

| Item | Class | Basis |
|---|---|---|
| 13-screen navigation shell | **D** | Confirmed: only the legacy 28-module `NAV_SECTIONS`/`LEGACY_ROUTES` structure exists; no 13-screen router/nav found anywhere |
| Autosave (30s interval) | **A** | Fully implemented, `useAssessmentAutosave.ts` |
| Lock/readiness parity | **A** | Same function backs both UI and server gate |
| Locked-record 423 protection | **A** | Confirmed on PUT and DELETE |
| `status`→`DRAFT` reset-on-update | **C** | Confirmed still present |
| Amendment workflow | **A** | Confirmed model + service + 4 endpoints + tests |
| POC adapter / explicit-action-only | **A** | Confirmed, plus explicit no-autogen decision doc |
| Structured Findings review/provenance | **A** | Confirmed, 5 backend test files + 1 frontend test file |
| LCD evidence engine (non-verdict) | **A** | Confirmed shape; UI copy audit for prohibited language **not done** this pass |
| ECOG Lock enforcement | **C** | Confirmed missing enforcement branch |
| AI recommendation audit event | **E** | Not found; needs service work if required |
| Fall Risk/Morse Lock-blocking status | **G** | Needs authority decision before classification as A-F is possible |
| ACP hard-required field count (3 vs. "six") | **C** | Confirmed discrepancy between prior document and code; needs authority reconciliation, not code, first |

## Items explicitly marked `[IMPLEMENTATION DISCOVERY REQUIRED]` (not resolved this pass)

1. Pain-reassessment/24h-follow-up gate — exact server validator distinct
   from base Pain Screening field, not isolated.
2. SFV documentation's server-side Lock-blocking enforcement path (client
   derivation confirmed; server enforcement not isolated).
3. Whether `finalization.signatureCertification`/`clinicianSignature` are
   hard Lock blockers distinct from the general readiness check, or merely
   captured/logged.
4. UI-copy audit for prohibited LCD/eligibility language across the
   current `RNICA.jsx` LCD panel.
5. Whether the 43 previously-catalogued unmapped Structured Findings
   fields (`RNICA_CERTIFICATION_PACKAGE.md`) remain unmapped today, or have
   since been resolved — needs a fresh pass, not assumed either way.
6. Whether HOPE J2050/J2051 wiring defects (`SNS_RNICA_GAP_VALIDATION_2.0.md`)
   remain present today.

## Summary

Of the 13 screens: **1 (Orders & POC) and 1 (Compliance & Readiness)** are
directly reusable presentation targets over already-correct backend logic
(**A**). **9 screens** need presentation rewiring only, over already-
implemented data/validation (**B**). **3 confirmed defects** exist
(ECOG enforcement, `status`-reset bug, ACP field-count discrepancy) that
must be fixed or reconciled, not designed around (**C**). **1 item**
(Fall Risk/Morse blocking) is blocked pending an explicit compliance/
authority decision (**G**). No screen in this pass was classified **F**
(requires schema work) — all approved target behavior maps to existing
JSONB `form_data` fields or existing dedicated tables (amendments, POC).
This is a materially better starting position than the phrase "13-screen
redesign" implies: the primary missing piece is the navigation shell
itself (**D**), not the underlying clinical logic.
