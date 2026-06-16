from __future__ import annotations

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class AuditLog(TenantScopedMixin, BaseModel):
    __tablename__ = "audit_logs"

    # ---------------------------------------------------------
    # TENANT ISOLATION (REQUIRED)
    # ---------------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # REQUEST CONTEXT (TRACEABILITY)
    # ---------------------------------------------------------
    request_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    ip_address = Column(
        String(64),
        nullable=True,
    )

    # ---------------------------------------------------------
    # ACTOR CONTEXT
    # ---------------------------------------------------------
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    role = Column(
        String(64),
        nullable=True,
    )

    # ---------------------------------------------------------
    # ACTION DETAILS (LOGGER CONTRACT)
    # ---------------------------------------------------------
    action = Column(
        String(64),
        nullable=False,
        index=True,
    )

    entity_type = Column(
        String(64),
        nullable=True,
        index=True,
    )

    entity_id = Column(
        String(128),
        nullable=True,
        index=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # STRUCTURED METADATA
    # DB column name = "metadata"
    # Python attribute name MUST NOT be "metadata"
    # ---------------------------------------------------------
    event_metadata = Column(
        "metadata",      # <-- DB column name
        JSON,
        nullable=True,
    )

    # ---------------------------------------------------------
    # TIMESTAMP (DB CONTROLLED)
    # ---------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
    )