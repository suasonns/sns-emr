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
import AdmissionActionCenterDrawer, {
  AdmissionActionCenterButton,
} from "./AdmissionActionCenterDrawer";
import {
  RNICA_ASSESSMENT_MODULES,
  validateBodyMapRegions,
} from "./rn-ica/rnIcaClinicalNavigation";
import { fetchPatientSummary } from "../api/patientCharts";
import { fetchCensusWorkspace } from "../api/census";
import {
  saveRnicaAssessment,
  getRnicaAssessment,
  getRnicaAssessmentByPatient,
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
} from "../api/icaAssessments";
import { detectLCD, evaluateLCD, getLCDConfig } from "../api/eligibility";
import {
  listAideVisitsForPatient,
  getChhaVisitOutcome,
  upsertChhaVisitOutcome,
} from "../api/chhaVisits";
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
} from "../api/physicianOrders";
import { getCurrentUser } from "../api/session";
import { fetchFacesheet, fetchPerformanceHistory } from "../api/facesheet";
import { listVendors } from "../api/vendors";
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
import {
  buildClinicalNarrative,
  DISEASE_TRAJECTORY_OPTIONS,
  isLegacyDiseaseTrajectoryValue,
  getDiseaseTrajectoryLabel,
} from "../intake/clinicalNarrativeBuilder";

import { getActivePatientId, setActivePatientId, clearActivePatientId } from "../utils/activePatient";
import MedicationNameInput from "./MedicationNameInput";
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
  "Diagnoses", "Performance Status", "Neurological", "Cardiovascular",
  "Respiratory", "Infection", "Gastrointestinal", "Nutrition",
  "Endocrine", "Genitourinary",
  "Musculoskeletal", "Integumentary - Skin", "Imminent Death", "SFV",
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
  { key: "neurological",      nav: "Neurological",          formSection: "neurological" },
  { key: "cardiovascular",    nav: "Cardiovascular",        formSection: "cardiovascular" },
  { key: "respiratory",       nav: "Respiratory",           formSection: "respiratory" },
  { key: "infection",         nav: "Infection",             formSection: "infection" },
  { key: "gastrointestinal",  nav: "Gastrointestinal",      formSection: "gastrointestinal" },
  { key: "nutrition",         nav: "Nutrition",             formSection: "nutrition" },
  { key: "endocrine",         nav: "Endocrine",             formSection: "endocrine" },
  { key: "genitourinary",     nav: "Genitourinary",         formSection: "genitourinary" },
  { key: "musculoskeletal",   nav: "Musculoskeletal",       formSection: "musculoskeletal" },
  { key: "skin",              nav: "Integumentary - Skin",  formSection: "skin" },
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

const SIDEBAR_CONFIG = [
  { key: "demographics",      label: "Patient Demographics",  icon: "👤", hope: ["A1110","A1005","A1010"], color: "green" },
  { key: "assessment",        label: "Assessment",           icon: "📁", hope: [],                         color: null },
  { key: "caregiverAssessment", label: "Caregiver Assessment", icon: "🧑‍⚕️", hope: [], color: null, parent: "demographics", scrollTarget: "pcg", cdphRequired: true },
  { key: "advancedCarePlanning", label: "Advanced Care Planning", icon: "📜", hope: ["F2000","F2100","F2200"], color: "green", parent: "demographics", scrollTarget: "advancedCarePlanning", cdphRequired: true },
  { key: "vitals",            label: "Vitals",                icon: "🩺", hope: [],                        color: null },
  { key: "pain",              label: "Pain Assessment",       icon: "⚡",    hope: ["J0900","J0915"],          color: "green", sfv: true },
  { key: "symptomImpact",     label: "Symptom Impact",        icon: "📊", hope: ["J2051"],                  color: "red" },
  { key: "diagnoses",         label: "Diagnoses",             icon: "🔬", hope: ["I0010","J0050"],          color: "green" },
  { key: "performanceStatus", label: "Performance Status",    icon: "📈", hope: ["M1190"],                  color: "green" },
  { key: "neurological",      label: "Neurological",          icon: "🧠", hope: ["N0500","N0510","N0520"],  color: "green", sfv: true },
  { key: "cardiovascular",    label: "Cardiovascular",        icon: "❤️", hope: [],                      color: null },
  { key: "respiratory",       label: "Respiratory",           icon: "🫁", hope: [],                         color: null, sfv: true },
  { key: "infection",         label: "Infection",             icon: "🦠", hope: [],                         color: null },
  { key: "gastrointestinal",  label: "Gastrointestinal",      icon: "🍽️", hope: [],                   color: null, sfv: true },
  { key: "nutrition",         label: "Nutrition",             icon: "🥗", hope: [],                         color: null },
  { key: "endocrine",         label: "Endocrine",             icon: "🔄", hope: [],                         color: null },
  { key: "genitourinary",     label: "Genitourinary",         icon: "💧", hope: [],                         color: null },
  { key: "musculoskeletal",   label: "Musculoskeletal",       icon: "🦴", hope: [],                         color: null },
  { key: "skin",              label: "Integumentary - Skin",  icon: "🩹", hope: ["M1190"],                  color: "green" },
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
    sleepRest: {
      sleepPattern: "", averageSleepHours: "",
      sleepAids: [], restfulness: "",
      nighttimeSymptoms: [], response: "",
      notes: "",
    },
    hopeItems: { n0500: "", n0510: "", n0520: "" },
    notes: "",
  },

  // ─── 8. CARDIOVASCULAR ────────────────────────────
  cardiovascular: {
    bpSymptoms: [],
    pulseSites: [],
    pulseQuality: "",
    edema: { present: "", location: [], severity: "", pitting: "" },
    chestPain: { present: "", type: "", frequency: "" },
    peripheralCirculation: "", heartSounds: "", jvd: "",
    skinColor: "", pacemaker: false, internalDefibrillator: false,
    varicoseVeins: false, centralVenousLine: false,
    coolExtremities: false, stasisUlcer: false,
    notes: "",
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
  },

  // ─── 15. MUSCULOSKELETAL ──────────────────────────
  musculoskeletal: {
    weakness: "", rigidity: "", contractures: "", paralysis: "",
    // Structured location to match the depth of sibling body-system findings
    // (e.g. cardiovascular.edema.location). `contractures` itself stays the
    // existing None/Mild/Moderate/Severe severity radio.
    contracturesLocation: [],
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
  },

  // ─── 16. SKIN ─────────────────────────────────────
  skin: {
    skinConditionsPresent: false,
    skinStatus: [], skinTurgor: "",
    skinBodySites: [],
    braden: {
      sensoryPerception: "", moisture: "", activity: "",
      mobility: "", nutrition: "", frictionShear: "", total: "",
    },
    pressureInjuryRisk: "",
    wounds: [],
    woundImpairment: "",
    pressureReliefMeasures: [], repositioningPlan: "",
    notes: "",
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
    familySocialSupport: "",
    primarySupportPerson: "", supportRelationship: "",
    patientConcerns: [],
    caregiverFamilyConcerns: [],
    distressRating: "",
    psychosocialHistory: [],
    copingAssessment: "", copingNotes: "",
    interventionPlan: [],
    socialWorkVisitNeeded: false,
    notes: "",
  },

  // ─── 21. SPIRITUAL ────────────────────────────────
  spiritual: {
    patientActiveInFaithTradition: false,
    patientFaith: "",
    caregiverActiveInFaithTradition: false,
    caregiverFaith: "",
    spiritualConcerns: [],
    spiritualDistressRating: "",
    concernsDiscussed: false,
    concernsAskedStatus: "", // HOPE F3000 A: 0 No / 1 Yes-discussed / 2 Yes-refused
    concernsDiscussedDate: "",
    chaplainNeeded: false,
    notes: "",
  },

  // ─── 22. BEREAVEMENT ──────────────────────────────
  bereavement: {
    patientConcerns: [],
    caregiverConcerns: [],
    bereavementRisk: "",
    riskFactors: [],
    bereavementVisitNeeded: false,
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
    saveRnicaAssessment(
      assessmentSubtype ? { patientId, formData, assessmentSubtype } : { patientId, formData }
    ),
  getRNICAAssessment: (assessmentId) => getRnicaAssessment(assessmentId),
  getRNICAAssessmentByPatient: (patientId) => getRnicaAssessmentByPatient(patientId),
  updateRNICAAssessment: (assessmentId, formData) =>
    updateRnicaAssessment(assessmentId, formData),
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
  if (formData.psychosocial.patientConcerns?.includes("Suicide concerns") && !formData.psychosocial.notes?.trim()) {
    warnings["psychosocial.notes"] = "Safety: Suicide concerns indicated — document safety assessment/plan in Psychosocial Notes";
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
  if (!formData.admissionsOrder.levelOfCare.level) {
    errors["admissionsOrder.levelOfCare"] = "Level of Care is required for admission";
  }

  // Admissions Order ? T.O. Verification
  if (!formData.admissionsOrder.toVerification.verbalOrderReadBack) {
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
      <input
        style={styles.input} type={type} value={value || ""}
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
      <textarea
        style={{ ...styles.textarea, minHeight: rows * 24 }} value={value || ""}
        onChange={(e) => onChange(e.target.value)} placeholder={placeholder} disabled={disabled}
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
      <select style={styles.select} value={value || ""} onChange={(e) => onChange(e.target.value)} disabled={disabled}>
        <option value="">— Select —</option>
        {options.map((opt) => (
          <option key={typeof opt === "string" ? opt : opt.value} value={typeof opt === "string" ? opt : opt.value}>
            {typeof opt === "string" ? opt : opt.label}
          </option>
        ))}
      </select>
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
      <div style={styles.radioGroup}>
        {options.map((opt) => {
          const val = typeof opt === "string" ? opt : opt.value;
          const lbl = typeof opt === "string" ? opt : opt.label;
          return (
            <label key={val} style={styles.radioLabel}>
              <input type="radio" checked={value === val} onChange={() => onChange(val)} />
              {lbl}
            </label>
          );
        })}
      </div>
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
      <div style={styles.radioGroup}>
        {options.map((opt) => (
          <label key={opt.value || "unassessed"} style={{
            ...styles.radioLabel,
            ...(opt.value === "" && normalized === "" ? { color: COLORS.gray, fontStyle: "italic" } : {}),
          }}>
            <input type="radio" checked={normalized === opt.value} onChange={() => onChange(opt.value)} />
            {opt.label}
          </label>
        ))}
      </div>
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
              <input type="checkbox" checked={values.includes(val)} onChange={() => toggle(val)} />
              {lbl}
            </label>
          );
        })}
      </div>
    </div>
  );
}

function FormCheckbox({ label, checked, onChange, disabled = false }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return (
    <label style={{ ...styles.checkboxLabel, ...styles.formGroup, opacity: disabled ? 0.55 : 1, cursor: disabled ? "not-allowed" : "pointer" }}>
      <input type="checkbox" checked={checked || false} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
      <span style={{ fontSize: 13, fontWeight: 500 }}>{label}</span>
    </label>
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
        const groupOpen = !workspacePilot
          || expandedGroups.has(group.group_id)
          || (needsReview && !collapsedGroups.has(group.group_id));
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
        label="Clinical Narrative"
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
              <span role="columnheader">ICD-10</span>
              <span role="columnheader">Description</span>
              <span role="columnheader">Terminal related</span>
              <span role="columnheader">Action</span>
            </div>
            {visibleRows.map((row, idx) => (
              <div className="rnica-diagnosis-ledger__row" role="row" key={idx}>
                <div role="cell">
                  <input
                    aria-label={`Secondary diagnosis ${idx + 1} ICD-10 code`}
                    placeholder="ICD-10"
                    value={row.icd10 || ""}
                    onChange={(event) => updateRow(idx, "icd10", event.target.value)}
                  />
                </div>
                <div role="cell">
                  <input
                    aria-label={`Secondary diagnosis ${idx + 1} description`}
                    placeholder="Description"
                    value={row.description || ""}
                    onChange={(event) => updateRow(idx, "description", event.target.value)}
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
  { key: "cancer", hopeCode: "I0100", label: "Cancer", group: "Cancer", regex: /^C\d/i },
  { key: "heartFailure", hopeCode: "I0600", label: "Heart Failure (e.g., CHF, pulmonary edema)", group: "Heart/Circulation", regex: /^I50/i },
  { key: "pvdPad", hopeCode: "I0900", label: "Peripheral Vascular Disease (PVD) or Peripheral Arterial Disease (PAD)", group: "Heart/Circulation", regex: /^I7[03]/i },
  { key: "cardiovascularExclHF", hopeCode: "I0950", label: "Cardiovascular (excluding heart failure)", group: "Heart/Circulation", regex: /^I(1[0-3]|15|2[0-5])/i },
  { key: "liverDisease", hopeCode: "I1101", label: "Liver disease (e.g., cirrhosis)", group: "Gastrointestinal", regex: /^K7[0-4]/i },
  { key: "renalDisease", hopeCode: "I1510", label: "Renal disease", group: "Genitourinary", regex: /^(N18|N19)/i },
  { key: "sepsis", hopeCode: "I2102", label: "Sepsis", group: "Infections", regex: /^A41/i },
  { key: "diabetesMellitus", hopeCode: "I2900", label: "Diabetes Mellitus (DM)", group: "Metabolic", regex: /^E(0[89]|1[013])/i },
  { key: "neuropathy", hopeCode: "I2910", label: "Neuropathy", group: "Metabolic", regex: /^(G6[023]|E1[013]\.4|E08\.4|E09\.4)/i },
  { key: "stroke", hopeCode: "I4501", label: "Stroke", group: "Neurological", regex: /^(I6[0-3]|I65|I66|I69)/i },
  { key: "dementia", hopeCode: "I4801", label: "Dementia (including Alzheimer's disease)", group: "Neurological", regex: /^(F0[0-3]|G30|G31\.1)/i },
  { key: "neurologicalConditions", hopeCode: "I5150", label: "Neurological Conditions (e.g., Parkinson's disease, MS, ALS)", group: "Neurological", regex: /^(G20|G35|G12\.2)/i },
  { key: "seizureDisorder", hopeCode: "I5401", label: "Seizure Disorder", group: "Neurological", regex: /^G40/i },
  { key: "copd", hopeCode: "I6202", label: "Chronic Obstructive Pulmonary Disease (COPD)", group: "Pulmonary", regex: /^J44/i },
];

function matchesCategory(icd10, regex) {
  const code = (icd10 || "").trim().toUpperCase();
  if (!code) return false;
  return regex.test(code);
}

function categorizeIcd10(icd10) {
  return HOPE_COMORBIDITY_CATEGORIES.find((cat) => matchesCategory(icd10, cat.regex)) || null;
}

// Used to gate disease-specific performance scales (NYHA/FAST/ECOG) in the
// Performance Status section so the RN only sees the scale relevant to this
// patient's actual diagnoses, checking both the primary diagnosis and every
// secondary diagnosis (not just the principal one) against the same
// ICD-10 category regexes used for HOPE comorbidity categorization above.
function diagnosesIncludeCategory(diagnosesData, categoryKey) {
  const category = HOPE_COMORBIDITY_CATEGORIES.find((cat) => cat.key === categoryKey);
  if (!category) return false;
  const primaryIcd10 = diagnosesData?.primaryDiagnosis?.icd10 || "";
  if (matchesCategory(primaryIcd10, category.regex)) return true;
  const secondaryDx = diagnosesData?.secondaryDiagnoses || [];
  return secondaryDx.some((dx) => matchesCategory(dx?.icd10, category.regex));
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

  const groups = useMemo(() => {
    const order = ["Cancer", "Heart/Circulation", "Gastrointestinal", "Genitourinary", "Infections", "Metabolic", "Neurological", "Pulmonary"];
    return order
      .map((group) => ({ group, categories: HOPE_COMORBIDITY_CATEGORIES.filter((c) => c.group === group) }))
      .filter((g) => g.categories.length);
  }, []);

  return (
    <div className={workspacePilot ? "rnica-comorbidity-panel" : undefined}>
      <div className={workspacePilot ? "rnica-comorbidity-guidance" : undefined} style={styles.infoBox}>
        Per CMS HOPE guidance: check all comorbid/coexisting conditions addressed in the plan of
        care. <strong>Do not check a category already coded as the Principal Diagnosis</strong>{" "}
        — the exception is if the patient has a second, distinct cancer diagnosis.
      </div>

      <div className={workspacePilot ? "rnica-comorbidity-grid" : undefined}>
      {groups.map(({ group, categories }) => (
        <div key={group} className={workspacePilot ? "rnica-comorbidity-group" : undefined} style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 12, fontWeight: 800, color: COLORS.gray, textTransform: "uppercase", letterSpacing: "0.03em", marginBottom: 6 }}>
            {group}
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
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={excluded}
                      onChange={(e) => setHope(cat.key, e.target.checked)}
                    />
                    <span>{cat.label}</span>
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
      </div>

      <div style={{ marginBottom: 8 }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: COLORS.gray, textTransform: "uppercase", letterSpacing: "0.03em", marginBottom: 6 }}>
          Other
        </div>
        <label style={styles.checkboxLabel}>
          <input type="checkbox" checked={Boolean(hope.other)} onChange={(e) => setHope("other", e.target.checked)} />
          <span>Other Medical Condition</span>
        </label>
        <HopeTag code="I8005" />
        {uncategorizedSecondary.length > 0 && (
          <div style={{ fontSize: 11, color: COLORS.gray, marginTop: 4 }}>
            Uncategorized secondary diagnoses: {uncategorizedSecondary.map((dx) => `${dx.icd10} ${dx.description || ""}`.trim()).join("; ")}
          </div>
        )}
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

// Auto-calculates BMI from height (inches) and weight (lbs) so it is never
// entered as an independent, unrelated manual value. The field remains
// editable (RN can override), but is pre-populated/kept in sync whenever
// height or weight change, and is still persisted at vitals.bmi in the
// existing form_data JSONB model (no new storage location).
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

// RN ICA -> Plan of Care controls for a single body-system subcard.
// Add / View / Update / Resolve here all call the authoritative Plan of
// Care document API (via backend app/services/rnica_poc_adapter.py) — this
// component holds no POC state of its own beyond what it fetches on demand,
// and never writes into RnicaAssessment.form_data.
function PocSectionControls({ assessmentId, sectionKey, cardTitle, styles, COLORS }) {
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
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button type="button" onClick={() => setShowAdd((v) => !v)} style={{
          fontSize: 11.5, fontWeight: 700, padding: "6px 10px", borderRadius: 6,
          border: `1px solid ${COLORS.teal}`, background: showAdd ? COLORS.teal : "transparent",
          color: showAdd ? COLORS.white : COLORS.teal, cursor: "pointer",
        }}>
          + Add to POC
        </button>
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

      {error && <div style={{ color: COLORS.error || "#ef4444", fontSize: 12, marginTop: 8 }}>{error}</div>}

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
      {error && <div style={{ color: "#ef4444", fontSize: 12.5 }}>{error}</div>}

      <Card title="CHHA Plan of Care" cms="Home Health Aide">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginBottom: 8 }}>
          <div style={{ fontSize: 12.5, color: COLORS.gray }}>
            Assigned Home Aide: <strong style={{ color: COLORS.dark }}>{assignedAide || "Not yet assigned"}</strong>
          </div>
          {chhaPoc.completed && (
            <div style={{ fontSize: 12.5, color: "#22c55e", fontWeight: 700 }}>
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
                background: "rgba(239,68,68,0.12)", color: "#b91c1c", border: "1px solid rgba(239,68,68,0.3)",
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
          <div style={{ fontSize: 12, fontWeight: 700, color: "#b91c1c", marginTop: 8 }}>
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
          <div style={{ fontSize: 11.5, fontWeight: 700, color: "#dc2626", background: "#fee2e2", borderRadius: 6, padding: "8px 10px", marginBottom: 10 }}>
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
                borderRadius: 8, border: `1px solid ${anyMissing ? "#f59e0b" : COLORS.border}`, background: COLORS.bg, padding: "8px 10px",
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
                            {isDisallowedAssist && <span style={{ fontSize: 10.5, color: "#dc2626" }}>— not safe at this patient's assist level</span>}
                          </label>
                          {itemChecked && itemDef.detail && (
                            <div style={{ marginLeft: 24, marginTop: 4, maxWidth: 420 }}>
                              <FormInput
                                label={`${itemDef.detailLabel} (required)`}
                                value={selected.detail}
                                onChange={(v) => updateTaskItemDetail(opt.value, itemDef.code, v)}
                              />
                              {needsDetail && <div style={{ fontSize: 10.5, color: "#f59e0b", marginTop: 2 }}>Required.</div>}
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {transferRequiredMissing && (
                      <div style={{ gridColumn: "1 / -1", fontSize: 11, fontWeight: 700, color: "#dc2626", background: "#fee2e2", borderRadius: 6, padding: "6px 8px" }}>
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
                          <div style={{ fontSize: 10.5, color: "#f59e0b", marginTop: 2 }}>Required.</div>
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
          <div style={{ ...styles.infoBox, marginBottom: 8, borderColor: "#f59e0b" }}>
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
        {!saving && saveMessage && <div style={{ fontSize: 11, color: "#22c55e", marginTop: 6 }}>{saveMessage}</div>}
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
      {error && <div style={{ color: "#ef4444", fontSize: 12.5, marginBottom: 8 }}>{error}</div>}
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
                        style={{ border: "none", background: "transparent", color: "#ef4444", cursor: "pointer", fontSize: 11.5, textDecoration: "underline" }}
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
                    {entry.issue_identified && <div style={{ color: "#b91c1c" }}>Issue: {entry.issue_narrative || "(no detail provided)"}</div>}
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
      {error && <div style={{ color: "#ef4444", fontSize: 12.5 }}>{error}</div>}

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
                background: "rgba(239,68,68,0.12)", color: "#b91c1c", border: "1px solid rgba(239,68,68,0.3)",
              }}>
                {c.riskLabel}
              </span>
            ))}
          </div>
          <div style={{ fontSize: 11.5, fontWeight: 700, color: COLORS.dark, marginBottom: 4 }}>Today, watch for:</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, color: COLORS.dark, lineHeight: 1.7 }}>
            {todayWatchFor.map((item) => <li key={item}>{item}</li>)}
          </ul>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#b91c1c", marginTop: 8 }}>
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
                  borderRadius: 8, border: `1px solid ${anyCategoryMissing ? "#f59e0b" : COLORS.border}`, background: COLORS.bg, padding: "10px 12px",
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
                              {needsChecklist && <div style={{ fontSize: 10.5, color: "#f59e0b", marginTop: 2 }}>Check at least one.</div>}
                              {checklist.some((c) => ASSIST_NAME_TRIGGER_CODES.includes(c)) && (
                                <div style={{ marginTop: 6 }}>
                                  <FormInput
                                    label="Who assisted? (name/role — required, staffing safety record)"
                                    value={result.assistedBy}
                                    onChange={(v) => setTaskResult(t.key, { assistedBy: v })}
                                    placeholder="e.g., Second HA, Maria R."
                                    disabled={visitLocked}
                                  />
                                  {needsAssistedBy && <div style={{ fontSize: 10.5, color: "#f59e0b", marginTop: 2 }}>Required.</div>}
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
                              {needsFreeNote && <div style={{ fontSize: 10.5, color: "#f59e0b", marginTop: 2 }}>Required.</div>}
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
          <div style={{ ...styles.infoBox, borderColor: "#ef4444", color: "#b91c1c", fontWeight: 700 }}>🚨 RN Notification Required</div>
        )}
      </Card>

      <Card title="Respiration">
        <FormCheckboxGroup values={note.respiration} onChange={(v) => setNote((p) => ({ ...p, respiration: v }))} options={CHHA_RESPIRATION_OPTIONS} label="Observed" />
        {respirationAbnormal && (
          <div style={{ ...styles.infoBox, borderColor: "#ef4444", color: "#b91c1c", fontWeight: 700 }}>🚨 RN Notification Required</div>
        )}
      </Card>

      <Card title="Nutrition / Swallowing">
        <FormCheckboxGroup values={note.nutrition} onChange={(v) => setNote((p) => ({ ...p, nutrition: v }))} options={CHHA_NUTRITION_OPTIONS} label="Observed" />
        {nutritionAbnormal && (
          <div style={{ ...styles.infoBox, borderColor: "#ef4444", color: "#b91c1c", fontWeight: 700 }}>🚨 RN Notification Required</div>
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
          <div style={{ ...styles.infoBox, borderColor: "#ef4444", marginBottom: 10 }}>
            <div style={{ fontWeight: 700, color: "#b91c1c", marginBottom: 4 }}>🚨 RN Notification Required — call {chhaReportToLabel(reportToRole)} now.</div>
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
            {missingRnNotifiedName && <div style={{ fontSize: 10.5, color: "#f59e0b", marginTop: 2 }}>Required.</div>}
          </div>
        )}
      </Card>

      <Card title="Submit">
        {missingTaskNotes > 0 && (
          <div style={{ ...styles.infoBox, marginBottom: 8, borderColor: "#f59e0b" }}>
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
        {!saving && saveMessage && <div style={{ fontSize: 11, color: "#22c55e", marginTop: 6 }}>{saveMessage}</div>}
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
      {error && <div style={{ color: COLORS.error || "#ef4444", fontSize: 12, marginBottom: 8 }}>{error}</div>}
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
                {linkError && <div style={{ color: COLORS.error || "#ef4444", fontSize: 11.5, marginTop: 6 }}>{linkError}</div>}
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
                {mergeError && <div style={{ color: COLORS.error || "#ef4444", fontSize: 11.5, marginTop: 6 }}>{mergeError}</div>}
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
                {historyError && <div style={{ color: COLORS.error || "#ef4444" }}>{historyError}</div>}
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
    if (status === "DENIED") return COLORS.error || "#ef4444";
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
      {error && <div style={{ color: COLORS.error || "#ef4444", fontSize: 11.5, marginTop: 8 }}>{error}</div>}

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
                <div style={{ color: COLORS.error || "#ef4444", marginTop: 2 }}>Denied: {a.decisionReason}</div>
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
                    border: `1px solid ${COLORS.error || "#ef4444"}`, background: "transparent",
                    color: COLORS.error || "#ef4444", cursor: decidingId === a.id ? "wait" : "pointer",
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

const SEVERITY_COLORS = {
  CONTRAINDICATED: { bg: "#450a0a", border: "#ef4444", text: "#fecaca" },
  MAJOR: { bg: "#450a0a", border: "#ef4444", text: "#fecaca" },
  MODERATE: { bg: "#451a03", border: "#f59e0b", text: "#fde68a" },
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
      {allergyError && <div style={{ color: "#ef4444", fontSize: 12, marginTop: 4 }}>{allergyError}</div>}
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

      {submitError && <div style={{ color: "#ef4444", fontSize: 12.5, margin: "6px 0" }}>{submitError}</div>}

      <button type="button" onClick={handleAddMedication} disabled={submitting} style={{ ...styles.btnPrimary, marginTop: 8 }}>
        {submitting ? "Adding…" : "+ Add Medication"}
      </button>

      {/* ── Current / historical medication list ── */}
      <div style={{ marginTop: 20 }}>
        <div style={{ ...styles.label, marginBottom: 8 }}>Medication List</div>
        {loading && <div style={{ fontSize: 12.5, color: COLORS.gray }}>Loading…</div>}
        {error && <div style={{ color: "#ef4444", fontSize: 12.5 }}>{error}</div>}
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
                      <span style={{ color: "#22c55e", fontWeight: 600 }}>
                        ✓ Signed{m.signed_by_name ? ` — ${m.signed_by_name}` : ""}
                      </span>
                    ) : m.order_status ? (
                      <span style={{ color: "#f59e0b", fontWeight: 600 }}>⏳ Awaiting MD Signature</span>
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

export function OrdersHubCard({ patientId }) {
  const currentUser = getCurrentUser();
  const isMD = currentUser?.role === "MD";

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
    source_type: "WRITTEN", ordered_by_provider_name: "", ordered_by_provider_role: "MD",
    prescriber_authenticated: false, phone_readback_confirmed: false,
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const [labCatalog, setLabCatalog] = useState(null);
  const [selectedLabTests, setSelectedLabTests] = useState([]);

  const [vendorOptions, setVendorOptions] = useState([]);

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

  const handleAddOrder = async () => {
    const orderText = activeType === "LAB"
      ? selectedLabTests.map((t) => `${t.name} (CPT ${t.cpt})`).join("; ")
      : [
          form.order_text,
          form.strength && `Strength: ${form.strength}`,
          form.dosage && `Dosage/Qty: ${form.dosage}`,
          form.route && `Route: ${form.route}`,
          form.frequency && `Frequency: ${form.frequency}`,
          form.indication && `Indication: ${form.indication}`,
          form.payer && `Payer: ${form.payer}`,
          form.vendor && `Vendor: ${form.vendor}`,
          form.administered_by && `Administered by: ${form.administered_by}`,
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
      });
      await submitPhysicianOrder(draft.id);
      setForm({
        order_text: "", strength: "", dosage: "", route: "", frequency: "", indication: "",
        quantity: "", payer: "", vendor: "", administered_by: "", special_instruction: "",
        source_type: "WRITTEN", ordered_by_provider_name: "", ordered_by_provider_role: "MD",
        prescriber_authenticated: false, phone_readback_confirmed: false,
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
                onChange={(e) => setImportAttestation((f) => ({ ...f, ordered_by_provider_name: e.target.value }))}
                placeholder="Dr. Jane Smith"
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
            {labCatalog?.categories?.map((cat) => (
              <div key={cat.category} style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: SNS_COLORS.muted, marginBottom: 4 }}>{cat.category}</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 16px" }}>
                  {cat.tests.map((test) => (
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
            ))}
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
            {activeType !== "OTHER" && (
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
          </div>
        )}
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
              <input style={ohInput} value={form.ordered_by_provider_name} onChange={(e) => setForm((f) => ({ ...f, ordered_by_provider_name: e.target.value }))} placeholder="Dr. Jane Smith" />
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
                    border: `1px solid ${o.status === "EXECUTED" && o.awaiting_countersignature ? SNS_COLORS.orange : o.status === "EXECUTED" ? SNS_COLORS.green : o.status === "APPROVED" ? SNS_COLORS.blue : o.status === "CANCELLED" ? SNS_COLORS.red : SNS_COLORS.orange}`,
                    color: o.status === "EXECUTED" && o.awaiting_countersignature ? SNS_COLORS.orange : o.status === "EXECUTED" ? SNS_COLORS.green : o.status === "APPROVED" ? SNS_COLORS.blue : o.status === "CANCELLED" ? SNS_COLORS.red : SNS_COLORS.orange,
                  }}>
                    {o.status === "EXECUTED" && o.awaiting_countersignature ? "Administered — Awaiting MD Countersignature" : o.status.replace(/_/g, " ")}
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
                  {o.status === "PENDING_HOSPICE_MD_APPROVAL" && isMD && (
                    <button type="button" style={ohBtnSecondary} disabled={busyOrderId === o.id} onClick={() => runOrderAction(o.id, approvePhysicianOrder)}>
                      Approve &amp; Sign (MD)
                    </button>
                  )}
                  {o.status === "PENDING_HOSPICE_MD_APPROVAL" && !isMD && !(o.source_type === "VERBAL_PHONE" && o.phone_readback_confirmed) && (
                    <span style={{ fontSize: 11, color: SNS_COLORS.orange }}>Awaiting Medical Director signature</span>
                  )}
                  {o.status === "APPROVED" && (
                    <button type="button" style={ohBtnSecondary} disabled={busyOrderId === o.id} onClick={() => runOrderAction(o.id, executePhysicianOrder)}>
                      Mark Executed
                    </button>
                  )}
                  {o.status === "EXECUTED" && o.awaiting_countersignature && isMD && (
                    <button type="button" style={{ ...ohBtnSecondary, borderColor: SNS_COLORS.blue, color: SNS_COLORS.blue }} disabled={busyOrderId === o.id} onClick={() => runOrderAction(o.id, approvePhysicianOrder)}>
                      Countersign (MD)
                    </button>
                  )}
                  {o.status === "EXECUTED" && o.awaiting_countersignature && !isMD && (
                    <span style={{ fontSize: 11, color: SNS_COLORS.orange }}>Administered — awaiting MD countersignature</span>
                  )}
                  {(o.status === "DRAFT" || o.status === "PENDING_HOSPICE_MD_APPROVAL" || o.status === "APPROVED") && (
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
function Card({ title, children, hopeCode, sfv, cms, id }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return (
    <div className="rnica-form-card" style={styles.card} id={id}>
      <div className="rnica-form-card__title" style={{ ...styles.cardTitle, display: "flex", alignItems: "center", gap: 8 }}>
        {title}
        {hopeCode && <HopeTag code={hopeCode} />}
        {sfv && <SfvTag />}
        {cms && <CmsTag label={cms} />}
      </div>
      {children}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// 6. SECTION RENDERERS — All 28 Modules
// ════════════════════════════════════════════════════════════════

function renderDemographics(data, update, COLORS, styles, moduleKey = "all") {
  const u = (path, val) => update("demographics", path, val);
  const showPatient = moduleKey === "all" || moduleKey === "demographics";
  const showCaregiver = moduleKey === "all" || moduleKey === "caregiverAssessment";
  const showPlanning = moduleKey === "all" || moduleKey === "advancedCarePlanning";
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
          options={["White", "Black/African American", "Asian", "American Indian/Alaska Native", "Native Hawaiian/Pacific Islander", "Other"]} />
        <FormCheckboxGroup label="Ethnicity" values={data.ethnicity} onChange={(v) => u("ethnicity", v)} hopeCode="A1005"
          options={["Hispanic/Latino", "Not Hispanic/Latino", "Unknown"]} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
          <FormSelect label="Preferred Language" value={data.preferredLanguage} onChange={(v) => u("preferredLanguage", v)}
            options={["English", "Spanish", "Chinese", "Vietnamese", "Tagalog", "Korean", "Other"]} />
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
            <FormRadioGroup label="Able to Administer Medications" value={data.pcg?.ableToAdministerMeds} onChange={(v) => u("pcg.ableToAdministerMeds", v)}
              options={["Yes", "No", "With training"]} />
            <FormRadioGroup label="Willing to Provide Care" value={data.pcg?.willingToProvideCare} onChange={(v) => u("pcg.willingToProvideCare", v)}
              options={["Yes", "No", "Ambivalent"]} />
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

function renderGenericSection(sectionKey, data, update, config, demographics, fullFormData, COLORS, styles, patientId, assessmentId, locked, workspacePilot = false, onNavigateToSection = undefined) {
  const u = (path, val) => update(sectionKey, path, val);
  const { title, subtitle, cards } = config;

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

  return (
    <>
      {subtitle && <p className="rnica-form-section__subtitle" style={styles.sectionSubtitle}>{subtitle}</p>}
      <div className={workspacePilot && sectionKey === "diagnoses" ? "rnica-pilot-diagnoses-grid" : undefined}>
        {cards.map((card, ci) => {
        const shouldRenderPainMap = sectionKey === "pain" && card.title === "Pain Characteristics";
        const shouldRenderSkinMap = sectionKey === "skin" && card.title === "Skin Assessment";
        const shouldRenderPainToolCard = sectionKey === "pain" && card.title === "Pain Assessment Tool" && painAssessmentMode !== "painad" && painAssessmentMode !== "flacc";
        const shouldRenderPainCharacteristicsCard = sectionKey === "pain" && card.title === "Pain Characteristics" && painAssessmentMode === "verbal";
        const shouldRenderPainadCard = sectionKey === "pain" && card.title === "PAINAD Scale (Non-verbal / unable to self-report)" && painAssessmentMode === "painad";
        const shouldRenderFlaccCard = sectionKey === "pain" && card.title === "FLACC Scale (Pediatric / child)" && painAssessmentMode === "flacc";

        if (sectionKey === "pain" && card.title === "Pain Assessment Tool" && !shouldRenderPainToolCard) {
          return null;
        }
        if (sectionKey === "pain" && card.title === "Pain Characteristics" && !shouldRenderPainCharacteristicsCard) {
          return null;
        }
        if (sectionKey === "pain" && card.title === "PAINAD Scale (Non-verbal / unable to self-report)" && !shouldRenderPainadCard) {
          return null;
        }
        if (sectionKey === "pain" && card.title === "FLACC Scale (Pediatric / child)" && !shouldRenderFlaccCard) {
          return null;
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
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <DeclineTrackerCard
                patientId={patientId}
                assessmentId={assessmentId}
                performanceData={data}
                weight={fullFormData?.vitals?.weight}
                updateField={u}
                styles={styles}
                COLORS={COLORS}
              />
            </Card>
          );
        }

        if (sectionKey === "nutrition" && card.customRenderer === "nutritionAnthropometricReference") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <NutritionAnthropometricReferenceCard fullFormData={fullFormData} styles={styles} COLORS={COLORS} />
            </Card>
          );
        }

        if (sectionKey === "nutrition" && card.customRenderer === "weightLossAutoCalc") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
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

        if (sectionKey === "vitals" && card.customRenderer === "anthropometricsAutoBmi") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <AnthropometricsAutoBmiCard data={data} updateField={u} styles={styles} COLORS={COLORS} />
            </Card>
          );
        }

        if (sectionKey === "skin" && card.customRenderer === "woundList") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <WoundListCard data={data} updateField={u} styles={styles} COLORS={COLORS} />
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

        if (sectionKey === "gastrointestinal" && card.customRenderer === "constipationAutoAssess") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
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

        if (sectionKey === "infection" && card.customRenderer === "patientAllergies") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
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
                      <span style={{ fontSize: 11.5, color: "#22c55e", fontWeight: 700 }}>✓ CHHA Plan of Care completed</span>
                    ) : (
                      <span style={{ fontSize: 11.5, color: "#f59e0b", fontWeight: 700 }}>⚠ CHHA Plan of Care not yet completed</span>
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

        return (
          <Card key={ci} id={card.id} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
            {sectionKey === "pain" && card.title === "Pain Assessment Tool" && (
              <NumericPainScale
                value={data.painIntensity?.current !== undefined && data.painIntensity?.current !== "" ? Number(data.painIntensity.current) : null}
                onChange={(score) => u("painIntensity.current", score)}
              />
            )}
            {sectionKey === "pain" && card.title === "FLACC Scale (Pediatric / child)" && (
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
            {sectionKey === "pain" && card.title === "PAINAD Scale (Non-verbal / unable to self-report)" && (
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
              <BodyMap
                value={data.painBodySites || []}
                tone="pain"
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

            <div style={styles.fieldsGrid}>
            {card.fields.map((field, fi) => {
              if (sectionKey === "pain" && (card.title === "FLACC Scale (Pediatric / child)" || card.title === "PAINAD Scale (Non-verbal / unable to self-report)")) {
                return null;
              }
              if (sectionKey === "pain" && card.title === "Pain Assessment Tool" && field.path === "assessmentTool") {
                return null;
              }
              const fieldForRender = sectionKey === "pain" && field.path === "assessmentTool"
                ? { ...field, options: getPainToolOptions(painAssessmentMode) }
                : field;
              const value = getNestedValue(data, fieldForRender.path);
              const onChange = (v) => {
                u(fieldForRender.path, v);
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
                case "input":
                  rendered = <FormInput label={fieldForRender.label} value={value} onChange={onChange}
                    type={fieldForRender.inputType} placeholder={fieldForRender.placeholder} required={fieldForRender.required} hopeCode={fieldForRender.hopeCode} />;
                  break;
                case "textarea":
                  rendered = <FormTextarea label={fieldForRender.label} value={value} onChange={onChange}
                    placeholder={fieldForRender.placeholder} rows={fieldForRender.rows} />;
                  break;
                case "select":
                  rendered = <FormSelect label={fieldForRender.label} value={value} onChange={onChange}
                    options={fieldForRender.options} required={fieldForRender.required} hopeCode={fieldForRender.hopeCode} />;
                  break;
                case "radio":
                  rendered = <FormRadioGroup label={fieldForRender.label} value={value} onChange={onChange}
                    options={fieldForRender.options} hopeCode={fieldForRender.hopeCode} sfv={fieldForRender.sfv} />;
                  break;
                case "checkboxGroup":
                  rendered = <FormCheckboxGroup label={fieldForRender.label} values={value || []} onChange={onChange}
                    options={fieldForRender.options} hopeCode={fieldForRender.hopeCode} />;
                  break;
                case "triState":
                  rendered = <FormTriState label={fieldForRender.label} value={value} onChange={onChange} hopeCode={fieldForRender.hopeCode} />;
                  break;
                case "checkbox":
                  rendered = <FormCheckbox label={fieldForRender.label} checked={value} onChange={onChange} />;
                  break;
                default:
                  rendered = null;
              }
              if (!rendered) return null;
              return <div key={fi} style={fieldSpan === "full" ? styles.fieldSpanFull : { gridColumn: `span ${fieldSpan}` }}>{rendered}</div>;
            })}
            </div>
            {POC_ENABLED_SECTIONS.has(sectionKey) && card.fields && (
              <PocSectionControls
                assessmentId={assessmentId}
                sectionKey={sectionKey}
                cardTitle={card.title}
                styles={styles}
                COLORS={COLORS}
              />
            )}
          </Card>
        );
        })}
      </div>
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
  const options = field.options || [];
  const maxLabelLen = options.reduce((m, o) => Math.max(m, String(typeof o === "string" ? o : o.label).length), 0);

  if (field.type === "textarea") {
    // Big narrative fields (explicit rows >= 4) still want real typing room;
    // short single-line-ish notes fields can share a row with a neighbor.
    return (field.rows || 3) >= 4 ? "full" : 3;
  }
  if (field.type === "radio") {
    if (options.length <= 2) return 1;
    if (options.length <= 4 && maxLabelLen <= 20) return 2;
    if (options.length <= 6) return 3;
    return "full";
  }
  if (field.type === "checkboxGroup") {
    // Now rendered as a horizontal wrapping row of pills, so it behaves
    // like a radio group: give it enough columns for its options to flow
    // across 1-2 lines instead of one cramped narrow column.
    if (options.length <= 2) return 1;
    if (options.length <= 4 && maxLabelLen <= 20) return 2;
    if (options.length <= 6) return 3;
    return "full";
  }
  return 1;
}

// Utility to get/set nested values
function getNestedValue(obj, path) {
  return path.split(".").reduce((curr, key) => curr?.[key], obj);
}

function setNestedValue(obj, path, value) {
  const clone = JSON.parse(JSON.stringify(obj));
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
        title: "Vital Signs", fields: [
          { type: "input", label: "Temperature", path: "temperature", inputType: "number", placeholder: "98.6" },
          { type: "radio", label: "Unit", path: "temperatureUnit", options: ["F", "C"] },
          { type: "input", label: "Pulse", path: "pulse", inputType: "number" },
          { type: "select", label: "Pulse Quality", path: "pulseQuality", options: ["Strong", "Weak", "Thready", "Bounding", "Irregular"] },
          { type: "input", label: "Respirations", path: "respirations", inputType: "number" },
          { type: "input", label: "BP Systolic", path: "bloodPressure.systolic", inputType: "number" },
          { type: "input", label: "BP Diastolic", path: "bloodPressure.diastolic", inputType: "number" },
          { type: "input", label: "O2 Saturation %", path: "oxygenSaturation", inputType: "number" },
          { type: "checkbox", label: "On Room Air", path: "oxygenSaturationOnRA" },
        ],
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
    subtitle: "Use the patient communication status to select the correct pain scale: verbal patients use numerical pain scoring, non-verbal patients use PAINAD or FLACC based on nurse selection, and pediatric patients use FLACC.",
    cards: [
      {
        title: "Pain Screening", hopeCode: "J0900", fields: [
          { type: "radio", label: "A. Was the patient screened for pain? (HOPE J0900.A)", path: "screenedForPain", hopeCode: "J0900", options: [
            { value: "0", label: "No — skip to Pain Active Problem (J0905)" }, { value: "1", label: "Yes" }
          ]},
          { type: "input", label: "B. Date of first screening for pain", path: "screeningDate", inputType: "date" },
          { type: "radio", label: "C. The patient's pain severity was: (HOPE J0900.C)", path: "painSeverityCategory", hopeCode: "J0900", options: [
            { value: "0", label: "None" }, { value: "1", label: "Mild" }, { value: "2", label: "Moderate" }, { value: "3", label: "Severe" }, { value: "9", label: "Pain not rated" }
          ]},
          { type: "radio", label: "D. Type of standardized pain tool used: (HOPE J0900.D)", path: "standardizedPainToolType", hopeCode: "J0900", options: [
            { value: "1", label: "Numeric" }, { value: "2", label: "Verbal descriptor" }, { value: "3", label: "Patient visual" }, { value: "4", label: "Staff observation" }, { value: "9", label: "No standardized tool used" }
          ]},
          { type: "radio", label: "Can the patient verbalize pain? (drives pain scale below, not a HOPE response)", path: "verbalizesPain", options: [
            { value: "0", label: "No" }, { value: "1", label: "Yes, reliably" }, { value: "2", label: "Sometimes" }, { value: "3", label: "Unable to determine" }
          ]},
          { type: "radio", label: "Is the patient uncomfortable because of pain?", path: "uncomfortableBecauseOfPain", options: [
            { value: "0", label: "No" }, { value: "1", label: "Yes" }, { value: "9", label: "Unable to determine" }
          ]},
          { type: "radio", label: "Does the patient have neuropathic pain (e.g., pain with burning, tingling, pins and needles, hypersensitivity to touch)? (HOPE J0915)", path: "neuropathicPain", hopeCode: "J0915", options: [
            { value: "0", label: "No" }, { value: "1", label: "Yes" }
          ]},
        ],
      },
      {
        title: "Pain Assessment Tool", fields: [
          { type: "select", label: "Pain scale selected", path: "assessmentTool", options: ["Numeric (0-10)"] },
          { type: "input", label: "Current intensity", path: "painIntensity.current", inputType: "number" },
          { type: "input", label: "Worst in 24 hours", path: "painIntensity.worst", inputType: "number" },
          { type: "input", label: "Best in 24 hours", path: "painIntensity.best", inputType: "number" },
          { type: "input", label: "Acceptable level", path: "painIntensity.acceptable", inputType: "number" },
          { type: "checkbox", label: "Comprehensive pain assessment completed", path: "comprehensiveAssessmentCompleted" },
          { type: "input", label: "Comprehensive pain assessment date", path: "comprehensiveAssessmentDate", inputType: "date" },
        ],
      },
      {
        title: "Pain Characteristics", fields: [
          { type: "checkboxGroup", label: "Pain location", path: "painLocation", options: ["Head", "Neck", "Chest", "Abdomen", "Back", "Upper extremities", "Lower extremities", "Generalized"] },
          { type: "checkboxGroup", label: "Pain character", path: "painCharacter", options: ["Sharp", "Dull", "Aching", "Burning", "Stabbing", "Throbbing", "Cramping", "Shooting", "Pressure"] },
          { type: "checkboxGroup", label: "Aggravating factors", path: "aggravatingFactors", options: ["Movement", "Coughing", "Eating", "Position change", "Touch", "Stress", "Weather"] },
          { type: "checkboxGroup", label: "Relieving factors", path: "relievingFactors", options: ["Medication", "Rest", "Heat", "Cold", "Position change", "Distraction", "Massage"] },
        ],
      },
      {
        title: "FLACC Scale (Pediatric / child)", fields: [
          { type: "select", label: "Face", path: "flacc.face", options: [{ value: "0", label: "0 — No particular expression" }, { value: "1", label: "1 — Occasional grimace or frown" }, { value: "2", label: "2 — Frequent to constant frown, clenched jaw" }] },
          { type: "select", label: "Legs", path: "flacc.legs", options: [{ value: "0", label: "0 — Normal position or relaxed" }, { value: "1", label: "1 — Uneasy, restless, tense" }, { value: "2", label: "2 — Kicking or legs drawn up" }] },
          { type: "select", label: "Activity", path: "flacc.activity", options: [{ value: "0", label: "0 — Lying quietly, normal movement" }, { value: "1", label: "1 — Squirming, shifting, tense" }, { value: "2", label: "2 — Arched, rigid, or jerking" }] },
          { type: "select", label: "Cry", path: "flacc.cry", options: [{ value: "0", label: "0 — No cry or moan" }, { value: "1", label: "1 — Moans or occasional complaint" }, { value: "2", label: "2 — Cries steadily, screams, or sobs" }] },
          { type: "select", label: "Consolability", path: "flacc.consolability", options: [{ value: "0", label: "0 — Content or relaxed" }, { value: "1", label: "1 — Reassured by touch or voice" }, { value: "2", label: "2 — Difficult to comfort or console" }] },
        ],
      },
      {
        title: "PAINAD Scale (Non-verbal / unable to self-report)", fields: [
          { type: "select", label: "Breathing", path: "painad.breathing", options: [{ value: "0", label: "0 — Normal" }, { value: "1", label: "1 — Occasional labored" }, { value: "2", label: "2 — Noisy labored" }] },
          { type: "select", label: "Vocalization", path: "painad.vocalization", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Occasional moan" }, { value: "2", label: "2 — Repeated calling out" }] },
          { type: "select", label: "Facial expression", path: "painad.facialExpression", options: [{ value: "0", label: "0 — Smiling/inexpressive" }, { value: "1", label: "1 — Sad/frightened" }, { value: "2", label: "2 — Grimacing" }] },
          { type: "select", label: "Body language", path: "painad.bodyLanguage", options: [{ value: "0", label: "0 — Relaxed" }, { value: "1", label: "1 — Tense/fidgeting" }, { value: "2", label: "2 — Rigid/striking" }] },
          { type: "select", label: "Consolability", path: "painad.consolability", options: [{ value: "0", label: "0 — No need" }, { value: "1", label: "1 — Distracted/reassured" }, { value: "2", label: "2 — Unable to console" }] },
        ],
      },
      {
        title: "Pain Management", fields: [
          { type: "checkboxGroup", label: "Non-Pharmacological Interventions", path: "nonPharmInterventions", options: ["Repositioning", "Heat therapy", "Cold therapy", "Massage", "Music therapy", "Guided imagery", "Relaxation techniques", "TENS unit", "Distraction"] },
          { type: "textarea", label: "Pain Management Plan", path: "painManagementPlan" },
        ],
      },
    ],
  },

  symptomImpact: {
    title: "Symptom Impact (J2051 A-H)",
    subtitle: "HOPE J2051 — Rate each symptom 0-3 based on impact on daily life",
    cards: [
      {
        title: "Symptom Impact Screening", hopeCode: "J2051", fields: [
          { type: "radio", label: "A. Pain", path: "pain", hopeCode: "J2051A", sfv: true, options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
          { type: "radio", label: "B. Shortness of Breath", path: "shortnessOfBreath", hopeCode: "J2051B", sfv: true, options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
          { type: "radio", label: "C. Anxiety", path: "anxiety", hopeCode: "J2051C", sfv: true, options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
          { type: "radio", label: "D. Nausea", path: "nausea", hopeCode: "J2051D", sfv: true, options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
          { type: "radio", label: "E. Vomiting", path: "vomiting", hopeCode: "J2051E", sfv: true, options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
          { type: "radio", label: "F. Diarrhea", path: "diarrhea", hopeCode: "J2051F", sfv: true, options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
          { type: "radio", label: "G. Constipation", path: "constipation", hopeCode: "J2051G", sfv: true, options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
          { type: "radio", label: "H. Agitation", path: "agitation", hopeCode: "J2051H", sfv: true, options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
          { type: "input", label: "Assessment Date", path: "assessmentDate", inputType: "date" },
        ],
      },
    ],
  },

  diagnoses: {
    title: "Diagnoses",
    subtitle: "Primary/Secondary Dx, comorbidities, disease trajectory, and LCD eligibility",
    cards: [
      {
        title: "Primary Diagnosis", hopeCode: "I0010", fields: [
          { type: "input", label: "ICD-10 Code", path: "primaryDiagnosis.icd10", required: true },
          { type: "input", label: "Description", path: "primaryDiagnosis.description", required: true },
          { type: "input", label: "Onset Date", path: "primaryDiagnosis.onsetDate", inputType: "date" },
          { type: "select", label: "HOPE Principal Diagnosis Category (I0010)", path: "primaryDiagnosis.hopeDiagnosisCategory", required: true, hopeCode: "I0010", options: [
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
          ] },
        ],
      },
      {
        title: "Terminal Prognosis", hopeCode: "J0050", fields: [
          { type: "select", label: "Terminal Prognosis", path: "terminalPrognosis", hopeCode: "J0050", options: ["6 months or less", "More than 6 months", "Undetermined"] },
        ],
      },
      {
        title: "Secondary Diagnoses",
        customRenderer: "secondaryDiagnoses",
      },
      {
        title: "LCD Eligibility",
        customRenderer: "lcdEligibility",
      },
      {
        title: "Comorbidities and Co-existing Conditions",
        hopeCode: "I0100-I8005",
        customRenderer: "hopeComorbidities",
      },
      {
        title: "LCD Supporting Evidence",
        customRenderer: "lcdSupportingEvidence",
      },
    ],
  },

  performanceStatus: {
    title: "Performance Status",
    subtitle: "PPS, KPS, ECOG, FAST, NYHA scales with justifications",
    cards: [
      {
        title: "Change Since Last Assessment",
        customRenderer: "declineTracker",
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
        title: "Functional Decline", fields: [
          { type: "textarea", label: "Functional Decline Notes", path: "functionalDeclineNotes", rows: 4 },
        ],
      },
    ],
  },

  neurological: {
    title: "Neurological / Mental / Sensory",
    subtitle: "Consciousness, orientation, cognition, BIMS (N0500-N0520), sleep/rest",
    cards: [
      {
        title: "Mental Status", hopeCode: "N0500", fields: [
          { type: "checkboxGroup", label: "Symptoms / Demeanor", path: "symptomsDemeanor", options: ["Anxiety", "Agitation", "Peaceful", "Confused", "Angry", "Restless", "Depressed", "Seizure", "Combative", "Sundowning", "Tremors / twitching", "Other"] },
          { type: "radio", label: "Level of Consciousness", path: "consciousness", options: ["Alert", "Lethargic", "Obtunded", "Stuporous", "Comatose", "Awake", "Minimally responsive", "Coma"] },
          { type: "checkbox", label: "Oriented to Time", path: "orientation.time" },
          { type: "checkbox", label: "Oriented to Place", path: "orientation.place" },
          { type: "checkbox", label: "Oriented to Person", path: "orientation.person" },
          { type: "checkbox", label: "Oriented to Situation", path: "orientation.situation" },
          { type: "checkbox", label: "Disoriented", path: "orientation.disoriented" },
        ],
      },
      {
        title: "BIMS (Brief Interview for Mental Status)", hopeCode: "N0500-N0520", fields: [
          { type: "select", label: "N0500 — Repetition", path: "hopeItems.n0500", hopeCode: "N0500", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — One word" }, { value: "2", label: "2 — Two words" }, { value: "3", label: "3 — Three words" }] },
          { type: "select", label: "N0510 — Recall", path: "hopeItems.n0510", hopeCode: "N0510", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — One" }, { value: "2", label: "2 — Two" }, { value: "3", label: "3 — Three" }] },
          { type: "select", label: "N0520 — Temporal Orientation", path: "hopeItems.n0520", hopeCode: "N0520", options: [{ value: "0", label: "0 — None correct" }, { value: "1", label: "1 — Year correct" }, { value: "2", label: "2 — Month correct" }, { value: "3", label: "3 — Day of week correct" }] },
        ],
      },
      {
        title: "Communication & Sensory", fields: [
          { type: "radio", label: "Communication", path: "communication", options: ["Clear", "Impaired", "Unable", "Normal", "Aphasia", "Slurred speech", "Speech limited to six or fewer intelligible words", "Other"] },
          { type: "radio", label: "Hearing", path: "hearing", options: ["Adequate", "Impaired", "Deaf", "Hearing aid"] },
          { type: "radio", label: "Vision", path: "vision", options: ["Adequate", "Impaired", "Blind", "Corrective lenses"] },
          { type: "radio", label: "Balance", path: "balance", options: ["Steady", "Unsteady", "Unable to stand", "Normal", "Impaired"] },
          { type: "checkboxGroup", label: "Sensory Deficits", path: "sensoryDeficits", options: ["Numbness", "Tingling", "Decreased sensation", "Phantom pain"] },
          { type: "checkboxGroup", label: "Sensory Aids", path: "sensoryAids", options: ["Glasses", "Hearing aids", "Other"] },
        ],
      },
      {
        title: "Psychiatric / Cognitive", fields: [
          { type: "input", label: "Cognition Assessment", path: "cognition" },
          { type: "checkbox", label: "Delirium", path: "delirium" },
          { type: "checkbox", label: "Seizure History", path: "seizureHistory" },
          { type: "checkboxGroup", label: "Psychiatric History", path: "psychiatricHistoryType", options: ["None", "Bipolar disorder", "OCD", "Schizophrenia", "Depression", "Other"] },
          { type: "textarea", label: "Psychiatric History Notes", path: "psychiatricHistory" },
        ],
      },
      {
        title: "Sleep / Rest", fields: [
          { type: "radio", label: "Sleep Pattern", path: "sleepRest.sleepPattern", options: ["Normal", "Insomnia", "Hypersomnia", "Fragmented", "Somnolence", "None identified", "Overly drowsy", "Excessive sleep", "Lack of sleep", "Satisfied with sleep"] },
          { type: "input", label: "Average Sleep Hours", path: "sleepRest.averageSleepHours", inputType: "number" },
          { type: "checkboxGroup", label: "Nighttime Symptoms", path: "sleepRest.nighttimeSymptoms", options: ["Pain", "Dyspnea", "Restlessness", "Confusion", "Anxiety", "Nausea", "None"] },
          { type: "checkboxGroup", label: "Sleep Aids / Current Interventions", path: "sleepRest.sleepAids", options: ["Medication", "Positioning", "White noise", "Warm milk/tea", "Other"] },
          { type: "input", label: "Response to Interventions", path: "sleepRest.response" },
          { type: "radio", label: "Restfulness", path: "sleepRest.restfulness", options: ["Adequate", "Inadequate"] },
          { type: "textarea", label: "Sleep Notes", path: "sleepRest.notes" },
        ],
      },
      {
        title: "Notes", fields: [
          { type: "textarea", label: "Neurological Notes", path: "notes", rows: 4 },
        ],
      },
    ],
  },

  cardiovascular: {
    title: "Cardiovascular",
    subtitle: "Blood pressure, pulse, edema, chest pain, circulation",
    cards: [
      { title: "Cardiovascular Assessment", fields: [
        { type: "checkboxGroup", label: "BP Symptoms", path: "bpSymptoms", options: ["Orthostatic", "Hypertensive", "Hypotensive", "Normal"] },
        { type: "checkboxGroup", label: "Pulse Sites", path: "pulseSites", options: ["Apical", "Pedal", "Radial", "Femoral"] },
        { type: "radio", label: "Pulse Quality", path: "pulseQuality", options: ["Regular", "Strong", "Weak", "Thready", "Bounding", "Irregular", "Tachycardia", "Bradycardia", "Absent"] },
        { type: "triState", label: "Edema Present", path: "edema.present" },
        { type: "checkboxGroup", label: "Edema Location", path: "edema.location", options: ["Bilateral lower extremities", "Unilateral LE", "Sacral", "Periorbital", "Upper extremities", "Generalized"] },
        { type: "radio", label: "Edema Severity", path: "edema.severity", options: ["Trace", "1+", "2+", "3+", "4+"] },
        { type: "triState", label: "Chest Pain Present", path: "chestPain.present" },
        { type: "input", label: "Chest Pain Type", path: "chestPain.type" },
        { type: "input", label: "Peripheral Circulation", path: "peripheralCirculation" },
        { type: "input", label: "Heart Sounds", path: "heartSounds" },
        { type: "triState", label: "JVD (Jugular Venous Distention)", path: "jvd" },
        { type: "input", label: "Skin Color", path: "skinColor" },
        { type: "checkbox", label: "Pacemaker", path: "pacemaker" },
        { type: "checkbox", label: "Internal Defibrillator", path: "internalDefibrillator" },
        { type: "checkbox", label: "Varicose Veins", path: "varicoseVeins" },
        { type: "checkbox", label: "Central Venous Line", path: "centralVenousLine" },
        { type: "checkbox", label: "Cool Extremities", path: "coolExtremities" },
        { type: "checkbox", label: "Stasis Ulcer", path: "stasisUlcer" },
        { type: "textarea", label: "Cardiovascular Notes", path: "notes" },
      ]},
    ],
  },

  respiratory: {
    title: "Respiratory",
    subtitle: "SOB (J2051B), lung sounds, oxygen therapy, cough assessment",
    cards: [
      { title: "Respiratory Assessment", fields: [
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
      { title: "Oxygen Therapy", fields: [
        { type: "checkbox", label: "Oxygen in Use", path: "oxygenTherapy.inUse" },
        { type: "select", label: "Delivery Type", path: "oxygenTherapy.type", options: ["Nasal cannula", "Simple mask", "Non-rebreather", "Venturi mask", "High flow"] },
        { type: "input", label: "Liters/Minute", path: "oxygenTherapy.litersPerMinute", inputType: "number" },
        { type: "input", label: "Hours/Day", path: "oxygenTherapy.hoursPerDay" },
        { type: "radio", label: "Delivery Mode", path: "oxygenTherapy.deliveryMode", options: ["Continuous", "PRN"] },
        { type: "checkbox", label: "On Room Air", path: "oxygenTherapy.onRoomAir" },
        { type: "input", label: "SpO2 on O2", path: "oxygenTherapy.satOnO2", inputType: "number" },
      ]},
      { title: "Ventilator / Airway Support", fields: [
        { type: "checkbox", label: "Short-Term Ventilator", path: "ventilator.shortTermVentilator" },
        { type: "checkbox", label: "Long-Term Ventilator", path: "ventilator.longTermVentilator" },
        { type: "input", label: "Ventilator Type and Settings", path: "ventilator.ventilatorTypeAndSettings" },
        { type: "input", label: "Tracheostomy Type", path: "ventilator.tracheostomyType" },
        { type: "input", label: "Tracheostomy Size", path: "ventilator.tracheostomySize" },
      ]},
      { title: "Notes", fields: [
        { type: "textarea", label: "Respiratory Notes", path: "notes" },
      ]},
    ],
  },

  infection: {
    title: "Immunological / Infection",
    subtitle: "Allergies, current infections, resistant-organism history, precautions",
    cards: [
      { title: "Allergies", customRenderer: "patientAllergies", fields: [] },
      { title: "Immune Status", fields: [
        { type: "checkbox", label: "Immunosuppressed", path: "immunosuppressed" },
        { type: "checkboxGroup", label: "Precautions", path: "precautions", options: ["Standard", "Contact", "Droplet", "Airborne"] },
      ]},
      { title: "Infection Assessment", fields: [
        { type: "checkboxGroup", label: "Antibiotic-Resistant Infection (current)", path: "antibioticResistantInfection", options: ["None", "MRSA", "C. difficile", "Other"] },
        { type: "checkboxGroup", label: "History of Resistant Infection", path: "historyOfResistantInfections", options: ["None", "MRSA", "C. difficile", "Other"] },
        { type: "checkboxGroup", label: "Current Active Infection", path: "currentInfections", options: ["None", "Sepsis", "UTI", "Respiratory tract", "IV site", "Wound", "HIV-related", "Pressure area", "Other"] },
      ]},
      { title: "Additional Findings", fields: [
        { type: "checkbox", label: "Antibiotic Use", path: "antibioticUse" },
        { type: "input", label: "Temperature", path: "temperature", inputType: "number", placeholder: "°F" },
        { type: "checkbox", label: "Recurrent Infection", path: "recurrentInfection" },
        { type: "textarea", label: "Infection History", path: "infectionHistory" },
        { type: "textarea", label: "Other Observations / Notes", path: "notes", placeholder: "List active infections..." },
      ]},
    ],
  },

  gastrointestinal: {
    title: "Gastrointestinal",
    subtitle: "J2051D-G (Nausea, Vomiting, Diarrhea, Constipation), bowel, feeding devices",
    cards: [
      { title: "Constipation — Auto-Suggested from Last BM Date", customRenderer: "constipationAutoAssess" },
      { title: "GI Symptoms", fields: [
        { type: "radio", label: "Nausea", path: "nausea", sfv: true, options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "radio", label: "Vomiting", path: "vomiting", sfv: true, options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "input", label: "Vomiting Occurrences (24 hours)", path: "vomitingOccurrences24h", inputType: "number" },
        { type: "radio", label: "Diarrhea", path: "diarrhea", sfv: true, options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "radio", label: "Constipation", path: "constipation", sfv: true, options: ["None", "Mild", "Moderate", "Severe"] },
      ]},
      { title: "Abdominal / Bowel Assessment", fields: [
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
      { title: "Feeding Devices", fields: [
        { type: "checkbox", label: "Feeding Tube Present", path: "feedingTube.present" },
        { type: "select", label: "Tube Type", path: "feedingTube.type", options: ["NG", "PEG", "PEJ", "G-tube", "J-tube"] },
        { type: "checkbox", label: "Ostomy Present", path: "ostomy.present" },
        { type: "select", label: "Ostomy Type", path: "ostomy.type", options: ["Colostomy", "Ileostomy", "Urostomy"] },
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
        customRenderer: "nutritionAnthropometricReference",
      },
      {
        title: "Weight Loss Auto-Calculation",
        customRenderer: "weightLossAutoCalc",
      },
      { title: "Nutritional Assessment", fields: [
        { type: "input", label: "Weight Loss (past 6 months)", path: "weightLossPastSixMonths", placeholder: "lbs or %" },
        { type: "radio", label: "Appetite", path: "appetite", options: ["Good", "Fair", "Poor", "Anorexic"] },
        { type: "input", label: "Diet Type", path: "dietType" },
        { type: "radio", label: "Fluid Intake", path: "fluidIntake", options: ["Adequate", "Decreased", "Minimal"] },
        { type: "checkboxGroup", label: "Swallowing Issues", path: "swallowingIssues", options: ["Dysphagia", "Aspiration risk", "Pocketing", "Coughing with swallowing", "None"] },
        { type: "input", label: "Oral Mucosa", path: "oralMucosa" },
        { type: "checkbox", label: "Upper Dentures", path: "dentures.upper" },
        { type: "checkbox", label: "Lower Dentures", path: "dentures.lower" },
        { type: "input", label: "Nutritional Supplements", path: "nutritionalSupplements" },
        { type: "textarea", label: "Nutrition Notes", path: "notes" },
      ]},
      { title: "NPO / Artificial Feeding", fields: [
        { type: "radio", label: "NPO Status", path: "npoStatus", options: ["Not NPO", "NPO", "NPO except meds", "Modified/thickened liquids only"] },
        { type: "checkboxGroup", label: "Artificial Feeding / Access Devices", path: "artificialFeeding", options: ["PEG", "NG", "J-tube", "Pump", "TPN", "None"] },
      ]},
      { title: "Oral Cavity", fields: [
        { type: "checkboxGroup", label: "Oral Cavity Findings", path: "oralCavityFindings", options: ["Edentulous", "Stomatitis", "Thrush", "Poor dentition", "Normal"] },
      ]},
    ],
  },
  endocrine: {
    title: "Endocrine",
    subtitle: "Impairment, thyroid, diabetes management, endocrine symptoms",
    cards: [
      { title: "Endocrine Impairment", fields: [
        { type: "checkboxGroup", label: "Impairment", path: "endocrineImpairment", options: ["Thyroid", "Parathyroid", "Pituitary", "Adrenal", "Pancreas", "None"] },
      ]},
      { title: "Thyroid Assessment", fields: [
        { type: "radio", label: "Thyroid", path: "thyroid.assessment", options: ["Normal", "Enlarged", "Tender", "Nodular", "Not assessed"] },
        { type: "textarea", label: "Thyroid Notes", path: "thyroid.notes" },
      ]},
      { title: "Diabetes Management", fields: [
        { type: "radio", label: "Diabetes Type", path: "diabetes.type", options: ["Type 1", "Type 2", "Not diabetic", "Unknown"] },
        { type: "radio", label: "Diabetes Dependency", path: "diabetes.dependency", options: ["Insulin-dependent", "Non-insulin-dependent", "Glucose-management concern", "Not applicable"] },
        { type: "select", label: "Glucose Monitoring Frequency", path: "diabetes.glucoseMonitoring", options: ["None", "Daily", "BID", "TID", "QID", "Weekly"] },
        { type: "input", label: "Last HbA1c Value", path: "diabetes.lastHbA1c" },
        { type: "input", label: "Last HbA1c Date", path: "diabetes.lastHbA1cDate", inputType: "date" },
        { type: "input", label: "Insulin Type", path: "diabetes.insulinType" },
        { type: "input", label: "Insulin Dose", path: "diabetes.insulinDose" },
        { type: "checkboxGroup", label: "Oral Hypoglycemics", path: "diabetes.oralHypoglycemics", options: ["Metformin", "Sulfonylurea", "DPP-4 inhibitor", "SGLT2 inhibitor", "None"] },
      ]},
      { title: "Endocrine Symptoms & Treatment", fields: [
        { type: "checkboxGroup", label: "Symptoms Present", path: "endocrineSymptoms", options: ["Fatigue", "Weight changes", "Temperature intolerance", "Hair/skin changes", "Polydipsia", "Polyuria", "Tremors"] },
        { type: "checkboxGroup", label: "Current Treatment", path: "currentEndocrineMeds", options: ["Levothyroxine", "Insulin", "Oral hypoglycemics", "Corticosteroid replacement", "Other endocrine medication", "None"] },
        { type: "textarea", label: "Other Observations / Notes", path: "notes" },
      ]},
    ],
  },

  genitourinary: {
    title: "Genitourinary / Reproductive",
    subtitle: "Urinary status, catheter, urine output, reproductive concerns",
    cards: [
      { title: "Urinary Status", fields: [
        { type: "radio", label: "Continence", path: "urinaryStatus", options: ["Continent", "Stress incontinence", "Urge incontinence", "Functional incontinence", "Total incontinence", "Catheterized", "Bladder program", "Urostomy", "Retention", "Painful urination", "Nocturia"] },
        { type: "input", label: "Frequency", path: "frequency" },
        { type: "checkboxGroup", label: "Urine", path: "urineCharacteristics", options: ["Clear", "Cloudy", "Pale", "Blood", "Odor"] },
        { type: "input", label: "Urine Color", path: "urineColor" },
      ]},
      { title: "Catheter Assessment", fields: [
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
      { title: "Urine Output", fields: [
        { type: "radio", label: "Output", path: "urineOutput", options: ["Adequate", "Decreased", "Anuria", "Polyuria"] },
        { type: "input", label: "24-Hour Volume (if measured)", path: "twentyFourHourVolume", inputType: "number" },
      ]},
      { title: "Reproductive Concerns", fields: [
        { type: "checkboxGroup", label: "Concerns", path: "reproductive.concerns", options: ["Vaginal bleeding", "Vaginal discharge", "Penile discharge", "Scrotal edema", "Testicular mass"] },
        { type: "textarea", label: "Reproductive Notes", path: "reproductive.notes" },
      ]},
      { title: "Bladder Management", fields: [
        { type: "checkboxGroup", label: "Interventions", path: "bladderManagement", options: ["Bladder training", "Scheduled toileting", "Pelvic floor exercises", "External collection device"] },
        { type: "textarea", label: "GU Notes", path: "notes" },
      ]},
    ],
  },

  musculoskeletal: {
    title: "Musculoskeletal",
    subtitle: "Weakness, ROM, gait, mobility status, ADL assessment",
    cards: [
      { title: "Musculoskeletal Assessment", fields: [
        { type: "radio", label: "Weakness", path: "weakness", options: ["None", "Mild", "Moderate", "Severe", "Paralysis"] },
        { type: "radio", label: "Rigidity", path: "rigidity", options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "radio", label: "Contractures", path: "contractures", options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "checkboxGroup", label: "Contracture Location", path: "contracturesLocation", options: ["Bilateral lower extremities", "Unilateral LE", "Upper extremities", "Hands/fingers", "Neck/spine", "Generalized"] },
        { type: "checkboxGroup", label: "ROM Loss Location", path: "romLimitations", options: ["Upper extremities", "Lower extremities", "Neck/spine", "Hands/fingers", "Generalized"] },
        { type: "checkboxGroup", label: "Issues", path: "musculoskeletalIssues", options: ["Joint swelling", "Spasms / cramps", "Amputation", "Prosthesis", "ROM loss", "None"] },
        { type: "radio", label: "Disability", path: "paralysis", options: ["None", "Paraplegia", "Quadriplegia", "Right hemiplegia", "Left hemiplegia", "Right hemiparesis", "Left hemiparesis"] },
        { type: "radio", label: "Gait", path: "gait", options: ["Normal", "Unsteady", "Shuffling", "Unable"] },
        { type: "checkboxGroup", label: "Assistive Devices", path: "assistiveDevices", options: ["Walker", "Wheelchair", "Cane", "Crutches", "Hospital bed", "Hoyer lift", "None"] },
      ]},
      { title: "Mobility Assessment", fields: [
        { type: "radio", label: "Ambulatory Status", path: "mobility.ambulatoryStatus", options: ["Independent", "Supervised", "Assisted", "Dependent", "Bedbound"] },
        { type: "radio", label: "Endurance", path: "mobility.endurance", options: ["Good", "Fair", "Poor"] },
        { type: "radio", label: "Transfer Ability", path: "mobility.transferAbility", options: ["Independent", "Standby assist", "1-person assist", "2-person assist", "Hoyer lift"] },
        { type: "radio", label: "Strength", path: "strength", options: ["Normal", "Decreased", "Absent"] },
        { type: "radio", label: "Balance", path: "balance", options: ["Normal", "Impaired"] },
        { type: "radio", label: "Pain with Movement", path: "painWithMovement", options: ["None", "Mild", "Moderate", "Severe"] },
      ]},
      { title: "ADL Assessment (0=Independent, 5=Dependent)", fields: [
        { type: "select", label: "Bathing", path: "adl.bathing", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup help only" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited assistance" }, { value: "4", label: "4 — Extensive assistance" }, { value: "5", label: "5 — Total dependence" }] },
        { type: "select", label: "Dressing", path: "adl.dressing", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited" }, { value: "4", label: "4 — Extensive" }, { value: "5", label: "5 — Total" }] },
        { type: "select", label: "Toileting", path: "adl.toileting", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited" }, { value: "4", label: "4 — Extensive" }, { value: "5", label: "5 — Total" }] },
        { type: "select", label: "Transferring", path: "adl.transferring", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited" }, { value: "4", label: "4 — Extensive" }, { value: "5", label: "5 — Total" }] },
        { type: "select", label: "Eating", path: "adl.eating", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited" }, { value: "4", label: "4 — Extensive" }, { value: "5", label: "5 — Total" }] },
        { type: "select", label: "Grooming", path: "adl.grooming", options: [{ value: "0", label: "0 — Independent" }, { value: "1", label: "1 — Setup" }, { value: "2", label: "2 — Supervision" }, { value: "3", label: "3 — Limited" }, { value: "4", label: "4 — Extensive" }, { value: "5", label: "5 — Total" }] },
      ]},
      { title: "Fall History & Notes", fields: [
        { type: "input", label: "Falls in Last 90 Days", path: "fallHistory.fallsLast90Days", inputType: "number" },
        { type: "input", label: "Fall Injuries", path: "fallHistory.fallInjuries" },
        { type: "textarea", label: "Musculoskeletal Notes", path: "notes" },
      ]},
    ],
  },

  skin: {
    title: "Integumentary - Skin",
    subtitle: "Integumentary assessment, Braden Scale, wound documentation (M1190)",
    cards: [
      { title: "Skin Assessment", hopeCode: "M1190", fields: [
        { type: "checkbox", label: "Skin Conditions Present", path: "skinConditionsPresent" },
        { type: "checkboxGroup", label: "Skin Status", path: "skinStatus", options: ["Intact", "Dry", "Fragile", "Edematous", "Bruising", "Rash", "Jaundice", "Cyanotic", "Mottled"] },
        { type: "radio", label: "Skin Turgor", path: "skinTurgor", options: ["Good", "Fair", "Poor", "Tenting"] },
      ]},
      { title: "Braden Scale", fields: [
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
        customRenderer: "woundList",
      },
      { title: "Wound Documentation & Notes", fields: [
        { type: "textarea", label: "Wound Impairment", path: "woundImpairment" },
        { type: "checkboxGroup", label: "Pressure-Relief Measures", path: "pressureReliefMeasures", options: ["Pressure-relief mattress", "Heel protectors/floating heels", "Cushioned wheelchair seat", "Foam/gel positioning devices", "Frequent position changes", "None in place"] },
        { type: "input", label: "Repositioning Plan", path: "repositioningPlan", placeholder: "e.g., Reposition every 2 hours, alternate sides" },
        { type: "textarea", label: "Skin Notes", path: "notes", rows: 4 },
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
        { type: "checkbox", label: "In-Person SFV Completed", path: "inPersonSfvCompleted" },
        { type: "input", label: "SFV Date", path: "sfvDate", inputType: "date" },
        { type: "input", label: "Reason SFV not completed", path: "reasonNotCompleted" },
      ]},
      { title: "SFV Symptom Impact", hopeCode: "J2053", fields: [
        { type: "radio", label: "A. Pain", path: "symptomImpactAtSfv.pain", hopeCode: "J2053A", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
        { type: "radio", label: "B. Shortness of Breath", path: "symptomImpactAtSfv.shortnessOfBreath", hopeCode: "J2053B", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
        { type: "radio", label: "C. Anxiety", path: "symptomImpactAtSfv.anxiety", hopeCode: "J2053C", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
        { type: "radio", label: "D. Nausea", path: "symptomImpactAtSfv.nausea", hopeCode: "J2053D", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
        { type: "radio", label: "E. Vomiting", path: "symptomImpactAtSfv.vomiting", hopeCode: "J2053E", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
        { type: "radio", label: "F. Diarrhea", path: "symptomImpactAtSfv.diarrhea", hopeCode: "J2053F", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
        { type: "radio", label: "G. Constipation", path: "symptomImpactAtSfv.constipation", hopeCode: "J2053G", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
        { type: "radio", label: "H. Agitation", path: "symptomImpactAtSfv.agitation", hopeCode: "J2053H", options: [{ value: "0", label: "0 — None" }, { value: "1", label: "1 — Mild" }, { value: "2", label: "2 — Moderate" }, { value: "3", label: "3 — Severe" }] },
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
    title: "Psychosocial Screening",
    subtitle: "Family/social support, patient/caregiver concerns, distress, coping",
    cards: [
      { title: "Social Support", fields: [
        { type: "radio", label: "Family/Social Support Level", path: "familySocialSupport", options: ["Strong support", "Adequate support", "Limited support", "No support", "Declined to answer"] },
        { type: "input", label: "Primary Support Person", path: "primarySupportPerson" },
        { type: "input", label: "Relationship", path: "supportRelationship" },
      ]},
      { title: "Patient Concerns", fields: [
        { type: "checkboxGroup", label: "Patient Concerns", path: "patientConcerns", options: [
          "None indicated",
          "Anxiety about illness", "Depression", "Grief/loss", "Financial concerns",
          "Family conflict", "Caregiver burden", "Social isolation", "Role changes",
          "Unfinished business", "Fear of dying", "Loss of independence", "Body image concerns",
          "Non-acceptance of diagnosis", "Potential for non-compliance", "Lack of coping skills",
          "Suicide concerns", "Substance abuse concerns", "History of emotional illness",
          "Cultural concerns", "Burial concerns", "Anger",
          "Want/need help with advance directives", "Want/need help with funeral plans"
        ]},
      ]},
      { title: "Caregiver/Family Concerns", fields: [
        { type: "checkboxGroup", label: "Caregiver Concerns", path: "caregiverFamilyConcerns", options: [
          "Anticipatory grief", "Caregiver fatigue", "Financial stress",
          "Work-life balance", "Children/family coping", "Funeral planning", "Estate/legal matters"
        ]},
      ]},
      { title: "Distress & Coping", fields: [
        { type: "select", label: "Distress Thermometer (0-10)", path: "distressRating", options: ["0","1","2","3","4","5","6","7","8","9","10"] },
        { type: "checkboxGroup", label: "Psychosocial History", path: "psychosocialHistory", options: [
          "History of depression", "History of anxiety", "History of substance abuse",
          "Current mental health treatment", "Psychiatric medications", "Previous counseling/therapy"
        ]},
        { type: "radio", label: "Coping Assessment", path: "copingAssessment", options: ["Effective coping", "Developing coping strategies", "Ineffective coping", "Crisis"] },
        { type: "textarea", label: "Coping Notes", path: "copingNotes" },
      ]},
      { title: "Intervention Plan", fields: [
        { type: "checkboxGroup", label: "Interventions", path: "interventionPlan", options: [
          "Counseling referral", "Support group", "Community resources", "Crisis intervention", "Psychiatric evaluation"
        ]},
        { type: "checkbox", label: "Social Work Visit Needed", path: "socialWorkVisitNeeded" },
        { type: "textarea", label: "Psychosocial Notes", path: "notes" },
      ]},
    ],
  },

  spiritual: {
    title: "Spiritual Screening",
    subtitle: "Patient/caregiver faith, spiritual concerns, chaplain needs",
    cards: [
      { title: "Spiritual Assessment", fields: [
        { type: "checkbox", label: "Patient Active in Faith Tradition", path: "patientActiveInFaithTradition" },
        { type: "input", label: "Patient Faith Tradition", path: "patientFaith" },
        { type: "checkbox", label: "Caregiver Active in Faith Tradition", path: "caregiverActiveInFaithTradition" },
        { type: "input", label: "Caregiver Faith Tradition", path: "caregiverFaith" },
        { type: "checkboxGroup", label: "Spiritual Concerns", path: "spiritualConcerns", options: [
          "Meaning of illness", "Forgiveness", "Hope", "Legacy", "Prayer requests",
          "Religious rituals", "Afterlife concerns", "Anger at God", "Spiritual distress",
          "Fear", "Hopelessness"
        ]},
        { type: "select", label: "Spiritual Distress Rating (0-10)", path: "spiritualDistressRating", options: ["0","1","2","3","4","5","6","7","8","9","10"] },
        { type: "checkbox", label: "Spiritual / existential concerns asked", path: "concernsDiscussed" },
        { type: "radio", label: "F3000: Was patient and/or caregiver asked about spiritual/existential concerns?", path: "concernsAskedStatus", hopeCode: "F3000",
          options: [{ value: "0", label: "No" }, { value: "1", label: "Yes, and discussion occurred" }, { value: "2", label: "Yes, but refused to discuss" }] },
        { type: "input", label: "Spiritual concerns discussion date", path: "concernsDiscussedDate", inputType: "date" },
        { type: "checkbox", label: "Chaplain Referral Needed", path: "chaplainNeeded" },
        { type: "textarea", label: "Spiritual Notes", path: "notes" },
      ]},
    ],
  },

  bereavement: {
    title: "Bereavement Screening",
    subtitle: "Patient/caregiver bereavement concerns, risk assessment",
    cards: [
      { title: "Bereavement Assessment", fields: [
        { type: "checkboxGroup", label: "Patient Concerns", path: "patientConcerns", options: [
          "Fear of death", "Unresolved grief", "Existential distress", "Legacy concerns", "Family preparedness",
          "Multiple losses", "Active grieving"
        ]},
        { type: "checkboxGroup", label: "Caregiver Concerns", path: "caregiverConcerns", options: [
          "Anticipatory grief", "Previous losses", "Complicated grief history",
          "Mental health concerns", "Substance abuse history", "Social isolation", "Concurrent stressors",
          "Multiple losses", "Active grieving"
        ]},
        { type: "radio", label: "Bereavement Risk Level", path: "bereavementRisk", options: ["Low", "Moderate", "High"] },
        { type: "checkbox", label: "Bereavement Visit Needed", path: "bereavementVisitNeeded" },
        { type: "textarea", label: "Bereavement Notes", path: "notes" },
      ]},
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
  const isOngoing = mode === "ongoing";
  const [assessmentType, setAssessmentType] = useState("update");
  const autosavePatientId = resolvedPatientId || patientId || "";
  // Admission Action Center (Phase A) — global drawer, reachable from every
  // section via the persistent footer button. No draft loss / navigation:
  // opening/closing this never touches `formData` or `activeSection`.
  const [actionCenterOpen, setActionCenterOpen] = useState(false);

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
  });
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  const routes = useMemo(() => {
    const orderedRoutes = workspacePilot ? PILOT_ROUTES : LEGACY_ROUTES;
    // SFV (Symptom Follow-Up Visit) is always its own separate visit -- HOPE
    // requires it to occur within 2 calendar days of the RN Initial
    // Comprehensive Assessment as a distinct documented visit, never filled
    // out inside the RNICA itself (initial or ongoing/recert).
    return orderedRoutes.filter((route) => route.key !== "sfv");
  }, [workspacePilot]);
  const sidebarConfigItems = useMemo(() => {
    const items = SIDEBAR_CONFIG.filter((item) => item.key !== "sfv");
    return isOngoing ? items.map((item) => ({ ...item, hope: [] })) : items;
  }, [isOngoing]);

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
      return undefined;
    }

    let mounted = true;
    const loadAssessment = existingAssessmentId
      ? api.getRNICAAssessment(existingAssessmentId)
      : api.getRNICAAssessmentByPatient(activePatientId);

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
          const merged = deepMergeFormData(INITIAL_FORM, data.formData);
          setFormData(merged);
          markPersisted(merged, data.assessmentId || existingAssessmentId);
        }
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
      });

    return () => {
      mounted = false;
    };
  }, [existingAssessmentId, markPersisted, patientId, refreshIntelligence, resolvedPatientId]);

  useEffect(() => {
    if (assessmentId) {
      refreshIntelligence(assessmentId);
    }
  }, [assessmentId, refreshIntelligence]);

  // Auto-validate on change
  useEffect(() => {
    setValidation(validateRNICA(formData, mode));
  }, [formData, mode]);

  useEffect(() => {
    onFormDataChange?.(formData);
  }, [formData, onFormDataChange]);

  // Deep update helper
  const updateField = useCallback((section, path, value) => {
    setFormData((prev) => {
      const next = { ...prev };
      next[section] = setNestedValue(prev[section], path, value);
      return next;
    });
    setSaveStatus(null);
  }, []);

  // Auto-derive all HOPE J2051 A-H Symptom Impact ratings from the
  // clinical sections elsewhere in this same RNICA where each symptom is
  // already assessed -- the RN shouldn't have to re-check something that
  // was already documented. Each value only fills in while the Symptom
  // Impact field is still blank, so a deliberate manual entry in Symptom
  // Impact (which may legitimately differ) is never overwritten.
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
    // symptomsDemeanor is a presence checklist, not a graded scale -- a
    // checked box only tells us the symptom is present, so it's mapped to
    // "1 - Mild" as a conservative starting point the RN can still adjust.
    const derived = {
      pain: ["0", "1", "2", "3"].includes(String(painSeverity)) ? String(painSeverity) : undefined,
      shortnessOfBreath: severityMap[formData.respiratory?.sobSeverity],
      anxiety: demeanor.includes("Anxiety") ? "1" : undefined,
      nausea: severityMap[formData.gastrointestinal?.nausea],
      vomiting: severityMap[formData.gastrointestinal?.vomiting],
      diarrhea: severityMap[formData.gastrointestinal?.diarrhea],
      constipation: severityMap[formData.gastrointestinal?.constipation],
      agitation: demeanor.includes("Agitation") ? "1" : undefined,
    };

    setFormData((prev) => {
      const current = prev.symptomImpact || {};
      let next = current;
      let changed = false;
      for (const key of Object.keys(derived)) {
        if (!current[key] && derived[key] !== undefined) {
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
    ? "Update Recert Assessment"
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
    const v = validateRNICA(formData, mode);
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
  const completedSections = useMemo(() => {
    const completed = [];
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
        const hasContent = JSON.stringify(sectionData) !== JSON.stringify(initialSectionData);
        if (hasContent) completed.push(route.key);
      }
    });
    return completed;
  }, [formData, routes, workspacePilot]);

  useEffect(() => {
    if (!routes.some((route) => route.key === activeSection)) {
      setActiveSection(routes[0]?.key || "demographics");
    }
  }, [activeSection, routes]);

  // Current route
  const currentRoute = routes.find((r) => r.key === activeSection);
  const currentSectionData = formData[currentRoute?.formSection];
  const sidebarConfig = sidebarConfigItems.find((s) => s.key === activeSection);
  const sfvStatus = useMemo(() => getSfvStatus(formData), [formData]);
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
    const isComplete = completedSections.includes(route.key);
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
            {isComplete && <span style={{ fontSize: 11, fontWeight: 700, color: COLORS.success }}>&#10003; Complete</span>}
          </div>
          {!open && (
            <span style={{ fontSize: 11, color: COLORS.gray }}>
              {isComplete ? "Documented — tap to review" : "Not started — tap to document"}
            </span>
          )}
        </div>
        {open && (
          <div style={{ padding: 16, contentVisibility: "auto", containIntrinsicSize: "600px" }}>
            {isDemo
              ? renderDemographics(formData.demographics, updateField, COLORS, styles)
              : config && sectionData
                ? renderGenericSection(route.formSection, sectionData, updateField, config, formData.demographics, formData, COLORS, styles, patientId, assessmentId, locked, false, onNavigateToSection)
                : <div style={styles.card}><p style={{ color: COLORS.gray }}>Section "{route.key}" — content loading...</p></div>}
          </div>
        )}
      </div>
    );
  });

  const renderWorkspaceSections = () => routes.map((route) => {
    const config = SECTION_CONFIGS[route.formSection];
    const sectionData = formData[route.formSection];
    const isDemographicsModule = ["demographics", "caregiverAssessment", "advancedCarePlanning"].includes(route.key);
    const content = isDemographicsModule
      ? renderDemographics(formData.demographics, updateField, COLORS, styles, route.key)
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
          )
        : <div style={styles.card}><p style={{ color: COLORS.gray }}>Section "{route.key}" — content loading...</p></div>;

    return (
      <div key={route.key} hidden={route.key !== activeSection} aria-hidden={route.key !== activeSection}>
        {content}
      </div>
    );
  });

  if (workspacePilot) {
    const secondaryDiagnoses = (formData.diagnoses.secondaryDiagnoses || [])
      .map((diagnosis) => `${diagnosis.description || diagnosis.icd10 || ""}`.trim())
      .filter(Boolean)
      .join(", ");
    const verifiedComorbidities = Object.entries(formData.diagnoses.hopeComorbidities || {})
      .filter(([, selected]) => selected === true)
      .map(([key]) => key)
      .join(", ");
    const commandRoutes = routes.map((route) => ({
      ...route,
      label: route.label || sidebarConfigItems.find((item) => item.key === route.key)?.label || route.nav,
      regulator: isOngoing && route.regulator === "HOPE" ? undefined : route.regulator,
    }));

    return (
      <AssessmentModeContext.Provider value={mode}>
        <RNICACommandWorkspace
          patient={{
            name: patientSummary?.patient?.full_name || (resolvedPatientId ? "Loading patient..." : "No patient selected"),
            mrn: patientSummary?.patient?.mrn || "Not available",
            primaryDiagnosis: formData.diagnoses.primaryDiagnosis.description || patientSummary?.patient?.primary_diagnosis || "",
            secondaryDiagnoses,
            comorbidities: verifiedComorbidities,
            priorIssues: patientSummary
              ? `${patientSummary.incident_summary.total} incident(s), ${patientSummary.communication_summary.total} communication item(s)`
              : "Patient record summary loading",
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
          renderWorkspaceSections={renderWorkspaceSections}
          visitRecorder={(
            <VisitRecorderCard
              patientId={resolvedPatientId || patientId}
              assessmentId={assessmentId}
              assessmentType={isOngoing ? "RN_RECERT" : "RNICA"}
              COLORS={COLORS}
              styles={styles}
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
              : "MRN: 94731 | DOB: 11/15/1941 (84F) | Lung Cancer (C34.90), CHF, COPD"}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 13, fontWeight: 600 }}>RN ICA</div>
          <div style={styles.bannerMeta}>Dr. James Olsen | Sarah Mitchell, RN, BSN</div>
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
                  diagnosis: "Lung cancer (C34.90), CHF, COPD",
                  painSummary: "Pain and symptom review ongoing; support needs and caregiver concerns require coordinated follow-up across the chart.",
                  primaryProvider: "Dr. James Olsen",
                  hnpStatus: "Updated 2 days ago",
                  lastVisit: "3 days ago",
                  disciplineHistory: [
                    "History & Physical — admission summary",
                    "Nursing Assessment — clinical status and safety review",
                    "Spiritual Assessment — coping and chaplain support",
                    "Psychosocial Assessment — caregiver burden and support needs",
                    "Tx / Meds / DME / Supplies — active orders and equipment",
                    "IDG — interdisciplinary group review",
                    "Plan of Care (POC) — current goals and revisions",
                    "Documents — uploaded patient records and external supporting files",
                  ],
                  careTeam: ["RN", "MSW", "SC", "MD", "Chaplain", "Admin"],
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
              style={{ ...styles.btnSecondary, color: COLORS.error || "#dc2626", borderColor: COLORS.error || "#dc2626" }}
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
