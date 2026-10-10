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
import type { VisitMode } from "../../domain/body-systems";

export interface BodySystemsWorkspacePageProps {
  patientId: string;
  /**
   * The Workspace visit mode to open in, resolved by the host screen from
   * the real Nursing Assessment context (see `resolveBodySystemsVisitMode`).
   * Defaults to the Workspace's own fallback (`routine_rn`) only when the
   * host has not supplied a resolved mode.
   */
  initialVisitMode?: VisitMode;
}

export function BodySystemsWorkspacePage({ patientId, initialVisitMode }: BodySystemsWorkspacePageProps) {
  if (!patientId) {
    return null;
  }

  return (
    <BodyShieldShell
      patientId={patientId}
      visitId={`chart-visit:${patientId}`}
      bodySystemsAssessmentId={`body-systems-assessment:${patientId}`}
      initialVisitMode={initialVisitMode}
    />
  );
}
