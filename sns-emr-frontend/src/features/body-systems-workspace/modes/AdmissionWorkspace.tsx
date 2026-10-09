/**
 * SNS Body Systems Workspace — Admission / Comprehensive mode entry point.
 *
 * Thin wrapper over BodyShieldShell that fixes visitMode to
 * "admission_comprehensive" per the canonical visit-mode configuration
 * (baseline evidence required, no prior-period comparison). No admission-
 * specific business logic lives here — see visitMode.ts.
 */
import * as React from "react";
import { BodyShieldShell } from "../shell/BodyShieldShell";

export interface AdmissionWorkspaceProps {
  patientId: string;
  visitId: string;
  bodySystemsAssessmentId: string;
}

export function AdmissionWorkspace(props: AdmissionWorkspaceProps) {
  return <BodyShieldShell {...props} initialVisitMode="admission_comprehensive" />;
}
