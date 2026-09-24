# Lock-Gate Dependency Trace (Phase 2, independent re-trace)

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED — Lock fails open on the legacy narrative path; not yet fixed. See `RNICA_PHASE3_REMEDIATION_REGISTER.md` (P3-006, P3-007).

**Scope:** every `form_data` path read by
`evaluate_finalization_readiness()` and its helper
`evaluate_poc_completeness()` in
`backend/app/services/rnica_finalization_service.py` at commit `16264cf`,
traced to a live UI writer.

**Classification enum (exactly one per row):** REACHABLE_VALID,
REACHABLE_LEGACY, UNREACHABLE_BLOCKER, DUPLICATE_NARRATIVE_AUTHORITY,
STALE_DEPENDENCY, NOT_VERIFIED.

---

## 1. Path-by-path trace

| # | Check key | Path read | Read file:line | Write site(s) | Classification | Evidence chain |
|---|---|---|---|---|---|---|
| 1 | `attestation` | `finalization.signatureCertification` | `rnica_finalization_service.py:103` | `RNICA.jsx:9719` (checkbox, `path: "signatureCertification"`); default `RNICA.jsx:893`; frontend error gate `RNICA.jsx:1101-1102` | REACHABLE_VALID | Field config lives in `SECTION_CONFIGS.finalization`, which is a registered section (`FORM_REGISTRY`, `RNICA.jsx:242-249`) and is rendered by the generic field renderer, not a custom renderer |
| 2 | `signature` | `finalization.clinicianSignature` | `rnica_finalization_service.py:111` | `RNICA.jsx:9720` (`required: true`); default `:894`; frontend error gate `:1094-1095` | REACHABLE_VALID | Same |
| 3 | `narrativeReviewed` | `diagnoses.clinicalNarrative` | `rnica_finalization_service.py:120` | Only `RNICA.jsx:2029` and `:2038`, both inside `ClinicalNarrativeCard` (`:2013`), which is dispatched **only** by `RNICA.jsx:8353` (`card.customRenderer === "clinicalNarrative"`). No card in `SECTION_CONFIGS` declares that renderer (full-file scan of `customRenderer:` literals returns 15 renderers, none named `clinicalNarrative`). **NONE FOUND (reachable)** | STALE_DEPENDENCY | The path can only be non-empty on legacy/seeded records; on any record created by the current UI it is always `""`, making the check vacuously `ready` via `rnica_finalization_service.py:122` (`narrative_ready = (not _has_text(narrative)) or narrative_reviewed`) |
| 4 | `narrativeReviewed` | `diagnoses.clinicalNarrativeReviewed` | `rnica_finalization_service.py:121` | Only `RNICA.jsx:2033, 2039, 2140` — same unreachable card. **NONE FOUND (reachable)** | STALE_DEPENDENCY | Same chain. Consequence: a legacy record that *does* carry narrative text can never be marked reviewed through the UI → for those records only, the gate becomes unsatisfiable |
| 5 | (live narrative, **not** read by the gate) | `finalization.clinicalNarrative` | not read by `rnica_finalization_service.py` (full-file read: no occurrence) | `RNICA.jsx:9714` (textarea, `required: true`); AI insert `RNICA.jsx:10313-10322`; frontend-only error gate `RNICA.jsx:1091-1092`; separately tracked by `backend/app/services/clinical_note_validation_engine.py:412-419` | DUPLICATE_NARRATIVE_AUTHORITY | Two narrative paths exist; the one the RN types into is not the one the Lock gate validates |
| 6 | `lcdBaseline` | `diagnoses.lcdEligibilityNarrative` | `rnica_finalization_service.py:130` | `RNICA.jsx:1973-1974` (`LcdEligibilityCard`) and `:1992-1993` (`LcdSupportingEvidenceCard`); both reachable via `customRenderer: "lcdEligibility"` (`:8934`) and `"lcdSupportingEvidence"` (`:8943`); default `:479` | REACHABLE_VALID | Two writers for one path — noted in `DUPLICATE_AUTHORITY_MATRIX.md`, but the gate itself is satisfiable |
| 7 | `referralsReviewed` | `referrals.reviewed` | `rnica_finalization_service.py:137` | `RNICA.jsx:9704` (checkbox "I reviewed the referral status…"); check-to-section map `RNICA.jsx:237` | REACHABLE_VALID | `referrals` is a registered section (`RNICA.jsx:242-249`) |
| 8 | `chhaPocCompleted` | `haAssignment.notApplicable` | `rnica_finalization_service.py:156` | `RNICA.jsx:9672` (field config) and `:8504` (`HaAssignmentCard` checkbox); default `:863` | REACHABLE_VALID | Two writers (config field + custom renderer) for the same path |
| 9 | `chhaPocCompleted` | `haAssignment.assignedAide` | `rnica_finalization_service.py:157` | `RNICA.jsx:9671` and `:8503`; default `:863` | REACHABLE_VALID | Same |
| 10 | `chhaPocCompleted` | `chhaPoc.completed` | `rnica_finalization_service.py:159` | `RNICA.jsx:4113-4119` — checkbox inside `CHHAPocCard` (`:3705`), which persists via `updateRnicaAssessment(assessmentId, { ...fullFormData, chhaPoc: next })` (`:3780`). Card is mounted from the patient chart: `sns-emr-frontend/src/charts/PatientChart.jsx:798` | REACHABLE_VALID | Prior pass recorded "no UI writer located"; that is **refuted** — the writer exists, but it lives outside RNICA's own screen flow (CHHA POC card on the Patient Chart), which is a discoverability issue, not an unreachable gate |
| 11 | `pocCompleteness` | POC problems / goals / interventions / `intervention.discipline` | `rnica_finalization_service.py:38-93` (called at `:144`) | Not a `form_data` path — supplied by the caller as `poc_problems` | REACHABLE_VALID | Frequency deliberately not enforced (docstring `:48-52`) |

## 2. Aggregate gate

`ready = all(check["ready"] …)` — `rnica_finalization_service.py:168`.

## 3. What this means in practice (independent derivation)

1. **The Lock gate cannot be blocked by the narrative the RN actually
   writes.** `finalization.clinicalNarrative` is never read by
   `evaluate_finalization_readiness()`. The backend test fixture
   `COMPLETE_FORM_DATA` (`backend/tests/test_rnica_finalization.py:56-65`)
   contains **no** narrative at all and still asserts
   `readiness["ready"] is True` (`test_rnica_finalization.py:116-119`). That is positive proof, from
   the repository's own test suite, that a record with zero clinical
   narrative locks cleanly server-side.
2. **The only narrative enforcement is client-side.**
   `RNICA.jsx:1091-1092` raises a frontend error when
   `finalization.clinicalNarrative` is empty. Per the service's own
   docstring (`rnica_finalization_service.py:5-8`), the backend is supposed
   to be the enforcement boundary and the UI "a courtesy" — for the
   narrative, that relationship is inverted.
3. **Legacy records are the only ones the `diagnoses.*` check can act on**,
   and for those it is unsatisfiable through the UI, because the only
   "mark reviewed" checkbox (`RNICA.jsx:2140`) lives in the undispatched
   card. Existing backend tests lock that behaviour in
   (`test_rnica_finalization.py:129-147`), so the defect is test-protected.

## 4. Summary by classification

| Classification | Count | Rows |
|---|---|---|
| REACHABLE_VALID | 8 | 1, 2, 6, 7, 8, 9, 10, 11 |
| STALE_DEPENDENCY | 2 | 3, 4 |
| DUPLICATE_NARRATIVE_AUTHORITY | 1 | 5 |
| UNREACHABLE_BLOCKER | 0 | — (the unreachable path fails *open*, not closed, for current-UI records) |
| REACHABLE_LEGACY | 0 | — |
| NOT_VERIFIED | 0 | — |

## 5. Reconciliation status for the finding as a whole

**CONFLICTING** — two narrative paths, one validated server-side and
unwritable, one written and validated only client-side. Remediation choice
(move the gate to `finalization.clinicalNarrative`, or re-dispatch the
Diagnoses narrative card, or migrate legacy values) is a clinical-authority
decision: see `STAFF_SUPPORT_IMPACT_REGISTER.md` and
`AUTHORITY_APPLICABILITY_REGISTER.md`. No code change was made this pass.
