import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class RnicaAssessment(Base):
    __tablename__ = "rnica_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="SET NULL"), nullable=True, index=True)

    # Scopes this assessment to the admission episode it belongs to. The RN
    # Initial Comprehensive Assessment (assessment_type == "RNICA") is only
    # ever performed once per admission -- this column is what lets the
    # backend enforce that (see _get_current_admission_for_patient /
    # save_rnica_assessment in app/api/visits.py) while still allowing a
    # brand-new one after a discharge + re-admission (new Admission row).
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True, index=True)

    # Defense-in-depth: lets any future query filter/scope by tenant directly
    # instead of relying solely on patient_id being globally unique.
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)

    assessment_type = Column(String(32), nullable=False, default="RNICA")
    status = Column(String(32), nullable=False, default="DRAFT")
    locked = Column(Boolean, nullable=False, default=False)

    form_data = Column(JSONB, nullable=False, default=dict)
    notes = Column(Text, nullable=True)

    locked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("Patient", backref="rnica_assessments")
    visit = relationship("Visit", backref="rnica_assessments")
