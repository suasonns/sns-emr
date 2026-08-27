# SNS Plan of Care Generation Matrix 1.0

Status: Governance and specification document — no code changes yet.
Companion to: `SNS_DESIGN_SYSTEM_1.0.md`, `SNS_RNICA_MASTER_MAP_1.0` (Section 11
— Care Planning & Team Recommendations), `RNICA_SECTION_INVENTORY.md`.

---

## 1. Purpose

Today SNS's dependency chain is:

```
Assessment Findings → Narrative
```

California hospice regulation requires the assessment to drive an
individualized Plan of Care, including symptoms, goals, interventions,
disciplines, service frequencies, supplies, equipment, and treatments. The
required chain is:

```
Assessment Findings → Problem → Goal → Intervention → Discipline
  → Visit Frequency → Task → Plan of Care
```

This document is the matrix needed to build the **Care Plan Engine** — the
logic that turns RNICA from a data-entry form into a system that
automatically produces Problems, Goals, Interventions, Disciplines,
Frequencies, Tasks, and the individualized Plan of Care.

This document defines the standard only. Implementation of the Care Plan
Engine requires a separate, explicit go-ahead (same governance rule as
`SNS_DESIGN_SYSTEM_1.0.md` §12 and the RNICA pilot).

---

## 2. Clinical Finding → Problem/Goal/Intervention Matrix

### 2.1 Pain

- **Finding:** Pain ≥ 4/10
- **Problem:** Acute Pain, or Chronic Pain
- **Goal:** Pain managed at acceptable level; patient reports improved
  comfort; patient/caregiver understands pain regimen
- **Interventions:** Pain assessment every visit; medication management;
  non-pharmacologic interventions; caregiver education; monitor side effects
- **Discipline:** RN
- **Frequency Suggestion:** 1–3 visits/week depending on severity
- **Action Center Trigger:** Medication Review, Physician Contact

### 2.2 Dyspnea

- **Finding:** Dyspnea
- **Problem:** Impaired Breathing Pattern
- **Goal:** Reduced respiratory distress; improved comfort
- **Interventions:** Assess respiratory status; positioning; oxygen
  management; medication monitoring; energy conservation education
- **Discipline:** RN
- **Frequency Suggestion:** 1–3 visits/week
- **Action Center Trigger:** Oxygen, Medication, Physician Contact
- **Note:** Dyspnea is specifically identified in CMS terminal-status
  guidance as an important symptom and decline indicator.

### 2.3 Anxiety / Agitation

- **Problem:** Anxiety, or Terminal Agitation
- **Goal:** Reduced anxiety; improved comfort
- **Interventions:** Medication monitoring; education; supportive
  counseling; environmental modification
- **Discipline:** RN, SW, Chaplain

### 2.4 Integumentary (Skin Breakdown / Wounds)

- **Finding:** Pressure Injury, Skin Tear, Non-healing Wound
- **Problem:** Impaired Skin Integrity, Risk For Skin Breakdown, Delayed
  Wound Healing, Altered Tissue Integrity
- **Goal:** Prevent further breakdown; promote comfort
- **Interventions:** Wound assessment; dressing changes; pressure relief;
  nutrition education
- **Discipline:** RN, HHA
- **Action Center Trigger:** Wound Supplies, DME
- **Note:** Pressure ulcers are expressly referenced as significant clinical
  indicators of decline within hospice terminal-status guidance. This
  section is named "Integumentary" to match the actual RNICA assessment
  section name (not "Skin/Wounds"), and owns pressure injuries, wounds,
  skin tears, rashes, bruising, drainage, and surgical wounds.

### 2.5 Nutrition Decline

- **Finding:** Weight Loss, Poor Appetite, Reduced Intake
- **Problem:** Nutritional Deficit
- **Goal:** Maintain intake as tolerated; promote comfort
- **Interventions:** Nutrition assessment; food preference education;
  hydration support
- **Discipline:** RN, SW
- **Note:** Nutritional decline and weight loss are established indicators
  supporting terminal prognosis documentation.

### 2.6 Falls

- **Finding:** Recent Fall, Unsteady Gait, Weakness
- **Problem:** Fall Risk
- **Goal:** Prevent injury
- **Interventions:** Safety education; transfer education; equipment review
- **Discipline:** RN, HHA
- **Action Center Trigger:** Walker, Wheelchair, Hospital Bed

### 2.7 ADL Decline

- **Finding:** Dependence With ADLs
- **Problem:** Self Care Deficit
- **Goal:** Maintain dignity and comfort
- **Interventions:** Caregiver education; personal care support
- **Discipline:** HHA, RN
- **Note:** Dependence in ADLs is a major non-disease-specific hospice
  eligibility factor and should drive care planning.

### 2.8 Caregiver Burnout

- **Finding:** Overwhelmed Caregiver, Unsafe Caregiver Situation
- **Problem:** Caregiver Stress
- **Goal:** Improve caregiver coping
- **Interventions:** Support; community resources; respite discussion
- **Discipline:** SW

### 2.9 Spiritual Distress

- **Finding:** Spiritual Concerns
- **Problem:** Spiritual Distress
- **Goal:** Peace and spiritual support
- **Interventions:** Chaplain visits; counseling
- **Discipline:** Chaplain

### 2.10 Bereavement Risk

- **Finding:** High Bereavement Risk
- **Problem:** Anticipatory Grief
- **Goal:** Prepare family; provide support
- **Interventions:** Bereavement services; counseling
- **Discipline:** Bereavement, SW, Chaplain

---

## 3. Disease-Specific Matrix

### 3.1 CHF

- **Finding:** NYHA IV, Dyspnea, Edema
- **Problem:** End Stage Heart Disease
- **Interventions:** Monitor fluid retention; monitor respiratory status;
  medication review
- **Discipline:** RN
- **Note:** Heart disease criteria include severe functional limitation and
  symptom burden.

### 3.2 COPD

- **Finding:** Oxygen, Dyspnea, Hypoxia
- **Problem:** Advanced Pulmonary Disease
- **Action Center Trigger:** Oxygen, Nebulizer
- **Note:** Pulmonary disease guidance relies heavily on disabling dyspnea,
  progression, and hypoxemia.

### 3.3 Dementia

- **Finding:** FAST stage, ADL Dependence, Weight Loss
- **Problem:** Advanced Dementia
- **Interventions:** Safety; nutrition; caregiver support
- **Discipline:** RN, SW, HHA
- **Note:** Dementia eligibility criteria are strongly tied to FAST stage,
  ADL dependence, communication loss, infections, and nutritional decline.

---

## 4. Frequency Generation Matrix

| Discipline | Acuity / Trigger | Suggested Frequency |
|---|---|---|
| RN | High acuity — pain, dyspnea, active decline | 2–3 visits/week |
| RN | Moderate — stable symptoms | 1–2 visits/week |
| RN | Low — stable | Weekly or per agency standard |
| HHA | Dependent ADLs | 3–7 visits/week |
| SW | Caregiver stress | 2x/month or PRN |
| Chaplain | Spiritual need | 2x/month or PRN |

These are suggestions the Care Plan Engine proposes to the clinician — not
auto-finalized orders. A human discipline/frequency decision always remains
in the loop (consistent with `SNS_DESIGN_SYSTEM_1.0.md` §2.4 — Structured
Evidence Plus Clinical Judgment).

---

## 5. Final SNS Care Plan Engine Logic

```
Assessment
  ↓
Clinical Findings
  ↓
Problem Generation
  ↓
Goal Generation
  ↓
Intervention Generation
  ↓
Discipline Recommendation
  ↓
Visit Frequency Recommendation
  ↓
Task Generation
  ↓
Plan of Care
  ↓
Narrative Validation
  ↓
Finalization
```

This is the logic chain the Care Plan Engine must implement so that RNICA
findings automatically propose Problems, Goals, Interventions, Disciplines,
Frequencies, and Tasks feeding an individualized Plan of Care — as required
by California hospice plan-of-care regulations (goals, outcomes, services,
frequencies, symptoms, supplies, equipment, and interventions must all be
incorporated).

---

## 6. Governance

- This matrix is a proposal/decision-support engine, not an auto-finalizing
  one. Every generated Problem/Goal/Intervention/Discipline/Frequency is a
  suggestion presented to the clinician for review and edit before it
  becomes part of the authoritative Plan of Care (per §2.3 Identity of Data
  and §2.4 Structured Evidence Plus Clinical Judgment in
  `SNS_DESIGN_SYSTEM_1.0.md`).
- Findings, Action Center triggers, and disease-specific criteria in this
  document must be reconciled against the actual RNICA field inventory
  (`SNS_RNICA_SECTION_INVENTORY_1.0.md`) before implementation, to
  confirm each "Finding" here maps to a real, existing structured field
  (not a field that still needs to be added).
- No code changes are authorized by this document alone.

---

## 7. POC Generation Rule (Per-Section POC, Not End-of-Assessment)

### 7.1 Principle

Nurses do not think "complete entire assessment → build care plan." They
think "found a problem → address the problem → move on." The Care Plan
Engine must match that mental model: **a problem is created and addressed
at the point it is found**, not deferred to a single end-of-assessment step.

### 7.2 Rule

> Every RNICA clinical section that can generate a problem shall contain a
> local POC action row:
>
> `[ Create POC ]` `[ View POC ]` `[ Update POC ]`
>
> The section becomes the **origin** of the problem, not just an input to a
> later, separate care-planning step.

### 7.3 Per-section states

Each qualifying section (Pain, Respiratory, Integumentary, Nutrition,
Caregiver Assessment, Falls/Safety, Psychosocial, Spiritual, Bereavement,
and any other section whose findings map to a row in §2/§3 above) renders
one of three states directly beneath its findings, using the Facesheet Card
Standard (`SNS_DESIGN_SYSTEM_1.0.md` §7):

1. **No POC exists:** `POC Status: Not Created` + `[ Create POC ]`.
2. **Suggested (preferred over a bare Create button):** `Suggested POC
   Available — Based on: ✓ <finding 1>, ✓ <finding 2>` + `[ Review
   Suggestion ]`. Clicking reviews/edits the auto-generated Problem, Goal,
   Interventions, Discipline, and Frequency from §2/§3 of this matrix before
   saving — never silently auto-saves.
3. **Active:** `POC Status: ✓ Active` + the current Problem/Goal summary +
   `[ View POC ]` `[ Update POC ]`.

### 7.4 Example (Pain section)

```
Pain Score: 8/10
Location: Back
Frequency: Constant
Current Medication: Morphine
----------------------
Pain POC Status
No Pain POC Exists
[ Create POC ]
```

On click, SNS generates (per §2.1 above) Problem: Acute Pain; Goal: Pain
maintained at acceptable level; Interventions: Monitor pain, Medication
review, Educate caregiver; Discipline: RN; Frequency: 2x/week. Nurse
reviews, edits if needed, saves. The Pain section then shows:

```
Pain POC Status
✓ Active
Problem: Acute Pain
Goal: Pain controlled
[ View POC ]
[ Update POC ]
```

The same pattern applies to Respiratory (Dyspnea → Impaired Breathing
Pattern), Integumentary (Stage III injury → Impaired Skin Integrity, which
then automatically appears in the master POC), Caregiver Assessment (High
Caregiver Burden → Caregiver Stress), and Nutrition (Weight Loss/Poor
Intake → Nutritional Deficit) — each generated directly from that section's
own findings, using the matrix in §2/§3.

### 7.5 Section 11 is redefined

Because most POC entries are now created at their point of origin (in-section,
per §7.2), Section 11 is no longer a creation step. Rename it:

- **From:** "Section 11 — Care Planning & Team Recommendations"
- **To:** "Section 11 — Master Plan of Care Review"

Section 11 becomes a read-oriented roll-up of every active problem created
across sections (Pain Problem ✓ Active, Respiratory Problem ✓ Active,
Nutrition Problem ✓ Active, Integumentary Problem ✓ Active, Caregiver
Stress ✓ Active, etc.) — the nurse reviews all active problems in one
place before Finalization, rather than authoring the Plan of Care from
scratch at the end. This is a rename/reframing of an existing planned
section (see `SNS_RNICA_SECTION_INVENTORY_1.0.md` / RNICA Master Map Section 11),
not a new section.

### 7.6 Revised assessment-to-POC flow

```
Pain Section
→ Create Pain POC

Respiratory Section
→ Create Respiratory POC

Integumentary Section
→ Create Integumentary POC

Nutrition / Hydration Section
→ Create Nutrition POC

Falls / Safety Section
→ Create Fall Risk POC

Caregiver Assessment
→ Create Caregiver POC

Psychosocial Assessment
→ Create Psychosocial POC

Spiritual Assessment
→ Create Spiritual POC

Bereavement Assessment
→ Create Bereavement POC

↓

Master POC Review

↓

Finalization
```

This still respects §2.1 (Patient Comfort Before Documentation Completion)
and the Admission Action Center standard — creating a per-section POC is
itself a lightweight, non-blocking action, not a gate on continuing the
assessment.

### 7.7 Master Plan of Care Synchronization Model

**Principle.** There is only ONE Master Plan of Care, ONE Problem record,
ONE Goal Set, and ONE Intervention Set for a given clinical problem. SNS
must never create duplicate POCs simply because a problem appears in more
than one assessment section. The individualized Plan of Care is a single
authoritative record derived from assessment findings, not a per-section
artifact.

**Section ownership model.** Each RNICA section is the *origin* of specific
clinical problems. This must include every RNICA assessment domain, not
just the major symptom areas, so there is one authoritative mapping to
build from:

| Originating section | Problems owned |
|---|---|
| Pain | Acute Pain, Chronic Pain |
| Neurological | Cognitive Impairment, Communication Deficit, Confusion, Safety Risk |
| Cardiovascular | Fluid Volume Excess, Cardiac Symptoms, End Stage Heart Disease |
| Respiratory | Dyspnea, Impaired Breathing Pattern, Oxygen Dependency |
| Gastrointestinal | Nausea, Vomiting, Constipation, Poor Intake |
| Genitourinary | Urinary Elimination Problem, Incontinence, Catheter Management Problem |
| Endocrine | Glucose Management Problem, Endocrine Symptom Management |
| Musculoskeletal | Weakness, Mobility Deficit, Transfer Assistance Required, Fall Risk |
| Nutrition / Hydration | Nutritional Deficit, Weight Loss, Poor Intake, Hydration Deficit |
| Integumentary | Impaired Skin Integrity, Pressure Injury, Risk For Skin Breakdown, Delayed Wound Healing, Altered Tissue Integrity |
| Falls / Safety | Fall Risk, Injury Risk, Unsafe Environment |
| Psychosocial | Psychosocial Distress, Family Stress, Adjustment Difficulties |
| Spiritual Assessment | Spiritual Distress |
| Bereavement Assessment | Anticipatory Grief, Bereavement Risk |
| Caregiver Assessment | Caregiver Stress, Caregiver Burden, Unsafe Caregiver Situation |

Note: "Integumentary" (not "Skin/Wounds") is used throughout this document
because that is the actual RNICA assessment section name (see
`SNS_RNICA_SECTION_INVENTORY_1.0.md`), and problem ownership should always
follow the real RNICA section structure.

**Synchronization Rule 1 — Create propagates immediately.** When a nurse
selects `[ Create POC ]` inside a section, SNS shall generate the suggested
Problem, Goal, Interventions, Discipline Recommendation, and Visit
Frequency Recommendation, and save to the Master Plan of Care immediately
(section → Master POC). No second approval screen is required.

**Synchronization Rule 2 — Section-side updates propagate.** When a nurse
updates a problem from within its originating section (e.g. editing the
Pain goal from "Comfort maintained" to "Pain level maintained ≤ 3/10"), SNS
shall immediately update both the section and the Master Plan of Care. No
duplicate records are created.

**Synchronization Rule 3 — Master-side updates propagate back.** When a
nurse updates a problem from Master Plan of Care Review (e.g. changing Pain
Frequency from 2x/week to 3x/week), SNS shall immediately update both the
Master Plan of Care and the originating section, which reflects the new
value (e.g. the Pain section immediately displays Frequency: 3x Week).

**Synchronization Rule 4 — Resolved problems.** When a nurse selects
"Problem Resolved," status becomes `Resolved`. The problem is removed from
the Active Problem List but remains visible in Historical Problem History
for auditability and clinical review — it is never deleted.

**Synchronization Rule 5 — Duplicate prevention.** SNS must prevent the
same problem (e.g. "Acute Pain") from being created multiple times. If a
matching active problem already exists, SNS displays "Existing Pain Problem
Found" with `[ View Existing ]` / `[ Update Existing ]` instead of creating
a new record.

**Synchronization Rule 6 — Cross-section linking.** A finding such as
Dyspnea may be identified in Respiratory, Disease-Specific Criteria, and
HOPE. All sections reference the ONE Dyspnea Problem within the Master Plan
of Care — SNS must never create separate Dyspnea POCs per section.

### 7.8 Section-Level POC Controls

Every clinical section capable of generating a problem shall display one of
four states:

- **No Existing POC** — `POC Status: Not Created` · `[ Create POC ]`
- **Suggested POC Available** — "Suggested Problem Available — Based On: ✓ Pain 8/10, ✓ Constant Pain" · `[ Review Suggestion ]`
- **Active POC** — `POC Status: ✓ Active` · Problem: *Acute Pain* · Goal: *Pain Maintained ≤ 3/10* · `[ View POC ]` `[ Update POC ]`
- **Resolved POC** — `POC Status: Resolved` · Resolved On: `<Date>` · `[ View History ]`

(This refines the 3-state model in §7.3 by adding the explicit "Suggested"
review-gate copy and the "Resolved" state's historical-visibility behavior,
consistent with Synchronization Rule 4 in §7.7.)

### 7.9 Section 11 Clarification

Section 11 does **not** create problems, originate goals, or originate
interventions. It functions solely as **Master Plan of Care Review**,
containing: all Active Problems, all Goals, all Interventions, Discipline
Assignments, Visit Frequencies, Tasks, Education, and Referrals. The nurse
verifies completeness, accuracy, and appropriateness here before
Finalization — this reinforces, and does not change, the §7.5 rename.

### 7.10 Final GitHub Build Rule

> Every qualified RNICA section must be able to: Create POC, View POC,
> Update POC, Resolve POC.
>
> All POC changes synchronize bidirectionally with a single authoritative
> Master Plan of Care.
>
> The originating section owns the problem definition.
>
> Section 11 (Master Plan of Care Review) serves as the consolidated review
> and governance workspace and is not the primary location where problems
> are first created.

This makes the model build-ready: where POCs originate, how updates flow
in both directions, how duplicates are prevented, how resolved problems
behave, and how the Master POC stays synchronized — while preserving the
hospice requirement that assessment findings directly drive the
individualized Plan of Care.

### 7.11 Disease-Specific Linking Rule

Disease-Specific Criteria sections (§3: CHF, COPD, Dementia, etc.) do
**not** automatically create new problems. Instead, they must **link to
existing POC problems** whenever a matching symptom-based problem already
exists:

- **COPD** → links to the Dyspnea problem; links to the Oxygen Dependency
  problem.
- **CHF** → links to the Fluid Volume Excess problem; links to the Dyspnea
  problem.
- **Dementia** → links to the Cognitive Impairment problem; links to the
  ADL Dependency problem.

SNS must avoid creating a duplicate disease-specific problem when a
symptom-based problem already exists (per Synchronization Rule 5, §7.7).
This keeps the care plan patient-centered instead of disease-label
centered — disease-specific findings support and corroborate the overall
clinical picture and plan of care, they do not fork it into parallel
problem records.

### 7.12 Master Plan of Care Governance Rule

Every problem in the Master Plan of Care must have:

- ✓ Problem
- ✓ Goal
- ✓ At least one Intervention
- ✓ Assigned Discipline
- ✓ Frequency
- ✓ Originating RNICA Section
- ✓ Created By
- ✓ Last Modified By
- ✓ Last Updated Date
- ✓ Status (Active / Resolved / Inactive)

A Plan of Care cannot be finalized with a missing Goal, missing
Intervention, missing Discipline, or missing Frequency, unless explicitly
documented and approved by clinical workflow rules (an exception path, not
the default). This governs Section 12 — Final Review & Finalization
validation (`SNS_RNICA_MASTER_MAP_1.0.md` Section 12) and is additive to,
not a replacement for, the HOPE/Narrative/POC validation gaps already
flagged in `SNS_RNICA_SECTION_INVENTORY_1.0.md`.

