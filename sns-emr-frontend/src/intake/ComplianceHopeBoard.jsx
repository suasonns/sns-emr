import React, { useEffect, useMemo, useState } from "react";
import { fetchHopeUpdateStatus, getRnicaAssessmentByPatient } from "../api/icaAssessments";
import { fetchPatientSummary } from "../api/patientCharts";
import { getCurrentUser } from "../api/session";
import { useThemeMode } from "../theme/theme";
import { getChartColors } from "../theme/chartColors";
import { defaultPatient } from "./ConsentNotifications";
import HopeReport from "./HopeReport";
import mapRnIcaToHopeReport from "./hopeReportMapper";
import { fetchDeclineOfStatusTrend } from "../api/facesheet";
import { fetchDischargePlanning } from "../api/patientCharts";

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

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function parseDateValue(value) {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function normalizeRangeValue(value, min, max) {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;
  return Number((((numeric - min) / Math.max(max - min, 1)) * 10).toFixed(2));
}

function toFiniteNumber(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function formatAxisValue(value) {
  const numeric = toFiniteNumber(value);
  if (numeric === null) return "—";
  const rounded = Math.round(numeric * 10) / 10;
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1).replace(/\.0$/, "");
}

function layoutEndLabels(labels, minY, maxY, gap = 16) {
  if (!labels.length) return [];
  const sorted = [...labels].sort((a, b) => a.point.y - b.point.y);
  const positioned = sorted.map((label) => ({ ...label, labelY: clamp(label.point.y, minY, maxY) }));
  for (let index = 1; index < positioned.length; index += 1) {
    positioned[index].labelY = Math.max(positioned[index].labelY, positioned[index - 1].labelY + gap);
  }
  for (let index = positioned.length - 2; index >= 0; index -= 1) {
    positioned[index].labelY = Math.min(positioned[index].labelY, positioned[index + 1].labelY - gap);
  }
  if (positioned[0].labelY < minY) {
    const shift = minY - positioned[0].labelY;
    positioned.forEach((label) => { label.labelY += shift; });
  }
  const lastLabel = positioned[positioned.length - 1];
  if (lastLabel.labelY > maxY) {
    const shift = lastLabel.labelY - maxY;
    positioned.forEach((label) => { label.labelY -= shift; });
  }
  return positioned;
}

const DECLINE_STATUS_SERIES = [
  {
    key: "pain_level",
    label: "Pain Level",
    shortLabel: "Pain",
    color: "#dc2626",
    strokeWidth: 2,
    unit: "",
    trendDirection: "higher-is-worse",
    significantThreshold: 2,
    getRawValue: (entry) => entry.pain_level,
    normalize: (entry) => clamp(Number(entry.pain_level || 0), 0, 10),
    displayValue: (entry) => entry.pain_level ?? "—",
    rawDisplay: (entry) => entry.pain_level ?? "—",
    clinicalLabel: (entry) => String(entry.pain_level ?? "—"),
  },
  {
    key: "bmi",
    label: "BMI",
    shortLabel: "BMI",
    color: "#2563eb",
    strokeWidth: 2,
    unit: "",
    trendDirection: "lower-is-worse",
    significantThreshold: 1,
    getRawValue: (entry) => entry.bmi,
    normalize: (entry) => normalizeRangeValue(entry.bmi, 10, 50),
    displayValue: (entry) => entry.bmi ?? "—",
    rawDisplay: (entry) => entry.bmi ?? "—",
    clinicalLabel: (entry) => String(entry.bmi ?? "—"),
    note: "Scaled to shared 0–10 axis from BMI 10–50.",
  },
  {
    key: "mac",
    label: "MAC",
    shortLabel: "MAC",
    color: "#16a34a",
    strokeWidth: 4,
    unit: "cm",
    trendDirection: "lower-is-worse",
    significantThreshold: 0.5,
    getRawValue: (entry) => entry.mac,
    normalize: (entry) => normalizeRangeValue(entry.mac, 10, 40),
    displayValue: (entry) => entry.mac ?? "—",
    rawDisplay: (entry) => entry.mac !== null && entry.mac !== undefined ? `${entry.mac}cm` : "—",
    clinicalLabel: (entry) => `${entry.mac ?? "—"} cm`,
    note: "Scaled to shared 0–10 axis from MAC 10–40.",
  },
  {
    key: "adl_score",
    label: "ADL Score",
    shortLabel: "ADL",
    color: "#f59e0b",
    strokeWidth: 2,
    unit: "",
    trendDirection: "higher-is-worse",
    significantThreshold: 3,
    getRawValue: (entry) => entry.adl_score,
    normalize: (entry) => clamp(Number(entry.adl_score || 0), 0, 10),
    displayValue: (entry) => entry.adl_score ?? "—",
    rawDisplay: (entry) => entry.adl_score ?? "—",
    clinicalLabel: (entry) => String(entry.adl_score ?? "—"),
  },
  {
    key: "kps",
    label: "KPS",
    shortLabel: "KPS",
    color: "#db2777",
    strokeWidth: 4,
    unit: "%",
    trendDirection: "lower-is-worse",
    significantThreshold: 10,
    getRawValue: (entry) => entry.kps,
    normalize: (entry) => normalizeRangeValue(entry.kps, 0, 100),
    displayValue: (entry) => entry.kps ?? "—",
    rawDisplay: (entry) => entry.kps !== null && entry.kps !== undefined ? `${entry.kps}%` : "—",
    clinicalLabel: (entry) => String(entry.kps ?? "—"),
    note: "Displayed on shared 0–10 axis as KPS ÷ 10.",
  },
  {
    key: "pps",
    label: "PPS",
    shortLabel: "PPS",
    color: "#fb7185",
    strokeWidth: 4,
    unit: "%",
    trendDirection: "lower-is-worse",
    significantThreshold: 10,
    getRawValue: (entry) => entry.pps,
    normalize: (entry) => normalizeRangeValue(entry.pps, 0, 100),
    displayValue: (entry) => entry.pps ?? "—",
    rawDisplay: (entry) => entry.pps !== null && entry.pps !== undefined ? `${entry.pps}%` : "—",
    clinicalLabel: (entry) => String(entry.pps ?? "—"),
    note: "Displayed on shared 0–10 axis as PPS ÷ 10.",
  },
  {
    key: "fast",
    label: "FAST",
    shortLabel: "FAST",
    color: "#111827",
    strokeWidth: 2,
    unit: "",
    trendDirection: "higher-is-worse",
    significantThreshold: 0.5,
    getRawValue: (entry) => entry.fast,
    normalize: (entry) => clamp(Number(entry.fast || 0), 0, 10),
    displayValue: (entry) => entry.fast_label || entry.fast || "—",
    rawDisplay: (entry) => entry.fast_label || entry.fast || "—",
    clinicalLabel: (entry) => String(entry.fast_label || entry.fast || "—"),
  },
  {
    key: "nyha",
    label: "NYHA",
    shortLabel: "NYHA",
    color: "#7c3aed",
    strokeWidth: 2,
    unit: "",
    trendDirection: "higher-is-worse",
    significantThreshold: 1,
    getRawValue: (entry) => entry.nyha,
    normalize: (entry) => clamp(Number(entry.nyha || 0), 0, 10),
    displayValue: (entry) => entry.nyha_label || entry.nyha || "—",
    rawDisplay: (entry) => entry.nyha_label || entry.nyha || "—",
    clinicalLabel: (entry) => String(entry.nyha_label || entry.nyha || "—"),
  },
];

function buildSeriesPoints(trend, seriesConfig) {
  return (trend || [])
    .map((entry) => {
      const parsedDate = parseDateValue(entry.date);
      const rawValue = seriesConfig.getRawValue(entry);
      const scaledValue = seriesConfig.normalize(entry);
      if (!parsedDate || rawValue === null || rawValue === undefined || scaledValue === null || scaledValue === undefined) {
        return null;
      }
      return {
        id: `${seriesConfig.key}-${entry.id}`,
        date: entry.date,
        parsedDate,
        assessmentType: entry.assessment_type,
        rawValue,
        scaledValue,
        displayValue: seriesConfig.displayValue(entry),
        rawDisplay: seriesConfig.rawDisplay ? seriesConfig.rawDisplay(entry) : seriesConfig.displayValue(entry),
        clinicalLabel: seriesConfig.clinicalLabel ? seriesConfig.clinicalLabel(entry) : String(seriesConfig.displayValue(entry)),
      };
    })
    .filter(Boolean);
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
  const [hopeUpdateStatus, setHopeUpdateStatus] = useState(null);
  const [dischargeState, setDischargeState] = useState(null);
  const [declineTrend, setDeclineTrend] = useState([]);
  const [declineRange, setDeclineRange] = useState({
    availableFromDate: "",
    availableToDate: "",
    appliedFromDate: "",
    appliedToDate: "",
  });
  const [declineDraftRange, setDeclineDraftRange] = useState({ fromDate: "", toDate: "" });
  const [declineLoading, setDeclineLoading] = useState(false);
  const [declineShowTable, setDeclineShowTable] = useState(false);
  const [declineTooltip, setDeclineTooltip] = useState(null);
  const [declineVisibleSeries, setDeclineVisibleSeries] = useState(() => Object.fromEntries(DECLINE_STATUS_SERIES.map((series) => [series.key, true])));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDeclineTrend = async (range = undefined) => {
    if (!patientId) return null;
    setDeclineLoading(true);
    try {
      const response = await fetchDeclineOfStatusTrend(patientId, range);
      setDeclineTrend(response?.trend || []);
      setDeclineRange({
        availableFromDate: response?.available_from_date || "",
        availableToDate: response?.available_to_date || "",
        appliedFromDate: response?.applied_from_date || "",
        appliedToDate: response?.applied_to_date || "",
      });
      return response;
    } finally {
      setDeclineLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    if (!patientId) {
      setPatientSummary(null);
      setAssessment(null);
      setHopeUpdateStatus(null);
      setDischargeState(null);
      setDeclineTrend([]);
      setDeclineRange({ availableFromDate: "", availableToDate: "", appliedFromDate: "", appliedToDate: "" });
      setDeclineDraftRange({ fromDate: "", toDate: "" });
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
      fetchHopeUpdateStatus(patientId),
      loadDeclineTrend(),
      fetchDischargePlanning(patientId),
    ])
      .then(([assessmentResult, summaryResult, hopeUpdateResult, declineTrendResult, dischargeResult]) => {
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

        if (hopeUpdateResult.status === "fulfilled") {
          setHopeUpdateStatus(hopeUpdateResult.value);
        } else {
          setHopeUpdateStatus(null);
          problems.push(hopeUpdateResult.reason?.message || "Unable to load HUV status.");
        }

        if (dischargeResult.status === "fulfilled") {
          setDischargeState(dischargeResult.value);
        } else {
          setDischargeState(null);
        }

        if (declineTrendResult.status === "fulfilled") {
          setDeclineDraftRange({
            fromDate: declineTrendResult.value?.available_from_date || "",
            toDate: declineTrendResult.value?.available_to_date || "",
          });
        } else {
          setDeclineTrend([]);
          problems.push(declineTrendResult.reason?.message || "Unable to load decline-of-status trend.");
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
  const huv1Window = hopeUpdateStatus?.huv1?.window
    ? `${formatDate(hopeUpdateStatus.huv1.window.start)} – ${formatDate(hopeUpdateStatus.huv1.window.end)}`
    : buildHuvWindow(electionDate, 6, 15);
  const huv2Window = hopeUpdateStatus?.huv2?.window
    ? `${formatDate(hopeUpdateStatus.huv2.window.start)} – ${formatDate(hopeUpdateStatus.huv2.window.end)}`
    : buildHuvWindow(electionDate, 16, 30);
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
    chartShell: {
      position: "relative",
      border: `1px solid ${colors.border}`,
      borderRadius: 10,
      padding: 14,
      backgroundColor: mode === "light" ? "#f8fbfc" : "#152132",
    },
    summaryStrip: { display: "grid", gap: 8, marginBottom: 14 },
    summaryRow: (tone) => ({
      display: "flex",
      alignItems: "center",
      gap: 10,
      padding: "10px 12px",
      borderRadius: 10,
      border: `1px solid ${tone.border}`,
      backgroundColor: tone.bg,
      color: tone.text,
      fontSize: 12.5,
      fontWeight: 700,
    }),
    summaryIcon: { width: 14, flexShrink: 0, textAlign: "center", fontSize: 14, lineHeight: 1 },
    summaryLabel: { fontWeight: 800, minWidth: 48 },
    chartTitle: { fontSize: 13, fontWeight: 800, color: colors.text, marginBottom: 8 },
    chartMeta: { fontSize: 12, color: colors.label, marginTop: 8, lineHeight: 1.5 },
    filterBar: { display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 16 },
    filterField: { display: "flex", flexDirection: "column", gap: 6, minWidth: 170 },
    filterInput: {
      minHeight: 40,
      borderRadius: 8,
      border: `1px solid ${colors.border}`,
      padding: "8px 10px",
      backgroundColor: mode === "light" ? "#ffffff" : "#0f172a",
      color: colors.text,
      fontSize: 13,
    },
    filterButton: (variant = "primary") => ({
      minHeight: 40,
      borderRadius: 8,
      border: `1px solid ${variant === "primary" ? colors.teal : colors.border}`,
      backgroundColor: variant === "primary" ? colors.teal : colors.card,
      color: variant === "primary" ? "#ffffff" : colors.text,
      padding: "0 14px",
      fontSize: 13,
      fontWeight: 700,
      cursor: "pointer",
    }),
    chartFrame: {
      border: `1px solid ${colors.border}`,
      borderRadius: 12,
      backgroundColor: mode === "light" ? "#ffffff" : "#101a29",
      padding: 14,
    },
    tooltip: {
      position: "absolute",
      minWidth: 180,
      maxWidth: 240,
      borderRadius: 10,
      border: `1px solid ${colors.border}`,
      backgroundColor: mode === "light" ? "rgba(255,255,255,0.98)" : "rgba(15,23,42,0.96)",
      color: colors.text,
      padding: "10px 12px",
      boxShadow: "0 14px 34px rgba(15, 23, 42, 0.28)",
      pointerEvents: "none",
      zIndex: 4,
      lineHeight: 1.45,
      fontSize: 12,
    },
    tooltipTitle: { fontSize: 12.5, fontWeight: 800, marginBottom: 6 },
    tooltipMeta: { color: colors.label, fontSize: 11.5, marginBottom: 8 },
    tooltipLine: { marginTop: 2 },
    legend: { display: "flex", flexWrap: "wrap", gap: 10, marginTop: 14 },
    legendItem: {
      display: "inline-flex",
      alignItems: "center",
      gap: 8,
      padding: "6px 10px",
      borderRadius: 999,
      border: `1px solid ${colors.border}`,
      backgroundColor: mode === "light" ? "#fbfeff" : "#132034",
      fontSize: 12,
      fontWeight: 700,
      color: colors.text,
    },
    legendSwatch: (color) => ({ width: 10, height: 10, borderRadius: 999, backgroundColor: color, border: color === "#111827" ? "1px solid #475569" : "none" }),
    graphDataButton: {
      display: "inline-flex",
      alignItems: "center",
      gap: 8,
      marginTop: 14,
      border: `1px solid ${colors.border}`,
      backgroundColor: mode === "light" ? "#ffffff" : "#111827",
      color: colors.text,
      borderRadius: 8,
      padding: "8px 12px",
      fontSize: 12.5,
      fontWeight: 700,
      cursor: "pointer",
    },
    tableWrap: {
      marginTop: 14,
      border: `1px solid ${colors.border}`,
      borderRadius: 10,
      overflow: "auto",
      backgroundColor: mode === "light" ? "#ffffff" : "#0f172a",
    },
    table: { width: "100%", borderCollapse: "collapse", minWidth: 860 },
    th: {
      textAlign: "left",
      fontSize: 11,
      letterSpacing: "0.06em",
      textTransform: "uppercase",
      color: colors.label,
      padding: "10px 12px",
      borderBottom: `1px solid ${colors.border}`,
      backgroundColor: mode === "light" ? "#f8fbfc" : "#132034",
    },
    td: {
      padding: "10px 12px",
      borderBottom: `1px solid ${colors.border}`,
      fontSize: 12.5,
      color: colors.text,
      verticalAlign: "top",
    },
    axisNote: { fontSize: 12, color: colors.label, marginTop: 10, lineHeight: 1.5 },
  };

  const declineDateCount = useMemo(
    () => new Set((declineTrend || []).map((entry) => String(entry.date || "").slice(0, 10)).filter(Boolean)).size,
    [declineTrend]
  );

  const declineSeries = useMemo(
    () => DECLINE_STATUS_SERIES.map((series) => ({ ...series, points: buildSeriesPoints(declineTrend, series) })),
    [declineTrend]
  );

  useEffect(() => {
    setDeclineVisibleSeries((current) => {
      const next = {};
      declineSeries.forEach((series) => {
        next[series.key] = current[series.key] !== false;
      });
      return next;
    });
  }, [declineSeries]);

  const visibleDeclineSeries = useMemo(
    () => declineSeries.filter((series) => declineVisibleSeries[series.key] !== false),
    [declineSeries, declineVisibleSeries]
  );

  const declineSummary = useMemo(() => declineSeries.map((series) => {
    const points = [...series.points].sort((a, b) => a.parsedDate.getTime() - b.parsedDate.getTime());
    if (!points.length) {
      return { key: series.key, icon: "▬", tone: "neutral", label: series.shortLabel || series.label, description: "Not yet documented" };
    }
    if (points.length === 1) {
      return { key: series.key, icon: "▬", tone: "neutral", label: series.shortLabel || series.label, description: "Not yet trackable" };
    }
    const first = points[0];
    const latest = points[points.length - 1];
    const firstNumber = toFiniteNumber(first.rawValue);
    const latestNumber = toFiniteNumber(latest.rawValue);
    if (firstNumber === null || latestNumber === null) {
      const stable = first.rawDisplay === latest.rawDisplay;
      return {
        key: series.key,
        icon: stable ? "▬" : "▼",
        tone: stable ? "neutral" : "amber",
        label: series.shortLabel || series.label,
        description: stable ? "Stable" : `${first.rawDisplay} → ${latest.rawDisplay}`,
      };
    }
    const delta = latestNumber - firstNumber;
    let changeAmount = 0;
    let direction = "stable";
    if (series.trendDirection === "lower-is-worse") {
      changeAmount = firstNumber - latestNumber;
      if (changeAmount > 0) direction = "decline";
      else if (changeAmount < 0) direction = "improvement";
    } else if (series.trendDirection === "higher-is-worse") {
      changeAmount = latestNumber - firstNumber;
      if (changeAmount > 0) direction = "decline";
      else if (changeAmount < 0) direction = "improvement";
    }
    if (direction === "stable" || Math.abs(delta) < 0.0001) {
      return { key: series.key, icon: "▬", tone: "neutral", label: series.shortLabel || series.label, description: "Stable" };
    }
    if (direction === "improvement") {
      return { key: series.key, icon: "▲", tone: "green", label: series.shortLabel || series.label, description: "Improved" };
    }
    return {
      key: series.key,
      icon: "▼",
      tone: Math.abs(changeAmount) >= (series.significantThreshold || 1) ? "red" : "amber",
      label: series.shortLabel || series.label,
      description: `${first.rawDisplay} → ${latest.rawDisplay}`,
    };
  }), [declineSeries]);

  const allDeclinePoints = useMemo(
    () => visibleDeclineSeries.flatMap((series) => series.points),
    [visibleDeclineSeries]
  );

  const declineChart = useMemo(() => {
    if (!allDeclinePoints.length) return null;
    const dateKeys = [...new Set((declineTrend || []).map((entry) => String(entry.date || "").slice(0, 10)).filter(Boolean))].sort();
    const times = dateKeys.map((value) => new Date(`${value}T00:00:00`).getTime());
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);
    const width = 980;
    const assessmentCount = Math.max((declineTrend || []).length, 1);
    const height = assessmentCount >= 16 ? 500 : assessmentCount >= 6 ? 400 : assessmentCount <= 2 ? 280 : 320;
    const padding = { top: 24, right: 144, bottom: 48, left: 44 };
    const innerWidth = width - padding.left - padding.right;
    const innerHeight = height - padding.top - padding.bottom;
    const xForTime = (time) => {
      if (maxTime === minTime) return padding.left + innerWidth / 2;
      return padding.left + (((time - minTime) / (maxTime - minTime)) * innerWidth);
    };
    const yForValue = (value) => padding.top + innerHeight - ((clamp(Number(value || 0), 0, 10) / 10) * innerHeight);
    const dateTicks = dateKeys.map((value) => ({ value, x: xForTime(new Date(`${value}T00:00:00`).getTime()) }));
    const yTicks = Array.from({ length: 11 }, (_, index) => ({ value: 10 - index, y: yForValue(10 - index) }));
    const series = visibleDeclineSeries.map((config) => {
      const byDate = new Map(config.points.map((point) => [String(point.date || "").slice(0, 10), point]));
      const sortedPoints = [...config.points].sort((a, b) => a.parsedDate.getTime() - b.parsedDate.getTime());
      const renderedPoints = sortedPoints.map((point, index) => {
        const previousPoint = sortedPoints[index - 1] || null;
        const previousRaw = previousPoint ? toFiniteNumber(previousPoint.rawValue) : null;
        const currentRaw = toFiniteNumber(point.rawValue);
        const rawDelta = previousRaw !== null && currentRaw !== null ? Number((currentRaw - previousRaw).toFixed(2)) : null;
        return {
          ...point,
          x: xForTime(point.parsedDate.getTime()),
          y: yForValue(point.scaledValue),
          previousRawDisplay: previousPoint ? previousPoint.rawDisplay : "—",
          rawDelta,
          isChangedPoint: rawDelta !== null ? Math.abs(rawDelta) >= (config.significantThreshold || 1) : Boolean(previousPoint && previousPoint.rawDisplay !== point.rawDisplay),
        };
      });
      const renderedByDate = new Map(renderedPoints.map((point) => [String(point.date || "").slice(0, 10), point]));
      const pathSegments = [];
      let activeSegment = [];
      dateKeys.forEach((dateKey) => {
        const point = renderedByDate.get(dateKey);
        if (point) {
          activeSegment.push(point);
        } else if (activeSegment.length) {
          pathSegments.push(activeSegment);
          activeSegment = [];
        }
      });
      if (activeSegment.length) pathSegments.push(activeSegment);
      const paths = pathSegments
        .filter((segment) => segment.length >= 2)
        .map((segment) => segment.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" "));
      return {
        ...config,
        byDate,
        paths,
        renderedPoints,
      };
    });
    const endLabels = layoutEndLabels(
      series
        .filter((config) => config.renderedPoints.length)
        .map((config) => {
          const point = config.renderedPoints[config.renderedPoints.length - 1];
          return {
            key: config.key,
            color: config.color,
            label: config.shortLabel || config.label,
            value: point.rawDisplay,
            point,
            labelX: point.x + 12,
          };
        }),
      padding.top + 12,
      height - padding.bottom - 8,
      16,
    );
    return { width, height, padding, yTicks, dateTicks, series, endLabels };
  }, [allDeclinePoints, declineTrend, visibleDeclineSeries]);

  const declineSummaryTones = {
    green: { bg: mode === "light" ? "#ecfdf5" : "rgba(22,163,74,0.16)", border: mode === "light" ? "#86efac" : "rgba(34,197,94,0.35)", text: mode === "light" ? "#166534" : "#bbf7d0" },
    amber: { bg: mode === "light" ? "#fffbeb" : "rgba(245,158,11,0.16)", border: mode === "light" ? "#fcd34d" : "rgba(251,191,36,0.35)", text: mode === "light" ? "#92400e" : "#fde68a" },
    red: { bg: mode === "light" ? "#fef2f2" : "rgba(220,38,38,0.16)", border: mode === "light" ? "#fca5a5" : "rgba(248,113,113,0.4)", text: mode === "light" ? "#991b1b" : "#fecaca" },
    neutral: { bg: mode === "light" ? "#f8fafc" : "rgba(148,163,184,0.12)", border: mode === "light" ? "#cbd5e1" : "rgba(148,163,184,0.24)", text: mode === "light" ? "#334155" : "#cbd5e1" },
  };

  const declineGraphDataRows = useMemo(
    () => declineSeries.flatMap((series) => (declineTrend || []).map((entry) => {
      const normalizedValue = series.normalize(entry);
      const rawValue = series.rawDisplay(entry);
      return {
        key: `${entry.id}-${series.key}`,
        date: entry.date,
        source: entry.assessment_type,
        metric: series.label,
        rawValue: rawValue || "—",
        unit: series.unit || "—",
        normalizedValue: normalizedValue === null || normalizedValue === undefined ? "—" : formatAxisValue(normalizedValue),
      };
    })),
    [declineSeries, declineTrend]
  );

  const handleDeclineFilterSubmit = async (event) => {
    event.preventDefault();
    try {
      const response = await loadDeclineTrend({
        fromDate: declineDraftRange.fromDate || undefined,
        toDate: declineDraftRange.toDate || undefined,
      });
      if (response) {
        setError((current) => current.replace(/Unable to load decline-of-status trend\.?/g, "").trim());
      }
    } catch (declineError) {
      setError((current) => {
        const prefix = current ? `${current} ` : "";
        return `${prefix}${declineError instanceof Error ? declineError.message : "Unable to load decline-of-status trend."}`.trim();
      });
    }
  };

  const renderHuvAssessment = (label, description, timepoint, windowData) => {
    const matchedAssessment = windowData?.assessment || null;
    if (!matchedAssessment) {
      return renderPlaceholder(
        label,
        description,
        <div style={styles.detailGrid}>
          <div style={styles.infoTile}>
            <div style={styles.label}>Tracking status</div>
            <div style={styles.value}>No locked Update Assessment in window yet</div>
          </div>
          <div style={styles.infoTile}>
            <div style={styles.label}>Expected visit window</div>
            <div style={styles.value}>{timepoint === "HUV1" ? huv1Window || "Hospice election date unavailable" : huv2Window || "Hospice election date unavailable"}</div>
          </div>
        </div>,
      );
    }
    return (
      <HopeReport
        formData={matchedAssessment.formData || {}}
        patient={patient}
        agency={agency}
        timepoint={timepoint}
        assessmentMeta={matchedAssessment}
        onNavigateToSection={onNavigateToSection}
      />
    );
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
      return (
        <HopeReport
          formData={formData}
          patient={patient}
          agency={agency}
          timepoint="ADMISSION"
          assessmentMeta={assessment || {}}
          onNavigateToSection={onNavigateToSection}
        />
      );
    }

    if (selectedSection === "hope-huv1") {
      return renderHuvAssessment(
        "HOPE - HUV1",
        "CMS HOPE Update Visit 1 completion is not yet surfaced in this workflow.",
        "HUV1",
        hopeUpdateStatus?.huv1,
      );
    }

    if (selectedSection === "hope-huv2") {
      return renderHuvAssessment(
        "HOPE - HUV2",
        "CMS HOPE Update Visit 2 completion is not yet surfaced in this workflow.",
        "HUV2",
        hopeUpdateStatus?.huv2,
      );
    }

    if (selectedSection === "hope-discharge") {
      if (!dischargeState?.discharged) {
        return renderPlaceholder(
          "HOPE - Discharge",
          "Not applicable — this patient has not been discharged from hospice services.",
          <div style={styles.detailGrid}>
            <div style={styles.infoTile}>
              <div style={styles.label}>Tracking status</div>
              <div style={styles.value}>Patient is currently {dischargeState?.patient_status || "ACTIVE"}. Use "Discharge Planning" in the sidebar to finalize a discharge when appropriate.</div>
            </div>
          </div>,
        );
      }
      const [reasonCode, ...reasonRest] = String(dischargeState.discharge_reason || "").split(" - ");
      return (
        <HopeReport
          formData={formData}
          patient={patient}
          agency={agency}
          timepoint="DISCHARGE"
          assessmentMeta={assessment || {}}
          discharge={{
            dischargeDate: dischargeState.discharge_date,
            reasonCode: reasonCode || "",
            reasonLabel: reasonRest.join(" - "),
          }}
          onNavigateToSection={onNavigateToSection}
        />
      );
    }

    if (selectedSection === "decline-of-status") {
      return (
        <div style={styles.card}>
          <div style={styles.sectionHeader}>
            <h3 style={styles.title}>Decline of Status Indicators</h3>
            <div style={styles.subtitle}>Multi-series trend view from real locked Admission + Update assessments only. No fabricated points are shown.</div>
          </div>
          <div style={styles.body}>
            <form style={styles.filterBar} onSubmit={handleDeclineFilterSubmit}>
              <label style={styles.filterField}>
                <span style={styles.label}>From</span>
                <input
                  type="date"
                  value={declineDraftRange.fromDate}
                  onChange={(event) => setDeclineDraftRange((current) => ({ ...current, fromDate: event.target.value }))}
                  style={styles.filterInput}
                />
              </label>
              <label style={styles.filterField}>
                <span style={styles.label}>To</span>
                <input
                  type="date"
                  value={declineDraftRange.toDate}
                  onChange={(event) => setDeclineDraftRange((current) => ({ ...current, toDate: event.target.value }))}
                  style={styles.filterInput}
                />
              </label>
              <button type="submit" style={styles.filterButton("primary")} disabled={declineLoading}>
                {declineLoading ? "Loading..." : "Submit"}
              </button>
              <button
                type="button"
                style={styles.filterButton("secondary")}
                onClick={() => {
                  const fullRange = {
                    fromDate: declineRange.availableFromDate || "",
                    toDate: declineRange.availableToDate || "",
                  };
                  setDeclineDraftRange(fullRange);
                  loadDeclineTrend(fullRange).catch(() => {});
                }}
                disabled={declineLoading || (!declineRange.availableFromDate && !declineRange.availableToDate)}
              >
                Full Range
              </button>
            </form>

            <div style={styles.chartMeta}>
              Showing {declineTrend.length} assessment{declineTrend.length === 1 ? "" : "s"}
              {declineRange.appliedFromDate || declineRange.appliedToDate
                ? ` from ${formatDate(declineRange.appliedFromDate || declineRange.availableFromDate)} to ${formatDate(declineRange.appliedToDate || declineRange.availableToDate)}`
                : declineRange.availableFromDate
                  ? ` across ${formatDate(declineRange.availableFromDate)} to ${formatDate(declineRange.availableToDate)}`
                  : ""}
              .
            </div>

            {!declineChart ? (
              <div style={styles.textPanel}>
                {(declineTrend || []).length === 0
                  ? "N/A — no locked Admission or Update assessments are available in the selected range."
                  : "Only a single dated assessment is available in the selected range. The chart shows standalone points and honest 'No previous value' summaries instead of fabricating a trend."}
              </div>
            ) : (
              <>
                <div style={styles.summaryStrip}>
                  {declineSummary.map((item) => (
                    <div key={item.key} style={styles.summaryRow(declineSummaryTones[item.tone] || declineSummaryTones.neutral)}>
                      <span style={styles.summaryIcon}>{item.icon}</span>
                      <span style={styles.summaryLabel}>{item.label}</span>
                      <span>{item.description}</span>
                    </div>
                  ))}
                </div>
                <div style={styles.chartFrame}>
                  <div style={styles.chartShell}>
                    <svg
                      viewBox={`0 0 ${declineChart?.width || 980} ${declineChart?.height || 300}`}
                      width="100%"
                      height={declineChart?.height || 300}
                      role="img"
                      aria-label="Decline of status indicators trend chart"
                      onMouseLeave={() => setDeclineTooltip(null)}
                    >
                      {declineChart?.yTicks.map((tick) => (
                        <g key={`y-${tick.value}`}>
                          <line
                            x1={declineChart.padding.left}
                            x2={declineChart.width - declineChart.padding.right}
                            y1={tick.y}
                            y2={tick.y}
                            stroke={tick.value === 0 ? colors.border : mode === "light" ? "#edf2f7" : "#1f2937"}
                            strokeWidth="1"
                          />
                          <text x={declineChart.padding.left - 10} y={tick.y + 4} fontSize="11" textAnchor="end" fill={colors.label}>{tick.value}</text>
                        </g>
                      ))}
                      {declineChart?.dateTicks.map((tick) => (
                        <g key={`x-${tick.value}`}>
                          <line
                            x1={tick.x}
                            x2={tick.x}
                            y1={declineChart.padding.top}
                            y2={declineChart.height - declineChart.padding.bottom}
                            stroke={mode === "light" ? "#f1f5f9" : "#162033"}
                            strokeWidth="1"
                          />
                          <text
                            x={tick.x}
                            y={declineChart.height - declineChart.padding.bottom + 18}
                            fontSize="10"
                            textAnchor="middle"
                            fill={colors.label}
                          >
                            {formatDate(tick.value)}
                          </text>
                        </g>
                      ))}
                      <line
                        x1={declineChart?.padding.left || 44}
                        x2={declineChart?.padding.left || 44}
                        y1={declineChart?.padding.top || 24}
                        y2={(declineChart?.height || 360) - (declineChart?.padding.bottom || 48)}
                        stroke={colors.border}
                        strokeWidth="1.5"
                      />
                      <line
                        x1={declineChart?.padding.left || 44}
                        x2={(declineChart?.width || 980) - (declineChart?.padding.right || 24)}
                        y1={(declineChart?.height || 360) - (declineChart?.padding.bottom || 48)}
                        y2={(declineChart?.height || 360) - (declineChart?.padding.bottom || 48)}
                        stroke={colors.border}
                        strokeWidth="1.5"
                      />
                      {declineChart?.series.map((series) => (
                        <g key={series.key}>
                          {series.paths.map((path, index) => (
                            <path key={`${series.key}-path-${index}`} d={path} fill="none" stroke={series.color} strokeWidth={series.strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
                          ))}
                          {series.renderedPoints.map((point) => (
                            <g
                              key={point.id}
                              onMouseMove={(event) => {
                                const rect = event.currentTarget.ownerSVGElement?.getBoundingClientRect();
                                const left = rect ? event.clientX - rect.left + 14 : point.x + 14;
                                const top = rect ? event.clientY - rect.top + 14 : point.y + 14;
                                setDeclineTooltip({
                                  x: left,
                                  y: top,
                                  maxX: rect?.width || 980,
                                  maxY: rect?.height || (declineChart?.height || 300),
                                  seriesLabel: series.label,
                                  date: point.date,
                                  assessmentType: point.assessmentType,
                                  clinicalValue: point.clinicalLabel,
                                  displayValue: formatAxisValue(point.scaledValue),
                                  previousRawValue: point.previousRawDisplay,
                                  rawChange: point.rawDelta !== null
                                    ? `${point.rawDelta > 0 ? "+" : ""}${point.rawDelta}${series.unit ? ` ${series.unit}` : ""}`.trim()
                                    : "No previous documented value",
                                });
                              }}
                              onMouseLeave={() => setDeclineTooltip(null)}
                            >
                              {point.isChangedPoint ? (
                                <circle
                                  cx={point.x}
                                  cy={point.y}
                                  r="8"
                                  fill="rgba(251,146,60,0.18)"
                                  stroke="#fb923c"
                                  strokeWidth="2"
                                />
                              ) : null}
                              <circle
                                cx={point.x}
                                cy={point.y}
                                r={point.isChangedPoint ? 6.5 : 5.25}
                                fill={series.color}
                                stroke="#ffffff"
                                strokeWidth={point.isChangedPoint ? 2.2 : 1.8}
                              />
                              <circle
                                cx={point.x}
                                cy={point.y}
                                r="8"
                                fill="transparent"
                                stroke="transparent"
                                strokeWidth="0"
                              >
                                <title>{`${series.label}\nClinical Value: ${point.clinicalLabel}\nDisplay Value: ${formatAxisValue(point.scaledValue)}\nPrevious: ${point.previousRawDisplay}\nRaw change: ${point.rawDelta !== null ? `${point.rawDelta > 0 ? "+" : ""}${point.rawDelta}${series.unit ? ` ${series.unit}` : ""}`.trim() : "No previous documented value"}`}</title>
                              </circle>
                            </g>
                          ))}
                        </g>
                      ))}
                      {declineChart?.endLabels.map((label) => (
                        <g key={`end-label-${label.key}`}>
                          {Math.abs(label.labelY - label.point.y) > 2 ? (
                            <line
                              x1={label.point.x + 6}
                              x2={label.labelX - 4}
                              y1={label.point.y}
                              y2={label.labelY}
                              stroke={label.color}
                              strokeWidth="1"
                              opacity="0.7"
                            />
                          ) : null}
                          <text
                            x={label.labelX}
                            y={label.labelY + 4}
                            fontSize="12"
                            fontWeight="800"
                            textAnchor="start"
                            fill={label.color}
                          >
                            {`${label.label} ${label.value}`}
                          </text>
                        </g>
                      ))}
                      <text x={18} y={22} fontSize="11" fill={colors.label}>0-10</text>
                    </svg>
                    {declineTooltip ? (
                      <div
                        style={{
                          ...styles.tooltip,
                          left: Math.max(12, Math.min(declineTooltip.x, Math.max(12, (declineTooltip.maxX || 980) - 210))),
                          top: Math.max(12, Math.min(declineTooltip.y, Math.max(12, (declineTooltip.maxY || (declineChart?.height || 300)) - 140))),
                        }}
                      >
                        <div style={styles.tooltipTitle}>{declineTooltip.seriesLabel}</div>
                        <div style={styles.tooltipMeta}>
                          {formatDate(declineTooltip.date)} · {humanizeKey(declineTooltip.assessmentType)}
                        </div>
                        <div style={styles.tooltipLine}>Clinical Value: {declineTooltip.clinicalValue}</div>
                        <div style={styles.tooltipLine}>Display Value: {declineTooltip.displayValue}</div>
                        <div style={styles.tooltipLine}>Previous Raw Value: {declineTooltip.previousRawValue}</div>
                        <div style={styles.tooltipLine}>Raw Change: {declineTooltip.rawChange}</div>
                      </div>
                    ) : null}
                  </div>

                  <div style={styles.legend}>
                    {declineSeries.map((series) => (
                      <button
                        key={series.key}
                        type="button"
                        onClick={() => setDeclineVisibleSeries((current) => ({ ...current, [series.key]: current[series.key] === false }))}
                        style={{
                          ...styles.legendItem,
                          opacity: declineVisibleSeries[series.key] === false ? 0.55 : 1,
                          cursor: "pointer",
                          backgroundColor: declineVisibleSeries[series.key] === false ? (mode === "light" ? "#f8fafc" : "#101a29") : (mode === "light" ? "#fbfeff" : "#132034"),
                        }}
                        aria-pressed={declineVisibleSeries[series.key] !== false}
                      >
                        <span style={styles.legendSwatch(series.color)} />
                        <span>{series.label}</span>
                      </button>
                    ))}
                  </div>

                  <div style={styles.axisNote}>
                    Shared 0–10 axis: Pain, ADL, FAST, and NYHA use their documented values directly. KPS/PPS are shown as tenths of their 0–100 scores. BMI and MAC are normalized onto the same 0–10 display axis so all eight indicators can share one chart like the HospiceMD reference.
                  </div>
                </div>
              </>
            )}

            <button type="button" style={styles.graphDataButton} onClick={() => setDeclineShowTable((current) => !current)}>
              <span aria-hidden="true">▦</span>
              {declineShowTable ? "Hide Graph Data" : "Graph Data"}
            </button>

            {declineShowTable ? (
              <div style={styles.tableWrap}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Date</th>
                      <th style={styles.th}>Assessment Source</th>
                      <th style={styles.th}>Metric</th>
                      <th style={styles.th}>Raw Value</th>
                      <th style={styles.th}>Unit</th>
                      <th style={styles.th}>Normalized Display</th>
                    </tr>
                  </thead>
                  <tbody>
                    {declineGraphDataRows.map((row) => (
                      <tr key={row.key}>
                        <td style={styles.td}>{formatDate(row.date)}</td>
                        <td style={styles.td}>{humanizeKey(row.source)}</td>
                        <td style={styles.td}>{row.metric}</td>
                        <td style={styles.td}>{row.rawValue}</td>
                        <td style={styles.td}>{row.unit}</td>
                        <td style={styles.td}>{row.normalizedValue}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        </div>
      );
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
              const liveKeys = new Set([
                "hope-admission",
                "lcd-eligibility",
                "decline-of-status",
                ...(hopeUpdateStatus?.huv1?.assessment ? ["hope-huv1"] : []),
                ...(hopeUpdateStatus?.huv2?.assessment ? ["hope-huv2"] : []),
              ]);
              const status = liveKeys.has(item.key) ? "Live content" : "Honest placeholder";
              const tone = liveKeys.has(item.key) ? "green" : "amber";
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
                    <div style={styles.statusSub}>{hopeUpdateStatus?.huv1?.assessment ? "Locked Update Assessment found" : "No qualifying update yet"}</div>
                    <div style={styles.muted}>
                      {hopeUpdateStatus?.huv1?.assessment
                        ? `Assessment locked ${formatDate(hopeUpdateStatus.huv1.assessment.lockedAt || hopeUpdateStatus.huv1.assessment.updatedAt)}.`
                        : hopeUpdateStatus?.huv1?.reason || "Backend Phase B window checked, but no locked Update Assessment falls in days 6–15 yet."}
                    </div>
                  </div>

                  <div style={styles.statusCard}>
                    <div style={styles.eyebrow}>HUV2 Status</div>
                    <div style={styles.statusLead}>{huv2Window || "Window unavailable"}</div>
                    <div style={styles.statusSub}>{hopeUpdateStatus?.huv2?.assessment ? "Locked Update Assessment found" : "No qualifying update yet"}</div>
                    <div style={styles.muted}>
                      {hopeUpdateStatus?.huv2?.assessment
                        ? `Assessment locked ${formatDate(hopeUpdateStatus.huv2.assessment.lockedAt || hopeUpdateStatus.huv2.assessment.updatedAt)}.`
                        : hopeUpdateStatus?.huv2?.reason || "Backend Phase B window checked, but no locked Update Assessment falls in days 16–30 yet."}
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
