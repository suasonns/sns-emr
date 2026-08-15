# models/idg_justification.py

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
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class IDGJustification(Base):
    """
    Structured justification supporting an IDG decision.

    This table documents WHY a decision was made and
    preserves the evidence trail supporting:

    - POC updates
    - POC non-updates
    - Risk acceptance
    - Escalation decisions
    - Hospitalization prevention decisions
    - Recertification rationale
    - Intelligence item disposition

    This table does not replace:
        - IDG intelligence items
        - IDG notes
        - POC problems
        - POC goals
        - POC interventions
    """

    __tablename__ = "idg_justification_notes"

    __table_args__ = (
        Index("ix_idg_justification_tenant_id", "tenant_id"),
        Index("ix_idg_justification_patient_id", "patient_id"),
        Index("ix_idg_justification_idg_review_id", "idg_review_id"),
        Index("ix_idg_justification_category", "category"),
        Index("ix_idg_justification_status", "status"),
        Index("ix_idg_justification_created_at", "created_at"),
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

    category = Column(
        String(100),
        nullable=True,
        index=True,
    )

    status = Column(
        String(50),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )

    justification_text = Column(
        Text,
        nullable=False,
    )

    decision_outcome = Column(
        String(100),
        nullable=True,
    )

    source_type = Column(
        String(100),
        nullable=True,
    )

    source_record_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    intelligence_item_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    decision_owner_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    created_by = Column(
        UUID(as_uuid=True),
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