from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class DocumentNotification(Base):
    __tablename__ = "document_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_records.id", ondelete="CASCADE"),
        nullable=False,
    )

    recipient_role = Column(String(32), nullable=False)

    recipient_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    notified_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    reminder_count = Column(Integer, nullable=False, default=0)
    last_reminder_at = Column(DateTime(timezone=True), nullable=True)

    # --- Resolution fields (added via Alembic migration) ---
    resolution_status = Column(String(32), nullable=True)  # ACCEPTED/NO_CHANGE/OVERRIDDEN
    resolution_note = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )