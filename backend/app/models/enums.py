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
    """

    # Visit-frequency driven tasks
    HUV = "HUV"                # High Utilization Visit
    SFV = "SFV"                # Standard Frequency Visit

    # Core compliance tasks
    POC_UPDATE = "POC_UPDATE"  # Plan of Care update
    IDG_REVIEW = "IDG_REVIEW"  # Interdisciplinary Group review

    # Certification / regulatory
    CERTIFICATION = "CERTIFICATION"
    RECERTIFICATION = "RECERTIFICATION"
    F2F = "F2F"                # Face-to-Face encounter

    # Catch-all / legacy
    OTHER = "OTHER"


class CompletionReferenceType(str, enum.Enum):
    """
    Used by:
    - tasks.completion_reference_type
    - tasks.completion_reference_id

    Enforces survey-defensible evidence linking.
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