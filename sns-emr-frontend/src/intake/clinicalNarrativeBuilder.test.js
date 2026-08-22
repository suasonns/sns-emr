import { describe, it, expect } from "vitest";
import {
  DISEASE_TRAJECTORY_OPTIONS,
  LEGACY_DISEASE_TRAJECTORY_VALUES,
  isLegacyDiseaseTrajectoryValue,
  getDiseaseTrajectoryLabel,
  hasDocumentedValue,
  buildClinicalNarrative,
} from "./clinicalNarrativeBuilder";

describe("hasDocumentedValue", () => {
  it("treats empty string, null, and undefined as not documented", () => {
    expect(hasDocumentedValue("")).toBe(false);
    expect(hasDocumentedValue(null)).toBe(false);
    expect(hasDocumentedValue(undefined)).toBe(false);
  });

  it("treats numeric/string zero as documented", () => {
    expect(hasDocumentedValue(0)).toBe(true);
    expect(hasDocumentedValue("0")).toBe(true);
  });

  it("treats other populated values as documented", () => {
    expect(hasDocumentedValue("some text")).toBe(true);
    expect(hasDocumentedValue(false)).toBe(true);
  });
});

describe("buildClinicalNarrative — documented facts included", () => {
  it("includes PPS/KPS only when documented", () => {
    const formData = { performanceStatus: { pps: "40" } };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).toContain("PPS is documented as 40%");
    expect(result.text).not.toContain("KPS");
  });

  it("includes ADL dependence only from recorded ADL values", () => {
    const formData = {
      musculoskeletal: { adl: { bathing: "Dependent", dressing: "Dependent", toileting: "" } },
    };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).toContain("bathing (Dependent)");
    expect(result.text).toContain("dressing (Dependent)");
    expect(result.text).not.toContain("toileting");
  });

  it("includes hospitalization/ER utilization only when recorded", () => {
    const formData = { diagnoses: { recentHospitalizations: "2", recentErVisits: "1" } };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).toContain("2 recent hospitalization(s)");
    expect(result.text).toContain("1 recent emergency department visit(s)");
  });

  it("includes documented comorbidities", () => {
    const formData = { diagnoses: { hopeComorbidities: { copd: true, diabetesMellitus: false, other: true } } };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).toContain("Documented comorbidities: copd.");
    expect(result.text).not.toContain("diabetesMellitus");
    expect(result.text).not.toContain(", other");
  });
});

describe("buildClinicalNarrative — omission of undocumented topics", () => {
  it("returns an empty draft (no placeholder text) when nothing is documented", () => {
    const result = buildClinicalNarrative({}, {});
    expect(result.text).toBe("");
    expect(result.isEmpty).toBe(true);
  });

  it("omits sections entirely when their source fields are blank", () => {
    const formData = { performanceStatus: { pps: "40" } };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).not.toContain("Nutritional");
    expect(result.text).not.toContain("Infection history");
    expect(result.text).not.toContain("Integumentary");
  });
});

describe("buildClinicalNarrative — zero preservation", () => {
  it("preserves documented numeric zero for hospitalizations/ER visits", () => {
    const formData = { diagnoses: { recentHospitalizations: "0", recentErVisits: "0" } };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).toContain("0 recent hospitalization(s)");
    expect(result.text).toContain("0 recent emergency department visit(s)");
  });

  it("distinguishes blank utilization (not documented) from zero utilization (documented none)", () => {
    const blank = buildClinicalNarrative({ diagnoses: { recentHospitalizations: "", recentErVisits: "" } }, {});
    const zero = buildClinicalNarrative({ diagnoses: { recentHospitalizations: "0", recentErVisits: "0" } }, {});
    expect(blank.text).not.toContain("hospitalization");
    expect(zero.text).toContain("0 recent hospitalization(s)");
  });
});

describe("buildClinicalNarrative — no inference / no auto trajectory / no eligibility or prognosis", () => {
  it("never assigns disease trajectory when none is selected", () => {
    const formData = { performanceStatus: { pps: "20" }, diagnoses: {} };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).not.toContain("Disease trajectory");
    expect(result.text).not.toMatch(/rapid decline/i);
    expect(result.text).not.toMatch(/saw-toothed/i);
  });

  it("only restates a trajectory explicitly stored by the clinician", () => {
    const formData = { diagnoses: { diseaseTrajectory: "RAPID_DECLINE" } };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).toContain("Disease trajectory is documented as Rapid decline.");
  });

  it("never states hospice eligibility, LCD criteria, or a six-month prognosis", () => {
    const formData = {
      diagnoses: {
        primaryDiagnosis: { icd10: "C34.90", description: "Lung cancer" },
        hopeComorbidities: { cancer: true },
        lcdEligibilityNarrative: "Physician-authored LCD narrative text here.",
      },
      performanceStatus: { pps: "30" },
    };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).not.toMatch(/hospice eligible/i);
    expect(result.text).not.toMatch(/meets? lcd criteria/i);
    expect(result.text).not.toMatch(/six.month prognosis/i);
    expect(result.text).not.toMatch(/terminally ill/i);
    // Never reads/restates the separate physician LCD eligibility narrative.
    expect(result.text).not.toContain("Physician-authored LCD narrative text here.");
  });

  it("does not mutate formData or patient inputs", () => {
    const formData = { diagnoses: { diseaseTrajectory: "RAPID_DECLINE" }, performanceStatus: { pps: "40" } };
    const patient = { age: 80, sex: "female" };
    const formDataCopy = JSON.parse(JSON.stringify(formData));
    const patientCopy = JSON.parse(JSON.stringify(patient));
    buildClinicalNarrative(formData, patient);
    expect(formData).toEqual(formDataCopy);
    expect(patient).toEqual(patientCopy);
  });

  it("produces deterministic output for identical inputs", () => {
    const formData = {
      diagnoses: { diseaseTrajectory: "SLOW_STEADY_DECLINE", recentHospitalizations: "1" },
      performanceStatus: { pps: "50", kps: "50" },
    };
    const first = buildClinicalNarrative(formData, { age: 70 });
    const second = buildClinicalNarrative(formData, { age: 70 });
    expect(first).toEqual(second);
  });
});

describe("Disease Trajectory — stable keys and legacy values", () => {
  it("exposes stable value keys distinct from display labels", () => {
    expect(DISEASE_TRAJECTORY_OPTIONS.map((o) => o.value)).toEqual([
      "RAPID_DECLINE", "SAW_TOOTHED_DECLINE", "SLOW_STEADY_DECLINE", "OTHER_UNCERTAIN",
    ]);
  });

  it("recognizes legacy values without converting them", () => {
    LEGACY_DISEASE_TRAJECTORY_VALUES.forEach((legacyValue) => {
      expect(isLegacyDiseaseTrajectoryValue(legacyValue)).toBe(true);
      // Legacy values display verbatim — never silently remapped to a new option.
      expect(getDiseaseTrajectoryLabel(legacyValue)).toBe(legacyValue);
    });
  });

  it("does not treat a current stable-key value as legacy", () => {
    expect(isLegacyDiseaseTrajectoryValue("RAPID_DECLINE")).toBe(false);
  });

  it("resolves a stable-key value to its friendly label", () => {
    expect(getDiseaseTrajectoryLabel("SLOW_STEADY_DECLINE")).toBe("Slow, steady decline");
  });
});
