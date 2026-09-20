# PatientInsurance vs. PatientPayer — Repository-Grounded Duplication Analysis

## Status

DISCOVERY ONLY. IMPLEMENTATION BLOCKED.

This document is the dedicated, standalone deliverable required in
addition to (not instead of) the shorter comparison embedded in
`TENANT_BILLER_SYSTEM_OF_RECORD_MATRIX.md` and
`LEGACY_BILLING_SCHEMA_INVENTORY.md`. All three documents must remain
consistent; this document is the authoritative field-by-field source
for the comparison.

Patient Coverage is a logical concept. **No third `PatientCoverage`
model is created or recommended anywhere in this document.**

This document does not proceed to Prompt 2 automatically and does not
authorize schema, migration, API, or UI work. It returns the analysis
for review.

---

## 1. Verified Starting Evidence

Re-verified directly against source in this pass:

**PatientInsurance** (`backend/app/models/patient_insurance.py`):
- Participates in eligibility workflows — confirmed: `eligibility_checks`
  relationship to `PayerEligibilityCheck`, `eligibility_status` field
  documented as "set from the most recent `PayerEligibilityCheck`."
- Referenced by both discovered eligibility-check structures — **partially
  confirmed**: `PayerEligibilityCheck.patient_insurance_id` is a mandatory
  FK to `patient_insurances`. `EligibilityVerification.payer_coverage_id`
  is an **optional** (`nullable=True`) FK to `patient_insurances` — so
  `EligibilityVerification` references it when present, but is not
  required to.
- No verified direct CRUD API — confirmed: no route in `app/api/` or
  `app/billing/api/` was found that performs create/update/delete
  directly on `PatientInsurance`; only eligibility-check endpoints
  reference it.
- No verified foreign-key relationship to `PatientPayer` — confirmed:
  neither model's `__table_args__`/columns reference the other.

**PatientPayer** (`backend/app/models/patient_payer.py`):
- Participates in billing and financial workflows — confirmed: consumed
  by `claim_financials.py`, `credit_balance_service.py`,
  `facility_payment_service.py`, `msp_validation_service.py`.
- CRUD behavior identified through the existing patient API — confirmed:
  `app/api/patients.py` (approx. lines 3244-3389) exposes create/update
  behavior for `PatientPayer` rows.
- Consumed by claim financials, credit balance, facility payment, and
  MSP-related validation — confirmed by import/usage in each of those
  four service files.
- No verified foreign-key relationship to `PatientInsurance` — confirmed
  (see above).

These are starting findings, carried forward from the prior pass and
re-verified here; they are not final ownership decisions.

---

## 2. Structure Comparison (field-by-field, from source)

| Attribute | `PatientInsurance` (`patient_insurances`) | `PatientPayer` (`patient_payers`) |
|---|---|---|
| Repository path | `backend/app/models/patient_insurance.py` | `backend/app/models/patient_payer.py` |
| Base class | `TenantScopedMixin`, `BaseModel` | `Base` (plain — **not** `BaseModel`, **not** `TenantScopedMixin`) |
| Creation migration | `521d501c6eea_consolidated_baseline` (squashed baseline — both tables appear in the same baseline migration; true creation order is **NOT VERIFIED**, see §6) | `521d501c6eea_consolidated_baseline` (same baseline); later extended by `c2e8a5d1f4b6_add_msp_fields_to_patient_payers` |
| Primary key | inherited from `BaseModel` (UUID, standard) | `id` = `UUID`, explicit `default=uuid.uuid4` |
| `tenant_id` | Yes — `ForeignKey("tenants.id", ondelete="CASCADE")`, `nullable=False`, indexed | **No column at all.** Tenant scope is only implied indirectly via `patient_id → patients.tenant_id`. This is a materially different scoping mechanism, not verified safe or unsafe — flagged as an open item. |
| `patient_id` | `ForeignKey("patients.id", ondelete="CASCADE")`, `nullable=False`, indexed | `ForeignKey("patients.id")` (no explicit `ondelete`), `nullable=False`, indexed |
| Payer name/type | `payer_type` (`String(32)`, e.g. MEDICARE/MEDICAID/HMO/PPO/VA/DENTAL/VISION/PHARMACY/OTHER), `payer_name` (`String(255)`) | `payer_type` (`String`, unconstrained length/enum), `payer_name` (`String`) |
| Member identifier | `subscriber_id` (`String(128)`, `nullable=False`, indexed) | `subscriber_id` (`String`, `nullable=True`) |
| Member-ID type | `subscriber_id_type` (`String(32)`, nullable — examples: MBI, CIN, MEMBER_ID, VA_ID, RX_BINPCN, OTHER) | `subscriber_id_type` (`String`, nullable) |
| Group identifier | `group_number` (`String(128)`, nullable) | **No group-number field found.** |
| Coverage scope | `coverage_scope` (`String(32)`, default `MEDICAL_GENERAL`; recommended values HOSPICE/MEDICAL_GENERAL/PHARMACY/DENTAL/VISION/VA/OTHER) | **No coverage-scope field found.** |
| Subscriber relationship (self/spouse/child, etc.) | **Not found** — no `relationship_to_subscriber`-style column | **Not found** |
| Coverage priority | `priority_order` (`Integer`, `nullable=False`, `CheckConstraint >= 1`) | `priority_order` (`Integer`, `nullable=True`, no check constraint) and `is_primary` (`Boolean`, nullable, default `true`) — **two overlapping priority signals**, not present on `PatientInsurance` |
| Effective dates | `effective_date` (`Date`, nullable), `end_date` (`Date`, nullable) | `effective_start_date` (`Date`, nullable), `end_date` (`Date`, nullable) — different column-naming convention for the start date |
| Active flag | `is_active` (`Boolean`, `nullable=False`, default `true`, indexed) | **No `is_active`/status flag found.** How a `PatientPayer` row is deactivated is not established by the schema — open item. |
| Verification status | `verified_at` (`DateTime(timezone=True)`, nullable), `verified_by` (FK to `users.id`, nullable), `eligibility_status` (`String(32)`, default `UNKNOWN`, doc: "set from the most recent `PayerEligibilityCheck`"), `next_verification_due` (`Date`, nullable) | **No verification-status fields found at all.** `PatientPayer` carries no eligibility/verification concept. |
| Eligibility linkage | `eligibility_checks` relationship → `PayerEligibilityCheck` (cascade `all, delete-orphan`) | **None.** No relationship to any eligibility model. |
| Claim linkage | **No FK to `Claim` found.** | **No FK to `Claim` found.** Linkage to claims, where it exists, is indirect via `ServiceCoverageDecision.selected_payer_id → PatientPayer.id`. |
| Billing-responsibility linkage | Not applicable — model is eligibility-scoped | `msp_type_code` (`String(2)`, nullable — CMS MSP value code, e.g. "12" Working Aged/GHP, "15" Workers' Comp, "47" Liability) plus `priority_order`/`is_primary` directly encode COB/billing-responsibility sequencing, per the field's own comment referencing `msp_validation_service.py` |
| Facility linkage | Not found | `facility_name` (`String(255)`, nullable) — a free-text facility-name snapshot field with no FK, unique to `PatientPayer` |
| Audit columns | `verified_at`/`verified_by` only (no `created_at`/`updated_at`/`created_by` columns directly on this model — inherited, if any, from `BaseModel`; not independently verified in this pass) | `created_at`, `updated_at` (both `DateTime(timezone=True)`, server-default `now()`), `created_by` (`UUID`, nullable) — present directly on the model |
| Constraints | `CheckConstraint("priority_order >= 1")`; unique index on `(tenant_id, patient_id, coverage_scope, priority_order)` preventing duplicate priority within a coverage scope | **No unique constraint found** preventing two rows with the same `patient_id` + `is_primary=true`, or the same `priority_order`, from coexisting |
| Indexes | `tenant_id`, `patient_id`, `payer_type`, `subscriber_id`, `coverage_scope`, `is_active`, `eligibility_status`, `verified_by` (all indexed); unique composite index above | `ix_patient_payers_patient_id` (`patient_id`), `ix_patient_payers_subscriber_id` (`subscriber_id`) — no tenant-scoped index (consistent with the missing `tenant_id` column) |
| History / versioning / supersession | **Not found.** `is_active` is a single boolean flag, not a supersession chain; no `superseded_by`/`superseded_at`-style column. | **Not found.** No history, versioning, or supersession columns at all. |
| Deactivation behavior | Implied via `is_active = false`; end-dating via `end_date` | **Not established by schema.** No boolean/status field to deactivate a row; only `end_date` exists to imply expiry. |

---

## 3. Consumer Comparison

| Consumer type | `PatientInsurance` | `PatientPayer` |
|---|---|---|
| Services | `eligibility_workflow_service.py` (per prior-pass discovery; re-confirmed via `eligibility_checks` relationship and `eligibility_status` doc-comment) | `claim_financials.py`, `credit_balance_service.py`, `facility_payment_service.py`, `msp_validation_service.py` |
| APIs | Eligibility-check endpoints only (`eligibility_check_router.py`, per prior-pass discovery) — **no direct CRUD route found for `PatientInsurance` itself** | `app/api/patients.py` (~lines 3244-3389) — direct CRUD confirmed |
| Frontend pages | `EligibilityVerificationPage.tsx` (per prior-pass discovery) | Indirect — Claims/Credit-Balance/Facility-Payment pages, via the services above (page-level route not independently re-traced this pass) |
| Eligibility workflows | Direct — this is the model's primary purpose | None — no eligibility fields or relationships exist on `PatientPayer` |
| Claim workflows | Not found directly; only indirectly plausible via shared `patient_id` | Indirect, via `ServiceCoverageDecision.selected_payer_id → PatientPayer.id` |
| Claim financials | Not found | Confirmed consumer (`claim_financials.py`) |
| Credit balance | Not found | Confirmed consumer (`credit_balance_service.py`) |
| Facility payment | Not found | Confirmed consumer (`facility_payment_service.py`) |
| MSP validation | Not found | Confirmed consumer (`msp_validation_service.py`) — uses `msp_type_code`/`priority_order` directly |
| Imports | NOT VERIFIED this pass | NOT VERIFIED this pass |
| Exports | NOT VERIFIED this pass | NOT VERIFIED this pass |
| Reports | `readiness_dashboard_service.py` (per prior-pass discovery) | Credit Balance Report, Facility Collections Report (per prior-pass discovery) |
| Tests / fixtures | NOT VERIFIED this pass — not searched | NOT VERIFIED this pass — not searched |
| Background jobs | NOT VERIFIED this pass | NOT VERIFIED this pass |

Neither model is called unused in this document; every consumer claim
above is either confirmed by direct source inspection or explicitly
marked NOT VERIFIED where the underlying search was not performed in
this pass.

---

## 4. Data Overlap

No live database query was run against this repository/environment in
this pass. Per instruction, no data is estimated. All data-level items
below are recorded as:

- Record counts: **NOT VERIFIED**
- Patients appearing in both tables: **NOT VERIFIED**
- Agencies represented: **NOT VERIFIED**
- Payer-name overlap: **NOT VERIFIED**
- Member-identifier overlap: **NOT VERIFIED**
- Coverage-priority conflicts: **NOT VERIFIED**
- Effective-date conflicts: **NOT VERIFIED**
- Orphaned records: **NOT VERIFIED**
- Null exposure: **NOT VERIFIED**
- Earliest/latest record dates: **NOT VERIFIED**
- Active vs. historical data: **NOT VERIFIED**

No data was modified, queried, exported, or estimated to produce this
document.

---

## 5. Eligibility Duplication (PayerEligibilityCheck vs. EligibilityVerification)

**Why both exist (from source):**
- `PayerEligibilityCheck` (`backend/app/billing/models/payer_eligibility_check.py`)
  is a lightweight, per-attempt audit log — one row per eligibility
  check event, whether a 270/271-style automated check or a manually
  logged phone/portal check. Its own docstring states it "Extends
  `PatientInsurance` ... with an audit trail of every verification
  attempt and its result — replacing any in-memory/fabricated
  eligibility status."
- `EligibilityVerification` (`backend/app/billing/models/eligibility_verification.py`)
  is a structured, document-sourced record of ~25 distinct hospice-
  specific eligibility facts (Medicare Part A/B entitlement, Medicare
  Advantage enrollment, MSP applicability/payer information, crossover
  coverage, QMB status, prior hospice election history, benefit-period
  history, home-health overlap), each stored in a tri-state envelope
  (`RETURNED` / `NOT_RETURNED` / `DOES_NOT_APPLY` / `UNKNOWN`) across
  three JSONB columns, specifically to prevent an absent finding from
  silently becoming a false negative. Its module docstring cites
  "Directive item 4/5" as the origin of this design.

**Both active:** Yes — both are real, mapped SQLAlchemy models with
live tables (`payer_eligibility_checks`, `eligibility_verifications`),
not stubs or deprecated code.

**Inputs and outputs:**
- `PayerEligibilityCheck` input: a check event (`check_method`:
  `MANUAL` or `BATCH_270_271`). Output: `result_status` (`ACTIVE` /
  `INACTIVE` / `UNKNOWN` / `ERROR`), `payer_response_code`,
  `plan_begin_date`/`plan_end_date`.
- `EligibilityVerification` input: a source document
  (`source_document_id`, mandatory FK to `eligibility_source_documents`)
  read by a human or (future) parser. Output: `status` (`NOT_RUN` /
  `PENDING` / `VERIFIED_ACTIVE` / `VERIFIED_INACTIVE` /
  `COVERAGE_CONFLICT` / `REVIEW_REQUIRED` / `ERROR`), plus the three
  structured JSONB fact groups.

**PatientInsurance relationships:**
- `PayerEligibilityCheck.patient_insurance_id` → `patient_insurances.id`,
  `nullable=False` (mandatory).
- `EligibilityVerification.payer_coverage_id` → `patient_insurances.id`,
  `nullable=True` (optional) — an `EligibilityVerification` row can
  exist without being tied to any specific `PatientInsurance` row.

**Provenance:** `PayerEligibilityCheck.checked_by` is a free-text
string with no FK. `EligibilityVerification.verified_by_user_id` is a
mandatory FK to `users`, and `source_document_id` is a mandatory FK to
`eligibility_source_documents` — a stronger, document-anchored
evidentiary chain.

**Current consumers:** Both are referenced from eligibility-workflow
code (`eligibility_check_router.py`, `eligibility_workflow_service.py`);
the exact service-to-model mapping line-by-line was not independently
re-traced in this pass.

**Overlap:** The genuine overlap is narrow: both carry an eligibility
result/status concept for the same coverage, using **two different,
explicitly-declared-distinct status vocabularies**
(`EligibilityVerification`'s module docstring states its status domain
is "intentionally a *different* status domain" from other workflow
statuses and instructs "do not conflate them"). No schema-level
constraint was found preventing `PayerEligibilityCheck.result_status`
and `EligibilityVerification.status` from disagreeing for the same
patient/coverage at the same time.

**Differences:** `PayerEligibilityCheck` = simple, mandatory-linked,
per-attempt log. `EligibilityVerification` = richer, document-sourced,
hospice-specific structured findings record, optionally linked, with
built-in append-only supersession (`superseded_at`, set when a later
verification supersedes an earlier one for the same patient+coverage;
the docstring states this satisfies "Directive item 8" — never deleted
or overwritten).

**Which structure is authoritative, if proven:** Not proven either way
in this pass. `PayerEligibilityCheck` is authoritative for "was a check
performed and what was its simple result." `EligibilityVerification` is
authoritative for "what structured hospice-eligibility facts were
found," a broader and distinct concern. Treating either as authoritative
for the other's concern would be incorrect based on the evidence above.

**Linking or consolidation required:** Not decided in this pass, per
instruction ("Do not consolidate either structure during discovery").
Eligibility evidence is not automatically verified Patient Coverage, and
the eligibility-duplication question is tracked separately from the
PatientInsurance-vs-PatientPayer question below.

---

## 6. Semantic Decision

Selected conclusion: **E — Authority remains unresolved pending
additional evidence.**

Rationale for not selecting A, B, C, or D:

- **A** (`PatientInsurance` owns insurance/coverage; `PatientPayer`
  owns a distinct billing/financial concept) is the closest fit to the
  field evidence — `PatientInsurance` carries verification/eligibility
  fields `PatientPayer` entirely lacks, while `PatientPayer` carries
  MSP/COB fields `PatientInsurance` entirely lacks. However, this
  cannot be selected as final because both models independently store
  overlapping payer-identity and priority-sequencing data (payer
  name/type, subscriber ID, priority ordering, effective/end dates) for
  what may be the same real-world payer relationship, with **no FK
  connecting them** and **no verified data showing whether they are
  kept in sync in practice** (§4, all NOT VERIFIED). Concluding A
  outright would assume the overlapping fields never diverge — not
  established.
- **B** is not supported: `PatientPayer` has no eligibility/verification
  fields at all, so it structurally cannot own the "insurance and
  coverage" side of the split.
- **C** (both partially duplicate and require controlled consolidation)
  is not selected because consolidation would need to be justified by
  proof of actual data divergence or actual double-entry burden — not
  verified in this pass (§4).
- **D** (an explicit link is required) is a plausible near-term
  recommendation but is not selected as the final semantic decision
  here because it presumes the two models should remain permanently
  separate — a decision that itself depends on resolving whether the
  overlapping payer-identity fields (§2) represent an actual data-
  integrity risk, which is unverified.

Given the missing data-overlap evidence (§4) and the structural
asymmetries found in §2 (no `tenant_id` on `PatientPayer`, no
verification concept on `PatientPayer`, no deactivation mechanism on
`PatientPayer`, two overlapping priority signals on `PatientPayer`
itself), forcing a decision now would exceed the available evidence.

---

## 7. System-of-Record Recommendation

- **Authoritative business concept:** Patient Coverage (logical concept
  only — see §8; not a physical model).
- **Recommended authoritative model:** Not selected. Working hypothesis,
  not a decision: `PatientInsurance` as the eligibility/coverage-identity
  authority, `PatientPayer` as the billing/financial-responsibility-
  sequencing authority, connected by a future link — consistent with
  Semantic Decision E, not a substitute for it.
- **Recommended authoritative table:** Not selected, for the same reason.
- **Data owned (if the working hypothesis holds):** `PatientInsurance`
  would own coverage identity, verification status, and eligibility
  linkage. `PatientPayer` would own COB/MSP sequencing and financial-
  responsibility fields consumed by claim financials, credit balance,
  facility payment, and MSP validation.
- **Data not owned:** Neither model would own a stored "Patient
  Coverage" record — that remains logical/derived, per the hard rule
  against a third model.
- **Required extensions:** Not decided. If LINK is eventually chosen: an
  FK from `PatientPayer` to `PatientInsurance` (or vice versa) would be
  additive. If CONSOLIDATE: a data-migration/backfill plan would be
  required and is explicitly out of scope for this document.
- **Required links:** Not decided (see §6).
- **Historical preservation:** Whichever path is eventually authorized
  must preserve every existing row in both tables and their audit trail;
  no deletion, merge, or rewrite is authorized by this document.
- **Consumer impact:** A future LINK would be additive for all four
  confirmed `PatientPayer` consumers and the `PatientInsurance`
  eligibility consumers; a future CONSOLIDATE would require updating all
  of them and is a materially larger change — not scoped here.
- **Migration exposure:** High if consolidation is eventually chosen;
  low (additive FK) if LINK is chosen. Not decided here.
- **Backfill exposure:** High if consolidation; moderate if LINK
  (matching existing rows across the two models by patient+payer would
  require a reviewed backfill plan). Not decided here.
- **Open defects:**
  1. `PatientPayer` has no `tenant_id` column — tenant scope is only
     indirect via `patient_id`. Flagged, not assessed as safe or unsafe
     in this pass.
  2. `PatientPayer` has no `is_active`/status field and no supersession
     mechanism — deactivation behavior is not established by the schema.
  3. `PatientPayer` has two overlapping priority signals
     (`is_primary` and `priority_order`) with no constraint reconciling
     them, and no unique constraint preventing duplicate "primary"
     assignments for the same patient.
  4. No FK connects `PatientInsurance` and `PatientPayer`, and no
     verified data confirms whether their overlapping payer-identity
     fields diverge in practice.
  5. `PayerEligibilityCheck.result_status` and
     `EligibilityVerification.status` are two different, explicitly
     non-conflatable status domains referencing overlapping coverage
     with no constraint preventing disagreement (§5).
- **Confidence level:** Verified (as a field-level, structural, and
  consumer comparison); UNRESOLVED (as an ownership/consolidation
  decision) — consistent with the matrix and legacy inventory.

**Explicit confirmation:** No third `PatientCoverage` model is
recommended by this document, under any of the five semantic-decision
options.

---

## 8. Prohibited Actions — Compliance Statement

This document did not: add tables; add columns; create migrations;
create `PatientCoverage`; rename either model; delete either model;
merge records; run backfills; modify APIs; modify UI; rewrite historical
migrations; use `alembic stamp`; or declare either model obsolete. Both
models remain exactly as they exist in the repository today.

---

## Final Output Summary

- Field-by-field comparison: §2
- Consumer comparison: §3
- Data-overlap analysis: §4 (all items NOT VERIFIED; no estimation)
- Eligibility-model analysis: §5
- Semantic decision: §6 — **E, Authority remains unresolved**
- System-of-record recommendation: §7 — working hypothesis only, not a
  final decision
- Historical-preservation requirements: §7
- Schema implications: §7 (not decided)
- Migration implications: §7 (not decided)
- Open defects: §7 (five items)
- Repository evidence: cited inline throughout §1–§5

This analysis is returned for review. Prompt 2
(`LEGACY_BILLING_SCHEMA_INVENTORY.md`) is not re-triggered by this
document. Implementation remains blocked.
