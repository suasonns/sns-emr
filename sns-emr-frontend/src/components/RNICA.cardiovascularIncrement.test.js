import { describe, it, expect } from "vitest";
import {
  computeCardiovascularNarrative,
  computeCardiovascularWorkflowStatus,
  cardiovascularHasActionablePocFinding,
  computeCardiovascularDocumentationCoverage,
  resolvePulseDimensionDisplay,
  resolveBpStatusDisplay,
  resolveOrthostaticFindingDisplay,
  resolveBpLegacyDisplay,
  resolveHeartFailureTypeSelection,
} from "./RNICA.jsx";

// PRODUCT OWNER DIRECTIVE (2026-10-13) "Remove The Cardiovascular 4-Path
// Gate -- No Replacement" regression coverage. The former Overview Gate
// (`cardiovascularOverview`/`cardiovascularUnableToAssessReason`/
// `...Other`/`cardiovascularFindingsConfirmedThisVisit`) is retired
// entirely, same precedent as Neurological's Overview Gate removal: the
// nurse documents findings, the software derives status/narrative
// directly from them. Legacy stored values on historical records are
// preserved but no longer read by any active workflow/narrative/POC
// logic -- several tests below verify that inertness explicitly. No
// schema, migration, or persistence changes are exercised here.

describe("computeCardiovascularWorkflowStatus", () => {
  it("returns Not Started when nothing has been documented", () => {
    expect(computeCardiovascularWorkflowStatus({}).code).toBe("not_started");
  });

  // PRODUCT OWNER DIRECTIVE (2026-10-13) -- Overview is no longer a
  // separate nurse decision the status can be "in progress" waiting on;
  // `in_progress` was removed entirely. Once any finding is documented,
  // the record is Ready for Review -- there is nothing left to answer.
  it("reports Ready for Review once any finding is documented (no separate Overview step to wait on)", () => {
    expect(computeCardiovascularWorkflowStatus({ fatigue: "Mild" }).code).toBe("ready_for_review");
  });

  it("reports Ready for Review once any pulse/BP/symptom finding is documented", () => {
    expect(computeCardiovascularWorkflowStatus({ chestPain: { present: "Yes" } }).code).toBe("ready_for_review");
    expect(computeCardiovascularWorkflowStatus({ pulseRhythm: "Regular" }).code).toBe("ready_for_review");
  });

  it("is Ready for Review even alongside a preserved abnormal finding -- there is no longer a conflicting path to contradict", () => {
    const status = computeCardiovascularWorkflowStatus({ chestPain: { present: "Yes" }, edema: { present: "Yes" } });
    expect(status.code).toBe("ready_for_review");
    expect(status.variant).toBe("success");
  });

  it("reports Ready for Review for a legacy record carrying a stale cardiovascularOverview value and nothing else", () => {
    const status = computeCardiovascularWorkflowStatus({
      cardiovascularOverview: "Unable to Assess",
      cardiovascularUnableToAssessReason: "Patient unresponsive",
    });
    expect(status.code).toBe("ready_for_review");
    expect(status.variant).toBe("success");
  });

  it("reports Not Started for a blank record even with stray empty-string legacy fields", () => {
    expect(computeCardiovascularWorkflowStatus({ cardiovascularOverview: "", cardiovascularUnableToAssessReason: "" }).code).toBe("not_started");
  });

  it("never deletes or clears a preserved finding while computing status", () => {
    const d = { chestPain: { present: "Yes" }, edema: { present: "Yes" } };
    computeCardiovascularWorkflowStatus(d);
    expect(d.chestPain.present).toBe("Yes");
    expect(d.edema.present).toBe("Yes");
  });
});


describe("resolvePulseDimensionDisplay - legacy pulseQuality aliasing", () => {
  it.each([
    ["Regular", "pulseRhythm", "Regular"],
    ["Irregular", "pulseRhythm", "Irregular"],
    ["Tachycardia", "pulseRate", "Tachycardic"],
    ["Bradycardia", "pulseRate", "Bradycardic"],
    ["Strong", "pulseStrength", "Strong"],
    ["Weak", "pulseStrength", "Weak"],
    ["Thready", "pulseStrength", "Thready"],
    ["Bounding", "pulseStrength", "Bounding"],
    ["Absent", "pulseStrength", "Absent"],
  ])("legacy pulseQuality=%s maps only into %s as %s, leaving other dimensions unanswered", (legacy, dimension, expected) => {
    const d = { pulseQuality: legacy, pulseRhythm: "", pulseRate: "", pulseStrength: "" };
    expect(resolvePulseDimensionDisplay(d, dimension)).toBe(expected);
    ["pulseRhythm", "pulseRate", "pulseStrength"].filter((dim) => dim !== dimension).forEach((otherDim) => {
      expect(resolvePulseDimensionDisplay(d, otherDim)).toBe("");
    });
  });

  it("never overrides an explicitly documented new-field value with the legacy alias", () => {
    const d = { pulseQuality: "Regular", pulseRhythm: "Irregular" };
    expect(resolvePulseDimensionDisplay(d, "pulseRhythm")).toBe("Irregular");
  });

  it("supports independent multi-dimension combinations with no cross-inference", () => {
    const d = { pulseRhythm: "Irregular", pulseRate: "Bradycardic", pulseStrength: "Bounding" };
    expect(resolvePulseDimensionDisplay(d, "pulseRhythm")).toBe("Irregular");
    expect(resolvePulseDimensionDisplay(d, "pulseRate")).toBe("Bradycardic");
    expect(resolvePulseDimensionDisplay(d, "pulseStrength")).toBe("Bounding");
  });

  // Explicit negative assertions requested by the 2026-09-28 audit --
  // resolvePulseDimensionDisplay is a pure, read-only function of its
  // input object: it is called fresh on every render from whatever
  // `formData.cardiovascular` currently holds, so "opening/closing a
  // record", "editing Notes", and "editing Neurological" cannot add a
  // pulse dimension -- there is no code path by which any of those
  // actions could mutate `pulseRhythm`/`pulseRate`/`pulseStrength`, since
  // they never touch the cardiovascular section object at all. A failed
  // save is a network-layer no-op for this pure function: it has no
  // memory of prior calls, so re-invoking it with the same unsaved `d`
  // after a rejected PUT returns byte-identical output.
  it("Regular does not create Pulse Rate = Normal", () => {
    const d = { pulseQuality: "Regular" };
    expect(resolvePulseDimensionDisplay(d, "pulseRate")).toBe("");
  });

  it("Regular does not create Pulse Strength = Strong", () => {
    const d = { pulseQuality: "Regular" };
    expect(resolvePulseDimensionDisplay(d, "pulseStrength")).toBe("");
  });

  it("Strong does not create Pulse Rhythm = Regular", () => {
    const d = { pulseQuality: "Strong" };
    expect(resolvePulseDimensionDisplay(d, "pulseRhythm")).toBe("");
  });

  it("Strong does not create Pulse Rate = Normal", () => {
    const d = { pulseQuality: "Strong" };
    expect(resolvePulseDimensionDisplay(d, "pulseRate")).toBe("");
  });

  it("Tachycardia does not create a Pulse Rhythm value", () => {
    const d = { pulseQuality: "Tachycardia" };
    expect(resolvePulseDimensionDisplay(d, "pulseRhythm")).toBe("");
  });

  it("Tachycardia does not create a Pulse Strength value", () => {
    const d = { pulseQuality: "Tachycardia" };
    expect(resolvePulseDimensionDisplay(d, "pulseStrength")).toBe("");
  });

  it("re-invoking with an identical (e.g. post-failed-save) object is idempotent -- no accumulated/derived state", () => {
    const d = { pulseQuality: "Weak", pulseRhythm: "", pulseRate: "", pulseStrength: "" };
    const first = ["pulseRhythm", "pulseRate", "pulseStrength"].map((dim) => resolvePulseDimensionDisplay(d, dim));
    const second = ["pulseRhythm", "pulseRate", "pulseStrength"].map((dim) => resolvePulseDimensionDisplay(d, dim));
    expect(second).toEqual(first);
    expect(second).toEqual(["", "", "Weak"]);
  });
});

describe("BP Status / Orthostatic Finding legacy aliasing", () => {
  it("aliases a single unambiguous legacy value to BP Status", () => {
    const d = { bpSymptoms: ["Hypotensive"] };
    expect(resolveBpStatusDisplay(d)).toBe("Hypotensive");
    expect(resolveBpLegacyDisplay(d).reviewRequired).toBe(false);
  });

  it("aliases legacy Orthostatic entry to Orthostatic Finding independently of BP Status", () => {
    const d = { bpSymptoms: ["Hypotensive", "Orthostatic"] };
    expect(resolveBpStatusDisplay(d)).toBe("Hypotensive");
    expect(resolveOrthostaticFindingDisplay(d)).toBe("Present");
  });

  it("flags a contradictory legacy array as review-required instead of silently picking one value", () => {
    const d = { bpSymptoms: ["Normal", "Hypertensive"] };
    const legacy = resolveBpLegacyDisplay(d);
    expect(legacy.reviewRequired).toBe(true);
    expect(resolveBpStatusDisplay(d)).toBe("");
    expect(legacy.legacyValues).toEqual(["Normal", "Hypertensive"]);
  });

  it("flags Hypertensive+Hypotensive as contradictory", () => {
    expect(resolveBpLegacyDisplay({ bpSymptoms: ["Hypertensive", "Hypotensive"] }).reviewRequired).toBe(true);
  });

  it("never overrides an explicitly documented new-field value with the legacy alias", () => {
    const d = { bpSymptoms: ["Hypotensive"], bpStatus: "Normal" };
    expect(resolveBpStatusDisplay(d)).toBe("Normal");
  });
});

describe("legacy cardiacDyspnea compatibility -- retired field, no UI gate", () => {
  // PRODUCT OWNER DIRECTIVE (2026-10-13) "Cardiovascular Subjective
  // Review" -- the "Dyspnea Attributed to Cardiac Condition" checkbox
  // and resolveCardiacDyspneaGate (its visibility gate) are retired from
  // active UI: it asked for a cardiac-cause attribution the RN cannot
  // directly observe, not an objective/measurable finding. No
  // replacement RN-facing question was introduced. A pre-retirement
  // record's legacy `cardiacDyspnea: true` is never cleared/rewritten
  // and still contributes to POC-actionable/narrative determinations
  // (see the dedicated assertions in the describe blocks below).
  it("no longer exports a visibility gate for this field", async () => {
    const module = await import("./RNICA.jsx");
    expect(module.resolveCardiacDyspneaGate).toBeUndefined();
  });
});

describe("cardiovascularHasActionablePocFinding", () => {
  it("is false for an empty record", () => {
    expect(cardiovascularHasActionablePocFinding({})).toBe(false);
  });

  it("is false for a stale legacy cardiovascularOverview value alone (no longer read)", () => {
    expect(cardiovascularHasActionablePocFinding({ cardiovascularOverview: "No Current Cardiovascular Concern" })).toBe(false);
    expect(cardiovascularHasActionablePocFinding({
      cardiovascularOverview: "Unable to Assess",
      cardiovascularUnableToAssessReason: "Patient declined",
    })).toBe(false);
    expect(cardiovascularHasActionablePocFinding({ cardiovascularOverview: "New or Worsening Cardiovascular Findings" })).toBe(false);
  });

  it("is false for stable chronic Heart Failure alone (Contradiction 7 correction)", () => {
    expect(cardiovascularHasActionablePocFinding({
      heartFailurePresent: true,
      clinicalStatusChange: "Stable / No Change",
    })).toBe(false);
  });

  it("is false for stable chronic edema alone", () => {
    expect(cardiovascularHasActionablePocFinding({
      edema: { present: "Yes", severity: "1+" },
    })).toBe(false);
  });

  it("is true for any documented Chest Pain Present", () => {
    expect(cardiovascularHasActionablePocFinding({ chestPain: { present: "Yes" } })).toBe(true);
  });

  it("is true for Syncope Present", () => {
    expect(cardiovascularHasActionablePocFinding({ syncope: "Yes" })).toBe(true);
  });

  it("is true for Declining or New Symptom Since Prior clinical status change", () => {
    expect(cardiovascularHasActionablePocFinding({ clinicalStatusChange: "Declining" })).toBe(true);
    expect(cardiovascularHasActionablePocFinding({ clinicalStatusChange: "New Symptom Since Prior Assessment" })).toBe(true);
  });

  it("is true for 3+/4+ edema severity", () => {
    expect(cardiovascularHasActionablePocFinding({ edema: { present: "Yes", severity: "3+" } })).toBe(true);
    expect(cardiovascularHasActionablePocFinding({ edema: { present: "Yes", severity: "4+" } })).toBe(true);
  });

  it("is true for a new thready or absent pulse strength", () => {
    expect(cardiovascularHasActionablePocFinding({ pulseStrength: "Thready" })).toBe(true);
    expect(cardiovascularHasActionablePocFinding({ pulseQuality: "Absent" })).toBe(true);
  });

  it("is true for a new cardiac dyspnea attribution", () => {
    expect(cardiovascularHasActionablePocFinding({ cardiacDyspnea: true })).toBe(true);
  });

  it("is false for device presence alone (pacemaker/ICD/CVL)", () => {
    expect(cardiovascularHasActionablePocFinding({ pacemaker: true, internalDefibrillator: true, centralVenousLine: true })).toBe(false);
  });
});

describe("computeCardiovascularNarrative - blank / legacy-only records", () => {
  it("returns '' (falsy) for a completely blank record, letting the generic fallback apply", () => {
    expect(computeCardiovascularNarrative({})).toBe("");
  });

  it("returns '' for a stale legacy cardiovascularOverview value alone (no longer read)", () => {
    expect(computeCardiovascularNarrative({ cardiovascularOverview: "No Current Cardiovascular Concern" })).toBe("");
    expect(computeCardiovascularNarrative({
      cardiovascularOverview: "Unable to Assess",
      cardiovascularUnableToAssessReason: "Patient unable to participate",
    })).toBe("");
    expect(computeCardiovascularNarrative({ cardiovascularOverview: "Existing Cardiovascular Findings Review" })).toBe("");
  });
});

describe("computeCardiovascularNarrative - documented findings", () => {
  it("generates one concise clause per confirmed finding only", () => {
    const narrative = computeCardiovascularNarrative({
      pulseRhythm: "Irregular",
      pulseRate: "Tachycardic",
      pulseStrength: "Weak",
      chestPain: { present: "Yes", type: "pressure-like" },
      edema: { present: "Yes", severity: "3+", location: ["Bilateral lower extremities"] },
      syncope: "Yes",
      heartFailurePresent: true,
      cardiacDyspnea: true,
    });
    expect(narrative).toContain("Pulse irregular, tachycardic, weak.");
    expect(narrative).toContain("Chest pain present: pressure-like.");
    expect(narrative).toContain("Syncope documented.");
    expect(narrative).toContain("Dyspnea attributed to cardiac condition.");
    // Owner directive (2026-09-28) "Cardiovascular Symptom-Focused Scope
    // Correction": Heart Failure is a diagnosis, not a current
    // sign/symptom, so it must never appear in the narrative even when
    // legacy `heartFailurePresent` data is present on the record.
    expect(narrative).not.toContain("Heart failure documented.");
  });

  it("omits pulse/BP clauses entirely when every dimension is normal", () => {
    const narrative = computeCardiovascularNarrative({
      pulseRhythm: "Regular",
      pulseRate: "Normal",
      pulseStrength: "Strong",
      bpStatus: "Normal",
    });
    expect(narrative).not.toMatch(/Pulse/);
    expect(narrative).not.toMatch(/BP status/);
  });

  it("surfaces a contradictory legacy BP array as a review-required note", () => {
    const narrative = computeCardiovascularNarrative({ bpSymptoms: ["Normal", "Hypertensive"] });
    expect(narrative).toMatch(/Legacy BP values on record \(Normal, Hypertensive\) -- review required\./);
  });
});

// PRODUCT OWNER DIRECTIVE (2026-10-13) -- Cardiovascular's own Clinical
// Status Change list is unchanged and still feeds
// `cardiovascularHasActionablePocFinding` directly; it no longer feeds any
// Overview-path narrative/status branching, since that branching was
// retired.
describe("Clinical Status Change -- Cardiovascular-specific list and legacy compatibility", () => {
  it("treats both the legacy and new decline/worsening strings as POC-actionable", () => {
    expect(cardiovascularHasActionablePocFinding({ clinicalStatusChange: "New Symptom Since Prior Assessment" })).toBe(true);
    expect(cardiovascularHasActionablePocFinding({ clinicalStatusChange: "New or Worsening Finding" })).toBe(true);
  });

  it("never rewrites a legacy Clinical Status Change value while computing status/narrative", () => {
    const d = { clinicalStatusChange: "Symptom Well-Managed" };
    computeCardiovascularWorkflowStatus(d);
    computeCardiovascularNarrative(d);
    expect(d.clinicalStatusChange).toBe("Symptom Well-Managed");
  });
});

// Owner directive (2026-09-28) "Correct the Overview Label" -- exact
// approved wording was "New or Worsening Cardiovascular Findings", not the
// slash-joined "New/Worsening Cardiovascular Findings". PRODUCT OWNER
// DIRECTIVE (2026-10-13) subsequently retired the Overview field from all
// active logic entirely; a stored value under either spelling is now
// just inert legacy data, confirmed identically inert below.
describe("legacy cardiovascularOverview compatibility -- inert field", () => {
  const legacyOverview = "New/Worsening Cardiovascular Findings";

  it("a stored legacy or corrected overview label no longer affects POC-actionable status", () => {
    expect(cardiovascularHasActionablePocFinding({ cardiovascularOverview: legacyOverview })).toBe(false);
    expect(cardiovascularHasActionablePocFinding({ cardiovascularOverview: "New or Worsening Cardiovascular Findings" })).toBe(false);
  });

  it("produces the identical (empty) narrative for the legacy and corrected labels alone", () => {
    const legacy = computeCardiovascularNarrative({ cardiovascularOverview: legacyOverview });
    const current = computeCardiovascularNarrative({ cardiovascularOverview: "New or Worsening Cardiovascular Findings" });
    expect(legacy).toBe(current);
    expect(legacy).toBe("");
  });

  it("produces the identical workflow status for the legacy and corrected labels alone", () => {
    const legacy = computeCardiovascularWorkflowStatus({ cardiovascularOverview: legacyOverview });
    const current = computeCardiovascularWorkflowStatus({ cardiovascularOverview: "New or Worsening Cardiovascular Findings" });
    expect(legacy).toEqual(current);
    expect(legacy.code).toBe("ready_for_review");
  });

  it("never rewrites the legacy stored value while computing status/narrative", () => {
    const d = { cardiovascularOverview: legacyOverview };
    computeCardiovascularWorkflowStatus(d);
    computeCardiovascularNarrative(d);
    expect(d.cardiovascularOverview).toBe(legacyOverview);
  });
});

// Directive (2026-09-28) "Cardiovascular Layout Consolidation" Section 14
// -- Heart Failure Type Unspecified/specific-type mutual exclusion.
describe("resolveHeartFailureTypeSelection", () => {
  it("selecting Unspecified clears any specific types already selected", () => {
    expect(resolveHeartFailureTypeSelection(["Systolic"], ["Systolic", "Unspecified"])).toEqual(["Unspecified"]);
  });

  it("selecting a specific type while Unspecified is active removes Unspecified", () => {
    expect(resolveHeartFailureTypeSelection(["Unspecified"], ["Unspecified", "Systolic"])).toEqual(["Systolic"]);
  });

  it("selecting both Systolic and Diastolic together is not corrected (never mutually exclusive with each other)", () => {
    expect(resolveHeartFailureTypeSelection(["Systolic"], ["Systolic", "Diastolic"])).toBeNull();
  });

  it("returns null (no correction) for an ordinary toggle with no Unspecified involved", () => {
    expect(resolveHeartFailureTypeSelection([], ["Diastolic"])).toBeNull();
    expect(resolveHeartFailureTypeSelection(["Diastolic"], [])).toBeNull();
  });

  it("re-selecting Unspecified alone when it was already the only value is a no-op (no correction needed)", () => {
    expect(resolveHeartFailureTypeSelection(["Unspecified"], ["Unspecified"])).toBeNull();
  });
});

// PRODUCT OWNER DIRECTIVE (2026-10-13) retired the per-field clinician
// confirmation checkbox (`cardiovascularFindingsConfirmedThisVisit`)
// entirely along with the Overview Gate it belonged to -- a stored
// legacy value is now just inert documented data like any other field.
describe("legacy cardiovascularFindingsConfirmedThisVisit compatibility -- inert field", () => {
  it("no longer affects workflow status in either direction", () => {
    expect(computeCardiovascularWorkflowStatus({ cardiovascularFindingsConfirmedThisVisit: true }).code).toBe("ready_for_review");
    expect(computeCardiovascularWorkflowStatus({ cardiovascularFindingsConfirmedThisVisit: false }).code).toBe("not_started");
  });

  it("never affects whether a POC finding is actionable", () => {
    expect(cardiovascularHasActionablePocFinding({ cardiovascularFindingsConfirmedThisVisit: true })).toBe(false);
  });

  it("never rewrites a preserved abnormal finding while computing status", () => {
    const d = {
      cardiovascularFindingsConfirmedThisVisit: true,
      heartFailurePresent: true,
    };
    computeCardiovascularWorkflowStatus(d);
    expect(d.heartFailurePresent).toBe(true);
  });
});

// PRODUCT OWNER DIRECTIVE (2026-10-13) "Add Cardiovascular Documentation
// Coverage" Phase 1 -- regression coverage for
// computeCardiovascularDocumentationCoverage, mirroring the test shape
// already used for its Neurological counterpart.
describe("computeCardiovascularDocumentationCoverage", () => {
  it("reports every item unresolved on a blank record except the always-complete Devices item", () => {
    const coverage = computeCardiovascularDocumentationCoverage({});
    const byKey = Object.fromEntries(coverage.map((item) => [item.key, item]));
    expect(byKey.pulseAssessment.complete).toBe(false);
    expect(byKey.pulseAssessment.unresolvedHint).toBe("Document pulse rhythm, rate, strength, or sites");
    expect(byKey.perfusion.complete).toBe(false);
    expect(byKey.edema.complete).toBe(false);
    expect(byKey.chestPain.complete).toBe(false);
    expect(byKey.bpStatus.complete).toBe(false);
    expect(byKey.fatigue.complete).toBe(false);
    expect(byKey.dizziness.complete).toBe(false);
    expect(byKey.syncope.complete).toBe(false);
    expect(byKey.comparison.complete).toBe(false);
    expect(byKey.devices.complete).toBe(true);
    expect(byKey.devices.value).toBe("None documented");
    expect(byKey.devices.unresolvedHint).toBeNull();
  });

  it("never surfaces the retired cardiacDyspnea field as a coverage item", () => {
    const coverage = computeCardiovascularDocumentationCoverage({ cardiacDyspnea: true });
    expect(coverage.some((item) => item.key === "cardiacDyspnea" || /dyspnea/i.test(item.label))).toBe(false);
  });

  it("marks pulse assessment complete and summarizes documented dimensions", () => {
    const coverage = computeCardiovascularDocumentationCoverage({
      pulseRhythm: "Regular", pulseRate: "Normal", pulseStrength: "Strong", pulseSites: ["Radial", "Pedal"],
    });
    const item = coverage.find((i) => i.key === "pulseAssessment");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Regular; Normal; Strong; Sites: Radial, Pedal");
    expect(item.unresolvedHint).toBeNull();
  });

  it("treats booleanPill extras (cool extremities, varicose veins, stasis ulcer) as summary-only, not a completion gate", () => {
    const incomplete = computeCardiovascularDocumentationCoverage({ coolExtremities: true });
    expect(incomplete.find((i) => i.key === "perfusion").complete).toBe(false);

    const complete = computeCardiovascularDocumentationCoverage({ skinColor: "Pale", coolExtremities: true });
    const item = complete.find((i) => i.key === "perfusion");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Pale; Cool Extremities");
  });

  it("treats Edema Present = 'No' as complete documentation with no sub-fields required", () => {
    const coverage = computeCardiovascularDocumentationCoverage({ edema: { present: "No" } });
    const item = coverage.find((i) => i.key === "edema");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("No Edema");
  });

  it("summarizes Edema Present = 'Yes' with its sub-fields", () => {
    const coverage = computeCardiovascularDocumentationCoverage({
      edema: { present: "Yes", location: ["Bilateral lower extremities"], severity: "2+", pitting: "Pitting" },
    });
    const item = coverage.find((i) => i.key === "edema");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Present; Bilateral lower extremities; 2+; Pitting");
  });

  it("marks comparison complete only once Clinical Status Change is selected", () => {
    const coverage = computeCardiovascularDocumentationCoverage({ clinicalStatusChange: "No Significant Change" });
    const item = coverage.find((i) => i.key === "comparison");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("No Significant Change");
  });
});

