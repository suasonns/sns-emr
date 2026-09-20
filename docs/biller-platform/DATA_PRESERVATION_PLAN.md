# Data Preservation Plan

## Status

**PLANNING ONLY.** For every locked authority, documents historical
preservation, protected records, protected references, protected
consumers, protected APIs, protected exports, and protected reports.
**No schema. No migrations. No code. No API. No UI. No data movement.
No deletion.**

---

## Patient Coverage Authority (PatientInsurance + PatientPayer + PatientFaceSheet)

- **Historical preservation:** All rows in `patient_insurances` (0
  verified), `patient_payers` (5 verified), `patient_facesheet` (5
  verified), and `facesheet_field_suggestions` (4 verified) remain
  untouched. No row is migrated, merged, or deleted under any future
  implementation of the approved link strategy.
- **Existing records protected:** All three models' current rows and
  schemas remain as-is; only an additive nullable FK is contemplated
  for a future phase, never a column removal or table drop.
- **Existing references protected:** `PayerEligibilityCheck`
  (mandatory FK to `PatientInsurance`), `EligibilityVerification`
  (optional FK to `PatientInsurance`), `ServiceCoverageDecision` (FK to
  `PatientPayer`) all remain intact.
- **Existing consumers protected:** eligibility-workflow services
  (`PatientInsurance`), `app/api/patients.py`/`claim_financials.py`/
  `credit_balance_service.py`/`facility_payment_service.py`/
  `msp_validation_service.py`/`claim_export_service.py`
  (`PatientPayer`), `admission_readiness_gate.py`/
  `eligibility_check_router.py`/`app/api/patients.py`/
  `app/api/referrals.py`/`seed_acceptance_patient.py`
  (`PatientFaceSheet`) — none require behavior change to remain
  functional.
- **Existing APIs protected:** `app/api/patients.py` CRUD for
  `PatientPayer` continues unmodified.
- **Existing exports protected:** `claim_export_service.py`'s 837I
  payer/subscriber block generation from `PatientPayer` is preserved
  exactly as-is.
- **Existing reports protected:** none identified as directly
  dependent on these three models beyond the consumers above; no
  report-specific risk found.

## Eligibility Authority (PayerEligibilityCheck + EligibilityVerification)

- **Historical preservation:** All rows in `payer_eligibility_checks`
  (0 verified), `eligibility_verifications` (8 verified), and
  `eligibility_source_documents` (4 verified) remain untouched.
  `EligibilityVerification`'s append-only (`superseded_at`) history is
  never rewritten.
- **Existing records protected:** both models' current rows and
  schemas remain as-is.
- **Existing references protected:** mandatory FK
  (`patient_insurance_id`) and optional FK (`payer_coverage_id`) both
  preserved.
- **Existing consumers protected:** `eligibility_check_router.py`,
  `eligibility_workflow_service.py`.
- **Existing APIs protected:** `eligibility_check_router.py` endpoints
  unchanged.
- **Existing exports protected:** none directly export these models
  today; no risk identified.
- **Existing reports protected:** none identified as directly
  dependent.

## BillingProviderAgencyAssignment Authority

- **Historical preservation:** The existing verified row in
  `billing_provider_agency_assignments` (1 verified) is never deleted
  or overwritten as part of the future delegation-code change; its
  current `relationship_status`/`effective_start_at`/
  `effective_end_at` values remain exactly as last written by whichever
  platform wrote them.
- **Existing records protected:** row-level history is preserved; no
  backfill or correction of historical write-race conditions is
  proposed (Final Schema Authorization Review §3.11 — no retroactive
  audit authorized).
- **Existing references protected:**
  `BillingProviderAgencyServiceScope` rows (2 verified) referencing
  this assignment remain intact.
- **Existing consumers protected:**
  `billing_provider_access_service.py` read-only resolution logic
  unaffected.
- **Existing APIs protected:** `billing_provider_router.py`
  (`POST`/`PATCH /assignments`) continues to function during the
  transition; `owner_admin.py::set_tenant_financials`'s external
  behavior (the "enable Financials for this tenant" action) is
  preserved even after it internally delegates instead of writing
  directly.
- **Existing exports protected:** none identified.
- **Existing reports protected:** none identified as directly
  dependent.

---

## Cross-Cutting Preservation Requirements

- **Audit trail:** `AuditLog` (1,106 rows verified) and
  `facility_payment_audit_log` (18 rows verified) remain append-only
  throughout every epic's implementation; no historical entry is ever
  altered or deleted (locked rule, Billing Platform Settings/Access
  specification, Section 5).
- **Legacy artifact:** `app/billing/store.py` (in-memory,
  non-persisted, superseded legacy artifact per
  `LEGACY_BILLING_SCHEMA_INVENTORY.md`) remains excluded from any live
  write path; no retirement action is proposed in this phase.
- **No historical migration rewrite:** the existing 116-file Alembic
  migration chain is never rewritten or stamped as part of any future
  implementation phase without a separate, explicit authorization.

## Status Summary

Data preservation requirements documented for all three locked
authorities plus cross-cutting audit/legacy-artifact requirements.
**No data movement, deletion, or retirement is proposed or authorized
by this document.**

**IMPLEMENTATION REMAINS BLOCKED.**
