# =========================================================
# FILE: app/services/poc_compiler_rn_mapper.py
# PURPOSE: Convert RN ICA payload -> canonical POC compiler nodes
# STATUS: CLEAN PRODUCTION VERSION
# =========================================================

from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# =========================================================
# UTILITIES
# =========================================================

def _s(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _normalize_keyword(value: Any) -> str:
    if value is None:
        return ""

    normalized = str(value).strip().lower()

    for sep in [" ", "-", "/", "\\"]:
        normalized = normalized.replace(sep, "_")

    while "__" in normalized:
        normalized = normalized.replace("__", "_")

    return normalized.strip("_")

# =========================================================
# RULE KEYWORDS
# =========================================================

RULE_KEYWORDS: set[str] = {
    # disease / trajectory
    "chf",
    "cardiac_disease",
    "copd",
    "respiratory_failure",
    "cancer",
    "metastatic",
    "dementia",
    "cva",
    "neuro_degenerative",
    "esrd",
    "liver_failure",
    "infection",
    "general_decline",

    # symptom / support
    "pain",
    "dyspnea",
    "fatigue",
    "appetite_decline",
    "anxiety",
    "edema",
    "fall_risk",
    "caregiver_support",
    "wound_skin_integrity",
    "sleep_disturbance",
    "confusion_delirium",
    "nausea_vomiting",
    "depression",
    
    # clinical management
    "medication_management",
    "constipation",
    "spiritual_distress",
    "grief_bereavement",
    "seizure_disorder",
    "toxicity"
}

# =========================================================
# ALIAS MAP
# =========================================================

ALIAS_MAP: dict[str, list[str]] = {
    # cardiac - CHF stays separate because CHF is NYHA / heart-failure specific
    "congestive_heart_failure": ["chf"],
    "heart_failure": ["chf"],
    "congestive_cardiac_failure": ["chf"],
    "systolic_heart_failure": ["chf"],
    "diastolic_heart_failure": ["chf"],

    # cardiac disease - separate from CHF
    "cardiac_disease": ["cardiac_disease"],
    "advanced_cardiac_disease": ["cardiac_disease"],
    "end_stage_cardiac_disease": ["cardiac_disease"],

    "cad": ["cardiac_disease"],
    "coronary_artery_disease": ["cardiac_disease"],
    "coronary_disease": ["cardiac_disease"],
    "ischemic_heart_disease": ["cardiac_disease"],

    "mi": ["cardiac_disease"],
    "myocardial_infarction": ["cardiac_disease"],
    "history_of_myocardial_infarction": ["cardiac_disease"],
    "history_of_mi": ["cardiac_disease"],
    "prior_mi": ["cardiac_disease"],
    "old_mi": ["cardiac_disease"],

    "atherosclerosis_of_aorta": ["cardiac_disease"],
    "aortic_atherosclerosis": ["cardiac_disease"],
    "atherosclerosis": ["cardiac_disease"],

    "ischemic_cardiomyopathy": ["cardiac_disease"],
    "dilated_cardiomyopathy": ["cardiac_disease"],
    "cardiomyopathy": ["cardiac_disease"],

    "atrial_fibrillation": ["cardiac_disease"],
    "afib": ["cardiac_disease"],
    "a_fib": ["cardiac_disease"],

    "valvular_heart_disease": ["cardiac_disease"],
    "valvular_disease": ["cardiac_disease"],
    "aortic_stenosis": ["cardiac_disease"],
    "mitral_regurgitation": ["cardiac_disease"],

    "pulmonary_hypertension": ["cardiac_disease"],

    # cardiac symptoms that should also trigger symptom rules
    "angina": ["cardiac_disease", "pain"],
    "angina_pectoris": ["cardiac_disease", "pain"],
    "chest_pain": ["cardiac_disease", "pain"],
    "chest_discomfort": ["cardiac_disease", "pain"],
    "exertional_chest_pain": ["cardiac_disease", "pain"],

    "cardiac_related_pain": ["cardiac_disease", "pain"],
    "activity_intolerance_due_to_cardiac_disease": ["cardiac_disease", "fatigue"],
    "reduced_activity_tolerance": ["fatigue"],
    "activity_intolerance": ["fatigue"],
    "increased_need_for_assistance_with_adls": [
        "general_decline",
        "caregiver_support",
    ],
    "increased_assistance_with_adls": [
        "general_decline",
        "caregiver_support",
    ],
    "needs_more_help_with_adls": [
        "general_decline",
        "caregiver_support",
    ],
    "unable_to_perform_adls": [
        "general_decline",
        "caregiver_support",
    ],
    # mobility / safety indicators
    "walker": ["fall_risk"],
    "walker_use": ["fall_risk"],
    "uses_walker": ["fall_risk"],
    "difficulty_walking": ["fall_risk"],
    "difficulty_ambulating": ["fall_risk"],
    "reduced_mobility": ["fall_risk", "general_decline"],
    "walker_dependent": ["fall_risk"],
    "wheelchair_bound": ["fall_risk"],
    "uses_wheelchair": ["fall_risk"],
    "wheelchair_use": ["fall_risk"],
    "wheelchair_dependent": ["fall_risk"],
    "requires_assistance_with_ambulation": ["fall_risk"],
    "gait_instability": ["fall_risk"],

    # respiratory
    "sob": ["dyspnea"],
    "shortness_of_breath": ["dyspnea"],
    "short_of_breath": ["dyspnea"],
    "breathing_difficulty": ["dyspnea"],

    # intake / nutrition
    "poor_intake": ["appetite_decline"],
    "decreased_intake": ["appetite_decline"],
    "decreased_appetite": ["appetite_decline"],
    "loss_of_appetite": ["appetite_decline"],

    "minimal_intake": ["appetite_decline"],
    "poor_oral_intake": ["appetite_decline"],
    "reduced_intake": ["appetite_decline"],

    "anorexia": ["appetite_decline"],
    "cachexia": ["appetite_decline"],

    "food_refusal": ["appetite_decline"],
    "refusing_meals": ["appetite_decline"],

    "weight_loss": ["appetite_decline"],
    "unintentional_weight_loss": ["appetite_decline"],

    "early_satiety": ["appetite_decline"],

    "failure_to_thrive": ["appetite_decline"],

    # fatigue / weakness
    "weakness": ["fatigue"],
    "generalized_weakness": ["fatigue"],
    "tired": ["fatigue"],   
    "tiredness": ["fatigue"],
    "low_energy": ["fatigue"],
    "decreased_energy": ["fatigue"],
    "activity_intolerance": ["fatigue"],
    "excessive_sleeping": ["fatigue"],

    # anxiety
    "restlessness": ["anxiety"],
    "agitation": ["anxiety"],

    "worry": ["anxiety"],
    "fear": ["anxiety"],
    "panic": ["anxiety"],

    "emotional_distress": ["anxiety"],

    # sleep disturbance / anxiety overlap
    "sleep_disturbance": ["sleep_disturbance"],
    "poor_sleep": ["sleep_disturbance", "anxiety"],
    "insomnia": ["sleep_disturbance", "anxiety"],

    "anxious": ["anxiety"],
    "feeling_anxious": ["anxiety"],

    "anxiety_attack": ["anxiety"],
    "panic_attack": ["anxiety"],
    "panic_symptoms": ["anxiety"],

    "increased_anxiety": ["anxiety"],
    "worsening_anxiety": ["anxiety"],

    "fear_of_death": ["anxiety"],
    "fear_of_dying": ["anxiety"],

    "terminal_anxiety": ["anxiety"],
    "end_of_life_anxiety": ["anxiety"],

    "caregiver_reports_anxiety": ["anxiety"],
    "caregiver_reports_distress": ["anxiety"],

    "restless_at_night": ["sleep_disturbance", "anxiety", "fall_risk"],
    "unable_to_relax": ["anxiety"],

    "nighttime_restlessness": ["sleep_disturbance", "anxiety", "fall_risk"],
    "terminal_restlessness": ["sleep_disturbance", "anxiety", "fall_risk"],
    "nighttime_agitation": [
        "confusion_delirium",
        "sleep_disturbance",
        "anxiety",
        "fall_risk",
    ],
    "difficulty_sleeping": ["sleep_disturbance", "anxiety"],
    "unable_to_sleep": ["sleep_disturbance", "anxiety"],
    "difficulty_falling_asleep": ["sleep_disturbance", "anxiety"],
    "difficulty_staying_asleep": ["sleep_disturbance", "anxiety"],
    "nighttime_awakenings": ["sleep_disturbance", "fall_risk"],
    "sleeps_poorly": ["sleep_disturbance", "anxiety"],
    "frequent_waking": ["sleep_disturbance", "fall_risk"],
    
    # edema
    "swelling": ["edema"],
    "fluid_overload": ["edema"],

    # falls
    "fall": ["fall_risk"],
    "falls": ["fall_risk"],

    # caregiver
    "caregiver_distress": ["caregiver_support"],
    "caregiver_burden": ["caregiver_support"],
    
    "caregiver_stress": ["caregiver_support"],
    "caregiver_fatigue": ["caregiver_support"],
    "caregiver_burnout": ["caregiver_support"],
    "caregiver_overwhelmed": ["caregiver_support"],

    "overwhelmed": ["caregiver_support"],
    "burnout": ["caregiver_support"],

    "caregiver_education": ["caregiver_support"],
    "caregiver_support_needed": ["caregiver_support"],

    "unable_to_provide_care": ["caregiver_support"],
    "unable_to_care_for_patient": ["caregiver_support"],
    
    # wound / skin
    "wound": ["wound_skin_integrity"],
    "wounds": ["wound_skin_integrity"],
    "skin_breakdown": ["wound_skin_integrity"],
    "pressure_injury": ["wound_skin_integrity"],
    "pressure_ulcer": ["wound_skin_integrity"],
    "decubitus": ["wound_skin_integrity"],
    "open_area": ["wound_skin_integrity"],
    "skin_tear": ["wound_skin_integrity"],
    
    # medication management
    "medication": ["medication_management"],
    "medications": ["medication_management"],
    "med": ["medication_management"],
    "meds": ["medication_management"],

    "medication_change": ["medication_management"],
    "medication_changes": ["medication_management"],
    "medication_review": ["medication_management"],
    "medication_reconciliation": ["medication_management"],
    "medication_history": ["medication_management"],

    "weekly_medication_review": ["medication_management"],
    "monthly_medication_review": ["medication_management"],

    "medication_started": ["medication_management"],
    "medication_discontinued": ["medication_management"],
    "medication_stopped": ["medication_management"],

    "started_medication": ["medication_management"],
    "discontinued_medication": ["medication_management"],
    "stopped_medication": ["medication_management"],

    "new_medication": ["medication_management"],
    "new_med": ["medication_management"],

    "dose_change": ["medication_management"],
    "dose_changed": ["medication_management"],
    "frequency_change": ["medication_management"],

    "polypharmacy": ["medication_management"],

    "medication_error": ["medication_management"],
    "medication_safety": ["medication_management"],

    "adverse_reaction": ["medication_management"],
    "adverse_effect": ["medication_management"],

    "ineffective_medication": ["medication_management"],
    "medication_not_effective": ["medication_management"],

    "caregiver_medication_barrier": ["medication_management"],
    "controlled_substance": ["medication_management"],
    "comfort_kit": ["medication_management"],
    
    "constipation": ["constipation"],
    "constipated": ["constipation"],
    "no_bowel_movement": ["constipation"],
    "no_bm": ["constipation"],
    "bowel_regimen": ["constipation"],
    "hard_stool": ["constipation"],
    "straining": ["constipation"],
    "abdominal_distention": ["constipation"],
    
    # infection
    "fever": ["infection"],
    "chills": ["infection"],
    "infected": ["infection"],
    "infection": ["infection"],
    "suspected_infection": ["infection"],
    "wound_infection": ["infection"],
    "respiratory_infection": ["infection"],
    "urinary_infection": ["infection"],
    "uti": ["infection"],
    "pneumonia": ["infection"],
    
    # confusion / delirium
    "confusion": ["confusion_delirium"],
    "confused": ["confusion_delirium"],

    "new_confusion": ["confusion_delirium"],
    "increased_confusion": ["confusion_delirium"],
    "worsening_confusion": ["confusion_delirium"],
    "acute_confusion": ["confusion_delirium"],

    "disorientation": ["confusion_delirium"],
    "disoriented": ["confusion_delirium"],

    "altered_mental_status": ["confusion_delirium"],
    "mental_status_change": ["confusion_delirium"],
    "acute_mental_status_change": ["confusion_delirium"],

    "delirium": ["confusion_delirium"],
    "terminal_delirium": ["confusion_delirium"],
    "acute_delirium": ["confusion_delirium"],

    "sundowning": [
        "confusion_delirium",
        "sleep_disturbance",
        "anxiety",
        "fall_risk",
    ],

    "hallucinations": ["confusion_delirium"],
    "visual_hallucinations": ["confusion_delirium"],
    "auditory_hallucinations": ["confusion_delirium"],

    "not_oriented": ["confusion_delirium"],
    "oriented_x1": ["confusion_delirium"],
    "oriented_x2": ["confusion_delirium"],

    "memory_loss": ["confusion_delirium"],
    "forgetfulness": ["confusion_delirium"],
    "forgetful": ["confusion_delirium"],

    "cognitive_decline": ["confusion_delirium"],

    "impaired_judgment": ["confusion_delirium"],

    "wandering": [
        "confusion_delirium",
        "fall_risk",
    ],

    "poor_safety_awareness": [
        "confusion_delirium",
        "fall_risk",
    ],

    "decreased_safety_awareness": [
        "confusion_delirium",
        "fall_risk",
    ],

    "impulsive_behavior": [
        "confusion_delirium",
        "fall_risk",
    ],

    "unable_to_follow_commands": [
        "confusion_delirium",
    ],

    "unable_to_follow_instructions": [
        "confusion_delirium",
    ],
    
    # nausea / vomiting
    "nausea": ["nausea_vomiting"],
    "nauseated": ["nausea_vomiting"],
    "vomiting": ["nausea_vomiting"],
    "vomit": ["nausea_vomiting"],
    "emesis": ["nausea_vomiting"],

    "nausea_vomiting": ["nausea_vomiting"],
    "nausea_and_vomiting": ["nausea_vomiting"],

    "persistent_nausea": ["nausea_vomiting"],
    "persistent_vomiting": ["nausea_vomiting"],
    "uncontrolled_nausea": ["nausea_vomiting"],
    "uncontrolled_vomiting": ["nausea_vomiting"],

    "cannot_keep_food_down": [
        "nausea_vomiting",
        "appetite_decline",
    ],

    "unable_to_tolerate_oral_intake": [
        "nausea_vomiting",
        "appetite_decline",
    ],

    "poor_intake_due_to_nausea": [
        "nausea_vomiting",
        "appetite_decline",
    ],

    "antiemetic": [
        "nausea_vomiting",
        "medication_management",
    ],

    "zofran": [
        "nausea_vomiting",
        "medication_management",
    ],

    "ondansetron": [
        "nausea_vomiting",
        "medication_management",
    ],

    "compazine": [
        "nausea_vomiting",
        "medication_management",
    ],

    "prochlorperazine": [
        "nausea_vomiting",
        "medication_management",
    ],
    # depression
    "depression": ["depression"],
    "depressed": ["depression"],

    "depressive_symptoms": ["depression"],
    "depressed_mood": ["depression"],

    "sadness": ["depression"],
    "persistent_sadness": ["depression"],

    "tearful": ["depression"],
    "tearfulness": ["depression"],

    "hopelessness": ["depression"],
    "feelings_of_hopelessness": ["depression"],

    "withdrawn": ["depression"],
    "social_withdrawal": ["depression"],

    "loss_of_interest": ["depression"],
    "loss_of_pleasure": ["depression"],

    "anhedonia": ["depression"],

    "feeling_down": ["depression"],
    "low_mood": ["depression"],

    "decreased_motivation": ["depression"],

    "decreased_engagement": ["depression"],

    "grief_related_depression": [
        "depression",
        "caregiver_support",
    ],

    "caregiver_reports_depression": [
        "depression",
        "caregiver_support",
    ],

    "refusing_activities": [
        "depression",
    ],
    
    # spiritual distress
    "spiritual_distress": ["spiritual_distress"],

    "spiritual_pain": ["spiritual_distress"],
    "spiritual_suffering": ["spiritual_distress"],

    "existential_distress": ["spiritual_distress"],
    "existential_concerns": ["spiritual_distress"],
    "existential_crisis": ["spiritual_distress"],

    "spiritual_concerns": ["spiritual_distress"],
    "unresolved_spiritual_concerns": ["spiritual_distress"],

    "loss_of_meaning": ["spiritual_distress"],
    "loss_of_purpose": ["spiritual_distress"],

    "questioning_faith": ["spiritual_distress"],
    "spiritual_conflict": ["spiritual_distress"],
    "loss_of_faith": ["spiritual_distress"],

    "fear_of_afterlife": [
        "spiritual_distress",
        "anxiety",
    ],

    "hopelessness_related_to_spiritual_concerns": [
        "spiritual_distress",
        "depression",
    ],

    "desire_for_chaplain": ["spiritual_distress"],
    "requests_chaplain": ["spiritual_distress"],
    "chaplain_support": ["spiritual_distress"],
    "requests_chaplain_support": ["spiritual_distress"],
    "requests_spiritual_support": ["spiritual_distress"],
    
    "grief": ["grief_bereavement"],
    "grieving": ["grief_bereavement"],
    "bereavement": ["grief_bereavement"],

    "anticipatory_grief": ["grief_bereavement"],

    "complicated_grief": ["grief_bereavement"],

    "family_grief": ["grief_bereavement"],

    "caregiver_grief": [
        "grief_bereavement",
        "caregiver_support",
    ],

    "loss_related_distress": ["grief_bereavement"],

    "difficulty_coping_with_loss": [
        "grief_bereavement",
    ],

    "family_coping_concern": [
        "grief_bereavement",
        "caregiver_support",
    ],

    "bereavement_support_needed": [
        "grief_bereavement",
    ],

    "caregiver_reports_grief": [
        "grief_bereavement",
        "caregiver_support",
    ],
    
    # seizure disorder

    "seizure": ["seizure_disorder"],
    "seizures": ["seizure_disorder"],

    "seizure_activity": ["seizure_disorder"],

    "convulsion": ["seizure_disorder"],
    "convulsions": ["seizure_disorder"],

    "tonic_clonic_seizure": ["seizure_disorder"],
    "grand_mal_seizure": ["seizure_disorder"],

    "focal_seizure": ["seizure_disorder"],

    "absence_seizure": ["seizure_disorder"],

    "postictal_state": ["seizure_disorder"],

    "postictal_confusion": [
        "seizure_disorder",
        "confusion_delirium",
    ],

    "breakthrough_seizure": ["seizure_disorder"],

    "uncontrolled_seizures": ["seizure_disorder"],

    "new_onset_seizure": ["seizure_disorder"],

    "antiepileptic_medication": [
        "seizure_disorder",
        "medication_management",
    ],

    "keppra": [
        "seizure_disorder",
        "medication_management",
    ],

    "levetiracetam": [
        "seizure_disorder",
        "medication_management",
    ],

    "dilantin": [
        "seizure_disorder",
        "medication_management",
    ],

    "phenytoin": [
        "seizure_disorder",
        "medication_management",
    ],
    
    "valproic_acid": [
        "seizure_disorder",
        "medication_management",
    ],

    "depakote": [
        "seizure_disorder",
        "medication_management",
    ],

    "carbamazepine": [
        "seizure_disorder",
        "medication_management",
    ],

    "tegretol": [
        "seizure_disorder",
        "medication_management",
    ],

    "phenobarbital": [
        "seizure_disorder",
        "medication_management",
    ],
    # toxicity
    "toxicity": ["toxicity"],

    "medication_toxicity": [
        "toxicity",
        "medication_management",
    ],

    "drug_toxicity": [
        "toxicity",
        "medication_management",
    ],

    "oversedation": ["toxicity"],

    "excessive_somnolence": ["toxicity"],

    "respiratory_depression": [
        "toxicity",
        "dyspnea",
    ],

    "polypharmacy_effects": [
        "toxicity",
        "medication_management",
    ],

    "adverse_drug_reaction": [
        "toxicity",
        "medication_management",
    ],

    # phenytoin toxicity

    "phenytoin_toxicity": [
        "toxicity",
        "seizure_disorder",
        "medication_management",
    ],
    
    "elevated_phenytoin_level": [
        "toxicity",
        "seizure_disorder",
        "medication_management",
    ],

    "high_phenytoin_level": [
        "toxicity",
        "seizure_disorder",
        "medication_management",
    ],

    "critical_phenytoin_level": [
        "toxicity",
        "seizure_disorder",
        "medication_management",
    ],

    "elevated_dilantin_level": [
        "toxicity",
        "seizure_disorder",
        "medication_management",
    ],

    "dilantin_toxicity": [
        "toxicity",
        "seizure_disorder",
        "medication_management",
    ],

    "nystagmus": [
        "toxicity",
        "seizure_disorder",
    ],

    "ataxia": [
        "toxicity",
        "fall_risk",
    ],

    "slurred_speech": [
        "toxicity",
    ],

    "unsteady_gait": [
        "toxicity",
        "fall_risk",
    ],

    "somnolence": [
        "toxicity",
    ],

    "difficulty_arousing": [
        "toxicity",
    ],

    "decreased_responsiveness": [
        "toxicity",
    ],
    }


# =========================================================
# ALIAS RESOLUTION
# =========================================================

def _resolve_keyword_aliases(raw_keyword: Any) -> list[str]:
    kw = _normalize_keyword(raw_keyword)
    if not kw:
        return []

    if kw in ALIAS_MAP:
        return ALIAS_MAP[kw]

    if kw in RULE_KEYWORDS:
        return [kw]

    return []


# =========================================================
# FREE TEXT EXTRACTION (NOISE-SAFE)
# =========================================================

def _extract_keywords_from_text(raw_text: Any) -> list[str]:
    if not isinstance(raw_text, str):
        return []

    text_value = raw_text.lower()

    # phrase-first matching so multi-word concepts stay intact
    phrase_candidates = [
        # CHF - keep separate from general cardiac disease
        "congestive heart failure",
        "congestive cardiac failure",
        "heart failure",
        "systolic heart failure",
        "diastolic heart failure",

        # cardiac disease - non-CHF cardiac pathway
        "cardiac disease",
        "advanced cardiac disease",
        "end stage cardiac disease",
        "end-stage cardiac disease",

        "coronary artery disease",
        "coronary disease",
        "ischemic heart disease",
        "cad",

        "myocardial infarction",
        "history of myocardial infarction",
        "history of mi",
        "prior mi",
        "old mi",
        "mi",

        "atherosclerosis of aorta",
        "aortic atherosclerosis",
        "atherosclerosis",

        "ischemic cardiomyopathy",
        "dilated cardiomyopathy",
        "cardiomyopathy",

        "atrial fibrillation",
        "afib",
        "a fib",

        "valvular heart disease",
        "valvular disease",
        "aortic stenosis",
        "mitral regurgitation",

        "pulmonary hypertension",

        # cardiac symptoms
        "angina",
        "angina pectoris",
        "chest pain",
        "chest discomfort",
        "exertional chest pain",
        "cardiac related pain",
        "activity intolerance due to cardiac disease",

        # mobility / safety terms
        "walker use",
        "uses walker",
        "walker dependent",
        "wheelchair bound",
        "wheelchair use",
        "wheelchair dependent",
        "uses wheelchair",
        "difficulty walking",
        "difficulty ambulating",
        "requires assistance with ambulation",
        "gait instability",
        "reduced mobility",

        "reduced activity tolerance",
        "increased need for assistance with adls",
        "increased assistance with adls",
        "needs more help with adls",
        "unable to perform adls",

        "shortness of breath",
        "short of breath",
        "breathing difficulty",
        "poor intake",
        "decreased intake",
        "decreased appetite",
        "loss of appetite",
        "generalized weakness",
        "fluid overload",
        "skin breakdown",
        "pressure injury",
        "pressure ulcer",
        "open area",
        "skin tear",
        
        "caregiver distress",
        "caregiver burden",
        "caregiver stress",
        "caregiver fatigue",
        "caregiver burnout",
        "caregiver overwhelmed",

        "needs caregiver education",
        "unable to provide care",
        "unable to care for patient",
        
        "medication review",
        "medication reconciliation",
        "medication history",
        "weekly medication review",
        "monthly medication review",

        "medication started",
        "medication discontinued",
        "medication stopped",
        "started medication",
        "discontinued medication",
        "stopped medication",

        "new medication",
        "new med",
        "dose change",
        "dose changed",
        "frequency change",

        "adverse reaction",
        "adverse effect",
        "medication error",
        "medication safety",
        "controlled substance",
        "comfort kit",
        "ineffective medication",
        "medication not effective",
        
        "constipation",
        "no bowel movement",
        "bowel regimen",
        "hard stool",
        "abdominal distention",
        
        # anxiety
        "emotional distress",
        "sleep disturbance",

        "panic symptoms",
        "panic attack",

        "worsening anxiety",
        "increased anxiety",

        "feeling anxious",
        "anxiety attack",

        "fear of death",
        "fear of dying",

        "terminal anxiety",
        "end of life anxiety",

        "caregiver reports anxiety",
        "caregiver reports distress",

        "restless at night",
        "unable to relax",

        "terminal restlessness",
        "nighttime restlessness",
        "nighttime agitation",

        "sleep disturbance",
        "poor sleep",
        "difficulty sleeping",
        "unable to sleep",
        "difficulty falling asleep",
        "difficulty staying asleep",
        "nighttime awakenings",
        "insomnia",
        "sleeps poorly",
        "frequent waking",
        
        # appetite decline
        "poor intake",
        "decreased intake",

        "decreased appetite",
        "loss of appetite",

        "minimal intake",
        "poor oral intake",
        "reduced intake",

        "food refusal",
        "refusing meals",

        "weight loss",
        "unintentional weight loss",

        "early satiety",

        "failure to thrive",
        
        "low energy",
        "decreased energy",
        "activity intolerance",
        "excessive sleeping",
        "increased sleeping",
        
        "suspected infection",
        "wound infection",
        "respiratory infection",
        "urinary infection",
        "increased weakness",
        "mental status change",
        "new confusion",
        
        # confusion / delirium
        "acute delirium",
        "mental status change",
        "altered mental status",

        "new confusion",
        "increased confusion",
        "worsening confusion",
        "acute confusion",

        "confusion",
        "confused",

        "delirium",
        "terminal delirium",
        "acute delirium",

        "disorientation",
        "disoriented",

        "memory loss",
        "forgetfulness",
        "forgetful",

        "cognitive decline",

        "impaired judgment",

        "poor safety awareness",
        "decreased safety awareness",

        "unable to follow commands",
        "unable to follow instructions",

        "hallucinations",
        "visual hallucinations",
        "auditory hallucinations",

        "oriented x1",
        "oriented x2",

        "wandering",
        
        # nausea / vomiting
        "nausea",
        "nauseated",
        "vomiting",
        "vomit",
        "emesis",

        "nausea and vomiting",
        "persistent nausea",
        "persistent vomiting",
        "uncontrolled nausea",
        "uncontrolled vomiting",

        "cannot keep food down",
        "unable to tolerate oral intake",
        "poor intake due to nausea",

        "antiemetic",
        "zofran",
        "ondansetron",
        "compazine",
        "prochlorperazine",
        
        # depression
        "depression",
        "depressed",

        "depressive symptoms",
        "depressed mood",

        "sadness",
        "persistent sadness",

        "tearful",
        "tearfulness",

        "hopelessness",
        "feelings of hopelessness",

        "withdrawn",
        "social withdrawal",

        "loss of interest",
        "loss of pleasure",

        "anhedonia",

        "feeling down",
        "low mood",

        "decreased motivation",

        "decreased engagement",

        "grief related depression",

        "caregiver reports depression",

        "refusing activities",
        
        # spiritual distress
        "spiritual distress",

        "spiritual pain",
        "spiritual suffering",

        "existential distress",
        "existential concerns",
        "existential crisis",

        "spiritual concerns",
        "unresolved spiritual concerns",

        "loss of meaning",
        "loss of purpose",

        "questioning faith",
        "spiritual conflict",
        "loss of faith",

        "fear of afterlife",

        "hopelessness related to spiritual concerns",

        "desire for chaplain",
        "requests chaplain",
        "chaplain support",
        "requests chaplain support",
        "requests spiritual support",
        
        "grief",
        "grieving",
        "bereavement",

        "anticipatory grief",

        "complicated grief",

        "family grief",

        "caregiver grief",

        "loss related distress",

        "difficulty coping with loss",

        "family coping concern",

        "bereavement support needed",

        "caregiver reports grief",
        
        "seizure",
        "seizures",

        "seizure activity",

        "convulsion",
        "convulsions",

        "tonic clonic seizure",
        "grand mal seizure",

        "focal seizure",

        "absence seizure",

        "postictal state",
        "postictal confusion",

        "breakthrough seizure",

        "uncontrolled seizures",

        "new onset seizure",

        "antiepileptic medication",

        "keppra",
        "levetiracetam",

        "dilantin",
        "phenytoin",
        
        "valproic acid",
        "depakote",

        "carbamazepine",
        "tegretol",

        "phenobarbital",
        
        # toxicity
        "toxicity",

        "medication toxicity",

        "drug toxicity",

        "oversedation",

        "excessive somnolence",

        "respiratory depression",

        "polypharmacy effects",

        "adverse drug reaction",

        "phenytoin toxicity",

        "dilantin toxicity",

        "nystagmus",

        "ataxia",

        "slurred speech",

        "unsteady gait",

        "somnolence",

        "difficulty arousing",

        "decreased responsiveness",
        
        "phenytoin level",

        "dilantin level",

        "toxic phenytoin level",
    ]

    keywords: list[str] = []

    # 1) phrase detection first, boundary-safe
    for phrase in phrase_candidates:
        pattern = r"\b" + re.escape(phrase) + r"\b"

        if re.search(pattern, text_value):
            keywords.extend(
                _resolve_keyword_aliases(phrase)
            )


    # 2) token fallback (ONLY valid rule keywords / aliases)
    normalized = text_value
    for sep in [",", ".", ";", ":", "(", ")", "/", "\\", "\n", "\t"]:
        normalized = normalized.replace(sep, " ")

    for token in normalized.split():
        resolved_list = _resolve_keyword_aliases(token)
        for resolved in resolved_list:
            if resolved in RULE_KEYWORDS:
                keywords.append(resolved)

    # 3) deduplicate preserving order
    final_keywords: list[str] = []
    seen: set[str] = set()

    for kw in keywords:
        if kw and kw not in seen:
            seen.add(kw)
            final_keywords.append(kw)

    return final_keywords


# =========================================================
# DATABASE RULE LOOKUP
# =========================================================

def _fetch_outcome_rule(
    db: Session,
    keyword: str,
) -> dict[str, Any] | None:
    row = (
        db.execute(
            text(
                """
                SELECT
                    condition_keyword,

                    goal_text,
                    measurable_outcome,
                    target_timeframe,

                    assessment_evidence_required,
                    problem_statement_template,

                    reassessment_criteria,
                    escalation_criteria,

                    documentation_evidence_required,
                    audit_rationale,

                    patient_specific_required,

                    required_assessment_fields,
                    prohibited_generic_phrases,

                    idg_review_requirements,
                    physician_notification_requirements,
                    caregiver_competency_requirements,

                    quality_measure_name,
                    quality_measure_definition,

                    severity_trigger_rules,
                    symptom_trigger_rules,
                    risk_trigger_rules,

                    priority

                FROM poc_outcome_rules
                WHERE active = TRUE
                AND condition_keyword = :keyword
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
                """
            ),
            {"keyword": keyword},
        )
        .mappings()
        .first()
    )
    
    if row:
        logger.debug(
            "Outcome rule retrieved keyword=%s fields=%s",
            keyword,
            list(dict(row).keys()),
        )

    return dict(row) if row else None

def _fetch_intervention_rules(
    db: Session,
    keyword: str,
) -> list[dict[str, Any]]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                    condition_keyword,
                    discipline,
                    intervention_text,
                    frequency,
                    priority
                FROM poc_intervention_rules
                WHERE active = TRUE
                  AND condition_keyword = :keyword
                ORDER BY priority ASC, created_at ASC
                """
            ),
            {"keyword": keyword},
        )
        .mappings()
        .all()
    )

    return [dict(row) for row in rows]


# =========================================================
# GOAL / PROBLEM BUILDERS
# =========================================================

def _build_goal_from_rules(
    *,
    db: Session,
    keyword: str,
    default_goal_text: str,
) -> dict[str, Any] | None:
    outcome_rule = _fetch_outcome_rule(db, keyword)
    logger.debug(
        "Outcome rule loaded keyword=%s fields=%s",
        keyword,
        list(outcome_rule.keys()) if outcome_rule else [],
    )
    
    if outcome_rule:
        logger.debug(
            "Outcome rule metadata keyword=%s assessment_fields=%s",
            keyword,
            outcome_rule.get("required_assessment_fields"),
        )

    if not outcome_rule:
        return None

    intervention_rules = _fetch_intervention_rules(db, keyword)

    interventions: list[dict[str, Any]] = []
    for rule in intervention_rules:
        interventions.append(
            {
                "discipline": _s(rule["discipline"]),
                "intervention_text": _s(rule["intervention_text"]),
                "frequency": _s(rule["frequency"]),
                "instructions": None,
                "source_kind": "RULE_GENERATED",
                "status": "ACTIVE",
                "sort_order": int(rule["priority"] or 100),
            }
        )

    goal_payload = {
        "problem_statement": _s(
            outcome_rule.get("problem_statement_template")
        ),

        "goal_text": _s(
            outcome_rule.get("goal_text")
        ) or default_goal_text,

        "measurable_outcome": _s(
            outcome_rule.get("measurable_outcome")
        ),

        "target_timeframe": _s(
            outcome_rule.get("target_timeframe")
        ),

        "assessment_evidence_required": _s(
            outcome_rule.get("assessment_evidence_required")
        ),

        "reassessment_criteria": _s(
            outcome_rule.get("reassessment_criteria")
        ),

        "escalation_criteria": _s(
            outcome_rule.get("escalation_criteria")
        ),

        "documentation_evidence_required": _s(
            outcome_rule.get("documentation_evidence_required")
        ),

        "audit_rationale": _s(
            outcome_rule.get("audit_rationale")
        ),

        "patient_specific_required": bool(
            outcome_rule.get("patient_specific_required")
        ),

        "required_assessment_fields":
            outcome_rule.get(
                "required_assessment_fields"
            ) or [],

        "prohibited_generic_phrases":
            outcome_rule.get(
                "prohibited_generic_phrases"
            ) or [],

        "idg_review_requirements": _s(
            outcome_rule.get(
                "idg_review_requirements"
            )
        ),

        "physician_notification_requirements": _s(
            outcome_rule.get(
                "physician_notification_requirements"
            )
        ),

        "caregiver_competency_requirements": _s(
            outcome_rule.get(
                "caregiver_competency_requirements"
            )
        ),

        "quality_measure_name": _s(
            outcome_rule.get(
                "quality_measure_name"
            )
        ),

        "quality_measure_definition": _s(
            outcome_rule.get(
                "quality_measure_definition"
            )
        ),

        "severity_trigger_rules":
            outcome_rule.get(
                "severity_trigger_rules"
            ) or {},

        "symptom_trigger_rules":
            outcome_rule.get(
                "symptom_trigger_rules"
            ) or {},

        "risk_trigger_rules":
            outcome_rule.get(
                "risk_trigger_rules"
            ) or {},

        "source_kind": "RULE_GENERATED",
        "status": "ACTIVE",
        
        "sort_order": int(
            outcome_rule["priority"] or 100
        ),

        "interventions": interventions,
    }
    
    logger.debug(
        "Goal payload generated keyword=%s fields=%s interventions=%s",
        keyword,
        list(goal_payload.keys()),
        len(interventions),
    )

    return goal_payload

def _build_problem_node(
    *,
    db: Session,
    keyword: str,
    label: str,
    source_condition: str,
    diagnosis_context: str = "PRIMARY",
    severity: str = "MODERATE",
    problem_code: str | None = None,
) -> dict[str, Any] | None:
    goal = _build_goal_from_rules(
        db=db,
        keyword=keyword,
        default_goal_text=(
            f"Patient will maintain comfort and minimize distress "
            f"associated with {label.lower()} as condition progresses"
        ),
    )
    if not goal:
        return None

    return {
        "problem_code": problem_code or keyword.upper(),
        "label": label,

        "assessment_evidence_required":
            goal.get("assessment_evidence_required"),

        "reassessment_criteria":
            goal.get("reassessment_criteria"),

        "escalation_criteria":
            goal.get("escalation_criteria"),

        "description": None,
        "severity": severity,
        "source_diagnosis_code": None,
        "source_condition": source_condition,
        "diagnosis_context": diagnosis_context,
        "rule_key": keyword,
        "source_kind": "RULE_GENERATED",
        "status": "ACTIVE",
        "sort_order": 100,

        "goals": [goal],
    }

# =========================================================
# KEYWORD DERIVATION
# =========================================================

def _derive_keywords_from_rn_ica(rn_ica_data: dict[str, Any]) -> list[str]:
    keywords: list[str] = []

    # 1) Canonical problems payload
    problems_root = rn_ica_data.get("problems")
    if isinstance(problems_root, list):
        for problem in problems_root:
            keywords.extend(_resolve_keyword_aliases(problem.get("source_condition", "")))

    # 2) Wrapped canonical payload
    poc_content = rn_ica_data.get("poc_content")
    if isinstance(poc_content, dict):
        problems = poc_content.get("problems", [])
        if isinstance(problems, list):
            for problem in problems:
                keywords.extend(_resolve_keyword_aliases(problem.get("source_condition", "")))

    # 3) Diagnosis summary payload
    diagnosis_summary = rn_ica_data.get("diagnosis_summary") or {}
    primary = diagnosis_summary.get("primary") or {}
    if primary:
        diagnosis_description = primary.get("diagnosis_description", "")
        display_name = primary.get("display_name", "")
        primary_diagnosis = rn_ica_data.get("primary_diagnosis", "")

        for value in [diagnosis_description, display_name, primary_diagnosis]:
            keywords.extend(_resolve_keyword_aliases(value))

    # 4) Free-text scan
    for field_name in ["note_text", "assessment", "narrative"]:
        keywords.extend(_extract_keywords_from_text(rn_ica_data.get(field_name, "")))

    # 5) Always include general decline
    keywords.append("general_decline")

    # 6) Final de-dup preserving order
    final_keywords: list[str] = []
    seen: set[str] = set()

    for kw in keywords:
        if kw and kw not in seen:
            seen.add(kw)
            final_keywords.append(kw)

    return final_keywords


# =========================================================
# PROBLEM LABEL MAPPING
# =========================================================

def _map_keyword_to_problem_identity(keyword: str) -> tuple[str, str]:
    mapping = {
        "chf": ("CHF", "Cardiac decline / CHF"),
        "cardiac_disease": (
            "CARDIAC_DISEASE",
            "Cardiac disease"
        ),
        "copd": ("COPD", "Pulmonary decline / COPD"),
        "respiratory_failure": ("RESPIRATORY_FAILURE", "Respiratory decline"),
        "cancer": ("CANCER", "Cancer-related decline"),
        "metastatic": ("METASTATIC", "Metastatic disease progression"),
        "dementia": ("DEMENTIA", "Cognitive and functional decline"),
        "cva": ("CVA", "Neurologic decline / post-CVA complications"),
        "neuro_degenerative": ("NEURO_DEGENERATIVE", "Progressive neurologic decline"),
        "esrd": ("ESRD", "Renal failure decline"),
        "liver_failure": ("LIVER_FAILURE", "Hepatic failure decline"),
        "infection": ("INFECTION", "Infection-related symptom burden"),
        "general_decline": ("GENERAL_DECLINE", "Progressive functional and clinical decline"),
        "pain": ("PAIN", "Pain"),
        "dyspnea": ("DYSPNEA", "Dyspnea"),
        "fatigue": ("FATIGUE", "Fatigue / weakness"),
        "sleep_disturbance": (
            "SLEEP_DISTURBANCE",
            "Sleep disturbance",
        ),
        "appetite_decline": (
            "APPETITE_DECLINE",
            "Appetite and intake decline",
        ),
        "anxiety": ("ANXIETY", "Anxiety / restlessness"),
        "depression": (
            "DEPRESSION",
            "Depression",
        ),
        "edema": ("EDEMA", "Edema / fluid retention"),
        "fall_risk": ("FALL_RISK", "Fall risk / safety concern"),
        "caregiver_support": (
            "CAREGIVER_SUPPORT",
            "Caregiver support and education",
        ),
        "wound_skin_integrity": (
            "WOUND_SKIN_INTEGRITY",
            "Wound / skin integrity concern",
        ),
        "medication_management": (
            "MEDICATION_MANAGEMENT",
            "Medication management and safety",
        ),
        "constipation": (
            "CONSTIPATION",
            "Constipation and bowel management",
        ),
        "confusion_delirium": (
            "CONFUSION_DELIRIUM",
            "Confusion / delirium",
        ),
        "nausea_vomiting": (
            "NAUSEA_VOMITING",
            "Nausea / vomiting",
        ),
        "spiritual_distress": (
            "SPIRITUAL_DISTRESS",
            "Spiritual distress",
        ),
        "grief_bereavement": (
            "GRIEF_BEREAVEMENT",
            "Grief / bereavement",
        ),
        "seizure_disorder": (
            "SEIZURE_DISORDER",
            "Seizure disorder",
        ),
        "toxicity": (
            "TOXICITY",
            "Medication toxicity",
        ),
    }
    return mapping.get(keyword, (keyword.upper(), keyword.replace("_", " ").title()))


# =========================================================
# PUBLIC ENTRY
# =========================================================

def map_rn_ica_to_problem_nodes(
    db: Session,
    rn_ica_data: dict[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(rn_ica_data, dict):
        raise ValueError("RN ICA payload must be a dictionary")

    keywords = _derive_keywords_from_rn_ica(rn_ica_data)
    problem_nodes: list[dict[str, Any]] = []

    for keyword in keywords:
        problem_code, label = _map_keyword_to_problem_identity(keyword)

        node = _build_problem_node(
            db=db,
            keyword=keyword,
            label=label,
            source_condition=keyword,
            diagnosis_context="PRIMARY",
            severity="MODERATE",
            problem_code=problem_code,
        )
        if node:
            problem_nodes.append(node)

    if not problem_nodes:
        raise ValueError("RN ICA payload produced no rule-mapped POC problems")

    return problem_nodes
