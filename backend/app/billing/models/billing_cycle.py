from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Integer, Date, ForeignKey, Index, DateTime, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class BillingCycle(Base):
    __tablename__ = "billing_cycles"

    # ---------------------------------------------------------
    # PRIMARY KEY
    # ---------------------------------------------------------
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ---------------------------------------------------------
    # TENANT (REQUIRED FOR ISOLATION)
    # ---------------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # BILLING PERIOD
    # ---------------------------------------------------------
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # ---------------------------------------------------------
    # STATUS (BILLING CONTROL)
    # ---------------------------------------------------------
    status = Column(
        String(32),
        nullable=False,
        default="OPEN",
        doc="OPEN / CLOSED / LOCKED",
    )

    # ---------------------------------------------------------
    # AUDIT FIELDS (REQUIRED FOR COMPLIANCE)
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

    created_by = Column(String(255), nullable=True)

    # ---------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------
    tenant = relationship("Tenant")

    # ---------------------------------------------------------
    # CONSTRAINTS + INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        # ✅ Prevent duplicate billing cycles
        UniqueConstraint(
            "tenant_id",
            "month",
            "year",
            name="uq_billing_cycle_tenant_month_year",
        ),

        # ✅ Ensure valid date range
        CheckConstraint(
            "end_date >= start_date",
            name="ck_billing_cycle_dates",
        ),

        # ✅ Query performance
        Index(
            "ix_billing_cycle_tenant_dates",
            "tenant_id",
            "start_date",
            "end_date",
        ),
    )