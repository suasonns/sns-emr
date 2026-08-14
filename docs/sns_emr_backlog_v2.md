# SNS Hospice EMR – V2 Backlog (Post Versioning & POC Stabilization)

---

# ✅ PURPOSE

This document defines the **next stage** of SNS development after:

- ✅ POC_UPDATE deduplication (same-cycle fix)
- ✅ Visit finalize stability
- ✅ Reopen workflow (72-hour correction model)
- ✅ Note amendment endpoint
- ✅ Versioned documentation model (in progress)

---

# ✅ WHAT WAS COMPLETED

## ✅ 1. POC TASK ENGINE STABILIZED

### Fix implemented:
- Prevent duplicate `POC_UPDATE` per cycle
- Same-cycle detection:
  - patient_id
  - task_type
  - origin
  - due_date

### Result:
- ✅ No more DB `UniqueViolation`
- ✅ One obligation per cycle enforced
- ✅ Multiple visits contribute to same POC

---

## ✅ 2. VISIT FINALIZE FLOW

- Finalize visit → system triggers compliance logic
- Visit status transitions:
  - DRAFT → FINALIZED → REOPENED → FINALIZED

✅ Verified:
- finalize returns 200
- audit trail logs correctly

---

## ✅ 3. REOPEN WORKFLOW (CRITICAL)

### Rules implemented:

- Author CANNOT edit after finalize
- Admin/Supervisor MUST reopen

### 72-hour rule:
- <72 hrs → editable via reopen ✅
- >72 hrs → LOCK → amend only ✅

### Endpoint:


POST /visits/{visit_id}/reopen

---

## ✅ 4. NOTE AMENDMENT (BASIC)

Endpoint:

POST /notes/{note_id}/amend

### Requirements:
- reason ✅
- content ✅

---

## ✅ 5. DOCUMENT VERSIONING (NEW CORE SYSTEM)

### NEW MODEL:

Instead of overwrite:

OLD ❌ → replaced

Now:

v1 → original
v2 → corrected (ACTIVE)

---

### ✅ PRINCIPLES

- Truth can change ✅
- History cannot be deleted ✅
- Only latest version is active ✅

---

### ✅ REQUIRED TABLES (IF NOT YET CREATED)

## notes

id
visit_id
current_version_id
created_at
updated_at

## note_versions

id
note_id
version_number
content
amend_reason
created_at
created_by
is_active

---

### ✅ REQUIRED BEHAVIOR

When amend is called:

1. Find current version
2. Mark it inactive
3. Insert new version
4. Update notes.current_version_id

---

# ✅ CURRENT SYSTEM STATE

| Component | Status |
|----------|-------|
| Visits | ✅ Stable |
| Tasks (POC_UPDATE) | ✅ Stable |
| Reopen logic | ✅ Working |
| Versioning | ⚠ In progress |
| Amend endpoint | ⚠ Needs version integration |

---

# 🚀 NEXT PHASE (PRIORITY ORDER)

---

## ✅ PRIORITY 1 — COMPLETE NOTE VERSIONING

### REQUIRED:

- Convert `/notes/{note_id}/amend` to:


INSERT new version
DO NOT UPDATE existing row

### ADD:

- GET endpoint returns ONLY active version
- optional: GET version history

---

## ✅ PRIORITY 2 — FINALIZE NOTE PIPELINE

### Add:


POST /notes/{note_id}/finalize

### Behavior:

| Condition | Behavior |
|----------|--------|
| <72 hrs | allow reopen/edit |
| >72 hrs | lock |
| signed/reviewed | immediate lock |

---

## ✅ PRIORITY 3 — LINK NOTES → VISIT → TASK

### REQUIRED:

- POC task must reference:
  - visit_id ✅
  - note_id ✅ (NEW)

---

### IMPACT:


Task completion now traceable to:
VISIT → NOTE VERSION → CLINICAL CONTENT

---

## ✅ PRIORITY 4 — DYNAMIC CARE MODEL ENGINE

### PURPOSE:

Automatically determine:

- RN-only
- RN + LVN
- RN + CHHA
- Supervisory requirement
- POC trigger logic

---

### INPUTS:

has_chha
has_lvn
has_wounds
acuity_state

---

### OUTPUT:


care_model_type
requires_supervisory
poc_trigger_mode

---

### RULES:

#### RN_ONLY
- Any RN visit triggers POC

#### RN + SUPPORT STAFF
- Supervisory RN required

#### WOUND OVERRIDE
- Always 14-day cadence

#### CRISIS
- Every RN visit triggers same-day POC

---

## ✅ PRIORITY 5 — CONDITION DETECTION ENGINE

### PURPOSE:

Auto-detect clinical conditions from notes

---

### DETECT:

- wounds ✅
- psychosocial issues ✅
- spiritual distress ✅
- bereavement ✅

---

### INPUT:
- note_versions.content
- structured fields

---

### OUTPUT:


{
has_wounds
psychosocial_issue
spiritual_distress
bereavement_flag
}

---

## ✅ PRIORITY 6 — REFUSAL + RE-OFFER SYSTEM

### REQUIRED:

| Field | Description |
|------|------------|
| was_offered | BOOLEAN |
| refused_at | TIMESTAMP |
| refusal_reason | TEXT |
| must_reoffer | BOOLEAN |

---

### RULES:

- RN ❌ cannot refuse
- MD ❌ cannot refuse
- LVN/CHHA/MSW/SC ✅ can refuse

---

### TRIGGERS:

- psychosocial issue → re-offer MSW
- spiritual → re-offer Chaplain

---

## ✅ PRIORITY 7 — BEREAVEMENT ENGINE

### REMOVE:
- standalone bereavement form ❌

---

### REPLACE WITH:
- aggregated signals from notes ✅

---

### OUTPUT:

{
rn_present
sw_present
chaplain_present
}

---

## ✅ PRIORITY 8 — NOTIFICATION ENGINE

### ADD:

| Time | Action |
|------|-------|
| -3 days | notify |
| -1 day | notify |
| due date | alert |
| overdue | escalate |

---

## ✅ PRIORITY 9 — TRANSFER ESCALATION

### TRIGGER:
- RN refusal ❌
- MD refusal ❌
- F2F refusal ❌

---

### ACTION:
- flag patient
- notify admin
- audit event

---

# ✅ FINAL SYSTEM PRINCIPLE

> ✅ ONE POC obligation per cycle  
> ✅ MANY visits contribute  
> ✅ NOTES evolve via versioning  
> ✅ 72h correction window enforced  
> ✅ AFTER LOCK → AMEND ONLY  

---

# ✅ NEXT COMMANDS

When ready:

👉 “implement note versioning logic”  
👉 “implement dynamic care model engine”  
👉 “implement condition detection engine”

---

# ✅ END STATE TARGET

This system will become:

✅ Versioned clinical EMR  
✅ Condition-aware workflow engine  
✅ Compliance-driven task engine  
✅ Survey-defensible hospice platform  

---

# ✅ ICA EXPANSION BACKLOG (CURRENT ACTIVE QUEUE)

## ACTIVE

### Shared ICA Contract

Status: ACTIVE

Purpose:
- Define one shared assessment lifecycle for all discipline ICA workflows.
- Reuse the same save/load/lock/intelligence patterns across RN, MSW, and SC.
- Keep evidence sourcing tied to patient data, diagnosis sources, and clinical notes instead of form-only state.

Requirements:
- common assessment_id / patient_id / status / locked model
- common API contract for save, update, load, lock, and intelligence
- common recommendation-only clinical intelligence output
- discipline-specific form payload while sharing the same governance model

### RN ICA Intelligence

Status: DONE

Completed:
- RN ICA assessment saved and persisted via the canonical visits API
- RN ICA route remains live in the app shell
- RN ICA intelligence service generates risk findings and recommendations from assessment + evidence
- UI surfaces RN ICA intelligence in the existing screen
- targeted validation passed for the current engine path

---

## NEXT

### MSW ICA

Status: NEXT

Scope:
- build the MSW ICA assessment structure and route using the shared ICA contract
- capture psychosocial support, caregiver burden, resource barriers, social isolation, and financial risk
- pull evidence from patient notes, diagnosis context, and social context records
- create save/load/lock/intelligence endpoints
- surface a discipline-specific intelligence panel in the MSW workflow

Required outputs:
- support risk summary
- resource-gap flags
- caregiver stress indicators
- missing evidence warnings
- recommendation-only intervention priorities

### SC ICA

Status: NEXT

Scope:
- build the SC ICA assessment structure and route using the same shared contract
- document spiritual distress, faith/cultural considerations, chaplain needs, and grief support concerns
- source support from patient notes, family context, and chaplain documentation
- create save/load/lock/intelligence endpoints
- surface a discipline-specific intelligence panel in the SC workflow

Required outputs:
- spiritual distress flags
- chaplain need cues
- family support and meaning-making concerns
- referral and follow-up recommendations
- missing evidence warnings

---

## DEFERRED

### Full audit-survival completion

Status: DEFERRED

This remains outside the active discipline ICA queue until the shared contract and the RN/MSW/SC flows are stable and validated.

Deferred items:
- full audit-trail finalization model
- final cross-discipline review automation
- downstream care-plan reconciliation work
- larger compliance automation beyond the current intelligence layer

---

## DONE

### RN ICA foundation

Status: DONE

Completed work:
- RN ICA route is live and usable in the app shell
- canonical backend persistence exists under the visits API
- RN ICA runtime validation passed
- RN ICA intelligence is implemented and surfaced in the screen
- active phase remains aligned to the clinical intelligence foundation and ICD engine

---

# ✅ CONTINUATION ORDER

1. Complete the shared ICA contract
2. Implement MSW ICA using that shared model
3. Implement SC ICA using that same model
4. Expand downstream task and review automation only after the shared layer is stable

This is the correct next sequence because RN ICA is already validated and is the reference implementation for the discipline-specific pattern.

---
