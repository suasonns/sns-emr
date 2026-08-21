import { useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { fetchPatientSummary } from "../api/patientCharts";
import { clearActivePatientId } from "../utils/activePatient";
import PatientContextSidebar from "./PatientContextSidebar";

type Section = {
  key: string;
  label: string;
  meta?: string;
};

type Overview = {
  diagnosis: string;
  painSummary: string;
  primaryProvider: string;
  hnpStatus: string;
  lastVisit: string;
  disciplineHistory: string[];
  careTeam: string[];
};

type Metric = {
  label: string;
  value: string;
  tone?: "default" | "good" | "warn" | "bad";
};

type ShellProps = {
  patientId: string;
  mrn?: string;
  patientName: string;
  disciplineLabel: string;
  title: string;
  subtitle: string;
  activeSection: string;
  sections: Section[];
  onSelect: (section: string) => void;
  patientOverview: Overview;
  metrics?: Metric[];
  children: ReactNode;
};

const metricToneStyles: Record<NonNullable<Metric["tone"]>, { bg: string; fg: string }> = {
  default: { bg: "var(--sns-cardSoft)", fg: "var(--sns-white)" },
  good: { bg: "rgba(16, 185, 129, 0.12)", fg: "var(--sns-green)" },
  warn: { bg: "rgba(245, 158, 11, 0.14)", fg: "var(--sns-orange)" },
  bad: { bg: "rgba(239, 68, 68, 0.12)", fg: "var(--sns-red)" },
};

const CLINICAL_BRAND = {
  navy: "var(--sns-card)",
  teal: "var(--sns-teal)",
  tealDark: "var(--sns-teal)",
  tealLight: "var(--sns-cardSoft)",
  bg: "var(--sns-bg)",
  canvas: "var(--sns-bgAlt)",
  panel: "var(--sns-card)",
  line: "var(--sns-border)",
  text: "var(--sns-white)",
  muted: "var(--sns-muted)",
};

const looksLikeUuid = (value?: string) => !!value && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);

export default function PatientModuleShell({
  patientId,
  mrn,
  patientName,
  disciplineLabel,
  title,
  subtitle,
  activeSection,
  sections,
  onSelect,
  patientOverview,
  metrics = [],
  children,
}: ShellProps) {
  const navigate = useNavigate();
  const [resolvedMrn, setResolvedMrn] = useState<string | undefined>(mrn);

  useEffect(() => {
    if (mrn) {
      setResolvedMrn(mrn);
      return;
    }

    if (!patientId) {
      setResolvedMrn("No MRN on file");
      return;
    }

    let isMounted = true;
    fetchPatientSummary(patientId)
      .then((summary) => {
        if (!isMounted) return;
        const nextMrn = summary?.patient?.mrn || "No MRN on file";
        setResolvedMrn(nextMrn);
      })
      .catch(() => {
        if (isMounted) setResolvedMrn("No MRN on file");
      });

    return () => {
      isMounted = false;
    };
  }, [mrn, patientId]);

  const displayMrn = resolvedMrn && !looksLikeUuid(resolvedMrn) ? resolvedMrn : "No MRN on file";

  return (
    <div style={{ display: "flex", minHeight: "100vh", width: "100%", maxWidth: "100vw", background: CLINICAL_BRAND.canvas, fontFamily: "'Inter', 'Segoe UI', sans-serif", overflowX: "hidden" }}>
      <PatientContextSidebar
        patientId={patientId}
        mrn={displayMrn}
        patientName={patientName}
        disciplineLabel={disciplineLabel}
        sections={sections as any}
        onSelect={onSelect}
        activeSection={activeSection}
        showContext={true}
        patientOverview={patientOverview as any}
      />

      <main style={{ flex: 1, minWidth: 0, padding: 28, overflowX: "auto" }}>
        <div
          style={{
            maxWidth: 1180,
            margin: "0 auto",
            background: CLINICAL_BRAND.bg,
            border: `1px solid ${CLINICAL_BRAND.line}`,
            borderRadius: 14,
            boxShadow: "0 12px 28px rgba(15, 23, 42, 0.08)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "18px 26px",
              background: "linear-gradient(90deg, var(--sns-card) 0%, var(--sns-teal) 100%)",
              color: "var(--sns-white)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", opacity: 0.8 }}>
                Patient Module
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, marginTop: 6 }}>{title}</div>
              <div style={{ fontSize: 13, opacity: 0.9, marginTop: 6 }}>{subtitle}</div>
            </div>
            <div style={{ fontSize: 12, opacity: 0.9, textAlign: "right" }}>
              <div>MRN: {displayMrn}</div>
              <div>{disciplineLabel}</div>
              <button
                type="button"
                onClick={() => {
                  clearActivePatientId();
                  navigate("/portal");
                }}
                style={{
                  marginTop: 10,
                  border: "1px solid rgba(255,255,255,0.3)",
                  background: "rgba(255,255,255,0.08)",
                  color: "#fff",
                  borderRadius: 999,
                  padding: "6px 12px",
                  fontSize: 11,
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                ← Dashboard
              </button>
            </div>
          </div>

          <div style={{ padding: 24, background: CLINICAL_BRAND.panel }}>
            {metrics.length > 0 ? (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                  gap: 14,
                  marginBottom: 24,
                }}
              >
                {metrics.map((metric) => {
                  const tone = metricToneStyles[metric.tone || "default"];
                  return (
                    <div
                      key={metric.label}
                      style={{
                        border: "1px solid #dfe8ee",
                        borderRadius: 12,
                        background: tone.bg,
                        padding: "14px 16px",
                      }}
                    >
                      <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em", color: "#64748b" }}>
                        {metric.label}
                      </div>
                      <div style={{ marginTop: 8, fontSize: 15, fontWeight: 700, color: tone.fg }}>{metric.value}</div>
                    </div>
                  );
                })}
              </div>
            ) : null}

            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
