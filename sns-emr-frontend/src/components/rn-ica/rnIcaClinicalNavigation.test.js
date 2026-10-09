import { describe, expect, it } from "vitest";

import {
  RNICA_ASSESSMENT_MODULES,
  UPDATE_HIDDEN_ROUTE_KEYS,
  validateRnIcaClinicalNavigation,
} from "./rnIcaClinicalNavigation";

// Regression coverage for issue #166: RNICA.jsx's `routes` memo hides both
// "sfv" (any ongoing/recert visit) AND "admissionsOrder" (Update/HUV visits
// specifically, via UPDATE_HIDDEN_ROUTE_KEYS) from the ACTUAL navigation,
// but the validator's EXPECTED route count previously only accounted for
// "sfv" being dropped -- so a genuine Update/HUV visit (28 actual routes)
// was always flagged against a stale 29-route expectation, crashing the
// whole SPA in dev builds (RNICACommandWorkspace.jsx throws when
// `import.meta.env.DEV && !navigationAudit.valid`).
//
// These tests build the routes array exactly the way RNICA.jsx's `routes`
// memo does, for each real visit type, and assert the validator agrees.

function buildRoutes({ isOngoing = false, isUpdateAssessment = false } = {}) {
  return RNICA_ASSESSMENT_MODULES.filter((module) => {
    if (isOngoing && module.key === "sfv") return false;
    if (isUpdateAssessment && UPDATE_HIDDEN_ROUTE_KEYS.has(module.key)) return false;
    return true;
  }).map((module) => ({
    // Mirrors RNICA.jsx's `commandRoutes` mapping, which strips the HOPE
    // regulatory badge for any ongoing (Recert or Update/HUV) visit --
    // the validator's `expectedRegulator` check already expects this.
    ...module,
    regulator: isOngoing && module.regulator === "HOPE" ? undefined : module.regulator,
  }));
}

const ALL_FORM_SECTIONS = Array.from(new Set(RNICA_ASSESSMENT_MODULES.map((module) => module.formSection)));

describe("validateRnIcaClinicalNavigation", () => {
  it("passes for Admission (initial) visits -- full 30-module navigation", () => {
    const routes = buildRoutes({ isOngoing: false, isUpdateAssessment: false });
    expect(routes).toHaveLength(30);
    const result = validateRnIcaClinicalNavigation(routes, ALL_FORM_SECTIONS, false, false);
    expect(result.errors).toEqual([]);
    expect(result.valid).toBe(true);
  });

  it("passes for Recert (ongoing, non-Update) visits -- 29 modules, sfv dropped only", () => {
    const routes = buildRoutes({ isOngoing: true, isUpdateAssessment: false });
    expect(routes).toHaveLength(29);
    const result = validateRnIcaClinicalNavigation(routes, ALL_FORM_SECTIONS, true, false);
    expect(result.errors).toEqual([]);
    expect(result.valid).toBe(true);
  });

  it("passes for Update/HUV visits -- 28 modules, sfv and admissionsOrder both dropped", () => {
    const routes = buildRoutes({ isOngoing: true, isUpdateAssessment: true });
    expect(routes).toHaveLength(28);
    const result = validateRnIcaClinicalNavigation(routes, ALL_FORM_SECTIONS, true, true);
    expect(result.errors).toEqual([]);
    expect(result.valid).toBe(true);
  });

  it("passes for an HUV1-shaped Update visit (same 28-module navigation as any Update visit)", () => {
    // HUV1/HUV2 are both represented as assessmentType "update" at
    // different day-window offsets -- the navigation shape is identical;
    // only hope_event_type/hope_event_date differ downstream in the
    // backend, which this test suite does not touch.
    const routes = buildRoutes({ isOngoing: true, isUpdateAssessment: true });
    const result = validateRnIcaClinicalNavigation(routes, ALL_FORM_SECTIONS, true, true);
    expect(result.valid).toBe(true);
    expect(routes.some((route) => route.key === "sfv")).toBe(false);
    expect(routes.some((route) => route.key === "admissionsOrder")).toBe(false);
  });

  it("passes for an HUV2-shaped Update visit (same 28-module navigation as any Update visit)", () => {
    const routes = buildRoutes({ isOngoing: true, isUpdateAssessment: true });
    const result = validateRnIcaClinicalNavigation(routes, ALL_FORM_SECTIONS, true, true);
    expect(result.valid).toBe(true);
    expect(routes.some((route) => route.key === "sfv")).toBe(false);
    expect(routes.some((route) => route.key === "admissionsOrder")).toBe(false);
  });

  it("REGRESSION: still fails when an Update/HUV visit is unexpectedly missing an additional module", () => {
    // Proves the fix only corrected the *expected* count for the two
    // intentionally-hidden keys -- it does not silently accept any other
    // unexpected route loss. Dropping "vitals" on top of the two
    // intentionally-hidden keys must still be caught (27 actual vs. 28
    // expected for Update/HUV).
    const routes = buildRoutes({ isOngoing: true, isUpdateAssessment: true }).filter(
      (route) => route.key !== "vitals",
    );
    expect(routes).toHaveLength(27);
    const result = validateRnIcaClinicalNavigation(routes, ALL_FORM_SECTIONS, true, true);
    expect(result.valid).toBe(false);
    expect(result.errors.some((error) => error.includes("must contain 28 modules, received 27"))).toBe(true);
  });

  it("REGRESSION: still fails when a Recert visit unexpectedly retains admissionsOrder's old position mismatch", () => {
    // Recert visits do NOT hide admissionsOrder. If a future change
    // mistakenly hid it for Recert too, the validator (called with
    // isUpdateAssessment=false for Recert) must still flag the mismatch
    // rather than silently accepting a shorter list.
    const routes = buildRoutes({ isOngoing: true, isUpdateAssessment: false }).filter(
      (route) => route.key !== "admissionsOrder",
    );
    expect(routes).toHaveLength(28);
    const result = validateRnIcaClinicalNavigation(routes, ALL_FORM_SECTIONS, true, false);
    expect(result.valid).toBe(false);
    expect(result.errors.some((error) => error.includes("must contain 29 modules, received 28"))).toBe(true);
  });

  it("still fails when Admission is missing a module (no hidden-key allowance applies)", () => {
    const routes = buildRoutes({ isOngoing: false, isUpdateAssessment: false }).filter(
      (route) => route.key !== "diagnoses",
    );
    const result = validateRnIcaClinicalNavigation(routes, ALL_FORM_SECTIONS, false, false);
    expect(result.valid).toBe(false);
    expect(result.errors.some((error) => error.includes("must contain 30 modules, received 29"))).toBe(true);
  });
});
