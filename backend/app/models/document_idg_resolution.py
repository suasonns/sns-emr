from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class DocumentIDGResolution(Base):
    """
    Enterprise-grade Document IDG Resolution.

    Purpose:
    - Tracks how documents are reviewed/resolved in IDG
    - Supports ADR response and survey defense

    Compliance:
    - MUST be tied to IDG review
    - Must track resolution history over time
    """

    __tablename__ = "document_idg_resolution"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "idg_review_id",
            name="uq_document_idg_review_resolution",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 🔥 CRITICAL LINK
    idg_review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_reviews.id"),
        nullable=False,
        index=True,
    )

    resolution_status = Column(
        String(32),
        nullable=False,
    )  # ACCEPTED / NO_CHANGE / OVERRIDDEN

    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    resolved_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    resolution_note = Column(
        Text,
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