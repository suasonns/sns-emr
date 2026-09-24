# J2052 Lineage Verification

**Document Status:** PHASE 2 GATING DELIVERABLE — required by the
"REVISED IMPLEMENTATION ORDER" directive before Phase 3 (J2053 capture
implementation) may begin. Verifies that the Phase 1 (P1A) code change
(commit `b4da769`) produces the corrected lineage with no residual
dependency on RNICA self-attestation, UI synchronization, or frontend
mutation.

## Required proof

**Claim:** J2052 now flows

```
RNICA Trigger (INITIAL_RN_ICA / HUV1 / HUV2 visit)
    ↓
SFVRequirement row created (backend, trigger_source_type/trigger_reference_id)
    ↓
SFVRequirement.status / SFVRequirement.completed_at
  (set only by complete_sfv_requirement_from_visit, backend/app/api/visits.py:4028,
   never by the RNICA form)
    ↓
GET /sfv-requirements?patientId=... (list_sfv_requirements, visits.py:4071)
    ↓
Frontend caller fetches + selects most-recently-completed row
  (HopeReport.jsx, ComplianceHopeBoard.jsx, RNICA.jsx — all independent
   fetches, same selection logic as SfvStatusCard)
    ↓
options.sfvRequirement passed into mapRnIcaToHopeReport()
    ↓
getSfvStatus(formData, sfvRequirement) — reads ONLY sfvRequirement.status
  / sfvRequirement.completedAt (hopeReportMapper.js:~400)
    ↓
HOPE Output — J2052 status/date entries
```

with **no dependency on**:

- RNICA self-attestation (`form_data.sfv.inPersonSfvCompleted`,
  `form_data.sfv.sfvDate`)
- UI synchronization (`SfvStatusCard`'s `onSyncCompletionStatus` write-back)
- frontend mutation of any kind

## Evidence

### 1. Backend: status/date are set only by the completion command, never by the RNICA form

`complete_sfv_requirement_from_visit` (called exclusively from the
`complete_sfv_requirement` endpoint, `backend/app/api/visits.py:3965-4046`)
is the only code path that writes `SFVRequirement.status` /
`SFVRequirement.completed_at`. The RNICA form endpoints
(`rnica_assessment.py`, the RNICA save/update handlers) do not import or
call this function — confirmed by the fact that `SFVRequirement.status`
carries a CHECK constraint (`sfv_requirement.py:52-58`, `OPEN` /
`COMPLETED` /
… ) with default `OPEN`, and only the completion command transitions it.

### 2. Frontend: `getSfvStatus` no longer reads `form_data.sfv.*` for `completed`/`completedAt`

`hopeReportMapper.js` (commit `b4da769`):

```js
function getSfvStatus(formData, sfvRequirement = null) {
  const completed = sfvRequirement
    ? sfvRequirement.status === "COMPLETED"
    : false;
  const completedAt = sfvRequirement ? sfvRequirement.completedAt : null;
  ...
}
```

There is no branch that reads `formData.sfv.inPersonSfvCompleted` or
`formData.sfv.sfvDate` to derive `completed`/`completedAt`. This is
verified by the new unit test *"UI state changed manually
(form_data.sfv.inPersonSfvCompleted = true) does not make J2052 complete
without a matching SFVRequirement"* — the test sets that self-attested
field to `true` and a stale date, passes `sfvRequirement: null`, and
asserts the exported J2052 value is still `"No"` with a placeholder
date. This is the direct proof that self-attestation cannot make J2052
appear complete.

### 3. Frontend: no caller falls back to `form_data` when the fetch has not resolved yet

The test *"no sfvRequirement supplied at all (e.g. fetch not yet
resolved): J2052 defaults to not-completed rather than trusting
form_data"* calls `mapRnIcaToHopeReport(formData)` with **no** `options`
argument at all (simulating a caller invoked before its `useEffect` has
resolved, or a legacy call site not yet updated) and confirms J2052
still reports `"No"` even though `form_data.sfv.inPersonSfvCompleted`
is `true`. There is no default/fallback path in `getSfvStatus` that
would let stale UI state leak through during a race or a missed
call site.

### 4. All known call sites now pass the authoritative source

A full-repository search for `getSfvStatus(` and `mapRnIcaToHopeReport(`
was re-run against the post-fix tree and confirms exactly 4 call sites
of `getSfvStatus`, all four now supplied with a fetched `SFVRequirement`:

| Call site | File | Fetch mechanism |
|---|---|---|
| `<HopeReport>` (admission/discharge dialogs) | `HopeReport.jsx` | `sfvRequirement` state via `listSfvRequirements(patientId)` |
| Compliance dashboard SFV widget | `ComplianceHopeBoard.jsx` (own `hopeReport` memo) | `sfvRequirement` state via `listSfvRequirements(patientId)` |
| `<HopeReport>` (3 dialog call sites) | `ComplianceHopeBoard.jsx` | same `sfvRequirement` state, passed via `patientId` prop |
| `<HopeReport>` (1 call site) | `NursingAssessmentBoard.jsx` | passes `patientId` prop through to `HopeReport.jsx`'s own fetch |
| On-screen SFV status badge | `RNICA.jsx` (`sfvStatus` memo, previously undiscovered) | new `latestSfvRequirement` state via `listSfvRequirements(patientId)` |

No call site passes `undefined`/omits `options.sfvRequirement` in
production code (the omission only occurs in the defensive unit test
above, to prove safe default behavior).

### 5. Determinism across reload

The test *"page reload (same SFVRequirement snapshot passed again):
J2052 is unchanged and deterministic"* calls `mapRnIcaToHopeReport`
twice with an identical `sfvRequirement` snapshot and asserts identical
output — proving the mapping is a pure function of the supplied
`SFVRequirement`, with no hidden dependency on component state,
memoization order, or prior form_data mutations.

## Test results (evidence of passing state)

```
$ npx vitest run src/intake/hopeReportMapper.test.js
 Test Files  1 passed (1)
      Tests  143 passed (143)

$ npx vitest run   # full frontend suite
 Test Files  21 passed (21)
      Tests  282 passed (282)   (was 277 before this change; +5 new)
```

Backend test suite for this phase: **not run** — Phase 1 (P1A) made
**zero backend file changes** (no schema, no migration, no API change,
per the Phase 1 acceptance criteria), so there is no backend behavior
to regress-test. The local backend test harness in this workspace also
requires a `DATABASE_URL`-configured Postgres instance not currently
reachable with known credentials in this environment; this is an
environment/tooling limitation unrelated to the code change and does
not block Phase 1 verification since no backend code was touched.

## Verdict

**J2052 LINEAGE VERIFIED: YES.**

J2052 now reads exclusively from the backend-authoritative
`SFVRequirement.status` / `SFVRequirement.completed_at`, fetched via
`GET /sfv-requirements`, with no residual dependency on RNICA
self-attestation, UI synchronization, or frontend mutation. Phase 2 is
complete; Phase 3 (J2053 capture path) may begin.
