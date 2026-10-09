/**
 * SNS Body Systems Workspace — Routine RN Visit mode entry point.
 *
 * Thin wrapper over BodyShieldShell that fixes visitMode to "routine_rn"
 * per the canonical visit-mode configuration (prior evidence read-only
 * until confirmed, change/symptom/intervention-focused). Same ten systems
 * as every other mode — not a reduced review.
 */
import * as React from "react";
import { BodyShieldShell } from "../shell/BodyShieldShell";

export interface RoutineRNWorkspaceProps {
  patientId: string;
  visitId: string;
  bodySystemsAssessmentId: string;
}

export function RoutineRNWorkspace(props: RoutineRNWorkspaceProps) {
  return <BodyShieldShell {...props} initialVisitMode="routine_rn" />;
}
