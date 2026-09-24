from __future__ import annotations

"""
Generic, polymorphic record-versioning support for the shared SNS
compliance framework. Created only where no existing domain-specific
version table already provides this (e.g. election addendum versioning
lives on ElectionAddendumRequest.version_number/supersedes_request_id;
Plan of Care already has PlanOfCareVersion) -- this table is for
compliance-domain records that don't already have a dedicated version
concept.
"""

import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.base import Base


class RecordVersion(Base):
    __tablename__ = "record_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    source_record_type = Column(String(64), nullable=False, index=True)
    source_record_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    version_number = Column(Integer, nullable=False)
    snapshot = Column(JSONB, nullable=False)
    change_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        Index("ix_record_versions_tenant_source", "tenant_id", "source_record_type", "source_record_id"),
        UniqueConstraint(
            "source_record_type",
            "source_record_id",
            "version_number",
            name="uq_record_versions_source_version",
        ),
        CheckConstraint("version_number > 0", name="ck_record_versions_version_positive"),
    )
