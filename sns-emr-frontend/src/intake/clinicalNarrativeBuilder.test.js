import { describe, it, expect } from "vitest";
import {
  DISEASE_TRAJECTORY_OPTIONS,
  LEGACY_DISEASE_TRAJECTORY_VALUES,
  isLegacyDiseaseTrajectoryValue,
  getDiseaseTrajectoryLabel,
  hasDocumentedValue,
  buildClinicalNarrative,
  computeNarrativeContextFingerprint,
  evaluateNarrativeQualityGate,
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

  it("includes ADL dependence only from recorded ADL values, rendered as human-readable labels (not raw 0-5 codes)", () => {
    // RNICA.jsx's ADL fields store the literal 0-5 dependence-scale code,
    // never a word like "Dependent" — real stored values look like "5"/"3".
    const formData = {
      musculoskeletal: { adl: { bathing: "5", dressing: "3", toileting: "" } },
    };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).toContain("bathing (Total dependence)");
    expect(result.text).toContain("dressing (Limited assistance)");
    expect(result.text).not.toContain("toileting");
    expect(result.text).not.toContain("bathing (5)");
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

  it("restates HOPE J0050 imminent-death charting using its literal CMS response code (\"1\"), not a \"Yes\" string", () => {
    // RNICA.jsx's imminentDeath.appearsThreeDaysOrLess radio field stores
    // the literal CMS J0050 response code ("0"/"1"/"9"), never "Yes"/"No".
    const formData = { imminentDeath: { appearsThreeDaysOrLess: "1", indicators: [] } };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).toContain("within three days or less of death");
  });

  it("does not restate J0050 imminent-death charting when documented as \"0\" (No) or \"9\" (Unable to determine)", () => {
    const noResult = buildClinicalNarrative({ imminentDeath: { appearsThreeDaysOrLess: "0", indicators: [] } }, {});
    expect(noResult.text).not.toContain("within three days or less of death");

    const unableResult = buildClinicalNarrative({ imminentDeath: { appearsThreeDaysOrLess: "9", indicators: [] } }, {});
    expect(unableResult.text).not.toContain("within three days or less of death");
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

describe("buildClinicalNarrative — hospiceContext (structured hospice reasoning, not a field dump)", () => {
  it("uses the chart's current diagnosis over a stale draft snapshot and flags the mismatch", () => {
    const formData = { diagnoses: { primaryDiagnosis: { description: "ANEMIA DUE TO CKD STAGE 3A" } } };
    const hospiceContext = {
      currentDiagnosisDescription: "SYSTOLIC HEART FAILURE, CHRONIC",
      diagnosisMismatch: true,
    };
    const result = buildClinicalNarrative(formData, {}, hospiceContext);
    expect(result.text).toContain("HOSPICE CLINICAL PICTURE");
    expect(result.text).toContain("Current chart diagnosis is documented as SYSTOLIC HEART FAILURE, CHRONIC");
    expect(result.text).toContain("ANEMIA DUE TO CKD STAGE 3A");
    expect(result.text).toContain("DOCUMENTATION GAPS");
    expect(result.text).toContain("does not match the current chart diagnosis");
  });

  it("renders REASON FOR HOSPICE and DISEASE-SPECIFIC SUPPORT from resolved eligibility output, using support-status language rather than an eligibility determination", () => {
    const hospiceContext = {
      currentDiagnosisDescription: "SYSTOLIC HEART FAILURE, CHRONIC",
      whyHospice: { selected_guideline: "HEART_FAILURE", eligible: true, supporting_criteria: ["NYHA Class IV documented"] },
      certificationSupport: { lcd_reference: "LCD Hospice Eligibility Determination – Heart Disease", source_document: "CAD, CHF.pdf" },
    };
    const result = buildClinicalNarrative({}, {}, hospiceContext);
    expect(result.text).toContain("REASON FOR HOSPICE ADMISSION");
    expect(result.text).toContain("HEART_FAILURE guideline");
    expect(result.text).toContain("criteria currently supported by documented evidence");
    expect(result.text).toContain("not a final eligibility determination");
    expect(result.text).toContain("DISEASE-SPECIFIC SUPPORT");
    expect(result.text).toContain("NYHA Class IV documented");
    expect(result.text).toContain("LCD Hospice Eligibility Determination – Heart Disease");
  });

  it("lists related and unrelated conditions from relatedness classification under RELATED CONDITIONS AND COMORBID DISEASE BURDEN", () => {
    const hospiceContext = {
      relatedConditions: {
        related: [{ description: "Coronary artery disease" }, { description: "Atrial fibrillation" }],
        unrelated: [{ description: "Hemiplegia" }],
      },
    };
    const result = buildClinicalNarrative({}, {}, hospiceContext);
    expect(result.text).toContain("RELATED CONDITIONS AND COMORBID DISEASE BURDEN");
    expect(result.text).toContain("Coronary artery disease, Atrial fibrillation");
    expect(result.text).toContain("not contributing to the terminal hospice picture: Hemiplegia");
  });

  it("lists outstanding documentation-gap items under DOCUMENTATION GAPS", () => {
    const hospiceContext = { documentationGaps: [{ gap: "Ejection fraction not documented" }] };
    const result = buildClinicalNarrative({}, {}, hospiceContext);
    expect(result.text).toContain("DOCUMENTATION GAPS");
    expect(result.text).toContain("Ejection fraction not documented");
  });

  it("omits hospice-context sections entirely when no hospiceContext is supplied (backward compatible)", () => {
    const formData = { performanceStatus: { pps: "40" } };
    const result = buildClinicalNarrative(formData, {});
    expect(result.text).not.toContain("REASON FOR HOSPICE ADMISSION");
    expect(result.text).not.toContain("DISEASE-SPECIFIC SUPPORT");
    expect(result.text).not.toContain("DOCUMENTATION GAPS");
  });

  it("always ends with the fixed Plan of Care pointer sentence under RN FOLLOW-UP when any content exists", () => {
    const result = buildClinicalNarrative({ performanceStatus: { pps: "40" } }, {});
    expect(result.text).toContain("RN FOLLOW-UP");
    expect(result.text.trim().endsWith("See current Plan of Care for active problems, goals, and interventions.")).toBe(true);
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
  it("PASSes real clinical prose produced by buildClinicalNarrative", () => {
    const result = buildClinicalNarrative(
      { performanceStatus: { pps: "40" }, diagnoses: { primaryDiagnosis: { description: "CHF" } } },
      { age: 76, sex: "Male" },
      { currentDiagnosisDescription: "SYSTOLIC HEART FAILURE, CHRONIC" }
    );
    const gate = evaluateNarrativeQualityGate(result.text);
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

  it("FAILs a raw label/value field-dump line", () => {
    const gate = evaluateNarrativeQualityGate("Primary Diagnosis Description: ANEMIA DUE TO CKD STAGE 3A");
    expect(gate.status).toBe("FAIL");
  });

  it("FAILs an embedded internal record identifier (UUID)", () => {
    const gate = evaluateNarrativeQualityGate(
      "Patient reports improvement. source_record_id 3ea2f6fa-8dd9-4e3c-9b7d-009ddbe17ab0 was referenced."
    );
    expect(gate.status).toBe("FAIL");
    expect(gate.reasons.some((r) => r.code === "INTERNAL_ID_REFERENCE")).toBe(true);
  });
});
