import { useEffect, useState } from "react";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchPatientSummary } from "../api/patientCharts";
import { getActivePatientId } from "../utils/activePatient";

const sections = [
  { key: "overview", label: "Care Overview" },
  { key: "visit-calendar", label: "Visit Calendar" },
  { key: "admission", label: "Admission" },
  { key: "assessment", label: "Assessment" },
  { key: "tx-meds-dme-supplies", label: "Tx / Meds / DME / Supplies" },
  { key: "idg", label: "IDG" },
  { key: "plan-of-care", label: "Plan of Care (POC)" },
  { key: "bereavement", label: "Bereavement" },
  { key: "compliance", label: "Compliance" },
  { key: "lcd-eligibility", label: "LCD Eligibility" },
  { key: "incident-occurrence", label: "Incident / Occurrence" },
  { key: "documents", label: "Documents" },
  { key: "communication-log", label: "Communication Log" },
  { key: "care-team", label: "Care Team" },
];

const patientOverview = {
  diagnosis: "Bereavement focus for family and caregiver support",
  painSummary: "No patient pain data; monitoring grief risk, follow-up calls, and support plan.",
  primaryProvider: "Bereavement coordinator",
  hnpStatus: "Family support plan active",
  lastVisit: "Last bereavement contact 2 days ago",
  disciplineHistory: [
    "Initial bereavement assessment completed",
    "Follow-up plan established for caregiver risk",
    "Support letter and resource packet prepared",
    "IDG notified of family coping concerns",
  ],
  careTeam: ["Bereavement", "MSW", "Chaplain", "RN", "Admin"],
};

const metrics = [
  { label: "Risk level", value: "Moderate", tone: "warn" as const },
  { label: "Primary concern", value: "Caregiver isolation", tone: "default" as const },
  { label: "Follow-up", value: "Phone call due Friday", tone: "good" as const },
  { label: "Support type", value: "Letters + grief resources", tone: "default" as const },
];

const contacts = [
  { name: "Spouse", status: "High contact", note: "Requests follow-up after discharge." },
  { name: "Adult child", status: "Supportive", note: "Open to phone check-ins." },
  { name: "Caregiver", status: "Monitor", note: "Showed early signs of anticipatory grief." },
];

export default function BereavementPage() {
  const patientId = getActivePatientId() ?? "";
  const [patientName, setPatientName] = useState("Loading patient...");

  useEffect(() => {
    if (!patientId) {
      setPatientName("No patient selected");
      return;
    }

    fetchPatientSummary(patientId)
      .then((result) => setPatientName(result.patient.full_name || "Patient"))
      .catch(() => setPatientName("Patient"));
  }, [patientId]);

  return (
    <PatientModuleShell
      patientId={patientId}
      patientName={patientName}
      disciplineLabel="Bereavement"
      title="Bereavement"
      subtitle="Assessment, support plan, follow-up schedule, and grief-risk monitoring"
      activeSection="bereavement"
      sections={sections}
      onSelect={() => undefined}
      patientOverview={patientOverview}
      metrics={metrics}
    >
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 20 }}>
        <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#f8fafc", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", fontSize: 15, fontWeight: 800, background: "#f1f5f9", borderBottom: "1px solid #dfe8ee" }}>
            Bereavement assessment history
          </div>
          <div style={{ padding: 16 }}>
            {patientOverview.disciplineHistory.map((item) => (
              <div key={item} style={{ marginBottom: 10, fontSize: 13, lineHeight: 1.5, color: "#0f172a" }}>
                • {item}
              </div>
            ))}
          </div>
        </section>

        <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#fff", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", fontSize: 15, fontWeight: 800, background: "#eef7ff", borderBottom: "1px solid #dfe8ee" }}>
            Support contacts
          </div>
          <div style={{ padding: 16 }}>
            {contacts.map((contact) => (
              <div key={contact.name} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: "1px solid #edf2f7" }}>
                <div style={{ fontSize: 13, fontWeight: 800 }}>{contact.name}</div>
                <div style={{ fontSize: 11, color: "#0f766e", fontWeight: 700, marginTop: 4 }}>{contact.status}</div>
                <div style={{ fontSize: 12, color: "#475569", marginTop: 6 }}>{contact.note}</div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </PatientModuleShell>
  );
}
