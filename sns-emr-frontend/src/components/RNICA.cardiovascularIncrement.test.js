import { describe, it, expect } from "vitest";
import {
  computeCardiovascularNarrative,
  computeCardiovascularWorkflowStatus,
  cardiovascularHasActionablePocFinding,
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

  it("never reports Reviewed/Ready for Unable to Assess, even with a complete reason", () => {
    const status = computeCardiovascularWorkflowStatus({
      cardiovascularOverview: "Unable to Assess",
      cardiovascularUnableToAssessReason: "Patient unresponsive",
    });
    expect(status.code).toBe("review_required");
    expect(status.variant).toBe("warning");
  });

  it("reports Ready for Review once a non-Unable-to-Assess path has documented findings", () => {
    const status = computeCardiovascularWorkflowStatus({
      cardiovascularOverview: "No Current Cardiovascular Concern",
      pulseRhythm: "Regular",
    });
    expect(status.code).toBe("ready_for_review");
  });

  it("reports In Progress for a chosen path with nothing else documented yet", () => {
    expect(computeCardiovascularWorkflowStatus({ cardiovascularOverview: "Existing Cardiovascular Findings Review" }).code).toBe("in_progress");
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
    expect(narrative).toContain("Heart failure signs present.");
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
