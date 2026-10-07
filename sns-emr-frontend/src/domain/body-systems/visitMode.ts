/**
 * SNS Body Systems — visit-mode configuration.
 *
 * Source of truth: docs/design/body-systems-figma/SNS_Body_Systems_Engineering_Specification.md
 * section 6 ("Visit-Mode Behavior"). All three visit modes share the same ten
 * systems, the same primary entity model, the same ownership registry, and
 * the same exception engine (section 6.1) — this module only expresses the
 * behavior that legitimately differs per mode, never a parallel system list
 * or a parallel ownership model.
 */
import type { VisitMode } from "./types";

export interface VisitModeConfig {
  mode: VisitMode;
  /** Section 6.1: identical in every mode. */
  allTenSystemsAlwaysVisible: true;
  /** Primary clinical goal of this mode, for display/help text only — not a business rule. */
  goal: string;
  /** Section 6.2/6.3/6.4: every mode still requires an explicit current review outcome per system. */
  requiresExplicitCurrentReviewForAllSystems: true;
  /**
   * Whether existing/prior evidence may be shown read-only until the RN
   * explicitly confirms or updates it (section 6.3, Routine RN). Admission
   * has no established "prior" by definition of establishing baseline;
   * Recertification shows prior but as a dated comparison, not as an
   * inline read-only draft of the current system.
   */
  priorEvidenceReadOnlyUntilConfirmed: boolean;
  /** Section 6.4: Recertification only — current vs. dated prior-period comparison view. */
  showsCurrentVsPriorPeriodComparison: boolean;
  /**
   * Section 6.4: "Do not copy prior values into current fields." This is an
   * absolute prohibition, not a per-mode toggle — every mode is `false`, and
   * no caller may set this `true`.
   */
  copyForwardPriorValuesIntoCurrentFields: false;
  /**
   * Section 6.3: "Stable does not mean normal." Applies to every mode a
   * `stable_existing` situation can occur in — every mode is `false`.
   */
  treatsStableAsNormal: false;
}

export const VISIT_MODE_CONFIGS: Record<VisitMode, VisitModeConfig> = {
  admission_comprehensive: {
    mode: "admission_comprehensive",
    allTenSystemsAlwaysVisible: true,
    goal: "Establish current baseline.",
    requiresExplicitCurrentReviewForAllSystems: true,
    priorEvidenceReadOnlyUntilConfirmed: false,
    showsCurrentVsPriorPeriodComparison: false,
    copyForwardPriorValuesIntoCurrentFields: false,
    treatsStableAsNormal: false,
  },
  routine_rn: {
    mode: "routine_rn",
    allTenSystemsAlwaysVisible: true,
    goal: "Document current state, change, intervention response, and follow-up without re-entering unchanged baseline detail.",
    requiresExplicitCurrentReviewForAllSystems: true,
    priorEvidenceReadOnlyUntilConfirmed: true,
    showsCurrentVsPriorPeriodComparison: false,
    copyForwardPriorValuesIntoCurrentFields: false,
    treatsStableAsNormal: false,
  },
  recertification: {
    mode: "recertification",
    allTenSystemsAlwaysVisible: true,
    goal: "Compare dated current evidence with dated prior-period evidence.",
    requiresExplicitCurrentReviewForAllSystems: true,
    priorEvidenceReadOnlyUntilConfirmed: false,
    showsCurrentVsPriorPeriodComparison: true,
    copyForwardPriorValuesIntoCurrentFields: false,
    treatsStableAsNormal: false,
  },
};

export function getVisitModeConfig(mode: VisitMode): VisitModeConfig {
  const config = VISIT_MODE_CONFIGS[mode];
  if (!config) {
    throw new Error(`Unknown visit mode: "${mode}"`);
  }
  return config;
}

/**
 * Section 6.2: "Admission must not be reduced to a change-only workflow."
 * A change-only workflow is one that skips current baseline evidence and
 * only records deltas — callers that drive the admission form flow should
 * treat this as `true` as a guard they are expected to honor; it is not a
 * configurable toggle.
 */
export function admissionRequiresBaselineEvidence(mode: VisitMode): boolean {
  return mode === "admission_comprehensive";
}

/**
 * Section 6.4: "Recertification review does not require recreating an
 * admission assessment." Recertification may read/compare prior evidence
 * without requiring the full baseline field set that admission requires.
 */
export function requiresFullAdmissionFieldSet(mode: VisitMode): boolean {
  return mode === "admission_comprehensive";
}
