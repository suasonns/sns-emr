# RNICA / HOPE Lifecycle

**Document Status:** ARCHITECTURE CORRECTION BASELINE — produced per the
"RNICA / HOPE ARCHITECTURE CORRECTION" directive (2026-09-23). Records
the authoritative data flow and, stage by stage, what the repository
actually implements today versus the target single-lifecycle
architecture. RNICA and HOPE are documented here as **one lifecycle**,
not two independent projects.

## 1. Authoritative data flow (per directive)

```
Facesheet
  ↓  Patient demographics
RNICA
  ↓  Clinical assessment
HOPE Generation
  ↓
HUV
  ↓
SFV
  ↓
HOPE Validation
  ↓
HOPE Export
  ↓
iQIES Submission
  ↓
Acceptance / Rejection
  ↓
Correction / Resubmission
```

## 2. Stage-by-stage: current implementation vs. target

| Stage | Target | Current implementation | Gap classification |
|---|---|---|---|
| **Facesheet → Patient demographics** | Facesheet is the sole demographic source of truth | `Patient` model fields (name/SSN/Medicare/Medicaid/payer) are Facesheet-owned and read directly by `hopeReportMapper.js`. Some demographic fields (gender, race, ethnicity, language, living situation) are **RNICA-owned, not Facesheet-owned** — a second, RNICA-local demographics block exists on `RNICA.jsx:7987-7999` | **PRESENT, PARTIALLY DUPLICATED** — see `DUPLICATE_AUTHORITY_MATRIX.md` for the DUPLICATE_EDITABLE_AUTHORITY findings (e.g. A0550/A0900 editable in two places) |
| **RNICA → Clinical assessment** | RNICA is the sole clinical source of truth | Confirmed: `rnica_assessments.form_data` holds the full clinical assessment; no competing assessment screen exists for the fields this pass traced | **IMPLEMENTED** |
| **Clinical assessment → HOPE Generation** | A backend service derives a HOPE payload from RNICA `form_data` | **No backend service exists.** The only code that walks `form_data` and emits HOPE item-code-keyed content is a **frontend-only** function, `sns-emr-frontend/src/intake/hopeReportMapper.js:462-670` (`mapRnIcaToHopeReport`). Backend HOPE code is limited to item-code metadata (`form_registry.py:341-418`) and workflow-status bookkeeping (`rnica_hope_workflow_service.py`) | **GAP** — HOPE Generation is a client-side view, not a persisted server-side derived object. This is the central architectural correction this directive targets: HOPE must become a derived record, not a browser-computed report |
| **HOPE Generation → HUV** | HUV is a filtered subset of the derived HOPE object | `hopeReportMapper.js:657` filters out Section F (Preferences) for HUV1/HUV2, matching `HOPE_HUV_ITEM_CODES` (`form_registry.py:430-441`) | **IMPLEMENTED** (client-side only, inherits the HOPE Generation gap above) |
| **HUV → SFV** | SFV requirement generated from RNICA symptom-impact severity; completed on a separate, later, authorized-nursing-clinician visit | Implemented server-side: `hope_phase_b_engine.py` creates `SFVRequirement` rows from J2051 impact severity; `POST /visits/sfv-requirements/{id}/complete` enforces the separate-visit invariant and nursing-credential authorization (see `SNS_CONSTITUTION.md` §31) | **IMPLEMENTED** (this is the one stage remediated to full backend authority this session) |
| **SFV → HOPE Validation** | Completed SFV outcome (J2052/J2053) flows back into the derived HOPE object; a validation stage checks the assembled HOPE record against CMS submission rules before export | The exporter still reads the **legacy self-attested** `sfv.inPersonSfvCompleted`/`.sfvDate` fields from the triggering RNICA form (`hopeReportMapper.js:618`), not the authoritative `SFVRequirement` record. No CMS-rule validation pass exists anywhere in the repository | **GAP** (two gaps: (a) SFV completion outcome is not re-synced into the exportable HOPE object; (b) no validation stage exists at all — see `HOPE_EXPORT_GAP_ANALYSIS.md`) |
| **HOPE Validation → HOPE Export** | A validated HOPE record is exported to a batch/file suitable for iQIES submission | `apply_export_to_batch()` (`rnica_hope_workflow_service.py:131-145`) only flips workflow-status columns (`hope_exported_to_batch_at/_by`, `hope_export_batch_id` — a locally generated placeholder ID, e.g. `f"HOPE-{id[:8]}"`) and requires the record already be locked. **No file, payload, or transmission artifact is produced.** The only concrete export output anywhere is the browser-rendered `HopeReport.jsx`, printable via `window.print()` | **GAP** — "export" today means a workflow-status flag plus an on-screen printable report, not a submission-ready artifact |
| **HOPE Export → iQIES Submission** | The exported HOPE record is transmitted to CMS's iQIES system and a submission receipt is recorded | **No iQIES integration exists.** A repository-wide search for `iQIES`/`iqies` returns no matches in `backend/app`. `apply_submission_update()` only accepts a manually-typed `submission_number` string (`rnica_hope_workflow_service.py:147-161`) — there is no outbound call, no receipt parsing, and no automated confirmation | **GAP** — submission is a manual data-entry field, not a system integration. See `HOPE_SUBMISSION_GAP_ANALYSIS.md` |
| **Submission → Acceptance / Rejection** | The system records CMS acceptance/rejection and surfaces validation errors | `RnicaAssessment.hope_validation_status`, `.hope_accepted_at`, `.hope_rejected_at` columns exist (with a mutual-exclusion check constraint) but **no service or API in the repository reads or writes them** — confirmed by a full-tree grep returning only the model declaration | **GAP — schema-ready, logic-absent** |
| **Acceptance/Rejection → Correction / Resubmission** | A rejected HOPE record can be corrected and resubmitted, with the correction and prior attempt both traceable | `RnicaAssessment.hope_correction_required`/`.hope_corrected_assessment_id` and the entire `RnicaHopeSubmissionAttempt` child table (attempt number, receipt reference, validation status, correction reason, `supersedes_attempt_id`) exist as schema but are **never populated** (grep of `backend/app` finds only the model file). A **separate, unrelated** correction mechanism (`RnicaAmendment` / `rnica_amendment_service.py`) exists for RNICA **clinical** corrections (PENDING/APPROVED/DENIED workflow) but is not wired to the HOPE submission-correction columns at all | **GAP — two disconnected correction concepts**: clinical amendment (implemented) vs. HOPE submission correction/resubmission (schema-only). See `HOPE_CORRECTION_GAP_ANALYSIS.md` |

## 3. What is already correct about the "single lifecycle" principle

- RNICA is already the sole clinical source of truth for the fields this
  pass traced (no second assessment screen competes with it).
- The SFV segment of the lifecycle has already been remediated this
  session to the target architecture: one authoritative backend record
  (`SFVRequirement`), a separate-visit invariant, and credential-based
  authorization — not a second charting system.
- HOPE Generation, HUV filtering, and the printable report are already
  **computed from** RNICA `form_data`, not independently authored. There
  is no evidence of HOPE being maintained as a second, competing source
  of truth for clinical content. The correction needed is architectural
  placement (client-only → server-side derived record) and completing
  the downstream stages, not eliminating duplicate clinical entry that
  does not currently exist.

## 4. What must change for the target architecture

1. Move `mapRnIcaToHopeReport()`'s logic (or an equivalent) server-side so
   a HOPE record is a **persisted derived object**, not a per-render
   browser computation — this is the prerequisite for validation,
   export, and audit to operate on a stable, referenceable payload.
2. Re-point the SFV fields (J2052/J2053) at the authoritative
   `SFVRequirement` completion outcome instead of the legacy
   self-attested `sfv.*` path.
3. Build the missing "HOPE Validation" stage (CMS submission-rule checks
   run against the derived HOPE object before export is allowed).
4. Wire `hope_validation_status`/`hope_accepted_at`/`hope_rejected_at` (or
   retire them in favor of `RnicaHopeSubmissionAttempt`, but not both
   silently) to a real iQIES submission integration or, at minimum, a
   structured manual receipt-entry workflow with validation.
5. Connect the correction/resubmission columns and
   `RnicaHopeSubmissionAttempt` table to an actual UI/API surface, and
   decide whether `RnicaAmendment` should be the correction mechanism for
   HOPE-level rejections too, or whether the two remain intentionally
   separate (clinical correction vs. submission correction) — this
   decision is required before implementation, per
   `HOPE_CORRECTION_GAP_ANALYSIS.md`.
6. Add `audit_event()` calls to every HOPE workflow transition
   (close/ready/export/submission-update/unlock/inactivation) in
   `visits.py` — none exist today (`HOPE_AUDIT_GAP_ANALYSIS.md`).

See `TOP_20_RNICA_HOPE_BLOCKERS.md` for these items prioritized with
severity, owner, dependency, and release impact.
