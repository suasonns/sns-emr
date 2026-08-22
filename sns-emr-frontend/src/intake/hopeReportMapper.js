import { defaultPatient } from "./ConsentNotifications";

const PLACEHOLDER = "^";

const lookup = (map, value, fallbackCode = PLACEHOLDER, fallbackDescription = PLACEHOLDER) => {
  if (value === undefined || value === null || value === "") {
    return { code: fallbackCode, description: fallbackDescription };
  }
  const match = map[value];
  if (match) {
    return { code: match[0], description: match[1] };
  }
  return { code: PLACEHOLDER, description: String(value) };
};

const arrayText = (value) => Array.isArray(value) && value.length ? value.join(", ") : PLACEHOLDER;
const valueText = (value) => {
  if (Array.isArray(value)) return value.length ? value.join(", ") : PLACEHOLDER;
  if (value === undefined || value === null || value === "") return PLACEHOLDER;
  return String(value);
};

const formatDate = (value) => {
  if (!value) return PLACEHOLDER;
  const normalized = String(value).slice(0, 10);
  const parts = normalized.split("-");
  if (parts.length === 3) return `${parts[1]}/${parts[2]}/${parts[0]}`;
  return String(value);
};

const addDays = (value, days) => {
  if (!value) return "";
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return "";
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
};

const boolCode = (value, yesCode = "1", yesDescription = "Yes", noCode = "0", noDescription = "No") => ({
  code: value ? yesCode : noCode,
  description: value ? yesDescription : noDescription,
});

const SEX_MAP = {
  Male: ["1", "Male"],
  M: ["1", "Male"],
  Female: ["2", "Female"],
  F: ["2", "Female"],
};

// A0215 Site of Service at Admission — official CMS codes.
const SITE_OF_SERVICE_LABELS = {
  "01": "Patient's Home/Residence",
  "02": "Assisted Living Facility",
  "03": "Nursing Long Term Care (LTC) or Non-Skilled Nursing Facility (NF)",
  "04": "Skilled Nursing Facility (SNF)",
  "05": "Inpatient Hospital",
  "06": "Inpatient Hospice Facility (General Inpatient (GIP))",
  "07": "Long Term Care Hospital (LTCH)",
  "08": "Inpatient Psychiatric Facility",
  "09": "Hospice Home Care (Routine Home Care (RHC)) Provided in a Hospice Facility",
  "99": "Not listed",
};
// Legacy RNICA free-vocab values (pre-code-set fix) translated to the official code.
const LEGACY_SITE_OF_SERVICE_TO_CODE = {
  Home: "01", ALF: "02", "Board & Care": "02", "Memory Care": "02", SNF: "04", Hospital: "05", Homeless: "99", Other: "99",
};

// A1805 Admitted From — official CMS codes.
const ADMITTED_FROM_LABELS = {
  "01": "Home/Community",
  "02": "Nursing Home (long-term care facility)",
  "03": "Skilled Nursing Facility (SNF, swing beds)",
  "04": "Short-Term General Hospital (acute hospital, IPPS)",
  "05": "Long-Term Care Hospital (LTCH)",
  "06": "Inpatient Rehabilitation Facility (IRF)",
  "07": "Inpatient Psychiatric Facility",
  "08": "Intermediate Care Facility (ID/DD facility)",
  "10": "Hospice (institutional facility)",
  "11": "Critical Access Hospital (CAH)",
  "99": "Not Listed",
};
const LEGACY_ADMITTED_FROM_TO_CODE = {
  Home: "01", ALF: "01", Hospital: "04", SNF: "03", Rehab: "06", Other: "99",
};

// A1905 Living Arrangements — official CMS codes.
const LIVING_ARRANGEMENT_LABELS = {
  "1": "Alone (no other residents in the home)",
  "2": "With others in the home (e.g., family, friends, or paid caregiver)",
  "3": "Congregate home (e.g., assisted living or residential care home)",
  "4": "Inpatient facility (e.g., SNF, nursing home, inpatient hospice, hospital)",
  "5": "Does not have a permanent home",
};
const LEGACY_LIVING_ARRANGEMENT_TO_CODE = {
  Alone: "1", "With spouse": "2", "With family": "2", "With non-relative": "2", Facility: "4",
};

// Resolve a value to its official CMS code: pass through if it's already an
// official code, translate if it's a legacy pre-fix vocabulary value, else
// fall back to the placeholder (never guess at an unrecognized value).
function officialCodeLookup(value, labelMap, legacyMap) {
  if (value === undefined || value === null || value === "") {
    return { code: PLACEHOLDER, description: PLACEHOLDER };
  }
  if (labelMap[value]) {
    return { code: value, description: labelMap[value] };
  }
  const legacyCode = legacyMap[value];
  if (legacyCode) {
    return { code: legacyCode, description: labelMap[legacyCode] };
  }
  return { code: PLACEHOLDER, description: String(value) };
}

// I0010 Principal Diagnosis — official CMS category codes.
const PRINCIPAL_DIAGNOSIS_CATEGORY_LABELS = {
  "01": "Cancer",
  "02": "Dementia (including Alzheimer's disease)",
  "03": "Neurological Condition (e.g., Parkinson's disease, multiple sclerosis, ALS)",
  "04": "Stroke",
  "05": "Chronic Obstructive Pulmonary Disease (COPD)",
  "06": "Cardiovascular (excluding heart failure)",
  "07": "Heart Failure",
  "08": "Liver Disease",
  "09": "Renal Disease",
  "99": "None of the above",
};

// A1400 Payer Information — official CMS multi-select codes (check all that apply).
const PAYER_SOURCE_LABELS = {
  A: "Medicare (traditional fee-for-service)",
  B: "Medicare (managed care/Part C/Medicare Advantage)",
  C: "Medicaid (traditional fee-for-service)",
  D: "Medicaid (managed care)",
  G: "Other government (e.g., TRICARE, VA, etc.)",
  H: "Private Insurance/Medigap",
  I: "Private managed care",
  J: "Self-pay",
  K: "No payer source",
  X: "Unknown",
  Y: "Other",
};

// Facesheet Insurance card "Payer Source Type" category (single source of
// truth for payer information — see PatientFacesheet.jsx) crosswalked to its
// official CMS A1400 code. A1400 is a multi-select item, so both the primary
// and secondary Facesheet payer types (when present) each contribute a code.
const FACESHEET_PAYER_TYPE_TO_A1400_CODE = {
  MEDICARE: "A",
  MEDICARE_ADVANTAGE: "B",
  MEDICAID: "C",
  MEDICAID_MANAGED_CARE: "D",
  PRIVATE_MANAGED_CARE: "I",
  OTHER_GOVERNMENT: "G",
  SELF_PAY: "J",
  NO_PAYER_SOURCE: "K",
};

function payerSources(primaryPayerType, secondaryPayerType) {
  const codes = [primaryPayerType, secondaryPayerType]
    .map((type) => FACESHEET_PAYER_TYPE_TO_A1400_CODE[type])
    .filter((code) => Boolean(code) && PAYER_SOURCE_LABELS[code]);
  const uniqueCodes = [...new Set(codes)];
  if (!uniqueCodes.length) {
    return { incomplete: true, codes: [], text: "Legacy record: review required" };
  }
  return {
    incomplete: false,
    codes: uniqueCodes,
    text: uniqueCodes.map((code) => `${code} - ${PAYER_SOURCE_LABELS[code]}`).join("; "),
  };
}

const ASSISTANCE_MAP = {
  "24/7 available": ["1", "Assistance available around the clock"],
  "Daytime only": ["2", "Assistance available daytime only"],
  "Nighttime only": ["3", "Assistance available nighttime only"],
  Limited: ["4", "Limited assistance available"],
  None: ["5", "No assistance available"],
};

// HOPE J0900.A "Was the patient screened for pain?" (0 No / 1 Yes),
// J0900.C "The patient's pain severity was:" (0 None / 1 Mild / 2 Moderate /
// 3 Severe / 9 Pain not rated), and J0900.D "Type of standardized pain tool
// used:" (1 Numeric / 2 Verbal descriptor / 3 Patient visual / 4 Staff
// observation / 9 No standardized tool used). These are distinct from RN
// ICA's verbalizesPain (drives which pain scale tool to show — Numeric /
// PAINAD / FLACC), painIntensity.current (a raw numeric score), and
// assessmentTool (an auto-derived UI tool selection, not the clinician's
// explicit CMS-coded tool-type confirmation) — none of those legacy fields
// is an official CMS HOPE response on its own.
const PAIN_SCREENED_LABELS = {
  "0": "No",
  "1": "Yes",
};

const PAIN_SEVERITY_LABELS = {
  "0": "None",
  "1": "Mild",
  "2": "Moderate",
  "3": "Severe",
  "9": "Pain not rated",
};

const PAIN_TOOL_LABELS = {
  "1": "Numeric",
  "2": "Verbal descriptor",
  "3": "Patient visual",
  "4": "Staff observation",
  "9": "No standardized tool used",
};

function painScreeningResponse(screenedForPain, painSeverityCategory, standardizedPainToolType) {
  if (screenedForPain !== "0" && screenedForPain !== "1") {
    return {
      a: PLACEHOLDER,
      aDescription: "Legacy record: review required",
      c: PLACEHOLDER,
      cDescription: PLACEHOLDER,
      d: PLACEHOLDER,
      dDescription: PLACEHOLDER,
      incomplete: true,
    };
  }
  if (screenedForPain === "0") {
    return {
      a: "0",
      aDescription: PAIN_SCREENED_LABELS["0"],
      c: PLACEHOLDER,
      cDescription: "Skipped — not screened (J0905, Pain Active Problem)",
      d: PLACEHOLDER,
      dDescription: "Skipped — not screened (J0905, Pain Active Problem)",
      incomplete: false,
    };
  }
  const severityDescription = PAIN_SEVERITY_LABELS[painSeverityCategory];
  const toolDescription = PAIN_TOOL_LABELS[standardizedPainToolType];
  if (!severityDescription || !toolDescription) {
    return {
      a: "1",
      aDescription: PAIN_SCREENED_LABELS["1"],
      c: severityDescription ? painSeverityCategory : PLACEHOLDER,
      cDescription: severityDescription || "Legacy record: review required",
      d: toolDescription ? standardizedPainToolType : PLACEHOLDER,
      dDescription: toolDescription || "Legacy record: review required",
      incomplete: true,
    };
  }
  return {
    a: "1",
    aDescription: PAIN_SCREENED_LABELS["1"],
    c: painSeverityCategory,
    cDescription: severityDescription,
    d: standardizedPainToolType,
    dDescription: toolDescription,
    incomplete: false,
  };
}

// HOPE J0915 "Does the patient have neuropathic pain?" (0 No / 1 Yes) —
// distinct from the clinical "uncomfortable because of pain" question,
// which is not itself a CMS HOPE item. J0915 is tracked for legacy review
// independently of J0900 — one item missing must not flag the other as
// incomplete.
const NEUROPATHIC_PAIN_MAP = {
  "0": ["0", "No"],
  "1": ["1", "Yes"],
};

const YES_NO_UNABLE_MAP = {
  "0": ["0", "No"],
  "1": ["1", "Yes"],
  "9": ["9", "Unable to determine"],
};

const IMPACT_MAP = {
  "0": ["0", "Not at all"],
  "1": ["1", "Slight"],
  "2": ["2", "Moderate"],
  "3": ["3", "Severe"],
  "9": ["9", "Not applicable"],
};

const IMPACT_KEYS = [
  ["pain", "Pain"],
  ["shortnessOfBreath", "Shortness of Breath"],
  ["anxiety", "Anxiety"],
  ["nausea", "Nausea"],
  ["vomiting", "Vomiting"],
  ["diarrhea", "Diarrhea"],
  ["constipation", "Constipation"],
  ["agitation", "Agitation"],
];

// HOPE F2000/F2100/F2200/F3000 item A: "was the patient/responsible party asked?"
// CMS defines this as 0 No / 1 Yes-discussion occurred / 2 Yes-refused to discuss.
// This is a distinct question from the resulting clinical preference (code status,
// treatment preference, etc.) that RNICA also documents alongside it.
const ASKED_STATUS_LABELS = {
  "0": "No",
  "1": "Yes, and discussion occurred",
  "2": "Yes, but patient/responsible party refused to discuss",
};

function askedStatus(codedValue, legacyIndicator) {
  if (codedValue === "0" || codedValue === "1" || codedValue === "2") {
    return { code: codedValue, description: ASKED_STATUS_LABELS[codedValue], incomplete: false };
  }
  if (legacyIndicator) {
    return {
      code: PLACEHOLDER,
      description: "Legacy record: review required",
      incomplete: true,
      blockedFromSubmission: true,
    };
  }
  return { code: PLACEHOLDER, description: PLACEHOLDER, incomplete: true, blockedFromSubmission: true };
}

function splitPatientName(patient = {}) {
  const first = patient.firstName || "";
  const last = patient.lastName || "";
  const firstParts = String(first).trim().split(/\s+/).filter(Boolean);
  const middleInitial = patient.middleInitial || (firstParts.length > 1 ? firstParts[firstParts.length - 1].slice(0, 1) : "");
  const cleanFirst = firstParts.length > 1 ? firstParts.slice(0, -1).join(" ") : first;
  return {
    first: cleanFirst || PLACEHOLDER,
    middleInitial: middleInitial || PLACEHOLDER,
    last: last || PLACEHOLDER,
    display: `${last || PLACEHOLDER} ${cleanFirst || PLACEHOLDER} ${middleInitial || PLACEHOLDER}`.trim(),
  };
}

function derivePainFindings(pain = {}) {
  const findings = [];
  if (pain.assessmentTool) findings.push(`Tool: ${pain.assessmentTool}`);
  if (pain.painIntensity?.current) findings.push(`Current intensity ${pain.painIntensity.current}`);
  if (Array.isArray(pain.painLocation) && pain.painLocation.length) findings.push(`Location: ${pain.painLocation.join(", ")}`);
  if (Array.isArray(pain.painCharacter) && pain.painCharacter.length) findings.push(`Character: ${pain.painCharacter.join(", ")}`);
  if (pain.painManagementPlan) findings.push(`Plan: ${pain.painManagementPlan}`);
  return findings.length ? findings.join("; ") : PLACEHOLDER;
}

function deriveSkinTreatments(skin = {}) {
  const treatments = [];
  if (skin.woundImpairment) treatments.push(skin.woundImpairment);
  if (skin.notes) treatments.push(skin.notes);
  return treatments.length ? treatments.join(" | ") : PLACEHOLDER;
}

function diagnosisEntries(diagnoses = {}) {
  const entries = [];
  const collect = (item) => {
    if (!item) return;
    if (typeof item === "string" && item) {
      entries.push(item);
      return;
    }
    const code = valueText(item.icd10 || item.code);
    const description = valueText(item.description || item.name);
    if (code !== PLACEHOLDER || description !== PLACEHOLDER) {
      entries.push(`${code} ${description}`.trim());
    }
  };
  collect(diagnoses.primaryDiagnosis);
  (diagnoses.secondaryDiagnoses || []).forEach(collect);
  (diagnoses.comorbidities || []).forEach(collect);
  return entries;
}

function diagnosisList(diagnoses = {}) {
  const entries = diagnosisEntries(diagnoses);
  return entries.length ? entries.join(", ") : PLACEHOLDER;
}

function symptomEntries(source = {}) {
  return IMPACT_KEYS.map(([key, label], index) => {
    const mapped = lookup(IMPACT_MAP, source[key]);
    return {
      label: `${String.fromCharCode(65 + index)}. ${label}`,
      value: `${mapped.code} - ${mapped.description}`,
    };
  });
}

function isModerateOrSevere(value) {
  if (value === 2 || value === 3) return true;
  const text = String(value || "").trim().toLowerCase();
  return text === "2" || text === "3" || text.includes("moderate") || text.includes("severe");
}

export function getSfvStatus(formData = {}) {
  const symptomImpact = formData.symptomImpact || {};
  const sfv = formData.sfv || {};
  const screeningDate = sfv.symptomImpactScreeningDate || symptomImpact.assessmentDate || "";
  const triggeredSymptoms = IMPACT_KEYS
    .filter(([key]) => isModerateOrSevere(symptomImpact[key]))
    .map(([, label]) => label);
  const required = triggeredSymptoms.length > 0;
  const dueDate = required ? addDays(screeningDate, 2) : "";
  const completed = Boolean(sfv.inPersonSfvCompleted);
  const statusLabel = !required
    ? "No SFV trigger identified"
    : completed
      ? "SFV completed"
      : "SFV required";
  const note = !required
    ? "No J2051 item is currently Moderate or Severe."
    : completed
      ? "J2052A is complete; J2053 follow-up symptom impact may be documented by an RN or LPN/LVN."
      : `Any Moderate or Severe J2051 symptom requires an in-person SFV within 2 calendar days${screeningDate ? ` of ${formatDate(screeningDate)}` : ""}.`;
  return {
    required,
    completed,
    screeningDate,
    dueDate,
    triggeredSymptoms,
    statusLabel,
    note,
  };
}

function activeDiagnosisFlag(diagnoses = {}, matcher) {
  return diagnosisEntries(diagnoses).some((entry) => matcher.test(entry.toLowerCase()));
}

// HOPE Section I0100-I8005: Comorbidities and Co-existing Conditions.
// Mirrors the category list used in RNICA.jsx's HopeComorbiditiesCard so the
// generated HOPE report reflects the same structured checklist the clinician
// confirmed on the assessment, instead of re-deriving it from free text.
const HOPE_COMORBIDITY_ITEMS = [
  { key: "cancer", code: "I0100", label: "Cancer" },
  { key: "heartFailure", code: "I0600", label: "Heart Failure" },
  { key: "pvdPad", code: "I0900", label: "Peripheral Vascular Disease (PVD) / Peripheral Arterial Disease (PAD)" },
  { key: "cardiovascularExclHF", code: "I0950", label: "Cardiovascular (excluding heart failure)" },
  { key: "liverDisease", code: "I1101", label: "Liver disease" },
  { key: "renalDisease", code: "I1510", label: "Renal disease" },
  { key: "sepsis", code: "I2102", label: "Sepsis" },
  { key: "diabetesMellitus", code: "I2900", label: "Diabetes Mellitus (DM)" },
  { key: "neuropathy", code: "I2910", label: "Neuropathy" },
  { key: "stroke", code: "I4501", label: "Stroke" },
  { key: "dementia", code: "I4801", label: "Dementia (including Alzheimer's disease)" },
  { key: "neurologicalConditions", code: "I5150", label: "Neurological Conditions (e.g., Parkinson's, MS, ALS)" },
  { key: "seizureDisorder", code: "I5401", label: "Seizure Disorder" },
  { key: "copd", code: "I6202", label: "Chronic Obstructive Pulmonary Disease (COPD)" },
];

function hasStructuredHopeComorbidities(diagnoses = {}) {
  const hope = diagnoses.hopeComorbidities;
  if (!hope) return false;
  return HOPE_COMORBIDITY_ITEMS.some((item) => Boolean(hope[item.key])) || Boolean(hope.other);
}

export function mapRnIcaToHopeReport(formData = {}, patient = defaultPatient, agency = {}) {
  const demographics = formData.demographics || {};
  const livingSituation = demographics.livingSituation || {};
  const advancedCarePlanning = demographics.advancedCarePlanning || {};
  const diagnoses = formData.diagnoses || {};
  const pain = formData.pain || {};
  const respiratory = formData.respiratory || {};
  const symptomImpact = formData.symptomImpact || {};
  const sfv = formData.sfv || {};
  const skin = formData.skin || {};
  const spiritual = formData.spiritual || {};
  const medications = formData.medications || {};
  const finalization = formData.finalization || {};
  const imminentDeath = formData.imminentDeath || {};
  const name = splitPatientName(patient);
  const agencyInfo = {
    name: agency.name || agency.agencyName || "Hospice Agency",
    address: agency.address || "Agency Address",
    phone: agency.phone || "(000) 000-0000",
    fax: agency.fax || "(000) 000-0001",
    npi: agency.npi || PLACEHOLDER,
    ccn: agency.ccn || PLACEHOLDER,
    facilityId: agency.facilityId || PLACEHOLDER,
  };
  const siteOfService = officialCodeLookup(livingSituation.siteOfService, SITE_OF_SERVICE_LABELS, LEGACY_SITE_OF_SERVICE_TO_CODE);
  const admittedFrom = officialCodeLookup(livingSituation.admittedFrom, ADMITTED_FROM_LABELS, LEGACY_ADMITTED_FROM_TO_CODE);
  const livingArrangement = officialCodeLookup(livingSituation.livingArrangement, LIVING_ARRANGEMENT_LABELS, LEGACY_LIVING_ARRANGEMENT_TO_CODE);
  const assistance = lookup(ASSISTANCE_MAP, livingSituation.availabilityOfAssistance);
  const sex = lookup(SEX_MAP, demographics.gender || patient.sex);
  const cprAsked = askedStatus(advancedCarePlanning.cprPreferenceAskedStatus, advancedCarePlanning.codeStatus);
  const lifeSustainingAsked = askedStatus(advancedCarePlanning.lifeSustainingAskedStatus, advancedCarePlanning.lifeSustainingTreatmentPreference);
  const hospitalizationAsked = askedStatus(advancedCarePlanning.hospitalizationAskedStatus, advancedCarePlanning.hospitalizationPreference);
  const painScreening = painScreeningResponse(pain.screenedForPain, pain.painSeverityCategory, pain.standardizedPainToolType);
  const neuropathicPain = lookup(NEUROPATHIC_PAIN_MAP, pain.neuropathicPain);
  const neuropathicPainIncomplete = neuropathicPain.code === PLACEHOLDER;
  const imminent = lookup(YES_NO_UNABLE_MAP, imminentDeath.appearsThreeDaysOrLess);
  const principalDiagnosis = `${valueText(diagnoses.primaryDiagnosis?.icd10)} - ${valueText(diagnoses.primaryDiagnosis?.description)}`;
  const principalDiagnosisCategoryCode = diagnoses.primaryDiagnosis?.hopeDiagnosisCategory || "";
  const principalDiagnosisCategory = {
    code: principalDiagnosisCategoryCode || PLACEHOLDER,
    description: PRINCIPAL_DIAGNOSIS_CATEGORY_LABELS[principalDiagnosisCategoryCode] || PLACEHOLDER,
  };
  const f3000LegacyIndicator = spiritual.concernsDiscussed || Boolean((spiritual.spiritualConcerns || []).length) || Boolean(spiritual.notes);
  const spiritualAsked = askedStatus(spiritual.concernsAskedStatus, f3000LegacyIndicator);
  const payerInformation = payerSources(patient.primaryPayerType, patient.secondaryPayerType);
  const legacyReviewItems = [
    ["F2000", cprAsked],
    ["F2100", lifeSustainingAsked],
    ["F2200", hospitalizationAsked],
    ["F3000", spiritualAsked],
    ["A1400", payerInformation],
    ["J0900", painScreening],
    // J0915 is tracked independently of J0900 — one missing item must not
    // flag the other as incomplete, since they are separate CMS codes.
    ["J0915", { incomplete: neuropathicPainIncomplete }],
  ].filter(([, result]) => result.incomplete).map(([code]) => code);
  const legacyReviewRequired = {
    required: legacyReviewItems.length > 0,
    items: legacyReviewItems,
  };
  const sobIndicated = Boolean(respiratory.sobSeverity && respiratory.sobSeverity !== "None");
  const sfvStatus = getSfvStatus(formData);
  const opioidPresent = Boolean(medications.scheduledOpioid || medications.prnOpioid);
  const bowelRegimenCode = medications.bowelRegimen ? ["2", "Initiated / continued"] : opioidPresent ? ["0", "Not initiated / continued"] : ["1", "Not applicable - no opioid trigger"];
  const hasHeartFailure = activeDiagnosisFlag(diagnoses, /\b(chf|congestive heart failure|heart failure)\b/);
  const hasCopd = activeDiagnosisFlag(diagnoses, /\b(copd|chronic obstructive pulmonary disease)\b/);
  const hasOtherMedicalCondition = diagnosisEntries(diagnoses).length > (diagnoses.primaryDiagnosis?.description || diagnoses.primaryDiagnosis?.icd10 ? 1 : 0);
  const useStructuredComorbidities = hasStructuredHopeComorbidities(diagnoses);
  const structuredHope = diagnoses.hopeComorbidities || {};
  const comorbidityItems = useStructuredComorbidities
    ? HOPE_COMORBIDITY_ITEMS.map((item) => ({
        code: item.code,
        label: item.label,
        entries: [{ label: "Active diagnosis indicator", value: boolCode(Boolean(structuredHope[item.key])).description }],
      })).concat([
        { code: "I8005", label: "Other Medical Condition", entries: [{ label: "Active diagnosis indicator", value: boolCode(Boolean(structuredHope.other)).description }] },
      ])
    : [
        { code: "I0600", label: "Heart Failure", entries: [{ label: "Active diagnosis indicator", value: boolCode(hasHeartFailure).description }] },
        { code: "I6202", label: "Chronic Obstructive Pulmonary Disease (COPD)", entries: [{ label: "Active diagnosis indicator", value: boolCode(hasCopd).description }] },
        { code: "I8005", label: "Other Medical Condition", entries: [{ label: "Active diagnosis indicator", value: boolCode(hasOtherMedicalCondition).description }] },
      ];

  return {
    agency: agencyInfo,
    patientName: name.display,
    sfvStatus,
    legacyReviewRequired,
    sections: [
      {
        title: "Section A - Administrative Information",
        items: [
          { code: "A0050", label: "Type of Record", entries: [{ label: "Code + description", value: "1 - Add new record" }] },
          { code: "A0100", label: "Facility Provider Numbers", entries: [{ label: "A. NPI", value: agencyInfo.npi }, { label: "B. CCN", value: agencyInfo.ccn }, { label: "C. Facility ID", value: agencyInfo.facilityId }] },
          { code: "A0215", label: "Site of Service at Admission", entries: [{ label: "Code + description", value: `${siteOfService.code} - ${siteOfService.description}` }] },
          { code: "A0220", label: "Admission Date", entries: [{ label: "Date", value: formatDate(patient.socDate || formData.admissionsOrder?.levelOfCare?.effectiveDate || finalization.signatureDate) }] },
          { code: "A0250", label: "Reason for Record", entries: [{ label: "Code + description", value: "1 - Admission (ADM)" }] },
          { code: "A0500", label: "Legal Name of Patient", entries: [{ label: "A. First", value: name.first }, { label: "B. MI", value: name.middleInitial }, { label: "C. Last", value: name.last }] },
          { code: "A0550", label: "Patient Zip Code", entries: [{ label: "ZIP", value: valueText(demographics.address?.zip) }] },
          { code: "A0600", label: "Social Security and Medicare Numbers", entries: [{ label: "A. SSN", value: valueText(patient.ssn) }, { label: "B. Medicare / MBI", value: valueText(patient.medicareNumber) }] },
          { code: "A0700", label: "Medicaid Number", entries: [{ label: "Number", value: valueText(patient.medicaidNumber) }] },
          { code: "A0810", label: "Sex", entries: [{ label: "Code + description", value: `${sex.code} - ${sex.description}` }] },
          { code: "A0900", label: "Birth Date", entries: [{ label: "Date", value: formatDate(demographics.dob || patient.dob) }] },
          { code: "A1005", label: "Ethnicity", entries: [{ label: "Selection", value: arrayText(demographics.ethnicity) }] },
          { code: "A1010", label: "Race", entries: [{ label: "Selection", value: arrayText(demographics.race) }] },
          { code: "A1110", label: "Language", entries: [{ label: "A. Preferred language", value: valueText(demographics.preferredLanguage) }, { label: "B. Need interpreter", value: boolCode(Boolean(demographics.needsInterpreter)).description }] },
          { code: "A1400", label: "Payer Information", entries: [{ label: "Payer source(s)", value: payerInformation.text }] },
          { code: "A1805", label: "Admitted From", entries: [{ label: "Code + description", value: `${admittedFrom.code} - ${admittedFrom.description}` }] },
          { code: "A1905", label: "Living Arrangements", entries: [{ label: "Code + description", value: `${livingArrangement.code} - ${livingArrangement.description}` }] },
          { code: "A1910", label: "Availability of Assistance", entries: [{ label: "Code + description", value: `${assistance.code} - ${assistance.description}` }] },
        ],
      },
      {
        title: "Section F - Preferences",
        dataSourceNote: legacyReviewRequired.required
          ? `⚠ HOPE Legacy Review Required — this assessment predates HOPE discussion-status tracking. Review ${legacyReviewRequired.items.join(", ")} before submission.`
          : undefined,
        items: [
          { code: "F2000", label: "CPR Preference", entries: [{ label: "A. Was patient / rep asked?", value: `${cprAsked.code} - ${cprAsked.description}` }, { label: "B. Date first asked", value: formatDate(advancedCarePlanning.codeStatusDate) }] },
          { code: "F2100", label: "Life-sustaining treatments other than CPR", entries: [{ label: "A. Asked?", value: `${lifeSustainingAsked.code} - ${lifeSustainingAsked.description}` }, { label: "B. Date first asked", value: formatDate(advancedCarePlanning.lifeSustainingTreatmentPreferenceDate) }] },
          { code: "F2200", label: "Hospitalization preference", entries: [{ label: "A. Asked?", value: `${hospitalizationAsked.code} - ${hospitalizationAsked.description}` }, { label: "B. Date first asked", value: formatDate(advancedCarePlanning.hospitalizationPreferenceDate) }] },
          { code: "F3000", label: "Spiritual / Existential Concerns", entries: [{ label: "A. Asked?", value: `${spiritualAsked.code} - ${spiritualAsked.description}` }, { label: "B. Date first asked", value: formatDate(spiritual.concernsDiscussedDate) }] },
        ],
      },
      {
        title: "Section I - Active Diagnoses",
        dataSourceNote: useStructuredComorbidities
          ? "Comorbidities harvested from structured RNICA findings (H&P/labs/MD records scan + RN assessment)."
          : "⚠ This assessment predates structured HOPE harvesting from the RNICA — Heart Failure/COPD/Other Medical Condition below were inferred from the free-text diagnosis list only. Verify against the chart (H&P, labs, MD notes) before submission.",
        items: [
          { code: "I0010", label: "Principal Diagnosis", entries: [
            { label: "Category", value: `${principalDiagnosisCategory.code} - ${principalDiagnosisCategory.description}` },
            { label: "ICD-10 code + description (supporting detail)", value: principalDiagnosis },
          ] },
          ...comorbidityItems,
          { code: "I0000", label: "Comorbidities and Co-existing Conditions", entries: [{ label: "Active conditions", value: diagnosisList(diagnoses) }] },
        ],
      },
      {
        title: "Section J - Health Conditions",
        items: [
          { code: "J0050", label: "Death is Imminent", entries: [{ label: "Yes / No", value: `${imminent.code} - ${imminent.description}` }] },
          { code: "J0900", label: "Pain Screening", entries: [{ label: "A. Screened?", value: `${painScreening.a} - ${painScreening.aDescription}` }, { label: "B. Date", value: formatDate(pain.screeningDate) }, { label: "C. Severity", value: `${painScreening.c} - ${painScreening.cDescription}` }, { label: "D. Tool used", value: `${painScreening.d} - ${painScreening.dDescription}` }] },
          { code: "J0905", label: "Pain Active Problem", entries: [{ label: "Yes / No", value: boolCode(Boolean(pain.painIntensity?.current || pain.painManagementPlan || (pain.painLocation || []).length)).description }] },
          { code: "J0910", label: "Comprehensive Pain Assessment", entries: [{ label: "A. Done?", value: boolCode(Boolean(pain.comprehensiveAssessmentCompleted)).description }, { label: "B. Date", value: formatDate(pain.comprehensiveAssessmentDate) }, { label: "C. Findings included", value: derivePainFindings(pain) }] },
          { code: "J0915", label: "Neuropathic Pain", entries: [{ label: "Yes / No / blank", value: `${neuropathicPain.code} - ${neuropathicPain.description}` }] },
          { code: "J2030", label: "Screening for Shortness of Breath", entries: [{ label: "A. Screened?", value: boolCode(Boolean(respiratory.shortnessOfBreathScreened || respiratory.sobSeverity)).description }, { label: "B. Date", value: formatDate(respiratory.screeningDate) }, { label: "C. Indicated SOB?", value: boolCode(sobIndicated).description }] },
          { code: "J2040", label: "Treatment for Shortness of Breath", entries: [{ label: "A. Initiated?", value: boolCode(Boolean(respiratory.treatmentInitiated)).description }, { label: "B. Date", value: formatDate(respiratory.treatmentDate) }] },
          { code: "J2050", label: "Symptom Impact Screening", entries: [{ label: "A. Completed?", value: boolCode(Boolean(sfv.symptomImpactScreeningCompleted || symptomImpact.assessmentDate)).description }, { label: "B. Date", value: formatDate(sfv.symptomImpactScreeningDate || symptomImpact.assessmentDate) }] },
          { code: "J2051", label: "Symptom Impact", entries: symptomEntries(symptomImpact) },
          { code: "J2052", label: "Symptom Follow-up Visit (SFV)", entries: [{ label: "A. In-person SFV completed?", value: boolCode(Boolean(sfv.inPersonSfvCompleted)).description }, { label: "B. Date", value: formatDate(sfv.sfvDate) }, { label: "C. Reason not completed", value: valueText(sfv.reasonNotCompleted) }] },
          { code: "J2053", label: "SFV Symptom Impact", entries: symptomEntries(sfv.symptomImpactAtSfv || {}) },
        ],
      },
      {
        title: "Section M - Skin Conditions",
        items: [
          { code: "M1190", label: "Skin Conditions", entries: [{ label: "Yes / No", value: boolCode(Boolean(skin.skinConditionsPresent)).description }] },
          { code: "M1195", label: "Types of Skin Conditions", entries: [{ label: "Types", value: arrayText(skin.skinStatus) }] },
          { code: "M1200", label: "Skin Treatments", entries: [{ label: "Treatments", value: deriveSkinTreatments(skin) }] },
        ],
      },
      {
        title: "Section N - Medications",
        items: [
          { code: "N0500", label: "Scheduled Opioid", entries: [{ label: "A. Initiated / continued?", value: boolCode(Boolean(medications.scheduledOpioid)).description }, { label: "B. Date", value: formatDate(medications.scheduledOpioidDate) }] },
          { code: "N0510", label: "PRN Opioid", entries: [{ label: "A. Initiated / continued?", value: boolCode(Boolean(medications.prnOpioid)).description }, { label: "B. Date", value: formatDate(medications.prnOpioidDate) }] },
          { code: "N0520", label: "Bowel Regimen", entries: [{ label: "A. Status", value: `${bowelRegimenCode[0]} - ${bowelRegimenCode[1]}` }, { label: "B. Date", value: bowelRegimenCode[0] === "2" ? formatDate(medications.bowelRegimenDate) : PLACEHOLDER }] },
        ],
      },
      {
        title: "Z0500 - Signature of Person Verifying Record Completion",
        items: [
          { code: "Z0500", label: "Attestation", entries: [{ label: "Attestation", value: finalization.signatureCertification ? "I certify this HOPE report reflects the RN initial comprehensive assessment." : PLACEHOLDER }, { label: "Clinician Signature", value: valueText(finalization.clinicianSignature) }, { label: "Date", value: formatDate(finalization.signatureDate) }, { label: "Submission / Confirmation Number", value: valueText(finalization.hopeSubmissionNumber) }, { label: "Already submitted / no tracking", value: boolCode(Boolean(finalization.hopeAlreadySubmitted)).description }] },
        ],
      },
    ],
  };
}

// HOPE Admission harvest/completion-status (RN ICA Master Map SECTION 7).
// RN ICA's role for HOPE Admission is to harvest the assessment answers that
// feed the HOPE Admission report and show completion status / missing HOPE
// sources — it does NOT generate, export, or submit the HOPE Admission
// record itself (that is a separate downstream concern out of RN ICA scope).
//
// `sections` is the caller's per-section HOPE-code inventory (RNICA.jsx's
// SIDEBAR_CONFIG entries — { key, label, hope: [...] } — already curated to
// the clinically-relevant, assessment-driven HOPE codes, deliberately
// excluding purely administrative/agency-level report fields like A0050 or
// Z0500 that are not "things the clinician charts" and would never read as
// complete for a real assessment). This function reuses the exact same
// completeness signal mapRnIcaToHopeReport already computes per code (no
// value in an item's entries containing the PLACEHOLDER "^") so there is a
// single source of truth for "is this HOPE code answered."
export function getHopeAdmissionStatus(formData = {}, patient = defaultPatient, agency = {}, sections = []) {
  const report = mapRnIcaToHopeReport(formData, patient, agency);
  const itemsByCode = new Map();
  report.sections.forEach((section) => {
    section.items.forEach((item) => {
      if (!itemsByCode.has(item.code)) itemsByCode.set(item.code, item);
    });
  });

  const isCodeComplete = (code) => {
    const item = itemsByCode.get(code);
    if (!item) return true; // Not a code the mapper harvests — not a gap.
    return !(item.entries || []).some((entry) => String(entry.value ?? "").includes(PLACEHOLDER));
  };

  const hopeSections = (sections || []).filter((section) => Array.isArray(section.hope) && section.hope.length > 0);
  const evaluated = hopeSections.map((section) => {
    const missingCodes = section.hope.filter((code) => !isCodeComplete(code));
    return {
      key: section.key,
      label: section.label,
      codes: section.hope,
      complete: missingCodes.length === 0,
      missingCodes,
    };
  });

  const missingSections = evaluated.filter((section) => !section.complete);
  const totalSections = evaluated.length;
  const completedCount = totalSections - missingSections.length;

  return {
    totalSections,
    completedCount,
    missingCount: missingSections.length,
    percentComplete: totalSections ? Math.round((completedCount / totalSections) * 100) : 100,
    sections: evaluated,
    missingSections,
    allComplete: missingSections.length === 0,
  };
}

export default mapRnIcaToHopeReport;
