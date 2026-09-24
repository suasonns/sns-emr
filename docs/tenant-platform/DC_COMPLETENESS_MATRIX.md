# DC Completeness Matrix

Status: Item-level completeness review, DC (Discharge) — 21 items:
Section A (18 items, same source/status as their ADM row) + 2
discharge-specific items (A0270, A2115) + Z0500. Confirmed via
`DC_PROVENANCE_TRACE.md` that Discharge does **not** emit J2052/J2053 at
all (no SFV section), so Discharge did not benefit from and is unaffected
by the SFV ownership remediation. This matrix reformats the
already-completed DC item trace on file in
`HOPE_ITEM_PROVENANCE_MATRIX.md`; no new repository research was
performed.

| CMS Item | SNS Source Record | SNS Source Field | Transformation | Validation | STATUS |
|---|---|---|---|---|---|
| A0050 | none (hardcoded) | literal string | `"1 - Add new record"` constant | none — always this value | NOT_VERIFIED |
| A0100 | Agency/tenant config | `agency.npi/.address/.phone` | passthrough | none — placeholder if absent | NOT_VERIFIED |
| A0215 | RnicaAssessment.form_data | `demographics.livingSituation.siteOfService` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | NOT_VERIFIED |
| A0220 | Patient / RnicaAssessment | `patient.socDate` ‖ `admissionsOrder.levelOfCare.effectiveDate` ‖ `completionDate` | 3-way fallback chain | none | NOT_VERIFIED |
| A0250 | derived from `options.timepoint` | `RECORD_REASON_BY_TIMEPOINT` map | direct lookup by timepoint | restricted to 4 known timepoint values | **VERIFIED** |
| A0500 | Patient | `patient` name fields via `splitPatientName` | string split | none | NOT_VERIFIED |
| A0550 | RnicaAssessment.form_data | `demographics.address.zip` | passthrough | none | NOT_VERIFIED |
| A0600 | Patient | `patient.ssn`, `.medicareNumber` | passthrough | none | NOT_VERIFIED |
| A0700 | Patient | `patient.medicaidNumber` | passthrough | none | NOT_VERIFIED |
| A0810 | RnicaAssessment.form_data / Patient | `demographics.gender` ‖ `patient.sex` | `SEX_MAP` lookup | restricted; unmapped → placeholder | NOT_VERIFIED |
| A0900 | RnicaAssessment.form_data / Patient | `demographics.dob` ‖ `patient.dob` | `formatDate` | none | NOT_VERIFIED |
| A1005 | RnicaAssessment.form_data | `demographics.ethnicity` | `arrayText` (raw join) | none | NOT_VERIFIED |
| A1010 | RnicaAssessment.form_data | `demographics.race` | `arrayText` (raw join) | none | NOT_VERIFIED |
| A1110 | RnicaAssessment.form_data | `demographics.preferredLanguage`, `.needsInterpreter` | passthrough / `boolCode` | none for language value | NOT_VERIFIED |
| A1400 | Patient | `patient.primaryPayerType`/`.secondaryPayerType` | `payerSources()` crosswalk | restricted to known payer crosswalk | NOT_VERIFIED |
| A1805 | RnicaAssessment.form_data | `demographics.livingSituation.admittedFrom` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | NOT_VERIFIED |
| A1905 | RnicaAssessment.form_data | `demographics.livingSituation.livingArrangement` | `officialCodeLookup` + legacy map | restricted; unmapped → placeholder | NOT_VERIFIED |
| A1910 | RnicaAssessment.form_data | `demographics.livingSituation.availabilityOfAssistance` | `ASSISTANCE_MAP` lookup | restricted; unmapped → placeholder | NOT_VERIFIED |
| A0270 | `patients` table | `discharge.dischargeDate` (via `options.discharge`, sourced from `patients.discharge_date`) | `formatDate` | none beyond date format | NOT_VERIFIED |
| A2115 | `patients` table | `discharge.reasonCode`/`.reasonLabel` (sourced from `patients.discharge_reason`) | code + label concat | **validated at capture time** — `finalize_patient_discharge` rejects any `reason_code` not in `GRANULAR_DISCHARGE_REASONS` (HTTP 422) | NOT_VERIFIED — validation exists and is real, but the registry's exact CMS-code accuracy was not independently cross-checked |
| Z0500 | RnicaAssessment.form_data | `finalization.{signatureCertification,clinicianSignature,signatureDate,hopeSubmissionNumber,hopeAlreadySubmitted}` | passthrough / `boolCode` | none beyond boolean/placeholder | NOT_VERIFIED |

## Summary

| Status | Count |
|---|---|
| VERIFIED | 1 (A0250) |
| NOT_VERIFIED | 20 |
| OPEN_QUESTION | 0 |
| **Total** | **21** |

**COMPLETENESS: NOT_VERIFIED. DENOMINATOR: NOT_VERIFIED.**

Same caveat: the 21-item denominator is an emitted-code count, not a
CMS-authority-confirmed applicable-item count. Retained:

- **CMS item-set version**: NOT_VERIFIED
- **Total applicable items**: NOT_VERIFIED (21 is emitted-code count)
- **Verified items**: 1 (A0250)
- **NOT_VERIFIED items**: 20
- **OPEN_QUESTION items**: 0
- **Blocked/Excluded items**: 0
- **Reproducible counting command**: none exists (hand-compiled)

Discharge does not export J2052/J2053, so it received no benefit from
the SFV ownership fix and carries no open questions from that
workstream (I0000/J2050 are also not emitted at Discharge — confirmed
via `DC_PROVENANCE_TRACE.md`'s 21-item scope). The single highest-value
item to check next is A2115: capture-time validation is real and
enforced, but the CMS-code accuracy of the `GRANULAR_DISCHARGE_REASONS`
registry itself was not independently cross-checked against CMS text
this pass.
