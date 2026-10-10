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
export { BodySystemsWorkspacePage } from "./BodySystemsWorkspacePage";
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
  GenitourinarySystemPanel,
  INITIAL_GENITOURINARY_FIELD_VALUES,
  type GenitourinaryFieldValues,
} from "./systems/genitourinary/GenitourinarySystemPanel";
export {
  NutritionSystemPanel,
  INITIAL_NUTRITION_FIELD_VALUES,
  type NutritionFieldValues,
} from "./systems/nutrition/NutritionSystemPanel";
export {
  MusculoskeletalSystemPanel,
  INITIAL_MUSCULOSKELETAL_FIELD_VALUES,
  type MusculoskeletalFieldValues,
} from "./systems/musculoskeletal/MusculoskeletalSystemPanel";
export {
  IntegumentarySystemPanel,
  INITIAL_INTEGUMENTARY_FIELD_VALUES,
  createWoundSubState,
  type IntegumentaryFieldValues,
  type WoundSubState,
  type WoundPhotoEvidence,
  type WoundBodyDiagramMarker,
  type BradenSubState,
} from "./systems/integumentary/IntegumentarySystemPanel";
export {
  InfectionSystemPanel,
  INITIAL_INFECTION_FIELD_VALUES,
  type InfectionFieldValues,
  type InfectionCrossSystemContext,
} from "./systems/infection/InfectionSystemPanel";

export { SystemNotesSection, type SystemNotesSectionProps } from "./systems/shared/SystemNotesSection";


export {
  useBodySystemsAssessmentState,
  type SystemWorkingState,
  type BodySystemsAssessmentCounts,
  type UseBodySystemsAssessmentStateResult,
} from "./state/useBodySystemsAssessmentState";
