// Shared Diagnosis & LCD derivation logic (data-only, no JSX, no styling).
//
// Extracted verbatim (behavior-preserving) from the legacy RNICA.jsx
// Diagnoses module so the same single source of truth can be reused by
// both:
//   - the legacy generic-section renderer (RNICA.jsx's renderGenericSection,
//     still the data-entry surface for PrimaryTerminalDiagnosisCard /
//     SecondaryDiagnosesCard / HopeComorbiditiesCard / LcdEligibilityCard /
//     LcdSupportingEvidenceCard), and
//   - the new "Diagnosis & LCD" summary screen (DiagnosisLcdOverview.jsx).
//
// Nothing here changes a field, option, HOPE mapping, or validation rule --
// it only centralizes the pure read-only functions that turn already-
// charted diagnosis/comorbidity fields into compact chip/pill summaries,
// so both surfaces agree on what counts as "checked"/"documented" instead
// of two copies drifting apart. Mirrors painLogic.js's precedent.
import { formatIcd10Code } from "../../../utils/formatIcd10";

// Verbatim from RNICA.jsx's HOPE_COMORBIDITY_CATEGORIES -- keep in sync if
// that list ever changes (category keys, hopeCode, regex, group).
export const HOPE_COMORBIDITY_CATEGORIES = [
  { key: "cancer", hopeCode: "I0100", label: "Cancer", shortLabel: "Cancer", group: "Cancer", regex: /^C\d/i },
  { key: "heartFailure", hopeCode: "I0600", label: "Heart Failure (e.g., CHF, pulmonary edema)", shortLabel: "Heart Failure", group: "Heart/Circulation", regex: /^I50/i },
  { key: "pvdPad", hopeCode: "I0900", label: "Peripheral Vascular Disease (PVD) or Peripheral Arterial Disease (PAD)", shortLabel: "PVD/PAD", group: "Heart/Circulation", regex: /^I7[03]/i },
  { key: "cardiovascularExclHF", hopeCode: "I0950", label: "Cardiovascular (excluding heart failure)", shortLabel: "Cardiovascular Disease", group: "Heart/Circulation", regex: /^I(1[0-3]|15|2[0-5])/i },
  { key: "liverDisease", hopeCode: "I1101", label: "Liver disease (e.g., cirrhosis)", shortLabel: "Liver Disease", group: "Gastrointestinal", regex: /^K7[0-4]/i },
  { key: "renalDisease", hopeCode: "I1510", label: "Renal disease", shortLabel: "Renal Disease", group: "Genitourinary", regex: /^(N18|N19)/i },
  { key: "sepsis", hopeCode: "I2102", label: "Sepsis", shortLabel: "Sepsis", group: "Infections", regex: /^A41/i },
  { key: "diabetesMellitus", hopeCode: "I2900", label: "Diabetes Mellitus (DM)", shortLabel: "Diabetes", group: "Metabolic", regex: /^E(0[89]|1[013])/i },
  { key: "neuropathy", hopeCode: "I2910", label: "Neuropathy", shortLabel: "Neuropathy", group: "Metabolic", regex: /^(G6[023]|E1[013]\.4|E08\.4|E09\.4)/i },
  { key: "stroke", hopeCode: "I4501", label: "Stroke", shortLabel: "Stroke", group: "Neurological", regex: /^(I6[0-3]|I65|I66|I69)/i },
  { key: "dementia", hopeCode: "I4801", label: "Dementia (including Alzheimer's disease)", shortLabel: "Dementia", group: "Neurological", regex: /^(F0[0-3]|G30|G31\.1)/i },
  { key: "neurologicalConditions", hopeCode: "I5150", label: "Neurological Conditions (e.g., Parkinson's disease, MS, ALS)", shortLabel: "Parkinson's/MS/ALS", group: "Neurological", regex: /^(G20|G35|G12\.2)/i },
  { key: "seizureDisorder", hopeCode: "I5401", label: "Seizure Disorder", shortLabel: "Seizure Disorder", group: "Neurological", regex: /^G40/i },
  { key: "copd", hopeCode: "I6202", label: "Chronic Obstructive Pulmonary Disease (COPD)", shortLabel: "COPD", group: "Pulmonary", regex: /^J44/i },
];

// Verbatim from RNICA.jsx's HOPE_PRINCIPAL_DIAGNOSIS_CATEGORY_OPTIONS.
export const HOPE_PRINCIPAL_DIAGNOSIS_CATEGORY_OPTIONS = [
  { value: "01", label: "01 — Cancer" },
  { value: "02", label: "02 — Dementia (including Alzheimer's disease)" },
  { value: "03", label: "03 — Neurological Condition (e.g., Parkinson's disease, MS, ALS)" },
  { value: "04", label: "04 — Stroke" },
  { value: "05", label: "05 — Chronic Obstructive Pulmonary Disease (COPD)" },
  { value: "06", label: "06 — Cardiovascular (excluding heart failure)" },
  { value: "07", label: "07 — Heart Failure" },
  { value: "08", label: "08 — Liver Disease" },
  { value: "09", label: "09 — Renal Disease" },
  { value: "99", label: "99 — None of the above" },
];

function matchesCategory(icd10, regex) {
  const code = (icd10 || "").trim().toUpperCase();
  if (!code) return false;
  return regex.test(code);
}

/** Verbatim from RNICA.jsx's categorizeIcd10. */
export function categorizeIcd10(icd10) {
  return HOPE_COMORBIDITY_CATEGORIES.find((cat) => matchesCategory(icd10, cat.regex)) || null;
}

export const joinList = (arr) => (Array.isArray(arr) && arr.length ? arr.join(", ") : "");

/** Primary diagnosis display facts -- ICD-10, description, HOPE I0010
 * category label, onset date, terminal prognosis. Read-only restatement of
 * fields owned/edited by PrimaryTerminalDiagnosisCard; never auto-fills or
 * overwrites anything. */
export function summarizePrimaryDiagnosis(diagnosesData) {
  const primary = diagnosesData?.primaryDiagnosis || {};
  const hopeCategoryLabel = HOPE_PRINCIPAL_DIAGNOSIS_CATEGORY_OPTIONS.find(
    (o) => o.value === primary.hopeDiagnosisCategory,
  )?.label || "";
  return {
    icd10: primary.icd10 ? formatIcd10Code(primary.icd10) : "",
    description: primary.description || "",
    hopeCategoryLabel,
    onsetDate: primary.onsetDate || "",
    terminalPrognosis: diagnosesData?.terminalPrognosis || "",
  };
}

/** One chip label per secondary diagnosis row ("ICD-10 Description"),
 * skipping fully-empty rows. Verbatim shape from SecondaryDiagnosisSearchRow
 * / SecondaryDiagnosesCard's own row rendering. */
export function summarizeSecondaryDiagnoses(diagnosesData) {
  return (diagnosesData?.secondaryDiagnoses || [])
    .filter((dx) => dx?.icd10 || dx?.description)
    .map((dx) => `${dx.icd10 ? formatIcd10Code(dx.icd10) : ""} ${dx.description || ""}`.trim());
}

/** Names of currently-checked HOPE comorbidity categories (+ "Other Medical
 * Condition" when checked), for a compact chip summary. Mirrors
 * HopeComorbiditiesCard's own `selectedSummary` derivation exactly
 * (principal-category exclusion + the cancer carve-out) -- keep the two in
 * sync if that gating logic ever changes. */
export function summarizeComorbidities(diagnosesData) {
  const primaryIcd10 = diagnosesData?.primaryDiagnosis?.icd10 || "";
  const secondaryDx = diagnosesData?.secondaryDiagnoses || [];
  const hope = diagnosesData?.hopeComorbidities || {};
  const principalCategory = categorizeIcd10(primaryIcd10);
  const autoDetected = new Set();
  secondaryDx.forEach((dx) => {
    const cat = categorizeIcd10(dx?.icd10);
    if (cat) autoDetected.add(cat.key);
  });
  const isChecked = (cat) => {
    const isPrincipal = principalCategory?.key === cat.key;
    const detected = autoDetected.has(cat.key);
    const cancerException = cat.key === "cancer" && isPrincipal && detected;
    const excluded = isPrincipal && !cancerException;
    return excluded ? false : Boolean(hope[cat.key]);
  };
  const names = HOPE_COMORBIDITY_CATEGORIES.filter(isChecked).map((cat) => cat.shortLabel || cat.label);
  if (hope.other) names.push("Other Medical Condition");
  return names;
}

/** Final-verification readiness checklist -- composite, auto-computed from
 * fields already captured elsewhere on this screen. Read-only; never
 * blocks, never writes. */
export function computeDiagnosisVerificationChecklist(diagnosesData) {
  const primary = diagnosesData?.primaryDiagnosis || {};
  const secondaryCount = (diagnosesData?.secondaryDiagnoses || []).filter((dx) => dx?.icd10 || dx?.description).length;
  const comorbidityCount = summarizeComorbidities(diagnosesData).length;
  const contributingIncomplete = (diagnosesData?.contributingConditions || [])
    .filter((c) => c?.active !== false)
    .filter(isContributingConditionIncomplete).length;
  return [
    { label: "Primary diagnosis coded", met: Boolean(primary.icd10 || primary.description) },
    { label: "HOPE Principal Category (I0010)", met: Boolean(primary.hopeDiagnosisCategory) },
    { label: "Terminal prognosis documented", met: Boolean(diagnosesData?.terminalPrognosis) },
    { label: "Secondary diagnoses reviewed", met: secondaryCount > 0 },
    { label: "Comorbidities reviewed", met: comorbidityCount > 0 },
    { label: "LCD supporting evidence documented", met: Boolean((diagnosesData?.lcdEligibilityNarrative || "").trim()) },
    // Contributing Conditions (Disease & LCD Workflow Spec, Phase 1): zero
    // documented conditions is a VALID state (not every patient has one),
    // so this item is only unmet when an active entry is missing a
    // diagnosis, a contribution status, or (when the status requires it) a
    // clinical rationale -- never merely because the list is empty.
    { label: "Contributing conditions reviewed", met: contributingIncomplete === 0 },
  ];
}

// ─── Contributing Conditions (Disease & LCD Workflow Spec, Phase 1 /
// Option A) ──────────────────────────────────────────────────────────────
// Manually-documented conditions that are distinct from the Primary
// Diagnosis, Secondary Diagnoses, and HOPE Comorbidities checklist, each
// carrying an explicit clinician judgment about whether it contributes to
// terminal prognosis or clinical burden. Persisted at
// `diagnoses.contributingConditions` (array) -- the established
// `formData.diagnoses.*` JSONB namespace, no new table/column. This is a
// compliance *documentation* aid only: SNS EMR makes no PASS/FAIL
// eligibility determination from these values (see LCD Eligibility card
// for the only place eligibility is ever computed).
export const CONTRIBUTING_CONDITION_STATUS_OPTIONS = [
  { value: "CONTRIBUTES_TO_TERMINAL_PROGNOSIS", label: "Contributes to Terminal Prognosis", shortLabel: "Terminal Prognosis" },
  { value: "CONTRIBUTES_TO_CLINICAL_BURDEN", label: "Contributes to Clinical Burden", shortLabel: "Clinical Burden" },
  { value: "DOES_NOT_MATERIALLY_CONTRIBUTE", label: "Does Not Materially Contribute", shortLabel: "Not Material" },
  { value: "UNABLE_TO_DETERMINE", label: "Unable to Determine", shortLabel: "Undetermined" },
];

export const CONTRIBUTING_CONDITION_STATUSES_REQUIRING_RATIONALE = new Set([
  "CONTRIBUTES_TO_TERMINAL_PROGNOSIS",
  "CONTRIBUTES_TO_CLINICAL_BURDEN",
]);

// Controlled, manual-entry-only source list for Phase 1 -- no automated
// document identification/extraction exists yet (auto-identifying the
// source document, author, and date from an uploaded/referenced record is
// Phase 2+, not authorized here). Every value below still describes a
// human reviewing a document/finding and selecting its origin themselves.
//
// H&P vs. Hospital Record: "H&P" is the clinician's own History & Physical
// exam/admission note for *this* episode of care; "Hospital Record" is an
// external institutional record (e.g., discharge summary, ED record, prior
// hospitalization chart) the clinician is reviewing, not authoring.
export const CONTRIBUTING_CONDITION_SOURCE_OPTIONS = [
  { value: "CLINICIAN_ENTERED", label: "Clinician Entered" },
  { value: "HNP", label: "H&P" },
  { value: "HOSPITAL_RECORD", label: "Hospital Record" },
  { value: "REFERRAL_DOCUMENTATION", label: "Referral Documentation" },
  { value: "PROVIDER_SPECIALIST_NOTE", label: "Provider / Specialist Note" },
  { value: "LABORATORY_RESULT", label: "Laboratory Result" },
  { value: "DIAGNOSTIC_IMAGING", label: "Diagnostic Imaging" },
  { value: "RNICA_FINDING", label: "RNICA Finding" },
  { value: "OTHER", label: "Other" },
];

function normalizeIcd10ForCompare(code) {
  return String(code || "").trim().toUpperCase();
}

/** True when a (still-active) contributing condition is missing a
 * required piece of documentation: no diagnosis selected, no
 * contribution-status chosen, or (for the two statuses that require it)
 * no clinical rationale. Used by the Final Verification checklist and by
 * the card's own per-row "incomplete" notice -- never blocks saving, only
 * flags for review. */
export function isContributingConditionIncomplete(condition) {
  if (!condition) return false;
  if (!condition.icdCode && !condition.icdDescription) return true;
  if (!condition.contributionStatus) return true;
  if (
    CONTRIBUTING_CONDITION_STATUSES_REQUIRING_RATIONALE.has(condition.contributionStatus) &&
    !String(condition.clinicalRationale || "").trim()
  ) {
    return true;
  }
  return false;
}

/** Chip-summary labels for currently-active contributing conditions
 * ("ICD-10 Description — Status"), mirroring summarizeSecondaryDiagnoses'
 * shape so both lists render with the same visual language. */
export function summarizeContributingConditions(diagnosesData) {
  return (diagnosesData?.contributingConditions || [])
    .filter((c) => c?.active !== false && (c?.icdCode || c?.icdDescription))
    .map((c) => {
      const statusLabel = CONTRIBUTING_CONDITION_STATUS_OPTIONS.find((o) => o.value === c.contributionStatus)?.shortLabel;
      const label = `${c.icdCode ? formatIcd10Code(c.icdCode) : ""} ${c.icdDescription || ""}`.trim();
      return statusLabel ? `${label} — ${statusLabel}` : label;
    });
}

/** Exact-ICD-10-match duplicate within the (active) contributing-conditions
 * list, excluding the row currently being edited. An exact duplicate is a
 * BLOCKING condition -- the caller must refuse to apply the selection and
 * point the clinician at the existing entry instead of creating a second
 * row for the same code. */
export function findExactDuplicateContributingCondition(conditions, icdCode, excludeId) {
  const target = normalizeIcd10ForCompare(icdCode);
  if (!target) return null;
  return (
    (conditions || []).find(
      (c) => c?.active !== false && c.id !== excludeId && normalizeIcd10ForCompare(c.icdCode) === target,
    ) || null
  );
}

/** Other active contributing conditions that fall into the same HOPE
 * comorbidity category (e.g. two different renal-disease codes) --
 * nonblocking, WARNING-ONLY per owner directive ("warn, never silently
 * merge"). A probable duplicate is not necessarily wrong (two distinct,
 * clinically real conditions can share a category); it only prompts the
 * clinician to confirm these are not the same condition entered twice. */
export function findProbableDuplicateContributingConditions(conditions, icdCode, excludeId) {
  const category = categorizeIcd10(icdCode);
  if (!category) return [];
  return (conditions || []).filter(
    (c) => c?.active !== false && c.id !== excludeId && categorizeIcd10(c.icdCode)?.key === category.key,
  );
}

/** Nonblocking cross-reference notices against Secondary Diagnoses and the
 * HOPE Comorbidities checklist. These are informational only -- a
 * Contributing Condition is NEVER auto-added to Secondary Diagnoses and a
 * HOPE checkbox is NEVER auto-checked from here, in either direction. */
export function findContributingConditionCrossReferences(diagnosesData, icdCode) {
  const target = normalizeIcd10ForCompare(icdCode);
  if (!target) return { inSecondaryDiagnoses: false, hopeCategory: null, hopeCategoryChecked: false };
  const inSecondaryDiagnoses = (diagnosesData?.secondaryDiagnoses || []).some(
    (dx) => normalizeIcd10ForCompare(dx?.icd10) === target,
  );
  const hopeCategory = categorizeIcd10(icdCode);
  const hopeCategoryChecked = hopeCategory ? Boolean(diagnosesData?.hopeComorbidities?.[hopeCategory.key]) : false;
  return { inSecondaryDiagnoses, hopeCategory, hopeCategoryChecked };
}
