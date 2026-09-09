# Election Addendum 2026 Gap Review (Phase 28)

Status: verification + research comparison. No production code changed. No billing feature or AI built.

## Current SNS behavior

`app/billing/models/election_addendum_request.py` (`ElectionAddendumRequest`) + `app/api/election_addendum.py`
+ `app/billing/services/election_addendum_service.py` implement a real, non-fabricated tracking system
for the CMS Election Statement Addendum (42 CFR 418.24(b)) — but **only in its on-request form**:

- A `POST /patients/{id}/election-addendum-requests` call is required to start the compliance clock.
  `requested_by` must be one of `PATIENT_OR_REPRESENTATIVE`, `NON_HOSPICE_PROVIDER`, or
  `MEDICARE_CONTRACTOR` — i.e., the system's data model *only represents a request-triggered event*;
  there is no representation of "furnished automatically at election, regardless of request."
- The deadline computed (`compute_addendum_compliance`) is 5 days if requested within the election
  window, 3 days (72 hours) if requested later — this exactly matches the **current, pre-10/1/2026**
  CMS rule.
- If no `ElectionAddendumRequest` row is ever created for a patient, the system has **no record at all**
  that an addendum obligation existed for that election — there is no query, screen, or job that
  proactively flags "this patient elected hospice and no addendum has been furnished."

## Required CMS behavior (effective 10/1/2026)

Every Medicare hospice election must automatically receive a written addendum — itemizing
conditions/services/drugs the hospice has determined are unrelated to the terminal illness — within 5
days of the election's effective date, **regardless of whether anyone requested it**. If the plan of
care changes what is/isn't related, the addendum must be updated and re-furnished within 3 days.

## Effective date

**October 1, 2026.** At the time of this review (2026-09-08), this is approximately **3 weeks away**.

## Affected workflows

- Every new hospice election going forward (not just ones where a request is logged).
- Any existing patient whose election addendum obligation would, under the old rule, have been
  satisfied by "never requested, so no obligation" — under the new rule, silence is not compliance;
  furnishing is mandatory regardless.

## Affected screens

Not independently located/confirmed this pass whether a dedicated UI screen consumes
`GET /patients/{id}/election-addendum-requests` — the API and service layer are confirmed real; the
frontend caller was not searched in this pass (out of scope of the backend-focused evidence gathered
so far). Flagged as an open verification item before implementation, not assumed either way.

## Affected APIs

- `POST /patients/{id}/election-addendum-requests` — would need a new code path (or a modified default
  behavior) that creates a row **automatically at election time**, not only when a request payload is
  submitted.
- `PATCH /patients/{id}/election-addendum-requests/{id}` — delivery-date recording logic is reusable
  as-is; no change needed to this endpoint's shape.
- `compute_addendum_compliance()` — the 5-day/72-hour deadline math is reusable; what changes is *when*
  the row's clock starts (at election, not at request), and that a request should no longer be a
  precondition for the obligation to exist.

## Affected documents

None located that specifically describe the CMS-mandated addendum *content* (which items/services are
unrelated) as a generated artifact — this system tracks the compliance *clock*, not the addendum
*document* itself. Whether SNS generates the actual addendum document/PDF was not investigated this
pass and is a distinct question from the compliance-tracking gap described here.

## Transition strategy (design-only, not implemented)

1. Add an automatic `ElectionAddendumRequest`-equivalent row creation at the point `election_signed_at`
   (or an election-effective event) is recorded, with a new `requested_by` value representing
   "AUTOMATIC_AT_ELECTION" (or treat automatic furnishing as not requiring a `requested_by` at all,
   since post-10/1/2026 no request is the trigger).
2. Preserve the existing on-request path unchanged for any addendum requested *again* later in the
   course of care after a plan-of-care change (the 3-day re-furnish rule continues to apply exactly as
   modeled today).
3. Add a proactive compliance signal (dashboard-style, mirroring the existing `cti_expiring` pattern)
   for "election addendum obligation not yet satisfied within N days of election" so the automatic
   obligation is visibly tracked, not just silently computable after the fact.
4. Confirm/build the actual addendum document-generation path, if it does not already exist elsewhere
   in the codebase (not confirmed either way this pass).

## Risk if unchanged

High. After 10/1/2026, every hospice election that does not have a corresponding automatically-created,
timely-furnished addendum record would represent a documentable compliance failure per election — this
is a per-patient, per-election exposure, not a one-time architectural risk.

## Priority

**0 — ahead of the certification-gating fix**, purely due to the fixed external deadline. Architecture
importance (per the Phase 9/27 findings) still ranks certification-gating as the more structurally
significant gap; this item is prioritized first only because it has a hard, dated compliance trigger
that the certification-gating gap does not.

---

## Most Important Question

**On October 1, 2026, will SNS become non-compliant?**

**PARTIAL.**

Evidence:
- For elections where staff already manually log an `ElectionAddendumRequest` (i.e., a request
  actually occurred), the existing 5-day/72-hour compliance math is already CMS-correct and would
  remain correct after 10/1/2026 — no regression there.
- For elections where no request is logged (which, under the new rule, is now the norm — furnishing is
  automatic, not request-triggered), SNS today has **no record of any obligation at all**, and
  therefore no visibility into whether the (now-mandatory) 5-day furnish deadline was met. This is the
  literal definition of a compliance gap for every such election, not a partial or ambiguous one.
- It is "PARTIAL" rather than an unqualified "YES" because the underlying deadline-math component is
  reusable and correct — the gap is specifically in *triggering* the record automatically, not in the
  compliance calculation itself, and not in every code path (the request-triggered path remains valid).

No production code has changed. No billing feature or AI has been built. This document is a gap
identification and design-only transition strategy, not an implementation.
