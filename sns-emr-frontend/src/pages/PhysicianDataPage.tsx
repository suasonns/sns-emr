import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import PatientModuleShell from "../components/PatientModuleShell";
import { fetchPhysicianSummary, type PhysicianSummaryResponse } from "../api/patientCharts";

import { getActivePatientId } from "../utils/activePatient";
const sections = [
  { key: "overview", label: "Care Overview" },
  { key: "physician", label: "Physician" },
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

const patientId = getActivePatientId() ?? "";
export default function PhysicianDataPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<PhysicianSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPhysicianSummary(patientId)
      .then((result) => {
        setData(result);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const metrics = data
    ? data.metrics.map((metric) => ({ label: metric.label, value: String(metric.value) }))
    : [];

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

  return (
    <PatientModuleShell
      patientId={patientId}
      patientName={data?.patient.full_name || "Loading..."}
      disciplineLabel="Physician"
      title="Physician"
      subtitle="CTI / certification and face-to-face attestation workspace"
      activeSection="physician"
      sections={sections}
      onSelect={handleSelect}
      patientOverview={
        data
          ? {
              diagnosis: data.patient.primary_diagnosis,
              painSummary: `${data.cti.length} CTI item(s) and ${data.f2f.length} F2F encounter(s).`,
              primaryProvider: "Attending physician",
              hnpStatus: "Physician workflow active",
              lastVisit: data.f2f[0]?.encounter_date || "—",
              disciplineHistory: [
                ...data.cti.slice(0, 2).map((row) => `${row.cert_type} — ${row.status}`),
                ...data.f2f.slice(0, 2).map((row) => `F2F — ${row.status}`),
              ],
              careTeam: ["MD", "NP", "RN", "Compliance"],
            }
          : {
              diagnosis: "Loading...",
              painSummary: "Loading...",
              primaryProvider: "—",
              hnpStatus: "—",
              lastVisit: "—",
              disciplineHistory: [],
              careTeam: [],
            }
      }
      metrics={metrics}
    >
      {loading ? <div>Loading physician data...</div> : null}
      {data ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#f8fafc", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#f1f5f9", borderBottom: "1px solid #dfe8ee" }}>
              CTI / Certification
            </div>
            <div style={{ padding: 16 }}>
              {data.cti.length ? (
                data.cti.map((row) => (
                  <div key={row.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid #edf2f7" }}>
                    <div style={{ fontSize: 13, fontWeight: 800 }}>{row.cert_type}</div>
                    <div style={{ fontSize: 12, color: "#475569" }}>{row.signed_at} · {row.signed_by_role}</div>
                    <div style={{ fontSize: 12, marginTop: 6 }}>{row.status}</div>
                  </div>
                ))
              ) : (
                <div>No CTI / certification records loaded.</div>
              )}
            </div>
          </section>

          <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#fff", overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", fontWeight: 800, background: "#eef7ff", borderBottom: "1px solid #dfe8ee" }}>
              F2F / Attestation
            </div>
            <div style={{ padding: 16 }}>
              {data.f2f.length ? (
                data.f2f.map((row) => (
                  <div key={row.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid #edf2f7" }}>
                    <div style={{ fontSize: 13, fontWeight: 800 }}>{row.encounter_date}</div>
                    <div style={{ fontSize: 12, color: "#475569" }}>{row.performed_by_role} · {row.status}</div>
                    <div style={{ fontSize: 12, marginTop: 6 }}>{row.summary || row.clinical_decline_summary || "No narrative recorded."}</div>
                  </div>
                ))
              ) : (
                <div>No F2F encounters loaded.</div>
              )}
            </div>
          </section>
        </div>
      ) : null}
    </PatientModuleShell>
  );
}
