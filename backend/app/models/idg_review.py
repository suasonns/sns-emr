from sqlalchemy import Column, Date, ForeignKey, Boolean
from datetime import date

from app.models.base import BaseModel


class IDGReview(BaseModel):
    __tablename__ = "idg_reviews"

    patient_id = Column(ForeignKey("patients.id"), nullable=False)
    review_date = Column(Date, nullable=False)

    # Discipline participation flags (survey‑friendly)
    rn_present = Column(Boolean, default=True)
    physician_present = Column(Boolean, default=True)
    social_worker_present = Column(Boolean, default=False)
    chaplain_present = Column(Boolean, default=False)
