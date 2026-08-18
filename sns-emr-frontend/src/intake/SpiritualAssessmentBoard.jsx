import React, { useEffect, useMemo, useState } from "react";
import SCICA from "../components/SCICA";

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
  resetRow: { display: "flex", justifyContent: "flex-end", padding: "0 16px" },
  resetButton: {
    border: "none",
    background: "transparent",
    color: "#5EEAD4",
    fontSize: 12,
    cursor: "pointer",
    textDecoration: "underline",
    padding: "6px 0",
  },
};

export default function SpiritualAssessmentBoard({ patientId = "" }) {
  const storageKey = useMemo(() => "sns-emr:ica-complete:sc:" + (patientId || "unknown-patient"), [patientId]);
  const [initialComplete, setInitialComplete] = useState(() => localStorage.getItem(storageKey) === "true");

  useEffect(() => {
    setInitialComplete(localStorage.getItem(storageKey) === "true");
  }, [storageKey]);

  const markInitialComplete = () => {
    localStorage.setItem(storageKey, "true");
    setInitialComplete(true);
  };

  const resetToInitial = () => {
    localStorage.removeItem(storageKey);
    setInitialComplete(false);
  };

  return (
    <div style={styles.shell}>
      <div style={styles.card}>
        <div>
          <div style={styles.eyebrow}>{initialComplete ? "Ongoing assessment" : "Initial admission assessment"}</div>
          <h2 style={styles.title}>{initialComplete ? "Comprehensive Spiritual Assessment" : "SC Initial Comprehensive Assessment"}</h2>
          <div style={styles.description}>
            {initialComplete
              ? "Use the toggle inside the assessment to document either an Update Assessment or a Recertification Assessment."
              : "Complete the full initial comprehensive assessment first. When ready, mark it complete to switch this patient to the ongoing comprehensive assessment workflow."}
          </div>
        </div>
        {!initialComplete && (
          <button type="button" style={styles.primaryButton} onClick={markInitialComplete}>
            Mark Initial Comprehensive Assessment Complete
          </button>
        )}
      </div>

      <SCICA patientId={patientId} mode={initialComplete ? "ongoing" : "ica"} />

      {initialComplete && (
        <div style={styles.resetRow}>
          <button type="button" style={styles.resetButton} onClick={resetToInitial}>
            Reset to Initial Assessment
          </button>
        </div>
      )}
    </div>
  );
}
