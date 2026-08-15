# backend/app/models/form_registry_model.py

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class FormRegistryModel(Base):
    __tablename__ = "form_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # -------------------------------------------------
    # Resolver dimensions (core identity)
    # -------------------------------------------------
    form_type = Column(String(64), nullable=False)
    form_family = Column(String(64), nullable=False)
    discipline = Column(String(32), nullable=False)
    level_of_care = Column(String(32), nullable=True)

    # -------------------------------------------------
    # Form identity (stable reference key)
    # -------------------------------------------------
    form_key = Column(String(128), nullable=False)

    # -------------------------------------------------
    # Control flags
    # -------------------------------------------------
    is_primary = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # -------------------------------------------------
    # Audit fields (REQUIRED for compliance)
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
        # ✅ Primary resolver index
        Index(
            "ix_form_registry_resolution",
            "discipline",
            "form_type",
            "level_of_care",
        ),

        # ✅ Make form_key unique ONLY within context
        Index(
            "ix_form_registry_unique_context",
            "form_key",
            "discipline",
            "level_of_care",
            unique=True,
        ),
    )