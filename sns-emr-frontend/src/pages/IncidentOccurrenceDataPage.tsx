import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchIncidentOccurrence, type IncidentOccurrenceResponse } from "../api/patientCharts";

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
  { key: "physician", label: "Physician" },
  { key: "lcd-eligibility", label: "LCD Eligibility" },
  { key: "incident-occurrence", label: "Incident / Occurrence" },
  { key: "documents", label: "Documents" },
  { key: "communication-log", label: "Communication Log" },
  { key: "care-team", label: "Care Team" },
];

const patientId = getActivePatientId() ?? "";
export default function IncidentOccurrenceDataPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<IncidentOccurrenceResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchIncidentOccurrence(patientId).then((result) => {
      setData(result);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleSelect = (section: string) => {
    const routes: Record<string, string> = {
      overview: "/care-overview",
      physician: "/physician",
      "visit-calendar": "/volunteer-scheduling",
      bereavement: "/bereavement",
      compliance: "/compliance",
      "lcd-eligibility": "/patient-lcd",
      "incident-occurrence": "/incident-occurrence",
      "communication-log": "/communication-log",
    };

    if (routes[section]) navigate(routes[section]);
  };

  const metrics = data ? [
    { label: "Total incidents", value: String(data.total) },
    { label: "Falls", value: String(data.counts_by_type.Fall || 0) },
    { label: "Sentinel events", value: String(data.counts_by_type["Sentinel Event"] || 0) },
    { label: "Medication reactions", value: String(data.counts_by_type["Adverse Reaction of Meds"] || 0) },
  ] : [];

  return (
    <PatientModuleShell
      patientId={patientId}
      patientName={data ? "Carr, V" : "Loading..."}
      disciplineLabel="Incident / Occurrence"
      title="Incident / Occurrence"
      subtitle="Classify the event, document the narrative, and assign follow-up"
      activeSection="incident-occurrence"
      sections={sections}
      onSelect={handleSelect}
      patientOverview={data ? {
        diagnosis: "Incident / occurrence tracking for patient safety and reporting",
        painSummary: `${data.total} incidents on file.`,
        primaryProvider: "Safety / compliance lead",
        hnpStatus: "Occurrence log active",
        lastVisit: data.items[0]?.incident_date || "—",
        disciplineHistory: data.items.slice(0, 4).map((item) => `${item.incident_type} — ${item.incident_severity}`),
        careTeam: ["RN", "Admin", "MD", "Compliance", "MSW"],
      } : { diagnosis: "Loading...", painSummary: "Loading...", primaryProvider: "—", hnpStatus: "—", lastVisit: "—", disciplineHistory: [], careTeam: [] }}
      metrics={metrics}
    >
      {loading ? <div>Loading incident data...</div> : null}
      {data ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#fff", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#f1f5f9", borderBottom: "1px solid #dfe8ee" }}>Incident list</div>
            <div style={{ padding: 16 }}>
              {data.items.map((item) => (
                <div key={item.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid #edf2f7" }}>
                  <div style={{ fontSize: 13, fontWeight: 800 }}>{item.incident_type}</div>
                  <div style={{ fontSize: 12, color: "#475569" }}>{item.incident_date} · {item.incident_severity}</div>
                  <div style={{ fontSize: 12, marginTop: 6 }}>{item.narrative}</div>
                </div>
              ))}
            </div>
          </section>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#f8fafc", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#eef7ff", borderBottom: "1px solid #dfe8ee" }}>Counts</div>
            <div style={{ padding: 16 }}>
              {Object.entries(data.counts_by_type).map(([key, value]) => (
                <div key={key} style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                  <span>{key}</span><strong>{value}</strong>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </PatientModuleShell>
  );
}
