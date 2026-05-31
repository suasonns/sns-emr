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
    PENDING = "PENDING"        # obligation exists, not yet due or completed
    COMPLETED = "COMPLETED"    # obligation fulfilled with evidence
    OVERDUE = "OVERDUE"        # due_date passed
    ESCALATED = "ESCALATED"    # overdue beyond escalation threshold
    WAIVED = "WAIVED"          # administratively waived (never completed)


class TaskType(str, enum.Enum):
    """
    Used by: tasks.task_type
    PostgreSQL enum: tasks_task_type_enum

    IMPORTANT:
    - This enum MUST reflect the full set of values present in the database.
    - Business logic may use a subset.
    """

    # Visit-frequency driven tasks
    HUV = "HUV"
    SFV = "SFV"

    # Admission / SOC compliance (CMS CRITICAL)
    INITIAL_RN_ICA = "INITIAL_RN_ICA"
    NOE_DUE = "NOE_DUE"

    # Core compliance
    POC_UPDATE = "POC_UPDATE"
    IDG_REVIEW = "IDG_REVIEW"

    # Certification / regulatory
    CERTIFICATION = "CERTIFICATION"
    RECERTIFICATION = "RECERTIFICATION"
    F2F = "F2F"

    # POC governance / exception states (present in DB)
    POC_NONCOMPLIANT_STRUCTURE = "POC_NONCOMPLIANT_STRUCTURE"
    POC_REVIEW_REQUIRED = "POC_REVIEW_REQUIRED"
    POC_OUT_OF_SCOPE_CARE = "POC_OUT_OF_SCOPE_CARE"
    POC_STALE_REVIEW = "POC_STALE_REVIEW"
    POC_PHYSICIAN_REVIEW_REQUIRED = "POC_PHYSICIAN_REVIEW_REQUIRED"

    # Legacy / fallback
    OTHER = "OTHER"

class TaskOrigin(str, enum.Enum):
    """
    Used by: tasks.origin
    PostgreSQL enum: tasks_origin_enum

    Indicates why the task was created.
    """

    ADMISSION = "ADMISSION"    # created as part of admission workflow
    PERIODIC = "PERIODIC"      # scheduled / recurring obligation
    MANUAL = "MANUAL"          # explicitly triggered by clinical action

class TaskDiscipline(str, enum.Enum):
    """
    Used by: tasks.discipline
    PostgreSQL enum: tasks_discipline_enum

    Identifies the clinical discipline responsible.
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
    Used by: tasks.regulatory_basis
    PostgreSQL enum: tasks_regulatory_basis_enum
    """
    POC_UPDATE = "POC_UPDATE"
    IDG_REVIEW = "IDG_REVIEW"
    CERTIFICATION = "CERTIFICATION"
    RECERTIFICATION = "RECERTIFICATION"

class CompletionReferenceType(str, enum.Enum):
    """
    Used by:
    - tasks.completion_reference_type
    - tasks.completion_reference_id

    Enforces survey-defensible evidence linking.
    PostgreSQL enum: tasks_completion_ref_enum
    """
    VISIT = "VISIT"            # finalized Visit record
    NOTE = "NOTE"              # signed clinical note
    DOCUMENT = "DOCUMENT"      # formal document (IDG, POC, PDF)
    CLINICAL_NOTE = "CLINICAL_NOTE"


# =====================================================================
# BENEFIT PERIOD ENUMS
# =====================================================================

class BenefitPeriodStatus(str, enum.Enum):
    """
    Used by: benefit_periods.status
    """
    OPEN = "OPEN"
    CLOSED = "CLOSED"


# =====================================================================
# SAFETY / CARE SETTING ENUMS
# =====================================================================

class CareSettingEnum(str, enum.Enum):
    """
    Used by: safety_assessments.care_setting
    PostgreSQL enum: care_setting_enum
    """
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
    """
    Used by: safety_assessments.safety_responsibility
    PostgreSQL enum: safety_responsibility_enum

    This value is DERIVED by system logic and must never be user-editable.
    """
    HOSPICE_MANAGED = "HOSPICE_MANAGED"
    FACILITY_MANAGED = "FACILITY_MANAGED"