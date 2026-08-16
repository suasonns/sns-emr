import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  fetchCommunicationLog,
  fetchCompliance,
  fetchIncidentOccurrence,
  fetchPatientSummary,
  fetchVolunteerScheduling,
  type CommunicationLogResponse,
  type ComplianceResponse,
  type IncidentOccurrenceResponse,
  type PatientSummaryResponse,
  type VolunteerSchedulingResponse,
} from "../api/patientCharts";
import { getCurrentUser } from "../api/session";
import PortalShell from "../components/PortalShell";
import { portalTypography } from "../styles/portalTypography";
import { getActivePatientId } from "../utils/activePatient";
const PATIENT_ID = getActivePatientId() ?? "";
const QUICK_LINKS = [
  { label: "Care Overview", route: "/care-overview" },
  { label: "Secure Inbox", route: "/secure-inbox" },
  { label: "Incident / Occurrence", route: "/clinical-alerts" },
  { label: "Compliance / LCD / HOPE / QIES", route: "/compliance" },
  { label: "Bereavement", route: "/bereavement" },
  { label: "Volunteer Scheduling", route: "/volunteer-scheduling" },
  { label: "RNICA", route: "/rnica" },
  { label: "MSW ICA", route: "/msw-ica" },
  { label: "SC ICA", route: "/sc-ica" },
  { label: "Patient LCD", route: "/patient-lcd" },
  { label: "Analytics", route: "/analytics" },
  { label: "Tenant Dashboard", route: "/tenant" },
  { label: "Owner Dashboard", route: "/owner" },
];

type LiveData = {
  summary: PatientSummaryResponse | null;
  messaging: CommunicationLogResponse | null;
  compliance: ComplianceResponse | null;
  volunteer: VolunteerSchedulingResponse | null;
  incidents: IncidentOccurrenceResponse | null;
};

function Panel({
  title,
  children,
  accent = "#0d9488",
}: {
  title: string;
  children: React.ReactNode;
  accent?: string;
}) {
  return (
    <section style={panelStyle}>
      <div style={{ ...sectionHeaderStyle, borderLeft: `3px solid ${accent}`, paddingLeft: 10 }}>
        {title}
      </div>
      {children}
    </section>
  );
}

export default function SNSPortal() {
  const navigate = useNavigate();
  const dashboardRef = useRef<HTMLDivElement | null>(null);
  const currentUser = getCurrentUser();
  const workspaceName = currentUser?.tenant_name ?? "Love & Faith Hospice Services Inc.";
  const displayName = currentUser?.full_name ?? "Signed-in User";
  const quickLinks = useMemo(() => QUICK_LINKS, []);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<LiveData>({
    summary: null,
    messaging: null,
    compliance: null,
    volunteer: null,
    incidents: null,
  });

  useEffect(() => {
    let mounted = true;

    Promise.allSettled([
      fetchPatientSummary(PATIENT_ID),
      fetchCommunicationLog(PATIENT_ID),
      fetchCompliance(PATIENT_ID),
      fetchVolunteerScheduling(PATIENT_ID),
      fetchIncidentOccurrence(PATIENT_ID),
    ])
      .then((results) => {
        if (!mounted) return;

        const next: LiveData = {
          summary: results[0].status === "fulfilled" ? results[0].value : null,
          messaging: results[1].status === "fulfilled" ? results[1].value : null,
          compliance: results[2].status === "fulfilled" ? results[2].value : null,
          volunteer: results[3].status === "fulfilled" ? results[3].value : null,
          incidents: results[4].status === "fulfilled" ? results[4].value : null,
        };

        setData(next);

        if (!next.summary) {
          setError("Unable to load live portal data.");
        }
      })
      .catch(() => {
        if (mounted) setError("Unable to load live portal data.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const summary = data.summary;
  const messaging = data.messaging;
  const compliance = data.compliance;
  const volunteer = data.volunteer;
  const incidents = data.incidents;

  const chartAlerts = useMemo(() => {
    const issues = compliance?.open_issues ?? [];
    const found = issues.join(" ").toLowerCase();
    const alerts: string[] = [];

    if (found.includes("cti")) {
      alerts.push("Missing CTI");
    } else if ((compliance?.note_counts.f2f ?? 0) === 0) {
      alerts.push("Missing CTI");
    }

    if (found.includes("signature")) {
      alerts.push("Missing Signature on Notes");
    } else if ((compliance?.note_counts.hope ?? 0) === 0) {
      alerts.push("Missing Signature on Notes");
    }

    if (found.includes("documentation")) {
      alerts.push("Missing Documentation");
    } else if ((compliance?.note_counts.total ?? 0) > 0 && (compliance?.open_issues.length ?? 0) === 0) {
      alerts.push("Missing Documentation");
    }

    return alerts;
  }, [compliance]);

  const timeSensitive = useMemo(() => {
    const items: Array<{ label: string; badge: string; color: string }> = [];

    compliance?.open_issues.slice(0, 2).forEach((issue) => {
      items.push({ label: issue, badge: "Review", color: "#f59e0b" });
    });

    chartAlerts.slice(0, 3).forEach((alert) => {
      if (!items.some((item) => item.label === alert)) {
        items.unshift({ label: alert, badge: "Required", color: "#dc2626" });
      }
    });

    if (!items.length && incidents?.items.length) {
      const alert = incidents.items[0];
      items.push({
        label: `${alert.incident_type} reported for patient`,
        badge: alert.incident_severity,
        color: alert.incident_severity === "SENTINEL" ? "#dc2626" : "#f59e0b",
      });
    }

    if (!items.length) {
      items.push({ label: "No urgent items loaded", badge: "OK", color: "#059669" });
    }

    return items;
  }, [chartAlerts, compliance, incidents]);

  const overdueTasks = useMemo(() => {
    const count = compliance?.task_counts.overdue ?? 0;
    const items = count
      ? [`${count} overdue task(s) in compliance queue`]
      : [];

    if (volunteer?.task_slots.length) {
      const next = volunteer.task_slots[0];
      items.push(`${next.task_type} · ${next.status}`);
    }

    if (!items.length) items.push("No overdue tasks");
    return items;
  }, [compliance, volunteer]);

  const qaAlerts = useMemo(() => {
    const items: string[] = [];
    const sev = incidents?.counts_by_severity || {};
    if ((sev.SENTINEL || 0) > 0) items.push(`${sev.SENTINEL} sentinel event(s)`);
    if ((sev.HIGH || 0) > 0) items.push(`${sev.HIGH} high severity event(s)`);
    if ((sev.MEDIUM || 0) > 0) items.push(`${sev.MEDIUM} medium severity event(s)`);
    if (!items.length) items.push("No QA alerts loaded");
    return items;
  }, [incidents]);

  const hopeChecklist = [
    { label: "Pending Nurse / Clinical Signature", count: compliance?.note_counts.hope ?? 0, status: "Pending" },
    { label: "Ready for Single QIES Submission", count: compliance?.note_counts.poc ?? 0, status: "Pending" },
    { label: "Ready for Batch Export Processing", count: compliance?.task_counts.completed ?? 0, status: "Ready" },
    { label: "Awaiting CDPH Federal Gateway Confirmation", count: compliance?.task_counts.pending ?? 0, status: "Ready" },
  ];

  const notesForCorrection = useMemo(() => {
    if (compliance?.open_issues.length) {
      return compliance.open_issues.slice(0, 3);
    }
    if (compliance?.recent_notes.length) {
      return compliance.recent_notes.slice(0, 3).map((note) => note.content);
    }
    return ["No correction items loaded"];
  }, [compliance]);

  const messages = messaging?.entries.slice(0, 2) ?? [];
  const signatures = useMemo(() => {
    if (compliance?.recent_notes.length) {
      return compliance.recent_notes.slice(0, 4).map((note) => ({
        title: note.form_key || note.note_type,
        subtitle: note.created_at || "Pending",
        action: note.form_key?.includes("F2F") || note.form_key?.includes("POC") ? "Review & Sign" : "Sign",
      }));
    }
    if (volunteer?.task_slots.length) {
      return volunteer.task_slots.slice(0, 4).map((slot) => ({
        title: slot.task_type,
        subtitle: slot.due_date || slot.status,
        action: "Open",
      }));
    }
    return [];
  }, [compliance, volunteer]);

  const scheduledVisits = volunteer?.visits.slice(0, 4) ?? [];
  const clinicalIssues = incidents?.items.slice(0, 2) ?? [];

  const go = (route?: string) => {
    if (!route) return;
    navigate(route);
  };

  return (
    <PortalShell activeTab="Dashboard">
      <main style={mainStyle} ref={dashboardRef}>
        <div style={heroStyle}>
          <div>
            <div style={heroTitleStyle}>Good Morning, {displayName}</div>
            <div style={heroSubStyle}>
              Active Agency Workspace: <span style={badgeStyle}>{workspaceName}</span>
            </div>
          </div>
          <div style={syncedStyle}>Last synced: Today at 08:30 AM</div>
        </div>

        {loading ? <div style={panelStyle}>Loading live portal data...</div> : null}
        {error ? <div style={{ ...panelStyle, color: "#b91c1c" }}>{error}</div> : null}

        {summary ? (
          <>
            <div style={grid3Style}>
              <Panel title="Time Sensitive" accent="#f59e0b">
                {timeSensitive.map((item) => (
                  <div key={item.label} style={listRowStyle}>
                    <div style={rowDot(item.color)} />
                    <div style={{ flex: 1 }}>
                      <div style={rowTitleStyle}>{item.label}</div>
                    </div>
                    <span style={pillStyle(item.color)}>{item.badge}</span>
                  </div>
                ))}
              </Panel>

              <Panel title="Overdue Tasks" accent="#dc2626">
                {overdueTasks.map((item) => (
                  <div key={item} style={listRowStyle}>
                    <div style={rowDot("#dc2626")} />
                    <div style={rowTitleStyle}>{item}</div>
                    <span style={pillStyle("#dc2626")}>Overdue</span>
                  </div>
                ))}
              </Panel>

              <Panel title="QA Alerts" accent="#2563eb">
                {qaAlerts.map((item) => (
                  <div key={item} style={listRowStyle}>
                    <div style={rowDot("#2563eb")} />
                    <div style={rowTitleStyle}>{item}</div>
                  </div>
                ))}
              </Panel>
            </div>

            <div style={grid2Style}>
              <Panel title="HOPE QIES Tracking Checklist" accent="#0d9488">
                {hopeChecklist.map((item) => (
                  <div key={item.label} style={checkRowStyle}>
                    <div style={{ flex: 1 }}>
                      <div style={rowTitleStyle}>{item.label}</div>
                      <div style={subtleTextStyle}>Patient: {summary.patient.full_name}</div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={countBubbleStyle}>{item.count}</span>
                      <span style={statusPillStyle(item.status === "Ready" ? "#059669" : "#f59e0b")}>{item.status}</span>
                    </div>
                  </div>
                ))}
              </Panel>

              <Panel title="Notes for Correction Required" accent="#0d9488">
                <div style={calloutStyle}>
                  Regulatory review found items that need attention. Click to open the patient chart and resolve them.
                </div>
                <div style={{ display: "grid", gap: 10 }}>
                  {notesForCorrection.map((item) => (
                    <div key={item} style={noteStyle}>
                      <div style={rowDot("#0d9488")} />
                      <div style={rowTitleStyle}>{item}</div>
                      <button style={miniButtonStyle} onClick={() => go("/compliance")}>Resolve Now</button>
                    </div>
                  ))}
                </div>
                <div style={quickLinksStyle}>
                  {quickLinks.slice(0, 4).map((item) => (
                    <button key={item.route} style={quickChipStyle} onClick={() => go(item.route)}>
                      + {item.label}
                    </button>
                  ))}
                </div>
              </Panel>
            </div>

            <div style={grid2Style}>
              <Panel title="Messaging" accent="#0d9488">
                {messages.length ? (
                  messages.map((message) => (
                    <div key={message.id} style={messageStyle}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                        <div>
                          <div style={rowTitleStyle}>{message.event_type}</div>
                          <div style={subtleTextStyle}>{message.event_time || "—"}</div>
                        </div>
                        <button style={miniButtonStyle} onClick={() => go("/messaging")}>Open</button>
                      </div>
                      <div style={{ marginTop: 8, fontSize: portalTypography.small, color: "#334155", lineHeight: 1.6 }}>{message.summary}</div>
                    </div>
                  ))
                ) : (
                  <div style={emptyStyle}>No messages loaded.</div>
                )}
              </Panel>

              <Panel title="My Signature Required" accent="#0d9488">
                {signatures.length ? (
                  signatures.map((item) => (
                    <div key={`${item.title}-${item.subtitle}`} style={signatureStyle}>
                      <div>
                        <div style={rowTitleStyle}>{item.title}</div>
                        <div style={subtleTextStyle}>{item.subtitle}</div>
                      </div>
                      <button style={miniButtonStyle} onClick={() => go("/portal")}>{item.action}</button>
                    </div>
                  ))
                ) : (
                  <div style={emptyStyle}>No signatures pending.</div>
                )}
              </Panel>
            </div>

            <div style={grid2Style}>
              <Panel title="Today's Scheduled Visits" accent="#0d9488">
                {scheduledVisits.length ? (
                  scheduledVisits.map((visit) => (
                    <div key={visit.id} style={visitStyle}>
                      <div style={{ minWidth: 72 }}>
                        <div style={visitTimeStyle}>{visit.visit_datetime || "—"}</div>
                        <div style={subtleTextStyle}>{visit.visit_type}</div>
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={rowTitleStyle}>{visit.provider_name}</div>
                        <div style={subtleTextStyle}>{visit.visit_discipline || "Visit"}</div>
                      </div>
                      <span style={statusPillStyle("#059669")}>{visit.status}</span>
                    </div>
                  ))
                ) : (
                  <div style={emptyStyle}>No scheduled visits loaded.</div>
                )}
              </Panel>

              <Panel title="New Clinical Issues" accent="#0d9488">
                {clinicalIssues.length ? (
                  clinicalIssues.map((issue) => (
                    <div key={issue.id} style={issueStyle(issue.incident_severity)}>
                      <div style={rowTitleStyle}>{issue.incident_type}: {issue.incident_severity}</div>
                      <div style={{ fontSize: portalTypography.small, color: "#334155", marginTop: 4 }}>{issue.narrative || "No narrative available."}</div>
                    </div>
                  ))
                ) : (
                  <div style={emptyStyle}>No clinical issues loaded.</div>
                )}
              </Panel>
            </div>

          </>
        ) : null}
      </main>
    </PortalShell>
  );
}

export const pageStyle: React.CSSProperties = {
  minHeight: "100vh",
  background: "#eef3f8",
  fontFamily: "'Inter', 'Segoe UI', sans-serif",
};

export const topBarStyle: React.CSSProperties = {
  height: 80,
  background: "#1f4a78",
  color: "#fff",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "0 30px",
  gap: 18,
};

export const brandStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 12,
  flexShrink: 0,
};

export const logoDot: React.CSSProperties = {
  width: 36,
  height: 36,
  borderRadius: 999,
  background: "#10b7a2",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontWeight: 800,
};

export const navStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "stretch",
  gap: 2,
  justifyContent: "center",
  flex: 1,
  minWidth: 0,
  overflow: "hidden",
  padding: "0 8px",
};

export const navButtonStyle: React.CSSProperties = {
  border: "none",
  color: "#fff",
  padding: "10px 13px",
  borderRadius: 6,
  fontSize: 12,
  fontWeight: 700,
  cursor: "pointer",
  whiteSpace: "nowrap",
  lineHeight: 1.1,
};

export const userStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 12,
  flexShrink: 0,
};

export const avatarStyle: React.CSSProperties = {
  width: 36,
  height: 36,
  borderRadius: 999,
  background: "#fff",
  color: "#1e3d66",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontWeight: 800,
  fontSize: 12,
};

const mainStyle: React.CSSProperties = {
  maxWidth: 1180,
  margin: "0 auto",
  boxSizing: "border-box",
  padding: "16px 24px 0",
};

const heroStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  background: "#fff",
  border: "1px solid #dbe5ea",
  borderRadius: 12,
  padding: "16px 20px",
  marginBottom: 16,
};

const heroTitleStyle: React.CSSProperties = {
  fontSize: 16,
  lineHeight: 1.15,
  fontWeight: 800,
  color: "#1f2937",
};

const heroSubStyle: React.CSSProperties = {
  marginTop: 6,
  fontSize: 12,
  color: "#64748b",
};

const syncedStyle: React.CSSProperties = {
  fontSize: 11,
  color: "#64748b",
  whiteSpace: "nowrap",
  marginTop: 4,
};

const badgeStyle: React.CSSProperties = {
  display: "inline-block",
  marginLeft: 4,
  background: "#ccfbf1",
  color: "#0f766e",
  padding: "3px 10px",
  borderRadius: 999,
  fontSize: 10,
  fontWeight: 800,
};

const panelStyle: React.CSSProperties = {
  background: "#fff",
  border: "1px solid #dbe5ea",
  borderRadius: 12,
  padding: 12,
  boxShadow: "0 12px 28px rgba(15, 23, 42, 0.05)",
};

const sectionHeaderStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 800,
  textTransform: "uppercase",
  letterSpacing: "0.1em",
  marginBottom: 10,
  color: "#0f2033",
};

const grid3Style: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
  gap: 12,
  marginBottom: 12,
};

const grid2Style: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
  gap: 12,
  marginBottom: 12,
};

const listRowStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  padding: "10px 0",
  borderBottom: "1px solid #edf2f7",
};

const rowTitleStyle: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 700,
  color: "#0f172a",
};

const subtleTextStyle: React.CSSProperties = {
  fontSize: portalTypography.small,
  color: "#64748b",
  marginTop: 2,
};

function rowDot(color: string): React.CSSProperties {
  return {
    width: 8,
    height: 8,
    borderRadius: 999,
    background: color,
    flexShrink: 0,
  };
}

function pillStyle(color: string): React.CSSProperties {
  return {
    padding: "2px 8px",
    borderRadius: 999,
    fontSize: 9,
    fontWeight: 800,
    color: "#fff",
    background: color,
    flexShrink: 0,
  };
}

const checkRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  padding: "10px 0",
  borderBottom: "1px solid #edf2f7",
};

const countBubbleStyle: React.CSSProperties = {
  minWidth: 22,
  height: 22,
  borderRadius: 999,
  background: "#e2e8f0",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: 10,
  fontWeight: 800,
  color: "#334155",
};

function statusPillStyle(bg: string): React.CSSProperties {
  return {
    padding: "2px 8px",
    borderRadius: 999,
    fontSize: 9,
    fontWeight: 800,
    color: "#fff",
    background: bg,
  };
}

const calloutStyle: React.CSSProperties = {
  border: "1px solid #0d9488",
  background: "#ecfeff",
  borderRadius: 12,
  padding: 12,
  fontSize: 11,
  color: "#0f766e",
  marginBottom: 12,
};

const noteStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  justifyContent: "space-between",
  padding: "10px 0",
  borderBottom: "1px solid #edf2f7",
};

const miniButtonStyle: React.CSSProperties = {
  border: "1px solid #0d9488",
  background: "#fff",
  color: "#0d9488",
  borderRadius: 8,
  padding: "6px 10px",
  fontSize: 10,
  fontWeight: 800,
  cursor: "pointer",
  whiteSpace: "nowrap",
};

const quickLinksStyle: React.CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
  marginTop: 12,
};

const quickChipStyle: React.CSSProperties = {
  border: "1px solid #dbe5ea",
  background: "#fff",
  borderRadius: 999,
  padding: "7px 12px",
  fontSize: 11,
  fontWeight: 700,
  color: "#475569",
  cursor: "pointer",
};

const messageStyle: React.CSSProperties = {
  border: "1px solid #dbe5ea",
  borderRadius: 12,
  padding: 10,
  marginBottom: 10,
  background: "#f8fafc",
};

const signatureStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 12,
  padding: "8px 0",
  borderBottom: "1px solid #edf2f7",
};

const visitStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 14,
  padding: "8px 0",
  borderBottom: "1px solid #edf2f7",
};

const visitTimeStyle: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 800,
  color: "#0f172a",
};

const issueStyle = (severity: string): React.CSSProperties => ({
  borderRadius: 10,
  padding: 12,
  marginBottom: 10,
  background: severity === "SENTINEL" ? "#fee2e2" : "#fef3c7",
  borderLeft: `3px solid ${severity === "SENTINEL" ? "#dc2626" : "#f59e0b"}`,
});

const emptyStyle: React.CSSProperties = {
  fontSize: 11,
  color: "#64748b",
};

export const footerBarStyle: React.CSSProperties = {
  background: "#1f3d66",
  color: "#fff",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "12px 24px",
  gap: 20,
};

export const footerLinksStyle: React.CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 24,
  fontSize: 12,
  fontWeight: 700,
};

export const legalFooterStyle: React.CSSProperties = {
  background: "#111827",
  color: "#9ca3af",
  fontSize: 11,
  textAlign: "center",
  padding: "10px 20px",
};
