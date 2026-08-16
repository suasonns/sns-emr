import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchCommunicationLog, type CommunicationLogResponse } from "../api/patientCharts";

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
export default function CommunicationLogDataPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<CommunicationLogResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCommunicationLog(patientId).then((result) => {
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
    { label: "Log count", value: String(data.total) },
    { label: "On-call notes", value: String(data.counts_by_type["On-Call Note"] || 0) },
    { label: "Phone calls", value: String(data.counts_by_type["Phone Call"] || 0) },
    { label: "Bereavement notes", value: String(data.counts_by_type["Bereavement Note"] || 0) },
  ] : [];

  return (
    <PatientModuleShell
      patientId={patientId}
      patientName={data ? "Carr, V" : "Loading..."}
      disciplineLabel="Communication Log"
      title="Communication Log"
      subtitle="Capture every call, update, and note so IDG can review the patient story"
      activeSection="communication-log"
      sections={sections}
      onSelect={handleSelect}
      patientOverview={data ? {
        diagnosis: "Cross-discipline communication log",
        painSummary: `${data.total} entries ready for IDG review.`,
        primaryProvider: "Communication coordinator",
        hnpStatus: "Log current",
        lastVisit: data.entries[0]?.event_time || "—",
        disciplineHistory: data.entries.slice(0, 4).map((entry) => `${entry.event_type} — ${entry.summary}`),
        careTeam: ["RN", "MSW", "SC", "MD", "Admin", "Volunteer"],
      } : { diagnosis: "Loading...", painSummary: "Loading...", primaryProvider: "—", hnpStatus: "—", lastVisit: "—", disciplineHistory: [], careTeam: [] }}
      metrics={metrics}
    >
      {loading ? <div>Loading communication log...</div> : null}
      {data ? (
        <div style={{ display: "grid", gridTemplateColumns: "0.8fr 1.2fr", gap: 20 }}>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#f8fafc", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#f1f5f9", borderBottom: "1px solid #dfe8ee" }}>Event types</div>
            <div style={{ padding: 16, display: "flex", flexWrap: "wrap", gap: 8 }}>
              {Object.entries(data.counts_by_type).map(([type, count]) => (
                <span key={type} style={{ borderRadius: 999, padding: "6px 10px", background: "#e2e8f0", fontSize: 11, fontWeight: 800 }}>
                  {type} ({count})
                </span>
              ))}
            </div>
          </section>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#fff", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#eef7ff", borderBottom: "1px solid #dfe8ee" }}>Log entries</div>
            <div style={{ padding: 16 }}>
              {data.entries.map((entry) => (
                <div key={entry.id} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: "1px solid #edf2f7" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                    <div style={{ fontSize: 13, fontWeight: 800 }}>{entry.event_type}</div>
                    <div style={{ fontSize: 10, fontWeight: 800, color: "#0f766e" }}>{entry.status}</div>
                  </div>
                  <div style={{ fontSize: 12, color: "#475569", marginTop: 4 }}>{entry.event_time}</div>
                  <div style={{ fontSize: 12, marginTop: 6, lineHeight: 1.6 }}>{entry.summary}</div>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </PatientModuleShell>
  );
}
