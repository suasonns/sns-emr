import { describe, it, expect } from "vitest";
import { INITIAL_FORM, validateRNICA } from "./RNICA.jsx";
import {
  summarizeEnvironmentalSafety,
  summarizeOxygenSafety,
  summarizeDisasterTriage,
  summarizeFallRisk,
  summarizeSafetyAssessment,
  getFirstIncompleteSafetyStepId,
  isFacilitySiteOfService,
  SAFETY_WIZARD_STEPS,
} from "./rn-ica/safety-clinical-risk/safetyLogic.js";

// PRODUCT OWNER DIRECTIVE "Replace the Inline Safety Page With Four
// Guided Assessments" (final), consolidated by PRODUCT OWNER DECISION
// "Safety Is One Assessment", then superseded by PRODUCT OWNER
// DIRECTIVE (2026-12-01) "Make Safety & Clinical Risk One Assessment" --
// proves the four underlying summaries (Environmental Safety, Fall
// Risk, Oxygen Safety, Disaster Triage) compute "complete" per the
// latest directive's expanded field set, that Oxygen Safety is now
// ALWAYS counted (never excluded even when Not Applicable, pending an
// explicit RN confirmation), that the single consolidated
// `summarizeSafetyAssessment` status model has all four states (Not
// Started / In Progress / Complete / Needs Review), and that
// `validateRNICA` now creates exactly ONE Safety Lock gate.

const COMPLETE_MORSE = {
  fallRiskMorseHistoryOfFalling: "No",
  fallRiskMorseSecondaryDiagnosis: "No",
  fallRiskMorseAmbulatoryAid: "None/Bed Rest/Nurse Assist",
  fallRiskMorseIvHeparinLock: "No",
  fallRiskMorseGaitTransferring: "Normal/Bedrest/Immobile",
  fallRiskMorseMentalStatus: "Oriented to Own Ability",
  // PRODUCT OWNER DECISION "Importing Prior Safety Assessments" -- adds a
  // SEPARATE "Hospice Clinical Fall Safety" precaution-level field
  // alongside (never merged into) the unchanged Morse score; required
  // for the Fall Risk step to be considered complete.
  hospiceClinicalFallSafetyLevel: "Standard Precautions",
};

// Minimal complete Environmental Safety for a clean (no-hazard) home visit --
// risk target/actions/disposition/follow-up are NOT required because
// `hasAnyHazard` is false.
const COMPLETE_ENVIRONMENTAL_HOME_CLEAN = {
  environmentalHomeConcerns: ["No Environmental Concerns Identified"],
  environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
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
  it("is complete for a clean home visit (no hazards) once both 'No Concern' selections are documented, with no Risk Target/Actions/Follow-Up required", () => {
    const summary = summarizeEnvironmentalSafety(COMPLETE_ENVIRONMENTAL_HOME_CLEAN, HOME_FULL_FORM_DATA);
    expect(summary.hasAnyHazard).toBe(false);
    expect(summary.complete).toBe(true);
    expect(summary.patientSummary).toBe("No Environmental Concerns Identified");
    expect(summary.staffSummary).toBe("No Staff Safety Concern Identified");
  });
  it("is incomplete with an active patient hazard until Risk Target, Actions Taken, and Follow-Up Required are also documented", () => {
    const partial = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["Lighting Concern"],
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      HOME_FULL_FORM_DATA
    );
    expect(partial.hasAnyHazard).toBe(true);
    expect(partial.complete).toBe(false);

    const complete = summarizeEnvironmentalSafety(
      {
        environmentalHomeConcerns: ["Lighting Concern"],
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
        environmentalRiskTarget: "Patient",
        environmentalActionsTaken: ["Education Provided"],
        environmentalFollowUpRequired: "No",
      },
      HOME_FULL_FORM_DATA
    );
    expect(complete.complete).toBe(true);
    expect(complete.patientHazards).toEqual(["Lighting Concern"]);
  });
  it("additionally requires Staff Visit Disposition when a staff hazard is identified", () => {
    const baseData = {
      environmentalHomeConcerns: ["No Environmental Concerns Identified"],
      environmentalStaffSafetyStatus: "Staff Safety Concern Identified",
      environmentalStaffSafetyHazards: ["Aggressive or uncontrolled animal"],
      environmentalRiskTarget: "Staff",
      environmentalActionsTaken: ["Caregiver Notified"],
      environmentalFollowUpRequired: "Yes",
    };
    const withoutDisposition = summarizeEnvironmentalSafety(baseData, HOME_FULL_FORM_DATA);
    expect(withoutDisposition.complete).toBe(false);

    const withDisposition = summarizeEnvironmentalSafety(
      { ...baseData, environmentalStaffDisposition: "Visit Modified for Safety" },
      HOME_FULL_FORM_DATA
    );
    expect(withDisposition.complete).toBe(true);
    expect(withDisposition.staffHazards).toEqual(["Aggressive or uncontrolled animal"]);
  });
  it("is incomplete for a facility until Facility Managed / Observed Concern is selected", () => {
    const summary = summarizeEnvironmentalSafety({}, FACILITY_FULL_FORM_DATA);
    expect(summary.setting).toBe("Facility");
    expect(summary.complete).toBe(false);
  });
  it("is complete for a facility once Facility Managed + staff visit safety are both documented (no hazard -> no additional fields required)", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalFacilityStatus: "Facility Managed",
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      FACILITY_FULL_FORM_DATA
    );
    expect(summary.patientSummary).toBe("Facility Managed");
    expect(summary.complete).toBe(true);
  });
});

describe("summarizeOxygenSafety", () => {
  it("is Not Applicable and incomplete when the patient is not on oxygen and the RN has not yet confirmed Not Applicable", () => {
    const summary = summarizeOxygenSafety({}, { respiratory: { oxygenTherapy: { inUse: false } } });
    expect(summary.applicable).toBe(false);
    expect(summary.complete).toBe(false);
    expect(summary.status).toBe("Not Applicable");
  });
  it("is complete once the RN explicitly confirms Not Applicable", () => {
    const summary = summarizeOxygenSafety(
      { oxygenSafetyConfirmedNotApplicable: true },
      { respiratory: { oxygenTherapy: { inUse: false } } }
    );
    expect(summary.applicable).toBe(false);
    expect(summary.complete).toBe(true);
    expect(summary.confirmedNotApplicable).toBe(true);
  });
  it("is incomplete when on oxygen but no concern status has been documented", () => {
    const summary = summarizeOxygenSafety({}, { respiratory: { oxygenTherapy: { inUse: true } } });
    expect(summary.applicable).toBe(true);
    expect(summary.complete).toBe(false);
  });
  it("is complete with 'No Concern' status when only 'No Concern' is selected (no actions/follow-up required)", () => {
    const summary = summarizeOxygenSafety(
      { oxygenSafetyConcerns: ["No Concern"] },
      { respiratory: { oxygenTherapy: { inUse: true } } }
    );
    expect(summary.complete).toBe(true);
    expect(summary.status).toBe("No Concern");
    expect(summary.concerns).toEqual([]);
  });
  it("is incomplete with an active concern until Actions Taken and Follow-Up Required are also documented", () => {
    const partial = summarizeOxygenSafety(
      { oxygenSafetyConcerns: ["Smoking Near Oxygen"] },
      { respiratory: { oxygenTherapy: { inUse: true } } }
    );
    expect(partial.status).toBe("Concern Identified");
    expect(partial.complete).toBe(false);

    const complete = summarizeOxygenSafety(
      {
        oxygenSafetyConcerns: ["Smoking Near Oxygen"],
        oxygenSafetyActionsTaken: ["Immediate Education Provided", "Caregiver Notified"],
        oxygenSafetyFollowUpRequired: "Required",
      },
      { respiratory: { oxygenTherapy: { inUse: true } } }
    );
    expect(complete.complete).toBe(true);
    expect(complete.concerns).toEqual(["Smoking Near Oxygen"]);
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
  it("is incomplete with only a level -- Planned Placement and Transportation Status are also required", () => {
    const partial = summarizeDisasterTriage({
      disasterLevel: "Level 2 — Hospice must contact to assure adequate assistance; limited assistance available",
      disasterLevelTwoConditions: ["Lives above ground floor"],
    });
    expect(partial.complete).toBe(false);
    expect(partial.shortLabel).toBe("Level 2");
    expect(partial.conditions).toEqual(["Lives above ground floor"]);
  });
  it("is complete once level, planned placement, and transportation status are all documented", () => {
    const summary = summarizeDisasterTriage({
      disasterLevel: "Level 2 — Hospice must contact to assure adequate assistance; limited assistance available",
      disasterLevelTwoConditions: ["Lives above ground floor"],
      disasterPlannedPlacement: "Remain at Residence",
      disasterResponsibleSupport: "Daughter (lives nearby)",
      disasterTransportationStatus: "Reliable Transportation Available",
    });
    expect(summary.complete).toBe(true);
    expect(summary.plannedPlacement).toBe("Remain at Residence");
    expect(summary.transportationStatus).toBe("Reliable Transportation Available");
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
  // PRODUCT OWNER DECISION "Importing Prior Safety Assessments" -- Morse
  // scoring itself is UNCHANGED (including "Bedbound = Score 0"); but a
  // SEPARATE "Hospice Clinical Fall Safety" precaution-level answer is now
  // ALSO required before the Fall Risk step counts as complete.
  it("is NOT complete when all 6 Morse factors are answered but Hospice Clinical Fall Safety precaution level is missing", () => {
    const { hospiceClinicalFallSafetyLevel, ...morseOnly } = COMPLETE_MORSE;
    const summary = summarizeFallRisk(morseOnly);
    expect(summary.total).toBe(0);
    expect(summary.classification).toBe("Low Risk");
    expect(summary.precautionLevel).toBe("");
    expect(summary.complete).toBe(false);
  });
  it("exposes the Hospice Clinical Fall Safety precaution level separately from the unchanged Morse score", () => {
    const summary = summarizeFallRisk(COMPLETE_MORSE);
    expect(summary.precautionLevel).toBe("Standard Precautions");
    expect(summary.total).toBe(0);
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

function fullyCompleteSafetyData() {
  return {
    ...COMPLETE_MORSE,
    ...COMPLETE_ENVIRONMENTAL_HOME_CLEAN,
    oxygenSafetyConfirmedNotApplicable: true,
    disasterLevel: "Level 3 — No need for hospice to assist; has adequate assistance available",
    disasterPlannedPlacement: "Remain at Residence",
    disasterTransportationStatus: "Reliable Transportation Available",
  };
}

describe("validateRNICA -- single consolidated Safety & Clinical Risk gate", () => {
  it("blocks Lock with one safety.assessment error when nothing has been documented", () => {
    const { errors } = validateRNICA(baseFormData(), "ica");
    expect(errors["safety.assessment"]).toBeTruthy();
  });

  it("does not require Patient Safety, Caregiver Safety, Safety Notes, DME, or Supplies to finalize", () => {
    const { errors } = validateRNICA(baseFormData(), "ica");
    expect(Object.keys(errors).some((k) => /patientSafety|caregiverSafety|safetyNotes|dme|supplies/i.test(k))).toBe(false);
  });

  it("clears safety.assessment once Environmental, Morse, Oxygen (confirmed N/A), and Disaster are all complete", () => {
    const completeFormData = baseFormData();
    completeFormData.safety = { ...completeFormData.safety, ...fullyCompleteSafetyData() };
    const { errors } = validateRNICA(completeFormData, "ica");
    expect(errors["safety.assessment"]).toBeUndefined();
  });

  it("does NOT require the Review & Complete submission (safetyAssessmentCompletedAt) to clear Lock", () => {
    const completeFormData = baseFormData();
    completeFormData.safety = { ...completeFormData.safety, ...fullyCompleteSafetyData() };
    // Deliberately no safetyAssessmentCompletedAt -- Lock reads allPartsComplete, not the UI submission flag.
    expect(completeFormData.safety.safetyAssessmentCompletedAt).toBeUndefined();
    const { errors } = validateRNICA(completeFormData, "ica");
    expect(errors["safety.assessment"]).toBeUndefined();
  });
});

// PRODUCT OWNER DIRECTIVE (2026-12-01) "Make Safety & Clinical Risk One
// Assessment" -- proves the 4-state status model, that Oxygen Safety is
// now ALWAYS counted (never excluded even when Not Applicable), and the
// deep-link helper used by validation/Edit Assessment navigation.
describe("summarizeSafetyAssessment -- single consolidated Safety record with 4-state status", () => {
  it("reports Not Started when nothing has been documented, counting all 4 parts including the inapplicable Oxygen step", () => {
    const formData = baseFormData();
    const summary = summarizeSafetyAssessment(formData.safety, formData);
    expect(summary.oxygen.applicable).toBe(false);
    expect(summary.status).toBe("Not Started");
    expect(summary.totalCount).toBe(4);
    expect(summary.completedCount).toBe(0);
  });

  it("reports In Progress when some but not all parts are documented", () => {
    const formData = baseFormData();
    formData.safety = {
      ...formData.safety,
      ...COMPLETE_MORSE,
      disasterLevel: "Level 3 — No need for hospice to assist; has adequate assistance available",
      disasterPlannedPlacement: "Remain at Residence",
      disasterTransportationStatus: "Reliable Transportation Available",
    };
    const summary = summarizeSafetyAssessment(formData.safety, formData);
    expect(summary.fallRisk.complete).toBe(true);
    expect(summary.disaster.complete).toBe(true);
    expect(summary.environmental.complete).toBe(false);
    expect(summary.status).toBe("In Progress");
    expect(summary.complete).toBe(false);
  });

  it("stays 'In Progress' (not 'Complete') once every part is answered but the RN has not yet clicked Complete Safety Assessment", () => {
    const formData = baseFormData();
    formData.safety = { ...formData.safety, ...fullyCompleteSafetyData() };
    const summary = summarizeSafetyAssessment(formData.safety, formData);
    expect(summary.allPartsComplete).toBe(true);
    expect(summary.completedAt).toBe("");
    expect(summary.status).toBe("In Progress");
    expect(summary.complete).toBe(false);
  });

  it("reports Complete only once every part is documented AND the RN has submitted via safetyAssessmentCompletedAt", () => {
    const formData = baseFormData();
    formData.safety = { ...formData.safety, ...fullyCompleteSafetyData(), safetyAssessmentCompletedAt: "2026-12-01T00:00:00.000Z" };
    const summary = summarizeSafetyAssessment(formData.safety, formData);
    expect(summary.totalCount).toBe(4);
    expect(summary.completedCount).toBe(4);
    expect(summary.allPartsComplete).toBe(true);
    expect(summary.complete).toBe(true);
    expect(summary.status).toBe("Complete");
  });

  it("reports Needs Review when a previously-submitted assessment's data has since become incomplete again", () => {
    const formData = baseFormData();
    formData.safety = {
      ...formData.safety,
      ...fullyCompleteSafetyData(),
      safetyAssessmentCompletedAt: "2026-12-01T00:00:00.000Z",
      // Drift: an Environmental field was cleared back out after submission.
      environmentalHomeConcerns: [],
    };
    const summary = summarizeSafetyAssessment(formData.safety, formData);
    expect(summary.allPartsComplete).toBe(false);
    expect(summary.status).toBe("Needs Review");
  });

  it("exposes exactly the five SAFETY_WIZARD_STEPS in Environmental -> Fall Risk -> Oxygen -> Disaster -> Review order", () => {
    expect(SAFETY_WIZARD_STEPS.map((s) => s.id)).toEqual([
      "environmental",
      "fallRisk",
      "oxygen",
      "disaster",
      "review",
    ]);
  });
});

describe("getFirstIncompleteSafetyStepId", () => {
  it("returns 'environmental' when nothing is documented", () => {
    const formData = baseFormData();
    const summary = summarizeSafetyAssessment(formData.safety, formData);
    expect(getFirstIncompleteSafetyStepId(summary)).toBe("environmental");
  });
  it("returns the next incomplete step in order once earlier steps are complete", () => {
    const formData = baseFormData();
    formData.safety = { ...formData.safety, ...COMPLETE_ENVIRONMENTAL_HOME_CLEAN, ...COMPLETE_MORSE };
    const summary = summarizeSafetyAssessment(formData.safety, formData);
    expect(getFirstIncompleteSafetyStepId(summary)).toBe("oxygen");
  });
  it("returns 'review' once every part is complete", () => {
    const formData = baseFormData();
    formData.safety = { ...formData.safety, ...fullyCompleteSafetyData() };
    const summary = summarizeSafetyAssessment(formData.safety, formData);
    expect(getFirstIncompleteSafetyStepId(summary)).toBe("review");
  });
});
