import SCICA from "../components/SCICA";

const DEFAULT_PATIENT_ID = "5d31a53f-eebd-468f-bcb6-1b43771fe113";

export default function SCICAPage() {
  return <SCICA patientId={DEFAULT_PATIENT_ID} />;
}
