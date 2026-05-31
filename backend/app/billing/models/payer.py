from sqlalchemy import Column, String
from app.db.base import Base


class PatientPayer(Base):
    __tablename__ = "patient_payers"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False)

    payer_name = Column(String, nullable=False)
    payer_type = Column(String, nullable=False)
