# Billing Migration Design Review

## Status

**DOCUMENTATION ONLY.** This document defines future migration
*strategy* for three carried-forward unresolved authorities. It does
not create, generate, preview, or schedule any migration. No schema is
modified. No alembic revision is authored. No API, UI, backfill, data
movement, deletion, retirement, alembic stamp, or historical migration
rewrite is authorized by this document.

## Scope

Per instruction, this review is scoped to exactly three carried-forward
items and does not re-open any other part of
`BILLING_SCHEMA_DESIGN_REVIEW.md`:

1. Patient Coverage Authority — `PatientInsurance` vs. `PatientPayer`
   vs. `PatientFaceSheet`.
2. Eligibility Authority — `PayerEligibilityCheck` vs.
   `EligibilityVerification`.
3. `BillingProviderAgencyAssignment` dual-write authority.

## Locked Findings Carried Into This Review

- Patient Coverage Authority: **UNRESOLVED.** Current structures:
  `PatientInsurance`, `PatientPayer`, `PatientFaceSheet`. **Do not
  create `PatientCoverage` as a third physical model.**
- Eligibility Authority: **UNRESOLVED.** Current structures:
  `PayerEligibilityCheck`, `EligibilityVerification`. **No
  consolidation authorized.**
- `BillingProviderAgencyAssignment`: **VERIFIED DUAL-WRITE STRUCTURE.**
  Current writers: `owner_admin.py`, `billing_provider_router.py`.
  Future authority not yet approved. Document only. No implementation
  authorized.

---

## 1. Patient Coverage Authority — Future Migration Strategy

### 1.1 Why no migration is proposed yet

A migration cannot be responsibly designed until an ownership decision
(LINK vs. CONSOLIDATE vs. remain-separate-by-design) is made, and that
decision is explicitly not authorized in this phase. This section
documents the migration *shape* each option would take, so that once an
ownership decision is eventually made, the migration-design work is
already scoped — it does not pre-select or recommend an option.

### 1.2 Option A — LINK (additive, lowest risk)

- **Migration shape:** Add nullable FK columns only — e.g.,
  `patient_facesheet.patient_insurance_id` and/or
  `patient_facesheet.patient_payer_id` (exact target(s) to be decided
  with the ownership decision, not here); no column is dropped, no
  table is dropped, no existing data is rewritten.
- **Sequencing:** Single forward-only migration; no dependent
  migrations required beyond it.
- **Backfill:** Would populate the new FK column(s) for existing rows
  using a payer-identity matching heuristic. Verified existing volumes
  are small in this environment (`patient_insurances`: 0,
  `patient_payers`: 5, `patient_facesheet`: 5), so backfill volume risk
  is low here, but this is a dev-environment observation, not a
  production guarantee.
- **Rollback:** Trivial — drop the added nullable column(s); no data
  loss, since nothing else changes.
- **Consumer impact:** None of the three models' existing consumers
  (`eligibility_check_router.py`/`eligibility_workflow_service.py` for
  `PatientInsurance`; `app/api/patients.py`/`claim_financials.py`/
  `msp_validation_service.py`/`claim_export_service.py` for
  `PatientPayer`; `admission_readiness_gate.py`/
  `eligibility_check_router.py`/`app/api/patients.py`/
  `app/api/referrals.py` for `PatientFaceSheet`) would need to change
  behavior on migration day, since the new columns are additive and
  unused until application code is later updated to read/write them —
  that application-code change is implementation work, not authorized
  here.
- **Historical preservation:** Full — no existing row, column, or
  table is altered or removed.

### 1.3 Option B — CONSOLIDATE (higher risk, not designed here beyond shape)

- **Migration shape:** Would require, at minimum: (a) a target schema
  decision (which of the three structures survives, or whether a new
  structure is warranted — the latter is prohibited for
  `PatientCoverage` specifically, per the locked finding above, and no
  other new consolidated structure is proposed here either); (b) a
  field-reconciliation migration; (c) a data-migration/backfill step;
  (d) a consumer cut-over step across all three domains
  (eligibility, claim export/financial sequencing,
  admission/authorization); (e) a deprecation step for the
  superseded structure(s).
- **Sequencing:** Multi-migration, multi-phase; cannot be a single
  forward-only step without unacceptable consumer-impact risk.
- **Backfill:** Would need to reconcile disagreements between the
  three structures' payer/subscriber-identity fields for the same
  patient — no reconciliation rule exists today (see
  `PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`), so this cannot be
  designed further without that rule being defined first, which is
  explicitly out of scope for this review.
- **Rollback:** Non-trivial — once consumers are cut over, rollback
  requires either a compensating migration or a maintenance window;
  this is a real risk factor against choosing this option lightly.
- **Consumer impact:** High — touches eligibility, claim-export/MSP
  sequencing, and admission/authorization workflows simultaneously.
- **Historical preservation:** At risk unless a verified
  no-data-loss migration plan is produced in a future, dedicated
  review — not produced here.

### 1.4 Option C — Remain Separate By Design (no migration)

- **Migration shape:** None. This option formalizes the current state
  (three structures, each authoritative for its own workflow) as an
  intentional architecture rather than an unresolved gap, if that is
  the eventual decision.
- **Consideration:** This does not resolve the verified SSOT-claim
  conflict already documented (`docs/workflows/SourceOfTruthMatrix.md`
  claims `PatientFaceSheet` is sole SSOT for insurance identifiers,
  while `claim_export_service.py` verifiably sources the claim's
  payer/subscriber block from `PatientPayer`) — that conflict would
  need to be resolved by correcting the documentation, not the schema,
  under this option. This is noted as a real, low-risk, non-schema
  remediation path that has not been decided here.

### 1.5 Recommended Next Step (not a decision)

Before any of the above can be selected, a **field-reconciliation
pass** (a full field-by-field mapping across all three structures,
extending `PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md` to include
`PatientFaceSheet`) is the logical prerequisite. This is a
documentation task, not a migration, and is not performed in this
review — it is named here as the next input Migration Design would
need before Option A or B could be scoped further.

---

## 2. Eligibility Authority — Future Migration Strategy

### 2.1 Why no migration is proposed yet

As with Patient Coverage, no consolidation is authorized, and the two
models already have distinct, non-competing primary purposes
(lightweight per-attempt check log vs. richer document-sourced
structured findings). The only verified risk is status-field
disagreement for the same coverage, not structural duplication.

### 2.2 Option A — LINK / Cross-Reference (additive)

- **Migration shape:** Add a nullable FK from `PayerEligibilityCheck`
  to `EligibilityVerification` (or vice versa) so a given check attempt
  can be associated with the richer verification record it relates to,
  without merging either model.
- **Backfill:** Would need a heuristic (e.g., matching on
  `patient_insurance_id`/`payer_coverage_id` and nearest-in-time
  `created_at`) — not designed here.
- **Rollback:** Trivial (drop the nullable FK).
- **Consumer impact:** Low — existing consumers
  (`eligibility_check_router.py`, `eligibility_workflow_service.py`)
  would not need to change until application code is updated to use
  the new link, which is implementation work not authorized here.
- **Historical preservation:** Full — `EligibilityVerification`'s
  append-only (`superseded_at`) behavior is unaffected.

### 2.3 Option B — Status Reconciliation Constraint (no schema change, or minimal)

- **Migration shape:** Either a database-level trigger/check (schema
  change) or an application-level reconciliation rule (no schema
  change) ensuring `PayerEligibilityCheck.result_status` and
  `EligibilityVerification`'s status domain cannot silently disagree
  for the same coverage. Which of the two (schema vs. application-level)
  is appropriate is not decided here.
- **Consumer impact:** Would need both models' write paths updated —
  implementation work, not authorized here.

### 2.4 Option C — Remain Separate By Design (no migration)

- Formalizes the current state as intentional: `PayerEligibilityCheck`
  = attempt log, `EligibilityVerification` = authoritative structured
  finding. This is consistent with the field-level analysis already on
  record and requires no schema change, only an explicit written
  decision (not made here) that this is the permanent architecture
  rather than a still-open question.

### 2.5 Recommended Next Step (not a decision)

A decision between Option B/C (whether a reconciliation guarantee is
needed at all) should precede any Option A link design, since Option A
without B/C would still allow the same disagreement risk it is meant to
surface. This sequencing note is informational only.

---

## 3. `BillingProviderAgencyAssignment` Dual-Write Authority — Future Migration Strategy

### 3.1 Why no migration is proposed yet

This is fundamentally a **write-authority/code-path problem, not a
schema problem** — no column, table, or constraint change is required
to resolve it under any of the three previously-analyzed options
(Section 4, `TENANT_BILLER_OWNERSHIP_BOUNDARIES.md`). This section adds
migration-specific detail only.

### 3.2 If Option A is chosen (single writer: Biller Platform; Owner Platform delegates)

- **Migration shape:** None required for the table itself.
  `owner_admin.py::set_tenant_financials` would call into Biller
  Platform's existing assignment-creation logic instead of constructing
  `BillingProviderAgencyAssignment` rows directly — a code change, not
  a schema change.
- **Data impact:** None — no existing row needs alteration.
- **Rollback:** Code-level revert only.
- **Side effect resolved:** Closes the verified service-scope-creation
  asymmetry (Section 2.3 of `TENANT_BILLER_OWNERSHIP_BOUNDARIES.md`),
  since assignments would always be created through the path that also
  creates scopes.

### 3.3 If Option C is chosen (field-level split ownership)

- **Migration shape:** Would likely require a schema addition — e.g.,
  a `last_written_by_platform` or similar provenance column — to
  enforce which platform may write which fields, since no such column
  exists today. This is the only one of the three dual-write options
  that would require an actual schema migration; it is not designed
  further here.
- **Data impact:** Would require a default/backfill value for existing
  rows (verified count: 1 row) — low volume in this environment.

### 3.4 Recommended Next Step (not a decision)

Per `TENANT_BILLER_OWNERSHIP_BOUNDARIES.md` Section 4, Option A is
already noted as most consistent with the locked
Administrative-Authority-vs-Operational-Authority architecture and
would require no schema migration at all — only a code-path change.
This is repeated here because it directly affects whether Migration
Design ever needs to touch this table's schema. No decision is made in
this document.

---

## Migration Design Approval Criteria — Self-Check

- [x] All three carried-forward items addressed with candidate
  migration shapes, not implementations.
- [x] No migration authored, previewed, or scheduled.
- [x] No schema, API, UI, or backfill work performed.
- [x] No `PatientCoverage` model proposed under any option.
- [x] No consolidation of `PayerEligibilityCheck`/
  `EligibilityVerification` authorized under any option.
- [x] Dual-write resolution options include the schema-free option
  (Option A) and the one schema-impacting option (Option C), both
  documented without selection.
- [x] Rollback and historical-preservation considerations documented
  for every option presented.

## Final Status

Migration Design Review: **DOCUMENTED — future migration strategy
recorded for all three carried-forward items, no option selected, no
migration authored.**

Patient Coverage Authority: **UNRESOLVED** (carried forward unchanged).
Eligibility Authority: **UNRESOLVED** (carried forward unchanged).
`BillingProviderAgencyAssignment` Authority: **UNRESOLVED** (carried
forward unchanged).

**IMPLEMENTATION REMAINS BLOCKED.** No schema creation, migration
creation, API implementation, UI implementation, backfill execution,
data movement, data deletion, retirement activity, alembic stamp, or
historical migration rewrite has been performed or is authorized by
this document.
