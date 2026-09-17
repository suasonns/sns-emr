# Biller Platform Discovery Report

Phase 0 deliverable required by
`docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md`,
`docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`,
and `docs/biller-platform/BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md`
(Section 10, "Required Discovery Deliverable" — 25-entity list; Phase 0
exit gate).

**This report performs discovery only. No schema changes, migrations,
tables, or ORM models were created or modified while producing it.**

All evidence below was gathered by direct inspection of this
repository's source files and by executing `alembic heads` /
`alembic current` against the live dev database on
2026-09-17. File paths are relative to `backend/` unless noted.

---

## 1. Current Migration Head

```
$ python -m alembic heads
um2d1c2c3o5u9 (head)

$ python -m alembic current
[ALEMBIC] Using DATABASE_URL: ******localhost:5432/sns_emr_dev_clean
um2d1c2c3o5u9 (head)
```

- **Single head**: `um2d1c2c3o5u9` ("add_staff_status_and_permission_grants").
- **No schema drift**: the live `sns_emr_dev_clean` database's current
  revision exactly equals the code's single head. `alembic current`
  and `alembic heads` agree.
- No `alembic stamp` was used to reach this state; it was verified via
  the ordinary `alembic current` read against the running Postgres
  instance on `localhost:5432`.

## 2. Migration Lineage

- `alembic branches` shows one historical branch point:
  `p7q8r9s0t1u2` → (`q8r9s0t1u2v3`, `q1r2s3t4u5v6`).
- That branch converges back to a single lineage before the current
  head (the codebase has no second, unmerged head — `alembic heads`
  returns exactly one revision). No unresolved branch/merge exists
  today.
- Conclusion: the migration graph is linear at HEAD. Any new Biller
  Platform migrations must chain forward from `um2d1c2c3o5u9` with a
  single new head — no additional branching is introduced by this
  report.

## 3. Current Tenant Models

- `app/models/tenant.py` — `Tenant`. Has a `tenant_type` CHECK
  constraint restricting values to `PRODUCTION, TRAINING, DEV,
  PLATFORM, BILLING`, and a `billing_enabled` boolean flag. `PLATFORM`
  and `BILLING` tenant types exist specifically to exclude the
  platform-vendor tenant and the billing-organization-as-tenant record
  from the ordinary hospice-agency tenant list.
- `app/core/tenant_scope.py` — `list_billable_agency_tenants()` and
  `resolve_billing_scope_tenant_id()`. These are the functions behind
  the frontend `AgencyContext`/agency selector.

## 4. Current Patient Models

- `app/models/patient.py` — `Patient`, tenant-scoped via `tenant_id`
  FK, standard pattern used across all clinical/billing tables.
- `app/models/benefit_period.py` — hospice benefit-period tracking,
  used by `benefit_period_determination.py`.

## 5. Current Claim Models

- `app/billing/models/claim.py` — `Claim`. Real, persisted,
  tenant-scoped, one row per `(patient_id, billing_cycle_id)` pair
  (`uq_claim_patient_cycle`). Fields: `payer_name`, `service_date`,
  `total_charge` (`Numeric(12,2)`), `total_units`, `risk_score`,
  `status` (`READY / SENT / ACCEPTED / DENIED / PAID` — **5 stages**,
  mutated in place, no history table), `last_status_reason`,
  `claim_control_number`, `exported_at`. Links to
  `billing_cycle_id` (month/year cycle), not to a `benefit_period_id`
  — there is **no direct FK from Claim to a benefit period**.
- `app/billing/models/claim_edi_batch.py` — `ClaimEdiBatch`. One EDI
  837I submission event. Explicitly documented in its own docstring as
  "currently one claim per batch" — no batch-versioning, no
  claim-membership table, no prepared-by/reviewed-by/approval fields,
  no removal/exception tracking. Tracks 999/277CA `ack_status`
  (`PENDING/ACCEPTED/REJECTED/PARTIAL`).
- `app/billing/models/billing_cycle.py` — `BillingCycle`. Tenant-scoped
  month/year period with `OPEN/CLOSED/LOCKED` status; unique per
  `(tenant_id, month, year)`.
- `app/billing/validators/claim_validator.py` — `validate_claim()`.
  Stateless, in-memory function over an export payload dict; returns
  `{errors, warnings}`. **Not a persisted record** — no history, no
  audit trail, no linkage to a claim ID in the database.
- `app/billing/models/denial.py` — `Denial`, tenant-scoped denial
  tracking linked to claims.
- `app/billing/models/payment.py` — `Payment`, tenant-scoped payment
  posting.
- No dedicated "Claim Lifecycle Event" table exists anywhere —
  `Claim.status` and `Claim.last_status_reason` are overwritten in
  place on each transition.

## 6. Current Eligibility Models

- `app/billing/models/eligibility_verification.py` —
  `EligibilityVerification`. Tenant-scoped, references
  `benefit_period` concepts; persisted eligibility-check results.

## 7. Current NOE Models

- `app/billing/models/noe_edi_submission.py` — `NoeEdiSubmission`.
  Tenant-scoped NOE (Notice of Election) EDI submission tracking,
  references `benefit_period`.

## 8. Current Audit Models

- `app/models/audit_log.py` — `AuditLog` (extends `TenantScopedMixin`,
  `BaseModel`). Fields: `tenant_id`, `request_id` (UUID, indexed —
  usable as a correlation ID), `ip_address`, `user_id` FK, `role`,
  `action`, `entity_type`, `entity_id`, `description`, `event_metadata`
  (JSON, DB column `metadata`), `created_at` (DB-controlled,
  server-default `now()`). No explicit `previous_state`/`new_state`
  columns — these would be carried inside `event_metadata` JSON today.
  This is a general-purpose, already-wired audit sink used across the
  application (not billing-specific).
- `app/billing/models/readiness_workflow_event.py` —
  `ReadinessWorkflowEvent`. Billing-readiness-specific, append-only,
  actor-attributed, with `previous_state`/`new_state` JSONB snapshot
  columns — richer than `AuditLog` for readiness-specific transitions.

## 9. Current Billing Models

Located in `app/billing/models/` (~35 files). Most relevant to this
discovery:

- `billing_provider_organization.py` — `BillingProviderOrganization`.
- `billing_provider_organization_membership.py` —
  `BillingProviderOrganizationMembership`.
- `billing_provider_agency_assignment.py` —
  `BillingProviderAgencyAssignment` +
  `BillingProviderAgencyServiceScope` (per-scope VIEW/EDIT
  permissions).
- `billing_readiness_verdict.py` — `BillingReadinessVerdict`
  (immutable, append-only, JSONB blockers/warnings, `evidence_hash`
  dedup).
- `billing_blocker_record.py` — `BillingBlockerRecord` (typed blocker
  lifecycle: `workflow_owner_category`, `blocker_code`,
  `source_document_id`, OPEN/RESOLVED status).
- `readiness_assignment.py` — `ReadinessAssignment` (generic,
  documented as dev-scaffolding, not agency/biller-specific).
- `readiness_follow_up.py` — `ReadinessFollowUp` (OPEN / IN_PROGRESS /
  BLOCKED / RESOLVED / CANCELLED work-item tracking with due dates,
  tenant- and patient-scoped, optional link to a `readiness_assignment`).
- `readiness_workflow_event.py` — `ReadinessWorkflowEvent` (see §8).
- `remittance_advice.py`, `credit_balance_case.py`,
  `facility_collection_alert.py` — additional billing-operations
  models supporting Aging Report / Credit Balance Report / Facility
  Collections pages (not part of the 25-entity list; noted for
  completeness).
- `app/billing/services/readiness_dashboard_service.py` — existing,
  mature dashboard/queue/history read-model layer computing
  **patient/claim counts** by READY/AT_RISK/NOT_READY/BLOCKED. Does
  **not** compute dollar revenue amounts.
- `app/billing/services/revenue_service.py` — Decimal-based rate/fee
  schedule estimator. Not a revenue-event ledger.

## 10. Current DDE Models

**None exist.** A precise, word-boundary grep
(`\bDDE\b|direct_data_entry|DirectDataEntry|fiss.?dde|FISS`) across the
entire backend returns only false positives inside static ICD-10 text
data files. There are no DDE models, no DDE routes, no DDE UI
components, and no DDE-related database columns anywhere in the
repository.

## 11. Current Route Structure

Backend, under `app/billing/api/` (existing, mounted routers):

- `/billing/agencies` — agency/tenant selector, backed by
  `list_billable_agency_tenants()` (see §12 finding).
- `/billing/tenants`
- `/billing/readiness-dashboard`
- `/billing/readiness-queue`
- `/billing/readiness-history/{patient_id}`
- `/billing/queue`
- `/billing/claims`
- `/billing/denials`
- `/billing/audit-history`
- `/billing/facility-payments/*`
- `/billing/credit-balance/*`
- `/billing/noe-tracking`
- `/billing/eligibility-roster`
- `/billing/remittances`
- `/billing/aging-report`
- `/billing/poc-certification-status`

Under `app/api/owner/` (Owner Platform prefix):

- `/api/owner/billing-providers/organizations`
- `/api/owner/billing-providers/assignments`

**Observation**: billing-provider organization/assignment *management*
endpoints currently live under the Owner Platform's `/api/owner/`
prefix, while operational billing endpoints live under `/billing/`.
This is consistent with the documented split ("Owner Platform assigns
billers; Biller Platform operates the assignment") but is called out
here as an observed fact for review, not assumed to be a defect.

## 12. Current API / Frontend Structure

- `sns-emr-frontend/src/App.tsx` — existing `/billing` route tree
  gated by `RequireFeatureAccess feature="billing"`, wrapping
  `BillerShell`. Child routes include `dashboard`
  (`BillingOverviewPage`) and `readiness` (`ReadinessWorkflowPage`),
  plus claims/denials/eligibility/payment-posting/NOE-tracking/
  credit-balance/facility-collections/aging-report/reports pages, and
  (still present today) `visits-notes` and `poc-certification` child
  routes — the latter two are already directed for removal per
  `TENANT_BILLER_DASHBOARD_SPECIFICATION.md`'s amended Remove list and
  `BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md`'s Clinical Boundary,
  but have **not** been removed from the frontend yet — this remains a
  separate, not-yet-authorized implementation task.
- `sns-emr-frontend/src/components/billing/AgencyContext.tsx` — the
  tenant/agency selector for the Biller's Dashboard; calls
  `/billing/agencies`.

**Critical finding (carried forward from investigation, most
significant discovery-report item):**
`app/core/tenant_scope.py::list_billable_agency_tenants()` returns
**every** non-`PLATFORM`/non-`BILLING` tenant — it does **not** filter
by `billing_provider_agency_assignments`.
`resolve_billing_scope_tenant_id()` only rejects a manually-supplied
`tenant_id` if it is a `PLATFORM`/`BILLING` tenant type; it does not
verify the tenant is actually assigned to the current user's billing
organization. `app/core/roles.py::access_scope_for_role()` grants
`"billing"` scope purely by role membership
(`BILLING, BILLING_MANAGER, BILLING_SPECIALIST, COLLECTIONS,
REVENUE_CYCLE`) with no tie to
`BillingProviderOrganizationMembership` or
`BillingProviderAgencyAssignment`. **Net effect: any user with a
billing-family role can currently select and view any agency tenant**
via `/billing/agencies`, directly contradicting the "visibility follows
assignment" Locked Access Principle repeated across every Biller
Platform specification in this repository, despite the assignment
tables already existing in the schema to enforce it. This is a
blocking finding for Phase 1 (Access and Assignment Foundation) and
must be remediated before or as part of that phase.

---

## 13. Discovery Matrix — 25 Logical Entities

Columns per
`BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md` §10: Logical
Requirement, Existing Model, Existing Table, Decision, Reason, Files
Affected. ("Existing Fields/Constraints/Indexes/API/UI" are folded
into Reason/Files Affected per entity for readability; no repository
model names are fabricated — entries marked "None" were confirmed
absent by direct search.)

| # | Logical Requirement | Existing Model / Table | Decision | Reason | Files Affected (if implemented) |
|---|---|---|---|---|---|
| 1 | Billing Organization | `BillingProviderOrganization` / `billing_provider_organizations` | **REUSE** | Already models a named billing organization (e.g. would carry "North East Billing Center"). No conflicting fields found. | `app/billing/models/billing_provider_organization.py` |
| 2 | Billing Organization Membership | `BillingProviderOrganizationMembership` / `billing_provider_organization_memberships` | **REUSE** | Already links a user to a billing organization with membership semantics. | `app/billing/models/billing_provider_organization_membership.py` |
| 3 | Tenant Billing Assignment | `BillingProviderAgencyAssignment` + `BillingProviderAgencyServiceScope` / `billing_provider_agency_assignments`, `billing_provider_agency_service_scopes` | **REUSE / EXTEND** | Already links a billing organization to an agency tenant, with per-scope VIEW/EDIT granularity beyond what the spec assumed. Must be EXTENDed to actually be enforced in `tenant_scope.py` (see §12 finding) — a query/service-layer change, not a schema change. | `app/billing/models/billing_provider_agency_assignment.py`, `app/core/tenant_scope.py`, `app/core/roles.py` |
| 4 | Individual Tenant Biller Assignment | None found distinct from org-level membership | **CREATE** | No table associates one specific user with one specific assigned agency (only org-to-agency and user-to-org exist). Required for "Individual Tenant Biller Assignment," "Assignment Accountability," and per-user DDE scoping. | New model + migration (not created by this report) |
| 5 | Individual DDE User Profile | None | **CREATE** | Confirmed absent via precise word-boundary grep across the entire backend. No DDE infrastructure exists. | New model + migration (not created by this report) |
| 6 | DDE Tenant Authorization | None | **CREATE** | Same as above — no per-tenant DDE authorization concept exists anywhere. | New model + migration (not created by this report) |
| 7 | Billable Episode | No dedicated model; `Claim` conflates "episode" and "claim" via `(patient_id, billing_cycle_id)` uniqueness | **EXTEND** | `Claim` + `BillingCycle` already establish one authoritative unit per patient per cycle, satisfying most of the "one authoritative billable unit" requirement from Epic 03. A distinct "Billable Episode" wrapper is not clearly needed; recommend formalizing `Claim` as the authoritative billable unit rather than creating a parallel entity, pending Phase 3 review. | `app/billing/models/claim.py`, `app/billing/models/billing_cycle.py` |
| 8 | Claim | `Claim` / `claims` | **REUSE** | Real, persisted, tenant-scoped claim record already exists with monetary `Numeric(12,2)` precision (no float). | `app/billing/models/claim.py` |
| 9 | Claim Validation | `validate_claim()` in `app/billing/validators/claim_validator.py` | **CREATE** | Existing function is stateless and in-memory (operates on an export payload dict); it is not a persisted, auditable, historical validation record as required by Epic 06/10. The existing field-level checks (missing patient ID, missing revenue code, etc.) can inform the new persisted model's logic, but the model itself must be created. | New model + migration (not created by this report) |
| 10 | Claim Lifecycle Event | None — `Claim.status` is mutated in place | **CREATE** | No append-only lifecycle-transition history table exists. `Claim.status` (5 values: READY/SENT/ACCEPTED/DENIED/PAID) is overwritten directly, which cannot satisfy the locked 8-stage lifecycle, Claim Status Timeline, or "no rewritten history" requirements. | New model + migration (not created by this report) |
| 11 | Claim Batch | `ClaimEdiBatch` / `claim_edi_batches` | **EXTEND** | Already a real, tenant-scoped batch/submission record with `ack_status` tracking (999/277CA). However its own docstring states it is "currently one claim per batch" — no true multi-claim batch, no versioning, no prepared-by/reviewed-by/approval fields. Must be extended (or paired with new membership/version tables) to support the locked Batch Management workflow. | `app/billing/models/claim_edi_batch.py` |
| 12 | Claim Batch Version | None | **CREATE** | No versioning concept exists on `ClaimEdiBatch`; batch amount/claim-count are plain columns updated in place, not append-only versions. Required for the locked non-destructive Batch Revision Rule (v1 → v2 → v3). | New model + migration (not created by this report) |
| 13 | Claim Batch Membership | Implicit only via `Claim.edi_batch_id` FK (one claim → one batch, no history) | **CREATE** | The current FK is a simple one-to-many pointer with no membership history, no "removed from batch" state, and no support for a claim moving between batch versions. A proper join/membership table is required. | New model + migration (not created by this report) |
| 14 | Batch Exception | None | **CREATE** | No table tracks claims removed from a batch, removal reason, removed-by, or returned status. Required for the locked Batch Exception Queue. | New model + migration (not created by this report) |
| 15 | Batch Review | None | **CREATE** | `ClaimEdiBatch` has no `prepared_by`, `reviewed_by`, or approval-status fields. Required for the locked multi-layer review (Prepared By / Reviewed By / Submission Approval Status). | New model + migration (not created by this report) |
| 16 | Validation Override | None | **CREATE** | Confirmed absent via grep for `Override`/`Validation` model classes. Required for the locked, immutable Validation Override History (released-by, reason, timestamp, audit status), distinct from the blocker record itself so the original blocker is never overwritten. | New model + migration (not created by this report) |
| 17 | Readiness Evaluation | `BillingReadinessVerdict` / `billing_readiness_verdicts` | **REUSE** | Already immutable, append-only, with JSONB blockers/warnings and `evidence_hash` deduplication — matches the "immutable readiness evaluations" requirement closely. | `app/billing/models/billing_readiness_verdict.py` |
| 18 | Readiness Condition | `BillingBlockerRecord` / `billing_blocker_records` | **REUSE / EXTEND** | Already has a typed blocker lifecycle (`blocker_code`, `workflow_owner_category`, OPEN/RESOLVED status, `source_document_id` evidence link). Would need EXTENSION to add DDE-specific blocker codes (DDE Verification Required, DDE Eligibility Conflict, DDE Response Pending, DDE Status Unknown, DDE Submission Failure) once DDE entities exist. | `app/billing/models/billing_blocker_record.py` |
| 19 | Readiness Evidence Reference | `source_document_id` field on `BillingBlockerRecord`; no dedicated evidence-reference model | **EXTEND / CREATE** | A single FK-style pointer exists on the blocker record, but there is no standalone, reusable "evidence reference" entity that could be attached to multiple condition types (readiness, validation override, DDE event) or carry provenance metadata (source system, retrieved-at, hash). Recommend a small new join-style entity rather than overloading `BillingBlockerRecord`. | New model + migration, or extension of `billing_blocker_record.py` (not created by this report) |
| 20 | Readiness Action | `ReadinessWorkflowEvent` / `readiness_workflow_events` | **REUSE** | Already append-only, actor-attributed, with `previous_state`/`new_state` JSONB snapshots — matches "Readiness Action" directly. | `app/billing/models/readiness_workflow_event.py` |
| 21 | Billing Work Item | `ReadinessFollowUp` (+ `ReadinessAssignment`) / `readiness_follow_ups`, `readiness_assignments` | **REUSE / EXTEND** | `ReadinessFollowUp` already provides OPEN/IN_PROGRESS/BLOCKED/RESOLVED/CANCELLED work-item tracking with due dates, tenant- and patient-scoped. `ReadinessAssignment` is explicitly documented as generic dev-scaffolding, not agency/biller-specific — would need EXTENSION (or the new Individual Tenant Biller Assignment entity, #4) to represent per-biller work-item ownership for Assignment Accountability. | `app/billing/models/readiness_follow_up.py`, `app/billing/models/readiness_assignment.py` |
| 22 | Revenue Event | None | **CREATE** | No append-only revenue-event ledger exists. `revenue_service.py` is a Decimal-based rate/fee-schedule estimator, not an event ledger; `Claim.total_charge`/`status` are point-in-time mutable fields, not events. Required to satisfy "Revenue Released" audit semantics (availability-to-progress is distinct from payment) and Dashboard/Readiness calculation-service parity (Epic 03). | New model + migration (not created by this report) |
| 23 | DDE Operational Event | None | **CREATE** | No DDE infrastructure exists at all (see §10). | New model + migration (not created by this report) |
| 24 | Regulatory Reference | None | **CREATE** | No dedicated model found (`app/api/regulatory/reports.py` and `app/services/regulatory_report_service.py` are report-generation code, not a persisted citation-reference table). Required so the system "does not invent regulatory citations" and only cites from an approved reference set. | New model + migration (not created by this report) |
| 25 | Audit Event | `AuditLog` / `audit_logs` | **REUSE** | General-purpose, already-wired audit sink with tenant, actor (`user_id`/`role`), `action`, `entity_type`/`entity_id`, `description`, `event_metadata` JSON, and `request_id` (usable as correlation ID). No explicit `previous_state`/`new_state` columns — these would need to be carried inside `event_metadata` JSON, or the more purpose-built `ReadinessWorkflowEvent` pattern (which has explicit JSONB snapshot columns) could be followed for new Biller Platform event types instead of overloading `AuditLog`. | `app/models/audit_log.py` |

### Summary counts

| Decision | Count | Entities |
|---|---|---|
| REUSE | 6 | Billing Organization, Billing Organization Membership, Claim, Readiness Evaluation, Readiness Action, Audit Event |
| REUSE / EXTEND | 4 | Tenant Billing Assignment, Readiness Condition, Billing Work Item, Billable Episode (listed as EXTEND alone) |
| EXTEND | 2 | Billable Episode, Claim Batch |
| EXTEND / CREATE | 1 | Readiness Evidence Reference |
| CREATE | 12 | Individual Tenant Biller Assignment, Individual DDE User Profile, DDE Tenant Authorization, Claim Validation, Claim Lifecycle Event, Claim Batch Version, Claim Batch Membership, Batch Exception, Batch Review, Validation Override, Revenue Event, DDE Operational Event, Regulatory Reference |

**13 of 25 entities (52%) require net-new tables.** The remaining 12
either reuse existing, already-production-grade models directly, or
require targeted extension of existing models/services rather than
new tables. This substantially reduces the true "from scratch" build
scope versus a naive reading of the specifications, while confirming
that the entire Claims Batch Management workflow (Epic 08) and all DDE
functionality (Epic 02) are genuinely net-new.

---

## 14. Blocking Findings Before Any Schema Work

1. **Assignment enforcement gap** (§12): `list_billable_agency_tenants()`
   and `resolve_billing_scope_tenant_id()` do not filter by
   `billing_provider_agency_assignments`; `access_scope_for_role()`
   grants billing access purely by role name. This must be resolved as
   part of Phase 1 (Access and Assignment Foundation) — it is a
   pre-existing security gap, not something introduced by this report.
2. **No append-only ledger for money**: neither `Claim` nor
   `ClaimEdiBatch` nor `revenue_service.py` provide an event-sourced
   Revenue Event ledger; Dashboard and Readiness currently compute
   patient/claim *counts*, not reconciled dollar totals from a single
   authoritative source. This must be resolved in Phase 3
   (Authoritative Revenue Foundation) before Phase 4/6 (Readiness
   Engine / Dashboard) can safely display revenue figures that are
   guaranteed to agree between the two pages.
3. **Claim Batch is single-claim-per-batch today**: `ClaimEdiBatch`'s
   own docstring documents this as a known limitation. The entire
   locked Batch Management workflow (Epic 08) — multi-claim batches,
   versioning, review layers, removal/exception queue — requires new
   entities (#12-15 above) and, likely, a compatibility decision about
   whether `ClaimEdiBatch` becomes the "batch version" record or is
   wrapped by a new `ClaimBatch` parent entity. This decision should be
   made explicitly in Phase 9 planning, not silently during
   implementation.
4. **No DDE anything**: all of Epic 02 (Individual DDE Authorization)
   is genuinely net-new — 3 of the 25 entities (#5, #6, #23) plus every
   DDE-specific blocker code on entity #18.

## 15. What This Report Does Not Do

- Does not create any table, column, index, constraint, or migration.
- Does not modify any existing model file.
- Does not decide the exact column-level shape of any CREATE entity —
  only that a new persisted entity is required and why.
- Does not resolve the Batch/Batch-Version compatibility question in
  Finding 3 — that decision is reserved for Phase 9 planning review.

---

## Status

Discovery Report complete. All 25 logical entities named in
`BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md` §10 have been
classified as REUSE, EXTEND, REUSE/EXTEND, EXTEND/CREATE, or CREATE
with direct repository file evidence, current Alembic head/lineage has
been verified against the live database with no drift, and four
blocking findings have been surfaced for review before any schema or
migration work begins. Per explicit instruction, **no schema
implementation, migrations, tables, or models were created while
producing this report** — the classifications above must be reviewed
and the mappings approved before Phase 1 (or any later phase)
authorizes actual schema changes.

## Relationship to Other Documents

- Fulfills the Phase 0 exit gate defined in
  `docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md`
  and `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`,
  and the Required Discovery Deliverable named in
  `docs/biller-platform/BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md`
  §10, using that document's expanded 25-entity list (which supersedes
  the original 15-entity list from the earlier "PHASE 0 DELIVERABLE
  REQUIRED" instruction).
- The assignment-enforcement gap (§12/§14.1) is the discovery-report
  evidence behind the Assignment Rule and Epic 01 acceptance criteria
  in `BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md` and
  `BILLER_PLATFORM_IMPLEMENTATION_HANDOFF.md`.
- The Claim Batch single-claim-per-batch limitation (§14.3) is the
  discovery-report evidence behind the Batch Management, Batch
  Revision, and Batch Exception Queue rules in the same two documents.
- The absence of any DDE model (§10, §14.4) is the discovery-report
  evidence behind the DDE Architecture sections in
  `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`,
  `BILLER_PLATFORM_FINAL_IMPLEMENTATION_BRIEF.md`, and
  `BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md`.
- Next required deliverable per the Phased Implementation Plan is
  Phase 1 (Access and Assignment Foundation) — but per explicit
  instruction, that work is **not authorized to begin** until this
  report's mappings are reviewed and schema changes are separately
  approved.

## Change Log

| Date | Change |
|---|---|
| 2026-09-17 | Document created — completed Phase 0 Discovery Report: current migration head/lineage verification (no drift), current tenant/patient/claim/eligibility/NOE/audit/billing/DDE model inventory, current route/API/frontend structure, and a full REUSE/EXTEND/CREATE discovery matrix for all 25 logical entities from `BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md` §10, with repository file evidence for every classification. Surfaced four blocking findings (assignment-enforcement gap, missing revenue-event ledger, single-claim-per-batch limitation, complete absence of DDE infrastructure) for review before any schema or migration work is authorized. No schema, migrations, tables, or models were created. |
