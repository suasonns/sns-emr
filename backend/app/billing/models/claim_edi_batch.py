from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, Index, DateTime, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class ClaimEdiBatch(Base):
    """
    One EDI 837I submission event (currently one claim per batch -- a
    future true multi-claim batch-generate/submit flow can add more
    claims to the same batch_number). Tracks 999/277CA acknowledgment
    state so "Claims Management" can show real batch/ack status instead
    of the old in-memory mock.
    """

    __tablename__ = "claim_edi_batches"

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
    # BATCH IDENTITY
    # ---------------------------------------------------------
    batch_number = Column(String(64), nullable=False)

    claim_count = Column(Integer, nullable=False, default=0, server_default=text("0"))

    total_amount = Column(Numeric(12, 2), nullable=False, default=0, server_default=text("0"))

    file_path = Column(String, nullable=True)

    submitted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # ---------------------------------------------------------
    # ACKNOWLEDGMENT (999 / 277CA)
    # ---------------------------------------------------------
    ack_status = Column(
        String(32),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
        doc="PENDING / ACCEPTED / REJECTED / PARTIAL",
    )

    ack_received_at = Column(DateTime(timezone=True), nullable=True)

    ack_raw_content = Column(Text, nullable=True)

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
    tenant = relationship("Tenant")
    claims = relationship("Claim", back_populates="edi_batch")

    __table_args__ = (
        Index("ix_claim_edi_batch_tenant_status", "tenant_id", "ack_status"),
        # Historical artifact: batch_number uniqueness is enforced by both
        # an explicit unique constraint (from the original migration) and a
        # separately-created plain index of the same name. Declared as two
        # objects here to match the DB exactly and keep the CI drift check
        # green without an unnecessary destructive migration.
        UniqueConstraint("batch_number", name="uq_claim_edi_batches_batch_number"),
        Index("ix_claim_edi_batches_batch_number", "batch_number"),
    )
