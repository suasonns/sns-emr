# Implementation Stories

## Status

**PLANNING ONLY.** Story-level decomposition of the 17 epics in
`IMPLEMENTATION_EPICS.md`. **No schema. No migrations. No code. No
API. No UI.** Stories describe future implementation work; none is
authorized to begin by this document.

---

## Epic 1 — Billing Organization

- **Story 1.1:** Confirm `BillingProviderOrganization` CRUD paths meet
  current business rules with no schema change.
  - *Acceptance:* Existing organization records (1 verified)
    unaffected; no new column/table.
  - *Dependencies:* none.
  - *Blockers:* none identified.
  - *Testing:* regression test of existing organization CRUD.
  - *Validation:* confirm no duplicate organization-authority table
    introduced.
- **Story 1.2:** Document organization status-lifecycle states used
  by `set_tenant_financials` gating (`ein`+`ptan`+`ACTIVE`).
  - *Acceptance:* gating conditions documented and unchanged.
  - *Dependencies:* Story 1.1.
  - *Blockers:* none.
  - *Testing:* none (documentation story).
  - *Validation:* cross-checked against `owner_admin.py`.

## Epic 2 — Billing Teams

- **Story 2.1:** Confirm `BillingProviderOrganizationMembership`
  supports current membership needs without a new sub-team model.
  - *Acceptance:* 1 verified row unaffected; no new table.
  - *Dependencies:* Epic 1.
  - *Blockers:* none.
  - *Testing:* regression test of membership CRUD.
  - *Validation:* confirm Schema Design Review Section 4 finding
    ("no further team/sub-team structure was found") still holds.

## Epic 3 — Agency Assignment

- **Story 3.1:** Plan the future code-path change so
  `owner_admin.py::set_tenant_financials` delegates to Biller
  Platform's assignment-creation logic instead of writing
  `BillingProviderAgencyAssignment` directly (Option B).
  - *Acceptance:* delegation design documented; no code change
    performed in this phase.
  - *Dependencies:* Epic 1, Epic 2.
  - *Blockers:* requires Implementation Authorization Review before
    any code change.
  - *Testing:* future integration test verifying single write path.
  - *Validation:* confirm no duplicate assignment table; confirm
    `relationship_status`/`effective_start_at`/`effective_end_at`
    remain single-writer post-change.
- **Story 3.2:** Document the existing dual-write risk window (both
  paths remain active until Story 3.1 is implemented) so no
  assumption of single-writer behavior leaks into other epics
  prematurely.
  - *Acceptance:* risk documented; other epics' stories reference this
    explicitly where relevant (Epic 4).
  - *Dependencies:* Story 3.1.
  - *Blockers:* none.
  - *Testing:* none (documentation story).
  - *Validation:* consistent with `TENANT_BILLER_OWNERSHIP_
    BOUNDARIES.md` Section 4.

## Epic 4 — Agency Coverage

- **Story 4.1:** Plan closing the verified asymmetry where
  Owner-Platform-created assignments receive no
  `BillingProviderAgencyServiceScope` rows.
  - *Acceptance:* remediation depends on Epic 3 Story 3.1 completing
    first (single write path); documented as a dependency, not solved
    independently.
  - *Dependencies:* Epic 3.
  - *Blockers:* Epic 3 Story 3.1 must be implementation-authorized
    first.
  - *Testing:* future test asserting every assignment has at least one
    service-scope row.
  - *Validation:* confirm 15-value scope enum remains unchanged and
    sufficient (per Schema Design Review Section 4).

## Epic 5 — Payer Authority

- **Story 5.1:** Plan the future nullable-FK link between
  `PatientInsurance` and `PatientPayer` (Migration Design Review
  Section 1.2, Option A shape).
  - *Acceptance:* link design documented (which side holds FK — open
    per Final Schema Authorization Review §1.11); no migration
    authored in this phase.
  - *Dependencies:* Epic 6 (Eligibility Authority) for full context.
  - *Blockers:* requires the field-reconciliation pass recommended in
    Migration Design Review Section 1.5 before the link is finalized.
  - *Testing:* future backfill-heuristic test once link is
    implemented.
  - *Validation:* confirm no `PatientCoverage` model is introduced;
    confirm `PatientFaceSheet` remains excluded from this link per
    locked decision.
- **Story 5.2:** Perform the field-reconciliation pass extending
  `PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md` to include
  `PatientFaceSheet` (documentation task, not schema).
  - *Acceptance:* extended analysis document produced.
  - *Dependencies:* none.
  - *Blockers:* none — this is a documentation prerequisite, may
    proceed within Implementation Planning if separately requested.
  - *Testing:* none (documentation story).
  - *Validation:* must not propose consolidation or a new model.

## Epic 6 — Eligibility Authority

- **Story 6.1:** Document the cross-reference-only relationship
  between `PayerEligibilityCheck` and `EligibilityVerification`
  (Final Schema Authorization Review §2, Option C).
  - *Acceptance:* both remain separate; optional future nullable FK
    (Migration Design Review Section 2.2) documented as a next step,
    not implemented.
  - *Dependencies:* Epic 5.
  - *Blockers:* none.
  - *Testing:* regression test confirming both models' existing
    consumers (`eligibility_check_router.py`,
    `eligibility_workflow_service.py`) remain unaffected.
  - *Validation:* confirm no consolidation attempted.

## Epic 7 — Claims

- **Story 7.1:** Confirm claim export continues to source the
  payer/subscriber block from `PatientPayer` (verified runtime
  behavior) and does not silently switch to `PatientFaceSheet` as a
  side effect of Epic 5/6 work.
  - *Acceptance:* `claim_export_service.py::_build_payer_block`
    behavior unchanged.
  - *Dependencies:* Epic 5, Epic 6.
  - *Blockers:* none.
  - *Testing:* regression test of 837I payer/subscriber block
    generation.
  - *Validation:* cross-checked against Schema Design Review Section
    1 finding (lines 268–296).

## Epic 8 — Payment Posting

- **Story 8.1:** Confirm `Payment`/`payment_adjustments` remain
  unaffected by upstream Claims changes.
  - *Acceptance:* existing 4/8 verified rows unaffected.
  - *Dependencies:* Epic 7.
  - *Blockers:* none.
  - *Testing:* regression test of payment posting and adjustment
    creation.
  - *Validation:* single-writer (`payment_service.py`) confirmed
    unchanged.

## Epic 9 — ERA

- **Story 9.1:** Confirm ERA ingestion continues to write into the
  combined `RemittanceAdvice` entry (no separate ERA table introduced).
  - *Acceptance:* no new ERA-only table created.
  - *Dependencies:* Epic 8.
  - *Blockers:* none.
  - *Testing:* regression test of ERA ingestion → remittance record
    creation.
  - *Validation:* confirms Schema Design Review's ERA/Remittance
    combined-entry clarifying note remains accurate.

## Epic 10 — Remittance

- **Story 10.1:** Confirm remittance-to-payment reconciliation logic
  is unaffected by Epic 5/6/7/8 changes.
  - *Acceptance:* existing 4 verified rows unaffected.
  - *Dependencies:* Epic 9.
  - *Blockers:* none.
  - *Testing:* regression test of reconciliation.
  - *Validation:* no duplicate remittance authority introduced.

## Epic 11 — NOE

- **Story 11.1:** Confirm `NoeEdiSubmission` remains unaffected by
  Claims changes.
  - *Acceptance:* existing 0 verified rows (structure present, no
    data) unaffected.
  - *Dependencies:* Epic 7.
  - *Blockers:* none.
  - *Testing:* regression test of NOE submission creation path.
  - *Validation:* single writer (`noe.py`) confirmed unchanged.

## Epic 12 — CAP

- **Story 12.1:** Confirm `HospiceCapRecord` remains unaffected by
  Payment Posting changes.
  - *Acceptance:* existing 0 verified rows unaffected.
  - *Dependencies:* Epic 8.
  - *Blockers:* none.
  - *Testing:* regression test of CAP record creation.
  - *Validation:* single writer (`hospice_cap.py`) confirmed
    unchanged.

## Epic 13 — Room & Board

- **Story 13.1:** Confirm facility payment expectation/allocation/
  alert/audit-log chain remains intact end-to-end.
  - *Acceptance:* existing 6/0/4/18 verified rows unaffected.
  - *Dependencies:* Epic 8.
  - *Blockers:* none.
  - *Testing:* regression test across the full facility-payment
    chain.
  - *Validation:* confirmed cohesive, singularly-owned domain (Schema
    Design Review Section 7) remains true.

## Epic 14 — Audit

- **Story 14.1:** Confirm append-only behavior of domain-specific and
  generic audit logs is preserved across every other epic's changes.
  - *Acceptance:* no historical `AuditLog` row (1,106 verified) or
    `facility_payment_audit_log` row (18 verified) is ever mutated or
    deleted.
  - *Dependencies:* cross-cutting; validated alongside Epics 1–13.
  - *Blockers:* none.
  - *Testing:* regression test asserting append-only constraint (no
    UPDATE/DELETE path exists) for both audit structures.
  - *Validation:* generic/domain-specific split remains a deliberate
    exception, not a duplicate.

## Epic 15 — Reporting

- **Story 15.1:** Resolve the open "duplicate export authority — NOT
  FULLY VERIFIED" item from Schema Design Review Section 7 before
  finalizing reporting stories.
  - *Acceptance:* export-authority verification completed
    (documentation task) confirming whether `AuditLog` alone safely
    captures export activity.
  - *Dependencies:* Epic 14.
  - *Blockers:* this verification must complete before Epic 15's
    remaining stories are finalized.
  - *Testing:* none (documentation/verification story).
  - *Validation:* no new "Export Event" model introduced without a
    separate, dedicated future review (per Schema Design Review
    Section 6).
- **Story 15.2:** Define reporting surfaces consuming Claims/Payment/
  ERA/Remittance/Room & Board data, read-only.
  - *Acceptance:* no new authoritative reporting table.
  - *Dependencies:* Story 15.1, Epics 7–14.
  - *Blockers:* none beyond Story 15.1.
  - *Testing:* future report-output regression test.
  - *Validation:* read-only access confirmed, no write path added.

## Epic 16 — Settings Integration

- **Story 16.1:** Apply the locked "Medicare Part A Hospice"
  user-facing label (internal enum `MEDICARE_HOSPICE` unchanged) to
  payer/plan settings screens.
  - *Acceptance:* label matches the authoritative terminology decision
    record exactly; no schema/migration change.
  - *Dependencies:* Epic 5.
  - *Blockers:* none.
  - *Testing:* future UI regression test of label rendering (once
    implementation is authorized).
  - *Validation:* confirm no other approved payer label was altered
    (Medicaid, Medi-Cal, Medicare Advantage HMO/PPO, Commercial HMO/
    PPO/POS, TRICARE, Veterans Affairs (VA), Private Pay, Other).

## Epic 17 — Security / Permissions

- **Story 17.1:** Confirm `PLATFORM_BILLING` vs. `BILLING` role
  distinction and `BillingProviderAgencyServiceScope.permission_level`
  remain the sole permission-granularity layers (no duplicate
  permissions authority).
  - *Acceptance:* no new permissions table/model introduced.
  - *Dependencies:* none (foundation).
  - *Blockers:* none.
  - *Testing:* regression test of existing role/permission checks.
  - *Validation:* cross-checked against Schema Design Review Section
    7 anti-duplication finding.

---

## Status Summary

Story decomposition complete for all 17 epics. Every story is framed
as planning/verification/regression-test work; no story authorizes
schema, migration, code, API, or UI changes in this phase.

**IMPLEMENTATION REMAINS BLOCKED.**
