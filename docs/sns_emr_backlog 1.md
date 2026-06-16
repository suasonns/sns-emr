✅ Dynamic care model engine
This will determine automatically:

RN-only vs RN+LVN vs RN+CHHA
supervisory requirements
POC trigger behavior


👉 Say:
“build dynamic care model engine”

🚀 NEXT STEP
Now that POC logic is complete, the next major system:
✅ Dynamic Condition Engine
👉 to automatically detect:

wounds ✅
psychosocial issues ✅
spiritual distress ✅

and trigger tasks accordingly

👉 Say:
“build condition detection engine”
…and I’ll wire it to:
✅ POC
✅ MSW re-offer
✅ Chaplain triggers
✅ Bereavement aggregation


# SNS Hospice EMR – Compliance & Workflow Backlog

## PURPOSE
This document defines the current system state and the next set of required compliance and workflow enhancements for the SNS Hospice EMR.  
The goal is to ensure:
- Clinical accuracy
- Regulatory compliance (CMS/ACHC/CDPH/Joint Commission)
- Audit defensibility
- Operational reliability

---

# ✅ CURRENT SYSTEM STATUS (CONFIRMED WORKING)

## Infrastructure
- FastAPI backend stable
- PostgreSQL schema aligned
- Alembic migrations applied
- Uvicorn runs clean

## Core Features Working
- ✅ Patient creation + retrieval
- ✅ Visit creation + finalize flow
- ✅ Task creation from SOC
- ✅ Task completion with evidence linkage
  - completed_at
  - completion_reference_type
  - completion_reference_id
- ✅ POC_UPDATE task generation
- ✅ Overdue escalation engine running
- ✅ Audit logging active

## Patient Data Model (CONFIRMED)
- has_chha ✅
- has_lvn ✅
- has_wounds ✅

---

# ⚠️ REQUIRED CORRECTIONS

## 1. RN Supervisory Rule (FIX REQUIRED)

### OLD (WRONG)
All ROUTINE RN visits must be supervisory

### CORRECT
Supervisory is only required if:
- patient.acuity = ROUTINE
- AND (has_chha OR has_lvn)

### RN-only patients
- No supervisory requirement
- All RN visits = follow-up

---

## 2. Wound-Based POC Rule

If:
- patient.has_wounds = true

Then:
- POC must be updated every 14 days
- regardless of supervisory visits

---

## 3. Discipline-Specific ICA Rules

| Task | Completion Discipline |
|------|----------------------|
| INITIAL_RN_ICA | RN |
| INITIAL_MSW_ICA | MSW/LCSW |
| INITIAL_SC_ICA | Chaplain |

---

## 4. BSW Supervision Rule

- BSW performs visit ✅
- BSW signs note ✅
- Task = NOT completed ❌
- MSW/LCSW must countersign ✅
- THEN task = completed ✅

---

# ✅ PRIORITY ENGINE 1
# Dynamic Care Model Engine

## PURPOSE
Determine automatically:
- RN-only vs RN+LVN vs RN+CHHA
- supervisory requirements
- POC trigger behavior

---

## INPUTS
- has_chha
- has_lvn
- has_wounds
- acuity_state

---

## OUTPUT


---

## RULES

### RN_ONLY
- no CHHA
- no LVN
- POC triggered by ANY RN visit

---

### RN + CHHA / LVN
- supervisory visits required
- POC triggered ONLY by supervisory RN visit

---

### WOUND OVERRIDE
- POC cadence = every 14 days

---

### CRISIS
- every RN visit triggers same-day POC

---

# ✅ PRIORITY ENGINE 2
# Dynamic Condition Detection Engine

## PURPOSE
Automatically detect clinical conditions from documentation

---

## DETECTIONS

### 1. Wounds
→ affects POC cadence

### 2. Psychosocial Issues
→ triggers MSW re-offer

### 3. Spiritual Distress
→ triggers Chaplain re-offer

### 4. Bereavement Content
→ feeds bereavement aggregation

---

## INPUTS
- RN notes
- MSW notes
- Chaplain notes
- structured fields

---

## OUTPUT


{
has_wounds
psychosocial_issue
spiritual_distress
bereavement_flag
}

---

# ✅ BEREAVEMENT REDESIGN

## REMOVE
- standalone bereavement form ❌

## REPLACE WITH
- RN / MSW / Chaplain notes as source ✅

---

## OUTPUT MODEL


{
rn_present
sw_present
chaplain_present
source_notes
}

---

# ✅ REFUSAL + RE-OFFER SYSTEM

## REFUSABLE
- LVN
- CHHA
- MSW
- SC

---

## NOT REFUSABLE
- RN ❗
- MD ❗
- F2F ❗

→ If refused → escalate / transfer required

---

## REQUIRED FIELDS


was_offered
refused_at
refusal_reason
must_reoffer

---

## RE-OFFER TRIGGERS
- psychosocial issue
- spiritual issue
- recert
- IDG

---

# ✅ TASK NOTIFICATION SYSTEM

## CURRENT
- overdue detection ✅
- no pre-due notification ❌

---

## REQUIRED

| Time | Action |
|------|-------|
| 3 days before | notify |
| 1 day before | notify |
| due today | alert |
| overdue | escalate |

---

# ✅ OVERDUE ENGINE
- Already implemented ✅
- Needs integration with pre-due notifications

---

# ✅ TRANSFER ESCALATION SYSTEM

## TRIGGER
RN / MD / F2F refused

---

## ACTION
- flag patient
- notify admin
- audit event
- require resolution

---

# 🚀 IMPLEMENTATION ORDER

## PHASE 1
- Fix RN supervisory logic
- Fix POC automation (wounds / RN-only / support staff)

---

## PHASE 2
- Fix ICA discipline enforcement
- Implement BSW countersign system
- Harden task completion API

---

## PHASE 3
- ✅ Dynamic Care Model Engine
- ✅ Dynamic Condition Detection Engine

---

## PHASE 4
- Bereavement aggregation
- Refusal + re-offer system

---

## PHASE 5
- Notification system
- Dashboard alerts
- Transfer escalation engine

---

# ⚠️ IMPORTANT — DO NOT DRIFT

When you’re ready, you can come back and say:

👉 “implement dynamic care model engine”  
or  
👉 “implement condition detection engine”  

…and the system will generate:

- ✅ full production-grade code (no snippets)
- ✅ exact file locations
- ✅ aligned with this document
- ✅ ready to paste into repo

---

# ✅ FINAL NOTE

This system is evolving into:

✅ Dynamic care model engine  
✅ Condition-driven workflow engine  
✅ Discipline-enforced compliance engine  
✅ Survey-defensible EMR  

---