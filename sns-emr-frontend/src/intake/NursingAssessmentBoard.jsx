import React, { useEffect, useMemo, useState } from "react";
import RNICA from "../components/RNICA";
import { fetchPatientSummary } from "../api/patientCharts";
import { getCurrentUser } from "../api/session";
import { defaultPatient } from "./ConsentNotifications";
import HopeReport from "./HopeReport";
import { useRnIcaCommandWorkspace } from "../features/rnIcaCommandWorkspace";
import "./NursingAssessmentBoard.css";

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
  buttonRow: { display: "flex", gap: 10, flexWrap: "wrap" },
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
  secondaryButton: {
    padding: "11px 18px",
    borderRadius: 10,
    border: "1px solid #10B7A2",
    background: "transparent",
    color: "#5EEAD4",
    fontSize: 13,
    fontWeight: 700,
    cursor: "pointer",
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

function mapSummaryToPatient(summary) {
  if (!summary?.patient) return defaultPatient;
  const patient = summary.patient;
  const fullName = String(patient.full_name || patient.name || "").trim();
  const parts = fullName.split(/\s+/).filter(Boolean);
  const lastName = parts.length > 1 ? parts[parts.length - 1] : (parts[0] || defaultPatient.lastName);
  const firstName = parts.length > 1 ? parts.slice(0, -1).join(" ") : defaultPatient.firstName;
  return {
    ...defaultPatient,
    firstName,
    lastName,
    mrn: patient.mrn || defaultPatient.mrn,
    dob: patient.dob || defaultPatient.dob,
    age: patient.age || defaultPatient.age,
    sex: patient.sex || defaultPatient.sex,
    payer: patient.payer || defaultPatient.payer,
    primaryPayerType: patient.primary_payer_type || "",
    secondaryPayerType: patient.secondary_payer_type || "",
    status: patient.status || defaultPatient.status,
    socDate: patient.soc_date || patient.hospice_election_date || defaultPatient.socDate,
    benefitPeriod: patient.benefit_period || defaultPatient.benefitPeriod,
  };
}

export default function NursingAssessmentBoard({ patientId = "" }) {
  const { enabled: workspacePilot, disable: exitWorkspacePilot } = useRnIcaCommandWorkspace();
  const storageKey = useMemo(() => "sns-emr:ica-complete:rn:" + (patientId || "unknown-patient"), [patientId]);
  const [initialComplete, setInitialComplete] = useState(() => localStorage.getItem(storageKey) === "true");
  const [view, setView] = useState("assessment");
  const [reportFormData, setReportFormData] = useState(null);
  const [patientSummary, setPatientSummary] = useState(null);

  useEffect(() => {
    setInitialComplete(localStorage.getItem(storageKey) === "true");
  }, [storageKey]);

  useEffect(() => {
    if (initialComplete && view === "report") {
      setView("assessment");
    }
  }, [initialComplete, view]);

  useEffect(() => {
    let mounted = true;
    if (!patientId) {
      setPatientSummary(null);
      return () => {
        mounted = false;
      };
    }
    fetchPatientSummary(patientId)
      .then((summary) => {
        if (mounted) setPatientSummary(summary);
      })
      .catch(() => {
        if (mounted) setPatientSummary(null);
      });
    return () => {
      mounted = false;
    };
  }, [patientId]);

  const patient = useMemo(() => mapSummaryToPatient(patientSummary), [patientSummary]);
  const agency = useMemo(() => ({
    name: getCurrentUser()?.tenant_name || "Hospice Agency",
    address: "Agency Address",
    phone: "(000) 000-0000",
    fax: "(000) 000-0001",
  }), []);

  const markInitialComplete = () => {
    localStorage.setItem(storageKey, "true");
    setInitialComplete(true);
    setView("assessment");
  };

  const resetToInitial = () => {
    localStorage.removeItem(storageKey);
    setInitialComplete(false);
  };

  return (
    <div
      className={workspacePilot ? "clinical-command clinical-command--compact nursing-assessment-board--pilot" : undefined}
      style={workspacePilot ? undefined : styles.shell}
    >
      {workspacePilot ? (
        <div className="nursing-assessment-board__pilot-header">
          <div className="nursing-assessment-board__pilot-copy">
            <span>{initialComplete ? "Ongoing assessment" : "Initial admission assessment"}</span>
            <h2>{initialComplete ? "Comprehensive Nursing Assessment" : "RN Initial Comprehensive Assessment"}</h2>
            <p>
              {initialComplete
                ? "Document an update or recertification assessment using the shared clinical workspace."
                : "Complete the initial assessment; the HOPE report remains a read-only harvest of RN documentation."}
            </p>
          </div>
          <div className="nursing-assessment-board__pilot-actions">
            {!initialComplete && (
              <button type="button" onClick={() => setView((current) => current === "report" ? "assessment" : "report")}>
                {view === "report" ? "Return to RN Assessment" : "View HOPE Report"}
              </button>
            )}
            {!initialComplete && (
              <button type="button" onClick={markInitialComplete}>Mark Initial Assessment Complete</button>
            )}
          </div>
        </div>
      ) : (
        <div style={styles.card}>
          <div>
            <div style={styles.eyebrow}>{initialComplete ? "Ongoing assessment" : "Initial admission assessment"}</div>
            <h2 style={styles.title}>{initialComplete ? "Comprehensive Nursing Assessment" : "RN Initial Comprehensive Assessment"}</h2>
            <div style={styles.description}>
              {initialComplete
                ? "Use the toggle inside the assessment to document either an Update Assessment or a Recertification Assessment."
                : "Complete the full initial comprehensive assessment first. Use View HOPE Report to review the read-only CMS harvest from the RN ICA before printing or submission."}
            </div>
          </div>
          <div style={styles.buttonRow}>
            {!initialComplete && (
              <button type="button" style={styles.secondaryButton} onClick={() => setView((current) => current === "report" ? "assessment" : "report")}>
                {view === "report" ? "Return to RN Assessment" : "View HOPE Report"}
              </button>
            )}
            {!initialComplete && (
              <button type="button" style={styles.primaryButton} onClick={markInitialComplete}>
                Mark Initial Comprehensive Assessment Complete
              </button>
            )}
          </div>
        </div>
      )}

      {!initialComplete && view === "report" ? (
        <HopeReport formData={reportFormData || {}} patient={patient} agency={agency} onBack={() => setView("assessment")} />
      ) : (
        <div style={{ width: "100%", minWidth: 0, overflowX: "hidden" }}>
          <RNICA
            patientId={patientId}
            mode={initialComplete ? "ongoing" : "ica"}
            onFormDataChange={setReportFormData}
            workspacePilot={workspacePilot}
            onExitWorkspacePilot={exitWorkspacePilot}
          />
        </div>
      )}

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
