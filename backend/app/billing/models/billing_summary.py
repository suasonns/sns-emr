from sqlalchemy import Column, String, Integer
from app.db.base import Base


class BillingSummary(Base):
    __tablename__ = "billing_summary"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False)
    billing_cycle_id = Column(String, nullable=False)

    total_units = Column(Integer, nullable=False)

    status = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False)