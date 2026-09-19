# RNICA Redesign Source of Truth — Final Figma Input

STATUS: AUTHORITATIVE DESIGN DOCUMENT
FIGMA DESIGN AUTHORITY
REPOSITORY DISCOVERY COMPLETE
THIS DOCUMENT OVERRIDES REPOSITORY STRUCTURE
THIS DOCUMENT DEFINES NURSE WORKFLOW

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
REDESIGN: NOT YET AUTHORIZED — this document is the design input, not the
redesign itself.

All prior repository-evidence documents in `docs/tenant-platform/`
(dependency maps, wiring matrices, narrative analyses, gating verification)
are supporting evidence only. This document does not describe code, models,
tables, services, APIs, repositories, or React components. It describes
what the nurse sees, does, and needs, screen by screen.

---

## PURPOSE

Figma designs from this document. Not from code. Not from component trees.
Not from repository structure. Not from historical RNICA workflows.

The purpose is to define:
- What nurses see
- What nurses do
- What appears
- What is hidden
- What is conditional
- What AI surfaces
- What workflow comes next

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

## LOCKED CLINICAL RULES

**PPS** — Always Visible

**KPS** — Always Visible

**FAST** — Visible only when Primary Diagnosis OR Secondary Diagnosis
contains: Dementia, Alzheimer's Disease, or a dementia-related diagnosis.
Hide otherwise.

**ECOG** — Visible only when Primary Diagnosis OR Secondary Diagnosis
contains: Cancer, an oncology diagnosis, metastatic disease, or
hematologic malignancy. Hide otherwise.

**NYHA** — Visible only when Primary Diagnosis OR Secondary Diagnosis
contains: CHF, Congestive Heart Failure, Cardiomyopathy, or Heart Failure.
Hide otherwise.

Multiple scales may display simultaneously when clinically appropriate
(example: CHF + Dementia displays PPS, KPS, NYHA, and FAST; hides ECOG).

Never show:
- Disabled scales
- Greyed-out scales
- Empty placeholders
- "Not Applicable" panels

Hide irrelevant scales completely — do not disable, grey out, or label
them as not applicable.

---

## SCREEN 1 — PATIENT STORY

**Purpose:** Help the nurse understand the patient before documenting.

**Always Visible:**
- Patient Name
- Hospice Diagnosis
- Primary Diagnosis
- Current Admission
- Current Episode
- Current Benefit Period
- Recent Hospitalization Summary
- Caregiver Summary
- Current Risks
- Missing Information
- AI Summary
- Suggested Next Action

**Do Not Show:** Forms, Validation Errors, Finalization Tasks.

**Nurse Question:** Who is this patient?

**Completion Criteria:** Nurse understands the patient in under 30 seconds.

---

## SCREEN 2 — EVIDENCE & INTAKE

**Purpose:** Show what is already known.

**Always Visible:**
- Referral Facts
- Face Sheet Facts
- Available Documents
- Structured Findings
- Evidence Sources
- AI Evidence Summary
- Missing Evidence
- Suggested Evidence Review

**Nurse Question:** What information do I already have?

**Completion Criteria:** Nurse can identify available evidence before
documenting.

---

## SCREEN 3 — FUNCTIONAL STATUS

**Purpose:** Assess current function and decline.

**Always Visible:**
- PPS
- KPS
- ADLs
- Mobility
- Transfers
- Fall Risk
- Cognitive Status

**Conditionally Visible:** FAST, ECOG, NYHA (per Locked Clinical Rules above).

**AI Content:**
- Significant Decline
- Missing Scales
- Suggested Assessments

**Nurse Question:** How functional is this patient today?

**Completion Criteria:** Functional status can be assessed from one screen.

---

## SCREEN 4 — PAIN & SYMPTOM BURDEN

**Purpose:** Assess symptom burden.

**Always Visible:**
- Pain
- Pain Severity
- Pain Pattern
- Pain Management
- Pain Findings
- Dyspnea
- Anxiety
- Depression
- Agitation
- Fatigue
- Sleep
- Nausea
- Appetite
- Weight Change

**AI Content:**
- Pain Findings
- Missing Pain Information
- Suggested Follow-Up

**Nurse Question:** What symptoms are impacting this patient?

**Completion Criteria:** Pain and symptom workflow completed without
navigating to multiple screens.

---

## SCREEN 5 — DIAGNOSIS & LCD

**Purpose:** Capture diagnosis-specific information.

**Always Visible:**
- Primary Diagnosis
- Secondary Diagnoses
- Comorbidities
- Terminal Prognosis
- Disease Trajectory
- HOPE Diagnosis Category
- LCD Supporting Evidence
- LCD Narrative
- Recent Utilization
- Recent Hospitalizations
- RN Addendum
- Clinician Clarification

**LOCKED RULE:** Do NOT show a Clinical Narrative field here.

**Nurse Question:** Why does this patient qualify for hospice?

**Completion Criteria:** Diagnosis and LCD requirements completed.

---

## SCREEN 6 — BODY SYSTEM REVIEW

**Purpose:** Head-to-toe clinical assessment.

**Sections:**
- Neurological
- Cardiovascular
- Respiratory
- Infection
- Gastrointestinal
- Nutrition
- Endocrine
- Genitourinary
- Musculoskeletal
- Skin & Wounds
- Imminent Death
- SFV

**Nurse Question:** What are the significant clinical findings?

**Completion Criteria:** All system findings reviewed.

---

## SCREEN 7 — CAREGIVER & SUPPORT

**Purpose:** Assess caregiver and support system.

**Always Visible:**
- Caregiver Assessment
- Psychosocial
- Spiritual
- Bereavement
- Personal Care
- Teaching Needs

**AI Content:**
- Caregiver Risk
- Caregiver Recommendations
- Teaching Priorities

**Nurse Question:** Who is supporting the patient and what are their risks?

**Completion Criteria:** Support system clearly understood.

---

## SCREEN 8 — SAFETY & CLINICAL RISK

**Purpose:** Surface risks immediately.

**Always Visible:**
- Fall Risk
- Safety Concerns
- Clinical Risks
- Imminent Death Indicators
- Behavior Risks
- Cognitive Risks
- AI Risk Findings
- Suggested Actions

**Nurse Question:** What could harm this patient?

**Completion Criteria:** Safety risks clearly understood.

---

## SCREEN 9 — ACP & GOALS OF CARE

**Purpose:** Document goals and treatment preferences.

**Always Visible:**
- Code Status
- CPR Preference
- Life Sustaining Treatment Preference
- Hospitalization Preference
- Advance Directives
- Decision Maker
- POA Information

**Nurse Question:** What care does the patient want?

**Completion Criteria:** Goals of care documented.

---

## SCREEN 10 — ORDERS & POC

**Purpose:** Connect assessment findings to the Plan of Care.

**Always Visible:**
- Problems
- Goals
- Interventions
- Orders
- Suggested Orders
- POC Readiness
- POC Findings

**Nurse Question:** What is the care plan?

**Completion Criteria:** POC workflow complete.

---

## SCREEN 11 — COMPLIANCE & READINESS

**Purpose:** Show what must be fixed before completion.

**Always Visible:**
- Missing Information
- Validation Findings
- Required Documentation
- Compliance Issues
- HOPE Status
- POC Status
- Readiness Status
- Suggested Actions
- AI Compliance Findings

**Nurse Question:** What is preventing completion?

**Completion Criteria:** Nurse understands remaining work.

---

## SCREEN 12 — AI ACTION CENTER

**Purpose:** Make existing AI visible.

**Always Visible:**
- AI Summary
- Findings
- Recommendations
- Missing Evidence
- Clinical Concerns
- Risk Findings
- Caregiver Suggestions
- Evidence Harvesting Output
- AI Status
- Last Analysis Timestamp
- Refresh AI

**Current AI Truth:** Refresh occurs on Load, Save, and Lock — not on
continuous typing. Do not invent live/continuous AI.

**Nurse Question:** What is AI telling me right now?

**Completion Criteria:** Nurse understands AI findings without hunting.

---

## SCREEN 13 — FINALIZATION

**Purpose:** Complete and sign the assessment.

**Always Visible:**
- Clinical Narrative
- Signature Certification
- Clinician Signature
- Readiness Checklist
- Lock Workflow

**LOCKED RULE:** This is the ONLY nurse-facing Clinical Narrative.
Authoritative narrative: the Finalization Clinical Narrative field.
The nurse completes the assessment first, then writes or reviews the
narrative last.

**Nurse Question:** Is this assessment ready to sign and lock?

**Completion Criteria:** Assessment can be finalized.

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

## FINAL ACCEPTANCE CRITERIA

- [ ] Patient Story visible first
- [ ] Functional Status workspace implemented
- [ ] FAST conditionally visible
- [ ] ECOG conditionally visible
- [ ] NYHA conditionally visible
- [ ] Pain workflow simplified
- [ ] AI findings visible
- [ ] Missing Information visible
- [ ] Compliance easier to understand
- [ ] One Clinical Narrative only
- [ ] No HospiceMD-style chart navigation
- [ ] Existing functionality preserved
- [ ] Existing compliance preserved
- [ ] Existing AI preserved
- [ ] Existing HOPE preserved
- [ ] Existing POC preserved

---

## FIGMA SUCCESS TEST

A nurse can answer, without searching through 27 sections:
- Who is this patient?
- Why is this patient hospice appropriate?
- What is missing?
- What is risky?
- What should I do next?
- What is AI telling me?
- Can I complete this assessment?

If not, redesign is not complete.

---

## FINAL QUESTIONS

1. **What is the exact nurse workflow from Start to Lock?**
   Screen 1 (Patient Story) → Screen 2 (Evidence & Intake) → Screen 3
   (Functional Status) → Screen 4 (Pain & Symptom Burden) → Screen 5
   (Diagnosis & LCD) → Screen 6 (Body System Review) → Screen 7 (Caregiver
   & Support) → Screen 8 (Safety & Clinical Risk) → Screen 9 (ACP & Goals
   of Care) → Screen 10 (Orders & POC) → Screen 11 (Compliance &
   Readiness) → Screen 12 (AI Action Center) → Screen 13 (Finalization).

2. **What should appear first?** Patient Story (Screen 1) — patient
   identity, hospice diagnosis, and AI Summary, before any form field.

3. **What should appear only when relevant?** FAST, ECOG, NYHA (per Locked
   Clinical Rules); condition-specific findings surfaced by AI within
   Screens 6-8.

4. **What should remain hidden until needed?** Irrelevant performance
   scales, Finalization tasks and validation errors on Screen 1, disabled/
   placeholder/"Not Applicable" controls anywhere.

5. **What should AI surface proactively?** Patient Story AI Summary and
   Suggested Next Action; Screen 3 significant decline and missing
   scales; Screen 4 pain findings and missing pain information; Screen 7
   caregiver risk and teaching priorities; Screen 8 AI risk findings;
   Screen 11 AI compliance findings; Screen 12's full AI output surfaced
   as a standing, always-reachable screen rather than something a nurse
   must trigger by saving or locking.

6. **What should never be shown?** Disabled or greyed-out scales, empty
   placeholders, "Not Applicable" panels, a second Clinical Narrative
   field outside Finalization, raw validation errors as the nurse's first
   view of the chart.

7. **What should never be redesigned?** Everything under Do Not Touch:
   HOPE Workflow, POC Adapter, Validation Engine, Structured Findings,
   RNICA Intelligence Data Contract, Autosave, Lock Workflow, Amendment
   Workflow, Audit Events, Required Fields, LCD Narrative, Signature
   Certification, Clinician Signature.

8. **What should be grouped together?** Diagnosis-specific narrative
   content (Disease Trajectory, LCD Narrative, HOPE Diagnosis Category,
   Comorbidities, Terminal Prognosis, RN Addendum, Clinician
   Clarification) on Screen 5; all performance/functional scales together
   on Screen 3; all symptom-burden content together on Screen 4; all AI
   output together on Screen 12 rather than scattered per-section.

9. **What should be removed from the nurse workflow entirely?** A second,
   diagnosis-workspace Clinical Narrative input — only one authoritative
   Clinical Narrative exists, in Finalization (Screen 13). Disabled/
   placeholder renderings of irrelevant performance scales.

10. **If Figma only had this document, could they design RNICA correctly
    without reading the repository?** YES — every screen states its
    purpose, its always-visible and conditionally-visible content, its AI
    content, its nurse question, and its completion criteria; the Locked
    Clinical Rules and Do Not Touch list state every hard constraint
    Figma must respect.

---

## GOAL

This document is the RNICA Design Authority. All prior repository
discovery documents in `docs/tenant-platform/` are supporting evidence
only. No implementation. No redesign. No code. No schema. No migrations.
