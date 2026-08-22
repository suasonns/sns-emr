import { describe, it, expect } from "vitest";
import {
  ACTION_CENTER_REQUEST_TYPES,
  ACTION_CENTER_STATUSES,
} from "./AdmissionActionCenterDrawer";

describe("Admission Action Center (Phase A) request types", () => {
  it("exposes exactly the five in-scope request types", () => {
    const values = ACTION_CENTER_REQUEST_TYPES.map((t) => t.value);
    expect(values).toEqual([
      "MEDICATION_REQUEST",
      "PHYSICIAN_ORDER",
      "DME_ORDER",
      "SUPPLY_ORDER",
      "REFERRAL",
    ]);
  });

  it("does not include out-of-scope types (Lab / Oxygen / Treatment)", () => {
    const values = ACTION_CENTER_REQUEST_TYPES.map((t) => t.value);
    expect(values).not.toContain("LAB_ORDER");
    expect(values).not.toContain("OXYGEN_ORDER");
    expect(values).not.toContain("TREATMENT_ORDER");
  });

  it("gives every request type a human-readable label", () => {
    for (const t of ACTION_CENTER_REQUEST_TYPES) {
      expect(typeof t.label).toBe("string");
      expect(t.label.length).toBeGreaterThan(0);
    }
  });
});

describe("Admission Action Center (Phase A) statuses", () => {
  it("tracks exactly the linear REQUESTED -> COMPLETED lifecycle in order", () => {
    expect(ACTION_CENTER_STATUSES).toEqual([
      "REQUESTED",
      "ORDERED",
      "SENT",
      "ACKNOWLEDGED",
      "DELIVERED",
      "COMPLETED",
    ]);
  });

  it("does not include approval-routing or fulfillment sub-states", () => {
    expect(ACTION_CENTER_STATUSES).not.toContain("PENDING_APPROVAL");
    expect(ACTION_CENTER_STATUSES).not.toContain("APPROVED");
    expect(ACTION_CENTER_STATUSES).not.toContain("REJECTED");
  });
});
