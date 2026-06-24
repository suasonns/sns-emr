import json
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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

    # Flexible metadata for trigger context, escalation chains, reminders, flags, etc.
    details: Optional[Dict[str, Any]] = None


class CommunicationsLogAction(BaseModel):
    note: Optional[str] = Field(
        None,
        description="Optional operational note added during acknowledge / verify / resolve actions.",
    )


class CommunicationsLogRead(BaseModel):
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
    def coerce_details_to_dict(cls, v):
        """
        Accept either:
        - a real dict
        - a JSON string stored in a legacy text column
        """
        if v is None:
            return None

        if isinstance(v, dict):
            return v

        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return {"raw": v}

        return {"raw": v}

    class Config:
        from_attributes = True