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

import React, { useState, useCallback, useMemo, useEffect, useContext } from "react";
import frontBody from "../assets/body-map/front.png";
import backBody from "../assets/body-map/back.png";
import { fetchPatientSummary } from "../api/patientCharts";
import { fetchCensusWorkspace } from "../api/census";
import {
  saveRnicaAssessment,
  getRnicaAssessment,
  updateRnicaAssessment,
  lockRnicaAssessment,
  getRnicaIntelligence,
} from "../api/icaAssessments";
import PatientContextSidebar from "./PatientContextSidebar";
import AssessmentTypeToggle from "./AssessmentTypeToggle";
import { getSfvStatus } from "../intake/hopeReportMapper";

import { getActivePatientId, setActivePatientId } from "../utils/activePatient";
// ════════════════════════════════════════════════════════════════
// 1. CONSTANTS & CONFIGURATION
// ════════════════════════════════════════════════════════════════

const API_BASE = "/visits/rnica";

const COLORS = {
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
};

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
    religion: "", maritalStatus: "", phone: "", alternatePhone: "",
    address: { street: "", city: "", state: "", zip: "", county: "" },
    emergencyContact: { name: "", relationship: "", phone: "" },
    pcg: {
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
      criteriaA: false, criteriaB: false, criteriaC: false,
      diseaseSpecificLCD: "",
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
    pulseQuality: "",
    edema: { present: false, location: [], severity: "", pitting: "" },
    chestPain: { present: false, type: "", frequency: "" },
    peripheralCirculation: "", heartSounds: "", jvd: false,
    notes: "",
  },

  // ─── 9. RESPIRATORY ───────────────────────────────
  respiratory: {
    sobSeverity: "", exertionLevel: "",
    shortnessOfBreathScreened: false, screeningDate: "",
    treatmentInitiated: false, treatmentDate: "",
    lungSounds: [], respirations: [],
    coughType: "", sputumCharacter: "",
    oxygenTherapy: {
      inUse: false, type: "", litersPerMinute: "",
      hoursPerDay: "", satOnO2: "",
    },
    notes: "",
  },

  // ─── 10. INFECTION ────────────────────────────────
  infection: {
    allergies: [],
    currentInfections: [],
    historyOfResistantInfections: [],
    immunosuppressed: false,
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
    notes: "",
  },

  // ─── 13. ENDOCRINE ────────────────────────────────
  endocrine: {
    thyroid: { assessment: "", notes: "" },
    diabetes: {
      type: "", glucoseMonitoring: "",
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

  // CDPH Gap #2 ? Caregiver willingness and capability evaluation
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
const styles = {
  page: {
    display: "flex",
    flexDirection: "column",
    minHeight: "100vh",
    height: "auto",
    fontFamily: "Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    color: COLORS.dark,
    background: "#EEF3F8",
  },
  banner: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "14px 24px",
    background: "linear-gradient(90deg, #1E3A5F 0%, #0D9488 100%)",
    color: COLORS.white,
    fontSize: 13,
    boxShadow: "0 4px 16px rgba(15, 23, 42, 0.12)",
    borderBottom: "1px solid rgba(148, 163, 184, 0.2)",
  },
  bannerName: { fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" },
  bannerMeta: { fontSize: 12, opacity: 0.82, letterSpacing: "0.01em" },
  workspace: { display: "flex", flex: 1, minHeight: 0, overflow: "visible" },
  sidebar: {
    width: 250,
    background: "#F8FBFD",
    borderRight: `1px solid ${COLORS.border}`,
    overflowY: "auto",
    padding: "18px 10px",
    flexShrink: 0,
    minHeight: 0,
  },
  sidebarItem: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "10px 12px",
    margin: "4px 0",
    fontSize: 13,
    cursor: "pointer",
    borderRadius: 10,
    borderLeft: "3px solid transparent",
    transition: "all 0.2s ease",
    color: "#334155",
  },
  sidebarActive: {
    background: "linear-gradient(90deg, rgba(13,148,136,0.12), rgba(13,148,136,0.03))",
    borderLeftColor: COLORS.teal,
    color: "#0F766E",
    fontWeight: 700,
    boxShadow: "inset 0 0 0 1px rgba(13,148,136,0.08)",
  },
  mainArea: { flex: 1, display: "flex", minHeight: 0, overflow: "visible" },
  content: { flex: 1, overflowY: "auto", minHeight: 0, padding: "24px 28px 32px" },
  rightPanel: {
    width: 290,
    background: "rgba(255,255,255,0.96)",
    borderLeft: `1px solid ${COLORS.border}`,
    overflowY: "auto",
    padding: 18,
    flexShrink: 0,
    backdropFilter: "blur(10px)",
    minHeight: 0,
  },
  card: {
    background: COLORS.white,
    borderRadius: 12,
    border: `1px solid ${COLORS.border}`,
    padding: 18,
    marginBottom: 18,
    boxShadow: "0 2px 10px rgba(15, 23, 42, 0.03)",
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: 800,
    marginBottom: 14,
    color: COLORS.dark,
    letterSpacing: "-0.01em",
  },
  sectionTitle: { fontSize: 22, fontWeight: 800, marginBottom: 6, letterSpacing: "-0.02em", color: COLORS.dark },
  sectionSubtitle: { fontSize: 12.5, color: COLORS.gray, marginBottom: 22, lineHeight: 1.5 },
  formGroup: { marginBottom: 16 },
  label: { display: "block", fontSize: 13, fontWeight: 700, marginBottom: 6, color: COLORS.dark, lineHeight: 1.4 },
  input: {
    width: "100%",
    padding: "10px 12px",
    border: `1px solid ${COLORS.border}`,
    borderRadius: 10,
    fontSize: 14,
    boxSizing: "border-box",
    background: "#ffffff",
    transition: "border-color 0.2s ease, box-shadow 0.2s ease",
    boxShadow: "inset 0 1px 3px rgba(15, 23, 42, 0.03)",
  },
  textarea: {
    width: "100%",
    padding: "10px 12px",
    border: `1px solid ${COLORS.border}`,
    borderRadius: 10,
    fontSize: 14,
    minHeight: 80,
    resize: "vertical",
    boxSizing: "border-box",
    background: "#ffffff",
    boxShadow: "inset 0 1px 3px rgba(15, 23, 42, 0.03)",
  },
  select: {
    width: "100%",
    padding: "10px 12px",
    border: `1px solid ${COLORS.border}`,
    borderRadius: 10,
    fontSize: 14,
    background: COLORS.white,
    boxSizing: "border-box",
    boxShadow: "inset 0 1px 3px rgba(15, 23, 42, 0.03)",
  },
  radioGroup: { display: "flex", gap: 16, flexWrap: "wrap" },
  radioLabel: { display: "flex", alignItems: "center", gap: 6, fontSize: 13, cursor: "pointer", color: COLORS.dark },
  checkboxGroup: { display: "flex", flexDirection: "column", gap: 8 },
  checkboxLabel: { display: "flex", alignItems: "center", gap: 8, fontSize: 13, cursor: "pointer", color: COLORS.dark },
  hopeTag: { display: "inline-block", padding: "3px 8px", borderRadius: 999, fontSize: 10, fontWeight: 800, background: "#ECFDF5", color: COLORS.hope, letterSpacing: "0.03em", textTransform: "uppercase" },
  sfvTag: { display: "inline-block", padding: "3px 8px", borderRadius: 999, fontSize: 10, fontWeight: 800, background: "#FEF2F2", color: COLORS.sfv, letterSpacing: "0.03em", textTransform: "uppercase" },
  cmsTag: { display: "inline-block", padding: "3px 8px", borderRadius: 999, fontSize: 10, fontWeight: 800, background: "#EFF6FF", color: COLORS.cms, letterSpacing: "0.03em", textTransform: "uppercase" },
  statusBadge: { display: "inline-flex", alignItems: "center", gap: 4, padding: "5px 10px", borderRadius: 999, fontSize: 12, fontWeight: 700, letterSpacing: "0.04em", textTransform: "uppercase" },
  btnPrimary: { padding: "11px 18px", background: "linear-gradient(135deg, #0D9488 0%, #0F766E 100%)", color: COLORS.white, border: "none", borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: "pointer", boxShadow: "0 8px 18px rgba(13, 148, 136, 0.2)" },
  btnSecondary: { padding: "11px 18px", background: COLORS.white, color: COLORS.dark, border: `1px solid ${COLORS.border}`, borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: "pointer", boxShadow: "0 4px 12px rgba(15, 23, 42, 0.03)" },
  btnDanger: { padding: "11px 18px", background: "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)", color: COLORS.white, border: "none", borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: "pointer", boxShadow: "0 8px 18px rgba(239, 68, 68, 0.2)" },
  footer: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 24px", background: "rgba(255,255,255,0.96)", borderTop: `1px solid ${COLORS.border}`, boxShadow: "0 -4px 12px rgba(15, 23, 42, 0.03)" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 13 },
  th: { padding: "8px 12px", textAlign: "left", fontWeight: 700, fontSize: 11, textTransform: "uppercase", color: COLORS.gray, borderBottom: `2px solid ${COLORS.border}`, background: COLORS.bg },
  td: { padding: "8px 12px", borderBottom: `1px solid ${COLORS.border}` },
  infoBox: { padding: 16, background: "linear-gradient(135deg, #eef6ff, #eefaf8)", borderRadius: 12, border: `1px solid rgba(30,58,95,0.18)`, fontSize: 13, lineHeight: 1.5, marginBottom: 16 },
  warningBox: { padding: 16, background: "linear-gradient(135deg, #fffbeb, #fff7ed)", borderRadius: 12, border: `1px solid rgba(245, 158, 11, 0.3)`, fontSize: 13, lineHeight: 1.5, marginBottom: 16 },
  successBox: { padding: 16, background: "linear-gradient(135deg, #ecfdf5, #f0fdf4)", borderRadius: 12, border: `1px solid rgba(16,185,129,0.26)`, fontSize: 13, lineHeight: 1.5, marginBottom: 16 },
};

// Tag components
function HopeTag({ code }) {
  const mode = useContext(AssessmentModeContext);
  if (mode === "ongoing") return null;
  return <span style={styles.hopeTag}>HOPE {code}</span>;
}
function SfvTag() {
  const mode = useContext(AssessmentModeContext);
  if (mode === "ongoing") return null;
  return <span style={styles.sfvTag}>SFV Trigger</span>;
}
function CmsTag({ label }) { return <span style={styles.cmsTag}>CMS {label || "Required"}</span>; }

// Form field components
function FormInput({ label, value, onChange, type = "text", placeholder, required, hopeCode, ...rest }) {
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

function FormCheckboxGroup({ label, values = [], onChange, options, hopeCode }) {
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
  return (
    <label style={{ ...styles.checkboxLabel, ...styles.formGroup }}>
      <input type="checkbox" checked={checked || false} onChange={(e) => onChange(e.target.checked)} />
      <span style={{ fontSize: 13, fontWeight: 500 }}>{label}</span>
    </label>
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
                border: patientType === option.value ? "1px solid #0D9488" : "1px solid #E2E8F0",
                background: patientType === option.value ? (tone === "skin" ? "#FEF3C7" : "#E0F2FE") : "#FFFFFF",
                color: "#0F172A",
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
          background: "#F8FAFC",
          border: "1px solid #E2E8F0",
          borderRadius: 12,
          boxShadow: "inset 0 1px 2px rgba(15, 23, 42, 0.04)",
        }}>
          <div style={{
            fontSize: 11,
            fontWeight: 800,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#475569",
          }}>
            Body view
          </div>

          <div style={{
            fontSize: 12,
            fontWeight: 800,
            color: "#0F172A",
            background: "#FFFFFF",
            border: "1px solid #CBD5E1",
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
                  border: view === option.value ? "1px solid #0D9488" : "1px solid transparent",
                  background: view === option.value ? "#CCFBF1" : "transparent",
                  color: view === option.value ? "#0F172A" : "#475569",
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

  const renderView = (imgSrc, regions, label, viewKey) => (
    <div style={{ flex: 1, textAlign: "center" }}>
      <div style={{
        fontSize: 12,
        fontWeight: 800,
        color: "#0F172A",
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
            <div style={{ fontSize: 12, fontWeight: 700, color: "#374151" }}>
              Selected Regions ({selectedRegions.length})
            </div>
            <button
              type="button"
              onClick={() => onClearAll?.()}
              style={{
                border: "1px solid #FECACA",
                background: "#FFF1F2",
                color: "#BE123C",
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
                    background: "#FEE2E2", color: "#DC2626", cursor: "pointer",
                    border: "1px solid #FECACA",
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

function renderDemographics(data, update) {
  const u = (path, val) => update("demographics", path, val);
  return (
    <>
      <h2 style={styles.sectionTitle}>Patient Demographics</h2>
      <p style={styles.sectionSubtitle}>Patient identification, caregiver, living situation, and advanced care planning</p>

      <Card title="Patient Information" hopeCode="A1110">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
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
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <FormSelect label="Preferred Language" value={data.preferredLanguage} onChange={(v) => u("preferredLanguage", v)}
            options={["English", "Spanish", "Chinese", "Vietnamese", "Tagalog", "Korean", "Other"]} />
          <FormCheckbox label="Needs Interpreter" checked={data.needsInterpreter} onChange={(v) => u("needsInterpreter", v)} />
          <FormInput label="Religion" value={data.religion} onChange={(v) => u("religion", v)} />
          <FormSelect label="Marital Status" value={data.maritalStatus} onChange={(v) => u("maritalStatus", v)}
            options={["Single", "Married", "Divorced", "Widowed", "Separated", "Domestic Partner"]} />
        </div>
      </Card>

      <Card title="Address">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
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
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
          <FormInput label="Name" value={data.emergencyContact?.name} onChange={(v) => u("emergencyContact.name", v)} />
          <FormInput label="Relationship" value={data.emergencyContact?.relationship} onChange={(v) => u("emergencyContact.relationship", v)} />
          <FormInput label="Phone" value={data.emergencyContact?.phone} onChange={(v) => u("emergencyContact.phone", v)} type="tel" />
        </div>
      </Card>

      <Card title="Primary Caregiver (PCG)" id="pcg">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
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
      </Card>

      {/* CDPH Gap #2 — Caregiver Willingness & Capability Evaluation */}
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
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
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

      <Card title="Living Situation" hopeCode="A1905">
        <FormSelect label="Site of Service" value={data.livingSituation?.siteOfService} onChange={(v) => u("livingSituation.siteOfService", v)}
          options={["Home", "SNF", "ALF", "Hospital", "Homeless", "Other"]} />
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
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
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

function renderGenericSection(sectionKey, data, update, config, demographics) {
  const u = (path, val) => update(sectionKey, path, val);
  const { title, subtitle, cards } = config;

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
      <h2 style={styles.sectionTitle}>{title}</h2>
      {subtitle && <p style={styles.sectionSubtitle}>{subtitle}</p>}
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

        return (
          <Card key={ci} title={card.title} hopeCode={card.hopeCode} sfv={card.sfv} cms={card.cms}>
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
                background: "#F8FAFC",
                border: "1px solid #E2E8F0",
                color: "#475569",
                fontSize: 12.5,
                lineHeight: 1.5,
              }}>
                <strong style={{ color: "#0F172A" }}>Body Map unavailable — </strong>
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

            {card.fields.map((field, fi) => {
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

              switch (fieldForRender.type) {
                case "input":
                  return <FormInput key={fi} label={fieldForRender.label} value={value} onChange={onChange}
                    type={fieldForRender.inputType} placeholder={fieldForRender.placeholder} required={fieldForRender.required} hopeCode={fieldForRender.hopeCode} />;
                case "textarea":
                  return <FormTextarea key={fi} label={fieldForRender.label} value={value} onChange={onChange}
                    placeholder={fieldForRender.placeholder} rows={fieldForRender.rows} />;
                case "select":
                  return <FormSelect key={fi} label={fieldForRender.label} value={value} onChange={onChange}
                    options={fieldForRender.options} required={fieldForRender.required} hopeCode={fieldForRender.hopeCode} />;
                case "radio":
                  return <FormRadioGroup key={fi} label={fieldForRender.label} value={value} onChange={onChange}
                    options={fieldForRender.options} hopeCode={fieldForRender.hopeCode} sfv={fieldForRender.sfv} />;
                case "checkboxGroup":
                  return <FormCheckboxGroup key={fi} label={fieldForRender.label} values={value || []} onChange={onChange}
                    options={fieldForRender.options} hopeCode={fieldForRender.hopeCode} />;
                case "checkbox":
                  return <FormCheckbox key={fi} label={fieldForRender.label} checked={value} onChange={onChange} />;
                default:
                  return null;
              }
            })}
          </Card>
        );
      })}
    </>
  );
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
        title: "Anthropometrics", fields: [
          { type: "input", label: "Height", path: "height", inputType: "number" },
          { type: "input", label: "Weight", path: "weight", inputType: "number" },
          { type: "input", label: "BMI", path: "bmi", inputType: "number" },
          { type: "input", label: "MAC (Mid-Arm Circumference)", path: "mac", inputType: "number" },
        ],
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
        title: "LCD Eligibility", fields: [
          { type: "checkbox", label: "Criteria A: PPS ≤ 70%", path: "ndsEligibility.criteriaA" },
          { type: "checkbox", label: "Criteria B: Dependence in 3+ ADLs", path: "ndsEligibility.criteriaB" },
          { type: "checkbox", label: "Criteria C: Comorbid conditions", path: "ndsEligibility.criteriaC" },
          { type: "input", label: "Disease-Specific LCD", path: "ndsEligibility.diseaseSpecificLCD" },
        ],
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
        { type: "radio", label: "Pulse Quality", path: "pulseQuality", options: ["Strong", "Weak", "Thready", "Bounding", "Irregular"] },
        { type: "checkbox", label: "Edema Present", path: "edema.present" },
        { type: "checkboxGroup", label: "Edema Location", path: "edema.location", options: ["Bilateral lower extremities", "Unilateral LE", "Sacral", "Periorbital", "Upper extremities", "Generalized"] },
        { type: "radio", label: "Edema Severity", path: "edema.severity", options: ["Trace", "1+", "2+", "3+", "4+"] },
        { type: "checkbox", label: "Chest Pain Present", path: "chestPain.present" },
        { type: "input", label: "Chest Pain Type", path: "chestPain.type" },
        { type: "input", label: "Peripheral Circulation", path: "peripheralCirculation" },
        { type: "input", label: "Heart Sounds", path: "heartSounds" },
        { type: "checkbox", label: "JVD (Jugular Venous Distention)", path: "jvd" },
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
        { type: "radio", label: "Exertion Level", path: "exertionLevel", options: ["At rest", "Minimal exertion", "Moderate exertion", "Severe exertion"] },
        { type: "checkbox", label: "Screened for shortness of breath", path: "shortnessOfBreathScreened" },
        { type: "input", label: "SOB screening date", path: "screeningDate", inputType: "date" },
        { type: "checkbox", label: "Treatment for shortness of breath initiated", path: "treatmentInitiated" },
        { type: "input", label: "SOB treatment date", path: "treatmentDate", inputType: "date" },
        { type: "checkboxGroup", label: "Lung Sounds", path: "lungSounds", options: ["Clear", "Crackles", "Wheezes", "Rhonchi", "Diminished", "Absent", "Stridor", "Pleural rub"] },
        { type: "checkboxGroup", label: "Respiration Pattern", path: "respirations", options: ["Regular", "Irregular", "Labored", "Cheyne-Stokes", "Apneic episodes", "Kussmaul", "Agonal"] },
        { type: "select", label: "Cough Type", path: "coughType", options: ["None", "Productive", "Non-productive", "Hemoptysis"] },
        { type: "input", label: "Sputum Character", path: "sputumCharacter" },
      ]},
      { title: "Oxygen Therapy", fields: [
        { type: "checkbox", label: "Oxygen in Use", path: "oxygenTherapy.inUse" },
        { type: "select", label: "Delivery Type", path: "oxygenTherapy.type", options: ["Nasal cannula", "Simple mask", "Non-rebreather", "Venturi mask", "High flow"] },
        { type: "input", label: "Liters/Minute", path: "oxygenTherapy.litersPerMinute", inputType: "number" },
        { type: "input", label: "Hours/Day", path: "oxygenTherapy.hoursPerDay" },
        { type: "input", label: "SpO2 on O2", path: "oxygenTherapy.satOnO2", inputType: "number" },
      ]},
      { title: "Notes", fields: [
        { type: "textarea", label: "Respiratory Notes", path: "notes" },
      ]},
    ],
  },

  infection: {
    title: "Immunological / Infection",
    subtitle: "Allergies, current infections, precautions",
    cards: [
      { title: "Infection Assessment", fields: [
        { type: "checkbox", label: "Immunosuppressed", path: "immunosuppressed" },
        { type: "checkboxGroup", label: "Precautions", path: "precautions", options: ["Standard", "Contact", "Droplet", "Airborne"] },
        { type: "textarea", label: "Current Infections", path: "notes", placeholder: "List active infections..." },
      ]},
    ],
  },

  gastrointestinal: {
    title: "Gastrointestinal",
    subtitle: "J2051D-G (Nausea, Vomiting, Diarrhea, Constipation), bowel, feeding devices",
    cards: [
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
    ],
  },
  endocrine: {
    title: "Endocrine",
    subtitle: "Thyroid, diabetes management, endocrine symptoms",
    cards: [
      { title: "Thyroid Assessment", fields: [
        { type: "radio", label: "Thyroid", path: "thyroid.assessment", options: ["Normal", "Enlarged", "Tender", "Nodular", "Not assessed"] },
        { type: "textarea", label: "Thyroid Notes", path: "thyroid.notes" },
      ]},
      { title: "Diabetes Management", fields: [
        { type: "radio", label: "Diabetes Type", path: "diabetes.type", options: ["Type 1", "Type 2", "Not diabetic", "Unknown"] },
        { type: "select", label: "Glucose Monitoring Frequency", path: "diabetes.glucoseMonitoring", options: ["None", "Daily", "BID", "TID", "QID", "Weekly"] },
        { type: "input", label: "Last HbA1c Value", path: "diabetes.lastHbA1c" },
        { type: "input", label: "Last HbA1c Date", path: "diabetes.lastHbA1cDate", inputType: "date" },
        { type: "input", label: "Insulin Type", path: "diabetes.insulinType" },
        { type: "input", label: "Insulin Dose", path: "diabetes.insulinDose" },
      ]},
      { title: "Endocrine Symptoms", fields: [
        { type: "checkboxGroup", label: "Symptoms Present", path: "endocrineSymptoms", options: ["Fatigue", "Weight changes", "Temperature intolerance", "Hair/skin changes", "Polydipsia", "Polyuria", "Tremors"] },
        { type: "textarea", label: "Endocrine Notes", path: "notes" },
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
      { title: "Wound Documentation & Notes", fields: [
        { type: "textarea", label: "Wound Impairment", path: "woundImpairment" },
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
          "Hoyer lift", "Egg crate mattress", "Incontinence supplies", "Wound care supplies"
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

// ════════════════════════════════════════════════════════════════
// 8. MAIN COMPONENT
// ════════════════════════════════════════════════════════════════

export default function RNICA({ patientId, assessmentId: existingAssessmentId = undefined, mode = "ica", onFormDataChange = undefined }) {
  const initialPatientId = patientId ?? getActivePatientId() ?? "";
  const [resolvedPatientId, setResolvedPatientId] = useState(initialPatientId);
  const [patientSummary, setPatientSummary] = useState(null);
  const [patientSummaryError, setPatientSummaryError] = useState("");
  const [formData, setFormData] = useState(JSON.parse(JSON.stringify(INITIAL_FORM)));
  const [activeSection, setActiveSection] = useState("demographics");
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
  const routes = useMemo(() => (isOngoing ? ROUTES.filter((route) => route.key !== "sfv") : ROUTES), [isOngoing]);
  const sidebarConfigItems = useMemo(() => {
    const items = isOngoing ? SIDEBAR_CONFIG.filter((item) => item.key !== "sfv") : SIDEBAR_CONFIG;
    return isOngoing ? items.map((item) => ({ ...item, hope: [] })) : items;
  }, [isOngoing]);

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

  const refreshIntelligence = useCallback(async (currentAssessmentId = assessmentId) => {
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
  }, [assessmentId]);

  // Load existing assessment
  useEffect(() => {
    if (existingAssessmentId) {
      api.getRNICAAssessment(existingAssessmentId)
        .then((data) => {
          if (data.formData) setFormData(data.formData);
          if (data.locked) setLocked(true);
          return data;
        })
        .then((data) => {
          if (data?.assessmentId) {
            setAssessmentId(data.assessmentId);
            return refreshIntelligence(data.assessmentId);
          }
          return refreshIntelligence(existingAssessmentId);
        })
        .catch((err) => {
          console.error("Failed to load assessment:", err);
          setPageError(err instanceof Error ? err.message : "Unable to load RN ICA assessment.");
        });
    }
  }, [existingAssessmentId, refreshIntelligence]);

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
      setSaveStatus("saved");
    } catch (err) {
      console.error("Save error:", err);
      setSaveStatus("error");
      setPageError(err instanceof Error ? err.message : "Unable to save RN ICA assessment.");
    } finally {
      setSaving(false);
    }
  }, [assessmentId, formData, patientId, refreshIntelligence]);

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

  // Navigate
  const goNext = () => {
    const idx = routes.findIndex((r) => r.key === activeSection);
    if (idx < routes.length - 1) setActiveSection(routes[idx + 1].key);
  };
  const goPrev = () => {
    const idx = routes.findIndex((r) => r.key === activeSection);
    if (idx > 0) setActiveSection(routes[idx - 1].key);
  };

  // Render current section
  const renderSection = () => {
    if (activeSection === "demographics") {
      return renderDemographics(formData.demographics, updateField);
    }

    const config = SECTION_CONFIGS[currentRoute?.formSection];
    if (config && currentSectionData) {
      return renderGenericSection(currentRoute.formSection, currentSectionData, updateField, config, formData.demographics);
    }

    return (
      <div style={styles.card}>
        <p style={{ color: COLORS.gray }}>Section "{activeSection}" — content loading...</p>
      </div>
    );
  };

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
          <div style={{
            ...styles.statusBadge,
            background: locked ? COLORS.success : COLORS.warning,
            color: COLORS.white, marginTop: 4,
          }}>
            {locked ? "LOCKED" : "IN PROGRESS"}
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
              setActiveSection(match.parent);
              setTimeout(() => {
                const el = document.getElementById(match.scrollTarget);
                if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
              }, 100);
              return;
            }

            setActiveSection(key);
          }}
        />

        {/* ── Main Content ── */}
        <div style={styles.mainArea}>
          <div style={styles.content}>
            {!isOngoing && sfvStatus.required && (activeSection === "symptomImpact" || activeSection === "sfv") && (
              <div style={{ ...styles.warningBox, marginBottom: 16, border: "1px solid rgba(234, 88, 12, 0.28)", background: "linear-gradient(135deg, #fff7ed, #fffbeb)" }}>
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
            {renderSection()}
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
                  <div key={key} style={{ fontSize: 11, color: COLORS.error, marginBottom: 4, padding: 4, background: "#FEF2F2", borderRadius: 4 }}>
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
                  <div key={key} style={{ fontSize: 11, color: COLORS.warning, marginBottom: 4, padding: 4, background: "#FFFBEB", borderRadius: 4 }}>
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
                    <div key={`${finding.category}-${idx}`} style={{ marginBottom: 8, padding: 8, borderRadius: 8, background: finding.severity === "high" ? "#FEF2F2" : finding.severity === "moderate" ? "#FFFBEB" : "#F8FAFC", border: `1px solid ${finding.severity === "high" ? "#FECACA" : finding.severity === "moderate" ? "#FDE68A" : COLORS.border}` }}>
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