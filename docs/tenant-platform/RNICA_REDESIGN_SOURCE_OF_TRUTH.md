# RNICA Redesign Source of Truth

STATUS: LIVE DOCUMENT — DISCOVERY-GROUNDED, UPDATED INCREMENTALLY
AUTHORITY: This document is the single consolidated reference for locked
Owner decisions and repository-verified behavior across the RNICA redesign
track. Where a topic below is marked "NOT YET DISCOVERED," no code search
has been performed for it in this repository during this session, and no
claim should be inferred until a dedicated discovery pass fills that section.

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
This document authorizes no implementation. It records what currently
exists and what the Owner has locked in as future direction.

Related documents (do not duplicate, cross-reference):
- `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md` (narrative placement authority)
- `RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md` (open defect)
- `RNICA_CLINICAL_NARRATIVE_REWIRING_MAP.md` (dead-code discovery)
- `RNICA_SECTION_BREAKDOWN.md` (full 27-section field inventory)

---

## 1. FAST / ECOG / NYHA / PPS / KPS VISIBILITY

### 1.1 Owner-Defined Clinical Rule (LOCKED)

| Scale | Visibility Rule |
|---|---|
| PPS | Always Visible |
| KPS | Always Visible |
| FAST | Visible only for dementia-related diagnoses |
| ECOG | Visible only for oncology-related diagnoses |
| NYHA | Visible only for heart-failure-related diagnoses |

Hide irrelevant scales entirely.

### 1.2 Repository Evidence — Current UI Behavior

`SECTION_CONFIGS.performanceStatus.cards` (`RNICA.jsx:8938-8985`) renders, in
order: Change Since Last Assessment (`declineTracker`), PPS (`hopeCode:
"M1190"`), KPS, ECOG, FAST, NYHA, Functional Decline notes.

Gating is implemented in `renderGenericSection` (`RNICA.jsx:8287-8326`):

```
const showNyha = sectionKey === "performanceStatus" && diagnosesIncludeCategory(fullFormData?.diagnoses, "heartFailure");
const showFast = sectionKey === "performanceStatus" && diagnosesIncludeCategory(fullFormData?.diagnoses, "dementia");
const showEcog = sectionKey === "performanceStatus" && diagnosesIncludeCategory(fullFormData?.diagnoses, "cancer");
...
if (sectionKey === "performanceStatus" && card.title === "NYHA Classification (Heart Failure)" && !showNyha) { return null; }
if (sectionKey === "performanceStatus" && card.title === "FAST Scale (Dementia)" && !showFast) { return null; }
if (sectionKey === "performanceStatus" && card.title === "ECOG Performance Status" && !showEcog) { return null; }
```

**Finding: current UI behavior already matches the Owner's locked rule.**
PPS and KPS cards have no gating condition (always rendered). FAST/ECOG/NYHA
are each conditionally suppressed (`return null`) unless the matching
diagnosis category is present. This contradicts the premise in the prior
"gating verification" request that these scales are "present but not
diagnosis-gated" — repository evidence shows they ARE gated.

`diagnosesIncludeCategory()` (`RNICA.jsx:2553-2565`) checks the Primary
Diagnosis AND every Secondary Diagnosis (not just the principal one),
using two independent match strategies:
1. ICD-10 code regex match (`HOPE_COMORBIDITY_CATEGORIES`, `RNICA.jsx:2496-2510`):
   - `cancer`: `/^C\d/i`
   - `heartFailure`: `/^I50/i`
   - `dementia`: `/^(F0[0-3]|G30|G31\.1)/i`
2. Free-text keyword fallback (`SCALE_GATING_KEYWORDS`, `RNICA.jsx:2532-2537`,
   used when no ICD-10 code is on file — deliberately scoped to scale-gating
   only, per an in-code comment, and NOT shared with the ICD-10-coded HOPE
   comorbidity checkboxes):
   - `cancer`: cancer, carcinoma, malignan, neoplasm, metasta, sarcoma, lymphoma, leukemia
   - `heartFailure`: heart failure, chf, cardiomyopathy, pulmonary edema
   - `dementia`: dementia, alzheimer, senile degeneration, senile psychosis

Multiple scales can be visible simultaneously (e.g., a patient with both a
heart-failure and a dementia diagnosis sees PPS, KPS, NYHA, and FAST, with
ECOG hidden) — this matches the Owner's example exactly, since gating is
per-scale and independently evaluated.

### 1.3 Repository Evidence — Backend Behavior (Second, Independent Gate)

The frontend visibility gate above only controls what the RN *sees*. A
second, entirely separate gating implementation exists in
`clinical_note_validation_engine.py` (lines 1075-1275) that determines what
is *compliance-required* at note-validation time (independent of RNICA.jsx,
operating on `ClinicalNote` records):

```python
DEMENTIA_DIAGNOSIS_KEYWORDS = {
    "DEMENTIA", "ALZHEIMER", "ALZHEIMER'S", "SENILE DEGENERATION",
    "LEWY BODY", "FRONTOTEMPORAL", "VASCULAR DEMENTIA", "PICK",
    "F01", "F02", "F03", "G30",
}
CARDIAC_DIAGNOSIS_KEYWORDS = {
    "CHF", "CONGESTIVE HEART FAILURE", "HEART FAILURE", "END STAGE HEART",
    "END-STAGE HEART", "END STAGE CARDIAC", "END-STAGE CARDIAC",
    "CARDIOMYOPATHY", "ISCHEMIC CARDIOMYOPATHY", "SYSTOLIC HEART FAILURE",
    "DIASTOLIC HEART FAILURE", "I50", "I42",
}
```

These keywords are matched (line 1112-1120) against free-text collected
from `primary_diagnosis`, `diagnosis`, `diagnoses`, `secondary_diagnoses`,
`comorbidities`, `related_diagnoses` fields (both `content` and
`assessment` payload shapes), producing `dementia_related` /
`cardiac_related` booleans — **not** ICD-10 regex matching, unlike the
frontend gate.

`RN_ICA_REQUIRED_FIELD_GROUPS` (lines 116-190+) always requires **PPS and
KPS** ("PPS is required for RN ICA, Update Assessment, and Recertification
Assessment" / same wording for KPS) — matching "Always Visible" for both.

**FAST and NYHA additionally escalate to a compliance-blocking requirement**
when their respective diagnosis flag is true (lines 1225-1274):
```python
if dementia_related and is_required_when_visible("fast_stage"):
    required_scores.append({"key": "fast", "label": "FAST", ...
        "reason": "FAST is required because a dementia-related diagnosis is documented..."})
if cardiac_related and is_required_when_visible("nyha_class"):
    required_scores.append({"key": "nyha", "label": "NYHA", ...
        "reason": "NYHA is required because a cardiac diagnosis is documented..."})
```
A missing required score becomes a `compliance_blocking_items` entry tagged
`RN_ICA_FINALIZATION`, `INITIAL_RN_ICA_TASK_COMPLETION`, and
`BILLING_READINESS` (lines 1275-1308).

**Finding — ECOG has no backend compliance enforcement.** There is no
`cancer_related` flag and no ECOG entry in `required_scores` anywhere in
`clinical_note_validation_engine.py`. ECOG is diagnosis-gated for *display*
in the frontend, but its absence never blocks Lock, Finalization, or
Billing Readiness the way FAST/NYHA absence can. This is a real asymmetry,
not an error in this document — repository evidence supports it exactly as
described.

**Finding — the frontend and backend gating keyword lists are not the same
list and are independently maintained.** Example divergence: frontend
dementia ICD-10 regex includes `F00` and `G31.1`; backend dementia keyword
set includes `F01`/`F02`/`F03`/`G30` (no `F00`, no `G31.1`) plus additional
free-text terms (`LEWY BODY`, `FRONTOTEMPORAL`, `VASCULAR DEMENTIA`,
`PICK`) that the frontend's `SCALE_GATING_KEYWORDS` fallback does not
contain. A chart could exist where the frontend shows FAST (matched via its
own list) while the backend does not treat it as `dementia_related` (or
vice versa), because the two gates never call a shared function or share a
constant. This has not been observed to cause an incident; it is
documented as a structural risk for future redesign/consolidation planning.

### 1.4 Structured Findings / AI Dependency

`structured_findings.py`'s `CONCEPT_REGISTRY` (lines 144-170) explicitly
**excludes** PPS, KPS, ECOG, FAST/FAST stage from AI-assertable concepts,
with an in-code rationale: "Formal scored/computed assessments the
clinician calculates themselves, never states as a raw fact to
transcribe." **NYHA is the sole exception** — `PERF_NYHA_CLASS_I` through
`PERF_NYHA_CLASS_IV` are registered concepts (lines 167-170), meaning the
AI evidence-harvesting pipeline may assert an NYHA class from clinician
narrative text, but may never assert a PPS/KPS/ECOG/FAST value.

`rnica_intelligence.py` was searched for `pps|kps|fast|ecog|nyha|
performanceStatus|performance_status` — **zero matches**. The RNICA
findings-heuristics/recommendation engine does not read any performance
scale as an input.

### 1.5 LCD Dependency

`buildClientLcdFacts()` (`RNICA.jsx:~1477-1513`) — the client-side LCD
eligibility fact-builder — reads `performanceStatus.pps`, `.kps`, `.nyha`,
and `.fast` (via `normalizeFastStage`/`fastStageAtOrBeyond7a`) into the LCD
evaluation payload. **ECOG is not read anywhere in this function.**
Backend equivalents (`poc_generation_service.py:582-590,742-745`,
`eligibility/evidence_harvester.py:40-180`,
`eligibility/eligibility_snapshot_service.py:38-39`,
`recertification_evidence_synthesis.py:364-374`) likewise only ever
reference `pps`/`kps`/`fast`/`nyha` — **none reference ECOG**. ECOG appears
to exist solely for clinical documentation/display purposes and is not an
input to any LCD, POC, or eligibility computation found in this repository.

### 1.6 Longitudinal Trend / Snapshot Dependency

Backend endpoint `GET /patients/{id}/performance-history`
(`app/api/patients.py:4022-4062`) aggregates **PPS, KPS, and FAST only**
(not ECOG, not NYHA) across RNICA + RN Recert assessments for
hospice-decline-trend documentation. This feeds:
- `DeclineTrackerCard` ("Change Since Last Assessment") — `RNICA.jsx:2712-2840`
- `Section1Snapshot`'s "PPS / KPS / FAST" summary item — `RNICA.jsx:9896`

ECOG and NYHA are absent from both the trend history and the top-of-chart
snapshot. This is a pre-existing asymmetry, not something this document
recommends changing.

### 1.7 HOPE Dependency

Only PPS carries an explicit `hopeCode` in the frontend field config
(`hopeCode: "M1190"`, both on the card and the field). KPS, ECOG, FAST, and
NYHA carry no `hopeCode` prop. However, the HOPE-referencing validation
warning (`RNICA.jsx:1044-1046`) is written as an "either/or":
```js
if (!formData.performanceStatus.pps && !formData.performanceStatus.kps) {
  warnings["performanceStatus"] = "HOPE M1190: At least PPS or KPS required";
}
```
This is a **soft warning**, not a hard blocking error (assigned to
`warnings`, not `errors`), and it is satisfied by either field being
non-empty. No HOPE code was found anywhere in the repository for ECOG,
FAST, or NYHA.

### 1.8 Consolidated Classification Table

| Scale | Visibility | Client Validation | Backend Compliance-Blocking | HOPE Code | AI/Structured Findings | LCD Input | Trend History |
|---|---|---|---|---|---|---|---|
| PPS | Always Visible | Soft warning (PPS-or-KPS) | Always required | M1190 | Excluded (computed score) | Yes | Yes |
| KPS | Always Visible | Soft warning (PPS-or-KPS) | Always required | None | Excluded (computed score) | Yes | Yes |
| FAST | Diagnosis-gated (dementia) | None found | Required only if dementia_related | None | Excluded (computed score) | Yes | Yes |
| ECOG | Diagnosis-gated (cancer) | None found | **Not enforced (no cancer_related check exists)** | None | Excluded (computed score) | **No** | **No** |
| NYHA | Diagnosis-gated (heart failure) | None found | Required only if cardiac_related | None | **Included** (NYHA Class I-IV concepts) | Yes | **No** |

### 1.9 Answer to the Final Question

If the RNICA Functional Status workspace were redesigned today:
- **Must always display:** PPS, KPS (repository evidence: no gating
  condition exists for either card; both are unconditionally compliance-
  required regardless of diagnosis).
- **Must display conditionally:** FAST (dementia-related diagnosis), ECOG
  (cancer-related diagnosis), NYHA (heart-failure-related diagnosis) —
  repository evidence: `showNyha`/`showFast`/`showEcog` gating in
  `renderGenericSection`, matching the Owner's stated rule exactly.
- **Must never display when irrelevant:** the same three scales, per the
  same gating logic — confirmed already implemented, not a future change.
- **Open items requiring an Owner decision before Figma finalizes this
  section** (not resolved by this document): (a) whether ECOG should
  receive a backend `cancer_related` compliance-blocking check to match
  FAST/NYHA's pattern, or whether its display-only status is intentional;
  (b) whether the frontend and backend gating keyword/ICD-10 lists should
  be unified into a single shared source to eliminate the divergence risk
  in §1.3.

---

## 2. NARRATIVE PLACEMENT

STATUS: LOCKED (see `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md` — this
section only summarizes; that document remains the authority).

- Authoritative nurse-facing Clinical Narrative: `finalization.clinicalNarrative`.
- `diagnoses.clinicalNarrative` and its sibling fields (`diseaseTrajectory`,
  `rnAddendum`, `clinicianClarification`) are currently unreachable dead UI
  code (no `customRenderer` entry in `SECTION_CONFIGS.diagnoses.cards`).
- Three invisible Diagnosis-section items (Disease Trajectory, RN
  Addendum, Clinician Clarification) are classified **REQUIRES CLINICAL
  REVIEW** — no further classification decision has been made.
- Open defect: existing records with `diagnoses.clinicalNarrative` set and
  `clinicalNarrativeReviewed=false` may be currently unlockable with no
  reachable UI fix (`RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md`).

---

## 3. PATIENT STORY

STATUS: **NOT YET DISCOVERED**

No dedicated code search for a "Patient Story" concept/section/component
has been performed in this repository during this session. Prior
discovery documents (`RNICA_EXPERIENCE_IMPLEMENTATION_PLAN.md` Phase 4)
describe a *proposed future* Patient Story layer (Why Hospice, Primary
Diagnosis, Hospitalization Summary, Caregiver Summary, Current Risks,
Clinical Summary, AI Summary, Missing Information) as a design goal, but
no repository evidence has been gathered confirming which of those exist
today, where, or how they are wired. This section requires its own
discovery pass before this document can certify anything here.

---

## 4. PAIN WORKFLOW

STATUS: **NOT YET DISCOVERED**

No code search for the RNICA Pain section (fields, validation, HOPE
dependencies such as J0900-series pain items, AI dependencies, workflow
placement) has been performed this session. Requires a dedicated
discovery pass before this section can be populated with evidence.

---

## 5. FUNCTIONAL STATUS WORKFLOW

STATUS: **PARTIALLY DISCOVERED**

Section 1 above covers the Performance Status scales (PPS/KPS/FAST/ECOG/
NYHA) in full. Functional Status as a broader concept in this repository
also includes `musculoskeletal.adl.*` (ADL 0-5 dependency scale) and
`functionalDeclineNotes` — these appear as inputs to
`buildClientLcdFacts()` (ADL dependency count, `RNICA.jsx:1483-1494`) and
are excluded from `CONCEPT_REGISTRY` for the same "computed score, not a
transcribable fact" reason as PPS/KPS/ECOG/FAST
(`structured_findings.py` comment, line ~147). No further discovery
(validation rules, HOPE dependency, workflow placement, AI dependency
beyond LCD facts) has been performed on the ADL fields specifically. This
subsection requires a follow-up discovery pass to be considered complete.

---

## 6. CLINICAL WORKFLOW

STATUS: **NOT YET DISCOVERED**

No code search has been scoped to a general "Clinical Workflow" topic this
session (this term was not defined by the Owner with a specific scope).
Requires clarification of scope (e.g., which section, which state machine,
which save/lock/amendment flow) before a discovery pass can be run.

---

## 7. DOCUMENT STATUS SUMMARY

| Topic | Status |
|---|---|
| FAST visibility | LOCKED — matches current repository behavior (§1) |
| ECOG visibility | LOCKED — matches current repository behavior; backend enforcement gap noted (§1) |
| NYHA visibility | LOCKED — matches current repository behavior (§1) |
| Narrative placement | LOCKED (§2, full authority in `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`) |
| Patient Story | NOT YET DISCOVERED (§3) |
| Pain workflow | NOT YET DISCOVERED (§4) |
| Functional Status workflow | PARTIALLY DISCOVERED (§5) |
| Clinical workflow | NOT YET DISCOVERED — scope undefined (§6) |

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
