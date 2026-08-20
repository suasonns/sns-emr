import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchPatientSummary } from "../api/patientCharts";
import { getActivePatientId } from "../utils/activePatient";
import {
  saveMswIcaAssessment,
  getMswIcaAssessment,
  getMswIcaAssessmentByPatient,
  updateMswIcaAssessment,
  lockMswIcaAssessment,
  getMswIcaIntelligence,
} from "../api/icaAssessments";
import AssessmentTypeToggle from "./AssessmentTypeToggle";
import { getCurrentUser } from "../api/session";
import { useThemeMode } from "../theme/theme";
import { getChartColors } from "../theme/chartColors";
import { useAssessmentAutosave } from "../hooks/useAssessmentAutosave";

const API_BASE = "/visits/msw-ica";
const STORAGE_PREFIX = "sns-hospice-solutions-msw-ica";

const NONE_IDENTIFIED_OPTION = "None identified";
const SUICIDE_RISK_OPTION = "Suicide risks";
const ABUSE_CONCERN_OPTION = "Abuse/neglect";
const SUPPORT_RELATIONSHIP_OPTIONS = ["", "Spouse/Partner", "Daughter", "Son", "Sibling", "Parent", "Friend", "Neighbor", "Paid caregiver", "Other"];
const ONGOING_COPING_OPTIONS = [
  "Access to accurate information",
  "Change in family roles",
  "Communication abilities",
  "Ability to fulfill desired sexual expression",
];
const ABUSE_CATEGORY_OPTIONS = ["Abuse/Domestic Violence", "Abandonment", "Neglect", "Exploitation"];

const createSupportPerson = () => ({ name: "", phone: "", relationship: "" });

const INITIAL_FORM = {
  pain: {
    uncomfortable: "",
    painLevel: "",
    mentalStatus: "",
    historian: "",
    historianOtherName: "",
    historianOtherRelation: "",
    notes: "",
  },
  psychosocial: {
    maritalStatus: "",
    childrenUnder21: "",
    childrenInHome: "",
    familyPcgName: "",
    familyPcgRelation: "",
    familyPcgHireDuration: "",
    patientLives: "",
    livingArrangement: "",
    familyCommunication: "",
    familyRelation: "",
    familyResponseToIllness: "",
    socialInteraction: "",
    supportSystem: "",
    supportPersons: [createSupportPerson(), createSupportPerson()],
    communitySupportSystems: "",
    communicationStyle: "",
    communicationStyleOther: "",
    drugAlcoholHistory: "",
    culturalDiversityCommunication: "",
    culturalDiversitySpace: "",
    culturalDiversityFamilyRole: "",
    culturalDiversityTraditions: "",
    responsiblePartyName: "",
    responsiblePartyRelationship: "",
    mentalCompetency: "",
    literacyLanguageSkills: "",
    legalConcerns: "",
    roleChanges: "",
    caregiverAvailabilityCapability: "",
    environmentalSafetyObstacles: "",
    spiritualIssuesConcern: false,
    spiritualIssuesNote: "",
    longTermCareAppropriate: "",
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
    anxietyRatedBy: "",
    distressRating: "",
    distressRatedBy: "",
    responseToPreviousLoss: "",
    copingStyle: "",
    illnessImpactPhysicalFunction: "",
    planOfCareComplianceObstacles: "",
    ongoingCopingItems: [],
    suicideRisk: {
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
    },
    abuseNeglectExploitation: {
      categories: [],
      indicatorsObserved: "",
      reportedTo: "",
      reportDate: "",
      reportReferenceCaseNumber: "",
      reportedBy: "",
      reportedByUserId: "",
    },
    notes: "",
  },
  familyDistress: {
    familyResponse: [],
    abilityToProvideCare: "",
    willingnessToProvideCare: "",
    familyCrisis: [],
    pcgAnxietyRating: "",
    pcgAnxietyRatedBy: "",
    notes: "",
  },
  financialLegal: {
    allNeedsMet: "",
    isVeteran: "",
    carePaidBy: "",
    financialAssessmentNote: "",
    patientLacks: [],
    needsAssistance: [],
    livingWill: "",
    livingWillCopy: "",
    livingWillNeedHelp: "",
    healthPOA: "",
    healthPOACopy: "",
    healthPOANeedHelp: "",
    healthProxy: "",
    healthProxyCopy: "",
    healthProxyNeedHelp: "",
    burialPlans: "",
    burialPlansNeedHelp: "",
    mortuaryName: "",
    mortuaryPhone: "",
    mortuaryAddress: "",
    mortuaryCity: "",
    mortuaryState: "",
    mortuaryZip: "",
    notes: "",
  },
  referrals: {
    communityProgram: "",
    communityAccepted: "",
    communityReferralSatisfaction: "",
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
    clinician_user_id: "",
    signature_date: "",
    patient_acknowledgement: false,
    patient_signature_name: "",
    patient_signature_relationship: "",
    patient_signature_date: "",
    countersign_required: false,
    countersign_staff_name: "",
    countersign_staff_user_id: "",
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
    sectionStack: { display: "flex", flexDirection: "column", gap: 12 },
    sectionCard: { border: `1px solid ${brand.line}`, background: brand.panel, borderRadius: 12, overflow: "hidden" },
    sectionHeader: { background: brand.panel, padding: "10px 14px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, cursor: "pointer", userSelect: "none" },
    sectionTitle: { fontSize: 14, fontWeight: 700, fontStyle: "italic", color: brand.text },
    sectionHint: { fontSize: 10, color: brand.muted },
    sectionBadge: { display: "inline-flex", alignItems: "center", borderRadius: 999, padding: "2px 8px", fontSize: 10, fontWeight: 800, color: brand.tealDark, background: brand.tealLight, letterSpacing: ".04em", textTransform: "uppercase" },
    sectionComplete: { fontSize: 11, fontWeight: 700, color: "#166534" },
    sectionSummary: { fontSize: 11, color: brand.muted },
    sectionBody: { padding: 14 },
    fieldLabel: { display: "block", fontSize: 11, fontWeight: 700, marginBottom: 4, color: brand.slate },
    fieldShell: { minWidth: 0, marginBottom: 10 },
    fieldShellFull: { minWidth: 0, marginBottom: 10, gridColumn: "1 / -1" },
    sectionSubcard: { background: brand.canvas, border: `1px solid ${brand.line}`, borderRadius: 10, padding: 10, marginBottom: 12, color: brand.text },
    input: { width: "100%", boxSizing: "border-box", padding: "8px 10px", border: `1px solid ${brand.line}`, borderRadius: 10, background: brand.panel, color: brand.text, fontSize: 13 },
    textarea: { width: "100%", boxSizing: "border-box", padding: "8px 10px", border: `1px solid ${brand.line}`, borderRadius: 10, background: brand.panel, color: brand.text, fontSize: 13, lineHeight: 1.3, resize: "vertical" },
    checkboxLabel: { display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11, color: brand.text },
    button: { border: `1px solid ${brand.teal}`, background: brand.panel, color: brand.tealDark, borderRadius: 10, padding: "8px 14px", fontSize: 12, cursor: "pointer", fontWeight: 700 },
    footer: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, paddingTop: 8, flexWrap: "wrap" },
    statusPill: { display: "inline-flex", alignItems: "center", borderRadius: 999, padding: "4px 8px", fontSize: 10, fontWeight: 800, textTransform: "uppercase" },
  };
}

function cloneInitialForm() {
  return JSON.parse(JSON.stringify(INITIAL_FORM));
}

function normalizeSupportPersons(items) {
  const normalized = Array.isArray(items)
    ? items.map((item) => ({
        ...createSupportPerson(),
        ...(item || {}),
      }))
    : [];
  while (normalized.length < 2) {
    normalized.push(createSupportPerson());
  }
  return normalized;
}

function withFormDefaults(value) {
  const parsed = value && typeof value === "object" ? value : {};
  const base = cloneInitialForm();
  return {
    ...base,
    ...parsed,
    pain: { ...base.pain, ...(parsed.pain || {}) },
    psychosocial: {
      ...base.psychosocial,
      ...(parsed.psychosocial || {}),
      supportPersons: normalizeSupportPersons(parsed.psychosocial?.supportPersons),
    },
    patientDistress: {
      ...base.patientDistress,
      ...(parsed.patientDistress || {}),
      iadl: { ...base.patientDistress.iadl, ...(parsed.patientDistress?.iadl || {}) },
      suicideRisk: { ...base.patientDistress.suicideRisk, ...(parsed.patientDistress?.suicideRisk || {}) },
      abuseNeglectExploitation: { ...base.patientDistress.abuseNeglectExploitation, ...(parsed.patientDistress?.abuseNeglectExploitation || {}) },
      patientResponse: Array.isArray(parsed.patientDistress?.patientResponse) ? parsed.patientDistress.patientResponse : [],
      patientConcerns: Array.isArray(parsed.patientDistress?.patientConcerns) ? parsed.patientDistress.patientConcerns : [],
      ongoingCopingItems: Array.isArray(parsed.patientDistress?.ongoingCopingItems) ? parsed.patientDistress.ongoingCopingItems : [],
    },
    familyDistress: {
      ...base.familyDistress,
      ...(parsed.familyDistress || {}),
      familyResponse: Array.isArray(parsed.familyDistress?.familyResponse) ? parsed.familyDistress.familyResponse : [],
      familyCrisis: Array.isArray(parsed.familyDistress?.familyCrisis) ? parsed.familyDistress.familyCrisis : [],
    },
    financialLegal: {
      ...base.financialLegal,
      ...(parsed.financialLegal || {}),
      patientLacks: Array.isArray(parsed.financialLegal?.patientLacks) ? parsed.financialLegal.patientLacks : [],
      needsAssistance: Array.isArray(parsed.financialLegal?.needsAssistance) ? parsed.financialLegal.needsAssistance : [],
    },
    referrals: {
      ...base.referrals,
      ...(parsed.referrals || {}),
      therapy: Array.isArray(parsed.referrals?.therapy) ? parsed.referrals.therapy : [],
      volunteerServices: Array.isArray(parsed.referrals?.volunteerServices) ? parsed.referrals.volunteerServices : [],
    },
    narrative: {
      ...base.narrative,
      ...(parsed.narrative || {}),
      careProvided: Array.isArray(parsed.narrative?.careProvided) ? parsed.narrative.careProvided : [],
    },
    finalization: { ...base.finalization, ...(parsed.finalization || {}) },
  };
}

function seedCurrentUserBindings(value, { preserveExisting = false } = {}) {
  const currentUser = getCurrentUser();
  const currentUserName = currentUser?.full_name || "";
  const currentUserId = currentUser?.id || "";
  const next = withFormDefaults(value);

  if (!preserveExisting || !next.finalization.clinician_name) next.finalization.clinician_name = currentUserName;
  if (!preserveExisting || !next.finalization.clinician_user_id) next.finalization.clinician_user_id = currentUserId;
  if (!preserveExisting || !next.finalization.countersign_staff_name) next.finalization.countersign_staff_name = currentUserName;
  if (!preserveExisting || !next.finalization.countersign_staff_user_id) next.finalization.countersign_staff_user_id = currentUserId;
  if ((!preserveExisting || !next.patientDistress.abuseNeglectExploitation.reportedBy) && next.patientDistress.abuseNeglectExploitation.categories.length) {
    next.patientDistress.abuseNeglectExploitation.reportedBy = currentUserName;
    next.patientDistress.abuseNeglectExploitation.reportedByUserId = currentUserId;
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

function toggleExclusiveValue(values, value, exclusiveValue) {
  if (value === exclusiveValue) {
    return values.includes(exclusiveValue) ? [] : [exclusiveValue];
  }
  const next = values.filter((item) => item !== exclusiveValue);
  return next.includes(value) ? next.filter((item) => item !== value) : [...next, value];
}

function todayDateString() {
  return new Date().toISOString().slice(0, 10);
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
  const [collapsedSections, setCollapsedSections] = useState(() => new Set());
  const [pendingAutoCollapse, setPendingAutoCollapse] = useState(true);
  const sectionRefs = useRef({});
  const isOngoing = mode === "ongoing";
  const [assessmentType, setAssessmentType] = useState("update");

  const prepareFormForPersist = useCallback((value, options = {}) => seedCurrentUserBindings(value, options), []);

  const autosaveSave = useCallback(async (currentPatientId, currentFormData) => {
    const payload = prepareFormForPersist(currentFormData);
    setFormData(payload);
    return api.saveMSWICAAssessment(currentPatientId, payload);
  }, [prepareFormForPersist]);

  const autosaveUpdate = useCallback(async (currentAssessmentId, currentFormData) => {
    const payload = prepareFormForPersist(currentFormData);
    setFormData(payload);
    return api.updateMSWICAAssessment(currentAssessmentId, payload);
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
        console.error("Failed to load MSW ICA patient summary:", error);
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
    setLocked(false);
    setSaveStatus(null);
    setPageError("");
    setIntelligence(null);
    setIntelligenceError("");
    setActiveSection("psychosocial");
    setCollapsedSections(new Set());
    setPendingAutoCollapse(true);
    resetAutosaveTracking({
      markCurrentAsPersisted: !hasStoredForm(patientId),
      persistedFormData: nextFormData,
      persistedAssessmentId: existingAssessmentId || null,
    });
  }, [existingAssessmentId, patientId, resetAutosaveTracking]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_PREFIX}:${patientId}`, JSON.stringify(formData));
  }, [formData, patientId]);

  const refreshIntelligence = useCallback(async (currentAssessmentId) => {
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
  }, []);

  useEffect(() => {
    if (!patientId && !existingAssessmentId) return;

    let mounted = true;
    const loadAssessment = existingAssessmentId
      ? api.getMSWICAAssessment(existingAssessmentId)
      : getMswIcaAssessmentByPatient(patientId);

    loadAssessment
      .then((data) => {
        if (!mounted) return null;
        if (!data?.assessmentId) {
          setAssessmentId(null);
          setLocked(false);
          setIntelligence(null);
          setIntelligenceError("");
          return null;
        }
        if (data.formData) {
          const preparedFormData = prepareFormForPersist(data.formData, { preserveExisting: !!data.locked });
          setFormData(preparedFormData);
          setCollapsedSections(new Set());
          setPendingAutoCollapse(true);
          markPersisted(preparedFormData, data.assessmentId || existingAssessmentId);
        }
        setLocked(!!data.locked);
        const resolvedId = data.assessmentId || existingAssessmentId;
        setAssessmentId(resolvedId);
        return refreshIntelligence(resolvedId);
      })
      .catch((err) => {
        if (!mounted) return;
        console.error("Failed to load MSW ICA assessment:", err);
        setPageError(err instanceof Error ? err.message : "Unable to load MSW ICA assessment.");
      });

    return () => {
      mounted = false;
    };
  }, [existingAssessmentId, markPersisted, patientId, prepareFormForPersist, refreshIntelligence]);

  useEffect(() => {
    if (assessmentId) refreshIntelligence(assessmentId);
  }, [assessmentId, refreshIntelligence]);

  const updateField = useCallback((section, key, value) => {
    setFormData((prev) => withFormDefaults({
      ...prev,
      [section]: key ? { ...prev[section], [key]: value } : value,
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

  const updateSupportPerson = useCallback((index, key, value) => {
    setFormData((prev) => {
      const arr = normalizeSupportPersons(prev.psychosocial.supportPersons);
      arr[index] = { ...arr[index], [key]: value };
      return withFormDefaults({
        ...prev,
        psychosocial: {
          ...prev.psychosocial,
          supportPersons: arr,
        },
      });
    });
    setSaveStatus(null);
    setPageError("");
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setPageError("");
    try {
      const payload = prepareFormForPersist(formData);
      setFormData(payload);
      let activeAssessmentId = assessmentId;
      if (activeAssessmentId) {
        await api.updateMSWICAAssessment(activeAssessmentId, payload);
      } else {
        const result = await api.saveMSWICAAssessment(patientId, payload);
        activeAssessmentId = result.assessmentId;
        setAssessmentId(activeAssessmentId);
      }
      await refreshIntelligence(activeAssessmentId);
      markPersisted(payload, activeAssessmentId);
      setSaveStatus("saved");
    } catch (err) {
      console.error("MSW ICA save error:", err);
      setSaveStatus("error");
      setPageError(err instanceof Error ? err.message : "Unable to save MSW ICA assessment.");
    } finally {
      setSaving(false);
    }
  }, [assessmentId, formData, markPersisted, patientId, prepareFormForPersist, refreshIntelligence]);

  const suicideRiskSelected = useMemo(
    () => formData.patientDistress.patientConcerns.includes(SUICIDE_RISK_OPTION) || formData.familyDistress.familyCrisis.includes(SUICIDE_RISK_OPTION),
    [formData.familyDistress.familyCrisis, formData.patientDistress.patientConcerns],
  );
  const abuseWorkflowActive = useMemo(
    () => formData.patientDistress.patientConcerns.includes(ABUSE_CONCERN_OPTION) || formData.patientDistress.abuseNeglectExploitation.categories.length > 0,
    [formData.patientDistress.abuseNeglectExploitation.categories.length, formData.patientDistress.patientConcerns],
  );
  const imminentSuicideRisk = useMemo(
    () => suicideRiskSelected && (
      formData.patientDistress.suicideRisk.specificSuicidePlanIdentified
      || formData.patientDistress.suicideRisk.lethalityOfMethod === "High"
      || formData.patientDistress.suicideRisk.meansAvailability === "Yes"
    ),
    [formData.patientDistress.suicideRisk.lethalityOfMethod, formData.patientDistress.suicideRisk.meansAvailability, formData.patientDistress.suicideRisk.specificSuicidePlanIdentified, suicideRiskSelected],
  );
  const suicideNotificationsComplete = formData.patientDistress.suicideRisk.notifiedCaseManagerSupervisor && formData.patientDistress.suicideRisk.notifiedAttendingPhysician;
  const lockBlockedReason = suicideRiskSelected && !suicideNotificationsComplete
    ? "Suicide risk is documented. Confirm both Case Manager/Supervisor and Attending Physician notifications before locking the assessment."
    : "";

  const handleLock = useCallback(async () => {
    if (!assessmentId) return;
    if (lockBlockedReason) {
      setPageError(lockBlockedReason);
      return;
    }
    setPageError("");
    setSaving(true);
    try {
      const payload = prepareFormForPersist({
        ...formData,
        finalization: {
          ...formData.finalization,
          assessment_complete: true,
          signature_date: formData.finalization.signature_date || todayDateString(),
          countersign_signature_date: formData.finalization.countersign_required
            ? (formData.finalization.countersign_signature_date || todayDateString())
            : formData.finalization.countersign_signature_date,
        },
      });
      setFormData(payload);
      await api.updateMSWICAAssessment(assessmentId, payload);
      await api.lockMSWICAAssessment(assessmentId);
      setLocked(true);
      await refreshIntelligence(assessmentId);
      markPersisted(payload, assessmentId);
    } catch (err) {
      console.error("MSW ICA lock error:", err);
      setPageError(err instanceof Error ? err.message : "Unable to lock MSW ICA assessment.");
    } finally {
      setSaving(false);
    }
  }, [assessmentId, formData, lockBlockedReason, markPersisted, prepareFormForPersist, refreshIntelligence]);
  const sections = useMemo(() => ([
    { key: "pain", formSection: "pain", label: "1. Pain", subtitle: "Patient response to illness", minWidth: 160 },
    { key: "psychosocial", formSection: "psychosocial", label: "2. Psychosocial Circumstances", subtitle: "Family, living arrangement, and support systems", minWidth: 180 },
    { key: "distress", formSection: "patientDistress", label: "3. Patient — Psychosocial Distress/Concerns", subtitle: "Select all that apply", minWidth: 160 },
    { key: "familyDistress", formSection: "familyDistress", label: "4. Family — Psychosocial Distress/Concerns", subtitle: "Family response, crisis, and anxiety", minWidth: 170 },
    { key: "financial", formSection: "financialLegal", label: "5. Financial / Legal Needs", subtitle: "Financial strain, advance directives, and mortuary", minWidth: 170 },
    { key: "referrals", formSection: "referrals", label: "6. Referrals", subtitle: "Community programs and support services", minWidth: 170 },
    { key: "narrative", formSection: "narrative", label: "7. Narrative (Include care provided items)", subtitle: "Visit summary and interventions", minWidth: 180 },
    { key: "signature", formSection: "finalization", label: "8. Signature", subtitle: "Complete and sign", minWidth: 200 },
  ]), []);

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

  const isSectionOpen = useCallback((key) => !collapsedSections.has(key), [collapsedSections]);

  const toggleSection = useCallback((key) => {
    setActiveSection(key);
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  }, []);

  const jumpToSection = useCallback((key) => {
    setActiveSection(key);
    setCollapsedSections((prev) => {
      if (!prev.has(key)) return prev;
      const next = new Set(prev);
      next.delete(key);
      return next;
    });
    requestAnimationFrame(() => {
      sectionRefs.current[key]?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, []);

  const completedSections = useMemo(() => sections.reduce((completed, section) => {
    const sectionData = formData[section.formSection];
    if (sectionData && JSON.stringify(sectionData) !== JSON.stringify(INITIAL_FORM[section.formSection])) {
      completed.push(section.key);
    }
    return completed;
  }, []), [formData, sections]);

  useEffect(() => {
    if (!pendingAutoCollapse) return;
    setCollapsedSections(new Set(completedSections));
    setPendingAutoCollapse(false);
  }, [completedSections, pendingAutoCollapse]);

  const gotoSection = useCallback((section) => {
    if (!section) return;
    jumpToSection(section);
  }, [jumpToSection]);

  const getGridStyle = useCallback((minWidth = 180) => ({
    display: "grid",
    gridTemplateColumns: `repeat(auto-fit, minmax(${minWidth}px, 1fr))`,
    gap: "0px 12px",
    alignItems: "start",
  }), []);

  const Field = ({ label, children, fullWidth = false, style = undefined }) => (
    <div style={{ ...(fullWidth ? styles.fieldShellFull : styles.fieldShell), ...style }}>
      <label style={styles.fieldLabel}>{label}</label>
      {children}
    </div>
  );

  const Card = ({ sectionKey, title, subtitle, children, badge = undefined }) => {
    const open = isSectionOpen(sectionKey);
    const isComplete = completedSections.includes(sectionKey);

    return (
      <section
        id={sectionKey}
        ref={(el) => { sectionRefs.current[sectionKey] = el; }}
        style={{
          ...styles.sectionCard,
          borderColor: activeSection === sectionKey ? CLINICAL_BRAND.teal : CLINICAL_BRAND.line,
        }}
      >
        <div
          onClick={() => toggleSection(sectionKey)}
          style={{
            ...styles.sectionHeader,
            background: activeSection === sectionKey ? CLINICAL_BRAND.tealLight : CLINICAL_BRAND.panel,
            borderBottom: open ? `1px solid ${CLINICAL_BRAND.line}` : "none",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
            <span style={{ fontSize: 12, color: CLINICAL_BRAND.muted, width: 14, display: "inline-block" }}>{open ? "▾" : "▸"}</span>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <span style={styles.sectionTitle}>{title}</span>
                {badge ? <span style={styles.sectionBadge}>{badge}</span> : null}
                {isComplete ? <span style={styles.sectionComplete}>✓ Complete</span> : null}
              </div>
              {subtitle ? <div style={styles.sectionHint}>{subtitle}</div> : null}
            </div>
          </div>
          {!open ? <span style={styles.sectionSummary}>{isComplete ? "Documented — tap to review" : "Not started — tap to document"}</span> : null}
        </div>
        {open ? (
          <div style={{ ...styles.sectionBody, contentVisibility: "auto", containIntrinsicSize: "600px" }}>
            {children}
          </div>
        ) : null}
      </section>
    );
  };

  const renderAllSections = () => sections.map((section) => {
    if (section.key === "pain") {
      return (
        <Card key={section.key} sectionKey={section.key} title={section.label} subtitle={section.subtitle}>
          <div style={getGridStyle(section.minWidth)}>
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
            <Field label="Observed patient mental status">
              <select value={formData.pain.mentalStatus} onChange={(e) => updateField("pain", "mentalStatus", e.target.value)} style={styles.input}>
                <option value="">Select</option>
                <option value="Awake">Awake</option>
                <option value="Alert & oriented">Alert & oriented</option>
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
            {formData.pain.historian === "Other" ? (
              <>
                <Field label="If other: name">
                  <input value={formData.pain.historianOtherName} onChange={(e) => updateField("pain", "historianOtherName", e.target.value)} style={styles.input} />
                </Field>
                <Field label="If other: relation">
                  <input value={formData.pain.historianOtherRelation} onChange={(e) => updateField("pain", "historianOtherRelation", e.target.value)} style={styles.input} />
                </Field>
              </>
            ) : null}
            <Field label="Narrative" fullWidth>
              <textarea
                value={formData.pain.notes}
                onChange={(e) => updateField("pain", "notes", e.target.value)}
                style={styles.textarea}
                placeholder="Social worker narrative and support context."
              />
            </Field>
          </div>
        </Card>
      );
    }

    if (section.key === "psychosocial") {
      const paidCaregiverSelected = formData.psychosocial.familyPcgRelation === "Paid caregiver";
      return (
        <Card key={section.key} sectionKey={section.key} title={section.label} subtitle={section.subtitle}>
          <div style={getGridStyle(section.minWidth)}>
            <Field label="Marital status"><select value={formData.psychosocial.maritalStatus} onChange={(e) => updateField("psychosocial", "maritalStatus", e.target.value)} style={styles.input}><option value="">Select</option><option value="Single">Single</option><option value="Married">Married</option><option value="Widowed">Widowed</option><option value="Divorced">Divorced</option><option value="Separated">Separated</option></select></Field>
            <Field label="# Children under 21"><input value={formData.psychosocial.childrenUnder21} onChange={(e) => updateField("psychosocial", "childrenUnder21", e.target.value)} style={styles.input} /></Field>
            <Field label="# Children living in patient's home"><input value={formData.psychosocial.childrenInHome} onChange={(e) => updateField("psychosocial", "childrenInHome", e.target.value)} style={styles.input} /></Field>
            <Field label="Family / PCG name"><input value={formData.psychosocial.familyPcgName} onChange={(e) => updateField("psychosocial", "familyPcgName", e.target.value)} style={styles.input} /></Field>
            <Field label="Relation"><select value={formData.psychosocial.familyPcgRelation} onChange={(e) => updateField("psychosocial", "familyPcgRelation", e.target.value)} style={styles.input}>{SUPPORT_RELATIONSHIP_OPTIONS.map((option) => (<option key={option || "blank"} value={option}>{option || "Select"}</option>))}</select></Field>
            {paidCaregiverSelected ? <Field label="If hired, for how long"><input value={formData.psychosocial.familyPcgHireDuration} onChange={(e) => updateField("psychosocial", "familyPcgHireDuration", e.target.value)} style={styles.input} /></Field> : null}
            <Field label="Responsible party name"><input value={formData.psychosocial.responsiblePartyName} onChange={(e) => updateField("psychosocial", "responsiblePartyName", e.target.value)} style={styles.input} /></Field>
            <Field label="Responsible party relationship"><input value={formData.psychosocial.responsiblePartyRelationship} onChange={(e) => updateField("psychosocial", "responsiblePartyRelationship", e.target.value)} style={styles.input} /></Field>
            <Field label="Patient lives"><select value={formData.psychosocial.patientLives} onChange={(e) => updateField("psychosocial", "patientLives", e.target.value)} style={styles.input}><option value="">Select</option><option value="Alone">Alone</option><option value="With Family">With Family</option><option value="in ALF">in ALF</option><option value="in SNF">in SNF</option><option value="Group Home">Group Home</option><option value="Other">Other</option></select></Field>
            <Field label="Living arrangement"><select value={formData.psychosocial.livingArrangement} onChange={(e) => updateField("psychosocial", "livingArrangement", e.target.value)} style={styles.input}><option value="">Select</option><option value="Satisfactory">Satisfactory</option><option value="Unsatisfactory">Unsatisfactory</option><option value="Other">Other</option></select></Field>
            <Field label="Family communication"><select value={formData.psychosocial.familyCommunication} onChange={(e) => updateField("psychosocial", "familyCommunication", e.target.value)} style={styles.input}><option value="">Select</option><option value="Good">Good</option><option value="Fair">Fair</option><option value="Poor">Poor</option><option value="Limited">Limited</option></select></Field>
            <Field label="Family relation"><select value={formData.psychosocial.familyRelation} onChange={(e) => updateField("psychosocial", "familyRelation", e.target.value)} style={styles.input}><option value="">Select</option><option value="Good">Good</option><option value="Fair">Fair</option><option value="Poor">Poor</option><option value="Strained">Strained</option></select></Field>
            <Field label="Family response to illness"><select value={formData.psychosocial.familyResponseToIllness} onChange={(e) => updateField("psychosocial", "familyResponseToIllness", e.target.value)} style={styles.input}><option value="">Select</option><option value="Supportive">Supportive</option><option value="Accepting">Accepting</option><option value="Denial">Denial</option><option value="Overwhelmed">Overwhelmed</option><option value="Other">Other</option></select></Field>
            <Field label="Social interaction"><select value={formData.psychosocial.socialInteraction} onChange={(e) => updateField("psychosocial", "socialInteraction", e.target.value)} style={styles.input}><option value="">Select</option><option value="Satisfactory">Satisfactory</option><option value="Limited">Limited</option><option value="Isolated">Isolated</option><option value="Other">Other</option></select></Field>
            <Field label="Support system"><select value={formData.psychosocial.supportSystem} onChange={(e) => updateField("psychosocial", "supportSystem", e.target.value)} style={styles.input}><option value="">Select</option><option value="Family">Family</option><option value="Friends">Friends</option><option value="Community">Community</option><option value="Church">Church</option><option value="None">None</option><option value="Other">Other</option></select></Field>
            <Field label="Community support systems in use"><input value={formData.psychosocial.communitySupportSystems} onChange={(e) => updateField("psychosocial", "communitySupportSystems", e.target.value)} style={styles.input} /></Field>
            <Field label="Preferred communication style"><select value={formData.psychosocial.communicationStyle} onChange={(e) => updateField("psychosocial", "communicationStyle", e.target.value)} style={styles.input}><option value="">Select</option><option value="Open discussion">Open discussion</option><option value="Quiet / reflective">Quiet / reflective</option><option value="Written prompts">Written prompts</option><option value="Needs family present">Needs family present</option><option value="Other">Other</option></select></Field>
            {formData.psychosocial.communicationStyle === "Other" ? <Field label="Communication style - other"><input value={formData.psychosocial.communicationStyleOther} onChange={(e) => updateField("psychosocial", "communicationStyleOther", e.target.value)} style={styles.input} /></Field> : null}
            <Field label="Mental competency evaluation"><select value={formData.psychosocial.mentalCompetency} onChange={(e) => updateField("psychosocial", "mentalCompetency", e.target.value)} style={styles.input}><option value="">Select</option><option value="Alert & oriented">Alert & oriented</option><option value="Impaired">Impaired</option><option value="Unable to assess">Unable to assess</option></select></Field>
            <Field label="Literacy and language skills"><input value={formData.psychosocial.literacyLanguageSkills} onChange={(e) => updateField("psychosocial", "literacyLanguageSkills", e.target.value)} style={styles.input} /></Field>
            <Field label="Legal concerns"><input value={formData.psychosocial.legalConcerns} onChange={(e) => updateField("psychosocial", "legalConcerns", e.target.value)} style={styles.input} /></Field>
            <Field label="Role changes due to illness"><input value={formData.psychosocial.roleChanges} onChange={(e) => updateField("psychosocial", "roleChanges", e.target.value)} style={styles.input} /></Field>
            <Field label="Caregiver availability / capability"><input value={formData.psychosocial.caregiverAvailabilityCapability} onChange={(e) => updateField("psychosocial", "caregiverAvailabilityCapability", e.target.value)} style={styles.input} /></Field>
            <Field label="Environmental safety obstacles"><input value={formData.psychosocial.environmentalSafetyObstacles} onChange={(e) => updateField("psychosocial", "environmentalSafetyObstacles", e.target.value)} style={styles.input} /></Field>
            <Field label="Long-term-care level appropriateness"><select value={formData.psychosocial.longTermCareAppropriate} onChange={(e) => updateField("psychosocial", "longTermCareAppropriate", e.target.value)} style={styles.input}><option value="">Select</option><option value="Appropriate as-is">Appropriate as-is</option><option value="Needs further evaluation">Needs further evaluation</option><option value="Higher level may be appropriate">Higher level may be appropriate</option><option value="Unable to determine">Unable to determine</option></select></Field>
            <Field label="Cultural diversity - communication"><input value={formData.psychosocial.culturalDiversityCommunication} onChange={(e) => updateField("psychosocial", "culturalDiversityCommunication", e.target.value)} style={styles.input} /></Field>
            <Field label="Cultural diversity - space / environment"><input value={formData.psychosocial.culturalDiversitySpace} onChange={(e) => updateField("psychosocial", "culturalDiversitySpace", e.target.value)} style={styles.input} /></Field>
            <Field label="Cultural diversity - family roles"><input value={formData.psychosocial.culturalDiversityFamilyRole} onChange={(e) => updateField("psychosocial", "culturalDiversityFamilyRole", e.target.value)} style={styles.input} /></Field>
            <Field label="Cultural diversity - traditions"><input value={formData.psychosocial.culturalDiversityTraditions} onChange={(e) => updateField("psychosocial", "culturalDiversityTraditions", e.target.value)} style={styles.input} /></Field>
            <div style={{ ...styles.sectionSubcard, gridColumn: "1 / -1" }}><div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.tealDark, textTransform: "uppercase", marginBottom: 8 }}>Support people</div><div style={getGridStyle(220)}>{formData.psychosocial.supportPersons.map((sp, i) => (<div key={i} style={getGridStyle(180)}><input placeholder="Name" value={sp.name} onChange={(e) => updateSupportPerson(i, "name", e.target.value)} style={styles.input} /><input placeholder="Phone" value={sp.phone} onChange={(e) => updateSupportPerson(i, "phone", e.target.value)} style={styles.input} /><select value={sp.relationship} onChange={(e) => updateSupportPerson(i, "relationship", e.target.value)} style={styles.input}>{SUPPORT_RELATIONSHIP_OPTIONS.map((option) => (<option key={`${i}-${option || "blank"}`} value={option}>{option || "For / relationship"}</option>))}</select></div>))}</div></div>
            <Field label="Spiritual issues / concerns" fullWidth><div style={{ display: "grid", gridTemplateColumns: "minmax(200px, 280px) minmax(0, 1fr)", gap: 12, alignItems: "center" }}><label style={styles.checkboxLabel}><input type="checkbox" checked={formData.psychosocial.spiritualIssuesConcern} onChange={(e) => updateField("psychosocial", "spiritualIssuesConcern", e.target.checked)} />Refer to Spiritual / SCICA assessment</label><input value={formData.psychosocial.spiritualIssuesNote} onChange={(e) => updateField("psychosocial", "spiritualIssuesNote", e.target.value)} style={styles.input} placeholder="Cross-reference note" /></div></Field>
            <Field label="Drug and alcohol history" fullWidth><textarea value={formData.psychosocial.drugAlcoholHistory} onChange={(e) => updateField("psychosocial", "drugAlcoholHistory", e.target.value)} style={styles.textarea} placeholder="Past/current use, treatment history, recovery supports..." /></Field>
            <Field label="Narrative" fullWidth><textarea value={formData.psychosocial.notes} onChange={(e) => updateField("psychosocial", "notes", e.target.value)} style={styles.textarea} placeholder="Living arrangement, caregiver context, and support notes..." /></Field>
          </div>
        </Card>
      );
    }

    if (section.key === "distress") {
      return (
        <Card key={section.key} sectionKey={section.key} title={section.label} subtitle={section.subtitle}>
          <div style={getGridStyle(section.minWidth)}>
            <Field label="Patient response to illness" fullWidth><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 6 }}>{["Cannot respond", "Overwhelmed", "Fearful", "Unaware of condition", "Accepting", "Depressed", "Sad", "Guilt", "Denial", "Angry", "Loss of worth", "Other"].map((option) => (<label key={option} style={styles.checkboxLabel}><input type="checkbox" checked={formData.patientDistress.patientResponse.includes(option)} onChange={() => updateField("patientDistress", "patientResponse", toggleValue(formData.patientDistress.patientResponse, option))} />{option}</label>))}</div></Field>
            <Field label="Patient concerns / possible patient crisis" fullWidth><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 6 }}>{[NONE_IDENTIFIED_OPTION, "Responsibility for others", "Finances", "Lacks cognitive ability", SUICIDE_RISK_OPTION, "Inadequate food/supplies", ABUSE_CONCERN_OPTION, "Substance/alcohol abuse", "Transfer to another setting", "Other"].map((option) => (<label key={option} style={styles.checkboxLabel}><input type="checkbox" checked={formData.patientDistress.patientConcerns.includes(option)} onChange={() => updateField("patientDistress", "patientConcerns", toggleExclusiveValue(formData.patientDistress.patientConcerns, option, NONE_IDENTIFIED_OPTION))} />{option}</label>))}</div></Field>
            <div style={{ ...styles.sectionSubcard, gridColumn: "1 / -1" }}><div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.tealDark, textTransform: "uppercase", marginBottom: 8 }}>Instrumental Activities of Daily Living (IADL)</div>{[{ q: "Phone access & able to make calls?", key: "phoneAccess" },{ q: "Goes out for shopping?", key: "shopping" },{ q: "Prepares own meals?", key: "mealPrep" },{ q: "Does housework?", key: "housework" },{ q: "Manages own finances?", key: "finances" }].map((item) => (<div key={item.key} style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 110px", gap: 8, marginBottom: 6, alignItems: "center" }}><span style={{ fontSize: 12 }}>{item.q}</span><select value={formData.patientDistress.iadl[item.key]} onChange={(e) => updateField("patientDistress", "iadl", { ...formData.patientDistress.iadl, [item.key]: e.target.value })} style={{ ...styles.input, padding: "4px 8px", fontSize: 12 }}><option value="">?</option><option value="Yes">Yes</option><option value="No">No</option></select></div>))}</div>
            <Field label="Patient anxiety rating"><select value={formData.patientDistress.anxietyRating} onChange={(e) => updateField("patientDistress", "anxietyRating", e.target.value)} style={styles.input}><option value="">Select</option><option value="None">None</option><option value="Mild">Mild</option><option value="Moderate">Moderate</option><option value="Severe">Severe</option></select></Field>
            <Field label="Anxiety rated by"><select value={formData.patientDistress.anxietyRatedBy} onChange={(e) => updateField("patientDistress", "anxietyRatedBy", e.target.value)} style={styles.input}><option value="">Select</option><option value="Patient">Patient</option><option value="Clinician">Clinician</option></select></Field>
            <Field label="Distress rating"><select value={formData.patientDistress.distressRating} onChange={(e) => updateField("patientDistress", "distressRating", e.target.value)} style={styles.input}><option value="">Select</option><option value="None">None</option><option value="Mild">Mild</option><option value="Moderate">Moderate</option><option value="Severe">Severe</option></select></Field>
            <Field label="Distress rated by"><select value={formData.patientDistress.distressRatedBy} onChange={(e) => updateField("patientDistress", "distressRatedBy", e.target.value)} style={styles.input}><option value="">Select</option><option value="Patient">Patient</option><option value="Clinician">Clinician</option></select></Field>
            <Field label="Response to previous loss"><input value={formData.patientDistress.responseToPreviousLoss} onChange={(e) => updateField("patientDistress", "responseToPreviousLoss", e.target.value)} style={styles.input} /></Field>
            <Field label="Coping style"><select value={formData.patientDistress.copingStyle} onChange={(e) => updateField("patientDistress", "copingStyle", e.target.value)} style={styles.input}><option value="">Select</option><option value="Problem-focused">Problem-focused</option><option value="Emotion-focused">Emotion-focused</option><option value="Avoidant">Avoidant</option><option value="Mixed">Mixed</option><option value="Other">Other</option></select></Field>
            <Field label="Impact of illness on physical function"><select value={formData.patientDistress.illnessImpactPhysicalFunction} onChange={(e) => updateField("patientDistress", "illnessImpactPhysicalFunction", e.target.value)} style={styles.input}><option value="">Select</option><option value="None">None</option><option value="Mild">Mild</option><option value="Moderate">Moderate</option><option value="Severe">Severe</option></select></Field>
            <Field label="Plan-of-care compliance obstacles"><input value={formData.patientDistress.planOfCareComplianceObstacles} onChange={(e) => updateField("patientDistress", "planOfCareComplianceObstacles", e.target.value)} style={styles.input} /></Field>
            <Field label="Ongoing coping concerns" fullWidth><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 6 }}>{ONGOING_COPING_OPTIONS.map((option) => (<label key={option} style={styles.checkboxLabel}><input type="checkbox" checked={formData.patientDistress.ongoingCopingItems.includes(option)} onChange={() => updateField("patientDistress", "ongoingCopingItems", toggleValue(formData.patientDistress.ongoingCopingItems, option))} />{option}</label>))}</div></Field>
            {suicideRiskSelected ? <div style={{ ...styles.sectionSubcard, gridColumn: "1 / -1" }}><div style={{ fontSize: 11, fontWeight: 700, color: "#b91c1c", textTransform: "uppercase", marginBottom: 8 }}>Suicide Risk - Documented Assessment</div>{!suicideNotificationsComplete ? <div style={{ marginBottom: 10, padding: 8, borderRadius: 8, border: "1px solid #fca5a5", background: "#fef2f2", fontSize: 11, color: "#991b1b" }}>Both notification checkboxes must be completed before the assessment can be locked.</div> : null}<div style={getGridStyle(210)}>{[["Age/sex statistical risk factors present", "ageSexRiskFactorsPresent"],["Early childhood loss", "earlyChildhoodLoss"],["Current alcohol/drug abuse", "currentAlcoholDrugAbuse"],["Recent irreversible loss", "recentIrreversibleLoss"],["Specific suicide plan identified", "specificSuicidePlanIdentified"]].map(([label, key]) => (<div key={key} style={styles.fieldShell}><label style={styles.fieldLabel}>{label}</label><label style={styles.checkboxLabel}><input type="checkbox" checked={!!formData.patientDistress.suicideRisk[key]} onChange={(e) => updateNestedField("patientDistress", "suicideRisk", key, e.target.checked)} />Present</label></div>))}<Field label="Lethality of method"><select value={formData.patientDistress.suicideRisk.lethalityOfMethod} onChange={(e) => updateNestedField("patientDistress", "suicideRisk", "lethalityOfMethod", e.target.value)} style={styles.input}><option value="">Select</option><option value="Low">Low</option><option value="Moderate">Moderate</option><option value="High">High</option></select></Field><Field label="Means availability"><select value={formData.patientDistress.suicideRisk.meansAvailability} onChange={(e) => updateNestedField("patientDistress", "suicideRisk", "meansAvailability", e.target.value)} style={styles.input}><option value="">Select</option><option value="Yes">Yes</option><option value="No">No</option><option value="Unknown">Unknown</option></select></Field>{imminentSuicideRisk ? <div style={styles.fieldShell}><label style={styles.fieldLabel}>Imminent-risk supervision</label><label style={styles.checkboxLabel}><input type="checkbox" checked={formData.patientDistress.suicideRisk.notLeftUnsupervised} onChange={(e) => updateNestedField("patientDistress", "suicideRisk", "notLeftUnsupervised", e.target.checked)} />Patient is not to be left unsupervised</label></div> : null}<div style={styles.fieldShell}><label style={styles.fieldLabel}>Notified - Case Manager / Supervisor</label><label style={styles.checkboxLabel}><input type="checkbox" checked={formData.patientDistress.suicideRisk.notifiedCaseManagerSupervisor} onChange={(e) => { updateNestedField("patientDistress", "suicideRisk", "notifiedCaseManagerSupervisor", e.target.checked); updateNestedField("patientDistress", "suicideRisk", "notifiedCaseManagerSupervisorAt", notificationTimestamp(e.target.checked, formData.patientDistress.suicideRisk.notifiedCaseManagerSupervisorAt)); }} />Confirmed{formData.patientDistress.suicideRisk.notifiedCaseManagerSupervisorAt ? ` ? ${formatTimestampLabel(formData.patientDistress.suicideRisk.notifiedCaseManagerSupervisorAt)}` : ""}</label></div><div style={styles.fieldShell}><label style={styles.fieldLabel}>Notified - Attending Physician</label><label style={styles.checkboxLabel}><input type="checkbox" checked={formData.patientDistress.suicideRisk.notifiedAttendingPhysician} onChange={(e) => { updateNestedField("patientDistress", "suicideRisk", "notifiedAttendingPhysician", e.target.checked); updateNestedField("patientDistress", "suicideRisk", "notifiedAttendingPhysicianAt", notificationTimestamp(e.target.checked, formData.patientDistress.suicideRisk.notifiedAttendingPhysicianAt)); }} />Confirmed{formData.patientDistress.suicideRisk.notifiedAttendingPhysicianAt ? ` ? ${formatTimestampLabel(formData.patientDistress.suicideRisk.notifiedAttendingPhysicianAt)}` : ""}</label></div><Field label="Suicide-risk notes" fullWidth><textarea value={formData.patientDistress.suicideRisk.notes} onChange={(e) => updateNestedField("patientDistress", "suicideRisk", "notes", e.target.value)} style={styles.textarea} placeholder="Document the discussion, interventions, notifications, and referral follow-up..." /></Field></div></div> : null}
            {abuseWorkflowActive ? <div style={{ ...styles.sectionSubcard, gridColumn: "1 / -1" }}><div style={{ fontSize: 11, fontWeight: 700, color: "#92400e", textTransform: "uppercase", marginBottom: 8 }}>Abuse / Neglect / Exploitation workflow</div><div style={getGridStyle(210)}><Field label="Category" fullWidth><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 6 }}>{ABUSE_CATEGORY_OPTIONS.map((option) => (<label key={option} style={styles.checkboxLabel}><input type="checkbox" checked={formData.patientDistress.abuseNeglectExploitation.categories.includes(option)} onChange={() => updateNestedField("patientDistress", "abuseNeglectExploitation", "categories", toggleValue(formData.patientDistress.abuseNeglectExploitation.categories, option))} />{option}</label>))}</div></Field><Field label="Reported to"><select value={formData.patientDistress.abuseNeglectExploitation.reportedTo} onChange={(e) => updateNestedField("patientDistress", "abuseNeglectExploitation", "reportedTo", e.target.value)} style={styles.input}><option value="">Select</option><option value="APS">APS</option><option value="Law Enforcement">Law Enforcement</option><option value="Licensing Board">Licensing Board</option><option value="Not yet reported">Not yet reported</option></select></Field><Field label="Report date"><input type="date" value={formData.patientDistress.abuseNeglectExploitation.reportDate} onChange={(e) => updateNestedField("patientDistress", "abuseNeglectExploitation", "reportDate", e.target.value)} style={styles.input} /></Field><Field label="Report reference / case number"><input value={formData.patientDistress.abuseNeglectExploitation.reportReferenceCaseNumber} onChange={(e) => updateNestedField("patientDistress", "abuseNeglectExploitation", "reportReferenceCaseNumber", e.target.value)} style={styles.input} /></Field><Field label="Reported by"><input value={formData.patientDistress.abuseNeglectExploitation.reportedBy} readOnly style={styles.input} /></Field><Field label="Indicators observed" fullWidth><textarea value={formData.patientDistress.abuseNeglectExploitation.indicatorsObserved} onChange={(e) => updateNestedField("patientDistress", "abuseNeglectExploitation", "indicatorsObserved", e.target.value)} style={styles.textarea} placeholder="What happened, to whom, when, where, and who was responsible..." /></Field></div></div> : null}
            <Field label="Narrative" fullWidth><textarea value={formData.patientDistress.notes} onChange={(e) => updateField("patientDistress", "notes", e.target.value)} style={styles.textarea} placeholder="Patient distress observations..." /></Field>
          </div>
        </Card>
      );
    }

    if (section.key === "familyDistress") {
      return (
        <Card key={section.key} sectionKey={section.key} title={section.label} subtitle={section.subtitle}>
          <div style={getGridStyle(section.minWidth)}>
            <Field label="Family response to illness" fullWidth><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 6 }}>{["Accepting", "Depressed", "Sad", "Guilt", "Denial", "Angry", "Fearful", "Despair", "Overwhelmed", "Anticipatory grieving", "Other"].map((option) => (<label key={option} style={styles.checkboxLabel}><input type="checkbox" checked={formData.familyDistress.familyResponse.includes(option)} onChange={() => updateField("familyDistress", "familyResponse", toggleValue(formData.familyDistress.familyResponse, option))} />{option}</label>))}</div></Field>
            <Field label="Ability to provide care"><select value={formData.familyDistress.abilityToProvideCare} onChange={(e) => updateField("familyDistress", "abilityToProvideCare", e.target.value)} style={styles.input}><option value="">Select</option><option value="Good">Good</option><option value="Fair">Fair</option><option value="Poor">Poor</option><option value="Unable">Unable</option></select></Field>
            <Field label="Willingness to provide care"><select value={formData.familyDistress.willingnessToProvideCare} onChange={(e) => updateField("familyDistress", "willingnessToProvideCare", e.target.value)} style={styles.input}><option value="">Select</option><option value="Good">Good</option><option value="Fair">Fair</option><option value="Poor">Poor</option><option value="Unwilling">Unwilling</option></select></Field>
            <Field label="PCG / family anxiety rating"><select value={formData.familyDistress.pcgAnxietyRating} onChange={(e) => updateField("familyDistress", "pcgAnxietyRating", e.target.value)} style={styles.input}><option value="">Select</option><option value="None">None</option><option value="Mild">Mild</option><option value="Moderate">Moderate</option><option value="Severe">Severe</option></select></Field>
            <Field label="PCG anxiety rated by"><select value={formData.familyDistress.pcgAnxietyRatedBy} onChange={(e) => updateField("familyDistress", "pcgAnxietyRatedBy", e.target.value)} style={styles.input}><option value="">Select</option><option value="Patient">Patient</option><option value="Clinician">Clinician</option></select></Field>
            <Field label="Family crisis" fullWidth><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 6 }}>{["None", SUICIDE_RISK_OPTION, "Inadequate food/supplies", "Financial/legal crisis", "Significant losses in recent past", "Substance/alcohol abuse", "Other"].map((option) => (<label key={option} style={styles.checkboxLabel}><input type="checkbox" checked={formData.familyDistress.familyCrisis.includes(option)} onChange={() => updateField("familyDistress", "familyCrisis", toggleValue(formData.familyDistress.familyCrisis, option))} />{option}</label>))}</div></Field>
            <Field label="Narrative" fullWidth><textarea value={formData.familyDistress.notes} onChange={(e) => updateField("familyDistress", "notes", e.target.value)} style={styles.textarea} placeholder="Family's response to patient's decline..." /></Field>
          </div>
        </Card>
      );
    }

    if (section.key === "financial") {
      const directiveRows = [{ label: "Living Will", key: "livingWill", copyKey: "livingWillCopy", helpKey: "livingWillNeedHelp" }, { label: "Health POA", key: "healthPOA", copyKey: "healthPOACopy", helpKey: "healthPOANeedHelp" }, { label: "Health Proxy", key: "healthProxy", copyKey: "healthProxyCopy", helpKey: "healthProxyNeedHelp" }, { label: "Burial plans", key: "burialPlans", copyKey: null, helpKey: "burialPlansNeedHelp" }];
      return (
        <Card key={section.key} sectionKey={section.key} title={section.label} subtitle={section.subtitle}>
          <div style={getGridStyle(section.minWidth)}>
            <Field label="All needs met by patient/family?"><select value={formData.financialLegal.allNeedsMet} onChange={(e) => updateField("financialLegal", "allNeedsMet", e.target.value)} style={styles.input}><option value="">Select</option><option value="Yes">Yes</option><option value="No">No</option></select></Field>
            <Field label="Is patient/spouse a veteran?"><select value={formData.financialLegal.isVeteran} onChange={(e) => updateField("financialLegal", "isVeteran", e.target.value)} style={styles.input}><option value="">Select</option><option value="No">No</option><option value="Yes">Yes</option></select></Field>
            <Field label="Patient care paid by"><select value={formData.financialLegal.carePaidBy} onChange={(e) => updateField("financialLegal", "carePaidBy", e.target.value)} style={styles.input}><option value="">Select</option><option value="Private pay">Private pay</option><option value="Indigent-non-funded charity">Indigent-non-funded charity</option><option value="Insufficient reserves-may be Medicaid eligible">Insufficient reserves-may be Medicaid eligible</option></select></Field>
            <Field label="Financial assessment follow-up"><input value={formData.financialLegal.financialAssessmentNote} onChange={(e) => updateField("financialLegal", "financialAssessmentNote", e.target.value)} style={styles.input} placeholder="If applicable, complete Financial Assessment" /></Field>
            {formData.financialLegal.allNeedsMet === "No" ? <><Field label="Patient lacks" fullWidth><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 6 }}>{["Food", "Utility", "Clothing", "Furniture", "Med/supplies unrelated to illness"].map((option) => (<label key={option} style={styles.checkboxLabel}><input type="checkbox" checked={formData.financialLegal.patientLacks.includes(option)} onChange={() => updateField("financialLegal", "patientLacks", toggleValue(formData.financialLegal.patientLacks, option))} />{option}</label>))}</div></Field><Field label="Needs assistance with" fullWidth><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 6 }}>{["Meals on wheels", "Food stamps", "Other"].map((option) => (<label key={option} style={styles.checkboxLabel}><input type="checkbox" checked={formData.financialLegal.needsAssistance.includes(option)} onChange={() => updateField("financialLegal", "needsAssistance", toggleValue(formData.financialLegal.needsAssistance, option))} />{option}</label>))}</div></Field></> : null}
            <div style={{ ...styles.sectionSubcard, gridColumn: "1 / -1" }}><div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.tealDark, textTransform: "uppercase", marginBottom: 8 }}>Planning / Advance Directives</div>{directiveRows.map((item) => (<div key={item.key} style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 90px 110px 160px", gap: 8, marginBottom: 6, alignItems: "center" }}><span style={{ fontSize: 12 }}>{item.label}</span><select value={formData.financialLegal[item.key]} onChange={(e) => updateField("financialLegal", item.key, e.target.value)} style={{ ...styles.input, padding: "4px 6px", fontSize: 11 }}><option value="">?</option><option value="Yes">Yes</option><option value="No">No</option><option value="N/A">N/A</option></select>{item.copyKey ? <select value={formData.financialLegal[item.copyKey]} onChange={(e) => updateField("financialLegal", item.copyKey, e.target.value)} style={{ ...styles.input, padding: "4px 6px", fontSize: 10 }}><option value="">Copy: ?</option><option value="Yes">Copy: Yes</option><option value="No">Copy: No</option><option value="N/A">Copy: N/A</option></select> : <div />}{<select value={formData.financialLegal[item.helpKey]} onChange={(e) => updateField("financialLegal", item.helpKey, e.target.value)} style={{ ...styles.input, padding: "4px 6px", fontSize: 10 }}><option value="">Need help: ?</option><option value="No help needed">No help needed</option><option value="Needs referral">Needs referral</option><option value="Referral made">Referral made</option></select>}</div>))}</div>
            <div style={{ ...styles.sectionSubcard, gridColumn: "1 / -1" }}><div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.tealDark, textTransform: "uppercase", marginBottom: 8 }}>Mortuary information</div><div style={getGridStyle(180)}><Field label="Mortuary name"><input value={formData.financialLegal.mortuaryName} onChange={(e) => updateField("financialLegal", "mortuaryName", e.target.value)} style={styles.input} /></Field><Field label="Phone"><input value={formData.financialLegal.mortuaryPhone} onChange={(e) => updateField("financialLegal", "mortuaryPhone", e.target.value)} style={styles.input} /></Field><Field label="Address"><input value={formData.financialLegal.mortuaryAddress} onChange={(e) => updateField("financialLegal", "mortuaryAddress", e.target.value)} style={styles.input} /></Field><Field label="City"><input value={formData.financialLegal.mortuaryCity} onChange={(e) => updateField("financialLegal", "mortuaryCity", e.target.value)} style={styles.input} /></Field><Field label="State"><input value={formData.financialLegal.mortuaryState} onChange={(e) => updateField("financialLegal", "mortuaryState", e.target.value)} style={styles.input} /></Field><Field label="Zip"><input value={formData.financialLegal.mortuaryZip} onChange={(e) => updateField("financialLegal", "mortuaryZip", e.target.value)} style={styles.input} /></Field></div></div>
            <Field label="Narrative" fullWidth><textarea value={formData.financialLegal.notes} onChange={(e) => updateField("financialLegal", "notes", e.target.value)} style={styles.textarea} placeholder="Financial/legal planning notes..." /></Field>
          </div>
        </Card>
      );
    }

    if (section.key === "referrals") {
      return (
        <Card key={section.key} sectionKey={section.key} title={section.label} subtitle={section.subtitle}>
          <div style={getGridStyle(section.minWidth)}>
            <Field label="Need for community program referral?"><select value={formData.referrals.communityProgram} onChange={(e) => updateField("referrals", "communityProgram", e.target.value)} style={styles.input}><option value="">Select</option><option value="N/A">N/A</option><option value="Yes">Yes</option><option value="No">No</option></select></Field>
            <Field label="Community referral accepted?"><select value={formData.referrals.communityAccepted} onChange={(e) => updateField("referrals", "communityAccepted", e.target.value)} style={styles.input}><option value="">Select</option><option value="N/A">N/A</option><option value="Yes">Yes</option><option value="No">No</option></select></Field>
            <Field label="Response / satisfaction with referral made"><select value={formData.referrals.communityReferralSatisfaction} onChange={(e) => updateField("referrals", "communityReferralSatisfaction", e.target.value)} style={styles.input}><option value="">Select</option><option value="Pending follow-up">Pending follow-up</option><option value="Satisfied">Satisfied</option><option value="Partially satisfied">Partially satisfied</option><option value="Not satisfied">Not satisfied</option></select></Field>
            <Field label="Therapy" fullWidth><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 6 }}>{["Music", "Art", "Pet", "Massage"].map((option) => (<label key={option} style={styles.checkboxLabel}><input type="checkbox" checked={formData.referrals.therapy.includes(option)} onChange={() => updateField("referrals", "therapy", toggleValue(formData.referrals.therapy, option))} />{option}</label>))}</div></Field>
            <Field label="Volunteer services" fullWidth><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 6 }}>{["Companionship", "Errands", "Respite", "Light housekeeping/meals"].map((option) => (<label key={option} style={styles.checkboxLabel}><input type="checkbox" checked={formData.referrals.volunteerServices.includes(option)} onChange={() => updateField("referrals", "volunteerServices", toggleValue(formData.referrals.volunteerServices, option))} />{option}</label>))}</div></Field>
            <Field label="Referral notes" fullWidth><textarea value={formData.referrals.notes} onChange={(e) => updateField("referrals", "notes", e.target.value)} style={styles.textarea} placeholder="Referral follow-up, response, and satisfaction notes..." /></Field>
          </div>
        </Card>
      );
    }

    if (section.key === "narrative") {
      return (
        <Card key={section.key} sectionKey={section.key} title={section.label} subtitle={section.subtitle}>
          <div style={getGridStyle(section.minWidth)}>
            <Field label="Care provided" fullWidth>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 6 }}>
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
            <Field label="Narrative" fullWidth>
              <textarea
                value={formData.narrative.notes}
                onChange={(e) => updateField("narrative", "notes", e.target.value)}
                style={{ ...styles.textarea, minHeight: 140 }}
                placeholder="Visit summary and interventions..."
              />
            </Field>
          </div>
        </Card>
      );
    }

    return (
      <Card key={section.key} sectionKey={section.key} title={section.label} subtitle={section.subtitle}>
        <div style={getGridStyle(section.minWidth)}>
          <Field label="Staff title"><input value={formData.finalization.staff_title} onChange={(e) => updateField("finalization", "staff_title", e.target.value)} style={styles.input} /></Field>
          <Field label="Clinician name"><input value={formData.finalization.clinician_name} readOnly style={styles.input} /></Field>
          <Field label="Signature date"><input type="date" value={formData.finalization.signature_date} onChange={(e) => updateField("finalization", "signature_date", e.target.value)} style={styles.input} /></Field>
          <div style={{ ...styles.sectionSubcard, gridColumn: "1 / -1", marginTop: 0 }}><div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.tealDark, textTransform: "uppercase", marginBottom: 8 }}>PCG / Patient acknowledgement</div><div style={getGridStyle(200)}><div style={styles.fieldShell}><label style={styles.fieldLabel}>Acknowledgement</label><label style={styles.checkboxLabel}><input type="checkbox" checked={formData.finalization.patient_acknowledgement} onChange={(e) => updateField("finalization", "patient_acknowledgement", e.target.checked)} />Signature of patient / PCG to acknowledge visit</label></div><Field label="Name"><input value={formData.finalization.patient_signature_name} onChange={(e) => updateField("finalization", "patient_signature_name", e.target.value)} style={styles.input} /></Field><Field label="Relationship"><input value={formData.finalization.patient_signature_relationship} onChange={(e) => updateField("finalization", "patient_signature_relationship", e.target.value)} style={styles.input} /></Field></div></div>
          <div style={{ ...styles.sectionSubcard, gridColumn: "1 / -1", marginBottom: 8 }}><div style={{ fontSize: 11, fontWeight: 700, color: CLINICAL_BRAND.tealDark, textTransform: "uppercase", marginBottom: 8 }}>QA review</div><div style={getGridStyle(200)}><Field label="Reviewed by"><input value={formData.finalization.countersign_staff_name} readOnly style={styles.input} /></Field><Field label="Review date"><input type="date" value={formData.finalization.countersign_signature_date} onChange={(e) => updateField("finalization", "countersign_signature_date", e.target.value)} style={styles.input} /></Field><div style={styles.fieldShell}><label style={styles.fieldLabel}>Approval</label><label style={styles.checkboxLabel}><input type="checkbox" checked={formData.finalization.countersign_required} onChange={(e) => updateField("finalization", "countersign_required", e.target.checked)} />QA review approved</label></div></div></div>
          {lockBlockedReason ? <div style={{ ...styles.alert, margin: 0, gridColumn: "1 / -1" }}>{lockBlockedReason}</div> : null}
          <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap", marginTop: 6 }}><label style={styles.checkboxLabel}><input type="checkbox" checked={formData.finalization.assessment_complete} onChange={(e) => updateField("finalization", "assessment_complete", e.target.checked)} />Assessment complete</label><button type="button" onClick={handleLock} style={styles.button} disabled={!assessmentId || locked || !!lockBlockedReason || saving}>{locked ? "Locked" : "Lock Assessment"}</button></div>
        </div>
      </Card>
    );
  });

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
              <div style={styles.sectionStack}>
                {renderAllSections()}

                <section style={styles.sectionCard}>
                  <div style={{ ...styles.sectionHeader, cursor: "default" }}>
                    <div>
                      <div style={styles.sectionTitle}>MSW ICA Intelligence</div>
                      <div style={styles.sectionHint}>Evaluating social-risk signals</div>
                    </div>
                  </div>
                  <div style={styles.sectionBody}>
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
                  </div>
                </section>

                <div style={styles.footer}>
                  <div style={{ fontSize: 11, color: CLINICAL_BRAND.muted, fontWeight: 700 }}>
                    {locked ? "LOCKED" : "IN PROGRESS"} · {summaryCount} completed field(s)
                  </div>
                  <div style={{ display: "flex", gap: 10 }}>
                    <button type="button" style={styles.button} onClick={handleSave} disabled={saving || locked}>
                      {saving ? "Saving..." : saveButtonLabel}
                    </button>
                    {assessmentId && !locked ? (
                      <button type="button" style={{ ...styles.button, background: "#fee2e2" }} onClick={handleLock} disabled={saving || !!lockBlockedReason}>
                        Lock Assessment
                      </button>
                    ) : null}
                  </div>
                </div>

                {saveStatus === "saved" && <div style={{ marginTop: 10, fontSize: 12, color: "#166534" }}>MSW ICA saved successfully.</div>}
                {saveStatus === "error" && <div style={{ marginTop: 10, fontSize: 12, color: "#92400e" }}>MSW ICA save failed — please try again.</div>}
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
