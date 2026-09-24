# Clinical Narrative Ownership — Redesign Regression Audit

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED — see `RNICA_PHASE3_REMEDIATION_REGISTER.md` (P3-006, P3-007, P3-008).

Status: **AUDIT ONLY — NO CODE CHANGES MADE.** Per directive, this document
classifies every reference to a "clinical narrative" field in the repository
and proposes (but does not implement) remediation. Evidence is cited as
`file:line`. Anything not directly read is marked `NOT_VERIFIED`.

Product authority (per session record): `finalization.clinicalNarrative` is
the sole current/correct narrative-ownership field. `diagnoses.clinicalNarrative`
must NOT be restored as a second authority.

---

## 1. Field inventory found

Two distinct narrative fields exist in the RNICA form schema today:

| Field | Where defined | Status |
|---|---|---|
| `diagnoses.clinicalNarrative` / `diagnoses.clinicalNarrativeReviewed` | `RNICA.jsx:487-488` (INITIAL_FORM default) | **Present in schema, but unreachable in the live UI (see §2).** |
| `finalization.clinicalNarrative` | `RNICA.jsx:892` (INITIAL_FORM default) | **Active, sole reachable writer, hard-required by frontend validation.** |

---

## 2. LEGACY REFERENCES (`diagnoses.clinicalNarrative` / `clinicalNarrativeReviewed`)

| # | File:Line | What it does | Classification |
|---|---|---|---|
| 1 | `RNICA.jsx:487-488` | `INITIAL_FORM.diagnoses` default object still declares both fields, with an in-code comment describing them as "SECTION 10 — Clinical Narrative & Disease Trajectory," deliberately separate from `lcdEligibilityNarrative` | **STALE-BUT-STILL-DECLARED** — schema slot exists, comment describes it as intentional, but nothing in the live UI can write to it (see #4) |
| 2 | `RNICA.jsx:1076-1077` | Soft (non-blocking) validation warning: if `diagnoses.clinicalNarrative` has text and `clinicalNarrativeReviewed !== true`, warns "Clinical narrative documented but not yet reviewed" | **DEAD IN PRACTICE** — condition can only be true for legacy assessments created before the redesign, or data written by direct API/import; no current UI path sets this text |
| 3 | `RNICA.jsx:2013-2145` (`ClinicalNarrativeCard`) | A fully-built component: radio buttons for Disease Trajectory, "Build Draft from Documented Findings" button (deterministic, non-AI `buildClinicalNarrative()`), a `diagnoses.clinicalNarrative` textarea, and a `clinicalNarrativeReviewed` checkbox. Writers at `:2029`, `:2033`, `:2038-2039` all target `diagnoses.clinicalNarrative`/`clinicalNarrativeReviewed` | **DEAD CODE PATH — CONFIRMED UNREACHABLE.** See #4. |
| 4 | `RNICA.jsx:8353-8365` | Dispatch: `if (sectionKey === "diagnoses" \&\& card.customRenderer === "clinicalNarrative") { <ClinicalNarrativeCard .../> }` | **CONFIRMED DEAD.** Grepped every `customRenderer:` value assigned to a card in the diagnoses section config (`:8789-8954`): `anthropometricsAutoBmi`, `secondaryDiagnoses`, `lcdEligibility`, `hopeComorbidities`, `lcdSupportingEvidence`, `declineTracker`. **No card anywhere sets `customRenderer: "clinicalNarrative"`.** This dispatch branch and `ClinicalNarrativeCard` are unreachable — dead code, not merely "legacy but still used." |
| 5 | `RNICA.jsx:11392` | Patient Story (Phase B) screen: `whyHospiceNarrative: formData.diagnoses.clinicalNarrative \|\| ""` | **LIVE READ OF A DEAD-WRITE FIELD — ACTIVE BUG.** Because #4 means no current assessment can ever populate `diagnoses.clinicalNarrative`, this Patient Story field will always render blank on every new assessment going forward. It only shows content for pre-redesign legacy records that still carry old data. |
| 6 | `backend/app/services/rnica_finalization_service.py:120-121` | Lock-readiness "Layer 2" check reads `diagnoses.clinicalNarrative` / `diagnoses.clinicalNarrativeReviewed` | **ACTIVE CODE, READS A DEAD FIELD — see §4/§5.** |
| 7 | `backend/app/models/rnica_amendment.py:76-78` | Code **comment** giving `"diagnoses.clinicalNarrative"` as an example format string for the free-text `section_reference` field | **COMPATIBILITY / ILLUSTRATIVE ONLY** — not an executable reference; only worth correcting the example text, no functional impact |
| 8 | `backend/tests/test_rnica_finalization.py:130, 140-141` | `test_finalization_readiness_narrative_auto_passes_when_empty` and `test_finalization_readiness_blocks_unreviewed_narrative` build fixtures against `diagnoses.clinicalNarrative`/`clinicalNarrativeReviewed` and assert on `checks["narrativeReviewed"]` | **ACTIVE TEST OF THE STALE PATH — see §7.** These tests currently pass because they test the code exactly as written today (fail-open on the dead field); they do **not** test `finalization.clinicalNarrative` at all. |
| 9 | `backend/tests/test_rnica_finalization.py:235, 241` | Post-lock-edit-rejection test uses `diagnoses: {"clinicalNarrative": "attempted post-lock edit"}` as arbitrary payload | **INCIDENTAL** — generic lock-immutability test, not narrative-logic-specific; any field path would serve equally |
| 10 | `backend/tests/test_rnica_amendments.py:36` | Fixture default: `form_data or {"diagnoses": {"clinicalNarrative": "Original signed narrative."}}` | **INCIDENTAL** — generic amendment fixture payload, not asserting narrative-ownership behavior |

---

## 3. ACTIVE REFERENCES (`finalization.clinicalNarrative`)

| # | File:Line | What it does | Classification |
|---|---|---|---|
| 1 | `RNICA.jsx:892` | `INITIAL_FORM.finalization` default declares `clinicalNarrative: ""` | ACTIVE — current schema authority |
| 2 | `RNICA.jsx:1091-1092` | **Hard-blocking** validation error: `if (!formData.finalization.clinicalNarrative) errors["finalization.clinicalNarrative"] = "Clinical narrative is required before attestation";` | ACTIVE — this is the only enforcement anywhere (frontend-only, see §4) that a narrative must exist before lock |
| 3 | `RNICA.jsx:9714-9716` | Field config: `{ type: "textarea", label: "Clinical narrative", path: "clinicalNarrative", rows: 8, required: true, ... }` inside the Finalization section's "Clinical Narrative" card (`rnica-clinical-narrative`) | ACTIVE — sole reachable UI writer for a manually-typed narrative |
| 4 | `RNICA.jsx:10305-10322` (`handleInsertAiNarrative`) | AI-assisted note-draft insertion from a visit recording. Blank-only-write guard: `if (formData.finalization?.clinicalNarrative) return false;` — never overwrites existing RN text. Writes to `finalization.clinicalNarrative` with a provenance record tagged `AI_NOTE_DRAFT_NARRATIVE` / `source_type: "TRANSCRIPT"` | ACTIVE — second writer, provenance-tracked, blank-only (does not silently overwrite RN documentation) |
| 5 | `backend/app/services/clinical_note_validation_engine.py:395-435` | Field-tracking config; the "Clinical Narrative" entry's `paths` array is `["finalization.clinicalNarrative", "assessment_summary", "nursing_summary"]` | ACTIVE and **already correctly aligned** to the redesign — this file needs no change |
| 6 | `backend/tests/test_rnica_functional_assessment_governance.py:183` | `"finalization": {"clinicalNarrative": "Narrative present"}` | ACTIVE — this test fixture already uses the correct current path |

---

## 4. READINESS IMPACT

`evaluate_finalization_readiness()` (`rnica_finalization_service.py`) is the
single source of truth for the Section 12 Lock-readiness checklist the
frontend renders. Its `checks` dict has **no entry that ever inspects
`finalization.clinicalNarrative`** — grepped the entire file for
`clinicalNarrative`; the only two hits are lines 120-121, both against the
dead `diagnoses.*` path.

Net effect:
- The **only** enforcement that a narrative must exist before Lock is the
  frontend hard-error at `RNICA.jsx:1091-1092`.
- The backend readiness check (`narrativeReviewed`) is checking a field
  (`diagnoses.clinicalNarrative`) that can never be populated by any current
  UI action, so `narrative_ready = (not _has_text(narrative)) or narrative_reviewed`
  always evaluates `not _has_text(narrative)` → `True` → **the check always
  reports ready, regardless of whether the real (`finalization`) narrative was
  ever written or reviewed.** This matches the previously-confirmed Phase 2
  Finding D ("fails open").

## 5. LOCK IMPACT

Because the backend readiness gate never actually inspects
`finalization.clinicalNarrative`, **the Lock action's backend contract does
not require the real, current-authority narrative to exist at all.** Any
caller of the finalization/lock API directly (bypassing the frontend form —
e.g., a script, an import job, a future mobile client, or a frontend
validation bug) could lock an assessment with **no clinical narrative
present anywhere**, and the backend would not object. Today this risk is
masked because the frontend's own hard error (`:1091-1092`) is the only real
UI path to Lock — but it is a single point of enforcement with no backend
backstop, which is exactly the pattern the constitution's "no field may have
undocumented dual/authority ambiguity" principle warns against.

## 6. AUDIT IMPACT

No audit-log or version-history code path was found that separately records
which of the two fields (`diagnoses.clinicalNarrative` vs.
`finalization.clinicalNarrative`) was in effect at lock time; the finalization
record simply persists whatever `form_data` blob was submitted. This means
historical/legacy locked assessments that *do* carry old
`diagnoses.clinicalNarrative` content (pre-redesign) remain retrievable as-is
— no destructive migration has occurred — but there is no automated flag
distinguishing "this locked record's narrative lives at the old path" from
"this one already uses the new path." `NOT_VERIFIED`: whether any reporting
or export code reads `diagnoses.clinicalNarrative` for historical records
(only the Patient Story `whyHospiceNarrative` read at `RNICA.jsx:11392` was
found; no backend export/report code referencing the field was found in this
pass).

## 7. AMENDMENT IMPACT

`backend/app/models/rnica_amendment.py:76-78` — only a **comment** showing an
example `section_reference` string format; amendments are free-text
`section_reference` fields, not structurally bound to either narrative path.
No functional amendment-workflow impact. `backend/tests/test_rnica_amendments.py:36`
uses `diagnoses.clinicalNarrative` only as arbitrary fixture payload — the
amendment test does not assert anything about narrative-field semantics, so
it is unaffected by which path is "correct."

## 8. TEST IMPACT

Two **existing, currently-passing** backend tests directly assert behavior
against the stale field and would need to be rewritten (not just left alone)
if `rnica_finalization_service.py` is repointed to `finalization.clinicalNarrative`:

- `test_finalization_readiness_narrative_auto_passes_when_empty` (`test_rnica_finalization.py:129-133`)
- `test_finalization_readiness_blocks_unreviewed_narrative` (`test_rnica_finalization.py:135-146`)

Both currently build a `diagnoses.clinicalNarrative`/`clinicalNarrativeReviewed`
fixture and assert on `checks["narrativeReviewed"]`. Important nuance:
**`finalization.clinicalNarrative` has no "reviewed" checkbox concept at
all today** — the Finalization card (`RNICA.jsx:9714-9716`) is a plain
required textarea with no companion review-confirmation checkbox, unlike the
dead `ClinicalNarrativeCard`. So a straight find-and-replace of the field
path in the backend service would silently drop the "reviewed" semantics
entirely (there is no `finalization.clinicalNarrativeReviewed` field
anywhere in the schema) — this must be a deliberate design decision, not an
accidental side effect of the fix.

`test_rnica_functional_assessment_governance.py:183` already uses the
correct current path and needs no change.

---

## 9. RECOMMENDED REMEDIATION (NOT IMPLEMENTED — for authorization)

Three components, smallest-safe-first:

1. **Backend readiness check** (`rnica_finalization_service.py:120-126`):
   repoint the check to read `finalization.clinicalNarrative`. Decision
   needed on the "reviewed" semantic since no equivalent field exists on
   `finalization` today — options: (a) drop the reviewed-gate entirely and
   simply require `_has_text(narrative)` to be true (matches what the
   frontend already hard-enforces), or (b) add a new
   `finalization.clinicalNarrativeReviewed` field to preserve the
   review-confirmation gate. **Recommend (a)** — the frontend has already
   made the field a hard-required plain text field with no review checkbox,
   so option (a) matches the field's actual current design rather than
   re-introducing a UI element that does not exist.
2. **Dead code removal**: delete the unreachable `ClinicalNarrativeCard`
   component (`RNICA.jsx:2013-2145`), its dead dispatch branch
   (`:8353-8365`), and the now-orphaned `diagnoses.clinicalNarrative` /
   `clinicalNarrativeReviewed` schema defaults (`:487-488`) and soft-warning
   validation (`:1076-1077`) — once confirmed no legacy data path still
   depends on them being present in `INITIAL_FORM` (`NOT_VERIFIED`: whether
   any load/hydration code depends on these keys existing as defaults for
   older records; recommend checking before deleting the schema defaults,
   even though the UI writer is already dead).
3. **Patient Story fix** (`RNICA.jsx:11392`): change
   `whyHospiceNarrative: formData.diagnoses.clinicalNarrative || ""` to read
   `formData.finalization.clinicalNarrative || ""` so the Patient Story
   screen reflects the real, current-authority narrative instead of a
   permanently-blank dead field.
4. **Test rewrite**: update the two affected tests in
   `test_rnica_finalization.py` to exercise `finalization.clinicalNarrative`
   under whichever readiness-semantic option is chosen in (1).
5. **Comment correction** (`rnica_amendment.py:76-78`): update the
   illustrative example string to `"finalization.clinicalNarrative"` so the
   comment does not continue to point future engineers at the stale path.

No code has been changed. Awaiting authorization before implementing any of
the above.
