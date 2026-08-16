import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchPatientSummary, type PatientSummaryResponse } from "../api/patientCharts";

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
export default function CareOverviewDataPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<PatientSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    fetchPatientSummary(patientId)
      .then((result) => {
        if (mounted) setData(result);
      })
      .catch(() => {
        if (mounted) setError("Unable to load the patient chart summary.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const handleSelect = (section: string) => {
    const routes: Record<string, string> = {
      overview: "/care-overview",
      "visit-calendar": "/volunteer-scheduling",
      bereavement: "/bereavement",
      compliance: "/compliance",
      physician: "/physician",
      "lcd-eligibility": "/patient-lcd",
      "incident-occurrence": "/incident-occurrence",
      "communication-log": "/communication-log",
    };

    if (routes[section]) navigate(routes[section]);
  };

  const patientOverview = data
    ? {
        diagnosis: data.patient.primary_diagnosis,
        painSummary: `${data.communication_summary.total} communication entries and ${data.incident_summary.total} incident(s) on file.`,
        primaryProvider: data.care_team[0]?.staff_name || "Unassigned",
        hnpStatus: `${data.patient.admission_status} / ${data.patient.acuity_state}`,
        lastVisit: data.recent_visits[0]
          ? `Last visit ${data.recent_visits[0].visit_datetime ?? "—"}`
          : "No visits recorded",
        disciplineHistory: [
          `${data.recent_visits.length} recent visits`,
          `${data.communication_summary.total} communication log entries`,
          `${data.incident_summary.total} incident reports`,
          `${data.care_team.length} active care team assignments`,
        ],
        careTeam: data.care_team.map((item) => item.discipline),
      }
    : {
        diagnosis: "Loading patient data...",
        painSummary: "Loading chart summary.",
        primaryProvider: "—",
        hnpStatus: "—",
        lastVisit: "—",
        disciplineHistory: [],
        careTeam: [],
      };

  const metrics = data
    ? [
        { label: "Care status", value: data.patient.status },
        { label: "Level of care", value: data.patient.acuity_state },
        { label: "Primary diagnosis", value: data.patient.primary_diagnosis },
        { label: "Recent visits", value: String(data.recent_visits.length) },
        { label: "Communication log", value: String(data.communication_summary.total) },
        { label: "Incident reports", value: String(data.incident_summary.total) },
      ]
    : [];

  return (
    <PatientModuleShell
      patientId={patientId}
      patientName={data?.patient.full_name || "Loading..."}
      disciplineLabel="Care Overview"
      title="Care Overview"
      subtitle="Shared patient chart, visit calendar, and cross-discipline readiness"
      activeSection="overview"
      sections={sections}
      onSelect={handleSelect}
      patientOverview={patientOverview}
      metrics={metrics}
    >
      {loading ? <div>Loading chart summary...</div> : null}
      {error ? <div style={{ color: "#b91c1c" }}>{error}</div> : null}
      {data ? (
        <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 20 }}>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, overflow: "hidden", background: "#f8fafc" }}>
            <div style={{ background: "#eaf5ef", borderBottom: "1px solid #dfe8ee", padding: "12px 16px", fontSize: 15, fontWeight: 800 }}>
              Recent visits
            </div>
            <div style={{ padding: 16 }}>
              {data.recent_visits.map((visit) => (
                <div key={visit.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid #edf2f7" }}>
                  <div style={{ fontSize: 13, fontWeight: 800 }}>{visit.visit_type}</div>
                  <div style={{ fontSize: 12, color: "#475569" }}>{visit.visit_datetime}</div>
                  <div style={{ fontSize: 11, color: "#0f766e", fontWeight: 700 }}>{visit.provider_name}</div>
                </div>
              ))}
            </div>
          </section>

          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, overflow: "hidden", background: "#f8fafc" }}>
            <div style={{ background: "#eef7ff", borderBottom: "1px solid #dfe8ee", padding: "12px 16px", fontSize: 15, fontWeight: 800 }}>
              Care team
            </div>
            <div style={{ padding: 16 }}>
              {data.care_team.map((item) => (
                <div key={`${item.discipline}-${item.staff_name}`} style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 13, fontWeight: 800 }}>{item.staff_name}</div>
                  <div style={{ fontSize: 12, color: "#0f766e" }}>{item.discipline}{item.primary ? " · Primary" : ""}</div>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </PatientModuleShell>
  );
}
