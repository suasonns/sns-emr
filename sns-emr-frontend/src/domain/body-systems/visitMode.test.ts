import { describe, expect, it } from "vitest";

import { BODY_SYSTEMS } from "./types";
import {
  VISIT_MODE_CONFIGS,
  admissionRequiresBaselineEvidence,
  getVisitModeConfig,
  requiresFullAdmissionFieldSet,
} from "./visitMode";

const ALL_MODES = ["admission_comprehensive", "routine_rn", "recertification"] as const;

describe("Body Systems — visit mode configuration", () => {
  it("defines exactly admission_comprehensive, routine_rn, and recertification", () => {
    expect(Object.keys(VISIT_MODE_CONFIGS).sort()).toEqual([...ALL_MODES].sort());
  });

  it("keeps all ten systems always visible for every visit mode (no diagnosis-based suppression)", () => {
    for (const mode of ALL_MODES) {
      const config = getVisitModeConfig(mode);
      expect(config.allTenSystemsAlwaysVisible).toBe(true);
      expect(config.requiresExplicitCurrentReviewForAllSystems).toBe(true);
    }
    // There is no per-mode or per-diagnosis system list to filter against —
    // BODY_SYSTEMS itself is the only system list, and it is fixed.
    expect(BODY_SYSTEMS.length).toBe(10);
  });

  it("never allows copying prior values forward into current fields, for any mode", () => {
    for (const mode of ALL_MODES) {
      expect(getVisitModeConfig(mode).copyForwardPriorValuesIntoCurrentFields).toBe(false);
    }
  });

  it("never treats 'stable' as equivalent to 'normal', for any mode", () => {
    for (const mode of ALL_MODES) {
      expect(getVisitModeConfig(mode).treatsStableAsNormal).toBe(false);
    }
  });

  it("only requires the full admission field set for admission_comprehensive", () => {
    expect(requiresFullAdmissionFieldSet("admission_comprehensive")).toBe(true);
    expect(requiresFullAdmissionFieldSet("routine_rn")).toBe(false);
    expect(requiresFullAdmissionFieldSet("recertification")).toBe(false);
  });

  it("only treats prior evidence as read-only-until-confirmed for routine_rn", () => {
    expect(getVisitModeConfig("routine_rn").priorEvidenceReadOnlyUntilConfirmed).toBe(true);
    expect(getVisitModeConfig("admission_comprehensive").priorEvidenceReadOnlyUntilConfirmed).toBe(false);
    expect(getVisitModeConfig("recertification").priorEvidenceReadOnlyUntilConfirmed).toBe(false);
  });

  it("only shows current-vs-prior-period comparison for recertification", () => {
    expect(getVisitModeConfig("recertification").showsCurrentVsPriorPeriodComparison).toBe(true);
    expect(getVisitModeConfig("admission_comprehensive").showsCurrentVsPriorPeriodComparison).toBe(false);
    expect(getVisitModeConfig("routine_rn").showsCurrentVsPriorPeriodComparison).toBe(false);
  });

  it("requires baseline evidence for admission_comprehensive only", () => {
    expect(admissionRequiresBaselineEvidence("admission_comprehensive")).toBe(true);
    expect(admissionRequiresBaselineEvidence("routine_rn")).toBe(false);
    expect(admissionRequiresBaselineEvidence("recertification")).toBe(false);
  });

  it("throws for an unknown visit mode rather than silently defaulting", () => {
    // @ts-expect-error intentionally invalid mode to prove no silent fallback
    expect(() => getVisitModeConfig("not_a_real_mode")).toThrow();
  });
});
