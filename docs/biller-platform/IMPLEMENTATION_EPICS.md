# Implementation Epics

## Status

**PLANNING ONLY.** Defines implementation epics for the sequence set
in `IMPLEMENTATION_PLAN.md`. **No schema. No migrations. No code. No
API. No UI.**

---

## Epic 1 — Billing Organization

- **Scope:** `BillingProviderOrganization` lifecycle management.
- **Existing structures:** `BillingProviderOrganization` (1 row
  verified).
- **Strategy:** REUSE / EXTEND (per `BILLING_SCHEMA_DESIGN_REVIEW.md`
  Section 4). No replacement entity.
- **Depends on:** none (foundation).

## Epic 2 — Billing Teams

- **Scope:** `BillingProviderOrganizationMembership` — user-to-provider
  organization membership.
- **Existing structures:** `BillingProviderOrganizationMembership` (1
  row verified).
- **Strategy:** REUSE / EXTEND. No new team/sub-team structure unless a
  future, separately authorized review finds one is required (Section
  4 noted none was found).
- **Depends on:** Epic 1.

## Epic 3 — Agency Assignment

- **Scope:** `BillingProviderAgencyAssignment` write-authority
  delegation (Final Schema Authorization Review Option B: Biller
  Platform operational authority; Owner Platform delegates).
- **Existing structures:** `BillingProviderAgencyAssignment` (1 row
  verified); writers `billing_provider_router.py`,
  `owner_admin.py::set_tenant_financials`.
- **Strategy:** REUSE existing table; future, separately authorized
  code-path change so `owner_admin.py` delegates instead of writing
  directly. **No schema change.** No replacement or duplicate
  assignment table.
- **Depends on:** Epic 1, Epic 2.

## Epic 4 — Agency Coverage

- **Scope:** `BillingProviderAgencyServiceScope` — per-assignment
  capability + permission level.
- **Existing structures:** `BillingProviderAgencyServiceScope` (2 rows
  verified); 15-value scope enum already covers every domain concept
  identified in Schema Design Review Section 1.
- **Strategy:** REUSE / EXTEND. Must close the verified asymmetry
  where Owner-Platform-created assignments receive no service-scope
  rows (see Epic 3).
- **Depends on:** Epic 3.

## Epic 5 — Payer Authority

- **Scope:** `Payer` (payer master), `PatientPayer` (billing/financial
  authority per Final Schema Authorization Review §1).
- **Existing structures:** `payers` (0 rows verified), `patient_payers`
  (5 rows verified); consumers `app/api/patients.py`,
  `claim_financials.py`, `credit_balance_service.py`,
  `facility_payment_service.py`, `msp_validation_service.py`,
  `claim_export_service.py`.
- **Strategy:** REUSE. Future, separately authorized link to
  `PatientInsurance` (Migration Design Review Section 1.2, Option A).
  **No `PatientCoverage`. No consolidation.**
- **Depends on:** Epic 1 (provider-scoping context only).

## Epic 6 — Eligibility Authority

- **Scope:** `PatientInsurance` (eligibility/verification authority
  per Final Schema Authorization Review §1), `PayerEligibilityCheck`
  (attempt/verification workflow), `EligibilityVerification`
  (structured eligibility state).
- **Existing structures:** `patient_insurances` (0 rows verified),
  `payer_eligibility_checks` (0 rows verified),
  `eligibility_verifications` (8 rows verified),
  `eligibility_source_documents` (4 rows verified); consumers
  `eligibility_check_router.py`, `eligibility_workflow_service.py`,
  `readiness_dashboard_service.py`.
- **Strategy:** REUSE both eligibility models as separate concepts
  (Final Schema Authorization Review §2, Option C). Cross-reference
  only. **No consolidation.**
- **Depends on:** Epic 5.

## Epic 7 — Claims

- **Scope:** `Claim`, `claim_edi_batches`.
- **Existing structures:** `claims` (4 rows verified),
  `claim_edi_batches` (0 rows verified).
- **Strategy:** REUSE. `_build_payer_block` continues sourcing the
  837I payer/subscriber block from `PatientPayer` via
  `msp_validation_service.py` (verified runtime behavior); no change
  to that sourcing is authorized here.
- **Depends on:** Epic 5, Epic 6.

## Epic 8 — Payment Posting

- **Scope:** `Payment`, `payment_adjustments`.
- **Existing structures:** `payments` (4 rows verified),
  `payment_adjustments` (8 rows verified); writer `payment_service.py`.
- **Strategy:** REUSE.
- **Depends on:** Epic 7.

## Epic 9 — ERA

- **Scope:** ERA ingestion / parsing as it feeds `RemittanceAdvice`.
- **Existing structures:** `remittance_advices` (4 rows verified) —
  ERA and Remittance are a combined entry per Schema Design Review's
  clarifying note (no separate ERA-only table found).
- **Strategy:** REUSE.
- **Depends on:** Epic 8.

## Epic 10 — Remittance

- **Scope:** `RemittanceAdvice` reconciliation against posted payments.
- **Existing structures:** `remittance_advices` (4 rows verified).
- **Strategy:** REUSE.
- **Depends on:** Epic 9.

## Epic 11 — NOE

- **Scope:** `NoeEdiSubmission`.
- **Existing structures:** `noe_edi_submissions` (0 rows verified);
  writer `noe.py`.
- **Strategy:** REUSE.
- **Depends on:** Epic 7.

## Epic 12 — CAP

- **Scope:** `HospiceCapRecord`.
- **Existing structures:** `hospice_cap_records` (0 rows verified);
  writer `hospice_cap.py`.
- **Strategy:** REUSE.
- **Depends on:** Epic 8.

## Epic 13 — Room & Board

- **Scope:** `facility_payment_expectations`,
  `facility_payment_allocations`, `facility_collection_alerts`,
  `facility_payment_audit_log`.
- **Existing structures:** verified counts 6 / 0 / 4 / 18
  respectively; `facility_payment_service.py`.
- **Strategy:** REUSE — already a cohesive, singularly-owned domain
  per Schema Design Review Section 7.
- **Depends on:** Epic 8.

## Epic 14 — Audit

- **Scope:** Domain-specific audit trail (`facility_payment_audit_log`)
  and generic `AuditLog` (1,106 rows verified). Append-only per locked
  Section 5 of the Billing Platform architecture (from earlier
  approved specifications).
- **Existing structures:** as above.
- **Strategy:** REUSE — the generic/domain-specific split is a
  deliberate, documented exception, not a duplicate (Schema Design
  Review Section 7).
- **Depends on:** cross-cutting; instrumented alongside Epics 1–13.

## Epic 15 — Reporting

- **Scope:** Reporting surfaces consuming Claims/Payment/ERA/
  Remittance/Room & Board/Audit data.
- **Existing structures:** none dedicated; consumes existing tables
  read-only.
- **Strategy:** REUSE existing data; no new reporting-authority table
  unless a future, separately authorized review finds one necessary.
  Export-authority duplication remains an open item carried from
  Schema Design Review Section 7 ("No duplicate export authority — NOT
  FULLY VERIFIED") and must be resolved before this epic's stories are
  finalized.
- **Depends on:** Epics 7–14.

## Epic 16 — Settings Integration

- **Scope:** User-facing terminology (e.g., "Medicare Part A Hospice"
  label, per the locked Billing Platform Settings Terminology Decision
  Record), payer/plan settings screens.
- **Existing structures:** internal enum `MEDICARE_HOSPICE` unchanged;
  no schema/migration required.
- **Strategy:** REUSE / display-layer only.
- **Depends on:** Epic 5 (payer/plan data it labels).

## Epic 17 — Security / Permissions

- **Scope:** Role-based access (`roles.py` — `PLATFORM_BILLING` vs.
  `BILLING`), `BillingProviderAgencyServiceScope.permission_level`
  (`VIEW`/`EDIT`).
- **Existing structures:** as above; foundation for every other epic's
  acceptance criteria.
- **Strategy:** REUSE — no duplicate permissions authority (locked
  rule).
- **Depends on:** none (foundation, sequenced first).

---

## Status Summary

17 epics defined, each mapped to existing, verified repository
structures with an explicit REUSE/EXTEND strategy. **No new physical
entity is proposed by any epic.** No `PatientCoverage`. No
consolidation of either locked pair. No duplicate authority for any
locked category.

**IMPLEMENTATION REMAINS BLOCKED.**
