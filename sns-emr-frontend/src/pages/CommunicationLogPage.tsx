import PatientModuleShell from "../components/PatientModuleShell";

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
  diagnosis: "Cross-discipline communication log",
  painSummary: "Family calls, on-call reports, reminders, and status updates should flow into IDG review.",
  primaryProvider: "Communication coordinator",
  hnpStatus: "Log current",
  lastVisit: "Updated moments ago",
  disciplineHistory: [
    "On-call family call documented",
    "Patient notification logged",
    "Progress note harvested for review",
    "IDG-ready summary generated from log",
  ],
  careTeam: ["RN", "MSW", "SC", "MD", "Admin", "Volunteer"],
};

const metrics = [
  { label: "Log count", value: "4", tone: "default" as const },
  { label: "On-call calls", value: "2", tone: "warn" as const },
  { label: "IDG ready", value: "Yes", tone: "good" as const },
  { label: "Open follow-up", value: "1 reminder", tone: "warn" as const },
];

const logTypes = [
  "All",
  "Bereavement Note",
  "Check Status",
  "Comm Note",
  "On-Call Note",
  "Patient Notification",
  "Phone Call",
  "Progress Note",
  "Reminder",
  "Vol Note",
];

const logEntries = [
  { type: "On-Call Note", body: "Family reported increased shortness of breath after hours; RN notified and reviewed interventions.", tag: "IDG" },
  { type: "Phone Call", body: "Caregiver called to confirm medication delivery and ask about symptom change.", tag: "Review" },
  { type: "Bereavement Note", body: "Spouse requested grief resources and follow-up after discharge planning.", tag: "IDG" },
  { type: "Vol Note", body: "Volunteer completed companionship visit and reported patient enjoyed conversation.", tag: "Archive" },
];

export default function CommunicationLogPage() {
  return (
    <PatientModuleShell
      patientId="HOSP-001234"
      patientName="Carr, V"
      disciplineLabel="Communication Log"
      title="Communication Log"
      subtitle="Capture every call, update, and note so IDG can review the patient story"
      activeSection="communication-log"
      sections={sections}
      onSelect={() => undefined}
      patientOverview={patientOverview}
      metrics={metrics}
    >
      <div style={{ display: "grid", gridTemplateColumns: "0.8fr 1.2fr", gap: 20 }}>
        <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#f8fafc", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", fontSize: 15, fontWeight: 800, background: "#f1f5f9", borderBottom: "1px solid #dfe8ee" }}>
            Event types
          </div>
          <div style={{ padding: 16, display: "flex", flexWrap: "wrap", gap: 8 }}>
            {logTypes.map((type, index) => (
              <span
                key={type}
                style={{
                  display: "inline-flex",
                  borderRadius: 999,
                  padding: "6px 10px",
                  fontSize: 11,
                  fontWeight: 800,
                  background: index === 0 ? "#0f766e" : "#e2e8f0",
                  color: index === 0 ? "#fff" : "#0f172a",
                }}
              >
                {type}
              </span>
            ))}
          </div>
        </section>

        <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#fff", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", fontSize: 15, fontWeight: 800, background: "#eef7ff", borderBottom: "1px solid #dfe8ee" }}>
            Log entries
          </div>
          <div style={{ padding: 16 }}>
            {logEntries.map((entry) => (
              <div key={`${entry.type}-${entry.body}`} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: "1px solid #edf2f7" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <div style={{ fontSize: 13, fontWeight: 800 }}>{entry.type}</div>
                  <div style={{ fontSize: 10, fontWeight: 800, color: "#0f766e", textTransform: "uppercase" }}>{entry.tag}</div>
                </div>
                <div style={{ marginTop: 6, fontSize: 12, color: "#475569", lineHeight: 1.6 }}>{entry.body}</div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </PatientModuleShell>
  );
}
