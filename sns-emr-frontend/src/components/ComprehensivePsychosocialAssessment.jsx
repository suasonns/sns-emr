import React, { useEffect, useMemo, useState } from "react";
import { fetchPatientSummary } from "../api/patientCharts";
import { getCurrentUser } from "../api/session";
import { getActivePatientId } from "../utils/activePatient";
import AssessmentTypeToggle from "./AssessmentTypeToggle";

const STORAGE_PREFIX = "sns-hospice-solutions-comprehensive-psychosocial";

const CLINICAL_BRAND = {
  navy: "#1E3A5F",
  teal: "#0D9488",
  tealDark: "#0F766E",
  tealLight: "#CCFBF1",
  bg: "#F8FAFC",
  canvas: "#EEF3F8",
  panel: "#FFFFFF",
  line: "#D8E3E8",
  text: "#0F172A",
  muted: "#64748B",
  slate: "#334155",
};

const YES_NO = ["", "Yes", "No"];
const YES_NO_NA = ["", "Yes", "No", "N/A"];
const GOOD_FAIR_POOR = ["", "Good", "Fair", "Poor"];
const NONE_MILD_MODERATE_SEVERE = ["", "None", "Mild", "Moderate", "Severe"];
const ASSESSMENT_SECTIONS = [
  { key: "pain", label: "1. Pain" },
  { key: "psychosocial", label: "2. Psychosocial Circumstances" },
  { key: "patientDistress", label: "3. Patient – Psychosocial Distress/Concerns" },
  { key: "familyDistress", label: "4. Family – Psychosocial Distress/Concerns" },
  { key: "financial", label: "5. Financial/Legal Needs" },
  { key: "referrals", label: "6. Referrals" },
  { key: "narrative", label: "7. Narrative" },
  { key: "signature", label: "Signature" },
];

const INITIAL_FORM = {
  visitMeta: {
    typeOfVisit: "",
    visitKind: "",
    visitKindSpecify: "",
    assessmentType: "update",
    visitDate: "",
    timeIn: "",
    timeOut: "",
    duration: "",
    enteredBy: "",
    staffAssigned: "",
    discipline: "MSW",
    careLevel: "",
  },
  pain: {
    uncomfortable: "",
    painLevel: "",
  },
  psychosocial: {
    mentalStatus: "",
    historian: "",
    historianOtherName: "",
    historianOtherRelation: "",
    maritalStatus: "",
    childrenUnder21: "",
    childrenInHome: "",
    familyPcgName: "",
    familyPcgRelation: "",
    hiredHowLong: "",
    patientLives: "",
    livingArrangement: "",
    familyCommunication: "",
    familyRelation: "",
    familyResponseToIllness: "",
    patientSocialInteraction: "",
    supportSystem: "",
    otherSupportPersons: [
      { name: "", phone: "", purpose: "" },
      { name: "", phone: "", purpose: "" },
    ],
    communitySupportSystems: "",
    comment: "",
  },
  patientDistress: {
    responseToIllness: [],
    responseOther: "",
    concerns: [],
    concernsOther: "",
    iadl: {
      phone: { independent: "", supportWho: "" },
      shopping: { independent: "", supportWho: "" },
      meals: { independent: "", supportWho: "" },
      housework: { independent: "", supportWho: "" },
      finances: { independent: "", supportWho: "" },
    },
    anxietyRating: "",
    anxietyRatedBy: "",
    distressRating: "",
    distressRatedBy: "",
    comment: "",
  },
  familyDistress: {
    responseToIllness: [],
    responseOther: "",
    abilityToProvideCare: "",
    willingnessToProvideCare: "",
    crisis: [],
    crisisOther: "",
    anxietyRating: "",
    anxietyRatedBy: "",
    comment: "",
  },
  financial: {
    allNeedsMet: "",
    veteran: "",
    lacks: [],
    assistance: [],
    assistanceOther: "",
    paidBy: [],
    advanceDirectives: {
      livingWill: { has: "", copyProvided: "", needHelp: "" },
      healthPoa: { has: "", copyProvided: "", needHelp: "" },
      healthProxy: { has: "", copyProvided: "", needHelp: "" },
      burialPlans: { has: "", copyProvided: "", needHelp: "" },
    },
    mortuary: {
      name: "",
      phone: "",
      address: "",
      city: "",
      stateZip: "",
    },
    comment: "",
  },
  referrals: {
    needCommunityReferral: "",
    referralAccepted: "",
    referralTypes: [],
    communitySupport: "",
    other: "",
  },
  narrative: {
    careProvided: [],
    careProvidedOther: "",
    noteOne: "",
    noteTwo: "",
  },
  signature: {
    patientPcgAcknowledgement: "",
    signedByName: "",
    signedByCredentials: "",
    signedDate: "",
    reviewerName: "",
    reviewerCredentials: "",
    reviewerDate: "",
  },
};

const styles = {
  page: { minHeight: "100vh", background: CLINICAL_BRAND.canvas },
  frame: { maxWidth: 1220, margin: "0 auto", padding: "24px 0" },
  shell: { display: "grid", gridTemplateColumns: "260px 1fr", gap: 12 },
  sidebar: { width: 260, minWidth: 260, paddingTop: 3 },
  patientCard: { border: `1px solid ${CLINICAL_BRAND.line}`, background: CLINICAL_BRAND.panel, fontSize: 11, marginBottom: 12, borderRadius: 12, overflow: "hidden" },
  patientCardHeader: { background: "linear-gradient(90deg, #1E3A5F 0%, #0D9488 100%)", color: "#fff", borderBottom: `1px solid ${CLINICAL_BRAND.navy}`, padding: "6px 10px", fontWeight: 700 },
  navCard: { border: `1px solid ${CLINICAL_BRAND.line}`, background: CLINICAL_BRAND.panel, borderRadius: 12, overflow: "hidden" },
  navHeader: { background: "#EDF7F7", borderBottom: `1px solid ${CLINICAL_BRAND.line}`, padding: "6px 10px", fontWeight: 700 },
  navBody: { padding: 8, maxHeight: 700, overflow: "auto" },
  navButton: {
    width: "100%",
    textAlign: "left",
    border: "none",
    background: "transparent",
    color: "#0f172a",
    fontSize: 12,
    padding: "6px 8px",
    cursor: "pointer",
    borderRadius: 8,
  },
  main: { background: "#f4f7f9", border: `1px solid ${CLINICAL_BRAND.line}`, boxShadow: "0 12px 28px rgba(15, 23, 42, 0.08)", borderRadius: 14, overflow: "hidden" },
  header: { borderBottom: `1px solid ${CLINICAL_BRAND.line}`, padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", background: "linear-gradient(90deg, #1E3A5F 0%, #0D9488 100%)", color: "#fff" },
  headerTitle: { fontSize: 18, fontWeight: 700 },
  headerSub: { fontSize: 11, color: "rgba(255,255,255,0.88)" },
  progress: { fontSize: 11, fontWeight: 700, textAlign: "right" },
  content: { padding: 24 },
  metaBar: {
    padding: "16px 24px",
    background: "#F8FAFC",
    borderBottom: `1px solid ${CLINICAL_BRAND.line}`,
  },
  sectionCard: { border: `1px solid ${CLINICAL_BRAND.line}`, marginBottom: 14, background: CLINICAL_BRAND.panel, borderRadius: 12, overflow: "hidden" },
  sectionHeader: { background: "#F8FAFC", borderBottom: `1px solid ${CLINICAL_BRAND.line}`, padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" },
  sectionTitle: { fontSize: 14, fontWeight: 700, fontStyle: "italic", color: CLINICAL_BRAND.text },
  sectionHint: { fontSize: 10, color: CLINICAL_BRAND.muted },
  sectionBody: { padding: 12 },
  fieldLabel: { display: "block", fontSize: 11, fontWeight: 700, marginBottom: 4, color: CLINICAL_BRAND.slate },
  input: { width: "100%", boxSizing: "border-box", padding: "8px 10px", border: "1px solid #c8d5df", borderRadius: 10, background: "#fff", fontSize: 13 },
  textarea: { width: "100%", boxSizing: "border-box", padding: "8px 10px", border: "1px solid #c8d5df", borderRadius: 10, fontSize: 13, lineHeight: 1.4, resize: "vertical" },
  select: { width: "100%", boxSizing: "border-box", padding: "8px 10px", border: "1px solid #c8d5df", borderRadius: 10, background: "#fff", fontSize: 13 },
  checkboxLabel: { display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, color: "#111827" },
  button: { border: `1px solid ${CLINICAL_BRAND.teal}`, background: "#fff", color: CLINICAL_BRAND.tealDark, borderRadius: 10, padding: "8px 14px", fontSize: 12, cursor: "pointer", fontWeight: 700 },
  stubButton: { border: "1px dashed #94a3b8", background: "#f8fafc", color: "#475569", borderRadius: 10, padding: "8px 14px", fontSize: 12, cursor: "not-allowed", fontWeight: 700 },
  footer: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, paddingTop: 8, flexWrap: "wrap" },
  statusPill: { display: "inline-flex", alignItems: "center", borderRadius: 999, padding: "4px 8px", fontSize: 10, fontWeight: 800, textTransform: "uppercase", background: "#dcfce7", color: "#166534" },
  mutedBox: { border: `1px solid ${CLINICAL_BRAND.line}`, background: "#F8FAFC", borderRadius: 12, padding: 12, fontSize: 12, color: CLINICAL_BRAND.slate },
  alert: { marginBottom: 12, padding: 10, border: "1px solid #f59e0b", background: "#fff7ed", color: "#9a3412", fontSize: 12, borderRadius: 10 },
};

function deepMerge(base, incoming) {
  if (!incoming || typeof incoming !== "object" || Array.isArray(incoming)) {
    return incoming ?? base;
  }
  const result = Array.isArray(base) ? [...base] : { ...base };
  Object.keys(incoming).forEach((key) => {
    if (Array.isArray(incoming[key])) {
      result[key] = incoming[key];
    } else if (incoming[key] && typeof incoming[key] === "object") {
      result[key] = deepMerge(base?.[key] ?? {}, incoming[key]);
    } else {
      result[key] = incoming[key];
    }
  });
  return result;
}

function readStoredForm(patientId) {
  const raw = localStorage.getItem(`${STORAGE_PREFIX}:${patientId}`);
  if (!raw) return INITIAL_FORM;
  try {
    return deepMerge(INITIAL_FORM, JSON.parse(raw));
  } catch {
    return INITIAL_FORM;
  }
}

function toggleValue(values, value) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

function formatDuration(timeIn, timeOut) {
  if (!timeIn || !timeOut) return "";
  const [startHour, startMinute] = timeIn.split(":").map(Number);
  const [endHour, endMinute] = timeOut.split(":").map(Number);
  if ([startHour, startMinute, endHour, endMinute].some((value) => Number.isNaN(value))) return "";
  const start = startHour * 60 + startMinute;
  const end = endHour * 60 + endMinute;
  if (end <= start) return "";
  const diff = end - start;
  const hours = Math.floor(diff / 60);
  const minutes = diff % 60;
  return `${hours}h ${minutes}m`;
}

function selectOptions(values) {
  return values.map((value) => (
    <option key={value || "blank"} value={value}>
      {value || "Select"}
    </option>
  ));
}

function Field({ label, children, hint }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <label style={styles.fieldLabel}>{label}</label>
      {children}
      {hint ? <div style={{ marginTop: 4, fontSize: 11, color: "#64748b" }}>{hint}</div> : null}
    </div>
  );
}

function Card({ title, subtitle, id, children }) {
  return (
    <section id={id} style={styles.sectionCard}>
      <div style={styles.sectionHeader}>
        <div>
          <div style={styles.sectionTitle}>{title}</div>
          {subtitle ? <div style={styles.sectionHint}>{subtitle}</div> : null}
        </div>
      </div>
      <div style={styles.sectionBody}>{children}</div>
    </section>
  );
}

function CheckboxGrid({ options, values, onToggle, columns = 2 }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`, gap: 6 }}>
      {options.map((option) => (
        <label key={option} style={styles.checkboxLabel}>
          <input type="checkbox" checked={values.includes(option)} onChange={() => onToggle(option)} />
          {option}
        </label>
      ))}
    </div>
  );
}

export default function ComprehensivePsychosocialAssessment({ patientId = getActivePatientId() ?? "" }) {
  const currentUser = useMemo(() => getCurrentUser(), []);
  const [patientSummary, setPatientSummary] = useState(null);
  const [patientSummaryError, setPatientSummaryError] = useState("");
  const [formData, setFormData] = useState(() => readStoredForm(patientId));
  const [saveStatus, setSaveStatus] = useState(null);
  const [lastSavedAt, setLastSavedAt] = useState("");

  useEffect(() => {
    let mounted = true;
    setPatientSummaryError("");
    fetchPatientSummary(patientId)
      .then((summary) => {
        if (!mounted) return;
        setPatientSummary(summary);
      })
      .catch((error) => {
        console.error("Failed to load psychosocial assessment patient summary:", error);
        if (mounted) {
          setPatientSummaryError(error instanceof Error ? error.message : "Unable to load patient summary.");
        }
      });
    return () => {
      mounted = false;
    };
  }, [patientId]);

  useEffect(() => {
    const saved = readStoredForm(patientId);
    setFormData((prev) =>
      deepMerge(saved, {
        visitMeta: {
          enteredBy: saved.visitMeta?.enteredBy || currentUser?.full_name || "",
          discipline: saved.visitMeta?.discipline || "MSW",
        },
      }),
    );
    setSaveStatus(null);
    setLastSavedAt("");
  }, [currentUser?.full_name, patientId]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_PREFIX}:${patientId}`, JSON.stringify(formData));
  }, [formData, patientId]);

  useEffect(() => {
    const computed = formatDuration(formData.visitMeta.timeIn, formData.visitMeta.timeOut);
    if (computed && computed !== formData.visitMeta.duration) {
      setFormData((prev) => ({
        ...prev,
        visitMeta: {
          ...prev.visitMeta,
          duration: computed,
        },
      }));
    }
  }, [formData.visitMeta.duration, formData.visitMeta.timeIn, formData.visitMeta.timeOut]);

  useEffect(() => {
    if (!patientSummary) return;
    const mswStaff = patientSummary.care_team.find((member) => String(member.discipline || "").toUpperCase().includes("MSW"));
    setFormData((prev) => ({
      ...prev,
      visitMeta: {
        ...prev.visitMeta,
        staffAssigned: prev.visitMeta.staffAssigned || mswStaff?.staff_name || currentUser?.full_name || "",
        careLevel: prev.visitMeta.careLevel || patientSummary.patient.acuity_state || "",
      },
      signature: {
        ...prev.signature,
        reviewerName: prev.signature.reviewerName || mswStaff?.staff_name || "",
      },
    }));
  }, [currentUser?.full_name, patientSummary]);

  const updateSection = (section, key, value) => {
    setFormData((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
    setSaveStatus(null);
  };

  const updateNested = (section, parent, key, value) => {
    setFormData((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [parent]: {
          ...prev[section][parent],
          [key]: value,
        },
      },
    }));
    setSaveStatus(null);
  };

  const updateDirective = (directive, key, value) => {
    setFormData((prev) => ({
      ...prev,
      financial: {
        ...prev.financial,
        advanceDirectives: {
          ...prev.financial.advanceDirectives,
          [directive]: {
            ...prev.financial.advanceDirectives[directive],
            [key]: value,
          },
        },
      },
    }));
    setSaveStatus(null);
  };

  const updateIadl = (key, field, value) => {
    setFormData((prev) => ({
      ...prev,
      patientDistress: {
        ...prev.patientDistress,
        iadl: {
          ...prev.patientDistress.iadl,
          [key]: {
            ...prev.patientDistress.iadl[key],
            [field]: value,
          },
        },
      },
    }));
    setSaveStatus(null);
  };

  const updateSupportPerson = (index, key, value) => {
    setFormData((prev) => ({
      ...prev,
      psychosocial: {
        ...prev.psychosocial,
        otherSupportPersons: prev.psychosocial.otherSupportPersons.map((row, rowIndex) =>
          rowIndex === index ? { ...row, [key]: value } : row,
        ),
      },
    }));
    setSaveStatus(null);
  };

  const handleSave = () => {
    localStorage.setItem(`${STORAGE_PREFIX}:${patientId}`, JSON.stringify(formData));
    setLastSavedAt(new Date().toLocaleString());
    setSaveStatus("saved");
  };

  const patientName = patientSummary?.patient?.full_name || "Patient";
  const mswReviewerName = formData.signature.reviewerName || "MSW Reviewer";
  const mswReviewerCredentials = formData.signature.reviewerCredentials || "MSW";
  const completedFields = useMemo(() => {
    const countValues = (value) => {
      if (Array.isArray(value)) return value.filter(Boolean).length;
      if (value && typeof value === "object") return Object.values(value).reduce((sum, item) => sum + countValues(item), 0);
      return value ? 1 : 0;
    };
    return countValues(formData);
  }, [formData]);

  const visitTypeLabel = formData.visitMeta.assessmentType === "recert" ? "Recertification Assessment" : "Update Assessment";

  const gotoSection = (section) => {
    document.getElementById(section)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div style={styles.page}>
      <div style={styles.frame}>
        <div style={styles.shell}>
          <aside style={styles.sidebar}>
            <div style={{ fontSize: 13, color: "#0f172a", fontWeight: 700, marginBottom: 8, paddingLeft: 2 }}>
              {currentUser?.tenant_name || "Love & Faith Hospice Services, Inc."}
            </div>
            <div style={styles.patientCard}>
              <div style={styles.patientCardHeader}>Patient</div>
              <div style={{ padding: 8 }}>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{patientName}</div>
                <div style={{ fontSize: 11, color: "#475569", marginTop: 4 }}>{patientSummary?.patient?.mrn || "MRN not loaded"}</div>
                <div style={{ fontSize: 11, color: "#475569", marginTop: 6 }}>Primary Dx: {patientSummary?.patient?.primary_diagnosis || "Pending"}</div>
              </div>
            </div>
            <div style={styles.navCard}>
              <div style={styles.navHeader}>Navigation</div>
              <div style={styles.navBody}>
                {ASSESSMENT_SECTIONS.map((section) => (
                  <button key={section.key} type="button" onClick={() => gotoSection(section.key)} style={styles.navButton}>
                    {section.label}
                  </button>
                ))}
              </div>
            </div>
          </aside>

          <main style={styles.main}>
            <div style={styles.header}>
              <div>
                <div style={styles.headerTitle}>Comprehensive Psychosocial Assessment</div>
                <div style={styles.headerSub}>Ongoing MSW assessment for change in condition or recertification visits</div>
              </div>
              <div style={styles.progress}>
                <div>{visitTypeLabel}</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.82)", marginTop: 4 }}>{completedFields} documented value(s)</div>
              </div>
            </div>

            <div style={styles.metaBar}>
              <div style={{ marginBottom: 14 }}>
                <AssessmentTypeToggle
                  value={formData.visitMeta.assessmentType}
                  onChange={(value) => updateSection("visitMeta", "assessmentType", value)}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12, marginBottom: 12 }}>
                <Field label="Type of Visit">
                  <select value={formData.visitMeta.typeOfVisit} onChange={(e) => updateSection("visitMeta", "typeOfVisit", e.target.value)} style={styles.select}>
                    {selectOptions(["", "In-Person", "Telephone", "Video"])}
                  </select>
                </Field>
                <Field label="Visit">
                  <select value={formData.visitMeta.visitKind} onChange={(e) => updateSection("visitMeta", "visitKind", e.target.value)} style={styles.select}>
                    {selectOptions(["", "Scheduled", "Unscheduled", "Other"])}
                  </select>
                </Field>
                <Field label="Visit Date">
                  <input type="date" value={formData.visitMeta.visitDate} onChange={(e) => updateSection("visitMeta", "visitDate", e.target.value)} style={styles.input} />
                </Field>
                <Field label="Duration (h:m)">
                  <input value={formData.visitMeta.duration} onChange={(e) => updateSection("visitMeta", "duration", e.target.value)} style={styles.input} placeholder="1h 15m" />
                </Field>
              </div>

              {formData.visitMeta.visitKind === "Other" && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12, marginBottom: 12 }}>
                  <Field label="Visit specify">
                    <input
                      value={formData.visitMeta.visitKindSpecify}
                      onChange={(e) => updateSection("visitMeta", "visitKindSpecify", e.target.value)}
                      style={styles.input}
                    />
                  </Field>
                </div>
              )}

              <div style={{ display: "grid", gridTemplateColumns: "repeat(6, minmax(0, 1fr))", gap: 12 }}>
                <Field label="Time In">
                  <input type="time" value={formData.visitMeta.timeIn} onChange={(e) => updateSection("visitMeta", "timeIn", e.target.value)} style={styles.input} />
                </Field>
                <Field label="Time Out">
                  <input type="time" value={formData.visitMeta.timeOut} onChange={(e) => updateSection("visitMeta", "timeOut", e.target.value)} style={styles.input} />
                </Field>
                <Field label="Entered By">
                  <input value={formData.visitMeta.enteredBy} onChange={(e) => updateSection("visitMeta", "enteredBy", e.target.value)} style={styles.input} />
                </Field>
                <Field label="Staff Assigned">
                  <input value={formData.visitMeta.staffAssigned} onChange={(e) => updateSection("visitMeta", "staffAssigned", e.target.value)} style={styles.input} />
                </Field>
                <Field label="Discipline">
                  <input value={formData.visitMeta.discipline} onChange={(e) => updateSection("visitMeta", "discipline", e.target.value)} style={styles.input} />
                </Field>
                <Field label="Care Level">
                  <input value={formData.visitMeta.careLevel} onChange={(e) => updateSection("visitMeta", "careLevel", e.target.value)} style={styles.input} />
                </Field>
              </div>
            </div>

            <div style={styles.content}>
              {patientSummaryError ? <div style={styles.alert}>Patient summary: {patientSummaryError}</div> : null}

              <Card title="1. Pain" subtitle="Pain screening and pain tool placeholder" id="pain">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 220px", gap: 12, alignItems: "end" }}>
                  <Field label="Are you uncomfortable because of pain?">
                    <select value={formData.pain.uncomfortable} onChange={(e) => updateSection("pain", "uncomfortable", e.target.value)} style={styles.select}>
                      {selectOptions(YES_NO)}
                    </select>
                  </Field>
                  <Field label="If Yes, what is the pain level?">
                    <input
                      type="number"
                      min="0"
                      max="10"
                      value={formData.pain.painLevel}
                      onChange={(e) => updateSection("pain", "painLevel", e.target.value)}
                      style={styles.input}
                      disabled={formData.pain.uncomfortable !== "Yes"}
                    />
                  </Field>
                  <button type="button" style={styles.stubButton} disabled>
                    Pain Assessment Tool
                  </button>
                </div>
              </Card>

              <Card title="2. Psychosocial Circumstances" subtitle="Living situation, family support, and social context" id="psychosocial">
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Observed patient mental status">
                    <select value={formData.psychosocial.mentalStatus} onChange={(e) => updateSection("psychosocial", "mentalStatus", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Awake", "Alert", "Oriented", "Confused", "Drowsy", "Withdrawn", "Tearful"])}
                    </select>
                  </Field>
                  <Field label="Historian">
                    <select value={formData.psychosocial.historian} onChange={(e) => updateSection("psychosocial", "historian", e.target.value)} style={styles.select}>
                      {selectOptions(["", "PCG", "Patient", "Other"])}
                    </select>
                  </Field>
                  <Field label="Marital Status">
                    <select value={formData.psychosocial.maritalStatus} onChange={(e) => updateSection("psychosocial", "maritalStatus", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Widowed", "Married", "Single", "Divorced", "Separated", "Partnered"])}
                    </select>
                  </Field>
                  <Field label="Patient lives">
                    <input value={formData.psychosocial.patientLives} onChange={(e) => updateSection("psychosocial", "patientLives", e.target.value)} style={styles.input} placeholder="e.g. in ALF" />
                  </Field>
                </div>

                {formData.psychosocial.historian === "Other" && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <Field label="Historian Name">
                      <input
                        value={formData.psychosocial.historianOtherName}
                        onChange={(e) => updateSection("psychosocial", "historianOtherName", e.target.value)}
                        style={styles.input}
                      />
                    </Field>
                    <Field label="Historian Relation">
                      <input
                        value={formData.psychosocial.historianOtherRelation}
                        onChange={(e) => updateSection("psychosocial", "historianOtherRelation", e.target.value)}
                        style={styles.input}
                      />
                    </Field>
                  </div>
                )}

                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Number of children under 21">
                    <input type="number" min="0" value={formData.psychosocial.childrenUnder21} onChange={(e) => updateSection("psychosocial", "childrenUnder21", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="Number of children living in patient's home">
                    <input type="number" min="0" value={formData.psychosocial.childrenInHome} onChange={(e) => updateSection("psychosocial", "childrenInHome", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="Family/PCG Name">
                    <input value={formData.psychosocial.familyPcgName} onChange={(e) => updateSection("psychosocial", "familyPcgName", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="Relation">
                    <input value={formData.psychosocial.familyPcgRelation} onChange={(e) => updateSection("psychosocial", "familyPcgRelation", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="If hired, for how long">
                    <input value={formData.psychosocial.hiredHowLong} onChange={(e) => updateSection("psychosocial", "hiredHowLong", e.target.value)} style={styles.input} />
                  </Field>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Living arrangement is" hint='If "Other", specify in narrative'>
                    <select value={formData.psychosocial.livingArrangement} onChange={(e) => updateSection("psychosocial", "livingArrangement", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Satisfactory", "Other"])}
                    </select>
                  </Field>
                  <Field label="Family communication is">
                    <select value={formData.psychosocial.familyCommunication} onChange={(e) => updateSection("psychosocial", "familyCommunication", e.target.value)} style={styles.select}>
                      {selectOptions(GOOD_FAIR_POOR)}
                    </select>
                  </Field>
                  <Field label="Family relation is">
                    <select value={formData.psychosocial.familyRelation} onChange={(e) => updateSection("psychosocial", "familyRelation", e.target.value)} style={styles.select}>
                      {selectOptions(GOOD_FAIR_POOR)}
                    </select>
                  </Field>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Family Response to Illness is" hint='If "Other", specify in narrative'>
                    <select value={formData.psychosocial.familyResponseToIllness} onChange={(e) => updateSection("psychosocial", "familyResponseToIllness", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Supportive", "Other"])}
                    </select>
                  </Field>
                  <Field label="Does patient have social interaction as desired?">
                    <select value={formData.psychosocial.patientSocialInteraction} onChange={(e) => updateSection("psychosocial", "patientSocialInteraction", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Satisfactory", "Other"])}
                    </select>
                  </Field>
                  <Field label="Support System">
                    <select value={formData.psychosocial.supportSystem} onChange={(e) => updateSection("psychosocial", "supportSystem", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Family", "Friends", "None", "Other"])}
                    </select>
                  </Field>
                </div>

                <div style={styles.mutedBox}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>Other Support persons/groups</div>
                  {formData.psychosocial.otherSupportPersons.map((row, index) => (
                    <div key={`support-person-${index}`} style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr", gap: 12, marginBottom: index === 0 ? 12 : 0 }}>
                      <Field label={`Name ${index + 1}`}>
                        <input value={row.name} onChange={(e) => updateSupportPerson(index, "name", e.target.value)} style={styles.input} />
                      </Field>
                      <Field label="Phone">
                        <input value={row.phone} onChange={(e) => updateSupportPerson(index, "phone", e.target.value)} style={styles.input} />
                      </Field>
                      <Field label='"For"'>
                        <input value={row.purpose} onChange={(e) => updateSupportPerson(index, "purpose", e.target.value)} style={styles.input} />
                      </Field>
                    </div>
                  ))}
                </div>

                <Field label="List community support systems in use">
                  <textarea value={formData.psychosocial.communitySupportSystems} onChange={(e) => updateSection("psychosocial", "communitySupportSystems", e.target.value)} style={styles.textarea} rows={3} />
                </Field>
                <Field label="Comment">
                  <textarea value={formData.psychosocial.comment} onChange={(e) => updateSection("psychosocial", "comment", e.target.value.slice(0, 500))} style={styles.textarea} rows={4} maxLength={500} />
                </Field>
              </Card>

              <Card title="3. Patient – Psychosocial Distress/Concerns" subtitle="Patient response, concerns, IADL, and ratings" id="patientDistress">
                <Field label="Patient response to illness">
                  <CheckboxGrid
                    options={["Cannot respond", "Overwhelmed", "Fearful", "Unaware of Condition", "Accepting", "Depressed", "Sad", "Guilt", "Denial", "Angry", "Loss of worth", "Other"]}
                    values={formData.patientDistress.responseToIllness}
                    onToggle={(option) => updateSection("patientDistress", "responseToIllness", toggleValue(formData.patientDistress.responseToIllness, option))}
                    columns={3}
                  />
                </Field>
                {formData.patientDistress.responseToIllness.includes("Other") && (
                  <Field label="Patient response to illness — other">
                    <input value={formData.patientDistress.responseOther} onChange={(e) => updateSection("patientDistress", "responseOther", e.target.value)} style={styles.input} />
                  </Field>
                )}

                <Field label="Patient Concerns">
                  <CheckboxGrid
                    options={["Responsibility for others", "Finances", "Lacks Cognitive Ability to Understand", "None", "Suicide Risks", "Inadequate food/supplies", "Abuse/neglect", "Hx or present substance/alcohol abuse", "Transfer to another setting", "Other"]}
                    values={formData.patientDistress.concerns}
                    onToggle={(option) => updateSection("patientDistress", "concerns", toggleValue(formData.patientDistress.concerns, option))}
                    columns={3}
                  />
                </Field>
                {(formData.patientDistress.concerns.includes("Other") || formData.patientDistress.concerns.includes("Lacks Cognitive Ability to Understand")) && (
                  <Field label="Patient concerns — narrative note">
                    <input value={formData.patientDistress.concernsOther} onChange={(e) => updateSection("patientDistress", "concernsOther", e.target.value)} style={styles.input} />
                  </Field>
                )}

                <div style={styles.mutedBox}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>Instrumental Activities of Daily Living (IADL)</div>
                  {[
                    ["phone", "Access to phone / able to make calls?", "If No, form of communication / alternate"],
                    ["shopping", "Goes out for shopping?", "If No, who shops for patient"],
                    ["meals", "Prepares own meals?", "If No, who prepares meals"],
                    ["housework", "Does housework?", "If No, who does housework"],
                    ["finances", "Manages own finances?", "If No, who manages finances"],
                  ].map(([key, label, helper]) => (
                    <div key={key} style={{ display: "grid", gridTemplateColumns: "1.3fr 200px 1fr", gap: 12, alignItems: "end", marginBottom: 10 }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: CLINICAL_BRAND.slate }}>{label}</div>
                      <Field label="Yes / No">
                        <select value={formData.patientDistress.iadl[key].independent} onChange={(e) => updateIadl(key, "independent", e.target.value)} style={styles.select}>
                          {selectOptions(YES_NO)}
                        </select>
                      </Field>
                      <Field label={helper}>
                        <input
                          value={formData.patientDistress.iadl[key].supportWho}
                          onChange={(e) => updateIadl(key, "supportWho", e.target.value)}
                          style={styles.input}
                          disabled={formData.patientDistress.iadl[key].independent !== "No"}
                        />
                      </Field>
                    </div>
                  ))}
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Patient Anxiety Rating">
                    <select value={formData.patientDistress.anxietyRating} onChange={(e) => updateSection("patientDistress", "anxietyRating", e.target.value)} style={styles.select}>
                      {selectOptions(NONE_MILD_MODERATE_SEVERE)}
                    </select>
                  </Field>
                  <Field label="Rated by">
                    <select value={formData.patientDistress.anxietyRatedBy} onChange={(e) => updateSection("patientDistress", "anxietyRatedBy", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Patient", "Clinician"])}
                    </select>
                  </Field>
                  <Field label="Patient Psychosocial Distress Rating">
                    <select value={formData.patientDistress.distressRating} onChange={(e) => updateSection("patientDistress", "distressRating", e.target.value)} style={styles.select}>
                      {selectOptions(NONE_MILD_MODERATE_SEVERE)}
                    </select>
                  </Field>
                  <Field label="Rated by">
                    <select value={formData.patientDistress.distressRatedBy} onChange={(e) => updateSection("patientDistress", "distressRatedBy", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Patient", "Clinician"])}
                    </select>
                  </Field>
                </div>

                <Field label="Comment">
                  <textarea value={formData.patientDistress.comment} onChange={(e) => updateSection("patientDistress", "comment", e.target.value.slice(0, 500))} style={styles.textarea} rows={4} maxLength={500} />
                </Field>
              </Card>

              <Card title="4. Family – Psychosocial Distress/Concerns" subtitle="Family coping, crisis, and caregiver readiness" id="familyDistress">
                <Field label="Family response to illness">
                  <CheckboxGrid
                    options={["Accepting", "Depressed", "Sad", "Guilt", "Denial", "Angry", "Fearful", "Despair", "Overwhelmed", "Anticipatory grieving", "Other"]}
                    values={formData.familyDistress.responseToIllness}
                    onToggle={(option) => updateSection("familyDistress", "responseToIllness", toggleValue(formData.familyDistress.responseToIllness, option))}
                    columns={3}
                  />
                </Field>
                {formData.familyDistress.responseToIllness.includes("Other") && (
                  <Field label="Family response to illness — other">
                    <input value={formData.familyDistress.responseOther} onChange={(e) => updateSection("familyDistress", "responseOther", e.target.value)} style={styles.input} />
                  </Field>
                )}

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Field label="Ability to provide care">
                    <select value={formData.familyDistress.abilityToProvideCare} onChange={(e) => updateSection("familyDistress", "abilityToProvideCare", e.target.value)} style={styles.select}>
                      {selectOptions(GOOD_FAIR_POOR)}
                    </select>
                  </Field>
                  <Field label="Willingness to provide care">
                    <select value={formData.familyDistress.willingnessToProvideCare} onChange={(e) => updateSection("familyDistress", "willingnessToProvideCare", e.target.value)} style={styles.select}>
                      {selectOptions(GOOD_FAIR_POOR)}
                    </select>
                  </Field>
                </div>

                <Field label="Family crisis">
                  <CheckboxGrid
                    options={["None", "Suicide Risks", "Inadequate food/supplies", "Death will precipitate financial/legal crisis", "Significant losses in recent past", "Hx or present substance/alcohol abuse", "Other"]}
                    values={formData.familyDistress.crisis}
                    onToggle={(option) => updateSection("familyDistress", "crisis", toggleValue(formData.familyDistress.crisis, option))}
                    columns={3}
                  />
                </Field>
                {formData.familyDistress.crisis.includes("Other") && (
                  <Field label="Family crisis — other">
                    <input value={formData.familyDistress.crisisOther} onChange={(e) => updateSection("familyDistress", "crisisOther", e.target.value)} style={styles.input} />
                  </Field>
                )}

                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="PCG Family Anxiety Rating">
                    <select value={formData.familyDistress.anxietyRating} onChange={(e) => updateSection("familyDistress", "anxietyRating", e.target.value)} style={styles.select}>
                      {selectOptions(NONE_MILD_MODERATE_SEVERE)}
                    </select>
                  </Field>
                  <Field label="Rated by">
                    <select value={formData.familyDistress.anxietyRatedBy} onChange={(e) => updateSection("familyDistress", "anxietyRatedBy", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Patient", "Clinician"])}
                    </select>
                  </Field>
                </div>

                <Field label="Comment">
                  <textarea value={formData.familyDistress.comment} onChange={(e) => updateSection("familyDistress", "comment", e.target.value.slice(0, 500))} style={styles.textarea} rows={4} maxLength={500} />
                </Field>
              </Card>

              <Card title="5. Financial/Legal Needs" subtitle="Financial supports, advance directives, and mortuary information" id="financial">
                <Field label="Financial: All needs met by patient and/or family">
                  <select value={formData.financial.allNeedsMet} onChange={(e) => updateSection("financial", "allNeedsMet", e.target.value)} style={styles.select}>
                    {selectOptions(YES_NO)}
                  </select>
                </Field>

                {formData.financial.allNeedsMet === "No" && (
                  <>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                      <Field label="Is Patient/Spouse a Veteran?">
                        <select value={formData.financial.veteran} onChange={(e) => updateSection("financial", "veteran", e.target.value)} style={styles.select}>
                          {selectOptions(YES_NO)}
                        </select>
                      </Field>
                    </div>

                    <Field label="Patient lacks">
                      <CheckboxGrid
                        options={["Food", "Utility", "Clothing", "Furniture", "Med/supplies unrelated to illness"]}
                        values={formData.financial.lacks}
                        onToggle={(option) => updateSection("financial", "lacks", toggleValue(formData.financial.lacks, option))}
                      />
                    </Field>

                    <Field label="Needs assistance with">
                      <CheckboxGrid
                        options={["Meal on wheels", "Food Stamps", "Other"]}
                        values={formData.financial.assistance}
                        onToggle={(option) => updateSection("financial", "assistance", toggleValue(formData.financial.assistance, option))}
                      />
                    </Field>
                    {formData.financial.assistance.includes("Other") && (
                      <Field label="Needs assistance with — other">
                        <input value={formData.financial.assistanceOther} onChange={(e) => updateSection("financial", "assistanceOther", e.target.value)} style={styles.input} />
                      </Field>
                    )}

                    <Field label="Patient care paid by">
                      <CheckboxGrid
                        options={["Private pay", "Indigent (Non-funded charity Patient)", "Insufficient financial reserves – may be Medicaid eligible"]}
                        values={formData.financial.paidBy}
                        onToggle={(option) => updateSection("financial", "paidBy", toggleValue(formData.financial.paidBy, option))}
                      />
                    </Field>
                    {formData.financial.paidBy.includes("Insufficient financial reserves – may be Medicaid eligible") && (
                      <div style={{ marginBottom: 12 }}>
                        <button type="button" style={styles.stubButton} disabled>
                          Financial Assessment
                        </button>
                      </div>
                    )}
                  </>
                )}

                <div style={styles.mutedBox}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>Planning / Advance Directive</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1.2fr repeat(3, 1fr)", gap: 12, marginBottom: 8, fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.muted }}>
                    <div>Directive</div>
                    <div>Does patient/family have?</div>
                    <div>Copy provided</div>
                    <div>Need help</div>
                  </div>
                  {[
                    ["livingWill", "Living Will"],
                    ["healthPoa", "Health POA"],
                    ["healthProxy", "Health Proxy"],
                    ["burialPlans", "Burial plans"],
                  ].map(([key, label]) => (
                    <div key={key} style={{ display: "grid", gridTemplateColumns: "1.2fr repeat(3, 1fr)", gap: 12, marginBottom: 10, alignItems: "center" }}>
                      <div style={{ fontSize: 12, color: CLINICAL_BRAND.slate }}>{label}</div>
                      <select value={formData.financial.advanceDirectives[key].has} onChange={(e) => updateDirective(key, "has", e.target.value)} style={styles.select}>
                        {selectOptions(YES_NO_NA)}
                      </select>
                      <select value={formData.financial.advanceDirectives[key].copyProvided} onChange={(e) => updateDirective(key, "copyProvided", e.target.value)} style={styles.select}>
                        {selectOptions(YES_NO_NA)}
                      </select>
                      <select value={formData.financial.advanceDirectives[key].needHelp} onChange={(e) => updateDirective(key, "needHelp", e.target.value)} style={styles.select}>
                        {selectOptions(YES_NO_NA)}
                      </select>
                    </div>
                  ))}
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Field label="Mortuary Name">
                    <input value={formData.financial.mortuary.name} onChange={(e) => updateNested("financial", "mortuary", "name", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="Phone No">
                    <input value={formData.financial.mortuary.phone} onChange={(e) => updateNested("financial", "mortuary", "phone", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="Address">
                    <input value={formData.financial.mortuary.address} onChange={(e) => updateNested("financial", "mortuary", "address", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="City">
                    <input value={formData.financial.mortuary.city} onChange={(e) => updateNested("financial", "mortuary", "city", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="State-Zip">
                    <input value={formData.financial.mortuary.stateZip} onChange={(e) => updateNested("financial", "mortuary", "stateZip", e.target.value)} style={styles.input} />
                  </Field>
                </div>

                <Field label="Comment">
                  <textarea value={formData.financial.comment} onChange={(e) => updateSection("financial", "comment", e.target.value.slice(0, 500))} style={styles.textarea} rows={4} maxLength={500} />
                </Field>
              </Card>

              <Card title="6. Referrals" subtitle="Community referral needs and ancillary services" id="referrals">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Field label="Is there a need for referral to community Program?">
                    <select value={formData.referrals.needCommunityReferral} onChange={(e) => updateSection("referrals", "needCommunityReferral", e.target.value)} style={styles.select}>
                      {selectOptions(YES_NO_NA)}
                    </select>
                  </Field>
                  <Field label="Is community referral accepted?">
                    <select value={formData.referrals.referralAccepted} onChange={(e) => updateSection("referrals", "referralAccepted", e.target.value)} style={styles.select}>
                      {selectOptions(YES_NO_NA)}
                    </select>
                  </Field>
                </div>

                <Field label="Referral types">
                  <CheckboxGrid
                    options={["Therapy", "Music", "Art", "Pet", "Massage", "Volunteer for Companionship", "Errands", "Respite", "Light housekeeping/meals"]}
                    values={formData.referrals.referralTypes}
                    onToggle={(option) => updateSection("referrals", "referralTypes", toggleValue(formData.referrals.referralTypes, option))}
                    columns={3}
                  />
                </Field>

                <Field label="Community support (specify)">
                  <textarea value={formData.referrals.communitySupport} onChange={(e) => updateSection("referrals", "communitySupport", e.target.value)} style={styles.textarea} rows={3} />
                </Field>
                <Field label="Other (specify)">
                  <textarea value={formData.referrals.other} onChange={(e) => updateSection("referrals", "other", e.target.value)} style={styles.textarea} rows={3} />
                </Field>
              </Card>

              <Card title="7. Narrative" subtitle="Care provided and psychosocial visit narrative" id="narrative">
                <Field label="Care provided">
                  <CheckboxGrid
                    options={["Listening/Emotional support", "Knowledge related needs", "Funeral planning", "Other"]}
                    values={formData.narrative.careProvided}
                    onToggle={(option) => updateSection("narrative", "careProvided", toggleValue(formData.narrative.careProvided, option))}
                  />
                </Field>
                {formData.narrative.careProvided.includes("Other") && (
                  <Field label="Care provided — other">
                    <input value={formData.narrative.careProvidedOther} onChange={(e) => updateSection("narrative", "careProvidedOther", e.target.value)} style={styles.input} />
                  </Field>
                )}

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Field label="Narrative paragraph 1">
                    <textarea value={formData.narrative.noteOne} onChange={(e) => updateSection("narrative", "noteOne", e.target.value)} style={styles.textarea} rows={6} />
                  </Field>
                  <Field label="Narrative paragraph 2">
                    <textarea value={formData.narrative.noteTwo} onChange={(e) => updateSection("narrative", "noteTwo", e.target.value)} style={styles.textarea} rows={6} />
                  </Field>
                </div>
              </Card>

              <Card title="Signature" subtitle="Acknowledgement and reviewer display" id="signature">
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Signature of Patient / PCG to acknowledge visit">
                    <select value={formData.signature.patientPcgAcknowledgement} onChange={(e) => updateSection("signature", "patientPcgAcknowledgement", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Signed", "Declined", "Unable to sign"])}
                    </select>
                  </Field>
                  <Field label="Signed by">
                    <input value={formData.signature.signedByName} onChange={(e) => updateSection("signature", "signedByName", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="Credentials / Relation">
                    <input value={formData.signature.signedByCredentials} onChange={(e) => updateSection("signature", "signedByCredentials", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="Date">
                    <input type="date" value={formData.signature.signedDate} onChange={(e) => updateSection("signature", "signedDate", e.target.value)} style={styles.input} />
                  </Field>
                </div>

                <div style={styles.mutedBox}>
                  Signature placeholder: Signed by {formData.signature.signedByName || "________________"} {formData.signature.signedByCredentials ? `(${formData.signature.signedByCredentials})` : ""}{" "}
                  {formData.signature.signedDate ? `on ${formData.signature.signedDate}` : ""}.
                </div>

                <div style={{ ...styles.mutedBox, marginTop: 12 }}>
                  This form has been reviewed by {mswReviewerName}, {mswReviewerCredentials}
                  {formData.signature.reviewerDate ? ` on ${formData.signature.reviewerDate}` : ""}.
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12, marginTop: 12 }}>
                  <Field label="Reviewer name">
                    <input value={formData.signature.reviewerName} onChange={(e) => updateSection("signature", "reviewerName", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="Reviewer credentials">
                    <input value={formData.signature.reviewerCredentials} onChange={(e) => updateSection("signature", "reviewerCredentials", e.target.value)} style={styles.input} placeholder="MSW" />
                  </Field>
                  <Field label="Reviewer date">
                    <input type="date" value={formData.signature.reviewerDate} onChange={(e) => updateSection("signature", "reviewerDate", e.target.value)} style={styles.input} />
                  </Field>
                </div>
              </Card>

              <div style={styles.footer}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                  <span style={styles.statusPill}>Ongoing MSW assessment</span>
                  <span style={{ fontSize: 11, color: "#475569", fontWeight: 700 }}>
                    {visitTypeLabel} · {lastSavedAt ? `Last saved ${lastSavedAt}` : "Unsaved changes"}
                  </span>
                </div>
                <div style={{ display: "flex", gap: 10 }}>
                  <button type="button" style={styles.button} onClick={handleSave}>
                    Save Assessment
                  </button>
                </div>
              </div>

              {saveStatus === "saved" ? <div style={{ marginTop: 10, fontSize: 12, color: "#166534" }}>Comprehensive Psychosocial Assessment saved locally.</div> : null}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
