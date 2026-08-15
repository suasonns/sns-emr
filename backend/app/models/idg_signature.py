# models/idg_signature.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class IDGSignature(Base):
    """
    IDG signature record.

    This table supports discipline-level IDG signature tracking.
    It should not replace attendee tracking. Attendee tracking and
    signature records may coexist if the system uses signatures for
    compliance evidence and attendees for participation.
    """

    __tablename__ = "idg_signatures"

    __table_args__ = (
        UniqueConstraint(
            "idg_review_id",
            "user_id",
            name="uq_idg_signature_review_user",
        ),
        Index("ix_idg_signatures_tenant_id", "tenant_id"),
        Index("ix_idg_signatures_patient_id", "patient_id"),
        Index("ix_idg_signatures_idg_review_id", "idg_review_id"),
        Index("ix_idg_signatures_user_id", "user_id"),
        Index("ix_idg_signatures_discipline", "discipline"),
        Index("ix_idg_signatures_signed_at", "signed_at"),
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
        nullable=False,
        index=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    discipline = Column(
        String(50),
        nullable=False,
        index=True,
    )

    signed = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    signed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    signature_note = Column(
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