import SCICA from "../components/SCICA";

import { getActivePatientId } from "../utils/activePatient";
const DEFAULT_PATIENT_ID = getActivePatientId() ?? "";
export default function SCICAPage() {
  return <SCICA patientId={DEFAULT_PATIENT_ID} />;
}
