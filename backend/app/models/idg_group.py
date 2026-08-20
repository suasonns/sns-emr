# models/idg_group.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class IDGGroup(Base):
    """
    A named/numbered IDG cohort within a tenant (e.g. "Group 1", "Group 2").

    Modeled after the real-world pattern where an agency splits its whole
    active census into multiple groups so IDG can happen more than once a
    week without every patient being reviewed on the same day (e.g. Group
    1 meets every Friday, Group 2 meets 2nd/4th Wednesday, Group 3 meets
    Monday and Thursday).

    A patient belongs to at most one active group at a time (assignment
    tracked on Patient via idg_group_id — see migration). This is
    intentionally separate from IDGMeeting/IDGMeetingPatientReview
    (entities #2/#3, see IDG_DOMAIN_MODEL.md): a group is a scheduling
    cohort, not a meeting instance.
    """

    __tablename__ = "idg_groups"

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_idg_groups_tenant_name"),
        Index("ix_idg_groups_tenant_id", "tenant_id"),
        Index("ix_idg_groups_is_active", "is_active"),
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

    name = Column(
        String(100),
        nullable=False,
    )

    # Display ordering only (Group 1, Group 2, ...) — not a schedule field.
    sort_order = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
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
