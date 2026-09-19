# Domain Implementation Order

## Status

**PLANNING ONLY.** For each required billing domain: existing
authority, existing models, existing APIs, existing consumers, reuse
strategy, extension strategy, validation strategy, testing strategy.
**No schema. No migrations. No code. No API. No UI.**

---

## PatientInsurance

- **Existing authority:** Eligibility/verification authority (Final
  Schema Authorization Review §1, Option C).
- **Existing model:** `backend/app/models/patient_insurance.py`;
  table `patient_insurances` (0 rows verified).
- **Existing APIs:** no dedicated CRUD API confirmed in prior
  discovery; written via eligibility-workflow services.
- **Existing consumers:** `PayerEligibilityCheck` (mandatory FK),
  `EligibilityVerification` (optional FK via `payer_coverage_id`),
  `eligibility_check_router.py`, `eligibility_workflow_service.py`,
  `readiness_dashboard_service.py`.
- **Reuse strategy:** REUSE as-is.
- **Extension strategy:** future nullable FK to `PatientPayer` (shape
  only, per Migration Design Review Section 1.2); no schema change in
  this phase.
- **Validation strategy:** confirm both eligibility models' FK
  integrity is unaffected by any future link.
- **Testing strategy:** regression test of eligibility-workflow read/
  write paths.

## PatientPayer

- **Existing authority:** Billing/financial authority (Final Schema
  Authorization Review §1, Option C).
- **Existing model:** `backend/app/models/patient_payer.py`; table
  `patient_payers` (5 rows verified); no direct `tenant_id` (scoped
  via `patient_id → patients.tenant_id`).
- **Existing APIs:** `app/api/patients.py` CRUD (lines 3244–3389).
- **Existing consumers:** `claim_financials.py`,
  `credit_balance_service.py`, `facility_payment_service.py`,
  `msp_validation_service.py` → `claim_export_service.py` (verified
  837I payer/subscriber block source).
- **Reuse strategy:** REUSE as-is; remains the verified claim-export
  authority.
- **Extension strategy:** future nullable FK to `PatientInsurance`
  (shape only); no schema change in this phase.
- **Validation strategy:** confirm claim export behavior is unchanged.
- **Testing strategy:** regression test of `app/api/patients.py` CRUD
  and claim-export payer-block generation.

## PatientFaceSheet

- **Existing authority:** Documentation/presentation structure only
  (Final Schema Authorization Review §1) — **not** coverage authority.
- **Existing model:** `backend/app/models/patient_facesheet.py`;
  table `patient_facesheet` (5 rows verified);
  `facesheet_field_suggestions` (4 rows verified, ownerless OCR
  staging queue).
- **Existing APIs:** facesheet-domain services/APIs (not exhaustively
  re-enumerated in this pass).
- **Existing consumers:** `claim_export_service.py`
  (attending-physician block only), `admission_readiness_gate.py`,
  `eligibility_check_router.py`, `app/api/patients.py`,
  `app/api/referrals.py`, `seed_acceptance_patient.py`.
- **Reuse strategy:** REUSE as-is.
- **Extension strategy:** none authorized; excluded from the
  `PatientInsurance`/`PatientPayer` link per locked decision. The
  `SourceOfTruthMatrix.md` SSOT-claim conflict remains an open,
  non-schema documentation-correction item (Final Schema
  Authorization Review §1.11).
- **Validation strategy:** confirm no consumer begins treating this
  as coverage authority.
- **Testing strategy:** regression test of attending-physician block
  and admission/authorization consumers.

## PayerEligibilityCheck

- **Existing authority:** Attempt/verification workflow (Final Schema
  Authorization Review §2, Option C).
- **Existing model:** `backend/app/models/payer_eligibility_check.py`;
  table `payer_eligibility_checks` (0 rows verified); mandatory FK to
  `patient_insurance_id`; creation migration `a2d6f8b1c4e9`.
- **Existing APIs:** `eligibility_check_router.py`.
- **Existing consumers:** `eligibility_workflow_service.py`,
  `test_eligibility_workflow_service.py`,
  `test_eligibility_roster_endpoint.py`.
- **Reuse strategy:** REUSE as-is; remains separate from
  `EligibilityVerification`.
- **Extension strategy:** optional future cross-reference FK to
  `EligibilityVerification` (shape only, Migration Design Review
  Section 2.2); no schema change in this phase.
- **Validation strategy:** confirm `result_status` domain
  (ACTIVE/INACTIVE/UNKNOWN/ERROR) unchanged.
- **Testing strategy:** regression test of check-attempt logging.

## EligibilityVerification

- **Existing authority:** Structured eligibility state (Final Schema
  Authorization Review §2, Option C).
- **Existing model:** `backend/app/models/eligibility_verification.py`;
  table `eligibility_verifications` (8 rows verified),
  `eligibility_source_documents` (4 rows verified); mandatory FK to
  `source_document_id`; optional FK to `patient_insurances` via
  `payer_coverage_id`; append-only via `superseded_at`; creation
  migration `x3y4z5a6b7c8`.
- **Existing APIs:** `eligibility_check_router.py`.
- **Existing consumers:** `eligibility_workflow_service.py` and the
  same test files as `PayerEligibilityCheck`.
- **Reuse strategy:** REUSE as-is; remains separate.
- **Extension strategy:** same optional future cross-reference as
  above; append-only behavior must not be altered.
- **Validation strategy:** confirm `superseded_at` append-only pattern
  is preserved.
- **Testing strategy:** regression test of document-sourced
  verification creation and supersession.

## BillingProviderOrganization

- **Existing authority:** Provider master (Schema Design Review
  Section 4 — EXTEND sufficient).
- **Existing model:** table `billing_provider_organizations` (1 row
  verified).
- **Existing APIs:** `billing_provider_router.py` (full CRUD).
- **Existing consumers:** `owner_admin.py` (read-only lookups),
  `billing_provider_access_service.py` (read-only).
- **Reuse strategy:** REUSE.
- **Extension strategy:** none required at this time.
- **Validation strategy:** confirm Biller-only write authority is
  preserved.
- **Testing strategy:** regression test of organization CRUD.

## BillingProviderAgencyAssignment

- **Existing authority:** Verified dual-write structure; future
  authority = Biller Platform operational, Owner Platform delegates
  (Final Schema Authorization Review §3, Option B).
- **Existing model:** table `billing_provider_agency_assignments` (1
  row verified).
- **Existing APIs:** `billing_provider_router.py` (`POST
  /assignments`, `PATCH /assignments/{id}`); `owner_admin.py::
  set_tenant_financials`.
- **Existing consumers:** `billing_provider_access_service.py`.
- **Reuse strategy:** REUSE existing table; **no schema change.**
- **Extension strategy:** future, separately authorized code-path
  change so `owner_admin.py` delegates instead of writing directly
  (Implementation Stories Epic 3, Story 3.1).
- **Validation strategy:** confirm single write path post-change;
  confirm no service-scope asymmetry remains.
- **Testing strategy:** regression + future integration test of
  delegated assignment creation.

## BillingProviderAgencyServiceScope

- **Existing authority:** Per-assignment capability + permission level
  (Schema Design Review Section 4).
- **Existing model:** table `billing_provider_agency_service_scopes`
  (2 rows verified); 15-value scope enum + `permission_level`
  (`VIEW`/`EDIT`).
- **Existing APIs:** `billing_provider_router.py`.
- **Existing consumers:** `billing_provider_access_service.py`.
- **Reuse strategy:** REUSE.
- **Extension strategy:** none required; enum already covers every
  domain concept identified.
- **Validation strategy:** confirm every assignment eventually has at
  least one scope row (post Epic 3/4 remediation).
- **Testing strategy:** regression test of scope CRUD and permission
  checks.

## Claim

- **Existing authority:** `Claim`/`claim_edi_batches` (singular,
  Schema Design Review Section 7).
- **Existing model:** tables `claims` (4 rows verified),
  `claim_edi_batches` (0 rows verified).
- **Existing APIs:** claim-domain services (`billing_engine.py`
  writer).
- **Existing consumers:** `claim_export_service.py`,
  `msp_validation_service.py`.
- **Reuse strategy:** REUSE.
- **Extension strategy:** none required.
- **Validation strategy:** confirm `app/billing/store.py` (superseded,
  non-persisted legacy artifact) remains excluded from any live path.
- **Testing strategy:** regression test of claim creation/export.

## Payment

- **Existing authority:** `payments`/`payment_adjustments` (singular).
- **Existing model:** tables `payments` (4 rows verified),
  `payment_adjustments` (8 rows verified).
- **Existing APIs:** `payment_service.py` (writer).
- **Existing consumers:** reconciliation and reporting paths.
- **Reuse strategy:** REUSE.
- **Extension strategy:** none required.
- **Validation strategy:** confirm single-writer status unchanged.
- **Testing strategy:** regression test of payment posting/adjustment.

## ERA

- **Existing authority:** combined with Remittance (no separate ERA
  table; Schema Design Review clarifying note).
- **Existing model:** see `remittance_advices`.
- **Existing APIs:** remittance ingestion path.
- **Existing consumers:** payment reconciliation.
- **Reuse strategy:** REUSE.
- **Extension strategy:** none required; no separate ERA table to be
  introduced.
- **Validation strategy:** confirm no duplicate ERA authority created.
- **Testing strategy:** regression test of ERA ingestion.

## Remittance

- **Existing authority:** `remittance_advices` (singular).
- **Existing model:** table `remittance_advices` (4 rows verified).
- **Existing APIs:** remittance-domain services.
- **Existing consumers:** payment reconciliation, reporting.
- **Reuse strategy:** REUSE.
- **Extension strategy:** none required.
- **Validation strategy:** confirm reconciliation logic unaffected by
  upstream changes.
- **Testing strategy:** regression test of remittance-to-payment
  matching.

## Room & Board

- **Existing authority:** `facility_payment_expectations`/
  `allocations`/`collection_alerts`/`facility_payment_audit_log`
  (cohesive, singularly-owned domain).
- **Existing model:** tables with verified counts 6 / 0 / 4 / 18
  respectively.
- **Existing APIs:** `facility_payment_service.py`.
- **Existing consumers:** facility collection/reporting workflows.
- **Reuse strategy:** REUSE.
- **Extension strategy:** none required.
- **Validation strategy:** confirm end-to-end chain integrity
  (expectation → allocation → alert → audit log).
- **Testing strategy:** regression test across the full chain.

---

## Status Summary

All 13 required domains documented with existing authority, models,
APIs, consumers, and REUSE/EXTEND-only strategies. **No new physical
model proposed for any domain.** No `PatientCoverage`. No
consolidation of either locked pair.

**IMPLEMENTATION REMAINS BLOCKED.**
