from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class FormPackageModule(Base):
    __tablename__ = "form_package_modules"

    # -------------------------------------------------
    # Identity
    # -------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # -------------------------------------------------
    # Relationships
    # -------------------------------------------------
    form_registry_id = Column(
        UUID(as_uuid=True),
        ForeignKey("form_registry.id", ondelete="CASCADE"),
        nullable=False,
    )

    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("form_modules.id", ondelete="CASCADE"),
        nullable=False,
    )

    # -------------------------------------------------
    # Control / behavior
    # -------------------------------------------------
    display_order = Column(Integer, nullable=True)

    is_required = Column(Boolean, nullable=False, default=True)

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
    # Constraints + indexing
    # -------------------------------------------------
    __table_args__ = (
        UniqueConstraint(
            "form_registry_id",
            "module_id",
            name="uq_form_package_modules_registry_module",
        ),
        Index("ix_fpm_form", "form_registry_id"),
        Index("ix_fpm_module", "module_id"),
        Index("ix_fpm_active", "is_active"),
    )