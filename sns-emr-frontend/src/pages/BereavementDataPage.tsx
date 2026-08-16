import { useEffect, useState } from "react";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchBereavement, type BereavementResponse } from "../api/patientCharts";

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
export default function BereavementDataPage() {
  const [data, setData] = useState<BereavementResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBereavement(patientId).then((result) => {
      setData(result);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const metrics = data ? [
    { label: "RN present", value: data.aggregation.rn_present ? "Yes" : "No", tone: data.aggregation.rn_present ? "good" as const : "warn" as const },
    { label: "MSW present", value: data.aggregation.sw_present ? "Yes" : "No", tone: data.aggregation.sw_present ? "good" as const : "warn" as const },
    { label: "Chaplain present", value: data.aggregation.chaplain_present ? "Yes" : "No", tone: data.aggregation.chaplain_present ? "good" as const : "warn" as const },
    { label: "Source notes", value: String(data.aggregation.source_notes.length), tone: "default" as const },
  ] : [];

  return (
    <PatientModuleShell
      patientId={patientId}
      patientName={data?.patient.full_name || "Loading..."}
      disciplineLabel="Bereavement"
      title="Bereavement"
      subtitle="Assessment, support plan, follow-up schedule, and grief-risk monitoring"
      activeSection="bereavement"
      sections={sections}
      onSelect={() => undefined}
      patientOverview={data ? {
        diagnosis: data.patient.primary_diagnosis,
        painSummary: `${data.supporting_communications.length} bereavement-related communication entries.`,
        primaryProvider: "Bereavement coordinator",
        hnpStatus: "Family support plan active",
        lastVisit: data.supporting_notes[0]?.created_at || "—",
        disciplineHistory: data.supporting_notes.slice(0, 4).map((n) => `${n.form_key || "Note"} — ${n.created_at || ""}`),
        careTeam: ["Bereavement", "MSW", "Chaplain", "RN", "Admin"],
      } : { diagnosis: "Loading...", painSummary: "Loading...", primaryProvider: "—", hnpStatus: "—", lastVisit: "—", disciplineHistory: [], careTeam: [] }}
      metrics={metrics}
    >
      {loading ? <div>Loading bereavement data...</div> : null}
      {data ? (
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 20 }}>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#f8fafc", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#f1f5f9", borderBottom: "1px solid #dfe8ee" }}>Supporting notes</div>
            <div style={{ padding: 16 }}>
              {data.supporting_notes.map((note) => (
                <div key={note.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid #edf2f7" }}>
                  <div style={{ fontSize: 13, fontWeight: 800 }}>{note.form_key || "Note"}</div>
                  <div style={{ fontSize: 12, color: "#475569" }}>{note.created_at}</div>
                  <div style={{ fontSize: 12, marginTop: 6 }}>{note.content}</div>
                </div>
              ))}
            </div>
          </section>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#fff", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#eef7ff", borderBottom: "1px solid #dfe8ee" }}>Support calls</div>
            <div style={{ padding: 16 }}>
              {data.supporting_communications.map((entry) => (
                <div key={entry.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid #edf2f7" }}>
                  <div style={{ fontSize: 13, fontWeight: 800 }}>{entry.event_type}</div>
                  <div style={{ fontSize: 12, color: "#475569" }}>{entry.event_time}</div>
                  <div style={{ fontSize: 12, marginTop: 6 }}>{entry.summary}</div>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </PatientModuleShell>
  );
}
