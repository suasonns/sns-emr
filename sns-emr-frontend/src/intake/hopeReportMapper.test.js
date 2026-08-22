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
