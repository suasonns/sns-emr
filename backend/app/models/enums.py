"""
Canonical ENUM registry for SNS Hospice EMR.

IMPORTANT:
- All enums in this file are mapped to PostgreSQL ENUM types.
- Enum values MUST remain stable once migrated.
- Changes require a forward-only Alembic migration.
- This file is intentionally dependency-free to avoid circular imports.

This design supports:
- CMS Hospice CoPs
- ACHC / CHAP / Joint Commission surveys
- Audit traceability and schema stability
"""

import enum


# =====================================================================
# TASK ENGINE ENUMS
# =====================================================================

class TaskStatus(str, enum.Enum):
    """
    Used by: tasks.status
    PostgreSQL enum: tasks_status_enum
    """
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    ESCALATED = "ESCALATED"
    WAIVED = "WAIVED"


class TaskType(str, enum.Enum):
    """
    Used by: tasks.task_type
    PostgreSQL enum: tasks_task_type_enum

    IMPORTANT:
    - This enum MUST reflect the full set of values present in the database.
    - Business logic may use a subset.
    """

    # ---------------------------------------------------------------
    # Visit-frequency driven tasks
    # ---------------------------------------------------------------
    HUV = "HUV"
    SFV = "SFV"

    # ---------------------------------------------------------------
    # Admission / SOC compliance (CMS CRITICAL)
    # ---------------------------------------------------------------
    INITIAL_RN_ICA = "INITIAL_RN_ICA"
    INITIAL_MSW_ICA = "INITIAL_MSW_ICA"
    INITIAL_SC_ICA = "INITIAL_SC_ICA"
    INITIAL_BEREAVEMENT = "INITIAL_BEREAVEMENT"
    NOE_DUE = "NOE_DUE"

    # ---------------------------------------------------------------
    # Core compliance
    # ---------------------------------------------------------------
    POC_UPDATE = "POC_UPDATE"
    IDG_REVIEW = "IDG_REVIEW"

    # ---------------------------------------------------------------
    # Certification / regulatory
    # ---------------------------------------------------------------
    CERTIFICATION = "CERTIFICATION"
    RECERTIFICATION = "RECERTIFICATION"
    F2F = "F2F"

    # ---------------------------------------------------------------
    # CONDITION ENGINE
    # ---------------------------------------------------------------
    MSW_REOFFER = "MSW_REOFFER"
    CHAPLAIN_REOFFER = "CHAPLAIN_REOFFER"
    AIDE_REOFFER = "AIDE_REOFFER"

    # ---------------------------------------------------------------
    # POC governance / exception states
    # ---------------------------------------------------------------
    POC_NONCOMPLIANT_STRUCTURE = "POC_NONCOMPLIANT_STRUCTURE"
    POC_REVIEW_REQUIRED = "POC_REVIEW_REQUIRED"
    POC_OUT_OF_SCOPE_CARE = "POC_OUT_OF_SCOPE_CARE"
    POC_STALE_REVIEW = "POC_STALE_REVIEW"
    POC_PHYSICIAN_REVIEW_REQUIRED = "POC_PHYSICIAN_REVIEW_REQUIRED"

    # ---------------------------------------------------------------
    # Legacy / fallback
    # ---------------------------------------------------------------
    OTHER = "OTHER"


class TaskOrigin(str, enum.Enum):
    """
    PostgreSQL enum: tasks_origin_enum
    """
    ADMISSION = "ADMISSION"
    PERIODIC = "PERIODIC"
    MANUAL = "MANUAL"
    SYSTEM = "SYSTEM"


class TaskDiscipline(str, enum.Enum):
    """
    PostgreSQL enum: tasks_discipline_enum
    """
    RN = "RN"
    LVN = "LVN"
    NP = "NP"
    MD = "MD"
    SW = "SW"
    CHAPLAIN = "CHAPLAIN"
    AIDE = "AIDE"


class TaskRegulatoryBasis(str, enum.Enum):
    """
    PostgreSQL enum: tasks_regulatory_basis_enum
    """
    POC_UPDATE = "POC_UPDATE"
    IDG_REVIEW = "IDG_REVIEW"
    CERTIFICATION = "CERTIFICATION"
    RECERTIFICATION = "RECERTIFICATION"
    CONDITION_TRIGGER = "CONDITION_TRIGGER"


class CompletionReferenceType(str, enum.Enum):
    """
    PostgreSQL enum: tasks_completion_ref_enum
    """
    VISIT = "VISIT"
    NOTE = "NOTE"
    DOCUMENT = "DOCUMENT"
    CLINICAL_NOTE = "CLINICAL_NOTE"


# =====================================================================
# BENEFIT PERIOD ENUMS
# =====================================================================

class BenefitPeriodStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


# =====================================================================
# SAFETY / CARE SETTING ENUMS
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