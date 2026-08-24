import React, { useEffect, useMemo, useState } from "react";
import { getRnicaAssessmentByPatient } from "../api/icaAssessments";
import { fetchPatientSummary } from "../api/patientCharts";
import { getCurrentUser } from "../api/session";
import { useThemeMode } from "../theme/theme";
import { getChartColors } from "../theme/chartColors";
import { defaultPatient } from "./ConsentNotifications";
import HopeReport from "./HopeReport";
import mapRnIcaToHopeReport from "./hopeReportMapper";

const COMPLIANCE_SECTION_KEY = "compliance";
const SECTION_ITEMS = [
  { label: "LCD Eligibility", key: "lcd-eligibility" },
  { label: "HOPE - Admission", key: "hope-admission" },
  { label: "HOPE - HUV1", key: "hope-huv1" },
  { label: "HOPE - HUV2", key: "hope-huv2" },
  { label: "HOPE - Discharge", key: "hope-discharge" },
  { label: "Decline of Status", key: "decline-of-status" },
];

function formatDate(value) {
  if (!value) return "—";
  const normalized = String(value).slice(0, 10);
  const parts = normalized.split("-");
  if (parts.length === 3) return `${parts[1]}/${parts[2]}/${parts[0]}`;
  return value;
}

function addDays(value, days) {
  if (!value) return "";
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return "";
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

function humanizeKey(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
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

function buildHuvWindow(electionDate, startDay, endDay) {
  if (!electionDate) return null;
  const windowStart = addDays(electionDate, startDay);
  const windowEnd = addDays(electionDate, endDay);
  return windowStart && windowEnd ? `${formatDate(windowStart)} – ${formatDate(windowEnd)}` : null;
}

function isPresent(value) {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim().length > 0;
  return true;
}

export default function ComplianceHopeBoard({
  patientId = "",
  activeSection = COMPLIANCE_SECTION_KEY,
  onNavigateToSection = undefined,
}) {
  const { mode } = useThemeMode();
  const colors = getChartColors(mode);
  const [patientSummary, setPatientSummary] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    if (!patientId) {
      setPatientSummary(null);
      setAssessment(null);
      setError("");
      setLoading(false);
      return () => {
        mounted = false;
      };
    }

    setLoading(true);
    setError("");

    Promise.allSettled([
      getRnicaAssessmentByPatient(patientId),
      fetchPatientSummary(patientId),
    ])
      .then(([assessmentResult, summaryResult]) => {
        if (!mounted) return;

        const problems = [];

        if (assessmentResult.status === "fulfilled") {
          setAssessment(assessmentResult.value);
        } else {
          setAssessment(null);
          problems.push(assessmentResult.reason?.message || "Unable to load RN ICA data.");
        }

        if (summaryResult.status === "fulfilled") {
          setPatientSummary(summaryResult.value);
        } else {
          setPatientSummary(null);
          problems.push(summaryResult.reason?.message || "Unable to load patient summary.");
        }

        setError(problems.join(" "));
      })
      .finally(() => {
        if (mounted) setLoading(false);
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
  const formData = assessment?.formData || {};
  const hopeReport = useMemo(() => mapRnIcaToHopeReport(formData, patient, agency), [formData, patient, agency]);
  const selectedSection = SECTION_ITEMS.some((item) => item.key === activeSection) ? activeSection : COMPLIANCE_SECTION_KEY;
  const electionDate = patientSummary?.patient?.hospice_election_date || "";
  const huv1Window = buildHuvWindow(electionDate, 6, 15);
  const huv2Window = buildHuvWindow(electionDate, 16, 30);
  const diagnoses = formData.diagnoses || {};
  const ndsEligibility = diagnoses.ndsEligibility || {};
  const detectedDisease = ndsEligibility.detectedDisease || "";
  const criteriaAnswers = detectedDisease ? (ndsEligibility.criteriaAnswers?.[detectedDisease] || {}) : {};
  const criteriaFacts = detectedDisease ? (ndsEligibility.criteriaFacts?.[detectedDisease] || {}) : {};
  const criteriaAnswerCount = Object.values(criteriaAnswers).filter(isPresent).length;
  const criteriaFactCount = Object.values(criteriaFacts).filter(isPresent).length;
  const hasAssessment = Boolean(assessment?.assessmentId);

  const styles = {
    page: { backgroundColor: colors.bg, color: colors.text, minHeight: "100%", padding: 18, fontFamily: "'Inter', sans-serif" },
    stack: { display: "grid", gap: 16 },
    card: {
      backgroundColor: colors.card,
      border: `1px solid ${colors.border}`,
      borderRadius: 12,
      boxShadow: "0 12px 24px rgba(15, 23, 42, 0.08)",
      overflow: "hidden",
    },
    sectionHeader: {
      padding: "14px 18px",
      borderBottom: `1px solid ${colors.border}`,
      background: mode === "light"
        ? "linear-gradient(90deg, rgba(13,125,122,0.12), rgba(13,125,122,0.03))"
        : "linear-gradient(90deg, rgba(16,183,162,0.12), rgba(16,183,162,0.03))",
    },
    title: { margin: 0, fontSize: 19, fontWeight: 800, color: colors.white },
    subtitle: { marginTop: 6, fontSize: 13, lineHeight: 1.5, color: colors.label },
    body: { padding: 18 },
    summaryGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 },
    statusCard: {
      border: `1px solid ${colors.border}`,
      borderRadius: 12,
      padding: 16,
      backgroundColor: mode === "light" ? "#fbfefe" : "#162033",
      minHeight: 156,
      display: "flex",
      flexDirection: "column",
      gap: 8,
    },
    eyebrow: {
      fontSize: 11,
      fontWeight: 800,
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      color: colors.teal,
    },
    statusLead: { fontSize: 20, fontWeight: 800, color: colors.white, lineHeight: 1.2 },
    statusSub: { fontSize: 13, fontWeight: 700, color: colors.text },
    muted: { fontSize: 12.5, lineHeight: 1.5, color: colors.label },
    legacyBanner: {
      marginTop: 14,
      padding: 14,
      borderRadius: 10,
      border: `1px solid ${mode === "light" ? "#fecaca" : "#7f1d1d"}`,
      backgroundColor: mode === "light" ? "#fef2f2" : "rgba(127,29,29,0.25)",
      color: mode === "light" ? "#7f1d1d" : "#fecaca",
      fontSize: 12.5,
      lineHeight: 1.5,
    },
    navRow: { display: "flex", gap: 10, flexWrap: "wrap" },
    navButton: (active) => ({
      borderRadius: 999,
      padding: "9px 14px",
      border: `1px solid ${active ? colors.teal : colors.border}`,
      backgroundColor: active ? colors.tealBg : colors.card,
      color: active ? colors.teal : colors.text,
      cursor: "pointer",
      fontSize: 12.5,
      fontWeight: 700,
    }),
    detailGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 },
    infoTile: {
      border: `1px solid ${colors.border}`,
      borderRadius: 10,
      padding: 14,
      backgroundColor: mode === "light" ? "#f8fbfc" : "#152132",
    },
    label: {
      fontSize: 10.5,
      fontWeight: 800,
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      color: colors.label,
      marginBottom: 6,
    },
    value: { fontSize: 14, fontWeight: 700, color: colors.text, lineHeight: 1.45 },
    textPanel: {
      marginTop: 12,
      border: `1px solid ${colors.border}`,
      borderRadius: 10,
      padding: 14,
      backgroundColor: mode === "light" ? "#fcfefe" : "#121d2d",
      whiteSpace: "pre-wrap",
      lineHeight: 1.6,
      fontSize: 13,
      color: colors.text,
    },
    list: { display: "grid", gap: 10 },
    listItem: {
      display: "grid",
      gridTemplateColumns: "minmax(0, 1fr) auto",
      gap: 12,
      padding: "12px 14px",
      border: `1px solid ${colors.border}`,
      borderRadius: 10,
      backgroundColor: mode === "light" ? "#f8fbfc" : "#152132",
      alignItems: "center",
    },
    badge: (tone = "teal") => ({
      display: "inline-flex",
      alignItems: "center",
      borderRadius: 999,
      padding: "4px 10px",
      fontSize: 10,
      fontWeight: 800,
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      backgroundColor: tone === "amber" ? colors.amberBg : tone === "green" ? colors.greenBg : colors.tealBg,
      color: tone === "amber" ? colors.amber : tone === "green" ? colors.green : colors.teal,
    }),
    yesNoPill: (active) => ({
      display: "inline-flex",
      alignItems: "center",
      borderRadius: 999,
      padding: "4px 10px",
      fontSize: 11,
      fontWeight: 800,
      backgroundColor: active ? colors.greenBg : (mode === "light" ? "#eef2f7" : "#1b2738"),
      color: active ? colors.green : colors.label,
      border: `1px solid ${active ? colors.green : colors.border}`,
    }),
  };

  const renderPlaceholder = (title, description, extra = null) => (
    <div style={styles.card}>
      <div style={styles.sectionHeader}>
        <h3 style={styles.title}>{title}</h3>
        <div style={styles.subtitle}>{description}</div>
      </div>
      <div style={styles.body}>
        {extra}
        <div style={styles.textPanel}>
          Not yet implemented. This section is now routed in the chart, but the current patient-chart workflow does not yet expose a real data source for this item.
        </div>
      </div>
    </div>
  );

  const renderDetail = () => {
    if (!hasAssessment) {
      return (
        <div style={styles.card}>
          <div style={styles.sectionHeader}>
            <h3 style={styles.title}>Assessment data unavailable</h3>
            <div style={styles.subtitle}>Complete or load an RN Initial Comprehensive Assessment to review HOPE and LCD content here.</div>
          </div>
          <div style={styles.body}>
            <div style={styles.textPanel}>
              No RN ICA assessment was returned for this patient. Once an RN ICA exists, this board will load the saved form data directly by patient ID.
            </div>
          </div>
        </div>
      );
    }

    if (selectedSection === "lcd-eligibility") {
      return (
        <div style={styles.card}>
          <div style={styles.sectionHeader}>
            <h3 style={styles.title}>LCD Eligibility</h3>
            <div style={styles.subtitle}>Reused from the patient’s saved RN ICA LCD section — no new evaluation is run here.</div>
          </div>
          <div style={styles.body}>
            <div style={styles.detailGrid}>
              <div style={styles.infoTile}>
                <div style={styles.label}>Primary diagnosis</div>
                <div style={styles.value}>
                  {[diagnoses.primaryDiagnosis?.icd10, diagnoses.primaryDiagnosis?.description].filter(Boolean).join(" — ") || "—"}
                </div>
              </div>
              <div style={styles.infoTile}>
                <div style={styles.label}>Saved detected guideline</div>
                <div style={styles.value}>{detectedDisease ? humanizeKey(detectedDisease) : "—"}</div>
              </div>
              <div style={styles.infoTile}>
                <div style={styles.label}>Saved structured findings</div>
                <div style={styles.value}>{criteriaAnswerCount} answers · {criteriaFactCount} facts</div>
              </div>
            </div>

            {detectedDisease ? (
              <div style={styles.textPanel}>
                <div style={{ fontWeight: 800, marginBottom: 10 }}>Saved RN ICA LCD capture</div>
                {criteriaAnswerCount > 0 || criteriaFactCount > 0 ? (
                  <div style={styles.list}>
                    {Object.entries(criteriaAnswers).map(([criterionKey, criterionValue]) => (
                      <div key={criterionKey} style={styles.listItem}>
                        <div style={{ fontSize: 13, fontWeight: 700, color: colors.text }}>{criterionKey}</div>
                        <span style={styles.yesNoPill(Boolean(criterionValue))}>{criterionValue ? "Yes" : "No"}</span>
                      </div>
                    ))}
                    {Object.entries(criteriaFacts).map(([factKey, factValue]) => (
                      <div key={factKey} style={styles.listItem}>
                        <div style={{ fontSize: 13, fontWeight: 700, color: colors.text }}>{humanizeKey(factKey)}</div>
                        <span style={styles.badge("teal")}>{String(factValue)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div>
                    This locked RN ICA only saved the LCD narrative and a detected guideline key. It does not contain persisted structured criteria answers/facts to replay the full yes/no checklist here.
                  </div>
                )}
              </div>
            ) : (
              <div style={styles.textPanel}>
                No saved LCD guideline detection is present on this locked RN ICA. Only the narrative below is available.
              </div>
            )}
            <div style={styles.textPanel}>
              {diagnoses.lcdEligibilityNarrative?.trim()
                ? diagnoses.lcdEligibilityNarrative.trim()
                : "No LCD supporting evidence narrative has been documented on this assessment yet."}
            </div>
          </div>
        </div>
      );
    }

    if (selectedSection === "hope-admission") {
      return <HopeReport formData={formData} patient={patient} agency={agency} />;
    }

    if (selectedSection === "hope-huv1") {
      return renderPlaceholder(
        "HOPE - HUV1",
        "CMS HOPE Update Visit 1 completion is not yet surfaced in this workflow.",
        <div style={styles.detailGrid}>
          <div style={styles.infoTile}>
            <div style={styles.label}>Tracking status</div>
            <div style={styles.value}>Not yet tracked</div>
          </div>
          <div style={styles.infoTile}>
            <div style={styles.label}>Expected visit window</div>
            <div style={styles.value}>{huv1Window || "Hospice election date unavailable"}</div>
          </div>
        </div>,
      );
    }

    if (selectedSection === "hope-huv2") {
      return renderPlaceholder(
        "HOPE - HUV2",
        "CMS HOPE Update Visit 2 completion is not yet surfaced in this workflow.",
        <div style={styles.detailGrid}>
          <div style={styles.infoTile}>
            <div style={styles.label}>Tracking status</div>
            <div style={styles.value}>Not yet tracked</div>
          </div>
          <div style={styles.infoTile}>
            <div style={styles.label}>Expected visit window</div>
            <div style={styles.value}>{huv2Window || "Hospice election date unavailable"}</div>
          </div>
        </div>,
      );
    }

    if (selectedSection === "hope-discharge") {
      return renderPlaceholder("HOPE - Discharge", "A discharge HOPE renderer has not been built in the patient chart yet.");
    }

    if (selectedSection === "decline-of-status") {
      return renderPlaceholder("Decline of Status", "A decline-of-status chart view has not been built in the patient chart yet.");
    }

    return (
      <div style={styles.card}>
        <div style={styles.sectionHeader}>
          <h3 style={styles.title}>Compliance workflow</h3>
          <div style={styles.subtitle}>Select a HOPE or LCD item below to review saved chart content.</div>
        </div>
        <div style={styles.body}>
          <div style={styles.list}>
            {SECTION_ITEMS.map((item) => {
              const status = item.key === "hope-admission" || item.key === "lcd-eligibility" ? "Live content" : "Not yet implemented";
              const tone = item.key === "hope-admission" || item.key === "lcd-eligibility" ? "green" : "amber";
              return (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => onNavigateToSection?.(item.key)}
                  style={{ ...styles.listItem, cursor: onNavigateToSection ? "pointer" : "default", textAlign: "left", border: `1px solid ${colors.border}` }}
                >
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: colors.text }}>{item.label}</div>
                    <div style={{ marginTop: 4, fontSize: 12.5, color: colors.label }}>
                      {item.key === "hope-admission"
                        ? "Loads the saved HOPE Admission print view from the patient’s RN ICA."
                        : item.key === "lcd-eligibility"
                          ? "Shows saved LCD narrative and structured disease-specific eligibility inputs."
                          : "Routed and ready for future clinical workflow wiring without fabricating completion data."}
                    </div>
                  </div>
                  <span style={styles.badge(tone)}>{status}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={styles.page}>
      <div style={styles.stack}>
        <div style={styles.card}>
          <div style={styles.sectionHeader}>
            <h2 style={styles.title}>HOPE - SFV/HUV Status</h2>
            <div style={styles.subtitle}>
              Compliance summary sourced from the patient summary and saved RN ICA form data.
              {hasAssessment ? ` RN ICA ${assessment.locked ? "locked" : "draft"} record: ${assessment.assessmentId}.` : " RN ICA record not yet available."}
            </div>
          </div>
          <div style={styles.body}>
            {loading ? (
              <div style={styles.muted}>Loading compliance data…</div>
            ) : (
              <>
                <div style={styles.summaryGrid}>
                  <div style={styles.statusCard}>
                    <div style={styles.eyebrow}>SFV Status</div>
                    <div style={styles.statusLead}>
                      {!hasAssessment
                        ? "Assessment unavailable"
                        : hopeReport.sfvStatus.required
                          ? `Visit by ${formatDate(hopeReport.sfvStatus.dueDate)}`
                          : "No SFV trigger"}
                    </div>
                    <div style={styles.statusSub}>{hasAssessment ? hopeReport.sfvStatus.statusLabel : "RN ICA not found"}</div>
                    <div style={styles.muted}>
                      {!hasAssessment
                        ? "An RN ICA is required before SFV trigger status can be derived from HOPE symptom-impact data."
                        : hopeReport.sfvStatus.required
                          ? `Triggered by: ${hopeReport.sfvStatus.triggeredSymptoms.join(", ") || "—"}`
                          : hopeReport.sfvStatus.note}
                    </div>
                  </div>

                  <div style={styles.statusCard}>
                    <div style={styles.eyebrow}>HUV1 Status</div>
                    <div style={styles.statusLead}>{huv1Window || "Window unavailable"}</div>
                    <div style={styles.statusSub}>Not yet tracked</div>
                    <div style={styles.muted}>
                      Backend Phase B rules define HUV1 for days 6–15 after election, but completion is not yet surfaced from the RN ICA workflow.
                    </div>
                  </div>

                  <div style={styles.statusCard}>
                    <div style={styles.eyebrow}>HUV2 Status</div>
                    <div style={styles.statusLead}>{huv2Window || "Window unavailable"}</div>
                    <div style={styles.statusSub}>Not yet tracked</div>
                    <div style={styles.muted}>
                      Backend Phase B rules define HUV2 for days 16–30 after election, but completion is not yet surfaced from the RN ICA workflow.
                    </div>
                  </div>
                </div>

                {hopeReport.legacyReviewRequired.required && (
                  <div style={styles.legacyBanner}>
                    <strong>HOPE Legacy Review Required:</strong> review {hopeReport.legacyReviewRequired.items.join(", ")} before printing or submission.
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        <div style={styles.card}>
          <div style={styles.sectionHeader}>
            <h3 style={styles.title}>Compliance sections</h3>
            <div style={styles.subtitle}>These routes now mirror the patient-chart HOPE/LCD sidebar structure.</div>
          </div>
          <div style={styles.body}>
            <div style={styles.navRow}>
              {SECTION_ITEMS.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => onNavigateToSection?.(item.key)}
                  style={styles.navButton(selectedSection === item.key)}
                >
                  {item.label}
                </button>
              ))}
            </div>
            {error ? <div style={{ ...styles.muted, marginTop: 12 }}>{error}</div> : null}
          </div>
        </div>

        {renderDetail()}
      </div>
    </div>
  );
}
