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

// PRODUCT OWNER DECISION "Importing Prior Safety Assessments" (approved)
// -- "REJECT Bedbound = Score 0 logic. BEDBOUND PATIENTS MAY STILL HAVE
// HIGH TRANSFER AND INJURY RISK." The Morse score/point table above is
// UNCHANGED (`gaitTransferring: "Normal/Bedrest/Immobile": 0` is the
// literal, correct, published 1989 Morse value and "KEEP MORSE SCORE FOR
// STANDARDIZED TRENDING" is explicit) -- Morse answers "how likely is a
// fall?" This is a SEPARATE field answering "how dangerous would a fall
// or transfer event be for this patient?" and is never merged into or
// substituted for the Morse score/classification.
export const HOSPICE_CLINICAL_FALL_SAFETY_OPTIONS = [
  "Standard Precautions",
  "Enhanced Precautions",
  "High-Risk Transfer Precautions",
  "Bedbound Safety Precautions",
];

/** Fall Risk Assessment summary -- score, classification, major
 * contributors (factors that scored > 0 points), trend, and the
 * separate Hospice Clinical Fall Safety precaution level. */
export function summarizeFallRisk(safetyData = {}) {
  const score = computeMorseFallScore(safetyData);
  const trend = computeFallRiskTrend(safetyData.fallRiskHistory);
  const majorContributors = score.complete
    ? score.breakdown.filter((b) => b.points > 0).map((b) => b.label)
    : [];
  const precautionLevel = safetyData.hospiceClinicalFallSafetyLevel || "";
  return {
    complete: score.complete && Boolean(precautionLevel),
    total: score.total,
    classification: score.classification,
    majorContributors,
    trend,
    transferSafetyLevel: safetyData.transferSafetyLevel || "",
    clarification: safetyData.fallRiskClarificationNote || "",
    precautionLevel,
  };
}

const ENVIRONMENTAL_HOME_NO_CONCERN = "No Environmental Concerns Identified";
const STAFF_VISIT_SAFETY_NO_CONCERN = "No Staff Safety Concerns Identified";
const OXYGEN_SAFETY_NO_CONCERN = "No Concern";

// FINAL PRODUCT OWNER DIRECTIVE section 11 -- Staff Visit Safety is a
// 2-state status gate plus 5 full hazard taxonomies, replacing the flat
// `STAFF_VISIT_SAFETY_NO_CONCERN`/6-option list above (preserved,
// legacy-chipped, never read again).
export const STAFF_SAFETY_STATUS_NO_CONCERN = "No Staff Safety Concern Identified";
export const STAFF_SAFETY_STATUS_CONCERN = "Staff Safety Concern Identified";
export const STAFF_SAFETY_STATUS_UNABLE = "Unable to Assess";
export const STAFF_SAFETY_STATUS_OPTIONS = [STAFF_SAFETY_STATUS_NO_CONCERN, STAFF_SAFETY_STATUS_CONCERN, STAFF_SAFETY_STATUS_UNABLE];
export const STAFF_SAFETY_HAZARD_CATEGORIES = [
  {
    label: "Violence or Threat",
    options: [
      "Aggressive or threatening patient", "Aggressive or threatening family member",
      "Aggressive or threatening caregiver", "Aggressive or threatening visitor",
      "Verbal threat or intimidation", "Recent violent behavior",
      "Domestic-violence concern", "Criminal-activity concern",
      "Other violence or threat concern",
    ],
  },
  {
    label: "Substance-Related Risk",
    options: [
      "Active illicit-drug use in the residence", "Intoxicated person present",
      "Unsafe alcohol-related behavior", "Drug-manufacturing or distribution concern",
      "Drug paraphernalia or unsafe substance exposure", "Heavy smoking or vaping exposure",
      "Other substance-related risk",
    ],
  },
  {
    label: "Weapons and Security",
    options: [
      "Firearm concern", "Other weapon concern", "Unsecured weapon",
      "Unsafe neighborhood or building access", "No secure entry or exit",
      "Staff could be prevented from leaving", "Security assistance needed",
      "Other weapon or security concern",
    ],
  },
  {
    label: "Animal Risk",
    options: [
      "Aggressive or uncontrolled dog", "Aggressive or uncontrolled animal",
      "Animal blocks entry or care area", "Animal cannot be secured",
      "Animal-bite history reported", "Other animal concern",
    ],
  },
  {
    label: "Physical or Exposure Risk",
    options: [
      "Structural hazard", "Electrical hazard", "Severe clutter preventing safe care delivery",
      "Unsafe stairs or access path", "Poor lighting affecting care delivery",
      "Unsanitary condition", "Pest or infestation exposure", "Extreme temperature",
      "Biohazard or sharps exposure", "Required protective equipment unavailable",
      "Other physical or exposure concern",
    ],
  },
];
export const STAFF_SAFETY_HAZARD_OPTIONS = STAFF_SAFETY_HAZARD_CATEGORIES.flatMap((c) => c.options);

// PRODUCT OWNER DIRECTIVE (2026-12-01) "Make Safety & Clinical Risk One
// Assessment" section 7 -- Environmental Safety must capture, in
// addition to the hazard lists above, who the hazard targets (Risk
// Target), what was done about it (Actions Taken), the staff visit
// disposition when a staff-safety hazard applies, and whether follow-up
// is required -- not a generic "Observed Concern" with no named hazard
// or outcome.
export const ENVIRONMENTAL_RISK_TARGET_OPTIONS = ["Patient", "Staff", "Patient and Staff"];
export const ENVIRONMENTAL_ACTIONS_TAKEN_OPTIONS = [
  "Education Provided", "Equipment/Repair Requested", "Caregiver Notified",
  "Facility Notified", "Referral Made", "No Action Needed", "Other",
];
export const ENVIRONMENTAL_STAFF_DISPOSITION_OPTIONS = [
  "Visit Completed as Scheduled", "Visit Modified for Safety",
  "Visit Terminated Early", "Law Enforcement Notified",
];

/** PRODUCT OWNER DIRECTIVE "Safety & Clinical Risk Current State Review
 * and Next Actions" (2026-10-24) Issue 1 -- shared Place-of-Service
 * resolver. `demographics.livingSituation.siteOfService` is the ONE
 * authoritative Place-of-Service field in the RNICA form: it is read by
 * Safety (this file), written by the "Living Situation" card in
 * Patient Story/Demographics (`renderDemographics`), written once by the
 * Face-Sheet-derived care-setting auto-default effect, and read by the
 * official HOPE report generator (`hopeReportMapper.js`'s
 * `demographics.livingSituation`). The HOPE Administrative Review screen
 * previously read/wrote a disconnected top-level `formData.livingSituation`
 * that nothing else consulted -- that bug is fixed by having HOPE
 * Administrative Review's data projection and write-back both go through
 * this same resolver / the same canonical path, so a Face Sheet /
 * Patient Story change now flows through to Safety, HOPE, and every other
 * residence-sensitive section without any direct database edit. */
export function getSiteOfServiceCode(fullFormData) {
  return fullFormData?.demographics?.livingSituation?.siteOfService || "";
}

/** Is the current Site of Service a facility (vs. a private residence)?
 * Verbatim from EnvironmentalSafetyCard's own `isFacility` derivation. */
export function isFacilitySiteOfService(fullFormData) {
  const siteOfService = getSiteOfServiceCode(fullFormData);
  return siteOfService !== "" && siteOfService !== "01";
}

// PRODUCT OWNER DIRECTIVE "Checkpoint 3: Environmental Safety Summary
// Accuracy" (2026-10-24) -- short, clinically-readable Site of Service
// labels used ONLY for the main-page Environmental Safety summary line
// (e.g. "Private Home", "Assisted Living"). Deliberately a separate,
// narrower map from the official long-form CMS A0215 labels
// (`SITE_OF_SERVICE_LABELS` in HopeAdministrativeReview.jsx /
// hopeReportMapper.js, which remain the source of truth for the actual
// HOPE report and are not duplicated or altered here) -- this map exists
// purely so the summary reads "Private Home" / "Assisted Living" instead
// of the full CMS phrasing ("Patient's Home/Residence" / "Assisted
// Living Facility") or a generic "Home"/"Facility".
const SETTING_SHORT_LABEL_BY_CODE = {
  "01": "Private Home",
  "02": "Assisted Living",
  "03": "Nursing/LTC Facility",
  "04": "Skilled Nursing Facility",
  "05": "Inpatient Hospital",
  "06": "Inpatient Hospice Facility",
  "07": "Long Term Care Hospital",
  "08": "Inpatient Psychiatric Facility",
  "09": "Hospice Home Care Facility",
  "99": "Facility (Not Listed)",
};

// PRODUCT OWNER DIRECTIVE "Checkpoint 3" -- "UNABLE TO ASSESS" requires a
// named reason; a blank Unable-To-Assess status is never allowed. Follows
// the SAME established "segmented reason + Other free-text" pattern
// already used by every other Body System's own Unable-to-Assess field
// (e.g. `respiratoryUnableToAssessReason`/`respiratoryUnableToAssessOther`
// in RNICA.jsx) -- no new pattern invented.
export const ENVIRONMENTAL_UNABLE_TO_ASSESS_REASON_OPTIONS = [
  "Environment Inaccessible",
  "Immediate Staff-Safety Concern",
  "Other",
];

/** Environmental Safety Assessment summary -- setting, completion,
 * patient (Home/Facility) hazards, staff visit-safety hazards. */
export function summarizeEnvironmentalSafety(safetyData = {}, fullFormData = {}) {
  const isFacility = isFacilitySiteOfService(fullFormData);
  const setting = isFacility ? "Facility" : "Home";
  const settingLabel = SETTING_SHORT_LABEL_BY_CODE[getSiteOfServiceCode(fullFormData)] || (isFacility ? "Facility" : "Private Home");
  const homeConcerns = (safetyData.environmentalHomeConcerns || []).filter((c) => c !== ENVIRONMENTAL_HOME_NO_CONCERN);
  const noHomeConcerns = (safetyData.environmentalHomeConcerns || []).includes(ENVIRONMENTAL_HOME_NO_CONCERN);
  const facilityStatus = safetyData.environmentalFacilityStatus || "";
  const facilityConcerns = safetyData.environmentalFacilityConcerns || [];
  const patientHazards = isFacility
    ? (facilityStatus === "Observed Concern" ? facilityConcerns : [])
    : homeConcerns;
  // FINAL PRODUCT OWNER DIRECTIVE section 11 -- Staff Visit Safety is now
  // a 2-state status gate (`environmentalStaffSafetyStatus`) plus 5
  // full hazard taxonomies (`environmentalStaffSafetyHazards`), replacing
  // the retired flat `environmentalStaffVisitSafety` list (preserved,
  // legacy-chipped, never read here again).
  const staffSafetyStatus = STAFF_SAFETY_STATUS_OPTIONS.includes(safetyData.environmentalStaffSafetyStatus) ? safetyData.environmentalStaffSafetyStatus : "";
  const staffHazards = staffSafetyStatus === STAFF_SAFETY_STATUS_CONCERN ? (safetyData.environmentalStaffSafetyHazards || []) : [];
  const noStaffConcerns = staffSafetyStatus === STAFF_SAFETY_STATUS_NO_CONCERN;
  const staffUnableToAssess = staffSafetyStatus === STAFF_SAFETY_STATUS_UNABLE;

  // Checkpoint 3 "UNABLE TO ASSESS" -- a named reason is required
  // whenever Staff Visit-Safety Status is "Unable to Assess" (the only
  // Unable-to-Assess gate Environmental Safety currently has); a blank
  // reason is never permitted to count as documented.
  const unableToAssessReason = staffUnableToAssess
    ? (safetyData.environmentalUnableToAssessReason === "Other"
      ? (safetyData.environmentalUnableToAssessOther || "")
      : (safetyData.environmentalUnableToAssessReason || ""))
    : "";

  const patientComplete = isFacility
    ? Boolean(facilityStatus)
    : (homeConcerns.length > 0 || noHomeConcerns);
  const staffComplete = Boolean(staffSafetyStatus)
    && (staffSafetyStatus !== STAFF_SAFETY_STATUS_CONCERN || staffHazards.length > 0)
    && (!staffUnableToAssess || Boolean(unableToAssessReason));

  // Section 7 additions -- only required when an actual hazard (patient
  // or staff) was identified; a clean "No Concerns" visit never requires
  // a risk target, actions taken, disposition, or follow-up decision.
  const hasAnyHazard = patientHazards.length > 0 || staffHazards.length > 0;
  const riskTarget = safetyData.environmentalRiskTarget || "";
  const actionsTaken = safetyData.environmentalActionsTaken || [];
  const staffDisposition = safetyData.environmentalStaffDisposition || "";
  const followUpRequired = safetyData.environmentalFollowUpRequired || "";
  const followUpNote = safetyData.environmentalFollowUpNote || "";

  const riskTargetComplete = !hasAnyHazard || Boolean(riskTarget);
  const actionsTakenComplete = !hasAnyHazard || actionsTaken.length > 0;
  const dispositionComplete = staffHazards.length === 0 || Boolean(staffDisposition);
  const followUpComplete = !hasAnyHazard || Boolean(followUpRequired);

  const complete = patientComplete && staffComplete && riskTargetComplete && actionsTakenComplete && dispositionComplete && followUpComplete;

  const patientSummary = isFacility
    ? (facilityStatus === "Observed Concern" ? facilityConcerns.join(", ") : (facilityStatus || ""))
    : (homeConcerns.length > 0 ? homeConcerns.join(", ") : (noHomeConcerns ? ENVIRONMENTAL_HOME_NO_CONCERN : ""));
  const staffSummary = staffHazards.length > 0 ? staffHazards.join(", ") : (noStaffConcerns ? STAFF_SAFETY_STATUS_NO_CONCERN : (staffUnableToAssess ? STAFF_SAFETY_STATUS_UNABLE : ""));

  // Checkpoint 3 "SETTING CHANGE BEHAVIOR" -- detects a Place-of-Service
  // change that has invalidated the OTHER branch's previously-recorded
  // answers (e.g. Facility -> Home: old `environmentalFacilityStatus`
  // data exists but the new Home branch has not yet been answered). No
  // new field is introduced: this is inferred purely from which
  // branch's data is present versus which branch is currently active,
  // the same "historical values never leak into the current summary"
  // guarantee already enforced by `patientHazards`/`patientSummary` only
  // ever reading the CURRENTLY active branch above.
  const otherSettingHasData = isFacility
    ? (homeConcerns.length > 0 || noHomeConcerns)
    : Boolean(facilityStatus);
  const settingChanged = otherSettingHasData && !patientComplete;

  // Checkpoint 3 "REQUIRED SUMMARY RULES" -- the main-page card summary
  // must always name the actual finding, never a meaningless placeholder
  // like bare "Observed Concern" or bare "Facility Managed". Built
  // SEPARATELY from `patientSummary`/`staffSummary` above (which stay
  // unchanged for their existing consumers -- the Review & Complete step
  // and the prior-assessment import banner, both of which already pair
  // the raw value with their own "Setting: X" label for context) so nothing
  // else that already reads `patientSummary`/`staffSummary` is altered.
  let cardSummary = "";
  if (settingChanged) {
    cardSummary = "Needs Review — Place of Service Changed";
  } else if (staffUnableToAssess) {
    cardSummary = unableToAssessReason ? `Unable To Assess — ${unableToAssessReason}` : "Unable To Assess";
  } else if (isFacility) {
    if (facilityStatus === "Facility Managed") {
      cardSummary = `${settingLabel} — Facility Managed, No Observed Concern`;
    } else if (facilityStatus === "Observed Concern" && facilityConcerns.length > 0) {
      cardSummary = `${settingLabel} — ${facilityConcerns.join("; ")}`;
    }
  } else if (noHomeConcerns) {
    cardSummary = `${settingLabel} — No Environmental Concern Identified`;
  } else if (homeConcerns.length > 0) {
    cardSummary = `${settingLabel} — ${homeConcerns.join("; ")}`;
  }

  let staffCardSummary = "";
  if (staffHazards.length > 0) {
    staffCardSummary = staffHazards.join("; ");
  } else if (noStaffConcerns) {
    staffCardSummary = "No Concern Identified";
  } else if (staffUnableToAssess) {
    staffCardSummary = unableToAssessReason ? `Unable to Assess — ${unableToAssessReason}` : "Unable to Assess";
  }

  return {
    setting,
    settingLabel,
    settingChanged,
    complete,
    patientHazards,
    staffHazards,
    patientSummary,
    staffSummary,
    cardSummary,
    staffCardSummary,
    hasAnyHazard,
    // PRODUCT OWNER DEFECT (2026-10-24) "Current Safety Completion Logic
    // Is Invalid" -- Risk Target / Actions Taken / Follow-Up are only
    // required when a hazard exists; Staff Disposition is only required
    // when a STAFF hazard specifically exists (narrower than
    // `hasAnyHazard`, matching `dispositionComplete` above). Exposed
    // explicitly so the Review screen can render "N/A" instead of
    // "Not Yet Documented" for correctly-skipped fields.
    staffDispositionRequired: staffHazards.length > 0,
    riskTarget,
    actionsTaken,
    staffDisposition,
    followUpRequired,
    followUpNote,
    clarification: safetyData.environmentalClarificationNote || "",
    staffSafetyStatus,
    unableToAssessReason,
  };
}

/** Oxygen Safety Assessment summary -- Not Applicable / No Concern /
 * Concern, driven by the SAME authoritative in-use source
 * (`respiratory.oxygenTherapy.inUse`, legacy `safety.oxygenInUse`
 * fallback) OxygenSafetyCard already reads.
 *
 * PRODUCT OWNER DIRECTIVE (2026-12-01) "Make Safety & Clinical Risk One
 * Assessment" section 4 & 9 -- the Oxygen step is never eliminated from
 * the wizard sequence, even when Not Applicable: the RN must explicitly
 * confirm "No current oxygen use documented" before it counts as
 * complete (`oxygenSafetyConfirmedNotApplicable`). When oxygen IS
 * applicable and an actual concern (not just "No Concern") is
 * identified, the RN must also capture the actions taken and whether
 * follow-up is required -- "do not stop at Concern Identified." */
export function summarizeOxygenSafety(safetyData = {}, fullFormData = {}) {
  const oxygenInUse = fullFormData?.respiratory?.oxygenTherapy?.inUse ?? safetyData.oxygenInUse;
  const confirmedNotApplicable = Boolean(safetyData.oxygenSafetyConfirmedNotApplicable);
  if (!oxygenInUse) {
    return {
      applicable: false,
      complete: confirmedNotApplicable,
      confirmedNotApplicable,
      status: "Not Applicable",
      concerns: [],
      hasActiveConcern: false,
      actionsTaken: [],
      followUpRequired: "",
      followUpNote: "",
      clarification: "",
    };
  }
  const concerns = (safetyData.oxygenSafetyConcerns || []);
  const hasNoConcern = concerns.includes(OXYGEN_SAFETY_NO_CONCERN);
  const activeConcerns = concerns.filter((c) => c !== OXYGEN_SAFETY_NO_CONCERN);
  const hasConcernDocumented = concerns.length > 0;
  const actionsTaken = safetyData.oxygenSafetyActionsTaken || [];
  const followUpRequired = safetyData.oxygenSafetyFollowUpRequired || "";
  const followUpNote = safetyData.oxygenSafetyFollowUpNote || "";
  const hasActiveConcern = activeConcerns.length > 0;
  const actionsComplete = !hasActiveConcern || actionsTaken.length > 0;
  const followUpComplete = !hasActiveConcern || Boolean(followUpRequired);
  const complete = hasConcernDocumented && actionsComplete && followUpComplete;
  const status = !hasConcernDocumented ? "" : (hasNoConcern ? "No Concern" : "Concern Identified");
  return {
    applicable: true,
    complete,
    confirmedNotApplicable: false,
    status,
    concerns: activeConcerns,
    hasActiveConcern,
    actionsTaken,
    followUpRequired,
    followUpNote,
    clarification: safetyData.oxygenSafetyClarificationNote || "",
  };
}

const DISASTER_TRIAGE_CONDITIONS_PATH_BY_LEVEL = {
  "Level 1 — Hospice must assist; no assistance available": "disasterLevelOneConditions",
  "Level 2 — Hospice must contact to assure adequate assistance; limited assistance available": "disasterLevelTwoConditions",
  "Level 3 — No need for hospice to assist; has adequate assistance available": "disasterLevelThreeConditions",
};

// PRODUCT OWNER DIRECTIVE (2026-12-01) "Make Safety & Clinical Risk One
// Assessment" section 10 -- Disaster Triage must answer "what priority
// level applies" (Level, unchanged). A validated algorithm for
// computing a "suggested" level distinct from the RN's own selection
// does not exist in this repository (no source for scoring
// weights/thresholds was provided, the same gap the owner already
// rejected once for the custom HospiceMD fall-risk model) -- consistent
// with "do not invent alternate point values," no suggested-level
// computation is fabricated here. The RN's Level selection is the
// single, authoritative "RN-confirmed level"; this is disclosed, not
// silently substituted.
//
// PRODUCT OWNER DIRECTIVE (2026-10-24) "Fix Disaster Triage and
// Review-Step Completion Logic" -- superseded the original "Planned
// Disaster Placement" required field: "Disaster Triage is asking the RN
// to predict future placement... overly specific. The RN frequently
// cannot know this information... Replace Planned Disaster Placement
// with Emergency Support Assessment." The RN should document WHAT MAKES
// THE PATIENT VULNERABLE during a disaster (current dependency/support
// factors below, all required), not predict WHERE the patient will be
// relocated to (Preferred Emergency Location, now explicitly OPTIONAL --
// "Unknown" is an acceptable, non-blocking answer). Responsible Support
// is likewise no longer a required field -- it "may be documented" when
// an emergency location is specified, otherwise it is Not Applicable /
// Unknown.
export const DISASTER_YES_NO_OPTIONS = ["Yes", "No"];
export const DISASTER_YES_NO_UNKNOWN_OPTIONS = ["Yes", "No", "Unknown"];
export const DISASTER_PREFERRED_EMERGENCY_LOCATION_OPTIONS = [
  "Remain at Residence", "Remain at Facility", "Family or Friend Residence", "Community Shelter", "Unknown", "Other",
];
export const DISASTER_REQUIREMENTS_OPTIONS = ["Oxygen", "Medication Supply", "DME/Equipment", "Backup Power", "None"];

/** Disaster Triage Assessment summary -- level, short label, dependency
 * factors (the level's selected conditions), the required Emergency
 * Support Assessment (current vulnerability/dependency factors), the
 * optional Preferred Emergency Location, and the optional Responsible
 * Support. */
export function summarizeDisasterTriage(safetyData = {}) {
  const level = safetyData.disasterLevel || "";
  const shortLabel = level.startsWith("Level 1") ? "Level 1" : level.startsWith("Level 2") ? "Level 2" : level.startsWith("Level 3") ? "Level 3" : "";
  const conditionsPath = DISASTER_TRIAGE_CONDITIONS_PATH_BY_LEVEL[level];
  const conditions = conditionsPath ? (safetyData[conditionsPath] || []) : [];
  const livesAlone = safetyData.disasterLivesAlone || "";
  const requiresEvacuationAssistance = safetyData.disasterRequiresEvacuationAssistance || "";
  const caregiverAvailable = safetyData.disasterCaregiverAvailable || "";
  const transportationAvailable = safetyData.disasterTransportationAvailable || "";
  const requiresElectricity = safetyData.disasterRequiresElectricity || "";
  const oxygenDependent = safetyData.disasterOxygenDependent || "";
  const backupPowerAvailable = safetyData.disasterBackupPowerAvailable || "";
  const preferredEmergencyLocation = safetyData.disasterPreferredEmergencyLocation || "";
  const responsibleSupport = safetyData.disasterResponsibleSupport || "";
  const requirements = safetyData.disasterRequirements || [];
  // Disaster Triage is complete once Level is selected AND the full
  // Emergency Support Assessment is answered (Lives Alone, Requires
  // Evacuation Assistance, Caregiver Available, Transportation
  // Available, Requires Electricity, Oxygen Dependent, Backup Power
  // Available -- "Unknown" counts as answered for the three
  // Yes/No/Unknown questions). Preferred Emergency Location and
  // Responsible Support are intentionally excluded from this gate --
  // both remain genuinely optional, never blocking completion.
  const complete = Boolean(level)
    && Boolean(livesAlone)
    && Boolean(requiresEvacuationAssistance)
    && Boolean(caregiverAvailable)
    && Boolean(transportationAvailable)
    && Boolean(requiresElectricity)
    && Boolean(oxygenDependent)
    && Boolean(backupPowerAvailable);
  return {
    complete,
    level,
    shortLabel,
    conditions,
    livesAlone,
    requiresEvacuationAssistance,
    caregiverAvailable,
    transportationAvailable,
    requiresElectricity,
    oxygenDependent,
    backupPowerAvailable,
    preferredEmergencyLocation,
    responsibleSupport,
    requirements,
    clarification: safetyData.disasterTriageClarificationNote || "",
  };
}

// PRODUCT OWNER DECISION (2026-10-24) "Safety Is One Assessment" --
// supersedes the prior "four independent Edit Sheets" presentation.
// "STOP TREATING SAFETY AS FOUR SEPARATE ASSESSMENTS... REPLACE 4
// INDEPENDENT ASSESSMENT SHEETS WITH 1 SAFETY ASSESSMENT WIZARD." The
// four underlying summarize* functions above are UNCHANGED (same
// fields, same completion rules, same validateRNICA gates) -- this is
// purely a single composed read of all four plus one consolidated
// status, so the new single-card Overview and the new single-sheet
// wizard (and any future caller) always agree on what counts as
// "Completed" / "In Progress" / "Not Started" for the WHOLE Safety
// assessment, not just one of its four parts.
export const SAFETY_WIZARD_STEPS = [
  { id: "environmental", label: "Environmental Safety", cardTitles: ["Environmental Safety"] },
  { id: "fallRisk", label: "Morse Fall Scale", cardTitles: ["Fall Risk and Transfer Safety"] },
  { id: "oxygen", label: "Oxygen Safety", cardTitles: ["Oxygen Safety"] },
  { id: "disaster", label: "Disaster Triage", cardTitles: ["Disaster Triage"] },
  { id: "review", label: "Review & Complete", cardTitles: null },
];

/** Which wizard step (by id) should be opened for the first incomplete
 * part of the assessment -- used both by validation deep-linking
 * ("Opening that validation item launches the unified modal at the
 * first incomplete step") and by Edit Assessment's own default-to-
 * Step-1-unless-validation rule. Returns "review" once every part is
 * complete (nothing left to fix, land on the consolidated summary). */
export function getFirstIncompleteSafetyStepId(summary) {
  if (!summary?.environmental?.complete) return "environmental";
  if (!summary?.fallRisk?.complete) return "fallRisk";
  if (!summary?.oxygen?.complete) return "oxygen";
  if (!summary?.disaster?.complete) return "disaster";
  return "review";
}

// PRODUCT OWNER DIRECTIVE (2026-12-01) "Make Safety & Clinical Risk One
// Assessment" section 12 -- four states, not two: Not Started / In
// Progress / Complete / Needs Review. "Complete" requires BOTH every
// part being complete-or-confirmed-Not-Applicable AND an explicit RN
// submission via "Complete Safety Assessment" on the Review step
// (`safetyAssessmentCompletedAt`, section 2/3/12) -- answering every
// question is not itself the completion action, same as Pain's own
// "Save Completed Assessment" gesture elsewhere in this app. "Needs
// Review" is the drift case: a previously-submitted assessment whose
// underlying data has since become incomplete again (e.g. a field was
// edited back out, or Oxygen newly became applicable but was never
// re-confirmed) -- the main page must never keep showing a stale
// "Complete" badge over data that no longer actually satisfies it.
export function summarizeSafetyAssessment(safetyData = {}, fullFormData = {}) {
  const environmental = summarizeEnvironmentalSafety(safetyData, fullFormData);
  const fallRisk = summarizeFallRisk(safetyData);
  const oxygen = summarizeOxygenSafety(safetyData, fullFormData);
  const disaster = summarizeDisasterTriage(safetyData);

  // Oxygen Safety is always counted (never excluded) -- the step itself
  // is always shown in the wizard sequence per directive section 4; when
  // Not Applicable, it only counts as complete once the RN has
  // explicitly confirmed that, never auto-attested.
  const applicableSections = [environmental, fallRisk, oxygen, disaster];
  const completedCount = applicableSections.filter((s) => s.complete).length;
  const totalCount = applicableSections.length;
  const allPartsComplete = completedCount === totalCount;

  const completedAt = safetyData.safetyAssessmentCompletedAt || "";
  let status = "Not Started";
  if (completedAt) {
    status = allPartsComplete ? "Complete" : "Needs Review";
  } else if (completedCount > 0) {
    status = "In Progress";
  }
  const complete = status === "Complete";

  return {
    environmental, fallRisk, oxygen, disaster,
    complete, allPartsComplete, status, completedCount, totalCount, completedAt,
  };
}
