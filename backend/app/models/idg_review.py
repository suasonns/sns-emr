from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class IDGReview(Base):
    """
    Enterprise-grade IDG Review.

    Purpose:
    - Represents patient-level interdisciplinary review
    - Links IDGMeeting to PlanOfCareVersion

    Compliance:
    - MUST be tied to POC (future enforcement)
    - MUST track disciplines and MD attestation externally
    - MUST be audit traceable (who, when, what)
    """

    __tablename__ = "idg_reviews"

    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "benefit_period_id",
            "review_date",
            name="uq_idg_review_patient_bp_date",
        ),
        # ✅ PERFORMANCE + QUERY OPTIMIZATION
        Index("ix_idg_reviews_patient_bp", "patient_id", "benefit_period_id"),
        Index("ix_idg_reviews_review_date", "review_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    idg_meeting_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_meetings.id"),
        nullable=False,
        index=True,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    review_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    summary = Column(Text, nullable=False)

    poc_action = Column(Text, nullable=True)

    # 🔥 TEMP: FK removed for stabilization phase
    plan_of_care_version_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    is_finalized = Column(Boolean, nullable=False, default=False)

    finalized_by = Column(UUID(as_uuid=True), nullable=True)

    finalized_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=True)

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

    # ✅ OPTIONAL (ENTERPRISE HARDENING)
    updated_by = Column(UUID(as_uuid=True), nullable=True)