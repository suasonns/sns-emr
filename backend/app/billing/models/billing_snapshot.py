from sqlalchemy import Column, String, JSON
from app.db.base import Base


class BillingSnapshot(Base):
    __tablename__ = "billing_snapshot"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False)

    data = Column(JSON, nullable=False)