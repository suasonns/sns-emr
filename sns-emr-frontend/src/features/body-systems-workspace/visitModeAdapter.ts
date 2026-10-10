/**
 * SNS Body Systems Workspace — Nursing Assessment visit-mode adapter.
 *
 * Deterministic mapping from the existing authoritative RNICA assessment
 * context (`isOngoingAssessment` / `isUpdateAssessment`, both already
 * computed in `RNICA.jsx` from `isOngoing/assessmentType` and already
 * piped into `RNICACommandWorkspace`) to the Workspace's `VisitMode`.
 *
 * No new identifiers, no string comparisons scattered in JSX, no fixture
 * or sample value is used here -- every input is a real assessment-context
 * flag the host already owns and passes down.
 */
import type { VisitMode } from "../../domain/body-systems";

export interface NursingAssessmentVisitContext {
  /** False for an Initial Admission/Comprehensive RNICA record. */
  isOngoingAssessment?: boolean;
  /**
   * True only for a HOPE Update Visit (HUV1/HUV2). When `isOngoingAssessment`
   * is true and this is false, the record is a non-HOPE Recertification.
   */
  isUpdateAssessment?: boolean;
}

/**
 * Resolves the Body Systems Workspace `VisitMode` for the current Nursing
 * Assessment record:
 *
 * - Initial Admission (`!isOngoingAssessment`)            -> admission_comprehensive
 * - HOPE Update Visit (`isOngoingAssessment && isUpdate`)  -> routine_rn
 * - Recertification (`isOngoingAssessment && !isUpdate`)  -> recertification
 */
export function resolveBodySystemsVisitMode({
  isOngoingAssessment = false,
  isUpdateAssessment = false,
}: NursingAssessmentVisitContext): VisitMode {
  if (!isOngoingAssessment) {
    return "admission_comprehensive";
  }
  return isUpdateAssessment ? "routine_rn" : "recertification";
}
