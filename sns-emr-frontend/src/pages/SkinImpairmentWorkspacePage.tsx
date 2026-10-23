import { useParams } from "react-router-dom";

import RNICA from "../components/RNICA";
import { getActivePatientId } from "../utils/activePatient";

// PRODUCT OWNER CLARIFICATION (2026-11-22) "Dedicated Wound Workspace"
// means a genuinely separate routed page -- its own browser history
// entry -- not an overlay/modal/drawer rendered inside RNICA. This page
// mounts RNICA itself in a special `skinImpairmentWorkspace` render mode
// (mirroring the existing `workspacePilot` precedent) so it reuses the
// same already-loaded assessment data/autosave engine rather than a
// second, parallel data-fetching stack. "Back to RNICA" navigates to
// /rnica, a real route change, not a close-overlay action.
export default function SkinImpairmentWorkspacePage() {
  const { woundId } = useParams();

  return (
    <RNICA
      patientId={getActivePatientId() ?? ""}
      skinImpairmentWorkspace
      initialWoundId={woundId}
    />
  );
}
