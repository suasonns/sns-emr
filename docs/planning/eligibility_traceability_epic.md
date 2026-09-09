# Eligibility Traceability Epic — Engineering Implementation Plan

Status: **implementation plan — no production code has been written against this document.**

This supersedes the earlier lighter-weight version of this file. Review, research, and compliance
analysis are complete (see `billing_inventory_and_gap_analysis.md`, Phases 1-58, and the four documents
it indexes for every underlying finding cited below). This document does not re-derive or re-justify
those findings — it converts them directly into engineering work.

## Purpose

Enable SNS to answer, from persisted SNS records alone:

1. Why was this patient billable on DATE X?
2. Who made this patient billable?
3. What certification supported billing?
4. What benefit period supported billing?
5. What evidence supported eligibility?
6. What claim resulted?
7. What payment resulted?
8. Show the chronology.

Today, questions 1-2 and 8 are **not** answerable (billing readiness is pure live computation with zero
persistence; benefit periods have no actor or event history). Questions 3, 5, 6, 7 are partially
answerable (certification and claim data exist but are not linked forward into a single causal chain).
Question 4 is answerable only in reverse (a certification can point at a benefit period; a benefit
period cannot show which certification, if any, was checked when it was created).

Explicitly excluded from this epic (consumers of it, not part of it): Billing Readiness Engine (AI),
Revenue Leakage Detection, Claim Risk AI, Biller Command Center, Certification Monitor, Recertification
Monitor.

---

## Workstream 1 — BenefitPeriod Audit Trail

**Problem**: `rollover_benefit_period` and the benefit-period creation path perform no audit-trail
writes. `BenefitPeriod.created_by` exists as a column but is never populated. There is no event history
of any kind (created/rolled/closed/corrected/reopened) and no update/close/correct/reopen endpoint even
exists today — only `POST` (create/rollover) and `GET` in `app/api/benefits.py`.

**Current State**: `benefit_periods` table only, no companion event table. `created_by` column present
but unpopulated at every call site. No lifecycle beyond insert.

**Target State**: Every benefit-period lifecycle action (create, rollover, and any future
close/correct/reopen) writes an immutable, actor-attributed event row in the same transaction as the
state change.

**Database Changes**:
- New table `benefit_period_status_events`:
  - `id` UUID PK
  - `benefit_period_id` FK → `benefit_periods.id`, not null, indexed
  - `event_type` enum (`CREATED`, `ROLLED`, `CLOSED`, `CORRECTED`, `REOPENED`)
  - `actor_user_id` FK → `users.id`, **not null**
  - `occurred_at` timestamptz, not null, server default `now()`
  - `reason` text, nullable except required (app-layer + CHECK constraint) for `CORRECTED`/`REOPENED`
  - `previous_value` JSONB, nullable (null only on `CREATED`)
  - `new_value` JSONB, not null
  - `related_certification_id` FK → `certifications.id`, nullable
  - Index on `(benefit_period_id, occurred_at)` for chronology queries.
- Alembic migration: create table + indexes only. No change to `benefit_periods` schema (the
  `created_by` column already exists; this workstream is what finally populates it).

**API Changes**:
- No new public endpoint required for `CREATED`/`ROLLED` — those already go through
  `POST /api/benefits/...`; the event write is internal to the service call.
- If `CLOSED`/`CORRECTED`/`REOPENED` are to be exposed (currently no such endpoint exists at all — this
  is a real gap, not just an audit gap), each needs a new authenticated endpoint in `app/api/benefits.py`
  that (a) performs the state change and (b) writes the event, in one transaction. Scoping a full
  correction workflow is a judgment call for the assigned engineer; the minimum viable version only needs
  the endpoint to require `reason` and record `actor_user_id` from the authenticated session.

**Backend Changes**:
- `app/services/benefit_period_service.py::rollover_benefit_period` — add an
  `benefit_period_status_events` insert inside the existing DB transaction, using the
  already-authenticated caller as `actor_user_id`. Existing rollover logic (90/90/60-day computation,
  idempotency checks) is unchanged.
- New helper `record_benefit_period_event(...)` to avoid duplicating insert logic across
  create/rollover/future correction call sites.
- `BenefitPeriod.created_by` populated at the same call sites, from the same actor value used for the
  event row (single source of truth, not two separate places that could drift).

**Frontend Changes**: None required for this workstream in isolation. (Consumed later by Workstream 5's
UI.)

**Migration Strategy**: Additive-only migration (new table, no existing-table alteration beyond the
already-present `created_by` column). Backfill is **not possible** for historical benefit periods created
before this ships — those rows will show `created_by = NULL` and no event history. This must be stated
explicitly in the eventual timeline report (Workstream 5) rather than silently treated as complete
history; it is a known, permanent limitation for pre-existing data, not a bug to be fixed later.

**Testing Strategy**:
- Unit test: creating a benefit period writes exactly one `CREATED` event with correct `new_value`
  snapshot and non-null actor.
- Unit test: rollover writes exactly one `ROLLED` event referencing the correct prior/new period pair.
- Unit test: event insert failure rolls back the entire benefit-period state change (proving the
  existing atomicity guarantee, confirmed correct in Phase 11, extends to the new write).
- Regression test: existing `rollover_benefit_period` idempotency tests (duplicate `start_date` dedup)
  continue to pass unmodified.

**Verification Steps**: Query `benefit_period_status_events` for a test patient after create + one
rollover; confirm two rows, correct `event_type` values, non-null `actor_user_id`, correctly ordered
`occurred_at`.

**Estimated Risk**: Low. Additive schema, no changes to existing benefit-period business logic
(deadline math, idempotency), which was already independently confirmed correct in Phase 11-13.

**Dependencies**: None — this is the first workstream in build order.

---

## Workstream 2 — Eligibility Chronology Layer

**Problem**: No single view exists that reconstructs a patient's Referral → Admission → Election →
Certification → Benefit Period → Recertification sequence in one ordered, attributed timeline. The
underlying facts exist across `Referral`, `AdmissionStatusHistory`, `CertificationStatusEvent`, and (once
Workstream 1 ships) `benefit_period_status_events` — but nothing composes them.

**Current State**: Four independent, un-joined audit sources; no chronology query or service exists.

**Target State**: A single read-only service function returns a chronologically ordered, per-patient
timeline spanning all four sources plus billing-readiness history (Workstream 3).

**Database Changes**: None. This is a read-side composition over existing and Workstream-1/3 tables —
no new tables, no new columns.

**API Changes**: None directly (the read is exposed via Workstream 5's endpoint, not a new one here).

**Backend Changes**:
- New service `app/services/eligibility_chronology_service.py`, function
  `build_patient_chronology(patient_id) -> list[ChronologyEvent]`.
- `ChronologyEvent` shape: `event_type`, `source_table`, `actor`, `timestamp`, `reason`, `evidence_ref`
  (FK/id back to the originating row, so every timeline entry is independently verifiable, not just a
  flattened string).
- Explicitly merges and sorts across: `Referral`, `AdmissionStatusHistory`, `CertificationStatusEvent`,
  `benefit_period_status_events`, `billing_readiness_verdicts` (Workstream 3).
- Rows for areas confirmed out of scope this engagement (Assessment, Transfer, Discharge) are emitted as
  explicit `"not tracked"` placeholders rather than silently omitted — preserving the standing rule of
  never implying completeness that hasn't been verified.

**Frontend Changes**: None in this workstream (consumed by Workstream 5).

**Migration Strategy**: N/A — no schema change.

**Testing Strategy**:
- Unit test with a fixture patient touching all five source tables: assert chronological ordering, no
  dropped events, every event has non-null `actor` and `timestamp` per the Workstream 4 attribution
  guarantee.
- Unit test confirming out-of-scope areas appear as labeled `"not tracked"` entries, not omissions.

**Verification Steps**: Run `build_patient_chronology()` against one real (or realistic fixture) patient
end-to-end and manually confirm the returned sequence matches the actual sequence of events recorded
elsewhere in the system for that patient.

**Estimated Risk**: Low-medium. Pure read/compose logic, but correctness depends on Workstreams 1 and 3
already being in place and populated.

**Dependencies**: Workstream 1 (benefit-period events), Workstream 3 (readiness verdicts).

---

## Workstream 3 — Billing Readiness Persistence

**Problem**: `check_patient_billing_readiness()` in
`app/billing/services/billing_readiness_service.py` is a pure compute-and-return function — confirmed
by direct code read to contain no `db.add`/`db.commit`/insert anywhere. Every call recomputes fresh;
no historical verdict is ever stored. This is the single largest confirmed gap in the entire engagement:
"why was this patient billable on a past date" cannot be answered at all today, only "why is this
patient billable right now."

**Current State**: Function returns `(is_ready: bool, blockers: list)` (or equivalent) computed live,
with no persistence step.

**Target State**: Every evaluation is persisted as an immutable verdict row, queryable by patient and
date, without altering the existing eligibility-rule logic itself (already confirmed correct — this is
not a re-audit of the rules).

**Database Changes**:
- New table `billing_readiness_verdicts`:
  - `id` UUID PK
  - `patient_id` FK, not null, indexed
  - `evaluated_at` timestamptz, not null, indexed
  - `is_ready` boolean, not null
  - `blockers` JSONB, not null (empty array when ready) — the existing computed blocker list, unchanged
  - `benefit_period_id` FK, nullable
  - `certification_id` FK, nullable — the certification the verdict cited, if any (a second
    forward-traceability link, alongside Workstream 1's `related_certification_id`)
  - `triggered_by` enum (`SCHEDULED_CHECK`, `MANUAL_CHECK`, `CLAIM_SUBMISSION_ATTEMPT`)
  - Composite index on `(patient_id, evaluated_at)` to support "most recent verdict as of date X"
    queries efficiently.

**API Changes**: No change to the public contract of any existing readiness-check caller. The function
signature and return value are unchanged; persistence is internal. A new read endpoint
`GET /api/patients/{id}/billing-readiness-history` (or folded into Workstream 5's timeline endpoint) is
the only new surface, and it is additive.

**Backend Changes**:
- `check_patient_billing_readiness()` gains exactly one additional step at the end: insert a
  `billing_readiness_verdicts` row from the value it was already about to return. No branching logic,
  blocker computation, or eligibility rule changes.
- `triggered_by` is passed in by the caller (claim-submission flow passes
  `CLAIM_SUBMISSION_ATTEMPT`; a scheduled job, if one exists or is added, passes `SCHEDULED_CHECK`;
  everything else defaults to `MANUAL_CHECK`).

**Frontend Changes**: None in this workstream (consumed by Workstream 5).

**Migration Strategy**: Additive-only migration. No historical backfill is possible — verdicts before
this ships do not exist and cannot be reconstructed; this must be labeled as a known limitation, the
same posture as Workstream 1's backfill gap.

**Testing Strategy**:
- Unit test: calling `check_patient_billing_readiness()` produces exactly one new
  `billing_readiness_verdicts` row matching the returned value.
- Unit test: the function's return value is byte-for-byte identical before/after this change for a fixed
  input (proving the persistence addition has zero effect on existing callers' behavior).
- Unit test: "most recent verdict as of date X" query returns the correct row when multiple verdicts
  exist for a patient across time.

**Verification Steps**: Trigger a readiness check for a test patient at two different times with
different underlying state (e.g., before/after a certification is finalized); confirm two distinct
verdict rows exist and a date-scoped query returns the correct one for each point in time.

**Estimated Risk**: Low. Strictly additive; the existing, already-correct business logic is not touched,
only wrapped with a persistence step.

**Dependencies**: None — can be built in parallel with Workstream 1.

---

## Workstream 4 — User Attribution

**Problem**: Attribution is inconsistent across the system. `CertificationStatusEvent` and
`AdmissionStatusHistory` already enforce non-null actors; `BenefitPeriod` does not
(`created_by` unpopulated); it is unconfirmed by direct code read whether election-signing captures a
user-attribution field at all.

**Current State**: Actor attribution exists as a real, enforced pattern in two subsystems
(Certification, Admission) and is absent in one (Benefit Period); election-signing attribution is an
open question, not yet resolved by code read.

**Target State**: Every new event/verdict table introduced by this epic enforces non-null actor
attribution at the schema level (not just application-layer convention), and the election-signing
question is resolved as a confirmed fact, not an assumption, before this workstream is called complete.

**Database Changes**: No new table of its own — this workstream is the `NOT NULL` constraint on
`actor_user_id` (Workstream 1) and, if the election-signing gap is confirmed real by the code read
below, whatever minimal column addition that specific finding requires (undetermined until the read is
done — this document does not pre-guess that outcome).

**API Changes**: None beyond what Workstreams 1 and 3 already specify.

**Backend Changes**:
- Enforce `NOT NULL` on `actor_user_id` in Workstream 1's and Workstream 3's migrations (already
  specified above — this workstream is the cross-cutting requirement that makes those non-negotiable,
  not a separate code change).
- **First task, before any schema work in this workstream begins**: a direct code read of the
  election-signing path (wherever `ElectionAddendumRequest`/election-statement signing is recorded) to
  determine whether a user-attribution field exists. Document the finding with a file:line citation. If
  missing, scope the minimal column/constraint addition as a follow-on task within this same workstream
  rather than a new one.

**Frontend Changes**: None, unless the election-signing read reveals a missing UI capture point (a
follow-on task, not assumed here).

**Migration Strategy**: Same as Workstreams 1/3 — additive constraints on new tables; any
election-signing fix (if needed) would be a separate, small additive migration scoped after the code
read.

**Testing Strategy**:
- Attempt to insert a `benefit_period_status_events` or `billing_readiness_verdicts` row with a null
  actor in a test; confirm the database constraint rejects it (not just an application-layer check that
  could be bypassed).
- If an election-signing fix is scoped: a test asserting the new field is populated on every signing
  call path.

**Verification Steps**: Attempted-null-insert test above, run against the actual schema, not mocked.

**Estimated Risk**: Low for the enforced-constraint portion (deterministic). Unknown-but-likely-small
for the election-signing portion until the code read happens — this is the one workstream in this plan
where the exact scope is not yet fully known, by design, since guessing at it would violate the
engagement's evidence-only standard.

**Dependencies**: Workstream 1 and Workstream 3 migrations (for the constraint enforcement); none for
the election-signing code read, which can happen immediately and in parallel with everything else.

---

## Workstream 5 — Eligibility Timeline Report

**Problem**: Even once Workstreams 1-4 exist, there is no consumer-facing surface — a case manager,
biller, compliance officer, or counsel responding to a records request has no way to actually see the
reconstructed chronology; it would otherwise exist only as rows in tables.

**Current State**: No such endpoint or UI exists.

**Target State**: A single read-only report, backed directly by Workstream 2's chronology service,
answering all 8 audit questions listed in this document's Purpose section in one view.

**Database Changes**: None — pure presentation layer over Workstream 2's output.

**API Changes**: New endpoint `GET /api/patients/{id}/eligibility-timeline`, returning
`build_patient_chronology(patient_id)`'s output plus a summary block directly answering questions 1-7
(most recent readiness verdict + reason, most recent certification, most recent benefit period, most
recent claim/payment reference) so the report doesn't require the reader to manually scan the full
timeline for the headline answers.

**Backend Changes**: Thin controller/route wiring only; no new business logic beyond what Workstream 2
already computes.

**Frontend Changes**: New read-only timeline view (page or panel) rendering the endpoint's output —
ordered event list plus the summary block. No write/edit capability in this view; it is a report, not an
editor, consistent with this epic's read-only, audit-trail focus.

**Migration Strategy**: N/A.

**Testing Strategy**:
- Endpoint integration test: for a fixture patient with full Referral→Payment history, response includes
  every expected event and a correctly populated summary block.
- Endpoint test: for a patient missing data in an out-of-scope area (Assessment/Transfer/Discharge),
  response labels those as `"not tracked"`, not silently absent.
- Frontend smoke test: timeline view renders without error for both a complete and a partial fixture
  patient.

**Verification Steps**: Re-run the Phase 43 (`cms_audit_simulation.md`) and Phase 44
(`cdph_survey_simulation.md`) walkthroughs against this endpoint's actual output once implemented, to
confirm the previously-PARTIAL verdicts genuinely improve rather than merely being asserted to.

**Estimated Risk**: Low. Presentation layer only; all underlying correctness risk lives in Workstreams
1-4.

**Dependencies**: Workstream 2 (chronology service), which itself depends on Workstreams 1 and 3.

---

## Workstream 6 — Certification → BenefitPeriod → Claim Linkage

**Problem**: The one confirmed missing causal link in the entire chain (Phase 54): a benefit period
cannot show which certification, if any, was checked and satisfied *at the moment it was created*.
`Certification.benefit_period_id` only supports a reverse lookup (which certifications reference this
period), never a forward one (this period exists *because of* certification X). Claim already carries a
foreign key relationship to the patient/benefit period context but has its own separate, pre-existing,
already-documented gap (2 of 3 `Claim.status` writers unaudited) that is out of scope here — this
workstream closes the certification→benefit-period link only, and wires the claim side up to what
Workstreams 1 and 3 already produce rather than re-opening claim-status auditing.

**Current State**: No forward link exists from Certification to the BenefitPeriod it authorized. Claim
references a patient/benefit-period context but nothing upstream of it carries a certification citation
through to it.

**Target State**: Creating or rolling a benefit period requires (or at minimum records, if a hard
business-rule gate is deferred) which finalized certification, if any, was checked — closing the loop so
a claim can be traced back through benefit period to the specific certification that authorized it,
without inference.

**Database Changes**: No new table — this workstream is the **usage** of
`benefit_period_status_events.related_certification_id` (Workstream 1) and
`billing_readiness_verdicts.certification_id` (Workstream 3), both already specified. The only
additional column this workstream introduces, if the gating check itself is implemented (not just
recorded): none required at the schema level — a gate is application logic reading existing
`certifications` rows, not a new column.

**API Changes**: None new. This workstream changes internal service behavior, not any public contract.

**Backend Changes**:
- `rollover_benefit_period` (and creation path) — before completing, query for the most recent
  `FINALIZED` certification for the patient and pass its id into the Workstream-1 event write as
  `related_certification_id`. Whether this becomes a hard gate (reject the rollover if no finalized
  certification exists) or a soft record (log/record but do not block) is a product decision explicitly
  flagged here as needing sign-off before this workstream starts — this plan documents both options
  rather than silently choosing one, since a hard gate is a behavior change to an already-shipped,
  independently-tested rollover path and must not be assumed.
- `check_patient_billing_readiness()` — when persisting a verdict (Workstream 3), populate
  `certification_id` with whichever certification the readiness computation already inspects (it
  currently checks for a finalized certification as one of its blockers — this workstream captures which
  one, since that lookup already happens, just isn't retained today).

**Frontend Changes**: Workstream 5's timeline/summary view surfaces the linkage once populated — no
separate UI work beyond that.

**Migration Strategy**: No schema migration of its own; depends entirely on Workstreams 1 and 3's
already-specified columns.

**Testing Strategy**:
- Unit test: rollover with an existing finalized certification populates
  `related_certification_id` correctly.
- Unit test (if hard gate is chosen): rollover without a finalized certification is rejected with a
  clear error, and existing rollover tests are updated to supply one, confirming no regression to
  already-passing rollover behavior for the normal case.
- Unit test: a readiness verdict's `certification_id` matches the certification the blocker-check logic
  actually evaluated.
- Integration test: given Certification → BenefitPeriod → Claim for one fixture patient, confirm the
  chain is traceable via a single join, with no inference step.

**Verification Steps**: Re-run the Phase 54 (`certification_to_payment_chain.md`) trace manually against
the new data after implementation; confirm the previously-identified "requires inference" step is now a
direct query.

**Estimated Risk**: Medium. This is the one workstream with a real product/business-rule decision (hard
gate vs. soft record) that must be made explicitly, not inferred by the engineer — the wrong default
could either silently change existing rollover behavior (if a hard gate is added without sign-off) or
leave the causal gap only partially closed (if only recorded, never enforced).

**Dependencies**: Workstream 1 (event table + `related_certification_id` column),
Workstream 3 (`certification_id` column). Should be built after both, not in parallel.

---

## Implementation Order

1. Workstream 1 — BenefitPeriod Audit Trail
2. Workstream 3 — Billing Readiness Persistence *(parallel with 1 — no shared dependency)*
3. Workstream 4 — User Attribution *(constraint enforcement piggybacks on 1/3's migrations; the
   election-signing code read happens in parallel with everything above)*
4. Workstream 6 — Certification → BenefitPeriod → Claim Linkage *(requires 1 and 3 to exist first)*
5. Workstream 2 — Eligibility Chronology Layer *(requires 1, 3, and ideally 6 for full linkage)*
6. Workstream 5 — Eligibility Timeline Report *(requires 2)*

## Sprint Breakdown (assuming one engineer, ~2-week sprints; adjust for actual team size)

- **Sprint 1**: Workstream 1 (schema + service integration + tests) and Workstream 3 (schema + service
  integration + tests) in parallel; Workstream 4's election-signing code read as a same-sprint side task.
- **Sprint 2**: Workstream 4's constraint enforcement (folded into Sprint 1's migrations in practice, but
  called out separately here for tracking) plus Workstream 6 (requires product sign-off on hard-gate vs.
  soft-record before this sprint starts — flag this decision to the product owner at the end of Sprint 1
  so it isn't a blocker at the start of Sprint 2).
- **Sprint 3**: Workstream 2 (chronology composition service + tests).
- **Sprint 4**: Workstream 5 (report endpoint + frontend view + re-run of Phase 43/44 simulations against
  real output).

## Dependencies (summary graph)

```
Workstream 1 ─┬─> Workstream 6 ─┐
Workstream 3 ─┘                 ├─> Workstream 2 ─> Workstream 5
Workstream 4 (constraints ride on 1 & 3; code-read task is independent)
```

## Recommended First PR

**Workstream 1 (BenefitPeriod Audit Trail) alone**, scoped to: the `benefit_period_status_events`
migration, the `record_benefit_period_event` helper, wiring it into `rollover_benefit_period` and the
create path, `created_by` backfill-at-write-time, and the unit tests specified above. Rationale: it is
the single highest-value, lowest-risk, fully independent unit of work — it closes the most-cited Audit
Gap on its own, requires no product decision (unlike Workstream 6), and every other workstream either
depends on it or can proceed in parallel without blocking on it.

---

## Non-Goals (restated)

This plan does not add or modify any certification/recertification business rule, does not add any
AI-generated recommendation or prediction, does not change claim-status-writer auditing or
remittance/payment logic (separate, already-documented, out-of-scope gaps), and does not implement the
election-addendum-2026 transition (tracked separately in `election_addendum_transition_plan.md`).

No production code has been written against this document. Further review, research, or compliance
documentation is not planned unless implementation of one of the above workstreams reveals a genuine
blocker.
