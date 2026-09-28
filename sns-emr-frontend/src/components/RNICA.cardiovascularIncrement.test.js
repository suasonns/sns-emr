import { describe, it, expect } from "vitest";
import {
  computeCardiovascularNarrative,
  computeCardiovascularWorkflowStatus,
  cardiovascularHasActionablePocFinding,
  cardiovascularHasPreservedAbnormalFinding,
  resolvePulseDimensionDisplay,
  resolveBpStatusDisplay,
  resolveOrthostaticFindingDisplay,
  resolveBpLegacyDisplay,
  resolveCardiacDyspneaGate,
} from "./RNICA.jsx";

// Cardiovascular Overview Gate regression coverage (Final Owner Directive,
// 2026-09-28). Scope: status/summary/POC-gating/legacy-alias behavior
// only. No schema, migration, or persistence changes are exercised here.

describe("computeCardiovascularWorkflowStatus", () => {
  it("returns Not Started when nothing has been documented", () => {
    expect(computeCardiovascularWorkflowStatus({}).code).toBe("not_started");
  });

  it("returns In Progress when data exists but no Overview path is chosen", () => {
    expect(computeCardiovascularWorkflowStatus({ fatigue: "Mild" }).code).toBe("in_progress");
  });

  // CORRECTION (2026-09-28, audit): a completed Unable to Assess path is
  // not automatically unresolved -- Review Required applies only while a
  // genuine blocker exists (no reason, incomplete Other, or a preserved
  // conflict). These 8 cases mirror the corrected directive's required
  // Unable-to-Assess status matrix exactly.
  describe("Unable to Assess status resolution", () => {
    it("1. no reason selected -> Review Required", () => {
      const status = computeCardiovascularWorkflowStatus({ cardiovascularOverview: "Unable to Assess" });
      expect(status.code).toBe("review_required");
    });

    it("2. Other selected with no explanation -> Review Required", () => {
      const status = computeCardiovascularWorkflowStatus({
        cardiovascularOverview: "Unable to Assess",
        cardiovascularUnableToAssessReason: "Other",
        cardiovascularUnableToAssessOther: "",
      });
      expect(status.code).toBe("review_required");
    });

    it("4. approved non-Other reason, no conflict -> Ready for Review", () => {
      const status = computeCardiovascularWorkflowStatus({
        cardiovascularOverview: "Unable to Assess",
        cardiovascularUnableToAssessReason: "Patient unresponsive",
      });
      expect(status.code).toBe("ready_for_review");
      expect(status.variant).toBe("success");
    });

    it("5. Other reason with explanation, no conflict -> Ready for Review", () => {
      const status = computeCardiovascularWorkflowStatus({
        cardiovascularOverview: "Unable to Assess",
        cardiovascularUnableToAssessReason: "Other",
        cardiovascularUnableToAssessOther: "Patient declined visit today.",
      });
      expect(status.code).toBe("ready_for_review");
    });

    it("6a. preserved conflicting legacy BP values -> Review Required", () => {
      const status = computeCardiovascularWorkflowStatus({
        cardiovascularOverview: "Unable to Assess",
        cardiovascularUnableToAssessReason: "Patient unresponsive",
        bpSymptoms: ["Normal", "Hypertensive"],
      });
      expect(status.code).toBe("review_required");
    });

    it("6b. preserved legacy cardiac-dyspnea attribution with blank Respiratory -> Review Required", () => {
      const status = computeCardiovascularWorkflowStatus(
        {
          cardiovascularOverview: "Unable to Assess",
          cardiovascularUnableToAssessReason: "Patient unresponsive",
          cardiacDyspnea: true,
        },
        undefined,
      );
      expect(status.code).toBe("review_required");
    });

    it("8. Unable to Assess alone never suggests POC, regardless of status resolution", () => {
      expect(cardiovascularHasActionablePocFinding({ cardiovascularOverview: "Unable to Assess", chestPain: { present: "Yes" } })).toBe(false);
    });
  });

  it("reports Ready for Review once a non-Unable-to-Assess path has documented findings", () => {
    const status = computeCardiovascularWorkflowStatus({
      cardiovascularOverview: "Existing Cardiovascular Findings Review",
      pulseRhythm: "Regular",
    });
    expect(status.code).toBe("ready_for_review");
  });

  it("reports In Progress for a chosen path with nothing else documented yet", () => {
    expect(computeCardiovascularWorkflowStatus({ cardiovascularOverview: "Existing Cardiovascular Findings Review" }).code).toBe("in_progress");
  });

  // FIX (2026-09-28, live-UI audit): reproduces the exact defect observed
  // in the running app on a real record -- selecting "No Current
  // Cardiovascular Concern" while chest pain / edema / heart failure /
  // other abnormal findings remain stored must never reach Ready for
  // Review, and completing Path 1's own required fields (with no
  // conflict) must reach Ready for Review on its own, independent of any
  // unrelated documented value.
  describe("No Current Cardiovascular Concern (Path 1) status resolution", () => {
    it("stays In Progress until Rhythm, Rate, Strength, and Clinical Status Change are all deliberately completed", () => {
      const status = computeCardiovascularWorkflowStatus({
        cardiovascularOverview: "No Current Cardiovascular Concern",
        pulseRhythm: "Regular",
      });
      expect(status.code).toBe("in_progress");
    });

    it("reaches Ready for Review once every required Path 1 field is complete and no conflict exists", () => {
      const status = computeCardiovascularWorkflowStatus({
        cardiovascularOverview: "No Current Cardiovascular Concern",
        pulseRhythm: "Regular",
        pulseRate: "Normal",
        pulseStrength: "Strong",
        clinicalStatusChange: "Stable / No Change",
      });
      expect(status.code).toBe("ready_for_review");
    });

    it("reproduction: preserved chest pain + edema + heart failure blocks Ready for Review", () => {
      const status = computeCardiovascularWorkflowStatus({
        cardiovascularOverview: "No Current Cardiovascular Concern",
        chestPain: { present: "Yes" },
        edema: { present: "Yes" },
        heartFailurePresent: true,
      });
      expect(status.code).toBe("review_required");
    });

    it.each([
      ["chest pain", { chestPain: { present: "Yes" } }],
      ["edema", { edema: { present: "Yes" } }],
      ["heart failure", { heartFailurePresent: true }],
      ["syncope", { syncope: "Yes" }],
      ["cardiac dyspnea attribution", { cardiacDyspnea: true }],
      ["dizziness", { dizziness: "Mild" }],
      ["conflicting legacy BP", { bpSymptoms: ["Normal", "Hypertensive"] }],
      ["abnormal BP status", { bpStatus: "Hypertensive" }],
      ["irregular pulse rhythm", { pulseRhythm: "Irregular" }],
      ["abnormal pulse rate", { pulseRate: "Tachycardic" }],
      ["abnormal pulse strength", { pulseStrength: "Thready" }],
    ])("%s alone forces Review Required, even with Path 1 selected", (_label, findings) => {
      const status = computeCardiovascularWorkflowStatus({ cardiovascularOverview: "No Current Cardiovascular Concern", ...findings });
      expect(status.code).toBe("review_required");
    });

    it("never deletes or clears the preserved abnormal finding while flagging the conflict", () => {
      const d = { cardiovascularOverview: "No Current Cardiovascular Concern", chestPain: { present: "Yes" }, edema: { present: "Yes" } };
      computeCardiovascularWorkflowStatus(d);
      expect(d.chestPain.present).toBe("Yes");
      expect(d.edema.present).toBe("Yes");
    });
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

describe("resolveCardiacDyspneaGate - Respiratory/Cardiovascular ownership", () => {
  it("shows the attribution checkbox once Respiratory confirms dyspnea", () => {
    const gate = resolveCardiacDyspneaGate({}, { sobSeverity: "Moderate" });
    expect(gate.visible).toBe(true);
    expect(gate.reviewRequired).toBe(false);
  });

  it("hides the checkbox and shows guidance when Respiratory is incomplete (blank)", () => {
    const gate = resolveCardiacDyspneaGate({}, {});
    expect(gate.visible).toBe(false);
    expect(gate.guidance).toMatch(/Document dyspnea in Respiratory/);
  });

  it("hides the checkbox with no guidance when Respiratory explicitly documents no dyspnea", () => {
    const gate = resolveCardiacDyspneaGate({}, { sobSeverity: "None" });
    expect(gate.visible).toBe(false);
    expect(gate.guidance).toBe("");
  });

  it("preserves and flags a legacy cardiacDyspnea value when Respiratory is blank", () => {
    const gate = resolveCardiacDyspneaGate({ cardiacDyspnea: true }, {});
    expect(gate.visible).toBe(true);
    expect(gate.reviewRequired).toBe(true);
  });

  it("preserves and flags a legacy cardiacDyspnea value when Respiratory is negative", () => {
    const gate = resolveCardiacDyspneaGate({ cardiacDyspnea: true }, { sobSeverity: "None" });
    expect(gate.visible).toBe(true);
    expect(gate.reviewRequired).toBe(true);
  });
});

describe("cardiovascularHasActionablePocFinding", () => {
  it("is false for an empty record", () => {
    expect(cardiovascularHasActionablePocFinding({})).toBe(false);
  });

  it("is false for No Current Cardiovascular Concern with no other findings", () => {
    expect(cardiovascularHasActionablePocFinding({ cardiovascularOverview: "No Current Cardiovascular Concern" })).toBe(false);
  });

  it("is false for Unable to Assess alone (per directive: not a POC trigger)", () => {
    expect(cardiovascularHasActionablePocFinding({
      cardiovascularOverview: "Unable to Assess",
      cardiovascularUnableToAssessReason: "Patient declined",
    })).toBe(false);
  });

  it("is false for stable chronic Heart Failure alone (Contradiction 7 correction)", () => {
    expect(cardiovascularHasActionablePocFinding({
      cardiovascularOverview: "Existing Cardiovascular Findings Review",
      heartFailurePresent: true,
      clinicalStatusChange: "Stable / No Change",
    })).toBe(false);
  });

  it("is false for stable chronic edema alone", () => {
    expect(cardiovascularHasActionablePocFinding({
      cardiovascularOverview: "Existing Cardiovascular Findings Review",
      edema: { present: "Yes", severity: "1+" },
    })).toBe(false);
  });

  it("is true for any documented Chest Pain Present", () => {
    expect(cardiovascularHasActionablePocFinding({ chestPain: { present: "Yes" } })).toBe(true);
  });

  it("is true for Syncope Present", () => {
    expect(cardiovascularHasActionablePocFinding({ syncope: "Yes" })).toBe(true);
  });

  it("is true whenever the New/Worsening path is selected", () => {
    expect(cardiovascularHasActionablePocFinding({ cardiovascularOverview: "New/Worsening Cardiovascular Findings" })).toBe(true);
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

describe("computeCardiovascularNarrative - Not Started / blank", () => {
  it("returns '' (falsy) for a completely blank record, letting the generic fallback apply", () => {
    expect(computeCardiovascularNarrative({})).toBe("");
  });
});

describe("computeCardiovascularNarrative - No Current Concern", () => {
  it("does not claim 'No current cardiovascular concern identified.' until all required normal-path fields are complete", () => {
    expect(computeCardiovascularNarrative({ cardiovascularOverview: "No Current Cardiovascular Concern" })).toBe("");
    expect(computeCardiovascularNarrative({
      cardiovascularOverview: "No Current Cardiovascular Concern",
      pulseRhythm: "Regular",
      pulseRate: "Normal",
    })).toBe("");
  });

  it("renders the exact approved sentence once Rhythm/Rate/Strength/Clinical Status Change are all documented", () => {
    const narrative = computeCardiovascularNarrative({
      cardiovascularOverview: "No Current Cardiovascular Concern",
      pulseRhythm: "Regular",
      pulseRate: "Normal",
      pulseStrength: "Strong",
      clinicalStatusChange: "Stable / No Change",
    });
    expect(narrative).toBe("No current cardiovascular concern identified.");
  });
});

describe("computeCardiovascularNarrative - Existing Findings Review", () => {
  it("does not claim stability without an explicit current Clinical Status Change selection", () => {
    const narrative = computeCardiovascularNarrative({ cardiovascularOverview: "Existing Cardiovascular Findings Review" });
    expect(narrative).toBe("Cardiovascular findings documented.");
    expect(narrative).not.toMatch(/stable/i);
  });

  it("claims stability only once Clinical Status Change = Stable / No Change is explicitly selected", () => {
    const narrative = computeCardiovascularNarrative({
      cardiovascularOverview: "Existing Cardiovascular Findings Review",
      clinicalStatusChange: "Stable / No Change",
    });
    expect(narrative).toBe("Cardiovascular findings documented as stable/no significant change.");
  });
});

describe("computeCardiovascularNarrative - Unable to Assess wording", () => {
  it("renders exactly the approved sentence with no unrelated clinical clauses", () => {
    const narrative = computeCardiovascularNarrative({
      cardiovascularOverview: "Unable to Assess",
      cardiovascularUnableToAssessReason: "Patient unable to participate",
      chestPain: { present: "Yes" },
      heartFailurePresent: true,
    });
    expect(narrative).toBe("Cardiovascular assessment unable to complete. Reason: Patient unable to participate.");
    expect(narrative).not.toMatch(/Chest pain/);
    expect(narrative).not.toMatch(/Heart failure/);
  });
});

describe("computeCardiovascularNarrative - New/Worsening findings", () => {
  it("generates one concise clause per confirmed finding only", () => {
    const narrative = computeCardiovascularNarrative({
      cardiovascularOverview: "New/Worsening Cardiovascular Findings",
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
    expect(narrative).toContain("Heart failure documented.");
    expect(narrative).toContain("Dyspnea attributed to cardiac condition.");
  });

  it("omits pulse/BP clauses entirely when every dimension is normal", () => {
    const narrative = computeCardiovascularNarrative({
      cardiovascularOverview: "New/Worsening Cardiovascular Findings",
      pulseRhythm: "Regular",
      pulseRate: "Normal",
      pulseStrength: "Strong",
      bpStatus: "Normal",
    });
    expect(narrative).not.toMatch(/Pulse/);
    expect(narrative).not.toMatch(/BP status/);
  });

  it("surfaces a contradictory legacy BP array as a review-required note", () => {
    const narrative = computeCardiovascularNarrative({
      cardiovascularOverview: "New/Worsening Cardiovascular Findings",
      bpSymptoms: ["Normal", "Hypertensive"],
    });
    expect(narrative).toMatch(/Legacy BP values on record \(Normal, Hypertensive\) -- review required\./);
  });
});

// Control-Model Correction directive (2026-09-28) Section 4/11 --
// Cardiovascular's own Clinical Status Change list must not affect the
// shared CLINICAL_STATUS_CHANGE_OPTIONS used by other body systems, and
// a Path 3 record that simultaneously claims stability is an internal
// contradiction that must surface for review.
describe("Clinical Status Change -- Cardiovascular-specific list and legacy compatibility", () => {
  it("treats both the legacy and new stability strings as equivalent for the Path 2 narrative", () => {
    const legacy = computeCardiovascularNarrative({
      cardiovascularOverview: "Existing Cardiovascular Findings Review",
      clinicalStatusChange: "Stable / No Change",
    });
    const current = computeCardiovascularNarrative({
      cardiovascularOverview: "Existing Cardiovascular Findings Review",
      clinicalStatusChange: "No Significant Change",
    });
    expect(legacy).toBe(current);
    expect(legacy).toMatch(/stable\/no significant change/);
  });

  it("treats both the legacy and new decline/worsening strings as POC-actionable", () => {
    expect(cardiovascularHasActionablePocFinding({ clinicalStatusChange: "New Symptom Since Prior Assessment" })).toBe(true);
    expect(cardiovascularHasActionablePocFinding({ clinicalStatusChange: "New or Worsening Finding" })).toBe(true);
  });

  it("forces Review Required when Path 3 (New/Worsening) is paired with a stability claim", () => {
    const legacy = computeCardiovascularWorkflowStatus({
      cardiovascularOverview: "New/Worsening Cardiovascular Findings",
      clinicalStatusChange: "Stable / No Change",
    });
    const current = computeCardiovascularWorkflowStatus({
      cardiovascularOverview: "New/Worsening Cardiovascular Findings",
      clinicalStatusChange: "No Significant Change",
    });
    expect(legacy.code).toBe("review_required");
    expect(current.code).toBe("review_required");
  });

  it("does not force Review Required for Path 3 with a genuine decline claim", () => {
    const status = computeCardiovascularWorkflowStatus({
      cardiovascularOverview: "New/Worsening Cardiovascular Findings",
      clinicalStatusChange: "Declining",
      chestPain: { present: "Yes" },
    });
    expect(status.code).toBe("ready_for_review");
  });

  it("never rewrites a legacy Clinical Status Change value while computing status/narrative", () => {
    const d = { cardiovascularOverview: "Existing Cardiovascular Findings Review", clinicalStatusChange: "Symptom Well-Managed" };
    computeCardiovascularWorkflowStatus(d);
    computeCardiovascularNarrative(d);
    expect(d.clinicalStatusChange).toBe("Symptom Well-Managed");
  });
});
