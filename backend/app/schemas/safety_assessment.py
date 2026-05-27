from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.models.enums import CareSettingEnum


# =========================================================
# CREATE
# =========================================================

class SafetyAssessmentCreate(BaseModel):
    patient_id: UUID
    care_setting: CareSettingEnum
    data_json: Optional[dict] = None


# =========================================================
# UPDATE
# (care_setting intentionally excluded – immutable after sign)
# =========================================================

class SafetyAssessmentUpdate(BaseModel):
    data_json: Optional[dict] = None


# =========================================================
# READ
# =========================================================

class SafetyAssessmentRead(BaseModel):
    id: UUID
    patient_id: UUID
    care_setting: CareSettingEnum
    safety_responsibility: str
    signed_at: Optional[datetime]

    # Pydantic v2 replacement for orm_mode = True
    model_config = ConfigDict(from_attributes=True)


# =========================================================
# BUSINESS RULES (SERVICE‑LEVEL)
# =========================================================

def derive_safety_responsibility(care_setting: CareSettingEnum) -> str:
    """
    Derive safety responsibility from care setting.

    HOME -> HOSPICE_MANAGED
    ALL OTHERS -> FACILITY_MANAGED
    """
    if care_setting == CareSettingEnum.HOME:
        return "HOSPICE_MANAGED"
    return "FACILITY_MANAGED"


def validate_care_setting_change(
    existing_record,
    incoming_care_setting: CareSettingEnum,
) -> None:
    """
    Prevent care setting changes after signing.

    Hard compliance rule.
    """
    if existing_record.signed_at is not None:
        raise ValueError("Care setting cannot be changed after signing")
