# RNICA_DOCUMENTATION_EXECUTION_MAP.md

**Status:** Execution map derived directly from the existing RNICA documentation
package under `docs/tenant-platform/`. This document does not introduce new
requirements; every row cites an existing controlling document. Where repo
code now exceeds a document's stated "current state," that drift is called
out explicitly rather than treated as a new decision.

## Controlling document precedence (as stated by the documents themselves)

1. **RNICA engineering authority — `RNICA_IMPLEMENTATION_AUTHORITY.md`**
   ("Approved implementation baseline (v2 — repository-validated)",
   supersedes v1).
2. **RNICA product/design intent — `RNICA_REDESIGN_SOURCE_OF_TRUTH.md`
   + `RNICA_WORKFLOW_AUTHORITY_MAP.md`** ("AUTHORITATIVE DESIGN INPUT. NOT
   IMPLEMENTATION AUTHORIZATION" — intent-controlling, not a standalone
   go-ahead).
3. **Per-screen / per-field binding matrices — `RNICA_SCREEN_AUTHORITY_MATRIX.md`,
   `RNICA_DATA_MAPPING_MATRIX.md`, `RNICA_LOCK_READINESS_MATRIX.md`,
   `RNICA_AI_GOVERNANCE.md`** (all "v2 — repository-validated").
4. **Narrative authority — `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`**
   (locked; explicitly supersedes `RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`
   and the "both fields stay" framing in `RNICA_NARRATIVE_PLACEMENT_DECISION.md`).
5. **Sequencing — `RNICA_PHASED_IMPLEMENTATION_PLAN.md` +
   `RNICA_GITHUB_HANDOFF_PLAN.md`** (documentation-only deliverables that
   define implementation order; they do not themselves authorize schema
   changes).
6. **Everything else** (`RNICA_CURRENT_TO_TARGET_GAP_REPORT.md`,
   `*_IMPACT_ANALYSIS.md`, `*_DEPENDENCY_MAP.md`, `*_SECTION_BREAKDOWN.md`,
   `RNICA_USABILITY_AND_AI_REVIEW.md`, `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`,
   `AI_VISIBILITY_MATRIX.md`) is supporting/discovery analysis, cited as
   corroboration, never as a source of new requirements.

**Repo-vs-doc drift confirmed during this pass:** ECOG backend enforcement
and 6-field ACP backend enforcement are now implemented in code
(`clinical_note_validation_engine.py`), while several supporting documents
still describe them as open/3-field. This is a documentation-currency gap,
not an unresolved product decision — see rows below.

## Document-to-code execution map

| Work item | Controlling document and section | Supporting documents | Existing component/service/API | Required change | Change type | Test requirement |
|---|---|---|---|---|---|---|
| 13-screen shell / navigator rollout | `RNICA_PHASED_IMPLEMENTATION_PLAN.md` Increment 1; `RNICA_GITHUB_HANDOFF_PLAN.md` §1 | `RNICA_IMPLEMENTATION_AUTHORITY.md`, `RNICA_WORKFLOW_AUTHORITY_MAP.md`, `RNICA_SCREEN_AUTHORITY_MATRIX.md` (global rule) | `RNICACommandWorkspace.jsx`, `rnicaThirteenScreenTaxonomy.js`, `RNICA.jsx` (`workspacePilot` branch) | Group existing modules under the 13 approved screens; add "Screen N of 13" indicator. | NAVIGATION | Screen-order regression; classic-view fallback unaffected. |
| Patient Story | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 1; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §1 | `RNICA_SCREEN_BY_SCREEN_EVIDENCE_MATRIX.md` | RNICA Intelligence rail, patient summary fetch in `RNICA.jsx` | Cross-cutting: navigate to existing read-only context (no new data authority) until a dedicated aggregation view is separately authorized. | PRESENTATION ONLY | Verify no writable/new data source is introduced. |
| Evidence & Intake | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 2; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §2 | `RNICA_DATA_MAPPING_MATRIX.md`, `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` | Legacy `demographics`, `vitals`, `referrals` modules | Reuse under Screen 2 grouping; preserve provenance. | COMPONENT REUSE | Route grouping test; no field/validation change. |
| Functional Status | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 3; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §3 | `RNICA_LOCK_READINESS_MATRIX.md` | `performanceStatus` module; `clinical_note_validation_engine.py` | Preserve PPS/KPS/FAST/NYHA/ECOG behavior under Screen 3. | COMPONENT REUSE | PPS/KPS/FAST/NYHA/ECOG parity tests (already passing, 9/9). |
| Pain & Symptom Burden | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 4; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §4 | `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` | `pain`, `symptomImpact` modules | Reuse under Screen 4; preserve HOPE J0900/J0915/J2051 derivation. | COMPONENT REUSE | Symptom-impact parity test. |
| Diagnosis & LCD | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 5; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §5 | `RNICA_DATA_MAPPING_MATRIX.md` | `diagnoses` module, LCD chain | Re-present under Screen 5; no eligibility reinterpretation. | COMPONENT REUSE | LCD/readiness regression; language audit. |
| Body Systems | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 6; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §6 | `RNICA_DATA_MAPPING_MATRIX.md` | 10 body-system modules | Group under Screen 6, unchanged mappings. | COMPONENT REUSE | No unmapped-field loss. |
| Caregiver & Support | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 7; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §7 | — | `caregiverAssessment`, `psychosocial`, `spiritual`, `bereavement`, `personalCare`, `teachingNeeds` | Group under Screen 7. | COMPONENT REUSE | Render parity across all Screen 7 modules. |
| Safety & Clinical Risk | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 8; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §8 | `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` | `safety`, `imminentDeath`, `sfv` modules | Group under Screen 8; preserve SFV/imminent-death logic. | COMPONENT REUSE | SFV trigger parity; no response-set change. |
| ACP & Goals of Care | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 9; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §9 | `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md` | `advancedCarePlanning` module; backend `RN_ICA_REQUIRED_FIELD_GROUPS` (6 fields) | Presentation regroup only; field set already implemented and enforced. | COMPONENT REUSE | 6-field ACP UI + backend requiredness parity (9/9 passing). |
| Orders & POC | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 10; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §10 | `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` | `admissionsOrder`, `ordersHub` modules; `rnica_poc_adapter.py` | Surface existing actions under Screen 10; ownership unchanged. | COMPONENT REUSE | Existing order/POC actions preserved. |
| Compliance & Readiness | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 11; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §11 | `RNICA_LOCK_READINESS_MATRIX.md` | `getRnicaFinalizationReadiness`; validation rail in `RNICACommandWorkspace.jsx` | Cross-cutting: navigate to Finalization + scroll to existing Validation rail. | PRESENTATION ONLY | Lock/readiness parity against existing backend response. |
| AI Action Center | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 12; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §12 | `RNICA_AI_GOVERNANCE.md`, `AI_VISIBILITY_MATRIX.md` | `getRnicaIntelligence`; RNICA Intelligence rail | Cross-cutting nav today; full governed Screen 12 parity (freshness/unavailable-state/audit) remains open — see AI section below. | AI IMPLEMENTATION (partial) | Freshness banner test, unavailable-state test, applied/dismissed audit-event test. |
| Finalization | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 13; `RNICA_SCREEN_AUTHORITY_MATRIX.md` §13 | `RNICA_LOCK_READINESS_MATRIX.md`, `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md` | `finalization` module; lock/amendment/audit UI; `AmendmentPanel` | Keep as sole narrative/attestation/lock/amendment/audit surface. | UI WIRING | Lock/signature/amendment/audit regression. |
| ECOG backend enforcement | `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md` (ECOG item) | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 3, `RNICA_LOCK_READINESS_MATRIX.md` | `clinical_note_validation_engine.py`, `eligibility_evidence_registry.json`, `test_rnica_functional_assessment_governance.py` | None — already implemented and tested this session. | COMPLETE | 9/9 passing; keep regression green. |
| ACP six-field enforcement parity | `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md` | `RNICA_SCREEN_AUTHORITY_MATRIX.md` §9 | `clinical_note_validation_engine.py`, `RNICA.jsx` | None functionally — code already at 6-field target; doc's "current state" language is stale (HOPE-label/response-set/release-rule confirmations remain doc-level open items, not implementation gaps). | COMPLETE (doc update recommended) | 9/9 passing; keep regression green. |
| Fall Risk/Morse lock-blocking status | `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md` | `RNICA_LOCK_READINESS_MATRIX.md` | Safety/readiness surfaces | Do not make Fall Risk/Morse a lock blocker (product decision already confirmed this session as advisory-only). | COMPLETE | No blocker regression introduced. |
| AI freshness / stale-state / unavailable-state honesty | `RNICA_AI_GOVERNANCE.md`, `AI_VISIBILITY_MATRIX.md` | `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` Screen 12 | Intelligence panel empty/error states in `RNICA.jsx` | Add explicit "last refreshed"/stale-after-edit and honest "not connected/unavailable" states; never fabricate. | AI IMPLEMENTATION | Freshness banner test, stale-after-edit test, unavailable-state test. |
| AI recommendation applied/dismissed audit event | `RNICA_AI_GOVERNANCE.md` | `RNICA_PHASED_IMPLEMENTATION_PLAN.md` | `harvest_service.py`, `icaAssessments.ts` review calls | Add a discrete audit-log event for AI apply/dismiss (currently only `review_status` metadata is persisted). | AI IMPLEMENTATION | Audit-log emission test. |
| Historical `narrativeReviewed` lock defect | `RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md` (STATUS: OPEN) | `RNICA_CLINICAL_NARRATIVE_REWIRING_MAP.md`, `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md` | Readiness check in `rnica_finalization_service.py`; dead diagnosis narrative UI in `RNICA.jsx` | Repoint/retire the stale `narrativeReviewed` gate so historical records aren't unfixably blocked. | VALIDATION DEFECT (open, separate from Phase B) | Fixture-based regression for historical blocked/unblocked records. |

## AI workstream status (confirmed from code + docs)

- **Recommendations are real and backend-generated**, not fabricated:
  `GET /visits/rnica/{id}/intelligence` → `rnica_intelligence.py`, output
  mode `"recommendation_only"` — deterministic rules engine over persisted
  RNICA content + evidence, not an LLM/hidden generator.
- **Apply**: saves the assessment, writes candidate values into form state,
  then marks the source signal `APPLIED` via `reviewHarvestedSignal`
  (`icaAssessments.ts`, `harvest_service.py`). The backend review call
  records disposition metadata only — it does not itself mutate clinical
  data.
- **Dismiss**: records `DISMISSED` review-status metadata only; never
  mutates RNICA/chart data.
- **Missing today** (documented, not yet built):
  1. Dedicated, fully-governed Screen 12 AI Action Center presentation
     (currently a rail/panel pattern, not a standalone screen).
  2. Visible "last refreshed" / stale-relative-to-unsaved-edits indicator.
  3. Discrete audit-log event for AI recommendation applied/dismissed
     (only generic review-status metadata exists today).
  4. Honest "not connected / unavailable" state — today only generic
     empty (`"Save the assessment to generate..."`) and error
     (`"Unable to load RN ICA intelligence."`) states exist.
  5. Governance-specific tests asserting no prohibited/overclaiming
     language.
- **Not a real gap**: continuous keystroke-driven AI refresh, a generative
  "Patient Story" narrative engine, CTI/F2F/Survey Readiness/Explanation
  Engine AI — none of these are approved-but-unbuilt; they are explicitly
  out of scope per `RNICA_AI_GOVERNANCE.md`/`AI_VISIBILITY_MATRIX.md`.

## Phased order confirmation

`RNICA_GITHUB_HANDOFF_PLAN.md` and `RNICA_PHASED_IMPLEMENTATION_PLAN.md`
both name **Increment 1 — Shell, routes, navigation, shared patient header,
responsive framework** as the next step, consistent with the 13-screen
shell already in progress in this session.
