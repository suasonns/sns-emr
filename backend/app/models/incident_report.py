# app/models/incident_report.py

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    String,
    Text,
    Time,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base  # ✅ USE SHARED BASE (CRITICAL)


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)

    clinical_note_id = Column(UUID(as_uuid=True), nullable=True)

    incident_type = Column(String(32), nullable=False)
    incident_severity = Column(
        String(16),
        nullable=False,
        server_default=text("'STANDARD'"),
    )

    incident_date = Column(Date, nullable=False)
    reported_date = Column(Date, nullable=True)
    incident_time = Column(Time, nullable=True)

    reported_by = Column(String(32), nullable=True)
    witnessed_by = Column(String(32), nullable=True)
    place = Column(String(16), nullable=True)
    area = Column(String(32), nullable=True)
    surface = Column(String(32), nullable=True)

    medication_used = Column(String(32), nullable=True)
    activity_at_time = Column(String(64), nullable=True)

    injury_level = Column(String(32), nullable=True)
    injury_type = Column(String(32), nullable=True)
    other_injury_text = Column(Text, nullable=True)

    narrative = Column(Text, nullable=True)

    entered_by = Column(UUID(as_uuid=True), nullable=True)
    signed_by = Column(UUID(as_uuid=True), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )