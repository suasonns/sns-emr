import React, { useCallback, useEffect, useMemo, useState } from "react";
import { fetchPatientSummary } from "../api/patientCharts";
import { getCurrentUser } from "../api/session";
import { getActivePatientId } from "../utils/activePatient";
import {
  getScicaAssessment,
  getScicaAssessmentByPatient,
  lockScicaAssessment,
  saveScicaAssessment,
  updateScicaAssessment,
} from "../api/icaAssessments";
import { useAssessmentAutosave } from "../hooks/useAssessmentAutosave";

const STORAGE_PREFIX = "sns-hospice-solutions-sc-ica";
const SUICIDAL_THOUGHTS_OPTION = "Suicidal thoughts";
const RATED_BY_OPTIONS = ["Patient", "Clinician", "SC"];
const DISTRESS_DETAIL_OPTIONS = ["Unresolved life matters", "Anger/resentment", "Active grief response", "Fear of dying process", "Guilt/regret", "Other significant losses"];

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
  SUICIDAL_THOUGHTS_OPTION,
  "Social isolation",
  "Anticipatory grief",
  "Unresolved life matters",
  "Anger/resentment",
  "Active grief response",
  "Fear of dying process",
  "Guilt/regret",
  "Hopelessness",
  "Other significant losses",
  "Other",
];

const createSuicideRisk = () => ({
  ageSexRiskFactorsPresent: false,
  earlyChildhoodLoss: false,
  currentAlcoholDrugAbuse: false,
  recentIrreversibleLoss: false,
  specificSuicidePlanIdentified: false,
  lethalityOfMethod: "",
  meansAvailability: "",
  notLeftUnsupervised: false,
  notes: "",
  notifiedCaseManagerSupervisor: false,
  notifiedCaseManagerSupervisorAt: "",
  notifiedAttendingPhysician: false,
  notifiedAttendingPhysicianAt: "",
});

const createSourceDetails = () => ({
  "Unresolved life matters": "",
  "Anger/resentment": "",
  "Active grief response": "",
  "Fear of dying process": "",
  "Guilt/regret": "",
  "Other significant losses": "",
});

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
    sourceDetails: createSourceDetails(),
    rating: "",
    ratedBy: [],
    suicideRisk: createSuicideRisk(),
  },
  caregiverDistress: {
    sources: [],
    sourceOther: "",
    sourceDetails: createSourceDetails(),
    rating: "",
    ratedBy: [],
    suicideRisk: createSuicideRisk(),
  },
  narrative: {
    careProvided: [],
    careProvidedOther: "",
    note: "",
  },
  signature: {
    acknowledgement: "",
    signedByName: "",
    signedByUserId: "",
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
  sectionSubcard: { border: `1px solid ${CLINICAL_BRAND.line}`, background: "#f8fafc", borderRadius: 12, padding: 12, marginBottom: 10 },
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

function cloneInitialForm() {
  return JSON.parse(JSON.stringify(INITIAL_FORM));
}

function normalizeArray(value) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

function withFormDefaults(value) {
  const parsed = value && typeof value === "object" ? value : {};
  const base = cloneInitialForm();
  return {
    ...base,
    ...parsed,
    visitMeta: { ...base.visitMeta, ...(parsed.visitMeta || {}) },
    pain: { ...base.pain, ...(parsed.pain || {}) },
    deliveryOfCare: { ...base.deliveryOfCare, ...(parsed.deliveryOfCare || {}) },
    spiritualCircumstances: {
      ...base.spiritualCircumstances,
      ...(parsed.spiritualCircumstances || {}),
      patientFaithCommunity: {
        ...base.spiritualCircumstances.patientFaithCommunity,
        ...(parsed.spiritualCircumstances?.patientFaithCommunity || {}),
      },
      pcgFaithCommunity: {
        ...base.spiritualCircumstances.pcgFaithCommunity,
        ...(parsed.spiritualCircumstances?.pcgFaithCommunity || {}),
      },
      spiritualSupport: normalizeArray(parsed.spiritualCircumstances?.spiritualSupport),
    },
    patientDistress: {
      ...base.patientDistress,
      ...(parsed.patientDistress || {}),
      sources: normalizeArray(parsed.patientDistress?.sources),
      ratedBy: Array.isArray(parsed.patientDistress?.ratedBy) ? parsed.patientDistress.ratedBy.filter(Boolean) : [],
      sourceDetails: { ...base.patientDistress.sourceDetails, ...(parsed.patientDistress?.sourceDetails || {}) },
      suicideRisk: { ...base.patientDistress.suicideRisk, ...(parsed.patientDistress?.suicideRisk || {}) },
    },
    caregiverDistress: {
      ...base.caregiverDistress,
      ...(parsed.caregiverDistress || {}),
      sources: normalizeArray(parsed.caregiverDistress?.sources),
      ratedBy: Array.isArray(parsed.caregiverDistress?.ratedBy) ? parsed.caregiverDistress.ratedBy.filter(Boolean) : [],
      sourceDetails: { ...base.caregiverDistress.sourceDetails, ...(parsed.caregiverDistress?.sourceDetails || {}) },
      suicideRisk: { ...base.caregiverDistress.suicideRisk, ...(parsed.caregiverDistress?.suicideRisk || {}) },
    },
    narrative: {
      ...base.narrative,
      ...(parsed.narrative || {}),
      careProvided: normalizeArray(parsed.narrative?.careProvided),
    },
    signature: { ...base.signature, ...(parsed.signature || {}) },
  };
}

function todayDateString() {
  return new Date().toISOString().slice(0, 10);
}

function seedCurrentUserBindings(value, { preserveExisting = false, bindSignature = false } = {}) {
  const currentUser = getCurrentUser();
  const currentUserName = currentUser?.full_name || currentUser?.display_name || "";
  const currentUserId = currentUser?.id || "";
  const next = withFormDefaults(value);

  if (!preserveExisting || !next.visitMeta.enteredBy) next.visitMeta.enteredBy = currentUserName;
  if (!preserveExisting || !next.signature.signedByCredentials) next.signature.signedByCredentials = "SC";

  if (bindSignature || (next.signature.acknowledgement && (!preserveExisting || !next.signature.signedByName || !next.signature.signedByUserId))) {
    next.signature.signedByName = currentUserName;
    next.signature.signedByUserId = currentUserId;
    if (!next.signature.signedDate) next.signature.signedDate = todayDateString();
  }

  return next;
}

function readStoredForm(patientId) {
  const raw = localStorage.getItem(`${STORAGE_PREFIX}:${patientId}`);
  if (!raw) return seedCurrentUserBindings(INITIAL_FORM);
  try {
    return seedCurrentUserBindings(JSON.parse(raw));
  } catch {
    return seedCurrentUserBindings(INITIAL_FORM);
  }
}

function hasStoredForm(patientId) {
  return !!localStorage.getItem(`${STORAGE_PREFIX}:${patientId}`);
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

function notificationTimestamp(checked, currentValue) {
  if (checked) return currentValue || new Date().toISOString();
  return "";
}

function formatTimestampLabel(value) {
  if (!value) return "";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}


const api = {
  saveSCICAAssessment: (patientId, formData) => saveScicaAssessment({ patientId, formData }),
  getSCICAAssessment: (assessmentId) => getScicaAssessment(assessmentId),
  getSCICAAssessmentByPatient: (patientId) => getScicaAssessmentByPatient(patientId),
  updateSCICAAssessment: (assessmentId, formData) => updateScicaAssessment(assessmentId, formData),
  lockSCICAAssessment: (assessmentId) => lockScicaAssessment(assessmentId),
};

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

function DistressSourceGrid({ distress, onToggleSource, onSourceDetailChange }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 8 }}>
      {DISTRESS_OPTIONS.map((option) => {
        const needsDetail = DISTRESS_DETAIL_OPTIONS.includes(option) && distress.sources.includes(option);
        return (
          <div key={option} style={{ minWidth: 0 }}>
            <label style={styles.checkboxLabel}>
              <input type="checkbox" checked={distress.sources.includes(option)} onChange={() => onToggleSource(option)} />
              {option}
            </label>
            {needsDetail ? (
              <input
                value={distress.sourceDetails?.[option] || ""}
                onChange={(e) => onSourceDetailChange(option, e.target.value)}
                style={{ ...styles.input, marginTop: 6, padding: "6px 8px", fontSize: 12 }}
                placeholder="Specify"
              />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function SuicideRiskCard({ distress, sectionKey, updateNestedField, imminentRisk, notificationsComplete }) {
  return (
    <div style={styles.sectionSubcard}>
      <div style={{ fontSize: 11, fontWeight: 700, color: "#b91c1c", textTransform: "uppercase", marginBottom: 8 }}>Suicide Risk - Documented Assessment</div>
      {!notificationsComplete ? (
        <div style={{ marginBottom: 10, padding: 8, borderRadius: 8, border: "1px solid #fca5a5", background: "#fef2f2", fontSize: 11, color: "#991b1b" }}>
          Both notification checkboxes must be completed before the assessment can be locked.
        </div>
      ) : null}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 10 }}>
        {[
          ["Age/sex statistical risk factors present", "ageSexRiskFactorsPresent"],
          ["Early childhood loss", "earlyChildhoodLoss"],
          ["Current alcohol/drug abuse", "currentAlcoholDrugAbuse"],
          ["Recent irreversible loss", "recentIrreversibleLoss"],
          ["Specific suicide plan identified", "specificSuicidePlanIdentified"],
        ].map(([label, key]) => (
          <div key={key}>
            <label style={styles.fieldLabel}>{label}</label>
            <label style={styles.checkboxLabel}>
              <input type="checkbox" checked={!!distress.suicideRisk[key]} onChange={(e) => updateNestedField(sectionKey, "suicideRisk", key, e.target.checked)} />
              Present
            </label>
          </div>
        ))}
        <Field label="Lethality of method">
          <select value={distress.suicideRisk.lethalityOfMethod} onChange={(e) => updateNestedField(sectionKey, "suicideRisk", "lethalityOfMethod", e.target.value)} style={styles.select}>
            <option value="">Select</option>
            <option value="Low">Low</option>
            <option value="Moderate">Moderate</option>
            <option value="High">High</option>
          </select>
        </Field>
        <Field label="Means availability">
          <select value={distress.suicideRisk.meansAvailability} onChange={(e) => updateNestedField(sectionKey, "suicideRisk", "meansAvailability", e.target.value)} style={styles.select}>
            <option value="">Select</option>
            <option value="Yes">Yes</option>
            <option value="No">No</option>
            <option value="Unknown">Unknown</option>
          </select>
        </Field>
        {imminentRisk ? (
          <div>
            <label style={styles.fieldLabel}>Imminent-risk supervision</label>
            <label style={styles.checkboxLabel}>
              <input type="checkbox" checked={distress.suicideRisk.notLeftUnsupervised} onChange={(e) => updateNestedField(sectionKey, "suicideRisk", "notLeftUnsupervised", e.target.checked)} />
              Patient is not to be left unsupervised
            </label>
          </div>
        ) : null}
        <div>
          <label style={styles.fieldLabel}>Notified - Case Manager / Supervisor</label>
          <label style={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={distress.suicideRisk.notifiedCaseManagerSupervisor}
              onChange={(e) => {
                updateNestedField(sectionKey, "suicideRisk", "notifiedCaseManagerSupervisor", e.target.checked);
                updateNestedField(sectionKey, "suicideRisk", "notifiedCaseManagerSupervisorAt", notificationTimestamp(e.target.checked, distress.suicideRisk.notifiedCaseManagerSupervisorAt));
              }}
            />
            Confirmed{distress.suicideRisk.notifiedCaseManagerSupervisorAt ? ` · ${formatTimestampLabel(distress.suicideRisk.notifiedCaseManagerSupervisorAt)}` : ""}
          </label>
        </div>
        <div>
          <label style={styles.fieldLabel}>Notified - Attending Physician</label>
          <label style={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={distress.suicideRisk.notifiedAttendingPhysician}
              onChange={(e) => {
                updateNestedField(sectionKey, "suicideRisk", "notifiedAttendingPhysician", e.target.checked);
                updateNestedField(sectionKey, "suicideRisk", "notifiedAttendingPhysicianAt", notificationTimestamp(e.target.checked, distress.suicideRisk.notifiedAttendingPhysicianAt));
              }}
            />
            Confirmed{distress.suicideRisk.notifiedAttendingPhysicianAt ? ` · ${formatTimestampLabel(distress.suicideRisk.notifiedAttendingPhysicianAt)}` : ""}
          </label>
        </div>
        <div style={{ gridColumn: "1 / -1" }}>
          <Field label="Suicide-risk notes">
            <textarea
              value={distress.suicideRisk.notes}
              onChange={(e) => updateNestedField(sectionKey, "suicideRisk", "notes", e.target.value)}
              style={styles.textarea}
              placeholder="Document the discussion, interventions, notifications, and referral follow-up..."
            />
          </Field>
        </div>
      </div>
    </div>
  );
}

export default function SCICA({ patientId = getActivePatientId() ?? "", assessmentId: existingAssessmentId = undefined, mode = "ica" }) {
  const currentUser = useMemo(() => getCurrentUser(), []);
  const [patientSummary, setPatientSummary] = useState(null);
  const [patientSummaryError, setPatientSummaryError] = useState("");
  const [formData, setFormData] = useState(() => readStoredForm(patientId));
  const [assessmentId, setAssessmentId] = useState(existingAssessmentId || null);
  const [saveStatus, setSaveStatus] = useState(null);
  const [lastSavedAt, setLastSavedAt] = useState("");
  const [saving, setSaving] = useState(false);
  const [locked, setLocked] = useState(false);
  const [pageError, setPageError] = useState("");

  const prepareFormForPersist = useCallback((value, options = {}) => seedCurrentUserBindings(value, options), []);

  const autosaveSave = useCallback(async (currentPatientId, currentFormData) => {
    const payload = prepareFormForPersist(currentFormData);
    setFormData(payload);
    return api.saveSCICAAssessment(currentPatientId, payload);
  }, [prepareFormForPersist]);

  const autosaveUpdate = useCallback(async (currentAssessmentId, currentFormData) => {
    const payload = prepareFormForPersist(currentFormData);
    setFormData(payload);
    return api.updateSCICAAssessment(currentAssessmentId, payload);
  }, [prepareFormForPersist]);

  const { markPersisted, resetAutosaveTracking } = useAssessmentAutosave({
    formData,
    assessmentId,
    setAssessmentId,
    locked,
    saving,
    saveFn: autosaveSave,
    updateFn: autosaveUpdate,
    patientId,
    intervalMs: 30000,
  });

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
    const nextFormData = readStoredForm(patientId);
    setFormData(nextFormData);
    setAssessmentId(existingAssessmentId || null);
    setSaveStatus(null);
    setLastSavedAt("");
    setLocked(false);
    setPageError("");
    resetAutosaveTracking({
      markCurrentAsPersisted: !hasStoredForm(patientId),
      persistedFormData: nextFormData,
      persistedAssessmentId: existingAssessmentId || null,
    });
  }, [existingAssessmentId, patientId, resetAutosaveTracking]);

  useEffect(() => {
    if (!patientId && !existingAssessmentId) return;

    let mounted = true;
    const loadAssessment = existingAssessmentId
      ? api.getSCICAAssessment(existingAssessmentId)
      : api.getSCICAAssessmentByPatient(patientId);

    loadAssessment
      .then((data) => {
        if (!mounted) return;
        if (!data?.assessmentId) {
          setAssessmentId(null);
          setLocked(false);
          return;
        }
        if (data.formData) {
          const preparedFormData = prepareFormForPersist(data.formData, { preserveExisting: !!data.locked });
          setFormData(preparedFormData);
          markPersisted(preparedFormData, data.assessmentId || existingAssessmentId);
        }
        setLocked(!!data.locked);
        setAssessmentId(data.assessmentId || existingAssessmentId);
      })
      .catch((error) => {
        if (!mounted) return;
        console.error("Failed to load SCICA assessment:", error);
        setPageError(error instanceof Error ? error.message : "Unable to load SCICA assessment.");
      });

    return () => {
      mounted = false;
    };
  }, [existingAssessmentId, markPersisted, patientId, prepareFormForPersist]);

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
    setFormData((prev) => prepareFormForPersist({
      ...prev,
      visitMeta: {
        ...prev.visitMeta,
        staffAssigned: prev.visitMeta.staffAssigned || spiritualStaff?.staff_name || currentUser?.full_name || "",
        careLevel: prev.visitMeta.careLevel || patientSummary.patient.acuity_state || "",
      },
    }, { preserveExisting: true }));
  }, [currentUser?.full_name, patientSummary, prepareFormForPersist]);

  const updateSection = useCallback((section, key, value) => {
    setFormData((prev) => withFormDefaults({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
    setSaveStatus(null);
    setPageError("");
  }, []);

  const updateNestedField = useCallback((section, parentKey, key, value) => {
    setFormData((prev) => withFormDefaults({
      ...prev,
      [section]: {
        ...prev[section],
        [parentKey]: {
          ...(prev[section]?.[parentKey] || {}),
          [key]: value,
        },
      },
    }));
    setSaveStatus(null);
    setPageError("");
  }, []);

  const updateFaithCommunity = useCallback((key, field, value) => {
    setFormData((prev) => withFormDefaults({
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
    setPageError("");
  }, []);

  const handleCopyFaithCommunity = useCallback((checked) => {
    setFormData((prev) => withFormDefaults({
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
    setPageError("");
  }, []);

  const notificationsCompleteFor = useCallback((section) => {
    const risk = section?.suicideRisk || {};
    return !!(risk.notifiedCaseManagerSupervisor && risk.notifiedAttendingPhysician);
  }, []);

  const patientSuicideRiskSelected = formData.patientDistress.sources.includes(SUICIDAL_THOUGHTS_OPTION);
  const caregiverSuicideRiskSelected = formData.caregiverDistress.sources.includes(SUICIDAL_THOUGHTS_OPTION);
  const suicideRiskSelected = patientSuicideRiskSelected || caregiverSuicideRiskSelected;
  const patientNotificationsComplete = !patientSuicideRiskSelected || notificationsCompleteFor(formData.patientDistress);
  const caregiverNotificationsComplete = !caregiverSuicideRiskSelected || notificationsCompleteFor(formData.caregiverDistress);
  const suicideNotificationsComplete = patientNotificationsComplete && caregiverNotificationsComplete;
  const lockBlockedReason = suicideRiskSelected && !suicideNotificationsComplete
    ? "Suicide risk is documented. Confirm both Case Manager/Supervisor and Attending Physician notifications before locking the assessment."
    : "";

  const patientImminentSuicideRisk = patientSuicideRiskSelected && (
    formData.patientDistress.suicideRisk.specificSuicidePlanIdentified
    || formData.patientDistress.suicideRisk.lethalityOfMethod === "High"
    || formData.patientDistress.suicideRisk.meansAvailability === "Yes"
  );
  const caregiverImminentSuicideRisk = caregiverSuicideRiskSelected && (
    formData.caregiverDistress.suicideRisk.specificSuicidePlanIdentified
    || formData.caregiverDistress.suicideRisk.lethalityOfMethod === "High"
    || formData.caregiverDistress.suicideRisk.meansAvailability === "Yes"
  );

  const handleSave = useCallback(async () => {
    setSaving(true);
    setPageError("");
    try {
      const payload = prepareFormForPersist(formData);
      setFormData(payload);
      let activeAssessmentId = assessmentId;
      if (activeAssessmentId) {
        await api.updateSCICAAssessment(activeAssessmentId, payload);
      } else {
        const result = await api.saveSCICAAssessment(patientId, payload);
        activeAssessmentId = result.assessmentId;
        setAssessmentId(activeAssessmentId);
      }
      setLastSavedAt(new Date().toLocaleString());
      markPersisted(payload, activeAssessmentId);
      setSaveStatus("saved");
    } catch (error) {
      console.error("SCICA save error:", error);
      setSaveStatus("error");
      setPageError(error instanceof Error ? error.message : "Unable to save SCICA assessment.");
    } finally {
      setSaving(false);
    }
  }, [assessmentId, formData, markPersisted, patientId, prepareFormForPersist]);

  const handleLock = useCallback(async () => {
    if (!assessmentId) return;
    if (lockBlockedReason) {
      setPageError(lockBlockedReason);
      return;
    }
    setSaving(true);
    setPageError("");
    try {
      const payload = prepareFormForPersist({
        ...formData,
        signature: {
          ...formData.signature,
          signedDate: formData.signature.signedDate || todayDateString(),
          reviewDate: formData.signature.reviewDate || todayDateString(),
        },
      }, { bindSignature: true });
      setFormData(payload);
      await api.updateSCICAAssessment(assessmentId, payload);
      await api.lockSCICAAssessment(assessmentId);
      setLocked(true);
      setLastSavedAt(new Date().toLocaleString());
      markPersisted(payload, assessmentId);
      setSaveStatus("saved");
    } catch (error) {
      console.error("SCICA lock error:", error);
      setPageError(error instanceof Error ? error.message : "Unable to lock SCICA assessment.");
    } finally {
      setSaving(false);
    }
  }, [assessmentId, formData, lockBlockedReason, markPersisted, prepareFormForPersist]);

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

  const gotoSection = useCallback((section) => {
    document.getElementById(section)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const saveButtonLabel = assessmentId ? "Update Assessment" : "Save Assessment";

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
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.82)", marginTop: 4 }}>{locked ? "LOCKED" : "IN PROGRESS"} · {completedFields} documented value(s)</div>
              </div>
            </div>

            <div style={styles.metaBar}>
              <div style={{ display: "grid", gridTemplateColumns: "180px repeat(4, minmax(0, 1fr))", gap: 12, marginBottom: 12 }}>
                <Field label="Correction">
                  <label style={styles.checkboxLabel}>
                    <input type="checkbox" checked={formData.visitMeta.correction} onChange={(e) => updateSection("visitMeta", "correction", e.target.checked)} />
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

              {formData.visitMeta.visitKind === "Other" ? (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(5, minmax(0, 1fr))", gap: 12, marginBottom: 12 }}>
                  <Field label="Visit specify">
                    <input value={formData.visitMeta.visitKindSpecify} onChange={(e) => updateSection("visitMeta", "visitKindSpecify", e.target.value)} style={styles.input} />
                  </Field>
                </div>
              ) : null}

              <div style={{ display: "grid", gridTemplateColumns: "repeat(6, minmax(0, 1fr))", gap: 12 }}>
                <Field label="Time In"><input type="time" value={formData.visitMeta.timeIn} onChange={(e) => updateSection("visitMeta", "timeIn", e.target.value)} style={styles.input} /></Field>
                <Field label="Time Out"><input type="time" value={formData.visitMeta.timeOut} onChange={(e) => updateSection("visitMeta", "timeOut", e.target.value)} style={styles.input} /></Field>
                <Field label="Duration (h:m)"><input value={formData.visitMeta.duration} onChange={(e) => updateSection("visitMeta", "duration", e.target.value)} style={styles.input} placeholder="1h 15m" /></Field>
                <Field label="Entered By"><input value={formData.visitMeta.enteredBy} onChange={(e) => updateSection("visitMeta", "enteredBy", e.target.value)} style={styles.input} /></Field>
                <Field label="Staff Assigned"><input value={formData.visitMeta.staffAssigned} onChange={(e) => updateSection("visitMeta", "staffAssigned", e.target.value)} style={styles.input} /></Field>
                <Field label="Discipline"><input value={formData.visitMeta.discipline} readOnly style={{ ...styles.input, background: "#f8fafc" }} /></Field>
                <Field label="Care Level"><input value={formData.visitMeta.careLevel} readOnly style={{ ...styles.input, background: "#f8fafc" }} /></Field>
              </div>
            </div>

            <div style={styles.content}>
              {patientSummaryError ? <div style={styles.alert}>Patient summary: {patientSummaryError}</div> : null}
              {pageError ? <div style={styles.alert}>{pageError}</div> : null}

              <Card title="1. Pain" subtitle="Comfort screening at the spiritual care visit" id="pain">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 220px", gap: 12, alignItems: "end" }}>
                  <Field label="Is Pain controlled at a comfortable level?"><select value={formData.pain.controlled} onChange={(e) => updateSection("pain", "controlled", e.target.value)} style={styles.select}>{selectOptions(YES_NO)}</select></Field>
                  <Field label="If No, Pain level?"><input type="number" min="0" max="10" value={formData.pain.level} onChange={(e) => updateSection("pain", "level", e.target.value)} style={styles.input} disabled={formData.pain.controlled !== "No"} /></Field>
                  <button type="button" style={styles.stubButton} disabled>Pain Assessment Tool</button>
                </div>
              </Card>

              <Card title="2. Delivery of Care" subtitle="Who will provide spiritual support services" id="deliveryOfCare">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Field label="Spiritual Care Declined by Patient/Family?"><select value={formData.deliveryOfCare.declined} onChange={(e) => updateSection("deliveryOfCare", "declined", e.target.value)} style={styles.select}>{selectOptions(YES_NO)}</select></Field>
                  <Field label="Will care be provided by hospice Spiritual Counselor?"><select value={formData.deliveryOfCare.hospiceScProvided} onChange={(e) => updateSection("deliveryOfCare", "hospiceScProvided", e.target.value)} style={styles.select} disabled={formData.deliveryOfCare.declined === "Yes"}>{selectOptions(YES_NO)}</select></Field>
                </div>

                {formData.deliveryOfCare.declined !== "Yes" && formData.deliveryOfCare.hospiceScProvided === "No" ? (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12 }}>
                    <Field label="Who will deliver spiritual care — Name"><input value={formData.deliveryOfCare.alternateCaregiverName} onChange={(e) => updateSection("deliveryOfCare", "alternateCaregiverName", e.target.value)} style={styles.input} /></Field>
                    <Field label="Relation"><input value={formData.deliveryOfCare.alternateCaregiverRelation} onChange={(e) => updateSection("deliveryOfCare", "alternateCaregiverRelation", e.target.value)} style={styles.input} /></Field>
                    <Field label="Phone"><input value={formData.deliveryOfCare.alternateCaregiverPhone} onChange={(e) => updateSection("deliveryOfCare", "alternateCaregiverPhone", e.target.value)} style={styles.input} /></Field>
                  </div>
                ) : null}
              </Card>

              <Card title="3. Spiritual Circumstances" subtitle="Faith communities, cultural influences, and support resources" id="spiritualCircumstances">
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Observed patient mental status"><select value={formData.spiritualCircumstances.mentalStatus} onChange={(e) => updateSection("spiritualCircumstances", "mentalStatus", e.target.value)} style={styles.select}>{selectOptions(MENTAL_STATUS_OPTIONS)}</select></Field>
                  <Field label="Historian"><select value={formData.spiritualCircumstances.historian} onChange={(e) => updateSection("spiritualCircumstances", "historian", e.target.value)} style={styles.select}>{selectOptions(["", "Patient", "PCG", "Other"])}</select></Field>
                  <Field label="Marital Status"><select value={formData.spiritualCircumstances.maritalStatus} onChange={(e) => updateSection("spiritualCircumstances", "maritalStatus", e.target.value)} style={styles.select}>{selectOptions(MARITAL_STATUS_OPTIONS)}</select></Field>
                  <Field label="Children under 21"><input type="number" min="0" value={formData.spiritualCircumstances.childrenUnder21} onChange={(e) => updateSection("spiritualCircumstances", "childrenUnder21", e.target.value)} style={styles.input} /></Field>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Children living in patient's home"><input type="number" min="0" value={formData.spiritualCircumstances.childrenInHome} onChange={(e) => updateSection("spiritualCircumstances", "childrenInHome", e.target.value)} style={styles.input} /></Field>
                </div>

                {formData.spiritualCircumstances.historian === "Other" ? (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <Field label="Historian Name"><input value={formData.spiritualCircumstances.historianOtherName} onChange={(e) => updateSection("spiritualCircumstances", "historianOtherName", e.target.value)} style={styles.input} /></Field>
                    <Field label="Historian Relation"><input value={formData.spiritualCircumstances.historianOtherRelation} onChange={(e) => updateSection("spiritualCircumstances", "historianOtherRelation", e.target.value)} style={styles.input} /></Field>
                  </div>
                ) : null}

                <div style={styles.mutedBox}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>Patient Faith Community Information</div>
                  <FaithCommunityFields prefix="Patient" value={formData.spiritualCircumstances.patientFaithCommunity} onChange={(field, value) => updateFaithCommunity("patientFaithCommunity", field, value)} />
                </div>

                <div style={{ ...styles.mutedBox, marginTop: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap", marginBottom: 10 }}>
                    <div style={{ fontWeight: 700 }}>PCG Faith Community Information</div>
                    <label style={styles.checkboxLabel}>
                      <input type="checkbox" checked={formData.spiritualCircumstances.pcgFaithCommunity.sameAsPatient} onChange={(e) => handleCopyFaithCommunity(e.target.checked)} />
                      Same as Patient faith community information
                    </label>
                  </div>
                  <FaithCommunityFields prefix="PCG" value={formData.spiritualCircumstances.pcgFaithCommunity} onChange={(field, value) => updateFaithCommunity("pcgFaithCommunity", field, value)} />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
                  <Field label="Faith is primary factor in making healthcare decisions for"><select value={formData.spiritualCircumstances.faithDecisionMaker} onChange={(e) => updateSection("spiritualCircumstances", "faithDecisionMaker", e.target.value)} style={styles.select}>{selectOptions(["", "Patient", "PCG", "Patient and PCG", "Family", "Unknown"])}</select></Field>
                  <Field label="Cultural traditions are a primary factor in making healthcare decisions for"><select value={formData.spiritualCircumstances.cultureDecisionMaker} onChange={(e) => updateSection("spiritualCircumstances", "cultureDecisionMaker", e.target.value)} style={styles.select}>{selectOptions(["", "Patient", "PCG", "Patient and PCG", "Family", "Unknown"])}</select></Field>
                </div>

                <Field label="Spiritual Support"><CheckboxGrid options={SPIRITUAL_SUPPORT_OPTIONS} values={formData.spiritualCircumstances.spiritualSupport} onToggle={(option) => updateSection("spiritualCircumstances", "spiritualSupport", toggleValue(formData.spiritualCircumstances.spiritualSupport, option))} columns={3} /></Field>
                {formData.spiritualCircumstances.spiritualSupport.includes("Other") ? <Field label="Spiritual support — other"><input value={formData.spiritualCircumstances.spiritualSupportOther} onChange={(e) => updateSection("spiritualCircumstances", "spiritualSupportOther", e.target.value)} style={styles.input} /></Field> : null}
              </Card>

              <Card title="4. Patient - Spiritual Distress/Concern" subtitle="Patient distress sources and spiritual distress rating" id="patientDistress">
                <Field label="Patient status"><label style={styles.checkboxLabel}><input type="checkbox" checked={formData.patientDistress.unresponsive} onChange={(e) => updateSection("patientDistress", "unresponsive", e.target.checked)} />Check here if the Patient is unresponsive</label></Field>
                <Field label="Sources of Distress/Concern"><DistressSourceGrid distress={formData.patientDistress} onToggleSource={(option) => updateSection("patientDistress", "sources", toggleValue(formData.patientDistress.sources, option))} onSourceDetailChange={(option, value) => updateNestedField("patientDistress", "sourceDetails", option, value)} /></Field>
                {formData.patientDistress.sources.includes("Other") ? <Field label="Patient distress — other"><input value={formData.patientDistress.sourceOther} onChange={(e) => updateSection("patientDistress", "sourceOther", e.target.value)} style={styles.input} /></Field> : null}
                {patientSuicideRiskSelected ? <SuicideRiskCard distress={formData.patientDistress} sectionKey="patientDistress" updateNestedField={updateNestedField} imminentRisk={patientImminentSuicideRisk} notificationsComplete={patientNotificationsComplete} /> : null}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Field label="Spiritual Distress Rating"><select value={formData.patientDistress.rating} onChange={(e) => updateSection("patientDistress", "rating", e.target.value)} style={styles.select}>{selectOptions(RATING_OPTIONS)}</select></Field>
                  <Field label="Rated by"><CheckboxGrid options={RATED_BY_OPTIONS} values={formData.patientDistress.ratedBy} onToggle={(option) => updateSection("patientDistress", "ratedBy", toggleValue(formData.patientDistress.ratedBy, option))} columns={3} /></Field>
                </div>
              </Card>

              <Card title="5. PCG - Spiritual Distress/Concern" subtitle="Primary caregiver distress sources and rating" id="caregiverDistress">
                <Field label="Sources of Distress/Concern"><DistressSourceGrid distress={formData.caregiverDistress} onToggleSource={(option) => updateSection("caregiverDistress", "sources", toggleValue(formData.caregiverDistress.sources, option))} onSourceDetailChange={(option, value) => updateNestedField("caregiverDistress", "sourceDetails", option, value)} /></Field>
                {formData.caregiverDistress.sources.includes("Other") ? <Field label="PCG distress — other"><input value={formData.caregiverDistress.sourceOther} onChange={(e) => updateSection("caregiverDistress", "sourceOther", e.target.value)} style={styles.input} /></Field> : null}
                {caregiverSuicideRiskSelected ? <SuicideRiskCard distress={formData.caregiverDistress} sectionKey="caregiverDistress" updateNestedField={updateNestedField} imminentRisk={caregiverImminentSuicideRisk} notificationsComplete={caregiverNotificationsComplete} /> : null}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Field label="Spiritual Distress Rating"><select value={formData.caregiverDistress.rating} onChange={(e) => updateSection("caregiverDistress", "rating", e.target.value)} style={styles.select}>{selectOptions(RATING_OPTIONS)}</select></Field>
                  <Field label="Rated by"><CheckboxGrid options={RATED_BY_OPTIONS} values={formData.caregiverDistress.ratedBy} onToggle={(option) => updateSection("caregiverDistress", "ratedBy", toggleValue(formData.caregiverDistress.ratedBy, option))} columns={3} /></Field>
                </div>
              </Card>

              <Card title="6. Care Provided And Narrative" subtitle="Document spiritual interventions and visit narrative" id="narrative">
                <Field label="Care provided"><CheckboxGrid options={["Active listening & emotional support", "Prayer & meditation guidance", "Anointing/blessing ritual", "Scripture or sacred text reading", "Religious rites/communion", "End-of-life ritual & funeral planning support", "Other"]} values={formData.narrative.careProvided} onToggle={(option) => updateSection("narrative", "careProvided", toggleValue(formData.narrative.careProvided, option))} columns={3} /></Field>
                {formData.narrative.careProvided.includes("Other") ? <Field label="Care provided — other"><input value={formData.narrative.careProvidedOther} onChange={(e) => updateSection("narrative", "careProvidedOther", e.target.value)} style={styles.input} /></Field> : null}
                <div style={{ marginBottom: 12 }}><button type="button" style={styles.stubButton} disabled>See history of modifications</button></div>
                <Field label="Narrative"><textarea value={formData.narrative.note} onChange={(e) => updateSection("narrative", "note", e.target.value)} style={styles.textarea} rows={10} /></Field>
              </Card>

              <Card title="Signature" subtitle="Visit acknowledgement and chaplain signature" id="signature">
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
                  <Field label="Signature of Patient / PCG to acknowledge visit"><select value={formData.signature.acknowledgement} onChange={(e) => updateSection("signature", "acknowledgement", e.target.value)} style={styles.select}>{selectOptions(["", "Signed", "Declined", "Unable to sign"])}</select></Field>
                  <Field label="Signed by"><input value={formData.signature.signedByName} onChange={(e) => updateSection("signature", "signedByName", e.target.value)} style={styles.input} readOnly={locked} /></Field>
                  <Field label="Credentials"><input value={formData.signature.signedByCredentials} onChange={(e) => updateSection("signature", "signedByCredentials", e.target.value)} style={styles.input} /></Field>
                  <Field label="Date"><input type="date" value={formData.signature.signedDate} onChange={(e) => updateSection("signature", "signedDate", e.target.value)} style={styles.input} /></Field>
                </div>

                <div style={styles.mutedBox}>
                  Signed by {formData.signature.signedByName || "________________"}, {formData.signature.signedByCredentials || "SC"}
                  {formData.signature.signedDate ? `, Date: ${formData.signature.signedDate}` : ", Date: ________________"}.
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 12, marginTop: 12 }}>
                  <Field label="Review / verification date"><input type="date" value={formData.signature.reviewDate} onChange={(e) => updateSection("signature", "reviewDate", e.target.value)} style={styles.input} /></Field>
                </div>
              </Card>

              {lockBlockedReason ? <div style={{ ...styles.alert, marginTop: 0 }}>{lockBlockedReason}</div> : null}

              <div style={styles.footer}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                  <span style={styles.statusPill}>SC ICA</span>
                  <span style={{ fontSize: 11, color: "#475569", fontWeight: 700 }}>{lastSavedAt ? `Last saved ${lastSavedAt}` : "Unsaved changes"}</span>
                </div>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  <button type="button" style={{ ...styles.button, opacity: saving || locked ? 0.7 : 1, cursor: saving || locked ? "not-allowed" : "pointer" }} onClick={handleSave} disabled={saving || locked}>{saveButtonLabel}</button>
                  {assessmentId && !locked ? <button type="button" style={{ ...styles.button, background: "#fee2e2", opacity: saving || !!lockBlockedReason ? 0.7 : 1, cursor: saving || !!lockBlockedReason ? "not-allowed" : "pointer" }} onClick={handleLock} disabled={saving || !!lockBlockedReason}>Lock Assessment</button> : null}
                </div>
              </div>

              {saveStatus === "saved" ? <div style={{ marginTop: 10, fontSize: 12, color: "#166534" }}>SCICA saved successfully.</div> : null}
              {saveStatus === "error" ? <div style={{ marginTop: 10, fontSize: 12, color: "#92400e" }}>SCICA save failed — please try again.</div> : null}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
