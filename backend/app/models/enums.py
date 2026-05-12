import enum


# ---------------------------------------------------------------------
# TASK STATUS
# ---------------------------------------------------------------------
# Used by tasks.status (PostgreSQL enum: tasks_status_enum)
# Must remain stable for audit and survey defensibility.
class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"        # obligation exists, not yet due or completed
    COMPLETED = "COMPLETED"    # obligation fulfilled with evidence
    OVERDUE = "OVERDUE"        # due_date passed
    ESCALATED = "ESCALATED"    # overdue beyond escalation threshold
    WAIVED = "WAIVED"          # administratively waived (never completed)


# ---------------------------------------------------------------------
# TASK TYPE
# ---------------------------------------------------------------------
# Used by tasks.task_type (PostgreSQL enum: tasks_task_type_enum)
class TaskType(str, enum.Enum):
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

    # Catch‑all / legacy
    OTHER = "OTHER"


# ---------------------------------------------------------------------
# COMPLETION REFERENCE TYPE
# ---------------------------------------------------------------------
# Used by:
#   tasks.completion_reference_type
#   tasks.completion_reference_id
#
# Enforces survey‑defensible evidence linking.
class CompletionReferenceType(str, enum.Enum):
    VISIT = "VISIT"            # finalized Visit record
    NOTE = "NOTE"              # signed clinical note
    DOCUMENT = "DOCUMENT"      # formal document (IDG, POC, PDF)
    CLINICAL_NOTE = "CLINICAL_NOTE"


# ---------------------------------------------------------------------
# BENEFIT PERIOD STATUS
# ---------------------------------------------------------------------
# Used by:
#   benefit_periods.status
#
# Required for:
# - visit attribution
# - task anchoring
# - survey traceability
class BenefitPeriodStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"