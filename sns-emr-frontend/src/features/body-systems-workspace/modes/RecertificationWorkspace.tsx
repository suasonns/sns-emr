/**
 * SNS Body Systems Workspace — Recertification mode entry point.
 *
 * Thin wrapper over BodyShieldShell that fixes visitMode to
 * "recertification" per the canonical visit-mode configuration (dated
 * current-vs-prior-period comparison). Documentation supports review; it
 * does not determine eligibility or prognosis automatically — no such
 * logic exists in this component or in BodyShieldShell.
 */
import * as React from "react";
import { BodyShieldShell } from "../shell/BodyShieldShell";

export interface RecertificationWorkspaceProps {
  patientId: string;
  visitId: string;
  bodySystemsAssessmentId: string;
}

export function RecertificationWorkspace(props: RecertificationWorkspaceProps) {
  return <BodyShieldShell {...props} initialVisitMode="recertification" />;
}
