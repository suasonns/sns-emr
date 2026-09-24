# HOPE Submission Gap Analysis

**Document Status:** ARCHITECTURE CORRECTION BASELINE — produced per the
"RNICA / HOPE ARCHITECTURE CORRECTION" directive (2026-09-23). Classified
as an **RNICA DEPENDENCY WORKSTREAM**, not a future enhancement.

## What "submission" currently means in this repository

`apply_submission_update()` (`backend/app/services/
rnica_hope_workflow_service.py:147-171`) accepts a **manually typed
string**, `submission_number`, from a user, and stores it on
`RnicaAssessment.hope_submission_number` along with
`hope_already_submitted=True` / `hope_submitted_at` / `hope_submitted_by`.
That is the entirety of "submission" in this repository today: a text
field the user fills in after (presumably) submitting through some
external, out-of-band process. There is no outbound network call to
iQIES, no receipt parsing, and no automated confirmation of acceptance.

## Confirmed dead schema (submission-lifecycle scaffolding with zero logic)

A full-tree grep of `backend/app` for each of the following names returns
**only their model declaration** — no service, API route, test, or
migration script reads or writes them:

- `RnicaAssessment.hope_validation_status`
- `RnicaAssessment.hope_accepted_at`
- `RnicaAssessment.hope_rejected_at`
- `RnicaAssessment.hope_last_submission_attempt_at`
- The entire `RnicaHopeSubmissionAttempt` table (`backend/app/models/
  rnica_hope_submission_attempt.py`) — a purpose-built child table with
  `attempt_number`, `submission_number`, `receipt_reference`,
  `validation_status`, `accepted_at`/`rejected_at` (mutually exclusive by
  check constraint), `error_payload`/`warning_payload` (JSONB),
  `correction_reason`, and `supersedes_attempt_id` (self-referential FK
  for resubmission chains) — is imported into `app/models/__init__.py`
  but otherwise **never referenced anywhere in the codebase**.

This table's own docstring states it "must never become a second owner
of HOPE workflow/submission status" — i.e. the schema was deliberately
designed in advance of the workflow logic that would populate it. That
logic was never built.

## Gaps

| Gap | Evidence | Severity |
|---|---|---|
| No iQIES API/transport integration exists at all | Repository-wide search for `iQIES`/`iqies` in `backend/app`: no matches | CRITICAL |
| Submission number is free-text, unvalidated, and self-reported by the user | `rnica_hope_workflow_service.py:147-161` (`_normalize_text(submission_number)`, no format check) | HIGH |
| No attempt history is recorded — a second submission silently overwrites `hope_submission_number` with no record of the first attempt | `apply_submission_update()` writes directly to the single-row columns; `RnicaHopeSubmissionAttempt` is unused | HIGH |
| No acceptance/rejection state is ever set, so downstream correction/resubmission logic (see `HOPE_CORRECTION_GAP_ANALYSIS.md`) has no trigger condition to react to | `hope_accepted_at`/`hope_rejected_at` unpopulated | CRITICAL |
| `apply_unlock()` explicitly blocks unlocking a submitted record ("Submitted HOPE records cannot be unlocked") but has no path to permit the correction workflow that would legitimately need to reopen one after a real rejection | `rnica_hope_workflow_service.py:188-206` | HIGH — this is a workflow dead-end: a record marked submitted can only be corrected by manually clearing submission tracking first, per the error message's own instruction, which has no defined procedure |

## Required before implementation

1. Determine the real CMS iQIES submission mechanism (manual portal
   upload vs. API — this is an external research question, not a
   repository-tracing question) and decide whether SNS should build an
   automated transport layer or a structured manual-receipt-entry
   workflow as an interim step.
2. If manual receipt entry remains the near-term approach, upgrade
   `apply_submission_update()` to create a `RnicaHopeSubmissionAttempt`
   row per attempt (using the schema that already exists) instead of
   overwriting single-row columns, so attempt history is preserved.
3. Wire `hope_validation_status`/`hope_accepted_at`/`hope_rejected_at` to
   whatever mechanism records the CMS response (manual entry initially,
   automated later) — these columns should not remain permanently dead.
4. Define the unlock-after-submission-rejection procedure explicitly
   (who can do it, what it changes, what audit trail it produces) rather
   than leaving it as an unimplemented manual workaround implied by an
   error message.
