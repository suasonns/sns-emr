import { describe, it, expect } from "vitest";
import { summarizeEnvironmentalSafety } from "./rn-ica/safety-clinical-risk/safetyLogic.js";

// PRODUCT OWNER DIRECTIVE "Checkpoint 3: Environmental Safety Summary
// Accuracy" (2026-10-24) -- the main Safety card previously displayed
// clinically meaningless placeholders ("Observed Concern", bare
// "Facility Managed"); the RN must be able to read what was actually
// found without reopening the assessment. These tests cover ONLY the
// new `cardSummary`/`staffCardSummary`/`settingLabel`/`settingChanged`/
// `unableToAssessReason` fields added to `summarizeEnvironmentalSafety`
// for this checkpoint -- `patientSummary`/`staffSummary` (the pre-
// existing fields used by the Review & Complete step and the prior-
// assessment import banner) are intentionally left unchanged and remain
// covered by RNICA.safetyGuidedAssessments.test.js.

const HOME_FULL_FORM_DATA = { demographics: { livingSituation: { siteOfService: "01" } } };
const ASSISTED_LIVING_FULL_FORM_DATA = { demographics: { livingSituation: { siteOfService: "02" } } };

describe("summarizeEnvironmentalSafety -- Checkpoint 3 card summaries", () => {
  it("1. Home, No Concern -- names the setting and the explicit no-concern finding", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["No Environmental Concerns Identified"],
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      HOME_FULL_FORM_DATA
    );
    expect(summary.cardSummary).toBe("Private Home — No Environmental Concern Identified");
  });

  it("2. Home, single concern -- names the actual hazard, never 'Observed Concern'", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["Clutter / Obstructed Walkway"],
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      HOME_FULL_FORM_DATA
    );
    expect(summary.cardSummary).toBe("Private Home — Clutter / Obstructed Walkway");
    expect(summary.cardSummary).not.toMatch(/Observed Concern/);
  });

  it("3. Home, multiple concerns -- all named hazards appear in the condensed summary", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["Clutter / Obstructed Walkway", "Smoking Concern"],
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      HOME_FULL_FORM_DATA
    );
    expect(summary.cardSummary).toBe("Private Home — Clutter / Obstructed Walkway; Smoking Concern");
  });

  it("4. Facility, No Concern -- names the facility type, never bare 'Facility Managed'", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalFacilityStatus: "Facility Managed",
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      ASSISTED_LIVING_FULL_FORM_DATA
    );
    expect(summary.cardSummary).toBe("Assisted Living — Facility Managed, No Observed Concern");
    expect(summary.cardSummary).not.toBe("Facility Managed");
  });

  it("5. Facility, with concern -- names the actual facility hazards, never bare 'Observed Concern'", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalFacilityStatus: "Observed Concern",
        environmentalFacilityConcerns: ["Call Light Concern", "Evacuation Access Concern"],
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      ASSISTED_LIVING_FULL_FORM_DATA
    );
    expect(summary.cardSummary).toBe("Assisted Living — Call Light Concern; Evacuation Access Concern");
    expect(summary.cardSummary).not.toMatch(/^Assisted Living — Observed Concern$/);
  });

  it("5b. Facility, concern selected but no sub-hazard chosen yet -- never falls back to meaningless 'Observed Concern'", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalFacilityStatus: "Observed Concern",
        environmentalFacilityConcerns: [],
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      ASSISTED_LIVING_FULL_FORM_DATA
    );
    expect(summary.cardSummary).toBe("");
    expect(summary.cardSummary).not.toMatch(/Observed Concern/);
  });

  it("6. Staff Visit Safety -- names the actual hazard; 'No Concern Identified' only when explicitly confirmed clear", () => {
    const noConcern = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["No Environmental Concerns Identified"],
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      HOME_FULL_FORM_DATA
    );
    expect(noConcern.staffCardSummary).toBe("No Concern Identified");

    const withConcern = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["No Environmental Concerns Identified"],
        environmentalStaffSafetyStatus: "Staff Safety Concern Identified",
        environmentalStaffSafetyHazards: ["Aggressive or uncontrolled animal"],
      },
      HOME_FULL_FORM_DATA
    );
    expect(withConcern.staffCardSummary).toBe("Aggressive or uncontrolled animal");
    expect(withConcern.staffCardSummary).not.toMatch(/^Staff Safety Concern$/);
  });

  it("7. Home -> Facility change -- old Home data never shown as current; Needs Review message instead", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["Clutter / Obstructed Walkway"],
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      ASSISTED_LIVING_FULL_FORM_DATA // now resolved as Facility, Facility fields never answered
    );
    expect(summary.settingChanged).toBe(true);
    expect(summary.cardSummary).toBe("Needs Review — Place of Service Changed");
  });

  it("8. Facility -> Home change -- old Facility data never shown as current; Needs Review message instead", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalFacilityStatus: "Observed Concern",
        environmentalFacilityConcerns: ["Call Light Concern"],
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      HOME_FULL_FORM_DATA // now resolved as Home, Home fields never answered
    );
    expect(summary.settingChanged).toBe(true);
    expect(summary.cardSummary).toBe("Needs Review — Place of Service Changed");
  });

  it("9. Historical values never leak into the current summary after a setting change", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalFacilityStatus: "Observed Concern",
        environmentalFacilityConcerns: ["Call Light Concern"],
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      HOME_FULL_FORM_DATA
    );
    expect(summary.cardSummary).not.toMatch(/Call Light Concern/);
    expect(summary.patientHazards).toEqual([]);
  });

  it("10. Unable to Assess requires a named reason -- blank reason is never complete or displayed as documented", () => {
    const blankReason = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["No Environmental Concerns Identified"],
        environmentalStaffSafetyStatus: "Unable to Assess",
      },
      HOME_FULL_FORM_DATA
    );
    expect(blankReason.complete).toBe(false);
    expect(blankReason.unableToAssessReason).toBe("");
    expect(blankReason.staffCardSummary).toBe("Unable to Assess");

    const withReason = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["No Environmental Concerns Identified"],
        environmentalStaffSafetyStatus: "Unable to Assess",
        environmentalUnableToAssessReason: "Immediate Staff-Safety Concern",
      },
      HOME_FULL_FORM_DATA
    );
    expect(withReason.complete).toBe(true);
    expect(withReason.unableToAssessReason).toBe("Immediate Staff-Safety Concern");
    expect(withReason.cardSummary).toBe("Unable To Assess — Immediate Staff-Safety Concern");
    expect(withReason.staffCardSummary).toBe("Unable to Assess — Immediate Staff-Safety Concern");
  });

  it("10b. Unable to Assess 'Other' reason requires the free-text explanation", () => {
    const blankOther = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["No Environmental Concerns Identified"],
        environmentalStaffSafetyStatus: "Unable to Assess",
        environmentalUnableToAssessReason: "Other",
      },
      HOME_FULL_FORM_DATA
    );
    expect(blankOther.complete).toBe(false);
    expect(blankOther.unableToAssessReason).toBe("");

    const withOther = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["No Environmental Concerns Identified"],
        environmentalStaffSafetyStatus: "Unable to Assess",
        environmentalUnableToAssessReason: "Other",
        environmentalUnableToAssessOther: "Patient actively combative on arrival",
      },
      HOME_FULL_FORM_DATA
    );
    expect(withOther.complete).toBe(true);
    expect(withOther.unableToAssessReason).toBe("Patient actively combative on arrival");
  });

  it("11. Save/reload preserves summaries -- re-deriving from the same stored data is idempotent", () => {
    const safetyData = {
      environmentalHomeConcerns: ["Clutter / Obstructed Walkway", "Smoking Concern"],
      environmentalStaffSafetyStatus: "Staff Safety Concern Identified",
      environmentalStaffSafetyHazards: ["Unsecured weapon"],
      environmentalRiskTarget: "Patient",
      environmentalActionsTaken: ["Education Provided"],
      environmentalStaffDisposition: "Visit Modified for Safety",
      environmentalFollowUpRequired: "No",
    };
    const first = summarizeEnvironmentalSafety(safetyData, HOME_FULL_FORM_DATA);
    const reloaded = summarizeEnvironmentalSafety(JSON.parse(JSON.stringify(safetyData)), HOME_FULL_FORM_DATA);
    expect(reloaded).toEqual(first);
    expect(reloaded.cardSummary).toBe("Private Home — Clutter / Obstructed Walkway; Smoking Concern");
    expect(reloaded.staffCardSummary).toBe("Unsecured weapon");
  });
});
