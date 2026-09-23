# Historical Compatibility Results (Phase 2, code-level only)

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED — code-level only, not yet validated against representative fixtures. See `RNICA_PHASE3_REMEDIATION_REGISTER.md` Phase G.

**Explicit scope limit.** This document is derived **entirely from source
code**. No live database, seeded tenant, or patient record was queried, and
no patient identifier of any kind appears below. Where an example record
shape is needed, it is taken from synthetic structures already present in
committed test files.

**Commit inspected:** `16264cf`.

---

## 1. Mechanism inventory

| # | Mechanism | File:line | What it does |
|---|---|---|---|
| 1 | `INITIAL_FORM` — complete default state, 28 sections | `RNICA.jsx:344-347` (header + declaration) through the object body | Canonical blank shape for every RN ICA section |
| 2 | `deepMergeFormData(defaults, saved)` | `RNICA.jsx:9734-9757` | Recursive merge of a saved document onto `INITIAL_FORM` |
| 3 | Initial component state | `RNICA.jsx:9980` (`useState(JSON.parse(JSON.stringify(INITIAL_FORM)))`) | Deep clone so defaults are never mutated |
| 4 | Load path | `RNICA.jsx:10901` (`const merged = deepMergeFormData(INITIAL_FORM, data.formData)`) | Every load of an existing record goes through the merge |
| 5 | Reset path | `RNICA.jsx:10894` | Deep clone of defaults |
| 6 | Completion math against defaults | `RNICA.jsx:1398-1405`, `:11136-11137` | Section completion compares saved data to the *current* `INITIAL_FORM`, so it self-updates as sections evolve |
| 7 | Server-side merge/sync of submission bookkeeping | `backend/app/services/rnica_hope_workflow_service.py:45-51, 95-99` | Copies workflow fields into `form_data["finalization"]` without touching clinical keys |
| 8 | Exporter tolerance of absent sections | `hopeReportMapper.js:463-481` (every section destructured as `formData.x || {}`), plus `PLACEHOLDER = "^"` (`:3`) and `valueText`/`arrayText` (`:16-20`) | Missing values degrade to `"^"`, never throw |
| 9 | Legacy-vocabulary crosswalks | `hopeReportMapper.js:72-74, 90-92, 101-103` + `officialCodeLookup` `:109-122` | Pre-code-set values are translated, unknown values fall back to the placeholder rather than being guessed |
| 10 | Explicit "legacy record: review required" signalling | `hopeReportMapper.js:171, 221-227, 313-327, 512-526` | Records predating a newer field are flagged for human review instead of silently exported as answered |

## 2. Verified merge behaviour (derived from `RNICA.jsx:9734-9757`)

| Input shape | Merge result | Risk |
|---|---|---|
| `saved === undefined` / `null` for a key | Returns `defaults` (`:9739`) | None — older record missing a whole section renders blank, not crashed |
| `defaults` is an array, `saved` is an array | `saved` wins wholesale, no element-wise merge (`:9740-9742`) | **New keys added to array *elements* later (e.g. a new column on a wound row or a POC intervention) are NOT back-filled.** Element-level renderers must tolerate `undefined`. This is the single real compatibility hazard found |
| `defaults` object, `saved` object | Key-by-key recursive merge over `Object.keys(defaults)` (`:9744-9747`) | New schema keys correctly receive their defaults |
| `saved` has keys not in `defaults` | Preserved verbatim (`:9748-9751`) | **No data loss.** Retired/renamed fields survive round-trips and remain in the JSONB document |
| Scalar mismatch (e.g. default `""`, saved `false`) | `saved` wins (`:9754`) | Type drift is possible but no crash; no coercion is attempted |

## 3. Records that could be lost or corrupted on load

| Scenario | Verdict | Evidence |
|---|---|---|
| Older record missing a section added later | Safe — defaults hydrate it | `RNICA.jsx:9739, 9744-9747` |
| Older record with a field that no longer exists in `INITIAL_FORM` | Safe and preserved (not deleted) | `RNICA.jsx:9748-9751` |
| Older record whose array elements lack newly added element keys | **Not hydrated** — element renderers must null-guard | `RNICA.jsx:9740-9742` |
| Legacy `diagnoses.clinicalNarrative` text on an older record | Loads fine, but can no longer be marked reviewed through the UI (the only checkbox is in the undispatched `ClinicalNarrativeCard`, `RNICA.jsx:2140` / `:8353`), so `evaluate_finalization_readiness` will report `narrativeReviewed: not ready` (`rnica_finalization_service.py:120-128`) | **This is the one identified path by which an existing record can become un-lockable.** See `LOCK_GATE_DEPENDENCY_TRACE.md` |
| Legacy record predating HOPE asked-status fields | Safe, and explicitly surfaced as "HOPE Legacy Review Required" | `hopeReportMapper.js:313-327, 512-526, 582-584` |
| Legacy free-vocabulary site-of-service / admitted-from / living-arrangement values | Translated, or placeholdered — never guessed | `hopeReportMapper.js:105-122` |
| Record with `symptomImpact` values as numbers rather than strings | Tolerated by the frontend trigger (`isModerateOrSevere` accepts `2`/`3` and substrings, `hopeReportMapper.js:394-398`) but **not** by the backend (`_is_moderate_or_severe` requires the exact strings `"MODERATE"`/`"SEVERE"`, `hope_phase_b_engine.py:40, 140-142`) | Divergent SFV determination for the same stored record |

## 4. Committed synthetic fixtures used as shape references

Used only as *shape* evidence; no identifiers reproduced.

| Fixture | File:line | Demonstrates |
|---|---|---|
| `COMPLETE_FORM_DATA` (minimal lockable document: `diagnoses.lcdEligibilityNarrative`, `referrals.reviewed`, four `finalization` keys) | `backend/tests/test_rnica_finalization.py:56-65` | A record with *no* narrative and *no* `chhaPoc` key locks successfully (`:116-119`) — partial documents are first-class |
| Narrative-present variant | `backend/tests/test_rnica_finalization.py:135-147` | Legacy `diagnoses.clinicalNarrative` + `clinicalNarrativeReviewed: False` blocks the gate |
| Round-trip reload test | `sns-emr-frontend/src/intake/hopeReportMapper.test.js:274-295` | JSONB save/reload produces an identical HOPE report |
| "Legacy records (new field absent)" suite | `hopeReportMapper.test.js:215-272` | Absent newer fields produce review flags, not crashes or false answers |
| "value 0 is a completed answer, not a missing one" | `hopeReportMapper.test.js:297-317` | Guards against treating `0` as unanswered |

## 5. Test evidence actually executed this pass

```
PS> cd sns-emr-frontend; npx vitest run src/intake/hopeReportMapper.test.js
Test Files  1 passed (1)
     Tests  138 passed (138)
EXITCODE=0
```

That suite includes the round-trip and legacy-record groups above, so the
exporter's historical-compatibility behaviour is empirically confirmed at
this commit. The backend suite was **not** run (no Python virtual
environment present: `Test-Path backend\.venv` → `False`).

## 6. Reconciliation status

| Aspect | Status |
|---|---|
| Object-level merge of older/partial records | VERIFIED_COMPLETE |
| Preservation of retired keys | VERIFIED_COMPLETE |
| Exporter tolerance of absent sections | VERIFIED_COMPLETE (138 tests, exit 0) |
| Array-element key back-fill | PRESENT_RESPONSE_SET_INCOMPLETE (by design; renderers must null-guard) |
| Legacy `diagnoses.clinicalNarrative` records vs the Lock gate | CONFLICTING |
| Frontend vs backend symptom-severity type tolerance | CONFLICTING |
| Backend merge/compat behaviour under test | NOT_VERIFIED (suite not executed this pass) |
