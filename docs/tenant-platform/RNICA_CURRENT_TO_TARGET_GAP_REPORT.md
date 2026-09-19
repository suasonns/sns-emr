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

### 9. ACP & Goals of Care
- **C** — **Resolved this pass** (see `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md`):
  1. **Current state:** `RN_ICA_REQUIRED_FIELD_GROUPS` hard-enforces 3
     fields at Lock — Code Status, Life-Sustaining Treatment Preference,
     Hospitalization Preference (`clinical_note_validation_engine.py:
     380-517`).
  2. **Target authority:** 6 required ACP values — the 3 above plus CPR
     Preference / Life-Sustaining Treatment / Hospitalization Preference
     Discussion Status. Not reduced to 3.
  3. **Confirmed this pass:** all 3 discussion-status fields already exist
     in `form_data` (`cprPreferenceAskedStatus`, `lifeSustainingAskedStatus`,
     `hospitalizationAskedStatus`, `RNICA.jsx:398-406`) — no new
     schema/storage required. `lifeSustainingAskedStatus` is client-
     required (`RNICA.jsx:975-976`) but not server-enforced.
  4. **Gap classification:** current-to-target validation-rule gap
     (3 of 6 target fields server-enforced) — **C**, not a design question.
  5. **Still open before implementation:** HOPE-vs-SNS-internal labeling
     confirmation and response-set integrity check (see reconciliation
     decision §4-5) — Discovery Item 7 is resolved for field *existence*,
     not yet for HOPE-label/response-set confirmation.

### 8. Safety & Clinical Risk
- **B** — Safety and Imminent Death modules exist.
- **BLOCKED BY AUTHORITY DECISION** — Fall Risk/Morse Lock-blocking status.
  Governing rule: a documented, validated fall-risk instrument may retain
  its instrument-specific score/interpretation; RNICA must not invent a
  new aggregate risk-scoring engine; the result becomes a Lock blocker
  only if a controlling requirement or approved agency policy explicitly
  requires completion for the applicable assessment type. Until that
  authority is documented, this item must **not** be converted into a new
  hard Lock blocker based on Figma presentation alone, and must not be
  classified A-F.

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
| ACP hard-required field count (target 6, current 3) | **C** | Target authority stands at 6; repository enforces 3; not a design reduction — see Discovery Item 7 |
| Fall Risk/Morse Lock-blocking status | **BLOCKED BY AUTHORITY DECISION** | Do not classify A-F or convert to a Lock blocker until controlling requirement/agency policy is documented |

## Discovery items — full required treatment

Each item below must be resolved, in this structure, before its affected
implementation increment begins. No item may be filled with an assumption.

### 1. Pain-reassessment / 24h-follow-up gate
- **Exact unresolved question:** Is the pain-reassessment/24h-follow-up
  gate shown in the product screenshot ("Pain Reassessment Required")
  enforced by a distinct server validator, or is it a client-only /
  not-yet-server-enforced check?
- **Files/services inspected:** `clinical_note_validation_engine.py`
  (`RN_ICA_REQUIRED_FIELD_GROUPS`, base Pain Screening entry only).
- **Current repository behavior:** Base Pain Screening field is
  server-enforced; the time-boxed reassessment/follow-up condition was not
  isolated as a separate validator in this pass.
- **Target authority:** Pain & Symptom Burden screen must show this as a
  Compliance & Readiness blocker per the approved Figma baseline.
- **Conflict:** Possible — UI may show a blocker the server does not
  independently enforce.
- **Required decision:** Confirm whether a distinct backend check exists;
  if not, decide whether to add one before or during the Pain & Symptom
  Burden increment.
- **Test impact:** New blocker-parity test required either way.
- **Blocks implementation:** Yes, for Increment 4 (Pain & Symptom Burden)
  and Increment 11 (Compliance & Readiness parity).

### 2. SFV documentation server-side Lock enforcement
- **Exact unresolved question:** Does a server-side check block Lock when
  SFV documentation is missing, or is "SFV Assessment Missing" (seen in
  the product screenshot) purely a client-derived status?
- **Files/services inspected:** `src/intake/hopeReportMapper.js`
  (`getSfvStatus`, `getHopeAdmissionStatus` — client-side derivation
  confirmed); `clinical_note_validation_engine.py` (no matching SFV entry
  found in `RN_ICA_REQUIRED_FIELD_GROUPS`).
- **Current repository behavior:** Client-side derivation only, confirmed;
  server-side enforcement not isolated in this pass.
- **Target authority:** SFV is a compliance-critical blocker per prior
  approved documents (RNICA Screen-by-Screen Evidence Matrix).
- **Conflict:** Possible client/server blocker mismatch.
- **Required decision:** Confirm/add server-side enforcement before
  Increment 6 (Body Systems) or Increment 13 (Finalization) is built.
- **Test impact:** Client/server parity test required.
- **Blocks implementation:** Yes, for Increment 13.

### 3. Attestation/signature as distinct hard blockers
- **Exact unresolved question:** Are `finalization.signatureCertification`
  and `finalization.clinicianSignature` enforced as their own hard Lock
  blockers, or only captured/logged as audit metadata?
- **Files/services inspected:** `backend/app/api/visits.py`
  (`lock_rnica_assessment` — confirmed these fields are read into audit
  metadata; a distinct blocking check was not isolated from the general
  `evaluate_finalization_readiness` call).
- **Current repository behavior:** Confirmed captured at Lock; blocking
  status not isolated.
- **Target authority:** Both must be hard blockers per
  `RNICA_LOCK_READINESS_MATRIX.md` §3 (locked decision, unchanged).
- **Conflict:** None known, but unverified.
- **Required decision:** Confirm `evaluate_finalization_readiness`
  includes these as checks; if not, add them explicitly.
- **Test impact:** Signature/attestation-specific Lock-failure test
  required.
- **Blocks implementation:** Yes, for Increment 13.

### 4. UI-copy audit for prohibited LCD/eligibility language
- **Exact unresolved question:** Does any current `RNICA.jsx` LCD panel
  copy use prohibited language ("Eligible", "LCD match: high", "Satisfies
  LCD") that must be replaced with evidence-support language before or
  during Increment 5?
- **Files/services inspected:** `RNICA.jsx` `LcdEligibilityCard` component
  (structure reviewed; full string-literal audit not performed this pass).
- **Current repository behavior:** Unknown until a targeted string search
  is run.
- **Target authority:** `RNICA_AI_GOVERNANCE.md` §5 required/prohibited
  language list (locked decision).
- **Conflict:** Unknown until audited.
- **Required decision:** Run the audit before Increment 5 begins; replace
  any prohibited strings found.
- **Test impact:** Prohibited-language snapshot test (already required by
  `RNICA_AI_GOVERNANCE.md` §9) should be added at the same time.
- **Blocks implementation:** Yes, for Increment 5 (Diagnosis & LCD).

### 5. 43 previously-catalogued unmapped Structured Findings fields
- **Exact unresolved question:** Do the 43 fields catalogued in
  `RNICA_CERTIFICATION_PACKAGE.md` (Skin/Wounds, GU catheter, GI
  device/output, endocrine insulin, CV edema pitting, respiratory
  ventilator settings, HOPE Symptom Impact ×8) remain unmapped today, or
  have some since been resolved?
- **Files/services inspected:** `RNICA_CERTIFICATION_PACKAGE.md` (dated
  document, not re-verified against current `CONCEPT_REGISTRY` this pass).
- **Current repository behavior:** Not re-checked; treat the 43-field list
  as unverified-current, not as confirmed-current or confirmed-resolved.
- **Target authority:** All auto-populatable clinical fields should
  eventually have concept/apply wiring per the certification package's own
  completion rule.
- **Conflict:** None known; purely a currency question.
- **Required decision:** Re-run the `CONCEPT_REGISTRY` coverage check
  before Increment 6 (Body Systems) is scoped.
- **Test impact:** None until re-verified.
- **Blocks implementation:** Only affects field-completeness scope for
  Increment 6, not screen-shell delivery.

### 6. HOPE J2050/J2051 wiring defects
- **Exact unresolved question:** Do the J2050 (Symptom Impact ownership
  conflict) and J2051 (SFV-trigger source mismatch:
  `clinical_notes` vs. `form_data`) defects recorded in
  `SNS_RNICA_GAP_VALIDATION_2.0.md` remain present today?
- **Files/services inspected:** `SNS_RNICA_GAP_VALIDATION_2.0.md` (dated
  document, not re-verified against current
  `rnica_hope_workflow_service.py` this pass).
- **Current repository behavior:** Not re-checked this pass.
- **Target authority:** HOPE governance rule — RNICA is the sole
  authoritative source for HOPE reporting elements; no ownership conflict
  or trigger-source mismatch is permitted.
- **Conflict:** Unknown until re-verified.
- **Required decision:** Re-verify before Increment 4 (Pain & Symptom
  Burden) or Increment 6 (Body Systems) is scoped, whichever owns J2050.
- **Test impact:** HOPE-derivation parity test required if still present.
- **Blocks implementation:** Yes, for whichever increment owns Symptom
  Impact/SFV triggers, until re-verified.

### 7. ACP target 6-field set and controlling HOPE mappings — RESOLVED (partially)
- **Resolution:** See `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md`,
  created and committed as part of this pass.
- **Exact 6-field target (itemized):** CPR Preference Discussion Status,
  Code Status, Life-Sustaining Treatment Discussion Status, Life-
  Sustaining Treatment Preference, Hospitalization Preference Discussion
  Status, Hospitalization Preference.
- **Files/services inspected:**
  `clinical_note_validation_engine.py:380-517` (confirms only 3 Preference
  fields server-enforced today); `RNICA.jsx:398-410,975-985` (confirms all
  3 discussion-status fields already exist in `form_data` under
  `demographics.advancedCarePlanning.*`, mapped in-code to HOPE
  F2000-A/F2100-A/F2200-A, with `lifeSustainingAskedStatus` client-
  required but not server-enforced).
- **Current repository behavior:** 3 of 6 target fields server-enforced;
  all 6 target fields already exist in storage — **no schema work
  required**.
- **Target authority:** 6 required ACP values (approved target, does not
  reduce to 3) — confirmed unchanged by this resolution.
- **Conflict:** Confirmed gap (3 vs. 6 server-enforced); resolved as a
  build/enforcement gap, not a design conflict or schema gap.
- **Remaining open sub-items (still `[IMPLEMENTATION DISCOVERY REQUIRED]`,
  tracked in the reconciliation decision, §9):**
  1. Independent confirmation of the F2000-A/F2100-A/F2200-A HOPE mapping
     against official CMS guidance (currently only an in-code comment).
  2. Whether the current 3-value response set satisfies a required
     5-state model (missing/not-asked/declined/unable-to-respond/unknown).
  3. Client-side requiredness confirmation for `cprPreferenceAskedStatus`
     and `hospitalizationAskedStatus` (only `lifeSustainingAskedStatus`
     confirmed client-required).
  4. Final HOPE-vs-SNS-internal labeling decision for each of the 6
     fields.
- **Test impact:** New Lock-blocker tests for the 3 additional fields once
  the remaining sub-items are resolved.
- **Blocks implementation:** Field-existence discovery no longer blocks
  scoping; server-enforcement work for Increment 9 remains blocked on the
  4 remaining sub-items above.

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
