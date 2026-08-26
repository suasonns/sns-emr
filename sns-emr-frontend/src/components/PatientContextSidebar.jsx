import React from "react";

const palette = {
  bg: "var(--sns-card)",
  panel: "var(--sns-bg)",
  card: "var(--sns-cardSoft)",
  line: "var(--sns-border)",
  accent: "var(--sns-teal)",
  accentSoft: "var(--sns-cardSoft)",
  text: "var(--sns-white)",
  muted: "var(--sns-muted)",
  success: "var(--sns-green)",
};

export default function PatientContextSidebar({
  patientId,
  mrn,
  patientName = "Patient",
  disciplineLabel = "Care Team",
  sections = [],
  onSelect,
  activeSection,
  showContext = true,
  patientOverview = null,
}) {
  const looksLikeUuid = (value) => typeof value === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);

  const defaultSections = [
    { key: "overview", label: "Care Overview" },
    { key: "visit-calendar", label: "Visit Calendar" },
    { key: "assessment", label: "Assessment" },
    { key: "nursing-assessment", label: "RN Assessment", parent: "assessment" },
    { key: "spiritual-assessment", label: "Spiritual", parent: "assessment" },
    { key: "psychosocial-assessment", label: "Psychosocial", parent: "assessment" },
    { key: "tx-meds-dme-supplies", label: "Tx / Meds / DME / Supplies" },
    { key: "idg", label: "IDG" },
    { key: "plan-of-care", label: "Plan of Care (POC)" },
    { key: "bereavement", label: "Bereavement" },
    { key: "compliance", label: "Compliance" },
    { key: "physician", label: "Physician" },
    { key: "lcd-eligibility", label: "LCD Eligibility" },
    { key: "incident-occurrence", label: "Incident / Occurrence" },
    { key: "documents", label: "Documents" },
    { key: "communication-log", label: "Communication Log" },
    { key: "care-team", label: "Care Team" },
  ];

  const nav = (sections.length ? sections : defaultSections).filter((item) => item.key !== "admission");
  const assessmentChildren = nav.filter((item) => item.parent === "assessment" || ["nursing-assessment", "spiritual-assessment", "psychosocial-assessment"].includes(item.key));
  const topLevelNav = nav.filter((item) => item.key !== "assessment" && item.parent !== "assessment" && !["nursing-assessment", "spiritual-assessment", "psychosocial-assessment"].includes(item.key));
  const displayMrn = (mrn && !looksLikeUuid(mrn)) ? mrn : (patientId && !looksLikeUuid(patientId) ? patientId : "No MRN on file");
  const resolvedOverview = patientOverview || {
    // No hardcoded/mock patient identity data here: displaying a fake
    // diagnosis, provider name, or care team when the caller doesn't
    // supply a real patientOverview could be mistaken for genuine PHI in
    // the UI. Every field is an explicit, neutral "not available" state.
    diagnosis: "Not available",
    painSummary: "Patient overview not available.",
    primaryProvider: "—",
    hnpStatus: "—",
    lastVisit: "—",
    disciplineHistory: [],
    careTeam: [],
  };

  return (
    <aside
      style={{
        width: 200,
        minWidth: 200,
        background: "linear-gradient(180deg, var(--sns-bg) 0%, var(--sns-card) 100%)",
        borderRight: `1px solid ${palette.line}`,
        borderTop: `1px solid ${palette.line}`,
        padding: "8px 6px",
        boxShadow: "inset -1px 0 0 rgba(15, 23, 42, 0.04)",
      }}
    >
      <div
        style={{
          background: "linear-gradient(135deg, var(--sns-card) 0%, var(--sns-bgAlt) 50%, var(--sns-teal) 100%)",
          borderRadius: 8,
          padding: 10,
          color: "var(--sns-white)",
          boxShadow: "0 10px 20px rgba(15, 23, 42, 0.12)",
        }}
      >
        <div style={{ fontSize: 8.5, textTransform: "uppercase", letterSpacing: ".12em", opacity: 0.8 }}>Patient</div>
        <div style={{ fontSize: 14, fontWeight: 900, lineHeight: 1.12, marginTop: 4, letterSpacing: "-0.02em" }}>
          {patientName}
        </div>
        <div style={{ fontSize: 10, opacity: 0.82, marginTop: 3, wordBreak: "break-word" }}>MRN: {displayMrn}</div>
        <div style={{ marginTop: 6, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: ".08em" }}>{disciplineLabel}</span>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              borderRadius: 999,
              background: "rgba(255,255,255,0.16)",
              padding: "2px 6px",
              fontSize: 8.5,
              fontWeight: 800,
              textTransform: "uppercase",
            }}
          >
            Active
          </span>
        </div>
      </div>

      <div style={{ marginTop: 8, border: `1px solid ${palette.line}`, borderRadius: 8, background: "var(--sns-card)", padding: 8 }}>
        <div style={{ fontSize: 8.5, letterSpacing: ".1em", textTransform: "uppercase", color: palette.muted, fontWeight: 800 }}>
          Patient record overview
        </div>
        <div style={{ fontSize: 11.5, fontWeight: 800, marginTop: 5, color: palette.text }}>{resolvedOverview.diagnosis}</div>
        <div style={{ fontSize: 10, color: palette.muted, marginTop: 5 }}>{resolvedOverview.painSummary}</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, marginTop: 6 }}>
          <div style={{ fontSize: 8.5, color: palette.muted }}>Primary MD</div>
          <div style={{ fontSize: 8.5, fontWeight: 700, textAlign: "right" }}>{resolvedOverview.primaryProvider}</div>
          <div style={{ fontSize: 8.5, color: palette.muted }}>HNP</div>
          <div style={{ fontSize: 8.5, fontWeight: 700, textAlign: "right" }}>{resolvedOverview.hnpStatus}</div>
          <div style={{ fontSize: 8.5, color: palette.muted }}>Last visit</div>
          <div style={{ fontSize: 8.5, fontWeight: 700, textAlign: "right" }}>{resolvedOverview.lastVisit}</div>
        </div>
      </div>

      <div style={{ marginTop: 8, marginBottom: 5, padding: "0 6px", fontSize: 8.5, fontWeight: 800, color: palette.muted, letterSpacing: ".12em", textTransform: "uppercase" }}>
        Assessment Modules
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {topLevelNav.map((item) => {
          const isActive = activeSection === item.key || (!activeSection && item.key === "overview");
          if (item.key === "assessment") {
            const assessmentActive = assessmentChildren.some((child) => activeSection === child.key);
            return (
              <div key={item.key || item.label} style={{ margin: "1px 0 1px 0", paddingLeft: 0 }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    width: "100%",
                    borderRadius: 6,
                    border: assessmentActive ? `1px solid ${palette.accent}` : `1px solid ${palette.line}`,
                    background: assessmentActive ? "linear-gradient(90deg, rgba(13,148,136,0.12), rgba(13,148,136,0.02))" : "var(--sns-card)",
                    color: palette.text,
                    fontWeight: 700,
                    fontSize: 11.5,
                    padding: "5px 8px",
                    boxShadow: assessmentActive ? "inset 0 0 0 1px rgba(13,148,136,0.08)" : "none",
                  }}
                >
                  <span>{item.label}</span>
                  {item.meta ? <span style={{ fontSize: 8.5, color: palette.muted }}>{item.meta}</span> : null}
                </div>

                {assessmentChildren.length > 0 ? (
                  <div style={{ margin: "1px 0 1px 10px", paddingLeft: 8, borderLeft: `2px solid ${palette.line}` }}>
                    <div style={{ marginBottom: 4, fontSize: 8.5, fontWeight: 800, color: palette.muted, letterSpacing: ".1em", textTransform: "uppercase" }}>
                      Assessment
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                      {assessmentChildren.map((child) => {
                        const childActive = activeSection === child.key;
                        return (
                          <button
                            key={child.key}
                            type="button"
                            onClick={() => onSelect?.(child.key)}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between",
                              width: "100%",
                              textAlign: "left",
                              borderRadius: 6,
                              border: childActive ? `1px solid ${palette.accent}` : `1px solid ${palette.line}`,
                              background: childActive ? "linear-gradient(90deg, rgba(13,148,136,0.12), rgba(13,148,136,0.02))" : "var(--sns-card)",
                              color: palette.text,
                              fontWeight: 700,
                              fontSize: 11.5,
                              cursor: "pointer",
                              padding: "4px 8px 4px 14px",
                              boxShadow: childActive ? "inset 0 0 0 1px rgba(13,148,136,0.08)" : "none",
                            }}
                          >
                            <span>{child.label}</span>
                            {child.meta ? <span style={{ fontSize: 8.5, color: palette.muted }}>{child.meta}</span> : null}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ) : null}
              </div>
            );
          }

          return (
            <React.Fragment key={item.key || item.label}>
              <button
                type="button"
                onClick={() => onSelect?.(item.key)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  width: "100%",
                  textAlign: "left",
                  borderRadius: 6,
                  border: isActive ? `1px solid ${palette.accent}` : `1px solid ${palette.line}`,
                  background: isActive ? "linear-gradient(90deg, rgba(13,148,136,0.12), rgba(13,148,136,0.02))" : "var(--sns-card)",
                  color: palette.text,
                  fontWeight: 700,
                  fontSize: 11.5,
                  cursor: "pointer",
                  padding: "5px 8px",
                  boxShadow: isActive ? "inset 0 0 0 1px rgba(13,148,136,0.08)" : "none",
                }}
              >
                <span>{item.label}</span>
                {item.meta ? <span style={{ fontSize: 8.5, color: palette.muted }}>{item.meta}</span> : null}
              </button>
            </React.Fragment>
          );
        })}
      </div>

      {showContext && (
        <div style={{ marginTop: 10 }}>
          <div style={{ padding: "0 6px", fontSize: 8.5, fontWeight: 800, color: palette.muted, letterSpacing: ".12em", textTransform: "uppercase" }}>
            Patient record workspace
          </div>

          <div style={{ marginTop: 6, border: `1px solid ${palette.line}`, background: "var(--sns-card)", borderRadius: 8, overflow: "hidden" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, padding: 8, background: palette.card }}>
              <div style={{ fontSize: 10, color: palette.muted }}>HNP</div>
              <div style={{ fontSize: 10, fontWeight: 700, textAlign: "right" }}>{resolvedOverview.hnpStatus}</div>
              <div style={{ fontSize: 10, color: palette.muted }}>RN</div>
              <div style={{ fontSize: 10, fontWeight: 700, textAlign: "right" }}>3 days ago</div>
              <div style={{ fontSize: 10, color: palette.muted }}>MSW</div>
              <div style={{ fontSize: 10, fontWeight: 700, textAlign: "right" }}>1 week</div>
              <div style={{ fontSize: 10, color: palette.muted }}>SC</div>
              <div style={{ fontSize: 10, fontWeight: 700, textAlign: "right" }}>4 days ago</div>
            </div>

            <div style={{ padding: 8, borderTop: `1px solid ${palette.line}` }}>
              <div style={{ fontSize: 8.5, fontWeight: 800, color: palette.muted, letterSpacing: ".08em", textTransform: "uppercase", marginBottom: 5 }}>
                Cross-discipline prep
              </div>
              {(resolvedOverview.disciplineHistory || []).map((item) => (
                <div key={item} style={{ fontSize: 10, lineHeight: 1.35, marginBottom: 4, color: palette.text }}>
                  • {item}
                </div>
              ))}
            </div>

            <div style={{ padding: 8, borderTop: `1px solid ${palette.line}` }}>
              <div style={{ fontSize: 8.5, fontWeight: 800, color: palette.muted, letterSpacing: ".08em", textTransform: "uppercase", marginBottom: 5 }}>
                Active care team
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {(resolvedOverview.careTeam || []).map((teamMember) => (
                  <span key={teamMember} style={{ fontSize: 8.5, background: "#ecfeff", color: "#0f766e", borderRadius: 999, padding: "2px 6px", fontWeight: 700 }}>
                    {teamMember}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
