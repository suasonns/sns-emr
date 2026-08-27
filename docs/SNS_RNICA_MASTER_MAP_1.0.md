# SNS RNICA Master Map 1.0

Status: **APPROVED FOR GOVERNANCE REVIEW — Architecture Complete. No
Further Architecture Work Required.**
Next Deliverable: `SNS_RNICA_SECTION_INVENTORY_1.0`.
**No Code Changes Authorized Without Separate Approval.**
Companion to: `SNS_DESIGN_SYSTEM_1.0.md`, `SNS_POC_GENERATION_MATRIX_1.0.md`,
`SNS_RNICA_SECTION_INVENTORY_1.0.md` (implementation-detail inventory).

This is the target 12-section architecture for the RNICA redesign, plus a
global (non-numbered) Admission Action Center. It supersedes the looser
"tier" language used in earlier drafts of this governance thread — treat the
section numbers below as canonical for all future references.

## Governance Freeze

As of this version, the following artifacts are **frozen** for the
duration of the `SNS_RNICA_SECTION_INVENTORY_1.0` inventory work (Field,
Database, API, Validation, Narrative Source, HOPE, Audit, Action Center
Trigger, POC Evidence, and Migration Complexity mapping):

- Section Names
- Section Numbers
- POC Ownership
- Master POC Rules
- Action Center Rules
- Dependency Flow
- Evidence Requirements
- Governance Rules

Any future change to these artifacts must go through a **Version 1.1
governance process** (a new, explicit revision cycle), not through ongoing
architectural edits made while inventory work is in progress. This
prevents Field → Database → API → UI mapping from being done against a
moving target. The next deliverable is `SNS_RNICA_SECTION_INVENTORY_1.0`,
not further architecture changes to this document.

---

## Section 1 — Patient & Encounter Snapshot

**Source:** Patient Demographics, Caregiver Assessment, Advanced Care
Planning, Facesheet.

**Contains:** Patient Name, MRN, DOB, Benefit Period, Level of Care, Primary
Diagnosis, Related Diagnoses, Code Status, Primary Caregiver, Decision
Maker, Emergency Contact, Residence Type, Facility, Attending Physician,
Medical Director.

**POC Functions:** View Existing POC, View Active Problems, View Goals,
View Interventions. **Does NOT create POC — snapshot only.**

Read-only from authoritative sources (per `SNS_DESIGN_SYSTEM_1.0.md` §2.3
Identity of Data — this section displays, it does not own, this data).

---

## Section 2 — Immediate Needs & Symptom Triage

**Source:** Pain Assessment, Symptom Impact, Admission Triage.

**Contains:** Pain, Dyspnea, Agitation, Anxiety, Nausea, Vomiting,
Secretions, Bleeding, Acute Distress, Current Interventions, Response.

**POC Panel — Suggested Problems:** Acute Pain, Impaired Breathing Pattern,
Anxiety, Agitation. Controls: `[ Add To POC ]` `[ View POC ]`
`[ Update POC ]`.

**Triggers / Action Center Triggers:** Medications, Physician Contact,
Urgent Actions.

**Launches:** Admission Action Center.

---

## Section 3 — Disease History & Clinical Trajectory

**Source:** Diagnoses, Family Interview, Hospitalization History, Disease
Trajectory.

**Contains:** Terminal Diagnosis, Related Diagnoses, Comorbidities,
Hospitalizations (3/6/12 months), ER Visits, Falls, Weight Changes,
Functional Changes, Disease Progression.

**POC Panel — Suggested Problems:** Disease Progression, Frequent
Hospitalization, Risk For Decline. **POC Functions:** Add To POC, Update
Goal, Update Intervention.

**Supports:** LCD Documentation, Eligibility Support, Narrative.

CMS specifically expects documentation of decline, disease progression,
utilization, clinical status, and patient-specific evidence.

---

## Section 4 — Functional & Performance Status

**Source:** Performance Status, ADLs, Strength Assessment.

**Contains:** PPS, KPS, FAST, NYHA, ECOG; Eating, Bathing, Dressing,
Transfer, Ambulation, Continence; Strength, Endurance.

**Comparison Engine:** Previous PPS vs Current PPS; Previous ADLs vs
Current ADLs.

**POC Panel — Suggested Problems:** ADL Dependency, Functional Decline,
Self Care Deficit, Risk For Falls. **POC Controls:** Add, View, Update,
Resolve.

Functional decline and ADL dependence are major hospice eligibility and
care-planning drivers.

---

## Section 5 — Head-To-Toe Clinical Assessment

**Source:** Neurological, Cardiovascular, Respiratory, Gastrointestinal,
Genitourinary, Endocrine, Musculoskeletal, Nutrition/Hydration, Infection,
Integumentary.

**Subcards:** one per system above. **Every sub-card gets its own POC
controls** (`[ Add To POC ]` `[ View POC ]` `[ Update POC ]`) in addition to
Current Findings, Clinical Comment, Previous Findings, Change Indicator.

Per-subcard POC problems / Action Center triggers:

- **Neurological** — Contains: LOC, Cognition, Communication, Behaviors,
  Neurological Findings. POC Problems: Cognitive Impairment, Communication
  Deficit, Confusion, Safety Risk.
- **Cardiovascular** — Contains: Blood Pressure, Edema, Perfusion, Heart
  Symptoms. POC Problems: Fluid Volume Excess, Cardiac Symptoms, End Stage
  Heart Disease. Supports CHF/heart disease documentation.
- **Respiratory** — Contains: Dyspnea, Breath Sounds, Oxygen, Pulse Ox,
  Secretions, Cough. POC Problems: Impaired Breathing Pattern, Dyspnea,
  Oxygen Dependency. Action Center: Oxygen, Nebulizer, Medication. Advanced
  pulmonary disease and dyspnea frequently require symptom interventions
  and equipment planning.
- **Gastrointestinal** — Contains: Appetite, Nausea, Vomiting,
  Constipation, Bowel Status. POC Problems: Nausea, Constipation, Poor
  Intake, GI Symptom Burden.
- **Genitourinary** — Contains: Voiding, Catheter, Continence. POC
  Problems: Urinary Elimination Problem, Incontinence, Catheter Management
  Problem.
- **Endocrine** — Contains: Glucose, Endocrine Symptoms. POC Problems:
  Glucose Management Problem, Endocrine Symptom Management.
- **Musculoskeletal** — Contains: Strength, Mobility, Transfers, Balance.
  POC Problems: Weakness, Mobility Deficit, Transfer Assistance Required,
  Fall Risk.
- **Nutrition / Hydration** — Contains: Weight, Weight Change, Appetite,
  Intake, Hydration. POC Problems: Nutritional Deficit, Weight Loss, Poor
  Intake, Hydration Deficit. Action Center: Nutritional Supplies,
  Education. Nutritional decline and weight loss are important clinical
  indicators supporting hospice documentation.
- **Infection** — Contains: Active Infection, Recurrent Infection,
  Antibiotic Use, Temperature, Infection History. POC Problems: Active
  Infection, Infection Risk, Recurrent Infection. Action Center: Physician
  Contact, Medication Review. Recurrent infections are recognized clinical
  indicators supporting prognosis documentation and care planning.
- **Integumentary** ✅ — Contains: Skin Assessment, Pressure Injuries,
  Wounds, Skin Tears, Surgical Wounds, Drainage, Bruising, Rashes,
  Non-Healing Wounds. POC Problems: Impaired Skin Integrity, Pressure
  Injury, Risk For Skin Breakdown, Delayed Wound Healing, Altered Tissue
  Integrity. Goals: Promote Comfort, Prevent Further Breakdown, Prevent
  Infection, Promote Healing. Interventions: Wound Assessment, Wound Care,
  Dressing Changes, Pressure Relief, Repositioning, Caregiver Education.
  Disciplines: RN, HHA. Action Center: Wound Supplies, Dressings, Hospital
  Bed, Low Air Loss Mattress, Pressure Relief Cushion. Pressure injuries
  and skin breakdown support both care planning and terminal-status
  documentation. (Named "Integumentary," matching the actual RNICA
  assessment section name — not "Skin/Wounds.")

---

## Section 6 — Disease Specific Criteria & Eligibility Support

**Source:** Diagnosis, Performance Status, Clinical Systems.

**Contains:** CHF, COPD, Cancer, ALS, Dementia, Stroke, Renal, Liver, HIV
(and Other LCD Criteria).

**POC Panel — Link To Existing Problem First.** Create a new
disease-specific problem only if no appropriate existing problem exists.
**POC Functions:** View, Update, **Link To Existing Problem** — **do NOT
create duplicate problems.** Disease-specific evidence should support the
existing care plan (this section links into a problem already created in
Section 2/4/5, it does not mint a new, competing one). Example: COPD
should usually connect to the existing Dyspnea and Oxygen Dependency
problems — not create a separate "Advanced Pulmonary Disease" problem
alongside them and produce duplicate planning. Likewise CHF links to Fluid
Volume Excess and Dyspnea; Dementia links to Cognitive Impairment and ADL
Dependency (see `SNS_POC_GENERATION_MATRIX_1.0.md` §7.11). Disease-specific
sections should support and enrich the clinical picture rather than
multiply care-plan records unnecessarily.

**Supports:** Eligibility Narrative, Certification, Recertification.

Should align with LCD disease-specific and non-disease-specific decline
guidance.

---

## Section 7 — HOPE & Symptom Follow-Up

**Source:** HOPE, Imminent Death, SFV, Symptom Follow-up.

**Contains:** HOPE Admission, HOPE Update, HOPE Symptom Data, J-Items,
Imminent Death, SFV Triggers, Submission Tracking.

**POC Panel:** View Related Problems, Update Existing Problem. **No direct
POC generation here** — HOPE should update existing symptom-related
problems (created in Section 2/5), not create new ones.

Must remain isolated for CMS reporting (per `SNS_DESIGN_SYSTEM_1.0.md`'s
original HOPE-separation principle — do not blend into general nursing
assessment sections).

---

## Section 8 — Whole Person & Caregiver Assessment

**Source:** Caregiver Assessment, Psychosocial, Spiritual, Bereavement,
Teaching Needs, Personal Care.

**Contains:** Caregiver Capacity, Caregiver Burden, Psychosocial Findings,
Spiritual Findings, Bereavement Risk, Cultural Needs, Language, Teaching
Needs, HHA Needs.

**Per-subsection POC problems:**
- Caregiver — Caregiver Stress, Caregiver Burden, Unsafe Caregiver Situation
- Psychosocial — Psychosocial Distress, Family Stress, Adjustment Difficulties
- Spiritual — Spiritual Distress
- Bereavement — Bereavement Risk, Anticipatory Grief
- Personal Care — ADL Assistance Required, Personal Care Deficit
- Teaching — Knowledge Deficit

**POC Controls:** Add, Update, View, Resolve.

Supports interdisciplinary planning required in hospice care. These areas
directly support interdisciplinary planning and individualized care
planning.

---

## Section 9 — Safety, Environment, Equipment & Supplies

**Source:** Safety, DME Requirements, Supply Requirements.

**Contains:** Fall Risk, Disaster Preparedness, Environmental Risks,
Transfer Safety, Existing DME, Needed DME, Existing Supplies, Needed
Supplies, Oxygen.

**Problems:** Fall Risk, Injury Risk, Unsafe Environment. **POC Controls:**
Add, Update, View. **Action Center:** Hospital Bed, Wheelchair, Walker,
Commode, Supplies, Oxygen.

**Does NOT create orders. Only identifies needs.** (Order creation is the
Admission Action Center's job — see below.)

---

## Section 10 — Clinical Narrative & Disease Trajectory

**Source:** Everything above. **This is the most important section.**

**Generated:** Clinical Summary, Terminal Disease Summary, Clinical Decline,
Functional Decline, Symptom Burden, Disease Progression, Prognosis Support.

**Editable:** RN Addendum.

**Functions:** View All Problems, View Goals, View Interventions.
**Narrative references POC. Narrative does not create POC.**

Narrative near the end follows CMS guidance that documentation should paint
a complete clinical picture and include decline and supporting evidence,
and should reflect the patient-specific picture documented throughout the
assessment.

---

## Section 11 — Master Plan of Care Review

> **Renamed** from "Care Planning & Team Recommendations." See
> `SNS_POC_GENERATION_MATRIX_1.0.md` §7.5 for the rationale: most POCs are
> now created at their point of origin inside each clinical section (Pain,
> Respiratory, Skin, Nutrition, Caregiver, etc. each get their own `[ Create
> POC ]` / `[ View POC ]` / `[ Update POC ]` actions), so this section is a
> **review roll-up and governance screen**, not the creation step. **This
> section DOES NOT create the initial problem — problems originate from
> assessment sections; this section reviews and governs them.**

**Source:** Full Assessment (aggregated).

**Contents (grouped by problem):** Active Problems, Goals, Interventions,
Disciplines, Visit Frequencies, Tasks, Education, Referrals — e.g.:

```
Problem: Acute Pain
Goal: Pain controlled
Interventions: Assess every visit, Medication review
Discipline: RN
Frequency: 2x week
```

**Controls:** Link Existing Problem, Edit Problem, Resolve Problem, Merge
Problem, Deactivate Problem. **No "Add Problem" control** — Section 11 is
a review/governance workspace, not a problem-creation surface. If nurses
could create problems directly inside the Master POC, they would bypass
assessment documentation, inverting the required architecture (Assessment
→ Problem, never Problem → Assessment later). Assessment findings must
remain the origin of the care plan.

**Output:** Plan of Care.

California plan-of-care requirements include goals, outcomes, services,
frequencies, symptoms, supplies, equipment, and interventions.

---

## Section 12 — Final Review & Finalization

**Validates:** Assessment Complete, Required POCs Reviewed, Goals Present,
Interventions Present, Discipline Assigned, Frequency Assigned, HOPE
Complete, Narrative Reviewed.

**Signatures:** RN Signature, Review Date, Audit Trail.

---

## Master Sync Rules (Critical)

The per-section POC panels (Sections 2–9) and the Master Plan of Care
Review (Section 11) are **two views of the same data, not two data
stores.** This is the architecture that makes per-section POC creation
(`SNS_POC_GENERATION_MATRIX_1.0.md` §7) safe rather than a source of
duplicate/conflicting problem records.

- **Rule 1:** Create POC in a section → immediately appears in Master POC
  (Section 11).
- **Rule 2:** Update POC in a section → immediately updates Master POC.
- **Rule 3:** Update POC in Master POC → immediately updates the
  originating section.
- **Rule 4:** There is only ONE Problem, ONE Goal Set, and ONE Intervention
  Set for each problem. No duplicates. (This is why Section 6 — Disease
  Specific Criteria — must "Link To Existing Problem" rather than create a
  new one, and why Section 7 — HOPE — only updates existing
  symptom-related problems.)
- **Rule 5:** Master POC (Section 11) is a synchronized *view*. It is not a
  separate database/table from the per-section POC entries.

**Origin Metadata Requirement.** Every Problem must store: Originating
Section, Originating Finding(s), Created By, Created Date, Last Updated By,
Last Updated Date, Status (Active / Resolved / Inactive), Related Action
Center Requests, Related Narrative References. This makes survey review,
audit review, recertification review, and interdisciplinary review much
easier, because every care-plan item can be traced back to the assessment
evidence that generated it. (This is additive to, and consistent with, the
Master Plan of Care Governance Rule in `SNS_POC_GENERATION_MATRIX_1.0.md`
§7.12.)

**POC Evidence Requirement.** Every POC problem shall contain at least one
linked assessment finding as its source evidence. Examples:

```
Problem: Impaired Breathing Pattern
Source Evidence: Respiratory Assessment —
  Dyspnea: Moderate
  Oxygen: 2L NC
  Pulse Ox: 88%

Problem: Nutrition Deficit
Source Evidence:
  Weight Loss: 15 lbs
  Appetite: Poor
  Intake: 25%
```

Rules:
- A problem cannot exist without linked evidence.
- Assessment findings remain the authoritative source.
- POC records must be traceable back to assessment findings.
- Section 11 displays source evidence links alongside each problem.

Benefits: Survey Readiness, Audit Readiness, Recertification Review, IDG
Review, Narrative Support, LCD Support. This supports documentation that
demonstrates functional decline, symptom burden, disease progression,
nutritional decline, recurrent complications, and patient-specific evidence
— rather than unsupported conclusions.

**GitHub one-sentence build rule:** Every RNICA section capable of
identifying a clinical problem shall contain `Add To POC`, `View POC`, and
`Update POC` controls. All changes synchronize bidirectionally with a
single Master Plan of Care. Section 11 serves as Master Plan of Care Review
and Governance, not the primary point of problem creation.

**Master Synchronization Rule diagram:**

```
Section Creates Problem
  ↓
Problem Added To Master POC
  ↓
Update In Section
  ↓
Updates Master POC
  ↓
Update In Master POC
  ↓
Updates Originating Section
```

There is only ONE Problem, ONE Goal Set, ONE Intervention Set, and ONE
Master Plan of Care. No duplicates.

This is the most nurse-friendly architecture because it follows the natural
workflow — Find problem → Create/Update POC immediately → Continue
assessment → Review all POCs at the end → Finalize — instead of forcing
nurses to rediscover every problem at the end of a long assessment. This
also keeps the assessment and plan-of-care relationship consistent with
California hospice requirements that the comprehensive assessment drives an
individualized plan of care.

---

## Admission Action Center (NOT an RNICA section — global)

Available from every screen. Not gated behind, or sequenced within, any
numbered section above.

**Contains:** Medication Requests, Physician Orders, DME Orders, Supply
Orders, Oxygen Orders, Lab Requests, Treatment Orders, Diet Orders,
Referrals, Physician Contact, Office Communication.

---

## Dependency Flow (Documentation Chain)

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
Discipline Assignment
  ↓
Frequency Assignment
  ↓
Master Plan of Care
  ↓
Narrative
  ↓
Finalization
```

Problems are created inside Sections 2-9, at their point of origin — not
after the Narrative. Narrative (Section 10) references the existing Master
Plan of Care; it does not create it. This reflects the per-section POC
model in `SNS_POC_GENERATION_MATRIX_1.0.md` §7 and supersedes the earlier
draft's HOPE→Narrative→Problem Generation ordering.

## Parallel Workflow (Never Blocking)

```
Assessment
  ↓
Need Identified
  ↓
Admission Action Center
  ↓
Medication / DME / Supplies / Referrals / Physician Contact
```

This parallel path never waits on the documentation chain above completing
(per `SNS_DESIGN_SYSTEM_1.0.md` §2.1 Patient Comfort Before Documentation
Completion).

---

## Status / Next Steps

**SNS RNICA Master Map 1.0 — STATUS: APPROVED FOR GOVERNANCE REVIEW.
Architecture Complete. No Further Architecture Work Required.** This map,
together with `SNS_DESIGN_SYSTEM_1.0.md` and
`SNS_POC_GENERATION_MATRIX_1.0.md`, forms the authoritative RNICA
architecture, POC architecture, and synchronization model for RNICA Pilot
Build 1.0 — see the **Governance Freeze** at the top of this document for
what is now locked pending a Version 1.1 revision cycle. It aligns with
the California hospice assessment-to-plan-of-care framework and CMS LCD
expectations for documenting decline, functional status, symptoms, disease
progression, and patient-specific evidence supporting terminal prognosis,
while ensuring the plan remains traceable back to documented clinical
evidence (§ POC Evidence Requirement above).

**Next Deliverable:** `SNS_RNICA_SECTION_INVENTORY_1.0`. Required
deliverables:

1. Field Inventory
2. Database Mapping
3. API Mapping
4. Validation Inventory
5. Narrative Source Inventory
6. HOPE Crosswalk
7. Audit Crosswalk
8. Action Center Trigger Inventory
9. POC Evidence Mapping
10. Migration Complexity Ratings

**Build Order (post-inventory):**

```
Phase 1 — Field Inventory
  ↓
Phase 2 — POC Generation Engine
  ↓
Phase 3 — Master POC Synchronization
  ↓
Phase 4 — RNICA UI Migration
  ↓
Phase 5 — HOPE Integration
  ↓
Phase 6 — Narrative Integration
  ↓
Phase 7 — Pilot Testing
```

No code changes are authorized by this document alone — implementation
requires a separate, explicit go-ahead (consistent with
`SNS_DESIGN_SYSTEM_1.0.md` §12 Governance). **No Code Changes Authorized
Without Separate Approval.**
