import RNICA from "../components/RNICA";

import { getActivePatientId } from "../utils/activePatient";
const DEFAULT_PATIENT_ID = getActivePatientId() ?? "";
export default function RNICAPage() {
  return <RNICA patientId={DEFAULT_PATIENT_ID} />;
}
