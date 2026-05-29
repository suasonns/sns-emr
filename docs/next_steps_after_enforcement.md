# \## SNS EMR – Post‑Enforcement Build Plan (ANTI‑DRIFT)

# 

# This document defines what work is allowed \*\*after enforcement is locked\*\*

# and prevents the project from drifting into unsafe, survey‑risky features.

# 

# \---

# 

# \## CURRENT STATE (REQUIRED BEFORE MOVING ON)

# 

# Before advancing, the system MUST have:

# 

# ✅ RN visit mode enforcement  

# ✅ RN supervisory guardrails  

# ✅ POC\_UPDATE task compliance (ROUTINE +14, CRISIS same‑day)  

# ✅ Tenant isolation enforced  

# ✅ Discipline normalization and validation  

# ✅ Explicit distinction between CLINICAL vs ADMINISTRATIVE visits  

# 

# If any of the above are missing, STOP.

# 

# \---

# 

# \## PHASE 1 — CONSISTENCY \& AUDIT ENGINES (LOCKED)

# 

# \### Goals

# \- Prevent interdisciplinary contradictions

# \- Protect MD signing

# \- Eliminate survey findings for inconsistent documentation

# 

# \### Required Work

# \- Consistency audit engine across disciplines:

# &#x20; - RN vs LVN vs CHHA vs MSW vs Chaplain narratives

# &#x20; - Weight, appetite, pain, decline, function

# \- Hard stops on MD certification if inconsistencies exist

# \- Single clinical story enforcement across IDG

# 

# ✅ This phase is considered \*\*complete\*\* once RN and task enforcement are green.

# 

# \---

# 

# \## PHASE 2 — DISCIPLINE DOCUMENTATION (LOCKED)

# 

# \### Guardrails for ALL discipline documentation

# \- Documentation must:

# &#x20; - Respect scope

# &#x20; - Defer to RN for clinical authority

# &#x20; - Never imply eligibility or prognosis unless allowed

# &#x20; - Never override enforcement logic

# 

# \### Deliverables

# \- RN finalize logic ✅

# \- LVN/LPN finalize logic ✅

# \- CHHA/AIDE finalize logic ✅

# \- MSW finalize logic ✅

# \- Chaplain finalize logic ✅

# 

# All finalize logic must reference:

# \- core\_rules.md

# 

# \---

# 

# \## PHASE 2.5 — ADMINISTRATIVE / QAPI VISITS (NEW – LOCKED INTO PLAN)

# 

# \### Purpose

# Explicitly support \*\*QAPI and leadership oversight visits\*\* without contaminating clinical care.

# 

# Administrative visits are used to:

# \- Assess family satisfaction

# \- Document complaints or concerns

# \- Evaluate staff performance

# \- Capture improvement opportunities

# \- Document follow‑up actions

# 

# \### Non‑Negotiable Rules

# \- Administrative visits:

# &#x20; - MUST use visit\_discipline = ADMINISTRATIVE

# &#x20; - MUST NOT be counted as clinical care

# &#x20; - MUST NOT satisfy visit frequency

# &#x20; - MUST NOT trigger RN supervisory logic

# &#x20; - MUST NOT trigger POC\_UPDATE tasks

# \- Administrative visits may be performed by:

# &#x20; - MARKETER

# &#x20; - OFFICE\_MANAGER

# &#x20; - ADMIN

# &#x20; - QUALITY

# &#x20; - LEADERSHIP

# &#x20; - RN or LVN acting in an administrative role

# \- Clinical credential does NOT change visit purpose.

# 

# \### Required Controls

# \- Discipline must be selected from an enforced allowed list

# \- Discipline normalization enforced in API layer

# \- Administrative visits are auditable and timestamped

# \- Administrative visits are explicitly excluded from clinical task engines

# 

# \### Survey Positioning

# Administrative visits are part of QAPI and leadership oversight

# and are intentionally separated from clinical care.

# 

# \---

# 

# \## PHASE 3 — QAPI STRUCTURE (ALLOWED AFTER PHASE 2.5)

# 

# \### Allowed Enhancements

# \- Administrative visit reason codes:

# &#x20; - FAMILY\_SATISFACTION

# &#x20; - QAPI\_REVIEW

# &#x20; - STAFF\_EVALUATION

# &#x20; - COMPLAINT\_REVIEW

# &#x20; - SERVICE\_RECOVERY

# &#x20; - LEADERSHIP\_ROUNDING

# \- QAPI reporting dashboards:

# &#x20; - Family satisfaction trends

# &#x20; - Complaint follow‑up closure

# &#x20; - Staff performance feedback loops

# 

# \### Explicitly Not Allowed

# ❌ Free‑text visit disciplines  

# ❌ Administrative visits masquerading as nursing care  

# ❌ Clinical metrics derived from administrative visits  

# 

# \---

# 

# \## WORK THAT IS EXPLICITLY BLOCKED UNTIL LATER

# 

# ❌ UI polish  

# ❌ Optimization work  

# ❌ Automation that bypasses enforcement  

# ❌ Analytics that mix clinical and administrative data  

# ❌ Any feature that weakens survey posture  

# 

# \---

# 

# \## PROJECT PRINCIPLE (NON‑NEGOTIABLE)

# 

# “If the system allows something that would fail a survey,

# the system is wrong — not the surveyor.”

# 

# SNS EMR exists to protect:

# \- Patients

# \- Nurses

# \- The organization

# \- The Medical Director

# 

# Enforcement comes first.

# Everything else is downstream.

# 

# \---

# 

# \### 2026‑05‑29 — Architectural Governance Update

# \- Administrative visits formally locked into system design

# \- QAPI explicitly supported without clinical contamination

# \- Discipline ≠ Role ≠ Credential formally separated

# \- Survey language aligned with CMS / ACHC / CHAP expectations

