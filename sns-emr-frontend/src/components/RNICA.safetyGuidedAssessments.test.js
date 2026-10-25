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
  it("is incomplete with only a level -- the full Emergency Support Assessment is also required", () => {
    const partial = summarizeDisasterTriage({
      disasterLevel: "Level 2 — Hospice must contact to assure adequate assistance; limited assistance available",
      disasterLevelTwoConditions: ["Lives above ground floor"],
    });
    expect(partial.complete).toBe(false);
    expect(partial.shortLabel).toBe("Level 2");
    expect(partial.conditions).toEqual(["Lives above ground floor"]);
  });
  it("is complete once level and the full Emergency Support Assessment are documented, even with an unknown Preferred Emergency Location and no Responsible Support", () => {
    const summary = summarizeDisasterTriage({
      disasterLevel: "Level 2 — Hospice must contact to assure adequate assistance; limited assistance available",
      disasterLevelTwoConditions: ["Lives above ground floor"],
      disasterLivesAlone: "No",
      disasterRequiresEvacuationAssistance: "No",
      disasterCaregiverAvailable: "Yes",
      disasterTransportationAvailable: "Yes",
      disasterRequiresElectricity: "No",
      disasterOxygenDependent: "No",
      disasterBackupPowerAvailable: "Unknown",
      disasterPreferredEmergencyLocation: "Unknown",
    });
    expect(summary.complete).toBe(true);
    expect(summary.caregiverAvailable).toBe("Yes");
    expect(summary.transportationAvailable).toBe("Yes");
    expect(summary.preferredEmergencyLocation).toBe("Unknown");
    expect(summary.responsibleSupport).toBe("");
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
    disasterLivesAlone: "No",
    disasterRequiresEvacuationAssistance: "No",
    disasterCaregiverAvailable: "Yes",
    disasterTransportationAvailable: "Yes",
    disasterRequiresElectricity: "No",
    disasterOxygenDependent: "No",
    disasterBackupPowerAvailable: "Unknown",
    disasterPreferredEmergencyLocation: "Remain at Residence",
    disasterResponsibleSupport: "Daughter (lives nearby)",
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
      disasterLivesAlone: "No",
      disasterRequiresEvacuationAssistance: "No",
      disasterCaregiverAvailable: "Yes",
      disasterTransportationAvailable: "Yes",
      disasterRequiresElectricity: "No",
      disasterOxygenDependent: "No",
      disasterBackupPowerAvailable: "Unknown",
      disasterPreferredEmergencyLocation: "Remain at Residence",
      disasterResponsibleSupport: "Daughter (lives nearby)",
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

// PRODUCT OWNER DEFECT (2026-10-24) "Current Safety Completion Logic Is
// Invalid" -- a field may be Completed, Not Applicable, or Incomplete,
// NEVER "Complete" + "Not Yet Documented" simultaneously. These tests
// cover the exact 5 scenarios the PO required for Environmental/Oxygen
// Safety, verifying both (a) the completion boolean is correct and (b)
// the exposed "is this field even required" flags the Review screen
// keys off (`hasAnyHazard`, `staffDispositionRequired`,
// `hasActiveConcern`) are correct, so a correctly-skipped field never
// renders "Not Yet Documented" under a "Complete" badge. Scenarios
// 6-8 (plus the trailing Responsible Support test) cover the later
// PRODUCT OWNER DIRECTIVE "Fix Disaster Triage and Review-Step
// Completion Logic" -- Disaster Triage's required-field verification
// list (Unknown Preferred Emergency Location, Unknown transportation,
// Unknown caregiver availability, oxygen/electricity-dependent,
// lives-alone), none of which require a predicted future placement or
// a named Responsible Support to reach Complete.
describe("Safety completion logic never mixes Complete with Not Yet Documented (PO defect fix)", () => {
  it("1. Facility Managed, no staff concern -- Complete, with Risk Target/Actions/Disposition/Follow-Up all correctly NOT required", () => {
    const summary = summarizeEnvironmentalSafety(
      {
        environmentalFacilityStatus: "Facility Managed",
        environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
      },
      FACILITY_FULL_FORM_DATA
    );
    expect(summary.complete).toBe(true);
    expect(summary.hasAnyHazard).toBe(false);
    expect(summary.staffDispositionRequired).toBe(false);
  });

  it("2. Home, No Concern -- Complete, with Risk Target/Actions/Disposition/Follow-Up all correctly NOT required", () => {
    const summary = summarizeEnvironmentalSafety(COMPLETE_ENVIRONMENTAL_HOME_CLEAN, HOME_FULL_FORM_DATA);
    expect(summary.complete).toBe(true);
    expect(summary.hasAnyHazard).toBe(false);
    expect(summary.staffDispositionRequired).toBe(false);
  });

  it("3. Staff Concern Present -- Risk Target/Actions/Follow-Up AND Staff Disposition all become genuinely required, and the step is Incomplete until every one of them is documented", () => {
    const base = {
      environmentalHomeConcerns: ["No Environmental Concerns Identified"],
      environmentalStaffSafetyStatus: "Staff Safety Concern Identified",
      environmentalStaffSafetyHazards: ["Firearm concern"],
    };
    const missingAll = summarizeEnvironmentalSafety(base, HOME_FULL_FORM_DATA);
    expect(missingAll.hasAnyHazard).toBe(true);
    expect(missingAll.staffDispositionRequired).toBe(true);
    expect(missingAll.complete).toBe(false);

    const fullyDocumented = summarizeEnvironmentalSafety(
      {
        ...base,
        environmentalRiskTarget: "Staff",
        environmentalActionsTaken: ["Law Enforcement Notified"],
        environmentalStaffDisposition: "Visit Terminated Early",
        environmentalFollowUpRequired: "Yes",
      },
      HOME_FULL_FORM_DATA
    );
    expect(fullyDocumented.complete).toBe(true);
  });

  it("4. Oxygen No Concern -- Complete, with Concerns/Actions/Follow-Up correctly NOT required (rendered as 'None'/'N/A', never 'Not Yet Documented')", () => {
    const summary = summarizeOxygenSafety(
      { oxygenSafetyConcerns: ["No Concern"] },
      { respiratory: { oxygenTherapy: { inUse: true } } }
    );
    expect(summary.applicable).toBe(true);
    expect(summary.status).toBe("No Concern");
    expect(summary.hasActiveConcern).toBe(false);
    expect(summary.complete).toBe(true);
  });

  it("5. Oxygen Concern Present -- Actions Taken and Follow-Up become genuinely required, and the step is Incomplete until both are documented", () => {
    const missing = summarizeOxygenSafety(
      { oxygenSafetyConcerns: ["Smoking Near Oxygen"] },
      { respiratory: { oxygenTherapy: { inUse: true } } }
    );
    expect(missing.hasActiveConcern).toBe(true);
    expect(missing.complete).toBe(false);

    const complete = summarizeOxygenSafety(
      {
        oxygenSafetyConcerns: ["Smoking Near Oxygen"],
        oxygenSafetyActionsTaken: ["Immediate Education Provided", "Caregiver Notified"],
        oxygenSafetyFollowUpRequired: "Yes",
      },
      { respiratory: { oxygenTherapy: { inUse: true } } }
    );
    expect(complete.complete).toBe(true);
  });

  it("6. Disaster assessment can be Complete without any known future Preferred Emergency Location or Responsible Support -- both are optional and 'Unknown'/blank are acceptable, non-blocking answers", () => {
    const summary = summarizeDisasterTriage({
      disasterLevel: "Level 2 — Hospice must contact to assure adequate assistance; limited assistance available",
      disasterLivesAlone: "No",
      disasterRequiresEvacuationAssistance: "No",
      disasterCaregiverAvailable: "Yes",
      disasterTransportationAvailable: "Yes",
      disasterRequiresElectricity: "No",
      disasterOxygenDependent: "No",
      disasterBackupPowerAvailable: "Yes",
      disasterPreferredEmergencyLocation: "Unknown",
      // disasterResponsibleSupport intentionally omitted
    });
    expect(summary.preferredEmergencyLocation).toBe("Unknown");
    expect(summary.responsibleSupport).toBe("");
    expect(summary.complete).toBe(true);
  });

  it("7. Unknown Transportation Available and Unknown Caregiver Availability both count as answered -- Complete", () => {
    const summary = summarizeDisasterTriage({
      disasterLevel: "Level 1 — Hospice must assist; no assistance available",
      disasterLivesAlone: "Yes",
      disasterRequiresEvacuationAssistance: "No",
      disasterCaregiverAvailable: "Unknown",
      disasterTransportationAvailable: "Unknown",
      disasterRequiresElectricity: "No",
      disasterOxygenDependent: "No",
      disasterBackupPowerAvailable: "Unknown",
    });
    expect(summary.caregiverAvailable).toBe("Unknown");
    expect(summary.transportationAvailable).toBe("Unknown");
    expect(summary.complete).toBe(true);
  });

  it("8. Oxygen-dependent, electricity-dependent, lives-alone patient -- Complete once every required Emergency Support Assessment field is answered", () => {
    const missing = summarizeDisasterTriage({
      disasterLevel: "Level 1 — Hospice must assist; no assistance available",
      disasterLivesAlone: "Yes",
      disasterRequiresEvacuationAssistance: "Yes",
      disasterOxygenDependent: "Yes",
      disasterRequiresElectricity: "Yes",
      // caregiverAvailable, transportationAvailable, backupPowerAvailable intentionally omitted
    });
    expect(missing.complete).toBe(false);

    const complete = summarizeDisasterTriage({
      disasterLevel: "Level 1 — Hospice must assist; no assistance available",
      disasterLivesAlone: "Yes",
      disasterRequiresEvacuationAssistance: "Yes",
      disasterOxygenDependent: "Yes",
      disasterRequiresElectricity: "Yes",
      disasterCaregiverAvailable: "No",
      disasterTransportationAvailable: "No",
      disasterBackupPowerAvailable: "No",
    });
    expect(complete.livesAlone).toBe("Yes");
    expect(complete.oxygenDependent).toBe("Yes");
    expect(complete.requiresElectricity).toBe("Yes");
    expect(complete.complete).toBe(true);
  });

  it("Responsible Support is never required for completion, even when a Preferred Emergency Location is specified", () => {
    const summary = summarizeDisasterTriage({
      disasterLevel: "Level 3 — No need for hospice to assist; has adequate assistance available",
      disasterLivesAlone: "No",
      disasterRequiresEvacuationAssistance: "No",
      disasterCaregiverAvailable: "Yes",
      disasterTransportationAvailable: "Yes",
      disasterRequiresElectricity: "No",
      disasterOxygenDependent: "No",
      disasterBackupPowerAvailable: "Yes",
      disasterPreferredEmergencyLocation: "Remain at Facility",
      // disasterResponsibleSupport intentionally omitted
    });
    expect(summary.preferredEmergencyLocation).toBe("Remain at Facility");
    expect(summary.responsibleSupport).toBe("");
    expect(summary.complete).toBe(true);
  });
});
