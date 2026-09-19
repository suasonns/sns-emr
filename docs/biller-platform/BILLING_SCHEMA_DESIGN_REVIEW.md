# Billing Schema Design Review

## Status

**DESIGN-REVIEW DOCUMENT ONLY.** Not an implementation plan, not a
migration plan, not a coding task. No schema changes, migrations, APIs,
UI work, backfills, data movement, deletions, or retirements are
authorized by this document. A separate Migration Review and
Implementation Authorization phase is required after this document is
reviewed and approved.

## Discovery Baseline (Carried Forward, Locked)

Completed: Repository Grounding Correction; Tenant/Biller
System-of-Record Matrix; Legacy Billing Inventory; Owner Platform
Billing Investigation; Ownership Boundaries Review; PatientInsurance
Analysis.

Approved findings carried forward without re-litigation:
- Billing was excluded from Owner Platform architecture, not removed
  from implementation.
- `BillingProviderOrganization` and `BillingProviderAgencyAssignment`
  are active existing structures.
- No third `PatientCoverage` model is authorized.
- Existing billing entities should be reused where possible.
- Duplicate payer, claim, payment, ERA, remittance, denial, and Room &
  Board authorities are prohibited.

Open findings carried forward, still unresolved:
- Patient Coverage Authority.
- Eligibility Authority.
- `BillingProviderAgencyAssignment` dual-write conflict.

All facts in this document are grounded in
`REPOSITORY_GROUNDING_CORRECTION_REPORT.md` (the standard requiring
every ownership claim to pass the 5-criteria evidence test, not
assumption),
`TENANT_BILLER_SYSTEM_OF_RECORD_MATRIX.md`,
`LEGACY_BILLING_SCHEMA_INVENTORY.md`,
`PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`, and
`TENANT_BILLER_OWNERSHIP_BOUNDARIES.md`. Record counts are the
verified, read-only counts captured in the Legacy Inventory's
Additional Discovery Pass; they are not re-queried here.

---

## Section 1 — System of Record Review

Format per concept: Current Authority | Current Tables | Current
Consumers | Current Scope | Current Ownership | Current Write
Authority | Duplicate Structures | Repository Evidence | Required
Action.

### Payer

- Current Authority: `Payer` model, the payer master/reference record.
- Current Tables: `payers` (0 rows).
- Current Consumers: `payer_contracts` (FK), `PatientPayer`
  (payer-identifying fields, not FK-verified to `payers` in this pass),
  claim/eligibility services that resolve payer type/name.
- Current Scope: Tenant-facing reference data used across billing
  workflows.
- Current Ownership: BILLER OWNED.
- Current Write Authority: Not independently re-traced in this pass;
  no competing writer identified in any prior document.
- Duplicate Structures: None found. `PatientPayer.payer_name`/
  `payer_type` store payer identity redundantly at the patient level
  rather than via a verified FK to `payers` — flagged as a data-quality
  question, not a duplicate authority.
- Repository Evidence: `backend/app/billing/models/payer.py` (baseline
  migration `521d501c6eea`).
- Required Action: **REUSE.**

### PatientInsurance

- Current Authority: Eligibility-workflow coverage record.
- Current Tables: `patient_insurances` (0 rows).
- Current Consumers: `PayerEligibilityCheck`, `EligibilityVerification`,
  `eligibility_check_router.py`, `eligibility_workflow_service.py`,
  `readiness_dashboard_service.py`.
- Current Scope: Tenant-scoped (`TenantScopedMixin`), unique on
  `(tenant_id, patient_id, coverage_scope, priority_order)`.
- Current Ownership: **UNRESOLVED** (see Section 2).
- Current Write Authority: Eligibility-workflow services; no CRUD API
  confirmed in this pass.
- Duplicate Structures: Overlaps `PatientPayer` and `PatientFaceSheet`
  on payer-identity fields — see Section 2.
- Repository Evidence:
  `backend/app/models/patient_insurance.py`;
  `PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`.
- Required Action: **REUSE for eligibility workflow; ownership decision
  deferred to Section 2.**

### PatientPayer

- Current Authority: Billing/financial-responsibility sequencing
  record.
- Current Tables: `patient_payers` (5 rows).
- Current Consumers: `app/api/patients.py` (direct CRUD, lines
  3244–3389), `claim_financials.py`, `credit_balance_service.py`,
  `facility_payment_service.py`, `msp_validation_service.py` →
  `claim_export_service.py` (verified source of the actual 837I
  payer/subscriber block).
- Current Scope: **Not tenant-scoped directly** — no `tenant_id`
  column; scope is indirect via `patient_id → patients.tenant_id`.
- Current Ownership: **UNRESOLVED** (see Section 2).
- Current Write Authority: `app/api/patients.py` CRUD endpoints.
- Duplicate Structures: Overlaps `PatientInsurance` and
  `PatientFaceSheet` on payer-identity fields — see Section 2.
- Repository Evidence: `backend/app/models/patient_payer.py`;
  `claim_export_service.py` lines 268–296.
- Required Action: **REUSE for claim/financial-sequencing workflow;
  ownership decision deferred to Section 2.**

### PatientFaceSheet

- Current Authority: Documented (by
  `docs/workflows/SourceOfTruthMatrix.md`) as the declared
  Source-of-Truth for demographic and insurance identifier fields.
- Current Tables: `patient_facesheet` (5 rows);
  `facesheet_field_suggestions` (4 rows, ownerless OCR staging queue,
  never authoritative).
- Current Consumers: `claim_export_service.py` (attending-physician
  block only, verified — **not** the payer/subscriber block),
  `admission_readiness_gate.py`, `eligibility_check_router.py`,
  `app/api/patients.py`, `app/api/referrals.py`,
  `seed_acceptance_patient.py`.
- Current Scope: Explicit `tenant_id` column with FK+index.
- Current Ownership: **UNRESOLVED** (see Section 2) — despite the
  self-declared SSOT claim, verified runtime behavior does not fully
  match it.
- Current Write Authority: Facesheet-domain services/APIs; not
  exhaustively re-enumerated in this pass.
- Duplicate Structures: Directly overlaps `PatientInsurance` and
  `PatientPayer` on `primary_payer`/`subscriber_id`/policy-number
  fields — the central open question of Section 2.
- Repository Evidence: `backend/app/models/patient_facesheet.py`;
  `docs/architecture/InsuranceMappingReconciliation.md`;
  `docs/workflows/SourceOfTruthMatrix.md`.
- Required Action: **REUSE; ownership decision deferred to Section 2.
  DO NOT CREATE a fourth structure to resolve this.**

### Eligibility Models (`PayerEligibilityCheck`, `EligibilityVerification`)

- Current Authority: Two distinct, non-duplicate eligibility record
  types — see Section 3 for the full comparison.
- Current Tables: `payer_eligibility_checks` (0 rows),
  `eligibility_verifications` (8 rows), `eligibility_source_documents`
  (4 rows).
- Current Consumers: `eligibility_check_router.py`,
  `eligibility_workflow_service.py`,
  `test_eligibility_workflow_service.py`,
  `test_eligibility_roster_endpoint.py`.
- Current Scope: `PayerEligibilityCheck` is mandatorily FK'd to
  `patient_insurance_id`; `EligibilityVerification` is mandatorily
  FK'd to `source_document_id` and optionally (`nullable=True`) FK'd
  to `patient_insurances` via `payer_coverage_id`.
- Current Ownership: BILLER OWNED (eligibility-workflow domain);
  internal authority split between the two models is UNRESOLVED (see
  Section 3).
- Current Write Authority: Eligibility-workflow services.
- Duplicate Structures: Narrow risk only — no constraint prevents the
  two models' independent status fields from disagreeing for the same
  coverage. Not a full duplicate per the field-level review already
  performed.
- Repository Evidence:
  `backend/app/models/payer_eligibility_check.py`,
  `backend/app/models/eligibility_verification.py`; migration
  `a2d6f8b1c4e9` (checks), `x3y4z5a6b7c8` (verifications + source
  documents).
- Required Action: **REUSE both; DO NOT CONSOLIDATE in this phase.**

### Claim

- Current Authority: `Claim` / `claims`, `claim_edi_batches`.
- Current Tables: `claims` (4 rows), `claim_edi_batches` (0 rows).
- Current Consumers: `claim_export_service.py`,
  `billing_readiness_service.py`, billing readiness test suite.
- Current Scope: Tenant-scoped.
- Current Ownership: BILLER OWNED.
- Current Write Authority: Biller Platform claim-generation/export
  services.
- Duplicate Structures: `app/billing/store.py` is a superseded,
  never-persisted, in-memory pre-`claims` placeholder — already
  documented and gated in `LEGACY_BILLING_SCHEMA_INVENTORY.md`; not a
  live competing authority.
- Repository Evidence: migration `d8a1f3c6e2b4`;
  `claim_export_service.py`.
- Required Action: **REUSE.**

### Payment

- Current Authority: `payments`.
- Current Tables: `payments` (4 rows).
- Current Consumers: `payment_adjustments`, `remittance_advices`
  (co-created in the same migration), credit-balance and facility
  payment services.
- Current Scope: Tenant-scoped.
- Current Ownership: BILLER OWNED.
- Current Write Authority: Payment-posting services (not
  independently re-traced this pass).
- Duplicate Structures: None found.
- Repository Evidence: migration `e1b7c9d4f8a2`.
- Required Action: **REUSE.**

### ERA / Remittance

Note: ERA and Remittance are documented together because both terms
refer to the same underlying structure in this repository — there is
no separate "ERA" table distinct from `remittance_advices`. Listed
individually below only to satisfy the review checklist's separate
line items; this is one authority, not two.

- Current Authority: `remittance_advices` (835-derived remittance
  data, serving both the "ERA" and "Remittance" checklist concepts).
- Current Tables: `remittance_advices` (4 rows).
- Current Consumers: Payment-posting/reconciliation services; no
  automated 835 ingestion pipeline was confirmed to exist in this or
  prior passes (flagged previously as NOT VERIFIED / likely absent).
- Current Scope: Tenant-scoped.
- Current Ownership: BILLER OWNED.
- Current Write Authority: Payment-posting domain.
- Duplicate Structures: None found.
- Repository Evidence: migration `e1b7c9d4f8a2`.
- Required Action: **REUSE.**

### Denial

- Current Authority: `denials`.
- Current Tables: `denials` (0 rows).
- Current Consumers: Denials/appeals workflow (co-created with
  `appeals` in the same migration); no dedicated service file was
  independently re-opened in this pass.
- Current Scope: Tenant-scoped.
- Current Ownership: BILLER OWNED.
- Current Write Authority: Not independently re-traced this pass.
- Duplicate Structures: None found.
- Repository Evidence: migration `f3a9c1e7b5d0`.
- Required Action: **REUSE.**

### Appeal

- Current Authority: `appeals`.
- Current Tables: `appeals` (0 rows).
- Current Consumers: Same as Denial (co-created).
- Current Scope: Tenant-scoped.
- Current Ownership: BILLER OWNED.
- Current Write Authority: Not independently re-traced this pass.
- Duplicate Structures: None found.
- Repository Evidence: migration `f3a9c1e7b5d0`.
- Required Action: **REUSE.**

### Credit Balance

- Current Authority: `credit_balance_cases`.
- Current Tables: `credit_balance_cases` (0 rows).
- Current Consumers: `credit_balance_service.py`,
  `test_credit_balance_report.py`, `PatientPayer` (via
  `credit_balance_service.py`).
- Current Scope: Tenant-scoped.
- Current Ownership: BILLER OWNED.
- Current Write Authority: `credit_balance_service.py`.
- Duplicate Structures: None found.
- Repository Evidence: migration `f5a6b7c8d9e0`.
- Required Action: **REUSE.**

### NOE

- Current Authority: `noe_edi_submissions`.
- Current Tables: `noe_edi_submissions` (0 rows).
- Current Consumers: NOE/EDI submission workflow (not independently
  re-opened this pass).
- Current Scope: Tenant-scoped.
- Current Ownership: BILLER OWNED.
- Current Write Authority: Not independently re-traced this pass.
- Duplicate Structures: None found.
- Repository Evidence: migration `9a8c04c006b3`.
- Required Action: **REUSE.**

### CAP

- Current Authority: `hospice_cap_records`.
- Current Tables: `hospice_cap_records` (0 rows).
- Current Consumers: CAP-monitoring workflow (not independently
  re-opened this pass); `BILLING_PROVIDER_SERVICE_SCOPES` includes a
  `CAP_MONITORING` scope value, confirming CAP is a modeled service
  scope for `BillingProviderAgencyServiceScope`.
- Current Scope: Tenant-scoped.
- Current Ownership: BILLER OWNED.
- Current Write Authority: Not independently re-traced this pass.
- Duplicate Structures: None found.
- Repository Evidence: migration `fe9eb2571468`;
  `billing_provider_agency_assignment.py`
  (`BILLING_PROVIDER_SERVICE_SCOPES`).
- Required Action: **REUSE.**

### Room & Board

- Current Authority: Facility Payment domain —
  `facility_payment_expectations`, `facility_payment_allocations`,
  `facility_collection_alerts`, `facility_payment_audit_log`.
- Current Tables: `facility_payment_expectations` (6 rows),
  `facility_payment_allocations` (0 rows),
  `facility_collection_alerts` (4 rows), `facility_payment_audit_log`
  (18 rows).
- Current Consumers: `facility_payment_service.py`,
  `test_facility_payment_visibility.py`.
- Current Scope: Tenant-scoped.
- Current Ownership: BILLER OWNED.
- Current Write Authority: `facility_payment_service.py`. Confirmed by
  code comment (line 1824–1826) that overdue-expectation evaluation is
  called opportunistically, with no scheduler/cron job introduced.
- Duplicate Structures: None found.
- Repository Evidence: migration `g1h2i3j4k5l6`.
- Required Action: **REUSE.**

### BillingProviderOrganization

- Current Authority: Billing-company/provider master record.
- Current Tables: `billing_provider_organizations` (1 row).
- Current Consumers: `billing_provider_router.py`,
  `owner_admin.py::set_tenant_financials` (read-only for this table).
- Current Scope: Platform-wide (not tenant-scoped by design — it
  represents an entity that services tenants).
- Current Ownership: BILLER OWNED.
- Current Write Authority: `billing_provider_router.py` only — no
  conflict (see `TENANT_BILLER_OWNERSHIP_BOUNDARIES.md` Section 2.1).
- Duplicate Structures: None found.
- Repository Evidence: migration `h1i2j3k4l5m6`;
  `TENANT_BILLER_OWNERSHIP_BOUNDARIES.md` Section 2.1.
- Required Action: **REUSE / EXTEND** (see Section 4 for extension
  strategy).

### BillingProviderAgencyAssignment

- Current Authority: Tenant-to-provider link with effective dating and
  relationship status.
- Current Tables: `billing_provider_agency_assignments` (1 row).
- Current Consumers: `billing_provider_router.py` (create/update),
  `owner_admin.py::set_tenant_financials` (create/update — **verified
  dual writer**), `billing_provider_access_service.py` (read-only
  financials-enabled computation).
- Current Scope: Tenant-linked (`tenant_id` FK).
- Current Ownership: **CONTESTED — write-authority conflict, not
  resolved** (see Section 5, and
  `TENANT_BILLER_OWNERSHIP_BOUNDARIES.md` Section 2.2).
- Current Write Authority: Two independent code paths (see Section 5).
- Duplicate Structures: None — the conflict is a dual-writer issue, not
  a duplicate-table issue.
- Repository Evidence: migration `h1i2j3k4l5m6`;
  `billing_provider_router.py` lines 311, 386; `owner_admin.py` line
  700.
- Required Action: **REUSE — but write-authority conflict must be
  resolved before further extension (see Section 5); no action
  authorized here.**

### BillingProviderAgencyServiceScope

- Current Authority: Per-assignment, per-capability scope + permission
  level (`VIEW`/`EDIT`) across 15 defined scope values including
  `CLAIMS`, `ELIGIBILITY`, `PAYMENT_POSTING`, `CAP_MONITORING`, etc.
- Current Tables: `billing_provider_agency_service_scopes` (2 rows).
- Current Consumers: `billing_provider_router.py` (creation only, at
  assignment-creation time), `billing_provider_access_service.py`
  (read-only permission resolution).
- Current Scope: Assignment-linked (`assignment_id` FK,
  `CASCADE`/`delete-orphan`).
- Current Ownership: BILLER OWNED.
- Current Write Authority: `billing_provider_router.py` only. Note the
  verified asymmetry: assignments created via `owner_admin.py` receive
  no service-scope rows at creation time.
- Duplicate Structures: None found.
- Repository Evidence: migration `h1i2j3k4l5m6`;
  `billing_provider_agency_assignment.py`
  (`BILLING_PROVIDER_SERVICE_SCOPES`/`BILLING_PROVIDER_PERMISSION_LEVELS`).
- Required Action: **REUSE / EXTEND** (see Section 4).

### Audit

- Current Authority: `AuditLog` (generic, cross-domain) and
  `FacilityPaymentAuditLog` (Room & Board specific).
- Current Tables: `audit_logs` (1,106 rows),
  `facility_payment_audit_log` (18 rows).
- Current Consumers: Cross-platform (clinical, billing, owner) per
  `owner_admin.py` line 810 comment.
- Current Scope: Both tenant- and cross-domain-scoped as applicable.
- Current Ownership: SHARED in practice (generic log), BILLER OWNED
  (domain-specific log) — not formally re-evaluated against the
  5-criteria SHARED DOMAIN OWNED test in this pass; carried forward
  from the Legacy Inventory's REUSE finding.
- Current Write Authority: Cross-platform for the generic log;
  Biller-Platform-only for the domain-specific log.
- Duplicate Structures: None — deliberate narrow exception, not a
  duplicate.
- Repository Evidence: `backend/app/models/audit_log.py`;
  `backend/app/billing/models/facility_payment_audit_log.py`.
- Required Action: **REUSE.**

### Export

- Current Authority: `claim_export_service.py` (837I claim export
  pipeline). No dedicated "Export Event" model was found.
- Current Tables: None dedicated — export activity is not itself
  persisted in a distinct table (open item, not resolved here).
- Current Consumers: Claim-export/EDI-generation workflow.
- Current Scope: Tenant-scoped (via `claims`/`patients`).
- Current Ownership: BILLER OWNED.
- Current Write Authority: `claim_export_service.py`.
- Duplicate Structures: A prior `claim_builder.py` and
  `export_router.py` were deleted from git history, superseded by the
  current `claim_export_service.py` — historical churn, not a live
  duplicate.
- Repository Evidence: `claim_export_service.py`; git history
  (deletion of `claim_builder.py`, `export_router.py`).
- Required Action: **REUSE** for claim export. **TENTATIVE CREATE**
  flagged only as an open question (not decided here) for whether a
  dedicated "Export Event" audit record should exist — no
  justification has been developed for it in this document, so it is
  not a live CREATE recommendation, only a noted gap.

---

## Section 2 — Patient Coverage Authority Review

**CURRENT STATUS: UNRESOLVED.**

`PatientInsurance`, `PatientPayer`, and `PatientFaceSheet` represent
**overlapping concepts with distinct primary purposes**, not a single
authority, not fully independent authorities, and not yet provably
reconcilable without further evidence:

- Data owned by `PatientInsurance`: eligibility-workflow evidence —
  `subscriber_id`, `group_number`, `coverage_scope`, `priority_order`,
  `is_active`, `verified_at`/`verified_by`/`eligibility_status`/
  `next_verification_due`.
- Data owned by `PatientPayer`: financial-responsibility sequencing —
  `payer_name`, `payer_type`, `subscriber_id`, `subscriber_id_type`,
  `msp_type_code`, `sequence_code`, `priority_order`, `is_primary`.
- Data owned by `PatientFaceSheet`: denormalized patient-snapshot
  insurance identifiers — `primary_payer`, `primary_payer_type`,
  `primary_policy_number`, `secondary_payer`, `secondary_payer_type`,
  `secondary_policy_number`, `mbi_number`, `subscriber_name`,
  `subscriber_relationship`, `subscriber_id`, plus authorization and
  payer-verification-audit fields.
- Data not owned by any of the three exclusively: none of the three
  fields are proven to be authoritative over the other two for the
  same identifier (e.g., `subscriber_id` appears on all three with no
  verified reconciliation rule).
- Consumers: eligibility workflow (`PatientInsurance`), claim export
  and financial sequencing (`PatientPayer`), admission/authorization
  workflow and OCR-suggestion intake (`PatientFaceSheet`).
- Relationships: `PatientInsurance` is FK'd by both eligibility models;
  `PatientPayer` is the FK target of `ServiceCoverageDecision`;
  `PatientFaceSheet` has no confirmed FK relationship to either of the
  other two.
- Historical value: all three are actively written and consumed;
  none is dormant or superseded.
- Required extensions: not decided in this document.
- Required links: an explicit FK between the three (or between
  `PatientFaceSheet` and whichever of `PatientInsurance`/`PatientPayer`
  is determined authoritative for a given field) is the most-likely
  future need, per the analysis in
  `PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`, but is **not authorized
  here**.

**No creation of `PatientCoverage` as a third physical model is
authorized by this section**, consistent with the explicit prohibition
carried forward from every prior review.

---

## Section 3 — Eligibility Authority Review

**CURRENT STATUS: UNRESOLVED.**

- `PayerEligibilityCheck`: mandatory FK to `patient_insurance_id`;
  lightweight per-attempt check log; simple `result_status`
  (ACTIVE/INACTIVE/UNKNOWN/ERROR).
- `EligibilityVerification`: mandatory FK to `source_document_id`;
  richer, document-sourced, hospice-specific structured tri-state
  findings model (~25 facts across 3 JSONB columns); optional
  (`nullable=True`) FK to `patient_insurances` via `payer_coverage_id`;
  append-only via `superseded_at`; deliberately different status
  domain (`NOT_RUN`/`PENDING`/`VERIFIED_ACTIVE`/etc.).
- Ownership: BILLER OWNED for both, at the platform level; internal
  authority between the two models (which one is authoritative for a
  given coverage's current eligibility state) is **not resolved**.
- Consumers: `eligibility_check_router.py`,
  `eligibility_workflow_service.py`, and the confirmed test files
  listed in Section 1.
- Relationships: both ultimately trace to `PatientInsurance`, one
  mandatorily and one optionally — this is itself evidence that
  `PatientInsurance` is the more likely eligibility-authority anchor of
  the two, but this document does not decide that.
- Data overlap: narrow — only the risk that the two models' status
  fields could disagree for the same coverage, since no constraint
  reconciles them.
- Authority: **UNRESOLVED.**
- Duplication risk: low-to-moderate, confined to status-field
  disagreement, not full structural duplication.
- Recommended future direction: further evaluation of whether
  `EligibilityVerification` should become the sole authority for
  hospice-specific eligibility state (given its richer, document-backed
  model) while `PayerEligibilityCheck` remains a lightweight audit log
  of individual check attempts feeding it — **not decided or
  authorized here.**

**No consolidation of these two models is authorized during this
phase.**

---

## Section 4 — BillingProvider Review

- Current authority: `BillingProviderOrganization` (provider master),
  `BillingProviderOrganizationMembership` (which users belong to a
  provider org, 1 row), `BillingProviderAgencyAssignment`
  (provider-to-tenant link), `BillingProviderAgencyServiceScope`
  (per-assignment capability + permission level).
- Current consumers: `billing_provider_router.py` (full CRUD across
  all four), `owner_admin.py` (assignment creation/update only, plus
  read-only organization/membership lookups),
  `billing_provider_access_service.py` (read-only permission/financials
  resolution).
- Current ownership: BILLER OWNED for all four, with the one proven
  exception on `BillingProviderAgencyAssignment` (Section 5).
- Future extension strategy: `BillingProviderAgencyServiceScope`
  already models a 15-value scope enum
  (`BILLING_READINESS`/`CLAIMS`/`NOE_TRACKING`/`ELIGIBILITY`/
  `AUTHORIZATION_TRACKING`/`PAYMENT_POSTING`/`PAYMENT_RECONCILIATION`/
  `FACILITY_COLLECTIONS`/`CREDIT_BALANCES`/`AGING_REPORT`/
  `DENIALS_APPEALS`/`EDI`/`BILLING_REPORTS`/`FINANCIAL_MONITORING`/
  `CAP_MONITORING`) plus a `VIEW`/`EDIT` permission level — this already
  covers every domain concept required by Section 1's "Required
  concepts" list.
- Coverage-assignment capability: not modeled here — coverage
  (patient-level payer/insurance data) is a distinct concern from
  provider-level agency assignment; no evidence found that
  `BillingProviderAgencyAssignment` is intended to model
  patient-coverage assignment.
- Agency-assignment capability: **present and active** —
  `BillingProviderAgencyAssignment` is exactly this.
- Team capability: `BillingProviderOrganizationMembership` provides a
  user-to-provider-organization membership record; no further
  team/sub-team structure was found.
- Hierarchy capability: no administrative-hierarchy structure was
  found among these four models; this is a distinct, separately
  reviewed concern (see the already-approved
  Administrative-Hierarchy-Relationship design from Section 24 of
  `BILLING_ORGANIZATION_DISCOVERY_REPORT.md`, Option B).
- Permission capability: `BillingProviderAgencyServiceScope.permission_level`
  (`VIEW`/`EDIT`) is the only permission granularity found at this
  layer; whether it is sufficient for future needs is not decided here.
- **EXTEND is sufficient** for all four models as currently defined —
  no evidence was found that any of the four require a new physical
  structure. **TENTATIVE CREATE is not recommended** for any
  BillingProvider-domain structure in this document.

---

## Section 5 — Dual-Write Review

- Structure: `BillingProviderAgencyAssignment`.
- Current writers: (1) `billing_provider_router.py`
  (`POST /assignments` line 311, `PATCH /assignments/{id}` line 386 —
  Biller Platform); (2) `owner_admin.py::set_tenant_financials` (line
  656; creates a row at line 700 or mutates
  `relationship_status = "ACTIVE"` on an existing row — Owner
  Platform).
- Current purpose: Biller Platform's path is general-purpose
  assignment management (create, update, scope, suspend, terminate).
  Owner Platform's path is narrowly scoped to the "enable Financials
  for this tenant" administrative action, gated on `ein`+`ptan` and an
  `ACTIVE` `BillingProviderOrganization`.
- Current risks: (a) both paths can set `relationship_status` and
  `effective_start_at`/`effective_end_at` with no reconciliation rule,
  risking silent overwrite of one platform's change by the other; (b)
  rows created via Owner Platform receive no
  `BillingProviderAgencyServiceScope` rows, leaving them without scoped
  permissions until a Biller Platform actor separately adds them — a
  verified behavioral asymmetry, not a hypothetical one; (c) no
  optimistic-locking column or audit trail distinguishing which
  platform last wrote a given row was found.
- Potential authority options (analysis only, already presented in
  full in `TENANT_BILLER_OWNERSHIP_BOUNDARIES.md` Section 4): single
  writer with Owner Platform delegating to Biller Platform; single
  writer with Biller Platform delegating to Owner Platform; field-level
  split ownership.
- **No implementation recommendation is made here beyond what is
  already recorded in `TENANT_BILLER_OWNERSHIP_BOUNDARIES.md`. No fix
  is authorized.**
- **Broader multi-writer sweep (performed for this review):** a
  repository-wide search for model-instantiation call sites
  (`Claim(`, `Payment(`, `Denial(`, `Appeal(`, `CreditBalanceCase(`,
  `HospiceCapRecord(`, `NoeEdiSubmission(`, `RemittanceAdvice(`) found
  exactly one writer file per model (`billing_engine.py`,
  `payment_service.py`, `credit_balance_case_service.py`,
  `hospice_cap.py`, `noe.py`, respectively) — no additional dual-writer
  structure was found beyond `BillingProviderAgencyAssignment`. This
  sweep used call-site pattern matching, not a full data-flow trace, so
  it is reported as the result of a targeted search, not an exhaustive
  guarantee.

---

## Section 6 — Entity Review (TENTATIVE CREATE Items)

No TENTATIVE CREATE entity is recommended for approval in this
document. The only candidate flagged anywhere in Section 1 is a
possible future "Export Event" audit record for claim exports, and it
is explicitly **not** advanced to a TENTATIVE CREATE recommendation
here because no business-purpose/data-owned/relationship analysis has
been performed for it — it is recorded only as an open question for a
future, separately reviewed pass. Per Section 24's already-approved
Administrative Hierarchy Relationship Table design (Option B, separate
relationship table), any future physical hierarchy model would also
require this section's full treatment in a dedicated future review;
it is not re-litigated here since it was already approved separately.

**No entity in this document currently carries an active TENTATIVE
CREATE recommendation requiring Section 6 treatment.**

---

## Section 7 — Anti-Duplication Review

- [x] No duplicate payer authority — `Payer`/`payers` is singular;
  `PatientPayer` is a distinct patient-level concept, not a competing
  payer master.
- [x] No duplicate plan authority — no separate "Plan" model was found
  competing with payer/coverage-type fields on `PatientInsurance`/
  `PatientPayer`/`PatientFaceSheet`.
- [ ] No duplicate coverage authority — **NOT CLEAR.** Three structures
  (`PatientInsurance`, `PatientPayer`, `PatientFaceSheet`) each store
  payer/subscriber identity data with no verified reconciliation rule.
  This is the central open item of Section 2 and is not resolved here.
- [x] No duplicate claim authority — `claims`/`claim_edi_batches` is
  singular; `app/billing/store.py` is a superseded, non-persisted,
  already-gated legacy artifact, not a live competing authority.
- [x] No duplicate payment authority — `payments` is singular.
- [x] No duplicate ERA authority — `remittance_advices` is singular.
- [x] No duplicate denial authority — `denials`/`appeals` are singular
  and co-created.
- [x] No duplicate Room & Board authority —
  `facility_payment_expectations`/`allocations`/`collection_alerts`/
  `facility_payment_audit_log` form one cohesive, singularly-owned
  domain.
- [x] No duplicate permissions authority —
  `BillingProviderAgencyServiceScope.permission_level` is the only
  permission-granularity model found at the BillingProvider layer;
  role-based permissions (`roles.py`) are a separate, already-documented
  layer, not a duplicate of this one.
- [ ] No duplicate settings authority — **NOT INDEPENDENTLY VERIFIED IN
  THIS PASS.** No dedicated billing-settings search was performed in
  this review; flagged as an open item rather than assumed clear.
- [x] No duplicate audit authority — the generic/domain-specific audit
  log split is a deliberate, documented exception, not a duplicate.
- [ ] No duplicate export authority — **NOT FULLY VERIFIED.** No
  dedicated "Export Event" model exists; whether export activity is
  otherwise safely captured (e.g., solely through `AuditLog`) was
  flagged, not confirmed, in the Legacy Inventory and is carried
  forward unresolved here.

---

## Section 8 — Migration Impact Review

No future schema candidate is authorized in this document. For the two
items carried forward as unresolved (Patient Coverage Authority,
Eligibility Authority) and the one proven conflict
(`BillingProviderAgencyAssignment` dual-write), the following exposure
is documented in advance, without authorizing any migration:

### Patient Coverage (if a future LINK or CONSOLIDATE decision is made)

- Migration Exposure: Any FK addition between `PatientInsurance`,
  `PatientPayer`, and `PatientFaceSheet` would touch three actively
  written tables with a combined 10 verified rows today (0 + 5 + 5),
  which is low in this environment but not necessarily representative
  of production volume.
- Backfill Exposure: A LINK approach would require backfilling FK
  values from existing rows using a payer-identity matching heuristic
  that has not been designed or approved.
- Data Preservation Risk: Moderate — a CONSOLIDATE approach risks field
  loss if the three models' field sets are not fully reconciled first
  (this document does not perform that full reconciliation).
- Historical Record Risk: Low for LINK (additive only); high for
  CONSOLIDATE if performed without a verified no-data-loss migration
  plan.
- Foreign-Key Risk: `PatientInsurance` is already FK'd by two
  eligibility models; any restructuring must preserve those
  relationships.
- Consumer Impact: Eligibility workflow, claim export, and
  admission/authorization workflow all consume at least one of the
  three structures today — all three consumer domains would need
  verification against any change.
- Operational Impact: A LINK migration is additive (new nullable FK
  columns) and would not require downtime; a CONSOLIDATE migration
  would require a maintenance window and a verified rollback plan
  before any production run, given the three domains' concurrent
  consumers. Neither is scheduled or authorized here.
- Verification Approach (if pursued in a future phase): read-only
  record-count and FK-integrity checks (of the kind already performed
  in `LEGACY_BILLING_SCHEMA_INVENTORY.md` Section C) before and after
  any migration, plus targeted test runs of the confirmed consumer
  test files listed in Section 1, before any such migration is
  proposed for approval.

### Eligibility Authority (if a future consolidation is made)

- Migration Exposure: Would touch `payer_eligibility_checks` (0 rows)
  and `eligibility_verifications` (8 rows) plus their FK relationships
  to `patient_insurances`.
- Backfill Exposure: Would require reconciling two different status
  domains — not designed here.
- Data Preservation Risk: Moderate, given `EligibilityVerification`'s
  richer JSONB structured findings.
- Historical Record Risk: `EligibilityVerification` is explicitly
  append-only (`superseded_at`) — any consolidation must preserve this.
- Foreign-Key Risk: Both models' FKs to `patient_insurances`/
  `eligibility_source_documents` would need to be preserved or
  re-pointed.
- Consumer Impact: `eligibility_check_router.py`,
  `eligibility_workflow_service.py`, and confirmed test suites.
- Operational Impact: Would require a maintenance window sized to the
  8 existing `eligibility_verifications` rows plus any production
  volume; append-only history (`superseded_at`) must remain queryable
  throughout, so any consolidation would need to preserve rather than
  collapse historical rows.
- Verification Approach (if pursued in a future phase): re-run
  `test_eligibility_workflow_service.py` and
  `test_eligibility_roster_endpoint.py` against the migrated schema,
  plus a read-only row-count comparison before/after.

### `BillingProviderAgencyAssignment` Dual-Write Resolution (if a future single-writer decision is made)

- Migration Exposure: No schema change is inherently required to
  resolve this (it is a write-authority/code-path issue, not a
  structural one) — flagged so it is not mistaken for a schema
  problem.
- Backfill Exposure: None anticipated, since no field would change.
- Data Preservation Risk: Low.
- Historical Record Risk: Low.
- Foreign-Key Risk: None.
- Consumer Impact: Both `owner_admin.py` and `billing_provider_router.py`
  call sites would need updating if a single-writer delegation model
  (Option A/B in `TENANT_BILLER_OWNERSHIP_BOUNDARIES.md` Section 4) is
  chosen.
- Operational Impact: Code-path change only (see Section 4 of
  `TENANT_BILLER_OWNERSHIP_BOUNDARIES.md`); no downtime or maintenance
  window anticipated since no column changes are required.
- Verification Approach (if pursued in a future phase): confirm the
  Section 2.3 service-scope-creation asymmetry is also closed, and
  re-run any existing tests touching `set_tenant_financials` and the
  Biller Platform assignment endpoints.

---

## Section 9 — Final Decision Matrix

| Entity | Decision | Repository Evidence |
|---|---|---|
| Payer | REUSE | `payer.py`, baseline migration |
| PatientInsurance | REUSE (ownership deferred) | `patient_insurance.py` |
| PatientPayer | REUSE (ownership deferred) | `patient_payer.py`, `claim_export_service.py` |
| PatientFaceSheet | REUSE (ownership deferred) | `patient_facesheet.py`, SourceOfTruthMatrix.md |
| PayerEligibilityCheck | REUSE | migration `a2d6f8b1c4e9` |
| EligibilityVerification | REUSE | migration `x3y4z5a6b7c8` |
| Claim / claim_edi_batches | REUSE | migration `d8a1f3c6e2b4` |
| Payment / payment_adjustments | REUSE | migration `e1b7c9d4f8a2` |
| ERA / remittance_advices | REUSE | migration `e1b7c9d4f8a2` |
| Denial | REUSE | migration `f3a9c1e7b5d0` |
| Appeal | REUSE | migration `f3a9c1e7b5d0` |
| Credit Balance | REUSE | migration `f5a6b7c8d9e0` |
| NOE | REUSE | migration `9a8c04c006b3` |
| CAP | REUSE | migration `fe9eb2571468` |
| Room & Board (Facility Payment domain) | REUSE | migration `g1h2i3j4k5l6` |
| BillingProviderOrganization | REUSE / EXTEND | migration `h1i2j3k4l5m6` |
| BillingProviderAgencyAssignment | REUSE (write-authority conflict unresolved) | `billing_provider_router.py`, `owner_admin.py` |
| BillingProviderAgencyServiceScope | REUSE / EXTEND | migration `h1i2j3k4l5m6` |
| Audit | REUSE | `audit_log.py`, `facility_payment_audit_log.py` |
| Export | REUSE (claim export); no CREATE recommendation for a dedicated Export Event model | `claim_export_service.py` |
| PatientCoverage (third model) | **DO NOT CREATE** | Sections 2, 6, 7 |

---

## Section 10 — Database Safety Review

- No alembic stamp is proposed anywhere in this document.
- No historical migration rewrite is proposed anywhere in this
  document. All 116 existing migration files, including the squashed
  `521d501c6eea_consolidated_baseline`, are treated as immutable
  history; none is proposed for editing, re-ordering, or replacement.
- **Forward-only migration approach maintained**: every future
  schema candidate discussed in Section 8 (Patient Coverage LINK/
  CONSOLIDATE, Eligibility consolidation, dual-write resolution) is
  described only as a possible future forward-only migration; none is
  designed, scheduled, or authorized here.
- **Forward-only repair approach maintained**: consistent with the
  prior discovery finding that at least one historical migration in
  this codebase was itself a repair migration
  (`4f7d7c237580_repair_billing_tables_if_missing.py`,
  `0b88fddadbe5_repair_schema_drift_tenants_payers_idg_.py`, both later
  removed during the baseline squash), any future repair need would
  follow the same forward-only repair pattern already established in
  this repository's own history, not a rewrite of past migrations.
- **Schema drift risk**: not independently re-assessed against the
  live database in this document beyond the read-only record-count
  verification already performed in `LEGACY_BILLING_SCHEMA_INVENTORY.md`
  (Section C), which confirmed all expected tables exist with the
  expected names (after two self-corrected naming errors). No
  model-vs-database column-level drift check was performed in this
  pass; this is recorded as an open item, not asserted as clear.
- **Historical records protected**: no data modification, backfill, or
  deletion is proposed or performed by this document. The verified
  record counts in Section 1 are read-only observations.
- **Active production structures protected**: every REUSE/EXTEND
  decision in Section 9 explicitly preserves the existing structure
  as-is; no structure is marked for replacement or retirement in this
  document.

---

## Schema Design Approval Criteria — Self-Check

- [x] One authoritative payer strategy exists (`Payer`/`payers`,
  REUSE).
- [x] One authoritative plan strategy exists (no competing Plan model
  found).
- [ ] One authoritative coverage strategy exists — **remains
  intentionally unresolved with documented blockers** (Section 2):
  three overlapping structures, no reconciliation rule, LINK vs.
  CONSOLIDATE undecided.
- [x] Eligibility authority documented (Section 3) — remains
  unresolved between the two models, documented as such.
- [x] Dual-write conflicts documented (Section 5).
- [x] BillingProvider strategy documented (Section 4) — EXTEND is
  sufficient; no new structure recommended.
- [x] No duplicate writable systems remain unreviewed — two items
  (settings authority, export authority) are flagged as **not fully
  verified** in Section 7 rather than falsely marked clear.
- [x] Migration exposure documented for all three unresolved/contested
  items (Section 8).
- [x] Historical preservation documented (Sections 2, 3, 8).
- [x] Anti-duplication review completed (Section 7), with two items
  honestly left open rather than checked off without evidence.
- [x] Every CREATE recommendation justified with evidence — **there are
  no active CREATE recommendations in this document** to justify; the
  one candidate (Export Event) is explicitly not advanced.

## Fail Conditions — Self-Check

- No third `PatientCoverage` model is proposed. ✅ Passes.
- No duplicate payer/plan/claim/payment/eligibility authority is
  created. ✅ Passes (none created; all REUSE).
- No existing active billing structure is ignored. ✅ Passes — all 20
  required concepts addressed in Section 1.
- No legacy structure is buried. ✅ Passes — `app/billing/store.py`
  remains documented and gated per the Legacy Inventory.
- No ownership assumption replaces repository evidence. ✅ Passes —
  Patient Coverage and Eligibility Authority remain explicitly
  UNRESOLVED rather than assigned by default.
- No CREATE recommendation lacks justification. ✅ Passes — there are no
  active CREATE recommendations.

## Final Status

**APPROVED WITH CORRECTIONS is not self-declared here** — this
document is submitted for your review, not self-approved. Based on the
approval criteria and fail-condition self-checks above, this reviewer's
assessment is that the document satisfies the stated criteria with two
explicitly-flagged open items (settings authority, export authority not
fully verified) and one intentionally-unresolved item (Patient Coverage
Authority, with documented blockers, as the approval criteria
explicitly permit).

Recommended status for your determination: **APPROVED FOR SCHEMA
DESIGN, WITH PATIENT COVERAGE AND ELIGIBILITY AUTHORITY REMAINING
INTENTIONALLY UNRESOLVED.**

This document does not authorize schema changes, migrations, APIs, UI
implementation, backfills, data movement, deletions, or retirements. A
separate Migration Review and Implementation Authorization phase is
required afterward.

**CURRENT STATUS**

Schema Design Review: **SUBMITTED FOR REVIEW.**
Implementation: **BLOCKED.**
