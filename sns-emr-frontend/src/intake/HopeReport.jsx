import React, { useMemo } from "react";
import { useThemeMode } from "../theme/theme";
import { getChartColors } from "../theme/chartColors";
import { defaultPatient } from "./ConsentNotifications";
import mapRnIcaToHopeReport from "./hopeReportMapper";

const styles = {
  page: (colors) => ({ flex: 1, backgroundColor: colors.bg, padding: 24, overflowY: "auto", fontFamily: "'Inter', sans-serif" }),
  actions: { display: "flex", gap: 12, justifyContent: "space-between", flexWrap: "wrap", marginBottom: 16 },
  buttonRow: { display: "flex", gap: 10, flexWrap: "wrap" },
  primaryButton: (colors) => ({ padding: "10px 18px", backgroundColor: colors.teal, color: "#fff", border: "none", borderRadius: 6, fontSize: 13, fontWeight: 700, cursor: "pointer" }),
  secondaryButton: (colors) => ({ padding: "10px 18px", backgroundColor: "transparent", color: colors.teal, border: `1px solid ${colors.teal}`, borderRadius: 6, fontSize: 13, fontWeight: 700, cursor: "pointer" }),
  card: (colors) => ({ backgroundColor: colors.card, borderRadius: 8, borderLeft: `4px solid ${colors.teal}`, padding: 24, boxShadow: "0 12px 28px rgba(15, 23, 42, 0.12)" }),
  paper: { backgroundColor: "#ffffff", color: "#1f2937", borderRadius: 8, padding: 28, border: "1px solid #d9e6eb" },
  title: { fontSize: 24, fontWeight: 700, marginBottom: 4, textAlign: "center" },
  subtitle: { fontSize: 13, color: "#475569", textAlign: "center", marginBottom: 20 },
  section: { marginTop: 24, borderTop: "1px solid #d9e6eb", paddingTop: 18 },
  sectionTitle: { fontSize: 16, fontWeight: 700, marginBottom: 12 },
  item: { marginBottom: 14 },
  codeLine: { fontSize: 13, fontWeight: 700, marginBottom: 6 },
  entryGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 10 },
  entry: { border: "1px solid #e2e8f0", borderRadius: 6, padding: 10, backgroundColor: "#f8fafc" },
  entryLabel: { fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em", color: "#64748b", marginBottom: 4 },
  entryValue: { fontSize: 13, color: "#0f172a", lineHeight: 1.45 },
  headerRow: { display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start", flexWrap: "wrap", marginBottom: 18 },
  patientLine: { fontSize: 14, fontWeight: 600 },
  sfvBanner: (required) => ({
    marginBottom: 18,
    padding: 14,
    borderRadius: 8,
    border: `1px solid ${required ? "#fdba74" : "#cbd5e1"}`,
    backgroundColor: required ? "#fff7ed" : "#f8fafc",
  }),
  sfvTitle: (required) => ({ fontSize: 13, fontWeight: 800, color: required ? "#c2410c" : "#334155", marginBottom: 6 }),
  sfvText: { fontSize: 13, color: "#334155", lineHeight: 1.5 },
};

export default function HopeReport({ formData = {}, patient = defaultPatient, agency, onBack }) {
  const { mode } = useThemeMode();
  const colors = getChartColors(mode);
  const report = useMemo(() => mapRnIcaToHopeReport(formData, patient, agency), [formData, patient, agency]);

  return (
    <div style={styles.page(colors)}>
      <style>{`@media print { .hope-report-actions { display: none !important; } body { background: #fff !important; } }`}</style>
      <div className="hope-report-actions" style={styles.actions}>
        <div style={styles.buttonRow}>
          {onBack ? <button type="button" style={styles.secondaryButton(colors)} onClick={onBack}>Back to RN Assessment</button> : null}
          <button type="button" style={styles.primaryButton(colors)} onClick={() => window.print()}>Print HOPE Report</button>
        </div>
      </div>

      <div style={styles.card(colors)}>
        <div style={styles.paper}>
          <div style={styles.headerRow}>
            <div>
              <div style={styles.title}>{report.agency.name}</div>
              <div style={styles.subtitle}>{report.agency.address} | Tel: {report.agency.phone} | Fax: {report.agency.fax}</div>
            </div>
            <div style={styles.patientLine}>[ ] Check here to Inactivate</div>
          </div>

          <div style={{ ...styles.title, fontSize: 22, marginBottom: 16 }}>HOPE REPORT - Admission</div>
          <div style={{ ...styles.patientLine, marginBottom: 8 }}>Patient Name: {report.patientName}</div>

          <div style={styles.sfvBanner(report.sfvStatus.required)}>
            <div style={styles.sfvTitle(report.sfvStatus.required)}>
              {report.sfvStatus.required ? "SFV Required" : "SFV Status"}
            </div>
            <div style={styles.sfvText}>
              {report.sfvStatus.required
                ? `${report.sfvStatus.statusLabel} - Triggered by: ${report.sfvStatus.triggeredSymptoms.join(", ")}.${report.sfvStatus.dueDate ? ` Due within 2 calendar days of screening (${report.sfvStatus.dueDate.replace(/^(\\d{4})-(\\d{2})-(\\d{2})$/, "$2/$3/$1")}).` : ""}`
                : report.sfvStatus.note}
            </div>
            {report.sfvStatus.required && (
              <div style={{ ...styles.sfvText, marginTop: 6 }}>
                {report.sfvStatus.completed
                  ? "J2052 is completed. J2053 follow-up symptom impact may be documented by an RN or LPN/LVN."
                  : "Complete J2052 after the in-person SFV. J2053 should only be completed once J2052A = 1."}
              </div>
            )}
          </div>

          {report.sections.map((section) => (
            <section key={section.title} style={styles.section}>
              <div style={styles.sectionTitle}>{section.title}</div>
              {section.dataSourceNote && (
                <div style={{
                  fontSize: 11, fontStyle: "italic", padding: "6px 8px", marginBottom: 8, borderRadius: 4,
                  background: section.dataSourceNote.startsWith("⚠") ? "#fffbeb" : "#f0fdf4",
                  color: section.dataSourceNote.startsWith("⚠") ? "#92400e" : "#166534",
                  border: `1px solid ${section.dataSourceNote.startsWith("⚠") ? "#fde68a" : "#bbf7d0"}`,
                }}>
                  {section.dataSourceNote}
                </div>
              )}
              {section.items.map((item) => (
                <div key={`${item.code}-${item.label}`} style={styles.item}>
                  <div style={styles.codeLine}>{item.code}. {item.label}</div>
                  <div style={styles.entryGrid}>
                    {(item.entries || []).map((entry, index) => (
                      <div key={`${item.code}-${index}`} style={styles.entry}>
                        <div style={styles.entryLabel}>{entry.label}</div>
                        <div style={styles.entryValue}>{entry.value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
