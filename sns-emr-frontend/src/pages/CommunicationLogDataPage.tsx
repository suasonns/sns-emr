import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchCommunicationLog, fetchPatientSummary, type CommunicationLogResponse } from "../api/patientCharts";

import { getActivePatientId } from "../utils/activePatient";

const C = {
  navy: "#1E3A5F",
  teal: "#0D9488",
  tealDark: "#0F766E",
  tealLight: "#CCFBF1",
  white: "#FFFFFF",
  bg: "#EEF3F8",
  panel: "#F8FBFD",
  border: "#DDE9F2",
  text: "#1F2937",
  muted: "#64748B",
  subtle: "#475569",
};

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
  const [patientName, setPatientName] = useState("Loading patient...");

  useEffect(() => {
    if (!patientId) {
      setPatientName("No patient selected");
      setLoading(false);
      return;
    }

    fetchCommunicationLog(patientId).then((result) => {
      setData(result);
      setLoading(false);
    }).catch(() => setLoading(false));

    fetchPatientSummary(patientId)
      .then((result) => setPatientName(result.patient.full_name || "Patient"))
      .catch(() => setPatientName("Patient"));
  }, [patientId]);

  const handleSelect = (section: string) => {
    const routes: Record<string, string> = {
      overview: "/care-overview",
      admission: "/rnica",
      assessment: "/rnica",
      "nursing-assessment": "/rnica",
      psychosocial: "/msw-ica",
      "psychosocial-assessment": "/msw-ica",
      spiritual: "/sc-ica",
      "spiritual-assessment": "/sc-ica",
      physician: "/physician",
      "visit-calendar": "/care-overview",
      "tx-meds-dme-supplies": "/care-overview",
      idg: "/care-overview",
      "plan-of-care": "/plan-of-care",
      bereavement: "/bereavement",
      compliance: "/compliance",
      "lcd-eligibility": "/patient-lcd",
      "incident-occurrence": "/incident-occurrence",
      documents: "/communication-log",
      "communication-log": "/communication-log",
      "care-team": "/care-overview",
    };

    const target = routes[section];
    if (!target) return;
    navigate(`${target}${patientId ? `?patientId=${encodeURIComponent(patientId)}` : ""}`);
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
      patientName={patientName}
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
          <section style={{ border: `1px solid ${C.border}`, borderRadius: 12, background: C.panel, overflow: "hidden", boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#F1F5F9", borderBottom: `1px solid ${C.border}` }}>Event types</div>
            <div style={{ padding: 16, display: "flex", flexWrap: "wrap", gap: 8 }}>
              {Object.entries(data.counts_by_type).map(([type, count]) => (
                <span key={type} style={{ borderRadius: 999, padding: "6px 10px", background: "#E2E8F0", fontSize: 11, fontWeight: 800, color: C.text }}>
                  {type} ({count})
                </span>
              ))}
            </div>
          </section>
          <section style={{ border: `1px solid ${C.border}`, borderRadius: 12, background: C.white, overflow: "hidden", boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#EEF7FF", borderBottom: `1px solid ${C.border}` }}>Log entries</div>
            <div style={{ padding: 16 }}>
              {data.entries.map((entry) => (
                <div key={entry.id} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: `1px solid ${C.border}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: C.text }}>{entry.event_type}</div>
                    <div style={{ fontSize: 10, fontWeight: 800, color: C.tealDark }}>{entry.status}</div>
                  </div>
                  <div style={{ fontSize: 12, color: C.subtle, marginTop: 4 }}>{entry.event_time}</div>
                  <div style={{ fontSize: 12, marginTop: 6, lineHeight: 1.6, color: C.text }}>{entry.summary}</div>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </PatientModuleShell>
  );
}
