import { describe, it, expect } from "vitest";
import {
  INFECTION_CLINICAL_STATUS_CHANGE_OPTIONS,
  INFECTION_CLINICAL_STATUS_CODES,
  INFECTION_RETIRED_CLINICAL_STATUS_VALUES,
  isRetiredInfectionClinicalStatusValue,
  validateInfectionClinicalStatusSelection,
} from "./RNICA.jsx";

// OWNER DIRECTIVE (2026-10-21) "Infection Language Standard" items 13-15 --
// exercises the Infection-specific Clinical Status Change option list
// (item 13), the shared supporting-findings gating validator (item 14),
// and legacy-value classification (item 15), all against synthetic data.

describe("Infection Language Standard item 13 -- option list", () => {
  it("exposes exactly five options, no sixth", () => {
    expect(INFECTION_CLINICAL_STATUS_CHANGE_OPTIONS).toHaveLength(5);
  });

  it("matches the owner-approved exact wording", () => {
    expect(INFECTION_CLINICAL_STATUS_CHANGE_OPTIONS).toEqual([
      "Infection-Related Findings Reduced Since Prior Assessment",
      "Current Infection-Related Interventions Appear Effective",
      "Infection-Related Decline Observed Since Prior Assessment",
      "New Infection-Related Finding Since Prior Assessment",
      "Not Applicable",
    ]);
  });

  it("never includes a retired term", () => {
    for (const retired of INFECTION_RETIRED_CLINICAL_STATUS_VALUES) {
      expect(INFECTION_CLINICAL_STATUS_CHANGE_OPTIONS).not.toContain(retired);
    }
  });

  it("pairs every option with a stable machine-readable code", () => {
    for (const label of INFECTION_CLINICAL_STATUS_CHANGE_OPTIONS) {
      expect(typeof INFECTION_CLINICAL_STATUS_CODES[label]).toBe("string");
    }
    expect(INFECTION_CLINICAL_STATUS_CODES["Not Applicable"]).toBe("not_applicable");
  });
});

describe("Infection Language Standard item 15 -- legacy value classification", () => {
  it("classifies every retired term as a legacy value (case-insensitive)", () => {
    expect(isRetiredInfectionClinicalStatusValue("Stable / No Change")).toBe(true);
    expect(isRetiredInfectionClinicalStatusValue("stable / no change")).toBe(true);
    expect(isRetiredInfectionClinicalStatusValue("UNABLE TO ASSESS")).toBe(true);
  });

  it("does not classify a current approved option as legacy", () => {
    for (const label of INFECTION_CLINICAL_STATUS_CHANGE_OPTIONS) {
      expect(isRetiredInfectionClinicalStatusValue(label)).toBe(false);
    }
  });

  it("does not classify an empty value as legacy", () => {
    expect(isRetiredInfectionClinicalStatusValue("")).toBe(false);
    expect(isRetiredInfectionClinicalStatusValue(undefined)).toBe(false);
  });
});

describe("Infection Language Standard item 14 -- supporting-findings gating", () => {
  it("'Not Applicable' is always valid, even with no prior assessment and no data", () => {
    const result = validateInfectionClinicalStatusSelection("Not Applicable", {}, {});
    expect(result.valid).toBe(true);
    expect(result.code).toBe("not_applicable");
  });

  it("rejects an unrecognized/retired value outright", () => {
    const result = validateInfectionClinicalStatusSelection("Stable / No Change", {}, { hasPriorInfectionAssessment: true });
    expect(result.valid).toBe(false);
    expect(result.code).toBeNull();
  });

  describe("SOC/initial-assessment special-casing (no prior assessment)", () => {
    it("blocks 'Findings Reduced' when no prior Infection assessment exists", () => {
      const result = validateInfectionClinicalStatusSelection(
        "Infection-Related Findings Reduced Since Prior Assessment",
        { antibioticTreatmentEffective: "Improving" },
        { hasPriorInfectionAssessment: false },
      );
      expect(result.valid).toBe(false);
      expect(result.message).toMatch(/prior Infection assessment/i);
    });

    it("blocks 'New Finding' when no prior Infection assessment exists, even with an active infection documented", () => {
      const result = validateInfectionClinicalStatusSelection(
        "New Infection-Related Finding Since Prior Assessment",
        { currentInfections: ["UTI"] },
        { hasPriorInfectionAssessment: false },
      );
      expect(result.valid).toBe(false);
    });
  });

  describe("Infection-Related Findings Reduced Since Prior Assessment", () => {
    it("is invalid without a documented improving response", () => {
      const result = validateInfectionClinicalStatusSelection(
        "Infection-Related Findings Reduced Since Prior Assessment",
        {},
        { hasPriorInfectionAssessment: true },
      );
      expect(result.valid).toBe(false);
      expect(result.supportingFieldIds).toContain("antibioticTreatmentEffective");
    });

    it("is valid with a documented 'Improving' treatment response and a prior assessment", () => {
      const result = validateInfectionClinicalStatusSelection(
        "Infection-Related Findings Reduced Since Prior Assessment",
        { antibioticTreatmentEffective: "Improving" },
        { hasPriorInfectionAssessment: true },
      );
      expect(result.valid).toBe(true);
    });
  });

  describe("Current Infection-Related Interventions Appear Effective", () => {
    it("is invalid when an intervention is documented but no effectiveness response is recorded", () => {
      const result = validateInfectionClinicalStatusSelection(
        "Current Infection-Related Interventions Appear Effective",
        { antibioticTherapyStatus: "Currently receiving antibiotics" },
        { hasPriorInfectionAssessment: true },
      );
      expect(result.valid).toBe(false);
    });

    it("is valid with an active intervention and a documented 'Improving' response", () => {
      const result = validateInfectionClinicalStatusSelection(
        "Current Infection-Related Interventions Appear Effective",
        { antibioticTherapyStatus: "Currently receiving antibiotics", antibioticTreatmentEffective: "Improving" },
        { hasPriorInfectionAssessment: true },
      );
      expect(result.valid).toBe(true);
    });
  });

  describe("Infection-Related Decline Observed Since Prior Assessment", () => {
    it("is invalid with no current infection-related finding at all", () => {
      const result = validateInfectionClinicalStatusSelection(
        "Infection-Related Decline Observed Since Prior Assessment",
        {},
        { hasPriorInfectionAssessment: true },
      );
      expect(result.valid).toBe(false);
    });

    it("is valid with a documented 'Worsening' treatment response", () => {
      const result = validateInfectionClinicalStatusSelection(
        "Infection-Related Decline Observed Since Prior Assessment",
        { antibioticTreatmentEffective: "Worsening" },
        { hasPriorInfectionAssessment: true },
      );
      expect(result.valid).toBe(true);
    });

    it("is valid with a current resistant organism documented", () => {
      const result = validateInfectionClinicalStatusSelection(
        "Infection-Related Decline Observed Since Prior Assessment",
        { antibioticResistantInfection: ["MRSA"] },
        { hasPriorInfectionAssessment: true },
      );
      expect(result.valid).toBe(true);
    });
  });

  describe("New Infection-Related Finding Since Prior Assessment", () => {
    it("is invalid without a current active infection documented", () => {
      const result = validateInfectionClinicalStatusSelection(
        "New Infection-Related Finding Since Prior Assessment",
        {},
        { hasPriorInfectionAssessment: true },
      );
      expect(result.valid).toBe(false);
    });

    it("is valid with a current active infection and a prior assessment", () => {
      const result = validateInfectionClinicalStatusSelection(
        "New Infection-Related Finding Since Prior Assessment",
        { currentInfections: ["UTI"] },
        { hasPriorInfectionAssessment: true },
      );
      expect(result.valid).toBe(true);
    });
  });

  it("never fabricates a comparisonAssessmentId/comparisonDate -- passes through context only", () => {
    const result = validateInfectionClinicalStatusSelection("Not Applicable", {}, {});
    expect(result.comparisonAssessmentId).toBeNull();
    expect(result.comparisonDate).toBeNull();
    const result2 = validateInfectionClinicalStatusSelection("Not Applicable", {}, { comparisonAssessmentId: "abc", comparisonDate: "2026-10-01" });
    expect(result2.comparisonAssessmentId).toBe("abc");
    expect(result2.comparisonDate).toBe("2026-10-01");
  });
});
