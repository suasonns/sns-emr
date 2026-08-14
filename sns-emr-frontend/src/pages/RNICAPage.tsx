import RNICA from "../components/RNICA";

const DEFAULT_PATIENT_ID = "5d31a53f-eebd-468f-bcb6-1b43771fe113";

export default function RNICAPage() {
  return <RNICA patientId={DEFAULT_PATIENT_ID} />;
}
