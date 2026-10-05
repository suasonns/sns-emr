// Shared Pain Assessment derivation logic (data-only, no JSX, no styling).
//
// Extracted verbatim (behavior-preserving) from the legacy RNICA.jsx Pain
// module so the same single source of truth can be reused by both:
//   - the legacy generic-section renderer (RNICA.jsx's renderGenericSection,
//     still the data-entry surface for J0900/J0905/J0915/Numeric/PAINAD/
//     FLACC), and
//   - the new approved "Pain & Symptom Burden" summary screen
//     (PainSymptomBurdenOverview.jsx).
//
// Nothing here changes a field, option, HOPE mapping, or validation rule --
// it only centralizes the pure functions that decide (a) which pain scale
// applies to this patient and (b) what AI insights / overdue alerts that
// scale's data supports, so both surfaces compute identical answers from
// identical data instead of two copies drifting apart.

/** Which pain scale applies: "verbal" (Numeric), "non-verbal" (PAINAD,
 * unless FLACC explicitly selected), or "pediatric" (FLACC). Mirrors
 * RNICA.jsx's getPainAssessmentMode/deriveModeFromScreening/
 * normalizePainPatientType exactly. */
export function derivePainAssessmentMode(data, isPediatricAge) {
  const normalizePainPatientType = (type) => {
    if (!type || type === "adult-alert" || type === "alert") return "verbal";
    if (type === "adult" || type === "alert-adult") return "verbal";
    return type;
  };
  const deriveModeFromScreening = (verbalizesPain) => {
    if (isPediatricAge) return "pediatric";
    if (verbalizesPain === "1" || verbalizesPain === "2") return "verbal";
    if (verbalizesPain === "0" || verbalizesPain === "3") return "non-verbal";
    return "verbal";
  };
  const patientType = normalizePainPatientType(data?.painMapMode || deriveModeFromScreening(data?.verbalizesPain));
  const selectedTool = String(data?.assessmentTool || "");
  if (patientType === "verbal") return "verbal";
  if (patientType === "non-verbal") return selectedTool === "FLACC" ? "flacc" : "painad";
  if (patientType === "pediatric") return "flacc";
  return "verbal";
}

/** Current pain score (0-10) regardless of which scale produced it, for a
 * single "SCORE: n/10" badge. PAINAD/FLACC are 0-10 sum-of-five-0-2-items
 * scales already, so no rescaling is needed. Returns null when nothing is
 * documented yet (never fabricates a 0). */
export function resolvePainScore(data, painAssessmentMode) {
  if (painAssessmentMode === "painad") {
    const items = ["breathing", "vocalization", "facialExpression", "bodyLanguage", "consolability"];
    const values = items.map((k) => Number(data?.painad?.[k]));
    if (values.some((v) => Number.isNaN(v))) return null;
    return values.reduce((sum, v) => sum + v, 0);
  }
  if (painAssessmentMode === "flacc") {
    const items = ["face", "legs", "activity", "cry", "consolability"];
    const values = items.map((k) => Number(data?.flacc?.[k]));
    if (values.some((v) => Number.isNaN(v))) return null;
    return values.reduce((sum, v) => sum + v, 0);
  }
  const current = data?.painIntensity?.current;
  if (current === undefined || current === "" || Number.isNaN(Number(current))) return null;
  return Number(current);
}

/** Grounded-only AI pain insight notes -- never fabricates a finding.
 * Verbatim from RNICA.jsx's computeAiPainNotes. */
export function computeAiPainNotes(data) {
  const notes = [];
  const currentPain = data?.currentPain;
  const current = Number(data?.painIntensity?.current);
  const worst = Number(data?.painIntensity?.worst);
  const hasCurrent = currentPain === "1" && data?.painIntensity?.current !== undefined && data?.painIntensity?.current !== "";
  const hasWorst = currentPain === "1" && data?.painIntensity?.worst !== undefined && data?.painIntensity?.worst !== "";
  const managementDocumented = Boolean(data?.routinePainMedicationPresent === "1" || data?.breakthroughPainMedication === "1" || data?.painManagementPlan || (data?.nonPharmInterventions || []).length);

  if (hasCurrent && current >= 7 && !managementDocumented) {
    notes.push({ text: `Current pain is severe (${current}/10) with no documented pain-management intervention.`, field: "Current Pain Intensity" });
  }
  if (hasCurrent && hasWorst && worst - current >= 4) {
    notes.push({ text: `Worst pain (${worst}/10) is substantially higher than current (${current}/10) — breakthrough control may need review.`, field: "Current/Worst Pain Intensity" });
  }
  if (data?.neuropathicPain === "1") {
    notes.push({ text: "Neuropathic pain documented (HOPE J0915) — confirm an adjuvant agent is part of the pain management plan.", field: "Neuropathic Pain" });
  }
  if (data?.painEffectivenessRating && /partial|ineffective/i.test(data.painEffectivenessRating)) {
    notes.push({ text: `Pain management effectiveness documented as "${data.painEffectivenessRating}" — consider regimen reassessment.`, field: "Effectiveness Rating" });
  }
  if (data?.controlStatus === "Uncontrolled") {
    notes.push({ text: "Chronic pain control status documented as Uncontrolled.", field: "Control Status" });
  }
  if (currentPain === "0" && data?.chronicPainHistory === "1" && data?.effectOnFunction) {
    notes.push({ text: `Pain is documented as affecting function/quality of life: "${data.effectOnFunction}".`, field: "Effect on Function/QOL" });
  }
  if (currentPain === "1" && data?.effectOnFunction) {
    notes.push({ text: `Pain is documented as affecting function/quality of life: "${data.effectOnFunction}".`, field: "Effect on Function/QOL" });
  }
  if (currentPain === "1" && !hasCurrent) {
    notes.push({ text: "Patient reports current pain but current intensity has not been documented.", field: "Current Pain / Current Intensity" });
  }
  return notes;
}

/** Real, currently-implemented overdue/incomplete-documentation rules only
 * -- no arbitrary timing/deadline logic. Verbatim from RNICA.jsx's
 * computePainOverdueAlerts. */
export function computePainOverdueAlerts(data, painAssessmentMode) {
  const alerts = [];
  if (!data?.screenedForPain) {
    alerts.push("Pain screening incomplete — was the patient assessed for pain? (HOPE J0900.A) has not been answered.");
    return alerts;
  }
  if (data.screenedForPain === "0" && !data?.reasonNotAssessed) {
    alerts.push("Reason pain assessment was not completed is required.");
  }
  if (data.screenedForPain === "1" && !data?.currentPain) {
    alerts.push("Current pain status (\"Is the patient experiencing pain now?\") has not been documented.");
  }
  if (data?.currentPain === "0" && !data?.chronicPainHistory) {
    alerts.push("Chronic/recurrent pain history has not been documented.");
  }
  if (data?.currentPain === "1" && !data?.comprehensiveAssessmentCompleted) {
    alerts.push("Required comprehensive pain assessment incomplete.");
  }
  if (painAssessmentMode === "painad") {
    const complete = ["breathing", "vocalization", "facialExpression", "bodyLanguage", "consolability"].every((k) => data?.painad?.[k] !== undefined && data?.painad?.[k] !== "");
    if (!complete) alerts.push("Required PAINAD Scale incomplete.");
  }
  if (painAssessmentMode === "flacc") {
    const complete = ["face", "legs", "activity", "cry", "consolability"].every((k) => data?.flacc?.[k] !== undefined && data?.flacc?.[k] !== "");
    if (!complete) alerts.push("Required FLACC Scale incomplete.");
  }
  const managementDocumented = Boolean(data?.routinePainMedicationPresent === "1" || data?.breakthroughPainMedication === "1" || data?.painManagementPlan || (data?.nonPharmInterventions || []).length);
  if (data?.currentPain === "1" && Number(data?.painIntensity?.current) >= 7 && !managementDocumented) {
    alerts.push("Current pain is severe without documented intervention.");
  }
  if (data?.breakthroughPainMedication === "1" && !data?.painEffectivenessRating) {
    alerts.push("Breakthrough pain medication documented without an effectiveness assessment.");
  }
  if (data?.painActiveProblem === "1" && !managementDocumented) {
    alerts.push("Active pain problem documented without a pain-management plan.");
  }
  return alerts;
}

const joinList = (arr) => (Array.isArray(arr) && arr.length ? arr.join(", ") : "");

/** Severity code ("0"-"3") -> display label, for the Symptom Burden Matrix
 * (HOPE J2051 derived fields, all graded None/Mild/Moderate/Severe except
 * Anxiety/Agitation which are presence-only "0"/"1"). */
const GRADED_SEVERITY_LABELS = { "0": "None", "1": "Mild", "2": "Moderate", "3": "Severe" };
const PRESENCE_LABELS = { "0": "Not present", "1": "Present" };

/** Compact Symptom Burden Matrix rows sourced from `formData.symptomImpact`
 * (the live HOPE J2051 A-H derivation already synced from each symptom's
 * true owning section -- see RNICA.jsx's symptomImpact sync effect). Only
 * the 7 non-Pain J2051 items are listed here (Pain itself is this screen).
 * Never invents a symptom the HOPE item set doesn't have. */
export function buildSymptomBurdenRows(symptomImpact) {
  return [
    { key: "shortnessOfBreath", label: "Shortness of Breath", hopeCode: "J2051B", moduleKey: "respiratory", graded: true, value: symptomImpact?.shortnessOfBreath },
    { key: "nausea", label: "Nausea", hopeCode: "J2051D", moduleKey: "gastrointestinal", graded: true, value: symptomImpact?.nausea },
    { key: "vomiting", label: "Vomiting", hopeCode: "J2051E", moduleKey: "gastrointestinal", graded: true, value: symptomImpact?.vomiting },
    { key: "diarrhea", label: "Diarrhea", hopeCode: "J2051F", moduleKey: "gastrointestinal", graded: true, value: symptomImpact?.diarrhea },
    { key: "constipation", label: "Constipation", hopeCode: "J2051G", moduleKey: "gastrointestinal", graded: true, value: symptomImpact?.constipation },
    { key: "anxiety", label: "Anxiety", hopeCode: "J2051C", moduleKey: "neurological", graded: false, value: symptomImpact?.anxiety },
    { key: "agitation", label: "Agitation", hopeCode: "J2051H", moduleKey: "neurological", graded: false, value: symptomImpact?.agitation },
  ].map((row) => ({
    ...row,
    statusLabel: row.value === undefined || row.value === "" || row.value === null
      ? null
      : (row.graded ? GRADED_SEVERITY_LABELS[row.value] : PRESENCE_LABELS[row.value]) || null,
    severityTone: row.value === "3" ? "critical" : row.value === "2" ? "warning" : row.value === "1" ? "info" : "neutral",
  }));
}

export { joinList };
