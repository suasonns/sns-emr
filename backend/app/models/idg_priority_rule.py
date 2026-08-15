# models/idg_priority_rule.py

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class IDGPriorityRule(Base):
    __tablename__ = "idg_priority_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    rule_key = Column(String(150), nullable=False, unique=True)
    keyword = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)

    idg_impact_level = Column(String(50), nullable=False, index=True)

    clinical_escalation_required = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    requires_idg_discussion = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    requires_followup = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    activation_route = Column(String(100), nullable=True)
    source_type = Column(String(100), nullable=True)

    weight = Column(
        Integer,
        nullable=False,
        server_default=text("50"),
    )

    active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )