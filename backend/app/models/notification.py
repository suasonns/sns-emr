from __future__ import annotations

import uuid
from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.db import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)

    # Source reference (audit-safe)
    source_type = Column(Text, nullable=False)  # e.g. COMMUNICATIONS_LOG
    source_id = Column(UUID(as_uuid=True), nullable=False)

    message = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    seen_at = Column(DateTime(timezone=True), nullable=True)
