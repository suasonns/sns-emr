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

    ORDER_MD_APPROVAL = "ORDER_MD_APPROVAL"
    IDG_DEFERRED_MD_REVIEW = "IDG_DEFERRED_MD_REVIEW"

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

    PHYSICIAN_ORDER = "PHYSICIAN_ORDER"
    IDG_PATIENT_REVIEW = "IDG_PATIENT_REVIEW"

    CERTIFICATION = "CERTIFICATION"
    RECERTIFICATION = "RECERTIFICATION"


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

    SC = "SC"
    CHAPLAIN = "CHAPLAIN"

    AIDE = "AIDE"


# ==========================================================
# ✅ DISCIPLINE NORMALIZATION
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
# ✅ VISIT ENUMS (FIXED + ENTERPRISE SAFE)
# ==========================================================

class VisitEventType(str, enum.Enum):
    SOC = "SOC"
    CHANGE_OF_CONDITION = "CHANGE_OF_CONDITION"
    NEW_ORDER = "NEW_ORDER"
    RECERT = "RECERT"
    UPDATE_ASSESSMENT = "UPDATE_ASSESSMENT"


class VisitFormType(str, enum.Enum):
    ASSESS = "ASSESS"
    ROUTINE_VISIT = "ROUTINE_VISIT"
    SHORT_FORM = "SHORT_FORM"
    PRE_ADMIT_EVAL = "PRE_ADMIT_EVAL"
    AFTER_DEATH = "AFTER_DEATH"
    ON_CALL_TRIAGE = "ON_CALL_TRIAGE"
    MISSED_VISIT = "MISSED_VISIT"
    DECLINED_VISIT = "DECLINED_VISIT"

class ServiceContext(str, enum.Enum):
    ADMISSION_RN_ICA = "ADMISSION_RN_ICA"
    ROUTINE_VISIT = "ROUTINE_VISIT"
    PRN_VISIT = "PRN_VISIT"
    RECERTIFICATION = "RECERTIFICATION"
    FACE_TO_FACE = "FACE_TO_FACE"
    IDG_REVIEW = "IDG_REVIEW"
    BEREAVEMENT = "BEREAVEMENT"
    VOLUNTEER_VISIT = "VOLUNTEER_VISIT"
    DISCHARGE = "DISCHARGE"
    TRANSFER = "TRANSFER"
    REVOCATION = "REVOCATION"

class NoteFormFamily(str, enum.Enum):
    CLINICAL = "CLINICAL"
    PSYCHOSOCIAL = "PSYCHOSOCIAL"
    SPIRITUAL = "SPIRITUAL"
    MEDICAL = "MEDICAL"
    SUPPORT = "SUPPORT"
    ADMIN = "ADMIN"


# ==========================================================
# DIAGNOSIS ENUMS (POSTGRESQL-BACKED — MUST MATCH DB)
# ==========================================================

class DiagnosisType(str, enum.Enum):
    """
    Classification of a patient diagnosis.

    Governance:
    - PRIMARY: official or proposed terminal/hospice primary diagnosis.
    - SECONDARY: supporting diagnosis related to the hospice clinical picture.
    - COMORBIDITY: active medical condition relevant to care, coverage,
      medication relatedness, or IDG/POC planning.
    """

    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    COMORBIDITY = "COMORBIDITY"


class DiagnosisStatus(str, enum.Enum):
    """
    Lifecycle state of a diagnosis.

    PROPOSED:
        Entered from referral/intake or suggested by RN/MD review but not yet
        accepted as the official active diagnosis.

    ACTIVE:
        Current accepted diagnosis.

    REJECTED:
        Not accepted by Medical Director or clinical review.

    HISTORICAL:
        Previously active or previously proposed diagnosis retained for audit.
    """

    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    HISTORICAL = "HISTORICAL"


class DiagnosisSource(str, enum.Enum):
    """
    Source workflow or authority that produced the diagnosis.

    REFERRAL:
        Diagnosis from referral packet, hospital record, facility record,
        family report, or intake entry.

    RN_ICA:
        Diagnosis reviewed or entered during RN Initial Comprehensive Assessment.

    SPECIALIST:
        Diagnosis recommended/documented by treating specialist.

    ATTENDING_PHYSICIAN:
        Diagnosis from attending physician.

    MEDICAL_DIRECTOR:
        Diagnosis accepted/changed by hospice Medical Director.

    CTI:
        Diagnosis used in Certification of Terminal Illness.

    RECERT:
        Diagnosis used or updated during recertification.

    MD:
        Generic physician source retained for compatibility.
    """

    REFERRAL = "REFERRAL"
    RN_ICA = "RN_ICA"
    SPECIALIST = "SPECIALIST"
    ATTENDING_PHYSICIAN = "ATTENDING_PHYSICIAN"
    MEDICAL_DIRECTOR = "MEDICAL_DIRECTOR"
    CTI = "CTI"
    RECERT = "RECERT"
    MD = "MD"


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
    "VisitEventType",
    "VisitFormType",
    "NoteFormFamily",
    "DiagnosisType",
    "DiagnosisStatus",
    "DiagnosisSource",
    "CORE_DISCIPLINES",
    "normalize_discipline",
]