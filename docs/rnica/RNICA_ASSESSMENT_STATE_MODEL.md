# RNICA Assessment State Model

**STATUS:** DISCOVERY / AUTHORITY REFERENCE ONLY. NOT IMPLEMENTATION AUTHORIZATION.

## 1. Purpose

Define authority concepts for assessment, contribution, package, HOPE, and
finalization states without creating database enums. This document is a
discovery artifact for design review — it does not create, migrate, or
alter any schema, enum, or state-machine implementation.

## 2. Assessment States

- `NOT_APPLICABLE`
- `NOT_STARTED`
- `CANDIDATE`
- `REVIEW_REQUIRED`
- `IN_PROGRESS`
- `COMPLETED`
- `FINALIZED`
- `CORRECTED`
- `AMENDED`
- `VOIDED`
- `MISSED_WINDOW`
- `BLOCKED`
- `SUPERSEDED`

## 3. Discipline-Contribution States

Applies independently to each of:

- RNICA
- MSW ICA
- SC ICA
- Other required contribution

States: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `EXEMPTED_WITH_REASON`,
`BLOCKED`, `CORRECTED`, `AMENDED`.

## 4. Comprehensive-Assessment Package States

- `NOT_STARTED`
- `IN_PROGRESS`
- `COMPLETE`
- `BLOCKED`
- `CORRECTED`
- `AMENDED`

Package = `COMPLETE` only when all required discipline contributions are
`COMPLETED` or `EXEMPTED_WITH_REASON`.

## 5. HOPE States

### HOPE Admission

`NOT_STARTED` → `IN_PROGRESS` → `COMPLETED` → `CORRECTED`/`AMENDED`.

### HUV1

`NOT_APPLICABLE` (outside Days 6-15) → `CANDIDATE` (visit occurs in
window) → `REVIEW_REQUIRED` (prompt shown) → `COMPLETED` (confirmed) or
`MISSED_WINDOW` (window closes unconfirmed).

### HUV2

Same shape as HUV1, scoped to Days 16-30.

### SFV

`NOT_APPLICABLE` → `CANDIDATE` (moderate/severe symptom trigger,
`REPOSITORY_CURRENT_STATE`: maps to `SFVRequirement.status = PENDING`) →
`COMPLETED` (`REPOSITORY_CURRENT_STATE`: maps to `SFVRequirement.status =
COMPLETE`, not yet observed in code as a literal value — see
`RNICA_HOPE_SOURCE_VALIDATION_GAPS.md` G-08 for the "reason not completed"
field gap).

## 6. Finalization States

- Draft
- Under Review
- Validation Required
- Finalized
- Corrected
- Amended
- Superseded
- Voided

## 7. Allowed Transitions

- `NOT_STARTED` → `IN_PROGRESS` → `COMPLETED`/`FINALIZED`.
- `CANDIDATE` → `REVIEW_REQUIRED` → `COMPLETED` (confirmed) or
  `MISSED_WINDOW` (window closes) or back to `NOT_APPLICABLE`-equivalent
  "declined with reason" (not a listed state; tracked as an attribute on
  `REVIEW_REQUIRED`, not a separate terminal state, pending further design).
- `FINALIZED` → `CORRECTED`/`AMENDED`/`VOIDED`/`SUPERSEDED` via an
  authorized workflow only.
- `BLOCKED` → `IN_PROGRESS` only after authorized correction/reassignment.

## 8. Blocked Transitions

- `FINALIZED` → `IN_PROGRESS`/`NOT_STARTED` directly (no silent overwrite;
  rules doc §11).
- `COMPLETE` (package) → `NOT_STARTED` (package) directly (rules doc §6,
  §10 — no silent restart).
- Any transition into `COMPLETED`/`FINALIZED` for HUV1/HUV2 without an
  explicit confirming user action (rules doc §7.2/§7.3).
- Any transition where authenticated discipline conflicts with assigned
  discipline (rules doc §9) — remains `BLOCKED` until resolved.

## 9. Duplicate Prevention

- One `PENDING`/active SFV requirement per patient+symptom
  (`REPOSITORY_CURRENT_STATE`, `sfv_engine.py`).
- One HUV1 and one HUV2 completed record per election episode (target
  rule; code enforcement `PENDING_SOURCE_VALIDATION`, see
  `RNICA_HOPE_SOURCE_VALIDATION_GAPS.md` G-01/G-02).
- No re-creation of a `COMPLETE` Initial Comprehensive Assessment package.

## 10. Post-Finalization Controls

Post-finalization changes must use one of: Correction, Amendment,
Addendum, Void, Replacement, Re-finalization. Each must preserve the prior
finalized version rather than overwrite it (rules doc §11).

## 11. Audit Events

Every transition in §7 must record: actor, timestamp, reason (where
applicable — e.g. HUV decline, discipline mismatch, exemption), and source
evidence reference. This is a documentation requirement for future design;
it does not itself implement an audit log.

## 12. Mapping to Current Repository Values

| Authority Concept | Current Repository Value | Location | Gap | Decision Needed |
| --- | --- | --- | --- | --- |
| SFV requirement status | `status = "PENDING"` (literal string, not enum) | `backend/app/services/sfv_engine.py`, `backend/app/models/sfv_requirement.py` | No confirmed `COMPLETE`/"reason not completed" literal observed in this discovery pass | Confirm full status value set on `SFVRequirement` |
| HUV1/HUV2 task type | `TASK_TYPE_HUV1`, `TASK_TYPE_HUV2` string constants | `backend/app/services/hope_phase_b_engine.py` | No day-window (6-15 / 16-30) enforcement located | Confirm whether window logic exists elsewhere or is not yet built |
| Discipline sources (RN/LVN/LPN) | `DISCIPLINE_RN`, `DISCIPLINE_LVN`, `DISCIPLINE_LPN` constants | `backend/app/services/hope_phase_b_engine.py` | Discipline-authority enforcement (rules doc §9) not traced | Confirm RBAC integration point |
| Visit mode | `VISIT_MODE_IN_PERSON` constant | `backend/app/services/hope_phase_b_engine.py` | Relationship to HUV1/HUV2 in-person requirement not traced | Confirm usage in HUV eligibility logic, if any |

## 13. Implementation Boundary

Do not create or change enums during discovery. `NOT_AUTHORIZED`.
