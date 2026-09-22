# RNICA Workflow Authority Map

Companion document to `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` (v1.1,
authority-labeled Figma input package) and
`RNICA_SCREEN_BY_SCREEN_EVIDENCE_MATRIX.md`. Those two documents establish
**Screen Authority** and **Evidence Authority**. This document establishes
**Workflow Authority**: the entry/exit conditions, required actions, and
failure paths that connect the 13 screens into one nurse workflow.

STATUS: AUTHORITATIVE DESIGN INPUT. NOT IMPLEMENTATION AUTHORIZATION.
CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED

> **[PRODUCT-AUTHORITY UPDATE — 2026-09-22]** The screen sequence in this
> document has been superseded. Screens 3-5 are now **3. Diagnosis & LCD,
> 4. Pain & Symptom Burden, 5. Functional Status** (previously 3. Functional
> Status, 4. Pain & Symptom Burden, 5. Diagnosis & LCD). This is a
> deliberate product-authority decision, not an oversight: diagnosis now
> provides context before symptom burden and functional interpretation are
> assessed. All other screen positions (1-2, 6-13) are unchanged. See
> `RNICA_NAVIGATION_SPECIFICATION.md` for the canonical order and
> navigation-ownership model.

This document does not reopen `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` or
`RNICA_SCREEN_BY_SCREEN_EVIDENCE_MATRIX.md`. It uses the same Authority
Legend and does not restate their per-screen content beyond what is
needed to define entry/exit/failure behavior.

## Authority Legend (same as the Source of Truth)

- **[REPOSITORY-DISCOVERED]** Proven current field, behavior, dependency,
  validation, trigger, consumer, or non-connection.
- **[LOCKED PRODUCT DECISION]** Approved future-state decision that may
  supersede current repository placement.
- **[REGULATORY / CLINICAL AUTHORITY]** Controlling assessment,
  plan-of-care, documentation, or terminal-status principle.
- **[DESIGN REQUIREMENT]** Figma presentation/interaction requirement
  preserving the approved authorities.
- **[FUTURE PRODUCT DIRECTION]** Desired capability not established as
  current functionality.
- **[NOT BUILT / NOT CONNECTED]** Explicit discovery non-finding.
- **[OPEN DEFECT]** Existing defect documented separately, not repaired
  by this artifact.

## Patient Story Rule (restated for workflow clarity)

- **[LOCKED PRODUCT DECISION]** Patient Story is a presentation layer.
- **[LOCKED PRODUCT DECISION]** Patient Story is NOT a clinical authority.
- **[LOCKED PRODUCT DECISION]** Patient Story does NOT own data.
- **[DESIGN REQUIREMENT]** Source sections (Diagnosis, Functional Status,
  Caregiver & Support, Safety & Clinical Risk, etc.) remain the
  authoritative owners of every fact the Patient Story screen displays.
- **[DESIGN REQUIREMENT]** Patient Story aggregates existing evidence only
  and must link back to the owning section for any correction.

## Workflow Diagram

```
Admission
   ↓
1. Patient Story
   ↓
2. Evidence & Intake
   ↓
3. Diagnosis & LCD
   ↓
4. Pain & Symptom Burden
   ↓
5. Functional Status
   ↓
6. Body Systems
   ↓
7. Caregiver & Support
   ↓
8. Safety & Clinical Risk
   ↓
9. ACP & Goals of Care
   ↓
10. Orders & POC
   ↓
11. Compliance & Readiness
   ↓
12. AI Action Center
   ↓
13. Finalization
   ↓
HOPE / Lock Workflow
```

**[DESIGN REQUIREMENT]** This sequence is the recommended default nurse
path, not a forced linear gate. **[REPOSITORY-DISCOVERED]** The current
repository does not enforce a section-completion order prior to
Finalization; server-side readiness checks are evaluated at Lock
regardless of navigation order. Figma may allow non-linear navigation
between screens as long as every entry/exit condition below is honestly
represented at Finalization/Lock time.

---

## Workflow Authority Table

| Screen | Entry Criteria | Inputs | Required Actions | Validation | AI Assistance | Compliance Touchpoints | Outputs | Next Screen | Failure Path | Lock Impact |
|---|---|---|---|---|---|---|---|---|---|---|
| 1. Patient Story | **[DESIGN REQUIREMENT]** Assessment opened/admitted; no prior screen required | **[REPOSITORY-DISCOVERED]** Patient identity, admission context, primary diagnosis, caregiver fields, prior-assessment history | **[DESIGN REQUIREMENT]** Review only; navigate to a source screen to correct anything | **[NOT BUILT / NOT CONNECTED]** No validation is owned by this screen — it aggregates validation state from other screens | **[REPOSITORY-DISCOVERED]** Intelligence summary/findings/missing evidence, refreshed on Load/Save/Lock | **[DESIGN REQUIREMENT]** None owned here; surfaces compliance state produced elsewhere | Read-only orientation view; no new data | 2. Evidence & Intake (or any screen, per non-linear navigation) | **[DESIGN REQUIREMENT]** No source data available yet → show explicit "not yet documented" state, never a fabricated summary | **[DESIGN REQUIREMENT]** None — this screen cannot block or unblock Lock |
| 2. Evidence & Intake | **[DESIGN REQUIREMENT]** None — reachable at any time | **[REPOSITORY-DISCOVERED]** Demographics, vitals, referral data, admission scoping, evidence-harvesting output | **[DESIGN REQUIREMENT]** Review available evidence; resolve missing required intake/referral documentation | **[REPOSITORY-DISCOVERED]** `referrals.reviewed` is a server-readiness requirement | **[REPOSITORY-DISCOVERED]** Evidence harvesting / missing-evidence output, refreshed on Load/Save/Lock | **[REGULATORY / CLINICAL AUTHORITY]** Initial/comprehensive assessment findings must be retained in the clinical record | Reviewed intake evidence; referral review state | 3. Diagnosis & LCD | **[REPOSITORY-DISCOVERED]** Missing referral review blocks Finalization readiness (not this screen directly) | **[REPOSITORY-DISCOVERED]** `referrals.reviewed` is evaluated again at Lock |
| 3. Diagnosis & LCD | **[DESIGN REQUIREMENT]** None — reachable at any time | **[REPOSITORY-DISCOVERED]** Primary/secondary diagnosis, comorbidities, terminal prognosis | **[DESIGN REQUIREMENT]** Complete required diagnosis/HOPE fields and the LCD narrative; resolve visible validation issues | **[REPOSITORY-DISCOVERED]** Primary diagnosis ICD-10 and HOPE diagnosis category are hard-required (HOPE I0010) | **[REPOSITORY-DISCOVERED]** LCD detect/config/evaluate chain reads diagnosis + functional-status facts | **[REPOSITORY-DISCOVERED]** HOPE I0010; **[LOCKED PRODUCT DECISION]** no Clinical Narrative shown on this screen | Diagnosis, HOPE category, LCD narrative | 4. Pain & Symptom Burden | **[REPOSITORY-DISCOVERED]** Missing primary diagnosis ICD-10 or HOPE category → hard validation error | **[REPOSITORY-DISCOVERED]** Missing primary diagnosis/HOPE category blocks Finalization |
| 4. Pain & Symptom Burden | **[DESIGN REQUIREMENT]** None — reachable at any time | **[REPOSITORY-DISCOVERED]** Pain assessment fields, J0900/J0915, Symptom Impact J2051 items | **[DESIGN REQUIREMENT]** Complete hard-required pain fields; review all applicable symptom-impact items | **[REPOSITORY-DISCOVERED]** J0900/J0915/J2051 HOPE mappings and validation | **[REPOSITORY-DISCOVERED]** Pain threshold findings/recommendations and missing-evidence output, refreshed on Load/Save/Lock | **[REPOSITORY-DISCOVERED]** HOPE pain/symptom-impact mappings | Pain and symptom-impact documentation | 5. Functional Status | **[DESIGN REQUIREMENT]** Missing required pain/symptom fields → visible gap, consistent with existing HOPE validation | **[REPOSITORY-DISCOVERED]** Missing required HOPE pain fields participate in existing Finalization readiness checks |
| 5. Functional Status | **[DESIGN REQUIREMENT]** None — reachable at any time | **[REPOSITORY-DISCOVERED]** Diagnosis data (drives FAST/ECOG/NYHA gating) | **[LOCKED PRODUCT DECISION]** Enter PPS and KPS always; enter FAST/ECOG/NYHA only when diagnosis-qualified and visible | **[REPOSITORY-DISCOVERED]** Soft warning if both PPS and KPS are empty (HOPE M1190); **[REPOSITORY-DISCOVERED]** FAST/NYHA escalate to a hard finalization/compliance requirement when a qualifying diagnosis is documented; **[OPEN DEFECT]** ECOG has no equivalent backend compliance requirement today even when a qualifying diagnosis is documented | **[NOT BUILT / NOT CONNECTED]** No AI reads or asserts PPS/KPS/ECOG/FAST as facts; **[REPOSITORY-DISCOVERED]** NYHA class is the one scale an AI evidence pipeline may assert from narrative text | **[REPOSITORY-DISCOVERED]** HOPE M1190 (PPS/KPS); dementia/cardiac diagnosis-conditional compliance requirement (FAST/NYHA) | PPS/KPS values; conditionally FAST/ECOG/NYHA values and justifications | 6. Body Systems | **[REPOSITORY-DISCOVERED]** Missing PPS and KPS → soft warning, does not block Lock by itself; missing FAST/NYHA when diagnosis-qualified → compliance-blocking item | **[REPOSITORY-DISCOVERED]** FAST/NYHA missing-when-required blocks Finalization; PPS/KPS missing is a warning only, not a hard Lock block by itself |
| 6. Body Systems | **[DESIGN REQUIREMENT]** None — reachable at any time | **[REPOSITORY-DISCOVERED]** Ten body-system section fields | **[DESIGN REQUIREMENT]** Review applicable systems; document significant findings | **[REPOSITORY-DISCOVERED]** Per-system validation rules where configured (not every system is fully validated) | **[REPOSITORY-DISCOVERED]** Structured findings / Intelligence findings for supported inputs only — not every system feeds Intelligence | **[REPOSITORY-DISCOVERED]** HOPE-coded neurological and skin/performance mappings | Body-system documentation | 7. Caregiver & Support | **[DESIGN REQUIREMENT]** Section left "not assessed" → must remain visibly unassessed, never silently treated as normal | **[REPOSITORY-DISCOVERED]** Required-field gaps within a system participate in existing Finalization readiness checks |
| 7. Caregiver & Support | **[DESIGN REQUIREMENT]** None — reachable at any time | **[REPOSITORY-DISCOVERED]** Caregiver assessed/no-caregiver state, willingness, capability, psychosocial/spiritual/personal-care/teaching fields | **[DESIGN REQUIREMENT]** Record caregiver availability/capability or the no-caregiver condition and required reason | **[REPOSITORY-DISCOVERED]** No-caregiver reason required when no caregiver is documented | **[REPOSITORY-DISCOVERED]** Existing caregiver-adjacent recommendation text only; **[NOT BUILT / NOT CONNECTED]** no dedicated caregiver intelligence/score | **[DESIGN REQUIREMENT]** Preserve caregiver/support documentation needed to plan safe care | Caregiver/support documentation | 8. Safety & Clinical Risk | **[DESIGN REQUIREMENT]** Missing no-caregiver reason when applicable → visible gap | **[REPOSITORY-DISCOVERED]** Required caregiver fields participate in existing Finalization readiness checks |
| 8. Safety & Clinical Risk | **[DESIGN REQUIREMENT]** None — reachable at any time | **[REPOSITORY-DISCOVERED]** Fall risk, oxygen safety, imminent-death screening, psychosocial/mobility/cognitive findings | **[DESIGN REQUIREMENT]** Review triggered risks; complete associated documentation | **[REPOSITORY-DISCOVERED]** Existing required/warning fields tied to risk documentation | **[REPOSITORY-DISCOVERED]** Pain/oxygen/fall/delirium/imminent-death/mobility/psychosocial threshold findings; **[NOT BUILT / NOT CONNECTED]** no formal numeric risk score | **[DESIGN REQUIREMENT]** Preserve suicide-concern note warning and all source evidence | Safety/risk documentation | 9. ACP & Goals of Care | **[DESIGN REQUIREMENT]** Triggered risk left undocumented → remains a visible required action, not hidden | **[REPOSITORY-DISCOVERED]** Required safety-related fields participate in existing Finalization readiness checks |
| 9. ACP & Goals of Care | **[DESIGN REQUIREMENT]** None — reachable at any time | **[REPOSITORY-DISCOVERED]** Code status, CPR preference, life-sustaining treatment preference, hospitalization preference, advance directives, decision maker | **[DESIGN REQUIREMENT]** Complete the six hard-required ACP values and applicable supporting detail | **[REPOSITORY-DISCOVERED]** Six ACP fields are hard-required with HOPE mappings | **[NOT BUILT / NOT CONNECTED]** No separate ACP AI engine; only missing-documentation prompts | **[REPOSITORY-DISCOVERED]** HOPE F2000/F2100/F2200-series mappings | ACP documentation | 10. Orders & POC | **[REPOSITORY-DISCOVERED]** Missing any of the six hard-required ACP fields → hard validation error | **[REPOSITORY-DISCOVERED]** Missing hard-required ACP fields blocks Finalization |
| 10. Orders & POC | **[DESIGN REQUIREMENT]** None — reachable at any time | **[REPOSITORY-DISCOVERED]** Admissions order content, problems, goals, interventions, discipline coverage | **[DESIGN REQUIREMENT]** Complete required admission-order items and discipline coverage; explicitly initiate any order/POC action | **[REPOSITORY-DISCOVERED]** POC completeness and conditional CHHA POC checks | **[DESIGN REQUIREMENT]** Existing recommendations may support an explicit user action only; **[NOT BUILT / NOT CONNECTED]** recommendations never auto-create orders | **[REGULATORY / CLINICAL AUTHORITY]** Individualized POC based on assessment findings (goals, services/frequency, symptoms, safety, supplies, treatments, limitations) | POC content; orders | 11. Compliance & Readiness | **[REPOSITORY-DISCOVERED]** Incomplete POC/CHHA POC → visible readiness gap | **[REPOSITORY-DISCOVERED]** POC completeness and CHHA POC checks participate in existing Finalization readiness checks |
| 11. Compliance & Readiness | **[DESIGN REQUIREMENT]** None — reachable at any time; typically reviewed just before Finalization | **[REPOSITORY-DISCOVERED]** Aggregated client/server validation state, HOPE status, referral review, POC/CHHA readiness | **[DESIGN REQUIREMENT]** Resolve every hard blocker; review warnings | **[REPOSITORY-DISCOVERED]** This screen surfaces, but does not itself define, the existing validation rule set | **[DESIGN REQUIREMENT]** Missing-evidence/recommendation content shown as advisory, visually separated from hard blockers | **[REPOSITORY-DISCOVERED]** Full existing compliance-blocking item set, unmodified | Confirmed readiness state (mirrors server truth) | 12. AI Action Center | **[REPOSITORY-DISCOVERED]** Any unresolved hard blocker → Finalization/Lock is refused server-side | **[REPOSITORY-DISCOVERED]** This screen is the primary pre-Lock checkpoint; Lock re-validates server-side regardless of what this screen shows |
| 12. AI Action Center | **[DESIGN REQUIREMENT]** None — reachable at any time | **[REPOSITORY-DISCOVERED]** Intelligence output, structured-findings signals, recommendations, missing evidence | **[DESIGN REQUIREMENT]** Review AI output; no blanket acknowledgment required | **[NOT BUILT / NOT CONNECTED]** This screen owns no validation of its own | **[REPOSITORY-DISCOVERED]** Full Intelligence output, refreshed on Load/Save/Lock only — not continuous | **[DESIGN REQUIREMENT]** Advisory output visually separated from required validation/finalization blockers | Reviewed AI output (no data mutation) | 13. Finalization | **[DESIGN REQUIREMENT]** Stale output not yet refreshed → must be labeled stale, never silently presented as current | **[DESIGN REQUIREMENT]** None — this screen cannot block or unblock Lock |
| 13. Finalization | **[DESIGN REQUIREMENT]** All prior screens reachable (not necessarily completed) before attestation is offered | **[REPOSITORY-DISCOVERED]** Aggregated readiness state from all prior screens; **[LOCKED PRODUCT DECISION]** `finalization.clinicalNarrative` as the sole Clinical Narrative field | **[DESIGN REQUIREMENT]** Complete the Clinical Narrative; resolve blockers; manually attest; sign | **[REPOSITORY-DISCOVERED]** Full Lock-readiness check set re-evaluated server-side at Lock time | **[REPOSITORY-DISCOVERED]** Existing visit-recording insertion into the Clinical Narrative remains blank-only (never auto-overwrites) | **[REPOSITORY-DISCOVERED]** Signature certification and clinician signature remain manual; Lock writes the existing audit event | Locked, attested, signed assessment | HOPE / Lock Workflow | **[REPOSITORY-DISCOVERED]** Any unresolved server-side readiness check → Lock is refused with the specific blocker identified | **[REPOSITORY-DISCOVERED]** This is the terminal screen; a successful Lock is the only path to HOPE/Lock Workflow completion |

---

## Cross-Screen Workflow Rules

1. **[DESIGN REQUIREMENT]** No screen in this workflow, including Patient
   Story and AI Action Center, owns or mutates clinical data that belongs
   to another screen's domain — every fact has exactly one owning screen.
2. **[REPOSITORY-DISCOVERED]** Section-level navigation order is not
   currently enforced by the backend; only the aggregate Finalization/Lock
   readiness check is enforced server-side. Figma's screen sequence is a
   recommended default path, not a technical gate, unless a future,
   separately authorized change adds sequence enforcement.
3. **[REPOSITORY-DISCOVERED]** AI content on every screen refreshes on
   Load, Save, and Lock only. No screen may present AI output as
   continuously live.
4. **[OPEN DEFECT]** The unreachable narrative-review condition
   (documented separately in
   `RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md`) is not resolved by
   this workflow map and is not a Figma design responsibility.
5. **[LOCKED PRODUCT DECISION]** FAST, ECOG, and NYHA visibility rules in
   this document and in `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` are approved
   product authority for the redesigned experience. They are not to be
   cited as proof of current repository behavior beyond what
   `RNICA_SCREEN_BY_SCREEN_EVIDENCE_MATRIX.md` already documents as
   repository-discovered (i.e., that today's diagnosis-gated *display*
   logic already happens to match this locked rule is a repository fact;
   the rule itself, as an approved requirement Figma must build to, is a
   locked product decision).
6. **[DESIGN REQUIREMENT]** Every "Failure Path" above must remain a
   visible, navigable state — never a silent block or a generic error
   with no path back to the source field.

## Figma Handoff Gate (workflow-specific addendum)

In addition to the Figma Handoff Gate in `RNICA_REDESIGN_SOURCE_OF_TRUTH.md`
§5, workflow handoff is ready only when:

- every screen's entry criteria, required actions, and failure path are
  defined above;
- no screen is designed to silently block progress without identifying
  the specific unresolved requirement;
- the Patient Story presentation-layer rule is visually enforced (no
  editable fields, no new authoritative data entry) on that screen;
- Lock/Finalization remains the single terminal compliance checkpoint,
  consistent with current server-side enforcement.

## Implementation Boundary

This document defines workflow requirements for Figma only. It does not
authorize code, APIs, schemas, migrations, section-order enforcement, or
any change to current server-side validation/readiness logic. A separate,
authorized implementation plan is required before any of the transitions
described here are built.
