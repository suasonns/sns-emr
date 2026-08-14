import PatientModuleShell from "../components/PatientModuleShell";

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
  return (
    <PatientModuleShell
      patientId="HOSP-001234"
      patientName="Carr, V"
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
        <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#f8fafc", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", fontSize: 15, fontWeight: 800, background: "#f1f5f9", borderBottom: "1px solid #dfe8ee" }}>
            Compliance work queue
          </div>
          <div style={{ padding: 16 }}>
            {complianceItems.map((item) => (
              <div key={item.label} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: "1px solid #edf2f7" }}>
                <div style={{ fontSize: 13, fontWeight: 800 }}>{item.label}</div>
                <div style={{ fontSize: 12, color: "#475569", marginTop: 6, lineHeight: 1.5 }}>{item.detail}</div>
              </div>
            ))}
          </div>
        </section>

        <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#fff", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", fontSize: 15, fontWeight: 800, background: "#eef7ff", borderBottom: "1px solid #dfe8ee" }}>
            Reporting notes
          </div>
          <div style={{ padding: 16, fontSize: 13, color: "#0f172a", lineHeight: 1.7 }}>
            This screen should keep the patient compliant with hospice reporting obligations, including HOPE transmission,
            LCD verification, QIES export readiness, and discharge/decline tracking for the quality team.
          </div>
        </section>
      </div>
    </PatientModuleShell>
  );
}
