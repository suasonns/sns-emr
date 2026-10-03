/**
 * RNICA.jsx — RN Initial Comprehensive Assessment
 * SNS Hospice Solutions EMR System
 *
 * 28-Module Single-File React Component
 * Frontend field-test candidate — backend integration via 4 API endpoints
 *
 * Modules: demographics, vitals, pain, symptomImpact, diagnoses, performanceStatus,
 *          neurological, cardiovascular, respiratory, infection, gastrointestinal,
 *          nutrition, endocrine, genitourinary, musculoskeletal, skin, imminentDeath,
 *          sfv, safety, psychosocial, spiritual, bereavement, personalCare,
 *          teachingNeeds, admissionsOrder, referrals, finalization
 *
 * Color System: HOPE = GREEN (#059669), SFV = RED (#DC2626), CMS = BLUE (#2563EB)
 * Accent: Teal (#0D9488)
 */

import React, { useState, useCallback, useMemo, useEffect, useContext, useRef } from "react";
import { useNavigate } from "react-router-dom";
import frontBody from "../assets/body-map/front.png";
import backBody from "../assets/body-map/back.png";
import {
  RNICA_BODY_SYSTEM_MODULES,
  RNICA_BODY_SYSTEM_SIDEBAR_ITEMS,
} from "../config/bodySystems";
import AdmissionActionCenterDrawer, {
  AdmissionActionCenterButton,
} from "./AdmissionActionCenterDrawer";
import {
  RNICA_ASSESSMENT_MODULES,
  validateBodyMapRegions,
} from "./rn-ica/rnIcaClinicalNavigation";
import { LANGUAGE_OPTIONS, ETHNICITY_OPTIONS, RACE_OPTIONS } from "./rn-ica/hope-admin-review/HopeAdministrativeReview";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "./ui/select";
import { Checkbox } from "./ui/checkbox";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";
import { Card as ShadcnCard, CardHeader as ShadcnCardHeader, CardTitle as ShadcnCardTitle, CardContent as ShadcnCardContent } from "./ui/card";
import { Badge as ShadcnBadge } from "./ui/badge";
import { Progress as ShadcnProgress } from "./ui/progress";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "./ui/accordion";
import { Input as ShadcnInput } from "./ui/input";
import { Textarea as ShadcnTextarea } from "./ui/textarea";
import { ToggleGroup, ToggleGroupItem } from "./ui/toggle-group";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "./ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from "./ui/sheet";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./ui/tabs";
import { Alert, AlertTitle, AlertDescription } from "./ui/alert";
import { fetchPatientSummary } from "../api/patientCharts";
import { fetchCensusWorkspace } from "../api/census";
import { listSfvRequirements } from "../api/sfv";
import {
  saveRnicaAssessmentOffline,
  updateRnicaAssessmentOffline,
} from "../api/offlineAssessmentApi";
import {
  reviewHarvestedSignalOffline,
  batchReviewHarvestedSignalsOffline,
} from "../api/offlineSignalReviewApi";
import {
  saveRnicaAssessment,
  getRnicaAssessment,
  getRnicaAssessmentByPatient,
  getRnicaAssessmentByPatientType,
  updateRnicaAssessment,
  lockRnicaAssessment,
  deleteRnicaAssessment,
  getRnicaIntelligence,
  viewRnicaSectionPoc,
  addRnicaSectionPocProblem,
  updateRnicaSectionPocProblem,
  resolveRnicaSectionPocProblem,
  viewRnicaAllPoc,
  deactivateRnicaSectionPocProblem,
  getRnicaFinalizationReadiness,
  requestRnicaCorrection,
  listRnicaAmendments,
  approveRnicaAmendment,
  denyRnicaAmendment,
  getRnicaSectionPocProblemHistory,
  linkExistingRnicaSectionPocProblem,
  mergeRnicaPocDuplicateProblems,
  getStructuredFindingsAnalytics,
  getRnProductivityMetrics,
} from "../api/icaAssessments";
import { applyStructuredFindings, applyAllNonConflicting, getPendingFindingTargetSections } from "./rn-ica/applyStructuredFindings";
import { CONCEPT_REGISTRY } from "./rn-ica/structuredFindingRegistry.generated";
import { detectLCD, evaluateLCD, getLCDConfig } from "../api/eligibility";
import {
  listAideVisitsForPatient,
  getChhaVisitOutcome,
  upsertChhaVisitOutcome,
} from "../api/chhaVisits";
import { createVisitNote, listAssignableStaff } from "../api/visitNotes";
import {
  listCcHourlyNarrativeEntries,
  createCcHourlyNarrativeEntry,
  deleteCcHourlyNarrativeEntry,
} from "../api/ccHourlyNarrative";
import {
  checkMedicationSafety,
  listMedications,
  addMedication,
  discontinueMedication,
  listPatientAllergies,
  addPatientAllergy,
  removePatientAllergy,
} from "../api/medications";
import {
  listOrderTemplates,
  importOrderTemplate,
  getLabCatalog,
  sendFax,
  getFaxHistory,
} from "../api/ordersHub";
import {
  listPhysicianOrders,
  createPhysicianOrder,
  submitPhysicianOrder,
  approvePhysicianOrder,
  executePhysicianOrder,
  cancelPhysicianOrder,
  ORDER_SIGNER_ROLES,
  getPhysicianOrderStatusTone,
  formatPhysicianOrderStatusLabel,
} from "../api/physicianOrders";
import { getCurrentUser } from "../api/session";
import { fetchFacesheet, fetchPerformanceHistory } from "../api/facesheet";
import { listVendors } from "../api/vendors";
import { listStaff } from "../api/staff";
import { COLORS as SNS_COLORS, S as SNS_S } from "../tenant/design";
import PatientContextSidebar from "./PatientContextSidebar";
import NumericPainScale from "../assessments/pain/NumericPainScale";
import PAINADScale from "../assessments/pain/PAINADScale";
import FLACCScale from "../assessments/pain/FLACCScale";
import { useThemeMode } from "../theme/theme";
import { getChartColors } from "../theme/chartColors";
import AssessmentTypeToggle from "./AssessmentTypeToggle";
import { useAssessmentAutosave } from "../hooks/useAssessmentAutosave";
import { getSfvStatus, getHopeAdmissionStatus } from "../intake/hopeReportMapper";
import { resolveReferralRecommendation } from "../intake/referralRecommendation";
import {
  buildClinicalNarrative,
  DISEASE_TRAJECTORY_OPTIONS,
  isLegacyDiseaseTrajectoryValue,
  getDiseaseTrajectoryLabel,
} from "../intake/clinicalNarrativeBuilder";

import { getActivePatientId, setActivePatientId, clearActivePatientId } from "../utils/activePatient";
import { formatIcd10Code } from "../utils/formatIcd10";
import MedicationNameInput from "./MedicationNameInput";
import Icd10DiagnosisInput from "./Icd10DiagnosisInput";
import VisitRecorderCard from "./VisitRecorderCard";
import RNICACommandWorkspace from "./rn-ica/RNICACommandWorkspace";
// getRnicaColors/getRnicaStyles live in ../theme/clinicalDesign — the single shared
// design system used by every clinical page (RNICA, CHHA, MSW ICA, SC ICA, ...).
// Re-exported here for backward compatibility with existing imports of this module.
import { getRnicaColors, getRnicaStyles } from "../theme/clinicalDesign";
export { getRnicaColors, getRnicaStyles };
// ════════════════════════════════════════════════════════════════
// 1. CONSTANTS & CONFIGURATION
// ════════════════════════════════════════════════════════════════

const API_BASE = "/visits/rnica";

// HOPE J2051 A-H checklist for the right-panel SFV Status tracker — lets
// the RN see at a glance which Symptom Impact items are still blank while
// documenting manually (whether by hand in Symptom Impact, or auto-derived
// from Pain/Respiratory/GI/Neuro elsewhere in the same RNICA).
const SYMPTOM_IMPACT_CHECKLIST = [
  { key: "pain", label: "A. Pain" },
  { key: "shortnessOfBreath", label: "B. Shortness of Breath" },
  { key: "anxiety", label: "C. Anxiety" },
  { key: "nausea", label: "D. Nausea" },
  { key: "vomiting", label: "E. Vomiting" },
  { key: "diarrhea", label: "F. Diarrhea" },
  { key: "constipation", label: "G. Constipation" },
  { key: "agitation", label: "H. Agitation" },
];
const SYMPTOM_SEVERITY_LABEL = { "0": "None", "1": "Mild", "2": "Moderate", "3": "Severe" };

const AssessmentModeContext = React.createContext("ica");

const NAV_SECTIONS = [
  "Patient Demographics", "Vitals", "Pain Assessment", "Symptom Impact",
  "Diagnoses", "Performance Status", ...RNICA_BODY_SYSTEM_MODULES.map((module) => module.label),
  "Imminent Death", "SFV",
  "Safety", "Psychosocial", "Spiritual", "Bereavement",
  "Personal Care", "Teaching Needs", "Admissions Order",
  "Referrals", "Finalization",
];

const LEGACY_ROUTES = [
  { key: "demographics",      nav: "Patient Demographics",  formSection: "demographics" },
  { key: "vitals",            nav: "Vitals",                formSection: "vitals" },
  { key: "pain",              nav: "Pain Assessment",       formSection: "pain" },
  { key: "symptomImpact",     nav: "Symptom Impact",        formSection: "symptomImpact" },
  { key: "diagnoses",         nav: "Diagnoses",             formSection: "diagnoses" },
  { key: "performanceStatus", nav: "Performance Status",    formSection: "performanceStatus" },
  ...RNICA_BODY_SYSTEM_MODULES.map((module) => ({ key: module.key, nav: module.label, formSection: module.formSection })),
  { key: "imminentDeath",     nav: "Imminent Death",        formSection: "imminentDeath" },
  { key: "sfv",               nav: "SFV",                   formSection: "sfv" },
  { key: "safety",            nav: "Safety",                formSection: "safety" },
  { key: "psychosocial",      nav: "Psychosocial",          formSection: "psychosocial" },
  { key: "spiritual",         nav: "Spiritual",             formSection: "spiritual" },
  { key: "bereavement",       nav: "Bereavement",           formSection: "bereavement" },
  { key: "personalCare",      nav: "Personal Care",         formSection: "personalCare" },
  { key: "teachingNeeds",     nav: "Teaching Needs",        formSection: "teachingNeeds" },
  { key: "admissionsOrder",   nav: "Admissions Order",      formSection: "admissionsOrder",
    subFields: ["levelOfCare","visitFrequency","haAssignment","initialPocIdg","nonCoveredItems"] },
  { key: "referrals",         nav: "Referrals",             formSection: "referrals" },
  { key: "finalization",      nav: "Finalization",          formSection: "finalization" },
];

const PILOT_ROUTES = RNICA_ASSESSMENT_MODULES.map((module) => ({
  ...module,
  nav: module.label,
}));

export const SIDEBAR_CONFIG = [
  { key: "demographics",      label: "Patient Demographics",  icon: "👤", hope: ["A1110","A1005","A1010"], color: "green" },
  { key: "assessment",        label: "Assessment",           icon: "📁", hope: [],                         color: null },
  { key: "caregiverAssessment", label: "Caregiver Assessment", icon: "🧑‍⚕️", hope: [], color: null, parent: "demographics", scrollTarget: "pcg", cdphRequired: true },
  { key: "advancedCarePlanning", label: "Advanced Care Planning", icon: "📜", hope: ["F2000","F2100","F2200"], color: "green", parent: "demographics", scrollTarget: "advancedCarePlanning", cdphRequired: true },
  { key: "vitals",            label: "Vitals",                icon: "🩺", hope: [],                        color: null },
  { key: "pain",              label: "Pain Assessment",       icon: "⚡",    hope: ["J0900","J0915"],          color: "green", sfv: true },
  { key: "symptomImpact",     label: "Symptom Impact",        icon: "📊", hope: ["J2051"],                  color: "red" },
  { key: "diagnoses",         label: "Diagnoses",             icon: "🔬", hope: ["I0010","J0050"],          color: "green" },
  // P3-016 (RNICA_PHASE3_REMEDIATION_REGISTER.md): M1190 is a Skin item
  // (form_registry.py HOPE_SKIN_ITEM_CODES; hopeReportMapper.js:625 emits
  // it from skin.skinConditionsPresent). It does not belong to Performance
  // Status — declaring it here made the Performance Status sidebar
  // complete/incomplete indicator flip based on unrelated Skin data. Skin's
  // own sidebar entry (bodySystems.js "skin" system) is the sole declarer.
  { key: "performanceStatus", label: "Performance Status",    icon: "📈", hope: [],                         color: "green" },
  ...RNICA_BODY_SYSTEM_SIDEBAR_ITEMS,
  { key: "imminentDeath",     label: "Imminent Death",        icon: "⏳",    hope: ["J0050"],                  color: "green" },
  { key: "sfv",               label: "SFV",                   icon: "🔴", hope: ["J2050","J2052","J2053"],  color: "red" },
  { key: "safety",            label: "Safety",                icon: "🛡️", hope: [],                   color: null },
  { key: "nursing-assessment", label: "Nursing",            icon: "🩺", hope: [],                         color: null, parent: "assessment", scrollTarget: "vitals" },
  { key: "psychosocial",      label: "Psychosocial",          icon: "💬", hope: [],                         color: null, parent: "assessment", scrollTarget: "psychosocial" },
  { key: "spiritual",         label: "Spiritual",             icon: "🕊️", hope: [],                   color: null, parent: "assessment", scrollTarget: "spiritual" },
  { key: "bereavement",       label: "Bereavement",           icon: "💐", hope: [],                         color: null },
  { key: "personalCare",      label: "Personal Care",         icon: "🤝", hope: [],                         color: null },
  { key: "teachingNeeds",     label: "Teaching Needs",        icon: "📚", hope: [],                         color: null },
  { key: "admissionsOrder",   label: "Admissions Order",      icon: "📝", hope: [],                         color: "blue",
    subFields: ["levelOfCare","visitFrequency","haAssignment","initialPocIdg","nonCoveredItems"],
    features: ["verbalOrderReadBack","locSelection","disciplineFrequency"] },
  { key: "referrals",         label: "Referrals",             icon: "🔗", hope: [],                         color: null },
  { key: "finalization",      label: "Finalization",          icon: "✅",    hope: ["F2000","F2100","F2200"],   color: "green" },
];

// Maps a Section 12 finalization readiness check key (see
// rnica_finalization_service.py) to the RN ICA section the nurse should be
// navigated to in order to resolve it. Checks without an obvious single
// section (e.g. POC completeness, which spans every section's "Add to POC"
// actions) are intentionally omitted here.
const FINALIZATION_CHECK_SECTION_MAP = {
  attestation: "finalization",
  signature: "finalization",
  narrativeReviewed: "diagnoses",
  lcdBaseline: "diagnoses",
  referralsReviewed: "referrals",
  chhaPocCompleted: "admissionsOrder",
};


const FORM_REGISTRY = [
  "demographics", "vitals", "pain", "symptomImpact", "diagnoses",
  "performanceStatus", "neurological", "cardiovascular", "respiratory",
  "infection", "gastrointestinal", "nutrition", "endocrine", "genitourinary",
  "musculoskeletal", "skin", "imminentDeath", "sfv", "safety",
  "psychosocial", "spiritual", "bereavement", "personalCare", "teachingNeeds",
  "admissionsOrder", "referrals", "finalization",
];

const UPDATE_HIDDEN_ROUTE_KEYS = new Set(["admissionsOrder", "sfv"]);
const UPDATE_HIDDEN_SIDEBAR_KEYS = new Set(["advancedCarePlanning", "admissionsOrder", "sfv"]);

// ════════════════════════════════════════════════════════════════
// SECTION 9 — DME per-item status tracker.
//
// Per SNS_RNICA_MASTER_MAP_1.1.md SECTION 9, each DME item must carry
// its own status (Has / Needs / Ordered / Delivered / Declined / N/A)
// rather than a single flat "needed" checkbox, since a hospice must be
// able to distinguish equipment the patient already has from equipment
// that has been ordered but not yet delivered, or declined.
// ════════════════════════════════════════════════════════════════
const DME_ITEM_LIST = [
  "Air mattress", "Bed", "Bedpan", "Egg crate", "Overbed table", "Cane",
  "Walker", "Wheelchair", "Shower chair", "Geri-chair/recliner", "Hoyer lift",
  "Urinal", "Commode", "Nebulizer", "Suction machine", "Oxygen concentrator", "E-tank", "Other",
];

// Default education topics for Teaching Needs
const DEFAULT_EDUCATION_TOPICS = [
  "Disease process and prognosis", "Medication management", "Pain management",
  "Symptom management", "Safety and fall prevention", "Infection control/hand hygiene",
  "Skin care and positioning", "Nutrition and hydration", "Emergency procedures",
  "When to call hospice", "Advance directives", "Hospice philosophy and services",
  "Equipment use and care", "Caregiver self-care",
  "Signs and symptoms of approaching death", "Grief and bereavement resources",
];

// Every discipline that may need an ordered visit frequency — not just the
// core hospice team. PT/OT/ST, dietitian, podiatry, chaplain/volunteer, etc.
// can all be added as-needed via the "+ Add Discipline" control below; this
// list is the full picklist, not a fixed set of rows.
const VISIT_FREQUENCY_DISCIPLINE_OPTIONS = [
  { value: "RN", label: "RN — Registered Nurse" },
  { value: "RN-SUP", label: "RN — Supervisory Visit" },
  { value: "LVN", label: "LVN/LPN — Licensed Vocational/Practical Nurse" },
  { value: "HA", label: "HA — Home Health Aide" },
  { value: "SC", label: "SC — Spiritual Counselor / Chaplain" },
  { value: "MSW", label: "MSW — Medical Social Worker" },
  { value: "BSW", label: "BSW — Bachelor Social Worker" },
  { value: "LCSW", label: "LCSW — Licensed Clinical Social Worker" },
  { value: "LSW", label: "LSW — Licensed Social Worker" },
  { value: "VOL", label: "VOL — Volunteer" },
  { value: "MD", label: "MD — Physician" },
  { value: "DO", label: "DO — Osteopathic Physician" },
  { value: "NP", label: "NP — Nurse Practitioner" },
  { value: "SN", label: "SN — Skilled Nursing" },
  { value: "PT", label: "PT — Physical Therapist" },
  { value: "OT", label: "OT — Occupational Therapist" },
  { value: "ST", label: "ST — Speech Therapist" },
  { value: "Dietitian", label: "Dietitian" },
  { value: "Podiatry", label: "Podiatry" },
  { value: "Pharm.D", label: "Pharm.D — Pharmacist" },
  { value: "BC", label: "BC — Bereavement Coordinator" },
];

const VISIT_FREQUENCY_COUNT_OPTIONS = Array.from({ length: 10 }, (_, i) => String(i + 1));

const VISIT_FREQUENCY_PERIOD_OPTIONS = [
  "As Needed", "Recert", "As needed and Recert", "One-time then PRN", "1 PRN",
  "per Week", "per Week + 1 PRN Visits", "per Week +2 PRN Visits", "per Week +3 PRN Visits",
  "per 2 Week + 1 PRN Visits", "per 2 Week +2 PRN Visits", "per 2 Week +3 PRN Visits",
  "per Month", "per Month + 1 PRN Visits", "per Month +2 PRN Visits", "per Month +3 PRN Visits",
  "every 14 days", "Declined", "Daily until further orders", "Face-to-Face",
];

// Default visit frequency rows for Admissions Order — the core hospice IDG
// disciplines are pre-populated; any other discipline the patient needs
// (PT/OT/ST, dietitian, podiatry, an upcoming F2F, etc.) is added on demand
// via "+ Add Discipline" in DisciplineFrequencyOfVisitCard.
const DEFAULT_VISIT_DISCIPLINES = [
  { discipline: "SN", numberOfVisits: "", period: "", specify: "" },
  { discipline: "HA", numberOfVisits: "", period: "", specify: "" },
  { discipline: "MSW", numberOfVisits: "", period: "", specify: "" },
  { discipline: "SC", numberOfVisits: "", period: "", specify: "" },
  { discipline: "RN-SUP", numberOfVisits: "", period: "", specify: "" },
];

// ─── Visit meta options (logistics/payroll tracking, shared across all ICA/visit forms) ───
const CARE_LEVEL_OPTIONS = ["Routine Care", "General Inpatient", "Continuous Care", "Respite Care"];
const REASON_FOR_VISIT_OPTIONS = [
  "Initial Comprehensive Assessment",
  "Recertification",
  "Follow-up / Routine Visit",
  "Update/Revision",
  "Bereavement Support",
  "Crisis Intervention",
  "Discharge/Transfer",
  "Other",
];
const CHHA_REASON_FOR_VISIT_OPTIONS = ["Follow-up", "Routine", "CC"];

// ════════════════════════════════════════════════════════════════
// 2. INITIAL_FORM — Complete State Shape (28 sections)
// ════════════════════════════════════════════════════════════════

const INITIAL_FORM = {
  // ─── VISIT META — Logistics/payroll tracking (correction, type, reason, time in/out, staff, discipline, care level) ───
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
    discipline: "RN",
    careLevel: "",
  },
  // ─── 1. DEMOGRAPHICS ───────────────────────────────
  demographics: {
    firstName: "", lastName: "", dob: "", gender: "",
    race: [], ethnicity: [], preferredLanguage: "", needsInterpreter: false,
    // A1005/A1010 source-attribution: recorded only when "Patient unable to
    // respond" is selected for that item, per CMS HOPE guidance -- when
    // another source supplies race/ethnicity, that source is documented
    // alongside the coded categories (owner design decision 2026-09-25).
    raceInformationSource: "", raceInformationSourceOther: "",
    ethnicityInformationSource: "", ethnicityInformationSourceOther: "",
    religion: "", maritalStatus: "", militaryService: "", phone: "", alternatePhone: "",
    address: { street: "", city: "", state: "", zip: "", county: "" },
    emergencyContact: { name: "", relationship: "", phone: "" },
    pcg: {
      // "assessed" distinguishes "RN confirmed Yes/No" from "not yet asked this visit" —
      // without it, an untouched assessment silently rendered as if "Yes — has PCG" had
      // been selected, per RNICA gap-review item #6.
      assessed: false,
      name: "", relationship: "", phone: "",
      healthStatus: "", anxietyLevel: "",
      ableToAdministerMeds: "", willingToProvideCare: "",
      pcgConcerns: "",
      // Cross-checked directly against real HospiceMD "Communications & Other
      // Factors > PCG" section (2026-09-25 owner-provided screenshots): these
      // 4 fields match that section 1:1. PCG education needs are intentionally
      // NOT duplicated here — the existing Teaching Needs module (moduleKey
      // "teachingNeeds", DEFAULT_EDUCATION_TOPICS) already covers "Teach
      // Patient/Family/PCG" with all 4 HospiceMD topics (Hospice, Disease
      // process, Medication, Advance directive) as a superset.
      participatesInCare: "", // Is PCG able to participate in care?
      signLanguageInterpreterNeeded: "", // If PCG hard of hearing/deaf, sign-language interpreter needed?
      householdChildren: "", // Any young children at home?
      householdChildrenDetail: "",
      householdPets: "", // Any pets? (If yes, specify)
      householdPetsDetail: "",
      // CDPH Caregiver Evaluation (Gap #2 — elevated for survey visibility)
      caregiverEvaluation: {
        physicalAbility: "",
        cognitiveAbility: "",
        emotionalReadiness: "",
        availabilityForCare: "",
        trainingNeeds: [],
        willingnessScore: "",
        capabilityScore: "",
        supportSystemAdequacy: "",
        evaluationNotes: "",
      },
    },
    // Patient's own medication self-administration capability — cross-checked
    // against real HospiceMD "Communications & Other Factors > Patient"
    // section: "Is Patient able to safely administer meds?" + "If No, who is
    // able to safely administer meds to Patient?" Distinct from the PCG's own
    // ableToAdministerMeds above (that is the caregiver's capability, this is
    // the patient's).
    medicationSafety: {
      selfAdministersMeds: "",
      medsAdministeredBy: "",
    },
    livingSituation: {
      siteOfService: "", admittedFrom: "",
      livingArrangement: "", availabilityOfAssistance: "",
    },
    advancedCarePlanning: {
      codeStatus: "", codeStatusDate: "", lifeSustainingTreatmentPreference: "",
      lifeSustainingTreatmentPreferenceDate: "", hospitalizationPreference: "",
      hospitalizationPreferenceDate: "", decisionMaker: "",
      poaName: "", poaPhone: "",
      advanceDirectiveOnFile: false, polstOnFile: false,
      // HOPE F2000/F2100/F2200 A: was the patient/responsible party asked? (0 No / 1 Yes-discussed / 2 Yes-refused)
      // Distinct from the clinical preference fields above — CMS defines these
      // items as "was asked", not the resulting clinical order.
      cprPreferenceAskedStatus: "", lifeSustainingAskedStatus: "", hospitalizationAskedStatus: "",
    },
  },

  // ─── 2. VITALS ─────────────────────────────────────
  vitals: {
    temperature: "", temperatureUnit: "F",
    pulse: "", pulseQuality: "", pulseRhythm: "",
    respirations: "", respirationPattern: "",
    bloodPressure: { systolic: "", diastolic: "", position: "" },
    height: "", heightUnit: "in", weight: "", weightUnit: "lbs",
    bmi: "", mac: "", oxygenSaturation: "", oxygenSaturationOnRA: true,
    ivAssessment: {
      hasIV: false, type: "", size: "", site: "",
      dressingType: "", insertionDate: "", lastChangeDate: "",
      condition: "", flushSchedule: "", notes: "",
    },
  },
  // ─── 3. PAIN ───────────────────────────────────────
  pain: {
    verbalizesPain: "", uncomfortableBecauseOfPain: "",
    // HOPE J0915 official CMS response: "Does the patient have neuropathic
    // pain?" (0 No / 1 Yes). Previously a plain boolean checkbox that was
    // never exported to HOPE at all — the mapper incorrectly exported
    // uncomfortableBecauseOfPain under the J0915 code instead. See
    // checkpoint "HOPE J0900/J0915 Pain compliance remediation".
    neuropathicPain: "",
    screeningDate: "",
    // HOPE J0900.A / J0900.C / J0900.D official CMS responses. Distinct from
    // verbalizesPain (which drives pain-scale tool selection, not the
    // official "was the patient screened for pain?" HOPE answer),
    // painIntensity.current (a raw numeric score, not the official 0/1/2/3/9
    // severity category), and assessmentTool (an auto-derived UI tool
    // selection based on communication status/age, not the clinician's
    // explicit confirmation of which standardized CMS tool category was
    // used). See checkpoint "HOPE J0900 compliance remediation".
    screenedForPain: "",
    painSeverityCategory: "",
    standardizedPainToolType: "",
    comprehensiveAssessmentCompleted: false,
    comprehensiveAssessmentDate: "",
    assessmentTool: "",
    painIntensity: { current: "", worst: "", best: "", acceptable: "" },
    painLocation: [], painCharacter: [], painRadiation: "",
    painBodySites: [],
    painMapMode: "verbal",
    aggravatingFactors: [], relievingFactors: [],
    painManagementPlan: "",
    flacc: {
      face: "", legs: "", activity: "", cry: "", consolability: "", total: "",
    },
    painad: {
      breathing: "", vocalization: "", facialExpression: "",
      bodyLanguage: "", consolability: "", total: "",
    },
    nonPharmInterventions: [],
  },

  // ─── 4. SYMPTOM IMPACT ─────────────────────────────
  // No RN-facing UI (owner correction 2026-09-25: pain, dyspnea, GI, and
  // anxiety/agitation severity are each documented exactly once in their
  // true owning section -- Pain, Respiratory, GI, Neuro/Mental Status --
  // never re-asked here). This object is a derived/computed store only,
  // kept in sync live by a background effect, so HOPE J2051 export, SFV
  // symptom logic, and reporting continue to work off a single source
  // of truth.
  symptomImpact: {
    pain: "", shortnessOfBreath: "", anxiety: "",
    nausea: "", vomiting: "", diarrhea: "",
    constipation: "", agitation: "",
    totalScore: "", assessmentDate: "",
  },

  // ─── 5. DIAGNOSES ──────────────────────────────────
  diagnoses: {
    primaryDiagnosis: { icd10: "", description: "", onsetDate: "", hopeDiagnosisCategory: "" },
    secondaryDiagnoses: [],
    comorbidities: [],
    terminalPrognosis: "",
    diseaseTrajectory: "",
    lcdEligibilityNarrative: "",
    // SECTION 10 — Clinical Narrative & Disease Trajectory. Deliberately
    // separate from lcdEligibilityNarrative (distinct purpose/field, never
    // merged/read by the other). clinicalNarrative is populated either by
    // manual RN typing or by an explicit "Build Draft from Documented
    // Findings" click that runs the deterministic, non-AI
    // buildClinicalNarrative() template renderer — it is never generated
    // automatically and never silently overwrites existing text.
    clinicalNarrative: "",
    clinicalNarrativeReviewed: false,
    // rnAddendum / clinicianClarification are pre-lock working fields
    // only. Once the assessment is locked, every Section 10 field
    // (including these two) becomes read-only in the UI — SNS EMR does
    // not yet have a separate authenticated addendum record/endpoint,
    // so this build intentionally does NOT fake one by keeping these
    // fields editable-with-a-timestamp after lock (that would still be
    // a silent mutation of already-authenticated documentation, not a
    // distinct traceable addendum).
    //
    // Future documentation infrastructure: Authenticated post-lock
    // addendum workflow — a separate record (parent assessment id,
    // addendum text, author identifier/credentials, created date/time,
    // reason/addendum type, authentication status) is the correct way
    // to capture information added after the original entry is
    // authenticated, and should be built as its own model/endpoint
    // rather than as mutable fields on this JSONB blob.
    rnAddendum: "",
    clinicianClarification: "",
    recentHospitalizations: "",
    recentErVisits: "",
    utilizationNotes: "",
    ndsEligibility: {
      detectedDisease: "",
      criteriaAnswers: {},
      criteriaFacts: {},
    },
    // HOPE Section I0000 — Comorbidities and Co-existing Conditions.
    // Manual overrides live here; auto-detection (from primary/secondary dx)
    // happens in HopeComorbiditiesCard and explicitly excludes any category
    // already represented by the Primary Diagnosis, so nothing is double-entered.
    hopeComorbidities: {
      cancer: false,
      heartFailure: false,
      pvdPad: false,
      cardiovascularExclHF: false,
      liverDisease: false,
      renalDisease: false,
      sepsis: false,
      diabetesMellitus: false,
      neuropathy: false,
      stroke: false,
      dementia: false,
      neurologicalConditions: false,
      seizureDisorder: false,
      copd: false,
      other: false,
      additionalNote: "",
    },
  },

  // ─── 6. PERFORMANCE STATUS ─────────────────────────
  performanceStatus: {
    pps: "", ppsJustification: "",
    kps: "", kpsJustification: "",
    ecog: "", ecogJustification: "",
    fast: "", fastStage: "",
    nyha: "", nyhaJustification: "",
    functionalDeclineNotes: "",
  },

  // ─── 7. NEUROLOGICAL ──────────────────────────────
  neurological: {
    consciousness: "",
    orientation: { time: false, place: false, person: false, situation: false, disoriented: false },
    communication: "", hearing: "", vision: "", balance: "",
    cognition: "", delirium: false, seizureHistory: false,
    psychiatricHistory: "", psychiatricHistoryType: [],
    sensoryDeficits: [],
    sensoryAids: [],
    symptomsDemeanor: [],
    // Motor deficit findings (e.g. hemiparesis/hemiplegia) extracted from
    // H&P/referral/uploaded-document/transcript evidence by the shared
    // StructuredFinding contract (app/services/evidence/structured_findings.py
    // NEURO_HEMIPARESIS_*/NEURO_HEMIPLEGIA_* concepts). `paralysis` under
    // musculoskeletal below is the matching cross-section write target for
    // the same finding (a hemiparesis is both a neurological deficit and a
    // musculoskeletal disability classification).
    motorDeficit: false,
    affectedSide: "",
    deficitType: [],
    sleepRest: {
      sleepPattern: "", averageSleepHours: "",
      sleepAids: [], restfulness: "",
      nighttimeSymptoms: [], response: "",
      notes: "",
    },
    hopeItems: { n0500: "", n0510: "", n0520: "" },
    notes: "",
    clinicalStatusChange: "",
  },

  // ─── 8. CARDIOVASCULAR ────────────────────────────
  cardiovascular: {
    // OWNER-APPROVED "Cardiovascular Overview Gate" (2026-09-28) --
    // presentation-only workflow gate, same pattern as Neurological's
    // `neuroOverview`. Not a clinical finding by itself.
    cardiovascularOverview: "",
    cardiovascularUnableToAssessReason: "",
    cardiovascularUnableToAssessOther: "",
    bpSymptoms: [],
    // OWNER CORRECTION (2026-09-28 Contradiction 4) -- "BP Status" and
    // "Orthostatic Finding" are two independent single-select fields
    // (Hypotensive + Orthostatic-Present is a valid combination). The
    // legacy multi-select `bpSymptoms` array above is preserved untouched
    // (never rewritten); resolveBpLegacyDisplay reads it for display only
    // when unambiguous (a contradictory legacy array is surfaced as a
    // review-required note instead of being silently collapsed).
    bpStatus: "",
    orthostaticFinding: "",
    pulseSites: [],
    pulseQuality: "",
    // OWNER-APPROVED "Pulse Redesign" (2026-09-28) -- Rhythm/Rate/
    // Strength are independently selectable. Legacy `pulseQuality` above
    // is preserved untouched and read-aliased into whichever of these
    // three dimensions it belongs to when the corresponding new field is
    // still blank (see PULSE_LEGACY_DIMENSION below).
    pulseRhythm: "", pulseRate: "", pulseStrength: "",
    edema: { present: "", location: [], severity: "", pitting: "" },
    chestPain: { present: "", type: "", frequency: "" },
    peripheralCirculation: "", heartSounds: "", jvd: "",
    skinColor: "", pacemaker: false, internalDefibrillator: false,
    varicoseVeins: false, centralVenousLine: false,
    coolExtremities: false, stasisUlcer: false,
    fatigue: "", dizziness: "", syncope: "", cardiacDyspnea: false,
    // Objective heart-failure finding drafted from evidence text (H&P,
    // referral, uploaded documents, or transcript) via the shared
    // StructuredFinding contract's CV_HEART_FAILURE_* concepts. Deliberately
    // separate from hopeComorbidities.heartFailure (HOPE I0600) below, which
    // is auto-derived from a coded Primary/Secondary Diagnosis category --
    // this field can be populated even before/without a coded diagnosis and
    // is always draft/review-needed until clinician review.
    heartFailurePresent: false,
    heartFailureType: [],
    notes: "",
    clinicalStatusChange: "",
    // Directive (2026-09-28) "Cardiovascular Layout Consolidation" Section
    // 13 -- Path 2 ("Existing Cardiovascular Findings Review") clinician
    // confirmation. A new, independent boolean; never rewrites author or
    // timestamp, never touches any existing finding, and is not required
    // on any other Overview path.
    cardiovascularFindingsConfirmedThisVisit: false,
  },

  // ─── 9. RESPIRATORY ───────────────────────────────
  respiratory: {
    sobSeverity: "", exertionLevel: "",
    shortnessOfBreathScreened: false, screeningDate: "",
    treatmentInitiated: false, treatmentDate: "", treatmentDeclined: false,
    lungSounds: [], respirations: [],
    coughType: "", sputumCharacter: "",
    oxygenTherapy: {
      inUse: false, type: "", litersPerMinute: "",
      hoursPerDay: "", satOnO2: "",
      deliveryMode: "", onRoomAir: false,
    },
    ventilator: {
      shortTermVentilator: false, longTermVentilator: false,
      ventilatorTypeAndSettings: "",
      tracheostomyType: "", tracheostomySize: "",
    },
    notes: "",
    clinicalStatusChange: "",
  },

  // ─── 10. INFECTION ────────────────────────────────
  infection: {
    allergies: [],
    allergyDetails: "",
    currentInfections: [],
    antibioticResistantInfection: [],
    historyOfResistantInfections: [],
    immunosuppressed: false,
    antibioticUse: false,
    temperature: "",
    recurrentInfection: false,
    infectionHistory: "",
    precautions: [],
    notes: "",
    clinicalStatusChange: "",
  },

  // ─── 11. GASTROINTESTINAL ─────────────────────────
  gastrointestinal: {
    nausea: "", vomiting: "", vomitingOccurrences24h: "", diarrhea: "", constipation: "",
    bowelSounds: "", abdomen: "", ascites: false, abdominalGirth: "",
    stoolCharacter: [],
    bowelStatus: "", bowelFrequency: "", reasonBowelRegimenNotInitiated: "", lastBM: "",
    continence: "",
    feedingTube: { present: false, type: "", site: "" },
    ostomy: { present: false, type: "", condition: "" },
    notes: "",
    clinicalStatusChange: "",
  },

  // ─── 12. NUTRITION ────────────────────────────────
  nutrition: {
    weightLossPastSixMonths: "", appetite: "",
    dietType: "", fluidIntake: "",
    swallowingIssues: [], oralMucosa: "",
    dentures: { upper: false, lower: false, condition: "" },
    nutritionalSupplements: "",
    npoStatus: "", artificialFeeding: [], oralCavityFindings: [],
    notes: "",
    clinicalStatusChange: "",
  },

  // ─── 13. ENDOCRINE ────────────────────────────────
  endocrine: {
    endocrineImpairment: [],
    thyroid: { assessment: "", notes: "" },
    diabetes: {
      type: "", dependency: "", glucoseMonitoring: "",
      lastHbA1c: "", lastHbA1cDate: "",
      insulinType: "", insulinDose: "",
      oralHypoglycemics: [],
    },
    endocrineSymptoms: [],
    symptomSeverity: {},
    currentEndocrineMeds: [],
    notes: "",
    clinicalStatusChange: "",
  },

  // ─── 14. GENITOURINARY ────────────────────────────
  genitourinary: {
    urinaryStatus: "", frequency: "",
    urineCharacteristics: [], urineColor: "",
    catheter: {
      present: false, type: "", size: "",
      insertionDate: "", lastChangeDate: "",
      condition: "", urineCharacteristics: [],
      irrigation: { solution: "", frequency: "", duration: "" },
    },
    catheterCare: "",
    urineOutput: "", twentyFourHourVolume: "",
    reproductive: { concerns: [], notes: "" },
    bladderManagement: [],
    notes: "",
    clinicalStatusChange: "",
  },

  // ─── 15. MUSCULOSKELETAL ──────────────────────────
  musculoskeletal: {
    weakness: "", rigidity: "", contractures: "", paralysis: "",
    // Structured location to match the depth of sibling body-system findings
    // (e.g. cardiovascular.edema.location). `contractures` itself stays the
    // existing None/Mild/Moderate/Severe severity radio.
    contracturesLocation: [],
    // Presence-only flags written by MSK_CONTRACTURES_PRESENT /
    // MSK_RIGIDITY_PRESENT (structured_findings.py) when evidence documents
    // the finding without stating a severity. The `contractures`/`rigidity`
    // severity radios above are only ever set by a distinct, explicit-
    // severity concept (MSK_CONTRACTURES_SEVERITY_*/MSK_RIGIDITY_SEVERITY_*)
    // so severity is never inferred/guessed from a presence-only mention.
    contracturesPresent: false,
    rigidityPresent: false,
    romLimitations: [],
    // §5.10 Issues/Additional items not covered by the existing severity
    // radios (weakness/rigidity/contractures) or paralysis/romLimitations.
    musculoskeletalIssues: [],
    strength: "", balance: "", painWithMovement: "",
    gait: "", assistiveDevices: [],
    fallHistory: { fallsLast90Days: "", fallInjuries: "" },
    mobility: {
      ambulatoryStatus: "", endurance: "", transferAbility: "",
    },
    adl: {
      bathing: "", dressing: "", toileting: "",
      transferring: "", eating: "", grooming: "",
    },
    notes: "",
    clinicalStatusChange: "",
  },

  // ─── 16. SKIN ─────────────────────────────────────
  skin: {
    skinConditionsPresent: false,
    skinStatus: [], skinTurgor: "",
    skinBodySites: [],
    skinMoisture: "", skinTemperature: "", skinColorFinding: "",
    skinEdema: { severity: "", location: "" },
    additionalSkinFindings: [],
    braden: {
      sensoryPerception: "", moisture: "", activity: "",
      mobility: "", nutrition: "", frictionShear: "", total: "",
    },
    pressureInjuryRisk: "",
    wounds: [],
    woundImpairment: "",
    pressureReliefMeasures: [], repositioningPlan: "",
    notes: "",
    clinicalStatusChange: "",
  },

  // ─── 17. IMMINENT DEATH ───────────────────────────
  imminentDeath: {
    appearsThreeDaysOrLess: "",
    indicators: [],
    comfortMeasuresInPlace: false,
    familyNotified: false,
    notes: "",
  },

  // ─── 18. SFV ──────────────────────────────────────
  sfv: {
    symptomImpactScreeningCompleted: false,
    symptomImpactScreeningDate: "",
    inPersonSfvCompleted: false,
    sfvDate: "", reasonNotCompleted: "", findings: "",
    triggeredSymptoms: [],
    symptomImpactAtSfv: {
      pain: "", shortnessOfBreath: "", anxiety: "", nausea: "",
      vomiting: "", diarrhea: "", constipation: "", agitation: "",
    },
    interventions: [],
    notes: "",
  },

  // ─── 19. SAFETY ───────────────────────────────────
  safety: {
    safetyAssessmentCompleted: false,
    homeEnvironment: [],
    fallRiskAssessmentCompleted: false,
    fallRiskLevel: "",
    transferSafetyLevel: "",
    firearmInHome: false,
    oxygenInUse: false, oxygenSafetyReviewed: false,
    incidentOccurrenceReported: false,
    incidentOccurrenceNotes: "",
    disasterLevel: "",
    disasterLevelOneConditions: [],
    disasterLevelTwoConditions: [],
    disasterLevelThreeConditions: [],
    dmeItems: DME_ITEM_LIST.map((item) => ({ item, status: "", specify: "" })),
    supplies: {
      existingCategories: [], neededCategories: [], otherSuppliesNotes: "",
    },
    notes: "",
  },

  // ─── 20. PSYCHOSOCIAL ─────────────────────────────
  psychosocial: {
    // Referral-determination workflow (owner design correction 2026-09-25,
    // refined 2026-09-25): Psychosocial is NOT a standalone discipline
    // assessment -- the RN documents findings only; SNS derives the MSW
    // Recommended YES/NO from those findings (display-only, never stored --
    // see referralRecommendation.js). The RN records only the Family
    // Response. When Recommended=YES and Family Response=Refused, the
    // Referral Refused record below captures who refused, when, and why
    // (RN follow-up responsibility changes on refusal).
    referralIndicators: [],
    familyResponse: "", // Accepted / Refused / Deferred
    refusal: { date: "", personRefusing: "", relationship: "", reason: "", recordedBy: "" },
    notes: "",
  },

  // ─── 21. SPIRITUAL ────────────────────────────────
  spiritual: {
    // Referral-determination workflow (owner design correction 2026-09-25,
    // refined 2026-09-25): Spiritual is NOT a Chaplain assessment -- the RN
    // documents findings only; SNS derives the Spiritual Care Recommended
    // YES/NO (display-only, never stored). The RN records only the Family
    // Response, plus a Referral Refused record on refusal. F3000
    // (HOPE-required) is retained verbatim.
    religiousPreference: "",
    clergyInvolvement: "", // Not involved / Community clergy involved / Facility chaplain involved / Both
    referralIndicators: [],
    familyResponse: "", // Accepted / Refused / Deferred
    refusal: { date: "", personRefusing: "", relationship: "", reason: "", recordedBy: "" },
    concernsAskedStatus: "", // HOPE F3000 A: 0 No / 1 Yes-discussed / 2 Yes-refused
    concernsDiscussedDate: "", // HOPE F3000 B
    notes: "",
  },

  // ─── 22. BEREAVEMENT ──────────────────────────────
  bereavement: {
    // Referral-determination workflow (owner design correction 2026-09-25,
    // refined 2026-09-25): Bereavement is NOT bereavement-counseling
    // documentation -- the RN documents risk factors only; SNS derives the
    // Bereavement Follow-Up Recommended YES/NO (display-only, never
    // stored). The RN records only the Family Response, plus a Referral
    // Refused record on refusal.
    riskFactors: [],
    familyResponse: "", // Accepted / Refused / Deferred
    refusal: { date: "", personRefusing: "", relationship: "", reason: "", recordedBy: "" },
    notes: "",
  },

  // ─── 23. PERSONAL CARE ────────────────────────────
  personalCare: {
    aideTasks: [],
    aideVisitPreferences: {
      frequency: "", preferredTime: "", duration: "",
    },
    volunteerServices: [],
    communityResources: [],
    equipmentSupplyNeeds: [],
    notes: "",
  },

  // ─── 24. TEACHING NEEDS ───────────────────────────
  teachingNeeds: {
    primaryLearner: "",
    learningStylePreference: "",
    barriersToLearning: [],
    educationTopics: DEFAULT_EDUCATION_TOPICS.map((topic) => ({
      topic, taught: false, understood: false, returnDemo: false, na: false,
    })),
    teachingTopics: [],
    teachingTopicsOther: "",
    teachingMethods: [],
    patientFamilyResponse: "",
    followUpPlan: "",
    notes: "",
  },

  // ─── 25. ADMISSIONS ORDER ─────────────────────────
  admissionsOrder: {
    admissionStatement: "On completion of assessment and medical history available to me, I have discussed patient's status with the Physician. Based on information provided to the Physician and review of patient's medical history, the Physician has issued an order to admit this patient to Hospice. Physician's initial order on Level of Care, Frequency of Visit and any applicable Meds/DME/Treatment is entered below. This is a verbal order / read back and verified.",
    levelOfCare: {
      level: "", effectiveDate: "", justification: "",
    },
    visitFrequency: DEFAULT_VISIT_DISCIPLINES.map((d) => ({ ...d })),
    treatmentMedsOrderCompleted: false,
    haAssignment: { assignedAide: "", notApplicable: false },
    initialPocIdg: {
      created: false, createdDate: "",
      notes: "IDG should only be created after all problems identified during this Assessment have been added to Initial POC using the ADD ISSUE feature.",
    },
    nonCoveredItems: [],
    toVerification: {
      verbalOrderReadBack: false, verifiedBy: "",
      prescriberContacted: false, verificationTimestamp: "",
    },
  },

  // ─── 27. REFERRALS ────────────────────────────────
  referrals: {
    socialWork: { referred: false, reason: "", urgency: "" },
    spiritualCare: { referred: false, reason: "", urgency: "" },
    volunteer: { referred: false, type: "", urgency: "" },
    therapy: [],
    dietitian: { referred: false, reason: "" },
    pharmacist: { referred: false, reason: "" },
    other: [],
    notes: "",
    reviewed: false,
  },

  // ─── 28. FINALIZATION ─────────────────────────────
  finalization: {
    completedSections: [],
    incompleteCount: 0,
    clinicalNarrative: "",
    signatureCertification: false,
    clinicianSignature: "",
    signatureDate: "",
    hopeSubmissionNumber: "",
    hopeAlreadySubmitted: false,
    supervisorReview: { required: false, reviewedBy: "", reviewDate: "" },
    assessmentLocked: false,
    lockedTimestamp: "",
  },
};

function normalizeLoadedRnicaFormData(loadedFormData) {
  return {
    ...loadedFormData,
    finalization: {
      ...INITIAL_FORM.finalization,
      ...(loadedFormData?.finalization || {}),
    },
  };
}

// ════════════════════════════════════════════════════════════════
// 3. API SERVICE — 4 Backend Endpoints
// ════════════════════════════════════════════════════════════════

// Delegates to the shared client so requests carry the auth token.
const api = {
  saveRNICAAssessment: (patientId, formData, assessmentSubtype) =>
    saveRnicaAssessmentOffline(
      assessmentSubtype ? { patientId, formData, assessmentSubtype } : { patientId, formData }
    ),
  getRNICAAssessment: (assessmentId) => getRnicaAssessment(assessmentId),
  getRNICAAssessmentByPatient: (patientId, assessmentSubtype = undefined) =>
    assessmentSubtype
      ? getRnicaAssessmentByPatientType(patientId, { assessmentSubtype })
      : getRnicaAssessmentByPatient(patientId),
  updateRNICAAssessment: (assessmentId, formData, fieldProvenance) =>
    updateRnicaAssessmentOffline(assessmentId, formData, fieldProvenance),
  lockRNICAAssessment: (assessmentId) => lockRnicaAssessment(assessmentId),
  deleteRNICAAssessment: (assessmentId) => deleteRnicaAssessment(assessmentId),
  getRNICAIntelligence: (assessmentId) =>
    assessmentId ? getRnicaIntelligence(assessmentId) : null,
};


// ════════════════════════════════════════════════════════════════
// 4. VALIDATION
// ════════════════════════════════════════════════════════════════

function validateRNICA(formData, mode = "ica") {
  const errors = {};
  const warnings = {};
  const includeHopeRequirements = mode !== "ongoing";
  const requireAdmissionOrders = mode === "ica";

  // Demographics ? required fields
  if (!formData.demographics.firstName) errors["demographics.firstName"] = "First name is required";
  if (!formData.demographics.lastName) errors["demographics.lastName"] = "Last name is required";
  if (!formData.demographics.dob) errors["demographics.dob"] = "Date of birth is required";
  if (!formData.demographics.gender) errors["demographics.gender"] = "Gender is required";

  if (includeHopeRequirements) {
    // HOPE items ? A1110 Language
    if (!formData.demographics.preferredLanguage) {
      warnings["demographics.preferredLanguage"] = "HOPE A1110: Preferred language required";
    }
    // A1005 Ethnicity
    if (formData.demographics.ethnicity.length === 0) {
      warnings["demographics.ethnicity"] = "HOPE A1005: Ethnicity required";
    }
    // A1010 Race
    if (formData.demographics.race.length === 0) {
      warnings["demographics.race"] = "HOPE A1010: Race required";
    }

    // Advanced Care Planning — HOPE required
    if (!formData.demographics.advancedCarePlanning.cprPreferenceAskedStatus) {
      errors["demographics.advancedCarePlanning.cprPreferenceAskedStatus"] = "F2000: Was patient/responsible party asked about CPR preference? is required";
    }
    if (!formData.demographics.advancedCarePlanning.codeStatus) {
      errors["demographics.advancedCarePlanning.codeStatus"] = "Code status is required";
    }
    if (!formData.demographics.advancedCarePlanning.lifeSustainingAskedStatus) {
      errors["demographics.advancedCarePlanning.lifeSustainingAskedStatus"] = "F2100: Was patient/responsible party asked about other life-sustaining treatments? is required";
    }
    if (!formData.demographics.advancedCarePlanning.lifeSustainingTreatmentPreference) {
      errors["demographics.advancedCarePlanning.lifeSustainingTreatmentPreference"] = "Life-sustaining treatment preference required";
    }
    if (!formData.demographics.advancedCarePlanning.hospitalizationAskedStatus) {
      errors["demographics.advancedCarePlanning.hospitalizationAskedStatus"] = "F2200: Was patient/responsible party asked about hospitalization preference? is required";
    }
    if (!formData.demographics.advancedCarePlanning.hospitalizationPreference) {
      errors["demographics.advancedCarePlanning.hospitalizationPreference"] = "Hospitalization preference required";
    }
  }

  if (!pcgIsAssessed(formData.demographics.pcg)) {
    warnings["demographics.pcg.assessed"] = "Primary Caregiver status not yet assessed this visit (Yes/No unanswered)";
  }

  // CDPH Gap #2 ? Caregiver willingness and capability evaluation (skip entirely for No-PCG/facility patients)
  if (!formData.demographics.pcg.noPcg) {
    if (!formData.demographics.pcg.willingToProvideCare) {
      warnings["demographics.pcg.willingToProvideCare"] = "CDPH: Caregiver willingness to provide care required";
    }
    if (!formData.demographics.pcg.ableToAdministerMeds) {
      warnings["demographics.pcg.ableToAdministerMeds"] = "CDPH: Caregiver ability to administer meds required";
    }
    if (!formData.demographics.pcg.caregiverEvaluation?.willingnessScore) {
      warnings["demographics.pcg.caregiverEvaluation.willingnessScore"] = "CDPH: Caregiver willingness score required";
    }
    if (!formData.demographics.pcg.caregiverEvaluation?.capabilityScore) {
      warnings["demographics.pcg.caregiverEvaluation.capabilityScore"] = "CDPH: Caregiver capability score required";
    }
  }

  if (includeHopeRequirements) {
    // Pain ? HOPE J0900, J0915
    if (!formData.pain.screenedForPain) {
      errors["pain.screenedForPain"] = "J0900.A: Was the patient screened for pain? is required";
    }
    if (formData.pain.screenedForPain === "1" && !formData.pain.painSeverityCategory) {
      errors["pain.painSeverityCategory"] = "J0900.C: Patient's pain severity is required when screened for pain";
    }
    if (formData.pain.screenedForPain === "1" && !formData.pain.standardizedPainToolType) {
      errors["pain.standardizedPainToolType"] = "J0900.D: Type of standardized pain tool used is required when screened for pain";
    }
    if (!formData.pain.verbalizesPain) {
      warnings["pain.verbalizesPain"] = "Pain verbalization status required to select pain scale";
    }
    if (!formData.pain.neuropathicPain) {
      errors["pain.neuropathicPain"] = "J0915: Does the patient have neuropathic pain? is required";
    }

    // Symptom Impact ? J2051 A-H (all 8 required)
    const siFields = ["pain","shortnessOfBreath","anxiety","nausea","vomiting","diarrhea","constipation","agitation"];
    siFields.forEach((f, i) => {
      if (!formData.symptomImpact[f]) {
        warnings[`symptomImpact.${f}`] = `HOPE J2051${String.fromCharCode(65 + i)}: ${f} score required`;
      }
    });

    // SFV -- J2052A/C: an SFV is required whenever any J2051 item is
    // Moderate (2) or Severe (3). HOPE J2052C ownership fix (issue #146):
    // the reason SFV was not completed is NOT knowable at the time this
    // triggering RN ICA/HUV assessment is completed (the SFV attempt
    // hasn't happened yet) and is captured/validated authoritatively on
    // the SFV attempt visit instead (VisitNotes.jsx
    // ::SymptomFollowUpVisitSection). This assessment must never block
    // signing on a value the clinician cannot yet truthfully know.

    // Diagnoses ? I0010
    if (!formData.diagnoses.primaryDiagnosis.icd10) {
      errors["diagnoses.primaryDiagnosis"] = "HOPE I0010: Primary diagnosis ICD-10 required";
    }
    if (!formData.diagnoses.primaryDiagnosis.hopeDiagnosisCategory) {
      errors["diagnoses.primaryDiagnosis.hopeDiagnosisCategory"] = "HOPE I0010: Principal diagnosis category required";
    }

    // Performance Status ? M1190
    if (!formData.performanceStatus.pps && !formData.performanceStatus.kps) {
      warnings["performanceStatus"] = "HOPE M1190: At least PPS or KPS required";
    }

    // Neurological ? BIMS N0500-N0520
    if (!formData.neurological.hopeItems.n0500) {
      warnings["neurological.hopeItems.n0500"] = "HOPE N0500: BIMS repetition required";
    }

    // Imminent Death ? J0050
    if (!formData.imminentDeath.appearsThreeDaysOrLess) {
      warnings["imminentDeath.appearsThreeDaysOrLess"] = "HOPE J0050: Prognosis assessment required";
    }
  }

  // Skin ? Braden
  if (!formData.skin.braden.total) {
    warnings["skin.braden.total"] = "Braden Scale total required";
  }

  // Psychosocial ? Suicide/self-harm safety documentation (CDPH: complete, accurate documentation required)
  if (formData.psychosocial.referralIndicators?.includes("Suicide/self-harm risk indicated") && !formData.psychosocial.notes?.trim()) {
    warnings["psychosocial.notes"] = "Safety: Suicide/self-harm risk indicated — document safety assessment/plan in Notes";
  }

  // SECTION 10 — Clinical Narrative & Disease Trajectory. The frozen
  // master map does not cite a HOPE code for this narrative (unlike the
  // hard-blocking Diagnoses/Pain/etc. items above), so this is a soft
  // completion warning rather than a hard error — but it applies equally
  // whether the narrative text was typed manually or built via "Build
  // Draft from Documented Findings," per the rule that a manually
  // entered narrative is just as valid as a generated one.
  if (formData.diagnoses.clinicalNarrative?.trim() && formData.diagnoses.clinicalNarrativeReviewed !== true) {
    warnings["diagnoses.clinicalNarrativeReviewed"] = "Clinical narrative documented but not yet reviewed — confirm review before finalizing (Section 10)";
  }

  // Admissions Order ? Level of Care required
  if (requireAdmissionOrders && !formData.admissionsOrder.levelOfCare.level) {
    errors["admissionsOrder.levelOfCare"] = "Level of Care is required for admission";
  }

  // Admissions Order ? T.O. Verification
  if (requireAdmissionOrders && !formData.admissionsOrder.toVerification.verbalOrderReadBack) {
    errors["admissionsOrder.toVerification"] = "Verbal order read-back verification required";
  }

  // Finalization ? signature
  if (!formData.finalization.clinicalNarrative) {
    errors["finalization.clinicalNarrative"] = "Clinical narrative is required before attestation";
  }
  if (!formData.finalization.clinicianSignature) {
    errors["finalization.clinicianSignature"] = "Clinician signature required";
  }

  // SECTION 12 — attestation. Previously present in the UI/INITIAL_FORM
  // but never enforced; the assessment must not be lockable without an
  // explicit clinician attestation that it is complete and accurate.
  if (formData.finalization.signatureCertification !== true) {
    errors["finalization.signatureCertification"] = "Signature certification (attestation) is required before locking";
  }

  return { errors, warnings, isValid: Object.keys(errors).length === 0 };
}

// Structured Findings application layer — human-readable "destination
// field(s)" description for a concept, e.g. "cardiovascular.chfPresent" or
// "wounds[].location" — used only for RN-facing display in the Structured
// Findings review panel, never to derive the actual write logic (that
// still lives entirely in applyStructuredFindings.js against the same
// CONCEPT_REGISTRY).
function describeStructuredFindingDestinations(conceptCode) {
  const concept = CONCEPT_REGISTRY[conceptCode];
  if (!concept) return conceptCode;
  const writes = concept.writes || [];
  if (writes.length === 0 && concept.valueSlot) {
    return `${concept.section}.${concept.valueSlot.path}`;
  }
  return writes
    .map((w) => `${w.section || concept.section}.${w.path}`)
    .join(", ");
}


// ════════════════════════════════════════════════════════════════
// 5. HELPER COMPONENTS
// ════════════════════════════════════════════════════════════════


// Tag components
function HopeTag({ code }) {
  const mode = useContext(AssessmentModeContext);
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  if (mode === "ongoing") return null;
  return <span style={styles.hopeTag}>HOPE {code}</span>;
}
function SfvTag() {
  const mode = useContext(AssessmentModeContext);
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  if (mode === "ongoing") return null;
  return <span style={styles.sfvTag}>SFV Trigger</span>;
}
function CmsTag({ label }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return <span style={styles.cmsTag}>CMS {label || "Required"}</span>;
}

// Form field components
function FormInput({ label, value, onChange, type = "text", placeholder, required, hopeCode, ...rest }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>
        {label} {required && <span style={{ color: COLORS.error }}>*</span>}
        {hopeCode && <> <HopeTag code={hopeCode} /></>}
      </label>
      <ShadcnInput
        type={type} value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder} {...rest}
      />
    </div>
  );
}

function FormTextarea({ label, value, onChange, placeholder, rows = 3, disabled }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>{label}</label>
      <ShadcnTextarea
        style={{ minHeight: rows * 24 }} value={value || ""}
        onChange={(e) => onChange(e.target.value)} placeholder={placeholder} disabled={disabled}
      />
    </div>
  );
}

// Structured-charting alternative to a pure narrative textarea: tap a
// preset phrase to add/remove it from the same underlying string field
// (semicolon-joined), instead of free typing. Same path/data type as a
// plain textarea -- no schema change, no new field -- just a faster
// click-to-chart entry path. The textarea stays available underneath for
// anything a preset doesn't cover.
function FormQuickPickTextarea({ label, value, onChange, presets = [], placeholder, rows = 2 }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  const parts = (value || "").split(";").map((s) => s.trim()).filter(Boolean);
  const togglePreset = (preset) => {
    const has = parts.includes(preset);
    const next = has ? parts.filter((p) => p !== preset) : [...parts, preset];
    onChange(next.join("; "));
  };
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>{label}</label>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 6 }}>
        {presets.map((preset) => {
          const selected = parts.includes(preset);
          return (
            <button
              key={preset}
              type="button"
              onClick={() => togglePreset(preset)}
              style={{
                borderRadius: 999,
                border: selected ? `1px solid ${COLORS.teal}` : `1px solid ${COLORS.border}`,
                background: selected ? COLORS.teal : "transparent",
                color: selected ? "#fff" : COLORS.text,
                fontSize: 11,
                fontWeight: 700,
                padding: "4px 10px",
                cursor: "pointer",
              }}
            >
              {preset}
            </button>
          );
        })}
      </div>
      <ShadcnTextarea
        style={{ minHeight: rows * 24 }} value={value || ""}
        onChange={(e) => onChange(e.target.value)} placeholder={placeholder || "Add detail not covered by the presets above (optional)"}
      />
    </div>
  );
}

function FormSelect({ label, value, onChange, options, required, hopeCode, disabled }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>
        {label} {required && <span style={{ color: COLORS.error }}>*</span>}
        {hopeCode && <> <HopeTag code={hopeCode} /></>}
      </label>
      <Select value={value || undefined} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger><SelectValue placeholder="— Select —" /></SelectTrigger>
        <SelectContent>
          {options.map((opt) => {
            const val = typeof opt === "string" ? opt : opt.value;
            const lbl = typeof opt === "string" ? opt : opt.label;
            return <SelectItem key={val} value={val}>{lbl}</SelectItem>;
          })}
        </SelectContent>
      </Select>
    </div>
  );
}

function FormRadioGroup({ label, value, onChange, options, hopeCode, sfv }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>
        {label}
        {hopeCode && <> <HopeTag code={hopeCode} /></>}
        {sfv && <> <SfvTag /></>}
      </label>
      <RadioGroup style={styles.radioGroup} value={value ?? undefined} onValueChange={onChange}>
        {options.map((opt) => {
          const val = typeof opt === "string" ? opt : opt.value;
          const lbl = typeof opt === "string" ? opt : opt.label;
          return (
            <label key={val} style={styles.radioLabel}>
              <RadioGroupItem value={val} />
              {lbl}
            </label>
          );
        })}
      </RadioGroup>
    </div>
  );
}

// GitHub Directive (2026-09-28) Critical Finding #4 -- progressive
// disclosure for single-select fields whose full option list creates
// "too many choices displayed simultaneously." Renders two large primary
// buttons; only when the current/selected value falls outside
// `normalValues` does a second, compact detail row of the remaining
// options appear. Both tiers write to the SAME field path -- no new field,
// no option removed, so every existing stored value (including legacy
// detail strings) round-trips exactly as before.
function FormGatedRadio({ label, value, onChange, primaryOptions, normalValues, detailOptions, hopeCode }) {
  // Bounded Compatibility Increment Section 13 -- primaryOptions may now
  // contain {value,label} display-adapter entries (matching FormSegmented's
  // existing convention, e.g. Communication's stored "Normal" displaying as
  // "No Current Communication Concern"). Only VALUES drive the gating
  // logic below; stored data and detail-reveal behavior are unchanged.
  const primaryValues = primaryOptions.map((opt) => (typeof opt === "string" ? opt : opt.value));
  const isDetailValue = Boolean(value) && !primaryValues.includes(value) && !normalValues.includes(value);
  const primaryValue = isDetailValue ? primaryValues[1] : (normalValues.includes(value) ? primaryValues[0] : value);
  const showDetail = isDetailValue || primaryValue === primaryValues[1];
  return (
    <div>
      <FormSegmented label={label} value={primaryValue} onChange={onChange} options={primaryOptions} hopeCode={hopeCode} />
      {showDetail && (
        <div style={{ marginTop: 4, marginLeft: 12, paddingLeft: 8, borderLeft: "2px solid var(--rnica-border, #d0d5dd)" }}>
          <FormSegmented label={`${label} — Detail`} value={isDetailValue ? value : undefined} onChange={onChange} options={detailOptions} />
        </div>
      )}
    </div>
  );
}

// Tri-state control for clinical "present/absent" findings that must not
// collapse "never assessed" and "assessed as negative" into the same value
// (a plain unchecked checkbox can't be told apart from a skipped field).
// Backward-compatible with legacy boolean data: true -> "Yes", false/""/null -> "" (Not Assessed).
function normalizeTriState(value) {
  if (value === true) return "Yes";
  if (value === "Yes" || value === "No") return value;
  return "";
}

// Back-compat check for pre-existing PCG data saved before the explicit
// "assessed" flag was introduced: if the record already has a meaningful
// answer (facility-based no-PCG, or any populated PCG detail field), treat
// it as already assessed so legacy/finalized charts aren't retroactively
// flagged as incomplete — never rewrites the stored data itself.
function pcgIsAssessed(pcg) {
  if (!pcg) return false;
  if (pcg.assessed === true) return true;
  if (pcg.noPcg === true) return true;
  return Boolean(pcg.name || pcg.relationship || pcg.phone || pcg.healthStatus || pcg.anxietyLevel || pcg.ableToAdministerMeds || pcg.willingToProvideCare);
}

function FormTriState({ label, value, onChange, hopeCode }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  const normalized = normalizeTriState(value);
  const options = [
    { value: "", label: "Not Assessed" },
    { value: "No", label: "No" },
    { value: "Yes", label: "Yes" },
  ];
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>
        {label}
        {hopeCode && <> <HopeTag code={hopeCode} /></>}
      </label>
      <RadioGroup style={styles.radioGroup} value={normalized || "unassessed"} onValueChange={(v) => onChange(v === "unassessed" ? "" : v)}>
        {options.map((opt) => (
          <label key={opt.value || "unassessed"} style={{
            ...styles.radioLabel,
            ...(opt.value === "" && normalized === "" ? { color: COLORS.gray, fontStyle: "italic" } : {}),
          }}>
            <RadioGroupItem value={opt.value || "unassessed"} />
            {opt.label}
          </label>
        ))}
      </RadioGroup>
    </div>
  );
}

function FormCheckboxGroup({ label, values = [], onChange, options, hopeCode }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  const toggle = (val) => {
    const next = values.includes(val) ? values.filter((v) => v !== val) : [...values, val];
    onChange(next);
  };
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>
        {label}
        {hopeCode && <> <HopeTag code={hopeCode} /></>}
      </label>
      <div style={styles.checkboxGroup}>
        {options.map((opt) => {
          const val = typeof opt === "string" ? opt : opt.value;
          const lbl = typeof opt === "string" ? opt : opt.label;
          return (
            <label key={val} style={styles.checkboxLabel}>
              <Checkbox checked={values.includes(val)} onCheckedChange={() => toggle(val)} />
              <span>{lbl}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

// GitHub UI Directive (2026-09-28) -- compact segmented-control replacement
// for FormRadioGroup's larger circular-radio rows, opt-in only via
// `type: "segmented"` on a field config (FormRadioGroup itself is
// untouched and keeps rendering exactly as before everywhere it is still
// used, so no other Body System or assessment screen changes visually).
// Same single-value/onChange contract as FormRadioGroup -- no data shape
// change. Optional `aliases` lets a legacy/duplicate stored value (e.g.
// "Awake") render as an already-existing canonical option (e.g. "Alert")
// selected, without ever writing the alias again and without removing the
// legacy value from the option list or backend concept registry.
function FormSegmented({ label, value, onChange, options, hopeCode, sfv, aliases }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  const displayValue = (aliases && aliases[value]) || value;
  // GitHub Directive (2026-09-28) Section 37/40 guardrail -- an option can
  // be retired from the visible control (e.g. duplicate concepts like
  // "Hearing aid" moving to Sensory Aids) without ever deleting a
  // patient's previously stored value. When the stored value no longer
  // matches any current option, show a small review chip instead of
  // silently rendering "nothing selected" -- the raw value is untouched.
  const hasLegacyValue = Boolean(displayValue) && !options.some((opt) => (typeof opt === "string" ? opt : opt.value) === displayValue);
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>
        {label}
        {hopeCode && <> <HopeTag code={hopeCode} /></>}
        {sfv && <> <SfvTag /></>}
      </label>
      {/* shadcn/ui ToggleGroup (Radix), type="single" -- compact mutually
          exclusive clinical-status chip row. Re-clicking the selected chip
          deselects it (Radix's native single-type behavior), preserving the
          existing "" unselected-default convention used throughout this
          file without any extra onClick interception. */}
      <ToggleGroup type="single" aria-label={label} value={displayValue || ""} onValueChange={(v) => onChange(v ?? "")}>
        {options.map((opt) => {
          const val = typeof opt === "string" ? opt : opt.value;
          const lbl = typeof opt === "string" ? opt : opt.label;
          return (
            <ToggleGroupItem key={val} value={val}>
              {lbl}
            </ToggleGroupItem>
          );
        })}
      </ToggleGroup>
      {hasLegacyValue && (
        <span
          title="This value was previously recorded but is no longer offered as an option. The stored value has not been changed."
          className="ml-1 inline-block rounded-full border border-dashed border-rnica-orange px-2 py-[2px] text-[10px] font-semibold leading-[1.6] text-rnica-orange whitespace-nowrap"
        >
          ⚠ Previously recorded: “{displayValue}”
        </span>
      )}
    </div>
  );
}

// Compact multi-select pill row, opt-in via `type: "pillGroup"`. Same
// array-value/onChange contract as FormCheckboxGroup (untouched, still
// used everywhere else) -- purely a denser visual for Body Systems.
function FormPillGroup({ label, values = [], onChange, options, hopeCode }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>
        {label}
        {hopeCode && <> <HopeTag code={hopeCode} /></>}
      </label>
      {/* shadcn/ui ToggleGroup (Radix), type="multiple" -- independent
          multi-select findings/interventions chip row. */}
      <ToggleGroup type="multiple" aria-label={label} value={values} onValueChange={(v) => onChange(v ?? [])}>
        {options.map((opt) => {
          const val = typeof opt === "string" ? opt : opt.value;
          const lbl = typeof opt === "string" ? opt : opt.label;
          return (
            <ToggleGroupItem key={val} value={val}>
              {lbl}
            </ToggleGroupItem>
          );
        })}
      </ToggleGroup>
    </div>
  );
}


function FormCheckbox({ label, checked, onChange, disabled = false }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return (
    <label style={{ ...styles.checkboxLabel, ...styles.formGroup, opacity: disabled ? 0.55 : 1, cursor: disabled ? "not-allowed" : "pointer" }}>
      <Checkbox checked={checked || false} disabled={disabled} onCheckedChange={onChange} />
      <span style={{ fontSize: 13, fontWeight: 500 }}>{label}</span>
    </label>
  );
}

// GitHub UI Directive (2026-09-28) -- "checkbox should never be larger
// than the text it represents." Single yes/no findings (e.g. "Motor
// Deficit Present") no longer render as a large square Checkbox next to
// a separate label; they render as one compact toggle pill, same visual
// language/size as FormSegmented/FormPillGroup. Same boolean value/
// onChange(bool) contract as FormCheckbox -- no data shape change.
function FormBooleanPill({ label, checked, onChange, disabled = false }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const isChecked = Boolean(checked);
  return (
    <button
      type="button" aria-pressed={isChecked} disabled={disabled}
      className="rnica-segment-btn"
      onClick={() => onChange(!isChecked)}
      style={{
        padding: "2px 9px", fontSize: 11, lineHeight: 1.6, borderRadius: 999,
        cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.55 : 1,
        border: `1px solid ${isChecked ? COLORS.teal : COLORS.border}`,
        background: isChecked ? COLORS.teal : "transparent",
        color: isChecked ? COLORS.textOnTeal : COLORS.dark,
        fontWeight: isChecked ? 700 : 500, whiteSpace: "nowrap",
      }}
    >
      {label}
    </button>
  );
}

const LCD_AUTO_FACT_FIELDS = new Set([
  "pps",
  "kps",
  "nyha_class",
  "fast_stage_at_or_beyond_7a",
  "fast_stage",
  "adl_dependency_count",
  "ambulation_assistance_required",
  "dressing_assistance_required",
  "bathing_assistance_required",
  "incontinence_or_catheter_ostomy_dependency",
  "is_bedbound",
  "dysphagia",
  "oral_intake_decline",
  "weight_loss_percent_6_months",
  "weight_loss_lbs",
  "continued_weight_loss",
  "o2_sat_percent",
  "resting_tachycardia_gt_100",
]);

function normalizeLcdNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const match = String(value).replace(/,/g, "").match(/-?\d+(\.\d+)?/);
  return match ? Number(match[0]) : null;
}

function normalizeFastStage(value) {
  return value ? String(value).trim().toLowerCase() : "";
}

function fastStageAtOrBeyond7a(value) {
  const order = {
    "1": 10, "2": 20, "3": 30, "4": 40, "5": 50,
    "6a": 61, "6b": 62, "6c": 63, "6d": 64, "6e": 65,
    "7a": 71, "7b": 72, "7c": 73, "7d": 74, "7e": 75, "7f": 76,
  };
  const key = normalizeFastStage(value);
  return key ? (order[key] || 0) >= order["7a"] : null;
}

function parseWeightLoss(value) {
  if (!value) return { lbs: null, percent: null };
  const num = normalizeLcdNumber(value);
  if (num === null) return { lbs: null, percent: null };
  if (String(value).includes("%")) return { lbs: null, percent: num };
  return { lbs: num, percent: null };
}

function normalizeYesNoUnknown(value) {
  if (value === true || value === false) return value;
  if (value === null || value === undefined || value === "") return null;
  const normalized = String(value).trim().toLowerCase();
  if (["true", "yes", "y", "1"].includes(normalized)) return true;
  if (["false", "no", "n", "0"].includes(normalized)) return false;
  return null;
}

function getValueByPath(obj, path) {
  return path.split(".").reduce((curr, key) => curr?.[key], obj);
}

// Recursively counts, for a section's saved data vs. its blank INITIAL_FORM
// default, how many individual leaf fields (scalars/booleans/flat arrays)
// actually hold RN-entered content vs. how many total leaf fields the
// section defines. This replaces the old "does ANYTHING differ from
// blank" check (which marked a 30-field section "Complete" because 1
// field changed) with a real documentation-completeness ratio, without
// hardcoding per-section field lists -- it walks whatever shape
// INITIAL_FORM[section] defines, so it stays correct as sections evolve.
//
// - Plain objects: recurse into each key and sum leaf counts.
// - Arrays of objects with a stable default length (e.g. the 16-item HOPE
//   education-topics scaffold, or per-item DME/equipment lists) are walked
//   element-by-element so real per-row documentation (a topic actually
//   marked taught/understood, an item's status actually set) counts,
//   instead of the array's mere existence counting as "populated."
// - Any other array is one leaf field, populated if it has any entries.
// - Scalars/booleans/strings are one leaf field each, populated if they
//   differ from the blank default (non-empty string, non-null, etc).
function countSectionCompletion(current, initial) {
  if (Array.isArray(initial)) {
    const allObjects = initial.length > 0 && initial.every((item) => item && typeof item === "object" && !Array.isArray(item));
    if (allObjects && Array.isArray(current) && current.length === initial.length) {
      return initial.reduce(
        (acc, initialItem, idx) => {
          const sub = countSectionCompletion(current[idx], initialItem);
          return { total: acc.total + sub.total, populated: acc.populated + sub.populated };
        },
        { total: 0, populated: 0 }
      );
    }
    const hasEntries = Array.isArray(current) && current.length > 0;
    return { total: 1, populated: hasEntries ? 1 : 0 };
  }
  if (initial && typeof initial === "object") {
    return Object.keys(initial).reduce(
      (acc, key) => {
        const sub = countSectionCompletion(current?.[key], initial[key]);
        return { total: acc.total + sub.total, populated: acc.populated + sub.populated };
      },
      { total: 0, populated: 0 }
    );
  }
  const isBlank = current === initial || current === "" || current === null || current === undefined;
  return { total: 1, populated: isBlank ? 0 : 1 };
}

// A section only earns the "Complete" badge once a meaningful share of its
// fields are actually documented -- not merely different from blank in one
// spot. 0.5 (half the section's fields) is the bar for "Complete"; any
// nonzero-but-below-threshold documentation is surfaced as "In Progress"
// instead of silently staying "Not started" or falsely reading "Complete".
const SECTION_COMPLETION_RATIO_THRESHOLD = 0.5;

function getSectionCompletionState(current, initial) {
  const { total, populated } = countSectionCompletion(current, initial);
  const ratio = total > 0 ? populated / total : 0;
  if (populated === 0) return { status: "not_started", ratio, populated, total };
  if (ratio >= SECTION_COMPLETION_RATIO_THRESHOLD) return { status: "complete", ratio, populated, total };
  return { status: "in_progress", ratio, populated, total };
}

function formatLcdRule(rule) {
  switch ((rule || "").toUpperCase()) {
    case "ALL_REQUIRED": return "ALL must be met";
    case "ANY_REQUIRED": return "ANY ONE may satisfy";
    case "ANY_3_REQUIRED": return "ANY 3 must be met";
    default: return rule || "Rule";
  }
}

function formatActualValue(value) {
  if (value === null || value === undefined || value === "") return "Unknown";
  if (value === true) return "Yes";
  if (value === false) return "No";
  return String(value);
}

function isCriteriaAnswerField(field) {
  return String(field || "").startsWith("criteria_answers.");
}

function buildClientLcdFacts(formData) {
  const weightLoss = parseWeightLoss(formData?.nutrition?.weightLossPastSixMonths);
  const adlValues = [
    formData?.musculoskeletal?.adl?.bathing,
    formData?.musculoskeletal?.adl?.dressing,
    formData?.musculoskeletal?.adl?.toileting,
    formData?.musculoskeletal?.adl?.transferring,
    formData?.musculoskeletal?.adl?.eating,
    formData?.musculoskeletal?.adl?.grooming,
  ]
    .map((value) => normalizeLcdNumber(value))
    .filter((value) => value !== null);
  const adlDependencyCount = adlValues.length
    ? adlValues.filter((value) => value >= 3).length
    : null;
  const swallowingIssues = formData?.nutrition?.swallowingIssues || [];
  const urinaryStatus = (formData?.genitourinary?.urinaryStatus || "").toLowerCase();
  const bowelStatus = (formData?.gastrointestinal?.bowelStatus || "").toLowerCase();
  const mobilityStatus = (formData?.musculoskeletal?.mobility?.ambulatoryStatus || "").toLowerCase();
  const pulse = normalizeLcdNumber(formData?.vitals?.pulse);
  const pps = normalizeLcdNumber(formData?.performanceStatus?.pps);
  const kps = normalizeLcdNumber(formData?.performanceStatus?.kps);
  const dressingScore = normalizeLcdNumber(formData?.musculoskeletal?.adl?.dressing);
  const bathingScore = normalizeLcdNumber(formData?.musculoskeletal?.adl?.bathing);
  const hasContinenceEvidence = Boolean(urinaryStatus || bowelStatus || formData?.genitourinary?.catheter?.present || formData?.gastrointestinal?.ostomy?.present);
  const hasWeightLossEvidence = weightLoss.lbs !== null || weightLoss.percent !== null;

  return {
    pps,
    kps,
    nyha_class: formData?.performanceStatus?.nyha || null,
    fast_stage: normalizeFastStage(formData?.performanceStatus?.fast),
    fast_stage_at_or_beyond_7a: fastStageAtOrBeyond7a(formData?.performanceStatus?.fast),
    weight_loss_lbs: weightLoss.lbs,
    weight_loss_percent_6_months: weightLoss.percent,
    continued_weight_loss: hasWeightLossEvidence ? (weightLoss.lbs ?? weightLoss.percent) > 0 : null,
    adl_dependency_count: adlDependencyCount,
    ambulation_assistance_required: mobilityStatus ? ["assisted", "dependent", "bedbound"].includes(mobilityStatus) : null,
    dressing_assistance_required: dressingScore !== null ? dressingScore >= 3 : null,
    bathing_assistance_required: bathingScore !== null ? bathingScore >= 3 : null,
    incontinence_or_catheter_ostomy_dependency: hasContinenceEvidence
      ? (
          ["stress incontinence", "urge incontinence", "functional incontinence", "total incontinence", "catheterized"].includes(urinaryStatus)
          || bowelStatus === "incontinent"
          || Boolean(formData?.genitourinary?.catheter?.present)
          || Boolean(formData?.gastrointestinal?.ostomy?.present)
        )
      : null,
    is_bedbound: mobilityStatus ? mobilityStatus === "bedbound" : null,
    dysphagia: swallowingIssues.includes("Dysphagia"),
    oral_intake_decline:
      ["poor", "anorexic"].includes((formData?.nutrition?.appetite || "").toLowerCase())
      || ["decreased", "minimal"].includes((formData?.nutrition?.fluidIntake || "").toLowerCase()),
    o2_sat_percent: normalizeLcdNumber(formData?.vitals?.oxygenSaturation) ?? normalizeLcdNumber(formData?.respiratory?.oxygenTherapy?.satOnO2),
    resting_tachycardia_gt_100: pulse !== null ? pulse > 100 : null,
    serum_albumin: normalizeLcdNumber(formData?.diagnoses?.ndsEligibility?.criteriaFacts?.[formData?.diagnoses?.ndsEligibility?.detectedDisease || ""]?.serum_albumin),
    serum_creatinine: normalizeLcdNumber(formData?.diagnoses?.ndsEligibility?.criteriaFacts?.[formData?.diagnoses?.ndsEligibility?.detectedDisease || ""]?.serum_creatinine),
    creatinine_clearance: normalizeLcdNumber(formData?.diagnoses?.ndsEligibility?.criteriaFacts?.[formData?.diagnoses?.ndsEligibility?.detectedDisease || ""]?.creatinine_clearance),
    gfr: normalizeLcdNumber(formData?.diagnoses?.ndsEligibility?.criteriaFacts?.[formData?.diagnoses?.ndsEligibility?.detectedDisease || ""]?.gfr),
    po2: normalizeLcdNumber(formData?.diagnoses?.ndsEligibility?.criteriaFacts?.[formData?.diagnoses?.ndsEligibility?.detectedDisease || ""]?.po2),
    pco2: normalizeLcdNumber(formData?.diagnoses?.ndsEligibility?.criteriaFacts?.[formData?.diagnoses?.ndsEligibility?.detectedDisease || ""]?.pco2),
    ejection_fraction: normalizeLcdNumber(formData?.diagnoses?.ndsEligibility?.criteriaFacts?.[formData?.diagnoses?.ndsEligibility?.detectedDisease || ""]?.ejection_fraction),
    cd4_count: normalizeLcdNumber(formData?.diagnoses?.ndsEligibility?.criteriaFacts?.[formData?.diagnoses?.ndsEligibility?.detectedDisease || ""]?.cd4_count),
    viral_load: normalizeLcdNumber(formData?.diagnoses?.ndsEligibility?.criteriaFacts?.[formData?.diagnoses?.ndsEligibility?.detectedDisease || ""]?.viral_load),
  };
}

function buildLcdEvaluationPayload(formData, disease) {
  const criteriaAnswers = formData?.diagnoses?.ndsEligibility?.criteriaAnswers?.[disease] || {};
  const criteriaFacts = formData?.diagnoses?.ndsEligibility?.criteriaFacts?.[disease] || {};
  const facts = {
    ...buildClientLcdFacts(formData),
    ...criteriaFacts,
    criteria_answers: disease ? { [disease]: criteriaAnswers } : {},
  };

  return {
    patient: {
      ...formData,
      assessment: formData,
      disease,
      primary_diagnosis_description: formData?.diagnoses?.primaryDiagnosis?.description || "",
      primary_diagnosis_code: formData?.diagnoses?.primaryDiagnosis?.icd10 || "",
    },
    facts,
  };
}

function LcdTernaryButtons({ value, onChange, COLORS }) {
  const options = [
    { key: true, label: "Yes" },
    { key: false, label: "No" },
    { key: null, label: "Unknown" },
  ];
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {options.map((option) => {
        const active = value === option.key;
        return (
          <button
            key={String(option.key)}
            type="button"
            onClick={() => onChange(option.key)}
            style={{
              padding: "4px 10px",
              borderRadius: 999,
              border: `1px solid ${active ? COLORS.teal : COLORS.border}`,
              background: active ? COLORS.tealBg : COLORS.white,
              color: COLORS.dark,
              fontSize: 12,
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

function LcdEligibilityCard({ diagnosesData, fullFormData, updateField, styles, COLORS, workspacePilot = false }) {
  const diagnosisText = `${diagnosesData?.primaryDiagnosis?.icd10 || ""} ${diagnosesData?.primaryDiagnosis?.description || ""}`.trim();
  const detectedDisease = diagnosesData?.ndsEligibility?.detectedDisease || "";
  const criteriaAnswers = diagnosesData?.ndsEligibility?.criteriaAnswers?.[detectedDisease] || {};
  const criteriaFacts = diagnosesData?.ndsEligibility?.criteriaFacts?.[detectedDisease] || {};
  const [config, setConfig] = useState(null);
  const [configLoading, setConfigLoading] = useState(false);
  const [configError, setConfigError] = useState("");
  const [evaluation, setEvaluation] = useState(null);
  const [evaluationLoading, setEvaluationLoading] = useState(false);
  const [evaluationError, setEvaluationError] = useState("");

  const updateDiagnoses = useCallback((path, value) => {
    updateField(path, value);
  }, [updateField]);

  useEffect(() => {
    if (!diagnosisText) {
      if (detectedDisease) updateDiagnoses("ndsEligibility.detectedDisease", "");
      setConfig(null);
      setEvaluation(null);
      setConfigError("");
      return;
    }

    const handle = window.setTimeout(async () => {
      try {
        const detected = await detectLCD(diagnosisText);
        if (detected?.disease && detected.disease !== detectedDisease) {
          updateDiagnoses("ndsEligibility.detectedDisease", detected.disease);
        }
      } catch (error) {
        console.error("LCD disease detection failed:", error);
        setConfigError(error instanceof Error ? error.message : "Unable to detect LCD disease.");
      }
    }, 250);

    return () => window.clearTimeout(handle);
  }, [diagnosisText, detectedDisease, updateDiagnoses]);

  useEffect(() => {
    if (!detectedDisease) {
      setConfig(null);
      return;
    }

    let active = true;
    setConfigLoading(true);
    setConfigError("");
    getLCDConfig(detectedDisease)
      .then((data) => {
        if (active) setConfig(data);
      })
      .catch((error) => {
        if (!active) return;
        console.error("LCD config load failed:", error);
        setConfig(null);
        setConfigError(error instanceof Error ? error.message : "Unable to load LCD config.");
      })
      .finally(() => {
        if (active) setConfigLoading(false);
      });

    return () => {
      active = false;
    };
  }, [detectedDisease]);

  const evaluationPayload = useMemo(
    () => (detectedDisease ? buildLcdEvaluationPayload(fullFormData, detectedDisease) : null),
    [fullFormData, detectedDisease],
  );

  useEffect(() => {
    if (!detectedDisease || !config || !evaluationPayload) {
      setEvaluation(null);
      return;
    }

    let active = true;
    const handle = window.setTimeout(async () => {
      setEvaluationLoading(true);
      setEvaluationError("");
      try {
        const result = await evaluateLCD(
          evaluationPayload.patient,
          evaluationPayload.facts,
        );
        if (active) setEvaluation(result);
      } catch (error) {
        if (!active) return;
        console.error("LCD evaluation failed:", error);
        setEvaluation(null);
        setEvaluationError(error instanceof Error ? error.message : "Unable to evaluate LCD eligibility.");
      } finally {
        if (active) setEvaluationLoading(false);
      }
    }, 250);

    return () => {
      active = false;
      window.clearTimeout(handle);
    };
  }, [detectedDisease, config, evaluationPayload]);

  const setCriteriaAnswer = useCallback((criterionId, value) => {
    updateDiagnoses(`ndsEligibility.criteriaAnswers.${detectedDisease}.${criterionId}`, value);
  }, [detectedDisease, updateDiagnoses]);

  const setCriteriaFact = useCallback((field, value) => {
    updateDiagnoses(`ndsEligibility.criteriaFacts.${detectedDisease}.${field}`, value);
  }, [detectedDisease, updateDiagnoses]);

  const groupResults = evaluation?.criteria_summary?.group_results || [];
  const criterionDetails = useMemo(() => {
    const map = new Map();
    groupResults.forEach((group) => {
      (group.criteria || []).forEach((criterion) => {
        map.set(`${group.group_id}:${criterion.criterion_id}`, criterion);
      });
    });
    return map;
  }, [groupResults]);

  const groupSummaries = useMemo(() => {
    return (config?.criteria_groups || []).map((group) => {
      let met = 0;
      let unmet = 0;
      let unknown = 0;
      (group.criteria || []).forEach((criterion) => {
        const detail = criterionDetails.get(`${group.group_id}:${criterion.criterion_id}`);
        if (!detail || detail.actual === null || detail.actual === undefined || detail.actual === "") {
          unknown += 1;
        } else if (detail.matched) {
          met += 1;
        } else {
          unmet += 1;
        }
      });
      return { group, met, unmet, unknown };
    });
  }, [config, criterionDetails]);
  const criterionSummary = useMemo(
    () => groupSummaries.reduce(
      (summary, group) => ({
        met: summary.met + group.met,
        unmet: summary.unmet + group.unmet,
        unknown: summary.unknown + group.unknown,
      }),
      { met: 0, unmet: 0, unknown: 0 },
    ),
    [groupSummaries],
  );
  const orderedGroupSummaries = useMemo(
    () => workspacePilot
      ? [...groupSummaries].sort((a, b) => {
          const aNeedsReview = a.unmet + a.unknown > 0 ? 0 : 1;
          const bNeedsReview = b.unmet + b.unknown > 0 ? 0 : 1;
          return aNeedsReview - bNeedsReview;
        })
      : groupSummaries,
    [groupSummaries, workspacePilot],
  );
  const [expandedGroups, setExpandedGroups] = useState(() => new Set());
  const [collapsedGroups, setCollapsedGroups] = useState(() => new Set());
  useEffect(() => {
    setExpandedGroups(new Set());
    setCollapsedGroups(new Set());
  }, [detectedDisease]);
  const toggleGroup = (groupId, isOpen) => {
    if (isOpen) {
      setExpandedGroups((current) => {
        const next = new Set(current);
        next.delete(groupId);
        return next;
      });
      setCollapsedGroups((current) => new Set(current).add(groupId));
      return;
    }
    setCollapsedGroups((current) => {
      const next = new Set(current);
      next.delete(groupId);
      return next;
    });
    setExpandedGroups((current) => new Set(current).add(groupId));
  };

  const supplementalValueFor = (field) => criteriaFacts?.[field] ?? "";
  const currentFacts = evaluationPayload?.facts || {};

  const renderCriterionInput = (criterion) => {
    if (isCriteriaAnswerField(criterion.field)) {
      return (
        <LcdTernaryButtons
          value={normalizeYesNoUnknown(criteriaAnswers?.[criterion.criterion_id])}
          onChange={(value) => setCriteriaAnswer(criterion.criterion_id, value)}
          COLORS={COLORS}
        />
      );
    }

    if (LCD_AUTO_FACT_FIELDS.has(criterion.field)) {
      const detail = criterionDetails.get(`${criterion.group_id}:${criterion.criterion_id}`);
      return (
        <div style={{ fontSize: 12, color: COLORS.gray, lineHeight: 1.45 }}>
          <div><strong style={{ color: COLORS.dark }}>{detail?.matched ? "✓ Met" : "✗ Not met"}</strong> — current value: {formatActualValue(detail?.actual ?? currentFacts?.[criterion.field])}</div>
          <div>Auto-filled from other RNICA sections.</div>
        </div>
      );
    }

    if (typeof criterion.expected === "number" && ["LT", "LTE", "GT", "GTE"].includes(String(criterion.operator || "").toUpperCase())) {
      return (
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <input
            type="number"
            value={supplementalValueFor(criterion.field)}
            onChange={(event) => setCriteriaFact(criterion.field, event.target.value === "" ? "" : Number(event.target.value))}
            style={{ ...styles.input, width: 120, padding: "5px 8px" }}
          />
          <button
            type="button"
            onClick={() => setCriteriaFact(criterion.field, "")}
            style={{ ...styles.btnSecondary, padding: "5px 10px", fontSize: 12 }}
          >
            Unknown
          </button>
        </div>
      );
    }

    return (
      <LcdTernaryButtons
        value={normalizeYesNoUnknown(criteriaFacts?.[criterion.field])}
        onChange={(value) => setCriteriaFact(criterion.field, value)}
        COLORS={COLORS}
      />
    );
  };

  return (
    <div>
      {!diagnosisText && (
        <div style={{ ...styles.infoBox, marginBottom: 10 }}>
          Enter the primary diagnosis ICD-10 and/or description above to load the matching LCD disease-specific criteria.
        </div>
      )}

      {diagnosisText && (
        <div className={workspacePilot ? "rnica-lcd-summary" : undefined} style={{ ...styles.infoBox, marginBottom: 10, padding: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
            <div>
              <div style={{ fontWeight: 800, marginBottom: 2 }}>
                {detectedDisease ? detectedDisease.replaceAll("_", " ") : "Detecting LCD disease..."}
              </div>
              {config?.lcd_reference && <div style={{ fontSize: 12, color: COLORS.gray }}>{config.lcd_reference}</div>}
            </div>
            <div style={{
              ...styles.statusBadge,
              background: evaluation?.eligible ? COLORS.successBoxBg : COLORS.warningBoxBg,
              color: COLORS.dark,
              border: `1px solid ${evaluation?.eligible ? "rgba(16,185,129,0.26)" : "rgba(245,158,11,0.3)"}`,
            }}>
              {evaluationLoading ? "Evaluating..." : evaluation?.eligible ? "Eligible" : "Not eligible"}
            </div>
          </div>
          {workspacePilot && (
            <div className="rnica-lcd-summary__counts" aria-label="LCD criterion summary">
              <span><strong>{criterionSummary.met}</strong> met</span>
              <span><strong>{criterionSummary.unmet}</strong> unmet</span>
              <span><strong>{criterionSummary.unknown}</strong> unknown</span>
            </div>
          )}
          {config?.source_document && <div style={{ fontSize: 11, color: COLORS.gray, marginTop: 6 }}>Source: {config.source_document}</div>}
        </div>
      )}

      {(configError || evaluationError) && (
        <div style={{ ...styles.warningBox, marginBottom: 10, padding: 12 }}>
          {configError || evaluationError}
        </div>
      )}

      {configLoading && <div style={{ fontSize: 12, color: COLORS.gray, marginBottom: 8 }}>Loading LCD criteria…</div>}

      {orderedGroupSummaries.map(({ group, met, unmet, unknown }) => {
        const groupResult = groupResults.find((item) => item.group_id === group.group_id);
        const needsReview = unmet + unknown > 0;
        // FR-007: LCD groups are collapsed by default in the pilot
        // workspace -- expand only on explicit RN toggle. (Previously a
        // group needing review auto-expanded; the owner directive is
        // explicit that collapsed-by-default applies unconditionally, so
        // the RN reviews the met/unmet/unknown counts first and opens a
        // group deliberately.)
        const groupOpen = !workspacePilot || expandedGroups.has(group.group_id);
        const groupBadges = (
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            {workspacePilot && <span className="rnica-lcd-group__count">{met} met · {unmet} unmet · {unknown} unknown</span>}
            <span style={styles.cmsTag}>{formatLcdRule(group.rule)}</span>
            {groupResult && (
              <span style={{
                ...styles.statusBadge,
                padding: "3px 8px",
                background: groupResult.passed ? COLORS.successBoxBg : COLORS.warningBoxBg,
                color: COLORS.dark,
                border: `1px solid ${groupResult.passed ? "rgba(16,185,129,0.26)" : "rgba(245,158,11,0.3)"}`,
              }}>
                {groupResult.passed ? "Pass" : "Fail"}
              </span>
            )}
          </div>
        );
        return (
          <div
            key={group.group_id}
            className={workspacePilot ? `rnica-lcd-group ${needsReview ? "needs-review" : "is-satisfied"}` : undefined}
            style={{
              border: `1px solid ${COLORS.border}`,
              borderRadius: 10,
              padding: 10,
              marginBottom: 10,
              background: COLORS.bg,
            }}
          >
            {workspacePilot ? (
              <button type="button" className="rnica-lcd-group__toggle" aria-expanded={groupOpen} onClick={() => toggleGroup(group.group_id, groupOpen)}>
                <span>{groupOpen ? "▾" : "▸"} {group.group_name}</span>
                {groupBadges}
              </button>
            ) : (
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center", marginBottom: 8, flexWrap: "wrap" }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: COLORS.dark }}>{group.group_name}</div>
                {groupBadges}
              </div>
            )}
            {groupOpen && <div className={workspacePilot ? "rnica-lcd-criteria" : undefined} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {(group.criteria || []).map((criterion) => {
                const detail = criterionDetails.get(`${group.group_id}:${criterion.criterion_id}`);
                const criterionWithGroup = { ...criterion, group_id: group.group_id };
                return (
                  <div
                    key={criterion.criterion_id}
                    className={workspacePilot ? "rnica-lcd-criterion" : undefined}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "minmax(0, 1fr) auto",
                      gap: 10,
                      alignItems: "center",
                      padding: "8px 10px",
                      borderRadius: 8,
                      border: `1px solid ${COLORS.border}`,
                      background: COLORS.white,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 12.5, fontWeight: 700, color: COLORS.dark }}>{criterion.criterion_id}. {criterion.description}</div>
                      {detail && (
                        <div style={{ fontSize: 11, color: COLORS.gray, marginTop: 3 }}>
                          Current: {formatActualValue(detail.actual)} • Expected: {formatActualValue(detail.expected)}
                        </div>
                      )}
                    </div>
                    <div style={{ minWidth: 180 }}>
                      {renderCriterionInput(criterionWithGroup)}
                    </div>
                  </div>
                );
              })}
            </div>}
          </div>
        );
      })}
      {!workspacePilot && (
        <div>
          <FormTextarea
            label="LCD supporting evidence"
            value={diagnosesData?.lcdEligibilityNarrative || ""}
            onChange={(value) => updateDiagnoses("lcdEligibilityNarrative", value)}
            placeholder="Document evidence specific to the selected LCD guideline. This is not the whole-patient clinical narrative."
            rows={4}
          />
        </div>
      )}
    </div>
  );
}

// In the pilot workflow, structured checklists (LCD criteria, secondary
// diagnoses, comorbidities) render first; this free-text LCD evidence card
// renders last on the Diagnoses page so no narrative sits mid-page.
function LcdSupportingEvidenceCard({ diagnosesData, updateField }) {
  return (
    <div className="rnica-lcd-evidence">
      <FormTextarea
        label="LCD supporting evidence"
        value={diagnosesData?.lcdEligibilityNarrative || ""}
        onChange={(value) => updateField("lcdEligibilityNarrative", value)}
        placeholder="Document evidence specific to the selected LCD guideline. This is not the whole-patient clinical narrative."
        rows={4}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// SECTION 10 — Clinical Narrative & Disease Trajectory.
//
// This card is deliberately separate from LcdEligibilityCard /
// lcdEligibilityNarrative (distinct field, distinct purpose — the RN's
// documented clinical findings narrative vs. the physician's LCD
// eligibility-support narrative). The deterministic
// buildClinicalNarrative() template renderer runs ONLY on an explicit
// "Build Draft from Documented Findings" click — never on mount, never
// on formData changes, never during save/validation/navigation. No AI
// service, AI flag, or AI control exists anywhere in this card.
// ════════════════════════════════════════════════════════════════
function ClinicalNarrativeCard({ diagnosesData, fullFormData, updateField, styles, COLORS, locked }) {
  const [pendingReplace, setPendingReplace] = useState(false);
  const narrative = diagnosesData?.clinicalNarrative || "";
  const trajectory = diagnosesData?.diseaseTrajectory || "";
  const isLegacyTrajectory = isLegacyDiseaseTrajectoryValue(trajectory);

  const handleBuildDraft = () => {
    if (narrative.trim()) {
      setPendingReplace(true);
      return;
    }
    applyDraft();
  };

  const applyDraft = () => {
    const draft = buildClinicalNarrative(fullFormData, {});
    updateField("clinicalNarrative", draft.text);
    // Replacing the narrative content always resets review — a
    // previously reviewed narrative cannot remain "reviewed" once its
    // text has changed.
    updateField("clinicalNarrativeReviewed", false);
    setPendingReplace(false);
  };

  const handleNarrativeChange = (value) => {
    updateField("clinicalNarrative", value);
    updateField("clinicalNarrativeReviewed", false);
  };

  return (
    <div>
      <div style={styles.formGroup}>
        <label style={styles.label}>Disease Trajectory</label>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {DISEASE_TRAJECTORY_OPTIONS.map((opt) => (
            <label key={opt.value} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLORS.dark }}>
              <input
                type="radio"
                name="diseaseTrajectory"
                value={opt.value}
                checked={trajectory === opt.value}
                disabled={locked}
                onChange={() => updateField("diseaseTrajectory", opt.value)}
              />
              {opt.label}
            </label>
          ))}
        </div>
        {isLegacyTrajectory && (
          <div style={{ marginTop: 6, fontSize: 12, color: COLORS.warning }}>
            Legacy value on file: "{trajectory}". This was recorded before the current trajectory options existed and is not
            automatically converted — please review and select one of the options above.
          </div>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
        <FormInput
          label="Recent Hospitalizations (count)"
          type="number"
          value={diagnosesData?.recentHospitalizations ?? ""}
          onChange={(v) => updateField("recentHospitalizations", v)}
          disabled={locked}
          min={0}
          step={1}
          placeholder="Leave blank if not documented"
        />
        <FormInput
          label="Recent Emergency Department Visits (count)"
          type="number"
          value={diagnosesData?.recentErVisits ?? ""}
          onChange={(v) => updateField("recentErVisits", v)}
          disabled={locked}
          min={0}
          step={1}
          placeholder="Leave blank if not documented"
        />
      </div>
      <FormTextarea
        label="Utilization Notes"
        value={diagnosesData?.utilizationNotes}
        onChange={(v) => updateField("utilizationNotes", v)}
        rows={2}
        disabled={locked}
      />

      <div style={{ marginTop: 12, marginBottom: 8 }}>
        <button
          type="button"
          style={{ ...styles.btnSecondary, opacity: locked ? 0.5 : 1 }}
          onClick={handleBuildDraft}
          disabled={locked}
        >
          Build Draft from Documented Findings
        </button>
        <span style={{ marginLeft: 10, fontSize: 11.5, color: COLORS.gray }}>
          Assembles a draft strictly from already-documented fields on this assessment. It never runs automatically and never
          determines eligibility, prognosis, or disease trajectory.
        </span>
      </div>

      {pendingReplace && (
        <div style={{
          padding: 10, borderRadius: 8, border: `1px solid ${COLORS.warning}`,
          background: COLORS.warningBoxBg, marginBottom: 10, fontSize: 12.5, color: COLORS.dark,
        }}>
          <div style={{ marginBottom: 8 }}>A clinical narrative already exists. Building a new draft will replace the current text.</div>
          <button type="button" style={styles.btnSecondary} onClick={() => setPendingReplace(false)}>Keep Existing Narrative</button>
          <button type="button" style={{ ...styles.btnPrimary, marginLeft: 8 }} onClick={applyDraft}>Replace with New Draft</button>
        </div>
      )}

      <FormTextarea
        label="Diagnoses Narrative"
        value={narrative}
        onChange={handleNarrativeChange}
        rows={10}
        disabled={locked}
        placeholder="Document the patient's clinical presentation and supporting findings in your own words, or click Build Draft from Documented Findings above."
      />

      <div style={{ display: "flex", alignItems: "center", gap: 8, margin: "8px 0 16px" }}>
        <input
          type="checkbox"
          id="clinicalNarrativeReviewed"
          checked={!!diagnosesData?.clinicalNarrativeReviewed}
          disabled={locked}
          onChange={(e) => updateField("clinicalNarrativeReviewed", e.target.checked)}
        />
        <label htmlFor="clinicalNarrativeReviewed" style={{ fontSize: 13, color: COLORS.dark }}>
          I reviewed this narrative and verified that it matches the documented assessment findings.
        </label>
      </div>

      <FormTextarea
        label="RN Addendum"
        value={diagnosesData?.rnAddendum}
        onChange={(v) => updateField("rnAddendum", v)}
        rows={3}
        disabled={locked}
      />
      <FormTextarea
        label="Clinician Clarification"
        value={diagnosesData?.clinicianClarification}
        onChange={(v) => updateField("clinicianClarification", v)}
        rows={3}
        disabled={locked}
      />
      {locked && (
        <div style={{ fontSize: 11.5, color: COLORS.gray }}>
          This assessment is locked/authenticated. Section 10 fields are read-only. Additional post-authentication information
          must be captured as a distinct, traceable, authenticated addendum record — a documented gap in current SNS EMR
          infrastructure, not implemented as an editable field on this locked assessment.
        </div>
      )}
    </div>
  );
}

// A single secondary-diagnosis row's search box, mirroring
// PrimaryTerminalDiagnosisCard's merged "Search Diagnosis or ICD-10"
// control -- one Icd10DiagnosisInput fills both icd10 + description in
// one action instead of two separate manually-typed fields. Extracted to
// its own component (rather than inline in the rows.map below) so each
// row can hold its own local "what the RN is currently typing" state
// without violating the rules of hooks across a dynamic-length list.
function SecondaryDiagnosisSearchRow({ row, idx, updateRow, removeRow, styles, COLORS }) {
  const [searchText, setSearchText] = useState(() => (
    row.description ? `${row.description}${row.icd10 ? ` (${formatIcd10Code(row.icd10)})` : ""}` : formatIcd10Code(row.icd10 || "")
  ));

  const handleSelectSuggestion = (suggestion) => {
    updateRow(idx, "icd10", suggestion.icd10_code);
    updateRow(idx, "description", suggestion.diagnosis_description);
  };

  return (
    <div className="rnica-diagnosis-ledger__row" role="row">
      <div role="cell">
        <Icd10DiagnosisInput
          value={searchText}
          onChange={setSearchText}
          onSelectSuggestion={handleSelectSuggestion}
          colors={{ cardBg: COLORS.white, border: COLORS.border, label: COLORS.gray, white: COLORS.dark }}
          inputStyle={styles.input}
          placeholder="Search diagnosis or ICD-10…"
        />
      </div>
      <label role="cell" className="rnica-diagnosis-ledger__related">
        <input
          type="checkbox"
          checked={row.relatedToTerminal !== false}
          onChange={(event) => updateRow(idx, "relatedToTerminal", event.target.checked)}
        />
        <span>{row.relatedToTerminal !== false ? "Related" : "Not related"}</span>
      </label>
      <div role="cell">
        <button type="button" className="rnica-diagnosis-ledger__remove" onClick={() => removeRow(idx)}>
          Remove
        </button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// SECONDARY DIAGNOSES — add/edit/remove list (feeds HOPE comorbidity
// auto-detection below and hopeReportMapper.js diagnosisEntries()).
// ════════════════════════════════════════════════════════════════
function SecondaryDiagnosesCard({ diagnosesData, updateField, styles, COLORS, workspacePilot = false }) {
  const rows = diagnosesData?.secondaryDiagnoses || [];
  const [showAll, setShowAll] = useState(false);
  const visibleRows = workspacePilot && !showAll ? rows.slice(0, 7) : rows;

  const setRows = (next) => updateField("secondaryDiagnoses", next);

  const addRow = () => {
    setRows([...rows, { icd10: "", description: "", relatedToTerminal: true }]);
    if (workspacePilot) setShowAll(true);
  };

  const updateRow = (idx, field, value) => {
    setRows(rows.map((row, i) => (i === idx ? { ...row, [field]: value } : row)));
  };

  const removeRow = (idx) => setRows(rows.filter((_, i) => i !== idx));

  if (workspacePilot) {
    return (
      <div className="rnica-diagnosis-ledger">
        <div className="rnica-diagnosis-ledger__summary">
          <p>
            Active diagnoses contributing to the plan of care. Related status does not add a diagnosis to the HOPE comorbidity checklist.
          </p>
          <strong>{rows.length} {rows.length === 1 ? "diagnosis" : "diagnoses"}</strong>
        </div>
        {rows.length === 0 ? (
          <div className="rnica-diagnosis-ledger__empty">No secondary diagnoses added yet.</div>
        ) : (
          <div className="rnica-diagnosis-ledger__table" role="table" aria-label="Secondary diagnoses">
            <div className="rnica-diagnosis-ledger__header" role="row">
              <span role="columnheader">Diagnosis</span>
              <span role="columnheader">Terminal related</span>
              <span role="columnheader">Action</span>
            </div>
            {visibleRows.map((row, idx) => (
              <SecondaryDiagnosisSearchRow
                key={idx}
                row={row}
                idx={idx}
                updateRow={updateRow}
                removeRow={removeRow}
                styles={styles}
                COLORS={COLORS}
              />
            ))}
          </div>
        )}
        <div className="rnica-diagnosis-ledger__actions">
          <button type="button" onClick={addRow}>+ Add secondary diagnosis</button>
          {rows.length > 7 && (
            <button type="button" onClick={() => setShowAll((current) => !current)} aria-expanded={showAll}>
              {showAll ? "Show fewer" : `Show all ${rows.length} diagnoses`}
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div>
      <p style={{ fontSize: 12, color: COLORS.gray, marginTop: -4, marginBottom: 10 }}>
        All other active diagnoses contributing to the plan of care. Marking a diagnosis as
        "related to terminal illness" is used for hospice benefit-period documentation and does
        not by itself add it to the HOPE comorbidity checklist below.
      </p>
      {rows.length === 0 && (
        <div style={{ fontSize: 12.5, color: COLORS.gray, fontStyle: "italic", marginBottom: 10 }}>
          No secondary diagnoses added yet.
        </div>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {rows.map((row, idx) => (
          <div
            key={idx}
            style={{
              display: "grid",
              gridTemplateColumns: "140px minmax(0, 1fr) auto auto",
              gap: 10,
              alignItems: "center",
              padding: "8px 10px",
              borderRadius: 8,
              border: `1px solid ${COLORS.border}`,
              background: COLORS.bg,
            }}
          >
            <input
              style={styles.input}
              placeholder="ICD-10"
              value={row.icd10 || ""}
              onChange={(e) => updateRow(idx, "icd10", e.target.value)}
            />
            <input
              style={styles.input}
              placeholder="Description"
              value={row.description || ""}
              onChange={(e) => updateRow(idx, "description", e.target.value)}
            />
            <label style={{ ...styles.checkboxLabel, whiteSpace: "nowrap" }}>
              <input
                type="checkbox"
                checked={row.relatedToTerminal !== false}
                onChange={(e) => updateRow(idx, "relatedToTerminal", e.target.checked)}
              />
              Related
            </label>
            <button type="button" style={{ ...styles.btnDanger, padding: "6px 10px" }} onClick={() => removeRow(idx)}>
              Remove
            </button>
          </div>
        ))}
      </div>
      <button type="button" style={{ ...styles.btnSecondary, marginTop: 10 }} onClick={addRow}>
        + Add Secondary Diagnosis
      </button>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// SKIN / WOUND — Structured wound documentation (Master Map §5.11).
// Each wound is a repeatable row capturing every §5.11 attribute.
// Wound Count is intentionally derived (rows.length), not a separate
// manual field, so it can never drift out of sync with the actual
// documented wounds (same "reuse, don't duplicate" rule applied to BMI).
// Pressure-relief measures and repositioning plan are plan-level (not
// per-wound) and are rendered as ordinary fields on the existing
// "Wound Documentation & Notes" card — see SECTION_CONFIGS.skin.
// ════════════════════════════════════════════════════════════════
const WOUND_STAGE_OPTIONS = [
  "Stage 1", "Stage 2", "Stage 3", "Stage 4",
  "Unstageable", "Deep Tissue Injury", "N/A",
];
const WOUND_TYPE_OPTIONS = [
  "Pressure injury", "Skin tear", "Surgical wound", "Venous ulcer",
  "Arterial ulcer", "Diabetic ulcer", "Nonhealing wound", "Other",
];
const WOUND_DRAINAGE_OPTIONS = ["None", "Scant", "Small", "Moderate", "Large"];
const WOUND_ODOR_OPTIONS = ["None", "Mild", "Foul"];

function WoundEntryCard({ wound, index, onChange, onRemove, styles, COLORS }) {
  const set = (field, value) => onChange(index, field, value);
  return (
    <div style={{
      padding: "10px 12px", borderRadius: 8, border: `1px solid ${COLORS.border}`,
      background: COLORS.bg, marginBottom: 10,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <strong style={{ fontSize: 13 }}>Wound {index + 1}</strong>
        <button type="button" style={{ ...styles.btnDanger, padding: "5px 10px", fontSize: 11.5 }} onClick={() => onRemove(index)}>
          Remove
        </button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10 }}>
        <label style={{ ...styles.checkboxLabel }}>
          <input type="checkbox" checked={!!wound.presentAsPressureInjury} onChange={(e) => set("presentAsPressureInjury", e.target.checked)} />
          Pressure injury
        </label>
        <FormSelect label="Stage" value={wound.stage} onChange={(v) => set("stage", v)} options={WOUND_STAGE_OPTIONS} />
        <FormSelect label="Wound Type" value={wound.woundType} onChange={(v) => set("woundType", v)} options={WOUND_TYPE_OPTIONS} />
        <FormInput label="Location" value={wound.location} onChange={(v) => set("location", v)} placeholder="e.g., Sacrum, L heel" />
        <FormInput label="Length (cm)" value={wound.length} onChange={(v) => set("length", v)} type="number" />
        <FormInput label="Width (cm)" value={wound.width} onChange={(v) => set("width", v)} type="number" />
        <FormInput label="Depth (cm)" value={wound.depth} onChange={(v) => set("depth", v)} type="number" />
        <FormSelect label="Drainage" value={wound.drainage} onChange={(v) => set("drainage", v)} options={WOUND_DRAINAGE_OPTIONS} />
        <FormSelect label="Odor" value={wound.odor} onChange={(v) => set("odor", v)} options={WOUND_ODOR_OPTIONS} />
        <FormInput label="Periwound Condition" value={wound.periwoundCondition} onChange={(v) => set("periwoundCondition", v)} />
        <label style={{ ...styles.checkboxLabel }}>
          <input type="checkbox" checked={!!wound.isSkinTear} onChange={(e) => set("isSkinTear", e.target.checked)} />
          Skin tear
        </label>
        <label style={{ ...styles.checkboxLabel }}>
          <input type="checkbox" checked={!!wound.isSurgicalWound} onChange={(e) => set("isSurgicalWound", e.target.checked)} />
          Surgical wound
        </label>
        <label style={{ ...styles.checkboxLabel }}>
          <input type="checkbox" checked={!!wound.isNonhealingWound} onChange={(e) => set("isNonhealingWound", e.target.checked)} />
          Nonhealing wound
        </label>
        <FormInput label="Current Treatment" value={wound.currentTreatment} onChange={(v) => set("currentTreatment", v)} />
        <FormInput label="Dressing" value={wound.dressing} onChange={(v) => set("dressing", v)} />
        <FormInput label="Dressing Frequency" value={wound.dressingFrequency} onChange={(v) => set("dressingFrequency", v)} placeholder="e.g., Daily, Q3 days" />
      </div>
    </div>
  );
}

function WoundListCard({ data, updateField, styles, COLORS }) {
  const wounds = data?.wounds || [];

  const setWounds = (next) => updateField("wounds", next);

  const addWound = () => setWounds([...wounds, {
    presentAsPressureInjury: false, stage: "", woundType: "", location: "",
    length: "", width: "", depth: "", drainage: "", odor: "",
    periwoundCondition: "", isSkinTear: false, isSurgicalWound: false,
    isNonhealingWound: false, currentTreatment: "", dressing: "", dressingFrequency: "",
  }]);

  const updateWound = (idx, field, value) => {
    setWounds(wounds.map((w, i) => (i === idx ? { ...w, [field]: value } : w)));
  };

  const removeWound = (idx) => setWounds(wounds.filter((_, i) => i !== idx));

  return (
    <div>
      <div style={{ fontSize: 12.5, color: COLORS.gray, marginBottom: 10 }}>
        Wound Count (auto): <strong style={{ color: COLORS.dark }}>{wounds.length}</strong>
      </div>
      {wounds.length === 0 && (
        <div style={{ fontSize: 12.5, color: COLORS.gray, fontStyle: "italic", marginBottom: 10 }}>
          No wounds documented yet.
        </div>
      )}
      {wounds.map((wound, idx) => (
        <WoundEntryCard key={idx} wound={wound} index={idx} onChange={updateWound} onRemove={removeWound} styles={styles} COLORS={COLORS} />
      ))}
      <button type="button" style={styles.btnSecondary} onClick={addWound}>
        + Add Wound
      </button>
    </div>
  );
}

const DME_ITEMS_WITH_SPECIFY = new Set(["Commode", "Other"]);

const DME_STATUS_OPTIONS = ["", "Has", "Needs", "Ordered", "Delivered", "Declined", "N/A"];

// Body Systems 9-part structure: shared "Clinical Status Change" options
// used by every body system's Clinical Status Change card. Hospice-oriented
// symptom-management/progression language -- NOT a disease-treatment
// response workflow. Reflects nursing judgment of stability, improvement,
// or decline in this system's symptoms/function since the prior
// assessment. "Not Applicable" is included deliberately so nurses are
// never forced to miscode when there is nothing to compare or manage.
const CLINICAL_STATUS_CHANGE_OPTIONS = ["Stable / No Change", "Improving", "Symptom Well-Managed", "Declining", "New Symptom Since Prior Assessment", "Not Applicable"];

// GitHub Directive (2026-09-28) "Final Neurological Density and
// Space-Utilization Plan" Section 10 -- Neurological's "Overall Change
// Since Prior Assessment" needs its own, more granular option set
// (Initial Assessment / trajectory language) distinct from the shared
// CLINICAL_STATUS_CHANGE_OPTIONS above, which is reused by ~10 other
// still-paused body systems (Cardiovascular, Respiratory, etc.) and must
// not be edited in place. Same `clinicalStatusChange` path (each body
// system has its own independent data namespace, so no collision), only
// Neurological's field config points at this new constant.
const NEURO_OVERALL_CHANGE_OPTIONS = ["Initial Assessment", "No Significant Change", "Improved", "Gradual Decline", "New or Worsening Concern", "Fluctuating", "Unable to Compare"];

// GitHub Directive (2026-09-28) "Cardiovascular Control-Model Correction"
// Section 4 -- Cardiovascular's own approved Clinical Status Change list,
// following the same NEURO_OVERALL_CHANGE_OPTIONS precedent: a dedicated
// constant so this change never touches the shared CLINICAL_STATUS_CHANGE_OPTIONS
// still used by the other ~9 still-paused body systems. A record charted
// under the OLD shared options (e.g. "Stable / No Change") is never
// rewritten -- FormSegmented's existing "Previously recorded" chip
// preserves and displays it read-only when it no longer matches this list.
const CARDIOVASCULAR_CLINICAL_STATUS_CHANGE_OPTIONS = ["Initial Assessment", "No Significant Change", "Improved", "Declining", "New or Worsening Finding", "Fluctuating", "Unable to Compare"];

function DmeStatusCard({ data, updateField, styles, COLORS }) {
  const items = data?.dmeItems || [];

  const updateItem = (idx, field, value) => {
    updateField("dmeItems", items.map((it, i) => (i === idx ? { ...it, [field]: value } : it)));
  };

  return (
    <div>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>Item</th>
            <th style={styles.th}>Status</th>
            <th style={styles.th}></th>
          </tr>
        </thead>
        <tbody>
          {items.map((it, idx) => (
            <tr key={it.item}>
              <td style={styles.td}>{it.item}</td>
              <td style={styles.td}>
                <select
                  style={styles.select}
                  value={it.status || ""}
                  onChange={(e) => updateItem(idx, "status", e.target.value)}
                >
                  {DME_STATUS_OPTIONS.map((opt) => (
                    <option key={opt || "blank"} value={opt}>{opt || "— select —"}</option>
                  ))}
                </select>
              </td>
              <td style={styles.td}>
                {DME_ITEMS_WITH_SPECIFY.has(it.item) && (
                  <input
                    style={styles.input}
                    placeholder="(specify)"
                    value={it.specify || ""}
                    onChange={(e) => updateItem(idx, "specify", e.target.value)}
                  />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// HOPE SECTION I0000 — Comorbidities and Co-existing Conditions.
//
// Per CMS HOPE Guidance Manual v1.02, Section I (Item I0100-I8005):
//   "Check all comorbid and/or coexisting diseases or medical conditions
//    that are addressed in the plan of care or that have the potential
//    to impact the plan of care. Do NOT include the principal diagnosis,
//    except if the patient has a secondary cancer."
//
// This component auto-detects candidate categories from the ICD-10 codes
// on the Primary/Secondary Diagnosis lists, but never silently checks a
// box — the clinician must click "Apply detected" to confirm. Any
// category matching the Primary Diagnosis is hard-disabled (excluded)
// so it can never be double-documented as a comorbidity, with the sole
// CMS carve-out for a second, distinct cancer diagnosis.
// ════════════════════════════════════════════════════════════════
const HOPE_COMORBIDITY_CATEGORIES = [
  { key: "cancer", hopeCode: "I0100", label: "Cancer", shortLabel: "Cancer", group: "Cancer", regex: /^C\d/i },
  { key: "heartFailure", hopeCode: "I0600", label: "Heart Failure (e.g., CHF, pulmonary edema)", shortLabel: "Heart Failure", group: "Heart/Circulation", regex: /^I50/i },
  { key: "pvdPad", hopeCode: "I0900", label: "Peripheral Vascular Disease (PVD) or Peripheral Arterial Disease (PAD)", shortLabel: "PVD/PAD", group: "Heart/Circulation", regex: /^I7[03]/i },
  { key: "cardiovascularExclHF", hopeCode: "I0950", label: "Cardiovascular (excluding heart failure)", shortLabel: "Cardiovascular Disease", group: "Heart/Circulation", regex: /^I(1[0-3]|15|2[0-5])/i },
  { key: "liverDisease", hopeCode: "I1101", label: "Liver disease (e.g., cirrhosis)", shortLabel: "Liver Disease", group: "Gastrointestinal", regex: /^K7[0-4]/i },
  { key: "renalDisease", hopeCode: "I1510", label: "Renal disease", shortLabel: "Renal Disease", group: "Genitourinary", regex: /^(N18|N19)/i },
  { key: "sepsis", hopeCode: "I2102", label: "Sepsis", shortLabel: "Sepsis", group: "Infections", regex: /^A41/i },
  { key: "diabetesMellitus", hopeCode: "I2900", label: "Diabetes Mellitus (DM)", shortLabel: "Diabetes", group: "Metabolic", regex: /^E(0[89]|1[013])/i },
  { key: "neuropathy", hopeCode: "I2910", label: "Neuropathy", shortLabel: "Neuropathy", group: "Metabolic", regex: /^(G6[023]|E1[013]\.4|E08\.4|E09\.4)/i },
  { key: "stroke", hopeCode: "I4501", label: "Stroke", shortLabel: "Stroke", group: "Neurological", regex: /^(I6[0-3]|I65|I66|I69)/i },
  { key: "dementia", hopeCode: "I4801", label: "Dementia (including Alzheimer's disease)", shortLabel: "Dementia", group: "Neurological", regex: /^(F0[0-3]|G30|G31\.1)/i },
  { key: "neurologicalConditions", hopeCode: "I5150", label: "Neurological Conditions (e.g., Parkinson's disease, MS, ALS)", shortLabel: "Parkinson's/MS/ALS", group: "Neurological", regex: /^(G20|G35|G12\.2)/i },
  { key: "seizureDisorder", hopeCode: "I5401", label: "Seizure Disorder", shortLabel: "Seizure Disorder", group: "Neurological", regex: /^G40/i },
  { key: "copd", hopeCode: "I6202", label: "Chronic Obstructive Pulmonary Disease (COPD)", shortLabel: "COPD", group: "Pulmonary", regex: /^J44/i },
];

function matchesCategory(icd10, regex) {
  const code = (icd10 || "").trim().toUpperCase();
  if (!code) return false;
  return regex.test(code);
}

function categorizeIcd10(icd10) {
  return HOPE_COMORBIDITY_CATEGORIES.find((cat) => matchesCategory(icd10, cat.regex)) || null;
}

// Free-text fallback keywords for the three categories that gate a
// disease-specific performance scale (NYHA/FAST/ECOG) below. Many charts
// (e.g. H&P-derived diagnoses) never get a coded ICD-10 on the Primary
// Diagnosis, only a free-text description -- without this fallback the
// relevant scale silently never appears for those patients even though
// the diagnosis clearly documents the condition. This is deliberately
// scoped to scale-gating only; the HOPE comorbidity checkboxes above
// (categorizeIcd10 / HopeComorbiditiesCard) remain ICD-10-coded only,
// per CMS HOPE guidance, and are untouched by this fallback.
const SCALE_GATING_KEYWORDS = {
  cancer: ["cancer", "carcinoma", "malignan", "neoplasm", "metasta", "sarcoma", "lymphoma", "leukemia"],
  heartFailure: ["heart failure", "chf", "cardiomyopathy", "pulmonary edema"],
  dementia: ["dementia", "alzheimer", "senile degeneration", "senile psychosis"],
};

function matchesCategoryText(description, categoryKey) {
  const keywords = SCALE_GATING_KEYWORDS[categoryKey];
  if (!keywords) return false;
  const text = (description || "").trim().toLowerCase();
  if (!text) return false;
  return keywords.some((kw) => text.includes(kw));
}

// Used to gate disease-specific performance scales (NYHA/FAST/ECOG) in the
// Performance Status section so the RN only sees the scale relevant to this
// patient's actual diagnoses, checking both the primary diagnosis and every
// secondary diagnosis (not just the principal one) against the same
// ICD-10 category regexes used for HOPE comorbidity categorization above,
// falling back to a free-text keyword match when no ICD-10 code is on
// file yet (see SCALE_GATING_KEYWORDS).
function diagnosesIncludeCategory(diagnosesData, categoryKey) {
  const category = HOPE_COMORBIDITY_CATEGORIES.find((cat) => cat.key === categoryKey);
  if (!category) return false;
  const primary = diagnosesData?.primaryDiagnosis;
  if (matchesCategory(primary?.icd10, category.regex)) return true;
  if (matchesCategoryText(primary?.description, categoryKey)) return true;
  const secondaryDx = diagnosesData?.secondaryDiagnoses || [];
  return secondaryDx.some(
    (dx) => matchesCategory(dx?.icd10, category.regex) || matchesCategoryText(dx?.description, categoryKey),
  );
}

// Explains WHY a disease-specific scale is currently visible, reusing the
// exact same category regex/text match already used by
// diagnosesIncludeCategory above (never re-derives its own matching rule).
// Returns null when nothing matched (scale hidden) so callers can skip the
// explanatory line entirely.
function describeScaleTrigger(diagnosesData, categoryKey) {
  const category = HOPE_COMORBIDITY_CATEGORIES.find((cat) => cat.key === categoryKey);
  if (!category) return null;
  const primary = diagnosesData?.primaryDiagnosis;
  if (matchesCategory(primary?.icd10, category.regex) || matchesCategoryText(primary?.description, categoryKey)) {
    return `Primary diagnosis: ${primary?.description || formatIcd10Code(primary?.icd10) || category.label}`;
  }
  const secondaryDx = diagnosesData?.secondaryDiagnoses || [];
  const match = secondaryDx.find(
    (dx) => matchesCategory(dx?.icd10, category.regex) || matchesCategoryText(dx?.description, categoryKey),
  );
  if (match) {
    return `Secondary diagnosis: ${match.description || formatIcd10Code(match.icd10) || category.label}`;
  }
  return null;
}

// ════════════════════════════════════════════════════════════════
// FUNCTIONAL STATUS — diagnosis-aware scale layout (owner directive:
// "RNICA Functional Status Context-Aware Scale Visibility", finalized by
// the owner's "NOT APPROVED YET" layout revision). PPS/KPS are core
// hospice scales (always shown, unchanged); ECOG/FAST/NYHA remain gated
// by the existing diagnosesIncludeCategory logic above — nothing about
// that gating changes here, only how the visible scales are presented
// (compact shadcn/ui cards instead of one full-width card per scale) and
// how the RN is told WHY a scale is/isn't showing. Pilot-mode only —
// legacy (workspacePilot=false) keeps rendering every card through the
// original card.fields generic renderer, completely untouched.
// ════════════════════════════════════════════════════════════════
const PERFORMANCE_SCALE_META = {
  pps: { isPercent: true },
  kps: { isPercent: true },
  ecog: { isPercent: false, hint: "cancer" },
  fast: { isPercent: false, hint: "dementia" },
  nyha: { isPercent: false, hint: "heartFailure" },
};

const PERFORMANCE_SCALE_TITLES = {
  "Palliative Performance Scale (PPS)": "pps",
  "Karnofsky Performance Scale (KPS)": "kps",
  "ECOG Performance Status": "ecog",
  "FAST Scale (Dementia)": "fast",
  "NYHA Classification (Heart Failure)": "nyha",
};

// One compact card per scale: score dropdown + single-row justification
// instead of the old full-width stacked layout, plus (for disease-specific
// scales) a one-line explanation of which diagnosis made it visible.
function PerformanceScaleCard({ scaleKey, card, data, update, diagnosesData }) {
  const meta = PERFORMANCE_SCALE_META[scaleKey] || {};
  const [scoreField, justificationField] = card.fields;
  const scoreValue = getNestedValue(data, scoreField.path);
  const justificationValue = getNestedValue(data, justificationField.path);
  const scoreOption = (scoreField.options || []).find((opt) => (typeof opt === "string" ? opt : opt.value) === scoreValue);
  const scoreLabel = scoreOption ? (typeof scoreOption === "string" ? null : scoreOption.label) : null;
  const percent = meta.isPercent && scoreValue ? parseInt(scoreValue, 10) : null;
  const trigger = meta.hint ? describeScaleTrigger(diagnosesData, meta.hint) : null;

  return (
    <ShadcnCard className="rnica-scale-card">
      <ShadcnCardHeader>
        <ShadcnCardTitle>
          {card.title}
          {card.hopeCode && <HopeTag code={card.hopeCode} />}
        </ShadcnCardTitle>
        <ShadcnBadge variant={scoreValue ? "teal" : "neutral"}>{scoreValue || "Not documented"}</ShadcnBadge>
      </ShadcnCardHeader>
      <ShadcnCardContent>
        {trigger && <div className="rnica-scale-card__trigger">Shown because of — {trigger}</div>}
        {percent !== null && <ShadcnProgress value={percent} className="rnica-scale-card__progress" />}
        {scoreLabel && <div className="rnica-scale-card__meaning">{scoreLabel}</div>}
        <div className="rnica-scale-card__row">
          <FormSelect
            label={scoreField.label}
            value={scoreValue}
            onChange={(v) => update(scoreField.path, v)}
            options={scoreField.options}
          />
          {justificationField.type === "textarea" ? (
            <FormTextarea
              label={justificationField.label}
              value={justificationValue}
              onChange={(v) => update(justificationField.path, v)}
              rows={1}
            />
          ) : (
            <FormInput
              label={justificationField.label}
              value={justificationValue}
              onChange={(v) => update(justificationField.path, v)}
            />
          )}
        </div>
      </ShadcnCardContent>
    </ShadcnCard>
  );
}

// Top-of-screen transparency banner: shows the diagnoses driving scale
// visibility and which scales are currently active, so the RN never has to
// wonder why FAST/ECOG/NYHA did or didn't appear (owner: "The screen
// should explain itself").
function FunctionalStatusSummaryCard({ diagnosesData, showEcog, showFast, showNyha }) {
  const primary = diagnosesData?.primaryDiagnosis;
  const secondaryDx = diagnosesData?.secondaryDiagnoses || [];
  const primaryLabel = primary?.description || (primary?.icd10 ? formatIcd10Code(primary.icd10) : "") || "Not documented";
  const secondaryLabel = secondaryDx.length
    ? secondaryDx.map((dx) => dx.description || (dx.icd10 ? formatIcd10Code(dx.icd10) : "")).filter(Boolean).join(", ") || "Not documented"
    : "None documented";
  const activeScales = ["PPS", "KPS", showEcog && "ECOG", showFast && "FAST", showNyha && "NYHA"].filter(Boolean);

  return (
    <ShadcnCard className="rnica-functional-summary">
      <ShadcnCardHeader><ShadcnCardTitle>Functional Status Summary</ShadcnCardTitle></ShadcnCardHeader>
      <ShadcnCardContent>
        <div className="rnica-functional-summary__grid">
          <div>
            <div className="rnica-functional-summary__label">Primary Diagnosis</div>
            <div className="rnica-functional-summary__value">{primaryLabel}</div>
          </div>
          <div>
            <div className="rnica-functional-summary__label">Secondary Diagnosis</div>
            <div className="rnica-functional-summary__value">{secondaryLabel}</div>
          </div>
          <div>
            <div className="rnica-functional-summary__label">Active Scales</div>
            <div className="rnica-functional-summary__badges">
              {activeScales.map((scale) => <ShadcnBadge key={scale} variant="teal">{scale}</ShadcnBadge>)}
            </div>
          </div>
        </div>
      </ShadcnCardContent>
    </ShadcnCard>
  );
}

// Compact single-row ADL grid (replaces the old one-select-per-row stack)
// plus a plain, non-AI, selection-derived summary sentence -- built only
// from the RN's own documented scores, per owner: "No AI interpretation
// required." Reads/writes the same adl.* fields via `update` (dataSection
// still resolves to musculoskeletal, unchanged storage/ownership).
const ADL_SUMMARY_PHRASES = {
  bathing: "bathing", dressing: "dressing", toileting: "toileting",
  transferring: "transfers", eating: "eating", grooming: "grooming",
};

function buildAdlSummaryText(data) {
  const adl = data?.adl || {};
  const scored = Object.entries(ADL_SUMMARY_PHRASES)
    .map(([key, phrase]) => ({ phrase, score: adl[key] !== undefined && adl[key] !== "" ? parseInt(adl[key], 10) : null }))
    .filter((item) => Number.isFinite(item.score));
  if (!scored.length) return "";
  const extensive = scored.filter((item) => item.score >= 4).map((item) => item.phrase);
  const independent = scored.filter((item) => item.score === 0).map((item) => item.phrase);
  const parts = [];
  if (extensive.length) parts.push(`Patient requires extensive assistance with ${extensive.join(", ")}.`);
  if (independent.length) parts.push(`Patient remains independent with ${independent.join(", ")}.`);
  return parts.join(" ");
}

function AdlSummaryGrid({ card, data, update }) {
  const summary = buildAdlSummaryText(data);
  return (
    <>
      <div className="rnica-adl-grid">
        {card.fields.map((field) => (
          <div key={field.path} className="rnica-adl-grid__item">
            <FormSelect
              label={field.label}
              value={getNestedValue(data, field.path)}
              onChange={(v) => update(field.path, v)}
              options={field.options}
            />
          </div>
        ))}
      </div>
      {summary && <div className="rnica-adl-grid__summary"><strong>ADL Summary — </strong>{summary}</div>}
    </>
  );
}

// Read-only reference card: Mobility/Transfer is documented on the
// Musculoskeletal (Body Systems) screen (musculoskeletal.mobility.*), not
// duplicated here as an editable field -- this only surfaces it inside
// Functional Status for context, per the owner's approved page structure.
// Never writes back into formData; a pure display of already-owned data.
function MobilityTransferSummaryCard({ fullFormData }) {
  const mobility = fullFormData?.musculoskeletal?.mobility || {};
  const hasAny = mobility.ambulatoryStatus || mobility.transferAbility || mobility.endurance;
  return (
    <ShadcnCard className="rnica-functional-summary">
      <ShadcnCardHeader><ShadcnCardTitle>Mobility &amp; Transfer</ShadcnCardTitle></ShadcnCardHeader>
      <ShadcnCardContent>
        {hasAny ? (
          <div className="rnica-functional-summary__grid">
            <div>
              <div className="rnica-functional-summary__label">Ambulatory Status</div>
              <div className="rnica-functional-summary__value">{mobility.ambulatoryStatus || "—"}</div>
            </div>
            <div>
              <div className="rnica-functional-summary__label">Transfer Ability</div>
              <div className="rnica-functional-summary__value">{mobility.transferAbility || "—"}</div>
            </div>
            <div>
              <div className="rnica-functional-summary__label">Endurance</div>
              <div className="rnica-functional-summary__value">{mobility.endurance || "—"}</div>
            </div>
          </div>
        ) : (
          <div className="rnica-info-note">Not yet documented on Body Systems → Musculoskeletal.</div>
        )}
        <div className="rnica-info-note" style={{ marginTop: 8 }}>
          Documented on Body Systems → Musculoskeletal; shown here for context only.
        </div>
      </ShadcnCardContent>
    </ShadcnCard>
  );
}

// ── RNICA Diagnosis & LCD Workspace Optimization (owner-approved
// implementation directive, GitHub issue "RNICA Diagnosis & LCD Workspace
// Optimization") ──────────────────────────────────────────────────────
// HOPE I0010 Principal Diagnosis Category options -- unchanged CMS
// response set (01-09, 99), now shared by the merged diagnosis-search
// card below instead of living inline on the removed "Primary Diagnosis"
// field config.
const HOPE_PRINCIPAL_DIAGNOSIS_CATEGORY_OPTIONS = [
  { value: "01", label: "01 — Cancer" },
  { value: "02", label: "02 — Dementia (including Alzheimer's disease)" },
  { value: "03", label: "03 — Neurological Condition (e.g., Parkinson's disease, MS, ALS)" },
  { value: "04", label: "04 — Stroke" },
  { value: "05", label: "05 — Chronic Obstructive Pulmonary Disease (COPD)" },
  { value: "06", label: "06 — Cardiovascular (excluding heart failure)" },
  { value: "07", label: "07 — Heart Failure" },
  { value: "08", label: "08 — Liver Disease" },
  { value: "09", label: "09 — Renal Disease" },
  { value: "99", label: "99 — None of the above" },
];

// Maps the same ICD-10 category regexes already used for HOPE comorbidity
// detection (HOPE_COMORBIDITY_CATEGORIES/categorizeIcd10 above) to the
// distinct I0010 Principal Diagnosis Category code set. Reuses existing
// categorization instead of duplicating regexes (only the categories that
// have a direct I0010 equivalent are mapped; anything else is left for the
// RN to pick manually rather than guessing "99").
const I0010_CATEGORY_BY_COMORBIDITY_KEY = {
  cancer: "01",
  dementia: "02",
  neurologicalConditions: "03",
  stroke: "04",
  copd: "05",
  cardiovascularExclHF: "06",
  heartFailure: "07",
  liverDisease: "08",
  renalDisease: "09",
};

function deriveHopeDiagnosisCategory(icd10) {
  const category = categorizeIcd10(icd10);
  if (!category) return "";
  return I0010_CATEGORY_BY_COMORBIDITY_KEY[category.key] || "";
}

// FR-003/FR-004: replaces the separate "Primary Diagnosis" (ICD-10 Code +
// Description + HOPE Category fields) and "Terminal Prognosis" cards with
// one compact, single-source-of-truth container. A diagnosis/ICD-10 search
// control (reusing the same Icd10DiagnosisInput/searchIcd10Diagnoses
// typeahead already used on the Face Sheet) fills ICD-10 + Description in
// one action; HOPE Category is auto-suggested from the selected code (via
// the existing categorization regexes) but is always RN-editable and is
// never overwritten once a value is on file. LCD Pathway is not a field
// here -- it is already auto-detected from primaryDiagnosis.icd10/
// description by LcdEligibilityCard's existing effect the moment this
// card's search fills those fields, so no new logic is introduced for it.
// Terminal Prognosis (6 months or less / More than 6 months /
// Undetermined) remains a plain RN-selected field, embedded in this same
// container instead of a separate card -- it is a clinical judgment, not a
// fact of the diagnosis, so it is intentionally never auto-filled.
function PrimaryTerminalDiagnosisCard({ diagnosesData, updateField, styles, COLORS, workspacePilot = false }) {
  const primary = diagnosesData?.primaryDiagnosis || {};
  const [searchText, setSearchText] = useState(() => (
    primary.description
      ? `${primary.description}${primary.icd10 ? ` (${formatIcd10Code(primary.icd10)})` : ""}`
      : formatIcd10Code(primary.icd10 || "")
  ));

  const setPrimary = (field, value) => updateField(`primaryDiagnosis.${field}`, value);

  const handleSelectSuggestion = (suggestion) => {
    setPrimary("icd10", suggestion.icd10_code);
    setPrimary("description", suggestion.diagnosis_description);
    // Auto-suggest HOPE category from the selected code, but never
    // silently overwrite a category the RN already documented.
    if (!primary.hopeDiagnosisCategory) {
      const derived = deriveHopeDiagnosisCategory(suggestion.icd10_code);
      if (derived) setPrimary("hopeDiagnosisCategory", derived);
    }
  };

  const summaryLabel = HOPE_PRINCIPAL_DIAGNOSIS_CATEGORY_OPTIONS.find((o) => o.value === primary.hopeDiagnosisCategory)?.label;

  return (
    <div className={workspacePilot ? "rnica-primary-dx" : undefined}>
      <div style={styles.formGroup}>
        <label style={styles.label}>Search Diagnosis or ICD-10</label>
        <Icd10DiagnosisInput
          value={searchText}
          onChange={setSearchText}
          onSelectSuggestion={handleSelectSuggestion}
          colors={{ cardBg: COLORS.white, border: COLORS.border, label: COLORS.gray, white: COLORS.dark }}
          inputStyle={styles.input}
          placeholder="e.g. Metastatic Breast Cancer, Lung Cancer, C50.919, CHF, ALS, COPD…"
        />
      </div>

      {(primary.description || primary.icd10) && (
        <div className={workspacePilot ? "rnica-primary-dx__summary" : undefined} style={{ ...styles.infoBox, marginTop: 8, marginBottom: 12 }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: COLORS.dark }}>{primary.description || "Description not documented"}</div>
          <div style={{ fontSize: 12, color: COLORS.gray, marginTop: 2 }}>
            {primary.icd10 && <span>ICD-10: {formatIcd10Code(primary.icd10)}</span>}
            {primary.icd10 && summaryLabel && <span> · </span>}
            {summaryLabel && <span>HOPE: {summaryLabel}</span>}
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
        <FormInput
          label="Onset Date"
          type="date"
          value={primary.onsetDate || ""}
          onChange={(v) => setPrimary("onsetDate", v)}
        />
        <FormSelect
          label="HOPE Principal Diagnosis Category (I0010)"
          required
          value={primary.hopeDiagnosisCategory || ""}
          onChange={(v) => setPrimary("hopeDiagnosisCategory", v)}
          options={HOPE_PRINCIPAL_DIAGNOSIS_CATEGORY_OPTIONS}
        />
        <FormSelect
          label="Terminal Prognosis"
          hopeCode="J0050"
          value={diagnosesData?.terminalPrognosis || ""}
          onChange={(v) => updateField("terminalPrognosis", v)}
          options={["6 months or less", "More than 6 months", "Undetermined"]}
        />
      </div>
    </div>
  );
}

function HopeComorbiditiesCard({ diagnosesData, updateField, styles, COLORS, workspacePilot = false }) {
  const primaryIcd10 = diagnosesData?.primaryDiagnosis?.icd10 || "";
  const secondaryDx = diagnosesData?.secondaryDiagnoses || [];
  const hope = diagnosesData?.hopeComorbidities || {};

  const principalCategory = useMemo(() => categorizeIcd10(primaryIcd10), [primaryIcd10]);

  const autoDetected = useMemo(() => {
    const set = new Set();
    secondaryDx.forEach((dx) => {
      const cat = categorizeIcd10(dx?.icd10);
      if (cat) set.add(cat.key);
    });
    return set;
  }, [secondaryDx]);

  const uncategorizedSecondary = useMemo(
    () => secondaryDx.filter((dx) => dx?.icd10 && !categorizeIcd10(dx.icd10)),
    [secondaryDx],
  );

  const setHope = (key, value) => updateField(`hopeComorbidities.${key}`, value);

  // Whether a category is checked (accounting for the Principal Diagnosis
  // exclusion/cancer carve-out) -- shared by the top summary and each
  // category row below so both agree on what "checked" means.
  const isCategoryChecked = (cat) => {
    const isPrincipal = principalCategory?.key === cat.key;
    const detected = autoDetected.has(cat.key);
    const cancerException = cat.key === "cancer" && isPrincipal && detected;
    const excluded = isPrincipal && !cancerException;
    return excluded ? false : Boolean(hope[cat.key]);
  };

  // Legacy (non-pilot) grouping/order is unchanged -- single-column,
  // always-expanded category sections, exactly as before this redesign.
  const legacyGroups = useMemo(() => {
    const order = ["Cancer", "Heart/Circulation", "Gastrointestinal", "Genitourinary", "Infections", "Metabolic", "Neurological", "Pulmonary"];
    return order
      .map((group) => ({ group, heading: group, categories: HOPE_COMORBIDITY_CATEGORIES.filter((c) => c.group === group) }))
      .filter((g) => g.categories.length);
  }, []);

  // Pilot (RNICA workspace) presentation: a fixed 3-column clinical
  // checklist grid instead of single-column stacking, per owner directive
  // -- Row 1 Cardiac/Pulmonary/Neurological, Row 2 GI/GU/Metabolic,
  // Row 3 Infection/Cancer/Other. Same HOPE_COMORBIDITY_CATEGORIES data,
  // same checked/excluded logic -- presentation-only reorder + relabel.
  const pilotColumns = useMemo(() => {
    const order = [
      { group: "Heart/Circulation", heading: "Cardiac" },
      { group: "Pulmonary", heading: "Pulmonary" },
      { group: "Neurological", heading: "Neurological" },
      { group: "Gastrointestinal", heading: "GI" },
      { group: "Genitourinary", heading: "GU" },
      { group: "Metabolic", heading: "Metabolic" },
      { group: "Infections", heading: "Infection" },
      { group: "Cancer", heading: "Cancer" },
    ];
    return order.map(({ group, heading }) => ({
      group,
      heading,
      categories: HOPE_COMORBIDITY_CATEGORIES.filter((c) => c.group === group),
    }));
  }, []);

  const groups = workspacePilot ? pilotColumns : legacyGroups;

  // Compact "Selected Comorbidities" summary -- immediate visibility of
  // what's already checked without scanning the whole grid. Pilot-only.
  const selectedSummary = useMemo(() => {
    const names = HOPE_COMORBIDITY_CATEGORIES.filter(isCategoryChecked).map((cat) => cat.shortLabel || cat.label);
    if (hope.other) names.push("Other Medical Condition");
    return names;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hope, principalCategory, autoDetected]);

  return (
    <div className={workspacePilot ? "rnica-comorbidity-panel" : undefined}>
      <div className={workspacePilot ? "rnica-comorbidity-guidance" : undefined} style={styles.infoBox}>
        Per CMS HOPE guidance: check all comorbid/coexisting conditions addressed in the plan of
        care. <strong>Do not check a category already coded as the Principal Diagnosis</strong>{" "}
        — the exception is if the patient has a second, distinct cancer diagnosis.
      </div>

      {workspacePilot && (
        <div className="rnica-comorbidity-summary">
          <strong>Selected Comorbidities: {selectedSummary.length}</strong>
          {selectedSummary.length > 0 && <span>{selectedSummary.join(", ")}</span>}
        </div>
      )}

      <div className={workspacePilot ? "rnica-comorbidity-grid" : undefined}>
      {groups.map(({ group, heading, categories }) => (
        <div key={group} className={workspacePilot ? "rnica-comorbidity-group" : undefined} style={{ marginBottom: 14 }}>
          <div className={workspacePilot ? "rnica-comorbidity-group__heading" : undefined} style={{ fontSize: 12, fontWeight: 800, color: COLORS.gray, textTransform: "uppercase", letterSpacing: "0.03em", marginBottom: 6 }}>
            {heading}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {categories.map((cat) => {
              const isPrincipal = principalCategory?.key === cat.key;
              const detected = autoDetected.has(cat.key);
              // CMS carve-out: cancer may be both the Principal Diagnosis and a
              // checked comorbidity if the patient has a second, distinct cancer.
              const cancerException = cat.key === "cancer" && isPrincipal && detected;
              const excluded = isPrincipal && !cancerException;
              const checked = excluded ? false : Boolean(hope[cat.key]);

              return (
                <div key={cat.key} className={workspacePilot ? "rnica-comorbidity-option" : undefined} style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <label
                    style={{
                      ...styles.checkboxLabel,
                      opacity: excluded ? 0.5 : 1,
                      cursor: excluded ? "not-allowed" : "pointer",
                    }}
                    title={excluded ? "Already coded as Principal Diagnosis — not double-entered per HOPE guidance." : ""}
                  >
                    <Checkbox
                      checked={checked}
                      disabled={excluded}
                      onCheckedChange={(v) => setHope(cat.key, Boolean(v))}
                    />
                    <span>{workspacePilot ? (cat.shortLabel || cat.label) : cat.label}</span>
                  </label>
                  <HopeTag code={cat.hopeCode} />
                  {excluded && (
                    <span style={{ fontSize: 11, color: COLORS.gray, fontStyle: "italic" }}>
                      Excluded — already Principal Diagnosis
                    </span>
                  )}
                  {!excluded && detected && !checked && (
                    <button
                      type="button"
                      style={{ ...styles.btnSecondary, padding: "2px 8px", fontSize: 11 }}
                      onClick={() => setHope(cat.key, true)}
                    >
                      Apply detected match
                    </button>
                  )}
                  {!excluded && detected && checked && (
                    <span style={{ fontSize: 11, color: COLORS.gray }}>✓ confirmed from diagnosis list</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
      {/* "Other" participates in the same grid flow as a regular category
          column in the pilot layout (Row 3, 3rd column); legacy mode keeps
          it as its own section below the groups, unchanged. */}
      <div className={workspacePilot ? "rnica-comorbidity-group" : undefined} style={{ marginBottom: 8 }}>
        <div className={workspacePilot ? "rnica-comorbidity-group__heading" : undefined} style={{ fontSize: 12, fontWeight: 800, color: COLORS.gray, textTransform: "uppercase", letterSpacing: "0.03em", marginBottom: 6 }}>
          Other
        </div>
        <label style={styles.checkboxLabel}>
          <Checkbox checked={Boolean(hope.other)} onCheckedChange={(v) => setHope("other", Boolean(v))} />
          <span>Other Medical Condition</span>
        </label>
        <HopeTag code="I8005" />
        {uncategorizedSecondary.length > 0 && (
          <div style={{ fontSize: 11, color: COLORS.gray, marginTop: 4 }}>
            Uncategorized secondary diagnoses: {uncategorizedSecondary.map((dx) => `${formatIcd10Code(dx.icd10)} ${dx.description || ""}`.trim()).join("; ")}
          </div>
        )}
      </div>
      </div>

      <FormTextarea
        label="Additional Note (optional)"
        value={hope.additionalNote}
        onChange={(v) => setHope("additionalNote", v)}
        placeholder="Clarify any comorbidity coding decisions..."
        rows={2}
      />
    </div>
  );
}

// CMS HOPE J2051/J2053 Symptom Impact scale -- the full 5-value response
// set (Not at all / Slight / Moderate / Severe / Not applicable), not the
// collapsed 4-value None/Mild/Moderate/Severe set used previously. Codes
// 0/1/2/3/9 match hopeReportMapper.js's IMPACT_MAP exactly.
const SYMPTOM_IMPACT_OPTIONS = [
  { value: "0", label: "0 — Not at all" },
  { value: "1", label: "1 — Slight" },
  { value: "2", label: "2 — Moderate" },
  { value: "3", label: "3 — Severe" },
  { value: "9", label: "9 — Not applicable" },
];

const PPS_ORDER = ["100%", "90%", "80%", "70%", "60%", "50%", "40%", "30%", "20%", "10%", "0%"];
const FAST_ORDER = ["1", "2", "3", "4", "5", "6a", "6b", "6c", "6d", "6e", "7a", "7b", "7c", "7d", "7e", "7f"];

function parsePercentOrNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const num = parseFloat(String(value).replace("%", ""));
  return Number.isFinite(num) ? num : null;
}

function fastStageIndex(stage) {
  if (!stage) return null;
  const idx = FAST_ORDER.indexOf(String(stage).trim());
  return idx === -1 ? null : idx;
}

function formatDate(value) {
  if (!value) return "unknown date";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "unknown date" : d.toLocaleDateString();
}

// "Change Since Last Assessment" — pulls the patient's prior RNICA/RN-recert
// PPS/KPS/FAST/weight and shows the trend so hospice recert documentation
// doesn't rely purely on a single point-in-time snapshot (CMS/LCD reviewers
// specifically look for documented functional decline over time).
function DeclineTrackerCard({ patientId, assessmentId, performanceData, weight, styles, COLORS }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!patientId) return;
    let active = true;
    setLoading(true);
    setError("");
    fetchPerformanceHistory(patientId)
      .then((res) => {
        if (active) setHistory(res?.history || []);
      })
      .catch((err) => {
        if (!active) return;
        console.error("Failed to load performance history:", err);
        setError("Unable to load prior assessment history.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [patientId]);

  const priorEntry = useMemo(() => {
    const priors = history.filter((h) => h.id !== assessmentId);
    return priors.length ? priors[priors.length - 1] : null;
  }, [history, assessmentId]);

  const currentPps = parsePercentOrNumber(performanceData?.pps);
  const currentKps = parsePercentOrNumber(performanceData?.kps);
  const currentFastIdx = fastStageIndex(performanceData?.fast);
  const currentWeight = parsePercentOrNumber(weight);

  const rows = useMemo(() => {
    if (!priorEntry) return [];
    const result = [];

    if (currentPps !== null && priorEntry.pps !== null && priorEntry.pps !== undefined) {
      const delta = currentPps - priorEntry.pps;
      result.push({
        label: "PPS", from: `${priorEntry.pps}%`, to: `${currentPps}%`,
        delta, trend: delta < 0 ? "decline" : delta > 0 ? "improvement" : "stable",
      });
    }
    if (currentKps !== null && priorEntry.kps !== null && priorEntry.kps !== undefined) {
      const delta = currentKps - priorEntry.kps;
      result.push({
        label: "KPS", from: `${priorEntry.kps}`, to: `${currentKps}`,
        delta, trend: delta < 0 ? "decline" : delta > 0 ? "improvement" : "stable",
      });
    }
    const priorFastIdx = fastStageIndex(priorEntry.fast_stage);
    if (currentFastIdx !== null && priorFastIdx !== null) {
      const delta = currentFastIdx - priorFastIdx;
      result.push({
        label: "FAST", from: priorEntry.fast_stage, to: performanceData?.fast,
        delta, trend: delta > 0 ? "decline" : delta < 0 ? "improvement" : "stable",
      });
    }
    if (currentWeight !== null && priorEntry.weight !== null && priorEntry.weight !== undefined) {
      const delta = currentWeight - priorEntry.weight;
      const pctChange = priorEntry.weight ? (delta / priorEntry.weight) * 100 : null;
      result.push({
        label: "Weight", from: `${priorEntry.weight} lbs`, to: `${currentWeight} lbs`,
        delta, pctChange, trend: delta < 0 ? "decline" : delta > 0 ? "improvement" : "stable",
      });
    }
    return result;
  }, [priorEntry, currentPps, currentKps, currentFastIdx, currentWeight, performanceData?.fast]);

  const trendColor = (trend) => {
    if (trend === "decline") return COLORS.warning;
    if (trend === "improvement") return COLORS.success;
    return COLORS.gray;
  };

  const summaryText = useMemo(() => {
    if (!priorEntry || !rows.length) return "";
    const declines = rows.filter((r) => r.trend === "decline");
    if (!declines.length) return "";
    const parts = declines.map((r) => {
      if (r.label === "Weight" && r.pctChange !== null) {
        return `weight decreased from ${r.from} to ${r.to} (${Math.abs(r.pctChange).toFixed(1)}% loss)`;
      }
      return `${r.label} declined from ${r.from} to ${r.to}`;
    });
    return `Documented decline since prior assessment on ${formatDate(priorEntry.date)}: ${parts.join("; ")}.`;
  }, [priorEntry, rows]);

  const handleCopy = () => {
    if (!summaryText) return;
    navigator.clipboard?.writeText(summaryText).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    });
  };

  if (loading) {
    return <p style={{ color: COLORS.gray, fontSize: 13 }}>Loading prior assessment history...</p>;
  }
  if (error) {
    return <p style={{ color: COLORS.error, fontSize: 13 }}>{error}</p>;
  }
  if (!priorEntry) {
    return (
      <div style={styles.infoBox}>
        No prior RNICA or RN recertification assessment on file yet — this is the patient's baseline.
        Once a subsequent assessment is documented, this panel will show the change in PPS/KPS/FAST/weight
        since this one.
      </div>
    );
  }
  if (!rows.length) {
    return (
      <div style={styles.infoBox}>
        Prior assessment on {formatDate(priorEntry.date)} found, but not enough matching scores (PPS/KPS/FAST/weight)
        are documented on both assessments to compute a trend yet.
      </div>
    );
  }

  return (
    <div>
      <div style={{ fontSize: 12, color: COLORS.gray, marginBottom: 10 }}>
        Compared to prior assessment ({priorEntry.source}) on <strong>{formatDate(priorEntry.date)}</strong>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {rows.map((r) => (
          <div key={r.label} style={{
            display: "flex", alignItems: "center", gap: 10, padding: "8px 10px",
            borderRadius: 8, border: `1px solid ${trendColor(r.trend)}55`, background: `${trendColor(r.trend)}11`,
          }}>
            <div style={{ fontWeight: 700, fontSize: 13, width: 60 }}>{r.label}</div>
            <div style={{ fontSize: 13 }}>{r.from} → {r.to}</div>
            <div style={{ fontSize: 12, fontWeight: 700, color: trendColor(r.trend), marginLeft: "auto", textTransform: "uppercase" }}>
              {r.trend === "decline" ? "▼ Decline" : r.trend === "improvement" ? "▲ Improved" : "— Stable"}
            </div>
          </div>
        ))}
      </div>

      {summaryText && (
        <div style={{ marginTop: 12 }}>
          <div style={styles.infoBox}>{summaryText}</div>
          <button type="button" onClick={handleCopy} style={{
            marginTop: 8, padding: "6px 12px", borderRadius: 6, border: `1px solid ${COLORS.teal}`,
            background: copied ? COLORS.teal : "transparent", color: copied ? COLORS.white : COLORS.teal,
            fontSize: 12, fontWeight: 700, cursor: "pointer",
          }}>
            {copied ? "Copied!" : "Copy decline summary for LCD Narrative"}
          </button>
        </div>
      )}
    </div>
  );
}

// Owner bug report (2026-09-25, HIGH severity, clinical data integrity):
// switching the Temperature unit toggle must convert the stored numeric
// value, not just relabel it (98.6 was staying "98.6" after switching to
// °C instead of becoming 37.0). Standard clinical conversion formulas;
// rounded to one decimal place, matching the field's normal precision.
function convertTemperature(value, fromUnit, toUnit) {
  if (value === "" || value === null || value === undefined) return value;
  const num = Number(value);
  if (Number.isNaN(num) || fromUnit === toUnit) return value;
  const converted = fromUnit === "F" ? ((num - 32) * 5) / 9 : (num * 9) / 5 + 32;
  return Math.round(converted * 10) / 10;
}

// Auto-calculates BMI from height (inches) and weight (lbs) so it is never
// entered as an independent, unrelated manual value. The field remains
// editable (RN can override), but is pre-populated/kept in sync whenever
// height or weight change, and is still persisted at vitals.bmi in the
// existing form_data JSONB model (no new storage location).
// Vital signs are clinical *concepts*, not raw database columns — a nurse
// reads "BP 120/80" as one measurement, not two independent numbers that
// happen to live in separate fields. Each tile below groups the inputs that
// make up a single clinical reading (e.g. Systolic/Diastolic under one
// "Blood Pressure" label) so the whole panel can be scanned in <2 seconds.
function VitalSignsClinicalCard({ data, updateField, styles, COLORS }) {
  const tileStyle = {
    border: `1px solid ${COLORS.border}`,
    borderRadius: 8,
    padding: "8px 10px",
    background: COLORS.bg,
    display: "flex",
    flexDirection: "column",
    gap: 5,
    minWidth: 0,
  };
  const rowStyle = { display: "flex", alignItems: "center", gap: 6, flexWrap: "nowrap" };
  const numInputStyle = { ...styles.input, width: 52, textAlign: "center", padding: "5px 4px", flex: "0 0 auto" };
  const bpInputStyle = { ...styles.input, width: 46, textAlign: "center", padding: "5px 4px", flex: "0 0 auto", fontWeight: 700 };
  const unitStyle = { fontSize: 10.5, color: COLORS.gray, fontWeight: 600, whiteSpace: "nowrap" };
  const smallSelectStyle = { ...styles.select, fontSize: 10.5, padding: "3px 6px" };
  const unitToggleBtn = (active) => ({
    padding: "3px 7px", borderRadius: 5, fontSize: 10.5, fontWeight: 700, cursor: "pointer",
    border: `1px solid ${active ? COLORS.teal : COLORS.border}`,
    background: active ? COLORS.tealBg : "transparent",
    color: active ? COLORS.tealDark : COLORS.gray,
  });

  const temperatureUnit = data?.temperatureUnit || "F";

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10 }}>
      <div style={tileStyle}>
        <label style={styles.label}>Temperature</label>
        <div style={rowStyle}>
          <input style={numInputStyle} type="number" value={data?.temperature ?? ""} placeholder="98.6"
            onChange={(e) => updateField("temperature", e.target.value)} />
          <div style={{ display: "flex", gap: 4 }}>
            {["F", "C"].map((u) => (
              <button key={u} type="button" style={unitToggleBtn(temperatureUnit === u)}
                onClick={() => {
                  if (u === temperatureUnit) return;
                  updateField("temperature", convertTemperature(data?.temperature, temperatureUnit, u));
                  updateField("temperatureUnit", u);
                }}>°{u}</button>
            ))}
          </div>
        </div>
      </div>

      <div style={tileStyle}>
        <label style={styles.label}>Pulse</label>
        <div style={rowStyle}>
          <input style={numInputStyle} type="number" value={data?.pulse ?? ""}
            onChange={(e) => updateField("pulse", e.target.value)} />
          <span style={unitStyle}>bpm</span>
        </div>
        <select style={smallSelectStyle} value={data?.pulseQuality || ""}
          onChange={(e) => updateField("pulseQuality", e.target.value)}>
          <option value="">Quality — Select —</option>
          {["Strong", "Weak", "Thready", "Bounding", "Irregular"].map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      </div>

      <div style={tileStyle}>
        <label style={styles.label}>Respirations</label>
        <div style={rowStyle}>
          <input style={numInputStyle} type="number" value={data?.respirations ?? ""}
            onChange={(e) => updateField("respirations", e.target.value)} />
          <span style={unitStyle}>/min</span>
        </div>
      </div>

      {/* Blood Pressure is ONE clinical measurement — Systolic/Diastolic
          are rendered together under a single label, never as two
          independent top-level fields. */}
      <div style={tileStyle}>
        <label style={styles.label}>Blood Pressure</label>
        <div style={rowStyle}>
          <input style={bpInputStyle} type="number" value={data?.bloodPressure?.systolic ?? ""} placeholder="120"
            onChange={(e) => updateField("bloodPressure.systolic", e.target.value)} />
          <span style={{ fontSize: 15, fontWeight: 800, color: COLORS.dark, lineHeight: 1 }}>/</span>
          <input style={bpInputStyle} type="number" value={data?.bloodPressure?.diastolic ?? ""} placeholder="80"
            onChange={(e) => updateField("bloodPressure.diastolic", e.target.value)} />
          <span style={unitStyle}>mmHg</span>
        </div>
      </div>

      <div style={tileStyle}>
        <label style={styles.label}>Oxygen Saturation</label>
        <div style={rowStyle}>
          <input style={numInputStyle} type="number" value={data?.oxygenSaturation ?? ""}
            onChange={(e) => updateField("oxygenSaturation", e.target.value)} />
          <span style={unitStyle}>%</span>
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 10.5, color: COLORS.dark, cursor: "pointer" }}>
          <input type="checkbox" checked={!!data?.oxygenSaturationOnRA}
            onChange={(e) => updateField("oxygenSaturationOnRA", e.target.checked)} />
          On Room Air
        </label>
      </div>
    </div>
  );
}

function AnthropometricsAutoBmiCard({ data, updateField, styles, COLORS }) {
  const height = parseFloat(data?.height);
  const weight = parseFloat(data?.weight);
  const calculatedBmi = (!Number.isNaN(height) && !Number.isNaN(weight) && height > 0)
    ? Math.round((703 * weight / (height * height)) * 10) / 10
    : null;

  const lastAutoValue = useRef(null);
  useEffect(() => {
    if (calculatedBmi === null) return;
    const currentBmi = data?.bmi === "" || data?.bmi === undefined || data?.bmi === null ? null : parseFloat(data.bmi);
    // Only auto-fill when the field is empty or still equal to our own last
    // auto-calculated value — never overwrite an RN's manual entry.
    if (currentBmi === null || currentBmi === lastAutoValue.current) {
      lastAutoValue.current = calculatedBmi;
      if (currentBmi !== calculatedBmi) updateField("bmi", calculatedBmi);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [calculatedBmi]);

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 }}>
        <FormInput label="Height (in)" value={data?.height} onChange={(v) => updateField("height", v)} type="number" />
        <FormInput label="Weight (lbs)" value={data?.weight} onChange={(v) => updateField("weight", v)} type="number" />
        <FormInput label="BMI (auto-calculated)" value={data?.bmi ?? ""} onChange={(v) => updateField("bmi", v)} type="number" />
        <FormInput label="MAC (Mid-Arm Circumference)" value={data?.mac} onChange={(v) => updateField("mac", v)} type="number" />
      </div>
      {calculatedBmi !== null && (
        <div style={{ fontSize: 12, color: COLORS.gray, marginTop: 6 }}>
          Calculated from height/weight: {calculatedBmi}. Overwrite the BMI field above only if a manually verified value differs.
        </div>
      )}
      {calculatedBmi === null && (
        <div style={styles.infoBox}>Enter height and weight to auto-calculate BMI.</div>
      )}
    </div>
  );
}

// Read-only reference of the authoritative anthropometric/metabolic values
// (height/weight/BMI/MAC live under Vitals; serum albumin lives under LCD
// Evidence). These are NOT duplicated as new Nutrition fields — this card
// only displays the existing values in context for the nutrition assessment.
function NutritionAnthropometricReferenceCard({ fullFormData, styles, COLORS }) {
  const vitals = fullFormData?.vitals || {};
  const criteriaFacts = fullFormData?.diagnoses?.ndsEligibility?.criteriaFacts || {};
  const detectedDisease = fullFormData?.diagnoses?.ndsEligibility?.detectedDisease;
  const albumin = detectedDisease ? criteriaFacts?.[detectedDisease]?.serum_albumin : null;

  const hasAny = vitals.height || vitals.weight || vitals.bmi || vitals.mac || albumin;
  if (!hasAny) {
    return <div style={styles.infoBox}>Height, weight, BMI, and MAC are documented under Vitals & Measurements and will appear here for reference once entered.</div>;
  }

  const Item = ({ label, value }) => (
    <div>
      <div style={{ fontSize: 11, color: COLORS.gray, textTransform: "uppercase", letterSpacing: 0.3 }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 700 }}>{value || "—"}</div>
    </div>
  );

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12 }}>
      <Item label="Height" value={vitals.height ? `${vitals.height} in` : null} />
      <Item label="Weight" value={vitals.weight ? `${vitals.weight} lbs` : null} />
      <Item label="BMI" value={vitals.bmi} />
      <Item label="MAC" value={vitals.mac} />
      <Item label="Serum Albumin" value={albumin} />
    </div>
  );
}

// Auto-computes the 6-month weight-loss % from actual serial weight entries
// (RNICA/recert history) instead of relying on the RN to calculate it by
// hand into a free-text field. Purely a suggestion -- the RN must click
// "Insert" to accept it, so it never silently overwrites documented data.
function WeightLossAutoCalcCard({ patientId, assessmentId, currentWeight, existingValue, updateField, styles, COLORS }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [inserted, setInserted] = useState(false);

  useEffect(() => {
    if (!patientId) return;
    let active = true;
    setLoading(true);
    setError("");
    fetchPerformanceHistory(patientId)
      .then((res) => {
        if (active) setHistory(res?.history || []);
      })
      .catch((err) => {
        if (!active) return;
        console.error("Failed to load weight history:", err);
        setError("Unable to load prior weight history.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [patientId]);

  const suggestion = useMemo(() => {
    const current = parsePercentOrNumber(currentWeight);
    if (current === null) return null;

    const candidates = history.filter((h) => h.id !== assessmentId && h.weight !== null && h.weight !== undefined);
    if (!candidates.length) return null;

    const now = Date.now();
    const targetTime = now - 183 * 86400000; // ~6 months
    let best = null;
    let bestDiff = Infinity;
    candidates.forEach((h) => {
      const t = new Date(h.date).getTime();
      if (Number.isNaN(t)) return;
      const diff = Math.abs(t - targetTime);
      if (diff < bestDiff) {
        bestDiff = diff;
        best = h;
      }
    });
    if (!best || !best.weight) return null;

    const lossLbs = best.weight - current;
    const lossPercent = (lossLbs / best.weight) * 100;
    return {
      priorWeight: best.weight,
      priorDate: best.date,
      currentWeight: current,
      lossLbs,
      lossPercent,
      text: lossLbs > 0
        ? `${lossLbs.toFixed(1)} lbs (${lossPercent.toFixed(1)}%) over ~6 months (from ${best.weight} lbs on ${formatDate(best.date)} to ${current} lbs today)`
        : lossLbs < 0
          ? `Weight gain of ${Math.abs(lossLbs).toFixed(1)} lbs (${Math.abs(lossPercent).toFixed(1)}%) since ${formatDate(best.date)} — no loss to report`
          : `No change since ${formatDate(best.date)}`,
    };
  }, [history, currentWeight, assessmentId]);

  const handleInsert = () => {
    if (!suggestion) return;
    updateField("weightLossPastSixMonths", suggestion.text);
    setInserted(true);
    window.setTimeout(() => setInserted(false), 2000);
  };

  if (loading) {
    return <p style={{ color: COLORS.gray, fontSize: 13 }}>Checking prior weight history...</p>;
  }
  if (error) {
    return <p style={{ color: COLORS.error, fontSize: 13 }}>{error}</p>;
  }
  if (!currentWeight) {
    return <div style={styles.infoBox}>Enter the patient's current weight under Vitals to auto-calculate 6-month weight loss.</div>;
  }
  if (!suggestion) {
    return (
      <div style={styles.infoBox}>
        No prior weight on file within range to compute a trend yet. Document weight at each assessment to enable
        automatic 6-month weight-loss calculation going forward.
      </div>
    );
  }

  return (
    <div>
      <div style={styles.infoBox}>{suggestion.text}</div>
      {existingValue && (
        <div style={{ fontSize: 12, color: COLORS.gray, marginTop: 6 }}>
          Current documented value: "{existingValue}"
        </div>
      )}
      <button type="button" onClick={handleInsert} style={{
        marginTop: 8, padding: "6px 12px", borderRadius: 6, border: `1px solid ${COLORS.teal}`,
        background: inserted ? COLORS.teal : "transparent", color: inserted ? COLORS.white : COLORS.teal,
        fontSize: 12, fontWeight: 700, cursor: "pointer",
      }}>
        {inserted ? "Inserted!" : "Insert into Weight Loss field"}
      </button>
    </div>
  );
}

// Integumentary -> Treatment Summary (read-only).
//
// Per owner directive: Skin/Integumentary assessment findings live in
// Body Systems; wound/skin TREATMENT (dressings, frequency, DME) stays
// owned by Orders & POC / Tx-Meds-DME. There is no separate
// WoundTreatment/TreatmentOrder backend entity in this codebase today —
// confirmed by inspecting app/models and app/api/routes/rnica_poc.py: the
// only structured "treatment" data already captured against the skin
// section is the intervention_text on that section's Plan of Care
// problems (the same PocSectionControls Add/View/Update/Resolve API
// below). This component does not add a new data model or duplicate
// entry; it only reads those existing records and displays the
// intervention text as an "Active Treatments" list, with a link to the
// real Orders & POC screen (the single source of truth) instead of
// re-implementing treatment management inside Body Systems.
function SkinTreatmentSummary({ assessmentId, patientId, styles, COLORS }) {
  const [problems, setProblems] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!assessmentId) return;
    let cancelled = false;
    setLoading(true);
    viewRnicaSectionPoc(assessmentId, "skin")
      .then((res) => {
        if (!cancelled) setProblems(Array.isArray(res?.problems) ? res.problems : []);
      })
      .catch(() => {
        if (!cancelled) setProblems([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [assessmentId]);

  const activeTreatments = (problems || []).filter(
    (p) => p.status !== "RESOLVED" && p.intervention_text && p.intervention_text.trim()
  );

  if (loading) return null;
  if (!problems || activeTreatments.length === 0) return null;

  return (
    <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px dashed ${COLORS.border}` }}>
      <div style={{ fontSize: 11.5, fontWeight: 800, color: COLORS.gray, textTransform: "uppercase", letterSpacing: "0.03em", marginBottom: 6 }}>
        Active Treatments
      </div>
      <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12.5 }}>
        {activeTreatments.map((p) => (
          <li key={p.rule_key} style={{ marginBottom: 3 }}>{p.intervention_text}</li>
        ))}
      </ul>
      <button
        type="button"
        onClick={() => window.open(`/plan-of-care?patientId=${encodeURIComponent(patientId || "")}#tx-meds-dme-supplies`, "_blank", "noopener")}
        style={{
          marginTop: 8, fontSize: 11, fontWeight: 700, padding: "5px 10px", borderRadius: 5,
          border: `1px solid ${COLORS.teal}`, background: "transparent", color: COLORS.teal, cursor: "pointer",
        }}
      >
        View Treatment Details →
      </button>
    </div>
  );
}

// RN ICA -> Plan of Care controls for a single body-system subcard.
// Add / View / Update / Resolve here all call the authoritative Plan of
// Care document API (via backend app/services/rnica_poc_adapter.py) — this
// component holds no POC state of its own beyond what it fetches on demand,
// and never writes into RnicaAssessment.form_data.
//
// Bounded Compatibility Increment (2026-09-28) Section 9/21/AC-04 --
// `canAdd` (default true, so every existing section behaves exactly as
// before) lets a caller hide the generic "+ Add to POC" button when no
// confirmed actionable finding exists yet. `suggestedFinding`, when set,
// renders a small "POC Review Suggested" indicator instead of silently
// changing the button's own label -- the clinician still explicitly
// clicks Add; nothing is auto-created.
function PocSectionControls({ assessmentId, sectionKey, cardTitle, styles, COLORS, canAdd = true, suggestedFinding = false }) {
  const [showAdd, setShowAdd] = useState(false);
  const [showList, setShowList] = useState(false);
  const [problems, setProblems] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState({ problem_label: "", evidence_text: "", goal_text: "", intervention_text: "" });
  const [editingRuleKey, setEditingRuleKey] = useState(null);
  const [editDraft, setEditDraft] = useState({ severity: "", description_addendum: "" });

  const loadProblems = useCallback(() => {
    if (!assessmentId) return;
    setLoading(true);
    setError("");
    viewRnicaSectionPoc(assessmentId, sectionKey)
      .then((res) => setProblems(res?.problems || []))
      .catch((err) => setError(err.message || "Unable to load Plan of Care"))
      .finally(() => setLoading(false));
  }, [assessmentId, sectionKey]);

  // Quietly check whether this section already has any POC problems (not
  // just on-demand when the RN opens the list) so "View POC" only ever
  // appears once there's something to view — a section with no linked
  // problems yet shows only "+ Add to POC".
  useEffect(() => {
    if (!assessmentId) return;
    let active = true;
    viewRnicaSectionPoc(assessmentId, sectionKey)
      .then((res) => { if (active) setProblems(res?.problems || []); })
      .catch(() => { /* silent — this is just existence-check prefetch */ });
    return () => { active = false; };
  }, [assessmentId, sectionKey]);

  const hasProblems = (problems?.length || 0) > 0;

  const handleToggleList = () => {
    const next = !showList;
    setShowList(next);
    if (next) loadProblems();
  };

  const handleAdd = () => {
    if (!draft.problem_label.trim() || !draft.evidence_text.trim()) {
      setError("Problem and supporting evidence are both required to add to the Plan of Care.");
      return;
    }
    setSaving(true);
    setError("");
    addRnicaSectionPocProblem(assessmentId, sectionKey, {
      problem_label: draft.problem_label.trim(),
      evidence_text: draft.evidence_text.trim(),
      goal_text: draft.goal_text.trim() || undefined,
      intervention_text: draft.intervention_text.trim() || undefined,
      discipline: "RN",
    })
      .then(() => {
        setDraft({ problem_label: "", evidence_text: "", goal_text: "", intervention_text: "" });
        setShowAdd(false);
        setShowList(true);
        loadProblems();
      })
      .catch((err) => setError(err.message || "Unable to add problem to Plan of Care"))
      .finally(() => setSaving(false));
  };

  const handleResolve = (ruleKey) => {
    setSaving(true);
    setError("");
    resolveRnicaSectionPocProblem(assessmentId, sectionKey, ruleKey)
      .then(() => loadProblems())
      .catch((err) => setError(err.message || "Unable to resolve Plan of Care problem"))
      .finally(() => setSaving(false));
  };

  const handleUpdate = (ruleKey) => {
    setSaving(true);
    setError("");
    updateRnicaSectionPocProblem(assessmentId, sectionKey, ruleKey, {
      severity: editDraft.severity || undefined,
      description_addendum: editDraft.description_addendum.trim() || undefined,
    })
      .then(() => {
        setEditingRuleKey(null);
        setEditDraft({ severity: "", description_addendum: "" });
        loadProblems();
      })
      .catch((err) => setError(err.message || "Unable to update Plan of Care problem"))
      .finally(() => setSaving(false));
  };

  if (!assessmentId) return null;

  return (
    <div style={{ marginTop: 12, paddingTop: 12, borderTop: `1px dashed ${COLORS.border}` }}>
      {suggestedFinding && canAdd && !hasProblems && (
        <p style={{ margin: "0 0 6px", fontSize: 11, fontWeight: 700, color: COLORS.orange || "#b45309" }}>
          POC Review Suggested
        </p>
      )}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {canAdd && (
          <button type="button" onClick={() => setShowAdd((v) => !v)} style={{
            fontSize: 11.5, fontWeight: 700, padding: "6px 10px", borderRadius: 6,
            border: `1px solid ${COLORS.teal}`, background: showAdd ? COLORS.teal : "transparent",
            color: showAdd ? COLORS.white : COLORS.teal, cursor: "pointer",
          }}>
            + Add to POC
          </button>
        )}
        {hasProblems && (
          <button type="button" onClick={handleToggleList} style={{
            fontSize: 11.5, fontWeight: 700, padding: "6px 10px", borderRadius: 6,
            border: `1px solid ${COLORS.gray}`, background: showList ? COLORS.gray : "transparent",
            color: showList ? COLORS.white : COLORS.gray, cursor: "pointer",
          }}>
            {showList ? "Hide POC" : "View POC"}
          </button>
        )}
      </div>

      {error && <div style={{ color: COLORS.error, fontSize: 12, marginTop: 8 }}>{error}</div>}

      {showAdd && (
        <div style={{ marginTop: 10, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 8 }}>
          <FormInput label="Problem" value={draft.problem_label} onChange={(v) => setDraft((d) => ({ ...d, problem_label: v }))}
            placeholder={`e.g., ${cardTitle || "clinical"} finding requiring intervention`} />
          <FormInput label="Supporting Evidence / Finding" value={draft.evidence_text} onChange={(v) => setDraft((d) => ({ ...d, evidence_text: v }))}
            placeholder="What was assessed/observed" />
          <FormInput label="Goal (optional)" value={draft.goal_text} onChange={(v) => setDraft((d) => ({ ...d, goal_text: v }))} />
          <FormInput label="Intervention (optional)" value={draft.intervention_text} onChange={(v) => setDraft((d) => ({ ...d, intervention_text: v }))} />
          <button type="button" disabled={saving} onClick={handleAdd} style={{
            fontSize: 12, fontWeight: 700, padding: "8px 12px", borderRadius: 6, border: "none",
            background: COLORS.teal, color: COLORS.white, cursor: saving ? "wait" : "pointer", height: 36, alignSelf: "end",
          }}>
            {saving ? "Saving…" : "Save to Plan of Care"}
          </button>
        </div>
      )}

      {showList && (
        <div style={{ marginTop: 10 }}>
          {loading && <div style={{ fontSize: 12, color: COLORS.gray }}>Loading Plan of Care…</div>}
          {!loading && problems && problems.length === 0 && (
            <div style={styles.infoBox}>No Plan of Care problems linked to this section yet.</div>
          )}
          {!loading && problems && problems.map((p) => (
            <div key={p.rule_key} style={{
              padding: "8px 10px", borderRadius: 8, border: `1px solid ${COLORS.border}`,
              marginBottom: 6, fontSize: 12.5, background: p.status === "RESOLVED" ? COLORS.bg : "transparent",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                <strong>{p.label}</strong>
                <span style={{ fontWeight: 700, color: p.status === "RESOLVED" ? COLORS.gray : COLORS.teal }}>
                  {p.status} {p.severity && p.severity !== "UNKNOWN" ? `· ${p.severity}` : ""}
                </span>
              </div>
              {p.description && <div style={{ color: COLORS.gray, fontSize: 11.5, marginTop: 4, whiteSpace: "pre-wrap" }}>{p.description}</div>}
              {p.status !== "RESOLVED" && (
                <div style={{ marginTop: 6, display: "flex", gap: 6 }}>
                  <button type="button" onClick={() => setEditingRuleKey(editingRuleKey === p.rule_key ? null : p.rule_key)}
                    style={{ fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5, border: `1px solid ${COLORS.teal}`, background: "transparent", color: COLORS.teal, cursor: "pointer" }}>
                    Update POC
                  </button>
                  <button type="button" disabled={saving} onClick={() => handleResolve(p.rule_key)}
                    style={{ fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5, border: `1px solid ${COLORS.gray}`, background: "transparent", color: COLORS.gray, cursor: "pointer" }}>
                    Resolve POC
                  </button>
                </div>
              )}
              {editingRuleKey === p.rule_key && (
                <div style={{ marginTop: 8, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 8 }}>
                  <FormSelect label="Severity" value={editDraft.severity} onChange={(v) => setEditDraft((d) => ({ ...d, severity: v }))}
                    options={["LOW", "MODERATE", "HIGH", "CRITICAL"]} />
                  <FormInput label="Update / Progress Note" value={editDraft.description_addendum}
                    onChange={(v) => setEditDraft((d) => ({ ...d, description_addendum: v }))} />
                  <button type="button" disabled={saving} onClick={() => handleUpdate(p.rule_key)} style={{
                    fontSize: 11.5, fontWeight: 700, padding: "6px 10px", borderRadius: 5, border: "none",
                    background: COLORS.teal, color: COLORS.white, cursor: saving ? "wait" : "pointer", alignSelf: "end",
                  }}>
                    {saving ? "Saving…" : "Save Update"}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// SECTION 5B (Admissions Order) — Discipline Frequency of Visit. Physician-
// ordered visit frequency, one row per discipline, added on demand — not a
// fixed 5-discipline table. Any discipline the patient needs (PT/OT/ST,
// dietitian, podiatry consult, an upcoming F2F-driving MD visit, etc.) can
// be added via "+ Add Discipline", each with its own number-of-visits /
// period, or a free-text "specify as required" override for anything that
// doesn't fit the standard period picklist.
function DisciplineFrequencyOfVisitCard({ rows, onChange, styles, COLORS }) {
  const list = Array.isArray(rows) ? rows : [];

  const updateRow = (idx, patch) => {
    onChange(list.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  };

  const removeRow = (idx) => {
    onChange(list.filter((_, i) => i !== idx));
  };

  const addRow = () => {
    onChange([...list, { discipline: "", numberOfVisits: "", period: "", specify: "" }]);
  };

  return (
    <div>
      <div style={{ ...styles.infoBox, marginBottom: 10 }}>
        Physician-ordered visit frequency for every discipline on this patient's plan of care. Add a row for each
        discipline needed — core IDG disciplines are pre-populated below, but any discipline can be added or removed.
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {list.map((row, idx) => (
          <div key={idx} style={{
            display: "grid", gridTemplateColumns: "1.3fr 0.7fr 1.3fr 1.6fr auto", gap: 8, alignItems: "end",
            padding: "8px 10px", borderRadius: 8, border: `1px solid ${COLORS.border}`, background: COLORS.bg,
          }}>
            <FormSelect
              label="Discipline"
              value={row.discipline}
              onChange={(v) => updateRow(idx, { discipline: v })}
              options={VISIT_FREQUENCY_DISCIPLINE_OPTIONS}
            />
            <FormSelect
              label="No. of Visits"
              value={row.numberOfVisits}
              onChange={(v) => updateRow(idx, { numberOfVisits: v })}
              options={VISIT_FREQUENCY_COUNT_OPTIONS}
            />
            <FormSelect
              label="Period"
              value={row.period}
              onChange={(v) => updateRow(idx, { period: v })}
              options={VISIT_FREQUENCY_PERIOD_OPTIONS}
            />
            <FormInput
              label="Or specify as required"
              value={row.specify || row.frequency || ""}
              onChange={(v) => updateRow(idx, { specify: v })}
              placeholder="e.g., within 5 days of admission then RECERT and PRN"
            />
            <button
              type="button"
              onClick={() => removeRow(idx)}
              title="Remove this discipline"
              style={{
                border: "none", background: "transparent", color: COLORS.gray, cursor: "pointer",
                fontSize: 16, fontWeight: 700, height: 34, alignSelf: "end",
              }}
            >
              ×
            </button>
          </div>
        ))}
        {list.length === 0 && (
          <div style={{ fontSize: 12, color: COLORS.gray }}>No disciplines added yet.</div>
        )}
      </div>
      <button
        type="button"
        onClick={addRow}
        style={{
          marginTop: 10, fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5,
          border: `1px solid ${COLORS.teal}`, background: "transparent", color: COLORS.teal, cursor: "pointer",
        }}
      >
        + Add Discipline
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------------
// CHHA (Home Health Aide) Plan of Care. RN-authored once per patient, lives at
// PatientChart's 'chha-assignment' destination (linked from RN ICA's HA
// Assignment card, and reachable from the CHHA/HHA nav group, so it's never
// forgotten once a patient has an aide assigned). Data is stored on the SAME
// RN ICA assessment record (form_data.chhaPoc) -- there is no separate CHHA
// data store, so this reads/writes through the same
// getRnicaAssessmentByPatient / updateRnicaAssessment endpoints RNICA itself
// uses.
//
// Deliberately does NOT list medications (an aide does not need drug names
// or doses) -- instead, the "Safety Alerts & Report To" banner below is
// auto-derived from documented risk factors (fall risk level, oxygen use,
// aspiration/swallowing risk, skin breakdown risk, and active
// anticoagulant/opioid/diabetes medication classes) so the relevant plain-
// language precaution + "call [Report To] if you see this" symptom is
// always surfaced -- the RN never has to remember to write it in by hand.
// "Report To" is configurable (RN / RN and MD / MD) rather than hardcoded
// to "RN office", since who the aide escalates to can differ once
// LVN-authored plans exist. Any suggested alert can still be dismissed if
// it doesn't apply, and custom alerts can be added.
// ---------------------------------------------------------------------------------

// Each task category expands into the specific, checkable interventions a
// real HA order actually needs (equipment, catheter/colostomy care, diet
// specifics, bed-rail configuration, razor type, etc.) -- a single
// "Ambulation" checkbox with a free-text Instructions box was too vague to
// act as the standing order. `detail: true` items show a required
// specify-box when checked (e.g., which diet, which vitals, bed rail sides).
const CHHA_TASK_OPTIONS = [
  {
    value: "Ambulation", label: "Ambulation",
    items: [
      { code: "AD_LIB", label: "Ambulates ad lib (no restriction)" },
      { code: "RESTRICTED", label: "Ambulation restricted", detail: true, detailLabel: "Restriction (specify distance/limits)" },
      { code: "WALKER", label: "Uses walker" },
      { code: "CANE", label: "Uses cane" },
      { code: "WHEELCHAIR", label: "Uses wheelchair" },
      { code: "GERI_CHAIR", label: "Uses geri chair (every visit)" },
      { code: "BEDBOUND", label: "Bedbound" },
      { code: "CHAIR_TO_BED", label: "Chair-to-bed only" },
      { code: "BED_RAILS", label: "Bed rails up (every visit)", detail: true, detailLabel: "Type & side(s) — e.g. full rail both sides, half rail left only" },
      { code: "CLEAR_PATH", label: "Keep walking path/objects within reach clear (every visit)" },
      { code: "LOW_BED", label: "Keep bed in low position (every visit)" },
      { code: "REPOSITION", label: "Turn and reposition patient (every visit)", detail: true, detailLabel: "How often / which side(s)" },
    ],
  },
  {
    value: "Toileting/Continence Care", label: "Toileting / Continence Care",
    items: [
      { code: "BATHROOM", label: "Assist to bathroom" },
      { code: "COMMODE", label: "Assist with bedside commode" },
      { code: "BEDPAN", label: "Assist with bedpan" },
      { code: "URINAL", label: "Assist with urinal (every visit)" },
      { code: "ADULT_DIAPERS", label: "Adult diapers" },
      { code: "BRIEFS", label: "Briefs (every visit)" },
      { code: "URINARY_CONTINENT", label: "Continent — urinary" },
      { code: "URINARY_INCONTINENT", label: "Incontinent — urinary (incontinence care every visit)" },
      { code: "FOLEY_CARE", label: "Foley catheter care (every visit)" },
      { code: "CONDOM_CATH", label: "Condom catheter — reapply (every visit)" },
      { code: "MEASURE_OUTPUT", label: "Measure and record urinary output (every visit)" },
      { code: "EMPTY_BAG", label: "Empty urinary collection bag" },
      { code: "BOWEL_CONTINENT", label: "Continent — bowel" },
      { code: "BOWEL_INCONTINENT", label: "Incontinent — bowel (incontinence care, record bowel movements every visit)" },
      { code: "COLOSTOMY_CARE", label: "Colostomy care / empty bag" },
    ],
  },
  {
    value: "Transfer", label: "Transfer",
    items: [
      { code: "ONE_PERSON", label: "1-person assist" },
      { code: "TWO_PERSON", label: "2-person assist" },
      { code: "MECHANICAL_LIFT", label: "Mechanical lift" },
      { code: "FALL_PRECAUTION", label: "Fall precaution (every visit)" },
    ],
  },
  {
    value: "Dressing", label: "Dressing",
    items: [
      { code: "STREET_CLOTHES", label: "Street clothes" },
      { code: "PAJAMAS", label: "Pajamas / gown" },
      { code: "DRESS_EVERY_VISIT", label: "Dress patient (every visit)" },
    ],
  },
  {
    value: "Feeding", label: "Feeding",
    items: [
      { code: "DIET_ORDER", label: "Diet order", detail: true, detailLabel: "Specify diet (e.g., mechanical soft, NAS, thickened liquids)" },
      { code: "ASPIRATION_PRECAUTION", label: "Aspiration precaution (every visit)" },
      { code: "MEAL_PREP", label: "Prepare meal(s)", detail: true, detailLabel: "Which meals (breakfast/lunch/dinner/snack)" },
      { code: "FEEDING_ASSIST", label: "Feeding assistance (every visit)" },
      { code: "ORAL_MED_ASSIST", label: "Assist with oral medication as ordered" },
      { code: "ENCOURAGE_FLUIDS", label: "Encourage fluids as tolerated if not contraindicated (every visit)" },
    ],
  },
  {
    value: "Bathing/Hygiene", label: "Bathing / Hygiene",
    items: [
      { code: "BATH", label: "Bath (every visit)", detail: true, detailLabel: "Type — shower, tub bath, bed bath, or shower chair" },
      { code: "HAIR_CARE", label: "Hair care — brush/comb/shampoo (every visit)" },
      { code: "FACIAL_HAIR", label: "Facial hair care — use electric razor, not a blade, unless otherwise ordered (every visit)" },
      { code: "MOUTH_CARE", label: "Mouth care — brush teeth / clean dentures (every visit)" },
      { code: "NAIL_CARE", label: "Nail care — clean and file (every visit)" },
      { code: "DEODORANT", label: "Apply deodorant (every visit)" },
      { code: "LOTION", label: "Apply lotion (every visit)" },
      { code: "SKIN_VISUALIZE", label: "Visualize skin condition and report to RN (every visit)" },
      { code: "PERI_CARE", label: "Peri care (every visit)" },
    ],
  },
  {
    value: "Light Housekeeping", label: "Light Housekeeping (patient-care related)",
    items: [
      { code: "CHANGE_LINENS", label: "Change patient linens (every visit)" },
      { code: "TIDY_ROOM", label: "Tidy patient's immediate area / empty trash (every visit)" },
      { code: "COMPANION", label: "Provide companionship/supervision as ordered" },
    ],
  },
  {
    value: "Vital Signs", label: "Vital Signs Monitoring",
    items: [
      { code: "CHECK_VITALS", label: "Check and record vital signs (every visit)", detail: true, detailLabel: "Which parameters (e.g., temp, pulse, respirations, BP, O2 sat, weight)" },
    ],
  },
];

// Fixed scope-of-practice caption per task -- every task carries a
// plain-language reminder of what is (and is not) within scope, in addition
// to whatever the RN writes in Instructions. Static text, not
// patient-specific, so it is not persisted.
const CHHA_TASK_GUIDANCE = {
  "Ambulation": "Assist only per the device/assist level checked below. Do not adjust the assist level yourself even if the patient asks.",
  "Transfer": "Use the assist level and equipment (gait belt, walker, wheelchair) checked below every time. Do not attempt a higher-risk transfer alone.",
  "Toileting/Continence Care": "Follow the assist level checked below. Report any change in continence, blood, or unusual color/odor -- do not assess or diagnose it yourself.",
  "Dressing": "Assist per the level checked below. Report any new skin changes noticed while dressing instead of treating them.",
  "Feeding": "Follow the diet/texture checked below exactly, including thickened liquids if ordered. Never change a patient's diet texture on your own.",
  "Bathing/Hygiene": "Follow water-temperature and skin precautions checked below. Report any new redness, wound, or bruising instead of treating it.",
  "Light Housekeeping": "Patient-care-related tasks only (e.g., changing linens, tidying patient's immediate area). Not general household chores.",
  "Vital Signs": "Record only -- do not interpret the reading or decide it is \"fine.\" Report any value outside the range given below immediately.",
};

const CHHA_DEPENDENCE_OPTIONS = ["Independent", "Assist", "Complete Dependence"];
const CHHA_TASK_FREQUENCY_OPTIONS = ["Every visit", "As needed (see instructions for exactly when)"];
// Minimum safe assist level for ANY transfer/repositioning of this patient --
// a hard staffing/safety requirement, never left to the HA's judgment
// (a caregiver who weighs 90 lbs must never be relied on to manually move a
// 300+ lb patient). Feeds a mandatory "Transfer / Lift Safety" guidance
// category and gates the Transfer task options below.
const CHHA_MINIMUM_ASSIST_OPTIONS = [
  "Independent",
  "1-person assist",
  "2-person assist required",
  "Mechanical lift required — no manual lift",
];

// Visit-time fact checklist per ordered task category -- what the HA
// actually saw/did during THIS visit, captured as fixed checkboxes instead
// of a free-text narrative. Narrative is unreliable (vague, inconsistent,
// easy to skip); a checklist forces a specific, auditable answer every time.
// At least one box is required whenever the task is marked "Completed as
// ordered" so the record always shows exactly what was done, not just that
// "something" was done.
// Checklist codes that mean "another staff member physically helped" -- when
// any of these are checked, we require the aide to name who assisted, both
// for staffing-safety accountability and because a solo bariatric/lift
// transfer is a documented safety violation.
const ASSIST_NAME_TRIGGER_CODES = ["SECOND_PERSON_PRESENT", "TWO_PERSON_BATH_TRANSFER"];

const CHHA_VISIT_FACT_OPTIONS = {
  "Ambulation": [
    { code: "USED_ORDERED_DEVICE", label: "Used the ordered device/assist level (walker, cane, wheelchair, etc.)" },
    { code: "BED_RAILS_UP", label: "Bed rails placed up as ordered" },
    { code: "PATH_CLEAR", label: "Walking path/objects kept clear" },
    { code: "LOW_BED", label: "Bed kept in low position" },
    { code: "REPOSITIONED", label: "Repositioned/turned per schedule" },
    { code: "NO_NEW_MOBILITY_ISSUE", label: "No new weakness, balance problem, or fall observed" },
  ],
  "Toileting/Continence Care": [
    { code: "ASSISTED_TOILETING", label: "Assisted to bathroom/commode/bedpan as ordered" },
    { code: "CHANGED_BRIEF", label: "Changed brief/diaper" },
    { code: "INCONTINENCE_CARE", label: "Provided incontinence care" },
    { code: "MEASURED_OUTPUT", label: "Emptied/measured output as ordered" },
    { code: "NO_NEW_FINDING", label: "No change in color, odor, or amount noted" },
  ],
  "Transfer": [
    { code: "USED_GAIT_BELT", label: "Used gait belt" },
    { code: "USED_MECH_LIFT", label: "Used mechanical lift" },
    { code: "SECOND_PERSON_PRESENT", label: "A second person physically assisted (name required below)" },
    { code: "FOLLOWED_ORDERED_LEVEL", label: "Followed the ordered assist level — did not attempt a lower-assist transfer alone" },
    { code: "FALL_PRECAUTIONS", label: "Fall precautions followed" },
  ],
  "Dressing": [
    { code: "DRESSED_AS_ORDERED", label: "Dressed patient as ordered" },
    { code: "NO_NEW_SKIN_FINDING", label: "No new skin change noticed while dressing" },
  ],
  "Feeding": [
    { code: "FOLLOWED_DIET_ORDER", label: "Followed the ordered diet/texture exactly" },
    { code: "ASSISTED_FEEDING", label: "Physically assisted with feeding" },
    { code: "UPRIGHT_DURING_MEAL", label: "Patient upright during the meal" },
    { code: "ASSISTED_ORAL_MEDS", label: "Assisted with oral medication" },
    { code: "ENCOURAGED_FLUIDS", label: "Encouraged fluids as tolerated" },
    { code: "NO_SWALLOWING_ISSUE", label: "No coughing, choking, or pocketing observed" },
  ],
  "Bathing/Hygiene": [
    { code: "BED_BATH", label: "Bed bath given (patient not moved to shower/tub)" },
    { code: "SHOWER_TUB_BATH", label: "Shower/tub bath given" },
    { code: "USED_SHOWER_CHAIR", label: "Used shower chair" },
    { code: "USED_MECH_LIFT_BATH", label: "Used mechanical lift to bathe" },
    { code: "TWO_PERSON_BATH_TRANSFER", label: "2-person transfer used to bathe" },
    { code: "HYGIENE_COMPLETED", label: "Hair/mouth/nail/skin care completed as ordered" },
    { code: "NO_NEW_SKIN_FINDING_BATH", label: "Skin visualized — no new findings" },
  ],
  "Light Housekeeping": [
    { code: "CHANGED_LINENS", label: "Changed patient linens" },
    { code: "TIDIED_AREA", label: "Tidied patient's immediate area" },
  ],
  "Vital Signs": [
    { code: "VITALS_IN_RANGE", label: "Vitals recorded, within the range ordered" },
    { code: "VITALS_OUT_OF_RANGE", label: "Vitals recorded, outside the range ordered — reported to RN" },
  ],
};

// Name fragments used ONLY to derive a plain-language safety alert -- the
// medication list itself is never shown in the CHHA POC.
const CHHA_ANTICOAGULANT_KEYWORDS = ["warfarin", "coumadin", "eliquis", "apixaban", "xarelto", "rivaroxaban", "heparin", "lovenox", "enoxaparin", "plavix", "clopidogrel", "pradaxa", "dabigatran", "savaysa", "edoxaban"];
const CHHA_OPIOID_KEYWORDS = ["morphine", "oxycodone", "oxycontin", "hydrocodone", "hydromorphone", "dilaudid", "fentanyl", "methadone", "roxanol"];
const CHHA_DIABETES_KEYWORDS = ["insulin", "metformin", "glipizide", "glyburide", "glimepiride", "januvia", "jardiance", "farxiga", "ozempic", "trulicity", "lantus", "novolog", "humalog"];

const CHHA_REPORT_TO_OPTIONS = [
  { value: "RN", label: "RN / Hospice Nurse" },
  { value: "RN_AND_MD", label: "RN and MD" },
  { value: "MD", label: "MD" },
];

function chhaTextIncludesAny(text, keywords) {
  const lower = (text || "").toLowerCase();
  return keywords.some((k) => lower.includes(k));
}

function chhaReportToLabel(reportToRole) {
  if (reportToRole === "RN_AND_MD") return "RN and MD";
  if (reportToRole === "MD") return "MD";
  return "RN";
}

// Derives structured, caregiver-safe guidance from data already documented
// elsewhere in the chart -- never invented, always traceable to a specific
// field. Per the "caregiver guidance engine" rule: clinical terms (Dysphagia,
// Anticoagulation therapy, Aspiration risk, pressure-injury staging, etc.)
// are NEVER surfaced here -- only the caregiver-safe risk label, what to
// observe, what to do, and when to escalate. `reportToRole` is configurable
// (default RN) since who the aide escalates to can differ once LVN-authored
// plans exist (report to RN and MD, or MD directly).
function deriveChhaCareGuidance({ formData, medications, reportToRole, minimumAssistLevel }) {
  const reportTo = chhaReportToLabel(reportToRole);
  const categories = [];
  const activeMeds = (medications || []).filter((m) => !m.status || m.status === "active");
  const medNames = activeMeds.map((m) => m.medication_name || "").join(" ");
  const diagnosisText = `${formData?.diagnoses?.primaryDiagnosis?.description || ""} ${(formData?.diagnoses?.secondaryDiagnoses || []).map((d) => d?.description || "").join(" ")}`;

  const fallRiskLevel = formData?.safety?.fallRiskLevel;
  if (fallRiskLevel === "Moderate" || fallRiskLevel === "High") {
    categories.push({
      key: "fallRisk",
      riskLabel: "Fall Risk",
      observe: ["Increased weakness", "Difficulty standing", "New balance problems"],
      safety: ["Keep pathways clear", "Lock wheelchair/bed brakes before any transfer", "Use walker/cane if ordered", "Do not leave the patient unattended during a transfer"],
      escalate: [`Any fall, near fall, or sudden weakness — call ${reportTo} immediately`],
    });
  }
  // Transfer/lift safety is a staff-injury risk, not just a patient-care
  // preference -- never rely on the HA to judge whether they personally can
  // lift the patient. If the RN has ordered 2-person or mechanical-lift
  // assist, that is a hard requirement surfaced everywhere, the same way
  // fall risk or oxygen precautions are.
  if (minimumAssistLevel === "2-person assist required" || minimumAssistLevel === "Mechanical lift required — no manual lift") {
    categories.push({
      key: "transferSafety",
      riskLabel: "Transfer / Lift Safety",
      observe: ["Any transfer that cannot be done at the required assist level", "Strain, pain, or skin shearing to the patient or caregiver during a transfer"],
      safety: [
        `Required assist level: ${minimumAssistLevel}. Never attempt a lower level of assist, even if it seems faster or no one else is available.`,
        "Wait for a second caregiver before starting if 2-person assist is required — do not attempt alone",
        "Use the mechanical lift/equipment ordered every time, not manual lifting",
      ],
      escalate: [`Unable to safely transfer the patient at the required assist level, or any caregiver/patient injury during a transfer — call ${reportTo} immediately`],
    });
  }
  if (formData?.safety?.oxygenInUse) {
    categories.push({
      key: "oxygen",
      riskLabel: "Oxygen Use",
      observe: ["Increased breathing difficulty", "Restlessness", "Lips or skin looking bluish/dusky", "Patient removing the oxygen"],
      safety: ["No smoking or open flame near the oxygen", "Keep tubing secured, not a tripping hazard", "Do not change the flow rate yourself"],
      escalate: [`Increased shortness of breath, oxygen not helping, or equipment malfunction — call ${reportTo} immediately`],
    });
  }
  const swallowing = formData?.nutrition?.swallowingIssues || [];
  if (["Dysphagia", "Aspiration risk", "Coughing with swallowing"].some((s) => swallowing.includes(s))) {
    categories.push({
      key: "swallowing",
      riskLabel: "Swallowing Precautions",
      observe: ["Coughing during meals", "Choking", "Food pocketing in the cheeks", "Wet or gurgly voice after swallowing"],
      safety: ["Keep the patient upright during and after meals", "Follow the diet/texture ordered exactly", "Small bites, slow feeding — never rush"],
      escalate: [`Choking episode, unable to swallow, refusing food due to swallowing difficulty, or increased coughing during meals — call ${reportTo} immediately`],
    });
  }
  const pressureRisk = formData?.skinWounds?.pressureInjuryRisk || "";
  if (pressureRisk.startsWith("High") || pressureRisk.startsWith("Moderate")) {
    categories.push({
      key: "skin",
      riskLabel: "Skin Precautions",
      observe: ["Redness", "Open areas", "Drainage", "Swelling"],
      safety: ["Reposition exactly per the schedule ordered", "Keep skin clean and dry"],
      escalate: [`New skin breakdown, drainage, or worsening redness — call ${reportTo} immediately`],
    });
  }
  if (chhaTextIncludesAny(medNames, CHHA_ANTICOAGULANT_KEYWORDS)) {
    categories.push({
      key: "bleeding",
      riskLabel: "Bleeding Precautions",
      observe: ["New bruising", "Bleeding gums", "Blood in urine or stool", "Black/tarry stool", "Nosebleeds", "Pale skin color"],
      safety: ["Use an electric razor, not a blade", "Use a soft-bristle toothbrush", "Avoid activities likely to cause cuts or skin injury", "Report falls immediately, even minor ones"],
      escalate: [`Any bleeding, significant bruising, a fall with head impact, or pale skin color — call ${reportTo} immediately`],
    });
  }
  if (chhaTextIncludesAny(medNames, CHHA_OPIOID_KEYWORDS)) {
    categories.push({
      key: "sedation",
      riskLabel: "Pain Medication Precautions",
      observe: ["Excessive sleepiness or difficulty waking", "Slow or shallow breathing", "Unrelieved pain"],
      safety: ["Do not adjust medication timing or dose yourself"],
      escalate: [`Excessive sleepiness/difficulty waking, slow or shallow breathing, or unrelieved pain — call ${reportTo} immediately`],
    });
  }
  if (chhaTextIncludesAny(medNames, CHHA_DIABETES_KEYWORDS) || chhaTextIncludesAny(diagnosisText, ["diabet"])) {
    categories.push({
      key: "glucose",
      riskLabel: "Blood Sugar Precautions",
      observe: ["Shakiness", "Sweating", "Confusion", "Other signs of low blood sugar"],
      safety: ["Follow the diet ordered", "Do not give food/juice on your own to \"treat\" a suspected episode without an order"],
      escalate: [`Shakiness, sweating, confusion, or other signs of low blood sugar — call ${reportTo} immediately`],
    });
  }
  return categories;
}

const DEFAULT_CHHA_POC = {
  tasks: [],
  dietInstructions: "",
  additionalInstructions: "",
  reportToRole: "RN",
  patientWeightLbs: "",
  minimumAssistLevel: "",
  safetyAlerts: [],
  dismissedSafetyAlertKeys: [],
  completed: false,
  completedDate: "",
  completedBy: "",
};

export function CHHAPocCard({ patientId, styles, COLORS }) {
  const [assessmentId, setAssessmentId] = useState(null);
  const [locked, setLocked] = useState(false);
  const [assignedAide, setAssignedAide] = useState("");
  const [fullFormData, setFullFormData] = useState(null);
  const [chhaPoc, setChhaPoc] = useState(DEFAULT_CHHA_POC);
  const [medications, setMedications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [customAlertDraft, setCustomAlertDraft] = useState("");

  const reload = useCallback(() => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    Promise.all([
      getRnicaAssessmentByPatient(patientId).catch(() => null),
      listMedications(patientId).catch(() => []),
    ])
      .then(([assessment, medList]) => {
        if (assessment?.assessmentId) {
          setAssessmentId(assessment.assessmentId);
          setLocked(!!assessment.locked);
          setFullFormData(assessment.formData || {});
          setAssignedAide(assessment.formData?.haAssignment?.assignedAide || "");
          setChhaPoc({ ...DEFAULT_CHHA_POC, ...(assessment.formData?.chhaPoc || {}) });
        } else {
          setError("No RN ICA assessment found for this patient yet — complete the RN ICA Admissions Order section first.");
        }
        setMedications(medList || []);
      })
      .catch((err) => setError(err.message || "Unable to load CHHA Plan of Care."))
      .finally(() => setLoading(false));
  }, [patientId]);

  useEffect(() => {
    reload();
  }, [reload]);

  const derivedCategories = useMemo(
    () => deriveChhaCareGuidance({ formData: fullFormData, medications, reportToRole: chhaPoc.reportToRole, minimumAssistLevel: chhaPoc.minimumAssistLevel }),
    [fullFormData, medications, chhaPoc.reportToRole, chhaPoc.minimumAssistLevel],
  );

  // System-derived guidance is computed live (never persisted as static text)
  // so changing "Report To", fall risk level, meds, etc. always updates the
  // wording immediately -- only *which keys were dismissed* is persisted.
  const dismissedKeys = useMemo(() => new Set(chhaPoc.dismissedSafetyAlertKeys || []), [chhaPoc.dismissedSafetyAlertKeys]);
  const visibleCategories = derivedCategories.filter((c) => !dismissedKeys.has(c.key));
  const customAlerts = (chhaPoc.safetyAlerts || []).filter((a) => a.custom);
  const todayWatchFor = [...new Set(visibleCategories.flatMap((c) => c.observe))];
  const chhaTaskMissingCounts = (chhaPoc.tasks || []).map((t) => {
    const items = t.items || [];
    const catalog = CHHA_TASK_OPTIONS.find((o) => o.value === t.task);
    const missingItemDetails = items.filter((i) => {
      const itemDef = catalog?.items.find((c) => c.code === i.code);
      return itemDef?.detail && !i.detail?.trim();
    }).length;
    const missingInstructions = items.length === 0 && !t.instructions?.trim() ? 1 : 0;
    const requiredAssistCode = chhaPoc.minimumAssistLevel === "2-person assist required" ? "TWO_PERSON"
      : chhaPoc.minimumAssistLevel === "Mechanical lift required — no manual lift" ? "MECHANICAL_LIFT" : null;
    const missingTransferSafety = t.task === "Transfer" && requiredAssistCode && !items.some((i) => i.code === requiredAssistCode) ? 1 : 0;
    return missingItemDetails + missingInstructions + missingTransferSafety;
  });
  const tasksMissingInstructions = chhaTaskMissingCounts.reduce((sum, n) => sum + n, 0)
    + (["2-person assist required", "Mechanical lift required — no manual lift"].includes(chhaPoc.minimumAssistLevel)
      && !(chhaPoc.tasks || []).some((t) => t.task === "Transfer") ? 1 : 0);

  const persist = (next) => {
    setChhaPoc(next);
    if (!assessmentId || !fullFormData) return;
    setSaving(true);
    setSaveMessage("");
    updateRnicaAssessment(assessmentId, { ...fullFormData, chhaPoc: next })
      .then(() => setSaveMessage("Saved"))
      .catch((err) => setError(err.message || "Unable to save CHHA Plan of Care."))
      .finally(() => setSaving(false));
  };

  const dismissCategory = (key) => {
    persist({ ...chhaPoc, dismissedSafetyAlertKeys: [...new Set([...(chhaPoc.dismissedSafetyAlertKeys || []), key])] });
  };

  const removeCustomAlert = (key) => {
    persist({ ...chhaPoc, safetyAlerts: (chhaPoc.safetyAlerts || []).filter((a) => a.key !== key) });
  };

  const addCustomAlert = () => {
    const text = customAlertDraft.trim();
    if (!text) return;
    persist({ ...chhaPoc, safetyAlerts: [...(chhaPoc.safetyAlerts || []), { key: `custom-${Date.now()}`, text, custom: true }] });
    setCustomAlertDraft("");
  };

  const toggleTask = (taskValue, checked) => {
    const existing = (chhaPoc.tasks || []).some((t) => t.task === taskValue);
    if (checked) {
      if (existing) return;
      persist({ ...chhaPoc, tasks: [...(chhaPoc.tasks || []), { task: taskValue, dependence: "", frequency: "", instructions: "", items: [] }] });
    } else {
      persist({ ...chhaPoc, tasks: (chhaPoc.tasks || []).filter((t) => t.task !== taskValue) });
    }
  };
  const updateTaskField = (taskValue, patch) => {
    const next = (chhaPoc.tasks || []).map((t) => (t.task === taskValue ? { ...t, ...patch } : t));
    persist({ ...chhaPoc, tasks: next });
  };
  const toggleTaskItem = (taskValue, itemCode, checked) => {
    const next = (chhaPoc.tasks || []).map((t) => {
      if (t.task !== taskValue) return t;
      const items = t.items || [];
      if (checked) {
        if (items.some((i) => i.code === itemCode)) return t;
        return { ...t, items: [...items, { code: itemCode, detail: "" }] };
      }
      return { ...t, items: items.filter((i) => i.code !== itemCode) };
    });
    persist({ ...chhaPoc, tasks: next });
  };
  const updateTaskItemDetail = (taskValue, itemCode, detailValue) => {
    const next = (chhaPoc.tasks || []).map((t) => {
      if (t.task !== taskValue) return t;
      return { ...t, items: (t.items || []).map((i) => (i.code === itemCode ? { ...i, detail: detailValue } : i)) };
    });
    persist({ ...chhaPoc, tasks: next });
  };

  if (loading) {
    return <div style={{ padding: 16, fontSize: 12.5, color: COLORS.gray }}>Loading CHHA Plan of Care…</div>;
  }

  return (
    <div style={{ padding: 12, display: "flex", flexDirection: "column", gap: 12 }}>
      {error && <div style={{ color: COLORS.error, fontSize: 12.5 }}>{error}</div>}

      <Card title="CHHA Plan of Care" cms="Home Health Aide">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginBottom: 8 }}>
          <div style={{ fontSize: 12.5, color: COLORS.gray }}>
            Assigned Home Aide: <strong style={{ color: COLORS.dark }}>{assignedAide || "Not yet assigned"}</strong>
          </div>
          {chhaPoc.completed && (
            <div style={{ fontSize: 12.5, color: COLORS.success, fontWeight: 700 }}>
              ✓ Completed{chhaPoc.completedDate ? ` — ${chhaPoc.completedDate}` : ""}{chhaPoc.completedBy ? ` by ${chhaPoc.completedBy}` : ""}
            </div>
          )}
        </div>
        {locked && (
          <div style={{ ...styles.infoBox, marginBottom: 8 }}>
            This patient's RN ICA is locked. CHHA Plan of Care edits after lock should go through the amendment process.
          </div>
        )}
      </Card>

      {/* ── Today's Key Observations — auto-generated summary card, always at the top ── */}
      {(visibleCategories.length > 0 || customAlerts.length > 0) && (
        <Card title="Today's Key Observations">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
            {visibleCategories.map((c) => (
              <span key={c.key} style={{
                fontSize: 11, fontWeight: 700, padding: "3px 9px", borderRadius: 999,
                background: "rgba(239,68,68,0.12)", color: COLORS.error, border: "1px solid rgba(239,68,68,0.3)",
              }}>
                {c.riskLabel}
              </span>
            ))}
          </div>
          <div style={{ fontSize: 11.5, fontWeight: 700, color: COLORS.dark, marginBottom: 4 }}>Today, watch for:</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, color: COLORS.dark, lineHeight: 1.7 }}>
            {todayWatchFor.map((item) => <li key={item}>{item}</li>)}
            {customAlerts.map((a) => <li key={a.key}>{a.text}</li>)}
          </ul>
          <div style={{ fontSize: 12, fontWeight: 700, color: COLORS.error, marginTop: 8 }}>
            Notify {chhaReportToLabel(chhaPoc.reportToRole)} immediately if observed.
          </div>
        </Card>
      )}

      {/* ── Safety Alerts & Report To — structured Observe / Safety / Escalate per risk, system-derived ── */}
      <Card title="Safety Alerts & Report To">
        <div style={{ ...styles.infoBox, marginBottom: 10 }}>
          Auto-generated from this patient's documented fall risk, oxygen use, swallowing risk, skin breakdown risk,
          and active medication classes — clinical terms and medication names/doses are never shown here, only what
          the HA should observe, do, and report. Dismiss a category if it doesn't apply; add anything else the RN
          wants flagged below.
        </div>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 10 }}>
          <div style={{ maxWidth: 260 }}>
            <FormSelect
              label="Report To"
              value={chhaPoc.reportToRole}
              onChange={(v) => persist({ ...chhaPoc, reportToRole: v })}
              options={CHHA_REPORT_TO_OPTIONS}
            />
          </div>
          <div style={{ maxWidth: 160 }}>
            <FormInput
              label="Patient Weight (lbs)"
              type="number"
              value={chhaPoc.patientWeightLbs}
              onChange={(v) => persist({ ...chhaPoc, patientWeightLbs: v })}
            />
          </div>
          <div style={{ maxWidth: 280 }}>
            <FormSelect
              label="Minimum Safe Assist Level for ANY Transfer (required)"
              value={chhaPoc.minimumAssistLevel}
              onChange={(v) => persist({ ...chhaPoc, minimumAssistLevel: v })}
              options={CHHA_MINIMUM_ASSIST_OPTIONS}
            />
          </div>
        </div>
        {["2-person assist required", "Mechanical lift required — no manual lift"].includes(chhaPoc.minimumAssistLevel)
          && !(chhaPoc.tasks || []).some((t) => t.task === "Transfer") && (
          <div style={{ fontSize: 11.5, fontWeight: 700, color: COLORS.error, background: COLORS.errorBg, borderRadius: 6, padding: "8px 10px", marginBottom: 10 }}>
            ⚠️ Check "Transfer" in Ordered Tasks below and select {chhaPoc.minimumAssistLevel === "Mechanical lift required — no manual lift" ? "Mechanical lift" : "2-person assist"} —
            a caregiver must never be relied on to manually move this patient at a lower assist level than ordered.
          </div>
        )}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {visibleCategories.map((c) => (
            <div key={c.key} style={{
              padding: "10px 12px", borderRadius: 8,
              background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.3)",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <span style={{ fontSize: 13 }}>⚠</span>
                <div style={{ flex: 1, fontSize: 13, fontWeight: 700, color: COLORS.dark }}>{c.riskLabel}</div>
                <button
                  type="button"
                  onClick={() => dismissCategory(c.key)}
                  title="Dismiss — does not apply to this patient"
                  style={{ border: "none", background: "transparent", color: COLORS.gray, cursor: "pointer", fontSize: 15, fontWeight: 700 }}
                >
                  ×
                </button>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10, fontSize: 12, color: COLORS.dark }}>
                <div>
                  <div style={{ fontWeight: 700, marginBottom: 2 }}>Observe</div>
                  <ul style={{ margin: 0, paddingLeft: 16, lineHeight: 1.6 }}>{c.observe.map((t) => <li key={t}>{t}</li>)}</ul>
                </div>
                <div>
                  <div style={{ fontWeight: 700, marginBottom: 2 }}>Safety</div>
                  <ul style={{ margin: 0, paddingLeft: 16, lineHeight: 1.6 }}>{c.safety.map((t) => <li key={t}>{t}</li>)}</ul>
                </div>
                <div>
                  <div style={{ fontWeight: 700, marginBottom: 2 }}>Escalate — call {chhaReportToLabel(chhaPoc.reportToRole)}</div>
                  <ul style={{ margin: 0, paddingLeft: 16, lineHeight: 1.6 }}>{c.escalate.map((t) => <li key={t}>{t}</li>)}</ul>
                </div>
              </div>
            </div>
          ))}
          {customAlerts.map((a) => (
            <div key={a.key} style={{
              display: "flex", gap: 10, alignItems: "flex-start", padding: "10px 12px", borderRadius: 8,
              background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.35)",
            }}>
              <span style={{ fontSize: 14 }}>⚠</span>
              <div style={{ flex: 1, fontSize: 12.5, color: COLORS.dark, lineHeight: 1.5 }}>{a.text}</div>
              <button
                type="button"
                onClick={() => removeCustomAlert(a.key)}
                title="Remove"
                style={{ border: "none", background: "transparent", color: COLORS.gray, cursor: "pointer", fontSize: 15, fontWeight: 700 }}
              >
                ×
              </button>
            </div>
          ))}
          {visibleCategories.length === 0 && customAlerts.length === 0 && (
            <div style={{ fontSize: 12, color: COLORS.gray }}>No active safety alerts for this patient right now.</div>
          )}
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          <FormInput
            label="Add custom safety alert"
            value={customAlertDraft}
            onChange={setCustomAlertDraft}
            placeholder={`e.g., Report to ${chhaReportToLabel(chhaPoc.reportToRole)} if patient refuses two consecutive visits`}
          />
          <button type="button" onClick={addCustomAlert} style={{ ...styles.btnSecondary, alignSelf: "end", height: 34 }}>
            + Add
          </button>
        </div>
      </Card>


      {/* ── Ordered tasks — checklist of the standard task categories; check the specific items this patient needs ── */}
      <Card title="Ordered Tasks">
        <div style={{ fontSize: 11.5, color: COLORS.gray, marginBottom: 8 }}>
          Check the category, then check only the specific items this patient actually needs. Fill in the specify-box for
          any item that needs one (diet, bed rails, which vitals, etc.) so the HA has exact instructions, not a
          judgment call.
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {CHHA_TASK_OPTIONS.map((opt) => {
            const row = (chhaPoc.tasks || []).find((t) => t.task === opt.value);
            const checked = !!row;
            const items = row?.items || [];
            const missingInstructions = checked && items.length === 0 && !row.instructions?.trim();
            const missingItemDetail = (code) => {
              const itemDef = opt.items.find((c) => c.code === code);
              const selected = items.find((i) => i.code === code);
              return checked && itemDef?.detail && selected && !selected.detail?.trim();
            };
            // Transfer/lift safety is a staff-injury risk -- if the RN set a
            // Minimum Safe Assist Level above, the matching Transfer item is
            // mandatory and lower (unsafe) assist levels are disabled, not
            // left as an option the HA or a rushed RN could pick by mistake.
            const isTransfer = opt.value === "Transfer";
            const transferRequiredCode = chhaPoc.minimumAssistLevel === "2-person assist required" ? "TWO_PERSON"
              : chhaPoc.minimumAssistLevel === "Mechanical lift required — no manual lift" ? "MECHANICAL_LIFT" : null;
            const transferRequiredMissing = isTransfer && checked && transferRequiredCode && !items.some((i) => i.code === transferRequiredCode);
            const anyMissing = missingInstructions || opt.items.some((i) => missingItemDetail(i.code)) || transferRequiredMissing;
            return (
              <div key={opt.value} style={{
                borderRadius: 8, border: `1px solid ${anyMissing ? COLORS.warning : COLORS.border}`, background: COLORS.bg, padding: "8px 10px",
              }}>
                <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, fontWeight: 700, color: COLORS.dark, cursor: "pointer" }}>
                  <input type="checkbox" checked={checked} onChange={(e) => toggleTask(opt.value, e.target.checked)} />
                  {opt.label}
                </label>
                <div style={{ fontSize: 11, color: COLORS.gray, marginTop: 2, marginLeft: 24 }}>{CHHA_TASK_GUIDANCE[opt.value]}</div>
                {checked && (
                  <div style={{ marginTop: 8, marginLeft: 24, display: "grid", gridTemplateColumns: "repeat(2, minmax(220px, 1fr))", gap: "6px 16px" }}>
                    {opt.items.map((itemDef) => {
                      const selected = items.find((i) => i.code === itemDef.code);
                      const itemChecked = !!selected;
                      const needsDetail = missingItemDetail(itemDef.code);
                      const isDisallowedAssist = isTransfer && transferRequiredCode === "MECHANICAL_LIFT" && (itemDef.code === "ONE_PERSON" || itemDef.code === "TWO_PERSON")
                        ? true
                        : isTransfer && transferRequiredCode === "TWO_PERSON" && itemDef.code === "ONE_PERSON";
                      return (
                        <div key={itemDef.code}>
                          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: isDisallowedAssist ? COLORS.gray : COLORS.dark, cursor: isDisallowedAssist ? "not-allowed" : "pointer" }}>
                            <input
                              type="checkbox"
                              checked={itemChecked}
                              disabled={isDisallowedAssist}
                              onChange={(e) => toggleTaskItem(opt.value, itemDef.code, e.target.checked)}
                            />
                            {itemDef.label}
                            {isDisallowedAssist && <span style={{ fontSize: 10.5, color: COLORS.error }}>— not safe at this patient's assist level</span>}
                          </label>
                          {itemChecked && itemDef.detail && (
                            <div style={{ marginLeft: 24, marginTop: 4, maxWidth: 420 }}>
                              <FormInput
                                label={`${itemDef.detailLabel} (required)`}
                                value={selected.detail}
                                onChange={(v) => updateTaskItemDetail(opt.value, itemDef.code, v)}
                              />
                              {needsDetail && <div style={{ fontSize: 10.5, color: COLORS.warning, marginTop: 2 }}>Required.</div>}
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {transferRequiredMissing && (
                      <div style={{ gridColumn: "1 / -1", fontSize: 11, fontWeight: 700, color: COLORS.error, background: COLORS.errorBg, borderRadius: 6, padding: "6px 8px" }}>
                        ⚠️ Required: this patient's Minimum Safe Assist Level is "{chhaPoc.minimumAssistLevel}" — check{" "}
                        {transferRequiredCode === "MECHANICAL_LIFT" ? "Mechanical lift" : "2-person assist"} above before finishing this plan.
                      </div>
                    )}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 8, marginTop: 4 }}>
                      <FormSelect label="Dependence Level" value={row.dependence} onChange={(v) => updateTaskField(opt.value, { dependence: v })} options={CHHA_DEPENDENCE_OPTIONS} />
                      <FormSelect label="Frequency" value={row.frequency} onChange={(v) => updateTaskField(opt.value, { frequency: v })} options={CHHA_TASK_FREQUENCY_OPTIONS} />
                      <div>
                        <FormInput
                          label={items.length === 0 ? "Instructions (required — no items checked above, so spell out exactly what to do)" : "Additional instructions (optional)"}
                          value={row.instructions}
                          onChange={(v) => updateTaskField(opt.value, { instructions: v })}
                          placeholder="e.g., Shower with chair, standby assist only, water lukewarm"
                        />
                        {missingInstructions && (
                          <div style={{ fontSize: 10.5, color: COLORS.warning, marginTop: 2 }}>Required.</div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        <div style={{ marginTop: 12 }}>
          <FormTextarea label="Diet / Nutrition Instructions" value={chhaPoc.dietInstructions} onChange={(v) => persist({ ...chhaPoc, dietInstructions: v })} rows={2} />
        </div>
        <div style={{ marginTop: 8 }}>
          <FormTextarea label="Additional Instructions" value={chhaPoc.additionalInstructions} onChange={(v) => persist({ ...chhaPoc, additionalInstructions: v })} rows={2} />
        </div>
        <div style={{ ...styles.infoBox, marginTop: 12 }}>
          If a task cannot be completed safely as written, or any symptom listed above occurs, stop and contact{" "}
          {chhaReportToLabel(chhaPoc.reportToRole)}.
        </div>
      </Card>

      {/* ── Completion — required before RN ICA can lock if an aide is assigned ── */}
      <Card title="Completion">
        {tasksMissingInstructions > 0 && (
          <div style={{ ...styles.infoBox, marginBottom: 8, borderColor: COLORS.warning }}>
            {tasksMissingInstructions} required field{tasksMissingInstructions > 1 ? "s are" : " is"} still blank in the
            Ordered Tasks above (a specify-box or Instructions). Complete those before marking this plan complete.
          </div>
        )}
        <FormCheckbox
          label="CHHA Plan of Care Completed"
          checked={chhaPoc.completed}
          disabled={tasksMissingInstructions > 0}
          onChange={(checked) => persist({
            ...chhaPoc,
            completed: checked,
            completedDate: checked ? (chhaPoc.completedDate || new Date().toISOString().slice(0, 10)) : "",
            completedBy: checked ? (chhaPoc.completedBy || getCurrentUser()?.full_name || getCurrentUser()?.name || "") : "",
          })}
        />
        {chhaPoc.completed && (
          <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
            <FormInput label="Completed Date" type="date" value={chhaPoc.completedDate} onChange={(v) => persist({ ...chhaPoc, completedDate: v })} />
            <FormInput label="Completed By" value={chhaPoc.completedBy} onChange={(v) => persist({ ...chhaPoc, completedBy: v })} />
          </div>
        )}
        {saving && <div style={{ fontSize: 11, color: COLORS.gray, marginTop: 6 }}>Saving…</div>}
        {!saving && saveMessage && <div style={{ fontSize: 11, color: COLORS.success, marginTop: 6 }}>{saveMessage}</div>}
      </Card>
    </div>
  );
}


// ---------------------------------------------------------------------------------
// CHHA Visit Note — per-visit documentation, distinct from the CHHA Plan of
// Care above (the POC is the RN's standing order; this is what the aide
// actually observed/did on ONE visit). Lives at PatientChart's 'chha-visits'
// destination and is backed by the real chha_visit_outcomes /
// chha_visit_task_results tables (visits.py's /visits/{id}/chha-outcome),
// NOT the RNICA form_data blob -- so it participates in the same automatic
// RN-follow-up-task creation as every other structured visit outcome
// (upsert_chha_outcome flags a pending RN task whenever redness/breakdown,
// a condition change, pain, or an explicit RN-notification flag is present).
//
// Same "never ask the aide to interpret clinical information" rule as the
// POC: every observation below is a plain-language, layman-observable
// checkbox (what was seen/heard), never a diagnosis. Any abnormal selection
// automatically raises "RN Notification Required" -- the aide never has to
// decide whether something is significant enough to report.
// ---------------------------------------------------------------------------------

const CHHA_SKIN_OPTIONS = [
  { value: "NORMAL", label: "Normal for patient", abnormal: false },
  { value: "PALE", label: "Pale", abnormal: true },
  { value: "BRUISING", label: "Increased bruising", abnormal: true },
  { value: "REDNESS", label: "Redness", abnormal: true },
  { value: "SWELLING", label: "Swelling", abnormal: true },
  { value: "BREAKDOWN", label: "Open area", abnormal: true },
];

const CHHA_RESPIRATION_OPTIONS = [
  { value: "COMFORTABLE", label: "Breathing comfortably", abnormal: false },
  { value: "INCREASED_DIFFICULTY", label: "Increased shortness of breath", abnormal: true },
  { value: "OXYGEN_IN_USE", label: "Oxygen in use", abnormal: false },
  { value: "COUGH", label: "Cough observed", abnormal: true },
];

const CHHA_NUTRITION_OPTIONS = [
  { value: "ATE_MEAL", label: "Ate meal", abnormal: false },
  { value: "FEEDING_ASSISTANCE", label: "Required feeding assistance", abnormal: false },
  { value: "COUGHING_WHILE_EATING", label: "Coughing while eating", abnormal: true },
  { value: "DIFFICULTY_SWALLOWING", label: "Difficulty swallowing", abnormal: true },
];

// Highest-severity-first, so a single skin_outcome column value can be
// derived from a multi-select checklist without losing signal.
const CHHA_SKIN_SEVERITY_ORDER = ["BREAKDOWN", "REDNESS", "SWELLING", "BRUISING", "PALE", "NORMAL"];

const CHHA_TOLERANCE_OPTIONS = [
  { value: "WELL_TOLERATED", label: "Patient tolerated care well" },
  { value: "FAIR", label: "Patient had some difficulty" },
  { value: "POOR", label: "Patient could not tolerate care as planned" },
];

// Per-visit supply/infection-control checklist -- stored as CHHAVisitTaskResult
// rows with section_code "SUPPLY" (no dedicated backend column needed).
const CHHA_SUPPLY_OPTIONS = [
  { code: "ADULT_DIAPERS", label: "Adult diapers" },
  { code: "BRIEFS", label: "Briefs" },
  { code: "UNDERPADS", label: "Chux / underpads" },
  { code: "DEODORIZERS", label: "Deodorizers" },
  { code: "DRESSINGS", label: "Dressings" },
  { code: "GLOVES", label: "Gloves" },
  { code: "HAND_SANITIZER", label: "Hand sanitizer" },
  { code: "WIPES", label: "Wipes" },
  { code: "BARRIER_CREAM", label: "Barrier cream" },
  { code: "CATHETER_SUPPLIES", label: "Catheter supplies" },
  { code: "WOUND_CARE_SUPPLIES", label: "Wound care supplies" },
  { code: "INFECTION_CONTROL_OBSERVED", label: "Infection control precautions observed" },
  { code: "DME_CHECKED", label: "DME checked and in safe working order" },
];

function chhaAbnormalSelected(selectedValues, optionList) {
  return selectedValues.some((v) => optionList.find((o) => o.value === v)?.abnormal);
}

function chhaDeriveSkinOutcome(selectedValues) {
  if (!selectedValues.length) return "NOT_ASSESSED";
  for (const level of CHHA_SKIN_SEVERITY_ORDER) {
    if (selectedValues.includes(level)) return level;
  }
  return "NOT_ASSESSED";
}

const DEFAULT_CHHA_VISIT_META = {
  correction: false,
  typeOfVisit: "",
  visitKind: "",
  visitKindSpecify: "",
  reasonForVisit: "",
  visitDate: "",
  timeIn: "",
  timeOut: "",
  duration: "",
  enteredBy: "",
  staffAssigned: "",
  discipline: "CHHA",
  careLevel: "",
};

// ════════════════════════════════════════════════════════════════
// Continuous Care (CC) Hourly Narrative — shared across RN, LVN, AIDE
// (CHHA), MSW, and Chaplain visits whenever the patient's care level is
// Continuous Care (see app.domain.forms.form_registry, get_cc_package).
// Renders live off note.visitMeta.careLevel so it appears/disappears the
// instant the visit's Care Level dropdown changes — no locking, no
// separate save step, since Care Level can change at any time.
// ════════════════════════════════════════════════════════════════

const DEFAULT_CC_ENTRY_DRAFT = {
  entry_date: "",
  entry_time: "",
  temperature: "",
  pulse: "",
  respirations: "",
  bp_systolic: "",
  bp_diastolic: "",
  o2_sat: "",
  pain_level: "",
  pain_location: "",
  pain_intervention: "",
  symptoms: "",
  care_provided: "",
  issue_identified: false,
  issue_narrative: "",
  poc_update_narrative: "",
  narrative: "",
};

export function ContinuousCareLogSection({ visitId, discipline, enteredBy, styles, COLORS, disabled }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState(DEFAULT_CC_ENTRY_DRAFT);

  const updateDraft = (key, value) => setDraft((p) => ({ ...p, [key]: value }));

  useEffect(() => {
    if (!visitId) {
      setEntries([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    listCcHourlyNarrativeEntries(visitId)
      .then((rows) => setEntries(Array.isArray(rows) ? rows : []))
      .catch((err) => setError(err.message || "Unable to load the continuous care log."))
      .finally(() => setLoading(false));
  }, [visitId]);

  const handleAddEntry = () => {
    if (!visitId || disabled) return;
    setSaving(true);
    setError("");
    createCcHourlyNarrativeEntry(visitId, { discipline, entered_by: enteredBy || "", ...draft })
      .then((created) => {
        setEntries((prev) => [...prev, created]);
        setDraft(DEFAULT_CC_ENTRY_DRAFT);
      })
      .catch((err) => setError(err.message || "Unable to save this continuous care log entry."))
      .finally(() => setSaving(false));
  };

  const handleRemoveEntry = (entryId) => {
    if (!visitId || disabled) return;
    deleteCcHourlyNarrativeEntry(visitId, entryId)
      .then(() => setEntries((prev) => prev.filter((e) => e.id !== entryId)))
      .catch((err) => setError(err.message || "Unable to remove this continuous care log entry."));
  };

  if (!visitId) {
    return (
      <Card title="Continuous Care Log" cms="Required hourly documentation while patient is on Continuous Care">
        <div style={{ ...styles.infoBox }}>Save this visit first to start the continuous care log.</div>
      </Card>
    );
  }

  return (
    <Card title="Continuous Care Log" cms="Required hourly documentation while patient is on Continuous Care">
      {error && <div style={{ color: COLORS.error, fontSize: 12.5, marginBottom: 8 }}>{error}</div>}
      {loading ? (
        <div style={{ fontSize: 12, color: COLORS.gray }}>Loading continuous care log…</div>
      ) : (
        <>
          {!disabled && (
            <div style={{ ...styles.fieldsGrid, marginBottom: 12 }}>
              <FormInput label="Date" type="date" value={draft.entry_date} onChange={(v) => updateDraft("entry_date", v)} />
              <FormInput label="Time" type="time" value={draft.entry_time} onChange={(v) => updateDraft("entry_time", v)} />
              <FormInput label="Temp" value={draft.temperature} onChange={(v) => updateDraft("temperature", v)} />
              <FormInput label="Pulse" value={draft.pulse} onChange={(v) => updateDraft("pulse", v)} />
              <FormInput label="Resp" value={draft.respirations} onChange={(v) => updateDraft("respirations", v)} />
              <FormInput label="BP Systolic" value={draft.bp_systolic} onChange={(v) => updateDraft("bp_systolic", v)} />
              <FormInput label="BP Diastolic" value={draft.bp_diastolic} onChange={(v) => updateDraft("bp_diastolic", v)} />
              <FormInput label="O2 Sat %" value={draft.o2_sat} onChange={(v) => updateDraft("o2_sat", v)} />
              <FormInput label="Pain Level" value={draft.pain_level} onChange={(v) => updateDraft("pain_level", v)} />
              <FormInput label="Pain Location" value={draft.pain_location} onChange={(v) => updateDraft("pain_location", v)} />
              <FormInput label="Pain Intervention" value={draft.pain_intervention} onChange={(v) => updateDraft("pain_intervention", v)} />
              <FormInput label="Symptoms" value={draft.symptoms} onChange={(v) => updateDraft("symptoms", v)} />
              <FormInput label="Care Provided" value={draft.care_provided} onChange={(v) => updateDraft("care_provided", v)} />
              <label style={styles.formGroup}>
                <span style={styles.label}>Issue Identified</span>
                <input
                  type="checkbox"
                  checked={draft.issue_identified}
                  onChange={(e) => updateDraft("issue_identified", e.target.checked)}
                  style={{ width: 18, height: 18 }}
                />
              </label>
              {draft.issue_identified && (
                <FormInput label="Issue Narrative" value={draft.issue_narrative} onChange={(v) => updateDraft("issue_narrative", v)} />
              )}
              <FormInput label="POC Update" value={draft.poc_update_narrative} onChange={(v) => updateDraft("poc_update_narrative", v)} />
              <FormInput label="Narrative" value={draft.narrative} onChange={(v) => updateDraft("narrative", v)} />
            </div>
          )}
          {!disabled && (
            <button
              type="button"
              onClick={handleAddEntry}
              disabled={saving}
              style={{ ...styles.btnPrimary, opacity: saving ? 0.55 : 1, cursor: saving ? "not-allowed" : "pointer", marginBottom: 14 }}
            >
              {saving ? "Adding…" : "Add Hourly Entry"}
            </button>
          )}

          {entries.length === 0 ? (
            <div style={{ fontSize: 12, color: COLORS.gray }}>No continuous care log entries recorded yet.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {entries.map((entry) => (
                <div key={entry.id} style={{ border: `1px solid ${COLORS.border || "#e2e8f0"}`, borderRadius: 8, padding: 10, fontSize: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                    <strong>
                      {entry.entry_date || "—"} {entry.entry_time || ""} · {entry.discipline}
                      {entry.entered_by ? ` · ${entry.entered_by}` : ""}
                    </strong>
                    {!disabled && (
                      <button
                        type="button"
                        onClick={() => handleRemoveEntry(entry.id)}
                        style={{ border: "none", background: "transparent", color: COLORS.error, cursor: "pointer", fontSize: 11.5, textDecoration: "underline" }}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  <div style={{ marginTop: 4, color: COLORS.dark }}>
                    {(entry.temperature || entry.pulse || entry.respirations || entry.bp_systolic || entry.o2_sat) && (
                      <div>
                        Vitals: T {entry.temperature || "—"} · P {entry.pulse || "—"} · R {entry.respirations || "—"} · BP{" "}
                        {entry.bp_systolic || "—"}/{entry.bp_diastolic || "—"} · O2 {entry.o2_sat || "—"}%
                      </div>
                    )}
                    {(entry.pain_level || entry.pain_location || entry.pain_intervention) && (
                      <div>
                        Pain: {entry.pain_level || "—"} {entry.pain_location ? `@ ${entry.pain_location}` : ""}{" "}
                        {entry.pain_intervention ? `— ${entry.pain_intervention}` : ""}
                      </div>
                    )}
                    {entry.symptoms && <div>Symptoms: {entry.symptoms}</div>}
                    {entry.care_provided && <div>Care provided: {entry.care_provided}</div>}
                    {entry.issue_identified && <div style={{ color: COLORS.error }}>Issue: {entry.issue_narrative || "(no detail provided)"}</div>}
                    {entry.poc_update_narrative && <div>POC update: {entry.poc_update_narrative}</div>}
                    {entry.narrative && <div>Narrative: {entry.narrative}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </Card>
  );
}

const DEFAULT_CHHA_VISIT_NOTE = {
  taskResults: {}, // task value -> { state: "completed"|"refused"|"notDone", note: string }
  skin: [],
  respiration: [],
  nutrition: [],
  supplies: [],
  painOrChangeObserved: false,
  painNote: "",
  toleranceToCare: "WELL_TOLERATED",
  exceptionNarrative: "",
  caregiverInstructionProvided: false,
  caregiverUnderstandingConfirmed: false,
  rnNotified: false,
  rnNotifiedName: "",
  visitMeta: DEFAULT_CHHA_VISIT_META,
};

export function CHHAVisitNoteCard({ patientId, styles, COLORS }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [fullFormData, setFullFormData] = useState(null);
  const [medications, setMedications] = useState([]);
  const [orderedTasks, setOrderedTasks] = useState([]);
  const [reportToRole, setReportToRole] = useState("RN");
  const [minimumAssistLevel, setMinimumAssistLevel] = useState("");
  const [visits, setVisits] = useState([]);
  const [selectedVisitId, setSelectedVisitId] = useState("");
  const [selectedVisitMeta, setSelectedVisitMeta] = useState(null);
  const [note, setNote] = useState(DEFAULT_CHHA_VISIT_NOTE);
  const [showCreateVisit, setShowCreateVisit] = useState(false);
  const [newVisitStaffOptions, setNewVisitStaffOptions] = useState([]);
  const [newVisitStaffId, setNewVisitStaffId] = useState("");
  const [newVisitDate, setNewVisitDate] = useState(new Date().toISOString().slice(0, 10));
  const [newVisitCareLevel, setNewVisitCareLevel] = useState("RC");
  const [creatingVisit, setCreatingVisit] = useState(false);
  const [createVisitError, setCreateVisitError] = useState("");

  const reloadPatientContext = useCallback(() => {
    setLoading(true);
    setError("");
    Promise.all([
      getRnicaAssessmentByPatient(patientId).catch(() => null),
      listMedications(patientId).catch(() => []),
      listAideVisitsForPatient(patientId).catch(() => []),
    ])
      .then(([assessment, meds, aideVisits]) => {
        const formData = assessment?.formData || null;
        setFullFormData(formData);
        setMedications(Array.isArray(meds) ? meds : []);
        setOrderedTasks(formData?.chhaPoc?.tasks || []);
        setReportToRole(formData?.chhaPoc?.reportToRole || "RN");
        setMinimumAssistLevel(formData?.chhaPoc?.minimumAssistLevel || "");
        setVisits(aideVisits || []);
        const preferred = (aideVisits || []).find((v) => !v.has_outcome) || (aideVisits || [])[0] || null;
        setSelectedVisitId(preferred?.visit_id || "");
        setSelectedVisitMeta(preferred || null);
      })
      .catch((err) => setError(err.message || "Unable to load this patient's CHHA visit context."))
      .finally(() => setLoading(false));
  }, [patientId]);

  useEffect(() => {
    reloadPatientContext();
  }, [reloadPatientContext]);

  // "HA CC Visit" staff+date picker -- lets the CHHA section create its own
  // visit (RN/LVN/SC/MSW already get this via Add New Visit) instead of
  // requiring a visit to already exist via scheduling before a note can be
  // attached. Care Level defaults to Continuous Care since that's the
  // primary reason this flow was requested (hourly CC documentation), but
  // Routine is also offered since CHHA still has routine visits too.
  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    listAssignableStaff(patientId, "CHHA")
      .then((rows) => {
        if (cancelled) return;
        setNewVisitStaffOptions(rows);
        const currentUser = getCurrentUser();
        const self = rows.find((row) => row.user_id === currentUser?.id);
        setNewVisitStaffId(self ? self.user_id : rows[0]?.user_id || currentUser?.id || "");
      })
      .catch(() => { if (!cancelled) setNewVisitStaffOptions([]); });
    return () => { cancelled = true; };
  }, [patientId]);

  const newVisitStaffChoices = useMemo(() => {
    const list = newVisitStaffOptions.map((row) => ({ value: row.user_id, label: `${row.name}${row.is_primary ? " (Primary)" : ""}` }));
    const currentUser = getCurrentUser();
    if (currentUser?.id && !list.some((item) => item.value === currentUser.id)) {
      list.unshift({ value: currentUser.id, label: `${currentUser.full_name || currentUser.name || "Me"} (Myself)` });
    }
    return list;
  }, [newVisitStaffOptions]);

  const handleCreateAideVisit = () => {
    setCreatingVisit(true);
    setCreateVisitError("");
    const currentUser = getCurrentUser();
    const staffLabel = newVisitStaffChoices.find((item) => item.value === newVisitStaffId)?.label || currentUser?.full_name || currentUser?.name || "";
    createVisitNote({
      patient_id: patientId,
      visit_type: "CHHA",
      level_of_care: newVisitCareLevel || null,
      visit_schedule_type: "SCHEDULED",
      assigned_staff_id: newVisitStaffId || null,
      visit_datetime: newVisitDate ? `${newVisitDate}T00:00:00` : null,
      clinical_note: {
        entered_by: currentUser?.full_name || currentUser?.name || "",
        staff_assigned: staffLabel,
        visit_date: newVisitDate,
      },
    })
      .then((response) => {
        setShowCreateVisit(false);
        reloadPatientContext();
        setSelectedVisitId(response.visit_id);
      })
      .catch((err) => setCreateVisitError(err.message || "Unable to create this CHHA visit."))
      .finally(() => setCreatingVisit(false));
  };

  useEffect(() => {
    if (!selectedVisitId) {
      setNote(DEFAULT_CHHA_VISIT_NOTE);
      return;
    }
    setSaveMessage("");
    const currentUser = getCurrentUser();
    const fallbackVisitMeta = {
      ...DEFAULT_CHHA_VISIT_META,
      visitDate: selectedVisitMeta?.visit_datetime
        ? new Date(selectedVisitMeta.visit_datetime).toISOString().slice(0, 10)
        : "",
      enteredBy: currentUser?.full_name || currentUser?.name || "",
      staffAssigned: currentUser?.full_name || currentUser?.name || "",
      discipline: "CHHA",
    };
    getChhaVisitOutcome(selectedVisitId)
      .then((existing) => {
        if (!existing) {
          setNote({ ...DEFAULT_CHHA_VISIT_NOTE, visitMeta: fallbackVisitMeta });
          return;
        }
        const taskResults = {};
        const skin = [];
        const respiration = [];
        const nutrition = [];
        const supplies = [];
        (existing.task_results || []).forEach((t) => {
          if (t.section_code === "TASK") {
            taskResults[t.task_code] = {
              state: t.refused ? "refused" : t.not_done ? "notDone" : t.completed ? "completed" : "",
              note: t.result_note || "",
              checklist: [],
              assistedBy: "",
              noteIsAuto: false,
            };
          } else if (t.section_code === "OBSERVATION" && t.task_code === "SKIN" && t.observation_code) {
            skin.push(t.observation_code);
          } else if (t.section_code === "OBSERVATION" && t.task_code === "RESPIRATION" && t.observation_code) {
            respiration.push(t.observation_code);
          } else if (t.section_code === "OBSERVATION" && t.task_code === "NUTRITION" && t.observation_code) {
            nutrition.push(t.observation_code);
          } else if (t.section_code === "SUPPLY") {
            supplies.push(t.task_code);
          }
        });
        setNote({
          taskResults,
          skin,
          respiration,
          nutrition,
          supplies,
          painOrChangeObserved: !!existing.pain_or_change_observed,
          painNote: existing.exception_narrative && existing.pain_or_change_observed ? existing.exception_narrative : "",
          toleranceToCare: existing.tolerance_to_care || "WELL_TOLERATED",
          exceptionNarrative: existing.exception_narrative || "",
          caregiverInstructionProvided: !!existing.caregiver_instruction_provided,
          caregiverUnderstandingConfirmed: !!existing.caregiver_understanding_confirmed,
          rnNotified: !!existing.rn_notified,
          rnNotifiedName: existing.rn_notified_name || "",
          visitMeta: {
            correction: !!existing.correction,
            typeOfVisit: existing.type_of_visit || "",
            visitKind: existing.visit_kind || "",
            visitKindSpecify: existing.visit_kind_specify || "",
            reasonForVisit: existing.reason_for_visit || "",
            visitDate: existing.visit_date || fallbackVisitMeta.visitDate,
            timeIn: existing.time_in || "",
            timeOut: existing.time_out || "",
            duration: existing.duration || "",
            enteredBy: existing.entered_by || fallbackVisitMeta.enteredBy,
            staffAssigned: existing.staff_assigned || fallbackVisitMeta.staffAssigned,
            discipline: "CHHA",
            careLevel: existing.care_level || "",
          },
        });
      })
      .catch((err) => setError(err.message || "Unable to load this visit's CHHA note."));
  }, [selectedVisitId, selectedVisitMeta]);

  const derivedCategories = useMemo(
    () => deriveChhaCareGuidance({ formData: fullFormData, medications, reportToRole, minimumAssistLevel }),
    [fullFormData, medications, reportToRole, minimumAssistLevel],
  );
  const todayWatchFor = useMemo(() => [...new Set(derivedCategories.flatMap((c) => c.observe))], [derivedCategories]);

  // Flatten each ordered task category down to the specific items the RN
  // actually checked in the POC -- the aide documents completion per item
  // (e.g., "Foley catheter care", "Bed rails up"), not per broad category,
  // matching how the standing order itself is now written. Carries the
  // dependence level, frequency, scope-of-practice guidance, and any
  // category-level instructions along with each item so the aide never has
  // to leave the Visit Note and go back to the POC screen to see the order.
  const orderedTaskItems = useMemo(() => orderedTasks.flatMap((t) => {
    const catalog = CHHA_TASK_OPTIONS.find((o) => o.value === t.task);
    const categoryLabel = catalog?.label || t.task;
    const guidance = CHHA_TASK_GUIDANCE[t.task] || "";
    const shared = { category: t.task, categoryLabel, guidance, dependence: t.dependence || "", frequency: t.frequency || "", categoryInstructions: t.instructions || "" };
    if ((t.items || []).length > 0) {
      return t.items.map((i) => {
        const itemDef = catalog?.items?.find((c) => c.code === i.code);
        return { key: `${t.task}::${i.code}`, itemCode: i.code, ...shared, label: itemDef?.label || i.code, detail: i.detail };
      });
    }
    // Backward-compatible fallback for a category ordered with free-text
    // Instructions only (no granular items checked).
    return [{ key: t.task, itemCode: null, ...shared, label: categoryLabel, detail: "" }];
  }), [orderedTasks]);

  // One card per category (Ambulation, Transfer, Feeding, ...) instead of
  // one card per item -- the category header, shared dependence/frequency,
  // instructions, and guidance are shown ONCE, and every item ordered under
  // that category is listed underneath it as its own row. This is what
  // keeps a patient with 5 Ambulation items from producing 5 near-identical
  // cards that all repeat "AMBULATION" at the top.
  const groupedTaskCategories = useMemo(() => {
    const byCategory = new Map();
    for (const item of orderedTaskItems) {
      if (!byCategory.has(item.category)) {
        byCategory.set(item.category, {
          category: item.category,
          categoryLabel: item.categoryLabel,
          guidance: item.guidance,
          dependence: item.dependence,
          frequency: item.frequency,
          categoryInstructions: item.categoryInstructions,
          items: [],
        });
      }
      byCategory.get(item.category).items.push(item);
    }
    // Sort largest-to-smallest so the grid's left/right pair on each row is
    // as close in item count as possible -- adjacent categories in a sorted
    // list are always the closest match available, which keeps left/right
    // box heights from looking randomly mismatched row to row.
    return [...byCategory.values()].sort((a, b) => b.items.length - a.items.length);
  }, [orderedTaskItems]);

  // Visit-time facts are captured as checklists (CHHA_VISIT_FACT_OPTIONS),
  // not free narrative -- narrative alone is unreliable (vague, inconsistent,
  // easy to write nothing useful). The checklist is the required, auditable
  // record. The narrative box is kept (some RNs/aides want to add color, and
  // exception detail still needs free text), but it is auto-drafted from
  // whatever the aide checks so it is never blank/generic -- the checklist
  // does the heavy lifting and the aide only edits/adds to it if needed.
  const visitFactCatalog = (t) => CHHA_VISIT_FACT_OPTIONS[t.category] || null;

  const draftNarrativeFromChecklist = (t, checklist) => {
    const catalog = visitFactCatalog(t) || [];
    const labels = (checklist || []).map((code) => catalog.find((o) => o.code === code)?.label).filter(Boolean);
    return labels.join("; ");
  };

  const setTaskResult = (itemKey, patch) => {
    setNote((prev) => ({
      ...prev,
      taskResults: { ...prev.taskResults, [itemKey]: { ...(prev.taskResults[itemKey] || { state: "", note: "", checklist: [], assistedBy: "", noteIsAuto: true }), ...patch } },
    }));
  };

  // Editing the narrative by hand "detaches" it from the checklist so later
  // checklist changes don't clobber what the user typed; a small control lets
  // them re-sync it to the checklist wording if they want to start over.
  const setTaskNarrative = (itemKey, value) => {
    setTaskResult(itemKey, { note: value, noteIsAuto: false });
  };

  const resyncTaskNarrative = (t) => {
    const result = note.taskResults[t.key] || {};
    setTaskResult(t.key, { note: draftNarrativeFromChecklist(t, result.checklist), noteIsAuto: true });
  };

  const toggleTaskChecklistItem = (t, code, checked) => {
    setNote((prev) => {
      const current = prev.taskResults[t.key] || { state: "", note: "", checklist: [], assistedBy: "", noteIsAuto: true };
      const checklist = checked ? [...new Set([...(current.checklist || []), code])] : (current.checklist || []).filter((c) => c !== code);
      const noteIsAuto = current.noteIsAuto !== false; // only auto-regenerate if the user hasn't manually diverged
      const nextNote = noteIsAuto ? draftNarrativeFromChecklist(t, checklist) : current.note;
      return {
        ...prev,
        taskResults: { ...prev.taskResults, [t.key]: { ...current, checklist, note: nextNote, noteIsAuto } },
      };
    });
  };

  const skinAbnormal = chhaAbnormalSelected(note.skin, CHHA_SKIN_OPTIONS);
  const respirationAbnormal = chhaAbnormalSelected(note.respiration, CHHA_RESPIRATION_OPTIONS);
  const nutritionAbnormal = chhaAbnormalSelected(note.nutrition, CHHA_NUTRITION_OPTIONS);
  const anyTaskRefusedOrNotDone = Object.values(note.taskResults).some((t) => t.state === "refused" || t.state === "notDone");
  const conditionDuringVisit = (respirationAbnormal || nutritionAbnormal) ? "CHANGE_OBSERVED" : "STABLE";
  const skinOutcome = chhaDeriveSkinOutcome(note.skin);

  const rnNotificationReasons = [
    skinAbnormal && "Abnormal skin finding",
    respirationAbnormal && "Abnormal breathing finding",
    nutritionAbnormal && "Coughing/swallowing difficulty during a meal",
    note.painOrChangeObserved && "Pain or condition change observed",
    anyTaskRefusedOrNotDone && "An ordered task was refused or not completed",
  ].filter(Boolean);
  const rnNotificationRequired = rnNotificationReasons.length > 0;

  const visitLocked = selectedVisitMeta?.status === "FINALIZED";

  const missingTaskNotes = orderedTaskItems.filter((t) => {
    const result = note.taskResults[t.key];
    const state = result?.state;
    if (state === "refused" || state === "notDone") return !result?.note?.trim();
    if (state === "completed") {
      const catalog = visitFactCatalog(t);
      const needsChecklist = !!catalog && (result?.checklist || []).length === 0;
      const needsAssistedBy = (result?.checklist || []).some((c) => ASSIST_NAME_TRIGGER_CODES.includes(c)) && !result?.assistedBy?.trim();
      return needsChecklist || needsAssistedBy;
    }
    return false;
  }).length;
  const missingRnNotifiedName = note.rnNotified && !note.rnNotifiedName.trim();
  const canSubmit = !visitLocked && !!selectedVisitId && missingTaskNotes === 0 && !missingRnNotifiedName;

  const updateVisitMeta = (key, value) => {
    setNote((p) => ({ ...p, visitMeta: { ...p.visitMeta, [key]: value } }));
  };

  const handleSubmit = () => {
    if (!selectedVisitId || !canSubmit) return;
    setSaving(true);
    setSaveMessage("");
    setError("");

    // Always lead with the checklist facts (the reliable, structured part of
    // the record); "Assisted by" and any hand-typed narrative are appended
    // as supplementary detail rather than replacing the checklist.
    const buildResultNote = (t, result) => {
      const catalog = visitFactCatalog(t) || [];
      const checklistLabels = (result.checklist || []).map((c) => catalog.find((o) => o.code === c)?.label).filter(Boolean);
      const parts = [];
      if (checklistLabels.length) parts.push(checklistLabels.join("; "));
      if (result.assistedBy?.trim()) parts.push(`Assisted by: ${result.assistedBy.trim()}`);
      if (result.note?.trim() && (result.noteIsAuto === false || checklistLabels.length === 0)) parts.push(result.note.trim());
      return parts.join(" | ") || null;
    };

    const taskResultRows = [
      ...orderedTaskItems.map((t) => {
        const result = note.taskResults[t.key] || { state: "", note: "" };
        return {
          section_code: "TASK",
          task_code: t.key,
          was_assigned: true,
          completed: result.state === "completed",
          refused: result.state === "refused",
          not_done: result.state === "notDone",
          observation_code: null,
          result_note: buildResultNote(t, result),
        };
      }),
      ...note.skin.map((v) => ({
        section_code: "OBSERVATION", task_code: "SKIN", was_assigned: true, completed: true, refused: false, not_done: false,
        observation_code: v, result_note: null,
      })),
      ...note.respiration.map((v) => ({
        section_code: "OBSERVATION", task_code: "RESPIRATION", was_assigned: true, completed: true, refused: false, not_done: false,
        observation_code: v, result_note: null,
      })),
      ...note.nutrition.map((v) => ({
        section_code: "OBSERVATION", task_code: "NUTRITION", was_assigned: true, completed: true, refused: false, not_done: false,
        observation_code: v, result_note: null,
      })),
      ...note.supplies.map((v) => ({
        section_code: "SUPPLY", task_code: v, was_assigned: true, completed: true, refused: false, not_done: false,
        observation_code: null, result_note: null,
      })),
    ];

    upsertChhaVisitOutcome(selectedVisitId, {
      tolerance_to_care: note.toleranceToCare,
      condition_during_visit: conditionDuringVisit,
      skin_outcome: skinOutcome,
      pain_or_change_observed: note.painOrChangeObserved,
      rn_notification_required: rnNotificationRequired,
      rn_notified: note.rnNotified,
      rn_notified_name: note.rnNotified ? note.rnNotifiedName.trim() : null,
      caregiver_instruction_provided: note.caregiverInstructionProvided,
      caregiver_understanding_confirmed: note.caregiverUnderstandingConfirmed,
      exception_narrative: [note.painNote?.trim(), note.exceptionNarrative?.trim()].filter(Boolean).join(" — ") || null,
      task_results: taskResultRows,
      correction: note.visitMeta.correction,
      type_of_visit: note.visitMeta.typeOfVisit || null,
      visit_kind: note.visitMeta.visitKind || null,
      visit_kind_specify: note.visitMeta.visitKind === "Other" ? (note.visitMeta.visitKindSpecify?.trim() || null) : null,
      reason_for_visit: note.visitMeta.reasonForVisit || null,
      visit_date: note.visitMeta.visitDate || null,
      time_in: note.visitMeta.timeIn || null,
      time_out: note.visitMeta.timeOut || null,
      duration: note.visitMeta.duration || null,
      entered_by: note.visitMeta.enteredBy?.trim() || null,
      staff_assigned: note.visitMeta.staffAssigned?.trim() || null,
      care_level: note.visitMeta.careLevel || null,
    })
      .then(() => {
        setSaveMessage("Visit note saved");
        setVisits((prev) => prev.map((v) => (v.visit_id === selectedVisitId ? { ...v, has_outcome: true, rn_notification_required: rnNotificationRequired } : v)));
      })
      .catch((err) => setError(err.message || "Unable to save this CHHA visit note."))
      .finally(() => setSaving(false));
  };

  if (loading) {
    return <div style={{ padding: 16, fontSize: 12.5, color: COLORS.gray }}>Loading CHHA Visit Note…</div>;
  }

  return (
    <div style={{ padding: 12, display: "flex", flexDirection: "column", gap: 12 }}>
      {error && <div style={{ color: COLORS.error, fontSize: 12.5 }}>{error}</div>}

      <Card title="CHHA Visit Note" cms="Home Health Aide">
        {visits.length === 0 ? (
          <div style={{ ...styles.infoBox }}>No Home Health Aide visits are on record for this patient yet.</div>
        ) : (
          <div style={{ maxWidth: 360 }}>
            <FormSelect
              label="Visit"
              value={selectedVisitId}
              onChange={(v) => {
                setSelectedVisitId(v);
                setSelectedVisitMeta(visits.find((x) => x.visit_id === v) || null);
              }}
              options={visits.map((v) => ({
                value: v.visit_id,
                label: `${v.visit_datetime ? new Date(v.visit_datetime).toLocaleString() : "Undated visit"} — ${v.status}${v.has_outcome ? " ✓ documented" : ""}`,
              }))}
            />
          </div>
        )}
        <button
          type="button"
          onClick={() => setShowCreateVisit((prev) => !prev)}
          style={{ ...styles.btnSecondary, marginTop: 8 }}
        >
          {showCreateVisit ? "Cancel" : "+ New CHHA Visit"}
        </button>
        {showCreateVisit && (
          <div style={{ ...styles.infoBox, marginTop: 8, maxWidth: 480 }}>
            {createVisitError && <div style={{ color: COLORS.error, fontSize: 12.5, marginBottom: 8 }}>{createVisitError}</div>}
            <div style={styles.fieldsGrid}>
              <FormSelect
                label="Staff Assigned"
                value={newVisitStaffId}
                onChange={setNewVisitStaffId}
                options={newVisitStaffChoices}
                placeholder="— Select HA Staff —"
              />
              <FormInput label="Visit Date" type="date" value={newVisitDate} onChange={setNewVisitDate} />
              <FormSelect
                label="Care Level"
                value={newVisitCareLevel}
                onChange={setNewVisitCareLevel}
                options={[
                  { value: "RC", label: "Routine Home Care" },
                  { value: "CC", label: "Continuous Care (Crisis)" },
                ]}
              />
            </div>
            <button
              type="button"
              onClick={handleCreateAideVisit}
              disabled={creatingVisit || !newVisitStaffId}
              style={{ ...styles.btnPrimary, opacity: creatingVisit || !newVisitStaffId ? 0.65 : 1, marginTop: 8 }}
            >
              {creatingVisit ? "Creating…" : "Create Visit"}
            </button>
          </div>
        )}
        {visitLocked && (
          <div style={{ ...styles.infoBox, marginTop: 8 }}>
            This visit is finalized. It is read-only — corrections go through the amendment process.
          </div>
        )}
      </Card>

      <Card title="Visit Details" cms="Logistics & payroll tracking for this visit">
          <div style={styles.fieldsGrid}>
            <label style={styles.formGroup}>
              <span style={styles.label}>Correction</span>
              <input
                type="checkbox"
                checked={note.visitMeta.correction}
                disabled={visitLocked}
                onChange={(e) => updateVisitMeta("correction", e.target.checked)}
                style={{ width: 18, height: 18 }}
              />
            </label>
            <FormSelect
              label="Type of Visit"
              value={note.visitMeta.typeOfVisit}
              onChange={(v) => updateVisitMeta("typeOfVisit", v)}
              options={["In-Person", "Telephone", "Video"]}
              disabled={visitLocked}
            />
            <FormSelect
              label="Visit"
              value={note.visitMeta.visitKind}
              onChange={(v) => updateVisitMeta("visitKind", v)}
              options={["Scheduled", "Unscheduled", "Other"]}
              disabled={visitLocked}
            />
            {note.visitMeta.visitKind === "Other" && (
              <FormInput
                label="Specify"
                value={note.visitMeta.visitKindSpecify}
                onChange={(v) => updateVisitMeta("visitKindSpecify", v)}
                disabled={visitLocked}
              />
            )}
            <FormSelect
              label="Reason for Visit"
              value={note.visitMeta.reasonForVisit}
              onChange={(v) => updateVisitMeta("reasonForVisit", v)}
              options={CHHA_REASON_FOR_VISIT_OPTIONS}
              disabled={visitLocked}
            />
            <FormInput
              label="Visit Date"
              type="date"
              value={note.visitMeta.visitDate}
              onChange={(v) => updateVisitMeta("visitDate", v)}
              disabled={visitLocked}
            />
            <FormInput label="Time In" type="time" value={note.visitMeta.timeIn} onChange={(v) => updateVisitMeta("timeIn", v)} disabled={visitLocked} />
            <FormInput label="Time Out" type="time" value={note.visitMeta.timeOut} onChange={(v) => updateVisitMeta("timeOut", v)} disabled={visitLocked} />
            <FormInput label="Duration (h:m)" value={note.visitMeta.duration} onChange={(v) => updateVisitMeta("duration", v)} placeholder="1h 15m" disabled={visitLocked} />
            <FormInput label="Entered By" value={note.visitMeta.enteredBy} onChange={(v) => updateVisitMeta("enteredBy", v)} disabled={visitLocked} />
            <FormInput label="Staff Assigned" value={note.visitMeta.staffAssigned} onChange={(v) => updateVisitMeta("staffAssigned", v)} disabled={visitLocked} />
            <FormInput label="Discipline" value="CHHA" disabled />
            <FormSelect
              label="Care Level"
              value={note.visitMeta.careLevel}
              onChange={(v) => updateVisitMeta("careLevel", v)}
              options={CARE_LEVEL_OPTIONS}
              disabled={visitLocked}
            />
          </div>
      </Card>

      {note.visitMeta.careLevel === "Continuous Care" && (
        <ContinuousCareLogSection
          visitId={selectedVisitId}
          discipline="AIDE"
          enteredBy={note.visitMeta.enteredBy}
          styles={styles}
          COLORS={COLORS}
          disabled={visitLocked}
        />
      )}

      {/* ── Today's Key Observations — same auto-generated summary as the POC, repeated at the top of every visit ── */}
      {(todayWatchFor.length > 0) && (
        <Card title="Today's Key Observations">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
            {derivedCategories.map((c) => (
              <span key={c.key} style={{
                fontSize: 11, fontWeight: 700, padding: "3px 9px", borderRadius: 999,
                background: "rgba(239,68,68,0.12)", color: COLORS.error, border: "1px solid rgba(239,68,68,0.3)",
              }}>
                {c.riskLabel}
              </span>
            ))}
          </div>
          <div style={{ fontSize: 11.5, fontWeight: 700, color: COLORS.dark, marginBottom: 4 }}>Today, watch for:</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, color: COLORS.dark, lineHeight: 1.7 }}>
            {todayWatchFor.map((item) => <li key={item}>{item}</li>)}
          </ul>
          <div style={{ fontSize: 12, fontWeight: 700, color: COLORS.error, marginTop: 8 }}>
            Notify {chhaReportToLabel(reportToRole)} immediately if observed.
          </div>
        </Card>
      )}

      {/* ── Ordered tasks — what actually happened at THIS visit, one row per ordered item ── */}
      <Card title="Ordered Tasks — Today's Visit">
        {orderedTaskItems.length === 0 ? (
          <div style={{ fontSize: 12, color: COLORS.gray }}>No tasks are ordered in this patient's CHHA Plan of Care yet.</div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10, alignItems: "start" }}>
            {groupedTaskCategories.map((cat) => {
              const anyCategoryMissing = cat.items.some((t) => {
                const result = note.taskResults[t.key];
                const state = result?.state;
                if (state === "refused" || state === "notDone") return !result?.note?.trim();
                if (state === "completed") {
                  const catalog = visitFactCatalog(t);
                  const needsChecklist = !!catalog && (result?.checklist || []).length === 0;
                  const needsAssistedBy = (result?.checklist || []).some((c) => ASSIST_NAME_TRIGGER_CODES.includes(c)) && !result?.assistedBy?.trim();
                  return needsChecklist || needsAssistedBy;
                }
                return false;
              });
              return (
                <div key={cat.category} style={{
                  borderRadius: 8, border: `1px solid ${anyCategoryMissing ? COLORS.warning : COLORS.border}`, background: COLORS.bg, padding: "10px 12px",
                }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.gray, textTransform: "uppercase", letterSpacing: 0.3 }}>{cat.categoryLabel}</div>
                  {(cat.dependence || cat.frequency) && (
                    <div style={{ fontSize: 11, color: COLORS.gray, marginTop: 2 }}>
                      {[cat.dependence, cat.frequency].filter(Boolean).join(" · ")}
                    </div>
                  )}
                  {cat.categoryInstructions && (
                    <div style={{ fontSize: 11.5, color: COLORS.dark, marginTop: 2, fontStyle: "italic" }}>“{cat.categoryInstructions}”</div>
                  )}
                  {cat.guidance && (
                    <div style={{ fontSize: 11, color: COLORS.gray, marginTop: 2 }}>{cat.guidance}</div>
                  )}
                  <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 10 }}>
                    {cat.items.map((t, idx) => {
                      const result = note.taskResults[t.key] || { state: "", note: "", checklist: [], assistedBy: "", noteIsAuto: true };
                      const catalog = visitFactCatalog(t);
                      const checklist = result.checklist || [];
                      const needsChecklist = result.state === "completed" && !!catalog && checklist.length === 0;
                      const needsAssistedBy = result.state === "completed" && checklist.some((c) => ASSIST_NAME_TRIGGER_CODES.includes(c)) && !result.assistedBy?.trim();
                      const needsFreeNote = (result.state === "refused" || result.state === "notDone") && !result.note?.trim();
                      const anyMissing = needsChecklist || needsAssistedBy || needsFreeNote;
                      const showChecklist = result.state === "completed" && !!catalog;
                      const showNarrative = result.state === "refused" || result.state === "notDone" || result.state === "completed";
                      return (
                        <div key={t.key} style={{
                          paddingTop: idx === 0 ? 0 : 10,
                          borderTop: idx === 0 ? "none" : `1px solid ${COLORS.border}`,
                        }}>
                          <div style={{ fontSize: 12.5, fontWeight: 700, color: anyMissing ? "#b45309" : COLORS.dark }}>{t.label}{t.detail ? ` — ${t.detail}` : ""}</div>
                          <div style={{ display: "flex", gap: 14, marginTop: 6, marginBottom: 6, flexWrap: "wrap" }}>
                            {[["completed", "Completed as ordered"], ["refused", "Patient refused"], ["notDone", "Not done"]].map(([val, lbl]) => (
                              <label key={val} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: COLORS.dark, cursor: "pointer" }}>
                                <input type="radio" name={`task-${t.key}`} checked={result.state === val} onChange={() => setTaskResult(t.key, { state: val })} disabled={visitLocked} />
                                {lbl}
                              </label>
                            ))}
                          </div>
                          {showChecklist && (
                            <div style={{ marginBottom: 6 }}>
                              <div style={{ fontSize: 10.5, fontWeight: 700, color: COLORS.gray, marginBottom: 4 }}>
                                What did you actually do/see? (check all that apply — required)
                              </div>
                              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                                {catalog.map((fact) => (
                                  <label key={fact.code} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: COLORS.dark, cursor: "pointer" }}>
                                    <input
                                      type="checkbox"
                                      checked={checklist.includes(fact.code)}
                                      onChange={(e) => toggleTaskChecklistItem(t, fact.code, e.target.checked)}
                                      disabled={visitLocked}
                                    />
                                    {fact.label}
                                  </label>
                                ))}
                              </div>
                              {needsChecklist && <div style={{ fontSize: 10.5, color: COLORS.warning, marginTop: 2 }}>Check at least one.</div>}
                              {checklist.some((c) => ASSIST_NAME_TRIGGER_CODES.includes(c)) && (
                                <div style={{ marginTop: 6 }}>
                                  <FormInput
                                    label="Who assisted? (name/role — required, staffing safety record)"
                                    value={result.assistedBy}
                                    onChange={(v) => setTaskResult(t.key, { assistedBy: v })}
                                    placeholder="e.g., Second HA, Maria R."
                                    disabled={visitLocked}
                                  />
                                  {needsAssistedBy && <div style={{ fontSize: 10.5, color: COLORS.warning, marginTop: 2 }}>Required.</div>}
                                </div>
                              )}
                            </div>
                          )}
                          {showNarrative && (
                            <div>
                              <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
                                <span style={{ fontSize: 10.5, fontWeight: 700, color: COLORS.gray }}>
                                  {result.state === "completed"
                                    ? "Notes (auto-filled from checklist above — add anything else, or edit)"
                                    : "What happened (required — describe only what you saw/heard)"}
                                </span>
                                {result.state === "completed" && catalog && result.noteIsAuto === false && (
                                  <button type="button" onClick={() => resyncTaskNarrative(t)} style={{ border: "none", background: "transparent", color: COLORS.gray, cursor: "pointer", fontSize: 10.5, textDecoration: "underline" }}>
                                    reset to checklist wording
                                  </button>
                                )}
                              </div>
                              <FormInput
                                value={result.note}
                                onChange={(v) => setTaskNarrative(t.key, v)}
                                placeholder={result.state === "completed" ? "" : "e.g., Patient asked to skip bathing today, said they were too tired"}
                                disabled={visitLocked}
                              />
                              {needsFreeNote && <div style={{ fontSize: 10.5, color: COLORS.warning, marginTop: 2 }}>Required.</div>}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* ── Structured observations — Skin / Respiration / Nutrition ── */}
      <Card title="Skin">
        <FormCheckboxGroup values={note.skin} onChange={(v) => setNote((p) => ({ ...p, skin: v }))} options={CHHA_SKIN_OPTIONS} label="Observed" />
        {skinAbnormal && (
          <div style={{ ...styles.infoBox, borderColor: COLORS.error, color: COLORS.error, fontWeight: 700 }}>🚨 RN Notification Required</div>
        )}
      </Card>

      <Card title="Respiration">
        <FormCheckboxGroup values={note.respiration} onChange={(v) => setNote((p) => ({ ...p, respiration: v }))} options={CHHA_RESPIRATION_OPTIONS} label="Observed" />
        {respirationAbnormal && (
          <div style={{ ...styles.infoBox, borderColor: COLORS.error, color: COLORS.error, fontWeight: 700 }}>🚨 RN Notification Required</div>
        )}
      </Card>

      <Card title="Nutrition / Swallowing">
        <FormCheckboxGroup values={note.nutrition} onChange={(v) => setNote((p) => ({ ...p, nutrition: v }))} options={CHHA_NUTRITION_OPTIONS} label="Observed" />
        {nutritionAbnormal && (
          <div style={{ ...styles.infoBox, borderColor: COLORS.error, color: COLORS.error, fontWeight: 700 }}>🚨 RN Notification Required</div>
        )}
      </Card>

      <Card title="Visit Supplies & Infection Control">
        <div style={{ fontSize: 11.5, color: COLORS.gray, marginBottom: 8 }}>
          Check what was used or observed at this visit.
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(160px, 1fr))", gap: "4px 16px" }}>
          {CHHA_SUPPLY_OPTIONS.map((opt) => (
            <label key={opt.code} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: COLORS.dark, cursor: "pointer", padding: "2px 0" }}>
              <input
                type="checkbox"
                checked={note.supplies.includes(opt.code)}
                disabled={visitLocked}
                onChange={(e) => setNote((p) => ({
                  ...p,
                  supplies: e.target.checked ? [...p.supplies, opt.code] : p.supplies.filter((c) => c !== opt.code),
                }))}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </Card>

      <Card title="Pain / Condition Change">
        <FormCheckbox
          label="Patient showed signs of pain or seemed different from their usual self today"
          checked={note.painOrChangeObserved}
          disabled={visitLocked}
          onChange={(checked) => setNote((p) => ({ ...p, painOrChangeObserved: checked }))}
        />
        {note.painOrChangeObserved && (
          <div style={{ marginTop: 6 }}>
            <FormTextarea
              label="Describe only what you saw or heard (not why you think it happened)"
              value={note.painNote}
              onChange={(v) => setNote((p) => ({ ...p, painNote: v }))}
              rows={2}
              disabled={visitLocked}
            />
          </div>
        )}
      </Card>

      <Card title="Visit Summary">
        <FormSelect
          label="Overall"
          value={note.toleranceToCare}
          onChange={(v) => setNote((p) => ({ ...p, toleranceToCare: v }))}
          options={CHHA_TOLERANCE_OPTIONS}
          disabled={visitLocked}
        />
        <div style={{ marginTop: 8 }}>
          <FormTextarea
            label="Anything else you noticed (describe only what you saw or heard)"
            value={note.exceptionNarrative}
            onChange={(v) => setNote((p) => ({ ...p, exceptionNarrative: v }))}
            rows={2}
            disabled={visitLocked}
          />
        </div>
        <div style={{ marginTop: 8 }}>
          <FormCheckbox
            label="Reviewed care instructions with family/caregiver present"
            checked={note.caregiverInstructionProvided}
            disabled={visitLocked}
            onChange={(checked) => setNote((p) => ({ ...p, caregiverInstructionProvided: checked }))}
          />
        </div>
        <FormCheckbox
          label="Family/caregiver confirmed understanding"
          checked={note.caregiverUnderstandingConfirmed}
          disabled={visitLocked}
          onChange={(checked) => setNote((p) => ({ ...p, caregiverUnderstandingConfirmed: checked }))}
        />
      </Card>

      <Card title="RN Notification">
        {rnNotificationRequired ? (
          <div style={{ ...styles.infoBox, borderColor: COLORS.error, marginBottom: 10 }}>
            <div style={{ fontWeight: 700, color: COLORS.error, marginBottom: 4 }}>🚨 RN Notification Required — call {chhaReportToLabel(reportToRole)} now.</div>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {rnNotificationReasons.map((r) => <li key={r}>{r}</li>)}
            </ul>
          </div>
        ) : (
          <div style={{ fontSize: 12, color: COLORS.gray, marginBottom: 10 }}>Nothing observed today requires RN notification.</div>
        )}
        <FormCheckbox
          label={`I notified ${chhaReportToLabel(reportToRole)}`}
          checked={note.rnNotified}
          disabled={visitLocked}
          onChange={(checked) => setNote((p) => ({ ...p, rnNotified: checked }))}
        />
        {note.rnNotified && (
          <div style={{ marginTop: 6 }}>
            <FormInput
              label="Name of person notified (required)"
              value={note.rnNotifiedName}
              onChange={(v) => setNote((p) => ({ ...p, rnNotifiedName: v }))}
              disabled={visitLocked}
            />
            {missingRnNotifiedName && <div style={{ fontSize: 10.5, color: COLORS.warning, marginTop: 2 }}>Required.</div>}
          </div>
        )}
      </Card>

      <Card title="Submit">
        {missingTaskNotes > 0 && (
          <div style={{ ...styles.infoBox, marginBottom: 8, borderColor: COLORS.warning }}>
            {missingTaskNotes} task{missingTaskNotes > 1 ? "s" : ""} above still {missingTaskNotes > 1 ? "need" : "needs"} a description of what happened.
          </div>
        )}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!canSubmit || saving}
          style={{ ...styles.btnPrimary, opacity: (!canSubmit || saving) ? 0.55 : 1, cursor: (!canSubmit || saving) ? "not-allowed" : "pointer" }}
        >
          {saving ? "Saving…" : "Save Visit Note"}
        </button>
        {!saving && saveMessage && <div style={{ fontSize: 11, color: COLORS.success, marginTop: 6 }}>{saveMessage}</div>}
      </Card>
    </div>
  );
}


//
// Reads the same authoritative poc_problems rows already written by
// PocSectionControls' "Add to POC" (via rnica_poc_adapter), across ALL RN
// ICA sections at once, and exposes View / Edit / Resolve / Deactivate.
//
// Deliberately does NOT:
// - create new problems (no "Add" control here — creation stays scoped to
//   the originating body-system section's PocSectionControls),
// - merge duplicate problems, link an existing problem, or show version
//   history (deferred — see Section 11 spec "Does not" list),
// - replace the assessment section that originated each problem.
const POC_STATUS_COLOR = (status, COLORS) => {
  if (status === "RESOLVED") return COLORS.gray;
  if (status === "HISTORICAL" || status === "SUPERSEDED") return COLORS.gray;
  return COLORS.teal;
};

export function MasterPocReviewCard({ assessmentId, styles, COLORS }) {
  const [problems, setProblems] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [expandedRuleKey, setExpandedRuleKey] = useState(null);
  const [editingRuleKey, setEditingRuleKey] = useState(null);
  const [editDraft, setEditDraft] = useState({ label: "", severity: "", description_addendum: "" });
  const [historyRuleKey, setHistoryRuleKey] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [linkingRuleKey, setLinkingRuleKey] = useState(null);
  const [linkDraft, setLinkDraft] = useState({ sectionKey: "", evidenceText: "" });
  const [linkError, setLinkError] = useState("");
  const [mergingSurvivorKey, setMergingSurvivorKey] = useState(null);
  const [mergeSelection, setMergeSelection] = useState(() => new Set());
  const [mergeReason, setMergeReason] = useState("");
  const [mergeError, setMergeError] = useState("");

  const loadProblems = useCallback(() => {
    if (!assessmentId) return;
    setLoading(true);
    setError("");
    viewRnicaAllPoc(assessmentId)
      .then((res) => setProblems(res?.problems || []))
      .catch((err) => setError(err.message || "Unable to load Plan of Care"))
      .finally(() => setLoading(false));
  }, [assessmentId]);

  useEffect(() => {
    loadProblems();
  }, [loadProblems]);

  const startEdit = (p) => {
    setEditingRuleKey(editingRuleKey === p.rule_key ? null : p.rule_key);
    setEditDraft({ label: p.label || "", severity: p.severity && p.severity !== "UNKNOWN" ? p.severity : "", description_addendum: "" });
  };

  const handleSaveEdit = (p) => {
    setSaving(true);
    setError("");
    updateRnicaSectionPocProblem(assessmentId, p.origin_section, p.rule_key, {
      label: editDraft.label.trim() || undefined,
      severity: editDraft.severity || undefined,
      description_addendum: editDraft.description_addendum.trim() || undefined,
    })
      .then(() => {
        setEditingRuleKey(null);
        setEditDraft({ label: "", severity: "", description_addendum: "" });
        loadProblems();
      })
      .catch((err) => setError(err.message || "Unable to update Plan of Care problem"))
      .finally(() => setSaving(false));
  };

  const handleResolve = (p) => {
    setSaving(true);
    setError("");
    resolveRnicaSectionPocProblem(assessmentId, p.origin_section, p.rule_key)
      .then(() => loadProblems())
      .catch((err) => setError(err.message || "Unable to resolve Plan of Care problem"))
      .finally(() => setSaving(false));
  };

  const handleDeactivate = (p) => {
    setSaving(true);
    setError("");
    deactivateRnicaSectionPocProblem(assessmentId, p.origin_section, p.rule_key)
      .then(() => loadProblems())
      .catch((err) => setError(err.message || "Unable to deactivate Plan of Care problem"))
      .finally(() => setSaving(false));
  };

  const toggleHistory = (p) => {
    if (historyRuleKey === p.rule_key) {
      setHistoryRuleKey(null);
      setHistoryData(null);
      setHistoryError("");
      return;
    }
    setHistoryRuleKey(p.rule_key);
    setHistoryData(null);
    setHistoryError("");
    setHistoryLoading(true);
    getRnicaSectionPocProblemHistory(assessmentId, p.origin_section, p.rule_key)
      .then((res) => setHistoryData(res))
      .catch((err) => setHistoryError(err.message || "Unable to load problem history"))
      .finally(() => setHistoryLoading(false));
  };

  // SECTION 11.C — Link Existing Problem. No new Plan of Care storage,
  // no duplicate problem creation: this reuses the same rule_key-matched
  // problem and only attaches additional documented evidence to it.
  const toggleLinkExisting = (p) => {
    if (linkingRuleKey === p.rule_key) {
      setLinkingRuleKey(null);
      setLinkDraft({ sectionKey: "", evidenceText: "" });
      setLinkError("");
      return;
    }
    setLinkingRuleKey(p.rule_key);
    setLinkDraft({ sectionKey: "", evidenceText: "" });
    setLinkError("");
  };

  const handleLinkExisting = (p) => {
    if (!linkDraft.sectionKey.trim()) {
      setLinkError("Select which section documents this additional evidence.");
      return;
    }
    if (!linkDraft.evidenceText.trim()) {
      setLinkError("Evidence text is required to link this problem.");
      return;
    }
    setSaving(true);
    setLinkError("");
    linkExistingRnicaSectionPocProblem(assessmentId, linkDraft.sectionKey.trim(), {
      rule_key: p.rule_key,
      evidence_text: linkDraft.evidenceText.trim(),
    })
      .then(() => {
        setLinkingRuleKey(null);
        setLinkDraft({ sectionKey: "", evidenceText: "" });
        loadProblems();
      })
      .catch((err) => setLinkError(err.message || "Unable to link existing Plan of Care problem"))
      .finally(() => setSaving(false));
  };

  const knownSectionKeys = Array.from(
    new Set((problems || []).map((p) => p.origin_section).filter(Boolean))
  ).sort();

  // SECTION 11 — Merge Duplicate Problems. Consolidates one or more
  // clinician-identified duplicates (matched by rule_key) into a single
  // surviving problem. Nothing is deleted: duplicates are marked
  // SUPERSEDED (an existing status value — no schema change) and remain
  // visible via View History; their evidence/description fold into the
  // survivor.
  const toggleMerge = (p) => {
    if (mergingSurvivorKey === p.rule_key) {
      setMergingSurvivorKey(null);
      setMergeSelection(new Set());
      setMergeReason("");
      setMergeError("");
      return;
    }
    setMergingSurvivorKey(p.rule_key);
    setMergeSelection(new Set());
    setMergeReason("");
    setMergeError("");
  };

  const toggleMergeCandidate = (ruleKey) => {
    setMergeSelection((prev) => {
      const next = new Set(prev);
      if (next.has(ruleKey)) next.delete(ruleKey);
      else next.add(ruleKey);
      return next;
    });
  };

  const handleMerge = (survivor) => {
    if (mergeSelection.size === 0) {
      setMergeError("Select at least one duplicate problem to merge.");
      return;
    }
    if (!mergeReason.trim()) {
      setMergeError("A reason is required to merge duplicate problems.");
      return;
    }
    setSaving(true);
    setMergeError("");
    mergeRnicaPocDuplicateProblems(assessmentId, {
      surviving_rule_key: survivor.rule_key,
      duplicate_rule_keys: Array.from(mergeSelection),
      reason: mergeReason.trim(),
    })
      .then(() => {
        setMergingSurvivorKey(null);
        setMergeSelection(new Set());
        setMergeReason("");
        loadProblems();
      })
      .catch((err) => setMergeError(err.message || "Unable to merge duplicate Plan of Care problems"))
      .finally(() => setSaving(false));
  };

  if (!assessmentId) {
    return <div style={styles.infoBox}>Save the assessment once to enable the Master Plan of Care Review.</div>;
  }

  return (
    <div>
      <div style={{ ...styles.infoBox, marginBottom: 10 }}>
        A synchronized, read-oriented view of every problem already recorded on the Plan of Care from any RN ICA
        section. This is a review and governance layer, not a second Plan of Care record — new problems are still
        added from the section that identified them.
      </div>

      {loading && <div style={{ fontSize: 12, color: COLORS.gray }}>Loading Plan of Care…</div>}
      {error && <div style={{ color: COLORS.error, fontSize: 12, marginBottom: 8 }}>{error}</div>}
      {!loading && problems && problems.length === 0 && (
        <div style={styles.infoBox}>No Plan of Care problems have been recorded yet.</div>
      )}

      {!loading && problems && problems.map((p) => {
        const isActive = p.status !== "RESOLVED" && p.status !== "HISTORICAL" && p.status !== "SUPERSEDED";
        const isExpanded = expandedRuleKey === p.rule_key;
        const disciplines = Array.from(
          new Set((p.goals || []).flatMap((g) => (g.interventions || []).map((i) => i.discipline).filter(Boolean)))
        );

        return (
          <div key={p.rule_key} style={{
            padding: "10px 12px", borderRadius: 8, border: `1px solid ${COLORS.border}`,
            marginBottom: 8, fontSize: 12.5, background: isActive ? "transparent" : COLORS.bg,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
              <strong>{p.label}</strong>
              <span style={{ fontWeight: 700, color: POC_STATUS_COLOR(p.status, COLORS) }}>
                {p.status} {p.severity && p.severity !== "UNKNOWN" ? `· ${p.severity}` : ""}
              </span>
            </div>
            <div style={{ color: COLORS.gray, fontSize: 11, marginTop: 4 }}>
              Origin Section: <strong>{p.origin_section || "—"}</strong>
              {disciplines.length > 0 && <> · Disciplines: <strong>{disciplines.join(", ")}</strong></>}
              {p.status === "SUPERSEDED" && p.merged_into_rule_key && (
                <> · Merged into: <strong>{p.merged_into_rule_key}</strong></>
              )}
            </div>

            <div style={{ marginTop: 6, display: "flex", gap: 6, flexWrap: "wrap" }}>
              <button type="button" onClick={() => setExpandedRuleKey(isExpanded ? null : p.rule_key)} style={{
                fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5,
                border: `1px solid ${COLORS.teal}`, background: "transparent", color: COLORS.teal, cursor: "pointer",
              }}>
                {isExpanded ? "Hide Details" : "View Problem"}
              </button>
              <button type="button" onClick={() => toggleHistory(p)} style={{
                fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5,
                border: `1px solid ${COLORS.gray}`, background: "transparent", color: COLORS.gray, cursor: "pointer",
              }}>
                {historyRuleKey === p.rule_key ? "Hide History" : "View History"}
              </button>
              {isActive && (
                <button type="button" onClick={() => toggleLinkExisting(p)} style={{
                  fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5,
                  border: `1px solid ${COLORS.teal}`, background: "transparent", color: COLORS.teal, cursor: "pointer",
                }}>
                  {linkingRuleKey === p.rule_key ? "Cancel Link" : "Link Existing Problem"}
                </button>
              )}
              {isActive && (problems || []).some((other) => other.rule_key !== p.rule_key && other.status !== "SUPERSEDED") && (
                <button type="button" onClick={() => toggleMerge(p)} style={{
                  fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5,
                  border: `1px solid ${COLORS.teal}`, background: "transparent", color: COLORS.teal, cursor: "pointer",
                }}>
                  {mergingSurvivorKey === p.rule_key ? "Cancel Merge" : "Merge Duplicates Into This"}
                </button>
              )}
              {isActive && (
                <>
                  <button type="button" onClick={() => startEdit(p)} style={{
                    fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5,
                    border: `1px solid ${COLORS.teal}`, background: "transparent", color: COLORS.teal, cursor: "pointer",
                  }}>
                    Edit Problem
                  </button>
                  <button type="button" disabled={saving} onClick={() => handleResolve(p)} style={{
                    fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5,
                    border: `1px solid ${COLORS.gray}`, background: "transparent", color: COLORS.gray, cursor: "pointer",
                  }}>
                    Resolve Problem
                  </button>
                  <button type="button" disabled={saving} onClick={() => handleDeactivate(p)} style={{
                    fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5,
                    border: `1px solid ${COLORS.gray}`, background: "transparent", color: COLORS.gray, cursor: "pointer",
                  }}>
                    Deactivate Problem
                  </button>
                </>
              )}
            </div>

            {editingRuleKey === p.rule_key && (
              <div style={{ marginTop: 8, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 8 }}>
                <FormInput label="Problem Label" value={editDraft.label} onChange={(v) => setEditDraft((d) => ({ ...d, label: v }))} />
                <FormSelect label="Severity" value={editDraft.severity} onChange={(v) => setEditDraft((d) => ({ ...d, severity: v }))}
                  options={["LOW", "MODERATE", "HIGH", "CRITICAL"]} />
                <FormInput label="Update / Progress Note" value={editDraft.description_addendum}
                  onChange={(v) => setEditDraft((d) => ({ ...d, description_addendum: v }))} />
                <button type="button" disabled={saving} onClick={() => handleSaveEdit(p)} style={{
                  fontSize: 11.5, fontWeight: 700, padding: "6px 10px", borderRadius: 5, border: "none",
                  background: COLORS.teal, color: COLORS.white, cursor: saving ? "wait" : "pointer", alignSelf: "end",
                }}>
                  {saving ? "Saving…" : "Save Update"}
                </button>
              </div>
            )}

            {linkingRuleKey === p.rule_key && (
              <div style={{ marginTop: 8, paddingTop: 8, borderTop: `1px dashed ${COLORS.border}` }}>
                <div style={{ color: COLORS.gray, fontSize: 11.5, marginBottom: 6 }}>
                  Attach additional documented evidence — from another RN ICA section — to this same problem. This
                  never creates a duplicate problem; the finding is linked to <strong>{p.label}</strong>, which
                  remains sourced from <strong>{p.origin_section}</strong>.
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 8 }}>
                  <FormSelect
                    label="Evidence Documented In Section"
                    value={linkDraft.sectionKey}
                    onChange={(v) => setLinkDraft((d) => ({ ...d, sectionKey: v }))}
                    options={knownSectionKeys}
                  />
                  <FormInput
                    label="Evidence Text"
                    value={linkDraft.evidenceText}
                    onChange={(v) => setLinkDraft((d) => ({ ...d, evidenceText: v }))}
                  />
                  <button type="button" disabled={saving} onClick={() => handleLinkExisting(p)} style={{
                    fontSize: 11.5, fontWeight: 700, padding: "6px 10px", borderRadius: 5, border: "none",
                    background: COLORS.teal, color: COLORS.white, cursor: saving ? "wait" : "pointer", alignSelf: "end",
                  }}>
                    {saving ? "Linking…" : "Link Evidence"}
                  </button>
                </div>
                {linkError && <div style={{ color: COLORS.error, fontSize: 11.5, marginTop: 6 }}>{linkError}</div>}
              </div>
            )}

            {mergingSurvivorKey === p.rule_key && (
              <div style={{ marginTop: 8, paddingTop: 8, borderTop: `1px dashed ${COLORS.border}` }}>
                <div style={{ color: COLORS.gray, fontSize: 11.5, marginBottom: 6 }}>
                  Select one or more duplicate problems to merge into <strong>{p.label}</strong>. Duplicates are
                  never deleted — they are marked SUPERSEDED and their evidence and description are folded into
                  this problem, remaining fully traceable via View History.
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 8 }}>
                  {(problems || [])
                    .filter((other) => other.rule_key !== p.rule_key && other.status !== "SUPERSEDED")
                    .map((other) => (
                      <label key={other.rule_key} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11.5 }}>
                        <input
                          type="checkbox"
                          checked={mergeSelection.has(other.rule_key)}
                          onChange={() => toggleMergeCandidate(other.rule_key)}
                        />
                        {other.label} <span style={{ color: COLORS.gray }}>({other.origin_section || "—"})</span>
                      </label>
                    ))}
                  {(problems || []).filter((other) => other.rule_key !== p.rule_key && other.status !== "SUPERSEDED").length === 0 && (
                    <div style={{ color: COLORS.gray, fontSize: 11.5 }}>No other active problems available to merge.</div>
                  )}
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 8 }}>
                  <FormInput label="Merge Reason" value={mergeReason} onChange={setMergeReason} />
                  <button type="button" disabled={saving} onClick={() => handleMerge(p)} style={{
                    fontSize: 11.5, fontWeight: 700, padding: "6px 10px", borderRadius: 5, border: "none",
                    background: COLORS.teal, color: COLORS.white, cursor: saving ? "wait" : "pointer", alignSelf: "end",
                  }}>
                    {saving ? "Merging…" : "Merge Selected"}
                  </button>
                </div>
                {mergeError && <div style={{ color: COLORS.error, fontSize: 11.5, marginTop: 6 }}>{mergeError}</div>}
              </div>
            )}

            {isExpanded && (
              <div style={{ marginTop: 8, paddingTop: 8, borderTop: `1px dashed ${COLORS.border}` }}>
                <div style={{ color: COLORS.gray, fontSize: 11.5, whiteSpace: "pre-wrap" }}>
                  <strong>Source Evidence:</strong> {p.description || "—"}
                </div>
                {(p.evidence_sources || []).length > 0 && (
                  <div style={{ marginTop: 6 }}>
                    <div style={{ fontWeight: 700, fontSize: 11.5 }}>Linked Evidence Sources</div>
                    {(p.evidence_sources || []).map((s, si) => (
                      <div key={si} style={{ color: COLORS.gray, fontSize: 11.5, marginTop: 2 }}>
                        From <strong>{s.section_key}</strong>: {s.evidence_text}
                        {s.linked_by ? ` — linked by ${s.linked_by}` : ""}
                        {s.linked_at ? ` on ${new Date(s.linked_at).toLocaleString()}` : ""}
                      </div>
                    ))}
                  </div>
                )}
                {(p.merged_from || []).length > 0 && (
                  <div style={{ marginTop: 6 }}>
                    <div style={{ fontWeight: 700, fontSize: 11.5 }}>Merged Duplicate Problems</div>
                    {(p.merged_from || []).map((m, mi) => (
                      <div key={mi} style={{ color: COLORS.gray, fontSize: 11.5, marginTop: 2 }}>
                        <strong>{m.label}</strong> ({m.rule_key}) from <strong>{m.origin_section || "—"}</strong>
                        {m.merged_by ? ` — merged by ${m.merged_by}` : ""}
                        {m.merged_at ? ` on ${new Date(m.merged_at).toLocaleString()}` : ""}
                        {m.merge_reason ? ` — ${m.merge_reason}` : ""}
                      </div>
                    ))}
                  </div>
                )}
                {(p.goals || []).length === 0 && (
                  <div style={{ color: COLORS.gray, fontSize: 11.5, marginTop: 6 }}>No goals recorded.</div>
                )}
                {(p.goals || []).map((g, gi) => (
                  <div key={gi} style={{ marginTop: 8 }}>
                    <div style={{ fontWeight: 700 }}>
                      Goal: {g.goal_text} <span style={{ fontWeight: 400, color: COLORS.gray }}>({g.status})</span>
                    </div>
                    {(g.interventions || []).length === 0 && (
                      <div style={{ color: COLORS.gray, fontSize: 11.5, marginLeft: 12 }}>No interventions recorded.</div>
                    )}
                    {(g.interventions || []).map((iv, ii) => (
                      <div key={ii} style={{ marginLeft: 12, fontSize: 11.5, color: COLORS.gray }}>
                        {iv.discipline || "—"}: {iv.intervention_text || "—"}
                        {iv.frequency ? ` (${iv.frequency})` : ""} — {iv.status}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}

            {historyRuleKey === p.rule_key && (
              <div style={{ marginTop: 8, paddingTop: 8, borderTop: `1px dashed ${COLORS.border}`, fontSize: 11.5 }}>
                <div style={{ fontWeight: 700, marginBottom: 6 }}>Problem History (read-only)</div>
                {historyLoading && <div style={{ color: COLORS.gray }}>Loading history…</div>}
                {historyError && <div style={{ color: COLORS.error }}>{historyError}</div>}
                {!historyLoading && !historyError && historyData && (
                  <div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 6, marginBottom: 8 }}>
                      <div><strong>Created By:</strong> {historyData.createdBy || "—"}</div>
                      <div><strong>Created Date:</strong> {historyData.createdDate ? new Date(historyData.createdDate).toLocaleString() : "—"}</div>
                      <div><strong>Last Updated By:</strong> {historyData.lastUpdatedBy || "—"}</div>
                      <div><strong>Last Updated Date:</strong> {historyData.lastUpdatedDate ? new Date(historyData.lastUpdatedDate).toLocaleString() : "—"}</div>
                    </div>

                    <div style={{ fontWeight: 700, marginTop: 6 }}>Status Changes</div>
                    {(historyData.statusChanges || []).length === 0 && (
                      <div style={{ color: COLORS.gray }}>No status changes recorded since creation.</div>
                    )}
                    {(historyData.statusChanges || []).map((c, ci) => (
                      <div key={ci} style={{ color: COLORS.gray, marginTop: 2 }}>
                        v{c.versionNumber}: {c.fromStatus} → {c.toStatus} by {c.changedBy} on{" "}
                        {c.changedAt ? new Date(c.changedAt).toLocaleString() : "—"}
                        {c.changeReason ? ` — ${c.changeReason}` : ""}
                      </div>
                    ))}

                    <div style={{ fontWeight: 700, marginTop: 6 }}>Resolve Events</div>
                    {(historyData.resolveEvents || []).length === 0 && (
                      <div style={{ color: COLORS.gray }}>None.</div>
                    )}
                    {(historyData.resolveEvents || []).map((c, ci) => (
                      <div key={ci} style={{ color: COLORS.gray, marginTop: 2 }}>
                        Resolved by {c.changedBy} on {c.changedAt ? new Date(c.changedAt).toLocaleString() : "—"}
                      </div>
                    ))}

                    <div style={{ fontWeight: 700, marginTop: 6 }}>Deactivate Events</div>
                    {(historyData.deactivateEvents || []).length === 0 && (
                      <div style={{ color: COLORS.gray }}>None.</div>
                    )}
                    {(historyData.deactivateEvents || []).map((c, ci) => (
                      <div key={ci} style={{ color: COLORS.gray, marginTop: 2 }}>
                        Deactivated by {c.changedBy} on {c.changedAt ? new Date(c.changedAt).toLocaleString() : "—"}
                      </div>
                    ))}

                    <div style={{ fontWeight: 700, marginTop: 6 }}>Merge Events</div>
                    {(historyData.mergeEvents || []).length === 0 && (
                      <div style={{ color: COLORS.gray }}>None.</div>
                    )}
                    {(historyData.mergeEvents || []).map((c, ci) => (
                      <div key={ci} style={{ color: COLORS.gray, marginTop: 2 }}>
                        Merged (superseded) by {c.changedBy} on {c.changedAt ? new Date(c.changedAt).toLocaleString() : "—"}
                        {c.changeReason ? ` — ${c.changeReason}` : ""}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// SECTION 12 — Post-lock amendments. The Lock button itself (see handleLock)
// runs the same finalization-readiness check the backend enforces
// server-side (rnica_finalization_service.py) and, if anything is missing,
// tells the nurse exactly what and navigates them to the relevant section —
// so there is no need for a standing pre-lock checklist card cluttering the
// assessment. Once locked, this card exposes the amendment entry point.
const AMENDMENT_CATEGORY_OPTIONS = [
  { value: "CLINICAL_CORRECTION", label: "Clinical correction" },
  { value: "ADDITIONAL_FINDING", label: "Additional finding" },
  { value: "DOCUMENTATION_ERROR", label: "Documentation error" },
  { value: "CLARIFICATION", label: "Clarification" },
  { value: "OTHER", label: "Other" },
];

const AMENDMENT_REASON_CODE_OPTIONS = [
  { value: "OMITTED_FINDING", label: "Omitted finding" },
  { value: "INCORRECT_VALUE", label: "Incorrect value" },
  { value: "CLARIFICATION_NEEDED", label: "Clarification needed" },
  { value: "LATE_ENTRY", label: "Late entry" },
  { value: "OTHER", label: "Other" },
];

const AMENDMENT_REQUEST_SOURCE_OPTIONS = [
  { value: "PATIENT", label: "Patient" },
  { value: "REPRESENTATIVE", label: "Representative" },
  { value: "STAFF", label: "Staff" },
  { value: "INTERNAL_QA", label: "Internal QA" },
];

// SECTION 12 -- who may approve/deny a proposed amendment. Mirrors the
// server's AMENDMENT_APPROVAL_ROLES gate (app/api/visits.py) so the button
// is hidden for roles the backend would 403 anyway; the backend remains the
// real enforcement point.
const AMENDMENT_APPROVAL_ROLES = new Set([
  "DPCS",
  "DPCS_DESIGNEE",
  "CASE_MANAGER",
  "SUPERVISOR",
  "ADMIN",
  "ADMINISTRATOR",
  "QA",
  "SYSTEM",
]);

function AmendmentPanel({ assessmentId, styles, COLORS }) {
  const [amendments, setAmendments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [decidingId, setDecidingId] = useState(null);
  const [message, setMessage] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    amendmentCategory: "",
    reasonCode: "",
    requestedChange: "",
    requestSource: "STAFF",
    sectionReference: "",
    proposedValue: "",
  });

  const currentUser = getCurrentUser();
  const currentRole = String(currentUser?.role || "").trim().toUpperCase();
  const currentUserId = currentUser?.userId || currentUser?.user_id || currentUser?.id || null;
  const canReview = AMENDMENT_APPROVAL_ROLES.has(currentRole);

  const loadAmendments = useCallback(() => {
    if (!assessmentId) return;
    setLoading(true);
    setError("");
    listRnicaAmendments(assessmentId)
      .then((res) => setAmendments(res?.amendments || []))
      .catch((err) => setError(err.message || "Unable to load amendment history"))
      .finally(() => setLoading(false));
  }, [assessmentId]);

  useEffect(() => {
    loadAmendments();
  }, [loadAmendments]);

  const updateForm = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = () => {
    if (!form.amendmentCategory || !form.reasonCode || !form.requestedChange.trim()) {
      setMessage("Category, reason, and the requested change are required.");
      return;
    }
    setSubmitting(true);
    setMessage("");
    requestRnicaCorrection(assessmentId, {
      amendmentCategory: form.amendmentCategory,
      reasonCode: form.reasonCode,
      requestedChange: form.requestedChange,
      requestSource: form.requestSource,
      sectionReference: form.sectionReference.trim() || null,
      proposedValue: form.proposedValue.trim() || null,
    })
      .then(() => {
        setMessage("Amendment submitted and is pending review.");
        setForm({ amendmentCategory: "", reasonCode: "", requestedChange: "", requestSource: "STAFF", sectionReference: "", proposedValue: "" });
        setShowForm(false);
        loadAmendments();
      })
      .catch((err) => setMessage(err.message || "Amendment submission failed."))
      .finally(() => setSubmitting(false));
  };

  const handleApprove = (amendmentId) => {
    setDecidingId(amendmentId);
    setMessage("");
    approveRnicaAmendment(assessmentId, amendmentId)
      .then(() => {
        setMessage("Amendment approved.");
        loadAmendments();
      })
      .catch((err) => setMessage(err.message || "Unable to approve amendment."))
      .finally(() => setDecidingId(null));
  };

  const handleDeny = (amendmentId) => {
    const reason = window.prompt("Reason for denying this amendment:");
    if (reason == null) return;
    if (!reason.trim()) {
      setMessage("A denial reason is required.");
      return;
    }
    setDecidingId(amendmentId);
    setMessage("");
    denyRnicaAmendment(assessmentId, amendmentId, reason.trim())
      .then(() => {
        setMessage("Amendment denied.");
        loadAmendments();
      })
      .catch((err) => setMessage(err.message || "Unable to deny amendment."))
      .finally(() => setDecidingId(null));
  };

  const statusColor = (status) => {
    if (status === "APPROVED") return COLORS.success || "#16a34a";
    if (status === "DENIED") return COLORS.error;
    return COLORS.gray;
  };

  return (
    <div style={{ marginTop: 14, paddingTop: 10, borderTop: `1px dashed ${COLORS.border}` }}>
      <div style={{ fontWeight: 700, fontSize: 12.5, marginBottom: 4 }}>Correction / Amendment</div>
      <div style={{ color: COLORS.gray, fontSize: 11.5, marginBottom: 6 }}>
        This assessment is locked and signed. A correction is a distinct, traceable addendum linked to the
        original -- it never overwrites the signed content, even once approved.
      </div>

      <button type="button" onClick={() => setShowForm((v) => !v)} style={{
        fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5,
        border: `1px solid ${COLORS.gray}`, background: "transparent", color: COLORS.gray, cursor: "pointer",
      }}>
        {showForm ? "Cancel" : "Request Correction / Amendment"}
      </button>

      {showForm && (
        <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 6, maxWidth: 480 }}>
          <label style={{ fontSize: 11, fontWeight: 600 }}>
            Category
            <select
              value={form.amendmentCategory}
              onChange={(e) => updateForm("amendmentCategory", e.target.value)}
              style={{ display: "block", width: "100%", marginTop: 2, fontSize: 12, padding: 4 }}
            >
              <option value="">Select…</option>
              {AMENDMENT_CATEGORY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
          <label style={{ fontSize: 11, fontWeight: 600 }}>
            Reason
            <select
              value={form.reasonCode}
              onChange={(e) => updateForm("reasonCode", e.target.value)}
              style={{ display: "block", width: "100%", marginTop: 2, fontSize: 12, padding: 4 }}
            >
              <option value="">Select…</option>
              {AMENDMENT_REASON_CODE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
          <label style={{ fontSize: 11, fontWeight: 600 }}>
            Requested by
            <select
              value={form.requestSource}
              onChange={(e) => updateForm("requestSource", e.target.value)}
              style={{ display: "block", width: "100%", marginTop: 2, fontSize: 12, padding: 4 }}
            >
              {AMENDMENT_REQUEST_SOURCE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
          <label style={{ fontSize: 11, fontWeight: 600 }}>
            Section reference (optional)
            <input
              type="text"
              value={form.sectionReference}
              onChange={(e) => updateForm("sectionReference", e.target.value)}
              placeholder="e.g. section_10_clinical_narrative"
              style={{ display: "block", width: "100%", marginTop: 2, fontSize: 12, padding: 4 }}
            />
          </label>
          <label style={{ fontSize: 11, fontWeight: 600 }}>
            Requested change
            <textarea
              value={form.requestedChange}
              onChange={(e) => updateForm("requestedChange", e.target.value)}
              rows={3}
              style={{ display: "block", width: "100%", marginTop: 2, fontSize: 12, padding: 4 }}
            />
          </label>
          <label style={{ fontSize: 11, fontWeight: 600 }}>
            Proposed value (optional, for reference only -- never auto-applied)
            <textarea
              value={form.proposedValue}
              onChange={(e) => updateForm("proposedValue", e.target.value)}
              rows={2}
              style={{ display: "block", width: "100%", marginTop: 2, fontSize: 12, padding: 4 }}
            />
          </label>
          <button type="button" disabled={submitting} onClick={handleSubmit} style={{
            alignSelf: "flex-start", fontSize: 11, fontWeight: 700, padding: "4px 8px", borderRadius: 5,
            border: `1px solid ${COLORS.teal}`, background: COLORS.teal, color: "#fff",
            cursor: submitting ? "wait" : "pointer",
          }}>
            {submitting ? "Submitting…" : "Submit Amendment"}
          </button>
        </div>
      )}

      {message && <div style={{ color: COLORS.gray, fontSize: 11.5, marginTop: 6 }}>{message}</div>}

      {loading && <div style={{ fontSize: 11.5, color: COLORS.gray, marginTop: 8 }}>Loading amendment history…</div>}
      {error && <div style={{ color: COLORS.error, fontSize: 11.5, marginTop: 8 }}>{error}</div>}

      {!loading && amendments.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <div style={{ fontWeight: 700, fontSize: 12, marginBottom: 4 }}>Amendment History</div>
          {amendments.map((a) => (
            <div key={a.id} style={{
              padding: "6px 0", borderBottom: `1px solid ${COLORS.border}`, fontSize: 11.5,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                <span style={{ fontWeight: 600 }}>
                  {AMENDMENT_CATEGORY_OPTIONS.find((o) => o.value === a.amendmentCategory)?.label || a.amendmentCategory}
                  {a.sectionReference ? ` — ${a.sectionReference}` : ""}
                </span>
                <span style={{ color: statusColor(a.status), fontWeight: 700 }}>{a.status}</span>
              </div>
              <div style={{ color: COLORS.gray, marginTop: 2 }}>{a.requestedChange}</div>
              <div style={{ color: COLORS.gray, marginTop: 2, fontSize: 11 }}>
                Requested by: {AMENDMENT_REQUEST_SOURCE_OPTIONS.find((o) => o.value === a.requestSource)?.label || a.requestSource || "Staff"}
              </div>
              {(a.status === "APPROVED" || a.status === "DENIED") && a.decisionUserId && (
                <div style={{ color: COLORS.gray, marginTop: 2, fontSize: 11 }}>
                  Decision by {a.decisionUserId} on {a.decisionTimestamp ? new Date(a.decisionTimestamp).toLocaleString() : "—"}
                </div>
              )}
              {a.status === "DENIED" && a.decisionReason && (
                <div style={{ color: COLORS.error, marginTop: 2 }}>Denied: {a.decisionReason}</div>
              )}
              {a.status === "APPROVED" && a.decisionReason && (
                <div style={{ color: COLORS.gray, marginTop: 2 }}>Note: {a.decisionReason}</div>
              )}
              {a.status === "PENDING" && canReview && String(currentUserId) !== String(a.createdBy) && (
                <div style={{ marginTop: 4, display: "flex", gap: 6 }}>
                  <button type="button" disabled={decidingId === a.id} onClick={() => handleApprove(a.id)} style={{
                    fontSize: 11, fontWeight: 700, padding: "3px 7px", borderRadius: 5,
                    border: `1px solid ${COLORS.success || "#16a34a"}`, background: "transparent",
                    color: COLORS.success || "#16a34a", cursor: decidingId === a.id ? "wait" : "pointer",
                  }}>
                    Approve
                  </button>
                  <button type="button" disabled={decidingId === a.id} onClick={() => handleDeny(a.id)} style={{
                    fontSize: 11, fontWeight: 700, padding: "3px 7px", borderRadius: 5,
                    border: `1px solid ${COLORS.error}`, background: "transparent",
                    color: COLORS.error, cursor: decidingId === a.id ? "wait" : "pointer",
                  }}>
                    Deny
                  </button>
                </div>
              )}
              {a.status === "PENDING" && canReview && String(currentUserId) === String(a.createdBy) && (
                <div style={{ color: COLORS.gray, marginTop: 4, fontStyle: "italic" }}>
                  Awaiting review by another reviewer (you submitted this amendment).
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Locked assessments can no longer be edited directly, so this is just the
// amendment entry point (propose/review corrections). Nothing is rendered
// pre-lock — see the note above on why the readiness checklist itself was
// removed from the assessment body.
function FinalReviewDashboardCard({ assessmentId, locked, styles, COLORS }) {
  if (!locked) return null;
  return <AmendmentPanel assessmentId={assessmentId} styles={styles} COLORS={COLORS} />;
}


// the same way WeightLossAutoCalcCard turns raw weights into a % change.
// The RN still confirms/overrides via the existing Constipation radio below;
// this card only proposes a starting point so the RN isn't over-analyzing.
const CONSTIPATION_THRESHOLDS = [
  { maxDays: 2, severity: "None" },
  { maxDays: 4, severity: "Mild" },
  { maxDays: 6, severity: "Moderate" },
  { maxDays: Infinity, severity: "Severe" },
];

function ConstipationAutoAssessCard({ lastBM, diarrhea, existingValue, updateField, styles, COLORS }) {
  const [inserted, setInserted] = useState(false);

  const suggestion = useMemo(() => {
    if (!lastBM) return null;
    const lastDate = new Date(lastBM);
    if (Number.isNaN(lastDate.getTime())) return null;

    const daysSince = Math.floor((Date.now() - lastDate.getTime()) / 86400000);
    if (daysSince < 0) return null; // future date entered — don't guess

    const match = CONSTIPATION_THRESHOLDS.find((t) => daysSince <= t.maxDays);
    return {
      daysSince,
      severity: match.severity,
      text: `${daysSince} day${daysSince === 1 ? "" : "s"} since last BM (${formatDate(lastBM)}) → suggested: ${match.severity}`,
    };
  }, [lastBM]);

  const diarrheaActive = diarrhea && diarrhea !== "None" && diarrhea !== "";

  const handleInsert = () => {
    if (!suggestion) return;
    updateField("constipation", suggestion.severity);
    setInserted(true);
    window.setTimeout(() => setInserted(false), 2000);
  };

  if (!lastBM) {
    return <div style={styles.infoBox}>Enter "Last BM Date" below (ask: when did the patient last have a bowel movement?) to auto-suggest constipation severity.</div>;
  }
  if (diarrheaActive) {
    return (
      <div style={styles.infoBox}>
        Diarrhea reported ({diarrhea}) — constipation suggestion skipped since the two findings conflict. Document constipation manually if clinically applicable.
      </div>
    );
  }
  if (!suggestion) {
    return <div style={styles.infoBox}>Last BM date could not be interpreted — re-check the entered date.</div>;
  }

  return (
    <div>
      <div style={styles.infoBox}>{suggestion.text}</div>
      {existingValue && (
        <div style={{ fontSize: 12, color: COLORS.gray, marginTop: 6 }}>
          Current documented value: "{existingValue}"
        </div>
      )}
      <button type="button" onClick={handleInsert} style={{
        marginTop: 8, padding: "6px 12px", borderRadius: 6, border: `1px solid ${COLORS.teal}`,
        background: inserted ? COLORS.teal : "transparent", color: inserted ? COLORS.white : COLORS.teal,
        fontSize: 12, fontWeight: 700, cursor: "pointer",
      }}>
        {inserted ? "Inserted!" : "Insert into Constipation field"}
      </button>
    </div>
  );
}

// Owner correction (2026-09-25): Symptom Impact / "Symptom Burden Matrix"
// is no longer an RN-facing card at all -- each J2051 item is documented
// once in its true owning section (Pain, Respiratory, GI, Neuro/Mental
// Status). HOPE J2051 continues to be derived from those source fields
// via the symptomImpact sync effect (see below); there is no card or
// component to render here.

// ── Referral-Determination Suggestion (Psychosocial / Spiritual /
// Bereavement) ───────────────────────────────────────────────────────────
// Owner design correction (2026-09-25, refined 2026-09-25): Psychosocial,
// Spiritual, and Bereavement are referral-determination workflows, not
// standalone discipline assessments, and the RN must NOT manually classify
// referral priority (Routine/Priority/Urgent) -- that adds documentation
// burden. The RN documents findings only; SNS derives a binary YES/NO
// recommendation from those findings (resolveReferralRecommendation,
// deterministic rule-based logic, not a real AI/ML call -- shared with
// clinicalNarrativeBuilder.js). This card is purely informational and
// writes nothing to formData: the RN confirms by acting on the
// recommendation, then records the outcome via the section's own Family
// Response field (Accepted / Refused / Deferred).
const REFERRAL_DOMAIN_LABELS = {
  psychosocial: "MSW Referral",
  spiritual: "Spiritual Care Referral",
  bereavement: "Bereavement Follow-Up",
};

function ReferralRecommendationCard({ domain, indicators, styles }) {
  const recommendation = useMemo(() => resolveReferralRecommendation(indicators), [indicators]);
  const label = REFERRAL_DOMAIN_LABELS[domain] || "Referral";

  return (
    <div style={styles.infoBox}>
      SNS Recommendation: <strong>{label} Recommended — {recommendation.recommended ? "YES" : "NO"}</strong>
      <div style={{ marginTop: 4 }}>{recommendation.reason}</div>
      <div style={{ fontSize: 12, marginTop: 6, opacity: 0.8 }}>
        This recommendation is informational only. RN judgment governs whether a referral is made; record the outcome below.
      </div>
    </div>
  );
}

const REFERRAL_REFUSED_LABELS = {
  psychosocial: "MSW",
  spiritual: "Spiritual Care",
  bereavement: "Bereavement Services",
};

// Referral Refusal record (owner requirement 2026-09-25): when SNS
// recommends a referral (YES) and the RN records Family Response =
// Refused, this materially changes RN follow-up responsibilities and must
// be captured explicitly -- who refused, their relationship to the
// patient, when, and why (optional) -- surfaced as an alert here and
// restated in the Clinical Narrative (buildClinicalNarrative). RN identity
// is captured automatically from the signed-in user, never re-typed.
function ReferralRefusalCard({ domain, recommended, familyResponse, refusal, updateField, styles, COLORS }) {
  if (!recommended || familyResponse !== "Refused") return null;
  const label = REFERRAL_REFUSED_LABELS[domain] || "Referral";

  const handleField = (field, value) => {
    updateField(`refusal.${field}`, value);
    if (!refusal?.recordedBy) {
      const currentUser = getCurrentUser();
      updateField("refusal.recordedBy", currentUser?.full_name || currentUser?.name || "");
    }
  };

  return (
    <div>
      <div style={{ ...styles.infoBox, background: "#450a0a", borderColor: "#fb7185", color: "#fecaca" }}>
        ⚠ {label} Referral Recommended — Family Refused {label}
      </div>
      <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
        <label>
          <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 4 }}>Date</div>
          <input type="date" value={refusal?.date || ""} onChange={(e) => handleField("date", e.target.value)} style={styles.input} />
        </label>
        <label>
          <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 4 }}>Person Refusing</div>
          <input type="text" value={refusal?.personRefusing || ""} onChange={(e) => handleField("personRefusing", e.target.value)} style={styles.input} placeholder="Name" />
        </label>
        <label>
          <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 4 }}>Relationship to Patient</div>
          <input type="text" value={refusal?.relationship || ""} onChange={(e) => handleField("relationship", e.target.value)} style={styles.input} placeholder="e.g. Spouse, Adult Child, POA" />
        </label>
        <label>
          <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 4 }}>Reason (optional)</div>
          <textarea value={refusal?.reason || ""} onChange={(e) => handleField("reason", e.target.value)} style={styles.textarea} />
        </label>
        {refusal?.recordedBy && (
          <div style={{ fontSize: 12, color: COLORS.gray }}>Recorded by: {refusal.recordedBy}</div>
        )}
      </div>
    </div>
  );
}

// ── Pain Summary Layer (owner review 2026-09-26, superseded 2026-09-26
// "FINAL OWNER REQUIREMENTS") ────────────────────────────────────────────
// Read-only/derived cards that consume existing Pain documentation. Never
// fabricate a value: every row either reflects an RN-entered field or is
// omitted/"Not documented". AI Pain Analysis always renders (an honest
// placeholder when nothing is grounded, so the feature is never
// invisible). Overdue Alerts renders nothing at all (no card, no
// placeholder) when no rule is triggered -- enforced by the branch-level
// hide check in the card-render loop (search for "computePainOverdueAlerts").
function SummaryRow({ label, value }) {
  if (value === undefined || value === null || value === "") return null;
  return (
    <div style={{ display: "flex", gap: 10, padding: "6px 0", borderBottom: "1px solid rgba(148, 163, 184, 0.14)" }}>
      <div style={{ flex: "0 0 40%", fontSize: 11, fontWeight: 600, color: "var(--sns-dim)" }}>{label}</div>
      <div style={{ flex: 1, fontSize: 11, color: "var(--sns-white)" }}>{value}</div>
    </div>
  );
}

const joinList = (arr) => (Array.isArray(arr) && arr.length ? arr.join(", ") : "");

// Section 15 "Clinical Summary" (formerly "Current Pain Summary"): omit
// undocumented fields entirely rather than fabricating a value or a
// default clinical statement.
function PainAssessmentSummaryCard({ data, styles }) {
  const currentPain = data?.currentPain;
  const chronicHistory = data?.chronicPainHistory;
  const rows = [];

  if (data?.screenedForPain === "0") {
    // Bug fix (2026-10-03): this used to hard-return here, hiding every
    // other documented field whenever screenedForPain === "0" — producing
    // a contradictory summary ("not assessed") on a screen that visibly
    // showed assessment data (e.g. currentPain, intensity, location
    // already filled in, perhaps from a prior screening answer that was
    // later changed). The summary must never suppress real documented
    // data; it only adds a banner, and only claims "nothing else is
    // documented" when that is actually true.
    const hasOtherPainEvidence = Boolean(
      currentPain || data?.painActiveProblem ||
      (data?.painIntensity?.current !== undefined && data?.painIntensity?.current !== "") ||
      (data?.painLocation || []).length || (data?.painCharacter || []).length ||
      data?.routinePainMedicationPresent === "1" || data?.breakthroughPainMedication === "1"
    );
    if (!hasOtherPainEvidence) {
      rows.push(<div key="not-assessed" style={styles.infoBox}>Patient was not assessed for pain. Reason: {data?.reasonNotAssessed || "Not documented"}</div>);
      return <div>{rows}</div>;
    }
    rows.push(<div key="screening-conflict" style={styles.infoBox}>Pain screening (HOPE J0900.A) is answered "No," but pain data is documented below — review for consistency before finalizing.</div>);
  }

  if (currentPain === "0") {
    // Auto-generated statement is the exact fixed sentence the field value
    // supports — it never implies current pain is present.
    rows.push(<div key="denied" style={styles.infoBox}>Pain assessed. Patient denied current pain.</div>);
  }

  rows.push(<SummaryRow key="active" label="Pain Active Problem" value={{ "1": "Yes", "0": "No", "9": "Unable to determine" }[data?.painActiveProblem] || ""} />);
  rows.push(<SummaryRow key="current-status" label="Current Pain" value={{ "1": "Yes", "0": "No / none reported", "9": "Unable to determine" }[currentPain] || ""} />);

  if (currentPain === "1") {
    rows.push(<SummaryRow key="intensity" label="Current Intensity" value={data?.painIntensity?.current !== undefined && data?.painIntensity?.current !== "" ? `${data.painIntensity.current}/10` : ""} />);
    rows.push(<SummaryRow key="worst" label="Worst Pain (24h)" value={data?.painIntensity?.worst !== undefined && data?.painIntensity?.worst !== "" ? `${data.painIntensity.worst}/10` : ""} />);
    rows.push(<SummaryRow key="location" label="Pain Location" value={joinList(data?.painLocation)} />);
    rows.push(<SummaryRow key="character" label="Pain Character" value={joinList(data?.painCharacter)} />);
    rows.push(<SummaryRow key="onset" label="Onset & Progression" value={data?.painOnsetProgression} />);
    rows.push(<SummaryRow key="duration" label="Duration & Frequency" value={data?.painDurationFrequency} />);
    rows.push(<SummaryRow key="agg" label="Aggravating Factors" value={joinList(data?.aggravatingFactors)} />);
    rows.push(<SummaryRow key="rel" label="Relieving Factors" value={joinList(data?.relievingFactors)} />);
    rows.push(<SummaryRow key="function" label="Effect on Function/QOL" value={data?.effectOnFunction} />);
  }

  rows.push(<SummaryRow key="chronic-history" label="Chronic/Recurrent Pain History" value={{ "1": "Present", "0": "None reported", "9": "Unknown", "unable": "Unable to determine" }[chronicHistory] || ""} />);

  if (currentPain === "0" && chronicHistory === "1") {
    rows.push(<SummaryRow key="condition" label="Chronic Pain Condition/Source" value={data?.chronicPainCondition} />);
    rows.push(<SummaryRow key="baseline" label="Usual Baseline Level" value={data?.usualBaselinePainLevel} />);
    rows.push(<SummaryRow key="tolerable" label="Tolerable Level" value={data?.tolerablePainLevel} />);
    rows.push(<SummaryRow key="threshold" label="Intervention Threshold" value={data?.interventionThresholdLevel} />);
    rows.push(<SummaryRow key="frequency" label="Usual Frequency/Pattern" value={data?.usualFrequencyPattern} />);
    rows.push(<SummaryRow key="approach" label="Current Management Approach" value={joinList(data?.currentManagementApproach)} />);
    rows.push(<SummaryRow key="control" label="Control Status" value={data?.controlStatus} />);
  }

  // Pain Management findings -- structured rows, each independently
  // omitted when undocumented (Current Pain Summary displays what the RN
  // documented; it is not the AI Pain Analysis, which is a separate,
  // deferred component -- see AiPainAnalysisCard below).
  rows.push(<SummaryRow key="routine-med" label="Routine Pain Medication" value={{ "1": "Yes", "0": "No", "9": "Unknown" }[data?.routinePainMedicationPresent] || ""} />);
  if (data?.routinePainMedicationPresent === "1") {
    rows.push(<SummaryRow key="med-type" label="Medication Type" value={data?.painMedicationType} />);
    rows.push(<SummaryRow key="med-route" label="Route" value={joinList(data?.painMedicationRoute)} />);
  }
  rows.push(<SummaryRow key="breakthrough-med" label="Breakthrough Pain Medication" value={{ "1": "Yes", "0": "No", "9": "Unknown" }[data?.breakthroughPainMedication] || ""} />);
  rows.push(<SummaryRow key="non-pharm" label="Non-Pharmacological Interventions" value={joinList(data?.nonPharmInterventions)} />);
  rows.push(<SummaryRow key="effectiveness" label="Effectiveness" value={data?.painEffectivenessRating} />);
  rows.push(<SummaryRow key="mgmt-notes" label="Pain Management Notes" value={data?.painManagementPlan} />);

  return <div>{rows}</div>;
}

// Deterministic rule-based analysis (not a real AI/ML call — same pattern
// as resolveReferralRecommendation): every note cites the RN-entered field
// it came from. Returns [] when there is nothing grounded to say; the
// render loop hides the card entirely in that case rather than showing an
// empty panel (owner requirement: never show an AI conclusion with no
// supporting data, never imply pain is present when denied).
function computeAiPainNotes(data) {
  const notes = [];
  const currentPain = data?.currentPain;
  const current = Number(data?.painIntensity?.current);
  const worst = Number(data?.painIntensity?.worst);
  const hasCurrent = currentPain === "1" && data?.painIntensity?.current !== undefined && data?.painIntensity?.current !== "";
  const hasWorst = currentPain === "1" && data?.painIntensity?.worst !== undefined && data?.painIntensity?.worst !== "";
  const managementDocumented = Boolean(data?.routinePainMedicationPresent === "1" || data?.breakthroughPainMedication === "1" || data?.painManagementPlan || (data?.nonPharmInterventions || []).length);

  if (hasCurrent && current >= 7 && !managementDocumented) {
    notes.push({ text: `Current pain is severe (${current}/10) with no documented pain-management intervention.`, field: "Current Pain Intensity" });
  }
  if (hasCurrent && hasWorst && worst - current >= 4) {
    notes.push({ text: `Worst pain (${worst}/10) is substantially higher than current (${current}/10) — breakthrough control may need review.`, field: "Current/Worst Pain Intensity" });
  }
  if (data?.neuropathicPain === "1") {
    notes.push({ text: "Neuropathic pain documented (HOPE J0915) — confirm an adjuvant agent is part of the pain management plan.", field: "Neuropathic Pain" });
  }
  if (data?.painEffectivenessRating && /partial|ineffective/i.test(data.painEffectivenessRating)) {
    notes.push({ text: `Pain management effectiveness documented as "${data.painEffectivenessRating}" — consider regimen reassessment.`, field: "Effectiveness Rating" });
  }
  if (data?.controlStatus === "Uncontrolled") {
    notes.push({ text: "Chronic pain control status documented as Uncontrolled.", field: "Control Status" });
  }
  if (currentPain === "0" && data?.chronicPainHistory === "1" && data?.effectOnFunction) {
    notes.push({ text: `Pain is documented as affecting function/quality of life: "${data.effectOnFunction}".`, field: "Effect on Function/QOL" });
  }
  if (currentPain === "1" && data?.effectOnFunction) {
    notes.push({ text: `Pain is documented as affecting function/quality of life: "${data.effectOnFunction}".`, field: "Effect on Function/QOL" });
  }
  if (currentPain === "1" && !hasCurrent) {
    notes.push({ text: "Patient reports current pain but current intensity has not been documented.", field: "Current Pain / Current Intensity" });
  }
  return notes;
}

function AiPainAnalysisCard({ data, styles }) {
  const notes = computeAiPainNotes(data);
  if (notes.length === 0) return <div style={styles.infoBox}>Insufficient reviewed pain data for analysis.</div>;
  return (
    <div style={styles.infoBox}>
      {notes.map((n, i) => (
        <div key={i} style={{ marginBottom: i < notes.length - 1 ? 6 : 0 }}>
          {n.text} <span style={{ opacity: 0.7, fontSize: 10 }}>(from {n.field})</span>
        </div>
      ))}
      <div style={{ fontSize: 10, marginTop: 8, opacity: 0.75 }}>AI-suggested — RN review required. Not a documented order or completed assessment.</div>
    </div>
  );
}

// Section 17: only real, currently-implemented rules — no arbitrary
// timing/deadline logic (no reassessment-overdue-by-N-days rule exists
// yet, so it is intentionally not included here).
function computePainOverdueAlerts(data, painAssessmentMode) {
  const alerts = [];
  if (!data?.screenedForPain) {
    alerts.push("Pain screening incomplete — was the patient assessed for pain? (HOPE J0900.A) has not been answered.");
    return alerts;
  }
  if (data.screenedForPain === "0" && !data?.reasonNotAssessed) {
    alerts.push("Reason pain assessment was not completed is required.");
  }
  if (data.screenedForPain === "1" && !data?.currentPain) {
    alerts.push("Current pain status (\"Is the patient experiencing pain now?\") has not been documented.");
  }
  if (data?.currentPain === "0" && !data?.chronicPainHistory) {
    alerts.push("Chronic/recurrent pain history has not been documented.");
  }
  if (data?.currentPain === "1" && !data?.comprehensiveAssessmentCompleted) {
    alerts.push("Required comprehensive pain assessment incomplete.");
  }
  if (painAssessmentMode === "painad") {
    const complete = ["breathing", "vocalization", "facialExpression", "bodyLanguage", "consolability"].every((k) => data?.painad?.[k] !== undefined && data?.painad?.[k] !== "");
    if (!complete) alerts.push("Required PAINAD Scale incomplete.");
  }
  if (painAssessmentMode === "flacc") {
    const complete = ["face", "legs", "activity", "cry", "consolability"].every((k) => data?.flacc?.[k] !== undefined && data?.flacc?.[k] !== "");
    if (!complete) alerts.push("Required FLACC Scale incomplete.");
  }
  const managementDocumented = Boolean(data?.routinePainMedicationPresent === "1" || data?.breakthroughPainMedication === "1" || data?.painManagementPlan || (data?.nonPharmInterventions || []).length);
  if (data?.currentPain === "1" && Number(data?.painIntensity?.current) >= 7 && !managementDocumented) {
    alerts.push("Current pain is severe without documented intervention.");
  }
  if (data?.breakthroughPainMedication === "1" && !data?.painEffectivenessRating) {
    alerts.push("Breakthrough pain medication documented without an effectiveness assessment.");
  }
  if (data?.painActiveProblem === "1" && !managementDocumented) {
    alerts.push("Active pain problem documented without a pain-management plan.");
  }
  return alerts;
}

function PainOverdueAlertsCard({ data, painAssessmentMode, styles }) {
  const alerts = computePainOverdueAlerts(data, painAssessmentMode);
  if (alerts.length === 0) return null;
  return (
    <div style={styles.warningBox}>
      <ul style={{ margin: 0, paddingLeft: 18 }}>
        {alerts.map((a, i) => <li key={i} style={{ marginBottom: i < alerts.length - 1 ? 4 : 0 }}>{a}</li>)}
      </ul>
    </div>
  );
}

// ── Pain Management medication harvesting (owner request 2026-09-26)
// ─────────────────────────────────────────────────────────────────────
// "Harvest existing medication information first. RN verifies. RN
// supplements. Do not force duplicate medication documentation." This
// derives suggested defaults from the patient's active medication list
// (same listMedications API/data as the Medications tab) and only ever
// pre-fills a field that the RN has not already answered — it never
// overwrites an RN correction, and the RN can always change any value.
const PAIN_OPIOID_KEYWORDS = [...CHHA_OPIOID_KEYWORDS, "percocet", "vicodin", "norco", "codeine", "tramadol", "ultram", "tapentadol", "nucynta", "buprenorphine", "butrans", "belbuca"];
const PAIN_NONOPIOID_KEYWORDS = ["acetaminophen", "tylenol", "ibuprofen", "advil", "motrin", "naproxen", "aleve", "aspirin", "celecoxib", "celebrex", "ketorolac", "toradol", "gabapentin", "neurontin", "pregabalin", "lyrica", "duloxetine", "cymbalta", "lidocaine", "lidoderm", "diclofenac", "voltaren"];
const PAIN_ROUTE_OPTIONS = ["Oral", "Patch", "Topical", "Pump", "Sublingual", "Rectal", "Other"];

// [Redesign 2026-10-03 "Nursing Assessment Flow"] Fields that only apply
// when the patient can verbally describe/report pain (painAssessmentMode
// === "verbal"). Used as a per-field render gate on the merged "Pain
// Character & Impact" card so neuropathic-pain fields on that same card
// (which are NOT verbal-only) keep showing for non-verbal/pediatric
// patients -- see the card-level comment at isPainCharacteristicsCard.
const PAIN_VERBAL_ONLY_PATHS = new Set([
  "painCharacter", "painOnsetProgression", "painDurationFrequency",
  "aggravatingFactors", "relievingFactors", "effectOnFunction",
]);

function classifyPainMedicationRoute(routeText) {
  const r = (routeText || "").toLowerCase();
  if (r.includes("patch")) return "Patch";
  if (r.includes("topical") || r.includes("cream") || r.includes("gel") || r.includes("ointment")) return "Topical";
  if (r.includes("pump") || r.includes("iv") || r.includes("infusion")) return "Pump";
  if (r.includes("sublingual") || r === "sl") return "Sublingual";
  if (r.includes("rectal") || r === "pr") return "Rectal";
  if (r.includes("oral") || r === "po") return "Oral";
  return r ? "Other" : "";
}

function isBreakthroughFrequency(frequencyText) {
  const f = (frequencyText || "").toLowerCase();
  return f.includes("prn") || f.includes("as needed") || f.includes("breakthrough");
}

// Returns null when the medication list itself hasn't loaded/isn't
// documented yet (never guess "No" from an empty/unloaded list).
function harvestPainMedications(medications) {
  if (!Array.isArray(medications)) return null;
  const active = medications.filter((m) => !m.status || m.status === "active");
  const painMeds = active.filter((m) => {
    const name = (m.medication_name || "").toLowerCase();
    return chhaTextIncludesAny(name, PAIN_OPIOID_KEYWORDS) || chhaTextIncludesAny(name, PAIN_NONOPIOID_KEYWORDS);
  });
  const hasOpioid = painMeds.some((m) => chhaTextIncludesAny((m.medication_name || "").toLowerCase(), PAIN_OPIOID_KEYWORDS));
  const hasNonOpioid = painMeds.some((m) => chhaTextIncludesAny((m.medication_name || "").toLowerCase(), PAIN_NONOPIOID_KEYWORDS));
  const routes = [...new Set(painMeds.map((m) => classifyPainMedicationRoute(m.route)).filter(Boolean))];
  const breakthrough = painMeds.some((m) => isBreakthroughFrequency(m.frequency));
  return {
    documented: active.length > 0,
    present: painMeds.length > 0,
    type: hasOpioid && hasNonOpioid ? "Both" : hasOpioid ? "Opioid" : hasNonOpioid ? "Non-Opioid" : "",
    routes,
    breakthrough,
    sourceMeds: painMeds.map((m) => `${m.medication_name}${m.route ? ` (${m.route})` : ""}${m.frequency ? ` — ${m.frequency}` : ""}`),
  };
}

function PainMedicationHarvestBanner({ patientId, data, onApply, styles, COLORS }) {
  const [meds, setMeds] = useState(null);
  const applied = useRef(false);

  useEffect(() => {
    if (!patientId) return;
    listMedications(patientId).then(setMeds).catch(() => setMeds([]));
  }, [patientId]);

  const harvest = meds ? harvestPainMedications(meds) : null;

  useEffect(() => {
    if (!harvest || applied.current) return;
    applied.current = true;
    if (!harvest.documented) return; // nothing to harvest from yet
    const patch = {};
    // Never overwrite a value the RN has already documented.
    if (data?.routinePainMedicationPresent === undefined || data?.routinePainMedicationPresent === "") {
      patch.routinePainMedicationPresent = harvest.present ? "1" : "0";
    }
    if (harvest.present && (data?.painMedicationType === undefined || data?.painMedicationType === "") && harvest.type) {
      patch.painMedicationType = harvest.type;
    }
    if (harvest.present && (!data?.painMedicationRoute || data.painMedicationRoute.length === 0) && harvest.routes.length) {
      patch.painMedicationRoute = harvest.routes;
    }
    if (harvest.present && (data?.breakthroughPainMedication === undefined || data?.breakthroughPainMedication === "")) {
      patch.breakthroughPainMedication = harvest.breakthrough ? "1" : "0";
    }
    if (Object.keys(patch).length) onApply(patch);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [harvest]);

  if (!harvest || !harvest.documented || !harvest.present) return null;
  return (
    <div style={{ ...styles.infoBox, marginBottom: 12, fontSize: 11.5 }}>
      <strong>Harvested from medication list:</strong> {harvest.sourceMeds.join("; ")}.
      Values below were pre-filled from this — verify and correct as needed.
    </div>
  );
}

const SEVERITY_COLORS = {
  CONTRAINDICATED: { bg: "#450a0a", border: "#fb7185", text: "#fecaca" },
  MAJOR: { bg: "#450a0a", border: "#fb7185", text: "#fecaca" },
  MODERATE: { bg: "#451a03", border: "#fbbf24", text: "#fde68a" },
  MINOR: { bg: "#1e293b", border: "#64748b", text: "#cbd5e1" },
  UNKNOWN: { bg: "#1e293b", border: "#64748b", text: "#cbd5e1" },
};

// Real, backend-linked allergy list — the single source of truth shared by
// the Infection section (RN ICA), the Medications card (Tx/Meds/DME), and
// the Facesheet's Structured Allergies panel (all three call the same
// listPatientAllergies/addPatientAllergy/removePatientAllergy API against
// the same patient_allergies table, so an allergy entered in any one of
// them appears in the other two immediately — no separate free-text field).
export function AllergiesCard({ patientId, styles, COLORS }) {
  const [allergies, setAllergies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [allergyForm, setAllergyForm] = useState({ allergen_text: "", severity: "", reaction_description: "" });
  const [allergyError, setAllergyError] = useState("");

  const reload = useCallback(() => {
    if (!patientId) return;
    setLoading(true);
    listPatientAllergies(patientId)
      .then((list) => setAllergies(list || []))
      .catch((err) => {
        console.error("Failed to load allergies:", err);
        setAllergyError(err?.response?.data?.detail || "Unable to load allergies.");
      })
      .finally(() => setLoading(false));
  }, [patientId]);

  useEffect(() => {
    reload();
  }, [reload]);

  const handleAddAllergy = async () => {
    if (!allergyForm.allergen_text.trim()) {
      setAllergyError("Allergen is required.");
      return;
    }
    setAllergyError("");
    try {
      await addPatientAllergy(patientId, {
        allergen_text: allergyForm.allergen_text.trim(),
        allergen_type: "DRUG",
        severity: allergyForm.severity || undefined,
        reaction_description: allergyForm.reaction_description || undefined,
      });
      setAllergyForm({ allergen_text: "", severity: "", reaction_description: "" });
      reload();
    } catch (err) {
      console.error("Add allergy failed:", err);
      setAllergyError(err?.response?.data?.detail || "Unable to add allergy.");
    }
  };

  const handleRemoveAllergy = async (allergyId) => {
    try {
      await removePatientAllergy(patientId, allergyId);
      reload();
    } catch (err) {
      console.error("Remove allergy failed:", err);
      window.alert("Unable to remove allergy.");
    }
  };

  return (
    <div>
      <div style={{ ...styles.label, marginBottom: 8 }}>Documented Allergies</div>
      {loading && <div style={{ fontSize: 12.5, color: COLORS.gray, marginBottom: 8 }}>Loading…</div>}
      {!loading && allergies.length === 0 && <div style={{ fontSize: 12.5, color: COLORS.gray, marginBottom: 8 }}>No allergies documented.</div>}
      {allergies.map((a) => (
        <div key={a.allergy_id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 0", fontSize: 12.5 }}>
          <span style={{ fontWeight: 700, color: COLORS.dark }}>{a.allergen_text}</span>
          {a.severity && <span style={{ color: COLORS.gray }}>({a.severity})</span>}
          {a.reaction_description && <span style={{ color: COLORS.gray }}>— {a.reaction_description}</span>}
          <button type="button" onClick={() => handleRemoveAllergy(a.allergy_id)} style={{ ...styles.btnSecondary, padding: "2px 8px", fontSize: 11 }}>
            Remove
          </button>
        </div>
      ))}
      <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
        <input
          style={{ ...styles.input, width: 160 }}
          placeholder="Allergen (e.g. penicillin)"
          value={allergyForm.allergen_text}
          onChange={(e) => setAllergyForm((f) => ({ ...f, allergen_text: e.target.value }))}
        />
        <select
          style={{ ...styles.select, width: 130 }}
          value={allergyForm.severity}
          onChange={(e) => setAllergyForm((f) => ({ ...f, severity: e.target.value }))}
        >
          <option value="">Severity</option>
          <option value="MILD">Mild</option>
          <option value="MODERATE">Moderate</option>
          <option value="SEVERE">Severe</option>
          <option value="ANAPHYLAXIS">Anaphylaxis</option>
        </select>
        <input
          style={{ ...styles.input, width: 180 }}
          placeholder="Reaction (optional)"
          value={allergyForm.reaction_description}
          onChange={(e) => setAllergyForm((f) => ({ ...f, reaction_description: e.target.value }))}
        />
        <button type="button" onClick={handleAddAllergy} style={{ ...styles.btnSecondary, padding: "6px 12px", fontSize: 12.5 }}>
          + Add Allergy
        </button>
      </div>
      {allergyError && <div style={{ color: COLORS.error, fontSize: 12, marginTop: 4 }}>{allergyError}</div>}
    </div>
  );
}

export function MedicationOrdersCard({ patientId, styles, COLORS }) {
  const [meds, setMeds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    medication_name: "",
    dosage: "",
    route: "",
    frequency: "",
    start_date: new Date().toISOString().slice(0, 10),
    ordering_provider_name: "",
    ordering_provider_role: "",
    source_type: "WRITTEN",
    phone_readback_confirmed: false,
  });
  const [safety, setSafety] = useState(null);
  const [safetyLoading, setSafetyLoading] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const reload = useCallback(() => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    listMedications(patientId)
      .then((medList) => setMeds(medList || []))
      .catch((err) => {
        console.error("Failed to load medications:", err);
        setError(err?.response?.data?.detail || "Unable to load medications.");
      })
      .finally(() => setLoading(false));
  }, [patientId]);

  useEffect(() => {
    reload();
  }, [reload]);

  // Live allergy + interaction check as the clinician types the medication name (debounced)
  useEffect(() => {
    if (!patientId || !form.medication_name.trim()) {
      setSafety(null);
      return;
    }
    let active = true;
    const handle = window.setTimeout(async () => {
      setSafetyLoading(true);
      try {
        const result = await checkMedicationSafety(patientId, form.medication_name.trim());
        if (active) setSafety(result);
      } catch (err) {
        console.error("Safety check failed:", err);
        if (active) setSafety(null);
      } finally {
        if (active) setSafetyLoading(false);
      }
    }, 350);
    return () => {
      active = false;
      window.clearTimeout(handle);
    };
  }, [patientId, form.medication_name]);

  const hasAlerts = (safety?.allergy_alerts?.length || 0) + (safety?.interaction_alerts?.length || 0) > 0;

  const handleAddMedication = async () => {
    if (!form.medication_name.trim() || !form.dosage.trim() || !form.route.trim() || !form.frequency.trim()) {
      setSubmitError("Medication name, dosage, route, and frequency are required.");
      return;
    }
    if (!form.ordering_provider_name.trim() || !form.ordering_provider_role) {
      setSubmitError("The prescribing physician/NP/PA's name and role are required (e.g. for telephone orders or orders given during IDG).");
      return;
    }
    if (form.source_type === "VERBAL_PHONE" && !form.phone_readback_confirmed) {
      setSubmitError("Telephone orders require a confirmed read-back before they can be submitted.");
      return;
    }
    setSubmitting(true);
    setSubmitError("");
    try {
      await addMedication(patientId, form);
      setForm({
        medication_name: "",
        dosage: "",
        route: "",
        frequency: "",
        start_date: new Date().toISOString().slice(0, 10),
        ordering_provider_name: "",
        ordering_provider_role: "",
        source_type: "WRITTEN",
        phone_readback_confirmed: false,
      });
      setSafety(null);
      reload();
    } catch (err) {
      console.error("Add medication failed:", err);
      setSubmitError(err?.response?.data?.detail || "Unable to add medication.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDiscontinue = async (medicationId) => {
    const reason = window.prompt("Reason for discontinuing (optional):", "");
    if (reason === null) return; // cancelled
    try {
      await discontinueMedication(medicationId, new Date().toISOString().slice(0, 10), reason || undefined);
      reload();
    } catch (err) {
      console.error("Discontinue failed:", err);
      window.alert(err?.response?.data?.detail || "Unable to discontinue medication.");
    }
  };

  return (
    <div>
      {/* ── Allergy list — shared component, same data as Infection section + Facesheet ── */}
      <div style={{ marginBottom: 16 }}>
        <AllergiesCard patientId={patientId} styles={styles} COLORS={COLORS} />
      </div>

      {/* ── Add medication form ── */}
      <div style={styles.fieldsGrid}>
        <div style={styles.formGroup}>
          <label style={styles.label}>Medication Name</label>
          <MedicationNameInput
            value={form.medication_name}
            onChange={(val) => setForm((f) => ({ ...f, medication_name: val }))}
            onSelectSuggestion={(s) => setForm((f) => ({
              ...f,
              dosage: s.strength || f.dosage,
              route: s.route || f.route,
            }))}
            inputStyle={styles.input}
            labelStyle={{ ...styles.label, fontSize: 11 }}
          />
        </div>
        <div style={styles.formGroup}>
          <label style={styles.label}>Dosage</label>
          <input style={styles.input} value={form.dosage} onChange={(e) => setForm((f) => ({ ...f, dosage: e.target.value }))} placeholder="e.g. 20mg" />
        </div>
        <div style={styles.formGroup}>
          <label style={styles.label}>Route</label>
          <input style={styles.input} value={form.route} onChange={(e) => setForm((f) => ({ ...f, route: e.target.value }))} placeholder="e.g. Sublingual" />
        </div>
        <div style={styles.formGroup}>
          <label style={styles.label}>Frequency</label>
          <input style={styles.input} value={form.frequency} onChange={(e) => setForm((f) => ({ ...f, frequency: e.target.value }))} placeholder="e.g. Every 4 hours PRN" />
        </div>
        <div style={styles.formGroup}>
          <label style={styles.label}>Start Date</label>
          <input type="date" style={styles.input} value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} />
        </div>
      </div>

      {/* ── Prescribing provider (required — telephone orders / IDG orders) ── */}
      <div style={{ ...styles.fieldsGrid, marginTop: 12 }}>
        <div style={styles.formGroup}>
          <label style={styles.label}>Prescribing Provider Name</label>
          <input
            style={styles.input}
            value={form.ordering_provider_name}
            onChange={(e) => setForm((f) => ({ ...f, ordering_provider_name: e.target.value }))}
            placeholder="e.g. Dr. Stephen Pine"
          />
        </div>
        <div style={styles.formGroup}>
          <label style={styles.label}>Provider Role</label>
          <select
            style={styles.select}
            value={form.ordering_provider_role}
            onChange={(e) => setForm((f) => ({ ...f, ordering_provider_role: e.target.value }))}
          >
            <option value="">Select role…</option>
            <option value="MD">MD</option>
            <option value="NP">NP</option>
            <option value="PA">PA</option>
          </select>
        </div>
        <div style={styles.formGroup}>
          <label style={styles.label}>Order Source</label>
          <select
            style={styles.select}
            value={form.source_type}
            onChange={(e) => setForm((f) => ({ ...f, source_type: e.target.value }))}
          >
            <option value="WRITTEN">Written</option>
            <option value="VERBAL_PHONE">Telephone Order</option>
            <option value="IDG">IDG</option>
            <option value="ELECTRONIC">Electronic</option>
          </select>
        </div>
        {form.source_type === "VERBAL_PHONE" && (
          <div style={{ ...styles.formGroup, display: "flex", alignItems: "flex-end" }}>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, color: COLORS.dark }}>
              <input
                type="checkbox"
                checked={form.phone_readback_confirmed}
                onChange={(e) => setForm((f) => ({ ...f, phone_readback_confirmed: e.target.checked }))}
              />
              Read-back confirmed
            </label>
          </div>
        )}
      </div>

      {/* ── Live safety alerts ── */}
      {safetyLoading && <div style={{ fontSize: 12, color: COLORS.gray, margin: "8px 0" }}>Checking allergies + interactions…</div>}
      {hasAlerts && (
        <div style={{ margin: "10px 0", display: "flex", flexDirection: "column", gap: 6 }}>
          {(safety.allergy_alerts || []).map((a, i) => {
            const c = SEVERITY_COLORS[a.severity] || SEVERITY_COLORS.UNKNOWN;
            return (
              <div key={`allergy-${i}`} style={{ padding: "8px 12px", borderRadius: 8, background: c.bg, border: `1px solid ${c.border}`, color: c.text, fontSize: 12.5 }}>
                <strong>⚠ ALLERGY ALERT ({a.severity}):</strong> Documented allergy to "{a.allergen}" {a.reaction ? `(reaction: ${a.reaction})` : ""} — {a.matched_on}.
              </div>
            );
          })}
          {(safety.interaction_alerts || []).map((a, i) => {
            const c = SEVERITY_COLORS[a.severity] || SEVERITY_COLORS.UNKNOWN;
            return (
              <div key={`interaction-${i}`} style={{ padding: "8px 12px", borderRadius: 8, background: c.bg, border: `1px solid ${c.border}`, color: c.text, fontSize: 12.5 }}>
                <strong>⚠ INTERACTION ({a.severity}) with {a.with_medication}:</strong> {a.effect} <em>Management: {a.management}</em>
              </div>
            );
          })}
        </div>
      )}

      {submitError && <div style={{ color: COLORS.error, fontSize: 12.5, margin: "6px 0" }}>{submitError}</div>}

      <button type="button" onClick={handleAddMedication} disabled={submitting} style={{ ...styles.btnPrimary, marginTop: 8 }}>
        {submitting ? "Adding…" : "+ Add Medication"}
      </button>

      {/* ── Current / historical medication list ── */}
      <div style={{ marginTop: 20 }}>
        <div style={{ ...styles.label, marginBottom: 8 }}>Medication List</div>
        {loading && <div style={{ fontSize: 12.5, color: COLORS.gray }}>Loading…</div>}
        {error && <div style={{ color: COLORS.error, fontSize: 12.5 }}>{error}</div>}
        {!loading && meds.length === 0 && <div style={{ fontSize: 12.5, color: COLORS.gray }}>No medications recorded yet.</div>}
        {meds.length > 0 && (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Medication</th>
                <th style={styles.th}>Dosage</th>
                <th style={styles.th}>Route</th>
                <th style={styles.th}>Frequency</th>
                <th style={styles.th}>Start</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Signature Status</th>
                <th style={styles.th}></th>
              </tr>
            </thead>
            <tbody>
              {meds.map((m) => (
                <tr key={m.medication_id} style={m.ui_hint?.row_color === "warning" ? { background: "rgba(245,158,11,0.08)" } : undefined}>
                  <td style={styles.td}>{m.medication_name}</td>
                  <td style={styles.td}>{m.dosage}</td>
                  <td style={styles.td}>{m.route}</td>
                  <td style={styles.td}>{m.frequency}</td>
                  <td style={styles.td}>{m.start_date}</td>
                  <td style={styles.td}>{m.status}{m.flags?.length ? ` (${m.flags.join(", ")})` : ""}</td>
                  <td style={styles.td}>
                    {m.order_status === "APPROVED" || m.order_status === "EXECUTED" ? (
                      <span style={{ color: COLORS.success, fontWeight: 600 }}>
                        ✓ Signed{m.signed_by_name ? ` — ${m.signed_by_name}` : ""}
                      </span>
                    ) : m.order_status ? (
                      <span style={{ color: COLORS.warning, fontWeight: 600 }}>⏳ Awaiting MD Signature</span>
                    ) : (
                      <span style={{ color: COLORS.gray }}>No signed order on file</span>
                    )}
                    <div style={{ fontSize: 10.5, color: COLORS.gray, marginTop: 2 }}>
                      Entered by {m.entered_by_name || "—"}
                      {m.ordered_by_provider_name ? ` · Ordered by ${m.ordered_by_provider_name} (${m.ordered_by_provider_role})` : ""}
                    </div>
                  </td>
                  <td style={styles.td}>
                    {m.status === "active" && (
                      <button type="button" onClick={() => handleDiscontinue(m.medication_id)} style={{ ...styles.btnSecondary, padding: "3px 8px", fontSize: 11 }}>
                        Discontinue
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------------
// Orders Hub — DME / Supplies / Lab / Treatment / Diet / Other + Templates + Fax
// Styled exclusively with the shared SNS Hospice Solutions dark-theme tokens
// (tenant/design.js COLORS + S) so it visually matches the rest of the app —
// no ad-hoc white/blue styling.
// ---------------------------------------------------------------------------------

const SOURCE_TYPE_LABELS = {
  WRITTEN: "Written Order",
  VERBAL_PHONE: "Verbal / Phone Order",
  ELECTRONIC: "Electronic Order",
  IDG: "IDG Meeting Order",
};
function formatSourceType(sourceType) {
  return SOURCE_TYPE_LABELS[sourceType] || (sourceType || "").replace(/_/g, " ");
}

const ORDER_TYPE_TABS = [
  { key: "MEDICATION", label: "Medication" },
  { key: "DME", label: "DME" },
  { key: "SUPPLY", label: "Supplies" },
  { key: "LAB", label: "Lab" },
  { key: "TREATMENT", label: "Treatment" },
  { key: "DIET", label: "Diet" },
  { key: "OTHER", label: "Other" },
];

const ORDER_TYPE_TO_VENDOR_TYPE = {
  MEDICATION: "Pharmacy",
  DME: "DME",
  SUPPLY: "DME",
  LAB: "Laboratory",
  TREATMENT: "Contracted Staff",
  DIET: "Other",
  OTHER: "Other",
};

// Order types whose real HospiceMD form has no drug-specific fields at all
// (no Strength/Dosage/Route/Frequency/Indication/Quantity) -- confirmed via
// real screenshots for Lab, Treatment, Other, and Supplies. DME and Diet keep
// the fuller field set (also confirmed via screenshot) and only gained
// Start Date/Stop Date, which every order type has in the real form.
const MINIMAL_ORDER_TYPES = new Set(["LAB", "TREATMENT", "OTHER", "SUPPLY"]);

// Common Orders quick-picks for the Lab tab — each is a single, independently
// selectable test (by CPT code, so labels stay in sync with the catalog).
// These are NOT bundled combos — e.g. CBC, CMP, and BMP are each their own
// button since providers often order just one, not all together.
const LAB_QUICK_PICKS = [
  { label: "UA", cpts: ["81003"] },
  { label: "UA with C&S", cpts: ["87088"] },
  { label: "CBC", cpts: ["85025"] },
  { label: "CMP", cpts: ["80053"] },
  { label: "BMP", cpts: ["80048"] },
  { label: "Liver Panel", cpts: ["80076"] },
  { label: "TSH", cpts: ["84443"] },
  { label: "Free T4", cpts: ["84439"] },
  { label: "Free T3", cpts: ["84481"] },
  { label: "BNP", cpts: ["83880"] },
  { label: "PT/INR", cpts: ["85610"] },
  { label: "A1C", cpts: ["83036"] },
];


const ohInput = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: 8,
  border: `1px solid ${SNS_COLORS.border}`,
  background: SNS_COLORS.bg,
  color: SNS_COLORS.white,
  fontSize: 13,
  outline: "none",
  boxSizing: "border-box",
};
const ohTextarea = { ...ohInput, minHeight: 60, resize: "vertical", fontFamily: "inherit" };
const ohLabel = { fontSize: 11, fontWeight: 600, color: SNS_COLORS.dim, textTransform: "uppercase", marginBottom: 4, display: "block" };
const ohFormGroup = { marginBottom: 10 };
const ohBtnPrimary = { ...SNS_S.btn(SNS_COLORS.teal) };
const ohBtnSecondary = { ...SNS_S.btnOutline, padding: "6px 12px", fontSize: 12 };

// Roles/disciplines eligible to be an ordering provider — same set used by
// StaffAssignment.jsx's "MD / NP / DO" provider group, so the Ordering
// Provider dropdown here lists the same staff (e.g. Stephen Pine, Tejon Woods).
const ORDERING_PROVIDER_ROLES = new Set(["MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "MD", "DO", "NP", "PA"]);

function providerRoleCode(staffMember) {
  const disc = (staffMember?.discipline || staffMember?.role || "").toUpperCase();
  if (disc.includes("NP")) return "NP";
  if (disc.includes("PA")) return "PA";
  return "MD";
}

const ohTabBtn = (active) => ({
  padding: "8px 16px",
  borderRadius: 8,
  border: `1px solid ${active ? SNS_COLORS.teal : SNS_COLORS.border}`,
  background: active ? "rgba(99, 231, 211, 0.14)" : "transparent",
  color: active ? SNS_COLORS.teal : SNS_COLORS.muted,
  fontSize: 12.5,
  fontWeight: 700,
  cursor: "pointer",
});

// Maps the backend-agnostic status tone (physicianOrders.ts) onto this
// surface's local SNS design tokens. The tone→severity mapping itself lives
// in physicianOrders.ts (shared with PhysicianOrdersBoard.jsx) so the two
// order-status surfaces cannot silently drift out of sync.
const OH_TONE_COLORS = {
  neutral: SNS_COLORS.muted,
  warning: SNS_COLORS.orange,
  info: SNS_COLORS.blue,
  success: SNS_COLORS.green,
  danger: SNS_COLORS.red,
};

export function OrdersHubCard({ patientId }) {
  const currentUser = getCurrentUser();
  // Any role the backend accepts as an order signer (not just legacy "MD")
  // must see the Approve/Countersign actions -- see ORDER_SIGNER_ROLES.
  const canSignOrders = ORDER_SIGNER_ROLES.includes(currentUser?.role);

  const [activeType, setActiveType] = useState("DME");
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [busyOrderId, setBusyOrderId] = useState(null);

  const [templates, setTemplates] = useState([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [importing, setImporting] = useState(false);
  const [importMessage, setImportMessage] = useState("");
  const [importAttestation, setImportAttestation] = useState({
    ordered_by_provider_name: "", ordered_by_provider_role: "MD",
    source_type: "WRITTEN", prescriber_authenticated: false, phone_readback_confirmed: false,
  });

  const [form, setForm] = useState({
    order_text: "", strength: "", dosage: "", route: "", frequency: "",
    indication: "", quantity: "", payer: "", vendor: "", administered_by: "",
    special_instruction: "",
    start_date: new Date().toISOString().slice(0, 10), stop_date: "",
    source_type: "WRITTEN", ordered_by_provider_name: "", ordered_by_provider_role: "MD",
    prescriber_authenticated: false, phone_readback_confirmed: false,
    visit_frequency_discipline: "", visit_frequency_per_week: "", visit_frequency_prn_count: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const [labCatalog, setLabCatalog] = useState(null);
  const [selectedLabTests, setSelectedLabTests] = useState([]);
  const [labSearch, setLabSearch] = useState("");

  const [vendorOptions, setVendorOptions] = useState([]);
  const [providerOptions, setProviderOptions] = useState([]);

  useEffect(() => {
    listStaff({ status: "active" })
      .then((list) => setProviderOptions((list || []).filter((s) => ORDERING_PROVIDER_ROLES.has((s.discipline || s.role || "").toUpperCase()))))
      .catch((err) => console.error("Failed to load providers:", err));
  }, []);

  const [faxOpen, setFaxOpen] = useState(false);
  const [faxForm, setFaxForm] = useState({ recipient_name: "", recipient_fax_number: "" });
  const [faxHistory, setFaxHistory] = useState([]);
  const [faxSending, setFaxSending] = useState(false);
  const [faxError, setFaxError] = useState("");

  const reload = useCallback(() => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    listPhysicianOrders(patientId, undefined, activeType)
      .then((list) => setOrders(list || []))
      .catch((err) => {
        console.error("Failed to load orders:", err);
        setError(err?.response?.data?.detail || "Unable to load orders.");
      })
      .finally(() => setLoading(false));
  }, [patientId, activeType]);

  useEffect(() => { reload(); }, [reload]);

  useEffect(() => {
    listOrderTemplates()
      .then((list) => setTemplates(list || []))
      .catch((err) => console.error("Failed to load order templates:", err));
  }, []);

  useEffect(() => {
    if (activeType === "LAB" && !labCatalog) {
      getLabCatalog()
        .then(setLabCatalog)
        .catch((err) => console.error("Failed to load lab catalog:", err));
    }
  }, [activeType, labCatalog]);

  useEffect(() => {
    const vendorType = ORDER_TYPE_TO_VENDOR_TYPE[activeType] || "Other";
    listVendors({ status: "active", vendor_type: vendorType })
      .then((list) => setVendorOptions(list || []))
      .catch((err) => console.error("Failed to load vendors:", err));
  }, [activeType]);

  const handleImportPack = async () => {
    if (!selectedTemplateId) return;
    if (!importAttestation.ordered_by_provider_name.trim()) {
      setImportMessage("Ordering provider name is required — every imported order must be attributable to a physician for signature, same as a manually-entered order.");
      return;
    }
    if (!importAttestation.prescriber_authenticated) {
      setImportMessage("Please confirm prescriber identity authentication before importing.");
      return;
    }
    if (importAttestation.source_type === "VERBAL_PHONE" && !importAttestation.phone_readback_confirmed) {
      setImportMessage("Phone read-back confirmation is required for telephone-ordered packs.");
      return;
    }
    setImporting(true);
    setImportMessage("");
    try {
      const result = await importOrderTemplate(selectedTemplateId, patientId, importAttestation);
      const allergyHits = (result.medications_created || []).filter((m) => (m.allergy_alerts || []).length > 0);
      const interactionHits = (result.medications_created || []).filter((m) => (m.interaction_alerts || []).length > 0);
      let msg = `Imported "${result.template_name}" — ${result.total_imported} orders added, each pending MD signature (or immediate execution if a verbal/read-back-confirmed order).`;
      if (allergyHits.length > 0) {
        const detail = allergyHits
          .map((m) => `${m.medication_name}: ${m.allergy_alerts.map((a) => `${a.allergen} (${a.severity})`).join(", ")}`)
          .join(" | ");
        msg += ` ⚠ ALLERGY ALERT — ${detail}`;
      }
      if (interactionHits.length > 0) {
        const detail = interactionHits
          .map((m) => `${m.medication_name}: ${m.interaction_alerts.map((a) => `${a.with_medication} (${a.severity})`).join(", ")}`)
          .join(" | ");
        msg += ` ⚠ INTERACTION ALERT — ${detail}`;
      }
      setImportMessage(msg);
      reload();
    } catch (err) {
      console.error("Import pack failed:", err);
      setImportMessage(err?.response?.data?.detail || "Unable to import pack.");
    } finally {
      setImporting(false);
    }
  };

  const toggleLabTest = (test) => {
    setSelectedLabTests((prev) =>
      prev.some((t) => t.cpt === test.cpt) ? prev.filter((t) => t.cpt !== test.cpt) : [...prev, test]
    );
  };

  const findLabTest = useCallback(
    (cpt) => {
      for (const cat of labCatalog?.categories || []) {
        const found = cat.tests.find((t) => t.cpt === cpt);
        if (found) return found;
      }
      return null;
    },
    [labCatalog]
  );

  const toggleLabQuickPick = (pick) => {
    const tests = pick.cpts.map(findLabTest).filter(Boolean);
    if (!tests.length) return;
    const allSelected = tests.every((test) => selectedLabTests.some((t) => t.cpt === test.cpt));
    setSelectedLabTests((prev) =>
      allSelected
        ? prev.filter((t) => !tests.some((test) => test.cpt === t.cpt))
        : [...prev, ...tests.filter((test) => !prev.some((t) => t.cpt === test.cpt))]
    );
  };

  const labSearchHasNoMatches = useMemo(() => {
    if (!labCatalog || !labSearch.trim()) return false;
    const query = labSearch.trim().toLowerCase();
    return !labCatalog.categories?.some((cat) =>
      cat.tests.some((test) => test.name.toLowerCase().includes(query) || test.cpt.toLowerCase().includes(query))
    );
  }, [labCatalog, labSearch]);

  const handleAddOrder = async () => {
    const freqDiscipline = activeType === "OTHER" ? form.visit_frequency_discipline : "";
    const freqPerWeek = freqDiscipline && form.visit_frequency_per_week !== "" ? parseInt(form.visit_frequency_per_week, 10) : null;
    const freqPrnCount = freqDiscipline && form.visit_frequency_prn_count !== "" ? parseInt(form.visit_frequency_prn_count, 10) : null;
    const freqSummaryParts = [];
    if (freqDiscipline) {
      if (freqPerWeek) freqSummaryParts.push(`${freqPerWeek}x/week`);
      if (freqPrnCount) freqSummaryParts.push(`PRN x${freqPrnCount}`);
    }
    const orderText = [
      activeType === "LAB"
        ? selectedLabTests.map((t) => `${t.name} (CPT ${t.cpt})`).join("; ")
        : form.order_text,
      !MINIMAL_ORDER_TYPES.has(activeType) && form.strength && `Strength: ${form.strength}`,
      !MINIMAL_ORDER_TYPES.has(activeType) && form.dosage && `Dosage/Qty: ${form.dosage}`,
      !MINIMAL_ORDER_TYPES.has(activeType) && form.route && `Route: ${form.route}`,
      !MINIMAL_ORDER_TYPES.has(activeType) && form.frequency && `Frequency: ${form.frequency}`,
      !MINIMAL_ORDER_TYPES.has(activeType) && form.indication && `Indication: ${form.indication}`,
      freqDiscipline && `Visit Frequency: ${freqDiscipline} ${freqSummaryParts.join(", ")}`.trim(),
      form.payer && `Payer: ${form.payer}`,
      form.vendor && `Vendor: ${form.vendor}`,
      form.administered_by && `Administered by: ${form.administered_by}`,
      form.start_date && `Start Date: ${form.start_date}`,
      form.stop_date && `Stop Date: ${form.stop_date}`,
      form.special_instruction && `Instructions: ${form.special_instruction}`,
    ].filter(Boolean).join(" — ");

    if (!orderText.trim()) {
      setSubmitError(activeType === "LAB" ? "Select at least one lab test." : "Order text is required.");
      return;
    }
    if (!form.ordered_by_provider_name.trim()) {
      setSubmitError("Ordering provider name is required — every order must be attributable to a physician for signature.");
      return;
    }
    if (form.source_type === "VERBAL_PHONE" && !form.phone_readback_confirmed) {
      setSubmitError("Phone read-back confirmation is required for telephone orders.");
      return;
    }
    setSubmitting(true);
    setSubmitError("");
    try {
      const draft = await createPhysicianOrder(patientId, {
        order_text: orderText.trim(),
        order_category: activeType,
        source_type: form.source_type,
        ordered_by_provider_name: form.ordered_by_provider_name,
        ordered_by_provider_role: form.ordered_by_provider_role,
        prescriber_authenticated: form.prescriber_authenticated,
        phone_readback_confirmed: form.phone_readback_confirmed,
        ordered_at: new Date().toISOString(),
        visit_frequency_discipline: freqDiscipline || null,
        visit_frequency_per_week: freqPerWeek,
        visit_frequency_prn_count: freqPrnCount,
      });
      await submitPhysicianOrder(draft.id);
      setForm({
        order_text: "", strength: "", dosage: "", route: "", frequency: "", indication: "",
        quantity: "", payer: "", vendor: "", administered_by: "", special_instruction: "",
        start_date: new Date().toISOString().slice(0, 10), stop_date: "",
        source_type: "WRITTEN", ordered_by_provider_name: "", ordered_by_provider_role: "MD",
        prescriber_authenticated: false, phone_readback_confirmed: false,
        visit_frequency_discipline: "", visit_frequency_per_week: "", visit_frequency_prn_count: "",
      });
      setSelectedLabTests([]);
      reload();
    } catch (err) {
      console.error("Add order failed:", err);
      setSubmitError(err?.response?.data?.detail || "Unable to add order.");
    } finally {
      setSubmitting(false);
    }
  };

  const runOrderAction = async (orderId, fn) => {
    setBusyOrderId(orderId);
    setActionError("");
    try {
      await fn(orderId);
      reload();
    } catch (err) {
      console.error("Order action failed:", err);
      setActionError(err?.response?.data?.detail || "Action failed.");
    } finally {
      setBusyOrderId(null);
    }
  };

  const openFax = () => {
    setFaxOpen(true);
    setFaxError("");
    getFaxHistory(patientId).then(setFaxHistory).catch((err) => console.error("Fax history failed:", err));
  };

  const handleSendFax = async () => {
    if (!faxForm.recipient_name.trim() || !faxForm.recipient_fax_number.trim()) {
      setFaxError("Recipient name and fax number are required.");
      return;
    }
    setFaxSending(true);
    setFaxError("");
    try {
      const summary = orders
        .filter((o) => o.status === "APPROVED" || o.status === "EXECUTED")
        .map((o) => `${o.order_category}: ${o.order_text}`)
        .join("\n") || `${activeType} orders for patient`;
      await sendFax(patientId, {
        subject_type: "ORDER_SET",
        recipient_name: faxForm.recipient_name.trim(),
        recipient_fax_number: faxForm.recipient_fax_number.trim(),
        document_summary: summary,
      });
      setFaxForm({ recipient_name: "", recipient_fax_number: "" });
      const history = await getFaxHistory(patientId);
      setFaxHistory(history);
    } catch (err) {
      console.error("Send fax failed:", err);
      setFaxError(err?.response?.data?.detail || "Unable to send fax.");
    } finally {
      setFaxSending(false);
    }
  };

  return (
    <div>
      {/* ── Template picker / Import Pack ── */}
      <div style={{ ...SNS_S.card, padding: 16, marginBottom: 16, background: SNS_COLORS.bg }}>
        <div style={ohLabel}>Order-Set Templates</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <select
            style={{ ...SNS_S.select, minWidth: 240 }}
            value={selectedTemplateId}
            onChange={(e) => setSelectedTemplateId(e.target.value)}
          >
            <option value="">Select a pack…</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name} ({t.item_count} items){t.is_system ? " — System" : ""}
              </option>
            ))}
          </select>
          <button type="button" style={ohBtnPrimary} disabled={!selectedTemplateId || importing} onClick={handleImportPack}>
            {importing ? "Importing…" : "Import Pack"}
          </button>
          <button type="button" style={ohBtnSecondary} onClick={openFax}>
            📠 Fax Orders
          </button>
        </div>
        {selectedTemplateId && (
          <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px solid ${SNS_COLORS.border}` }}>
            <div style={{ fontSize: 10.5, fontWeight: 700, color: SNS_COLORS.orange, textTransform: "uppercase", marginBottom: 6 }}>
              Ordering Provider (required — same attestation as a manual order)
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 8 }}>
              <input
                style={ohInput}
                value={importAttestation.ordered_by_provider_name}
                onChange={(e) => {
                  const name = e.target.value;
                  const match = providerOptions.find((p) => p.full_name === name);
                  setImportAttestation((f) => ({
                    ...f,
                    ordered_by_provider_name: name,
                    ordered_by_provider_role: match ? providerRoleCode(match) : f.ordered_by_provider_role,
                  }));
                }}
                list="oh-provider-options"
                placeholder={providerOptions.length ? "Select or type a provider…" : "Dr. Jane Smith"}
              />
              <select style={ohInput} value={importAttestation.ordered_by_provider_role} onChange={(e) => setImportAttestation((f) => ({ ...f, ordered_by_provider_role: e.target.value }))}>
                <option value="MD">MD</option>
                <option value="NP">NP</option>
                <option value="PA">PA</option>
              </select>
              <select style={ohInput} value={importAttestation.source_type} onChange={(e) => setImportAttestation((f) => ({ ...f, source_type: e.target.value }))}>
                <option value="WRITTEN">Written</option>
                <option value="VERBAL_PHONE">Telephone Order</option>
                <option value="ELECTRONIC">Electronic</option>
                <option value="IDG">IDG (discussed &amp; ordered during IDG meeting)</option>
              </select>
            </div>
            <div style={{ display: "flex", gap: 18, marginTop: 8 }}>
              <label style={{ fontSize: 12, color: SNS_COLORS.muted, display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
                <input type="checkbox" checked={importAttestation.prescriber_authenticated} onChange={(e) => setImportAttestation((f) => ({ ...f, prescriber_authenticated: e.target.checked }))} />
                Prescriber identity authenticated
              </label>
              {importAttestation.source_type === "VERBAL_PHONE" && (
                <label style={{ fontSize: 12, color: SNS_COLORS.muted, display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
                  <input type="checkbox" checked={importAttestation.phone_readback_confirmed} onChange={(e) => setImportAttestation((f) => ({ ...f, phone_readback_confirmed: e.target.checked }))} />
                  Telephone read-back confirmed
                </label>
              )}
            </div>
          </div>
        )}
        {importMessage && (
          <div style={{ fontSize: 12.5, color: importMessage.includes("⚠") ? SNS_COLORS.red : SNS_COLORS.teal, marginTop: 8, fontWeight: importMessage.includes("⚠") ? 700 : 400 }}>
            {importMessage}
          </div>
        )}
      </div>

      {/* ── Order type tabs ── */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {ORDER_TYPE_TABS.map((t) => (
          <button key={t.key} type="button" style={ohTabBtn(activeType === t.key)} onClick={() => setActiveType(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Add order form ── */}
      <div style={{ ...SNS_S.card, padding: 16, marginBottom: 16, background: SNS_COLORS.bg }}>
        {activeType === "LAB" ? (
          <div>
            <div style={ohLabel}>Lab Tests (select all that apply)</div>
            {!labCatalog && <div style={{ fontSize: 12.5, color: SNS_COLORS.dim }}>Loading catalog…</div>}
            {labCatalog ? (
              <div style={{ marginBottom: 12 }}>
                <div style={{ ...ohLabel, marginBottom: 6 }}>Common Orders</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {LAB_QUICK_PICKS.map((pick) => {
                    const tests = pick.cpts.map(findLabTest).filter(Boolean);
                    const active = tests.length > 0 && tests.every((test) => selectedLabTests.some((t) => t.cpt === test.cpt));
                    return (
                      <button
                        key={pick.label}
                        type="button"
                        onClick={() => toggleLabQuickPick(pick)}
                        style={{
                          padding: "5px 10px",
                          borderRadius: 999,
                          border: `1px solid ${active ? SNS_COLORS.teal : SNS_COLORS.border}`,
                          background: active ? SNS_COLORS.teal : "transparent",
                          color: active ? SNS_COLORS.bg : SNS_COLORS.white,
                          fontSize: 11.5,
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        {pick.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : null}
            {labCatalog ? (
              <input
                style={{ ...ohInput, marginBottom: 12, maxWidth: 320 }}
                value={labSearch}
                onChange={(e) => setLabSearch(e.target.value)}
                placeholder="Search by test name or CPT code…"
              />
            ) : null}
            {selectedLabTests.length > 0 && (
              <div style={{ fontSize: 11.5, color: SNS_COLORS.teal, marginBottom: 8 }}>
                {selectedLabTests.length} test{selectedLabTests.length === 1 ? "" : "s"} selected: {selectedLabTests.map((t) => t.name).join(", ")}
              </div>
            )}
            {labCatalog?.categories?.map((cat) => {
              const query = labSearch.trim().toLowerCase();
              const visibleTests = query
                ? cat.tests.filter((test) => test.name.toLowerCase().includes(query) || test.cpt.toLowerCase().includes(query))
                : cat.tests;
              if (!visibleTests.length) return null;
              return (
                <div key={cat.category} style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: SNS_COLORS.muted, marginBottom: 4 }}>{cat.category}</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 16px" }}>
                    {visibleTests.map((test) => (
                      <label key={test.cpt + test.name} style={{ fontSize: 12, color: SNS_COLORS.white, display: "flex", alignItems: "center", gap: 4, cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={selectedLabTests.some((t) => t.cpt === test.cpt)}
                          onChange={() => toggleLabTest(test)}
                        />
                        {test.name} <span style={{ color: SNS_COLORS.dim }}>(CPT {test.cpt})</span>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
            {labCatalog && labSearchHasNoMatches ? (
              <div style={{ fontSize: 12, color: SNS_COLORS.dim }}>No lab tests match "{labSearch}".</div>
            ) : null}
            {labCatalog?.clinical_notes && Object.values(labCatalog.clinical_notes).map((note, i) => (
              <div key={i} style={{ fontSize: 11.5, color: SNS_COLORS.orange, marginTop: 8, fontStyle: "italic" }}>{note}</div>
            ))}
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 }}>
            <div style={ohFormGroup}>
              <label style={ohLabel}>{activeType === "MEDICATION" ? "Medication Name" : "Order"}</label>
              {activeType === "MEDICATION" ? (
                <MedicationNameInput
                  value={form.order_text}
                  onChange={(val) => setForm((f) => ({ ...f, order_text: val }))}
                  onSelectSuggestion={(s) => setForm((f) => ({
                    ...f,
                    strength: s.strength || f.strength,
                    route: s.route || f.route,
                  }))}
                  inputStyle={ohInput}
                  labelStyle={{ fontSize: 10.5, color: SNS_COLORS.dim }}
                />
              ) : (
                <input style={ohInput} value={form.order_text} onChange={(e) => setForm((f) => ({ ...f, order_text: e.target.value }))} placeholder="e.g. Hospital Bed Full Electric" />
              )}
            </div>
            {!MINIMAL_ORDER_TYPES.has(activeType) && (
              <>
                <div style={ohFormGroup}>
                  <label style={ohLabel}>Strength</label>
                  <input style={ohInput} value={form.strength} onChange={(e) => setForm((f) => ({ ...f, strength: e.target.value }))} />
                </div>
                <div style={ohFormGroup}>
                  <label style={ohLabel}>Dosage/Qty</label>
                  <input style={ohInput} value={form.dosage} onChange={(e) => setForm((f) => ({ ...f, dosage: e.target.value }))} />
                </div>
                <div style={ohFormGroup}>
                  <label style={ohLabel}>Route</label>
                  <input style={ohInput} value={form.route} onChange={(e) => setForm((f) => ({ ...f, route: e.target.value }))} />
                </div>
                <div style={ohFormGroup}>
                  <label style={ohLabel}>Frequency</label>
                  <input style={ohInput} value={form.frequency} onChange={(e) => setForm((f) => ({ ...f, frequency: e.target.value }))} />
                </div>
                <div style={ohFormGroup}>
                  <label style={ohLabel}>Indication</label>
                  <input style={ohInput} value={form.indication} onChange={(e) => setForm((f) => ({ ...f, indication: e.target.value }))} />
                </div>
              </>
            )}
            <div style={ohFormGroup}>
              <label style={ohLabel}>Payer</label>
              <select style={ohInput} value={form.payer} onChange={(e) => setForm((f) => ({ ...f, payer: e.target.value }))}>
                <option value="">—</option>
                <option value="Hospice">Hospice covered</option>
                <option value="Insurance">Insurance non-covered</option>
                <option value="Patient">Patient non-covered</option>
              </select>
            </div>
            <div style={ohFormGroup}>
              <label style={ohLabel}>Vendor</label>
              <input
                style={ohInput}
                value={form.vendor}
                onChange={(e) => setForm((f) => ({ ...f, vendor: e.target.value }))}
                list="oh-vendor-options"
                placeholder={vendorOptions.length ? "Select or type a vendor…" : "No vendors on file — type a name"}
              />
              <datalist id="oh-vendor-options">
                {vendorOptions.map((v) => (
                  <option key={v.id} value={v.name} />
                ))}
              </datalist>
              <div style={{ fontSize: 10.5, color: SNS_COLORS.dim, marginTop: 3 }}>
                Add/edit vendors from Agency Settings → Vendors.
              </div>
            </div>
            <div style={ohFormGroup}>
              <label style={ohLabel}>Administered By</label>
              <input style={ohInput} value={form.administered_by} onChange={(e) => setForm((f) => ({ ...f, administered_by: e.target.value }))} placeholder="e.g. Hospice Nurse Only" />
            </div>
            {activeType === "OTHER" && (
              <>
                <div style={ohFormGroup}>
                  <label style={ohLabel}>Visit Frequency — Discipline</label>
                  <select
                    style={ohInput}
                    value={form.visit_frequency_discipline}
                    onChange={(e) => setForm((f) => ({ ...f, visit_frequency_discipline: e.target.value }))}
                  >
                    <option value="">— Not a frequency order —</option>
                    <option value="RN">RN (Skilled Nursing)</option>
                    <option value="LVN">LVN/LPN</option>
                    <option value="CHHA">CHHA (Home Health Aide)</option>
                    <option value="MSW">MSW (Social Work)</option>
                    <option value="SC">Chaplain / Spiritual Care</option>
                  </select>
                  <div style={{ fontSize: 10.5, color: SNS_COLORS.dim, marginTop: 3 }}>
                    Set this to record a structured "visits per week" order the scheduling engine can track. Leave blank for a non-frequency Other order.
                  </div>
                </div>
                {form.visit_frequency_discipline && (
                  <>
                    <div style={ohFormGroup}>
                      <label style={ohLabel}>Visits per Week</label>
                      <input
                        type="number"
                        min="0"
                        style={ohInput}
                        value={form.visit_frequency_per_week}
                        onChange={(e) => setForm((f) => ({ ...f, visit_frequency_per_week: e.target.value }))}
                        placeholder="e.g. 2"
                      />
                    </div>
                    <div style={ohFormGroup}>
                      <label style={ohLabel}>PRN Visits (count)</label>
                      <input
                        type="number"
                        min="0"
                        style={ohInput}
                        value={form.visit_frequency_prn_count}
                        onChange={(e) => setForm((f) => ({ ...f, visit_frequency_prn_count: e.target.value }))}
                        placeholder="e.g. 1"
                      />
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        )}
        {activeType === "LAB" && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10, marginTop: 10 }}>
            <div style={ohFormGroup}>
              <label style={ohLabel}>Payer</label>
              <select style={ohInput} value={form.payer} onChange={(e) => setForm((f) => ({ ...f, payer: e.target.value }))}>
                <option value="">—</option>
                <option value="Hospice">Hospice covered</option>
                <option value="Insurance">Insurance non-covered</option>
                <option value="Patient">Patient non-covered</option>
              </select>
            </div>
            <div style={ohFormGroup}>
              <label style={ohLabel}>Vendor</label>
              <input
                style={ohInput}
                value={form.vendor}
                onChange={(e) => setForm((f) => ({ ...f, vendor: e.target.value }))}
                list="oh-vendor-options"
                placeholder={vendorOptions.length ? "Select or type a vendor…" : "No vendors on file — type a name"}
              />
              <datalist id="oh-vendor-options">
                {vendorOptions.map((v) => (
                  <option key={v.id} value={v.name} />
                ))}
              </datalist>
            </div>
            <div style={ohFormGroup}>
              <label style={ohLabel}>Administered By</label>
              <input style={ohInput} value={form.administered_by} onChange={(e) => setForm((f) => ({ ...f, administered_by: e.target.value }))} placeholder="e.g. Outside Lab" />
            </div>
          </div>
        )}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10, marginTop: 10 }}>
          <div style={ohFormGroup}>
            <label style={ohLabel}>Start Date</label>
            <input type="date" style={ohInput} value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} />
          </div>
          <div style={ohFormGroup}>
            <label style={ohLabel}>Stop Date</label>
            <input type="date" style={ohInput} value={form.stop_date} onChange={(e) => setForm((f) => ({ ...f, stop_date: e.target.value }))} />
          </div>
        </div>
        <div style={ohFormGroup}>
          <label style={ohLabel}>Special Instruction</label>
          <textarea style={ohTextarea} value={form.special_instruction} onChange={(e) => setForm((f) => ({ ...f, special_instruction: e.target.value }))} />
        </div>

        <div style={{ borderTop: `1px solid ${SNS_COLORS.border}`, marginTop: 6, paddingTop: 10 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: SNS_COLORS.orange, textTransform: "uppercase", marginBottom: 8 }}>
            Physician Sign-Off (required for all orders)
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 }}>
            <div style={ohFormGroup}>
              <label style={ohLabel}>Ordering Provider Name</label>
              <input
                style={ohInput}
                value={form.ordered_by_provider_name}
                onChange={(e) => {
                  const name = e.target.value;
                  const match = providerOptions.find((p) => p.full_name === name);
                  setForm((f) => ({
                    ...f,
                    ordered_by_provider_name: name,
                    ordered_by_provider_role: match ? providerRoleCode(match) : f.ordered_by_provider_role,
                  }));
                }}
                list="oh-provider-options"
                placeholder={providerOptions.length ? "Select or type a provider…" : "Dr. Jane Smith"}
              />
              <datalist id="oh-provider-options">
                {providerOptions.map((p) => (
                  <option key={p.id} value={p.full_name} />
                ))}
              </datalist>
            </div>
            <div style={ohFormGroup}>
              <label style={ohLabel}>Provider Role</label>
              <select style={ohInput} value={form.ordered_by_provider_role} onChange={(e) => setForm((f) => ({ ...f, ordered_by_provider_role: e.target.value }))}>
                <option value="MD">MD</option>
                <option value="NP">NP</option>
                <option value="PA">PA</option>
              </select>
            </div>
            <div style={ohFormGroup}>
              <label style={ohLabel}>Order Source</label>
              <select style={ohInput} value={form.source_type} onChange={(e) => setForm((f) => ({ ...f, source_type: e.target.value }))}>
                <option value="WRITTEN">Written</option>
                <option value="VERBAL_PHONE">Telephone Order</option>
                <option value="ELECTRONIC">Electronic</option>
                <option value="IDG">IDG (discussed &amp; ordered during IDG meeting)</option>
              </select>
            </div>
          </div>
          <div style={{ display: "flex", gap: 18, marginTop: 8 }}>
            <label style={{ fontSize: 12.5, color: SNS_COLORS.muted, display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
              <input type="checkbox" checked={form.prescriber_authenticated} onChange={(e) => setForm((f) => ({ ...f, prescriber_authenticated: e.target.checked }))} />
              Prescriber identity authenticated
            </label>
            {form.source_type === "VERBAL_PHONE" && (
              <label style={{ fontSize: 12.5, color: SNS_COLORS.muted, display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
                <input type="checkbox" checked={form.phone_readback_confirmed} onChange={(e) => setForm((f) => ({ ...f, phone_readback_confirmed: e.target.checked }))} />
                Telephone read-back confirmed
              </label>
            )}
          </div>
        </div>

        {submitError && <div style={{ color: SNS_COLORS.red, fontSize: 12.5, marginTop: 10, marginBottom: 8 }}>{submitError}</div>}
        <button type="button" style={{ ...ohBtnPrimary, marginTop: 10 }} disabled={submitting} onClick={handleAddOrder}>
          {submitting ? "Submitting…" : `Submit ${ORDER_TYPE_TABS.find((t) => t.key === activeType)?.label || ""} Order for MD Signature`}
        </button>
      </div>

      {/* ── Orders list ── */}
      <div>
        <div style={ohLabel}>{ORDER_TYPE_TABS.find((t) => t.key === activeType)?.label} Orders</div>
        {loading && <div style={{ fontSize: 12.5, color: SNS_COLORS.dim }}>Loading…</div>}
        {error && <div style={{ color: SNS_COLORS.red, fontSize: 12.5 }}>{error}</div>}
        {actionError && <div style={{ color: SNS_COLORS.red, fontSize: 12.5, marginBottom: 8 }}>{actionError}</div>}
        {!loading && orders.length === 0 && <div style={{ fontSize: 12.5, color: SNS_COLORS.dim }}>No {activeType.toLowerCase()} orders recorded yet.</div>}
        {orders.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {orders.map((o) => (
              <div key={o.id} style={{ border: `1px solid ${SNS_COLORS.border}`, borderRadius: 8, padding: 10, display: "flex", flexDirection: "column", gap: 6 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div style={{ fontSize: 13, color: SNS_COLORS.white, fontWeight: 600, maxWidth: "70%" }}>{o.order_text}</div>
                  <span style={{
                    fontSize: 10, fontWeight: 700, borderRadius: 6, padding: "2px 8px", textTransform: "uppercase",
                    border: `1px solid ${o.awaiting_countersignature ? SNS_COLORS.orange : OH_TONE_COLORS[getPhysicianOrderStatusTone(o.status)]}`,
                    color: o.awaiting_countersignature ? SNS_COLORS.orange : OH_TONE_COLORS[getPhysicianOrderStatusTone(o.status)],
                  }}>
                    {o.awaiting_countersignature ? "Administered — Awaiting Countersignature" : formatPhysicianOrderStatusLabel(o.status, o.status_label)}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: SNS_COLORS.dim }}>
                  {o.ordered_by_provider_name} ({o.ordered_by_provider_role}) · {formatSourceType(o.source_type)} · {o.ordered_at ? new Date(o.ordered_at).toLocaleString() : "—"}
                </div>
                {o.signed_at && (
                  <div style={{ fontSize: 11, color: SNS_COLORS.blue }}>Signed {new Date(o.signed_at).toLocaleString()} ({o.signature_method})</div>
                )}
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  {o.status === "PENDING_HOSPICE_MD_APPROVAL" && o.source_type === "VERBAL_PHONE" && o.phone_readback_confirmed && (
                    <button type="button" style={{ ...ohBtnSecondary, borderColor: SNS_COLORS.teal, color: SNS_COLORS.teal }} disabled={busyOrderId === o.id} onClick={() => runOrderAction(o.id, executePhysicianOrder)}>
                      Administer Now (Verbal Order)
                    </button>
                  )}
                  {o.status === "PENDING_HOSPICE_MD_APPROVAL" && canSignOrders && (
                    <button type="button" style={ohBtnSecondary} disabled={busyOrderId === o.id} onClick={() => runOrderAction(o.id, approvePhysicianOrder)}>
                      Approve &amp; Sign
                    </button>
                  )}
                  {o.status === "PENDING_HOSPICE_MD_APPROVAL" && !canSignOrders && !(o.source_type === "VERBAL_PHONE" && o.phone_readback_confirmed) && (
                    <span style={{ fontSize: 11, color: SNS_COLORS.orange }}>Awaiting Medical Director signature</span>
                  )}
                  {o.status === "APPROVED" && (
                    <button type="button" style={ohBtnSecondary} disabled={busyOrderId === o.id} onClick={() => runOrderAction(o.id, executePhysicianOrder)}>
                      Mark Executed
                    </button>
                  )}
                  {o.status === "EXECUTED" && o.awaiting_countersignature && canSignOrders && (
                    <button type="button" style={{ ...ohBtnSecondary, borderColor: SNS_COLORS.blue, color: SNS_COLORS.blue }} disabled={busyOrderId === o.id} onClick={() => runOrderAction(o.id, approvePhysicianOrder)}>
                      Countersign
                    </button>
                  )}
                  {o.status === "EXECUTED" && o.awaiting_countersignature && !canSignOrders && (
                    <span style={{ fontSize: 11, color: SNS_COLORS.orange }}>Administered — awaiting countersignature</span>
                  )}
                  {(o.status === "DRAFT" || o.status === "PENDING_CLINICAL_REVIEW" || o.status === "PENDING_HOSPICE_MD_APPROVAL" || o.status === "APPROVED") && (
                    <button type="button" style={{ ...ohBtnSecondary, color: SNS_COLORS.red, borderColor: SNS_COLORS.red }} disabled={busyOrderId === o.id} onClick={() => runOrderAction(o.id, (id) => cancelPhysicianOrder(id, "Cancelled from Orders Hub"))}>
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Fax panel ── */}
      {faxOpen && (
        <div style={{ ...SNS_S.card, padding: 16, marginTop: 16, background: SNS_COLORS.bg, border: `1px solid ${SNS_COLORS.teal}` }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: SNS_COLORS.white }}>Fax Order / History</div>
            <button type="button" style={ohBtnSecondary} onClick={() => setFaxOpen(false)}>Close</button>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            <input style={{ ...ohInput, width: 220 }} placeholder="Recipient (e.g. pharmacy name)" value={faxForm.recipient_name} onChange={(e) => setFaxForm((f) => ({ ...f, recipient_name: e.target.value }))} />
            <input style={{ ...ohInput, width: 180 }} placeholder="Fax number" value={faxForm.recipient_fax_number} onChange={(e) => setFaxForm((f) => ({ ...f, recipient_fax_number: e.target.value }))} />
            <button type="button" style={ohBtnPrimary} disabled={faxSending} onClick={handleSendFax}>
              {faxSending ? "Sending…" : "Send Fax"}
            </button>
          </div>
          {faxError && <div style={{ color: SNS_COLORS.red, fontSize: 12, marginBottom: 8 }}>{faxError}</div>}
          <div style={{ fontSize: 11, fontWeight: 600, color: SNS_COLORS.dim, textTransform: "uppercase", marginBottom: 4 }}>History</div>
          {faxHistory.length === 0 && <div style={{ fontSize: 12, color: SNS_COLORS.dim }}>No faxes sent yet.</div>}
          {faxHistory.map((f) => (
            <div key={f.id} style={{ fontSize: 12, color: SNS_COLORS.muted, padding: "4px 0", borderBottom: `1px solid ${SNS_COLORS.border}` }}>
              {f.recipient_name} ({f.recipient_fax_number}) — <span style={{ color: f.status === "FAILED" ? SNS_COLORS.red : SNS_COLORS.green }}>{f.status}</span> — {f.created_at ? new Date(f.created_at).toLocaleString() : ""}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const BODY_MAP_COLORS = {
  bg: "#1E293B",
  silhouette: "#CBD5E1",
  silhouetteStroke: "#64748B",
  wound: "#EF4444",
  woundGlow: "rgba(239, 68, 68, 0.35)",
  healed: "#10B981",
  text: "#F8FAFC",
  textMuted: "#94A3B8",
  card: "#334155",
  border: "#475569",
  teal: "#0D9488",
};

// ── Anatomically accurate front silhouette ──
const FRONT_BODY = () => (
  <g transform="translate(20, 5) scale(0.72)">
    <ellipse cx="100" cy="22" rx="18" ry="21" />
    <rect x="92" y="42" width="16" height="10" rx="4" />
    <path d="M68,52 Q62,52 58,56 L52,62 Q48,66 50,72 L50,72 Q48,70 44,72 L36,76 Q28,80 26,88 L22,104 Q20,112 26,114 L40,116 L42,108 L50,108 L50,130 Q50,136 52,142 L52,142 L48,160 L44,178 Q42,186 44,194 L46,204 Q47,208 50,210 L50,212 Q48,216 48,220 L47,228 Q46,234 50,236 L66,238 Q70,238 70,234 L70,226 L68,218 L70,210 L74,194 L80,170 L86,194 L90,210 L92,218 L90,226 L90,234 Q90,238 94,238 L110,236 Q114,234 113,228 L112,220 Q112,216 110,212 L110,210 Q113,208 114,204 L116,194 Q118,186 116,178 L112,160 L108,142 Q110,136 110,130 L110,108 L118,108 L120,116 L134,114 Q140,112 138,104 L134,88 Q132,80 124,76 L116,72 Q112,70 110,72 L110,72 Q112,66 108,62 L102,56 Q98,52 92,52 Z" />
    <line x1="80" y1="62" x2="80" y2="130" stroke="rgba(100,116,139,0.3)" strokeWidth="0.5" />
    <path d="M68,78 Q80,86 92,78" fill="none" stroke="rgba(100,116,139,0.3)" strokeWidth="0.5" />
    <circle cx="80" cy="118" r="2" fill="rgba(100,116,139,0.3)" />
  </g>
);

// ── Anatomically accurate back silhouette ──
const BACK_BODY = () => (
  <g transform="translate(20, 5) scale(0.72)">
    <ellipse cx="100" cy="22" rx="18" ry="21" />
    <rect x="92" y="42" width="16" height="10" rx="4" />
    <path d="M68,52 Q62,52 58,56 L52,62 Q48,66 50,72 L50,72 Q48,70 44,72 L36,76 Q28,80 26,88 L22,104 Q20,112 26,114 L40,116 L42,108 L50,108 L50,130 Q50,136 52,142 L52,142 L48,160 L44,178 Q42,186 44,194 L46,204 Q47,208 50,210 L50,212 Q48,216 48,220 L47,228 Q46,234 50,236 L66,238 Q70,238 70,234 L70,226 L68,218 L70,210 L74,194 L80,170 L86,194 L90,210 L92,218 L90,226 L90,234 Q90,238 94,238 L110,236 Q114,234 113,228 L112,220 Q112,216 110,212 L110,210 Q113,208 114,204 L116,194 Q118,186 116,178 L112,160 L108,142 Q110,136 110,130 L110,108 L118,108 L120,116 L134,114 Q140,112 138,104 L134,88 Q132,80 124,76 L116,72 Q112,70 110,72 L110,72 Q112,66 108,62 L102,56 Q98,52 92,52 Z" />
    <line x1="80" y1="52" x2="80" y2="142" stroke="rgba(100,116,139,0.4)" strokeWidth="1" strokeDasharray="2,3" />
    <path d="M64,72 Q60,80 64,90 Q68,84 72,78 Z" fill="rgba(100,116,139,0.15)" />
    <path d="M96,72 Q100,80 96,90 Q92,84 88,78 Z" fill="rgba(100,116,139,0.15)" />
    <ellipse cx="80" cy="138" rx="8" ry="5" fill="rgba(100,116,139,0.15)" />
  </g>
);

function WoundMarker({ x, y, label, woundName, stage, onClick, isSelected }) {
  const calloutX = x > 90 ? x - 85 : x + 18;
  return (
    <g onClick={onClick} style={{ cursor: "pointer" }}>
      <circle cx={x} cy={y} r={14} fill={BODY_MAP_COLORS.woundGlow} />
      <circle cx={x} cy={y} r={8} fill={BODY_MAP_COLORS.wound} stroke="#FFF" strokeWidth={2} />
      <text x={x} y={y + 3.5} textAnchor="middle" fontSize={9} fontWeight={800} fill="#FFF" style={{ pointerEvents: "none" }}>
        {label}
      </text>
      {isSelected && (
        <>
          <line x1={x > 90 ? x - 8 : x + 8} y1={y} x2={calloutX + (x > 90 ? 65 : 0)} y2={y - 10} stroke={BODY_MAP_COLORS.wound} strokeWidth={1} opacity={0.7} />
          <rect x={calloutX} y={y - 32} width={70} height={28} rx={4} fill={BODY_MAP_COLORS.card} stroke={BODY_MAP_COLORS.wound} strokeWidth={1} />
          <text x={calloutX + 6} y={y - 18} fontSize={8} fill={BODY_MAP_COLORS.text} fontWeight={600}>{woundName}</text>
          <text x={calloutX + 6} y={y - 9} fontSize={7} fill={BODY_MAP_COLORS.textMuted}>Stage {stage}</text>
        </>
      )}
    </g>
  );
}

function BodyMap({ value = [], tone = "pain", patientType = "verbal", onPatientTypeChange, onToggle, onClearAll }) {
  const [view, setView] = useState("both");
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const selectedRegions = Array.isArray(value) ? value : [];

  const bodyTypeButtons = [
    { label: "Verbal / able to self-report", value: "verbal" },
    { label: "Non-verbal / unable to self-report", value: "non-verbal" },
    { label: "Pediatric / child", value: "pediatric" },
  ];

  const viewLabelMap = {
    both: "Anterior (Front) / Posterior (Back)",
    front: "Anterior (Front)",
    back: "Posterior (Back)",
  };

  return (
    <div style={{ marginBottom: 16 }}>
      {onPatientTypeChange && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
          {bodyTypeButtons.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => onPatientTypeChange(option.value)}
              style={{
                borderRadius: 999,
                border: patientType === option.value ? `1px solid ${COLORS.teal}` : `1px solid ${COLORS.border}`,
                background: patientType === option.value ? (tone === "skin" ? COLORS.warningBoxBg : COLORS.tealBg) : COLORS.white,
                color: COLORS.dark,
                fontSize: 11,
                fontWeight: 700,
                padding: "5px 10px",
                cursor: "pointer",
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}

      <div style={{ marginBottom: 12 }}>
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
          padding: "8px 10px",
          background: COLORS.mapControlBg,
          border: `1px solid ${COLORS.mapControlBorder}`,
          borderRadius: 12,
          boxShadow: "inset 0 1px 2px rgba(15, 23, 42, 0.04)",
        }}>
          <div style={{
            fontSize: 11,
            fontWeight: 800,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: COLORS.mapMuted,
          }}>
            Body view
          </div>

          <div style={{
            fontSize: 12,
            fontWeight: 800,
            color: COLORS.mapChipText,
            background: COLORS.mapChipBg,
            border: `1px solid ${COLORS.mapControlBorder}`,
            borderRadius: 8,
            padding: "6px 10px",
            minWidth: 190,
            textAlign: "center",
          }}>
            {viewLabelMap[view] || "Anterior (Front) / Posterior (Back)"}
          </div>

          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            flexWrap: "wrap",
          }}>
            {[
              { label: "Both", value: "both" },
              { label: "Front", value: "front" },
              { label: "Back", value: "back" },
            ].map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setView(option.value)}
                style={{
                  borderRadius: 8,
                  border: view === option.value ? `1px solid ${COLORS.teal}` : "1px solid transparent",
                  background: view === option.value ? COLORS.tealBg : "transparent",
                  color: view === option.value ? COLORS.mapChipText : COLORS.mapMuted,
                  fontSize: 11,
                  fontWeight: 700,
                  padding: "7px 12px",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <BodyMapPain
        selectedRegions={selectedRegions}
        onToggleRegion={(regionId) => onToggle?.(regionId)}
        onClearAll={onClearAll}
        view={view}
      />
    </div>
  );
}

// Body map is a secondary interaction: the Pain screen's primary surface
// only ever shows a one-line summary + "Edit body map" button. The full
// interactive silhouette (BodyMap above) only exists inside this Dialog,
// so it never consumes vertical space in the normal page flow -- opened
// on demand, closed by default, same data/onToggle contract as before.
function PainBodyMapDialogField({ value = [], onToggle, onClearAll, regionLabelById }) {
  const [open, setOpen] = useState(false);
  const selected = Array.isArray(value) ? value : [];
  const summaryText = selected.length
    ? selected.map((id) => regionLabelById?.[id] || id).join(", ")
    : "No body map location documented";

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
      <div style={{ fontSize: 12, color: "var(--sns-text, inherit)", flex: 1, minWidth: 160 }}>
        <strong style={{ fontWeight: 700 }}>Body map: </strong>{summaryText}
      </div>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rnica-pain-bodymap-edit-btn"
        style={{
          borderRadius: 8,
          border: "1px solid var(--sns-border, #ccc)",
          background: "transparent",
          fontSize: 11.5,
          fontWeight: 700,
          padding: "6px 12px",
          cursor: "pointer",
          whiteSpace: "nowrap",
        }}
      >
        {selected.length ? "Edit body map" : "Add body map location"}
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Pain — Body Map</DialogTitle>
            <DialogDescription>Select every region where the patient reports or shows pain.</DialogDescription>
          </DialogHeader>
          <BodyMap value={selected} tone="pain" onToggle={onToggle} onClearAll={onClearAll} />
          <DialogFooter>
            <button
              type="button"
              onClick={() => setOpen(false)}
              style={{
                borderRadius: 8,
                border: "1px solid var(--sns-teal, #0d9488)",
                background: "var(--sns-teal, #0d9488)",
                color: "#fff",
                fontSize: 12.5,
                fontWeight: 700,
                padding: "8px 16px",
                cursor: "pointer",
              }}
            >
              Done
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

const ANTERIOR_REGIONS = [
  { id: "head_crown",          label: "Head (Crown)",            x: 90,  y: 25  },
  { id: "right_temple",        label: "Right Temple",            x: 78,  y: 26  },
  { id: "left_temple",         label: "Left Temple",             x: 101, y: 27  },
  { id: "right_eye",           label: "Right Eye",               x: 84,  y: 34  },
  { id: "left_eye",            label: "Left Eye",                x: 96,  y: 35  },
  { id: "nose",                label: "Nose",                    x: 90,  y: 36  },
  { id: "right_ear",           label: "Right Ear",               x: 76,  y: 38  },
  { id: "left_ear",            label: "Left Ear",                x: 104, y: 38  },
  { id: "mouth",               label: "Mouth",                   x: 90,  y: 46  },
  { id: "right_mandible",      label: "Right Mandible",          x: 81,  y: 47  },
  { id: "left_mandible",       label: "Left Mandible",           x: 98,  y: 46  },
  { id: "neck_anterior",       label: "Neck (Anterior)",         x: 90,  y: 57  },
  { id: "right_shoulder",      label: "Right Shoulder",          x: 63,  y: 69  },
  { id: "left_shoulder",       label: "Left Shoulder",           x: 118, y: 69  },
  { id: "sternum",             label: "Sternum",                 x: 90,  y: 82  },
  { id: "right_chest",         label: "Right Chest",             x: 76,  y: 85  },
  { id: "left_chest",          label: "Left Chest",              x: 106, y: 82  },
  { id: "right_rib_cage",      label: "Right Rib Cage",          x: 72,  y: 101 },
  { id: "left_rib_cage",       label: "Left Rib Cage",           x: 111, y: 99  },
  { id: "right_bicep",         label: "Right Bicep",             x: 54,  y: 102 },
  { id: "left_bicep",          label: "Left Bicep",              x: 126, y: 101 },
  { id: "right_elbow",         label: "Right Elbow",             x: 50,  y: 116 },
  { id: "left_elbow",          label: "Left Elbow",              x: 130, y: 117 },
  { id: "right_forearm",       label: "Right Forearm",           x: 47,  y: 130 },
  { id: "left_forearm",        label: "Left Forearm",            x: 133, y: 133 },
  { id: "right_wrist",         label: "Right Wrist",             x: 46,  y: 155 },
  { id: "left_wrist",          label: "Left Wrist",              x: 135, y: 155 },
  { id: "right_hand",          label: "Right Hand",              x: 44,  y: 172 },
  { id: "left_hand",           label: "Left Hand",               x: 137, y: 170 },
  { id: "right_upper_abdomen", label: "Right Upper Abdomen",     x: 76,  y: 114 },
  { id: "left_upper_abdomen",  label: "Left Upper Abdomen",      x: 104, y: 116 },
  { id: "navel",               label: "Umbilicus (Navel)",       x: 90,  y: 128 },
  { id: "right_lower_abdomen", label: "Right Lower Abdomen",     x: 78,  y: 134 },
  { id: "left_lower_abdomen",  label: "Left Lower Abdomen",      x: 104, y: 134 },
  { id: "right_hip",           label: "Right Hip (Anterior)",    x: 66,  y: 143 },
  { id: "left_hip",            label: "Left Hip (Anterior)",     x: 113, y: 143 },
  { id: "suprapubic",          label: "Suprapubic",              x: 90,  y: 152 },
  { id: "right_groin",         label: "Right Groin",             x: 79,  y: 158 },
  { id: "left_groin",          label: "Left Groin",              x: 101, y: 158 },
  { id: "perineum",            label: "Perineum",                x: 90,  y: 164 },
  { id: "right_upper_thigh",   label: "Right Upper Thigh",       x: 71,  y: 167 },
  { id: "left_upper_thigh",    label: "Left Upper Thigh",        x: 110, y: 169 },
  { id: "right_medial_thigh",  label: "Right Medial Thigh",      x: 82,  y: 178 },
  { id: "left_medial_thigh",   label: "Left Medial Thigh",       x: 99,  y: 178 },
  { id: "right_lower_thigh",   label: "Right Lower Thigh",       x: 71,  y: 187 },
  { id: "left_lower_thigh",    label: "Left Lower Thigh",        x: 110, y: 188 },
  { id: "right_knee",          label: "Right Knee",              x: 75,  y: 219 },
  { id: "left_knee",           label: "Left Knee",               x: 107, y: 220 },
  { id: "right_shin",          label: "Right Shin",              x: 71,  y: 247 },
  { id: "left_shin",           label: "Left Shin",               x: 109, y: 247 },
  { id: "right_ankle",         label: "Right Ankle",             x: 72,  y: 287 },
  { id: "left_ankle",          label: "Left Ankle",              x: 109, y: 287 },
  { id: "right_foot",          label: "Right Foot (Dorsal)",     x: 72,  y: 297 },
  { id: "left_foot",           label: "Left Foot (Dorsal)",      x: 109, y: 297 },
  { id: "right_toes",          label: "Right Toes",              x: 72,  y: 308 },
  { id: "left_toes",           label: "Left Toes",               x: 109, y: 308 },
];

const POSTERIOR_REGIONS = [
  { id: "occiput",             label: "Occiput",                 x: 89,  y: 33  },
  { id: "cervical_spine",      label: "Cervical Spine",          x: 89,  y: 43  },
  { id: "posterior_neck",      label: "Posterior Neck",           x: 89,  y: 52  },
  { id: "left_shoulder_post",  label: "Left Shoulder (Post)",    x: 56,  y: 72  },
  { id: "right_shoulder_post", label: "Right Shoulder (Post)",   x: 118, y: 70  },
  { id: "left_deltoid",        label: "Left Deltoid",            x: 52,  y: 80  },
  { id: "right_deltoid",       label: "Right Deltoid",           x: 125, y: 75  },
  { id: "upper_back",          label: "Upper Back (Thoracic)",   x: 91,  y: 75  },
  { id: "left_scapula",        label: "Left Scapula",            x: 76,  y: 83  },
  { id: "right_scapula",       label: "Right Scapula",           x: 101, y: 83  },
  { id: "left_tricep",         label: "Left Tricep",             x: 48,  y: 95  },
  { id: "right_tricep",        label: "Right Tricep",            x: 129, y: 95  },
  { id: "left_elbow_post",     label: "Left Olecranon",          x: 49,  y: 113 },
  { id: "right_elbow_post",    label: "Right Olecranon",         x: 128, y: 112 },
  { id: "left_post_forearm",   label: "Left Posterior Forearm",  x: 44,  y: 138 },
  { id: "right_post_forearm",  label: "Right Posterior Forearm", x: 134, y: 138 },
  { id: "left_hand_post",      label: "Left Hand (Dorsal)",      x: 39,  y: 163 },
  { id: "right_hand_post",     label: "Right Hand (Dorsal)",     x: 141, y: 163 },
  { id: "lumbar_spine",        label: "Lumbar Spine",             x: 90,  y: 112 },
  { id: "left_flank",          label: "Left Flank",              x: 81,  y: 120 },
  { id: "right_flank",         label: "Right Flank",             x: 101, y: 119 },
  { id: "lower_back",          label: "Lower Back",              x: 90,  y: 125 },
  { id: "sacrum",              label: "Sacrum",                   x: 90,  y: 137 },
  { id: "left_hip_post",       label: "Left Hip (Posterior)",     x: 70,  y: 141 },
  { id: "right_hip_post",      label: "Right Hip (Posterior)",    x: 110, y: 140 },
  { id: "left_ischial",        label: "Left Ischial Tuberosity", x: 79,  y: 147 },
  { id: "right_ischial",       label: "Right Ischial Tuberosity",x: 101, y: 146 },
  { id: "coccyx",              label: "Coccyx",                   x: 90,  y: 156 },
  { id: "left_gluteal",        label: "Left Gluteal",             x: 80,  y: 159 },
  { id: "right_gluteal",       label: "Right Gluteal",            x: 104, y: 159 },
  { id: "left_trochanter",     label: "Left Greater Trochanter",  x: 67,  y: 150 },
  { id: "right_trochanter",    label: "Right Greater Trochanter", x: 113, y: 150 },
  { id: "left_post_thigh",     label: "Left Posterior Thigh",     x: 73,  y: 181 },
  { id: "right_post_thigh",    label: "Right Posterior Thigh",    x: 104, y: 181 },
  { id: "left_popliteal",      label: "Left Popliteal",           x: 74,  y: 216 },
  { id: "right_popliteal",     label: "Right Popliteal",          x: 104, y: 216 },
  { id: "left_calf",           label: "Left Calf",                x: 74,  y: 245 },
  { id: "right_calf",          label: "Right Calf",               x: 104, y: 244 },
  { id: "left_achilles",       label: "Left Achilles Tendon",     x: 75,  y: 286 },
  { id: "right_achilles",      label: "Right Achilles Tendon",    x: 102, y: 289 },
  { id: "left_heel",           label: "Left Heel",                x: 75,  y: 293 },
  { id: "right_heel",          label: "Right Heel",               x: 102, y: 295 },
  { id: "left_lateral_malleolus",  label: "Left Lateral Malleolus",  x: 68, y: 282 },
  { id: "right_lateral_malleolus", label: "Right Lateral Malleolus", x: 111,y: 282 },
  { id: "left_sole",           label: "Left Sole",                x: 76,  y: 300 },
  { id: "right_sole",          label: "Right Sole",               x: 101, y: 300 },
];

const BODY_MAP_REGION_LABEL_BY_ID = Object.fromEntries(
  [...ANTERIOR_REGIONS, ...POSTERIOR_REGIONS].map((r) => [r.id, r.label])
);

const BODY_MAP_AUDIT = validateBodyMapRegions({
  anterior: ANTERIOR_REGIONS,
  posterior: POSTERIOR_REGIONS,
  assetWidth: 540,
  assetHeight: 960,
  viewBoxWidth: 180,
  viewBoxHeight: 320,
});
if (import.meta.env.DEV && !BODY_MAP_AUDIT.valid) {
  throw new Error(`Invalid RNICA body-map overlay: ${BODY_MAP_AUDIT.errors.join("; ")}`);
}

function BodyMapPain({ selectedRegions = [], onToggleRegion, onClearAll, view = "both" }) {
  const [hovered, setHovered] = useState(null);
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const isDark = themeMode !== "light";

  const renderView = (imgSrc, regions, label, viewKey) => (
    <div style={{ flex: 1, textAlign: "center" }}>
      <div style={{
        fontSize: 12,
        fontWeight: 800,
        color: COLORS.mapChipText,
        marginBottom: 8,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
      }}>{label}</div>
      <div style={{
        position: "relative",
        width: "100%",
        maxWidth: 240,
        margin: "0 auto",
        aspectRatio: "180 / 320",
        overflow: "hidden",
      }}>
        <img
          src={imgSrc}
          alt={label}
          style={{
            position: "absolute",
            top: 0, left: 0,
            width: "100%",
            height: "100%",
            objectFit: "fill",
          }}
          draggable={false}
        />
        <svg
          viewBox="0 0 180 320"
          style={{
            position: "absolute",
            top: 0, left: 0,
            width: "100%",
            height: "100%",
          }}
        >
          {regions.map((r) => {
            const isActive = selectedRegions.includes(r.id);
            const isHover = hovered === r.id;
            const singleViewMode = view === "front" || view === "back";
            const showMarker = !singleViewMode || isActive || isHover;
            const showLabel = (isHover || isActive) && (view === "both" || view === viewKey);
            if (!showMarker) return null;
            return (
              <g key={r.id}
                onMouseEnter={() => setHovered(r.id)}
                onMouseLeave={() => setHovered(null)}
                onClick={() => onToggleRegion?.(r.id, r.label, viewKey)}
                style={{ cursor: "pointer" }}
              >
                <circle cx={r.x} cy={r.y} r={10} fill="transparent" />
                <circle
                  cx={r.x} cy={r.y}
                  r={isActive ? 7 : isHover ? 6 : 4.5}
                  fill={isActive ? "rgba(239,68,68,0.75)" : isHover ? "rgba(239,68,68,0.35)" : "rgba(100,116,139,0.2)"}
                  stroke={isActive ? "#DC2626" : isHover ? "#EF4444" : "rgba(100,116,139,0.35)"}
                  strokeWidth={1}
                  style={{ transition: "all 0.15s" }}
                />
                {showLabel && (
                  <text
                    x={r.x} y={r.y - 10}
                    textAnchor="middle" fontSize="8" fontWeight="700"
                    fill={isActive ? "#DC2626" : "#1E293B"}
                    stroke={"rgba(255,255,255,0.8)"}
                    strokeWidth={0.7}
                    paintOrder="stroke"
                  >{r.label}</text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );

  const showFront = view === "both" || view === "front";
  const showBack = view === "both" || view === "back";

  return (
    <div>
      <div style={{ display: "flex", gap: 32, justifyContent: "center" }}>
        {showFront && renderView(frontBody, ANTERIOR_REGIONS, "Anterior (Front)", "anterior")}
        {showBack && renderView(backBody, POSTERIOR_REGIONS, "Posterior (Back)", "posterior")}
      </div>

      {selectedRegions.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            marginBottom: 8,
            flexWrap: "wrap",
          }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: COLORS.mapMuted }}>
              Selected Regions ({selectedRegions.length})
            </div>
            <button
              type="button"
              onClick={() => onClearAll?.()}
              style={{
                border: isDark ? "1px solid rgba(248,113,113,0.4)" : "1px solid #FECACA",
                background: isDark ? "rgba(248,113,113,0.14)" : "#FFF1F2",
                color: isDark ? "#f87171" : "#BE123C",
                borderRadius: 999,
                padding: "5px 10px",
                fontSize: 11,
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Remove all markers
            </button>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {selectedRegions.map((id) => {
              const r = [...ANTERIOR_REGIONS, ...POSTERIOR_REGIONS].find((r) => r.id === id);
              return (
                <span key={id} onClick={() => onToggleRegion?.(id)}
                  style={{
                    padding: "4px 10px", borderRadius: 14, fontSize: 11, fontWeight: 500,
                    background: isDark ? "rgba(248,113,113,0.18)" : "#FEE2E2",
                    color: isDark ? "#fca5a5" : "#DC2626", cursor: "pointer",
                    border: isDark ? "1px solid rgba(248,113,113,0.4)" : "1px solid #FECACA",
                  }}>
                  {r?.label || id} ×
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// P3-009/P3-017: read-only SFV Follow-Up status card for the TRIGGERING
// RNICA encounter. This screen never offers a "Complete SFV" action --
// completion can only happen from a separate, later qualifying visit
// (see the Symptom Follow-Up Visit section on the Visit Notes screen).
// This card exists so the triggering clinician can see whether a
// follow-up is outstanding and jump to Visit Notes to create/open it.
function SfvStatusCard({ patientId, onNavigateToSection, onSyncCompletionStatus, styles, COLORS }) {
  const [requirements, setRequirements] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    listSfvRequirements(patientId)
      .then((rows) => {
        if (cancelled) return;
        setRequirements(rows);
        // HOPE J2052 export needs an accurate "in-person SFV completed?"
        // value -- source it from the authoritative backend requirement
        // status instead of a manual self-attested checkbox (P3-009).
        // Best-effort: reflects the most recently completed requirement,
        // if any (SFVRequirement lifecycle normally has one OPEN
        // requirement per patient at a time).
        const completedRows = rows.filter((r) => r.status === "COMPLETED" && r.completedAt);
        const latest = completedRows.sort((a, b) => (a.completedAt < b.completedAt ? 1 : -1))[0];
        onSyncCompletionStatus?.(Boolean(latest), latest ? latest.completedAt.slice(0, 10) : "");
      })
      .catch((err) => { if (!cancelled) setError(err.message || "Unable to load SFV status."); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  if (!patientId) return null;

  const cardStyle = {
    border: `1px solid ${COLORS.mapControlBorder || "#334155"}`,
    background: COLORS.mapControlBg || "rgba(15,23,42,0.4)",
    borderRadius: 10,
    padding: "12px 14px",
    marginBottom: 14,
    fontSize: 12.5,
    color: COLORS.mapMuted || COLORS.gray,
    lineHeight: 1.6,
  };

  if (error) {
    return <div style={cardStyle}>SFV Follow-Up Required — status unavailable ({error})</div>;
  }
  if (requirements === null) {
    return <div style={cardStyle}>Loading SFV follow-up status…</div>;
  }
  if (requirements.length === 0) {
    return null;
  }

  return (
    <div style={cardStyle}>
      <strong style={{ color: COLORS.mapChipText || COLORS.text }}>SFV Follow-Up Required</strong>
      <div style={{ marginTop: 6, display: "flex", flexDirection: "column", gap: 8 }}>
        {requirements.map((r) => (
          <div key={r.sfvRequirementId}>
            <div>Status: <strong>{r.status}</strong>{r.dueAt ? ` · due ${new Date(r.dueAt).toLocaleDateString()}` : ""}</div>
            {r.status === "COMPLETED" ? (
              <div>Completed via a separate follow-up visit{r.completedAt ? ` on ${new Date(r.completedAt).toLocaleDateString()}` : ""}.</div>
            ) : (
              <div>
                Symptom follow-up requires a separate clinical encounter. The follow-up
                may be completed by the original nurse, another assigned nurse, or another
                appropriately authorized nursing clinician.
              </div>
            )}
          </div>
        ))}
        {onNavigateToSection && (
          <button
            type="button"
            onClick={() => onNavigateToSection("visit-notes")}
            style={{
              alignSelf: "flex-start",
              background: "transparent",
              border: `1px solid ${COLORS.mapControlBorder || "#334155"}`,
              color: COLORS.mapChipText || COLORS.text,
              borderRadius: 6,
              padding: "4px 10px",
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            Create/Open Follow-Up Visit
          </button>
        )}
      </div>
    </div>
  );
}

function Card({ title, children, hopeCode, sfv, cms, id, collapsible = false, defaultCollapsed = false, bare = false, importance = null, fullWidth = false, compact = false }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  // [OWNER REVIEW -- 2026-09-25] Pain Assessment Tool must default to
  // collapsed: the 0-10 scale/protocol reference consumes excessive
  // screen space and most RNs already know how to use it. Generic
  // `collapsible` support on Card so any card can opt into this pattern
  // without a bespoke wrapper.
  const [collapsed, setCollapsed] = useState(collapsible && defaultCollapsed);
  const titleRowContent = (
    <>
      {collapsible && <span aria-hidden="true" style={{ fontSize: 11, color: COLORS.label || COLORS.gray }}>{collapsed ? "►" : "▾"}</span>}
      {title}
      {hopeCode && <HopeTag code={hopeCode} />}
      {sfv && <SfvTag />}
      {cms && <CmsTag label={cms} />}
    </>
  );
  const titleRowProps = {
    className: "rnica-form-card__title",
    style: { ...styles.cardTitle, display: "flex", alignItems: "center", gap: 8, cursor: collapsible ? "pointer" : undefined },
    onClick: collapsible ? () => setCollapsed((c) => !c) : undefined,
    role: collapsible ? "button" : undefined,
    tabIndex: collapsible ? 0 : undefined,
    "aria-expanded": collapsible ? !collapsed : undefined,
    onKeyDown: collapsible ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setCollapsed((c) => !c); } } : undefined,
  };
  // `bare` renders an inline group (title row + children only, no card
  // box/border/shadow/margin) -- used to pack multiple sub-sections into
  // one shared workspace Card instead of each getting its own bordered
  // container. Same title/hopeCode/sfv/cms row and same children content;
  // only the outer box chrome is removed.
  // GitHub Directive (2026-09-28) Critical Finding #3 -- visual hierarchy:
  // an optional "high"/"medium"/"low" importance modifier class so a card's
  // weight (border/background emphasis) can reflect clinical importance
  // instead of every section competing equally. Purely a CSS hook -- no
  // behavior change when omitted.
  const importanceClass = importance ? ` rnica-form-card--${importance}` : "";
  // GitHub Directive (2026-09-28) "Final Neurological Density and
  // Space-Utilization Plan" Section 11/21 -- some sub-sections (e.g.
  // Sleep/Responsiveness, the merged Communication and Sensory card) must
  // span the full workspace width instead of being squeezed into one
  // column of the surrounding auto-fit grid alongside much shorter
  // sub-sections (the "uneven column height" defect). Pure CSS hook.
  const fullWidthClass = fullWidth ? " rnica-bodysystem-workspace__group--full" : "";
  if (bare) {
    return (
      <div className={`rnica-bodysystem-workspace__group${importanceClass}${fullWidthClass}`} id={id}>
        <div {...titleRowProps}>{titleRowContent}</div>
        {(!collapsible || !collapsed) && children}
      </div>
    );
  }
  // Migrated onto the shadcn Card primitives (ShadcnCard/CardHeader/
  // CardTitle/CardContent, restyled to the RNICA theme tokens) instead of
  // a hand-rolled div -- same title/hopeCode/sfv/cms/collapsible/id
  // contract, so none of the 28 modules' field configs change.
  // [Pain density pass -- 2026-10] `compact` trims header/content padding
  // (px-5/pt-4/py-4 -> px-4/pt-3/py-3). Opt-in only -- defaults to false so
  // every other module's card chrome is byte-for-byte unchanged; only the
  // Pain section passes compact=true (see renderGenericSection). No field,
  // title, hopeCode, or content change -- padding only.
  return (
    <ShadcnCard id={id} className={`rnica-form-card${importanceClass}`}>
      <ShadcnCardHeader className={compact ? "px-4 pt-3" : undefined}>
        <ShadcnCardTitle {...titleRowProps}>{titleRowContent}</ShadcnCardTitle>
      </ShadcnCardHeader>
      {(!collapsible || !collapsed) && <ShadcnCardContent className={compact ? "px-4 py-3" : undefined}>{children}</ShadcnCardContent>}
    </ShadcnCard>
  );
}

// ════════════════════════════════════════════════════════════════
// 6. SECTION RENDERERS — All 28 Modules
// ════════════════════════════════════════════════════════════════

// HOPE A1905 Living Arrangement value-code labels -- kept in sync with the
// FormRadioGroup options rendered in renderDemographics below. Used by the
// Patient Story "Patient Attributes" panel to display the human-readable
// label rather than the raw HOPE code.
const LIVING_ARRANGEMENT_LABELS = {
  "1": "Alone (no other residents in the home)",
  "2": "With others in the home (family, friends, or paid caregiver)",
  "3": "Congregate home (e.g., assisted living or residential care home)",
  "4": "Inpatient facility (e.g., SNF, nursing home, inpatient hospice, hospital)",
  "5": "Does not have a permanent home (unstable housing / homeless)",
};

function renderDemographics(data, update, COLORS, styles, moduleKey = "all", uiProfile = {}) {
  const u = (path, val) => update("demographics", path, val);
  const showPatient = moduleKey === "all" || moduleKey === "demographics";
  const showCaregiver = moduleKey === "all" || moduleKey === "caregiverAssessment";
  const showPlanning = (moduleKey === "all" || moduleKey === "advancedCarePlanning") && !uiProfile.hideAdvancedCarePlanning;
  return (
    <>
      <p className="rnica-form-section__subtitle" style={styles.sectionSubtitle}>
        {showCaregiver && !showPatient
          ? "Primary caregiver and willingness/capability assessment"
          : showPlanning && !showPatient
            ? "Code status, treatment preferences, decision maker, and directives"
            : "Patient identification, contacts, and living situation"}
      </p>

      {showPatient && <>
      <Card title="Patient Information" hopeCode="A1110">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
          <FormInput label="First Name" value={data.firstName} onChange={(v) => u("firstName", v)} required />
          <FormInput label="Last Name" value={data.lastName} onChange={(v) => u("lastName", v)} required />
          <FormInput label="Date of Birth" value={data.dob} onChange={(v) => u("dob", v)} type="date" required />
          <FormSelect label="Gender" value={data.gender} onChange={(v) => u("gender", v)} required
            options={["Male", "Female", "Non-binary", "Other", "Declined"]} />
          <FormInput label="Phone" value={data.phone} onChange={(v) => u("phone", v)} type="tel" />
          <FormInput label="Alternate Phone" value={data.alternatePhone} onChange={(v) => u("alternatePhone", v)} type="tel" />
        </div>
        <FormCheckboxGroup label="Race" values={data.race} onChange={(v) => u("race", v)} hopeCode="A1010"
          options={RACE_OPTIONS} />
        <FormCheckboxGroup label="Ethnicity" values={data.ethnicity} onChange={(v) => u("ethnicity", v)} hopeCode="A1005"
          options={ETHNICITY_OPTIONS} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
          <FormSelect label="Preferred Language" value={data.preferredLanguage} onChange={(v) => u("preferredLanguage", v)}
            options={LANGUAGE_OPTIONS} />
          <FormCheckbox label="Needs Interpreter" checked={data.needsInterpreter} onChange={(v) => u("needsInterpreter", v)} />
          <FormInput label="Religion" value={data.religion} onChange={(v) => u("religion", v)} />
          <FormSelect label="Marital Status" value={data.maritalStatus} onChange={(v) => u("maritalStatus", v)}
            options={["Single", "Married", "Divorced", "Widowed", "Separated", "Domestic Partner"]} />
          <FormSelect label="Military Service (Patient/Spouse)" value={data.militaryService} onChange={(v) => u("militaryService", v)}
            options={["Yes", "No", "Unknown"]} />
        </div>
      </Card>

      <Card title="Address">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
          <div style={{ gridColumn: "1 / -1" }}>
            <FormInput label="Street" value={data.address?.street} onChange={(v) => u("address.street", v)} />
          </div>
          <FormInput label="City" value={data.address?.city} onChange={(v) => u("address.city", v)} />
          <FormInput label="State" value={data.address?.state} onChange={(v) => u("address.state", v)} />
          <FormInput label="ZIP" value={data.address?.zip} onChange={(v) => u("address.zip", v)} />
          <FormInput label="County" value={data.address?.county} onChange={(v) => u("address.county", v)} />
        </div>
      </Card>

      <Card title="Emergency Contact">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
          <FormInput label="Name" value={data.emergencyContact?.name} onChange={(v) => u("emergencyContact.name", v)} />
          <FormInput label="Relationship" value={data.emergencyContact?.relationship} onChange={(v) => u("emergencyContact.relationship", v)} />
          <FormInput label="Phone" value={data.emergencyContact?.phone} onChange={(v) => u("emergencyContact.phone", v)} type="tel" />
        </div>
      </Card>
      </>}

      {showCaregiver && <>
      <Card title="Primary Caregiver (PCG)" id="pcg">
        <FormRadioGroup label="Does this patient have a Primary Caregiver?"
          value={!pcgIsAssessed(data.pcg) ? "" : (data.pcg?.noPcg ? "no" : "yes")}
          onChange={(v) => { u("pcg.assessed", true); u("pcg.noPcg", v === "no"); }}
          options={[{ value: "yes", label: "Yes — has a PCG" }, { value: "no", label: "No PCG — facility-based care" }]} />
        {!pcgIsAssessed(data.pcg) && (
          <div style={{ fontSize: 12, color: COLORS.warning || "#92400e", background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 4, padding: "6px 8px", marginBottom: 8 }}>
            Not yet assessed this visit — select Yes or No above before finalizing.
          </div>
        )}
        {data.pcg?.noPcg ? (
          <FormSelect label="Facility / Care Setting" value={data.pcg?.noPcgReason}
            onChange={(v) => {
              u("pcg.noPcgReason", v);
              // Keep Living Situation in sync so the facility type is only entered once.
              // Values are the official CMS HOPE A0215 Site of Service codes.
              const siteOfService = { "Memory Care": "02", "Board & Care": "02", "Skilled Nursing Facility": "04", "Assisted Living Facility": "02", "Other facility-based care": "99" }[v];
              if (siteOfService) {
                u("livingSituation.siteOfService", siteOfService);
                u("livingSituation.livingArrangement", "4"); // A1905: Inpatient facility
              }
            }}
            options={["Memory Care", "Board & Care", "Skilled Nursing Facility", "Assisted Living Facility", "Other facility-based care"]} />
        ) : (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
              <FormInput label="PCG Name" value={data.pcg?.name} onChange={(v) => u("pcg.name", v)} />
              <FormInput label="Relationship" value={data.pcg?.relationship} onChange={(v) => u("pcg.relationship", v)} />
              <FormInput label="Phone" value={data.pcg?.phone} onChange={(v) => u("pcg.phone", v)} type="tel" />
            </div>
            <FormRadioGroup label="PCG Health Status" value={data.pcg?.healthStatus} onChange={(v) => u("pcg.healthStatus", v)}
              options={["Good", "Fair", "Poor"]} />
            <FormRadioGroup label="PCG Anxiety Level" value={data.pcg?.anxietyLevel} onChange={(v) => u("pcg.anxietyLevel", v)}
              options={["None", "Mild", "Moderate", "Severe"]} />
            <FormRadioGroup label="Sign-Language Interpreter Needed (if PCG hard of hearing/deaf)" value={data.pcg?.signLanguageInterpreterNeeded} onChange={(v) => u("pcg.signLanguageInterpreterNeeded", v)}
              options={["No", "Yes", "Unable to determine"]} />
            <FormRadioGroup label="PCG Able to Participate in Care" value={data.pcg?.participatesInCare} onChange={(v) => u("pcg.participatesInCare", v)}
              options={["Yes", "Partially", "No", "Unable to assess"]} />
            <FormRadioGroup label="Able to Administer Medications" value={data.pcg?.ableToAdministerMeds} onChange={(v) => u("pcg.ableToAdministerMeds", v)}
              options={["Yes", "No", "With training"]} />
            <FormRadioGroup label="Willing to Provide Care" value={data.pcg?.willingToProvideCare} onChange={(v) => u("pcg.willingToProvideCare", v)}
              options={["Yes", "No", "Ambivalent"]} />

            {/* Household factors — cross-checked against real HospiceMD
                "Communications & Other Factors > PCG" section: "Any young
                children at home?" and "Any pets? (If yes, specify)". These
                are household/safety/care-planning factors, not demographics. */}
            <FormRadioGroup label="Young Children in the Home" value={data.pcg?.householdChildren} onChange={(v) => u("pcg.householdChildren", v)}
              options={["No", "Yes", "Unknown"]} />
            {data.pcg?.householdChildren === "Yes" && (
              <FormInput label="Age Range / Safety-Support Concern (if clinically useful)" value={data.pcg?.householdChildrenDetail} onChange={(v) => u("pcg.householdChildrenDetail", v)} />
            )}
            <FormRadioGroup label="Pets in the Home" value={data.pcg?.householdPets} onChange={(v) => u("pcg.householdPets", v)}
              options={["No", "Yes", "Unknown"]} />
            {data.pcg?.householdPets === "Yes" && (
              <FormInput label="Specify (safety/access/infection concern if applicable)" value={data.pcg?.householdPetsDetail} onChange={(v) => u("pcg.householdPetsDetail", v)} />
            )}

            {/* Patient's own medication self-administration capability —
                deliberately adjacent to PCG's "Able to Administer
                Medications" above so both capabilities are reviewed
                together, but visually distinct (own heading) since
                HospiceMD tracks these as two separate fields. */}
            <div className="rnica-classic-subheading" style={{ fontSize: 12, fontWeight: 700, color: COLORS?.label || "#64748b", textTransform: "uppercase", letterSpacing: "0.03em", marginTop: 12, marginBottom: 4 }}>
              Medication Safety — Patient Self-Administration
            </div>
            <FormRadioGroup label="Patient Able to Safely Self-Administer Medications" value={data.medicationSafety?.selfAdministersMeds} onChange={(v) => u("medicationSafety.selfAdministersMeds", v)}
              options={["Yes", "With assistance", "No", "Not applicable", "Unable to assess"]} />
            {["With assistance", "No"].includes(data.medicationSafety?.selfAdministersMeds) && (
              <FormSelect label="If No, Who Administers Medications to Patient" value={data.medicationSafety?.medsAdministeredBy} onChange={(v) => u("medicationSafety.medsAdministeredBy", v)}
                options={["Primary caregiver", "Family member", "Facility staff", "Hospice staff under an authorized plan", "Other", "No responsible person identified"]} />
            )}

            <FormTextarea label="PCG Concerns / Notes" value={data.pcg?.pcgConcerns} onChange={(v) => u("pcg.pcgConcerns", v)} />
          </>
        )}
      </Card>

      {/* CDPH Gap #2 — Caregiver Willingness & Capability Evaluation.
          Only applies when the patient has an informal/family PCG; facility
          -based patients (memory care, board & care, SNF, ALF) are cared for
          by licensed facility staff, so this evaluation is N/A for them. */}
      {!data.pcg?.noPcg && (
      <Card title="Caregiver Willingness & Capability Evaluation" cms="CDPH Required">
        <div style={styles.infoBox}>
          <strong>CDPH Requirement:</strong> The comprehensive assessment must include an evaluation of caregiver
          willingness and capability to provide care. This section documents the structured evaluation.
        </div>
        <FormRadioGroup label="Physical Ability to Perform Care Tasks" value={data.pcg?.caregiverEvaluation?.physicalAbility}
          onChange={(v) => u("pcg.caregiverEvaluation.physicalAbility", v)}
          options={["Fully capable", "Capable with limitations", "Limited capability", "Unable"]} />
        <FormRadioGroup label="Cognitive Ability to Follow Care Instructions" value={data.pcg?.caregiverEvaluation?.cognitiveAbility}
          onChange={(v) => u("pcg.caregiverEvaluation.cognitiveAbility", v)}
          options={["Fully understands", "Understands with reinforcement", "Difficulty understanding", "Unable to understand"]} />
        <FormRadioGroup label="Emotional Readiness for Caregiving Role" value={data.pcg?.caregiverEvaluation?.emotionalReadiness}
          onChange={(v) => u("pcg.caregiverEvaluation.emotionalReadiness", v)}
          options={["Ready and engaged", "Ambivalent but willing", "Reluctant", "Overwhelmed/resistant"]} />
        <FormSelect label="Hours/Day Available for Care" value={data.pcg?.caregiverEvaluation?.availabilityForCare}
          onChange={(v) => u("pcg.caregiverEvaluation.availabilityForCare", v)}
          options={["24/7 available", "16-23 hours", "8-15 hours", "4-7 hours", "Less than 4 hours", "Not available"]} />
        <FormCheckboxGroup label="Training Needs Identified" values={data.pcg?.caregiverEvaluation?.trainingNeeds || []}
          onChange={(v) => u("pcg.caregiverEvaluation.trainingNeeds", v)}
          options={["Medication administration", "Wound care", "Symptom management", "Emergency procedures",
            "Body mechanics/transfers", "Nutrition/feeding", "Skin care/positioning", "Equipment use",
            "Infection control", "Pain assessment", "When to call hospice"]} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
          <FormSelect label="Willingness Score (1-5)" value={data.pcg?.caregiverEvaluation?.willingnessScore}
            onChange={(v) => u("pcg.caregiverEvaluation.willingnessScore", v)}
            options={[
              { value: "1", label: "1 — Unwilling" }, { value: "2", label: "2 — Reluctant" },
              { value: "3", label: "3 — Ambivalent" }, { value: "4", label: "4 — Willing" },
              { value: "5", label: "5 — Fully committed" },
            ]} />
          <FormSelect label="Capability Score (1-5)" value={data.pcg?.caregiverEvaluation?.capabilityScore}
            onChange={(v) => u("pcg.caregiverEvaluation.capabilityScore", v)}
            options={[
              { value: "1", label: "1 — Unable" }, { value: "2", label: "2 — Minimal" },
              { value: "3", label: "3 — Moderate" }, { value: "4", label: "4 — Capable" },
              { value: "5", label: "5 — Fully capable" },
            ]} />
          <FormRadioGroup label="Support System Adequacy" value={data.pcg?.caregiverEvaluation?.supportSystemAdequacy}
            onChange={(v) => u("pcg.caregiverEvaluation.supportSystemAdequacy", v)}
            options={["Adequate", "Inadequate", "Needs reinforcement"]} />
        </div>
        <FormTextarea label="Caregiver Evaluation Notes" value={data.pcg?.caregiverEvaluation?.evaluationNotes}
          onChange={(v) => u("pcg.caregiverEvaluation.evaluationNotes", v)}
          placeholder="Document caregiver evaluation findings, concerns, and recommended interventions..." rows={4} />
      </Card>
      )}
      </>}

      {showPatient && (
      <Card title="Living Situation" hopeCode="A1905">
        <FormSelect label="Site of Service" value={data.livingSituation?.siteOfService} onChange={(v) => u("livingSituation.siteOfService", v)}
          hopeCode="A0215" options={[
            { value: "01", label: "Patient's Home/Residence" },
            { value: "02", label: "Assisted Living Facility" },
            { value: "03", label: "Nursing Long Term Care (LTC) or Non-Skilled Nursing Facility (NF)" },
            { value: "04", label: "Skilled Nursing Facility (SNF)" },
            { value: "05", label: "Inpatient Hospital" },
            { value: "06", label: "Inpatient Hospice Facility (General Inpatient / GIP)" },
            { value: "07", label: "Long Term Care Hospital (LTCH)" },
            { value: "08", label: "Inpatient Psychiatric Facility" },
            { value: "09", label: "Hospice Home Care (Routine Home Care) Provided in a Hospice Facility" },
            { value: "99", label: "Not listed" },
          ]} />
        <FormSelect label="Admitted From" value={data.livingSituation?.admittedFrom} onChange={(v) => u("livingSituation.admittedFrom", v)}
          hopeCode="A1805" options={[
            { value: "01", label: "Home/Community (private home/apt., board/care, assisted living, group home, etc.)" },
            { value: "02", label: "Nursing Home (long-term care facility)" },
            { value: "03", label: "Skilled Nursing Facility (SNF, swing beds)" },
            { value: "04", label: "Short-Term General Hospital (acute hospital, IPPS)" },
            { value: "05", label: "Long-Term Care Hospital (LTCH)" },
            { value: "06", label: "Inpatient Rehabilitation Facility (IRF)" },
            { value: "07", label: "Inpatient Psychiatric Facility" },
            { value: "08", label: "Intermediate Care Facility (ID/DD facility)" },
            { value: "10", label: "Hospice (institutional facility)" },
            { value: "11", label: "Critical Access Hospital (CAH)" },
            { value: "99", label: "Not Listed" },
          ]} />
        <FormRadioGroup label="Living Arrangement" value={data.livingSituation?.livingArrangement} onChange={(v) => u("livingSituation.livingArrangement", v)}
          hopeCode="A1905" options={[
            { value: "1", label: "Alone (no other residents in the home)" },
            { value: "2", label: "With others in the home (family, friends, or paid caregiver)" },
            { value: "3", label: "Congregate home (e.g., assisted living or residential care home)" },
            { value: "4", label: "Inpatient facility (e.g., SNF, nursing home, inpatient hospice, hospital)" },
            { value: "5", label: "Does not have a permanent home (unstable housing / homeless)" },
          ]} />
        <FormRadioGroup label="Availability of Assistance" value={data.livingSituation?.availabilityOfAssistance} onChange={(v) => u("livingSituation.availabilityOfAssistance", v)}
          hopeCode="A1910" options={["24/7 available", "Daytime only", "Nighttime only", "Limited", "None"]} />
      </Card>
      )}

      {showPlanning && (
      <Card title="Advanced Care Planning" cms="F2000/F2100/F2200" id="advancedCarePlanning">
        <FormRadioGroup label="F2000: Was patient/responsible party asked about CPR preference?" value={data.advancedCarePlanning?.cprPreferenceAskedStatus}
          onChange={(v) => u("advancedCarePlanning.cprPreferenceAskedStatus", v)} hopeCode="F2000"
          options={[{ value: "0", label: "No" }, { value: "1", label: "Yes, and discussion occurred" }, { value: "2", label: "Yes, but refused to discuss" }]} />
        <FormRadioGroup label="Code Status" value={data.advancedCarePlanning?.codeStatus} onChange={(v) => u("advancedCarePlanning.codeStatus", v)}
          options={["Full Code", "DNR", "DNR-CC", "Comfort Measures Only"]} />
        <FormInput label="Code Status Discussion Date" value={data.advancedCarePlanning?.codeStatusDate}
          onChange={(v) => u("advancedCarePlanning.codeStatusDate", v)} type="date" />
        <FormRadioGroup label="F2100: Was patient/responsible party asked about other life-sustaining treatments?" value={data.advancedCarePlanning?.lifeSustainingAskedStatus}
          onChange={(v) => u("advancedCarePlanning.lifeSustainingAskedStatus", v)} hopeCode="F2100"
          options={[{ value: "0", label: "No" }, { value: "1", label: "Yes, and discussion occurred" }, { value: "2", label: "Yes, but refused to discuss" }]} />
        <FormRadioGroup label="Life-Sustaining Treatment Preference" value={data.advancedCarePlanning?.lifeSustainingTreatmentPreference}
          onChange={(v) => u("advancedCarePlanning.lifeSustainingTreatmentPreference", v)}
          options={["Yes — wants life-sustaining treatment", "No — does not want", "Undecided"]} />
        <FormInput label="Life-Sustaining Treatment Discussion Date" value={data.advancedCarePlanning?.lifeSustainingTreatmentPreferenceDate}
          onChange={(v) => u("advancedCarePlanning.lifeSustainingTreatmentPreferenceDate", v)} type="date" />
        <FormRadioGroup label="F2200: Was patient/responsible party asked about hospitalization preference?" value={data.advancedCarePlanning?.hospitalizationAskedStatus}
          onChange={(v) => u("advancedCarePlanning.hospitalizationAskedStatus", v)} hopeCode="F2200"
          options={[{ value: "0", label: "No" }, { value: "1", label: "Yes, and discussion occurred" }, { value: "2", label: "Yes, but refused to discuss" }]} />
        <FormRadioGroup label="Hospitalization Preference" value={data.advancedCarePlanning?.hospitalizationPreference}
          onChange={(v) => u("advancedCarePlanning.hospitalizationPreference", v)}
          options={["Yes — wants hospitalization", "No — does not want", "Undecided"]} />
        <FormInput label="Hospitalization Discussion Date" value={data.advancedCarePlanning?.hospitalizationPreferenceDate}
          onChange={(v) => u("advancedCarePlanning.hospitalizationPreferenceDate", v)} type="date" />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
          <FormInput label="Decision Maker" value={data.advancedCarePlanning?.decisionMaker} onChange={(v) => u("advancedCarePlanning.decisionMaker", v)} />
          <FormInput label="POA Name" value={data.advancedCarePlanning?.poaName} onChange={(v) => u("advancedCarePlanning.poaName", v)} />
          <FormInput label="POA Phone" value={data.advancedCarePlanning?.poaPhone} onChange={(v) => u("advancedCarePlanning.poaPhone", v)} type="tel" />
        </div>
        <FormCheckbox label="Advance Directive on File" checked={data.advancedCarePlanning?.advanceDirectiveOnFile} onChange={(v) => u("advancedCarePlanning.advanceDirectiveOnFile", v)} />
        <FormCheckbox label="POLST on File" checked={data.advancedCarePlanning?.polstOnFile} onChange={(v) => u("advancedCarePlanning.polstOnFile", v)} />
      </Card>
      )}
    </>
  );
}


// ── Generic Section Renderer ──
function calculateAgeFromDob(dobStr) {
  if (!dobStr) return null;
  const dob = new Date(dobStr);
  if (Number.isNaN(dob.getTime())) return null;
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const monthDiff = today.getMonth() - dob.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
    age -= 1;
  }
  return age;
}

// Body Systems density redesign (owner directive, 2026-09-26): the 10
// body-system modules render inside one compact accordion screen (see
// RNICACommandWorkspace.jsx bodySystems branch) -- within that screen,
// each module's own sub-cards (Mental Status, BIMS, Communication &
// Sensory, Skin Integrity, Pressure Injury, Wounds, ...) pack into a
// responsive 2-3 column "clinical review grid" instead of stacking full
// width, and default to collapsed (same `collapsible`/`defaultCollapsed`
// mechanism the Pain Assessment Tool card already uses) so the RN sees
// compact titles first and expands only what's relevant. Pilot-only;
// legacy/non-grouped rendering of these same sections is unaffected --
// no field, HOPE mapping, POC, or validation behavior changes.
const BODY_SYSTEM_FORM_SECTIONS = new Set(
  RNICA_BODY_SYSTEM_MODULES.map((module) => module.formSection),
);

// Body Systems 9-part nursing-workflow structure (owner directive: every
// system follows identical navigation so a nurse always knows where to
// look). Cards are tagged with one of these `category` values; a card
// with no explicit category defaults to "core" (see resolvedCards.map
// below) so nothing can silently fall out of the workspace. "summary" is
// synthetic (computed, not a real card) and "poc" is handled by the
// pre-existing PocSectionControls component, so neither appears here.
const BODY_SYSTEM_CATEGORY_ORDER = ["core", "symptoms", "functional", "disease", "treatments", "response", "observation"];
const BODY_SYSTEM_CATEGORY_LABELS = {
  core: "Core Findings",
  symptoms: "Symptom Impact",
  functional: "Functional Impact",
  disease: "Disease-Specific Findings",
  treatments: "Current Management",
  response: "Clinical Status Change",
  observation: "Nurse Observation",
};

// Deterministic, plain-language restatement of ALREADY-DOCUMENTED fields
// for a single body system (owner directive: "only include findings
// already documented... do not generate/infer/create findings"). Every
// line reads one specific, already-existing field and only appears when
// that field has a real charted value -- no new fields, nothing derived
// or predicted. Shared by the per-system "Summary" strip (Body Systems
// clinical-workflow layout) and the combined cross-system Structured
// Findings panel so the two never drift out of sync.
function computeBodySystemFindings(sectionKey, sectionData) {
  const findings = [];
  const d = sectionData || {};
  switch (sectionKey) {
    case "neurological": {
      if (d.consciousness && !["Alert", "Awake"].includes(d.consciousness)) {
        findings.push(`Level of consciousness: ${d.consciousness}.`);
      }
      if (d.orientation?.disoriented) findings.push(`Disoriented.`);
      // GitHub Review Major Issue #6 -- Sleep/Responsiveness and
      // Communication/Behavioral findings weren't surfacing in the
      // Structured Findings rail, making Neurological's own findings look
      // thin next to other systems. Neurological is already first in the
      // panel's fixed section order (see bodySystemsStructuredFindings);
      // this only enriches what that first section actually shows.
      if (d?.sleepRest?.changeSincePrior && d.sleepRest.changeSincePrior !== "No Change") {
        findings.push(`Sleep/responsiveness change: ${d.sleepRest.changeSincePrior}.`);
      } else if (d?.sleepRest?.responsiveness && !["Easily Aroused", ""].includes(d.sleepRest.responsiveness)) {
        // Display the clinical-finding noun ("Somnolence"), not the stored
        // legacy adjective value ("Somnolent") -- GitHub Directive
        // (2026-09-28) Major Concern #1/#2.
        const responsivenessDisplay = d.sleepRest.responsiveness === "Somnolent" ? "Somnolence" : d.sleepRest.responsiveness;
        findings.push(`Responsiveness: ${responsivenessDisplay}.`);
      }
      if (d.communication && !["Normal", "Clear", ""].includes(d.communication)) {
        findings.push(`Communication: ${d.communication}.`);
      }
      if (d.cognition) findings.push(`Cognitive status: ${d.cognition}.`);
      const bimsFields = [d?.hopeItems?.n0500, d?.hopeItems?.n0510, d?.hopeItems?.n0520];
      if (bimsFields.every((v) => v !== "" && v !== undefined && v !== null)) {
        const bimsSum = bimsFields.reduce((sum, v) => sum + parseInt(v, 10), 0);
        findings.push(`BIMS score: ${bimsSum}/9.`);
      }
      if (d.delirium) findings.push(`Delirium present.`);
      const behavioral = (d.symptomsDemeanor || []).filter((s) => s && s !== "Peaceful");
      if (behavioral.length > 0) findings.push(`Behavioral: ${behavioral.join(", ")}.`);
      if (d.motorDeficit) findings.push(`Motor deficit present${d.affectedSide ? ` (${d.affectedSide})` : ""}.`);
      if (d.balance && !["Steady", "Normal"].includes(d.balance)) findings.push(`Balance: ${d.balance}.`);
      break;
    }
    case "respiratory": {
      if (d.oxygenTherapy?.inUse) {
        const detail = [d.oxygenTherapy.litersPerMinute && `${d.oxygenTherapy.litersPerMinute} L/min`, d.oxygenTherapy.deliveryMode].filter(Boolean).join(", ");
        findings.push(`Continuous oxygen therapy in use${detail ? ` (${detail})` : ""}.`);
      }
      break;
    }
    case "cardiovascular": {
      if (d.chestPain?.present === "Yes") {
        findings.push(`Chest pain present${d.chestPain.type ? ` (${d.chestPain.type})` : ""}.`);
      }
      if (d.edema?.present === "Yes") {
        findings.push(`${d.edema.severity || "Edema"} documented${d.edema.location?.length ? ` (${d.edema.location.join(", ")})` : ""}.`);
      }
      if (d.syncope === "Yes") findings.push(`Syncope (fainting episodes) documented.`);
      if (d.dizziness && d.dizziness !== "None") findings.push(`Dizziness: ${d.dizziness}.`);
      if (d.fatigue && d.fatigue !== "None") findings.push(`Fatigue: ${d.fatigue}.`);
      // Owner directive (2026-09-28) "Cardiovascular Symptom-Focused Scope
      // Correction" -- Cardiovascular documents current signs/symptoms/
      // assessment findings, not disease/diagnosis conclusions. Heart
      // Failure is a diagnosis (owned by the HOPE I0600 comorbidity
      // workflow, auto-derived from coded Diagnosis, and by Diagnosis &
      // LCD/certification), so `heartFailurePresent`/`heartFailureType`
      // no longer drive Structured Findings. The raw fields are untouched
      // (never deleted/nulled) and remain visible read-only on Path 2 --
      // see the Path 2 legacy display block in the field-render loop.
      break;
    }
    case "skin": {
      if ((d.wounds || []).length > 0) {
        findings.push(`${d.wounds.length} active wound${d.wounds.length === 1 ? "" : "s"} documented — ongoing wound care oversight required.`);
      }
      if (d.skinColorFinding && d.skinColorFinding !== "Normal") findings.push(`Skin color: ${d.skinColorFinding}.`);
      if (d.skinTemperature && !["Warm", ""].includes(d.skinTemperature)) findings.push(`Skin temperature: ${d.skinTemperature}.`);
      if (d.skinMoisture && d.skinMoisture !== "Dry") findings.push(`Skin moisture: ${d.skinMoisture}.`);
      if (d.skinEdema?.severity && d.skinEdema.severity !== "None") {
        findings.push(`Skin edema: ${d.skinEdema.severity}${d.skinEdema.location ? ` (${d.skinEdema.location})` : ""}.`);
      }
      const additionalSkinFindings = (d.additionalSkinFindings || []).filter((f) => f && f !== "None");
      if (additionalSkinFindings.length > 0) findings.push(`Additional skin findings: ${additionalSkinFindings.join(", ")}.`);
      break;
    }
    case "gastrointestinal": {
      if (d.ostomy?.present) findings.push(`Ostomy present (${d.ostomy.type || "type not specified"}).`);
      if (d.feedingTube?.present) findings.push(`Feeding tube present (${d.feedingTube.type || "type not specified"}).`);
      break;
    }
    case "genitourinary": {
      if (d.catheter?.present) findings.push(`Urinary catheter present (${d.catheter.type || "type not specified"}).`);
      break;
    }
    case "nutrition": {
      if (d.weightLossPastSixMonths && !/^(none|no)$/i.test(d.weightLossPastSixMonths)) {
        findings.push(`Weight loss documented: ${d.weightLossPastSixMonths}.`);
      }
      break;
    }
    case "endocrine": {
      if (d.diabetes?.type && !["Not diabetic", "Unknown"].includes(d.diabetes.type)) {
        findings.push(`Diabetes (${d.diabetes.type})${d.diabetes.insulinType ? `, on insulin` : ""}.`);
      }
      break;
    }
    case "infection": {
      const activeInfections = (d.currentInfections || []).filter((i) => i && i !== "None");
      if (activeInfections.length > 0) findings.push(`Active infection: ${activeInfections.join(", ")}.`);
      break;
    }
    case "musculoskeletal": {
      if (d.weakness && d.weakness !== "None") findings.push(`Weakness: ${d.weakness}.`);
      if (d.paralysis && d.paralysis !== "None") findings.push(`Disability: ${d.paralysis}.`);
      if (d.contractures && d.contractures !== "None") {
        findings.push(`Contractures: ${d.contractures}${d.contracturesLocation?.length ? ` (${d.contracturesLocation.join(", ")})` : ""}.`);
      } else if (d.contracturesPresent) {
        findings.push(`Contractures present${d.contracturesLocation?.length ? ` (${d.contracturesLocation.join(", ")})` : ""}.`);
      }
      if (d.rigidity && d.rigidity !== "None") findings.push(`Rigidity: ${d.rigidity}.`);
      else if (d.rigidityPresent) findings.push(`Rigidity present.`);
      const fallsCount = parseInt(d.fallHistory?.fallsLast90Days, 10);
      if (Number.isFinite(fallsCount) && fallsCount > 0) {
        findings.push(`${fallsCount} fall${fallsCount === 1 ? "" : "s"} in last 90 days${d.fallHistory?.fallInjuries ? ` (${d.fallHistory.fallInjuries})` : ""}.`);
      }
      break;
    }
    default:
      break;
  }
  return findings;
}

// GitHub Directive (2026-09-28) Critical Finding #7 -- blank documentation
// must never be presented as "no significant findings" (that implies an
// active assessment was performed and came back normal). Deep-walks the
// section's stored data; only once at least one field has actually been
// touched does the "no significant findings" / "findings present" status
// apply. Generic across all Body Systems sections (same defect could occur
// anywhere computeBodySystemSummary is used), not a neurological-only patch.
function hasAnyDocumentedValue(value) {
  if (value == null) return false;
  if (typeof value === "boolean") return value === true;
  if (typeof value === "string") return value.trim() !== "";
  if (typeof value === "number") return Number.isFinite(value);
  if (Array.isArray(value)) return value.some(hasAnyDocumentedValue);
  if (typeof value === "object") return Object.values(value).some(hasAnyDocumentedValue);
  return false;
}

// GitHub Review Major Issue #5 -- the generic "Findings Present" Summary
// status reads as a warning banner, not a clinical picture. For
// Neurological only, composes a short, plain-language narrative from
// fields the nurse has actually already selected (consciousness,
// orientation, sleep/responsiveness change, communication, motor deficit,
// behavioral symptoms, overall clinical status change) -- every clause
// reads one existing field and is omitted when that field is blank; never
// infers, predicts, or compares against a prior visit beyond the nurse's
// own "Change Since Prior" selection. Scoped to sectionKey ===
// "neurological" only so every other Body System's Summary behavior is
// untouched.
const NEURO_CONSCIOUSNESS_ALIASES = { Awake: "Alert", Coma: "Comatose" };

// OWNER DIRECTIVE (2026-09-28) "Clinical Blocker -- Consciousness Model" --
// Awake and Alert are distinct neurological concepts (a patient may be
// awake but not alert, e.g. dementia/delirium/encephalopathy/end-of-life
// decline). The stored canonical value stays "Alert" (no schema/migration
// change, no historical rewrite), but display text -- both the option
// label and every narrative clause -- now reads "Awake" only. The
// narrative must never assert "Alert" unless Alertness is independently
// documented, and no separate Alertness field exists yet, so "Alert" is
// never emitted.
const NEURO_CONSCIOUSNESS_DISPLAY = { Alert: "Awake" };

// GitHub Directive (2026-09-28) "Neurological Review -- Average Sleep
// Hours, Clinical Relevance, and Final Density Refinement" Issue #2 --
// "Overall Change" must always resolve to an explicit clinical sentence
// (stable AND declining both need to say so), not be silently dropped
// whenever it isn't the single "no change" baseline value. One phrase
// per NEURO_OVERALL_CHANGE_OPTIONS value; kept next to that constant's
// definition in spirit but colocated here where it's consumed.
const NEURO_OVERALL_CHANGE_NARRATIVE = {
  "Initial Assessment": "Initial neurological assessment; no prior comparison available.",
  "No Significant Change": "No neurological decline documented.",
  "Improved": "Neurological status improved since prior assessment.",
  "Gradual Decline": "Gradual neurological decline documented.",
  "New or Worsening Concern": "New or worsening neurological concern documented.",
  "Fluctuating": "Neurological status fluctuating.",
  "Unable to Compare": "Unable to compare to prior neurological assessment.",
};

export function computeNeurologicalNarrative(d) {
  const clauses = [];

  // Bounded Compatibility Increment (2026-09-28) Section 7/AC-02 -- when
  // the nurse can't complete the assessment, the summary must say ONLY
  // that (plus the controlled reason) as two short sentences, and must
  // never add an unrelated clinical clause (e.g. Communication) just
  // because the Overview path was set to Unable to Assess. Independently
  // documented findings on OTHER fields are not read here at all -- this
  // is an intentional early return, not a filter.
  if (d.neuroOverview === "Unable to Assess") {
    const reason = d.neuroUnableToAssessReason === "Other" && d.neuroUnableToAssessOther
      ? d.neuroUnableToAssessOther
      : d.neuroUnableToAssessReason;
    return reason
      ? `Neurological assessment unable to complete. Reason: ${reason}.`
      : "Neurological assessment unable to complete.";
  }

  const consciousnessCanonical = NEURO_CONSCIOUSNESS_ALIASES[d.consciousness] || d.consciousness;
  const consciousnessDisplay = NEURO_CONSCIOUSNESS_DISPLAY[consciousnessCanonical] || consciousnessCanonical;
  if (consciousnessDisplay) clauses.push(`${consciousnessDisplay}.`);

  const o = d.orientation || {};
  if (o.disoriented) {
    clauses.push("Disoriented.");
  } else {
    const orientedTo = [o.person && "person", o.place && "place", o.time && "time", o.situation && "situation"].filter(Boolean);
    if (orientedTo.length === 4) clauses.push("Oriented x4.");
    else if (orientedTo.length > 0) clauses.push(`Oriented to ${orientedTo.join(", ")}.`);
  }

  // Issue #2/#10 -- Sleep/Responsiveness is the strongest section of the
  // page and the summary must reflect it every time it's documented, not
  // only when abnormal, so "Normal sleep pattern. Easily aroused." reads
  // as clearly as any decline sentence.
  const sleep = d.sleepRest || {};
  const sleepChangeText = {
    "Sleeping More": "Sleeping more than prior assessment.",
    "Increased Somnolence": "Increased somnolence since prior assessment.",
    "More Difficult To Arouse": "More difficult to arouse since prior assessment.",
    "New Unresponsiveness": "New unresponsiveness since prior assessment.",
  };
  if (sleep.changeSincePrior && sleepChangeText[sleep.changeSincePrior]) {
    clauses.push(sleepChangeText[sleep.changeSincePrior]);
  } else if (sleep.sleepPattern) {
    clauses.push(sleep.sleepPattern === "Normal" ? "Usual sleep pattern." : `Sleep pattern: ${sleep.sleepPattern}.`);
  }
  const responsivenessText = {
    "Easily Aroused": "Easily aroused.",
    // GitHub Directive (2026-09-28) "Neurological Review -- Major Success,
    // But We Are Drifting..." Major Concern #1 -- narrate the clinical
    // finding ("Somnolence documented."), not an adjective describing the
    // patient ("Patient somnolent."). Stored value is unchanged (still
    // "Somnolent" -- see the option's {value,label} split below), so this
    // is a display-only rewording.
    Somnolent: "Somnolence documented.",
    "Difficult To Arouse": "Difficult to arouse.",
    "Minimally Responsive": "Minimally responsive.",
    Unresponsive: "Unresponsive.",
    "Unable to assess": "Responsiveness unable to assess.",
  };
  if (sleep.responsiveness && responsivenessText[sleep.responsiveness]) {
    clauses.push(responsivenessText[sleep.responsiveness]);
  }

  if (d.communication && !["Normal", "Clear", ""].includes(d.communication)) {
    clauses.push("Communication limited.");
  } else if (d.communication === "Normal" || d.communication === "Clear") {
    // GitHub Directive (2026-09-28) "Neurological Overview Gate" Section
    // 18 example -- only say "no concern" when the nurse deliberately
    // selected the no-concern value, never inferred from a blank field.
    clauses.push("No current communication concern identified.");
  }
  if (d.hearing && d.hearing !== "Adequate") {
    clauses.push(`Hearing: ${d.hearing}.`);
  }
  if (d.vision && d.vision !== "Adequate") {
    clauses.push(`Vision: ${d.vision}.`);
  }
  const sensoryDeficits = (d.sensoryDeficits || []).filter(Boolean);
  if (sensoryDeficits.length > 0) {
    clauses.push(`Sensory deficits: ${sensoryDeficits.join(", ")}.`);
  }

  // Issue #7 -- Motor Status is now a 3-state primary control (None
  // Identified / Present / Unable to Assess). Legacy records that only
  // ever set the boolean `motorDeficit` (never the new `motorStatus`
  // path) still narrate correctly via the same fallback used for display.
  const motorPresent = d.motorStatus === "Present" || (d.motorStatus === undefined && d.motorDeficit === true);
  if (motorPresent) {
    clauses.push(`Motor deficit present${d.affectedSide ? ` (${d.affectedSide})` : ""}.`);
  } else if (d.motorStatus === "Unable to Assess") {
    clauses.push("Motor status unable to assess.");
  } else if (d.motorStatus === "None Identified") {
    clauses.push("No motor deficit identified.");
  } else if (d.motorBalanceStatus === "No New Concern") {
    clauses.push("No new motor or balance concern identified.");
  } else if (d.motorBalanceStatus === "Patient Does Not Ambulate") {
    clauses.push("Patient does not ambulate.");
  }

  // Issue #2 -- "reflect only documented items": a never-touched field
  // must not generate a fabricated "no concerns" sentence (that's an
  // inferred-normal-from-blank-data error, not a documented finding). Only
  // emit a clause when the nurse has actually selected something, and
  // treat "Peaceful" as its own documented (reassuring) finding rather
  // than silently discarding it.
  const behavioralAll = (d.symptomsDemeanor || []).filter(Boolean);
  if (behavioralAll.length > 0) {
    const concerns = behavioralAll.filter((s) => s !== "Peaceful");
    clauses.push(concerns.length > 0 ? `Behavioral: ${concerns.join(", ")}.` : "Peaceful / calm mood documented.");
  } else if (d.behavioralStatus === "No Current Concern") {
    clauses.push("No behavioral concern identified.");
  }

  if (d.clinicalStatusChange && NEURO_OVERALL_CHANGE_NARRATIVE[d.clinicalStatusChange]) {
    clauses.push(NEURO_OVERALL_CHANGE_NARRATIVE[d.clinicalStatusChange]);
  }

  return clauses.join(" ");
}

// Bounded Compatibility Increment (2026-09-28) Section 9/21/AC-04 -- a
// deliberately conservative, deterministic proxy for "a confirmed
// current actionable finding exists" so the always-visible generic
// "+ Add to POC" button can become conditional without a new POC-
// candidate engine. Every check below reads an already-documented,
// explicitly-selected value; nothing here is inferred from blank data
// or generated from the Overview Gate choice itself.
export function neurologicalHasActionablePocFinding(d) {
  const sleep = d.sleepRest || {};
  if (["Sleeping More", "Increased Somnolence", "More Difficult To Arouse", "New Unresponsiveness"].includes(sleep.changeSincePrior)) return true;
  if (["Somnolent", "Difficult To Arouse", "Minimally Responsive", "Unresponsive"].includes(sleep.responsiveness)) return true;
  if (d.communication && !["Normal", "Clear", ""].includes(d.communication)) return true;
  const behavioralConcerns = (d.symptomsDemeanor || []).filter((s) => s && s !== "Peaceful");
  if (behavioralConcerns.length > 0) return true;
  if (d.delirium === true || d.delirium === "Yes") return true;
  if (d.seizureHistory && d.seizureHistory !== "None" && d.seizureHistory !== "") return true;
  const motorPresent = d.motorStatus === "Present" || (d.motorStatus === undefined && d.motorDeficit === true);
  if (motorPresent) return true;
  if (["Gradual Decline", "New or Worsening Concern"].includes(d.clinicalStatusChange)) return true;
  return false;
}

// Bounded Compatibility Increment (2026-09-28) Section 5/AC-03 -- honest,
// bounded workflow status for the Neurological accordion badge. Does NOT
// attempt full "applicable required item" completeness validation (that
// would require the official HOPE validation engine explicitly deferred
// in Section 17/19) -- it only distinguishes the states this bounded
// pass can actually determine: unset vs. Unable-to-Assess vs. "something
// beyond the Overview answer itself has been documented."
export function computeNeurologicalWorkflowStatus(d) {
  const overview = d.neuroOverview;
  if (!overview) {
    return hasAnyDocumentedValue(d)
      ? { code: "in_progress", label: "In Progress", variant: "neutral" }
      : { code: "not_started", label: "Not Started", variant: "neutral" };
  }
  if (overview === "Unable to Assess") {
    // An incomplete assessment always needs follow-up -- never "reviewed",
    // regardless of whether the controlled reason itself is filled in yet.
    return { code: "review_required", label: "Review Required", variant: "warning" };
  }
  const { neuroOverview: _o, ...rest } = d;
  return hasAnyDocumentedValue(rest)
    ? { code: "ready_for_review", label: "Ready for Review", variant: "success" }
    : { code: "in_progress", label: "In Progress", variant: "neutral" };
}

// OWNER-DIRECTED "Cardiovascular Overview Gate" (2026-09-28, Contradiction
// 6) -- legacy `pulseQuality` was a single combined value conflating
// Rhythm/Rate/Strength (the Cardiovascular equivalent of Neurological's
// "Awake / Alert" problem). Each legacy value belongs to exactly one of
// the three new independent dimensions; the other two dimensions are
// left unanswered rather than backfilled/inferred, per the directive
// ("Do not infer missing dimensions... Do not backfill Normal rate,
// Regular rhythm, Strong strength from one legacy value").
const PULSE_LEGACY_DIMENSION = {
  Regular: { dimension: "pulseRhythm", display: "Regular" },
  Irregular: { dimension: "pulseRhythm", display: "Irregular" },
  Tachycardia: { dimension: "pulseRate", display: "Tachycardic" },
  Bradycardia: { dimension: "pulseRate", display: "Bradycardic" },
  Strong: { dimension: "pulseStrength", display: "Strong" },
  Weak: { dimension: "pulseStrength", display: "Weak" },
  Thready: { dimension: "pulseStrength", display: "Thready" },
  Bounding: { dimension: "pulseStrength", display: "Bounding" },
  Absent: { dimension: "pulseStrength", display: "Absent" },
};

// Read-only alias resolver: returns the display value for one of the
// three new pulse dimension fields, falling back to the legacy
// `pulseQuality` value ONLY when it maps to that exact dimension and the
// new field itself is still blank. Never writes to storage -- storage is
// only ever written when the clinician interacts with a control.
export function resolvePulseDimensionDisplay(d, dimension) {
  const current = d[dimension];
  if (current) return current;
  const legacy = PULSE_LEGACY_DIMENSION[d.pulseQuality];
  return legacy && legacy.dimension === dimension ? legacy.display : "";
}

const BP_STATUS_LEGACY_VALUES = ["Normal", "Hypertensive", "Hypotensive"];

// OWNER-DIRECTED (2026-09-28, Contradiction 4) -- legacy `bpSymptoms` was
// a multi-select array that could (and, per the directive, sometimes
// does) hold contradictory combinations (e.g. "Normal" + "Hypertensive").
// This never silently picks a "first" or "most severe" value: an
// unambiguous single legacy status value is alias-displayed; a
// contradictory legacy array is surfaced as `reviewRequired` (rendered as
// a read-only note in the narrative/findings, never auto-resolved).
export function resolveBpLegacyDisplay(d) {
  const legacy = Array.isArray(d.bpSymptoms) ? d.bpSymptoms : [];
  const statusValues = legacy.filter((v) => BP_STATUS_LEGACY_VALUES.includes(v));
  const contradictory = statusValues.length > 1;
  return {
    statusDisplay: !contradictory && statusValues.length === 1 ? statusValues[0] : "",
    orthostaticDisplay: legacy.includes("Orthostatic") ? "Present" : "",
    reviewRequired: contradictory,
    legacyValues: legacy,
  };
}

export function resolveBpStatusDisplay(d) {
  return d.bpStatus || resolveBpLegacyDisplay(d).statusDisplay;
}

export function resolveOrthostaticFindingDisplay(d) {
  return d.orthostaticFinding || resolveBpLegacyDisplay(d).orthostaticDisplay;
}

// OWNER-DIRECTED "Dyspnea Ownership Model" (2026-09-28, Contradiction 5)
// -- Respiratory owns the dyspnea symptom/severity; Cardiovascular owns
// only the cardiac-cause attribution. Returns a state, not a boolean, so
// the render loop and narrative can distinguish "hidden, nothing to
// preserve" from "hidden, but a legacy value must be preserved and
// flagged" without ever silently clearing a legacy value.
export function resolveCardiacDyspneaGate(cardiovascularData, respiratoryData) {
  const sobSeverity = (respiratoryData || {}).sobSeverity;
  const hasLegacyValue = cardiovascularData.cardiacDyspnea === true;
  if (sobSeverity && sobSeverity !== "None") {
    return { visible: true, reviewRequired: false, guidance: "" };
  }
  if (hasLegacyValue) {
    // Respiratory is blank or negative but a value already exists here --
    // never auto-cleared, never silently rewritten; flagged for review.
    return { visible: true, reviewRequired: true, guidance: "" };
  }
  if (!sobSeverity) {
    return { visible: false, reviewRequired: false, guidance: "Document dyspnea in Respiratory before assigning cardiac attribution." };
  }
  // sobSeverity === "None": Respiratory has explicitly documented no
  // dyspnea, so no NEW cardiac attribution may be started.
  return { visible: false, reviewRequired: false, guidance: "" };
}

// Owner directive (2026-09-28) "Correct the Overview Label" -- the
// approved exact wording is "New or Worsening Cardiovascular Findings"
// (not the slash-joined "New/Worsening..."). Historical records already
// saved with the old slash wording are never rewritten; every place that
// compares against this option normalizes through this helper first so
// both spellings are always treated identically.
const CV_OVERVIEW_NEW_OR_WORSENING = "New or Worsening Cardiovascular Findings";
const CV_OVERVIEW_NEW_OR_WORSENING_LEGACY = "New/Worsening Cardiovascular Findings";
function normalizeCardiovascularOverview(value) {
  return value === CV_OVERVIEW_NEW_OR_WORSENING_LEGACY ? CV_OVERVIEW_NEW_OR_WORSENING : value;
}

// Bounded Compatibility Increment (2026-09-28) Section 9/21/AC-04 --
// Cardiovascular counterpart to neurologicalHasActionablePocFinding.
// OWNER CORRECTION (Contradiction 7): a chronic/stable finding (e.g.
// Heart Failure Present alone, on the "Existing Findings Review" path)
// must NOT trigger POC review by itself -- only the explicit
// always-actionable list, clinically-significant thresholds, and the
// New/Worsening path itself do.
export function cardiovascularHasActionablePocFinding(d) {
  const overview = normalizeCardiovascularOverview(d.cardiovascularOverview);
  if (overview === "Unable to Assess") return false;
  if (overview === CV_OVERVIEW_NEW_OR_WORSENING) return true;
  if (d.chestPain?.present === "Yes") return true;
  if (d.syncope === "Yes") return true;
  // Both the legacy shared-option string ("New Symptom Since Prior
  // Assessment") and the new Cardiovascular-approved string ("New or
  // Worsening Finding") must trigger this -- a record charted under
  // either option set is never treated as less actionable than the other.
  if (["Declining", "New Symptom Since Prior Assessment", "New or Worsening Finding"].includes(d.clinicalStatusChange)) return true;
  if (d.edema?.present === "Yes" && ["3+", "4+"].includes(d.edema?.severity)) return true;
  if (["Thready", "Absent"].includes(resolvePulseDimensionDisplay(d, "pulseStrength"))) return true;
  if (d.cardiacDyspnea === true) return true;
  return false;
}

// FIX (2026-09-28, live-UI audit): "No Current Cardiovascular Concern"
// must not be confirmable while an abnormal finding is already stored on
// the record (e.g. a legacy/preserved chest pain, edema, or heart
// failure value from before this Overview Gate existed). Confirming "no
// concern" over an unreviewed abnormal finding is a genuine contradiction
// -- the record cannot simultaneously assert "no current concern" and
// carry an unresolved abnormal finding. This never clears or rewrites
// those preserved values; it only blocks the No-Concern path from
// reaching Ready for Review until the clinician reviews/resolves them
// (by switching path, editing the finding, etc.).
export function cardiovascularHasPreservedAbnormalFinding(d) {
  if (d.chestPain?.present === "Yes") return true;
  if (d.edema?.present === "Yes") return true;
  // Owner directive (2026-09-28) "Cardiovascular Symptom-Focused Scope
  // Correction" -- hospice body-system assessments document current
  // signs/symptoms/findings for comfort/symptom management, not disease
  // conclusions. `heartFailurePresent` is a diagnosis flag, not a
  // symptom, so it no longer drives this conflict check; the actual
  // symptoms hospice cares about (edema, dyspnea attribution, chest
  // pain, abnormal BP/pulse, syncope) already trigger it independently.
  if (d.syncope === "Yes") return true;
  if (d.cardiacDyspnea === true) return true;
  if (d.dizziness && d.dizziness !== "None") return true;
  if (resolveBpLegacyDisplay(d).reviewRequired) return true;
  const abnormalBp = resolveBpStatusDisplay(d);
  if (abnormalBp && abnormalBp !== "Normal" && abnormalBp !== "Unable to assess") return true;
  const abnormalPulse = [
    resolvePulseDimensionDisplay(d, "pulseRhythm"),
    resolvePulseDimensionDisplay(d, "pulseRate"),
    resolvePulseDimensionDisplay(d, "pulseStrength"),
  ];
  if (abnormalPulse.includes("Irregular")) return true;
  if (["Tachycardic", "Bradycardic"].includes(abnormalPulse[1])) return true;
  if (["Weak", "Thready", "Bounding", "Absent"].includes(abnormalPulse[2])) return true;
  return false;
}

// Directive (2026-09-28) "Cardiovascular Layout Consolidation" Section 14
// -- data inspection (SFV registry CV_HEART_FAILURE_SYSTOLIC/DIASTOLIC
// both use `multi_add`, and mixed systolic+diastolic heart failure is a
// real clinical presentation) confirms Heart Failure Type stays
// multi-select. The only genuine contradiction is "Unspecified"
// coexisting with a specific type, so selecting Unspecified clears the
// specific types, and selecting a specific type clears Unspecified --
// Systolic + Diastolic together are never mutually exclusive with each
// other. `prevArray`/`nextArray` are the value before/after the raw
// FormPillGroup toggle; returns the corrected array to write, or `null`
// when no correction is needed (the raw toggle already stands).
export function resolveHeartFailureTypeSelection(prevArray, nextArray) {
  const prev = Array.isArray(prevArray) ? prevArray : [];
  const next = Array.isArray(nextArray) ? nextArray : [];
  const addedUnspecified = next.includes("Unspecified") && !prev.includes("Unspecified");
  if (addedUnspecified) return ["Unspecified"];
  if (next.includes("Unspecified") && (next.includes("Systolic") || next.includes("Diastolic"))) {
    return next.filter((t) => t !== "Unspecified");
  }
  return null;
}

// Bounded Compatibility Increment (2026-09-28) Section 5/AC-03 --
// Cardiovascular counterpart to computeNeurologicalWorkflowStatus.
//
// CORRECTION (2026-09-28, audit): "Unable to Assess" is Review Required
// only while genuinely UNRESOLVED -- no reason selected, "Other" selected
// without an explanation, or a preserved legacy value that conflicts with
// the path (BP contradiction, or a legacy cardiac-dyspnea attribution the
// current Respiratory state no longer supports). A completed Unable To
// Assess path (approved reason, or Other + explanation, with no
// conflict) reaches Ready for Review like every other path -- it must
// never be forced to Review Required by the path selection alone.
// `respiratoryData` is optional (undefined when the caller has no access
// to the sibling section) and only affects the dyspnea-conflict check.
export function computeCardiovascularWorkflowStatus(d, respiratoryData) {
  const overview = normalizeCardiovascularOverview(d.cardiovascularOverview);
  if (!overview) {
    return hasAnyDocumentedValue(d)
      ? { code: "in_progress", label: "In Progress", variant: "neutral" }
      : { code: "not_started", label: "Not Started", variant: "neutral" };
  }
  if (overview === "Unable to Assess") {
    const reason = d.cardiovascularUnableToAssessReason;
    const unresolved =
      !reason ||
      (reason === "Other" && !d.cardiovascularUnableToAssessOther) ||
      resolveBpLegacyDisplay(d).reviewRequired ||
      resolveCardiacDyspneaGate(d, respiratoryData).reviewRequired;
    return unresolved
      ? { code: "review_required", label: "Review Required", variant: "warning" }
      : { code: "ready_for_review", label: "Ready for Review", variant: "success" };
  }
  // FIX (2026-09-28, live-UI audit): "No Current Cardiovascular Concern"
  // has its own required-field set (Pulse Rhythm/Rate/Strength +
  // Clinical Status Change) and its own conflict rule -- it must never
  // fall through to the generic "any documented value => ready" rule
  // below, which would let an unrelated preserved abnormal finding (or
  // even the Path 1 fields themselves) silently mark it Ready for
  // Review while contradicting findings sit unresolved.
  if (overview === "No Current Cardiovascular Concern") {
    if (cardiovascularHasPreservedAbnormalFinding(d)) {
      return { code: "review_required", label: "Review Required", variant: "warning" };
    }
    const rhythm = resolvePulseDimensionDisplay(d, "pulseRhythm");
    const rate = resolvePulseDimensionDisplay(d, "pulseRate");
    const strength = resolvePulseDimensionDisplay(d, "pulseStrength");
    const complete = Boolean(rhythm && rate && strength && d.clinicalStatusChange);
    return complete
      ? { code: "ready_for_review", label: "Ready for Review", variant: "success" }
      : { code: "in_progress", label: "In Progress", variant: "neutral" };
  }
  // Directive (2026-09-28) Section 11 "Path 3 plus No Significant
  // Change": documenting New/Worsening Cardiovascular Findings while
  // Clinical Status Change simultaneously claims stability is an
  // internal contradiction that must surface for review, not silently
  // pass through as Ready for Review.
  if (
    overview === CV_OVERVIEW_NEW_OR_WORSENING &&
    ["Stable / No Change", "No Significant Change"].includes(d.clinicalStatusChange)
  ) {
    return { code: "review_required", label: "Review Required", variant: "warning" };
  }
  // Directive (2026-09-28) Section 11/13: Path 2 ("Existing Cardiovascular
  // Findings Review") requires the clinician confirmation plus a current
  // Clinical Status Change selection before it can be Ready for Review --
  // reviewing stored findings without acting on them is In Progress, not
  // done.
  if (overview === "Existing Cardiovascular Findings Review") {
    const complete = Boolean(d.cardiovascularFindingsConfirmedThisVisit && d.clinicalStatusChange);
    return complete
      ? { code: "ready_for_review", label: "Ready for Review", variant: "success" }
      : { code: "in_progress", label: "In Progress", variant: "neutral" };
  }
  const { cardiovascularOverview: _o, ...rest } = d;
  return hasAnyDocumentedValue(rest)
    ? { code: "ready_for_review", label: "Ready for Review", variant: "success" }
    : { code: "in_progress", label: "In Progress", variant: "neutral" };
}

// OWNER-DIRECTED Cardiovascular narrative (2026-09-28). Mirrors
// computeNeurologicalNarrative's contract exactly: returns "" (falsy)
// when nothing path-specific applies, letting computeBodySystemSummary's
// existing generic fallback take over -- never infers a diagnosis,
// normal finding, or stability from the Overview selection alone.
export function computeCardiovascularNarrative(d) {
  const overview = normalizeCardiovascularOverview(d.cardiovascularOverview);
  if (!overview) return "";

  if (overview === "Unable to Assess") {
    const reason = d.cardiovascularUnableToAssessReason === "Other"
      ? d.cardiovascularUnableToAssessOther
      : d.cardiovascularUnableToAssessReason;
    return reason ? `Cardiovascular assessment unable to complete. Reason: ${reason}.` : "";
  }

  if (overview === "No Current Cardiovascular Concern") {
    // FIX (2026-09-28, live-UI audit): surface the conflict explicitly
    // instead of falling through to the generic "Findings Present"
    // fallback, which incorrectly implied the section had assessed and
    // found abnormal cardiovascular findings under a "no concern" path.
    if (cardiovascularHasPreservedAbnormalFinding(d)) {
      return "Stored cardiovascular findings require review before No Current Cardiovascular Concern can be confirmed.";
    }
    const rhythm = resolvePulseDimensionDisplay(d, "pulseRhythm");
    const rate = resolvePulseDimensionDisplay(d, "pulseRate");
    const strength = resolvePulseDimensionDisplay(d, "pulseStrength");
    // Owner directive: this exact sentence is only allowed once ALL
    // required normal-path selections are complete -- not from the
    // Overview answer alone.
    if (rhythm && rate && strength && d.clinicalStatusChange) {
      return "No current cardiovascular concern identified.";
    }
    return "";
  }

  const clauses = [];
  const bpStatusDisplay = resolveBpStatusDisplay(d);
  const orthostaticDisplay = resolveOrthostaticFindingDisplay(d);
  const bpLegacy = resolveBpLegacyDisplay(d);

  if (overview === "Existing Cardiovascular Findings Review") {
    // Accept both the legacy shared option and the new Cardiovascular-
    // approved option -- a record charted under either renders the same
    // stability language; neither string is rewritten.
    if (["Stable / No Change", "No Significant Change"].includes(d.clinicalStatusChange)) {
      clauses.push("Cardiovascular findings documented as stable/no significant change.");
    } else {
      clauses.push("Cardiovascular findings documented.");
    }
  }

  if (overview === CV_OVERVIEW_NEW_OR_WORSENING) {
    const pulseDims = [];
    const rhythm = resolvePulseDimensionDisplay(d, "pulseRhythm");
    const rate = resolvePulseDimensionDisplay(d, "pulseRate");
    const strength = resolvePulseDimensionDisplay(d, "pulseStrength");
    if (rhythm === "Irregular") pulseDims.push("irregular");
    if (rate && rate !== "Normal" && rate !== "Unable to assess") pulseDims.push(rate.toLowerCase());
    if (strength && !["Strong", "Unable to assess"].includes(strength)) pulseDims.push(strength.toLowerCase());
    if (pulseDims.length > 0) {
      clauses.push(`Pulse ${pulseDims.join(", ")}.`);
    }
    if (d.chestPain?.present === "Yes") {
      clauses.push(d.chestPain?.type ? `Chest pain present: ${d.chestPain.type}.` : "Chest pain present.");
    }
    if (d.edema?.present === "Yes") {
      const severity = d.edema?.severity ? `${d.edema.severity} ` : "";
      const location = Array.isArray(d.edema?.location) && d.edema.location.length > 0 ? d.edema.location.join(", ").toLowerCase() : "";
      clauses.push(`${severity}${location ? location + " " : ""}edema documented.`.trim().replace(/^\w/, (c) => c.toUpperCase()));
    }
    if (bpStatusDisplay && bpStatusDisplay !== "Normal" && bpStatusDisplay !== "Unable to assess") {
      clauses.push(`BP status: ${bpStatusDisplay.toLowerCase()}.`);
    }
    if (orthostaticDisplay === "Present") {
      clauses.push("Orthostatic finding present.");
    }
    if (d.dizziness && d.dizziness !== "None") clauses.push(`Dizziness: ${d.dizziness.toLowerCase()}.`);
    if (d.fatigue && d.fatigue !== "None") clauses.push(`Fatigue: ${d.fatigue.toLowerCase()}.`);
    if (d.syncope === "Yes") clauses.push("Syncope documented.");
    if (d.cardiacDyspnea === true) clauses.push("Dyspnea attributed to cardiac condition.");
    // Owner directive (2026-09-28) "Cardiovascular Symptom-Focused Scope
    // Correction" -- Heart Failure is a diagnosis, not a current
    // sign/symptom/assessment finding; it no longer drives the current
    // narrative/summary. `heartFailurePresent` is preserved untouched and
    // shown read-only on Path 2 only (see field-render loop).
  }

  if (bpLegacy.reviewRequired) {
    clauses.push(`Legacy BP values on record (${bpLegacy.legacyValues.join(", ")}) -- review required.`);
  }

  return clauses.join(" ");
}

// second, drifting source of truth. Deliberately does NOT include a
// "Changes Since Prior" line -- no prior-assessment/longitudinal-diff
// infrastructure exists yet anywhere in RNICA (confirmed: no
// priorAssessment/sincePrior/priorVisit concept in this file), so that
// would have to be guessed or fabricated. Omitted here pending real
// longitudinal infrastructure, not silently dropped -- see the Body
// Systems completion summary of work. Neurological is the one exception:
// its "Change Since Prior" fields (sleepRest.changeSincePrior,
// clinicalStatusChange) are nurse-selected charted values, not a computed
// diff, so computeNeurologicalNarrative may read them directly.
//
// (Comment continues from "Computed Summary panel for the Body Systems
// 9-part structure. Reuses computeBodySystemFindings (the same
// deterministic, already-documented-only findings list used elsewhere)
// so the Summary never introduces a" -- split by an earlier edit that
// inserted the Bounded Compatibility Increment helpers above.)
function computeBodySystemSummary(sectionKey, sectionData) {
  const primaryIssues = computeBodySystemFindings(sectionKey, sectionData);
  if (!hasAnyDocumentedValue(sectionData)) {
    if (sectionKey === "cardiovascular") {
      // Owner-required exact wording (2026-09-28) -- distinct casing from
      // the generic label-based fallback below; must never be confused
      // with the explicit "No current cardiovascular concern identified."
      // sentence, which requires a completed normal-path selection.
      return { status: "Cardiovascular assessment not yet documented.", primaryIssues, requiresFollowUp: false };
    }
    const label = sectionKey ? sectionKey.charAt(0).toUpperCase() + sectionKey.slice(1) : "This section's";
    return {
      status: `${label} Assessment Not Yet Documented`,
      primaryIssues,
      requiresFollowUp: false,
    };
  }
  if (sectionKey === "neurological") {
    const narrative = computeNeurologicalNarrative(sectionData || {});
    return {
      status: narrative || (primaryIssues.length > 0 ? "Findings Present" : "No Significant Findings Documented"),
      primaryIssues,
      requiresFollowUp: primaryIssues.length > 0,
    };
  }
  if (sectionKey === "cardiovascular") {
    const narrative = computeCardiovascularNarrative(sectionData || {});
    return {
      status: narrative || (primaryIssues.length > 0 ? "Findings Present" : "No Significant Findings Documented"),
      primaryIssues,
      requiresFollowUp: primaryIssues.length > 0,
    };
  }
  return {
    status: primaryIssues.length > 0 ? "Findings Present" : "No Significant Findings Documented",
    primaryIssues,
    requiresFollowUp: primaryIssues.length > 0,
  };
}

// Owner directive (2026-09-28) "New Cardiovascular Defect -- one-way
// segmented selections": Cardiovascular Path 2 only shows fields that are
// already "documented" (see the guard inside renderGenericSection below).
// Now that segmented pills can be cleared back to "" by re-clicking the
// selected option, that live documented-check would make a field vanish
// the moment it's cleared. This module-level cache (keyed by
// `${assessmentId}::${fieldPath}`) remembers which fields have been shown
// at least once during this browser session so clearing a value never
// hides its own control. It never reads or writes any stored field value
// -- purely a render-visibility memo, reset naturally on full page reload.
const cvPath2EverDocumentedFields = new Map();

function renderGenericSection(sectionKey, data, update, config, demographics, fullFormData, COLORS, styles, patientId, assessmentId, locked, workspacePilot = false, onNavigateToSection = undefined, uiProfile = {}) {
  const u = (path, val) => update(sectionKey, path, val);
  const { title, subtitle, cards } = config;
  const resolvedCards = uiProfile.hideSpiritualHopeFields && sectionKey === "spiritual"
    ? (cards || []).map((card) => ({
        ...card,
        fields: (card.fields || []).filter((field) => !["concernsAskedStatus", "concernsDiscussedDate"].includes(field.path)),
      }))
    : cards;

  // Every clinical assessment section where an RN finding can turn into a
  // Plan of Care problem gets Add/View/Update/Resolve POC controls on each
  // field-based subcard (matches the legacy vendor system's per-focus-area
  // "Add Issue" / "View POC" pattern). Excludes purely administrative /
  // summary sections that don't themselves generate findings: demographics,
  // vitals (numeric-only), diagnoses, performanceStatus, sfv (follow-up
  // summary), admissionsOrder, referrals, finalization.
  const POC_ENABLED_SECTIONS = new Set([
    "pain", "symptomImpact",
    "neurological", "cardiovascular", "respiratory", "infection",
    "gastrointestinal", "nutrition", "endocrine", "genitourinary",
    "musculoskeletal", "skin", "imminentDeath",
    "safety", "psychosocial", "spiritual", "bereavement",
    "personalCare", "teachingNeeds",
  ]);

  const normalizePainPatientType = (type) => {
    if (!type || type === "adult-alert" || type === "alert") return "verbal";
    if (type === "adult" || type === "alert-adult") return "verbal";
    return type;
  };

  const patientAge = sectionKey === "pain" ? calculateAgeFromDob(demographics?.dob) : null;
  const isPediatricAge = typeof patientAge === "number" && patientAge < 18;

  // Auto-derive the pain scale from the patient's pain-communication status
  // (can the patient verbalize pain? — a clinical tool-selection question,
  // distinct from the official HOPE J0900.A response) and the patient's age
  // — only one scale (Numeric / PAINAD / FLACC)
  // is ever shown. A nurse can still override via the BodyMap patient-type
  // toggle, which updates painMapMode directly.
  const deriveModeFromScreening = (verbalizesPain) => {
    if (isPediatricAge) return "pediatric";
    if (verbalizesPain === "1" || verbalizesPain === "2") return "verbal";
    if (verbalizesPain === "0" || verbalizesPain === "3") return "non-verbal";
    return "verbal";
  };

  const getPainAssessmentMode = () => {
    const patientType = normalizePainPatientType(data.painMapMode || deriveModeFromScreening(data.verbalizesPain));
    const selectedTool = String(data.assessmentTool || "");
    if (patientType === "verbal") return "verbal";
    if (patientType === "non-verbal") return selectedTool === "FLACC" ? "flacc" : "painad";
    if (patientType === "pediatric") return "flacc";
    return "verbal";
  };

  const getPainToolOptions = (mode) => {
    if (mode === "painad") return ["PAINAD", "FLACC"];
    if (mode === "flacc") return ["FLACC"];
    return ["Numeric (0-10)"];
  };

  const painAssessmentMode = sectionKey === "pain" ? getPainAssessmentMode() : null;

  // Disease-specific performance scales only apply to patients with the
  // matching diagnosis (primary or secondary): NYHA needs CHF/heart
  // failure, FAST needs dementia, ECOG needs cancer.
  const showNyha = sectionKey === "performanceStatus" && diagnosesIncludeCategory(fullFormData?.diagnoses, "heartFailure");
  const showFast = sectionKey === "performanceStatus" && diagnosesIncludeCategory(fullFormData?.diagnoses, "dementia");
  const showEcog = sectionKey === "performanceStatus" && diagnosesIncludeCategory(fullFormData?.diagnoses, "cancer");

  const isBodySystemWorkspace = workspacePilot && BODY_SYSTEM_FORM_SECTIONS.has(sectionKey);

  const cardsContent = resolvedCards.map((card, ci) => {
        // [PRESENTATION-ONLY RELOCATION] A card may declare `dataSection` to
        // render under a different screen/section than the one that owns its
        // data (e.g. the ADL Assessment card visually relocated to Functional
        // Status while its fields remain part of the `musculoskeletal`
        // module). When set, field values/updates and POC controls resolve
        // against that owning section instead of the ambient `sectionKey`, so
        // storage, validation, LCD facts, and HOPE/POC ownership are
        // unchanged -- see RNICA_SCREEN_AUTHORITY_MATRIX.md.
        const cardDataSection = card.dataSection || sectionKey;
        const cardData = card.dataSection ? (fullFormData?.[card.dataSection] || {}) : data;
        // [Pain information-hierarchy regroup -- 2026-10] Several "Pain
        // Pattern & Trend" cards now share one visual title (the numeric/
        // FLACC/PAINAD tool variants plus the chronic-pain detail card), so
        // card identity below is detected by a field it uniquely owns
        // rather than by `card.title` string equality. No field, path,
        // option, or HOPE mapping changed -- only which named card a field
        // renders under.
        const isPainNumericToolCard = sectionKey === "pain" && card.fields?.some((f) => f.path === "assessmentTool");
        const isPainFlaccCard = sectionKey === "pain" && card.fields?.some((f) => f.path === "flacc.face");
        const isPainPainadCard = sectionKey === "pain" && card.fields?.some((f) => f.path === "painad.breathing");
        const isPainLocationCard = sectionKey === "pain" && card.fields?.some((f) => f.path === "painLocation");
        // [Redesign 2026-10-03 "Nursing Assessment Flow"] Pain Type,
        // Characteristics, and Functional Impact are merged into one
        // "Pain Character & Impact" card (identified by either of its two
        // always-present anchor fields) so the former 3-box/3-border
        // layout becomes 1 box. Visibility that used to be a whole-card
        // gate (`painAssessmentMode === "verbal"`) is now a per-field gate
        // below (PAIN_VERBAL_ONLY_PATHS) -- neuropathic-pain fields are
        // NOT verbal-only and must keep showing for non-verbal patients,
        // which the old card-level gate would have wrongly hidden if
        // simply merged without this change. No field/path/option/HOPE
        // mapping touched.
        const isPainCharacteristicsCard = sectionKey === "pain" && card.fields?.some((f) => f.path === "painOnsetProgression" || f.path === "neuropathicPain");
        // Pain History merges the former standalone chronic/recurrent-pain
        // gate question and its detail sub-fields (baseline/tolerance/
        // threshold/management-approach/control-status) into one card
        // (was two boxes). Same card-level visibility rule as before
        // (only relevant once the patient denies current pain) and the
        // same field-level chronicPainHistory === "1" gate on every detail
        // field, both unchanged below.
        const isPainHistoryCard = sectionKey === "pain" && card.fields?.some((f) => f.path === "chronicPainHistory");
        const shouldRenderPainMap = isPainLocationCard;
        const shouldRenderSkinMap = sectionKey === "skin" && card.title === "Skin Assessment";
        const shouldRenderPainToolCard = isPainNumericToolCard && painAssessmentMode !== "painad" && painAssessmentMode !== "flacc";
        const shouldRenderLocationCard = isPainLocationCard && painAssessmentMode === "verbal";
        const shouldRenderPainadCard = isPainPainadCard && painAssessmentMode === "painad";
        const shouldRenderFlaccCard = isPainFlaccCard && painAssessmentMode === "flacc";

        if (isPainNumericToolCard && !shouldRenderPainToolCard) {
          return null;
        }
        if (isPainLocationCard && !shouldRenderLocationCard) {
          return null;
        }
        if (isPainPainadCard && !shouldRenderPainadCard) {
          return null;
        }
        if (isPainFlaccCard && !shouldRenderFlaccCard) {
          return null;
        }
        // The chronic/recurrent-history question (and its detail fields)
        // only applies once the patient denies current pain -- hide the
        // whole merged card rather than show it with just one field.
        if (isPainHistoryCard && cardData.currentPain !== "0") {
          return null;
        }

        // HOPE J2052A controls the J2053 branch too: symptom impact "at
        // the SFV" is only applicable once an SFV was actually completed.
        // When J2052A = No, hide the whole J2053 card (CMS mutual
        // exclusivity: J2052B/J2053 only apply when J2052A = Yes).
        if (sectionKey === "sfv" && card.title === "SFV Symptom Impact" && !cardData.inPersonSfvCompleted) {
          return null;
        }

        // GitHub Directive (2026-09-28) "Neurological Overview Gate" --
        // the audit confirmed the normal-patient path required ~22 visible
        // decisions against a 5-10 target. Everything below the new
        // "Neurological Overview" card is now gated on that single
        // up-front triage answer; nothing is removed, renamed, or
        // reinterpreted -- cards simply don't render until they're
        // relevant to the path the nurse selected.
        if (sectionKey === "neurological" && card.title !== "Neurological Overview") {
          const overview = data.neuroOverview;
          // Before the gate is answered, show ONLY the Overview card --
          // this is the single biggest lever for cutting the initial
          // decision count.
          if (!overview) return null;
          // "Unable to Assess": the reason control lives on the Overview
          // card itself; nothing else applies.
          if (overview === "Unable to Assess") return null;
          if (overview === "No Current Neurological Concern") {
            // Path 1 (fastest): Consciousness, Orientation, Sleep/
            // Responsiveness (baseline only), Overall Change,
            // Communication (primary only), Behavioral Status gate,
            // Motor/Balance Status gate. HOPE and Notes stay visible --
            // official/independent obligations are never gated behind an
            // internal speed metric (mega-directive Section 17).
            if (["Psychiatric History"].includes(card.title)) return null;
          }
          // "Existing Neurological Findings Stable" and "New/Worsening
          // Neurological Findings" both render the full comprehensive
          // card set unchanged (today's existing behavior) -- Stable's
          // "confirm rather than re-enter prior values" flow is a
          // separate, larger feature tracked for a future pass, not
          // faked here.
        }

        // OWNER-DIRECTED "Cardiovascular Overview Gate" (2026-09-28 Final
        // Directive, Section 3) -- same triage pattern as Neurological.
        // Path 1 target is exactly 5 selections (Overview, Rhythm, Rate,
        // Strength, Clinical Status Change); Path 4 shows only the
        // Overview card (its reason control lives there). Path 2's
        // "only show already-documented findings" rule is enforced at
        // the field level (see the render-loop guard below), not by
        // hiding whole cards, since Clinical Status Change/Notes/Circulation
        // & Perfusion (which hosts the always-visible Pulse dimensions)
        // must remain visible.
        if (sectionKey === "cardiovascular" && card.title !== "Cardiovascular Overview") {
          const overview = data.cardiovascularOverview;
          if (!overview) return null;
          if (overview === "Unable to Assess") return null;
          if (overview === "No Current Cardiovascular Concern" && ["Cardiovascular Symptoms", "Cardiac Devices"].includes(card.title)) {
            return null;
          }
        }

        if (sectionKey === "performanceStatus" && card.title === "NYHA Classification (Heart Failure)" && !showNyha) {
          return null;
        }
        if (sectionKey === "performanceStatus" && card.title === "FAST Scale (Dementia)" && !showFast) {
          return null;
        }
        if (sectionKey === "performanceStatus" && card.title === "ECOG Performance Status" && !showEcog) {
          return null;
        }
        // Pilot-only cards (summary banner / group labels / mobility
        // reference) are hidden entirely in legacy mode -- legacy keeps
        // exactly the original card list/order it always had.
        if (sectionKey === "performanceStatus" && !workspacePilot && ["functionalStatusSummary", "scaleGroupLabel", "mobilityTransferSummary"].includes(card.customRenderer)) {
          return null;
        }
        if (sectionKey === "performanceStatus" && card.customRenderer === "scaleGroupLabel") {
          const groupHasVisibleScale = card.title === "Specialized Diagnosis-Specific Scales" ? (showEcog || showFast || showNyha) : true;
          if (!groupHasVisibleScale) return null;
          return <div key={ci} className="rnica-performance-group-label">{card.title}</div>;
        }
        if (sectionKey === "performanceStatus" && card.customRenderer === "functionalStatusSummary") {
          return (
            <FunctionalStatusSummaryCard
              key={ci}
              diagnosesData={fullFormData?.diagnoses}
              showEcog={showEcog}
              showFast={showFast}
              showNyha={showNyha}
            />
          );
        }
        if (sectionKey === "performanceStatus" && card.customRenderer === "mobilityTransferSummary") {
          return <MobilityTransferSummaryCard key={ci} fullFormData={fullFormData} />;
        }
        if (sectionKey === "performanceStatus" && workspacePilot && PERFORMANCE_SCALE_TITLES[card.title]) {
          return (
            <PerformanceScaleCard
              key={ci}
              scaleKey={PERFORMANCE_SCALE_TITLES[card.title]}
              card={card}
              data={cardData}
              update={(path, v) => update(cardDataSection, path, v)}
              diagnosesData={fullFormData?.diagnoses}
            />
          );
        }
        if (sectionKey === "performanceStatus" && workspacePilot && card.customRenderer === "adlSummaryGrid") {
          return (
            <Card key={ci} id={card.id} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <AdlSummaryGrid card={card} data={cardData} update={(path, v) => update(cardDataSection, path, v)} />
            </Card>
          );
        }

        if (sectionKey === "diagnoses" && card.customRenderer === "primaryTerminalDiagnosis") {
          return (
            <Card key={ci} id={card.id} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <PrimaryTerminalDiagnosisCard
                diagnosesData={data}
                updateField={u}
                styles={styles}
                COLORS={COLORS}
                workspacePilot={workspacePilot}
              />
            </Card>
          );
        }

        if (sectionKey === "diagnoses" && card.customRenderer === "lcdEligibility") {
          return (
            <Card key={ci} id={card.id} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <LcdEligibilityCard
                diagnosesData={data}
                fullFormData={fullFormData}
                updateField={u}
                styles={styles}
                COLORS={COLORS}
                workspacePilot={workspacePilot}
              />
            </Card>
          );
        }

        if (sectionKey === "diagnoses" && card.customRenderer === "clinicalNarrative") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <ClinicalNarrativeCard
                diagnosesData={data}
                fullFormData={fullFormData}
                updateField={u}
                styles={styles}
                COLORS={COLORS}
                locked={locked}
              />
            </Card>
          );
        }

        if (sectionKey === "diagnoses" && card.customRenderer === "secondaryDiagnoses") {
          return (
            <Card key={ci} id={card.id} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <SecondaryDiagnosesCard diagnosesData={data} updateField={u} styles={styles} COLORS={COLORS} workspacePilot={workspacePilot} />
            </Card>
          );
        }

        if (sectionKey === "diagnoses" && card.customRenderer === "hopeComorbidities") {
          return (
            <Card key={ci} id={card.id} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <HopeComorbiditiesCard diagnosesData={data} updateField={u} styles={styles} COLORS={COLORS} workspacePilot={workspacePilot} />
            </Card>
          );
        }

        if (sectionKey === "diagnoses" && card.customRenderer === "lcdSupportingEvidence") {
          // Pilot-only: renders last on the Diagnoses page so free-text
          // narrative never sits between structured checklists. Legacy mode
          // keeps the evidence field inside the LCD Eligibility card above
          // (unchanged) and this card renders nothing.
          if (!workspacePilot) return null;
          return (
            <Card key={ci} id={card.id} title={card.title}>
              <LcdSupportingEvidenceCard diagnosesData={data} updateField={u} />
            </Card>
          );
        }

        if (sectionKey === "performanceStatus" && card.customRenderer === "declineTracker") {
          const declineTrackerBody = (
            <DeclineTrackerCard
              patientId={patientId}
              assessmentId={assessmentId}
              performanceData={data}
              weight={fullFormData?.vitals?.weight}
              updateField={u}
              styles={styles}
              COLORS={COLORS}
            />
          );
          // Collapsed by default in pilot mode -- most admissions have "no
          // prior assessment available" here, so it shouldn't occupy space
          // above the actual scales. Legacy mode is untouched (always
          // expanded, plain Card wrapper).
          if (workspacePilot) {
            return (
              <Accordion key={ci} type="single" collapsible className="rnica-decline-accordion">
                <AccordionItem value="decline">
                  <AccordionTrigger>{card.title}</AccordionTrigger>
                  <AccordionContent>{declineTrackerBody}</AccordionContent>
                </AccordionItem>
              </Accordion>
            );
          }
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              {declineTrackerBody}
            </Card>
          );
        }

        if (sectionKey === "nutrition" && card.customRenderer === "nutritionAnthropometricReference") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms} bare={workspacePilot && BODY_SYSTEM_FORM_SECTIONS.has(sectionKey)}>
              <NutritionAnthropometricReferenceCard fullFormData={fullFormData} styles={styles} COLORS={COLORS} />
            </Card>
          );
        }

        if (sectionKey === "nutrition" && card.customRenderer === "weightLossAutoCalc") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms} bare={workspacePilot && BODY_SYSTEM_FORM_SECTIONS.has(sectionKey)}>
              <WeightLossAutoCalcCard
                patientId={patientId}
                assessmentId={assessmentId}
                currentWeight={fullFormData?.vitals?.weight}
                existingValue={data?.weightLossPastSixMonths}
                updateField={u}
                styles={styles}
                COLORS={COLORS}
              />
            </Card>
          );
        }

        if (sectionKey === "vitals" && card.customRenderer === "vitalSignsClinical") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <VitalSignsClinicalCard data={data} updateField={u} styles={styles} COLORS={COLORS} />
            </Card>
          );
        }

        if (sectionKey === "vitals" && card.customRenderer === "anthropometricsAutoBmi") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <AnthropometricsAutoBmiCard data={data} updateField={u} styles={styles} COLORS={COLORS} />
            </Card>
          );
        }

        if (sectionKey === "skin" && card.customRenderer === "woundList") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms} bare={workspacePilot && BODY_SYSTEM_FORM_SECTIONS.has(sectionKey)}>
              <WoundListCard data={data} updateField={u} styles={styles} COLORS={COLORS} />
              {/* Owner directive: compress Pressure Relief Measures into an
                  inline checklist within Wound Documentation rather than a
                  separate "Wound Documentation & Notes" card. Same fields/
                  paths as before (woundImpairment, pressureReliefMeasures,
                  repositioningPlan, notes) -- no data model change. */}
              <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px dashed ${COLORS.border}`, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 8 }}>
                <FormCheckboxGroup label="Pressure-Relief Measures" values={data.pressureReliefMeasures || []}
                  onChange={(v) => u("pressureReliefMeasures", v)}
                  options={["Pressure-relief mattress", "Heel protectors/floating heels", "Cushioned wheelchair seat", "Foam/gel positioning devices", "Frequent position changes", "None in place"]} />
                <FormInput label="Repositioning Plan" value={data.repositioningPlan} onChange={(v) => u("repositioningPlan", v)}
                  placeholder="e.g., Reposition every 2 hours, alternate sides" />
              </div>
              <div style={{ marginTop: 8, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 8 }}>
                <FormTextarea label="Wound Impairment" rows={2} value={data.woundImpairment} onChange={(v) => u("woundImpairment", v)} />
                <FormTextarea label="Skin Notes" rows={2} value={data.notes} onChange={(v) => u("notes", v)} />
              </div>
              <SkinTreatmentSummary assessmentId={assessmentId} patientId={patientId} styles={styles} COLORS={COLORS} />
            </Card>
          );
        }

        if (sectionKey === "safety" && card.customRenderer === "dmeStatus") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <DmeStatusCard data={data} updateField={u} styles={styles} COLORS={COLORS} />
            </Card>
          );
        }

        // [OWNER REVIEW -- 2026-09-26, superseded by FINAL OWNER
        // REQUIREMENTS] Current Pain Summary is a single read-only card
        // (no separate "Pain Management Summary"). AI Pain Analysis always
        // renders (with an honest placeholder when there is nothing
        // grounded to say). Overdue Action Alerts renders nothing at all
        // -- no card, no placeholder -- when no rule is triggered.
        if (sectionKey === "pain" && card.customRenderer === "painAssessmentSummary") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms} compact>
              <PainAssessmentSummaryCard data={data} styles={styles} />
            </Card>
          );
        }

        if (sectionKey === "pain" && card.customRenderer === "aiPainAnalysis") {
          // Always render: AiPainAnalysisCard already shows an honest
          // "Insufficient reviewed pain data for analysis." placeholder
          // when computeAiPainNotes() returns []. Hiding the whole card in
          // that case made the feature invisible/undiscoverable during
          // review -- it must always be present so the RN/owner can see
          // it is implemented, not missing.
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms} compact>
              <AiPainAnalysisCard data={data} styles={styles} />
            </Card>
          );
        }

        if (sectionKey === "pain" && card.customRenderer === "painOverdueAlerts") {
          if (computePainOverdueAlerts(data, painAssessmentMode).length === 0) return null;
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms} compact>
              <PainOverdueAlertsCard data={data} painAssessmentMode={painAssessmentMode} styles={styles} />
            </Card>
          );
        }

        if (sectionKey === "gastrointestinal" && card.customRenderer === "constipationAutoAssess") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms} bare={workspacePilot && BODY_SYSTEM_FORM_SECTIONS.has(sectionKey)}>
              <ConstipationAutoAssessCard
                lastBM={data?.lastBM}
                diarrhea={data?.diarrhea}
                existingValue={data?.constipation}
                updateField={u}
                styles={styles}
                COLORS={COLORS}
              />
            </Card>
          );
        }

        if (card.customRenderer === "referralRecommendation" && ["psychosocial", "spiritual", "bereavement"].includes(sectionKey)) {
          const indicatorsPath = sectionKey === "bereavement" ? "riskFactors" : "referralIndicators";
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <ReferralRecommendationCard
                domain={sectionKey}
                indicators={data?.[indicatorsPath]}
                styles={styles}
              />
            </Card>
          );
        }

        if (card.customRenderer === "referralRefusal" && ["psychosocial", "spiritual", "bereavement"].includes(sectionKey)) {
          const indicatorsPath = sectionKey === "bereavement" ? "riskFactors" : "referralIndicators";
          const recommendation = resolveReferralRecommendation(data?.[indicatorsPath]);
          if (!recommendation.recommended || data?.familyResponse !== "Refused") return null;
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <ReferralRefusalCard
                domain={sectionKey}
                recommended={recommendation.recommended}
                familyResponse={data?.familyResponse}
                refusal={data?.refusal}
                updateField={u}
                styles={styles}
                COLORS={COLORS}
              />
            </Card>
          );
        }

        if (sectionKey === "infection" && card.customRenderer === "patientAllergies") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms} bare={workspacePilot && BODY_SYSTEM_FORM_SECTIONS.has(sectionKey)}>
              <AllergiesCard patientId={patientId} styles={styles} COLORS={COLORS} />
            </Card>
          );
        }

        if (sectionKey === "admissionsOrder" && card.customRenderer === "disciplineFrequencyOfVisit") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <DisciplineFrequencyOfVisitCard
                rows={data.visitFrequency}
                onChange={(next) => u("visitFrequency", next)}
                styles={styles}
                COLORS={COLORS}
              />
            </Card>
          );
        }

        if (sectionKey === "admissionsOrder" && card.customRenderer === "haAssignment") {
          const assignedAide = data.haAssignment?.assignedAide || "";
          const notApplicable = !!data.haAssignment?.notApplicable;
          const chhaPocCompleted = fullFormData?.chhaPoc?.completed === true;
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <FormInput label="Assigned Home Aide" value={assignedAide} onChange={(v) => u("haAssignment.assignedAide", v)} />
              <FormCheckbox label="HA Assignment N/A" checked={notApplicable} onChange={(v) => u("haAssignment.notApplicable", v)} />
              {!notApplicable && (
                <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                  <button
                    type="button"
                    onClick={() => onNavigateToSection?.("chha-assignment")}
                    disabled={!onNavigateToSection}
                    style={{ ...styles.btnSecondary, opacity: onNavigateToSection ? 1 : 0.5 }}
                    title={onNavigateToSection ? "Open the CHHA Plan of Care" : "Open this patient's chart to reach the CHHA Plan of Care"}
                  >
                    → Open CHHA Plan of Care
                  </button>
                  {assignedAide.trim() && (
                    chhaPocCompleted ? (
                      <span style={{ fontSize: 11.5, color: COLORS.success, fontWeight: 700 }}>✓ CHHA Plan of Care completed</span>
                    ) : (
                      <span style={{ fontSize: 11.5, color: COLORS.warning, fontWeight: 700 }}>⚠ CHHA Plan of Care not yet completed</span>
                    )
                  )}
                </div>
              )}
            </Card>
          );
        }

        if (sectionKey === "finalization" && card.customRenderer === "finalReviewDashboard") {
          if (!locked) return null;
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <FinalReviewDashboardCard
                assessmentId={assessmentId}
                locked={locked}
                styles={styles}
                COLORS={COLORS}
              />
            </Card>
          );
        }
        // Body Systems architectural correction (pilot-only, supersedes
        // the earlier per-card collapse-by-default density fix): each
        // system renders as ONE workspace instead of N bordered cards, so
        // sub-sections use `bare` (title row + fields only, no box/
        // collapse) and are visually packed together -- nothing is hidden
        // behind a click, preventing missed documentation. The outer
        // workspace Card wrapper is added once per section below (see
        // the wrapping <Card> around this whole map() call).
        const isBodySystemPilotCard = workspacePilot && BODY_SYSTEM_FORM_SECTIONS.has(sectionKey);
        return (
          <Card
            key={ci}
            id={card.id}
            title={card.title}
            hopeCode={card.hopeCode}
            sfv={card.sfv}
            cms={card.cms}
            bare={isBodySystemPilotCard}
            importance={card.importance}
            fullWidth={Boolean(card.fullWidth)}
            // [Pain density pass -- 2026-10] Pain-only card-chrome
            // compaction (tighter header/content padding). Scoped by
            // sectionKey so every other module's cards are unaffected.
            compact={sectionKey === "pain"}
            // Bug fix: Psychiatric History's `collapsedByDefault` (and
            // any other card's) had no effect while Body Systems' pilot
            // "bare" grouping was active, because this excluded
            // isBodySystemPilotCard entirely -- Section 28's "keep
            // collapsed by default" requirement was silently not applying.
            // The bare-card render branch already respects
            // collapsible/collapsed correctly; only this gate was wrong.
            collapsible={(isPainNumericToolCard || isPainLocationCard || isPainCharacteristicsCard || isPainHistoryCard) || card.collapsedByDefault}
            defaultCollapsed={(isPainNumericToolCard || isPainLocationCard || isPainCharacteristicsCard || isPainHistoryCard) || card.collapsedByDefault}
          >
            {isPainNumericToolCard && (
              <NumericPainScale
                value={data.painIntensity?.current !== undefined && data.painIntensity?.current !== "" ? Number(data.painIntensity.current) : null}
                onChange={(score) => u("painIntensity.current", score)}
              />
            )}
            {isPainFlaccCard && (
              <FLACCScale
                value={["face", "legs", "activity", "cry", "consolability"].map((k) => Number(data.flacc?.[k]) || 0)}
                onChange={(arr) => {
                  u("flacc.face", String(arr[0]));
                  u("flacc.legs", String(arr[1]));
                  u("flacc.activity", String(arr[2]));
                  u("flacc.cry", String(arr[3]));
                  u("flacc.consolability", String(arr[4]));
                }}
              />
            )}
            {isPainPainadCard && (
              <PAINADScale
                value={["breathing", "vocalization", "facialExpression", "bodyLanguage", "consolability"].map((k) => Number(data.painad?.[k]) || 0)}
                onChange={(arr) => {
                  u("painad.breathing", String(arr[0]));
                  u("painad.vocalization", String(arr[1]));
                  u("painad.facialExpression", String(arr[2]));
                  u("painad.bodyLanguage", String(arr[3]));
                  u("painad.consolability", String(arr[4]));
                }}
              />
            )}

            {shouldRenderPainMap && painAssessmentMode === "verbal" && (
              <PainBodyMapDialogField
                value={data.painBodySites || []}
                regionLabelById={BODY_MAP_REGION_LABEL_BY_ID}
                onToggle={(regionId) => {
                  const current = data.painBodySites || [];
                  const next = current.includes(regionId)
                    ? current.filter((id) => id !== regionId)
                    : [...current, regionId];
                  u("painBodySites", next);
                }}
                onClearAll={() => u("painBodySites", [])}
              />
            )}
            {shouldRenderPainMap && painAssessmentMode !== "verbal" && (
              <div style={{
                padding: "14px 16px",
                borderRadius: 12,
                background: COLORS.mapControlBg,
                border: `1px solid ${COLORS.mapControlBorder}`,
                color: COLORS.mapMuted,
                fontSize: 12.5,
                lineHeight: 1.5,
              }}>
                <strong style={{ color: COLORS.mapChipText }}>Body Map unavailable — </strong>
                the patient is unable to reliably verbalize or point to a pain location
                (per HOPE J0900 above{isPediatricAge ? " / pediatric patient" : ""}).
                Pain location should be documented via clinician/caregiver observation
                using the {painAssessmentMode === "flacc" ? "FLACC" : "PAINAD"} scale below instead.
              </div>
            )}

            {shouldRenderSkinMap && (
              <BodyMap
                value={data.skinBodySites || []}
                tone="skin"
                onToggle={(regionId) => {
                  const current = data.skinBodySites || [];
                  const next = current.includes(regionId)
                    ? current.filter((id) => id !== regionId)
                    : [...current, regionId];
                  u("skinBodySites", next);
                }}
              />
            )}

            {sectionKey === "pain" && card.title === "Pain Management" && (
              <PainMedicationHarvestBanner
                patientId={patientId}
                data={cardData}
                onApply={(patch) => Object.entries(patch).forEach(([k, v]) => u(k, v))}
                styles={styles}
                COLORS={COLORS}
              />
            )}

            <div style={isBodySystemPilotCard ? undefined : styles.fieldsGrid} className={isBodySystemPilotCard ? "rnica-bodysystem-workspace__fields" : undefined}>
            {card.fields.map((field, fi) => {
              if (isPainFlaccCard || isPainPainadCard) {
                return null;
              }
              if (sectionKey === "pain" && field.path === "assessmentTool") {
                return null;
              }
              // [Redesign 2026-10-03] "Pain Character & Impact" merge:
              // these fields only apply when the patient can verbally
              // describe/report pain (same verbal-only gate Location &
              // Body Map uses) -- a per-field gate now that the card
              // itself is unconditional (neuropathicPain/
              // neuropathicCharacteristics are NOT verbal-only and must
              // keep showing for non-verbal patients on the same card).
              if (sectionKey === "pain" && PAIN_VERBAL_ONLY_PATHS.has(field.path) && painAssessmentMode !== "verbal") {
                return null;
              }
              // HOPE J2052A controls the J2052 branch: when the SFV was
              // completed (inPersonSfvCompleted = true), J2052C (reason not
              // completed) is not applicable and must be hidden -- CMS
              // defines these as mutually exclusive. Shown otherwise.
              if (sectionKey === "sfv" && field.path === "reasonNotCompleted" && cardData.inPersonSfvCompleted) {
                return null;
              }
              // [FINAL OWNER REQUIREMENTS -- 2026-09-26] Pain Screening
              // conditional gates. "Pain assessed?" reuses the existing
              // HOPE J0900.A screenedForPain field (Yes/No) rather than a
              // duplicate question -- CMS defines that field as binary, so
              // "Unable to assess" is intentionally NOT added to it (would
              // corrupt the coded HOPE value); reasonNotAssessed captures
              // that path as free text instead. Pain absent does not stop
              // the assessment: it branches to a chronic-pain-history
              // question, then (only if chronic AND the patient can
              // verbalize) RN-entered baseline/tolerance/threshold fields.
              if (sectionKey === "pain" && field.path === "reasonNotAssessed" && cardData.screenedForPain !== "0") {
                return null;
              }
              if (sectionKey === "pain" && field.path === "currentPain" && cardData.screenedForPain !== "1") {
                return null;
              }
              // [Pain density pass -- 2026-10] screenedForPain's own
              // option label reads "No -- skip to Pain Active Problem
              // (J0905)", so when the nurse answers No, the downstream
              // ASSESSMENT-group fields that only make sense once pain
              // has actually been screened (tool used, self-report
              // reliability, severity category, discomfort) are not
              // applicable yet. painActiveProblem (the stated skip
              // target) is deliberately excluded and always renders.
              // Same existing per-field gating mechanism as the rows
              // above -- no field/option/HOPE mapping removed, only
              // conditionally not rendered.
              if (sectionKey === "pain" && ["standardizedPainToolType", "verbalizesPain", "painSeverityCategory", "uncomfortableBecauseOfPain"].includes(field.path) && cardData.screenedForPain === "0") {
                return null;
              }
              if (sectionKey === "pain" && field.path === "chronicPainHistory" && cardData.currentPain !== "0") {
                return null;
              }
              if (sectionKey === "pain" && field.path === "neuropathicCharacteristics" && cardData.neuropathicPain !== "1") {
                return null;
              }
              if (sectionKey === "pain" && ["chronicPainCondition", "usualBaselinePainLevel", "tolerablePainLevel", "interventionThresholdLevel", "usualFrequencyPattern", "currentManagementApproach", "controlStatus"].includes(field.path)) {
                if (cardData.currentPain !== "0" || cardData.chronicPainHistory !== "1") return null;
                // Per Section 9: patient-stated tolerance/threshold levels
                // never apply when the patient cannot reliably self-report.
                if (field.path === "tolerablePainLevel" && painAssessmentMode !== "verbal") return null;
              }
              if (sectionKey === "pain" && ["painOnsetProgression", "painDurationFrequency", "effectOnFunction"].includes(field.path) && cardData.currentPain === "0" && cardData.chronicPainHistory !== "1") {
                return null;
              }
              // [RNICA_NEURO_CARDIO_WORKFLOW_CORRECTION.md -- Category A,
              // presentation-only, no new fields/values] Reveal a follow-up
              // field only once its trigger field establishes it applies,
              // and preserve all existing stored data/paths/HOPE mappings.
              if (sectionKey === "neurological") {
                const motorPresent = cardData.motorStatus === "Present" || (cardData.motorStatus === undefined && cardData.motorDeficit === true);
                const motorDetailVisible = cardData.neuroOverview !== "No Current Neurological Concern" || cardData.motorBalanceStatus === "Findings Present";
                if (["affectedSide", "deficitType"].includes(field.path) && !(motorPresent && motorDetailVisible)) {
                  return null;
                }
              }
              if (sectionKey === "neurological" && field.path === "psychiatricHistory" && !(cardData.psychiatricHistoryType || []).length) {
                return null;
              }
              // GitHub Directive (2026-09-28) "Neurological Review --
              // Average Sleep Hours..." Issue #1 -- only reveal the hours
              // field once the nurse has said a trend is actually known;
              // otherwise it's asking for a number nobody has.
              if (sectionKey === "neurological" && field.path === "sleepRest.averageSleepHours" && cardData.sleepRest?.sleepTrendKnown !== "Yes") {
                return null;
              }
              // GitHub Directive (2026-09-28) "Neurological Overview Gate"
              // -- Path 4 (Unable to Assess) reason control only applies
              // once that path is selected; the free-text "Other" detail
              // only applies once "Other" is the selected reason.
              if (sectionKey === "neurological" && field.path === "neuroUnableToAssessReason" && cardData.neuroOverview !== "Unable to Assess") {
                return null;
              }
              if (sectionKey === "neurological" && field.path === "neuroUnableToAssessOther" && (cardData.neuroOverview !== "Unable to Assess" || cardData.neuroUnableToAssessReason !== "Other")) {
                return null;
              }
              if (sectionKey === "neurological") {
                // The Overview gate's whole purpose: on the fastest path
                // (patient has no current neurological concern), the
                // "advanced" detail fields below don't earn their place on
                // screen unless something actually turns out abnormal --
                // they stay fully intact in stored data and reappear
                // immediately if the nurse switches Overview to Stable or
                // New/Worsening, or if the underlying value itself already
                // indicates a concern (never hides a documented abnormal
                // finding).
                const neuroNormalPathActive = cardData.neuroOverview === "No Current Neurological Concern";
                const sleepAbnormal = (cardData.sleepRest?.sleepPattern && cardData.sleepRest.sleepPattern !== "Normal")
                  || (cardData.sleepRest?.responsiveness && cardData.sleepRest.responsiveness !== "Easily Aroused")
                  || (cardData.sleepRest?.changeSincePrior && cardData.sleepRest.changeSincePrior !== "No Change");
                const advancedSleepFields = ["sleepRest.changeSincePrior", "sleepRest.sleepTrendKnown", "sleepRest.nighttimeSymptoms", "sleepRest.sleepAids", "sleepRest.effectOnComfort", "sleepRest.response", "sleepRest.restfulness", "sleepRest.notes"];
                if (advancedSleepFields.includes(field.path) && neuroNormalPathActive && !sleepAbnormal) {
                  return null;
                }
                if (["hearing", "vision", "sensoryDeficits", "sensoryAids"].includes(field.path) && neuroNormalPathActive) {
                  return null;
                }
                // New gate fields (`behavioralStatus`/`motorBalanceStatus`)
                // only exist to keep the fast path fast -- they're hidden
                // once the nurse is off that path, where the full detail
                // renders unconditionally exactly as it did before this
                // directive.
                if (field.path === "behavioralStatus" && !neuroNormalPathActive) {
                  return null;
                }
                if (field.path === "motorBalanceStatus" && !neuroNormalPathActive) {
                  return null;
                }
                const behavioralDetailVisible = !neuroNormalPathActive || cardData.behavioralStatus === "Findings Present";
                if (["cognition", "symptomsDemeanor", "delirium", "seizureHistory"].includes(field.path) && !behavioralDetailVisible) {
                  return null;
                }
                const motorDetailVisible = !neuroNormalPathActive || cardData.motorBalanceStatus === "Findings Present";
                if (["motorStatus", "balance"].includes(field.path) && !motorDetailVisible) {
                  return null;
                }
              }
              if (sectionKey === "cardiovascular" && field.path === "chestPain.type" && cardData.chestPain?.present !== "Yes") {
                return null;
              }
              if (sectionKey === "cardiovascular" && field.path === "edema.location" && cardData.edema?.present !== "Yes") {
                return null;
              }
              if (sectionKey === "cardiovascular" && field.path === "edema.severity" && cardData.edema?.present !== "Yes") {
                return null;
              }
              // (Heart Failure Type's "only if Heart Failure Present" gate
              // is now folded into the Section-3/5/6/7 legacy-display
              // guard below, since both fields are read-only legacy-only.)
              // OWNER-DIRECTED "Cardiovascular Overview Gate" (2026-09-28
              // Final Directive, Sections 2/3) -- the reason control lives
              // on the Overview card itself; nothing else applies once
              // that path is selected (Path 4 hides everything else via
              // the card-level guard above).
              if (sectionKey === "cardiovascular" && field.path === "cardiovascularUnableToAssessReason" && cardData.cardiovascularOverview !== "Unable to Assess") {
                return null;
              }
              if (sectionKey === "cardiovascular" && field.path === "cardiovascularUnableToAssessOther" && (cardData.cardiovascularOverview !== "Unable to Assess" || cardData.cardiovascularUnableToAssessReason !== "Other")) {
                return null;
              }
              if (sectionKey === "cardiovascular") {
                // Path 1 ("No Current Cardiovascular Concern"): approved
                // normal path is exactly Overview + Rhythm + Rate +
                // Strength + Clinical Status Change (Notes optional) --
                // every other Circulation & Perfusion field is hidden
                // (never deleted) until the path changes.
                const cvNormalPathActive = cardData.cardiovascularOverview === "No Current Cardiovascular Concern";
                const normalPathHiddenFields = [
                  "pulseSites", "peripheralCirculation", "heartSounds", "jvd", "skinColor",
                  "coolExtremities", "varicoseVeins", "stasisUlcer",
                  "edema.present", "edema.location", "edema.severity",
                ];
                if (cvNormalPathActive && normalPathHiddenFields.includes(field.path)) {
                  return null;
                }
                // Path 2 ("Existing Cardiovascular Findings Review"): show
                // only values that already exist in the currently loaded
                // record (owner directive Section 3, Path 2) -- this is a
                // visibility/review convenience only, never a claim of
                // verified prior-assessment comparison.
                const CV_ALWAYS_VISIBLE_FIELDS = new Set([
                  "cardiovascularOverview", "cardiovascularUnableToAssessReason", "cardiovascularUnableToAssessOther",
                  "clinicalStatusChange", "notes", "cardiovascularFindingsConfirmedThisVisit",
                ]);
                if (cardData.cardiovascularOverview === "Existing Cardiovascular Findings Review" && !CV_ALWAYS_VISIBLE_FIELDS.has(field.path)) {
                  const existing = getNestedValue(cardData, field.path);
                  const documented = Array.isArray(existing) ? existing.length > 0 : (typeof existing === "boolean" ? existing === true : Boolean(existing));
                  // Owner directive (2026-09-28) "New Cardiovascular Defect --
                  // one-way segmented selections": a segmentedTriState field
                  // (JVD/Edema Present/Chest Pain Present) can now be cleared
                  // back to "" by re-clicking its selected pill. Without this
                  // memo, clearing it here on Path 2 would make the field
                  // vanish (documented === false) with no control left to
                  // click -- an unrecoverable documentation trap. Once a
                  // field has been shown for this open record, it stays
                  // shown for the rest of the editing session even if the
                  // clinician clears it back out; the stored value itself is
                  // untouched by this -- it only freezes visibility.
                  const everDocumentedKey = `${assessmentId || "unsaved"}::${field.path}`;
                  let everDocumented = cvPath2EverDocumentedFields.get(everDocumentedKey);
                  if (!everDocumented && documented) {
                    everDocumented = true;
                    cvPath2EverDocumentedFields.set(everDocumentedKey, true);
                  }
                  if (!everDocumented) return null;
                }
                // Directive (2026-09-28) Section 13 -- the confirmation
                // control only makes sense on Path 2; every other path
                // hides it (never deletes a previously-recorded value).
                if (field.path === "cardiovascularFindingsConfirmedThisVisit" && cardData.cardiovascularOverview !== "Existing Cardiovascular Findings Review") {
                  return null;
                }
                // Dyspnea Ownership Model (Contradiction 5): the checkbox
                // and its guidance note are mutually exclusive, and both
                // are independently gated from the plain edema/chestPain-
                // style "parent present" pattern because the controlling
                // value lives in a different Body System (Respiratory).
                const dyspneaGate = resolveCardiacDyspneaGate(cardData, fullFormData?.respiratory);
                if (field.path === "cardiacDyspnea" && !dyspneaGate.visible) {
                  return null;
                }
                if (field.path === "cardiacDyspneaGuidanceNote" && (dyspneaGate.visible || !dyspneaGate.guidance)) {
                  return null;
                }
                // Owner directive (2026-09-28) "Remove Heart Failure From
                // Cardiovascular Body System Completely" -- Heart Failure
                // is a diagnosis, not a current-entry symptom control or a
                // reviewable Body System field, on ANY path including
                // Path 2. Diagnosis-level Heart Failure data continues to
                // live in Diagnosis & LCD / HOPE I0600 (untouched); this
                // guard just stops it from ever rendering inside
                // Cardiovascular. The stored value itself is never read,
                // deleted, or rewritten by this guard.
                if (["heartFailurePresent", "heartFailureType"].includes(field.path)) {
                  return null;
                }
              }
              const fieldForRender = sectionKey === "pain" && field.path === "assessmentTool"
                ? { ...field, options: getPainToolOptions(painAssessmentMode) }
                : field;
              // Issue #7 -- a legacy record that only ever set the old
              // `motorDeficit` boolean (never touched the new `motorStatus`
              // path) should still visually show "Present" here instead of
              // appearing unanswered; nothing is written until the nurse
              // actually interacts with the control.
              const CV_PULSE_DIMENSION_PATHS = new Set(["pulseRhythm", "pulseRate", "pulseStrength"]);
              const value = sectionKey === "neurological" && fieldForRender.path === "motorStatus" && cardData.motorStatus === undefined && cardData.motorDeficit === true
                ? "Present"
                : sectionKey === "cardiovascular" && CV_PULSE_DIMENSION_PATHS.has(fieldForRender.path)
                ? resolvePulseDimensionDisplay(cardData, fieldForRender.path)
                : sectionKey === "cardiovascular" && fieldForRender.path === "bpStatus"
                ? resolveBpStatusDisplay(cardData)
                : sectionKey === "cardiovascular" && fieldForRender.path === "orthostaticFinding"
                ? resolveOrthostaticFindingDisplay(cardData)
                : getNestedValue(cardData, fieldForRender.path);
              const onChange = (v) => {
                update(cardDataSection, fieldForRender.path, v);
                // [Control Conflict Report #1] Orientation vs. Disoriented
                // are mutually exclusive findings, not independent
                // checkboxes -- checking one now clears the other so a
                // record can never store both simultaneously. No field
                // removed/renamed; both paths keep their existing booleans.
                if (sectionKey === "neurological" && fieldForRender.path === "orientation.disoriented" && v) {
                  ["orientation.time", "orientation.place", "orientation.person", "orientation.situation"].forEach((p) => u(p, false));
                }
                if (sectionKey === "neurological" && ["orientation.time", "orientation.place", "orientation.person", "orientation.situation"].includes(fieldForRender.path) && v) {
                  u("orientation.disoriented", false);
                }
                // Issue #7 (2026-09-28 follow-up review) -- Motor Status is
                // the new primary 3-state control; keep the legacy
                // `motorDeficit` boolean in sync (true only for "Present")
                // so every existing consumer of that boolean (Structured
                // Findings, narrative Summary, affectedSide/deficitType
                // reveal guards) keeps working unchanged.
                if (sectionKey === "neurological" && fieldForRender.path === "motorStatus") {
                  u("motorDeficit", v === "Present");
                }
                // Directive (2026-09-28) "Cardiovascular Layout
                // Consolidation" Section 14 -- data inspection (SFV
                // registry CV_HEART_FAILURE_SYSTOLIC/DIASTOLIC both use
                // `multi_add`, and mixed systolic+diastolic heart failure
                // is a real clinical presentation) confirms Heart Failure
                // Type stays multi-select. The only genuine contradiction
                // is "Unspecified" coexisting with a specific type -- so
                // selecting Unspecified clears the specific types, and
                // selecting a specific type clears Unspecified, without
                // ever preventing Systolic + Diastolic together.
                // NOTE (2026-09-28, Scope Correction): `heartFailureType`
                // is now rendered `legacyReadOnly` (no onChange wired), so
                // this interceptor is currently dormant in the UI. Left in
                // place (and still covered by resolveHeartFailureTypeSelection's
                // own unit tests) in case a future, explicitly-approved
                // change reintroduces an editable Heart Failure Type
                // control; it does not affect current behavior.
                if (sectionKey === "cardiovascular" && fieldForRender.path === "heartFailureType" && Array.isArray(v)) {
                  const corrected = resolveHeartFailureTypeSelection(cardData.heartFailureType, v);
                  if (corrected) {
                    update(cardDataSection, fieldForRender.path, corrected);
                    return;
                  }
                }
                if (sectionKey === "pain" && fieldForRender.path === "verbalizesPain") {
                  // Auto-select the correct pain scale from the patient's
                  // communication status + age so only one tool is ever shown:
                  // verbal (reliable/sometimes) -> Numeric, non-verbal adult
                  // -> PAINAD, pediatric -> FLACC. Note: this communication
                  // status is distinct from the official HOPE J0900.A
                  // "was patient screened for pain?" response (screenedForPain).
                  const mode = deriveModeFromScreening(v);
                  u("painMapMode", mode);
                  if (mode === "verbal") {
                    u("assessmentTool", "Numeric (0-10)");
                  } else if (mode === "non-verbal") {
                    u("assessmentTool", "PAINAD");
                  } else if (mode === "pediatric") {
                    u("assessmentTool", "FLACC");
                  }
                }
              };

              // Size each field to the columns it actually needs instead of
              // defaulting long-form types to the full card width. CSS grid
              // auto-placement then packs short neighbors onto the same row
              // (e.g. a 3-option radio group and a select can share a row),
              // so nothing sits alone with empty space beside it.
              const fieldSpan = getFieldSpan(fieldForRender);

              let rendered;
              switch (fieldForRender.type) {
                case "groupLabel":
                  // Presentational-only sub-header (2026-10-03 density pass):
                  // no path, no data binding, nothing persisted/rendered to
                  // the record -- purely a visual divider so a card's field
                  // list can read as two labeled groups (e.g. "SCREENING" /
                  // "ASSESSMENT") without splitting it into a second card.
                  rendered = (
                    <div style={{
                      fontSize: 10.5, fontWeight: 700, letterSpacing: 0.6, textTransform: "uppercase",
                      color: COLORS.gray, borderBottom: `1px solid ${COLORS.border}`,
                      paddingBottom: 4, marginTop: fi === 0 ? 0 : 10, marginBottom: 2,
                    }}>
                      {fieldForRender.label}
                    </div>
                  );
                  break;
                case "input":
                  rendered = <FormInput label={fieldForRender.label} value={value} onChange={onChange}
                    type={fieldForRender.inputType} placeholder={fieldForRender.placeholder} required={fieldForRender.required} hopeCode={fieldForRender.hopeCode} />;
                  break;
                case "textarea":
                  rendered = <FormTextarea label={fieldForRender.label} value={value} onChange={onChange}
                    placeholder={fieldForRender.placeholder} rows={fieldForRender.rows} />;
                  break;
                case "quickPickTextarea":
                  rendered = <FormQuickPickTextarea label={fieldForRender.label} value={value} onChange={onChange}
                    presets={fieldForRender.presets} placeholder={fieldForRender.placeholder} rows={fieldForRender.rows} />;
                  break;
                case "select":
                  rendered = <FormSelect label={fieldForRender.label} value={value} onChange={onChange}
                    options={fieldForRender.options} required={fieldForRender.required} hopeCode={fieldForRender.hopeCode} />;
                  break;
                case "radio":
                  rendered = <FormRadioGroup label={fieldForRender.label} value={value} onChange={onChange}
                    options={fieldForRender.options} hopeCode={fieldForRender.hopeCode} sfv={fieldForRender.sfv} />;
                  break;
                case "gatedRadio":
                  rendered = <FormGatedRadio label={fieldForRender.label} value={value} onChange={onChange}
                    primaryOptions={fieldForRender.primaryOptions} normalValues={fieldForRender.normalValues}
                    detailOptions={fieldForRender.detailOptions} hopeCode={fieldForRender.hopeCode} />;
                  break;
                case "checkboxGroup":
                  rendered = <FormCheckboxGroup label={fieldForRender.label} values={value || []} onChange={onChange}
                    options={fieldForRender.options} hopeCode={fieldForRender.hopeCode} />;
                  break;
                case "segmented":
                  rendered = <FormSegmented label={fieldForRender.label} value={value} onChange={onChange}
                    options={fieldForRender.options} hopeCode={fieldForRender.hopeCode} sfv={fieldForRender.sfv} aliases={fieldForRender.aliases} />;
                  break;
                case "pillGroup":
                  rendered = <FormPillGroup label={fieldForRender.label} values={value || []} onChange={onChange}
                    options={fieldForRender.options} hopeCode={fieldForRender.hopeCode} />;
                  break;
                case "note":
                  // OWNER-DIRECTED "Dyspnea Ownership Model" (2026-09-28,
                  // Contradiction 5) -- a non-interactive, non-blocking
                  // guidance line (e.g. "Document dyspnea in Respiratory
                  // before assigning cardiac attribution."). Read-only:
                  // never written to storage, never gates save.
                  rendered = <p style={{ fontSize: 12, fontStyle: "italic", color: COLORS.textMuted || "#6b7280", margin: "2px 0" }}>{fieldForRender.label}</p>;
                  break;
                case "legacyReadOnly": {
                  // Owner directive (2026-09-28) "Cardiovascular
                  // Symptom-Focused Scope Correction" Section 5 -- a
                  // stored legacy value that must remain visible (never
                  // deleted/nulled/rewritten) but must not be presented as
                  // an editable current-entry control. Renders whatever
                  // string the field's own `legacyFormat` produces; never
                  // calls onChange, so it cannot write to the record.
                  const legacyText = typeof fieldForRender.legacyFormat === "function"
                    ? fieldForRender.legacyFormat(value)
                    : (Array.isArray(value) ? value.join(", ") : String(value ?? ""));
                  rendered = (
                    <div style={styles.formGroup}>
                      <label style={styles.label}>{fieldForRender.label}</label>
                      <p style={{ fontSize: 13, color: COLORS.dark, margin: "2px 0", fontStyle: "italic" }} data-legacy-readonly="true">
                        {legacyText}
                      </p>
                    </div>
                  );
                  break;
                }
                case "booleanPillRow": {
                  // Compact multi-path boolean row (e.g. Orientation's 5
                  // independent time/place/person/situation/disoriented
                  // booleans) rendered as one line of toggle pills instead
                  // of a vertical checkbox stack. Each pill still reads and
                  // writes its own existing path via the same update()
                  // used everywhere else -- no data shape change -- and
                  // re-applies the same section-specific mutual-exclusivity
                  // rule the generic per-path onChange interceptor above
                  // already applies to individual "checkbox" fields.
                  // GitHub Directive (2026-09-28) "Bounded Compatibility
                  // Increment" Section 10/AC-05 -- an optional data-driven
                  // "quick action" convenience button (currently used only
                  // for Orientation's "Mark Oriented x4") that sets/clears
                  // a batch of the SAME already-existing boolean paths this
                  // row already reads/writes. It stores no new field and
                  // no "Oriented x4" value anywhere -- its pressed state is
                  // derived each render from whether every setPath is true
                  // and every clearPath is false, so manually clearing any
                  // one dimension automatically un-highlights the shortcut
                  // without any extra bookkeeping.
                  const quickAction = fieldForRender.quickAction;
                  const quickActionActive = quickAction
                    ? quickAction.setPaths.every((p) => Boolean(getNestedValue(cardData, p)))
                      && (quickAction.clearPaths || []).every((p) => !getNestedValue(cardData, p))
                    : false;
                  rendered = (
                    <div style={styles.formGroup}>
                      <label style={styles.label}>{fieldForRender.label}</label>
                      <div role="group" aria-label={fieldForRender.label} style={{ display: "flex", flexWrap: "wrap", gap: 3, alignItems: "center" }}>
                        {quickAction && (
                          <button
                            type="button"
                            aria-pressed={quickActionActive}
                            onClick={() => {
                              quickAction.setPaths.forEach((p) => update(cardDataSection, p, true));
                              (quickAction.clearPaths || []).forEach((p) => update(cardDataSection, p, false));
                            }}
                            style={{
                              padding: "2px 9px", fontSize: 11, lineHeight: 1.6, borderRadius: 999,
                              cursor: "pointer", border: `1px solid ${quickActionActive ? COLORS.teal : COLORS.border}`,
                              background: quickActionActive ? COLORS.teal : "transparent",
                              color: quickActionActive ? COLORS.textOnTeal : COLORS.dark,
                              fontWeight: 700, whiteSpace: "nowrap", fontStyle: "italic",
                            }}
                          >
                            {quickAction.label}
                          </button>
                        )}
                        {fieldForRender.items.map((item) => {
                          const itemChecked = Boolean(getNestedValue(cardData, item.path));
                          const handleToggle = () => {
                            const next = !itemChecked;
                            update(cardDataSection, item.path, next);
                            if (sectionKey === "neurological" && item.path === "orientation.disoriented" && next) {
                              ["orientation.time", "orientation.place", "orientation.person", "orientation.situation"].forEach((p) => update(cardDataSection, p, false));
                            }
                            if (sectionKey === "neurological" && ["orientation.time", "orientation.place", "orientation.person", "orientation.situation"].includes(item.path) && next) {
                              update(cardDataSection, "orientation.disoriented", false);
                            }
                          };
                          return (
                            <button
                              type="button" key={item.path} aria-pressed={itemChecked}
                              className="rnica-segment-btn"
                              onClick={handleToggle}
                              style={{
                                padding: "2px 9px", fontSize: 11, lineHeight: 1.6, borderRadius: 999,
                                cursor: "pointer", border: `1px solid ${itemChecked ? COLORS.teal : COLORS.border}`,
                                background: itemChecked ? COLORS.teal : "transparent",
                                color: itemChecked ? COLORS.textOnTeal : COLORS.dark,
                                fontWeight: itemChecked ? 700 : 500, whiteSpace: "nowrap",
                              }}
                            >
                              {item.label}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                  break;
                }
                case "triState":
                  rendered = <FormTriState label={fieldForRender.label} value={value} onChange={onChange} hopeCode={fieldForRender.hopeCode} />;
                  break;
                // Cardiovascular Execution Plan (2026-09-28) Child Issue 2 --
                // "no editable Cardiovascular field displays the legacy
                // square checkbox... tri-state fields use the existing
                // Neurological assessment-state primitive." Reuses
                // FormSegmented (already Neurological's pill/segmented
                // control) with the same fixed Not Assessed/No/Yes option
                // set and normalizeTriState value handling as FormTriState
                // -- identical stored value contract ("" / "No" / "Yes"),
                // purely a visual swap. FormTriState itself is untouched
                // and keeps rendering for every other body system still
                // using `type: "triState"`.
                case "segmentedTriState":
                  rendered = <FormSegmented label={fieldForRender.label} value={normalizeTriState(value)}
                    onChange={onChange} hopeCode={fieldForRender.hopeCode} sfv={fieldForRender.sfv}
                    options={[
                      { value: "", label: "Not Assessed" },
                      { value: "No", label: "No" },
                      { value: "Yes", label: "Yes" },
                    ]} />;
                  break;
                case "checkbox":
                  rendered = <FormCheckbox label={fieldForRender.label} checked={value} onChange={onChange} />;
                  break;
                case "booleanPill":
                  rendered = <FormBooleanPill label={fieldForRender.label} checked={value} onChange={onChange} />;
                  break;
                default:
                  rendered = null;
              }
              if (!rendered) return null;
              return <div key={fi} style={fieldSpan === "full" ? styles.fieldSpanFull : { gridColumn: `span ${fieldSpan}` }}>{rendered}</div>;
            })}
            </div>
            {!isBodySystemPilotCard && POC_ENABLED_SECTIONS.has(cardDataSection) && card.fields && (
              <PocSectionControls
                assessmentId={assessmentId}
                sectionKey={cardDataSection}
                cardTitle={card.title}
                styles={styles}
                COLORS={COLORS}
              />
            )}
          </Card>
        );
  });

  // Body Systems 9-part structure: group the already-rendered cardsContent
  // (post all conditional-null filters above -- pain/skin custom-renderer
  // suppression, spiritual field filtering, etc. are untouched) by each
  // card's declared `category`, defaulting to "core" so an untagged card is
  // never silently dropped from the workspace. Purely a final-assembly
  // reorder; no field, data shape, HOPE mapping, or POC control changes.
  const bodySystemSummary = isBodySystemWorkspace ? computeBodySystemSummary(sectionKey, data) : null;

  const bodySystemGroupedContent = isBodySystemWorkspace
    ? BODY_SYSTEM_CATEGORY_ORDER.map((category) => {
        const items = resolvedCards
          .map((card, ci) => ({ ci, category: card.category || "core" }))
          .filter((entry) => entry.category === category && cardsContent[entry.ci] != null)
          .map((entry) => cardsContent[entry.ci]);
        if (items.length === 0) return null;
        return (
          <div key={category} className="rnica-bodysystem-group" data-category={category}>
            <h4 className="rnica-bodysystem-group__heading">{BODY_SYSTEM_CATEGORY_LABELS[category]}</h4>
            <div className="rnica-bodysystem-group__cards">{items}</div>
          </div>
        );
      })
    : null;

  return (
    <>
      {subtitle && <p className="rnica-form-section__subtitle" style={styles.sectionSubtitle}>{subtitle}</p>}
      {sectionKey === "sfv" && (
        <SfvStatusCard patientId={patientId} onNavigateToSection={onNavigateToSection} onSyncCompletionStatus={(completed, completedAt) => {
          u("inPersonSfvCompleted", completed);
          u("sfvDate", completedAt || "");
        }} styles={styles} COLORS={COLORS} />
      )}
      {isBodySystemWorkspace ? (
        // Body Systems architectural correction: the AccordionTrigger in
        // RNICACommandWorkspace.jsx already shows the system name/status,
        // so this single outer shadcn Card renders content only (no
        // CardHeader/title -- avoids a duplicate heading). Generic
        // fallback cards and customRenderer widgets inside it render
        // `bare` so they read as inline groups within this one box
        // instead of N separate bordered cards, and the section gets ONE
        // consolidated Add/View/Update/Resolve POC control instead of one
        // per sub-card.
        <ShadcnCard className="rnica-bodysystem-workspace">
          <ShadcnCardContent className="rnica-bodysystem-workspace__content">
            {bodySystemSummary && (
              <div className="rnica-bodysystem-summary" data-requires-follow-up={bodySystemSummary.requiresFollowUp}>
                <h4 className="rnica-bodysystem-summary__heading">Summary</h4>
                <p className="rnica-bodysystem-summary__status">{bodySystemSummary.status}</p>
                {bodySystemSummary.primaryIssues.length > 0 && (
                  <ul className="rnica-bodysystem-summary__issues">
                    {bodySystemSummary.primaryIssues.map((issue, ii) => <li key={ii}>{issue}</li>)}
                  </ul>
                )}
                {bodySystemSummary.requiresFollowUp && (
                  <p className="rnica-bodysystem-summary__flag">Requires Follow-Up</p>
                )}
              </div>
            )}
            {bodySystemGroupedContent}
            {POC_ENABLED_SECTIONS.has(sectionKey) && (
              <PocSectionControls
                assessmentId={assessmentId}
                sectionKey={sectionKey}
                cardTitle={title}
                styles={styles}
                COLORS={COLORS}
                {...(sectionKey === "neurological"
                  ? {
                      canAdd: neurologicalHasActionablePocFinding(data || {}),
                      suggestedFinding: neurologicalHasActionablePocFinding(data || {}),
                    }
                  : sectionKey === "cardiovascular"
                  ? {
                      canAdd: cardiovascularHasActionablePocFinding(data || {}),
                      suggestedFinding: cardiovascularHasActionablePocFinding(data || {}),
                    }
                  : null)}
              />
            )}
          </ShadcnCardContent>
        </ShadcnCard>
      ) : (
        <div className={
          workspacePilot && sectionKey === "diagnoses" ? "rnica-pilot-diagnoses-grid"
          : workspacePilot && sectionKey === "performanceStatus" ? "rnica-performance-grid"
          : undefined
        }>
          {cardsContent}
        </div>
      )}
    </>
  );
}

// Decide how many grid columns (of the ~150px fieldsGrid track) a field
// should occupy. Only true long-form content (large narrative textareas,
// very large option sets) claims the full card width; everything else gets
// just enough columns to fit its own content so grid auto-placement can pack
// several short controls onto the same row instead of stacking them one per
// row with wasted space to the right.
function getFieldSpan(field) {
  // GitHub Directive (2026-09-28) "Neurological Review -- Average Sleep
  // Hours, Clinical Relevance, and Final Density Refinement" Issue #5/#9 --
  // an explicit per-field override so a card's author can hand-tune a
  // tighter grid (e.g. Communication and Sensory, HOPE alignment) instead
  // of relying only on the heuristics below. Optional; every existing
  // field config omits it and falls through unchanged.
  if (field.fieldSpan !== undefined) return field.fieldSpan;
  const options = field.options || [];
  const maxLabelLen = options.reduce((m, o) => Math.max(m, String(typeof o === "string" ? o : o.label).length), 0);

  if (field.type === "textarea" || field.type === "quickPickTextarea") {
    // Big narrative fields (explicit rows >= 4) still want real typing room;
    // short single-line-ish notes fields can share a row with a neighbor.
    // Bug fix (2026-10-03 density pass): quickPickTextarea fell through to
    // the default span-1 below, squeezing its whole preset-chip row + the
    // textarea underneath into a single ~200px column and inflating the
    // card's height with chips wrapping one-per-line -- it needs the same
    // sizing as a plain textarea.
    return (field.rows || 3) >= 4 ? "full" : 3;
  }
  if (field.type === "radio" || field.type === "segmented") {
    if (options.length <= 2) return 1;
    if (options.length <= 4 && maxLabelLen <= 20) return 2;
    if (options.length <= 6) return 3;
    return "full";
  }
  if (field.type === "checkboxGroup" || field.type === "pillGroup") {
    // Now rendered as a horizontal wrapping row of pills, so it behaves
    // like a radio group: give it enough columns for its options to flow
    // across 1-2 lines instead of one cramped narrow column.
    if (options.length <= 2) return 1;
    if (options.length <= 4 && maxLabelLen <= 20) return 2;
    if (options.length <= 6) return 3;
    return "full";
  }
  if (field.type === "booleanPillRow") {
    // One compact toggle-pill row spanning several boolean paths (e.g.
    // Orientation) -- give it the same room a multi-option pill/radio row
    // gets so it doesn't wrap onto a cramped single column.
    const items = field.items || [];
    const maxItemLabelLen = items.reduce((m, it) => Math.max(m, String(it.label).length), 0);
    if (items.length <= 4 && maxItemLabelLen <= 20) return 2;
    return 3;
  }
  return 1;
}

// Utility to get/set nested values
function getNestedValue(obj, path) {
  if (!path) return undefined;
  return path.split(".").reduce((curr, key) => curr?.[key], obj);
}

function setNestedValue(obj, path, value) {
  // Guard against a missing/undefined section state (e.g. a formData section
  // that has not yet been initialized for an older/partial persisted record).
  // Without this, JSON.stringify(undefined) => undefined and the subsequent
  // JSON.parse(undefined) throws, crashing the entire RNICA tree with no
  // error boundary to catch it (this was the root cause of the Living
  // Environment "not working at all" crash).
  const clone = obj == null ? {} : JSON.parse(JSON.stringify(obj));
  const keys = path.split(".");
  let curr = clone;
  for (let i = 0; i < keys.length - 1; i++) {
    if (!curr[keys[i]]) curr[keys[i]] = {};
    curr = curr[keys[i]];
  }
  curr[keys[keys.length - 1]] = value;
  return clone;
}


// ════════════════════════════════════════════════════════════════
// 7. SECTION CONFIGS — All remaining 27 modules
// ════════════════════════════════════════════════════════════════

const SECTION_CONFIGS = {
  vitals: {
    title: "Vitals & Measurements",
    subtitle: "Temperature, pulse, respirations, blood pressure, anthropometrics, IV assessment",
    cards: [
      {
        title: "Vital Signs",
        customRenderer: "vitalSignsClinical",
      },
      {
        title: "Anthropometrics",
        customRenderer: "anthropometricsAutoBmi",
      },
      {
        title: "IV Assessment", fields: [
          { type: "checkbox", label: "Patient has IV access", path: "ivAssessment.hasIV" },
          { type: "select", label: "IV Type", path: "ivAssessment.type", options: ["Peripheral", "Central", "PICC", "Port"] },
          { type: "input", label: "Size (gauge)", path: "ivAssessment.size" },
          { type: "input", label: "Site/Location", path: "ivAssessment.site" },
          { type: "select", label: "Dressing Type", path: "ivAssessment.dressingType", options: ["Tegaderm", "Gauze", "Other"] },
          { type: "input", label: "Insertion Date", path: "ivAssessment.insertionDate", inputType: "date" },
          { type: "input", label: "Last Change Date", path: "ivAssessment.lastChangeDate", inputType: "date" },
          { type: "select", label: "Condition", path: "ivAssessment.condition", options: ["Patent", "Infiltrated", "Phlebitis", "Occluded"] },
          { type: "textarea", label: "IV Notes", path: "ivAssessment.notes" },
        ],
      },
    ],
  },

  pain: {
    title: "Pain Assessment",
    subtitle: "Use the patient communication status to select the correct pain scale: verbal patients use numerical pain scoring, non-verbal patients use PAINAD or FLACC based on nurse selection, and pediatric patients use FLACC. [Information hierarchy regrouped 2026-10 to match the Neurological architecture -- no field, option, path, or HOPE mapping changed, only which named section each field renders under.]",
    cards: [
      // 1. Pain Overview -- the triage front door (HOPE J0900 A-D, J0905,
      // and the self-report/comfort/active-problem questions), same role
      // as the Neurological Overview card: establishes the top-level
      // picture before any detail section below is reached.
      {
        title: "Pain Overview", hopeCode: "J0900", fields: [
          // Reorganized (2026-10-03 density pass) into two labeled groups --
          // SCREENING (did we screen, and when) then ASSESSMENT (what the
          // screening found) -- per explicit layout directive. Same fields,
          // same paths, same options, same order within each group as
          // before; only the visual grouping + a non-data groupLabel marker
          // changed. GitHub UI Directive (2026-10-03) "Neuro Interaction
          // Parity" -- every exclusive single-choice field below uses
          // `type: "segmented"` (compact chip row) instead of `type:
          // "radio"` (large circular-radio stack), the same opt-in swap
          // already applied throughout Neurological/Cardiovascular. Same
          // options array/value/onChange contract -- no data shape change.
          { type: "groupLabel", label: "Screening" },
          { type: "segmented", label: "A. Was the patient screened for pain? (HOPE J0900.A)", path: "screenedForPain", hopeCode: "J0900", fieldSpan: 2, options: [
            { value: "0", label: "No — skip to Pain Active Problem (J0905)" }, { value: "1", label: "Yes" }
          ]},
          // Reason not assessed: shown only when screenedForPain = No.
          // Free text so it never has to fit CMS's binary J0900.A coding.
          { type: "textarea", label: "Reason pain assessment was not completed", path: "reasonNotAssessed", fieldSpan: "full" },
          { type: "input", label: "B. Date of first screening for pain", path: "screeningDate", inputType: "date" },

          { type: "groupLabel", label: "Assessment" },
          { type: "segmented", label: "D. Type of standardized pain tool used: (HOPE J0900.D)", path: "standardizedPainToolType", hopeCode: "J0900", fieldSpan: "full", options: [
            { value: "1", label: "Numeric" }, { value: "2", label: "Verbal descriptor" }, { value: "3", label: "Patient visual" }, { value: "4", label: "Staff observation" }, { value: "9", label: "No standardized tool used" }
          ]},
          { type: "segmented", label: "Can the patient reliably self-report pain? (drives pain scale below, not a HOPE response)", path: "verbalizesPain", fieldSpan: 2, options: [
            { value: "0", label: "No" }, { value: "1", label: "Yes, reliably" }, { value: "2", label: "Sometimes" }, { value: "3", label: "Unable to determine" }
          ]},
          { type: "segmented", label: "C. The patient's pain severity was: (HOPE J0900.C)", path: "painSeverityCategory", hopeCode: "J0900", fieldSpan: "full", options: [
            { value: "0", label: "None" }, { value: "1", label: "Mild" }, { value: "2", label: "Moderate" }, { value: "3", label: "Severe" }, { value: "9", label: "Pain not rated" }
          ]},
          // Section 10: conceptually distinct from "current pain" -- a
          // patient can deny pain right now and still have an active pain
          // problem requiring ongoing management/monitoring. AI may
          // propose this (see AI Insights); the RN always confirms.
          { type: "segmented", label: "Is pain an active problem? (J0905)", path: "painActiveProblem", hopeCode: "J0905", fieldSpan: 2, options: [
            { value: "1", label: "Yes" }, { value: "0", label: "No" }, { value: "9", label: "Unable to determine" }
          ]},
          // Section 4: current pain is conceptually distinct from HOPE
          // J0900.C severity-in-general and from pain-as-active-problem.
          { type: "segmented", label: "Is the patient experiencing pain now?", path: "currentPain", fieldSpan: 2, options: [
            { value: "1", label: "Yes" }, { value: "0", label: "No" }, { value: "9", label: "Unable to determine" }
          ]},
          { type: "segmented", label: "Is the patient uncomfortable because of pain?", path: "uncomfortableBecauseOfPain", fieldSpan: 2, options: [
            { value: "0", label: "No" }, { value: "1", label: "Yes" }, { value: "9", label: "Unable to determine" }
          ]},
        ],
      },
      // 2. Pain Intensity -- the longitudinal intensity picture
      // (current/worst/best/acceptable). The three tool-specific cards
      // immediately below share this same section title because only one
      // of them ever renders at a time (Numeric for verbal patients,
      // FLACC for pediatric, PAINAD for non-verbal adults -- see
      // painAssessmentMode).
      {
        title: "Pain Intensity", fields: [
          { type: "select", label: "Pain scale selected", path: "assessmentTool", options: ["Numeric (0-10)"] },
          { type: "input", label: "Current intensity", path: "painIntensity.current", inputType: "number" },
          { type: "input", label: "Worst in 24 hours", path: "painIntensity.worst", inputType: "number" },
          { type: "input", label: "Best in 24 hours", path: "painIntensity.best", inputType: "number" },
          { type: "input", label: "Acceptable level", path: "painIntensity.acceptable", inputType: "number" },
          { type: "booleanPill", label: "Comprehensive pain assessment completed", path: "comprehensiveAssessmentCompleted" },
          { type: "input", label: "Comprehensive pain assessment date", path: "comprehensiveAssessmentDate", inputType: "date" },
        ],
      },
      {
        title: "Pain Intensity", fields: [
          { type: "select", label: "Face", path: "flacc.face", options: [{ value: "0", label: "0 — No particular expression" }, { value: "1", label: "1 — Occasional grimace or frown" }, { value: "2", label: "2 — Frequent to constant frown, clenched jaw" }] },
          { type: "select", label: "Legs", path: "flacc.legs", options: [{ value: "0", label: "0 — Normal position or relaxed" }, { value: "1", label: "1 — Uneasy, restless, tense" }, { value: "2", label: "2 — Kicking or legs drawn up" }] },
          { type: "select", label: "Activity", path: "flacc.activity", options: [{ value: "0", label: "0 — Lying quietly, normal movement" }, { value: "1", label: "1 — Squirming, shifting, tense" }, { value: "2", label: "2 — Arched, rigid, or jerking" }] },
          { type: "select", label: "Cry", path: "flacc.cry", options: [{ value: "0", label: "0 — No cry or moan" }, { value: "1", label: "1 — Moans or occasional complaint" }, { value: "2", label: "2 — Cries steadily, screams, or sobs" }] },
          { type: "select", label: "Consolability", path: "flacc.consolability", options: [{ value: "0", label: "0 — Content or relaxed" }, { value: "1", label: "1 — Reassured by touch or voice" }, { value: "2", label: "2 — Difficult to comfort or console" }] },
        ],
      },
      {
        title: "Pain Intensity", fields: [
          { type: "select", label: "Breathing", path: "painad.breathing", options: [{ value: "0", label: "0 — Normal" }, { value: "1", label: "1 — Occasional labored" }, { value: "2", label: "2 — Noisy labored" }] },
          { type: "select", label: "Vocalization", path: "painad.vocalization", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Occasional moan" }, { value: "2", label: "2 — Repeated calling out" }] },
          { type: "select", label: "Facial expression", path: "painad.facialExpression", options: [{ value: "0", label: "0 — Smiling/inexpressive" }, { value: "1", label: "1 — Sad/frightened" }, { value: "2", label: "2 — Grimacing" }] },
          { type: "select", label: "Body language", path: "painad.bodyLanguage", options: [{ value: "0", label: "0 — Relaxed" }, { value: "1", label: "1 — Tense/fidgeting" }, { value: "2", label: "2 — Rigid/striking" }] },
          { type: "select", label: "Consolability", path: "painad.consolability", options: [{ value: "0", label: "0 — No need" }, { value: "1", label: "1 — Distracted/reassured" }, { value: "2", label: "2 — Unable to console" }] },
        ],
      },
      // 3. Pain History -- the chronic/recurrent-history gate plus its
      // detail sub-fields (baseline/tolerance/threshold/management-
      // approach/control-status), merged into one card (was two boxes:
      // a standalone one-field gate card and a separate detail card).
      // Same visibility rules as before: the whole card only applies once
      // the patient denies current pain (isPainHistoryCard card-level
      // gate), and the detail fields only apply once chronicPainHistory
      // = Yes (unchanged field-level gate below in the render loop).
      {
        title: "Pain History", fields: [
          { type: "segmented", label: "Does the patient have a history of chronic or recurrent pain?", path: "chronicPainHistory", options: [
            { value: "1", label: "Yes" }, { value: "0", label: "No" }, { value: "9", label: "Unknown" }, { value: "unable", label: "Unable to determine" }
          ]},
          { type: "textarea", label: "Chronic pain condition or source", path: "chronicPainCondition" },
          { type: "input", label: "Usual/baseline pain level (0-10, or \"Unable to quantify\")", path: "usualBaselinePainLevel" },
          { type: "input", label: "Patient's tolerable pain level before requesting intervention (0-10, \"Unable to identify\", or \"Not discussed\")", path: "tolerablePainLevel" },
          { type: "input", label: "Pain level that typically requires intervention (0-10, \"Unable to identify\", or \"Not discussed\")", path: "interventionThresholdLevel" },
          { type: "input", label: "Usual frequency or pattern", path: "usualFrequencyPattern" },
          { type: "pillGroup", label: "Current pain-management approach", path: "currentManagementApproach", options: ["Medication", "Positioning", "Heat", "Cold", "Massage", "Rest", "Distraction", "Other nonpharmacologic intervention", "No current intervention", "Unable to determine"] },
          { type: "segmented", label: "Current control status", path: "controlStatus", options: [
            { value: "Controlled", label: "Controlled" }, { value: "Partially controlled", label: "Partially controlled" }, { value: "Uncontrolled", label: "Uncontrolled" }, { value: "Unable to determine", label: "Unable to determine" }
          ]},
        ],
      },
      // 4. Location -- the visual body silhouette plus the location
      // checklist. Verbal-patients-only, same as before (see
      // shouldRenderLocationCard). Stays collapsed by default (secondary
      // interaction): the body map consumes significant vertical space
      // the nurse doesn't need in view while reviewing Pain Management/
      // treatment response -- Pain Overview and Pain Management stay open.
      {
        title: "Location", fields: [
          { type: "pillGroup", label: "Pain location", path: "painLocation", options: ["Head", "Neck", "Chest", "Abdomen", "Back", "Upper extremities", "Lower extremities", "Generalized"] },
        ],
      },
      // 5. Pain Character & Impact -- merges the former Pain Type,
      // Characteristics, and Functional Impact cards (was 3 boxes) into
      // one. Neuropathic classification (HOPE J0915) and pain character
      // always apply; onset/duration/aggravating/relieving/functional-
      // impact are verbal-patients-only (PAIN_VERBAL_ONLY_PATHS field-
      // level gate in the render loop replaces the old per-card mode
      // gate) and current-pain-or-chronic-history-only (unchanged
      // field-level gate). Stays collapsed by default, same convention as
      // Location, to keep this detail out of view while Pain Management
      // is being reviewed.
      {
        title: "Pain Character & Impact", fields: [
          { type: "segmented", label: "Does the patient have neuropathic pain (e.g., pain with burning, tingling, pins and needles, hypersensitivity to touch)? (HOPE J0915)", path: "neuropathicPain", hopeCode: "J0915", options: [
            { value: "0", label: "No" }, { value: "1", label: "Yes" }
          ]},
          { type: "pillGroup", label: "Supporting neuropathic characteristics", path: "neuropathicCharacteristics", options: ["Burning", "Tingling", "Pins and needles", "Electric/shooting quality", "Hyperesthesia", "Allodynia (pain to light touch)", "Other documented characteristic"] },
          // fieldSpan overrides below (2026-10-03 density pass): these
          // pillGroups' option counts push the default heuristic to "full"
          // width, forcing neuropathicPain (a 2-option Yes/No) to sit alone
          // in its own row with empty space beside it, and stacking
          // Aggravating/Relieving as two separate full-width rows. Same
          // fields, same paths, same options -- only how many grid columns
          // each claims, so neuropathicPain shares Pain Character's row and
          // Aggravating/Relieving share one row instead of two.
          { type: "pillGroup", label: "Pain character", path: "painCharacter", fieldSpan: 3, options: ["Sharp", "Dull", "Aching", "Burning", "Stabbing", "Throbbing", "Cramping", "Shooting", "Pressure"] },
          { type: "textarea", label: "Onset & progression", path: "painOnsetProgression" },
          { type: "input", label: "Duration & frequency", path: "painDurationFrequency" },
          { type: "pillGroup", label: "Aggravating factors", path: "aggravatingFactors", fieldSpan: 2, options: ["Movement", "Coughing", "Eating", "Position change", "Touch", "Stress", "Weather"] },
          { type: "pillGroup", label: "Relieving factors", path: "relievingFactors", fieldSpan: 2, options: ["Medication", "Rest", "Heat", "Cold", "Position change", "Distraction", "Massage"] },
          { type: "quickPickTextarea", label: "Effect on function or quality of life", path: "effectOnFunction", presets: ["Limits mobility/ambulation", "Disrupts sleep", "Limits ADLs", "Decreases appetite", "Limits social engagement", "Causes mood/irritability changes", "No functional impact reported"] },
        ],
      },
      // 6. Pain Management -- unchanged from the prior architecture.
      {
        // Section 14 (simplified 2026-09-26 per owner request): harvest
        // from the medication list first (see PainMedicationHarvestBanner
        // above the fields grid) -- Type/Route/Breakthrough are
        // auto-detected from active medications when possible, RN
        // verifies/corrects. Detailed regimen text, last-breakthrough-dose,
        // and administration-history fields were removed from the primary
        // admission workflow (better suited to medication management /
        // follow-up visits, not admission documentation burden).
        title: "Pain Management", fields: [
          { type: "segmented", label: "Routine pain medication present?", path: "routinePainMedicationPresent", options: [
            { value: "1", label: "Yes" }, { value: "0", label: "No" }, { value: "9", label: "Unknown" }
          ]},
          { type: "segmented", label: "Pain medication type", path: "painMedicationType", options: [
            { value: "Opioid", label: "Opioid" }, { value: "Non-Opioid", label: "Non-Opioid" }, { value: "Both", label: "Both" }
          ]},
          // fieldSpan overrides (2026-10-03 density pass, same rationale as
          // Pain Character & Impact above): Route (7 options) and
          // Non-Pharmacological Interventions (9 options) each defaulted to
          // full card width and stacked as two separate full rows. Pairing
          // them onto one row makes this a genuine two-column layout instead
          // of two chip rows each spanning the entire viewport.
          { type: "pillGroup", label: "Route", path: "painMedicationRoute", fieldSpan: 2, options: PAIN_ROUTE_OPTIONS },
          { type: "segmented", label: "Breakthrough pain medication present?", path: "breakthroughPainMedication", options: [
            { value: "1", label: "Yes" }, { value: "0", label: "No" }, { value: "9", label: "Unknown" }
          ]},
          { type: "pillGroup", label: "Non-Pharmacological Interventions", path: "nonPharmInterventions", fieldSpan: 2, options: ["Repositioning", "Heat therapy", "Cold therapy", "Massage", "Music therapy", "Guided imagery", "Relaxation techniques", "TENS unit", "Distraction"] },
          { type: "segmented", label: "Effectiveness", path: "painEffectivenessRating", options: [
            { value: "Effective", label: "Effective" }, { value: "Partially Effective", label: "Partially Effective" }, { value: "Ineffective", label: "Ineffective" }, { value: "Unable To Determine", label: "Unable To Determine" }
          ]},
          { type: "textarea", label: "Pain Management Notes (optional)", path: "painManagementPlan" },
        ],
      },
      // Three derived/read-only cards follow Pain Management. Each is
      // grounded-only (never fabricates) and the AI Insights and Overdue
      // Alerts cards render nothing at all -- no card, no placeholder --
      // when there is no supported finding/triggered rule (see the
      // customRenderer dispatch above for the hide-when-empty guards).
      // 7. Clinical Summary (+ its overdue-action companion card).
      { title: "Clinical Summary", customRenderer: "painAssessmentSummary" },
      { title: "Overdue Action Alerts", customRenderer: "painOverdueAlerts" },
      // 8. AI Insights.
      { title: "AI Insights", customRenderer: "aiPainAnalysis" },
    ],
  },

  // symptomImpact intentionally has no RN-facing section config (owner
  // correction 2026-09-25): each J2051 symptom is documented once, in its
  // true owning section, never re-asked here. See the symptomImpact
  // default-state comment and its background sync effect for how HOPE
  // J2051 export/SFV/reporting still derive from those source fields.

  diagnoses: {
    title: "Diagnoses",
    subtitle: "Primary/Secondary Dx, comorbidities, disease trajectory, and LCD eligibility",
    cards: [
      // RNICA Diagnosis & LCD Workspace Optimization (owner-approved
      // directive): Primary Diagnosis + Terminal Prognosis merged into one
      // compact search-driven container (FR-003/FR-004); LCD moved
      // immediately after diagnosis, with its supporting-evidence card
      // directly below it, ahead of Secondary Diagnoses/HOPE Comorbidities
      // (FR-006/FR-010) -- see PrimaryTerminalDiagnosisCard above for the
      // auto-populate logic and the customRenderer dispatch above for how
      // each of these renders.
      {
        title: "Primary Terminal Diagnosis", hopeCode: "I0010", customRenderer: "primaryTerminalDiagnosis",
      },
      {
        title: "LCD Eligibility",
        customRenderer: "lcdEligibility",
      },
      {
        title: "LCD Supporting Evidence",
        customRenderer: "lcdSupportingEvidence",
      },
      {
        title: "Secondary Diagnoses",
        customRenderer: "secondaryDiagnoses",
      },
      {
        title: "Comorbidities and Co-existing Conditions",
        hopeCode: "I0100-I8005",
        customRenderer: "hopeComorbidities",
      },
    ],
  },

  performanceStatus: {
    title: "Performance Status",
    subtitle: "PPS, KPS, ECOG, FAST, NYHA scales with justifications, and ADL assessment",
    cards: [
      // Pilot-only cards below (functionalStatusSummary/scaleGroupLabel/
      // mobilityTransferSummary) are hidden entirely in legacy mode -- see
      // the sectionKey === "performanceStatus" guards in the renderer.
      {
        title: "Functional Status Summary",
        customRenderer: "functionalStatusSummary",
      },
      {
        title: "Core Hospice Functional Scales",
        customRenderer: "scaleGroupLabel",
      },
      {
        title: "Palliative Performance Scale (PPS)", hopeCode: "M1190", fields: [
          { type: "select", label: "PPS Score", path: "pps", hopeCode: "M1190", options: ["100%","90%","80%","70%","60%","50%","40%","30%","20%","10%","0%"] },
          { type: "textarea", label: "PPS Justification", path: "ppsJustification" },
        ],
      },
      {
        title: "Karnofsky Performance Scale (KPS)", fields: [
          { type: "select", label: "KPS Score", path: "kps", options: ["100","90","80","70","60","50","40","30","20","10","0"] },
          { type: "textarea", label: "KPS Justification", path: "kpsJustification" },
        ],
      },
      {
        title: "Specialized Diagnosis-Specific Scales",
        customRenderer: "scaleGroupLabel",
      },
      {
        title: "ECOG Performance Status", fields: [
          { type: "select", label: "ECOG Score", path: "ecog", options: [
            { value: "0", label: "0 — Fully active" }, { value: "1", label: "1 — Restricted but ambulatory" },
            { value: "2", label: "2 — Ambulatory, >50% waking hours" }, { value: "3", label: "3 — Limited self-care, >50% in bed" },
            { value: "4", label: "4 — Completely disabled" }, { value: "5", label: "5 — Dead" },
          ]},
          { type: "textarea", label: "ECOG Justification", path: "ecogJustification" },
        ],
      },
      {
        title: "FAST Scale (Dementia)", fields: [
          { type: "select", label: "FAST Stage", path: "fast", options: ["1","2","3","4","5","6a","6b","6c","6d","6e","7a","7b","7c","7d","7e","7f"] },
          { type: "input", label: "FAST Stage Description", path: "fastStage" },
        ],
      },
      {
        title: "NYHA Classification (Heart Failure)", fields: [
          { type: "select", label: "NYHA Class", path: "nyha", options: [
            { value: "I", label: "I — No limitation" }, { value: "II", label: "II — Slight limitation" },
            { value: "III", label: "III — Marked limitation" }, { value: "IV", label: "IV — Severe limitation" },
          ]},
          { type: "textarea", label: "NYHA Justification", path: "nyhaJustification" },
        ],
      },
      {
        title: "Functional Decline", id: "rnica-functional-decline-card", fields: [
          { type: "textarea", label: "Functional Decline Notes", path: "functionalDeclineNotes", rows: 4 },
        ],
      },
      // [PRESENTATION-ONLY RELOCATION] ADLs move into Functional Status'
      // presentation ownership per the visual-polish directive. Fields,
      // storage, validation, LCD facts, and POC ownership remain with
      // `musculoskeletal` (Body Systems) via `dataSection` -- see
      // RNICA_SCREEN_AUTHORITY_MATRIX.md.
      { title: "ADL Assessment (0=Independent, 5=Dependent)", id: "rnica-adl-assessment-card", dataSection: "musculoskeletal", customRenderer: "adlSummaryGrid", fields: [
        { type: "select", label: "Bathing", path: "adl.bathing", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup help only" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited assistance" }, { value: "4", label: "4 — Extensive assistance" }, { value: "5", label: "5 — Total dependence" }] },
        { type: "select", label: "Dressing", path: "adl.dressing", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited" }, { value: "4", label: "4 — Extensive" }, { value: "5", label: "5 — Total" }] },
        { type: "select", label: "Toileting", path: "adl.toileting", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited" }, { value: "4", label: "4 — Extensive" }, { value: "5", label: "5 — Total" }] },
        { type: "select", label: "Transferring", path: "adl.transferring", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited" }, { value: "4", label: "4 — Extensive" }, { value: "5", label: "5 — Total" }] },
        { type: "select", label: "Eating", path: "adl.eating", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited" }, { value: "4", label: "4 — Extensive" }, { value: "5", label: "5 — Total" }] },
        { type: "select", label: "Grooming", path: "adl.grooming", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited" }, { value: "4", label: "4 — Extensive" }, { value: "5", label: "5 — Total" }] },
      ]},
      {
        title: "Mobility & Transfer",
        customRenderer: "mobilityTransferSummary",
      },
      {
        title: "Change Since Last Assessment",
        customRenderer: "declineTracker",
      },
    ],
  },

  neurological: {
    title: "Neurological / Mental / Sensory",
    subtitle: "Consciousness, orientation, sleep/responsiveness, communication, cognition, BIMS (N0500-N0520)",
    cards: [
      {
        // GitHub Directive (2026-09-28) "Neurological Overview Gate" --
        // this single up-front triage question determines everything
        // else that renders below it (see the card-level guard next to
        // `resolvedCards.map`). It is deliberately its own card, first,
        // full-width, high-importance: the nurse must answer it before
        // any other Neurological control appears. New path (`neuroOverview`)
        // -- no existing field/value is touched.
        title: "Neurological Overview", category: "core", importance: "high", fullWidth: true, fields: [
          {
            type: "segmented", label: "Neurological Overview", path: "neuroOverview",
            options: [
              "No Current Neurological Concern",
              "Existing Neurological Findings Stable",
              "New/Worsening Neurological Findings",
              "Unable to Assess",
            ],
          },
          // Path 4 -- require a controlled reason instead of silently
          // skipping the whole system (same pattern as Pain's
          // reasonNotAssessed). New path; gated in the render loop below.
          {
            type: "segmented", label: "Reason Unable to Assess", path: "neuroUnableToAssessReason",
            options: ["Patient unable to participate", "Patient unresponsive", "Assessment interrupted", "Other"],
          },
          { type: "input", label: "Other Reason (if selected above)", path: "neuroUnableToAssessOther" },
        ],
      },
      // GitHub Directive (2026-09-28) "Final Neurological Density and
      // Space-Utilization Plan" Section 5 -- required order: Consciousness
      // / Orientation / Overall Change render as a 3-column "status" row
      // (all category "core", none full-width, so the existing auto-fit
      // grid packs them side by side); Sleep/Responsiveness then takes its
      // own full-width row (Section 11/21 -- previously squeezed into one
      // of 3 equal columns, making it look abnormally tall/imbalanced);
      // Communication and Sensory (merged) takes the next full-width row;
      // then Cognitive/Behavioral, Motor/Balance + Psychiatric (row), HOPE,
      // Notes. Presentation/grouping only -- no field removed, no path
      // renamed, no HOPE/SFV mapping touched.
      {
        title: "Consciousness", category: "core", importance: "high", fields: [
          {
            type: "segmented", label: "Level of Consciousness", path: "consciousness",
            // GitHub Review Major Issue #2 -- Awake/Alert and Coma/Comatose
            // are equivalent workflow states; consolidated to 6 visible
            // segments so they stop visually competing with each other.
            // Legacy stored "Awake"/"Coma" still display correctly via
            // aliases (resolved to Alert/Comatose) -- neither the option
            // list value nor the backend NEURO_CONSCIOUSNESS_* concept
            // registry (only ever mapped Alert/Lethargic/Obtunded/
            // Stuporous/Comatose) is changed.
            //
            // OWNER DIRECTIVE (2026-09-28) Clinical Blocker -- Awake and
            // Alert are distinct neurological concepts and must not be
            // presented as equivalent. The stored canonical value stays
            // "Alert" (no schema/migration change), but the label now
            // reads "Awake" only; no Alertness field exists, so nothing
            // in this UI or its narrative asserts "Alert".
            options: [
              { value: "Alert", label: "Awake" },
              "Lethargic", "Obtunded", "Stuporous",
              { value: "Minimally responsive", label: "Min. Responsive" },
              "Comatose",
              "Unable to assess",
            ],
            aliases: { Awake: "Alert", Coma: "Comatose" },
          },
        ],
      },
      {
        title: "Orientation", category: "core", importance: "high", fields: [
          {
            type: "booleanPillRow", label: "Orientation", items: [
              { label: "Time", path: "orientation.time" },
              { label: "Place", path: "orientation.place" },
              { label: "Person", path: "orientation.person" },
              { label: "Situation", path: "orientation.situation" },
              { label: "Disoriented", path: "orientation.disoriented" },
            ],
            // Section 10/AC-05 -- presentation-only convenience over the
            // four existing authoritative fields; stores nothing new.
            quickAction: {
              label: "Mark Oriented x4",
              setPaths: ["orientation.time", "orientation.place", "orientation.person", "orientation.situation"],
              clearPaths: ["orientation.disoriented"],
            },
          },
        ],
      },
      {
        // Section 10 -- Neurological uses its own more granular option set
        // (NEURO_OVERALL_CHANGE_OPTIONS, not the shared CLINICAL_STATUS_
        // CHANGE_OPTIONS other paused systems reuse) and sits directly
        // beside Consciousness/Orientation as the third card of the
        // "status row" -- hospice is about progression, and this is the
        // fastest way to answer "is this patient declining?" without
        // scrolling. Same `clinicalStatusChange` path as before; only the
        // option list and title changed.
        title: "Overall Change Since Prior Assessment", category: "core", importance: "high", fields: [
          { type: "segmented", label: "Overall Change", path: "clinicalStatusChange", options: NEURO_OVERALL_CHANGE_OPTIONS },
        ],
      },
      {
        // One of the strongest hospice decline indicators (Finding #1/#6)
        // -- kept as its own major, high-importance section. `fullWidth`
        // (Section 11/21) gives it the entire workspace row instead of
        // being squeezed into one of 3 equal columns alongside the much
        // shorter Consciousness/Orientation/Overall Change cards, which
        // was the reported "uneven, abnormally tall column" defect.
        title: "Sleep / Responsiveness", category: "core", importance: "high", fullWidth: true, fields: [
          { type: "segmented", label: "Sleep Pattern", path: "sleepRest.sleepPattern", options: [{ value: "Normal", label: "Usual / No Significant Concern" }, "Increased Sleeping", "Excessive Sleeping", "Fragmented Sleep", "Insomnia", "Unable to assess"] },
          { type: "segmented", label: "Responsiveness", path: "sleepRest.responsiveness", options: ["Easily Aroused", { value: "Somnolent", label: "Somnolence" }, "Difficult To Arouse", "Minimally Responsive", "Unresponsive", "Unable to assess"] },
          { type: "segmented", label: "Change Since Prior Visit", path: "sleepRest.changeSincePrior", options: ["No Change", "Sleeping More", "Increased Somnolence", "More Difficult To Arouse", "New Unresponsiveness"] },
          // GitHub Directive (2026-09-28) "Neurological Review -- Major
          // Success, But We Are Drifting..." Major Concern #5 -- reframed
          // as a direct clinical question ("Can sleep be estimated?")
          // rather than a meta-question about whether a trend is known;
          // same path/options, label only, so no data is affected.
          { type: "segmented", label: "Can Sleep Be Estimated?", path: "sleepRest.sleepTrendKnown", options: ["Yes", "No", "Unable to Determine"] },
          { type: "input", label: "Average Sleep Hours / 24 Hours", path: "sleepRest.averageSleepHours", inputType: "number" },
          { type: "pillGroup", label: "Nighttime Symptoms", path: "sleepRest.nighttimeSymptoms", options: ["Pain", "Dyspnea", "Restlessness", "Confusion", "Anxiety", "Nausea", "None"] },
          // Section 17 rename: "Interventions" reframed as comfort measures
          // (hospice language) -- same path/values, label only.
          { type: "pillGroup", label: "Sleep Aids / Current Comfort Measures", path: "sleepRest.sleepAids", options: ["Medication", "Positioning", "White noise", "Warm milk/tea", "Other"] },
          // Section 18 -- replaced the free-text "Response to Interventions"
          // with a constrained single-select so it can actually be scanned
          // at a glance. Added as a NEW field/path rather than repurposing
          // the old free-text one, so no historical narrative answer is
          // silently reinterpreted as one of these 4 fixed values (Section
          // 40 guardrail); the old field is kept, demoted to an optional
          // comment for any nurse who needs to add nuance.
          { type: "segmented", label: "Current Effect on Comfort or Rest", path: "sleepRest.effectOnComfort", options: ["Helpful", "Partially Helpful", "Not Helpful", "Unable to Determine"] },
          { type: "input", label: "Additional Comment (if needed)", path: "sleepRest.response" },
          { type: "segmented", label: "Restfulness", path: "sleepRest.restfulness", options: ["Adequate", "Inadequate", "Unable to Determine"] },
          { type: "textarea", label: "Sleep Notes", path: "sleepRest.notes", rows: 2 },
        ],
      },
      {
        // Section 5/8/16 -- Communication merged with Hearing/Vision/
        // Sensory Deficits/Sensory Aids into one "Communication and
        // Sensory" full-width card so related sensory-input concepts read
        // together instead of being scattered as separate same-height
        // boxes. Category stays "symptoms" so it renders in the required
        // bucket position (after Sleep/Responsiveness, before Cognitive/
        // Behavioral Findings).
        title: "Communication and Sensory", category: "symptoms", importance: "medium", fullWidth: true, fields: [
          // Finding #5: progressive disclosure -- Normal/Impaired first,
          // detail (Aphasia/Slurred speech/Unable/Other) revealed only when
          // Impaired. Same field/path/values as before; no data migrated.
          // Issue #5 (2026-09-28 follow-up review): explicit fieldSpan so
          // Communication/Hearing/Vision pack onto one tighter row instead
          // of each claiming more grid width than their short controls need.
          {
            type: "gatedRadio", label: "Communication", path: "communication", fieldSpan: 2,
            primaryOptions: [{ value: "Normal", label: "No Current Communication Concern" }, "Impaired"],
            normalValues: ["Normal", "Clear"],
            detailOptions: ["Unable", "Aphasia", "Slurred speech", "Speech limited to six or fewer intelligible words", "Other"],
          },
          // Section 16 -- "Hearing aid"/"Corrective lenses" removed as
          // duplicate concepts (they belong under Sensory Aids, not as a
          // hearing/vision *status*); "Unable to assess" added. Any
          // patient with these exact legacy stored values still sees them
          // via FormSegmented's new "Previously recorded" review chip --
          // the value itself is never deleted or rewritten.
          { type: "segmented", label: "Hearing", path: "hearing", fieldSpan: 2, options: ["Adequate", "Impaired", "Deaf", "Unable to assess"] },
          { type: "segmented", label: "Vision", path: "vision", fieldSpan: 2, options: ["Adequate", "Impaired", "Blind", "Unable to assess"] },
          { type: "pillGroup", label: "Sensory Deficits", path: "sensoryDeficits", fieldSpan: 3, options: ["Numbness", "Tingling", "Decreased sensation", "Phantom pain"] },
          // Section 16 -- clarified labels (display only, via {value,label}
          // so stored values "Glasses"/"Hearing aids" are unchanged) since
          // this is now the one place hearing/vision aids are documented.
          { type: "pillGroup", label: "Sensory Aids", path: "sensoryAids", fieldSpan: 3, options: [{ value: "Glasses", label: "Glasses / Corrective Lenses" }, { value: "Hearing aids", label: "Hearing Aid" }, "Other"] },
        ],
      },
      {
        // Issue #6 (2026-09-28 follow-up review) -- explicit fullWidth so
        // the Symptoms/Demeanor pill row always has the entire workspace
        // width to wrap into a dense multi-per-line chip layout instead of
        // stacking narrowly, regardless of what else is in this category
        // bucket.
        title: "Cognitive / Behavioral Findings", category: "symptoms", importance: "medium", fullWidth: true, fields: [
          // GitHub Directive (2026-09-28) "Neurological Overview Gate" --
          // fast-path replacement for the full detail below. New path;
          // only rendered/relevant when Neurological Overview = "No
          // Current Neurological Concern" (see the render-loop guard).
          // Selecting "Findings Present" reveals the existing detail
          // fields unchanged; nothing here rewrites their values.
          { type: "segmented", label: "Behavioral Status", path: "behavioralStatus", options: ["No Current Concern", "Findings Present", "Unable to Assess"] },
          // Relocated from Consciousness (Section 8); renamed (Issue #4) --
          // this is a narrative clarification field, not a duplicate of
          // Consciousness/Orientation/BIMS/Cognitive-Behavioral findings
          // (confirmed: its only other consumer is the read-only
          // Structured Findings generator at path `cognition`), so it's
          // now a small textarea instead of a wide single-line input.
          { type: "textarea", label: "Additional Cognitive Observations", path: "cognition", rows: 2 },
          { type: "pillGroup", label: "Symptoms / Demeanor", path: "symptomsDemeanor", fieldSpan: "full", options: ["Anxiety", "Agitation", "Peaceful", "Confused", "Angry", "Restless", "Depressed", "Seizure", "Combative", "Sundowning", "Tremors / twitching", "Other"] },
          // GitHub UI Directive (2026-09-28): single yes/no findings use a
          // compact toggle pill, not a large square checkbox. Same path/
          // boolean value -- no data migration.
          { type: "booleanPill", label: "Delirium", path: "delirium" },
          { type: "booleanPill", label: "Seizure History", path: "seizureHistory" },
        ],
      },
      {
        title: "Motor / Balance", category: "functional", importance: "medium", fields: [
          // GitHub Directive (2026-09-28) "Neurological Overview Gate" --
          // same fast-path pattern as Behavioral Status above. New path;
          // gated the same way.
          { type: "segmented", label: "Motor/Balance Status", path: "motorBalanceStatus", options: ["No New Concern", "Findings Present", "Patient Does Not Ambulate", "Unable to Assess"] },
          // Issue #7 (2026-09-28 follow-up review) -- "Motor Deficit
          // Present" was only a positive-state toggle with no way to
          // record "assessed, none identified" vs. "never assessed" as
          // different facts. Motor Status is a true 3-state primary
          // control on a NEW path (`motorStatus`); its onChange also
          // writes the legacy `motorDeficit` boolean (true only for
          // "Present") so every existing consumer of that boolean
          // (Structured Findings, the narrative Summary) keeps working
          // unchanged. A record that only ever has the legacy boolean set
          // still displays correctly here (falls back to "Present" when
          // motorDeficit is true and motorStatus was never touched).
          { type: "segmented", label: "Motor Status", path: "motorStatus", options: ["None Identified", "Present", "Unable to Assess"] },
          { type: "segmented", label: "Affected Side", path: "affectedSide", options: ["Left", "Right", "Bilateral"] },
          { type: "pillGroup", label: "Deficit Type", path: "deficitType", options: ["Hemiparesis", "Hemiplegia", "Paraparesis", "Quadriparesis", "Other"] },
          // Finding #8: "Normal"/"Impaired" removed as duplicate/overlapping
          // concepts -- Steady/Unsteady/Unable to stand already cover them.
          // Section 27 adds the one remaining legitimate missing state: a
          // non-ambulatory patient for whom "balance" doesn't apply at all.
          { type: "segmented", label: "Balance", path: "balance", options: ["Steady", "Unsteady", "Unable to stand", "Unable to assess", "Not Assessed — Patient Does Not Ambulate"] },
        ],
      },
      {
        // Finding #9: historical diagnoses shouldn't compete with active
        // findings -- collapsed by default, same fields/paths/values. (A
        // prior version of the Card component had a bug where this
        // `collapsedByDefault` had no effect at all while Body Systems'
        // pilot rendering was active -- fixed alongside this change.)
        // Category "functional" (not "symptoms") so this renders directly
        // after Motor / Balance within that bucket, matching the required
        // 10-group order.
        title: "Psychiatric History", category: "functional", importance: "low", collapsedByDefault: true, fields: [
          { type: "pillGroup", label: "Psychiatric History", path: "psychiatricHistoryType", options: ["None", "Bipolar disorder", "OCD", "Schizophrenia", "Depression", "Other"] },
          { type: "textarea", label: "Psychiatric History Notes", path: "psychiatricHistory", rows: 2 },
        ],
      },
      {
        // BIMS is the CMS-standard cognitive-impairment screen; kept as the
        // one "HOPE Cognitive Assessment" card so staging (FAST, under
        // Performance Status) is not duplicated as a second source of
        // truth here. Finding #10: visually separated, structure untouched.
        title: "HOPE Cognitive Assessment (BIMS Screen)", category: "disease", importance: "medium", hopeCode: "N0500-N0520", fields: [
          // Issue #9 (2026-09-28 follow-up review) -- explicit equal
          // fieldSpan so the three BIMS selects align into one even row
          // instead of drifting to uneven widths based on option-label
          // length heuristics.
          { type: "select", label: "N0500 — Repetition", path: "hopeItems.n0500", hopeCode: "N0500", fieldSpan: 2, options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — One word" }, { value: "2", label: "2 — Two words" }, { value: "3", label: "3 — Three words" }] },
          { type: "select", label: "N0510 — Recall", path: "hopeItems.n0510", hopeCode: "N0510", fieldSpan: 2, options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — One" }, { value: "2", label: "2 — Two" }, { value: "3", label: "3 — Three" }] },
          { type: "select", label: "N0520 — Temporal Orientation", path: "hopeItems.n0520", hopeCode: "N0520", fieldSpan: 2, options: [{ value: "0", label: "0 — None correct" }, { value: "1", label: "1 — Year correct" }, { value: "2", label: "2 — Month correct" }, { value: "3", label: "3 — Day of week correct" }] },
        ],
      },
      {
        title: "Notes", category: "observation", importance: "low", fields: [
          // Section 20/30 -- reduced textarea footprint (4 rows -> 2).
          { type: "textarea", label: "Neurological Notes", path: "notes", rows: 2 },
        ],
      },
    ],
  },

  cardiovascular: {
    title: "Cardiovascular",
    subtitle: "Blood pressure, pulse, edema, chest pain, circulation",
    cards: [
      {
        // OWNER-APPROVED "Cardiovascular Overview Gate" (2026-09-28) --
        // same triage pattern as Neurological's Overview Gate: this
        // up-front question determines which detail cards render below
        // (see the card/field-level guards in the render loop). New path
        // (`cardiovascularOverview`) -- no existing field/value touched.
        title: "Cardiovascular Overview", category: "core", importance: "high", fullWidth: true, fields: [
          {
            // OWNER CORRECTION (2026-09-28 Contradiction 2/3) -- renamed
            // from "...Findings Stable" to "...Findings Review": the app
            // has no verified prior-assessment/comparison infrastructure,
            // so this path must not itself claim stability. Stability is
            // only ever asserted via an explicit current Clinical Status
            // Change = "Stable / No Change" selection (see
            // computeCardiovascularNarrative).
            // Owner directive (2026-09-28) "Correct the Overview Label" --
            // exact approved wording is "New or Worsening Cardiovascular
            // Findings". A record already saved with the old slash-joined
            // "New/Worsening Cardiovascular Findings" is never rewritten;
            // `aliases` makes that legacy stored value render selected
            // under the new label instead of appearing unselected, and
            // every business-logic comparison goes through
            // normalizeCardiovascularOverview() so both spellings behave
            // identically.
            type: "segmented", label: "Cardiovascular Overview", path: "cardiovascularOverview",
            options: [
              "No Current Cardiovascular Concern",
              "Existing Cardiovascular Findings Review",
              "New or Worsening Cardiovascular Findings",
              "Unable to Assess",
            ],
            aliases: { "New/Worsening Cardiovascular Findings": "New or Worsening Cardiovascular Findings" },
          },
          {
            type: "segmented", label: "Reason Unable to Assess", path: "cardiovascularUnableToAssessReason",
            options: ["Patient unable to participate", "Patient unresponsive", "Clinical condition prevented completion", "Assessment interrupted", "Patient or representative declined", "Other"],
          },
          { type: "input", label: "Other Reason (if selected above)", path: "cardiovascularUnableToAssessOther" },
        ],
      },
      { title: "Circulation & Perfusion", category: "core", fields: [
        { type: "pillGroup", label: "Pulse Sites", path: "pulseSites", options: ["Apical", "Pedal", "Radial", "Femoral"] },
        // OWNER-APPROVED "Pulse Redesign" (2026-09-28) -- Rhythm/Rate/
        // Strength are three independent clinical concepts (previously
        // one combined "Pulse Quality" radio, the Cardiovascular
        // equivalent of Neurological's "Awake / Alert" problem) and must
        // be independently selectable (e.g. Irregular + Bradycardic +
        // Weak all at once). The legacy `pulseQuality` field is never
        // rewritten; PULSE_LEGACY_DIMENSION aliases it for display into
        // whichever of these three fields is still blank.
        { type: "segmented", label: "Pulse Rhythm", path: "pulseRhythm", options: ["Regular", "Irregular", "Unable to assess"] },
        { type: "segmented", label: "Pulse Rate", path: "pulseRate", options: ["Normal", "Tachycardic", "Bradycardic", "Unable to assess"] },
        { type: "segmented", label: "Pulse Strength", path: "pulseStrength", options: ["Strong", "Weak", "Thready", "Bounding", "Absent", "Unable to assess"] },
        { type: "input", label: "Peripheral Circulation", path: "peripheralCirculation" },
        { type: "input", label: "Heart Sounds", path: "heartSounds" },
        { type: "segmentedTriState", label: "JVD (Jugular Venous Distention)", path: "jvd" },
        { type: "input", label: "Skin Color", path: "skinColor" },
        { type: "booleanPill", label: "Cool Extremities", path: "coolExtremities" },
        { type: "booleanPill", label: "Varicose Veins", path: "varicoseVeins" },
        { type: "booleanPill", label: "Stasis Ulcer", path: "stasisUlcer" },
        { type: "segmentedTriState", label: "Edema Present", path: "edema.present" },
        { type: "pillGroup", label: "Edema Location", path: "edema.location", options: ["Bilateral lower extremities", "Unilateral LE", "Sacral", "Periorbital", "Upper extremities", "Generalized"] },
        { type: "segmented", label: "Edema Severity", path: "edema.severity", options: ["Trace", "1+", "2+", "3+", "4+"] },
      ]},
      // Owner directive (2026-09-27): Cardiovascular must stay symptom- and
      // function-focused, not a disease-specific cardiology workup.
      // Chest pain, edema/perfusion (Circulation & Perfusion card above), BP
      // abnormalities, fatigue, dizziness, syncope, and cardiac-related
      // dyspnea are the prioritized findings a hospice RN documents here.
      { title: "Cardiovascular Symptoms", category: "symptoms", fields: [
        { type: "segmentedTriState", label: "Chest Pain Present", path: "chestPain.present" },
        { type: "input", label: "Chest Pain Type", path: "chestPain.type" },
        // OWNER CORRECTION (2026-09-28 Contradiction 4) -- "Orthostatic"
        // is not the same dimension as Normal/Hypertensive/Hypotensive
        // (a patient can be Hypotensive AND have an Orthostatic finding
        // at the same time), so this is two independent single-select
        // controls, not one merged control. Legacy `bpSymptoms`
        // multi-select array is never rewritten; resolveBpLegacyDisplay
        // aliases it for display only when unambiguous (a contradictory
        // legacy array is surfaced as a review-required note instead of
        // being silently collapsed to one value -- see
        // computeCardiovascularNarrative).
        { type: "segmented", label: "BP Status", path: "bpStatus", options: ["Normal", "Hypertensive", "Hypotensive", "Unable to assess"] },
        { type: "segmented", label: "Orthostatic Finding", path: "orthostaticFinding", options: ["Not Present", "Present", "Unable to assess"] },
        { type: "segmented", label: "Fatigue", path: "fatigue", options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "segmented", label: "Dizziness", path: "dizziness", options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "segmentedTriState", label: "Syncope (Fainting Episodes)", path: "syncope" },
        // OWNER-DIRECTED "Dyspnea Ownership Model" (2026-09-28,
        // Contradiction 5) -- Respiratory owns the symptom (sobSeverity);
        // Cardiovascular owns only the cardiac-cause attribution of an
        // already-documented dyspnea. The `cardiacDyspnea` checkbox and
        // this guidance note are mutually exclusive at render time (see
        // resolveCardiacDyspneaGate + the render-loop guard below):
        // Respiratory positive -> show checkbox; Respiratory blank ->
        // show only this note; Respiratory negative -> show neither
        // (unless a legacy value already exists, which is always
        // preserved and never auto-hidden).
        { type: "checkbox", label: "Dyspnea Attributed to Cardiac Condition", path: "cardiacDyspnea" },
        { type: "note", label: "Document dyspnea in Respiratory before assigning cardiac attribution.", path: "cardiacDyspneaGuidanceNote" },
        // Owner directive (2026-09-28) "Cardiovascular Symptom-Focused
        // Scope Correction" -- Heart Failure is a diagnosis/disease
        // process, not a current sign/symptom/assessment finding, so it
        // is no longer an editable current-entry control anywhere in
        // Cardiovascular (Path 1/3/4 hide these two fields entirely --
        // see the render-loop guard below). `heartFailurePresent`/
        // `heartFailureType` are preserved untouched (never deleted,
        // nulled, or rewritten) and surface only as read-only, clearly
        // labeled "previously stored" information on Path 2 ("Existing
        // Cardiovascular Findings Review"), and only when a value is
        // already documented on the record (the existing Path 2 "only
        // show already-documented findings" rule -- not a new mechanism).
        // The diagnosis itself belongs to the HOPE I0600 comorbidity
        // workflow (auto-derived from coded Diagnosis, see hopeComorbidities
        // above) and to Diagnosis/Certification/LCD -- not to this
        // symptom-focused body-system assessment.
        {
          type: "legacyReadOnly", label: "Previously Stored Cardiovascular Condition Information", path: "heartFailurePresent",
          legacyFormat: (v) => (v === true ? "Heart failure documented." : "Not documented."),
        },
        {
          type: "legacyReadOnly", label: "Historical Heart Failure Type", path: "heartFailureType",
          legacyFormat: (v) => (Array.isArray(v) && v.length > 0 ? v.map((t) => `Historical Heart Failure type: ${t}.`).join(" ") : "Not documented."),
        },
      ]},
      { title: "Cardiac Devices", category: "treatments", fields: [
        { type: "booleanPill", label: "Pacemaker", path: "pacemaker" },
        { type: "booleanPill", label: "Internal Defibrillator", path: "internalDefibrillator" },
        { type: "booleanPill", label: "Central Venous Line", path: "centralVenousLine" },
      ]},
      { title: "Clinical Status Change", category: "response", fields: [
        // Directive (2026-09-28) Section 13 -- Path 2 clinician
        // confirmation, kept adjacent to the stored findings/Clinical
        // Status Change/Notes it applies to (hidden on every other path
        // via the render-loop guard below).
        { type: "booleanPill", label: "Findings Reviewed and Confirmed This Visit", path: "cardiovascularFindingsConfirmedThisVisit" },
        { type: "segmented", label: "Clinical Status Change", path: "clinicalStatusChange", options: CARDIOVASCULAR_CLINICAL_STATUS_CHANGE_OPTIONS },
      ]},
      { title: "Cardiovascular Notes", category: "observation", fields: [
        { type: "textarea", label: "Cardiovascular Notes", path: "notes" },
      ]},
    ],
  },

  respiratory: {
    title: "Respiratory",
    subtitle: "SOB (J2051B), lung sounds, oxygen therapy, cough assessment",
    cards: [
      { title: "Respiratory Assessment", category: "core", fields: [
        { type: "radio", label: "SOB Severity", path: "sobSeverity", sfv: true, options: ["None", "Mild", "Moderate", "Severe", "At rest"] },
        { type: "checkbox", label: "Treatment Declined (when applicable)", path: "treatmentDeclined" },
        { type: "radio", label: "Exertion Level", path: "exertionLevel", options: ["At rest", "Minimal exertion", "Moderate exertion", "Severe exertion", "With speech", "Push of speech", "Pursed-lip breathing", "Other"] },
        { type: "checkbox", label: "Screened for shortness of breath", path: "shortnessOfBreathScreened" },
        { type: "input", label: "SOB screening date", path: "screeningDate", inputType: "date" },
        { type: "checkbox", label: "Treatment for shortness of breath initiated", path: "treatmentInitiated" },
        { type: "input", label: "SOB treatment date", path: "treatmentDate", inputType: "date" },
        { type: "checkboxGroup", label: "Lung Sounds", path: "lungSounds", options: ["Clear", "Crackles", "Wheezes", "Rhonchi", "Diminished", "Absent", "Stridor", "Pleural rub", "Rales"] },
        { type: "checkboxGroup", label: "Respiration Pattern", path: "respirations", options: ["Regular", "Normal", "Irregular", "Labored", "Cheyne-Stokes", "Apneic episodes", "Kussmaul", "Agonal", "Tachypnea", "Bradypnea", "Orthopnea"] },
        { type: "select", label: "Cough Type", path: "coughType", options: ["None", "Productive", "Non-productive", "Hemoptysis", "Barrel chest"] },
        { type: "input", label: "Sputum Character", path: "sputumCharacter" },
      ]},
      { title: "Oxygen Therapy", category: "treatments", fields: [
        { type: "checkbox", label: "Oxygen in Use", path: "oxygenTherapy.inUse" },
        { type: "select", label: "Delivery Type", path: "oxygenTherapy.type", options: ["Nasal cannula", "Simple mask", "Non-rebreather", "Venturi mask", "High flow"] },
        { type: "input", label: "Liters/Minute", path: "oxygenTherapy.litersPerMinute", inputType: "number" },
        { type: "input", label: "Hours/Day", path: "oxygenTherapy.hoursPerDay" },
        { type: "radio", label: "Delivery Mode", path: "oxygenTherapy.deliveryMode", options: ["Continuous", "PRN"] },
        { type: "checkbox", label: "On Room Air", path: "oxygenTherapy.onRoomAir" },
        { type: "input", label: "SpO2 on O2", path: "oxygenTherapy.satOnO2", inputType: "number" },
      ]},
      { title: "Ventilator / Airway Support", category: "treatments", fields: [
        { type: "checkbox", label: "Short-Term Ventilator", path: "ventilator.shortTermVentilator" },
        { type: "checkbox", label: "Long-Term Ventilator", path: "ventilator.longTermVentilator" },
        { type: "input", label: "Ventilator Type and Settings", path: "ventilator.ventilatorTypeAndSettings" },
        { type: "input", label: "Tracheostomy Type", path: "ventilator.tracheostomyType" },
        { type: "input", label: "Tracheostomy Size", path: "ventilator.tracheostomySize" },
      ]},
      { title: "Clinical Status Change", category: "response", fields: [
        { type: "radio", label: "Clinical Status Change", path: "clinicalStatusChange", options: CLINICAL_STATUS_CHANGE_OPTIONS },
      ]},
      { title: "Notes", category: "observation", fields: [
        { type: "textarea", label: "Respiratory Notes", path: "notes" },
      ]},
    ],
  },

  infection: {
    title: "Immunological / Infection",
    subtitle: "Allergies, current infections, resistant-organism history, precautions",
    cards: [
      { title: "Allergies", category: "core", customRenderer: "patientAllergies", fields: [] },
      { title: "Immune Status", category: "core", fields: [
        { type: "checkbox", label: "Immunosuppressed", path: "immunosuppressed" },
        { type: "checkboxGroup", label: "Precautions", path: "precautions", options: ["Standard", "Contact", "Droplet", "Airborne"] },
      ]},
      { title: "Infection Assessment", category: "disease", fields: [
        { type: "checkboxGroup", label: "Antibiotic-Resistant Infection (current)", path: "antibioticResistantInfection", options: ["None", "MRSA", "C. difficile", "Other"] },
        { type: "checkboxGroup", label: "History of Resistant Infection", path: "historyOfResistantInfections", options: ["None", "MRSA", "C. difficile", "Other"] },
        { type: "checkboxGroup", label: "Current Active Infection", path: "currentInfections", options: ["None", "Sepsis", "UTI", "Respiratory tract", "IV site", "Wound", "HIV-related", "Pressure area", "Other"] },
      ]},
      { title: "Infection Symptoms", category: "symptoms", fields: [
        { type: "input", label: "Temperature", path: "temperature", inputType: "number", placeholder: "°F" },
        { type: "checkbox", label: "Recurrent Infection", path: "recurrentInfection" },
        { type: "textarea", label: "Infection History", path: "infectionHistory" },
      ]},
      { title: "Antibiotic Treatment", category: "treatments", fields: [
        { type: "checkbox", label: "Antibiotic Use", path: "antibioticUse" },
      ]},
      { title: "Clinical Status Change", category: "response", fields: [
        { type: "radio", label: "Clinical Status Change", path: "clinicalStatusChange", options: CLINICAL_STATUS_CHANGE_OPTIONS },
      ]},
      { title: "Notes", category: "observation", fields: [
        { type: "textarea", label: "Other Observations / Notes", path: "notes", placeholder: "List active infections..." },
      ]},
    ],
  },

  gastrointestinal: {
    title: "Gastrointestinal",
    subtitle: "J2051D-G (Nausea, Vomiting, Diarrhea, Constipation), bowel, feeding devices",
    cards: [
      { title: "Constipation — Auto-Suggested from Last BM Date", category: "core", customRenderer: "constipationAutoAssess" },
      { title: "GI Symptoms", category: "symptoms", fields: [
        { type: "radio", label: "Nausea", path: "nausea", sfv: true, options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "radio", label: "Vomiting", path: "vomiting", sfv: true, options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "input", label: "Vomiting Occurrences (24 hours)", path: "vomitingOccurrences24h", inputType: "number" },
        { type: "radio", label: "Diarrhea", path: "diarrhea", sfv: true, options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "radio", label: "Constipation", path: "constipation", sfv: true, options: ["None", "Mild", "Moderate", "Severe"] },
      ]},
      { title: "Abdominal / Bowel Assessment", category: "core", fields: [
        { type: "radio", label: "Bowel Sounds", path: "bowelSounds", options: ["Normal", "Hyperactive", "Hypoactive", "Absent"] },
        { type: "radio", label: "Abdomen", path: "abdomen", options: ["Soft", "Firm", "Tympanic", "Distended", "Tender", "Nontender", "Rigid"] },
        { type: "checkbox", label: "Ascites", path: "ascites" },
        { type: "input", label: "Abdominal Girth", path: "abdominalGirth" },
        { type: "checkboxGroup", label: "Stool", path: "stoolCharacter", options: ["Normal", "Bloody", "Colostomy", "Ileostomy"] },
        { type: "radio", label: "Bowel Status", path: "bowelStatus", options: ["Regular", "Irregular", "Impaction", "Continent", "Incontinent", "Bowel/bladder program"] },
        { type: "input", label: "Bowel Frequency", path: "bowelFrequency" },
        { type: "input", label: "Last BM Date", path: "lastBM", inputType: "date" },
        { type: "textarea", label: "Reason Bowel Regimen Could Not Be Initiated", path: "reasonBowelRegimenNotInitiated" },
      ]},
      { title: "Feeding Devices", category: "treatments", fields: [
        { type: "checkbox", label: "Feeding Tube Present", path: "feedingTube.present" },
        { type: "select", label: "Tube Type", path: "feedingTube.type", options: ["NG", "PEG", "PEJ", "G-tube", "J-tube"] },
        { type: "checkbox", label: "Ostomy Present", path: "ostomy.present" },
        { type: "select", label: "Ostomy Type", path: "ostomy.type", options: ["Colostomy", "Ileostomy", "Urostomy"] },
      ]},
      { title: "Clinical Status Change", category: "response", fields: [
        { type: "radio", label: "Clinical Status Change", path: "clinicalStatusChange", options: CLINICAL_STATUS_CHANGE_OPTIONS },
      ]},
      { title: "Notes", category: "observation", fields: [
        { type: "textarea", label: "GI Notes", path: "notes" },
      ]},
    ],
  },

  nutrition: {
    title: "Nutrition",
    subtitle: "Weight loss, appetite, swallowing, hydration, diet",
    cards: [
      {
        title: "Anthropometric & Metabolic Reference",
        category: "core",
        customRenderer: "nutritionAnthropometricReference",
      },
      {
        title: "Weight Loss Auto-Calculation",
        category: "core",
        customRenderer: "weightLossAutoCalc",
      },
      { title: "Nutritional Assessment", category: "core", fields: [
        { type: "input", label: "Weight Loss (past 6 months)", path: "weightLossPastSixMonths", placeholder: "lbs or %" },
        { type: "radio", label: "Appetite", path: "appetite", options: ["Good", "Fair", "Poor", "Anorexic"] },
        { type: "input", label: "Diet Type", path: "dietType" },
        { type: "radio", label: "Fluid Intake", path: "fluidIntake", options: ["Adequate", "Decreased", "Minimal"] },
      ]},
      { title: "Nutrition Symptoms", category: "symptoms", fields: [
        { type: "checkboxGroup", label: "Swallowing Issues", path: "swallowingIssues", options: ["Dysphagia", "Aspiration risk", "Pocketing", "Coughing with swallowing", "None"] },
        { type: "input", label: "Oral Mucosa", path: "oralMucosa" },
        { type: "checkbox", label: "Upper Dentures", path: "dentures.upper" },
        { type: "checkbox", label: "Lower Dentures", path: "dentures.lower" },
      ]},
      { title: "Nutrition Support", category: "treatments", fields: [
        { type: "input", label: "Nutritional Supplements", path: "nutritionalSupplements" },
      ]},
      { title: "NPO / Artificial Feeding", category: "treatments", fields: [
        { type: "radio", label: "NPO Status", path: "npoStatus", options: ["Not NPO", "NPO", "NPO except meds", "Modified/thickened liquids only"] },
        { type: "checkboxGroup", label: "Artificial Feeding / Access Devices", path: "artificialFeeding", options: ["PEG", "NG", "J-tube", "Pump", "TPN", "None"] },
      ]},
      { title: "Oral Cavity", category: "core", fields: [
        { type: "checkboxGroup", label: "Oral Cavity Findings", path: "oralCavityFindings", options: ["Edentulous", "Stomatitis", "Thrush", "Poor dentition", "Normal"] },
      ]},
      { title: "Clinical Status Change", category: "response", fields: [
        { type: "radio", label: "Clinical Status Change", path: "clinicalStatusChange", options: CLINICAL_STATUS_CHANGE_OPTIONS },
      ]},
      { title: "Nutrition Notes", category: "observation", fields: [
        { type: "textarea", label: "Nutrition Notes", path: "notes" },
      ]},
    ],
  },
  endocrine: {
    title: "Endocrine",
    subtitle: "Impairment, thyroid, diabetes management, endocrine symptoms",
    cards: [
      { title: "Endocrine Impairment", category: "core", fields: [
        { type: "checkboxGroup", label: "Impairment", path: "endocrineImpairment", options: ["Thyroid", "Parathyroid", "Pituitary", "Adrenal", "Pancreas", "None"] },
      ]},
      { title: "Thyroid Assessment", category: "core", fields: [
        { type: "radio", label: "Thyroid", path: "thyroid.assessment", options: ["Normal", "Enlarged", "Tender", "Nodular", "Not assessed"] },
        { type: "textarea", label: "Thyroid Notes", path: "thyroid.notes" },
      ]},
      { title: "Diabetes Management", category: "disease", fields: [
        { type: "radio", label: "Diabetes Type", path: "diabetes.type", options: ["Type 1", "Type 2", "Not diabetic", "Unknown"] },
        { type: "radio", label: "Diabetes Dependency", path: "diabetes.dependency", options: ["Insulin-dependent", "Non-insulin-dependent", "Glucose-management concern", "Not applicable"] },
        { type: "select", label: "Glucose Monitoring Frequency", path: "diabetes.glucoseMonitoring", options: ["None", "Daily", "BID", "TID", "QID", "Weekly"] },
        { type: "input", label: "Last HbA1c Value", path: "diabetes.lastHbA1c" },
        { type: "input", label: "Last HbA1c Date", path: "diabetes.lastHbA1cDate", inputType: "date" },
        { type: "input", label: "Insulin Type", path: "diabetes.insulinType" },
        { type: "input", label: "Insulin Dose", path: "diabetes.insulinDose" },
        { type: "checkboxGroup", label: "Oral Hypoglycemics", path: "diabetes.oralHypoglycemics", options: ["Metformin", "Sulfonylurea", "DPP-4 inhibitor", "SGLT2 inhibitor", "None"] },
      ]},
      { title: "Endocrine Symptoms", category: "symptoms", fields: [
        { type: "checkboxGroup", label: "Symptoms Present", path: "endocrineSymptoms", options: ["Fatigue", "Weight changes", "Temperature intolerance", "Hair/skin changes", "Polydipsia", "Polyuria", "Tremors"] },
      ]},
      { title: "Endocrine Treatment", category: "treatments", fields: [
        { type: "checkboxGroup", label: "Current Treatment", path: "currentEndocrineMeds", options: ["Levothyroxine", "Insulin", "Oral hypoglycemics", "Corticosteroid replacement", "Other endocrine medication", "None"] },
      ]},
      { title: "Clinical Status Change", category: "response", fields: [
        { type: "radio", label: "Clinical Status Change", path: "clinicalStatusChange", options: CLINICAL_STATUS_CHANGE_OPTIONS },
      ]},
      { title: "Notes", category: "observation", fields: [
        { type: "textarea", label: "Other Observations / Notes", path: "notes" },
      ]},
    ],
  },

  genitourinary: {
    title: "Genitourinary / Reproductive",
    subtitle: "Urinary status, catheter, urine output, reproductive concerns",
    cards: [
      { title: "Urinary Status", category: "core", fields: [
        { type: "radio", label: "Continence", path: "urinaryStatus", options: ["Continent", "Stress incontinence", "Urge incontinence", "Functional incontinence", "Total incontinence", "Catheterized", "Bladder program", "Urostomy", "Retention", "Painful urination", "Nocturia"] },
        { type: "input", label: "Frequency", path: "frequency" },
        { type: "checkboxGroup", label: "Urine", path: "urineCharacteristics", options: ["Clear", "Cloudy", "Pale", "Blood", "Odor"] },
        { type: "input", label: "Urine Color", path: "urineColor" },
      ]},
      { title: "Catheter Assessment", category: "treatments", fields: [
        { type: "checkbox", label: "Catheter Present", path: "catheter.present" },
        { type: "select", label: "Type", path: "catheter.type", options: ["None", "Foley", "Suprapubic", "Condom", "Intermittent", "Urostomy"] },
        { type: "input", label: "Size", path: "catheter.size" },
        { type: "input", label: "Insertion Date", path: "catheter.insertionDate", inputType: "date" },
        { type: "input", label: "Last Change Date", path: "catheter.lastChangeDate", inputType: "date" },
        { type: "radio", label: "Condition", path: "catheter.condition", options: ["Patent", "Blocked", "Leaking"] },
        { type: "checkboxGroup", label: "Urine Characteristics (Catheter)", path: "catheter.urineCharacteristics", options: ["Clear", "Cloudy", "Amber", "Dark", "Hematuria", "Sediment", "Foul odor"] },
        { type: "input", label: "Irrigation Solution", path: "catheter.irrigation.solution" },
        { type: "input", label: "Irrigation Frequency", path: "catheter.irrigation.frequency" },
        { type: "input", label: "Irrigation Duration", path: "catheter.irrigation.duration" },
        { type: "textarea", label: "Catheter Care", path: "catheterCare" },
      ]},
      { title: "Urine Output", category: "core", fields: [
        { type: "radio", label: "Output", path: "urineOutput", options: ["Adequate", "Decreased", "Anuria", "Polyuria"] },
        { type: "input", label: "24-Hour Volume (if measured)", path: "twentyFourHourVolume", inputType: "number" },
      ]},
      { title: "Reproductive Concerns", category: "symptoms", fields: [
        { type: "checkboxGroup", label: "Concerns", path: "reproductive.concerns", options: ["Vaginal bleeding", "Vaginal discharge", "Penile discharge", "Scrotal edema", "Testicular mass"] },
        { type: "textarea", label: "Reproductive Notes", path: "reproductive.notes" },
      ]},
      { title: "Bladder Management", category: "treatments", fields: [
        { type: "checkboxGroup", label: "Interventions", path: "bladderManagement", options: ["Bladder training", "Scheduled toileting", "Pelvic floor exercises", "External collection device"] },
      ]},
      { title: "Clinical Status Change", category: "response", fields: [
        { type: "radio", label: "Clinical Status Change", path: "clinicalStatusChange", options: CLINICAL_STATUS_CHANGE_OPTIONS },
      ]},
      { title: "GU Notes", category: "observation", fields: [
        { type: "textarea", label: "GU Notes", path: "notes" },
      ]},
    ],
  },

  musculoskeletal: {
    title: "Musculoskeletal",
    subtitle: "Weakness, ROM, gait, mobility status (ADL assessment presents under Functional Status)",
    cards: [
      { title: "Musculoskeletal Assessment", category: "core", fields: [
        { type: "radio", label: "Weakness", path: "weakness", options: ["None", "Mild", "Moderate", "Severe", "Paralysis"] },
        { type: "radio", label: "Rigidity", path: "rigidity", options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "checkbox", label: "Rigidity Present (severity not documented)", path: "rigidityPresent" },
        { type: "radio", label: "Contractures", path: "contractures", options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "checkbox", label: "Contractures Present (severity not documented)", path: "contracturesPresent" },
        { type: "checkboxGroup", label: "Contracture Location", path: "contracturesLocation", options: ["Bilateral lower extremities", "Unilateral LE", "Upper extremities", "Hands/fingers", "Neck/spine", "Generalized"] },
        { type: "checkboxGroup", label: "ROM Loss Location", path: "romLimitations", options: ["Upper extremities", "Lower extremities", "Neck/spine", "Hands/fingers", "Generalized"] },
        { type: "checkboxGroup", label: "Issues", path: "musculoskeletalIssues", options: ["Joint swelling", "Spasms / cramps", "Amputation", "Prosthesis", "ROM loss", "None"] },
        { type: "radio", label: "Disability", path: "paralysis", options: ["None", "Paraplegia", "Quadriplegia", "Right hemiplegia", "Left hemiplegia", "Right hemiparesis", "Left hemiparesis"] },
        { type: "radio", label: "Gait", path: "gait", options: ["Normal", "Unsteady", "Shuffling", "Unable"] },
        { type: "checkboxGroup", label: "Assistive Devices", path: "assistiveDevices", options: ["Walker", "Wheelchair", "Cane", "Crutches", "Hospital bed", "Hoyer lift", "None"] },
      ]},
      { title: "Mobility Assessment", category: "functional", fields: [
        { type: "radio", label: "Ambulatory Status", path: "mobility.ambulatoryStatus", options: ["Independent", "Supervised", "Assisted", "Dependent", "Bedbound"] },
        { type: "radio", label: "Endurance", path: "mobility.endurance", options: ["Good", "Fair", "Poor"] },
        { type: "radio", label: "Transfer Ability", path: "mobility.transferAbility", options: ["Independent", "Standby assist", "1-person assist", "2-person assist", "Hoyer lift"] },
        { type: "radio", label: "Strength", path: "strength", options: ["Normal", "Decreased", "Absent"] },
        { type: "radio", label: "Balance", path: "balance", options: ["Normal", "Impaired"] },
        { type: "radio", label: "Pain with Movement", path: "painWithMovement", options: ["None", "Mild", "Moderate", "Severe"] },
      ]},
      { title: "Clinical Status Change", category: "response", fields: [
        { type: "radio", label: "Clinical Status Change", path: "clinicalStatusChange", options: CLINICAL_STATUS_CHANGE_OPTIONS },
      ]},
      { title: "Fall History & Notes", category: "observation", fields: [
        { type: "input", label: "Falls in Last 90 Days", path: "fallHistory.fallsLast90Days", inputType: "number" },
        { type: "input", label: "Fall Injuries", path: "fallHistory.fallInjuries" },
        { type: "textarea", label: "Musculoskeletal Notes", path: "notes" },
      ]},
    ],
  },

  skin: {
    title: "Skin / Wounds",
    subtitle: "Integumentary assessment, Braden Scale, wound documentation (M1190)",
    cards: [
      // Owner directive: one consolidated Integumentary assessment
      // container instead of a separate card per finding group. Body Map
      // (shouldRenderSkinMap) already injects into this same card by
      // title match ("Skin Assessment"), so Skin Integrity, Status,
      // Turgor, Temperature, Moisture, Color, Edema, and Additional
      // Findings all live together with it in one workspace. Field paths
      // are unchanged from the prior per-field cards -- no data model or
      // HOPE/SFV mapping change, presentation-only consolidation.
      { title: "Skin Assessment", category: "core", hopeCode: "M1190", fields: [
        { type: "checkbox", label: "Skin Conditions Present", path: "skinConditionsPresent" },
        { type: "checkboxGroup", label: "Skin Status", path: "skinStatus", options: ["Intact", "Dry", "Fragile", "Edematous", "Bruising", "Rash", "Jaundice", "Cyanotic", "Mottled"] },
        { type: "radio", label: "Skin Turgor", path: "skinTurgor", options: ["Good", "Fair", "Poor", "Tenting"] },
        { type: "radio", label: "Skin Moisture", path: "skinMoisture", options: ["Dry", "Moist", "Diaphoretic"] },
        { type: "radio", label: "Skin Temperature", path: "skinTemperature", options: ["Warm", "Cool", "Hot"] },
        { type: "radio", label: "Skin Color", path: "skinColorFinding", options: ["Normal", "Pale", "Cyanotic", "Jaundiced", "Mottled", "Flushed"] },
        { type: "radio", label: "Edema", path: "skinEdema.severity", options: ["None", "1+", "2+", "3+", "4+"] },
        { type: "input", label: "Edema Location", path: "skinEdema.location" },
        { type: "checkboxGroup", label: "Additional Skin Findings", path: "additionalSkinFindings", options: ["Bruising", "Skin Tears", "Excoriation", "Pruritus", "Dry Scaling", "None"] },
      ]},
      { title: "Braden Scale", category: "core", fields: [
        { type: "select", label: "Sensory Perception", path: "braden.sensoryPerception", options: [{ value: "1", label: "1 — Completely limited" }, { value: "2", label: "2 — Very limited" }, { value: "3", label: "3 — Slightly limited" }, { value: "4", label: "4 — No impairment" }] },
        { type: "select", label: "Moisture", path: "braden.moisture", options: [{ value: "1", label: "1 — Constantly moist" }, { value: "2", label: "2 — Very moist" }, { value: "3", label: "3 — Occasionally moist" }, { value: "4", label: "4 — Rarely moist" }] },
        { type: "select", label: "Activity", path: "braden.activity", options: [{ value: "1", label: "1 — Bedfast" }, { value: "2", label: "2 — Chairfast" }, { value: "3", label: "3 — Walks occasionally" }, { value: "4", label: "4 — Walks frequently" }] },
        { type: "select", label: "Mobility", path: "braden.mobility", options: [{ value: "1", label: "1 — Completely immobile" }, { value: "2", label: "2 — Very limited" }, { value: "3", label: "3 — Slightly limited" }, { value: "4", label: "4 — No limitation" }] },
        { type: "select", label: "Nutrition", path: "braden.nutrition", options: [{ value: "1", label: "1 — Very poor" }, { value: "2", label: "2 — Inadequate" }, { value: "3", label: "3 — Adequate" }, { value: "4", label: "4 — Excellent" }] },
        { type: "select", label: "Friction & Shear", path: "braden.frictionShear", options: [{ value: "1", label: "1 — Problem" }, { value: "2", label: "2 — Potential problem" }, { value: "3", label: "3 — No apparent problem" }] },
        { type: "radio", label: "Pressure Injury Risk", path: "pressureInjuryRisk", options: ["Low (19-23)", "Moderate (15-18)", "High (≤14)"] },
      ]},
      {
        title: "Wound Documentation (Structured)",
        category: "disease",
        customRenderer: "woundList",
      },
      { title: "Clinical Status Change", category: "response", fields: [
        { type: "radio", label: "Clinical Status Change", path: "clinicalStatusChange", options: CLINICAL_STATUS_CHANGE_OPTIONS },
      ]},
    ],
  },

  imminentDeath: {
    title: "Imminent Death Assessment",
    subtitle: "HOPE J0050 — Does patient appear to be within 3 days or less of death?",
    cards: [
      { title: "Prognosis Assessment", hopeCode: "J0050", fields: [
        { type: "radio", label: "Appears within 3 days or less of death?", path: "appearsThreeDaysOrLess", hopeCode: "J0050", options: [
          { value: "0", label: "0 — No" }, { value: "1", label: "1 — Yes" }, { value: "9", label: "9 — Unable to determine" }
        ]},
        { type: "checkboxGroup", label: "Indicators of Imminent Death", path: "indicators", options: [
          "Mottling of extremities", "Mandibular breathing", "Apneic periods", "Cyanosis",
          "No urine output", "Unresponsive", "Death rattle", "Cheyne-Stokes breathing",
          "Cool/cold extremities", "Decreased level of consciousness", "Inability to swallow"
        ]},
        { type: "checkbox", label: "Comfort Measures in Place", path: "comfortMeasuresInPlace" },
        { type: "checkbox", label: "Family Notified", path: "familyNotified" },
        { type: "textarea", label: "Notes", path: "notes" },
      ]},
    ],
  },

  sfv: {
    title: "Symptom Follow-up Visit (SFV)",
    subtitle: "HOPE J2050/J2052/J2053 — SFV evaluation and follow-up",
    cards: [
      { title: "SFV Screening", hopeCode: "J2050", fields: [
        { type: "checkbox", label: "Symptom Impact Screening Completed", path: "symptomImpactScreeningCompleted" },
        { type: "input", label: "Screening Date", path: "symptomImpactScreeningDate", inputType: "date" },
        // P3-009/P3-017 continuation directive Section 4: this triggering
        // RNICA screen no longer offers a local completion checkbox --
        // SFV completion is authoritative only through a separate
        // qualifying follow-up visit calling POST /visits/sfv-requirements/
        // {id}/complete (see the Symptom Follow-Up Visit section on the
        // Visit Notes screen). The read-only SfvStatusCard rendered above
        // this section shows current follow-up status.
        //
        // HOPE J2052C (Reason SFV Not Completed): CMS defines exactly one
        // coded response set (1/2/3/9). This must be a coded selection, not
        // free text -- hopeReportMapper.js::j2052ReasonNotCompleted() only
        // ever exports one of these four codes and treats anything else as
        // NOT_VERIFIED. Conditional on J2052A (sfv.inPersonSfvCompleted):
        // hidden when the SFV was completed (see the fields.map guard
        // below), shown only when it was not.
        // HOPE J2052C ownership fix (issue #146): this field is now a
        // legacy/manual fallback ONLY. Authoritative capture happens on
        // the SFV attempt visit (VisitNotes.jsx::SymptomFollowUpVisitSection
        // -> POST /visits/sfv-requirements/{id}/not-completed), attributed
        // to the clinician who actually attempted the SFV. This value is
        // no longer read by hopeReportMapper.js and is no longer required
        // to sign this assessment -- the triggering RN ICA/HUV author may
        // not be the same clinician who ever learns this answer. Still
        // conditionally hidden when J2052A = Yes (see the fields.map guard
        // below).
        { type: "radio", label: "Reason SFV Not Completed (legacy -- see SFV attempt visit for the authoritative HOPE export value)", path: "reasonNotCompleted", options: [
          { value: "1", label: "1 — Patient and/or caregiver declined an in-person visit" },
          { value: "2", label: "2 — Patient unavailable" },
          { value: "3", label: "3 — Attempts to contact patient and/or caregiver were unsuccessful" },
          { value: "9", label: "9 — None of the above" },
        ] },
      ]},
      { title: "SFV Symptom Impact", hopeCode: "J2053", fields: [
        { type: "radio", label: "A. Pain", path: "symptomImpactAtSfv.pain", hopeCode: "J2053A", options: SYMPTOM_IMPACT_OPTIONS },
        { type: "radio", label: "B. Shortness of Breath", path: "symptomImpactAtSfv.shortnessOfBreath", hopeCode: "J2053B", options: SYMPTOM_IMPACT_OPTIONS },
        { type: "radio", label: "C. Anxiety", path: "symptomImpactAtSfv.anxiety", hopeCode: "J2053C", options: SYMPTOM_IMPACT_OPTIONS },
        { type: "radio", label: "D. Nausea", path: "symptomImpactAtSfv.nausea", hopeCode: "J2053D", options: SYMPTOM_IMPACT_OPTIONS },
        { type: "radio", label: "E. Vomiting", path: "symptomImpactAtSfv.vomiting", hopeCode: "J2053E", options: SYMPTOM_IMPACT_OPTIONS },
        { type: "radio", label: "F. Diarrhea", path: "symptomImpactAtSfv.diarrhea", hopeCode: "J2053F", options: SYMPTOM_IMPACT_OPTIONS },
        { type: "radio", label: "G. Constipation", path: "symptomImpactAtSfv.constipation", hopeCode: "J2053G", options: SYMPTOM_IMPACT_OPTIONS },
        { type: "radio", label: "H. Agitation", path: "symptomImpactAtSfv.agitation", hopeCode: "J2053H", options: SYMPTOM_IMPACT_OPTIONS },
      ]},
      { title: "SFV Findings", fields: [
        { type: "checkboxGroup", label: "Triggered Symptoms", path: "triggeredSymptoms", options: ["Pain", "SOB", "Anxiety", "Nausea", "Vomiting", "Diarrhea", "Constipation", "Agitation"] },
        { type: "textarea", label: "Findings", path: "findings" },
        { type: "textarea", label: "Notes", path: "notes" },
      ]},
    ],
  },

  safety: {
    title: "Environmental / Safety",
    subtitle: "Home safety, fall risk, disaster triage level",
    cards: [
      { title: "Safety Assessment", fields: [
        { type: "checkbox", label: "Safety Assessment Completed", path: "safetyAssessmentCompleted" },
        { type: "checkboxGroup", label: "Home Environment Hazards", path: "homeEnvironment", options: [
          "Adequate lighting", "Handrails present", "Throw rugs", "Clutter/obstacles",
          "Stairs without railing", "Pets", "Weapons/firearms", "Pest infestation",
          "Inadequate heating/cooling", "Smoke detectors present"
        ]},
        { type: "checkbox", label: "Fall Risk Assessment Completed", path: "fallRiskAssessmentCompleted" },
        { type: "radio", label: "Fall Risk Level", path: "fallRiskLevel", options: ["Low", "Moderate", "High"] },
        { type: "radio", label: "Transfer Safety", path: "transferSafetyLevel", options: [
          "Independent", "Needs assist x1", "Needs assist x2", "Mechanical lift required", "Unsafe/high risk"
        ]},
        { type: "checkbox", label: "Firearm in Home", path: "firearmInHome" },
        { type: "checkbox", label: "Oxygen in Use", path: "oxygenInUse" },
        { type: "checkbox", label: "Oxygen Safety Reviewed", path: "oxygenSafetyReviewed" },
        { type: "checkbox", label: "Incident/Occurrence Reported This Visit", path: "incidentOccurrenceReported" },
        { type: "textarea", label: "Incident/Occurrence Notes", path: "incidentOccurrenceNotes" },
      ]},
      { title: "Disaster Triage", fields: [
        { type: "radio", label: "Disaster Level", path: "disasterLevel", options: [
          "Level 1 — Hospice must assist; no assistance available",
          "Level 2 — Hospice must contact to assure adequate assistance; limited assistance available",
          "Level 3 — No need for hospice to assist; has adequate assistance available"
        ]},
        { type: "checkboxGroup", label: "Level 1 Conditions (two or more apply)", path: "disasterLevelOneConditions", options: [
          "Bed- or chair-confined", "Dependent on walker or cane",
          "Lives above ground floor", "Requires electricity for medical equipment"
        ]},
        { type: "checkboxGroup", label: "Level 2 Conditions (one applies)", path: "disasterLevelTwoConditions", options: [
          "Bed- or chair-confined", "Dependent on walker or cane",
          "Lives above ground floor", "Requires electricity for medical equipment"
        ]},
        { type: "checkboxGroup", label: "Level 3 Conditions", path: "disasterLevelThreeConditions", options: [
          "Lives in facility with disaster support", "Has alternate location and available helper to go to"
        ]},
        { type: "textarea", label: "Safety Notes", path: "notes" },
      ]},
      { title: "DME (Durable Medical Equipment)", customRenderer: "dmeStatus" },
      { title: "Supplies", fields: [
        { type: "checkboxGroup", label: "Existing Supplies", path: "supplies.existingCategories", options: [
          "Wound supplies", "Continence supplies", "Oxygen supplies", "Medication supplies", "Other supplies"
        ]},
        { type: "checkboxGroup", label: "Needed Supplies", path: "supplies.neededCategories", options: [
          "Wound supplies", "Continence supplies", "Oxygen supplies", "Medication supplies", "Other supplies"
        ]},
        { type: "textarea", label: "Other Supplies Notes", path: "supplies.otherSuppliesNotes" },
      ]},
    ],
  },

  psychosocial: {
    title: "Psychosocial Referral Determination",
    subtitle: "Is Social Work involvement needed? The RN documents findings — SNS determines the recommendation.",
    cards: [
      { title: "Referral Indicators", fields: [
        { type: "checkboxGroup", label: "Findings supporting an MSW referral", path: "referralIndicators", options: [
          "Family unable to cope", "Caregiver overwhelmed", "Caregiver burden present", "Family in denial",
          "Family conflict present", "Limited hospice understanding", "Resource concerns (financial/housing/transportation)",
          "Inadequate support system", "Suicide/self-harm risk indicated", "None indicated",
        ]},
      ]},
      { title: "SNS Referral Recommendation", customRenderer: "referralRecommendation" },
      { title: "Family Response", fields: [
        { type: "radio", label: "Family Response", path: "familyResponse", options: ["Accepted", "Refused", "Deferred"] },
        { type: "textarea", label: "Notes", path: "notes" },
      ]},
      { title: "Referral Refused", customRenderer: "referralRefusal" },
    ],
  },

  spiritual: {
    title: "Spiritual Referral Determination",
    subtitle: "Is Spiritual Care involvement needed? The RN documents findings — SNS determines the recommendation.",
    cards: [
      { title: "Faith & Clergy", fields: [
        { type: "input", label: "Religious / Faith Preference", path: "religiousPreference" },
        { type: "select", label: "Clergy Involvement", path: "clergyInvolvement", options: ["Not involved", "Community clergy involved", "Facility chaplain involved", "Both"] },
      ]},
      { title: "Referral Indicators", fields: [
        { type: "checkboxGroup", label: "Findings supporting a Spiritual Care referral", path: "referralIndicators", options: [
          "Family requested clergy", "Patient requested clergy", "Last rites requested",
          "Spiritual distress expressed by family", "Spiritual support needs identified",
          "Existing clergy already involved", "None indicated",
        ]},
      ]},
      { title: "SNS Referral Recommendation", customRenderer: "referralRecommendation" },
      { title: "Family Response", fields: [
        { type: "radio", label: "Family Response", path: "familyResponse", options: ["Accepted", "Refused", "Deferred"] },
      ]},
      { title: "Referral Refused", customRenderer: "referralRefusal" },
      { title: "F3000 — Spiritual / Existential Concerns", hopeCode: "F3000", fields: [
        { type: "radio", label: "Was patient and/or caregiver asked about spiritual/existential concerns?", path: "concernsAskedStatus", hopeCode: "F3000",
          options: [{ value: "0", label: "No" }, { value: "1", label: "Yes, and discussion occurred" }, { value: "2", label: "Yes, but refused to discuss" }] },
        { type: "input", label: "Date first asked", path: "concernsDiscussedDate", inputType: "date" },
        { type: "textarea", label: "Additional Notes", path: "notes" },
      ]},
    ],
  },

  bereavement: {
    title: "Bereavement Referral Determination",
    subtitle: "Should bereavement follow-up be prioritized? The RN documents risk factors — SNS determines the recommendation.",
    cards: [
      { title: "Risk Factors", fields: [
        { type: "checkboxGroup", label: "Findings supporting bereavement follow-up priority", path: "riskFactors", options: [
          "High-risk family situation", "Vulnerable caregiver(s) identified", "Anticipatory grief concerns",
          "Significant family stressors", "History of complicated grief", "Multiple recent losses", "None indicated",
        ]},
      ]},
      { title: "SNS Referral Recommendation", customRenderer: "referralRecommendation" },
      { title: "Family Response", fields: [
        { type: "radio", label: "Family Response", path: "familyResponse", options: ["Accepted", "Refused", "Deferred"] },
        { type: "textarea", label: "Notes", path: "notes" },
      ]},
      { title: "Referral Refused", customRenderer: "referralRefusal" },
    ],
  },

  personalCare: {
    title: "Personal Care & Support Needs",
    subtitle: "Home aide tasks, volunteer services, community resources, equipment needs",
    cards: [
      { title: "Home Visit Aide Tasks", fields: [
        { type: "checkboxGroup", label: "Aide Tasks Needed", path: "aideTasks", options: [
          "None",
          "Bathing/showering", "Hair care/grooming", "Oral hygiene", "Skin care",
          "Dressing", "Toileting assistance", "Transfers/mobility", "Light meal preparation",
          "Light housekeeping", "Laundry", "Linen change", "Vital signs", "Range of motion exercises",
          "Respite for caregiver", "See ADL assessment for other needs"
        ]},
      ]},
      { title: "Aide Visit Preferences", fields: [
        { type: "select", label: "Frequency", path: "aideVisitPreferences.frequency", options: ["Daily", "3x/week", "2x/week", "Weekly", "PRN"] },
        { type: "radio", label: "Preferred Time", path: "aideVisitPreferences.preferredTime", options: ["Morning", "Afternoon", "Evening", "Flexible"] },
        { type: "select", label: "Duration", path: "aideVisitPreferences.duration", options: ["1 hour", "2 hours", "3 hours", "4 hours"] },
      ]},
      { title: "Volunteer Services", fields: [
        { type: "checkboxGroup", label: "Services Needed", path: "volunteerServices", options: [
          "None",
          "Companionship/visits", "Respite care", "Errand assistance", "Transportation",
          "Vigil/11th hour", "Pet care", "Legacy project", "Music/art therapy", "Reading/letter writing"
        ]},
      ]},
      { title: "Community Resources", fields: [
        { type: "checkboxGroup", label: "Resources Needed", path: "communityResources", options: [
          "None",
          "Meals on Wheels", "Adult day care", "Transportation services", "Legal aid",
          "Financial assistance programs", "Faith community support", "Veteran services", "Disease-specific organizations"
        ]},
      ]},
      { title: "Equipment/Supply Needs", fields: [
        { type: "checkboxGroup", label: "Equipment Needed", path: "equipmentSupplyNeeds", options: [
          "Hospital bed", "Wheelchair", "Walker", "Commode", "Shower chair",
          "Hoyer lift", "Egg crate mattress", "Incontinence supplies", "Wound care supplies",
          "Air mattress", "Bedpan", "Overbed table", "Cane", "Geri-chair/recliner",
          "Urinal", "Nebulizer", "Suction machine", "O2 concentrator", "E-tank"
        ]},
        { type: "textarea", label: "Personal Care Notes", path: "notes" },
      ]},
    ],
  },

  teachingNeeds: {
    title: "Teaching Needs",
    subtitle: "Patient/family education assessment, topics, methods, response",
    cards: [
      { title: "Teaching Assessment", fields: [
        { type: "radio", label: "Primary Learner", path: "primaryLearner", options: ["Patient", "Caregiver", "Both"] },
        { type: "radio", label: "Learning Style Preference", path: "learningStylePreference", options: ["Visual", "Auditory", "Hands-on", "Written materials"] },
        { type: "checkboxGroup", label: "Barriers to Learning", path: "barriersToLearning", options: [
          "Language", "Literacy", "Cognitive impairment", "Hearing deficit",
          "Vision deficit", "Emotional readiness", "Cultural considerations", "Denial of diagnosis"
        ]},
      ]},
      { title: "Teaching Topics", fields: [
        { type: "checkboxGroup", label: "Teach Patient/Family/PCG", path: "teachingTopics", options: [
          "Diagnosis and disease process",
          "Medication administration",
          "Medication side effects",
          "Medication contraindications",
          "Comfort pack use",
          "Opioid use and risk",
          "Medication reconciliation",
          "Oxygen",
          "DME (durable medical equipment)",
          "Infection control",
          "Universal precautions",
          "Safe use and disposal of controlled medications",
          "Other education",
        ]},
        { type: "input", label: "Other Topic (specify)", path: "teachingTopicsOther" },
      ]},
      { title: "Teaching Methods Used", fields: [
        { type: "checkboxGroup", label: "Methods", path: "teachingMethods", options: [
          "Verbal instruction", "Written materials provided", "Demonstration",
          "Return demonstration", "Video/multimedia", "Interpreter used"
        ]},
      ]},
      { title: "Patient/Family Response", fields: [
        { type: "radio", label: "Response", path: "patientFamilyResponse", options: [
          "Verbalized understanding", "Demonstrated competency", "Needs reinforcement",
          "Unable to learn at this time", "Refused teaching"
        ]},
        { type: "textarea", label: "Follow-up Plan", path: "followUpPlan" },
        { type: "textarea", label: "Teaching Notes", path: "notes" },
      ]},
    ],
  },

  admissionsOrder: {
    title: "Admissions Order",
    subtitle: "Physician's initial order — LOC, visit frequency, HA assignment, POC/IDG, non-covered items",
    cards: [
      { title: "Admission Statement", cms: "Verbal Order", fields: [
        { type: "textarea", label: "Admission Order Statement", path: "admissionStatement", rows: 4 },
      ]},
      { title: "Level of Care", fields: [
        { type: "radio", label: "Level of Care", path: "levelOfCare.level", options: ["Routine Care", "General Inpatient", "Continuous Care", "Respite Care"] },
        { type: "input", label: "Effective Date", path: "levelOfCare.effectiveDate", inputType: "date" },
        { type: "textarea", label: "LOC Justification", path: "levelOfCare.justification" },
      ]},
      { title: "Discipline Frequency of Visit", customRenderer: "disciplineFrequencyOfVisit", fields: [] },
      { title: "HA Assignment", customRenderer: "haAssignment", fields: [
        { type: "input", label: "Assigned Home Aide", path: "haAssignment.assignedAide" },
        { type: "checkbox", label: "HA Assignment N/A", path: "haAssignment.notApplicable" },
      ]},
      { title: "Initial POC/IDG", fields: [
        { type: "checkbox", label: "Initial POC Created", path: "initialPocIdg.created" },
        { type: "input", label: "Created Date", path: "initialPocIdg.createdDate", inputType: "date" },
        { type: "textarea", label: "POC/IDG Notes", path: "initialPocIdg.notes" },
      ]},
      { title: "T.O. Verification", fields: [
        { type: "checkbox", label: "Verbal Order Read Back and Verified", path: "toVerification.verbalOrderReadBack" },
        { type: "input", label: "Verified By", path: "toVerification.verifiedBy" },
        { type: "checkbox", label: "Prescriber on Call Contacted", path: "toVerification.prescriberContacted" },
        { type: "input", label: "Verification Timestamp", path: "toVerification.verificationTimestamp", inputType: "datetime-local" },
      ]},
    ],
  },

  referrals: {
    title: "Referrals",
    subtitle: "Social work, spiritual care, volunteer, therapy, dietitian, pharmacist",
    cards: [
      { title: "Referral Status", fields: [
        { type: "checkbox", label: "Social Work Referral", path: "socialWork.referred" },
        { type: "input", label: "SW Reason", path: "socialWork.reason" },
        { type: "checkbox", label: "Spiritual Care Referral", path: "spiritualCare.referred" },
        { type: "input", label: "SC Reason", path: "spiritualCare.reason" },
        { type: "checkbox", label: "Volunteer Referral", path: "volunteer.referred" },
        { type: "input", label: "Volunteer Type", path: "volunteer.type" },
        { type: "checkbox", label: "Dietitian Referral", path: "dietitian.referred" },
        { type: "input", label: "Dietitian Reason", path: "dietitian.reason" },
        { type: "checkbox", label: "Pharmacist Referral", path: "pharmacist.referred" },
        { type: "input", label: "Pharmacist Reason", path: "pharmacist.reason" },
        { type: "textarea", label: "Referral Notes", path: "notes" },
        { type: "checkbox", label: "I reviewed the referral status for this patient and it is current and complete.", path: "reviewed" },
      ]},
    ],
  },

  finalization: {
    title: "Finalization & Signature",
    subtitle: "Completion, certification, clinician signature",
    cards: [
      { id: "rnica-clinical-narrative", title: "Clinical Narrative", fields: [
        { type: "textarea", label: "Clinical narrative", path: "clinicalNarrative", rows: 8, required: true,
          placeholder: "Synthesize the completed whole-patient assessment findings, changes, interventions, response, risks, and plan. Review all source-linked draft content before attestation." },
      ]},
      { title: "Amendments", customRenderer: "finalReviewDashboard", fields: [] },
      { title: "Completion Status", cms: "F2000/F2100/F2200", fields: [
        { type: "checkbox", label: "Signature Certification — I certify this assessment is complete and accurate", path: "signatureCertification" },
        { type: "input", label: "Clinician Signature", path: "clinicianSignature", required: true },
        { type: "input", label: "Signature Date", path: "signatureDate", inputType: "date", required: true },
        { type: "input", label: "HOPE Submission / Confirmation Number", path: "hopeSubmissionNumber" },
        { type: "checkbox", label: "HOPE report already submitted — tracking not required", path: "hopeAlreadySubmitted" },
      ]},
      { title: "Supervisor Review", fields: [
        { type: "checkbox", label: "Supervisor Review Required", path: "supervisorReview.required" },
        { type: "input", label: "Reviewed By", path: "supervisorReview.reviewedBy" },
        { type: "input", label: "Review Date", path: "supervisorReview.reviewDate", inputType: "date" },
      ]},
    ],
  },
};

// Recursively merges a saved form-data object onto the full INITIAL_FORM
// defaults so that partial/older records (missing nested keys added later)
// don't crash rendering. Arrays are taken wholesale from `saved` when
// present (not merged element-wise); plain objects are merged key-by-key.
function deepMergeFormData(defaults, saved) {
  if (saved === undefined || saved === null) return defaults;
  if (Array.isArray(defaults) || Array.isArray(saved)) {
    return Array.isArray(saved) ? saved : defaults;
  }
  if (typeof defaults === "object" && typeof saved === "object") {
    const merged = { ...defaults };
    for (const key of Object.keys(defaults)) {
      merged[key] = deepMergeFormData(defaults[key], saved[key]);
    }
    // Preserve any extra keys present in saved but not in defaults.
    for (const key of Object.keys(saved)) {
      if (!(key in merged)) merged[key] = saved[key];
    }
    return merged;
  }
  return saved !== undefined ? saved : defaults;
}

// ════════════════════════════════════════════════════════════════
// SECTION 1 — PATIENT & ENCOUNTER SNAPSHOT (read-only)
// ════════════════════════════════════════════════════════════════
// Per docs/SNS_RNICA_MASTER_MAP_1.1.md L94-151: "This section displays
// authoritative information. It does not duplicate or independently own
// patient data." Every value below comes from the same authoritative,
// already-existing endpoints PatientFacesheet.jsx uses
// (GET /patients/{id}/facesheet, /performance-history) — no new backend
// field/model/write-path was added. PatientFacesheet.jsx itself was used
// only as a visual model (spacing/typography/card treatment), not
// imported, extended, or coupled to. Fields with no authoritative source
// (living arrangement, medication summary, interpreter need, NYHA, POC
// problem/goal/intervention sub-routes) are intentionally omitted — see
// the contract's "Open Items" section for the tracked defects.
const CARE_TEAM_DISPLAY_FIELDS = [
  { key: "primary_rn_name", label: "Primary RN" },
  { key: "lvn_name", label: "LVN" },
  { key: "social_worker_name", label: "Social Worker" },
  { key: "chaplain_name", label: "Chaplain" },
  { key: "chha_name", label: "CHHA" },
  { key: "volunteer_name", label: "Volunteer" },
  { key: "clinical_manager_name", label: "Clinical Manager" },
];

function Section1SnapshotBadge({ colors, tone, children }) {
  const palette = {
    auto: { bg: colors.tealBg, color: colors.teal },
    manual: { bg: colors.amberTagBg, color: colors.warning },
    unassigned: { bg: colors.border, color: colors.gray },
    synced: { bg: colors.hopeTagBg, color: colors.hope },
  }[tone] || { bg: colors.border, color: colors.gray };
  return (
    <span style={{
      display: "inline-block", padding: "1px 7px", borderRadius: 4, fontSize: 9,
      fontWeight: 700, letterSpacing: 0.4, textTransform: "uppercase",
      background: palette.bg, color: palette.color, whiteSpace: "nowrap",
    }}>
      {children}
    </span>
  );
}

function Section1SnapshotItem({ colors, label, value }) {
  return (
    <div style={{ minHeight: 34 }}>
      <span style={{ color: colors.gray, fontSize: 9, textTransform: "uppercase", letterSpacing: 0.4, display: "block" }}>
        {label}
      </span>
      <span style={{ color: colors.dark, fontSize: 12.5, fontWeight: 600 }}>{value || "—"}</span>
    </div>
  );
}

function Section1CareTeamGrid({ colors, facesheet }) {
  const assignments = facesheet?.care_team?.assignments || {};
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
      gap: 10,
    }}>
      {CARE_TEAM_DISPLAY_FIELDS.map(({ key, label }) => {
        const autoMatch = assignments[key];
        const manualName = facesheet?.care_team?.[key];
        const name = autoMatch?.name || manualName || null;
        const tone = autoMatch ? "auto" : manualName ? "manual" : "unassigned";
        const tag = autoMatch ? "AUTO" : manualName ? "MANUAL" : "UNASSIGNED";
        return (
          <div key={key} style={{
            display: "flex", flexDirection: "column", justifyContent: "space-between",
            minHeight: 66, padding: "8px 10px", border: `1px solid ${colors.border}`,
            borderRadius: 8, background: colors.white,
          }}>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 6, minHeight: 24 }}>
              <span style={{ color: colors.gray, fontSize: 10, textTransform: "uppercase", letterSpacing: 0.4, lineHeight: 1.3 }}>
                {label}
              </span>
              <Section1SnapshotBadge colors={colors} tone={tone}>{tag}</Section1SnapshotBadge>
            </div>
            <span style={{ color: colors.dark, fontSize: 12.5, fontWeight: 700, marginTop: 6 }}>
              {name || "Unassigned"}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function Section1Snapshot({ colors, patientSummary, facesheet, facesheetError, performanceHistory, locked, saving, resolvedPatientId, patientIdProp }) {
  if (!patientSummary?.patient) return null;
  const identity = facesheet?.identity || {};
  const address = facesheet?.address || {};
  const clinical = facesheet?.clinical || {};
  const levelOfCare = facesheet?.level_of_care || {};
  const placeOfService = facesheet?.place_of_service || {};
  const serviceDates = facesheet?.service_dates || {};
  const benefitPeriod = facesheet?.benefit_period || {};
  const hospiceSnapshot = facesheet?.hospice_snapshot || {};
  const physicians = facesheet?.physicians || {};
  const contacts = facesheet?.contacts || {};
  const latestPerformance = performanceHistory?.[0] || null;
  const pid = resolvedPatientId || patientIdProp;

  const age = (() => {
    if (!identity.dob) return null;
    const dob = new Date(identity.dob);
    if (Number.isNaN(dob.getTime())) return null;
    const today = new Date();
    let years = today.getFullYear() - dob.getFullYear();
    const m = today.getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) years--;
    return years;
  })();

  const contactLine = (contact) => {
    if (!contact || !contact.name) return null;
    return contact.relationship ? `${contact.name} (${contact.relationship})` : contact.name;
  };

  return (
    <div style={{
      margin: "0 24px 16px", padding: "12px 14px", borderRadius: 8,
      border: `1px solid ${colors.border}`, background: colors.bg,
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <span style={{ color: colors.dark, fontSize: 13, fontWeight: 700 }}>Section 1 — Patient &amp; Encounter Snapshot</span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: colors.gray, fontSize: 9.5, fontFamily: "monospace" }}>
            {import.meta.env.VITE_BUILD_BRANCH ? `${import.meta.env.VITE_BUILD_BRANCH} @ ${import.meta.env.VITE_BUILD_COMMIT}` : ""}
          </span>
          <Section1SnapshotBadge colors={colors} tone="unassigned">READ ONLY</Section1SnapshotBadge>
        </div>
      </div>
      {facesheetError && (
        <div style={{ color: colors.error, fontSize: 11, marginBottom: 8 }}>Facesheet: {facesheetError}</div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "8px 16px", marginBottom: 12 }}>
        <Section1SnapshotItem colors={colors} label="DOB / Age" value={identity.dob ? `${identity.dob}${age !== null ? ` (${age}y)` : ""}` : null} />
        <Section1SnapshotItem colors={colors} label="Sex" value={identity.gender} />
        <Section1SnapshotItem colors={colors} label="SOC Date" value={serviceDates.soc_date} />
        <Section1SnapshotItem colors={colors} label="Benefit Period" value={benefitPeriod.benefit_period_number ? `#${benefitPeriod.benefit_period_number} (${benefitPeriod.benefit_period_start || "?"} – ${benefitPeriod.benefit_period_end || "?"})` : null} />
        <Section1SnapshotItem colors={colors} label="Level of Care" value={levelOfCare.current_level_of_care} />
        <Section1SnapshotItem colors={colors} label="Payer" value={facesheet?.insurance?.primary_payer} />
        <Section1SnapshotItem colors={colors} label="Site of Service" value={placeOfService.current_pos_type} />
        <Section1SnapshotItem colors={colors} label="Facility" value={placeOfService.current_pos_name} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "8px 16px", marginBottom: 12 }}>
        <Section1SnapshotItem colors={colors} label="Terminal Diagnosis" value={clinical.active_primary_diagnosis?.description || clinical.primary_diagnosis} />
        <Section1SnapshotItem colors={colors} label="Related / Comorbid Dx" value={clinical.secondary_diagnoses} />
        <Section1SnapshotItem colors={colors} label="Code Status" value={hospiceSnapshot.code_status} />
        <Section1SnapshotItem colors={colors} label="Allergies" value={clinical.allergies || (clinical.has_allergies === false ? "NKDA" : null)} />
        <Section1SnapshotItem colors={colors} label="PPS / KPS / FAST" value={
          (latestPerformance || hospiceSnapshot.pps_score)
            ? `${latestPerformance?.pps ?? hospiceSnapshot.pps_score ?? "—"} / ${latestPerformance?.kps ?? hospiceSnapshot.kps_score ?? "—"} / ${latestPerformance?.fast_stage ?? hospiceSnapshot.fast_stage ?? "—"}`
            : null
        } />
        <Section1SnapshotItem colors={colors} label="Attending Physician" value={physicians.attending?.name} />
        <Section1SnapshotItem colors={colors} label="Medical Director" value={physicians.medical_director?.name} />
        <Section1SnapshotItem colors={colors} label="Preferred Language" value={identity.language} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "8px 16px", marginBottom: 12 }}>
        <Section1SnapshotItem colors={colors} label="Primary Caregiver" value={contactLine(contacts.primary_caregiver)} />
        <Section1SnapshotItem colors={colors} label="Decision-Maker" value={contactLine(contacts.decision_maker)} />
        <Section1SnapshotItem colors={colors} label="Emergency Contact" value={contactLine(contacts.emergency_contact)} />
      </div>

      <div style={{ marginBottom: 6 }}>
        <span style={{ color: colors.dark, fontSize: 11.5, fontWeight: 700 }}>Care Team</span>
      </div>
      <Section1CareTeamGrid colors={colors} facesheet={facesheet} />

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 12, gap: 10, flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: 14 }}>
          <Section1SnapshotItem colors={colors} label="Assessment Status" value={locked ? "LOCKED" : "IN PROGRESS"} />
          <Section1SnapshotItem colors={colors} label="Autosave" value={saving ? "Saving…" : "Saved"} />
        </div>
        {pid ? (
          <button
            type="button"
            onClick={() => window.open(`/plan-of-care?patientId=${pid}`, "_blank", "noopener")}
            title="Opens the patient's current Master Plan of Care in a new tab (read-only link — Section 11 problem/goal/intervention deep-links are not yet available)"
            style={{
              fontSize: 11, fontWeight: 700, padding: "5px 10px", borderRadius: 6,
              border: `1px solid ${colors.border}`, background: colors.white, color: colors.dark, cursor: "pointer",
            }}
          >
            View Master Plan of Care ↗
          </button>
        ) : null}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// 8. MAIN COMPONENT
// ════════════════════════════════════════════════════════════════

export default function RNICA({ patientId, assessmentId: existingAssessmentId = undefined, mode = "ica", onFormDataChange = undefined, workspacePilot = false, onExitWorkspacePilot = () => {}, onNavigateToSection = undefined }) {
  const navigate = useNavigate();
  const initialPatientId = patientId ?? getActivePatientId() ?? "";
  const [resolvedPatientId, setResolvedPatientId] = useState(initialPatientId);
  const [patientSummary, setPatientSummary] = useState(null);
  const [patientSummaryError, setPatientSummaryError] = useState("");
  // Section 1 (Patient & Encounter Snapshot) read-only data. Sourced
  // exclusively from the same authoritative endpoints PatientFacesheet.jsx
  // already uses (GET /patients/{id}/facesheet, /performance-history) — no
  // new backend field, model, or write path. See
  // docs/SNS_RNICA_SECTION_1_IMPLEMENTATION_CONTRACT.md.
  const [facesheetData, setFacesheetData] = useState(null);
  // True once the "load existing assessment" fetch has resolved (success or
  // failure). The facesheet-driven demographics prefill below must wait for
  // this so it always applies AFTER any saved draft is loaded into
  // formData -- otherwise, whichever of the two independent async fetches
  // (assessment draft vs. facesheet) happens to resolve second wins the
  // race and can silently wipe out the other's data.
  const [assessmentLoaded, setAssessmentLoaded] = useState(false);
  const [facesheetError, setFacesheetError] = useState("");
  const [performanceHistory, setPerformanceHistory] = useState([]);
  const [formData, setFormData] = useState(JSON.parse(JSON.stringify(INITIAL_FORM)));
  const [activeSection, setActiveSection] = useState("demographics");
  // Sections collapse independently of "activeSection" (which still drives
  // the validation panel / SFV banner scoping). Nothing is unmounted when
  // collapsed or off-screen — CSS `content-visibility` (below) skips the
  // browser's layout/paint work for content that isn't visible, so keeping
  // all 28 sections mounted in one scrollable page stays cheap.
  const [collapsedSections, setCollapsedSections] = useState(() => new Set());
  const sectionRefs = useRef({});
  const isSectionOpen = (key) => !collapsedSections.has(key);
  const toggleSection = (key) => {
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };
  const jumpToSection = (key) => {
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
  };
  const [assessmentId, setAssessmentId] = useState(existingAssessmentId || null);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);
  const [pageError, setPageError] = useState("");
  const [intelligenceError, setIntelligenceError] = useState("");
  const [validation, setValidation] = useState({ errors: {}, warnings: {}, isValid: true });
  const [locked, setLocked] = useState(false);
  const [lockedAt, setLockedAt] = useState(null);
  const [finalizationReadiness, setFinalizationReadiness] = useState(null);
  const [intelligence, setIntelligence] = useState(null);
  const [intelligenceLoading, setIntelligenceLoading] = useState(false);

  // --- Structured Findings application layer (dedicated, separate from ---
  // --- the narrative AI-signal review workflow above) ---------------------
  // `pendingStructuredSignals` mirrors intelligence.structured_findings_signals
  // (harvested signals with review_status === "NEW" that carry validated
  // StructuredFinding objects — from REFERRAL_HNP, uploaded documents,
  // transcripts, etc). Kept as separate local state (rather than read
  // directly off `intelligence`) so an Apply/Dismiss action can remove a
  // signal from the visible list immediately, without waiting on a full
  // intelligence refetch.
  const [pendingStructuredSignals, setPendingStructuredSignals] = useState([]);
  const [structuredFindingsBusyId, setStructuredFindingsBusyId] = useState(null);
  const [structuredFindingsError, setStructuredFindingsError] = useState("");
  // Provenance: every field ever populated by an applied structured finding,
  // so the RN can always see why a control is populated (source type,
  // excerpt, concept, confidence) — never silently overwritten again once
  // recorded here.
  const [structuredFieldProvenance, setStructuredFieldProvenance] = useState([]);
  // Conflicts: fields where an existing (RN-entered) value differed from
  // the AI-suggested value — the clinician value is never overwritten;
  // these are surfaced for explicit RN review/resolution instead.
  const [structuredFieldConflicts, setStructuredFieldConflicts] = useState([]);
  // Acceptance Analytics (read-only): counts by status/application rate
  // for this patient's structured findings, computed entirely from
  // persisted review_status data on the backend (no new schema). Refetched
  // whenever the pending list changes size, so applying/dismissing
  // (single or bulk) keeps the summary current without a full page reload.
  const [structuredFindingsAnalytics, setStructuredFindingsAnalytics] = useState(null);
  // RN Productivity Metrics (read-only): fields_populated and
  // manual_entries_avoided, also computed entirely from persisted data
  // (no time-saved estimate -- that would require an assumption, not a
  // persisted fact). Refetched alongside Acceptance Analytics above.
  const [rnProductivityMetrics, setRnProductivityMetrics] = useState(null);
  // P1A (J2052 read-path correction, docs/tenant-platform/
  // J2052_J2053_LINEAGE_AUDIT.md): the on-screen SFV status badge below
  // must also read the authoritative SFVRequirement directly rather than
  // the RNICA form's own self-attested `sfv.inPersonSfvCompleted`. This
  // mirrors SfvStatusCard's own "most-recently-completed" selection
  // logic (RNICA.jsx's SfvStatusCard component) so both surfaces agree;
  // it is a separate, independent fetch from that card's, matching the
  // existing pattern of other supplementary read-only cards on this page
  // (e.g. DeclineTrackerCard, WeightLossAutoCalcCard) each fetching their
  // own data independently.
  const [latestSfvRequirement, setLatestSfvRequirement] = useState(null);

  useEffect(() => {
    if (!patientId) {
      setLatestSfvRequirement(null);
      return undefined;
    }
    let cancelled = false;
    listSfvRequirements(patientId)
      .then((rows) => {
        if (cancelled) return;
        const completedRows = (rows || []).filter((r) => r.status === "COMPLETED" && r.completedAt);
        const latest = completedRows.sort((a, b) => (a.completedAt < b.completedAt ? 1 : -1))[0];
        setLatestSfvRequirement(latest || null);
      })
      .catch(() => { if (!cancelled) setLatestSfvRequirement(null); });
    return () => { cancelled = true; };
  }, [patientId]);

  useEffect(() => {
    setPendingStructuredSignals(intelligence?.structured_findings_signals || []);
  }, [intelligence]);

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    getStructuredFindingsAnalytics({ patientId })
      .then((data) => {
        if (!cancelled) setStructuredFindingsAnalytics(data);
      })
      .catch(() => {
        // Analytics is a non-critical, supplementary summary -- never
        // block or error out the rest of the RNICA page over it.
        if (!cancelled) setStructuredFindingsAnalytics(null);
      });
    getRnProductivityMetrics({ patientId })
      .then((data) => {
        if (!cancelled) setRnProductivityMetrics(data);
      })
      .catch(() => {
        if (!cancelled) setRnProductivityMetrics(null);
      });
    return () => {
      cancelled = true;
    };
  }, [patientId, pendingStructuredSignals.length]);

  const handleApplyStructuredSignal = useCallback(
    async (signal) => {
      setStructuredFindingsError("");
      setStructuredFindingsBusyId(signal.id);
      try {
        const { formData: nextFormData, appliedFields, conflicts } = applyStructuredFindings(
          formData,
          signal.structured_findings || []
        );

        const provenanceEntries = appliedFields.map((f) => ({
          section: f.section,
          path: f.path,
          value: f.value,
          concept_code: f.concept_code,
          source_type: signal.source_type,
          source_excerpt: signal.original_text_excerpt,
          recorded_at: signal.recorded_at,
          confidence: f.finding?.confidence,
          signal_id: signal.id,
        }));
        const nextProvenance =
          provenanceEntries.length > 0 ? [...structuredFieldProvenance, ...provenanceEntries] : structuredFieldProvenance;

        // Persist the field values AND their provenance durably BEFORE
        // marking the source signal "APPLIED" (reviewed/consumed). These
        // writes must land together: relying on the 30s autosave timer to
        // eventually notice the local `formData` change was the root cause
        // of signals being marked applied while their destination fields
        // silently never reached the saved chart (lost on tab close/nav/
        // reload). Persisting fieldProvenance in this same call (not just
        // React state) is what lets the RN still see WHY a field was
        // populated after a refresh, logout, or reconnect. If this save
        // fails, we throw before marking anything applied or touching
        // visible state, so the RN can safely retry with no data loss.
        let persistedAssessmentId = assessmentId;
        if (persistedAssessmentId) {
          await api.updateRNICAAssessment(persistedAssessmentId, nextFormData, nextProvenance);
        } else {
          const result = await api.saveRNICAAssessment(
            patientId,
            nextFormData,
            isOngoing ? assessmentType : undefined
          );
          persistedAssessmentId = result.assessmentId;
          setAssessmentId(persistedAssessmentId);
        }
        markPersisted(nextFormData, persistedAssessmentId);
        setFormData(nextFormData);

        if (provenanceEntries.length > 0) {
          setStructuredFieldProvenance(nextProvenance);
        }
        if (conflicts.length > 0) {
          const conflictEntries = conflicts.map((c) => ({
            section: c.section,
            path: c.path,
            existingValue: c.existingValue,
            suggestedValue: c.suggestedValue,
            concept_code: c.concept_code,
            source_type: signal.source_type,
            source_excerpt: signal.original_text_excerpt,
            signal_id: signal.id,
          }));
          setStructuredFieldConflicts((prev) => [...prev, ...conflictEntries]);
        }

        const reasonParts = [];
        if (appliedFields.length > 0) reasonParts.push(`applied ${appliedFields.length} field(s)`);
        if (conflicts.length > 0) reasonParts.push(`${conflicts.length} conflict(s) for review`);
        await reviewHarvestedSignalOffline(
          signal.id,
          "APPLIED",
          reasonParts.length > 0 ? reasonParts.join("; ") : "No blank fields to populate"
        );
        setPendingStructuredSignals((prev) => prev.filter((s) => s.id !== signal.id));
        setSelectedStructuredSignalIds((prev) => {
          if (!prev.has(signal.id)) return prev;
          const next = new Set(prev);
          next.delete(signal.id);
          return next;
        });
      } catch (err) {
        console.error("Apply structured finding error:", err);
        setStructuredFindingsError(err instanceof Error ? err.message : "Unable to apply structured finding(s).");
      } finally {
        setStructuredFindingsBusyId(null);
      }
    },
    // NOTE: isOngoing / assessmentType / markPersisted are intentionally
    // omitted here even though they're read in the body above -- they (and
    // the useAssessmentAutosave() call that produces markPersisted) are
    // declared further down in this component, so including them in this
    // array would evaluate a not-yet-initialized binding on first render
    // (TDZ ReferenceError). assessmentId/patientId/setAssessmentId ARE
    // declared earlier and are safe to depend on. markPersisted has a
    // permanently stable identity ([] deps in useAssessmentAutosave), and
    // isOngoing/assessmentType are only read on the rare "no assessmentId
    // yet" create-path, so omitting them from deps carries no meaningful
    // staleness risk in practice.
    [formData, assessmentId, patientId, setAssessmentId, structuredFieldProvenance]
  );

  const handleDismissStructuredSignal = useCallback(async (signal) => {
    setStructuredFindingsError("");
    setStructuredFindingsBusyId(signal.id);
    try {
      await reviewHarvestedSignalOffline(signal.id, "DISMISSED", "Reviewed — not applied by RN");
      setPendingStructuredSignals((prev) => prev.filter((s) => s.id !== signal.id));
      setSelectedStructuredSignalIds((prev) => {
        if (!prev.has(signal.id)) return prev;
        const next = new Set(prev);
        next.delete(signal.id);
        return next;
      });
    } catch (err) {
      console.error("Dismiss structured finding error:", err);
      setStructuredFindingsError(err instanceof Error ? err.message : "Unable to dismiss structured finding(s).");
    } finally {
      setStructuredFindingsBusyId(null);
    }
  }, []);

  // --- AI symptom_severity insertion (from a visit recording's note draft)
  // --------------------------------------------------------------------
  // Maps the 6 HOPE J2051 symptom_severity keys note_draft_service.py
  // produces (pain, shortnessOfBreath, nausea, vomiting, diarrhea,
  // constipation, each "0"-"3") onto the actual RNICA fields those same
  // symptoms are graded on elsewhere in this form (pain.painSeverityCategory
  // is numeric "0"-"3"; respiratory.sobSeverity and the GI fields use the
  // None/Mild/Moderate/Severe words) -- same blank-only-write +
  // durable-provenance-persist contract as handleApplyStructuredSignal
  // above, so an AI-suggested severity never overwrites an RN's own entry
  // and always survives refresh/logout/reconnect. Returns the list of
  // symptom keys actually written (for the calling VisitRecorderCard button
  // to show which suggestions were applied vs. already blocked by an
  // existing RN entry).
  const SEVERITY_WORD_BY_NUMBER = { "0": "None", "1": "Mild", "2": "Moderate", "3": "Severe" };
  const handleInsertAiSymptomSeverity = useCallback(
    async (symptomSeverity, sourceRecordingId) => {
      if (!symptomSeverity || Object.keys(symptomSeverity).length === 0) return [];

      const writes = []; // { section, path, value, symptomKey }
      const painVal = symptomSeverity.pain;
      if (painVal && !formData.pain?.painSeverityCategory) {
        writes.push({ section: "pain", path: "painSeverityCategory", value: painVal, symptomKey: "pain" });
      }
      const sobVal = symptomSeverity.shortnessOfBreath;
      if (sobVal && !formData.respiratory?.sobSeverity) {
        writes.push({
          section: "respiratory",
          path: "sobSeverity",
          value: SEVERITY_WORD_BY_NUMBER[sobVal] || sobVal,
          symptomKey: "shortnessOfBreath",
        });
      }
      for (const giKey of ["nausea", "vomiting", "diarrhea", "constipation"]) {
        const val = symptomSeverity[giKey];
        if (val && !formData.gastrointestinal?.[giKey]) {
          writes.push({
            section: "gastrointestinal",
            path: giKey,
            value: SEVERITY_WORD_BY_NUMBER[val] || val,
            symptomKey: giKey,
          });
        }
      }

      if (writes.length === 0) return [];

      let nextFormData = formData;
      for (const w of writes) {
        nextFormData = {
          ...nextFormData,
          [w.section]: { ...nextFormData[w.section], [w.path]: w.value },
        };
      }

      const provenanceEntries = writes.map((w) => ({
        section: w.section,
        path: w.path,
        value: w.value,
        concept_code: `AI_SYMPTOM_SEVERITY_${w.symptomKey.toUpperCase()}`,
        source_type: "TRANSCRIPT",
        source_excerpt: `AI-suggested HOPE J2051 severity from visit recording ${sourceRecordingId}`,
        recorded_at: new Date().toISOString(),
        confidence: null,
        signal_id: `visit_recording:${sourceRecordingId}`,
      }));
      const nextProvenance = [...structuredFieldProvenance, ...provenanceEntries];

      try {
        let persistedAssessmentId = assessmentId;
        if (persistedAssessmentId) {
          await api.updateRNICAAssessment(persistedAssessmentId, nextFormData, nextProvenance);
        } else {
          const result = await api.saveRNICAAssessment(
            patientId,
            nextFormData,
            isOngoing ? assessmentType : undefined
          );
          persistedAssessmentId = result.assessmentId;
          setAssessmentId(persistedAssessmentId);
        }
        markPersisted(nextFormData, persistedAssessmentId);
        setFormData(nextFormData);
        setStructuredFieldProvenance(nextProvenance);
        return writes.map((w) => w.symptomKey);
      } catch (err) {
        console.error("Insert AI symptom severity error:", err);
        setStructuredFindingsError(
          err instanceof Error ? err.message : "Unable to insert AI-suggested symptom severity."
        );
        return [];
      }
    },
    // Same TDZ caveat as handleApplyStructuredSignal above: isOngoing/
    // assessmentType/markPersisted are declared later in this component.
    [formData, assessmentId, patientId, setAssessmentId, structuredFieldProvenance]
  );

  // --- AI narrative-draft insertion (from a visit recording's note draft)
  // --------------------------------------------------------------------
  // Same blank-only-write + durable-provenance-persist contract as
  // handleInsertAiSymptomSeverity above: never overwrites an RN's own
  // Clinical Narrative entry. Returns true if the narrative was written,
  // false if a narrative already existed (so the calling VisitRecorderCard
  // button can tell the RN their existing text was preserved).
  const handleInsertAiNarrative = useCallback(
    async (narrativeText, sourceRecordingId) => {
      if (!narrativeText || !narrativeText.trim()) return false;
      if (formData.finalization?.clinicalNarrative) return false;

      const nextFormData = {
        ...formData,
        finalization: { ...formData.finalization, clinicalNarrative: narrativeText },
      };

      const provenanceEntry = {
        section: "finalization",
        path: "clinicalNarrative",
        value: narrativeText,
        concept_code: "AI_NOTE_DRAFT_NARRATIVE",
        source_type: "TRANSCRIPT",
        source_excerpt: `AI-generated note draft narrative from visit recording ${sourceRecordingId}`,
        recorded_at: new Date().toISOString(),
        confidence: null,
        signal_id: `visit_recording:${sourceRecordingId}`,
      };
      const nextProvenance = [...structuredFieldProvenance, provenanceEntry];

      try {
        let persistedAssessmentId = assessmentId;
        if (persistedAssessmentId) {
          await api.updateRNICAAssessment(persistedAssessmentId, nextFormData, nextProvenance);
        } else {
          const result = await api.saveRNICAAssessment(
            patientId,
            nextFormData,
            isOngoing ? assessmentType : undefined
          );
          persistedAssessmentId = result.assessmentId;
          setAssessmentId(persistedAssessmentId);
        }
        markPersisted(nextFormData, persistedAssessmentId);
        setFormData(nextFormData);
        setStructuredFieldProvenance(nextProvenance);
        return true;
      } catch (err) {
        console.error("Insert AI narrative draft error:", err);
        setStructuredFindingsError(
          err instanceof Error ? err.message : "Unable to insert AI-generated note draft into Clinical Narrative."
        );
        return false;
      }
    },
    [formData, assessmentId, patientId, setAssessmentId, structuredFieldProvenance]
  );

  // --- Bulk actions: "Apply All Non-Conflicting" / "Apply Selected" /
  // "Dismiss Selected" / "Dismiss All" -------------------------------------
  // Kept as a separate busy/loading flag from the per-signal
  // structuredFindingsBusyId so a bulk action's own button can show its own
  // pending state without disabling/relabeling every individual row.
  const [structuredFindingsBulkBusy, setStructuredFindingsBulkBusy] = useState(false);
  // RN-driven checkbox selection over the pending list, used by "Apply
  // Selected" / "Dismiss Selected" -- deliberately independent of "Apply
  // All Non-Conflicting" / "Dismiss All", which always act on the full
  // pending list regardless of what's checked.
  const [selectedStructuredSignalIds, setSelectedStructuredSignalIds] = useState(() => new Set());

  const toggleStructuredSignalSelected = useCallback((signalId) => {
    setSelectedStructuredSignalIds((prev) => {
      const next = new Set(prev);
      if (next.has(signalId)) next.delete(signalId);
      else next.add(signalId);
      return next;
    });
  }, []);

  // Shared core for "Apply All Non-Conflicting" and "Apply Selected" --
  // both run the exact same all-or-nothing-per-signal merge, just over a
  // different target list (the full pending list vs. only checked rows).
  const applyStructuredSignalsBulk = useCallback(
    async (targetSignals, reasonLabel) => {
      if (targetSignals.length === 0) {
        setStructuredFindingsError("No structured findings selected to apply.");
        return;
      }
      setStructuredFindingsError("");
      setStructuredFindingsBulkBusy(true);
      try {
        const {
          formData: nextFormData,
          appliedSignalIds,
          skippedSignalIds,
          appliedFieldsBySignal,
          skippedConflicts,
        } = applyAllNonConflicting(formData, targetSignals);

        if (appliedSignalIds.length === 0) {
          setStructuredFindingsError(
            skippedSignalIds.length > 0
              ? "Every selected signal has at least one conflicting field — review them individually below."
              : "No pending structured findings to apply."
          );
          return;
        }

        const provenanceEntries = [];
        for (const signal of targetSignals) {
          if (!appliedSignalIds.includes(signal.id)) continue;
          const applied = appliedFieldsBySignal[signal.id] || [];
          for (const f of applied) {
            provenanceEntries.push({
              section: f.section,
              path: f.path,
              value: f.value,
              concept_code: f.concept_code,
              source_type: signal.source_type,
              source_excerpt: signal.original_text_excerpt,
              recorded_at: signal.recorded_at,
              confidence: f.finding?.confidence,
              signal_id: signal.id,
            });
          }
        }
        const nextProvenance =
          provenanceEntries.length > 0 ? [...structuredFieldProvenance, ...provenanceEntries] : structuredFieldProvenance;

        // Persist the merged field values AND their provenance durably
        // BEFORE marking any signal "APPLIED". This must land before the
        // review-status write below -- otherwise a signal can be
        // permanently marked consumed while its fields (and the record of
        // why they were populated) only ever existed in this tab's memory,
        // silently lost on tab close/navigation/reload/logout (the exact
        // gap that produced the "57 populated in the UI, 21 populated in
        // the DB" discrepancy, and the analogous gap where provenance
        // vanished on refresh even though the fields themselves persisted).
        // If this save fails we throw here, before touching any visible
        // state or marking anything applied, so the RN can safely retry.
        let persistedAssessmentId = assessmentId;
        if (persistedAssessmentId) {
          await api.updateRNICAAssessment(persistedAssessmentId, nextFormData, nextProvenance);
        } else {
          const result = await api.saveRNICAAssessment(
            patientId,
            nextFormData,
            isOngoing ? assessmentType : undefined
          );
          persistedAssessmentId = result.assessmentId;
          setAssessmentId(persistedAssessmentId);
        }
        markPersisted(nextFormData, persistedAssessmentId);
        setFormData(nextFormData);

        if (provenanceEntries.length > 0) {
          setStructuredFieldProvenance(nextProvenance);
        }

        await batchReviewHarvestedSignalsOffline(appliedSignalIds, "APPLIED", { reason: reasonLabel });
        setPendingStructuredSignals((prev) => prev.filter((s) => !appliedSignalIds.includes(s.id)));
        setSelectedStructuredSignalIds((prev) => {
          if (prev.size === 0) return prev;
          const next = new Set(prev);
          for (const id of appliedSignalIds) next.delete(id);
          return next;
        });

        if (skippedConflicts.length > 0) {
          // A signal can land in `appliedSignalIds` (its non-conflicting
          // findings were written) while STILL producing conflicts for
          // its other bundled findings -- e.g. a new wound mention and an
          // unrelated already-set duplicate finding harvested together.
          // Those conflicts must always reach the RN review queue,
          // regardless of whether the signal itself ended up fully
          // skipped or partially applied.
          setStructuredFieldConflicts((prev) => [...prev, ...skippedConflicts]);
          setStructuredFindingsError(
            `Applied ${appliedSignalIds.length} signal(s). ${skippedConflicts.length} field(s) across ${skippedSignalIds.length} fully-conflicting signal(s) (plus any partially-applied signals) still need individual review.`
          );
        }
      } catch (err) {
        console.error(`${reasonLabel} error:`, err);
        setStructuredFindingsError(err instanceof Error ? err.message : "Unable to apply structured findings.");
      } finally {
        setStructuredFindingsBulkBusy(false);
      }
    },
    // See note on handleApplyStructuredSignal above: isOngoing /
    // assessmentType / markPersisted are declared later in this component
    // (after useAssessmentAutosave()), so they cannot appear in this array
    // without a TDZ ReferenceError on first render, even though they are
    // safely read in the body (deferred execution). markPersisted is
    // permanently stable-identity; isOngoing/assessmentType only affect the
    // rare "no assessmentId yet" create-path.
    [formData, assessmentId, patientId, setAssessmentId, structuredFieldProvenance]
  );

  const handleApplyAllNonConflicting = useCallback(() => {
    return applyStructuredSignalsBulk(pendingStructuredSignals, "Apply All Non-Conflicting");
  }, [applyStructuredSignalsBulk, pendingStructuredSignals]);

  const handleApplySelected = useCallback(() => {
    const selected = pendingStructuredSignals.filter((s) => selectedStructuredSignalIds.has(s.id));
    return applyStructuredSignalsBulk(selected, "Apply Selected");
  }, [applyStructuredSignalsBulk, pendingStructuredSignals, selectedStructuredSignalIds]);

  // Shared core for "Dismiss Selected" and "Dismiss All" -- both just
  // record every target signal's disposition as DISMISSED in one call.
  const dismissStructuredSignalsBulk = useCallback(async (targetSignals, reasonLabel) => {
    if (targetSignals.length === 0) {
      setStructuredFindingsError("No structured findings selected to dismiss.");
      return;
    }
    setStructuredFindingsError("");
    setStructuredFindingsBulkBusy(true);
    try {
      const ids = targetSignals.map((s) => s.id);
      await batchReviewHarvestedSignalsOffline(ids, "DISMISSED", { reason: reasonLabel });
      setPendingStructuredSignals((prev) => prev.filter((s) => !ids.includes(s.id)));
      setSelectedStructuredSignalIds((prev) => {
        if (prev.size === 0) return prev;
        const next = new Set(prev);
        for (const id of ids) next.delete(id);
        return next;
      });
    } catch (err) {
      console.error(`${reasonLabel} error:`, err);
      setStructuredFindingsError(err instanceof Error ? err.message : "Unable to dismiss structured findings.");
    } finally {
      setStructuredFindingsBulkBusy(false);
    }
  }, []);

  const handleDismissAllPending = useCallback(() => {
    return dismissStructuredSignalsBulk(pendingStructuredSignals, "Bulk dismissed by RN — reviewed, not applied (Dismiss All)");
  }, [dismissStructuredSignalsBulk, pendingStructuredSignals]);

  const handleDismissSelected = useCallback(() => {
    const selected = pendingStructuredSignals.filter((s) => selectedStructuredSignalIds.has(s.id));
    return dismissStructuredSignalsBulk(selected, "Bulk dismissed by RN — reviewed, not applied (Dismiss Selected)");
  }, [dismissStructuredSignalsBulk, pendingStructuredSignals, selectedStructuredSignalIds]);

  const isOngoing = mode === "ongoing";
  const [assessmentType, setAssessmentType] = useState("update");
  const isUpdateAssessment = isOngoing && assessmentType === "update";
  const assessmentUiProfile = useMemo(() => ({
    hideAdvancedCarePlanning: isUpdateAssessment,
    hideAdmissionsOrder: isUpdateAssessment,
    hideSpiritualHopeFields: isUpdateAssessment,
  }), [isUpdateAssessment]);
  const autosavePatientId = resolvedPatientId || patientId || "";
  // Admission Action Center (Phase A) — global drawer, reachable from every
  // section via the persistent footer button. No draft loss / navigation:
  // opening/closing this never touches `formData` or `activeSection`.
  const [actionCenterOpen, setActionCenterOpen] = useState(false);

  const userEditedRef = useRef(false);
  const { markPersisted, resetAutosaveTracking } = useAssessmentAutosave({
    formData,
    assessmentId,
    setAssessmentId,
    locked,
    saving,
    saveFn: api.saveRNICAAssessment,
    updateFn: api.updateRNICAAssessment,
    patientId: autosavePatientId,
    intervalMs: 30000,
    userEditedRef,
  });
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  const routes = useMemo(() => {
    const orderedRoutes = workspacePilot ? PILOT_ROUTES : LEGACY_ROUTES;
    // SFV (Symptom Follow-Up Visit) is its own separate, distinctly
    // documented visit that HOPE requires within 2 calendar days of the RN
    // Initial Comprehensive Assessment -- it is never filled out inside an
    // *ongoing/recert* RNICA visit. It IS part of the canonical 30-module
    // initial-assessment navigation (module 20), so it must only be
    // filtered when this is genuinely an ongoing-assessment visit, not
    // unconditionally (see rnIcaClinicalNavigation.js's
    // validateRnIcaClinicalNavigation, which checks the same explicit
    // isOngoing flag rather than back-inferring it from route count).
    return orderedRoutes.filter((route) => {
      if (isOngoing && route.key === "sfv") return false;
      if (assessmentUiProfile.hideAdmissionsOrder && UPDATE_HIDDEN_ROUTE_KEYS.has(route.key)) return false;
      return true;
    });
  }, [assessmentUiProfile.hideAdmissionsOrder, workspacePilot, isOngoing]);
  const sidebarConfigItems = useMemo(() => {
    // Keep in lock-step with `routes` above: SFV is only excluded from
    // sidebar/lookup metadata for genuinely-ongoing (recert) visits.
    const items = SIDEBAR_CONFIG.filter((item) => {
      if (isOngoing && item.key === "sfv") return false;
      if (isUpdateAssessment && UPDATE_HIDDEN_SIDEBAR_KEYS.has(item.key)) return false;
      return true;
    });
    return isOngoing ? items.map((item) => ({ ...item, hope: [] })) : items;
  }, [isOngoing, isUpdateAssessment]);

  // Default every section to collapsed on load so the RN sees one page of
  // short, tap-to-open rows instead of all 28 sections expanded at once
  // requiring constant scrolling. Runs once per mount, before the RN has
  // manually toggled anything — jumpToSection (sidebar nav) still expands
  // + scrolls to whichever section is clicked afterward, and once opened a
  // section stays open until the RN collapses it again.
  const didInitCollapse = useRef(false);
  useEffect(() => {
    if (didInitCollapse.current || routes.length === 0) return;
    didInitCollapse.current = true;
    setCollapsedSections(new Set(routes.map((route) => route.key).filter((key) => key !== activeSection)));
  }, [routes, activeSection]);

  useEffect(() => {
    userEditedRef.current = false;
    resetAutosaveTracking({ markCurrentAsPersisted: true });
  }, [existingAssessmentId, patientId, resetAutosaveTracking, resolvedPatientId]);

  useEffect(() => {
    const nextId = patientId || getActivePatientId();
    if (nextId) {
      setResolvedPatientId(nextId);
      setActivePatientId(nextId);
      return;
    }

    let mounted = true;
    fetchCensusWorkspace()
      .then(({ patients }) => {
        if (!mounted) return;
        const firstPatient = patients?.[0];
        if (firstPatient?.patient_id) {
          setActivePatientId(firstPatient.patient_id);
          setResolvedPatientId(firstPatient.patient_id);
        }
      })
      .catch((error) => {
        console.warn("Unable to auto-select patient for RN ICA:", error);
      });

    return () => {
      mounted = false;
    };
  }, [patientId]);

  useEffect(() => {
    const activeId = resolvedPatientId || patientId;
    if (!activeId) {
      setPatientSummary(null);
      setPatientSummaryError("");
      return;
    }

    let mounted = true;
    setPatientSummaryError("");
    fetchPatientSummary(activeId)
      .then((summary) => {
        if (mounted) {
          setPatientSummary(summary);
        }
      })
      .catch((error) => {
        console.error("Failed to load RN ICA patient summary:", error);
        if (mounted) {
          setPatientSummary(null);
          setPatientSummaryError(error instanceof Error ? error.message : "Unable to load patient summary.");
        }
      });

    return () => {
      mounted = false;
    };
  }, [resolvedPatientId, patientId]);

  // Visit meta — seed discipline/staff/care level for logistics + payroll tracking.
  useEffect(() => {
    const currentUser = getCurrentUser();
    setFormData((prev) => ({
      ...prev,
      visitMeta: {
        ...prev.visitMeta,
        discipline: currentUser?.role || prev.visitMeta.discipline || "RN",
        enteredBy: prev.visitMeta.enteredBy || currentUser?.full_name || "",
        staffAssigned: prev.visitMeta.staffAssigned || currentUser?.full_name || "",
        careLevel: prev.visitMeta.careLevel || patientSummary?.patient?.acuity_state || "",
      },
    }));
  }, [patientSummary]);

  useEffect(() => {
    const activeId = resolvedPatientId || patientId;
    if (!activeId) {
      setFacesheetData(null);
      setFacesheetError("");
      setPerformanceHistory([]);
      return;
    }

    let mounted = true;
    setFacesheetError("");
    fetchFacesheet(activeId)
      .then((data) => {
        if (mounted) setFacesheetData(data);
      })
      .catch((error) => {
        console.error("Failed to load facesheet for RN ICA Section 1:", error);
        if (mounted) {
          setFacesheetData(null);
          setFacesheetError(error instanceof Error ? error.message : "Unable to load facesheet.");
        }
      });
    fetchPerformanceHistory(activeId)
      .then((res) => {
        if (mounted) setPerformanceHistory(res?.history || []);
      })
      .catch((error) => {
        console.error("Failed to load performance history for RN ICA Section 1:", error);
        if (mounted) setPerformanceHistory([]);
      });

    return () => {
      mounted = false;
    };
  }, [resolvedPatientId, patientId]);

  useEffect(() => {
    if (!patientSummary?.patient || assessmentId) {
      return;
    }

    setFormData((prev) => {
      const next = JSON.parse(JSON.stringify(prev));
      const patient = patientSummary.patient;
      const fullName = (patient.full_name || "").trim();
      const nameParts = fullName ? fullName.split(/\s+/) : [];
      const firstName = nameParts[0] || "";
      const lastName = nameParts.length > 1 ? nameParts.slice(1).join(" ") : "";

      if (!next.demographics.firstName && firstName) {
        next.demographics.firstName = firstName;
      }
      if (!next.demographics.lastName && lastName) {
        next.demographics.lastName = lastName;
      }
      if (!next.diagnoses.primaryDiagnosis.description && patient.primary_diagnosis) {
        next.diagnoses.primaryDiagnosis.description = patient.primary_diagnosis;
      }
      if (!next.admissionsOrder.levelOfCare.level) {
        next.admissionsOrder.levelOfCare.level = patient.acuity_state === "ROUTINE" ? "Routine Care" : patient.acuity_state || "Routine Care";
      }
      if (!next.admissionsOrder.levelOfCare.effectiveDate) {
        next.admissionsOrder.levelOfCare.effectiveDate = patient.hospice_election_date || patient.soc_date || new Date().toISOString().slice(0, 10);
      }

      return next;
    });
  }, [patientSummary, assessmentId]);

  // Fill demographics/diagnosis identity fields from the same authoritative
  // Facesheet data Section 1 already displays read-only, whenever it becomes
  // available. Unlike the patientSummary prefill above, this deliberately
  // runs on every facesheet load (not just "new assessment, no assessmentId
  // yet") -- an already-in-progress assessment that still shows these as
  // blank/required (e.g. because it was started before the facesheet was
  // completed, or before this prefill existed) should self-heal the next
  // time its Facesheet data loads, rather than staying permanently blank.
  // Every field write is guarded by "only if currently empty" so an RN's
  // own entry (including one that deliberately differs from the facesheet)
  // is never overwritten -- this only fills gaps, never replaces values.
  useEffect(() => {
    if (!facesheetData || !assessmentLoaded) {
      return;
    }
    const identity = facesheetData.identity || {};
    const primaryDx = facesheetData.clinical?.active_primary_diagnosis || null;

    setFormData((prev) => {
      let changed = false;
      const next = JSON.parse(JSON.stringify(prev));
      const d = next.demographics;

      if (!d.dob && identity.dob) {
        d.dob = identity.dob;
        changed = true;
      }
      if (!d.gender && identity.gender) {
        d.gender = identity.gender;
        changed = true;
      }
      if ((!d.race || d.race.length === 0) && identity.race) {
        d.race = [identity.race];
        changed = true;
      }
      if ((!d.ethnicity || d.ethnicity.length === 0) && identity.ethnicity) {
        d.ethnicity = [identity.ethnicity];
        changed = true;
      }
      if (!d.preferredLanguage && identity.language) {
        d.preferredLanguage = identity.language;
        changed = true;
      }
      // HOPE A0550 (Patient ZIP Code): same blank-only hydration pattern as
      // the fields above -- Face Sheet's mailing address is the only place
      // ZIP is captured today; RNICA's own address.zip field (used for
      // HOPE A0550 export) never had this fallback wired, unlike its
      // neighboring demographic fields.
      if (!d.address?.zip && facesheetData.address?.zip) {
        d.address = { ...(d.address || {}), zip: facesheetData.address.zip };
        changed = true;
      }
      if (!d.religion && identity.religion) {
        d.religion = identity.religion;
        changed = true;
      }
      if (!d.maritalStatus && identity.marital_status) {
        d.maritalStatus = identity.marital_status;
        changed = true;
      }
      if (!d.phone && identity.phone) {
        d.phone = identity.phone;
        changed = true;
      }

      const dx = next.diagnoses.primaryDiagnosis;
      if (!dx.icd10 && primaryDx?.icd10_code) {
        dx.icd10 = primaryDx.icd10_code;
        changed = true;
      }
      if (!dx.description && primaryDx?.description) {
        dx.description = primaryDx.description;
        changed = true;
      }

      return changed ? next : prev;
    });
  }, [facesheetData, assessmentLoaded]);

  const refreshIntelligence = useCallback(async (currentAssessmentId) => {
    if (!currentAssessmentId) {
      setIntelligence(null);
      setIntelligenceError("");
      return;
    }
    setIntelligenceLoading(true);
    try {
      const data = await api.getRNICAIntelligence(currentAssessmentId);
      setIntelligence(data);
      setIntelligenceError("");
    } catch (err) {
      console.error("RN ICA intelligence load error:", err);
      setIntelligence(null);
      setIntelligenceError(err instanceof Error ? err.message : "Unable to load RN ICA intelligence.");
    } finally {
      setIntelligenceLoading(false);
    }
  }, []);

  const refreshFinalizationReadiness = useCallback(async (currentAssessmentId) => {
    if (!currentAssessmentId) {
      setFinalizationReadiness(null);
      return;
    }
    try {
      const data = await getRnicaFinalizationReadiness(currentAssessmentId);
      setFinalizationReadiness(data);
    } catch (err) {
      console.error("RN ICA finalization readiness load error:", err);
      // Fail closed: an unreadable readiness check must not silently enable Lock.
      setFinalizationReadiness({ ready: false, checks: {} });
    }
  }, []);

  useEffect(() => {
    if (assessmentId) {
      refreshFinalizationReadiness(assessmentId);
    }
  }, [assessmentId, refreshFinalizationReadiness]);

  // Load existing assessment
  useEffect(() => {
    const activePatientId = resolvedPatientId || patientId;
    if (!existingAssessmentId && !activePatientId) {
      setAssessmentLoaded(true);
      return undefined;
    }

    let mounted = true;
    setAssessmentLoaded(false);
    const loadAssessment = existingAssessmentId
      ? api.getRNICAAssessment(existingAssessmentId)
      : api.getRNICAAssessmentByPatient(activePatientId, isOngoing ? assessmentType : undefined);

    loadAssessment
      .then((data) => {
        if (!mounted) return null;
        if (!data?.assessmentId) {
          setAssessmentId(null);
          setLocked(false);
          setLockedAt(null);
          setFormData(JSON.parse(JSON.stringify(INITIAL_FORM)));
          setIntelligence(null);
          setIntelligenceError("");
          setStructuredFieldProvenance([]);
          return null;
        }
        if (data.formData) {
          const merged = deepMergeFormData(INITIAL_FORM, data.formData);
          setFormData(merged);
          markPersisted(merged, data.assessmentId || existingAssessmentId);
        }
        // Rehydrate applied-field provenance from the server so an RN can
        // still see why a field was populated after a refresh, logout, or
        // reconnect -- not only within the same browser session the Apply
        // happened in.
        setStructuredFieldProvenance(Array.isArray(data.fieldProvenance) ? data.fieldProvenance : []);
        setLocked(!!data.locked);
        setLockedAt(data.lockedAt || null);
        return data;
      })
      .then((data) => {
        if (!mounted || !data?.assessmentId) return null;
        setAssessmentId(data.assessmentId);
        return refreshIntelligence(data.assessmentId);
      })
      .catch((err) => {
        if (!mounted) return;
        console.error("Failed to load assessment:", err);
        setPageError(err instanceof Error ? err.message : "Unable to load RN ICA assessment.");
      })
      .finally(() => {
        if (mounted) {
          setAssessmentLoaded(true);
        }
      });

    return () => {
      mounted = false;
    };
  }, [assessmentType, existingAssessmentId, isOngoing, markPersisted, patientId, refreshIntelligence, resolvedPatientId]);

  useEffect(() => {
    if (assessmentId) {
      refreshIntelligence(assessmentId);
    }
  }, [assessmentId, refreshIntelligence]);

  // Auto-validate on change
  useEffect(() => {
    setValidation(validateRNICA(formData, mode, assessmentType));
  }, [assessmentType, formData, mode]);

  useEffect(() => {
    onFormDataChange?.(formData);
  }, [formData, onFormDataChange]);

  // Deep update helper
  const updateField = useCallback((section, path, value) => {
    userEditedRef.current = true;
    setFormData((prev) => {
      const next = { ...prev };
      next[section] = setNestedValue(prev[section], path, value);
      return next;
    });
    setSaveStatus(null);
  }, []);

  // Live single-source derivation of all HOPE J2051 A-H Symptom Impact
  // ratings from the clinical sections where each symptom is actually
  // assessed (owner design review 2026-09-25: "Document symptom severity
  // once. Store symptom severity once. Reuse everywhere." -- Symptom
  // Impact Screening no longer accepts independent RN entry for these
  // eight items; it is now a read-only summary, so this effect always
  // keeps `symptomImpact` in sync with its true source instead of only
  // filling once while blank).
  //   A. Pain              <- Pain Assessment: painSeverityCategory (0-3)
  //   B. Shortness of Breath <- Respiratory: sobSeverity (None-Severe)
  //   C. Anxiety           <- Neuro/Mental Status: symptomsDemeanor checklist
  //   D. Nausea            <- Gastrointestinal: nausea (None-Severe)
  //   E. Vomiting          <- Gastrointestinal: vomiting (None-Severe)
  //   F. Diarrhea          <- Gastrointestinal: diarrhea (None-Severe)
  //   G. Constipation      <- Gastrointestinal: constipation (None-Severe)
  //   H. Agitation         <- Neuro/Mental Status: symptomsDemeanor checklist
  useEffect(() => {
    const severityMap = { None: "0", Mild: "1", Moderate: "2", Severe: "3" };
    const painSeverity = formData.pain?.painSeverityCategory;
    const demeanor = formData.neurological?.symptomsDemeanor || [];
    // symptomsDemeanor is a presence checklist, not a graded scale -- its
    // absence is read as "0 - None reported" so the summary never shows a
    // stale severity after the checkbox is unchecked.
    const derived = {
      pain: ["0", "1", "2", "3"].includes(String(painSeverity)) ? String(painSeverity) : "",
      shortnessOfBreath: severityMap[formData.respiratory?.sobSeverity] ?? "",
      anxiety: demeanor.includes("Anxiety") ? "1" : "0",
      nausea: severityMap[formData.gastrointestinal?.nausea] ?? "",
      vomiting: severityMap[formData.gastrointestinal?.vomiting] ?? "",
      diarrhea: severityMap[formData.gastrointestinal?.diarrhea] ?? "",
      constipation: severityMap[formData.gastrointestinal?.constipation] ?? "",
      agitation: demeanor.includes("Agitation") ? "1" : "0",
    };

    setFormData((prev) => {
      const current = prev.symptomImpact || {};
      let next = current;
      let changed = false;
      for (const key of Object.keys(derived)) {
        if (current[key] !== derived[key]) {
          next = { ...next, [key]: derived[key] };
          changed = true;
        }
      }
      if (!changed) return prev;
      return { ...prev, symptomImpact: next };
    });
  }, [
    formData.pain?.painSeverityCategory,
    formData.respiratory?.sobSeverity,
    formData.neurological?.symptomsDemeanor,
    formData.gastrointestinal?.nausea,
    formData.gastrointestinal?.vomiting,
    formData.gastrointestinal?.diarrhea,
    formData.gastrointestinal?.constipation,
  ]);

  // RNICA (RN Initial Comprehensive Assessment) is a one-time document --
  // it is never "updated" or "recertified" through this same form. Saving
  // before it is locked is just progressing the single initial assessment,
  // so the label never changes to "update"/"recert" wording while
  // mode="ica". mode="ongoing" is a distinct follow-up encounter (not the
  // RNICA itself) and keeps its own label.
  const saveButtonLabel = isOngoing
    ? (assessmentType === "recert" ? "Recertification Assessment" : "Update Assessment")
    : "Initial Comprehensive RN Assessment";

  // Save / Update
  const handleSave = useCallback(async () => {
    setSaving(true);
    setPageError("");
    try {
      let activeAssessmentId = assessmentId;
      if (assessmentId) {
        await api.updateRNICAAssessment(assessmentId, formData);
      } else {
        const result = await api.saveRNICAAssessment(
          patientId,
          formData,
          isOngoing ? assessmentType : undefined
        );
        activeAssessmentId = result.assessmentId;
        setAssessmentId(activeAssessmentId);
      }
      await refreshIntelligence(activeAssessmentId);
      await refreshFinalizationReadiness(activeAssessmentId);
      markPersisted(formData, activeAssessmentId);
      setSaveStatus("saved");
    } catch (err) {
      console.error("Save error:", err);
      setSaveStatus("error");
      setPageError(err instanceof Error ? err.message : "Unable to save RN ICA assessment.");
    } finally {
      setSaving(false);
    }
  }, [assessmentId, formData, markPersisted, patientId, refreshIntelligence, refreshFinalizationReadiness, isOngoing, assessmentType]);

  // Lock
  const handleLock = useCallback(async () => {
    if (!assessmentId) return;
    const v = validateRNICA(formData, mode, assessmentType);
    if (!v.isValid) {
      alert("Cannot lock: there are validation errors. Please complete all required fields.");
      return;
    }
    if (finalizationReadiness && !finalizationReadiness.ready) {
      const failedChecks = Object.entries(finalizationReadiness.checks || {}).filter(([, check]) => !check.ready);
      const lines = failedChecks.map(([, check]) => `• ${check.label}: ${check.message}`);
      const firstMappedSection = failedChecks
        .map(([key]) => FINALIZATION_CHECK_SECTION_MAP[key])
        .find(Boolean);
      alert(
        `Cannot lock this assessment yet — the following must be completed first:\n\n${lines.join("\n")}`
      );
      if (firstMappedSection) setActiveSection(firstMappedSection);
      return;
    }
    setPageError("");
    setSaving(true);
    let persistedBeforeLock = false;
    try {
      await api.updateRNICAAssessment(assessmentId, formData);
      persistedBeforeLock = true;
      markPersisted(formData, assessmentId);
      setSaveStatus("saved");
      const result = await api.lockRNICAAssessment(assessmentId);
      setLocked(true);
      setLockedAt(result?.lockedAt || null);
      await Promise.all([
        refreshIntelligence(assessmentId),
        refreshFinalizationReadiness(assessmentId),
      ]);
    } catch (err) {
      console.error("Lock error:", err);
      setSaveStatus(persistedBeforeLock ? "saved" : "error");
      setPageError(err instanceof Error ? err.message : "Unable to lock RN ICA assessment.");
    } finally {
      setSaving(false);
    }
  }, [assessmentId, formData, markPersisted, mode, finalizationReadiness, refreshFinalizationReadiness, refreshIntelligence, setActiveSection]);

  // Delete — only reachable for an in-progress DRAFT (never signed).
  // Once locked, the backend rejects deletion at 423 so a permanent
  // clinical record can never be removed outright, only amended.
  const handleDelete = useCallback(async () => {
    if (!assessmentId) return;
    const confirmed = window.confirm(
      "Delete this RN ICA assessment? This cannot be undone. Only unsigned drafts can be deleted."
    );
    if (!confirmed) return;
    setSaving(true);
    setPageError("");
    try {
      await api.deleteRNICAAssessment(assessmentId);
      const pid = resolvedPatientId || patientId;
      clearActivePatientId();
      if (pid) {
        navigate(`/portal?patientId=${pid}`);
      } else {
        navigate("/portal");
      }
    } catch (err) {
      console.error("Delete error:", err);
      setPageError(err instanceof Error ? err.message : "Unable to delete RN ICA assessment.");
    } finally {
      setSaving(false);
    }
  }, [assessmentId, resolvedPatientId, patientId, navigate]);

  // Section completion tracker
  const sectionCompletionStates = useMemo(() => {
    const states = {};
    routes.forEach((route) => {
      let sectionData = route.completionPath
        ? getValueByPath(formData[route.formSection], route.completionPath)
        : formData[route.formSection];
      let initialSectionData = route.completionPath
        ? getValueByPath(INITIAL_FORM[route.formSection], route.completionPath)
        : INITIAL_FORM[route.formSection];
      if (route.key === "demographics" && workspacePilot) {
        const { pcg: _pcg, advancedCarePlanning: _planning, ...patientDemographics } = sectionData;
        const { pcg: _initialPcg, advancedCarePlanning: _initialPlanning, ...initialPatientDemographics } = initialSectionData;
        sectionData = patientDemographics;
        initialSectionData = initialPatientDemographics;
      }
      if (sectionData) {
        states[route.key] = getSectionCompletionState(sectionData, initialSectionData);
      }
    });
    return states;
  }, [formData, routes, workspacePilot]);

  // Kept for existing callers that only need the complete/not-complete
  // list (e.g. the top-level "8 / 27" progress bar) -- now driven by the
  // same meaningful-documentation threshold as the per-section badges,
  // instead of the old "any field changed" check.
  const completedSections = useMemo(
    () => Object.keys(sectionCompletionStates).filter((key) => sectionCompletionStates[key].status === "complete"),
    [sectionCompletionStates]
  );
  const inProgressSections = useMemo(
    () => Object.keys(sectionCompletionStates).filter((key) => sectionCompletionStates[key].status === "in_progress"),
    [sectionCompletionStates]
  );

  // Which formData sections have at least one pending (not yet applied or
  // dismissed) structured finding aimed at them -- computed WITHOUT
  // requiring an apply pass, so this stays accurate the instant a signal
  // arrives, not only after the RN clicks Apply. Keyed by formSection
  // (e.g. "pain"), since that's what CONCEPT_REGISTRY writes target, not
  // by the sidebar route key.
  const pendingReviewFormSections = useMemo(() => {
    const counts = {};
    for (const signal of pendingStructuredSignals) {
      const sections = getPendingFindingTargetSections(signal.structured_findings || []);
      sections.forEach((section) => {
        counts[section] = (counts[section] || 0) + 1;
      });
    }
    return counts;
  }, [pendingStructuredSignals]);

  // Four-stage section status (per the RNICA Phase 4 certification
  // requirement): Not Started / Partially Populated / Ready for RN Review
  // / Complete. "Ready for RN Review" takes priority over a documentation
  // ratio that would otherwise read "Complete" -- new AI-suggested
  // findings still awaiting Apply/Dismiss mean the section isn't truly
  // settled yet, even if it already has enough manually-documented fields
  // to clear the completion threshold.
  const sectionStatuses = useMemo(() => {
    const statuses = {};
    routes.forEach((route) => {
      const completion = sectionCompletionStates[route.key];
      const pendingCount = pendingReviewFormSections[route.formSection] || 0;
      let status;
      if (pendingCount > 0) {
        status = "ready_for_review";
      } else if (!completion || completion.status === "not_started") {
        status = "not_started";
      } else if (completion.status === "complete") {
        status = "complete";
      } else {
        status = "partially_populated";
      }
      statuses[route.key] = { status, pendingCount, completion };
    });
    return statuses;
  }, [routes, sectionCompletionStates, pendingReviewFormSections]);

  const SECTION_STATUS_LABELS = {
    not_started: { label: "Not Started", color: "gray" },
    partially_populated: { label: "Partially Populated", color: "warning" },
    ready_for_review: { label: "Ready for RN Review", color: "teal" },
    complete: { label: "Complete", color: "success" },
  };

  useEffect(() => {
    if (!routes.some((route) => route.key === activeSection)) {
      setActiveSection(routes[0]?.key || "demographics");
    }
  }, [activeSection, routes]);

  // Current route
  const currentRoute = routes.find((r) => r.key === activeSection);
  const currentSectionData = formData[currentRoute?.formSection];
  const sidebarConfig = sidebarConfigItems.find((s) => s.key === activeSection);
  const sfvStatus = useMemo(() => getSfvStatus(formData, latestSfvRequirement), [formData, latestSfvRequirement]);
  // SECTION 7 — HOPE Admission harvest/completion-status. RN ICA's job here is
  // only to harvest the answers and show completion status / missing HOPE
  // sources (never to generate, export, or submit the HOPE Admission record
  // itself). A1400 (Payer Information) is Facesheet-sourced, not an RN ICA
  // field, so it isn't part of SIDEBAR_CONFIG's per-section hope arrays and
  // is intentionally excluded from this section-level completion check.
  const hopeAdmissionPatient = useMemo(() => ({
    primaryPayerType: patientSummary?.patient?.primary_payer_type || "",
    secondaryPayerType: patientSummary?.patient?.secondary_payer_type || "",
  }), [patientSummary]);
  const hopeAdmissionStatus = useMemo(
    () => getHopeAdmissionStatus(formData, hopeAdmissionPatient, {}, sidebarConfigItems),
    [formData, hopeAdmissionPatient, sidebarConfigItems]
  );

  // Navigate — move focus + scroll to the next/previous section (all
  // sections stay mounted; this no longer swaps content).
  const goNext = () => {
    const idx = routes.findIndex((r) => r.key === activeSection);
    if (idx < routes.length - 1) jumpToSection(routes[idx + 1].key);
  };
  const goPrev = () => {
    const idx = routes.findIndex((r) => r.key === activeSection);
    if (idx > 0) jumpToSection(routes[idx - 1].key);
  };

  // Render ALL sections as one continuous, collapsible page (replaces the
  // old one-section-at-a-time swap). Completed sections default to a
  // one-line summary; incomplete/flagged ones stay open. `content-visibility`
  // lets the browser skip layout/paint for whatever isn't on screen, so
  // keeping every section mounted stays cheap even with 28 of them.
  const renderAllSections = () => routes.map((route) => {
    const isDemo = route.key === "demographics";
    const config = SECTION_CONFIGS[route.formSection];
    const sectionData = formData[route.formSection];
    const open = isSectionOpen(route.key);
    const statusEntry = sectionStatuses[route.key] || { status: "not_started", pendingCount: 0 };
    const statusMeta = SECTION_STATUS_LABELS[statusEntry.status];
    const statusColor = COLORS[statusMeta.color] || COLORS.gray;
    const cfg = sidebarConfigItems.find((s) => s.key === route.key);

    return (
      <div
        key={route.key}
        id={route.key}
        ref={(el) => { sectionRefs.current[route.key] = el; }}
        style={{ marginBottom: 14, border: `1px solid ${COLORS.border}`, borderRadius: 10, overflow: "hidden" }}
      >
        <div
          onClick={() => toggleSection(route.key)}
          style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "10px 16px", cursor: "pointer", userSelect: "none",
            background: activeSection === route.key ? COLORS.tealTint || COLORS.bg : COLORS.bg,
            borderBottom: open ? `1px solid ${COLORS.border}` : "none",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 12, color: COLORS.gray, width: 14, display: "inline-block" }}>{open ? "▾" : "▸"}</span>
            <span style={{ fontSize: 14, fontWeight: 700 }}>{cfg?.label || route.key}</span>
            {cfg?.cdphRequired && <span style={{ fontSize: 10, fontWeight: 700, color: COLORS.teal }}>CDPH</span>}
            {statusEntry.status === "complete" && <span style={{ fontSize: 11, fontWeight: 700, color: statusColor }}>&#10003; Complete</span>}
            {statusEntry.status === "ready_for_review" && (
              <span style={{ fontSize: 11, fontWeight: 700, color: statusColor }}>
                &#9679; Ready for RN Review{statusEntry.pendingCount > 1 ? ` (${statusEntry.pendingCount})` : ""}
              </span>
            )}
            {statusEntry.status === "partially_populated" && <span style={{ fontSize: 11, fontWeight: 700, color: statusColor }}>&#9679; Partially Populated</span>}
          </div>
          {!open && (
            <span style={{ fontSize: 11, color: COLORS.gray }}>
              {statusEntry.status === "complete"
                ? "Documented — tap to review"
                : statusEntry.status === "ready_for_review"
                  ? "AI findings awaiting review — tap to review"
                  : statusEntry.status === "partially_populated"
                    ? "Partially documented — tap to continue"
                    : "Not started — tap to document"}
            </span>
          )}
        </div>
        {open && (
          <div style={{ padding: 16, contentVisibility: "auto", containIntrinsicSize: "600px" }}>
            {isDemo
              ? renderDemographics(formData.demographics, updateField, COLORS, styles, "all", assessmentUiProfile)
              : config && sectionData
                ? renderGenericSection(route.formSection, sectionData, updateField, config, formData.demographics, formData, COLORS, styles, patientId, assessmentId, locked, false, onNavigateToSection, assessmentUiProfile)
                : <div style={styles.card}><p style={{ color: COLORS.gray }}>Section "{route.key}" — content loading...</p></div>}
          </div>
        )}
      </div>
    );
  });

  // `forceVisibleKeys` lets a screen show a legacy section's content
  // continuously (no click/tab required) even when it is not the globally
  // "active" section -- used by Evidence & Intake to keep Vitals visible
  // inline per owner direction ("vitals are part of continuous clinical
  // context, not a tab"). Every other caller passes nothing and behavior is
  // unchanged (only the active section renders visible).
  const renderWorkspaceSections = (forceVisibleKeys = []) => routes.map((route) => {
    const config = SECTION_CONFIGS[route.formSection];
    const sectionData = formData[route.formSection];
    const isDemographicsModule = ["demographics", "caregiverAssessment", "advancedCarePlanning"].includes(route.key);
    const content = isDemographicsModule
      ? renderDemographics(formData.demographics, updateField, COLORS, styles, route.key, assessmentUiProfile)
      : config && sectionData
        ? renderGenericSection(
            route.formSection,
            sectionData,
            updateField,
            config,
            formData.demographics,
            formData,
            COLORS,
            styles,
            patientId,
            assessmentId,
            locked,
            true,
            onNavigateToSection,
            assessmentUiProfile,
          )
        : <div style={styles.card}><p style={{ color: COLORS.gray }}>Section "{route.key}" — content loading...</p></div>;

    const visible = route.key === activeSection || forceVisibleKeys.includes(route.key);
    return (
      <div key={route.key} hidden={!visible} aria-hidden={!visible}>
        {content}
      </div>
    );
  });

  // ── Body Systems screen (pilot-only) ──────────────────────────────
  // Purely mechanical "is anything here documented" scan used only to
  // badge a body system Reviewed/Not Started in the compact accordion
  // below -- never a clinical judgment, never invents a finding. Treats
  // empty string/false/[]/{}/undefined/null as "not documented"; any
  // other value (including "0", itself a charted answer) counts.
  const sectionHasDocumentedData = (value) => {
    if (value === null || value === undefined || value === "") return false;
    if (typeof value === "boolean") return value === true;
    if (Array.isArray(value)) return value.some((item) => sectionHasDocumentedData(item));
    if (typeof value === "object") return Object.values(value).some((v) => sectionHasDocumentedData(v));
    return true;
  };

  // One compact accordion item per body system (all 10, always rendered
  // together instead of one-at-a-time) -- reuses the exact same
  // config/sectionData/renderGenericSection call as every other route, so
  // fields, HOPE mappings, and Add/View POC controls are byte-for-byte the
  // same as legacy/non-grouped rendering. Presentation-only grouping.
  // Bounded Compatibility Increment (2026-09-28) Section 5/AC-03 -- the
  // shared `sectionHasDocumentedData` boolean above still drives the
  // Reviewed/Not-started badge for every OTHER body system unchanged.
  // Neurological alone gets a richer status because it now has an
  // Overview Gate that can honestly report "review required" (Unable to
  // Assess) instead of collapsing every state into the same two-value
  // badge. This intentionally does not touch or generalize the shared
  // helper -- Cardiovascular and the rest are untouched.
  const bodySystemsAccordionItems = useMemo(() => {
    return RNICA_BODY_SYSTEM_MODULES.map((module) => {
      const route = routes.find((r) => r.key === module.key);
      if (!route) return null;
      const config = SECTION_CONFIGS[route.formSection];
      const sectionData = formData[route.formSection];
      const meta = sidebarConfigItems.find((s) => s.key === module.key);
      const neuroStatus = module.key === "neurological" ? computeNeurologicalWorkflowStatus(sectionData || {}) : null;
      const cardiovascularStatus = module.key === "cardiovascular" ? computeCardiovascularWorkflowStatus(sectionData || {}, formData.respiratory) : null;
      const workflowStatus = neuroStatus || cardiovascularStatus;
      return {
        key: module.key,
        label: meta?.label || module.label,
        icon: meta?.icon || "🩺",
        reviewed: workflowStatus ? workflowStatus.code === "ready_for_review" : sectionHasDocumentedData(sectionData),
        statusLabel: workflowStatus?.label,
        statusVariant: workflowStatus?.variant,
        content: config && sectionData
          ? renderGenericSection(route.formSection, sectionData, updateField, config, formData.demographics, formData, COLORS, styles, patientId, assessmentId, locked, true, onNavigateToSection, assessmentUiProfile)
          : null,
      };
    }).filter(Boolean);
  }, [routes, formData, sidebarConfigItems, COLORS, styles, patientId, assessmentId, locked, onNavigateToSection, assessmentUiProfile]);

  // Structured Findings — a deterministic, plain-language restatement of
  // ALREADY-DOCUMENTED body-system fields only (owner directive: "only
  // include findings already documented... do not generate/infer/create
  // findings"). Every line below reads one specific, already-existing
  // field and only appears when that field has a real charted value; none
  // of these paths are new fields, and nothing is derived/predicted.
  const bodySystemsStructuredFindings = useMemo(() => {
    return [
      "neurological", "respiratory", "cardiovascular", "skin",
      "gastrointestinal", "genitourinary", "nutrition", "endocrine", "infection",
    ].flatMap((key) => computeBodySystemFindings(key, formData?.[key]));
  }, [formData]);

  if (workspacePilot) {
    const ownSecondaryDiagnoses = (formData.diagnoses.secondaryDiagnoses || [])
      .map((diagnosis) => `${diagnosis.description || formatIcd10Code(diagnosis.icd10) || ""}`.trim())
      .filter(Boolean)
      .join(", ");
    // Fallback to the Face Sheet's already-documented secondary diagnoses
    // when RNICA's own Diagnoses section hasn't been filled in yet (e.g.
    // early in the assessment). Read-only display fallback only -- never
    // written back into `formData.diagnoses`, so it can never mask or
    // conflict with the RN's own entry once made.
    const facesheetSecondaryDiagnoses = (facesheetData?.clinical?.active_secondary_diagnoses || [])
      .map((dx) => dx.display_name || dx.diagnosis_description || "")
      .filter(Boolean)
      .join(", ") || facesheetData?.clinical?.secondary_diagnoses || "";
    const secondaryDiagnoses = ownSecondaryDiagnoses || facesheetSecondaryDiagnoses;
    // Latest RNICA/Recert performance entry (same source + ordering already
    // used by the Face Sheet's "PPS (auto)" display) -- fallback for the
    // context bar only when the current assessment's own Performance Status
    // section hasn't been filled in yet.
    const latestPerformance = performanceHistory?.[0] || null;
    const verifiedComorbidities = Object.entries(formData.diagnoses.hopeComorbidities || {})
      .filter(([, selected]) => selected === true)
      .map(([key]) => key)
      .join(", ");
    const commandRoutes = routes.map((route) => ({
      ...route,
      label: route.label || sidebarConfigItems.find((item) => item.key === route.key)?.label || route.nav,
      regulator: isOngoing && route.regulator === "HOPE" ? undefined : route.regulator,
    }));

    const patientAge = calculateAgeFromDob(facesheetData?.identity?.dob || formData.demographics.dob);
    const pcg = formData.demographics.pcg || {};

    return (
      <AssessmentModeContext.Provider value={mode}>
        <RNICACommandWorkspace
          patient={{
            id: resolvedPatientId,
            name: patientSummary?.patient?.full_name || (resolvedPatientId ? "Loading patient..." : "No patient selected"),
            mrn: patientSummary?.patient?.mrn || "",
            primaryDiagnosis: formData.diagnoses.primaryDiagnosis.description || patientSummary?.patient?.primary_diagnosis || "",
            secondaryDiagnoses,
            comorbidities: verifiedComorbidities,
            priorIssues: patientSummary
              ? `${patientSummary.incident_summary.total} incident(s), ${patientSummary.communication_summary.total} communication item(s)`
              : "Patient record summary loading",
            // Additive Patient Story context (Phase B reference screen).
            // Every value is read from a field already owned/edited by its
            // authoritative RNICA screen (or the facesheet) -- nothing new
            // is captured or persisted here.
            age: patientAge,
            sex: formData.demographics.gender || "",
            admissionDate: facesheetData?.service_dates?.soc_date || "",
            attendingPhysician: patientSummary?.patient?.attending_physician_name || "",
            currentPps: formData.performanceStatus?.pps || latestPerformance?.pps || "",
            assessmentStage: isOngoing ? (assessmentType === "recert" ? "Recertification" : "Update assessment") : "Initial admission",
            whyHospiceNarrative: formData.diagnoses.clinicalNarrative || "",
            recentHospitalization: formData.diagnoses.recentHospitalizations || "",
            functionalDeclineNarrative: formData.performanceStatus?.functionalDeclineNotes || "",
            // Read-only reflection of the existing `vitals` module's own
            // state -- nothing new is captured here. Used by the persistent
            // clinical context bar so vitals are visible on every screen
            // without navigating to the Vitals section.
            vitals: {
              temperature: formData.vitals?.temperature || "",
              temperatureUnit: formData.vitals?.temperatureUnit || "F",
              pulse: formData.vitals?.pulse || "",
              respirations: formData.vitals?.respirations || "",
              bpSystolic: formData.vitals?.bloodPressure?.systolic || "",
              bpDiastolic: formData.vitals?.bloodPressure?.diastolic || "",
              oxygenSaturation: formData.vitals?.oxygenSaturation || "",
              weight: formData.vitals?.weight || latestPerformance?.weight || "",
            },
            caregiver: {
              name: pcg.name || "",
              relationship: pcg.relationship || "",
              noPcg: pcg.noPcg === true,
              willingToProvideCare: pcg.willingToProvideCare,
              anxietyLevel: pcg.anxietyLevel || "",
              concerns: pcg.pcgConcerns || "",
            },
            // Administrative Demographics -- a small, independent HOPE
            // concept (A0215 Site of Service, A1805 Admitted From, A1005
            // Ethnicity, A1010 Race, A1110 Language/Interpreter, A1905
            // Living Arrangement, A1910 Availability of Assistance). Per
            // owner direction this is NOT a "Patient Information" screen
            // and must never be bundled with identity/contact fields
            // (name, DOB, phone, address, emergency contact, religion,
            // marital status, military service) -- those remain Face
            // Sheet's exclusively. Raw values are passed (not joined
            // display strings) so HOPE Administrative Review can render
            // them as its own compact, editable grid via `onUpdateField`.
            administrativeDemographics: {
              preferredLanguage: formData.demographics.preferredLanguage || "",
              needsInterpreter: formData.demographics.needsInterpreter,
              interpreterOffered: formData.demographics.interpreterOffered,
              understandsParticipatesInCare: formData.demographics.understandsParticipatesInCare,
              specialWishStatus: formData.demographics.specialWishStatus,
              specialEventDesire: formData.demographics.specialEventDesire || "",
              specialWishFollowUpDiscipline: formData.demographics.specialWishFollowUpDiscipline || "",
              specialWishReviewStatus: formData.demographics.specialWishReviewStatus || "",
              ethnicity: formData.demographics.ethnicity || [],
              race: formData.demographics.race || [],
              raceInformationSource: formData.demographics.raceInformationSource || "",
              raceInformationSourceOther: formData.demographics.raceInformationSourceOther || "",
              ethnicityInformationSource: formData.demographics.ethnicityInformationSource || "",
              ethnicityInformationSourceOther: formData.demographics.ethnicityInformationSourceOther || "",
              siteOfService: formData.livingSituation?.siteOfService || "",
              admittedFrom: formData.livingSituation?.admittedFrom || "",
              livingArrangement: formData.livingSituation?.livingArrangement || "",
              availabilityOfAssistance: formData.livingSituation?.availabilityOfAssistance || "",
            },
          }}
          routes={commandRoutes}
          formSections={Object.keys(formData)}
          activeSection={activeSection}
          completedSections={completedSections}
          validation={validation}
          locked={locked}
          saving={saving}
          saveStatus={saveStatus}
          intelligence={intelligence}
          isOngoingAssessment={isOngoing}
          renderWorkspaceSections={renderWorkspaceSections}
          bodySystemsAccordionItems={bodySystemsAccordionItems}
          bodySystemsStructuredFindings={bodySystemsStructuredFindings}
          // Lets Evidence & Intake's Administrative Demographics section
          // (Language/Interpreter/Ethnicity/Race/Living Arrangement/
          // Availability of Assistance) write directly back into RNICA's
          // own `demographics`/`livingSituation` form state -- the exact
          // same update path every other RNICA field already uses.
          onUpdateField={updateField}
          visitRecorder={(
            <VisitRecorderCard
              patientId={resolvedPatientId || patientId}
              assessmentId={assessmentId}
              assessmentType={isOngoing ? "RN_RECERT" : "RNICA"}
              COLORS={COLORS}
              styles={styles}
              // Withheld until the initial "load existing assessment" fetch
              // resolves (see the effect that sets assessmentLoaded above).
              // Otherwise VisitRecorderCard's auto-insert-on-ready effect can
              // race that fetch: it sees assessmentId still at its initial
              // null and creates a brand-new duplicate DRAFT instead of
              // updating the real assessment that was about to load a
              // moment later. Passing undefined here (not a no-op wrapper)
              // is what matters: the auto-insert effect's own
              // `if (!onInsertNarrative) return` guard skips it entirely
              // without marking the recording as attempted, so it fires for
              // real once assessmentLoaded flips true and this prop is
              // supplied.
              onInsertSymptomSeverity={assessmentLoaded ? handleInsertAiSymptomSeverity : undefined}
              onInsertNarrative={assessmentLoaded ? handleInsertAiNarrative : undefined}
            />
          )}
          alerts={(
            <>
              {(patientSummaryError || pageError) && (
                <div style={styles.warningBox}>
                  {patientSummaryError && <div>Patient summary: {patientSummaryError}</div>}
                  {pageError && <div>RN ICA: {pageError}</div>}
                </div>
              )}
              {!isOngoing && sfvStatus.required && (
                <div style={styles.warningBox}>
                  <strong>SFV required:</strong> Moderate or severe symptom impact detected for {sfvStatus.triggeredSymptoms.join(", ")}.
                  {sfvStatus.dueDate ? ` Due ${sfvStatus.dueDate}.` : " Due within 2 calendar days of screening."}
                </div>
              )}
            </>
          )}
          onSelect={setActiveSection}
          onSave={handleSave}
          onLock={handleLock}
          onPrevious={goPrev}
          onNext={goNext}
          onExitPilot={onExitWorkspacePilot}
          canLock={Boolean(assessmentId)}
        />
      </AssessmentModeContext.Provider>
    );
  }

  return (
    <AssessmentModeContext.Provider value={mode}>
      <div style={styles.page}>
      {/* ── Patient Banner ── */}
      <div style={styles.banner}>
        <div>
          <div style={styles.bannerName}>{patientSummary?.patient?.full_name || (resolvedPatientId ? "Loading patient..." : "No patient selected")}</div>
          <div style={styles.bannerMeta}>
            {patientSummary
              ? `MRN: ${patientSummary.patient.mrn} | ${patientSummary.patient.primary_diagnosis}`
              : resolvedPatientId
                ? "Loading patient details..."
                : "Select a patient to view chart details"}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 13, fontWeight: 600 }}>RN ICA</div>
          <div style={styles.bannerMeta}>
            {(() => {
              const attending = patientSummary?.patient?.attending_physician_name;
              const careTeam = patientSummary?.care_team || [];
              const rnAssignment =
                careTeam.find((member) => member.discipline === "RN" && member.primary) ||
                careTeam.find((member) => member.discipline === "RN");
              const assignedRn = rnAssignment?.staff_name;
              if (!attending && !assignedRn) {
                return "Attending physician / assigned RN not yet on file";
              }
              return [attending, assignedRn].filter(Boolean).join(" | ");
            })()}
          </div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 8, marginTop: 6 }}>
            <button
              type="button"
              onClick={() => {
                clearActivePatientId();
                navigate("/portal");
              }}
              title="Return to the patient dashboard"
              style={{
                fontSize: 11, fontWeight: 700, padding: "5px 10px", borderRadius: 6,
                border: `1px solid ${COLORS.border}`, background: COLORS.bg, color: COLORS.dark, cursor: "pointer",
              }}
            >
              ← Dashboard
            </button>
            <button
              type="button"
              onClick={() => {
                const pid = resolvedPatientId || patientId;
                if (pid) window.open(`/plan-of-care?patientId=${pid}`, "_blank", "noopener");
              }}
              title="Opens the patient's current Plan of Care in a new tab — does not lose your assessment progress"
              style={{
                fontSize: 11, fontWeight: 700, padding: "5px 10px", borderRadius: 6,
                border: `1px solid ${COLORS.border}`, background: COLORS.bg, color: COLORS.dark, cursor: "pointer",
              }}
            >
              View Plan of Care ↗
            </button>
            <div style={{
              ...styles.statusBadge,
              background: locked ? COLORS.success : COLORS.warning,
              color: COLORS.white,
            }}>
              {locked ? "LOCKED" : "IN PROGRESS"}
            </div>
          </div>
        </div>
      </div>

      {/* ── Visit Meta — logistics/payroll tracking (type of visit, reason, time in/out, staff, discipline, care level) ── */}
      <div style={{ padding: "0 24px 12px" }}>
        <div style={styles.card}>
          <div style={styles.cardTitle}>Visit Details</div>
          <div style={styles.sectionSubtitle}>Visit logistics for agency scheduling and payroll tracking</div>
          <div style={styles.fieldsGrid}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Correction</label>
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: COLORS.dark }}>
                <input type="checkbox" checked={formData.visitMeta.correction} onChange={(e) => updateField("visitMeta", "correction", e.target.checked)} />
                Correction
              </label>
            </div>
            <FormSelect label="Type of Visit" value={formData.visitMeta.typeOfVisit} onChange={(v) => updateField("visitMeta", "typeOfVisit", v)} options={["In-Person", "Telephone", "Video"]} />
            <FormSelect label="Visit" value={formData.visitMeta.visitKind} onChange={(v) => updateField("visitMeta", "visitKind", v)} options={["Scheduled", "Unscheduled", "Other"]} />
            <FormSelect label="Reason for Visit" value={formData.visitMeta.reasonForVisit} onChange={(v) => updateField("visitMeta", "reasonForVisit", v)} options={REASON_FOR_VISIT_OPTIONS} />
            <FormInput label="Visit Date" type="date" value={formData.visitMeta.visitDate} onChange={(v) => updateField("visitMeta", "visitDate", v)} />
            {formData.visitMeta.visitKind === "Other" && (
              <FormInput label="Visit specify" value={formData.visitMeta.visitKindSpecify} onChange={(v) => updateField("visitMeta", "visitKindSpecify", v)} />
            )}
            <FormInput label="Time In" type="time" value={formData.visitMeta.timeIn} onChange={(v) => updateField("visitMeta", "timeIn", v)} />
            <FormInput label="Time Out" type="time" value={formData.visitMeta.timeOut} onChange={(v) => updateField("visitMeta", "timeOut", v)} />
            <FormInput label="Duration (h:m)" value={formData.visitMeta.duration} onChange={(v) => updateField("visitMeta", "duration", v)} placeholder="1h 15m" />
            <FormInput label="Entered By" value={formData.visitMeta.enteredBy} onChange={(v) => updateField("visitMeta", "enteredBy", v)} />
            <FormInput label="Staff Assigned" value={formData.visitMeta.staffAssigned} onChange={(v) => updateField("visitMeta", "staffAssigned", v)} />
            <div style={styles.formGroup}>
              <label style={styles.label}>Discipline</label>
              <input value={formData.visitMeta.discipline} readOnly style={{ ...styles.input, background: COLORS.bg }} />
            </div>
            <FormSelect label="Care Level" value={formData.visitMeta.careLevel} onChange={(v) => updateField("visitMeta", "careLevel", v)} options={CARE_LEVEL_OPTIONS} />
          </div>
        </div>
      </div>

      <Section1Snapshot
        colors={COLORS}
        patientSummary={patientSummary}
        facesheet={facesheetData}
        facesheetError={facesheetError}
        performanceHistory={performanceHistory}
        locked={locked}
        saving={saving}
        resolvedPatientId={resolvedPatientId}
        patientIdProp={patientId}
      />

      {(patientSummaryError || pageError) && (
        <div style={styles.warningBox}>
          {patientSummaryError && <div>Patient summary: {patientSummaryError}</div>}
          {pageError && <div>RN ICA: {pageError}</div>}
        </div>
      )}

      {/* ── Workspace ── */}
      {isOngoing && (
        <div style={{ padding: "0 24px 16px" }}>
          <AssessmentTypeToggle value={assessmentType} onChange={setAssessmentType} />
        </div>
      )}

      <div style={styles.workspace}>
        <PatientContextSidebar
          patientId={patientSummary?.patient?.mrn || patientId || resolvedPatientId || "No MRN on file"}
          patientName={patientSummary?.patient?.full_name || (resolvedPatientId ? "Loading patient..." : "No patient selected")}
          disciplineLabel="RN ICA"
          activeSection={activeSection}
          patientOverview={
            patientSummary
              ? {
                  diagnosis: patientSummary.patient.primary_diagnosis,
                  painSummary: `${patientSummary.recent_visits.length} recent visit(s) and ${patientSummary.communication_summary.total} communication entry(ies) on file.`,
                  primaryProvider: patientSummary.care_team[0]?.staff_name || "Unassigned",
                  hnpStatus: `${patientSummary.patient.admission_status} / ${patientSummary.patient.acuity_state}`,
                  lastVisit: patientSummary.recent_visits[0]
                    ? `${patientSummary.recent_visits[0].visit_type} — ${patientSummary.recent_visits[0].visit_datetime || "—"}`
                    : "No visits recorded",
                  disciplineHistory: [
                    `${patientSummary.recent_visits.length} recent visit(s)`,
                    `${patientSummary.communication_summary.total} communication entry(ies)`,
                    `${patientSummary.incident_summary.total} incident report(s)`,
                    `${patientSummary.care_team.length} active care team assignment(s)`,
                  ],
                  careTeam: patientSummary.care_team.map((item) => item.discipline),
                }
              : {
                  // No hardcoded/mock patient identity data here: showing a
                  // fake diagnosis, provider name, or care team while the
                  // real patient summary hasn't loaded (or failed to load)
                  // could be mistaken for genuine PHI. Every field below is
                  // an explicit, neutral "not yet available" placeholder.
                  diagnosis: resolvedPatientId ? "Loading…" : "No patient selected",
                  painSummary: resolvedPatientId
                    ? "Patient overview is loading."
                    : "Select a patient to view the clinical overview.",
                  primaryProvider: "—",
                  hnpStatus: "—",
                  lastVisit: "—",
                  disciplineHistory: [],
                  careTeam: [],
                }
          }
          sections={sidebarConfigItems.map((item) => ({
            key: item.key,
            label: item.label,
            meta: item.cdphRequired ? "CDPH" : !isOngoing && item.hope?.length ? "HOPE" : undefined,
          }))}
          onSelect={(key) => {
            const match = sidebarConfigItems.find((item) => item.key === key);
            if (!match) return;

            if (match.parent) {
              jumpToSection(match.parent);
              setTimeout(() => {
                const el = document.getElementById(match.scrollTarget);
                if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
              }, 100);
              return;
            }

            jumpToSection(key);
          }}
        />

        {/* ── Main Content ── */}
        <div style={styles.mainArea}>
          <div style={styles.content}>
            <VisitRecorderCard
              patientId={patientId}
              assessmentId={assessmentId}
              assessmentType={isOngoing ? "RN_RECERT" : "RNICA"}
              COLORS={COLORS}
              styles={styles}
              // See the matching comment on the other VisitRecorderCard
              // usage above: withheld until assessmentLoaded to prevent a
              // race that creates a duplicate DRAFT assessment.
              onInsertSymptomSeverity={assessmentLoaded ? handleInsertAiSymptomSeverity : undefined}
              onInsertNarrative={assessmentLoaded ? handleInsertAiNarrative : undefined}
            />
            {!isOngoing && sfvStatus.required && (
              <div style={{ ...styles.warningBox, marginBottom: 16, border: "1px solid rgba(234, 88, 12, 0.28)", background: COLORS.warningBoxBg }}>
                <div style={{ fontWeight: 800, marginBottom: 6 }}>SFV Required</div>
                <div>
                  Moderate or Severe symptom impact detected for {sfvStatus.triggeredSymptoms.join(", ")}.
                  {sfvStatus.dueDate ? ` In-person SFV is due within 2 calendar days of screening by ${sfvStatus.dueDate.slice(5, 7)}/${sfvStatus.dueDate.slice(8, 10)}/${sfvStatus.dueDate.slice(0, 4)}.` : " In-person SFV is due within 2 calendar days of screening."}
                </div>
                <div style={{ marginTop: 6 }}>
                  Complete J2052 after the follow-up visit. J2053 may then be documented by an RN or LPN/LVN.
                </div>
              </div>
            )}
            {!isOngoing && hopeAdmissionStatus.totalSections > 0 && (
              <div style={{
                ...styles.warningBox,
                marginBottom: 16,
                border: `1px solid ${hopeAdmissionStatus.allComplete ? "rgba(16,185,129,0.35)" : "rgba(234, 88, 12, 0.28)"}`,
                background: hopeAdmissionStatus.allComplete ? COLORS.successBoxBg : COLORS.warningBoxBg,
              }}>
                <div style={{ fontWeight: 800, marginBottom: 6 }}>
                  HOPE Admission Completion: {hopeAdmissionStatus.completedCount} / {hopeAdmissionStatus.totalSections} sections ({hopeAdmissionStatus.percentComplete}%)
                </div>
                {hopeAdmissionStatus.allComplete ? (
                  <div>All HOPE Admission sources harvested from this assessment are complete.</div>
                ) : (
                  <div>
                    Missing HOPE sources: {hopeAdmissionStatus.missingSections.map((section) => `${section.label} (${section.missingCodes.join(", ")})`).join("; ")}.
                  </div>
                )}
              </div>
            )}
            {renderAllSections()}
          </div>

          {/* ── Right Validation Panel ── */}
          <div style={styles.rightPanel}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>Validation</div>

            {/* Completion */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, color: COLORS.gray, marginBottom: 4 }}>Completion</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: COLORS.teal }}>
                {completedSections.length} / {routes.length}
              </div>
              <div style={{
                height: 6, borderRadius: 3, background: COLORS.border, marginTop: 8,
              }}>
                <div style={{
                  height: "100%", borderRadius: 3, background: COLORS.teal,
                  width: `${(completedSections.length / routes.length) * 100}%`,
                  transition: "width 0.3s",
                }} />
              </div>
            </div>

            {/* SFV (Symptom Follow-up Visit) Status — always visible in the
                right panel, independent of scroll position or which section
                is active, since SFV is a required separate visit the RN
                must not lose track of. Only tracked during the initial ICA;
                a recert cannot trigger a new SFV requirement. */}
            {!isOngoing && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, color: COLORS.gray, marginBottom: 4 }}>SFV Status</div>
                <div style={{
                  padding: 8,
                  borderRadius: 6,
                  fontSize: 11.5,
                  fontWeight: 700,
                  background: sfvStatus.completed
                    ? COLORS.successBoxBg
                    : sfvStatus.required
                      ? COLORS.warningBoxBg
                      : COLORS.bg,
                  color: sfvStatus.completed ? COLORS.success : sfvStatus.required ? COLORS.warning : COLORS.gray,
                  border: `1px solid ${sfvStatus.completed ? "rgba(16,185,129,0.35)" : sfvStatus.required ? "rgba(234,88,12,0.28)" : COLORS.border}`,
                }}>
                  {sfvStatus.statusLabel}
                </div>
                {sfvStatus.required && !sfvStatus.completed && sfvStatus.dueDate && (
                  <div style={{ fontSize: 11, color: COLORS.gray, marginTop: 4 }}>
                    Due {sfvStatus.dueDate.slice(5, 7)}/{sfvStatus.dueDate.slice(8, 10)}/{sfvStatus.dueDate.slice(0, 4)}
                  </div>
                )}
                {sfvStatus.required && (
                  <div style={{ fontSize: 10, color: COLORS.gray, marginTop: 4 }}>
                    Triggered by: {sfvStatus.triggeredSymptoms.join(", ")}
                  </div>
                )}

                {/* J2051 A-H checklist — lets the RN see at a glance which
                    Symptom Impact items are still blank when documenting
                    manually, without hunting through the Symptom Impact
                    section itself. Auto-derived values (from Pain,
                    Respiratory, GI, Neuro sections) show here too. */}
                <div style={{ marginTop: 8 }}>
                  {SYMPTOM_IMPACT_CHECKLIST.map(({ key, label }) => {
                    const value = formData.symptomImpact?.[key];
                    const filled = value !== undefined && value !== null && value !== "";
                    return (
                      <div
                        key={key}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          fontSize: 10.5,
                          padding: "3px 0",
                          color: filled ? COLORS.dark : COLORS.gray,
                        }}
                      >
                        <span>{filled ? "✔" : "○"} {label}</span>
                        <span style={{ fontWeight: 700 }}>
                          {filled ? SYMPTOM_SEVERITY_LABEL[value] || value : "Not documented"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* HOPE Items for current section */}
            {!isOngoing && sidebarConfig?.hope?.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, color: COLORS.gray, marginBottom: 8 }}>HOPE Items</div>
                {sidebarConfig.hope.map((code) => (
                  <div key={code} style={{ marginBottom: 4 }}><HopeTag code={code} /></div>
                ))}
              </div>
            )}

            {/* Errors */}
            {Object.keys(validation.errors).length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, color: COLORS.error, fontWeight: 700, marginBottom: 8 }}>
                  Errors ({Object.keys(validation.errors).length})
                </div>
                {Object.entries(validation.errors).map(([key, msg]) => (
                  <div key={key} style={{ fontSize: 11, color: COLORS.error, marginBottom: 4, padding: 4, background: COLORS.sfvTagBg, borderRadius: 4 }}>
                    {msg}
                  </div>
                ))}
              </div>
            )}

            {/* Warnings */}
            {Object.keys(validation.warnings).length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, color: COLORS.warning, fontWeight: 700, marginBottom: 8 }}>
                  Warnings ({Object.keys(validation.warnings).length})
                </div>
                {Object.entries(validation.warnings).slice(0, 5).map(([key, msg]) => (
                  <div key={key} style={{ fontSize: 11, color: COLORS.warning, marginBottom: 4, padding: 4, background: COLORS.amberTagBg, borderRadius: 4 }}>
                    {msg}
                  </div>
                ))}
                {Object.keys(validation.warnings).length > 5 && (
                  <div style={{ fontSize: 11, color: COLORS.gray }}>
                    +{Object.keys(validation.warnings).length - 5} more...
                  </div>
                )}
              </div>
            )}

            {/* Save Status */}
            {saveStatus === "saved" && (
              <div style={styles.successBox}>Assessment saved successfully</div>
            )}
            {saveStatus === "error" && (
              <div style={styles.warningBox}>Save failed — please try again</div>
            )}

            <div style={{ marginTop: 18, paddingTop: 12, borderTop: `1px solid ${COLORS.border}` }}>
              <div style={{ fontSize: 12, color: COLORS.gray, fontWeight: 700, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                RN ICA Intelligence
              </div>

              {intelligenceLoading && (
                <div style={{ fontSize: 12, color: COLORS.gray }}>Evaluating RN ICA clinical signals…</div>
              )}

              {intelligenceError && (
                <div style={{ ...styles.warningBox, marginTop: 0 }}>
                  RN ICA intelligence: {intelligenceError}
                </div>
              )}

              {!intelligenceLoading && intelligence && (
                <>
                  <div style={{ fontSize: 12, color: COLORS.dark, marginBottom: 8 }}>
                    Priority: <strong style={{ textTransform: "uppercase" }}>{intelligence.summary?.overall_priority || "low"}</strong>
                  </div>
                  <div style={{ fontSize: 11, color: COLORS.gray, marginBottom: 10 }}>
                    {intelligence.summary?.finding_count || 0} findings • {intelligence.summary?.recommendation_count || 0} recommendations • {intelligence.summary?.missing_evidence_count || 0} missing inputs
                  </div>

                  {(intelligence.findings || []).slice(0, 3).map((finding, idx) => (
                    <div key={`${finding.category}-${idx}`} style={{ marginBottom: 8, padding: 8, borderRadius: 8, background: finding.severity === "high" ? COLORS.sfvTagBg : finding.severity === "moderate" ? COLORS.amberTagBg : COLORS.bg, border: `1px solid ${finding.severity === "high" ? COLORS.error : finding.severity === "moderate" ? COLORS.warning : COLORS.border}` }}>
                      <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 4 }}>{finding.title}</div>
                      <div style={{ fontSize: 10, lineHeight: 1.4, color: COLORS.dark }}>{finding.details}</div>
                    </div>
                  ))}

                  {(intelligence.recommendations || []).slice(0, 3).map((rec, idx) => (
                    <div key={`${rec.title}-${idx}`} style={{ fontSize: 10, lineHeight: 1.5, color: COLORS.gray, marginTop: 6 }}>
                      • {rec.title}
                    </div>
                  ))}
                </>
              )}

              {!intelligenceLoading && !intelligence && assessmentId && (
                <div style={{ fontSize: 11, color: COLORS.gray }}>No intelligence available yet. Save the assessment to generate the clinical signal summary.</div>
              )}
            </div>

            {/* ──────────────────────────────────────────────────────────
                Structured Findings — dedicated application-layer panel.
                Deliberately separate from the "RN ICA Intelligence" box
                above (which is narrative/rule-based signal summary only).
                Surfaces evidence-harvested StructuredFinding objects
                (review_status === "NEW") pulled from H&P, referral
                packets, uploaded documents, and speech-to-documentation
                transcripts, and lets the RN Apply (populate blank RNICA
                fields, preserving provenance, never overwriting existing
                RN-entered data) or Dismiss (mark reviewed, not applied)
                each one. Never auto-applies anything on its own.
               ────────────────────────────────────────────────────────── */}
            <div style={{ marginTop: 18, paddingTop: 12, borderTop: `1px solid ${COLORS.border}` }}>
              <div style={{ fontSize: 12, color: COLORS.gray, fontWeight: 700, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Structured Findings — Pending Review
              </div>

              {structuredFindingsAnalytics && structuredFindingsAnalytics.total_signals > 0 && (
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 16,
                    fontSize: 11,
                    color: COLORS.gray,
                    marginBottom: 10,
                    padding: "6px 10px",
                    borderRadius: 6,
                    background: COLORS.bg,
                    border: `1px solid ${COLORS.border}`,
                  }}
                >
                  <span>
                    <strong style={{ color: COLORS.dark }}>{structuredFindingsAnalytics.total_signals}</strong> total findings
                  </span>
                  <span>
                    <strong style={{ color: COLORS.dark }}>{structuredFindingsAnalytics.by_status?.APPLIED ?? 0}</strong> applied
                  </span>
                  <span>
                    <strong style={{ color: COLORS.dark }}>{structuredFindingsAnalytics.by_status?.DISMISSED ?? 0}</strong> dismissed
                  </span>
                  <span>
                    <strong style={{ color: COLORS.dark }}>{structuredFindingsAnalytics.by_status?.NEW ?? 0}</strong> pending
                  </span>
                  <span>
                    Application rate:{" "}
                    <strong style={{ color: COLORS.dark }}>
                      {structuredFindingsAnalytics.application_rate === null || structuredFindingsAnalytics.application_rate === undefined
                        ? "—"
                        : `${Math.round(structuredFindingsAnalytics.application_rate * 100)}%`}
                    </strong>
                  </span>
                </div>
              )}

              {rnProductivityMetrics && rnProductivityMetrics.manual_entries_avoided > 0 && (
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 16,
                    fontSize: 11,
                    color: COLORS.gray,
                    marginBottom: 10,
                    padding: "6px 10px",
                    borderRadius: 6,
                    background: COLORS.bg,
                    border: `1px solid ${COLORS.border}`,
                  }}
                >
                  <span>
                    <strong style={{ color: COLORS.dark }}>{rnProductivityMetrics.manual_entries_avoided}</strong> manual entries
                    avoided
                  </span>
                  <span>
                    <strong style={{ color: COLORS.dark }}>{rnProductivityMetrics.fields_populated}</strong> RNICA fields populated
                  </span>
                </div>
              )}

              {pendingStructuredSignals.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
                  <button
                    type="button"
                    onClick={handleApplyAllNonConflicting}
                    disabled={structuredFindingsBulkBusy || structuredFindingsBusyId !== null}
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: "6px 12px",
                      borderRadius: 6,
                      border: "none",
                      background: COLORS.teal,
                      color: "#fff",
                      cursor: structuredFindingsBulkBusy || structuredFindingsBusyId !== null ? "default" : "pointer",
                      opacity: structuredFindingsBulkBusy || structuredFindingsBusyId !== null ? 0.6 : 1,
                    }}
                  >
                    {structuredFindingsBulkBusy ? "Applying…" : `Apply All Non-Conflicting (${pendingStructuredSignals.length})`}
                  </button>
                  <button
                    type="button"
                    onClick={handleApplySelected}
                    disabled={structuredFindingsBulkBusy || structuredFindingsBusyId !== null || selectedStructuredSignalIds.size === 0}
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: "6px 12px",
                      borderRadius: 6,
                      border: `1px solid ${COLORS.teal}`,
                      background: "transparent",
                      color: COLORS.teal,
                      cursor:
                        structuredFindingsBulkBusy || structuredFindingsBusyId !== null || selectedStructuredSignalIds.size === 0
                          ? "default"
                          : "pointer",
                      opacity:
                        structuredFindingsBulkBusy || structuredFindingsBusyId !== null || selectedStructuredSignalIds.size === 0
                          ? 0.5
                          : 1,
                    }}
                  >
                    {`Apply Selected (${selectedStructuredSignalIds.size})`}
                  </button>
                  <button
                    type="button"
                    onClick={handleDismissSelected}
                    disabled={structuredFindingsBulkBusy || structuredFindingsBusyId !== null || selectedStructuredSignalIds.size === 0}
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: "6px 12px",
                      borderRadius: 6,
                      border: `1px solid ${COLORS.border}`,
                      background: "transparent",
                      color: COLORS.gray,
                      cursor:
                        structuredFindingsBulkBusy || structuredFindingsBusyId !== null || selectedStructuredSignalIds.size === 0
                          ? "default"
                          : "pointer",
                      opacity:
                        structuredFindingsBulkBusy || structuredFindingsBusyId !== null || selectedStructuredSignalIds.size === 0
                          ? 0.5
                          : 1,
                    }}
                  >
                    {`Dismiss Selected (${selectedStructuredSignalIds.size})`}
                  </button>
                  <button
                    type="button"
                    onClick={handleDismissAllPending}
                    disabled={structuredFindingsBulkBusy || structuredFindingsBusyId !== null}
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: "6px 12px",
                      borderRadius: 6,
                      border: `1px solid ${COLORS.border}`,
                      background: "transparent",
                      color: COLORS.gray,
                      cursor: structuredFindingsBulkBusy || structuredFindingsBusyId !== null ? "default" : "pointer",
                      opacity: structuredFindingsBulkBusy || structuredFindingsBusyId !== null ? 0.6 : 1,
                    }}
                  >
                    {`Dismiss All (${pendingStructuredSignals.length})`}
                  </button>
                </div>
              )}


              {structuredFindingsError && (
                <div style={{ ...styles.warningBox, marginTop: 0, marginBottom: 8 }}>{structuredFindingsError}</div>
              )}

              {pendingStructuredSignals.length === 0 && (
                <div style={{ fontSize: 11, color: COLORS.gray }}>
                  No pending structured findings from H&amp;P, referral, uploaded documents, or transcripts.
                </div>
              )}

              {pendingStructuredSignals.map((signal) => (
                <div
                  key={signal.id}
                  style={{ marginBottom: 10, padding: 10, borderRadius: 8, background: COLORS.bg, border: `1px solid ${COLORS.border}` }}
                >
                  <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
                    <input
                      type="checkbox"
                      checked={selectedStructuredSignalIds.has(signal.id)}
                      onChange={() => toggleStructuredSignalSelected(signal.id)}
                      disabled={structuredFindingsBulkBusy || structuredFindingsBusyId === signal.id}
                      aria-label={`Select structured finding from ${signal.source_type}`}
                      style={{ marginTop: 2 }}
                    />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 10, color: COLORS.gray, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                        {signal.source_type}{signal.recorded_at ? ` • ${new Date(signal.recorded_at).toLocaleDateString()}` : ""}
                      </div>
                      {signal.original_text_excerpt && (
                        <div style={{ fontSize: 11, fontStyle: "italic", color: COLORS.dark, marginBottom: 6 }}>
                          &ldquo;{signal.original_text_excerpt}&rdquo;
                        </div>
                      )}
                  {(signal.structured_findings || []).map((finding, fIdx) => (
                    <div key={`${finding.concept_code}-${fIdx}`} style={{ fontSize: 10, color: COLORS.gray, marginBottom: 2 }}>
                      <strong style={{ color: COLORS.dark }}>{finding.concept_code}</strong>
                      {" → "}{describeStructuredFindingDestinations(finding.concept_code)}
                      {typeof finding.confidence === "number" ? ` (confidence ${Math.round(finding.confidence * 100)}%)` : ""}
                    </div>
                  ))}
                  <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                    <button
                      type="button"
                      onClick={() => handleApplyStructuredSignal(signal)}
                      disabled={structuredFindingsBusyId === signal.id || structuredFindingsBulkBusy}
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        padding: "6px 12px",
                        borderRadius: 6,
                        border: "none",
                        background: COLORS.teal,
                        color: "#fff",
                        cursor: structuredFindingsBusyId === signal.id || structuredFindingsBulkBusy ? "default" : "pointer",
                        opacity: structuredFindingsBusyId === signal.id || structuredFindingsBulkBusy ? 0.6 : 1,
                      }}
                    >
                      {structuredFindingsBusyId === signal.id ? "Applying…" : "Apply to RNICA"}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDismissStructuredSignal(signal)}
                      disabled={structuredFindingsBusyId === signal.id || structuredFindingsBulkBusy}
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        padding: "6px 12px",
                        borderRadius: 6,
                        border: `1px solid ${COLORS.border}`,
                        background: "transparent",
                        color: COLORS.gray,
                        cursor: structuredFindingsBusyId === signal.id || structuredFindingsBulkBusy ? "default" : "pointer",
                        opacity: structuredFindingsBusyId === signal.id || structuredFindingsBulkBusy ? 0.6 : 1,
                      }}
                    >
                      Dismiss
                    </button>
                  </div>
                    </div>
                  </div>
                </div>
              ))}

              {structuredFieldProvenance.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.dark, marginBottom: 6 }}>
                    Applied field provenance ({structuredFieldProvenance.length})
                  </div>
                  {structuredFieldProvenance.map((p, idx) => (
                    <div key={`${p.signal_id}-${p.path}-${idx}`} style={{ fontSize: 10, color: COLORS.gray, marginBottom: 4 }}>
                      <strong style={{ color: COLORS.dark }}>{p.section}.{p.path}</strong> = {JSON.stringify(p.value)}
                      <div style={{ fontStyle: "italic" }}>
                        from {p.source_type}{p.source_excerpt ? `: "${p.source_excerpt}"` : ""}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {structuredFieldConflicts.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.error, marginBottom: 6 }}>
                    Conflicts requiring RN review ({structuredFieldConflicts.length})
                  </div>
                  {structuredFieldConflicts.map((c, idx) => (
                    <div
                      key={`${c.signal_id}-${c.path}-${idx}`}
                      style={{ fontSize: 10, color: COLORS.dark, marginBottom: 6, padding: 6, borderRadius: 6, background: COLORS.sfvTagBg, border: `1px solid ${COLORS.error}` }}
                    >
                      <strong>{c.section}.{c.path}</strong>
                      <div>Current value: {JSON.stringify(c.existingValue)}</div>
                      <div>AI-suggested value: {JSON.stringify(c.suggestedValue)}</div>
                      <div style={{ fontStyle: "italic" }}>
                        from {c.source_type}{c.source_excerpt ? `: "${c.source_excerpt}"` : ""}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Spacer so page content isn't hidden behind the fixed footer below */}
      <div style={styles.footerSpacer} />

      {/* ── Footer ── */}
      <div style={styles.footer}>
        <div style={{ display: "flex", gap: 8 }}>
          <button style={styles.btnSecondary} onClick={goPrev} disabled={activeSection === routes[0]?.key}>
            &larr; Previous
          </button>
          <button style={styles.btnSecondary} onClick={goNext} disabled={activeSection === routes[routes.length - 1]?.key}>
            Next &rarr;
          </button>
          {assessmentId && (
            <AdmissionActionCenterButton
              styles={styles}
              onClick={() => setActionCenterOpen(true)}
            />
          )}
          {assessmentId && !locked && (
            <button
              type="button"
              style={{ ...styles.btnSecondary, color: COLORS.error, borderColor: COLORS.error }}
              onClick={handleDelete}
              disabled={saving}
              title="Permanently delete this draft assessment (only available before it is signed)"
            >
              Delete
            </button>
          )}
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {assessmentId && (
            <span style={{ fontSize: 12, color: COLORS.gray }}>ID: {assessmentId}</span>
          )}
          {locked && lockedAt && (
            <span style={{ fontSize: 12, color: COLORS.gray }}>
              Signed: {new Date(lockedAt).toLocaleString()}
            </span>
          )}
          <button style={styles.btnPrimary} onClick={handleSave} disabled={saving || locked}>
            {saving ? "Saving..." : saveButtonLabel}
          </button>
          {assessmentId && !locked && (
            <button
              style={styles.btnDanger}
              onClick={handleLock}
            >
              Lock Assessment
            </button>
          )}
        </div>
      </div>

      <AdmissionActionCenterDrawer
        open={actionCenterOpen}
        onClose={() => setActionCenterOpen(false)}
        assessmentId={assessmentId}
        sourceSection={activeSection}
        styles={styles}
        COLORS={COLORS}
      />
      </div>
    </AssessmentModeContext.Provider>
  );
}
