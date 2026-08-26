// ════════════════════════════════════════════════════════════════
// SECTION 10 — Clinical Narrative & Disease Trajectory
// (RN ICA Master Map SECTION 10, deterministic draft assembly).
//
// This module is intentionally separate from hopeReportMapper.js:
// hopeReportMapper.js stays responsible for CMS HOPE representation and
// completion-status logic, while this file owns general RN clinical
// narrative documentation. Neither module imports the other.
//
// buildClinicalNarrative() is NOT an AI feature. It is a fixed-rule
// template renderer: it reads already-documented structured facts out
// of `formData` and formats them into plain sentences using static
// rules. No model call, no network request, no inference of
// unsupported findings, no randomness, no wall-clock timestamp in the
// output — identical inputs always produce identical output.
//
// Rules enforced by this function:
//   - Uses only documented structured facts already present in
//     `formData`; never invents values.
//   - Omits any topic whose backing field(s) are not documented
//     (blank/undefined/null) rather than emitting placeholder text.
//   - Preserves a clinician-documented value of 0 (e.g. "0 recent
//     hospitalizations") as meaningful, distinct from "not
//     documented" — presence is tested explicitly, never by JS
//     truthiness, so numeric/string zero is never treated as absent.
//   - Never determines or states hospice eligibility.
//   - Never assigns or states a prognosis / time-limited survival
//     estimate.
//   - Never claims LCD (local coverage determination) criteria are
//     met.
//   - Never selects or infers a disease trajectory — it only restates
//     the trajectory the clinician explicitly selected elsewhere.
//   - Never reads or restates `lcdEligibilityNarrative` — that field
//     is the distinct physician/LCD eligibility-support narrative and
//     is never merged with this RN clinical-findings narrative.
//   - Never runs automatically. This function has no side effects and
//     is invoked only when the caller (an explicit user action such as
//     a "Build Draft from Documented Findings" button) chooses to call
//     it — nothing here schedules, memoizes-on-mount, or subscribes to
//     data changes.
//   - Ends with a fixed pointer sentence to the current Plan of Care;
//     never creates, infers, or duplicates POC problems itself.
// ════════════════════════════════════════════════════════════════

// Stable, storage-safe keys for the Disease Trajectory selector. Persist
// `value` in formData.diagnoses.diseaseTrajectory — never the label —
// so relabeling copy later never requires a data migration.
export const DISEASE_TRAJECTORY_OPTIONS = [
  { value: "RAPID_DECLINE", label: "Rapid decline" },
  { value: "SAW_TOOTHED_DECLINE", label: "Saw-toothed decline (symptom exacerbations and improvement)" },
  { value: "SLOW_STEADY_DECLINE", label: "Slow, steady decline" },
  { value: "OTHER_UNCERTAIN", label: "Other / uncertain" },
];

// Legacy values persisted by earlier builds of this form, before the
// stable-key taxonomy above existed. These are NOT silently converted
// to a new value (e.g. "Decline" is not reliably equivalent to
// "Rapid decline" — a slow decline could also have been charted as
// "Decline"). They remain stored and displayed as-is, flagged for
// clinician review so a real reassessment/selection happens instead of
// a guessed mapping.
export const LEGACY_DISEASE_TRAJECTORY_VALUES = ["Decline", "Plateau", "Fluctuating"];

export function isLegacyDiseaseTrajectoryValue(value) {
  return LEGACY_DISEASE_TRAJECTORY_VALUES.includes(value);
}

export function getDiseaseTrajectoryLabel(value) {
  if (!value) return "";
  const match = DISEASE_TRAJECTORY_OPTIONS.find((opt) => opt.value === value);
  if (match) return match.label;
  // Legacy or otherwise-unrecognized stored value — display verbatim.
  return value;
}

// Explicit presence test. Used everywhere in this file instead of
// truthiness so a clinician-documented "0" (e.g. zero recent
// hospitalizations) is treated as documented data, distinct from a
// blank/unset field ("" / null / undefined), which means "not
// documented."
export function hasDocumentedValue(value) {
  return value !== "" && value !== null && value !== undefined;
}

function narrativeLine(condition, text) {
  return condition ? text : null;
}

// RNICA.jsx's ADL fields (musculoskeletal.adl.{bathing,dressing,toileting,
// transferring,eating,grooming}) store the literal 0–5 dependence-scale
// code, not a human-readable word — restating the raw code in a narrative
// ("bathing (3)") is not clinically legible. Map the shared 0–5 scale to a
// plain-language description; per-field UI copy differs slightly ("Setup"
// vs "Setup help only") but the underlying 0–5 CMS-aligned dependence
// scale is identical across all six ADLs, so one shared map is correct.
const ADL_DEPENDENCE_LABELS = {
  "0": "Independent",
  "1": "Setup/supervision only",
  "2": "Supervision",
  "3": "Limited assistance",
  "4": "Extensive assistance",
  "5": "Total dependence",
};

function formatAdlValue(value) {
  return ADL_DEPENDENCE_LABELS[value] ?? value;
}

export function buildClinicalNarrative(formData = {}, patient = {}) {
  const lines = [];
  const dx = formData.diagnoses || {};
  const primaryDx = dx.primaryDiagnosis || {};
  const perf = formData.performanceStatus || {};
  const adl = formData.musculoskeletal?.adl || {};
  const bims = formData.neurological?.hopeItems || {};
  const symptomImpact = formData.symptomImpact?.scores || formData.symptomImpact || {};
  const pain = formData.pain || {};
  const respiratory = formData.respiratory || {};
  const nutrition = formData.nutrition || {};
  const vitals = formData.vitals || {};
  const infection = formData.infection || {};
  const skin = formData.skin || {};
  const pcg = formData.demographics?.pcg || {};
  const psychosocial = formData.psychosocial || {};
  const spiritual = formData.spiritual || {};
  const imminent = formData.imminentDeath || {};
  const admittedFrom = formData.demographics?.livingSituation?.admittedFrom || "";

  const age = patient?.age;
  const sex = patient?.sex || patient?.gender;

  // Patient-specific summary of documented context (not a diagnosis or
  // eligibility statement).
  lines.push(narrativeLine(
    hasDocumentedValue(age) || hasDocumentedValue(sex) || hasDocumentedValue(admittedFrom),
    `Patient${hasDocumentedValue(age) ? ` is a ${age}-year-old` : ""}${hasDocumentedValue(sex) ? ` ${sex}` : ""}${hasDocumentedValue(admittedFrom) ? ` admitted from ${admittedFrom}` : ""}.`
  ));

  // Documented primary diagnosis (restates what was charted; does not
  // state or imply hospice eligibility).
  lines.push(narrativeLine(
    hasDocumentedValue(primaryDx.description) || hasDocumentedValue(primaryDx.icd10),
    `Primary diagnosis is documented as ${primaryDx.description || primaryDx.icd10}${hasDocumentedValue(primaryDx.icd10) && hasDocumentedValue(primaryDx.description) ? ` (ICD-10: ${primaryDx.icd10})` : ""}${hasDocumentedValue(primaryDx.hopeDiagnosisCategory) ? `, HOPE category ${primaryDx.hopeDiagnosisCategory}` : ""}.`
  ));

  // Disease trajectory — restates the clinician's own selection only;
  // this function never selects/infers a trajectory.
  lines.push(narrativeLine(
    hasDocumentedValue(dx.diseaseTrajectory),
    `Disease trajectory is documented as ${getDiseaseTrajectoryLabel(dx.diseaseTrajectory)}.`
  ));

  // Functional decline (PPS/KPS/FAST/ECOG only when documented).
  const functionalParts = [];
  if (hasDocumentedValue(perf.pps)) functionalParts.push(`PPS is documented as ${perf.pps}%`);
  if (hasDocumentedValue(perf.kps)) functionalParts.push(`KPS is documented as ${perf.kps}%`);
  if (hasDocumentedValue(perf.fast)) functionalParts.push(`FAST is documented as ${perf.fast}${hasDocumentedValue(perf.fastStage) ? ` (stage ${perf.fastStage})` : ""}`);
  if (hasDocumentedValue(perf.ecog)) functionalParts.push(`ECOG is documented as ${perf.ecog}`);
  lines.push(narrativeLine(functionalParts.length > 0, functionalParts.join(". ") + (functionalParts.length ? "." : "")));
  lines.push(narrativeLine(hasDocumentedValue(perf.functionalDeclineNotes), `Functional decline notes: ${perf.functionalDeclineNotes}.`));

  // ADL dependence — only the ADLs the RN actually recorded a value for.
  const adlEntries = Object.entries(adl).filter(([, v]) => hasDocumentedValue(v));
  lines.push(narrativeLine(
    adlEntries.length > 0,
    `The assessment records ${adlEntries.map(([k, v]) => `${k} (${formatAdlValue(v)})`).join(", ")}.`
  ));

  // Cognitive status (BIMS) — only recorded items.
  const bimsParts = Object.entries(bims).filter(([, v]) => hasDocumentedValue(v)).map(([k, v]) => `${k} is documented as ${v}`);
  lines.push(narrativeLine(bimsParts.length > 0, `${bimsParts.join("; ")}.`));

  // Symptom burden — only recorded scores.
  const symptomParts = Object.entries(symptomImpact).filter(([, v]) => hasDocumentedValue(v)).map(([k, v]) => `${k}: ${v}`);
  lines.push(narrativeLine(symptomParts.length > 0, `Documented symptom impact screening: ${symptomParts.join(", ")}.`));

  // Pain burden.
  lines.push(narrativeLine(
    hasDocumentedValue(pain.painSeverityCategory) || hasDocumentedValue(pain.neuropathicPain),
    `Pain severity is documented as ${pain.painSeverityCategory || "not categorized"}${hasDocumentedValue(pain.neuropathicPain) ? `; neuropathic pain documented as ${pain.neuropathicPain}` : ""}.`
  ));

  // Respiratory burden.
  const lungSounds = respiratory.lungSounds || [];
  lines.push(narrativeLine(
    hasDocumentedValue(respiratory.sobSeverity) || lungSounds.length > 0,
    `${hasDocumentedValue(respiratory.sobSeverity) ? `Dyspnea severity is documented as ${respiratory.sobSeverity}` : ""}${lungSounds.length ? `${hasDocumentedValue(respiratory.sobSeverity) ? "; " : ""}documented lung sounds: ${lungSounds.join(", ")}` : ""}.`
  ));

  // Nutritional decline.
  lines.push(narrativeLine(
    hasDocumentedValue(nutrition.weightLossPastSixMonths) || hasDocumentedValue(nutrition.appetite),
    `${hasDocumentedValue(nutrition.weightLossPastSixMonths) ? `Weight loss of ${nutrition.weightLossPastSixMonths} over the past six months is documented` : ""}${hasDocumentedValue(nutrition.appetite) ? `${hasDocumentedValue(nutrition.weightLossPastSixMonths) ? "; " : ""}appetite is documented as ${nutrition.appetite}` : ""}.`
  ));

  // Anthropometrics (weight/BMI/MAC) — only documented values.
  const anthro = [];
  if (hasDocumentedValue(vitals.weight)) anthro.push(`weight ${vitals.weight}${vitals.weightUnit || ""}`);
  if (hasDocumentedValue(vitals.bmi)) anthro.push(`BMI ${vitals.bmi}`);
  if (hasDocumentedValue(vitals.mac)) anthro.push(`MAC ${vitals.mac}`);
  lines.push(narrativeLine(anthro.length > 0, `Documented anthropometrics: ${anthro.join(", ")}.`));

  // Infection history.
  const currentInfections = infection.currentInfections || [];
  const infectionParts = [];
  if (currentInfections.length) infectionParts.push(`current infections: ${currentInfections.join(", ")}`);
  if (infection.recurrentInfection === true) infectionParts.push("recurrent infection history is documented");
  if (hasDocumentedValue(infection.infectionHistory)) infectionParts.push(infection.infectionHistory);
  lines.push(narrativeLine(infectionParts.length > 0, `Infection history: ${infectionParts.join("; ")}.`));

  // Integumentary findings.
  const wounds = skin.wounds || [];
  const integParts = [];
  if (hasDocumentedValue(skin.braden?.total)) integParts.push(`Braden total score is documented as ${skin.braden.total}`);
  if (wounds.length) integParts.push(`${wounds.length} documented wound(s)`);
  lines.push(narrativeLine(integParts.length > 0, `${integParts.join(". ")}.`));

  // Hospitalization / ER utilization. recentHospitalizations and
  // recentErVisits are entered as small integers where "0" is a
  // meaningful, clinician-documented answer ("no recent utilization"),
  // distinct from a blank field ("not documented") — hasDocumentedValue() is
  // required here, not truthiness.
  const utilParts = [];
  if (hasDocumentedValue(dx.recentHospitalizations)) utilParts.push(`${dx.recentHospitalizations} recent hospitalization(s)`);
  if (hasDocumentedValue(dx.recentErVisits)) utilParts.push(`${dx.recentErVisits} recent emergency department visit(s)`);
  const utilSentence = utilParts.length ? `${utilParts.join(" and ")} ${utilParts.length > 1 ? "are" : "is"} documented.` : "";
  const utilNotesSentence = hasDocumentedValue(dx.utilizationNotes) ? dx.utilizationNotes : "";
  lines.push(narrativeLine(utilSentence || utilNotesSentence, [utilSentence, utilNotesSentence].filter(Boolean).join(" ")));

  // Caregiver situation.
  lines.push(narrativeLine(
    pcg.noPcg === true || hasDocumentedValue(pcg.willingToProvideCare) || hasDocumentedValue(pcg.ableToAdministerMeds),
    pcg.noPcg === true
      ? "No primary caregiver is documented."
      : `Caregiver willingness to provide care is documented as ${pcg.willingToProvideCare || "not documented"}; ability to administer medications is documented as ${pcg.ableToAdministerMeds || "not documented"}.`
  ));

  // Psychosocial findings.
  const patientConcerns = psychosocial.patientConcerns || [];
  lines.push(narrativeLine(
    patientConcerns.length > 0 || hasDocumentedValue(psychosocial.distressRating),
    `${patientConcerns.length ? `Documented psychosocial concerns: ${patientConcerns.join(", ")}` : ""}${hasDocumentedValue(psychosocial.distressRating) ? `${patientConcerns.length ? "; " : ""}distress rating documented as ${psychosocial.distressRating}` : ""}.`
  ));

  // Spiritual findings.
  const spiritualConcerns = spiritual.spiritualConcerns || [];
  lines.push(narrativeLine(
    spiritualConcerns.length > 0 || hasDocumentedValue(spiritual.spiritualDistressRating),
    `${spiritualConcerns.length ? `Documented spiritual concerns: ${spiritualConcerns.join(", ")}` : ""}${hasDocumentedValue(spiritual.spiritualDistressRating) ? `${spiritualConcerns.length ? "; " : ""}spiritual distress rating documented as ${spiritual.spiritualDistressRating}` : ""}.`
  ));

  // Imminently-dying findings — only restated when explicitly charted.
  // HOPE J0050 ("appearsThreeDaysOrLess") is captured as the literal CMS
  // response code string "0"/"1"/"9" (see RNICA.jsx's imminentDeath field
  // definition), never as "Yes"/"No" — comparing against "Yes" here would
  // never match, silently dropping this narrative line even when J0050 is
  // charted as "1" (Yes).
  const imminentIndicators = imminent.indicators || [];
  const appearsImminent = imminent.appearsThreeDaysOrLess === "1";
  lines.push(narrativeLine(
    appearsImminent || imminentIndicators.length > 0,
    `${appearsImminent ? "The assessment documents that the patient appears to be within three days or less of death" : ""}${imminentIndicators.length ? `${appearsImminent ? "; " : ""}documented indicators: ${imminentIndicators.join(", ")}` : ""}.`
  ));

  // Documented comorbidities (restated verbatim; this is not a
  // statement of LCD-criteria satisfaction, eligibility, or prognosis).
  const comorbidityKeys = Object.entries(dx.hopeComorbidities || {})
    .filter(([k, v]) => v === true && k !== "other")
    .map(([k]) => k);
  lines.push(narrativeLine(comorbidityKeys.length > 0, `Documented comorbidities: ${comorbidityKeys.join(", ")}.`));

  const filtered = lines.filter(Boolean);

  return {
    text: filtered.length
      ? `Clinical Narrative Draft — based on documented assessment findings only.\n\n${filtered.join("\n\n")}\n\nSee current Plan of Care for active problems, goals, and interventions.`
      : "",
    isEmpty: filtered.length === 0,
  };
}

export default buildClinicalNarrative;
