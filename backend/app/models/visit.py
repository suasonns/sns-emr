from sqlalchemy import Column, String, DateTime, ForeignKey
from app.models.base import BaseModel
from datetime import datetime


class Visit(BaseModel):
    __tablename__ = "visits"

    patient_id = Column(
        ForeignKey("patients.id"),
        nullable=False,
    )

    provider_id = Column(
        ForeignKey("users.id"),
        nullable=False,
    )

    visit_type = Column(String, nullable=False)
    visit_datetime = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="draft")