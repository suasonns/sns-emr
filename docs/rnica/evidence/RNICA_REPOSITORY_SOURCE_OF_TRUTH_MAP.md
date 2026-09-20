# RNICA Repository Source-of-Truth Map

## Amendment Log

### Amendment 1 (post-review correction)

A subsequent verification pass required by the BUILD_NOW-001 findings review discovered `backend/app/domain/forms/form_registry.py`, which was not identified in the original discovery pass. This file contains:

- `HOPE_SYMPTOM_ITEM_CODES` and `HOPE_SFV_ITEM_CODES`, which include `J2050`, `J2051A`–`J2051H`, `J2052`, and `J2053` as named HOPE form item codes.
- `WORKFLOW_TRIGGER_REGISTRY`, a structured, authoritative registry defining `TRIGGER_HUV1`, `TRIGGER_HUV2`, and `TRIGGER_SFV` rules, each with `allowed_disciplines`, day windows (HUV1: days 6–15, HUV2: days 16–30), and source/completion HOPE item codes for SFV (`source_items`: `J2051A`–`H`; `completion_items`: `J2052`, `J2053`).

**Correction**: The original Summary Table classified `J2050`, `J2052`, and `J2053` as `NOT_FOUND` and `J2051` as `UNRESOLVED`. This was incorrect — all of these exist as named HOPE item codes in the backend. `J2050B` remains correctly classified as `NOT_FOUND` (no match found anywhere, including in `form_registry.py`). The HUV1/HUV2 findings are also updated: the trigger *rule* (day window, allowed discipline, item codes) is authoritatively modeled in `form_registry.py`, even though no dedicated HUV1/HUV2 clinical-record entity exists.

**New finding requiring review (not resolved here)**: `WORKFLOW_TRIGGER_REGISTRY[TRIGGER_SFV]["allowed_disciplines"]` is `{"RN", "LVN"}` — i.e., the repository's SFV trigger rule currently permits both RN and LVN to satisfy an SFV trigger. This is directly relevant to the frozen SFV/LVN escalation authority and must be compared against that authority document before any conclusion is drawn. See MAP-C02 below.

Corrected rows are marked inline. The Final Report counts at the end of this document reflect the correction.

## Purpose

Evidence-backed map of the current repository (`suasonns/sns-emr`, branch `main` at commit `c6889c4`) for concepts relevant to RNICA, HOPE, HUV, and SFV. This document is discovery only. It does not authorize, propose, or design any application, schema, or migration change.

## Scope Discipline

- This document contains repository evidence only.
- It does not rewrite any authority rule.
- It does not establish new clinical policy.
- It does not resolve any unresolved CMS issue.
- It does not authorize implementation.
- Findings marked `NOT_FOUND` are not assumptions of future design; they record only that no such structure currently exists.

## Related Records

- Issue #121 — SFV Source Validation and Evidence Tracker
- Issue #124 — Pre-Development Review and Development Kickoff (`APPROVED_FOR_BUILD_NOW_001`)
- Issue #125 — `BUILD_NOW-001`: Read-Only RNICA, HOPE, HUV, and SFV Repository Mapping
- `docs/rnica/RNICA_DOCUMENT_FREEZE_AND_SOURCE_CHANGE_CONTROL.md`

Allowed finding values: `VERIFIED`, `NOT_FOUND`, `UNRESOLVED`, `DUPLICATE_SOURCE`, `CONFLICT`.

---

## Summary Table

| Area | Repository Path | Entity | Source of Truth | Finding |
|---|---|---|---|---|
| Patient | `backend/app/models/patient.py` | `Patient` (`patients` table) | Authoritative patient record | `VERIFIED` |
| Admission | `backend/app/models/admission.py` | `Admission` (`admissions` table) | Authoritative admission record | `VERIFIED` |
| Episode of care | — | — | No distinct episode-of-care entity; `Admission` functions as the episode boundary | `NOT_FOUND` |
| Benefit Period | `backend/app/models/benefit_period.py` | `BenefitPeriod` (`benefit_periods` table) | Authoritative benefit-period record | `VERIFIED` |
| Visit | `backend/app/models/visit.py` | `Visit` (`visits` table) | Authoritative visit record | `VERIFIED` |
| Schedule | — | — | No distinct `Schedule` entity/table found | `NOT_FOUND` |
| Visit Type | `backend/app/core/visit_types.py` | `CANONICAL_VISIT_TYPES`, `normalize_visit_type()` | Code-level normalization list, not a DB enum | `VERIFIED` |
| Discipline (visit) | `backend/app/core/visit_types.py` | `ALLOWED_VISIT_SERVICES` | Visit-level discipline/service normalization | `VERIFIED` |
| Discipline (clinician) | `backend/app/models/user.py` | `User.discipline`, `User.role` | Free-text `String(50)` column, not a DB enum | `VERIFIED` |
| RNICA (RN Initial Comprehensive Assessment) | `backend/app/models/rnica_assessment.py` | `RnicaAssessment` (`rnica_assessments` table) | Authoritative RNICA record | `VERIFIED` |
| MSW ICA | `backend/app/models/msw_ica_assessment.py` | `MswIcaAssessment` (`msw_ica_assessments` table) | Authoritative MSW Initial Comprehensive Assessment record | `VERIFIED` |
| SC ICA | `backend/app/models/scica_assessment.py` | `ScicaAssessment` (`scica_assessments` table) | Authoritative Spiritual Care Initial Comprehensive Assessment record | `VERIFIED` |
| Updated Comprehensive Assessment (UCA) | `backend/app/models/rn_recert_assessment.py` | `RNRecertAssessment` (`rn_recert_assessments` table) | Closest existing analog is the recertification assessment (`form_type="RECERT"`); no entity literally named "Updated Comprehensive Assessment" | `UNRESOLVED` |
| Assessment finalization (RNICA) | `backend/app/models/rnica_assessment.py` | `RnicaAssessment.locked`, `.locked_at`, `.status`, `.hope_workflow_status` | Locking/finalization fields on the assessment row | `VERIFIED` |
| Assessment amendment (RNICA) | `backend/app/models/rnica_amendment.py` | `RnicaAmendment` (`rnica_amendments` table) | Distinct append-only amendment record referencing `rnica_assessment_id`; never overwrites the locked assessment | `VERIFIED` |
| Assessment correction (generic clinical note) | `backend/app/models/amendment.py` | `Amendment` (`amendments` table) | Generic correction/amendment record tied to `clinical_note_id`, separate from `RnicaAmendment` | `VERIFIED` / `DUPLICATE_SOURCE` (two separate amendment mechanisms exist: `Amendment` for clinical notes, `RnicaAmendment` for RNICA) |
| HOPE Admission | — | — | No distinct `HopeAdmission` model; HOPE Admission workflow state is carried on `RnicaAssessment` itself via `hope_workflow_status`, `hope_closed_at`, `hope_ready_at`, `hope_submitted_at`, `hope_inactivated`, etc. | `UNRESOLVED` |
| HUV1 | `backend/app/domain/forms/form_registry.py` (`WORKFLOW_TRIGGER_REGISTRY[TRIGGER_HUV1]`); also `backend/app/models/enums.py` (`TaskType.HUV1`), `backend/app/services/hope_phase_b_engine.py` | Structured trigger rule (`allowed_disciplines={"RN"}`, `window_start_day=6`, `window_end_day=15`, `hope_item_codes=HOPE_HUV_ITEM_CODES`); also a `Task` type and a `trigger_source_type` string on `SFVRequirement` | The trigger *rule* is authoritatively modeled in `form_registry.py`; no dedicated HUV1 clinical-record/table exists — updated finding (correction — see Amendment 1 below) | `VERIFIED` (rule definition) / `NOT_FOUND` (dedicated record) |
| HUV2 | `backend/app/domain/forms/form_registry.py` (`WORKFLOW_TRIGGER_REGISTRY[TRIGGER_HUV2]`); also `backend/app/models/enums.py` (`TaskType.HUV2`), `backend/app/services/hope_phase_b_engine.py` | Structured trigger rule (`allowed_disciplines={"RN"}`, `window_start_day=16`, `window_end_day=30`, `hope_item_codes=HOPE_HUV_ITEM_CODES`) | Same pattern as HUV1 — updated finding (correction — see Amendment 1 below) | `VERIFIED` (rule definition) / `NOT_FOUND` (dedicated record) |
| SFV | `backend/app/models/sfv_requirement.py` | `SFVRequirement` (`sfv_requirements` table) | Authoritative SFV requirement/tracking record, linked to a `completed_visit_id` | `VERIFIED` |
| Workflow trigger registry (HUV1/HUV2/SFV) | `backend/app/domain/forms/form_registry.py` | `WORKFLOW_TRIGGER_REGISTRY` (`TRIGGER_HUV1`, `TRIGGER_HUV2`, `TRIGGER_SFV` keys) | Authoritative, structured trigger-rule source: day windows, allowed disciplines, and source/completion HOPE item codes for HUV1/HUV2/SFV, distinct from the runtime logic in `hope_phase_b_engine.py` | `VERIFIED` (correction — see Amendment 1 below) |
| J2050 | `backend/app/domain/forms/form_registry.py` | `HOPE_SYMPTOM_ITEM_CODES` list entry `"J2050"` | Exists as a HOPE form item code (symptom family) | `VERIFIED` (correction — see Amendment 1 below) |
| J2050B | — | — | Not found as a code identifier anywhere in the repository | `NOT_FOUND` (re-confirmed) |
| J2051 (J2051A–J2051H) | `backend/app/domain/forms/form_registry.py`; also `backend/app/services/hope_phase_b_engine.py`, `backend/app/api/visits.py` | `HOPE_SYMPTOM_ITEM_CODES`/`TRIGGER_SFV["metadata"]["source_items"]` list entries `"J2051A"`–`"J2051H"`; also `j2051_pain_impact`/`j2051_non_pain_impact` function parameters at runtime | Exists as 8 named HOPE form item codes, used as the SFV trigger `source_items`; the `j2051_*` function parameters are a runtime derivation from these items, not the underlying source | `VERIFIED` (correction — see Amendment 1 below) |
| J2052 | `backend/app/domain/forms/form_registry.py` | `HOPE_SFV_ITEM_CODES` list entry `"J2052"`, also `TRIGGER_SFV["metadata"]["completion_items"]` | Exists as a HOPE form item code and as one of the two SFV completion items | `VERIFIED` (correction — see Amendment 1 below) |
| J2053 | `backend/app/domain/forms/form_registry.py` | `HOPE_SFV_ITEM_CODES` list entry `"J2053"`, also `TRIGGER_SFV["metadata"]["completion_items"]` | Exists as a HOPE form item code and as one of the two SFV completion items | `VERIFIED` (correction — see Amendment 1 below) |
| User (authenticated identity) | `backend/app/models/user.py` | `User` (`users` table) | Authoritative user/identity record | `VERIFIED` |
| Role | `backend/app/models/user.py` (`User.role`), `backend/app/models/role.py` (`Role`) | Two separate representations | `User.role` is a free-text string used for functional/permission role; `Role` (`roles` table) is a separate, `interface_id`-scoped entity | `UNRESOLVED` / `DUPLICATE_SOURCE` |
| Credential | `backend/app/models/user.py` | `User.license_number`, `User.npi` | Credential fields live directly on `User`; no separate credential/license-tracking table found for expiration or verification state | `UNRESOLVED` |
| Discipline source (identity) | `backend/app/models/user.py` | `User.discipline` | Free-text field, distinct from visit-level discipline in `visit_types.py` | `VERIFIED` (see also Discipline/visit conflict note below) |
| Permissions | `backend/app/models/staff_permission_grant.py` | `StaffPermissionGrant` (`staff_permission_grants` table) | Delegated capability grants layered on top of role defaults (`app.core.roles`) | `VERIFIED` |
| CreatedBy / CreatedAt | Multiple models (e.g. `patient.py`, `admission.py`, `benefit_period.py`) | `created_by`, `created_at` columns | Present on most core clinical/administrative tables | `VERIFIED` |
| ModifiedBy / ModifiedAt | Multiple models (e.g. `patient.py` `updated_by`/`updated_at`) | `updated_by`, `updated_at` columns | Present on most core tables; naming varies (`updated_by` vs. `modified_by` not standardized) | `VERIFIED` / `UNRESOLVED` (naming inconsistency) |
| Audit trail (generic) | `backend/app/models/audit_log.py` | `AuditLog` (`audit_logs` table) | Generic, tenant-scoped audit-event log capturing actor, action, entity type/id, and structured metadata | `VERIFIED` |
| Correction history (RNICA) | `backend/app/models/rnica_amendment.py` | `RnicaAmendment.original_value_snapshot`, `.proposed_value` | Point-in-time snapshot plus proposed replacement value; never auto-applied | `VERIFIED` |
| Amendment history (clinical notes) | `backend/app/models/amendment.py` | `Amendment` (`amendments` table) | Generic amendment record for `clinical_notes`; separate mechanism from `RnicaAmendment` | `VERIFIED` |
| Version history (Plan of Care) | `backend/app/models/plan_of_care_version.py` | `PlanOfCareVersion` (`plan_of_care_versions` table) | Versioned, append-only Plan of Care history with `based_on_version_id` lineage and `status` (`DRAFT`/`ACTIVE`/`FINALIZED`/`SUPERSEDED`) | `VERIFIED` |
| Version history (RNICA/assessments) | — | — | No dedicated version-history table for `rnica_assessments`, `msw_ica_assessments`, or `scica_assessments`; only the amendment tables above provide post-lock traceability | `NOT_FOUND` |

---

## Detailed Findings by Domain

### A. Patient, Admission, and Episode

- **Patient**: `backend/app/models/patient.py` — `Patient` / `patients`. Fields include `mrn`, `date_of_birth`, `hospice_election_date`, `discharge_date`, `admission_status`, `created_by`/`created_at`, `updated_by`/`updated_at`, `deleted_at`.
- **Admission**: `backend/app/models/admission.py` — `Admission` / `admissions`. Fields include `admission_date`, `status`, `soc_date`, `soc_time`, `effective_date`, `election_signed_at`, `certification_completed_at`, `physician_order_signed_at`, `initial_assessment_completed_at`, `discharged_at`, `discharge_reason`.
- **Episode of care**: `NOT_FOUND` as a distinct entity. `Admission` appears to serve this role (one admission per episode); no separate `episode` table or model exists.
- **Admission status history**: `backend/app/models/admission_status_history.py` — tracks status transitions for an `Admission` (imported by `patient.py`).
- **Duplicate/conflicting date fields**: `Patient.hospice_election_date`/`Patient.discharge_date` overlap conceptually with `Admission.election_signed_at`/`Admission.discharged_at`/`Admission.soc_date`. Both models carry admission-adjacent dates independently — flagged `CONFLICT` candidate for source-change review, not resolved here.

### B. Benefit Period

- `backend/app/models/benefit_period.py` — `BenefitPeriod` / `benefit_periods`. Fields: `benefit_type` (`INITIAL`/`RECERT` enum), `period_number`, `election_date`, `start_date`, `end_date`, `is_current`, `noe_submitted_date`, `noe_exception_reason`.
- Related: `backend/app/models/benefit_period_status_event.py` (status-event history), `backend/app/services/benefit_period_service.py`, `backend/app/services/benefit_period_resolver.py`, `backend/app/services/benefit_periods.py`.
- Recertification linkage: `backend/app/models/rn_recert_assessment.py` references `benefit_period_id`.

### C. Visits and Schedules

- `backend/app/models/visit.py` — `Visit` / `visits`. Fields include `visit_type`, `visit_mode`, `visit_datetime`, `provider_id`, `admission_id`, `patient_id`, `status`.
- **Schedule (visit)**: `NOT_FOUND` — no `class Schedule` or `schedules` table exists in `backend/app/models/`. Note: `backend/app/api/idg/router.py` defines `ScheduleRuleCreateRequest` (`weekday`, `nth_occurrences`), but this is an IDG meeting-cadence rule, not a visit-scheduling entity — confirmed unrelated to this finding on re-verification.
- **Visit type / discipline normalization**: `backend/app/core/visit_types.py` — `CANONICAL_VISIT_TYPES` (`RN`, `LVN`, `NP`, `MD`, `SW`, `CHAPLAIN`, `CHHA`, `VOLUNTEER`), `VISIT_TYPE_ALIASES`, `ALLOWED_VISIT_SERVICES`. This is code-level normalization, not a Postgres enum.
- **Core discipline standard**: `backend/app/models/enums.py` — `CORE_DISCIPLINES = ["RN", "MD", "MSW", "SC"]`, explicitly documented as the only disciplines used for IDG completeness, signature validation, task routing, and compliance logic. This is a narrower list than `CANONICAL_VISIT_TYPES` — flagged `UNRESOLVED` (two discipline vocabularies exist for different purposes).

### D. Assessments

- **RNICA**: `backend/app/models/rnica_assessment.py` — `RnicaAssessment` / `rnica_assessments`. `assessment_type` defaults to `"RNICA"`. Scoped to `admission_id` (one RNICA per admission, enforced in `app/api/visits.py`).
- **MSW ICA**: `backend/app/models/msw_ica_assessment.py` — `MswIcaAssessment` / `msw_ica_assessments`. `assessment_type` defaults to `"MSWICA"`.
- **SC ICA**: `backend/app/models/scica_assessment.py` — `ScicaAssessment` / `scica_assessments`. `assessment_type` defaults to `"SCICA"`.
- **Recertification / Updated Comprehensive Assessment**: `backend/app/models/rn_recert_assessment.py` — `RNRecertAssessment` / `rn_recert_assessments`. `form_type` defaults to `"RECERT"`; no entity is literally named "Updated Comprehensive Assessment" — flagged `UNRESOLVED`.
- **Finalization**: RNICA/MSW ICA/SC ICA each carry `status`, `locked`, `locked_at` on the assessment row itself (`rnica_assessment.py`, `msw_ica_assessment.py`, `scica_assessment.py`).
- **Amendment (RNICA-specific)**: `backend/app/models/rnica_amendment.py` — `RnicaAmendment` / `rnica_amendments`. Distinct, append-only, references `rnica_assessment_id`; documented as "NEVER overwrites" the signed record.
- **Amendment (generic clinical note)**: `backend/app/models/amendment.py` — `Amendment` / `amendments`. References `clinical_note_id`, separate mechanism from `RnicaAmendment`.
- **Plan-of-Care links**: `backend/app/models/plan_of_care_version.py` — `PlanOfCareVersion.source_kind` includes `"ICA"` as a valid origin, connecting assessment completion to Plan-of-Care versioning.

### E. HOPE and SFV

- **HOPE Admission**: `NOT_FOUND` as a distinct model. HOPE workflow state (`hope_workflow_status`, `hope_closed_at`/`_by`, `hope_ready_at`/`_by`, `hope_exported_to_batch_at`/`_by`/`_batch_id`, `hope_submission_number`, `hope_already_submitted`, `hope_submitted_at`/`_by`, `hope_inactivated`/`_at`/`_by`, `hope_unlocked_at`/`_by`/`_reason`) is carried directly on `RnicaAssessment` (`backend/app/models/rnica_assessment.py`). Flagged `UNRESOLVED` — no separate HOPE Admission record exists apart from the RNICA row it is embedded in.
- **HUV1 / HUV2 trigger rules**: `VERIFIED` as structured rule definitions in `backend/app/domain/forms/form_registry.py` — `WORKFLOW_TRIGGER_REGISTRY[TRIGGER_HUV1]` / `[TRIGGER_HUV2]`, each with `allowed_disciplines={"RN"}`, `window_start_day`/`window_end_day` (6–15 / 16–30), and `hope_item_codes=HOPE_HUV_ITEM_CODES`. *(Corrected in Amendment 1 — this authoritative rule source was missed in the original pass.)* No dedicated HUV1/HUV2 clinical-record entity exists (`NOT_FOUND` for the record itself); the rule definitions also independently exist as:
  - `TaskType.HUV1` / `TaskType.HUV2` in `backend/app/models/enums.py`.
  - String literals `SOURCE_HUV1 = "HUV1"`, `SOURCE_HUV2 = "HUV2"`, `TASK_TYPE_HUV1`, `TASK_TYPE_HUV2` in `backend/app/services/hope_phase_b_engine.py`.
  - Allowed values for `SFVRequirement.trigger_source_type` (`CheckConstraint("trigger_source_type IN ('INITIAL_RN_ICA', 'HUV1', 'HUV2')")`) in `backend/app/models/sfv_requirement.py`.
  - Task-creation logic: `create_huv_tasks_from_initial_rn_ica()` in `hope_phase_b_engine.py` creates `Task` rows of type `HUV1`/`HUV2` with day-window escalation reasons ("HUV1 required on or between days 6 and 15", "HUV2 required on or between days 16 and 30"), consistent with the `form_registry.py` windows.
  - Completion validation: `validate_huv_visit_completion()` in `hope_phase_b_engine.py` enforces HUV1 must complete on days 6–15 and HUV2 on days 16–30, and that HUV visits must be completed by RN — consistent with `allowed_disciplines={"RN"}` in `form_registry.py`.
- **SFV**: `VERIFIED` — `backend/app/models/sfv_requirement.py` — `SFVRequirement` / `sfv_requirements`. Fields: `trigger_source_type`, `trigger_reference_id`, `trigger_symptom_group` (`PAIN`/`NON_PAIN`/`BOTH`), `trigger_datetime`, `due_at`, `completed_visit_id`, `completed_at`, `status` (`OPEN`/`COMPLETED`/`OVERDUE`/`CANCELLED`). A unique index (`uq_sfv_requirements_trigger_once`) prevents duplicate SFV requirements for the same `(patient_id, trigger_source_type, trigger_reference_id)`.
- **SFV trigger rule (structured)**: `VERIFIED` — `backend/app/domain/forms/form_registry.py` — `WORKFLOW_TRIGGER_REGISTRY[TRIGGER_SFV]`: `allowed_disciplines={"RN", "LVN"}`, `trigger_source="moderate_or_severe_symptom_impact"`, `must_be_separate_visit=True`, `due_within_calendar_days=2`, `source_items=["J2051A".."J2051H"]`, `completion_items=["J2052","J2053"]`. *(New finding, Amendment 1.)* **This is flagged as MAP-C02 below** — the repository currently permits LVN, not only RN, to satisfy an SFV trigger, which must be compared against the frozen SFV/LVN escalation authority before any conclusion is drawn.
- **SFV trigger/completion logic (runtime)**: `backend/app/services/hope_phase_b_engine.py` — `maybe_trigger_sfv_from_hope_timepoint()`, `_find_existing_sfv_requirement()`, `complete_sfv_requirement_from_visit()`, `process_initial_rn_ica_finalize()`, `process_huv_finalize()`. Enforces `trigger_source_type` must be one of `INITIAL_RN_ICA`, `HUV1`, `HUV2`, and that "SFV must be a separate visit from the triggering INITIAL_RN_ICA/HUV."
- **J2050 / J2050B / J2051 / J2052 / J2053** *(corrected in Amendment 1)*:
  - `J2050`: `VERIFIED` — exists in `HOPE_SYMPTOM_ITEM_CODES` in `backend/app/domain/forms/form_registry.py`.
  - `J2050B`: `NOT_FOUND` — re-confirmed absent from `form_registry.py` and the rest of the repository; only J2050 (no suffix) exists.
  - `J2051` (`J2051A`–`J2051H`): `VERIFIED` — exists as 8 named HOPE item codes in `HOPE_SYMPTOM_ITEM_CODES` and as `WORKFLOW_TRIGGER_REGISTRY[TRIGGER_SFV]["metadata"]["source_items"]` in `form_registry.py`. The previously-identified `j2051_pain_impact`/`j2051_non_pain_impact` function parameters in `hope_phase_b_engine.py`/`visits.py` are a runtime derivation from these items via `_extract_j2051_impacts_from_notes()`, not the underlying source; the exact JSONB storage key(s) within `RnicaAssessment.form_data` were still not exhaustively enumerated in this pass.
  - `J2052`, `J2053`: `VERIFIED` — exist in `HOPE_SFV_ITEM_CODES` and as `WORKFLOW_TRIGGER_REGISTRY[TRIGGER_SFV]["metadata"]["completion_items"]` in `form_registry.py`.
- **iQIES submission status**: `RnicaAssessment.hope_submission_number`, `.hope_already_submitted`, `.hope_submitted_at`/`_by` (see above). No separate iQIES-specific model or validation-result table found.
- **Validation errors/warnings**: `NOT_FOUND` as a dedicated structure for iQIES/HOPE validation results.

### F. Identity and Discipline

- **User**: `backend/app/models/user.py` — `User` / `users`. Fields include `email`, `role` (free-text), `license_number`, `npi`, `discipline` (free-text `String(50)`), `active`, `account_type`, `physician_id`, `physician_link_status`.
- **Role**: Two representations exist:
  - `User.role` — free-text string column used operationally for permission/role checks.
  - `backend/app/models/role.py` — `Role` / `roles`, `interface_id`-scoped, with `name`/`description`. Not clearly cross-referenced from `User` in the files reviewed. Flagged `UNRESOLVED`/`DUPLICATE_SOURCE`.
- **Credential**: `User.license_number`, `User.npi` on the `users` table directly. No separate license/credential-expiration-tracking table found (distinct from `backend/app/models/license_allocation.py`, which is a *seat allocation* table for subscription billing, not a clinical credential record). Flagged `UNRESOLVED`.
- **Permissions**: `backend/app/models/staff_permission_grant.py` — `StaffPermissionGrant` / `staff_permission_grants`. Delegated capability grants (`capability` string from `app.core.roles.STAFF_CAPABILITIES`), with `granted_by_user_id`, `revoked_at`, `revoke_reason` preserved as an audit trail (never deleted).
- **RN-only workflow checks**: Referenced in `hope_phase_b_engine.py` (`validate_huv_visit_completion` raises `"HUV must be completed by RN"`) — logic exists but the underlying identity/discipline check function was not traced to its source in this pass.
- **Audit linkage to authenticated user**: `created_by`/`updated_by` foreign keys to `users.id` are present on most core models (`Patient`, `Admission`, `BenefitPeriod`, `PlanOfCareVersion`, etc.).

### G. Audit and Record Integrity

- **Generic audit log**: `backend/app/models/audit_log.py` — `AuditLog` / `audit_logs`. Tenant-scoped; fields include `request_id`, `ip_address`, `user_id`, `role`, `action`, `entity_type`, `entity_id`, `description`, `event_metadata` (JSON, DB column `metadata`), `created_at`.
- **CreatedBy/CreatedAt**: Present on most models reviewed (`patient.py`, `admission.py`, `benefit_period.py`, `plan_of_care_version.py`, `rn_recert_assessment.py` as `created_by_user_id`).
- **ModifiedBy/ModifiedAt**: Present but naming is inconsistent — `Patient.updated_by`/`updated_at`, `PlanOfCareVersion.updated_by_user_id`/`updated_at`. No universal `modified_by` convention. Flagged `UNRESOLVED` (naming inconsistency, not a functional gap).
- **Original-value preservation / correction reason**: `RnicaAmendment.original_value_snapshot`, `.proposed_value`, `.reason_code`, `.requested_change`, `.decision_reason` (`backend/app/models/rnica_amendment.py`).
- **Correction-discovery date / correction date**: Not found as explicitly separate fields; `RnicaAmendment.created_at` (request) and `.decision_timestamp` (disposition) are the closest equivalents. Flagged `UNRESOLVED` — CDPH-style discovery-date/correction-date distinction not confirmed as separately tracked.
- **Addendum support**: `RnicaAmendment` serves this role for RNICA (append-only, never overwrites); `Amendment` (`amendments` table) serves the equivalent role for generic clinical notes.
- **Version history**: `backend/app/models/plan_of_care_version.py` — `PlanOfCareVersion` provides full version lineage (`based_on_version_id`, `version_number`, `status` enum `DRAFT`/`ACTIVE`/`FINALIZED`/`SUPERSEDED`) for Plan of Care only. No equivalent version-history table exists for `rnica_assessments`, `msw_ica_assessments`, or `scica_assessments` — those rely solely on the `locked`/`RnicaAmendment` pattern rather than full version snapshots. Flagged `NOT_FOUND` for assessment-level version history.
- **Finalized-record protection**: `RnicaAssessment.locked` / `locked_at` gates further direct edits; amendments are the only documented post-lock path (per code comment in `rnica_amendment.py`: "`rnica_assessments.form_data` for a locked assessment is never mutated by this workflow").
- **Silent-overwrite risk / wrong-patient correction / duplicate-record handling**: Not exhaustively traced in this pass; `SFVRequirement`'s unique index (`uq_sfv_requirements_trigger_once`) is the only explicit duplicate-prevention mechanism confirmed for the concepts in scope.

---

## Conflicts and Unresolved Items Requiring Issue #121 / Source-Change Review

| ID | Finding | Description | Next Action |
|---|---|---|---|
| MAP-C01 | `CONFLICT` (candidate) | `Patient` carries `hospice_election_date`/`discharge_date`; `Admission` independently carries `election_signed_at`/`discharged_at`/`soc_date`. Two models track overlapping hospice-lifecycle dates. | Add to Issue #121; do not resolve here. |
| MAP-C02 | `CONFLICT` (candidate, new — Amendment 1) | `backend/app/domain/forms/form_registry.py` — `WORKFLOW_TRIGGER_REGISTRY[TRIGGER_SFV]["allowed_disciplines"]` is `{"RN", "LVN"}`, meaning the repository's SFV trigger rule currently permits LVN, not only RN, to satisfy an SFV trigger. This must be compared against the frozen SFV/LVN escalation authority document before any conclusion is drawn. | Add to Issue #121 as high-priority; do not resolve or modify here; do not implement against this rule until compared to the frozen authority. |
| MAP-U01 | `UNRESOLVED` | No distinct "Episode of Care" entity; `Admission` appears to serve this function. | Add to Issue #121 as a repository gap. |
| MAP-U02 | `UNRESOLVED` | No distinct "Schedule" entity/table. | Add to Issue #121 as a repository gap. |
| MAP-U03 | `UNRESOLVED` | No entity literally named "Updated Comprehensive Assessment"; `RNRecertAssessment` (`form_type="RECERT"`) is the closest existing analog. | Add to Issue #121 for clarification. |
| MAP-U04 | `UNRESOLVED` | No distinct "HOPE Admission" record; HOPE workflow fields live directly on `RnicaAssessment`. | Add to Issue #121; relevant to future `BUILD_LATER: HOPE Admission workflow`. |
| MAP-U05 | `UNRESOLVED` | HUV1/HUV2 trigger *rules* are authoritatively defined in `WORKFLOW_TRIGGER_REGISTRY` (`form_registry.py`), but no dedicated HUV1/HUV2 clinical-record entity exists. *(Updated, Amendment 1.)* | Add to Issue #121; relevant to future `BUILD_LATER: HUV1/HUV2 workflow`. |
| MAP-N01 | `NOT_FOUND` (narrowed, Amendment 1) | Only `J2050B` does not exist as a code identifier anywhere in the backend. `J2050`, `J2051A`–`J2051H`, `J2052`, and `J2053` are `VERIFIED` in `backend/app/domain/forms/form_registry.py` (see Amendment 1). | Add `J2050B` to Issue #121 as a repository gap; do not fabricate this field. |
| MAP-U06 | `UNRESOLVED` (narrowed, Amendment 1) | J2051 items are `VERIFIED` as named HOPE item codes in `form_registry.py`; the exact JSONB key(s) storing their values within `RnicaAssessment.form_data` are not yet exhaustively confirmed. | Add to Issue #121 for a follow-up JSONB-schema-focused pass. |
| MAP-D01 | `DUPLICATE_SOURCE` | Two amendment mechanisms exist: `RnicaAmendment` (RNICA-specific) and `Amendment` (generic clinical notes). | Add to Issue #121 for clarification of intended scope boundary. |
| MAP-D02 | `DUPLICATE_SOURCE` / `UNRESOLVED` | Two role representations exist: `User.role` (free-text, operationally used) and `Role` (`roles` table, `interface_id`-scoped). Relationship between them not confirmed. | Add to Issue #121 for clarification. |
| MAP-U07 | `UNRESOLVED` | Two discipline vocabularies exist: `CORE_DISCIPLINES = ["RN","MD","MSW","SC"]` (`enums.py`) vs. `CANONICAL_VISIT_TYPES`/`ALLOWED_VISIT_SERVICES` (`visit_types.py`), which include additional values (`LVN`, `NP`, `SW`, `CHAPLAIN`, `CHHA`, `VOLUNTEER`, `PA`, `LPN`). | Add to Issue #121 for clarification of intended scope per use case. |
| MAP-U08 | `UNRESOLVED` | No dedicated clinical credential/license-expiration tracking table found separate from `User.license_number`/`User.npi`. | Add to Issue #121 as a repository gap. |
| MAP-N02 | `NOT_FOUND` | No version-history table exists for `rnica_assessments`, `msw_ica_assessments`, or `scica_assessments` (unlike `plan_of_care_versions`). | Add to Issue #121 as a repository gap. |

---

## Verification

- [x] Backend `app/models/` directory enumerated (114 files) and reviewed for entities in scope.
- [x] Backend `app/services/` and `app/api/` searched for HOPE/HUV/SFV/J2050–J2053 logic.
- [x] Backend `app/core/` searched for visit-type and discipline normalization.
- [x] Repository-wide search performed for `J2050`, `J2050B`, `J2051`, `J2052`, `J2053`. Corrected in Amendment 1: `backend/app/domain/forms/form_registry.py` contains `J2050`, `J2051A`–`J2051H`, `J2052`, and `J2053` as named HOPE item codes; only `J2050B` remains not found anywhere in the repository.
- [ ] Frontend (`sns-emr-frontend/`) source-of-truth for RNICA form fields not exhaustively cross-checked against backend `form_data` JSONB contents in this pass (see MAP-U06).
- [ ] Migration history (`alembic` revision files) not exhaustively cross-referenced against current model state in this pass.
- [x] No synthetic fields or entities were invented; all `NOT_FOUND`/`UNRESOLVED` items are recorded as such rather than assumed.
- [x] Frozen authority documents were not modified to produce this map.
- [x] No application behavior, schema, migration, or production data was changed.

## Final Report

```text
PATIENT/EPISODE MAPPING: INCOMPLETE (Episode of care NOT_FOUND)
BENEFIT-PERIOD MAPPING: COMPLETE
VISIT/SCHEDULE MAPPING: INCOMPLETE (Schedule NOT_FOUND)
ASSESSMENT MAPPING: INCOMPLETE (UCA UNRESOLVED)
HOPE/HUV/SFV MAPPING: INCOMPLETE (HOPE Admission UNRESOLVED; HUV1/HUV2 record NOT_FOUND, rule VERIFIED)
J2050-J2053 MAPPING: INCOMPLETE (J2050B NOT_FOUND; J2050/J2051/J2052/J2053 VERIFIED per Amendment 1)
IDENTITY/DISCIPLINE MAPPING: INCOMPLETE (Role, Credential, Discipline vocabulary UNRESOLVED)
AUDIT/CORRECTION MAPPING: INCOMPLETE (assessment-level version history NOT_FOUND)

VERIFIED: 22
NOT_FOUND: 6
UNRESOLVED: 9
DUPLICATE_SOURCE: 2
CONFLICT: 2 (candidates, unconfirmed — MAP-C01, MAP-C02)

FROZEN DOCUMENTS MODIFIED: NO
APPLICATION BEHAVIOR MODIFIED: NO
SCHEMA MODIFIED: NO
MIGRATIONS MODIFIED: NO
IMPLEMENTATION AUTHORIZATION: NOT_AUTHORIZED
```
