# HUV2 Provenance Trace

Status labels per SNS Review Rule: VERIFIED BY CMS / VERIFIED BY REPOSITORY
TRACE / VERIFIED BY PRODUCTION CODE / NOT_VERIFIED / OPEN QUESTION.
Traced independently from HUV1 (see `HUV1_PROVENANCE_TRACE.md`) — no
assumption that HUV2 mirrors HUV1's correctness without its own citation.

## CMS requirement (VERIFIED BY CMS)

HOPE Update Visit 2 (HUV2) must be completed by an RN between days 16-30
after Day 0 (hospice election effective date), per the directive's cited
HOPE Guidance Manual v1.02.

## Timing window — VERIFIED BY REPOSITORY TRACE

`backend/app/api/visits.py::get_hope_update_status` (line 1017), same
Day-0 source as HUV1 (`current_admission.election_signed_at`, with the
same fallback chain). `_window_bounds(election_datetime, 16, 30)` (called
at line 1046) computes the HUV2 window as `election_datetime + 16 days`
through `election_datetime + 30 days` — VERIFIED BY REPOSITORY TRACE this
is the distinct 16-30 range, not a copy-paste of the HUV1 6-15 range.

Window matching reuses the same `_matches_huv_window(record,
election_datetime, TASK_TYPE_HUV2)` helper (line 232), passing the HUV2
task-type constant so `validate_huv_visit_completion` applies the HUV2-
specific CMS rule (distinct error text from HUV1's, per the function's
own docstring). Internal arithmetic of `validate_huv_visit_completion`
was not re-opened in this pass — NOT_VERIFIED at that depth (same caveat
as HUV1).

## Source record — VERIFIED BY REPOSITORY TRACE

Same query as HUV1 (`RnicaAssessment` filtered to `assessment_type ==
"UPDATE"`, `locked == True`, `admission_id == current_admission.id`,
lines 1047-1056) iterates the *same* candidate list and independently
tests each against the HUV2 window. A single locked Update Assessment
could in principle satisfy neither, either, or (if mis-timed) match only
one of HUV1/HUV2 — the loop tests both windows per record and stops
each independently once a match is found (`continue`/no early-exit
coupling between huv1/huv2 branches). No admission-data fallback exists
for HUV2 either — `huv2.assessment` is `null` with an explicit reason
string when no qualifying record exists.

## UI wiring — VERIFIED BY REPOSITORY TRACE

`ComplianceHopeBoard.jsx` line 1057-1064:
`renderHuvAssessment("HOPE - HUV2", ..., "HUV2", hopeUpdateStatus?.huv2)`
— same `renderHuvAssessment` function as HUV1 (lines 907-936), so the
same "Honest placeholder when no matched HUV2 record" behavior applies
(no fabricated/fallback data). `HopeReport` receives
`formData={matchedAssessment.formData}` (the HUV2 record's own data) and
`timepoint="HUV2"` when a match exists.

## Item-set behavior inside the mapper — VERIFIED BY REPOSITORY TRACE

Identical code path to HUV1 in `hopeReportMapper.js` (`timepoint ===
"HUV1" || timepoint === "HUV2"` conditions throughout — Section F
excluded, Z0350 added, `RECORD_REASON_BY_TIMEPOINT.HUV2` resolves A0250
to `"3 - HOPE Update Visit 2 (HUV2)"`). No HUV2-specific divergence found
or expected here beyond the reason-for-record code and timing window.

## NOT_VERIFIED

- Same completeness caveat as HUV1: full official CMS HUV2 item set was
  not cross-checked item-by-item against the mapper's current section
  selection in this pass.
- `validate_huv_visit_completion` internal arithmetic not re-verified.

## OPEN QUESTION — REQUIRES ROMEL DECISION

Same as the HUV1 finding: `HopeReport.jsx`'s `sfvRequirement` selection
(most-recently-completed for the patient, not scoped to the specific
HUV2 assessment/trigger) applies identically to HUV2 reports. See
`HUV1_PROVENANCE_TRACE.md`'s OPEN QUESTION section for the full
KNOWN/UNKNOWN FACTS, ARCHITECTURAL IMPACT, and OPTIONS — this is a single
shared open question across ADM/HUV1/HUV2 (one fix location:
`HopeReport.jsx`), not three separate ones. Not duplicated here to avoid
presenting one gap as three.
