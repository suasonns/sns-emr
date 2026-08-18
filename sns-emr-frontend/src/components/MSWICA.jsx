import React, { useCallback, useEffect, useMemo, useState } from "react";
import { fetchPatientSummary } from "../api/patientCharts";
import { getActivePatientId } from "../utils/activePatient";
import {
  saveMswIcaAssessment,
  getMswIcaAssessment,
  updateMswIcaAssessment,
  lockMswIcaAssessment,
  getMswIcaIntelligence,
} from "../api/icaAssessments";
import AssessmentTypeToggle from "./AssessmentTypeToggle";
import { useThemeMode } from "../theme/theme";
import { getChartColors } from "../theme/chartColors";

const API_BASE = "/visits/msw-ica";
const STORAGE_PREFIX = "sns-hospice-solutions-msw-ica";

const INITIAL_FORM = {
  pain: {
    uncomfortable: "",
    painLevel: "",
    mentalStatus: "",
    historian: "",
    notes: "",
  },
  psychosocial: {
    maritalStatus: "",
    childrenUnder21: "",
    familyPcgName: "",
    familyPcgRelation: "",
    patientLives: "",
    livingArrangement: "",
    familyCommunication: "",
    familyRelation: "",
    familyResponseToIllness: "",
    socialInteraction: "",
    supportSystem: "",
    supportPersons: [{ name: "", phone: "" }, { name: "", phone: "" }],
    notes: "",
  },
  patientDistress: {
    patientResponse: [],
    patientConcerns: [],
    iadl: {
      phoneAccess: "",
      shopping: "",
      mealPrep: "",
      housework: "",
      finances: "",
    },
    anxietyRating: "",
    distressRating: "",
    notes: "",
  },
  familyDistress: {
    familyResponse: [],
    abilityToProvideCare: "",
    willingnessToProvideCare: "",
    familyCrisis: [],
    pcgAnxietyRating: "",
    notes: "",
  },
  financialLegal: {
    allNeedsMet: "",
    isVeteran: "",
    patientLacks: [],
    needsAssistance: [],
    livingWill: "",
    livingWillCopy: "",
    healthPOA: "",
    healthPOACopy: "",
    healthProxy: "",
    healthProxyCopy: "",
    burialPlans: "",
    mortuaryName: "",
    mortuaryPhone: "",
    mortuaryAddress: "",
    notes: "",
  },
  referrals: {
    communityProgram: "",
    communityAccepted: "",
    therapy: [],
    volunteerServices: [],
    notes: "",
  },
  narrative: {
    careProvided: [],
    notes: "",
  },
  finalization: {
    staff_title: "",
    assessment_complete: false,
    clinician_name: "",
    signature_date: "",
    patient_acknowledgement: false,
    patient_signature_name: "",
    patient_signature_relationship: "",
    patient_signature_date: "",
    countersign_required: false,
    countersign_staff_name: "",
    countersign_staff_title: "",
    countersign_signature_date: "",
  },
};

const sidebarItems = [
  "Admission",
  "Assessment",
  "Psychosocial",
  "Tx / Med / DME",
  "IDG",
  "POC",
  "Issues / Outcome",
  "Physician",
  "Visit Notes",
  "Health Aide (HA)",
  "Volunteer",
  "Comm / Progress Log",
  "Document / Images",
  "Discharge",
  "Bereavement",
  "Compliance",
  "Incident / Occurrence",
  "Faxes",
  "Care Overview",
  "Monthly Schedule",
];

function getBrand(colors) {
  return {
    navy: "#1E3A5F",
    teal: colors.teal,
    tealDark: colors.teal,
    tealLight: colors.tealBg,
    bg: colors.bg,
    canvas: colors.bg,
    panel: colors.card,
    line: colors.border,
    text: colors.text,
    muted: colors.label,
    slate: colors.text,
  };
}

function getStyles(brand) {
  return {
    page: { minHeight: "100vh", background: brand.canvas },
    frame: { maxWidth: 1180, margin: "0 auto", padding: "24px 0" },
    shell: { display: "grid", gridTemplateColumns: "260px 1fr", gap: 12 },
    sidebar: { width: 260, minWidth: 260, paddingTop: 3 },
    patientCard: { border: `1px solid ${brand.line}`, background: brand.panel, fontSize: 11, marginBottom: 12, borderRadius: 12, overflow: "hidden" },
    patientCardHeader: { background: "linear-gradient(90deg, #1E3A5F 0%, #0D9488 100%)", color: "#fff", borderBottom: `1px solid ${brand.navy}`, padding: "6px 10px", fontWeight: 700 },
    navCard: { border: `1px solid ${brand.line}`, background: brand.panel, borderRadius: 12, overflow: "hidden" },
    navHeader: { background: brand.panel, borderBottom: `1px solid ${brand.line}`, padding: "6px 10px", fontWeight: 700, color: brand.text },
    navBody: { padding: 8, maxHeight: 640, overflow: "auto" },
    main: { background: brand.bg, border: `1px solid ${brand.line}`, boxShadow: "0 12px 28px rgba(15, 23, 42, 0.08)", borderRadius: 14, overflow: "hidden" },
    header: { borderBottom: `1px solid ${brand.line}`, padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", background: "linear-gradient(90deg, #1E3A5F 0%, #0D9488 100%)", color: "#fff" },
    headerTitle: { fontSize: 18, fontWeight: 700 },
    headerSub: { fontSize: 11, color: "rgba(255,255,255,0.88)" },
    progress: { fontSize: 11, fontWeight: 700 },
    uploadBar: { padding: 10, background: brand.tealLight, borderBottom: `1px solid ${brand.line}`, fontSize: 11, color: brand.text },
    alert: { margin: 10, padding: 10, border: "1px solid #f59e0b", background: "#fff7ed", color: "#9a3412", fontSize: 12, borderRadius: 10 },
    content: { padding: 24 },
    columns: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 },
    sectionCard: { border: `1px solid ${brand.line}`, marginBottom: 12, background: brand.panel, borderRadius: 12, overflow: "hidden" },
    sectionHeader: { background: brand.panel, borderBottom: `1px solid ${brand.line}`, padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" },
    sectionTitle: { fontSize: 14, fontWeight: 700, fontStyle: "italic", color: brand.text },
    sectionHint: { fontSize: 10, color: brand.muted },
    addIssue: { fontSize: 10, color: brand.tealDark, fontWeight: 700 },
    sectionBody: { padding: 12 },
    fieldLabel: { display: "block", fontSize: 11, fontWeight: 700, marginBottom: 4, color: brand.slate },
    input: { width: "100%", boxSizing: "border-box", padding: "8px 10px", border: `1px solid ${brand.line}`, borderRadius: 10, background: brand.panel, color: brand.text, fontSize: 13 },
    textarea: { width: "100%", boxSizing: "border-box", padding: "8px 10px", border: `1px solid ${brand.line}`, borderRadius: 10, background: brand.panel, color: brand.text, fontSize: 13, lineHeight: 1.3, resize: "vertical" },
    checkboxLabel: { display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11, color: brand.text },
    button: { border: `1px solid ${brand.teal}`, background: brand.panel, color: brand.tealDark, borderRadius: 10, padding: "8px 14px", fontSize: 12, cursor: "pointer", fontWeight: 700 },
    footer: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, paddingTop: 8, flexWrap: "wrap" },
    statusPill: { display: "inline-flex", alignItems: "center", borderRadius: 999, padding: "4px 8px", fontSize: 10, fontWeight: 800, textTransform: "uppercase" },
  };
}

function readStoredForm(patientId) {
  const raw = localStorage.getItem(`${STORAGE_PREFIX}:${patientId}`);
  if (!raw) return INITIAL_FORM;
  try {
    const parsed = JSON.parse(raw);
    return {
      ...INITIAL_FORM,
      ...parsed,
      pain: { ...INITIAL_FORM.pain, ...(parsed.pain || {}) },
      psychosocial: { ...INITIAL_FORM.psychosocial, ...(parsed.psychosocial || {}) },
      patientDistress: {
        ...INITIAL_FORM.patientDistress,
        ...(parsed.patientDistress || {}),
        iadl: { ...INITIAL_FORM.patientDistress.iadl, ...((parsed.patientDistress || {}).iadl || {}) },
      },
      familyDistress: { ...INITIAL_FORM.familyDistress, ...(parsed.familyDistress || {}) },
      financialLegal: { ...INITIAL_FORM.financialLegal, ...(parsed.financialLegal || {}) },
      referrals: { ...INITIAL_FORM.referrals, ...(parsed.referrals || {}) },
      narrative: { ...INITIAL_FORM.narrative, ...(parsed.narrative || {}) },
      finalization: { ...INITIAL_FORM.finalization, ...(parsed.finalization || {}) },
    };
  } catch {
    return INITIAL_FORM;
  }
}

function toggleValue(values, value) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <label style={styles.fieldLabel}>{label}</label>
      {children}
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
        <div style={styles.addIssue}>Add Issue</div>
      </div>
      <div style={styles.sectionBody}>{children}</div>
    </section>
  );
}

// Delegates to the shared client so requests carry the auth token.
const api = {
  saveMSWICAAssessment: (patientId, formData) =>
    saveMswIcaAssessment({ patientId, formData }),
  getMSWICAAssessment: (assessmentId) => getMswIcaAssessment(assessmentId),
  updateMSWICAAssessment: (assessmentId, formData) =>
    updateMswIcaAssessment(assessmentId, formData),
  lockMSWICAAssessment: (assessmentId) => lockMswIcaAssessment(assessmentId),
  getMSWICAIntelligence: (assessmentId) => getMswIcaIntelligence(assessmentId),
};

export default function MSWICA({ patientId = getActivePatientId() ?? "", assessmentId: existingAssessmentId = undefined, mode = "ica" }) {
  const { mode: themeMode } = useThemeMode();
  const colors = useMemo(() => getChartColors(themeMode), [themeMode]);
  const CLINICAL_BRAND = useMemo(() => getBrand(colors), [colors]);
  const styles = useMemo(() => getStyles(CLINICAL_BRAND), [CLINICAL_BRAND]);
  const [patientSummary, setPatientSummary] = useState(null);
  const [patientSummaryError, setPatientSummaryError] = useState("");
  const [formData, setFormData] = useState(() => readStoredForm(patientId));
  const [assessmentId, setAssessmentId] = useState(existingAssessmentId || null);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);
  const [pageError, setPageError] = useState("");
  const [intelligenceError, setIntelligenceError] = useState("");
  const [locked, setLocked] = useState(false);
  const [intelligence, setIntelligence] = useState(null);
  const [intelligenceLoading, setIntelligenceLoading] = useState(false);
  const [activeSection, setActiveSection] = useState("psychosocial");
  const isOngoing = mode === "ongoing";
  const [assessmentType, setAssessmentType] = useState("update");

  useEffect(() => {
    let mounted = true;
    setPatientSummaryError("");
    fetchPatientSummary(patientId)
      .then((summary) => {
        if (mounted) setPatientSummary(summary);
      })
      .catch((error) => {
        console.error("Failed to load MSW ICA patient summary:", error);
        if (mounted) setPatientSummaryError(error instanceof Error ? error.message : "Unable to load patient summary.");
      });
    return () => {
      mounted = false;
    };
  }, [patientId]);

  useEffect(() => {
    setFormData(readStoredForm(patientId));
    setAssessmentId(existingAssessmentId || null);
    setLocked(false);
    setSaveStatus(null);
    setPageError("");
    setIntelligence(null);
    setIntelligenceError("");
  }, [patientId, existingAssessmentId]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_PREFIX}:${patientId}`, JSON.stringify(formData));
  }, [formData, patientId]);

  const refreshIntelligence = useCallback(async (currentAssessmentId = assessmentId) => {
    if (!currentAssessmentId) {
      setIntelligence(null);
      setIntelligenceError("");
      return;
    }
    setIntelligenceLoading(true);
    try {
      const data = await api.getMSWICAIntelligence(currentAssessmentId);
      setIntelligence(data);
      setIntelligenceError("");
    } catch (err) {
      console.error("MSW ICA intelligence load error:", err);
      setIntelligence(null);
      setIntelligenceError(err instanceof Error ? err.message : "Unable to load MSW ICA intelligence.");
    } finally {
      setIntelligenceLoading(false);
    }
  }, [assessmentId]);

  useEffect(() => {
    if (existingAssessmentId) {
      api.getMSWICAAssessment(existingAssessmentId)
        .then((data) => {
          if (data.formData) setFormData(data.formData);
          if (data.locked) setLocked(true);
          const resolvedId = data.assessmentId || existingAssessmentId;
          setAssessmentId(resolvedId);
          return refreshIntelligence(resolvedId);
        })
        .catch((err) => {
          console.error("Failed to load MSW ICA assessment:", err);
          setPageError(err instanceof Error ? err.message : "Unable to load MSW ICA assessment.");
        });
    }
  }, [existingAssessmentId, refreshIntelligence]);

  useEffect(() => {
    if (assessmentId) refreshIntelligence(assessmentId);
  }, [assessmentId, refreshIntelligence]);

  const updateField = useCallback((section, key, value) => {
    setFormData((prev) => ({
      ...prev,
      [section]: key ? { ...prev[section], [key]: value } : value,
    }));
    setSaveStatus(null);
    setPageError("");
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setPageError("");
    try {
      let activeAssessmentId = assessmentId;
      if (activeAssessmentId) {
        await api.updateMSWICAAssessment(activeAssessmentId, formData);
      } else {
        const result = await api.saveMSWICAAssessment(patientId, formData);
        activeAssessmentId = result.assessmentId;
        setAssessmentId(activeAssessmentId);
      }
      await refreshIntelligence(activeAssessmentId);
      setSaveStatus("saved");
    } catch (err) {
      console.error("MSW ICA save error:", err);
      setSaveStatus("error");
      setPageError(err instanceof Error ? err.message : "Unable to save MSW ICA assessment.");
    } finally {
      setSaving(false);
    }
  }, [assessmentId, formData, patientId, refreshIntelligence]);

  const handleLock = useCallback(async () => {
    if (!assessmentId) return;
    setPageError("");
    try {
      await api.lockMSWICAAssessment(assessmentId);
      setLocked(true);
    } catch (err) {
      console.error("MSW ICA lock error:", err);
      setPageError(err instanceof Error ? err.message : "Unable to lock MSW ICA assessment.");
    }
  }, [assessmentId]);

  const sections = [
    { key: "pain", label: "1. Pain" },
    { key: "psychosocial", label: "2. Psychosocial Circumstances" },
    { key: "distress", label: "3. Patient Distress / Concerns" },
    { key: "familyDistress", label: "4. Family Distress / Concerns" },
    { key: "financial", label: "5. Financial / Legal Needs" },
    { key: "referrals", label: "6. Referrals" },
    { key: "narrative", label: "7. Narrative" },
    { key: "signature", label: "Signature" },
  ];

  const patientName = patientSummary?.patient?.full_name || "RNICA Runtime Test Patient";
  const progressLabel = locked ? "COMPLETED" : "IN PROGRESS";
  const progressTone = locked ? "#2563eb" : "#f59e0b";

  const summaryCount = [
    formData.pain.uncomfortable,
    formData.psychosocial.maritalStatus,
    formData.psychosocial.patientLives,
    formData.financialLegal.allNeedsMet,
    formData.referrals.communityProgram,
    formData.finalization.staff_title,
  ].filter(Boolean).length;

  const patientOverview = useMemo(() => {
    if (!patientSummary) {
      return {
        diagnosis: "Hospice qualifying diagnosis",
        painSummary: "Loading patient context...",
        primaryProvider: "Unassigned",
        hnpStatus: "Pre-referral / Routine",
        lastVisit: "No visits recorded",
        disciplineHistory: [],
        careTeam: [],
      };
    }
    return {
      diagnosis: patientSummary.patient.primary_diagnosis,
      painSummary: `${patientSummary.care_team.length} active care team member(s) and ${patientSummary.recent_visits.length} recent visit(s) on file.`,
      primaryProvider: patientSummary.care_team[0]?.staff_name || "Unassigned",
      hnpStatus: `${patientSummary.patient.admission_status} / ${patientSummary.patient.acuity_state}`,
      lastVisit: patientSummary.recent_visits[0]
        ? `${patientSummary.recent_visits[0].visit_type} — ${patientSummary.recent_visits[0].visit_datetime || "—"}`
        : "No visits recorded",
      disciplineHistory: [
        `${patientSummary.communication_summary.total} communication entry(ies)`,
        `${patientSummary.incident_summary.total} incident report(s)`,
        `${patientSummary.care_team.length} active care team assignment(s)`,
      ],
      careTeam: patientSummary.care_team.map((item) => item.discipline),
    };
  }, [patientSummary]);

  const gotoSection = (section) => {
    setActiveSection(section);
    document.getElementById(section)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const selectedConcerns = formData.patientDistress.patientConcerns.length + formData.patientDistress.patientResponse.length;
  const saveButtonLabel = isOngoing || assessmentId ? "Update Assessment / Recert" : "Save Assessment";
  const assessmentChildren = [
    { label: "Nursing", target: "psychosocial" },
    { label: "Spiritual", target: "narrative" },
    { label: "Psychosocial", target: "psychosocial" },
  ];

  return (
    <div style={styles.page}>
      <div style={styles.frame}>
        <div style={styles.shell}>
          <aside style={styles.sidebar}>
            <div style={{ fontSize: 13, color: CLINICAL_BRAND.text, fontWeight: 700, marginBottom: 8, paddingLeft: 2 }}>Love & Faith Hospice Services, Inc.</div>
            <div style={styles.patientCard}>
              <div style={styles.patientCardHeader}>Patient</div>
              <div style={{ padding: 8, color: CLINICAL_BRAND.text }}>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{patientName}</div>
                <div style={{ fontSize: 11, color: CLINICAL_BRAND.muted, marginTop: 4 }}>{patientSummary?.patient?.mrn || "MRN not loaded"}</div>
                <div style={{ fontSize: 11, color: CLINICAL_BRAND.muted, marginTop: 6 }}>DOB: 11/15/1941 (84F)</div>
              </div>
            </div>
            <div style={styles.navCard}>
              <div style={styles.navHeader}>Navigation</div>
              <div style={styles.navBody}>
                {sidebarItems.map((item) => {
                  if (item === "Psychosocial") {
                    return null;
                  }
                  if (item === "Assessment") {
                    return (
                      <div key={item} style={{ marginBottom: 6 }}>
                        <div style={{ fontSize: 10, fontWeight: 800, color: CLINICAL_BRAND.muted, letterSpacing: ".08em", textTransform: "uppercase", padding: "6px 4px 4px" }}>
                          Assessment
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: 4, paddingLeft: 10 }}>
                          {assessmentChildren.map((child) => (
                            <button
                              key={child.label}
                              type="button"
                              onClick={() => gotoSection(child.target)}
                              style={{
                                width: "100%",
                                textAlign: "left",
                                border: "none",
                                background: "transparent",
                                color: CLINICAL_BRAND.text,
                                fontSize: 12,
                                padding: "3px 4px",
                                cursor: "pointer",
                              }}
                            >
                              {child.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    );
                  }

                  return (
                    <button
                      key={item}
                      type="button"
                      onClick={() => gotoSection(item === "Admission" ? "psychosocial" : "narrative")}
                      style={{
                        width: "100%",
                        textAlign: "left",
                        border: "none",
                        background: "transparent",
                        color: CLINICAL_BRAND.text,
                        fontSize: 12,
                        padding: "3px 4px",
                        cursor: "pointer",
                      }}
                    >
                      {item}
                    </button>
                  );
                })}
              </div>
            </div>
          </aside>

          <main style={styles.main}>
            <div style={styles.header}>
              <div>
                <div style={styles.headerTitle}>{isOngoing ? "Comprehensive Psychosocial Assessment" : "MSW Initial Comprehensive Assessment"}</div>
                <div style={styles.headerSub}>Psychosocial support, caregiver burden, resource barriers, and intervention planning</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: progressTone }}>{progressLabel}</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.8)" }}>Close</div>
              </div>
            </div>

            {isOngoing && (
              <div style={{ padding: "12px 24px", background: CLINICAL_BRAND.canvas, borderBottom: `1px solid ${CLINICAL_BRAND.line}`, color: CLINICAL_BRAND.text }}>
                <AssessmentTypeToggle value={assessmentType} onChange={setAssessmentType} />
              </div>
            )}

            <div style={styles.uploadBar}>Upload Documents (0)</div>

            {(patientSummaryError || pageError) && (
              <div style={styles.alert}>
                {patientSummaryError && <div>Patient summary: {patientSummaryError}</div>}
                {pageError && <div>MSW ICA: {pageError}</div>}
              </div>
            )}

            <div style={styles.content}>
              <div style={styles.columns}>
                <div>
                  <Card title="1. Pain" subtitle="Patient response to illness" id="pain">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Are you uncomfortable because of pain?">
                        <select value={formData.pain.uncomfortable} onChange={(e) => updateField("pain", "uncomfortable", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="No">No</option>
                          <option value="Yes">Yes</option>
                        </select>
                      </Field>
                      <Field label="If yes, pain level (0-10)">
                        <input type="number" min="0" max="10" value={formData.pain.painLevel} onChange={(e) => updateField("pain", "painLevel", e.target.value)} style={styles.input} />
                      </Field>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Observed patient mental status">
                        <select value={formData.pain.mentalStatus} onChange={(e) => updateField("pain", "mentalStatus", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Awake">Awake</option>
                          <option value="Confused">Confused</option>
                          <option value="Withdrawn">Withdrawn</option>
                          <option value="Overwhelmed">Overwhelmed</option>
                          <option value="Lethargic">Lethargic</option>
                          <option value="Comatose">Comatose</option>
                        </select>
                      </Field>
                      <Field label="Historian / primary support">
                        <select value={formData.pain.historian} onChange={(e) => updateField("pain", "historian", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="PCG">PCG</option>
                          <option value="Patient">Patient</option>
                          <option value="Family">Family</option>
                          <option value="Other">Other</option>
                        </select>
                      </Field>
                    </div>
                    <Field label="Narrative">
                      <textarea
                        value={formData.pain.notes}
                        onChange={(e) => updateField("pain", "notes", e.target.value)}
                        style={styles.textarea}
                        placeholder="Social worker narrative and support context."
                      />
                    </Field>
                  </Card>

                  <Card title="2. Psychosocial Circumstances" subtitle="Family, living arrangement, and support systems" id="psychosocial">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Marital status">
                        <select value={formData.psychosocial.maritalStatus} onChange={(e) => updateField("psychosocial", "maritalStatus", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Single">Single</option>
                          <option value="Married">Married</option>
                          <option value="Widowed">Widowed</option>
                          <option value="Divorced">Divorced</option>
                          <option value="Separated">Separated</option>
                        </select>
                      </Field>
                      <Field label="# Children under 21">
                        <input value={formData.psychosocial.childrenUnder21} onChange={(e) => updateField("psychosocial", "childrenUnder21", e.target.value)} style={styles.input} />
                      </Field>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Family / PCG name">
                        <input value={formData.psychosocial.familyPcgName} onChange={(e) => updateField("psychosocial", "familyPcgName", e.target.value)} style={styles.input} />
                      </Field>
                      <Field label="Relation">
                        <input value={formData.psychosocial.familyPcgRelation} onChange={(e) => updateField("psychosocial", "familyPcgRelation", e.target.value)} style={styles.input} />
                      </Field>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Patient lives">
                        <select value={formData.psychosocial.patientLives} onChange={(e) => updateField("psychosocial", "patientLives", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Alone">Alone</option>
                          <option value="With Family">With Family</option>
                          <option value="in ALF">in ALF</option>
                          <option value="in SNF">in SNF</option>
                          <option value="Group Home">Group Home</option>
                          <option value="Other">Other</option>
                        </select>
                      </Field>
                      <Field label="Living arrangement">
                        <select value={formData.psychosocial.livingArrangement} onChange={(e) => updateField("psychosocial", "livingArrangement", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Satisfactory">Satisfactory</option>
                          <option value="Unsatisfactory">Unsatisfactory</option>
                          <option value="Other">Other</option>
                        </select>
                      </Field>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Family communication">
                        <select value={formData.psychosocial.familyCommunication} onChange={(e) => updateField("psychosocial", "familyCommunication", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Good">Good</option>
                          <option value="Fair">Fair</option>
                          <option value="Poor">Poor</option>
                          <option value="Limited">Limited</option>
                        </select>
                      </Field>
                      <Field label="Family relation">
                        <select value={formData.psychosocial.familyRelation} onChange={(e) => updateField("psychosocial", "familyRelation", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Good">Good</option>
                          <option value="Fair">Fair</option>
                          <option value="Poor">Poor</option>
                          <option value="Strained">Strained</option>
                        </select>
                      </Field>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Family response to illness">
                        <select value={formData.psychosocial.familyResponseToIllness} onChange={(e) => updateField("psychosocial", "familyResponseToIllness", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Supportive">Supportive</option>
                          <option value="Accepting">Accepting</option>
                          <option value="Denial">Denial</option>
                          <option value="Overwhelmed">Overwhelmed</option>
                          <option value="Other">Other</option>
                        </select>
                      </Field>
                      <Field label="Social interaction">
                        <select value={formData.psychosocial.socialInteraction} onChange={(e) => updateField("psychosocial", "socialInteraction", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Satisfactory">Satisfactory</option>
                          <option value="Limited">Limited</option>
                          <option value="Isolated">Isolated</option>
                          <option value="Other">Other</option>
                        </select>
                      </Field>
                    </div>
                    <Field label="Support system">
                      <select value={formData.psychosocial.supportSystem} onChange={(e) => updateField("psychosocial", "supportSystem", e.target.value)} style={styles.input}>
                        <option value="">Select</option>
                        <option value="Family">Family</option>
                        <option value="Friends">Friends</option>
                        <option value="Community">Community</option>
                        <option value="Church">Church</option>
                        <option value="None">None</option>
                        <option value="Other">Other</option>
                      </select>
                    </Field>
                    <div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.muted, marginBottom: 6 }}>Other support persons</div>
                    {formData.psychosocial.supportPersons.map((sp, i) => (
                      <div key={i} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 6 }}>
                        <input
                          placeholder="Name"
                          value={sp.name}
                          onChange={(e) => {
                            const arr = [...formData.psychosocial.supportPersons];
                            arr[i] = { ...arr[i], name: e.target.value };
                            updateField("psychosocial", "supportPersons", arr);
                          }}
                          style={styles.input}
                        />
                        <input
                          placeholder="Phone"
                          value={sp.phone}
                          onChange={(e) => {
                            const arr = [...formData.psychosocial.supportPersons];
                            arr[i] = { ...arr[i], phone: e.target.value };
                            updateField("psychosocial", "supportPersons", arr);
                          }}
                          style={styles.input}
                        />
                      </div>
                    ))}
                    <Field label="Narrative">
                      <textarea value={formData.psychosocial.notes} onChange={(e) => updateField("psychosocial", "notes", e.target.value)} style={styles.textarea} placeholder="Living arrangement, caregiver context, and support notes..." />
                    </Field>
                  </Card>

                  <Card title="3. Patient — Psychosocial Distress/Concerns" subtitle="Select all that apply" id="distress">
                    <div style={{ marginBottom: 12 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.muted, marginBottom: 6 }}>Patient response to illness</div>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 6 }}>
                        {["Cannot respond", "Overwhelmed", "Fearful", "Unaware of condition", "Accepting", "Depressed", "Sad", "Guilt", "Denial", "Angry", "Loss of worth", "Other"].map((option) => (
                          <label key={option} style={styles.checkboxLabel}>
                            <input
                              type="checkbox"
                              checked={formData.patientDistress.patientResponse.includes(option)}
                              onChange={() => updateField("patientDistress", "patientResponse", toggleValue(formData.patientDistress.patientResponse, option))}
                            />
                            {option}
                          </label>
                        ))}
                      </div>
                    </div>
                    <div style={{ marginBottom: 12 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.muted, marginBottom: 6 }}>Patient concerns</div>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 6 }}>
                        {["Responsibility for others", "Finances", "Lacks cognitive ability", "Suicide risks", "Inadequate food/supplies", "Abuse/neglect", "Substance/alcohol abuse", "Transfer to another setting", "Other"].map((option) => (
                          <label key={option} style={styles.checkboxLabel}>
                            <input
                              type="checkbox"
                              checked={formData.patientDistress.patientConcerns.includes(option)}
                              onChange={() => updateField("patientDistress", "patientConcerns", toggleValue(formData.patientDistress.patientConcerns, option))}
                            />
                            {option}
                          </label>
                        ))}
                      </div>
                    </div>
                    <div style={{ background: CLINICAL_BRAND.canvas, border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 10, padding: 10, marginBottom: 12, color: CLINICAL_BRAND.text }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.tealDark, textTransform: "uppercase", marginBottom: 8 }}>Instrumental Activities of Daily Living (IADL)</div>
                      {[
                        { q: "Phone access & able to make calls?", key: "phoneAccess" },
                        { q: "Goes out for shopping?", key: "shopping" },
                        { q: "Prepares own meals?", key: "mealPrep" },
                        { q: "Does housework?", key: "housework" },
                        { q: "Manages own finances?", key: "finances" },
                      ].map((item) => (
                        <div key={item.key} style={{ display: "grid", gridTemplateColumns: "1fr 110px", gap: 8, marginBottom: 6, alignItems: "center" }}>
                          <span style={{ fontSize: 12 }}>{item.q}</span>
                          <select
                            value={formData.patientDistress.iadl[item.key]}
                            onChange={(e) =>
                              updateField("patientDistress", "iadl", { ...formData.patientDistress.iadl, [item.key]: e.target.value })
                            }
                            style={{ ...styles.input, padding: "4px 8px", fontSize: 12 }}
                          >
                            <option value="">—</option>
                            <option value="Yes">Yes</option>
                            <option value="No">No</option>
                          </select>
                        </div>
                      ))}
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Patient anxiety rating">
                        <select value={formData.patientDistress.anxietyRating} onChange={(e) => updateField("patientDistress", "anxietyRating", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="None">None</option>
                          <option value="Mild">Mild</option>
                          <option value="Moderate">Moderate</option>
                          <option value="Severe">Severe</option>
                        </select>
                      </Field>
                      <Field label="Distress rating">
                        <select value={formData.patientDistress.distressRating} onChange={(e) => updateField("patientDistress", "distressRating", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="None">None</option>
                          <option value="Mild">Mild</option>
                          <option value="Moderate">Moderate</option>
                          <option value="Severe">Severe</option>
                        </select>
                      </Field>
                    </div>
                    <Field label="Narrative">
                      <textarea value={formData.patientDistress.notes} onChange={(e) => updateField("patientDistress", "notes", e.target.value)} style={styles.textarea} placeholder="Patient distress observations..." />
                    </Field>
                  </Card>
                </div>

                <div>
                  <Card title="4. Family — Psychosocial Distress/Concerns" subtitle="Family response, crisis, and anxiety" id="familyDistress">
                    <div style={{ marginBottom: 12 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.muted, marginBottom: 6 }}>Family response to illness</div>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 6 }}>
                        {["Accepting", "Depressed", "Sad", "Guilt", "Denial", "Angry", "Fearful", "Despair", "Overwhelmed", "Anticipatory grieving", "Other"].map((option) => (
                          <label key={option} style={styles.checkboxLabel}>
                            <input
                              type="checkbox"
                              checked={formData.familyDistress.familyResponse.includes(option)}
                              onChange={() => updateField("familyDistress", "familyResponse", toggleValue(formData.familyDistress.familyResponse, option))}
                            />
                            {option}
                          </label>
                        ))}
                      </div>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Ability to provide care">
                        <select value={formData.familyDistress.abilityToProvideCare} onChange={(e) => updateField("familyDistress", "abilityToProvideCare", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Good">Good</option>
                          <option value="Fair">Fair</option>
                          <option value="Poor">Poor</option>
                          <option value="Unable">Unable</option>
                        </select>
                      </Field>
                      <Field label="Willingness to provide care">
                        <select value={formData.familyDistress.willingnessToProvideCare} onChange={(e) => updateField("familyDistress", "willingnessToProvideCare", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Good">Good</option>
                          <option value="Fair">Fair</option>
                          <option value="Poor">Poor</option>
                          <option value="Unwilling">Unwilling</option>
                        </select>
                      </Field>
                    </div>
                    <div style={{ marginBottom: 12 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.muted, marginBottom: 6 }}>Family crisis</div>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 6 }}>
                        {["None", "Suicide risks", "Inadequate food/supplies", "Financial/legal crisis", "Significant losses in recent past", "Substance/alcohol abuse", "Other"].map((option) => (
                          <label key={option} style={styles.checkboxLabel}>
                            <input
                              type="checkbox"
                              checked={formData.familyDistress.familyCrisis.includes(option)}
                              onChange={() => updateField("familyDistress", "familyCrisis", toggleValue(formData.familyDistress.familyCrisis, option))}
                            />
                            {option}
                          </label>
                        ))}
                      </div>
                    </div>
                    <Field label="PCG / family anxiety rating">
                      <select value={formData.familyDistress.pcgAnxietyRating} onChange={(e) => updateField("familyDistress", "pcgAnxietyRating", e.target.value)} style={styles.input}>
                        <option value="">Select</option>
                        <option value="None">None</option>
                        <option value="Mild">Mild</option>
                        <option value="Moderate">Moderate</option>
                        <option value="Severe">Severe</option>
                      </select>
                    </Field>
                    <Field label="Narrative">
                      <textarea value={formData.familyDistress.notes} onChange={(e) => updateField("familyDistress", "notes", e.target.value)} style={styles.textarea} placeholder="Family's response to patient's decline..." />
                    </Field>
                  </Card>

                  <Card title="5. Financial / Legal Needs" subtitle="Financial strain, advance directives, and mortuary" id="financial">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="All needs met by patient/family?">
                        <select value={formData.financialLegal.allNeedsMet} onChange={(e) => updateField("financialLegal", "allNeedsMet", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Yes">Yes</option>
                          <option value="No">No</option>
                        </select>
                      </Field>
                      <Field label="Is patient/spouse a veteran?">
                        <select value={formData.financialLegal.isVeteran} onChange={(e) => updateField("financialLegal", "isVeteran", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="No">No</option>
                          <option value="Yes">Yes</option>
                        </select>
                      </Field>
                    </div>
                    {formData.financialLegal.allNeedsMet === "No" && (
                      <>
                        <Field label="Patient lacks">
                          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 6 }}>
                            {["Food", "Utility", "Clothing", "Furniture", "Med/supplies unrelated to illness"].map((option) => (
                              <label key={option} style={styles.checkboxLabel}>
                                <input
                                  type="checkbox"
                                  checked={formData.financialLegal.patientLacks.includes(option)}
                                  onChange={() => updateField("financialLegal", "patientLacks", toggleValue(formData.financialLegal.patientLacks, option))}
                                />
                                {option}
                              </label>
                            ))}
                          </div>
                        </Field>
                        <Field label="Needs assistance with">
                          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 6 }}>
                            {["Meals on wheels", "Food stamps", "Other"].map((option) => (
                              <label key={option} style={styles.checkboxLabel}>
                                <input
                                  type="checkbox"
                                  checked={formData.financialLegal.needsAssistance.includes(option)}
                                  onChange={() => updateField("financialLegal", "needsAssistance", toggleValue(formData.financialLegal.needsAssistance, option))}
                                />
                                {option}
                              </label>
                            ))}
                          </div>
                        </Field>
                      </>
                    )}
                    <div style={{ background: CLINICAL_BRAND.canvas, border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 10, padding: 10, marginBottom: 12, color: CLINICAL_BRAND.text }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.tealDark, textTransform: "uppercase", marginBottom: 8 }}>Planning / Advance Directives</div>
                      {[
                        { label: "Living Will", key: "livingWill", copyKey: "livingWillCopy" },
                        { label: "Health POA", key: "healthPOA", copyKey: "healthPOACopy" },
                        { label: "Health Proxy", key: "healthProxy", copyKey: "healthProxyCopy" },
                      ].map((item) => (
                        <div key={item.key} style={{ display: "grid", gridTemplateColumns: "1fr 90px 110px", gap: 8, marginBottom: 6, alignItems: "center" }}>
                          <span style={{ fontSize: 12 }}>{item.label}</span>
                          <select value={formData.financialLegal[item.key]} onChange={(e) => updateField("financialLegal", item.key, e.target.value)} style={{ ...styles.input, padding: "4px 6px", fontSize: 11 }}>
                            <option value="">—</option>
                            <option value="Yes">Yes</option>
                            <option value="No">No</option>
                            <option value="N/A">N/A</option>
                          </select>
                          <select value={formData.financialLegal[item.copyKey]} onChange={(e) => updateField("financialLegal", item.copyKey, e.target.value)} style={{ ...styles.input, padding: "4px 6px", fontSize: 10 }}>
                            <option value="">Copy: —</option>
                            <option value="Yes">Copy: Yes</option>
                            <option value="No">Copy: No</option>
                            <option value="N/A">Copy: N/A</option>
                          </select>
                        </div>
                      ))}
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 90px", gap: 8, alignItems: "center" }}>
                        <span style={{ fontSize: 12 }}>Burial plans</span>
                        <select value={formData.financialLegal.burialPlans} onChange={(e) => updateField("financialLegal", "burialPlans", e.target.value)} style={{ ...styles.input, padding: "4px 6px", fontSize: 11 }}>
                          <option value="">—</option>
                          <option value="Yes">Yes</option>
                          <option value="No">No</option>
                          <option value="N/A">N/A</option>
                        </select>
                      </div>
                    </div>
                    <div style={{ background: CLINICAL_BRAND.canvas, border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 10, padding: 10, marginBottom: 12, color: CLINICAL_BRAND.text }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.tealDark, textTransform: "uppercase", marginBottom: 8 }}>Mortuary information</div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                        <Field label="Mortuary name">
                          <input value={formData.financialLegal.mortuaryName} onChange={(e) => updateField("financialLegal", "mortuaryName", e.target.value)} style={styles.input} />
                        </Field>
                        <Field label="Phone">
                          <input value={formData.financialLegal.mortuaryPhone} onChange={(e) => updateField("financialLegal", "mortuaryPhone", e.target.value)} style={styles.input} />
                        </Field>
                      </div>
                      <Field label="Address">
                        <input value={formData.financialLegal.mortuaryAddress} onChange={(e) => updateField("financialLegal", "mortuaryAddress", e.target.value)} style={styles.input} />
                      </Field>
                    </div>
                    <Field label="Narrative">
                      <textarea value={formData.financialLegal.notes} onChange={(e) => updateField("financialLegal", "notes", e.target.value)} style={styles.textarea} placeholder="Financial/legal planning notes..." />
                    </Field>
                  </Card>

                  <Card title="6. Referrals" subtitle="Community programs and support services" id="referrals">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Need for community program referral?">
                        <select value={formData.referrals.communityProgram} onChange={(e) => updateField("referrals", "communityProgram", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="N/A">N/A</option>
                          <option value="Yes">Yes</option>
                          <option value="No">No</option>
                        </select>
                      </Field>
                      <Field label="Community referral accepted?">
                        <select value={formData.referrals.communityAccepted} onChange={(e) => updateField("referrals", "communityAccepted", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="N/A">N/A</option>
                          <option value="Yes">Yes</option>
                          <option value="No">No</option>
                        </select>
                      </Field>
                    </div>
                    <Field label="Therapy">
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 6 }}>
                        {["Music", "Art", "Pet", "Massage"].map((option) => (
                          <label key={option} style={styles.checkboxLabel}>
                            <input
                              type="checkbox"
                              checked={formData.referrals.therapy.includes(option)}
                              onChange={() => updateField("referrals", "therapy", toggleValue(formData.referrals.therapy, option))}
                            />
                            {option}
                          </label>
                        ))}
                      </div>
                    </Field>
                    <Field label="Volunteer services">
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 6 }}>
                        {["Companionship", "Errands", "Respite", "Light housekeeping/meals"].map((option) => (
                          <label key={option} style={styles.checkboxLabel}>
                            <input
                              type="checkbox"
                              checked={formData.referrals.volunteerServices.includes(option)}
                              onChange={() => updateField("referrals", "volunteerServices", toggleValue(formData.referrals.volunteerServices, option))}
                            />
                            {option}
                          </label>
                        ))}
                      </div>
                    </Field>
                  </Card>

                  <Card title="7. Narrative (Include care provided items)" subtitle="Visit summary and interventions" id="narrative">
                    <Field label="Care provided">
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 6 }}>
                        {["Listening/Emotional support", "Knowledge related needs", "Funeral planning", "Motivational interviewing", "Cognitive behavioral therapy", "Positive reinforcement", "Other"].map((option) => (
                          <label key={option} style={styles.checkboxLabel}>
                            <input
                              type="checkbox"
                              checked={formData.narrative.careProvided.includes(option)}
                              onChange={() => updateField("narrative", "careProvided", toggleValue(formData.narrative.careProvided, option))}
                            />
                            {option}
                          </label>
                        ))}
                      </div>
                    </Field>
                    <Field label="Narrative">
                      <textarea
                        value={formData.narrative.notes}
                        onChange={(e) => updateField("narrative", "notes", e.target.value)}
                        style={{ ...styles.textarea, minHeight: 140 }}
                        placeholder="Visit summary and interventions..."
                      />
                    </Field>
                  </Card>

                  <Card title="8. Signature" subtitle="Complete and sign" id="signature">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Staff title">
                        <input value={formData.finalization.staff_title} onChange={(e) => updateField("finalization", "staff_title", e.target.value)} style={styles.input} />
                      </Field>
                      <Field label="Clinician name">
                        <input value={formData.finalization.clinician_name} onChange={(e) => updateField("finalization", "clinician_name", e.target.value)} style={styles.input} />
                      </Field>
                    </div>
                    <Field label="Signature date">
                      <input type="date" value={formData.finalization.signature_date} onChange={(e) => updateField("finalization", "signature_date", e.target.value)} style={styles.input} />
                    </Field>
                    <div style={{ background: CLINICAL_BRAND.canvas, border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 10, padding: 10, margin: "10px 0", color: CLINICAL_BRAND.text }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.tealDark, textTransform: "uppercase", marginBottom: 8 }}>PCG / Patient acknowledgement</div>
                      <label style={styles.checkboxLabel}>
                        <input
                          type="checkbox"
                          checked={formData.finalization.patient_acknowledgement}
                          onChange={(e) => updateField("finalization", "patient_acknowledgement", e.target.checked)}
                        />
                        Signature of patient / PCG to acknowledge visit
                      </label>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 8 }}>
                        <Field label="Name">
                          <input value={formData.finalization.patient_signature_name} onChange={(e) => updateField("finalization", "patient_signature_name", e.target.value)} style={styles.input} />
                        </Field>
                        <Field label="Relationship">
                          <input value={formData.finalization.patient_signature_relationship} onChange={(e) => updateField("finalization", "patient_signature_relationship", e.target.value)} style={styles.input} />
                        </Field>
                      </div>
                    </div>
                    <div style={{ background: CLINICAL_BRAND.canvas, border: `1px solid ${CLINICAL_BRAND.line}`, borderRadius: 10, padding: 10, marginBottom: 8, color: CLINICAL_BRAND.text }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.tealDark, textTransform: "uppercase", marginBottom: 8 }}>QA review</div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                        <Field label="Reviewed by">
                          <input value={formData.finalization.countersign_staff_name} onChange={(e) => updateField("finalization", "countersign_staff_name", e.target.value)} style={styles.input} placeholder="MSW Supervisor" />
                        </Field>
                        <Field label="Review date">
                          <input type="date" value={formData.finalization.countersign_signature_date} onChange={(e) => updateField("finalization", "countersign_signature_date", e.target.value)} style={styles.input} />
                        </Field>
                      </div>
                      <label style={{ ...styles.checkboxLabel, marginTop: 8 }}>
                        <input
                          type="checkbox"
                          checked={formData.finalization.countersign_required}
                          onChange={(e) => updateField("finalization", "countersign_required", e.target.checked)}
                        />
                        QA review approved
                      </label>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap", marginTop: 6 }}>
                      <label style={styles.checkboxLabel}>
                        <input
                          type="checkbox"
                          checked={formData.finalization.assessment_complete}
                          onChange={(e) => updateField("finalization", "assessment_complete", e.target.checked)}
                        />
                        Assessment complete
                      </label>
                      <button type="button" onClick={handleLock} style={styles.button} disabled={!assessmentId || locked}>
                        {locked ? "Locked" : "Lock Assessment"}
                      </button>
                    </div>
                  </Card>

                  <Card title="MSW ICA Intelligence" subtitle="Evaluating social-risk signals">
                    {intelligenceLoading && <div style={{ fontSize: 12, color: CLINICAL_BRAND.muted }}>Evaluating social-risk signals...</div>}
                    {intelligenceError && <div style={{ ...styles.alert, margin: 0 }}>{intelligenceError}</div>}
                    {!intelligenceLoading && intelligence && (
                      <div style={{ fontSize: 12, lineHeight: 1.6 }}>
                        <div style={{ marginBottom: 8, fontWeight: 700, textTransform: "uppercase" }}>Priority: {intelligence.summary?.overall_priority || "low"}</div>
                        <div style={{ marginBottom: 8 }}>Risk flags: {Array.isArray(intelligence.summary?.risk_flags) ? intelligence.summary.risk_flags.join(", ") : "—"}</div>
                        <div style={{ marginBottom: 8 }}>Recommended actions:</div>
                        <ul style={{ margin: 0, paddingLeft: 18 }}>
                          {(intelligence.recommendations || []).map((rec, idx) => (
                            <li key={`${rec.title || "rec"}-${idx}`}>{rec.title || rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {!intelligenceLoading && !intelligence && <div style={{ fontSize: 12, color: CLINICAL_BRAND.muted }}>No intelligence available yet.</div>}
                  </Card>

                  <div style={styles.footer}>
                    <div style={{ fontSize: 11, color: CLINICAL_BRAND.muted, fontWeight: 700 }}>
                      {locked ? "LOCKED" : "IN PROGRESS"} · {summaryCount} completed field(s)
                    </div>
                    <div style={{ display: "flex", gap: 10 }}>
                      <button type="button" style={styles.button} onClick={handleSave} disabled={saving || locked}>
                        {saving ? "Saving..." : saveButtonLabel}
                      </button>
                      {assessmentId && !locked ? (
                        <button type="button" style={{ ...styles.button, background: "#fee2e2" }} onClick={handleLock}>
                          Lock Assessment
                        </button>
                      ) : null}
                    </div>
                  </div>

                  {saveStatus === "saved" && <div style={{ marginTop: 10, fontSize: 12, color: "#166534" }}>MSW ICA saved successfully.</div>}
                  {saveStatus === "error" && <div style={{ marginTop: 10, fontSize: 12, color: "#92400e" }}>MSW ICA save failed — please try again.</div>}
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
