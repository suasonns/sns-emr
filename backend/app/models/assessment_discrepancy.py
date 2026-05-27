from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class AssessmentDiscrepancy(Base):
    __tablename__ = "assessment_discrepancies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)

    domain = Column(String(50), nullable=False)

    baseline_assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    comparing_assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)

    discrepancy_summary = Column(Text, nullable=False)

    # IMPORTANT: interdisciplinary model
    requires_idg_reconciliation = Column(Boolean, nullable=False, default=True)
    resolved = Column(Boolean, nullable=False, default=False)

    resolution_type = Column(String(30), nullable=True)
    # RESOLVED | ACCEPTED_DIFFERENCE | ESCALATED

    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_in_idg_meeting_id = Column(UUID(as_uuid=True), nullable=True)

    resolution_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", backref="assessment_discrepancies")

    baseline_assessment = relationship(
        "Assessment",
        foreign_keys=[baseline_assessment_id],
        back_populates="discrepancies_as_baseline"
    )

    comparing_assessment = relationship(
        "Assessment",
        foreign_keys=[comparing_assessment_id],
        back_populates="discrepancies_as_comparing"
    )
