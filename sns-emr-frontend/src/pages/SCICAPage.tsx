import SCICA from "../components/SCICA";

import { getActivePatientId } from "../utils/activePatient";

export default function SCICAPage() {
  return <SCICA patientId={getActivePatientId() ?? ""} />;
}
