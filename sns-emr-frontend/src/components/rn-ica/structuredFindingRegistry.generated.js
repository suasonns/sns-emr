// AUTO-GENERATED MIRROR of backend app/services/evidence/structured_findings.py
// CONCEPT_REGISTRY. Regenerate this file whenever the backend registry changes --
// do NOT hand-edit concept entries here, they must stay byte-identical to the
// server-controlled source of truth so a concept behaves identically whether it
// was validated by the backend (note_draft_service.py / ai_extraction_service.py)
// or applied here on the frontend.
export const CONCEPT_REGISTRY = {
  PERF_NYHA_CLASS_I: {
    section: "performanceStatus",
    writes: [
      { path: "nyha", value: "I", op: "set", section: null },
    ],
  },
  PERF_NYHA_CLASS_II: {
    section: "performanceStatus",
    writes: [
      { path: "nyha", value: "II", op: "set", section: null },
    ],
  },
  PERF_NYHA_CLASS_III: {
    section: "performanceStatus",
    writes: [
      { path: "nyha", value: "III", op: "set", section: null },
    ],
  },
  PERF_NYHA_CLASS_IV: {
    section: "performanceStatus",
    writes: [
      { path: "nyha", value: "IV", op: "set", section: null },
    ],
  },
  CV_BP_ORTHOSTATIC: {
    section: "cardiovascular",
    writes: [
      { path: "bpSymptoms", value: "Orthostatic", op: "multi_add", section: null },
    ],
  },
  CV_BP_HYPERTENSIVE: {
    section: "cardiovascular",
    writes: [
      { path: "bpSymptoms", value: "Hypertensive", op: "multi_add", section: null },
    ],
  },
  CV_BP_HYPOTENSIVE: {
    section: "cardiovascular",
    writes: [
      { path: "bpSymptoms", value: "Hypotensive", op: "multi_add", section: null },
    ],
  },
  CV_BP_NORMAL: {
    section: "cardiovascular",
    writes: [
      { path: "bpSymptoms", value: "Normal", op: "multi_add", section: null },
    ],
  },
  CV_PULSE_SITE_APICAL: {
    section: "cardiovascular",
    writes: [
      { path: "pulseSites", value: "Apical", op: "multi_add", section: null },
    ],
  },
  CV_PULSE_SITE_PEDAL: {
    section: "cardiovascular",
    writes: [
      { path: "pulseSites", value: "Pedal", op: "multi_add", section: null },
    ],
  },
  CV_PULSE_SITE_RADIAL: {
    section: "cardiovascular",
    writes: [
      { path: "pulseSites", value: "Radial", op: "multi_add", section: null },
    ],
  },
  CV_PULSE_SITE_FEMORAL: {
    section: "cardiovascular",
    writes: [
      { path: "pulseSites", value: "Femoral", op: "multi_add", section: null },
    ],
  },
  CV_PULSE_QUALITY_REGULAR: {
    section: "cardiovascular",
    writes: [
      { path: "pulseQuality", value: "Regular", op: "set", section: null },
    ],
  },
  CV_PULSE_QUALITY_STRONG: {
    section: "cardiovascular",
    writes: [
      { path: "pulseQuality", value: "Strong", op: "set", section: null },
    ],
  },
  CV_PULSE_QUALITY_WEAK: {
    section: "cardiovascular",
    writes: [
      { path: "pulseQuality", value: "Weak", op: "set", section: null },
    ],
  },
  CV_PULSE_QUALITY_THREADY: {
    section: "cardiovascular",
    writes: [
      { path: "pulseQuality", value: "Thready", op: "set", section: null },
    ],
  },
  CV_PULSE_QUALITY_BOUNDING: {
    section: "cardiovascular",
    writes: [
      { path: "pulseQuality", value: "Bounding", op: "set", section: null },
    ],
  },
  CV_PULSE_QUALITY_IRREGULAR: {
    section: "cardiovascular",
    writes: [
      { path: "pulseQuality", value: "Irregular", op: "set", section: null },
    ],
  },
  CV_PULSE_QUALITY_TACHYCARDIA: {
    section: "cardiovascular",
    writes: [
      { path: "pulseQuality", value: "Tachycardia", op: "set", section: null },
    ],
  },
  CV_PULSE_QUALITY_BRADYCARDIA: {
    section: "cardiovascular",
    writes: [
      { path: "pulseQuality", value: "Bradycardia", op: "set", section: null },
    ],
  },
  CV_PULSE_QUALITY_ABSENT: {
    section: "cardiovascular",
    writes: [
      { path: "pulseQuality", value: "Absent", op: "set", section: null },
    ],
  },
  CV_EDEMA_PRESENT: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
    ],
  },
  CV_EDEMA_ABSENT: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "No", op: "set", section: null },
    ],
  },
  CV_EDEMA_LOC_BILATERAL_LE: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
      { path: "edema.location", value: "Bilateral lower extremities", op: "multi_add", section: null },
    ],
  },
  CV_EDEMA_LOC_UNILATERAL_LE: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
      { path: "edema.location", value: "Unilateral LE", op: "multi_add", section: null },
    ],
  },
  CV_EDEMA_LOC_SACRAL: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
      { path: "edema.location", value: "Sacral", op: "multi_add", section: null },
    ],
  },
  CV_EDEMA_LOC_PERIORBITAL: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
      { path: "edema.location", value: "Periorbital", op: "multi_add", section: null },
    ],
  },
  CV_EDEMA_LOC_UPPER_EXTREMITIES: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
      { path: "edema.location", value: "Upper extremities", op: "multi_add", section: null },
    ],
  },
  CV_EDEMA_LOC_GENERALIZED: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
      { path: "edema.location", value: "Generalized", op: "multi_add", section: null },
    ],
  },
  CV_EDEMA_SEVERITY_TRACE: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
      { path: "edema.severity", value: "Trace", op: "set", section: null },
    ],
  },
  CV_EDEMA_SEVERITY_1PLUS: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
      { path: "edema.severity", value: "1+", op: "set", section: null },
    ],
  },
  CV_EDEMA_SEVERITY_2PLUS: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
      { path: "edema.severity", value: "2+", op: "set", section: null },
    ],
  },
  CV_EDEMA_SEVERITY_3PLUS: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
      { path: "edema.severity", value: "3+", op: "set", section: null },
    ],
  },
  CV_EDEMA_SEVERITY_4PLUS: {
    section: "cardiovascular",
    writes: [
      { path: "edema.present", value: "Yes", op: "set", section: null },
      { path: "edema.severity", value: "4+", op: "set", section: null },
    ],
  },
  CV_CHEST_PAIN_PRESENT: {
    section: "cardiovascular",
    writes: [
      { path: "chestPain.present", value: "Yes", op: "set", section: null },
    ],
  },
  CV_CHEST_PAIN_ABSENT: {
    section: "cardiovascular",
    writes: [
      { path: "chestPain.present", value: "No", op: "set", section: null },
    ],
  },
  CV_JVD_PRESENT: {
    section: "cardiovascular",
    writes: [
      { path: "jvd", value: "Yes", op: "set", section: null },
    ],
  },
  CV_JVD_ABSENT: {
    section: "cardiovascular",
    writes: [
      { path: "jvd", value: "No", op: "set", section: null },
    ],
  },
  CV_PACEMAKER_PRESENT: {
    section: "cardiovascular",
    writes: [
      { path: "pacemaker", value: true, op: "set", section: null },
    ],
  },
  CV_ICD_PRESENT: {
    section: "cardiovascular",
    writes: [
      { path: "internalDefibrillator", value: true, op: "set", section: null },
    ],
  },
  CV_VARICOSE_VEINS_PRESENT: {
    section: "cardiovascular",
    writes: [
      { path: "varicoseVeins", value: true, op: "set", section: null },
    ],
  },
  CV_CENTRAL_LINE_PRESENT: {
    section: "cardiovascular",
    writes: [
      { path: "centralVenousLine", value: true, op: "set", section: null },
    ],
  },
  CV_COOL_EXTREMITIES_PRESENT: {
    section: "cardiovascular",
    writes: [
      { path: "coolExtremities", value: true, op: "set", section: null },
    ],
  },
  CV_COOL_EXTREMITIES_ABSENT: {
    section: "cardiovascular",
    writes: [
      { path: "coolExtremities", value: false, op: "set", section: null },
    ],
  },
  CV_STASIS_ULCER_PRESENT: {
    section: "cardiovascular",
    writes: [
      { path: "stasisUlcer", value: true, op: "set", section: null },
    ],
  },
  CV_STASIS_ULCER_ABSENT: {
    section: "cardiovascular",
    writes: [
      { path: "stasisUlcer", value: false, op: "set", section: null },
    ],
  },
  CV_HEART_FAILURE_PRESENT: {
    section: "cardiovascular",
    writes: [
      { path: "heartFailurePresent", value: true, op: "set", section: null },
    ],
  },
  CV_HEART_FAILURE_SYSTOLIC: {
    section: "cardiovascular",
    writes: [
      { path: "heartFailurePresent", value: true, op: "set", section: null },
      { path: "heartFailureType", value: "Systolic", op: "multi_add", section: null },
    ],
  },
  CV_HEART_FAILURE_DIASTOLIC: {
    section: "cardiovascular",
    writes: [
      { path: "heartFailurePresent", value: true, op: "set", section: null },
      { path: "heartFailureType", value: "Diastolic", op: "multi_add", section: null },
    ],
  },
  CV_HEART_FAILURE_UNSPECIFIED_TYPE: {
    section: "cardiovascular",
    writes: [
      { path: "heartFailurePresent", value: true, op: "set", section: null },
      { path: "heartFailureType", value: "Unspecified", op: "multi_add", section: null },
    ],
  },
  CV_HEART_FAILURE_ABSENT: {
    section: "cardiovascular",
    writes: [
      { path: "heartFailurePresent", value: false, op: "set", section: null },
    ],
  },
  RESP_SOB_NONE: {
    section: "respiratory",
    writes: [
      { path: "sobSeverity", value: "None", op: "set", section: null },
    ],
  },
  RESP_SOB_MILD: {
    section: "respiratory",
    writes: [
      { path: "sobSeverity", value: "Mild", op: "set", section: null },
    ],
  },
  RESP_SOB_MODERATE: {
    section: "respiratory",
    writes: [
      { path: "sobSeverity", value: "Moderate", op: "set", section: null },
    ],
  },
  RESP_SOB_SEVERE: {
    section: "respiratory",
    writes: [
      { path: "sobSeverity", value: "Severe", op: "set", section: null },
    ],
  },
  RESP_DYSPNEA_AT_REST: {
    section: "respiratory",
    writes: [
      { path: "sobSeverity", value: "At rest", op: "set", section: null },
      { path: "exertionLevel", value: "At rest", op: "set", section: null },
    ],
  },
  RESP_DYSPNEA_MINIMAL_EXERTION: {
    section: "respiratory",
    writes: [
      { path: "exertionLevel", value: "Minimal exertion", op: "set", section: null },
    ],
  },
  RESP_DYSPNEA_MODERATE_EXERTION: {
    section: "respiratory",
    writes: [
      { path: "exertionLevel", value: "Moderate exertion", op: "set", section: null },
    ],
  },
  RESP_DYSPNEA_SEVERE_EXERTION: {
    section: "respiratory",
    writes: [
      { path: "exertionLevel", value: "Severe exertion", op: "set", section: null },
    ],
  },
  RESP_DYSPNEA_WITH_SPEECH: {
    section: "respiratory",
    writes: [
      { path: "exertionLevel", value: "With speech", op: "set", section: null },
    ],
  },
  RESP_DYSPNEA_PURSED_LIP_BREATHING: {
    section: "respiratory",
    writes: [
      { path: "exertionLevel", value: "Pursed-lip breathing", op: "set", section: null },
    ],
  },
  RESP_COUGH_PRODUCTIVE: {
    section: "respiratory",
    writes: [
      { path: "coughType", value: "Productive", op: "set", section: null },
    ],
  },
  RESP_COUGH_NON_PRODUCTIVE: {
    section: "respiratory",
    writes: [
      { path: "coughType", value: "Non-productive", op: "set", section: null },
    ],
  },
  RESP_COUGH_HEMOPTYSIS: {
    section: "respiratory",
    writes: [
      { path: "coughType", value: "Hemoptysis", op: "set", section: null },
    ],
  },
  RESP_COUGH_NONE: {
    section: "respiratory",
    writes: [
      { path: "coughType", value: "None", op: "set", section: null },
    ],
  },
  RESP_LUNG_SOUNDS_CLEAR: {
    section: "respiratory",
    writes: [
      { path: "lungSounds", value: "Clear", op: "multi_add", section: null },
    ],
  },
  RESP_LUNG_SOUNDS_CRACKLES: {
    section: "respiratory",
    writes: [
      { path: "lungSounds", value: "Crackles", op: "multi_add", section: null },
    ],
  },
  RESP_LUNG_SOUNDS_WHEEZES: {
    section: "respiratory",
    writes: [
      { path: "lungSounds", value: "Wheezes", op: "multi_add", section: null },
    ],
  },
  RESP_LUNG_SOUNDS_RHONCHI: {
    section: "respiratory",
    writes: [
      { path: "lungSounds", value: "Rhonchi", op: "multi_add", section: null },
    ],
  },
  RESP_LUNG_SOUNDS_DIMINISHED: {
    section: "respiratory",
    writes: [
      { path: "lungSounds", value: "Diminished", op: "multi_add", section: null },
    ],
  },
  RESP_LUNG_SOUNDS_ABSENT: {
    section: "respiratory",
    writes: [
      { path: "lungSounds", value: "Absent", op: "multi_add", section: null },
    ],
  },
  RESP_LUNG_SOUNDS_STRIDOR: {
    section: "respiratory",
    writes: [
      { path: "lungSounds", value: "Stridor", op: "multi_add", section: null },
    ],
  },
  RESP_LUNG_SOUNDS_PLEURAL_RUB: {
    section: "respiratory",
    writes: [
      { path: "lungSounds", value: "Pleural rub", op: "multi_add", section: null },
    ],
  },
  RESP_LUNG_SOUNDS_RALES: {
    section: "respiratory",
    writes: [
      { path: "lungSounds", value: "Rales", op: "multi_add", section: null },
    ],
  },
  RESP_PATTERN_REGULAR: {
    section: "respiratory",
    writes: [
      { path: "respirations", value: "Regular", op: "multi_add", section: null },
    ],
  },
  RESP_PATTERN_IRREGULAR: {
    section: "respiratory",
    writes: [
      { path: "respirations", value: "Irregular", op: "multi_add", section: null },
    ],
  },
  RESP_PATTERN_LABORED: {
    section: "respiratory",
    writes: [
      { path: "respirations", value: "Labored", op: "multi_add", section: null },
    ],
  },
  RESP_PATTERN_CHEYNE_STOKES: {
    section: "respiratory",
    writes: [
      { path: "respirations", value: "Cheyne-Stokes", op: "multi_add", section: null },
    ],
  },
  RESP_PATTERN_APNEIC_EPISODES: {
    section: "respiratory",
    writes: [
      { path: "respirations", value: "Apneic episodes", op: "multi_add", section: null },
    ],
  },
  RESP_PATTERN_TACHYPNEA: {
    section: "respiratory",
    writes: [
      { path: "respirations", value: "Tachypnea", op: "multi_add", section: null },
    ],
  },
  RESP_PATTERN_BRADYPNEA: {
    section: "respiratory",
    writes: [
      { path: "respirations", value: "Bradypnea", op: "multi_add", section: null },
    ],
  },
  RESP_PATTERN_ORTHOPNEA: {
    section: "respiratory",
    writes: [
      { path: "respirations", value: "Orthopnea", op: "multi_add", section: null },
    ],
  },
  RESP_OXYGEN_NOT_IN_USE: {
    section: "respiratory",
    writes: [
      { path: "oxygenTherapy.inUse", value: false, op: "set", section: null },
      { path: "oxygenTherapy.onRoomAir", value: true, op: "set", section: null },
    ],
  },
  RESP_OXYGEN_NASAL_CANNULA: {
    section: "respiratory",
    writes: [
      { path: "oxygenTherapy.inUse", value: true, op: "set", section: null },
      { path: "oxygenTherapy.type", value: "Nasal cannula", op: "set", section: null },
    ],
    valueSlot: { kind: "numeric", path: "oxygenTherapy.litersPerMinute", minValue: 0, maxValue: 15, maxLen: null },
  },
  RESP_OXYGEN_SIMPLE_MASK: {
    section: "respiratory",
    writes: [
      { path: "oxygenTherapy.inUse", value: true, op: "set", section: null },
      { path: "oxygenTherapy.type", value: "Simple mask", op: "set", section: null },
    ],
    valueSlot: { kind: "numeric", path: "oxygenTherapy.litersPerMinute", minValue: 0, maxValue: 15, maxLen: null },
  },
  RESP_OXYGEN_NON_REBREATHER: {
    section: "respiratory",
    writes: [
      { path: "oxygenTherapy.inUse", value: true, op: "set", section: null },
      { path: "oxygenTherapy.type", value: "Non-rebreather", op: "set", section: null },
    ],
    valueSlot: { kind: "numeric", path: "oxygenTherapy.litersPerMinute", minValue: 0, maxValue: 15, maxLen: null },
  },
  RESP_OXYGEN_VENTURI_MASK: {
    section: "respiratory",
    writes: [
      { path: "oxygenTherapy.inUse", value: true, op: "set", section: null },
      { path: "oxygenTherapy.type", value: "Venturi mask", op: "set", section: null },
    ],
    valueSlot: { kind: "numeric", path: "oxygenTherapy.litersPerMinute", minValue: 0, maxValue: 15, maxLen: null },
  },
  RESP_OXYGEN_HIGH_FLOW: {
    section: "respiratory",
    writes: [
      { path: "oxygenTherapy.inUse", value: true, op: "set", section: null },
      { path: "oxygenTherapy.type", value: "High flow", op: "set", section: null },
    ],
    valueSlot: { kind: "numeric", path: "oxygenTherapy.litersPerMinute", minValue: 0, maxValue: 60, maxLen: null },
  },
  RESP_OXYGEN_CONTINUOUS: {
    section: "respiratory",
    writes: [
      { path: "oxygenTherapy.inUse", value: true, op: "set", section: null },
      { path: "oxygenTherapy.deliveryMode", value: "Continuous", op: "set", section: null },
    ],
  },
  RESP_OXYGEN_PRN: {
    section: "respiratory",
    writes: [
      { path: "oxygenTherapy.inUse", value: true, op: "set", section: null },
      { path: "oxygenTherapy.deliveryMode", value: "PRN", op: "set", section: null },
    ],
  },
  RESP_VENTILATOR_SHORT_TERM: {
    section: "respiratory",
    writes: [
      { path: "ventilator.shortTermVentilator", value: true, op: "set", section: null },
    ],
  },
  RESP_VENTILATOR_LONG_TERM: {
    section: "respiratory",
    writes: [
      { path: "ventilator.longTermVentilator", value: true, op: "set", section: null },
    ],
  },
  NEURO_HEMIPARESIS_RIGHT: {
    section: "neurological",
    writes: [
      { path: "motorDeficit", value: true, op: "set", section: null },
      { path: "affectedSide", value: "Right", op: "set", section: null },
      { path: "deficitType", value: "Hemiparesis", op: "multi_add", section: null },
      { path: "paralysis", value: "Right hemiparesis", op: "set", section: "musculoskeletal" },
    ],
  },
  NEURO_HEMIPARESIS_LEFT: {
    section: "neurological",
    writes: [
      { path: "motorDeficit", value: true, op: "set", section: null },
      { path: "affectedSide", value: "Left", op: "set", section: null },
      { path: "deficitType", value: "Hemiparesis", op: "multi_add", section: null },
      { path: "paralysis", value: "Left hemiparesis", op: "set", section: "musculoskeletal" },
    ],
  },
  NEURO_HEMIPLEGIA_RIGHT: {
    section: "neurological",
    writes: [
      { path: "motorDeficit", value: true, op: "set", section: null },
      { path: "affectedSide", value: "Right", op: "set", section: null },
      { path: "deficitType", value: "Hemiplegia", op: "multi_add", section: null },
      { path: "paralysis", value: "Right hemiplegia", op: "set", section: "musculoskeletal" },
    ],
  },
  NEURO_HEMIPLEGIA_LEFT: {
    section: "neurological",
    writes: [
      { path: "motorDeficit", value: true, op: "set", section: null },
      { path: "affectedSide", value: "Left", op: "set", section: null },
      { path: "deficitType", value: "Hemiplegia", op: "multi_add", section: null },
      { path: "paralysis", value: "Left hemiplegia", op: "set", section: "musculoskeletal" },
    ],
  },
  NEURO_PARAPLEGIA: {
    section: "neurological",
    writes: [
      { path: "motorDeficit", value: true, op: "set", section: null },
      { path: "affectedSide", value: "Bilateral", op: "set", section: null },
      { path: "deficitType", value: "Plegia", op: "multi_add", section: null },
      { path: "paralysis", value: "Paraplegia", op: "set", section: "musculoskeletal" },
    ],
  },
  NEURO_QUADRIPLEGIA: {
    section: "neurological",
    writes: [
      { path: "motorDeficit", value: true, op: "set", section: null },
      { path: "affectedSide", value: "Bilateral", op: "set", section: null },
      { path: "deficitType", value: "Plegia", op: "multi_add", section: null },
      { path: "paralysis", value: "Quadriplegia", op: "set", section: "musculoskeletal" },
    ],
  },
  NEURO_CONSCIOUSNESS_ALERT: {
    section: "neurological",
    writes: [
      { path: "consciousness", value: "Alert", op: "set", section: null },
    ],
  },
  NEURO_CONSCIOUSNESS_LETHARGIC: {
    section: "neurological",
    writes: [
      { path: "consciousness", value: "Lethargic", op: "set", section: null },
    ],
  },
  NEURO_CONSCIOUSNESS_OBTUNDED: {
    section: "neurological",
    writes: [
      { path: "consciousness", value: "Obtunded", op: "set", section: null },
    ],
  },
  NEURO_CONSCIOUSNESS_STUPOROUS: {
    section: "neurological",
    writes: [
      { path: "consciousness", value: "Stuporous", op: "set", section: null },
    ],
  },
  NEURO_CONSCIOUSNESS_COMATOSE: {
    section: "neurological",
    writes: [
      { path: "consciousness", value: "Comatose", op: "set", section: null },
    ],
  },
  NEURO_ORIENTED_TIME: {
    section: "neurological",
    writes: [
      { path: "orientation.time", value: true, op: "set", section: null },
    ],
  },
  NEURO_ORIENTED_PLACE: {
    section: "neurological",
    writes: [
      { path: "orientation.place", value: true, op: "set", section: null },
    ],
  },
  NEURO_ORIENTED_PERSON: {
    section: "neurological",
    writes: [
      { path: "orientation.person", value: true, op: "set", section: null },
    ],
  },
  NEURO_ORIENTED_SITUATION: {
    section: "neurological",
    writes: [
      { path: "orientation.situation", value: true, op: "set", section: null },
    ],
  },
  NEURO_DISORIENTED: {
    section: "neurological",
    writes: [
      { path: "orientation.disoriented", value: true, op: "set", section: null },
    ],
  },
  NEURO_COMMUNICATION_CLEAR: {
    section: "neurological",
    writes: [
      { path: "communication", value: "Clear", op: "set", section: null },
    ],
  },
  NEURO_COMMUNICATION_IMPAIRED: {
    section: "neurological",
    writes: [
      { path: "communication", value: "Impaired", op: "set", section: null },
    ],
  },
  NEURO_COMMUNICATION_UNABLE: {
    section: "neurological",
    writes: [
      { path: "communication", value: "Unable", op: "set", section: null },
    ],
  },
  NEURO_COMMUNICATION_APHASIA: {
    section: "neurological",
    writes: [
      { path: "communication", value: "Aphasia", op: "set", section: null },
    ],
  },
  NEURO_COMMUNICATION_SLURRED_SPEECH: {
    section: "neurological",
    writes: [
      { path: "communication", value: "Slurred speech", op: "set", section: null },
    ],
  },
  NEURO_HEARING_ADEQUATE: {
    section: "neurological",
    writes: [
      { path: "hearing", value: "Adequate", op: "set", section: null },
    ],
  },
  NEURO_HEARING_IMPAIRED: {
    section: "neurological",
    writes: [
      { path: "hearing", value: "Impaired", op: "set", section: null },
    ],
  },
  NEURO_HEARING_DEAF: {
    section: "neurological",
    writes: [
      { path: "hearing", value: "Deaf", op: "set", section: null },
    ],
  },
  NEURO_VISION_ADEQUATE: {
    section: "neurological",
    writes: [
      { path: "vision", value: "Adequate", op: "set", section: null },
    ],
  },
  NEURO_VISION_IMPAIRED: {
    section: "neurological",
    writes: [
      { path: "vision", value: "Impaired", op: "set", section: null },
    ],
  },
  NEURO_VISION_BLIND: {
    section: "neurological",
    writes: [
      { path: "vision", value: "Blind", op: "set", section: null },
    ],
  },
  NEURO_BALANCE_STEADY: {
    section: "neurological",
    writes: [
      { path: "balance", value: "Steady", op: "set", section: null },
    ],
  },
  NEURO_BALANCE_UNSTEADY: {
    section: "neurological",
    writes: [
      { path: "balance", value: "Unsteady", op: "set", section: null },
    ],
  },
  NEURO_BALANCE_UNABLE_TO_STAND: {
    section: "neurological",
    writes: [
      { path: "balance", value: "Unable to stand", op: "set", section: null },
    ],
  },
  NEURO_SENSORY_NUMBNESS: {
    section: "neurological",
    writes: [
      { path: "sensoryDeficits", value: "Numbness", op: "multi_add", section: null },
    ],
  },
  NEURO_SENSORY_TINGLING: {
    section: "neurological",
    writes: [
      { path: "sensoryDeficits", value: "Tingling", op: "multi_add", section: null },
    ],
  },
  NEURO_SENSORY_DECREASED_SENSATION: {
    section: "neurological",
    writes: [
      { path: "sensoryDeficits", value: "Decreased sensation", op: "multi_add", section: null },
    ],
  },
  NEURO_DELIRIUM_PRESENT: {
    section: "neurological",
    writes: [
      { path: "delirium", value: true, op: "set", section: null },
    ],
  },
  NEURO_SEIZURE_HISTORY: {
    section: "neurological",
    writes: [
      { path: "seizureHistory", value: true, op: "set", section: null },
    ],
  },
  NEURO_DEMEANOR_ANXIETY: {
    section: "neurological",
    writes: [
      { path: "symptomsDemeanor", value: "Anxiety", op: "multi_add", section: null },
    ],
  },
  NEURO_DEMEANOR_AGITATION: {
    section: "neurological",
    writes: [
      { path: "symptomsDemeanor", value: "Agitation", op: "multi_add", section: null },
    ],
  },
  NEURO_DEMEANOR_PEACEFUL: {
    section: "neurological",
    writes: [
      { path: "symptomsDemeanor", value: "Peaceful", op: "multi_add", section: null },
    ],
  },
  NEURO_DEMEANOR_CONFUSED: {
    section: "neurological",
    writes: [
      { path: "symptomsDemeanor", value: "Confused", op: "multi_add", section: null },
    ],
  },
  NEURO_DEMEANOR_RESTLESS: {
    section: "neurological",
    writes: [
      { path: "symptomsDemeanor", value: "Restless", op: "multi_add", section: null },
    ],
  },
  NEURO_DEMEANOR_DEPRESSED: {
    section: "neurological",
    writes: [
      { path: "symptomsDemeanor", value: "Depressed", op: "multi_add", section: null },
    ],
  },
  NEURO_DEMEANOR_COMBATIVE: {
    section: "neurological",
    writes: [
      { path: "symptomsDemeanor", value: "Combative", op: "multi_add", section: null },
    ],
  },
  INFECT_IMMUNOSUPPRESSED: {
    section: "infection",
    writes: [
      { path: "immunosuppressed", value: true, op: "set", section: null },
    ],
  },
  INFECT_ANTIBIOTIC_USE_CURRENT: {
    section: "infection",
    writes: [
      { path: "antibioticUse", value: true, op: "set", section: null },
    ],
  },
  INFECT_RECURRENT_INFECTION: {
    section: "infection",
    writes: [
      { path: "recurrentInfection", value: true, op: "set", section: null },
    ],
  },
  INFECT_PRECAUTIONS_CONTACT: {
    section: "infection",
    writes: [
      { path: "precautions", value: "Contact", op: "multi_add", section: null },
    ],
  },
  INFECT_PRECAUTIONS_DROPLET: {
    section: "infection",
    writes: [
      { path: "precautions", value: "Droplet", op: "multi_add", section: null },
    ],
  },
  INFECT_PRECAUTIONS_AIRBORNE: {
    section: "infection",
    writes: [
      { path: "precautions", value: "Airborne", op: "multi_add", section: null },
    ],
  },
  INFECT_CURRENT_SEPSIS: {
    section: "infection",
    writes: [
      { path: "currentInfections", value: "Sepsis", op: "multi_add", section: null },
    ],
  },
  INFECT_CURRENT_UTI: {
    section: "infection",
    writes: [
      { path: "currentInfections", value: "UTI", op: "multi_add", section: null },
    ],
  },
  INFECT_CURRENT_RESPIRATORY: {
    section: "infection",
    writes: [
      { path: "currentInfections", value: "Respiratory tract", op: "multi_add", section: null },
    ],
  },
  INFECT_CURRENT_WOUND_INFECTION: {
    section: "infection",
    writes: [
      { path: "currentInfections", value: "Wound", op: "multi_add", section: null },
    ],
  },
  INFECT_CURRENT_IV_SITE: {
    section: "infection",
    writes: [
      { path: "currentInfections", value: "IV site", op: "multi_add", section: null },
    ],
  },
  INFECT_CURRENT_PRESSURE_AREA: {
    section: "infection",
    writes: [
      { path: "currentInfections", value: "Pressure area", op: "multi_add", section: null },
    ],
  },
  INFECT_MRSA_CURRENT: {
    section: "infection",
    writes: [
      { path: "antibioticResistantInfection", value: "MRSA", op: "multi_add", section: null },
    ],
  },
  INFECT_C_DIFF_CURRENT: {
    section: "infection",
    writes: [
      { path: "antibioticResistantInfection", value: "C. difficile", op: "multi_add", section: null },
    ],
  },
  SKIN_WOUND_PRESENT: {
    section: "skin",
    writes: [
      { path: "skinConditionsPresent", value: true, op: "set", section: null },
      { path: "wounds", value: {}, op: "push_draft_row", section: null },
    ],
    valueSlot: { kind: "free_text_bounded", path: "wounds[].location", minValue: null, maxValue: null, maxLen: 60 },
  },
  SKIN_STATUS_DRY: {
    section: "skin",
    writes: [
      { path: "skinConditionsPresent", value: true, op: "set", section: null },
      { path: "skinStatus", value: "Dry", op: "multi_add", section: null },
    ],
  },
  SKIN_STATUS_FRAGILE: {
    section: "skin",
    writes: [
      { path: "skinConditionsPresent", value: true, op: "set", section: null },
      { path: "skinStatus", value: "Fragile", op: "multi_add", section: null },
    ],
  },
  SKIN_STATUS_EDEMATOUS: {
    section: "skin",
    writes: [
      { path: "skinConditionsPresent", value: true, op: "set", section: null },
      { path: "skinStatus", value: "Edematous", op: "multi_add", section: null },
    ],
  },
  SKIN_STATUS_BRUISING: {
    section: "skin",
    writes: [
      { path: "skinConditionsPresent", value: true, op: "set", section: null },
      { path: "skinStatus", value: "Bruising", op: "multi_add", section: null },
    ],
  },
  SKIN_STATUS_RASH: {
    section: "skin",
    writes: [
      { path: "skinConditionsPresent", value: true, op: "set", section: null },
      { path: "skinStatus", value: "Rash", op: "multi_add", section: null },
    ],
  },
  SKIN_STATUS_JAUNDICE: {
    section: "skin",
    writes: [
      { path: "skinConditionsPresent", value: true, op: "set", section: null },
      { path: "skinStatus", value: "Jaundice", op: "multi_add", section: null },
    ],
  },
  SKIN_STATUS_CYANOTIC: {
    section: "skin",
    writes: [
      { path: "skinConditionsPresent", value: true, op: "set", section: null },
      { path: "skinStatus", value: "Cyanotic", op: "multi_add", section: null },
    ],
  },
  SKIN_STATUS_MOTTLED: {
    section: "skin",
    writes: [
      { path: "skinConditionsPresent", value: true, op: "set", section: null },
      { path: "skinStatus", value: "Mottled", op: "multi_add", section: null },
    ],
  },
  SKIN_STATUS_INTACT: {
    section: "skin",
    writes: [
      { path: "skinStatus", value: "Intact", op: "multi_add", section: null },
    ],
  },
  SKIN_TURGOR_GOOD: {
    section: "skin",
    writes: [
      { path: "skinTurgor", value: "Good", op: "set", section: null },
    ],
  },
  SKIN_TURGOR_FAIR: {
    section: "skin",
    writes: [
      { path: "skinTurgor", value: "Fair", op: "set", section: null },
    ],
  },
  SKIN_TURGOR_POOR: {
    section: "skin",
    writes: [
      { path: "skinTurgor", value: "Poor", op: "set", section: null },
    ],
  },
  SKIN_TURGOR_TENTING: {
    section: "skin",
    writes: [
      { path: "skinTurgor", value: "Tenting", op: "set", section: null },
    ],
  },
  NUTR_APPETITE_GOOD: {
    section: "nutrition",
    writes: [
      { path: "appetite", value: "Good", op: "set", section: null },
    ],
  },
  NUTR_APPETITE_FAIR: {
    section: "nutrition",
    writes: [
      { path: "appetite", value: "Fair", op: "set", section: null },
    ],
  },
  NUTR_APPETITE_POOR: {
    section: "nutrition",
    writes: [
      { path: "appetite", value: "Poor", op: "set", section: null },
    ],
  },
  NUTR_APPETITE_ANOREXIC: {
    section: "nutrition",
    writes: [
      { path: "appetite", value: "Anorexic", op: "set", section: null },
    ],
  },
  NUTR_FLUID_INTAKE_ADEQUATE: {
    section: "nutrition",
    writes: [
      { path: "fluidIntake", value: "Adequate", op: "set", section: null },
    ],
  },
  NUTR_FLUID_INTAKE_DECREASED: {
    section: "nutrition",
    writes: [
      { path: "fluidIntake", value: "Decreased", op: "set", section: null },
    ],
  },
  NUTR_FLUID_INTAKE_MINIMAL: {
    section: "nutrition",
    writes: [
      { path: "fluidIntake", value: "Minimal", op: "set", section: null },
    ],
  },
  NUTR_DYSPHAGIA: {
    section: "nutrition",
    writes: [
      { path: "swallowingIssues", value: "Dysphagia", op: "multi_add", section: null },
    ],
  },
  NUTR_ASPIRATION_RISK: {
    section: "nutrition",
    writes: [
      { path: "swallowingIssues", value: "Aspiration risk", op: "multi_add", section: null },
    ],
  },
  NUTR_POCKETING: {
    section: "nutrition",
    writes: [
      { path: "swallowingIssues", value: "Pocketing", op: "multi_add", section: null },
    ],
  },
  NUTR_COUGHING_WITH_SWALLOWING: {
    section: "nutrition",
    writes: [
      { path: "swallowingIssues", value: "Coughing with swallowing", op: "multi_add", section: null },
    ],
  },
  NUTR_NPO: {
    section: "nutrition",
    writes: [
      { path: "npoStatus", value: "NPO", op: "set", section: null },
    ],
  },
  NUTR_NPO_EXCEPT_MEDS: {
    section: "nutrition",
    writes: [
      { path: "npoStatus", value: "NPO except meds", op: "set", section: null },
    ],
  },
  NUTR_MODIFIED_THICKENED_LIQUIDS: {
    section: "nutrition",
    writes: [
      { path: "npoStatus", value: "Modified/thickened liquids only", op: "set", section: null },
    ],
  },
  NUTR_ARTIFICIAL_FEEDING_PEG: {
    section: "nutrition",
    writes: [
      { path: "artificialFeeding", value: "PEG", op: "multi_add", section: null },
    ],
  },
  NUTR_ARTIFICIAL_FEEDING_NG: {
    section: "nutrition",
    writes: [
      { path: "artificialFeeding", value: "NG", op: "multi_add", section: null },
    ],
  },
  NUTR_ARTIFICIAL_FEEDING_TPN: {
    section: "nutrition",
    writes: [
      { path: "artificialFeeding", value: "TPN", op: "multi_add", section: null },
    ],
  },
  NUTR_ORAL_CAVITY_EDENTULOUS: {
    section: "nutrition",
    writes: [
      { path: "oralCavityFindings", value: "Edentulous", op: "multi_add", section: null },
    ],
  },
  NUTR_ORAL_CAVITY_STOMATITIS: {
    section: "nutrition",
    writes: [
      { path: "oralCavityFindings", value: "Stomatitis", op: "multi_add", section: null },
    ],
  },
  NUTR_ORAL_CAVITY_THRUSH: {
    section: "nutrition",
    writes: [
      { path: "oralCavityFindings", value: "Thrush", op: "multi_add", section: null },
    ],
  },
  MSK_WEAKNESS_MILD: {
    section: "musculoskeletal",
    writes: [
      { path: "weakness", value: "Mild", op: "set", section: null },
    ],
  },
  MSK_WEAKNESS_MODERATE: {
    section: "musculoskeletal",
    writes: [
      { path: "weakness", value: "Moderate", op: "set", section: null },
    ],
  },
  MSK_WEAKNESS_SEVERE: {
    section: "musculoskeletal",
    writes: [
      { path: "weakness", value: "Severe", op: "set", section: null },
    ],
  },
  MSK_RIGIDITY_PRESENT: {
    section: "musculoskeletal",
    writes: [
      { path: "rigidityPresent", value: true, op: "set", section: null },
    ],
  },
  MSK_RIGIDITY_SEVERITY_MILD: {
    section: "musculoskeletal",
    writes: [
      { path: "rigidityPresent", value: true, op: "set", section: null },
      { path: "rigidity", value: "Mild", op: "set", section: null },
    ],
  },
  MSK_RIGIDITY_SEVERITY_MODERATE: {
    section: "musculoskeletal",
    writes: [
      { path: "rigidityPresent", value: true, op: "set", section: null },
      { path: "rigidity", value: "Moderate", op: "set", section: null },
    ],
  },
  MSK_RIGIDITY_SEVERITY_SEVERE: {
    section: "musculoskeletal",
    writes: [
      { path: "rigidityPresent", value: true, op: "set", section: null },
      { path: "rigidity", value: "Severe", op: "set", section: null },
    ],
  },
  MSK_CONTRACTURES_PRESENT: {
    section: "musculoskeletal",
    writes: [
      { path: "contracturesPresent", value: true, op: "set", section: null },
    ],
  },
  MSK_CONTRACTURES_SEVERITY_MILD: {
    section: "musculoskeletal",
    writes: [
      { path: "contracturesPresent", value: true, op: "set", section: null },
      { path: "contractures", value: "Mild", op: "set", section: null },
    ],
  },
  MSK_CONTRACTURES_SEVERITY_MODERATE: {
    section: "musculoskeletal",
    writes: [
      { path: "contracturesPresent", value: true, op: "set", section: null },
      { path: "contractures", value: "Moderate", op: "set", section: null },
    ],
  },
  MSK_CONTRACTURES_SEVERITY_SEVERE: {
    section: "musculoskeletal",
    writes: [
      { path: "contracturesPresent", value: true, op: "set", section: null },
      { path: "contractures", value: "Severe", op: "set", section: null },
    ],
  },
  MSK_CONTRACTURES_LOC_BILATERAL_LE: {
    section: "musculoskeletal",
    writes: [
      { path: "contracturesLocation", value: "Bilateral lower extremities", op: "multi_add", section: null },
    ],
  },
  MSK_CONTRACTURES_LOC_UPPER_EXTREMITIES: {
    section: "musculoskeletal",
    writes: [
      { path: "contracturesLocation", value: "Upper extremities", op: "multi_add", section: null },
    ],
  },
  MSK_ROM_LOSS_UPPER_EXTREMITIES: {
    section: "musculoskeletal",
    writes: [
      { path: "romLimitations", value: "Upper extremities", op: "multi_add", section: null },
    ],
  },
  MSK_ROM_LOSS_LOWER_EXTREMITIES: {
    section: "musculoskeletal",
    writes: [
      { path: "romLimitations", value: "Lower extremities", op: "multi_add", section: null },
    ],
  },
  MSK_ISSUE_JOINT_SWELLING: {
    section: "musculoskeletal",
    writes: [
      { path: "musculoskeletalIssues", value: "Joint swelling", op: "multi_add", section: null },
    ],
  },
  MSK_ISSUE_SPASMS_CRAMPS: {
    section: "musculoskeletal",
    writes: [
      { path: "musculoskeletalIssues", value: "Spasms / cramps", op: "multi_add", section: null },
    ],
  },
  MSK_ISSUE_AMPUTATION: {
    section: "musculoskeletal",
    writes: [
      { path: "musculoskeletalIssues", value: "Amputation", op: "multi_add", section: null },
    ],
  },
  MSK_ISSUE_PROSTHESIS: {
    section: "musculoskeletal",
    writes: [
      { path: "musculoskeletalIssues", value: "Prosthesis", op: "multi_add", section: null },
    ],
  },
  MSK_PARAPLEGIA: {
    section: "musculoskeletal",
    writes: [
      { path: "paralysis", value: "Paraplegia", op: "set", section: null },
    ],
  },
  MSK_QUADRIPLEGIA: {
    section: "musculoskeletal",
    writes: [
      { path: "paralysis", value: "Quadriplegia", op: "set", section: null },
    ],
  },
  MSK_GAIT_NORMAL: {
    section: "musculoskeletal",
    writes: [
      { path: "gait", value: "Normal", op: "set", section: null },
    ],
  },
  MSK_GAIT_UNSTEADY: {
    section: "musculoskeletal",
    writes: [
      { path: "gait", value: "Unsteady", op: "set", section: null },
    ],
  },
  MSK_GAIT_SHUFFLING: {
    section: "musculoskeletal",
    writes: [
      { path: "gait", value: "Shuffling", op: "set", section: null },
    ],
  },
  MSK_GAIT_UNABLE: {
    section: "musculoskeletal",
    writes: [
      { path: "gait", value: "Unable", op: "set", section: null },
    ],
  },
  MSK_ASSISTIVE_DEVICE_WALKER: {
    section: "musculoskeletal",
    writes: [
      { path: "assistiveDevices", value: "Walker", op: "multi_add", section: null },
    ],
  },
  MSK_ASSISTIVE_DEVICE_WHEELCHAIR: {
    section: "musculoskeletal",
    writes: [
      { path: "assistiveDevices", value: "Wheelchair", op: "multi_add", section: null },
    ],
  },
  MSK_ASSISTIVE_DEVICE_CANE: {
    section: "musculoskeletal",
    writes: [
      { path: "assistiveDevices", value: "Cane", op: "multi_add", section: null },
    ],
  },
  MSK_ASSISTIVE_DEVICE_CRUTCHES: {
    section: "musculoskeletal",
    writes: [
      { path: "assistiveDevices", value: "Crutches", op: "multi_add", section: null },
    ],
  },
  MSK_ASSISTIVE_DEVICE_HOSPITAL_BED: {
    section: "musculoskeletal",
    writes: [
      { path: "assistiveDevices", value: "Hospital bed", op: "multi_add", section: null },
    ],
  },
  MSK_ASSISTIVE_DEVICE_HOYER_LIFT: {
    section: "musculoskeletal",
    writes: [
      { path: "assistiveDevices", value: "Hoyer lift", op: "multi_add", section: null },
    ],
  },
  MSK_AMBULATORY_INDEPENDENT: {
    section: "musculoskeletal",
    writes: [
      { path: "mobility.ambulatoryStatus", value: "Independent", op: "set", section: null },
    ],
  },
  MSK_AMBULATORY_SUPERVISED: {
    section: "musculoskeletal",
    writes: [
      { path: "mobility.ambulatoryStatus", value: "Supervised", op: "set", section: null },
    ],
  },
  MSK_AMBULATORY_ASSISTED: {
    section: "musculoskeletal",
    writes: [
      { path: "mobility.ambulatoryStatus", value: "Assisted", op: "set", section: null },
    ],
  },
  MSK_AMBULATORY_DEPENDENT: {
    section: "musculoskeletal",
    writes: [
      { path: "mobility.ambulatoryStatus", value: "Dependent", op: "set", section: null },
    ],
  },
  MSK_BEDBOUND: {
    section: "musculoskeletal",
    writes: [
      { path: "mobility.ambulatoryStatus", value: "Bedbound", op: "set", section: null },
    ],
  },
  MSK_TRANSFER_INDEPENDENT: {
    section: "musculoskeletal",
    writes: [
      { path: "mobility.transferAbility", value: "Independent", op: "set", section: null },
    ],
  },
  MSK_TRANSFER_1_PERSON_ASSIST: {
    section: "musculoskeletal",
    writes: [
      { path: "mobility.transferAbility", value: "1-person assist", op: "set", section: null },
    ],
  },
  MSK_TRANSFER_2_PERSON_ASSIST: {
    section: "musculoskeletal",
    writes: [
      { path: "mobility.transferAbility", value: "2-person assist", op: "set", section: null },
    ],
  },
  MSK_TRANSFER_HOYER_LIFT: {
    section: "musculoskeletal",
    writes: [
      { path: "mobility.transferAbility", value: "Hoyer lift", op: "set", section: null },
    ],
  },
  MSK_STRENGTH_DECREASED: {
    section: "musculoskeletal",
    writes: [
      { path: "strength", value: "Decreased", op: "set", section: null },
    ],
  },
  MSK_STRENGTH_ABSENT: {
    section: "musculoskeletal",
    writes: [
      { path: "strength", value: "Absent", op: "set", section: null },
    ],
  },
  MSK_BALANCE_IMPAIRED: {
    section: "musculoskeletal",
    writes: [
      { path: "balance", value: "Impaired", op: "set", section: null },
    ],
  },
  MSK_PAIN_WITH_MOVEMENT_MILD: {
    section: "musculoskeletal",
    writes: [
      { path: "painWithMovement", value: "Mild", op: "set", section: null },
    ],
  },
  MSK_PAIN_WITH_MOVEMENT_MODERATE: {
    section: "musculoskeletal",
    writes: [
      { path: "painWithMovement", value: "Moderate", op: "set", section: null },
    ],
  },
  MSK_PAIN_WITH_MOVEMENT_SEVERE: {
    section: "musculoskeletal",
    writes: [
      { path: "painWithMovement", value: "Severe", op: "set", section: null },
    ],
  },
};