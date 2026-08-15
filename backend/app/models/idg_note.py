# models/idg_note.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
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


class IDGNote(Base):
    """
    Discipline-specific IDG narrative documentation.

    Purpose:
        Capture the discipline narrative entered during
        interdisciplinary review.

    Scope:
        This table stores discipline documentation only.

        It does NOT replace:
            - IDG intelligence items
            - IDG justifications
            - POC problems
            - POC goals
            - POC interventions
    """

    __tablename__ = "idg_notes"

    __table_args__ = (
        UniqueConstraint(
            "idg_review_id",
            "discipline",
            name="uq_idg_note_review_discipline",
        ),
        Index("ix_idg_notes_tenant_id", "tenant_id"),
        Index("ix_idg_notes_patient_id", "patient_id"),
        Index("ix_idg_notes_idg_review_id", "idg_review_id"),
        Index("ix_idg_notes_discipline", "discipline"),
        Index("ix_idg_notes_status", "status"),
        Index("ix_idg_notes_created_at", "created_at"),
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

    discipline = Column(
        String(50),
        nullable=False,
        index=True,
    )

    role_label = Column(
        String(100),
        nullable=True,
    )

    status = Column(
        String(50),
        nullable=False,
        server_default=text("'COMPLETED'"),
    )

    note = Column(
        Text,
        nullable=True,
    )

    entered_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    entered_by_name = Column(
        String(255),
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