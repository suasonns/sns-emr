# models/idg_group_schedule_rule.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class IDGGroupScheduleRule(Base):
    """
    Recurring IDG meeting cadence for one IDGGroup.

    A group may have multiple active rules (e.g. a group meeting twice a
    week has one rule per weekday). Automatic generation (see
    idg_group_scheduler_service.py) unions every active rule for a group
    to compute its actual upcoming calendar of meeting dates — no manual
    "click to create" step, per agency requirement (fully automatic).

    Examples:
        - Weekly:            weekday=FRI (4), nth_occurrences=NULL
        - Biweekly 2nd/4th:  weekday=FRI (4), nth_occurrences=[2, 4]
        - 3x/week:           three rows, weekday=MON(0)/WED(2)/FRI(4), each NULL
    """

    __tablename__ = "idg_group_schedule_rules"

    __table_args__ = (
        Index("ix_idg_group_schedule_rules_tenant_id", "tenant_id"),
        Index("ix_idg_group_schedule_rules_idg_group_id", "idg_group_id"),
        Index("ix_idg_group_schedule_rules_is_active", "is_active"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    idg_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_groups.id"),
        nullable=False,
        index=True,
    )

    # 0=Monday ... 6=Sunday (Python datetime.weekday() convention).
    weekday = Column(
        Integer,
        nullable=False,
    )

    # NULL/empty => every occurrence of that weekday (weekly cadence).
    # Otherwise a JSON array of 1-based occurrence-in-month numbers, e.g.
    # [2, 4] for "2nd and 4th Friday of the month".
    nth_occurrences = Column(
        JSONB,
        nullable=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        index=True,
    )

    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )
