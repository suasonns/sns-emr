# models/idg_md_attestation.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class IDGMDAttestation(Base):
    """
    Medical Director attestation of an IDG review.

    Purpose:
        Documents physician oversight and review of IDG findings,
        recommendations, and clinical decisions.

    Scope:
        This is NOT the Plan of Care physician approval workflow.

        POC approvals belong in:
            poc_physician_approvals

        This table exists solely for IDG review attestation.
    """

    __tablename__ = "idg_md_attestations"

    __table_args__ = (
        UniqueConstraint(
            "idg_review_id",
            name="uq_idg_md_attestation_review",
        ),
        Index("ix_idg_md_attestations_tenant_id", "tenant_id"),
        Index("ix_idg_md_attestations_patient_id", "patient_id"),
        Index("ix_idg_md_attestations_idg_review_id", "idg_review_id"),
        Index("ix_idg_md_attestations_attested_by", "attested_by"),
        Index("ix_idg_md_attestations_attested_at", "attested_at"),
        Index("ix_idg_md_attestations_status", "status"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    patient_id = Column(
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

    status = Column(
        String(50),
        nullable=False,
        server_default=text("'PENDING'"),
    )

    attested = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    attested_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    physician_role = Column(
        String(100),
        nullable=True,
    )

    attested_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    attestation_note = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )

    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )