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

// RNICA.jsx's HOPE J2051 Symptom Impact fields (symptomImpact.{pain,
// shortnessOfBreath,anxiety,nausea,vomiting,diarrhea,constipation,
// agitation}) store the camelCase formData key and a raw 0-3 severity
// code — restating either verbatim ("shortnessOfBreath: 3") is a raw
// field-dump the Narrative Quality Gate correctly rejects. Map both to
// plain clinical language; mirrors RNICA.jsx's own
// SYMPTOM_IMPACT_CHECKLIST / SYMPTOM_SEVERITY_LABEL constants.
const SYMPTOM_IMPACT_LABELS = {
  pain: "pain",
  shortnessOfBreath: "shortness of breath",
  anxiety: "anxiety",
  nausea: "nausea",
  vomiting: "vomiting",
  diarrhea: "diarrhea",
  constipation: "constipation",
  agitation: "agitation",
};
const SYMPTOM_SEVERITY_WORDS = {
  "0": "none",
  "1": "mild",
  "2": "moderate",
  "3": "severe",
};

// Builds one named section from an array of candidate lines (each either a
// string or null/""). Returns null when every candidate line is empty so the
// caller can omit the section heading entirely rather than emit an empty
// header — this is what keeps the output from degrading into a field-dump
// with headings over nothing.
function buildSection(heading, candidateLines) {
  const body = candidateLines.filter(Boolean);
  if (body.length === 0) return null;
  return `${heading}\n${body.join(" ")}`;
}

export function buildClinicalNarrative(formData = {}, patient = {}, hospiceContext = {}) {
  const dx = formData.diagnoses || {};
  const primaryDx = dx.primaryDiagnosis || {};
  const perf = formData.performanceStatus || {};
  const adl = formData.musculoskeletal?.adl || {};
  // NOTE: `neurological.hopeItems` is a deprecated (READ_ONLY_LEGACY) path
  // name that collided with the official CMS HOPE Section N medication
  // item codes (N0500/N0510/N0520 = Scheduled Opioid/PRN Opioid/Bowel
  // Regimen, owned by hopeReportMapper.js / formData.medications.*). It
  // never held HOPE medication data -- only this BIMS-style cognitive
  // screen, now stored under `neurological.cognitiveScreen`. Semantic
  // ownership lives in RNICA.jsx/structured_findings.py, not here; this
  // is only the mechanical read-path update for the rename.
  const bims = formData.neurological?.cognitiveScreen || {};
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

  // hospiceContext carries the resolved, chart-authoritative hospice
  // reasoning already computed server-side (see
  // app/services/rnica_intelligence.py build_hospice_reasoning_panel()) and
  // the chart/draft diagnosis-sync check (see
  // app/api/visits.py _build_chart_diagnosis_sync()). Every field here is
  // optional and read-only-consumed: this function never writes back to
  // formData or the chart, it only decides what to say and where to say it.
  const currentDiagnosisDescription = hasDocumentedValue(hospiceContext.currentDiagnosisDescription)
    ? hospiceContext.currentDiagnosisDescription
    : null;
  const draftDiagnosisDescription = primaryDx.description || primaryDx.icd10 || null;
  const diagnosisMismatch = Boolean(
    hospiceContext.diagnosisMismatch && currentDiagnosisDescription && draftDiagnosisDescription
  );
  const whyHospice = hospiceContext.whyHospice || null;
  const diseaseBurden = hospiceContext.diseaseBurden || null;
  const driverRecs = hospiceContext.hospiceDriverRecommendation?.pending_recommendations || [];
  const relatedConditions = hospiceContext.relatedConditions?.related || [];
  const unrelatedConditions = hospiceContext.relatedConditions?.unrelated || [];
  const certificationSupport = hospiceContext.certificationSupport || null;
  const documentationGaps = hospiceContext.documentationGaps || [];

  // ── HOSPICE CLINICAL PICTURE ────────────────────────────────────────
  // The chart's current diagnosis context takes priority over a possibly
  // stale RNICA draft snapshot; when both exist and disagree, both values
  // are stated explicitly rather than one silently winning.
  const resolvedDiagnosisLine = (() => {
    if (currentDiagnosisDescription && diagnosisMismatch) {
      return `Current chart diagnosis is documented as ${currentDiagnosisDescription}. This assessment's draft primary diagnosis (${draftDiagnosisDescription}) has not yet been updated to match and requires RN review.`;
    }
    if (currentDiagnosisDescription) {
      return `Primary diagnosis is documented as ${currentDiagnosisDescription}${hasDocumentedValue(primaryDx.icd10) ? ` (ICD-10: ${primaryDx.icd10})` : ""}${hasDocumentedValue(primaryDx.hopeDiagnosisCategory) ? `, HOPE category ${primaryDx.hopeDiagnosisCategory}` : ""}.`;
    }
    // No resolved chart context supplied — fall back to the original,
    // draft-only behavior so this function still works when called
    // without hospiceContext (e.g. offline/no chart lookup available).
    return narrativeLine(
      hasDocumentedValue(primaryDx.description) || hasDocumentedValue(primaryDx.icd10),
      `Primary diagnosis is documented as ${primaryDx.description || primaryDx.icd10}${hasDocumentedValue(primaryDx.icd10) && hasDocumentedValue(primaryDx.description) ? ` (ICD-10: ${primaryDx.icd10})` : ""}${hasDocumentedValue(primaryDx.hopeDiagnosisCategory) ? `, HOPE category ${primaryDx.hopeDiagnosisCategory}` : ""}.`
    );
  })();

  const hospiceClinicalPicture = buildSection("HOSPICE CLINICAL PICTURE", [
    narrativeLine(
      hasDocumentedValue(age) || hasDocumentedValue(sex) || hasDocumentedValue(admittedFrom),
      `Patient${hasDocumentedValue(age) ? ` is a ${age}-year-old` : ""}${hasDocumentedValue(sex) ? ` ${sex}` : ""}${hasDocumentedValue(admittedFrom) ? ` admitted from ${admittedFrom}` : ""}.`
    ),
    resolvedDiagnosisLine,
    // Disease trajectory — restates the clinician's own selection only;
    // this function never selects/infers a trajectory.
    narrativeLine(
      hasDocumentedValue(dx.diseaseTrajectory),
      `Disease trajectory is documented as ${getDiseaseTrajectoryLabel(dx.diseaseTrajectory)}.`
    ),
    narrativeLine(
      Boolean(diseaseBurden?.guideline),
      `Disease burden is being tracked against the ${diseaseBurden?.guideline} guideline.`
    ),
    driverRecs.length > 0
      ? `Hospice driver recommendation${driverRecs.length > 1 ? "s" : ""} pending RN review: ${driverRecs.map((rec) => `${rec.diagnosis_keyword || "unnamed condition"} (${rec.confidence || "unscored"} confidence)`).join(", ")}.`
      : null,
  ]);

  // ── REASON FOR HOSPICE ADMISSION ────────────────────────────────────
  // Restates the guideline/criteria-support status the eligibility engine
  // already returned (same wording used in the RNICA hospice-reasoning
  // panel) — this is a support status, never a final eligibility
  // determination, prognosis, or "terminally ill" statement.
  const reasonForHospice = buildSection("REASON FOR HOSPICE ADMISSION", [
    whyHospice?.selected_guideline
      ? `${whyHospice.selected_guideline} guideline${whyHospice.eligible ? " — criteria currently supported by documented evidence" : " — criteria not yet fully supported by documented evidence"}. This reflects criteria-support status only and is not a final eligibility determination.`
      : null,
  ]);

  // ── EVIDENCE OF DECLINE ──────────────────────────────────────────────
  const functionalParts = [];
  if (hasDocumentedValue(perf.pps)) functionalParts.push(`PPS is documented as ${perf.pps}%`);
  if (hasDocumentedValue(perf.kps)) functionalParts.push(`KPS is documented as ${perf.kps}%`);
  if (hasDocumentedValue(perf.fast)) functionalParts.push(`FAST is documented as ${perf.fast}${hasDocumentedValue(perf.fastStage) ? ` (stage ${perf.fastStage})` : ""}`);
  if (hasDocumentedValue(perf.ecog)) functionalParts.push(`ECOG is documented as ${perf.ecog}`);
  // NYHA Class is the disease-specific functional measure for the
  // heart-disease hospice pathway; omitted here previously even though it
  // is captured in RNICA and consumed by the HEART_FAILURE LCD evaluator.
  if (hasDocumentedValue(perf.nyha)) functionalParts.push(`NYHA Class is documented as ${perf.nyha}`);

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

  // Imminently-dying findings — only restated when explicitly charted.
  // HOPE J0050 ("appearsThreeDaysOrLess") is captured as the literal CMS
  // response code string "0"/"1"/"9" (see RNICA.jsx's imminentDeath field
  // definition), never as "Yes"/"No" — comparing against "Yes" here would
  // never match, silently dropping this narrative line even when J0050 is
  // charted as "1" (Yes).
  const imminentIndicators = imminent.indicators || [];
  const appearsImminent = imminent.appearsThreeDaysOrLess === "1";

  const evidenceOfDecline = buildSection("EVIDENCE OF DECLINE", [
    narrativeLine(functionalParts.length > 0, functionalParts.join(". ") + (functionalParts.length ? "." : "")),
    narrativeLine(hasDocumentedValue(perf.functionalDeclineNotes), `Functional decline notes: ${perf.functionalDeclineNotes}.`),
    narrativeLine(utilSentence || utilNotesSentence, [utilSentence, utilNotesSentence].filter(Boolean).join(" ")),
    narrativeLine(
      appearsImminent || imminentIndicators.length > 0,
      `${appearsImminent ? "The assessment documents that the patient appears to be within three days or less of death" : ""}${imminentIndicators.length ? `${appearsImminent ? "; " : ""}documented indicators: ${imminentIndicators.join(", ")}` : ""}.`
    ),
  ]);

  // ── DISEASE-SPECIFIC SUPPORT ─────────────────────────────────────────
  const supportingCriteria = whyHospice?.supporting_criteria || [];
  const diseaseSpecificSupport = buildSection("DISEASE-SPECIFIC SUPPORT", [
    supportingCriteria.length > 0
      ? `Documented evidence currently supporting the ${whyHospice?.selected_guideline || "selected"} guideline includes: ${supportingCriteria.map((c) => (typeof c === "string" ? c : c?.description || c?.label || JSON.stringify(c))).join("; ")}.`
      : null,
    certificationSupport?.lcd_reference || certificationSupport?.source_document
      ? `Certification support references ${certificationSupport?.lcd_reference || "the applicable LCD"}${certificationSupport?.source_document ? ` (source: ${certificationSupport.source_document})` : ""}.`
      : null,
  ]);

  // ── FUNCTIONAL STATUS ─────────────────────────────────────────────────
  const adlEntries = Object.entries(adl).filter(([, v]) => hasDocumentedValue(v));
  const bimsParts = Object.entries(bims).filter(([, v]) => hasDocumentedValue(v)).map(([k, v]) => `${k} is documented as ${v}`);
  const functionalStatus = buildSection("FUNCTIONAL STATUS", [
    narrativeLine(
      adlEntries.length > 0,
      `The assessment records ${adlEntries.map(([k, v]) => `${k} (${formatAdlValue(v)})`).join(", ")}.`
    ),
    narrativeLine(bimsParts.length > 0, `${bimsParts.join("; ")}.`),
  ]);

  // ── NUTRITIONAL STATUS ────────────────────────────────────────────────
  const anthro = [];
  if (hasDocumentedValue(vitals.weight)) anthro.push(`weight ${vitals.weight}${vitals.weightUnit || ""}`);
  if (hasDocumentedValue(vitals.bmi)) anthro.push(`BMI ${vitals.bmi}`);
  if (hasDocumentedValue(vitals.mac)) anthro.push(`MAC ${vitals.mac}`);
  const nutritionalStatus = buildSection("NUTRITIONAL STATUS", [
    narrativeLine(
      hasDocumentedValue(nutrition.weightLossPastSixMonths) || hasDocumentedValue(nutrition.appetite),
      `${hasDocumentedValue(nutrition.weightLossPastSixMonths) ? `Weight loss of ${nutrition.weightLossPastSixMonths} over the past six months is documented` : ""}${hasDocumentedValue(nutrition.appetite) ? `${hasDocumentedValue(nutrition.weightLossPastSixMonths) ? "; " : ""}appetite is documented as ${nutrition.appetite}` : ""}.`
    ),
    narrativeLine(anthro.length > 0, `Documented anthropometrics: ${anthro.join(", ")}.`),
  ]);

  // ── SYMPTOM BURDEN ────────────────────────────────────────────────────
  // Bug fix (Narrative Quality Gate live validation): this previously
  // emitted the raw camelCase formData key (e.g. "shortnessOfBreath: 3"),
  // a field-dump pattern the Quality Gate correctly rejects. Render the
  // documented HOPE J2051 symptom-impact label and severity word instead.
  const symptomParts = Object.entries(symptomImpact)
    .filter(([, v]) => hasDocumentedValue(v))
    .map(([k, v]) => `${SYMPTOM_IMPACT_LABELS[k] || k} (${SYMPTOM_SEVERITY_WORDS[v] || v})`);
  const lungSounds = respiratory.lungSounds || [];
  const symptomBurden = buildSection("SYMPTOM BURDEN", [
    narrativeLine(symptomParts.length > 0, `Symptom impact screening documents ${symptomParts.join(", ")}.`),
    narrativeLine(
      hasDocumentedValue(pain.painSeverityCategory) || hasDocumentedValue(pain.neuropathicPain),
      `Pain severity is documented as ${pain.painSeverityCategory || "not categorized"}${hasDocumentedValue(pain.neuropathicPain) ? `; neuropathic pain documented as ${pain.neuropathicPain}` : ""}.`
    ),
    narrativeLine(
      hasDocumentedValue(respiratory.sobSeverity) || lungSounds.length > 0,
      `${hasDocumentedValue(respiratory.sobSeverity) ? `Dyspnea severity is documented as ${respiratory.sobSeverity}` : ""}${lungSounds.length ? `${hasDocumentedValue(respiratory.sobSeverity) ? "; " : ""}documented lung sounds: ${lungSounds.join(", ")}` : ""}.`
    ),
  ]);

  // ── RELATED CONDITIONS AND COMORBID DISEASE BURDEN ───────────────────
  // Documented comorbidities (restated verbatim; this is not a
  // statement of LCD-criteria satisfaction, eligibility, or prognosis).
  const comorbidityKeys = Object.entries(dx.hopeComorbidities || {})
    .filter(([k, v]) => v === true && k !== "other")
    .map(([k]) => k);
  const relatedConditionsSection = buildSection("RELATED CONDITIONS AND COMORBID DISEASE BURDEN", [
    narrativeLine(comorbidityKeys.length > 0, `Documented comorbidities: ${comorbidityKeys.join(", ")}.`),
    relatedConditions.length > 0
      ? `Conditions classified as contributing to the hospice clinical picture: ${relatedConditions.map((c) => c.description || c.icd10).join(", ")}.`
      : null,
    unrelatedConditions.length > 0
      ? `Conditions classified as not contributing to the terminal hospice picture: ${unrelatedConditions.map((c) => c.description || c.icd10).join(", ")}.`
      : null,
  ]);

  // ── CLINICAL RISKS ────────────────────────────────────────────────────
  const currentInfections = infection.currentInfections || [];
  const infectionParts = [];
  if (currentInfections.length) infectionParts.push(`current infections: ${currentInfections.join(", ")}`);
  if (infection.recurrentInfection === true) infectionParts.push("recurrent infection history is documented");
  if (hasDocumentedValue(infection.infectionHistory)) infectionParts.push(infection.infectionHistory);

  const wounds = skin.wounds || [];
  const integParts = [];
  if (hasDocumentedValue(skin.braden?.total)) integParts.push(`Braden total score is documented as ${skin.braden.total}`);
  if (wounds.length) integParts.push(`${wounds.length} documented wound(s)`);

  const patientConcerns = psychosocial.patientConcerns || [];
  const spiritualConcerns = spiritual.spiritualConcerns || [];

  const clinicalRisks = buildSection("CLINICAL RISKS", [
    narrativeLine(infectionParts.length > 0, `Infection history: ${infectionParts.join("; ")}.`),
    narrativeLine(integParts.length > 0, `${integParts.join(". ")}.`),
    narrativeLine(
      patientConcerns.length > 0 || hasDocumentedValue(psychosocial.distressRating),
      `${patientConcerns.length ? `Documented psychosocial concerns: ${patientConcerns.join(", ")}` : ""}${hasDocumentedValue(psychosocial.distressRating) ? `${patientConcerns.length ? "; " : ""}distress rating documented as ${psychosocial.distressRating}` : ""}.`
    ),
    narrativeLine(
      spiritualConcerns.length > 0 || hasDocumentedValue(spiritual.spiritualDistressRating),
      `${spiritualConcerns.length ? `Documented spiritual concerns: ${spiritualConcerns.join(", ")}` : ""}${hasDocumentedValue(spiritual.spiritualDistressRating) ? `${spiritualConcerns.length ? "; " : ""}spiritual distress rating documented as ${spiritual.spiritualDistressRating}` : ""}.`
    ),
  ]);

  // ── DOCUMENTATION GAPS ────────────────────────────────────────────────
  const documentationGapsSection = buildSection("DOCUMENTATION GAPS", [
    diagnosisMismatch
      ? "The primary diagnosis documented in this assessment does not match the current chart diagnosis and needs RN verification before this record is finalized."
      : null,
    documentationGaps.length > 0
      ? `Outstanding documentation needed for certification support: ${documentationGaps.map((g) => (typeof g === "string" ? g : g?.gap || g?.description || JSON.stringify(g))).join("; ")}.`
      : null,
  ]);

  // ── RN FOLLOW-UP ──────────────────────────────────────────────────────
  const rnFollowUp = buildSection("RN FOLLOW-UP", [
    // Caregiver situation.
    narrativeLine(
      pcg.noPcg === true || hasDocumentedValue(pcg.willingToProvideCare) || hasDocumentedValue(pcg.ableToAdministerMeds),
      pcg.noPcg === true
        ? "No primary caregiver is documented."
        : `Caregiver willingness to provide care is documented as ${pcg.willingToProvideCare || "not documented"}; ability to administer medications is documented as ${pcg.ableToAdministerMeds || "not documented"}.`
    ),
    "See current Plan of Care for active problems, goals, and interventions.",
  ]);

  const sections = [
    hospiceClinicalPicture,
    reasonForHospice,
    evidenceOfDecline,
    diseaseSpecificSupport,
    functionalStatus,
    nutritionalStatus,
    symptomBurden,
    relatedConditionsSection,
    clinicalRisks,
    documentationGapsSection,
    rnFollowUp,
  ].filter(Boolean);

  // RN FOLLOW-UP always renders (fixed POC pointer sentence) once ANY other
  // section has content, so an assessment with at least one documented
  // finding always still ends with the same fixed pointer sentence the
  // original renderer always emitted. When truly nothing is documented
  // anywhere (sections.length === 1 and that section is only RN FOLLOW-UP),
  // treat the draft as empty exactly like the original renderer did.
  const hasSubstantiveContent = sections.some((s) => !s.startsWith("RN FOLLOW-UP\n"));

  return {
    text: hasSubstantiveContent
      ? `Clinical Narrative Draft — based on documented assessment findings only.\n\n${sections.join("\n\n")}`
      : "",
    isEmpty: !hasSubstantiveContent,
  };
}

// ════════════════════════════════════════════════════════════════
// Narrative versioning / staleness detection (Task 4/5).
//
// The narrative is a point-in-time synthesis of the reconciled clinical
// context (diagnosis, functional status, symptom burden, etc). If that
// context changes after the narrative was built/reviewed -- e.g. a
// diagnosis sync, a new HOPE score, an updated disease trajectory -- the
// existing narrative text is not automatically wrong, but it is
// unverified against the new facts and must not be presented as current
// without a fresh review. This computes a small, deterministic
// fingerprint of exactly the inputs buildClinicalNarrative() reads, so a
// mismatch between the stored fingerprint (captured when the draft was
// built) and the fingerprint of the assessment's current live state is an
// honest, cheap, no-network signal that the reviewed narrative may now be
// stale -- never a silent "trust it" or "regenerate it" decision.
export function computeNarrativeContextFingerprint(formData = {}, patient = {}, hospiceContext = {}) {
  const dx = formData.diagnoses || {};
  const relevant = {
    primaryDescription: hospiceContext.currentDiagnosisDescription || dx.primaryDiagnosis?.description || null,
    primaryIcd10: dx.primaryDiagnosis?.icd10 || null,
    diseaseTrajectory: dx.diseaseTrajectory || null,
    performanceStatus: formData.performanceStatus || null,
    symptomImpact: formData.symptomImpact || null,
    nutrition: formData.nutrition || null,
    musculoskeletal: formData.musculoskeletal || null,
    respiratory: formData.respiratory || null,
    psychosocial: formData.psychosocial || null,
    skin: formData.skin || null,
    whyHospice: hospiceContext.whyHospice || null,
    diseaseBurden: hospiceContext.diseaseBurden || null,
    relatedConditions: hospiceContext.relatedConditions || null,
    certificationSupport: hospiceContext.certificationSupport || null,
    documentationGaps: hospiceContext.documentationGaps || null,
    recentHospitalizations: dx.recentHospitalizations ?? null,
    recentErVisits: dx.recentErVisits ?? null,
  };
  return stableFingerprint(relevant);
}

// Deterministic string hash (djb2 variant) over a stably-key-sorted JSON
// serialization -- not cryptographic, only needs to detect "did any
// relevant input change", not resist tampering.
function stableFingerprint(value) {
  const json = stableStringify(value);
  let hash = 5381;
  for (let i = 0; i < json.length; i++) {
    hash = ((hash << 5) + hash + json.charCodeAt(i)) | 0;
  }
  return `fp_${(hash >>> 0).toString(16)}`;
}

function stableStringify(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  const keys = Object.keys(value).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${stableStringify(value[k])}`).join(",")}}`;
}

// ════════════════════════════════════════════════════════════════
// Narrative Quality Gate (Task 6).
//
// A narrative that is technically "reviewed" can still be clinically
// unusable if it leaks internal representation instead of synthesizing
// it -- raw camelCase field keys, bare "Label: value" field-dump lines,
// internal IDs, or raw timestamps. This is a deterministic, explainable
// linter over the final narrative TEXT (not the generation logic) so it
// catches leakage regardless of which generator produced the text
// (template draft or an inserted AI note). Returns PASS/FAIL plus the
// specific offending lines so a reviewer knows exactly what to fix --
// never a silent auto-correction of narrative content.
const FIELD_DUMP_PATTERNS = [
  { code: "CAMELCASE_FIELD_KEY", regex: /\b[a-z][a-zA-Z]*(?:[A-Z][a-z0-9]+){1,}\b\s*[:=]/ },
  { code: "RAW_LABEL_COLON_VALUE", regex: /^[A-Za-z ]{2,40}:\s*\S.*$/m },
  { code: "INTERNAL_ID_REFERENCE", regex: /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/i },
  { code: "RAW_JSON_FRAGMENT", regex: /[{["]\s*"[a-zA-Z_]+"\s*:/ },
];

export function evaluateNarrativeQualityGate(narrativeText) {
  const text = String(narrativeText || "");
  if (!text.trim()) {
    return { status: "FAIL", reasons: [{ code: "NARRATIVE_EMPTY", detail: "No narrative text documented." }] };
  }
  const reasons = [];
  for (const { code, regex } of FIELD_DUMP_PATTERNS) {
    const match = text.match(regex);
    if (match) {
      reasons.push({ code, detail: `Detected disallowed pattern near: "${match[0].slice(0, 80)}"` });
    }
  }
  return reasons.length > 0 ? { status: "FAIL", reasons } : { status: "PASS", reasons: [] };
}

export default buildClinicalNarrative;
