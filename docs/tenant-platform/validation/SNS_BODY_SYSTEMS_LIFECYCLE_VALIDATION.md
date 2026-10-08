# SNS Body Systems Lifecycle Validation

**Document type:** Analysis / validation artifact. **NOT an
implementation specification.** No code tasks, no schema changes, no
architecture recommendations are made by this document.

**Status:** DISCOVERY ONLY. CODE: NOT AUTHORIZED. SCHEMA: NOT AUTHORIZED.

---

## Current Repository Evidence

Models: `backend/app/models/body_systems.py`
(`BodySystemsAssessment`, `SystemAssessment`, `ReviewException`).
Routes: `backend/app/api/routes/body_systems.py`
(`GET`/`PUT /patients/{patient_id}/respiratory` only).

### Are Body Systems drafts?

Yes, exclusively. Every `BodySystemsAssessment` row that can currently
be created has `status="draft"` (`body_systems.py:90-116`,
`_get_or_create_current_assessment`), and no code path in the
repository ever changes that value. The schema's `status` column is
CHECK-constrained to allow a `"signed"` value (per
`backend/app/models/body_systems.py`), and the fetch query already
excludes signed rows (`WHERE status != "signed"`) in anticipation of a
signed state existing — but nothing produces one.

### Can Body Systems be finalized?

**No.** No endpoint, service function, or code path sets any
finalization-equivalent flag (there is no `is_finalized` column on
`BodySystemsAssessment`, unlike `IDGReview.is_finalized`).

### Can Body Systems be signed?

**No.** A direct search for any assignment of
`BodySystemsAssessment.status = "signed"` (or equivalent) across the
entire backend returned zero matches. `signed_at`/`signed_by` columns
exist on the model but are never written. There is no `POST
/sign`-equivalent route for Body Systems, unlike the bereavement family
(`POST /{id}/sign`) or CTI (`PENDING_SIGNATURE → FINALIZED`
transition).

### Can Body Systems be corrected?

**No dedicated mechanism exists.** No `BodySystemsAmendment` model, no
`BodySystemsCorrection` model, and no code links `BodySystemsAssessment`
or `SystemAssessment` rows to the generic `RecordVersion` table or to
`PatientDisciplineServiceEvent`. The existing `ReviewException` model
(`body_systems.py`) is a CHECK-constrained `system`/`type`/
`blocking_level`/`status` record **scoped to the Respiratory clinical
review workflow itself** (flagging a limitation/exception during
documentation) — it is not a correction-to-a-signed-record mechanism,
and nothing could be corrected today since nothing can be signed.

### Can Body Systems participate in QA?

**No.** No QA model exists anywhere in the repository (see
`SNS_QA_WORKFLOW_VALIDATION.md`), and Body Systems has no finalized
state for a QA step to act upon even if one existed.

### Can Body Systems participate in Recertification workflows?

**No evidence of any linkage.** `BodySystemsAssessment` has FKs only to
`tenant_id`, `patient_id`, and `visit_id` (nullable) — no
`admission_id` (unlike `RnicaAssessment`, which has `admission_id` to
scope the one-per-admission rule), no `benefit_period_id` (unlike
`Certification`), and no FK to the general `Assessment` model. A direct
search of `backend/app/services/recert_f2f_tasks.py`,
`services/recertification_evidence_synthesis.py`, and
`services/benefit_period_service.py` found no reference to
`body_systems` or `BodySystemsAssessment` in this pass — **NOT
VERIFIED exhaustively**, but no positive evidence of linkage was found.

## Observed Behavior Summary

| Question | Answer | Evidence |
|---|---|---|
| Are Body Systems drafts? | Yes, always | Every row created with `status="draft"`; no transition exists |
| Can Body Systems be finalized? | No | No `is_finalized`-equivalent field or logic |
| Can Body Systems be signed? | No | Zero code matches setting `status="signed"`; schema supports it, code does not use it |
| Can Body Systems be corrected? | No | No amendment/correction model references `BodySystemsAssessment` |
| Can Body Systems participate in QA? | No | No QA model exists system-wide; nothing to review even if one did |
| Can Body Systems participate in Recertification? | No evidence found | No FK to `admission_id`, `benefit_period_id`, or the general `Assessment` model |

## Expected SNS Workflow

Not established by repository evidence. No design document found in
this repository (across the current branch or any of the other 11
worktrees searched) that specifies an intended Body Systems lifecycle
beyond its current perpetual-draft, single-system (Respiratory) proof-
of-pattern scope. This is recorded as an open product question, not
answered here.

## Validation Questions (restated, with direct answers)

1. Are Body Systems drafts? — Yes, exclusively, today.
2. Can Body Systems be finalized? — No code path exists.
3. Can Body Systems be signed? — No code path exists; schema is ready.
4. Can Body Systems be corrected? — No mechanism exists; nothing to
   correct yet since nothing can be signed.
5. Can Body Systems participate in QA? — No; no QA mechanism exists
   system-wide, and Body Systems has nothing a QA step could act on.
6. Can Body Systems participate in Recertification workflows? — No
   evidence of any linkage found in this pass.

## Open Decisions

1. Should Body Systems reuse the bereavement/CTI sign-endpoint pattern,
   the `IDGReview.is_finalized` pattern, or a new pattern, if/when
   finalization is authorized?
2. Should Body Systems adopt RNICA's `admission_id`-scoped
   one-per-admission convention, or remain patient-scoped only (its
   current, narrower convention)?
3. If a correction/amendment mechanism is added, should it reuse
   `RnicaAmendment`'s structure (snapshot + proposed value + decision)
   or a new Body-Systems-specific model?
4. Should Body Systems link to `benefit_period_id` or the general
   `Assessment` model to participate in recertification workflows, and
   if so, which relationship (`Patient → Assessment → Body Systems` vs.
   the current direct `Patient → Body Systems`)?

## Repository Files Reviewed

- `backend/app/models/body_systems.py`
- `backend/app/api/routes/body_systems.py`
- `backend/app/models/idg_review.py`
- `backend/app/models/rnica_assessment.py`
- `backend/app/models/rnica_amendment.py`
- `backend/app/models/certification.py`
- `backend/app/models/benefit_period.py`
- `backend/app/models/assessment.py`
- `backend/app/services/recert_f2f_tasks.py`
- `backend/app/services/recertification_evidence_synthesis.py`
- `backend/app/services/benefit_period_service.py`
