# app/services/clinical_note_validation_engine.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.clinical_note import ClinicalNote
from app.models.incident_report import IncidentReport

from app.services.eligibility.eligibility_registry_service import (
    is_required_when_visible,
)
from app.domain.clinical.rn_ica_keys import (
    RN_ICA_ACCEPTED_KEYS,
    is_rn_ica_key,
)

# =========================================================
# CONSTANTS
# =========================================================

NOTE_STATUS_DRAFT = "DRAFT"
NOTE_STATUS_SIGNED = "SIGNED"
NOTE_STATUS_FINALIZED = "FINALIZED"

INCIDENT_STATUS_NONE = "NONE"
INCIDENT_STATUS_PENDING = "PENDING"
INCIDENT_STATUS_COMPLETED = "COMPLETED"
INCIDENT_STATUS_WAIVED = "WAIVED"

INCIDENT_TYPE_FALL = "FALL"
INCIDENT_TYPE_ADVERSE_REACTION = "ADVERSE_REACTION"
INCIDENT_TYPE_SENTINEL_EVENT = "SENTINEL_EVENT"
INCIDENT_TYPE_OTHER = "OTHER"

INCIDENT_SEVERITY_STANDARD = "STANDARD"
INCIDENT_SEVERITY_SIGNIFICANT = "SIGNIFICANT"
INCIDENT_SEVERITY_SENTINEL = "SENTINEL"

DISCIPLINES_ALLOWED = {"RN", "LVN", "MSW", "SC", "HHA", "CHHA", "MD", "NP"}

CARE_LEVELS_ALLOWED = {
    "RC",
    "CC",
    "GIP",
    "RSP",
    "ROUTINE",
    "CRISIS",
}

ENCOUNTER_TYPES_ALLOWED = {
    "COMPREHENSIVE",
    "ROUTINE",
    "PRN",
    "IDG",
    "DISCIPLINE",
}

REQUIRED_FULL_ROS_SECTIONS = {
    "constitutional",
    "neurological",
    "cardiovascular",
    "respiratory",
    "gastrointestinal",
    "genitourinary",
    "endocrine",
    "musculoskeletal",
    "integumentary",
    "psychosocial",
    "spiritual",
}

REQUIRED_FOCUSED_ROS_SECTIONS = {
    "pain",
    "respiratory",
    "gastrointestinal",
    "neuro_behavior",
    "skin",
    "genitourinary",
}

# =========================================================
# FUNCTIONAL ASSESSMENT GOVERNANCE
# =========================================================

FUNCTIONAL_ASSESSMENT_REQUIRED_NOTE_TYPES = {
    "INITIAL_RN_ICA",
    "RN_ICA",
    "RN_ASSESS",
    "RN_ASSESS_V1",
    "RN_HOPE_ADMISSION",
    "UPDATE_ASSESSMENT",
    "RN_UPDATE_ASSESSMENT",
    "RECERTIFICATION",
    "RECERTIFICATION_ASSESSMENT",
    "RN_RECERTIFICATION",
    "RN_RECERT_ASSESSMENT",
    "RN_RECERT",
    "RECERT",
}

DEMENTIA_DIAGNOSIS_KEYWORDS = {
    "DEMENTIA",
    "ALZHEIMER",
    "ALZHEIMER'S",
    "SENILE DEGENERATION",
    "LEWY BODY",
    "FRONTOTEMPORAL",
    "VASCULAR DEMENTIA",
    "PICK",
    "F01",
    "F02",
    "F03",
    "G30",
}

CARDIAC_DIAGNOSIS_KEYWORDS = {
    "CHF",
    "CONGESTIVE HEART FAILURE",
    "HEART FAILURE",
    "END STAGE HEART",
    "END-STAGE HEART",
    "END STAGE CARDIAC",
    "END-STAGE CARDIAC",
    "CARDIOMYOPATHY",
    "ISCHEMIC CARDIOMYOPATHY",
    "SYSTOLIC HEART FAILURE",
    "DIASTOLIC HEART FAILURE",
    "I50",
    "I42",
}

ROS_SECTION_ALIASES = {
    "constitutional": "constitutional",
    "general": "constitutional",

    "endo": "endocrine",
    "endocrine": "endocrine",

    "neuro": "neurological",
    "neuro_mental": "neurological",
    "neuro_behavior": "neurological",

    "cardiac": "cardiovascular",
    "cardio": "cardiovascular",

    "pulmonary": "respiratory",
    "resp": "respiratory",

    "gi": "gastrointestinal",
    "gastro": "gastrointestinal",

    "gu": "genitourinary",
    "urinary": "genitourinary",

    "msk": "musculoskeletal",
    "mobility": "musculoskeletal",

    "skin": "integumentary",
    "integument": "integumentary",

    "psych": "psychosocial",
    "psychosocial_support": "psychosocial",
    "psychosocial_screening": "psychosocial",

    "spiritual_distress": "spiritual",
    "spiritual_screening": "spiritual",
}

ROS_COMPLETENESS_RULES: dict[str, dict[str, Any]] = {
        "constitutional": {
        "label": "Constitutional",
        "minimum_any_fields": [
            "fatigue",
            "weakness",
            "fever",
            "chills",
            "weight_loss",
            "activity_tolerance",
            "general_appearance",
            "constitutional_narrative",
            "narrative",
        ],
    },
    "neurological": {
        "label": "Neurological / Mental Status",
        "minimum_any_fields": [
            "mental_status",
            "orientation",
            "cognitive_status",
            "communication_ability",
            "speech_pattern",
            "confusion",
            "agitation",
            "anxiety",
            "neuro_narrative",
            "narrative",
        ],
    },
    "cardiovascular": {
        "label": "Cardiovascular",
        "minimum_any_fields": [
            "heart_rhythm",
            "edema",
            "edema_location",
            "pulse_assessment",
            "chest_pain",
            "dizziness",
            "syncope",
            "cardiac_findings",
            "cardiovascular_narrative",
            "narrative",
        ],
    },
    "respiratory": {
        "label": "Respiratory",
        "minimum_any_fields": [
            "dyspnea",
            "dyspnea_level",
            "oxygen_use",
            "oxygen_used",
            "oxygen_lpm",
            "lung_sounds",
            "respiratory_effort",
            "cough",
            "secretions",
            "orthopnea",
            "respiratory_narrative",
            "narrative",
        ],
    },
    "gastrointestinal": {
        "label": "Gastrointestinal",
        "minimum_any_fields": [
            "appetite",
            "oral_intake",
            "food_intake",
            "nausea",
            "vomiting",
            "constipation",
            "diarrhea",
            "bowel_pattern",
            "dysphagia",
            "nutrition",
            "gi_narrative",
            "narrative",
        ],
    },
    "genitourinary": {
        "label": "Genitourinary",
        "minimum_any_fields": [
            "continence",
            "incontinence",
            "foley",
            "catheter",
            "urinary_frequency",
            "urinary_retention",
            "dysuria",
            "hematuria",
            "gu_narrative",
            "narrative",
        ],
    },
    "endocrine": {
        "label": "Endocrine",
        "minimum_any_fields": [
            "diabetes",
            "blood_sugar",
            "hypoglycemia",
            "hyperglycemia",
            "polyuria",
            "polydipsia",
            "thyroid_condition",
            "endocrine_narrative",
            "narrative",
        ],
    },
    "musculoskeletal": {
        "label": "Musculoskeletal / Mobility",
        "minimum_any_fields": [
            "mobility",
            "ambulation",
            "transfer_status",
            "strength",
            "rom",
            "contractures",
            "fall_history",
            "assistive_device",
            "bedbound",
            "musculoskeletal_narrative",
            "narrative",
        ],
    },
    "integumentary": {
        "label": "Skin / Integumentary",
        "minimum_any_fields": [
            "skin_integrity",
            "skin_color",
            "skin_temperature",
            "skin_turgor",
            "pressure_injury",
            "wound",
            "wound_assessment",
            "skin_tear",
            "bruising",
            "edema",
            "comprehensive_skin_assessment",
            "skin_narrative",
            "narrative",
        ],
    },
    "psychosocial": {
        "label": "RN Psychosocial Screening",
        "minimum_any_fields": [
            "support_system",
            "primary_caregiver",
            "caregiver_availability",
            "patient_coping",
            "family_coping",
            "caregiver_stress",
            "psychosocial_concerns",
            "msw_need",
            "psychosocial_narrative",
            "narrative",
        ],
    },
    "spiritual": {
        "label": "RN Spiritual Screening",
        "minimum_any_fields": [
            "faith_preference",
            "spiritual_concerns",
            "spiritual_distress",
            "chaplain_needed",
            "clergy_requested",
            "sc_need",
            "spiritual_narrative",
            "narrative",
        ],
    },
}

VITALS_RECOMMENDED_FIELDS = {
    "bp",
    "pulse",
    "respirations",
    "temperature",
    "spo2",
}

MUAC_REQUIRED_WHEN_PRESENT = {
    "value_cm",
    "arm",
}

VALID_MUAC_ARMS = {"LEFT", "RIGHT"}

VALID_SELF_REPORT_PAIN_SCALES = {
    "NUMERIC",
    "VERBAL",
    "FACES",
}

VALID_OBSERVATIONAL_PAIN_SCALES = {
    "PAINAD",
    "FLACC",
}

RN_ICA_REQUIRED_FIELD_GROUPS = [
    {
        "label": "Primary Diagnosis",
        "section": "Diagnosis Review",
        "paths": [
            "diagnoses.primaryDiagnosis",
            "primary_diagnosis",
            "terminal_diagnosis",
        ],
    },
    {
        "label": "LCD Eligibility Narrative",
        "section": "Eligibility Narrative",
        "paths": [
            "diagnoses.lcdEligibilityNarrative",
            "lcd_eligibility_narrative",
            "assessment_summary",
            "nursing_summary",
        ],
    },
    {
        "label": "Disease Trajectory",
        "section": "Disease Trajectory",
        "paths": [
            "diagnoses.diseaseTrajectory",
            "disease_trajectory",
            "assessment_summary",
        ],
    },
    {
        "label": "PPS",
        "section": "Performance Status",
        "paths": [
            "performanceStatus.pps",
            "functional_assessment.pps",
            "functional_scores.pps",
            "pps",
            "pps_score",
        ],
    },
    {
        "label": "KPS",
        "section": "Performance Status",
        "paths": [
            "performanceStatus.kps",
            "functional_assessment.kps",
            "functional_scores.kps",
            "kps",
            "kps_score",
        ],
    },
    {
        "label": "Code Status",
        "section": "Advance Care Planning",
        "paths": [
            "advancedCarePlanning.codeStatus",
            "code_status",
        ],
    },
    {
        "label": "Life-Sustaining Treatment Preference",
        "section": "Advance Care Planning",
        "paths": [
            "advancedCarePlanning.lifeSustainingTreatmentPreference",
            "life_sustaining_treatment_preference",
        ],
    },
    {
        "label": "Hospitalization Preference",
        "section": "Advance Care Planning",
        "paths": [
            "advancedCarePlanning.hospitalizationPreference",
            "hospitalization_preference",
        ],
    },
    {
        "label": "Pain Screening",
        "section": "Pain Assessment",
        "paths": [
            "pain.verbalizesPain",
            "pain.pain_score",
            "pain_score",
        ],
    },
    {
        "label": "Respiratory Rate",
        "section": "Vitals / Respiratory",
        "paths": [
            "vitals.respirations",
            "respiratory.respiratoryRate",
            "respiratory_rate",
        ],
    },
    {
        "label": "Weight",
        "section": "Nutrition / Measurements",
        "paths": [
            "vitals.weight",
            "nutrition.weight",
            "weight",
        ],
    },
    {
        "label": "Appetite / Intake",
        "section": "Nutrition",
        "paths": [
            "nutrition.appetite",
            "gastrointestinal.appetite",
            "appetite",
        ],
    },
    {
        "label": "ADL Assistance Required",
        "section": "Functional Status",
        "paths": [
            "functionalStatus.adlAssistanceRequired",
            "functional_status.adl_assistance_required",
            "adl_assistance_required",
        ],
    },
    {
        "label": "Mobility Decline",
        "section": "Functional Status",
        "paths": [
            "functionalStatus.mobilityDecline",
            "functional_status.mobility_decline",
            "mobility_decline",
        ],
    },
    {
        "label": "Cognitive Decline",
        "section": "Neurological / Cognitive",
        "paths": [
            "neurological.cognitiveDecline",
            "cognitive_decline",
        ],
    },
    {
        "label": "Plan of Care Narrative",
        "section": "Plan of Care",
        "paths": [
            "planOfCare.summary",
            "plan_of_care",
            "nursing_summary",
        ],
    },
]

# =========================================================
# RESULT DTO
# =========================================================

@dataclass
class ValidationResult:
    warnings: list[str]
    red_flags: list[str]
    audit_flags: list[str]
    needs_clarification: bool
    clarification_items: list[str]
    incident_required: bool
    incident_status: str
    incident_id: UUID | None
    finalization_allowed: bool = True
    compliance_blocking_items: list[dict[str, Any]] = field(default_factory=list)
    compliance_summary: dict[str, Any] = field(default_factory=dict)


# =========================================================
# PUBLIC ENGINE
# =========================================================

def validate_and_trigger_incident(
    db: Session,
    note: ClinicalNote,
    actor_user_id: UUID | None,
    actor_role: str = "SYSTEM_ENGINE",
) -> ValidationResult:
    warnings: list[str] = []
    red_flags: list[str] = []
    audit_flags: list[str] = []
    clarification_items: list[str] = []
    compliance_blocking_items: list[dict[str, Any]] = []

    content = _content(note)

    observed = _extract_json_block(note, content, "observed_data", ["observed"])
    patient_reported = _extract_json_block(note, content, "patient_reported")
    caregiver_reported = _extract_json_block(note, content, "caregiver_reported")
    assessment = _extract_json_block(note, content, "assessment")
    interventions = _extract_json_block(note, content, "interventions")

    _validate_core_classification(
        note,
        content,
        warnings,
        red_flags,
    )

    _validate_truth_layers(
        observed,
        patient_reported,
        caregiver_reported,
        assessment,
        interventions,
        clarification_items,
    )

    _validate_required_ros(
        note,
        content,
        observed,
        assessment,
        warnings,
        audit_flags,
        compliance_blocking_items,
    )

    _validate_required_functional_assessments(
        note,
        content,
        assessment,
        warnings,
        audit_flags,
        compliance_blocking_items,
    )
    
    _validate_required_rn_ica_sections(
        note,
        content,
        assessment,
        warnings,
        audit_flags,
        compliance_blocking_items,
    )
    
    _validate_vitals_and_muac(
        content,
        observed,
        assessment,
        warnings,
        audit_flags,
        compliance_blocking_items,
    )

    _validate_pain_assessment(
        content,
        observed,
        assessment,
        warnings,
        audit_flags,
        compliance_blocking_items,
    )

    _validate_symptom_interventions(
        observed,
        assessment,
        interventions,
        warnings,
    )

    _validate_discipline_specific(
        note,
        content,
        observed,
        assessment,
        warnings,
    )

    incident_decision = _detect_incident(
        note,
        observed,
        patient_reported,
        caregiver_reported,
        assessment,
        interventions,
        warnings,
        red_flags,
        clarification_items,
    )

    incident_id: UUID | None = None
    incident_status = INCIDENT_STATUS_NONE

    if incident_decision["required"]:
        incident_id = _ensure_incident_report(
            db,
            note,
            actor_user_id,
            incident_decision["incident_type"],
            incident_decision["incident_severity"],
            observed,
            patient_reported,
            caregiver_reported,
            assessment,
            interventions,
        )
        incident_status = INCIDENT_STATUS_PENDING
        audit_flags.append(f"incident_triggered:{incident_decision['incident_type']}")

    finalization_allowed = len(compliance_blocking_items) == 0

    compliance_summary = {
        "finalization_allowed": finalization_allowed,
        "blocking_item_count": len(compliance_blocking_items),
        "warnings_count": len(warnings),
        "red_flags_count": len(red_flags),
        "audit_flags_count": len(audit_flags),
        "needs_clarification": bool(clarification_items),
    }

    _persist_validation_result_to_note(
        note,
        warnings,
        red_flags,
        audit_flags,
        clarification_items,
        bool(incident_decision["required"]),
        incident_status,
        incident_id,
        finalization_allowed,
        compliance_blocking_items,
        compliance_summary,
    )

    _write_audit_log(
        db,
        actor_user_id,
        actor_role,
        "CLINICAL_NOTE_VALIDATED",
        "clinical_note",
        note.id,
    )

    db.add(note)
    db.flush()

    return ValidationResult(
        warnings=warnings,
        red_flags=red_flags,
        audit_flags=audit_flags,
        needs_clarification=bool(clarification_items),
        clarification_items=clarification_items,
        incident_required=bool(incident_decision["required"]),
        incident_status=incident_status,
        incident_id=incident_id,
        finalization_allowed=finalization_allowed,
        compliance_blocking_items=compliance_blocking_items,
        compliance_summary=compliance_summary,
    )


# =========================================================
# VALIDATION RULES
# =========================================================

def _validate_core_classification(
    note: ClinicalNote,
    content: dict[str, Any],
    warnings: list[str],
    red_flags: list[str],
) -> None:
    care_level = _clean_upper(_note_value(note, content, "care_level"))
    encounter_type = _clean_upper(_note_value(note, content, "encounter_type"))
    discipline = _clean_upper(_note_value(note, content, "discipline"))
    visit_type = _clean_upper(_note_value(note, content, "visit_type"))
    visit_origin = _clean_upper(_note_value(note, content, "visit_origin"))

    if care_level and care_level not in CARE_LEVELS_ALLOWED:
        red_flags.append(f"invalid_care_level:{care_level}")

    if encounter_type and encounter_type not in ENCOUNTER_TYPES_ALLOWED:
        red_flags.append(f"invalid_encounter_type:{encounter_type}")

    if discipline and discipline not in DISCIPLINES_ALLOWED:
        red_flags.append(f"invalid_discipline:{discipline}")

    if visit_type in {"PRN", "CRISIS"} and visit_origin == "SCHEDULED":
        warnings.append("visit_type suggests unscheduled workflow but visit_origin is scheduled")


def _validate_truth_layers(
    observed: dict[str, Any],
    patient_reported: dict[str, Any],
    caregiver_reported: dict[str, Any],
    assessment: dict[str, Any],
    interventions: dict[str, Any],
    clarification_items: list[str],
) -> None:
    if observed and not isinstance(observed, dict):
        clarification_items.append("observed_data must be structured json object")

    if patient_reported and not isinstance(patient_reported, dict):
        clarification_items.append("patient_reported must be structured json object")

    if caregiver_reported and not isinstance(caregiver_reported, dict):
        clarification_items.append("caregiver_reported must be structured json object")

    if assessment and not isinstance(assessment, dict):
        clarification_items.append("assessment must be structured json object")

    if interventions and not isinstance(interventions, dict):
        clarification_items.append("interventions must be structured json object")


def _validate_required_ros(
    note: ClinicalNote,
    content: dict[str, Any],
    observed: dict[str, Any],
    assessment: dict[str, Any],
    warnings: list[str],
    audit_flags: list[str],
    compliance_blocking_items: list[dict[str, Any]],
) -> None:
    raw_ros = _extract_review_of_systems(
        content,
        observed,
        assessment,
    )

    ros = _canonicalize_ros(raw_ros)

    encounter_type = _clean_upper(
        _note_value(note, content, "encounter_type")
    )

    discipline = _clean_upper(
        _note_value(note, content, "discipline")
    )

    note_type = _clean_upper(
        _note_value(note, content, "note_type")
    )

    form_key = _clean_upper(
        _note_value(note, content, "form_key")
    )

    form_type = _clean_upper(
        _note_value(note, content, "form_type")
    )

    is_rn_ica = (
        discipline == "RN"
        and (
            is_rn_ica_key(note_type)
            or is_rn_ica_key(form_key)
            or form_type in {
                "ASSESS",
                "COMPREHENSIVE",
            }
        )
    )

    if is_rn_ica:
        return

    requires_full_ros = (
        encounter_type == "COMPREHENSIVE"
    )

    if requires_full_ros:
        missing = sorted(
            section
            for section in REQUIRED_FULL_ROS_SECTIONS
            if section not in ros
        )

        if missing:
            warnings.append(
                f"comprehensive_missing_ros:{', '.join(missing)}"
            )
            audit_flags.append("full_ros_incomplete")

            for section in missing:
                _add_blocker(
                    compliance_blocking_items,
                    "Review of Systems",
                    _section_label(section),
                    None,
                    f"{_section_label(section)} assessment missing",
                    "RN_ICA_REQUIRED",
                    "Required comprehensive RN ICA review-of-systems section is missing.",
                    f"Complete the {_section_label(section)} assessment section.",
                    _navigation(
                        "Review of Systems",
                        "review_of_systems",
                        "Review of Systems",
                        section,
                        _section_label(section),
                        section,
                        f"{_section_label(section)} Assessment",
                    ),
                    [
                        "RN_ICA_FINALIZATION",
                        "INITIAL_RN_ICA_TASK_COMPLETION",
                        "BILLING_READINESS",
                    ],
                )

        for section in sorted(REQUIRED_FULL_ROS_SECTIONS):
            if section not in ros:
                continue

            section_data = _obj(ros.get(section))

            if not _ros_section_is_complete(section, section_data):
                warnings.append(
                    f"comprehensive_incomplete_ros_section:{section}"
                )
                audit_flags.append("full_ros_incomplete")

                _add_blocker(
                    compliance_blocking_items,
                    "Review of Systems",
                    _section_label(section),
                    None,
                    f"{_section_label(section)} assessment incomplete",
                    "RN_ICA_REQUIRED",
                    "Section is present but does not contain enough assessment data to support a compliant comprehensive RN ICA.",
                    f"Document assessment findings for {_section_label(section)}.",
                    _navigation(
                        "Review of Systems",
                        "review_of_systems",
                        "Review of Systems",
                        section,
                        _section_label(section),
                        section,
                        f"{_section_label(section)} Assessment",
                    ),
                    [
                        "RN_ICA_FINALIZATION",
                        "INITIAL_RN_ICA_TASK_COMPLETION",
                        "BILLING_READINESS",
                    ],
                )

    elif encounter_type in {"ROUTINE", "PRN"}:
        present = {
            section
            for section in REQUIRED_FOCUSED_ROS_SECTIONS
            if section in ros
        }

        if not present:
            warnings.append("routine_or_prn_note_missing_focused_ros")
            audit_flags.append("focused_ros_missing")

def _validate_required_rn_ica_sections(
    note: ClinicalNote,
    content: dict[str, Any],
    assessment: dict[str, Any],
    warnings: list[str],
    audit_flags: list[str],
    compliance_blocking_items: list[dict[str, Any]],
) -> None:
    if not _is_rn_ica_workflow(note, content):
        return

    rn_ica = _rn_ica_payload(content, assessment)

    if not rn_ica:
        warnings.append("rn_ica_payload_missing")
        audit_flags.append("rn_ica_payload_missing")

        _add_rn_ica_required_field_blocker(
            compliance_blocking_items,
            label="RN ICA Payload",
            section="RN ICA",
            path="assessment",
        )
        return

    for field_group in RN_ICA_REQUIRED_FIELD_GROUPS:
        path, value = _first_present_path(
            rn_ica,
            field_group["paths"],
        )

        if path and not _empty(value):
            continue

        expected_path = field_group["paths"][0]
        label = field_group["label"]
        section = field_group["section"]

        warnings.append(
            f"rn_ica_required_missing:{expected_path}"
        )

        audit_flags.append(
            "rn_ica_required_missing"
        )

        _add_rn_ica_required_field_blocker(
            compliance_blocking_items,
            label=label,
            section=section,
            path=expected_path,
        )
        
def _validate_required_functional_assessments(
    note: ClinicalNote,
    content: dict[str, Any],
    assessment: dict[str, Any],
    warnings: list[str],
    audit_flags: list[str],
    compliance_blocking_items: list[dict[str, Any]],
) -> None:
    """
    Functional assessment governance.

    Required only for formal RN disease progression workflows:

    - RN ICA
    - RN Update Assessment
    - RN Recertification Assessment

    Always required when workflow applies:
    - PPS
    - KPS

    Conditionally required when clinically relevant:
    - FAST when dementia-related diagnosis exists
    - NYHA when cardiac-related diagnosis exists

    Routine and PRN visits are not required to document
    PPS, KPS, FAST, or NYHA.
    """

    discipline = _clean_upper(
        _note_value(note, content, "discipline")
    )

    note_type = _clean_upper(
        _note_value(note, content, "note_type")
    )

    form_key = _clean_upper(
        _note_value(note, content, "form_key")
    )

    form_type = _clean_upper(
        _note_value(note, content, "form_type")
    )

    assessment_type = _clean_upper(
        _note_value(note, content, "assessment_type")
    )

    visit_type = _clean_upper(
        _note_value(note, content, "visit_type")
    )

    if discipline != "RN":
        return

    classification_values = {
        note_type,
        form_key,
        form_type,
        assessment_type,
        visit_type,
    }

    is_formal_functional_assessment = bool(
        classification_values.intersection(
            FUNCTIONAL_ASSESSMENT_REQUIRED_NOTE_TYPES
        )
    )

    if not is_formal_functional_assessment:
        return

    def collect_text(value: Any, output: list[str]) -> None:
        if value is None:
            return

        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                output.append(cleaned)
            return

        if isinstance(value, (int, float, bool)):
            output.append(str(value))
            return

        if isinstance(value, dict):
            for nested_value in value.values():
                collect_text(nested_value, output)
            return

        if isinstance(value, list):
            for nested_value in value:
                collect_text(nested_value, output)
            return

    diagnosis_text_parts: list[str] = []

    diagnosis_sources = [
        content.get("primary_diagnosis"),
        content.get("primary_dx"),
        content.get("primary_dx_code"),
        content.get("primary_diagnosis_description"),
        content.get("diagnosis"),
        content.get("diagnoses"),
        content.get("secondary_diagnoses"),
        content.get("comorbidities"),
        content.get("related_diagnoses"),
        assessment.get("primary_diagnosis"),
        assessment.get("primary_dx"),
        assessment.get("primary_dx_code"),
        assessment.get("primary_diagnosis_description"),
        assessment.get("diagnosis"),
        assessment.get("diagnoses"),
        assessment.get("secondary_diagnoses"),
        assessment.get("comorbidities"),
        assessment.get("related_diagnoses"),
    ]

    for diagnosis_source in diagnosis_sources:
        collect_text(diagnosis_source, diagnosis_text_parts)

    diagnosis_text = " ".join(diagnosis_text_parts).upper()

    dementia_related = any(
        keyword in diagnosis_text
        for keyword in DEMENTIA_DIAGNOSIS_KEYWORDS
    )

    cardiac_related = any(
        keyword in diagnosis_text
        for keyword in CARDIAC_DIAGNOSIS_KEYWORDS
    )

    pps = (
        content.get("pps")
        or content.get("pps_score")
        or assessment.get("pps")
        or assessment.get("pps_score")
        or _obj(content.get("functional_scores")).get("pps")
        or _obj(content.get("functional_scores")).get("pps_score")
        or _obj(assessment.get("functional_scores")).get("pps")
        or _obj(assessment.get("functional_scores")).get("pps_score")
        or _obj(content.get("functional_assessment")).get("pps")
        or _obj(content.get("functional_assessment")).get("pps_score")
        or _obj(assessment.get("functional_assessment")).get("pps")
        or _obj(assessment.get("functional_assessment")).get("pps_score")
        or _obj(content.get("scores")).get("pps")
        or _obj(content.get("scores")).get("pps_score")
        or _obj(assessment.get("scores")).get("pps")
        or _obj(assessment.get("scores")).get("pps_score")
    )

    kps = (
        content.get("kps")
        or content.get("kps_score")
        or assessment.get("kps")
        or assessment.get("kps_score")
        or _obj(content.get("functional_scores")).get("kps")
        or _obj(content.get("functional_scores")).get("kps_score")
        or _obj(assessment.get("functional_scores")).get("kps")
        or _obj(assessment.get("functional_scores")).get("kps_score")
        or _obj(content.get("functional_assessment")).get("kps")
        or _obj(content.get("functional_assessment")).get("kps_score")
        or _obj(assessment.get("functional_assessment")).get("kps")
        or _obj(assessment.get("functional_assessment")).get("kps_score")
        or _obj(content.get("scores")).get("kps")
        or _obj(content.get("scores")).get("kps_score")
        or _obj(assessment.get("scores")).get("kps")
        or _obj(assessment.get("scores")).get("kps_score")
    )

    fast = (
        content.get("fast")
        or content.get("fast_stage")
        or content.get("fast_score")
        or assessment.get("fast")
        or assessment.get("fast_stage")
        or assessment.get("fast_score")
        or _obj(content.get("functional_scores")).get("fast")
        or _obj(content.get("functional_scores")).get("fast_stage")
        or _obj(content.get("functional_scores")).get("fast_score")
        or _obj(assessment.get("functional_scores")).get("fast")
        or _obj(assessment.get("functional_scores")).get("fast_stage")
        or _obj(assessment.get("functional_scores")).get("fast_score")
        or _obj(content.get("functional_assessment")).get("fast")
        or _obj(content.get("functional_assessment")).get("fast_stage")
        or _obj(content.get("functional_assessment")).get("fast_score")
        or _obj(assessment.get("functional_assessment")).get("fast")
        or _obj(assessment.get("functional_assessment")).get("fast_stage")
        or _obj(assessment.get("functional_assessment")).get("fast_score")
        or _obj(content.get("scores")).get("fast")
        or _obj(content.get("scores")).get("fast_stage")
        or _obj(content.get("scores")).get("fast_score")
        or _obj(assessment.get("scores")).get("fast")
        or _obj(assessment.get("scores")).get("fast_stage")
        or _obj(assessment.get("scores")).get("fast_score")
    )

    nyha = (
        content.get("nyha")
        or content.get("nyha_class")
        or assessment.get("nyha")
        or assessment.get("nyha_class")
        or _obj(content.get("functional_scores")).get("nyha")
        or _obj(content.get("functional_scores")).get("nyha_class")
        or _obj(assessment.get("functional_scores")).get("nyha")
        or _obj(assessment.get("functional_scores")).get("nyha_class")
        or _obj(content.get("functional_assessment")).get("nyha")
        or _obj(content.get("functional_assessment")).get("nyha_class")
        or _obj(assessment.get("functional_assessment")).get("nyha")
        or _obj(assessment.get("functional_assessment")).get("nyha_class")
        or _obj(content.get("scores")).get("nyha")
        or _obj(content.get("scores")).get("nyha_class")
        or _obj(assessment.get("scores")).get("nyha")
        or _obj(assessment.get("scores")).get("nyha_class")
    )

    required_scores: list[dict[str, str]] = [
        {
            "key": "pps",
            "label": "PPS",
            "value": pps,
            "reason": (
                "PPS is required for RN ICA, Update Assessment, "
                "and Recertification Assessment."
            ),
            "correction": (
                "Document a PPS score before finalizing this assessment."
            ),
        },
        {
            "key": "kps",
            "label": "KPS",
            "value": kps,
            "reason": (
                "KPS is required for RN ICA, Update Assessment, "
                "and Recertification Assessment."
            ),
            "correction": (
                "Document a KPS score before finalizing this assessment."
            ),
        },
    ]

    if (
        dementia_related
        and is_required_when_visible(
            "fast_stage"
        )
    ):
        required_scores.append(
            {
                "key": "fast",
                "label": "FAST",
                "value": fast,
                "reason": (
                    "FAST is required because a dementia-related diagnosis "
                    "is documented and dementia progression is clinically relevant."
                ),
                "correction": (
                    "Document a FAST stage before finalizing this assessment."
                ),
            }
        )

    if (
        cardiac_related
        and is_required_when_visible(
            "nyha_class"
        )
    ):
        required_scores.append(
            {
                "key": "nyha",
                "label": "NYHA",
                "value": nyha,
                "reason": (
                    "NYHA is required because a cardiac diagnosis is documented "
                    "and cardiac progression is clinically relevant."
                ),
                "correction": (
                    "Document an NYHA classification before finalizing this assessment."
                ),
            }
        )

    for required_score in required_scores:
        score_key = required_score["key"]
        score_label = required_score["label"]
        score_value = required_score["value"]

        if not _empty(score_value):
            continue

        warnings.append(
            f"functional_assessment_missing:{score_key}"
        )

        audit_flags.append(
            "functional_assessment_missing"
        )

        _add_blocker(
            compliance_blocking_items,
            "Functional Assessment",
            score_label,
            score_key,
            f"{score_label} missing",
            "RN_ICA_REQUIRED",
            required_score["reason"],
            required_score["correction"],
            _navigation(
                "Functional Assessment",
                "functional_assessment",
                "Functional Assessment",
                score_key,
                score_label,
                score_key,
                f"{score_label} Score",
            ),
            [
                "RN_ICA_FINALIZATION",
                "INITIAL_RN_ICA_TASK_COMPLETION",
                "BILLING_READINESS",
            ],
        )
    
def _validate_vitals_and_muac(
    content: dict[str, Any],
    observed: dict[str, Any],
    assessment: dict[str, Any],
    warnings: list[str],
    audit_flags: list[str],
    compliance_blocking_items: list[dict[str, Any]],
) -> None:
    vitals = _extract_vitals(content, observed, assessment)

    if not vitals:
        warnings.append("vitals_missing")
        audit_flags.append("vitals_missing")
        return

    missing_recommended = sorted(
        field for field in VITALS_RECOMMENDED_FIELDS if _empty(vitals.get(field))
    )

    if missing_recommended:
        warnings.append(f"vitals_missing_recommended:{', '.join(missing_recommended)}")
        audit_flags.append("vitals_incomplete")

    muac = _obj(vitals.get("muac") or assessment.get("muac") or observed.get("muac"))

    if muac:
        missing_muac = sorted(
            field for field in MUAC_REQUIRED_WHEN_PRESENT if _empty(muac.get(field))
        )

        if missing_muac:
            warnings.append(f"muac_incomplete:{', '.join(missing_muac)}")
            audit_flags.append("muac_incomplete")

            _add_blocker(
                compliance_blocking_items,
                "Vitals / Measurements",
                "MUAC",
                None,
                "MUAC measurement incomplete",
                "RN_ICA_REQUIRED",
                "MUAC was started but required MUAC value or arm side is missing.",
                "Complete MUAC value in centimeters and select Left or Right arm.",
                _navigation(
                    "Vitals / Measurements",
                    "vitals",
                    "Vitals / Measurements",
                    "muac",
                    "MUAC",
                    "muac",
                    "MUAC Measurement",
                ),
                [
                    "RN_ICA_FINALIZATION",
                    "BILLING_READINESS",
                ],
            )

        arm = _clean_upper(muac.get("arm"))
        if arm and arm not in VALID_MUAC_ARMS:
            warnings.append(f"muac_invalid_arm:{arm}")
            audit_flags.append("muac_invalid_arm")


def _validate_pain_assessment(
    content: dict[str, Any],
    observed: dict[str, Any],
    assessment: dict[str, Any],
    warnings: list[str],
    audit_flags: list[str],
    compliance_blocking_items: list[dict[str, Any]],
) -> None:
    pain = _extract_pain(content, observed, assessment)

    if not pain:
        return

    pain_present = (
        _truthy(pain.get("pain_present"))
        or _numeric(pain.get("severity")) > 0
        or _numeric(pain.get("pain_score")) > 0
    )

    if not pain_present:
        return

    self_report_capable = pain.get("self_report_capable")

    if self_report_capable is None:
        warnings.append("pain_present_without_self_report_capability")
        audit_flags.append("pain_assessment_incomplete")
        _add_pain_blocker(
            compliance_blocking_items,
            "Pain self-report capability missing",
            "Pain is present but the note does not identify whether the patient can reliably self-report pain.",
            "Document whether the patient can reliably self-report pain.",
            "self_report_capable",
            "Can Patient Reliably Self-Report Pain?",
        )
        return

    scale_used = _clean_upper(pain.get("pain_scale_used"))

    if _truthy(self_report_capable):
        if scale_used not in VALID_SELF_REPORT_PAIN_SCALES:
            warnings.append("pain_self_report_without_valid_scale")
            audit_flags.append("pain_assessment_incomplete")
            _add_pain_blocker(
                compliance_blocking_items,
                "Pain scale missing",
                "Patient can self-report pain but no valid numeric/verbal pain scale is documented.",
                "Select Numeric, Verbal, or Faces pain scale and document score/response.",
                "pain_scale_used",
                "Pain Scale Used",
            )

    else:
        if scale_used not in VALID_OBSERVATIONAL_PAIN_SCALES:
            warnings.append("pain_nonverbal_without_painad_or_flacc")
            audit_flags.append("pain_assessment_incomplete")
            _add_pain_blocker(
                compliance_blocking_items,
                "Observational pain scale missing",
                "Patient cannot reliably self-report pain. PAINAD or FLACC is required.",
                "Complete PAINAD or FLACC assessment.",
                "pain_scale_used",
                "Pain Scale Used",
            )


def _validate_symptom_interventions(
    observed: dict[str, Any],
    assessment: dict[str, Any],
    interventions: dict[str, Any],
    warnings: list[str],
) -> None:
    pain = _extract_pain({}, observed, assessment)
    respiratory = _obj(observed.get("respiratory") or assessment.get("respiratory"))
    skin = _obj(observed.get("skin") or assessment.get("skin"))

    if (
        _truthy(pain.get("pain_present"))
        or _numeric(pain.get("severity")) > 0
        or _numeric(pain.get("pain_score")) > 0
    ):
        if not interventions.get("pain"):
            warnings.append("pain_present_without_documented_intervention")

    dyspnea_level = _clean_upper(respiratory.get("dyspnea_level") or respiratory.get("dyspnea"))
    if dyspnea_level in {"MODERATE", "SEVERE", "AT_REST"} and not interventions.get("respiratory"):
        warnings.append("moderate_or_severe_dyspnea_without_intervention")

    if _truthy(skin.get("skin_tear")) and not interventions.get("skin"):
        warnings.append("skin_tear_documented_without_skin_intervention")


def _validate_discipline_specific(
    note: ClinicalNote,
    content: dict[str, Any],
    observed: dict[str, Any],
    assessment: dict[str, Any],
    warnings: list[str],
) -> None:
    discipline = _clean_upper(_note_value(note, content, "discipline"))
    encounter_type = _clean_upper(_note_value(note, content, "encounter_type"))
    visit_type = _clean_upper(_note_value(note, content, "visit_type"))

    if discipline in {"MSW", "SC"}:
        baseline_ref = assessment.get("rn_baseline_reference_id")
        if encounter_type == "COMPREHENSIVE" and not baseline_ref:
            warnings.append("msw_sc_comprehensive_note_missing_rn_baseline_reference")

    if discipline in {"HHA", "CHHA"}:
        adls = _obj(observed.get("adls") or assessment.get("adls"))
        if not adls:
            warnings.append("hha_note_missing_adl_observation")

    if discipline in {"MD", "NP"} and visit_type == "F2F":
        if not assessment.get("eligibility_justification"):
            warnings.append("f2f_note_missing_eligibility_justification")


# =========================================================
# INCIDENT DETECTION
# =========================================================

def _detect_incident(
    note: ClinicalNote,
    observed: dict[str, Any],
    patient_reported: dict[str, Any],
    caregiver_reported: dict[str, Any],
    assessment: dict[str, Any],
    interventions: dict[str, Any],
    warnings: list[str],
    red_flags: list[str],
    clarification_items: list[str],
) -> dict[str, Any]:
    incident_required = False
    incident_type = INCIDENT_TYPE_OTHER
    incident_severity = INCIDENT_SEVERITY_STANDARD

    fall_reported = (
        _truthy(caregiver_reported.get("fall_reported"))
        or _truthy(patient_reported.get("fall_reported"))
    )
    fall_observed = (
        _truthy(observed.get("fall"))
        or _truthy(_obj(observed.get("incident")).get("fall"))
    )

    skin = _obj(observed.get("skin") or assessment.get("skin"))
    injury = _obj(observed.get("injury") or assessment.get("injury"))
    med_event = _obj(observed.get("medication_event") or assessment.get("medication_event"))
    disposition = _obj(assessment.get("disposition"))

    skin_tear = _truthy(skin.get("skin_tear")) or _truthy(injury.get("skin_tear"))
    bruise = _truthy(injury.get("bruise")) or _truthy(skin.get("bruising"))
    laceration = _truthy(injury.get("laceration"))
    fracture = _truthy(injury.get("fracture"))
    hospitalization_required = (
        _truthy(injury.get("hospitalization_required"))
        or _truthy(disposition.get("hospitalization_required"))
    )

    if fall_reported or fall_observed:
        incident_required = True
        incident_type = INCIDENT_TYPE_FALL

    if skin_tear or bruise or laceration or fracture:
        incident_required = True
        if incident_type != INCIDENT_TYPE_FALL:
            incident_type = INCIDENT_TYPE_OTHER

    if _truthy(med_event.get("adverse_reaction")):
        incident_required = True
        incident_type = INCIDENT_TYPE_ADVERSE_REACTION

    if hospitalization_required:
        incident_required = True
        incident_severity = INCIDENT_SEVERITY_SENTINEL
        if incident_type == INCIDENT_TYPE_OTHER:
            incident_type = INCIDENT_TYPE_SENTINEL_EVENT

    if any([skin_tear, laceration, fracture]) and incident_severity == INCIDENT_SEVERITY_STANDARD:
        incident_severity = INCIDENT_SEVERITY_SIGNIFICANT

    caregiver_no_injury = str(caregiver_reported.get("reported_injury") or "").strip().lower() in {
        "none",
        "no",
        "no injury",
    }

    injury_observed = any([skin_tear, bruise, laceration, fracture])

    if caregiver_no_injury and injury_observed:
        red_flags.append("reported_no_injury_but_clinician_observed_injury")
        clarification_items.append("family/facility report of no injury differs from clinician findings")
        incident_required = True

        if incident_type == INCIDENT_TYPE_OTHER and (fall_reported or fall_observed):
            incident_type = INCIDENT_TYPE_FALL

    note_category = _clean_upper(_note_value(note, _content(note), "note_category"))
    if incident_required and note_category == "MISSED_VISIT":
        warnings.append("incident flagged on note that appears to be a missed visit; review workflow context")

    return {
        "required": incident_required,
        "incident_type": incident_type,
        "incident_severity": incident_severity,
    }


# =========================================================
# INCIDENT PLACEHOLDER CREATION
# =========================================================

def _ensure_incident_report(
    db: Session,
    note: ClinicalNote,
    actor_user_id: UUID | None,
    incident_type: str,
    incident_severity: str,
    observed: dict[str, Any],
    patient_reported: dict[str, Any],
    caregiver_reported: dict[str, Any],
    assessment: dict[str, Any],
    interventions: dict[str, Any],
) -> UUID | None:
    existing = (
        db.query(IncidentReport)
        .filter(
            IncidentReport.tenant_id == note.tenant_id,
            IncidentReport.patient_id == note.patient_id,
            IncidentReport.clinical_note_id == note.id,
            IncidentReport.incident_type == incident_type,
        )
        .first()
    )

    if existing:
        return existing.id

    reported_by = _coerce_report_party(caregiver_reported) or _coerce_report_party(patient_reported)
    witnessed_by = _coerce_witness_party(caregiver_reported)
    place = _coerce_place(observed, assessment)
    area = _coerce_area(observed, assessment)
    surface = _coerce_surface(observed, assessment)
    medication_used = _coerce_medication_used(observed)
    activity_at_time = _coerce_activity(observed, caregiver_reported)
    injury_level = _coerce_injury_level(observed, assessment)
    injury_type = _coerce_injury_type(observed)
    other_injury_text = _coerce_other_injury_text(observed)
    narrative = _build_incident_narrative(note, observed, patient_reported, caregiver_reported)

    incident = IncidentReport(
        tenant_id=note.tenant_id,
        patient_id=note.patient_id,
        clinical_note_id=note.id,
        incident_type=incident_type,
        incident_severity=incident_severity,
        incident_date=note.encounter_date,
        reported_date=note.encounter_date,
        incident_time=getattr(note, "encounter_time", None),
        reported_by=reported_by,
        witnessed_by=witnessed_by,
        place=place,
        area=area,
        surface=surface,
        medication_used=medication_used,
        activity_at_time=activity_at_time,
        injury_level=injury_level,
        injury_type=injury_type,
        other_injury_text=other_injury_text,
        narrative=narrative,
        entered_by=actor_user_id,
    )

    db.add(incident)
    db.flush()

    _write_audit_log(
        db,
        actor_user_id,
        "SYSTEM_ENGINE",
        "INCIDENT_AUTO_CREATED",
        "incident_report",
        incident.id,
    )

    return incident.id


# =========================================================
# COMPLIANCE BLOCKER HELPERS
# =========================================================

def _add_blocker(
    blocking_items: list[dict[str, Any]],
    section: str,
    subsection: str,
    item_code: str | None,
    label: str,
    compliance_type: str,
    reason: str,
    correction_required: str,
    navigation: dict[str, Any],
    blocks: list[str],
) -> None:
    blocking_items.append(
        {
            "section": section,
            "subsection": subsection,
            "item_code": item_code,
            "label": label,
            "compliance_type": compliance_type,
            "severity": "HARD_STOP",
            "reason": reason,
            "correction_required": correction_required,
            "navigation": navigation,
            "blocks": blocks,
        }
    )


def _add_pain_blocker(
    blocking_items: list[dict[str, Any]],
    label: str,
    reason: str,
    correction_required: str,
    field_code: str,
    field_label: str,
) -> None:
    _add_blocker(
        blocking_items,
        "Pain Assessment",
        "Pain Assessment",
        None,
        label,
        "RN_ICA_REQUIRED",
        reason,
        correction_required,
        _navigation(
            "Pain Assessment",
            "pain_assessment",
            "Pain Assessment",
            "pain",
            "Pain Assessment",
            field_code,
            field_label,
        ),
        [
            "RN_ICA_FINALIZATION",
            "INITIAL_RN_ICA_TASK_COMPLETION",
            "BILLING_READINESS",
        ],
    )


def _navigation(
    ui_panel: str,
    section_code: str,
    section_title: str,
    subsection_code: str,
    subsection_title: str,
    field_code: str,
    field_label: str,
    button_label: str = "Fix Now",
) -> dict[str, Any]:
    return {
        "ui_tab": "RN ICA",
        "ui_panel": ui_panel,
        "section_code": section_code,
        "section_title": section_title,
        "subsection_code": subsection_code,
        "subsection_title": subsection_title,
        "field_code": field_code,
        "field_label": field_label,
        "scroll_anchor": f"{section_code}.{subsection_code}.{field_code}",
        "button_label": button_label,
    }


# =========================================================
# EXTRACTION HELPERS
# =========================================================

def _content(note: ClinicalNote) -> dict[str, Any]:
    return note.content if isinstance(getattr(note, "content", None), dict) else {}


# =========================================================
# PUBLIC ACCESSOR
# =========================================================
# Validation results (red_flags, needs_clarification, incident_required, etc.)
# are NOT stored as top-level ClinicalNote columns. They are persisted by
# _persist_validation_result_to_note() into note.content["_validation"] at
# note-submission time. Any code that needs to re-read a note's validation
# outcome later (IDG readiness checks, dashboards, alerts) MUST go through
# this accessor rather than attempting direct attribute access on the note
# (e.g. `note.red_flags`), which will raise AttributeError since no such
# column exists.
_EMPTY_VALIDATION_FLAGS: dict[str, Any] = {
    "warnings": [],
    "red_flags": [],
    "audit_flags": [],
    "needs_clarification": False,
    "clarification_items": [],
    "incident_required": False,
    "incident_status": None,
    "incident_id": None,
    "finalization_allowed": True,
    "compliance_blocking_items": [],
    "compliance_summary": {},
}


def get_note_validation_flags(note: ClinicalNote) -> dict[str, Any]:
    """Return the persisted validation payload for a clinical note.

    Falls back to safe empty defaults if the note was never validated
    (e.g. legacy notes created before this engine existed) or its content
    isn't a dict.
    """
    content = _content(note)
    validation = content.get("_validation") if isinstance(content, dict) else None
    if not isinstance(validation, dict):
        return dict(_EMPTY_VALIDATION_FLAGS)
    merged = dict(_EMPTY_VALIDATION_FLAGS)
    merged.update(validation)
    return merged


def _extract_json_block(
    note: ClinicalNote,
    content: dict[str, Any],
    key: str,
    aliases: list[str] | None = None,
) -> dict[str, Any]:
    aliases = aliases or []

    direct = getattr(note, key, None)
    if isinstance(direct, dict):
        return direct

    value = content.get(key)
    if isinstance(value, dict):
        return value

    for alias in aliases:
        alias_value = content.get(alias)
        if isinstance(alias_value, dict):
            return alias_value

    return {}


def _note_value(note: ClinicalNote, content: dict[str, Any], key: str) -> Any:
    if hasattr(note, key):
        value = getattr(note, key)
        if value is not None:
            return value

    if key in content:
        return content.get(key)

    metadata = _obj(content.get("metadata"))
    if key in metadata:
        return metadata.get(key)

    visit = _obj(content.get("visit"))
    if key in visit:
        return visit.get(key)

    return None

def _get_path(data: dict[str, Any], path: str) -> Any:
    current: Any = data

    for part in path.split("."):
        if not isinstance(current, dict):
            return None

        current = current.get(part)

    return current


def _first_present_path(data: dict[str, Any], paths: list[str]) -> tuple[str | None, Any]:
    for path in paths:
        value = _get_path(data, path)

        if not _empty(value):
            return path, value

    return None, None


def _is_rn_ica_workflow(
    note: ClinicalNote,
    content: dict[str, Any],
) -> bool:
    discipline = _clean_upper(
        _note_value(note, content, "discipline")
    )

    if discipline != "RN":
        return False

    note_type = _clean_upper(
        _note_value(note, content, "note_type")
    )

    form_key = _clean_upper(
        _note_value(note, content, "form_key")
    )

    form_type = _clean_upper(
        _note_value(note, content, "form_type")
    )

    assessment_type = _clean_upper(
        _note_value(note, content, "assessment_type")
    )

    return (
        is_rn_ica_key(note_type)
        or is_rn_ica_key(form_key)
        or is_rn_ica_key(assessment_type)
        or form_type in {
            "ASSESS",
            "COMPREHENSIVE",
        }
    )


def _rn_ica_payload(
    content: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    """
    Supports both legacy flat RN assessment payloads and newer RNICA.jsx payloads.
    """
    if isinstance(assessment, dict) and assessment:
        return assessment

    for key in [
        "rn_ica",
        "rnica",
        "payload",
        "form_payload",
        "structured_payload",
        "assessment",
    ]:
        candidate = content.get(key)

        if isinstance(candidate, dict) and candidate:
            return candidate

    return content if isinstance(content, dict) else {}


def _add_rn_ica_required_field_blocker(
    compliance_blocking_items: list[dict[str, Any]],
    *,
    label: str,
    section: str,
    path: str,
) -> None:
    _add_blocker(
        compliance_blocking_items,
        section,
        label,
        path,
        f"{label} missing",
        "RN_ICA_REQUIRED",
        f"{label} is required before RN ICA finalization.",
        f"Complete {label}.",
        _navigation(
            section,
            path.split(".")[0],
            section,
            path,
            label,
            path,
            label,
        ),
        [
            "RN_ICA_FINALIZATION",
            "INITIAL_RN_ICA_TASK_COMPLETION",
            "BILLING_READINESS",
        ],
    )

def _extract_review_of_systems(
    content: dict[str, Any],
    observed: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    candidates = [
        observed.get("review_of_systems"),
        assessment.get("review_of_systems"),
        content.get("review_of_systems"),
        _obj(content.get("assessment")).get("review_of_systems"),
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    direct_ros: dict[str, Any] = {}
    search_keys = REQUIRED_FULL_ROS_SECTIONS.union(set(ROS_SECTION_ALIASES.keys()))

    for key in search_keys:
        if key in assessment and isinstance(assessment.get(key), dict):
            direct_ros[key] = assessment[key]

        if key in observed and isinstance(observed.get(key), dict):
            direct_ros[key] = observed[key]

        if key in content and isinstance(content.get(key), dict):
            direct_ros[key] = content[key]

    return direct_ros


def _extract_vitals(
    content: dict[str, Any],
    observed: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    candidates = [
        observed.get("vitals"),
        assessment.get("vitals"),
        content.get("vitals"),
        _obj(content.get("assessment")).get("vitals"),
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    return {}


def _extract_pain(
    content: dict[str, Any],
    observed: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    candidates = [
        observed.get("pain"),
        observed.get("pain_assessment"),
        assessment.get("pain"),
        assessment.get("pain_assessment"),
        content.get("pain"),
        content.get("pain_assessment"),
        _obj(content.get("assessment")).get("pain"),
        _obj(content.get("assessment")).get("pain_assessment"),
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    legacy_pain_score = assessment.get("pain_score") or content.get("pain_score")
    if legacy_pain_score is not None:
        return {
            "pain_present": True,
            "pain_score": legacy_pain_score,
            "severity": legacy_pain_score,
        }

    return {}


# =========================================================
# ROS HELPERS
# =========================================================

def _canonicalize_ros(raw_ros: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for raw_key, value in raw_ros.items():
        key = str(raw_key or "").strip().lower()
        canonical = ROS_SECTION_ALIASES.get(key, key)
        result[canonical] = value

    return result

def _ros_section_is_complete(
    section: str,
    section_data: dict[str, Any],
) -> bool:
    if not section_data:
        return False

    if _value_present(section_data.get("assessment")):
        return True

    if _value_present(section_data.get("findings")):
        return True

    if _value_present(section_data.get("narrative")):
        return True

    rules = ROS_COMPLETENESS_RULES.get(section)

    if not rules:
        return bool(section_data)

    minimum_fields = rules.get("minimum_any_fields") or []

    return _has_any_deep(
        section_data,
        minimum_fields,
    )

def _has_any_deep(data: dict[str, Any], keys: list[str]) -> bool:
    for key in keys:
        if _value_present(data.get(key)):
            return True

    for value in data.values():
        if isinstance(value, dict) and _has_any_deep(value, keys):
            return True

        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and _has_any_deep(item, keys):
                    return True

                if _value_present(item):
                    return True

    return False


def _section_label(section: str) -> str:
    rule = ROS_COMPLETENESS_RULES.get(section)
    if rule:
        return str(rule.get("label") or section)

    return str(section).replace("_", " ").title()


# =========================================================
# PERSISTENCE HELPERS
# =========================================================

def _persist_validation_result_to_note(
    note: ClinicalNote,
    warnings: list[str],
    red_flags: list[str],
    audit_flags: list[str],
    clarification_items: list[str],
    incident_required: bool,
    incident_status: str,
    incident_id: UUID | None,
    finalization_allowed: bool,
    compliance_blocking_items: list[dict[str, Any]],
    compliance_summary: dict[str, Any],
) -> None:
    content = _content(note)

    if not isinstance(content, dict):
        content = {}

    validation_payload = {
        "warnings": warnings,
        "red_flags": red_flags,
        "audit_flags": audit_flags,
        "needs_clarification": bool(clarification_items),
        "clarification_items": clarification_items,
        "incident_required": incident_required,
        "incident_status": incident_status,
        "incident_id": str(incident_id) if incident_id else None,
        "finalization_allowed": finalization_allowed,
        "compliance_blocking_items": compliance_blocking_items,
        "compliance_summary": compliance_summary,
    }

    content["_validation"] = validation_payload

    note.content = content

    _flag_json_modified(note, "content")

# =========================================================
# AUDIT LOGGING
# =========================================================

def _write_audit_log(
    db: Session,
    actor_user_id: UUID | None,
    actor_role: str,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
) -> None:
    if entity_id is None or actor_user_id is None:
        return

    try:
        with db.begin_nested():
            db.execute(
                text(
                    """
                    INSERT INTO public.audit_logs (
                        id,
                        user_id,
                        action,
                        entity_type,
                        entity_id,
                        role,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        gen_random_uuid(),
                        :user_id,
                        :action,
                        :entity_type,
                        :entity_id,
                        :role,
                        NOW(),
                        NOW()
                    )
                    """
                ),
                {
                    "user_id": actor_user_id,
                    "action": action,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "role": actor_role,
                },
            )
    except SQLAlchemyError:
        return


# =========================================================
# GENERAL HELPERS
# =========================================================

def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _merge_json_list(existing: Any, additions: list[str]) -> list[str]:
    base = existing if isinstance(existing, list) else []
    merged = list(dict.fromkeys([str(x) for x in base + additions if x]))
    return merged


def _flag_json_modified(note: ClinicalNote, attr_name: str) -> None:
    try:
        flag_modified(note, attr_name)
    except Exception:
        return


def _clean_upper(value: Any) -> str:
    return str(value or "").strip().upper()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value != 0

    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "yes",
            "y",
            "1",
            "present",
            "required",
            "positive",
        }

    return False


def _numeric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _empty(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str) and not value.strip():
        return True

    if isinstance(value, dict) and not value:
        return True

    if isinstance(value, list) and not value:
        return True

    return False


def _value_present(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, bool):
        return True

    if isinstance(value, (int, float)):
        return True

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, dict):
        return bool(value)

    if isinstance(value, list):
        return bool(value)

    return False


# =========================================================
# INCIDENT COERCION HELPERS
# =========================================================

def _coerce_report_party(data: dict[str, Any]) -> str | None:
    reported_by = str(data.get("reported_by") or "").strip().upper()

    if reported_by in {
        "PATIENT",
        "PCG",
        "SPOUSE_PARTNER",
        "CHILD",
        "RELATIVE",
        "FRIEND",
        "FACILITY_STAFF",
        "OTHER",
    }:
        return reported_by

    facility_hint = str(data.get("source") or data.get("facility_report") or "").strip().lower()
    if facility_hint:
        return "FACILITY_STAFF"

    return None


def _coerce_witness_party(data: dict[str, Any]) -> str | None:
    witnessed = str(data.get("witnessed_by") or "").strip().upper()

    if witnessed in {
        "NOT_WITNESSED",
        "STAFF",
        "PCG",
        "SPOUSE_PARTNER",
        "CHILD",
        "RELATIVE",
        "FRIEND",
        "FACILITY_STAFF",
        "OTHER",
    }:
        return witnessed

    if _truthy(data.get("unwitnessed")):
        return "NOT_WITNESSED"

    return None


def _coerce_place(observed: dict[str, Any], assessment: dict[str, Any]) -> str | None:
    place = str(
        _obj(observed.get("incident")).get("place")
        or assessment.get("place")
        or ""
    ).strip().upper()

    return place if place in {"POS", "OTHER"} else None


def _coerce_area(observed: dict[str, Any], assessment: dict[str, Any]) -> str | None:
    area = str(
        _obj(observed.get("incident")).get("area")
        or assessment.get("area")
        or ""
    ).strip().upper()

    approved = {
        "PT_ROOM_BEDROOM",
        "HALLWAY",
        "BATHROOM",
        "STEPS",
        "KITCHEN",
        "OTHER",
    }

    return area if area in approved else None


def _coerce_surface(observed: dict[str, Any], assessment: dict[str, Any]) -> str | None:
    surface = str(
        _obj(observed.get("incident")).get("surface")
        or assessment.get("surface")
        or ""
    ).strip().upper()

    approved = {
        "CARPET",
        "RUNNER",
        "THROW_AWAY_RUG",
        "SLAB",
        "WOOD",
        "OTHER",
    }

    return surface if surface in approved else None


def _coerce_medication_used(observed: dict[str, Any]) -> str | None:
    med_used = str(
        _obj(observed.get("medication_event")).get("medication_used")
        or ""
    ).strip().upper()

    approved = {
        "NONE",
        "ANALGESIC",
        "SEDATIVE",
        "OPIATE",
        "OTHER",
    }

    return med_used if med_used in approved else None


def _coerce_activity(
    observed: dict[str, Any],
    caregiver_reported: dict[str, Any],
) -> str | None:
    activity = str(
        _obj(observed.get("incident")).get("activity_at_time")
        or caregiver_reported.get("activity_at_time")
        or ""
    ).strip().upper()

    approved = {
        "REACHING_CHAIR_TO_BED",
        "REACHING_BED_TO_CHAIR",
        "AMBULATING",
        "TOILETING",
        "TRANSFERRING",
        "SITTING",
        "OTHER",
    }

    return activity if activity in approved else None


def _coerce_injury_level(
    observed: dict[str, Any],
    assessment: dict[str, Any],
) -> str | None:
    injury = _obj(observed.get("injury"))
    disposition = _obj(assessment.get("disposition"))

    if _truthy(injury.get("hospitalization_required")) or _truthy(disposition.get("hospitalization_required")):
        return "HOSPITALIZATION_REQUIRED"

    if _truthy(injury.get("fracture")) or _truthy(injury.get("laceration")) or _truthy(injury.get("skin_tear")):
        return "MODERATE_INJURY"

    if _truthy(injury.get("bruise")):
        return "MINOR_INJURY"

    if injury:
        return "NO_INJURY"

    return None


def _coerce_injury_type(observed: dict[str, Any]) -> str | None:
    injury = _obj(observed.get("injury"))
    skin = _obj(observed.get("skin"))

    if _truthy(skin.get("skin_tear")) or _truthy(injury.get("skin_tear")):
        return "SKIN_TEAR"

    if _truthy(injury.get("laceration")):
        return "LACERATION"

    if _truthy(injury.get("bruise")) or _truthy(skin.get("bruising")):
        return "BRUISE"

    if _truthy(injury.get("fracture")):
        return "FRACTURE"

    if injury:
        return "OTHER"

    return None


def _coerce_other_injury_text(observed: dict[str, Any]) -> str | None:
    injury = _obj(observed.get("injury"))
    txt = str(injury.get("other_injury_text") or "").strip()
    return txt or None


def _build_incident_narrative(
    note: ClinicalNote,
    observed: dict[str, Any],
    patient_reported: dict[str, Any],
    caregiver_reported: dict[str, Any],
) -> str:
    pieces: list[str] = []

    if caregiver_reported:
        pieces.append(f"Caregiver/facility reported: {caregiver_reported}")

    if patient_reported:
        pieces.append(f"Patient reported: {patient_reported}")

    if observed:
        incident_obs = _obj(observed.get("incident"))
        injury_obs = _obj(observed.get("injury"))
        skin_obs = _obj(observed.get("skin"))
        pieces.append(
            f"Clinician observed: incident={incident_obs}, injury={injury_obs}, skin={skin_obs}"
        )

    pieces.append(f"Generated from clinical note {note.id}")
    return " | ".join(pieces)