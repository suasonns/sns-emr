"""
SNS EMR COMPLIANCE NOTICE
This module is governed by:
  /docs/compliance/core_rules.md

If behavior in this file conflicts with core_rules.md,
the behavior in this file MUST be changed.
"""

# SNS EMR – Core Compliance Rules (NON‑NEGOTIABLE)

This document defines the **canonical compliance rules** for the SNS Hospice EMR.
These rules exist to prevent regulatory drift, survey exposure, and unsafe clinical behavior.

If a feature, workflow, or documentation pattern conflicts with this document,
**the feature is wrong and must be changed**.

This file is the single source of truth for:
- CMS Hospice Conditions of Participation (CoPs)
- ACHC
- CDPH (California)
- The Joint Commission
- CHAP

---

## 1. RN ROLE IS FOUNDATIONAL (CANNOT BE SUBSTITUTED)

### 1.1 RN services are core hospice services
- RN is the clinical coordinator and assessment authority.
- LVN/LPN, CHHA/AIDE, MSW, and CHAPLAIN **cannot substitute** for RN functions.
- Anything LVN/CHHA can do, RN can do.
- RN functions **cannot** be delegated downward.

### 1.2 RN services cannot be “declined”
- RN **cannot** be marked as a declined discipline.
- Patient/family may **refuse an RN visit**, but this is treated as a **care delivery risk**, not a preference.
- RN refusal triggers escalation and resolution pathways.

---

## 2. VISIT MODES ARE STRICTLY DEFINED

### 2.1 Visit modes
All visits must have an explicit visit mode:

- `IN_PERSON`
- `TELEPHONE`
- `VIDEO` (provider‑only, limited use)

### 2.2 RN visit requirements
- **RN visits that satisfy hospice requirements must be IN_PERSON.**
- RN TELEPHONE calls:
  - are allowed as communication
  - are NOT visits
  - do NOT satisfy visit frequency
  - do NOT satisfy assessments
  - do NOT satisfy supervisory requirements
- RN VIDEO visits are **not allowed** to replace in‑person nursing visits.

### 2.3 Labeling requirement
All RN telephone interactions must be clearly labeled:
> “RN Telephone Call — does not replace in‑person visit”

---

## 3. RN REFUSAL = CARE DELIVERY RISK (NOT BUSINESS AS USUAL)

### 3.1 RN refusal handling
When an RN visit is refused:
- A care‑delivery‑risk event is created
- Escalation tasks are automatically generated
- The chart is flagged as **AT RISK FOR DISCHARGE FOR CAUSE**

### 3.2 Mandatory escalation steps
The system must enforce:
- Education on why RN visits are required
- Offer of an alternate RN
- IDG review
- Medical Director visibility

No RN refusal may be silently ignored.

---

## 4. DISCHARGE FOR CAUSE (DFC) IS GUARDED

### 4.1 When DFC is allowed
Discharge for cause is only allowed when:
- RN services are refused
- Care delivery is seriously impaired
- Resolution attempts are documented
- IDG has reviewed
- Medical Director has ordered discharge

### 4.2 Hard checklist before discharge
SNS EMR must block discharge unless ALL are present:
- RN refusal events documented
- Education documented
- Alternate RN offered
- IDG review completed
- MD discharge order
- Narrative explicitly states “care delivery seriously impaired”

---

## 5. RN‑ONLY CARE MODE (VALID, BUT LIMITED)

RN‑only care is allowed **only when**:
- All other disciplines are declined by patient/family
- RN visits continue in person

RN‑only care is **NOT allowed** when:
- RN visits are refused
- Care status is AT_RISK_FOR_DFC

---

## 6. DISCIPLINE DOCUMENTATION GUARDRAILS (ALL DISCIPLINES)

### 6.1 Scope enforcement
Each discipline may document **only within scope**:

- RN: clinical assessment, decline, symptom management, POC ownership
- LVN/LPN: RN‑directed treatments and observations
- CHHA/AIDE: tasks performed, tolerance, observations only
- MSW/BSW: psychosocial assessment and intervention
- CHAPLAIN: spiritual assessment and support
- PROVIDERS: orders, certification, medical decision‑making

### 6.2 No cross‑scope narrative
- No discipline may contradict RN narrative without documented escalation.
- No discipline may imply prognosis, eligibility, or decline outside scope.

---

## 7. TELEPHONE ≠ VISIT (ALL DISCIPLINES)

- Telephone contacts may be documented.
- Telephone contacts do NOT replace required visits.
- Telephone contacts do NOT satisfy supervision or assessment obligations.

---

## 8. AUDIT & FINALIZATION RULES

- No note may finalize if required tasks are incomplete.
- All task completion requires:
  - timestamp
  - completing user
  - evidence reference
- Survey logic > convenience logic.

---

## 9. CHANGE CONTROL

Any proposed change that:
- weakens RN authority
- allows substitution of visits
- reduces escalation requirements
- blurs discipline scope

**must be rejected** unless this document is formally revised.

This document is intentionally strict.
That strictness is what keeps the system survey‑defensible.