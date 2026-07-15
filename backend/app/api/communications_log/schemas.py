import json
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict,
)


class CommunicationsLogCreate(BaseModel):
    patient_id: UUID

    event_type: str = Field(
        ...,
        description=(
            "Bereavement Note, Check Status, Comm Note, On-Call Note, "
            "Patient Notification, Phone Call, Progress Note, Reminder, Vol Note"
        ),
    )

    focus_area: Optional[str] = Field(
        None,
        description="ADL, Pain, Neurological/Mental, Family, Environment/Safety, etc.",
    )

    event_time: datetime
    summary: str

    details: Optional[Dict[str, Any]] = None


class CommunicationsLogAction(BaseModel):
    note: Optional[str] = Field(
        None,
        description=(
            "Optional operational note added during "
            "acknowledge / verify / resolve actions."
        ),
    )


class CommunicationsLogRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    patient_id: UUID

    event_type: str
    focus_area: Optional[str]

    event_time: datetime
    summary: str

    details: Optional[Dict[str, Any]]

    created_by: UUID
    created_at: datetime

    status: str

    acknowledged_by: Optional[UUID]
    acknowledged_at: Optional[datetime]

    verified_by: Optional[UUID]
    verified_at: Optional[datetime]

    resolved_by: Optional[UUID]
    resolved_at: Optional[datetime]

    @field_validator("details", mode="before")
    @classmethod
    def coerce_details_to_dict(cls, value):
        """
        Accept either:
        - dict
        - JSON string stored in legacy columns
        - fallback raw value
        """
        if value is None:
            return None

        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            try:
                parsed = json.loads(value)

                if isinstance(parsed, dict):
                    return parsed

            except Exception:
                return {"raw": value}

        return {"raw": value}