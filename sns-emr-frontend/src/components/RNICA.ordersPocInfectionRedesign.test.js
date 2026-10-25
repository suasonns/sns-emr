import { describe, it, expect } from "vitest";
import {
  getHaAssignmentStatus,
  getInitialPocStatus,
  getComfortMeasuresStatus,
  isVisitFrequencyConfigured,
  computeOrdersPocDocumentationCoverage,
  visitFrequencyPillFromRow,
  visitFrequencyRowFromPill,
} from "./RNICA.jsx";

// PRODUCT OWNER DIRECTIVE (2026-10-25) "Orders & POC Still Does Not
// Follow Infection Design" -- proves the pure derivation/coverage
// helpers that power the Infection-style redesign (Documentation
// Coverage summary pills, HA/Initial-POC/Comfort-Measures state pills,
// Visit Frequency pill<->row mapping). UI rendering itself is exercised
// by the project's existing manual/live-browser verification process
// (per established session convention); these tests lock in the pure
// business logic so it can't silently regress.

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
    expect(isVisitFrequencyConfigured([{ discipline: "SN", numberOfVisits: "", period: "" }])).toBe(false);
  });
  it("is true once at least one row has a structured count+period", () => {
    expect(isVisitFrequencyConfigured([{ discipline: "SN", numberOfVisits: "3", period: "per Week" }])).toBe(true);
  });
  it("is true for a free-text 'specify' override even with no structured count/period", () => {
    expect(isVisitFrequencyConfigured([{ discipline: "SN", specify: "within 5 days of admission" }])).toBe(true);
  });
});

describe("visitFrequencyPillFromRow / visitFrequencyRowFromPill", () => {
  it("round-trips every named pill through its row shape", () => {
    for (const pill of ["DAILY", "5X_WEEK", "3X_WEEK", "2X_WEEK", "1X_WEEK", "PRN"]) {
      const row = visitFrequencyRowFromPill(pill);
      expect(visitFrequencyPillFromRow(row)).toBe(pill);
    }
  });
  it("maps a Custom pill to the free-text 'specify' field", () => {
    const row = visitFrequencyRowFromPill("CUSTOM", "RECERT and PRN");
    expect(row.specify).toBe("RECERT and PRN");
    expect(visitFrequencyPillFromRow(row)).toBe("CUSTOM");
  });
  it("shows a previously-charted non-standard count/period combination as Custom rather than hiding it", () => {
    expect(visitFrequencyPillFromRow({ numberOfVisits: "4", period: "per Week" })).toBe("CUSTOM");
  });
  it("shows nothing selected for a never-touched row", () => {
    expect(visitFrequencyPillFromRow({ discipline: "SN", numberOfVisits: "", period: "", specify: "" })).toBe("");
    expect(visitFrequencyPillFromRow(null)).toBe("");
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
