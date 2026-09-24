# SFV Trigger Ownership Trace

Status: **DISCOVERY / DESIGN ONLY — NOT IMPLEMENTED**

Scope: repository-trace proof of the SFV cross-timepoint selection defect
first identified in `HOPE_ITEM_PROVENANCE_MATRIX.md`, plus a fix *design*
(not implemented) built entirely from linkage columns that already exist
in the schema. No field, table, enum, or API is created by this document.

SNS Review Rule labels used throughout: VERIFIED BY REPOSITORY TRACE /
NOT_VERIFIED / OPEN_QUESTION. No "probably" / "likely" / "should come
from" language is used except where explicitly labeled NOT_VERIFIED.

---

## 1. What actually links an SFVRequirement to its trigger (repository trace)

`backend/app/models/sfv_requirement.py`:

```
trigger_source_type   = Column(String(32), nullable=False)   # 'INITIAL_RN_ICA' | 'HUV1' | 'HUV2'
trigger_reference_id  = Column(UUID(as_uuid=True), nullable=False)
...
UniqueConstraint(trigger_source_type, trigger_reference_id, name="uq_sfv_requirements_trigger_once")
```

**VERIFIED BY REPOSITORY TRACE.** The unique constraint proves the data
model already enforces "exactly one SFVRequirement per (timepoint,
triggering record)" — ownership is a first-class, already-enforced
concept in storage. The defect is not in the data model; it is in the
frontend query that ignores these two columns entirely.

### What `trigger_reference_id` actually points to

`backend/app/services/hope_phase_b_engine.py`:
- `process_initial_rn_ica_finalize(...)` → calls
  `maybe_trigger_sfv_from_hope_timepoint(trigger_source_type=SOURCE_INITIAL_RN_ICA, trigger_reference_id=initial_rn_ica_visit_id, ...)`
- `process_huv_finalize(...)` → calls
  `maybe_trigger_sfv_from_hope_timepoint(trigger_source_type=huv_task_type, trigger_reference_id=huv_visit_id, ...)`

Both are called from `backend/app/api/visits.py::_run_phase_b_finalize_hooks`
with `initial_rn_ica_visit_id=visit.id` / `huv_visit_id=visit.id` — i.e.
**`trigger_reference_id` is a `Visit.id`**, not a `RnicaAssessment.id`.
VERIFIED BY REPOSITORY TRACE.

### What the frontend export screen actually has in hand

`HopeReport.jsx` receives `assessmentMeta` (a serialized `RnicaAssessment`
row — see `ComplianceHopeBoard.jsx` lines 931/1041/1086 passing
`assessmentMeta={matchedAssessment}` / `assessment || {}`). It does
**not** receive a `visitId` at all today —
`backend/app/api/visits.py::_serialize_rnica_assessment` (line 128) does
not include `visit_id` in its payload. NOT_VERIFIED as currently wired;
this is a real, small gap in the fix path (see §4), not a defect in the
concept.

### The missing link that makes ownership resolvable without new storage

`backend/app/models/rnica_assessment.py`:

```
visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="SET NULL"), nullable=True, index=True)
hope_event_type = Column(String(20), nullable=True, doc="ADMISSION / HUV1 / HUV2 / DISCHARGE ...")
```

`RnicaAssessment` already carries **both** the `visit_id` that finalized
it **and** its own `hope_event_type`. This means the full ownership chain
already exists in the schema, end to end:

```
RnicaAssessment.id (assessmentId, known to HopeReport.jsx)
        -> RnicaAssessment.visit_id                     (exists, not yet exposed to the frontend)
        -> SFVRequirement.trigger_reference_id           (exact match, when
           SFVRequirement.trigger_source_type matches the assessment's
           hope_event_type: ADMISSION -> INITIAL_RN_ICA, HUV1 -> HUV1, HUV2 -> HUV2)
        -> SFVRequirement.completed_visit_id             (existing column)
        -> ClinicalNote.content.symptomImpact for that completion visit
        -> J2052 / J2053
```

**VERIFIED BY REPOSITORY TRACE.** No new column is required anywhere in
this chain. The only gap is that `_serialize_rnica_assessment` does not
currently return `visit_id`, and the frontend/API does not currently
query `SFVRequirement` filtered by `(trigger_source_type,
trigger_reference_id)`. Both are additive uses of existing columns, not
new schema.

---

## 2. Per-path trace: can another SFV be incorrectly chosen?

### ADM path

```
ADM (RnicaAssessment, hope_event_type=ADMISSION)
  -> J2051 trigger (moderate/severe symptom impact recorded on the same finalize call)
  -> process_initial_rn_ica_finalize(trigger_source_type=INITIAL_RN_ICA, trigger_reference_id=visit.id)
  -> SFVRequirement (trigger_source_type=INITIAL_RN_ICA, trigger_reference_id=<ADM visit id>)
  -> completed_visit_id -> ClinicalNote.content.symptomImpact
  -> J2052 / J2053
```

**Can another SFV be incorrectly chosen? YES.**
Proof: `HopeReport.jsx` (lines 162-176) calls `listSfvRequirements(patientId)`
(no `trigger_source_type`/`trigger_reference_id` filter), keeps only rows
with `status === "COMPLETED" && completedAt`, sorts by `completedAt`
descending, and takes `[0]`. If a later HUV1 or HUV2 SFV completes after
the ADM one, that later row — not the ADM-triggered
`SFVRequirement` — is what gets attached to the ADM export. Nothing in
the query constrains it to `trigger_source_type=INITIAL_RN_ICA`.

### HUV1 path

```
HUV1 (RnicaAssessment, hope_event_type=HUV1, assessment_type=UPDATE, locked=true, in HUV1 window)
  -> J2051 trigger (from that HUV1 visit's finalize call)
  -> process_huv_finalize(trigger_source_type=HUV1, trigger_reference_id=visit.id)
  -> SFVRequirement (trigger_source_type=HUV1, trigger_reference_id=<HUV1 visit id>)
  -> completed_visit_id -> ClinicalNote.content.symptomImpact
  -> J2052 / J2053
```

**Can another SFV be incorrectly chosen? YES.**
Same proof as ADM — the selection query in `HopeReport.jsx` is identical
regardless of `normalizedTimepoint`. If a later HUV2 SFV completes after
the HUV1 one, the HUV1 export receives the HUV2-triggered SFV instead.

### HUV2 path

```
HUV2 (RnicaAssessment, hope_event_type=HUV2, assessment_type=UPDATE, locked=true, in HUV2 window)
  -> J2051 trigger (from that HUV2 visit's finalize call)
  -> process_huv_finalize(trigger_source_type=HUV2, trigger_reference_id=visit.id)
  -> SFVRequirement (trigger_source_type=HUV2, trigger_reference_id=<HUV2 visit id>)
  -> completed_visit_id -> ClinicalNote.content.symptomImpact
  -> J2052 / J2053
```

**Can another SFV be incorrectly chosen? YES** (same mechanism; there is
no timepoint-specific branch anywhere in `HopeReport.jsx`'s selection
effect).

---

## 3. Root cause (single location, not three)

There is exactly one defective call site:
`sns-emr-frontend/src/intake/HopeReport.jsx`, lines 162-176
(`useEffect` populating `sfvRequirement` state via
`listSfvRequirements(patientId)` + sort + `[0]`).

- `mapRnIcaToHopeReport` itself is **not** defective — it correctly
  isolates whatever single `sfvRequirement` object it is handed
  (VERIFIED BY REPOSITORY TRACE, per the existing 3-way multi-SFV
  isolation test in `hopeReportMapper.test.js`).
- The backend `SFVRequirement` model and its trigger columns are **not**
  defective — the unique constraint and `trigger_source_type`/
  `trigger_reference_id` columns are exactly what a correct fix needs.
- `SfvStatusCard`'s equivalent "most-recently-completed" logic (referenced
  in `HopeReport.jsx`'s own code comment, line 158-159, "mirrors
  SfvStatusCard's own logic so both surfaces agree") is **out of scope**
  for HOPE export correctness specifically, but is flagged here as a
  second surface with the same pattern — NOT independently re-verified in
  this pass (NOT_VERIFIED whether `SfvStatusCard` has the same
  cross-timepoint consequence; it is a status-display surface, not an
  export surface, so the blast radius is different and was not traced
  further here).

---

## 4. Proposed ownership model (DESIGN ONLY — NOT IMPLEMENTED)

Replace the patient-level "most recently completed" query with a
trigger-scoped lookup, using only columns that already exist:

1. Expose `visitId` (`RnicaAssessment.visit_id`) in
   `_serialize_rnica_assessment` (additive field on an existing endpoint
   response — not a new table, not a new column).
2. Map the assessment's `hope_event_type` to the matching
   `SFVRequirement.trigger_source_type`:
   `ADMISSION -> INITIAL_RN_ICA`, `HUV1 -> HUV1`, `HUV2 -> HUV2`.
3. Query `SFVRequirement` filtered by
   `trigger_source_type = <mapped type> AND trigger_reference_id = <assessment's visitId>`
   instead of "all completed SFVs for the patient, most recent first."
4. If no `SFVRequirement` exists for that exact `(trigger_source_type,
   trigger_reference_id)` pair, J2052/J2053 must be left unset for that
   export — never fall back to a different timepoint's SFV.

This is a **reuse of existing columns only**: `RnicaAssessment.visit_id`,
`RnicaAssessment.hope_event_type`, `SFVRequirement.trigger_source_type`,
`SFVRequirement.trigger_reference_id` all already exist. No new field,
table, enum, or storage is proposed. This satisfies the standing reuse
priority order (existing field > existing JSON structure > existing
workflow > existing enum > new field > new schema) at the highest tier.

**This design is not implemented in this pass.** Per instruction, this
remains discovery/design only pending explicit approval to proceed.

---

## 5. Required response summary

| Question | Answer | Proof location |
|---|---|---|
| ADM→SFV linkage verified? | NO (not yet implemented; chain exists but frontend doesn't use it) | §1, §4 |
| HUV1→SFV linkage verified? | NO (same) | §1, §4 |
| HUV2→SFV linkage verified? | NO (same) | §1, §4 |
| Patient-level SFV selection present? | YES | §3, `HopeReport.jsx` lines 162-176 |
| Cross-timepoint leak confirmed? | YES (all 3 directional cases proven) | §2 |
| Fix requires new storage? | NO — existing columns are sufficient | §4 |

J2052 and J2053 status are downgraded to `OPEN_QUESTION` (source field
verified; ownership/selection not verified) in
`HOPE_ITEM_PROVENANCE_MATRIX.md`, consistent with this trace.
