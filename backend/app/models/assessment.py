from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --------------------------------------------------
    # ✅ RELATIONS
    # --------------------------------------------------
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    visit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("visits.id"),
        nullable=True,
        index=True
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_records.id"),
        nullable=True
    )

    # --------------------------------------------------
    # ✅ CORE CLINICAL
    # --------------------------------------------------
    discipline = Column(String(10), nullable=False)
    assessment_type = Column(String(50), nullable=False)

    occurred_at = Column(DateTime(timezone=True), nullable=False)

    # SOC reference for HUV logic
    soc_date = Column(DateTime(timezone=True), nullable=False)

    # --------------------------------------------------
    # ✅ SIGNATURE
    # --------------------------------------------------
    signed_at = Column(DateTime(timezone=True), nullable=True)
    signed_by = Column(UUID(as_uuid=True), nullable=True)

    status = Column(String(20), nullable=False, default="DRAFT")

    # --------------------------------------------------
    # ✅ CLINICAL RISK
    # --------------------------------------------------
    risk_score = Column(Numeric, nullable=True)
    risk_level = Column(String(20), nullable=True)

    # --------------------------------------------------
    # ✅ DATA PAYLOAD
    # --------------------------------------------------
    data_json = Column(JSONB, nullable=False, default=dict)

    # --------------------------------------------------
    # ✅ AUDIT
    # --------------------------------------------------
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # --------------------------------------------------
    # ✅ RELATIONSHIPS
    # --------------------------------------------------
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

    # --------------------------------------------------
    # ✅ INDEXES (CRITICAL FOR TIMEPOINT RULES)
    # --------------------------------------------------
    __table_args__ = (
        Index("idx_assessment_patient_time", "patient_id", "occurred_at"),
    )