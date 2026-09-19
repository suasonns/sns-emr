# Tenant / Biller Ownership Boundaries

## Status

**DRAFT — Prompt 3 deliverable.** Documentation only. No schema,
migration, API, or UI changes are authorized by this document.
Schema Design and Implementation remain **BLOCKED**.

## Purpose

Determine, on verified repository evidence only, the ownership
boundaries, write authority, and shared-record strategy for the
structures identified across the prior discovery documents
(`TENANT_BILLER_SYSTEM_OF_RECORD_MATRIX.md`,
`LEGACY_BILLING_SCHEMA_INVENTORY.md`,
`PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`), and to define the role of
`BillingProviderOrganization` in the future architecture. This document
does not decide unresolved authority questions where the required
evidence does not yet exist; it documents what is and is not proven.

## Method

Every ownership/write-authority claim below is backed by a direct
citation to model, router, or service code. No claim is based on
naming convention, UI presence, or assumption. Where evidence is
incomplete, the finding is recorded as **UNRESOLVED**, not decided by
default.

## Carried-Forward Findings (from Legacy Inventory Review — Locked)

1. No evidence that Owner Platform billing functionality was removed.
2. Evidence supports an architectural exclusion boundary
   (`BILLING_AND_LICENSING_MANAGEMENT_SCOPE.md`,
   `Owner-Platform-Roadmap.md`) rather than deleted billing
   implementation.
3. `BillingProviderOrganization` and `BillingProviderAgencyAssignment`
   remain significant existing billing structures — addressed in
   detail below.
4. Patient Coverage Authority remains unresolved.
5. Eligibility Authority remains unresolved.
6. `PatientFaceSheet` must be included in the ownership-boundary review
   — addressed below.
7. No third `PatientCoverage` model is created here.
8. `PatientInsurance`, `PatientPayer`, and `PatientFaceSheet` ownership
   is **not** resolved in this document without repository evidence
   sufficient to do so — and that evidence does not yet exist.

---

## Section 1 — Ownership Boundary Framework (Reused, Not Redefined)

This document reuses two already-locked frameworks rather than
inventing new ones:

- **Administrative Authority vs. Operational Authority** (locked in
  Section 24 of `BILLING_ORGANIZATION_DISCOVERY_REPORT.md`):
  Administrative Authority = platform-level decisions about *who is
  allowed to operate* (e.g., onboarding a billing company, enabling a
  tenant's Financials access). Operational Authority = day-to-day
  execution of billing work itself (claims, eligibility, payment
  posting, etc.) once access is enabled.
- **Ownership categories** from
  `TENANT_BILLER_SYSTEM_OF_RECORD_MATRIX.md`: `TENANT OWNED`,
  `BILLER OWNED`, `SHARED DOMAIN OWNED` (only if all 5 evidence
  criteria are met), and `OWNERSHIP UNRESOLVED`.

A new category is introduced here because the evidence requires it:

- **WRITE AUTHORITY CONFLICT (UNRESOLVED)** — used when two
  independent, currently-active code paths both perform create/update
  operations against the same table, with no existing constraint,
  locking strategy, or single-writer rule preventing divergence. This
  is distinct from `OWNERSHIP UNRESOLVED` (which means ownership was
  never determined) — a write-authority conflict means ownership *is*
  contested by verified, currently-running code, not merely undecided.

---

## Section 2 — Per-Structure Determination

### 2.1 `BillingProviderOrganization` (`billing_provider_organizations`)

- **Ownership: BILLER OWNED.**
- **Write authority (verified):** Created and updated exclusively via
  `backend/app/billing/api/billing_provider_router.py`
  (`POST /organizations` at line 188, `PATCH /organizations/{id}` at
  line 236). No `BillingProviderOrganization(...)` construction or
  `db.add`/attribute-mutation against this model was found anywhere in
  `backend/app/api/owner_admin.py`.
- **Owner Platform relationship:** `owner_admin.py`'s
  `set_tenant_financials` (line 656) only **reads** an existing
  `BillingProviderOrganization` via `db.get(...)` to validate it is
  `ACTIVE` before linking a tenant to it. Owner Platform does not
  create or modify the organization record itself.
- **Conclusion:** No conflict. Biller Platform is the sole writer of
  this table; Owner Platform is a verified read-only consumer for
  eligibility-to-link validation.

### 2.2 `BillingProviderAgencyAssignment` (`billing_provider_agency_assignments`)

- **Ownership: WRITE AUTHORITY CONFLICT (UNRESOLVED).**
- **Write authority (verified — two independent writers):**
  1. `backend/app/billing/api/billing_provider_router.py`,
     `POST /assignments` (line 311) and
     `PATCH /assignments/{id}` (line 386) — the Biller Platform's own
     dedicated assignment-management endpoints.
  2. `backend/app/api/owner_admin.py`, `PATCH
     /tenants/{target_tenant_id}/financials` (`set_tenant_financials`,
     line 656) — creates a new `BillingProviderAgencyAssignment` row
     directly (line 700: `row = BillingProviderAgencyAssignment(...)`,
     `db.add(row)`) when none exists for the tenant/provider pair, or
     mutates `row.relationship_status = "ACTIVE"` on an existing row
     when one does.
- **What is proven:** Both platforms currently write to this table
  through independently maintained code paths. No optimistic-locking
  column, single-writer flag, or reconciliation rule was found in the
  model (`backend/app/billing/models/billing_provider_agency_assignment.py`)
  preventing the two paths from producing conflicting
  `relationship_status`/`effective_start_at`/`effective_end_at` values
  for the same tenant/organization pair.
- **What is not proven / not decided here:** Which platform *should*
  hold write authority going forward. This document does not assign a
  winner. See Section 4 (Shared-Record Strategy) for the option
  analysis.
- **Verified record count (read-only):** 1 row (see
  `LEGACY_BILLING_SCHEMA_INVENTORY.md`, Section C).

### 2.3 `BillingProviderAgencyServiceScope` (`billing_provider_agency_service_scopes`)

- **Ownership: BILLER OWNED.**
- **Write authority (verified):** Created only inside
  `billing_provider_router.py`'s `POST /assignments` handler (line
  348–351, one row per requested `service_scope` at assignment-creation
  time). No write to this table was found in `owner_admin.py`.
- **Conclusion:** No conflict. This table is downstream of assignment
  creation and is Biller-Platform-only in practice, even though its
  parent row (`BillingProviderAgencyAssignment`) can be created by
  either platform. If Owner Platform's `set_tenant_financials` path
  creates an assignment with no `service_scopes` rows, that assignment
  would carry no scoped permissions until a Biller Platform actor adds
  them — this is a real, verified behavioral asymmetry between the two
  assignment-creation paths, not a hypothetical one, and is recorded as
  an open defect rather than resolved here.

### 2.4 `PatientInsurance`, `PatientPayer`, `PatientFaceSheet`

- **Ownership: UNRESOLVED (all three), per explicit instruction.** No
  new evidence sufficient to resolve this has been produced since
  `LEGACY_BILLING_SCHEMA_INVENTORY.md`'s Additional Discovery Pass.
- **What is proven:**
  - `PatientInsurance`: tenant-scoped (`TenantScopedMixin`), FK target
    of `PayerEligibilityCheck`/`EligibilityVerification`; primary
    consumer domain is eligibility.
  - `PatientPayer`: not tenant-scoped directly (no `tenant_id` column);
    is the verified source of the claim-export payer/subscriber block
    via `msp_validation_service.py` → `claim_export_service.py`.
  - `PatientFaceSheet`: has an explicit `tenant_id` column; is
    documented elsewhere in the repository
    (`docs/workflows/SourceOfTruthMatrix.md`) as the declared Source of
    Truth for insurance identifiers, a claim that conflicts with the
    verified claim-export runtime behavior (see
    `LEGACY_BILLING_SCHEMA_INVENTORY.md`, Section B).
- **What is not proven:** Which of the three (if any) should hold
  write authority for a given insurance identifier field going forward,
  and whether the correct resolution is LINK (add explicit FKs between
  the three without removing any) or CONSOLIDATE (merge into fewer
  structures). Both require a dedicated, separately reviewed
  forward-only migration plan per the existing Retirement/Consolidation
  gate — neither is authorized here.
- **No third `PatientCoverage` model is proposed or implied by this
  section.**

### 2.5 `Contract` (`payer_contracts`) — Referenced by `BillingProviderOrganization`

- Not a shared-record conflict: `payer_contracts` FKs to `payers`, not
  to `BillingProviderOrganization`; no Owner Platform write path was
  found against this table. Recorded here only because it was newly
  confirmed to exist (0 rows) during the prior discovery pass and had
  not previously been assigned an ownership category. **Ownership:
  BILLER OWNED** (Biller Platform payer/contract domain; no competing
  writer found).

---

## Section 3 — Write Authority Matrix

| Structure | Owning Platform | Write Authority | Conflict? |
|---|---|---|---|
| `BillingProviderOrganization` | Biller Platform | `billing_provider_router.py` only | No |
| `BillingProviderAgencyAssignment` | **Contested** | `billing_provider_router.py` **and** `owner_admin.py` | **Yes — unresolved** |
| `BillingProviderAgencyServiceScope` | Biller Platform | `billing_provider_router.py` only (via assignment creation) | No (but see 2.3 asymmetry defect) |
| `PatientInsurance` | Unresolved | Eligibility-workflow services (not exhaustively re-enumerated here; see Matrix) | Unresolved, not conflict-proven |
| `PatientPayer` | Unresolved | `app/api/patients.py` CRUD; consumed by `claim_financials.py`/`msp_validation_service.py` | Unresolved, not conflict-proven |
| `PatientFaceSheet` | Unresolved | Facesheet-domain services/APIs (per Legacy Inventory) | Unresolved; documented SSOT claim conflicts with verified claim-export behavior |
| `payer_contracts` (`Contract`) | Biller Platform | No writer located this pass | No |

---

## Section 4 — Shared-Record Strategy (Option Analysis Only — No Decision)

This section applies specifically to the one **proven** write-authority
conflict, `BillingProviderAgencyAssignment`. It presents options; it
does not select one.

**Option A — Single Writer, Owner Platform Delegates.** Biller
Platform's `billing_provider_router.py` becomes the only writer.
`owner_admin.py`'s `set_tenant_financials` would call into the Biller
Platform's assignment-creation logic (internally or via API) instead of
constructing `BillingProviderAgencyAssignment` rows directly. This
would also close the Section 2.3 asymmetry (service scopes would
always be created alongside the assignment, from one code path).
Requires coordinated changes to both `owner_admin.py` and
`billing_provider_router.py` — not authorized here.

**Option B — Single Writer, Biller Platform Delegates to Owner
Platform's Existing Path.** Reverse of Option A. Less consistent with
the Administrative-Authority-enables/Operational-Authority-executes
split already locked in Section 24, since enabling Financials is an
Administrative Authority action (Owner Platform's role) while ongoing
assignment management (scopes, suspension, termination) is Operational
Authority (Biller Platform's role) — this option would blur that
distinction rather than reinforce it.

**Option C — Field-Level Split Ownership.** Owner Platform retains
write authority only over assignment *creation* and
`relationship_status` transitions triggered by the Financials toggle;
Biller Platform retains write authority over `service_scopes`,
`effective_end_at` (termination), and any other operational fields.
This would require an explicit, enforced field-level write-authority
rule (e.g., separate service-layer functions with restricted field
sets) that does not currently exist — today both paths can write the
same fields.

**Recommendation (not a decision):** Option A most closely matches the
already-approved Administrative-Authority-vs-Operational-Authority
architecture (Section 24) and would resolve the Section 2.3 asymmetry
as a side effect. This document records it as the most consistent
option with prior locked decisions; it does not authorize implementing
it.

---

## Section 5 — Role of `BillingProviderOrganization` in the Future Architecture

Based on verified evidence only:

- `BillingProviderOrganization` represents a third-party or in-house
  billing company that can be assigned to service one or more tenant
  agencies. Its lifecycle (creation, activation/deactivation) is
  entirely Biller-Platform-owned.
- Its **link** to a tenant (`BillingProviderAgencyAssignment`) is the
  Administrative Authority boundary point: Owner Platform's
  `set_tenant_financials` is the mechanism by which a platform
  administrator authorizes that a tenant *may* have billing
  operations performed by a given provider, gated on `ein`+`ptan` and
  the provider being `ACTIVE`.
- Once linked, `BillingProviderAgencyServiceScope` rows define the
  Operational Authority detail (which specific billing capabilities —
  `CLAIMS`, `ELIGIBILITY`, `PAYMENT_POSTING`, `CAP_MONITORING`, etc. —
  the provider may exercise, and at what permission level). This is
  Biller-Platform-owned and, per verified evidence, is currently only
  populated through the Biller Platform's own assignment-creation
  endpoint.
- This confirms `BillingProviderOrganization` is the intended
  structural bridge between Administrative Authority (Owner Platform:
  "is this tenant allowed to have billing enabled, with which
  provider") and Operational Authority (Biller Platform: "what can that
  provider actually do for this tenant") — consistent with, and
  reinforcing, the already-locked Section 24 architecture. The
  Section 2.2/4 write-authority conflict is the one place this bridge
  is not yet cleanly enforced in code.

---

## Section 6 — Explicit Non-Decisions (Carried Forward)

- No third `PatientCoverage` model is created, proposed, or implied.
- `PatientInsurance`, `PatientPayer`, and `PatientFaceSheet` ownership
  remains **UNRESOLVED** — not assigned to TENANT, BILLER, or SHARED by
  default.
- No schema, migration, API, or UI change is authorized by this
  document.
- No write-authority conflict identified in Section 2.2 is resolved by
  this document — only documented, with options analyzed, not chosen.
- No retirement, consolidation, or LINK migration is authorized for any
  structure named in Section 2.

## Final Status

- Ownership boundaries: **documented** for
  `BillingProviderOrganization`, `BillingProviderAgencyAssignment`
  (flagged unresolved conflict), `BillingProviderAgencyServiceScope`,
  and `payer_contracts`.
- Ownership boundaries: **remain UNRESOLVED** for `PatientInsurance`,
  `PatientPayer`, and `PatientFaceSheet`, per explicit instruction and
  because sufficient evidence does not yet exist to resolve them.
- Patient Coverage Authority: **UNRESOLVED.**
- Eligibility Result Authority: **UNRESOLVED.**
- Schema Design: **BLOCKED.**
- Implementation: **BLOCKED.**

This document is submitted for your review. It does not authorize
Schema Design to begin.
