import MSWICA from "../components/MSWICA";

import { getActivePatientId } from "../utils/activePatient";

export default function MSWICAPage() {
  return <MSWICA patientId={getActivePatientId() ?? ""} />;
}
