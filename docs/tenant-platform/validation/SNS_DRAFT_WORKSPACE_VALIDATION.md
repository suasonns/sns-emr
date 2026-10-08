# SNS Draft Workspace Validation

**Document type:** Analysis / validation artifact. **NOT an implementation
specification.** This document contains no code tasks, no schema changes,
and no architecture recommendations. It records current repository
behavior against a candidate "Draft Workspace → Finalization → Legal
Record" model so product authority can decide whether that model should
be adopted, and if so, for which document families.

**Status:** DISCOVERY ONLY. CODE: NOT AUTHORIZED. SCHEMA: NOT AUTHORIZED.

---

## 1. Current Repository Evidence

No SNS document family today has a structurally separate "draft
workspace" store distinct from its "legal record" store. In every
clinical-document model found, draft and finalized states are the
**same database row**; only a `status` column (and, once set,
`signed_at`/`signed_by`) distinguishes them.

Confirmed examples:

| Model / Route | Draft representation | Finalize event | File |
|---|---|---|---|
| `BereavementAssessment` | row with `status != "SIGNED"`, freely overwritten via `PATCH` | `POST /{id}/sign` sets `status="SIGNED"`, `signed_by`, `signed_at` | `backend/app/api/bereavement.py:236-285` |
| Bereavement POC | same pattern | same pattern | `backend/app/api/bereavement_poc.py:340-440` |
| Post-Death Bereavement | same pattern | same pattern | `backend/app/api/post_death_bereavement.py:470-535` |
| `Certification` (CTI) | `status="DRAFT"` row | `PENDING_SIGNATURE → FINALIZED`, with `SUPERSEDED` chaining via `superseded_by_id` | `backend/app/models/certification.py`, `backend/app/api/certifications.py` |
| General `Assessment` | `status` column, default `"DRAFT"`, `signed_at`/`signed_by` columns present | No sign endpoint found acting on this model in this search | `backend/app/models/assessment.py:48-52` |
| `BodySystemsAssessment` | `status="draft"` row, re-fetched via `WHERE status != "signed"` | **No endpoint sets `status="signed"` anywhere in the codebase** (confirmed by direct search — zero matches) | `backend/app/models/body_systems.py`, `backend/app/api/routes/body_systems.py:90-116` |

Draft edits in every case examined are **plain in-place field
overwrites** (`_apply_fields(assessment, payload)` in
`bereavement.py:252`) with no diff capture, no version row, and no
audit event. The only audit event observed fires at the **sign** action
(`audit_event(action="BEREAVEMENT_ASSESSMENT_SIGNED", ...)`), not on
each draft save.

No autosave mechanism was located in this search (frontend or backend)
for these document families; this is **NOT VERIFIED** either way and
would require a separate targeted search before being asserted.

## 2. Observed Behavior

- A draft **is** the legal-record row in waiting; there is no copy, no
  promotion, no separate "workspace" table anywhere examined.
- Multiple in-place edits before signing are indistinguishable from each
  other after the fact — no revision history exists for the pre-sign
  period in any model reviewed.
- Once a `status == "SIGNED"` guard trips, further `PATCH` calls are
  rejected with `409 Conflict` (`bereavement.py:247`) — this is the only
  immutability mechanism found, and it is hand-written per route, not a
  shared/generic enforcement layer.
- Body Systems has none of this: no sign action exists, so the
  "finalization" half of the model has not been reached in code for that
  feature at all; every `BodySystemsAssessment` row that can currently
  exist is permanently `status="draft"`.

## 3. Gaps (between current behavior and the candidate Draft Workspace model)

- No separate draft-workspace storage exists anywhere; adopting the
  candidate model would be a new pattern, not an extension of one that
  already exists for any document family.
- No draft-level versioning/audit exists for any of the reviewed
  document families (bereavement, CTI, post-death, Body Systems) —
  only the terminal sign event is audited.
- No autosave behavior was located in this pass (open question, not a
  confirmed gap).
- Body Systems lacks even the single-row draft→signed mechanism that
  bereavement/CTI/post-death already have; it would need that minimal
  mechanism before a draft-workspace discussion is even reachable for
  it specifically.

## 4. Validation Scenarios

For each scenario: "Current behavior" describes what the repository
does today for the closest analogous document family (bereavement/CTI);
"Body Systems" describes what happens for Body Systems specifically
(today: no sign path exists at all, so every scenario below terminates
in "still draft").

| Scenario | Current behavior (bereavement/CTI analogue) | Body Systems today |
|---|---|---|
| Nurse voice dictation captured into a field | Not evidenced in this search — no dictation-specific code path found (NOT VERIFIED) | N/A — not evidenced |
| Rough/incomplete observations saved mid-visit | Plain `PATCH` overwrite while `status != SIGNED`; no flag distinguishes "rough" from "complete" | `PUT /patients/{id}/respiratory` overwrite; no completeness flag |
| Incomplete note left and resumed later | Row persists with whatever fields were last written; no explicit "incomplete" state | Same — row persists as `draft` indefinitely |
| Autosave | Not evidenced (NOT VERIFIED) | Not evidenced (NOT VERIFIED) |
| Rewritten narrative before signing | Overwrites prior value in place; prior value is not retained anywhere | Same — no prior-value retention |
| Clinician changes assessment answers before signing | Same in-place overwrite; no diff/version captured | Same |
| Final signature | `POST /{id}/sign` flips `status`, sets `signed_by/signed_at`, writes one audit event, subsequent edits blocked with `409` | **Does not exist** — no code path can ever set a `BodySystemsAssessment` to `signed` |

## 5. Question: Should drafts be considered part of the legal record?

This document does not answer that question. It records that **today**,
structurally, drafts and legal records are the same row in every model
examined — there is no repository evidence of a separate draft/legal
distinction anywhere in SNS as currently implemented. Whether that
*should* change is a product-authority decision, not something this
analysis resolves.

## Open Decisions

1. Should SNS adopt a structurally separate draft-workspace store, and
   if so, for which document families (all, or only new ones like Body
   Systems)?
2. Should pre-sign edits be versioned/audited, or is sign-time-only
   audit sufficient?
3. Is autosave an existing requirement anywhere in SNS today, and if so,
   where — this document could not locate it and flags it as unresolved.
4. Should the bereavement/CTI draft→sign pattern be treated as the
   reference implementation other families (including Body Systems)
   extend, rather than inventing a new pattern?

## Repository Files Reviewed

- `backend/app/api/bereavement.py`
- `backend/app/api/bereavement_poc.py`
- `backend/app/api/post_death_bereavement.py`
- `backend/app/models/certification.py`
- `backend/app/api/certifications.py`
- `backend/app/models/assessment.py`
- `backend/app/models/body_systems.py`
- `backend/app/api/routes/body_systems.py`
