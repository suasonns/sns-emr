# SNS QA Workflow Validation

**Document type:** Analysis / validation artifact. **NOT an
implementation specification.** No code tasks, no schema changes, no
architecture recommendations are made by this document.

**Status:** DISCOVERY ONLY. CODE: NOT AUTHORIZED. SCHEMA: NOT AUTHORIZED.

---

## Current Repository Evidence

No dedicated "QA workflow" model, table, or API route was found
anywhere in the repository (all worktrees searched — see the prior
cross-worktree discovery). Specifically:

- No file matching `*qa*.py` exists under any `backend/app/models/`
  across any of the 12 worktrees searched.
- `docs/compliance/SNS_EMR_QAPI_DASHBOARD_ALIGNMENT.md` exists (all
  worktrees) but concerns a **QAPI dashboard** (quality assurance
  performance improvement reporting/metrics), not a per-document QA
  review-and-approval workflow.
- `INTERNAL_QA` appears as one of four permitted values of
  `request_source` on `RnicaAmendment`
  (`backend/app/models/rnica_amendment.py:32`:
  `AMENDMENT_REQUEST_SOURCES = ("PATIENT", "REPRESENTATIVE", "STAFF", "INTERNAL_QA")`)
  — i.e., the amendment model already anticipates that a QA reviewer
  might be the one *requesting* a correction, but no code currently
  creates an `RnicaAmendment` row on QA's behalf; `INTERNAL_QA` is an
  allowed value with no producer.
- `QA_REVIEWER` appears as a **role name** in dev-identity bootstrap
  code (`admin_bootstrap_service.py`, found in an earlier pass this
  session) — confirming a QA *role* exists in the permission model, but
  no route was found that is gated specifically on a QA-review action
  (as opposed to general edit/view roles).
- The closest **implemented** analog to a "review → follow-up →
  correction → closure" loop is `backend/app/models/idg_review.py`
  (`IDGReview` + `IDGReviewAuditEvent`):
  - `is_finalized` / `finalized_by` / `finalized_at` on the review row.
  - `follow_up_required` (bool), `follow_up_status`
    (`ASSIGNED | IN_PROGRESS | COMPLETED`), `follow_up_assigned_to_user_id`,
    `follow_up_due_date`, `closure_summary` (required before status can
    become `COMPLETED`, enforced by a `CheckConstraint`), `reopened_at` /
    `reopen_reason` (required together, also a `CheckConstraint`).
  - A dedicated append-only `IDGReviewAuditEvent` table with an
    enumerated `event_type` CHECK constraint: `IDG_FOLLOW_UP_CREATED`,
    `IDG_RECOMMENDATION_RECORDED`, `FOLLOW_UP_ASSIGNED`,
    `FOLLOW_UP_REASSIGNED`, `FOLLOW_UP_PROGRESS_RECORDED`,
    `PATIENT_RESPONSE_LINKED`, `FOLLOW_UP_COMPLETED`,
    `FOLLOW_UP_REOPENED`.
  - This is scoped to **IDG (interdisciplinary group) review**, not
    labeled or generalized as "QA," and the follow-up loop operates
    **after** `is_finalized`, not as a pre-finalization gate.

No evidence was found of:
- A QA queue/worklist model.
- A "QA finding" or "QA exception" model separate from clinical
  documentation.
- Any rule enforcing that QA review occurs before or after a specific
  document's finalization (because no generic finalization-gated QA
  step exists at all).
- Any enforcement that QA edits are kept separate from clinician
  authorship (there is nothing to enforce, since no QA-write path
  exists).

## Expected SNS Workflow (as described by the requesting product
instruction, not yet verified in the repository)

The instruction describes: note pending QA → QA inconsistency found →
QA follow-up required → clinician correction → QA approval, with QA
never editing clinician documentation directly and clinician remaining
the sole author of record content. This document records that
description as the **candidate** expectation; it is not shown by any
repository evidence to be already implemented, beyond the
IDG-follow-up precedent below.

## Scenario-by-Scenario Evidence

| Scenario | Repository evidence found |
|---|---|
| Note pending QA | No "pending QA" status/flag found on any clinical-document model (`Assessment.status` is `DRAFT`/presumably `SIGNED`; no `PENDING_QA` value observed in any CHECK constraint reviewed) |
| QA inconsistency found | No QA-specific finding/flag model found. `ReviewException` exists on `BodySystemsAssessment`/`SystemAssessment` (`backend/app/models/body_systems.py`) — CHECK-constrained `system`/`type`/`blocking_level`/`status` — but this is authored by/for the clinical review workflow within Body Systems itself, not evidenced as a QA-origination mechanism |
| QA follow-up required | Closest analog: `IDGReview.follow_up_required` / `follow_up_status` (`idg_review.py`) — real, implemented, but IDG-scoped, not QA-labeled |
| Clinician correction (in response to review) | `RnicaAmendment` supports a clinician proposing `proposed_value` against `original_value_snapshot`, decided `APPROVED`/`DENIED` by a reviewer — the closest evidenced "respond to a flagged issue" mechanism, but it is RNICA-only and not tied to any QA trigger today |
| QA approval | No `QA_APPROVED` status or equivalent found anywhere. `RnicaAmendment.status` has `APPROVED`/`DENIED`, decided by `AMENDMENT_APPROVAL_ROLES` (`app/api/visits.py`) — those roles were not individually enumerated in this pass (open item) |

## Validation: QA never edits clinician documentation; clinician remains author; QA findings are separate

Cannot be confirmed as an *enforced* behavior because no QA-write path
exists in the repository to evaluate. By absence, QA cannot currently
edit clinician documentation through any dedicated mechanism (there is
none), which trivially satisfies "QA never edits" only because no QA
workflow exists yet — this should not be read as evidence of an
intentional separation-of-authorship control; it is evidence of an
**absence of QA tooling altogether**.

## Open Decisions

1. Should SNS generalize the `IDGReview` follow-up/closure pattern
   (`is_finalized`, `follow_up_status`, append-only audit event table)
   as the template for a QA workflow, or build something QA-specific?
2. Should QA review be modeled as happening **before** finalization
   (pending-QA gate) or **after** (as IDG follow-up currently does)?
3. Should a QA-originated correction flow through the existing
   `RnicaAmendment`-style request/decision model (already anticipates
   `INTERNAL_QA` as a `request_source`), generalized beyond RNICA?
4. Is `QA_REVIEWER` (existing role) intended to gate a not-yet-built set
   of QA-specific routes, or is it currently vestigial?

## Repository Files Reviewed

- `backend/app/models/idg_review.py`
- `backend/app/models/rnica_amendment.py`
- `backend/app/models/body_systems.py`
- `docs/compliance/SNS_EMR_QAPI_DASHBOARD_ALIGNMENT.md`
- Cross-worktree filename search for `*qa*.py` under `backend/app/models/` (12 worktrees, zero matches)
