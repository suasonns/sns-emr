import { describe, expect, it } from "vitest";

import { OWNERSHIP_REGISTRY } from "./ownership";
import {
  RESPIRATORY_FIELD_INVENTORY,
  RESPIRATORY_NOT_VERIFIED_REQUIREMENTS,
  isRespiratoryRequirementNotVerified,
} from "./respiratoryFieldInventory";

describe("Body Systems — Respiratory verified field inventory", () => {
  it("every field is owned by respiratory", () => {
    for (const field of RESPIRATORY_FIELD_INVENTORY) {
      expect(field.owner).toBe("respiratory");
    }
  });

  it("every field has a non-empty legacy source path into the existing RNICA.jsx respiratory object", () => {
    for (const field of RESPIRATORY_FIELD_INVENTORY) {
      expect(field.legacySource.startsWith("respiratory.")).toBe(true);
    }
  });

  it("every field has a unique fieldId", () => {
    const ids = RESPIRATORY_FIELD_INVENTORY.map((field) => field.fieldId);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("every field's ownerFactKey exists in the respiratory ownership registry", () => {
    const respiratoryOwnership = OWNERSHIP_REGISTRY.find((rule) => rule.owner === "respiratory");
    expect(respiratoryOwnership).toBeDefined();
    for (const field of RESPIRATORY_FIELD_INVENTORY) {
      expect(respiratoryOwnership?.factKeys).toContain(field.ownerFactKey);
    }
  });

  it("controlled-value fields only exist for select-type fields", () => {
    for (const field of RESPIRATORY_FIELD_INVENTORY) {
      if (field.controlledValues) {
        expect(["single_select", "multi_select"]).toContain(field.responseType);
      }
    }
  });

  it("flags the documented NOT VERIFIED situation-branch sub-requirements", () => {
    expect(RESPIRATORY_NOT_VERIFIED_REQUIREMENTS).toContain("dated_prior_reference");
    expect(RESPIRATORY_NOT_VERIFIED_REQUIREMENTS).toContain("follow_up_decision");
    expect(isRespiratoryRequirementNotVerified("dated_prior_reference")).toBe(true);
    expect(isRespiratoryRequirementNotVerified("reason")).toBe(false);
  });
});
