export const SEVERITY_OPTIONS = [
  { value: "NONE", label: "None (0)", rank: 0 },
  { value: "MILD", label: "Mild (1-3)", rank: 1 },
  { value: "MODERATE", label: "Moderate (4-6)", rank: 2 },
  { value: "SEVERE", label: "Severe (7-10)", rank: 3 },
];

export const SEVERITY_LABELS = Object.fromEntries(SEVERITY_OPTIONS.map((option) => [option.value, option.label]));
export const SEVERITY_RANKS = Object.fromEntries(SEVERITY_OPTIONS.map((option) => [option.value, option.rank]));

export const ADL_ACTIVITIES = [
  { key: "bathing", label: "Bathing" },
  { key: "dressing", label: "Dressing" },
  { key: "toileting", label: "Toileting" },
  { key: "transferring", label: "Transferring" },
  { key: "feeding", label: "Feeding" },
  { key: "grooming", label: "Grooming" },
];

export const FUNCTIONAL_SCORE_OPTIONS = Array.from({ length: 11 }, (_, index) => {
  const value = String(index * 10);
  return { value, label: value };
});

export const FAST_OPTIONS = [
  "1",
  "2",
  "3",
  "4",
  "5",
  "6a",
  "6b",
  "6c",
  "6d",
  "6e",
  "7a",
  "7b",
  "7c",
  "7d",
  "7e",
  "7f",
].map((value) => ({ value, label: value.toUpperCase() }));

export const NYHA_OPTIONS = [
  { value: "I", label: "Class I" },
  { value: "II", label: "Class II" },
  { value: "III", label: "Class III" },
  { value: "IV", label: "Class IV" },
];

export const RESPONSE_OPTIONS = [
  { value: "YES", label: "Yes" },
  { value: "NO", label: "No" },
  { value: "UNABLE", label: "Unable to determine" },
  { value: "NA", label: "Not applicable" },
];

export const CONCERN_OPTIONS = [
  { value: "YES", label: "Yes" },
  { value: "NO", label: "No" },
  { value: "UNABLE", label: "Unable to assess" },
];

export const PRESENT_OPTIONS = [
  { value: "PRESENT", label: "Present" },
  { value: "NOT_PRESENT", label: "Not present" },
];

export const FOLLOW_UP_OPTIONS = [
  { value: "YES", label: "Yes" },
  { value: "NO", label: "No" },
];

export const ORAL_INTAKE_OPTIONS = [
  { value: "NORMAL", label: "Normal" },
  { value: "REDUCED", label: "Reduced" },
  { value: "MINIMAL", label: "Minimal" },
  { value: "SIPS_ONLY", label: "Sips only" },
  { value: "NPO", label: "NPO" },
];

export const AMBULATORY_STATUS_OPTIONS = [
  { value: "AMBULATORY", label: "Ambulatory" },
  { value: "LIMITED", label: "Limited ambulation" },
  { value: "TRANSFER_ONLY", label: "Transfer only" },
  { value: "NON_AMBULATORY", label: "Non-ambulatory" },
];

export const ASSISTANCE_LEVEL_OPTIONS = [
  { value: "INDEPENDENT", label: "Independent" },
  { value: "STANDBY", label: "Standby assist" },
  { value: "ONE_PERSON", label: "One-person assist" },
  { value: "TWO_PERSON", label: "Two-person assist" },
  { value: "TOTAL", label: "Total assist" },
];

export const BODY_SYSTEM_DEFINITIONS = [
  {
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
  {
    key: "cardiovascular",
    label: "Cardiovascular",
    sectionId: "cardiovascular",
    findings: [
      ["arrhythmia", "Arrhythmia"],
      ["edema", "Edema"],
      ["chest_discomfort", "Chest discomfort"],
    ],
  },
  {
    key: "respiratory",
    label: "Respiratory",
    sectionId: "respiratory",
    findings: [
      ["dyspnea", "Dyspnea"],
      ["cough", "Cough"],
      ["abnormal_breath_sounds", "Abnormal breath sounds"],
    ],
  },
  {
    key: "immunological_infection",
    label: "Immunological/Infection",
    sectionId: "immunological",
    findings: [
      ["fever", "Fever"],
      ["signs_of_infection", "Signs of infection"],
      ["isolation_precautions", "Isolation precautions"],
    ],
  },
  {
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
  {
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
  {
    key: "endocrine",
    label: "Endocrine",
    sectionId: "endocrine",
    findings: [
      ["glucose_instability", "Glucose instability"],
      ["polyuria", "Polyuria"],
      ["polydipsia", "Polydipsia"],
    ],
  },
  {
    key: "gu_reproductive",
    label: "GU/Reproductive",
    sectionId: "gu",
    findings: [
      ["urgency", "Urgency"],
      ["retention", "Retention"],
      ["dysuria", "Dysuria"],
    ],
  },
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
    key: "musculoskeletal",
    label: "Musculoskeletal",
    sectionId: "musculoskeletal",
    findings: [
      ["weakness", "Weakness"],
      ["stiffness", "Stiffness"],
      ["contracture", "Contracture"],
    ],
  },
  {
    key: "integumentary_skin",
    label: "Integumentary/Skin",
    sectionId: "skin",
    findings: [
      ["rash", "Rash"],
      ["wound", "Wound"],
      ["ulcer_pressure_injury", "Ulcer / pressure injury"],
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

export const BODY_SYSTEM_LOOKUP = Object.fromEntries(BODY_SYSTEM_DEFINITIONS.map((definition) => [definition.key, definition]));
export const BODY_SYSTEM_FINDING_LABELS = BODY_SYSTEM_DEFINITIONS.reduce((accumulator, definition) => {
  definition.findings.forEach(([value, label]) => {
    accumulator[value] = label;
  });
  return accumulator;
}, {});

export const VISIT_NOTE_SECTION_ITEMS = [
  { id: "top", label: "Top" },
  { id: "pain", label: "Pain" },
  { id: "vitals", label: "Vitals" },
  { id: "function", label: "Function" },
  { id: "nutrition", label: "Nutrition" },
  { id: "neuro", label: "Neuro" },
  { id: "cardiovascular", label: "Cardiovascular" },
  { id: "respiratory", label: "Respiratory" },
  { id: "gi", label: "GI" },
  { id: "gu", label: "GU" },
  { id: "skin", label: "Skin" },
  { id: "mobility", label: "Mobility" },
  { id: "adl", label: "ADL" },
  { id: "falls-safety", label: "Falls/Safety" },
  { id: "rn-supervision", label: "RN Supervision" },
  { id: "care-provided", label: "Care Provided" },
  { id: "checklist", label: "Checklist" },
  { id: "narrative", label: "Narrative" },
];

// Discipline-specific nav item not part of the canonical full-body (RN)
// order above — SC/MSW visits substitute a "Symptoms" section for the
// full body-system review, so it is inserted at render time rather than
// baked into the master ordering the spec defines for RN visit notes.
export const VISIT_NOTE_SYMPTOMS_SECTION_ITEM = { id: "symptoms", label: "Symptoms" };

// Computes the sticky nav items that actually exist on the page for the
// current visit note context, in the spec-required RN order. SC/MSW visits
// get a compact Symptoms-based nav instead of the full body-system list.
export function buildVisitNoteNavItems({ isFullBody, isSpiritualVisit, isMswVisit, isContinuousCare, showSupervision }) {
  if (isContinuousCare) {
    return [
      VISIT_NOTE_SECTION_ITEMS.find((item) => item.id === "top"),
      VISIT_NOTE_SECTION_ITEMS.find((item) => item.id === "narrative"),
    ].filter(Boolean);
  }
  if (isSpiritualVisit || isMswVisit) {
    return [
      VISIT_NOTE_SECTION_ITEMS.find((item) => item.id === "top"),
      VISIT_NOTE_SECTION_ITEMS.find((item) => item.id === "pain"),
      VISIT_NOTE_SYMPTOMS_SECTION_ITEM,
      VISIT_NOTE_SECTION_ITEMS.find((item) => item.id === "care-provided"),
      VISIT_NOTE_SECTION_ITEMS.find((item) => item.id === "narrative"),
    ].filter(Boolean);
  }
  if (!isFullBody) {
    return [
      VISIT_NOTE_SECTION_ITEMS.find((item) => item.id === "top"),
      VISIT_NOTE_SECTION_ITEMS.find((item) => item.id === "narrative"),
    ].filter(Boolean);
  }
  return VISIT_NOTE_SECTION_ITEMS.filter((item) => {
    if (item.id === "rn-supervision") return showSupervision;
    return true;
  });
}

function stringValue(value) {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

export function hasDocumentedValue(value) {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  return true;
}

export function formatComparableDate(value) {
  if (!value) return "—";
  const normalized = String(value).slice(0, 10);
  const [year, month, day] = normalized.split("-");
  if (year && month && day) return `${month}/${day}/${year}`;
  return String(value);
}

export function buildVisitDateTime(content) {
  const visitDate = stringValue(content?.visit_date);
  const visitTime = stringValue(content?.time_in) || "00:00";
  if (!visitDate) return null;
  const parsed = new Date(`${visitDate}T${visitTime.length === 5 ? `${visitTime}:00` : visitTime}`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function numberValue(value) {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function enumLabel(options, value) {
  const normalized = stringValue(value).toUpperCase();
  const match = options.find((option) => option.value === normalized || option.value === value);
  return match?.label || stringValue(value);
}

function summarizeFindings(selectedFindings = []) {
  return selectedFindings
    .map((finding) => BODY_SYSTEM_FINDING_LABELS[finding] || finding)
    .filter(Boolean)
    .join(", ");
}

function summarizeBodySystem(row, systemKey) {
  const bodySystem = row || {};
  const parts = [];
  if (bodySystem.assessed_no_issues) {
    parts.push("No issues reported");
  }
  if (bodySystem.severity) {
    parts.push(SEVERITY_LABELS[String(bodySystem.severity).toUpperCase()] || bodySystem.severity);
  }
  const findings = summarizeFindings(bodySystem.selected_findings || []);
  if (findings) parts.push(findings);
  if (systemKey === "nutrition") {
    if (bodySystem.oral_intake) {
      parts.push(enumLabel(ORAL_INTAKE_OPTIONS, bodySystem.oral_intake));
    }
    if (bodySystem.diet) parts.push(`Diet: ${bodySystem.diet}`);
    if (bodySystem.diet_specify) parts.push(`Diet detail: ${bodySystem.diet_specify}`);
  }
  if (systemKey === "gu_reproductive") {
    if (bodySystem.incontinent) parts.push(`Incontinence: ${bodySystem.incontinent}`);
    if (bodySystem.last_bm) parts.push(`Last BM: ${formatComparableDate(bodySystem.last_bm)}`);
  }
  if (systemKey === "mobility") {
    if (bodySystem.ambulatory_status) parts.push(enumLabel(AMBULATORY_STATUS_OPTIONS, bodySystem.ambulatory_status));
    if (bodySystem.assistive_device) parts.push(`Assistive device: ${bodySystem.assistive_device}`);
    if (bodySystem.assistance_level) parts.push(enumLabel(ASSISTANCE_LEVEL_OPTIONS, bodySystem.assistance_level));
    if (bodySystem.endurance) parts.push(`Endurance: ${bodySystem.endurance}`);
    if (bodySystem.bedbound_status) parts.push(bodySystem.bedbound_status);
  }
  if (systemKey === "adl_assessment" && hasDocumentedValue(bodySystem.adl_total_score)) {
    parts.push(`ADL score ${bodySystem.adl_total_score}`);
  }
  if (bodySystem.other_symptom) parts.push(bodySystem.other_symptom);
  if (bodySystem.other_observation) parts.push(bodySystem.other_observation);
  return parts.join(" · ");
}

function rawToDisplay(raw, unit = "") {
  if (!hasDocumentedValue(raw)) return "";
  return `${raw}${unit}`.trim();
}

function buildMetric(label, sectionId, currentMetric, previousMetric, config = {}) {
  const currentPresent = hasDocumentedValue(currentMetric?.raw) || hasDocumentedValue(currentMetric?.display);
  const previousPresent = hasDocumentedValue(previousMetric?.raw) || hasDocumentedValue(previousMetric?.display);
  const currentDisplay = currentMetric?.display || rawToDisplay(currentMetric?.raw, config.unit || "");
  const previousDisplay = previousMetric?.display || rawToDisplay(previousMetric?.raw, config.unit || "");
  const currentNumeric = numberValue(currentMetric?.compareValue ?? currentMetric?.raw);
  const previousNumeric = numberValue(previousMetric?.compareValue ?? previousMetric?.raw);
  const delta = currentNumeric !== null && previousNumeric !== null ? Number((currentNumeric - previousNumeric).toFixed(2)) : null;

  let statusLabel = "No previous documented value";
  let summaryLabel = currentDisplay;
  let changeText = "";

  if (!previousPresent) {
    statusLabel = "No previous documented value";
  } else if (!currentPresent) {
    statusLabel = "Not comparable";
  } else if (config.rankMap) {
    const currentRank = config.rankMap[String(currentMetric?.compareValue ?? currentMetric?.raw).toUpperCase()];
    const previousRank = config.rankMap[String(previousMetric?.compareValue ?? previousMetric?.raw).toUpperCase()];
    if (currentRank === undefined || previousRank === undefined) {
      statusLabel = currentDisplay === previousDisplay ? "Stable" : "Not comparable";
    } else if (currentRank === previousRank) {
      statusLabel = "Stable";
    } else if (config.direction === "higher-is-worse") {
      statusLabel = currentRank > previousRank ? "Worsened" : "Improved";
    } else if (config.direction === "lower-is-worse") {
      statusLabel = currentRank < previousRank ? "Worsened" : "Improved";
    } else {
      statusLabel = "Not comparable";
    }
  } else if (currentNumeric !== null && previousNumeric !== null) {
    if (Math.abs(currentNumeric - previousNumeric) < 0.0001) {
      statusLabel = "Stable";
    } else if (config.direction === "higher-is-worse") {
      statusLabel = currentNumeric > previousNumeric ? "Worsened" : "Improved";
    } else if (config.direction === "lower-is-worse") {
      statusLabel = currentNumeric < previousNumeric ? "Worsened" : "Improved";
    } else {
      statusLabel = "Not comparable";
    }
  } else {
    statusLabel = currentDisplay === previousDisplay ? "Stable" : "Not comparable";
  }

  if (delta !== null && config.deltaFormatter) {
    changeText = config.deltaFormatter(delta, previousNumeric, currentNumeric);
  } else if (delta !== null && config.unit) {
    changeText = `${delta > 0 ? "+" : ""}${delta} ${config.unit}`.trim();
  } else if (delta !== null) {
    changeText = `${delta > 0 ? "+" : ""}${delta}`;
  }

  if (previousPresent && currentPresent) {
    summaryLabel = `${previousDisplay} → ${currentDisplay}`;
  } else if (currentPresent) {
    summaryLabel = currentDisplay;
  } else if (previousPresent) {
    summaryLabel = previousDisplay;
  }

  return {
    key: config.key || `${sectionId}-${label}`.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
    label,
    sectionId,
    previousDisplay,
    previousDate: previousMetric?.date || previousMetric?.visitDate || "",
    previousVisitType: previousMetric?.visitType || "",
    currentDisplay,
    statusLabel,
    changeText,
    currentPresent,
    previousPresent,
    showInSummary: previousPresent && currentPresent,
    summaryLabel,
  };
}

function metricValue(raw, display, extra = {}) {
  return { raw, display, ...extra };
}

function getBodySystem(content, key) {
  return content?.signs_symptoms?.[key] || {};
}

function getFunctional(content) {
  return content?.functional_decline || {};
}

function getSnapshotMetricGroups(content, previousMeta = undefined) {
  const pain = content?.pain || {};
  const vitals = content?.vitals || {};
  const functional = getFunctional(content);
  const mobility = getBodySystem(content, "mobility");
  const adl = getBodySystem(content, "adl_assessment");
  const nutrition = getBodySystem(content, "nutrition");

  return {
    pain: [
      buildMetric(
        "Pain level",
        "pain",
        metricValue(pain.pain_level, hasDocumentedValue(pain.pain_level) ? String(pain.pain_level) : ""),
        metricValue(previousMeta?.pain?.pain_level, hasDocumentedValue(previousMeta?.pain?.pain_level) ? String(previousMeta.pain.pain_level) : "", previousMeta),
        { key: "pain-level", direction: "higher-is-worse" }
      ),
    ],
    vitals: [
      buildMetric("Temperature", "vitals", metricValue(vitals.temperature, stringValue(vitals.temperature)), metricValue(previousMeta?.vitals?.temperature, stringValue(previousMeta?.vitals?.temperature), previousMeta), { key: "temperature" }),
      buildMetric("Pulse", "vitals", metricValue(vitals.pulse, stringValue(vitals.pulse)), metricValue(previousMeta?.vitals?.pulse, stringValue(previousMeta?.vitals?.pulse), previousMeta), { key: "pulse" }),
      buildMetric("Respirations", "vitals", metricValue(vitals.respirations, stringValue(vitals.respirations)), metricValue(previousMeta?.vitals?.respirations, stringValue(previousMeta?.vitals?.respirations), previousMeta), { key: "respirations" }),
      buildMetric(
        "Blood pressure",
        "vitals",
        metricValue(
          `${stringValue(vitals.bp_systolic)}/${stringValue(vitals.bp_diastolic)}`.replace(/^\/|\/$/g, ""),
          `${stringValue(vitals.bp_systolic)}/${stringValue(vitals.bp_diastolic)}`.replace(/^\/|\/$/g, "")
        ),
        metricValue(
          `${stringValue(previousMeta?.vitals?.bp_systolic)}/${stringValue(previousMeta?.vitals?.bp_diastolic)}`.replace(/^\/|\/$/g, ""),
          `${stringValue(previousMeta?.vitals?.bp_systolic)}/${stringValue(previousMeta?.vitals?.bp_diastolic)}`.replace(/^\/|\/$/g, ""),
          previousMeta
        ),
        { key: "blood-pressure" }
      ),
      buildMetric("O2 saturation", "vitals", metricValue(vitals.o2_sat, stringValue(vitals.o2_sat)), metricValue(previousMeta?.vitals?.o2_sat, stringValue(previousMeta?.vitals?.o2_sat), previousMeta), { key: "o2-sat" }),
      buildMetric("O2 delivery", "vitals", metricValue(vitals.o2_delivery, stringValue(vitals.o2_delivery)), metricValue(previousMeta?.vitals?.o2_delivery, stringValue(previousMeta?.vitals?.o2_delivery), previousMeta), { key: "o2-delivery" }),
    ],
    function: [
      buildMetric(
        "Mobility",
        "mobility",
        metricValue(mobility.severity || mobility.ambulatory_status, summarizeBodySystem(mobility, "mobility")),
        metricValue(previousMeta?.signs_symptoms?.mobility?.severity || previousMeta?.signs_symptoms?.mobility?.ambulatory_status, summarizeBodySystem(previousMeta?.signs_symptoms?.mobility || {}, "mobility"), previousMeta),
        { key: "mobility", rankMap: SEVERITY_RANKS, direction: "higher-is-worse" }
      ),
      buildMetric(
        "ADL score",
        "adl",
        metricValue(adl.adl_total_score, hasDocumentedValue(adl.adl_total_score) ? String(adl.adl_total_score) : summarizeBodySystem(adl, "adl_assessment")),
        metricValue(previousMeta?.signs_symptoms?.adl_assessment?.adl_total_score, hasDocumentedValue(previousMeta?.signs_symptoms?.adl_assessment?.adl_total_score) ? String(previousMeta.signs_symptoms.adl_assessment.adl_total_score) : summarizeBodySystem(previousMeta?.signs_symptoms?.adl_assessment || {}, "adl_assessment"), previousMeta),
        { key: "adl-score", direction: "higher-is-worse", deltaFormatter: (delta) => `${delta > 0 ? "+" : ""}${delta} points` }
      ),
      buildMetric(
        "KPS",
        "function",
        metricValue(functional.kps, stringValue(functional.kps)),
        metricValue(previousMeta?.functional_decline?.kps, stringValue(previousMeta?.functional_decline?.kps), previousMeta),
        { key: "kps", direction: "lower-is-worse", deltaFormatter: (delta) => `${delta > 0 ? "+" : ""}${delta} points` }
      ),
      buildMetric(
        "PPS",
        "function",
        metricValue(functional.pps, stringValue(functional.pps)),
        metricValue(previousMeta?.functional_decline?.pps, stringValue(previousMeta?.functional_decline?.pps), previousMeta),
        { key: "pps", direction: "lower-is-worse", deltaFormatter: (delta) => `${delta > 0 ? "+" : ""}${delta} points` }
      ),
      buildMetric(
        "FAST",
        "function",
        metricValue(functional.fast, stringValue(functional.fast).toUpperCase()),
        metricValue(previousMeta?.functional_decline?.fast, stringValue(previousMeta?.functional_decline?.fast).toUpperCase(), previousMeta),
        {
          key: "fast",
          rankMap: {
            "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6A": 6.1, "6B": 6.2, "6C": 6.3, "6D": 6.4, "6E": 6.5,
            "7A": 7.1, "7B": 7.2, "7C": 7.3, "7D": 7.4, "7E": 7.5, "7F": 7.6,
          },
          direction: "higher-is-worse",
        }
      ),
      buildMetric(
        "NYHA",
        "function",
        metricValue(functional.nyha, enumLabel(NYHA_OPTIONS, functional.nyha)),
        metricValue(previousMeta?.functional_decline?.nyha, enumLabel(NYHA_OPTIONS, previousMeta?.functional_decline?.nyha), previousMeta),
        { key: "nyha", rankMap: { I: 1, II: 2, III: 3, IV: 4 }, direction: "higher-is-worse" }
      ),
    ],
    nutrition: [
      buildMetric(
        "Nutrition",
        "nutrition",
        metricValue(nutrition.severity || nutrition.oral_intake, summarizeBodySystem(nutrition, "nutrition")),
        metricValue(previousMeta?.signs_symptoms?.nutrition?.severity || previousMeta?.signs_symptoms?.nutrition?.oral_intake, summarizeBodySystem(previousMeta?.signs_symptoms?.nutrition || {}, "nutrition"), previousMeta),
        { key: "nutrition", rankMap: SEVERITY_RANKS, direction: "higher-is-worse" }
      ),
      buildMetric(
        "Weight",
        "nutrition",
        metricValue(vitals.weight, rawToDisplay(vitals.weight, " lb")),
        metricValue(previousMeta?.vitals?.weight, rawToDisplay(previousMeta?.vitals?.weight, " lb"), previousMeta),
        { key: "weight", direction: "lower-is-worse", deltaFormatter: (delta) => `${delta > 0 ? "+" : ""}${delta} lb` }
      ),
      buildMetric(
        "MAC",
        "nutrition",
        metricValue(vitals.mac, rawToDisplay(vitals.mac, " cm")),
        metricValue(previousMeta?.vitals?.mac, rawToDisplay(previousMeta?.vitals?.mac, " cm"), previousMeta),
        { key: "mac", deltaFormatter: (delta) => `${delta > 0 ? "+" : ""}${delta} cm` }
      ),
      buildMetric(
        "BMI",
        "nutrition",
        metricValue(vitals.bmi, stringValue(vitals.bmi)),
        metricValue(previousMeta?.vitals?.bmi, stringValue(previousMeta?.vitals?.bmi), previousMeta),
        { key: "bmi", deltaFormatter: (delta) => `${delta > 0 ? "+" : ""}${delta}` }
      ),
    ],
    systems: BODY_SYSTEM_DEFINITIONS.filter((definition) => !["nutrition", "mobility", "adl_assessment", "fall_incidence", "safety_issues"].includes(definition.key))
      .map((definition) => buildMetric(
        definition.label,
        definition.sectionId,
        metricValue(getBodySystem(content, definition.key).severity || summarizeBodySystem(getBodySystem(content, definition.key), definition.key), summarizeBodySystem(getBodySystem(content, definition.key), definition.key)),
        metricValue(previousMeta?.signs_symptoms?.[definition.key]?.severity || summarizeBodySystem(previousMeta?.signs_symptoms?.[definition.key] || {}, definition.key), summarizeBodySystem(previousMeta?.signs_symptoms?.[definition.key] || {}, definition.key), previousMeta),
        { key: definition.key, rankMap: SEVERITY_RANKS, direction: "higher-is-worse" }
      )),
    fallsSafety: [
      buildMetric(
        "Fall / Incident",
        "falls-safety",
        metricValue(getBodySystem(content, "fall_incidence").severity || summarizeBodySystem(getBodySystem(content, "fall_incidence"), "fall_incidence"), summarizeBodySystem(getBodySystem(content, "fall_incidence"), "fall_incidence")),
        metricValue(previousMeta?.signs_symptoms?.fall_incidence?.severity || summarizeBodySystem(previousMeta?.signs_symptoms?.fall_incidence || {}, "fall_incidence"), summarizeBodySystem(previousMeta?.signs_symptoms?.fall_incidence || {}, "fall_incidence"), previousMeta),
        { key: "fall-incidence", rankMap: SEVERITY_RANKS, direction: "higher-is-worse" }
      ),
      buildMetric(
        "Safety",
        "falls-safety",
        metricValue(getBodySystem(content, "safety_issues").severity || summarizeBodySystem(getBodySystem(content, "safety_issues"), "safety_issues"), summarizeBodySystem(getBodySystem(content, "safety_issues"), "safety_issues")),
        metricValue(previousMeta?.signs_symptoms?.safety_issues?.severity || summarizeBodySystem(previousMeta?.signs_symptoms?.safety_issues || {}, "safety_issues"), summarizeBodySystem(previousMeta?.signs_symptoms?.safety_issues || {}, "safety_issues"), previousMeta),
        { key: "safety-issues", rankMap: SEVERITY_RANKS, direction: "higher-is-worse" }
      ),
    ],
  };
}

export function resolvePreviousComparableVisit(comparableHistory = [], content) {
  const currentDate = buildVisitDateTime(content);
  const sorted = [...comparableHistory].sort((left, right) => {
    const leftDate = new Date(left.visit_datetime || left.visit_date || 0).getTime();
    const rightDate = new Date(right.visit_datetime || right.visit_date || 0).getTime();
    return rightDate - leftDate;
  });
  if (!currentDate) return sorted[0] || null;
  return sorted.find((entry) => {
    const comparableDate = new Date(entry.visit_datetime || entry.visit_date || 0);
    return !Number.isNaN(comparableDate.getTime()) && comparableDate.getTime() < currentDate.getTime();
  }) || null;
}

export function buildVisitNoteComparisonState(content, comparableHistory = []) {
  const previousEntry = resolvePreviousComparableVisit(comparableHistory, content);
  const previousMeta = previousEntry
    ? {
      ...previousEntry,
      ...(previousEntry.content_snapshot || {}),
      visitDate: previousEntry.visit_date,
      visitType: previousEntry.form_type,
    }
    : null;
  const groups = getSnapshotMetricGroups(content, previousMeta);
  const allComparisons = [
    ...groups.pain,
    ...groups.vitals,
    ...groups.function,
    ...groups.nutrition,
    ...groups.systems,
    ...groups.fallsSafety,
  ];

  const sectionMap = allComparisons.reduce((accumulator, comparison) => {
    if (!accumulator[comparison.sectionId]) accumulator[comparison.sectionId] = [];
    accumulator[comparison.sectionId].push(comparison);
    return accumulator;
  }, {});

  const summaryItems = [
    ...groups.function,
    ...groups.nutrition,
    ...groups.pain,
    ...groups.systems,
    ...groups.fallsSafety,
  ]
    .filter((comparison) => comparison.showInSummary)
    .map((comparison) => ({
      key: comparison.key,
      sectionId: comparison.sectionId,
      label: comparison.label,
      text: comparison.changeText ? `${comparison.summaryLabel} | ${comparison.changeText}` : comparison.summaryLabel,
      statusLabel: comparison.statusLabel,
    }));

  return {
    previousEntry,
    groups,
    sectionMap,
    summaryItems,
  };
}

export function createEmptySupervisoryReview() {
  return {
    hha: {},
    lvn_lpn: {},
  };
}

export function hasStartedSupervisoryReview(form = {}) {
  return Object.entries(form || {}).some(([key, value]) => key !== "audit" && hasDocumentedValue(value));
}

function requiredError(sectionId, fieldLabel) {
  return { sectionId, message: `${fieldLabel} is required.` };
}

export function validateSupervisoryReview(content, supervisoryContext) {
  const errors = [];
  const review = content?.supervisory_review || {};
  const evaluateSubform = (form, config) => {
    if (!config?.applicable || !hasStartedSupervisoryReview(form)) return;
    if (!form.assigned_staff_user_id) errors.push(requiredError("rn-supervision", `${config.label} assigned staff`));
    if (!form.supervision_type) errors.push(requiredError("rn-supervision", `${config.label} supervision type`));
    if (!form.observation_datetime) errors.push(requiredError("rn-supervision", `${config.label} observation date/time`));
    if (!stringValue(form.rn_supervisor_name)) errors.push(requiredError("rn-supervision", `${config.label} RN supervisor`));
    config.questions.forEach((question) => {
      if (!stringValue(form[question.key])) {
        errors.push(requiredError("rn-supervision", `${config.label} ${question.label}`));
      }
      if (String(form[question.key]).toUpperCase() === "NO" && !stringValue(form.concern_details)) {
        errors.push(requiredError("rn-supervision", `${config.label} concern details`));
      }
    });
    if (String(form.patient_family_concerns).toUpperCase() === "YES" && !stringValue(form.concern_details)) {
      errors.push(requiredError("rn-supervision", `${config.label} concern details`));
    }
    if (String(form.corrective_action_required).toUpperCase() === "YES" && !stringValue(form.corrective_action_details)) {
      errors.push(requiredError("rn-supervision", `${config.label} corrective action details`));
    }
    if (String(form.notification_documented).toUpperCase() === "YES") {
      if (!stringValue(form.person_notified)) errors.push(requiredError("rn-supervision", `${config.label} person notified`));
      if (!stringValue(form.notification_datetime)) errors.push(requiredError("rn-supervision", `${config.label} notification date/time`));
    }
    if (String(form.follow_up_required).toUpperCase() === "YES" && !stringValue(form.follow_up_due_date)) {
      errors.push(requiredError("rn-supervision", `${config.label} follow-up due date`));
    }
  };

  evaluateSubform(review.hha, {
    label: "HHA",
    applicable: supervisoryContext?.hha?.applicable,
    questions: [
      { key: "services_meet_patient_needs", label: "services meet patient needs" },
      { key: "follows_care_plan", label: "follows current aide care plan" },
      { key: "demonstrates_competency", label: "demonstrates competency" },
      { key: "communication_appropriate", label: "communication with patient/family and care team" },
      { key: "infection_control_safety", label: "infection-control and safety practices" },
    ],
  });

  evaluateSubform(review.lvn_lpn, {
    label: "LVN/LPN",
    applicable: supervisoryContext?.lvn_lpn?.applicable,
    questions: [
      { key: "services_meet_patient_needs", label: "services meet patient needs" },
      { key: "follows_care_plan", label: "plan of care followed" },
      { key: "ordered_interventions_completed", label: "ordered interventions completed appropriately" },
      { key: "documentation_consistent", label: "documentation reviewed and consistent" },
      { key: "demonstrates_competency", label: "skills/tasks performed competently" },
      { key: "communication_appropriate", label: "communication with patient/family and care team" },
      { key: "infection_control_safety", label: "infection-control and safety practices" },
    ],
  });

  return errors;
}
