from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class AssessmentReference(Base):
    __tablename__ = "assessment_references"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    referenced_assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)

    reference_kind = Column(String(30), nullable=False)

    reviewed_ack = Column(Boolean, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    assessment = relationship(
        "Assessment",
        foreign_keys=[assessment_id],
        back_populates="references"
    )

    referenced_assessment = relationship(
        "Assessment",
        foreign_keys=[referenced_assessment_id]
    )