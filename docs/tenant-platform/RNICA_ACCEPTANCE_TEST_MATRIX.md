# RNICA Acceptance Test Matrix (Phase 2)

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED — this matrix tracks execution of *existing* tests; it is not the Phase 3 remediation register. See `RNICA_PHASE3_REMEDIATION_REGISTER.md` for defect-to-test mapping required by Phase 3 §5.

**Commit under test:** `16264cf`.

**Honesty rule applied throughout:** a row is marked `Pass` **only** where a
command was actually executed this pass and its exit code recorded.
Everything else is `Not-yet-run` or `Blocked`. No test result is inferred
from reading code.

**Test levels used:** static repository review · unit · component ·
contract · integration · end-to-end · historical compatibility ·
production build.

---

## 1. Commands actually executed this pass

| Command | Working dir | Exit code | Result |
|---|---|---|---|
| `npx vitest run src/intake/hopeReportMapper.test.js` | `sns-emr-frontend` | `0` | Test Files 1 passed (1); Tests 138 passed (138) |

Backend suites were **not** executed: `Test-Path backend\.venv` → `False`
(no Python environment provisioned in this workspace). Every backend row is
therefore `Not-yet-run`, not `Pass`.

---

## 2. Matrix

| Test ID | Requirement | Repository evidence ID | Test level | Preconditions | Action | Expected result | Evidence artifact | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| **AT-A1** | No backend service extracts RNICA field values into a HOPE payload (Finding A) | `HOPE_FIELD_TRACE_MATRIX.md` §0 | static repository review | Clean checkout at `16264cf` | Full-tree scan of `backend/` for HOPE payload assembly from `form_data` | Only metadata constants/getters, workflow status, and the SFV engine are found | This pass's scan output; `form_registry.py:341-418, 1137-1156`; `rnica_hope_workflow_service.py:25-200` | **Pass (static)** | Verified by direct read, not by an executable test |
| **AT-A2** | A backend contract test should assert HOPE export parity with `hopeReportMapper.js` | — (no such test exists) | contract | Backend env | Run a parity test comparing backend-emitted HOPE items to the frontend mapper | Parity or an explicit "frontend is authoritative" assertion | none | **Not-yet-run** | No such test exists in the repository; proposed |
| **AT-A3** | Existing frontend exporter behaviour is stable | `HOPE_FIELD_TRACE_MATRIX.md` §1-8 | unit | `node_modules` present | `npx vitest run src/intake/hopeReportMapper.test.js` | 138 tests pass | Command output, exit code `0` | **Pass** | Executed this pass |
| **AT-B1** | N0500/N0510/N0520 have exactly one semantics | `ITEM_CODE_CONFLICT_MATRIX.md` Conflict 1 | static repository review | — | Scan all files for the three codes | One semantics per code | 9 usage sites found across 2 contradictory semantics (`RNICA.jsx:9030-9033`; `hopeReportMapper.js:633-635`; `structured_findings.py:1224-1270`; `bodySystems.js:20`; `HopeReport.jsx:17-18`) | **Fail** | Confirmed conflict |
| **AT-B2** | `neurological.hopeItems.*` reaches an exporter | `DEAD_EXPORT_PATH_ANALYSIS.md` §4 | unit | — | Assert the mapper emits a value derived from `neurological.hopeItems.n0500` | Emitted | No reader exists | **Fail** (by static trace) | Proposed regression test |
| **AT-B3** | `medications.*` has a UI writer | `DEAD_EXPORT_PATH_ANALYSIS.md` §2 rows 1-3 | component | — | Render RN ICA and locate a control writing `medications.scheduledOpioid` | Control found | `medications` absent from `FORM_REGISTRY` (`RNICA.jsx:242-249`) | **Fail** (by static trace) | Proposed component test |
| **AT-C1** | I8005 is reachable from a UI control (Finding C) | `DEAD_EXPORT_PATH_ANALYSIS.md` §1 | component | — | Render `HopeComorbiditiesCard`, toggle "Other Medical Condition", assert `hopeComorbidities.other` written | Written | `RNICA.jsx:2668` + dispatch `:8376-8379`, config `:8939` | **Not-yet-run** (static trace passes) | Prior "dead path" claim refuted statically; no component test exists to lock it in |
| **AT-C2** | I8005 round-trips into the exporter | `HOPE_FIELD_TRACE_MATRIX.md` §3 | unit | `node_modules` | Assert `mapRnIcaToHopeReport({diagnoses:{hopeComorbidities:{other:true}}})` emits I8005 = Yes | Yes | `hopeReportMapper.js:459, 542` | **Not-yet-run** | No I8005 assertion exists in `hopeReportMapper.test.js` (code scan of test literals) — proposed |
| **AT-D1** | The Lock gate validates the narrative the RN writes (Finding D) | `LOCK_GATE_DEPENDENCY_TRACE.md` rows 3-5 | unit (backend) | Backend env | `evaluate_finalization_readiness({"finalization": {...no narrative...}})` | Should block if a narrative is required | `test_rnica_finalization.py:116-119` currently asserts `ready is True` with no narrative present | **Fail** (by static trace) | Current behaviour is test-protected; changing it requires a documented decision |
| **AT-D2** | `diagnoses.clinicalNarrativeReviewed` is settable from the UI | `LOCK_GATE_DEPENDENCY_TRACE.md` row 4 | component | — | Render RN ICA Diagnoses screen, locate the "narrative reviewed" checkbox | Found | Only writer is inside `ClinicalNarrativeCard` (`RNICA.jsx:2140`), never dispatched (`:8353`) | **Fail** (by static trace) | Legacy records with narrative text become un-lockable |
| **AT-D3** | Existing lock-readiness unit tests still pass | `LOCK_GATE_DEPENDENCY_TRACE.md` §3 | unit (backend) | Backend env | `python scripts\run_isolated_tests.py -- tests\test_rnica_finalization.py tests\test_rnica_hope_workflow.py -q` | All pass | All pass | **Pass** | Executed with `backend/dev.env` loaded; combined run with AT-E3 (26 tests, all dots, exit code 0) |
| **AT-D4** | Post-lock immutability | `test_rnica_finalization.py:230-241` | integration | Backend env | Attempt a post-lock `formData` edit | Rejected | — | **Not-yet-run** | Test exists; not executed |
| **AT-E1** | SFV trigger predicates agree frontend↔backend | `SFV_LIFECYCLE_TRACE_MATRIX.md` §4 | contract | Both envs | Feed the same `symptomImpact` values to `getSfvStatus` and `_is_moderate_or_severe` | Identical `required` outcome | `hopeReportMapper.js:394-398` accepts `2`/`3`/substrings; `hope_phase_b_engine.py:40,140-142` requires exact `"MODERATE"`/`"SEVERE"` | **Fail** (by static trace) | Proposed contract test |
| **AT-E2** | SFV cannot be self-attested on the triggering visit | `SFV_LIFECYCLE_TRACE_MATRIX.md` §4 row 3 | integration | Backend env | Complete an SFV requirement with the triggering visit id | `ValueError` | `hope_phase_b_engine.py:425-426` | **Not-yet-run** | Backend rule exists and is correct; the frontend checkbox (`RNICA.jsx:9398`) bypasses it for export purposes |
| **AT-E3** | Backend SFV/HUV engine behaviour | `backend/tests/test_rnica_hope_workflow.py` | unit/integration | Backend env | `python scripts\run_isolated_tests.py -- tests\test_rnica_finalization.py tests\test_rnica_hope_workflow.py -q` | All pass | All pass | **Pass** | Executed with `backend/dev.env` loaded; combined run with AT-D3 (26 tests, all dots, exit code 0) |
| **AT-F1** | Older/partial records merge safely | `HISTORICAL_COMPATIBILITY_RESULTS.md` §2-3 | historical compatibility | `node_modules` | Round-trip + legacy-absent-field suites | Pass | Included in the 138 passing tests (`hopeReportMapper.test.js:215-295`) | **Pass** | Executed this pass |
| **AT-F2** | Array-element schema additions back-fill | `HISTORICAL_COMPATIBILITY_RESULTS.md` §2 | unit | — | Merge a saved array whose elements lack a newly added key | Element keys hydrated | `RNICA.jsx:9740-9742` takes arrays wholesale | **Fail** (by design, by static trace) | Documented as a renderer null-guard obligation, not necessarily a defect |
| **AT-G1** | Facesheet vs RN ICA demographics single authority | `DUPLICATE_AUTHORITY_MATRIX.md` §1 | component | — | Edit DOB in both surfaces, compare persisted values | One authoritative store | Both are independently writable (`RNICA.jsx:7986`; `PatientFacesheet.jsx:398, 1201-1208`) | **Fail** (by static trace) | Requires an authority decision before any test can assert a correct outcome |
| **AT-H1** | Z0400 is emitted when declared | `ITEM_CODE_CONFLICT_MATRIX.md` Conflict 7 | unit | — | Assert the mapper emits Z0400 | Emitted | No `"Z0400"` in `sns-emr-frontend/src` | **Fail** (by static trace) | Or the registry declaration should be removed — authority decision |
| **AT-I1** | Production build unaffected by this pass | — | production build | `node_modules` | `npm run build` | Success | — | **Not-yet-run** | No application file was modified this pass (documentation only), so a build was not warranted |

---

## 2b. SFV Completion Visit Rule (product-authority directive, see `SNS_CONSTITUTION.md` §31 / `SFV_LIFECYCLE_TRACE_MATRIX.md` §6)

**Requirement:** `triggerVisitId != completionVisitId`. Clinician identity,
discipline, and same-day timing are explicitly **not** disqualifying —
only completing the SFV on the same visit record that produced the
trigger fails.

New file this pass: `backend/tests/test_sfv_completion_visit_separation.py`
— **executed** via
`python scripts\run_isolated_tests.py -- tests\test_sfv_completion_visit_separation.py -q`
(env loaded from `backend/dev.env`) → **8 passed, exit code 0**, 1.55s,
against an auto-provisioned isolated `sns_emr_test_*` database (migrations
applied to head `f7a8b9c0d1e2`).

| Test ID | Requirement | Repository evidence ID | Test level | Preconditions | Action | Expected result | Evidence artifact | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| **AT-SFV1** | Same nurse + different visit = PASS | `hope_phase_b_engine.py:425-426` | integration (backend) | Backend env | `test_same_nurse_different_visit_passes` | `SFVRequirement.status == "COMPLETED"` | `test_sfv_completion_visit_separation.py` | **Pass** | Executed this pass, exit 0 |
| **AT-SFV2** | Same RN + different visit = PASS | same | integration (backend) | Backend env | `test_same_rn_different_visit_passes` | Completed | same | **Pass** | Executed this pass, exit 0 |
| **AT-SFV3** | Same LVN + different visit = PASS | same | integration (backend) | Backend env | `test_same_lvn_different_visit_passes` | Completed | same | **Pass** | Executed this pass, exit 0 |
| **AT-SFV4** | Different clinician + different visit = PASS | same | integration (backend) | Backend env | `test_different_clinician_different_visit_passes` | Completed | same | **Pass** | Executed this pass, exit 0 |
| **AT-SFV5** | Same visit = FAIL | `hope_phase_b_engine.py:425-426` | integration (backend) | Backend env | `test_same_visit_fails` | `ValueError("... separate visit ...")` | same | **Pass** | Executed this pass, exit 0; confirms backend already enforces the rule |
| **AT-SFV6** | Same visit cannot self-complete SFV | same | integration (backend) | Backend env | `test_same_visit_cannot_self_complete_sfv` | `ValueError` | same | **Pass** | Executed this pass, exit 0 |
| **AT-SFV7** | Readiness/status not COMPLETED until a separate visit exists | `sfv_requirement.py` (`status`, `completed_visit_id`) | integration (backend) | Backend env | `test_readiness_status_not_complete_until_separate_visit_exists` | `status` stays `OPEN` until completion, then flips to `COMPLETED` only via a distinct visit | same | **Pass** | Executed this pass, exit 0 |
| **AT-SFV8** | Reporting retains trigger visit and completion visit as distinct fields | `sfv_requirement.py` (`trigger_reference_id`, `completed_visit_id`) | integration (backend) | Backend env | `test_reporting_reflects_trigger_and_completion_visits_separately` | `trigger_reference_id != completed_visit_id`, both populated | same | **Pass** | Executed this pass, exit 0; confirms no field collapses the two lifecycle events |

**Environment note:** initial attempt in this session guessed at
credentials (`postgres`/`postgres`, refused) instead of checking
`backend/dev.env`, which this same session's own checkpoint history
(`012-rnica-theme-verification-block.md`) had already recorded as the
correct source — load the *entire* file into the shell environment (not
just `DATABASE_URL`), then invoke
`python scripts\run_isolated_tests.py -- tests\<file> -q` from `backend/`.
Corrected and re-run successfully; no code defect was found in either the
test file or `complete_sfv_requirement_from_visit`.

---

## 2c. SFV Completion Command (authoritative endpoint, "RNICA SFV REMEDIATION CONTINUATION" + "SFV FRONTEND PLACEMENT DECISION" directives)

**Requirement:** a real, callable `POST /visits/sfv-requirements/{id}/complete`
command backed by `can_complete_sfv` (generic capability authorization, not
`role == RN || role == LVN`), with idempotent replay and safe concurrent
resolution, plus a `GET /visits/sfv-requirements` read endpoint for the
frontend. Completion is offered only from a separate, later, finalized
visit (`sns-emr-frontend/src/components/VisitNotes.jsx`); the triggering
RNICA screen is read-only.

New file this pass: `backend/tests/test_sfv_completion_api.py` —
**executed** via
`python scripts\run_isolated_tests.py -- tests\test_sfv_completion_api.py -v`
(env loaded from `backend/dev.env`) → **23 passed, exit code 0** (grew
from 10 → 14 after "SFV AUTHORIZATION CORRECTION", then 14 → 23 after
"FINAL AUTHORIZATION CORRECTION" refined `CASE_MANAGER` handling and
required the full PASS/FAIL role test matrix below, all 2026-09-23).

| Test ID | Requirement | Test | Level | Expected result | Status |
|---|---|---|---|---|---|
| **AT-SFV9** | Happy path completion | `test_complete_sfv_requirement_endpoint_happy_path` | integration (backend, HTTP) | `200`, `status == "COMPLETED"` | **Pass** |
| **AT-SFV10** | Same-visit rejection reachable from a real HTTP call | `test_complete_sfv_requirement_endpoint_rejects_same_visit` | integration (backend, HTTP) | `409 SAME_VISIT_NOT_ALLOWED` | **Pass** |
| **AT-SFV11** | Requirement not found | `test_complete_sfv_requirement_endpoint_requirement_not_found` | integration (backend, HTTP) | `404` | **Pass** |
| **AT-SFV12** | Completion visit not found | `test_complete_sfv_requirement_endpoint_completion_visit_not_found` | integration (backend, HTTP) | `404` | **Pass** |
| **AT-SFV13** | Idempotent replay | `test_complete_sfv_requirement_endpoint_idempotent_replay` | integration (backend, HTTP) | Second call returns the same authoritative result, no error, no duplicate mutation | **Pass** |
| **AT-SFV14** | Cross-tenant completion visit rejected | `test_complete_sfv_requirement_endpoint_cross_tenant_visit_rejected` | integration (backend, HTTP) | Rejected, no state change | **Pass** |
| **AT-SFV15** | Unauthorized role rejected (VOLUNTEER) | `test_complete_sfv_requirement_endpoint_unauthorized_role_rejected` | integration (backend, HTTP) | `403`, no state mutation | **Pass** |
| **AT-SFV16** | Authorized LVN, different clinician than trigger, completes | `test_complete_sfv_requirement_endpoint_authorized_lvn_different_clinician` | integration (backend, HTTP) | `200`, `status == "COMPLETED"` | **Pass** — was silently merged into the concurrency test's body during authoring (missing `def`, executed but mislabeled); split into its own named test this pass so it reports independently. |
| **AT-SFV17** | Concurrent completion requests resolve to exactly one winner | `test_complete_sfv_requirement_endpoint_concurrent_requests_single_winner` | integration (backend, HTTP, real `ThreadPoolExecutor` race) | Both HTTP responses `200`, both agree on the same `completionVisitId`, DB shows exactly one `COMPLETED` state | **Pass** |
| **AT-SFV18** | Read-only list endpoint returns open requirement | `test_list_sfv_requirements_endpoint_returns_open_requirement` | integration (backend, HTTP) | `200`, requirement summary present | **Pass** |
| **AT-SFV19** | Authorized NP (Nurse Practitioner, physician-identity linkage verified) completes | `test_complete_sfv_requirement_endpoint_authorized_np` | integration (backend, HTTP) | `200`, `status == "COMPLETED"` | **Pass** — added 2026-09-23; NP is an AUTHORIZED SFV COMPLETER ROLE per the corrected product rule. |
| **AT-SFV20** | Administrator (holds shared RN-scope capability, but not a nursing credential) rejected | `test_complete_sfv_requirement_endpoint_administrator_rejected` | integration (backend, HTTP) | `403`, requirement stays `OPEN` | **Pass** — added 2026-09-23; failed against the pre-correction `can_complete_sfv`, confirming the original implementation was over-broad (see P3-018). |
| **AT-SFV21** | Physician Assistant (PA — non-nursing clinician, physician-identity linkage verified) rejected | `test_complete_sfv_requirement_endpoint_physician_assistant_rejected` | integration (backend, HTTP) | `403`, requirement stays `OPEN` | **Pass** — added 2026-09-23; same finding as AT-SFV20. |
| **AT-SFV22** | Social Worker (SW — non-nursing role with ordinary chart access) rejected | `test_complete_sfv_requirement_endpoint_social_worker_rejected` | integration (backend, HTTP) | `403`, requirement stays `OPEN` | **Pass** — added 2026-09-23. |
| **AT-SFV23** | Authorized LPN (alias of LVN) completes | `test_complete_sfv_requirement_endpoint_authorized_lpn` | integration (backend, HTTP) | `200`, `status == "COMPLETED"` | **Pass** — added 2026-09-23 (final review). |
| **AT-SFV24** | RN Case Manager (role=CASE_MANAGER, discipline=RN) completes | `test_complete_sfv_requirement_endpoint_authorized_rn_case_manager` | integration (backend, HTTP) | `200`, `status == "COMPLETED"` | **Pass** — added 2026-09-23; proves CASE_MANAGER qualifies only when the underlying discipline also qualifies (see P3-019). |
| **AT-SFV25** | LVN Case Manager (role=CASE_MANAGER, discipline=LVN) completes | `test_complete_sfv_requirement_endpoint_authorized_lvn_case_manager` | integration (backend, HTTP) | `200`, `status == "COMPLETED"` | **Pass** — added 2026-09-23. |
| **AT-SFV26** | Non-nursing Case Manager (role=CASE_MANAGER, discipline=SW) rejected | `test_complete_sfv_requirement_endpoint_non_nursing_case_manager_rejected` | integration (backend, HTTP) | `403`, requirement stays `OPEN` | **Pass** — added 2026-09-23; proves "Case Manager" is a job title, not itself a credential. |
| **AT-SFV27** | On-call RN completes | `test_complete_sfv_requirement_endpoint_on_call_rn_completes` | integration (backend, HTTP) | `200`, `status == "COMPLETED"` | **Pass** — added 2026-09-23; on-call status is operational routing, not a distinct authorization path (no dedicated on-call subsystem exists or is required). |
| **AT-SFV28** | On-call LVN completes | `test_complete_sfv_requirement_endpoint_on_call_lvn_completes` | integration (backend, HTTP) | `200`, `status == "COMPLETED"` | **Pass** — added 2026-09-23. |
| **AT-SFV29** | Chaplain rejected | `test_complete_sfv_requirement_endpoint_chaplain_rejected` | integration (backend, HTTP) | `403`, requirement stays `OPEN` | **Pass** — added 2026-09-23. |
| **AT-SFV30** | Volunteer (VOLUNTEER_COORDINATOR, closest existing role) rejected | `test_complete_sfv_requirement_endpoint_volunteer_rejected` | integration (backend, HTTP) | `403`, requirement stays `OPEN` | **Pass** — added 2026-09-23. |
| **AT-SFV31** | Platform/billing user (BILLING) rejected | `test_complete_sfv_requirement_endpoint_platform_user_rejected` | integration (backend, HTTP) | `403`, requirement stays `OPEN` | **Pass** — added 2026-09-23. |

Frontend companion, executed via `npx vitest run
src/components/SymptomFollowUpVisitSection.test.jsx` → **4 passed**, and
full suite `npm test -- --run` → **277 passed** (was 273 before this
file was added), plus `npm run build` → exit 0.

**Not yet executed / explicitly deferred, not fabricated:**
completion-before-trigger timing edge cases beyond what
`test_sfv_completion_visit_separation.py` already covers (AT-SFV7), and
browser-automated end-to-end (Playwright/Cypress-style) tests — no such
framework was found configured in this repository as of this pass; only
backend HTTP-integration-level and frontend component-level tests exist.

---

## 3. Status roll-up

| Status | Count |
|---|---|
| Pass (executed) | 35 (AT-A3, AT-D3, AT-E3, AT-F1, AT-SFV1–AT-SFV31) |
| Pass (static review only, explicitly labelled) | 1 (AT-A1) |
| Fail (by static trace — no executable test exists yet) | 9 |
| Not-yet-run | 6 |
| Blocked (no backend environment) | 0 |

**No test in this matrix is claimed as passing on the basis of code reading
alone except AT-A1, which is explicitly labelled "static".**
