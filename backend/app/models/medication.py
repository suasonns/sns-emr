from sqlalchemy import Column, String, Date, ForeignKey
from app.models.base import BaseModel

class Medication(BaseModel):
    __tablename__ = "medications"

    patient_id = Column(ForeignKey("patients.id"), nullable=False)

    medication_name = Column(String, nullable=False)
    canonical_name = Column(String(255), index=True, nullable=True)

    dosage = Column(String, nullable=False)
    route = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)