# SNS Hospice EMR — ICA + Bereavement + Skin + Safety/Fall + Pain
Implementation Map / Schema / Plan / Checklists

Version: 1.3 (Compliance‑First, CA Hospice)
Owner: SNS Hospice EMR

Scope:
- RN / MSW / SC Initial Comprehensive Assessment (ICA)
- Bereavement (RN baseline → MSW/SC reference)
- Skin / Integumentary (RN ROS)
- Safety & Fall Risk (Facility vs Home toggle)
- Pain Assessment (ALL disciplines)
- First IDG discrepancy reconciliation

---

## 0) Compliance Anchors

- RN Initial Assessment: ≤ 48 hours from hospice election / SOC
- Comprehensive Assessment (RN + MSW + SC): ≤ 5 calendar days from SOC
- Comprehensive Assessment must include:
  - Physical
  - Psychosocial
  - Emotional
  - Spiritual
  - Bereavement
- Hospice must provide counseling services, including bereavement counseling
- Hospice care includes support for caregiver and family (CA / CDPH expectation)

---

## 1) Canonical Business Rules

### 1.1 SOC Definition (California Practice)
- SOC_DATE is typically the RN admission / RN initial assessment date.
- If election/referral order exists earlier:
  - SOC_DATE = earliest of:
    - election/referral order timestamp
    - RN initial assessment timestamp

### 1.2 ICA Timing Windows (from SOC_DATE)
- RN ICA due ≤ SOC_DATE + 48 hours
- MSW ICA due ≤ SOC_DATE + 5 calendar days
- SC ICA due ≤ SOC_DATE + 5 calendar days

---

## 2) Bereavement Discipline Model (Authoritative)

- RN documents bereavement baseline at SOC (always part of RN ICA).
- MSW and/or SC may complete the bereavement assessment.
- MSW/SC must see RN bereavement baseline inside their view (no navigation).
- MSW/SC must explicitly acknowledge RN baseline review.
- RN does not duplicate bereavement if MSW/SC completes it.
- Any discrepancy RN vs MSW/SC must be flagged and resolved at the first IDG.
- If BOTH MSW and SC decline/unavailable → RN completes bereavement (fallback).

---

## 3) Evidence Model (Audit‑Proof)

A task or assessment is valid only if it includes:
- completed_at timestamp
- completion_reference_type
- completion_reference_id
- signer metadata (who / when)

---

## 4) Data Model (Schema Plan)

### 4.1 Reused Tables
- patients
- visits
- clinical_notes / document_records
- tasks
- idg_meetings / idg_notes / idg_signatures

---

### 4.2 New / Extended Structures

#### A) assessments
Fields:
- id (uuid, PK)
- patient_id (FK)
- discipline (RN | MSW | SC | MD | NP | LVN | CHHA)
- assessment_type:
  - RN_ICA
  - MSW_ICA
  - SC_ICA
  - RN_BEREAVEMENT_BASELINE
  - BEREAVEMENT_ASSESSMENT
- occurred_at
- signed_at
- signed_by
- status (DRAFT | SIGNED | VOIDED)
- risk_score (bereavement)
- risk_level (LOW | MODERATE | HIGH)
- data_json (jsonb)
- document_id (FK, nullable)
- visit_id (FK, nullable)
- created_at
- updated_at

Constraints:
- signed_at required when status = SIGNED
- RN_BEREAVEMENT_BASELINE discipline must be RN

---

#### B) assessment_references
Fields:
- id
- assessment_id (MSW/SC record)
- referenced_assessment_id (RN baseline)
- reference_kind (RN_BASELINE)
- reviewed_ack (boolean REQUIRED)
- reviewed_at
- created_at

Constraint:
- MSW/SC bereavement requires exactly one RN baseline reference.

---

#### C) assessment_discrepancies
Fields:
- id
- patient_id
- domain (BEREAVEMENT | SKIN | SAFETY | FALLS | PAIN | PSYCHOSOCIAL | SPIRITUAL | OTHER)
- baseline_assessment_id (RN)
- comparing_assessment_id (MSW/SC or other)
- discrepancy_summary
- requires_idg_reconciliation (default true)
- resolved (default false)
- resolved_at
- resolved_in_idg_meeting_id
- resolution_note
- created_at

Constraint:
- Unresolved discrepancies block first IDG finalization.

---

## 5) Task Engine Rules

### 5.1 Required Task Types
- INITIAL_RN_ICA
- INITIAL_MSW_ICA
- INITIAL_SC_ICA
- INITIAL_BEREAVEMENT

NOTE: Task type strings must be normalized and match DB enums exactly.

### 5.2 Task Creation (at SOC)
- RN ICA → due SOC + 48h
- MSW ICA → due SOC + 5d
- SC ICA → due SOC + 5d
- Bereavement → due SOC + 5d

### 5.3 Task Completion Rules
- RN ICA → requires RN ICA evidence
- MSW ICA → requires MSW evidence + RN baseline reference
- SC ICA → requires SC evidence + RN baseline reference
- Bereavement → requires RN baseline + MSW/SC OR RN fallback

---

## 6) UI / UX Enforcement (Non‑Negotiable)

### RN Baseline Injection
MSW and SC views MUST display a read‑only RN Baseline Panel:
- RN assessment date (SOC)
- RN bereavement baseline summary
- RN skin baseline summary
- RN safety / fall baseline summary
- RN signer + timestamp

### Required Controls (MSW / SC)
- ☐ RN baseline reviewed (REQUIRED)
- ☐ Aligns with RN baseline
- ☐ Differs from RN baseline → explanation REQUIRED → discrepancy record created

---

## 7) RN ICA — CORE REVIEW OF SYSTEMS (ROS)

### 7.1 Integumentary / Skin Integrity (MANDATORY)

#### Skin Assessment Status
- [ ] Skin assessment performed
- [ ] Skin intact
- [ ] Skin impaired

#### Risk Factors
- [ ] Poor nutrition
- [ ] Incontinence
- [ ] Immobility / weakness
- [ ] Advanced age
- [ ] Altered sensation
- [ ] Edema
- [ ] Other: __________

#### Wound Presence
- [ ] No wounds present
- [ ] Wounds present → Skin Impairment Assessment REQUIRED

---

### 7.2 Skin Impairment / Wound Assessment (RN — if applicable)

- [ ] Assessment completed
- [ ] Assessment date
- [ ] Anatomical location(s)
- [ ] Pressure injury stage:
  - [ ] I
  - [ ] II
  - [ ] III
  - [ ] IV
  - [ ] Unstageable
  - [ ] Suspected Deep Tissue Injury
- [ ] Size (L × W × D)
- [ ] Color
- [ ] Drainage
- [ ] Odor
- [ ] Inflammation
- [ ] Undermining / tunneling
- [ ] Status (e.g., Change of Condition)
- [ ] Treatment documented
- [ ] Monitoring plan

---

### 7.3 Skin Narrative & Education (RN)

- [ ] RN narrative addresses skin integrity
- [ ] Education provided:
  - [ ] Repositioning (q2h)
  - [ ] Pressure offloading
  - [ ] Skin monitoring
  - [ ] When to report changes
- [ ] Patient / PCG verbalized understanding

---

## 8) Safety & Fall Risk Assessment (RN — REQUIRED)

### Care Setting Toggle (REQUIRED)
- [ ] Facility‑Managed (SNF / ALF / Hospital / Board & Care)
- [ ] Home / Family‑Managed

### Fall Risk (Always Required)
- [ ] Fall risk assessment completed
- [ ] Fall risk level documented (Low / Moderate / High)
- [ ] History of falls reviewed
- [ ] Mobility limitations documented
- [ ] Assistive devices reviewed

### Facility‑Managed Path (ONLY if Facility selected)
- [ ] Facility safety protocols reviewed
- [ ] Call light availability confirmed
- [ ] Bed / chair alarms reviewed (if applicable)
- [ ] Facility responsible for prevention measures
- [ ] Facility staff notified if indicated

### Home / Family‑Managed Path (ONLY if Home selected)
- [ ] Home hazards assessed (rugs, cords, clutter, lighting)
- [ ] Bathroom safety reviewed
- [ ] Bed / chair safety reviewed
- [ ] Oxygen safety reviewed (if applicable)
- [ ] Emergency preparedness reviewed
- [ ] Education limited to caregiver scope
- [ ] Patient / PCG verbalized understanding

Enforcement:
- Toggle is REQUIRED
- Paths are mutually exclusive
- RN ICA cannot be signed without fall risk level and correct path

---

## 9) Bereavement Checklist

### RN Baseline (SOC)
- [ ] Bereavement awareness documented
- [ ] Baseline visible to MSW/SC

### MSW / SC Assessment
- [ ] RN baseline reviewed
- [ ] Aligns with RN baseline OR discrepancy flagged

### RN Fallback
- [ ] MSW declined
- [ ] SC declined
- [ ] RN completed bereavement assessment

---

## 10) Pain Assessment — ALL DISCIPLINES (NON‑NEGOTIABLE)

Applies to:
- MD
- NP
- RN
- LVN
- MSW
- SC
- CHHA

### Tool Selection Rule (AUTHORITATIVE)
- Patient alert / able to self‑report → Numeric scale REQUIRED
- Patient not alert / unable to self‑report → FLACC or PAINAD REQUIRED

### Minimum Documentation (Per Visit / Note)
- [ ] Pain assessed
- [ ] Patient alert status documented
- [ ] Tool matches alert status
- [ ] Pain present Yes / No

If pain present:
- [ ] Severity documented
- [ ] Intervention or escalation documented

If pain absent:
- [ ] “No pain” explicitly documented

Enforcement:
- Pain fields REQUIRED to sign visit/note
- Tool selection validated against alertness
- Uncontrolled pain triggers escalation / POC update

---

## 11) First IDG — Discrepancy Resolution Gate

- [ ] RN findings reviewed
- [ ] MSW findings reviewed
- [ ] SC findings reviewed
- [ ] Bereavement discrepancies resolved
- [ ] Skin discrepancies resolved
- [ ] Safety / fall discrepancies resolved
- [ ] Pain discrepancies resolved
- [ ] Resolution documented
- [ ] Plan of Care updated OR rationale documented

❌ IDG cannot finalize with unresolved discrepancies.

---

## 12) QA “Nothing Missed” Checklist

RN:
- [ ] RN ICA signed ≤ 48h
- [ ] Pain assessed with correct tool
- [ ] ROS integumentary completed
- [ ] Wound assessment if applicable
- [ ] Safety/fall toggle + correct path
- [ ] Education documented

MSW:
- [ ] MSW ICA signed ≤ 5d
- [ ] RN baseline visible & reviewed
- [ ] Pain assessed
- [ ] IDG resolution if discrepancy

SC:
- [ ] SC ICA signed ≤ 5d
- [ ] RN baseline visible & reviewed
- [ ] Pain assessed
- [ ] IDG resolution if discrepancy

Bereavement:
- [ ] Assessment completed
- [ ] RN baseline referenced
- [ ] Discrepancies resolved at IDG

END