from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------
# Enums (API / validation layer)
# -----------------------------

class TranslationMode(StrEnum):
    OFF = "OFF"
    DETERMINISTIC = "DETERMINISTIC"
    AI = "AI"


class EligibilityDirection(StrEnum):
    RECERTIFY = "RECERTIFY"
    DISCHARGE = "DISCHARGE"
    UNDECIDED = "UNDECIDED"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class OxygenMode(StrEnum):
    CONTINUOUS = "CONTINUOUS"
    PRN = "PRN"
    UNKNOWN = "UNKNOWN"


class OxygenDevice(StrEnum):
    NASAL_CANNULA = "NASAL_CANNULA"
    MASK = "MASK"
    UNKNOWN = "UNKNOWN"


class BaselineChange(StrEnum):
    WORSE = "WORSE"
    SAME = "SAME"
    BETTER = "BETTER"
    DECREASED = "DECREASED"
    INCREASED = "INCREASED"
    UNKNOWN = "UNKNOWN"


class RNRecertStatus(StrEnum):
    DRAFT = "DRAFT"
    FINAL = "FINAL"


# -----------------------------
# Raw observation input
# -----------------------------

class BaseObservationEnvelope(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    discipline: str
    form_type: str = "RECERT"
    benefit_period_id: str
    patient_id: str
    visit_id: Optional[str] = None
    assessment_context: str = "RN_RECERT"


class RNLVNObservations(BaseModel):
    mobility_change: Optional[str] = None
    transfer_change: Optional[str] = None
    adl_notes: Optional[str] = None
    intake_change: Optional[str] = None
    weight_change_note: Optional[str] = None
    oxygen_use_note: Optional[str] = None
    dyspnea_note: Optional[str] = None
    sleep_pattern_note: Optional[str] = None
    symptom_notes: Optional[str] = None
    dme_items_reported: List[str] = Field(default_factory=list)
    current_orders_reported: List[str] = Field(default_factory=list)
    hospitalization_note: Optional[str] = None
    diagnosis_context_note: Optional[str] = None


class MSWObservations(BaseModel):
    caregiver_stress_note: Optional[str] = None
    coping_change_note: Optional[str] = None
    family_support_note: Optional[str] = None
    psychosocial_barrier_note: Optional[str] = None
    discharge_barrier_note: Optional[str] = None


class SCObservations(BaseModel):
    spiritual_distress_note: Optional[str] = None
    existential_concern_note: Optional[str] = None
    anticipatory_grief_note: Optional[str] = None
    ritual_support_note: Optional[str] = None


class CHHAObservations(BaseModel):
    bathing_assistance_note: Optional[str] = None
    transfer_assistance_note: Optional[str] = None
    feeding_assistance_note: Optional[str] = None
    observed_tolerance_note: Optional[str] = None
    dme_items_reported: List[str] = Field(default_factory=list)


class ClarificationItem(BaseModel):
    field: str
    reason: str
    question: str
    required: bool = True


# -----------------------------
# Normalized observations
# -----------------------------

class MobilityStatus(BaseModel):
    baseline_change: BaselineChange = BaselineChange.UNKNOWN
    requires_assistance: bool = False
    assist_level: str = "UNKNOWN"


class TransferStatus(BaseModel):
    baseline_change: BaselineChange = BaselineChange.UNKNOWN
    requires_assistance: bool = False


class IntakeStatus(BaseModel):
    baseline_change: BaselineChange = BaselineChange.UNKNOWN
    swallowing_issue_present: bool = False


class OxygenStatus(BaseModel):
    in_use: bool = False
    flow_lpm: Optional[float] = None
    mode: OxygenMode = OxygenMode.UNKNOWN
    device: OxygenDevice = OxygenDevice.UNKNOWN
    recent_change: str = "UNKNOWN"


class DMEStatus(BaseModel):
    items_in_use: List[str] = Field(default_factory=list)


class OrdersStatus(BaseModel):
    active_orders: List[str] = Field(default_factory=list)


class SleepPatternStatus(BaseModel):
    baseline_change: BaselineChange = BaselineChange.UNKNOWN


class HospitalizationStatus(BaseModel):
    report_present: bool = False
    count_if_known: Optional[int] = None


class NormalizedObservations(BaseModel):
    mobility_status: MobilityStatus = Field(default_factory=MobilityStatus)
    transfers: TransferStatus = Field(default_factory=TransferStatus)
    intake: IntakeStatus = Field(default_factory=IntakeStatus)
    oxygen: OxygenStatus = Field(default_factory=OxygenStatus)
    dme: DMEStatus = Field(default_factory=DMEStatus)
    orders: OrdersStatus = Field(default_factory=OrdersStatus)
    sleep_pattern: SleepPatternStatus = Field(default_factory=SleepPatternStatus)
    hospitalization: HospitalizationStatus = Field(default_factory=HospitalizationStatus)


# -----------------------------
# Translation + interpretation
# -----------------------------

class TranslationOutput(BaseModel):
    translated_narrative: List[str] = Field(default_factory=list)
    translation_mode_used: TranslationMode = TranslationMode.DETERMINISTIC
    generated_at: Optional[datetime] = None
    review_required: bool = True


class InterpretationOutput(BaseModel):
    functional_decline: bool = False
    nutritional_decline: bool = False
    clinical_decline: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    eligibility_direction: EligibilityDirection = EligibilityDirection.UNDECIDED
    missing_required_elements: List[str] = Field(default_factory=list)


class TranslationRealtimeRequest(BaseObservationEnvelope):
    observations: Dict[str, Any] = Field(default_factory=dict)


class TranslationRealtimeResponse(BaseModel):
    clarification_items: List[ClarificationItem] = Field(default_factory=list)
    normalized_observations_json: NormalizedObservations = Field(default_factory=NormalizedObservations)
    translation_output_json: TranslationOutput = Field(default_factory=TranslationOutput)
    interpretation_output_json: InterpretationOutput = Field(default_factory=InterpretationOutput)
    translation_source_map_json: Dict[str, List[str]] = Field(default_factory=dict)


# -----------------------------
# RN Recert schemas
# -----------------------------

class RNRecertDraftCreate(BaseModel):
    patient_id: str
    benefit_period_id: str
    created_by_user_id: str

    # clinical structured fields
    pps_score: Optional[int] = None
    kps_score: Optional[int] = None
    fast_stage: Optional[str] = None
    nyha_class: Optional[str] = None

    adl_level: Optional[str] = None
    adl_dependency_count: Optional[int] = None

    primary_diagnosis: Optional[str] = None
    eligibility_recommendation: EligibilityDirection = EligibilityDirection.UNDECIDED

    raw_observations_json: Dict[str, Any] = Field(default_factory=dict)
    clarification_items_json: List[Dict[str, Any]] = Field(default_factory=list)
    normalized_observations_json: Dict[str, Any] = Field(default_factory=dict)
    translation_output_json: Dict[str, Any] = Field(default_factory=dict)
    translation_source_map_json: Dict[str, Any] = Field(default_factory=dict)
    interpretation_output_json: Dict[str, Any] = Field(default_factory=dict)

    translation_mode_used: TranslationMode = TranslationMode.DETERMINISTIC


class RNRecertDraftRead(RNRecertDraftCreate):
    id: str
    status: RNRecertStatus
    created_at: datetime
    updated_at: datetime
    finalized_at: Optional[datetime] = None
    translation_reviewed_by: Optional[str] = None
    translation_reviewed_at: Optional[datetime] = None
    translation_accepted: bool = False


class RNRecertFinalizeRequest(BaseModel):
    translation_reviewed_by: str
    translation_accepted: bool = True