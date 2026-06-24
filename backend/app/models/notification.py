from __future__ import annotations

import uuid
from sqlalchemy import Column, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    # =========================================================
    # PRIMARY KEY
    # =========================================================
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # =========================================================
    # MULTI-TENANT + OWNERSHIP
    # =========================================================
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)

    # ✅ CRITICAL FOR CLINICAL CONTEXT
    patient_id = Column(UUID(as_uuid=True), nullable=True)

    # =========================================================
    # MESSAGE STRUCTURE (UI / UX READY)
    # =========================================================
    title = Column(Text, nullable=False)
    message = Column(Text, nullable=False)

    # =========================================================
    # CLASSIFICATION (ENTERPRISE READY)
    # =========================================================
    notification_type = Column(Text, nullable=False)
    # e.g. TASK_ASSIGNED, ESCALATION, POC_TRIGGER

    # =========================================================
    # SOURCE TRACEABILITY (AUDIT SAFE)
    # =========================================================
    source_type = Column(Text, nullable=False)
    # e.g. TASK, POC, COMMUNICATION_LOG

    source_id = Column(UUID(as_uuid=True), nullable=False)

    # =========================================================
    # STATE MANAGEMENT
    # =========================================================
    is_read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # =========================================================
    # TIMESTAMPS
    # =========================================================
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )