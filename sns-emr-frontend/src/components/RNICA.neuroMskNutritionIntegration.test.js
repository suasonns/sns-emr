import { describe, it, expect } from "vitest";
import {
  INITIAL_FORM,
  validateRNICA,
  isMskPhysicalMotorLimitationComplete,
  isNeuroSpeechLanguageComplete,
  isNutritionDysphagiaComplete,
  isNutritionAspirationConcernResponseComplete,
  computeMotorDeficitFollowUp,
  computeNeurologicalDocumentationCoverage,
  computeNutritionDocumentationCoverage,
} from "./RNICA.jsx";

// PRODUCT OWNER DIRECTIVE "RNICA Neurological-MSK-Swallowing
// Integration" (authorized in full, "Option A") regression coverage.
// Scope: the cross-system Motor Deficit / Speech-Language / Dysphagia /
// Aspiration Concern / Intake Effect additions. Each of Neuro, MSK, and
// Nutrition's own existing fields/tests are untouched -- these are
// brand-new, additive paths only.

function baseFormData() {
  return {
    ...INITIAL_FORM,
    musculoskeletal: { ...INITIAL_FORM.musculoskeletal },
    neurological: { ...INITIAL_FORM.neurological },
    nutrition: { ...INITIAL_FORM.nutrition },
    skin: { ...INITIAL_FORM.skin },
  };
}

describe("isMskPhysicalMotorLimitationComplete / isNeuroSpeechLanguageComplete / isNutritionDysphagiaComplete", () => {
  it("are incomplete when Present is Not Assessed or blank", () => {
    expect(isMskPhysicalMotorLimitationComplete({})).toBe(false);
    expect(isNeuroSpeechLanguageComplete({ speechLanguageImpairmentPresent: "Not Assessed" })).toBe(false);
    expect(isNutritionDysphagiaComplete({ dysphagiaPresent: "Not Assessed" })).toBe(false);
  });

  it("are complete when Present is No", () => {
    expect(isMskPhysicalMotorLimitationComplete({ physicalMotorLimitationPresent: "No" })).toBe(true);
    expect(isNeuroSpeechLanguageComplete({ speechLanguageImpairmentPresent: "No" })).toBe(true);
    expect(isNutritionDysphagiaComplete({ dysphagiaPresent: "No" })).toBe(true);
  });

  it("require a selected type/impact when Present is Yes", () => {
    expect(isNeuroSpeechLanguageComplete({ speechLanguageImpairmentPresent: "Yes" })).toBe(false);
    expect(isNeuroSpeechLanguageComplete({ speechLanguageImpairmentPresent: "Yes", speechLanguageImpairmentType: ["Aphasia"] })).toBe(true);
    expect(isNutritionDysphagiaComplete({ dysphagiaPresent: "Yes" })).toBe(false);
    expect(isNutritionDysphagiaComplete({ dysphagiaPresent: "Yes", swallowingImpact: ["Pocketing Food"] })).toBe(true);
  });

  it("require Details when the selected type/impact includes Other", () => {
    expect(isNeuroSpeechLanguageComplete({ speechLanguageImpairmentPresent: "Yes", speechLanguageImpairmentType: ["Other"] })).toBe(false);
    expect(isNeuroSpeechLanguageComplete({ speechLanguageImpairmentPresent: "Yes", speechLanguageImpairmentType: ["Other"], speechLanguageImpairmentDetails: "Describes impairment" })).toBe(true);
    expect(isNutritionDysphagiaComplete({ dysphagiaPresent: "Yes", swallowingImpact: ["Other"] })).toBe(false);
    expect(isNutritionDysphagiaComplete({ dysphagiaPresent: "Yes", swallowingImpact: ["Other"], swallowingImpactDetails: "Describes impact" })).toBe(true);
  });
});

describe("isNutritionAspirationConcernResponseComplete", () => {
  it("is complete (not applicable) unless Aspiration Concern Present is directly Yes", () => {
    expect(isNutritionAspirationConcernResponseComplete({})).toBe(true);
    expect(isNutritionAspirationConcernResponseComplete({ aspirationConcernPresent: "No" })).toBe(true);
    expect(isNutritionAspirationConcernResponseComplete({ aspirationConcernPresent: "Not Assessed" })).toBe(true);
  });

  it("requires a structured Response (not satisfied by nothing) once Present is Yes", () => {
    expect(isNutritionAspirationConcernResponseComplete({ aspirationConcernPresent: "Yes" })).toBe(false);
    expect(isNutritionAspirationConcernResponseComplete({ aspirationConcernPresent: "Yes", aspirationConcernResponse: ["Supervised Intake"] })).toBe(true);
  });

  it("requires Details when Response includes Other", () => {
    expect(isNutritionAspirationConcernResponseComplete({ aspirationConcernPresent: "Yes", aspirationConcernResponse: ["Other"] })).toBe(false);
    expect(isNutritionAspirationConcernResponseComplete({ aspirationConcernPresent: "Yes", aspirationConcernResponse: ["Other"], aspirationConcernResponseDetails: "Describes response" })).toBe(true);
  });
});

describe("computeMotorDeficitFollowUp", () => {
  it("reports all five related assessments as incomplete on a blank record", () => {
    const followUp = computeMotorDeficitFollowUp(baseFormData());
    expect(followUp.map((i) => i.key)).toEqual(["physicalMotorLimitation", "mobility", "speechLanguage", "swallowing", "pressureRisk"]);
    expect(followUp.every((i) => i.complete === false)).toBe(true);
  });

  it("marks each item complete once its own owning section documents a 'No'/Not Present answer", () => {
    const formData = baseFormData();
    formData.musculoskeletal.physicalMotorLimitationPresent = "No";
    formData.musculoskeletal.ambulationStatus = "Ambulatory";
    formData.musculoskeletal.ambulationAssistance = "Independent";
    formData.musculoskeletal.stepsBeforeResting = "More than 10 steps";
    formData.musculoskeletal.gait = "Normal";
    formData.neurological.speechLanguageImpairmentPresent = "No";
    formData.nutrition.dysphagiaPresent = "No";
    formData.skin.braden = { ...formData.skin.braden, total: 18 };

    const followUp = computeMotorDeficitFollowUp(formData);
    expect(followUp.every((i) => i.complete === true)).toBe(true);
  });

  it("never writes to any related section -- it is a read-only reminder, not a second data store", () => {
    const formData = baseFormData();
    computeMotorDeficitFollowUp(formData);
    expect(formData.musculoskeletal.physicalMotorLimitationPresent).toBe("");
    expect(formData.neurological.speechLanguageImpairmentPresent).toBe("");
    expect(formData.nutrition.dysphagiaPresent).toBe("");
  });
});

describe("computeNeurologicalDocumentationCoverage -- Motor Deficit / Speech-Language", () => {
  it("reports Motor Deficit incomplete when Not Assessed, complete (Not Present) when No", () => {
    expect(computeNeurologicalDocumentationCoverage({}).find((i) => i.key === "motorDeficit").complete).toBe(false);
    const complete = computeNeurologicalDocumentationCoverage({ motorDeficitPresent: "No" }).find((i) => i.key === "motorDeficit");
    expect(complete.complete).toBe(true);
    expect(complete.value).toBe("Not Present");
  });

  it("summarizes Speech / Language by its selected type(s) without re-prefixing the label", () => {
    const item = computeNeurologicalDocumentationCoverage({
      speechLanguageImpairmentPresent: "Yes",
      speechLanguageImpairmentType: ["Aphasia", "Dysarthria"],
    }).find((i) => i.key === "speechLanguage");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Aphasia, Dysarthria");
    expect(item.value.startsWith("Speech")).toBe(false);
  });
});

describe("computeNutritionDocumentationCoverage -- Dysphagia / Aspiration Concern / Intake Effect", () => {
  it("reports Dysphagia incomplete when Not Assessed, complete (Not Present) when No", () => {
    expect(computeNutritionDocumentationCoverage({}).find((i) => i.key === "dysphagia").complete).toBe(false);
    const complete = computeNutritionDocumentationCoverage({ dysphagiaPresent: "No" }).find((i) => i.key === "dysphagia");
    expect(complete.complete).toBe(true);
    expect(complete.value).toBe("Not Present");
  });

  it("suppresses Aspiration Concern entirely (not 'Not Applicable') unless Present is directly Yes", () => {
    expect(computeNutritionDocumentationCoverage({}).find((i) => i.key === "aspirationConcern")).toBeUndefined();
    expect(computeNutritionDocumentationCoverage({ aspirationConcernPresent: "No" }).find((i) => i.key === "aspirationConcern")).toBeUndefined();
    const item = computeNutritionDocumentationCoverage({ aspirationConcernPresent: "Yes" }).find((i) => i.key === "aspirationConcern");
    expect(item).toBeDefined();
    expect(item.complete).toBe(false);
  });

  it("requires Intake Effect Details only when Other is selected", () => {
    expect(computeNutritionDocumentationCoverage({ intakeEffect: "No Observed Effect" }).find((i) => i.key === "intakeEffect").complete).toBe(true);
    expect(computeNutritionDocumentationCoverage({ intakeEffect: "Other" }).find((i) => i.key === "intakeEffect").complete).toBe(false);
    expect(computeNutritionDocumentationCoverage({ intakeEffect: "Other", intakeEffectDetails: "Takes much longer to eat" }).find((i) => i.key === "intakeEffect").complete).toBe(true);
  });
});

describe("validateRNICA -- Aspiration Concern Response and Motor Deficit cross-system hard blocks", () => {
  it("hard-blocks Lock when Aspiration Concern Present is Yes with no structured Response", () => {
    const formData = baseFormData();
    formData.nutrition.aspirationConcernPresent = "Yes";
    const result = validateRNICA(formData, "ica");
    expect(result.errors["nutrition.aspirationConcernResponse"]).toBeTruthy();
  });

  it("does not hard-block Aspiration Concern when Present is No or Not Assessed", () => {
    const formData = baseFormData();
    formData.nutrition.aspirationConcernPresent = "No";
    expect(validateRNICA(formData, "ica").errors["nutrition.aspirationConcernResponse"]).toBeUndefined();
  });

  it("hard-blocks Lock on all three related assessments when Motor Deficit Present is Yes and none are documented", () => {
    const formData = baseFormData();
    formData.neurological.motorDeficitPresent = "Yes";
    const result = validateRNICA(formData, "ica");
    expect(result.errors["musculoskeletal.physicalMotorLimitationPresent"]).toBeTruthy();
    expect(result.errors["neurological.speechLanguageImpairmentPresent"]).toBeTruthy();
    expect(result.errors["nutrition.dysphagiaPresent"]).toBeTruthy();
  });

  it("clears the Motor Deficit cross-system hard blocks once all three related assessments are documented", () => {
    const formData = baseFormData();
    formData.neurological.motorDeficitPresent = "Yes";
    formData.musculoskeletal.physicalMotorLimitationPresent = "No";
    formData.neurological.speechLanguageImpairmentPresent = "No";
    formData.nutrition.dysphagiaPresent = "No";
    const result = validateRNICA(formData, "ica");
    expect(result.errors["musculoskeletal.physicalMotorLimitationPresent"]).toBeUndefined();
    expect(result.errors["neurological.speechLanguageImpairmentPresent"]).toBeUndefined();
    expect(result.errors["nutrition.dysphagiaPresent"]).toBeUndefined();
  });

  it("does not hard-block the related assessments when Motor Deficit Present is No or Not Assessed", () => {
    const formData = baseFormData();
    formData.neurological.motorDeficitPresent = "No";
    const result = validateRNICA(formData, "ica");
    expect(result.errors["musculoskeletal.physicalMotorLimitationPresent"]).toBeUndefined();
    expect(result.errors["neurological.speechLanguageImpairmentPresent"]).toBeUndefined();
    expect(result.errors["nutrition.dysphagiaPresent"]).toBeUndefined();
  });
});
