# J2052C Decision Record

Status: NOT_VERIFIED — no authoritative source found. This record
reformats the completed investigation in `J2052C_SOURCE_DISCOVERY.md`
into the requested decision-record template. No new research was
performed; no schema, storage, API, or enum is designed or proposed here.

## CMS Requirement

J2052C — Reason SFV Not Completed. Required only when J2052A = No.
Codes: 1 = Patient/caregiver declined visit, 2 = Patient unavailable,
3 = Unable to contact patient/caregiver, 9 = None of the above.

## Candidate Sources Evaluated

| CANDIDATE SOURCE | CURRENT WORKFLOW | REPOSITORY EVIDENCE | MATCHES CMS | REUSE POSSIBLE |
|---|---|---|---|---|
| `RNICA.jsx` `sfv.reasonNotCompleted` | Free-text input on the RNICA trigger form's "Symptom Follow-Up Visit" section (line ~9515). Never submitted to any backend endpoint — lives only in the RNICA form's local JSON blob. | `RNICA.jsx` line ~9515: `{ type: "input", label: "Reason SFV not completed", path: "reasonNotCompleted" }` | NO — free text, not restricted to codes 1/2/3/9 | NO — architecturally disallowed (RNICA self-attestation at trigger time, not a completion-visit/backend record) |
| `SFVRequirement.status` | Requirement lifecycle state (`OPEN`/`COMPLETED`/`OVERDUE`/`CANCELLED`), set by `complete_sfv_requirement_from_visit` and scheduled/overdue logic | `sfv_requirement.py` model, DB check constraint | NO — 4 lifecycle states, no mapping to CMS reason codes 1/2/3/9 exists in code | NO — conflates a workflow-lifecycle enum with a clinical reason code |
| `Refusal` model | Discipline-level visit refusal tracking (`patient_id` + `discipline`, free-text `reason`) | `backend/app/models/refusal.py`, `services/refusal_engine.py` | NO — no code set; not linked to a specific visit or `SFVRequirement` | NO — different entity scope (general discipline refusal, not SFV-linked) |
| `CHHAVisitOutcome` | Home Health Aide visit outcome/logistics record, one row per `visit_id` | `backend/app/models/chha_visit_outcome.py` (`reason_for_visit`, `exception_narrative`) | NO — free `String(64)`, no fixed code list | NO — wrong discipline/workflow scope (CHHA aide, not RN/LPN SFV) |
| SFV completion API | `POST /visits/sfv-requirements/{id}/complete` only handles the "SFV was completed" case | `api/visits.py::complete_sfv_requirement`, `hope_phase_b_engine.py::complete_sfv_requirement_from_visit` | N/A | N/A — no "not completed" branch exists in the backend at all; confirmed by trace, not assumed |

## Finding

**AUTHORITATIVE SOURCE FOUND: NO.**

Every candidate fails the AUTHORITATIVE and/or MATCHES-CMS tests. The gap
is structural, not a storage-location choice: no backend workflow today
asks a clinician to record one of the four CMS reason codes at the point
an SFV goes uncompleted. The only existing capture point is RNICA
self-attestation free text, which is architecturally disallowed as an
export source (same class of defect the SFV ownership fix eliminated
for J2052A/B and J2053).

## OPEN QUESTION — REQUIRES ROMEL DECISION

**Option A**: Build a dedicated "SFV not completed" capture workflow
(new backend field/endpoint on `SFVRequirement` + UI), analogous to the
J2053 capture-path work, for the not-completed branch.

**Option B**: Leave J2052C unexported (always placeholder) until Option A
is approved and built; document explicitly as a known HOPE export gap.

No option is selected or implemented in this record.
