from pydantic import BaseModel
from uuid import UUID
from datetime import date
from typing import Optional


class F2FCreateRequest(BaseModel):
    patient_id: UUID
    benefit_period_id: UUID
    encounter_date: date
    performed_by_role: str
    performed_by_user_id: Optional[UUID] = None
    summary: Optional[str] = None
