import uuid
from sqlalchemy import Column, Date, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class Certification(BaseModel):
    __tablename__ = "certifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=False, index=True)

    cert_type = Column(String, nullable=False)  # INITIAL or RECERT
    signed_at = Column(DateTime, nullable=False)
    effective_date = Column(Date, nullable=False)

    signed_by_role = Column(String, nullable=False)  # MD or NP
    signed_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    status = Column(String, nullable=False, default="FINALIZED")