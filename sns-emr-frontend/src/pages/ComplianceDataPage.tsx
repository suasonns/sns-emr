import { useEffect, useState } from "react";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchCompliance, type ComplianceResponse } from "../api/patientCharts";

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
export default function ComplianceDataPage() {
  const [data, setData] = useState<ComplianceResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCompliance(patientId).then((result) => {
      setData(result);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const metrics = data ? [
    { label: "LCD", value: data.eligibility["eligible"] ? "Eligible" : "Review" },
    { label: "HOPE", value: data.hope_status },
    { label: "QIES", value: data.qies_status },
    { label: "Open issues", value: String(data.open_issues.length) },
  ] : [];

  return (
    <PatientModuleShell
      patientId={patientId}
      patientName={data ? "Carr, V" : "Loading..."}
      disciplineLabel="Compliance"
      title="Compliance"
      subtitle="LCD, HOPE, QIES, discharge, and decline-of-status workflow"
      activeSection="compliance"
      sections={sections}
      onSelect={() => undefined}
      patientOverview={data ? {
        diagnosis: data.patient.primary_diagnosis,
        painSummary: `${data.task_counts.pending} pending task(s) and ${data.note_counts.total} note(s).`,
        primaryProvider: "Compliance lead",
        hnpStatus: "Submission queue active",
        lastVisit: data.recent_notes[0]?.created_at || "—",
        disciplineHistory: data.open_issues.length ? data.open_issues : ["No open issues"],
        careTeam: ["Compliance", "RN", "Admin", "MD"],
      } : { diagnosis: "Loading...", painSummary: "Loading...", primaryProvider: "—", hnpStatus: "—", lastVisit: "—", disciplineHistory: [], careTeam: [] }}
      metrics={metrics}
    >
      {loading ? <div>Loading compliance data...</div> : null}
      {data ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#f8fafc", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#f1f5f9", borderBottom: "1px solid #dfe8ee" }}>Work queue</div>
            <div style={{ padding: 16 }}>
              <div>Pending tasks: {data.task_counts.pending}</div>
              <div>Overdue tasks: {data.task_counts.overdue}</div>
              <div>Completed tasks: {data.task_counts.completed}</div>
              <div style={{ marginTop: 12 }}>HOPE notes: {data.note_counts.hope}</div>
              <div>POC notes: {data.note_counts.poc}</div>
              <div>F2F notes: {data.note_counts.f2f}</div>
            </div>
          </section>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#fff", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#eef7ff", borderBottom: "1px solid #dfe8ee" }}>Open issues</div>
            <div style={{ padding: 16 }}>
              {data.open_issues.length ? data.open_issues.map((issue) => <div key={issue} style={{ marginBottom: 10 }}>• {issue}</div>) : <div>No open issues.</div>}
            </div>
          </section>
        </div>
      ) : null}
    </PatientModuleShell>
  );
}
