from __future__ import annotations

import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class IDGNote(Base):
    """
    Enterprise-grade IDG discipline note.

    Purpose:
    - Captures interdisciplinary participation during IDG.
    - Supports IDG completeness validation.
    - Preserves discipline-specific documentation.

    Current database-safe version:
    - Does not include signed_by.
    - Does not include updated_by.
    - Uses existing DB-compatible columns only.
    """

    __tablename__ = "idg_notes"

    __table_args__ = (
        UniqueConstraint(
            "idg_review_id",
            "discipline",
            name="uq_idg_note_discipline",
        ),
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

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    idg_review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_reviews.id"),
        nullable=False,
        index=True,
    )

    discipline = Column(
        String(50),
        nullable=False,
    )

    note = Column(
        Text,
        nullable=False,
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    signed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )