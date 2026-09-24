# J2053 Source-of-Truth Analysis

**Document Status:** PHASE 3A GATING DELIVERABLE — required before any
`SFVRequirement.symptom_impact` schema change is approved, per the
"PAUSE SCHEMA DESIGN" directive (2026-09-23). No implementation is made
in this document; it is evidence-gathering only.

## 1. What exact structure exists today?

A `symptom_impact` / `symptomImpact` JSON object, keyed by the same
HOPE J2051/J2053 symptom vocabulary and severity scale already used
throughout the RNICA form and the AI concept-mapping registry:

```json
{
  "pain": "0|1|2|3",
  "shortnessOfBreath": "0|1|2|3",
  "anxiety": "0|1|2|3",
  "nausea": "0|1|2|3",
  "vomiting": "0|1|2|3",
  "diarrhea": "0|1|2|3",
  "constipation": "0|1|2|3",
  "agitation": "0|1|2|3"
}
```

(0 = None, 1 = Mild, 2 = Moderate, 3 = Severe — the exact vocabulary
`structured_findings.py` cross-writes via `PAIN_SEVERITY_*`,
`SYMPTOM_ANXIETY_SEVERITY_*`, `SYMPTOM_AGITATION_SEVERITY_*`,
`RESP_SOB_*`, and the GI concept families for nausea/vomiting/
diarrhea/constipation — `backend/app/services/evidence/
structured_findings.py:232-783`.) This is the same vocabulary the
recommended `symptom_impact` JSONB structure from the Phase 3
remediation plan proposed re-creating on `SFVRequirement` — it already
exists.

## 2. Where is it stored?

`ClinicalNote.content` (`backend/app/models/clinical_note.py:134`, a
generic JSON column on the visit's note row, one row per `Visit` via
`ClinicalNote.visit_id`). There is no dedicated `symptom_impact` column
anywhere in the schema today — it is a key inside the free-form
`content` JSON blob, the same blob that already holds `pain`, `vitals`,
`signs_symptoms`, etc. for that visit's note.

## 3. Which visit types use it today?

Only as a **read** path, and only for **trigger** visits: 
`_extract_j2051_impacts_from_notes` (`backend/app/api/visits.py:3611`)
is called from `_run_phase_b_finalize_hooks` (`visits.py:4113`), which
runs at visit-finalize time to detect whether a newly-finalized
`INITIAL_RN_ICA` / `HUV1` / `HUV2` visit **triggers** a new
`SFVRequirement` (via J2051 pain/non-pain severity). It reads whichever
notes were attached to *that* triggering visit. **It is never invoked
against the completion visit** (`complete_sfv_requirement`, `visits.py
:3965-4046`, calls only `complete_sfv_requirement_from_visit` — no call
to `_extract_j2051_impacts_from_notes` or any symptom-impact read).

There is also no **write** UI for this key on any visit type: the
general visit-note content editor (`VisitNoteEditor` in
`VisitNotes.jsx`) has a `signs_symptoms.*` structured "Symptoms"
section (mobility/nutrition/fall-incidence/safety-issues — an
OASIS-style body-system severity model), and a separate single `pain`
object, but no field that writes `content.symptomImpact.{anxiety,
nausea, vomiting, diarrhea, constipation, agitation}` directly. Today
`content.symptomImpact` is populated **only** as an opportunistic
cross-write from the AI/scribe structured-findings concept-mapping
pipeline (`structured_findings.py`) — i.e., only when a clinician
dictates or documents free text that the AI concept-matcher recognizes
as one of the fixed `CONCEPT_REGISTRY` codes, and only if the clinician
then accepts that suggestion (the module's own contract: "Never
auto-applied by this module... application happens client-side").

## 4. Can SFV completion visits already store it?

**Structurally, yes** — `ClinicalNote.content` is an unconstrained JSON
column, so a completion visit's note could hold a `symptomImpact` key
today with zero schema change. **Operationally, no** — the completion
visit's `SymptomFollowUpVisitSection` (`VisitNotes.jsx:1026-1113`) has
no field at all for symptom impact; it only surfaces a free-text
instruction ("Document the symptom reassessment and interventions
above...") and a "Complete SFV" button. A nurse has no deterministic,
always-available control to enter `symptomImpact` values during the
completion visit — the only path is the opportunistic AI cross-write
described above.

## 5. Can it support all J2053 requirements?

**Vocabulary: yes.** The existing `symptomImpact` key already maps 1:1
onto every HOPE J2053-relevant symptom category and the 0-3 severity
scale.

**Reliability: no, not as-is.** J2053 export readiness must be
guaranteed-answerable for every completed SFV (per the Phase 4
acceptance criteria: *"completion visit exists, symptom impact empty →
validation blocker"*). An AI-opportunistic cross-write cannot satisfy
that — there must be a deterministic manual entry point a nurse can
always use, with or without AI/dictation.

## 6. Can HOPE export read from it directly?

Yes, mechanically — once the completion visit's `ClinicalNote.content
.symptomImpact` is populated, HOPE export can read it exactly the way
`_extract_j2051_impacts_from_notes` already reads the same key from
trigger-visit notes, with no new column and no new JSON shape. The only
new backend work would be an equivalent read function keyed off
`SFVRequirement.completed_visit_id → ClinicalNote.visit_id` (see §9)
rather than off the trigger visit.

## 7. Is any information missing?

Yes — a **deterministic manual capture UI** for `symptomImpact` inside
`SymptomFollowUpVisitSection` (or the completion visit's note editor).
The JSON shape, the vocabulary, and the read-time parsing convention
all already exist; only the guaranteed write path from a nurse's own
action is missing.

## 8. What specific gap remains if we reuse it?

Adding a small, explicit `symptomImpact` control set
(pain/shortnessOfBreath/anxiety/nausea/vomiting/diarrhea/constipation/
agitation, 0-3 each) directly to `SymptomFollowUpVisitSection`, writing
into the **same** `content.symptomImpact` key on the completion visit's
`ClinicalNote` that already exists in the schema and is already parsed
elsewhere — this closes the gap with a UI change only, no migration.

## 9. Why would a second storage location be necessary?

It would only be necessary if the completion visit could not reliably
produce its own `ClinicalNote` row at the time `symptomImpact` needs to
be captured. It can: `complete_sfv_requirement` already requires and
receives a `completionVisitId` (`SfvCompletionRequest.completionVisitId
`, `visits.py:3965`), and that visit already carries its own
`ClinicalNote` (created via the same `createVisitNote`/`VisitNoteEditor`
flow used for every visit type, per `VisitNotes.jsx`). Because
`SFVRequirement.completed_visit_id` is a single scalar FK to exactly
one `Visit` (see §10), there is an unambiguous 1:1 path from
"the SFVRequirement that was completed" to "the one ClinicalNote whose
content should hold symptomImpact." No second storage location is
architecturally required.

## 10. What audit risks occur if we duplicate it?

Storing `symptom_impact` on **both** `ClinicalNote.content` (already
existing) and a new `SFVRequirement.symptom_impact` column would
recreate the exact anti-pattern P1A just eliminated for J2052: two
independent locations for the same clinical fact, one of which must be
kept in sync with the other via UI-driven or service-layer
synchronization. That reintroduces:
- ambiguity about which value is authoritative if they disagree
  (e.g. a correction made to the note after the SFVRequirement snapshot
  was written),
- a second correction-workflow surface (Phase 4/Correction Workflow
  would need to know which column HOPE actually exported from, and
  keep both updated on every correction),
- audit-trail duplication (two "who changed what, when" trails for one
  clinical fact instead of one).

## Multiple-SFVRequirement completion-visit linkage

**Can a single SFVRequirement be uniquely linked to one completion
visit? YES.** `SFVRequirement.completed_visit_id`
(`backend/app/models/sfv_requirement.py:45-49`) is a single, nullable
`UUID` `ForeignKey("visits.id")` — a scalar column, not a collection.
Exactly one `Visit` (or `NULL` while still `OPEN`) is recorded per
`SFVRequirement` row, set exclusively by
`complete_sfv_requirement_from_visit`. Combined with the confirmed fact
that a patient may accumulate multiple `SFVRequirement` rows over time
(§ prior finding — one per distinct `INITIAL_RN_ICA`/`HUV1`/`HUV2`
trigger), this means: **the completion visit is a viable, unambiguous
per-requirement source of symptom impact** — each `SFVRequirement`'s
own `completed_visit_id` points to the one encounter where its J2053
value should be captured and read from, with no cross-requirement
ambiguity.

## Required finding

**OPTION A — Reuse the existing `ClinicalNote.content.symptomImpact`
structure, plus a small, additive UI change to make it a deterministic
manual capture on the completion visit.**

### Rationale

- The vocabulary, JSON shape, and read-time parsing convention for
  `symptomImpact` already exist and are already production code
  (`structured_findings.py`, `_extract_j2051_impacts_from_notes`) — a
  new `SFVRequirement.symptom_impact` column would duplicate all three.
- `SFVRequirement.completed_visit_id` gives an unambiguous 1:1 link
  from requirement to the one `ClinicalNote` that should hold the
  value, so there is no technical need for a second storage location.
- The only real gap is a deterministic manual entry control — a UI
  change, not a schema change.
- This preserves the architecture rule stated in the redesign
  directive: RNICA/encounter documentation remains the clinical source
  of truth; HOPE remains a derived reporting layer that reads from it,
  rather than acquiring its own competing storage.
- No migration is required: `ClinicalNote.content` is already an
  unconstrained JSON column capable of holding this key today.

**Option B (new `SFVRequirement.symptom_impact` JSONB column) is
rejected** for this design — not because it's technically infeasible,
but because it fails the "one source of truth" acceptance criterion by
creating a second, sync-dependent storage location for a fact that
already has exactly one correct home (the completion visit's own
clinical note).

## Answers to standalone required questions

- **Schema change still required: NO.** No new column. `content` JSON
  already supports this key.
- **API change required: YES.** The visit-note save/update endpoint
  (or the SFV completion endpoint) needs a way to persist the
  `symptomImpact` object on the completion visit's note, and a new
  (or extended) read function is needed to pull it keyed off
  `completed_visit_id` for HOPE export — this is new backend
  read/write logic, not a schema migration.
- **UI change required: YES.** `SymptomFollowUpVisitSection` needs an
  explicit, always-visible `symptomImpact` capture control set.
- **Migration required: NO.**
