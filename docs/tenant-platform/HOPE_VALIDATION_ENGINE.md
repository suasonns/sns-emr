# HOPE Validation Engine — Design

**Document Status:** DESIGN ONLY — NO IMPLEMENTATION. Produced per the
"RNICA \u2192 HOPE REDESIGN EXECUTION DIRECTIVE" (2026-09-23), Priority 4.
Confirms the finding in `HOPE_EXPORT_GAP_ANALYSIS.md`/
`RNICA_HOPE_LIFECYCLE.md`: no HOPE validation stage exists anywhere in
the repository today. Export happens directly from raw `form_data` with
no pass/fail gate. This document designs `HopeValidationService` —
no code is written by this document.

## Position in the lifecycle

```
HopeGenerationService ──▶ HOPE Projection ──▶ HopeValidationService ──▶ (pass) Export
                                                        │
                                                        └─▶ (fail) FAILED_VALIDATION, blocks Export
```

`HopeValidationService` consumes a `HopeProjection` (see
`HOPE_GENERATION_SERVICE_DESIGN.md`) and produces a validation result:
a list of findings, each with a rule id, severity, and pass/fail
status, plus an overall `validation_status` (`PASSED` /
`FAILED` / `PASSED_WITH_WARNINGS`).

## Validation domains (per directive)

| Domain | What it must check | Severity if failed |
|---|---|---|
| **Demographics** | Required Facesheet-sourced fields present (name, MRN/patient id, DOB, payer/insurance identifiers required for HOPE submission) | BLOCKING |
| **Chronology** | Required dates are internally consistent — admission date precedes assessment date; SFV `completed_at` falls after the triggering RNICA assessment's date; certification effective dates do not overlap invalidly | BLOCKING |
| **Signatures** | Required attestations/signatures exist and are authenticated (ties into existing "documentation permission"/"authentication permission" checks established during the P3-009 SFV remediation — reused, not reinvented) | BLOCKING |
| **HUV1** | Required Historical/admission Hospice Utilization Visit fields present per `HOPE_FIELD_TRACE_MATRIX.md`/`RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md` | BLOCKING |
| **HUV2** | Required second-visit fields present, same source | BLOCKING |
| **SFV** | `SFVRequirement.status == COMPLETED` with a valid `completed_visit_id` that differs from the triggering visit (`triggerVisitId != completionVisitId`, the invariant established during P3-009); J2052 status/date sourced from `SFVRequirement` (not a stale denormalized copy); J2053 present and attributed to the completion visit, not the triggering visit — this last check is a hard **dependency** on the J2053 schema/capture fix in `P1_J2052_J2053_REMEDIATION_PLAN.md`; until that fix ships, this rule cannot pass and must be explicitly reported as `BLOCKED_ON_UPSTREAM_GAP`, not silently skipped | BLOCKING |
| **Required HOPE fields (general)** | Every field enumerated in `RNICA_HOPE_FIELD_MAP.md`/`HOPE_DATA_PROVENANCE_MATRIX.md` that is marked required has a non-null value in the projection | BLOCKING (per-field) or WARNING (per field, if the field-map marks it as CMS-optional) |
| **Export eligibility** | Composite gate: record is not already `SUBMITTED`/`ACCEPTED` (would require the correction path instead, see `HOPE_SUBMISSION_LIFECYCLE.md`); record is not locked pending an unrelated amendment; tenant/patient access has not been revoked since generation | BLOCKING |

## Rule model (design only)

Each rule is a discrete, named, independently testable unit:

| Attribute | Description |
|---|---|
| `rule_id` | Stable identifier, e.g. `SFV_SEPARATE_VISIT_REQUIRED`, `SFV_J2053_PRESENT`, `DEMOGRAPHICS_MRN_PRESENT` |
| `domain` | One of the seven domains above |
| `severity` | `BLOCKING` (prevents export) or `WARNING` (export allowed, finding recorded) |
| `input` | The specific `HopeProjection` field(s)/source record(s) it reads |
| `pass_condition` | Plain-language condition (implementation detail deferred) |
| `failure_message` | User-facing explanation surfaced back to the clinician/administrator |

This mirrors the same "named, independently visible" testing
philosophy already established and explicitly required for the SFV
authorization test suite during P3-009 (`SNS_CONSTITUTION.md` §31) —
validation rules should not be collapsed into one opaque "is valid"
boolean; each rule must be independently reportable, matching the
directive's general preference for explicit, named, non-collapsed
checks over parameterized/opaque ones.

## Blocking vs. warning behavior

- **BLOCKING** findings prevent `HopeGenerationService`'s projection
  from transitioning to `READY`/`VALIDATED` state (see
  `HOPE_SUBMISSION_LIFECYCLE.md`) — export cannot proceed.
- **WARNING** findings are recorded and surfaced but do not block
  export — reserved for fields the field-map marks as CMS-optional or
  for known, accepted upstream gaps (e.g., while the J2053 capture-path
  fix is pending, the SFV domain may need a transitional `WARNING`
  classification for the J2053 presence check rather than `BLOCKING`,
  as an explicit, visible, temporary carve-out — **this is a product
  decision, not decided by this document**, and should default to
  `BLOCKING` unless explicitly relaxed with sign-off, since a silent
  warning-only gap is exactly the kind of masked defect this whole
  audit effort was meant to surface).

## Output (design only)

A `HopeValidationResult` associated 1:1 with a `HopeProjection`
version:

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `hope_projection_id` | FK | |
| `validated_at` | timestamp | |
| `overall_status` | enum | `PASSED` / `FAILED` / `PASSED_WITH_WARNINGS` |
| `findings` | JSONB array | one entry per rule evaluated, each with `rule_id`, `domain`, `severity`, `passed` (bool), `message` |

This reuses the existing `RnicaAssessment.hope_validation_status`
column's *intent* (currently dead, per `HOPE_SUBMISSION_GAP_ANALYSIS.md`)
but attaches it to the new `HopeProjection`/`HopeValidationResult`
records rather than the source `RnicaAssessment` row directly, since a
single RNICA assessment may have multiple HOPE projection attempts over
time (regenerations, corrections) each needing their own validation
outcome — the old single-column design could not represent that
history.

## What this document does NOT do

- Does not implement any validation rule logic.
- Does not decide the exact CMS field-requirement list (per
  `TOP_20_RNICA_HOPE_BLOCKERS.md` #20, that requires external CMS
  specification research as a prerequisite content-authoring task, not
  a code-design task).
- Does not resolve whether J2053's temporary classification (BLOCKING
  vs. WARNING) should be relaxed during the gap period — flagged above
  as a product decision requiring explicit sign-off.

## Dependency on Priorities 1 and 3

This engine validates `HopeProjection` records produced by
`HopeGenerationService` (Priority 3) — it has no independent input
source. Its SFV domain rules are directly blocked by the same J2052/
J2053 gaps tracked in `P1_J2052_J2053_REMEDIATION_PLAN.md`.
