from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class BenefitPeriod(BaseModel):
    __tablename__ = "benefit_periods"

    patient_id = Column(ForeignKey("patients.id"), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    # BP1/BP2/BP3... (90/90/60/60)
    period_number = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="active")
