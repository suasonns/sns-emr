import React, { useCallback, useEffect, useMemo, useState } from "react";
import { fetchPatientSummary } from "../api/patientCharts";

const API_BASE = "/visits/msw-ica";
const DEFAULT_PATIENT_ID = "5d31a53f-eebd-468f-bcb6-1b43771fe113";
const STORAGE_PREFIX = "sns-emr-msw-ica";

const INITIAL_FORM = {
  social: {
    support_level: "",
    support_person: "",
    relationship: "",
    concerns: [],
    coping_mechanisms: "",
    notes: "",
  },
  caregiver: {
    burden_level: "",
    caregiver_name: "",
    caregiver_concerns: [],
    transportation_barrier: "",
    respite_needs: "",
    notes: "",
  },
  risk: {
    financial_stress: "",
    housing_insecurity: "",
    social_isolation: "",
    anger_or_conflict: "",
    safety_concerns: "",
    mental_health_crisis: "",
    transportation_barrier: "",
    patient_psychosocial_concerns: [],
    family_psychosocial_concerns: [],
    financial_legal_needs: [],
    financial_legal_notes: "",
    notes: "",
  },
  interventions: {
    referral_needed: false,
    referral_type: "",
    priority_level: "",
    intervention_plan: "",
    follow_up_date: "",
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

const styles = {
  page: { minHeight: "100vh", background: "#eef3f8" },
  frame: { maxWidth: 1180, margin: "0 auto", padding: "24px 0" },
  shell: { display: "grid", gridTemplateColumns: "260px 1fr", gap: 12 },
  sidebar: { width: 260, minWidth: 260, paddingTop: 3 },
  patientCard: { border: "1px solid #dbe5ee", background: "#fff", fontSize: 11, marginBottom: 12, borderRadius: 12, overflow: "hidden" },
  patientCardHeader: { background: "linear-gradient(90deg, #1f4a78 0%, #10b7a2 100%)", color: "#fff", borderBottom: "1px solid #1f4a78", padding: "6px 10px", fontWeight: 700 },
  navCard: { border: "1px solid #dbe5ee", background: "#fff", borderRadius: 12, overflow: "hidden" },
  navHeader: { background: "#eef6fb", borderBottom: "1px solid #dbe5ee", padding: "6px 10px", fontWeight: 700 },
  navBody: { padding: 8, maxHeight: 640, overflow: "auto" },
  main: { background: "#f4f7f9", border: "1px solid #dbe5ee", boxShadow: "0 12px 28px rgba(15, 23, 42, 0.08)", borderRadius: 14, overflow: "hidden" },
  header: { borderBottom: "1px solid #dbe5ee", padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", background: "linear-gradient(90deg, #1f4a78 0%, #10b7a2 100%)", color: "#fff" },
  headerTitle: { fontSize: 18, fontWeight: 700 },
  headerSub: { fontSize: 11, color: "rgba(255,255,255,0.88)" },
  progress: { fontSize: 11, fontWeight: 700 },
  uploadBar: { padding: 10, background: "#effaf8", borderBottom: "1px solid #dbe5ee", fontSize: 11 },
  alert: { margin: 10, padding: 10, border: "1px solid #f59e0b", background: "#fff7ed", color: "#9a3412", fontSize: 12, borderRadius: 10 },
  content: { padding: 24 },
  columns: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 },
  sectionCard: { border: "1px solid #dbe5ee", marginBottom: 12, background: "#fff", borderRadius: 12, overflow: "hidden" },
  sectionHeader: { background: "#f8fafc", borderBottom: "1px solid #dbe5ee", padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" },
  sectionTitle: { fontSize: 14, fontWeight: 700, fontStyle: "italic" },
  sectionHint: { fontSize: 10, color: "#64748b" },
  addIssue: { fontSize: 10, color: "#0f766e", fontWeight: 700 },
  sectionBody: { padding: 12 },
  fieldLabel: { display: "block", fontSize: 11, fontWeight: 700, marginBottom: 4, color: "#334155" },
  input: { width: "100%", boxSizing: "border-box", padding: "8px 10px", border: "1px solid #c8d5df", borderRadius: 10, background: "#fff", fontSize: 13 },
  textarea: { width: "100%", boxSizing: "border-box", padding: "8px 10px", border: "1px solid #c8d5df", borderRadius: 10, fontSize: 13, lineHeight: 1.3, resize: "vertical" },
  checkboxLabel: { display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11, color: "#111827" },
  button: { border: "1px solid #10b7a2", background: "#fff", color: "#0f766e", borderRadius: 10, padding: "8px 14px", fontSize: 12, cursor: "pointer", fontWeight: 700 },
  footer: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, paddingTop: 8, flexWrap: "wrap" },
  statusPill: { display: "inline-flex", alignItems: "center", borderRadius: 999, padding: "4px 8px", fontSize: 10, fontWeight: 800, textTransform: "uppercase" },
};

function readStoredForm(patientId) {
  const raw = localStorage.getItem(`${STORAGE_PREFIX}:${patientId}`);
  if (!raw) return INITIAL_FORM;
  try {
    const parsed = JSON.parse(raw);
    return {
      ...INITIAL_FORM,
      ...parsed,
      social: { ...INITIAL_FORM.social, ...(parsed.social || {}) },
      caregiver: { ...INITIAL_FORM.caregiver, ...(parsed.caregiver || {}) },
      risk: { ...INITIAL_FORM.risk, ...(parsed.risk || {}) },
      interventions: { ...INITIAL_FORM.interventions, ...(parsed.interventions || {}) },
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

const api = {
  async saveMSWICAAssessment(patientId, formData) {
    const res = await fetch(`${API_BASE}/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ patientId, formData }),
    });
    if (!res.ok) throw new Error(`MSW ICA save failed: ${res.status}`);
    return res.json();
  },
  async getMSWICAAssessment(assessmentId) {
    const res = await fetch(`${API_BASE}/${assessmentId}`);
    if (!res.ok) throw new Error(`MSW ICA get failed: ${res.status}`);
    return res.json();
  },
  async updateMSWICAAssessment(assessmentId, formData) {
    const res = await fetch(`${API_BASE}/${assessmentId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ formData }),
    });
    if (!res.ok) throw new Error(`MSW ICA update failed: ${res.status}`);
    return res.json();
  },
  async lockMSWICAAssessment(assessmentId) {
    const res = await fetch(`${API_BASE}/${assessmentId}/lock`, { method: "POST" });
    if (!res.ok) throw new Error(`MSW ICA lock failed: ${res.status}`);
    return res.json();
  },
  async getMSWICAIntelligence(assessmentId) {
    const res = await fetch(`${API_BASE}/${assessmentId}/intelligence`, { method: "GET" });
    if (!res.ok) throw new Error(`MSW ICA intelligence failed: ${res.status}`);
    return res.json();
  },
};

export default function MSWICA({ patientId = DEFAULT_PATIENT_ID, assessmentId: existingAssessmentId = undefined }) {
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
    { key: "psychosocial", label: "1. Psychosocial Circumstances" },
    { key: "caregiver", label: "2. Caregiver Burden / Resources" },
    { key: "distress", label: "3. Patient Distress / Concerns" },
    { key: "financial", label: "4. Financial / Legal Needs" },
    { key: "referrals", label: "5. Referrals" },
    { key: "narrative", label: "6. Narrative" },
    { key: "signature", label: "Signature" },
  ];

  const patientName = patientSummary?.patient?.full_name || "RNICA Runtime Test Patient";
  const progressLabel = locked ? "COMPLETED" : "IN PROGRESS";
  const progressTone = locked ? "#2563eb" : "#f59e0b";

  const summaryCount = [
    formData.social.support_level,
    formData.social.support_person,
    formData.caregiver.burden_level,
    formData.risk.financial_stress,
    formData.interventions.referral_type,
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

  const selectedConcerns = formData.risk.patient_psychosocial_concerns.length + formData.social.concerns.length;
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
            <div style={{ fontSize: 13, color: "#0f172a", fontWeight: 700, marginBottom: 8, paddingLeft: 2 }}>Love & Faith Hospice Services, Inc.</div>
            <div style={styles.patientCard}>
              <div style={styles.patientCardHeader}>Patient</div>
              <div style={{ padding: 8 }}>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{patientName}</div>
                <div style={{ fontSize: 11, color: "#475569", marginTop: 4 }}>{patientSummary?.patient?.mrn || "MRN not loaded"}</div>
                <div style={{ fontSize: 11, color: "#475569", marginTop: 6 }}>DOB: 11/15/1941 (84F)</div>
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
                        <div style={{ fontSize: 10, fontWeight: 800, color: "#64748b", letterSpacing: ".08em", textTransform: "uppercase", padding: "6px 4px 4px" }}>
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
                                color: "#0f172a",
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
                        color: "#0f172a",
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
                <div style={styles.headerTitle}>Comprehensive Psychosocial Assessment</div>
                <div style={styles.headerSub}>Psychosocial support, caregiver burden, resource barriers, and intervention planning</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: progressTone }}>{progressLabel}</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.8)" }}>Close</div>
              </div>
            </div>

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
                  <Card title="1. Pain" subtitle="Patient response to illness" id="psychosocial">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Observed patient mental status">
                        <select value={formData.social.support_level} onChange={(e) => updateField("social", "support_level", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Aware">Aware</option>
                          <option value="Confused">Confused</option>
                          <option value="Withdrawn">Withdrawn</option>
                          <option value="Overwhelmed">Overwhelmed</option>
                        </select>
                      </Field>
                      <Field label="Historian / primary support">
                        <input value={formData.social.support_person} onChange={(e) => updateField("social", "support_person", e.target.value)} style={styles.input} />
                      </Field>
                    </div>
                    <Field label="Family communication">
                      <select value={formData.social.relationship} onChange={(e) => updateField("social", "relationship", e.target.value)} style={styles.input}>
                        <option value="">Select</option>
                        <option value="Good">Good</option>
                        <option value="Poor">Poor</option>
                        <option value="Fair">Fair</option>
                        <option value="Limited">Limited</option>
                      </select>
                    </Field>
                    <Field label="Narrative">
                      <textarea
                        value={formData.social.notes}
                        onChange={(e) => updateField("social", "notes", e.target.value)}
                        style={styles.textarea}
                        placeholder="Social worker narrative and support context."
                      />
                    </Field>
                  </Card>

                  <Card title="2. Psychosocial Circumstances" subtitle="Caregiver stress and support" id="caregiver">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Caregiver burden level">
                        <select value={formData.caregiver.burden_level} onChange={(e) => updateField("caregiver", "burden_level", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Low">Low</option>
                          <option value="Moderate">Moderate</option>
                          <option value="High">High</option>
                        </select>
                      </Field>
                      <Field label="Caregiver name">
                        <input value={formData.caregiver.caregiver_name} onChange={(e) => updateField("caregiver", "caregiver_name", e.target.value)} style={styles.input} />
                      </Field>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Transportation barrier">
                        <select value={formData.caregiver.transportation_barrier} onChange={(e) => updateField("caregiver", "transportation_barrier", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Yes">Yes</option>
                          <option value="No">No</option>
                        </select>
                      </Field>
                      <Field label="Respite needs">
                        <input value={formData.caregiver.respite_needs} onChange={(e) => updateField("caregiver", "respite_needs", e.target.value)} style={styles.input} />
                      </Field>
                    </div>
                    <Field label="Caregiver concerns">
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 6 }}>
                        {["Burnout", "Isolation", "Anxiety", "Financial strain", "Transportation", "Respite"].map((option) => (
                          <label key={option} style={styles.checkboxLabel}>
                            <input
                              type="checkbox"
                              checked={formData.caregiver.caregiver_concerns.includes(option)}
                              onChange={() =>
                                updateField("caregiver", "caregiver_concerns", toggleValue(formData.caregiver.caregiver_concerns, option))
                              }
                            />
                            {option}
                          </label>
                        ))}
                      </div>
                    </Field>
                    <Field label="Caregiver notes">
                      <textarea value={formData.caregiver.notes} onChange={(e) => updateField("caregiver", "notes", e.target.value)} style={styles.textarea} />
                    </Field>
                  </Card>

                  <Card title="3. Patient — Psychosocial Distress/Concerns" subtitle="Select all that apply" id="distress">
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 6 }}>
                      {["Cannot respond", "Overwhelmed", "Fearful", "Unaware of condition", "Accepting", "Depressed", "Sad", "Guilt", "Denial", "Angry", "Loss of worth"].map((option) => (
                        <label key={option} style={styles.checkboxLabel}>
                          <input
                            type="checkbox"
                            checked={formData.risk.patient_psychosocial_concerns.includes(option)}
                            onChange={() =>
                              updateField("risk", "patient_psychosocial_concerns", toggleValue(formData.risk.patient_psychosocial_concerns, option))
                            }
                          />
                          {option}
                        </label>
                      ))}
                    </div>
                  </Card>
                </div>

                <div>
                  <Card title="4. Financial/Legal Needs" subtitle="Financial strain, housing, and safety" id="financial">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Financial stress">
                        <select value={formData.risk.financial_stress} onChange={(e) => updateField("risk", "financial_stress", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="No">No</option>
                          <option value="Yes">Yes</option>
                        </select>
                      </Field>
                      <Field label="Housing insecurity">
                        <select value={formData.risk.housing_insecurity} onChange={(e) => updateField("risk", "housing_insecurity", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="No">No</option>
                          <option value="Yes">Yes</option>
                        </select>
                      </Field>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Social isolation">
                        <select value={formData.risk.social_isolation} onChange={(e) => updateField("risk", "social_isolation", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="No">No</option>
                          <option value="Yes">Yes</option>
                        </select>
                      </Field>
                      <Field label="Safety concerns">
                        <select value={formData.risk.safety_concerns} onChange={(e) => updateField("risk", "safety_concerns", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="No">No</option>
                          <option value="Yes">Yes</option>
                        </select>
                      </Field>
                    </div>
                    <Field label="Financial / legal concerns">
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 6 }}>
                        {["None", "Utilities", "Rent", "Legal", "Insurance", "Benefits"].map((option) => (
                          <label key={option} style={styles.checkboxLabel}>
                            <input
                              type="checkbox"
                              checked={formData.risk.financial_legal_needs.includes(option)}
                              onChange={() => updateField("risk", "financial_legal_needs", toggleValue(formData.risk.financial_legal_needs, option))}
                            />
                            {option}
                          </label>
                        ))}
                      </div>
                    </Field>
                    <Field label="Financial / legal notes">
                      <textarea
                        value={formData.risk.financial_legal_notes}
                        onChange={(e) => updateField("risk", "financial_legal_notes", e.target.value)}
                        style={styles.textarea}
                      />
                    </Field>
                  </Card>

                  <Card title="5. Referrals" subtitle="Support services and follow-up" id="referrals">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Referral needed">
                        <select value={formData.interventions.referral_needed ? "Yes" : "No"} onChange={(e) => updateField("interventions", "referral_needed", e.target.value === "Yes")} style={styles.input}>
                          <option value="No">No</option>
                          <option value="Yes">Yes</option>
                        </select>
                      </Field>
                      <Field label="Referral type">
                        <input value={formData.interventions.referral_type} onChange={(e) => updateField("interventions", "referral_type", e.target.value)} style={styles.input} />
                      </Field>
                    </div>
                    <Field label="Intervention plan">
                      <textarea value={formData.interventions.intervention_plan} onChange={(e) => updateField("interventions", "intervention_plan", e.target.value)} style={styles.textarea} />
                    </Field>
                  </Card>

                  <Card title="6. Narrative (Include care provided items)" subtitle="Visit summary and interventions" id="narrative">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Support level">
                        <select value={formData.social.support_level} onChange={(e) => updateField("social", "support_level", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Strong">Strong</option>
                          <option value="Adequate">Adequate</option>
                          <option value="Limited">Limited</option>
                          <option value="None">None</option>
                        </select>
                      </Field>
                      <Field label="Priority level">
                        <select value={formData.interventions.priority_level} onChange={(e) => updateField("interventions", "priority_level", e.target.value)} style={styles.input}>
                          <option value="">Select</option>
                          <option value="Low">Low</option>
                          <option value="Moderate">Moderate</option>
                          <option value="High">High</option>
                        </select>
                      </Field>
                    </div>
                    <Field label="Narrative">
                      <textarea
                        value={formData.interventions.notes || formData.risk.notes || ""}
                        onChange={(e) => updateField("risk", "notes", e.target.value)}
                        style={styles.textarea}
                        placeholder="Document psychosocial narrative and care provided."
                      />
                    </Field>
                    <div style={{ marginTop: 6, fontSize: 11, color: "#64748b" }}>{selectedConcerns} concern(s) selected</div>
                  </Card>

                  <Card title="7. Signature" subtitle="Complete and sign" id="signature">
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
                    {intelligenceLoading && <div style={{ fontSize: 12, color: "#64748b" }}>Evaluating social-risk signals...</div>}
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
                    {!intelligenceLoading && !intelligence && <div style={{ fontSize: 12, color: "#64748b" }}>No intelligence available yet.</div>}
                  </Card>

                  <div style={styles.footer}>
                    <div style={{ fontSize: 11, color: "#475569", fontWeight: 700 }}>
                      {locked ? "LOCKED" : "IN PROGRESS"} · {summaryCount} completed field(s)
                    </div>
                    <div style={{ display: "flex", gap: 10 }}>
                      <button type="button" style={styles.button} onClick={handleSave} disabled={saving || locked}>
                        {saving ? "Saving..." : assessmentId ? "Update Assessment" : "Save Assessment"}
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
