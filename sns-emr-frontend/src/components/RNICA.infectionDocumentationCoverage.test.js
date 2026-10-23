import { describe, it, expect } from "vitest";
import { computeInfectionDocumentationCoverage, deriveFeverStatus } from "./RNICA.jsx";

// PRODUCT OWNER DIRECTIVE (2026-10-13) "Infection Shall Follow The
// Cardiovascular Redesign Model" Step 1 -- regression coverage for
// computeInfectionDocumentationCoverage, mirroring the test shape already
// used for its Cardiovascular/Neurological counterparts. This is a purely
// additive, read-only restatement of already-documented Infection
// fields -- "Infection Overview", the Summary banner, and every disease/
// treatment/profile card are untouched (Steps 2/3 of the directive --
// duplication analysis and gate evaluation -- are explicitly deferred).
describe("computeInfectionDocumentationCoverage", () => {
  it("reports every item unresolved on a blank record except the always-complete Allergies and Immune Status items", () => {
    const coverage = computeInfectionDocumentationCoverage({});
    const byKey = Object.fromEntries(coverage.map((item) => [item.key, item]));
    expect(byKey.activeInfection.complete).toBe(false);
    expect(byKey.activeInfection.unresolvedHint).toBe("Document current active infection (or select None)");
    expect(byKey.resistantOrganisms.complete).toBe(false);
    expect(byKey.infectionHistory.complete).toBe(false);
    expect(byKey.antibioticTherapy.complete).toBe(false);
    expect(byKey.precautions.complete).toBe(false);
    expect(byKey.temperature.complete).toBe(false);
    expect(byKey.clinicalStatusChange.complete).toBe(false);
    expect(byKey.allergies.complete).toBe(true);
    expect(byKey.allergies.value).toBe("No Known Allergies Documented");
    expect(byKey.allergies.unresolvedHint).toBeNull();
    expect(byKey.immuneStatus.complete).toBe(true);
    expect(byKey.immuneStatus.value).toBe("Not Immunosuppressed");
    expect(byKey.immuneStatus.unresolvedHint).toBeNull();
  });

  it("treats Active Infection = 'None' as complete documentation", () => {
    const coverage = computeInfectionDocumentationCoverage({ currentInfections: ["None"] });
    const item = coverage.find((i) => i.key === "activeInfection");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("No Active Infection");
  });

  it("summarizes a documented active infection including the Other free-text", () => {
    const coverage = computeInfectionDocumentationCoverage({
      currentInfections: ["UTI", "Other"], currentInfectionOther: "Bronchitis",
    });
    const item = coverage.find((i) => i.key === "activeInfection");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("UTI, Other (Bronchitis)");
  });

  it("summarizes current and historical resistant organisms independently", () => {
    const coverage = computeInfectionDocumentationCoverage({
      antibioticResistantInfection: ["None"], historyOfResistantInfections: ["MRSA"],
    });
    const item = coverage.find((i) => i.key === "resistantOrganisms");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("No Current Resistant Organism; Hx: MRSA");
  });

  it("treats recurrentInfection (booleanPill) as summary-only, not a completion gate", () => {
    const incomplete = computeInfectionDocumentationCoverage({ recurrentInfection: true });
    expect(incomplete.find((i) => i.key === "infectionHistory").complete).toBe(false);

    const complete = computeInfectionDocumentationCoverage({
      recurrentInfection: true, infectionHistoryTypes: ["Recurrent UTI"],
    });
    const item = complete.find((i) => i.key === "infectionHistory");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Recurrent Infection; Recurrent UTI");
  });

  it("marks precautions complete once Standard (or any option) is selected", () => {
    const coverage = computeInfectionDocumentationCoverage({ precautions: ["Standard"] });
    const item = coverage.find((i) => i.key === "precautions");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Standard");
  });

  it("surfaces allergy alerts from the shared patient_allergies extra, independent of section form data", () => {
    const coverage = computeInfectionDocumentationCoverage({}, { allergyAlerts: ["Medication allergy: Penicillin (severe)."] });
    const item = coverage.find((i) => i.key === "allergies");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Medication allergy: Penicillin (severe).");
  });

  it("marks immune status complete and summarizes the reason once immunosuppressed is documented", () => {
    const coverage = computeInfectionDocumentationCoverage({
      immunosuppressed: true, immunosuppressionReason: "Cancer treatment",
    });
    const item = coverage.find((i) => i.key === "immuneStatus");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Immunosuppressed (Cancer treatment)");
  });

  it("marks clinical status change complete only once selected", () => {
    const coverage = computeInfectionDocumentationCoverage({ clinicalStatusChange: "No Significant Change" });
    const item = coverage.find((i) => i.key === "clinicalStatusChange");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("No Significant Change");
  });

  // PRODUCT OWNER DIRECTIVE (2026-10-20) "SNS Clinical Ownership Model"
  // Phase 2 -- Temperature is sourced from Vitals via `extra`, never from
  // Infection's own section data, except as a read-only legacy fallback.
  it("sources temperature completeness and value from the Vitals extra, including derived fever status", () => {
    const coverage = computeInfectionDocumentationCoverage({}, { vitalsTemperature: 102.1, vitalsTemperatureUnit: "F" });
    const item = coverage.find((i) => i.key === "temperature");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("102.1°F (Moderate fever)");
  });

  it("falls back to a legacy Infection-section temperature only when no Vitals value exists", () => {
    const withLegacyOnly = computeInfectionDocumentationCoverage({ temperature: "99.1" }, {});
    const legacyItem = withLegacyOnly.find((i) => i.key === "temperature");
    expect(legacyItem.complete).toBe(true);
    expect(legacyItem.value).toBe("99.1°F (Afebrile)");

    const withBoth = computeInfectionDocumentationCoverage(
      { temperature: "99.1" },
      { vitalsTemperature: 103.5, vitalsTemperatureUnit: "F" },
    );
    expect(withBoth.find((i) => i.key === "temperature").value).toBe("103.5°F (High-grade fever)");
  });

  it("leaves temperature unresolved when neither Vitals nor a legacy value is documented", () => {
    const coverage = computeInfectionDocumentationCoverage({});
    const item = coverage.find((i) => i.key === "temperature");
    expect(item.complete).toBe(false);
    expect(item.unresolvedHint).toBe("Document temperature under Vitals & Measurements");
  });
});

describe("deriveFeverStatus", () => {
  it("classifies standard clinical fever bands in Fahrenheit", () => {
    expect(deriveFeverStatus(98.6, "F")).toBe("Afebrile");
    expect(deriveFeverStatus(100.4, "F")).toBe("Low-grade fever");
    expect(deriveFeverStatus(101.3, "F")).toBe("Low-grade fever");
    expect(deriveFeverStatus(102.5, "F")).toBe("Moderate fever");
    expect(deriveFeverStatus(104, "F")).toBe("High-grade fever");
  });

  it("normalizes Celsius values before classifying", () => {
    expect(deriveFeverStatus(37, "C")).toBe("Afebrile");
    expect(deriveFeverStatus(39.4, "C")).toBe("Moderate fever");
  });

  it("returns null for blank or non-numeric input", () => {
    expect(deriveFeverStatus("", "F")).toBeNull();
    expect(deriveFeverStatus(null, "F")).toBeNull();
    expect(deriveFeverStatus("abc", "F")).toBeNull();
  });
});
