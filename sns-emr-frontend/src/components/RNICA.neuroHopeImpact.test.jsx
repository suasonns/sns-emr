import { describe, it, expect } from "vitest";
import {
  deriveSymptomImpactFromForm,
  computeNeurologicalDocumentationCoverage,
  computeBodySystemFindings,
  computeNeurologicalNarrative,
} from "./RNICA.jsx";

// PRODUCT OWNER CORRECTION (2026-10-21) "Neurological Layout and HOPE
// Anxiety/Agitation Impact" -- verifies the corrected HOPE J2051C
// (Anxiety) / J2051H (Agitation) derivation: real "Impact over past 2
// days" responses (anxietyImpact/agitationImpact), not the retired
// presence-only "0"/"1" read. See Section 16 Acceptance Tests 1-4, 6-7.

describe("deriveSymptomImpactFromForm -- Anxiety/Agitation HOPE impact", () => {
  it("reads 0 (not applicable/no impact) when the symptom is not selected at all, even if an impact value is stray-set", () => {
    const result = deriveSymptomImpactFromForm({
      neurological: { symptomsDemeanor: [], anxietyImpact: "Severe", agitationImpact: "Moderate" },
    });
    expect(result.anxiety).toBe("0");
    expect(result.agitation).toBe("0");
  });

  it("does NOT auto-assign code 1 when the symptom is selected but Impact has not been answered yet (Acceptance Test 1)", () => {
    const result = deriveSymptomImpactFromForm({
      neurological: { symptomsDemeanor: ["Anxiety", "Agitation"] },
    });
    expect(result.anxiety).toBe("");
    expect(result.agitation).toBe("");
  });

  it.each([
    ["Mild", "1"],
    ["Moderate", "2"],
    ["Severe", "3"],
  ])("maps Anxiety Impact %s to HOPE code %s", (impact, code) => {
    const result = deriveSymptomImpactFromForm({
      neurological: { symptomsDemeanor: ["Anxiety"], anxietyImpact: impact },
    });
    expect(result.anxiety).toBe(code);
  });

  it.each([
    ["Mild", "1"],
    ["Moderate", "2"],
    ["Severe", "3"],
  ])("maps Agitation Impact %s to HOPE code %s", (impact, code) => {
    const result = deriveSymptomImpactFromForm({
      neurological: { symptomsDemeanor: ["Agitation"], agitationImpact: impact },
    });
    expect(result.agitation).toBe(code);
  });

  it("derives Anxiety and Agitation independently (one selected/answered, the other untouched)", () => {
    const result = deriveSymptomImpactFromForm({
      neurological: { symptomsDemeanor: ["Anxiety"], anxietyImpact: "Moderate" },
    });
    expect(result.anxiety).toBe("2");
    expect(result.agitation).toBe("0");
  });
});

describe("Documentation Coverage -- Anxiety/Agitation Impact items are conditionally applicable", () => {
  it("does not show the Anxiety/Agitation Impact items at all when neither symptom is selected", () => {
    const coverage = computeNeurologicalDocumentationCoverage({ symptomsDemeanor: [] });
    const keys = coverage.map((item) => item.key);
    expect(keys).not.toContain("anxietyImpact");
    expect(keys).not.toContain("agitationImpact");
  });

  it("shows Anxiety Impact as incomplete with the correct unresolved hint once Anxiety is selected but Impact is blank", () => {
    const coverage = computeNeurologicalDocumentationCoverage({ symptomsDemeanor: ["Anxiety"] });
    const item = coverage.find((i) => i.key === "anxietyImpact");
    expect(item).toBeTruthy();
    expect(item.complete).toBe(false);
    expect(item.unresolvedHint).toMatch(/impact over the past 2 days/i);
  });

  it("shows Agitation Impact as complete once answered", () => {
    const coverage = computeNeurologicalDocumentationCoverage({
      symptomsDemeanor: ["Agitation"],
      agitationImpact: "Moderate",
    });
    const item = coverage.find((i) => i.key === "agitationImpact");
    expect(item).toBeTruthy();
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Moderate");
  });
});

describe("Clinical Findings / Narrative -- impact-aware Behavioral wording", () => {
  it("appends the Impact qualifier to the Clinical Findings Behavioral line once answered", () => {
    const findings = computeBodySystemFindings("neurological", {
      symptomsDemeanor: ["Anxiety"],
      anxietyImpact: "Moderate",
    });
    expect(findings.some((f) => f.includes("Anxiety (moderate impact)"))).toBe(true);
  });

  it("does not append an Impact qualifier when Impact is unanswered", () => {
    const findingsUnanswered = computeBodySystemFindings("neurological", { symptomsDemeanor: ["Anxiety"] });
    expect(findingsUnanswered.some((f) => f.includes("Anxiety ("))).toBe(false);
  });

  it("reflects the same impact-aware wording in the Clinical Story narrative", () => {
    const narrative = computeNeurologicalNarrative({
      symptomsDemeanor: ["Agitation"],
      agitationImpact: "Severe",
    });
    expect(narrative).toMatch(/Agitation \(severe impact\)/);
  });
});
