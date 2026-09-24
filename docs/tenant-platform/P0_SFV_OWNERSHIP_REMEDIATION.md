# P0 SFV Ownership Remediation

Status: **REMEDIATION DESIGN — implementation not yet started in this
document.** Discovery is complete and closed per instruction; this
document is the concrete engineering plan derived directly from the
already-committed proofs in `SFV_TRIGGER_OWNERSHIP_TRACE.md` and
`SFV_OWNERSHIP_TRACE.md`. No further leakage-proof work is performed
here.

---

## Current Logic

**Current file:** `sns-emr-frontend/src/intake/HopeReport.jsx`

**Current query** (lines 162-176):

```js
listSfvRequirements(patientId)
  .then((rows) => {
    if (cancelled) return;
    const completedRows = (rows || []).filter((r) => r.status === "COMPLETED" && r.completedAt);
    const latest = completedRows.sort((a, b) => (a.completedAt < b.completedAt ? 1 : -1))[0];
    setSfvRequirement(latest || null);
  })
```

**Current selection rule:** "the single most-recently-completed
SFVRequirement across the entire patient, regardless of which HOPE
record (`timepoint`/`assessmentMeta`) is being exported." No filter on
`trigger_source_type` or `trigger_reference_id` exists anywhere in this
function.

---

## Correct Selection Rule

"The SFVRequirement whose `trigger_source_type` matches this HOPE
record's own timepoint AND whose `trigger_reference_id` equals the
`Visit.id` that finalized this specific `RnicaAssessment` — never the
patient's most recent SFV, never a different timepoint's SFV, and never
a fallback when no exact match exists."

```
timepoint  -> expected trigger_source_type
ADMISSION  -> INITIAL_RN_ICA
HUV1       -> HUV1
HUV2       -> HUV2
DISCHARGE  -> (none -- mapper already excludes J2052/J2053 for Discharge)

match = SFVRequirement WHERE
  trigger_source_type == expected trigger_source_type
  AND trigger_reference_id == RnicaAssessment.visit_id (of the record being exported)
  AND status == "COMPLETED"
  AND completedAt IS NOT NULL

if no match: sfvRequirement = null  (never fall back to "most recent")
```

This uses **only existing columns** — confirmed in
`SFV_TRIGGER_OWNERSHIP_TRACE.md` §1/§4. No migration, no new table, no
new enum.

---

## Files Impacted

### 1. `backend/app/api/visits.py` — expose two existing columns that are not yet returned to the frontend

- `SfvRequirementSummary` (Pydantic response model, line 4105): add one
  field, `triggerSourceType: str`, sourced from the already-existing
  `SFVRequirement.trigger_source_type` column.
- `list_sfv_requirements` (line 4164): add
  `triggerSourceType=r.trigger_source_type` to the `SfvRequirementSummary(...)`
  construction. Existing query/filtering/authorization logic is
  unchanged.
- `_serialize_rnica_assessment` (line 128): add one field,
  `"visitId": str(record.visit_id) if record.visit_id else None`,
  sourced from the already-existing `RnicaAssessment.visit_id` column.

No new columns, no new endpoints, no schema/migration. Purely additive
fields on two existing response payloads.

### 2. `sns-emr-frontend/src/api/sfv.ts` — mirror the new field in the TS contract

- `SfvRequirementSummary` interface: add `triggerSourceType: string;`
  (mirrors the backend Pydantic field 1:1, per existing convention in
  this file).

### 3. `sns-emr-frontend/src/intake/HopeReport.jsx` — replace the selection query

- Add a small `HOPE_EVENT_TYPE_TO_TRIGGER_SOURCE` constant mapping
  `ADMISSION -> INITIAL_RN_ICA`, `HUV1 -> HUV1`, `HUV2 -> HUV2` (no entry
  for `DISCHARGE`, consistent with the mapper's existing Section
  A/Z0500-only scope for Discharge — see `DC_PROVENANCE_TRACE.md`).
- Replace the `useEffect` at lines 162-176 to require both
  `assessmentMeta?.visitId` and the mapped expected
  `trigger_source_type`, and to `find()` the one matching row instead of
  sorting all completed rows patient-wide. If either input is missing,
  or no match is found, `sfvRequirement` is set to `null` — never a
  fallback to "most recent."

### 4. Callers of `HopeReport` — no change expected, but must be verified

- `ComplianceHopeBoard.jsx` (lines 931, 1041, 1086): passes
  `assessmentMeta={matchedAssessment}` / `assessment || {}` — these
  objects come directly from the backend's `_serialize_rnica_assessment`
  payload, so once `visitId` is added there, it flows through
  automatically. **No code change anticipated here**, but this must be
  confirmed once the backend change lands (the object is not
  re-shaped/whitelisted anywhere between the API call and this prop —
  NOT_VERIFIED until traced at implementation time; flagged so it isn't
  silently assumed).
- `NursingAssessmentBoard.jsx` (line 394): passes
  `assessmentMeta={{ locked: false }}` (no `visitId`) for an in-progress
  editing preview, not a finalized export. Under the corrected rule this
  correctly yields `sfvRequirement = null` (no SFV can exist yet for an
  unfinalized record) rather than crashing — this is the intended
  behavior, not a regression.

**Estimated file count: 3 modified** (`visits.py`, `sfv.ts`,
`HopeReport.jsx`). Zero new files, zero schema/migration files.

---

## Tests Required

New/updated automated tests (none written yet — listed as required):

1. **Backend:** `list_sfv_requirements` returns `triggerSourceType` for
   each row (unit/contract test on `SfvRequirementSummary` shape).
2. **Backend:** `_serialize_rnica_assessment` / the ADM/HUV1/HUV2 GET
   endpoints return `visitId` matching the underlying `RnicaAssessment.visit_id`.
3. **Frontend (`HopeReport.jsx` / `hopeReportMapper` integration):**
   - ADM Trigger A → SFV A; HUV1 Trigger B → SFV B. Export ADM → uses
     SFV A, never SFV B.
   - Same setup. Export HUV1 → uses SFV B, never SFV A.
   - ADM Trigger A / HUV1 Trigger B / HUV2 Trigger C, all three present.
     Export ADM → uses A only. Export HUV1 → uses B only. Export HUV2 →
     uses C only. No crossover in either direction.
   - A newer SFV completes after an older HOPE record's own SFV. Export
     the older HOPE record → still uses its own (older) SFV, not the
     newer one.
   - No matching SFVRequirement exists for the record being exported →
     `sfvRequirement` is `null` (J2052/J2053 left unset), never a
     fallback to any other SFV.
4. **Regression:** existing 3-way multi-SFV isolation test in
   `hopeReportMapper.test.js` must continue to pass unchanged — the
   mapper function itself is not being modified, only its caller.

These map directly to the acceptance-test scenarios already specified in
the remediation directive (ADM/HUV1/HUV2 triggers, no crossover) and in
`SFV_OWNERSHIP_TRACE.md`'s 7 acceptance tests — this document does not
re-derive them, it assigns them to the concrete files above.

---

## Required response summary

| Question | Answer |
|---|---|
| File to modify | `backend/app/api/visits.py`, `sns-emr-frontend/src/api/sfv.ts`, `sns-emr-frontend/src/intake/HopeReport.jsx` |
| Schema/migration required | NO |
| New endpoint required | NO |
| Estimated file count | 3 |
| Ready to implement | YES — plan is fully concrete, no open unknowns remain except the one flagged NOT_VERIFIED caller-passthrough check in `ComplianceHopeBoard.jsx`, which the plan already accounts for and will confirm during implementation, not block on |
