import MSWICA from "../components/MSWICA";

import { getActivePatientId } from "../utils/activePatient";
const DEFAULT_PATIENT_ID = getActivePatientId() ?? "";
export default function MSWICAPage() {
  return <MSWICA patientId={DEFAULT_PATIENT_ID} />;
}
