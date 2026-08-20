import RNICA from "../components/RNICA";
import { useRnIcaCommandWorkspace } from "../features/rnIcaCommandWorkspace";

import { getActivePatientId } from "../utils/activePatient";

export default function RNICAPage() {
  const { enabled: workspacePilot, disable: exitPilot } = useRnIcaCommandWorkspace();

  return <RNICA patientId={getActivePatientId() ?? ""} workspacePilot={workspacePilot} onExitWorkspacePilot={exitPilot} />;
}
