from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class IDGReview(Base):
    """
    Enterprise-grade IDG Review.

    Purpose:
    - Represents patient-level interdisciplinary review.
    - Links IDG meeting activities to care planning workflows.
    - Supports audit-defensible IDG compliance.

    Compliance:
    - Must be tenant isolated.
    - Must be audit traceable.
    - Must support IDG review history.
    - Must support future POC linkage enforcement.
    """

    __tablename__ = "idg_reviews"

    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "benefit_period_id",
            "review_date",
            name="uq_idg_review_patient_bp_date",
        ),
        Index(
            "ix_idg_reviews_patient_bp",
            "patient_id",
            "benefit_period_id",
        ),
        Index(
            "ix_idg_reviews_review_date",
            "review_date",
        ),
    )

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

    summary = Column(
        Text,
        nullable=False,
    )

    poc_action = Column(
        Text,
        nullable=True,
    )

    # FK intentionally deferred during stabilization phase.
    plan_of_care_version_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    is_finalized = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    finalized_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    finalized_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )