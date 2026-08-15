from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class GuardrailPolicy(Base):
    """
    Tenant-scoped configurable policy value.

    This table stores tenant-specific operational and compliance policy
    values used by guardrails, IDG enforcement, admission checks, and
    other configurable workflows.

    Examples of policy_key values:
        GUARDRAIL_MODE
        MIN_NARRATIVE_LENGTH
        REQUIRE_MEASURABLE_DECLINE
        IDG_REQUIRED_NOTE_DISCIPLINES
        IDG_REQUIRED_NOTE_DISCIPLINES_ROUTINE
        IDG_REQUIRED_NOTE_DISCIPLINES_EMERGENCY

    The value field is JSONB so callers can store booleans, numbers,
    strings, lists, or structured configuration without schema churn.
    """

    __tablename__ = "guardrail_policies"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "policy_key",
            name="uq_guardrail_policy_tenant_key",
        ),
        Index("ix_guardrail_policies_tenant_id", "tenant_id"),
        Index("ix_guardrail_policies_policy_key", "policy_key"),
        Index("ix_guardrail_policies_tenant_key", "tenant_id", "policy_key"),
        Index("ix_guardrail_policies_enabled", "enabled"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
    )

    policy_key = Column(
        String(150),
        nullable=False,
    )

    value = Column(
        JSONB,
        nullable=True,
    )

    enabled = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

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

    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )