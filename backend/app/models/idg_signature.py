from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class IDGSignature(Base):
    """
    Enterprise-grade IDG Signature.

    Purpose:
    - Captures user participation in IDG meeting
    - Serves as legal attendance + participation record

    Compliance:
    - One signature per user per meeting
    - Must include audit timestamps
    """

    __tablename__ = "idg_signatures"

    __table_args__ = (
        UniqueConstraint(
            "idg_meeting_id",
            "user_id",
            name="uq_idg_signature_user_meeting",
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

    idg_meeting_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_meetings.id"),
        nullable=False,
        index=True,
    )

    idg_review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_reviews.id"),
        nullable=True,
        index=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    is_signed = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    signed_at = Column(
        DateTime(timezone=True),
        nullable=True,
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