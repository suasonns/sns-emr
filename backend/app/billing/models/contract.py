from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Contract(Base):
    __tablename__ = "payer_contracts"

    # ---------------------------------------------------------
    # PRIMARY KEY
    # ---------------------------------------------------------
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ---------------------------------------------------------
    # TENANT
    # ---------------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # PAYER LINK
    # ---------------------------------------------------------
    payer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("payers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # CONTRACT DATA
    # ---------------------------------------------------------
    contract_number = Column(String(100), nullable=True)

    status = Column(
        String(32),
        nullable=False,
        default="ACTIVE",
        doc="ACTIVE / INACTIVE / TERMINATED",
    )

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # ---------------------------------------------------------
    # AUDIT
    # ---------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_by = Column(String(255), nullable=True)

    # ---------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------
    payer = relationship("Payer")
    tenant = relationship("Tenant")

    # ---------------------------------------------------------
    # INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        Index("ix_contract_payer", "payer_id"),
    )