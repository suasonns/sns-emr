"""
Canonical ENUM registry for SNS Hospice EMR.

CRITICAL RULES:
- PostgreSQL-backed enums MUST match DB exactly
- NEVER change enum values without a forward-only migration
- Do NOT remove enum values used in historical records
- This file is dependency-free by design

COMPLIANCE COVERAGE:
- CMS Hospice Conditions of Participation (CoPs)
- ACHC / CHAP / CDPH / Joint Commission
- Audit traceability + lifecycle enforcement
"""

from __future__ import annotations

import enum


# =====================================================================
# TASK ENGINE ENUMS (POSTGRESQL-BACKED — MUST MATCH DB EXACTLY)
# =====================================================================

class TaskStatus(str, enum.Enum):
    """
    Canonical task lifecycle.

    IMPORTANT:
    - Must match PostgreSQL enum exactly
    - Used for workflow, SLA, and audit validation
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    ESCALATED = "ESCALATED"
    WAIVED = "WAIVED"


class TaskType(str, enum.Enum):
    """
    Clinical + regulatory task taxonomy.
    """

    # VISIT TYPES
    HUV = "HUV"
    SFV = "SFV"

    # INITIAL ASSESSMENTS
    INITIAL_RN_ICA = "INITIAL_RN_ICA"
    INITIAL_MSW_ICA = "INITIAL_MSW_ICA"
    INITIAL_SC_ICA = "INITIAL_SC_ICA"
    INITIAL_BEREAVEMENT = "INITIAL_BEREAVEMENT"
    NOE_DUE = "NOE_DUE"

    # PLAN OF CARE
    POC_UPDATE = "POC_UPDATE"
    IDG_REVIEW = "IDG_REVIEW"

    # CERTIFICATION
    CERTIFICATION = "CERTIFICATION"
    RECERTIFICATION = "RECERTIFICATION"
    F2F = "F2F"

    # RE-OFFERS
    MSW_REOFFER = "MSW_REOFFER"
    CHAPLAIN_REOFFER = "CHAPLAIN_REOFFER"
    AIDE_REOFFER = "AIDE_REOFFER"

    # POC VALIDATION
    POC_NONCOMPLIANT_STRUCTURE = "POC_NONCOMPLIANT_STRUCTURE"
    POC_REVIEW_REQUIRED = "POC_REVIEW_REQUIRED"
    POC_OUT_OF_SCOPE_CARE = "POC_OUT_OF_SCOPE_CARE"
    POC_STALE_REVIEW = "POC_STALE_REVIEW"
    POC_PHYSICIAN_REVIEW_REQUIRED = "POC_PHYSICIAN_REVIEW_REQUIRED"

    # CLINICAL REVIEW
    CLINICAL_REVIEW_REQUIRED = "CLINICAL_REVIEW_REQUIRED"
    CLINICAL_FOLLOWUP = "CLINICAL_FOLLOWUP"

    OTHER = "OTHER"


class TaskOrigin(str, enum.Enum):
    """
    Source of task creation.
    """

    ADMISSION = "ADMISSION"
    PERIODIC = "PERIODIC"
    MANUAL = "MANUAL"
    SYSTEM = "SYSTEM"


class TaskRegulatoryBasis(str, enum.Enum):
    """
    Regulatory driver for the task.
    """

    POC_UPDATE = "POC_UPDATE"
    IDG_REVIEW = "IDG_REVIEW"
    CERTIFICATION = "CERTIFICATION"
    RECERTIFICATION = "RECERTIFICATION"
    CONDITION_TRIGGER = "CONDITION_TRIGGER"


class CompletionReferenceType(str, enum.Enum):
    """
    Evidence linkage for COMPLETED tasks.

    IMPORTANT:
    - Only valid when TaskStatus == COMPLETED
    - Must reference real clinical artifacts
    """

    VISIT = "VISIT"
    NOTE = "NOTE"
    DOCUMENT = "DOCUMENT"

    CLINICAL_NOTE = "CLINICAL_NOTE"
    PSYCHOSOCIAL_NOTE = "PSYCHOSOCIAL_NOTE"
    SPIRITUAL_NOTE = "SPIRITUAL_NOTE"


# =====================================================================
# TASK DISCIPLINE (POSTGRESQL ENUM — MUST MATCH DB EXACTLY)
# =====================================================================

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


# =====================================================================
# MASTER DISCIPLINE ENUM (APP-LEVEL)
# =====================================================================

class Discipline(str, enum.Enum):
    # MEDICAL
    MD = "MD"
    DO = "DO"
    MEDICAL_DIRECTOR = "MEDICAL_DIRECTOR"
    ATTENDING_PHYSICIAN = "ATTENDING_PHYSICIAN"
    NP = "NP"
    PA = "PA"

    # NURSING
    RN = "RN"
    LVN = "LVN"
    LPN = "LPN"

    # AIDE
    CHHA = "CHHA"
    AIDE = "AIDE"

    # IDG CORE
    SW = "SW"
    MSW = "MSW"
    BSW = "BSW"
    LCSW = "LCSW"
    SC = "SC"
    CHAPLAIN = "CHAPLAIN"

    BEREAVEMENT_COORDINATOR = "BEREAVEMENT_COORDINATOR"

    # SUPPORT
    PHARMACIST = "PHARMACIST"
    DIETITIAN = "DIETITIAN"
    RESPIRATORY_THERAPIST = "RESPIRATORY_THERAPIST"

    # MANAGEMENT
    ADMIN = "ADMIN"
    EXECUTIVE_DIRECTOR = "EXECUTIVE_DIRECTOR"
    ADMINISTRATOR = "ADMINISTRATOR"
    DIRECTOR = "DIRECTOR"
    CLINICAL_DIRECTOR = "CLINICAL_DIRECTOR"
    DPCS = "DPCS"

    # OPERATIONS
    INTAKE = "INTAKE"
    CASE_MANAGER = "CASE_MANAGER"

    # REGULATORY
    SURVEYOR = "SURVEYOR"
    CONSULTANT = "CONSULTANT"

    # VOLUNTEER
    VOLUNTEER_COORDINATOR = "VOLUNTEER_COORDINATOR"
    VOLUNTEER = "VOLUNTEER"

    # SUPPORT STAFF
    DRIVER = "DRIVER"
    INTERPRETER = "INTERPRETER"
    HOUSEKEEPER = "HOUSEKEEPER"


# =====================================================================
# BENEFIT PERIOD
# =====================================================================

class BenefitPeriodStatus(str, enum.Enum):
    """
    LEGACY COMPATIBILITY:
    OPEN mapped to PENDING.

    DO NOT use OPEN in new logic.
    """

    OPEN = "PENDING"
    CLOSED = "CLOSED"

# =====================================================================
# CARE SETTINGS
# =====================================================================

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


# =====================================================================
# FORM ENGINE (APP LEVEL TEXT)
# =====================================================================

class VisitFormType(str, enum.Enum):
    AFTER_DEATH = "AFTER_DEATH"
    AFTER_HOURS = "AFTER_HOURS"
    ANCILLARY_SUPPORT = "ANCILLARY_SUPPORT"
    ASSESS = "ASSESS"
    BEREAVEMENT_VISIT = "BEREAVEMENT_VISIT"
    DEATH_VISIT = "DEATH_VISIT"
    DECLINED_VISIT = "DECLINED_VISIT"
    MISSED_VISIT = "MISSED_VISIT"
    OFFICE_HOURS = "OFFICE_HOURS"
    ON_CALL_TRIAGE = "ON_CALL_TRIAGE"
    RESPITE_RELIEF = "RESPITE_RELIEF"
    ROUTINE_VISIT = "ROUTINE_VISIT"
    SHORT_FORM = "SHORT_FORM"
    SUPV_VISIT_ONLY = "SUPV_VISIT_ONLY"
    VOLUNTEER_SUPPORT = "VOLUNTEER_SUPPORT"
    WEEKENDS = "WEEKENDS"
    PRE_ADMIT_EVAL = "PRE_ADMIT_EVAL"


class NoteFormFamily(str, enum.Enum):
    CLINICAL = "CLINICAL"
    PSYCHOSOCIAL = "PSYCHOSOCIAL"
    SPIRITUAL = "SPIRITUAL"
    MEDICAL = "MEDICAL"
    SUPPORT = "SUPPORT"
    ADMIN = "ADMIN"
