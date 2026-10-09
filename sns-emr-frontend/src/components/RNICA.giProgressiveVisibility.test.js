import { describe, it, expect } from "vitest";
import { computeGiOverviewCardGate, giOverviewForcesFullExam } from "./RNICA.jsx";

// OWNER DIRECTIVE (2026-10-30) "GI Progressive Visibility Defect B Fix" --
// proves `gastrointestinalOverview` now actually gates GI card visibility
// (previously it was read only by the structured-findings summary
// computation and never affected rendering at all -- the 3 Overview pills
// rendered an identical layout). `computeGiOverviewCardGate` and
// `giOverviewForcesFullExam` are called directly by the real card-filter
// render code (not a parallel reimplementation), so a passing unit test
// is proof of the real component's behavior, not a simulation. Full
// DOM-level verification (zero reserved layout height for hidden cards,
// annotated screenshots per state) is additionally confirmed by the
// required manual browser UAT using synthetic data.

describe("computeGiOverviewCardGate -- GI Overview and Notes are always visible", () => {
  it("never gates the GI Overview card itself, regardless of its own value", () => {
    expect(computeGiOverviewCardGate("GI Overview", { gastrointestinalOverview: "No Current GI Concern" })).toBe("pass-through");
    expect(computeGiOverviewCardGate("GI Overview", {})).toBe("pass-through");
  });

  it("never gates the Notes card", () => {
    expect(computeGiOverviewCardGate("Notes", { gastrointestinalOverview: "No Current GI Concern" })).toBe("pass-through");
  });
});

describe("computeGiOverviewCardGate -- No Current GI Concern (state 1)", () => {
  const overview = "No Current GI Concern";

  it("hides GI Symptoms when no GI data has ever been documented", () => {
    expect(computeGiOverviewCardGate("GI Symptoms", { gastrointestinalOverview: overview })).toBe("hide");
  });

  it("hides Abdominal / Bowel Assessment when no GI data has ever been documented", () => {
    expect(computeGiOverviewCardGate("Abdominal / Bowel Assessment", { gastrointestinalOverview: overview })).toBe("hide");
  });

  it("hides Feeding Devices when no GI data has ever been documented", () => {
    expect(computeGiOverviewCardGate("Feeding Devices", { gastrointestinalOverview: overview })).toBe("hide");
  });

  it("hides the Constipation auto-suggest helper card", () => {
    expect(computeGiOverviewCardGate("Constipation — Auto-Suggested from Last BM Date", { gastrointestinalOverview: overview })).toBe("hide");
  });

  it("hides Clinical Status Change unconditionally (a conclusion about findings, not data to preserve)", () => {
    expect(computeGiOverviewCardGate("Clinical Status Change", {
      gastrointestinalOverview: overview,
      clinicalStatusChange: "Improved",
    })).toBe("hide");
  });

  it("falls through to a preserved-findings banner (never silently disappears) when GI Symptoms already has documented data", () => {
    const data = { gastrointestinalOverview: overview, constipation: "Moderate" };
    expect(computeGiOverviewCardGate("GI Symptoms", data)).toBe("banner");
  });

  it("falls through to a preserved-findings banner when Abdominal / Bowel Assessment already has documented data", () => {
    const data = { gastrointestinalOverview: overview, bowelSounds: "Hypoactive" };
    expect(computeGiOverviewCardGate("Abdominal / Bowel Assessment", data)).toBe("banner");
  });

  it("falls through to a preserved-findings banner when Feeding Devices already has documented data", () => {
    const data = { gastrointestinalOverview: overview, feedingTube: { present: "Yes" } };
    expect(computeGiOverviewCardGate("Feeding Devices", data)).toBe("banner");
  });
});

describe("computeGiOverviewCardGate -- Existing GI Findings Review (state 2)", () => {
  const overview = "Existing GI Findings Review";

  it("passes through GI Symptoms (full review of current severities)", () => {
    expect(computeGiOverviewCardGate("GI Symptoms", { gastrointestinalOverview: overview })).toBe("pass-through");
  });

  it("passes through Clinical Status Change", () => {
    expect(computeGiOverviewCardGate("Clinical Status Change", { gastrointestinalOverview: overview })).toBe("pass-through");
  });

  it("passes through Abdominal / Bowel Assessment (its own existing data/manual-toggle gate still applies downstream)", () => {
    expect(computeGiOverviewCardGate("Abdominal / Bowel Assessment", { gastrointestinalOverview: overview })).toBe("pass-through");
  });
});

describe("computeGiOverviewCardGate -- New or Worsening GI Findings (state 3)", () => {
  const overview = "New or Worsening GI Findings";

  it("passes through every hideable card (nothing is gated -- full documentation required)", () => {
    expect(computeGiOverviewCardGate("GI Symptoms", { gastrointestinalOverview: overview })).toBe("pass-through");
    expect(computeGiOverviewCardGate("Abdominal / Bowel Assessment", { gastrointestinalOverview: overview })).toBe("pass-through");
    expect(computeGiOverviewCardGate("Feeding Devices", { gastrointestinalOverview: overview })).toBe("pass-through");
    expect(computeGiOverviewCardGate("Clinical Status Change", { gastrointestinalOverview: overview })).toBe("pass-through");
  });
});

describe("computeGiOverviewCardGate -- no Overview selected yet (legacy/unanswered records)", () => {
  it("passes every card through unchanged when gastrointestinalOverview is unset (backward compatible with records predating this field)", () => {
    expect(computeGiOverviewCardGate("GI Symptoms", {})).toBe("pass-through");
    expect(computeGiOverviewCardGate("Abdominal / Bowel Assessment", {})).toBe("pass-through");
    expect(computeGiOverviewCardGate("Feeding Devices", {})).toBe("pass-through");
    expect(computeGiOverviewCardGate("Clinical Status Change", {})).toBe("pass-through");
  });
});

describe("giOverviewForcesFullExam -- forces the complete Abdominal/Bowel exam open on New or Worsening", () => {
  it("is true only for New or Worsening GI Findings", () => {
    expect(giOverviewForcesFullExam({ gastrointestinalOverview: "New or Worsening GI Findings" })).toBe(true);
    expect(giOverviewForcesFullExam({ gastrointestinalOverview: "Existing GI Findings Review" })).toBe(false);
    expect(giOverviewForcesFullExam({ gastrointestinalOverview: "No Current GI Concern" })).toBe(false);
    expect(giOverviewForcesFullExam({})).toBe(false);
  });
});
