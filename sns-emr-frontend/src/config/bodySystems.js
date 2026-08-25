const SHARED_BODY_SYSTEM_CONFIG = [
  {
    visitNote: {
      key: "neuro_mental_sensory",
      label: "Neuro/Mental/Sensory",
      sectionId: "neuro",
      findings: [
        ["anxiety", "Anxiety"],
        ["agitation", "Agitation"],
        ["confusion", "Confusion"],
        ["cognitive_change", "Cognitive change"],
        ["speech_communication_change", "Speech/communication change"],
      ],
    },
    rnica: {
      key: "neurological",
      label: "Neurological",
      formSection: "neurological",
      regulator: "HOPE",
      hope: ["N0500", "N0510", "N0520"],
      icon: "🧠",
      color: "green",
      sfv: true,
    },
  },
  {
    visitNote: {
      key: "cardiovascular",
      label: "Cardiovascular",
      sectionId: "cardiovascular",
      findings: [
        ["arrhythmia", "Arrhythmia"],
        ["edema", "Edema"],
        ["chest_discomfort", "Chest discomfort"],
      ],
    },
    rnica: {
      key: "cardiovascular",
      label: "Cardiovascular",
      formSection: "cardiovascular",
      hope: [],
      icon: "❤️",
      color: null,
    },
  },
  {
    visitNote: {
      key: "respiratory",
      label: "Respiratory",
      sectionId: "respiratory",
      findings: [
        ["dyspnea", "Dyspnea"],
        ["cough", "Cough"],
        ["abnormal_breath_sounds", "Abnormal breath sounds"],
      ],
    },
    rnica: {
      key: "respiratory",
      label: "Respiratory",
      formSection: "respiratory",
      hope: [],
      icon: "🫁",
      color: null,
      sfv: true,
    },
  },
  {
    visitNote: {
      key: "immunological_infection",
      label: "Immunological/Infection",
      sectionId: "immunological",
      findings: [
        ["fever", "Fever"],
        ["signs_of_infection", "Signs of infection"],
        ["isolation_precautions", "Isolation precautions"],
      ],
    },
    rnica: {
      key: "infection",
      label: "Infection",
      formSection: "infection",
      hope: [],
      icon: "🦠",
      color: null,
    },
  },
  {
    visitNote: {
      key: "gi_digestive",
      label: "GI/Digestive",
      sectionId: "gi",
      findings: [
        ["nausea", "Nausea"],
        ["vomiting", "Vomiting"],
        ["constipation", "Constipation"],
        ["diarrhea", "Diarrhea"],
        ["incontinence", "Incontinence"],
      ],
    },
    rnica: {
      key: "gastrointestinal",
      label: "Gastrointestinal",
      formSection: "gastrointestinal",
      hope: [],
      icon: "🍽️",
      color: null,
      sfv: true,
    },
  },
  {
    visitNote: {
      key: "nutrition",
      label: "Nutrition",
      sectionId: "nutrition",
      findings: [
        ["appetite_decline", "Appetite decline"],
        ["meal_refusal", "Meal refusal"],
        ["dysphagia", "Dysphagia"],
        ["artificial_feeding", "Artificial feeding"],
      ],
    },
    rnica: {
      key: "nutrition",
      label: "Nutrition",
      formSection: "nutrition",
      hope: [],
      icon: "🥗",
      color: null,
    },
  },
  {
    visitNote: {
      key: "endocrine",
      label: "Endocrine",
      sectionId: "endocrine",
      findings: [
        ["glucose_instability", "Glucose instability"],
        ["polyuria", "Polyuria"],
        ["polydipsia", "Polydipsia"],
      ],
    },
    rnica: {
      key: "endocrine",
      label: "Endocrine",
      formSection: "endocrine",
      hope: [],
      icon: "🔄",
      color: null,
    },
  },
  {
    visitNote: {
      key: "gu_reproductive",
      label: "GU/Reproductive",
      sectionId: "gu",
      findings: [
        ["urgency", "Urgency"],
        ["retention", "Retention"],
        ["dysuria", "Dysuria"],
      ],
    },
    rnica: {
      key: "genitourinary",
      label: "Genitourinary",
      formSection: "genitourinary",
      hope: [],
      icon: "💧",
      color: null,
    },
  },
  {
    visitNote: {
      key: "musculoskeletal",
      label: "Musculoskeletal",
      sectionId: "musculoskeletal",
      findings: [
        ["weakness", "Weakness"],
        ["stiffness", "Stiffness"],
        ["contracture", "Contracture"],
      ],
    },
    rnica: {
      key: "musculoskeletal",
      label: "Musculoskeletal",
      formSection: "musculoskeletal",
      hope: [],
      icon: "🦴",
      color: null,
    },
  },
  {
    visitNote: {
      key: "integumentary_skin",
      label: "Integumentary/Skin",
      sectionId: "skin",
      findings: [
        ["rash", "Rash"],
        ["wound", "Wound"],
        ["ulcer_pressure_injury", "Ulcer / pressure injury"],
      ],
    },
    rnica: {
      key: "skin",
      label: "Integumentary - Skin",
      formSection: "skin",
      regulator: "HOPE",
      hope: ["M1190"],
      icon: "🩹",
      color: "green",
    },
  },
];

const VISIT_NOTE_ONLY_BODY_SYSTEMS = [
  {
    key: "sleep_rest",
    label: "Sleep/Rest",
    sectionId: "sleep-rest",
    findings: [
      ["insomnia", "Insomnia"],
      ["somnolence", "Somnolence / increased sleeping"],
    ],
  },
  {
    key: "mobility",
    label: "Mobility",
    sectionId: "mobility",
    findings: [
      ["bedbound", "Bedbound / non-ambulatory"],
      ["endurance_decline", "Endurance decline"],
    ],
  },
  {
    key: "adl_assessment",
    label: "ADL",
    sectionId: "adl",
    findings: [],
  },
  {
    key: "fall_incidence",
    label: "Fall/Incident",
    sectionId: "falls-safety",
    findings: [
      ["fall_reported", "Fall reported"],
      ["injury_reported", "Injury reported"],
      ["near_fall", "Near fall"],
    ],
  },
  {
    key: "safety_issues",
    label: "Safety",
    sectionId: "falls-safety",
    findings: [
      ["medication_safety", "Medication safety concern"],
      ["transfer_safety", "Transfer safety concern"],
      ["environmental_hazard", "Environmental hazard"],
    ],
  },
];

export const VISIT_NOTE_BODY_SYSTEM_DEFINITIONS = [
  ...SHARED_BODY_SYSTEM_CONFIG.map((system) => ({ ...system.visitNote })),
  ...VISIT_NOTE_ONLY_BODY_SYSTEMS.map((system) => ({ ...system })),
];

export const RNICA_BODY_SYSTEM_MODULES = SHARED_BODY_SYSTEM_CONFIG.map((system) => ({
  key: system.rnica.key,
  label: system.rnica.label,
  formSection: system.rnica.formSection,
  ...(system.rnica.regulator ? { regulator: system.rnica.regulator } : {}),
  ...(system.rnica.hope ? { hope: [...system.rnica.hope] } : {}),
}));

export const RNICA_BODY_SYSTEM_SIDEBAR_ITEMS = SHARED_BODY_SYSTEM_CONFIG.map((system) => ({
  key: system.rnica.key,
  label: system.rnica.label,
  icon: system.rnica.icon,
  hope: [...(system.rnica.hope || [])],
  color: system.rnica.color ?? null,
  ...(system.rnica.sfv ? { sfv: true } : {}),
}));
