"""
Enterprise-grade IDG justification note.

Purpose:
- Stores eligibility-driven or compliance-driven justification
- DISTINCT from canonical CMS IDG review (idg_reviews)
- Used for survey defense, ADR responses, and audit traceability
"""

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class IDGJustificationNote(Base):
    __tablename__ = "idg_justification_notes"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
    )

    eligibility_assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("eligibility_assessments.id", ondelete="CASCADE"),
        nullable=True,
    )

    justification_text = Column(
        Text,
        nullable=False,
        doc="Narrative justification supporting eligibility or care decisions",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_by = Column(
        Text,
        nullable=True,
    )