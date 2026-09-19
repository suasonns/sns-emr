# Tenant and Biller Platform System-of-Record Matrix

## Status

CURRENT PHASE: Tenant Platform, Biller Platform, and Legacy Billing
Schema Discovery

DOCUMENTATION ONLY. IMPLEMENTATION BLOCKED.

This is a full replacement of the prior version of this document,
issued to correct two problems in that version:

1. It occasionally implied Shared Domain ownership or asserted a
   CREATE decision without first exhausting whether an existing
   structure already covers the concept under a different name.
2. It did not carry an explicit Ownership Status field, so ownership
   could be read as more settled than the repository evidence
   supports.

## Hard Rules Applied Throughout This Document

- One authoritative record per business fact.
- Ownership defaults to **UNRESOLVED** unless repository evidence
  proves TENANT OWNED, BILLER OWNED, SHARED DOMAIN OWNED, or LEGACY
  AUTHORITY. A Shared Billing Domain is never assumed to exist.
- A proposed model is never reported as existing.
- Every REUSE claim carries a file-path citation.
- Different names do not prove different business concepts. Where a
  proposed entity would only rename an existing structure without
  adding a distinct business purpose, the decision is **DO NOT
  CREATE**, not CREATE — per the explicit prohibition: *"Creating a
  new entity whose only purpose is to provide a cleaner name for an
  existing table"* is not authorized (examples given: `PatientCoverage`
  when `PatientInsurance` already owns coverage; `PayerOrganization`
  when `Payer` already owns payer identity; `ClaimPayerRelationship`
  when an existing relationship already owns payer linkage).
- Patient Coverage is treated as a **logical concept**, not a physical
  model, until `PatientInsurance` vs. `PatientPayer` is resolved
  (deferred to the dedicated comparison document, per instruction).
- Billing Responsibility may only own service-, date-, claim-, or
  workflow-specific responsibility determination. It can never become
  the system of record for insurance coverage.
- Claim Category, Payer Organization, Plan/Product, Benefit/Program,
  Patient Coverage, Billing Responsibility, and Billing-company
  Coverage Assignment are kept strictly separate below.

## Decision Vocabulary (used exactly as specified)

REUSE, EXTEND, LINK, CONSOLIDATE, CREATE, DO NOT CREATE, RETIRE AFTER
VERIFIED REPLACEMENT, FURTHER INVESTIGATION.

## Ownership Status Vocabulary (used exactly as specified)

TENANT OWNED, BILLER OWNED, SHARED DOMAIN OWNED, LEGACY AUTHORITY,
OWNERSHIP UNRESOLVED (the value previously written as `UNRESOLVED`
throughout this document is the same value as `OWNERSHIP UNRESOLVED`;
both spellings are used interchangeably below and refer to one
vocabulary term).

**SHARED DOMAIN OWNED evidence bar.** A concept may only be classified
SHARED DOMAIN OWNED when repository evidence shows all four of the
following. If any one is missing, the correct classification is
OWNERSHIP UNRESOLVED (or TENANT OWNED / BILLER OWNED / LEGACY AUTHORITY,
if evidence otherwise supports single-platform ownership) — never
SHARED DOMAIN OWNED by default:

1. The table is intentionally shared across platforms (a documented or
   code-level design decision, not incidental reuse).
2. Tenant and Biller consumers reference the same authoritative record
   (a verified Biller Platform consumer must exist).
3. Write authority is defined (which platform/role may write, under
   what conditions).
4. Scope enforcement is defined (tenant/agency/billing-organization
   isolation rules for the shared record).
5. No competing writable copy exists elsewhere.

No concept in this document currently satisfies all five conditions,
because no Biller Platform consumer of any Tenant-owned billing table
has been found. See "Ownership Correction Log" below for the
concept-by-concept test result.

## Method

Every entry reflects direct inspection of `backend/app/models/`,
`backend/app/billing/models/`, `backend/app/billing/services/`,
`backend/app/billing/api/`, `backend/app/api/`, and
`sns-emr-frontend/src/`, plus the completed background-agent consumer
sweep. Fields marked "not verified in this pass" are genuine open
items, not filled in with assumptions.

---

### Concept: Patient Identity

Tenant Platform model and table: `Patient` / `patients`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: `patients` (consumed by both clinical and billing code via FK)
Current verified system of record: `Patient`
Ownership status: TENANT OWNED — CORRECTED. No Biller Platform consumer of `Patient` exists today (the only real cross-platform consumer, `BillingProviderOrganization`/`BillingProviderAgencyAssignment`, references tenant/agency identity, not `Patient` directly). "Shared" was previously asserted based on cross-*module* (clinical + billing) consumption within the single Tenant Platform, not cross-*platform* consumption — this does not meet the bar for SHARED DOMAIN OWNED under the rule that a Shared Billing Domain must not be assumed. Reclassified to TENANT OWNED; would become a genuine SHARED DOMAIN OWNED candidate only once a Biller Platform consumer is built and verified.
Owning organization: tenant hospice agency
Owning platform: shared
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none (a future Biller Platform must access this record via authorized reference, not copy it)
Patient scope: n/a (is the patient record)
Current fields: standard identity/demographic fields (not itemized — out of scope for a billing-only sweep)
Relationships: FK target of `PatientInsurance`, `PatientPayer`, `Claim`, `ServiceCoverageDecision`, `FacilityPaymentExpectation`
Consumers: entire application
APIs: `app/api/patients.py` and broader clinical API surface
Frontend consumers: entire application
Background jobs: none billing-specific
Reports and exports: appears as a reference in nearly all billing reports
Existing data exposure: not queried (production data, not itemized)
Duplicate data present: none
Missing relationships: none identified for billing purposes
Missing constraints: none identified
Missing history: standard audit trail via `AuditLog` where applicable
Decision: REUSE
Reason: single, unambiguous, universally-consumed identity record; no competing model exists.
Repository evidence: FK references confirmed in `patient_insurance.py`, `patient_payer.py`, `app/billing/models/claim.py`, `service_coverage_decision.py`, `facility_payment_expectation.py`
Migration exposure: none proposed
Backfill exposure: none proposed
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified

---

### Concept: Hospice Episode

Tenant Platform model and table: not located within this billing-focused sweep
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: unresolved
Current verified system of record: UNRESOLVED — this billing-discovery pass examined billing-domain files only; the authoritative episode/admission model was not directly inspected and must not be guessed at.
Ownership status: UNRESOLVED
Owning organization: expected tenant hospice agency, not verified
Owning platform: expected Tenant Platform, not verified
Tenant scope: expected yes, not verified
Agency scope: expected yes, not verified
Billing-organization scope: expected none, not verified
Patient scope: expected yes, not verified
Current fields: unresolved
Relationships: unresolved
Consumers: NOE/CAP billing calculations reference episode/benefit-period concepts by date range in the services already reviewed, but the model backing those dates was not independently confirmed in this pass
APIs: unresolved
Frontend consumers: unresolved
Background jobs: unresolved
Reports and exports: unresolved
Existing data exposure: unresolved
Duplicate data present: unresolved
Missing relationships: unresolved
Missing constraints: unresolved
Missing history: unresolved
Decision: FURTHER INVESTIGATION
Reason: a dedicated clinical-schema pass is required before any REUSE/EXTEND/CREATE decision can be made honestly.
Repository evidence: none collected for this concept in this pass
Migration exposure: unresolved
Backfill exposure: unresolved
Historical-preservation requirements: unresolved
Open defects: flagged as a genuine open item
Confidence: Unverified

---

### Concept: Payer Organization

Tenant Platform model and table: `Payer` / `payers`
Biller Platform model and table: `app.billing.models.payer` is an intentional re-export stub of `app.models.payer.Payer` — not a second model or table
Legacy model and table: none
Existing shared model and table: `payers`
Current verified system of record: `Payer`
Ownership status: TENANT OWNED — CORRECTED. `Payer` has no verified Biller Platform consumer; its only confirmed consumer (`Contract`) is Tenant-Platform-scoped billing code. Reclassified from SHARED DOMAIN OWNED (which incorrectly treated same-platform module reuse as cross-platform sharing) to TENANT OWNED. Would become SHARED DOMAIN OWNED only when a verified Biller Platform consumer exists.
Owning organization: platform-wide catalog
Owning platform: shared
Tenant scope: consuming records are tenant-scoped; the catalog itself is not
Agency scope: n/a at catalog level
Billing-organization scope: none
Patient scope: n/a
Current fields: not itemized beyond the confirmed FK relationship
Relationships: FK'd by `Contract.payer_id` (`app/billing/models/contract.py:38-40,74`)
Consumers: `Contract` model/service
APIs: none found exposing `Payer` CRUD to biller-facing pages
Frontend consumers: none confirmed
Background jobs: none confirmed
Reports and exports: none confirmed
Existing data exposure: not queried
Duplicate data present: none — the re-export pattern explicitly prevents duplicate ORM definitions (per that file's own docstring)
Missing relationships: no FK exists today from `Claim`, `PatientPayer`, or `PatientInsurance` to `Payer` — these currently store free text or their own identity
Missing constraints: n/a
Missing history: n/a
Decision: REUSE
Reason: `Payer` is a real, working, single-table payer-identity catalog. A proposed "Payer Organization" entity would only be a cleaner name for this existing table and is therefore **prohibited as a new entity** under the naming rule; any additional business purpose (e.g., licensing/contracting attributes) should be pursued as EXTEND of `Payer`, not as a new root entity.
Repository evidence: `backend/app/models/payer.py`; `backend/app/billing/models/payer.py` (re-export docstring); `backend/app/billing/models/contract.py:38-40,74`
Migration exposure: any EXTEND is additive
Backfill exposure: none for reuse
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified

---

### Concept: Payer Plan

Tenant Platform model and table: none found
Biller Platform model and table: none found
Legacy model and table: none found
Existing shared model and table: none exists
Current verified system of record: none — no plan/product/benefit-plan/program catalog exists anywhere in the repository
Ownership status: UNRESOLVED (nothing to own)
Owning organization: n/a
Owning platform: n/a
Tenant scope: n/a
Agency scope: n/a
Billing-organization scope: n/a
Patient scope: n/a
Current fields: n/a
Relationships: n/a
Consumers: n/a
APIs: n/a
Frontend consumers: n/a
Background jobs: n/a
Reports and exports: n/a
Existing data exposure: none — no table exists
Duplicate data present: none — nothing to duplicate
Missing relationships: a Plan-to-Payer relationship is absent because Plan itself is absent
Missing constraints: n/a
Missing history: n/a
Decision: TENTATIVE CREATE (only if/when Payer/Plan design phase resumes, and only after this entry is reviewed) — this is a genuine new business concept (a plan/product is not merely a renamed payer), so the naming-prohibition rule does not block it. No authoritative equivalent was found during the current repository search. Creation is not approved until the Legacy Billing Schema Inventory confirms that no historical, inactive, archived, or differently named equivalent exists.
Reason: targeted searches for plan/product/insurance-plan/benefit-plan/program model classes returned no matches.
Repository evidence: absence confirmed via repository-wide search of `backend/app/models/` and `backend/app/billing/models/`
Migration exposure: none today
Backfill exposure: none today
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified (as an absence finding)

---

### Concept: PatientInsurance

Tenant Platform model and table: `PatientInsurance` / `patient_insurances`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none — single model
Current verified system of record: eligibility-workflow system of record
Repository Location: Tenant-scoped implementation — `backend/app/models/patient_insurance.py`, consumed only by tenant-scoped eligibility workflow code.
Ownership: OWNERSHIP UNRESOLVED. Repository location (where the code lives, which platform's routers/services touch it today) is distinct from system-of-record authority over the Patient Coverage business concept — the latter is not decided here per instruction. Pending `PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform
Tenant scope: yes
Agency scope: yes (via patient)
Billing-organization scope: none
Patient scope: yes (FK to `Patient`)
Current fields: fields sufficient to drive eligibility checks (not itemized field-by-field)
Relationships: FK'd by `PayerEligibilityCheck` and `EligibilityVerification`
Consumers: `eligibility_check_router.py`, `eligibility_workflow_service.py`; frontend `EligibilityVerificationPage.tsx`
APIs: eligibility-check endpoints only — **no direct CRUD API for `PatientInsurance` itself was found**
Frontend consumers: `EligibilityVerificationPage.tsx`
Background jobs: none confirmed beyond eligibility workflow triggers
Reports and exports: feeds `readiness_dashboard_service.py`
Existing data exposure: not queried
Duplicate data present: see Patient Coverage (below) and the dedicated PatientInsurance-vs-PatientPayer comparison
Missing relationships: no FK to `PatientPayer`
Missing constraints: n/a
Missing history: not verified
Decision: FURTHER INVESTIGATION for its ultimate relationship to `PatientPayer` (see dedicated comparison); REUSE as the eligibility-evidence system of record is not in question
Reason: real, active, authoritative for eligibility evidence; its relationship to `PatientPayer` is the genuinely open question, not its own validity.
Repository evidence: `backend/app/models/patient_insurance.py`; `eligibility_check_router.py`; `eligibility_workflow_service.py`
Migration exposure: a future FK link to `PatientPayer` would be additive
Backfill exposure: matching existing rows across the two models would require a reviewed backfill plan — not performed
Historical-preservation requirements: preserve as-is; no consolidation without separate review
Open defects: absence of direct CRUD API is a functional gap, not introduced by this discovery
Confidence: Verified

---

### Concept: PatientPayer

Tenant Platform model and table: `PatientPayer` / `patient_payers`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none — single model
Current verified system of record: billing/financial-responsibility system of record
Repository Location: Tenant-scoped implementation — `backend/app/models/patient_payer.py`, full CRUD only through tenant-scoped `app/api/patients.py`.
Ownership: OWNERSHIP UNRESOLVED. Repository location is distinct from system-of-record authority over the Patient Coverage business concept — the latter is not decided here per instruction. Pending `PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`. Note (newly verified): `PatientPayer` has no `tenant_id` column at all (unlike `PatientInsurance`, which is `TenantScopedMixin`) — its tenant scope is only implied indirectly through its `patient_id` FK to `Patient` (which is tenant-scoped). This is a materially different scoping mechanism between the two models and is treated as an open item, not assumed safe.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform
Tenant scope: yes
Agency scope: yes (via patient)
Billing-organization scope: none
Patient scope: yes (FK to `Patient`)
Current fields: payer sequencing/COB-relevant fields (not itemized field-by-field)
Relationships: FK target of `ServiceCoverageDecision.selected_payer_id`
Consumers: `app/api/patients.py` (direct CRUD, ~lines 3244-3389), `claim_financials.py`, `credit_balance_service.py`, `facility_payment_service.py`, `msp_validation_service.py`
APIs: `app/api/patients.py` — confirmed direct CRUD
Frontend consumers: indirect, via Claims/Credit-Balance/Facility-Payment pages calling the services above
Background jobs: none confirmed
Reports and exports: Credit Balance Report, Facility Collections Report
Existing data exposure: not queried
Duplicate data present: see Patient Coverage (below)
Missing relationships: no FK to `PatientInsurance`
Missing constraints: n/a
Missing history: not verified
Decision: FURTHER INVESTIGATION for its ultimate relationship to `PatientInsurance`; REUSE as the billing/financial system of record is not in question
Reason: actively CRUD'd, actively consumed by four services; correct REUSE target for billing/financial responsibility.
Repository evidence: `backend/app/models/patient_payer.py`; `backend/app/api/patients.py:3244-3389`; `claim_financials.py`; `credit_balance_service.py`; `facility_payment_service.py`; `msp_validation_service.py`; `service_coverage_decision.py`
Migration exposure: none for reuse; a future FK link to `PatientInsurance` would be additive
Backfill exposure: none for reuse; linking would require reviewed backfill
Historical-preservation requirements: preserve as-is
Open defects: none identified
Confidence: Verified

---

### Concept: Patient Coverage (logical concept)

Tenant Platform model and table: **no physical model — logical concept only**, currently represented across `PatientInsurance` (eligibility) and `PatientPayer` (financial responsibility)
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none unified
Current verified system of record: split — no single system of record
Ownership status: OWNERSHIP UNRESOLVED — explicitly not classified TENANT OWNED, BILLER OWNED, or SHARED DOMAIN OWNED until `PatientInsurance` vs. `PatientPayer` is resolved. Patient Coverage Authority is tracked as OWNERSHIP UNRESOLVED at the document level (see Status block at end) pending `PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`.
Owning organization: tenant hospice agency (both underlying models)
Owning platform: Tenant Platform (both underlying models)
Tenant scope: yes (both)
Agency scope: yes (both, via patient)
Billing-organization scope: none
Patient scope: yes (both, via patient)
Current fields: n/a — spans two models
Relationships: no FK connects the two underlying models
Consumers: see `PatientInsurance` and `PatientPayer` entries above
APIs: see above
Frontend consumers: see above
Background jobs: none confirmed
Reports and exports: see above
Existing data exposure: not queried
Duplicate data present: **yes — the core finding of this investigation.** `PatientInsurance` and `PatientPayer` can independently represent the same real-world payer relationship for the same patient with no cross-reference.
Missing relationships: no FK between `PatientInsurance` and `PatientPayer`
Missing constraints: no constraint prevents divergent payer data between the two models for the same patient/payer
Missing history: not verified
Decision: **DO NOT CREATE** a third "Patient Coverage" physical model. Patient Coverage remains a logical concept only. The correct decision (LINK vs. CONSOLIDATE) between `PatientInsurance` and `PatientPayer` is deferred to the dedicated comparison document, per instruction, and is not decided here.
Reason: a third model would add a third source of truth on top of an already-unresolved two-model split, and would also violate the naming-prohibition rule if its only purpose were a cleaner name for what one of the two existing models already does.
Repository evidence: see `PatientInsurance` and `PatientPayer` entries above
Migration exposure: high if consolidation is eventually chosen; low if LINK (additive FK) is chosen — not decided here
Backfill exposure: high if consolidation; moderate if LINK — not decided here
Historical-preservation requirements: whichever path is eventually chosen must preserve both models' existing rows and audit trail
Open defects: this is the single most material open item in the entire cross-platform investigation
Confidence: Verified (as a duplication finding); UNRESOLVED (as an ownership/consolidation decision)

---

### Concept: Eligibility Response

Tenant Platform model and table: `PayerEligibilityCheck` (`payer_eligibility_checks`) and `EligibilityVerification` (`eligibility_verifications`) — two real, active models with **different scope and purpose**, not confirmed simple duplicates on closer field-level inspection (see below)
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none unified
Current verified system of record: split between the two models — by design, not by accident, per the field-level evidence below
Ownership status: TENANT OWNED — verified: both consumed only by tenant-scoped eligibility workflow code; no Biller Platform consumer exists.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform
Tenant scope: yes (both — both carry their own `tenant_id` FK)
Agency scope: yes (both, via patient)
Billing-organization scope: none
Patient scope: `PayerEligibilityCheck` via `patient_insurance_id` only (indirect); `EligibilityVerification` via both a direct `patient_id` FK and an optional (`nullable=True`) `payer_coverage_id` FK to `patient_insurances`

**Purpose (verified from source):**
- `PayerEligibilityCheck` (`backend/app/billing/models/payer_eligibility_check.py`) is an audit-trail log of individual eligibility-check *attempts* against one `PatientInsurance` row — one row per check event (270/271-style or manually logged). Its own docstring states it "Extends `PatientInsurance` ... with an audit trail of every verification attempt and its result."
- `EligibilityVerification` (`backend/app/billing/models/eligibility_verification.py`) is a structured, document-sourced record of ~25 hospice-specific eligibility *findings* (Medicare Part A/B entitlement dates, Medicare Advantage enrollment, MSP applicability/type, crossover, QMB status, prior hospice election history, benefit-period history, home-health overlap), each stored as a tri-state envelope (`RETURNED` / `NOT_RETURNED` / `DOES_NOT_APPLY` / `UNKNOWN`) across three JSONB columns, explicitly to avoid collapsing "not returned" into a false negative. Every verification is traceable to a `source_document_id` FK (the document a human or parser read to produce it).

**Tables:** `payer_eligibility_checks` vs. `eligibility_verifications` — two distinct physical tables, not the same table under two names.

**PatientInsurance linkage:** `PayerEligibilityCheck.patient_insurance_id` is `nullable=False` (mandatory FK — every check belongs to exactly one coverage row). `EligibilityVerification.payer_coverage_id` is `nullable=True` (optional FK to the same `patient_insurances` table) — meaning an `EligibilityVerification` can exist without being tied to a specific `PatientInsurance` row at all, which is a structural difference, not an implementation gap.

**Result/status domain overlap:** `PayerEligibilityCheck.result_status` uses `ACTIVE / INACTIVE / UNKNOWN / ERROR` (mirrors `PatientInsurance.eligibility_status`, which its own `doc=` comment says is "set from the most recent `PayerEligibilityCheck`"). `EligibilityVerification.status` uses a materially different domain: `NOT_RUN / PENDING / VERIFIED_ACTIVE / VERIFIED_INACTIVE / COVERAGE_CONFLICT / REVIEW_REQUIRED / ERROR` — the module docstring explicitly warns this is "intentionally a *different* status domain" from other workflow statuses and instructs "do not conflate them." This is documented, deliberate non-overlap, not accidental duplication.

**Provenance:** `PayerEligibilityCheck` has no source-document requirement (`checked_by` is a free-text string). `EligibilityVerification` mandates `source_document_id` (FK, `nullable=False`) and `verified_by_user_id` (FK to `users`, `nullable=False`) — a stronger evidentiary chain.

**History/supersession:** `EligibilityVerification` is explicitly append-only (`superseded_at`, nullable, set only when a later verification supersedes an earlier one for the same patient+coverage — never deleted or overwritten, per its docstring, "Directive item 8"). `PayerEligibilityCheck` has no supersession field; whether older check rows are ever superseded or simply accumulate was not verified in this pass.

Consumers: `eligibility_check_router.py`, `eligibility_workflow_service.py`, `readiness_dashboard_service.py` (exact per-model consumer split not independently traced in this pass — both models' consumers were confirmed to exist, but which specific service calls which model line-by-line was not re-verified here)
APIs: eligibility-check endpoints
Frontend consumers: `EligibilityVerificationPage.tsx`
Background jobs: not confirmed
Reports and exports: readiness dashboard
Existing data exposure: not queried
Duplicate data present: **partially revised finding.** The two models were previously flagged as "overlapping purpose" without field-level verification. On field-level inspection, they are complementary, not duplicative: `PayerEligibilityCheck` is a lightweight per-attempt check log; `EligibilityVerification` is a richer, document-sourced, hospice-specific structured-findings record. The genuine overlap is narrow and specific: both carry an eligibility result/status concept referencing the same coverage, using two different status vocabularies, which creates a real risk of the two statuses disagreeing for the same patient/coverage at the same point in time. This narrower risk — not wholesale duplication — is the open item.
Missing relationships: n/a
Missing constraints: no constraint verified that prevents `PayerEligibilityCheck.result_status` and `EligibilityVerification.status` from disagreeing for the same coverage at the same time
Missing history: `EligibilityVerification`'s append-only supersession appears to already provide history; `PayerEligibilityCheck` history not verified
Decision: FURTHER INVESTIGATION (recommended authority not decided in this phase). Do not consolidate either structure during discovery, per instruction.
Reason: eligibility evidence must remain distinct from verified Patient Coverage or Billing Responsibility per the hard rules; this entry documents the evidence layer only and does not resolve the two-model relationship.
Repository evidence: `backend/app/billing/models/payer_eligibility_check.py`; `backend/app/billing/models/eligibility_verification.py`
Migration exposure: none proposed in this phase
Backfill exposure: none proposed in this phase
Historical-preservation requirements: preserve both models as-is pending future review
Open defects: potential status-domain disagreement between the two models for the same coverage, flagged for a future, separate discovery pass; Eligibility Result Authority tracked as OWNERSHIP UNRESOLVED at the document level (see Status block at end)
Confidence: Verified

---

### Concept: Billing Responsibility

Tenant Platform model and table: no dedicated generic model; closest analogs are `FacilityPaymentExpectation.responsibility_category` / `expected_funding_source` (Room & Board specific) and `PatientPayer` (general patient-level payer sequencing)
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none unified
Current verified system of record: split/partial — no single entity spanning all claim types
Ownership status: TENANT OWNED (both underlying structures) — UNRESOLVED as a unified concept
Owning organization: tenant hospice agency
Owning platform: Tenant Platform
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none
Patient scope: yes
Current fields: see `PatientPayer` and Room & Board entries
Relationships: `FacilityPaymentExpectation` does not FK to `PatientPayer`; it carries its own free-text payer-name snapshots
Consumers: `facility_payment_service.py`, `facility_payment_router.py`; `claim_financials.py` (via `PatientPayer`)
APIs: see above
Frontend consumers: `FacilityCollectionsReportPage.tsx`
Background jobs: none confirmed
Reports and exports: Facility Collections Report
Existing data exposure: not queried
Duplicate data present: potential overlap between `FacilityPaymentExpectation`'s responsibility fields and `PatientPayer` sequencing — not confirmed as true duplication, flagged for future review
Missing relationships: no FK between `FacilityPaymentExpectation` and `PatientPayer`
Missing constraints: n/a
Missing history: not verified
Decision: DO NOT CREATE a new generic "Billing Responsibility" entity yet. Any future work should EXTEND or LINK existing structures (`PatientPayer` for general claims, `FacilityPaymentExpectation` for Room & Board) once Patient Coverage (`PatientInsurance` vs. `PatientPayer`) is resolved.
Reason: consistent with the hard rule that Billing Responsibility can never become the system of record for insurance coverage — it must remain a narrower, claim/period/service-specific determination layered on top of coverage, not a replacement for it.
Repository evidence: `backend/app/billing/models/facility_payment_expectation.py`; `backend/app/models/patient_payer.py`
Migration exposure: none proposed in this phase
Backfill exposure: none proposed in this phase
Historical-preservation requirements: n/a
Open defects: none new beyond what is flagged under Patient Coverage and Room & Board
Confidence: Partially Verified

---

### Concept: Claim

Tenant Platform model and table: `Claim` / `claims`
Biller Platform model and table: none
Legacy model and table: `app/billing/store.py` in-memory tenant-picker list — its own docstring states claim data now lives in the real `claims` table (not a database table; see Legacy Inventory for detail)
Existing shared model and table: `claims` (single, shared, authoritative)
Current verified system of record: `Claim`
Ownership status: TENANT OWNED — CORRECTED. `Claim` has zero verified Biller Platform consumers today; all listed consumers are Tenant Platform routers/services/pages. Reclassified from SHARED DOMAIN OWNED to TENANT OWNED per the rule against assuming a Shared Billing Domain exists. This is the correct starting ownership for the future Biller Platform to access via authorized reference (per the Ownership Principle), not evidence that sharing already exists.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform (today); a future Biller Platform must access this table, not copy it
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none today
Patient scope: yes (FK to `Patient`)
Current fields: **no `claim_category` column; no payer FK; free-text `payer_name` field only** (confirmed by direct source inspection)
Relationships: consumed broadly (see below)
Consumers: `claims_router.py`, `claim_status_router.py`, `billing_router.py`, `credit_balance_router.py`, `denials_router.py`, `payment_posting_router.py`; services: `billing_engine.py`, `aging_report_service.py`, `claim_financials.py`, `credit_balance_service.py`, `facility_payment_service.py`
APIs: routers listed above
Frontend consumers: `ClaimsManagementPage.tsx`, `BillingOverviewPage.tsx`, `AgingReportPage.tsx`, `CreditBalanceReportPage.tsx`, `DenialsAppealsPage.tsx`, `PaymentPostingPage.tsx`, `ReportsPage.tsx`, `FacilityCollectionsReportPage.tsx`
Background jobs: not confirmed
Reports and exports: virtually all billing reports
Existing data exposure: not queried (production data presumed to exist)
Duplicate data present: none — one authoritative table
Missing relationships: no FK to `Payer`, `PatientInsurance`, or `PatientPayer`
Missing constraints: no `claim_category` constraint exists
Missing history: not verified
Decision: REUSE; EXTEND (not CREATE) if/when `claim_category` or payer FKs are added
Reason: single, heavily-consumed, real table; must never be duplicated by a disconnected Biller-side copy.
Repository evidence: `backend/app/billing/models/claim.py`; `backend/app/billing/store.py` (docstring confirming supersession)
Migration exposure: any EXTEND touches a high-traffic table — requires careful planning, not performed in this phase
Backfill exposure: adding `claim_category` would require backfilling every existing row (design only, in Sections 25-26 of the discovery report, not executed)
Historical-preservation requirements: existing rows and free-text `payer_name` values must be preserved
Open defects: none beyond the already-corrected `claim_category` misstatement
Confidence: Verified

---

### Concept: Claim Category

Tenant Platform model and table: does not exist — no `claim_category` column, enum, or constraint anywhere in the codebase
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none
Current verified system of record: none — proposed only
Ownership status: UNRESOLVED (nothing exists to own)
Owning organization: n/a
Owning platform: n/a
Tenant scope: n/a
Agency scope: n/a
Billing-organization scope: n/a
Patient scope: n/a
Current fields: n/a
Relationships: n/a
Consumers: n/a
APIs: n/a
Frontend consumers: n/a
Background jobs: n/a
Reports and exports: n/a
Existing data exposure: none — column does not exist
Duplicate data present: none
Missing relationships: would need to live on `Claim` (or a linked table); must not be conflated with Payer Organization or Plan
Missing constraints: the entire proposed constraint set from prior sections is unbuilt
Missing history: n/a
Decision: **PROPOSED, NOT REUSE.** Formal reclassification from the prior (incorrect) locked/REUSE treatment to CREATE-pending-authorization.
Reason: verified absent by direct source inspection; kept strictly separate from Payer Organization and Plan per the hard rules.
Repository evidence: full-file inspection of `backend/app/billing/models/claim.py`; repository-wide search for `claim_category`
Migration exposure: full new-column + constraint + backfill migration, designed but not executed
Backfill exposure: every existing `Claim` row would need a category backfilled (Section 26 design, plan only)
Historical-preservation requirements: the approved user-facing label "Medicare Part A Hospice" for the `MEDICARE_HOSPICE` internal value remains valid whenever this is eventually implemented
Open defects: same finding already documented in `REPOSITORY_GROUNDING_CORRECTION_REPORT.md`
Confidence: Verified (as an absence finding)

---

### Concept: Claim Payer Relationship

Tenant Platform model and table: none — `Claim.payer_name` is free text; no FK to `Payer`, `PatientInsurance`, or `PatientPayer`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none
Current verified system of record: none — payer identity on a claim is currently free text only
Ownership status: UNRESOLVED
Owning organization: n/a
Owning platform: n/a
Tenant scope: n/a
Agency scope: n/a
Billing-organization scope: n/a
Patient scope: n/a
Current fields: `Claim.payer_name` (free text)
Relationships: none formal
Consumers: same consumers as Claim
APIs: same as Claim
Frontend consumers: same as Claim
Background jobs: none confirmed
Reports and exports: display `payer_name` as free text today
Existing data exposure: not queried
Duplicate data present: none — nothing to duplicate; the relationship does not exist yet
Missing relationships: primary payer, secondary payer, payer sequence, and submission destination are all currently absent as structured relationships on `Claim`
Missing constraints: n/a
Missing history: n/a
Decision: **FURTHER INVESTIGATION**, not CREATE. A structured Claim-to-Payer relationship must not be built until Patient Coverage (`PatientInsurance` vs. `PatientPayer`) is resolved, since the correct link target depends on that decision; deciding CREATE now, before that dependency is resolved, would risk building a relationship to the wrong side of an unresolved split.
Reason: sequencing this after the Patient Coverage resolution avoids creating a second unresolved duplication, and avoids naming a new entity before its distinct business purpose (versus simply linking to an existing model) is established.
Repository evidence: `backend/app/billing/models/claim.py` (confirmed free-text `payer_name`, no FK)
Migration exposure: deferred pending Patient Coverage resolution
Backfill exposure: deferred
Historical-preservation requirements: existing free-text `payer_name` values must be preserved/mapped, not discarded, whenever this is built
Open defects: none beyond the sequencing dependency noted above
Confidence: Verified

---

### Concept: Claim Line

Tenant Platform model and table: not found
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none
Current verified system of record: none — no line-item-level claim model was found in this pass; line detail may or may not be embedded as fields/JSON on `Claim` itself, which was not exhaustively ruled out
Ownership status: UNRESOLVED
Owning organization: n/a
Owning platform: n/a
Tenant scope: n/a
Agency scope: n/a
Billing-organization scope: n/a
Patient scope: n/a
Current fields: n/a
Relationships: n/a
Consumers: n/a
APIs: n/a
Frontend consumers: n/a
Background jobs: n/a
Reports and exports: n/a
Existing data exposure: none confirmed
Duplicate data present: none
Missing relationships: n/a
Missing constraints: n/a
Missing history: n/a
Decision: FURTHER INVESTIGATION
Reason: a repository-wide class-name search (`ClaimLine`) returned no matches, but `Claim`'s own internal field structure was not fully itemized in this pass — treated as an open item, not a confirmed absence.
Repository evidence: absence of a `ClaimLine` class confirmed via search
Migration exposure: unresolved
Backfill exposure: unresolved
Historical-preservation requirements: unresolved
Open defects: flagged for a narrower follow-up investigation
Confidence: Partially Verified

---

### Concept: Claim Batch

Tenant Platform model and table: not found
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none
Current verified system of record: none
Ownership status: UNRESOLVED (nothing to own)
Owning organization: n/a
Owning platform: n/a
Tenant scope: n/a
Agency scope: n/a
Billing-organization scope: n/a
Patient scope: n/a
Current fields: n/a
Relationships: n/a
Consumers: n/a
APIs: n/a
Frontend consumers: n/a
Background jobs: n/a
Reports and exports: n/a
Existing data exposure: none
Duplicate data present: none
Missing relationships: n/a
Missing constraints: n/a
Missing history: n/a
Decision: TENTATIVE CREATE if pursued (no existing structure to reuse or rename). No authoritative equivalent was found during the current repository search. Creation is not approved until the Legacy Billing Schema Inventory confirms that no historical, inactive, archived, or differently named equivalent exists.
Reason: repository-wide search for a batching/`ClaimBatch` model returned no matches; `Claim.exported_at` suggests submission timing is tracked per-claim, not via a distinct batch entity — this is a genuinely new concept, not a renamed existing one.
Repository evidence: absence confirmed via search; `Claim.exported_at` referenced in `aging_report_service.py` docstring
Migration exposure: n/a (nothing exists)
Backfill exposure: n/a
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified (as an absence finding)

---

### Concept: Claim Submission

Tenant Platform model and table: no dedicated model; `Claim.exported_at` is the only submission-related field confirmed
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none dedicated
Current verified system of record: `Claim.exported_at` (partial — a timestamp, not a full submission/acknowledgment history)
Ownership status: TENANT OWNED (as far as the existing field goes)
Owning organization: tenant hospice agency
Owning platform: Tenant Platform
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none
Patient scope: yes (via Claim)
Current fields: `exported_at`
Relationships: n/a
Consumers: `aging_report_service.py` (aging clock start)
APIs: same as Claim
Frontend consumers: `AgingReportPage.tsx`
Background jobs: not confirmed
Reports and exports: aging report
Existing data exposure: not queried
Duplicate data present: none
Missing relationships: no dedicated submission-batch or acknowledgment-history record exists
Missing constraints: n/a
Missing history: full submission/acknowledgment history (277/999/997-style acks) does not appear to be modeled
Decision: FURTHER INVESTIGATION before choosing EXTEND (of `Claim`) vs. CREATE (a new linked submission-history table); CREATE is not ruled out here because a full acknowledgment history is a genuinely distinct concept from the existing single timestamp, not merely a renamed version of it.
Reason: a single timestamp field already exists and is actively consumed; before creating a new submission model, confirm whether extending `Claim` meets the requirement.
Repository evidence: `backend/app/billing/services/aging_report_service.py` docstring referencing `Claim.exported_at`
Migration exposure: additive if EXTEND is chosen
Backfill exposure: none for existing field
Historical-preservation requirements: preserve `exported_at` values
Open defects: none
Confidence: Partially Verified

---

### Concept: Clearinghouse Transaction

Tenant Platform model and table: not found
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none
Current verified system of record: none
Ownership status: UNRESOLVED (nothing to own)
Owning organization: n/a
Owning platform: n/a
Tenant scope: n/a
Agency scope: n/a
Billing-organization scope: n/a
Patient scope: n/a
Current fields: n/a
Relationships: n/a
Consumers: n/a
APIs: n/a
Frontend consumers: n/a
Background jobs: n/a
Reports and exports: n/a
Existing data exposure: none
Duplicate data present: none
Missing relationships: n/a
Missing constraints: n/a
Missing history: n/a
Decision: TENTATIVE CREATE if pursued
Reason: no trading-partner/clearinghouse routing model was found anywhere in the repository; this is a genuinely new concept. No authoritative equivalent was found during the current repository search. Creation is not approved until the Legacy Billing Schema Inventory confirms that no historical, inactive, archived, or differently named equivalent exists.
Repository evidence: absence confirmed via repository-wide search
Migration exposure: n/a
Backfill exposure: n/a
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified (as an absence finding)

---

### Concept: Payment

Tenant Platform model and table: `Payment`, `PaymentAdjustment` / `payments`, `payment_adjustments`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: `payments`/`payment_adjustments` (shared, authoritative)
Current verified system of record: `Payment`/`PaymentAdjustment`
Ownership status: TENANT OWNED — CORRECTED. No verified Biller Platform consumer exists for `Payment`/`PaymentAdjustment`; reclassified from SHARED DOMAIN OWNED to TENANT OWNED for the same reason as `Claim`.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform (today)
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none
Patient scope: yes (via Claim)
Current fields: not itemized field-by-field
Relationships: consumed with `Claim`, `RemittanceAdvice`
Consumers: `payment_posting_router.py`, `facility_payment_router.py`, `credit_balance_router.py`, `claim_financials.py`, `credit_balance_service.py`, `facility_payment_service.py`, `aging_report_service.py`
APIs: `payment_posting_router.py`, `facility_payment_router.py`
Frontend consumers: `PaymentPostingPage.tsx`
Background jobs: not confirmed
Reports and exports: Aging Report, Credit Balance Report
Existing data exposure: not queried
Duplicate data present: none
Missing relationships: none identified
Missing constraints: none identified
Missing history: not verified
Decision: REUSE
Reason: heavily consumed, single-source, real tables.
Repository evidence: `payment_posting_router.py`; `claim_financials.py`; `aging_report_service.py` docstring
Migration exposure: none proposed
Backfill exposure: none proposed
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified

---

### Concept: ERA

Tenant Platform model and table: `RemittanceAdvice` / `remittance_advices` (no separate "ERA" class exists distinct from remittance)
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: `remittance_advices`
Current verified system of record: `RemittanceAdvice`
Ownership status: TENANT OWNED — CORRECTED. No verified Biller Platform consumer exists for `RemittanceAdvice`; reclassified from SHARED DOMAIN OWNED to TENANT OWNED for the same reason as `Claim`.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform (today)
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none
Patient scope: yes (via Claim)
Current fields: free-text `payer_name` (same pattern as `Claim`)
Relationships: consumed with `Claim`, `Payment`
Consumers: `payment_posting_router.py`, `aging_report_service.py`, `facility_payment_service.py`
APIs: `payment_posting_router.py`
Frontend consumers: `PaymentPostingPage.tsx`, `BillingOverviewPage.tsx`
Background jobs: automated 835-import mechanics not verified in this pass
Reports and exports: Billing Overview
Existing data exposure: not queried
Duplicate data present: none identified — treated as the same concept as Remittance in this codebase
Missing relationships: same free-text payer gap as `Claim`
Missing constraints: n/a
Missing history: import-source/idempotency handling not verified
Decision: REUSE `RemittanceAdvice` as the single ERA/remittance authority; DO NOT CREATE a separate "ERA" model, since the codebase does not distinguish ERA from Remittance and doing so now would only be a renamed duplicate.
Reason: same table already serves both concepts.
Repository evidence: `backend/app/billing/models/remittance_advice.py`
Migration exposure: none proposed
Backfill exposure: none proposed
Historical-preservation requirements: n/a
Open defects: automated import-job mechanics not verified — flagged for future investigation
Confidence: Partially Verified

---

### Concept: Remittance

Tenant Platform model and table: `RemittanceAdvice` / `remittance_advices` (same model as ERA above — no separate models exist)
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: `remittance_advices`
Current verified system of record: `RemittanceAdvice`
Ownership status: TENANT OWNED — CORRECTED. No verified Biller Platform consumer exists for `RemittanceAdvice` under the "Remittance" framing either; reclassified from SHARED DOMAIN OWNED to TENANT OWNED for the same reason as ERA/Claim above.

Owning organization: tenant hospice agency
Owning platform: Tenant Platform (today)
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none
Patient scope: yes (via Claim)
Current fields: free-text `payer_name`
Relationships: relates to `Claim` and `Payment` through service-layer logic (formal DB FK not independently verified in this pass)
Consumers: same as ERA
APIs: same as ERA
Frontend consumers: same as ERA
Background jobs: same as ERA
Reports and exports: same as ERA
Existing data exposure: not queried
Duplicate data present: none
Missing relationships: formal FK to `Claim`/`Payment` not verified — flagged, not assumed
Missing constraints: n/a
Missing history: not verified
Decision: REUSE
Reason: same as ERA
Repository evidence: same as ERA
Migration exposure: none proposed
Backfill exposure: none proposed
Historical-preservation requirements: n/a
Open defects: formal FK relationship should be verified in a future, narrower pass
Confidence: Partially Verified

---

### Concept: Payment Posting

Tenant Platform model and table: no separate model — a workflow built on `Payment`, `PaymentAdjustment`, `RemittanceAdvice`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: same underlying tables as Payment/Remittance
Current verified system of record: the underlying financial tables are authoritative; "Payment Posting" is a workflow concept, not a distinct data model
Ownership status: TENANT OWNED (workflow); underlying data TENANT OWNED — CORRECTED from SHARED DOMAIN OWNED for the same reason as Payment/Remittance above (no verified Biller Platform consumer)
Owning organization: tenant hospice agency
Owning platform: Tenant Platform
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none
Patient scope: yes
Current fields: n/a (workflow, not a table)
Relationships: n/a
Consumers: `payment_posting_router.py`
APIs: `payment_posting_router.py`
Frontend consumers: `PaymentPostingPage.tsx`
Background jobs: not confirmed
Reports and exports: n/a
Existing data exposure: n/a
Duplicate data present: none
Missing relationships: n/a
Missing constraints: n/a
Missing history: n/a
Decision: REUSE the underlying financial models; DO NOT CREATE a separate "Payment Posting" entity
Reason: financial transaction authority must remain separate from any future Biller workflow-assignment layer (who is posting, queue, follow-up).
Repository evidence: `backend/app/billing/api/payment_posting_router.py`
Migration exposure: none proposed
Backfill exposure: none proposed
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified

---

### Concept: Denial

Tenant Platform model and table: `Denial` / `denials`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: `denials`
Current verified system of record: `Denial`
Ownership status: TENANT OWNED — CORRECTED from SHARED DOMAIN OWNED. No verified Biller Platform consumer exists.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform (today)
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none
Patient scope: yes (via Claim)
Current fields: includes a `WRITTEN_OFF` status consumed by the aging report's write-off exclusion rule
Relationships: relates to `Claim`
Consumers: `denials_router.py`, `aging_report_service.py`, `credit_balance_service.py`, `claim_financials.py`
APIs: `denials_router.py`
Frontend consumers: `DenialsAppealsPage.tsx`
Background jobs: not confirmed
Reports and exports: Aging Report, Credit Balance Report
Existing data exposure: not queried
Duplicate data present: none
Missing relationships: none identified
Missing constraints: none identified
Missing history: not verified
Decision: REUSE
Reason: single, heavily-consumed, real model.
Repository evidence: `denials_router.py`; `aging_report_service.py` docstring
Migration exposure: none proposed
Backfill exposure: none proposed
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified

---

### Concept: Appeal

Tenant Platform model and table: `Appeal` / `appeals`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: `appeals`
Current verified system of record: `Appeal`
Ownership status: TENANT OWNED — CORRECTED from SHARED DOMAIN OWNED. No verified Biller Platform consumer exists.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform (today)
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none
Patient scope: yes (via Denial/Claim)
Current fields: not itemized; preparation/approval/submission-stage distinction not verified
Relationships: relates to `Denial`
Consumers: `denials_router.py`
APIs: `denials_router.py`
Frontend consumers: `DenialsAppealsPage.tsx`
Background jobs: not confirmed
Reports and exports: none confirmed beyond the Denials & Appeals page
Existing data exposure: not queried
Duplicate data present: none
Missing relationships: none identified
Missing constraints: none identified
Missing history: whether preparation/approval/submission are distinct tracked stages was not verified
Decision: REUSE
Reason: single, real, consumed model; no competing structure found.
Repository evidence: `denials_router.py`
Migration exposure: none proposed
Backfill exposure: none proposed
Historical-preservation requirements: n/a
Open defects: stage-tracking granularity should be verified in a future, narrower pass
Confidence: Partially Verified

---

### Concept: AR Item

Tenant Platform model and table: **none — AR is a pure computed report, not a stored model**
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: none — derived reporting only
Current verified system of record: no stored AR record; `aging_report_service.py` computes AR state on demand from `Claim`/`Payment`/`PaymentAdjustment`/`Denial`
Ownership status: TENANT OWNED — CORRECTED. The "shared source tables" it derives from (Claim/Payment/Adjustment/Denial) are themselves now TENANT OWNED per the corrections above; no verified Biller Platform consumer of the AR calculation exists.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform (today)
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none
Patient scope: yes
Current fields: computed `Outstanding Balance = Total Charges - Posted Payments - Adjustments - Write-offs`
Relationships: reads `Claim.exported_at` as the aging clock
Consumers: `aging_report_service.py`; shares arithmetic with `credit_balance_service.py` via `claim_financials.py` "so both reports never diverge"
APIs: aging report endpoint
Frontend consumers: `AgingReportPage.tsx`
Background jobs: none — computed live
Reports and exports: Aging Report
Existing data exposure: none — no AR table exists
Duplicate data present: none — explicitly designed as a single shared calculation to avoid divergence
Missing relationships: n/a
Missing constraints: n/a
Missing history: n/a — AR is a derived, point-in-time view by design
Decision: REUSE the existing derived-calculation approach; DO NOT CREATE a stored "AR Item" table
Reason: the existing design is explicitly documented as intentional ("No new data store") and already prevents the exact divergence risk a stored/duplicated AR record would create.
Repository evidence: `backend/app/billing/services/aging_report_service.py` (full docstring)
Migration exposure: none
Backfill exposure: none
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified

---

### Concept: Credit Balance

Tenant Platform model and table: `CreditBalanceCase` / `credit_balance_cases`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: `credit_balance_cases`
Current verified system of record: `CreditBalanceCase`
Ownership status: TENANT OWNED — CORRECTED from SHARED DOMAIN OWNED. No verified Biller Platform consumer exists.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform (today)
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none
Patient scope: yes (via Claim)
Current fields: not itemized; case-management fields distinct from the underlying balance calculation
Relationships: relates to `Claim`; balance arithmetic shared with Aging Report via `claim_financials.py`
Consumers: `credit_balance_router.py`, `credit_balance_case_service.py`, `credit_balance_service.py`
APIs: `credit_balance_router.py`
Frontend consumers: `CreditBalanceReportPage.tsx`
Background jobs: not confirmed
Reports and exports: Credit Balance Report
Existing data exposure: not queried
Duplicate data present: none — case management is correctly separated from the shared balance-calculation module
Missing relationships: none identified
Missing constraints: none identified
Missing history: not verified
Decision: REUSE
Reason: single, real, actively-consumed model with correctly separated calculation logic.
Repository evidence: `credit_balance_router.py`; `credit_balance_case_service.py`; `credit_balance_service.py`; `aging_report_service.py`
Migration exposure: none proposed
Backfill exposure: none proposed
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified

---

### Concept: NOE

Tenant Platform model and table: `NoeEdiSubmission` / `noe_edi_submissions`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: `noe_edi_submissions`
Current verified system of record: `NoeEdiSubmission`
Ownership status: TENANT OWNED for patient/episode facts (a future Biller Platform work-queue layer, if built, would be BILLER OWNED for the queue itself only)
Owning organization: tenant hospice agency
Owning platform: Tenant Platform
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none today
Patient scope: yes (via patient/episode)
Current fields: not itemized
Relationships: EDI-submission-specific
Consumers: `noe_tracking_router.py`, `noe_edi_builder.py`
APIs: `noe_tracking_router.py`
Frontend consumers: `NoeTrackingPage.tsx`
Background jobs: EDI builder logic exists; batch/timing not fully verified
Reports and exports: NOE Tracking page
Existing data exposure: not queried
Duplicate data present: none identified
Missing relationships: none identified
Missing constraints: none identified
Missing history: not verified
Decision: REUSE the patient/episode-specific NOE facts; LINK any future Biller work-queue/follow-up/assignment layer to this model rather than duplicating it
Reason: Tenant Platform owns patient/episode NOE facts; Biller Platform may own work queues around them, per the hard rules.
Repository evidence: `noe_tracking_router.py`; `noe_edi_builder.py`
Migration exposure: none proposed
Backfill exposure: none proposed
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified

---

### Concept: CAP

Tenant Platform model and table: `HospiceCapRecord` / `hospice_cap_records`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: `hospice_cap_records`
Current verified system of record: `HospiceCapRecord`
Ownership status: TENANT OWNED — CORRECTED from SHARED DOMAIN OWNED. No verified Biller Platform consumer exists.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform (today)
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none
Patient scope: aggregate/cap-period scope rather than single-patient (exact grain not itemized in this pass)
Current fields: not itemized
Relationships: calculation source data, calculations, and reviews produced by `hospice_cap_service.py`
Consumers: `hospice_cap_service.py`
APIs: not independently identified beyond the service
Frontend consumers: `CapCalculationPage.tsx`
Background jobs: not confirmed
Reports and exports: Cap Calculation page
Existing data exposure: not queried
Duplicate data present: none identified
Missing relationships: none identified
Missing constraints: none identified
Missing history: not verified
Decision: REUSE
Reason: single, real, consumed model and service.
Repository evidence: `hospice_cap_service.py`
Migration exposure: none proposed
Backfill exposure: none proposed
Historical-preservation requirements: n/a
Open defects: none
Confidence: Partially Verified (API-layer detail not independently confirmed)

---

### Concept: Room & Board Case

Tenant Platform model and table: `FacilityPaymentExpectation`, `FacilityPaymentAllocation`, `FacilityCollectionAlert` (+ threshold model), `FacilityPaymentAuditLog`
Biller Platform model and table: none
Legacy model and table: none
Existing shared model and table: the four tables above (shared, authoritative)
Current verified system of record: this four-model group, collectively
Ownership status: TENANT OWNED — CORRECTED from SHARED DOMAIN OWNED. No verified Biller Platform consumer exists for the Room & Board model group today.
Owning organization: tenant hospice agency
Owning platform: Tenant Platform (today)
Tenant scope: yes
Agency scope: yes
Billing-organization scope: none today
Patient scope: yes
Current fields: `FacilityPaymentExpectation` carries `responsibility_category`, `expected_funding_source`, `expected_payer_name_snapshot`, `primary_payer_name_snapshot`, `secondary_payer_name_snapshot` (free-text snapshots, not FKs)
Relationships: `FacilityPaymentAllocation`/`FacilityCollectionAlert`/`FacilityPaymentAuditLog` relate to `FacilityPaymentExpectation`; none FK to `Payer`, `PatientPayer`, or `PatientInsurance`
Consumers: `facility_payment_router.py`, `facility_payment_service.py`
APIs: `facility_payment_router.py`
Frontend consumers: `FacilityCollectionsReportPage.tsx`
Background jobs: alert-threshold evaluation logic exists per model naming; exact trigger mechanics not verified
Reports and exports: Facility Collections Report
Existing data exposure: not queried
Duplicate data present: none identified as a second Room & Board system — this is the sole implementation
Missing relationships: no FK from `FacilityPaymentExpectation` to `Payer`/`PatientPayer`/`PatientInsurance` — free-text snapshots only
Missing constraints: none identified
Missing history: `FacilityPaymentAuditLog` appears to already provide dedicated audit history
Decision: REUSE this four-model group as the single authoritative Room & Board system; DO NOT CREATE a second Tenant/Biller copy of payer reimbursements, SNF payments, advances, or reconciliation
Reason: real, actively-consumed, single implementation with its own dedicated audit log.
Repository evidence: `facility_payment_expectation.py`, `facility_payment_allocation.py`, `facility_collection_alert.py`, `facility_payment_audit_log.py`, `facility_payment_router.py`, `facility_payment_service.py`
Migration exposure: none proposed
Backfill exposure: none proposed
Historical-preservation requirements: n/a
Open defects: free-text payer snapshots share the same structural gap as `Claim.payer_name` — should be resolved together, not separately, if Payer/Plan work resumes
Confidence: Verified

---

### Concept: BillingProviderOrganization

Tenant Platform model and table: none
Biller Platform model and table: `BillingProviderOrganization` / `billing_provider_organizations`
Legacy model and table: none
Existing shared model and table: none — Owner-portal-scoped
Current verified system of record: `BillingProviderOrganization` — for the **licensing/authorization concept only**, not the richer Figma "Organization & Teams" concept
Ownership status: BILLER OWNED — verified, but scoped to platform-owner licensing, not the Figma-designed Biller Platform UI
Owning organization: platform owner, not the tenant hospice agency
Owning platform: Owner/Platform-Admin console (`src/owner/`)
Tenant scope: cross-tenant (assignable to any tenant via `BillingProviderAgencyAssignment`)
Agency scope: via assignment, not directly
Billing-organization scope: yes — this **is** the billing organization entity
Patient scope: none
Current fields: not itemized
Relationships: has many `BillingProviderOrganizationMembership`, `BillingProviderAgencyAssignment`
Consumers: `billing_provider_router.py` (`/api/owner/billing-providers`), `billing_provider_access_service.py`
APIs: `/api/owner/billing-providers/organizations`
Frontend consumers: `src/owner/pages/BillingLicensing.jsx`, `src/owner/pages/TenantManagement.jsx`
Background jobs: not confirmed
Reports and exports: none confirmed
Existing data exposure: not queried
Duplicate data present: **conceptually adjacent to, but not the same as,** the Figma "Organization & Teams" design — no code implements Team Portfolios, hierarchy, or Coverage Assignment on top of this model today
Missing relationships: no team/hierarchy/coverage-assignment layer exists on top of this entity
Missing constraints: n/a
Missing history: not verified
Decision: REUSE this model as the authoritative "billing organization" entity for the licensing concept; EXTEND (add team/hierarchy/coverage as new linked tables) rather than CREATE a second, parallel "billing organization" concept for the Figma design
Reason: real, working, named "billing provider organization" already serving the platform-owner licensing use case; a second root entity with a similar name would violate the naming/duplication rule.
Repository evidence: `billing_provider_router.py`; `billing_provider_access_service.py`; `src/owner/pages/BillingLicensing.jsx`; `src/owner/pages/TenantManagement.jsx`
Migration exposure: any EXTEND (teams/hierarchy) would be additive to this table's relationships
Backfill exposure: none for reuse
Historical-preservation requirements: n/a
Open defects: naming collision (two different concepts sharing "billing organization" vocabulary) is a documentation-clarity risk and should be called out explicitly in all future specs
Confidence: Verified

---

### Concept: BillingProviderOrganizationMembership

Tenant Platform model and table: none
Biller Platform model and table: `BillingProviderOrganizationMembership` / `billing_provider_organization_memberships`
Legacy model and table: none
Existing shared model and table: none
Current verified system of record: `BillingProviderOrganizationMembership`
Ownership status: BILLER OWNED — verified
Owning organization: platform owner
Owning platform: Owner/Platform-Admin console
Tenant scope: n/a (organization-scoped)
Agency scope: n/a
Billing-organization scope: yes
Patient scope: none
Current fields: **role is limited to `MEMBER`/`ADMIN` only — confirmed by direct source inspection**
Relationships: FK to `BillingProviderOrganization`
Consumers: `billing_provider_access_service.py`
APIs: covered under the organization router
Frontend consumers: `BillingLicensing.jsx`
Background jobs: none confirmed
Reports and exports: none confirmed
Existing data exposure: not queried
Duplicate data present: none
Missing relationships: **no hierarchy fields exist (no supervisor/lead/reports-to relationship)**
Missing constraints: n/a
Missing history: not verified
Decision: REUSE for basic organization membership; DO NOT assume this satisfies the Figma "System Role Definitions" or "Administrative Hierarchy" requirements — those require a separate relationship table (per the previously approved separate-table option) layered on top
Reason: role support and hierarchy limitations were directly verified as absent.
Repository evidence: direct source inspection (role enum limited to `MEMBER`/`ADMIN`)
Migration exposure: adding a hierarchy relationship table is additive
Backfill exposure: none for reuse
Historical-preservation requirements: n/a
Open defects: none beyond the already-documented role/hierarchy gap
Confidence: Verified

---

### Concept: BillingProviderAgencyAssignment

Tenant Platform model and table: none
Biller Platform model and table: `BillingProviderAgencyAssignment` / `billing_provider_agency_assignments`
Legacy model and table: none
Existing shared model and table: none — links a tenant agency to a billing organization
Current verified system of record: `BillingProviderAgencyAssignment`
Ownership status: BILLER OWNED — verified (relationship to a Tenant-owned agency)
Owning organization: platform owner (grants), tenant agency (receiving end)
Owning platform: Owner/Platform-Admin console
Tenant scope: yes (references the assigned tenant/agency)
Agency scope: yes
Billing-organization scope: yes
Patient scope: none
Current fields: not itemized
Relationships: FK to `BillingProviderOrganization`; references a tenant/agency
Consumers: `billing_provider_router.py` (`/assignments`), `billing_provider_access_service.py`
APIs: `/api/owner/billing-providers/.../assignments`
Frontend consumers: `BillingLicensing.jsx`, `TenantManagement.jsx`
Background jobs: none confirmed
Reports and exports: none confirmed
Existing data exposure: not queried
Duplicate data present: none — this is the authoritative billing-organization-to-agency relationship for licensing
Missing relationships: no payer-specific or team-specific granularity — see `BillingProviderAgencyServiceScope`
Missing constraints: n/a
Missing history: not verified
Decision: REUSE as the authoritative licensing-level billing-organization-to-agency relationship; LINK any future payer/team-specific coverage assignment concept to this, rather than duplicating agency-assignment logic
Reason: real, working, authoritative relationship already granting a billing organization access to a tenant agency.
Repository evidence: `billing_provider_router.py`; `billing_provider_access_service.py`
Migration exposure: additive if EXTEND with payer/team granularity
Backfill exposure: none for reuse
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified

---

### Concept: BillingProviderAgencyServiceScope

Tenant Platform model and table: none
Biller Platform model and table: `BillingProviderAgencyServiceScope` / `billing_provider_agency_service_scopes`
Legacy model and table: none
Existing shared model and table: none
Current verified system of record: `BillingProviderAgencyServiceScope`
Ownership status: BILLER OWNED — verified, but its payer-specific granularity is UNRESOLVED
Owning organization: platform owner
Owning platform: Owner/Platform-Admin console
Tenant scope: via the parent assignment
Agency scope: via the parent assignment
Billing-organization scope: yes
Patient scope: none
Current fields: functional service scope + permission level per assignment (per prior investigation); payer-specific or Medicare/Medi-Cal-specific granularity **not confirmed**
Relationships: FK to `BillingProviderAgencyAssignment`
Consumers: `billing_provider_router.py`, `billing_provider_access_service.py`
APIs: covered under the assignment router
Frontend consumers: `BillingLicensing.jsx`
Background jobs: none confirmed
Reports and exports: none confirmed
Existing data exposure: not queried
Duplicate data present: none
Missing relationships: **not confirmed to support payer-specific coverage (e.g., "Medicare Biller," "Medi-Cal Biller") — must not be assumed equal to the approved Agency Coverage assignment architecture**
Missing constraints: n/a
Missing history: not verified
Decision: FURTHER INVESTIGATION REQUIRED to confirm exact field-level scope before deciding EXTEND vs. CREATE for payer-specific coverage assignment
Reason: the hard rules explicitly instruct not to assume this equals the approved architecture; honoring that by flagging the gap rather than asserting either REUSE or CREATE.
Repository evidence: `billing_provider_router.py`; `billing_provider_access_service.py` (field-level payer-specificity not independently re-verified)
Migration exposure: unresolved pending further investigation
Backfill exposure: unresolved
Historical-preservation requirements: n/a
Open defects: flagged as an open item requiring a dedicated follow-up read of the model's exact fields
Confidence: Partially Verified

---

### Concept: Billing Team

Tenant Platform model and table: none
Biller Platform model and table: none — **confirmed absent**
Legacy model and table: none
Existing shared model and table: none
Current verified system of record: none exists
Ownership status: UNRESOLVED (nothing exists to own)
Owning organization: n/a
Owning platform: n/a
Tenant scope: n/a
Agency scope: n/a
Billing-organization scope: n/a
Patient scope: n/a
Current fields: n/a
Relationships: n/a
Consumers: n/a
APIs: n/a
Frontend consumers: n/a
Background jobs: n/a
Reports and exports: n/a
Existing data exposure: none
Duplicate data present: none
Missing relationships: n/a
Missing constraints: n/a
Missing history: n/a
Decision: TENTATIVE CREATE if pursued, only after this documented absence
Reason: `billing_teams` and all team/hierarchy tables were previously (incorrectly) cited as REUSE in earlier sections and were confirmed absent by the repository-grounding correction; re-confirmed absent in this pass. No authoritative equivalent was found during the current repository search. Creation is not approved until the Legacy Billing Schema Inventory confirms that no historical, inactive, archived, or differently named equivalent exists.
Repository evidence: repository-wide search for team/hierarchy models found no matches
Migration exposure: n/a
Backfill exposure: n/a
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified (as an absence finding)

---

### Concept: Team Membership

Tenant Platform model and table: none
Biller Platform model and table: none — confirmed absent
Legacy model and table: none
Existing shared model and table: none
Current verified system of record: none
Ownership status: UNRESOLVED (nothing exists to own)
Owning organization: n/a
Owning platform: n/a
Decision: TENTATIVE CREATE if pursued, separately from `BillingProviderOrganizationMembership`, per instruction to verify separately
Reason: confirmed absent; `BillingProviderOrganizationMembership` (`MEMBER`/`ADMIN` only) cannot represent team membership. No authoritative equivalent was found during the current repository search. Creation is not approved until the Legacy Billing Schema Inventory confirms that no historical, inactive, archived, or differently named equivalent exists.
Repository evidence: repository-wide search found no matches
Migration exposure: n/a
Backfill exposure: n/a
Historical-preservation requirements: n/a
Open defects: none
Confidence: Verified (as an absence finding)

---

### Concept: Team Leader Assignment

Tenant Platform model and table: none
Biller Platform model and table: none — confirmed absent (design proposal only in prior discovery-report sections, not implemented code)
Legacy model and table: none
Current verified system of record: none exists
Ownership status: UNRESOLVED (nothing exists to own)
Decision: CREATE if pursued
Reason: proposed design only, must not be described as existing.
Repository evidence: absence confirmed via repository-wide search
Confidence: Verified (as an absence finding)

---

### Concept: Billing Supervisor Assignment

Tenant Platform model and table: none
Biller Platform model and table: none — confirmed absent
Legacy model and table: none
Current verified system of record: none exists
Ownership status: UNRESOLVED (nothing exists to own)
Decision: CREATE if pursued
Reason: same as Team Leader Assignment
Repository evidence: absence confirmed via repository-wide search
Confidence: Verified (as an absence finding)

---

### Concept: Medicare Billing Assignment

Tenant Platform model and table: none
Biller Platform model and table: none confirmed as payer-specific — `BillingProviderAgencyServiceScope` is the closest existing structure, but its payer-specificity is unverified
Legacy model and table: none
Current verified system of record: none confirmed
Ownership status: UNRESOLVED
Decision: FURTHER INVESTIGATION before deciding EXTEND (of `BillingProviderAgencyServiceScope`) vs. CREATE
Reason: whether existing service scopes can represent this safely is not yet confirmed either way.
Repository evidence: see `BillingProviderAgencyServiceScope`
Confidence: Partially Verified

---

### Concept: Medi-Cal / Managed Care Assignment

Tenant Platform model and table: none
Biller Platform model and table: none confirmed — same open question as Medicare Billing Assignment, tracked separately per instruction
Legacy model and table: none
Current verified system of record: none confirmed
Ownership status: UNRESOLVED
Decision: FURTHER INVESTIGATION, tracked separately from Medicare Billing Assignment
Reason: same reasoning as Medicare Billing Assignment
Repository evidence: see `BillingProviderAgencyServiceScope`
Confidence: Partially Verified

---

### Concept: Backup Coverage Assignment

Tenant Platform model and table: none
Biller Platform model and table: none — confirmed absent
Legacy model and table: none
Current verified system of record: none exists
Ownership status: UNRESOLVED (nothing exists to own)
Decision: TENTATIVE CREATE if pursued; effective-dating and primary/backup self-duplication prevention must be designed, not present today
Reason: confirmed absent by repository-wide search. No authoritative equivalent was found during the current repository search. Creation is not approved until the Legacy Billing Schema Inventory confirms that no historical, inactive, archived, or differently named equivalent exists.
Repository evidence: absence confirmed via search
Confidence: Verified (as an absence finding)

---

### Concept: Capability Grant

Tenant Platform model and table: `app/core/permissions.py` contains `require_permission`/`has_permission` — **confirmed to be literal, real placeholder functions, not a working permission/capability engine**
Biller Platform model and table: `CapabilityAssignment`/`WorkforceCapability` — **confirmed absent** (previously miscited as REUSE, corrected in `REPOSITORY_GROUNDING_CORRECTION_REPORT.md`)
Legacy model and table: none
Current verified system of record: none — no working capability/permission grant system exists
Ownership status: UNRESOLVED
Decision: DO NOT CREATE a second permissions system without first evaluating whether `app/core/permissions.py`'s placeholder should be built out into the real one
Reason: re-confirms the correction report's finding.
Repository evidence: `backend/app/core/permissions.py`; absence of `CapabilityAssignment`/`WorkforceCapability` confirmed via search
Confidence: Verified

---

### Concept: Individual DDE Authorization

Tenant Platform model and table: none
Biller Platform model and table: none — confirmed absent
Legacy model and table: none
Current verified system of record: none exists
Ownership status: UNRESOLVED (nothing exists to own)
Decision: TENTATIVE CREATE if pursued; must remain separate from role, team, agency, and billing-coverage models
Reason: confirmed absent by repository-wide search. No authoritative equivalent was found during the current repository search. Creation is not approved until the Legacy Billing Schema Inventory confirms that no historical, inactive, archived, or differently named equivalent exists.
Repository evidence: absence confirmed via search
Confidence: Verified (as an absence finding)

---

### Concept: Audit Event

Tenant Platform model and table: `AuditLog` / `audit_logs` (generic, cross-domain)
Biller Platform model and table: `FacilityPaymentAuditLog` / `facility_payment_audit_logs` (Room & Board domain-specific)
Legacy model and table: none
Current verified system of record: `AuditLog` (generic) + `FacilityPaymentAuditLog` (domain-specific)
Ownership status: TENANT OWNED — CORRECTED from SHARED DOMAIN OWNED. Both audit logs are consumed only within the Tenant Platform today; no verified Biller Platform audit consumer exists. Would become a genuine SHARED DOMAIN OWNED candidate once a Biller Platform audit consumer is built, provided it reuses (not duplicates) this log.
Owning organization: tenant hospice agency
Owning platform: shared
Decision: REUSE the generic `AuditLog` for any new Biller Platform audit events unless a domain-specific reason (like Room & Board's) justifies a dedicated log
Reason: the codebase already demonstrates both patterns; a new Biller Platform capability should default to the shared log to avoid proliferating audit systems.
Repository evidence: `backend/app/models/audit_log.py`; `facility_payment_audit_log.py`
Migration exposure: none proposed
Confidence: Verified

---

### Concept: Export Event

Tenant Platform model and table: none dedicated — exports appear to be handled as report-generation actions, logged (where logged) through the generic `AuditLog`
Biller Platform model and table: none
Legacy model and table: none
Current verified system of record: none dedicated — unresolved whether existing exports are audited at all
Ownership status: UNRESOLVED
Decision: REUSE the generic `AuditLog` for export events if/when a dedicated Export Access History feature is built, rather than creating a separate export-event system — recommendation only, not a confirmed REUSE of an already-built mechanism
Reason: consistent with the shared-infrastructure-first principle, but pending verification
Repository evidence: absence of a dedicated export-event model confirmed via search; whether current exports are audited at all was not independently verified
Confidence: Partially Verified

---

### Concept: Billing Platform Settings

Tenant Platform model and table: not directly inspected in this pass — outside the file set examined for this billing-schema sweep
Biller Platform model and table: none confirmed
Legacy model and table: none confirmed
Current verified system of record: unresolved
Ownership status: UNRESOLVED
Decision: FURTHER INVESTIGATION REQUIRED before deciding whether the existing settings system can support organization defaults, agency overrides, versioning, and effective dates
Reason: this concept was not part of the files directly examined; asserting REUSE or CREATE without evidence would violate the discovery discipline this investigation exists to enforce.
Repository evidence: none collected for this concept in this pass
Confidence: Unverified

---

### Concept: SecureInbox Routing Relationship

Tenant Platform model and table: none
Biller Platform model and table: none — confirmed absent
Legacy model and table: none
Current verified system of record: none exists
Ownership status: UNRESOLVED (nothing exists to own)
Decision: PREVIEW ONLY — DO NOT CREATE messaging infrastructure during this phase
Reason: no messaging/routing model was found, and none is authorized to be created in this phase.
Repository evidence: absence confirmed via repository-wide search
Confidence: Verified (as an absence finding)

---

## Matrix Approval Gate — Self-Check

- Every required concept has an entry: yes.
- Ownership defaults to UNRESOLVED and is only marked otherwise with repository evidence: yes.
- No entity is recommended as CREATE where it would only be a cleaner name for an existing structure: verified — Payer Organization, Patient Coverage, ERA, and Payment Posting are each explicitly marked REUSE/DO NOT CREATE with the existing structure named.
- Every REUSE claim is proven to exist with a file citation: yes.
- Patient Coverage remains a logical concept, not a physical model: yes — no third model recommended.
- PatientInsurance vs. PatientPayer is not resolved here — correctly deferred to the dedicated comparison document. **This remains the highest-priority unresolved architecture decision.**
- Billing Responsibility is not treated as insurance coverage: yes.
- Claim Category, Payer, Plan, Coverage, and Responsibility remain separate: yes.
- Existing consumers are mapped for every confirmed-existing structure: yes.
- Migration exposure documented per concept: yes.

## Ownership Correction Log (applied 2026-09-18)

A first-pass review of this matrix used **SHARED DOMAIN OWNED** for
several concepts (Patient Identity, Payer, Claim, Payment, ERA,
Remittance, Payment Posting, Denial, Appeal, AR Item, Credit Balance,
CAP, Room & Board, Audit Event) based on the fact that each has exactly
one physical table used by more than one *module* inside the Tenant
Platform (e.g., both clinical and billing code, or both a report and a
service). On review, this did not meet the bar this document itself
sets: a Shared Billing Domain must not be assumed to exist, and none of
these concepts has a **verified Biller Platform consumer** today — the
only real Biller Platform code that exists
(`BillingProviderOrganization`/`BillingProviderAgencyAssignment`/
`BillingProviderAgencyServiceScope`) does not reference any of them.

All fourteen entries above have been corrected to **TENANT OWNED**,
with an inline note in each entry explaining the correction and stating
what would need to be true (a verified Biller Platform consumer) for
the entry to become a genuine SHARED DOMAIN OWNED candidate in the
future. No REUSE/EXTEND/CREATE decision changed as a result of this
correction — only the ownership-status label, which was overstating
cross-platform sharing that does not yet exist.

### Addendum — Explicit 4-Criteria Evidence Test (applied per required review)

Per review instruction, SHARED DOMAIN OWNED requires all of: (1)
intentional cross-platform sharing, (2) verified Tenant + Biller
consumers referencing the same record, (3) defined write authority, (4)
defined scope enforcement, (5) no competing writable copy. Applying
this test to each of the fourteen corrected concepts:

| Concept | (1) Intentional sharing | (2) Verified Biller consumer | (3) Write authority defined | (4) Scope enforcement defined | (5) No competing copy | Result |
|---|---|---|---|---|---|---|
| Patient Identity | Not documented | No | No | No (Tenant-only today) | Yes | Fails (2)–(4) → TENANT OWNED |
| Payer | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |
| Claim | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |
| Payment / PaymentAdjustment | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |
| RemittanceAdvice (ERA/Remittance) | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |
| Payment Posting (workflow) | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |
| Denial | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |
| Appeal | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |
| AR Item (computed) | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |
| Credit Balance | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |
| CAP | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |
| Room & Board | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |
| Audit Event | Not documented | No | No | No | Yes | Fails (2)–(4) → TENANT OWNED |

None of the fourteen satisfies the full five-part test, so SHARED
DOMAIN OWNED is not available to any of them today; each is classified
TENANT OWNED on the basis of criterion (5) holding (no competing
writable copy — a single authoritative table exists) combined with the
absence of any verified Biller Platform consumer, rather than on any
formal cross-platform sharing decision. This is a narrower, more
defensible basis than the prior SHARED DOMAIN OWNED label and is
revisited the moment a real Biller Platform consumer is built.

## Status

Documentation only. No schema, migration, API, UI, backfill, deletion,
or retirement performed. Implementation remains blocked.

Ownership corrections applied per your review. Proceeding to Prompt 2
(`LEGACY_BILLING_SCHEMA_INVENTORY.md`) per your authorization. Schema
design, migration design, and Payer/Plan implementation remain not
started. PatientInsurance vs. PatientPayer remains the highest-priority
unresolved architecture decision, unaffected by this Prompt.

## Matrix Status (per required-corrections review)

- Prompt 1: **CORRECTED AND CONDITIONALLY APPROVED**
- Patient Coverage Authority: **UNRESOLVED**
- Eligibility Result Authority: **UNRESOLVED**
- Legacy Billing Inventory: **PENDING**
- Schema Design: **BLOCKED**
- Implementation: **BLOCKED**

No schema, migration, API, UI, backfill, deletion, consolidation, or
retirement is authorized by this document.
