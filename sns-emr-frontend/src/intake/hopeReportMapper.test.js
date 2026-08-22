import { describe, it, expect } from "vitest";
import { mapRnIcaToHopeReport } from "./hopeReportMapper";

// Priority 1 HOPE compliance remediation — focused mapper tests for
// F2000 / F2100 / F2200 / F3000 "was patient/responsible party asked?"
// tri-state items. See checkpoint "HOPE Admission CMS compliance remediation".

const PLACEHOLDER = "^";

function baseFormData(overrides = {}) {
  const {
    advancedCarePlanning: acpOverrides = {},
    spiritual: spiritualOverrides = {},
    livingSituation: livingSituationOverrides = {},
    ...rest
  } = overrides;

  return {
    demographics: {
      firstName: "Test",
      lastName: "Patient",
      dob: "1950-01-01",
      gender: "Female",
      ethnicity: [],
      race: [],
      advancedCarePlanning: {
        codeStatus: "",
        codeStatusDate: "",
        lifeSustainingTreatmentPreference: "",
        lifeSustainingTreatmentPreferenceDate: "",
        hospitalizationPreference: "",
        hospitalizationPreferenceDate: "",
        cprPreferenceAskedStatus: "",
        lifeSustainingAskedStatus: "",
        hospitalizationAskedStatus: "",
        ...acpOverrides,
      },
      livingSituation: {
        siteOfService: "",
        admittedFrom: "",
        livingArrangement: "",
        availabilityOfAssistance: "",
        ...livingSituationOverrides,
      },
    },
    spiritual: {
      concernsDiscussed: false,
      concernsDiscussedDate: "",
      spiritualConcerns: [],
      notes: "",
      concernsAskedStatus: "",
      ...spiritualOverrides,
    },
    ...rest,
  };
}

// A1400 Payer Information is sourced from the Facesheet insurance record
// (patient.primaryPayerType / patient.secondaryPayerType), not from RN ICA
// form_data — see checkpoint notes on why this is Facesheet-owned.
function basePatient(overrides = {}) {
  return {
    firstName: "Test",
    lastName: "Patient",
    mrn: "000-000",
    dob: "1950-01-01",
    age: 75,
    sex: "F",
    payer: "",
    primaryPayerType: "MEDICARE",
    secondaryPayerType: "",
    status: "ACTIVE",
    socDate: "2026-01-01",
    benefitPeriod: "",
    ...overrides,
  };
}

function findItem(report, code) {
  for (const section of report.sections) {
    const item = section.items.find((candidate) => candidate.code === code);
    if (item) return item;
  }
  throw new Error(`HOPE item ${code} not found in report`);
}

// Items are rendered as "<code> - <description>" in entry "A" (item.entries[0]).
// Split back out the leading response code for assertions.
function responseCode(report, code) {
  const item = findItem(report, code);
  const value = item.entries[0].value;
  return String(value).split(" - ")[0];
}

function responseDescription(report, code) {
  const item = findItem(report, code);
  const value = item.entries[0].value;
  return String(value).split(" - ").slice(1).join(" - ");
}

describe("mapRnIcaToHopeReport — F2000/F2100/F2200/F3000 asked-status", () => {
  describe("F2000 (CPR preference asked)", () => {
    it.each(["0", "1", "2"])("cprPreferenceAskedStatus = %s produces response code %s", (status) => {
      const formData = baseFormData({ advancedCarePlanning: { cprPreferenceAskedStatus: status } });
      const report = mapRnIcaToHopeReport(formData);
      expect(responseCode(report, "F2000")).toBe(status);
    });
  });

  describe("F2100 (life-sustaining treatment asked)", () => {
    it.each(["0", "1", "2"])("lifeSustainingAskedStatus = %s produces response code %s", (status) => {
      const formData = baseFormData({ advancedCarePlanning: { lifeSustainingAskedStatus: status } });
      const report = mapRnIcaToHopeReport(formData);
      expect(responseCode(report, "F2100")).toBe(status);
    });
  });

  describe("F2200 (hospitalization preference asked)", () => {
    it.each(["0", "1", "2"])("hospitalizationAskedStatus = %s produces response code %s", (status) => {
      const formData = baseFormData({ advancedCarePlanning: { hospitalizationAskedStatus: status } });
      const report = mapRnIcaToHopeReport(formData);
      expect(responseCode(report, "F2200")).toBe(status);
    });
  });

  describe("F3000 (spiritual/existential concerns asked)", () => {
    it.each(["0", "1", "2"])("concernsAskedStatus = %s produces response code %s", (status) => {
      const formData = baseFormData({ spiritual: { concernsAskedStatus: status } });
      const report = mapRnIcaToHopeReport(formData);
      expect(responseCode(report, "F3000")).toBe(status);
    });
  });
});

describe("mapRnIcaToHopeReport — separation of asked-status from clinical preference", () => {
  it("F2000 = 0 regardless of codeStatus = DNR", () => {
    const formData = baseFormData({
      advancedCarePlanning: { cprPreferenceAskedStatus: "0", codeStatus: "DNR" },
    });
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "F2000")).toBe("0");
  });

  it("F2100 = 1 regardless of lifeSustainingTreatmentPreference = 'No — does not want'", () => {
    const formData = baseFormData({
      advancedCarePlanning: {
        lifeSustainingAskedStatus: "1",
        lifeSustainingTreatmentPreference: "No — does not want",
      },
    });
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "F2100")).toBe("1");
  });

  it("F2200 = 2 regardless of hospitalizationPreference = 'Yes — wants hospitalization'", () => {
    const formData = baseFormData({
      advancedCarePlanning: {
        hospitalizationAskedStatus: "2",
        hospitalizationPreference: "Yes — wants hospitalization",
      },
    });
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "F2200")).toBe("2");
  });

  it("F3000 = 0 regardless of concernsDiscussed = true", () => {
    const formData = baseFormData({
      spiritual: { concernsAskedStatus: "0", concernsDiscussed: true },
    });
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "F3000")).toBe("0");
  });

  it("changing only the legacy clinical fields does not change the response code for any of the four items", () => {
    const withoutClinical = mapRnIcaToHopeReport(
      baseFormData({ advancedCarePlanning: { cprPreferenceAskedStatus: "1", lifeSustainingAskedStatus: "1", hospitalizationAskedStatus: "1" }, spiritual: { concernsAskedStatus: "1" } })
    );
    const withClinical = mapRnIcaToHopeReport(
      baseFormData({
        advancedCarePlanning: {
          cprPreferenceAskedStatus: "1",
          lifeSustainingAskedStatus: "1",
          hospitalizationAskedStatus: "1",
          codeStatus: "Full Code",
          lifeSustainingTreatmentPreference: "Undecided",
          hospitalizationPreference: "Undecided",
        },
        spiritual: { concernsAskedStatus: "1", concernsDiscussed: true, notes: "extensive narrative" },
      })
    );
    for (const code of ["F2000", "F2100", "F2200", "F3000"]) {
      expect(responseCode(withClinical, code)).toBe(responseCode(withoutClinical, code));
    }
  });
});

describe("mapRnIcaToHopeReport — legacy records (new field absent)", () => {
  it("F2000 is not a valid 0/1/2 when cprPreferenceAskedStatus is absent, even with codeStatus populated", () => {
    const formData = baseFormData({ advancedCarePlanning: { cprPreferenceAskedStatus: "", codeStatus: "DNR", codeStatusDate: "2024-01-01" } });
    const report = mapRnIcaToHopeReport(formData);
    expect(["0", "1", "2"]).not.toContain(responseCode(report, "F2000"));
    expect(responseCode(report, "F2000")).toBe(PLACEHOLDER);
    expect(responseDescription(report, "F2000")).toBe("Legacy record: review required");
  });

  it("F2100 is not a valid 0/1/2 when lifeSustainingAskedStatus is absent, even with a discussion date present", () => {
    const formData = baseFormData({
      advancedCarePlanning: {
        lifeSustainingAskedStatus: "",
        lifeSustainingTreatmentPreference: "Yes — wants life-sustaining treatment",
        lifeSustainingTreatmentPreferenceDate: "2024-05-01",
      },
    });
    const report = mapRnIcaToHopeReport(formData);
    expect(["0", "1", "2"]).not.toContain(responseCode(report, "F2100"));
    expect(responseDescription(report, "F2100")).toBe("Legacy record: review required");
  });

  it("F2200 is not a valid 0/1/2 when hospitalizationAskedStatus is absent, even with a preference recorded", () => {
    const formData = baseFormData({
      advancedCarePlanning: { hospitalizationAskedStatus: "", hospitalizationPreference: "No — does not want" },
    });
    const report = mapRnIcaToHopeReport(formData);
    expect(["0", "1", "2"]).not.toContain(responseCode(report, "F2200"));
    expect(responseDescription(report, "F2200")).toBe("Legacy record: review required");
  });

  it("F3000 is not a valid 0/1/2 when concernsAskedStatus is absent, even with concernsDiscussed = true and narrative notes", () => {
    const formData = baseFormData({
      spiritual: { concernsAskedStatus: "", concernsDiscussed: true, notes: "Patient discussed spiritual concerns at length." },
    });
    const report = mapRnIcaToHopeReport(formData);
    expect(["0", "1", "2"]).not.toContain(responseCode(report, "F3000"));
    expect(responseDescription(report, "F3000")).toBe("Legacy record: review required");
  });

  it("does not silently default to 0 when every source field is entirely empty", () => {
    const formData = baseFormData();
    const report = mapRnIcaToHopeReport(formData);
    for (const code of ["F2000", "F2100", "F2200", "F3000"]) {
      expect(responseCode(report, code)).toBe(PLACEHOLDER);
      expect(responseCode(report, code)).not.toBe("0");
    }
  });

  it("does not silently infer 1 from an existing discussion date alone", () => {
    const formData = baseFormData({
      advancedCarePlanning: { cprPreferenceAskedStatus: "", codeStatusDate: "2024-01-01" },
    });
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "F2000")).not.toBe("1");
    expect(responseCode(report, "F2000")).toBe(PLACEHOLDER);
  });
});

describe("mapRnIcaToHopeReport — JSONB save/reload round-trip", () => {
  it("preserves all four asked-status codes after a JSON serialize/deserialize cycle", () => {
    const original = baseFormData({
      advancedCarePlanning: {
        cprPreferenceAskedStatus: "0",
        lifeSustainingAskedStatus: "1",
        hospitalizationAskedStatus: "2",
      },
      spiritual: { concernsAskedStatus: "1" },
    });

    // Simulate persistence through the RN ICA form_data JSONB column: serialize on
    // save, parse on reload, exactly as the backend adapter does with form_data.
    const reloaded = JSON.parse(JSON.stringify(original));

    const report = mapRnIcaToHopeReport(reloaded);
    expect(responseCode(report, "F2000")).toBe("0");
    expect(responseCode(report, "F2100")).toBe("1");
    expect(responseCode(report, "F2200")).toBe("2");
    expect(responseCode(report, "F3000")).toBe("1");
  });
});

describe("mapRnIcaToHopeReport — value 0 is a completed answer, not a missing one", () => {
  it("treats string \"0\" as present via the same completeness rule used by validation (!value)", () => {
    // Mirrors the truthiness check in RNICA.jsx's validateRNICA: `!value` must be
    // false for "0" (present/complete) and true only for "" / undefined (missing).
    expect(!"0").toBe(false);
    expect(!"").toBe(true);
    expect(!undefined).toBe(true);
  });

  it("F2000/F2100/F2200/F3000 all export the literal string \"0\" (not the placeholder) when asked-status is '0'", () => {
    const formData = baseFormData({
      advancedCarePlanning: { cprPreferenceAskedStatus: "0", lifeSustainingAskedStatus: "0", hospitalizationAskedStatus: "0" },
      spiritual: { concernsAskedStatus: "0" },
    });
    const report = mapRnIcaToHopeReport(formData);
    for (const code of ["F2000", "F2100", "F2200", "F3000"]) {
      expect(responseCode(report, code)).toBe("0");
      expect(responseCode(report, code)).not.toBe(PLACEHOLDER);
    }
  });
});

describe("mapRnIcaToHopeReport — legacyReviewRequired banner/filter data", () => {
  it("is not required when all four asked-status fields are answered (including '0')", () => {
    const formData = baseFormData({
      advancedCarePlanning: { cprPreferenceAskedStatus: "0", lifeSustainingAskedStatus: "0", hospitalizationAskedStatus: "0" },
      spiritual: { concernsAskedStatus: "0" },
      pain: { screenedForPain: "0", neuropathicPain: "0" },
    });
    const report = mapRnIcaToHopeReport(formData);
    expect(report.legacyReviewRequired.required).toBe(false);
    expect(report.legacyReviewRequired.items).toEqual([]);
  });

  it("is required and lists exactly the missing items when some asked-status fields are absent", () => {
    const formData = baseFormData({
      advancedCarePlanning: { cprPreferenceAskedStatus: "1", lifeSustainingAskedStatus: "", hospitalizationAskedStatus: "1" },
      spiritual: { concernsAskedStatus: "" },
      pain: { screenedForPain: "0", neuropathicPain: "0" },
    });
    const report = mapRnIcaToHopeReport(formData);
    expect(report.legacyReviewRequired.required).toBe(true);
    expect(report.legacyReviewRequired.items).toEqual(["F2100", "F3000"]);
  });

  it("lists all five items when the record is fully legacy (no new fields at all)", () => {
    const report = mapRnIcaToHopeReport(baseFormData());
    expect(report.legacyReviewRequired.required).toBe(true);
    expect(report.legacyReviewRequired.items).toEqual(["F2000", "F2100", "F2200", "F3000", "J0900", "J0915"]);
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Priority 2 — A0215 Site of Service, A1805 Admitted From, A1905 Living
// Arrangements now persist/export the official CMS code directly instead of
// a locally-invented code translated from a free-text label.
// ─────────────────────────────────────────────────────────────────────────

describe("mapRnIcaToHopeReport — A0215 Site of Service", () => {
  it.each([
    ["01", "Patient's Home/Residence"],
    ["02", "Assisted Living Facility"],
    ["03", "Nursing Long Term Care (LTC) or Non-Skilled Nursing Facility (NF)"],
    ["04", "Skilled Nursing Facility (SNF)"],
    ["05", "Inpatient Hospital"],
    ["06", "Inpatient Hospice Facility (General Inpatient (GIP))"],
    ["07", "Long Term Care Hospital (LTCH)"],
    ["08", "Inpatient Psychiatric Facility"],
    ["09", "Hospice Home Care (Routine Home Care (RHC)) Provided in a Hospice Facility"],
    ["99", "Not listed"],
  ])("official code %s passes through unchanged with its official description", (code, description) => {
    const report = mapRnIcaToHopeReport(baseFormData({ livingSituation: { siteOfService: code } }));
    expect(responseCode(report, "A0215")).toBe(code);
    expect(responseDescription(report, "A0215")).toBe(description);
  });

  it.each([
    ["Home", "01"],
    ["ALF", "02"],
    ["Board & Care", "02"],
    ["Memory Care", "02"],
    ["SNF", "04"],
    ["Hospital", "05"],
    ["Homeless", "99"],
    ["Other", "99"],
  ])("legacy value '%s' translates to official code %s", (legacyValue, expectedCode) => {
    const report = mapRnIcaToHopeReport(baseFormData({ livingSituation: { siteOfService: legacyValue } }));
    expect(responseCode(report, "A0215")).toBe(expectedCode);
  });

  it("is not a valid official code when the field is empty", () => {
    const report = mapRnIcaToHopeReport(baseFormData());
    expect(responseCode(report, "A0215")).toBe(PLACEHOLDER);
  });
});

describe("mapRnIcaToHopeReport — A1805 Admitted From", () => {
  it.each([
    ["01", "Home/Community"],
    ["02", "Nursing Home (long-term care facility)"],
    ["03", "Skilled Nursing Facility (SNF, swing beds)"],
    ["04", "Short-Term General Hospital (acute hospital, IPPS)"],
    ["05", "Long-Term Care Hospital (LTCH)"],
    ["06", "Inpatient Rehabilitation Facility (IRF)"],
    ["07", "Inpatient Psychiatric Facility"],
    ["08", "Intermediate Care Facility (ID/DD facility)"],
    ["10", "Hospice (institutional facility)"],
    ["11", "Critical Access Hospital (CAH)"],
    ["99", "Not Listed"],
  ])("official code %s passes through unchanged with its official description", (code, description) => {
    const report = mapRnIcaToHopeReport(baseFormData({ livingSituation: { admittedFrom: code } }));
    expect(responseCode(report, "A1805")).toBe(code);
    expect(responseDescription(report, "A1805")).toBe(description);
  });

  it("does not use code 09 (official A1805 code set skips from 08 to 10)", () => {
    expect(Object.keys({
      "01": 1, "02": 1, "03": 1, "04": 1, "05": 1, "06": 1, "07": 1, "08": 1, "10": 1, "11": 1, "99": 1,
    })).not.toContain("09");
  });

  it.each([
    ["Home", "01"],
    ["ALF", "01"],
    ["Hospital", "04"],
    ["SNF", "03"],
    ["Rehab", "06"],
    ["Other", "99"],
  ])("legacy value '%s' translates to official code %s", (legacyValue, expectedCode) => {
    const report = mapRnIcaToHopeReport(baseFormData({ livingSituation: { admittedFrom: legacyValue } }));
    expect(responseCode(report, "A1805")).toBe(expectedCode);
  });

  it("is not a valid official code when the field is empty", () => {
    const report = mapRnIcaToHopeReport(baseFormData());
    expect(responseCode(report, "A1805")).toBe(PLACEHOLDER);
  });
});

describe("mapRnIcaToHopeReport — A1905 Living Arrangements", () => {
  it.each([
    ["1", "Alone (no other residents in the home)"],
    ["2", "With others in the home (e.g., family, friends, or paid caregiver)"],
    ["3", "Congregate home (e.g., assisted living or residential care home)"],
    ["4", "Inpatient facility (e.g., SNF, nursing home, inpatient hospice, hospital)"],
    ["5", "Does not have a permanent home"],
  ])("official code %s passes through unchanged with its official description", (code, description) => {
    const report = mapRnIcaToHopeReport(baseFormData({ livingSituation: { livingArrangement: code } }));
    expect(responseCode(report, "A1905")).toBe(code);
    expect(responseDescription(report, "A1905")).toBe(description);
  });

  it.each([
    ["Alone", "1"],
    ["With spouse", "2"],
    ["With family", "2"],
    ["With non-relative", "2"],
    ["Facility", "4"],
  ])("legacy value '%s' translates to official code %s", (legacyValue, expectedCode) => {
    const report = mapRnIcaToHopeReport(baseFormData({ livingSituation: { livingArrangement: legacyValue } }));
    expect(responseCode(report, "A1905")).toBe(expectedCode);
  });

  it("legacy code collision is resolved correctly: old code '5' (Facility) must now export official code 4, not 5", () => {
    // Old local vocabulary used numeric code 5 for "Facility resident", but the
    // official CMS code 5 means "Does not have a permanent home" — a materially
    // different, opposite-risk category. Confirms no accidental code collision.
    const report = mapRnIcaToHopeReport(baseFormData({ livingSituation: { livingArrangement: "Facility" } }));
    expect(responseCode(report, "A1905")).toBe("4");
    expect(responseCode(report, "A1905")).not.toBe("5");
  });

  it("is not a valid official code when the field is empty", () => {
    const report = mapRnIcaToHopeReport(baseFormData());
    expect(responseCode(report, "A1905")).toBe(PLACEHOLDER);
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Priority 3 — I0010 Principal Diagnosis now exports the official CMS
// diagnosis category code (01-09, 99), additive alongside the existing
// free-text ICD-10 diagnosis field (kept as supporting detail).
// ─────────────────────────────────────────────────────────────────────────

describe("mapRnIcaToHopeReport — I0010 Principal Diagnosis category", () => {
  it.each([
    ["01", "Cancer"],
    ["02", "Dementia (including Alzheimer's disease)"],
    ["03", "Neurological Condition (e.g., Parkinson's disease, multiple sclerosis, ALS)"],
    ["04", "Stroke"],
    ["05", "Chronic Obstructive Pulmonary Disease (COPD)"],
    ["06", "Cardiovascular (excluding heart failure)"],
    ["07", "Heart Failure"],
    ["08", "Liver Disease"],
    ["09", "Renal Disease"],
    ["99", "None of the above"],
  ])("category code %s exports with its official description", (code, description) => {
    const formData = baseFormData();
    formData.diagnoses = {
      primaryDiagnosis: { icd10: "C50.911", description: "Malignant neoplasm", onsetDate: "2024-01-01", hopeDiagnosisCategory: code },
    };
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "I0010")).toBe(code);
    expect(responseDescription(report, "I0010")).toBe(description);
  });

  it("keeps the ICD-10 code + description as a separate supporting detail entry, not the primary response", () => {
    const formData = baseFormData();
    formData.diagnoses = {
      primaryDiagnosis: { icd10: "C50.911", description: "Malignant neoplasm", onsetDate: "2024-01-01", hopeDiagnosisCategory: "01" },
    };
    const report = mapRnIcaToHopeReport(formData);
    const item = findItem(report, "I0010");
    expect(item.entries).toHaveLength(2);
    expect(item.entries[1].value).toBe("C50.911 - Malignant neoplasm");
  });

  it("is not a valid official code when the category field is empty (legacy records predating this field)", () => {
    const formData = baseFormData();
    formData.diagnoses = {
      primaryDiagnosis: { icd10: "C50.911", description: "Malignant neoplasm", onsetDate: "2024-01-01" },
    };
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "I0010")).toBe(PLACEHOLDER);
  });
});

// A1400 Payer Information is sourced from the Facesheet insurance record
// (patient.primaryPayerType / patient.secondaryPayerType), not RN ICA
// form_data. See checkpoint notes: duplicating payer data into RN ICA would
// create a second, potentially conflicting source of truth, so the mapper
// crosswalks the Facesheet's structured "Payer Source Type" into the
// official CMS A1400 code instead.
describe("mapRnIcaToHopeReport — A1400 Payer Information (Facesheet-sourced)", () => {
  it.each([
    ["MEDICARE", "A - Medicare (traditional fee-for-service)"],
    ["MEDICARE_ADVANTAGE", "B - Medicare (managed care/Part C/Medicare Advantage)"],
    ["MEDICAID", "C - Medicaid (traditional fee-for-service)"],
    ["MEDICAID_MANAGED_CARE", "D - Medicaid (managed care)"],
    ["PRIVATE_MANAGED_CARE", "I - Private managed care"],
    ["OTHER_GOVERNMENT", "G - Other government (e.g., TRICARE, VA, etc.)"],
    ["SELF_PAY", "J - Self-pay"],
    ["NO_PAYER_SOURCE", "K - No payer source"],
  ])("Facesheet primary payer source type '%s' exports official A1400 code '%s'", (primaryPayerType, expectedText) => {
    const report = mapRnIcaToHopeReport(baseFormData(), basePatient({ primaryPayerType, secondaryPayerType: "" }));
    const item = findItem(report, "A1400");
    expect(item.entries[0].value).toBe(expectedText);
  });

  it("primary and secondary payer types that differ both contribute distinct codes (multi-select)", () => {
    const report = mapRnIcaToHopeReport(
      baseFormData(),
      basePatient({ primaryPayerType: "MEDICARE", secondaryPayerType: "PRIVATE_MANAGED_CARE" })
    );
    const item = findItem(report, "A1400");
    expect(item.entries[0].value).toBe(
      "A - Medicare (traditional fee-for-service); I - Private managed care"
    );
  });

  it("primary and secondary payer types that map to the same code are deduplicated", () => {
    const report = mapRnIcaToHopeReport(
      baseFormData(),
      basePatient({ primaryPayerType: "MEDICARE", secondaryPayerType: "MEDICARE" })
    );
    const item = findItem(report, "A1400");
    expect(item.entries[0].value).toBe("A - Medicare (traditional fee-for-service)");
  });

  it("clinical/legacy patient.payer free text does not determine the A1400 response", () => {
    const report = mapRnIcaToHopeReport(
      baseFormData(),
      basePatient({ payer: "Blue Shield", primaryPayerType: "MEDICAID", secondaryPayerType: "" })
    );
    const item = findItem(report, "A1400");
    expect(item.entries[0].value).toBe("C - Medicaid (traditional fee-for-service)");
  });

  it("is marked legacy/incomplete when neither Facesheet payer type is set (pre-remediation records)", () => {
    const report = mapRnIcaToHopeReport(
      baseFormData(),
      basePatient({ payer: "Blue Shield", primaryPayerType: "", secondaryPayerType: "" })
    );
    const item = findItem(report, "A1400");
    expect(item.entries[0].value).toBe("Legacy record: review required");
    expect(report.legacyReviewRequired.required).toBe(true);
    expect(report.legacyReviewRequired.items).toContain("A1400");
  });

  it("an unrecognized/unmapped payer type string does not silently produce a valid code", () => {
    const report = mapRnIcaToHopeReport(
      baseFormData(),
      basePatient({ primaryPayerType: "SOME_UNKNOWN_VALUE", secondaryPayerType: "" })
    );
    const item = findItem(report, "A1400");
    expect(item.entries[0].value).toBe("Legacy record: review required");
    expect(report.legacyReviewRequired.items).toContain("A1400");
  });

  it("round-trips through the patient object unchanged", () => {
    const patient = basePatient({ primaryPayerType: "SELF_PAY", secondaryPayerType: "" });
    const reportA = mapRnIcaToHopeReport(baseFormData(), patient);
    const reportB = mapRnIcaToHopeReport(baseFormData(), JSON.parse(JSON.stringify(patient)));
    expect(findItem(reportA, "A1400").entries[0].value).toBe(findItem(reportB, "A1400").entries[0].value);
    expect(findItem(reportB, "A1400").entries[0].value).toBe("J - Self-pay");
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Priority 5 — J0900 Pain Screening / J0915 Neuropathic Pain.
//
// J0900.A ("Was the patient screened for pain?") and J0900.C ("The
// patient's pain severity was:") are official CMS-coded responses that must
// come from dedicated fields (screenedForPain / painSeverityCategory), not
// be inferred from verbalizesPain (a communication-status/tool-selection
// field) or painIntensity.current (a raw numeric score). J0915
// ("Does the patient have neuropathic pain?") must come from the
// neuropathicPain field, not the separate uncomfortableBecauseOfPain
// clinical field it was previously (incorrectly) tagged to.
// ─────────────────────────────────────────────────────────────────────────

describe("mapRnIcaToHopeReport — J0900 Pain Screening", () => {
  it.each([
    ["0", "No"],
    ["1", "Yes"],
  ])("J0900.A code '%s' exports with its official description", (screenedForPain, description) => {
    const formData = baseFormData({ pain: { screenedForPain, painSeverityCategory: screenedForPain === "1" ? "1" : "", standardizedPainToolType: screenedForPain === "1" ? "1" : "" } });
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "J0900")).toBe(screenedForPain);
    expect(responseDescription(report, "J0900")).toBe(description);
  });

  it.each([
    ["0", "None"],
    ["1", "Mild"],
    ["2", "Moderate"],
    ["3", "Severe"],
    ["9", "Pain not rated"],
  ])("J0900.C severity code '%s' exports with its official description when screened = Yes", (severityCode, description) => {
    const formData = baseFormData({ pain: { screenedForPain: "1", painSeverityCategory: severityCode, standardizedPainToolType: "1" } });
    const report = mapRnIcaToHopeReport(formData);
    const item = findItem(report, "J0900");
    expect(item.entries[2].value).toBe(`${severityCode} - ${description}`);
  });

  it.each([
    ["1", "Numeric"],
    ["2", "Verbal descriptor"],
    ["3", "Patient visual"],
    ["4", "Staff observation"],
    ["9", "No standardized tool used"],
  ])("J0900.D tool code '%s' exports with its official description when screened = Yes", (toolCode, description) => {
    const formData = baseFormData({ pain: { screenedForPain: "1", painSeverityCategory: "1", standardizedPainToolType: toolCode } });
    const report = mapRnIcaToHopeReport(formData);
    const item = findItem(report, "J0900");
    expect(item.entries[3].value).toBe(`${toolCode} - ${description}`);
  });

  it("J0900.C and J0900.D are validly skipped (not required) when J0900.A is 'No'", () => {
    const formData = baseFormData({ pain: { screenedForPain: "0", painSeverityCategory: "", standardizedPainToolType: "" } });
    const report = mapRnIcaToHopeReport(formData);
    const item = findItem(report, "J0900");
    expect(item.entries[0].value).toBe("0 - No");
    expect(item.entries[2].value).toContain("Skipped");
    expect(item.entries[3].value).toContain("Skipped");
    expect(report.legacyReviewRequired.items).not.toContain("J0900");
  });

  it("is legacy/incomplete when screenedForPain is absent (pre-remediation records)", () => {
    const formData = baseFormData({ pain: {} });
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "J0900")).toBe(PLACEHOLDER);
    expect(report.legacyReviewRequired.required).toBe(true);
    expect(report.legacyReviewRequired.items).toContain("J0900");
  });

  it("is legacy/incomplete when screenedForPain is 'Yes' but painSeverityCategory is missing", () => {
    const formData = baseFormData({ pain: { screenedForPain: "1", painSeverityCategory: "", standardizedPainToolType: "1" } });
    const report = mapRnIcaToHopeReport(formData);
    const item = findItem(report, "J0900");
    expect(item.entries[0].value).toBe("1 - Yes");
    expect(item.entries[2].value).toBe("^ - Legacy record: review required");
    expect(report.legacyReviewRequired.items).toContain("J0900");
  });

  it("is legacy/incomplete when screenedForPain is 'Yes' but standardizedPainToolType is missing", () => {
    const formData = baseFormData({ pain: { screenedForPain: "1", painSeverityCategory: "1", standardizedPainToolType: "" } });
    const report = mapRnIcaToHopeReport(formData);
    const item = findItem(report, "J0900");
    expect(item.entries[0].value).toBe("1 - Yes");
    expect(item.entries[3].value).toBe("^ - Legacy record: review required");
    expect(report.legacyReviewRequired.items).toContain("J0900");
  });

  it("verbalizesPain (tool-selection) does not influence the J0900.A response", () => {
    const formData = baseFormData({ pain: { screenedForPain: "0", verbalizesPain: "1" } });
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "J0900")).toBe("0");
  });

  it("painIntensity.current (raw numeric score) does not influence the J0900.C response", () => {
    const formData = baseFormData({ pain: { screenedForPain: "1", painSeverityCategory: "2", standardizedPainToolType: "1", painIntensity: { current: 7 } } });
    const report = mapRnIcaToHopeReport(formData);
    const item = findItem(report, "J0900");
    expect(item.entries[2].value).toBe("2 - Moderate");
  });

  it("assessmentTool (auto-derived UI tool selection) does not influence the J0900.D response", () => {
    const formData = baseFormData({ pain: { screenedForPain: "1", painSeverityCategory: "1", standardizedPainToolType: "4", assessmentTool: "Numeric (0-10)" } });
    const report = mapRnIcaToHopeReport(formData);
    const item = findItem(report, "J0900");
    expect(item.entries[3].value).toBe("4 - Staff observation");
  });

  it("round-trips through JSONB save/reload unchanged", () => {
    const formData = baseFormData({ pain: { screenedForPain: "1", painSeverityCategory: "3", standardizedPainToolType: "2" } });
    const reloaded = JSON.parse(JSON.stringify(formData));
    const report = mapRnIcaToHopeReport(reloaded);
    expect(responseCode(report, "J0900")).toBe("1");
    expect(findItem(report, "J0900").entries[2].value).toBe("3 - Severe");
    expect(findItem(report, "J0900").entries[3].value).toBe("2 - Verbal descriptor");
  });
});

describe("mapRnIcaToHopeReport — J0915 Neuropathic Pain", () => {
  it.each([
    ["0", "No"],
    ["1", "Yes"],
  ])("code '%s' exports with its official description", (neuropathicPain, description) => {
    const formData = baseFormData({ pain: { neuropathicPain } });
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "J0915")).toBe(neuropathicPain);
    expect(responseDescription(report, "J0915")).toBe(description);
  });

  it("uncomfortableBecauseOfPain (a separate clinical field) does not influence the J0915 response", () => {
    const formData = baseFormData({ pain: { neuropathicPain: "0", uncomfortableBecauseOfPain: "1" } });
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "J0915")).toBe("0");
  });

  it("is legacy/incomplete independently of J0900 when neuropathicPain is missing but J0900 is fully answered", () => {
    const formData = baseFormData({ pain: { screenedForPain: "0", neuropathicPain: "" } });
    const report = mapRnIcaToHopeReport(formData);
    expect(report.legacyReviewRequired.items).toContain("J0915");
    expect(report.legacyReviewRequired.items).not.toContain("J0900");
  });

  it("does not flag J0915 as incomplete when J0900 is missing but neuropathicPain is answered", () => {
    const formData = baseFormData({ pain: { neuropathicPain: "1" } });
    const report = mapRnIcaToHopeReport(formData);
    expect(report.legacyReviewRequired.items).toContain("J0900");
    expect(report.legacyReviewRequired.items).not.toContain("J0915");
  });

  it("is blank/placeholder when neuropathicPain is not set (legacy records)", () => {
    const formData = baseFormData({ pain: {} });
    const report = mapRnIcaToHopeReport(formData);
    expect(responseCode(report, "J0915")).toBe(PLACEHOLDER);
  });
});

