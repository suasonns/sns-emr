# SNS Action Center Trigger Inventory 1.0 — Phase 1, Deliverable 7

**STATUS: FROZEN — ACCEPTED COMPLETE (2026-08-21)**
No further edits except factual corrections.

> **HOPE GOVERNANCE RULE**
>
> RNICA is the authoritative assessment. HOPE is not a separate
> clinician-facing form. All HOPE reporting elements originate from
> RNICA fields through approved mapping, derivation, and validation
> rules. No duplicate clinician documentation shall be required solely
> for HOPE reporting.

## INVENTORY RULE

This document records workflow-automation triggers as they actually
exist in the current codebase. It does not modify any prior frozen
deliverable and does not propose new automation.

Source of truth: `backend/app/api/visits.py` (full file, checked for
every call site of `Task(...)`, `_safe_log_event(...)`,
`record_refusal(...)`, `_run_bereavement_aggregation_non_blocking(...)`,
against the exact line ranges of the RNICA route handlers, lines
751-1027); `backend/app/services/dynamic_condition_detection_engine.py`,
`refusal_engine.py`, `bereavement_aggregation_engine.py`. Frontend
searched for an "Action Center" concept tied to RNICA
(`sns-emr-frontend/src`) — no match found.

## Key finding

**No automated task, alert, or escalation is created by any RNICA
endpoint in the current implementation.** `visits.py` does contain a
Task-creation call site (`Task(...)`, line 2493), calls into
`record_refusal()` (line 4031), and a bereavement-aggregation trigger
(`_run_bereavement_aggregation_non_blocking`, line 4656) — but every one
of these sits well outside the RNICA handler range
(`save_rnica_assessment` 751-795, `update_rnica_assessment` 930-975,
`lock_rnica_assessment` 978-999, `get_rnica_intelligence` 1002-1027).
None of `dynamic_condition_detection_engine`,
`bereavement_aggregation_engine`, or `refusal_engine` — despite being
imported at the top of `visits.py` (lines 71-79) — are invoked from
inside any RNICA route. They are used by other assessment types/visit
flows in the same file, not by RNICA.

Consequently, this inventory has **no positive rows to report** for a
"Trigger → Task Created / Alert Created / Escalation Rule" mapping,
because none of the triggers described in the example scenarios the
project has referenced previously (e.g. "Dyspnea → Oxygen Request,"
"Pain Crisis → Physician Contact," "Pressure Injury → Wound Supplies")
exist as implemented code paths today. The table below documents the
**absence** explicitly, field by field, rather than fabricating
triggers that are not present.

## Trigger inventory (current implementation)

| Trigger (candidate source field) | Source Field | Task Created | Alert Created | Escalation Rule | Dependency | Automation Target | Status |
|---|---|---|---|---|---|---|---|
| Dyspnea / respiratory distress | `symptomImpact.shortnessOfBreath`, `respiratory.*` | None | None | None | — | — | **Not implemented** |
| Pain crisis | `pain.*`, `symptomImpact.pain` | None | None | None | — | — | **Not implemented** |
| Pressure injury / skin breakdown | `skin.*` | None | None | None | — | — | **Not implemented** |
| Imminent death indicator | `imminentDeath.appearsThreeDaysOrLess` | None | None | None | — | — | **Not implemented** (field is validated as a HOPE warning only — see `SNS_RNICA_VALIDATION_INVENTORY_1.0`; no downstream action fires) |
| Code status change | `demographics.advancedCarePlanning.codeStatus` | None (sync writes to `patient_code_statuses`, but no Task/alert) | None | None | `set_current_code_status()` (data sync only, see `SNS_RNICA_DATABASE_MAPPING_1.0` §3.3) | `patient_code_statuses` row | Data sync exists; workflow automation does not |
| Level of care change | `admissionsOrder.levelOfCare.level` | None | None | None | direct write to `patient_facesheets.current_level_of_care` (see Database Mapping §3.5) | `patient_facesheets` row | Data sync exists; workflow automation does not |
| Diagnosis added/changed | `diagnoses.primaryDiagnosis`, `.secondaryDiagnoses[]`, `.comorbidities[]` | None | None | None | `sync_official_primary_diagnosis()`, `sync_secondary_and_comorbidity_diagnoses()` | `patient_diagnoses` rows | Data sync exists; workflow automation does not |
| Allergy added | `infection.allergies[]` | None | None | None | `sync_allergies_from_source()` | `patient_allergies` rows | Data sync exists; workflow automation does not |
| Braden Scale threshold | `skin.braden.total` | None | None | None | — | — | Frontend validation warning only (see Validation Inventory); no Task/alert |
| POC generation flag | `finalization.pocGenerationCompleted` | None | None | None | — | — | Manual checkbox only; no automated POC creation is triggered by it (see Deliverable #8) |
| Assessment locked/finalized | (the lock action itself) | None | None | None | — | — | `lock_rnica_assessment` performs only `locked`/`status`/`locked_at` writes (see Audit Inventory §"Finalize / Lock") |

## Automation infrastructure that exists in the codebase but is not reachable from RNICA

| Engine/Function | File | What it does | Why it's excluded here |
|---|---|---|---|
| `Task(...)` model instantiation | `visits.py:2493` | Creates a `Task` row | Call site is inside a different endpoint (not in the 751-1027 RNICA range) |
| `record_refusal()` | `refusal_engine.py`, called at `visits.py:4031` | Records a refusal-of-care event | Call site is inside a different endpoint |
| `_run_bereavement_aggregation_non_blocking()` | `visits.py:2651`, called at `4656` | Triggers bereavement-related aggregation | Call site is inside a different endpoint |
| `dynamic_condition_detection_engine` | imported `visits.py:75-78` | Condition-detection logic | Imported but never called anywhere in the RNICA handler bodies |

These exist and are real, working automation for *other* parts of the
system (other assessment/visit endpoints in the same file) — they are
listed here only to make clear that their presence in `visits.py`'s
import block does not mean RNICA uses them.

## HOPE-derived-finding triggers (explicit check requested)

Checked specifically: does any HOPE-derived finding (a validation
warning/error tagged with a HOPE item number, or a value read out of
`form_data` for HOPE purposes) trigger a Task, alert, or escalation?
**No.** The 13 HOPE-tagged validation rules in
`SNS_RNICA_VALIDATION_INVENTORY_1.0` (A1005, A1010, A1110, F2000, F2100,
F2200, I0010, J0050, J0900, J0915, J2051 A-H, M1190, N0500) produce only
in-memory `errors`/`warnings` objects rendered in the UI — none of them
triggers a `Task`, notification, or escalation in the backend. The J2051
HOPE item does drive a real downstream trigger, but not from RNICA
directly: per prior codebase research recorded in
`SNS_RNICA_SECTION_INVENTORY_1.0` ("HOPE Crosswalk" section), the SFV
(J2052/J2053) trigger engine (`hope_phase_b_engine.py:319-394`) reads
J2051-equivalent symptom-impact values from **`clinical_notes`**, not
from `rnica_assessments.form_data.symptomImpact` — so saving/locking an
RNICA assessment alone does not fire the SFV requirement; a separate
clinical note must exist. This is the one HOPE-adjacent automation that
does exist in the codebase, and it is documented here precisely because
it is NOT reachable directly from an RNICA save/update/lock call.

## Status

**Deliverable #7 (`SNS_ACTION_CENTER_TRIGGER_INVENTORY_1.0`) complete.**
Every previously-discussed example trigger (dyspnea, pain crisis,
pressure injury, imminent death, code status, level of care, diagnosis,
allergy, Braden, POC flag, lock/finalize) was checked directly against
the RNICA route handlers and confirmed to have **no** Task creation,
alert creation, or escalation logic attached in the current
implementation. The only real automation reachable from RNICA save/
update is the data-synchronization set already documented in
`SNS_RNICA_DATABASE_MAPPING_1.0` and `SNS_RNICA_API_MAPPING_1.0` — none
of which create a Task, notification, or Action Center-style item.

No changes made to any frozen artifact. No code changes are authorized
by this document.

Next: Deliverable #8 — `SNS_POC_EVIDENCE_INVENTORY_1.0`.
