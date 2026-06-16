from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field


class CommunicationsLogCreate(BaseModel):
    patient_id: UUID

    # EXACT dropdown values
    event_type: str = Field(
        ...,
        description="Bereavement Note, Check Status, Comm Note, On-Call Note, "
                    "Patient Notification, Phone Call, Progress Note, Reminder, Vol Note",
    )

    focus_area: Optional[str] = Field(
        None,
        description="ADL, Pain, Neurological/Mental, Family, Environment/Safety, etc.",
    )

    event_time: datetime
    summary: str

    # Free‑form; used for reminders, flags, future expansion
    details: Optional[Dict] = None


class CommunicationsLogRead(BaseModel):
    id: UUID
    patient_id: UUID
    event_type: str
    focus_area: Optional[str]
    event_time: datetime
    summary: str
    details: Optional[Dict]
    created_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True