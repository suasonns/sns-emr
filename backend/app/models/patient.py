import uuid
from sqlalchemy import Column, String, Date, DateTime
from app.models.base import BaseModel
from sqlalchemy import Column, Date

class Patient(BaseModel):
    __tablename__ = "patients"

    mrn = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    primary_diagnosis = Column(String, nullable=False)
    status = Column(String, nullable=False)

    hospice_election_date = Column(Date, nullable=True)
    discharge_date = Column(Date, nullable=True)
    discharge_reason = Column(String, nullable=True)

    # ✅ Crisis / acuity tracking (must be inside the class)
    acuity_state = Column(String, nullable=False, default="ROUTINE")
    crisis_started_at = Column(DateTime, nullable=True)
    crisis_ended_at = Column(DateTime, nullable=True)
