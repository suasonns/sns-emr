import React, { useEffect, useMemo, useState } from "react";
import { fetchPatientSummary } from "../api/patientCharts";
import { getCurrentUser } from "../api/session";
import { getActivePatientId } from "../utils/activePatient";

const STORAGE_PREFIX = "sns-hospice-solutions-sc-ica";

const CLINICAL_BRAND = {
  navy: "#1E3A5F",
  teal: "#0D9488",
  tealDark: "#0F766E",
  tealLight: "#CCFBF1",
  bg: "#F8FAFC",
  canvas: "#EEF3E8",
  panel: "#FFFFFF",
  line: "#D8E3E8",
  text: "#0F172A",
  muted: "#64748B",
  slate: "#334155",
};

const YES_NO = ["", "Yes", "No"];
const MENTAL_STATUS_OPTIONS = ["", "Alert", "Awake", "Oriented", "Calm", "Confused", "Drowsy", "Withdrawn", "Tearful"];
const MARITAL_STATUS_OPTIONS = ["", "Widowed", "Married", "Single", "Divorced", "Separated", "Partnered"];
const INVOLVEMENT_OPTIONS = ["", "Active", "Inactive", "Occasional", "Unknown"];
const RATING_OPTIONS = ["", "None", "Mild", "Moderate", "Severe"];
const RATED_BY_OPTIONS = ["", "Patient", "Clinician", "SC"];
const SPIRITUAL_SUPPORT_OPTIONS = [
  "Faith Community",
  "Prayer",
  "Meditation",
  "Faith in God",
  "Scripture Reading",
  "Family",
  "Friends",
  "Pets",
  "Ethnic Community",
  "Art/Music/Literature",
  "Nature",
  "Other",
];
const DISTRESS_OPTIONS = [
  "Alienation from the Divine/loss of faith",
  "Alienation from faith community",
  "Anger at God",
  "Need to give/receive forgiveness of self or others",
  "Loss of meaning/self worth",
  "Concern about the afterlife",
  "Concerned about family/those left behind",
  "Family stress/conflict",
  "Relationships/Need for reconciliation",
  "Pain and suffering",
  "Loneliness",
  "Powerlessness",
  "Substance abuse",
  "Diagnosis/Prognosis",
  "Dying",
  "Loss of independence",
  "Depression",
  "Anxiety",
  "Denying reality",
  "Withdrawal",
  "Suicidal thoughts",
  "Social isolation",
  "Anticipatory grief",
  "Unfinished business",
  "Anger",
  "Grieving",
  "Fear",
  "Guilt",
  "Hopelessness",
  "Other losses",
  "Other",
];

const INITIAL_FORM = {
  visitMeta: {
    correction: false,
    typeOfVisit: "",
    visitKind: "",
    visitKindSpecify: "",
    reasonForVisit: "Initial Comprehensive Assessment",
    visitDate: "",
    timeIn: "",
    timeOut: "",
    duration: "",
    enteredBy: "",
    staffAssigned: "",
    discipline: "SC",
    careLevel: "",
  },
  pain: {
    controlled: "",
    level: "",
  },
  deliveryOfCare: {
    declined: "",
    hospiceScProvided: "",
    alternateCaregiverName: "",
    alternateCaregiverRelation: "",
    alternateCaregiverPhone: "",
  },
  spiritualCircumstances: {
    mentalStatus: "",
    historian: "",
    historianOtherName: "",
    historianOtherRelation: "",
    maritalStatus: "",
    childrenUnder21: "",
    childrenInHome: "",
    patientFaithCommunity: {
      faith: "",
      denomination: "",
      faithCommunityName: "",
      involvement: "",
      address: "",
      clergyName: "",
      phone: "",
    },
    pcgFaithCommunity: {
      sameAsPatient: false,
      faith: "",
      denomination: "",
      faithCommunityName: "",
      involvement: "",
      address: "",
      clergyName: "",
      phone: "",
    },
    faithDecisionMaker: "",
    cultureDecisionMaker: "",
    spiritualSupport: [],
    spiritualSupportOther: "",
  },
  patientDistress: {
    unresponsive: false,
    sources: [],
    sourceOther: "",
    rating: "",
    ratedBy: "",
  },
  caregiverDistress: {
    sources: [],
    sourceOther: "",
    rating: "",
    ratedBy: "",
  },
  narrative: {
    careProvided: [],
    careProvidedOther: "",
    note: "",
  },
  signature: {
    acknowledgement: "",
    signedByName: "",
    signedByCredentials: "SC",
    signedDate: "",
    reviewDate: "",
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
  metaBar: { padding: "16px 24px", background: "#F8FAFC", borderBottom: `1px solid ${CLINICAL_BRAND.line}` },
  content: { padding: 24 },
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
  mutedBox: { border: `1px solid ${CLINICAL_BRAND.line}`, background: "#F8FAFC", borderRadius: 12, padding: 12, fontSize: 12, color: CLINICAL_BRAND.slate },
  statusPill: { display: "inline-flex", alignItems: "center", borderRadius: 999, padding: "4px 8px", fontSize: 10, fontWeight: 800, textTransform: "uppercase", background: "#dcfce7", color: "#166534" },
  footer: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, paddingTop: 8, flexWrap: "wrap" },
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
  return `${Math.floor(diff / 60)}h ${diff % 60}m`;
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

function FaithCommunityFields({ prefix, value, onChange }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12 }}>
      <Field label={`${prefix} Faith`}>
        <select value={value.faith} onChange={(e) => onChange("faith", e.target.value)} style={styles.select}>
          {selectOptions(["", "Christian", "Catholic", "Jewish", "Muslim", "Buddhist", "Hindu", "None", "Other"])}
        </select>
      </Field>
      <Field label="Denomination">
        <input value={value.denomination} onChange={(e) => onChange("denomination", e.target.value)} style={styles.input} />
      </Field>
      <Field label="Name of Faith Community">
        <input value={value.faithCommunityName} onChange={(e) => onChange("faithCommunityName", e.target.value)} style={styles.input} />
      </Field>
      <Field label="Involvement">
        <select value={value.involvement} onChange={(e) => onChange("involvement", e.target.value)} style={styles.select}>
          {selectOptions(INVOLVEMENT_OPTIONS)}
        </select>
      </Field>
      <Field label="Address">
        <input value={value.address} onChange={(e) => onChange("address", e.target.value)} style={styles.input} />
      </Field>
      <Field label="Name of Clergy">
        <input value={value.clergyName} onChange={(e) => onChange("clergyName", e.target.value)} style={styles.input} />
      </Field>
      <Field label="Phone">
        <input value={value.phone} onChange={(e) => onChange("phone", e.target.value)} style={styles.input} />
      </Field>
    </div>
  );
}

export default function SCICA({ patientId = getActivePatientId() ?? "", mode = "ica" }) {
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
        if (mounted) setPatientSummary(summary);
      })
      .catch((error) => {
        console.error("Failed to load SC ICA patient summary:", error);
        if (mounted) setPatientSummaryError(error instanceof Error ? error.message : "Unable to load patient summary.");
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
          discipline: "SC",
        },
        signature: {
          signedByName: saved.signature?.signedByName || currentUser?.full_name || "",
          signedByCredentials: saved.signature?.signedByCredentials || "SC",
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
    if (!formData.spiritualCircumstances.pcgFaithCommunity.sameAsPatient) return;
    setFormData((prev) => ({
      ...prev,
      spiritualCircumstances: {
        ...prev.spiritualCircumstances,
        pcgFaithCommunity: {
          ...prev.spiritualCircumstances.patientFaithCommunity,
          sameAsPatient: true,
        },
      },
    }));
  }, [formData.spiritualCircumstances.patientFaithCommunity, formData.spiritualCircumstances.pcgFaithCommunity.sameAsPatient]);

  useEffect(() => {
    if (!patientSummary) return;
    const spiritualStaff = patientSummary.care_team.find((member) => String(member.discipline || "").toUpperCase().includes("SC"));
    setFormData((prev) => ({
      ...prev,
      visitMeta: {
        ...prev.visitMeta,
        staffAssigned: prev.visitMeta.staffAssigned || spiritualStaff?.staff_name || currentUser?.full_name || "",
        careLevel: prev.visitMeta.careLevel || patientSummary.patient.acuity_state || "",
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

  const updateFaithCommunity = (key, field, value) => {
    setFormData((prev) => ({
      ...prev,
      spiritualCircumstances: {
        ...prev.spiritualCircumstances,
        [key]: {
          ...prev.spiritualCircumstances[key],
          [field]: value,
        },
      },
    }));
    setSaveStatus(null);
  };

  const handleCopyFaithCommunity = (checked) => {
    setFormData((prev) => ({
      ...prev,
      spiritualCircumstances: {
        ...prev.spiritualCircumstances,
        pcgFaithCommunity: checked
          ? {
              ...prev.spiritualCircumstances.patientFaithCommunity,
              sameAsPatient: true,
            }
          : {
              ...prev.spiritualCircumstances.pcgFaithCommunity,
              sameAsPatient: false,
            },
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
  const completedFields = useMemo(() => {
    const countValues = (value) => {
      if (Array.isArray(value)) return value.filter(Boolean).length;
      if (value && typeof value === "object") return Object.values(value).reduce((sum, item) => sum + countValues(item), 0);
      return value ? 1 : 0;
    };
    return countValues(formData);
  }, [formData]);

  const sections = [
    { key: "pain", label: "1. Pain" },
    { key: "deliveryOfCare", label: "2. Delivery of Care" },
    { key: "spiritualCircumstances", label: "3. Spiritual Circumstances" },
    { key: "patientDistress", label: "4. Patient - Spiritual Distress/Concern" },
    { key: "caregiverDistress", label: "5. PCG - Spiritual Distress/Concern" },
    { key: "narrative", label: "6. Care Provided And Narrative" },
    { key: "signature", label: "Signature" },
  ];

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
                {sections.map((section) => (
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
                <div style={styles.headerTitle}>SC Initial Comprehensive Assessment</div>
                <div style={styles.headerSub}>Admission spiritual care assessment aligned to the production Spiritual Counselor form</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 11, fontWeight: 700 }}>{mode === "ongoing" ? "ICA FORM VIEW" : "INITIAL ASSESSMENT"}</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.82)", marginTop: 4 }}>{completedFields} documented value(s)</div>
              </div>
            </div>

            <div style={styles.metaBar}>
              <div style={{ display: "grid", gridTemplateColumns: "180px repeat(4, minmax(0, 1fr))", gap: 12, marginBottom: 12 }}>
                <Field label="Correction">
                  <label style={styles.checkboxLabel}>
                    <input
                      type="checkbox"
                      checked={formData.visitMeta.correction}
                      onChange={(e) => updateSection("visitMeta", "correction", e.target.checked)}
                    />
                    Correction
                  </label>
                </Field>
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
                <Field label="Reason for Visit">
                  <input value={formData.visitMeta.reasonForVisit} readOnly style={{ ...styles.input, background: "#f8fafc" }} />
                </Field>
                <Field label="Visit Date">
                  <input type="date" value={formData.visitMeta.visitDate} onChange={(e) => updateSection("visitMeta", "visitDate", e.target.value)} style={styles.input} />
                </Field>
              </div>

              {formData.visitMeta.visitKind === "Other" && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(5, minmax(0, 1fr))", gap: 12, marginBottom: 12 }}>
                  <Field label="Visit specify">
                    <input value={formData.visitMeta.visitKindSpecify} onChange={(e) => updateSection("visitMeta", "visitKindSpecify", e.target.value)} style={styles.input} />
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
                <Field label="Duration (h:m)">
                  <input value={formData.visitMeta.duration} onChange={(e) => updateSection("visitMeta", "duration", e.target.value)} style={styles.input} placeholder="1h 15m" />
                </Field>
                <Field label="Entered By">
                  <input value={formData.visitMeta.enteredBy} onChange={(e) => updateSection("visitMeta", "enteredBy", e.target.value)} style={styles.input} />
                </Field>
                <Field label="Staff Assigned">
                  <input value={formData.visitMeta.staffAssigned} onChange={(e) => updateSection("visitMeta", "staffAssigned", e.target.value)} style={styles.input} />
                </Field>
                <Field label="Discipline">
                  <input value={formData.visitMeta.discipline} readOnly style={{ ...styles.input, background: "#f8fafc" }} />
                </Field>
                <Field label="Care Level">
                  <input value={formData.visitMeta.careLevel} readOnly style={{ ...styles.input, background: "#f8fafc" }} />
                </Field>
              </div>
            </div>

            <div style={styles.content}>
              {patientSummaryError ? <div style={styles.alert}>Patient summary: {patientSummaryError}</div> : null}

              <Card title="1. Pain" subtitle="Comfort screening at the spiritual care visit" id="pain">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 220px", gap: 12, alignItems: "end" }}>
                  <Field label="Is Pain controlled at a comfortable level?">
                    <select value={formData.pain.controlled} onChange={(e) => updateSection("pain", "controlled", e.target.value)} style={styles.select}>
                      {selectOptions(YES_NO)}
                    </select>
                  </Field>
                  <Field label="If No, Pain level?">
                    <input
                      type="number"
                      min="0"
                      max="10"
                      value={formData.pain.level}
                      onChange={(e) => updateSection("pain", "level", e.target.value)}
                      style={styles.input}
                      disabled={formData.pain.controlled !== "No"}
                    />
                  </Field>
                  <button type="button" style={styles.stubButton} disabled>
                    Pain Assessment Tool
                  </button>
                </div>
              </Card>

              <Card title="2. Delivery of Care" subtitle="Who will provide spiritual support services" id="deliveryOfCare">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Field label="Spiritual Care Declined by Patient/Family?">
                    <select value={formData.deliveryOfCare.declined} onChange={(e) => updateSection("deliveryOfCare", "declined", e.target.value)} style={styles.select}>
                      {selectOptions(YES_NO)}
                    </select>
                  </Field>
                  <Field label="Will care be provided by hospice Spiritual Counselor?">
                    <select value={formData.deliveryOfCare.hospiceScProvided} onChange={(e) => updateSection("deliveryOfCare", "hospiceScProvided", e.target.value)} style={styles.select} disabled={formData.deliveryOfCare.declined === "Yes"}>
                      {selectOptions(YES_NO)}
                    </select>
                  </Field>
                </div>

                {formData.deliveryOfCare.declined !== "Yes" && formData.deliveryOfCare.hospiceScProvided === "No" && (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12 }}>
                    <Field label="Who will deliver spiritual care — Name">
                      <input value={formData.deliveryOfCare.alternateCaregiverName} onChange={(e) => updateSection("deliveryOfCare", "alternateCaregiverName", e.target.value)} style={styles.input} />
                    </Field>
                    <Field label="Relation">
                      <input value={formData.deliveryOfCare.alternateCaregiverRelation} onChange={(e) => updateSection("deliveryOfCare", "alternateCaregiverRelation", e.target.value)} style={styles.input} />
                    </Field>
                    <Field label="Phone">
                      <input value={formData.deliveryOfCare.alternateCaregiverPhone} onChange={(e) => updateSection("deliveryOfCare", "alternateCaregiverPhone", e.target.value)} style={styles.input} />
                    </Field>
                  </div>
                )}
              </Card>

              <Card title="3. Spiritual Circumstances" subtitle="Faith communities, cultural influences, and support resources" id="spiritualCircumstances">
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Observed patient mental status">
                    <select value={formData.spiritualCircumstances.mentalStatus} onChange={(e) => updateSection("spiritualCircumstances", "mentalStatus", e.target.value)} style={styles.select}>
                      {selectOptions(MENTAL_STATUS_OPTIONS)}
                    </select>
                  </Field>
                  <Field label="Historian">
                    <select value={formData.spiritualCircumstances.historian} onChange={(e) => updateSection("spiritualCircumstances", "historian", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Patient", "PCG", "Other"])}
                    </select>
                  </Field>
                  <Field label="Marital Status">
                    <select value={formData.spiritualCircumstances.maritalStatus} onChange={(e) => updateSection("spiritualCircumstances", "maritalStatus", e.target.value)} style={styles.select}>
                      {selectOptions(MARITAL_STATUS_OPTIONS)}
                    </select>
                  </Field>
                  <Field label="Children under 21">
                    <input type="number" min="0" value={formData.spiritualCircumstances.childrenUnder21} onChange={(e) => updateSection("spiritualCircumstances", "childrenUnder21", e.target.value)} style={styles.input} />
                  </Field>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Children living in patient's home">
                    <input type="number" min="0" value={formData.spiritualCircumstances.childrenInHome} onChange={(e) => updateSection("spiritualCircumstances", "childrenInHome", e.target.value)} style={styles.input} />
                  </Field>
                </div>

                {formData.spiritualCircumstances.historian === "Other" && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <Field label="Historian Name">
                      <input value={formData.spiritualCircumstances.historianOtherName} onChange={(e) => updateSection("spiritualCircumstances", "historianOtherName", e.target.value)} style={styles.input} />
                    </Field>
                    <Field label="Historian Relation">
                      <input value={formData.spiritualCircumstances.historianOtherRelation} onChange={(e) => updateSection("spiritualCircumstances", "historianOtherRelation", e.target.value)} style={styles.input} />
                    </Field>
                  </div>
                )}

                <div style={styles.mutedBox}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>Patient Faith Community Information</div>
                  <FaithCommunityFields
                    prefix="Patient"
                    value={formData.spiritualCircumstances.patientFaithCommunity}
                    onChange={(field, value) => updateFaithCommunity("patientFaithCommunity", field, value)}
                  />
                </div>

                <div style={{ ...styles.mutedBox, marginTop: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap", marginBottom: 10 }}>
                    <div style={{ fontWeight: 700 }}>PCG Faith Community Information</div>
                    <label style={styles.checkboxLabel}>
                      <input
                        type="checkbox"
                        checked={formData.spiritualCircumstances.pcgFaithCommunity.sameAsPatient}
                        onChange={(e) => handleCopyFaithCommunity(e.target.checked)}
                      />
                      Same as Patient faith community information
                    </label>
                  </div>
                  <FaithCommunityFields
                    prefix="PCG"
                    value={formData.spiritualCircumstances.pcgFaithCommunity}
                    onChange={(field, value) => updateFaithCommunity("pcgFaithCommunity", field, value)}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
                  <Field label="Faith is primary factor in making healthcare decisions for">
                    <select value={formData.spiritualCircumstances.faithDecisionMaker} onChange={(e) => updateSection("spiritualCircumstances", "faithDecisionMaker", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Patient", "PCG", "Patient and PCG", "Family", "Unknown"])}
                    </select>
                  </Field>
                  <Field label="Cultural traditions are a primary factor in making healthcare decisions for">
                    <select value={formData.spiritualCircumstances.cultureDecisionMaker} onChange={(e) => updateSection("spiritualCircumstances", "cultureDecisionMaker", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Patient", "PCG", "Patient and PCG", "Family", "Unknown"])}
                    </select>
                  </Field>
                </div>

                <Field label="Spiritual Support">
                  <CheckboxGrid
                    options={SPIRITUAL_SUPPORT_OPTIONS}
                    values={formData.spiritualCircumstances.spiritualSupport}
                    onToggle={(option) => updateSection("spiritualCircumstances", "spiritualSupport", toggleValue(formData.spiritualCircumstances.spiritualSupport, option))}
                    columns={3}
                  />
                </Field>
                {formData.spiritualCircumstances.spiritualSupport.includes("Other") && (
                  <Field label="Spiritual support — other">
                    <input value={formData.spiritualCircumstances.spiritualSupportOther} onChange={(e) => updateSection("spiritualCircumstances", "spiritualSupportOther", e.target.value)} style={styles.input} />
                  </Field>
                )}
              </Card>

              <Card title="4. Patient - Spiritual Distress/Concern" subtitle="Patient distress sources and spiritual distress rating" id="patientDistress">
                <Field label="Patient status">
                  <label style={styles.checkboxLabel}>
                    <input
                      type="checkbox"
                      checked={formData.patientDistress.unresponsive}
                      onChange={(e) => updateSection("patientDistress", "unresponsive", e.target.checked)}
                    />
                    Check here if the Patient is unresponsive
                  </label>
                </Field>
                <Field label="Sources of Distress/Concern">
                  <CheckboxGrid
                    options={DISTRESS_OPTIONS}
                    values={formData.patientDistress.sources}
                    onToggle={(option) => updateSection("patientDistress", "sources", toggleValue(formData.patientDistress.sources, option))}
                    columns={2}
                  />
                </Field>
                {formData.patientDistress.sources.includes("Other") && (
                  <Field label="Patient distress — other">
                    <input value={formData.patientDistress.sourceOther} onChange={(e) => updateSection("patientDistress", "sourceOther", e.target.value)} style={styles.input} />
                  </Field>
                )}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Field label="Spiritual Distress Rating">
                    <select value={formData.patientDistress.rating} onChange={(e) => updateSection("patientDistress", "rating", e.target.value)} style={styles.select}>
                      {selectOptions(RATING_OPTIONS)}
                    </select>
                  </Field>
                  <Field label="Rated by">
                    <select value={formData.patientDistress.ratedBy} onChange={(e) => updateSection("patientDistress", "ratedBy", e.target.value)} style={styles.select}>
                      {selectOptions(RATED_BY_OPTIONS)}
                    </select>
                  </Field>
                </div>
              </Card>

              <Card title="5. PCG - Spiritual Distress/Concern" subtitle="Primary caregiver distress sources and rating" id="caregiverDistress">
                <Field label="Sources of Distress/Concern">
                  <CheckboxGrid
                    options={DISTRESS_OPTIONS}
                    values={formData.caregiverDistress.sources}
                    onToggle={(option) => updateSection("caregiverDistress", "sources", toggleValue(formData.caregiverDistress.sources, option))}
                    columns={2}
                  />
                </Field>
                {formData.caregiverDistress.sources.includes("Other") && (
                  <Field label="PCG distress — other">
                    <input value={formData.caregiverDistress.sourceOther} onChange={(e) => updateSection("caregiverDistress", "sourceOther", e.target.value)} style={styles.input} />
                  </Field>
                )}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Field label="Spiritual Distress Rating">
                    <select value={formData.caregiverDistress.rating} onChange={(e) => updateSection("caregiverDistress", "rating", e.target.value)} style={styles.select}>
                      {selectOptions(RATING_OPTIONS)}
                    </select>
                  </Field>
                  <Field label="Rated by">
                    <select value={formData.caregiverDistress.ratedBy} onChange={(e) => updateSection("caregiverDistress", "ratedBy", e.target.value)} style={styles.select}>
                      {selectOptions(["", "PCG", "Clinician", "SC"])}
                    </select>
                  </Field>
                </div>
              </Card>

              <Card title="6. Care Provided And Narrative" subtitle="Document spiritual interventions and visit narrative" id="narrative">
                <Field label="Care provided">
                  <CheckboxGrid
                    options={["Listening/Emotional", "Prayer/Meditation", "Anointing & Blessing", "Scripture Reading", "Rites/Communion", "Funeral Planning", "Other"]}
                    values={formData.narrative.careProvided}
                    onToggle={(option) => updateSection("narrative", "careProvided", toggleValue(formData.narrative.careProvided, option))}
                    columns={3}
                  />
                </Field>
                {formData.narrative.careProvided.includes("Other") && (
                  <Field label="Care provided — other">
                    <input value={formData.narrative.careProvidedOther} onChange={(e) => updateSection("narrative", "careProvidedOther", e.target.value)} style={styles.input} />
                  </Field>
                )}
                <div style={{ marginBottom: 12 }}>
                  <button type="button" style={styles.stubButton} disabled>
                    See history of modifications
                  </button>
                </div>
                <Field label="Narrative">
                  <textarea value={formData.narrative.note} onChange={(e) => updateSection("narrative", "note", e.target.value)} style={styles.textarea} rows={10} />
                </Field>
              </Card>

              <Card title="Signature" subtitle="Visit acknowledgement and chaplain signature" id="signature">
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Signature of Patient / PCG to acknowledge visit">
                    <select value={formData.signature.acknowledgement} onChange={(e) => updateSection("signature", "acknowledgement", e.target.value)} style={styles.select}>
                      {selectOptions(["", "Signed", "Declined", "Unable to sign"])}
                    </select>
                  </Field>
                  <Field label="Signed by">
                    <input value={formData.signature.signedByName} onChange={(e) => updateSection("signature", "signedByName", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="Credentials">
                    <input value={formData.signature.signedByCredentials} onChange={(e) => updateSection("signature", "signedByCredentials", e.target.value)} style={styles.input} />
                  </Field>
                  <Field label="Date">
                    <input type="date" value={formData.signature.signedDate} onChange={(e) => updateSection("signature", "signedDate", e.target.value)} style={styles.input} />
                  </Field>
                </div>

                <div style={styles.mutedBox}>
                  Signed by {formData.signature.signedByName || "________________"}, {formData.signature.signedByCredentials || "SC"}
                  {formData.signature.signedDate ? `, Date: ${formData.signature.signedDate}` : ", Date: ________________"}.
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 12, marginTop: 12 }}>
                  <Field label="Review / verification date">
                    <input type="date" value={formData.signature.reviewDate} onChange={(e) => updateSection("signature", "reviewDate", e.target.value)} style={styles.input} />
                  </Field>
                </div>
              </Card>

              <div style={styles.footer}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                  <span style={styles.statusPill}>SC ICA</span>
                  <span style={{ fontSize: 11, color: "#475569", fontWeight: 700 }}>
                    {lastSavedAt ? `Last saved ${lastSavedAt}` : "Unsaved changes"}
                  </span>
                </div>
                <button type="button" style={styles.button} onClick={handleSave}>
                  Save Assessment
                </button>
              </div>

              {saveStatus === "saved" ? <div style={{ marginTop: 10, fontSize: 12, color: "#166534" }}>SC Initial Comprehensive Assessment saved locally.</div> : null}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
