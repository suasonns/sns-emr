# Hospice Reimbursement Chronology — Eligibility Traceability Epic (Implementation Plan)

Status: **planning only — no code in this document has been written to the repository.**

This document converts the findings from Phases 1-58 (`billing_inventory_and_gap_analysis.md` and its
referenced docs) into an actionable engineering plan. It does not reopen or re-litigate any prior
finding. It assumes every conclusion already reached is correct and asks only: what is the smallest set
of changes that closes the four confirmed gaps (Chronology, Attribution, Audit, Traceability) before
any billing-facing AI feature is built.

**Explicitly out of scope for this epic**: Billing Readiness Engine (AI), Revenue Leakage Detection,
Claim Risk AI, Biller Command Center, Certification Monitor (AI), Recertification Monitor (AI). Those
features consume the chronology layer this epic builds — they are not part of it, and none of their
code is touched here.

**In scope**: the audit-grade chronology layer itself — the persisted, attributed, reconstructable
record of eligibility/benefit-period/readiness state that every future AI feature will read from
instead of re-deriving.

---

## 1. Why this ordering

Every AI-facing feature proposed so far (Certification Monitor, Billing Readiness Engine, Revenue
Leakage, Claim Risk) needs to answer "why/who/when did this state become true" for the patient it is
reasoning about. Today that question is only answerable for Certification and Recertification (both
already have real audit tables). It is **not** answerable for Benefit Period or Billing Readiness — the
two areas any of those AI features would most need to cite as evidence. Building AI on an ungrounded
foundation would produce recommendations that cannot themselves be defended under audit, which
reproduces the exact problem this entire engagement was commissioned to prevent. This epic exists to
remove that dependency risk before any AI code is written.

---

## 2. Scope item 1 — BenefitPeriod Audit Trail

**Gap closed**: Audit Gap — "No event stream exists for any Benefit Period lifecycle action."

**Design basis**: `docs/planning/benefit_period_audit_design.md` (Phase 38), extended in Phase 53 with
`related_certification_id`.

### 2.1 New table: `benefit_period_status_events`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `benefit_period_id` | FK → `benefit_periods.id`, not null | |
| `event_type` | enum: `CREATED`, `ROLLED`, `CLOSED`, `CORRECTED`, `REOPENED` | matches Phase 38 design |
| `actor_user_id` | FK → `users.id`, not null | closes the Attribution Gap for this table |
| `occurred_at` | timestamptz, not null, server default now() | |
| `reason` | text, nullable for `CREATED`/`ROLLED`, required for `CORRECTED`/`REOPENED` | mirrors `CertificationStatusEvent.reason` pattern |
| `previous_value` | JSONB, nullable | snapshot of prior row state; null on `CREATED` |
| `new_value` | JSONB, not null | snapshot of row state after the event |
| `related_certification_id` | FK → `certifications.id`, nullable | Phase 53 addition — populated when a certification check gated the event; this is the field that converts the Phase 54 reverse-only FK into a forward causal record |
| `retention` | not a column — retention is indefinite/append-only, consistent with `CertificationStatusEvent` |

Append-only, no update/delete path, same posture as `CertificationStatusEvent`.

### 2.2 Code changes required (planning-level, not implemented here)
- `app/services/benefit_period_service.py::rollover_benefit_period` — insert a `benefit_period_status_events`
  row inside the existing transaction (same atomic block already confirmed correct in Phase 11), passing
  the certification id that satisfied the (also-being-added, see Scope Item 4) gate check.
- New endpoint(s) if benefit-period correction/close/reopen actions are added — each must write its
  corresponding event before or as part of any state mutation, never after.
- `BenefitPeriod.created_by` (already identified as unpopulated) gets backfilled going forward via the
  same event-insert transaction rather than as a separate column-only fix, so the two gaps close together.

### 2.3 Acceptance criteria
- Every benefit period created after this ships has at least one `CREATED` event with a non-null actor.
- Every rollover produces a `ROLLED` event referencing both the prior and new benefit period state.
- A query "list all lifecycle events for benefit period X" returns a complete, chronologically ordered
  history with no gaps, matching the existing `CertificationStatusEvent` query pattern used in Phase 10.

---

## 3. Scope item 2 — Eligibility Chronology

**Gap closed**: Chronology Gap — "Cannot answer why this benefit period was created as a causal record."

**Design basis**: `reimbursement_chronology_model.md` (Phase 51), `certification_to_payment_chain.md`
(Phase 54).

### 3.1 Approach
No new source-of-truth table beyond `benefit_period_status_events` above. Chronology is a **read-side
composition**, not a new write path, to avoid duplicating data that already exists in
`CertificationStatusEvent`, `AdmissionStatusHistory`, and the new benefit-period event table.

- New service: `app/services/eligibility_chronology_service.py` (planned name) —
  `build_patient_chronology(patient_id)` reads, in timestamp order, across:
  - `AdmissionStatusHistory`
  - `Referral` (`created_by`, `reviewed_by`/`reviewed_at`)
  - `CertificationStatusEvent`
  - `benefit_period_status_events` (new)
  - billing-readiness history (new, see Scope Item 3)
  and returns a single ordered timeline with `event_type`, `actor`, `timestamp`, `reason`, `evidence_ref`
  per row.
- This function is read-only. It performs no writes and requires no schema changes beyond Scope Item 1
  and Scope Item 3 already existing.

### 3.2 Acceptance criteria
- For a single test patient, `build_patient_chronology()` returns every event from Referral through the
  most recent Benefit Period action in strict chronological order.
- Every returned event has a non-null actor and non-null timestamp (this is a direct test of the
  Attribution Gap closure, not just a formatting exercise).
- Missing-evidence rows (e.g., Assessment/Transfer/Discharge, still confirmed out of scope this
  engagement) are explicitly labeled `"not tracked"` rather than omitted, preserving the engagement's
  standing rule of never implying compliance/completeness that hasn't been verified.

---

## 4. Scope item 3 — Readiness Persistence

**Gap closed**: Chronology Gap — "Cannot answer why patient was billable on DATE X" (Phase 52, the
single largest confirmed gap in the entire engagement).

**Design basis**: `app/billing/services/billing_readiness_service.py::check_patient_billing_readiness`
(confirmed pure-compute, zero persistence).

### 4.1 New table: `billing_readiness_verdicts`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `patient_id` | FK, not null | |
| `evaluated_at` | timestamptz, not null | when the check ran |
| `is_ready` | boolean, not null | the verdict |
| `blockers` | JSONB, not null (empty array if ready) | the exact blocker list already computed by the existing function — no new logic, just persisted |
| `benefit_period_id` | FK, nullable | the benefit period the verdict was evaluated against, if any |
| `certification_id` | FK, nullable | the certification the verdict cited, if any — another forward-traceability link |
| `triggered_by` | enum: `SCHEDULED_CHECK`, `MANUAL_CHECK`, `CLAIM_SUBMISSION_ATTEMPT` | records why the check ran, not just that it did |

### 4.2 Code changes required (planning-level)
- `check_patient_billing_readiness()` keeps its existing pure-compute logic (already confirmed correct —
  this is not a re-audit or rewrite of the eligibility rules themselves) and gains one additional step:
  insert a `billing_readiness_verdicts` row with its own output before returning. This is strictly
  additive — no existing return value, blocker logic, or call signature changes.
- Callers (claim-submission flow, any scheduled job) are unaffected; the persistence is internal to the
  service function.

### 4.3 Acceptance criteria
- After this ships, "why was patient billable on DATE X" is answered by a single indexed query
  (`patient_id`, `evaluated_at <= X`, most recent row) — no re-computation, no staff recollection.
- Every historical verdict is immutable once written (no update path — new checks produce new rows,
  consistent with the append-only posture used everywhere else in this epic).

---

## 5. Scope item 4 — User Attribution

**Gap closed**: Attribution Gap (both instances) — Benefit Period actions and, if confirmed missing on
investigation, election-signing.

### 5.1 Approach
This is not a separate table — it is a *constraint*, enforced by making the actor column on every new
event/verdict table (Sections 2 and 4 above) **non-nullable at the schema level**, the same pattern
already relied upon for `CertificationStatusEvent.changed_by_user_id` and
`AdmissionStatusHistory.changed_by`. No event or verdict row can be written without an actor.

For the still-open "does election signing capture a user-attribution field" question (carried forward
from Phase 51, never resolved because it fell outside every prior phase's specific investigation scope):
this epic's first engineering task includes a direct code read of the election-signing code path before
any schema work begins, so this gets resolved as fact rather than remaining an assumption. If it is
found to be missing, it is added as a fifth, explicitly-named subtask before this scope item is
considered complete — this document will not claim the gap is closed until that read has actually
happened.

### 5.2 Acceptance criteria
- Every row written by Scope Items 1 and 3 has a non-null actor, enforced by database constraint, not
  just application-layer convention.
- The election-signing attribution question is answered with a direct citation (file:line), not
  inferred, before this scope item is marked done.

---

## 6. Scope item 5 — Eligibility Timeline Reporting

**Gap closed**: Traceability Gap — no consumer-facing surface exists for any of the above; the data
would otherwise exist only in tables, not in anything a case manager, biller, or compliance officer (or
their counsel, during a records request) could actually read.

### 6.1 Approach
- One new read-only report endpoint, e.g. `GET /api/patients/{id}/eligibility-timeline`, backed directly
  by `build_patient_chronology()` (Scope Item 2). No new business logic — this is a presentation layer
  over data Scope Items 1-4 already produce.
- Output format matches the "audit package" shape already validated conceptually in
  `cms_audit_package.md` / `cdph_survey_package.md` (Phases 55-56): each row labeled Automatically
  Available / Partially Available / Unavailable (or the CDPH PASS/PARTIAL/FAIL/UNKNOWN equivalent) so the
  report itself demonstrates, rather than merely claims, defensibility.
- No PDF/export requirement is assumed for this epic; that is left as a follow-on decision once the
  underlying data exists, to avoid scope creep into presentation formats not yet requested.

### 6.2 Acceptance criteria
- For a test patient with a full Referral→Payment history, the endpoint returns a complete, correctly
  ordered timeline with no unexplained gaps other than the explicitly-still-unknown areas (Assessment,
  Transfer, Discharge) — which must display as labeled unknowns, not silent omissions.
- This is the surface used to re-run the Phase 43 (`cms_audit_simulation.md`) and Phase 44
  (`cdph_survey_simulation.md`) walkthroughs after implementation, to confirm the PARTIAL verdicts from
  those phases improve to PASS/YES rather than merely asserting they do.

---

## 7. Sequencing

Scope items are not independent; item 2 and item 5 both read data produced by items 1, 3, and 4. Build
order:

1. Scope Item 1 (BenefitPeriod audit trail) + Scope Item 4's non-null-actor constraint applied to it.
2. Scope Item 3 (Readiness persistence) + Scope Item 4's non-null-actor constraint applied to it,
   in parallel with (1) — no shared dependency between them.
3. Scope Item 4's remaining open question (election-signing attribution) — a direct code read, done
   alongside (1)/(2), not blocking either.
4. Scope Item 2 (Chronology composition service) — depends on (1) and (3) existing.
5. Scope Item 5 (Timeline reporting endpoint) — depends on (2).

No item in this epic requires or touches Certification, Recertification, Claim, or Payment code paths —
all of those remain read-only sources cited by the new chronology service, consistent with the
engagement's confirmed finding that those areas are not the problem.

---

## 8. Explicit non-goals (repeated for this document's own record)

This epic does **not**:
- add or modify any certification/recertification business rule (already correct, per Phase 10-11).
- add any AI-generated recommendation, prediction, or determination of any kind.
- change claim-status or remittance/payment logic (a separate, already-documented gap, out of scope
  here).
- build the election-addendum-2026 transition fix (a separate, already-scoped, time-critical item
  tracked in `election_addendum_transition_plan.md` — not folded into this epic to avoid conflating two
  independent deadlines).

## 9. Status

No code has been written under this plan. This document is the engineering-ready specification the
next implementation session should execute against, in the sequence given in Section 7, starting with
Scope Item 1.
