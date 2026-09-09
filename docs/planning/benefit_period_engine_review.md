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
