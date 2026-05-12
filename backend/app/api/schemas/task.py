from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TaskResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    benefit_period_id: Optional[UUID]

    task_type: str
    discipline: str
    regulatory_basis: str

    due_date: date
    status: str
    completed_at: Optional[datetime]

    alert_reason: Optional[str]

    model_config = ConfigDict(from_attributes=True)
