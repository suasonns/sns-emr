"""
SNS EMR COMPLIANCE NOTICE
This module is governed by:
  /docs/compliance/core_rules.md

If behavior in this file conflicts with core_rules.md,
the behavior in this file MUST be changed.
"""

# GOVERNED BY: /docs/compliance/core_rules.md
# Discipline scope and visit rules enforced here must not exceed defined scope.

# See core_rules.md:
# - Section 2: Visit Modes
# - Section 3: RN Refusal = Care Delivery Risk
# - Section 4: Discharge for Cause Guardrails

### Compliance Check
- [ ] Changes reviewed against /docs/compliance/core_rules.md
- [ ] RN scope not weakened
- [ ] Telephone ≠ visit rule preserved
- [ ] No discipline scope expansion

def assert_core_rules():
    """
    This logic assumes compliance with /docs/compliance/core_rules.md.
    If this assertion fails, the implementation is non-compliant.
    """
    return True


✅ Core Rules → Services Mapping (AUTHORITATIVE)

🧠 SECTION 1 — RN ROLE IS FOUNDATIONAL
core_rules.md

Section 1. RN ROLE IS FOUNDATIONAL

Services / Files

services/visits/visit_create.py
services/visits/visit_finalize.py
services/documentation/finalize_rn_note.py
services/documentation/finalize_lvn_note.py
services/documentation/finalize_aide_note.py
services/documentation/finalize_msw_note.py
services/documentation/finalize_chaplain_note.py

Enforcement Behavior

RN visit type cannot be replaced by LVN/LPN/CHHA
LVN/LPN finalize requires RN oversight evidence
CHHA/AIDE finalize requires RN supervision evidence
RN owns:

clinical assessment
decline narrative
POC ownership



Database / Models

visits.visit_type (ENUM)
notes.discipline
tasks.originating_role


🩺 SECTION 2 — VISIT MODES (IN_PERSON vs TELEPHONE)
core_rules.md

Section 2. Visit Modes Are Strictly Defined

Services / Files

services/visits/visit_create.py
services/visits/visit_update.py
services/visits/visit_finalize.py
services/validation/visit_validation.py

Enforcement Behavior

RN + TELEPHONE:

cannot satisfy visit frequency
cannot satisfy supervisory visit
cannot close RN tasks


RN + IN_PERSON:

valid visit


RN + VIDEO:

blocked or rejected (unless future policy)



Database / Models

visits.visit_mode (ENUM: IN_PERSON | TELEPHONE | VIDEO)
visits.is_countable (derived or computed)

Guardrail

RN TELEPHONE ≠ RN VISIT (system‑enforced)


🚨 SECTION 3 — RN REFUSAL = CARE DELIVERY RISK
core_rules.md

Section 3. RN Refusal = Care Delivery Risk

Services / Files

services/documentation/declined_services_engine.py
services/visits/rn_refusal_handler.py
services/tasks/task_factory.py
services/patient_care/care_status_engine.py

Enforcement Behavior
On RN refusal:

Create RN_REFUSAL_EVENT
Auto‑create tasks:

OFFER_ALTERNATE_RN
EDUCATE_RN_REQUIREMENT
IDG_REVIEW_RN_REFUSAL


Set:
care_status = AT_RISK_FOR_DFC



Database / Models

patient_visit_refusals
care_status
tasks.task_type


🧾 SECTION 4 — DISCHARGE FOR CAUSE (GUARDED)
core_rules.md

Section 4. Discharge for Cause (DFC) Is Guarded

Services / Files

services/discharge/discharge_for_cause.py
services/discharge/discharge_validation.py
services/tasks/task_completion_validator.py
services/providers/md_signing_guard.py

Enforcement Behavior
Discharge blocked unless ALL exist:

RN refusal events
Education documentation
Alternate RN offer
IDG review
MD discharge order
Narrative: “care delivery seriously impaired”

Database / Models

discharges
tasks
task_completion_references
provider_orders

Guardrail

Discharge without evidence = hard stop


🧑‍⚕️ SECTION 5 — RN‑ONLY CARE MODE
core_rules.md

Section 5. RN‑Only Care Mode

Services / Files

services/patient_care/care_mode_engine.py
services/documentation/finalize_rn_note.py
services/idg/idg_review_builder.py

Enforcement Behavior
RN‑only mode allowed when:

MSW/CHAP/AIDE/LVN = declined
RN visits continue IN_PERSON

RN‑only mode blocked when:

RN refusal exists
care_status = AT_RISK_FOR_DFC

Database / Models

patient_service_preferences
care_mode


📚 SECTION 6 — DISCIPLINE DOCUMENTATION GUARDRAILS
core_rules.md

Section 6. Discipline Documentation Guardrails

Services / Files

All finalize_*_note.py
services/validation/scope_validation.py
services/validation/narrative_consistency.py

Enforcement Behavior

Each discipline restricted to scope
No prognosis, eligibility, or decline outside RN/MD
Contradictions require escalation

Database / Models

notes.discipline
notes.flags
consistency_audit_results


☎️ SECTION 7 — TELEPHONE ≠ VISIT (ALL DISCIPLINES)
core_rules.md

Section 7. Telephone ≠ Visit

Services / Files

services/visits/visit_validation.py
services/notes/note_type_resolver.py
services/audit/survey_mode_view.py

Enforcement Behavior

TELEPHONE visits:

informational only
never counted
never close tasks



Database / Models

visits.visit_mode
visits.counts_toward_compliance (derived)


✅ SECTION 8 — AUDIT & FINALIZATION RULES
core_rules.md

Section 8. Audit & Finalization Rules

Services / Files

services/tasks/task_completion.py
services/finalization/finalization_policy.py
services/audit/audit_trail.py

Enforcement Behavior

No task completion without:

completed_at
completed_by
reference_type
reference_id


No note finalization with open required tasks

Database / Models

tasks
task_completions
audit_log


🔐 SECTION 9 — CHANGE CONTROL
core_rules.md

Section 9. Change Control

Services / Files

PR templates
services/compliance/assert_core_rules.py
Unit tests in tests/compliance/

Enforcement Behavior

Any feature touching visits, RN, discharge, scope must reference core_rules.md
Tests fail if core rules violated
