import { describe, it, expect } from "vitest";
import {
  computeBodySystemSummary,
  computeInfectionRequiresFollowUp,
} from "./RNICA.jsx";

// OWNER DIRECTIVE (2026-10-05) "Infection Is Not A Patient-Interview
// Workflow" -- exercises exact-wording and REQUIRES FOLLOW-UP decoupling
// requirements (items 4 and 12) against synthetic data, independent of
// any shared/seeded patient fixture (the dev-environment test patient
// already carries legitimately-documented baseline allergies, so a true
// zero-allergy state cannot be reliably produced end-to-end).

describe("Infection Summary -- Initial Unselected State (item 4)", () => {
  it('reads the exact required wording when nothing is documented and no allergies exist', () => {
    const summary = computeBodySystemSummary("infection", {}, { allergyAlerts: [] });
    expect(summary.status).toBe("Infection assessment not yet documented.");
    expect(summary.requiresFollowUp).toBe(false);
  });

  it("falls through to Findings Present (not the not-yet-documented wording) when an allergy already exists, even before Overview is selected", () => {
    const summary = computeBodySystemSummary("infection", {}, {
      allergyAlerts: ["Medication allergy: Penicillin (Severe) — Hives."],
    });
    expect(summary.status).toBe("Findings Present");
    expect(summary.primaryIssues).toContain("Medication allergy: Penicillin (Severe) — Hives.");
  });
});

describe("Infection Summary -- REQUIRES FOLLOW-UP decoupling (item 12)", () => {
  it("does NOT require follow-up for a severe allergy alone", () => {
    expect(computeInfectionRequiresFollowUp({})).toBe(false);
    const summary = computeBodySystemSummary("infection", {}, {
      allergyAlerts: ["Medication allergy: Penicillin (Severe) — Hives."],
    });
    expect(summary.requiresFollowUp).toBe(false);
  });

  it("does NOT require follow-up for immunosuppression alone", () => {
    const data = { immunosuppressed: true, immunosuppressionReason: "Cancer treatment" };
    expect(computeInfectionRequiresFollowUp(data)).toBe(false);
    const summary = computeBodySystemSummary("infection", data, { allergyAlerts: [] });
    expect(summary.requiresFollowUp).toBe(false);
  });

  it("DOES require follow-up for a genuine active infection finding", () => {
    const data = { currentInfections: ["UTI"] };
    expect(computeInfectionRequiresFollowUp(data)).toBe(true);
    const summary = computeBodySystemSummary("infection", data, { allergyAlerts: [] });
    expect(summary.requiresFollowUp).toBe(true);
  });

  it("DOES require follow-up for a current resistant organism", () => {
    expect(computeInfectionRequiresFollowUp({ antibioticResistantInfection: ["MRSA"] })).toBe(true);
  });

  it("DOES require follow-up for active antibiotic therapy", () => {
    expect(computeInfectionRequiresFollowUp({ antibioticTherapyStatus: "Currently receiving antibiotics" })).toBe(true);
  });

  it("does NOT require follow-up when antibiotic therapy status is explicitly 'Not receiving antibiotics'", () => {
    expect(computeInfectionRequiresFollowUp({ antibioticTherapyStatus: "Not receiving antibiotics" })).toBe(false);
  });

  it("DOES require follow-up for non-standard precautions", () => {
    expect(computeInfectionRequiresFollowUp({ precautions: ["Contact"] })).toBe(true);
  });

  it("does NOT require follow-up for Standard precautions alone", () => {
    expect(computeInfectionRequiresFollowUp({ precautions: ["Standard"] })).toBe(false);
  });

  it("does NOT require follow-up for historical infection findings alone (Infection Follow-Up Governance Correction)", () => {
    // Recurrent UTI / prior sepsis / recurrent-infection notes are
    // disease-burden and prognosis-support indicators in hospice, not by
    // themselves an active clinical problem -- history alone must never
    // raise REQUIRES FOLLOW-UP.
    expect(computeInfectionRequiresFollowUp({ recurrentInfection: true })).toBe(false);
    expect(computeInfectionRequiresFollowUp({ infectionHistoryTypes: ["Prior sepsis"] })).toBe(false);
    expect(computeInfectionRequiresFollowUp({ infectionHistoryTypes: ["Recurrent UTI", "Prior sepsis"] })).toBe(false);
    expect(computeInfectionRequiresFollowUp({ infectionHistory: "Recurrent UTIs over past year" })).toBe(false);
  });

  it("does NOT require follow-up for history of a resistant organism alone", () => {
    expect(computeInfectionRequiresFollowUp({ historyOfResistantInfections: ["MRSA"] })).toBe(false);
  });

  it("DOES require follow-up when historical infection findings are combined with a current active signal", () => {
    const data = {
      infectionHistoryTypes: ["Recurrent UTI", "Prior sepsis"],
      currentInfections: ["UTI"],
    };
    expect(computeInfectionRequiresFollowUp(data)).toBe(true);
  });

  it("still returns No Current Infection Concern / no follow-up when history is documented but Overview is explicitly 'No Current Infection Concern' with no current signals", () => {
    const data = {
      infectionOverview: "No Current Infection Concern",
      infectionHistoryTypes: ["Recurrent UTI", "Prior sepsis"],
      historyOfResistantInfections: ["MRSA"],
    };
    const summary = computeBodySystemSummary("infection", data, { allergyAlerts: [] });
    expect(summary.requiresFollowUp).toBe(false);
  });

  it("combines a real infection finding with allergy/immunosuppression without losing the follow-up signal", () => {
    const data = { currentInfections: ["Sepsis"], immunosuppressed: true };
    const summary = computeBodySystemSummary("infection", data, {
      allergyAlerts: ["Medication allergy: Penicillin (Severe) — Hives."],
    });
    expect(summary.requiresFollowUp).toBe(true);
  });
});

describe("Infection Summary -- legacy 'Unable to Assess' backward compatibility (item 8)", () => {
  it("still renders a review-pending status with the stored reason for a legacy record", () => {
    const summary = computeBodySystemSummary("infection", {
      infectionOverview: "Unable to Assess",
      infectionUnableToAssessReason: "Patient unresponsive",
    }, { allergyAlerts: [] });
    expect(summary.status).toBe("Infection assessment unable to complete. Reason: Patient unresponsive.");
    expect(summary.requiresFollowUp).toBe(true);
  });
});
