# HOPE Export Gap Analysis

**Document Status:** ARCHITECTURE CORRECTION BASELINE — produced per the
"RNICA / HOPE ARCHITECTURE CORRECTION" directive (2026-09-23). Classified
as an **RNICA DEPENDENCY WORKSTREAM**, not a future enhancement, per that
directive: RNICA is not complete until its output can complete the HOPE
lifecycle.

## What "export" currently means in this repository

Two independent things are both called "export" today, and neither
produces a submission-ready artifact:

1. **Workflow-status export** — `apply_export_to_batch()`
   (`backend/app/services/rnica_hope_workflow_service.py:131-145`):
   requires the assessment to be locked and not already submitted, then
   sets `hope_exported_to_batch_at`, `hope_exported_to_batch_by`, and a
   **locally generated placeholder batch ID** (`f"HOPE-{str(record.id)[:8]}"`
   if none is supplied). No file, XML payload, or transmission artifact
   is produced by this call. It is a status flag, not an export.
2. **Human-readable report export** — `HopeReport.jsx` renders
   `mapRnIcaToHopeReport()`'s output on-screen; the only "export" action
   is `window.print()` (`HopeReport.jsx:214`), i.e. print-to-PDF via the
   browser. This is suitable for a human chart copy, not for a CMS
   submission format.

## Gaps

| Gap | Evidence | Severity |
|---|---|---|
| No CMS/iQIES submission file format is ever generated (no XML/JSON submission payload builder exists in `backend/app`) | Repository-wide search for `iQIES`/`iqies` returns no matches | HIGH |
| "Export to batch" does not validate the record before flipping the status flag — it only checks lock state and non-duplicate-submission, not HOPE content completeness | `rnica_hope_workflow_service.py:131-145` | HIGH |
| No validation stage precedes export (see `HOPE_FIELD_TRACE_MATRIX.md` gaps: incomplete response sets on A0810/A1005/A1010/A1110/M1195; unwired N0500/510/520; missing Z0400) — these can be exported today without any block | Cross-reference `HOPE_FIELD_TRACE_MATRIX.md` | HIGH |
| The exported SFV fields (J2052/J2053) are read from the legacy self-attested RNICA-form path, not the authoritative `SFVRequirement` completion outcome | `hopeReportMapper.js:618`; see `RNICA_HOPE_FIELD_MAP.md` §2 | CRITICAL — this means "export" can currently emit an SFV completion value that contradicts the backend's authoritative record |
| The "batch ID" is a locally generated string with no relationship to any real batch/submission system | `rnica_hope_workflow_service.py:139` | MEDIUM |
| No audit trail records the export action | `audit_events.py` is never called from the HOPE workflow endpoints in `visits.py` | MEDIUM (see `HOPE_AUDIT_GAP_ANALYSIS.md`) |

## What already works and should be reused, not replaced

- The item-code-keyed payload shape (`mapRnIcaToHopeReport()`'s output)
  is a reasonable starting schema for a real export payload — the gap is
  that it is computed client-side, per render, rather than persisted
  server-side as a validated, exportable record (see
  `RNICA_HOPE_LIFECYCLE.md` §4, recommendation 1).
- The `hope_exported_to_batch_at/_by`/`hope_export_batch_id` columns are
  a reasonable place to record *that* an export happened, once a real
  export artifact exists to point them at.

## Required before implementation

1. Decide whether HOPE Generation moves server-side first (recommended,
   per `RNICA_HOPE_LIFECYCLE.md`), or whether a server-side export step
   re-derives the payload independently as an interim measure.
2. Define the actual CMS/iQIES export file format required (out of scope
   for this document — requires CMS specification research, not
   repository tracing).
3. Add a validation stage (see `HOPE_EXPORT_GAP_ANALYSIS` gaps above and
   `HOPE_FIELD_TRACE_MATRIX.md`) that blocks export on incomplete/
   conflicting fields, run before `apply_export_to_batch()` — not merely
   the current lock-state check.
4. Re-point J2052/J2053 at `SFVRequirement` before any export redesign
   ships, since this is a correctness defect independent of the export
   format question.
