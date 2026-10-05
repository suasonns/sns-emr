# SNS Design System 1.0

Status: Governance and build-ready implementation specification
Reference implementation: RNICA Pain & Symptom Burden and Neurological
Assessment (both already implemented and approved)
Master visual reference: RNICA Pain & Symptom Burden + Neurological
Assessment (supersedes the prior Facesheet-derived typography baseline —
see §12 Governance / Revision History)
Scope: All SNS clinical documentation modules, and ultimately the whole
chart and every discipline (see §12)

This document defines the standard. It does not itself change any code
beyond the shared, additive typography tokens described in §3.2-§3.4,
which are the literal values already shipped in
`sns-emr-frontend/src/theme/sns-typography.css` (loaded globally from
`main.tsx`) and already consumed by the Comorbidities and Neurological/Body
Systems group headings.
**Sequencing (explicit):** Pain & Symptom Burden and Neurological Assessment
are the approved reference implementations — not a future pilot. Every other
RNICA section, and in time the rest of the chart and other disciplines
(Patient Story, RN/LVN visits, MSW, Chaplain, CHHA, Bereavement, Compliance,
HOPE workflows, and the remaining modules listed in §12), must be brought
into conformance with the typography/token values in §3, not the legacy
Facesheet-derived values this document previously specified. Do not redesign
all modules simultaneously — convert incrementally, section by section.

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
- **Biller's Dashboard / External Billing Services portal** (billing-department-facing,
  cross-agency views — see `docs/design/biller-dashboard-figma/README.md` for its page-specific
  layout/content reference; this document's tokens govern its visual implementation)

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

**[SUPERSEDED 2026-10 — see §12 Revision History]** The typography tokens in
§3.2-§3.4 below previously derived from the legacy Facesheet implementation
(`sns-emr-frontend/src/charts/PatientFacesheet.jsx`). Per explicit owner
direction, that baseline is superseded: **RNICA Pain & Symptom Burden and
Neurological Assessment are now the approved reference implementations**,
and the values below are the literal tokens already shipped in
`sns-emr-frontend/src/theme/sns-typography.css` (loaded globally from
`main.tsx`, so they are available on every route, not only RNICA). Color
tokens (§3.5), card dimensions (§3.6), and the rest of this section are
unaffected by this change. **Do not create duplicate tokens when an
equivalent token already exists.**

### 3.1 Font Family

Use the current application font family everywhere:

```css
--sns-font-family: inherit;
```

No module should introduce a new one.

### 3.2 Typography Tokens (CSS custom properties — "RNICA-H1" etc.)

These are the canonical, literal typography tokens for the entire system,
derived from the approved RNICA Pain & Symptom Burden / Neurological
Assessment implementations. Every module must reference one of these five
values — no ad hoc font sizes or weights.

```css
--rnica-h1-size: 16px;  --rnica-h1-weight: 500;
--rnica-h2-size: 14px;  --rnica-h2-weight: 500;
--rnica-h3-size: 12px;  --rnica-h3-weight: 500;
--rnica-body-size: 13px;  --rnica-body-weight: 400;
--rnica-helper-size: 11px;  --rnica-helper-weight: 400;
```

Utility classes `.rnica-h1`, `.rnica-h2`, `.rnica-h3`, `.rnica-body-text`,
`.rnica-helper-text` wrap these pairs (`.rnica-helper-text` also sets
`color: var(--sns-muted)`).

| Token | Usage |
|---|---|
| RNICA-H1 (16px / 500) | Top-level card/section title — patient/page title, "Pain Overview", "Neurological Overview" |
| RNICA-H2 (14px / 500) | Card title / sub-screen heading — "Pain Intensity", "Secondary Diagnoses & Comorbidities" |
| RNICA-H3 (12px / 500) | Group/category label inside a card — comorbidity category headings, body-system subsection headings; typically uppercase + letter-spacing, applied by the consuming selector |
| RNICA-Body (13px / 400) | Standard reading copy/value text inside a card, input values |
| RNICA-Helper (11px / 400, muted) | Secondary/helper/meta text, field labels, timestamps, counts, tooltip-replacement copy |

### 3.3 Font Weight Policy

Only two weights appear in the standard typography scale: `500` (medium —
RNICA-H1/H2/H3) and `400` (regular — RNICA-Body/Helper). **`700` (bold) is
never part of the baseline scale** — it is reserved exclusively for the
Alert Hierarchy (§6, per the Bold Text Policy §4) and status badges (§3.9).
A heading is never bolded merely for emphasis; if something needs to stand
out beyond RNICA-H1/H2/H3's medium weight, it must qualify under the Alert
Hierarchy (§6), not receive ad hoc bold.

### 3.4 Typography Hierarchy

One sizing hierarchy. Minimal variation. Maps the five RNICA-H1...Helper
tokens from §3.2 onto on-screen purpose.

| Level | Purpose | Token | Weight |
|---|---|---|---|
| 1 | Patient Name (or record/entity name for non-chart modules) / page title | RNICA-H1 (16px) | 500 (medium) |
| 2 | Section/Card Header | RNICA-H2 (14px) | 500 (medium) |
| 3 | Group/Category Label (uppercase, letter-spacing) | RNICA-H3 (12px) | 500 (medium) |
| 4 | Field Content / Body / Input Values | RNICA-Body (13px) | 400 (regular) (bold only if alert, see §6) |
| 5 | Helper / Meta / Field Label text | RNICA-Helper (11px, muted) | 400 (regular), uppercase where used as a field label |

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
| `white` (primary text) | `#ffffff` | `#18354c` | Level 1/2/4 primary text (RNICA-H1/H2/Body) |
| `label` | `#94a3b8` | `#5f7286` | Level 3/5 group labels and helper/field-label text (RNICA-H3/Helper) — same color as `--sns-muted` |
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
- `fontSize: 13` (RNICA-Body), `lineHeight: 1.25`
- `padding: '5px 7px'`

### 3.8 Label Style

`fontSize: 11` (RNICA-Helper), `textTransform: 'uppercase'`,
`letterSpacing: 0.5`, `display: 'block'`, color = `colors.label`, weight =
400 (regular — never bold — see §4).

### 3.9 Status Badge Style

Small pill (e.g. admission status): `padding: '2px 8px'`, `borderRadius: 4`,
`fontSize: 11` (RNICA-Helper), `fontWeight: 700` (bold — intentional
exception), background/color from the green/red/amber tokens + their `*Bg`
tint pair above (bold IS allowed here because a status badge is itself a
compact alert/status indicator, not routine label text — this is the same
exception carved out in §3.3/§4, not a reintroduction of ad hoc bold).

### 3.10 Banner/Header Style

Top-of-page identity card: container `borderRadius: 8`, `padding: '12px
16px'`, `boxShadow: '0 1px 2px rgba(15,23,42,0.04)'`; name `fontSize: 16`
(RNICA-H1), `fontWeight: 500`; supporting line `fontSize: 12`,
`lineHeight: 1.4`, `color: colors.label`; key-fact label `fontSize: 11`
(RNICA-Helper), uppercase, `letterSpacing: 0.5`; key-fact value `fontSize:
13` (RNICA-Body), `fontWeight: 700` ONLY when `alert` is true (Alert
Hierarchy, §6), otherwise `fontWeight` is 400 (regular).

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
- **RNICA Pain & Symptom Burden and Neurological Assessment are the approved,
  already-implemented reference implementations** (superseding the prior
  "RNICA is the pilot, not yet started" sequencing). The typography tokens in
  §3.2-§3.4 are already live app-wide via
  `sns-emr-frontend/src/theme/sns-typography.css`, and already consumed by
  the Comorbidities and Neurological/Body Systems group headings. This
  document now extends to the remaining modules in this priority order:
  remaining RNICA sections (Functional Status, Safety, Caregiver Support,
  ACP, Orders, Compliance, Finalization), Patient Story, future chart
  workspaces, RN/LVN visits, MSW Assessment, Chaplain/Spiritual Assessment,
  CHHA, Bereavement Assessment, Compliance & HOPE workflows, Volunteer
  documentation, Visit Notes, Orders, Plan of Care, Referrals, Care Plans,
  CTI, F2F, IDG, QAPI, HR (clinical-assessment-adjacent modules first,
  operational modules last).
- No code changes are authorized by this document alone beyond the shared
  typography tokens already shipped (§3.2-§3.4) — per-module conversion of
  layout/cards/workflow still requires a separate, explicit go-ahead.
- Non-Negotiable Clinical Principles (§2) and Identity of Data (§2.3) govern
  every future module conversion — a module cannot be "converted" to this
  design system if doing so would duplicate an authoritative data source or
  weaken existing compliance behavior (§2.5).

### Revision History

- **2026-10 — Typography baseline superseded.** §3.1-§3.4 and the dependent
  references in §3.7-§3.10 were rewritten: the font-size/weight tokens no
  longer derive from the legacy Facesheet implementation
  (`PatientFacesheet.jsx`). They now derive from the approved RNICA Pain &
  Symptom Burden and Neurological Assessment implementations, per explicit
  owner direction ("Do not maintain separate typography systems for RNICA,
  Chart, Facesheet, Disciplines. Approved RNICA sections become the source
  of truth."). Color tokens (§3.5), card dimensions (§3.6), the Bold Text
  Policy (§4), Color Policy (§5), and Alert Hierarchy (§6) are unchanged.

