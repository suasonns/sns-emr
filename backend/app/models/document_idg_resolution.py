from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class DocumentIDGResolution(Base):
    __tablename__ = "document_idg_resolution"

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_records.id", ondelete="CASCADE"),
        primary_key=True,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    resolution_status = Column(
        String(32),
        nullable=False,
    )  # ACCEPTED / NO_CHANGE / OVERRIDDEN

    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    resolved_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    resolution_note = Column(
        Text,
        nullable=True,
    )
