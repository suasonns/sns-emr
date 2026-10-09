import { describe, expect, it } from "vitest";

import {
  getScaleInterpretation,
  PPS_INTERPRETATIONS,
  KPS_INTERPRETATIONS,
  ECOG_INTERPRETATIONS,
  FAST_INTERPRETATIONS,
  NYHA_INTERPRETATIONS,
} from "./performanceScaleInterpretations";

// These mirror the exact option values defined in RNICA.jsx's
// `performanceStatus` section field schema (pps/kps/ecog/fast/nyha). If the
// schema ever adds/removes a score option, this list -- and the
// corresponding interpretation table -- must be kept in sync, otherwise a
// documented score would silently show no interpretation.
const PPS_VALUES = ["100%", "90%", "80%", "70%", "60%", "50%", "40%", "30%", "20%", "10%", "0%"];
const KPS_VALUES = ["100", "90", "80", "70", "60", "50", "40", "30", "20", "10", "0"];
const ECOG_VALUES = ["0", "1", "2", "3", "4", "5"];
const FAST_VALUES = ["1", "2", "3", "4", "5", "6a", "6b", "6c", "6d", "6e", "7a", "7b", "7c", "7d", "7e", "7f"];
const NYHA_VALUES = ["I", "II", "III", "IV"];

function expectCompleteCoverage(table, values) {
  values.forEach((value) => {
    const entry = table[value];
    expect(entry, `missing interpretation for score "${value}"`).toBeTruthy();
    expect(typeof entry.interpretation).toBe("string");
    expect(entry.interpretation.length).toBeGreaterThan(0);
    expect(typeof entry.significance).toBe("string");
    expect(entry.significance.length).toBeGreaterThan(0);
  });
}

describe("performanceScaleInterpretations", () => {
  it("covers every PPS score option", () => {
    expectCompleteCoverage(PPS_INTERPRETATIONS, PPS_VALUES);
  });

  it("covers every KPS score option", () => {
    expectCompleteCoverage(KPS_INTERPRETATIONS, KPS_VALUES);
  });

  it("covers every ECOG score option", () => {
    expectCompleteCoverage(ECOG_INTERPRETATIONS, ECOG_VALUES);
  });

  it("covers every FAST stage option", () => {
    expectCompleteCoverage(FAST_INTERPRETATIONS, FAST_VALUES);
  });

  it("covers every NYHA class option", () => {
    expectCompleteCoverage(NYHA_INTERPRETATIONS, NYHA_VALUES);
  });

  describe("getScaleInterpretation", () => {
    it("matches the user-provided PPS 20% example", () => {
      const result = getScaleInterpretation("pps", "20%");
      expect(result.interpretation).toBe("Totally bedbound.");
      expect(result.significance).toMatch(/Unable to perform work activities/);
    });

    it("returns null when no score is documented yet", () => {
      expect(getScaleInterpretation("pps", undefined)).toBeNull();
      expect(getScaleInterpretation("pps", "")).toBeNull();
      expect(getScaleInterpretation("pps", null)).toBeNull();
    });

    it("returns null for an unknown scale key", () => {
      expect(getScaleInterpretation("not-a-scale", "100%")).toBeNull();
    });

    it("returns null for a value with no matching table entry", () => {
      expect(getScaleInterpretation("nyha", "V")).toBeNull();
    });

    it("resolves ECOG and NYHA scores correctly", () => {
      expect(getScaleInterpretation("ecog", "4").interpretation).toBe("Completely disabled.");
      expect(getScaleInterpretation("nyha", "IV").interpretation).toMatch(/Severe limitation/);
    });
  });
});
