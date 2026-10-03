import { describe, it, expect } from "vitest";
import {
  computeNeurologicalNarrative,
  computeNeurologicalWorkflowStatus,
  neurologicalHasActionablePocFinding,
} from "./RNICA.jsx";

// Bounded Compatibility Increment (2026-09-28) regression coverage.
// Scope: Neurological Overview Gate status/summary/POC-gating behavior
// only. No new fields, schema, or migrations are exercised here.

describe("computeNeurologicalWorkflowStatus", () => {
  it("returns Not Started when nothing has been documented", () => {
    expect(computeNeurologicalWorkflowStatus({}).code).toBe("not_started");
  });

  it("returns In Progress when data exists but no Overview path is chosen", () => {
    const status = computeNeurologicalWorkflowStatus({ communication: "Impaired" });
    expect(status.code).toBe("in_progress");
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

  it("reports In Progress for a chosen path with nothing else documented yet", () => {
    const status = computeNeurologicalWorkflowStatus({ neuroOverview: "Existing Neurological Findings Stable" });
    expect(status.code).toBe("in_progress");
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
