# Dead Code Removals

Permanent log of production code removed because it was proven unreachable.
Every entry must show proof before removal is allowed — no code is removed on
suspicion alone.

---

## `AdmissionWorkflowService.start_soc()`

**Removed:** 2026-09-09

**File:** `backend/app/services/admission/admission_workflow_service.py`

**Reason:** Duplicate/parallel SOC-writing path that was never wired to any
route, superseded by `AdmissionGuardrailService.set_soc_datetime()` (Path A
in the SOC Entry Analysis). Keeping it around risked a future caller
accidentally writing `admission.soc_date` through a path with no SOC gate
enforcement (violates Single Source of Truth for SOC — see
`docs/workflows/SourceOfTruthMatrix.md`).

**Proof (SOC Entry Analysis, 2026-09-09):**
- No API caller — grepped every `app/api/*.py`; the only same-named symbol
  is the unrelated FastAPI route handler `start_soc()` in
  `app/api/admission.py:199`, which calls
  `AdmissionGuardrailService.set_soc_datetime()`, not this method.
- No frontend caller — grepped `sns-emr-frontend/src` for `start-soc`,
  `startSoc`, `soc-orders`, `rn-admission`, and `soc_date`/`socDate` write
  usage; every hit found was a read-only display value.
- No workflow caller — grepped all of `backend/app/` for
  `AdmissionWorkflowService.start_soc` / `.start_soc(`; the only match
  outside this file's own definition was the unit test removed alongside it.
- No scheduled caller — no Celery/cron/task-runner references.
- No integration caller — no references outside `backend/`.
- No production caller — confirmed by all of the above.

**Replacement:** `AdmissionGuardrailService.set_soc_datetime()` (Path A) and
`authorize_admission()` (Path B) remain the two real SOC-establishment
entry points; both now call the shared `SOCValidationService` so the same
rule enforces regardless of which one fires, per the SSOT directive.

**Test removed alongside:** `test_start_soc` in
`backend/tests/services/admission/test_admission_workflow_service.py`
(the only caller of the removed method).
