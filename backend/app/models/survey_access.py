from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from datetime import datetime

from app.models.base import BaseModel


class SurveyAccess(BaseModel):
    __tablename__ = "survey_access"

    patient_id = Column(ForeignKey("patients.id"), nullable=False)
    issued_by = Column(ForeignKey("users.id"), nullable=True)

    token_jti = Column(String, unique=True, nullable=False)

    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    used = Column(Boolean, default=False)
    revoked = Column(Boolean, default=False)