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
 *          teachingNeeds, admissionsOrder, ordersHub, referrals, finalization
 *
 * Color System: HOPE = GREEN (#059669), SFV = RED (#DC2626), CMS = BLUE (#2563EB)
 * Accent: Teal (#0D9488)
 */

import React, { useState, useCallback, useMemo, useEffect, useContext, useRef } from "react";
import { useNavigate } from "react-router-dom";
import frontBody from "../assets/body-map/front.png";
import backBody from "../assets/body-map/back.png";
import { fetchPatientSummary } from "../api/patientCharts";
import { fetchCensusWorkspace } from "../api/census";
import {
  saveRnicaAssessment,
  getRnicaAssessment,
  getRnicaAssessmentByPatient,
  updateRnicaAssessment,
  lockRnicaAssessment,
  getRnicaIntelligence,
  viewRnicaSectionPoc,
  addRnicaSectionPocProblem,
  updateRnicaSectionPocProblem,
  resolveRnicaSectionPocProblem,
} from "../api/icaAssessments";
import { detectLCD, evaluateLCD, getLCDConfig } from "../api/eligibility";
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
import { fetchPerformanceHistory } from "../api/facesheet";
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
import { getSfvStatus } from "../intake/hopeReportMapper";

import { getActivePatientId, setActivePatientId, clearActivePatientId } from "../utils/activePatient";
import MedicationNameInput from "./MedicationNameInput";
import VisitRecorderCard from "./VisitRecorderCard";
// ════════════════════════════════════════════════════════════════
// 1. CONSTANTS & CONFIGURATION
// ════════════════════════════════════════════════════════════════

const API_BASE = "/visits/rnica";

export function getRnicaColors(mode) {
  if (mode === "light") {
    return {
      navy: "#1E3A5F",
      hope: "#059669",
      sfv: "#DC2626",
      cms: "#2563EB",
      teal: "#0D9488",
      dark: "#0F172A",
      gray: "#64748B",
      border: "#D8E3E8",
      bg: "#F8FAFC",
      white: "#FFFFFF",
      warning: "#F59E0B",
      error: "#EF4444",
      success: "#10B981",
      pageBg: "#EEF3F8",
      sidebarBg: "#F8FBFD",
      sidebarItemColor: "#334155",
      sidebarActiveColor: "#0F766E",
      panelBg: "rgba(255,255,255,0.96)",
      inputBg: "#FFFFFF",
      hopeTagBg: "#ECFDF5",
      sfvTagBg: "#FEF2F2",
      cmsTagBg: "#EFF6FF",
      infoBoxBg: "linear-gradient(135deg, #eef6ff, #eefaf8)",
      warningBoxBg: "linear-gradient(135deg, #fffbeb, #fff7ed)",
      successBoxBg: "linear-gradient(135deg, #ecfdf5, #f0fdf4)",
      mapControlBg: "#F8FAFC",
      mapControlBorder: "#E2E8F0",
      mapChipBg: "#FFFFFF",
      mapChipText: "#0F172A",
      mapMuted: "#475569",
      tealBg: "#CCFBF1",
      amberTagBg: "#FFFBEB",
    };
  }
  return {
    navy: "#1E3A5F",
    hope: "#34d399",
    sfv: "#f87171",
    cms: "#60a5fa",
    teal: "#10b7a2",
    dark: "#e2e8f0",
    gray: "#94a3b8",
    border: "#334155",
    bg: "#0f172a",
    white: "#1e293b",
    warning: "#f59e0b",
    error: "#f87171",
    success: "#34d399",
    pageBg: "#0f172a",
    sidebarBg: "#0b1220",
    sidebarItemColor: "#cbd5e1",
    sidebarActiveColor: "#5eead4",
    panelBg: "rgba(30, 41, 59, 0.9)",
    inputBg: "#1e293b",
    hopeTagBg: "rgba(52, 211, 153, 0.16)",
    sfvTagBg: "rgba(248, 113, 113, 0.16)",
    cmsTagBg: "rgba(96, 165, 250, 0.16)",
    infoBoxBg: "linear-gradient(135deg, rgba(30,58,95,0.35), rgba(13,148,136,0.15))",
    warningBoxBg: "linear-gradient(135deg, rgba(245,158,11,0.18), rgba(249,115,22,0.12))",
    successBoxBg: "linear-gradient(135deg, rgba(16,185,129,0.18), rgba(52,211,153,0.12))",
    mapControlBg: "#1e293b",
    mapControlBorder: "#334155",
    mapChipBg: "#0f172a",
    mapChipText: "#e2e8f0",
    mapMuted: "#94a3b8",
    tealBg: "rgba(16, 183, 162, 0.18)",
    amberTagBg: "rgba(245, 158, 11, 0.16)",
  };
}

const AssessmentModeContext = React.createContext("ica");

const NAV_SECTIONS = [
  "Patient Demographics", "Vitals", "Pain Assessment", "Symptom Impact",
  "Diagnoses", "Performance Status", "Neurological", "Cardiovascular",
  "Respiratory", "Infection", "Gastrointestinal", "Nutrition",
  "Endocrine", "Genitourinary",
  "Musculoskeletal", "Skin / Wounds", "Imminent Death", "SFV",
  "Safety", "Psychosocial", "Spiritual", "Bereavement",
  "Personal Care", "Teaching Needs", "Admissions Order",
  "Hospice Orders Hub", "Referrals", "Finalization",
];

const ROUTES = [
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
  { key: "skin",              nav: "Skin / Wounds",         formSection: "skin" },
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
  { key: "ordersHub",         nav: "Hospice Orders Hub",    formSection: "medications",
    subViews: ["ordersList","orderEntry","medReconciliation","startedStoppedLog"] },
  { key: "referrals",         nav: "Referrals",             formSection: "referrals" },
  { key: "finalization",      nav: "Finalization",          formSection: "finalization" },
];

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
  { key: "skin",              label: "Skin / Wounds",         icon: "🩹", hope: ["M1190"],                  color: "green" },
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
  { key: "ordersHub",         label: "Hospice Orders Hub",    icon: "📋", hope: [],                         color: null,
    orderCategories: ["Meds","DME","Supplies","Lab","Treatment","Diet","Other"],
    features: ["eRx","phoneOrderReadBack","medReconciliation","compounding","startedStoppedLog"] },
  { key: "referrals",         label: "Referrals",             icon: "🔗", hope: [],                         color: null },
  { key: "finalization",      label: "Finalization",          icon: "✅",    hope: ["F2000","F2100","F2200"],   color: "green" },
];

const FORM_REGISTRY = [
  "demographics", "vitals", "pain", "symptomImpact", "diagnoses",
  "performanceStatus", "neurological", "cardiovascular", "respiratory",
  "infection", "gastrointestinal", "nutrition", "endocrine", "genitourinary",
  "musculoskeletal", "skin", "imminentDeath", "sfv", "safety",
  "psychosocial", "spiritual", "bereavement", "personalCare", "teachingNeeds",
  "admissionsOrder", "ordersHub", "referrals", "finalization",
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

// Default visit frequency disciplines for Admissions Order
const DEFAULT_VISIT_DISCIPLINES = [
  { discipline: "SN", label: "Skilled Nursing", frequency: "", duration: "per Week", prnVisits: "" },
  { discipline: "HA", label: "Home Aide", frequency: "", duration: "per Week", prnVisits: "" },
  { discipline: "MSW", label: "Medical Social Worker", frequency: "", duration: "", prnVisits: "" },
  { discipline: "SC", label: "Spiritual Counselor", frequency: "", duration: "", prnVisits: "" },
  { discipline: "RN-SUP", label: "RN Supervisory", frequency: "", duration: "every 14 days", prnVisits: "" },
];

const BODY_MAP_REGIONS = {
  front: [
    { id: "head", label: "Head", x: 110, y: 32, r: 18 },
    { id: "neck", label: "Neck", x: 110, y: 68, r: 12 },
    { id: "shoulders", label: "Shoulders", x: 110, y: 102, r: 16 },
    { id: "chest", label: "Chest", x: 110, y: 138, r: 18 },
    { id: "abdomen", label: "Abdomen", x: 110, y: 188, r: 18 },
    { id: "pelvis", label: "Pelvis", x: 110, y: 236, r: 16 },
    { id: "right-arm", label: "R Arm", x: 52, y: 156, r: 16 },
    { id: "left-arm", label: "L Arm", x: 168, y: 156, r: 16 },
    { id: "right-leg", label: "R Leg", x: 88, y: 300, r: 18 },
    { id: "left-leg", label: "L Leg", x: 132, y: 300, r: 18 },
    { id: "right-foot", label: "R Foot", x: 88, y: 372, r: 14 },
    { id: "left-foot", label: "L Foot", x: 132, y: 372, r: 14 },
  ],
  back: [
    { id: "head", label: "Head", x: 110, y: 32, r: 18 },
    { id: "neck", label: "Neck", x: 110, y: 68, r: 12 },
    { id: "shoulders", label: "Shoulders", x: 110, y: 102, r: 16 },
    { id: "upper-back", label: "Upper Back", x: 110, y: 138, r: 18 },
    { id: "lower-back", label: "Lower Back", x: 110, y: 192, r: 18 },
    { id: "buttocks", label: "Buttocks", x: 110, y: 238, r: 16 },
    { id: "right-arm", label: "R Arm", x: 52, y: 156, r: 16 },
    { id: "left-arm", label: "L Arm", x: 168, y: 156, r: 16 },
    { id: "right-leg", label: "R Leg", x: 88, y: 300, r: 18 },
    { id: "left-leg", label: "L Leg", x: 132, y: 300, r: 18 },
    { id: "right-foot", label: "R Foot", x: 88, y: 372, r: 14 },
    { id: "left-foot", label: "L Foot", x: 132, y: 372, r: 14 },
  ],
};


// ════════════════════════════════════════════════════════════════
// 2. INITIAL_FORM — Complete State Shape (28 sections)
// ════════════════════════════════════════════════════════════════

const INITIAL_FORM = {
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
    neuropathicPain: false,
    screeningDate: "",
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
    primaryDiagnosis: { icd10: "", description: "", onsetDate: "" },
    secondaryDiagnoses: [],
    comorbidities: [],
    terminalPrognosis: "",
    diseaseTrajectory: "",
    lcdEligibilityNarrative: "",
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
    orientation: { time: false, place: false, person: false, situation: false },
    communication: "", hearing: "", vision: "", balance: "",
    cognition: "", delirium: false, seizureHistory: false,
    psychiatricHistory: "",
    sensoryDeficits: [],
    sleepRest: {
      sleepPattern: "", averageSleepHours: "",
      sleepAids: [], restfulness: "", notes: "",
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
    nausea: "", vomiting: "", diarrhea: "", constipation: "",
    bowelSounds: "", abdomen: "", bowelStatus: "", lastBM: "",
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
    catheter: {
      present: false, type: "", size: "",
      insertionDate: "", lastChangeDate: "",
      condition: "", urineCharacteristics: [],
    },
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
    firearmInHome: false,
    oxygenInUse: false, oxygenSafetyReviewed: false,
    disasterLevel: "",
    disasterLevelOneConditions: [],
    disasterLevelTwoConditions: [],
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

  // ─── 26. ORDERS HUB (medications) ─────────────────
  medications: {
    scheduledOpioid: false, scheduledOpioidDate: "",
    prnOpioid: false, prnOpioidDate: "",
    bowelRegimen: false, bowelRegimenDate: "",
    currentMedications: [],
    orders: [],
    medReconciliation: { completed: false, completedDate: "", completedBy: "" },
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
  },

  // ─── 28. FINALIZATION ─────────────────────────────
  finalization: {
    completedSections: [],
    incompleteCount: 0,
    // Gap #3 — Response to Interventions (CDPH: assessment-to-assessment change baseline)
    responseToInterventions: {
      initialResponseSummary: "",
      interventionEffectiveness: [],
      baselineEstablished: false,
      baselineDate: "",
      progressNotes: "",
    },
    // Gap #4 — POC Auto-Generation (CDPH: every problem → Problem/Goal/Intervention/Discipline)
    pocEntries: [],
    pocDraft: { problem: "", goal: "", intervention: "", discipline: "" },
    pocGenerationCompleted: false,
    pocReviewedWithIdg: false,
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

// ════════════════════════════════════════════════════════════════
// 3. API SERVICE — 4 Backend Endpoints
// ════════════════════════════════════════════════════════════════

// Delegates to the shared client so requests carry the auth token.
const api = {
  saveRNICAAssessment: (patientId, formData) =>
    saveRnicaAssessment({ patientId, formData }),
  getRNICAAssessment: (assessmentId) => getRnicaAssessment(assessmentId),
  getRNICAAssessmentByPatient: (patientId) => getRnicaAssessmentByPatient(patientId),
  updateRNICAAssessment: (assessmentId, formData) =>
    updateRnicaAssessment(assessmentId, formData),
  lockRNICAAssessment: (assessmentId) => lockRnicaAssessment(assessmentId),
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

    // Advanced Care Planning ? HOPE required
    if (!formData.demographics.advancedCarePlanning.codeStatus) {
      errors["demographics.advancedCarePlanning.codeStatus"] = "F2000: Code status is required";
    }
    if (!formData.demographics.advancedCarePlanning.lifeSustainingTreatmentPreference) {
      errors["demographics.advancedCarePlanning.lifeSustainingTreatmentPreference"] = "F2100: Life-sustaining treatment preference required";
    }
    if (!formData.demographics.advancedCarePlanning.hospitalizationPreference) {
      errors["demographics.advancedCarePlanning.hospitalizationPreference"] = "F2200: Hospitalization preference required";
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

  // CDPH Gap #4 ? POC entries from assessment
  if (!formData.finalization.pocGenerationCompleted) {
    warnings["finalization.pocGenerationCompleted"] = "CDPH: POC generation from assessment problems required before lock";
  }

  if (includeHopeRequirements) {
    // Pain ? HOPE J0900, J0915
    if (!formData.pain.verbalizesPain) {
      warnings["pain.verbalizesPain"] = "HOPE J0900: Pain verbalization required";
    }
    if (!formData.pain.uncomfortableBecauseOfPain) {
      warnings["pain.uncomfortableBecauseOfPain"] = "HOPE J0915: Uncomfortable because of pain required";
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

  // Admissions Order ? Level of Care required
  if (!formData.admissionsOrder.levelOfCare.level) {
    errors["admissionsOrder.levelOfCare"] = "Level of Care is required for admission";
  }

  // Admissions Order ? T.O. Verification
  if (!formData.admissionsOrder.toVerification.verbalOrderReadBack) {
    errors["admissionsOrder.toVerification"] = "Verbal order read-back verification required";
  }

  // Finalization ? signature
  if (!formData.finalization.clinicianSignature) {
    errors["finalization.clinicianSignature"] = "Clinician signature required";
  }

  return { errors, warnings, isValid: Object.keys(errors).length === 0 };
}


// ════════════════════════════════════════════════════════════════
// 5. HELPER COMPONENTS
// ════════════════════════════════════════════════════════════════

// ── Shared Styles ──
export function getRnicaStyles(COLORS) {
  return {
    page: {
      display: "flex",
      flexDirection: "column",
      minHeight: "100vh",
      height: "auto",
      fontFamily: "Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
      color: COLORS.dark,
      background: COLORS.pageBg,
    },
    banner: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "14px 24px",
      background: "linear-gradient(90deg, #1E3A5F 0%, #0D9488 100%)",
      color: "#FFFFFF",
      fontSize: 13,
      boxShadow: "0 4px 16px rgba(15, 23, 42, 0.12)",
      borderBottom: "1px solid rgba(148, 163, 184, 0.2)",
    },
    bannerName: { fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" },
    bannerMeta: { fontSize: 12, opacity: 0.82, letterSpacing: "0.01em" },
    workspace: { display: "flex", flex: 1, minHeight: 0, minWidth: 0, overflow: "visible" },
    sidebar: {
      width: 220,
      background: COLORS.sidebarBg,
      borderRight: `1px solid ${COLORS.border}`,
      overflowY: "auto",
      padding: "12px 8px",
      flexShrink: 0,
      minHeight: 0,
    },
    sidebarItem: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      padding: "6px 10px",
      margin: "2px 0",
      fontSize: 12.5,
      cursor: "pointer",
      borderRadius: 8,
      borderLeft: "3px solid transparent",
      transition: "all 0.2s ease",
      color: COLORS.sidebarItemColor,
    },
    sidebarActive: {
      background: "linear-gradient(90deg, rgba(13,148,136,0.18), rgba(13,148,136,0.05))",
      borderLeftColor: COLORS.teal,
      color: COLORS.sidebarActiveColor,
      fontWeight: 700,
      boxShadow: "inset 0 0 0 1px rgba(13,148,136,0.08)",
    },
    mainArea: { flex: 1, display: "flex", minHeight: 0, minWidth: 0, overflow: "visible" },
    content: { flex: 1, overflowY: "auto", overflowX: "hidden", minHeight: 0, minWidth: 0, padding: "24px 28px 32px" },
    rightPanel: {
      width: 290,
      background: COLORS.panelBg,
      borderLeft: `1px solid ${COLORS.border}`,
      overflowY: "auto",
      padding: 18,
      flexShrink: 0,
      backdropFilter: "blur(10px)",
      minHeight: 0,
    },
    card: {
      background: COLORS.white,
      borderRadius: 10,
      border: `1px solid ${COLORS.border}`,
      padding: 12,
      marginBottom: 10,
      boxShadow: "0 2px 10px rgba(15, 23, 42, 0.03)",
    },
    cardTitle: {
      fontSize: 14,
      fontWeight: 800,
      marginBottom: 8,
      color: COLORS.dark,
      letterSpacing: "-0.01em",
    },
    sectionTitle: { fontSize: 18, fontWeight: 800, marginBottom: 3, letterSpacing: "-0.02em", color: COLORS.dark },
    sectionSubtitle: { fontSize: 12, color: COLORS.gray, marginBottom: 12, lineHeight: 1.4 },
    formGroup: { marginBottom: 10 },
    fieldsGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "0px 16px", alignItems: "start" },
    fieldSpanFull: { gridColumn: "1 / -1" },
    stackedFields: { display: "flex", flexDirection: "column", gap: 10 },
    label: { display: "block", fontSize: 12.5, fontWeight: 700, marginBottom: 4, color: COLORS.dark, lineHeight: 1.3 },
    input: {
      width: "100%",
      padding: "7px 10px",
      border: `1px solid ${COLORS.border}`,
      borderRadius: 8,
      fontSize: 13.5,
      boxSizing: "border-box",
      background: COLORS.inputBg,
      color: COLORS.dark,
      transition: "border-color 0.2s ease, box-shadow 0.2s ease",
      boxShadow: "inset 0 1px 3px rgba(15, 23, 42, 0.03)",
    },
    textarea: {
      width: "100%",
      padding: "7px 10px",
      border: `1px solid ${COLORS.border}`,
      borderRadius: 8,
      fontSize: 13.5,
      minHeight: 60,
      resize: "vertical",
      boxSizing: "border-box",
      background: COLORS.inputBg,
      color: COLORS.dark,
      boxShadow: "inset 0 1px 3px rgba(15, 23, 42, 0.03)",
    },
    select: {
      width: "100%",
      padding: "7px 10px",
      border: `1px solid ${COLORS.border}`,
      borderRadius: 8,
      fontSize: 13.5,
      background: COLORS.inputBg,
      color: COLORS.dark,
      boxSizing: "border-box",
      boxShadow: "inset 0 1px 3px rgba(15, 23, 42, 0.03)",
    },
    radioGroup: { display: "flex", gap: 12, flexWrap: "wrap" },
    radioLabel: { display: "flex", alignItems: "center", gap: 5, fontSize: 12.5, cursor: "pointer", color: COLORS.dark },
    checkboxGroup: { display: "flex", flexDirection: "row", flexWrap: "wrap", gap: "4px 14px" },
    checkboxLabel: { display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, cursor: "pointer", color: COLORS.dark },
    hopeTag: { display: "inline-block", padding: "3px 8px", borderRadius: 999, fontSize: 10, fontWeight: 800, background: COLORS.hopeTagBg, color: COLORS.hope, letterSpacing: "0.03em", textTransform: "uppercase" },
    sfvTag: { display: "inline-block", padding: "3px 8px", borderRadius: 999, fontSize: 10, fontWeight: 800, background: COLORS.sfvTagBg, color: COLORS.sfv, letterSpacing: "0.03em", textTransform: "uppercase" },
    cmsTag: { display: "inline-block", padding: "3px 8px", borderRadius: 999, fontSize: 10, fontWeight: 800, background: COLORS.cmsTagBg, color: COLORS.cms, letterSpacing: "0.03em", textTransform: "uppercase" },
    statusBadge: { display: "inline-flex", alignItems: "center", gap: 4, padding: "5px 10px", borderRadius: 999, fontSize: 12, fontWeight: 700, letterSpacing: "0.04em", textTransform: "uppercase" },
    btnPrimary: { padding: "11px 18px", background: "linear-gradient(135deg, #0D9488 0%, #0F766E 100%)", color: "#FFFFFF", border: "none", borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: "pointer", boxShadow: "0 8px 18px rgba(13, 148, 136, 0.2)" },
    btnSecondary: { padding: "11px 18px", background: COLORS.white, color: COLORS.dark, border: `1px solid ${COLORS.border}`, borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: "pointer", boxShadow: "0 4px 12px rgba(15, 23, 42, 0.03)" },
    btnDanger: { padding: "11px 18px", background: "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)", color: "#FFFFFF", border: "none", borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: "pointer", boxShadow: "0 8px 18px rgba(239, 68, 68, 0.2)" },
    footer: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 24px", background: COLORS.panelBg, borderTop: `1px solid ${COLORS.border}`, boxShadow: "0 -4px 12px rgba(15, 23, 42, 0.03)" },
    table: { width: "100%", borderCollapse: "collapse", fontSize: 13 },
    th: { padding: "8px 12px", textAlign: "left", fontWeight: 700, fontSize: 11, textTransform: "uppercase", color: COLORS.gray, borderBottom: `2px solid ${COLORS.border}`, background: COLORS.bg },
    td: { padding: "8px 12px", borderBottom: `1px solid ${COLORS.border}` },
    infoBox: { padding: 16, background: COLORS.infoBoxBg, borderRadius: 12, border: `1px solid rgba(30,58,95,0.18)`, fontSize: 13, lineHeight: 1.5, marginBottom: 16, color: COLORS.dark },
    warningBox: { padding: 16, background: COLORS.warningBoxBg, borderRadius: 12, border: `1px solid rgba(245, 158, 11, 0.3)`, fontSize: 13, lineHeight: 1.5, marginBottom: 16, color: COLORS.dark },
    successBox: { padding: 16, background: COLORS.successBoxBg, borderRadius: 12, border: `1px solid rgba(16,185,129,0.26)`, fontSize: 13, lineHeight: 1.5, marginBottom: 16, color: COLORS.dark },
  };
}


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

function FormTextarea({ label, value, onChange, placeholder, rows = 3 }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>{label}</label>
      <textarea
        style={{ ...styles.textarea, minHeight: rows * 24 }} value={value || ""}
        onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
      />
    </div>
  );
}

function FormSelect({ label, value, onChange, options, required, hopeCode }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return (
    <div style={styles.formGroup}>
      <label style={styles.label}>
        {label} {required && <span style={{ color: COLORS.error }}>*</span>}
        {hopeCode && <> <HopeTag code={hopeCode} /></>}
      </label>
      <select style={styles.select} value={value || ""} onChange={(e) => onChange(e.target.value)}>
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

function FormCheckbox({ label, checked, onChange }) {
  const { mode: themeMode } = useThemeMode();
  const COLORS = useMemo(() => getRnicaColors(themeMode), [themeMode]);
  const styles = useMemo(() => getRnicaStyles(COLORS), [COLORS]);
  return (
    <label style={{ ...styles.checkboxLabel, ...styles.formGroup }}>
      <input type="checkbox" checked={checked || false} onChange={(e) => onChange(e.target.checked)} />
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

function LcdEligibilityCard({ diagnosesData, fullFormData, updateField, styles, COLORS }) {
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
        <div style={{ ...styles.infoBox, marginBottom: 10, padding: 12 }}>
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
          {config?.source_document && <div style={{ fontSize: 11, color: COLORS.gray, marginTop: 6 }}>Source: {config.source_document}</div>}
        </div>
      )}

      {(configError || evaluationError) && (
        <div style={{ ...styles.warningBox, marginBottom: 10, padding: 12 }}>
          {configError || evaluationError}
        </div>
      )}

      {configLoading && <div style={{ fontSize: 12, color: COLORS.gray, marginBottom: 8 }}>Loading LCD criteria…</div>}

      {(config?.criteria_groups || []).map((group) => {
        const groupResult = groupResults.find((item) => item.group_id === group.group_id);
        return (
          <div
            key={group.group_id}
            style={{
              border: `1px solid ${COLORS.border}`,
              borderRadius: 10,
              padding: 10,
              marginBottom: 10,
              background: COLORS.bg,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center", marginBottom: 8, flexWrap: "wrap" }}>
              <div style={{ fontSize: 13, fontWeight: 800, color: COLORS.dark }}>{group.group_name}</div>
              <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
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
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {(group.criteria || []).map((criterion) => {
                const detail = criterionDetails.get(`${group.group_id}:${criterion.criterion_id}`);
                const criterionWithGroup = { ...criterion, group_id: group.group_id };
                return (
                  <div
                    key={criterion.criterion_id}
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
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// SECONDARY DIAGNOSES — add/edit/remove list (feeds HOPE comorbidity
// auto-detection below and hopeReportMapper.js diagnosisEntries()).
// ════════════════════════════════════════════════════════════════
function SecondaryDiagnosesCard({ diagnosesData, updateField, styles, COLORS }) {
  const rows = diagnosesData?.secondaryDiagnoses || [];

  const setRows = (next) => updateField("secondaryDiagnoses", next);

  const addRow = () => setRows([...rows, { icd10: "", description: "", relatedToTerminal: true }]);

  const updateRow = (idx, field, value) => {
    setRows(rows.map((row, i) => (i === idx ? { ...row, [field]: value } : row)));
  };

  const removeRow = (idx) => setRows(rows.filter((_, i) => i !== idx));

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

function HopeComorbiditiesCard({ diagnosesData, updateField, styles, COLORS }) {
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
    <div>
      <div style={styles.infoBox}>
        Per CMS HOPE guidance: check all comorbid/coexisting conditions addressed in the plan of
        care. <strong>Do not check a category already coded as the Principal Diagnosis</strong>{" "}
        — the exception is if the patient has a second, distinct cancer diagnosis.
      </div>

      {groups.map(({ group, categories }) => (
        <div key={group} style={{ marginBottom: 14 }}>
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
                <div key={cat.key} style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
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
        <button type="button" onClick={handleToggleList} style={{
          fontSize: 11.5, fontWeight: 700, padding: "6px 10px", borderRadius: 6,
          border: `1px solid ${COLORS.gray}`, background: showList ? COLORS.gray : "transparent",
          color: showList ? COLORS.white : COLORS.gray, cursor: "pointer",
        }}>
          {showList ? "Hide POC" : "View POC"}
        </button>
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

  const [allergies, setAllergies] = useState([]);
  const [allergyForm, setAllergyForm] = useState({ allergen_text: "", severity: "", reaction_description: "" });
  const [allergyError, setAllergyError] = useState("");

  const reload = useCallback(() => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    Promise.all([listMedications(patientId), listPatientAllergies(patientId)])
      .then(([medList, allergyList]) => {
        setMeds(medList || []);
        setAllergies(allergyList || []);
      })
      .catch((err) => {
        console.error("Failed to load medications/allergies:", err);
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
      {/* ── Allergy list ── */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ ...styles.label, marginBottom: 8 }}>Documented Allergies</div>
        {allergies.length === 0 && <div style={{ fontSize: 12.5, color: COLORS.gray, marginBottom: 8 }}>No allergies documented.</div>}
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
        {showFront && renderView("/body-front.png", ANTERIOR_REGIONS, "Anterior (Front)", "anterior")}
        {showBack && renderView("/body-back.png", POSTERIOR_REGIONS, "Posterior (Back)", "posterior")}
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
    <div style={styles.card} id={id}>
      <div style={{ ...styles.cardTitle, display: "flex", alignItems: "center", gap: 8 }}>
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

function renderDemographics(data, update, COLORS, styles) {
  const u = (path, val) => update("demographics", path, val);
  return (
    <>
      <p style={styles.sectionSubtitle}>Patient identification, caregiver, living situation, and advanced care planning</p>

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
              const siteOfService = { "Memory Care": "Memory Care", "Board & Care": "Board & Care", "Skilled Nursing Facility": "SNF", "Assisted Living Facility": "ALF", "Other facility-based care": "Other" }[v];
              if (siteOfService) {
                u("livingSituation.siteOfService", siteOfService);
                u("livingSituation.livingArrangement", "Facility");
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

      <Card title="Living Situation" hopeCode="A1905">
        <FormSelect label="Site of Service" value={data.livingSituation?.siteOfService} onChange={(v) => u("livingSituation.siteOfService", v)}
          options={["Home", "SNF", "ALF", "Board & Care", "Memory Care", "Hospital", "Homeless", "Other"]} />
        <FormSelect label="Admitted From" value={data.livingSituation?.admittedFrom} onChange={(v) => u("livingSituation.admittedFrom", v)}
          options={["Home", "Hospital", "SNF", "ALF", "Rehab", "Other"]} />
        <FormRadioGroup label="Living Arrangement" value={data.livingSituation?.livingArrangement} onChange={(v) => u("livingSituation.livingArrangement", v)}
          options={["Alone", "With spouse", "With family", "With non-relative", "Facility"]} />
        <FormRadioGroup label="Availability of Assistance" value={data.livingSituation?.availabilityOfAssistance} onChange={(v) => u("livingSituation.availabilityOfAssistance", v)}
          options={["24/7 available", "Daytime only", "Nighttime only", "Limited", "None"]} />
      </Card>

      <Card title="Advanced Care Planning" cms="F2000/F2100/F2200" id="advancedCarePlanning">
        <FormRadioGroup label="Code Status" value={data.advancedCarePlanning?.codeStatus} onChange={(v) => u("advancedCarePlanning.codeStatus", v)}
          hopeCode="F2000" options={["Full Code", "DNR", "DNR-CC", "Comfort Measures Only"]} />
        <FormInput label="Code Status Discussion Date" value={data.advancedCarePlanning?.codeStatusDate}
          onChange={(v) => u("advancedCarePlanning.codeStatusDate", v)} type="date" />
        <FormRadioGroup label="Life-Sustaining Treatment Preference" value={data.advancedCarePlanning?.lifeSustainingTreatmentPreference}
          onChange={(v) => u("advancedCarePlanning.lifeSustainingTreatmentPreference", v)} hopeCode="F2100"
          options={["Yes — wants life-sustaining treatment", "No — does not want", "Undecided"]} />
        <FormInput label="Life-Sustaining Treatment Discussion Date" value={data.advancedCarePlanning?.lifeSustainingTreatmentPreferenceDate}
          onChange={(v) => u("advancedCarePlanning.lifeSustainingTreatmentPreferenceDate", v)} type="date" />
        <FormRadioGroup label="Hospitalization Preference" value={data.advancedCarePlanning?.hospitalizationPreference}
          onChange={(v) => u("advancedCarePlanning.hospitalizationPreference", v)} hopeCode="F2200"
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

function renderGenericSection(sectionKey, data, update, config, demographics, fullFormData, COLORS, styles, patientId, assessmentId) {
  const u = (path, val) => update(sectionKey, path, val);
  const { title, subtitle, cards } = config;

  // The 10 Body System Assessment sections (SNS_RNICA_MASTER_MAP_1.1.md)
  // each get Add/View/Update/Resolve Plan of Care controls on every
  // field-based subcard.
  const BODY_SYSTEM_SECTIONS = new Set([
    "neurological", "cardiovascular", "respiratory", "infection",
    "gastrointestinal", "nutrition", "endocrine", "genitourinary",
    "musculoskeletal", "skin", "imminentDeath",
  ]);

  const normalizePainPatientType = (type) => {
    if (!type || type === "adult-alert" || type === "alert") return "verbal";
    if (type === "adult" || type === "alert-adult") return "verbal";
    return type;
  };

  const patientAge = sectionKey === "pain" ? calculateAgeFromDob(demographics?.dob) : null;
  const isPediatricAge = typeof patientAge === "number" && patientAge < 18;

  // Auto-derive the pain scale from HOPE J0900 (can the patient verbalize
  // pain?) and the patient's age — only one scale (Numeric / PAINAD / FLACC)
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

  return (
    <>
      {subtitle && <p style={styles.sectionSubtitle}>{subtitle}</p>}
      {cards.map((card, ci) => {
        const shouldRenderPainMap = sectionKey === "pain" && card.title === "Pain Characteristics";
        const shouldRenderSkinMap = sectionKey === "skin" && card.title === "Skin Assessment";
        const shouldRenderPainToolCard = sectionKey === "pain" && card.title === "Pain Assessment Tool" && painAssessmentMode !== "painad" && painAssessmentMode !== "flacc";
        const shouldRenderPainCharacteristicsCard = sectionKey === "pain" && card.title === "Pain Characteristics" && painAssessmentMode === "verbal";
        const shouldRenderPainadCard = sectionKey === "pain" && card.title === "PAINAD Scale (Non-verbal / unable to self-report)" && painAssessmentMode === "painad";
        const shouldRenderFlaccCard = sectionKey === "pain" && card.title === "FLACC Scale (Pediatric / child)" && painAssessmentMode === "flacc";
        const shouldRenderPocIssueEditor = sectionKey === "finalization" && card.title === "Plan of Care — Problem Generation (CDPH Gap #4)";

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

        if (sectionKey === "diagnoses" && card.customRenderer === "lcdEligibility") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <LcdEligibilityCard
                diagnosesData={data}
                fullFormData={fullFormData}
                updateField={u}
                styles={styles}
                COLORS={COLORS}
              />
            </Card>
          );
        }

        if (sectionKey === "diagnoses" && card.customRenderer === "secondaryDiagnoses") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <SecondaryDiagnosesCard diagnosesData={data} updateField={u} styles={styles} COLORS={COLORS} />
            </Card>
          );
        }

        if (sectionKey === "diagnoses" && card.customRenderer === "hopeComorbidities") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <HopeComorbiditiesCard diagnosesData={data} updateField={u} styles={styles} COLORS={COLORS} />
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

        if (sectionKey === "medications" && card.customRenderer === "medicationOrders") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <MedicationOrdersCard patientId={patientId} styles={styles} COLORS={COLORS} />
            </Card>
          );
        }

        if (sectionKey === "medications" && card.customRenderer === "ordersHub") {
          return (
            <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
              <OrdersHubCard patientId={patientId} />
            </Card>
          );
        }

        return (
          <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
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

            {shouldRenderPocIssueEditor && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ ...styles.infoBox, marginBottom: 10 }}>
                  Add every problem identified during this assessment to the Plan of Care below (Problem / Goal /
                  Intervention / Discipline), then open the current POC to confirm it was generated correctly.
                </div>
                {(data.pocEntries || []).length > 0 && (
                  <div style={{ marginBottom: 10, display: "flex", flexDirection: "column", gap: 6 }}>
                    {data.pocEntries.map((entry, ei) => (
                      <div key={entry.id || ei} style={{
                        display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto auto", gap: 8, alignItems: "center",
                        padding: "8px 10px", borderRadius: 8, border: `1px solid ${COLORS.border}`, background: COLORS.bg, fontSize: 12.5,
                      }}>
                        <div><strong>Problem:</strong> {entry.problem || "—"}</div>
                        <div><strong>Goal:</strong> {entry.goal || "—"}</div>
                        <div><strong>Intervention:</strong> {entry.intervention || "—"}</div>
                        <div style={{ fontWeight: 700, color: COLORS.teal }}>{entry.discipline || "—"}</div>
                        <button type="button" onClick={() => u("pocEntries", data.pocEntries.filter((_, i) => i !== ei))}
                          style={{ border: "none", background: "transparent", color: COLORS.gray, cursor: "pointer", fontSize: 15, fontWeight: 700 }}
                          title="Remove this POC entry">×</button>
                      </div>
                    ))}
                  </div>
                )}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10, alignItems: "end" }}>
                  <FormInput label="Problem" value={data.pocDraft?.problem} onChange={(v) => u("pocDraft.problem", v)} placeholder="e.g., Pain related to bone mets" />
                  <FormInput label="Goal" value={data.pocDraft?.goal} onChange={(v) => u("pocDraft.goal", v)} placeholder="e.g., Pain ≤3/10 within 72 hrs" />
                  <FormInput label="Intervention / Frequency" value={data.pocDraft?.intervention} onChange={(v) => u("pocDraft.intervention", v)} placeholder="e.g., RN visits 2x/wk, titrate opioid per protocol" />
                  <FormSelect label="Discipline" value={data.pocDraft?.discipline} onChange={(v) => u("pocDraft.discipline", v)}
                    options={["RN", "LVN/LPN", "MSW", "Chaplain", "HHA", "Volunteer", "Dietitian", "All disciplines"]} />
                  <button type="button"
                    disabled={!data.pocDraft?.problem}
                    onClick={() => {
                      const draft = data.pocDraft || {};
                      if (!draft.problem) return;
                      const entries = [...(data.pocEntries || []), { id: `poc-${Date.now()}`, ...draft }];
                      u("pocEntries", entries);
                      u("pocDraft", { problem: "", goal: "", intervention: "", discipline: "" });
                    }}
                    style={{
                      fontSize: 12.5, fontWeight: 700, padding: "9px 14px", borderRadius: 6, border: "none",
                      background: data.pocDraft?.problem ? COLORS.teal : COLORS.border,
                      color: COLORS.white, cursor: data.pocDraft?.problem ? "pointer" : "not-allowed", height: 38,
                    }}
                  >
                    + Add to POC
                  </button>
                </div>
              </div>
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
                  // Auto-select the correct pain scale from the HOPE J0900
                  // answer + patient age so only one tool is ever shown:
                  // verbal (reliable/sometimes) -> Numeric, non-verbal adult
                  // -> PAINAD, pediatric -> FLACC.
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
            {BODY_SYSTEM_SECTIONS.has(sectionKey) && card.fields && (
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
          { type: "radio", label: "Can the patient verbalize pain?", path: "verbalizesPain", hopeCode: "J0900", options: [
            { value: "0", label: "No" }, { value: "1", label: "Yes, reliably" }, { value: "2", label: "Sometimes" }, { value: "3", label: "Unable to determine" }
          ]},
          { type: "radio", label: "Is the patient uncomfortable because of pain?", path: "uncomfortableBecauseOfPain", hopeCode: "J0915", options: [
            { value: "0", label: "No" }, { value: "1", label: "Yes" }, { value: "9", label: "Unable to determine" }
          ]},
          { type: "checkbox", label: "Neuropathic pain present", path: "neuropathicPain" },
          { type: "input", label: "Pain screening date", path: "screeningDate", inputType: "date" },
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
    subtitle: "Primary/Secondary Dx, comorbidities, LCD eligibility, disease trajectory narrative",
    cards: [
      {
        title: "Primary Diagnosis", hopeCode: "I0010", fields: [
          { type: "input", label: "ICD-10 Code", path: "primaryDiagnosis.icd10", required: true, hopeCode: "I0010" },
          { type: "input", label: "Description", path: "primaryDiagnosis.description", required: true },
          { type: "input", label: "Onset Date", path: "primaryDiagnosis.onsetDate", inputType: "date" },
        ],
      },
      {
        title: "Terminal Prognosis", hopeCode: "J0050", fields: [
          { type: "select", label: "Terminal Prognosis", path: "terminalPrognosis", hopeCode: "J0050", options: ["6 months or less", "More than 6 months", "Undetermined"] },
          { type: "radio", label: "Disease Trajectory", path: "diseaseTrajectory", options: ["Decline", "Plateau", "Fluctuating"] },
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
        title: "Narrative & Disease Trajectory", fields: [
          { type: "textarea", label: "LCD Eligibility Narrative", path: "lcdEligibilityNarrative", rows: 6, placeholder: "Document the patient's terminal illness, functional decline trajectory, and LCD eligibility criteria..." },
        ],
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
          { type: "radio", label: "Level of Consciousness", path: "consciousness", options: ["Alert", "Lethargic", "Obtunded", "Stuporous", "Comatose"] },
          { type: "checkbox", label: "Oriented to Time", path: "orientation.time" },
          { type: "checkbox", label: "Oriented to Place", path: "orientation.place" },
          { type: "checkbox", label: "Oriented to Person", path: "orientation.person" },
          { type: "checkbox", label: "Oriented to Situation", path: "orientation.situation" },
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
          { type: "radio", label: "Communication", path: "communication", options: ["Clear", "Impaired", "Unable"] },
          { type: "radio", label: "Hearing", path: "hearing", options: ["Adequate", "Impaired", "Deaf", "Hearing aid"] },
          { type: "radio", label: "Vision", path: "vision", options: ["Adequate", "Impaired", "Blind", "Corrective lenses"] },
          { type: "radio", label: "Balance", path: "balance", options: ["Steady", "Unsteady", "Unable to stand"] },
          { type: "checkboxGroup", label: "Sensory Deficits", path: "sensoryDeficits", options: ["Numbness", "Tingling", "Decreased sensation", "Phantom pain"] },
        ],
      },
      {
        title: "Psychiatric / Cognitive", fields: [
          { type: "input", label: "Cognition Assessment", path: "cognition" },
          { type: "checkbox", label: "Delirium", path: "delirium" },
          { type: "checkbox", label: "Seizure History", path: "seizureHistory" },
          { type: "textarea", label: "Psychiatric History", path: "psychiatricHistory" },
        ],
      },
      {
        title: "Sleep / Rest", fields: [
          { type: "radio", label: "Sleep Pattern", path: "sleepRest.sleepPattern", options: ["Normal", "Insomnia", "Hypersomnia", "Fragmented"] },
          { type: "input", label: "Average Sleep Hours", path: "sleepRest.averageSleepHours", inputType: "number" },
          { type: "checkboxGroup", label: "Sleep Aids", path: "sleepRest.sleepAids", options: ["Medication", "Positioning", "White noise", "Warm milk/tea", "Other"] },
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
      { title: "Allergies", fields: [
        { type: "checkboxGroup", label: "Allergies", path: "allergies", options: ["Food allergies", "Other allergies", "Sensitivities", "None known"] },
        { type: "input", label: "Allergy Details", path: "allergyDetails" },
      ]},
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
        { type: "radio", label: "Diarrhea", path: "diarrhea", sfv: true, options: ["None", "Mild", "Moderate", "Severe"] },
        { type: "radio", label: "Constipation", path: "constipation", sfv: true, options: ["None", "Mild", "Moderate", "Severe"] },
      ]},
      { title: "Abdominal / Bowel Assessment", fields: [
        { type: "radio", label: "Bowel Sounds", path: "bowelSounds", options: ["Normal", "Hyperactive", "Hypoactive", "Absent"] },
        { type: "radio", label: "Abdomen", path: "abdomen", options: ["Soft", "Firm", "Distended", "Tender", "Rigid"] },
        { type: "radio", label: "Bowel Status", path: "bowelStatus", options: ["Regular", "Irregular", "Incontinent"] },
        { type: "input", label: "Last BM Date", path: "lastBM", inputType: "date" },
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
        { type: "radio", label: "Continence", path: "urinaryStatus", options: ["Continent", "Stress incontinence", "Urge incontinence", "Functional incontinence", "Total incontinence", "Catheterized"] },
        { type: "input", label: "Frequency", path: "frequency" },
      ]},
      { title: "Catheter Assessment", fields: [
        { type: "checkbox", label: "Catheter Present", path: "catheter.present" },
        { type: "select", label: "Type", path: "catheter.type", options: ["Foley", "Suprapubic", "Condom", "Intermittent"] },
        { type: "input", label: "Size", path: "catheter.size" },
        { type: "input", label: "Insertion Date", path: "catheter.insertionDate", inputType: "date" },
        { type: "input", label: "Last Change Date", path: "catheter.lastChangeDate", inputType: "date" },
        { type: "radio", label: "Condition", path: "catheter.condition", options: ["Patent", "Blocked", "Leaking"] },
        { type: "checkboxGroup", label: "Urine Characteristics", path: "catheter.urineCharacteristics", options: ["Clear", "Cloudy", "Amber", "Dark", "Hematuria", "Sediment", "Foul odor"] },
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
        { type: "radio", label: "Gait", path: "gait", options: ["Normal", "Unsteady", "Shuffling", "Unable"] },
        { type: "checkboxGroup", label: "Assistive Devices", path: "assistiveDevices", options: ["Walker", "Wheelchair", "Cane", "Crutches", "Hospital bed", "Hoyer lift", "None"] },
      ]},
      { title: "Mobility Assessment", fields: [
        { type: "radio", label: "Ambulatory Status", path: "mobility.ambulatoryStatus", options: ["Independent", "Supervised", "Assisted", "Dependent", "Bedbound"] },
        { type: "radio", label: "Endurance", path: "mobility.endurance", options: ["Good", "Fair", "Poor"] },
        { type: "radio", label: "Transfer Ability", path: "mobility.transferAbility", options: ["Independent", "Standby assist", "1-person assist", "2-person assist", "Hoyer lift"] },
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
    title: "Skin / Wounds",
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
        { type: "checkbox", label: "Firearm in Home", path: "firearmInHome" },
        { type: "checkbox", label: "Oxygen in Use", path: "oxygenInUse" },
        { type: "checkbox", label: "Oxygen Safety Reviewed", path: "oxygenSafetyReviewed" },
      ]},
      { title: "Disaster Triage", fields: [
        { type: "radio", label: "Disaster Level", path: "disasterLevel", options: ["Level 1 — Priority", "Level 2 — Urgent", "Level 3 — Non-urgent"] },
        { type: "checkboxGroup", label: "Level 1 Conditions", path: "disasterLevelOneConditions", options: [
          "Ventilator dependent", "IV medications", "Oxygen dependent", "Suction dependent",
          "Tube feeding dependent", "Wound vac", "No caregiver"
        ]},
        { type: "textarea", label: "Safety Notes", path: "notes" },
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
          "Anxiety about illness", "Depression", "Grief/loss", "Financial concerns",
          "Family conflict", "Caregiver burden", "Social isolation", "Role changes",
          "Unfinished business", "Fear of dying", "Loss of independence", "Body image concerns"
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
          "Religious rituals", "Afterlife concerns", "Anger at God", "Spiritual distress"
        ]},
        { type: "select", label: "Spiritual Distress Rating (0-10)", path: "spiritualDistressRating", options: ["0","1","2","3","4","5","6","7","8","9","10"] },
        { type: "checkbox", label: "Spiritual / existential concerns asked", path: "concernsDiscussed" },
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
          "Fear of death", "Unresolved grief", "Existential distress", "Legacy concerns", "Family preparedness"
        ]},
        { type: "checkboxGroup", label: "Caregiver Concerns", path: "caregiverConcerns", options: [
          "Anticipatory grief", "Previous losses", "Complicated grief history",
          "Mental health concerns", "Substance abuse history", "Social isolation", "Concurrent stressors"
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
          "Bathing/showering", "Hair care/grooming", "Oral hygiene", "Skin care",
          "Dressing", "Toileting assistance", "Transfers/mobility", "Light meal preparation",
          "Light housekeeping", "Laundry", "Vital signs", "Range of motion exercises", "Respite for caregiver"
        ]},
      ]},
      { title: "Aide Visit Preferences", fields: [
        { type: "select", label: "Frequency", path: "aideVisitPreferences.frequency", options: ["Daily", "3x/week", "2x/week", "Weekly", "PRN"] },
        { type: "radio", label: "Preferred Time", path: "aideVisitPreferences.preferredTime", options: ["Morning", "Afternoon", "Evening", "Flexible"] },
        { type: "select", label: "Duration", path: "aideVisitPreferences.duration", options: ["1 hour", "2 hours", "3 hours", "4 hours"] },
      ]},
      { title: "Volunteer Services", fields: [
        { type: "checkboxGroup", label: "Services Needed", path: "volunteerServices", options: [
          "Companionship/visits", "Respite care", "Errand assistance", "Transportation",
          "Vigil/11th hour", "Pet care", "Legacy project", "Music/art therapy", "Reading/letter writing"
        ]},
      ]},
      { title: "Community Resources", fields: [
        { type: "checkboxGroup", label: "Resources Needed", path: "communityResources", options: [
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
      { title: "HA Assignment", fields: [
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

  medications: {
    title: "Hospice Orders Hub",
    subtitle: "Unified orders — Meds, DME, Supplies, Lab, Treatment, Diet, Other",
    cards: [
      { title: "Opioid / Bowel Assessment", fields: [
        { type: "checkbox", label: "Scheduled Opioid", path: "scheduledOpioid" },
        { type: "input", label: "Scheduled Opioid Start / Continue Date", path: "scheduledOpioidDate", inputType: "date" },
        { type: "checkbox", label: "PRN Opioid", path: "prnOpioid" },
        { type: "input", label: "PRN Opioid Start / Continue Date", path: "prnOpioidDate", inputType: "date" },
        { type: "checkbox", label: "Bowel Regimen in Place", path: "bowelRegimen" },
        { type: "input", label: "Bowel Regimen Start / Continue Date", path: "bowelRegimenDate", inputType: "date" },
      ]},
      { title: "Medication Reconciliation", fields: [
        { type: "checkbox", label: "Med Reconciliation Completed", path: "medReconciliation.completed" },
        { type: "input", label: "Completed Date", path: "medReconciliation.completedDate", inputType: "date" },
        { type: "input", label: "Completed By", path: "medReconciliation.completedBy" },
      ]},
      { title: "Medications — Allergies, Orders & Interaction Safety Check", customRenderer: "medicationOrders" },
      { title: "Orders Hub — DME, Supplies, Lab, Treatment, Diet & Other", customRenderer: "ordersHub" },
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
      ]},
    ],
  },

  finalization: {
    title: "Finalization & Signature",
    subtitle: "Response to interventions, POC generation, completion, certification, clinician signature",
    cards: [
      { title: "Response to Initial Interventions (CDPH Gap #3)", cms: "CDPH", fields: [
        { type: "textarea", label: "Initial Response Summary", path: "responseToInterventions.initialResponseSummary", rows: 4,
          placeholder: "Document patient's initial response to admission interventions — pain management, symptom control, comfort measures, family support. This establishes the baseline for subsequent reassessments." },
        { type: "checkbox", label: "Baseline Response Established", path: "responseToInterventions.baselineEstablished" },
        { type: "input", label: "Baseline Date", path: "responseToInterventions.baselineDate", inputType: "date" },
        { type: "textarea", label: "Progress Notes / Assessment-to-Assessment Context", path: "responseToInterventions.progressNotes", rows: 3,
          placeholder: "Initial observations that will anchor future reassessments and update comparisons..." },
      ]},
      { title: "Plan of Care — Problem Generation (CDPH Gap #4)", cms: "CDPH POC", fields: [
        { type: "checkbox", label: "All assessment problems have been reviewed and POC entries generated", path: "pocGenerationCompleted" },
        { type: "checkbox", label: "POC reviewed with IDG team", path: "pocReviewedWithIdg" },
      ]},
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
// 8. MAIN COMPONENT
// ════════════════════════════════════════════════════════════════

export default function RNICA({ patientId, assessmentId: existingAssessmentId = undefined, mode = "ica", onFormDataChange = undefined }) {
  const navigate = useNavigate();
  const initialPatientId = patientId ?? getActivePatientId() ?? "";
  const [resolvedPatientId, setResolvedPatientId] = useState(initialPatientId);
  const [patientSummary, setPatientSummary] = useState(null);
  const [patientSummaryError, setPatientSummaryError] = useState("");
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
  const [intelligence, setIntelligence] = useState(null);
  const [intelligenceLoading, setIntelligenceLoading] = useState(false);
  const isOngoing = mode === "ongoing";
  const [assessmentType, setAssessmentType] = useState("update");
  const autosavePatientId = resolvedPatientId || patientId || "";

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
  const routes = useMemo(() => (isOngoing ? ROUTES.filter((route) => route.key !== "sfv") : ROUTES), [isOngoing]);
  const sidebarConfigItems = useMemo(() => {
    const items = isOngoing ? SIDEBAR_CONFIG.filter((item) => item.key !== "sfv") : SIDEBAR_CONFIG;
    return isOngoing ? items.map((item) => ({ ...item, hope: [] })) : items;
  }, [isOngoing]);

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

  const saveButtonLabel = isOngoing || assessmentId ? "Update Assessment / Recert Assessment" : "Initial Comprehensive RN Assessment";

  // Save / Update
  const handleSave = useCallback(async () => {
    setSaving(true);
    setPageError("");
    try {
      let activeAssessmentId = assessmentId;
      if (assessmentId) {
        await api.updateRNICAAssessment(assessmentId, formData);
      } else {
        const result = await api.saveRNICAAssessment(patientId, formData);
        activeAssessmentId = result.assessmentId;
        setAssessmentId(activeAssessmentId);
      }
      await refreshIntelligence(activeAssessmentId);
      markPersisted(formData, activeAssessmentId);
      setSaveStatus("saved");
    } catch (err) {
      console.error("Save error:", err);
      setSaveStatus("error");
      setPageError(err instanceof Error ? err.message : "Unable to save RN ICA assessment.");
    } finally {
      setSaving(false);
    }
  }, [assessmentId, formData, markPersisted, patientId, refreshIntelligence]);

  // Lock
  const handleLock = useCallback(async () => {
    if (!assessmentId) return;
    const v = validateRNICA(formData, mode);
    if (!v.isValid) {
      alert("Cannot lock: there are validation errors. Please complete all required fields.");
      return;
    }
    setPageError("");
    try {
      await api.lockRNICAAssessment(assessmentId);
      setLocked(true);
    } catch (err) {
      console.error("Lock error:", err);
      setPageError(err instanceof Error ? err.message : "Unable to lock RN ICA assessment.");
    }
  }, [assessmentId, formData]);

  // Section completion tracker
  const completedSections = useMemo(() => {
    const completed = [];
    routes.forEach((route) => {
      const sectionData = formData[route.formSection];
      if (sectionData) {
        const hasContent = JSON.stringify(sectionData) !== JSON.stringify(INITIAL_FORM[route.formSection]);
        if (hasContent) completed.push(route.key);
      }
    });
    return completed;
  }, [formData, routes]);

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
                ? renderGenericSection(route.formSection, sectionData, updateField, config, formData.demographics, formData, COLORS, styles, patientId, assessmentId)
                : <div style={styles.card}><p style={{ color: COLORS.gray }}>Section "{route.key}" — content loading...</p></div>}
          </div>
        )}
      </div>
    );
  });

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

      {/* ── Footer ── */}
      <div style={styles.footer}>
        <div style={{ display: "flex", gap: 8 }}>
          <button style={styles.btnSecondary} onClick={goPrev} disabled={activeSection === routes[0]?.key}>
            &larr; Previous
          </button>
          <button style={styles.btnSecondary} onClick={goNext} disabled={activeSection === routes[routes.length - 1]?.key}>
            Next &rarr;
          </button>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {assessmentId && (
            <span style={{ fontSize: 12, color: COLORS.gray }}>ID: {assessmentId}</span>
          )}
          <button style={styles.btnPrimary} onClick={handleSave} disabled={saving || locked}>
            {saving ? "Saving..." : saveButtonLabel}
          </button>
          {assessmentId && !locked && (
            <button style={styles.btnDanger} onClick={handleLock}>
              Lock Assessment
            </button>
          )}
        </div>
      </div>
      </div>
    </AssessmentModeContext.Provider>
  );
}