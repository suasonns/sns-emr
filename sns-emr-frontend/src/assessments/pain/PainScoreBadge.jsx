import React from "react";
import { getPainInterpretation, PAIN_TOOL_LABELS } from "./painScoring";

/**
 * PainScoreBadge — compact, reusable "Score + description" chip.
 * Drop this into ANY nursing note/documentation type (Initial Comprehensive,
 * PRN, Routine, Change of Condition, GIP, etc.) so a pain score is never
 * shown as a bare number — it always carries its clinical interpretation.
 *
 * tool: "numeric" | "painad" | "flacc"
 */
const PainScoreBadge = ({ tool = "numeric", score, size = "md", style: extra }) => {
  const interp = getPainInterpretation(tool, score);
  if (!interp || score === null || score === undefined || score === "") return null;

  const fontSize = size === "sm" ? 11 : 12.5;
  const padding = size === "sm" ? "3px 8px" : "4px 12px";

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding,
        borderRadius: 999,
        background: `${interp.color}20`,
        border: `1px solid ${interp.color}`,
        color: interp.color,
        fontSize,
        fontWeight: 700,
        whiteSpace: "nowrap",
        ...extra,
      }}
    >
      {PAIN_TOOL_LABELS[tool] || "Numeric"}: {score}/10 — {interp.label}
    </span>
  );
};

export default PainScoreBadge;
