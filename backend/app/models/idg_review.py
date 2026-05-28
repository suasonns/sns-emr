from __future__ import annotations

from sqlalchemy import Column, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class IDGReview(Base):
    """
    Canonical interdisciplinary review record.

    Regulatory basis:
    - CMS CoPs §418.56
    """

    __tablename__ = "idg_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True)

    idg_meeting_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_meetings.id"),
        nullable=False,
        index=True,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id"),
        nullable=True,
        index=True,
    )

    summary = Column(Text, nullable=True)
    poc_action = Column(Text, nullable=True)

    is_finalized = Column(Boolean, nullable=False, server_default="false")

    finalized_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )