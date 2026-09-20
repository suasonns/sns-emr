# RNICA_AI_GOVERNANCE.md

**Status:** Binding RNICA implementation guardrail (v2 — repository-validated)
Supersedes v1 (commit `7836ca1`).

## 1. Current role (confirmed)

RNICA Intelligence is an advisory rules/heuristics layer, surfaced via
`getRnicaIntelligence` → `intelligence` state in `RNICA.jsx`, and a separate
Structured Findings signal-review pipeline
(`intelligence.structured_findings_signals`, `applyStructuredFindings.js`,
`CONCEPT_REGISTRY` in `structuredFindingRegistry.generated.js`). It does not
replace clinical judgment, physician certification, validation, or lock
readiness.

## 2. Authorized triggers

- Load (page/record open)
- Explicit Save/autosave completion where currently wired (autosave fires
  every 30000ms via `useAssessmentAutosave.ts`, confirmed below)
- Lock/readiness processing where currently wired
  (`getRnicaFinalizationReadiness`, same evaluator the server Lock endpoint
  re-runs)

The interface must not claim that RNICA Intelligence updates continuously
while typing unless that capability is separately implemented and approved.
No continuous/keystroke-driven intelligence refresh was found in
`RNICA.jsx` — `intelligence` is only set from explicit
`getRnicaIntelligence()` calls, not from a `formData` change effect.

## 3. Authorized outputs

- Documented findings requiring review
- Missing evidence
- Documentation gaps
- Suggested follow-up
- Compliance signals
- LCD supporting evidence alignment (`evaluateLCD` response — a criteria
  facts/match structure, confirmed non-verdict shaped in
  `src/api/eligibility.ts`)
- Structured findings already authorized by the repository contract
  (`CONCEPT_REGISTRY`)
- Source evidence and last-refreshed status

## 4. Prohibited outputs

- Hospice eligibility determination
- Terminal-prognosis generation
- Physician certification
- Final Clinical Narrative generation or ownership
- New aggregate risk scores
- Caregiver burden/sustainability scores
- Diagnoses presented as AI conclusions
- Automatic attestation, signature, lock, order, or POC action — confirmed:
  Lock (`visits.py:1178-1250`) never invokes POC generation, and no code
  path invokes `lockRnicaAssessment` without an explicit user-initiated
  API call
- Claims of chart-wide AI coverage

## 5. Required language

Preferred: "Advisory finding", "For clinician review only", "Supporting
evidence identified", "Documentation aligns with LCD support criteria",
"Physician certification remains required", "Suggestion, not mandated."

Prohibited: "Eligible", "Eligibility confirmed", "LCD match: high",
"Satisfies LCD", "Predicted prognosis", "AI-certified."

## 6. Evidence and explainability

Every advisory output must include or resolve to: rule identifier, source
field(s), source record/date when available, trigger/freshness timestamp,
recommended destination for clinician review. Confirmed supporting
infrastructure already exists for Structured Findings: `signal.source_type`,
`signal.original_text_excerpt`, `signal.recorded_at`,
`finding?.confidence`, `signal.id` are all captured into
`structuredFieldProvenance` entries (`RNICA.jsx`,
`handleApplyStructuredSignal`) — this provenance object is the pattern any
new AI Action Center output must follow.

## 7. Mutation safety (confirmed)

- Recommendations never mutate clinical records automatically —
  applying a structured finding is a click-through, user-initiated action
  (`handleApplyStructuredSignal`), not an automatic write.
- Order/POC actions require explicit user initiation
  (`viewRnicaSectionPoc`/`addRnicaSectionPocProblem`/etc. are all called
  from explicit button handlers, never from an effect).
- Manual clinical entries remain authoritative: applied structured findings
  are recorded with a `conflicts` array
  (`structuredFieldConflicts` state) when an existing RN-entered value
  differs — the clinician value is never overwritten, only surfaced.
- Derived symptom values may fill only according to approved blank-only
  behavior and may not overwrite manual data.

## 8. Audit requirements

Log: ruleset version, trigger, assessment identifier, output identifiers,
source-evidence references, user-initiated downstream action,
success/failure of downstream action. Confirmed today: Lock emits
`RNICA_ASSESSMENT_LOCKED` via `_safe_log_event` with
`signatureCertification`/`clinicianSignature`/`lockedAt` metadata
(`visits.py`, Lock handler). **Not confirmed:** an equivalent audit event
for "AI recommendation applied" or "AI recommendation dismissed" —
Structured Findings review persists `review_status` but no dedicated audit
log entry was found for the review action itself —
`[IMPLEMENTATION DISCOVERY REQUIRED]`.

## 9. Test requirements

- Trigger tests for Load, Save, and Lock
- No-live-typing claim test
- Deterministic-output regression tests
- Source-provenance tests — partially covered today by
  `test_structured_findings_application.py`,
  `test_structured_findings_acceptance_analytics.py`,
  `test_structured_findings_rn_productivity_metrics.py`,
  `test_structured_findings_bulk_api.py`, `test_structured_findings.py`
  (5 backend test files confirmed) and
  `applyStructuredFindings.test.js` (frontend)
- No-silent-mutation tests
- Manual-entry preservation tests
- Prohibited-language snapshot tests — **not found**;
  `[IMPLEMENTATION DISCOVERY REQUIRED]`
- Historical-record compatibility tests

## 10. Chart-wide AI expansion — restated

Per `PATIENT_CHART_AUTHORITY_MAP.md`, chart-wide AI expansion beyond RNICA
remains a deferred decision, not a gap. This document governs RNICA's AI
surface only.
