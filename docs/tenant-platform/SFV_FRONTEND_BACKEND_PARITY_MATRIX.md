Document Status: AUDIT BASELINE / REMEDIATION REQUIRED

# SFV Frontend/Backend Parity Matrix

**Purpose:** Track, per required scenario, whether the frontend and
backend agree on SFV lifecycle behavior. Populated from direct repository
evidence (file:line), not assumption. A row is `PASS` only when both
frontend and backend behavior were traced and agree; `GAP` when a
required capability does not exist yet; `NOT_VERIFIED` when the
repository evidence needed to decide is incomplete.

**Repository state as of this pass (HEAD `16264cf` + uncommitted SFV
messaging fix):**

- The only backend SFV completion path is the automatic hook
  `_maybe_complete_open_sfv_for_visit` (`backend/app/api/visits.py:3868`),
  invoked from `_run_phase_b_finalize_hooks` as a side effect of
  finalizing any qualifying visit note for the patient. It picks the
  **oldest OPEN** `SFVRequirement` for the patient
  (`_find_oldest_open_sfv_requirement_for_patient`, row-locked via
  `.with_for_update()`) and calls
  `complete_sfv_requirement_from_visit` (`hope_phase_b_engine.py:397-438`).
- **There is no dedicated SFV completion API endpoint** (verified: no
  `sfv-requirement`/`/sfv/` route exists anywhere in `backend/app/api`).
  The frontend has no way to explicitly request completion or read back a
  structured result.
- The frontend's `sfv.inPersonSfvCompleted` checkbox (`RNICA.jsx`, `sfv`
  screen) is a local-only form field on the triggering visit's own form
  data. It is never sent to, or checked against,
  `complete_sfv_requirement_from_visit`. It has been relabeled this pass
  to state plainly that it is reference-only (P3-009 partial mitigation —
  messaging only, no wiring change).
- `SFVRequirement.status` (`backend/app/models/sfv_requirement.py:52-73`)
  is constrained to exactly `OPEN`, `COMPLETED`, `OVERDUE`, `CANCELLED` —
  not the richer trigger/due/visit-started/completed/export/submission
  lifecycle required by product direction (see
  `RNICA_PHASE3_REMEDIATION_REGISTER.md`).
- Tenant/patient isolation for the completion hook is **structurally
  enforced today**, verified via `get_authorized_patient`
  (`backend/app/core/patient_access.py:61`), which every visit-finalize
  endpoint calls before reaching the finalize hooks: it enforces
  `Patient.tenant_id == caller.tenant_id`, active-user status, and
  intra-tenant care-team/assignment scoping. The completing clinician is
  therefore always an active employee of the patient's own tenant/agency
  before the SFV hook ever runs.

| ID | Scenario | Frontend expected | Backend expected | Audit expected | Result |
|---|---|---|---|---|---|
| SFV-P01 | Original RN completes a different visit | Allow | Accept | Completion recorded | **GAP** — backend accepts (visit-ID + discipline check passes); frontend has no explicit action to allow/disallow because no completion request exists at all. Silent-hook behavior only. |
| SFV-P02 | Original LVN completes a different visit | Allow when authorized | Accept when authorized | Completion recorded | **GAP** — same as SFV-P01; "when authorized" cannot be evaluated because there is no authorization-service call in the current hook, only a discipline string check. |
| SFV-P03 | Different RN completes a different visit | Allow | Accept | Completing RN recorded | **PASS (backend only)** — `complete_sfv_requirement_from_visit` never compares clinician identity, only visit ID + discipline (confirmed `hope_phase_b_engine.py:397-438`). Frontend has no visibility into this. |
| SFV-P04 | Different LVN completes a different visit | Allow when authorized | Accept when authorized | Completing LVN recorded | Same as SFV-P03. |
| SFV-P05 | Authorized on-call RN completes different visit | Allow | Accept | On-call RN and visit recorded | **NOT_VERIFIED** — no on-call/assignment authorization model was found gating this hook; "on-call" status is not read anywhere in `hope_phase_b_engine.py` or `_maybe_complete_open_sfv_for_visit`. |
| SFV-P06 | Authorized on-call LVN completes different visit | Allow when authorized | Accept when authorized | On-call LVN and visit recorded | Same as SFV-P05. |
| SFV-P07 | Other authorized clinician completes different visit | Reflect configured permission | Accept only when permission and scope allow | Role and authority recorded | **GAP** — no permission-service integration exists in the current hook; only RN/LPN/LVN discipline strings are checked. |
| SFV-P08 | Same clinician attempts completion in trigger visit | Block | Reject | Rejection recorded | **PASS (backend only)** — `completing_visit_id == requirement.trigger_reference_id` raises `ValueError`, silently caught, no completion occurs. **GAP (frontend)** — the frontend checkbox does not block anything; it is a local field with no backend call. |
| SFV-P09 | Different clinician but same triggering visit | Block | Reject | Rejection recorded | Same visit-ID rejection as SFV-P08 — clinician identity is irrelevant to this check, which is correct per the product rule. |
| SFV-P10 | Same-day, separate qualifying visit | Allow | Accept | Both visits preserved | **PASS (backend)** — no same-day exclusion in the visit-ID comparison; confirmed no date-only check exists. |
| SFV-P11 | Completion before trigger | Block | Reject | Rejection reason recorded | **NOT_VERIFIED** — `hope_phase_b_engine.py:397-438` was not re-traced in this pass for a `completing_visit_datetime < trigger_datetime` guard; needs explicit re-check before closure. |
| SFV-P12 | Completion outside verified timing window | Warn/block per authority | Reject or exception workflow | Timing result recorded | **NOT_VERIFIED** — the 48-hour figure is an SNS product rule pending external CMS/HOPE timing-spec verification (constitution §31); whether/where it is enforced in code was not re-traced this pass. |
| SFV-P13 | Cross-patient completion visit | Do not offer | Reject | Security event recorded | **PASS (structural)** — `_find_oldest_open_sfv_requirement_for_patient` filters by `patient_id == visit.patient_id`; `visit.patient_id` was already tenant/patient-authorized via `get_authorized_patient` earlier in the finalize request. A visit cannot complete a different patient's requirement. |
| SFV-P14 | Cross-tenant completion visit | Do not offer | Reject | Security event recorded | **PASS (structural)** — `get_authorized_patient` enforces `Patient.tenant_id == caller.tenant_id` before any finalize hook runs; verified `backend/app/core/patient_access.py:61-84`. |
| SFV-P15 | Unauthorized on-call individual | Do not offer | Reject | Authorization failure recorded | **NOT_VERIFIED** — see SFV-P05/P07; no on-call authorization model traced. |
| SFV-P16 | Assigned but visit not performed | Show assigned/incomplete | Reject completion | Assignment preserved, no completion | **NOT_VERIFIED** — no "assignment" concept was found on `SFVRequirement`; only `task_id` (nullable). |
| SFV-P17 | Visit started but required symptom documentation absent | Show incomplete | Reject completion | Missing documentation recorded | **GAP** — `complete_sfv_requirement_from_visit` does not inspect clinical note content; completion is driven by visit metadata (ID, datetime, discipline, mode), not documentation completeness. |
| SFV-P18 | Valid visit with incomplete signature/authentication | Show incomplete | Reject completion | Authentication blocker recorded | **NOT_VERIFIED** — visit signature/authentication gating for this specific hook was not re-traced this pass. |
| SFV-P19 | Repeated completion request | Show existing completion | Return idempotent result | No duplicate completion | **PARTIAL PASS** — `_find_oldest_open_sfv_requirement_for_patient` only returns `status == 'OPEN'` rows, so a second finalize on an already-completed requirement finds nothing to complete (no duplicate). There is no idempotency key or structured "already completed" response because there is no request/response API at all. |
| SFV-P20 | Two clinicians submit concurrently | Show refreshed authoritative state | Accept one; reject/idempotently resolve other | Concurrency recorded | **PASS (backend, partial)** — `.with_for_update()` row-locks the `SFVRequirement` row during lookup, preventing a double-complete race at the DB level. No frontend-visible concurrency signal exists (no API to observe it from). |
| SFV-P21 | Completion visit later voided | Show no longer satisfied or correction state | Reopen/recalculate per authority | Full change history preserved | **GAP** — no void/correction workflow exists for `SFVRequirement`; `status` has no `VOIDED`/`CORRECTED` value. |
| SFV-P22 | Completed clinically but not exported | Show completed/export pending | Keep separate lifecycle statuses | Export-pending state recorded | **GAP** — `status` conflates clinical completion and export/submission into one 4-value field; no separate export/submission state exists on this model. |
| SFV-P23 | Exported but submission rejected | Show rejected submission, not incomplete visit | Preserve completed visit and rejected submission | Rejection details recorded | **GAP** — same as SFV-P22; no submission-state tracking on `SFVRequirement`. |
| SFV-P24 | Corrected and resubmitted | Show corrected/resubmitted state | Accept valid transition | Original and corrected history retained | **GAP** — no correction/resubmission lifecycle exists. |
| SFV-P25 | Browser sends forged completion visit | Do not permit through normal UI | Reject | Security-relevant rejection recorded | **PASS (structural)** — there is no client-writable API surface for SFV completion at all today; the only path is server-side, triggered by the server's own visit-finalize flow. A forged frontend request has nothing to call. |
| SFV-P26 | Theme or navigation change | Preserve SFV state | No mutation | No new lifecycle event | **PASS** — theme/navigation code paths do not touch `SFVRequirement` (confirmed no cross-references). |
| SFV-P27 | Page reload | Reload backend truth | No duplicate record or completion | No duplicate audit event | **GAP** — the frontend has no read API for `SFVRequirement` state either, so "reload backend truth" is not currently possible; the `sfv.inPersonSfvCompleted` checkbox reflects only the triggering visit's own saved form data, not the authoritative requirement. |
| SFV-P28 | Original clinician unavailable | Offer authorized reassignment/on-call path | Accept authorized alternate clinician | Assignment and completion preserved separately | **PASS (backend, partial)** — the backend never requires the original clinician (confirmed no clinician-identity check exists); "offer authorized reassignment/on-call path" has no frontend surface because there is no dedicated SFV workflow UI beyond the triggering-visit checkbox. |

## Summary

- **Structural PASS (verified, no code change needed):** tenant isolation
  (SFV-P14), cross-patient isolation (SFV-P13), same-visit rejection
  (SFV-P08/P09), forged-request resistance (SFV-P25), theme/navigation
  non-interference (SFV-P26), concurrent double-complete prevention
  (SFV-P20), clinician-identity independence (SFV-P03/P04/P28).
- **Confirmed architectural gap, not a simple bug:** no dedicated SFV
  completion API endpoint exists; lifecycle is a 4-value status, not the
  12-state model required by product direction; no idempotency key, no
  structured error codes, no on-call/permission-service integration, no
  clinical-content validation, no void/correction/export/submission
  tracking. Building this is a schema + API change requiring its own
  explicit authorization (see `RNICA_PHASE3_REMEDIATION_REGISTER.md`
  P3-009 and P3-014 for tracking).
- **NOT_VERIFIED items requiring a dedicated re-trace pass before
  closure:** completion-before-trigger guard (SFV-P11), timing-window
  enforcement (SFV-P12), on-call/assignment authorization (SFV-P05/P06/
  P07/P15/P16), signature/authentication gating (SFV-P18).

No row is claimed CLOSED. This matrix documents current behavior only.
