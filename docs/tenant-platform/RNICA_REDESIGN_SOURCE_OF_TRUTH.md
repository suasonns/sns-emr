# RNICA Redesign Source of Truth

VERSION 1.0 — FINAL FIGMA REQUIREMENTS / FINAL FIGMA INPUT PACKAGE

STATUS: AUTHORITATIVE DESIGN DOCUMENT
FIGMA MUST DESIGN FROM THIS DOCUMENT
REPOSITORY DOCUMENTS ARE SUPPORTING EVIDENCE ONLY

DO NOT DESIGN FROM:
- Current RNICA Layout
- Current Navigation
- Current Card Placement
- Historical UI
- Repository Structure

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
REDESIGN: NOT YET AUTHORIZED — this document is the design input, not the
redesign itself.

This document does not describe code, models, tables, services, APIs,
repositories, or React components. Where a fact traces to prior repository
discovery, it is stated in plain product language (e.g. "already matches
current behavior," "not currently enforced") rather than as a code
citation. Full file/line evidence lives in the supporting documents listed
below and is not repeated here.

Supporting evidence documents (repository-facing, not for Figma):
- `RNICA_SECTION_BREAKDOWN.md`
- `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`
- `RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md`
- `RNICA_CLINICAL_NARRATIVE_REWIRING_MAP.md`
- `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`
- `AI_VISIBILITY_MATRIX.md`
- `RNICA_USABILITY_AND_AI_REVIEW.md`

---

## PRIMARY OBJECTIVE

**Preserve:**
- HOPE
- POC
- Validation
- Structured Findings
- Intelligence
- Lock Workflow
- Amendment Workflow
- Autosave
- Assessment History
- Auditability

**Redesign:**
- Navigation
- Workflow
- AI Visibility
- Patient Experience
- Nurse Experience

---

## GLOBAL RULES

RNICA IS:
- Patient First
- Evidence First
- Nurse First
- Workflow First
- AI Assisted
- Compliance Guided

RNICA IS NOT:
- Form First
- Document First
- Repository First

---

## MASTER NURSE WORKFLOW

```
Step 1  Patient Story
   ↓
Step 2  Evidence & Intake
   ↓
Step 3  Functional Status
   ↓
Step 4  Pain & Symptom Burden
   ↓
Step 5  Diagnosis & LCD
   ↓
Step 6  Body Systems
   ↓
Step 7  Caregiver & Support
   ↓
Step 8  Safety & Clinical Risk
   ↓
Step 9  ACP & Goals of Care
   ↓
Step 10 Orders & POC
   ↓
Step 11 Compliance & Readiness
   ↓
Step 12 AI Action Center
   ↓
Step 13 Finalization
```

---

## CLINICAL RULE EVIDENCE TABLES

Each performance-status rule below is stated with the Owner's locked rule,
the required Figma behavior, a plain-language note on how it compares to
current repository behavior (no code references), and PASS/FAIL acceptance
criteria for the redesigned Functional Status screen.

### PPS

| Field | Value |
|---|---|
| Owner Rule | Always Visible |
| Required Figma Behavior | Always Visible |
| Current Behavior | Already matches — no diagnosis condition exists today |
| Current AI Dependency | None (excluded as a computed score, not an AI-assertable fact) |
| Current HOPE Dependency | Yes — paired with KPS in an either/or HOPE requirement |
| Current Lock/Compliance Dependency | Always required at finalization, independent of diagnosis |
| PASS | PPS visible on every patient |
| FAIL | PPS hidden for any patient |

### KPS

| Field | Value |
|---|---|
| Owner Rule | Always Visible |
| Required Figma Behavior | Always Visible |
| Current Behavior | Already matches — no diagnosis condition exists today |
| Current AI Dependency | None (excluded as a computed score) |
| Current HOPE Dependency | Yes — paired with PPS in an either/or HOPE requirement |
| Current Lock/Compliance Dependency | Always required at finalization, independent of diagnosis |
| PASS | KPS visible on every patient |
| FAIL | KPS hidden for any patient |

### FAST

| Field | Value |
|---|---|
| Owner Rule | Visible only if: Dementia, Alzheimer's, or a dementia-related diagnosis |
| Required Figma Behavior | Visible only when diagnosis qualifies; hidden otherwise |
| Current Behavior | Already matches — diagnosis-gated today on both primary and secondary diagnosis |
| Current AI Dependency | None (excluded as a computed score) |
| Current HOPE Dependency | None found |
| Current Lock/Compliance Dependency | Required at finalization only when a dementia-related diagnosis is documented |
| Open Gap | None identified |
| PASS | Diagnosed dementia patient shows FAST; non-dementia patient does not |
| FAIL | FAST visible for non-dementia patients |

### ECOG

| Field | Value |
|---|---|
| Owner Rule | Visible only if: Oncology diagnosis, Cancer diagnosis, or Metastatic disease |
| Required Figma Behavior | Visible only when diagnosis qualifies; hidden otherwise |
| Current Behavior | Already matches — diagnosis-gated today on both primary and secondary diagnosis |
| Current AI Dependency | None (excluded as a computed score) |
| Current HOPE Dependency | None found |
| Current Lock/Compliance Dependency | **Open Gap** — unlike FAST/NYHA, nothing today makes ECOG a finalization/compliance requirement even when a qualifying diagnosis is documented |
| Future Rewiring Required | Owner decision needed: add an equivalent compliance requirement for ECOG, or confirm its display-only status is intentional |
| PASS | Cancer patient shows ECOG; non-cancer patient does not |
| FAIL | ECOG visible for non-cancer diagnosis |

### NYHA

| Field | Value |
|---|---|
| Owner Rule | Visible only if: CHF, Heart Failure, or Cardiomyopathy |
| Required Figma Behavior | Visible only when diagnosis qualifies; hidden otherwise |
| Current Behavior | Already matches — diagnosis-gated today on both primary and secondary diagnosis |
| Current AI Dependency | Yes — the only performance scale an AI evidence pipeline may currently assert from clinician narrative text |
| Current HOPE Dependency | None found |
| Current Lock/Compliance Dependency | Required at finalization only when a cardiac-related diagnosis is documented |
| Open Gap | None identified |
| PASS | CHF patient shows NYHA; non-cardiac patient does not |
| FAIL | NYHA appears for non-cardiac diagnosis |

**Cross-cutting open item (not resolved by this document):** the diagnosis
keywords used to gate each scale for display and the diagnosis keywords
used to decide whether FAST/NYHA are compliance-required are two
independently maintained lists today and can disagree at the edges. Owner
decision needed on whether to unify them before/after redesign.

---

## SCREEN EVIDENCE TABLES

For each screen: Purpose, Nurse Question(s), what content is Always
Visible / Conditionally Visible / must never be shown, AI content, items
that must survive redesign unchanged, and PASS/FAIL acceptance criteria.
Where a screen's underlying workflow has not yet had a dedicated
repository discovery pass this session, that is stated explicitly rather
than inventing content.

### SCREEN 1 — PATIENT STORY

**Purpose:** Understand the patient before documenting.

**Nurse Questions:** Who is this patient? Why hospice? What changed? What
matters most today?

**Always Visible:** Patient Name, Primary Diagnosis, Secondary Diagnoses,
Hospice Narrative Summary, Recent Hospitalization Summary, Caregiver
Summary, Current Risks, AI Summary, Missing Information, Suggested Next
Action.

**AI Content:** Summary, Risk Findings, Clinical Highlights, Missing
Evidence.

**Do Not Show:** Forms, Validation Errors, Compliance Tasks.

**Items That Must Survive:** none — this screen is a new presentation
layer over existing data; no backend workflow is altered.

**PASS:** Nurse understands the patient within 30 seconds.
**FAIL:** Nurse needs multiple screens to understand the patient.

---

### SCREEN 2 — EVIDENCE & INTAKE

**Purpose:** Review available evidence.

**Nurse Question:** What information do I already have?

**Always Visible:** Referral Data, Facesheet Facts, Imported Documents,
Structured Findings, Evidence Sources, Evidence Summary, Missing Evidence.

**AI Content:** Evidence Summary, Evidence Gaps, Suggested Review.

**Discovery Status:** Evidence-harvesting and structured-findings sourcing
for this screen has been discovered in prior narrative/AI-visibility
documents; a dedicated per-source discovery pass for this specific screen
has not yet been run this session.

**PASS:** Nurse understands available evidence before documenting.
**FAIL:** Nurse must search the chart to find evidence.

---

### SCREEN 3 — FUNCTIONAL STATUS

**Purpose:** Assess decline and performance.

**Nurse Question:** How functional is this patient today?

**Always Visible:** PPS, KPS, ADLs, Mobility, Transfers, Fall Risk,
Cognitive Status.

**Conditionally Visible:** FAST, ECOG, NYHA — see Clinical Rule Evidence
Tables above.

**Do Not Show:** Disabled scales, empty scales, "Not Applicable" cards.

**AI Content:** Significant Decline, Missing Scales, Suggested Assessments.

**Evidence Table:**

| Scale | Trigger | Visible |
|---|---|---|
| PPS | Always | Yes |
| KPS | Always | Yes |
| FAST | Dementia diagnosis | Conditional |
| ECOG | Oncology diagnosis | Conditional |
| NYHA | CHF diagnosis | Conditional |

**Items That Must Survive:** the diagnosis-gating logic itself (already
correct), the always-required PPS/KPS compliance check, the FAST/NYHA
diagnosis-conditional compliance check.

**PASS:** Only clinically relevant scales display.
**FAIL:** Irrelevant scales visible.

---

### SCREEN 4 — PAIN & SYMPTOM BURDEN

**Purpose:** Assess symptom impact.

**Nurse Question:** What symptoms are impacting this patient?

**Always Visible:** Pain Score, Pain Pattern, Pain Severity, Pain
Management, Pain Findings, Dyspnea, Anxiety, Depression, Agitation,
Fatigue, Sleep, Nausea, Constipation, Diarrhea, Appetite, Weight Change.

**AI Content:** Pain Findings, Pain Recommendations, Missing Pain
Information, Suggested Follow-Up.

**Discovery Status:** NOT YET DISCOVERED. No repository search has been
run this session for the current Pain section's field inventory,
validation rules, AI/structured-findings inputs, or HOPE symptom-impact
dependency (e.g., HOPE J2051-series items). The Owner-supplied content
above is recorded as the target requirement, but it is not yet verified
against repository evidence. A dedicated discovery pass is required before
this screen's PASS/FAIL criteria can be certified as achievable without
regression.

**PASS:** Nurse completes the pain workflow from one screen.
**FAIL:** Symptoms remain split across unrelated screens.

---

### SCREEN 5 — DIAGNOSIS & LCD

**Purpose:** Document hospice eligibility.

**Nurse Question:** Why does this patient qualify for hospice?

**Always Visible:** Primary Diagnosis, Secondary Diagnoses, Comorbidities,
Terminal Prognosis, Disease Trajectory, HOPE Diagnosis Category, LCD
Supporting Evidence, LCD Narrative, Recent Utilization, RN Addendum,
Clinician Clarification.

**LOCKED RULE:** Do NOT show a Clinical Narrative, Final Assessment
Narrative, Clinical Synthesis Narrative, or Attestation Narrative here —
already a locked, repository-verified decision.

**Evidence Table:**

| Item | Compliance Critical |
|---|---|
| Diagnosis | Yes |
| HOPE Category | Yes |
| LCD Evidence | Yes |
| LCD Narrative | Yes |
| Disease Trajectory | Yes |

**Discovery Status:** RN Addendum and Clinician Clarification remain
classified REQUIRES CLINICAL REVIEW per the Clinical Narrative Final
Decision — they are listed here as target content, but their inclusion is
not yet a final Owner decision.

**PASS:** Clinical Narrative absent from this screen.
**FAIL:** Clinical Narrative appears here.

---

### SCREEN 6 — BODY SYSTEM REVIEW

**Purpose:** Head-to-toe assessment.

**Nurse Question:** What are the significant clinical findings?

**Always Visible:** Neurological, Cardiovascular, Respiratory, Infection,
Gastrointestinal, Nutrition, Endocrine, Genitourinary, Musculoskeletal,
Skin/Wounds, Imminent Death, SFV.

**AI Content:** Clinical Findings, Missing Findings, Safety Findings.

**Discovery Status:** NOT YET DISCOVERED per-system. Purpose, required
data, conditional data, AI content, compliance content, and validation
rules for each individual body system have not been separately verified
against the repository this session.

**PASS:** All systems accessible.
**FAIL:** Any system omitted or hidden.

---

### SCREEN 7 — CAREGIVER & SUPPORT

**Purpose:** Evaluate support system.

**Nurse Question:** Who is supporting the patient and what are their risks?

**Always Visible:** Caregiver Assessment, Psychosocial, Spiritual,
Bereavement, Personal Care, Teaching Needs.

**AI Content:** Caregiver Risk, Support Risks, Teaching Recommendations.

**Discovery Status:** NOT YET DISCOVERED. Grouping rationale and current
AI/validation dependencies for this screen have not been verified against
the repository this session.

**PASS:** Caregiver workflow centralized.
**FAIL:** Caregiver workflow fragmented.

---

### SCREEN 8 — SAFETY & CLINICAL RISK

**Purpose:** Surface risk.

**Nurse Question:** What could harm this patient?

**Always Visible:** Fall Risk, Clinical Risks, Safety Issues, Behavior
Risks, Cognitive Risks, Imminent Death Indicators, AI Risk Findings,
Suggested Actions.

**Discovery Status:** NOT YET DISCOVERED. Current risk-source wiring and
AI risk logic for this screen have not been verified against the
repository this session.

**PASS:** Risks visible without hunting.
**FAIL:** Risk buried or omitted.

---

### SCREEN 9 — ACP & GOALS OF CARE

**Purpose:** Document goals and treatment preferences.

**Nurse Question:** What care does the patient want?

**Always Visible:** Code Status, CPR Preference, Life Sustaining Treatment
Preference, Hospitalization Preference, Advance Directives, Decision
Maker, POA Information.

**Discovery Status:** NOT YET DISCOVERED. Field inventory and dependency
verification for ACP content has not been run this session.

**PASS:** Goals of care obvious and complete.
**FAIL:** Goals of care fragmented.

---

### SCREEN 10 — ORDERS & POC

**Purpose:** Connect assessment findings to the Plan of Care.

**Nurse Question:** What is the care plan?

**Always Visible:** Problems, Goals, Interventions, Orders, Suggested
Orders, POC Readiness, POC Findings.

**Evidence Table:**

| Component | Must Remain |
|---|---|
| POC Adapter | Yes |
| POC Readiness Logic | Yes |
| Suggested Orders Source | Yes |

**Discovery Status:** NOT YET DISCOVERED in this document's terms
(the POC adapter and generation service exist per prior discovery
documents, but a screen-level requirements verification has not been run
this session).

**PASS:** POC workflow preserved.
**FAIL:** POC workflow altered.

---

### SCREEN 11 — COMPLIANCE & READINESS

**Purpose:** Show what must be fixed before completion.

**Nurse Question:** What is preventing completion?

**Always Visible:** Missing Information, Validation Findings, Required
Documentation, Compliance Issues, HOPE Status, POC Status, Readiness
Status, Suggested Actions, AI Compliance Findings.

**Discovery Status:** NOT YET DISCOVERED as a consolidated screen. The
underlying validation/compliance-blocking mechanism is documented in
`clinical_note_validation_engine.py`-derived findings elsewhere, but this
screen's specific presentation requirements have not been separately
verified.

**PASS:** Nurse immediately knows blockers.
**FAIL:** Nurse must hunt for blockers.

---

### SCREEN 12 — AI ACTION CENTER

**Purpose:** Make existing AI visible.

**Nurse Question:** What is AI telling me right now?

**Always Visible:** AI Summary, Findings, Recommendations, Missing
Evidence, Clinical Concerns, Risk Findings, Caregiver Suggestions,
Evidence Harvesting Output, AI Status, Last Analysis Timestamp, Refresh AI.

**Evidence Table:**

| AI Capability | Trigger | Current State | Desired State |
|---|---|---|---|
| RNICA Intelligence | Save / Lock | Hidden until Save/Lock | Visible standing screen |
| Structured Findings | Save / Lock | Hidden until Save/Lock | Visible standing screen |
| Evidence Harvesting | Load | Runs on load, not surfaced prominently | Visible standing screen |
| Recommendations | Save / Lock | Hidden until Save/Lock | Visible standing screen |
| Risk Findings | Save / Lock | Hidden until Save/Lock | Visible standing screen |

**Current AI Truth (already established):** AI refreshes on Load, Save,
and Lock — not on continuous typing. Do not invent live/continuous AI.

**PASS:** AI outputs visible without navigating away.
**FAIL:** AI remains hidden until Save/Lock.

---

### SCREEN 13 — FINALIZATION

**Purpose:** Complete and sign the assessment.

**Nurse Question:** Is this assessment ready to sign and lock?

**Always Visible:** Clinical Narrative, Signature Certification, Clinician
Signature, Readiness Checklist, Lock Workflow.

**LOCKED RULE:** Only one Clinical Narrative exists. Authoritative field:
the Finalization Clinical Narrative (already a locked, repository-verified
decision — see `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`).

**Required Evidence (already established):** Attestation, Lock, and
validation dependencies all point to the Finalization Clinical Narrative;
AI narrative-insertion also targets this field.

**PASS:** One Clinical Narrative shown.
**FAIL:** More than one Clinical Narrative shown.

---

## DO NOT TOUCH

- HOPE Workflow
- POC Adapter
- Validation Engine
- Structured Findings
- RNICA Intelligence Data Contract
- Autosave
- Lock Workflow
- Amendment Workflow
- Audit Events
- Required Fields
- LCD Narrative
- Signature Certification
- Clinician Signature

---

## FINAL FIGMA READINESS CHECKLIST

Checked items are backed by completed repository discovery this session.
Unchecked items require a dedicated discovery pass before they can be
certified.

- [x] FAST rule documented
- [x] ECOG rule documented
- [x] NYHA rule documented
- [x] PPS/KPS always-visible rule documented
- [x] Narrative rule documented
- [x] AI visibility (Load/Save/Lock triggers) documented
- [x] HOPE dependency for PPS/KPS documented
- [x] Lock dependency for FAST/NYHA documented
- [x] Open Gap: ECOG has no compliance/lock dependency — documented
- [x] Patient Story requirements documented (target state)
- [ ] Evidence & Intake workflow — requires dedicated discovery
- [ ] Pain & Symptom Burden workflow — requires dedicated discovery
- [ ] Body System Review (per-system) workflow — requires dedicated discovery
- [ ] Caregiver & Support workflow — requires dedicated discovery
- [ ] Safety & Clinical Risk workflow — requires dedicated discovery
- [ ] ACP & Goals of Care workflow — requires dedicated discovery
- [ ] Orders & POC screen-level requirements — requires dedicated discovery
- [ ] Compliance & Readiness screen-level requirements — requires dedicated discovery
- [x] Finalization / single-narrative rule documented
- [x] PASS criteria written for every screen
- [x] FAIL criteria written for every screen
- [ ] Frontend/backend diagnosis-gating keyword unification — open Owner decision, not resolved

---

## GITHUB SUCCESS TEST

**Question:** Can Figma design RNICA without reading code, models, React,
services, or validation files, and still create the correct workflow?

**Answer: NOT YET.**

Figma can already design Screens 1, 3, 5, 12, and 13 correctly from this
document alone — those rules are fully discovered, Owner-locked, and
evidence-verified. Screens 2, 4, 6, 7, 8, 9, 10, and 11 currently carry
Owner-supplied target content that has **not yet been checked against
repository evidence** (existing fields, validation rules, AI dependencies,
HOPE/POC dependencies, current consumers). Until those dedicated discovery
passes are completed and this document is updated with their verified
findings, approving the full document for Figma risks Figma designing
around requirements that may conflict with an existing compliance,
billing, or AI dependency that has not yet been surfaced.

**Recommendation:** Approve Screens 1, 3, 5, 12, and 13 (and the Clinical
Rule Evidence Tables) for Figma now. Run discovery on Screens 2, 4, 6, 7,
8, 9, 10, and 11 before final approval of the complete document.
