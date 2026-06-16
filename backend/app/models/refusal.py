from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.db.base import Base


class Refusal(Base):
    __tablename__ = "refusals"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    discipline = Column(Text, nullable=False, index=True)
    reason = Column(Text, nullable=True)

    refused_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    was_reoffered = Column(Boolean, nullable=False, default=False)
    reoffered_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(PGUUID(as_uuid=True), nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
