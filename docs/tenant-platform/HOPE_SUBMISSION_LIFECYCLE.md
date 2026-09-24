# HOPE Submission Lifecycle — Architecture

**Document Status:** DESIGN ONLY — NO IMPLEMENTATION. Produced per the
"RNICA \u2192 HOPE REDESIGN EXECUTION DIRECTIVE" (2026-09-23), Priority 6.
Confirms the findings in `HOPE_SUBMISSION_GAP_ANALYSIS.md`: no iQIES
integration exists, the purpose-built `RnicaHopeSubmissionAttempt`
schema has zero writers, and submission tracking today is a single
free-text field. This document designs the full state machine; no code
is written or scheduled by this document.

## States

```
DRAFT ──▶ READY ──▶ VALIDATED ──▶ EXPORTED ──▶ SUBMITTED ──▶ ACCEPTED
                        │                            │
                        │ (validation fails)          │ (CMS rejects)
                        ▼                            ▼
                  FAILED_VALIDATION              REJECTED
                                                       │
                                                       ▼
                                                  CORRECTED ──▶ RESUBMITTED ──▶ ACCEPTED
                                                                                    │
                                                                                    ▼
                                                                                 CLOSED
```

| State | Meaning | Entered from | Exits to |
|---|---|---|---|
| `DRAFT` | A `HopeProjection` exists (per `HOPE_GENERATION_SERVICE_DESIGN.md`) but has not been marked ready | `GENERATED` event | `READY` |
| `READY` | User/workflow has marked the projection as intended for export (mirrors today's `apply_ready_to_export()` semantics, reused not reinvented) | `DRAFT` | `VALIDATED` or `FAILED_VALIDATION` |
| `VALIDATED` | `HopeValidationService` returned `PASSED`/`PASSED_WITH_WARNINGS` (per `HOPE_VALIDATION_ENGINE.md`) | `READY` (via validation run) | `EXPORTED` |
| `FAILED_VALIDATION` | `HopeValidationService` returned `FAILED` — export blocked until re-generation/correction and re-validation | `READY` (via validation run) | `DRAFT` (after correction, triggering regeneration) |
| `EXPORTED` | A concrete export artifact was produced (mirrors today's `apply_export_to_batch()` intent, but only meaningful once a real artifact exists — see `HOPE_EXPORT_GAP_ANALYSIS.md`) | `VALIDATED` | `SUBMITTED` |
| `SUBMITTED` | A `HopeSubmissionAttempt` row was created recording the attempt (reusing the existing, currently-dead `RnicaHopeSubmissionAttempt` schema) | `EXPORTED` | `ACCEPTED` or `REJECTED` |
| `ACCEPTED` | CMS/iQIES accepted the submission (recorded manually today, potentially automated later) | `SUBMITTED` | `CLOSED` |
| `REJECTED` | CMS/iQIES rejected the submission | `SUBMITTED` | `CORRECTED` |
| `CORRECTED` | The correction workflow (per `HOPE_CORRECTION_GAP_ANALYSIS.md`'s Option A/B decision) produced an amended projection | `REJECTED` | `RESUBMITTED` |
| `RESUBMITTED` | A new `HopeSubmissionAttempt` was created with `supersedes_attempt_id` pointing at the rejected attempt | `CORRECTED` | `ACCEPTED` or `REJECTED` (loop) |
| `CLOSED` | Terminal state — mirrors today's `apply_close()` intent, reused once a real accepted submission exists to close against | `ACCEPTED` | (terminal) |

## Mapping to existing (already-built) mechanisms

This state machine is designed to **reuse**, not replace, mechanisms
that already exist:

| Existing mechanism | Role in this state machine |
|---|---|
| `rnica_hope_workflow_service.py::apply_ready_to_export()` | Drives `DRAFT` → `READY` transition |
| `rnica_hope_workflow_service.py::apply_export_to_batch()` | Drives `VALIDATED` → `EXPORTED` transition, once export produces a real artifact |
| `rnica_hope_workflow_service.py::apply_submission_update()` | Becomes the trigger for creating a `HopeSubmissionAttempt` row (currently it instead directly overwrites single-row columns — this is the specific fix called for in `HOPE_SUBMISSION_GAP_ANALYSIS.md`) |
| `RnicaHopeSubmissionAttempt` table (currently dead) | Becomes the backing table for the `SUBMITTED`/`ACCEPTED`/`REJECTED`/`RESUBMITTED` states — its existing `attempt_number`, `receipt_reference`, `validation_status`, `accepted_at`/`rejected_at` (mutually exclusive), `error_payload`/`warning_payload`, `correction_reason`, and `supersedes_attempt_id` columns already model this exact lifecycle and require **no schema change** |
| `rnica_hope_workflow_service.py::apply_close()` | Drives `ACCEPTED` → `CLOSED` transition |
| `rnica_hope_workflow_service.py::apply_unlock()` | Today unconditionally blocks unlocking a submitted record. Under this design, unlock becomes meaningful specifically as the mechanism enabling `REJECTED` → `CORRECTED` (reopening a record for correction after a real rejection) rather than remaining an undefined dead end |
| `RnicaAssessment.hope_validation_status`/`hope_accepted_at`/`hope_rejected_at`/`hope_correction_required`/`hope_corrected_assessment_id` (currently dead columns) | Become fast current-state mirrors of the authoritative `HopeValidationResult`/`HopeSubmissionAttempt` history, analogous to how `hope_closed_by`/`_at` etc. already mirror workflow state today — additive convenience columns, not the source of truth |

## Manual vs. automated submission (explicit open question)

Per `HOPE_SUBMISSION_GAP_ANALYSIS.md`, whether CMS/iQIES submission
becomes an automated API integration or remains a structured
manual-receipt-entry workflow is an **external research question**
(what does iQIES actually expose/require), not something this
repository trace can answer. This state machine is designed to support
**either**:

- **Manual interim:** `SUBMITTED`/`ACCEPTED`/`REJECTED` transitions are
  triggered by a user entering a receipt/result, same as today's
  `apply_submission_update()` but now creating an attempt row instead
  of overwriting single-row columns.
- **Automated future:** the same transitions are triggered by an
  integration layer parsing an iQIES response, with no other change to
  the state machine itself.

This is a deliberate design property (not an oversight) — the state
machine's states/transitions are the same either way; only the trigger
mechanism differs.

## What this document does NOT do

- Does not implement any state transition logic.
- Does not perform the `RnicaHopeSubmissionAttempt`-wiring fix itself
  (that remains a to-be-approved implementation task, tracked in
  `HOPE_SUBMISSION_GAP_ANALYSIS.md`'s "Required before implementation"
  list).
- Does not decide the correction-workflow option (A: extend
  `RnicaAmendment`; B: keep separate) — that remains open per
  `HOPE_CORRECTION_GAP_ANALYSIS.md`.
- Does not perform external CMS/iQIES research.

## Dependency

`EXPORTED`/`SUBMITTED` states depend on Priority 3 (generation) and
Priority 4 (validation) existing first, since a projection must be
generated and validated before it can be exported or submitted. The
`REJECTED` → `CORRECTED` path additionally depends on the correction
Option A/B decision.
