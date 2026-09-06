import React, { useEffect, useMemo, useState } from "react";
import {
  closeRnicaHopeWorkflow,
  exportRnicaHopeWorkflow,
  patchRnicaHopeInactivation,
  patchRnicaHopeSubmission,
  readyRnicaHopeWorkflow,
  unlockRnicaHopeWorkflow,
} from "../api/icaAssessments";
import { useThemeMode } from "../theme/theme";
import { getChartColors } from "../theme/chartColors";
import { defaultPatient } from "./ConsentNotifications";
import mapRnIcaToHopeReport from "./hopeReportMapper";
import BrandLogo from "../components/BrandLogo";

const MED_ORDER_LINKS = {
  N0510: { section: "add-md-order", label: "Open physician orders" },
  N0520: { section: "add-md-order", label: "Open bowel-regimen order" },
};

const styles = {
  page: (colors) => ({ flex: 1, backgroundColor: colors.bg, padding: 24, overflowY: "auto", fontFamily: "'Inter', sans-serif" }),
  actions: { display: "flex", gap: 12, justifyContent: "space-between", flexWrap: "wrap", marginBottom: 16 },
  buttonRow: { display: "flex", gap: 10, flexWrap: "wrap" },
  primaryButton: (colors) => ({ padding: "10px 18px", backgroundColor: colors.teal, color: "#fff", border: "none", borderRadius: 6, fontSize: 13, fontWeight: 700, cursor: "pointer" }),
  secondaryButton: (colors) => ({ padding: "10px 18px", backgroundColor: "transparent", color: colors.teal, border: `1px solid ${colors.teal}`, borderRadius: 6, fontSize: 13, fontWeight: 700, cursor: "pointer" }),
  disabledButton: () => ({ padding: "10px 18px", backgroundColor: "#94a3b8", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, fontWeight: 700, cursor: "not-allowed" }),
  card: (colors) => ({ backgroundColor: colors.card, borderRadius: 8, borderLeft: `4px solid ${colors.teal}`, padding: 24, boxShadow: "0 12px 28px rgba(15, 23, 42, 0.12)" }),
  paper: { backgroundColor: "#ffffff", color: "#1f2937", borderRadius: 8, padding: 28, border: "1px solid #d9e6eb" },
  title: { fontSize: 24, fontWeight: 700, marginBottom: 4, textAlign: "center" },
  subtitle: { fontSize: 13, color: "#475569", textAlign: "center", marginBottom: 20 },
  section: { marginTop: 24, borderTop: "1px solid #d9e6eb", paddingTop: 18 },
  sectionTitle: { fontSize: 16, fontWeight: 700, marginBottom: 12 },
  item: { marginBottom: 14 },
  codeRow: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, flexWrap: "wrap", marginBottom: 6 },
  codeLine: { fontSize: 13, fontWeight: 700 },
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
  legacyBanner: { marginBottom: 18, padding: 14, borderRadius: 8, border: "1px solid #fecaca", backgroundColor: "#fef2f2" },
  legacyTitle: { fontSize: 13, fontWeight: 800, color: "#b91c1c", marginBottom: 6 },
  legacyText: { fontSize: 13, color: "#7f1d1d", lineHeight: 1.5 },
  logo: { width: 140, height: "auto", objectFit: "contain" },
  headerMeta: { display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" },
  workflowPanel: { marginBottom: 18, padding: 16, borderRadius: 10, border: "1px solid #d9e6eb", background: "#f8fafc" },
  workflowGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginTop: 12 },
  field: { display: "flex", flexDirection: "column", gap: 6 },
  fieldLabel: { fontSize: 11, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.06em" },
  input: { minHeight: 40, borderRadius: 8, border: "1px solid #cbd5e1", padding: "8px 10px", fontSize: 13, color: "#0f172a", background: "#ffffff" },
  textarea: { minHeight: 76, borderRadius: 8, border: "1px solid #cbd5e1", padding: "10px 12px", fontSize: 13, color: "#0f172a", background: "#ffffff", resize: "vertical" },
  workflowActions: { display: "flex", gap: 10, flexWrap: "wrap", marginTop: 14 },
  badge: (status) => ({
    display: "inline-flex",
    alignItems: "center",
    padding: "5px 10px",
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 700,
    background:
      status === "SUBMITTED" ? "#dcfce7"
        : status === "INACTIVATED" ? "#fee2e2"
          : status === "EXPORTED_TO_BATCH" ? "#dbeafe"
            : status === "READY_TO_EXPORT" ? "#fef3c7"
              : status === "CLOSED" ? "#e0f2fe"
                : "#e2e8f0",
    color:
      status === "SUBMITTED" ? "#166534"
        : status === "INACTIVATED" ? "#991b1b"
          : status === "EXPORTED_TO_BATCH" ? "#1d4ed8"
            : status === "READY_TO_EXPORT" ? "#92400e"
              : status === "CLOSED" ? "#0f766e"
                : "#334155",
  }),
  message: (tone) => ({
    marginTop: 12,
    padding: "10px 12px",
    borderRadius: 8,
    fontSize: 13,
    border: `1px solid ${tone === "error" ? "#fecaca" : "#bbf7d0"}`,
    background: tone === "error" ? "#fef2f2" : "#f0fdf4",
    color: tone === "error" ? "#991b1b" : "#166534",
  }),
  timestampList: { display: "grid", gap: 6, marginTop: 12, fontSize: 12, color: "#475569" },
  checkboxRow: { display: "inline-flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 600, color: "#334155" },
  miniLink: { padding: "6px 10px", borderRadius: 999, border: "1px solid #0d9488", background: "transparent", color: "#0d9488", fontSize: 12, fontWeight: 700, cursor: "pointer" },
};

const REPORT_TITLE_BY_TIMEPOINT = {
  ADMISSION: "HOPE REPORT - Admission",
  HUV1: "HOPE REPORT - HUV1",
  HUV2: "HOPE REPORT - HUV2",
  DISCHARGE: "HOPE REPORT - Discharge",
};

const STATUS_LABELS = {
  OPEN: "Open",
  CLOSED: "Closed",
  READY_TO_EXPORT: "Ready to export",
  EXPORTED_TO_BATCH: "Exported to batch",
  SUBMITTED: "Submitted",
  INACTIVATED: "Inactivated",
};

function formatDateTime(value) {
  if (!value) return "N/A";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString();
}

function mergeWorkflowIntoFormData(formData, workflow) {
  const merged = { ...(formData || {}) };
  const finalization = { ...(merged.finalization || {}) };
  finalization.hopeSubmissionNumber = workflow?.submissionNumber || "";
  finalization.hopeAlreadySubmitted = Boolean(workflow?.alreadySubmitted);
  merged.finalization = finalization;
  return merged;
}

export default function HopeReport({
  formData = {},
  patient = defaultPatient,
  agency,
  onBack,
  timepoint = "ADMISSION",
  assessmentMeta = {},
  discharge = null,
  onNavigateToSection,
}) {
  const { mode } = useThemeMode();
  const colors = getChartColors(mode);
  const normalizedTimepoint = String(timepoint || "ADMISSION").toUpperCase();
  const [workflow, setWorkflow] = useState(assessmentMeta?.hopeWorkflow || null);
  const [batchId, setBatchId] = useState(assessmentMeta?.hopeWorkflow?.exportBatchId || "");
  const [submissionNumber, setSubmissionNumber] = useState(assessmentMeta?.hopeWorkflow?.submissionNumber || "");
  const [alreadySubmitted, setAlreadySubmitted] = useState(Boolean(assessmentMeta?.hopeWorkflow?.alreadySubmitted));
  const [unlockReason, setUnlockReason] = useState("");
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setWorkflow(assessmentMeta?.hopeWorkflow || null);
    setBatchId(assessmentMeta?.hopeWorkflow?.exportBatchId || "");
    setSubmissionNumber(assessmentMeta?.hopeWorkflow?.submissionNumber || "");
    setAlreadySubmitted(Boolean(assessmentMeta?.hopeWorkflow?.alreadySubmitted));
  }, [assessmentMeta]);

  const mergedFormData = useMemo(() => mergeWorkflowIntoFormData(formData, workflow), [formData, workflow]);
  const report = useMemo(
    () => mapRnIcaToHopeReport(mergedFormData, patient, agency, {
      timepoint: normalizedTimepoint,
      assessmentMeta: { ...assessmentMeta, hopeWorkflow: workflow || assessmentMeta?.hopeWorkflow || null },
      discharge,
    }),
    [assessmentMeta, agency, mergedFormData, normalizedTimepoint, patient, workflow, discharge]
  );

  const locked = Boolean(assessmentMeta?.locked);
  const assessmentId = assessmentMeta?.assessmentId;
  const status = workflow?.status || "OPEN";
  const workflowBlocked = !assessmentId || !locked;
  const legacyBlocked = report.legacyReviewRequired.required;

  async function runAction(action, successMessage) {
    if (!assessmentId) return;
    setBusy(true);
    setMessage(null);
    try {
      const result = await action();
      setWorkflow(result.hopeWorkflow);
      if (result.hopeWorkflow?.exportBatchId) setBatchId(result.hopeWorkflow.exportBatchId);
      setSubmissionNumber(result.hopeWorkflow?.submissionNumber || "");
      setAlreadySubmitted(Boolean(result.hopeWorkflow?.alreadySubmitted));
      setMessage({ tone: "success", text: successMessage });
    } catch (error) {
      setMessage({ tone: "error", text: error instanceof Error ? error.message : "Unable to update HOPE workflow." });
    } finally {
      setBusy(false);
    }
  }

  const renderActionButton = (label, onClick, disabled = false, variant = "primary") => (
    <button
      type="button"
      style={disabled ? styles.disabledButton(colors) : (variant === "secondary" ? styles.secondaryButton(colors) : styles.primaryButton(colors))}
      onClick={onClick}
      disabled={disabled}
    >
      {label}
    </button>
  );

  return (
    <div style={styles.page(colors)}>
      <style>{`@media print { .hope-report-actions { display: none !important; } body { background: #fff !important; } }`}</style>
      <div className="hope-report-actions" style={styles.actions}>
        <div style={styles.buttonRow}>
          {onBack ? <button type="button" style={styles.secondaryButton(colors)} onClick={onBack}>Back to RN Assessment</button> : null}
          <button
            type="button"
            style={legacyBlocked ? styles.disabledButton(colors) : styles.primaryButton(colors)}
            onClick={() => window.print()}
            disabled={legacyBlocked}
            title={legacyBlocked ? "Blocked: complete HOPE Legacy Review before printing/submission" : undefined}
          >
            Print HOPE Report
          </button>
        </div>
      </div>

      <div style={styles.card(colors)}>
        <div style={styles.paper}>
          <div style={styles.headerRow}>
            <div style={styles.headerMeta}>
              <BrandLogo variant="dark" style={styles.logo} />
              <div>
                <div style={styles.title}>{report.agency.name}</div>
                <div style={styles.subtitle}>{report.agency.address} | Tel: {report.agency.phone} | Fax: {report.agency.fax}</div>
              </div>
            </div>
            <label style={styles.checkboxRow}>
              <input
                type="checkbox"
                checked={Boolean(workflow?.inactivated)}
                disabled={workflowBlocked || busy}
                onChange={(event) => runAction(
                  () => patchRnicaHopeInactivation(assessmentId, event.target.checked),
                  event.target.checked ? "HOPE report inactivated." : "HOPE report reactivated."
                )}
              />
              Check here to Inactivate
            </label>
          </div>

          <div style={{ ...styles.title, fontSize: 22, marginBottom: 16 }}>{REPORT_TITLE_BY_TIMEPOINT[normalizedTimepoint] || REPORT_TITLE_BY_TIMEPOINT.ADMISSION}</div>
          <div style={{ ...styles.patientLine, marginBottom: 8 }}>Patient Name: {report.patientName}</div>

          <div className="hope-report-actions" style={styles.workflowPanel}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              <div>
                <div style={styles.fieldLabel}>Workflow status</div>
                <div style={styles.badge(status)}>{STATUS_LABELS[status] || status}</div>
              </div>
              <div style={{ fontSize: 12, color: "#475569" }}>
                Clinical lock: <strong>{locked ? "Locked" : "Draft / unlocked"}</strong>
              </div>
            </div>

            <div style={styles.workflowGrid}>
              <div style={styles.field}>
                <span style={styles.fieldLabel}>Export batch ID</span>
                <input
                  value={batchId}
                  onChange={(event) => setBatchId(event.target.value)}
                  placeholder="Optional batch reference"
                  style={styles.input}
                  disabled={workflowBlocked || busy}
                />
              </div>
              <div style={styles.field}>
                <span style={styles.fieldLabel}>Submission number</span>
                <input
                  value={submissionNumber}
                  onChange={(event) => setSubmissionNumber(event.target.value)}
                  placeholder="CMS / batch submission number"
                  style={styles.input}
                  disabled={workflowBlocked || busy}
                />
              </div>
              <div style={{ ...styles.field, justifyContent: "flex-end" }}>
                <label style={styles.checkboxRow}>
                  <input
                    type="checkbox"
                    checked={alreadySubmitted}
                    disabled={workflowBlocked || busy}
                    onChange={(event) => setAlreadySubmitted(event.target.checked)}
                  />
                  Already submitted
                </label>
              </div>
              <div style={styles.field}>
                <span style={styles.fieldLabel}>Unlock reason</span>
                <textarea
                  value={unlockReason}
                  onChange={(event) => setUnlockReason(event.target.value)}
                  placeholder="Required only when reopening the HOPE workflow."
                  style={styles.textarea}
                  disabled={workflowBlocked || busy}
                />
              </div>
            </div>

            <div style={styles.workflowActions}>
              {renderActionButton("Close", () => runAction(() => closeRnicaHopeWorkflow(assessmentId), "HOPE report closed."), workflowBlocked || busy || legacyBlocked || status === "INACTIVATED")}
              {renderActionButton("Ready to Export", () => runAction(() => readyRnicaHopeWorkflow(assessmentId), "HOPE report marked ready to export."), workflowBlocked || busy || legacyBlocked || status === "INACTIVATED")}
              {renderActionButton("Export to Batch", () => runAction(() => exportRnicaHopeWorkflow(assessmentId, batchId), "HOPE report exported to batch."), workflowBlocked || busy || legacyBlocked || status === "INACTIVATED")}
              {renderActionButton("Save Submission Tracking", () => runAction(
                () => patchRnicaHopeSubmission(assessmentId, { hopeSubmissionNumber: submissionNumber || null, hopeAlreadySubmitted: alreadySubmitted }),
                "HOPE submission tracking updated."
              ), workflowBlocked || busy || status === "INACTIVATED")}
              {renderActionButton("Unlock", () => runAction(() => unlockRnicaHopeWorkflow(assessmentId, unlockReason), "HOPE workflow reopened."), workflowBlocked || busy || !unlockReason.trim(), "secondary")}
            </div>

            <div style={styles.timestampList}>
              <div>Closed: {formatDateTime(workflow?.closedAt)}</div>
              <div>Ready to export: {formatDateTime(workflow?.readyAt)}</div>
              <div>Exported to batch: {formatDateTime(workflow?.exportedToBatchAt)}{workflow?.exportBatchId ? ` (${workflow.exportBatchId})` : ""}</div>
              <div>Submitted: {formatDateTime(workflow?.submittedAt)}{workflow?.submissionNumber ? ` (${workflow.submissionNumber})` : ""}</div>
              <div>Inactivated: {formatDateTime(workflow?.inactivatedAt)}</div>
              <div>Last unlock: {formatDateTime(workflow?.unlockedAt)}{workflow?.unlockReason ? ` — ${workflow.unlockReason}` : ""}</div>
            </div>

            {workflowBlocked ? <div style={styles.message("error")}>Lock the assessment first to use HOPE workflow controls.</div> : null}
            {legacyBlocked ? <div style={styles.message("error")}>Legacy HOPE review items must be completed before close/export actions are allowed.</div> : null}
            {message ? <div style={styles.message(message.tone)}>{message.text}</div> : null}
          </div>

          {report.legacyReviewRequired.required && (
            <div style={styles.legacyBanner}>
              <div style={styles.legacyTitle}>HOPE Legacy Review Required</div>
              <div style={styles.legacyText}>
                This assessment predates HOPE discussion-status tracking. Review {report.legacyReviewRequired.items.join(", ")} before submission.
              </div>
            </div>
          )}

          <div style={styles.sfvBanner(report.sfvStatus.required)}>
            <div style={styles.sfvTitle(report.sfvStatus.required)}>
              {report.sfvStatus.required ? "SFV Required" : "SFV Status"}
            </div>
            <div style={styles.sfvText}>
              {report.sfvStatus.required
                ? `${report.sfvStatus.statusLabel} - Triggered by: ${report.sfvStatus.triggeredSymptoms.join(", ")}.${report.sfvStatus.dueDate ? ` Due within 2 calendar days of screening (${report.sfvStatus.dueDate.replace(/^(\d{4})-(\d{2})-(\d{2})$/, "$2/$3/$1")}).` : ""}`
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
              {section.items.map((item) => {
                const medLink = MED_ORDER_LINKS[item.code];
                return (
                  <div key={`${item.code}-${item.label}`} style={styles.item}>
                    <div style={styles.codeRow}>
                      <div style={styles.codeLine}>{item.code}. {item.label}</div>
                      {medLink && onNavigateToSection ? (
                        <button type="button" style={styles.miniLink} onClick={() => onNavigateToSection(medLink.section)}>
                          {medLink.label}
                        </button>
                      ) : null}
                    </div>
                    <div style={styles.entryGrid}>
                      {(item.entries || []).map((entry, index) => (
                        <div key={`${item.code}-${index}`} style={styles.entry}>
                          <div style={styles.entryLabel}>{entry.label}</div>
                          <div style={styles.entryValue}>{entry.value}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
