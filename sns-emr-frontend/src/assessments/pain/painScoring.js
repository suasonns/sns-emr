// Shared pain-score interpretation logic used by every documentation type
// (RN/LVN Initial Comprehensive, PRN, Routine, Change of Condition, GIP, etc.)
// so a pain score is ALWAYS paired with its plain-language description,
// no matter which chart/note the nurse is completing.

export const PAIN_TOOL_LABELS = {
  numeric: "Numeric (0-10)",
  painad: "PAINAD",
  flacc: "FLACC",
};

function bandLabel(total, labels) {
  if (total === null || total === undefined || total === "") return null;
  const t = Number(total);
  if (Number.isNaN(t)) return null;
  if (t === 0) return labels.none;
  if (t <= 3) return labels.mild;
  if (t <= 6) return labels.moderate;
  return labels.severe;
}

// Numeric Pain Rating Scale — patient self-report 0-10
export function getNumericInterpretation(score) {
  const label = bandLabel(score, {
    none: "No Pain", mild: "Mild Pain", moderate: "Moderate Pain", severe: "Severe Pain",
  });
  if (!label) return null;
  const color = score === 0 ? "#059669" : score <= 3 ? "#84cc16" : score <= 6 ? "#f59e0b" : "#ef4444";
  return { label, color };
}

// PAINAD — observed, non-verbal/dementia patients
export function getPainadInterpretation(total) {
  const label = bandLabel(total, {
    none: "No Pain", mild: "Mild Pain", moderate: "Moderate Pain", severe: "Severe Pain",
  });
  if (!label) return null;
  const t = Number(total);
  const color = t === 0 ? "#059669" : t <= 3 ? "#84cc16" : t <= 6 ? "#f59e0b" : "#ef4444";
  return { label, color };
}

// FLACC — observed, pediatric/non-verbal patients
export function getFlaccInterpretation(total) {
  const label = bandLabel(total, {
    none: "Relaxed / Comfortable", mild: "Mild Discomfort", moderate: "Moderate Pain", severe: "Severe Pain",
  });
  if (!label) return null;
  const t = Number(total);
  const color = t === 0 ? "#059669" : t <= 3 ? "#84cc16" : t <= 6 ? "#f59e0b" : "#ef4444";
  return { label, color };
}

// tool: "numeric" | "painad" | "flacc"
export function getPainInterpretation(tool, score) {
  if (tool === "painad") return getPainadInterpretation(score);
  if (tool === "flacc") return getFlaccInterpretation(score);
  return getNumericInterpretation(score);
}

// One-line summary safe to drop into any narrative/note text area, e.g.
// "Pain Score: 6/10 (Moderate Pain) — PAINAD"
export function getPainScoreSummary(tool, score) {
  if (score === null || score === undefined || score === "") return null;
  const interp = getPainInterpretation(tool, score);
  if (!interp) return null;
  return `Pain Score: ${score}/10 (${interp.label}) — ${PAIN_TOOL_LABELS[tool] || "Numeric (0-10)"}`;
}
