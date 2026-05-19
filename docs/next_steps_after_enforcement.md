# SNS EMR – Post‑Enforcement Build Plan (ANTI‑DRIFT)

This document defines what work is allowed **after enforcement is locked**
and prevents the project from drifting into unsafe or premature features.

---

## CURRENT STATE (REQUIRED BEFORE MOVING ON)

Before advancing, the system MUST have:

✅ RN visit mode enforcement  
✅ RN refusal escalation engine  
✅ Discharge‑for‑cause guarded workflow  
✅ Clear distinction between VISIT vs TELEPHONE  
✅ No silent LVN‑only or CHHA‑only care states  

If any of the above are missing, STOP.

---

## PHASE 1 — CONSISTENCY & AUDIT ENGINES (NEXT PRIORITY)

### Goals
- Prevent interdisciplinary contradictions
- Protect MD signing
- Eliminate survey “inconsistent documentation” findings

### Required work
- Consistency audit engine:
  - RN vs LVN vs CHHA vs MSW narratives
  - Weight, appetite, function, pain, decline
- Hard stops on MD certification when inconsistencies exist
- One‑story enforcement across IDG

---

## PHASE 2 — DISCIPLINE DOCUMENTATION (SAFE TO PROCEED)

Only after enforcement + consistency are complete.

### Guardrails for ALL discipline documentation
- Documentation must:
  - Respect scope
  - Defer to RN clinical narrative
  - Never imply eligibility or prognosis unless allowed
- Voice recommendations must be discipline‑scoped
- Notes must not finalize if scope violations exist

### Deliverables
- RN documentation (already primary)
- LVN/LPN finalize logic
- CHHA/AIDE finalize logic
- MSW/BSW finalize logic
- Chaplain finalize logic

All finalize logic must reference:
- `core_rules.md`

---

## PHASE 3 — VOICE → RECOMMENDATION (OPTIONAL, LATER)

Voice features may ONLY:
- Suggest discipline‑appropriate language
- Never generate cross‑scope recommendations
- Never override enforcement rules

Voice is an assistant, not an authority.

---

## WORK THAT IS EXPLICITLY BLOCKED UNTIL LATER

❌ UI polish  
❌ Optimization work  
❌ Analytics dashboards  
❌ Automation that bypasses tasks  
❌ Any feature that weakens enforcement  

---

## PROJECT PRINCIPLE (READ THIS WHEN TEMPTED TO CUT CORNERS)

> “If the system allows something that would fail a survey,
> the system is wrong — not the surveyor.”

SNS EMR is built to protect:
- Patients
- Nurses
- The organization
- The medical director

Enforcement comes first.
Everything else is downstream.