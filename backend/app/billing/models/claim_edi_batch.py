from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, Index, DateTime, Text
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
    batch_number = Column(String(64), nullable=False, unique=True, index=True)

    claim_count = Column(Integer, nullable=False, default=0)

    total_amount = Column(Numeric(12, 2), nullable=False, default=0)

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
    )
