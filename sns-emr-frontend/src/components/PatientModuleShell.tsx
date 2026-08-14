import type { ReactNode } from "react";
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
  default: { bg: "#f8fafc", fg: "#0f172a" },
  good: { bg: "#dcfce7", fg: "#166534" },
  warn: { bg: "#fef3c7", fg: "#92400e" },
  bad: { bg: "#fee2e2", fg: "#b91c1c" },
};

export default function PatientModuleShell({
  patientId,
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
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "linear-gradient(180deg, #dfeef2 0%, #d7ebf1 100%)" }}>
      <PatientContextSidebar
        patientId={patientId}
        patientName={patientName}
        disciplineLabel={disciplineLabel}
        sections={sections as any}
        onSelect={onSelect}
        activeSection={activeSection}
        showContext={true}
        patientOverview={patientOverview as any}
      />

      <main style={{ flex: 1, padding: 28 }}>
        <div
          style={{
            maxWidth: 1180,
            margin: "0 auto",
            background: "#f4f7f9",
            border: "1px solid #dbe5ea",
            borderRadius: 14,
            boxShadow: "0 12px 28px rgba(15, 23, 42, 0.08)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "18px 26px",
              background: "linear-gradient(90deg, #0f2033 0%, #0d6c7f 100%)",
              color: "#fff",
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
              <div>Patient ID: {patientId}</div>
              <div>{disciplineLabel}</div>
            </div>
          </div>

          <div style={{ padding: 24, background: "#ffffff" }}>
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
