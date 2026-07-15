from __future__ import annotations

import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Index,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class BillingSummary(Base):
    __tablename__ = "billing_summaries"

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
    # RELATIONS
    # ---------------------------------------------------------
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # ✅ FIXED: MUST MATCH billing_cycles.id (UUID)
    # ---------------------------------------------------------
    billing_cycle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("billing_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # BILLING DATA
    # ---------------------------------------------------------
    total_units = Column(
        Integer,
        nullable=False,
        default=0,
    )

    total_amount = Column(
        Integer,
        nullable=False,
        default=0,
    )

    risk_score = Column(
        Integer,
        nullable=False,
        doc="0–100 risk score for audit / claim review",
    )

    status = Column(
        String(32),
        nullable=False,
        default="DRAFT",
        doc="DRAFT / FINALIZED / SUBMITTED / RECONCILED",
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
    patient = relationship("Patient")
    billing_cycle = relationship("BillingCycle")
    tenant = relationship("Tenant")

    # ---------------------------------------------------------
    # CONSTRAINTS + INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "billing_cycle_id",
            name="uq_billing_summary_patient_cycle",
        ),
        Index(
            "ix_billing_summary_patient_status",
            "patient_id",
            "status",
        ),
        Index(
            "ix_billing_summary_cycle",
            "billing_cycle_id",
        ),
    )