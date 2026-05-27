from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)

    discipline = Column(String(10), nullable=False)
    assessment_type = Column(String(50), nullable=False)

    occurred_at = Column(DateTime(timezone=True), nullable=False)

    signed_at = Column(DateTime(timezone=True), nullable=True)
    signed_by = Column(UUID(as_uuid=True), nullable=True)

    status = Column(String(10), nullable=False, default="DRAFT")

    risk_score = Column(Numeric, nullable=True)
    risk_level = Column(String(20), nullable=True)

    data_json = Column(JSONB, nullable=False, default=dict)

    document_id = Column(UUID(as_uuid=True), ForeignKey("document_records.id"), nullable=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships (SAFE — no cascade deletes on parent direction)
    patient = relationship("Patient", backref="assessments")
    visit = relationship("Visit", backref="assessments")
    document = relationship("DocumentRecord", backref="assessments")

    references = relationship(
        "AssessmentReference",
        foreign_keys="[AssessmentReference.assessment_id]",
        back_populates="assessment",
        cascade="all, delete-orphan"
    )

    discrepancies_as_baseline = relationship(
        "AssessmentDiscrepancy",
        foreign_keys="[AssessmentDiscrepancy.baseline_assessment_id]",
        back_populates="baseline_assessment"
    )

    discrepancies_as_comparing = relationship(
        "AssessmentDiscrepancy",
        foreign_keys="[AssessmentDiscrepancy.comparing_assessment_id]",
        back_populates="comparing_assessment"
    )