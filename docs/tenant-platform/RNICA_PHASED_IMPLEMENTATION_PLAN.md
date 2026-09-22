# RNICA_PHASED_IMPLEMENTATION_PLAN.md

**Status:** Documentation-only deliverable. Does not authorize application
code, schema, or migration changes. Application coding requires a separate,
subsequently approved pull request per increment.
**Depends on:** `RNICA_IMPLEMENTATION_AUTHORITY.md`,
`RNICA_SCREEN_AUTHORITY_MATRIX.md`, `RNICA_DATA_MAPPING_MATRIX.md`,
`RNICA_AI_GOVERNANCE.md`, `RNICA_LOCK_READINESS_MATRIX.md`,
`RNICA_GITHUB_HANDOFF_PLAN.md`, `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md`.

> **[PRODUCT-AUTHORITY UPDATE — 2026-09-22]** The final canonical RNICA
> screen navigation order is: 1 Patient Story, 2 Evidence & Intake,
> 3 Pain & Symptom Burden, 4 Diagnosis & LCD, 5 Functional Status, 6-13
> unchanged. See `RNICA_NAVIGATION_SPECIFICATION.md`. The "Increment N"
> numbers below describe implementation build sequencing, not final
> screen navigation position.

Each increment below reports, in order: Verified files/components/services
· Current reusable implementation · Presentation rewiring · Confirmed
defects · New API/service work · Schema impact · Migration impact ·
Ownership domains affected · Acceptance criteria · Automated test
requirements · Historical-record handling · Feature-flag/rollback
strategy · Dependencies/blockers.

**Cross-cutting historical-record handling rule (applies to every
increment unless the increment states otherwise):** no increment in this
plan rewrites, backfills, or re-evaluates existing signed/locked/amended
records against a new or changed rule. New validation, enforcement, or
presentation behavior applies prospectively to assessments created or
unlocked after the increment's approved release/flag activation.
Increments 3, 9, and 13 state their historical-record handling explicitly
because they introduce Lock-blocking behavior changes; the remaining
increments are presentation-only or additive and inherit this rule without
restating it, except where noted.

**Verified files/components/services** for increments not restating them
individually are the files already cited inline under "Current reusable
implementation" for that increment; Increment 9 below shows the full
citation-explicit pattern this plan follows once a defect/discovery item
is in scope.

---

## Increment 1 — Shell, routes, navigation, shared patient header, responsive framework

- **Current reusable implementation:** `RNICAPage.tsx` route mount point;
  `/visits/rnica` API base; existing patient-header/context sidebar
  (`PatientContextSidebar.jsx`).
- **Presentation rewiring:** Full replacement of `NAV_SECTIONS`/
  `LEGACY_ROUTES` (28-module legacy nav) with the approved 13-screen
  navigation. Legacy module list must not be recreated inside the new
  shell (per governance instruction).
- **Confirmed defects:** None specific to shell; inherits the `status`
  reset-to-`DRAFT` defect from Increment 13's scope if autosave fires
  during shell navigation.
- **New API/service work:** None expected — the shell reads/writes through
  existing `icaAssessments.ts` functions.
- **Schema impact:** None.
- **Migration impact:** None.
- **Ownership domains affected:** None (presentation only); must not
  duplicate ownership from Diagnosis & LCD, Body Systems, POC, Compliance,
  AI, or Finalization screens.
- **Acceptance criteria:** All 13 screens reachable; legacy 28-module nav
  removed from the active experience; existing autosave/lock/amendment
  behavior unaffected by navigation change.
- **Automated test requirements:** Navigation regression test (13 routes
  reachable); existing 16 backend + 1 frontend RNICA test files must still
  pass unmodified.
- **Feature-flag/rollback strategy:** Ship behind a feature flag; rollback
  restores legacy nav without data loss (no schema change involved).
- **Dependencies/blockers:** None. This increment can start first.

## Increment 2 — Patient Story and Evidence & Intake

- **Current reusable implementation:** `fetchPatientSummary`,
  `fetchFacesheet`, `getRnicaIntelligence`, Structured Findings
  review/apply/provenance pipeline (fully built, tested).
- **Presentation rewiring:** New read-only Patient Story aggregation
  component; new Evidence & Intake component consuming legacy
  `demographics`/`vitals`/`referrals` modules.
- **Confirmed defects:** None found for these two screens specifically.
- **New API/service work:** None identified.
- **Schema impact:** None.
- **Migration impact:** None.
- **Ownership domains affected:** None — both screens are read-only/
  aggregation per `RNICA_SCREEN_AUTHORITY_MATRIX.md` §1-2.
- **Acceptance criteria:** Patient Story shows no editable fields except
  navigation links; Evidence & Intake preserves external-source provenance.
- **Automated test requirements:** Presentation snapshot tests; provenance
  display test (data still traces to source).
- **Feature-flag/rollback strategy:** Same flag as Increment 1.
- **Dependencies/blockers:** Depends on Increment 1 (shell).

## Increment 3 — Functional Status and conditional scale logic

- **Current reusable implementation:** PPS/KPS/FAST/NYHA fields and server
  validation (`_validate_required_functional_assessments`).
- **Presentation rewiring:** Conditional visibility rules for FAST (dementia)
  and NYHA (cardiac) in the new screen shell; PPS/KPS always visible.
- **Confirmed defects:** ECOG has no server-side Lock-enforcement branch —
  must be fixed as part of this increment, not designed around.
- **New API/service work:** Add ECOG enforcement branch to
  `_validate_required_functional_assessments`, conditioned on oncology/
  metastatic/hematologic diagnosis, mirroring the existing FAST/NYHA
  pattern.
- **Schema impact:** None (ECOG field already exists in `form_data`).
- **Migration impact:** None.
- **Ownership domains affected:** Functional Status only.
- **Acceptance criteria:** FAST/ECOG/NYHA render only per locked
  conditional rules; hidden scales are not rendered as disabled/
  placeholder; ECOG now enforced server-side when applicable.
- **Historical-record handling:** New ECOG enforcement applies only to
  assessments created or unlocked after the flag activates; existing
  signed/locked assessments that lack ECOG (where it should have applied)
  are not retroactively invalidated or reopened.
- **Automated test requirements:** New backend test for ECOG conditional
  enforcement (mirrors existing FAST/NYHA tests); regression test that
  PPS/KPS remain always-required.
- **Feature-flag/rollback strategy:** ECOG enforcement change should ship
  behind its own flag, independent of the navigation flag, since it changes
  Lock behavior (a blocking change) not just presentation.
- **Dependencies/blockers:** Depends on Increment 1. The ECOG fix is
  independently shippable before the screen shell if desired.

## Increment 4 — Pain & Symptom Burden

- **Current reusable implementation:** `NumericPainScale`, `PAINADScale`,
  `FLACCScale`, `SYMPTOM_IMPACT_CHECKLIST` (HOPE J2051 A-H), SFV status
  derivation.
- **Presentation rewiring:** Consolidate `pain` + `symptomImpact` legacy
  modules into one screen.
- **Confirmed defects:** None newly confirmed this pass for this screen
  specifically (carried-forward J2050/J2051 items are tracked as Discovery
  Item 6, not yet re-verified).
- **New API/service work:** Contingent on Discovery Item 1 (pain-
  reassessment/24h-follow-up server enforcement) and Discovery Item 6
  (J2050/J2051 wiring) resolution — see below.
- **Schema impact:** None expected unless Discovery Item 6 requires a new
  field.
- **Migration impact:** None expected.
- **Ownership domains affected:** Pain & Symptom Burden; HOPE J2050/J2051
  ownership pending Discovery Item 6 resolution.
- **Acceptance criteria:** Screen presents pain/symptom fields from one
  place; Compliance & Readiness blocker for pain reassessment matches
  actual server enforcement (once Discovery Item 1 is resolved).
- **Automated test requirements:** HOPE-derivation parity test once
  Discovery Items 1 and 6 are resolved.
- **Feature-flag/rollback strategy:** Same flag as Increment 1 for
  presentation; any new server enforcement ships behind its own flag.
- **Dependencies/blockers:** **Blocked** on resolving Discovery Items 1 and
  6 (`RNICA_CURRENT_TO_TARGET_GAP_REPORT.md`) before server-enforcement
  work in this increment can be scoped precisely; presentation-only work
  can proceed in parallel.

## Increment 5 — Diagnosis & LCD

- **Current reusable implementation:** `detectLCD`/`evaluateLCD`/
  `getLCDConfig`, `buildClientLcdFacts()` — fully built, non-verdict
  response shape confirmed.
- **Presentation rewiring:** Apply evidence-support terminology uniformly;
  remove any prohibited language found by Discovery Item 4's audit.
- **Confirmed defects:** None confirmed this pass; Discovery Item 4 (UI
  copy audit) is unresolved, not a confirmed defect.
- **New API/service work:** None expected unless the copy audit finds
  logic (not just copy) using a prohibited verdict shape.
- **Schema impact:** None.
- **Migration impact:** None.
- **Ownership domains affected:** Diagnosis & LCD owns an LCD Supporting
  Narrative only — must not introduce a duplicate Clinical Narrative.
- **Acceptance criteria:** No prohibited language ("Eligible", "LCD match:
  high", "Satisfies LCD") appears anywhere in this screen; "Physician
  certification remains required" is always shown alongside LCD evidence.
- **Automated test requirements:** Prohibited-language snapshot test (also
  required by `RNICA_AI_GOVERNANCE.md` §9).
- **Feature-flag/rollback strategy:** Same flag as Increment 1.
- **Dependencies/blockers:** **Blocked** on Discovery Item 4 (UI-copy
  audit) before this increment can be marked complete.

## Increment 6 — Body Systems

- **Current reusable implementation:** `RNICA_BODY_SYSTEM_MODULES` (10
  systems); LCD-facts consumption; most fields feed Structured Findings.
- **Presentation rewiring:** Consolidate 10 systems + Imminent Death + SFV
  into one screen shell.
- **Confirmed defects:** RN ICA notes skip the generic ROS validator by
  design (`_validate_required_ros`, `if is_rn_ica: return`) — this is
  documented existing behavior, not a defect to fix.
- **New API/service work:** Contingent on Discovery Item 5 (43
  previously-catalogued unmapped Structured Findings fields) re-
  verification — if fields remain unmapped, concept/apply wiring work is
  required here, scope TBD until re-verified.
- **Schema impact:** None expected (fields already exist in `form_data`).
- **Migration impact:** None expected.
- **Ownership domains affected:** Body Systems; must not duplicate
  ownership assigned to Diagnosis & LCD, POC, Compliance, AI, or
  Finalization screens.
- **Acceptance criteria:** All 10 systems + Imminent Death + SFV reachable;
  clinically significant findings not hidden.
- **Automated test requirements:** Existing Structured Findings test suite
  (5 backend files) must still pass; new tests for any newly-wired
  concepts if Discovery Item 5 finds unresolved gaps.
- **Feature-flag/rollback strategy:** Same flag as Increment 1.
- **Dependencies/blockers:** Field-completeness scope depends on Discovery
  Item 5 re-verification; screen-shell delivery is not blocked by it.

## Increment 7 — Caregiver & Support

- **Current reusable implementation:** Psychosocial/spiritual/bereavement/
  personal-care/teaching-needs modules.
- **Presentation rewiring:** Consolidate into one screen.
- **Confirmed defects:** None found.
- **New API/service work:** None.
- **Schema impact:** None. **Migration impact:** None.
- **Ownership domains affected:** Caregiver & Support only. No derived
  burden/sustainability scoring may be introduced (confirmed none exists
  today — compliant by omission).
- **Acceptance criteria:** No new aggregate caregiver score appears
  anywhere in this screen.
- **Automated test requirements:** Presentation regression test.
- **Feature-flag/rollback strategy:** Same flag as Increment 1.
- **Dependencies/blockers:** Depends on Increment 1 only.

## Increment 8 — Safety & Clinical Risk

- **Current reusable implementation:** Safety and Imminent Death modules.
- **Presentation rewiring:** Consolidate into one screen.
- **Confirmed defects:** None found for this screen's existing fields.
- **New API/service work:** **None authorized.** Fall Risk/Morse
  Lock-blocking behavior is **BLOCKED BY AUTHORITY DECISION** — do not
  add a new hard Lock blocker for Fall Risk/Morse based on Figma
  presentation alone. A validated instrument may retain its
  instrument-specific score/interpretation; RNICA must not introduce a new
  aggregate risk-scoring engine.
- **Schema impact:** None. **Migration impact:** None.
- **Ownership domains affected:** Safety & Clinical Risk only.
- **Acceptance criteria:** Fall Risk/Morse score (if shown) displays its
  own validated instrument result only; it does not block Lock unless and
  until a controlling requirement or approved agency policy is documented
  and separately approved.
- **Automated test requirements:** Regression test confirming Fall
  Risk/Morse does not block Lock unless explicitly authorized in a future
  approved change.
- **Feature-flag/rollback strategy:** Same flag as Increment 1.
- **Dependencies/blockers:** **Blocked** on the Fall Risk/Morse authority
  decision before any Lock-blocking behavior may be added; screen-shell
  delivery without new blocking behavior is not blocked.

## Increment 9 — ACP & Goals of Care

- **Verified files/components/services:** `clinical_note_validation_engine.py:380-517`
  (server hard-required list); `RNICA.jsx:398-406` (ACP field declarations,
  including the previously-unmapped discussion-status fields);
  `RNICA.jsx:975-985` (client-side requiredness); `RNICA_ACP_SIX_FIELD_
  RECONCILIATION_DECISION.md` (resolves Discovery Item 7).
- **Current reusable implementation:** 3 of the 6 target ACP fields are
  already server-enforced at Lock (Code Status, Life-Sustaining Treatment
  Preference, Hospitalization Preference). **The other 3 target fields
  (CPR/Life-Sustaining/Hospitalization Discussion Status) already exist in
  `form_data`** under `cprPreferenceAskedStatus`, `lifeSustainingAskedStatus`,
  `hospitalizationAskedStatus` — confirmed no new schema/storage is
  required for the six-field target.
- **Presentation rewiring:** Consolidate ACP fields (currently scattered
  across `demographics`/`diagnoses`) into one dedicated screen.
- **Confirmed defects:** Current repository enforces 3 of the approved
  6-field ACP target — a current-to-target validation gap, not a design
  reduction. The approved 6-field target stands (see
  `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md`). Additionally,
  `lifeSustainingAskedStatus` is client-required but not server-enforced —
  an existing client/server parity gap independent of the 3-vs-6 question.
- **New API/service work:** Add server-side hard-required enforcement for
  `cprPreferenceAskedStatus`, `lifeSustainingAskedStatus`, and
  `hospitalizationAskedStatus`, once the reconciliation decision's 4 open
  items (HOPE-vs-SNS-internal labeling, response-set integrity,
  client-side requiredness confirmation, prospective-only release rule)
  are resolved.
- **Schema impact:** None — all 6 target fields already exist in
  `form_data` (confirmed, not assumed).
- **Migration impact:** None expected; forward-only migration only if a
  future re-check of `form_data` proves otherwise.
- **Ownership domains affected:** ACP & Goals of Care only; must not own
  POC interventions, final certification, or Final Clinical Narrative.
- **Acceptance criteria:** All 6 target ACP fields are server-enforced at
  Lock, applied prospectively only (no rewrite of signed/locked records);
  each field's HOPE-vs-SNS-internal label and response-set integrity
  confirmed per the reconciliation decision.
- **Automated test requirements:** New Lock-blocker tests for the 3 newly-
  enforced fields; a client/server parity test for
  `lifeSustainingAskedStatus`.
- **Historical-record handling:** New enforcement applies only to
  assessments created/unlocked after the approved release rule takes
  effect. Existing signed or locked records are not rewritten or
  retroactively evaluated against the 6-field requirement.
- **Feature-flag/rollback strategy:** New enforcement behind its own flag
  (Lock-blocking change, not presentation-only).
- **Dependencies/blockers:** **Blocked** on the 4 open items in
  `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md` §9 before server-
  enforcement work can be scoped. Field-existence discovery (previously
  Discovery Item 7) is now resolved — no longer a blocker for scoping the
  presentation-only portion of this increment.

## Increment 10 — Orders & POC explicit actions

- **Current reusable implementation:** Full POC adapter
  (`rnica_poc_adapter.py`, `rnica_poc.py`) — add/update/resolve/link/merge/
  deactivate/view, all explicit-action-only, no auto-generation at Lock.
  Classified **A** (already implemented and reusable) in the Gap Report.
- **Presentation rewiring:** New screen surfacing existing adapter actions.
- **Confirmed defects:** None found.
- **New API/service work:** None expected.
- **Schema impact:** None. **Migration impact:** None.
- **Ownership domains affected:** None — POC domain ownership is preserved
  unchanged; RNICA only presents explicit actions against it.
- **Acceptance criteria:** No silent order/POC creation; all actions
  require explicit user initiation (already true today — regression-test
  only).
- **Automated test requirements:** Existing `test_rnica_poc_adapter.py`,
  `test_rnica_poc_history.py` must still pass unmodified.
- **Feature-flag/rollback strategy:** Same flag as Increment 1.
- **Dependencies/blockers:** Depends on Increment 1 only. Lowest-risk
  increment in the plan.

## Increment 11 — Compliance & Readiness parity

- **Current reusable implementation:** `getRnicaFinalizationReadiness` —
  same function (`evaluate_finalization_readiness`) backs both this
  endpoint and the server Lock gate. Classified **A** in the Gap Report.
- **Presentation rewiring:** New screen rendering the existing `checks`
  structure with navigation to each blocker's source screen.
- **Confirmed defects:** None in the readiness mechanism itself; the
  screen must accurately reflect Discovery Items 1-3 once resolved (pain
  reassessment, SFV, signature/attestation).
- **New API/service work:** None expected beyond Discovery Items 1-3.
- **Schema impact:** None. **Migration impact:** None.
- **Ownership domains affected:** None — presentation of compliance state
  only, not source clinical data.
- **Acceptance criteria:** Every blocker shown matches server severity
  exactly; every blocker navigates to its authoritative source screen.
- **Automated test requirements:** UI/server blocker-identity parity test.
- **Feature-flag/rollback strategy:** Same flag as Increment 1.
- **Dependencies/blockers:** Partially blocked on Discovery Items 1-3 for
  full accuracy; the screen shell itself can be built in parallel.

## Increment 12 — AI Action Center governance and freshness

- **Current reusable implementation:** `getRnicaIntelligence`,
  `CONCEPT_REGISTRY`, confirmed Load/Save/Lock-only trigger pattern (no
  live-typing refresh found).
- **Presentation rewiring:** New screen surfacing existing intelligence
  output with freshness timestamp and required disclaimer language per
  `RNICA_AI_GOVERNANCE.md`.
- **Confirmed defects:** None in the trigger mechanism.
- **New API/service work:** Add a dedicated audit event for "AI
  recommendation applied"/"AI recommendation dismissed" if required by
  `RNICA_AI_GOVERNANCE.md` §8 (currently only generic
  `review_status` persistence exists, no discrete audit log entry
  confirmed for the review action itself).
- **Schema impact:** None expected (may reuse existing audit-event table).
- **Migration impact:** None expected.
- **Ownership domains affected:** None — AI Action Center owns no clinical
  source data.
- **Acceptance criteria:** No prohibited AI language anywhere on this
  screen; freshness/trigger basis always visible; new audit event fires
  correctly if added.
- **Automated test requirements:** Trigger tests (Load/Save/Lock only),
  no-live-typing-claim test, prohibited-language snapshot test, new audit
  event test if added.
- **Feature-flag/rollback strategy:** Same flag as Increment 1; new audit
  event behind its own flag if it changes existing log volume/shape.
- **Dependencies/blockers:** Depends on Increment 1. Audit-event work is
  optional pending confirmation it's required by governance.

## Increment 13 — Finalization, signature, Lock, amendment, and audit

- **Current reusable implementation:** `finalization.clinicalNarrative`,
  `finalization.signatureCertification`, `finalization.clinicianSignature`,
  Lock endpoint (idempotent re-lock, readiness parity, HOPE sync, audit
  event), amendment workflow (4 endpoints, tested). Classified **B**
  overall in the Gap Report (implemented, needs presentation rewiring).
- **Presentation rewiring:** New screen presenting existing
  narrative/signature/lock/amendment functionality under the approved
  13-screen shell.
- **Confirmed defect:** `record.status = "DRAFT"` resets unconditionally on
  every non-locked `PUT` (`visits.py:1118`), including trivial autosave
  ticks. **Must be fixed in this increment, not designed around.**
- **New API/service work:** Change the status-reset logic to only reset to
  `"DRAFT"` on a substantive clinical edit, not on every autosave tick (or
  remove the reset entirely if `status` is not meant to track draft/
  submitted state at that granularity — requires product confirmation of
  intended `status` semantics before the fix is written).
- **Schema impact:** None — same `status` column, different write
  condition.
- **Migration impact:** None; existing `status` values for historical
  records are unaffected.
- **Ownership domains affected:** Finalization owns
  `finalization.clinicalNarrative` exclusively; no other screen may
  introduce a duplicate.
- **Acceptance criteria:** `status` no longer flips to `"DRAFT"` on a
  trivial autosave tick; Lock/amendment/audit behavior otherwise unchanged
  and regression-tested; Discovery Item 3 (signature/attestation as
  distinct blockers) resolved.
- **Historical-record handling:** The `status`-reset fix changes only the
  write condition on future updates; historical rows' existing `status`
  values are not rewritten or reinterpreted. Amendment/audit history for
  already-locked records is unaffected, since locked records never hit
  this code path (blocked by the existing 423 protection).
- **Automated test requirements:** Regression test for the `status`-reset
  fix (assert `status` unaffected by autosave-only updates); existing
  `test_rnica_finalization.py`, `test_rnica_amendments.py` must still pass.
- **Feature-flag/rollback strategy:** `status`-reset fix behind its own
  flag, since it changes existing (if defective) behavior other code may
  depend on; verify no downstream consumer relies on the current
  every-update-resets-to-DRAFT behavior before removing it.
- **Dependencies/blockers:** **Blocked** on product confirmation of
  intended `status` semantics before the defect fix is scoped; screen
  presentation work is not blocked.

## Increment 14 — Regression, accessibility, mobile, and historical-record verification

- **Current reusable implementation:** 16 backend test files + 1 frontend
  test file already cover RNICA behavior; these form the regression
  baseline for this increment.
- **Presentation rewiring:** N/A — this increment is verification, not new
  screens.
- **Confirmed defects:** Any defect fixed in Increments 3, 9, or 13 must be
  independently regression-tested here against historical (already-locked)
  records to confirm no silent overwrite or reinterpretation occurs.
- **New API/service work:** None expected; this increment validates prior
  increments.
- **Schema impact:** None. **Migration impact:** None.
- **Ownership domains affected:** None directly; verifies all domains
  touched by Increments 1-13 remain intact.
- **Acceptance criteria:** All 13 screens pass accessibility (keyboard/ARIA)
  and responsive (mobile/tablet/desktop) checks; all pre-existing
  automated tests pass unmodified; a sample of historical locked/amended
  records renders identically before and after the full rollout.
- **Automated test requirements:** Full existing RNICA suite (16 backend +
  1 frontend files) plus new accessibility/responsive test pass; a
  historical-record snapshot-diff test.
- **Feature-flag/rollback strategy:** Full rollout flag flip only after
  this increment passes; rollback path is disabling the feature flag from
  Increment 1, which reverts to the legacy 28-module nav with no data loss
  since no schema change occurred in Increments 1-12 (Increment 13's
  `status`-reset fix is the only state-affecting change in the whole plan
  and has its own independent flag).
- **Dependencies/blockers:** Depends on all prior increments being
  complete.

---

## Cross-increment blockers requiring resolution before their increment starts

| Increment | Blocked on |
|---|---|
| 3 | None — ECOG fix is independently scoped and shippable |
| 4 | Discovery Items 1, 6 |
| 5 | Discovery Item 4 |
| 6 | Discovery Item 5 (field-completeness scope only, not shell) |
| 8 | Fall Risk/Morse authority decision (must remain `BLOCKED BY AUTHORITY DECISION` until resolved) |
| 9 | Discovery Item 7 |
| 13 | Product confirmation of intended `status` semantics |

No increment above may proceed past its blocked scope by assumption. Each
blocker must be resolved and documented (per the discovery-item structure
in `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md`) before code is written for that
scope.

## Explicit non-goals of this plan

- Does not authorize any code, schema, or migration change by itself.
- Does not reduce the approved 6-field ACP target to the current 3-field
  repository state.
- Does not convert Fall Risk/Morse into a Lock blocker.
- Does not recreate the legacy 28-module navigation inside the new shell.
- Does not duplicate ownership of Diagnosis, LCD, Body Systems, POC,
  Compliance, AI, or Finalization in any other screen, including a
  presentation-only "Clinical Review" screen if one is later added.
