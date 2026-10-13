import { describe, it, expect } from "vitest";
import {
  computeNeurologicalNarrative,
  computeNeurologicalWorkflowStatus,
  neurologicalHasActionablePocFinding,
  deriveNeurologicalOverview,
  computeNeurologicalSystemStatus,
  computeNeurologicalDocumentationCoverage,
} from "./RNICA.jsx";

// Bounded Compatibility Increment (2026-09-28) regression coverage.
// Scope: Neurological Overview Gate status/summary/POC-gating behavior
// only. No new fields, schema, or migrations are exercised here.

describe("computeNeurologicalWorkflowStatus", () => {
  it("returns Not Started when nothing has been documented", () => {
    expect(computeNeurologicalWorkflowStatus({}).code).toBe("not_started");
  });

  // PRODUCT OWNER DIRECTIVE (2026-10-12) "Neurological Overview -- System
  // Derived, Read Only" -- Overview is no longer a separate nurse
  // decision the status can be "in progress" waiting on; `in_progress`
  // was removed entirely. Once any finding is documented, the record is
  // Ready for Review -- there is nothing left to answer.
  it("reports Ready for Review once any finding is documented (no separate Overview step to wait on)", () => {
    const status = computeNeurologicalWorkflowStatus({ communication: "Impaired" });
    expect(status.code).toBe("ready_for_review");
  });

  it("never reports Reviewed/Ready for Unable to Assess, even with a complete reason", () => {
    const status = computeNeurologicalWorkflowStatus({
      neuroOverview: "Unable to Assess",
      neuroUnableToAssessReason: "Patient unresponsive",
    });
    expect(status.code).toBe("review_required");
    expect(status.variant).toBe("warning");
  });

  it("reports Ready for Review once a non-Unable-to-Assess path has documented findings", () => {
    const status = computeNeurologicalWorkflowStatus({
      neuroOverview: "No Current Neurological Concern",
      orientation: { time: true, place: true, person: true, situation: true },
    });
    expect(status.code).toBe("ready_for_review");
    expect(status.variant).toBe("success");
  });

  // `neuroOverview` now only ever legitimately holds "Unable to Assess"
  // going forward; a stale legacy string from a historical record is
  // still just "documented data" like any other field (harmless --
  // deriveNeurologicalOverview only ever pass-throughs the literal
  // "Unable to Assess" string, never any other stored value).
  it("reports Ready for Review for a stale legacy Overview value with nothing else documented", () => {
    const status = computeNeurologicalWorkflowStatus({ neuroOverview: "Existing Neurological Findings Stable" });
    expect(status.code).toBe("ready_for_review");
  });
});

// PRODUCT OWNER DIRECTIVE (2026-10-12) "Neurological Overview -- System
// Derived, Read Only" -- the nurse documents findings; SNS documents the
// summary. "Unable to Assess" remains the one real, explicit, stored
// clinician action (pass-through); every other value is computed fresh
// from already-documented findings, never a separate nurse choice.
describe("deriveNeurologicalOverview", () => {
  it("passes through the explicit Unable to Assess flag regardless of any other data", () => {
    expect(deriveNeurologicalOverview({ neuroOverview: "Unable to Assess", communication: "Impaired" })).toBe("Unable to Assess");
  });

  it("defaults to No Current Neurological Concern when nothing is documented", () => {
    expect(deriveNeurologicalOverview({})).toBe("No Current Neurological Concern");
  });

  it("derives New/Worsening Neurological Findings from an actionable POC finding", () => {
    const d = { motorStatus: "Present", motorDeficit: true };
    expect(neurologicalHasActionablePocFinding(d)).toBe(true);
    expect(deriveNeurologicalOverview(d)).toBe("New/Worsening Neurological Findings");
  });

  it("derives Existing Neurological Findings Stable from a documented clinical status change with no actionable finding", () => {
    expect(deriveNeurologicalOverview({ clinicalStatusChange: "No Change" })).toBe("Existing Neurological Findings Stable");
  });

  it("does not treat Initial Assessment as a prior-comparison change", () => {
    expect(deriveNeurologicalOverview({ clinicalStatusChange: "Initial Assessment" })).toBe("No Current Neurological Concern");
  });

  it("ignores a stale legacy neuroOverview string (only the literal Unable to Assess value is ever read back)", () => {
    expect(deriveNeurologicalOverview({ neuroOverview: "Existing Neurological Findings Stable" })).toBe("No Current Neurological Concern");
  });
});

describe("neurologicalHasActionablePocFinding", () => {
  it("is false for an empty record", () => {
    expect(neurologicalHasActionablePocFinding({})).toBe(false);
  });

  it("is false for No Current Neurological Concern with no other findings", () => {
    expect(neurologicalHasActionablePocFinding({ neuroOverview: "No Current Neurological Concern" })).toBe(false);
  });

  it("is false for Unable to Assess alone (per directive: not a POC trigger)", () => {
    expect(neurologicalHasActionablePocFinding({
      neuroOverview: "Unable to Assess",
      neuroUnableToAssessReason: "Patient declined",
    })).toBe(false);
  });

  it("is true for new/increased somnolence since prior", () => {
    expect(neurologicalHasActionablePocFinding({ sleepRest: { changeSincePrior: "Increased Somnolence" } })).toBe(true);
  });

  it("is true for a documented motor deficit", () => {
    expect(neurologicalHasActionablePocFinding({ motorStatus: "Present" })).toBe(true);
  });

  it("is true for a non-normal communication finding", () => {
    expect(neurologicalHasActionablePocFinding({ communication: "Impaired" })).toBe(true);
  });

  it("is true for a gradual decline or new/worsening clinical status change", () => {
    expect(neurologicalHasActionablePocFinding({ clinicalStatusChange: "New or Worsening Concern" })).toBe(true);
  });
});

describe("computeNeurologicalNarrative - Unable to Assess wording", () => {
  it("renders exactly the two approved sentences with no unrelated clinical clauses", () => {
    const narrative = computeNeurologicalNarrative({
      neuroOverview: "Unable to Assess",
      neuroUnableToAssessReason: "Patient unable to participate",
      communication: "Impaired",
      motorStatus: "Present",
    });
    expect(narrative).toBe("Neurological assessment unable to complete. Reason: Patient unable to participate.");
    expect(narrative).not.toMatch(/Communication/);
    expect(narrative).not.toMatch(/Motor/);
  });
});

describe("computeNeurologicalNarrative - Somnolence display grammar", () => {
  it("narrates 'Somnolence documented.' rather than the stored adjective value", () => {
    const narrative = computeNeurologicalNarrative({ sleepRest: { responsiveness: "Somnolent" } });
    expect(narrative).toContain("Somnolence documented.");
    expect(narrative).not.toContain("Somnolent.");
  });
});

describe("computeNeurologicalNarrative - Sleep Pattern display adapter", () => {
  it("narrates 'Usual sleep pattern.' for the stored 'Normal' value", () => {
    const narrative = computeNeurologicalNarrative({ sleepRest: { sleepPattern: "Normal" } });
    expect(narrative).toContain("Usual sleep pattern.");
  });
});

// SNS PRODUCT-OWNER CORRECTION (2026-10-12) "Preserve Discipline Clinical
// Stories / Documentation Coverage Standard" regression coverage --
// Documentation Coverage ("what is missing?") is a separate concept from
// the Clinical Story narrative above ("what did this discipline
// document?"); each item here reads a field already documented for its
// own clinical reason -- no new question/field/schema.
describe("computeNeurologicalDocumentationCoverage", () => {
  it("reports every domain missing when nothing has been documented", () => {
    const coverage = computeNeurologicalDocumentationCoverage({});
    expect(coverage).toHaveLength(7);
    expect(coverage.every((item) => item.complete === false)).toBe(true);
    expect(coverage.map((item) => item.label)).toEqual([
      "Consciousness",
      "Orientation",
      "Communication",
      "Behavioral Findings",
      "Sleep",
      "Comparison",
      "Psychiatric History",
    ]);
  });

  it("reports every domain complete for a fully documented record", () => {
    const coverage = computeNeurologicalDocumentationCoverage({
      consciousness: "Awake",
      orientation: { time: true, place: true, person: true, situation: true },
      communication: "Normal",
      symptomsDemeanor: ["Anxiety", "Agitation"],
      sleepRest: { sleepPattern: "Insomnia" },
      clinicalStatusChange: "New or Worsening Concern",
      psychiatricHistoryType: ["None"],
    });
    expect(coverage.every((item) => item.complete === true)).toBe(true);
  });

  it("does not treat 'Initial Assessment' comparison as missing -- it is itself a documented answer", () => {
    const coverage = computeNeurologicalDocumentationCoverage({ clinicalStatusChange: "Initial Assessment" });
    const comparison = coverage.find((item) => item.key === "comparison");
    expect(comparison.complete).toBe(true);
  });

  it("reports Comparison missing only when clinicalStatusChange is entirely blank", () => {
    const coverage = computeNeurologicalDocumentationCoverage({ consciousness: "Awake" });
    const comparison = coverage.find((item) => item.key === "comparison");
    expect(comparison.complete).toBe(false);
  });

  it("treats an explicit 'None' Psychiatric History selection as documented, not missing", () => {
    const coverage = computeNeurologicalDocumentationCoverage({ psychiatricHistoryType: ["None"] });
    const psych = coverage.find((item) => item.key === "psychiatricHistory");
    expect(psych.complete).toBe(true);
  });

  it("reports Unable to Assess as a documented state with its reason, not an empty coverage list", () => {
    const coverage = computeNeurologicalDocumentationCoverage({
      neuroOverview: "Unable to Assess",
      neuroUnableToAssessReason: "Patient declined",
    });
    expect(coverage).toHaveLength(1);
    expect(coverage[0].complete).toBe(true);
    expect(coverage[0].value).toBe("Unable to Assess — Patient declined");
  });
});

// SNS PRODUCT-OWNER CORRECTION (2026-10-12) Section 18 required tests --
// scenarios A-F for the Clinical Story (computeNeurologicalNarrative is
// the current, preserved generator; these are additional named scenarios
// beyond the pre-existing Unable-to-Assess/Somnolence/Sleep-Pattern tests
// above).
describe("computeNeurologicalNarrative - required scenario coverage", () => {
  it("A. normal findings -- states only documented normal findings, invents nothing", () => {
    const narrative = computeNeurologicalNarrative({
      consciousness: "Awake",
      orientation: { time: true, place: true, person: true, situation: true },
      communication: "Normal",
    });
    expect(narrative).toBe("Awake. Oriented x4. No current communication concern identified.");
  });

  it("B. behavioral symptoms (Anxiety, Agitation, depressed demeanor) all appear", () => {
    const narrative = computeNeurologicalNarrative({ symptomsDemeanor: ["Anxiety", "Agitation", "Depressed"] });
    expect(narrative).toContain("Behavioral: Anxiety, Agitation, Depressed.");
  });

  it("C. sleep concern (insomnia) appears without duplication", () => {
    const narrative = computeNeurologicalNarrative({ sleepRest: { sleepPattern: "Insomnia" } });
    const occurrences = narrative.split("Insomnia").length - 1;
    expect(occurrences).toBe(1);
  });

  it("D. sensory concern (Numbness) appears when documented", () => {
    const narrative = computeNeurologicalNarrative({ sensoryDeficits: ["Numbness"] });
    expect(narrative).toContain("Sensory deficits: Numbness.");
  });

  it("E. Unable to Assess states the documented inability/reason only, no normal findings invented", () => {
    const narrative = computeNeurologicalNarrative({
      neuroOverview: "Unable to Assess",
      neuroUnableToAssessReason: "Patient declined",
    });
    expect(narrative).toBe("Neurological assessment unable to complete. Reason: Patient declined.");
  });

  it("F. missing comparison -- narrative does not assert improvement, stability, or decline", () => {
    const narrative = computeNeurologicalNarrative({ consciousness: "Awake" });
    expect(narrative).not.toMatch(/stable|improved|declin/i);
    const coverage = computeNeurologicalDocumentationCoverage({ consciousness: "Awake" });
    expect(coverage.find((item) => item.key === "comparison").complete).toBe(false);
  });

  it("G. save/reload determinism -- identical input always produces identical story", () => {
    const input = { consciousness: "Awake", symptomsDemeanor: ["Anxiety"], sleepRest: { sleepPattern: "Insomnia" } };
    expect(computeNeurologicalNarrative(input)).toBe(computeNeurologicalNarrative({ ...input }));
  });
});

// SNS PRODUCT-OWNER CORRECTION (2026-10-12) "Documentation Coverage As A
// Source-Linked Discipline Findings Inventory" -- Neurological Phase 1
// acceptance tests A-J. Each test name below matches the lettered
// scenario from that directive so the "Test results" item of the
// required GitHub response can cite it directly.
describe("Neurological Phase 1 acceptance scenarios", () => {
  it("A. explicit normal answer -- Coverage shows documented and displays the answer", () => {
    const coverage = computeNeurologicalDocumentationCoverage({ communication: "Normal" });
    const communication = coverage.find((item) => item.key === "communication");
    expect(communication.complete).toBe(true);
    expect(communication.value).toBe("No Current Concern");
  });

  it("B. abnormal findings -- Coverage displays all documented values, HOPE mapping untouched", () => {
    const coverage = computeNeurologicalDocumentationCoverage({ symptomsDemeanor: ["Anxiety", "Agitation", "Depressed"] });
    const behavioral = coverage.find((item) => item.key === "behavioral");
    expect(behavioral.complete).toBe(true);
    expect(behavioral.value).toBe("Anxiety, Agitation, Depressed");
    // HOPE sourcing is untouched by Coverage -- Coverage only reads the
    // same raw `symptomsDemeanor` field HOPE's own approved mapping
    // already reads elsewhere; this test does not exercise the HOPE
    // mapper itself (out of scope here), only that Coverage does not
    // fabricate a different value from the one HOPE would also see.
  });

  it("C. unanswered field -- Coverage shows the exact unresolved requirement, no normal value fabricated", () => {
    const coverage = computeNeurologicalDocumentationCoverage({});
    const comparison = coverage.find((item) => item.key === "comparison");
    expect(comparison.complete).toBe(false);
    expect(comparison.value).toBeNull();
    expect(comparison.unresolvedHint).toBe("Select comparison to prior assessment");
  });

  it("D. Unable to Assess -- Coverage displays Unable to Assess and the documented reason, no normal findings generated", () => {
    const coverage = computeNeurologicalDocumentationCoverage({
      neuroOverview: "Unable to Assess",
      neuroUnableToAssessReason: "Patient unresponsive",
      communication: "Impaired",
    });
    expect(coverage).toHaveLength(1);
    expect(coverage[0].value).toBe("Unable to Assess — Patient unresponsive");
  });

  it("E. comparison -- Coverage shows the nurse-documented value; internal system status does not overwrite it", () => {
    const d = { clinicalStatusChange: "New or Worsening Concern" };
    const coverage = computeNeurologicalDocumentationCoverage(d);
    expect(coverage.find((item) => item.key === "comparison").value).toBe("New or Worsening Concern");
    // The internal system status is a derived read, never a write -- it
    // must not alter the stored field it just read.
    computeNeurologicalSystemStatus(d);
    expect(d.clinicalStatusChange).toBe("New or Worsening Concern");
  });

  it("F. derived status conflict -- Coverage keeps the nurse's comparison separate from actionable findings; neither is rewritten", () => {
    const d = { clinicalStatusChange: "No Change", motorStatus: "Present", motorDeficit: true };
    const coverage = computeNeurologicalDocumentationCoverage(d);
    expect(coverage.find((item) => item.key === "comparison").value).toBe("No Change");
    expect(neurologicalHasActionablePocFinding(d)).toBe(true);
    // The internal system status may use the actionable finding for its
    // own behavior (e.g. visibility/auto-collapse), but it is a distinct
    // read -- Coverage's comparison value above is untouched by it.
    expect(computeNeurologicalSystemStatus(d)).toBe("New/Worsening Neurological Findings");
    expect(d.clinicalStatusChange).toBe("No Change");
  });

  it("G. save and reload -- Coverage shows identical source values after an equivalent reload of the same record", () => {
    const stored = { consciousness: "Awake", sleepRest: { sleepPattern: "Insomnia" } };
    const reloaded = JSON.parse(JSON.stringify(stored));
    expect(computeNeurologicalDocumentationCoverage(stored)).toEqual(computeNeurologicalDocumentationCoverage(reloaded));
  });

  it("H. historical record -- a pre-existing stored value remains readable through Coverage with no silent regeneration", () => {
    const historical = { consciousness: "Alert" }; // legacy stored alias for "Awake"
    const coverage = computeNeurologicalDocumentationCoverage(historical);
    expect(coverage.find((item) => item.key === "consciousness").value).toBe("Awake");
  });

  it("I. retired feature check -- SNS Cognitive Screen score is not read by Coverage or the internal system status", () => {
    const d = { cognitiveScreen: { repetition: "3", recall: "3" } };
    const coverage = computeNeurologicalDocumentationCoverage(d);
    expect(coverage.some((item) => /cognitive/i.test(item.label))).toBe(false);
    expect(computeNeurologicalSystemStatus(d)).toBe("No Current Neurological Concern");
  });

  it("J. no AI -- Coverage and system-status computation are synchronous pure functions with no network/model call", () => {
    const result = computeNeurologicalDocumentationCoverage({ consciousness: "Awake" });
    expect(result).not.toBeInstanceOf(Promise);
    expect(computeNeurologicalSystemStatus({})).not.toBeInstanceOf(Promise);
  });
});

describe("computeNeurologicalSystemStatus", () => {
  it("is the same computation as deriveNeurologicalOverview (isolated, not duplicated)", () => {
    expect(computeNeurologicalSystemStatus).toBe(deriveNeurologicalOverview);
  });
});

