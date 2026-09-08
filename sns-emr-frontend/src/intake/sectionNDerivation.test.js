import { describe, it, expect } from "vitest";
import { deriveSectionNFromMedications } from "./sectionNDerivation";

function med(overrides) {
  return {
    medication_id: "m1",
    medication_name: "Test Drug",
    dosage: "10 MG",
    route: "PO",
    frequency: "Daily",
    start_date: "2026-01-01",
    end_date: null,
    status: "active",
    drug_classes: [],
    ...overrides,
  };
}

describe("deriveSectionNFromMedications", () => {
  it("returns all-negative when there are no medications", () => {
    const result = deriveSectionNFromMedications([]);
    expect(result).toEqual({
      scheduledOpioid: false,
      prnOpioid: false,
      bowelRegimen: false,
      opioidPresent: false,
      derivedFrom: { scheduledOpioid: [], prnOpioid: [], bowelRegimen: [] },
    });
  });

  it("returns all-negative for a non-opioid, non-laxative medication list (Loren Shields case)", () => {
    const meds = [
      med({ medication_name: "Lisinopril", frequency: "Daily", drug_classes: ["ACE_INHIBITORS"] }),
      med({ medication_name: "Metformin", frequency: "BID", drug_classes: ["ANTIDIABETICS"] }),
    ];
    const result = deriveSectionNFromMedications(meds);
    expect(result.scheduledOpioid).toBe(false);
    expect(result.prnOpioid).toBe(false);
    expect(result.bowelRegimen).toBe(false);
    expect(result.opioidPresent).toBe(false);
  });

  it("detects a scheduled (non-PRN) opioid as N0500", () => {
    const meds = [med({ medication_name: "Morphine", frequency: "Q4H", drug_classes: ["OPIOIDS"] })];
    const result = deriveSectionNFromMedications(meds);
    expect(result.scheduledOpioid).toBe(true);
    expect(result.prnOpioid).toBe(false);
    expect(result.opioidPresent).toBe(true);
    expect(result.derivedFrom.scheduledOpioid).toEqual(["Morphine 10 MG PO Q4H"]);
  });

  it("detects a PRN opioid as N0510, distinct from scheduled", () => {
    const meds = [med({ medication_name: "Oxycodone", frequency: "Q4H PRN breakthrough pain", drug_classes: ["OPIOIDS"] })];
    const result = deriveSectionNFromMedications(meds);
    expect(result.scheduledOpioid).toBe(false);
    expect(result.prnOpioid).toBe(true);
    expect(result.opioidPresent).toBe(true);
  });

  it("detects both scheduled and PRN opioids simultaneously", () => {
    const meds = [
      med({ medication_name: "Morphine ER", frequency: "Q12H", drug_classes: ["OPIOIDS"] }),
      med({ medication_name: "Morphine IR", frequency: "Q2H PRN", drug_classes: ["OPIOIDS"] }),
    ];
    const result = deriveSectionNFromMedications(meds);
    expect(result.scheduledOpioid).toBe(true);
    expect(result.prnOpioid).toBe(true);
    expect(result.opioidPresent).toBe(true);
  });

  it("detects an active laxative as bowel regimen present (N0520 support)", () => {
    const meds = [med({ medication_name: "Senna", frequency: "BID", drug_classes: ["LAXATIVES"] })];
    const result = deriveSectionNFromMedications(meds);
    expect(result.bowelRegimen).toBe(true);
    expect(result.derivedFrom.bowelRegimen).toEqual(["Senna 10 MG PO BID"]);
  });

  it("ignores discontinued medications entirely", () => {
    const meds = [
      med({ medication_name: "Morphine", frequency: "Q4H", drug_classes: ["OPIOIDS"], status: "discontinued", end_date: "2026-01-01" }),
      med({ medication_name: "Senna", frequency: "BID", drug_classes: ["LAXATIVES"], status: "discontinued", end_date: "2026-01-01" }),
    ];
    const result = deriveSectionNFromMedications(meds);
    expect(result.scheduledOpioid).toBe(false);
    expect(result.prnOpioid).toBe(false);
    expect(result.bowelRegimen).toBe(false);
    expect(result.opioidPresent).toBe(false);
  });

  it("treats a record with an end_date but no status field as inactive", () => {
    const meds = [med({ medication_name: "Morphine", drug_classes: ["OPIOIDS"], status: undefined, end_date: "2026-01-01" })];
    const result = deriveSectionNFromMedications(meds);
    expect(result.opioidPresent).toBe(false);
  });

  it("does not treat a non-opioid classified medication with 'prn' in frequency as an opioid", () => {
    const meds = [med({ medication_name: "Diphenhydramine", frequency: "Q6H PRN itching", drug_classes: ["ANTIHISTAMINES"] })];
    const result = deriveSectionNFromMedications(meds);
    expect(result.scheduledOpioid).toBe(false);
    expect(result.prnOpioid).toBe(false);
    expect(result.opioidPresent).toBe(false);
  });

  it("handles null/undefined input gracefully", () => {
    expect(deriveSectionNFromMedications(null)).toEqual({
      scheduledOpioid: false,
      prnOpioid: false,
      bowelRegimen: false,
      opioidPresent: false,
      derivedFrom: { scheduledOpioid: [], prnOpioid: [], bowelRegimen: [] },
    });
    expect(deriveSectionNFromMedications(undefined).opioidPresent).toBe(false);
  });
});
