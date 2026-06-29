from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.models.base import Base


class Form(Base):
    __tablename__ = "forms"

    # -------------------------------------------------
    # Identity
    # -------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # -------------------------------------------------
    # Relationships
    # -------------------------------------------------
    visit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("visits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    form_registry_id = Column(
        UUID(as_uuid=True),
        ForeignKey("form_registry.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # -------------------------------------------------
    # Snapshot fields (CRITICAL for audit history)
    # -------------------------------------------------
    form_key = Column(String(128), nullable=False)
    form_family = Column(String(64), nullable=False)
    form_type = Column(String(64), nullable=False)

    # -------------------------------------------------
    # Core data
    # -------------------------------------------------
    content = Column(JSONB, nullable=False, server_default="{}")

    is_primary = Column(Boolean, nullable=False, default=False)

    # -------------------------------------------------
    # Status / lifecycle
    # -------------------------------------------------
    status = Column(String(32), nullable=False, default="DRAFT")

    # -------------------------------------------------
    # Audit fields (REQUIRED)
    # -------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    finalized_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    finalized_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # -------------------------------------------------
    # Multi-tenant safety (if applicable)
    # -------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )