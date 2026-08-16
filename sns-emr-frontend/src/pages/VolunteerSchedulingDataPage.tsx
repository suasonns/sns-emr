import { useEffect, useState } from "react";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchVolunteerScheduling, type VolunteerSchedulingResponse } from "../api/patientCharts";

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
export default function VolunteerSchedulingDataPage() {
  const [data, setData] = useState<VolunteerSchedulingResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVolunteerScheduling(patientId).then((result) => {
      setData(result);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const metrics = data ? [
    { label: "Assignments", value: String(data.assignments.length) },
    { label: "Visit slots", value: String(data.visits.length) },
    { label: "Task slots", value: String(data.task_slots.length) },
    { label: "Volunteer coordinator", value: data.assignments[0]?.staff_name || "Unassigned" },
  ] : [];

  return (
    <PatientModuleShell
      patientId={patientId}
      patientName={data ? "Carr, V" : "Loading..."}
      disciplineLabel="Volunteer Scheduling"
      title="Volunteer Assignment Scheduling"
      subtitle="Plot visits in the calendar and assign or self-schedule volunteers"
      activeSection="visit-calendar"
      sections={sections}
      onSelect={() => undefined}
      patientOverview={data ? {
        diagnosis: "Volunteer assignment and visit plotting",
        painSummary: `${data.assignments.length} volunteer assignment(s) and ${data.visits.length} visit slot(s).`,
        primaryProvider: "Volunteer coordinator",
        hnpStatus: "Calendar current",
        lastVisit: data.visits[0]?.visit_datetime || "—",
        disciplineHistory: data.task_slots.slice(0, 4).map((task) => `${task.task_type} — ${task.status}`),
        careTeam: ["Volunteer", "Admin", "RN", "MSW", "Chaplain"],
      } : { diagnosis: "Loading...", painSummary: "Loading...", primaryProvider: "—", hnpStatus: "—", lastVisit: "—", disciplineHistory: [], careTeam: [] }}
      metrics={metrics}
    >
      {loading ? <div>Loading volunteer schedule...</div> : null}
      {data ? (
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 20 }}>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#f8fafc", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#f1f5f9", borderBottom: "1px solid #dfe8ee" }}>Calendar view</div>
            <div style={{ padding: 16 }}>
              {data.visits.map((visit) => (
                <div key={visit.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid #edf2f7" }}>
                  <div style={{ fontSize: 13, fontWeight: 800 }}>{visit.visit_type}</div>
                  <div style={{ fontSize: 12, color: "#475569" }}>{visit.visit_datetime}</div>
                  <div style={{ fontSize: 11, color: "#0f766e", fontWeight: 700 }}>{visit.provider_name} · {visit.status}</div>
                </div>
              ))}
            </div>
          </section>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#fff", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#eef7ff", borderBottom: "1px solid #dfe8ee" }}>Assignments</div>
            <div style={{ padding: 16 }}>
              {data.assignments.map((assignment) => (
                <div key={assignment.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid #edf2f7" }}>
                  <div style={{ fontSize: 13, fontWeight: 800 }}>{assignment.staff_name}</div>
                  <div style={{ fontSize: 12, color: "#475569" }}>{assignment.discipline}{assignment.primary ? " · Primary" : ""}</div>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </PatientModuleShell>
  );
}
