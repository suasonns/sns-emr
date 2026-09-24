# HOPE Audit Event Matrix

**Document Status:** DESIGN ONLY — NO IMPLEMENTATION. Produced per the
"RNICA \u2192 HOPE REDESIGN EXECUTION DIRECTIVE" (2026-09-23), Priority 5.
Confirms the finding in `HOPE_AUDIT_GAP_ANALYSIS.md`: no audit pipeline
exists for any HOPE lifecycle event. Reuses the existing, working
`audit_event()` helper (`backend/app/services/audit_events.py`) and
`AuditLog` model — per the directive's own instruction to reuse
existing capacity, this document does not propose a new audit
subsystem.

## Required events (per directive)

Each row below is a distinct, independently emitted audit event tied to
a `HopeProjection`/`HopeValidationResult`/submission-attempt lifecycle
transition (see `HOPE_GENERATION_SERVICE_DESIGN.md`,
`HOPE_VALIDATION_ENGINE.md`, `HOPE_SUBMISSION_LIFECYCLE.md`).

| Event | Emitted by | Actor | Timestamp | Source | Before | After |
|---|---|---|---|---|---|---|
| `GENERATED` | `HopeGenerationService.generate()` | User/system triggering generation (or `SYSTEM` for a future scheduled job) | Generation time | `rnica_assessment_id`, `sfv_requirement_id` (if applicable) | No prior `HopeProjection` (or the prior version, if regenerating) | New `HopeProjection` row (id, version) |
| `VALIDATED` | `HopeValidationService.validate()` on `overall_status == PASSED` or `PASSED_WITH_WARNINGS` | User/system triggering validation | Validation time | `hope_projection_id` | `HopeProjection` with no/prior `HopeValidationResult` | New `HopeValidationResult` (id, `overall_status`, findings summary) |
| `FAILED_VALIDATION` | `HopeValidationService.validate()` on `overall_status == FAILED` | Same | Same | `hope_projection_id` | Same | Same, `overall_status = FAILED`, blocking findings list |
| `EXPORTED` | Export step (successor to today's `HopeReport.jsx`/`ComplianceHopeBoard.jsx` render+print, or the future automated export path) | User/system triggering export | Export time | `hope_projection_id`, export format/target | Projection state prior to export | Export artifact reference (once a real export artifact exists — see `HOPE_EXPORT_GAP_ANALYSIS.md`) |
| `SUBMITTED` | Submission step (extension of existing `apply_submission_update()`, or its `HopeSubmissionAttempt`-based successor per `HOPE_SUBMISSION_LIFECYCLE.md`) | User recording/initiating submission | Submission time | `hope_projection_id`, `submission_attempt_id` | Not-yet-submitted state | `submission_number`, `submitted_at`, `submitted_by` |
| `ACCEPTED` | Submission-result recording step | User recording the CMS response, or a future automated integration | Acceptance time | `submission_attempt_id` | `SUBMITTED` | `ACCEPTED`, `accepted_at` |
| `REJECTED` | Same | Same | Rejection time | `submission_attempt_id` | `SUBMITTED` | `REJECTED`, `rejected_at`, rejection reason payload |
| `CORRECTED` | Correction workflow (see `HOPE_CORRECTION_GAP_ANALYSIS.md`'s Option A/B product decision) | User performing the correction | Correction time | `submission_attempt_id` or `RnicaAmendment` id, depending on which option is chosen | `REJECTED` (or a prior accepted-but-amended record) | New corrected `HopeProjection`/amendment reference |
| `RESUBMITTED` | Submission step, re-invoked after correction | User initiating resubmission | Resubmission time | New `submission_attempt_id`, `supersedes_attempt_id` pointing at the rejected attempt | `CORRECTED` | New `SUBMITTED` attempt, chained via `supersedes_attempt_id` (reusing the existing, currently-dead `RnicaHopeSubmissionAttempt.supersedes_attempt_id` column) |

Each event record captures, per the directive's required fields:

- **actor** — the authenticated user id (or `SYSTEM` for a non-interactive trigger), consistent with `audit_event()`'s existing `user_id`/`role` parameters
- **timestamp** — event time, via `audit_event()`'s existing timestamp handling
- **source** — the entity type/id the event is attached to (`HopeProjection`, `HopeValidationResult`, `HopeSubmissionAttempt`), consistent with `audit_event()`'s existing `entity_type`/`entity_id` parameters
- **before** — prior state snapshot (or null for the first event in a chain), stored in `audit_event()`'s existing `meta` JSONB parameter
- **after** — new state snapshot, same `meta` parameter

No new column families or tables are required for the audit trail
itself — `AuditLog`'s existing schema-drift-safe shape
(`action`, `entity_type`, `entity_id`, `user_id`, `role`, `ip_address`,
`tenant_id`, `meta`) already accommodates all nine events above by
varying `action` and populating `meta` with the before/after payload.

## Retrofit into existing endpoints (also required, independent of the new services above)

Per `HOPE_AUDIT_GAP_ANALYSIS.md`, the existing (already-implemented)
HOPE workflow transitions in `rnica_hope_workflow_service.py` and the
SFV completion endpoint in `visits.py` still have **zero** audit calls
today, independent of whether/when the new generation/validation/
submission services above are built. This matrix additionally requires
(as a smaller, independent, immediately actionable item — not gated on
Priorities 3/4/6):

| Existing transition | Proposed `action` value |
|---|---|
| `apply_close()` | `hope.closed` |
| `apply_ready_to_export()` | `hope.ready_to_export` |
| `apply_export_to_batch()` | `hope.exported_to_batch` |
| `apply_submission_update()` | `hope.submission_number_updated` |
| `apply_inactivation()` | `hope.inactivation_toggled` |
| `apply_unlock()` | `hope.unlocked` |
| SFV completion (success) | `sfv.completed` |
| SFV completion (authorization denial) | `sfv.completion_denied` |

This retrofit is independent, low-risk, and does not require the new
`HopeProjection`/`HopeValidationResult` schema — it can be scheduled
ahead of Priorities 3/4/6 if desired, since it only adds calls to an
already-existing helper at already-existing call sites.

## What this document does NOT do

- Does not implement any `audit_event()` call.
- Does not modify `AuditLog`'s schema — none is required.
- Does not decide the exact `meta` payload shape for each event (left
  to implementation, informed by each service's own data model above).

## Dependency

The nine lifecycle events (`GENERATED` through `RESUBMITTED`) depend on
Priorities 3 (generation), 4 (validation), and 6 (submission) existing
first. The **retrofit** of the six existing transitions plus SFV
completion has no such dependency and can proceed independently.
