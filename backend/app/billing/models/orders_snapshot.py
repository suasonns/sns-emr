from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class OrdersSnapshot(Base):
    __tablename__ = "orders_snapshots"

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
    # PATIENT LINK
    # ---------------------------------------------------------
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # ORDER DATA
    # ---------------------------------------------------------
    discipline = Column(
        String(32),
        nullable=False,
        doc="RN / LVN / HHA / PT / OT / ST / MSW",
    )

    visits_per_week = Column(
        Integer,
        nullable=False,
    )

    status = Column(
        String(32),
        nullable=False,
        default="ACTIVE",
        doc="ACTIVE / OFF_HOLD / DISCONTINUED",
    )

    effective_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True, index=True)

    # ---------------------------------------------------------
    # SNAPSHOT METADATA
    # ---------------------------------------------------------
    snapshot_type = Column(
        String(50),
        nullable=False,
        default="ORDERS",
    )

    version = Column(
        String(50),
        nullable=True,
    )

    # ---------------------------------------------------------
    # AUDIT FIELDS
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
    patient = relationship("Patient")
    tenant = relationship("Tenant")

    # ---------------------------------------------------------
    # CONSTRAINTS + INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        # ✅ enforce valid date range
        CheckConstraint(
            "end_date IS NULL OR end_date >= effective_date",
            name="ck_orders_snapshot_dates",
        ),

        # ✅ performance indexes
        Index(
            "ix_orders_snapshot_patient_date",
            "patient_id",
            "effective_date",
        ),
        Index(
            "ix_orders_snapshot_tenant",
            "tenant_id",
        ),
    )