# SNS Design System 1.0

Status: Governance and build-ready implementation specification
Initial pilot: RNICA
Master visual reference: Existing SNS Facesheet
Scope: All SNS clinical documentation modules

This document defines the standard. It does not itself change any code.
**Sequencing (explicit):** this document establishes the SNS design language
first. RNICA is the pilot — it is the FIRST module actually converted to this
standard, and only after this document is reviewed/approved. No RNICA code
changes happen until a separate, explicit go-ahead is given. Once RNICA is
validated, every other module listed below must be built/converted to match
the RNICA implementation (not re-derive its own interpretation of Facesheet).
Do not redesign all modules simultaneously.

---

## 1. Purpose

SNS Design System 1.0 establishes a single visual, interaction,
clinical-workflow, and documentation standard for:

- RN ICA
- RNICA
- RN visits
- LVN visits
- Social Worker assessments and visits
- Spiritual Care assessments and visits
- Bereavement assessments and contacts
- HHA assessments, care plans, and visits
- Volunteer documentation
- CTI
- Face-to-Face
- Orders
- Plan of Care
- IDG
- Referrals
- QAPI
- HR and personnel compliance

The existing Facesheet (`sns-emr-frontend/src/charts/PatientFacesheet.jsx`)
is the visual reference implementation. RNICA will be the first pilot
conversion. Do not redesign all modules simultaneously.

The test for any screen, new or existing: **"This is SNS."** If a module
doesn't pass that test, it must be redesigned to match this document before
being considered "done."

---

## 2. Non-Negotiable Clinical Principles

### 2.1 Patient Comfort Before Documentation Completion

SNS must never require completion of an assessment, narrative, plan of care,
or finalization before the clinician can initiate an urgent patient-care
action.

Medication, oxygen, DME, supplies, physician communication, and urgent
referrals are parallel clinical workflows. They are not final assessment
steps. See §9 (Admission Action Center Standard).

### 2.2 Assessment Before Narrative

The clinical narrative is the synthesis of the completed assessment. The
nurse should first document:

- Immediate symptoms
- Disease history and trajectory
- Utilization history
- Functional condition
- Head-to-toe findings
- Disease-specific findings
- HOPE data
- Psychosocial findings
- Spiritual findings
- Caregiver and bereavement findings
- Safety risks
- Performance status

The narrative is generated and reviewed near the end, immediately before care
planning and finalization. See §8 (Clinical Narrative Standard).

### 2.3 Identity of Data

Do not duplicate patient data when an authoritative source already exists.

Examples:

- Facesheet demographics remain authoritative for demographics.
- Active diagnoses remain authoritative for diagnosis displays.
- Structured allergies remain authoritative across the chart.
- Physician directory and assignment records remain authoritative for
  provider identity.
- Orders Hub remains authoritative for orders.
- Current Plan of Care remains authoritative for active problems, goals,
  interventions, disciplines, and frequencies.

RNICA (and every other module) may display authoritative information but
must not silently create a competing version. Where RNICA currently
overlays shared/authoritative values at read time (e.g. code status,
caregiver/DPOA contacts — see `_overlay_shared_code_status` in
`backend/app/api/visits.py`), that pattern is the model to preserve and
extend, not replace with a new locally-owned copy.

### 2.4 Structured Evidence Plus Clinical Judgment

SNS should collect structured evidence while preserving a clearly identified
clinician comment or addendum field where clinical judgment is needed. Every
system assessment may contain:

1. Structured findings
2. Optional system-specific clinical comment
3. Generated summary preview
4. Identified change from prior assessment, when available

### 2.5 Preserve Existing Compliance Behavior

The RNICA redesign is initially a presentation and workflow reorganization.
Do not remove, weaken, rename, or reinterpret existing:

- Required fields
- HOPE fields
- Validation rules
- Signatures
- Authentication requirements
- Audit events
- Patient assignment rules
- Provider identity controls
- Orders
- Plan-of-care records
- Historical assessment records

Any behavioral change requires a separate governance decision.

---

## 3. Design Tokens

The following tokens are derived from the existing Facesheet design
language (`sns-emr-frontend/src/charts/PatientFacesheet.jsx`). Before
implementation, inspect the live Facesheet styles and reuse existing
variables or components where available. **Do not create duplicate tokens
when an equivalent token already exists.**

### 3.1 Font Family

Use the current Facesheet application font family everywhere:

```css
--sns-font-family: inherit;
```

Facesheet never sets a custom `fontFamily` beyond `inherit` — no module
should introduce a new one.

### 3.2 Font Size Tokens (CSS custom properties)

These are the canonical, literal font-size tokens for the entire system.
Every module must reference one of these seven values — no ad hoc font sizes.

```css
--sns-font-utility: 8.5px;
--sns-font-label: 9px;
--sns-font-caption: 10px;
--sns-font-body: 11.5px;
--sns-font-card-title: 13px;
--sns-font-section-title: 14px;
--sns-font-page-title: 18px;
```

| Token | Usage |
|---|---|
| `--sns-font-utility` | Timestamps, codes, compact audit metadata |
| `--sns-font-label` | Uppercase field labels, card metadata labels |
| `--sns-font-caption` | Supporting instructions, source labels, helper text |
| `--sns-font-body` | Input values, paragraph text, clinical content |
| `--sns-font-card-title` | Card and subsection headings |
| `--sns-font-section-title` | Major workspace section headings |
| `--sns-font-page-title` | Patient or document title only |

### 3.3 Font Weight Tokens

```css
--sns-weight-regular: 400;
--sns-weight-medium: 500;
--sns-weight-semibold: 600;
--sns-weight-bold: 700;
```

`--sns-weight-bold` is reserved for the exact Alert Hierarchy in §6 (per the
Bold Text Policy, §4) plus `--sns-font-page-title` / `--sns-font-section-title`
headings and status badges (§3.9). `--sns-weight-medium` /
`--sns-weight-semibold` may be used sparingly for card titles
(`--sns-font-card-title`) where a heavier-than-body weight helps scanability
without competing with an actual alert. Routine field labels and content use
`--sns-weight-regular` only.

### 3.4 Typography Hierarchy

One sizing hierarchy. Minimal variation. Maps the four Level 1-4 zones from
§3.2's Purpose column onto the token set above.

| Level | Purpose | Token | Weight |
|---|---|---|---|
| 1 | Patient Name (or record/entity name for non-chart modules) | `--sns-font-page-title` (18px) | `--sns-weight-bold` |
| 2 | Section Header | `--sns-font-section-title` (14px) | `--sns-weight-bold` |
| 3 | Field Label | `--sns-font-label` (9px) / `--sns-font-utility` (8.5px) | `--sns-weight-regular`, uppercase, letter-spacing 0.5 |
| 4 | Field Content | `--sns-font-body` (11.5px) / `--sns-font-card-title` (13px) | `--sns-weight-regular` (bold only if alert, see §6) |

No other font sizes are introduced without updating this table. For
non-patient-chart modules (Orders, Care Plans, IDG, QAPI, HR) Level 1 becomes
the record/entity name (e.g. Order #, Care Plan title, IDG meeting date, QAPI
indicator, employee name) in place of "Patient Name" — the hierarchy and
sizes stay the same.

### 3.5 Color Tokens (`getColors(mode)` in PatientFacesheet.jsx)

| Token | Dark mode | Light mode | Meaning |
|---|---|---|---|
| `bg` | `#0f172a` | `#f3f8f7` | Page background |
| `card` | `#1e293b` | `#ffffff` | Card background |
| `border` | `#334155` | `#d9e6eb` | Card/input border |
| `teal` | `#10b7a2` | `#0d7d7a` | Primary accent (card left-border, active state) |
| `white` (primary text) | `#ffffff` | `#18354c` | Level 1/2/4 primary text |
| `label` | `#94a3b8` | `#5f7286` | Level 3 field labels |
| `text` | `#e2e8f0` | `#1e2d3b` | Secondary body text |
| `green` | `#059669` | `#2d7b63` | Status: Complete |
| `red` | `#ef4444` | `#d64d57` | Status: Clinical Risk / Alert |
| `amber` | `#f59e0b` | `#d38a2b` | Status: Needs Attention |
| `greenBg` | `#05966915` | `#dff5ee` | Complete tint background |
| `redBg` | `#ef444415` | `#fbe3e7` | Risk tint background |
| `amberBg` | `#f59e0b15` | `#f9edd7` | Attention tint background |
| `tealBg` | `#10b7a215` | `#dff8f4` | Info/accent tint background |

### 3.6 Card Dimensions (`cardBase(colors)`)

- `borderRadius: 8`
- `padding: 10` (list/grid cards) — larger container cards use `'8px 10px'` up
  to `'12px 16px'` depending on density (banner card = `'12px 16px'`)
- `borderLeft: '3px solid ' + colors.teal` (primary accent edge)
- `minHeight: 84`
- `boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)'`
- `boxSizing: 'border-box'`, `display: 'flex'`, `flexDirection: 'column'`

### 3.7 Input/Field Dimensions (`baseInputStyle(colors)`)

- `borderRadius: 5`
- `border: '1px solid ' + colors.border`
- `fontSize: 11.5` (`--sns-font-body`), `lineHeight: 1.25`
- `padding: '5px 7px'`

### 3.8 Label Style

`fontSize: 8.5` (`--sns-font-utility`), `textTransform: 'uppercase'`,
`letterSpacing: 0.5`, `display: 'block'`, color = `colors.label`, weight =
`--sns-weight-regular` (never bold — see §4).

### 3.9 Status Badge Style

Small pill (e.g. admission status): `padding: '2px 8px'`, `borderRadius: 4`,
`fontSize: 10` (`--sns-font-caption`), `fontWeight: 700`
(`--sns-weight-bold`), background/color from the green/red/amber tokens +
their `*Bg` tint pair above (bold IS allowed here because a status badge is
itself a compact alert/status indicator, not routine label text).

### 3.10 Banner/Header Style

Top-of-page identity card: container `borderRadius: 8`, `padding: '12px
16px'`, `boxShadow: '0 1px 2px rgba(15,23,42,0.04)'`; name `fontSize: 18`
(`--sns-font-page-title`), `fontWeight: 700`; supporting line `fontSize: 12`,
`lineHeight: 1.4`, `color: colors.label`; key-fact label `fontSize: 9`
(`--sns-font-label`), uppercase, `letterSpacing: 0.5`; key-fact value
`fontSize: 13` (`--sns-font-card-title`), `fontWeight: 700` ONLY when `alert`
is true, otherwise `fontWeight` is `--sns-weight-regular`.

---

## 4. Bold Text Policy

Bold is a scarce resource. If everything is bold, nothing stands out.

**Bold is reserved for the exact Alert Hierarchy in §6 — no other field is
ever bold.**

**Normal weight (never bold):** Address, County, ZIP, Phone, Language,
Religion, Race, Marital Status, and all other routine demographic/field
labels — this applies equally to non-clinical modules (e.g. HR employee
fields, QAPI indicator metadata) unless the field is itself a flagged risk
item in §6.

---

## 5. Color Policy

Color communicates urgency only — never decoration.

| Color | Meaning | Facesheet reference |
|---|---|---|
| Green | Complete | status/complete indicators |
| Yellow / Amber | Needs Attention | `colors.amber` warning hints |
| Red | Clinical Risk | `colors.red` alert values |
| Blue | Information | neutral informational banners |

No other color meanings are permitted anywhere in the system, including
QAPI (e.g. red = out-of-threshold indicator, not decoration) and HR (e.g.
red = expired credential/compliance item). Color + bold together are
reserved exclusively for the Alert Hierarchy in §6.

---

## 6. Alert Hierarchy

Only the following are permitted to visually dominate a screen (bold + the
Color Policy's red/amber tokens, rendered as a distinct alert card per §6).
**No other item may use this treatment — this is the complete, exclusive
list:**

1. Pain
2. Dyspnea
3. Oxygen
4. Allergies
5. DNR
6. Fall Risk
7. Pressure Injury
8. Imminent Death
9. Uncontrolled Symptoms
10. Missing Required Compliance Items

Example renderings: "PAIN 8/10", "DYSPNEA — UNCONTROLLED", "OXYGEN
DEPENDENT", "ALLERGY: PENICILLIN", "DNR", "HIGH FALL RISK", "STAGE III
PRESSURE INJURY", "IMMINENT DEATH TRIGGERS PRESENT", "UNCONTROLLED NAUSEA",
"MISSING REQUIRED SIGNATURE". Everything else in the system — including
Terminal Diagnosis, demographics, routine assessment findings — renders at
normal weight per §3/§4, even when clinically significant, unless it appears
in this exact list.

---

## 7. Facesheet Card Standard

Every card, in every module, shall contain:
- Header
- Key summary
- Expandable details
- Minimal decoration
- Consistent spacing and padding: `borderRadius: 8`, `padding: '10px 12px'`
  to `'12px 16px'`, `boxShadow: '0 1px 2px rgba(15,23,42,0.04)'` (Facesheet
  card tokens per §3 — reuse these values verbatim, do not reinvent
  per-module shadows/radii)
- Consistent typography per §3.4

---

## 8. Clinical Narrative Standard

Narrative is a **synthesis**, not an intake step. It occurs **near
Finalization**, generated *after* Assessment, Performance Status, Disease
Findings, HOPE, Symptoms, and Functional Assessment are captured — never at
the start of the workflow. The nurse should not have to scroll back and forth
to keep narrative in sync with earlier findings; narrative is composed once
the inputs it summarizes already exist. (See also §2.2.)

---

## 9. Admission Action Center Standard (Clinical Workflow Standard)

**Orders, DME, Supplies, and Referrals must never depend on assessment
completion.** This is a hard workflow rule, not a UI preference:

- Orders must never depend on assessment completion.
- DME must never depend on assessment completion.
- Supplies must never depend on assessment completion.
- Referrals must never depend on assessment completion.
- The Admission Action Center must be available from every assessment
  screen — not gated behind, or sequenced before/after, any documentation
  step.

Orders, DME, Supplies, Medications, and Referrals are **not** sequential
assessment steps gated behind assessment completion. They become a single
persistent, always-available **Admission Action Center**, reachable from
every RN ICA screen throughout the assessment — never blocking comfort
measures behind documentation completion.

**Sections:**
- **Immediate Clinical Needs** (checklist): Pain Medication Needed, Oxygen
  Needed, Nebulizer Needed, Comfort Kit Needed, Foley Supplies Needed, Wound
  Supplies Needed, Incontinence Supplies Needed, DME Needed, Pharmacy Contact
  Needed, Physician Contact Needed
- **DME Requests**: Hospital Bed, Low Air Loss Mattress, Wheelchair, Commode,
  Walker, Oxygen Concentrator
- **Supply Requests**: Wound Supplies, Briefs, Chux, Gloves, Dressings
- **Medication Requests**: STAT Comfort Medication, Pain Medication, Dyspnea
  Medication, Anxiety Medication
- **Referrals**: Social Worker, Chaplain, Volunteer, Dietitian, Pharmacist

**Offline requirement:** the RN must be able to create, document, and queue
these requests without connectivity; on reconnect, requests, assessment data,
and the audit trail all synchronize. Hospice care delivery must never depend
on cell service.

---

## 10. Clinical Documentation Standard

Every assessment must be visually and structurally divided into two distinct
modes, so the nurse spends more time reviewing the clinical picture and less
time searching through forms:

**1. Information Display** (read-oriented, reviewed first):
- Patient Snapshot
- Diagnosis Summary
- Current Scores (e.g. PPS/KPS, Braden, Fall Risk, pain score)
- Historical Trend
- Previous Assessment Comparison

**2. Data Collection** (write-oriented, entered second):
- Nurse Documentation
- Assessment Findings
- Clinical Inputs

Information Display renders using the Facesheet Card Standard (§7) —
read-only summaries, trends, and comparisons the nurse can scan quickly.
Data Collection is where active charting happens. These two modes are
visually distinguishable (e.g. Information Display cards vs. Data Collection
form sections) so the nurse always knows whether they're reviewing the
existing clinical picture or actively entering new findings.

---

## 11. RNICA Pilot Implementation Plan (for when implementation begins)

### 11.1 Target section layout (Facesheet-style cards, replacing long scroll)

Information Display first (§10): Patient Snapshot → Current Concerns
(Alert Hierarchy, §6) → Diagnosis Summary → Current Scores → Historical
Trend/Previous Assessment Comparison. Then Data Collection (§10): Pain →
Functional Status → Disease Status → Clinical Findings → Caregiver
Assessment → Safety → Orders (Admission Action Center, persistent throughout,
§9) → Narrative (§8) → Plan of Care → Finalization.

### 11.2 Mapping from RNICA's current 28 sections (`SIDEBAR_CONFIG` in
`RNICA.jsx`) to the new layout

| New card | Existing section key(s) |
|---|---|
| Patient Snapshot | `demographics` |
| Current Concerns (Alert Hierarchy, §6) | derived: pain, safety(fallRisk), skin(pressure injury), safety(oxygen), imminentDeath |
| Pain | `pain` |
| Functional Status | `performanceStatus`, `musculoskeletal` |
| Disease Status | `diagnoses` |
| Clinical Findings | `vitals`, `neurological`, `cardiovascular`, `respiratory`, `infection`, `gastrointestinal`, `nutrition`, `endocrine`, `genitourinary`, `skin`, `symptomImpact`, `sfv` |
| Caregiver Assessment | `caregiverAssessment` |
| Safety | `safety` |
| Orders (Admission Action Center) | `admissionsOrder`, `ordersHub` (becomes persistent, not sequential — see §9) |
| Narrative | new — synthesized after all findings sections above (§8) |
| Plan of Care | `psychosocial`, `spiritual`, `bereavement`, `personalCare`, `teachingNeeds`, `referrals` |
| Finalization | `finalization`, `advancedCarePlanning` |

This mapping is the starting point for the pilot; it may be refined once
implementation begins, but must be recorded here as this document is updated.

### 11.3 Revised assessment sequence (documentation flow, independent of the
Admission Action Center which is always available per §9)

Introduction & Hospice Education → Immediate Symptom Triage → Disease
Understanding → Hospitalization/Decline History → Family Interview → General
Observation → Strength/Functional Assessment → Head-to-Toe Assessment →
Disease-Specific Findings → HOPE & Symptom Burden → Psychosocial → Spiritual
→ Bereavement → Personal Care/HHA → Performance Status → Clinical Narrative &
Disease Trajectory → Problem Generation → Goals → Interventions → Discipline
Recommendations → Visit Frequency Recommendations → Final Review →
Finalization.

---

## 12. Governance

- This document is the source of truth for all future module UI work,
  clinical (RN ICA, RNICA, RN/LVN visits, SW/Spiritual/Bereavement/HHA
  Assessments, Volunteer documentation, Visit Notes, Orders, Care Plans,
  CTI, F2F, IDG, Referrals, Plan of Care) and operational (QAPI, HR) alike.
- Any module claiming compliance with "SNS Design System 1.0" must pass the
  test in §1.
- RNICA is the pilot; once validated there, this document extends to the
  remaining modules in this priority order: RN/LVN visits, SW Assessment,
  Spiritual Assessment, Bereavement Assessment, HHA Assessment, Volunteer
  documentation, Visit Notes, Orders, Plan of Care, Referrals, Care Plans,
  CTI, F2F, IDG, QAPI, HR (clinical-assessment-adjacent modules first,
  operational modules last).
- No code changes are authorized by this document alone — implementation
  work (starting with RNICA) requires a separate, explicit go-ahead.
- Non-Negotiable Clinical Principles (§2) and Identity of Data (§2.3) govern
  every future module conversion — a module cannot be "converted" to this
  design system if doing so would duplicate an authoritative data source or
  weaken existing compliance behavior (§2.5).

