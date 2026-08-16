"""
Security activity events.

Read by the internal superuser dashboard via raw SQL to report bulk export
activity. Like diagnosis_sources, this table existed only in the hand-built
development database.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class SecurityActivityEvent(Base):
    __tablename__ = "security_activity_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # e.g. BULK_EXPORT_ATTEMPT, BULK_EXPORT_ALLOWED.
    event_type = Column(String(64), nullable=False, index=True)
    event_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    scope = Column(String(64), nullable=True)
    result = Column(String(32), nullable=True)

    patient_count = Column(Integer, nullable=True)
    document_count = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_security_activity_events_type_at", "event_type", "event_at"),
    )
