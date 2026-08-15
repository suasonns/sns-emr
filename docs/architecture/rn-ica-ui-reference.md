# RN ICA (Initial Comprehensive Assessment) — UI Reference

Patient: Margaret Sullivan | MRN: 847291 | DOB: 03/14/1941 (84F)
Primary Dx: Lung Cancer (C34.90) | Terminal Dx: NSCLC Stage IV
Attending: Dr. James Chen | Clinician: Sarah Mitchell, RN, BSN

---

## HOPE QES Item Mapping (CMS Required for QIES Export)

| HOPE Code | Item Description | Source Screen | Source Field | 
|-----------|-----------------|---------------|-------------|
| A0215 | Site of Service at Admission | General Assessment | Site of Service |
| A0220 | Admission Date | General Assessment | Admission Date |
| F2000 | CPR Preference | General Assessment | CPR Preference |
| F2100 | Life-Sustaining Treatment | General Assessment | Life Sustaining Treatment |
| F2200 | Hospitalization Preference | General Assessment | Hospitalization Preference |
| F3000 | Spiritual/Existential Concerns | Spiritual Screening | Spiritual Concern |
| I0010 | Principal Diagnosis | Diagnosis Review | Principal Diagnosis |
| J0900 | Pain Screening | Pain Assessment | Pain Present |
| J2030 | Shortness of Breath | Respiratory | SOB Present |
| J2051 | Symptom Impact (A-H) | Symptom Impact | HOPE Symptoms |
| J2052 | SFV Completed | SFV Engine | SFV Completed |
| J2053 | SFV Follow-up Findings | SFV Engine | SFV Followup Findings |
| N0500 | Scheduled Opioid | Medication Review | Scheduled Opioid |
| N0510 | PRN Opioid | Medication Review | PRN Opioid |
| N0520 | Bowel Regimen | Medication Review | Bowel Regimen |

Color coding: HOPE items = GREEN (#059669), SFV items = RED (#DC2626)

## J2051 Symptom Impact Sub-codes

| Code | Symptom | Scale |
|------|---------|-------|
| J2051.A | Pain | 0=Not at all, 1=Slight, 2=Moderate, 3=Severe, 9=N/A |
| J2051.B | Shortness of Breath | Same scale |
| J2051.C | Anxiety | Same scale |
| J2051.D | Nausea | Same scale |
| J2051.E | Vomiting | Same scale |
| J2051.F | Diarrhea | Same scale |
| J2051.G | Constipation | Same scale |
| J2051.H | Agitation | Same scale |

SFV Rule: Must be initiated within 2 calendar days when any symptom is Moderate or Severe.

---

## Assessment Navigation (Left Sidebar)

### Admission Foundation
- Patient Overview
- General Assessment
- Diagnosis Review

### Head-to-Toe Assessment
- Vitals & Measurements
- HEENT
- Respiratory
- Cardiac / Cardiovascular
- Gastrointestinal
- Genitourinary
- Musculoskeletal
- Integumentary / Skin & Wounds
- Endocrine
- Infection / Immunological

### Symptoms
- Pain Assessment
- Symptom Impact (HOPE)
- SFV Triggers
- Imminently Dying

### Functional Status
- ADL Assessment, Mobility, Nutrition

### Medications & Equipment
- Medication Review, DME & Supplies

### Safety & Teaching
- Safety Assessment
- Environmental & Emergency Preparedness
- Personal Care & Support Needs
- Teaching & Education Summary

### Interdisciplinary Screening
- Psychosocial Screening
- Spiritual Screening
- Bereavement Risk Screening

### Finalization
- Care Plan Hub, HOPE QES Dashboard, SFV Evaluation
- Compliance Validation, Finalization (Sign & Lock)

---

## Screen Details

### 1. General Assessment (HOPE: A0215, A0220, F2000, F2100, F2200)
- Site of Service (HOPE A0215)
- Admission Date (HOPE A0220)
- CPR Preference (HOPE F2000)
- Life-Sustaining Treatment Preference (HOPE F2100)
- Hospitalization Preference (HOPE F2200)
- Communication, Decision Making, Advance Care Planning
- Living Situation, Caregiver, Medication Safety, Veteran status

### 2. Diagnosis Review (HOPE: I0010)
Section 1: Primary / Secondary Diagnosis & Comorbidities (*HOPE Items in green)

**Primary Dx** (HOPE I0010 - green tag)
- Read-only from Diagnosis SSOT module
- ICD-10 code displayed
- HOPE Principal Diagnosis mapping shown

**Secondary Dx**
- Dropdown selector
- "+ Add Secondary Dx" button

**Comorbidities and Co-existing Conditions** (CMS HOPE Section I)
Checkbox list - check all that apply:
- Cancer (I0700)
- Heart Failure / CHF / Pulmonary Edema (I0600)
- Peripheral Vascular Disease PVD/PAD (I0900)
- Cardiovascular
- Gastrointestinal
- Liver Disease / Cirrhosis (I5100)
- Renal / Kidney Disease (I1400)
- Diabetes Mellitus (E86.1/E06)
- Neurological
- Seizure Disorder (I4900)
- Dementia including Alzheimer's (I4800)
- Neurological Conditions - Parkinson's, MS, ALS (I5150)
- Chronic Obstructive Pulmonary Disease COPD (I6202)
- Other Medical Condition (I8005)
- Additional ICD Codes text field

Section 2: KPS/PPS/FAST/NYHA/ECOG score effecting ADL?
- Link to Performance Status section

Section 3: Nature & Condition of Terminal Illness / LCD Eligibility
- Disease Trajectory: Stable | Gradual Decline | Rapid Decline | Actively Dying
- Evidence of Decline (required, multi-select)
- LCD Eligibility Narrative (required textarea)

Section 4: Prognosis & Goals Alignment

### 3. Vitals & Performance Status
Tabs: Vitals | Weight | Pain Screen | **Performance Status**

**Vitals Tab:**
- Blood Pressure (Systolic/Diastolic, required)
- Heart Rate (bpm, required), Pulse Rhythm dropdown
- Respirations (/min, required), Respiratory Effort dropdown
- Temperature (required), Obtained? Yes/No
- Oxygen: SpO2, Oxygen Use toggle, Device dropdown, Flow Rate
- Weight & Nutrition Trends with 30/90/180 Day change alerts
- Pain as Fifth Vital Sign: 0-10 scale

**Performance Status Tab:**
Always visible (all patients):
- PPS (Palliative Performance Scale) * — Dropdown 0-100% in 10% increments + Justification textarea
- KPS (Karnofsky Performance Status) * — Dropdown 0-100 in 10-point increments + Justification textarea

Conditional (diagnosis-driven):
- ECOG (Eastern Cooperative Oncology Group) — Visible when Cancer Dx detected. Scale 0-5 (0=Fully Active, 1=Restricted, 2=Ambulatory/self-care, 3=Limited self-care, 4=Completely disabled, 5=Dead)
- FAST (Functional Assessment Staging) — Visible when Dementia Dx. 7-stage scale
- NYHA (New York Heart Association) — Visible when Heart Failure Dx. Class I-IV

### 4. Pain Assessment (HOPE: J0900)
- Pain Present (HOPE J0900, required)
- Assessment Method (required)
- Pain Severity: Current/Best 24h/Worst 24h/Acceptable Goal
- Interactive Body Map (front/back anatomic figures with clickable regions)
- Documented pain locations with quality, frequency, treatment, effectiveness
- HOPE Pain Data auto-mapped
- SFV evaluation integration

### 5-13. Body System Assessments
Each has: Assessment Status, Clinical Findings, Symptom Severity, HOPE Auto-Mapping badge, SFV Candidate alerts
- Neuro/Mental/Sensory, Respiratory, Cardiovascular (NYHA auto-linked), GI/Nutrition, Genitourinary, Musculoskeletal, Skin/Wounds (body map), Endocrine, Infection/Immunological

### 14. Imminently Dying Assessment
- End-of-Life Status, Estimated Stage, Family Distress, Caregiver Preparedness

### 15-17. Interdisciplinary Screenings
- Psychosocial (PHQ-2), Spiritual (HOPE F3000), Bereavement Risk

### 18-19. Environmental & Personal Care
- Emergency Preparedness, Hospice Aide needs, Volunteer/Community support

### 20. Teaching & Education Summary (Read-Only Dashboard)
- Auto-generated, education gaps identified, teaching coverage percentage

### 21. HOPE QES Auto-Mapping Dashboard
- All 15 HOPE items with CMS codes in BLUE
- Source screen, source field, harvested value, mapping status
- J2052/J2053 flagged as SFV Required in RED
- QIES submission readiness tracker
- 13/15 mapped, pending SFV completion

### 22. SFV Evaluation Screen
- SFV Screening & Parameters (2-calendar-day protocol)
- Active SFV Candidates table (J2051.A through J2051.H)
- Severity levels, source sections, SFV status
- SFV Resolution tracking (J2052 & J2053)
- Protocol compliance deadline

### 23. Compliance Validation Engine (Read-Only Dashboard)
- Clinical Data, HOPE Domains, Referrals, Care Plans, Teaching, Cross-System percentages

### 24. Finalization
- 27/27 Sections Complete checklist
- Electronic Signature with certification statement

---

## Cross-System Features
- **HOPE Auto-Mapping**: Green tags with CMS codes on mapped fields
- **SFV Triggers**: Red indicators, 2-day compliance window
- **IDG Review Triggers**: Flagged for care conference
- **Care Plan Auto-Linking**: Findings -> Problem -> Goal -> IDG Review
- **Compliance Validation Engine**: Real-time regulatory checking
- **Conditional Display Logic**: ECOG for Cancer, FAST for Dementia, NYHA for CHF

## Key UI Patterns
- Header Bar: Patient info, diagnosis, physician, assessment status badge
- Left Sidebar: Collapsible sections with completion indicators
- Progress Bar: Percentage with section count
- Required Fields: Asterisk (*), tracked in sidebar checklist
- HOPE Tags: Green (#059669) with CMS code
- SFV Alerts: Red (#DC2626) with protocol rules
- Action Bar: Save Draft, Sign & Lock, Print, Send to QA
- Navigation Footer: + Care Plan, Previous/Next section links
