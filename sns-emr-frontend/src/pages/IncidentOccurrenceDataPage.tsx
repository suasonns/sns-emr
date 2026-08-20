import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchIncidentOccurrence, fetchPatientSummary, type IncidentOccurrenceResponse } from "../api/patientCharts";

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
  borderStrong: "#C7D8E5",
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
export default function IncidentOccurrenceDataPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<IncidentOccurrenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [patientName, setPatientName] = useState("Loading patient...");

  useEffect(() => {
    if (!patientId) {
      setPatientName("No patient selected");
      setLoading(false);
      return;
    }

    fetchIncidentOccurrence(patientId).then((result) => {
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
    { label: "Total incidents", value: String(data.total) },
    { label: "Falls", value: String(data.counts_by_type.Fall || 0) },
    { label: "Sentinel events", value: String(data.counts_by_type["Sentinel Event"] || 0) },
    { label: "Medication reactions", value: String(data.counts_by_type["Adverse Reaction of Meds"] || 0) },
  ] : [];

  return (
    <PatientModuleShell
      patientId={patientId}
      patientName={patientName}
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
          <section style={{ border: `1px solid ${C.border}`, borderRadius: 12, background: C.white, overflow: "hidden", boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#F1F5F9", borderBottom: `1px solid ${C.border}` }}>Incident list</div>
            <div style={{ padding: 16 }}>
              {data.items.map((item) => (
                <div key={item.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: `1px solid ${C.border}` }}>
                  <div style={{ fontSize: 13, fontWeight: 800, color: C.text }}>{item.incident_type}</div>
                  <div style={{ fontSize: 12, color: C.subtle }}>{item.incident_date} · {item.incident_severity}</div>
                  <div style={{ fontSize: 12, marginTop: 6, color: C.text }}>{item.narrative}</div>
                </div>
              ))}
            </div>
          </section>
          <section style={{ border: `1px solid ${C.border}`, borderRadius: 12, background: C.panel, overflow: "hidden", boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#EEF7FF", borderBottom: `1px solid ${C.border}` }}>Counts</div>
            <div style={{ padding: 16 }}>
              {Object.entries(data.counts_by_type).map(([key, value]) => (
                <div key={key} style={{ display: "flex", justifyContent: "space-between", marginBottom: 10, color: C.text }}>
                  <span>{key}</span><strong style={{ color: C.tealDark }}>{value}</strong>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </PatientModuleShell>
  );
}
