/**
 * Proof points for `respiratoryPersistenceMapping.ts`: every field the
 * Respiratory panel can produce has exactly one named classification, no
 * field is silently unresolved, and the two known backend-destination-
 * missing sub-fields are explicitly named (not swept into a vague
 * "unresolved" bucket).
 */
import { describe, expect, it } from "vitest";
import {
  findRespiratoryMappingEntry,
  RESPIRATORY_PERSISTENCE_MAPPING,
  type RespiratoryFieldMappingCategory,
} from "./respiratoryPersistenceMapping";

const ALL_RESPIRATORY_FIELD_VALUES_FIELDS = [
  "values.sobSeverity",
  "values.screeningDateTime",
  "values.priorComparison",
  "values.onsetOrSource",
  "values.lungSounds",
  "values.respiratoryPattern",
  "values.oxygenDelivery",
  "values.flowRateLpm",
  "values.ventilatorInfo",
  "values.spo2Value",
  "values.spo2Context",
  "values.exertionTolerance",
  "values.hopeComfortImpact",
  "values.hopeFunctionImpact",
];

const ALL_LIMITATION_FIELDS = [
  "limitation.scope",
  "limitation.reason",
  "limitation.assessedPortion",
  "limitation.followUpRequired",
  "limitation.responsibleClinicianId",
  "limitation.timingOrContingency",
];

const VALID_CATEGORIES: RespiratoryFieldMappingCategory[] = [
  "DIRECT_BACKEND_MAPPING",
  "TRANSFORMED_MAPPING",
  "DISPLAY_ONLY",
  "HISTORICAL_REFERENCE_ONLY",
  "BACKEND_DESTINATION_MISSING",
  "LEGACY_FIELD_NOT_USED_BY_WORKSPACE",
  "UNRESOLVED",
];

describe("RESPIRATORY_PERSISTENCE_MAPPING", () => {
  it("1. is non-empty", () => {
    expect(RESPIRATORY_PERSISTENCE_MAPPING.length).toBeGreaterThan(0);
  });

  it("2. has no duplicate field entries", () => {
    const fields = RESPIRATORY_PERSISTENCE_MAPPING.map((e) => e.field);
    expect(new Set(fields).size).toBe(fields.length);
  });

  it("3. classifies every field into a valid category only", () => {
    for (const entry of RESPIRATORY_PERSISTENCE_MAPPING) {
      expect(VALID_CATEGORIES).toContain(entry.category);
    }
  });

  it("4. has no UNRESOLVED entries", () => {
    const unresolved = RESPIRATORY_PERSISTENCE_MAPPING.filter((e) => e.category === "UNRESOLVED");
    expect(unresolved).toEqual([]);
  });

  it("5. covers every RespiratoryFieldValues field", () => {
    for (const field of ALL_RESPIRATORY_FIELD_VALUES_FIELDS) {
      expect(findRespiratoryMappingEntry(field)).toBeDefined();
    }
  });

  it("6. covers every AssessmentLimitation sub-field", () => {
    for (const field of ALL_LIMITATION_FIELDS) {
      expect(findRespiratoryMappingEntry(field)).toBeDefined();
    }
  });

  it("7. covers situation, reviewState, reviewExceptions, summary, and version", () => {
    for (const field of ["situation", "reviewState", "reviewExceptions", "summary", "version / expectedVersion"]) {
      expect(findRespiratoryMappingEntry(field)).toBeDefined();
    }
  });

  it("8. classifies every RespiratoryFieldValues field as DIRECT_BACKEND_MAPPING (opaque JSONB passthrough)", () => {
    for (const field of ALL_RESPIRATORY_FIELD_VALUES_FIELDS) {
      expect(findRespiratoryMappingEntry(field)?.category).toBe("DIRECT_BACKEND_MAPPING");
    }
  });

  it("9. classifies limitation.scope as DIRECT_BACKEND_MAPPING to limitation_scope", () => {
    const entry = findRespiratoryMappingEntry("limitation.scope");
    expect(entry?.category).toBe("DIRECT_BACKEND_MAPPING");
    expect(entry?.backendDestination).toContain("limitation_scope");
  });

  it("10. classifies limitation.reason as DIRECT_BACKEND_MAPPING to limitation_reason", () => {
    const entry = findRespiratoryMappingEntry("limitation.reason");
    expect(entry?.category).toBe("DIRECT_BACKEND_MAPPING");
    expect(entry?.backendDestination).toContain("limitation_reason");
  });

  it("11. classifies limitation.assessedPortion as DIRECT_BACKEND_MAPPING to limitation_assessed_portion", () => {
    const entry = findRespiratoryMappingEntry("limitation.assessedPortion");
    expect(entry?.category).toBe("DIRECT_BACKEND_MAPPING");
    expect(entry?.backendDestination).toContain("limitation_assessed_portion");
  });

  it("12. classifies limitation.followUpRequired as TRANSFORMED_MAPPING (boolean <-> Text column)", () => {
    const entry = findRespiratoryMappingEntry("limitation.followUpRequired");
    expect(entry?.category).toBe("TRANSFORMED_MAPPING");
    expect(entry?.backendDestination).toContain("limitation_follow_up_required");
  });

  it("13. classifies limitation.responsibleClinicianId as BACKEND_DESTINATION_MISSING with a null destination", () => {
    const entry = findRespiratoryMappingEntry("limitation.responsibleClinicianId");
    expect(entry?.category).toBe("BACKEND_DESTINATION_MISSING");
    expect(entry?.backendDestination).toBeNull();
  });

  it("14. classifies limitation.timingOrContingency as BACKEND_DESTINATION_MISSING with a null destination", () => {
    const entry = findRespiratoryMappingEntry("limitation.timingOrContingency");
    expect(entry?.category).toBe("BACKEND_DESTINATION_MISSING");
    expect(entry?.backendDestination).toBeNull();
  });

  it("15. has exactly two BACKEND_DESTINATION_MISSING entries (no more, no fewer)", () => {
    const missing = RESPIRATORY_PERSISTENCE_MAPPING.filter((e) => e.category === "BACKEND_DESTINATION_MISSING");
    expect(missing.map((e) => e.field).sort()).toEqual(
      ["limitation.responsibleClinicianId", "limitation.timingOrContingency"].sort(),
    );
  });

  it("16. every DIRECT_BACKEND_MAPPING / TRANSFORMED_MAPPING entry has a non-null backendDestination", () => {
    const mapped = RESPIRATORY_PERSISTENCE_MAPPING.filter(
      (e) => e.category === "DIRECT_BACKEND_MAPPING" || e.category === "TRANSFORMED_MAPPING",
    );
    for (const entry of mapped) {
      expect(entry.backendDestination).not.toBeNull();
    }
  });

  it("17. every BACKEND_DESTINATION_MISSING entry has a null backendDestination", () => {
    const missing = RESPIRATORY_PERSISTENCE_MAPPING.filter((e) => e.category === "BACKEND_DESTINATION_MISSING");
    for (const entry of missing) {
      expect(entry.backendDestination).toBeNull();
    }
  });

  it("18. every entry has a non-empty explanatory note", () => {
    for (const entry of RESPIRATORY_PERSISTENCE_MAPPING) {
      expect(entry.note.trim().length).toBeGreaterThan(0);
    }
  });
});
