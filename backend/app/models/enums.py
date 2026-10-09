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
    VOLUNTEER_REOFFER = "VOLUNTEER_REOFFER"

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

    VOLUNTEER = "VOLUNTEER"


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
    # Additional Visit Notes form types (RN/LVN "Add New Visit" workflow) —
    # minimal-content visit types that collapse the documentation body down
    # to just a Narrative (plus a couple of contextual fields).
    AFTER_HOURS = "AFTER_HOURS"
    OFFICE_HOURS = "OFFICE_HOURS"
    ANCILLARY_SUPPORT = "ANCILLARY_SUPPORT"
    BEREAVEMENT_VISIT = "BEREAVEMENT_VISIT"
    DEATH_VISIT = "DEATH_VISIT"
    RESPITE_RELIEF = "RESPITE_RELIEF"
    SUPV_VISIT_ONLY = "SUPV_VISIT_ONLY"
    VOLUNTEER_SUPPORT = "VOLUNTEER_SUPPORT"
    WEEKENDS = "WEEKENDS"

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
# INTERDISCIPLINARY CONTINUITY (MSW / CHAPLAIN / VOLUNTEER)
#
# Owner-authorized continuity workflow (Authorized Continuity Workflow
# Implementation directive). Scope is exactly MSW, CHAPLAIN, VOLUNTEER --
# RN/MD/F2F/Hospice-Aide refusal pathways are explicitly out of scope and
# continue to use app.models.refusal.Refusal / app.services.refusal_engine
# unchanged. These enums back app.models.discipline_service and
# app.models.idg_recommendation and app.models.patient_issue's additive
# columns -- never reuse these values for the legacy refusals table.
# ==========================================================

class ContinuityDiscipline(str, enum.Enum):
    """Canonical disciplines for the continuity workflow ONLY. Normalize
    MSW/SW/SOCIAL_WORK/SOCIAL_WORKER/LCSW -> MSW; SPIRITUAL_COUNSELOR*/SC/
    CHAPLAIN/PASTORAL_COUNSELOR -> CHAPLAIN (never two active service
    records for Chaplain and Spiritual Counselor); VOLUNTEER* -> VOLUNTEER.
    See app.services.discipline_service_engine.normalize_continuity_discipline."""

    MSW = "MSW"
    CHAPLAIN = "CHAPLAIN"
    VOLUNTEER = "VOLUNTEER"


class DisciplineServiceState(str, enum.Enum):
    """Current-state projection values for patient_discipline_services.
    No generic RESOLVED state -- every terminal/paused condition is explicit."""

    NOT_YET_OFFERED = "NOT_YET_OFFERED"
    OFFER_DUE = "OFFER_DUE"
    OFFERED_AWAITING_DECISION = "OFFERED_AWAITING_DECISION"
    ACCEPTED_AWAITING_ACTIVATION = "ACCEPTED_AWAITING_ACTIVATION"
    ACTIVE = "ACTIVE"
    REFUSED_MONITORING_CONTINUES = "REFUSED_MONITORING_CONTINUES"
    REOFFER_DUE = "REOFFER_DUE"
    REOFFERED_AWAITING_DECISION = "REOFFERED_AWAITING_DECISION"
    PAUSED = "PAUSED"
    ENDED = "ENDED"
    UNABLE_TO_CONTACT = "UNABLE_TO_CONTACT"
    DECISION_MAKER_UNAVAILABLE = "DECISION_MAKER_UNAVAILABLE"


class DisciplineServiceEventType(str, enum.Enum):
    """Append-only event types for patient_discipline_service_events.
    Events are never deleted or rewritten; corrections are recorded as new
    CORRECTION_RECORDED events referencing the event they correct."""

    DISCIPLINE_IDENTIFIED = "DISCIPLINE_IDENTIFIED"
    SERVICE_OFFERED = "SERVICE_OFFERED"
    DECISION_PENDING = "DECISION_PENDING"
    SERVICE_ACCEPTED = "SERVICE_ACCEPTED"
    SERVICE_REFUSED = "SERVICE_REFUSED"
    SERVICE_ACTIVATED = "SERVICE_ACTIVATED"
    SERVICE_PAUSED = "SERVICE_PAUSED"
    SERVICE_RESUMED = "SERVICE_RESUMED"
    SERVICE_ENDED = "SERVICE_ENDED"
    REFUSAL_WITHDRAWN = "REFUSAL_WITHDRAWN"
    REOFFER_SCHEDULED = "REOFFER_SCHEDULED"
    SERVICE_REOFFERED = "SERVICE_REOFFERED"
    REOFFER_ACCEPTED = "REOFFER_ACCEPTED"
    REOFFER_REFUSED = "REOFFER_REFUSED"
    UNABLE_TO_CONTACT = "UNABLE_TO_CONTACT"
    DECISION_MAKER_UNAVAILABLE = "DECISION_MAKER_UNAVAILABLE"
    IDG_REVIEW_REQUESTED = "IDG_REVIEW_REQUESTED"
    IDG_REVIEW_COMPLETED = "IDG_REVIEW_COMPLETED"
    DISCIPLINE_RECOMMENDATION_ADDED = "DISCIPLINE_RECOMMENDATION_ADDED"
    RN_MONITORING_ASSIGNED = "RN_MONITORING_ASSIGNED"
    RN_MONITORING_CHANGED = "RN_MONITORING_CHANGED"
    RN_MONITORING_ENDED = "RN_MONITORING_ENDED"
    CORRECTION_RECORDED = "CORRECTION_RECORDED"


class IDGRecommendationType(str, enum.Enum):
    CONTINUE_MONITORING = "CONTINUE_MONITORING"
    PROVIDE_EDUCATION = "PROVIDE_EDUCATION"
    REOFFER_SERVICE = "REOFFER_SERVICE"
    REQUEST_ASSESSMENT = "REQUEST_ASSESSMENT"
    REVIEW_POC = "REVIEW_POC"
    REQUEST_INFORMATION = "REQUEST_INFORMATION"
    ESCALATE_CONCERN = "ESCALATE_CONCERN"


class IDGRecommendationStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    SUPERSEDED = "SUPERSEDED"


class PatientIssueDomain(str, enum.Enum):
    """Values for PatientIssue.issue_domain (additive column)."""

    PSYCHOSOCIAL = "PSYCHOSOCIAL"
    EMOTIONAL = "EMOTIONAL"
    CAREGIVER = "CAREGIVER"
    FAMILY_SYSTEM = "FAMILY_SYSTEM"
    SPIRITUAL = "SPIRITUAL"
    BEREAVEMENT = "BEREAVEMENT"
    SOCIAL_RESOURCE = "SOCIAL_RESOURCE"
    FINANCIAL = "FINANCIAL"
    SAFETY = "SAFETY"


class PatientIssueClinicalStatus(str, enum.Enum):
    """Values for PatientIssue.clinical_status (additive column). Distinct
    from the existing free-text `status` (OPEN/RESOLVED) column, which is
    unchanged and still authoritative for existing callers."""

    IDENTIFIED = "IDENTIFIED"
    ACTIVE = "ACTIVE"
    MONITORING = "MONITORING"
    STABLE = "STABLE"
    IMPROVING = "IMPROVING"
    WORSENING = "WORSENING"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED_IN_ERROR = "CLOSED_IN_ERROR"


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
    "ContinuityDiscipline",
    "DisciplineServiceState",
    "DisciplineServiceEventType",
    "IDGRecommendationType",
    "IDGRecommendationStatus",
    "PatientIssueDomain",
    "PatientIssueClinicalStatus",
]