from __future__ import annotations

import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Payer(Base):
    __tablename__ = "payers"

    # ---------------------------------------------------------
    # PRIMARY KEY
    # ---------------------------------------------------------
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ---------------------------------------------------------
    # TENANT ISOLATION
    # ---------------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # CORE DATA
    # ---------------------------------------------------------
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    code = Column(
        String(50),
        nullable=True,
        index=True,
    )

    payer_type = Column(
        String(50),
        nullable=True,
        doc="MEDICARE / MEDICAID / PRIVATE / HMO / PPO",
    )

    status = Column(
        String(32),
        nullable=False,
        default="ACTIVE",
        doc="ACTIVE / INACTIVE",
    )

    # ---------------------------------------------------------
    # AUDIT FIELDS
    # ---------------------------------------------------------
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

    created_by = Column(
        String(255),
        nullable=True,
    )

    # ---------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------
    tenant = relationship("Tenant")

    # ---------------------------------------------------------
    # INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        Index("ix_payers_name", "name"),
    )
