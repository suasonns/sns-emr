# SFV Lifecycle Trace Matrix (Phase 2, independent re-trace)

**Document Status:** REMEDIATION COMPLETE (backend + frontend parity) — see `RNICA_PHASE3_REMEDIATION_REGISTER.md` P3-009/P3-017. §4/§5 originally documented a frontend-only conflation and a missing authoritative completion path; both have since been closed: the self-attested checkbox was removed from the triggering RN ICA form, a real `POST /visits/sfv-requirements/{id}/complete` endpoint now exists, and the only completion UI lives on a separate, later Visit Notes encounter. Remaining out-of-scope items (no formal on-call subsystem, no browser-automated E2E suite) are recorded in `SFV_FRONTEND_BACKEND_PARITY_MATRIX.md`.

**Scope:** every Symptom Follow-up Visit (SFV) / HOPE Update Visit (HUV)
trigger condition in `backend/app/services/hope_phase_b_engine.py`, traced to
its "due" state and its "completed" state, and checked for trigger-vs-
completion conflation.

**Commit inspected:** `16264cf`.

---

## 1. Backend trigger engine

| # | Trigger condition | Trigger file:line | "Due" state file:line | "Completed" state file:line | Trigger vs completion conflated? | Status |
|---|---|---|---|---|---|---|
| 1 | Any J2051 **pain** impact normalized to MODERATE/SEVERE | `hope_phase_b_engine.py:140-142` (`_is_moderate_or_severe`, set at `:40`) → `_symptom_group_from_inputs:145-155` returns `"PAIN"` | `SFVRequirement.due_at = trigger_datetime + 2 days` (`:356`), `status="OPEN"` (`:380`); companion `Task.due_date` (`:95-96, 236`) | `complete_sfv_requirement_from_visit:397-446` sets `status="COMPLETED"`, `completed_at`, `completed_visit_id` (`:428-431`); task closed `:433-443` | **No** (backend) — separate objects and separate call sites | VERIFIED_COMPLETE |
| 2 | Any J2051 **non-pain** impact MODERATE/SEVERE | same, `:145-155` returns `"NON_PAIN"` | same `:356, 380` | same `:428-443` | No | VERIFIED_COMPLETE |
| 3 | Both pain and non-pain MODERATE/SEVERE | `:149-150` returns `"BOTH"` | same | same | No | VERIFIED_COMPLETE |
| 4 | Neither → no SFV | `:154` returns `None`; early return `:334-340` with reason "No moderate or severe symptom impact; SFV not required" | N/A | N/A | No | VERIFIED_COMPLETE |
| 5 | Trigger source must be INITIAL_RN_ICA ‖ HUV1 ‖ HUV2 | `:330-331` (`ValueError` otherwise); constants `:23-25` | N/A | N/A | No | VERIFIED_COMPLETE |
| 6 | Idempotency — one requirement per (patient, source, reference) | `_find_existing_sfv_requirement:303-317`, early return `:342-349` | existing row | existing row | No | VERIFIED_COMPLETE |
| 7 | HUV1 task creation on RN ICA finalize | `create_huv_tasks_from_initial_rn_ica:262-283` | `due_at = election + 15 days` (`:259`) | `validate_huv_visit_completion:158-181` (days 6-15, RN only) | No | VERIFIED_COMPLETE |
| 8 | HUV2 task creation on RN ICA finalize | `:285-295` | `due_at = election + 30 days` (`:260`) | `validate_huv_visit_completion:176-179` (days 16-30) | No | VERIFIED_COMPLETE |
| 9 | Task de-duplication for an open SFV/HUV | `_get_existing_open_task:184-204` + `_create_task_if_missing:206-230` | `TaskStatus.PENDING` (`:99-101, 240`) | `TaskStatus.COMPLETED` (`:103-105, 436`) | No | VERIFIED_COMPLETE |

## 2. SFV completion eligibility rules (backend)

| Rule | File:line | Effect |
|---|---|---|
| Must be an in-person visit | `hope_phase_b_engine.py:417-419` | `ValueError("SFV must be completed by an in-person visit")` |
| Must be RN or LPN/LVN | `:421-423` | `ValueError` otherwise |
| Must be a **separate visit** from the triggering INITIAL_RN_ICA/HUV | `:425-426` | `ValueError("SFV must be a separate visit from the triggering INITIAL_RN_ICA/HUV")` |
| Already-completed requirement is a no-op | `:413-415` | returns unchanged |

## 3. Trigger inputs as actually supplied by the API layer

| Step | File:line | Note |
|---|---|---|
| J2051 impacts parsed out of structured note content | `backend/app/api/visits.py:3611-3710` (`_extract_j2051_impacts_from_notes`; reads `content["symptom_impact"]` / `["symptomImpact"]` at `:3694`) | The engine is fed by **visit note content**, not by RNICA `form_data` directly |
| Oldest open SFV requirement located for a patient | `visits.py:3833-3846` | `status == "OPEN"`, ordered by `due_at` |
| Completion attempted for an arriving visit | `visits.py:3868-3904` | Calls `complete_sfv_requirement_from_visit` (`:3885-3893`); logs `NOT_ELIGIBLE` on `ValueError` (`:3902`) |
| RN ICA finalize path | `visits.py:3916-3940` | Passes `j2051_pain_impact` / `j2051_non_pain_impact` into `process_initial_rn_ica_finalize` |
| HUV finalize path | `visits.py:3990-3991` | Same inputs into `process_huv_finalize` |

## 4. Frontend SFV state — the conflation finding

| # | Element | File:line | Behaviour |
|---|---|---|---|
| 1 | Frontend trigger computation | `sns-emr-frontend/src/intake/hopeReportMapper.js:400-429` (`getSfvStatus`) | Recomputes `required` from `formData.symptomImpact` using its **own** `isModerateOrSevere` (`:394-398`), which additionally accepts numeric `2`/`3` and substring matches — a different predicate from the backend's exact-set `{"MODERATE","SEVERE"}` (`hope_phase_b_engine.py:40, 140-142`) |
| 2 | Frontend "due" date | `hopeReportMapper.js:421` (`addDays(screeningDate, 2)`) | Derived from `sfv.symptomImpactScreeningDate` ‖ `symptomImpact.assessmentDate`, i.e. a **clinician-entered date**, whereas the backend derives `due_at` from `trigger_datetime` (`hope_phase_b_engine.py:356`) |
| 3 | Frontend "completed" state | `hopeReportMapper.js:422` reads `sfv.inPersonSfvCompleted` | Written by a plain checkbox on the **triggering RN ICA form itself**: `RNICA.jsx:9398` (`{ type: "checkbox", label: "In-Person SFV Completed", path: "inPersonSfvCompleted" }`), default `RNICA.jsx:755` |
| 4 | Exported J2052 | `hopeReportMapper.js:618` | Emits "In-person SFV completed?" from that same self-attested checkbox |
| 5 | Consumption inside RNICA | `RNICA.jsx:11225` (`getSfvStatus(formData)`) | The UI's SFV banner never consults `SFVRequirement`/`Task` |

**Conflation verdict: YES — in the frontend only.**
`sfv.inPersonSfvCompleted` is editable on the very visit form that produces
the trigger, so a user can mark an SFV "completed" on the triggering
assessment. The backend explicitly rejects that same fact pattern
(`hope_phase_b_engine.py:425-426`). There is no code path that reconciles
`form_data.sfv.*` with `SFVRequirement` — a repository-wide scan found no
reader of `SFVRequirement` in the frontend and no writer of
`form_data.sfv.inPersonSfvCompleted` in the backend.

| Conflation row | Trigger side | Completion side | Status |
|---|---|---|---|
| Frontend same-form self-attested completion | `getSfvStatus` required (`hopeReportMapper.js:415-419`) | `sfv.inPersonSfvCompleted` checkbox (`RNICA.jsx:9398`) | CONFLICTING |
| Two independent trigger predicates | `hope_phase_b_engine.py:140-142` | `hopeReportMapper.js:394-398` | CONFLICTING |
| Two independent due-date derivations | `hope_phase_b_engine.py:356` | `hopeReportMapper.js:421` | CONFLICTING |
| Backend requirement lifecycle | `hope_phase_b_engine.py:319-395` | `:397-446` | VERIFIED_COMPLETE |
| Trigger source restricted to the three HOPE timepoints | `:330-331` | N/A | VERIFIED_COMPLETE |
| J2052/J2053 exported from `form_data` only, never from `SFVRequirement` | — | `hopeReportMapper.js:618-619` | PRESENT_NOT_HARVESTED |

**Update (remediation pass):** row 3 ("frontend completed state") and the
"same-form self-attested completion" conflation row are now **closed**.
`sfv.inPersonSfvCompleted`/`sfvDate` are no longer editable anywhere in
`RNICA.jsx` — the checkbox was removed. The new `SfvStatusCard` on the
triggering RN ICA screen instead auto-syncs those two fields from the
authoritative `SFVRequirement` status returned by
`GET /visits/sfv-requirements`, so `hopeReportMapper.js` (row 4, J2052
export) now reflects real backend completion state instead of manual
self-attestation, and the "PRESENT_NOT_HARVESTED" row above is also
closed: `form_data.sfv.*` is now populated *from* `SFVRequirement`, not
independently of it. Rows 1–2 (independent trigger predicate and due-date
derivation) remain open and are unrelated to this SFV-completion-endpoint
remediation.

## 5. SFV Completion Visit Rule (product-authority directive)

**Rule as stated by product authority:** the SFV completion event must
occur in a **different visit record** than the visit that generated the
SFV trigger — `triggerVisitId != completionVisitId`. Same clinician, same
RN, same LVN, same discipline, same patient, and same day (within 48
hours, if timing rules permit) are all explicitly **allowed**. The only
disqualifying condition is completing the SFV inside the same visit
record that produced the trigger. Clinician identity is not the
determining factor; visit identity is.

**Independent re-trace of backend enforcement** (`hope_phase_b_engine.py`,
commit `16264cf`):

```python
# complete_sfv_requirement_from_visit, :425-426
if str(completing_visit_id) == str(requirement.trigger_reference_id):
    raise ValueError("SFV must be a separate visit from the triggering INITIAL_RN_ICA/HUV")
```

This is a **visit-identity comparison only** — `completing_visit_id` vs.
`requirement.trigger_reference_id` (the id of the triggering
INITIAL_RN_ICA/HUV visit, stored at trigger time,
`hope_phase_b_engine.py:378`). There is no comparison anywhere in this
function against a clinician id, user id, or discipline value beyond the
separate, independent check that the completing clinician's discipline is
RN or LPN/LVN (`:421-423`, `DISCIPLINE_RN`/`DISCIPLINE_LVN`/`DISCIPLINE_LPN`)
— which does not compare the completing clinician to the triggering
clinician at all, it only validates that whoever completes it holds one of
those two disciplines.

**Verdict: the backend already fully implements the product-authority rule
exactly as specified.** No backend code change is required for this
directive.

| Example (from directive) | Trigger visit | Completion visit | Expected | Backend evidence | Status |
|---|---|---|---|---|---|
| Same RN, different visit | `RNICA Admission`, RN = Jane Smith | `Skilled Nursing Visit`, RN = Jane Smith | PASS | `:425-426` compares visit ids only, not clinician ids | VERIFIED_COMPLETE |
| Same LVN, different visit | `RNICA Admission`, LVN = John Jones | `Skilled Nursing Visit`, LVN = John Jones | PASS | same | VERIFIED_COMPLETE |
| Different clinician, different visit | `RNICA Admission`, RN = Nurse A | `Skilled Nursing Visit`, LVN = Nurse B | PASS | same | VERIFIED_COMPLETE |
| Same visit (trigger and completion collapsed) | one visit record, both events | — | FAIL | `:425-426` raises `ValueError` | VERIFIED_COMPLETE |

**Frontend gap — closed (later pass, "RNICA SFV REMEDIATION
CONTINUATION" + "SFV FRONTEND PLACEMENT DECISION" directives):** the
self-attested `sfv.inPersonSfvCompleted` checkbox has been **removed**
from `RNICA.jsx`. Completion is no longer offered on the triggering form
at all. A new authoritative backend command,
`POST /visits/sfv-requirements/{sfvRequirementId}/complete`
(`backend/app/api/visits.py`), directly reuses
`complete_sfv_requirement_from_visit` (no duplicated rule logic), so the
backend's visit-identity rule is now reachable from a real, callable
completion path. The frontend calls it exclusively through
`completeSfvRequirement` (`sns-emr-frontend/src/api/sfv.ts`), and the only
UI control that invokes it lives on a **separate, later visit** — the new
`SymptomFollowUpVisitSection` on the Visit Notes screen
(`sns-emr-frontend/src/components/VisitNotes.jsx`), gated on that visit
being finalized. The triggering RN ICA screen now shows only a read-only
`SfvStatusCard` (current status + navigation link), enforcing the
separate-visit rule structurally at the UI-placement level as well as at
the backend-validation level.

**New tests, executed and passing:**
`backend/tests/test_sfv_completion_visit_separation.py` (8 scenarios) and
`backend/tests/test_sfv_completion_api.py` (9 scenarios, including the new
completion endpoint, the read-only list endpoint, unauthorized-role
rejection, authorized-LVN success, idempotent replay, and a real
two-thread concurrency race) — all passing under
`scripts/run_isolated_tests.py`. Frontend:
`sns-emr-frontend/src/components/SymptomFollowUpVisitSection.test.jsx`
(4 scenarios) plus the full existing 277-test frontend suite and
production build, all passing.

---

## 6. Regulatory framing

All "2 calendar days", "days 6-15", "days 16-30", "RN only", "in-person"
rules above are transcribed from the repository's own code and docstrings
(`hope_phase_b_engine.py:158-181, 356`). Their currency and bindingness
against CMS HOPE guidance was **not** verified this pass — see
`AUTHORITY_APPLICABILITY_REGISTER.md`.
