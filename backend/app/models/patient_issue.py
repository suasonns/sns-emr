from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class PatientIssue(Base):
    __tablename__ = "patient_issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    identified_date = Column(Date, nullable=False)
    identified_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(
        String(16),
        nullable=False,
        default="OPEN",
        server_default=text("'OPEN'"),
        index=True,
    )
    outcome_notes = Column(Text, nullable=True)
    resolved_date = Column(Date, nullable=True)
    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_patient_issues_tenant_patient_identified_date", "tenant_id", "patient_id", "identified_date"),
    )
