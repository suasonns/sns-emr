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

---

# Addendum: Backend ↔ Frontend Gap Analysis and SSOT Audit

**STATUS: DISCOVERY ONLY. NO CODE, SCHEMA, MIGRATION, WORKFLOW, FORM, MODEL, API, OR REGISTRY CHANGES WERE MADE TO PRODUCE THIS ADDENDUM.**

This addendum reconciles the SNS EMR backend (`backend/app/`, 1021 Python files) and frontend (`sns-emr-frontend/src/`, 256 JS/TS/JSX/TSX files) to identify sources of truth, duplicate sources of truth, undocumented functionality, and legacy/hidden objects, per the requested 8-phase analysis. **Coverage note**: given the repository size, this is a representative, evidence-backed inventory of the objects most relevant to the RNICA/HOPE/SFV domain and system-wide architecture, not a literal row-per-file listing of all 1021+256 files. Categories that could not be fully enumerated are explicitly marked `(partial)`.

## Phase 1 — Repository Inventory

### Backend

| Type | Name | Path | Referenced By | Active |
|---|---|---|---|---|
| Forms | `form_registry` (static registry/constants) | `backend/app/domain/forms/form_registry.py` | `app.domain.forms.form_resolution_service`, `app.api.routes.forms`, `app.models.form_registry_model` | ACTIVE |
| Forms | `MODULE_REGISTRY` | `backend/app/domain/forms/module_registry.py` | `app.domain.forms.form_resolution_service` | ACTIVE |
| Forms | `FormType`, `FormFamily`, `Discipline` (forms-domain enums) | `backend/app/domain/forms/enums.py:6,25,39` | form registry/resolution | ACTIVE |
| Models | 114 SQLAlchemy models across `backend/app/models/` (Patient, Admission, BenefitPeriod, Visit, RnicaAssessment, MswIcaAssessment, ScicaAssessment, RNRecertAssessment, SFVRequirement, User, Role, AuditLog, Task, PlanOfCare/PlanOfCareVersion, IDG* (11 models), POC* (3+ models), Physician*, Billing/Ontology tables, etc.) | `backend/app/models/*.py` | API routers and services throughout | ACTIVE (114/114 enumerated by name; see full list in background-agent output retained in PR discussion) |
| Enums | `CORE_DISCIPLINES`, `TaskStatus`, `TaskType`, `TaskOrigin`, `TaskRegulatoryBasis`, `CompletionReferenceType`, `TaskDiscipline`, `Discipline`, `CareSettingEnum`, `SafetyResponsibilityEnum`, `VisitEventType`, `VisitFormType`, `ServiceContext`, `NoteFormFamily`, `DiagnosisType`, `DiagnosisStatus`, `DiagnosisSource` | `backend/app/models/enums.py` | task engine, form registry, diagnosis sync | ACTIVE |
| Enums | `IDGImpactLevel`, `IDGActivationRoute` | `backend/app/constants/idg_enums.py` | IDG services | ACTIVE |
| Enums | `RuleOutcome`, `RuleSeverity`, `Workflow` | `backend/app/rules/base.py` | rules engine/registry | ACTIVE |
| APIs | ~40+ FastAPI routers sampled, incl. `/auth`, `/patients`, `/admissions`, `/patient-orders`, `/physicians`, `/physician-orders`, `/clinical-notes`, `/communications-log`, `/dashboard`, `/idg`, `/forms`, `/visits/rnica`, `/rules`, `/compliance`, `/documents`, `/tasks`, `/task-scheduling`, `/billing/hospice-cap`, `/billing/835`, `/admin/*`, `/api/owner/*` | `backend/app/api/*.py`, `backend/app/api/routes/*.py`, `backend/app/api/idg/router.py` (partial — 97 total router files, ~40 sampled) | `app.api.registry` | ACTIVE |
| Services | `task_engine`, `task_scheduler`/`overdue_scheduler`, `document_recovery_scheduler`, `clinical_note_validation_engine`, `clinical_reasoning_engine`, `idg_meeting_scheduler`, `idg_group_service`, `idg_lifecycle_engine`, `idg_task_engine`, `idg_review_automation`, `supervisory_scheduling_service`, `bereavement_letters_service`, `bereavement_poc_catalog`, `eligibility_registry_service`, `eligibility.engine`, `evidence.document_harvest_job`, `evidence.recovery_service`, `billing_engine`, `claim_segment_service`, `readiness_workflow_service`, `claim_export_service`, `poc_generation_service`, `poc_service`, `poc_task_engine`, `task_completion_service`, `task_notification_engine`, `task_overdue_engine`, `workflow_validation`, `hope_phase_b_engine` (partial — 203 total service files, ~30 sampled) | `backend/app/services/*.py`, `backend/app/billing/services/*.py` | routers, other services, `app.main` startup | ACTIVE |
| Validators | `clinical_note_validation_engine`, `admission_dx_validation_engine`, `workflow_validation`, `rules_dry_run`, `eligibility/evidence_conflict_detection` | `backend/app/services/*.py` | clinical note/admission/eligibility flows | ACTIVE |
| Workflow/trigger/status registries | `RULE_CLASS_REGISTRY`, `MANDATORY_RULE_IDS`, `DEFAULT_RULES_BY_WORKFLOW` | `backend/app/rules/registry.py` | rules engine | ACTIVE |
| Workflow/trigger/status registries | `MODULE_REGISTRY`, `VISIT_HEADER_FIELDS`, `FORM_TYPE_ALIASES`, `DISCIPLINE_ALIASES` | `backend/app/domain/forms/module_registry.py`, `form_registry.py` | form resolution | ACTIVE |
| Workflow/trigger/status registries | **`WORKFLOW_TRIGGER_REGISTRY`** (`TRIGGER_HUV1`, `TRIGGER_HUV2`, `TRIGGER_SFV`, `TRIGGER_SUPERVISORY` keys; `allowed_disciplines`, day windows, `hope_item_codes`, `source_items`/`completion_items`) | `backend/app/domain/forms/form_registry.py:912` | `get_base_form_config`, discipline/trigger validation functions in the same file (lines ~1017-1098) | **ACTIVE — corrects a background-agent scan that reported this registry as "not found"; directly confirmed by `grep` against `origin/main` in this pass.** |
| Status engines | Status-transition logic in `admission_status_engine`, `task_engine`, `idg_lifecycle_engine`, `idg_meeting_scheduler` | `backend/app/services/*.py` | admission/task/IDG workflows | ACTIVE |
| Database tables/views | `form_registry`, `form_modules`, `form_package_modules`, `forms`, `tasks`, `visits`, `patients`, `physicians`, `poc_*`, `idg_*` (11 tables), `clinical_notes`/`clinical_note_versions`, `clinical_workflow_map`, `tenant_rule_toggles`, `ontology_*` (multiple), `billing/*` (multiple) | `backend/app/models/*.py` | see Models row above | ACTIVE |
| Database tables/views | `backend/alembic/` migration history | `backend/alembic/` | schema history | present, not cross-referenced line-by-line in this pass |
| Jobs/scheduled tasks | `overdue_scheduler()`, `document_recovery_scheduler()`, `generate_idg_meetings`/IDG meeting scheduler, `BackgroundTasks`-driven evidence/document harvest, `visit_recordings` background upload processing | `backend/app/services/task_scheduler.py`, `document_recovery_scheduler.py`, `idg_meeting_scheduler.py`, `evidence/document_harvest_job.py`, `api/visit_recordings.py` | `app.main` startup, API entrypoints | ACTIVE |
| Jobs/scheduled tasks | `backfill_med_recon_duplicate_backlog_sql.main` | `backend/app/jobs/backfill_med_recon_duplicate_backlog_sql.py` | ad hoc script, not scheduled | UNCLEAR — appears to be a one-off backfill script, not a recurring job |

*(Backend inventory is partial for Services (203 files) and APIs (97 files) — sampled ~30 and ~40 respectively, prioritized toward RNICA/HOPE/SFV, IDG, POC, billing, and rules-engine domains most relevant to this reconciliation.)*

### Frontend

| Type | Name | Path | Calls API | Visible |
|---|---|---|---|---|
| Routes | Full route table: `/login`, `/set-password`, `/billing/*` (10 sub-routes), `/analytics`, `/tenant`, `/owner`, `/owner/:section`, `/rnica` (+ aliases `/nursing-assessment`, `/admission`, `/assessment`), `/msw-ica` (+ aliases `/psychosocial`, `/psychosocial-assessment`), `/sc-ica` (+ aliases `/spiritual`, `/spiritual-assessment`), `/patient-lcd`, `/care-overview`, `/plan-of-care`, `/bereavement`, `/incident-occurrence`, `/clinical-alerts`, `/physician`, `/communication-log`, `/secure-inbox` (+ aliases), `/compliance`, `/volunteer-scheduling`, `/idg-workspace`, `/my-profile`, `/portal`, `/chart/:patientId`, fallback `*` → `/login` | `src/App.tsx` (lines 69-132) | route-specific | VISIBLE, several role-gated (`tenant`/`owner`/`analytics`/`billing` feature) |
| Pages | RNICAPage, MSWICAPage, SCICAPage, CareOverviewPage, PlanOfCarePage, BereavementDataPage, IncidentOccurrenceDataPage, ClinicalAlertsDataPage, PhysicianDataPage, CommunicationLogDataPage, SecureInboxDataPage, ComplianceDataPage, VolunteerSchedulingDataPage, IDGWorkspacePage, MyProfilePage, PatientLCDPage, TenantDashboard, OwnerDashboard, SNSAnalytics, 9 billing pages, `ComingSoonPage` (placeholder) | `src/pages/*.tsx`, `src/tenant/TenantDashboard.jsx`, `src/owner/OwnerDashboard.jsx` | per-page APIs, see below | VISIBLE (most); `ComingSoonPage` is an explicit placeholder |
| Forms | RNICA, MSWICA, SCICA (major clinical forms); `AdmissionActionCenterDrawer`; `CompliancePage` workflow panel; `PlanOfCarePage`; `PatientLCDPage`; `VolunteerSchedulingPage` | `src/components/RNICA.jsx`, `src/components/MSWICA.jsx`, `src/components/SCICA.jsx`, `src/components/AdmissionActionCenterDrawer.jsx`, `src/pages/*.tsx` | `icaAssessments`, `patientCharts`, `eligibility`, `medications`, `ordersHub`, `physicianOrders`, `facesheet`, others | VISIBLE |
| Tabs/Wizards/Modals | `RNICACommandWorkspace`, `AdmissionActionCenterDrawer`, `PhysicianDirectoryModal`, `AuditEventDrawer` (owner), `StaffProfileDrawer` (owner) | `src/components/rn-ica/RNICACommandWorkspace.jsx`, `src/components/AdmissionActionCenterDrawer.jsx`, `src/components/PhysicianDirectoryModal.jsx`, `src/owner/components/*.jsx` | RN ICA command APIs, physician lookup, owner audit/staff APIs | VISIBLE |
| Components | `layout/Sidebar`, `PortalShell`, `PatientModuleShell`, `PatientChart`, `PatientChartSidebar`, `PatientFacesheet`, `DischargePlanningBoard`, `PhysicianOrdersBoard`, `DocumentsBoard`, `VisitNotes`, `VisitRecorderCard`, `ClaimLifecycle`, `BillerShell`, `AgencyContext`, `ClinicalComplianceDashboard`, `RequireSessionAccess`, `RequireFeatureAccess`, `UnauthorizedAccess`, `MedicationNameInput`, `Icd10DiagnosisInput`, `BillingAuditHistoryPanel` (partial — representative sample) | `src/components/**/*.jsx,tsx`, `src/charts/*.jsx` | per-component APIs | VISIBLE |
| Grids/Tables | BillingDashboard data tables, EligibilityVerificationPage tables, ReportsPage/FacilityCollectionsReportPage grids, RNICA structured findings panels, MSWICA/SCICA assessment sections | `src/pages/BillingDashboard.tsx`, `src/pages/billing/*.tsx`, `src/components/RNICA.jsx`, `src/components/MSWICA.jsx`, `src/components/SCICA.jsx` | per-page/component APIs | VISIBLE |
| Navigation entries | Owner Dashboard, Billing Hub, Analytics, Tenant Dashboard, IDG Meeting Workspace, Portal Preview (`Sidebar.tsx`); TenantDashboard internal tabs (Dashboard, Patient Census, Referrals, Clinical, Insights, Help & Support, Agency Settings, Inbox, Settings); OwnerShell nav items; Portal quick links (Care Overview, Secure Inbox, Incident/Occurrence, Compliance/LCD/HOPE/QIES, Bereavement, Patient LCD, Analytics, Tenant Dashboard) | `src/components/layout/Sidebar.tsx`, `src/tenant/TenantDashboard.jsx`, `src/owner/shell/OwnerShell.jsx`, `src/pages/SNSPortal.tsx` | none directly (nav only) | VISIBLE, several conditional on role/feature |
| Feature flags | `billing` feature gate (routes + sidebar nav), owner-only branch (`hasRouteAccess(sessionUser, "owner")`), `access_scope === "billing"` branch, role-gated route wrappers (`tenant`/`owner`/`analytics`) | `src/App.tsx`, `src/components/layout/Sidebar.tsx` | none | HIDDEN unless the corresponding flag/role/scope is satisfied |
| API call sites | `src/api/dashboard.ts`, `ownerAdmin.ts`, `auth.ts`, `icaAssessments.ts`, `patientCharts.ts`, `census.ts`, `visitNotes.ts`, `eligibility.ts`, `medications.ts`, `ordersHub.ts`, `physicianOrders.ts`, `facesheet.ts`, `vendors.ts`, `staff.ts`, `offlineAssessmentApi.ts`, `offlineSignalReviewApi.ts`, `offlineRecordingQueue.js` | `src/api/*.ts,js` | see individual endpoint lists in agent output retained in PR discussion | N/A (these are the API client layer, not UI) |

*(Frontend inventory is partial for the `components/` directory generally — a representative sample was taken, prioritized toward RNICA/HOPE/SFV-adjacent and navigation-critical components, not all ~150+ component files.)*

## Phase 2 — Backend ↔ Frontend Mapping

| Backend Object | Frontend Object | Status |
|---|---|---|
| `RnicaAssessment` + RNICA APIs (`/visits/rnica`, `icaAssessments`) | `RNICAPage` / `src/components/RNICA.jsx` / `RNICACommandWorkspace` | MATCHED |
| `MswIcaAssessment` + ICA APIs | `MSWICAPage` / `src/components/MSWICA.jsx` | MATCHED |
| `ScicaAssessment` + ICA APIs | `SCICAPage` / `src/components/SCICA.jsx` | MATCHED |
| `RNRecertAssessment` | No dedicated frontend page/component identified distinct from RNICA | PARTIAL — recert assessment likely rendered through the same RNICA form/route (`assessment_type` differentiation), not a separately named UI surface |
| `PlanOfCare`/`PlanOfCareVersion` + POC services | `PlanOfCarePage` | MATCHED |
| `SFVRequirement` + `WORKFLOW_TRIGGER_REGISTRY[TRIGGER_SFV]` | SFV nav section + trigger banner inside `RNICA.jsx` (per `docs/tenant-platform/RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`, line ~11393) | MATCHED — note: this contradicts a background-agent scan of the frontend that reported "no explicit SFV string found"; the existing, more targeted `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` citation is treated as authoritative here since it includes a specific file:line reference |
| HUV1/HUV2 trigger rules (`WORKFLOW_TRIGGER_REGISTRY`) | No RNICA-specific HUV UI surface found (per `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`: "BACKEND ONLY") | BACKEND_ONLY |
| HOPE workflow fields on `RnicaAssessment` (`hope_workflow_status`, etc.) | HOPE-adjacent references in `CompliancePage`/`SNSPortal` ("Compliance / LCD / HOPE / QIES" quick link) | PARTIAL — HOPE lifecycle actions surface inside the RNICA form itself (per `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`: "HOPE Generator" WIRED), while `CompliancePage` provides only a general compliance/HOPE reference point, not the same workflow surface |
| `IDGGroup`/`IDGMeeting`/`IDGReview`/etc. (11 models) + `/idg` API + IDG services | `IDGWorkspacePage`, IDG nav entry, `idg` router | MATCHED |
| `Amendment` (generic clinical note correction) | No distinct frontend correction/amendment UI identified in this pass | UNCLEAR — not traced to a specific component |
| `RnicaAmendment` (RNICA-specific correction) | No distinct frontend amendment UI identified in this pass, separate from the main RNICA form | UNCLEAR — not traced to a specific component |
| `Role` model (`roles` table) | No frontend role-management UI identified in this pass | UNCLEAR — `User.role` (free text) appears to drive frontend role-gating (`hasRouteAccess`), not the separate `Role` table |
| Billing engine/services (`billing_engine`, `claim_*`, `readiness_workflow_service`) | 9 billing pages (`BillingOverviewPage`, `ReadinessWorkflowPage`, `ClaimsManagementPage`, etc.) + `ComingSoonPage` placeholder | MATCHED, with `ComingSoonPage` explicitly marking at least one unbuilt billing sub-feature |
| `guardrail_policies` model | No frontend surface identified in this pass | BACKEND_ONLY (unconfirmed — not exhaustively searched) |
| `clinical_workflow_map` model | No frontend surface identified in this pass | BACKEND_ONLY (unconfirmed — not exhaustively searched) |

## Phase 3 — RNICA / Assessment Audit

| Assessment | Backend | Frontend | API | Workflow | Status |
|---|---|---|---|---|---|
| RNICA | `RnicaAssessment` (`rnica_assessments`) | `RNICAPage`/`RNICA.jsx` | `/visits/rnica`, `icaAssessments` | HOPE workflow fields embedded on the row; lock/amendment via `RnicaAmendment` | VERIFIED, MATCHED |
| Initial Assessment / Initial Comprehensive Assessment (RNICA+MSW ICA+SC ICA package) | Three separate models (`RnicaAssessment`, `MswIcaAssessment`, `ScicaAssessment`) tracked independently, composed as one package per `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` ("SNS_INTERNAL_WORKFLOW composition") | Three separate pages/forms | Three separate API surfaces | SNS-internal composition, not a CMS-required single entity | VERIFIED as three-discipline composition, not a single backend/frontend object — MATCHED at the discipline level, no single "package" entity exists |
| Updated Comprehensive Assessment (UCA) | No entity literally named this; `RNRecertAssessment` is closest analog | No distinct frontend surface identified separate from RNICA form | Not separately confirmed | UNRESOLVED (carried over from BUILD_NOW-001, MAP-U03) | UNRESOLVED |
| Recertification Assessment | `RNRecertAssessment` (`form_type="RECERT"`) | No separately named page/component found; likely rendered via the same RNICA-family UI | Not separately confirmed in this pass | — | PARTIAL |
| HOPE Admission | No distinct model; fields embedded on `RnicaAssessment` | No distinct page; HOPE actions appear inside the RNICA form itself | HOPE lifecycle endpoints inside RNICA API surface | UNRESOLVED (carried over from BUILD_NOW-001, MAP-U04) | UNRESOLVED |
| HUV1 | Trigger rule VERIFIED in `WORKFLOW_TRIGGER_REGISTRY`; no dedicated record | Not found as a distinct frontend surface | Not separately confirmed | Trigger/task creation logic in `hope_phase_b_engine.py` | BACKEND_ONLY |
| HUV2 | Same as HUV1 | Not found as a distinct frontend surface | Not separately confirmed | Same pattern as HUV1 | BACKEND_ONLY |
| SFV | `SFVRequirement` VERIFIED; trigger rule VERIFIED in `WORKFLOW_TRIGGER_REGISTRY` | SFV nav section + trigger banner exists inside `RNICA.jsx` per `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` | `/visits/rnica`-adjacent (not separately enumerated here) | `hope_phase_b_engine.py` trigger/completion functions | MATCHED (backend and frontend both confirmed, via two different evidence sources) |

## Phase 4 — HOPE Item Audit (J2050–J2053)

This phase is fully covered by **Amendment 1** above. Summary, with frontend/API columns added:

| Item | Backend Location | Frontend Location | API | Status |
|---|---|---|---|---|
| J2050 | `HOPE_SYMPTOM_ITEM_CODES` in `backend/app/domain/forms/form_registry.py` | Not confirmed as a literal frontend field key in this pass (referenced only in prose in `docs/` and possibly `sns-emr-frontend/schemas/rnica-field-schema.json` — not re-verified in this addendum) | Not separately confirmed | VERIFIED (backend) / UNCONFIRMED (frontend) |
| J2050B | Not found anywhere in the repository | Not found | Not found | NOT_FOUND |
| J2051 (A–H) | `HOPE_SYMPTOM_ITEM_CODES` + `WORKFLOW_TRIGGER_REGISTRY[TRIGGER_SFV]["metadata"]["source_items"]` in `form_registry.py`; runtime derivation via `j2051_pain_impact`/`j2051_non_pain_impact` in `hope_phase_b_engine.py`/`visits.py` | Not confirmed as literal frontend field keys in this pass | Not separately confirmed | VERIFIED (backend) / UNCONFIRMED (frontend) |
| J2052, J2053 | `HOPE_SFV_ITEM_CODES` + `WORKFLOW_TRIGGER_REGISTRY[TRIGGER_SFV]["metadata"]["completion_items"]` in `form_registry.py` | Not confirmed as literal frontend field keys in this pass | Not separately confirmed | VERIFIED (backend) / UNCONFIRMED (frontend) |

**Recommended follow-up (not performed in this pass)**: a targeted grep of `sns-emr-frontend/schemas/rnica-field-schema.json` and `RNICA.jsx` for literal `J20xx` keys, to close the "UNCONFIRMED (frontend)" gap above.

## Phase 5 — Registry Audit

| Registry | Definition Location | Authority | Duplicate | Conflict |
|---|---|---|---|---|
| `form_registry` (static) | `backend/app/domain/forms/form_registry.py` | Code-level authoritative source for form structure/field lists | Also exists as a DB-backed model `FormRegistryModel`/`form_registry` table (`backend/app/models/form_registry_model.py`) | **Potential duplicate** — a static, code-defined registry and a DB-backed model share the name "form registry." Relationship between the two (which one is authoritative at runtime) was not resolved in this pass — flagged below as MAP-D03. |
| `WORKFLOW_TRIGGER_REGISTRY` | `backend/app/domain/forms/form_registry.py:912` | Authoritative for HUV1/HUV2/SFV/SUPERVISORY trigger rules (disciplines, day windows, item codes) | None found | None found in this pass, other than the SFV-discipline finding already logged as MAP-C02 |
| `MODULE_REGISTRY` | `backend/app/domain/forms/module_registry.py` | Authoritative for form-module composition | None found | None found |
| `RULE_CLASS_REGISTRY` / `DEFAULT_RULES_BY_WORKFLOW` | `backend/app/rules/registry.py` | Authoritative for the general clinical-rules engine (distinct from HOPE/SFV triggers) | None found | Not cross-checked against `WORKFLOW_TRIGGER_REGISTRY` for overlapping responsibility — flagged as MAP-U09 below |
| Status registry / task registry / assessment registry (as literal named objects) | Not found as single centralized registries; status/task logic is distributed across `task_engine`, `admission_status_engine`, `idg_lifecycle_engine`, and per-model `status` fields | No single authoritative registry exists for these concerns | Distributed logic, not literally duplicated | Not confirmed as a conflict, but distributed status logic is itself a documentation gap — flagged as MAP-U10 below |

## Phase 6 — SSOT Register

| Domain | Authoritative Source | Alternate Sources | Classification |
|---|---|---|---|
| Patient | `backend/app/models/patient.py` (`Patient`) | None found | SINGLE_SSOT |
| Episode (of care) | `Admission` serves this role; no distinct entity | None — this is a naming gap, not a duplication | SINGLE_SSOT (by function, under a different name) |
| Benefit Period | `backend/app/models/benefit_period.py` (`BenefitPeriod`) | None found | SINGLE_SSOT |
| Visit | `backend/app/models/visit.py` (`Visit`) | None found | SINGLE_SSOT |
| Assessment (RNICA family) | `RnicaAssessment`, `MswIcaAssessment`, `ScicaAssessment`, `RNRecertAssessment` — four distinct, discipline-scoped models | None duplicating the same discipline | SINGLE_SSOT per discipline; the "package" concept composing all three ICA disciplines is SNS-internal, not a backend entity |
| RNICA specifically | `backend/app/models/rnica_assessment.py` | None found | SINGLE_SSOT |
| HOPE (workflow state) | Embedded fields on `RnicaAssessment` | None found | SINGLE_SSOT (but embedded rather than a distinct "HOPE Admission" entity — MAP-U04) |
| HOPE (item-code definitions) | `HOPE_*_ITEM_CODES` lists in `backend/app/domain/forms/form_registry.py` | None found | SINGLE_SSOT |
| HUV (trigger rule) | `WORKFLOW_TRIGGER_REGISTRY[TRIGGER_HUV1]`/`[TRIGGER_HUV2]` in `form_registry.py` | Also referenced as `TaskType.HUV1`/`HUV2` (`enums.py`) and `trigger_source_type` values (`sfv_requirement.py`) | **DUPLICATE_SSOT (candidate)** — the same trigger concept is represented in three places (form_registry rule, enums.py task type, sfv_requirement check constraint). Not necessarily wrong (they may be intentionally cross-referenced layers), but not documented as such anywhere — flagged as MAP-D04 below. |
| SFV (requirement tracking) | `backend/app/models/sfv_requirement.py` (`SFVRequirement`) | Trigger *rule* duplicated in `WORKFLOW_TRIGGER_REGISTRY` (see HUV row above) | PARTIAL — record-tracking is SINGLE_SSOT; trigger-rule definition overlaps with the same pattern as HUV |
| User (identity) | `backend/app/models/user.py` (`User`) | None found | SINGLE_SSOT |
| Employee/Staff | Not confirmed as a distinct entity separate from `User`; `StaffPermissionGrant` references staff capability, not identity | Not resolved in this pass | UNRESOLVED |
| Credential | `User.license_number`/`User.npi` fields | None found as a separate table | SINGLE_SSOT (narrow) — no credential-expiration tracking exists (MAP-U08, carried over) |
| Discipline | `CORE_DISCIPLINES` (`enums.py`), `CANONICAL_VISIT_TYPES`/`ALLOWED_VISIT_SERVICES` (`visit_types.py`), `Discipline` enum (`domain/forms/enums.py`), `User.discipline` (free text) | **Four separate representations of "discipline" exist across the codebase** | **CONFLICTING_SSOT** — carried over and escalated from MAP-U07; a fourth representation (`domain/forms/enums.py::Discipline`) was newly identified in this pass and was not part of the original BUILD_NOW-001 finding. Flagged as MAP-C03 below. |
| Audit | `backend/app/models/audit_log.py` (`AuditLog`) — generic; `RnicaAmendment`/`Amendment` — correction-specific | Two separate amendment mechanisms (already MAP-D01) | PARTIAL — generic audit log is SINGLE_SSOT; correction/amendment tracking is DUPLICATE_SSOT (MAP-D01) |
| Role/Permission | `User.role` (free text) + `Role` model (`roles` table) + `StaffPermissionGrant` (capability grants) | Three distinct mechanisms | **DUPLICATE_SSOT** — carried over from MAP-D02, now with a third mechanism (`StaffPermissionGrant`) confirmed to layer on top rather than replace the other two |

## Phase 7 — Legacy / Hidden Object Discovery

| Object | Location | Status |
|---|---|---|
| `ComingSoonPage` | `sns-emr-frontend/src/pages/billing/ComingSoonPage.tsx` | ACTIVE placeholder — explicitly marks at least one billing sub-feature as not yet built; not legacy, but worth noting as a known incomplete surface |
| `AssessmentDiscrepancy` model | `backend/app/models/assessment_discrepancy.py` | UNCLEAR — background scan could not confirm active referencing; requires a follow-up reference trace before being called ACTIVE or LEGACY |
| `ClinicalWorkflowMap` model | `backend/app/models/clinical_workflow_map.py` | UNCLEAR — same as above |
| `GuardrailPolicy` model | `backend/app/models/guardrail_policy.py` | UNCLEAR — same as above |
| `Refusal` model | `backend/app/models/refusal.py` | UNCLEAR — same as above |
| `SurveyAccess` model | `backend/app/models/survey_access.py` | UNCLEAR — same as above |
| `Interface` model | `backend/app/models/interface.py` | UNCLEAR — same as above |
| `backfill_med_recon_duplicate_backlog_sql.py` | `backend/app/jobs/` | UNKNOWN — appears to be a one-off backfill script, not a recurring scheduled job; status as "still needed" vs. "completed/dead" not determined in this pass |
| `Amendment` vs. `RnicaAmendment` | `backend/app/models/amendment.py`, `backend/app/models/rnica_amendment.py` | Both ACTIVE by different call paths (MAP-D01) — not legacy, but a duplicate-mechanism risk, not dead code |

**No object in this phase was confirmed as `DEAD_CODE` in this pass** — several are `UNCLEAR` and require a targeted reference-trace (grep for imports/instantiations) before a confident ACTIVE/LEGACY/DEAD_CODE classification can be made. This addendum does not fabricate a classification where evidence is insufficient.

## Phase 8 — Gap Report

| Gap ID | Category | Finding | Severity | Recommended Authority |
|---|---|---|---|---|
| GAP-01 | SSOT — Discipline | Four separate representations of "discipline" exist (`CORE_DISCIPLINES`, `CANONICAL_VISIT_TYPES`/`ALLOWED_VISIT_SERVICES`, `domain/forms/enums.Discipline`, `User.discipline` free text) | HIGH | Compliance + Engineering |
| GAP-02 | SSOT — Role/Permission | Three separate role/permission mechanisms (`User.role`, `Role` model, `StaffPermissionGrant`) with unconfirmed relationship | HIGH | Engineering + Security |
| GAP-03 | SSOT — Form registry | Static code-defined `form_registry.py` and DB-backed `FormRegistryModel`/`form_registry` table share a name; authoritative-at-runtime relationship not confirmed | MEDIUM | Engineering |
| GAP-04 | SSOT — HUV/SFV trigger representation | Same trigger concept (HUV1/HUV2) is represented in three places (`WORKFLOW_TRIGGER_REGISTRY`, `TaskType` enum, `SFVRequirement.trigger_source_type` check constraint) without a documented single authority | MEDIUM | Engineering + Compliance |
| GAP-05 | Compliance — SFV discipline scope | `WORKFLOW_TRIGGER_REGISTRY[TRIGGER_SFV]["allowed_disciplines"]` includes both RN and LVN (MAP-C02) | **CRITICAL** | Compliance + Medical Director |
| GAP-06 | Frontend/Backend — HUV visibility | HUV1/HUV2 trigger rules exist in the backend with no corresponding frontend surface; clinicians have no dedicated UI for HUV1/HUV2 tasks beyond the generic task list (unconfirmed) | MEDIUM | Clinical Operations + Engineering |
| GAP-07 | Frontend/Backend — J2050–J2053 field confirmation | Backend HOPE item codes for J2050/J2051/J2052/J2053 are verified, but their presence as literal frontend field keys was not confirmed in this pass | LOW | Engineering |
| GAP-08 | Legacy/Unknown — Several models with unconfirmed activity | `AssessmentDiscrepancy`, `ClinicalWorkflowMap`, `GuardrailPolicy`, `Refusal`, `SurveyAccess`, `Interface` models could not be confirmed ACTIVE or LEGACY in this pass | LOW | Engineering |
| GAP-09 | Assessment/Frontend — UCA and Recert UI | No distinct frontend surface was identified for the "Updated Comprehensive Assessment" concept or `RNRecertAssessment`, separate from the main RNICA form | LOW | Clinical Operations |
| GAP-10 | Amendment mechanism visibility | Neither `Amendment` nor `RnicaAmendment` was traced to a distinct frontend correction/amendment UI in this pass | LOW | Engineering |

## Recommended Authoritative Sources (non-binding, for Issue #121 review — not implemented here)

- **Discipline**: Recommend `CORE_DISCIPLINES` (`enums.py`) as the compliance-facing authority (IDG completeness, signature validation, task routing) and `CANONICAL_VISIT_TYPES` as the visit-scheduling-facing authority, with an explicit documented mapping between them — **not implemented; requires Compliance sign-off.**
- **Role/Permission**: Recommend `Role` model as the structural authority and `StaffPermissionGrant` as the capability-delegation layer on top of it, with `User.role` treated as a legacy/display field pending confirmation — **not implemented; requires Engineering + Security review.**
- **Form registry**: Recommend clarifying whether `backend/app/domain/forms/form_registry.py` (code) or `FormRegistryModel`/`form_registry` (DB) is authoritative at runtime — **not implemented; requires Engineering review.**
- **HUV/SFV trigger definition**: Recommend `WORKFLOW_TRIGGER_REGISTRY` as the single authoritative rule source, with `TaskType` enum and `SFVRequirement.trigger_source_type` treated as consuming/validating representations rather than independent sources — **not implemented; requires Engineering confirmation.**
- **SFV discipline scope (GAP-05 / MAP-C02)**: No recommendation is made here. This is a clinical-compliance question requiring comparison against the frozen SFV/LVN escalation authority before any recommendation can be responsibly made.

## New Conflict/Unresolved Items From This Addendum (for Issue #121)

| ID | Finding | Type |
|---|---|---|
| MAP-D03 | Static `form_registry.py` vs. DB-backed `FormRegistryModel`/`form_registry` table — relationship unconfirmed | DUPLICATE_SOURCE |
| MAP-D04 | HUV1/HUV2 trigger concept represented in three places (`WORKFLOW_TRIGGER_REGISTRY`, `TaskType` enum, `SFVRequirement` check constraint) | DUPLICATE_SOURCE |
| MAP-C03 | Four discipline vocabularies now confirmed (escalated from MAP-U07, which found two) | CONFLICT (candidate) |
| MAP-U09 | `RULE_CLASS_REGISTRY`/general rules engine not cross-checked against `WORKFLOW_TRIGGER_REGISTRY` for overlapping responsibility | UNRESOLVED |
| MAP-U10 | No single centralized status/task/assessment registry exists; status logic is distributed across multiple engines | UNRESOLVED |

## Addendum Verification

- [x] Backend scanned via direct grep/view plus a dedicated background inventory pass covering models (114/114 by name), a representative sample of APIs (~40/97) and services (~30/203), all reviewed registries, enums, and jobs discovered.
- [x] Frontend scanned via a dedicated background inventory pass covering the full route table, all top-level pages, and a representative sample of forms/components/nav entries.
- [x] RNICA/HOPE/HUV/SFV/J2050-J2053 objects specifically cross-checked against both this document's own Amendment 1 and the pre-existing `docs/tenant-platform/RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`.
- [x] Discrepancy between this addendum's background-agent backend scan (which reported `WORKFLOW_TRIGGER_REGISTRY` as "not found") and direct verification (which found it at `form_registry.py:912`) was caught and corrected in this same pass — background-agent output is treated as a lead requiring direct confirmation, not as final evidence.
- [ ] Full row-by-row enumeration of all 1021 backend and 256 frontend files was not performed — this addendum is evidence-backed but representative, not exhaustive. Categories/counts below reflect this.
- [x] No new workflows, forms, models, APIs, registries, or enums were created.
- [x] No schema, migration, or application behavior change was made.
- [x] No new file was created — this addendum was appended to the existing `RNICA_REPOSITORY_SOURCE_OF_TRUTH_MAP.md`.

## Addendum Final Report

```text
BACKEND OBJECTS INVENTORIED:    ~230 (114 models + ~40 API routers + ~30 services + ~15 registries/enums/jobs; partial for services/APIs)
FRONTEND OBJECTS INVENTORIED:   ~70 (26 routes + ~35 pages/forms/components + navigation/feature-flag entries; partial for components/)
MATCHED:                        7 (RNICA, MSW ICA, SC ICA, POC, IDG, SFV, Billing)
BACKEND_ONLY:                   4 (HUV1, HUV2, guardrail_policies, clinical_workflow_map — unconfirmed)
FRONTEND_ONLY:                  0 identified in this pass
PARTIAL:                        5 (RNRecertAssessment, HOPE workflow surface, Amendment, RnicaAmendment, SFV record-vs-rule split)
CONFLICTS:                      3 (MAP-C01, MAP-C02, MAP-C03)
DUPLICATE SSOT:                 4 (MAP-D01, MAP-D02, MAP-D03, MAP-D04)
LEGACY ITEMS CONFIRMED:         0 (6 UNCLEAR, none confirmed LEGACY or DEAD_CODE in this pass)

STOP CONDITION TRIGGERED:       YES — DUPLICATE_SSOT found (Discipline, Role/Permission, Form Registry, HUV/SFV trigger representation)
IMPLEMENTATION PLANNING:        NOT STARTED, per Stop Conditions
ROUTED FOR RESOLUTION:          Issue #121 (pending)

NEW FILES CREATED:               NO
NEW WORKFLOWS CREATED:           NO
NEW FORMS CREATED:               NO
NEW MODELS CREATED:              NO
NEW APIS CREATED:                NO
NEW REGISTRIES CREATED:          NO
NEW ENUMS CREATED:               NO
SCHEMA MODIFIED:                 NO
MIGRATIONS MODIFIED:             NO
CODE CHANGES MADE:               NO
```
