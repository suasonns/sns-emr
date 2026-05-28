from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class IDGSignature(Base):
    """
    Signature attesting participation in IDG review.
    """

    __tablename__ = "idg_signatures"

    id = Column(UUID(as_uuid=True), primary_key=True)

    idg_meeting_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_meetings.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    signed_at = Column(
        DateTime(timezone=False),
        nullable=False,
    )

    created_by = Column(
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