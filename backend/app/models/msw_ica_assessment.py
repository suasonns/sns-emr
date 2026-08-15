import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class MswIcaAssessment(Base):
    __tablename__ = "msw_ica_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="SET NULL"), nullable=True, index=True)

    assessment_type = Column(String(32), nullable=False, default="MSWICA")
    status = Column(String(32), nullable=False, default="DRAFT")
    locked = Column(Boolean, nullable=False, default=False)

    form_data = Column(JSONB, nullable=False, default=dict)
    notes = Column(Text, nullable=True)

    locked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("Patient", backref="msw_ica_assessments")
    visit = relationship("Visit", backref="msw_ica_assessments")
