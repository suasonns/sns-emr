import { describe, it, expect } from "vitest";
import {
  computeMusculoskeletalDocumentationCoverage,
  computeMobilityStatusClearPatch,
  resolveRigidityAffectsSelection,
} from "./RNICA.jsx";

// PRODUCT OWNER DIRECTIVE (2026-11-16) "Musculoskeletal Phase 2
// Implementation" regression coverage. MSK-only: Muscle Wasting (new
// finding), Rigidity Affects (replaces the retired Rigidity Severity),
// and the Non-Ambulatory/Bedbound Mobility status-transition clearing
// rule. No other Body System, discipline, or backend consumer is
// touched by this test file.

describe("computeMusculoskeletalDocumentationCoverage -- Muscle Wasting item", () => {
  const findMuscleWasting = (d) =>
    computeMusculoskeletalDocumentationCoverage(d).find((i) => i.key === "muscleWasting");

  it("is incomplete when Present is unanswered (Not Assessed)", () => {
    const item = findMuscleWasting({});
    expect(item.complete).toBe(false);
  });

  it("is complete and reads 'Not Present' when Present is No", () => {
    const item = findMuscleWasting({ muscleWastingPresent: false });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Not Present");
  });

  it("is incomplete when Present is Yes but Distribution is unanswered", () => {
    const item = findMuscleWasting({ muscleWastingPresent: true });
    expect(item.complete).toBe(false);
  });

  it("is complete and reads 'Generalized' when Present is Yes and Distribution is Generalized", () => {
    const item = findMuscleWasting({ muscleWastingPresent: true, muscleWastingDistribution: "Generalized" });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Generalized");
  });

  it("is incomplete when Distribution is Localized but no Location is selected", () => {
    const item = findMuscleWasting({ muscleWastingPresent: true, muscleWastingDistribution: "Localized" });
    expect(item.complete).toBe(false);
  });

  it("is complete and summarizes the Location(s) when Distribution is Localized with a Location", () => {
    const item = findMuscleWasting({
      muscleWastingPresent: true,
      muscleWastingDistribution: "Localized",
      muscleWastingLocation: ["Lower Extremities"],
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Localized — Lower Extremities");
  });

  it("joins multiple Locations in the summary", () => {
    const item = findMuscleWasting({
      muscleWastingPresent: true,
      muscleWastingDistribution: "Localized",
      muscleWastingLocation: ["Upper Extremities", "Lower Extremities"],
    });
    expect(item.value).toBe("Localized — Upper Extremities, Lower Extremities");
  });

  it("is incomplete when Location includes 'Other' but Location Details is blank", () => {
    const item = findMuscleWasting({
      muscleWastingPresent: true,
      muscleWastingDistribution: "Localized",
      muscleWastingLocation: ["Other"],
    });
    expect(item.complete).toBe(false);
  });

  it("is complete when Location includes 'Other' and Location Details is documented", () => {
    const item = findMuscleWasting({
      muscleWastingPresent: true,
      muscleWastingDistribution: "Localized",
      muscleWastingLocation: ["Other"],
      muscleWastingLocationDetails: "Facial wasting noted bilaterally",
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Localized — Other");
  });
});

// PRODUCT OWNER DIRECTIVE (2026-11-16) "Musculoskeletal Phase 2
// Implementation" -- Rigidity Severity (Mild/Moderate/Severe) is rejected
// as "subjective, hospital-assessment-style grading of no demonstrated
// hospice value"; Rigidity Affects (Comfort/Positioning-Turning/Personal
// Care/Mobility/No Observed Care Impact/Other) replaces it as the sole
// editable/Coverage-surfaced concept.
describe("computeMusculoskeletalDocumentationCoverage -- Rigidity item (Rigidity Affects replaces Severity)", () => {
  const findRigidity = (d) => computeMusculoskeletalDocumentationCoverage(d).find((i) => i.key === "rigidity");

  it("is incomplete when Present is unanswered (Not Assessed)", () => {
    const item = findRigidity({});
    expect(item.complete).toBe(false);
  });

  it("is complete and reads 'Not Present' when Present is No", () => {
    const item = findRigidity({ rigidityPresent: false });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Not Present");
  });

  it("is incomplete when Present is Yes but no Rigidity Affects value is selected (even if a legacy Severity value exists)", () => {
    const item = findRigidity({ rigidityPresent: true, rigidity: "Moderate" });
    expect(item.complete).toBe(false);
  });

  it("is complete and summarizes Rigidity Affects (no legacy Severity) when Present is Yes with a value", () => {
    const item = findRigidity({ rigidityPresent: true, rigidity: "Moderate", rigidityAffects: ["Positioning / Turning"] });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Positioning / Turning");
  });

  it("joins multiple Rigidity Affects values in the summary", () => {
    const item = findRigidity({ rigidityPresent: true, rigidityAffects: ["Comfort", "Mobility"] });
    expect(item.value).toBe("Comfort, Mobility");
  });

  it("is incomplete when Rigidity Affects includes 'Other' but Rigidity Impact Details is blank", () => {
    const item = findRigidity({ rigidityPresent: true, rigidityAffects: ["Other"] });
    expect(item.complete).toBe(false);
  });

  it("is complete when Rigidity Affects includes 'Other' and Rigidity Impact Details is documented", () => {
    const item = findRigidity({
      rigidityPresent: true,
      rigidityAffects: ["Other"],
      rigidityOtherDetails: "Interferes with wound care positioning",
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Other");
  });
});

describe("resolveRigidityAffectsSelection -- 'No Observed Care Impact' mutual exclusivity", () => {
  it("passes through a non-array value unchanged", () => {
    expect(resolveRigidityAffectsSelection(undefined)).toBe(undefined);
  });

  it("passes through a selection with no 'No Observed Care Impact' entry unchanged", () => {
    const next = ["Comfort", "Mobility"];
    expect(resolveRigidityAffectsSelection(next)).toBe(next);
  });

  it("passes through a lone 'No Observed Care Impact' selection unchanged", () => {
    const next = ["No Observed Care Impact"];
    expect(resolveRigidityAffectsSelection(next)).toBe(next);
  });

  it("selecting 'No Observed Care Impact' after real values clears the real values (impact-free wins)", () => {
    expect(resolveRigidityAffectsSelection(["Comfort", "Mobility", "No Observed Care Impact"])).toEqual([
      "No Observed Care Impact",
    ]);
  });

  it("selecting a real value after 'No Observed Care Impact' clears 'No Observed Care Impact' (real values win)", () => {
    expect(resolveRigidityAffectsSelection(["No Observed Care Impact", "Comfort"])).toEqual(["Comfort"]);
  });
});

// PRODUCT OWNER DIRECTIVE (2026-11-16) "Musculoskeletal Phase 2
// Implementation" Section 9 -- a single generic rule (three status-
// specific field groups, each cleared only when Ambulation Status no
// longer matches that group's own status) covers all 11 named transition
// examples from the directive.
describe("computeMobilityStatusClearPatch -- Ambulation Status transition clearing", () => {
  it("clears the Ambulatory-only group when leaving Ambulatory", () => {
    const patch = computeMobilityStatusClearPatch("Non-Ambulatory");
    expect(patch.ambulationAssistance).toBe("");
    expect(patch.stepsBeforeResting).toBe("");
    expect(patch.gait).toBe("");
    expect(patch.gaitDetails).toBe("");
  });

  it("clears the Non-Ambulatory-only group when leaving Non-Ambulatory", () => {
    const patch = computeMobilityStatusClearPatch("Ambulatory");
    expect(patch.outOfBedActivity).toBe("");
    expect(patch.outOfBedPosition).toBe("");
    expect(patch.outOfBedPositionDetails).toBe("");
    expect(patch.assistanceToLeaveBed).toBe("");
  });

  it("clears the Bedbound-only field when leaving Bedbound", () => {
    const patch = computeMobilityStatusClearPatch("Ambulatory");
    expect(patch.repositioningSupport).toBe("");
  });

  it("does not clear the Ambulatory-only group when the new status is Ambulatory", () => {
    const patch = computeMobilityStatusClearPatch("Ambulatory");
    expect(patch.ambulationAssistance).toBeUndefined();
    expect(patch.stepsBeforeResting).toBeUndefined();
    expect(patch.gait).toBeUndefined();
    expect(patch.gaitDetails).toBeUndefined();
  });

  it("does not clear the Non-Ambulatory-only group when the new status is Non-Ambulatory", () => {
    const patch = computeMobilityStatusClearPatch("Non-Ambulatory");
    expect(patch.outOfBedActivity).toBeUndefined();
    expect(patch.outOfBedPosition).toBeUndefined();
    expect(patch.outOfBedPositionDetails).toBeUndefined();
    expect(patch.assistanceToLeaveBed).toBeUndefined();
  });

  it("does not clear Repositioning Support when the new status is Bedbound", () => {
    const patch = computeMobilityStatusClearPatch("Bedbound");
    expect(patch.repositioningSupport).toBeUndefined();
  });

  it("clears both other groups when moving to Bedbound, leaving Repositioning Support alone", () => {
    const patch = computeMobilityStatusClearPatch("Bedbound");
    expect(patch.ambulationAssistance).toBe("");
    expect(patch.gait).toBe("");
    expect(patch.outOfBedActivity).toBe("");
    expect(patch.assistanceToLeaveBed).toBe("");
    expect(patch.repositioningSupport).toBeUndefined();
  });

  it("clears all three groups when the status becomes 'Not Assessed'/blank", () => {
    const patch = computeMobilityStatusClearPatch("Not Assessed");
    expect(patch.ambulationAssistance).toBe("");
    expect(patch.outOfBedActivity).toBe("");
    expect(patch.repositioningSupport).toBe("");
  });
});
