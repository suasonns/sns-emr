import uuid
from sqlalchemy import Column, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.db import Base


class CommunicationsLog(Base):
    __tablename__ = "communications_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False)

    # EXACT event types as staff uses them
    event_type = Column(Text, nullable=False)

    # Clinical focus area (ADL, Pain, Neuro, etc.)
    focus_area = Column(Text, nullable=True)

    # When it actually happened
    event_time = Column(DateTime(timezone=True), nullable=False)

    # Free‑form narrative
    summary = Column(Text, nullable=False)

    # Flexible metadata (reminders, flags, future expansion)
    details = Column(JSON, nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)