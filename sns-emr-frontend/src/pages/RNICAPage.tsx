import { useState } from "react";
import RNICA from "../components/RNICA";
import { getRnIcaCommandWorkspaceEnabled, setRnIcaCommandWorkspaceEnabled } from "../features/rnIcaCommandWorkspace";

import { getActivePatientId } from "../utils/activePatient";

export default function RNICAPage() {
  const [workspacePilot, setWorkspacePilot] = useState(getRnIcaCommandWorkspaceEnabled);

  const exitPilot = () => {
    setRnIcaCommandWorkspaceEnabled(false);
    setWorkspacePilot(false);
  };

  return <RNICA patientId={getActivePatientId() ?? ""} workspacePilot={workspacePilot} onExitWorkspacePilot={exitPilot} />;
}
