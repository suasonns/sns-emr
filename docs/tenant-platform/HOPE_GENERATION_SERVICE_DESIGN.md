# HOPE Generation Service — Design

**Document Status:** DESIGN ONLY — NO IMPLEMENTATION. Produced per the
"RNICA \u2192 HOPE REDESIGN EXECUTION DIRECTIVE" (2026-09-23), Priority 3.
Confirms and addresses the finding in `RNICA_HOPE_LIFECYCLE.md`/
`HOPE_EXPORT_GAP_ANALYSIS.md`: HOPE generation today exists **only** in
the frontend (`hopeReportMapper.js`), invoked on-demand by
`HopeReport.jsx`/`ComplianceHopeBoard.jsx`. There is no server-side
generation, persistence, or generation-time record of what was
generated. This document proposes a `HopeGenerationService` design
only — no code is written or scheduled by this document.

## Why frontend-only generation is a defect, not a convenience

- **No persisted HOPE record exists.** Every render recomputes the HOPE
  projection from live `form_data`; there is nothing to validate,
  audit, submit, or version.
- **No non-UI trigger path.** A batch job, a scheduled export, or an
  API-driven integration (e.g. future iQIES submission) has no service
  to call — the only "generation" logic lives inside a React component
  tree.
- **No point-in-time snapshot.** If underlying RNICA/Facesheet/SFV data
  changes after generation but before submission, there is no way to
  detect drift, because nothing was actually saved at generation time.
- **J2052 dependency (see `P1_J2052_J2053_REMEDIATION_PLAN.md`):** the
  current UI-only generation path is the *reason* the fragile
  `SfvStatusCard` sync currently "works" — because export cannot happen
  without the RNICA screen (and thus the sync effect) having rendered
  first. Server-side generation removes that accidental safety net and
  makes the direct-`SFVRequirement`-read fix mandatory, not optional.

## Target architecture

```
Facesheet ──┐
            ├─▶ HopeGenerationService ──▶ HOPE Projection (persisted)
RNICA ──────┤                                   │
            │                                   ▼
Follow-Up   │                             HopeValidationService
Visits ─────┤                                   │
            │                                   ▼
Certification┘                              HOPE Export
```

`HopeGenerationService` is the **single** place that reads clinical
source data (Facesheet, RNICA, `SFVRequirement`/completion visits,
certification records) and produces a HOPE projection. It replaces
`hopeReportMapper.js` as the source of truth for field derivation;
`hopeReportMapper.js`'s logic should be **ported**, not duplicated —
the field-mapping rules already encoded there (J2051 symptom-impact
evaluation, J2052/J2053 derivation, HUV1/HUV2 mapping, etc.) are the
correct starting point for the service's transformation rules, per
`RNICA_HOPE_FIELD_MAP.md`.

## Responsibilities

1. **Input assembly.** Given a patient + assessment context (admission
   RNICA assessment id, and the current `SFVRequirement` cycle if
   applicable), gather all source records needed: Facesheet
   demographics, the RNICA assessment's `form_data`, the relevant
   `SFVRequirement` (status/completed_at/symptom_impact once added per
   the P1 plan), and certification records.
2. **Transformation.** Apply the same field-by-field derivation rules
   currently in `hopeReportMapper.js`, ported to a backend service
   function/module. No new derivation logic is invented here — this is
   a relocation of existing, working logic to a place where it can be
   persisted, versioned, and reused by non-UI callers.
3. **Persistence.** Write a new `HopeProjection` record (see "Proposed
   schema" below) representing the generated-at-this-point-in-time HOPE
   dataset, distinct from the live source data it was derived from.
4. **Generation event.** Emit a `GENERATED` audit event (see
   `HOPE_AUDIT_EVENT_MATRIX.md`) recording actor, timestamp, and the
   generated projection's id.
5. **Idempotency / regeneration.** Support regenerating a projection
   (e.g. source data changed before submission) — each regeneration
   creates a new `HopeProjection` version rather than mutating the
   prior one in place, preserving history for audit.

## Proposed schema (design only — no migration performed)

A new table, tentatively `hope_projections`:

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `patient_id` | FK | |
| `tenant_id` | FK | matches existing tenant-scoping pattern used elsewhere in the schema |
| `source_rnica_assessment_id` | FK | the RNICA assessment this projection was derived from |
| `source_sfv_requirement_id` | FK, nullable | the SFV cycle this projection incorporates, if applicable |
| `version` | integer | incremented on regeneration |
| `generated_at` | timestamp | |
| `generated_by` | FK to user | |
| `payload` | JSONB | the full derived HOPE field set (structure mirrors `hopeReportMapper.js`'s current output shape) |
| `validation_status` | enum, nullable | populated by `HopeValidationService`, not this service — kept here for a fast current-state read, not as a substitute for the audit trail |
| `superseded_by_id` | FK to self, nullable | points to the newer version when regenerated, mirroring the existing `RnicaHopeSubmissionAttempt.supersedes_attempt_id` pattern already present in the schema |

This reuses the same "row-per-attempt with a supersession pointer"
pattern already established (and already unused) in
`RnicaHopeSubmissionAttempt` — per the directive's own instruction not
to re-design capacity that already exists in the schema, this design
deliberately mirrors that pattern rather than inventing a new one.

## Interfaces (design only)

- `HopeGenerationService.generate(patient_id, rnica_assessment_id) -> HopeProjection`
  — synchronous, callable from: (a) the existing on-screen
  `HopeReport.jsx`/`ComplianceHopeBoard.jsx` flows (replacing their
  direct call into `hopeReportMapper.js` with an API call to this
  service), (b) a future batch/scheduled job, (c) a future
  submission-pipeline trigger.
- `HopeGenerationService.regenerate(projection_id) -> HopeProjection` —
  creates a new version, marks the prior one superseded.

## What this document does NOT do

- Does not implement any code.
- Does not decide the exact JSONB payload shape (that is a 1:1 port of
  `hopeReportMapper.js`'s existing output, to be done at implementation
  time).
- Does not resolve the J2052/J2053 data gaps — those are tracked
  separately in `P1_J2052_J2053_REMEDIATION_PLAN.md` and are a
  **prerequisite** for this service to produce correct output for
  those two fields.
- Does not address validation, audit persistence, or submission — see
  `HOPE_VALIDATION_ENGINE.md`, `HOPE_AUDIT_EVENT_MATRIX.md`, and
  `HOPE_SUBMISSION_LIFECYCLE.md`.

## Dependency on Priority 1

This service cannot be safely implemented until the J2052 structural
fix (read `SFVRequirement` directly, not `form_data.sfv.*`) is in place
— otherwise the service would simply relocate the existing fragile
sync problem into a new persisted record. J2053's schema gap must also
be resolved (or explicitly deferred with a documented placeholder) before
this service can produce a complete HOPE projection.
