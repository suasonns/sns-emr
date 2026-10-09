# Pain & Symptom Burden — Approved Screen Field Mapping (Pilot)

Status: DRAFT / PILOT — covers one approved workflow container as a template
for the remaining containers. Not yet reviewed/approved.

## Purpose

The approved "Pain & Symptom Burden" screen is a **presentation-layer
workflow container**. It is not a replacement data model and does not
remove or alter HOPE/CMS mappings, PAINAD/FLACC, validation rules,
eligibility/LCD logic, or audit trails. This document maps every
RNICA.jsx field that the approved screen must surface back to its
existing implementation, so the new screen can be built as a view on top
of the current compliance infrastructure, unchanged underneath.

Per the user's clarification: the workflow container is a clinician-facing
presentation grouping, not a 1:1 module count. "Pain & Symptom Burden"
pulls fields from four true-owning RNICA modules (Pain, Respiratory, GI,
Neurological) plus the derived Symptom Impact (HOPE J2051) rollup — it
does not introduce a new module or move ownership of any field.

## Scope note (no-assumption classification)

All rows below are classified VERIFIED (confirmed by direct reading of
`sns-emr-frontend/src/components/RNICA.jsx` and
`sns-emr-frontend/src/config/bodySystems.js` in this repo state) unless
marked otherwise. No field's HOPE mapping, validation, or audit behavior
was inferred from memory of a prior session.

## Module registry (source of truth: `SIDEBAR_CONFIG`, RNICA.jsx ~L204-237)

| RNICA module | HOPE codes | Role in this screen |
|---|---|---|
| `pain` | J0900, J0915 | True owner of pain fields; primary content of screen |
| `symptomImpact` | J2051 | Derived/read-only rollup (A–H); drives the screen's symptom-burden summary |
| `respiratory` (formSection, from `bodySystems.js`) | — | True owner of `sobSeverity` (feeds J2051B) |
| `gastrointestinal` (formSection) | — | True owner of `nausea`/`vomiting`/`diarrhea`/`constipation` (feed J2051D–G) |
| `neurological` (formSection) | N0500, N0510, N0520 | True owner of `symptomsDemeanor` checklist entries "Anxiety"/"Agitation" (feed J2051C/H) |

## Symptom Impact derivation (VERIFIED, RNICA.jsx ~L14893-14933)

Symptom Impact has **no RN-facing input UI**. It is a `useEffect`-driven,
one-way derivation that keeps J2051 A–H in sync with each symptom's true
owning section, per the 2026-09-25 owner design review ("Document symptom
severity once. Store symptom severity once. Reuse everywhere."):

| J2051 item | Derived field | True source field | Severity mapping |
|---|---|---|---|
| A. Pain | `symptomImpact.pain` | `pain.painSeverityCategory` | passthrough "0"–"3" |
| B. Shortness of Breath | `symptomImpact.shortnessOfBreath` | `respiratory.sobSeverity` | None/Mild/Moderate/Severe → 0–3 |
| C. Anxiety | `symptomImpact.anxiety` | `neurological.symptomsDemeanor` includes "Anxiety" | presence → "1", else "0" |
| D. Nausea | `symptomImpact.nausea` | `gastrointestinal.nausea` | None/Mild/Moderate/Severe → 0–3 |
| E. Vomiting | `symptomImpact.vomiting` | `gastrointestinal.vomiting` | None/Mild/Moderate/Severe → 0–3 |
| F. Diarrhea | `symptomImpact.diarrhea` | `gastrointestinal.diarrhea` | None/Mild/Moderate/Severe → 0–3 |
| G. Constipation | `symptomImpact.constipation` | `gastrointestinal.constipation` | None/Mild/Moderate/Severe → 0–3 |
| H. Agitation | `symptomImpact.agitation` | `neurological.symptomsDemeanor` includes "Agitation" | presence → "1", else "0" |

**Implication for the approved screen**: a "Symptom Burden Matrix" or
equivalent summary view on this screen should read from `symptomImpact.*`
(the already-reconciled rollup) for display, and deep-link each row to its
true-owning section's input control for editing — it must not re-collect
severity independently, which would reintroduce the pre-2026-09-25
duplicate-entry defect this architecture was built to eliminate.

## Field mapping — Pain module (`formData.pain`, VERIFIED)

| Source field | HOPE item | Approved screen location (proposed) | Validation logic (RNICA.jsx) | Audit source |
|---|---|---|---|---|
| `pain.screenedForPain` | J0900.A | Pain & Symptom Burden → Pain Overview | `errors["pain.screenedForPain"]`, required (~L1122) | 30s autosave (`useAssessmentAutosave`, L14474) → `api.saveRNICAAssessment`/`updateRNICAAssessment`; locked at finalization (`lockedAt`/`signed_at`) |
| `pain.painSeverityCategory` | J0900.C | Pain Overview + feeds Symptom Burden Matrix (A) | `errors["pain.painSeverityCategory"]`, required when screened=Yes (~L1125) | same |
| `pain.standardizedPainToolType` | J0900.D | Pain Overview / Pain Intensity | `errors["pain.standardizedPainToolType"]`, required when screened=Yes (~L1128) | same |
| `pain.verbalizesPain` | — (internal gate) | Pain Intensity (scale selection) | `warnings["pain.verbalizesPain"]` (~L1130) | same |
| `pain.neuropathicPain` | J0915 | Pain Character & Impact | `errors["pain.neuropathicPain"]`, always required (~L1133) | same |
| `pain.painActiveProblem` | J0900 (skip-path target) | Pain Overview | referenced as the stated skip target when screened=No; no separate error rule found this pass | same |
| `pain.uncomfortableBecauseOfPain` | — | Pain Overview (hidden when screened=No, per L11464 gate) | none found this pass | same |
| `pain.comprehensiveAssessmentDate` | — | Pain Intensity summary grid | none found this pass | same |
| `pain.assessmentTool` | — | Pain Intensity | none found this pass | same |
| `pain.painIntensity.{current,worst,best,acceptable}` | — | Pain Intensity summary grid | none found this pass | same |
| `pain.painLocation`, `pain.painBodySites`, `pain.painMapMode`, `pain.painRadiation` | — | Location (Dialog/Sheet, secondary interaction) | `validateBodyMapRegions` (imported from `rnIcaClinicalNavigation.js`) — not yet inspected this pass (NOT VERIFIED) | same |
| `pain.painCharacter` | — | Pain Character & Impact | none found this pass | same |
| `pain.aggravatingFactors`, `pain.relievingFactors` | — | Pain Character & Impact | none found this pass | same |
| `pain.painManagementPlan`, `pain.nonPharmInterventions` | — | Pain Management | none found this pass | same |
| `pain.flacc.{face,legs,activity,cry,consolability,total}` | — (PAINAD/FLACC scale, non-verbal) | Pain Intensity (alternate scale) | not yet inspected this pass (NOT VERIFIED) | same |
| `pain.painad.{breathing,vocalization,facialExpression,bodyLanguage,consolability,total}` | — (PAINAD scale, non-verbal/dementia) | Pain Intensity (alternate scale) | not yet inspected this pass (NOT VERIFIED) | same |

## Field mapping — Symptom Impact (`formData.symptomImpact`, VERIFIED)

| Source field | HOPE item | Approved screen location | Validation logic | Audit source |
|---|---|---|---|---|
| `symptomImpact.{pain,shortnessOfBreath,anxiety,nausea,vomiting,diarrhea,constipation,agitation}` | J2051 A–H | Pain & Symptom Burden → Symptom Burden Matrix | `warnings[\`symptomImpact.${f}\`]`, all 8 required (~L1139-1143) | read-only derived value; audited via the true-owning field's autosave (see derivation table above) — the rollup itself is not independently editable, so there is no separate audit trail for it |
| `symptomImpact.totalScore`, `symptomImpact.assessmentDate` | J2051 (summary) | Symptom Burden Matrix header | not yet inspected this pass (NOT VERIFIED) | same |

## SFV trigger (VERIFIED, referenced at ~L1144-1151)

J2052A/C: an SFV (Symptom Follow-Up Visit) is required whenever any J2051
item is Moderate (2) or Severe (3). This is a cross-cutting rule the
approved screen's Symptom Burden Matrix should surface as an alert/badge,
not a new field — "reason SFV not completed" is validated on the separate
SFV visit, never on this assessment (owner fix, issue #146).

## Not yet mapped in this pass (candidates for "Pain & Symptom Burden" per user's example)

- Dyspnea / Nausea / Anxiety / Depression / Fatigue as **named** standalone
  concepts: confirmed NOT present as separate RNICA modules or sidebar
  entries (NOT FOUND via repo search) — same as HospiceMD, which also has
  no standalone "Depression" module; it is the same underlying data,
  different UI surface. Dyspnea = `respiratory.sobSeverity`; Nausea/
  Vomiting/Diarrhea/Constipation = `gastrointestinal.*`; Anxiety/Agitation
  = `neurological.symptomsDemeanor` checklist entries (all above).
  **Depression — VERIFIED present, two places, matching HospiceMD exactly**:
  (1) `neurological.symptomsDemeanor` pill-group includes "Depressed"
  (RNICA.jsx ~L12720, options: Anxiety, Agitation, Peaceful, Confused,
  Angry, Restless, Depressed, Seizure, Combative, Sundowning, Tremors /
  twitching, Other) — HospiceMD's "Symptoms/Demeanor" checkbox row;
  (2) `neurological.psychiatricHistoryType` pill-group includes
  "Depression" (~L12765, options: None, Bipolar disorder, OCD,
  Schizophrenia, Depression, Other) — HospiceMD's "Psych Hx" row.
  Neither feeds `symptomImpact`/J2051 (correctly — J2051 A-H has no
  depression item; only Anxiety/Agitation are HOPE-reportable). No new
  field needed; map the approved screen's Depression row to
  `symptomsDemeanor` (current symptom) and/or `psychiatricHistoryType`
  (history) as appropriate to what the mockup is showing.
  "Fatigue" as a named field: `fatigue` exists under `cardiovascular`
  (RNICA.jsx ~L673, no HOPE code attached) — NOT VERIFIED whether this is
  the field the approved screen intends; still open.
- AI analysis for pain: `painAssessmentSummary` / `aiPainAnalysis` /
  `painOverdueAlerts` customRenderer cards exist (RNICA.jsx ~L11170-11199)
  but their internal field-level logic has not been inspected this pass
  (NOT VERIFIED) — needed to map "AI analysis" row in the approved screen.

## Open questions before proceeding to implementation

1. Should "Fatigue" (currently a Cardiovascular field with no HOPE code)
   be the field the approved screen's Symptom Burden shows, or is a
   different/new field intended? ("Depression" was not found at all.)
2. Confirm whether the approved screen's "AI analysis" row should surface
   the existing `aiPainAnalysis` card content as-is, or a new synthesis
   across Pain + Symptom Impact + the four feeder modules.
3. Confirm this mapping format (columns: source field, HOPE item, approved
   screen location, validation logic, audit source) is correct before it
   is produced for the remaining approved-screen containers (Patient
   Story, Evidence & Intake, Functional Status, Body Systems, Caregiver &
   Support, Safety & Risk, ACP & Goals of Care, Compliance, Finalize).
