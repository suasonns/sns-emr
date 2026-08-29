from __future__ import annotations

import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Date,
    ForeignKey,
    Index,
    DateTime,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Appeal(Base):
    """
    Real, persisted appeal attempt against a Denial. A single denial can
    have multiple appeal levels (e.g. first-level reconsideration ->
    second-level formal appeal), each tracked as its own row so the
    Denials & Appeals page can show true appeal history/outcomes instead
    of a single fabricated status.
    """

    __tablename__ = "appeals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    denial_id = Column(
        UUID(as_uuid=True),
        ForeignKey("denials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    level = Column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
        doc="1 = first-level reconsideration, 2 = second-level formal appeal, 3+ = ALJ/external review",
    )

    status = Column(
        String(32),
        nullable=False,
        default="DRAFT",
        server_default=text("'DRAFT'"),
        index=True,
        doc="DRAFT / SUBMITTED / IN_REVIEW / APPROVED / DENIED / WITHDRAWN",
    )

    submitted_date = Column(Date, nullable=True)

    submitted_by = Column(String(255), nullable=True)

    decision_date = Column(Date, nullable=True)

    outcome_amount = Column(
        Numeric(12, 2),
        nullable=True,
        doc="Amount recovered if the appeal was approved/partially approved.",
    )

    notes = Column(Text, nullable=True)

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

    tenant = relationship("Tenant")
    denial = relationship("Denial", back_populates="appeals")

    __table_args__ = (
        Index("ix_appeal_tenant_status", "tenant_id", "status"),
        Index("ix_appeal_denial_level", "denial_id", "level"),
    )
