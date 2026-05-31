from sqlalchemy import Column, String, Date
from app.db.base import Base


class PatientPOS(Base):
    __tablename__ = "patient_pos"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False)

    pos_type = Column(String, nullable=False)
    facility_name = Column(String)

    effective_date = Column(Date, nullable=False)
    end_date = Column(Date)