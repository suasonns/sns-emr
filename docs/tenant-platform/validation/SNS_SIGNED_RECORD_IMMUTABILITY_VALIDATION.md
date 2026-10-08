# SNS Signed Record Immutability Validation

**Document type:** Analysis / validation artifact. **NOT an
implementation specification.** No code tasks, no schema changes, no
architecture recommendations are made by this document.

**Status:** DISCOVERY ONLY. CODE: NOT AUTHORIZED. SCHEMA: NOT AUTHORIZED.

---

## 1. Current Repository Evidence

### What makes a record immutable?

A hand-written guard clause inside the domain's own `PATCH`/update
endpoint, checked against a `status` string column. There is no shared,
generic immutability layer (e.g., no decorator, no ORM-level hook, no
database trigger) enforcing this across models — each route implements
its own check:

```python
# backend/app/api/bereavement.py:247
if assessment.status == "SIGNED":
    raise HTTPException(status_code=409, detail="Assessment is signed and locked; unlock is not yet supported")
```

The same literal pattern repeats at `bereavement_poc.py:356,434` and
`post_death_bereavement.py:481,530`. `Certification` uses a richer,
multi-state version of the same idea: `DRAFT → PENDING_SIGNATURE →
FINALIZED → SUPERSEDED`, where `FINALIZED` is terminal for that row and
further change is represented by creating a **new** certification row
that sets `superseded_by_id`/`superseded_at` on the old one
(`backend/app/models/certification.py`), rather than by unlocking it.

### Current lock behavior

Locking is binary and per-row: `status == "SIGNED"` (or `FINALIZED`)
blocks the one `PATCH` endpoint that was written to check it. No
evidence was found of row-level database locks, triggers, or
constraints enforcing immutability independent of the API layer — if a
different code path (migration script, admin tool, direct DB access)
wrote to a signed row, nothing at the schema level would stop it. This
is an **API-layer convention, not a database-enforced guarantee**.

### Current sign behavior

A dedicated `POST /{id}/sign` (or equivalent) endpoint:
1. Loads the row.
2. Re-checks `status == "SIGNED"` and rejects with `409` if already
   signed (`bereavement.py:264-265`).
3. Validates minimum required fields are present (e.g.,
   `bereavement.py:266-267`: requires `primary_first_name` or
   `no_family` before allowing signature).
4. Sets `status="SIGNED"`, `signed_by=user.user_id`,
   `signed_at=now()`.
5. Writes one `audit_event(action="BEREAVEMENT_ASSESSMENT_SIGNED", ...)`
   row.

**Body Systems has none of this.** `backend/app/api/routes/body_systems.py`
contains only `GET /patients/{id}/respiratory` and
`PUT /patients/{id}/respiratory` (`save_respiratory_draft`). A direct
search for any code setting `BodySystemsAssessment.status = "signed"`
returned **zero matches**. The schema supports a signed state
(`status` CHECK constraint, `signed_at`/`signed_by` columns on
`BodySystemsAssessment` per `backend/app/models/body_systems.py`), and
the read-path query already excludes signed rows
(`_get_or_create_current_assessment`, `body_systems.py:90-116`,
`WHERE status != "signed"`), but no code reaches that state. It is
schema-ready, not implemented.

### Current amendment behavior

A dedicated, actively-used model exists for RNICA specifically:
`backend/app/models/rnica_amendment.py` (`RnicaAmendment`). Key
properties, taken directly from the model and its docstring:

- Attached to an **already-locked (signed)** `rnica_assessments` row via
  `rnica_assessment_id` FK.
- **Never mutates** the original signed `form_data` — the amendment is
  a separate row.
- Lifecycle: `status` = `PENDING → APPROVED | DENIED` (no intermediate
  states; a human reviewer must decide — see
  `AMENDMENT_APPROVAL_ROLES` in `app/api/visits.py`).
- Captures `original_value_snapshot` (point-in-time copy of the prior
  value) and `proposed_value` (the clinician's suggested replacement) —
  the proposed value is **never auto-applied** even on approval.
- Captures `request_source` (`PATIENT | REPRESENTATIVE | STAFF |
  INTERNAL_QA`) — i.e., the model already anticipates a QA-originated
  correction request as one of four sources, though no QA workflow
  currently creates such a row.
- `decision_reason` is required for `DENIED` per the docstring (CDPH
  documentation requirement cited directly in the model).

A separate, narrower `Amendment` model
(`backend/app/models/amendment.py`) exists scoped only to
`clinical_notes` (FK `clinical_note_id`), with `reason`, `content`,
`original_finalized_at` — a simpler, single-purpose version of the same
idea for a different document family.

**No amendment model exists for Body Systems, Bereavement, or the
general `Assessment` model** — only RNICA (via `RnicaAmendment`) and
clinical notes (via `Amendment`) have this mechanism today.

### Current correction behavior

The established repository convention for "corrections" (as distinct
from amendments) is **append-only event rows**, not in-place
correction of a prior value:
`backend/app/models/discipline_service.py`
(`PatientDisciplineServiceEvent`) — a correction is a new row with
`event_type=CORRECTION_RECORDED` and a `corrects_event_id` FK pointing
at the event it corrects. The original event is never updated or
deleted.

A second correction/versioning pattern exists generically:
`backend/app/models/record_version.py` (`RecordVersion`) — a polymorphic
snapshot table (`source_record_type`, `source_record_id`,
`version_number`, `snapshot` JSONB) explicitly documented as a
**fallback** for "compliance-domain records that don't already have a
dedicated version concept" — the docstring explicitly notes Plan of
Care (`plan_of_care_version.py`) and election addenda already have
their own dedicated versioning and do not use this generic table.

### Current addendum behavior

No model or route named "addendum" acting on clinical assessments was
found in this search beyond the `docs/phase2/P2-008-ADDENDUM-WORKFLOW.md`
audit-task checklist (unfilled template, no Findings). `election_addendum_request.py`
exists (`backend/app/billing/models/election_addendum_request.py`) but
is scoped to election/billing addenda, not clinical documentation.

## 2. Observed Behavior Summary

| Capability | Exists today? | Where | Scope |
|---|---|---|---|
| Sign/lock guard | Yes | bereavement family, CTI | Per-domain, hand-written |
| DB-level immutability enforcement | Not found | — | API-layer only |
| Amendment-to-signed-record workflow | Yes | RNICA (`RnicaAmendment`) | RNICA only |
| Amendment-to-signed-record workflow (narrow) | Yes | `clinical_notes` (`Amendment`) | Clinical notes only |
| Append-only correction-as-new-row | Yes | `PatientDisciplineServiceEvent` | Discipline-service events |
| Generic polymorphic versioning | Yes (fallback) | `RecordVersion` | Only where no dedicated version model exists |
| Dedicated addendum workflow (clinical) | Not found | — | — |
| Body Systems: sign/lock | **No** | — | Schema ready, no code path |
| Body Systems: amendment/correction | **No** | — | Not applicable — nothing can be signed yet |

## Validation Questions

1. What makes a record immutable? — Answered above: an API-level
   `status == "SIGNED"` check, not a schema/DB-enforced constraint.
2. Who can modify it? — Determined per-route by role-gated dependencies
   (e.g., `BEREAVEMENT_EDIT_ROLES`, `AMENDMENT_APPROVAL_ROLES`,
   `CTI_SIGNER_ROLES`); no single unified permission model was found
   governing all signed-record modification paths.
3. How are corrections represented? — Append-only new rows referencing
   the event/record they correct (`PatientDisciplineServiceEvent`
   pattern), or generic `RecordVersion` snapshots as fallback.
4. How are amendments represented? — `RnicaAmendment` (RNICA,
   full-featured) or `Amendment` (clinical notes, narrower) — both are
   separate rows referencing the original, never mutating it.
5. How are addenda represented? — No dedicated clinical-addendum model
   found; only a billing/election-scoped addendum model exists.

## Open Decisions

1. Should immutability be enforced at the API layer only (current
   convention) or also at the database layer (trigger/constraint)?
2. Should Body Systems reuse `RnicaAmendment`'s pattern, a new
   `BodySystemsAmendment`, the generic `Amendment` model widened in
   scope, or the generic `RecordVersion` fallback — if and when sign/lock
   is implemented for it?
3. Is a single unified permission model for "who can modify a signed
   record" desired, replacing the current per-route role lists?
4. Does SNS intend a dedicated clinical-addendum model distinct from
   amendment/correction, or is the amendment model (`PENDING →
   APPROVED/DENIED`, non-mutating) considered sufficient to also cover
   addenda?

## Repository Files Reviewed

- `backend/app/api/bereavement.py`
- `backend/app/api/bereavement_poc.py`
- `backend/app/api/post_death_bereavement.py`
- `backend/app/models/certification.py`
- `backend/app/models/rnica_amendment.py`
- `backend/app/models/amendment.py`
- `backend/app/models/discipline_service.py`
- `backend/app/models/record_version.py`
- `backend/app/models/plan_of_care_version.py`
- `backend/app/billing/models/election_addendum_request.py`
- `backend/app/models/body_systems.py`
- `backend/app/api/routes/body_systems.py`
- `docs/phase2/P2-008-ADDENDUM-WORKFLOW.md`
