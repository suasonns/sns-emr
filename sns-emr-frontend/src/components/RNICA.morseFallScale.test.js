import { describe, it, expect } from "vitest";
import {
  computeMorseFallScore,
  isFallRiskMorseComplete,
  computeFallRiskTrend,
  computeSafetyDocumentationCoverage,
} from "./RNICA.jsx";

// PRODUCT OWNER DECISION (2026-11-29) "Fall Risk Assessment -- Morse Fall
// Scale" (final) -- proves the published Morse Fall Scale point values
// and classification thresholds are reproduced exactly (no invented
// alternate point values), that an unanswered factor never silently
// scores as zero, and that trend is computed only from this chart's own
// completed-assessment history.

const COMPLETE_LOW = {
  fallRiskMorseHistoryOfFalling: "No",
  fallRiskMorseSecondaryDiagnosis: "No",
  fallRiskMorseAmbulatoryAid: "None/Bed Rest/Nurse Assist",
  fallRiskMorseIvHeparinLock: "No",
  fallRiskMorseGaitTransferring: "Normal/Bedrest/Immobile",
  fallRiskMorseMentalStatus: "Oriented to Own Ability",
};

const COMPLETE_HIGH = {
  fallRiskMorseHistoryOfFalling: "Yes", // 25
  fallRiskMorseSecondaryDiagnosis: "Yes", // 15
  fallRiskMorseAmbulatoryAid: "Furniture", // 30
  fallRiskMorseIvHeparinLock: "Yes", // 20
  fallRiskMorseGaitTransferring: "Impaired", // 20
  fallRiskMorseMentalStatus: "Overestimates/Forgets Limitations", // 15
}; // total 125

describe("computeMorseFallScore", () => {
  it("is incomplete when any factor is unanswered (never scores it as zero)", () => {
    const result = computeMorseFallScore({ ...COMPLETE_LOW, fallRiskMorseMentalStatus: "" });
    expect(result.complete).toBe(false);
    expect(result.total).toBeNull();
    expect(result.classification).toBe("");
  });

  it("scores all-zero factors as 0 / Low Risk when every factor is explicitly answered", () => {
    const result = computeMorseFallScore(COMPLETE_LOW);
    expect(result.complete).toBe(true);
    expect(result.total).toBe(0);
    expect(result.classification).toBe("Low Risk");
  });

  it("computes the maximum score (125) and High Risk from the published point values", () => {
    const result = computeMorseFallScore(COMPLETE_HIGH);
    expect(result.complete).toBe(true);
    expect(result.total).toBe(125);
    expect(result.classification).toBe("High Risk");
  });

  it("classifies boundary totals correctly (0-24 Low, 25-44 Moderate, >=45 High)", () => {
    // 0 -> Low
    expect(computeMorseFallScore(COMPLETE_LOW).classification).toBe("Low Risk");
    // 25 (History of Falling only) -> Moderate
    const at25 = { ...COMPLETE_LOW, fallRiskMorseHistoryOfFalling: "Yes" };
    expect(computeMorseFallScore(at25).total).toBe(25);
    expect(computeMorseFallScore(at25).classification).toBe("Moderate Risk");
    // 40 (History 25 + Secondary Diagnosis 15) -> Moderate
    const at40 = { ...COMPLETE_LOW, fallRiskMorseHistoryOfFalling: "Yes", fallRiskMorseSecondaryDiagnosis: "Yes" };
    expect(computeMorseFallScore(at40).total).toBe(40);
    expect(computeMorseFallScore(at40).classification).toBe("Moderate Risk");
    // 45 (History 25 + Secondary 15 + IV lock... 25+15=40, +20 IV = 60; use 25+20=45) -> High
    const at45 = { ...COMPLETE_LOW, fallRiskMorseHistoryOfFalling: "Yes", fallRiskMorseIvHeparinLock: "Yes" };
    expect(computeMorseFallScore(at45).total).toBe(45);
    expect(computeMorseFallScore(at45).classification).toBe("High Risk");
  });
});

describe("isFallRiskMorseComplete", () => {
  it("is false for an empty/new record", () => {
    expect(isFallRiskMorseComplete({})).toBe(false);
  });
  it("is true only once all 6 factors are answered", () => {
    expect(isFallRiskMorseComplete(COMPLETE_LOW)).toBe(true);
  });
});

describe("computeFallRiskTrend", () => {
  it("returns no trend when fewer than two completed assessments exist", () => {
    expect(computeFallRiskTrend([]).trend).toBe("");
    expect(computeFallRiskTrend([{ totalScore: 10, classification: "Low Risk" }]).trend).toBe("");
  });
  it("reports Worsening when the score increases", () => {
    const trend = computeFallRiskTrend([
      { totalScore: 10, classification: "Low Risk" },
      { totalScore: 55, classification: "High Risk" },
    ]);
    expect(trend.trend).toBe("Worsening");
    expect(trend.change).toBe(45);
  });
  it("reports Improving when the score decreases", () => {
    const trend = computeFallRiskTrend([
      { totalScore: 55, classification: "High Risk" },
      { totalScore: 35, classification: "Moderate Risk" },
    ]);
    expect(trend.trend).toBe("Improving");
    expect(trend.change).toBe(-20);
  });
  it("reports Stable when the score is unchanged", () => {
    const trend = computeFallRiskTrend([
      { totalScore: 30, classification: "Moderate Risk" },
      { totalScore: 30, classification: "Moderate Risk" },
    ]);
    expect(trend.trend).toBe("Stable");
    expect(trend.change).toBe(0);
  });
});

describe("computeSafetyDocumentationCoverage -- Fall Risk (Morse Fall Scale)", () => {
  it("is unresolved until the Morse Fall Scale is completed", () => {
    const item = computeSafetyDocumentationCoverage({}).find((i) => i.key === "fallRisk");
    expect(item.complete).toBe(false);
    expect(item.unresolvedHint).toBe("Complete the Morse Fall Scale (all 6 factors)");
  });
  it("is complete and summarizes the score/classification once Morse is completed", () => {
    const item = computeSafetyDocumentationCoverage(COMPLETE_HIGH).find((i) => i.key === "fallRisk");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Score 125 · High Risk");
  });
});
