import React, { useEffect, useMemo, useState } from "react";
import RNICA from "../components/RNICA";
import { fetchPatientSummary } from "../api/patientCharts";
import { getCurrentUser } from "../api/session";
import { fetchHopeUpdateStatus, getRnicaAdmissionStatus, listRnicaAssessmentsByPatientType } from "../api/icaAssessments";
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
  historyCard: {
    margin: "0 12px 12px",
    padding: "14px 16px",
    background: "#111827",
    border: "1px solid #1F2937",
    borderRadius: 12,
    color: "#E2E8F0",
  },
  historyHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap", marginBottom: 12 },
  historyTableWrap: { overflowX: "auto" },
  historyTable: { width: "100%", borderCollapse: "collapse", minWidth: 680 },
  historyTh: { textAlign: "left", padding: "10px 12px", fontSize: 11, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.08em", borderBottom: "1px solid #1F2937" },
  historyTd: { padding: "10px 12px", fontSize: 12.5, color: "#E2E8F0", borderBottom: "1px solid #1F2937", verticalAlign: "top" },
  historyMeta: { fontSize: 11.5, color: "#94A3B8", marginTop: 4 },
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
};

function formatHistoryDate(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return parsed.toLocaleDateString([], { month: "2-digit", day: "2-digit", year: "numeric" });
}

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

export default function NursingAssessmentBoard({ patientId = "", onNavigateToSection = undefined, selectedAssessmentId: externallySelectedAssessmentId = null }) {
  const { enabled: workspacePilot, disable: exitWorkspacePilot } = useRnIcaCommandWorkspace();
  // Whether this patient's *current* admission has already completed its
  // one-time RN Initial Comprehensive Assessment (RNICA). This used to be
  // a client-only localStorage flag the RN could flip manually (a "Mark
  // Initial Assessment Complete" button) -- that let a still-in-progress,
  // unlocked RN ICA be mislabeled/switched into "ongoing" Update/Recert
  // mode, and could be bypassed entirely by clearing browser storage or
  // opening the chart on another device. It is now derived solely from
  // the backend (GET /visits/rnica/admission-status/{patientId}), which
  // only reports true once the initial RN ICA is actually locked/signed
  // for the current admission. null = still loading (treated as "not yet
  // ongoing" so the initial assessment renders by default).
  const [initialComplete, setInitialComplete] = useState(null);
  const [view, setView] = useState("assessment");
  const [reportFormData, setReportFormData] = useState(null);
  const [patientSummary, setPatientSummary] = useState(null);
  const [historyRecords, setHistoryRecords] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(null);

  useEffect(() => {
    let mounted = true;
    if (!patientId) {
      setInitialComplete(null);
      return () => {
        mounted = false;
      };
    }
    getRnicaAdmissionStatus(patientId)
      .then((status) => {
        if (mounted) setInitialComplete(Boolean(status?.initialAssessmentComplete));
      })
      .catch(() => {
        if (mounted) setInitialComplete(false);
      });
    return () => {
      mounted = false;
    };
  }, [patientId]);

  useEffect(() => {
    let mounted = true;
    if (!patientId) {
      setHistoryRecords([]);
      setSelectedAssessmentId(null);
      setHistoryError("");
      setHistoryLoading(false);
      return () => {
        mounted = false;
      };
    }
    setHistoryLoading(true);
    setHistoryError("");
    Promise.all([
      listRnicaAssessmentsByPatientType(patientId, { assessmentType: "RNICA" }),
      listRnicaAssessmentsByPatientType(patientId, { assessmentType: "UPDATE" }),
      listRnicaAssessmentsByPatientType(patientId, { assessmentType: "RECERT" }),
      fetchHopeUpdateStatus(patientId).catch(() => null),
    ])
      .then(([admissionResult, updateResult, recertResult, hopeStatus]) => {
        if (!mounted) return;
        const huv1Id = hopeStatus?.huv1?.assessment?.assessmentId || null;
        const huv2Id = hopeStatus?.huv2?.assessment?.assessmentId || null;
        const merged = [
          ...(admissionResult?.assessments || []),
          ...(updateResult?.assessments || []),
          ...(recertResult?.assessments || []),
        ]
          .map((item) => {
            const assessmentType = String(item.assessmentType || "").toUpperCase();
            let label = assessmentType === "RNICA"
              ? "RNICA Admission"
              : assessmentType === "RECERT"
                ? "RN Recert Assessment"
                : "Update Assessment";
            if (item.assessmentId === huv1Id) label = "Update Assessment (HUV1)";
            if (item.assessmentId === huv2Id) label = "Update Assessment (HUV2)";
            return { ...item, assessmentLabel: label };
          })
          .sort((a, b) => String(a.visitDate || a.createdAt || "").localeCompare(String(b.visitDate || b.createdAt || "")));
        setHistoryRecords(merged);
        setSelectedAssessmentId((current) => {
          if (current && merged.some((item) => item.assessmentId === current)) return current;
          return merged[merged.length - 1]?.assessmentId || null;
        });
      })
      .catch((error) => {
        if (!mounted) return;
        setHistoryRecords([]);
        setHistoryError(error?.message || "Unable to load nursing assessment history.");
      })
      .finally(() => {
        if (mounted) setHistoryLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [patientId]);

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

  const selectedRecord = useMemo(
    () => historyRecords.find((item) => item.assessmentId === selectedAssessmentId) || null,
    [historyRecords, selectedAssessmentId]
  );
  const activeMode = selectedRecord
    ? (String(selectedRecord.assessmentType || "").toUpperCase() === "RNICA" ? "ica" : "ongoing")
    : (initialComplete ? "ongoing" : "ica");
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
          </div>
        </div>
      ) : (
        <div style={styles.card}>
          <div>
            <div style={styles.eyebrow}>{initialComplete ? "Ongoing assessment" : "Initial admission assessment"}</div>
            <h2 style={styles.title}>{initialComplete ? "Comprehensive Nursing Assessment" : "RN Initial Comprehensive Assessment"}</h2>
            <div style={styles.description}>
              {initialComplete
                ? "The RN Initial Comprehensive Assessment for this admission is complete and locked. Use the toggle inside the assessment to document either an Update Assessment or a Recertification Assessment."
                : "Complete the full initial comprehensive assessment first. Use View HOPE Report to review the read-only CMS harvest from the RN ICA before printing or submission."}
            </div>
          </div>
          <div style={styles.buttonRow}>
            {!initialComplete && (
              <button type="button" style={styles.secondaryButton} onClick={() => setView((current) => current === "report" ? "assessment" : "report")}>
                {view === "report" ? "Return to RN Assessment" : "View HOPE Report"}
              </button>
            )}
          </div>
        </div>
      )}

      <div style={styles.historyCard}>
        <div style={styles.historyHeader}>
          <div>
            <div style={styles.eyebrow}>Nursing document history</div>
            <div style={{ fontSize: 13, color: "#94A3B8", lineHeight: 1.5 }}>
              Real RNICA-family records for this patient. Admission, HUV1/HUV2, and future RN recert/update records appear here.
            </div>
          </div>
          <span style={styles.smallBadge("teal")}>{historyRecords.length} record{historyRecords.length === 1 ? "" : "s"}</span>
        </div>
        {historyLoading ? (
          <div style={{ fontSize: 13, color: "#94A3B8" }}>Loading nursing history…</div>
        ) : historyError ? (
          <div style={{ fontSize: 13, color: "#FCA5A5" }}>{historyError}</div>
        ) : historyRecords.length === 0 ? (
          <div style={{ fontSize: 13, color: "#94A3B8" }}>No nursing assessments are on file for this patient yet.</div>
        ) : (
          <div style={styles.historyTableWrap}>
            <table style={styles.historyTable}>
              <thead>
                <tr>
                  <th style={styles.historyTh}>Assessment</th>
                  <th style={styles.historyTh}>Type</th>
                  <th style={styles.historyTh}>Status</th>
                  <th style={styles.historyTh}>Date</th>
                  <th style={styles.historyTh}>Action</th>
                </tr>
              </thead>
              <tbody>
                {historyRecords.map((record) => (
                  <tr key={record.assessmentId}>
                    <td style={styles.historyTd}>
                      <div style={{ fontWeight: 700 }}>{record.assessmentLabel}</div>
                      <div style={styles.historyMeta}>{record.assessmentId}</div>
                    </td>
                    <td style={styles.historyTd}>{record.assessmentType}</td>
                    <td style={styles.historyTd}>
                      <span style={styles.smallBadge(statusTone(record.status))}>{String(record.status || "DRAFT").replaceAll("_", " ")}</span>
                    </td>
                    <td style={styles.historyTd}>{formatHistoryDate(record.visitDate || record.createdAt)}</td>
                    <td style={styles.historyTd}>
                      <button type="button" style={styles.secondaryButton} onClick={() => setSelectedAssessmentId(record.assessmentId)}>
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

      {!initialComplete && view === "report" ? (
        <HopeReport
          formData={reportFormData || {}}
          patient={patient}
          agency={agency}
          onBack={() => setView("assessment")}
          onNavigateToSection={onNavigateToSection}
          assessmentMeta={{ locked: false }}
        />
      ) : (
        <div style={{ width: "100%", minWidth: 0, overflowX: "hidden" }}>
          <RNICA
            patientId={patientId}
            assessmentId={selectedRecord?.assessmentId}
            mode={activeMode}
            onFormDataChange={setReportFormData}
            workspacePilot={workspacePilot}
            onExitWorkspacePilot={exitWorkspacePilot}
            onNavigateToSection={onNavigateToSection}
          />
        </div>
      )}
    </div>
  );
}
