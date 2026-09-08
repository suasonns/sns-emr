import { describe, it, expect } from "vitest";
import {
  DISEASE_TRAJECTORY_OPTIONS,
  LEGACY_DISEASE_TRAJECTORY_VALUES,
  isLegacyDiseaseTrajectoryValue,
  getDiseaseTrajectoryLabel,
  computeNarrativeContextFingerprint,
  evaluateNarrativeQualityGate,
} from "./narrativeSupport";

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

describe("computeNarrativeContextFingerprint — staleness detection input", () => {
  it("is stable across repeated calls with identical inputs", () => {
    const formData = { diagnoses: { primaryDiagnosis: { description: "CHF" } } };
    const patient = { age: 76 };
    const hospiceContext = { currentDiagnosisDescription: "CHF" };
    const a = computeNarrativeContextFingerprint(formData, patient, hospiceContext);
    const b = computeNarrativeContextFingerprint(formData, patient, hospiceContext);
    expect(a).toBe(b);
  });

  it("is stable regardless of object key order", () => {
    const hospiceContextA = { currentDiagnosisDescription: "CHF", whyHospice: { selected_guideline: "X" } };
    const hospiceContextB = { whyHospice: { selected_guideline: "X" }, currentDiagnosisDescription: "CHF" };
    const a = computeNarrativeContextFingerprint({}, {}, hospiceContextA);
    const b = computeNarrativeContextFingerprint({}, {}, hospiceContextB);
    expect(a).toBe(b);
  });

  it("changes when the resolved primary diagnosis changes", () => {
    const before = computeNarrativeContextFingerprint({}, {}, { currentDiagnosisDescription: "ANEMIA DUE TO CKD STAGE 3A" });
    const after = computeNarrativeContextFingerprint({}, {}, { currentDiagnosisDescription: "SYSTOLIC HEART FAILURE, CHRONIC" });
    expect(before).not.toBe(after);
  });

  it("changes when documented functional status changes", () => {
    const before = computeNarrativeContextFingerprint({ performanceStatus: { pps: "40" } }, {}, {});
    const after = computeNarrativeContextFingerprint({ performanceStatus: { pps: "20" } }, {}, {});
    expect(before).not.toBe(after);
  });

  it("does not change when an irrelevant field (e.g. visit logistics) changes", () => {
    const before = computeNarrativeContextFingerprint({ visitMeta: { typeOfVisit: "In-Person" } }, {}, {});
    const after = computeNarrativeContextFingerprint({ visitMeta: { typeOfVisit: "Telephone" } }, {}, {});
    expect(before).toBe(after);
  });
});

describe("evaluateNarrativeQualityGate — field-dump / leakage detection", () => {
  it("PASSes clinically-synthesized free-flowing prose (the only kind the V2 engine produces)", () => {
    const prose = "Patient is a 76-year-old female admitted to hospice with a terminal diagnosis of " +
      "systolic heart failure, chronic. She is at PPS 40%, meaning she requires considerable assistance " +
      "and frequent medical care, reflecting significant functional decline consistent with continued " +
      "hospice appropriateness.";
    const gate = evaluateNarrativeQualityGate(prose);
    expect(gate.status).toBe("PASS");
    expect(gate.reasons).toEqual([]);
  });

  it("FAILs an empty narrative", () => {
    expect(evaluateNarrativeQualityGate("").status).toBe("FAIL");
    expect(evaluateNarrativeQualityGate("   ").status).toBe("FAIL");
  });

  it("FAILs raw camelCase field-key leakage", () => {
    const gate = evaluateNarrativeQualityGate("neurologicalAffectedSide: Left");
    expect(gate.status).toBe("FAIL");
    expect(gate.reasons.some((r) => r.code === "CAMELCASE_FIELD_KEY")).toBe(true);
  });

  it("FAILs a raw label/value field-dump line, including raw anthropometric abstraction", () => {
    const gate = evaluateNarrativeQualityGate("Primary Diagnosis Description: ANEMIA DUE TO CKD STAGE 3A");
    expect(gate.status).toBe("FAIL");

    const anthro = evaluateNarrativeQualityGate("Documented anthropometrics: weight 145.505062lbs, BMI 24.2.");
    expect(anthro.status).toBe("FAIL");
  });

  it("FAILs an embedded internal record identifier (UUID)", () => {
    const gate = evaluateNarrativeQualityGate(
      "Patient reports improvement. source_record_id 3ea2f6fa-8dd9-4e3c-9b7d-009ddbe17ab0 was referenced."
    );
    expect(gate.status).toBe("FAIL");
    expect(gate.reasons.some((r) => r.code === "INTERNAL_ID_REFERENCE")).toBe(true);
  });
});
