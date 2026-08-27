import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchPatientSummary, type PatientSummaryResponse } from "../api/patientCharts";
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

function formatVisitParts(value: string | null | undefined) {
  if (!value) {
    return {
      day: "Date unavailable",
      time: "Time unavailable",
    };
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return {
      day: value,
      time: "Time unavailable",
    };
  }

  return {
    day: parsed.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" }),
    time: parsed.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }),
  };
}

function buildVisitList(summary: PatientSummaryResponse | null) {
  return (summary?.recent_visits || []).map((visit) => {
    const parts = formatVisitParts(visit.visit_datetime);
    return {
      id: visit.id,
      day: parts.day,
      time: parts.time,
      staff: visit.provider_name || "Provider unavailable",
      type: visit.visit_type || "Visit",
      discipline: visit.discipline || "Discipline unavailable",
      status: visit.status || "Recorded",
    };
  });
}

function buildClinicalReadiness(summary: PatientSummaryResponse | null) {
  if (!summary) return [];

  const openIssues = summary.compliance_summary?.open_issues?.length || 0;
  const recentVisits = summary.recent_visits?.length || 0;
  const careTeamAssignments = summary.care_team?.length || 0;
  const communications = summary.communication_summary?.total || 0;
  const incidents = summary.incident_summary?.total || 0;

  return [
    {
      label: summary.patient?.status ? `Patient status: ${summary.patient.status}` : "Patient status not available",
      tone: "neutral",
    },
    {
      label: recentVisits ? `${recentVisits} recent visit record(s) on chart` : "No visits recorded yet",
      tone: recentVisits ? "positive" : "warning",
    },
    {
      label: openIssues ? `${openIssues} open compliance issue(s)` : "No open compliance issues in chart summary",
      tone: openIssues ? "warning" : "positive",
    },
    {
      label: communications ? `${communications} communication log entr${communications === 1 ? "y" : "ies"}` : "No communication log entries in chart summary",
      tone: "neutral",
    },
    {
      label: careTeamAssignments ? `${careTeamAssignments} care team assignment(s) on file` : "No care team assignments on file",
      tone: careTeamAssignments ? "positive" : "warning",
    },
    {
      label: incidents ? `${incidents} incident report(s) on file` : "No incident reports in chart summary",
      tone: incidents ? "warning" : "positive",
    },
  ];
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
  const [summary, setSummary] = useState<PatientSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const recentVisits = useMemo(() => buildVisitList(summary), [summary]);
  const readinessItems = useMemo(() => buildClinicalReadiness(summary), [summary]);

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
    const clinician = summary?.care_team?.find((person) => person.primary)?.staff_name || "Provider not assigned";
    const latestCommunication = summary?.communication_summary?.latest?.[0];

    return {
      diagnosis: patient?.primary_diagnosis || "No diagnosis on file",
      painSummary: latestCommunication ? latestCommunication.summary : "No recent communication summary available.",
      primaryProvider: clinician,
      hnpStatus: patient?.status || "No status on file",
      lastVisit: latestVisit ? formatDate(latestVisit.visit_datetime) : "No recent visit recorded",
      disciplineHistory: summary?.care_team?.map((member) => `${member.discipline || "Care team"} — ${member.staff_name || "Unassigned"}`) || ["No care team data"],
      careTeam: summary?.care_team?.map((member) => member.discipline || "Care team") || ["Care team"],
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
            Recent / upcoming visits
          </div>
          <div style={{ padding: 16 }}>
            {recentVisits.length ? (
              <div style={{ display: "grid", gap: 10 }}>
                {recentVisits.map((item) => (
                  <div key={item.id} style={{ border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 10, background: CLINICAL_BRAND.panel, padding: 12, boxShadow: "0 8px 18px rgba(15, 23, 42, 0.03)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                      <div>
                        <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em", color: CLINICAL_BRAND.muted }}>{item.day}</div>
                        <div style={{ marginTop: 6, fontSize: 13, fontWeight: 800, color: CLINICAL_BRAND.text }}>{item.time}</div>
                        <div style={{ marginTop: 6, fontSize: 12, color: CLINICAL_BRAND.text }}>{item.type}</div>
                        <div style={{ marginTop: 4, fontSize: 11, color: CLINICAL_BRAND.muted }}>
                          {item.discipline} · {item.staff}
                        </div>
                      </div>
                      <div
                        style={{
                          display: "inline-flex",
                          padding: "4px 8px",
                          borderRadius: 999,
                          background: item.status.toLowerCase() === "completed" ? "#dcfce7" : item.status.toLowerCase() === "scheduled" ? "#E0F2FE" : "#FEF3C7",
                          color: item.status.toLowerCase() === "completed" ? "#166534" : item.status.toLowerCase() === "scheduled" ? CLINICAL_BRAND.tealDark : "#92400e",
                          fontSize: 10,
                          fontWeight: 800,
                          textTransform: "uppercase",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {item.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ border: `1px dashed ${CLINICAL_BRAND.line}`, borderRadius: 10, background: CLINICAL_BRAND.panel, padding: 18, color: CLINICAL_BRAND.muted, fontSize: 13 }}>
                No visits recorded yet.
              </div>
            )}
          </div>
        </section>

        <section style={{ border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 12, overflow: "hidden", background: CLINICAL_BRAND.bg }}>
          <div style={{ background: "linear-gradient(90deg, rgba(30,58,95,0.12), rgba(13,148,136,0.08))", borderBottom: `1px solid ${CLINICAL_BRAND.line}`, padding: "12px 16px", fontSize: 15, fontWeight: 800, color: CLINICAL_BRAND.text }}>
            Clinical readiness
          </div>
          <div style={{ padding: 16 }}>
            {readinessItems.map((item) => (
              <div key={item.label} style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
                <span
                  style={{
                    width: 18,
                    height: 18,
                    borderRadius: 999,
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: item.tone === "positive" ? "#dcfce7" : item.tone === "warning" ? "#FEF3C7" : "#E2E8F0",
                    color: item.tone === "positive" ? "#166534" : item.tone === "warning" ? "#92400e" : "#475569",
                    fontSize: 12,
                    fontWeight: 900,
                  }}
                >
                  {item.tone === "warning" ? "!" : "•"}
                </span>
                <span style={{ fontSize: 13, color: CLINICAL_BRAND.text }}>{item.label}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </PatientModuleShell>
  );
}
