import React, { useEffect, useMemo, useState } from "react";
import SCICA from "../components/SCICA";
import { listScicaAssessmentsByPatient } from "../api/icaAssessments";

const styles = {
  shell: { background: "#0F172A", paddingBottom: 16 },
  card: {
    margin: "12px",
    padding: "16px 18px",
    background: "#111827",
    border: "1px solid #1F2937",
    borderLeft: "4px solid #0D9488",
    borderRadius: 12,
    boxShadow: "0 10px 24px rgba(15, 23, 42, 0.18)",
    color: "#E2E8F0",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 16,
    flexWrap: "wrap",
  },
  eyebrow: { fontSize: 11, fontWeight: 800, letterSpacing: "0.08em", color: "#5EEAD4", textTransform: "uppercase", marginBottom: 6 },
  title: { margin: 0, fontSize: 20, fontWeight: 700, color: "#F8FAFC" },
  description: { marginTop: 6, fontSize: 13, lineHeight: 1.5, color: "#94A3B8", maxWidth: 760 },
  primaryButton: {
    padding: "11px 18px",
    borderRadius: 10,
    border: "none",
    background: "linear-gradient(135deg, #0D9488 0%, #10B7A2 100%)",
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: 700,
    cursor: "pointer",
    boxShadow: "0 10px 22px rgba(13, 148, 136, 0.28)",
  },
  historyCard: { margin: "0 12px 12px", padding: "14px 16px", background: "#111827", border: "1px solid #1F2937", borderRadius: 12, color: "#E2E8F0" },
  historyTableWrap: { overflowX: "auto" },
  historyTable: { width: "100%", borderCollapse: "collapse", minWidth: 620 },
  historyTh: { textAlign: "left", padding: "10px 12px", fontSize: 11, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.08em", borderBottom: "1px solid #1F2937" },
  historyTd: { padding: "10px 12px", fontSize: 12.5, color: "#E2E8F0", borderBottom: "1px solid #1F2937", verticalAlign: "top" },
  smallBadge: (tone = "teal") => ({
    display: "inline-flex",
    alignItems: "center",
    borderRadius: 999,
    padding: "4px 10px",
    fontSize: 10,
    fontWeight: 800,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    backgroundColor: tone === "amber" ? "rgba(245, 158, 11, 0.16)" : tone === "green" ? "rgba(16, 185, 129, 0.16)" : "rgba(16, 183, 162, 0.16)",
    color: tone === "amber" ? "#FBBF24" : tone === "green" ? "#6EE7B7" : "#5EEAD4",
    border: `1px solid ${tone === "amber" ? "rgba(245, 158, 11, 0.28)" : tone === "green" ? "rgba(16, 185, 129, 0.28)" : "rgba(16, 183, 162, 0.28)"}`,
  }),
};

function formatHistoryDate(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return parsed.toLocaleDateString([], { month: "2-digit", day: "2-digit", year: "numeric" });
}

export default function SpiritualAssessmentBoard({ patientId = "", selectedAssessmentId: externallySelectedAssessmentId = null }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(null);

  useEffect(() => {
    let mounted = true;
    if (!patientId) {
      setRecords([]);
      setSelectedAssessmentId(null);
      setLoading(false);
      setError("");
      return () => {
        mounted = false;
      };
    }
    setLoading(true);
    setError("");
    listScicaAssessmentsByPatient(patientId)
      .then((result) => {
        if (!mounted) return;
        const items = [...(result?.assessments || [])].sort((a, b) => String(a.visitDate || a.createdAt || "").localeCompare(String(b.visitDate || b.createdAt || "")));
        setRecords(items);
        setSelectedAssessmentId((current) => current && items.some((item) => item.assessmentId === current) ? current : (items[items.length - 1]?.assessmentId || null));
      })
      .catch((loadError) => {
        if (!mounted) return;
        setRecords([]);
        setError(loadError?.message || "Unable to load spiritual assessment history.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [patientId]);

  const selectedRecord = useMemo(
    () => records.find((item) => item.assessmentId === selectedAssessmentId) || null,
    [records, selectedAssessmentId]
  );
  const initialComplete = records.some((item) => item.locked);
  const statusTone = (status) => {
    const normalized = String(status || "").toUpperCase();
    if (normalized === "LOCKED") return "green";
    if (normalized === "DRAFT" || normalized === "IN_PROGRESS" || normalized === "PENDING") return "amber";
    return "teal";
  };

  useEffect(() => {
    if (!externallySelectedAssessmentId) return;
    setSelectedAssessmentId(externallySelectedAssessmentId);
  }, [externallySelectedAssessmentId]);

  return (
    <div style={styles.shell}>
      <div style={styles.card}>
        <div>
          <div style={styles.eyebrow}>{initialComplete ? "Ongoing assessment" : "Initial admission assessment"}</div>
          <h2 style={styles.title}>{initialComplete ? "Comprehensive Spiritual Assessment" : "SC Initial Comprehensive Assessment"}</h2>
          <div style={styles.description}>
            {initialComplete
              ? "Real spiritual assessment records for this patient are listed below and can be reopened directly."
              : "No locked spiritual assessment is on file yet. When one exists, it will appear below automatically."}
          </div>
        </div>
        <span style={styles.primaryButton}>{records.length} record{records.length === 1 ? "" : "s"}</span>
      </div>

      <div style={styles.historyCard}>
        {loading ? (
          <div style={{ fontSize: 13, color: "#94A3B8" }}>Loading spiritual history…</div>
        ) : error ? (
          <div style={{ fontSize: 13, color: "#FCA5A5" }}>{error}</div>
        ) : records.length === 0 ? (
          <div style={{ fontSize: 13, color: "#94A3B8" }}>No SC ICA records are on file for this patient yet.</div>
        ) : (
          <div style={styles.historyTableWrap}>
            <table style={styles.historyTable}>
              <thead>
                <tr>
                  <th style={styles.historyTh}>Assessment</th>
                  <th style={styles.historyTh}>Status</th>
                  <th style={styles.historyTh}>Date</th>
                  <th style={styles.historyTh}>Action</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.assessmentId}>
                    <td style={styles.historyTd}>
                      <div style={{ fontWeight: 700 }}>{record.assessmentType || "SC ICA"}</div>
                      <div style={{ fontSize: 11.5, color: "#94A3B8", marginTop: 4 }}>{record.assessmentId}</div>
                    </td>
                    <td style={styles.historyTd}>
                      <span style={styles.smallBadge(statusTone(record.status))}>{String(record.status || "DRAFT").replaceAll("_", " ")}</span>
                    </td>
                    <td style={styles.historyTd}>{formatHistoryDate(record.visitDate || record.createdAt)}</td>
                    <td style={styles.historyTd}>
                      <button type="button" style={styles.primaryButton} onClick={() => setSelectedAssessmentId(record.assessmentId)}>
                        Open
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <SCICA patientId={patientId} assessmentId={selectedRecord?.assessmentId} mode="ica" />
    </div>
  );
}
