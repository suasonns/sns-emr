# J2052C Source Discovery

Status: NOT_VERIFIED — no reusable authoritative source found.
Rule in effect: SNS Review Rule (VERIFIED BY CMS / VERIFIED BY REPOSITORY
TRACE / VERIFIED BY PRODUCTION CODE / NOT_VERIFIED / OPEN_QUESTION).
This document does not create, propose, or select a field, table, or
enum. It records the repository search only, per instruction.

## CMS requirement (VERIFIED BY CMS)

J2052C — Reason SFV Not Completed. Required only when J2052A = No.
Allowed codes:
- 1 = Patient/caregiver declined visit
- 2 = Patient unavailable
- 3 = Unable to contact patient/caregiver
- 9 = None of the above

## Search performed

Backend (`backend/app/**`) and frontend (`sns-emr-frontend/src/**`) full-text
search for: declin*, unavailable, unable to contact, refus*, missed visit,
visit outcome, no-show, not home, reason not completed, cancellation/cancel
reason, no_show, missed_appointment, visit_status, appointment_status,
scheduling_status, cancellation_code. Also traced every code path that
writes to `SFVRequirement` (`sfv_requirement.py` model, `hope_phase_b_engine.
complete_sfv_requirement_from_visit`, `visits.py complete_sfv_requirement`)
and every model in the "refusal"/"outcome" family
(`models/refusal.py`, `models/chha_visit_outcome.py`,
`models/chha_visit_task_result.py`).

## Candidate sources found

### 1. `RNICA.jsx` — `reasonNotCompleted` (RNICA trigger form)

| | |
|---|---|
| TABLE | none — client-side RNICA `formData.sfv` JSON only |
| FIELD | `sfv.reasonNotCompleted` |
| UI LOCATION | RNICA.jsx line ~9515, "Symptom Follow-Up Visit" section, `{ type: "input", label: "Reason SFV not completed", path: "reasonNotCompleted" }` |
| API | none — never submitted to any backend endpoint; lives only in the RNICA form's local JSON blob |
| ENUM VALUES | none — free-text `<input>`, no options list, no code set |
| CURRENT USAGE | RNICA self-attestation only; this is the exact source the earlier J2052 directive required removing as the exporter's authoritative source |
| MATCHES CMS? | NO — free text, not restricted to 1/2/3/9 |
| REUSE POSSIBILITY | LOW — architecturally disallowed (RNICA self-attestation, not a completion-visit/backend record) and not CMS-coded |

### 2. `SFVRequirement.status` (backend model)

| | |
|---|---|
| TABLE | `sfv_requirements` |
| FIELD | `status` |
| UI LOCATION | none directly; surfaced read-only via `SfvStatusCard` |
| API | set by `complete_sfv_requirement_from_visit` (→ `COMPLETED`) and by scheduled/overdue logic (→ `OVERDUE`); `CANCELLED` value exists in the check constraint but no code path was found that sets it |
| ENUM VALUES | `OPEN`, `COMPLETED`, `OVERDUE`, `CANCELLED` (DB check constraint) |
| CURRENT USAGE | Requirement lifecycle state, not a documented clinical reason |
| MATCHES CMS? | NO — 4 lifecycle states, not the 4 CMS reason codes; no mapping between `OVERDUE`/`CANCELLED` and `2`/`3`/`9` exists in code or docs |
| REUSE POSSIBILITY | LOW — conflating a workflow-lifecycle enum with a clinical reason code would be an unverified assumption, not a trace |

### 3. `Refusal` model (`backend/app/models/refusal.py`, `services/refusal_engine.py`)

| | |
|---|---|
| TABLE | `refusals` |
| FIELD | `discipline` (required), `reason` (free-text), `refused_at`, `was_reoffered` |
| UI LOCATION | not traced in this pass (out of scope of the SFV/HOPE workflow files searched) |
| API | not traced in this pass |
| ENUM VALUES | none — `reason` is free `Text` |
| CURRENT USAGE | Discipline-level visit refusal tracking (RN/MSW/etc. declining discipline visits generally), scoped by `patient_id` + `discipline`, with no `visit_id`, no `sfv_requirement_id`, and no FK to `visits` at all |
| MATCHES CMS? | NO — no code set, and not linked to a specific visit or SFV requirement |
| REUSE POSSIBILITY | LOW — different entity scope (discipline-level general refusal, not a specific completion-visit-linked SFV record) and no CMS code vocabulary |

### 4. `CHHAVisitOutcome` model (`backend/app/models/chha_visit_outcome.py`)

| | |
|---|---|
| TABLE | `chha_visit_outcomes` |
| FIELD | `reason_for_visit`, `exception_narrative` |
| UI LOCATION | not traced in this pass |
| API | not traced in this pass |
| ENUM VALUES | `reason_for_visit` is free `String(64)`, no fixed code list found |
| CURRENT USAGE | Home Health Aide (CHHA) visit outcome/logistics record, one row per `visit_id` (unique) |
| MATCHES CMS? | NO — CHHA-specific outcome model, not SFV-specific, no CMS J2052C code mapping |
| REUSE POSSIBILITY | LOW — wrong discipline/workflow scope (CHHA aide visits, not RN/LPN SFV visits), no code set |

### 5. SFV completion API (`api/visits.py::complete_sfv_requirement`, `services/hope_phase_b_engine.py::complete_sfv_requirement_from_visit`)

| | |
|---|---|
| TABLE | `sfv_requirements` (write path) |
| FIELD | none — payload (`SfvCompletionRequest`) and function signature only accept `completionVisitId`/`completing_visit_id`, `completing_visit_datetime`, `discipline`, `visit_mode` |
| UI LOCATION | "Complete SFV" action on Visit Notes screen |
| API | `POST /visits/sfv-requirements/{id}/complete` |
| ENUM VALUES | none — no "not completed"/decline path exists in this endpoint at all |
| CURRENT USAGE | Only handles the "SFV was completed" case. There is no corresponding "mark SFV not completed with reason" endpoint anywhere in the codebase (confirmed by trace — no `cancel_sfv_requirement`/`mark_sfv_not_completed` function exists). |
| MATCHES CMS? | NO — the not-completed path does not exist as a backend workflow at all |
| REUSE POSSIBILITY | N/A — nothing to reuse; this confirms the gap is structural, not just a missing UI control |

## Reuse attempts summary

| Candidate | Reuse Possibility |
|---|---|
| RNICA `reasonNotCompleted` (free text) | LOW |
| `SFVRequirement.status` | LOW |
| `Refusal` model | LOW |
| `CHHAVisitOutcome` | LOW |
| SFV completion API | N/A (no not-completed path exists) |

No candidate reaches MEDIUM or HIGH. No existing table, JSON structure,
workflow, or enum captures a CMS-coded (1/2/3/9) "why wasn't the SFV
completed" value tied to a specific `SFVRequirement`.

## Second-pass candidate analysis (source-of-truth question, not storage)

Per the follow-up correction: the question is not "where should this be
stored" but "does an authoritative, clinically appropriate source already
exist." Re-evaluated on that basis:

| Candidate | AUTHORITATIVE | CLINICALLY APPROPRIATE | MATCHES CMS RESPONSE SET | SUPPORTS ALL REQUIRED VALUE STATES | USED IN PRODUCTION WORKFLOW |
|---|---|---|---|---|---|
| RNICA `reasonNotCompleted` free text | NO — self-attestation on the *triggering* form, not the SFV encounter itself; already disqualified as a HOPE export source by the P1A directive | NO — captured at trigger time, before the SFV outcome is even known | NO — free `<input>`, no code restriction at all | NO — no code states exist, just prose | YES (this is the only field a user can currently type into) |
| `SFVRequirement.status` (`OPEN`/`COMPLETED`/`OVERDUE`/`CANCELLED`) | NO — a workflow-lifecycle flag, not a clinical reason a person recorded | NO — no clinician ever asserts "declined" vs "unavailable" vs "unable to contact" through this field; it is system/schedule-derived | NO — 4 lifecycle states do not correspond 1:1 to the 4 CMS reason codes; no mapping exists in code | NO — cannot distinguish code 1 vs 2 vs 3 vs 9 | YES (status is actively used) but not for this purpose |
| `Refusal` model | NO — scoped to `patient_id` + `discipline`, not to a specific `SFVRequirement` or visit | Plausibly, if extended — refusal *is* a clinically meaningful concept — but not proven for this use without a linkage | NO — `reason` is free `Text` | NO | NOT_VERIFIED — usage sites in production were not traced beyond the model file in this pass |
| `CHHAVisitOutcome` | NO — CHHA (home health aide) discipline-specific outcome record, wrong discipline for an RN/LPN/LVN SFV | NO — wrong workflow entirely | NO — `reason_for_visit` is free `String(64)` | NO | YES, but for CHHA visits, not SFV |
| SFV completion API (`complete_sfv_requirement*`) | N/A | N/A | N/A | N/A | The "not completed" branch does not exist as a workflow at all — confirmed by trace, not assumed |

## Finding

**NO AUTHORITATIVE SOURCE FOUND.**

Every candidate fails at least the AUTHORITATIVE and MATCHES-CMS-
RESPONSE-SET tests. This is not a storage-location problem to solve by
picking among these candidates — none of them is a clinically appropriate,
CMS-coded record of *why* a specific SFV was not completed. The gap is
structural: no workflow in the repository today asks a clinician to
record one of the four CMS reason codes at the point an SFV goes
uncompleted.

## Conclusion

J2052C remains **NOT_VERIFIED**. There is no authoritative repository
source to read from — not because a field wasn't wired up, but because
the underlying workflow (recording *why* an SFV was not completed) does
not exist in the backend at all today. The only place this exists is the
RNICA free-text self-attestation field, which is architecturally
disallowed as an export source.

This is escalated below as an OPEN QUESTION. No field, table, enum, or
storage has been created or proposed for selection — per instruction,
only the two structurally distinct options are named for Romel's decision.

---

## OPEN QUESTION — REQUIRES ROMEL DECISION

**KNOWN FACTS**
- CMS requires J2052C only when J2052A = No, restricted to codes 1/2/3/9.
- No backend field, table, or endpoint exists to capture this today.
- The only existing capture point is a free-text field on the RNICA
  trigger form (`reasonNotCompleted`), which is self-attestation at
  trigger time, not a completion-visit/backend record, and is not
  CMS-coded.
- No adjacent workflow (Refusal, CHHAVisitOutcome, SFVRequirement.status)
  captures this in a reusable, CMS-coded, SFV-linked form.

**UNKNOWN FACTS**
- Where, operationally, should a clinician (or scheduler) record that an
  SFV could not be completed and why — on the Visit Notes screen, a
  scheduling/task workflow, or elsewhere?
- Whether this should be captured at all today, or whether J2052C should
  remain unexported (placeholder) until a real capture workflow is built.

**ARCHITECTURAL IMPACT**
Any authoritative fix requires new capture surface (workflow + storage)
since none currently exists — this is not a read-path correction like
J2052A/B, nor a reuse-only fix like J2053.

**OPTION A**
Build a dedicated "SFV not completed" capture workflow (new backend
field/endpoint on `SFVRequirement` + UI), analogous in shape to the J2053
capture-path work, but for the not-completed branch.

**OPTION B**
Leave J2052C unexported (always placeholder) until Option A is approved
and built; document this explicitly as a known HOPE export gap rather
than exporting an unverified value.

**REQUIRES ROMEL DECISION** — no option is selected or implemented here.
