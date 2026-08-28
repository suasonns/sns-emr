from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


# processing_status state machine (Phase A durability, see
# app/services/evidence/recovery_service.py for the recovery sweep that
# drives documents through this machine when a step is interrupted):
#
#   PENDING    -- uploaded, not yet picked up by run_document_intelligence
#                 (either brand new, or the server restarted/crashed
#                 before the background task ever started).
#   PROCESSING -- run_document_intelligence is actively working on it, or
#                 was, until it either finished or the process died
#                 mid-flight (the recovery sweep treats a PROCESSING row
#                 whose processing_started_at is older than a timeout as
#                 stuck, and safely re-drives it).
#   COMPLETE   -- text extraction + AI classification + harvest all ran
#                 (or were safely skipped as already-done); nothing left
#                 to do for this document.
#   FAILED     -- the pipeline raised and gave up for this attempt;
#                 eligible for automatic retry by the recovery sweep up
#                 to a bounded attempt count.
DOCUMENT_PROCESSING_STATUSES = ("PENDING", "PROCESSING", "COMPLETE", "FAILED")


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

    # -----------------------------------------------------------
    # PHASE A DURABILITY: processing state machine, idempotency, retry
    # -----------------------------------------------------------
    processing_status = Column(String(24), nullable=False, default="PENDING")

    # sha256 of the uploaded bytes. Combined with (tenant_id, patient_id)
    # at the API layer, this lets a byte-identical re-upload (e.g. an RN's
    # offline app retrying an upload it wasn't sure succeeded) resolve to
    # the SAME document_records row instead of creating a duplicate that
    # would be harvested twice.
    content_hash = Column(String(64), nullable=True)

    processing_attempts = Column(Integer, nullable=False, default=0)
    last_processing_error = Column(Text, nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
