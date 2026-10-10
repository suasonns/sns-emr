/**
 * SNS Body Systems Workspace — chart mount point.
 *
 * Thin adapter that mounts the real `BodyShieldShell` into the existing
 * patient chart for a given patient. No clinical logic lives here.
 *
 * `visitId` and `bodySystemsAssessmentId` are not yet backed by a
 * dedicated visit/assessment selection flow in the patient chart (only
 * Respiratory has real backend persistence today, scoped by `patientId`
 * via `useRespiratoryPersistence`; see BodyShieldShell). Both values are
 * derived deterministically from the real `patientId` rather than
 * hardcoded literals: `bodySystemsAssessmentId` is used only to tag
 * in-memory exception records (no API call), and `visitId` is used only
 * as a display/data attribute. Neither is sent to, or required by, any
 * backend endpoint. This is a documented Phase 1 limitation, not a
 * fabricated clinical identifier.
 */
import * as React from "react";
import { BodyShieldShell } from "./shell/BodyShieldShell";

export interface BodySystemsWorkspacePageProps {
  patientId: string;
}

export function BodySystemsWorkspacePage({ patientId }: BodySystemsWorkspacePageProps) {
  if (!patientId) {
    return null;
  }

  return (
    <BodyShieldShell
      patientId={patientId}
      visitId={`chart-visit:${patientId}`}
      bodySystemsAssessmentId={`body-systems-assessment:${patientId}`}
    />
  );
}
