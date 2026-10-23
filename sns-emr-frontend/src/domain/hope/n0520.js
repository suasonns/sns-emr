// PRODUCT OWNER IMPLEMENTATION DIRECTIVE (2026-10-21) "GI Cleanup and HOPE
// N0520" Sections 7-12 -- ONE authoritative N0520-applicability selector
// and CMS code mapping, shared by the RNICA GI UI (`RNICA.jsx`) and the
// HOPE export mapper (`hopeReportMapper.js`) so this condition is never
// reimplemented a second time.
//
// HOPE N0520 ("Bowel Regimen") is applicable ONLY when a Scheduled Opioid
// (N0500A) or PRN Opioid (N0510A) was initiated or continued on this
// assessment. Per the directive, applicability is explicitly NEVER based
// on: pain severity, any GI symptom (nausea/vomiting/constipation/etc.),
// an opioid being "merely present" on the medication list with no
// initiated/continued status, or an opioid order that was NOT initiated/
// continued. `medications.scheduledOpioid`/`medications.prnOpioid` are the
// only two HOPE-defined N0500A/N0510A "initiated or continued" booleans.
export function isN0520Applicable(medications = {}) {
  return Boolean(medications.scheduledOpioid) || Boolean(medications.prnOpioid);
}

// The 3 structured response options the GI "HOPE N0520: Bowel Regimen"
// block offers once `isN0520Applicable` is true, and their CMS codes.
export const BOWEL_REGIMEN_RESPONSE_YES = "Yes";
export const BOWEL_REGIMEN_RESPONSE_NO_REASON_DOCUMENTED = "No - Reason Documented";
export const BOWEL_REGIMEN_RESPONSE_NO_NO_REASON = "No - No Documented Reason";

export const BOWEL_REGIMEN_RESPONSE_OPTIONS = [
  BOWEL_REGIMEN_RESPONSE_YES,
  BOWEL_REGIMEN_RESPONSE_NO_REASON_DOCUMENTED,
  BOWEL_REGIMEN_RESPONSE_NO_NO_REASON,
];

// Clinician-facing option labels for the GI UI's segmented control only
// (per the originating directive's exact wording -- no CMS code is ever
// shown in the UI). `value` is unchanged from `BOWEL_REGIMEN_RESPONSE_OPTIONS`
// above (still what gets stored and fed into `bowelRegimenCmsCode`); only
// the displayed `label` differs, via the existing `{value, label}` option
// support `FormSegmented` already provides (see its RNICA.jsx precedent
// at the location-side selector). No data/CMS-mapping change.
export const BOWEL_REGIMEN_RESPONSE_UI_OPTIONS = [
  { value: BOWEL_REGIMEN_RESPONSE_YES, label: "Yes" },
  { value: BOWEL_REGIMEN_RESPONSE_NO_REASON_DOCUMENTED, label: "No, reason documented" },
  { value: BOWEL_REGIMEN_RESPONSE_NO_NO_REASON, label: "No, no documented reason" },
];

const BOWEL_REGIMEN_RESPONSE_CODES = Object.freeze({
  [BOWEL_REGIMEN_RESPONSE_YES]: "2",
  [BOWEL_REGIMEN_RESPONSE_NO_REASON_DOCUMENTED]: "1",
  [BOWEL_REGIMEN_RESPONSE_NO_NO_REASON]: "0",
});

const BOWEL_REGIMEN_RESPONSE_DESCRIPTIONS = Object.freeze({
  [BOWEL_REGIMEN_RESPONSE_YES]: "Yes",
  [BOWEL_REGIMEN_RESPONSE_NO_REASON_DOCUMENTED]: "No - reason documented",
  [BOWEL_REGIMEN_RESPONSE_NO_NO_REASON]: "No - no documented reason",
});

// Reasons offered when the response is "No - Reason Documented". Exact
// wording per the originating directive's required reason list (CMS
// HOPE N0520 exception context, not a general GI finding list). The last
// entry ("Other clinical contraindication") reveals a short free-text
// field (stored in the pre-existing `reasonBowelRegimenNotInitiated`
// path, which is also the historical free-text field this directive
// retires from general GI use -- reused here, not duplicated, so
// pre-existing historical entries remain readable with no data
// migration).
export const BOWEL_REGIMEN_OTHER_REASON = "Other clinical contraindication";

export const BOWEL_REGIMEN_NOT_INITIATED_REASONS = [
  "Patient or representative declined",
  "Bowel obstruction or ileus",
  "Diarrhea",
  "No bowel function",
  "Colostomy or ileostomy",
  "Nausea or vomiting",
  "Recent abdominal surgery",
  "NPO",
  BOWEL_REGIMEN_OTHER_REASON,
];

// CMS code "9" ("Not applicable") is the established convention already
// used elsewhere in this mapper (see the standardized-pain-tool mapping)
// for a HOPE item that is skip-logic-excluded rather than unanswered.
export function bowelRegimenCmsCode(medications, bowelRegimenResponse) {
  if (!isN0520Applicable(medications)) {
    return ["9", "Not applicable"];
  }
  const code = BOWEL_REGIMEN_RESPONSE_CODES[bowelRegimenResponse];
  if (!code) {
    return null; // applicable but not yet answered -- caller renders the incomplete-data placeholder.
  }
  return [code, BOWEL_REGIMEN_RESPONSE_DESCRIPTIONS[bowelRegimenResponse]];
}

// Forward-only legacy fallback: assessments recorded before this
// structured workflow existed only ever wrote a plain
// `medications.bowelRegimen` boolean. Never migrates/overwrites that
// legacy value -- only used to derive a response when the new structured
// field was never recorded for that (older) assessment.
export function legacyBowelRegimenResponse(medications = {}) {
  if (medications.bowelRegimen === true) return BOWEL_REGIMEN_RESPONSE_YES;
  if (medications.bowelRegimen === false && isN0520Applicable(medications)) return BOWEL_REGIMEN_RESPONSE_NO_NO_REASON;
  return "";
}
