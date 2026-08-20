import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import PatientModuleShell from "../components/PatientModuleShell";
import { fetchPatientSummary } from "../api/patientCharts";
import { getActivePatientId } from "../utils/activePatient";
import {
  getCurrentPlanOfCareByPatient,
  getPlanOfCareVersions,
  type CurrentPlanOfCare,
  type PocVersionSummary,
} from "../api/planOfCare";

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

const SEVERITY_TONE: Record<string, { bg: string; fg: string }> = {
  CRITICAL: { bg: "rgba(239, 68, 68, 0.16)", fg: "var(--sns-red)" },
  HIGH: { bg: "rgba(239, 68, 68, 0.12)", fg: "var(--sns-red)" },
  MODERATE: { bg: "rgba(245, 158, 11, 0.14)", fg: "var(--sns-orange)" },
  LOW: { bg: "rgba(16, 185, 129, 0.12)", fg: "var(--sns-green)" },
  UNKNOWN: { bg: "var(--sns-cardSoft)", fg: "var(--sns-muted)" },
};

const STATUS_TONE: Record<string, { bg: string; fg: string }> = {
  ACTIVE: { bg: "rgba(13, 148, 136, 0.16)", fg: "var(--sns-teal)" },
  IMPROVING: { bg: "rgba(16, 185, 129, 0.12)", fg: "var(--sns-green)" },
  RESOLVED: { bg: "var(--sns-cardSoft)", fg: "var(--sns-muted)" },
  HISTORICAL: { bg: "var(--sns-cardSoft)", fg: "var(--sns-muted)" },
  SUPERSEDED: { bg: "var(--sns-cardSoft)", fg: "var(--sns-muted)" },
};

function Badge({ label, bg, fg }: { label: string; bg: string; fg: string }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "2px 8px",
        borderRadius: 999,
        background: bg,
        color: fg,
        fontSize: 10,
        fontWeight: 800,
        textTransform: "uppercase",
        letterSpacing: "0.03em",
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </span>
  );
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return value;
  }
}

export default function PlanOfCarePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [summary, setSummary] = useState<any>(null);
  const [poc, setPoc] = useState<CurrentPlanOfCare | null>(null);
  const [versions, setVersions] = useState<PocVersionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);

  const patientId = new URLSearchParams(location.search).get("patientId") || getActivePatientId() || "";
  const displayMrn = summary?.patient?.mrn || (patientId ? "Loading MRN..." : "No patient selected");

  useEffect(() => {
    if (!patientId) {
      setLoading(false);
      return;
    }
    let mounted = true;
    setLoading(true);
    setNotFound(false);

    fetchPatientSummary(patientId)
      .then((result) => {
        if (mounted) setSummary(result);
      })
      .catch(() => {
        if (mounted) setSummary(null);
      });

    getCurrentPlanOfCareByPatient(patientId)
      .then(async (result) => {
        if (!mounted) return;
        setPoc(result);
        try {
          const history = await getPlanOfCareVersions(result.plan_of_care_id);
          if (mounted) setVersions(history);
        } catch {
          if (mounted) setVersions([]);
        }
      })
      .catch((err) => {
        if (!mounted) return;
        if (err instanceof Error && err.message === "not_found") {
          setNotFound(true);
        }
        setPoc(null);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [patientId]);

  const problems = poc?.current_version?.poc_content?.problems || [];
  const revisionCount = Math.max(versions.length - 1, 0);
  const latestVersion = versions[versions.length - 1];

  const patientOverview = useMemo(() => {
    const patient = summary?.patient;
    return {
      diagnosis: patient?.primary_diagnosis || "No diagnosis on file",
      painSummary: poc ? `${problems.length} active POC problem(s) — v${poc.current_version.version_number}` : "No Plan of Care on file",
      primaryProvider: summary?.care_team?.find((p: any) => p.primary)?.staff_name || "Provider not assigned",
      hnpStatus: poc?.status || "No POC",
      lastVisit: latestVersion?.created_at ? formatDate(latestVersion.created_at) : "—",
      disciplineHistory: versions.slice(-4).reverse().map((v) => `v${v.version_number} — ${v.source_kind}${v.change_reason ? ` (${v.change_reason})` : ""}`),
      careTeam: summary?.care_team?.map((m: any) => m.discipline || "Care team") || ["Care team"],
    };
  }, [summary, poc, problems.length, versions, latestVersion]);

  const handleSelect = (section: string) => {
    const routes: Record<string, string> = {
      overview: "/care-overview",
      admission: "/rnica",
      assessment: "/rnica",
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
    const search = new URLSearchParams();
    if (patientId) search.set("patientId", patientId);
    navigate(`${target}${search.toString() ? `?${search.toString()}` : ""}`);
  };

  return (
    <PatientModuleShell
      patientId={patientId}
      mrn={displayMrn}
      patientName={summary?.patient?.full_name || (loading ? "Loading patient..." : "No patient selected")}
      disciplineLabel="Plan of Care"
      title="Plan of Care (POC)"
      subtitle="Problem → Goal → Intervention, IDG-tracked revisions with rationale"
      activeSection="plan-of-care"
      sections={sections}
      onSelect={handleSelect}
      patientOverview={patientOverview}
      metrics={[
        { label: "Active problems", value: String(problems.length) },
        { label: "Current version", value: poc ? `v${poc.current_version.version_number}` : "—" },
        { label: "Revisions", value: String(revisionCount) },
        { label: "Reviewed in IDG", value: poc?.current_version.reviewed_in_idg ? "Yes" : "No", tone: poc?.current_version.reviewed_in_idg ? "good" : "warn" },
      ]}
    >
      {!patientId && !loading ? (
        <div style={{ padding: 20, color: "var(--sns-muted)", fontSize: 14 }}>Choose a patient from the census to open the chart.</div>
      ) : null}

      {loading ? <div style={{ padding: 20, color: "var(--sns-muted)", fontSize: 14 }}>Loading Plan of Care...</div> : null}

      {notFound && !loading ? (
        <div
          style={{
            padding: 20,
            border: "1px dashed var(--sns-border)",
            borderRadius: 12,
            color: "var(--sns-muted)",
            fontSize: 13,
            background: "var(--sns-cardSoft)",
          }}
        >
          No Plan of Care exists yet for this patient. A POC is generated automatically once the RN ICA problems are finalized
          (Finalization &amp; Signature → "POC generation from assessment problems").
        </div>
      ) : null}

      {poc && !loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {/* Compact problem → goal → intervention table, one row per problem, no full-form editing here */}
          <section style={{ border: "1px solid var(--sns-border)", borderRadius: 12, overflow: "hidden", background: "var(--sns-bg)" }}>
            <div
              style={{
                background: "linear-gradient(90deg, rgba(13,148,136,0.14), rgba(13,148,136,0.06))",
                borderBottom: "1px solid var(--sns-border)",
                padding: "10px 14px",
                fontSize: 13,
                fontWeight: 800,
                color: "var(--sns-white)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>Currently Active Issues</span>
              <span style={{ fontSize: 11, fontWeight: 600, color: "var(--sns-muted)" }}>{problems.length} problem(s) · v{poc.current_version.version_number}</span>
            </div>

            <div style={{ maxHeight: "58vh", overflowY: "auto" }}>
              {problems.length === 0 ? (
                <div style={{ padding: 16, fontSize: 12, color: "var(--sns-muted)" }}>No POC problems recorded in the current version.</div>
              ) : (
                problems.map((problem, idx) => {
                  const severityTone = SEVERITY_TONE[problem.severity] || SEVERITY_TONE.UNKNOWN;
                  const statusTone = STATUS_TONE[problem.status] || STATUS_TONE.ACTIVE;
                  return (
                    <div
                      key={`${problem.problem_code}-${idx}`}
                      style={{
                        padding: "10px 14px",
                        borderBottom: idx < problems.length - 1 ? "1px solid var(--sns-border)" : "none",
                        display: "grid",
                        gridTemplateColumns: "1.1fr 1.3fr 1.3fr 0.6fr",
                        gap: 12,
                        alignItems: "start",
                      }}
                    >
                      <div>
                        <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                          <Badge label={problem.severity} bg={severityTone.bg} fg={severityTone.fg} />
                          <Badge label={problem.status} bg={statusTone.bg} fg={statusTone.fg} />
                        </div>
                        <div style={{ marginTop: 6, fontSize: 12.5, fontWeight: 700, color: "var(--sns-white)" }}>{problem.label}</div>
                        {problem.source_condition ? (
                          <div style={{ marginTop: 2, fontSize: 10.5, color: "var(--sns-muted)" }}>{problem.source_condition}{problem.source_diagnosis_code ? ` · ${problem.source_diagnosis_code}` : ""}</div>
                        ) : null}
                      </div>

                      <div style={{ fontSize: 11.5, color: "var(--sns-white)" }}>
                        {problem.goals.map((goal, gi) => (
                          <div key={gi} style={{ marginBottom: gi < problem.goals.length - 1 ? 6 : 0 }}>
                            {goal.goal_text}
                            {goal.target_timeframe ? <span style={{ color: "var(--sns-muted)" }}> · target: {goal.target_timeframe}</span> : null}
                          </div>
                        ))}
                      </div>

                      <div style={{ fontSize: 11.5, color: "var(--sns-white)" }}>
                        {problem.goals.flatMap((goal) => goal.interventions).map((iv, ii, arr) => (
                          <div key={ii} style={{ marginBottom: ii < arr.length - 1 ? 6 : 0 }}>
                            <span style={{ fontWeight: 700, color: "var(--sns-teal)" }}>{iv.discipline}</span>{" "}
                            {iv.intervention_text}
                            {iv.frequency ? <span style={{ color: "var(--sns-muted)" }}> · {iv.frequency}</span> : null}
                          </div>
                        ))}
                      </div>

                      <div style={{ fontSize: 10.5, color: "var(--sns-muted)", textAlign: "right" }}>{problem.diagnosis_context}</div>
                    </div>
                  );
                })
              )}
            </div>
          </section>

          {/* Revision tracker — how many times the POC has changed and why, not just a count */}
          <section style={{ border: "1px solid var(--sns-border)", borderRadius: 12, overflow: "hidden", background: "var(--sns-bg)" }}>
            <button
              onClick={() => setHistoryOpen((v) => !v)}
              style={{
                width: "100%",
                textAlign: "left",
                background: "var(--sns-cardSoft)",
                border: "none",
                borderBottom: historyOpen ? "1px solid var(--sns-border)" : "none",
                padding: "10px 14px",
                fontSize: 13,
                fontWeight: 800,
                color: "var(--sns-white)",
                cursor: "pointer",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>Revision History — Revised ×{revisionCount}</span>
              <span style={{ fontSize: 11, color: "var(--sns-muted)" }}>{historyOpen ? "Hide" : "Show"} full history ▾</span>
            </button>

            {historyOpen ? (
              <div style={{ padding: "6px 14px 14px" }}>
                {versions.length === 0 ? (
                  <div style={{ fontSize: 12, color: "var(--sns-muted)", padding: "8px 0" }}>No version history available.</div>
                ) : (
                  [...versions].reverse().map((v) => (
                    <div
                      key={v.version_id}
                      style={{
                        display: "grid",
                        gridTemplateColumns: "60px 110px 1fr 90px",
                        gap: 10,
                        padding: "8px 0",
                        borderBottom: "1px solid var(--sns-border)",
                        fontSize: 11.5,
                        alignItems: "start",
                      }}
                    >
                      <div style={{ fontWeight: 800, color: "var(--sns-white)" }}>v{v.version_number}</div>
                      <div>
                        <Badge label={v.source_kind} bg="var(--sns-cardSoft)" fg="var(--sns-teal)" />
                      </div>
                      <div style={{ color: "var(--sns-white)" }}>
                        {v.change_reason || <span style={{ color: "var(--sns-muted)", fontStyle: "italic" }}>No reason documented</span>}
                        {v.reviewed_in_idg ? <span style={{ marginLeft: 8, color: "var(--sns-green)", fontWeight: 700 }}>✓ IDG reviewed</span> : null}
                      </div>
                      <div style={{ color: "var(--sns-muted)", textAlign: "right" }}>{formatDate(v.created_at)}</div>
                    </div>
                  ))
                )}
              </div>
            ) : null}
          </section>
        </div>
      ) : null}
    </PatientModuleShell>
  );
}
