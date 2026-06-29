from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Text, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class IDGJustification(Base):
    """
    Enterprise-grade IDG Justification record.

    Purpose:
    - ADR responses
    - Eligibility justification
    - Survey defense
    - Clinical decision documentation

    Compliance Notes:
    - MUST be traceable to IDG review
    - MUST be patient + tenant scoped
    """

    __tablename__ = "idg_justification_notes"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    # 🔥 CRITICAL: LINK TO IDG REVIEW
    idg_review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_reviews.id"),
        nullable=True,
        index=True,
    )

    # ✅ STRUCTURED CATEGORY
    justification_type = Column(
        String(50),
        nullable=False,
        default="GENERAL",  # ADR, ELIGIBILITY, SURVEY, CLINICAL
    )

    note_text = Column(
        Text,
        nullable=False,
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )