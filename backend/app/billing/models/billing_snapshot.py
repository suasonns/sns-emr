from __future__ import annotations

import uuid

from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class BillingSnapshot(Base):
    __tablename__ = "billing_snapshots"

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
    # OPTIONAL BILLING CONTEXT (FIXED TYPE ✅)
    # ---------------------------------------------------------
    billing_cycle_id = Column(
        String,  # ✅ MUST MATCH billing_cycles.id (VARCHAR)
        ForeignKey("billing_cycles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # SNAPSHOT METADATA
    # ---------------------------------------------------------
    snapshot_type = Column(
        String(50),
        nullable=False,
        doc="BILLING / CLAIM / INVOICE / POC_BILLING",
    )

    version = Column(
        String(50),
        nullable=True,
        doc="Optional version tag or sequence number",
    )

    # ---------------------------------------------------------
    # SNAPSHOT DATA (CRITICAL FOR AUDIT)
    # ---------------------------------------------------------
    data = Column(
        JSON,
        nullable=False,
        doc="Full serialized billing snapshot payload",
    )

    # ---------------------------------------------------------
    # AUDIT FIELDS (CRITICAL)
    # ---------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
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
    # INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        Index(
            "ix_billing_snapshot_patient_created",
            "patient_id",
            "created_at",
        ),
        Index(
            "ix_billing_snapshot_tenant_type",
            "tenant_id",
            "snapshot_type",
        ),
    )