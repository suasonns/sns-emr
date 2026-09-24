# SFV Ownership Trace

Status: **DISCOVERY ONLY — NO IMPLEMENTATION.** This document proves (or
disproves) ownership using repository code-path tracing. It does **not**
use live database record IDs: this environment has no reachable
authenticated Postgres instance (documented limitation, unchanged all
session), so trigger/SFV/visit/note UUIDs below are **symbolic** (`Trigger
A`, `SFV A`, etc.) representing one instance of each code path, not
literal database rows. Where the template asks for a concrete ID and none
can be produced, the field is marked `NOT_VERIFIED (no live DB access)`
rather than fabricated. This is disclosed up front per the no-invention
rule.

---

## Authoritative linkage key (repository-verified, not assumed)

```
HOPE Record (RnicaAssessment.id, known as assessmentId)
  -> RnicaAssessment.hope_event_type   (ADMISSION | HUV1 | HUV2)
  -> RnicaAssessment.visit_id          (the Visit that finalized this record)
  -> SFVRequirement                     WHERE trigger_source_type = <mapped from hope_event_type>
                                           AND trigger_reference_id = RnicaAssessment.visit_id
  -> SFVRequirement.completed_visit_id -> ClinicalNote.content.symptomImpact
  -> J2052 / J2053
```

Mapping `hope_event_type -> trigger_source_type`: `ADMISSION ->
INITIAL_RN_ICA`, `HUV1 -> HUV1`, `HUV2 -> HUV2`.

**This is the "HOPE Record → Trigger Visit → SFV Requirement → Completion
Visit" option** from the required decision list — VERIFIED BY REPOSITORY
TRACE (see `SFV_TRIGGER_OWNERSHIP_TRACE.md` §1 for the column-by-column
citations: `sfv_requirement.py` lines 36-37, `hope_phase_b_engine.py`
lines 371-377/487-490/534-542, `rnica_assessment.py` line 16).

**This is not what the current code does.** The current code implements
neither this linkage nor the SFVRequirement-direct option — it implements
patient-level latest-completed selection with no linkage at all
(`HopeReport.jsx` lines 162-176). That is the defect.

---

## Trace Scenario 1 — ADM

| Field | Value | Repository proof |
|---|---|---|
| Trigger record type | ADM | `RnicaAssessment.hope_event_type = "ADMISSION"` |
| Trigger record ID | Trigger A (symbolic — `RnicaAssessment.id`) | NOT_VERIFIED (no live DB access) |
| Trigger visit ID | Visit A (symbolic — `RnicaAssessment.visit_id`) | `rnica_assessment.py` line 16 |
| Trigger date | `visit.visit_datetime` at ADM finalize | `visits.py::_run_phase_b_finalize_hooks`, `election_datetime=visit.visit_datetime` |
| Trigger J2051 values | `pain_impact`/`non_pain_impact` extracted from that visit's notes | `_extract_j2051_impacts_from_notes(visit_id=visit.id)` |
| Created SFV Requirement ID | SFV A (symbolic) — `trigger_source_type=INITIAL_RN_ICA, trigger_reference_id=Visit A` | `hope_phase_b_engine.py` lines 487-490 |
| Linked completion visit ID | `SFVRequirement.completed_visit_id` for SFV A | `sfv_requirement.py` line 45 (column exists; population path is the SFV completion API, not re-traced here) |
| Linked clinical note ID | `ClinicalNote` for that completion visit, `content.symptomImpact` | `_extract_symptom_impact_from_content`, `visits.py` |
| J2052 source | SFV A's `status`/`completed_at` fields | `sfv_requirement.py` |
| J2053 source | SFV A's linked completion visit's `ClinicalNote.content.symptomImpact` | as above |
| Export record ID | ADM `RnicaAssessment.id` (= Trigger A) | — |
| Ownership verified | **NO** | current export code (`HopeReport.jsx`) does not query by `(trigger_source_type, trigger_reference_id)` at all |
| Cross-timepoint leak possible | **YES** | see Test 1-3 below |
| Status | **FAIL** | — |

## Trace Scenario 2 — HUV1

| Field | Value | Repository proof |
|---|---|---|
| Trigger record type | HUV1 | `RnicaAssessment.hope_event_type = "HUV1"`, `assessment_type = "UPDATE"`, `locked = true`, in HUV1 window |
| Trigger record ID | Trigger B (symbolic) | NOT_VERIFIED (no live DB access) |
| Trigger visit ID | Visit B (symbolic) | `rnica_assessment.py` line 16 |
| Trigger date | `visit.visit_datetime` at HUV1 finalize | `process_huv_finalize(completed_visit_datetime=visit.visit_datetime)` |
| Trigger J2051 values | extracted from Visit B's notes | same mechanism as ADM |
| Created SFV Requirement ID | SFV B (symbolic) — `trigger_source_type=HUV1, trigger_reference_id=Visit B` | `hope_phase_b_engine.py` line 534-542 |
| Linked completion visit ID | `SFVRequirement.completed_visit_id` for SFV B | as above |
| Linked clinical note ID | `ClinicalNote` for that completion visit | as above |
| J2052 source | SFV B | — |
| J2053 source | SFV B's completion visit's `symptomImpact` | — |
| Export record ID | HUV1 `RnicaAssessment.id` (= Trigger B) | — |
| Ownership verified | **NO** | same root cause as Scenario 1 |
| Cross-timepoint leak possible | **YES** | see Test 2, 4 below |
| Status | **FAIL** | — |

## Trace Scenario 3 — HUV2

| Field | Value | Repository proof |
|---|---|---|
| Trigger record type | HUV2 | `RnicaAssessment.hope_event_type = "HUV2"`, `assessment_type = "UPDATE"`, `locked = true`, in HUV2 window |
| Trigger record ID | Trigger C (symbolic) | NOT_VERIFIED (no live DB access) |
| Trigger visit ID | Visit C (symbolic) | `rnica_assessment.py` line 16 |
| Trigger date | `visit.visit_datetime` at HUV2 finalize | same mechanism |
| Trigger J2051 values | extracted from Visit C's notes | same mechanism |
| Created SFV Requirement ID | SFV C (symbolic) — `trigger_source_type=HUV2, trigger_reference_id=Visit C` | `hope_phase_b_engine.py` line 534-542 |
| Linked completion visit ID | `SFVRequirement.completed_visit_id` for SFV C | as above |
| Linked clinical note ID | `ClinicalNote` for that completion visit | as above |
| J2052 source | SFV C | — |
| J2053 source | SFV C's completion visit's `symptomImpact` | — |
| Export record ID | HUV2 `RnicaAssessment.id` (= Trigger C) | — |
| Ownership verified | **NO** | same root cause |
| Cross-timepoint leak possible | **YES** | see Test 3, 5 below |
| Status | **FAIL** | — |

**Verify claims (per scenario) — current code:**

- "HUV1 SFV cannot replace SFV A" — **FALSE currently.** Nothing in
  `HopeReport.jsx` prevents this; only the *timing* of completion
  determines which SFV wins the sort.
- "HUV2 SFV cannot replace SFV A/B" — **FALSE currently**, same reason.
- "Most-recent-SFV logic cannot replace SFV A/B/C" — **FALSE currently
  — most-recent-SFV logic IS the entire selection mechanism today.**
- "Patient-level lookup cannot replace SFV A/B/C" — **FALSE currently —
  patient-level lookup (`listSfvRequirements(patientId)` with no trigger
  filter) IS the query used today.**

All four "verify" claims fail for all three scenarios under the current
implementation. This is the same finding restated per-scenario, not three
independent defects.

---

## Acceptance tests (cross-timepoint leakage)

These are **documented required test scenarios**, not implemented test
code — no test files were added or changed in this pass, per the
discovery-only constraint. Each is evaluated against **current
repository behavior** (traced above), not a hypothetical fixed
implementation.

| # | Scenario | Expected | Current behavior | Result |
|---|---|---|---|---|
| 1 | ADM→SFV A, HUV1→SFV B, export ADM | Exports SFV A only | Exports whichever of A/B has the later `completedAt` (patient-wide) | **FAIL** |
| 2 | ADM→SFV A, HUV1→SFV B, export HUV1 | Exports SFV B only | Same mechanism as Test 1 — depends only on completion timing, not which record is being exported | **FAIL** |
| 3 | ADM→SFV A, HUV1→SFV B, HUV2→SFV C, export ADM | Exports SFV A only | Exports whichever of A/B/C has the latest `completedAt` | **FAIL** |
| 4 | Same setup, export HUV1 | Exports SFV B only | Same as Test 3 — identical query regardless of `timepoint` prop | **FAIL** |
| 5 | Same setup, export HUV2 | Exports SFV C only | Same as Test 3 | **FAIL** |
| 6 | Newer SFV created after an older HOPE record's own SFV; export the older HOPE record | Exporter uses the older record's own linked SFV; ignores the newer one | Exporter uses whichever SFV is now most recently completed — will use the newer one if it completes later, in violation of the expectation | **FAIL** |
| 7 | Patient has 5 SFVs across timepoints; export every qualifying HOPE record | Every HOPE record exports only its own linked SFV; no fallback | All exports for that patient currently resolve to the *same single* most-recently-completed SFV, regardless of which HOPE record is being exported | **FAIL** |

**Number of failed ownership tests: 7 of 7.** This is not a partial
defect — under the current implementation, correct behavior would only
occur by coincidence (i.e., if the trigger records happen to complete
their SFVs in the same chronological order as their own timepoints, with
no HUV2 SFV ever completing before a still-open HUV1/ADM one, etc.).
There is no code path that guarantees it.

---

## J2052 / J2053 status (per required downgrade)

| Item | Prior status | New status |
|---|---|---|
| J2052 | VERIFIED | **SOURCE VERIFIED / OWNERSHIP NOT VERIFIED** |
| J2053 | VERIFIED | **SOURCE VERIFIED / OWNERSHIP NOT VERIFIED** |

This matches (does not contradict) the `OPEN_QUESTION` status already
recorded for both items in `HOPE_ITEM_PROVENANCE_MATRIX.md` — that
document uses the 3-value STATUS vocabulary (`VERIFIED` /
`NOT_VERIFIED` / `OPEN_QUESTION`) mandated for that specific deliverable,
under which "source verified, ownership not verified" maps to
`OPEN_QUESTION`. This document uses the finer-grained two-axis label
requested here for the same underlying fact.

---

## What is and is not fixed by this document

- **Not fixed:** `HopeReport.jsx`'s selection query. No code was changed.
- **Not created:** no new field, table, enum, or endpoint.
- **Confirmed sufficient:** the existing `trigger_source_type` /
  `trigger_reference_id` / `visit_id` / `hope_event_type` columns are
  enough to implement a correct fix without new storage (see
  `SFV_TRIGGER_OWNERSHIP_TRACE.md` §4 for the specific, still-unimplemented
  design).
