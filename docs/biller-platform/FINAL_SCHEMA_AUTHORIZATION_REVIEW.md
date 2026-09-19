# Final Schema Authorization Review

## Status

**APPROVED.** Discovery: COMPLETE. Schema Design Review: COMPLETE.
Migration Design Review: COMPLETE. Final Schema Authorization Review:
**APPROVED** — the three authority decisions below (Sections 1–3) are
now the approved, locked authority model. **IMPLEMENTATION REMAINS
BLOCKED.**

This document originally existed to select **recommended** authority
decisions for the three items carried forward, unresolved, from
`BILLING_SCHEMA_DESIGN_REVIEW.md` and
`BILLING_MIGRATION_DESIGN_REVIEW.md`. Those recommendations have now
been reviewed and approved (see Final Decision, below) as the final
authority model.

**NO SCHEMA CHANGES AUTHORIZED. NO MIGRATIONS AUTHORIZED. NO
IMPLEMENTATION AUTHORIZED BY THIS DOCUMENT.** Approval of the authority
*decisions* is not, by itself, approval of schema creation, migration
authoring, API changes, or UI changes. No schema is created or
modified. No migration is authored, generated, previewed, or
scheduled. No API, UI, backfill, data movement, deletion, retirement,
alembic stamp, or historical migration rewrite is performed or
authorized by this document.

## Previous Phases (all complete)

- ✅ Discovery
- ✅ Repository Grounding
- ✅ System-of-Record Review
- ✅ Legacy Billing Review
- ✅ Ownership Boundary Review
- ✅ Schema Design Review
- ✅ Migration Design Review

## Scope

Exactly three unresolved authority decisions, per instruction:

1. Patient Coverage Authority — `PatientInsurance` vs. `PatientPayer`
   vs. `PatientFaceSheet`.
2. Eligibility Authority — `PayerEligibilityCheck` vs.
   `EligibilityVerification`.
3. `BillingProviderAgencyAssignment` future write-authority model.

No other structure, model, or table is reopened in this document.

---

## 1. Patient Coverage Authority

### 1.1 Current Structures

- `PatientInsurance` (table `patient_insurances`, 0 rows verified).
- `PatientPayer` (table `patient_payers`, 5 rows verified).
- `PatientFaceSheet` (table `patient_facesheet`, 5 rows verified;
  `facesheet_field_suggestions`, 4 rows verified, ownerless OCR
  staging queue, never authoritative).

### 1.2 Repository Evidence

- `backend/app/models/patient_insurance.py` — tenant-scoped
  (`TenantScopedMixin`), unique on
  `(tenant_id, patient_id, coverage_scope, priority_order)`; FK target
  of `PayerEligibilityCheck` (mandatory) and `EligibilityVerification`
  (optional, via `payer_coverage_id`).
- `backend/app/models/patient_payer.py` — no direct `tenant_id`
  column; scoped indirectly via `patient_id → patients.tenant_id`; FK
  target of `ServiceCoverageDecision`.
- `backend/app/models/patient_facesheet.py` — explicit `tenant_id`
  column with FK+index; no confirmed FK relationship to either of the
  other two models.
- `backend/app/billing/claim_export_service.py` lines 268–296
  (`_build_payer_block`) — verified to build the actual 837I
  payer/subscriber block from `PatientPayer` via
  `msp_validation_service.py`, **not** from `PatientFaceSheet`.
- `docs/workflows/SourceOfTruthMatrix.md` — declares `PatientFaceSheet`
  the sole SSOT for insurance identifiers, a claim that conflicts with
  the verified runtime behavior above (documentation-vs-runtime
  conflict, previously recorded, not previously resolved).
- `docs/biller-platform/PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md` —
  field-by-field comparison of `PatientInsurance`/`PatientPayer`
  (does not yet include `PatientFaceSheet`).
- `docs/biller-platform/BILLING_SCHEMA_DESIGN_REVIEW.md` Section 2 —
  prior UNRESOLVED finding, carried forward.

### 1.3 Current Consumers

| Structure | Consumers |
|---|---|
| `PatientInsurance` | `eligibility_check_router.py`, `eligibility_workflow_service.py`, `readiness_dashboard_service.py`, `PayerEligibilityCheck`, `EligibilityVerification` |
| `PatientPayer` | `app/api/patients.py` (CRUD, lines 3244–3389), `claim_financials.py`, `credit_balance_service.py`, `facility_payment_service.py`, `msp_validation_service.py` → `claim_export_service.py` |
| `PatientFaceSheet` | `claim_export_service.py` (attending-physician block only), `admission_readiness_gate.py`, `eligibility_check_router.py`, `app/api/patients.py`, `app/api/referrals.py`, `seed_acceptance_patient.py` |

### 1.4 Current Write Paths

- `PatientInsurance`: eligibility-workflow services; no dedicated CRUD
  API confirmed in prior discovery passes.
- `PatientPayer`: `app/api/patients.py` CRUD endpoints.
- `PatientFaceSheet`: facesheet-domain services/APIs; OCR-suggestion
  intake pipeline (`facesheet_field_suggestions`) feeds it but is not
  itself authoritative.

### 1.5 Risks

- No verified reconciliation rule exists across the three structures'
  overlapping payer/subscriber-identity fields
  (`subscriber_id`/policy-number/payer-name equivalents appear on all
  three).
- The `SourceOfTruthMatrix.md` SSOT claim for `PatientFaceSheet` is
  contradicted by verified claim-export runtime behavior. Left
  unresolved, this remains a real risk that engineers or billing staff
  could rely on stale or incorrect documentation.
- `PatientFaceSheet` has no confirmed FK relationship to either
  `PatientInsurance` or `PatientPayer`, so any future consumer cannot
  safely assume any one of the three is derivable from another today.

### 1.6 Preservation Requirements

- All three structures, their current tables, and their current
  consumers must remain fully intact. No table may be dropped. No
  column may be removed. No existing row may be altered by this
  review.
- No fourth physical model may be created to "solve" this by adding
  another structure alongside the existing three.

### 1.7 Authority Options (as specified)

- **A. `PatientInsurance` authority.**
- **B. `PatientPayer` authority.**
- **C. `PatientInsurance` + `PatientPayer` linked.**
- **D. Authority intentionally unresolved.**

### 1.8 Recommended Decision

**Option C — `PatientInsurance` + `PatientPayer` linked**, with
`PatientFaceSheet` treated as a separate, presentation/snapshot-layer
concern whose SSOT documentation claim requires a **documentation
correction**, not a schema change, as a follow-on action (not
authorized here).

This recommendation does **not** create `PatientCoverage` or any other
third physical model, and does **not** consolidate any of the three
structures. It recommends only that a future, separately-authorized
migration add a link (e.g., a nullable FK) between `PatientInsurance`
and `PatientPayer`, consistent with Migration Design Review's
already-documented Option A (LINK) shape for this pair.

### 1.9 Alternative Decisions Considered

- **Option A alone** (`PatientInsurance` authority only): rejected as
  the sole authority because `PatientPayer` is the verified,
  production-proven source of the actual claim payer/subscriber block
  — treating `PatientInsurance` as sole authority would misrepresent
  which structure claim generation actually depends on today.
- **Option B alone** (`PatientPayer` authority only): rejected as the
  sole authority because `PatientInsurance` is the verified,
  mandatory FK anchor for both eligibility models
  (`PayerEligibilityCheck`, `EligibilityVerification`) — treating
  `PatientPayer` as sole authority would misrepresent the eligibility
  workflow's actual dependency.
- **Option D** (intentionally unresolved): rejected as the final
  recommendation because the two structures already have clean,
  non-overlapping primary purposes (eligibility evidence vs.
  claim/financial sequencing) that support a linked-authority model
  without requiring consolidation; leaving both authority questions
  open indefinitely was appropriate during Discovery/Design/Migration
  review, but a Final Authorization phase exists specifically to
  reach a recommendation.

### 1.10 Reasoning

- `PatientInsurance` and `PatientPayer` are each independently
  authoritative for a distinct, verified, currently-active workflow —
  neither can be safely demoted to "non-authoritative" for its own
  domain.
- No evidence supports collapsing either into the other, and no
  evidence supports promoting `PatientFaceSheet` to sit above both,
  given the verified claim-export behavior contradicts its documented
  SSOT status.
- A link (not a merge) preserves both structures' current behavior
  and consumers unchanged while creating the traceability path needed
  to eventually reconcile identity-field disagreements — this is
  exactly the LINK option already scoped, without selection, in
  `BILLING_MIGRATION_DESIGN_REVIEW.md` Section 1.2.
- `PatientFaceSheet` is excluded from the linked-authority pair
  because no FK relationship to either other structure was ever
  found, and its actual verified role (attending-physician block,
  admission/authorization, patient-snapshot display) is materially
  different from claim-payer-block generation or eligibility
  verification.

### 1.11 Open Concerns

- The recommended link's exact shape (which side holds the FK, whether
  it is one-directional or requires a join table) is **not decided
  here** and remains migration-design work for a future, separately
  authorized pass.
- The `PatientFaceSheet`/`SourceOfTruthMatrix.md` documentation
  conflict remains open and unresolved; correcting it is recommended
  as a near-term, low-risk, non-schema follow-on action, but is not
  performed by this document.
- The field-reconciliation pass recommended in
  `BILLING_MIGRATION_DESIGN_REVIEW.md` Section 1.5 (extending
  `PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md` to include
  `PatientFaceSheet`) has still not been performed and should precede
  any future migration authoring for this link.

---

## 2. Eligibility Authority

### 2.1 Current Structures

- `PayerEligibilityCheck` (table `payer_eligibility_checks`, 0 rows
  verified).
- `EligibilityVerification` (table `eligibility_verifications`, 8 rows
  verified) plus `eligibility_source_documents` (4 rows verified).

### 2.2 Repository Evidence

- `backend/app/models/payer_eligibility_check.py` — mandatory FK to
  `patient_insurance_id`; simple `result_status`
  (ACTIVE/INACTIVE/UNKNOWN/ERROR); creation migration `a2d6f8b1c4e9`.
- `backend/app/models/eligibility_verification.py` — mandatory FK to
  `source_document_id`; optional (`nullable=True`) FK to
  `patient_insurances` via `payer_coverage_id`; richer,
  document-sourced, hospice-specific structured tri-state findings
  (~25 facts across 3 JSONB columns); append-only via
  `superseded_at`; distinct status domain
  (`NOT_RUN`/`PENDING`/`VERIFIED_ACTIVE`/etc.); creation migration
  `x3y4z5a6b7c8`.
- `docs/biller-platform/BILLING_SCHEMA_DESIGN_REVIEW.md` Section 3 —
  prior UNRESOLVED finding, carried forward.

### 2.3 Current Consumers

- `eligibility_check_router.py`, `eligibility_workflow_service.py`,
  `test_eligibility_workflow_service.py`,
  `test_eligibility_roster_endpoint.py` (all consume both models).

### 2.4 Current Write Paths

- Both are written exclusively through eligibility-workflow services;
  no dual-writer or competing write path was identified for either
  model in any prior discovery pass.

### 2.5 Risks

- No constraint reconciles the two models' independent status fields
  for the same coverage — they could disagree with no system-enforced
  correction.
- Both ultimately trace to `PatientInsurance` (one mandatorily, one
  optionally), which is itself evidence that `PatientInsurance` is the
  more likely eligibility-authority anchor of the two, but this alone
  does not resolve which of the two models is authoritative for
  *current eligibility state*.

### 2.6 Preservation Requirements

- Both structures, their current tables, and their current consumers
  must remain fully intact. `EligibilityVerification`'s append-only
  (`superseded_at`) behavior must not be altered.
- No consolidation of the two models is authorized by this decision.

### 2.7 Authority Options (as specified)

- **A. `PayerEligibilityCheck` authority.**
- **B. `EligibilityVerification` authority.**
- **C. Separate concepts.**
- **D. Authority intentionally unresolved.**

### 2.8 Recommended Decision

**Option C — Separate concepts**, with a documented (not implemented)
role clarification: `PayerEligibilityCheck` is the lightweight
per-attempt check log, and `EligibilityVerification` is the
authoritative, richer, document-sourced record of current
hospice-specific eligibility state for a coverage.

### 2.9 Alternative Decisions Considered

- **Option A** (`PayerEligibilityCheck` authority): rejected — this
  model is structurally a per-attempt log (simple status enum, no
  document backing, no append-only supersession pattern), not a
  suitable authority for the richer eligibility facts the platform
  actually needs.
- **Option B** (`EligibilityVerification` authority, exclusively):
  rejected as a total authority claim — `PayerEligibilityCheck` still
  serves a distinct, valid, non-overlapping purpose (recording
  individual check attempts) that `EligibilityVerification` does not
  replace; declaring it sole authority for everything eligibility
  would understate `PayerEligibilityCheck`'s legitimate scope.
- **Option D** (unresolved): rejected as the final recommendation for
  the same reason as in Section 1 — the models' purposes are already
  clean and non-competing, so a "separate concepts" recommendation is
  reachable without consolidation or new schema.

### 2.10 Reasoning

- The two models were already found, in Schema Design Review Section
  3, to have "clean, non-overlapping primary purposes." Declaring them
  formally "separate concepts" simply confirms and locks in that
  finding as the permanent architecture, closing the open question
  without touching schema.
- This recommendation preserves `PATIENT_INSURANCE_DUPLICATION_
  ANALYSIS.md`'s and `BILLING_SCHEMA_DESIGN_REVIEW.md`'s existing
  field-level findings rather than reopening them.
- It matches Migration Design Review Section 2.4 (Option C — Remain
  Separate By Design), which was already identified as requiring no
  schema change, only an explicit written decision.

### 2.11 Open Concerns

- The status-field disagreement risk (Section 2.5) is **not resolved**
  by declaring the two concepts "separate" — a future, separately
  authorized reconciliation mechanism (application-level or
  schema-level, per Migration Design Review Section 2.3) is still
  needed if this risk is judged unacceptable. This document does not
  select or authorize that mechanism.
- A future optional LINK (Migration Design Review Section 2.2) between
  the two models remains a reasonable next step but is not authorized
  or scheduled by this decision.

---

## 3. `BillingProviderAgencyAssignment` Write Authority

### 3.1 Current Situation

Verified dual-write structure. Table `billing_provider_agency_
assignments` (1 row verified).

### 3.2 Repository Evidence

- `backend/app/billing/api/billing_provider_router.py`:
  `POST /assignments` (line 311), `PATCH /assignments/{id}` (line 386)
  — Biller Platform; full CRUD across create, update, scope, suspend,
  terminate.
- `backend/app/api/owner_admin.py`: `set_tenant_financials` (line 656)
  — Owner Platform; creates a row at line ~700, or mutates
  `relationship_status = "ACTIVE"` on an existing row; narrowly scoped
  to the "enable Financials for this tenant" administrative action,
  gated on `ein`+`ptan` and an `ACTIVE` `BillingProviderOrganization`.
- `docs/biller-platform/TENANT_BILLER_OWNERSHIP_BOUNDARIES.md` Section
  4 — prior write-authority analysis (three options: single writer
  with Owner delegating to Biller; single writer with Biller
  delegating to Owner; field-level split ownership) and the locked
  Administrative-Authority-vs-Operational-Authority architecture
  (BillingProvider = administrative/operational bridge, per Section 24
  of `BILLING_ORGANIZATION_DISCOVERY_REPORT.md`).
- `docs/biller-platform/BILLING_MIGRATION_DESIGN_REVIEW.md` Section 3
  — prior migration-shape analysis per option.

### 3.3 Current Consumers

- `billing_provider_router.py` (full CRUD), `owner_admin.py`
  (assignment creation/update only, plus read-only organization/
  membership lookups), `billing_provider_access_service.py` (read-only
  permission/financials resolution).

### 3.4 Current Write Paths

- Two independent writers, as above. No optimistic-locking column or
  audit trail distinguishing which platform last wrote a given row was
  found.

### 3.5 Risks

- Both paths can set `relationship_status` and
  `effective_start_at`/`effective_end_at` with no reconciliation rule,
  risking silent overwrite of one platform's change by the other.
- Rows created via Owner Platform receive no
  `BillingProviderAgencyServiceScope` rows, leaving them without scoped
  permissions until a Biller Platform actor separately adds them — a
  verified behavioral asymmetry, not a hypothetical one.

### 3.6 Preservation Requirements

- The table, its current row, and both platforms' existing consumer
  behavior must remain intact until any future, separately authorized
  code change is made. No schema change is required to implement any
  option below except Option C (field-level split), which is not the
  recommended option.

### 3.7 Authority Options (as specified)

- **A. Owner Platform authority.**
- **B. Biller Platform authority.**
- **C. Shared authority.**
- **D. Authority intentionally unresolved.**

### 3.8 Recommended Decision

**Option B — Biller Platform authority**, with the Owner Platform's
`set_tenant_financials` action delegating to Biller Platform's
existing assignment-creation/update logic instead of writing
`BillingProviderAgencyAssignment` rows directly.

### 3.9 Alternative Decisions Considered

- **Option A** (Owner Platform authority): rejected — Owner Platform's
  write path is narrowly purpose-built for one administrative action
  and does not create the accompanying
  `BillingProviderAgencyServiceScope` rows that Biller Platform's path
  creates; making Owner Platform authoritative would require it to
  absorb full assignment-lifecycle responsibility (scope management,
  suspension, termination) that it does not currently implement and
  was never designed to own.
- **Option C** (shared authority): rejected as the recommended option
  because it is the only option that requires an actual schema change
  (a provenance column, per Migration Design Review Section 3.3) to
  enforce field-level write boundaries, and no evidence was found that
  the two platforms need to write genuinely different fields — the
  observed conflict is about *whether* a write should happen and by
  whom, not about needing both platforms to legitimately own different
  columns.
- **Option D** (unresolved): rejected as the final recommendation
  because a concrete, already-documented, schema-free resolution path
  (Option A of the prior write-authority analysis, corresponding to
  Option B here) already exists and was previously identified as most
  consistent with the platform's locked architecture.

### 3.10 Reasoning

- `TENANT_BILLER_OWNERSHIP_BOUNDARIES.md` Section 4 already identified
  the "single writer: Biller Platform; Owner Platform delegates" shape
  as most consistent with the locked
  Administrative-Authority-vs-Operational-Authority architecture
  (BillingProvider as the administrative/operational bridge). This
  recommendation formally adopts that identified direction as the
  Final Schema Authorization recommendation rather than leaving it as
  an unselected option.
- This option requires **no schema migration at all** — only a future,
  separately authorized code-path change in `owner_admin.py` — which
  is the lowest-risk path of the three concrete options and directly
  closes the verified service-scope-creation asymmetry (Section 3.5),
  since assignments would always be created through the path that
  also creates scopes.
- `BillingProviderOrganization` and `BillingProviderAgencyServiceScope`
  are already Biller-only-written per prior ownership-boundary
  findings; making `BillingProviderAgencyAssignment` consistently
  Biller-authoritative aligns this one remaining dual-write structure
  with the rest of the BillingProvider domain rather than leaving it
  as the sole exception.

### 3.11 Open Concerns

- This recommendation does **not** authorize the code change itself.
  `owner_admin.py::set_tenant_financials` continues to write directly
  until a future, separately authorized implementation phase performs
  the delegation change.
- Whether Owner Platform administrators require any *read-only*
  visibility change (e.g., surfacing scope information they currently
  cannot set) is not addressed here and is out of scope for this
  authority decision.
- No optimistic-locking or audit-trail column exists today to detect
  whether a race between the two writers has already occurred
  historically for the existing verified row; this document does not
  propose or authorize any retroactive audit of that row.

---

## Final Approval Test — Self-Check

- ✅ Patient Coverage Authority addressed (Section 1).
- ✅ Eligibility Authority addressed (Section 2).
- ✅ `BillingProviderAgencyAssignment` authority addressed (Section 3).
- ✅ Repository evidence cited throughout (Sections 1.2, 2.2, 3.2).
- ✅ Existing structures preserved — no table, column, or row altered.
- ✅ No duplicate authority introduced — recommendations link or
  clarify existing structures; none are duplicated.
- ✅ No third `PatientCoverage` model proposed.
- ✅ No implementation instructions included — all recommendations are
  explicitly framed as pending future, separately authorized work.
- ✅ No migrations proposed.
- ✅ No schema changes proposed.
- ✅ No data movement proposed.
- ✅ No deletions proposed.
- ✅ No retirements proposed.

## Final Decision

**APPROVED.**

### Approved Final Authority Decisions

1. **Patient Coverage Authority — APPROVED, Option C.**
   `PatientInsurance` and `PatientPayer` remain separate and linked.
   `PatientInsurance` remains the eligibility- and
   verification-oriented structure. `PatientPayer` remains the
   billing and financial structure. `PatientFaceSheet` is **not**
   selected as coverage authority and remains a documentation/
   presentation structure pending any future review.

   Approved rules: no `PatientCoverage` model created; no
   `PatientInsurance` consolidation; no `PatientPayer` consolidation;
   no historical data movement; no forced merger.

   Future direction: an explicit relationship between
   `PatientInsurance` and `PatientPayer` when implementation is
   authorized.

2. **Eligibility Authority — APPROVED, Option C.** Separate concepts.
   `PayerEligibilityCheck` owns attempt and verification activity.
   `EligibilityVerification` owns structured eligibility state.

   Approved rules: no consolidation; no data movement; no
   replacement; no historical rewrite.

   Future direction: cross-reference only.

3. **`BillingProviderAgencyAssignment` — APPROVED, Option B.**
   Operational Authority: Biller Platform. Administrative Authority:
   Owner Platform delegates through approved workflows.

   Approved rules: `BillingProviderAgencyAssignment` retained; no
   replacement entity; no duplicate assignment table; no schema
   changes; no implementation during this phase.

   Future direction: single operational authority model during
   implementation review.

### Locked Decisions (carried forward into any future implementation phase)

- **DO NOT CREATE** `PatientCoverage` without a future explicit
  architecture review.
- **DO NOT CONSOLIDATE** `PatientInsurance`, `PatientPayer`,
  `PatientFaceSheet` during implementation.
- **DO NOT CONSOLIDATE** `PayerEligibilityCheck`,
  `EligibilityVerification` during implementation.
- **DO NOT CREATE** duplicate: Payer authority, Plan authority, Claim
  authority, Payment authority, ERA authority, Remittance authority,
  Denial authority, Appeal authority, Room & Board authority, Audit
  authority, Export authority, Permissions authority, Settings
  authority.

### Implementation Prerequisites (status)

- ✅ Existing authorities preserved
- ✅ Repository evidence documented
- ✅ Historical preservation documented
- ✅ Anti-duplication review completed
- ✅ Legacy billing review completed
- ✅ Ownership boundaries completed
- ✅ Migration strategies documented

## Implementation Status

**IMPLEMENTATION REMAINS BLOCKED.**

Discovery: **COMPLETE.** Schema Design Review: **COMPLETE.** Migration
Design Review: **COMPLETE.** Final Schema Authorization Review:
**APPROVED.** Implementation: **BLOCKED.**

No schema. No migrations. No API changes. No UI changes. No backfill.
No deletion. No retirement. No alembic stamp. No historical migration
rewrite.

The three authority decisions above are now approved and locked. This
approval authorizes only the decisions themselves (which structures
are authoritative, and their relationship strategy). It does **not**,
by itself, authorize schema creation, migration authoring, API
changes, or UI changes. A separate, explicit Implementation
Authorization is required before any of that work may begin.

### Phase Status

- Discovery: **✅ CLOSED**
- Repository Grounding: **✅ COMPLETE**
- System-of-Record Review: **✅ COMPLETE**
- Legacy Billing Review: **✅ COMPLETE**
- Ownership Boundary Review: **✅ COMPLETE**
- Schema Design Review: **✅ COMPLETE**
- Migration Design Review: **✅ COMPLETE**
- Final Schema Authorization Review: **✅ COMPLETE**

### Next Phase — Authorized

**IMPLEMENTATION PLANNING — AUTHORIZED.**

Implementation Planning may produce:

- Implementation sequence
- Epics
- Stories
- Work packages
- Acceptance criteria
- Dependency map
- Validation plan
- Roll-forward repair strategy
- Testing strategy

### Still Not Authorized

- ❌ Schema creation
- ❌ Migration creation
- ❌ Code changes
- ❌ API changes
- ❌ UI changes
- ❌ Backfills
- ❌ Data movement
- ❌ Data deletion
- ❌ Retirement actions
- ❌ Alembic stamp
- ❌ Historical migration rewrite

A separate **Implementation Authorization Review** must occur after
Implementation Planning is completed, before any of the above may be
authorized.
