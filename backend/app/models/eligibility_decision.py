from sqlalchemy import Column, Integer, String, Date, DateTime
from app.core.db import Base

class EligibilityDecision(Base):
    __tablename__ = "eligibility_decisions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, nullable=False)

    decision = Column(String(50), nullable=False)

    lcd_id = Column(String(20), nullable=False)
    mac = Column(String(20), nullable=False)
    mac_type = Column(String(10), nullable=False)
    lcd_effective_date = Column(Date, nullable=False)

    decision_timestamp = Column(DateTime, nullable=False)
    config_hash = Column(String(64), nullable=False)