# Legacy Billing Schema Inventory

## Status

CURRENT PHASE: Tenant Platform, Biller Platform, and Legacy Billing
Schema Discovery

DISCOVERY ONLY. No deletion, migration, consolidation, retirement, or
implementation authorized.

## Purpose

Identify and preserve every historical billing structure before any
future system-of-record selection. An old table or model is not
obsolete merely because the current frontend does not display it, a
newer design uses different terminology, new documentation proposes
another model name, or no recent developer recognizes it.

## Method

Searched `backend/app/models/`, `backend/app/billing/models/`,
`backend/app/billing/services/`, `backend/app/billing/api/`,
`backend/app/api/`, migration history (Alembic revisions under
`backend/alembic/versions/` where present), and
`sns-emr-frontend/src/` (including archived/deprecated directory
names, feature flags, and test/fixture directories) for the full
search vocabulary specified in the source request (billing, payer,
payor, insurance, insurer, carrier, plan, coverage, eligibility,
claim, claim line/batch, submission, acknowledgment, payment, ERA,
remittance, denial, appeal, AR, aging, credit balance, CAP, NOE, DDE,
Room & Board, facility reimbursement, billing provider/organization,
agency assignment, service scope, responsible payer, financial class,
secondary payer, audit, export).

## Executive Finding

**PRELIMINARY LEGACY FINDING.** Based on the components searched in
this pass, the sole component meeting the definition of "legacy"
(superseded, no longer the active system of record) is:
`backend/app/billing/store.py`, an in-memory, non-persisted, dev/demo
tenant-picker list. Its own module docstring states that claim data
now lives in the real `claims` table — i.e., it documents its own
supersession. No other archived, deprecated, orphaned, or historical
billing schema was found in the directories and vocabulary searched
(no `legacy/`, `deprecated/`, `archive/`, or `old/` directories exist
under `backend/app/billing/` or `backend/app/models/`; no feature flags
gating a retired billing schema were found).

This is explicitly **not** declared the final or only legacy structure
in the repository: the search covered the directories and vocabulary
listed under Method, but did not exhaustively trace every test,
fixture, background job, import/export path, or historically removed-
then-reintroduced migration. If a future, more exhaustive pass finds
additional legacy structures, this finding will be superseded, not
treated as contradictory — this document's Legacy Inventory
Completion Gate below records exactly which coverage areas are
confirmed vs. not yet exhaustively traced.

Every other required component below (`Payer`, `PatientInsurance`,
`PatientPayer`, `Claim`, `BillingProviderOrganization` and its related
models, and the eligibility/payment/ERA/remittance/denial/appeal/
credit-balance/NOE/CAP/Room & Board models) is **ACTIVE** — currently
consumed by real routers, services, and frontend pages — and none of
them is a candidate for retirement based on evidence gathered in this
pass. This finding does not resolve whether any of them should be
consolidated with another *active* structure (that is a separate
question, addressed in the dedicated PatientInsurance-vs-PatientPayer
comparison below, and authoritatively in
`PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`, and in the System-of-Record
Matrix); it only confirms that none of them is legacy/superseded.

---

## Required-Component Status Records

Each record below follows the template's core fields in condensed
form; full consumer detail for each is already documented in
`TENANT_BILLER_SYSTEM_OF_RECORD_MATRIX.md` and is not repeated in
full here to avoid the two documents diverging — this inventory
records **current status** (ACTIVE vs. legacy) and **legacy/duplication
signal** specifically, per its purpose.

### Component: Payer

Repository path: `backend/app/models/payer.py` (canonical), `backend/app/billing/models/payer.py` (re-export stub)
Model / Table: `Payer` / `payers`
Current status: **ACTIVE**
Business concepts represented: payer identity catalog
Historical value: n/a — currently active, not historical
Missing capabilities: no FK consumer from `Claim`, `PatientPayer`, or `PatientInsurance` (see System-of-Record Matrix)
Potential overlap: none — the billing-module re-export is intentional, documented, non-duplicative
Duplication risk: none
Recommended decision: REUSE (not a legacy/retirement question)
Repository evidence: `backend/app/models/payer.py`; `backend/app/billing/models/payer.py` docstring; `backend/app/billing/models/contract.py:38-40,74` (FK consumer)
Open defects: none

### Component: PatientInsurance

Repository path: `backend/app/models/patient_insurance.py`
Model / Table: `PatientInsurance` / `patient_insurances`
Current status: **ACTIVE**
Business concepts represented: eligibility-workflow coverage evidence
Historical value: n/a — currently active
Missing capabilities: no direct CRUD API; no FK to `PatientPayer`
Potential overlap: `PatientPayer` (see dedicated comparison below)
Duplication risk: **yes — see dedicated comparison below**
Recommended decision: FURTHER INVESTIGATION (relationship to PatientPayer); REUSE as eligibility-evidence record is not in question
Repository evidence: `eligibility_check_router.py`; `eligibility_workflow_service.py`
Open defects: none beyond the duplication risk noted

### Component: PatientPayer

Repository path: `backend/app/models/patient_payer.py`
Model / Table: `PatientPayer` / `patient_payers`
Current status: **ACTIVE**
Business concepts represented: billing/financial payer-responsibility sequencing
Historical value: n/a — currently active
Missing capabilities: no FK to `PatientInsurance`
Potential overlap: `PatientInsurance` (see dedicated comparison below)
Duplication risk: **yes — see dedicated comparison below**
Recommended decision: FURTHER INVESTIGATION (relationship to PatientInsurance); REUSE as billing/financial system of record is not in question
Repository evidence: `app/api/patients.py:3244-3389`; `claim_financials.py`; `credit_balance_service.py`; `facility_payment_service.py`; `msp_validation_service.py`
Open defects: none beyond the duplication risk noted

### Component: Claim

Repository path: `backend/app/billing/models/claim.py`
Model / Table: `Claim` / `claims`
Current status: **ACTIVE**
Business concepts represented: the authoritative claim record
Historical value: n/a — currently active
Missing capabilities: no `claim_category` column; no payer FK; free-text `payer_name` only
Potential overlap: none — single authoritative table
Duplication risk: none
Recommended decision: REUSE
Repository evidence: `backend/app/billing/models/claim.py`
Open defects: `claim_category` previously (incorrectly) described elsewhere as already-locked/constrained — corrected in `REPOSITORY_GROUNDING_CORRECTION_REPORT.md`

### Component: Eligibility structures (PayerEligibilityCheck, EligibilityVerification)

Repository path: `backend/app/billing/models/payer_eligibility_check.py`, `backend/app/billing/models/eligibility_verification.py`
Model / Table: `PayerEligibilityCheck` / `payer_eligibility_checks`; `EligibilityVerification` / `eligibility_verifications`
Current status: **ACTIVE (both)**
Business concepts represented: eligibility check result and richer, append-only eligibility verification history
Historical value: n/a — both currently active
Missing capabilities: n/a
Potential overlap: **the two models overlap in purpose** — both represent eligibility-check results for the same `PatientInsurance` FK target
Duplication risk: **yes — flagged as a second, distinct duplication pair** (separate from PatientInsurance/PatientPayer), noted for a future dedicated review; not required to be resolved in this phase
Recommended decision: FURTHER INVESTIGATION
Repository evidence: both model files; `eligibility_check_router.py`; `eligibility_workflow_service.py`
Open defects: none beyond the flagged overlap

### Component: Payment / PaymentAdjustment

Repository path: `backend/app/billing/models/payment.py` (and adjustment model)
Model / Table: `Payment`, `PaymentAdjustment` / `payments`, `payment_adjustments`
Current status: **ACTIVE**
Business concepts represented: posted payments and adjustments
Historical value: n/a — currently active
Missing capabilities: none identified
Potential overlap: none
Duplication risk: none
Recommended decision: REUSE
Repository evidence: `payment_posting_router.py`; `claim_financials.py`; `aging_report_service.py`
Open defects: none

### Component: ERA / Remittance (RemittanceAdvice)

Repository path: `backend/app/billing/models/remittance_advice.py`
Model / Table: `RemittanceAdvice` / `remittance_advices`
Current status: **ACTIVE**
Business concepts represented: ERA/remittance import target (the codebase does not distinguish "ERA" from "Remittance" as separate models)
Historical value: n/a — currently active
Missing capabilities: free-text `payer_name`, same gap as `Claim`; automated 835-import mechanics not independently verified
Potential overlap: none — single model serves both concepts
Duplication risk: none
Recommended decision: REUSE
Repository evidence: `backend/app/billing/models/remittance_advice.py`
Open defects: import-job mechanics flagged for future investigation

### Component: Denial / Appeal

Repository path: `backend/app/billing/models/denial.py`, `backend/app/billing/models/appeal.py`
Model / Table: `Denial` / `denials`; `Appeal` / `appeals`
Current status: **ACTIVE (both)**
Business concepts represented: claim denial and appeal tracking
Historical value: n/a — currently active
Missing capabilities: appeal preparation/approval/submission stage-tracking granularity not verified
Potential overlap: none
Duplication risk: none
Recommended decision: REUSE
Repository evidence: `denials_router.py`; `aging_report_service.py` (WRITTEN_OFF reference)
Open defects: none

### Component: AR (Accounts Receivable)

Repository path: `backend/app/billing/services/aging_report_service.py`
Model / Table: **none — no stored AR table; pure computed report**
Current status: **ACTIVE** (as a live calculation, not a stored structure)
Business concepts represented: outstanding-balance/aging calculation
Historical value: n/a
Missing capabilities: n/a — intentionally not a stored fact, per its own docstring ("No new data store")
Potential overlap: none — explicitly designed as a single shared calculation module (`claim_financials.py`) also used by Credit Balance, specifically to prevent divergence
Duplication risk: none
Recommended decision: REUSE the existing calculation approach; DO NOT CREATE a stored AR table
Repository evidence: `aging_report_service.py` full docstring
Open defects: none

### Component: Credit Balance (CreditBalanceCase)

Repository path: `backend/app/billing/models/credit_balance_case.py`
Model / Table: `CreditBalanceCase` / `credit_balance_cases`
Current status: **ACTIVE**
Business concepts represented: credit-balance case management
Historical value: n/a — currently active
Missing capabilities: none identified
Potential overlap: none
Duplication risk: none
Recommended decision: REUSE
Repository evidence: `credit_balance_router.py`; `credit_balance_case_service.py`; `credit_balance_service.py`
Open defects: none

### Component: NOE (NoeEdiSubmission)

Repository path: `backend/app/billing/models/noe_edi_submission.py`
Model / Table: `NoeEdiSubmission` / `noe_edi_submissions`
Current status: **ACTIVE**
Business concepts represented: Notice of Election EDI submission tracking
Historical value: n/a — currently active
Missing capabilities: batch/timing mechanics of the EDI builder not fully verified
Potential overlap: none
Duplication risk: none
Recommended decision: REUSE
Repository evidence: `noe_tracking_router.py`; `noe_edi_builder.py`
Open defects: none

### Component: CAP (HospiceCapRecord)

Repository path: `backend/app/billing/models/hospice_cap_record.py`
Model / Table: `HospiceCapRecord` / `hospice_cap_records`
Current status: **ACTIVE**
Business concepts represented: hospice cap calculation source data/results
Historical value: n/a — currently active
Missing capabilities: API-layer detail not independently confirmed in this pass
Potential overlap: none
Duplication risk: none
Recommended decision: REUSE
Repository evidence: `hospice_cap_service.py`
Open defects: none

### Component: Room & Board (FacilityPaymentExpectation, FacilityPaymentAllocation, FacilityCollectionAlert, FacilityPaymentAuditLog)

Repository path: `backend/app/billing/models/facility_payment_expectation.py`, `facility_payment_allocation.py`, `facility_collection_alert.py`, `facility_payment_audit_log.py`
Model / Table: as named / `facility_payment_expectations`, `facility_payment_allocations`, `facility_collection_alerts` (+ thresholds), `facility_payment_audit_logs`
Current status: **ACTIVE (all four)**
Business concepts represented: facility (Room & Board) payment expectation, allocation, alerting, and dedicated audit trail
Historical value: n/a — currently active
Missing capabilities: no FK from `FacilityPaymentExpectation` to `Payer`/`PatientPayer`/`PatientInsurance` — free-text payer-name snapshots only, same structural gap as `Claim`
Potential overlap: none — sole Room & Board implementation
Duplication risk: none as a second Room & Board system; the free-text-payer gap mirrors `Claim`'s and should be resolved together if Payer/Plan work resumes
Recommended decision: REUSE
Repository evidence: all four model files; `facility_payment_router.py`; `facility_payment_service.py`
Open defects: free-text payer snapshots (structural gap, not a legacy/duplication issue)

### Component: BillingProviderOrganization / BillingProviderOrganizationMembership / BillingProviderAgencyAssignment / BillingProviderAgencyServiceScope

Repository path: `backend/app/billing/models/billing_provider_organization.py`, `billing_provider_organization_membership.py`, `billing_provider_agency_assignment.py`, `billing_provider_agency_service_scope.py`
Model / Table: as named
Current status: **ACTIVE (all four)** — but scoped to Owner/Platform-Admin licensing, not the Figma-designed Biller Platform UI
Business concepts represented: billing-company licensing entity, membership (role `MEMBER`/`ADMIN` only, no hierarchy), tenant/agency assignment, functional service scope
Historical value: n/a — currently active
Missing capabilities: no team/hierarchy layer; membership has no hierarchy fields; service-scope payer-specificity unverified
Potential overlap: conceptually adjacent to (but not the same as) the Figma "Organization & Teams" design — no code implements Team Portfolios, hierarchy, or payer-specific Coverage Assignment on top of these models today
Duplication risk: naming-collision risk only (two different concepts sharing "billing organization" vocabulary), not a data-duplication risk
Recommended decision: REUSE; EXTEND for any future team/hierarchy/coverage layer rather than creating a second root entity
Repository evidence: `billing_provider_router.py`; `billing_provider_access_service.py`; `src/owner/pages/BillingLicensing.jsx`; `src/owner/pages/TenantManagement.jsx`
Open defects: naming-collision documentation-clarity risk (already flagged in the Matrix)

### Component: Clearinghouse configuration, payer crosswalks, import mappings

Current status: **not found anywhere in the repository**
Business concepts represented: n/a
Historical value: n/a — nothing to preserve; nothing found, historical or active
Recommended decision: CREATE if pursued (genuinely new; nothing to consolidate or retire)
Repository evidence: absence confirmed via repository-wide search
Open defects: none

### Component: Audit / Export structures

Repository path: `backend/app/models/audit_log.py`; `backend/app/billing/models/facility_payment_audit_log.py`
Model / Table: `AuditLog` / `audit_logs` (generic, cross-domain); `FacilityPaymentAuditLog` / `facility_payment_audit_logs` (Room & Board specific)
Current status: **ACTIVE (both)**
Business concepts represented: audit trail
Historical value: n/a — currently active
Missing capabilities: no dedicated "Export Event" model found — whether current exports are already audited through `AuditLog` was not independently verified in this pass
Potential overlap: none — the domain-specific log is a deliberate, narrow exception to the generic log, not a duplicate of it
Duplication risk: none
Recommended decision: REUSE the generic `AuditLog` for future export events unless a domain-specific reason justifies a dedicated log, consistent with the existing pattern
Repository evidence: both model files
Open defects: export-event audit coverage should be verified in a future, narrower pass

---

## Legacy Component Record (preliminary — sole legacy artifact found in this pass)

### Legacy Component: In-Memory Billing/Tenant Store

Repository path: `backend/app/billing/store.py`
Model: none (plain in-memory Python data structure, not an ORM model)
Table: **none — not a database table; never persisted**
Migration created by: n/a (no migration ever created this — it was never a database structure)
Migration revision: n/a
Migration date: n/a
Current fields: an in-memory, hardcoded list of tenants/claims used for early development/demo purposes (per its own docstring)
Foreign keys: none (in-memory, not relational)
Relationships: none
Constraints: none
Indexes: none
Tenant scope: was a flat dev-only list, not truly tenant-scoped in the way the real `claims` table is
Agency scope: none
Patient scope: none
Billing-organization scope: none
Current services: **none** — no production service imports this as a data source for claim data any longer (its own docstring confirms supersession)
Current APIs: none confirmed to depend on this module for claim data
Current UI consumers: none confirmed
Current background jobs: none
Current integration consumers: none
Current report consumers: none
Current export consumers: none
Current tests: not independently verified in this pass whether any test still imports this module — flagged as an open item rather than assumed
Fixture or seed usage: possible dev/demo usage only; not confirmed as production seed data
Known existing data: none — in-memory only, does not persist between process restarts, so there is no "existing data" to preserve in the traditional sense
Estimated data exposure: **Verified — none** (nothing persists to disk/database; restarting the process discards it)
Current status: **PARTIALLY ACTIVE** — the module file still exists in the repository and has not been deleted, but its own docstring states the real `claims` table has already superseded it for claim data; it was not confirmed fully INACTIVE only because whether any remaining dev/demo code path still imports it was not exhaustively traced in this pass
Business concepts represented: an early, pre-`claims`-table placeholder for claim/tenant demo data
Historical value: low — no persisted data exists to lose; its only value is as a code-archaeology reference showing the module's own documented supersession
Missing capabilities: n/a — fully superseded by `Claim`/`claims`
Potential replacement: `Claim` / `claims` (already the active replacement, per the module's own docstring)
Duplication risk: **none** — it does not persist data, so it cannot diverge from `claims`; it is dead weight at most, not a competing system of record
Recommended decision: **FURTHER INVESTIGATION** (not RETIRE AFTER VERIFIED REPLACEMENT yet) — before any retirement decision, confirm (a) no remaining code path imports this module, and (b) no test relies on it. This inventory documents its status; it does not authorize removing the file.
Repository evidence: `backend/app/billing/store.py` (full docstring read, confirms self-described supersession by the `claims` table)
Open defects: whether any dead import of this module remains was not exhaustively traced — flagged as the one remaining open item before a retirement recommendation could be finalized

---

## Dedicated Comparison: PatientInsurance vs. PatientPayer

This comparison is required by the source request before any Patient
Coverage entity is proposed. **Patient Coverage remains a logical
concept only; no third model is recommended here or anywhere in this
document.** The authoritative, field-by-field version of this
comparison is `PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`; the table
below is a condensed summary and must stay consistent with it.

| Dimension | `PatientInsurance` | `PatientPayer` |
|---|---|---|
| Distinct purpose | Eligibility-workflow evidence — represents a coverage record used to run eligibility checks | Billing/financial-responsibility sequencing — represents which payer is responsible for a patient's charges, in what order |
| Table | `patient_insurances` | `patient_payers` |
| Semantic overlap | Both describe "this patient has this payer/coverage" | Both describe "this patient has this payer/coverage" |
| Data overlap | Likely stores payer-identifying fields (carrier, ID) needed to run an eligibility check | Likely stores payer-identifying fields needed for claim/financial sequencing — the two field sets were not diffed field-by-field in this pass; flagged as an open item |
| Relationships | FK'd by `PayerEligibilityCheck` and `EligibilityVerification` | FK target of `ServiceCoverageDecision.selected_payer_id` |
| Consumers | `eligibility_check_router.py`, `eligibility_workflow_service.py` | `app/api/patients.py` (CRUD), `claim_financials.py`, `credit_balance_service.py`, `facility_payment_service.py`, `msp_validation_service.py` |
| APIs | No direct CRUD API found | Direct CRUD via `app/api/patients.py:3244-3389` |
| Import usage | Feeds eligibility-check import/response flow | Not confirmed to be import-driven; appears to be user/staff-entered via the patients API |
| Claim usage | Not directly FK'd to `Claim` | Not directly FK'd to `Claim`, but is the responsibility-sequencing input consumed by `claim_financials.py` |
| Eligibility usage | Direct — this is the eligibility-evidence anchor | Indirect, if at all — not a confirmed consumer of eligibility results |
| Reports | Feeds `readiness_dashboard_service.py` | Feeds Credit Balance Report and Facility Collections Report (via the services listed) |
| Existing records | Not queried in this pass | Not queried in this pass |
| Historical value | Active, ongoing eligibility workflow value | Active, ongoing billing/financial workflow value |
| Which is older | **NOT VERIFIED — and likely not determinable from migration history.** Both `patient_insurances` and `patient_payers` appear in the same squashed baseline migration (`521d501c6eea_consolidated_baseline`); the baseline does not preserve original creation order. `patient_payers` was later extended (not created) by `c2e8a5d1f4b6_add_msp_fields_to_patient_payers`. This does not indicate which table existed first. |
| Which is more complete | **Not determined** — a field-by-field diff was not performed in this pass; flagged as an open item |
| Whether either is authoritative | **Each is authoritative for its own workflow** (eligibility vs. billing/financial responsibility) — neither is authoritative for the other's workflow, and neither is confirmed authoritative for a unified "Patient Coverage" concept |
| Whether the structures should be linked | **Recommended for further evaluation**: an explicit FK (LINK) between the two would close the most material integrity gap found in this entire investigation, without requiring either model to give up its distinct purpose |
| Whether either can be extended | Plausible in principle (e.g., adding an FK field to one or both), but not decided here — decision explicitly deferred |
| Whether eventual consolidation is appropriate | **Not decided here.** CONSOLIDATE is a valid future path only if a dedicated, separately reviewed forward-only migration plan can prove no data loss, no broken FK, and no workflow regression for either eligibility or billing/financial-responsibility consumers. LINK is the lower-risk interim recommendation, but this document does not authorize either. |

**Decision for this document: FURTHER INVESTIGATION.** Patient Coverage
remains a logical concept, not a physical model, until this comparison
is formally approved and a LINK or CONSOLIDATE decision is made
separately. No schema change is authorized by this comparison.

---

## Retirement Gate — Applied to `app/billing/store.py`

Per the required gate, this component **cannot** be retired yet
because:
- Replacement authority is not formally approved in a migration-design
  document (only informally evidenced by the module's own docstring).
- Whether any remaining code path or test imports it has not been
  exhaustively traced.
- No forward-only migration or repair path applies (nothing to
  migrate — it was never persisted).
- No explicit retirement authorization has been requested or granted.

This document records the finding; it does not authorize deletion.

## Legacy Inventory Completion Gate — Self-Check

- Every discovered billing model is listed: yes (14 active component
  records + 1 legacy record + 2 confirmed-absent categories).
- Every discovered billing table is listed: yes.
- Creation migrations were not independently re-derived from Alembic
  revision history in this pass (no Alembic environment query was
  run); this is a genuine gap and is flagged, not glossed over.
- Consumers are mapped: yes, for every active component.
- Current status is proven: yes, with PARTIALLY ACTIVE (not
  INACTIVE) honestly used for `app/billing/store.py` where full
  certainty was not reached.
- Existing data exposure is documented: yes (none, for the one legacy
  artifact; not queried for the active components).
- Historical value is documented: yes.
- No component is silently buried: yes — every required component from
  the source request appears above.
- No retirement is performed: confirmed.

## Status

Documentation only. No schema, migration, API, UI, backfill, deletion,
or retirement performed. Implementation remains blocked.

PatientInsurance vs. PatientPayer remains the highest-priority
unresolved architecture decision, consistent with your instruction.
This document does not resolve it — it documents the comparison and
recommends further evaluation of LINK vs. CONSOLIDATE. The
field-by-field authority for this comparison is now
`PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`.

## Review Checklist Self-Check (per required review)

**Repository coverage:**
- Models searched: yes (`backend/app/models/`, `backend/app/billing/models/`)
- Tables searched: yes (via model `__tablename__` inspection)
- Historical migrations searched: partial — `patient_insurances` and
  `patient_payers` traced to the consolidated baseline plus two
  follow-on migrations; a full revision-history walk of every table
  was not performed
- Services searched: yes (`backend/app/billing/services/`)
- APIs searched: yes (`backend/app/api/`, `backend/app/billing/api/`)
- Background jobs searched: **not exhaustively** — flagged as an open
  item throughout (e.g., `app/billing/store.py` open defect)
- Imports and exports searched: **not verified** — flagged NOT VERIFIED
  in the dedicated duplication analysis
- Reports searched: yes, at the service/consumer level
- Tests and fixtures searched: **not verified** — flagged as an open
  item
- Deprecated and archived directories searched: yes (confirmed absent)
- Equivalent behavior searched, not only names: yes — `PatientPayer`,
  `PatientInsurance`, and the two eligibility models were each compared
  on structure/behavior, not name alone

**Legacy-preservation check:**
- No structure dismissed for UI non-exposure, naming preference, or
  unfamiliarity: confirmed
- Consumers mapped before "unused" classification: confirmed for all
  ACTIVE components
- Historical/audit value documented: confirmed
- Existing records protected; no deletion, retirement, migration, or
  backfill performed: confirmed

**Decision validation:**
- REUSE/EXTEND decisions include evidence: yes, throughout
- TENTATIVE CREATE decisions remain unapproved: yes (aligned with the
  matrix's parallel correction)
- Retirement recommendations remain gated: yes — Retirement Gate above
  explicitly blocks retirement of `app/billing/store.py`
- `app/billing/store.py` is not declared the only legacy structure
  without complete search evidence: **corrected** — now explicitly
  labeled a PRELIMINARY LEGACY FINDING, not a final/exhaustive one

## Final Review Result

**APPROVED WITH CORRECTIONS** — corrections applied in this revision:
(1) Executive Finding reframed as a PRELIMINARY LEGACY FINDING rather
than a definitive/exhaustive conclusion; (2) the PatientInsurance-vs-
PatientPayer comparison now defers to the newly created, field-level
`PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md` as its authority; (3) the
"which is older" cell corrected to reflect the verified migration
evidence (both tables share a squashed baseline migration, so creation
order is genuinely not determinable from history, not merely
unchecked).

Prompt 3 (`TENANT_BILLER_OWNERSHIP_BOUNDARIES.md`) remains blocked
pending your review of this corrected inventory and the new duplication
analysis.
