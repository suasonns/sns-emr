# Insurance Mapping Reconciliation

Purpose: before building any insurance-field harvesting/review capability
(Priority 3 — MBI, Policy Number, Subscriber Information, Payer Name),
determine whether the existing demographic-field suggestion framework can
be reused, per the SSOT rule ("one review framework, not two").

No code changes are made in this document. This is a design decision
record only.

---

## Section 1 — Existing Suggestion Framework (as built today)

**Model**: `app/models/facesheet_field_suggestion.py` — `FacesheetFieldSuggestion`
- Columns: `id`, `tenant_id`, `patient_id`, `field_name` (free-text string,
  not an enum — currently only ever populated with one of `first_name`,
  `last_name`, `dob`, `gender`, `phone`, `address`), `current_value`,
  `suggested_value` (both stored as `String`, uniformly text-encoded even
  for dates), `source_document_id` (FK → `document_records`), `status`
  (`pending` | `accepted` | `rejected` | `dismissed` | `auto_applied`),
  `created_at`/`created_by`, `resolved_at`/`resolved_by`.
- Indexed on `(tenant_id, patient_id, status)`.
- Field-agnostic by design: nothing in the schema restricts `field_name`
  to demographic fields — it is a plain string column.

**Write path**: `app/api/patients.py::_reconcile_demographic_field()`,
called from `persist_patient_from_hnp_extraction()` for each of the 6
demographic fields on every H&P-derived document ingest. Behavior is
governed by the tenant's `facesheet_protection_mode` (`OFF` / `WARN` /
`REQUIRE_REVIEW`, a `Tenant` column with a DB check constraint):
- `OFF` — overwrite immediately, no record (legacy).
- `WARN` — overwrite immediately AND record a `status="auto_applied"`
  row (visible/audited, not blocking).
- `REQUIRE_REVIEW` (default) — never overwrite; insert a `status="pending"`
  row for a human to resolve.
- New values are only ever queued when the target field is already
  non-empty and the new value differs (write-once-then-protect pattern).
- Deduplicates against any existing `pending`/`auto_applied` row for the
  same `(tenant_id, patient_id, field_name, suggested_value)`.

**Review path — API**: **does not exist.** The docstring on
`_reconcile_demographic_field()` references "the facesheet suggestions
endpoints," but no `GET`/`accept`/`reject`/`dismiss` route for
`FacesheetFieldSuggestion` exists anywhere in `app/api/`. Confirmed by
exhaustive grep across the backend — the only references to
`FacesheetFieldSuggestion` are the model file, its import, and the write
path in `patients.py`.

**Review path — UI**: **does not exist.** Confirmed by exhaustive grep
across `sns-emr-frontend/src` — zero references to facesheet suggestions
anywhere in the frontend.

**Apply path**: **does not exist** (no code transitions a `pending` row to
`accepted`/`rejected`/`dismissed`, and no code applies an accepted
suggestion's value back onto `PatientFaceSheet`).

**Conclusion**: the "harvest → suggestion queue → review → apply" loop
described in prior directives is **only half-built**. The write/queue
half exists and works (used today for demographic conflicts from H&P
text). The review/apply half — the part a human actually interacts with —
has never been implemented, for demographic fields or anything else. This
is true regardless of whether insurance fields reuse it or not.

---

## Section 2 — Current Insurance Fields (existing storage)

All already exist on `PatientFaceSheet` (`app/models/patient_facesheet.py`):

| Field | Column | Notes |
|---|---|---|
| MBI | `mbi_number` | String |
| Primary Payer (name) | `primary_payer` | String |
| Primary Payer Type | `primary_payer_type` | CMS HOPE A1400 crosswalk category — distinct from the free-text name |
| Primary Policy Number | `primary_policy_number` | String |
| Secondary Payer (name) | `secondary_payer` | String |
| Secondary Payer Type | `secondary_payer_type` | String |
| Secondary Policy Number | `secondary_policy_number` | String |

Not present anywhere in the schema today: a dedicated Subscriber
Name/Subscriber DOB/Subscriber Relationship field. `claim_export_service.py`
references `subscriber_id`/`subscriber_id_type` but pulls them from a
runtime `payer_block` dict built at claim-export time, not from a stored
column — there is no persisted "subscriber information" field on
`PatientFaceSheet` or elsewhere. If Subscriber Information needs to be
harvested/reviewed, new columns are required on `PatientFaceSheet` (not a
new table — same SSOT owner as the other insurance fields).

All of the above fields are currently populated **only by direct staff
entry** via the existing `PATCH` facesheet endpoints in `patients.py`
(lines ~1297-1386, ~2009-2019, ~2657-2660, ~3553-3559). **No OCR/extraction
code path writes to any of these fields today.** This is a genuinely new
capability, not an extension of something already running in production.

---

## Section 3 — Can the Existing Suggestion Framework Be Extended?

**Classification: REUSE WITH EXTENSION.**

Rationale:
- The `FacesheetFieldSuggestion` schema is already field-name-agnostic
  (plain string column) and dedupes/resolves generically — nothing about
  its shape is demographic-specific except the comment and the 6 values
  it happens to be fed today.
- `current_value`/`suggested_value` are already stored as uniform text,
  so `mbi_number`, `primary_payer`, `primary_policy_number`,
  `secondary_payer`, `secondary_policy_number` slot in as additional
  `field_name` values with zero schema changes.
- `source_document_id` already exists for traceability back to the
  originating document — exactly what "OCR harvested this from document
  X" requires.
- The `protection_mode` (`OFF`/`WARN`/`REQUIRE_REVIEW`) semantics apply
  identically: an insurance card OCR pass conflicting with an
  already-entered policy number is the same shape of problem as an H&P
  conflicting with an already-entered DOB.

What must be added (extension, not replacement):
1. `field_name` values: `mbi_number`, `primary_payer`, `primary_policy_number`,
   `secondary_payer`, `secondary_policy_number`, and (if pursued)
   `subscriber_name`/`subscriber_dob`/`subscriber_relationship` — the last
   three requiring new `PatientFaceSheet` columns first (Section 2).
2. A generic reconciliation helper mirroring `_reconcile_demographic_field()`
   but parameterized for these fields (the current function is not
   private-API-locked to demographics, just currently only called with
   demographic args).
3. **The review/apply API + UI that does not exist yet for ANY field.**
   This is required regardless of which fields flow through the queue,
   and is the actual gap — not a new insurance-specific concern.

What must NOT be created:
- `InsuranceSuggestionTable` / `InsuranceReviewTable` / `InsuranceExtractionTable`
  / `InsuranceFieldMappingTable` / `InsuranceCandidateTable` / `OCRInsuranceQueue`
  — none of these are needed; `FacesheetFieldSuggestion` already covers
  the shape.
- A second facesheet-protection-mode-style tenant setting — the existing
  `Tenant.facesheet_protection_mode` already governs write behavior
  tenant-wide and applies unchanged.

---

## Section 4 — SSOT Decision (per field)

| Field | Source of Truth | Notes |
|---|---|---|
| MBI | `PatientFaceSheet.mbi_number` | OCR candidate + staff review, same as today's demographic fields |
| Primary Payer (name) | `PatientFaceSheet.primary_payer` | OCR candidate + staff review |
| Primary Payer Type | `PatientFaceSheet.primary_payer_type` | Staff-reviewed (CMS crosswalk category selection, not free-text OCR) |
| Primary Policy Number | `PatientFaceSheet.primary_policy_number` | OCR candidate + staff review |
| Secondary Payer (name) | `PatientFaceSheet.secondary_payer` | OCR candidate + staff review |
| Secondary Policy Number | `PatientFaceSheet.secondary_policy_number` | OCR candidate + staff review |
| Subscriber Information | *(does not yet exist — new `PatientFaceSheet` columns if pursued)* | Would be OCR candidate + staff review, owned by the same table |
| Conflict/candidate queue | `FacesheetFieldSuggestion` (extended `field_name` domain) | Not a second source of truth — a staging area that resolves into the fields above; never read as authoritative by any consumer |

No field gets two owners. `FacesheetFieldSuggestion` is explicitly a
**staging/reconciliation area**, not a source of truth — consumers
(billing, claims, readiness) must always read `PatientFaceSheet`, never
the suggestion table.

---

## Section 5 — Recommended Implementation

```
OCR / document extraction
        ↓
Candidate value (per insurance field)
        ↓
FacesheetFieldSuggestion (field_name extended to insurance fields)
        ↓
Staff review  ← NEW: this is the actual missing piece, for both
                demographic AND insurance fields
        ↓
Apply  ← NEW: also missing today
        ↓
PatientFaceSheet (SSOT)
```

Concretely, when Priority 3 is authorized to proceed:
1. Extend `_reconcile_demographic_field()` (or a thin sibling using the
   identical logic) to also accept the 5 existing insurance columns.
2. Build the missing review/apply layer once, generically, for
   `FacesheetFieldSuggestion` — covering both demographic and insurance
   `field_name` values with the same endpoints/UI. This closes a gap that
   has existed since before this project started, not something new
   introduced by insurance harvesting.
3. Only if Subscriber Information is required: add the new
   `PatientFaceSheet` columns first, then feed them through the same
   path — never a separate table.
4. Wire an OCR/extraction source (insurance card and/or referral
   documents) to call the extended reconciliation helper. This is the
   only genuinely new "harvest" logic; everything downstream of it is
   reused.

No new tables. No new queue. One suggestion system, one review process,
one SSOT (`PatientFaceSheet`) — consistent with the SOC precedent
(`SOCValidationService`: one rule, multiple entry points) applied here as
one queue, multiple field domains.
