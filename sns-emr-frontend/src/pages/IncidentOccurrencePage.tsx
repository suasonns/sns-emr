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
  diagnosis: "Incident / occurrence tracking for patient safety and reporting",
  painSummary: "Falls, medication reactions, sentinel events, and other incidents are documented here.",
  primaryProvider: "Safety / compliance lead",
  hnpStatus: "Occurrence log active",
  lastVisit: "Most recent incident reviewed today",
  disciplineHistory: [
    "Fall event logged and categorized",
    "Narrative reviewed and signed",
    "Follow-up actions assigned",
    "IDG notified when clinically relevant",
  ],
  careTeam: ["RN", "Admin", "MD", "Compliance", "MSW"],
};

const metrics = [
  { label: "Incident type", value: "Fall", tone: "warn" as const },
  { label: "Severity", value: "Hospitalization required", tone: "bad" as const },
  { label: "Reported by", value: "Facility / staff", tone: "default" as const },
  { label: "Status", value: "Signed and closed", tone: "good" as const },
];

const eventTypes = ["Fall", "Sentinel Event", "Adverse Reaction of Meds", "Other", "Near Miss"];

export default function IncidentOccurrencePage() {
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
      disciplineLabel="Incident / Occurrence"
      title="Incident / Occurrence"
      subtitle="Classify the event, document the narrative, and assign follow-up"
      activeSection="incident-occurrence"
      sections={sections}
      onSelect={() => undefined}
      patientOverview={patientOverview}
      metrics={metrics}
    >
      <div style={{ display: "grid", gridTemplateColumns: "1fr 0.9fr", gap: 20 }}>
        <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#fff", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", fontSize: 15, fontWeight: 800, background: "#f1f5f9", borderBottom: "1px solid #dfe8ee" }}>
            Incident classification
          </div>
          <div style={{ padding: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 10 }}>
              {eventTypes.map((type, index) => (
                <div
                  key={type}
                  style={{
                    border: "1px solid #dfe8ee",
                    borderRadius: 10,
                    padding: 12,
                    background: index === 0 ? "#eff6ff" : "#f8fafc",
                    fontSize: 13,
                    fontWeight: 700,
                  }}
                >
                  {type}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, fontSize: 12, color: "#475569", lineHeight: 1.6 }}>
              Use this screen for falls, sentinel events, medication reactions, injuries, and other reportable occurrences.
            </div>
          </div>
        </section>

        <section style={{ border: "1px solid #dfe8ee", borderRadius: 12, background: "#f8fafc", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", fontSize: 15, fontWeight: 800, background: "#eef7ff", borderBottom: "1px solid #dfe8ee" }}>
            Required follow-up
          </div>
          <div style={{ padding: 16 }}>
            {["Immediate assessment", "Provider notification", "Family notification if needed", "IDG review", "Corrective action"].map((item) => (
              <div key={item} style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
                <span style={{ width: 18, height: 18, borderRadius: 999, background: "#dcfce7", color: "#166534", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 900 }}>✓</span>
                <span style={{ fontSize: 13, color: "#0f172a" }}>{item}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </PatientModuleShell>
  );
}
