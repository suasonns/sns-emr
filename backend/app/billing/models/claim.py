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
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Claim(Base):
    """
    Real, persisted per-patient-per-cycle claim record backing the
    Claims Management page and the Biller's Dashboard claim-lifecycle
    counts. Replaces the old in-memory app.billing.store mock.

    Lifecycle (see app.billing.api.claim_status_router.ALLOWED_TRANSITIONS):
        READY -> SENT -> ACCEPTED -> PAID
                       -> DENIED
                 ACCEPTED -> DENIED
    """

    __tablename__ = "claims"

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

    billing_cycle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("billing_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    edi_batch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("claim_edi_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # CLAIM DATA
    # ---------------------------------------------------------
    payer_name = Column(String(255), nullable=True)

    service_date = Column(Date, nullable=True)

    total_charge = Column(Numeric(12, 2), nullable=False, default=0, server_default=text("0"))

    total_units = Column(Integer, nullable=False, default=0, server_default=text("0"))

    risk_score = Column(Integer, nullable=False, default=0, server_default=text("0"))

    status = Column(
        String(32),
        nullable=False,
        default="READY",
        server_default=text("'READY'"),
        index=True,
        doc="READY / SENT / ACCEPTED / DENIED / PAID",
    )

    last_status_reason = Column(Text, nullable=True)

    claim_control_number = Column(String(64), nullable=True, index=True)

    exported_at = Column(DateTime(timezone=True), nullable=True)

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

    created_by = Column(String(255), nullable=True)

    # ---------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------
    tenant = relationship("Tenant")
    patient = relationship("Patient")
    billing_cycle = relationship("BillingCycle")
    edi_batch = relationship("ClaimEdiBatch", back_populates="claims")

    # ---------------------------------------------------------
    # CONSTRAINTS + INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "billing_cycle_id",
            name="uq_claim_patient_cycle",
        ),
        Index("ix_claim_tenant_status", "tenant_id", "status"),
    )
