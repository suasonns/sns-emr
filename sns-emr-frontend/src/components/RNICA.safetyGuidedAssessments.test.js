import { describe, it, expect } from "vitest";
import { INITIAL_FORM, validateRNICA } from "./RNICA.jsx";
import {
  summarizeEnvironmentalSafety,
  summarizeOxygenSafety,
  summarizeDisasterTriage,
  summarizeFallRisk,
  isFacilitySiteOfService,
} from "./rn-ica/safety-clinical-risk/safetyLogic.js";

// PRODUCT OWNER DIRECTIVE "Replace the Inline Safety Page With Four
// Guided Assessments" (final) -- proves the four new guided-assessment
// summaries (Environmental Safety, Fall Risk, Oxygen Safety, Disaster
// Triage) compute "complete" the same way the new SafetyAssessmentOverview
// badges and the validateRNICA Lock gates both read, and that the
// explicitly-removed main-page items (Patient Safety, Caregiver Safety,
// Safety Notes, DME, Supplies) are NOT required to finalize.

const COMPLETE_MORSE = {
  fallRiskMorseHistoryOfFalling: "No",
  fallRiskMorseSecondaryDiagnosis: "No",
  fallRiskMorseAmbulatoryAid: "None/Bed Rest/Nurse Assist",
  fallRiskMorseIvHeparinLock: "No",
  fallRiskMorseGaitTransferring: "Normal/Bedrest/Immobile",
  fallRiskMorseMentalStatus: "Oriented to Own Ability",
};

const HOME_FULL_FORM_DATA = { demographics: { livingSituation: { siteOfService: "01" } } };
const FACILITY_FULL_FORM_DATA = { demographics: { livingSituation: { siteOfService: "02" } } };

describe("isFacilitySiteOfService", () => {
  it("treats '01' (Patient's Home/Residence) as not-a-facility", () => {
    expect(isFacilitySiteOfService(HOME_FULL_FORM_DATA)).toBe(false);
  });
  it("treats any other site-of-service code as a facility", () => {
    expect(isFacilitySiteOfService(FACILITY_FULL_FORM_DATA)).toBe(true);
  });
  it("treats an empty/unset site of service as not-a-facility", () => {
    expect(isFacilitySiteOfService({})).toBe(false);
  });
});

describe("summarizeEnvironmentalSafety", () => {
  it("is incomplete for a home residence with neither a concern nor 'No Environmental Concerns Identified'", () => {
    const summary = summarizeEnvironmentalSafety({}, HOME_FULL_FORM_DATA);
    expect(summary.setting).toBe("Home");
    expect(summary.complete).toBe(false);
  });
  it("is complete for a home residence once 'No Environmental Concerns Identified' + staff safety are both documented", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["No Environmental Concerns Identified"],
        environmentalStaffVisitSafety: ["No Staff Safety Concerns Identified"],
      },
      HOME_FULL_FORM_DATA
    );
    expect(summary.complete).toBe(true);
    expect(summary.patientSummary).toBe("No Environmental Concerns Identified");
    expect(summary.staffSummary).toBe("No Staff Safety Concerns Identified");
  });
  it("is complete for a home residence with an active hazard + staff hazard documented", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["Lighting Concern"],
        environmentalStaffVisitSafety: ["Aggressive Animal"],
      },
      HOME_FULL_FORM_DATA
    );
    expect(summary.complete).toBe(true);
    expect(summary.patientHazards).toEqual(["Lighting Concern"]);
    expect(summary.staffHazards).toEqual(["Aggressive Animal"]);
  });
  it("is incomplete for a facility until Facility Managed / Observed Concern is selected", () => {
    const summary = summarizeEnvironmentalSafety({}, FACILITY_FULL_FORM_DATA);
    expect(summary.setting).toBe("Facility");
    expect(summary.complete).toBe(false);
  });
  it("is complete for a facility once Facility Managed is selected (even with no staff concern documented is still required)", () => {
    const summary = summarizeEnvironmentalSafety(
      { environmentalFacilityStatus: "Facility Managed" },
      FACILITY_FULL_FORM_DATA
    );
    expect(summary.patientSummary).toBe("Facility Managed");
    expect(summary.complete).toBe(false); // staff visit safety still undocumented
  });
  it("requires BOTH patient and staff hazard documentation to be complete", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalFacilityStatus: "Facility Managed",
        environmentalStaffVisitSafety: ["No Staff Safety Concerns Identified"],
      },
      FACILITY_FULL_FORM_DATA
    );
    expect(summary.complete).toBe(true);
  });
});

describe("summarizeOxygenSafety", () => {
  it("is Not Applicable (and complete) when the patient is not on oxygen", () => {
    const summary = summarizeOxygenSafety({}, { respiratory: { oxygenTherapy: { inUse: false } } });
    expect(summary.applicable).toBe(false);
    expect(summary.complete).toBe(true);
    expect(summary.status).toBe("Not Applicable");
  });
  it("is incomplete when on oxygen but no concern status has been documented", () => {
    const summary = summarizeOxygenSafety({}, { respiratory: { oxygenTherapy: { inUse: true } } });
    expect(summary.applicable).toBe(true);
    expect(summary.complete).toBe(false);
  });
  it("is complete with 'No Concern' status when only 'No Concern' is selected", () => {
    const summary = summarizeOxygenSafety(
      { oxygenSafetyConcerns: ["No Concern"] },
      { respiratory: { oxygenTherapy: { inUse: true } } }
    );
    expect(summary.complete).toBe(true);
    expect(summary.status).toBe("No Concern");
    expect(summary.concerns).toEqual([]);
  });
  it("is complete with 'Concern Identified' status when an active concern is selected", () => {
    const summary = summarizeOxygenSafety(
      { oxygenSafetyConcerns: ["Smoking Near Oxygen"] },
      { respiratory: { oxygenTherapy: { inUse: true } } }
    );
    expect(summary.complete).toBe(true);
    expect(summary.status).toBe("Concern Identified");
    expect(summary.concerns).toEqual(["Smoking Near Oxygen"]);
  });
  it("falls back to the legacy safety.oxygenInUse flag when respiratory.oxygenTherapy.inUse is unset", () => {
    const summary = summarizeOxygenSafety({ oxygenInUse: true }, {});
    expect(summary.applicable).toBe(true);
  });
});

describe("summarizeDisasterTriage", () => {
  it("is incomplete until a disaster level is selected", () => {
    expect(summarizeDisasterTriage({}).complete).toBe(false);
  });
  it("is complete once a level is selected, with the matching conditions list", () => {
    const summary = summarizeDisasterTriage({
      disasterLevel: "Level 2 — Hospice must contact to assure adequate assistance; limited assistance available",
      disasterLevelTwoConditions: ["Lives above ground floor"],
    });
    expect(summary.complete).toBe(true);
    expect(summary.shortLabel).toBe("Level 2");
    expect(summary.conditions).toEqual(["Lives above ground floor"]);
  });
});

describe("summarizeFallRisk", () => {
  it("is incomplete until all 6 Morse factors are answered", () => {
    expect(summarizeFallRisk({}).complete).toBe(false);
  });
  it("is complete with score/classification once all 6 Morse factors are answered", () => {
    const summary = summarizeFallRisk(COMPLETE_MORSE);
    expect(summary.complete).toBe(true);
    expect(summary.total).toBe(0);
    expect(summary.classification).toBe("Low Risk");
  });
});

function baseFormData() {
  return {
    ...INITIAL_FORM,
    demographics: { ...INITIAL_FORM.demographics, livingSituation: { ...INITIAL_FORM.demographics?.livingSituation, siteOfService: "01" } },
    respiratory: { ...INITIAL_FORM.respiratory },
    safety: { ...INITIAL_FORM.safety },
  };
}

describe("validateRNICA -- four guided Safety & Clinical Risk gates", () => {
  it("blocks Lock when Environmental Safety, Oxygen Safety, and Disaster Triage are all undocumented", () => {
    const { errors } = validateRNICA(baseFormData(), "ica");
    expect(errors["safety.environmentalSafety"]).toBeTruthy();
    expect(errors["safety.disasterTriage"]).toBeTruthy();
    // Oxygen Safety is Not Applicable by default (no oxygen in use), so it is NOT a blocker here.
    expect(errors["safety.oxygenSafety"]).toBeUndefined();
  });

  it("does not require Patient Safety, Caregiver Safety, Safety Notes, DME, or Supplies to finalize", () => {
    const { errors } = validateRNICA(baseFormData(), "ica");
    expect(Object.keys(errors).some((k) => /patientSafety|caregiverSafety|safetyNotes|dme|supplies/i.test(k))).toBe(false);
  });

  it("clears the Environmental Safety / Oxygen Safety / Disaster Triage gates once all three are documented", () => {
    const completeFormData = baseFormData();
    completeFormData.respiratory.oxygenTherapy = { ...completeFormData.respiratory.oxygenTherapy, inUse: true };
    completeFormData.safety = {
      ...completeFormData.safety,
      ...COMPLETE_MORSE,
      environmentalHomeConcerns: ["No Environmental Concerns Identified"],
      environmentalStaffVisitSafety: ["No Staff Safety Concerns Identified"],
      oxygenSafetyConcerns: ["No Concern"],
      disasterLevel: "Level 3 — No need for hospice to assist; has adequate assistance available",
    };
    const { errors } = validateRNICA(completeFormData, "ica");
    expect(errors["safety.environmentalSafety"]).toBeUndefined();
    expect(errors["safety.oxygenSafety"]).toBeUndefined();
    expect(errors["safety.disasterTriage"]).toBeUndefined();
    expect(errors["safety.fallRiskMorse"]).toBeUndefined();
  });
});
