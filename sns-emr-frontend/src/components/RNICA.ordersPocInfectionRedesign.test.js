import { describe, it, expect } from "vitest";
import {
  getHaAssignmentStatus,
  getInitialPocStatus,
  getComfortMeasuresStatus,
  isVisitFrequencyConfigured,
  computeOrdersPocDocumentationCoverage,
  formatVisitFrequencySummary,
  getConfiguredVisitFrequencySummaries,
  DEFAULT_VISIT_DISCIPLINE_CODES,
  OPTIONAL_VISIT_DISCIPLINE_CODES,
} from "./RNICA.jsx";

// PRODUCT OWNER DIRECTIVE (2026-10-25) "Orders & POC Still Does Not
// Follow Infection Design" / "Orders & POC Visit Frequency Redesign
// Revision" -- proves the pure derivation/coverage helpers that power
// the Infection-style redesign (Documentation Coverage summary pills,
// HA/Initial-POC/Comfort-Measures state pills, the per-discipline Visit
// Frequency summary). UI rendering itself is exercised by the project's
// existing manual/live-browser verification process (per established
// session convention); these tests lock in the pure business logic so
// it can't silently regress.

describe("getHaAssignmentStatus", () => {
  it("is NOT_APPLICABLE when explicitly marked N/A, regardless of any stale aide name", () => {
    expect(getHaAssignmentStatus({ notApplicable: true, assignedAide: "Jane Doe" })).toBe("NOT_APPLICABLE");
  });
  it("is ASSIGNED when an aide name is present", () => {
    expect(getHaAssignmentStatus({ assignedAide: "Jane Doe" })).toBe("ASSIGNED");
  });
  it("is NOT_ASSIGNED when neither N/A nor an aide name is present", () => {
    expect(getHaAssignmentStatus({})).toBe("NOT_ASSIGNED");
    expect(getHaAssignmentStatus({ assignedAide: "   " })).toBe("NOT_ASSIGNED");
  });
});

describe("getInitialPocStatus", () => {
  it("uses the explicit status field when present", () => {
    expect(getInitialPocStatus({ status: "REQUIRES_REVIEW", created: true })).toBe("REQUIRES_REVIEW");
  });
  it("falls back to the legacy `created` boolean for pre-redesign records with no status", () => {
    expect(getInitialPocStatus({ created: true })).toBe("CREATED");
    expect(getInitialPocStatus({ created: false })).toBe("NOT_STARTED");
    expect(getInitialPocStatus({})).toBe("NOT_STARTED");
  });
});

describe("getComfortMeasuresStatus", () => {
  it("uses the explicit status field when present", () => {
    expect(getComfortMeasuresStatus({ comfortMeasuresStatus: "NOT_APPLICABLE", comfortMeasuresInPlace: true })).toBe("NOT_APPLICABLE");
  });
  it("falls back to the legacy boolean for pre-redesign records with no status", () => {
    expect(getComfortMeasuresStatus({ comfortMeasuresInPlace: true })).toBe("ESTABLISHED");
    expect(getComfortMeasuresStatus({ comfortMeasuresInPlace: false })).toBe("NOT_YET_ESTABLISHED");
    expect(getComfortMeasuresStatus({})).toBe("NOT_YET_ESTABLISHED");
  });
});

describe("isVisitFrequencyConfigured", () => {
  it("is false for an empty/all-blank row set", () => {
    expect(isVisitFrequencyConfigured([])).toBe(false);
    expect(isVisitFrequencyConfigured([{ discipline: "SN", numberOfVisits: "", period: "", prn: false }])).toBe(false);
  });
  it("is true once at least one row has a free-text hospice-shorthand frequency", () => {
    expect(isVisitFrequencyConfigured([{ discipline: "SN", numberOfVisits: "2W4", period: "" }])).toBe(true);
  });
  it("is true for a selected Period alone", () => {
    expect(isVisitFrequencyConfigured([{ discipline: "RN-SUP", numberOfVisits: "", period: "every 14 days" }])).toBe(true);
  });
  it("is true for an explicit PRN flag alone", () => {
    expect(isVisitFrequencyConfigured([{ discipline: "HA", numberOfVisits: "", period: "", prn: true }])).toBe(true);
  });
  it("is true for a free-text 'specify'/Frequency Notes override even with no frequency/period/PRN", () => {
    expect(isVisitFrequencyConfigured([{ discipline: "SN", specify: "within 5 days of admission" }])).toBe(true);
  });
  it("ignores the SN row's staffing-only Provider Mix/Coverage fields -- they are not a frequency order", () => {
    expect(isVisitFrequencyConfigured([
      { discipline: "SN", numberOfVisits: "", period: "", prn: false, providerMix: "RN/LVN Combination", rnCoverage: "Every 14 days", lvnCoverage: "Routine visit coverage" },
    ])).toBe(false);
  });
});

describe("formatVisitFrequencySummary", () => {
  it("shows the free-text Frequency plus Period when both are present", () => {
    expect(formatVisitFrequencySummary({ numberOfVisits: "2", period: "W4" })).toBe("2 W4");
  });
  it("shows the Frequency alone when it already carries the full hospice shorthand", () => {
    expect(formatVisitFrequencySummary({ numberOfVisits: "2W4" })).toBe("2W4");
    expect(formatVisitFrequencySummary({ numberOfVisits: "3W2" })).toBe("3W2");
  });
  it("shows the Period alone when Frequency is blank", () => {
    expect(formatVisitFrequencySummary({ period: "every 14 days" })).toBe("every 14 days");
  });
  it("falls back to 'PRN' when only the PRN flag is set", () => {
    expect(formatVisitFrequencySummary({ prn: true })).toBe("PRN");
  });
  it("is blank for a never-touched row", () => {
    expect(formatVisitFrequencySummary({})).toBe("");
    expect(formatVisitFrequencySummary()).toBe("");
  });
});

describe("getConfiguredVisitFrequencySummaries", () => {
  it("returns canonical disciplines in their fixed display order, omitting unconfigured ones", () => {
    const rows = [
      { discipline: "SW", numberOfVisits: "1W4" },
      { discipline: "SN", numberOfVisits: "2W4" },
      { discipline: "HA", numberOfVisits: "", period: "" },
    ];
    const summaries = getConfiguredVisitFrequencySummaries(rows);
    expect(summaries.map((s) => s.code)).toEqual(["SN", "SW"]);
    expect(summaries.find((s) => s.code === "SN")).toEqual({ code: "SN", shortLabel: "SN", summary: "2W4" });
    expect(summaries.find((s) => s.code === "SW")).toEqual({ code: "SW", shortLabel: "Social Work", summary: "1W4" });
  });
  it("matches the acceptance test from the 'SN As Primary Orderable Nursing Discipline' directive -- one nursing order, no RN/LVN contradiction", () => {
    const rows = [
      { discipline: "SN", numberOfVisits: "2", period: "per Week", providerMix: "RN/LVN Combination", rnCoverage: "Every 14 days", lvnCoverage: "Routine visit coverage" },
    ];
    const summaries = getConfiguredVisitFrequencySummaries(rows);
    // Exactly one nursing order (SN); RN/LVN never appear as separate codes.
    expect(summaries.map((s) => s.code)).toEqual(["SN"]);
    expect(summaries.find((s) => s.code === "RN")).toBeUndefined();
    expect(summaries.find((s) => s.code === "LVN")).toBeUndefined();
    expect(summaries[0].summary).toBe("2 per Week");
  });
  it("matches every literal example from the earlier PO directive, re-expressed with the consolidated disciplines", () => {
    const rows = [
      { discipline: "SN", numberOfVisits: "2W4" },
      { discipline: "HA", numberOfVisits: "3W4" },
      { discipline: "SW", numberOfVisits: "1W4" },
      { discipline: "SC", numberOfVisits: "1W4" },
      { discipline: "RN-SUP", period: "every 14 days" },
      { discipline: "NP", prn: true },
    ];
    const summaries = getConfiguredVisitFrequencySummaries(rows);
    const byCode = Object.fromEntries(summaries.map((s) => [s.code, s]));
    expect(byCode.SN.summary).toBe("2W4");
    expect(byCode.HA.summary).toBe("3W4");
    expect(byCode.SW).toEqual(expect.objectContaining({ shortLabel: "Social Work", summary: "1W4" }));
    expect(byCode.SC).toEqual(expect.objectContaining({ shortLabel: "Spiritual Counseling", summary: "1W4" }));
    expect(byCode["RN-SUP"]).toEqual(expect.objectContaining({ shortLabel: "RN Supervisor", summary: "every 14 days" }));
    expect(byCode.NP.summary).toBe("PRN");
  });
  it("still surfaces a legacy/non-canonical discipline (e.g. pre-consolidation 'RN'/'LVN' data) after the canonical disciplines", () => {
    const rows = [
      { discipline: "SN", numberOfVisits: "2W4" },
      { discipline: "RN", numberOfVisits: "3", period: "per Week" },
      { discipline: "LVN", prn: true },
    ];
    const summaries = getConfiguredVisitFrequencySummaries(rows);
    expect(summaries.map((s) => s.code)).toEqual(["SN", "RN", "LVN"]);
    expect(summaries[1].summary).toBe("3 per Week");
    expect(summaries[2].summary).toBe("PRN");
  });
  it("returns an empty array when no discipline has been configured", () => {
    expect(getConfiguredVisitFrequencySummaries([])).toEqual([]);
    expect(getConfiguredVisitFrequencySummaries()).toEqual([]);
  });
});

describe("DEFAULT_VISIT_DISCIPLINE_CODES / OPTIONAL_VISIT_DISCIPLINE_CODES", () => {
  it("has exactly the 5 always-rendered disciplines, led by SN as the one authoritative nursing order", () => {
    expect(DEFAULT_VISIT_DISCIPLINE_CODES).toEqual(["SN", "HA", "SW", "SC", "RN-SUP"]);
  });
  it("has exactly the 8 PO-named optional disciplines from the 'SN As Primary Orderable Nursing Discipline' closed list", () => {
    expect(OPTIONAL_VISIT_DISCIPLINE_CODES).toEqual(
      expect.arrayContaining(["VOL", "PT", "OT", "ST", "NP", "MD", "BC", "ADMIN"])
    );
    expect(OPTIONAL_VISIT_DISCIPLINE_CODES).toHaveLength(8);
  });
  it("default and optional codes are disjoint and together cover all 13 canonical disciplines", () => {
    const overlap = DEFAULT_VISIT_DISCIPLINE_CODES.filter((c) => OPTIONAL_VISIT_DISCIPLINE_CODES.includes(c));
    expect(overlap).toEqual([]);
    expect(DEFAULT_VISIT_DISCIPLINE_CODES.length + OPTIONAL_VISIT_DISCIPLINE_CODES.length).toBe(13);
  });
  it("no longer treats RN/LVN/MSW/LCSW/BSW/Dietitian as independently orderable disciplines", () => {
    const removed = ["RN", "LVN", "MSW", "LCSW", "BSW", "Dietitian"];
    removed.forEach((code) => {
      expect(DEFAULT_VISIT_DISCIPLINE_CODES).not.toContain(code);
      expect(OPTIONAL_VISIT_DISCIPLINE_CODES).not.toContain(code);
    });
  });
});

describe("computeOrdersPocDocumentationCoverage", () => {
  const COMPLETE_DATA = {
    levelOfCare: { level: "Routine Care" },
    visitFrequency: [{ discipline: "SN", numberOfVisits: "3", period: "per Week" }],
    haAssignment: { assignedAide: "Jane Doe" },
    initialPocIdg: { status: "CREATED" },
    toVerification: { verbalOrderReadBack: true },
    treatmentMedsOrderCompleted: true,
  };

  it("reports every item complete once every field is documented (Comfort Measures N/A when not clinically applicable)", () => {
    const coverage = computeOrdersPocDocumentationCoverage(COMPLETE_DATA, { hasTerminalDeclineEvidence: false });
    expect(coverage.every((i) => i.complete)).toBe(true);
    const comfort = coverage.find((i) => i.key === "comfortMeasures");
    expect(comfort.value).toBe("N/A");
    expect(comfort.state).toBe("not_applicable");
  });

  it("flags HA as incomplete, never Not Applicable, when a HA hasn't been assigned or marked N/A", () => {
    const coverage = computeOrdersPocDocumentationCoverage({ ...COMPLETE_DATA, haAssignment: {} }, {});
    const ha = coverage.find((i) => i.key === "ha");
    expect(ha.complete).toBe(false);
    expect(ha.unresolvedHint).toBeTruthy();
  });

  it("treats HA explicitly marked Not Applicable as complete/N/A", () => {
    const coverage = computeOrdersPocDocumentationCoverage({ ...COMPLETE_DATA, haAssignment: { notApplicable: true } }, {});
    const ha = coverage.find((i) => i.key === "ha");
    expect(ha.complete).toBe(true);
    expect(ha.value).toBe("N/A");
  });

  it("requires Comfort Measures to be documented once terminal-decline evidence exists", () => {
    const coverage = computeOrdersPocDocumentationCoverage(COMPLETE_DATA, { hasTerminalDeclineEvidence: true });
    const comfort = coverage.find((i) => i.key === "comfortMeasures");
    expect(comfort.complete).toBe(false);
    expect(comfort.unresolvedHint).toBeTruthy();
  });

  it("flags every item incomplete on a brand-new/empty record", () => {
    const coverage = computeOrdersPocDocumentationCoverage({}, { hasTerminalDeclineEvidence: false });
    const incompleteKeys = coverage.filter((i) => !i.complete).map((i) => i.key);
    expect(incompleteKeys).toEqual(expect.arrayContaining(["loc", "visitFrequency", "ha", "poc", "verbalOrder", "physicianOrder"]));
  });
});
