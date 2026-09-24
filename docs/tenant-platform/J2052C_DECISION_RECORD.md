# J2052C Decision Record

Status: NOT_VERIFIED — no authoritative source found. This record
reformats the completed investigation in `J2052C_SOURCE_DISCOVERY.md`
into the requested decision-record template. No new research was
performed; no schema, storage, API, or enum is designed or proposed here.

## CMS Requirement — VERIFIED BY CMS (reverified against v1.02)

Source: *HOPE Guidance Manual v1.02*, Effective October 1, 2025, p.73
(see `HOPE_CMS_AUTHORITY_SOURCE_REGISTER.md` for full citation, URL, and
checksum). Verified 2026-09-24.

J2052C — Reason SFV Not Completed. Required only when J2052A = 0 (No);
skips to M1190, Skin Conditions. Verbatim CMS codes:

> 1. Patient and/or caregiver declined an in-person visit.
> 2. Patient unavailable (e.g., in ED, hospital, travel outside of
>    service area, expired).
> 3. Attempts to contact patient and/or caregiver were unsuccessful.
> 9. None of the above.

**CMS v1.01→v1.02 change status**: The complete 7-row v1.01→v1.02
change table (`HOPE_CMS_AUTHORITY_SOURCE_REGISTER.md`) was read in full.
J2052C's codes and skip target are **textually identical** in both
versions — zero rows in the change table touch J2052C. This conclusion
was reached by reading the change table end-to-end, not by assuming a
J2053-only impact from a partial search result.

## Candidate Sources Evaluated

| CANDIDATE SOURCE | CURRENT WORKFLOW | REPOSITORY EVIDENCE | MATCHES CMS | REUSE POSSIBLE |
|---|---|---|---|---|
| `RNICA.jsx` `sfv.reasonNotCompleted` | Free-text input on the RNICA trigger form's "Symptom Follow-Up Visit" section (line ~9515). Never submitted to any backend endpoint — lives only in the RNICA form's local JSON blob. | `RNICA.jsx` line ~9515: `{ type: "input", label: "Reason SFV not completed", path: "reasonNotCompleted" }` | NO — free text, not restricted to codes 1/2/3/9 | NO — architecturally disallowed (RNICA self-attestation at trigger time, not a completion-visit/backend record) |
| `SFVRequirement.status` | Requirement lifecycle state (`OPEN`/`COMPLETED`/`OVERDUE`/`CANCELLED`), set by `complete_sfv_requirement_from_visit` and scheduled/overdue logic | `sfv_requirement.py` model, DB check constraint | NO — 4 lifecycle states, no mapping to CMS reason codes 1/2/3/9 exists in code | NO — conflates a workflow-lifecycle enum with a clinical reason code |
| `Refusal` model | Discipline-level visit refusal tracking (`patient_id` + `discipline`, free-text `reason`) | `backend/app/models/refusal.py`, `services/refusal_engine.py` | NO — no code set; not linked to a specific visit or `SFVRequirement` | NO — different entity scope (general discipline refusal, not SFV-linked) |
| `CHHAVisitOutcome` | Home Health Aide visit outcome/logistics record, one row per `visit_id` | `backend/app/models/chha_visit_outcome.py` (`reason_for_visit`, `exception_narrative`) | NO — free `String(64)`, no fixed code list | NO — wrong discipline/workflow scope (CHHA aide, not RN/LPN SFV) |
| SFV completion API | `POST /visits/sfv-requirements/{id}/complete` only handles the "SFV was completed" case | `api/visits.py::complete_sfv_requirement`, `hope_phase_b_engine.py::complete_sfv_requirement_from_visit` | N/A | N/A — no "not completed" branch exists in the backend at all; confirmed by trace, not assumed |

## Additional Candidates Re-Checked (post-commit verification pass)

Per instruction to exhaust scheduling, missed-visit, contact-attempt,
decline, unavailable, cancellation, void, task-closure, audit-event, and
historical/deprecated candidates before retaining "NO AUTHORITATIVE
SOURCE FOUND," the following were additionally searched this pass
(commit `e3806cb` and prior). None qualifies — none is scoped to a
specific `SFVRequirement`, and none distinguishes CMS codes 1/2/3/9:

| Candidate | Repository Evidence | Why it does not qualify |
|---|---|---|
| `ClinicalOutcomeRecord` / `ClinicalOutcomeAuditEvent` | `backend/app/models/clinical_outcome.py` — California two-hour response tracking (issue #143), FKs to `source_visit_id`/`source_task_id`, not `sfv_requirement_id` | Different workflow entirely (response-time compliance, not SFV completion reason); no code set matching 1/2/3/9 |
| `PatientResponseEvent` / `NurseResponseAssignment` / `PatientResponseAuditEvent` | `backend/app/models/patient_response.py` — same California two-hour chain | No relationship to `SFVRequirement` or HOPE triggers at all |
| Broad grep for `contact_attempt`, `unable_to_contact`, `patient_declined`, `patient_unavailable`, `cancellation_reason`, `missed_visit`, `no_show`, `task_closure`, `audit_event`, `void_reason` (case-insensitive, `backend/app`) | 42 files matched; manually reviewed the visit/outcome-adjacent ones (above); remainder are generic audit-logging infrastructure (`app/core/audit_events.py`, billing audit routers, document/bereavement notification services) unrelated to SFV | Confirmed unrelated by direct file review, not assumed from a keyword match alone |
| `sfv_engine.py::create_sfv_requirement_if_needed` (legacy/dead code, confirmed unused this session) | Re-searched for `reason`/`declin`/`cancel`/`void`/`not_completed` — **no matches** | Confirms this dead function also carries no reason-code field, closing off the last "historical implementation" candidate |

**Not exhaustively re-verified this pass**: scheduling/task-management
modules outside the `sfv`/`visit`/`clinical_outcome`/`patient_response`
model files (e.g., a generic `tasks` table exists per FK references in
`clinical_outcome.py`, but its own model file was not opened this pass).
This is disclosed as a residual gap, not silently treated as closed.

## Finding

**AUTHORITATIVE SOURCE FOUND: NO** (re-affirmed, with an expanded and
now-documented candidate set; not merely re-asserted from the prior
pass). This conclusion is retained because every listed candidate was
individually traced to a repository path/symbol and individually fails
at least one mandatory rule (AUTHORITATIVE and/or MATCHES-CMS), per the
table above — it is not a blanket assertion.

Four separate questions, kept separate per instruction:

- **A. What does CMS require?** — Answered above: **VERIFIED BY CMS**,
  four fixed codes (1/2/3/9), skip to M1190.
- **B. Where does SNS currently capture it?** — **VERIFIED BY REPOSITORY
  TRACE**: nowhere in a form that reaches the backend. The only capture
  point is RNICA free-text self-attestation (`RNICA.jsx` line ~9515),
  which never reaches an API or database column.
- **C. Can an existing SNS model be reused safely?** — **NOT_VERIFIED /
  NO**, for every candidate examined (`SFVRequirement.status`,
  `Refusal`, `CHHAVisitOutcome`, `ClinicalOutcomeRecord`,
  `PatientResponseEvent`) — each fails on code-set mismatch, entity
  scope, or workflow scope as detailed in the tables above.
- **D. What new workflow, if any, should SNS adopt?** — **OPEN QUESTION
  — REQUIRES ROMEL DECISION**. Not answered here; see Options below.

**NEW STORAGE REQUIRED: REQUIRES ROMEL DECISION** — this record does not
assert that new storage is definitively required. It asserts only that
no existing SNS storage safely represents the CMS codes today (question
C above). Whether the resolution is new storage, a reused/extended
model, or a documented permanent gap is a product decision, not a
repository-trace finding.

## OPEN QUESTION — REQUIRES ROMEL DECISION

**Option A — Extend `SFVRequirement`.** Add a controlled
not-completed-reason field (fixed-choice, values 1/2/3/9) directly on
`SFVRequirement`, captured at the point staff record that an SFV could
not occur, analogous to the J2053 capture-path work. Requires new schema
+ new UI entry point + new tests. Not designed or scoped further here.

**Option B — Reuse an existing visit-outcome/refusal model.** Only
after proving semantic and audit compatibility (code-set mapping,
entity-linkage to the specific `SFVRequirement`, and audit-trail
parity) — none of `Refusal`, `CHHAVisitOutcome`,
`ClinicalOutcomeRecord`, or `PatientResponseEvent` currently satisfy
this per the candidate table above, so Option B as evaluated today would
still require modification, not pure reuse.

**Option C — Create a new linked SFV-outcome record.** If neither
Option A (extending the existing requirement row) nor Option B (reusing
an existing model) can safely represent the CMS response set without
conflating unrelated workflows, create a new, narrowly-scoped record
type linked 1:1 to `SFVRequirement` solely for the not-completed outcome
and its CMS reason code.

No option is selected or implemented in this record. Issue #146 remains
blocked pending this Romel decision.
