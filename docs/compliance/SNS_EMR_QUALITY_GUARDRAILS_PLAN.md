
# SNS EMR — Quality, Time, and Assessment Guardrails (ANTI-DRIFT)

**Status:** PLANNED / FUTURE PHASE (NON-ENFORCING)

This document captures and freezes the design decisions discussed regarding:
- hospice visit duration philosophy
- assessment-first care expectations
- protection of patients, staff, and organizations
- CMS/CDPH-aligned, non-punitive system behavior

This file exists to **prevent drift** and to ensure future implementation remains aligned with agreed principles.

---

## 1. Canonical Quality Philosophy Statement (LOCKED TEXT)

> "The organization identified a gap in symptom assessment and implemented corrective actions, including staff education and workflow adjustments, to reinforce comprehensive hospice-level care. Visit duration is guided by patient needs rather than arbitrary time requirements."

### Rules
- Text is **system-provided and locked** (not user-editable)
- Text is **organizational**, not personal
- Text is **not injected** into clinical documentation

---

## 2. Tenant-Level Toggle (FUTURE FEATURE)

### Flag Name (proposed)
`quality.philosophy.enabled`

### Scope
- Tenant-level
- Default: **OFF**

### When OFF
- No behavior change
- No quality philosophy surfaced
- Tenant manages QA externally

### When ON
The quality philosophy MAY be referenced in:
- QAPI / Quality Review screens
- Survey Readiness / Compliance Summary views
- QA flag explanations (soft, informational only)

### Explicit Non-Behavior
Even when enabled, this flag MUST NOT:
- block visits
- enforce minimum minutes
- penalize staff
- appear in bedside workflows

---

## 3. Time Handling — Authoritative Rule

### Source of Truth
- **Time-In / Time-Out entered by staff** is authoritative
- AI recording time is **supporting metadata only**

### Rationale
- CMS/CDPH do not require real-time documentation
- Patient care must not be interrupted for tooling

---

## 4. Visit Duration — System Position

### Regulatory Reality
- CMS/CDPH define **no minimum visit length**

### Organizational Practice (Allowed)
- Tenants MAY set internal expectations (e.g., ~45 minutes)
- These are **practice standards**, not regulatory rules

### System Rule
- SNS EMR MUST NOT hard-enforce visit duration
- SNS EMR MAY soft-flag patterns for QA review

---

## 5. Assessment-First Enforcement (CORE PRINCIPLE)

The system prioritizes **assessment quality over time spent**.

### Required Emphasis
- Symptom recognition (pain, bowel, dyspnea, agitation, etc.)
- Meaningful narrative
- Clear clinical reasoning

### Anti-Patterns to Guard Against
- "Vitals-only" visits
- Repeated very short visits with no substance
- Documentation that fails to justify medical necessity

---

## 6. Continuous Care (CC) Alignment

- CC eligibility is driven by **symptom crisis**, not dying alone
- Multiple staff visits per day are allowed
- RN daily assessment required to justify continuation
- Disciplines supported: RN, LVN, CHHA, MSW, SC

---

## 7. Unit Handling (Future Billing Layer)

- 1 unit = 15 minutes
- Unit calculation uses **Time-In / Time-Out**, rounded **DOWN**
- Billing logic is explicitly deferred

---

## 8. Staff Protection Principles (NON-NEGOTIABLE)

The system MUST:
- protect clinicians who prioritize patient care
- avoid punishment for documentation timing
- avoid forcing false documentation

---

## 9. Survey Positioning (Canonical)

When explaining system behavior to surveyors:

> "The organization emphasizes comprehensive hospice-level assessment and symptom management. Visit duration is guided by patient needs, supported by documentation and quality review rather than rigid time thresholds."

---

## 10. Governance

- This document is **additive**
- No existing files are modified by this plan
- Any future implementation MUST reference this file
- Conflicts default to `core_rules.md`

---

**Purpose:**
Protect patients. Protect staff. Protect the organization.

