import React, { useEffect, useMemo, useState } from "react";
import RNICA from "../components/RNICA";
import { fetchPatientSummary } from "../api/patientCharts";
import { getCurrentUser } from "../api/session";
import { fetchHopeUpdateStatus, getRnicaAdmissionStatus, listRnicaAssessmentsByPatientType } from "../api/icaAssessments";
import { defaultPatient } from "./ConsentNotifications";
import HopeReport from "./HopeReport";
import { useRnIcaCommandWorkspace } from "../features/rnIcaCommandWorkspace";
import "./NursingAssessmentBoard.css";

// R3 (Owner Directive, "RNICA Update/HUV Creation Workflow", clarified by
// "OWNER CLARIFICATION — PRIMARY RULE: the trigger for an Update Assessment
// is clinical need, not calendar day"): the reasons below describe *why a
// comprehensive reassessment and Plan of Care review is clinically
// indicated right now* -- none of them reference a HOPE/HUV calendar
// window, because HOPE/HUV eligibility is an outcome the existing backend
// evaluates afterward, never the reason an RN starts the reassessment.
export const CHANGE_OF_CONDITION_REASONS = [
  { value: "NEW_SYMPTOM_OR_FINDING", label: "New symptom or finding" },
  { value: "WORSENING_SYMPTOM_OR_FINDING", label: "Worsening symptom or finding" },
  { value: "SEVERE_SYMPTOM_CONTINUED_MANAGEMENT", label: "Existing severe symptom requiring continued management" },
  { value: "INTERVENTION_INEFFECTIVE", label: "Current intervention appears ineffective" },
  { value: "FUNCTIONAL_STATUS_CHANGE", label: "Change in functional status" },
  { value: "COGNITION_BEHAVIOR_CHANGE", label: "Change in cognition or behavior" },
  { value: "INTAKE_HYDRATION_ELIMINATION_CHANGE", label: "Change in intake, hydration, or elimination" },
  { value: "SKIN_WOUND_CHANGE", label: "Change in skin or wound status" },
  { value: "HOSPITAL_ER_TRANSITION", label: "Hospital or emergency-care transition" },
  { value: "POC_REVIEW_NEEDED", label: "POC review needed before scheduled review" },
  { value: "OTHER", label: "Other" },
];

// Single, shared reason-label resolver (R3 Command Workspace parity
// repair, Owner Directive): both RNICA.jsx's classic banner and the
// Command Workspace's UpdateAssessmentContextBanner read
// `changeOfConditionContext.reasonLabel`, which is always produced here,
// never recomputed per-view.
export function reasonLabelFor(reasonCode) {
  return CHANGE_OF_CONDITION_REASONS.find((r) => r.value === reasonCode)?.label || reasonCode;
}

function pendingNewUpdateStorageKey(patientId) {
  return `sns.rnica.pendingNewUpdateAssessment.${patientId}`;
}

// Single, shared staging function used by BOTH entry points (the history
// panel's "New Update Assessment" button in this file, and the "Complete
// Update Assessment" action in VisitNotes.jsx). VisitNotes.jsx and this
// board are mounted as sibling tabs with no shared parent state available
// (PatientChart.jsx is not an authorized file for this change), so a
// sessionStorage handoff -- rather than a shared in-memory closure -- is
// the mechanism both entry points funnel through. This function owns all
// validation and the context shape; beginNewUpdateAssessment below is the
// single place that actually applies it to the RNICA workspace.
export function stageNewUpdateAssessmentRequest(patientId, {
  reasonCode,
  reasonDetail = "",
  source = "DIRECT_HISTORY_ACTION",
  sourceVisitType = null,
  originatingVisitId = null,
  originatingVisitDate = null,
} = {}) {
  if (!patientId) throw new Error("A patient is required to begin a new Update Assessment.");
  if (!reasonCode) throw new Error("Select a reason before starting the Update Assessment.");
  if (reasonCode === "OTHER" && !String(reasonDetail || "").trim()) {
    throw new Error('Enter a reason detail when "Other" is selected.');
  }
  const currentUser = getCurrentUser();
  const context = {
    source,
    reasonCode,
    reasonLabel: reasonLabelFor(reasonCode),
    reasonDetail: String(reasonDetail || "").trim() || null,
    sourceVisitType,
    originatingVisitId,
    originatingVisitDate,
    initiatedBy: currentUser?.id || currentUser?.full_name || currentUser?.name || null,
    initiatedAt: new Date().toISOString(),
  };
  try {
    sessionStorage.setItem(pendingNewUpdateStorageKey(patientId), JSON.stringify(context));
  } catch (err) {
    console.error("Unable to stage new Update Assessment request:", err);
  }
  return context;
}

export function consumeStagedNewUpdateAssessmentRequest(patientId) {
  if (!patientId) return null;
  const key = pendingNewUpdateStorageKey(patientId);
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;
    sessionStorage.removeItem(key);
    return JSON.parse(raw);
  } catch (err) {
    console.error("Unable to read staged new Update Assessment request:", err);
    return null;
  }
}

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
  const [historyReloadToken, setHistoryReloadToken] = useState(0);
  // R3: when set, RNICA renders a brand-new blank Update Assessment draft
  // instead of the patient's latest same-type record (the original
  // "no path to create a new Update assessment" defect). Cleared the
  // moment the draft receives its first persisted assessmentId.
  const [pendingNewAssessment, setPendingNewAssessment] = useState(null);
  const [rnicaInstanceKey, setRnicaInstanceKey] = useState(0);
  const [showReasonPicker, setShowReasonPicker] = useState(false);
  const [reasonCode, setReasonCode] = useState("");
  const [reasonDetail, setReasonDetail] = useState("");
  const [reasonError, setReasonError] = useState("");

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
  }, [patientId, historyReloadToken]);

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
  const activeMode = pendingNewAssessment
    ? "ongoing"
    : selectedRecord
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

  // R3: begin a brand-new Update Assessment draft -- used by both the
  // "New Update Assessment" button below and by a staged request handed
  // off from VisitNotes.jsx (see consumeStagedNewUpdateAssessmentRequest).
  // Opening a historical record (the existing "Open" action) is untouched
  // and continues to just set selectedAssessmentId.
  const beginNewUpdateAssessment = (context) => {
    setSelectedAssessmentId(null);
    setPendingNewAssessment(context);
    setRnicaInstanceKey((k) => k + 1);
  };

  // Pick up a "Complete Update Assessment" request staged from the Visit
  // Notes tab. VisitNotes.jsx and this board are sibling tabs with no
  // shared parent state (PatientChart.jsx is out of scope for this
  // change) and only one is mounted at a time, so this runs the moment an
  // RN switches into the Nursing Assessment tab after staging a request.
  useEffect(() => {
    if (!patientId) return;
    const staged = consumeStagedNewUpdateAssessmentRequest(patientId);
    if (staged) beginNewUpdateAssessment(staged);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  const handleOpenHistoricalRecord = (assessmentId) => {
    setPendingNewAssessment(null);
    setSelectedAssessmentId(assessmentId);
  };

  const handleRequestNewUpdateAssessment = () => {
    setReasonCode("");
    setReasonDetail("");
    setReasonError("");
    setShowReasonPicker(true);
  };

  const handleConfirmNewUpdateAssessment = () => {
    try {
      const context = stageNewUpdateAssessmentRequest(patientId, {
        reasonCode,
        reasonDetail,
        source: "DIRECT_HISTORY_ACTION",
      });
      beginNewUpdateAssessment(context);
      setShowReasonPicker(false);
      setReasonCode("");
      setReasonDetail("");
      setReasonError("");
    } catch (err) {
      setReasonError(err?.message || "Unable to start a new Update Assessment.");
    }
  };

  const handleAssessmentCreated = (newAssessmentId) => {
    setPendingNewAssessment(null);
    setSelectedAssessmentId(newAssessmentId);
    setHistoryReloadToken((t) => t + 1);
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

      <div
        className={workspacePilot ? "nursing-assessment-board__history" : undefined}
        style={workspacePilot ? undefined : styles.historyCard}
      >
        <div className={workspacePilot ? "nursing-assessment-board__history-header" : undefined} style={workspacePilot ? undefined : styles.historyHeader}>
          <div>
            <div className={workspacePilot ? "nursing-assessment-board__history-eyebrow" : undefined} style={workspacePilot ? undefined : styles.eyebrow}>Nursing document history</div>
            <div className={workspacePilot ? "nursing-assessment-board__history-desc" : undefined} style={workspacePilot ? undefined : { fontSize: 13, color: "#94A3B8", lineHeight: 1.5 }}>
              Real RNICA-family records for this patient. Admission, HUV1/HUV2, and future RN recert/update records appear here.
            </div>
          </div>
          {workspacePilot ? (
            <span className="nursing-assessment-board__history-badge">{historyRecords.length} record{historyRecords.length === 1 ? "" : "s"}</span>
          ) : (
            <span style={styles.smallBadge("teal")}>{historyRecords.length} record{historyRecords.length === 1 ? "" : "s"}</span>
          )}
          {initialComplete ? (
            <button
              type="button"
              style={workspacePilot ? undefined : styles.secondaryButton}
              onClick={handleRequestNewUpdateAssessment}
              title="Start a brand-new Update Assessment draft. Existing records are preserved and remain viewable/editable as before."
            >
              New Update Assessment
            </button>
          ) : null}
        </div>
        {showReasonPicker && (
          <div style={{ ...styles.card, display: "block", marginBottom: 12 }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>New Update Assessment — Change of Condition</div>
            <div style={{ fontSize: 12.5, color: "#94A3B8", marginBottom: 10 }}>
              Does the patient have a new condition, worsening condition, severe symptom requiring continued management,
              or another clinical change that may require review of the Plan of Care before the next scheduled review?
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
              {CHANGE_OF_CONDITION_REASONS.map((reason) => (
                <button
                  key={reason.value}
                  type="button"
                  onClick={() => setReasonCode(reason.value)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: 999,
                    border: reasonCode === reason.value ? "1px solid #10B7A2" : "1px solid #1F2937",
                    background: reasonCode === reason.value ? "rgba(16, 183, 162, 0.16)" : "transparent",
                    color: reasonCode === reason.value ? "#5EEAD4" : "#E2E8F0",
                    fontSize: 12, fontWeight: 600, cursor: "pointer",
                  }}
                >
                  {reason.label}
                </button>
              ))}
            </div>
            {reasonCode === "OTHER" && (
              <input
                type="text"
                value={reasonDetail}
                onChange={(e) => setReasonDetail(e.target.value)}
                placeholder="Describe the reason"
                style={{ width: "100%", padding: "8px 10px", borderRadius: 8, border: "1px solid #1F2937", background: "#0F172A", color: "#E2E8F0", marginBottom: 10 }}
              />
            )}
            {reasonError && <div style={{ color: "#FCA5A5", fontSize: 12, marginBottom: 10 }}>{reasonError}</div>}
            <div style={{ display: "flex", gap: 8 }}>
              <button type="button" style={styles.primaryButton} onClick={handleConfirmNewUpdateAssessment}>
                Start Update Assessment
              </button>
              <button type="button" style={styles.secondaryButton} onClick={() => setShowReasonPicker(false)}>
                Cancel
              </button>
            </div>
          </div>
        )}
        {historyLoading ? (
          <div className={workspacePilot ? "nursing-assessment-board__history-loading" : undefined} style={workspacePilot ? undefined : { fontSize: 13, color: "#94A3B8" }}>Loading nursing history…</div>
        ) : historyError ? (
          <div className={workspacePilot ? "nursing-assessment-board__history-error" : undefined} style={workspacePilot ? undefined : { fontSize: 13, color: "#FCA5A5" }}>{historyError}</div>
        ) : historyRecords.length === 0 ? (
          <div className={workspacePilot ? "nursing-assessment-board__history-empty" : undefined} style={workspacePilot ? undefined : { fontSize: 13, color: "#94A3B8" }}>No nursing assessments are on file for this patient yet.</div>
        ) : (
          <div className={workspacePilot ? "nursing-assessment-board__history-table-wrap" : undefined} style={workspacePilot ? undefined : styles.historyTableWrap}>
            <table className={workspacePilot ? "nursing-assessment-board__history-table" : undefined} style={workspacePilot ? undefined : styles.historyTable}>
              <thead>
                <tr>
                  <th style={workspacePilot ? undefined : styles.historyTh}>Assessment</th>
                  <th style={workspacePilot ? undefined : styles.historyTh}>Type</th>
                  <th style={workspacePilot ? undefined : styles.historyTh}>Status</th>
                  <th style={workspacePilot ? undefined : styles.historyTh}>Date</th>
                  <th style={workspacePilot ? undefined : styles.historyTh}>Action</th>
                </tr>
              </thead>
              <tbody>
                {historyRecords.map((record) => {
                  const tone = statusTone(record.status);
                  return (
                    <tr key={record.assessmentId}>
                      <td style={workspacePilot ? undefined : styles.historyTd}>
                        <div style={{ fontWeight: 700 }}>{record.assessmentLabel}</div>
                        <div className={workspacePilot ? "nursing-assessment-board__history-meta" : undefined} style={workspacePilot ? undefined : styles.historyMeta}>{record.assessmentId}</div>
                      </td>
                      <td style={workspacePilot ? undefined : styles.historyTd}>{record.assessmentType}</td>
                      <td style={workspacePilot ? undefined : styles.historyTd}>
                        {workspacePilot ? (
                          <span className={`nursing-assessment-board__history-badge${tone !== "teal" ? ` nursing-assessment-board__history-badge--${tone}` : ""}`}>
                            {String(record.status || "DRAFT").replaceAll("_", " ")}
                          </span>
                        ) : (
                          <span style={styles.smallBadge(tone)}>{String(record.status || "DRAFT").replaceAll("_", " ")}</span>
                        )}
                      </td>
                      <td style={workspacePilot ? undefined : styles.historyTd}>{formatHistoryDate(record.visitDate || record.createdAt)}</td>
                      <td style={workspacePilot ? undefined : styles.historyTd}>
                        {workspacePilot ? (
                          <button type="button" className="nursing-assessment-board__history-open-btn" onClick={() => handleOpenHistoricalRecord(record.assessmentId)}>
                            Open
                          </button>
                        ) : (
                          <button type="button" style={styles.secondaryButton} onClick={() => handleOpenHistoricalRecord(record.assessmentId)}>
                            Open
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
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
          patientId={patientId}
        />
      ) : (
        <div style={{ width: "100%", minWidth: 0, overflowX: "hidden" }}>
          <RNICA
            key={pendingNewAssessment ? `new-update-${rnicaInstanceKey}` : (selectedRecord?.assessmentId || "none")}
            patientId={patientId}
            assessmentId={pendingNewAssessment ? undefined : selectedRecord?.assessmentId}
            mode={activeMode}
            onFormDataChange={setReportFormData}
            workspacePilot={workspacePilot}
            onExitWorkspacePilot={exitWorkspacePilot}
            onNavigateToSection={onNavigateToSection}
            forceNewDraft={!!pendingNewAssessment}
            initialAssessmentType={pendingNewAssessment ? "update" : undefined}
            changeOfConditionContext={pendingNewAssessment}
            onAssessmentCreated={handleAssessmentCreated}
          />
        </div>
      )}
    </div>
  );
}
