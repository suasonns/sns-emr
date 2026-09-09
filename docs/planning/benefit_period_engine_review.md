# Benefit Period Engine Review

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

## Correction to the prior pass (stated plainly, not buried)

The immediately-prior document
(`hospice_billing_architecture_review.md`, Phase 3) stated: *"no
rollover/advancement logic was found... only resolving the current
period, not advancing it."* **That was a false negative.** A dedicated
`app/services/benefit_period_service.py` exists, was missed because the
earlier pass only grepped `benefit_period_resolver.py` (a
similarly-named but different file), and contains a real, tested,
production-grade `rollover_benefit_period` function. This document
replaces that earlier conclusion with verified evidence, including
re-running the existing guardrail test suite to confirm current
behavior rather than trusting the earlier read.

**Confirmed by execution this pass**:
`backend/tests/guardrails/test_benefit_period_rollover_guardrails.py`
— 4/4 tests passing (`test_first_benefit_period_creation`,
`test_rollover_to_next_benefit_period`,
`test_repeat_call_does_not_create_extra_benefit_period`,
`test_only_one_current_benefit_period_remains_after_rollover`), run via
`python scripts/run_isolated_tests.py -- tests/guardrails/test_benefit_period_rollover_guardrails.py -q`
against the real isolated Postgres test DB.

## How is active benefit period determined?

`get_active_benefit_period` (`app/services/benefit_period_resolver.py`):
a deterministic SQL resolver — `start_date <= as_of_date AND (end_date
IS NULL OR end_date >= as_of_date)`, tenant-scoped via a join to
`patients`, raises `ValueError` if more than one active period is found
(an integrity guard, not just a query), and degrades gracefully (returns
`None` without aborting the transaction) if the DB role lacks SELECT
permission. This is genuinely enterprise-grade defensive code.

## How is next benefit period determined?

`rollover_benefit_period` (`app/services/benefit_period_service.py`):
- Locks all `BenefitPeriod` rows for the patient (`with_for_update`) —
  prevents concurrent double-rollover.
- **Idempotency check**: if a row already exists with the same
  `start_date`/`benefit_type`/`tenant_id`/`patient_id`, returns that row
  instead of creating a duplicate — confirmed by
  `test_repeat_call_does_not_create_extra_benefit_period`.
- **Chronology validation**: rejects a `start_date` earlier than the
  current BP's `start_date`.
- **Period number**: computed as `max(existing period_number) + 1`, or
  `1` if none exist.
- **CMS-correct period lengths**: `_cms_benefit_period_length_days` —
  BP1/BP2 = 90 days, BP3+ = 60 days, matching real CMS hospice election
  period rules, not an arbitrary/placeholder number.
- **Closes the old current BP** (`is_current = False`, and backfills
  `end_date = start_date - 1 day` if it wasn't already set) before
  creating the new one — confirmed by
  `test_only_one_current_benefit_period_remains_after_rollover`.
- Runs inside a single DB transaction, rolls back on any exception.

## How is recertification linked?

Recertification-due is **not** a separately-stored field — it is
computed as `BenefitPeriod.end_date` for the current period, surfaced in
`PocCertificationPage.tsx` (already confirmed in the prior pass). The
rollover engine itself does not push/notify anyone that recert is due;
it only creates the next period once called.

## How is period advancement triggered?

**Manually, via `POST /benefits/`** (`rollover_benefit_period_endpoint`,
`app/api/benefits.py`), role-gated to `RN`/`Administrator`. **No
frontend caller was found** — `sns-emr-frontend/src/api/benefitPeriods.ts`
only implements the GET (list) call; no `rolloverBenefitPeriod`/
`createBenefitPeriod` function exists anywhere in
`sns-emr-frontend/src`. **No scheduled/background job** was found that
calls this function automatically either (no cron, no Celery-beat-style
task, no matches for `rollover_benefit_period` outside the two files
already named). **Classification: BACKEND ONLY, correctly implemented,
not operationally reachable by any user or automatic process.**

## How is benefit-period history preserved?

By construction: old periods are **closed, not deleted**
(`is_current = False`, `end_date` set) and remain in the same
`BenefitPeriod` table with their own `period_number`. A full,
reconstructable history exists in the data. **No dedicated "benefit
period history" screen was found this pass** — the read-side API
(`GET /benefits/patients/{id}` / `benefitPeriods.ts`'s `list`) returns
all periods for a patient (not filtered to current-only), so the raw
data for a history view is already exposed; whether any current screen
renders it as a *history timeline* (as opposed to just the active one)
was not confirmed.

## How is rollover audited?

**Not via a dedicated audit event.** `rollover_benefit_period` does not
call `append_audit_event`/`build_audit_event` (confirmed by direct read
of the function body — no such import or call exists in
`benefit_period_service.py`). The only "trail" is the row history itself
(who created a `BenefitPeriod` row is not separately captured — no
`created_by`/actor field was populated by this function, though the
`BenefitPeriod` model does have a `created_by` column present per the
Section 9 map in the master doc). **Gap**: no explicit
who/when/why-changed audit trail exists for benefit-period rollover,
consistent with the pattern already found for two of the three
Claim.status writers.

## What creates a new benefit period?

Only `rollover_benefit_period`, only reachable via `POST /benefits/`.
No other writer of `BenefitPeriod` rows was found this pass (not
re-verified via a fresh repo-wide grep for `BenefitPeriod(` beyond the
two files already identified — treated as sufficient given the narrow,
specific question asked).

## What ends a benefit period?

Only the rollover function itself, as a side effect of creating the
*next* one (it closes the *previous* current period). **There is no
independent "end/close a benefit period" action** that doesn't also
require creating a new one — meaning a benefit period cannot be closed
out (e.g., for a discharge with no recertification) without also
supplying a next-period `start_date`/`election_date`/`benefit_type`.
Whether discharge has its own closing path was not confirmed this pass
(carried forward as the same open "discharge → billing closure" item
noted in earlier phases).

## What triggers recertification?

Nothing in the code *triggers* it automatically — it is surfaced
passively via the 14-day-window display on `PocCertificationPage.tsx`.
Recertification itself (the clinical act of re-certifying) is a
separate, not-re-verified-this-pass process; this document only
confirms that the *benefit period the recert would attach to* can be
created via the rollover engine.

## Can a period exist without certification?

**YES — nothing in `rollover_benefit_period` or its endpoint checks for
an existing/finalized certification before creating a period.** This is
a real, confirmed gap: the billing-*readiness* check
(`check_patient_billing_readiness`) enforces certification as a
prerequisite for being marked billing-ready, but that is a separate,
independently-invoked check — it is not wired as a precondition to
calling `rollover_benefit_period` itself. A benefit period could be
created today with no certification on file; it would simply then fail
the (separate) billing-readiness check afterward.

## Can a period exist without election?

**Functionally no, but only because `election_date` is a required
parameter, not because anything validates it represents a real
election.** Since there is no separate `Election` entity (confirmed in
the prior pass), "election" here means nothing more than "a date value
was supplied to this function call." Nothing cross-checks that value
against any other election-related record (because none exists).

## Direct answers to the three required questions

**"What benefit period is this patient currently in?" — Can SNS answer?
YES.** Source: `get_active_benefit_period`
(`app/services/benefit_period_resolver.py`), a real, tenant-scoped,
integrity-checked SQL resolver.

**"When is recertification due?" — Can SNS answer? YES.** Source:
`BenefitPeriod.end_date` of the current period, surfaced in
`PocCertificationPage.tsx` (already confirmed in the prior pass).

**"What benefit period comes next?" — Can SNS answer?**

This is the one place this document must correct itself mid-review:
**the engine that computes and creates the next period is real, tested,
and correct** (`rollover_benefit_period`). But "can SNS answer" in the
sense the question implies — *can a hospice administrator ask this and
get an answer from the running system* — is **still effectively NO in
practice**, because:
1. There is no frontend control that invokes it.
2. There is no read-only "preview the next period" query — the function
   only *creates* the next period; it does not expose a side-effect-free
   "what would the next period look like" answer.

**Revised priority, replacing the prior pass's "no rollover logic
exists" framing**: this is **not** a build-the-engine problem anymore —
the engine is done and correct. It is a **UI/operational-exposure
problem**, the same category as several other findings in this review
(835 upload, enforced claim-status endpoint). The Priority #1 development
item is therefore: **expose `rollover_benefit_period` (and ideally a
read-only "preview next period" variant) to a real screen**, not
rebuild the underlying logic.

**Superseded by Phase 9/10 findings**: the certification-gating review
(`certification_gated_eligibility_review.md`, `eligibility_integrity_review.md`)
found a more fundamental gap upstream of the UI-exposure problem above:
the function itself performs zero certification/recertification
validation, so even a correctly-built UI would still let a user create a
period with no valid certification behind it. UI exposure remains
necessary but is no longer Priority #1 in isolation — see
`eligibility_integrity_review.md` for the current top priority.

## Phase 12/13 addendum (2026-09-08) — protections, failure handling, audit trail

Status: verification only, no code changed. Directly answers the directive's Phase 12 (Benefit
Period Protections) and Phase 13 (Audit Trail Review) questions.

### Missing protections (confirmed by re-reading `rollover_benefit_period`, `benefit_period_service.py:38-172`)
- **Certification gating**: missing (see `eligibility_integrity_review.md` Q1/Q2).
- **Recert gating**: missing (same).
- **Audit logging**: missing — no `append_audit_event`/`build_audit_event` call in this file;
  `BenefitPeriod.created_by` is never populated by the `BenefitPeriod(...)` constructor call (no
  `created_by=` kwarg passed).
- **Administrative overrides**: none exist because there is nothing to override — since there is no
  gate, there is no override path, and no `PUT`/`PATCH`/`DELETE` endpoint exists for benefit periods
  at all (`app/api/benefits.py` defines only `GET /patients/{id}` and `POST /`). "Period Updated,"
  "Period Corrected," and "Period Deleted" are not currently possible operations in this codebase —
  they do not merely lack an audit trail, they do not exist as code paths.
- **Rollback behavior**: present and correct — the entire function body is wrapped in a single
  `try`/`except Exception: db.rollback(); raise` block, with one `db.commit()` at the very end. This
  means partial creation is not possible: either the old-BP close + new-BP create + IDG task seed all
  commit together, or none of them do.
- **Failure handling — direct answers**:
  - Current period preserved on failure? **YES** — `current_bp.is_current = False` is an in-memory
    ORM mutation not flushed/committed until the final `db.commit()`; an exception before that point
    rolls back the whole session, leaving the prior current BP unchanged in the database.
  - Partial creation possible? **NO** — single atomic commit, confirmed by code structure (not
    re-executed this pass beyond the prior segment's 4/4 guardrail-test run, which already exercises
    the happy path; failure-path behavior here is a code-structure conclusion, not a fresh test run).
  - Duplicate periods possible? **Partially** — the idempotency check only matches on an *exact*
    `(start_date, benefit_type, tenant_id, patient_id)` tuple. Two calls with the same `benefit_type`
    but different `start_date` values are **not** deduplicated and will each increment
    `period_number`, creating two rows that are both plausible "next" periods for the same patient.
    This is a real, distinct gap from the certification-gating gap — it is a data-integrity gap, not
    an eligibility gap, and was not previously documented.
  - Audit trail written on failure? **N/A** — none is written on success either (see above), so there
    is nothing to compare for the failure path.

### Audit trail review — per lifecycle action (Phase 13)

| Action | Exists as a code path? | Audit event exists? | User attribution? | Timestamp? |
|---|---|---|---|---|
| Period Created | Yes (`rollover_benefit_period`, `benefit_type` implies INITIAL) | No | No (`created_by` unpopulated) | Only via `BaseModel`'s generic `created_at` column (not action-specific) |
| Period Rolled | Yes (`rollover_benefit_period`, `benefit_type=RECERT`) | No | No | Same as above |
| Period Updated | **No such endpoint exists** | N/A | N/A | N/A |
| Period Corrected | **No such endpoint exists** | N/A | N/A | N/A |
| Period Closed | Implicit only, as a side effect of the *next* rollover setting `is_current=False`/`end_date` on the prior row — not a standalone, directly-callable action | No | No | Only the row's generic `updated_at`, if `BaseModel` provides one (not itself an audit record) |
| Period Deleted | **No such endpoint exists** | N/A | N/A | N/A |

**Can an auditor reconstruct every benefit-period transition for a patient? NO.** Only the current
state of each row is queryable (via `GET /patients/{id}`); there is no event stream, so an auditor
cannot see *when* a period was closed relative to when the next was created, *who* triggered either
action, or reconstruct a chronological narrative beyond what the rows' own `start_date`/`end_date`/
`period_number` values imply. This stands in direct contrast to `Certification`, whose
`CertificationStatusEvent` table (`app/models/certification.py:77-104`) already gives auditors exactly
this reconstruction capability for certification status changes. The benefit-period audit-trail gap is
real but narrower in scope than "no audit trail exists anywhere in the system" — it is specific to
`BenefitPeriod`, and the pattern for fixing it (an append-only status-event table plus population of
`created_by`) already exists elsewhere in the codebase as a working template.
