# models/idg_attendee.py  

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class IDGAttendee(Base):
    __tablename__ = "idg_attendees"

    __table_args__ = (
        # ✅ prevent duplicate attendance records
        UniqueConstraint(
            "idg_review_id",
            "user_id",
            name="uq_idg_attendee_review_user"
        ),
        # ✅ performance indexes
        Index("ix_idg_attendees_review", "idg_review_id"),
        Index("ix_idg_attendees_user", "user_id"),
        Index("ix_idg_attendees_tenant", "tenant_id"),
        Index("ix_idg_attendees_discipline", "discipline"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    idg_review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_reviews.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),  # ✅ enforce referential integrity
        nullable=False,
        index=True,
    )

    # ✅ Core hospice disciplines
    discipline = Column(
        String,
        nullable=False,
    )
    # Expected values:
    # MD, RN, MSW, SC, OTHER

    role_label = Column(
        String,
        nullable=True,
    )

    attended = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ✅ signature tracking (compliance-critical)
    signed = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    signed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ✅ audit fields (REQUIRED for defensibility)
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

    updated_by = Column(UUID(as_uuid=True), nullable=True)
