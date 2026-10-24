// Shared Safety & Clinical Risk derivation logic (data-only, no JSX, no
// styling). Mirrors diagnosisLogic.js/painLogic.js's precedent: pure
// read-only functions that turn already-charted Safety fields into
// compact summaries for the new guided-assessment overview, so the
// overview and the legacy field-level cards (still the only place any
// of this data is captured/edited, reused unchanged inside the new Edit
// Sheets via `renderSafetyStepCards`) always agree on what counts as
// "complete"/"documented".
//
// PRODUCT OWNER DIRECTIVE (2026-12) "Safety & Clinical Risk -- Four
// Guided Assessments Only" -- the approved main-page overview is exactly
// four cards: Environmental Safety, Morse Fall Scale (Fall Risk),
// Oxygen Safety, Disaster Triage. Patient Safety / Caregiver Safety /
// Safety Notes / DME / Supplies are removed as standalone main-page
// cards per that directive's explicit per-item ownership decisions (see
// RNICA.jsx SECTION_CONFIGS.safety / SAFETY_COVERAGE_ITEMS comments for
// the full ownership table) -- their underlying fields are left in the
// data model untouched (never deleted) for historical round-tripping,
// they are simply no longer rendered as separate top-level cards here.
//
// Like diagnosisLogic.js/painLogic.js, this file takes NO import from
// RNICA.jsx (RNICA.jsx's own module graph ends up importing the
// Overview that imports this file, so importing back from RNICA.jsx
// would be circular). The Morse Fall Scale point table/thresholds below
// are reproduced VERBATIM from RNICA.jsx's `MORSE_FALL_SCALE_FACTOR_
// POINTS`/`computeMorseFallScore` (same published Morse, 1989 instrument
// values -- "do not invent alternate point values") -- RNICA.jsx's own
// copy remains the single source FallRiskCard and validateRNICA actually
// read/write; keep this copy in sync if that table ever changes.
const MORSE_FALL_SCALE_FACTOR_POINTS = {
  historyOfFalling: { "No": 0, "Yes": 25 },
  secondaryDiagnosis: { "No": 0, "Yes": 15 },
  ambulatoryAid: { "None/Bed Rest/Nurse Assist": 0, "Crutches/Cane/Walker": 15, "Furniture": 30 },
  ivHeparinLock: { "No": 0, "Yes": 20 },
  gaitTransferring: { "Normal/Bedrest/Immobile": 0, "Weak": 10, "Impaired": 20 },
  mentalStatus: { "Oriented to Own Ability": 0, "Overestimates/Forgets Limitations": 15 },
};

export const MORSE_FALL_SCALE_FACTORS = [
  { key: "historyOfFalling", dataKey: "fallRiskMorseHistoryOfFalling", label: "History of Falling", options: ["No", "Yes"] },
  { key: "secondaryDiagnosis", dataKey: "fallRiskMorseSecondaryDiagnosis", label: "Secondary Diagnosis", options: ["No", "Yes"] },
  { key: "ambulatoryAid", dataKey: "fallRiskMorseAmbulatoryAid", label: "Ambulatory Aid", options: ["None/Bed Rest/Nurse Assist", "Crutches/Cane/Walker", "Furniture"] },
  { key: "ivHeparinLock", dataKey: "fallRiskMorseIvHeparinLock", label: "IV / Heparin Lock", options: ["No", "Yes"] },
  { key: "gaitTransferring", dataKey: "fallRiskMorseGaitTransferring", label: "Gait / Transferring", options: ["Normal/Bedrest/Immobile", "Weak", "Impaired"] },
  { key: "mentalStatus", dataKey: "fallRiskMorseMentalStatus", label: "Mental Status", options: ["Oriented to Own Ability", "Overestimates/Forgets Limitations"] },
];

/** Verbatim from RNICA.jsx's `computeMorseFallScore` -- never scores an
 * unanswered factor as zero; an unanswered factor makes the whole
 * assessment incomplete. */
export function computeMorseFallScore(data) {
  let total = 0;
  let allAnswered = true;
  const breakdown = MORSE_FALL_SCALE_FACTORS.map((f) => {
    const value = data?.[f.dataKey] || "";
    if (!value) { allAnswered = false; return { ...f, value: "", points: null }; }
    const points = MORSE_FALL_SCALE_FACTOR_POINTS[f.key][value];
    total += points;
    return { ...f, value, points };
  });
  if (!allAnswered) {
    return { complete: false, total: null, classification: "", breakdown };
  }
  let classification = "Low Risk";
  if (total >= 45) classification = "High Risk";
  else if (total >= 25) classification = "Moderate Risk";
  return { complete: true, total, classification, breakdown };
}

export function isFallRiskMorseComplete(data) {
  return computeMorseFallScore(data || {}).complete;
}

/** Verbatim from RNICA.jsx's `computeFallRiskTrend` -- scoped only to
 * this chart's own `fallRiskHistory` array. */
export function computeFallRiskTrend(history) {
  const list = Array.isArray(history) ? history : [];
  if (list.length === 0) return { current: null, previous: null, change: null, trend: "" };
  const current = list[list.length - 1];
  const previous = list.length > 1 ? list[list.length - 2] : null;
  if (!previous) return { current, previous: null, change: null, trend: "" };
  const change = current.totalScore - previous.totalScore;
  let trend = "Stable";
  if (change > 0) trend = "Worsening";
  else if (change < 0) trend = "Improving";
  return { current, previous, change, trend };
}

/** Fall Risk Assessment summary -- score, classification, major
 * contributors (factors that scored > 0 points), trend. */
export function summarizeFallRisk(safetyData = {}) {
  const score = computeMorseFallScore(safetyData);
  const trend = computeFallRiskTrend(safetyData.fallRiskHistory);
  const majorContributors = score.complete
    ? score.breakdown.filter((b) => b.points > 0).map((b) => b.label)
    : [];
  return {
    complete: score.complete,
    total: score.total,
    classification: score.classification,
    majorContributors,
    trend,
    transferSafetyLevel: safetyData.transferSafetyLevel || "",
    clarification: safetyData.fallRiskClarificationNote || "",
  };
}

const ENVIRONMENTAL_HOME_NO_CONCERN = "No Environmental Concerns Identified";
const STAFF_VISIT_SAFETY_NO_CONCERN = "No Staff Safety Concerns Identified";
const OXYGEN_SAFETY_NO_CONCERN = "No Concern";

/** Is the current Site of Service a facility (vs. a private residence)?
 * Verbatim from EnvironmentalSafetyCard's own `isFacility` derivation. */
export function isFacilitySiteOfService(fullFormData) {
  const siteOfService = fullFormData?.demographics?.livingSituation?.siteOfService || "";
  return siteOfService !== "" && siteOfService !== "01";
}

/** Environmental Safety Assessment summary -- setting, completion,
 * patient (Home/Facility) hazards, staff visit-safety hazards. */
export function summarizeEnvironmentalSafety(safetyData = {}, fullFormData = {}) {
  const isFacility = isFacilitySiteOfService(fullFormData);
  const setting = isFacility ? "Facility" : "Home";
  const homeConcerns = (safetyData.environmentalHomeConcerns || []).filter((c) => c !== ENVIRONMENTAL_HOME_NO_CONCERN);
  const noHomeConcerns = (safetyData.environmentalHomeConcerns || []).includes(ENVIRONMENTAL_HOME_NO_CONCERN);
  const facilityStatus = safetyData.environmentalFacilityStatus || "";
  const facilityConcerns = safetyData.environmentalFacilityConcerns || [];
  const patientHazards = isFacility
    ? (facilityStatus === "Observed Concern" ? facilityConcerns : [])
    : homeConcerns;
  const staffHazards = (safetyData.environmentalStaffVisitSafety || []).filter((c) => c !== STAFF_VISIT_SAFETY_NO_CONCERN);
  const noStaffConcerns = (safetyData.environmentalStaffVisitSafety || []).includes(STAFF_VISIT_SAFETY_NO_CONCERN);

  const patientComplete = isFacility
    ? Boolean(facilityStatus)
    : (homeConcerns.length > 0 || noHomeConcerns);
  const staffComplete = staffHazards.length > 0 || noStaffConcerns;
  const complete = patientComplete && staffComplete;

  const patientSummary = isFacility
    ? (facilityStatus === "Observed Concern" ? (facilityConcerns.join(", ") || "Observed Concern") : (facilityStatus || ""))
    : (homeConcerns.length > 0 ? homeConcerns.join(", ") : (noHomeConcerns ? ENVIRONMENTAL_HOME_NO_CONCERN : ""));
  const staffSummary = staffHazards.length > 0 ? staffHazards.join(", ") : (noStaffConcerns ? STAFF_VISIT_SAFETY_NO_CONCERN : "");

  return {
    setting,
    complete,
    patientHazards,
    staffHazards,
    patientSummary,
    staffSummary,
    clarification: safetyData.environmentalClarificationNote || "",
  };
}

/** Oxygen Safety Assessment summary -- Not Applicable / No Concern /
 * Concern, driven by the SAME authoritative in-use source
 * (`respiratory.oxygenTherapy.inUse`, legacy `safety.oxygenInUse`
 * fallback) OxygenSafetyCard already reads. */
export function summarizeOxygenSafety(safetyData = {}, fullFormData = {}) {
  const oxygenInUse = fullFormData?.respiratory?.oxygenTherapy?.inUse ?? safetyData.oxygenInUse;
  if (!oxygenInUse) {
    return { applicable: false, complete: true, status: "Not Applicable", concerns: [], clarification: "" };
  }
  const concerns = (safetyData.oxygenSafetyConcerns || []);
  const hasNoConcern = concerns.includes(OXYGEN_SAFETY_NO_CONCERN);
  const activeConcerns = concerns.filter((c) => c !== OXYGEN_SAFETY_NO_CONCERN);
  const complete = concerns.length > 0;
  const status = !complete ? "" : (hasNoConcern ? "No Concern" : "Concern Identified");
  return {
    applicable: true,
    complete,
    status,
    concerns: activeConcerns,
    clarification: safetyData.oxygenSafetyClarificationNote || "",
  };
}

const DISASTER_TRIAGE_CONDITIONS_PATH_BY_LEVEL = {
  "Level 1 — Hospice must assist; no assistance available": "disasterLevelOneConditions",
  "Level 2 — Hospice must contact to assure adequate assistance; limited assistance available": "disasterLevelTwoConditions",
  "Level 3 — No need for hospice to assist; has adequate assistance available": "disasterLevelThreeConditions",
};

/** Disaster Triage Assessment summary -- level, short label, dependency
 * factors (the level's selected conditions). */
export function summarizeDisasterTriage(safetyData = {}) {
  const level = safetyData.disasterLevel || "";
  const complete = Boolean(level);
  const shortLabel = level.startsWith("Level 1") ? "Level 1" : level.startsWith("Level 2") ? "Level 2" : level.startsWith("Level 3") ? "Level 3" : "";
  const conditionsPath = DISASTER_TRIAGE_CONDITIONS_PATH_BY_LEVEL[level];
  const conditions = conditionsPath ? (safetyData[conditionsPath] || []) : [];
  return {
    complete,
    level,
    shortLabel,
    conditions,
    clarification: safetyData.disasterTriageClarificationNote || "",
  };
}
