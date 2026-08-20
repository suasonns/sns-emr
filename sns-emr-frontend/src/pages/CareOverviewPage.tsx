import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchPatientSummary } from "../api/patientCharts";
import { fetchCensusWorkspace } from "../api/census";
import { getActivePatientId, setActivePatientId } from "../utils/activePatient";

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

function buildScheduleFromOrders(summary: any) {
  const orderSummary = [
    summary?.patient?.order_summary,
    summary?.patient?.orders_text,
    summary?.patient?.ordersSummary,
    summary?.patient?.visit_plan,
    summary?.order_summary,
    summary?.orders_summary,
  ].filter(Boolean).join(" \n ");

  const normalized = (orderSummary || "").toLowerCase();
  const hasSnOrder = /skilled nursing|lvn|rn.*visit|sn.*visit/.test(normalized);
  const hasAideOrder = /hospice aide|chha|home aide/.test(normalized);
  const hasMswOrder = /msw.*visit|medical social worker|psychosocial/.test(normalized);
  const hasScOrder = /sc.*visit|spiritual counselor|chaplain|spiritual/.test(normalized);

  const defaultSchedule = [
    { day: "Mon", time: "9:00 AM", staff: "RN", type: "RN Visit", status: "Scheduled" },
    { day: "Mon", time: "11:00 AM", staff: "LVN", type: "Skilled Nursing", status: "Scheduled" },
    { day: "Tue", time: "8:30 AM", staff: "MSW", type: "Psychosocial", status: "Confirmed" },
    { day: "Tue", time: "1:00 PM", staff: "SC", type: "Spiritual Support", status: "Scheduled" },
    { day: "Wed", time: "10:15 AM", staff: "RN", type: "Wound/Medication", status: "Scheduled" },
    { day: "Thu", time: "9:45 AM", staff: "CHHA", type: "Home Aide Care", status: "Confirmed" },
    { day: "Fri", time: "12:00 PM", staff: "LVN", type: "Medication Review", status: "Scheduled" },
    { day: "Sat", time: "1:30 PM", staff: "CHHA", type: "Hygiene / Personal Care", status: "Scheduled" },
  ];

  if (!orderSummary) return defaultSchedule;

  const schedule = [...defaultSchedule];
  if (hasSnOrder) {
    schedule.push({ day: "Tue", time: "2:00 PM", staff: "LVN", type: "Skilled Nursing Follow-up", status: "Scheduled" });
  }
  if (hasAideOrder) {
    schedule.push({ day: "Thu", time: "3:00 PM", staff: "CHHA", type: "Aide Visit", status: "Scheduled" });
  }
  if (hasMswOrder) {
    schedule.push({ day: "Fri", time: "9:00 AM", staff: "MSW", type: "Caregiver Check-in", status: "Confirmed" });
  }
  if (hasScOrder) {
    schedule.push({ day: "Sun", time: "10:00 AM", staff: "SC", type: "Spiritual Support", status: "Scheduled" });
  }
  return schedule;
}

function formatDate(value: string | null | undefined) {
  if (!value) return "No recent visit recorded";
  try {
    return new Date(value).toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  } catch {
    return value;
  }
}

export default function CareOverviewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const schedule = useMemo(() => buildScheduleFromOrders(summary), [summary]);

  const patientId = new URLSearchParams(location.search).get("patientId") || getActivePatientId() || "";
  const selectedSection = new URLSearchParams(location.search).get("section") || "overview";
  const displayMrn = summary?.patient?.mrn || (patientId ? "Loading MRN..." : "No patient selected");

  useEffect(() => {
    if (!patientId) {
      let mounted = true;
      fetchCensusWorkspace()
        .then(({ patients }) => {
          if (!mounted) return;
          const firstPatient = patients?.[0];
          if (!firstPatient?.patient_id) {
            setSummary(null);
            setLoading(false);
            return;
          }
          setActivePatientId(firstPatient.patient_id);
          navigate(`${location.pathname}?patientId=${encodeURIComponent(firstPatient.patient_id)}`, { replace: true });
        })
        .catch(() => {
          if (mounted) {
            setSummary(null);
            setLoading(false);
          }
        });

      return () => {
        mounted = false;
      };
    }

    if (!patientId) {
      setSummary(null);
      setLoading(false);
      return;
    }

    let mounted = true;
    fetchPatientSummary(patientId)
      .then((result) => {
        if (mounted) setSummary(result);
      })
      .catch(() => {
        if (mounted) setSummary(null);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [patientId, location.pathname, navigate]);

  const patientOverview = useMemo(() => {
    const patient = summary?.patient;
    const latestVisit = summary?.recent_visits?.[0];
    const clinician = summary?.care_team?.find((person: any) => person.primary)?.staff_name || "Provider not assigned";
    const latestCommunication = summary?.communication_summary?.latest?.[0];

    return {
      diagnosis: patient?.primary_diagnosis || "No diagnosis on file",
      painSummary: latestCommunication ? latestCommunication.summary : "No recent communication summary available.",
      primaryProvider: clinician,
      hnpStatus: patient?.status || "No status on file",
      lastVisit: latestVisit ? formatDate(latestVisit.visit_datetime) : "No recent visit recorded",
      disciplineHistory: summary?.care_team?.map((member: any) => `${member.discipline || "Care team"} — ${member.staff_name || "Unassigned"}`) || ["No care team data"],
      careTeam: summary?.care_team?.map((member: any) => member.discipline || "Care team") || ["Care team"],
    };
  }, [summary]);

  const metrics = useMemo(() => {
    const patient = summary?.patient;
    return [
      { label: "Care status", value: patient?.status || "Not loaded" },
      { label: "Level of care", value: patient?.admission_status || "Pending" },
      { label: "Primary diagnosis", value: patient?.primary_diagnosis || "—" },
      { label: "SOC", value: patient?.soc_date ? new Date(patient.soc_date).toLocaleDateString() : "—" },
      { label: "Recent visits", value: String(summary?.recent_visits?.length || 0) },
      { label: "Open issues", value: String(summary?.compliance_summary?.open_issues?.length || 0) },
    ];
  }, [summary]);

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
      "visit-calendar": "/care-overview",
      "tx-meds-dme-supplies": "/care-overview",
      idg: "/care-overview",
      "plan-of-care": "/plan-of-care",
      bereavement: "/bereavement",
      compliance: "/compliance",
      physician: "/physician",
      "lcd-eligibility": "/patient-lcd",
      "incident-occurrence": "/incident-occurrence",
      documents: "/communication-log",
      "communication-log": "/communication-log",
      "care-team": "/care-overview",
    };

    const target = routes[section];
    if (!target) return;
    const search = new URLSearchParams();
    if (patientId) search.set("patientId", patientId);
    if (section === "visit-calendar") search.set("section", "visit-calendar");
    if (section === "overview") search.set("section", "overview");
    navigate(`${target}${search.toString() ? `?${search.toString()}` : ""}`);
  };

  return (
    <PatientModuleShell
      patientId={patientId}
      mrn={displayMrn}
      patientName={summary?.patient?.full_name || (loading ? "Loading patient..." : "No patient selected")}
      disciplineLabel="Care Overview"
      title="Care Overview"
      subtitle="Shared patient chart, visit calendar, and cross-discipline readiness"
      activeSection={selectedSection}
      sections={sections}
      onSelect={handleSelect}
      patientOverview={patientOverview}
      metrics={metrics}
    >
      {!patientId && !loading ? (
        <div style={{ padding: 20, color: "#475569", fontSize: 14 }}>Choose a patient from the census to open the chart.</div>
      ) : null}

      <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 20 }}>
        <section style={{ border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 12, overflow: "hidden", background: CLINICAL_BRAND.bg }}>
          <div style={{ background: "linear-gradient(90deg, rgba(30,58,95,0.10), rgba(13,148,136,0.08))", borderBottom: `1px solid ${CLINICAL_BRAND.line}`, padding: "12px 16px", fontSize: 15, fontWeight: 800, color: CLINICAL_BRAND.text }}>
            Visit calendar / staffing view
          </div>
          <div style={{ padding: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
              {schedule.map((item) => (
                <div key={`${item.day}-${item.time}`} style={{ border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 10, background: CLINICAL_BRAND.panel, padding: 10, boxShadow: "0 8px 18px rgba(15, 23, 42, 0.03)" }}>
                  <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em", color: CLINICAL_BRAND.muted }}>{item.day}</div>
                  <div style={{ marginTop: 8, fontSize: 13, fontWeight: 800, color: CLINICAL_BRAND.text }}>{item.time}</div>
                  <div style={{ marginTop: 6, fontSize: 12, color: CLINICAL_BRAND.text }}>{item.staff}</div>
                  <div style={{ marginTop: 4, fontSize: 11, color: CLINICAL_BRAND.tealDark, fontWeight: 700 }}>{item.type}</div>
                  <div
                    style={{
                      marginTop: 8,
                      display: "inline-flex",
                      padding: "4px 8px",
                      borderRadius: 999,
                      background: item.status === "Confirmed" ? "#dcfce7" : item.status === "Scheduled" ? "#E0F2FE" : "#FEF3C7",
                      color: item.status === "Confirmed" ? "#166534" : item.status === "Scheduled" ? CLINICAL_BRAND.tealDark : "#92400e",
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

        <section style={{ border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 12, overflow: "hidden", background: CLINICAL_BRAND.bg }}>
          <div style={{ background: "linear-gradient(90deg, rgba(30,58,95,0.12), rgba(13,148,136,0.08))", borderBottom: `1px solid ${CLINICAL_BRAND.line}`, padding: "12px 16px", fontSize: 15, fontWeight: 800, color: CLINICAL_BRAND.text }}>
            Clinical readiness
          </div>
          <div style={{ padding: 16 }}>
            {[
              "HNP reviewed and current",
              "POC update pending physician review",
              "LCD eligibility active",
              "QIES/HOPE submission ready",
              "Communication log reviewed",
              "Bereavement support call scheduled",
              "Incident reporting closed",
            ].map((item) => (
              <div key={item} style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
                <span style={{ width: 18, height: 18, borderRadius: 999, display: "inline-flex", alignItems: "center", justifyContent: "center", background: "#dcfce7", color: "#166534", fontSize: 12, fontWeight: 900 }}>
                  ✓
                </span>
                <span style={{ fontSize: 13, color: CLINICAL_BRAND.text }}>{item}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </PatientModuleShell>
  );
}
