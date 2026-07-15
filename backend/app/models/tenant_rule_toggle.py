from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class TenantRuleToggle(Base):
    __tablename__ = "tenant_rule_toggles"

    # ✅ UUID PK (consistent with system)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ✅ FIXED — MUST MATCH tenants.id (UUID)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    workflow = Column(String(32), nullable=False, index=True)
    rule_id = Column(String(128), nullable=False, index=True)
    enabled = Column(Boolean, nullable=False, server_default=text("false"))

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    created_by = Column(UUID(as_uuid=True), nullable=True)