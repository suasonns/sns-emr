from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    document_type = Column(String(64), nullable=False)
    source = Column(String(32), nullable=False, default="EXTERNAL")

    file_name = Column(String(255), nullable=True)
    file_path = Column(String(512), nullable=True)

    extracted_values = Column(JSONB, nullable=True)
    document_text = Column(Text, nullable=True)

    is_flagged = Column(Boolean, nullable=False, default=False)
    flag_tier = Column(String(16), nullable=True)
    matched_rule_ids = Column(JSONB, nullable=True)

    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Optional: if you want referential integrity here, make it FK("users.id")
    created_by = Column(UUID(as_uuid=True), nullable=True)
