from __future__ import annotations

import uuid

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class ClaimExportLog(Base):
    __tablename__ = "claim_export_logs"

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
    # RELATIONSHIPS
    # ---------------------------------------------------------
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    billing_cycle_id = Column(
        String,  # ✅ FIX: must match billing_cycles.id (VARCHAR)
        ForeignKey("billing_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # EXPORT DATA
    # ---------------------------------------------------------
    file_path = Column(
        String,
        nullable=False,
    )

    export_type = Column(
        String(50),
        nullable=True,
        doc="EDI / CSV / JSON / XML",
    )

    status = Column(
        String(32),
        nullable=False,
        default="SUCCESS",
        doc="SUCCESS / FAILED / RETRIED",
    )

    # ---------------------------------------------------------
    # OVERRIDE TRACKING (CRITICAL FOR COMPLIANCE)
    # ---------------------------------------------------------
    override_used = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    override_reason = Column(
        String,
        nullable=True,
    )

    override_approved_by = Column(
        String,
        nullable=True,
    )

    # ---------------------------------------------------------
    # AUDIT FIELDS (REQUIRED)
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
        doc="User who triggered export",
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
            "ix_claim_export_patient_cycle",
            "patient_id",
            "billing_cycle_id",
        ),
        Index(
            "ix_claim_export_status",
            "status",
        ),
    )