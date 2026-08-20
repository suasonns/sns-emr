import { useEffect, useState } from "react";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchPatientSummary } from "../api/patientCharts";
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
  { key: "lcd-eligibility", label: "LCD Eligibility" },
  { key: "incident-occurrence", label: "Incident / Occurrence" },
  { key: "documents", label: "Documents" },
  { key: "communication-log", label: "Communication Log" },
  { key: "care-team", label: "Care Team" },
];

const patientOverview = {
  diagnosis: "Compliance and quality reporting",
  painSummary: "LCD eligibility, HOPE, QIES, and discharge reporting are tracked here.",
  primaryProvider: "Compliance lead",
  hnpStatus: "Submission queue active",
  lastVisit: "Latest rule check today",
  disciplineHistory: [
    "LCD eligibility verified",
    "HOPE admission and follow-up submissions queued",
    "QIES workflow checked",
    "Discharge and decline reporting reviewed",
  ],
  careTeam: ["Compliance", "RN", "Admin", "MD"],
};

const CLINICAL_BRAND = {
  navy: "#1E3A5F",
  teal: "#0D9488",
  tealDark: "#0F766E",
  tealLight: "#CCFBF1",
  bg: "#F8FAFC",
  canvas: "#EEF3F8",
  panel: "#FFFFFF",
  line: "#D8E3E8",
  text: "#0F172A",
  muted: "#64748B",
};

const metrics = [
  { label: "LCD status", value: "Eligible", tone: "good" as const },
  { label: "HOPE", value: "Ready", tone: "good" as const },
  { label: "QIES", value: "Pending export", tone: "warn" as const },
  { label: "Open issues", value: "0", tone: "good" as const },
];

const complianceItems = [
  { label: "LCD Eligibility", detail: "Diagnosis and trajectory reviewed against registry." },
  { label: "HOPE - Admission", detail: "Admission submission prepared for transmission." },
  { label: "HOPE - HV1", detail: "First follow-up visit data ready." },
  { label: "HOPE - HV2", detail: "Second follow-up visit data ready." },
  { label: "HOPE - Discharge", detail: "Discharge event marked for export." },
  { label: "Decline of Status", detail: "Clinical decline documented for review." },
];

export default function CompliancePage() {
  const patientId = getActivePatientId() ?? "";
  const [patientName, setPatientName] = useState("Loading patient...");

  useEffect(() => {
    if (!patientId) {
      setPatientName("No patient selected");
      return;
    }

    fetchPatientSummary(patientId)
      .then((result) => setPatientName(result.patient.full_name || "Patient"))
      .catch(() => setPatientName("Patient"));
  }, [patientId]);

  return (
    <PatientModuleShell
      patientId={patientId}
      patientName={patientName}
      disciplineLabel="Compliance"
      title="Compliance"
      subtitle="LCD, HOPE, QIES, discharge, and decline-of-status workflow"
      activeSection="compliance"
      sections={sections}
      onSelect={() => undefined}
      patientOverview={patientOverview}
      metrics={metrics}
    >
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <section style={{ border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 12, background: CLINICAL_BRAND.bg, overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", fontSize: 15, fontWeight: 800, background: "linear-gradient(90deg, rgba(30,58,95,0.12), rgba(13,148,136,0.08))", borderBottom: `1px solid ${CLINICAL_BRAND.line}`, color: CLINICAL_BRAND.text }}>
            Compliance work queue
          </div>
          <div style={{ padding: 16 }}>
            {complianceItems.map((item) => (
              <div key={item.label} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: `1px solid ${CLINICAL_BRAND.line}` }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: CLINICAL_BRAND.text }}>{item.label}</div>
                <div style={{ fontSize: 12, color: CLINICAL_BRAND.muted, marginTop: 6, lineHeight: 1.5 }}>{item.detail}</div>
              </div>
            ))}
          </div>
        </section>

        <section style={{ border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 12, background: CLINICAL_BRAND.panel, overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", fontSize: 15, fontWeight: 800, background: "linear-gradient(90deg, rgba(30,58,95,0.10), rgba(13,148,136,0.08))", borderBottom: `1px solid ${CLINICAL_BRAND.line}`, color: CLINICAL_BRAND.text }}>
            Reporting notes
          </div>
          <div style={{ padding: 16, fontSize: 13, color: CLINICAL_BRAND.text, lineHeight: 1.7 }}>
            This screen should keep the patient compliant with hospice reporting obligations, including HOPE transmission,
            LCD verification, QIES export readiness, and discharge/decline tracking for the quality team.
          </div>
        </section>
      </div>
    </PatientModuleShell>
  );
}
