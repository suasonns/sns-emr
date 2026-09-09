# Election Addendum Transition Plan (Phase 36)

Status: verification + design. No production code changed. No billing feature or AI built. This
document consolidates and formalizes `election_addendum_2026_gap_review.md` into the specific
structure requested this phase; it does not re-derive evidence already established there.

## Current rule (in effect today)
Election Statement Addendum furnished only **on request** — 5 days if requested within the first 5
days of election, 3 days (72 hours) if requested later in the course of care (42 CFR 418.24(b), as
implemented today).

## Future rule (effective 10/1/2026)
Addendum furnished **automatically for every election**, within 5 days of the election's effective
date, regardless of request. If the plan of care changes what is/isn't related to the terminal
illness, the addendum must be updated and re-furnished within 3 days.

## Effective date
**October 1, 2026** — approximately 3 weeks from this review (2026-09-08).

## Affected workflows
Every hospice election going forward. Retroactively, any patient currently in an active election with
no addendum-request record on file would, under the new rule's spirit, still need one furnished — CMS
guidance on transition-day handling for already-active elections was not located in this pass and
should be confirmed before implementation (flagged, not assumed).

## Affected APIs
- `POST /patients/{id}/election-addendum-requests` — needs an automatic-trigger path at election time,
  not only a manually-submitted request payload.
- `PATCH /patients/{id}/election-addendum-requests/{id}` — reusable as-is for recording delivery.
- `compute_addendum_compliance()` — deadline math (5-day/72-hour) is reusable as-is; only the trigger
  condition changes.

## Affected forms
Not confirmed whether a dedicated frontend form exists for staff to log addendum requests/deliveries —
the backend API is confirmed real; frontend caller was not located in this pass (flagged as an open
verification item, consistent with the same flag raised in `election_addendum_2026_gap_review.md`).

## Affected database fields
No schema change is strictly required. `ElectionAddendumRequest.requested_by` currently only accepts
`PATIENT_OR_REPRESENTATIVE` / `NON_HOSPICE_PROVIDER` / `MEDICARE_CONTRACTOR` — an automatic-furnish
event does not cleanly fit any of these three values conceptually (none of them represent "the hospice
itself, unprompted"), so a 4th value or a nullable/optional `requested_by` for automatic rows is a
design question to resolve before implementation, not a decision made in this document.

## Affected documents
The actual addendum content/document (which items/services are deemed unrelated) generation path was
not located in this pass — this tracking system manages the compliance *clock*, not the addendum
*artifact* itself. Whether that artifact-generation capability exists elsewhere in the codebase remains
an open question, carried forward from `election_addendum_2026_gap_review.md`.

## Affected reports
No existing report/dashboard widget surfaces addendum compliance status in aggregate (unlike
`cti_expiring`, which has a real dashboard widget). This is a net-new reporting need under the
mandatory rule, since staff will need proactive visibility into "which recent elections have not yet
had an addendum furnished," not just a per-patient lookup.

---

## Question: On 10/1/2026, does SNS become COMPLIANT / PARTIALLY COMPLIANT / NON-COMPLIANT?

**PARTIALLY COMPLIANT.**

Proof:
- For any election where a staff member manually logs an `ElectionAddendumRequest`, the deadline
  computation remains exactly CMS-correct after 10/1/2026 — this code path does not regress.
- For any election where no request is manually logged — which becomes the *default* case once
  furnishing is automatic and no longer request-triggered — SNS has **no record of any obligation at
  all**, and therefore no way to prove the 5-day furnish deadline was met, because nothing establishes
  that the clock ever started. This is a confirmed, direct code-read finding
  (`election_addendum.py`/`election_addendum_request.py`/`election_addendum_service.py`), not an
  inference.
- It is not NON-COMPLIANT outright because the underlying compliance-math component is correct and
  reusable, and any election where staff happen to still log a request (out of habit or manual
  diligence) would remain fully compliant. It is not COMPLIANT because the system provides no
  structural guarantee that every election gets an addendum record — compliance under the new rule
  would depend entirely on manual staff diligence with zero system enforcement, which is not a
  defensible audit posture.

No production code has changed. No billing feature or AI has been built.
