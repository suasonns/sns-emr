/**
 * SNS Body Systems Workspace — public barrel.
 *
 * Phase 1 foundation: BodyShieldShell + BodySystemsWorkspace platform,
 * the fixed ten-system registry, Current vs Historical evidence display,
 * Review By Exception, the source-linked correction scaffold, the three
 * visit-mode entry points, the AI suggestion shell, and the Neurological /
 * Respiratory pilot panels. Built on, and never duplicating, the canonical
 * domain foundation in `src/domain/body-systems`.
 */
export { BodyShieldShell } from "./shell/BodyShieldShell";
export { ResponsiveDesktopLayout } from "./shell/ResponsiveDesktopLayout";
export { ResponsiveMobileLayout } from "./shell/ResponsiveMobileLayout";
export { useViewportKind } from "./shell/useViewportKind";

export { BodySystemsWorkspace } from "./workspace/BodySystemsWorkspace";
export { SystemRegisterRow } from "./workspace/SystemRegisterRow";
export { CurrentHistoricalEvidencePanel } from "./workspace/CurrentHistoricalEvidencePanel";
export { ReviewExceptionDrawer } from "./workspace/ReviewExceptionDrawer";
export { SourceLinkedCorrectionFlow } from "./workspace/SourceLinkedCorrectionFlow";

export { AdmissionWorkspace } from "./modes/AdmissionWorkspace";
export { RoutineRNWorkspace } from "./modes/RoutineRNWorkspace";
export { RecertificationWorkspace } from "./modes/RecertificationWorkspace";

export { AISuggestionShell } from "./ai/AISuggestionShell";

export { NeurologicalSystemPanel } from "./systems/neurological/NeurologicalSystemPanel";
export {
  RespiratorySystemPanel,
  INITIAL_RESPIRATORY_FIELD_VALUES,
  type RespiratoryFieldValues,
  type HopeImpactValue,
} from "./systems/respiratory/RespiratorySystemPanel";
export {
  CardiovascularSystemPanel,
  INITIAL_CARDIOVASCULAR_FIELD_VALUES,
  type CardiovascularFieldValues,
} from "./systems/cardiovascular/CardiovascularSystemPanel";
export {
  GastrointestinalSystemPanel,
  INITIAL_GASTROINTESTINAL_FIELD_VALUES,
  type GastrointestinalFieldValues,
} from "./systems/gastrointestinal/GastrointestinalSystemPanel";

export {
  useBodySystemsAssessmentState,
  type SystemWorkingState,
  type BodySystemsAssessmentCounts,
  type UseBodySystemsAssessmentStateResult,
} from "./state/useBodySystemsAssessmentState";
