import { useNavigate } from "react-router-dom";
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
  diagnosis: "Lung cancer (C34.90), CHF, COPD",
  painSummary: "Pain controlled with symptom review; caregiver support needs ongoing monitoring.",
  primaryProvider: "Dr. James Olsen",
  hnpStatus: "HNP current",
  lastVisit: "Last RN visit 3 days ago",
  disciplineHistory: [
    "Admission — intake and referral review",
    "Assessment — nursing, psychosocial, spiritual",
    "Tx / Meds / DME / Supplies — active orders and equipment",
    "IDG — interdisciplinary team review",
    "Plan of Care (POC) — current goals and revisions",
    "Bereavement — family support and follow-up",
    "Compliance — LCD, QIES, HOPE, incident review",
    "Communication Log — all calls and caregiver updates",
  ],
  careTeam: ["RN", "MSW", "SC", "MD", "Chaplain", "Volunteer", "Admin"],
};

const metrics = [
  { label: "Care status", value: "Stable / monitoring" },
  { label: "Level of care", value: "Routine Hospice" },
  { label: "Primary diagnosis", value: "Lung cancer (C34.90)" },
  { label: "Current focus", value: "Symptom management" },
  { label: "Next IDG", value: "Friday 2:00 PM" },
  { label: "Volunteer support", value: "2 visits this week" },
];

const schedule = [
  { day: "Mon", time: "9:00 AM", staff: "RN", type: "RN Visit", status: "Scheduled" },
  { day: "Mon", time: "11:00 AM", staff: "MSW", type: "Psychosocial", status: "Confirmed" },
  { day: "Tue", time: "8:30 AM", staff: "Chaplain", type: "Spiritual Support", status: "Scheduled" },
  { day: "Tue", time: "1:00 PM", staff: "ST", type: "PT/OT Review", status: "Pending" },
  { day: "Wed", time: "10:15 AM", staff: "RN", type: "Wound/Medication", status: "Scheduled" },
  { day: "Thu", time: "9:45 AM", staff: "MSW", type: "Caregiver Check-in", status: "Confirmed" },
  { day: "Fri", time: "12:00 PM", staff: "Admin", type: "IDG Review", status: "Scheduled" },
  { day: "Sat", time: "1:30 PM", staff: "Volunteer", type: "Companionship", status: "Requested" },
];

const checklist = [
  "HNP reviewed and current",
  "POC update pending physician review",
  "LCD eligibility active",
  "QIES/HOPE submission ready",
  "Communication log reviewed",
  "Bereavement support call scheduled",
  "Incident reporting closed",
];

export default function CareOverviewPage() {
  const navigate = useNavigate();

  const handleSelect = (section: string) => {
    const routes: Record<string, string> = {
      overview: "/care-overview",
      "visit-calendar": "/volunteer-scheduling",
      bereavement: "/bereavement",
      compliance: "/compliance",
      "lcd-eligibility": "/patient-lcd",
      "incident-occurrence": "/incident-occurrence",
      "communication-log": "/communication-log",
    };

    const target = routes[section];
    if (target) {
      navigate(target);
    }
  };

  return (
    <PatientModuleShell
      patientId="HOSP-001234"
      patientName="Carr, V"
      disciplineLabel="Care Overview"
      title="Care Overview"
      subtitle="Shared patient chart, visit calendar, and cross-discipline readiness"
      activeSection="overview"
      sections={sections}
      onSelect={handleSelect}
      patientOverview={patientOverview}
      metrics={metrics}
    >
      <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 20 }}>
        <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, overflow: "hidden", background: "#f8fafc" }}>
          <div style={{ background: "#eaf5ef", borderBottom: "1px solid #dfe8ee", padding: "12px 16px", fontSize: 15, fontWeight: 800, color: "#0f172a" }}>
            Visit calendar / staffing view
          </div>
          <div style={{ padding: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
              {schedule.map((item) => (
                <div key={`${item.day}-${item.time}`} style={{ border: "1px solid #dfe8ee", borderRadius: 10, background: "#fff", padding: 10 }}>
                  <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em", color: "#64748b" }}>{item.day}</div>
                  <div style={{ marginTop: 8, fontSize: 13, fontWeight: 800 }}>{item.time}</div>
                  <div style={{ marginTop: 6, fontSize: 12, color: "#0f172a" }}>{item.staff}</div>
                  <div style={{ marginTop: 4, fontSize: 11, color: "#0f766e", fontWeight: 700 }}>{item.type}</div>
                  <div
                    style={{
                      marginTop: 8,
                      display: "inline-flex",
                      padding: "4px 8px",
                      borderRadius: 999,
                      background: item.status === "Confirmed" ? "#dcfce7" : item.status === "Scheduled" ? "#e0f2fe" : "#fef3c7",
                      color: item.status === "Confirmed" ? "#166534" : item.status === "Scheduled" ? "#0f766e" : "#92400e",
                      fontSize: 10,
                      fontWeight: 800,
                      textTransform: "uppercase",
                    }}
                  >
                    {item.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, overflow: "hidden", background: "#f8fafc" }}>
          <div style={{ background: "#eef7ff", borderBottom: "1px solid #dfe8ee", padding: "12px 16px", fontSize: 15, fontWeight: 800, color: "#0f172a" }}>
            Clinical readiness
          </div>
          <div style={{ padding: 16 }}>
            {checklist.map((item) => (
              <div key={item} style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
                <span style={{ width: 18, height: 18, borderRadius: 999, display: "inline-flex", alignItems: "center", justifyContent: "center", background: "#dcfce7", color: "#166534", fontSize: 12, fontWeight: 900 }}>
                  ✓
                </span>
                <span style={{ fontSize: 13, color: "#0f172a" }}>{item}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </PatientModuleShell>
  );
}
