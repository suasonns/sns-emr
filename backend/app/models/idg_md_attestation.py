from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class IDGMDAttestation(Base):
    """
    Enterprise-grade MD Attestation for IDG Review.

    Purpose:
    - Confirms physician participation in IDG
    - Required for regulatory compliance
    - NOT an approval system (attestation only)

    Compliance:
    - Exactly ONE attestation per IDG review
    - Must include timestamp when signed
    """

    __tablename__ = "idg_md_attestations"

    __table_args__ = (
        UniqueConstraint("idg_review_id", name="uq_idg_md_attestation_review"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    idg_review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_reviews.id"),
        nullable=False,
        index=True,
    )

    physician_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    is_signed = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    signed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
