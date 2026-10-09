import { describe, it, expect } from "vitest";
import {
  computeSnsCognitiveScreen,
  computeNeurologicalCognitiveSummary,
  migrateNeurologicalCognitiveData,
} from "./RNICA.jsx";
import { RNICA_BODY_SYSTEM_SIDEBAR_ITEMS } from "../config/bodySystems.js";

// GitHub Directive (2026-10-04) "BIMS/HOPE compliance correction".
//
// Root cause under test: the Neuro "BIMS" card stored its three answers
// under `hopeItems.n0500/n0510/n0520` -- the OFFICIAL HOPE codes for
// Scheduled Opioid / PRN Opioid / Bowel Regimen (Section N medications;
// see docs/compliance/hope/HOPE_OFFICIAL_ITEM_INVENTORY_1.0.csv and
// hopeReportMapper.js:717-719) -- and two independent, duplicate score
// calculators read those same fields: one assumed a 0-9 scale, the other
// a CMS BIMS 0-15 scale, producing the reported "8/15 vs 8/9"
// inconsistency. This suite proves:
//   1. computeSnsCognitiveScreen is the single authoritative 0-9
//      calculation (no 0-15 assumption anywhere).
//   2. It never reports a score for an incomplete screen.
//   3. Its interpretation language is neutral/non-diagnostic (no clinical
//      bands like "Moderately Impaired").
//   4. computeNeurologicalCognitiveSummary delegates to it and reads
//      `cognitiveScreen`, not `hopeItems`.
//   5. The legacy-data migration is idempotent, non-destructive, and
//      never overwrites an RN's already-entered new-schema answers.
describe("computeSnsCognitiveScreen", () => {
  it("reports NOT_STARTED with no score when nothing is documented", () => {
    const result = computeSnsCognitiveScreen({});
    expect(result.completionStatus).toBe("NOT_STARTED");
    expect(result.rawScore).toBeNull();
    expect(result.maxScore).toBe(9);
    expect(result.missingItems).toEqual(["Word Repetition", "Word Recall", "Temporal Orientation"]);
  });

  it("reports PARTIAL with no score when only some items are answered", () => {
    const result = computeSnsCognitiveScreen({ repetition: "3", recall: "2" });
    expect(result.completionStatus).toBe("PARTIAL");
    expect(result.rawScore).toBeNull();
    expect(result.missingItems).toEqual(["Temporal Orientation"]);
  });

  it("sums to a real 0-9 maximum when COMPLETE, never a 0-15 scale", () => {
    const result = computeSnsCognitiveScreen({ repetition: "3", recall: "3", temporalOrientation: "3" });
    expect(result.completionStatus).toBe("COMPLETE");
    expect(result.rawScore).toBe(9);
    expect(result.maxScore).toBe(9);
  });

  it("computes the documented 8/9 case without ever producing 8/15", () => {
    const result = computeSnsCognitiveScreen({ repetition: "3", recall: "3", temporalOrientation: "2" });
    expect(result.rawScore).toBe(8);
    expect(result.maxScore).toBe(9);
  });

  it("uses neutral, non-diagnostic interpretation language only", () => {
    const low = computeSnsCognitiveScreen({ repetition: "0", recall: "0", temporalOrientation: "0" });
    expect(low.interpretation.source).toBe("SNS recommendation");
    expect(low.interpretation.label).not.toMatch(/impaired/i);
    expect(low.interpretation.detail).not.toMatch(/impaired/i);

    const high = computeSnsCognitiveScreen({ repetition: "3", recall: "3", temporalOrientation: "3" });
    expect(high.interpretation.label).toBe("Within expected range");
  });
});

describe("computeNeurologicalCognitiveSummary", () => {
  it("returns null when nothing has been documented", () => {
    expect(computeNeurologicalCognitiveSummary({})).toBeNull();
  });

  it("reads from cognitiveScreen, not hopeItems", () => {
    const summary = computeNeurologicalCognitiveSummary({
      cognitiveScreen: { repetition: "3", recall: "3", temporalOrientation: "3" },
      hopeItems: { n0500: "0", n0510: "0", n0520: "0" }, // legacy/unrelated -- must be ignored
    });
    expect(summary.screen.rawScore).toBe(9);
  });

  it("still surfaces behavioral/flag findings even with no cognitive screen data", () => {
    const summary = computeNeurologicalCognitiveSummary({ behavioralStatus: "No Current Concern", delirium: "Yes" });
    expect(summary.screen.completionStatus).toBe("NOT_STARTED");
    expect(summary.behavioralLine).toMatch(/no behavioral concern/i);
    expect(summary.flags).toContain("Delirium");
  });
});

describe("bodySystems.js Neurological sidebar HOPE declaration", () => {
  it("declares no HOPE codes for Neurological (N0500-N0520 belong to Medications, not Neuro)", () => {
    const neuro = RNICA_BODY_SYSTEM_SIDEBAR_ITEMS.find((s) => s.key === "neurological");
    expect(neuro).toBeDefined();
    expect(neuro.hope).toEqual([]);
  });
});

describe("migrateNeurologicalCognitiveData", () => {
  it("is a no-op when there is no legacy hopeItems data", () => {
    const merged = { neurological: { cognitiveScreen: { repetition: "", recall: "", temporalOrientation: "" } } };
    expect(migrateNeurologicalCognitiveData(merged)).toEqual(merged);
  });

  it("migrates valid legacy 0-3 values into cognitiveScreen", () => {
    const merged = {
      neurological: {
        cognitiveScreen: { repetition: "", recall: "", temporalOrientation: "" },
        hopeItems: { n0500: "3", n0510: "2", n0520: "1" },
      },
    };
    const result = migrateNeurologicalCognitiveData(merged);
    expect(result.neurological.cognitiveScreen.repetition).toBe("3");
    expect(result.neurological.cognitiveScreen.recall).toBe("2");
    expect(result.neurological.cognitiveScreen.temporalOrientation).toBe("1");
    // Legacy values are preserved, not deleted (non-destructive).
    expect(result.neurological.hopeItems).toEqual({ n0500: "3", n0510: "2", n0520: "1" });
  });

  it("never overwrites an already-entered new-schema answer", () => {
    const merged = {
      neurological: {
        cognitiveScreen: { repetition: "1", recall: "", temporalOrientation: "" },
        hopeItems: { n0500: "3", n0510: "2", n0520: "1" },
      },
    };
    expect(migrateNeurologicalCognitiveData(merged)).toEqual(merged);
  });

  it("is idempotent -- running it twice produces the same result", () => {
    const merged = {
      neurological: {
        cognitiveScreen: { repetition: "", recall: "", temporalOrientation: "" },
        hopeItems: { n0500: "3", n0510: "2", n0520: "1" },
      },
    };
    const once = migrateNeurologicalCognitiveData(merged);
    const twice = migrateNeurologicalCognitiveData(once);
    expect(twice).toEqual(once);
  });

  it("ignores out-of-range/blank legacy values", () => {
    const merged = {
      neurological: {
        cognitiveScreen: { repetition: "", recall: "", temporalOrientation: "" },
        hopeItems: { n0500: "", n0510: "", n0520: "" },
      },
    };
    expect(migrateNeurologicalCognitiveData(merged)).toEqual(merged);
  });
});
