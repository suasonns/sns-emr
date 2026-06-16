CORE RULES → SERVICES MAPPING (AUTHORITATIVE)
This section maps rules to code locations.
Rules themselves live ONLY in core_rules.md.

SECTION 1 — RN ROLE IS FOUNDATIONAL
(core_rules.md §1)
Services / Files

services/visits/visit_create.py
services/visits/visit_finalize.py
services/documentation/finalize_rn_note.py
services/documentation/finalize_lvn_note.py
services/documentation/finalize_aide_note.py
services/documentation/finalize_msw_note.py
services/documentation/finalize_chaplain_note.py

Enforcement

RN visit type cannot be replaced by LVN/LPN/CHHA
LVN/LPN finalize requires RN oversight evidence
CHHA/AIDE finalize requires RN supervision evidence
RN owns:

clinical assessment
decline narrative
Plan of Care ownership



Models

visits.visit_type
notes.discipline
tasks.originating_role


SECTION 2 — VISIT MODES (IN_PERSON ≠ TELEPHONE)
(core_rules.md §2)
Services / Files

services/visits/visit_create.py
services/visits/visit_update.py
services/visits/visit_finalize.py
services/validation/visit_validation.py

Enforcement

TELEPHONE:

informational only
never counted
never closes tasks


IN_PERSON:

valid visit


VIDEO:

blocked unless explicitly enabled later



Models

visits.visit_mode
visits.counts_toward_compliance (derived)


SECTION 3 — RN REFUSAL = CARE DELIVERY RISK
(core_rules.md §3)
Services / Files

services/documentation/declined_services_engine.py
services/visits/rn_refusal_handler.py
services/tasks/task_factory.py
services/patient_care/care_status_engine.py

Enforcement

RN refusal creates RN_REFUSAL_EVENT
Auto‑create tasks:

OFFER_ALTERNATE_RN
EDUCATE_RN_REQUIREMENT
IDG_REVIEW_RN_REFUSAL


Set:

care_status = AT_RISK_FOR_DFC




SECTION 4 — DISCHARGE FOR CAUSE (GUARDED)
(core_rules.md §4)
Services / Files

services/discharge/discharge_for_cause.py
services/discharge/discharge_validation.py
services/tasks/task_completion_validator.py
services/providers/md_signing_guard.py

Enforcement
Discharge blocked unless ALL exist:

RN refusal events
Education documentation
Alternate RN offer
IDG review
MD discharge order
Narrative: “care delivery seriously impaired”

Guardrail: discharge without evidence = hard stop

SECTION 5 — RN‑ONLY CARE MODE
(core_rules.md §5)
Services / Files

services/patient_care/care_mode_engine.py
services/documentation/finalize_rn_note.py
services/idg/idg_review_builder.py

Enforcement

RN‑only mode allowed when:

non‑RN disciplines declined


RN‑only mode blocked when:

RN refusal exists
care_status = AT_RISK_FOR_DFC




SECTION 6 — DISCIPLINE DOCUMENTATION GUARDRAILS
(core_rules.md §6)
Services / Files

services/documentation/finalize_*_note.py
services/validation/scope_validation.py
services/validation/narrative_consistency.py

Enforcement

Scope restricted per discipline
No prognosis, eligibility, or decline outside RN/MD
Contradictions require escalation


SECTION 7 — TELEPHONE ≠ VISIT (ALL DISCIPLINES)
(core_rules.md §7)
Services / Files

services/visits/visit_validation.py
services/notes/note_type_resolver.py
services/audit/survey_mode_view.py

Enforcement

TELEPHONE is never counted
TELEPHONE never closes tasks


SECTION 8 — AUDIT & FINALIZATION
(core_rules.md §8)
Services / Files

services/tasks/task_completion.py
services/finalization/finalization_policy.py
services/audit/audit_trail.py

Enforcement

No task completion without:

completed_at
completed_by
reference_type
reference_id


No note finalization with open required tasks


SECTION 9 — CHANGE CONTROL
(core_rules.md §9)
Services / Files

PR templates
services/compliance/assert_core_rules.py
tests/compliance/

Enforcement
Any feature touching:

visits
RN logic
discharge
discipline scope

MUST reference core_rules.md.
Tests must fail if core rules are violated.