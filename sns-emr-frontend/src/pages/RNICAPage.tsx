import RNICA from "../components/RNICA";

import { getActivePatientId } from "../utils/activePatient";

export default function RNICAPage() {
  return <RNICA patientId={getActivePatientId() ?? ""} />;
}
