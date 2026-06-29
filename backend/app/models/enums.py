"""
Canonical ENUM registry for SNS Hospice EMR.

CRITICAL RULES:
- PostgreSQL-backed enums MUST match DB exactly
- NEVER change enum values without a forward-only migration
- Do NOT remove enum values used in historical records
- This file is dependency-free by design
"""

from __future__ import annotations

import enum


# ==========================================================
# ✅ CANONICAL CORE DISCIPLINE STANDARD (SYSTEM-WIDE)
# ==========================================================

CORE_DISCIPLINES = ["RN", "MD", "MSW", "SC"]

"""
RULE:
- These are the ONLY disciplines used for:
  ✅ IDG completeness
  ✅ signature validation
  ✅ task routing
  ✅ compliance logic
"""


# ==========================================================
# TASK ENGINE ENUMS (POSTGRESQL-BACKED — MUST MATCH DB)
# ==========================================================

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    ESCALATED = "ESCALATED"
    WAIVED = "WAIVED"


class TaskType(str, enum.Enum):

    HUV1 = "HUV1"
    HUV2 = "HUV2"
    SFV = "SFV"
    HUV = "HUV"

    INITIAL_RN_ICA = "INITIAL_RN_ICA"
    INITIAL_MSW_ICA = "INITIAL_MSW_ICA"
    INITIAL_SC_ICA = "INITIAL_SC_ICA"
    INITIAL_BEREAVEMENT = "INITIAL_BEREAVEMENT"
    NOE_DUE = "NOE_DUE"

    POC_UPDATE = "POC_UPDATE"
    IDG_REVIEW = "IDG_REVIEW"

    CERTIFICATION = "CERTIFICATION"
    RECERTIFICATION = "RECERTIFICATION"
    F2F = "F2F"

    MSW_REOFFER = "MSW_REOFFER"
    CHAPLAIN_REOFFER = "CHAPLAIN_REOFFER"
    AIDE_REOFFER = "AIDE_REOFFER"

    POC_NONCOMPLIANT_STRUCTURE = "POC_NONCOMPLIANT_STRUCTURE"
    POC_REVIEW_REQUIRED = "POC_REVIEW_REQUIRED"
    POC_OUT_OF_SCOPE_CARE = "POC_OUT_OF_SCOPE_CARE"
    POC_STALE_REVIEW = "POC_STALE_REVIEW"
    POC_PHYSICIAN_REVIEW_REQUIRED = "POC_PHYSICIAN_REVIEW_REQUIRED"

    CLINICAL_REVIEW_REQUIRED = "CLINICAL_REVIEW_REQUIRED"
    CLINICAL_FOLLOWUP = "CLINICAL_FOLLOWUP"

    OTHER = "OTHER"


# ==========================================================
# TASK METADATA ENUMS
# ==========================================================

class TaskOrigin(str, enum.Enum):
    ADMISSION = "ADMISSION"
    PERIODIC = "PERIODIC"
    MANUAL = "MANUAL"
    SYSTEM = "SYSTEM"


class TaskRegulatoryBasis(str, enum.Enum):
    POC_UPDATE = "POC_UPDATE"
    IDG_REVIEW = "IDG_REVIEW"
    CERTIFICATION = "CERTIFICATION"
    RECERTIFICATION = "RECERTIFICATION"
    CONDITION_TRIGGER = "CONDITION_TRIGGER"


class CompletionReferenceType(str, enum.Enum):
    VISIT = "VISIT"
    NOTE = "NOTE"
    DOCUMENT = "DOCUMENT"

    CLINICAL_NOTE = "CLINICAL_NOTE"
    PSYCHOSOCIAL_NOTE = "PSYCHOSOCIAL_NOTE"
    SPIRITUAL_NOTE = "SPIRITUAL_NOTE"


# ==========================================================
# ✅ TASK DISCIPLINE (DB-STABLE)
# ==========================================================

class TaskDiscipline(str, enum.Enum):
    RN = "RN"
    LVN = "LVN"
    NP = "NP"
    MD = "MD"
    CHHA = "CHHA"

    SW = "SW"
    MSW = "MSW"
    BSW = "BSW"
    LCSW = "LCSW"

    # ✅ SPIRITUAL CARE (CANONICAL)
    SC = "SC"

    # ✅ LEGACY / DISPLAY ONLY
    CHAPLAIN = "CHAPLAIN"

    AIDE = "AIDE"


# ==========================================================
# ✅ DISCIPLINE NORMALIZATION (CRITICAL)
# ==========================================================

DISCIPLINE_NORMALIZATION_MAP = {
    "RN": "RN",
    "LVN": "RN",
    "LPN": "RN",

    "MD": "MD",
    "DO": "MD",
    "NP": "MD",
    "PA": "MD",

    "SW": "MSW",
    "MSW": "MSW",
    "BSW": "MSW",
    "LCSW": "MSW",

    "SC": "SC",
    "CHAPLAIN": "SC",
}


def normalize_discipline(value: str) -> str:
    """
    Converts any discipline into core discipline.

    REQUIRED for:
    ✅ IDG validation
    ✅ task assignment
    ✅ signature matching
    """
    return DISCIPLINE_NORMALIZATION_MAP.get(value, value)


# ==========================================================
# MASTER DISCIPLINE ENUM
# ==========================================================

class Discipline(str, enum.Enum):

    MD = "MD"
    DO = "DO"
    MEDICAL_DIRECTOR = "MEDICAL_DIRECTOR"
    ATTENDING_PHYSICIAN = "ATTENDING_PHYSICIAN"
    NP = "NP"
    PA = "PA"

    RN = "RN"
    LVN = "LVN"
    LPN = "LPN"

    CHHA = "CHHA"
    AIDE = "AIDE"

    SW = "SW"
    MSW = "MSW"
    BSW = "BSW"
    LCSW = "LCSW"

    SC = "SC"
    CHAPLAIN = "CHAPLAIN"

    ADMIN = "ADMIN"
    CASE_MANAGER = "CASE_MANAGER"


# ==========================================================
# CARE SETTINGS
# ==========================================================

class CareSettingEnum(str, enum.Enum):
    HOME = "HOME"
    ALF = "ALF"
    BOARD_AND_CARE = "BOARD_AND_CARE"
    SNF = "SNF"
    HOSPITAL = "HOSPITAL"
    INPATIENT_HOSPICE = "INPATIENT_HOSPICE"
    RESIDENTIAL_CARE_FACILITY = "RESIDENTIAL_CARE_FACILITY"
    CORRECTIONAL_FACILITY = "CORRECTIONAL_FACILITY"
    HOMELESS_SHELTER = "HOMELESS_SHELTER"
    TEMPORARY_RELOCATION = "TEMPORARY_RELOCATION"
    OTHER = "OTHER"


class SafetyResponsibilityEnum(str, enum.Enum):
    HOSPICE_MANAGED = "HOSPICE_MANAGED"
    FACILITY_MANAGED = "FACILITY_MANAGED"


# ==========================================================
# VISIT FORMS
# ==========================================================

class VisitFormType(str, enum.Enum):
    ASSESS = "ASSESS"
    ROUTINE_VISIT = "ROUTINE_VISIT"
    SHORT_FORM = "SHORT_FORM"
    PRE_ADMIT_EVAL = "PRE_ADMIT_EVAL"
    AFTER_DEATH = "AFTER_DEATH"
    ON_CALL_TRIAGE = "ON_CALL_TRIAGE"
    MISSED_VISIT = "MISSED_VISIT"
    DECLINED_VISIT = "DECLINED_VISIT"


class NoteFormFamily(str, enum.Enum):
    CLINICAL = "CLINICAL"
    PSYCHOSOCIAL = "PSYCHOSOCIAL"
    SPIRITUAL = "SPIRITUAL"
    MEDICAL = "MEDICAL"
    SUPPORT = "SUPPORT"
    ADMIN = "ADMIN"


# ==========================================================
# EXPORTS
# ==========================================================

__all__ = [
    "TaskStatus",
    "TaskType",
    "TaskOrigin",
    "TaskRegulatoryBasis",
    "CompletionReferenceType",
    "TaskDiscipline",
    "Discipline",
    "CareSettingEnum",
    "SafetyResponsibilityEnum",
    "VisitFormType",
    "NoteFormFamily",
    "CORE_DISCIPLINES",
    "normalize_discipline",
]