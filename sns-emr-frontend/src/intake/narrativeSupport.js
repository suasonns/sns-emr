// ════════════════════════════════════════════════════════════════
// Narrative support utilities — Disease Trajectory constants, narrative
// context fingerprinting (staleness detection), and the Narrative
// Quality Gate.
//
// This module intentionally contains NO clinical-narrative composition
// logic. The single active narrative-composition engine is the backend
// RNICA V2 service (generate_rnica_narrative_v2() /
// preview_rnica_narrative_v2 in the backend), reached from the frontend
// only via previewRnicaNarrativeV2(). The legacy frontend deterministic
// template that used to live here (clinicalNarrativeBuilder.js /
// buildClinicalNarrative()) has been removed entirely — see the
// architecture map (docs/clinical/rnica-architecture-map.md), Section 13
// (Resolved Findings) and Section 16 (Discovery Log), "Legacy frontend
// narrative writer removed."
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

// ════════════════════════════════════════════════════════════════
// Narrative versioning / staleness detection.
//
// The narrative is a point-in-time synthesis of the reconciled clinical
// context (diagnosis, functional status, symptom burden, etc). If that
// context changes after the narrative was built/reviewed -- e.g. a
// diagnosis sync, a new HOPE score, an updated disease trajectory -- the
// existing narrative text is not automatically wrong, but it is
// unverified against the new facts and must not be presented as current
// without a fresh review. This computes a small, deterministic
// fingerprint of exactly the clinical inputs the RN reviews the
// narrative against, so a mismatch between the stored fingerprint
// (captured when the draft was last built/reviewed) and the
// fingerprint of the assessment's current live state is an honest,
// cheap, no-network signal that the reviewed narrative may now be
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
// Narrative Quality Gate.
//
// A narrative that is technically "reviewed" can still be clinically
// unusable if it leaks internal representation instead of synthesizing
// it -- raw camelCase field keys, bare "Label: value" field-dump lines,
// internal IDs, or raw timestamps. This is a deterministic, explainable
// linter over the final narrative TEXT (not the generation logic), so
// it catches leakage regardless of which generator produced the text.
// Since the RNICA V2 backend service is now the only narrative
// composition engine, this gate is what actually blocked the old
// legacy-writer field-dump text (e.g. "Documented anthropometrics:
// weight 145.505062lbs, BMI 24.2.") — the fix for that failure was
// removing the legacy writer, not weakening this gate. Returns
// PASS/FAIL plus the specific offending lines so a reviewer knows
// exactly what to fix -- never a silent auto-correction of narrative
// content.
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
