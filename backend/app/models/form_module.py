from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class FormModule(Base):
    __tablename__ = "form_modules"

    # -------------------------------------------------
    # Identity
    # -------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    module_key = Column(String(128), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(String, nullable=True)

    # -------------------------------------------------
    # Control flags
    # -------------------------------------------------
    is_active = Column(Boolean, nullable=False, default=True)

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
        nullable=True,
        onupdate=func.now(),
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -------------------------------------------------
    # Indexing strategy
    # -------------------------------------------------
    __table_args__ = (
        Index("ix_form_modules_module_key", "module_key"),
        Index("ix_form_modules_active", "is_active"),
    )
