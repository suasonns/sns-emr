import { describe, it, expect } from "vitest";
import {
  computeMusculoskeletalDocumentationCoverage,
  computeMobilityChildFieldVisibility,
  computeMobilityAssistanceVisibility,
  computeMobilityStatusClearPatch,
  resolveAssistiveDevicesSelection,
  resolveNonAmbulatoryMobilityConcernsSelection,
  isMskMobilityComplete,
  isMskRepositioningResponseComplete,
  computeMusculoskeletalWorkflowStatus,
  validateRNICA,
  INITIAL_FORM,
} from "./RNICA.jsx";

// PRODUCT OWNER DIRECTIVE (2026-10-16) "Musculoskeletal Mobility
// Implementation" regression coverage. MSK-only: three new fields
// (ambulationStatus / ambulationAssistance / stepsBeforeResting), the
// existing `assistiveDevices` field reused without a second editor, and
// Gait kept fully separate. No other Body System, discipline, or backend
// consumer is touched by this test file.

describe("computeMobilityChildFieldVisibility -- gating matrix (Steps Before Resting)", () => {
  it("hides Steps when Ambulation Status is Not Assessed", () => {
    expect(computeMobilityChildFieldVisibility("Not Assessed", "")).toBe("hide");
  });

  it("hides Steps when Ambulation Status is Non-Ambulatory", () => {
    expect(computeMobilityChildFieldVisibility("Non-Ambulatory", "")).toBe("hide");
  });

  it("hides Steps when Ambulation Status is Bedbound", () => {
    expect(computeMobilityChildFieldVisibility("Bedbound", "")).toBe("hide");
  });

  it("shows Steps when Ambulation Status is Ambulatory", () => {
    expect(computeMobilityChildFieldVisibility("Ambulatory", "")).toBe("show");
  });

  it("never hides already-documented data even if status later reads non-Ambulatory", () => {
    expect(computeMobilityChildFieldVisibility("Non-Ambulatory", "Stand-By Assist")).toBe("show");
  });
});

// PRODUCT OWNER DIRECTIVE (2026-11-16) "Musculoskeletal Phase 2
// Implementation" -- REVERSES the 2026-11-16 "MSK Rehabilitation-Thinking
// Removal" widening: Mobility Assistance Level is Ambulatory-only again
// now that dedicated Non-Ambulatory (Out-of-Bed Activity/Position/
// Assistance Needed to Leave Bed) and Bedbound (Repositioning Support)
// fields exist instead. No legacy-value exception (same no-exception
// precedent as Gait): a single-argument function of Ambulation Status
// alone.
describe("computeMobilityAssistanceVisibility -- gating matrix (Mobility Assistance Level)", () => {
  it("hides when Ambulation Status is unanswered", () => {
    expect(computeMobilityAssistanceVisibility("")).toBe("hide");
  });

  it("hides when Ambulation Status is directly 'Not Assessed'", () => {
    expect(computeMobilityAssistanceVisibility("Not Assessed")).toBe("hide");
  });

  it("shows when Ambulation Status is Ambulatory", () => {
    expect(computeMobilityAssistanceVisibility("Ambulatory")).toBe("show");
  });

  it("hides when Ambulation Status is Non-Ambulatory", () => {
    expect(computeMobilityAssistanceVisibility("Non-Ambulatory")).toBe("hide");
  });

  it("hides when Ambulation Status is Bedbound", () => {
    expect(computeMobilityAssistanceVisibility("Bedbound")).toBe("hide");
  });
});

describe("resolveAssistiveDevicesSelection -- None mutual exclusivity", () => {
  it("selecting a real device after None clears None (devices win)", () => {
    expect(resolveAssistiveDevicesSelection(["None", "Walker"])).toEqual(["Walker"]);
  });

  it("selecting None after real devices clears all real devices (None wins)", () => {
    expect(resolveAssistiveDevicesSelection(["Walker", "Wheelchair", "None"])).toEqual(["None"]);
  });

  it("Walker and Wheelchair may coexist (no exclusivity between real devices)", () => {
    expect(resolveAssistiveDevicesSelection(["Walker", "Wheelchair"])).toEqual(["Walker", "Wheelchair"]);
  });

  it("a single selection (None alone, or one device alone) passes through unchanged", () => {
    expect(resolveAssistiveDevicesSelection(["None"])).toEqual(["None"]);
    expect(resolveAssistiveDevicesSelection(["Walker"])).toEqual(["Walker"]);
    expect(resolveAssistiveDevicesSelection([])).toEqual([]);
  });
});

describe("computeMusculoskeletalDocumentationCoverage -- Mobility item", () => {
  const findMobility = (d) => computeMusculoskeletalDocumentationCoverage(d).find((i) => i.key === "mobility");

  it("is incomplete (null value, per established convention) when ambulationStatus is blank", () => {
    const item = findMobility({});
    expect(item.complete).toBe(false);
    expect(item.value).toBe(null);
    expect(item.unresolvedHint).toMatch(/ambulation status/i);
  });

  it("is incomplete when ambulationStatus is directly 'Not Assessed'", () => {
    const item = findMobility({ ambulationStatus: "Not Assessed" });
    expect(item.complete).toBe(false);
    expect(item.value).toBe(null);
  });

  it("is incomplete when Ambulatory but Ambulation Assistance is unanswered", () => {
    const item = findMobility({ ambulationStatus: "Ambulatory", stepsBeforeResting: "1–5 Steps" });
    expect(item.complete).toBe(false);
  });

  it("is incomplete when Ambulatory but Steps Before Resting is unanswered", () => {
    const item = findMobility({ ambulationStatus: "Ambulatory", ambulationAssistance: "Independent" });
    expect(item.complete).toBe(false);
  });

  it("is incomplete when Ambulatory and Steps Before Resting is itself 'Not Assessed'", () => {
    const item = findMobility({
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Independent",
      stepsBeforeResting: "Not Assessed",
    });
    expect(item.complete).toBe(false);
  });

  // PRODUCT OWNER CORRECTION (2026-11-16) "Musculoskeletal Final Hospice
  // Workflow Correction" -- PRIMARY DEFECT: Mobility previously read
  // complete for an Ambulatory patient while Gait was blank or "Not
  // Assessed" (Assistance + Steps alone were enough). "A green Mobility
  // pill must mean the complete applicable Mobility assessment is
  // documented" -- Gait is now a required applicable field.
  it("is incomplete when Ambulatory with Assistance and Steps answered but Gait is blank", () => {
    const item = findMobility({
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Maximum Assist",
      stepsBeforeResting: "1–5 Steps",
    });
    expect(item.complete).toBe(false);
  });

  it("is incomplete when Ambulatory with Assistance and Steps answered but Gait is directly 'Not Assessed'", () => {
    const item = findMobility({
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Maximum Assist",
      stepsBeforeResting: "1–5 Steps",
      gait: "Not Assessed",
    });
    expect(item.complete).toBe(false);
  });

  it("is incomplete when Ambulatory with Gait = Other but Gait Details is blank", () => {
    const item = findMobility({
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Independent",
      stepsBeforeResting: "6–10 Steps",
      gait: "Other",
    });
    expect(item.complete).toBe(false);
  });

  it("is complete: Ambulatory + Independent + More Than 50 Steps + Gait Normal, no device", () => {
    const item = findMobility({
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Independent",
      stepsBeforeResting: "More Than 50 Steps",
      gait: "Normal",
      assistiveDevices: ["None"],
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Ambulatory — Independent — More Than 50 Steps — Normal Gait");
  });

  it("is complete when Ambulatory + Gait = Other with Gait Details documented", () => {
    const item = findMobility({
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Stand-By Assist",
      stepsBeforeResting: "11–25 Steps",
      gait: "Other",
      gaitDetails: "Festinating gait",
    });
    expect(item.complete).toBe(true);
  });

  // PRODUCT OWNER DIRECTIVE (2026-11-16) "Musculoskeletal Phase 2
  // Implementation" -- Walking Aid is deliberately excluded from the
  // Mobility summary; it already has its own dedicated "Walking Aid"
  // Coverage item, so a device never appears twice.
  it("summarizes Ambulatory + Stand-By Assist + 6–10 Steps accurately, excluding the device (shown by its own Coverage item)", () => {
    const item = findMobility({
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Stand-By Assist",
      stepsBeforeResting: "6–10 Steps",
      gait: "Normal",
      assistiveDevices: ["Walker"],
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Ambulatory — Stand-By Assist — 6–10 Steps — Normal Gait");
  });

  it("does not list coexisting devices (Walker and Wheelchair) in the Mobility summary", () => {
    const item = findMobility({
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "1-Person Assist",
      stepsBeforeResting: "1–5 Steps",
      gait: "Normal",
      assistiveDevices: ["Walker", "Wheelchair"],
    });
    expect(item.value).toBe("Ambulatory — 1-Person Assist — 1–5 Steps — Normal Gait");
  });

  // PRODUCT OWNER DIRECTIVE (2026-11-16) "Musculoskeletal Phase 2
  // Implementation" -- "Complete the Mobility Story": Non-Ambulatory now
  // requires Out-of-Bed Activity (and its own required children) instead
  // of defaulting to complete with no documentation at all.
  it("is incomplete for Non-Ambulatory until Out-of-Bed Activity is answered", () => {
    const item = findMobility({ ambulationStatus: "Non-Ambulatory" });
    expect(item.complete).toBe(false);
  });

  it("is complete for Non-Ambulatory when Out-of-Bed Activity is 'No'", () => {
    const item = findMobility({ ambulationStatus: "Non-Ambulatory", outOfBedActivity: "No" });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Non-Ambulatory — Does Not Routinely Leave Bed");
  });

  it("is complete for Non-Ambulatory when Out-of-Bed Activity is 'Not Tolerated'", () => {
    const item = findMobility({ ambulationStatus: "Non-Ambulatory", outOfBedActivity: "Not Tolerated" });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Non-Ambulatory — Does Not Tolerate Out-of-Bed Activity");
  });

  it("is incomplete for Non-Ambulatory + Out-of-Bed Activity Yes + Position + Assistance but no Mobility Concern selected", () => {
    const item = findMobility({
      ambulationStatus: "Non-Ambulatory",
      outOfBedActivity: "Yes",
      outOfBedPosition: "Wheelchair",
      assistanceToLeaveBed: "2-Person Assist",
    });
    expect(item.complete).toBe(false);
  });

  it("summarizes Non-Ambulatory + Out-of-Bed Activity Yes + Position + Assistance + a single Mobility Concern", () => {
    const item = findMobility({
      ambulationStatus: "Non-Ambulatory",
      outOfBedActivity: "Yes",
      outOfBedPosition: "Wheelchair",
      assistanceToLeaveBed: "2-Person Assist",
      nonAmbulatoryMobilityConcerns: ["Poor Trunk / Seated Control"],
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Non-Ambulatory — Wheelchair — 2-Person Assist — Poor Trunk / Seated Control");
  });

  it("summarizes multiple Mobility Concerns joined by comma within the single flat pill", () => {
    const item = findMobility({
      ambulationStatus: "Non-Ambulatory",
      outOfBedActivity: "Yes",
      outOfBedPosition: "Chair",
      assistanceToLeaveBed: "Maximum Assist",
      nonAmbulatoryMobilityConcerns: ["Limited Upright Tolerance", "Fatigue With Out-of-Bed Activity"],
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Non-Ambulatory — Chair — Maximum Assist — Limited Upright Tolerance, Fatigue With Out-of-Bed Activity");
  });

  it("is complete with 'No Observed Mobility Concern' alone", () => {
    const item = findMobility({
      ambulationStatus: "Non-Ambulatory",
      outOfBedActivity: "Yes",
      outOfBedPosition: "Commode",
      assistanceToLeaveBed: "Stand-By Assist",
      nonAmbulatoryMobilityConcerns: ["No Observed Mobility Concern"],
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Non-Ambulatory — Commode — Stand-By Assist — No Observed Mobility Concern");
  });

  it("is incomplete when Mobility Concerns includes 'Other' without Concern Details", () => {
    const item = findMobility({
      ambulationStatus: "Non-Ambulatory",
      outOfBedActivity: "Yes",
      outOfBedPosition: "Wheelchair",
      assistanceToLeaveBed: "1-Person Assist",
      nonAmbulatoryMobilityConcerns: ["Other"],
    });
    expect(item.complete).toBe(false);
  });

  it("substitutes Concern Details text for 'Other' in the summary once documented", () => {
    const item = findMobility({
      ambulationStatus: "Non-Ambulatory",
      outOfBedActivity: "Yes",
      outOfBedPosition: "Wheelchair",
      assistanceToLeaveBed: "1-Person Assist",
      nonAmbulatoryMobilityConcerns: ["Other"],
      nonAmbulatoryMobilityConcernDetails: "Leans heavily to the right side",
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Non-Ambulatory — Wheelchair — 1-Person Assist — Leans heavily to the right side");
  });

  it("is incomplete for Non-Ambulatory + Out-of-Bed Activity Yes + Position Other without Position Details", () => {
    const item = findMobility({
      ambulationStatus: "Non-Ambulatory",
      outOfBedActivity: "Yes",
      outOfBedPosition: "Other",
      assistanceToLeaveBed: "Stand-By Assist",
      nonAmbulatoryMobilityConcerns: ["No Observed Mobility Concern"],
    });
    expect(item.complete).toBe(false);
  });

  // PRODUCT OWNER DIRECTIVE (2026-11-17) "Musculoskeletal Non-Ambulatory
  // Workflow Expansion" -- context-specific amber hint for Non-Ambulatory
  // + unassessed Out-of-Bed Activity; every other incomplete Mobility
  // state keeps the original generic hint.
  it("shows the Non-Ambulatory-specific unresolved hint only when Out-of-Bed Activity has not been assessed", () => {
    const notAssessed = findMobility({ ambulationStatus: "Non-Ambulatory" });
    expect(notAssessed.unresolvedHint).toBe("Non-Ambulatory — Out-of-Bed Activity Not Assessed");

    // PRODUCT OWNER DIRECTIVE "Ambulation Status Safety Validation" --
    // a blank/"Not Assessed" Ambulation Status itself now takes
    // precedence over the generic fallback, reading the exact approved
    // "Ambulation Status required" text.
    const blankAmbulationStatus = findMobility({});
    expect(blankAmbulationStatus.unresolvedHint).toBe("Ambulation Status required");

    // PRODUCT OWNER DIRECTIVE "Musculoskeletal Final Stabilization" --
    // Coverage must state the exact missing element rather than one
    // generic Mobility warning; once Activity/Position/Assistance are
    // answered, the next unresolved field (Non-Ambulatory Mobility
    // Concerns) is named directly instead of falling back to the
    // generic "Select ambulation status..." message.
    const incompleteYes = findMobility({
      ambulationStatus: "Non-Ambulatory",
      outOfBedActivity: "Yes",
      outOfBedPosition: "Wheelchair",
      assistanceToLeaveBed: "2-Person Assist",
    });
    expect(incompleteYes.unresolvedHint).toBe("Non-Ambulatory Mobility Concerns required");
  });

  // PRODUCT OWNER DIRECTIVE (2026-11-16) "Musculoskeletal Phase 2
  // Implementation" -- Repositioning Support Needed in Bed is now
  // required for Bedbound completion instead of auto-completing with no
  // documentation.
  it("is incomplete for Bedbound until Repositioning Support is answered", () => {
    const item = findMobility({ ambulationStatus: "Bedbound" });
    expect(item.complete).toBe(false);
  });

  it("is complete for Bedbound once Repositioning Support is answered and does not auto-select a device", () => {
    const item = findMobility({ ambulationStatus: "Bedbound", repositioningSupport: "2-Person Assistance" });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Bedbound — 2-Person Assistance");
  });

  it("does not require Notes to complete Mobility Coverage", () => {
    const item = findMobility({ ambulationStatus: "Bedbound", repositioningSupport: "Repositions Independently", notes: "" });
    expect(item.complete).toBe(true);
  });

  // PRODUCT OWNER CORRECTION (2026-11-16) "Musculoskeletal Final Hospice
  // Workflow Correction" -- structured Mobility/Weakness completion must
  // never be gated, blocked, or contradicted by free-text Notes content,
  // even when Notes appears to describe a different clinical picture
  // (e.g. "Patient is bedbound" while Ambulation Status is structurally
  // "Ambulatory"). SNS does not parse free text to auto-correct
  // structured fields or vice versa -- that is explicitly out of scope
  // (deferred to a future Documentation Guidance Engine, not built here).
  it("completes Mobility from structured fields alone even when Notes text describes a different clinical picture", () => {
    const item = findMobility({
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Maximum Assist",
      stepsBeforeResting: "1–5 Steps",
      gait: "Unsteady",
      weakness: "Severe",
      notes: "Patient is bedbound and no longer tolerates the wheelchair; severe weakness noted.",
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Ambulatory — Maximum Assist — 1–5 Steps — Unsteady Gait");
  });
});

// PRODUCT OWNER DIRECTIVE (2026-11-17) "Musculoskeletal Non-Ambulatory
// Workflow Expansion" regression coverage for the new
// "Non-Ambulatory Mobility Concerns" field.
describe("resolveNonAmbulatoryMobilityConcernsSelection -- 'No Observed Mobility Concern' mutual exclusivity", () => {
  it("selecting a real concern after 'No Observed Mobility Concern' clears it (concern wins)", () => {
    expect(resolveNonAmbulatoryMobilityConcernsSelection(["No Observed Mobility Concern", "Unable to Bear Weight"]))
      .toEqual(["Unable to Bear Weight"]);
  });

  it("selecting 'No Observed Mobility Concern' after real concerns clears all real concerns ('No Observed' wins)", () => {
    expect(resolveNonAmbulatoryMobilityConcernsSelection(["Unable to Bear Weight", "Limited Upright Tolerance", "No Observed Mobility Concern"]))
      .toEqual(["No Observed Mobility Concern"]);
  });

  it("multiple real concerns may coexist (no exclusivity between genuine concerns)", () => {
    expect(resolveNonAmbulatoryMobilityConcernsSelection(["Unable to Bear Weight", "Fatigue With Out-of-Bed Activity"]))
      .toEqual(["Unable to Bear Weight", "Fatigue With Out-of-Bed Activity"]);
  });

  it("a single selection (alone) passes through unchanged", () => {
    expect(resolveNonAmbulatoryMobilityConcernsSelection(["No Observed Mobility Concern"])).toEqual(["No Observed Mobility Concern"]);
    expect(resolveNonAmbulatoryMobilityConcernsSelection(["Unable to Bear Weight"])).toEqual(["Unable to Bear Weight"]);
    expect(resolveNonAmbulatoryMobilityConcernsSelection([])).toEqual([]);
  });
});

describe("computeMobilityStatusClearPatch -- Non-Ambulatory Mobility Concerns clearing", () => {
  it("clears Non-Ambulatory Mobility Concerns and their Details when Ambulation Status moves to Ambulatory", () => {
    const patch = computeMobilityStatusClearPatch("Ambulatory");
    expect(patch.nonAmbulatoryMobilityConcerns).toEqual([]);
    expect(patch.nonAmbulatoryMobilityConcernDetails).toBe("");
    expect(patch.outOfBedActivity).toBe("");
    expect(patch.outOfBedPosition).toBe("");
    expect(patch.assistanceToLeaveBed).toBe("");
  });

  it("clears Non-Ambulatory Mobility Concerns and their Details when Ambulation Status moves to Bedbound", () => {
    const patch = computeMobilityStatusClearPatch("Bedbound");
    expect(patch.nonAmbulatoryMobilityConcerns).toEqual([]);
    expect(patch.nonAmbulatoryMobilityConcernDetails).toBe("");
  });

  it("does not clear Non-Ambulatory Mobility Concerns when Ambulation Status stays Non-Ambulatory", () => {
    const patch = computeMobilityStatusClearPatch("Non-Ambulatory");
    expect(patch.nonAmbulatoryMobilityConcerns).toBeUndefined();
    expect(patch.nonAmbulatoryMobilityConcernDetails).toBeUndefined();
  });
});

// PRODUCT OWNER CORRECTION (2026-11-16) "MSK Rehabilitation-Thinking
// Removal" -- Gait is suppressed from Coverage entirely (not shown as
// "Not Applicable") whenever Ambulation Status is not directly
// "Ambulatory" -- no legacy-value exception ("do not build legacy-value
// workflows"; this is test data, not a production migration concern).
describe("Gait Coverage is suppressed when not clinically applicable", () => {
  it("is omitted entirely for a Bedbound patient with no documented Gait value", () => {
    const items = computeMusculoskeletalDocumentationCoverage({
      ambulationStatus: "Bedbound",
    });
    expect(items.find((i) => i.key === "gait")).toBeUndefined();
  });

  it("is omitted entirely for a Non-Ambulatory patient with no documented Gait value", () => {
    const items = computeMusculoskeletalDocumentationCoverage({
      ambulationStatus: "Non-Ambulatory",
    });
    expect(items.find((i) => i.key === "gait")).toBeUndefined();
  });

  it("is omitted for a Bedbound patient even when a legacy Gait value already exists (no legacy-value exception)", () => {
    const items = computeMusculoskeletalDocumentationCoverage({
      gait: "Unsteady",
      ambulationStatus: "Bedbound",
    });
    expect(items.find((i) => i.key === "gait")).toBeUndefined();
  });

  it("requires Gait to be answered for an Ambulatory patient", () => {
    const items = computeMusculoskeletalDocumentationCoverage({
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Independent",
      stepsBeforeResting: "26–50 Steps",
    });
    const gait = items.find((i) => i.key === "gait");
    expect(gait.complete).toBe(false);
  });

  it("is complete once an Ambulatory patient's Gait is documented", () => {
    const items = computeMusculoskeletalDocumentationCoverage({
      ambulationStatus: "Ambulatory",
      gait: "Normal",
    });
    const gait = items.find((i) => i.key === "gait");
    expect(gait.complete).toBe(true);
    expect(gait.value).toBe("Normal");
  });

  // PRODUCT OWNER CORRECTION (2026-11-16) "Musculoskeletal Final Hospice
  // Workflow Correction" -- "Not Assessed" is a selectable value but must
  // NOT read as complete ("Do not display a green check beside Gait: Not
  // Assessed"). Gait is applicable and must be actually assessed once
  // Ambulatory.
  it("reads incomplete (not complete) when Gait is directly 'Not Assessed' for an Ambulatory patient", () => {
    const items = computeMusculoskeletalDocumentationCoverage({
      ambulationStatus: "Ambulatory",
      gait: "Not Assessed",
    });
    const gait = items.find((i) => i.key === "gait");
    expect(gait.complete).toBe(false);
    expect(gait.value).toBeNull();
  });

  it("requires Gait Details when Gait = Other before reading complete", () => {
    const items = computeMusculoskeletalDocumentationCoverage({
      ambulationStatus: "Ambulatory",
      gait: "Other",
    });
    const gait = items.find((i) => i.key === "gait");
    expect(gait.complete).toBe(false);
  });

  it("is complete and includes Gait Details in the summary once Gait = Other is documented", () => {
    const items = computeMusculoskeletalDocumentationCoverage({
      ambulationStatus: "Ambulatory",
      gait: "Other",
      gaitDetails: "Festinating gait",
    });
    const gait = items.find((i) => i.key === "gait");
    expect(gait.complete).toBe(true);
    expect(gait.value).toBe("Other — Festinating gait");
  });
});

// PRODUCT OWNER CORRECTION (2026-11-16) "MSK Rehabilitation-Thinking
// Removal" -- Contractures Severity is removed as an editable concept;
// completion and the Coverage pill now key off Present -> Location only.
describe("computeMusculoskeletalDocumentationCoverage -- Contractures item (Severity removed)", () => {
  const findContractures = (d) => computeMusculoskeletalDocumentationCoverage(d).find((i) => i.key === "contractures");

  it("is incomplete when Present is unanswered", () => {
    const item = findContractures({});
    expect(item.complete).toBe(false);
  });

  it("is complete and reads 'Not Present' when Present is No", () => {
    const item = findContractures({ contracturesPresent: false });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Not Present");
  });

  it("is incomplete when Present is Yes but no Location is selected (even if a legacy Severity value exists)", () => {
    const item = findContractures({ contracturesPresent: true, contractures: "Moderate" });
    expect(item.complete).toBe(false);
  });

  it("is complete and summarizes Location only (no Severity) when Present is Yes with a Location", () => {
    const item = findContractures({
      contracturesPresent: true,
      contractures: "Moderate",
      contracturesLocation: ["Bilateral lower extremities"],
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Bilateral lower extremities");
  });
});

// PRODUCT OWNER DIRECTIVE "Ambulation Status Safety Validation" / "SNS
// Global Clinical Safety Rule" -- MSK ONLY. Ambulation Status is a
// safety-critical Mobility anchor: unresolved (blank/"Not Assessed")
// must be flagged immediately, "Defer to Last" is a transient workflow
// state that never completes/waives the field, Documentation Coverage
// stays amber while unresolved, and Validate & Lock hard-blocks with no
// override. `isMskMobilityComplete` is the single completeness predicate
// shared by BOTH the `mobility` Coverage item and `validateRNICA`'s Lock
// gate, so the two can never disagree. No other Body System, field, or
// workflow is touched by this test file.
describe("isMskMobilityComplete -- standalone predicate shared by Coverage and validateRNICA", () => {
  it("is incomplete when Ambulation Status is blank", () => {
    expect(isMskMobilityComplete({})).toBe(false);
  });

  it("is incomplete when Ambulation Status is explicitly 'Not Assessed'", () => {
    expect(isMskMobilityComplete({ ambulationStatus: "Not Assessed" })).toBe(false);
  });

  it("is complete for a fully-documented Ambulatory pathway", () => {
    expect(isMskMobilityComplete({
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Stand-By Assist",
      stepsBeforeResting: "6-10 Steps",
      gait: "Unsteady",
    })).toBe(true);
  });

  it("is complete for Non-Ambulatory + Out-of-Bed Activity 'No' (no further fields required)", () => {
    expect(isMskMobilityComplete({ ambulationStatus: "Non-Ambulatory", outOfBedActivity: "No" })).toBe(true);
  });

  it("is complete for Bedbound + Repositioning Support answered", () => {
    expect(isMskMobilityComplete({ ambulationStatus: "Bedbound", repositioningSupport: "2-Person Assist" })).toBe(true);
  });

  it("never disagrees with the `mobility` Documentation Coverage item's own `complete` flag, across every pathway", () => {
    const samples = [
      {},
      { ambulationStatus: "Not Assessed" },
      { ambulationStatus: "Ambulatory" },
      { ambulationStatus: "Ambulatory", ambulationAssistance: "Independent", stepsBeforeResting: "11+ Steps", gait: "Normal" },
      { ambulationStatus: "Non-Ambulatory" },
      { ambulationStatus: "Non-Ambulatory", outOfBedActivity: "Not Tolerated" },
      {
        ambulationStatus: "Non-Ambulatory", outOfBedActivity: "Yes", outOfBedPosition: "Wheelchair",
        assistanceToLeaveBed: "2-Person Assist", nonAmbulatoryMobilityConcerns: ["No Observed Mobility Concern"],
      },
      { ambulationStatus: "Bedbound" },
      { ambulationStatus: "Bedbound", repositioningSupport: "Stand-By Assist" },
    ];
    samples.forEach((d) => {
      const coverageItem = computeMusculoskeletalDocumentationCoverage(d).find((i) => i.key === "mobility");
      expect(isMskMobilityComplete(d)).toBe(coverageItem.complete);
    });
  });
});

describe("computeMusculoskeletalDocumentationCoverage -- Mobility unresolvedHint top-priority Ambulation Status branch", () => {
  const findMobility = (d) => computeMusculoskeletalDocumentationCoverage(d).find((i) => i.key === "mobility");

  it("reads the exact approved 'Ambulation Status required' text when blank, ahead of every other hint", () => {
    expect(findMobility({}).unresolvedHint).toBe("Ambulation Status required");
  });

  it("reads the exact approved 'Ambulation Status required' text when explicitly 'Not Assessed'", () => {
    expect(findMobility({ ambulationStatus: "Not Assessed" }).unresolvedHint).toBe("Ambulation Status required");
  });

  it("stays amber (incomplete) regardless of the transient ambulationStatusDeferred workflow flag -- Coverage never reads it", () => {
    const deferred = findMobility({ ambulationStatusDeferred: true });
    const notDeferred = findMobility({ ambulationStatusDeferred: false });
    expect(deferred.complete).toBe(false);
    expect(notDeferred.complete).toBe(false);
    expect(deferred.unresolvedHint).toBe(notDeferred.unresolvedHint);
  });
});

describe("computeMobilityStatusClearPatch -- never touches ambulationStatusDeferred", () => {
  it("does not include ambulationStatusDeferred in its returned patch for any status, so the passive load-time reconciliation effect (which unconditionally replays every clearPatch entry) can never silently wipe a saved, deferred chart on reload", () => {
    ["Ambulatory", "Non-Ambulatory", "Bedbound", "Not Assessed", ""].forEach((status) => {
      expect(Object.prototype.hasOwnProperty.call(computeMobilityStatusClearPatch(status), "ambulationStatusDeferred")).toBe(false);
    });
  });
});

describe("INITIAL_FORM -- ambulationStatusDeferred default", () => {
  it("defaults to false (transient workflow state, never undefined/missing)", () => {
    expect(INITIAL_FORM.musculoskeletal.ambulationStatusDeferred).toBe(false);
  });
});

// Builds a formData object that is fully VALID for every validateRNICA
// requirement EXCEPT whatever musculoskeletal overrides are supplied --
// mode "ongoing" with no assessmentType skips the HOPE-timepoint and
// admission-order requirement blocks entirely, isolating the assertions
// below to the always-checked Demographics/Finalization fields (filled
// in below) plus the new MSK Ambulation Status check.
function buildFormDataForLockCheck(musculoskeletalOverrides = {}) {
  const base = JSON.parse(JSON.stringify(INITIAL_FORM));
  base.demographics.firstName = "Test";
  base.demographics.lastName = "Patient";
  base.demographics.dob = "1950-01-01";
  base.demographics.gender = "Female";
  base.finalization.clinicalNarrative = "Narrative on file.";
  base.finalization.clinicianSignature = "RN Test, RN";
  base.finalization.signatureCertification = true;
  // Safety & Clinical Risk is also a Lock-blocking requirement
  // (consolidated single `safety.assessment` gate) -- fully satisfy it
  // here so these MSK-focused assertions stay isolated to the one new
  // Ambulation Status error, per this helper's own documented intent.
  base.safety = {
    ...base.safety,
    fallRiskMorseHistoryOfFalling: "No",
    fallRiskMorseSecondaryDiagnosis: "No",
    fallRiskMorseAmbulatoryAid: "None/Bed Rest/Nurse Assist",
    fallRiskMorseIvHeparinLock: "No",
    fallRiskMorseGaitTransferring: "Normal/Bedrest/Immobile",
    fallRiskMorseMentalStatus: "Oriented to Own Ability",
    hospiceClinicalFallSafetyLevel: "Standard Precautions",
    environmentalHomeConcerns: ["No Environmental Concerns Identified"],
    environmentalStaffSafetyStatus: "No Staff Safety Concern Identified",
    oxygenSafetyConfirmedNotApplicable: true,
    disasterLevel: "Level 3 — No need for hospice to assist; has adequate assistance available",
    disasterPlannedPlacement: "Remain at Residence",
    disasterResponsibleSupport: "Daughter (lives nearby)",
    disasterTransportationStatus: "Reliable Transportation Available",
  };
  base.musculoskeletal = { ...base.musculoskeletal, ...musculoskeletalOverrides };
  return base;
}

describe("validateRNICA -- Ambulation Status hard-blocks Lock (MSK only, no override/bypass)", () => {
  it("produces the exact approved finalization error when Ambulation Status is blank", () => {
    const v = validateRNICA(buildFormDataForLockCheck({}), "ongoing");
    expect(v.errors["musculoskeletal.ambulationStatus"]).toBe(
      "Ambulation Status must be completed before this assessment can be finalized."
    );
    expect(v.isValid).toBe(false);
  });

  it("produces the same error when Ambulation Status is explicitly 'Not Assessed'", () => {
    const v = validateRNICA(buildFormDataForLockCheck({ ambulationStatus: "Not Assessed" }), "ongoing");
    expect(v.errors["musculoskeletal.ambulationStatus"]).toBeTruthy();
  });

  it("does NOT block Lock for a complete Ambulatory pathway", () => {
    const v = validateRNICA(buildFormDataForLockCheck({
      ambulationStatus: "Ambulatory", ambulationAssistance: "Independent",
      stepsBeforeResting: "11+ Steps", gait: "Normal",
    }), "ongoing");
    expect(v.errors["musculoskeletal.ambulationStatus"]).toBeUndefined();
    expect(v.isValid).toBe(true);
  });

  it("does NOT block Lock for a complete Non-Ambulatory 'Does Not Routinely Leave Bed' pathway", () => {
    const v = validateRNICA(buildFormDataForLockCheck({
      ambulationStatus: "Non-Ambulatory", outOfBedActivity: "No",
    }), "ongoing");
    expect(v.errors["musculoskeletal.ambulationStatus"]).toBeUndefined();
    expect(v.isValid).toBe(true);
  });

  it("blocks Lock for an incomplete Non-Ambulatory 'Yes' pathway missing Mobility Concerns", () => {
    const v = validateRNICA(buildFormDataForLockCheck({
      ambulationStatus: "Non-Ambulatory", outOfBedActivity: "Yes",
      outOfBedPosition: "Wheelchair", assistanceToLeaveBed: "2-Person Assist",
    }), "ongoing");
    expect(v.errors["musculoskeletal.ambulationStatus"]).toBeTruthy();
    expect(v.isValid).toBe(false);
  });

  it("does NOT block Lock for a fully-documented Non-Ambulatory 'Yes' pathway", () => {
    const v = validateRNICA(buildFormDataForLockCheck({
      ambulationStatus: "Non-Ambulatory", outOfBedActivity: "Yes",
      outOfBedPosition: "Wheelchair", assistanceToLeaveBed: "2-Person Assist",
      nonAmbulatoryMobilityConcerns: ["No Observed Mobility Concern"],
    }), "ongoing");
    expect(v.errors["musculoskeletal.ambulationStatus"]).toBeUndefined();
    expect(v.isValid).toBe(true);
  });

  it("blocks Lock for an incomplete Bedbound pathway (Repositioning Support not assessed)", () => {
    const v = validateRNICA(buildFormDataForLockCheck({ ambulationStatus: "Bedbound" }), "ongoing");
    expect(v.errors["musculoskeletal.ambulationStatus"]).toBeTruthy();
    expect(v.isValid).toBe(false);
  });

  it("does NOT block Lock for a complete Bedbound pathway", () => {
    const v = validateRNICA(buildFormDataForLockCheck({
      ambulationStatus: "Bedbound", repositioningSupport: "2-Person Assist",
    }), "ongoing");
    expect(v.errors["musculoskeletal.ambulationStatus"]).toBeUndefined();
    expect(v.isValid).toBe(true);
  });

  it("hard-blocks overall isValid even when Ambulation Status is the ONLY incomplete field in the entire assessment", () => {
    const v = validateRNICA(buildFormDataForLockCheck({}), "ongoing");
    expect(Object.keys(v.errors)).toEqual(["musculoskeletal.ambulationStatus"]);
    expect(v.isValid).toBe(false);
  });

  it("'Defer to Last' (ambulationStatusDeferred=true) does NOT suppress the error or unblock Lock -- deferring never completes or waives the field", () => {
    const deferred = validateRNICA(buildFormDataForLockCheck({ ambulationStatusDeferred: true }), "ongoing");
    expect(deferred.errors["musculoskeletal.ambulationStatus"]).toBeTruthy();
    expect(deferred.isValid).toBe(false);
  });

  it("introduces no other MSK or cross-system error/warning as a side effect -- scope-locked to the one new error key", () => {
    const complete = validateRNICA(buildFormDataForLockCheck({
      ambulationStatus: "Bedbound", repositioningSupport: "Stand-By Assist",
    }), "ongoing");
    expect(complete.isValid).toBe(true);
    expect(Object.keys(complete.errors)).toHaveLength(0);
  });
});

// PRODUCT OWNER CORRECTION (2026-11-16) "Musculoskeletal Dependency and
// Display Correction" -- a legacy/retired-option value must never be
// treated as a complete, displayable Coverage answer.
describe("computeMusculoskeletalDocumentationCoverage -- legacy/retired values never display", () => {
  it("Weakness: a legacy 'Paralysis' value reads incomplete, not displayed", () => {
    const items = computeMusculoskeletalDocumentationCoverage({ weakness: "Paralysis" });
    const weakness = items.find((i) => i.key === "weakness");
    expect(weakness.complete).toBe(false);
    expect(weakness.value).toBeNull();
  });

  it("Weakness: a current option (e.g. 'Moderate') still reads complete", () => {
    const items = computeMusculoskeletalDocumentationCoverage({ weakness: "Moderate" });
    const weakness = items.find((i) => i.key === "weakness");
    expect(weakness.complete).toBe(true);
    expect(weakness.value).toBe("Moderate");
  });

  it("Gait: a legacy 'Unable' value reads incomplete, not displayed, for an Ambulatory patient", () => {
    const items = computeMusculoskeletalDocumentationCoverage({ ambulationStatus: "Ambulatory", gait: "Unable" });
    const gait = items.find((i) => i.key === "gait");
    expect(gait.complete).toBe(false);
    expect(gait.value).toBeNull();
  });

  it("Gait: a current option (e.g. 'Unsteady') still reads complete for an Ambulatory patient", () => {
    const items = computeMusculoskeletalDocumentationCoverage({ ambulationStatus: "Ambulatory", gait: "Unsteady" });
    const gait = items.find((i) => i.key === "gait");
    expect(gait.complete).toBe(true);
    expect(gait.value).toBe("Unsteady");
  });
});

// PRODUCT OWNER CORRECTION (2026-11-16) "Musculoskeletal Dependency and
// Display Correction" -- "Show and require both Location and Prosthesis
// status when Amputation = Yes."
describe("computeMusculoskeletalDocumentationCoverage -- Limb Status requires both Location and Prosthesis when Yes", () => {
  const findLimbStatus = (d) => computeMusculoskeletalDocumentationCoverage(d).find((i) => i.key === "limbStatus");

  it("is incomplete when Amputation is unanswered", () => {
    expect(findLimbStatus({}).complete).toBe(false);
  });

  it("is complete and reads 'No Amputation' when Amputation is No", () => {
    const item = findLimbStatus({ amputationPresent: false });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("No Amputation");
  });

  it("is incomplete when Amputation is Yes with Location but no Prosthesis answer", () => {
    const item = findLimbStatus({ amputationPresent: true, amputationLocation: ["Right lower extremity"] });
    expect(item.complete).toBe(false);
  });

  it("is incomplete when Amputation is Yes with a Prosthesis answer but no Location", () => {
    const item = findLimbStatus({ amputationPresent: true, prosthesisCurrentlyUsed: false });
    expect(item.complete).toBe(false);
  });

  it("is complete once Amputation is Yes with both Location and a Prosthesis answer", () => {
    const item = findLimbStatus({
      amputationPresent: true,
      amputationLocation: ["Right lower extremity"],
      prosthesisCurrentlyUsed: false,
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Right lower extremity Amputation — No Prosthesis");
  });
});

// PRODUCT OWNER DIRECTIVE "Musculoskeletal Final Safety-State Correction"
// -- "Unable to Tolerate Repositioning" is a documented positive safety
// finding (not an unresolved field); documentation completion (Mobility
// pill) and clinical-response resolution (Safety Response pill) are two
// separate states that must never be conflated.
describe("Musculoskeletal Final Safety-State Correction -- Repositioning Immediate Response", () => {
  const bedboundUnable = { ambulationStatus: "Bedbound", repositioningSupport: "Unable to Tolerate Repositioning" };

  it("isMskMobilityComplete: Mobility itself reads complete for Bedbound + Unable to Tolerate Repositioning regardless of Immediate Response", () => {
    expect(isMskMobilityComplete(bedboundUnable)).toBe(true);
  });

  it("Mobility Coverage summary stays concise/unchanged: 'Bedbound — Unable to Tolerate Repositioning'", () => {
    const mobility = computeMusculoskeletalDocumentationCoverage(bedboundUnable).find((i) => i.key === "mobility");
    expect(mobility.complete).toBe(true);
    expect(mobility.value).toBe("Bedbound — Unable to Tolerate Repositioning");
  });

  it("isMskRepositioningResponseComplete: reads complete/not-applicable for any Repositioning Support value other than 'Unable to Tolerate Repositioning'", () => {
    expect(isMskRepositioningResponseComplete({ ambulationStatus: "Bedbound", repositioningSupport: "Maximum Assistance" })).toBe(true);
    expect(isMskRepositioningResponseComplete({ ambulationStatus: "Bedbound", repositioningSupport: "" })).toBe(true);
  });

  it("isMskRepositioningResponseComplete: incomplete when Unable to Tolerate Repositioning has no Immediate Response selected", () => {
    expect(isMskRepositioningResponseComplete(bedboundUnable)).toBe(false);
  });

  it("isMskRepositioningResponseComplete: complete once at least one Immediate Response (other than Other) is selected", () => {
    expect(isMskRepositioningResponseComplete({ ...bedboundUnable, repositioningImmediateResponse: ["Comfort Measures Provided"] })).toBe(true);
  });

  it("isMskRepositioningResponseComplete: 'Other' requires Immediate Response Details", () => {
    expect(isMskRepositioningResponseComplete({ ...bedboundUnable, repositioningImmediateResponse: ["Other"] })).toBe(false);
    expect(isMskRepositioningResponseComplete({ ...bedboundUnable, repositioningImmediateResponse: ["Other"], repositioningImmediateResponseDetails: "Notified on-call physician" })).toBe(true);
  });

  it("Safety Response Coverage item is suppressed entirely unless Repositioning Support is directly 'Unable to Tolerate Repositioning'", () => {
    const notApplicable = computeMusculoskeletalDocumentationCoverage({ ambulationStatus: "Bedbound", repositioningSupport: "Maximum Assistance" });
    expect(notApplicable.find((i) => i.key === "repositioningSafetyResponse")).toBeUndefined();
  });

  it("Safety Response Coverage item appears amber ('Immediate response required') when response is missing", () => {
    const items = computeMusculoskeletalDocumentationCoverage(bedboundUnable);
    const safetyResponse = items.find((i) => i.key === "repositioningSafetyResponse");
    expect(safetyResponse).toBeDefined();
    expect(safetyResponse.complete).toBe(false);
    expect(safetyResponse.unresolvedHint).toBe("Immediate response required");
  });

  it("Safety Response Coverage item reads 'Documented' once Immediate Response is recorded", () => {
    const items = computeMusculoskeletalDocumentationCoverage({ ...bedboundUnable, repositioningImmediateResponse: ["Repositioning Modified"] });
    const safetyResponse = items.find((i) => i.key === "repositioningSafetyResponse");
    expect(safetyResponse.complete).toBe(true);
    expect(safetyResponse.value).toBe("Documented");
  });

  const everyOtherMskFieldComplete = {
    weakness: "None",
    physicalMotorLimitationPresent: "No",
    rigidityPresent: false,
    contracturesPresent: false,
    romLossPresent: false,
    muscleWastingPresent: false,
    amputationPresent: false,
    musculoskeletalIssues: ["None"],
    assistiveDevices: ["None"],
    clinicalStatusChange: "No Change",
    notes: "Caregiver reports repositioning tolerance has declined since the previous assessment.",
  };

  it("MSK does not read 'Reviewed' while Immediate Response is missing, even if every other field is complete", () => {
    const status = computeMusculoskeletalWorkflowStatus({ ...everyOtherMskFieldComplete, ...bedboundUnable });
    expect(status.label).not.toBe("Reviewed");
  });

  it("MSK reads 'Reviewed' once Immediate Response is documented and every other field is complete", () => {
    const status = computeMusculoskeletalWorkflowStatus({
      ...everyOtherMskFieldComplete,
      ...bedboundUnable,
      repositioningImmediateResponse: ["Comfort Measures Provided"],
    });
    expect(status.label).toBe("Reviewed");
  });

  it("validateRNICA: finalization fails with the exact approved message while Immediate Response is missing, and Notes alone does not satisfy it", () => {
    const formData = {
      ...INITIAL_FORM,
      musculoskeletal: { ...INITIAL_FORM.musculoskeletal, ...bedboundUnable, notes: "Caregiver reports repositioning tolerance has declined since the previous assessment." },
    };
    const result = validateRNICA(formData, "interactive", "comprehensive");
    expect(result.errors["musculoskeletal.repositioningImmediateResponse"]).toBe(
      "Document the immediate response to the patient's inability to tolerate repositioning before finalizing."
    );
  });

  it("validateRNICA: finalization no longer reports the Immediate Response error once it is documented", () => {
    const formData = {
      ...INITIAL_FORM,
      musculoskeletal: {
        ...INITIAL_FORM.musculoskeletal,
        ...bedboundUnable,
        repositioningImmediateResponse: ["Repositioning Stopped"],
      },
    };
    const result = validateRNICA(formData, "interactive", "comprehensive");
    expect(result.errors["musculoskeletal.repositioningImmediateResponse"]).toBeUndefined();
  });

  it("'Maximum Assistance' does not trigger the Immediate Response workflow (Safety Response not shown, no Lock error)", () => {
    const maxAssist = { ambulationStatus: "Bedbound", repositioningSupport: "Maximum Assistance" };
    const items = computeMusculoskeletalDocumentationCoverage(maxAssist);
    expect(items.find((i) => i.key === "repositioningSafetyResponse")).toBeUndefined();
    const formData = { ...INITIAL_FORM, musculoskeletal: { ...INITIAL_FORM.musculoskeletal, ...maxAssist } };
    const result = validateRNICA(formData, "interactive", "comprehensive");
    expect(result.errors["musculoskeletal.repositioningImmediateResponse"]).toBeUndefined();
  });

  it("computeMobilityStatusClearPatch: moving Ambulation Status away from Bedbound also clears Immediate Response + its Details", () => {
    const patch = computeMobilityStatusClearPatch("Ambulatory");
    expect(patch.repositioningImmediateResponse).toEqual([]);
    expect(patch.repositioningImmediateResponseDetails).toBe("");
  });

  it("computeMobilityStatusClearPatch: staying Bedbound does not clear Immediate Response (only the active-change onChange interceptor, not this status-group patch, clears it when the value itself changes away from Unable to Tolerate Repositioning)", () => {
    const patch = computeMobilityStatusClearPatch("Bedbound");
    expect(patch.repositioningImmediateResponse).toBeUndefined();
    expect(patch.repositioningImmediateResponseDetails).toBeUndefined();
  });
});

describe("Documentation Coverage is flat (no internal group titles)", () => {
  it("no MSK Coverage item carries a `group` property", () => {
    const items = computeMusculoskeletalDocumentationCoverage({});
    for (const item of items) {
      expect(item.group).toBeUndefined();
    }
  });
});

// PRODUCT OWNER DIRECTIVE "Musculoskeletal Final Stabilization" --
// CRITICAL DEFECT regression coverage: the section accordion badge must
// never read "Reviewed" while a required, applicable MSK Coverage item
// is still unresolved. `computeMusculoskeletalWorkflowStatus` reuses
// `computeMusculoskeletalDocumentationCoverage` directly, so these tests
// assert against the exact same data shapes used by the Coverage tests
// above, not a parallel/duplicated completeness model.
describe("computeMusculoskeletalWorkflowStatus -- section badge can never disagree with Coverage", () => {
  const fullyComplete = {
    weakness: "None",
    physicalMotorLimitationPresent: "No",
    muscleWastingPresent: false,
    rigidityPresent: false,
    contracturesPresent: false,
    romLossPresent: false,
    musculoskeletalIssues: ["None"],
    amputationPresent: false,
    ambulationStatus: "Ambulatory",
    ambulationAssistance: "Independent",
    stepsBeforeResting: "More Than 50 Steps",
    gait: "Normal",
    assistiveDevices: ["None"],
    clinicalStatusChange: "No Change",
  };

  it("reads 'Not Started' when nothing has been documented", () => {
    const status = computeMusculoskeletalWorkflowStatus({});
    expect(status.code).toBe("not_started");
    expect(status.label).toBe("Not Started");
  });

  it("reads 'In Progress' -- NOT 'Reviewed' -- when Weakness is documented but Ambulation Status is still blank", () => {
    const status = computeMusculoskeletalWorkflowStatus({ weakness: "Mild" });
    expect(status.code).toBe("in_progress");
    expect(status.label).toBe("In Progress");
  });

  it("reads 'In Progress' -- NOT 'Reviewed' -- when Ambulation Status is documented but Weakness is still unassessed", () => {
    const status = computeMusculoskeletalWorkflowStatus({
      ambulationStatus: "Ambulatory", ambulationAssistance: "Independent",
      stepsBeforeResting: "More Than 50 Steps", gait: "Normal",
    });
    expect(status.code).toBe("in_progress");
    expect(status.label).toBe("In Progress");
  });

  it("reads 'Reviewed' only once every applicable Coverage item is complete (Ambulatory pathway)", () => {
    const status = computeMusculoskeletalWorkflowStatus(fullyComplete);
    expect(status.code).toBe("ready_for_review");
    expect(status.label).toBe("Reviewed");
    expect(status.variant).toBe("success");
  });

  it("reads 'Reviewed' for a fully-complete Non-Ambulatory pathway (Gait correctly excluded, not required)", () => {
    const status = computeMusculoskeletalWorkflowStatus({
      ...fullyComplete,
      ambulationStatus: "Non-Ambulatory",
      ambulationAssistance: undefined,
      stepsBeforeResting: undefined,
      gait: undefined,
      outOfBedActivity: "No",
    });
    expect(status.code).toBe("ready_for_review");
    expect(status.label).toBe("Reviewed");
  });

  it("reads 'Reviewed' for a fully-complete Bedbound pathway (Gait correctly excluded, not required)", () => {
    const status = computeMusculoskeletalWorkflowStatus({
      ...fullyComplete,
      ambulationStatus: "Bedbound",
      ambulationAssistance: undefined,
      stepsBeforeResting: undefined,
      gait: undefined,
      repositioningSupport: "Stand-By Assist",
    });
    expect(status.code).toBe("ready_for_review");
    expect(status.label).toBe("Reviewed");
  });

  it("does NOT read 'Reviewed' merely because Clinical Status Change is 'Not Applicable' while other required fields remain blank", () => {
    const status = computeMusculoskeletalWorkflowStatus({ clinicalStatusChange: "Not Applicable" });
    expect(status.code).not.toBe("ready_for_review");
    expect(status.label).not.toBe("Reviewed");
  });

  it("drops back out of 'Reviewed' the instant a previously-complete field is cleared (Ambulation Status reset to blank)", () => {
    const status = computeMusculoskeletalWorkflowStatus({ ...fullyComplete, ambulationStatus: "Not Assessed" });
    expect(status.code).not.toBe("ready_for_review");
  });

  it("the section badge and the Coverage array can never disagree -- 'Reviewed' iff every Coverage item is complete", () => {
    const samples = [
      {},
      { weakness: "Moderate" },
      fullyComplete,
      { ...fullyComplete, ambulationStatus: "Non-Ambulatory", ambulationAssistance: undefined, stepsBeforeResting: undefined, gait: undefined, outOfBedActivity: "Yes" },
    ];
    samples.forEach((d) => {
      const coverage = computeMusculoskeletalDocumentationCoverage(d);
      const allComplete = coverage.every((item) => item.complete);
      const status = computeMusculoskeletalWorkflowStatus(d);
      expect(status.code === "ready_for_review").toBe(allComplete);
    });
  });
});

// PRODUCT OWNER DIRECTIVE "Musculoskeletal Motor-Limitation Gap" -- new
// MSK-only "Physical Motor Limitation" field group. Single-select Primary
// Motor Limitation (prevents contradictory combinations), fully
// independent of Weakness/Muscle Wasting/Contractures/ROM
// Loss/Ambulation/Walking Aid/Repositioning Support (no auto-derivation).
describe("computeMusculoskeletalDocumentationCoverage -- Physical Motor Limitation item", () => {
  const findMotorLimitation = (d) => computeMusculoskeletalDocumentationCoverage(d).find((i) => i.key === "physicalMotorLimitation");

  it("is incomplete with unresolvedHint 'Not Assessed' when physicalMotorLimitationPresent is blank", () => {
    const item = findMotorLimitation({});
    expect(item).toBeDefined();
    expect(item.complete).toBe(false);
    expect(item.unresolvedHint).toBe("Not Assessed");
  });

  it("is incomplete with unresolvedHint 'Not Assessed' when physicalMotorLimitationPresent is directly 'Not Assessed'", () => {
    const item = findMotorLimitation({ physicalMotorLimitationPresent: "Not Assessed" });
    expect(item.complete).toBe(false);
    expect(item.unresolvedHint).toBe("Not Assessed");
  });

  it("is complete with value 'Not Present' when physicalMotorLimitationPresent is 'No'", () => {
    const item = findMotorLimitation({ physicalMotorLimitationPresent: "No" });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Not Present");
  });

  it("is incomplete with unresolvedHint 'Primary Motor Limitation required' when Present is 'Yes' but Type is blank", () => {
    const item = findMotorLimitation({ physicalMotorLimitationPresent: "Yes" });
    expect(item.complete).toBe(false);
    expect(item.unresolvedHint).toBe("Primary Motor Limitation required");
  });

  it("is complete with the exact Type string as value for a direct pattern (e.g. 'Right Hemiplegia')", () => {
    const item = findMotorLimitation({ physicalMotorLimitationPresent: "Yes", physicalMotorLimitationType: "Right Hemiplegia" });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Right Hemiplegia");
  });

  it("supports 'Bilateral Hemiparesis' as an approved Type value", () => {
    const item = findMotorLimitation({ physicalMotorLimitationPresent: "Yes", physicalMotorLimitationType: "Bilateral Hemiparesis" });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Bilateral Hemiparesis");
  });

  it("is incomplete with unresolvedHint 'Motor Limitation Details required' when Type is 'Multiple / Other' but Details is blank", () => {
    const item = findMotorLimitation({ physicalMotorLimitationPresent: "Yes", physicalMotorLimitationType: "Multiple / Other" });
    expect(item.complete).toBe(false);
    expect(item.unresolvedHint).toBe("Motor Limitation Details required");
  });

  it("is complete once Details is provided for 'Multiple / Other'", () => {
    const item = findMotorLimitation({
      physicalMotorLimitationPresent: "Yes",
      physicalMotorLimitationType: "Multiple / Other",
      physicalMotorLimitationDetails: "Right hemiparesis with superimposed generalized deconditioning",
    });
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Multiple / Other");
  });

  it("Coverage never re-prefixes the item's own label inside value/unresolvedHint (shared pill component applies the 'Label:' prefix)", () => {
    const notAssessed = findMotorLimitation({});
    const notPresent = findMotorLimitation({ physicalMotorLimitationPresent: "No" });
    const yesPattern = findMotorLimitation({ physicalMotorLimitationPresent: "Yes", physicalMotorLimitationType: "Paraplegia" });
    [notAssessed.unresolvedHint, notPresent.value, yesPattern.value].forEach((text) => {
      expect(text).not.toMatch(/Physical Motor Limitation/i);
    });
  });

  it("is never auto-derived from or dependent on Weakness, Muscle Wasting, Contractures, ROM Loss, Ambulation Status, or Repositioning Support", () => {
    const withUnrelatedFindings = {
      physicalMotorLimitationPresent: "Yes",
      physicalMotorLimitationType: "Right Hemiplegia",
      weakness: "Severe",
      muscleWastingPresent: true,
      muscleWastingDistribution: "Generalized",
      contracturesPresent: true,
      contracturesLocation: ["Bilateral Lower Extremities"],
      romLossPresent: true,
      romLossLocation: ["Upper Extremities"],
      ambulationStatus: "Non-Ambulatory",
      outOfBedActivity: "No",
      repositioningSupport: "Maximum Assistance",
    };
    const item = findMotorLimitation(withUnrelatedFindings);
    expect(item.value).toBe("Right Hemiplegia");
    // and the reverse: no unrelated item silently reflects the motor-limitation pattern
    const weaknessItem = computeMusculoskeletalDocumentationCoverage(withUnrelatedFindings).find((i) => i.key === "weakness");
    expect(weaknessItem.value).not.toMatch(/Hemiplegia/i);
  });
});

describe("computeMusculoskeletalWorkflowStatus -- Physical Motor Limitation participates in the section badge like any other Coverage item", () => {
  it("MSK does not read 'Reviewed' while Physical Motor Limitation is unanswered, even if every other field is complete", () => {
    const status = computeMusculoskeletalWorkflowStatus({
      weakness: "None",
      rigidityPresent: false,
      contracturesPresent: false,
      romLossPresent: false,
      muscleWastingPresent: false,
      amputationPresent: false,
      musculoskeletalIssues: ["None"],
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Independent",
      stepsBeforeResting: "More Than 50 Steps",
      gait: "Normal",
      assistiveDevices: ["None"],
      clinicalStatusChange: "No Change",
    });
    expect(status.label).not.toBe("Reviewed");
  });

  it("MSK reads 'Reviewed' once Physical Motor Limitation is documented (Not Present) alongside every other complete field", () => {
    const status = computeMusculoskeletalWorkflowStatus({
      weakness: "None",
      physicalMotorLimitationPresent: "No",
      rigidityPresent: false,
      contracturesPresent: false,
      romLossPresent: false,
      muscleWastingPresent: false,
      amputationPresent: false,
      musculoskeletalIssues: ["None"],
      ambulationStatus: "Ambulatory",
      ambulationAssistance: "Independent",
      stepsBeforeResting: "More Than 50 Steps",
      gait: "Normal",
      assistiveDevices: ["None"],
      clinicalStatusChange: "No Change",
    });
    expect(status.label).toBe("Reviewed");
  });
});
