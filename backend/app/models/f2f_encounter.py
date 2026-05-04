import uuid
from sqlalchemy import Column, Date, DateTime, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class F2FEncounter(BaseModel):
    __tablename__ = "f2f_encounters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=False, index=True)

    encounter_date = Column(Date, nullable=False)
    performed_by_role = Column(String, nullable=False)  # MD or NP
    performed_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    summary = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="DRAFT")
    finalized_at = Column(DateTime, nullable=True)
