# RNICA_IMPLEMENTATION_PLANNING_HANDOFF.md

**Status:** Process document for the implementation-planning documentation
gate. Documentation-only; does not authorize application code.

## 1. Package covered by this handoff

Documentation pull request contents:
1. `RNICA_PHASED_IMPLEMENTATION_PLAN.md` (updated: verified files/
   components/services and historical-record handling added per
   increment; ACP increment reconciled against the six-field decision)
2. `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md` (new)
3. `RNICA_IMPLEMENTATION_PLANNING_HANDOFF.md` (this file, new)
4. `RNICA_DATA_MAPPING_MATRIX.md` (updated: ACP row reflects six-field target)
5. `RNICA_LOCK_READINESS_MATRIX.md` (updated: ACP row reflects six-field target)
6. `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md` (updated: Discovery Item 7 resolved)

No application code, schema, or migration is modified in this pull request.

## 2. Verified reusable foundation (restated, unchanged)

Preserve and reuse without independent rebuild:
- Autosave (`useAssessmentAutosave.ts`, 30s interval)
- Lock / Compliance & Readiness server parity
  (`evaluate_finalization_readiness` shared by both)
- Locked-record protection (423 on `PUT`/`DELETE`)
- Amendment workflow (`rnica_amendment.py`, `rnica_amendment_service.py`)
- Explicit-action-only POC adapter (`rnica_poc_adapter.py`, `rnica_poc.py`)
- Non-verdict LCD evidence engine (`detectLCD`/`evaluateLCD`/`getLCDConfig`)
- Structured Findings pipeline (`applyStructuredFindings.js`,
  `CONCEPT_REGISTRY`)
- 16 backend + 1 frontend RNICA test files

## 3. Confirmed defects carried forward

| # | Defect | Current behavior | Target behavior | Affected files/services | Historical-record impact | Automated tests | Feature-flag/rollback |
|---|---|---|---|---|---|---|---|
| 1 | ECOG lacks server-side Lock enforcement | No enforcement branch in `_validate_required_functional_assessments` | Enforce ECOG when oncology/metastatic/hematologic diagnosis, mirroring FAST/NYHA pattern | `clinical_note_validation_engine.py` | None — new enforcement applies prospectively to unlocked/new assessments only; already-locked records unaffected | New backend test mirroring existing FAST/NYHA conditional tests | Own flag, independent of navigation-shell flag (this is a Lock-blocking behavior change) |
| 2 | Autosave resets assessment status to DRAFT | `record.status = "DRAFT"` set unconditionally on every non-locked `PUT`, including trivial autosave ticks (`visits.py:1118`) | `status` reflects intended draft/submitted semantics without being reset by autosave-only writes | `backend/app/api/visits.py` | Requires care: any downstream logic reading `status` today may rely on the current (defective) behavior — must be audited before the fix ships, not assumed safe | Regression test asserting `status` unaffected by autosave-only updates | Own flag; verify no downstream consumer depends on current behavior before removing it |
| 3 | ACP server enforcement covers 3 of the approved 6 target values | `RN_ICA_REQUIRED_FIELD_GROUPS` enforces Code Status, Life-Sustaining Treatment Preference, Hospitalization Preference only | All 6 target values enforced (see `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md`) | `clinical_note_validation_engine.py` (server), `RNICA.jsx` (client, currently enforces only `lifeSustainingAskedStatus`) | Applied prospectively only per the reconciliation decision §8; no rewrite of signed/locked records | New Lock-blocker tests for the 3 newly-enforced discussion-status fields | Own flag; ships only after the reconciliation decision's 4 open items are resolved |

## 4. Fall Risk / Morse — status unchanged

Remains classified **BLOCKED BY AUTHORITY DECISION**. A validated
instrument may display its own score/interpretation; RNICA must not create
a new aggregate risk-scoring engine; it becomes a Lock blocker only if
controlling authority or approved agency policy explicitly requires
completion for that assessment. No new hard blocker may be implemented
based only on Figma presentation. This item is not resolved by this
handoff and remains a gate condition for Increment 8.

## 5. Locked implementation rules (restated, unchanged)

- Finalization owns the sole active Final Clinical Narrative at
  `finalization.clinicalNarrative`.
- Diagnosis & LCD owns the LCD Supporting Narrative only.
- RNICA Intelligence remains advisory; must not determine eligibility,
  prognosis, or physician certification.
- Orders and POC changes require explicit user action.
- Manual clinical entries must not be silently overwritten.
- Historical, locked, and amended records must remain readable and
  auditable.
- Current repository behavior is discovery evidence; approved product
  authority defines the target.
- Use forward-only migrations; do not rewrite migration history.

## 6. LCD language (restated, unchanged)

Use: "LCD Supporting Evidence Present", "Evidence alignment identified",
"Supports LCD documentation review", "Physician certification remains
required."
Do not use: "Eligible", "Eligibility confirmed", "LCD match: high",
"Satisfies LCD", "AI-generated prognosis." The implementation must present
patient-specific observations and supporting evidence rather than
substitute RNICA output for physician certification.

## 7. Finalization requirements (restated, unchanged)

Re-run authoritative server validation at Lock; reject stale client-only
readiness; preserve assessment state when Lock fails; return structured
blocker identifiers and source targets; never infer attestation or
signature; prevent direct modification of locked records; preserve
original records during amendments; audit actor/timestamp/version/action/
amendment reason; preserve written justification for denied correction/
amendment requests where required. The assessment, POC approval, signed
clinical records, and amendment history must remain traceable and
distinct — all confirmed already true in current code (see
`RNICA_LOCK_READINESS_MATRIX.md` §4, §6).

## 8. Application-coding gate

Application coding begins only after:
- `RNICA_PHASED_IMPLEMENTATION_PLAN.md` is approved.
- `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md` is approved.
- Critical `RNICA_DATA_MAPPING_MATRIX.md` placeholders are resolved.
- Critical `RNICA_LOCK_READINESS_MATRIX.md` placeholders are resolved.
- Fall Risk / Morse is decided or explicitly deferred (currently deferred,
  explicitly, as `BLOCKED BY AUTHORITY DECISION`).
- Latest Figma production-candidate frames are identified and superseded
  frames are marked (tracked in `RNICA_GITHUB_HANDOFF_PLAN.md` §E; not
  independently re-verified in this pass).
- The first implementation increment (shell/nav) has no unresolved
  authority blocker — confirmed none exists for Increment 1.
- Feature-flag and rollback strategy is accepted for each increment (see
  `RNICA_PHASED_IMPLEMENTATION_PLAN.md` per-increment entries).

## 9. Patient Chart gate — unchanged

Patient Chart workflow design may begin after this implementation-planning
documentation gate closes. RNICA does not need to be fully coded first.
The Patient Chart phase must use:
- `PATIENT_CHART_AUTHORITY_MAP.md` as ownership authority
- RNICA as the workflow-first proof of concept
- `PATIENT_CHART_WORKFLOW_AUTHORITY.md` as future workflow authority (not
  yet created; to be created only after this gate closes)

## 10. Final status

RNICA implementation planning documentation: **ready for documentation-
only pull request.**
Application code: **not yet authorized.**
Patient Chart workflow: **may begin after this documentation gate is
approved** — not before.
