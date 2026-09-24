# HUV1 Provenance Trace

Status labels per SNS Review Rule: VERIFIED BY CMS / VERIFIED BY REPOSITORY
TRACE / VERIFIED BY PRODUCTION CODE / NOT_VERIFIED / OPEN QUESTION.
No assumption is made about source without a cited file/line.

## CMS requirement (VERIFIED BY CMS)

HOPE Update Visit 1 (HUV1) must be completed by an RN between days 6-15
after Day 0 (hospice election effective date), per the directive's cited
HOPE Guidance Manual v1.02.

## Timing window — VERIFIED BY REPOSITORY TRACE

`backend/app/api/visits.py::get_hope_update_status` (`GET
/rnica/hope-update-status/{patient_id}`, line 1017):
- Day 0 is `current_admission.election_signed_at` (falling back to
  `soc_date`/`effective_date`/`admission_date` only if election date is
  absent) — VERIFIED BY REPOSITORY TRACE matching the CMS Day-0 definition.
- `_window_bounds(election_datetime, 6, 15)` (line 225) computes the HUV1
  window as `election_datetime + 6 days` through `election_datetime + 15
  days` — VERIFIED BY REPOSITORY TRACE that the 6-15 day range is
  implemented exactly as CMS specifies (not off-by-one; not assumed).
- Window/candidate matching is delegated to
  `validate_huv_visit_completion(...)` (called from `_matches_huv_window`,
  line 232), which raises the *actual* CMS violation message (e.g. "HUV1
  must be completed on or between days 6 and 15") rather than the caller
  re-implementing the rule. The exact contents of
  `validate_huv_visit_completion` were not re-opened in this pass — its
  existence and call-site contract are VERIFIED BY REPOSITORY TRACE; its
  internal correctness is NOT independently re-verified here (it was
  already exercised by `_matches_huv_window`'s own error-message
  round-trip in existing code, not by this trace).

## Source record — VERIFIED BY REPOSITORY TRACE

- HUV1 is **not** generated from the original admission `RnicaAssessment`
  row. `get_hope_update_status` queries `RnicaAssessment` filtered to
  `assessment_type == "UPDATE"`, `locked == True`, and
  `admission_id == current_admission.id` (lines 1047-1056), then evaluates
  each locked update-assessment candidate against the HUV1 window via
  `_matches_huv_window`. The first candidate whose completion falls in the
  window is returned as `huv1.assessment`; this is a **distinct row**,
  not a fallback to the admission's own data.
- If no locked Update Assessment falls in the window, `huv1.assessment`
  is `null` and a `reason` string is returned instead
  (`"No RN ICA Update Assessment has been locked for this admission
  yet."` or the specific CMS-window mismatch reason). No synthetic/
  fabricated HUV1 data is produced.

## UI wiring — VERIFIED BY REPOSITORY TRACE

`sns-emr-frontend/src/intake/ComplianceHopeBoard.jsx`:
- `renderHuvAssessment(label, description, "HUV1", hopeUpdateStatus?.huv1)`
  (lines 907-936, called at line 1048-1055 for `selectedSection ===
  "hope-huv1"`) only renders a live `<HopeReport timepoint="HUV1" ...>`
  when `hopeUpdateStatus.huv1.assessment` is present; otherwise it renders
  an explicit "Honest placeholder" (line 1422's `status` badge logic;
  visible copy: "No locked Update Assessment in window yet"). There is
  **no code path** that substitutes the admission assessment's data for a
  missing HUV1 record — VERIFIED BY REPOSITORY TRACE this does not recreate
  the "generic follow-up/certification fallback" anti-pattern the earlier
  HOPE source-model directive required removing.
- When a real HUV1 record exists, `HopeReport` is called with
  `formData={matchedAssessment.formData}` (the HUV1 assessment's own
  `form_data`, not the admission's) and `timepoint="HUV1"`.

## Item-set behavior inside the mapper — VERIFIED BY REPOSITORY TRACE

`sns-emr-frontend/src/intake/hopeReportMapper.js::mapRnIcaToHopeReport`,
given `timepoint: "HUV1"`:
- `A0250` (Reason for Record) resolves to `"2 - HOPE Update Visit 1
  (HUV1)"` via `RECORD_REASON_BY_TIMEPOINT` (line 39-44) — VERIFIED BY
  REPOSITORY TRACE (also covered by an existing test:
  `hopeReportMapper.test.js` "maps A0250 to the HUV1 reason-for-record
  code").
- Section F ("Preferences" — F2000/F2100/F2200/F3000) is excluded for
  HUV1/HUV2 (final `.filter(...)`, line 727) — these are one-time
  admission-only advance-care-planning discussion items, not repeated at
  each update visit.
- `Z0350` (Date Assessment Completed) is added for HUV1/HUV2 only (line
  714-716).
- Sections A, I, J, M, N are otherwise rendered from the same field paths
  as the admission report, sourced from the HUV1 assessment's own
  `form_data` (not the admission's), since `formData` passed to the mapper
  is now the HUV1 record's data (see UI wiring above).

## NOT_VERIFIED

- Whether the full official CMS HUV1 item set (every required item code)
  is covered by the mapper's current Section A/I/J/M/N selection was not
  cross-checked item-by-item against the CMS HUV1 item set specification
  in this pass — this trace confirms *source correctness* for the items
  the mapper does produce, not *completeness* against the full CMS HUV1
  item list.
- `validate_huv_visit_completion`'s internal day-boundary arithmetic
  (inclusive/exclusive edges, timezone handling) was not re-opened/
  re-verified line-by-line in this pass.
- J2052/J2053 (SFV-linked items) inside a HUV1 report: `sfvRequirement`
  is passed into `mapRnIcaToHopeReport` via `options.sfvRequirement`
  from `HopeReport.jsx`. **`HopeReport.jsx` currently selects
  `sfvRequirement` as "the most recently completed SFVRequirement for
  the patient overall"** (lines ~168-176: `listSfvRequirements(patientId)
  ... .sort((a,b)=> ...).completedAt ...)[0]`), not one scoped to the
  specific HUV1 assessment/trigger being viewed. This is flagged as an
  **OPEN QUESTION** below — it is a patient-level "latest completed SFV"
  selection, which is the same shape of shortcut the multi-SFV isolation
  requirement explicitly warned against, though the *exporter function
  itself* (`mapRnIcaToHopeReport`) does correctly isolate per whichever
  `sfvRequirement` object it is given.

## OPEN QUESTION — REQUIRES ROMEL DECISION

**KNOWN FACTS**
- `HopeReport.jsx` fetches all of a patient's `SFVRequirement`s and picks
  the single most-recently-completed one, regardless of which timepoint
  (ADM/HUV1/HUV2) the report is being rendered for.
- `mapRnIcaToHopeReport` itself has no cross-assignment bug — it renders
  whatever `sfvRequirement` object it receives with correct per-record
  isolation (VERIFIED — see `hopeReportMapper.test.js` 3-way multi-SFV
  test).

**UNKNOWN FACTS**
- Whether a HUV1/HUV2 HOPE report is only ever viewed for a patient with
  at most one relevant open/completed SFVRequirement per window (making
  "most recent" incidentally correct in practice), or whether a patient
  could have multiple SFVRequirements whose trigger windows span more
  than one timepoint's report, making the current selection produce the
  wrong SFV's J2052/J2053 values on a HUV1 or HUV2 report.

**CMS REQUIREMENT**: J2052/J2053 on a given HOPE record must reflect the
SFV triggered by that record's own screening (ADM, HUV1, or HUV2), not an
unrelated later/earlier SFV.

**REPOSITORY EVIDENCE**: `HopeReport.jsx` lines ~168-176 (patient-level
"latest completed" selection, not admission/timepoint-scoped).

**ARCHITECTURAL IMPACT**: If confirmed as a real cross-assignment risk,
this affects `HopeReport.jsx` only (a UI wiring fix — pass the SFV
requirement whose `trigger_source_type`/`trigger_reference_id` matches
the record being viewed), not the mapper or the SFVRequirement schema.

**OPTIONS**
- OPTION A: Scope the `listSfvRequirements` selection to the specific
  `trigger_reference_id` (the ADM/HUV1/HUV2 assessment id) of the record
  being viewed, instead of "most recent for patient."
- OPTION B: Leave as-is if it is confirmed that HOPE reports are only
  ever generated after full closure of prior SFV cycles, making
  "most recent" always correct in practice — requires evidence, not
  assumption.

**REQUIRES ROMEL DECISION** — no option selected or implemented here.
