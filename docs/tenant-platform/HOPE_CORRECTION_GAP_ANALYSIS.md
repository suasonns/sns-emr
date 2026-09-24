# HOPE Correction Gap Analysis

**Document Status:** ARCHITECTURE CORRECTION BASELINE — produced per the
"RNICA / HOPE ARCHITECTURE CORRECTION" directive (2026-09-23). Classified
as an **RNICA DEPENDENCY WORKSTREAM**, not a future enhancement.

## Two disconnected correction concepts exist today

### 1. `RnicaAmendment` — implemented, but this is a **clinical** correction mechanism, not a HOPE submission-correction mechanism

`backend/app/models/rnica_amendment.py` + `backend/app/services/
rnica_amendment_service.py` (`create_amendment`, `list_amendments`,
`approve_amendment`, `deny_amendment`) implement a real, working
correction/addendum workflow for an **already-locked RN ICA assessment**:
category (`CLINICAL_CORRECTION`/`ADDITIONAL_FINDING`/
`DOCUMENTATION_ERROR`/`CLARIFICATION`/`OTHER`), reason code, requested
change, before/after value snapshots, requester source (patient/
representative/staff/QA), and a PENDING → APPROVED/DENIED decision
workflow with a required denial reason. Per its own docstring, an
amendment is **always appended, never overwrites** the signed record.

This is a solid, functioning correction mechanism — but it corrects the
**clinical content** of an RNICA assessment. It has no relationship to a
HOPE submission being rejected by CMS and needing resubmission.

### 2. HOPE submission correction/resubmission — schema exists, zero logic

`RnicaAssessment.hope_correction_required`,
`.hope_corrected_assessment_id` (self-referential FK, with a check
constraint preventing self-reference), and the `supersedes_attempt_id`
field on `RnicaHopeSubmissionAttempt` are all schema-ready to represent
"this HOPE record was rejected and a corrected version supersedes it."
**No service or API populates any of these fields** — confirmed by a
full-tree grep of `backend/app` returning only the model declarations
and their own check constraints.

## Gaps

| Gap | Evidence | Severity |
|---|---|---|
| No connection between `RnicaAmendment` (clinical, implemented) and `hope_correction_required`/`hope_corrected_assessment_id` (submission-level, unimplemented) | Grep of both symbol sets confirms zero cross-references | HIGH |
| A CMS rejection has no defined trigger to create a corrected assessment or set `hope_correction_required` | `hope_rejected_at` itself is never set (see `HOPE_SUBMISSION_GAP_ANALYSIS.md`), so there is no event to react to even if the correction logic existed | CRITICAL (upstream dependency) |
| No UI exists for a HOPE-level correction/resubmission workflow (as opposed to the working `RnicaAmendment` UI, if one exists — not traced in this pass) | Not found in `sns-emr-frontend/src` under a HOPE-correction-specific component name | HIGH |
| `apply_unlock()` blocks unlocking a submitted record with no defined re-entry path (see `HOPE_SUBMISSION_GAP_ANALYSIS.md`), which is the same dead-end from the correction side: even if `hope_correction_required` were set, there is no unlock/correct/resubmit sequence defined | `rnica_hope_workflow_service.py:188-206` | HIGH |

## Required product decision (must precede implementation)

The directive requires this decision to be made explicitly, not
defaulted silently:

- **Option A:** extend `RnicaAmendment` to also serve HOPE-submission
  corrections (add a category or a parallel `HOPE_SUBMISSION_CORRECTION`
  reason, and link it to `hope_corrected_assessment_id`).
- **Option B:** keep `RnicaAmendment` clinical-only, and build a
  dedicated, smaller HOPE-correction workflow scoped only to fields that
  differ from the last submission attempt (using
  `RnicaHopeSubmissionAttempt.supersedes_attempt_id`).

This document does not recommend one option — that is the product
decision the directive requires before any redesign implementation
begins. Recommendation for the redesign-readiness review: default
expectation should favor **Option B** (a dedicated, narrower workflow)
unless the correction is itself a clinical-content correction, in which
case `RnicaAmendment` is the correct mechanism and Option A is
unnecessary — i.e. the real question is "was the rejection a clinical
content problem or a submission/format/administrative problem," and the
correction mechanism should follow that distinction rather than being
unified for convenience.
