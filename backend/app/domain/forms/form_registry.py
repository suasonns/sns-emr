# app/domain/forms/form_registry.py

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.models.enums import NoteFormFamily, TaskDiscipline


# =========================================================
# VISIT HEADER
# =========================================================

VISIT_HEADER_FIELDS = [
    "created_by",
    "staff_assigned",
    "discipline",
    "care_level",
    "visit_type",
    "visit_origin",
    "visit_date",
    "time_in",
    "time_out",
    "duration",
    "form_type",
]


# =========================================================
# MODULE KEYS
# =========================================================
#
# IMPORTANT:
# These module keys must match the frontend RNICA.jsx screen/module names.
# RNICA.jsx is the source of truth for the RN Initial Comprehensive Assessment UI.
#
# form_registry.py decides which modules belong to a form.
# form_modules stores these same module_key values in the database.
# React maps these module_key values to screen components.
# =========================================================

MOD_VISIT_HEADER = "visit_header"

# RNICA admission foundation
MOD_PATIENT_DEMOGRAPHICS = "patient_demographics"
MOD_LIVING_SITUATION = "living_situation"
MOD_ADVANCED_CARE_PLANNING = "advanced_care_planning"
MOD_DIAGNOSIS_REVIEW = "diagnosis_review"

# RNICA vitals and assessment
MOD_VITALS = "vitals"
MOD_PAIN = "pain"
MOD_PERFORMANCE_STATUS = "performance_status"

# RNICA body system assessment
MOD_NEUROLOGICAL = "neurological"
MOD_CARDIOVASCULAR = "cardiovascular"
MOD_RESPIRATORY = "respiratory"
MOD_INFECTION = "infection"
MOD_GASTROINTESTINAL = "gastrointestinal"
MOD_NUTRITION = "nutrition"
MOD_MUSCULOSKELETAL = "musculoskeletal"
MOD_SKIN = "skin"

# RNICA end of life
MOD_IMMINENT_DEATH = "imminent_death"

# RNICA medications, safety, interdisciplinary
MOD_MEDICATION_REVIEW = "medication_review"
MOD_SAFETY = "safety"
MOD_SPIRITUAL = "spiritual"
MOD_BEREAVEMENT = "bereavement"
MOD_REFERRALS = "referrals"

# RNICA finalization / post-assessment review
MOD_COMPLIANCE_VALIDATION = "compliance_validation"
MOD_HOPE_DASHBOARD = "hope_dashboard"
MOD_FINALIZATION = "finalization"

# Generic clinical modules used by non-ICA visit forms
MOD_SYMPTOMS = "symptoms"
MOD_NARRATIVE = "narrative"
MOD_TEACHING = "teaching"
MOD_ISSUE_MANAGEMENT = "issue_management"
MOD_POC_UPDATE = "plan_of_care_update"

# MSW / Chaplain / Aide modules
MOD_PSYCHOSOCIAL = "psychosocial"
MOD_CARE_PROVIDED = "care_provided"

# Continuous Care
MOD_CC_ENTRY = "cc_hourly_narrative"
MOD_CC_SHIFT_SUMMARY = "cc_shift_summary"

# Death / supervisory / HOPE overlays
MOD_DEATH_VISIT = "death_visit"
MOD_SUPERVISORY = "supervisory"
MOD_HUV = "huv"
MOD_SFV = "sfv"


# =========================================================
# FORM TYPE CONSTANTS
# =========================================================

FORM_INITIAL_ICA = "INITIAL_ICA"
FORM_UPDATE_ASSESSMENT = "UPDATE_ASSESSMENT"
FORM_RECERT = "RECERT"
FORM_ROUTINE_VISIT = "ROUTINE_VISIT"
FORM_SHORT_FORM = "SHORT_FORM"
FORM_DEATH_VISIT = "DEATH_VISIT"
FORM_GIP_DAILY_ASSESSMENT = "GIP_DAILY_ASSESSMENT"
FORM_CONTINUOUS_CARE = "CONTINUOUS_CARE"
FORM_HOME_HEALTH_AIDE_VISIT = "HOME_HEALTH_AIDE_VISIT"


# =========================================================
# PRIMARY FORM KEYS
# =========================================================

PRIMARY_RN_INITIAL_ICA = "RN_INITIAL_ICA"
PRIMARY_RN_UPDATE_ASSESSMENT = "RN_UPDATE_ASSESSMENT"
PRIMARY_RN_RECERT = "RN_RECERT"
PRIMARY_RN_ROUTINE = "RN_ROUTINE"
PRIMARY_RN_SHORT_FORM = "RN_SHORT_FORM"
PRIMARY_RN_GIP_DAILY_ASSESSMENT = "RN_GIP_DAILY_ASSESSMENT"
PRIMARY_RN_DEATH_VISIT = "RN_DEATH_VISIT"

PRIMARY_LVN_ROUTINE = "LVN_ROUTINE"
PRIMARY_LVN_SHORT = "LVN_SHORT"

PRIMARY_HHA_VISIT = "HHA_VISIT"

PRIMARY_MSW_INITIAL_ICA = "MSW_INITIAL_ICA"
PRIMARY_MSW_ROUTINE = "MSW_ROUTINE"

PRIMARY_CHAPLAIN_INITIAL_ICA = "CHAPLAIN_INITIAL_ICA"
PRIMARY_CHAPLAIN_ROUTINE = "CHAPLAIN_ROUTINE"

PRIMARY_CC_HOURLY_NARRATIVE = "CC_HOURLY_NARRATIVE"


# =========================================================
# TRIGGER CONSTANTS
# =========================================================

TRIGGER_HUV1 = "HUV1"
TRIGGER_HUV2 = "HUV2"
TRIGGER_SFV = "SFV"
TRIGGER_SUPERVISORY = "SUPERVISORY"


# =========================================================
# HELPERS
# =========================================================

def _pkg(
    *,
    form_family,
    primary_form: str,
    modules: list[str],
    attached_forms: list[str] | None = None,
    is_shared_cc_form: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "form_family": form_family,
        "primary_form": primary_form,
        "modules": modules,
        "attached_forms": attached_forms or [],
        "is_shared_cc_form": is_shared_cc_form,
        "visit_header_fields": VISIT_HEADER_FIELDS,
        "metadata": metadata or {},
    }


def _value(v: Any) -> str | None:
    if v is None:
        return None

    return str(getattr(v, "value", v)).strip().upper()


# =========================================================
# NORMALIZATION
# =========================================================

DISCIPLINE_ALIASES = {
    # Nursing
    "SN": "RN",
    "NURSE": "RN",
    "REGISTERED_NURSE": "RN",
    "LPN": "LVN",
    "LICENSED_VOCATIONAL_NURSE": "LVN",

    # Aide
    "CHHA": "AIDE",
    "HHA": "AIDE",
    "HOME_HEALTH_AIDE": "AIDE",

    # Social Work
    "SW": "MSW",
    "BSW": "MSW",
    "LCSW": "MSW",
    "SOCIAL_WORK": "MSW",

    # Spiritual Care
    "SC": "CHAPLAIN",
    "SPIRITUAL": "CHAPLAIN",

    # Medical
    "DO": "MD",
}


FORM_TYPE_ALIASES = {
    # Legacy compatibility while API/resolver callers are migrated.
    "ASSESS": FORM_UPDATE_ASSESSMENT,
    "RN_ASSESS": FORM_UPDATE_ASSESSMENT,
    "COMPREHENSIVE": FORM_UPDATE_ASSESSMENT,
    "COMPREHENSIVE_ASSESSMENT": FORM_UPDATE_ASSESSMENT,
    "UPDATE": FORM_UPDATE_ASSESSMENT,
    "UPDATE_ASSESSMENT": FORM_UPDATE_ASSESSMENT,

    "ROUTINE": FORM_ROUTINE_VISIT,
    "ROUTINE_VISIT": FORM_ROUTINE_VISIT,

    "SUPERVISORY": FORM_ROUTINE_VISIT,
    "SUPV": FORM_ROUTINE_VISIT,
    "SUPV_VISIT_ONLY": FORM_ROUTINE_VISIT,

    "SHORT": FORM_SHORT_FORM,
    "SHORT_FORM": FORM_SHORT_FORM,

    "INITIAL": FORM_INITIAL_ICA,
    "ICA": FORM_INITIAL_ICA,
    "INITIAL_ICA": FORM_INITIAL_ICA,

    "RECERTIFICATION": FORM_RECERT,
    "BENEFIT_PERIOD_ASSESSMENT": FORM_RECERT,
    "RECERT": FORM_RECERT,

    "DEATH": FORM_DEATH_VISIT,
    "DEATH_VISIT": FORM_DEATH_VISIT,

    "GIP": FORM_GIP_DAILY_ASSESSMENT,
    "GIP_DAILY": FORM_GIP_DAILY_ASSESSMENT,
    "GIP_DAILY_ASSESSMENT": FORM_GIP_DAILY_ASSESSMENT,

    "CC": FORM_CONTINUOUS_CARE,
    "CONTINUOUS_CARE": FORM_CONTINUOUS_CARE,

    "HHA_VISIT": FORM_HOME_HEALTH_AIDE_VISIT,
    "HOME_HEALTH_AIDE_VISIT": FORM_HOME_HEALTH_AIDE_VISIT,
}


def normalize_discipline(v: Any) -> str | None:
    value = _value(v)

    if not value:
        return None

    return DISCIPLINE_ALIASES.get(value, value)


def normalize_form_type(v: Any) -> str | None:
    value = _value(v)

    if not value:
        return None

    return FORM_TYPE_ALIASES.get(value, value)


def normalize_event_type(v: Any) -> str | None:
    return _value(v)


def normalize_level_of_care(v: Any) -> str | None:
    return _value(v)


# =========================================================
# TASK DISCIPLINE -> FORM FAMILY
# =========================================================

TASK_DISCIPLINE_TO_FORM_FAMILY = {
    TaskDiscipline.RN: NoteFormFamily.CLINICAL,
    TaskDiscipline.LVN: NoteFormFamily.CLINICAL,
    TaskDiscipline.NP: NoteFormFamily.CLINICAL,
    TaskDiscipline.MD: NoteFormFamily.CLINICAL,

    TaskDiscipline.CHHA: NoteFormFamily.SUPPORT,

    TaskDiscipline.SW: NoteFormFamily.PSYCHOSOCIAL,
    TaskDiscipline.MSW: NoteFormFamily.PSYCHOSOCIAL,
    TaskDiscipline.BSW: NoteFormFamily.PSYCHOSOCIAL,
    TaskDiscipline.LCSW: NoteFormFamily.PSYCHOSOCIAL,

    TaskDiscipline.SC: NoteFormFamily.SPIRITUAL,
    TaskDiscipline.CHAPLAIN: NoteFormFamily.SPIRITUAL,
}


def required_form_family_for_task_discipline(discipline: Any):
    if not discipline:
        return None

    normalized = _value(discipline)

    for d, family in TASK_DISCIPLINE_TO_FORM_FAMILY.items():
        if d.value == normalized:
            return family

    return None


def note_matches_task_family(note_form_family: Any, task_discipline: Any) -> bool:
    required = required_form_family_for_task_discipline(task_discipline)

    if not required:
        return False

    return _value(note_form_family) == required.value


# =========================================================
# HOPE MAPPING FIELD GROUPS
# =========================================================
#
# These are not visible form modules.
# They tell downstream engines which CMS item groups can be derived
# from the completed clinical form.
#
# RN should not see the HOPE review during ICA documentation.
# RN sees HOPE review only after ICA finalization.
# =========================================================

HOPE_ADMIN_ITEM_CODES = [
    "A0050",
    "A0100",
    "A0215",
    "A0220",
    "A0250",
    "A0270",
    "A0500",
    "A0550",
    "A0600",
    "A0700",
    "A0810",
    "A0900",
    "A1005",
    "A1010",
    "A1110",
    "A1400",
    "A1805",
    "A1905",
    "A1910",
    "A2115",
]

HOPE_PREFERENCES_ITEM_CODES = [
    "F2000",
    "F2100",
    "F2200",
    "F3000",
]

HOPE_DIAGNOSIS_ITEM_CODES = [
    "I0010",
    "I0600",
    "I6202",
    "I8005",
]

HOPE_SYMPTOM_ITEM_CODES = [
    "J0050",
    "J0900",
    "J0905",
    "J0910",
    "J0915",
    "J2030",
    "J2040",
    "J2050",
    "J2051A",
    "J2051B",
    "J2051C",
    "J2051D",
    "J2051E",
    "J2051F",
    "J2051G",
    "J2051H",
]

HOPE_SFV_ITEM_CODES = [
    "J2052",
    "J2053",
]

HOPE_SKIN_ITEM_CODES = [
    "M1190",
    "M1195",
    "M1200",
]

HOPE_MEDICATION_ITEM_CODES = [
    "N0500",
    "N0510",
    "N0520",
]

HOPE_FINALIZATION_ITEM_CODES = [
    "Z0350",
    "Z0400",
    "Z0500",
]

HOPE_ADMISSION_ITEM_CODES = (
    HOPE_ADMIN_ITEM_CODES
    + HOPE_PREFERENCES_ITEM_CODES
    + HOPE_DIAGNOSIS_ITEM_CODES
    + HOPE_SYMPTOM_ITEM_CODES
    + HOPE_SKIN_ITEM_CODES
    + HOPE_MEDICATION_ITEM_CODES
    + HOPE_FINALIZATION_ITEM_CODES
)

HOPE_HUV_ITEM_CODES = (
    HOPE_ADMIN_ITEM_CODES
    + HOPE_DIAGNOSIS_ITEM_CODES
    + HOPE_SYMPTOM_ITEM_CODES
    + HOPE_SKIN_ITEM_CODES
    + HOPE_MEDICATION_ITEM_CODES
    + HOPE_FINALIZATION_ITEM_CODES
)


def _hope_metadata(
    *,
    enabled: bool,
    record_type: str | None,
    show_during_documentation: bool,
    review_available_after_finalization: bool,
    item_codes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "hope_enabled": enabled,
        "hope_record_type": record_type,
        "show_hope_review_during_documentation": show_during_documentation,
        "hope_review_available_after_finalization": review_available_after_finalization,
        "hope_item_codes": item_codes or [],
    }


# =========================================================
# PRIMARY FORM REGISTRY
# =========================================================
#
# This registry defines the primary form a staff member opens for a visit.
#
# HUV, SFV, and Supervisory are not standalone primary visit forms.
# They are workflow triggers / overlays.
# =========================================================

FORM_REGISTRY = {
    "RN": {
        FORM_INITIAL_ICA: _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form=PRIMARY_RN_INITIAL_ICA,
            modules=[
                MOD_PATIENT_DEMOGRAPHICS,
                MOD_LIVING_SITUATION,
                MOD_ADVANCED_CARE_PLANNING,
                MOD_DIAGNOSIS_REVIEW,
                MOD_VITALS,
                MOD_PAIN,
                MOD_PERFORMANCE_STATUS,
                MOD_NEUROLOGICAL,
                MOD_CARDIOVASCULAR,
                MOD_RESPIRATORY,
                MOD_INFECTION,
                MOD_GASTROINTESTINAL,
                MOD_NUTRITION,
                MOD_MUSCULOSKELETAL,
                MOD_SKIN,
                MOD_IMMINENT_DEATH,
                MOD_MEDICATION_REVIEW,
                MOD_SAFETY,
                MOD_SPIRITUAL,
                MOD_BEREAVEMENT,
                MOD_REFERRALS,
                MOD_COMPLIANCE_VALIDATION,
                MOD_FINALIZATION,
            ],
            attached_forms=[],
            metadata={
                "one_per_admission": True,
                "completes_task": "INITIAL_RN_ICA",
                **_hope_metadata(
                    enabled=True,
                    record_type="ADMISSION",
                    show_during_documentation=False,
                    review_available_after_finalization=True,
                    item_codes=HOPE_ADMISSION_ITEM_CODES,
                ),
            },
        ),

        FORM_UPDATE_ASSESSMENT: _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form=PRIMARY_RN_UPDATE_ASSESSMENT,
                modules=[
                    MOD_VITALS,
                    MOD_PAIN,
                    MOD_SYMPTOMS,
                    MOD_PERFORMANCE_STATUS,
                    MOD_NEUROLOGICAL,
                    MOD_CARDIOVASCULAR,
                    MOD_RESPIRATORY,
                    MOD_INFECTION,
                    MOD_GASTROINTESTINAL,
                    MOD_NUTRITION,
                    MOD_MUSCULOSKELETAL,
                    MOD_SKIN,
                    MOD_MEDICATION_REVIEW,
                    MOD_ISSUE_MANAGEMENT,
                    MOD_POC_UPDATE,
                    MOD_TEACHING,
                    MOD_NARRATIVE,
                ],
            attached_forms=[],
            metadata={
                "use_when": "new_or_worsening_problem_requires_comprehensive_reassessment",
                "supports_supervisory_overlay": True,
                "supports_huv_overlay": True,
                "supports_sfv_trigger_detection": True,
                **_hope_metadata(
                    enabled=True,
                    record_type="UPDATE",
                    show_during_documentation=False,
                    review_available_after_finalization=True,
                    item_codes=HOPE_HUV_ITEM_CODES,
                ),
            },
        ),

        FORM_RECERT: _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form=PRIMARY_RN_RECERT,
            modules=[
                MOD_VITALS,
                MOD_PAIN,
                MOD_SYMPTOMS,
                MOD_PERFORMANCE_STATUS,
                MOD_NEUROLOGICAL,
                MOD_CARDIOVASCULAR,
                MOD_RESPIRATORY,
                MOD_INFECTION,
                MOD_GASTROINTESTINAL,
                MOD_NUTRITION,
                MOD_MUSCULOSKELETAL,
                MOD_SKIN,
                MOD_MEDICATION_REVIEW,
                MOD_ISSUE_MANAGEMENT,
                MOD_POC_UPDATE,
                MOD_NARRATIVE,
            ],
            attached_forms=[],
            metadata={
                "same_as": "benefit_period_assessment",
                "supports_supervisory_overlay": True,
                "supports_sfv_trigger_detection": True,
                **_hope_metadata(
                    enabled=False,
                    record_type=None,
                    show_during_documentation=False,
                    review_available_after_finalization=False,
                    item_codes=[],
                ),
            },
        ),

        FORM_ROUTINE_VISIT: _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form=PRIMARY_RN_ROUTINE,
                modules=[
                    MOD_VITALS,
                    MOD_PAIN,
                    MOD_SYMPTOMS,
                    MOD_MEDICATION_REVIEW,
                    MOD_ISSUE_MANAGEMENT,
                    MOD_POC_UPDATE,
                    MOD_TEACHING,
                    MOD_NARRATIVE,
                ],
            attached_forms=[],
            metadata={
                "supports_supervisory_overlay": True,
                "supports_huv_overlay": True,
                "supports_sfv_trigger_detection": True,
                "supports_sfv_completion": True,
                **_hope_metadata(
                    enabled=True,
                    record_type="VISIT",
                    show_during_documentation=False,
                    review_available_after_finalization=True,
                    item_codes=HOPE_SYMPTOM_ITEM_CODES,
                ),
            },
        ),

        FORM_SHORT_FORM: _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form=PRIMARY_RN_SHORT_FORM,
            modules=[
                MOD_VITALS,
                MOD_PAIN,
                MOD_NARRATIVE,
            ],
            attached_forms=[],
            metadata={
                "use_when": "false_alarm_or_prn_no_issue",
                "supports_huv_overlay": False,
                "supports_sfv_trigger_detection": False,
                "supports_sfv_completion": False,
                **_hope_metadata(
                    enabled=False,
                    record_type=None,
                    show_during_documentation=False,
                    review_available_after_finalization=False,
                    item_codes=[],
                ),
            },
        ),

        FORM_GIP_DAILY_ASSESSMENT: _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form=PRIMARY_RN_GIP_DAILY_ASSESSMENT,
                modules=[
                    MOD_VITALS,
                    MOD_PAIN,
                    MOD_SYMPTOMS,
                    MOD_RESPIRATORY,
                    MOD_MEDICATION_REVIEW,
                    MOD_ISSUE_MANAGEMENT,
                    MOD_POC_UPDATE,
                    MOD_NARRATIVE,
                ],
            attached_forms=[],
            metadata={
                "level_of_care": "GIP",
                "supports_sfv_trigger_detection": True,
                **_hope_metadata(
                    enabled=True,
                    record_type="VISIT",
                    show_during_documentation=False,
                    review_available_after_finalization=True,
                    item_codes=HOPE_SYMPTOM_ITEM_CODES,
                ),
            },
        ),

        FORM_DEATH_VISIT: _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form=PRIMARY_RN_DEATH_VISIT,
            modules=[
                MOD_DEATH_VISIT,
                MOD_NARRATIVE,
            ],
            attached_forms=[],
            metadata={
                **_hope_metadata(
                    enabled=False,
                    record_type=None,
                    show_during_documentation=False,
                    review_available_after_finalization=False,
                    item_codes=[],
                ),
            },
        ),
    },

    "LVN": {
        FORM_ROUTINE_VISIT: _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form=PRIMARY_LVN_ROUTINE,
                modules=[
                    MOD_VITALS,
                    MOD_PAIN,
                    MOD_SYMPTOMS,
                    MOD_RESPIRATORY,
                    MOD_MEDICATION_REVIEW,
                    MOD_ISSUE_MANAGEMENT,
                    MOD_POC_UPDATE,
                    MOD_TEACHING,
                    MOD_NARRATIVE,
                ],
            attached_forms=[],
            metadata={
                "supports_sfv_trigger_detection": True,
                "supports_sfv_completion": True,
                **_hope_metadata(
                    enabled=False,
                    record_type=None,
                    show_during_documentation=False,
                    review_available_after_finalization=False,
                    item_codes=[],
                ),
            },      
        ),

        FORM_SHORT_FORM: _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form=PRIMARY_LVN_SHORT,
            modules=[
                MOD_VITALS,
                MOD_PAIN,
                MOD_NARRATIVE,
            ],
            attached_forms=[],
            metadata={
                "use_when": "false_alarm_or_prn_no_issue",
                "supports_sfv_trigger_detection": False,
                "supports_sfv_completion": False,
                **_hope_metadata(
                    enabled=False,
                    record_type=None,
                    show_during_documentation=False,
                    review_available_after_finalization=False,
                    item_codes=[],
                ),
            },
        ),
    },

    "AIDE": {
        FORM_HOME_HEALTH_AIDE_VISIT: _pkg(
            form_family=NoteFormFamily.SUPPORT,
            primary_form=PRIMARY_HHA_VISIT,
            modules=[
                MOD_CARE_PROVIDED,
                MOD_SAFETY,
                MOD_NARRATIVE,
            ],
            attached_forms=[],
            metadata={
                **_hope_metadata(
                    enabled=False,
                    record_type=None,
                    show_during_documentation=False,
                    review_available_after_finalization=False,
                    item_codes=[],
                ),
            },
        ),

        FORM_ROUTINE_VISIT: _pkg(
            form_family=NoteFormFamily.SUPPORT,
            primary_form=PRIMARY_HHA_VISIT,
            modules=[
                MOD_CARE_PROVIDED,
                MOD_SAFETY,
                MOD_NARRATIVE,
            ],
            attached_forms=[],
            metadata={
                **_hope_metadata(
                    enabled=False,
                    record_type=None,
                    show_during_documentation=False,
                    review_available_after_finalization=False,
                    item_codes=[],
                ),
            },
        ),
    },

    "MSW": {
        FORM_INITIAL_ICA: _pkg(
            form_family=NoteFormFamily.PSYCHOSOCIAL,
            primary_form=PRIMARY_MSW_INITIAL_ICA,
            modules=[
                MOD_PSYCHOSOCIAL,
                MOD_POC_UPDATE,
                MOD_NARRATIVE,
            ],
            attached_forms=[],
            metadata={
                "one_per_admission": True,
                "completes_task": "INITIAL_MSW_ICA",
            },
        ),

        FORM_ROUTINE_VISIT: _pkg(
            form_family=NoteFormFamily.PSYCHOSOCIAL,
            primary_form=PRIMARY_MSW_ROUTINE,
            modules=[
                MOD_PSYCHOSOCIAL,
                MOD_POC_UPDATE,
                MOD_NARRATIVE,
            ],
            attached_forms=[],
        ),
    },

    "CHAPLAIN": {
        FORM_INITIAL_ICA: _pkg(
            form_family=NoteFormFamily.SPIRITUAL,
            primary_form=PRIMARY_CHAPLAIN_INITIAL_ICA,
            modules=[
                MOD_SPIRITUAL,
                MOD_POC_UPDATE,
                MOD_NARRATIVE,
            ],
            attached_forms=[],
            metadata={
                "one_per_admission": True,
                "completes_task": "INITIAL_SC_ICA",
            },
        ),

        FORM_ROUTINE_VISIT: _pkg(
            form_family=NoteFormFamily.SPIRITUAL,
            primary_form=PRIMARY_CHAPLAIN_ROUTINE,
            modules=[
                MOD_SPIRITUAL,
                MOD_POC_UPDATE,
                MOD_NARRATIVE,
            ],
            attached_forms=[],
        ),
    },
}


# =========================================================
# SHARED CONTINUOUS CARE PACKAGE
# =========================================================
#
# CC is the same hourly narrative form across disciplines.
# Discipline controls who completed the form, not which CC form exists.
# =========================================================

CC_ALLOWED_DISCIPLINES = {
    "RN",
    "LVN",
    "AIDE",
    "MSW",
    "CHAPLAIN",
}


def get_cc_package(discipline: str):
    d = normalize_discipline(discipline)

    if d not in CC_ALLOWED_DISCIPLINES:
        return None

    if d in {"RN", "LVN"}:
        family = NoteFormFamily.CLINICAL
    elif d == "AIDE":
        family = NoteFormFamily.SUPPORT
    elif d == "MSW":
        family = NoteFormFamily.PSYCHOSOCIAL
    elif d == "CHAPLAIN":
        family = NoteFormFamily.SPIRITUAL
    else:
        return None

    return deepcopy(
        _pkg(
            form_family=family,
            primary_form=PRIMARY_CC_HOURLY_NARRATIVE,
                modules=[
                    MOD_CC_ENTRY,
                    MOD_CC_SHIFT_SUMMARY,
                    MOD_VITALS,
                    MOD_PAIN,
                    MOD_SYMPTOMS,
                    MOD_CARE_PROVIDED,
                    MOD_ISSUE_MANAGEMENT,
                    MOD_POC_UPDATE,
                    MOD_NARRATIVE,
                ],
            attached_forms=[],
            is_shared_cc_form=True,
            metadata={
                "shared_across_disciplines": True,
                "level_of_care": "CONTINUOUS_CARE",
                **_hope_metadata(
                    enabled=False,
                    record_type=None,
                    show_during_documentation=False,
                    review_available_after_finalization=False,
                    item_codes=[],
                ),
            },
        )
    )


# =========================================================
# WORKFLOW TRIGGERS
# =========================================================
#
# These are not primary visit forms.
# They are overlays or triggered documentation.
# =========================================================

WORKFLOW_TRIGGER_REGISTRY = {
    TRIGGER_HUV1: {
        "trigger_family": "HOPE",
        "allowed_disciplines": {"RN"},
        "modules": [MOD_HUV],
        "metadata": {
            "trigger_source": "admission_window",
            "window_start_day": 6,
            "window_end_day": 15,
            "same_visit_allowed": True,
            "must_be_separate_visit": False,
            "hope_item_codes": HOPE_HUV_ITEM_CODES,
        },
    },

    TRIGGER_HUV2: {
        "trigger_family": "HOPE",
        "allowed_disciplines": {"RN"},
        "modules": [MOD_HUV],
        "metadata": {
            "trigger_source": "admission_window",
            "window_start_day": 16,
            "window_end_day": 30,
            "same_visit_allowed": True,
            "must_be_separate_visit": False,
            "hope_item_codes": HOPE_HUV_ITEM_CODES,
        },
    },

    TRIGGER_SFV: {
        "trigger_family": "HOPE",
        "allowed_disciplines": {"RN", "LVN"},
        "modules": [MOD_SFV],
        "metadata": {
            "trigger_source": "moderate_or_severe_symptom_impact",
            "must_be_separate_visit": True,
            "same_visit_allowed": False,
            "due_within_calendar_days": 2,
            "source_items": [
                "J2051A",
                "J2051B",
                "J2051C",
                "J2051D",
                "J2051E",
                "J2051F",
                "J2051G",
                "J2051H",
            ],
            "completion_items": [
                "J2052",
                "J2053",
            ],
        },
    },

    TRIGGER_SUPERVISORY: {
        "trigger_family": "COMPLIANCE",
        "allowed_disciplines": {"RN"},
        "modules": [MOD_SUPERVISORY],
        "metadata": {
            "standalone_visit_form": False,
            "chha_due_days": 14,
            "lvn_due_days": 28,
            "valid_parent_forms": [
                PRIMARY_RN_ROUTINE,
                PRIMARY_RN_UPDATE_ASSESSMENT,
                PRIMARY_RN_RECERT,
            ],
        },
    },
}


# =========================================================
# ACCESS FUNCTIONS
# =========================================================

def get_base_form_config(*, discipline: str, form_type: str):
    d = normalize_discipline(discipline)
    f = normalize_form_type(form_type)

    if f == FORM_CONTINUOUS_CARE:
        cc_package = get_cc_package(discipline)
        if cc_package:
            return cc_package

    if d not in FORM_REGISTRY:
        raise ValueError(f"No registry for discipline: {d}")

    if f not in FORM_REGISTRY[d]:
        raise ValueError(f"No form type {f} for discipline {d}")

    return deepcopy(FORM_REGISTRY[d][f])


def get_event_form_config(*, discipline: str, event_type: str):
    return None


def get_workflow_trigger_config(trigger_key: str):
    key = _value(trigger_key)

    if not key:
        return None

    config = WORKFLOW_TRIGGER_REGISTRY.get(key)

    if not config:
        return None

    return deepcopy(config)


def trigger_allowed_for_discipline(*, trigger_key: str, discipline: str) -> bool:
    config = get_workflow_trigger_config(trigger_key)

    if not config:
        return False

    d = normalize_discipline(discipline)

    return d in config["allowed_disciplines"]


def get_supported_form_types_for_discipline(discipline: str) -> list[str]:
    d = normalize_discipline(discipline)

    if d not in FORM_REGISTRY:
        return []

    return sorted(FORM_REGISTRY[d].keys())


def get_supported_primary_forms_for_discipline(discipline: str) -> list[str]:
    d = normalize_discipline(discipline)

    if d not in FORM_REGISTRY:
        return []

    return sorted(
        pkg["primary_form"]
        for pkg in FORM_REGISTRY[d].values()
    )


def get_supported_workflow_triggers_for_discipline(discipline: str) -> list[str]:
    d = normalize_discipline(discipline)

    supported: list[str] = []

    for trigger_key, config in WORKFLOW_TRIGGER_REGISTRY.items():
        if d in config["allowed_disciplines"]:
            supported.append(trigger_key)

    return sorted(supported)


def get_all_primary_form_keys() -> set[str]:
    keys: set[str] = set()

    for discipline_registry in FORM_REGISTRY.values():
        for pkg in discipline_registry.values():
            keys.add(pkg["primary_form"])

    keys.add(PRIMARY_CC_HOURLY_NARRATIVE)

    return keys


def get_all_workflow_trigger_keys() -> set[str]:
    return set(WORKFLOW_TRIGGER_REGISTRY.keys())


def form_supports_trigger(*, primary_form: str, trigger_key: str) -> bool:
    trigger = _value(trigger_key)
    form = _value(primary_form)

    if not trigger or not form:
        return False

    if trigger == TRIGGER_SUPERVISORY:
        valid_forms = WORKFLOW_TRIGGER_REGISTRY[TRIGGER_SUPERVISORY]["metadata"][
            "valid_parent_forms"
        ]
        return form in valid_forms

    if trigger in {TRIGGER_HUV1, TRIGGER_HUV2}:
        return form in {
            PRIMARY_RN_ROUTINE,
            PRIMARY_RN_UPDATE_ASSESSMENT,
            PRIMARY_RN_RECERT,
        }

    if trigger == TRIGGER_SFV:
        return form in {
            PRIMARY_RN_ROUTINE,
            PRIMARY_RN_UPDATE_ASSESSMENT,
            PRIMARY_LVN_ROUTINE,
        }

    return False


def hope_review_available_after_finalization(*, discipline: str, form_type: str) -> bool:
    config = get_base_form_config(
        discipline=discipline,
        form_type=form_type,
    )

    metadata = config.get("metadata") or {}

    return bool(metadata.get("hope_review_available_after_finalization"))


def hope_review_visible_during_documentation(*, discipline: str, form_type: str) -> bool:
    config = get_base_form_config(
        discipline=discipline,
        form_type=form_type,
    )

    metadata = config.get("metadata") or {}

    return bool(metadata.get("show_hope_review_during_documentation"))


def get_hope_item_codes_for_form(*, discipline: str, form_type: str) -> list:
    config = get_base_form_config(
        discipline=discipline,
        form_type=form_type,
    )

    metadata = config.get("metadata") or {}

    return list(metadata.get("hope_item_codes") or [])


def get_hope_item_codes_for_trigger(trigger_key: str) -> list:
    config = get_workflow_trigger_config(trigger_key)

    if not config:
        return []

    metadata = config.get("metadata") or {}

    return list(metadata.get("hope_item_codes") or [])