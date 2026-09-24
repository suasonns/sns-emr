# Discharge (DC) Provenance Trace

Status labels per SNS Review Rule: VERIFIED BY CMS / VERIFIED BY REPOSITORY
TRACE / VERIFIED BY PRODUCTION CODE / NOT_VERIFIED / OPEN QUESTION.
No ownership is assumed — RNICA, certification, and discharge-summary
ownership are each checked explicitly per the directive's instruction, not
presumed.

## Scope of the current Discharge HOPE record — VERIFIED BY REPOSITORY TRACE

`hopeReportMapper.js::mapRnIcaToHopeReport`, `isDischarge` branch (line
536, filters at line 727-728): when `timepoint === "DISCHARGE"`, the
returned report is filtered down to **only**:
- "Section A - Administrative Information" (which itself adds two
  discharge-specific items only in this branch: `A0270` Discharge Date and
  `A2115` Reason for Discharge — lines 632-636)
- "Z0500 - Signature of Person Verifying Record Completion"

All other sections (F/I/J/M/N — pain, symptoms, medications, skin,
diagnoses) are explicitly excluded for Discharge. This means the current
Discharge HOPE record does **not** claim ownership of clinical content at
all — it is scoped to administrative discharge facts + signature only.
This is a narrower scope than a full CMS HOPE Discharge item set may
require (see NOT_VERIFIED below), but it is not incorrectly attributing
clinical content to the wrong owner, since it does not attempt to source
any clinical section for Discharge at all.

## Source of A0270 / A2115 — VERIFIED BY REPOSITORY TRACE

- **Not RNICA-owned.** Discharge date/reason are read from `options.
  discharge` (`discharge.dischargeDate`, `discharge.reasonCode`,
  `discharge.reasonLabel`), passed into `mapRnIcaToHopeReport` by
  `HopeReport.jsx`'s caller — not from `formData` (the RNICA/assessment
  JSON blob).
- **Not certification-owned.** No reference to `certifications.py`,
  `certification_service.py`, or any certification/recertification model
  was found feeding the discharge branch (grep-confirmed; also consistent
  with the earlier HOPE-source-model correction removing certification as
  a source category).
- **Not discharge-summary-document-owned.** No reference to a narrative
  "discharge summary" document was found feeding these fields.
- **Actual owner: the `patients` table's own discharge columns**, via
  `backend/app/api/admissions.py`:
  - `GET /{patient_id}/discharge` (`get_discharge_planning`, line 412)
    reads `status, discharge_date, discharge_reason, discharge_
    initiated_by, discharge_projected_date, discharge_comments,
    discharge_plan_reviewed, discharge_notified, ...` directly from the
    `patients` table (lines 420-437) and returns them via `_serialize_
    discharge_state` (line 388), which is what `ComplianceHopeBoard.jsx`'s
    `fetchDischargePlanning(patientId)` call retrieves (`dischargeState`)
    and passes to `<HopeReport discharge={{dischargeDate: dischargeState.
    discharge_date, reasonCode, reasonLabel}} .../>` (lines 1080-1094).
  - `POST /{patient_id}/discharge/finalize` (`finalize_patient_discharge`,
    line 520) is the authoritative write path: it requires `payload.
    reason_code` to be a key in `GRANULAR_DISCHARGE_REASONS` (line
    526-531, rejecting any other value with HTTP 422) and resolves a
    `cms_code` from that registry (line 532) before persisting — VERIFIED
    BY REPOSITORY TRACE that `A2115`'s reason value is backed by a real,
    validated CMS-code registry, not free text.

## UI gating — VERIFIED BY REPOSITORY TRACE

`ComplianceHopeBoard.jsx` line 1066-1078: the Discharge HOPE view is only
rendered live when `dischargeState?.discharged` is true (i.e.
`patient.status == "DISCHARGED"`, per `_serialize_discharge_state` line
393); otherwise an explicit placeholder ("Not applicable — this patient
has not been discharged from hospice services.") is shown, with no
fabricated discharge data.

## NOT_VERIFIED

- Whether the official CMS HOPE Discharge item set requires any item
  beyond A0270/A2115/administrative-identity/Z0500 (e.g. discharge
  disposition detail beyond the reason code, discharge location, or
  discharge-time clinical status items) was not cross-checked against
  the CMS Discharge item set specification in this pass. If additional
  CMS-required Discharge items exist beyond what this mapper currently
  emits, that is a genuine coverage gap, not merely a provenance question
  — flagged here rather than assumed complete.
- `GRANULAR_DISCHARGE_REASONS`'s exact code list was not itself
  cross-checked against the CMS-published discharge reason code table in
  this pass (its existence and enforcement mechanism are VERIFIED BY
  REPOSITORY TRACE; its content-accuracy against CMS is NOT_VERIFIED).

## No open question escalated for Discharge

Unlike ADM/HUV1/HUV2, the Discharge branch of `mapRnIcaToHopeReport` does
not read `sfvRequirement` at all (J2052/J2053 are filtered out of the
Discharge section set), so the `HopeReport.jsx` "most-recent-SFV" open
question (see `HUV1_PROVENANCE_TRACE.md`) does not apply to Discharge.
