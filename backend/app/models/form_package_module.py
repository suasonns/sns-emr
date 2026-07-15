from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Index,
    text,
)
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
    display_order = Column(Integer, nullable=False)

    is_required = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

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
            # Prevent duplicate modules per form (active rows only)
            Index(
                "uq_fpm_active_unique",
                "form_registry_id",
                "module_id",
                unique=True,
                postgresql_where=(Column("deleted_at").is_(None)),
            ),

            # Enforce deterministic ordering per form
            UniqueConstraint(
                "form_registry_id",
                "display_order",
                name="uq_form_registry_display_order",
            ),

            # Performance indexes
            Index("ix_fpm_form", "form_registry_id"),
            Index("ix_fpm_module", "module_id"),
            Index(
                "ix_fpm_active_registry",
                "form_registry_id",
                postgresql_where=(Column("is_active") == True),
            ),
        )